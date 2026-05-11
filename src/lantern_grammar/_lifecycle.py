# Copyright 2025 Lantern Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Grammar-schema-conformant lifecycle declaration (GSCLD) bundle loader and validator.

Implements DN-LGR-PROP-007. A GSCLD is a directory bundle: one manifest file plus one
family file per artifact family. The Lifecycle class loads the bundle, validates each
file structurally against the published JSON Schemas, validates referenced grammar entity
IDs against the loaded Grammar, and exposes typed query methods over the declaration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from ._exceptions import LanternGrammarLoadError
from ._grammar import Grammar


SCHEMA_VERSION = "1.0"
_MANIFEST_SCHEMA = f"gscld-manifest-{SCHEMA_VERSION}.schema.json"
_FAMILY_SCHEMA = f"gscld-family-{SCHEMA_VERSION}.schema.json"


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation problem, with its location path and description."""

    path: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    """The aggregated result of a Lifecycle.validate() call."""

    ok: bool
    issues: tuple[ValidationIssue, ...]


@dataclass(frozen=True)
class StatusBinding:
    """A status declared for an artifact family, with its display label."""

    status_id: str
    label: str


@dataclass(frozen=True)
class Transition:
    """A permitted status transition within an artifact family."""

    from_status: str
    to_status: str


@dataclass(frozen=True)
class Cardinality:
    """A single cardinality form. Exactly one descriptive field is populated."""

    exact: int | None = None
    min_count: int | None = None
    max_count: int | None = None
    is_all: bool = False
    is_none: bool = False


@dataclass(frozen=True)
class CardinalityRule:
    """A single cardinality predicate over a status set."""

    statuses: tuple[str, ...]
    cardinality: Cardinality


@dataclass(frozen=True)
class TraversalConstraint:
    """A named slot's constraints: related family + AND-combined cardinality rules."""

    slot: str
    related_family_id: str
    rules: tuple[CardinalityRule, ...]


@dataclass(frozen=True)
class StateConstraint:
    """All traversal constraints active when a subject artifact is in a given status."""

    subject_family_id: str
    status_id: str
    traversals: tuple[TraversalConstraint, ...]


