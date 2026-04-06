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

"""Core Grammar class — the read-only projection of Lantern Grammar model data.

This module is an implementation detail.  Consumers should import only from
``lantern_grammar``::

    from lantern_grammar import Grammar, LanternGrammarLoadError

Thread safety
-------------
A ``Grammar`` instance is immutable after construction and is safe for
concurrent read-only access across threads.  See DN-LGR-PROP-004.

Authority boundary
------------------
The packaged model data is the semantic source of truth.  This class is a
projection and query surface over that data; it does not invent or reinterpret
model meaning.  Workflow policy, workbench IDs, and runtime posture remain
outside this package.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Iterator, Optional

from ._exceptions import LanternGrammarLoadError


# ---------------------------------------------------------------------------
# Location of bundled model data
# ---------------------------------------------------------------------------
# Resolution order for Grammar.load():
#
# 1. <package_dir>/_model/
#    For installed (non-editable) packages: setuptools copies model/ into
#    _model/ inside the wheel.  For editable installs with a _model symlink
#    manually created at src/lantern_grammar/_model -> ../../model, same path.
#
# 2. <project_root>/model/
#    Fallback for editable installs in a src/ layout when no _model/ symlink
#    exists.  Detected by walking up from the package file to find model/.
#
def _find_model_bundle_dir() -> Path:
    pkg_dir = Path(__file__).parent
    # --- Primary: _model/ inside the installed package directory ---
    bundled = pkg_dir / "_model"
    if bundled.is_dir():
        return bundled
    # --- Fallback: project root model/ for src-layout editable installs ---
    # src/lantern_grammar/ -> src/ -> project_root/ -> model/
    candidate = pkg_dir.parent.parent / "model"
    if candidate.is_dir():
        return candidate
    # Return primary path so load() surfaces a clear error.
    return bundled


_MODEL_BUNDLE_DIR: Path = _find_model_bundle_dir()

# Canonical relation-type IDs used for gate-dependency categorisation.
_REQUIRES_INPUT = "lg:reltypes/requires_input"
_REQUIRES_EVIDENCE = "lg:reltypes/requires_evidence"
_REQUIRES_STATUS = "lg:reltypes/requires_status"
_GATE_PREFIX = "lg:gates/"


# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------


class Grammar:
    """Read-only projection of the released Lantern Grammar model.

    Do not instantiate directly.  Use one of the class-method constructors:

    * ``Grammar.load()``  — load the model bundled with the distribution.
    * ``Grammar.from_directory(path)``  — load from an explicit directory.

    All public methods are read-only and thread-safe.
    """

    # --- Internal construction (not public API) ---

    def __init__(
        self,
        manifest_data: dict,
        entities: dict,
        relations: dict,
        terms: dict,
        package_version: str,
    ) -> None:
        # All collections are built once and never mutated after this point,
        # giving the thread-safety guarantee in the contract.
        self._manifest: MappingProxyType = MappingProxyType(dict(manifest_data))
        self._entities: dict[str, MappingProxyType] = {k: MappingProxyType(v) for k, v in entities.items()}
        self._relations: dict[str, MappingProxyType] = {k: MappingProxyType(v) for k, v in relations.items()}
        self._terms: dict[str, MappingProxyType] = {k: MappingProxyType(v) for k, v in terms.items()}
        self._package_version = package_version

    # --- Stable construction contract ---

    @classmethod
    def load(cls) -> "Grammar":
        """Load the Lantern Grammar model bundled with the installed distribution.

        Returns a ``Grammar`` instance ready for read-only queries.

        Raises:
            LanternGrammarLoadError: if packaged model data is absent,
                unloadable, or structurally invalid.
        """
        if not _MODEL_BUNDLE_DIR.is_dir():
            raise LanternGrammarLoadError(
                f"Bundled model data not found at {_MODEL_BUNDLE_DIR}. "
                "The lantern-grammar package may not have been installed correctly."
            )
        return cls._load_from_path(_MODEL_BUNDLE_DIR)

    @classmethod
    def from_directory(cls, path) -> "Grammar":
        """Load a Lantern Grammar model from an explicit filesystem directory.

        This constructor is stable because Lantern and package tests need a
        deterministic way to load the grammar from local checkouts and to
        validate against malformed test fixtures.

        Args:
            path: path-like object or str pointing to the grammar model root
                (the directory that contains ``manifest.json`` and ``index.json``).

        Returns a ``Grammar`` instance ready for read-only queries.

        Raises:
            FileNotFoundError: if *path* does not exist.
            LanternGrammarLoadError: if *path* exists but does not contain a
                valid Lantern Grammar model structure.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Grammar model directory not found: {path}")
        if not p.is_dir():
            raise LanternGrammarLoadError(f"Grammar model path is not a directory: {path}")
        return cls._load_from_path(p)

    @classmethod
    def _load_from_path(cls, model_dir: Path) -> "Grammar":
        """Internal loader shared by both public constructors."""
        manifest_data = _load_json_file(model_dir / "manifest.json", "manifest.json")
        _require_fields(manifest_data, ("model_id", "model_version"), "manifest.json")

        index_data = _load_json_file(model_dir / "index.json", "index.json")
        if "entries" not in index_data:
            raise LanternGrammarLoadError("index.json missing required 'entries' field")

        entities: dict = {}
        relations: dict = {}
        terms: dict = {}

        for entry in index_data["entries"]:
            entry_id: Optional[str] = entry.get("id")
            entry_kind: Optional[str] = entry.get("kind")
            locator: Optional[str] = entry.get("locator")

            if not (entry_id and entry_kind and locator):
                raise LanternGrammarLoadError(f"Index entry missing required fields (id/kind/locator): {entry}")

            # Locators are of the form "model/objects/<Kind>/<file>.json",
            # expressed relative to the repository root with "model/" as the
            # base segment.  We rebase them onto model_dir so they work both
            # in the source tree (where _model/ is a symlink to model/) and in
            # an installed distribution (where _model/ is a real copy).
            relative = locator.removeprefix("model/")
            obj_path = model_dir / relative
            obj_data = _load_json_file(obj_path, f"object for {entry_id!r}")

            if entry_kind == "Entity":
                entities[entry_id] = obj_data
            elif entry_kind == "Relation":
                relations[entry_id] = obj_data
            elif entry_kind == "Term":
                terms[entry_id] = obj_data
            # Unknown future kinds are silently skipped; this preserves
            # forward-compatibility as the grammar evolves.

        pkg_version = _get_package_version()
        return cls(manifest_data, entities, relations, terms, pkg_version)

    # --- Manifest and version metadata ---

    def manifest(self) -> MappingProxyType:
        """Return the model manifest as a read-only mapping.

        Stable minimum fields: ``model_id``, ``model_version``.
        All other manifest fields are surfaced verbatim.
        """
        return self._manifest

    def package_version(self) -> str:
        """Return the installed Python distribution version string.

        Distinct from ``manifest()["model_version"]``, which is the semantic
        grammar version.  Returns ``"unknown"`` when metadata is unavailable.
        """
        return self._package_version

    # --- Entity access ---

    def get_entity(self, entity_id: str) -> Optional[MappingProxyType]:
        """Return the entity with *entity_id*, or ``None`` if not found.

        Covers all entity kinds: artifacts, gates, statuses, relation types,
        and record classes.  Use the ``prefix`` filter on ``iter_entities()``
        to iterate a specific family.

        Stable minimum fields: ``id``, ``kind``, ``short_name``,
        ``definition``, ``status``.
        """
        return self._entities.get(entity_id)

    def iter_entities(
        self,
        *,
        prefix: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Iterator[MappingProxyType]:
        """Iterate over entity mappings in the loaded model.

        Args:
            prefix: if given, yield only entities whose ``id`` starts with
                this string (e.g. ``"lg:gates/"``).
            status: if given, yield only entities with this ``status`` value
                (e.g. ``"Released"``).
        """
        for entity in self._entities.values():
            if prefix is not None and not entity["id"].startswith(prefix):
                continue
            if status is not None and entity.get("status") != status:
                continue
            yield entity

    # --- Relation access ---

    def get_relation(self, relation_id: str) -> Optional[MappingProxyType]:
        """Return the relation with *relation_id*, or ``None`` if not found.

        Stable minimum fields: ``id``, ``kind``, ``short_name``,
        ``definition``, ``status``, ``relation_type_id``,
        ``source_entity_id``, ``target_entity_id``.
        """
        return self._relations.get(relation_id)

    def find_relations(
        self,
        *,
        relation_type_id: Optional[str] = None,
        source_entity_id: Optional[str] = None,
        target_entity_id: Optional[str] = None,
    ) -> Iterator[MappingProxyType]:
        """Iterate over relations matching one or more filter criteria.

        At least one filter argument must be supplied.

        Args:
            relation_type_id: match on ``relation_type_id`` field.
            source_entity_id: match on ``source_entity_id`` field.
            target_entity_id: match on ``target_entity_id`` field.

        Raises:
            ValueError: if no filter arguments are supplied.
        """
        if not any([relation_type_id, source_entity_id, target_entity_id]):
            raise ValueError(
                "find_relations() requires at least one filter argument: "
                "relation_type_id, source_entity_id, or target_entity_id"
            )
        for rel in self._relations.values():
            if relation_type_id is not None and rel.get("relation_type_id") != relation_type_id:
                continue
            if source_entity_id is not None and rel.get("source_entity_id") != source_entity_id:
                continue
            if target_entity_id is not None and rel.get("target_entity_id") != target_entity_id:
                continue
            yield rel

    # --- Term lookup ---

    def get_term(self, term_id: str) -> Optional[MappingProxyType]:
        """Return the vocabulary term with *term_id*, or ``None`` if not found.

        Stable minimum fields: ``id``, ``kind``, ``short_name``,
        ``definition``, ``status``.
        """
        return self._terms.get(term_id)

    def find_terms(
        self,
        *,
        prefix: Optional[str] = None,
        short_name: Optional[str] = None,
    ) -> Iterator[MappingProxyType]:
        """Iterate over vocabulary term mappings.

        Args:
            prefix: if given, yield only terms whose ``id`` starts with this
                string.
            short_name: if given, yield only terms with this exact
                ``short_name``.
        """
        for term in self._terms.values():
            if prefix is not None and not term["id"].startswith(prefix):
                continue
            if short_name is not None and term.get("short_name") != short_name:
                continue
            yield term

    # --- Gate-dependency queries ---

    def gate_dependencies(self, gate_id: str) -> MappingProxyType:
        """Return the semantic dependencies for *gate_id*.

        Args:
            gate_id: canonical gate entity ID, e.g. ``"lg:gates/gt_115"``.

        Returns a read-only mapping with stable keys:

        * ``gate_id`` — the requested gate ID.
        * ``requires_input`` — tuple of target entity IDs via
          ``requires_input`` relations.
        * ``requires_evidence`` — tuple of target entity IDs via
          ``requires_evidence`` relations.
        * ``requires_status`` — tuple of target entity IDs via
          ``requires_status`` relations.
        * ``relation_ids`` — tuple of all supporting relation IDs.

        Raises:
            KeyError: if *gate_id* does not exist or is not a gate entity.
        """
        entity = self._entities.get(gate_id)
        if entity is None or not gate_id.startswith(_GATE_PREFIX):
            raise KeyError(f"Gate not found in model: {gate_id!r}.  " "Gate IDs must start with 'lg:gates/'.")

        requires_input: list[str] = []
        requires_evidence: list[str] = []
        requires_status: list[str] = []
        relation_ids: list[str] = []

        for rel_id in entity.get("relation_ids", []):
            rel = self._relations.get(rel_id)
            if rel is None:
                continue
            rtype = rel.get("relation_type_id")
            target = rel.get("target_entity_id", "")
            relation_ids.append(rel_id)
            if rtype == _REQUIRES_INPUT:
                requires_input.append(target)
            elif rtype == _REQUIRES_EVIDENCE:
                requires_evidence.append(target)
            elif rtype == _REQUIRES_STATUS:
                requires_status.append(target)

        return MappingProxyType(
            {
                "gate_id": gate_id,
                "requires_input": tuple(requires_input),
                "requires_evidence": tuple(requires_evidence),
                "requires_status": tuple(requires_status),
                "relation_ids": tuple(relation_ids),
            }
        )

    # --- Integrity validation ---

    def validate_integrity(self) -> MappingProxyType:
        """Validate the structural integrity of the loaded model.

        Returns a read-only mapping with stable keys:

        * ``ok`` — ``True`` when no errors were found.
        * ``errors`` — tuple of human-readable error messages.
        * ``warnings`` — tuple of non-fatal notices.

        Coverage:

        * manifest has required fields.
        * Each relation's ``source_entity_id``, ``target_entity_id``, and
          ``relation_type_id`` exist in the entity index.
        * Each gate entity's ``relation_ids`` list references existing
          relations.
        """
        errors: list[str] = []
        warnings: list[str] = []

        # --- Manifest ---
        for field in ("model_id", "model_version"):
            if field not in self._manifest:
                errors.append(f"manifest missing required field: {field!r}")

        # --- Relation cross-references ---
        for rel_id, rel in self._relations.items():
            src = rel.get("source_entity_id")
            tgt = rel.get("target_entity_id")
            rtype = rel.get("relation_type_id")
            if src and src not in self._entities:
                errors.append(f"Relation {rel_id!r}: source_entity_id {src!r} " "not found in entity index")
            if tgt and tgt not in self._entities:
                errors.append(f"Relation {rel_id!r}: target_entity_id {tgt!r} " "not found in entity index")
            if rtype and rtype not in self._entities:
                errors.append(f"Relation {rel_id!r}: relation_type_id {rtype!r} " "not found in entity index")

        # --- Gate relation_ids cross-references ---
        for entity_id, entity in self._entities.items():
            if entity_id.startswith(_GATE_PREFIX):
                for rel_id in entity.get("relation_ids", []):
                    if rel_id not in self._relations:
                        errors.append(f"Gate {entity_id!r}: relation_id {rel_id!r} " "not found in relation index")

        return MappingProxyType(
            {
                "ok": len(errors) == 0,
                "errors": tuple(errors),
                "warnings": tuple(warnings),
            }
        )

    def __repr__(self) -> str:
        model_id = self._manifest.get("model_id", "?")
        version = self._manifest.get("model_version", "?")
        return (
            f"Grammar(model_id={model_id!r}, model_version={version!r}, "
            f"entities={len(self._entities)}, relations={len(self._relations)}, "
            f"terms={len(self._terms)})"
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _load_json_file(path: Path, label: str) -> dict:
    """Load a JSON file, raising LanternGrammarLoadError on failure."""
    if not path.exists():
        raise LanternGrammarLoadError(f"{label} not found at {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LanternGrammarLoadError(f"Failed to parse {label}: {exc}") from exc
    except OSError as exc:
        raise LanternGrammarLoadError(f"Failed to read {label}: {exc}") from exc


def _require_fields(data: dict, fields: tuple, source: str) -> None:
    """Raise LanternGrammarLoadError if any of *fields* is absent from *data*."""
    for field in fields:
        if field not in data:
            raise LanternGrammarLoadError(f"{source} missing required field: {field!r}")


def _get_package_version() -> str:
    """Return installed package version, or 'unknown' if unavailable."""
    try:
        from importlib.metadata import version

        return version("lantern-grammar")
    except Exception:
        return "unknown"