class Lifecycle:
    """A grammar-schema-conformant lifecycle declaration (GSCLD) bundle."""

    SCHEMA_VERSION = SCHEMA_VERSION

    def __init__(
        self,
        grammar: Grammar,
        manifest: dict[str, Any],
        families: dict[str, dict[str, Any]],
    ) -> None:
        self._grammar = grammar
        self._manifest = manifest
        self._families = families  # keyed by artifact family ID

    # --- factories ---------------------------------------------------------

    @classmethod
    def from_manifest(cls, grammar: Grammar, manifest_path: str | Path) -> "Lifecycle":
        """Load a full GSCLD bundle from a manifest file path."""
        manifest_path = Path(manifest_path)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
        if not isinstance(manifest, dict):
            raise LanternGrammarLoadError(f"Manifest root must be a mapping; got {type(manifest).__name__}")
        base = manifest_path.parent
        families_list = manifest.get("families", [])
        if not isinstance(families_list, list):
            raise LanternGrammarLoadError(f"Manifest 'families' must be a list; got {type(families_list).__name__}")
        families: dict[str, dict[str, Any]] = {}
        for rel_path in families_list:
            if not isinstance(rel_path, str):
                raise LanternGrammarLoadError(
                    f"Manifest 'families' entries must be strings; got {type(rel_path).__name__}"
                )
            family_path = base / rel_path
            with open(family_path, "r", encoding="utf-8") as f:
                family_data = yaml.safe_load(f)
            if not isinstance(family_data, dict):
                raise LanternGrammarLoadError(f"Family file {rel_path} root must be a mapping")
            family_id = family_data.get("id", rel_path)
            families[family_id] = family_data
        return cls(grammar, manifest, families)

    @classmethod
    def from_family_dict(cls, grammar: Grammar, data: dict[str, Any]) -> "Lifecycle":
        """Wrap a single family dict for single-family validation.

        Runs JSON Schema structural validation, per-family internal consistency
        checks (duplicate statuses, duplicate transitions, min > max cardinality),
        and grammar entity existence checks. Cross-bundle checks — in particular,
        whether a related_family_id appears in the same bundle — are not performed
        because no manifest is present. Use from_manifest for full bundle validation.
        """
        family_id = data.get("id", "")
        return cls(grammar, {}, {family_id: data})

    @classmethod
    def manifest_schema(cls) -> dict[str, Any]:
        """Return the published GSCLD manifest JSON Schema as a parsed dict."""
        text = files("lantern_grammar").joinpath("_schemas").joinpath(_MANIFEST_SCHEMA).read_text(encoding="utf-8")
        return json.loads(text)

    @classmethod
    def family_schema(cls) -> dict[str, Any]:
        """Return the published GSCLD family JSON Schema as a parsed dict."""
        text = files("lantern_grammar").joinpath("_schemas").joinpath(_FAMILY_SCHEMA).read_text(encoding="utf-8")
        return json.loads(text)

    # --- validation --------------------------------------------------------

    def validate(self) -> ValidationResult:
        """Run per-file structural validation then bundle-level referential checks.

        Returns a ValidationResult collecting all issues; never raises for content
        problems. Raises only for unrecoverable I/O errors.
        """
        issues: list[ValidationIssue] = []

        # Per-file structural validation
        if self._manifest:
            issues.extend(self._validate_structural(self._manifest, self.manifest_schema(), "/manifest"))
        for family_id, family_data in self._families.items():
            issues.extend(self._validate_structural(family_data, self.family_schema(), f"/{family_id}"))

        if issues:
            return ValidationResult(ok=False, issues=tuple(issues))

        # Per-family internal checks run for every family regardless of manifest presence.
        # (Duplicate detection, min > max, and grammar entity lookups are per-family.)
        issues.extend(self._validate_bundle_references())

        # Grammar compatibility and cross-bundle checks require a full manifest.
        if self._manifest:
            issues.extend(self._validate_grammar_compatibility())

        return ValidationResult(ok=not issues, issues=tuple(issues))

    def _validate_structural(self, data: dict, schema: dict, base_path: str) -> list[ValidationIssue]:
        from jsonschema import Draft202012Validator

        results: list[ValidationIssue] = []
        for err in sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: e.path):
            path = base_path + "/" + "/".join(str(p) for p in err.path)
            results.append(ValidationIssue(path=path, message=err.message))
        return results

    def _validate_grammar_compatibility(self) -> list[ValidationIssue]:
        results: list[ValidationIssue] = []
        min_v = self._manifest.get("grammar_compatibility", {}).get("min_model_version")
        if not min_v:
            return results
        actual = self._grammar.manifest().get("model_version", "")
        if _semver_tuple(actual) < _semver_tuple(min_v):
            results.append(
                ValidationIssue(
                    path="/manifest/grammar_compatibility/min_model_version",
                    message=f"GSCLD requires model >= {min_v} but loaded Grammar reports {actual}",
                )
            )
        return results

    def _validate_bundle_references(self) -> list[ValidationIssue]:
        results: list[ValidationIssue] = []
        declared_family_ids = set(self._families.keys())

        for family_id, family_data in self._families.items():
            base = f"/{family_id}"

            if self._grammar.get_entity(family_id) is None:
                results.append(
                    ValidationIssue(
                        path=f"{base}/id",
                        message=f"unknown artifact family: {family_id}",
                    )
                )

            # Collect declared status IDs and validate each
            declared_status_ids: set[str] = set()
            seen_status_ids: set[str] = set()
            for i, st in enumerate(family_data.get("statuses", [])):
                sid = st.get("id", "")
                if sid in seen_status_ids:
                    results.append(
                        ValidationIssue(
                            path=f"{base}/statuses/{i}/id",
                            message=f"duplicate status id: {sid}",
                        )
                    )
                seen_status_ids.add(sid)
                declared_status_ids.add(sid)
                if self._grammar.get_entity(sid) is None:
                    results.append(
                        ValidationIssue(
                            path=f"{base}/statuses/{i}/id",
                            message=f"unknown status: {sid}",
                        )
                    )

            # Validate transitions reference declared statuses
            seen_pairs: set[tuple[str, str]] = set()
            for i, t in enumerate(family_data.get("transitions", [])):
                frm, to = t.get("from", ""), t.get("to", "")
                for field, val in (("from", frm), ("to", to)):
                    if val not in declared_status_ids:
                        results.append(
                            ValidationIssue(
                                path=f"{base}/transitions/{i}/{field}",
                                message=f"status {val} not declared for family {family_id}",
                            )
                        )
                pair = (frm, to)
                if pair in seen_pairs:
                    results.append(
                        ValidationIssue(
                            path=f"{base}/transitions/{i}",
                            message=f"duplicate transition {frm} -> {to}",
                        )
                    )
                seen_pairs.add(pair)

            # Validate state_constraints
            slot_family_index: dict[str, str] = {}
            for i, sc in enumerate(family_data.get("state_constraints", [])):
                status = sc.get("status", "")
                if status not in declared_status_ids:
                    results.append(
                        ValidationIssue(
                            path=f"{base}/state_constraints/{i}/status",
                            message=f"status {status} not declared for family {family_id}",
                        )
                    )
                for slot, tc in (sc.get("rules") or {}).items():
                    rf_id = tc.get("related_family_id", "")
                    slot_path = f"{base}/state_constraints/{i}/rules/{slot}"

                    # Slot consistency within family
                    if slot in slot_family_index:
                        if slot_family_index[slot] != rf_id:
                            results.append(
                                ValidationIssue(
                                    path=f"{slot_path}/related_family_id",
                                    message=(
                                        f"slot '{slot}' bound to {rf_id} but "
                                        f"previously bound to {slot_family_index[slot]}"
                                    ),
                                )
                            )
                    else:
                        slot_family_index[slot] = rf_id

                    if self._grammar.get_entity(rf_id) is None:
                        results.append(
                            ValidationIssue(
                                path=f"{slot_path}/related_family_id",
                                message=f"unknown artifact family: {rf_id}",
                            )
                        )
                    if self._manifest and rf_id not in declared_family_ids:
                        results.append(
                            ValidationIssue(
                                path=f"{slot_path}/related_family_id",
                                message=f"family {rf_id} is not declared in this bundle",
                            )
                        )

                    for j, rule in enumerate(tc.get("constraints", []) or []):
                        rule_path = f"{slot_path}/constraints/{j}"
                        for k, sid in enumerate(rule.get("statuses", []) or []):
                            if self._grammar.get_entity(sid) is None:
                                results.append(
                                    ValidationIssue(
                                        path=f"{rule_path}/statuses/{k}",
                                        message=f"unknown status: {sid}",
                                    )
                                )
                        card = rule.get("cardinality", {})
                        if "min" in card and "max" in card and card["min"] > card["max"]:
                            results.append(
                                ValidationIssue(
                                    path=f"{rule_path}/cardinality",
                                    message=f"min ({card['min']}) > max ({card['max']})",
                                )
                            )
        return results

    # --- queries -----------------------------------------------------------

    def artifact_families(self) -> tuple[str, ...]:
        """Return the artifact family IDs declared in this bundle."""
        return tuple(self._families.keys())

    def statuses_for(self, family_id: str) -> tuple[StatusBinding, ...]:
        """Return all status bindings declared for the given artifact family."""
        return tuple(
            StatusBinding(status_id=s["id"], label=s["label"])
            for s in self._families.get(family_id, {}).get("statuses", [])
        )

    def transitions_for(self, family_id: str) -> tuple[Transition, ...]:
        """Return all permitted status transitions for the given artifact family."""
        return tuple(
            Transition(from_status=t["from"], to_status=t["to"])
            for t in self._families.get(family_id, {}).get("transitions", [])
        )

    def state_constraints_for(self, family_id: str, status_id: str | None = None) -> tuple[StateConstraint, ...]:
        """Return state constraints for a family, optionally filtered to one status."""
        result: list[StateConstraint] = []
        for sc in self._families.get(family_id, {}).get("state_constraints", []):
            if status_id is not None and sc["status"] != status_id:
                continue
            traversals: list[TraversalConstraint] = []
            for slot, tc in (sc.get("rules") or {}).items():
                rules: list[CardinalityRule] = []
                for rule in tc.get("constraints", []) or []:
                    card = rule["cardinality"]
                    rules.append(
                        CardinalityRule(
                            statuses=tuple(rule["statuses"]),
                            cardinality=Cardinality(
                                exact=card.get("exact"),
                                min_count=card.get("min"),
                                max_count=card.get("max"),
                                is_all=bool(card.get("all", False)),
                                is_none=bool(card.get("none", False)),
                            ),
                        )
                    )
                traversals.append(
                    TraversalConstraint(
                        slot=slot,
                        related_family_id=tc["related_family_id"],
                        rules=tuple(rules),
                    )
                )
            result.append(
                StateConstraint(
                    subject_family_id=family_id,
                    status_id=sc["status"],
                    traversals=tuple(traversals),
                )
            )
        return tuple(result)


def _semver_tuple(s: str) -> tuple[int, ...]:
    return tuple(int(p) for p in s.split(".") if p.isdigit())
