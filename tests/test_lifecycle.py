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

"""Tests for the Lifecycle public API (DN-LGR-PROP-007)."""

import copy
from pathlib import Path

import pytest
import yaml

from lantern_grammar import (
    Grammar,
    Lifecycle,
    LanternGrammarLoadError,
    StatusBinding,
    Transition,
)

FIXTURE_MANIFEST = Path(__file__).parent / "fixtures" / "lifecycle-policy" / "manifest.yaml"
FIXTURE_CH = Path(__file__).parent / "fixtures" / "lifecycle-policy" / "ch.yaml"


@pytest.fixture
def grammar():
    return Grammar.load()


@pytest.fixture
def ch_family_dict():
    with open(FIXTURE_CH) as f:
        return yaml.safe_load(f)


def test_schemas_load():
    m = Lifecycle.manifest_schema()
    f = Lifecycle.family_schema()
    assert m["$id"] == "https://lantern-grammar.org/schemas/gscld/1.0/manifest"
    assert f["$id"] == "https://lantern-grammar.org/schemas/gscld/1.0/family"


def test_from_manifest_loads(grammar):
    lc = Lifecycle.from_manifest(grammar, FIXTURE_MANIFEST)
    families = lc.artifact_families()
    assert "lg:artifacts/ch" in families
    assert "lg:artifacts/ci" in families


def test_bundle_validates_ok(grammar):
    lc = Lifecycle.from_manifest(grammar, FIXTURE_MANIFEST)
    result = lc.validate()
    assert result.ok, f"unexpected issues: {result.issues}"


def test_from_family_dict_structural_ok(grammar, ch_family_dict):
    lc = Lifecycle.from_family_dict(grammar, ch_family_dict)
    result = lc.validate()
    # No manifest — structural + per-family internal checks; cross-bundle checks skipped
    assert result.ok, f"unexpected issues: {result.issues}"


def test_from_family_dict_catches_duplicate_status(grammar, ch_family_dict):
    data = copy.deepcopy(ch_family_dict)
    data["statuses"].append(data["statuses"][0].copy())
    lc = Lifecycle.from_family_dict(grammar, data)
    result = lc.validate()
    assert not result.ok
    assert any("duplicate status" in i.message for i in result.issues)


def test_from_family_dict_catches_duplicate_transition(grammar, ch_family_dict):
    data = copy.deepcopy(ch_family_dict)
    data["transitions"].append(data["transitions"][0].copy())
    lc = Lifecycle.from_family_dict(grammar, data)
    result = lc.validate()
    assert not result.ok
    assert any("duplicate transition" in i.message for i in result.issues)


def test_from_family_dict_catches_min_greater_than_max(grammar, ch_family_dict):
    data = copy.deepcopy(ch_family_dict)
    data["state_constraints"][0]["rules"]["related_cis"]["constraints"].append(
        {"statuses": ["lg:statuses/verified"], "cardinality": {"min": 5, "max": 1}}
    )
    lc = Lifecycle.from_family_dict(grammar, data)
    result = lc.validate()
    assert not result.ok
    assert any("min" in i.message and "max" in i.message for i in result.issues)


def test_from_manifest_malformed_families_type(grammar, tmp_path):
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text("schema_version: '1.0'\nfamilies: not_a_list\n")
    with pytest.raises(LanternGrammarLoadError, match="families.*must be a list"):
        Lifecycle.from_manifest(grammar, manifest_path)


def test_validate_unknown_status_in_family(grammar, ch_family_dict):
    data = copy.deepcopy(ch_family_dict)
    data["statuses"][0]["id"] = "lg:statuses/does_not_exist"
    lc = Lifecycle.from_manifest(
        grammar,
        FIXTURE_MANIFEST,
    )
    # Inject bad data directly for bundle-level check
    lc._families["lg:artifacts/ch"] = data
    result = lc.validate()
    assert not result.ok
    assert any("does_not_exist" in i.message for i in result.issues)


def test_validate_unknown_related_family(grammar, ch_family_dict):
    data = copy.deepcopy(ch_family_dict)
    data["state_constraints"][0]["rules"]["related_cis"]["related_family_id"] = "lg:artifacts/does_not_exist"
    lc = Lifecycle.from_manifest(grammar, FIXTURE_MANIFEST)
    lc._families["lg:artifacts/ch"] = data
    result = lc.validate()
    assert not result.ok
    assert any("does_not_exist" in i.message for i in result.issues)


def test_validate_slot_family_inconsistency(grammar, ch_family_dict):
    data = copy.deepcopy(ch_family_dict)
    # Add a second state_constraint entry where related_cis binds a different family
    data["state_constraints"].append(
        {
            "status": "lg:statuses/in_progress",
            "rules": {
                "related_cis": {
                    "related_family_id": "lg:artifacts/ch",  # wrong family for this slot
                    "constraints": [
                        {
                            "statuses": ["lg:statuses/in_progress"],
                            "cardinality": {"min": 1},
                        }
                    ],
                }
            },
        }
    )
    data["statuses"].append({"id": "lg:statuses/in_progress", "label": "In Progress"})
    lc = Lifecycle.from_manifest(grammar, FIXTURE_MANIFEST)
    lc._families["lg:artifacts/ch"] = data
    result = lc.validate()
    assert not result.ok
    assert any("previously bound" in i.message for i in result.issues)


def test_validate_min_model_version_too_high(grammar, ch_family_dict):
    lc = Lifecycle.from_manifest(grammar, FIXTURE_MANIFEST)
    lc._manifest["grammar_compatibility"]["min_model_version"] = "99.0.0"
    result = lc.validate()
    assert not result.ok
    assert any("99.0.0" in i.message for i in result.issues)


def test_validate_min_greater_than_max(grammar, ch_family_dict):
    data = copy.deepcopy(ch_family_dict)
    data["state_constraints"][0]["rules"]["related_cis"]["constraints"].append(
        {"statuses": ["lg:statuses/verified"], "cardinality": {"min": 3, "max": 1}}
    )
    lc = Lifecycle.from_manifest(grammar, FIXTURE_MANIFEST)
    lc._families["lg:artifacts/ch"] = data
    result = lc.validate()
    assert not result.ok
    assert any("min" in i.message and "max" in i.message for i in result.issues)


def test_validate_cardinality_oneof_violation(grammar, ch_family_dict):
    data = copy.deepcopy(ch_family_dict)
    data["state_constraints"][0]["rules"]["related_cis"]["constraints"][0]["cardinality"] = {"exact": 1, "all": True}
    lc = Lifecycle.from_family_dict(grammar, data)
    result = lc.validate()
    assert not result.ok


def test_query_statuses_for(grammar):
    lc = Lifecycle.from_manifest(grammar, FIXTURE_MANIFEST)
    bindings = lc.statuses_for("lg:artifacts/ci")
    assert StatusBinding("lg:statuses/in_progress", "In Progress") in bindings


def test_query_transitions_for(grammar):
    lc = Lifecycle.from_manifest(grammar, FIXTURE_MANIFEST)
    transitions = lc.transitions_for("lg:artifacts/ci")
    assert Transition("lg:statuses/draft", "lg:statuses/candidate") in transitions


def test_query_state_constraints_for(grammar):
    lc = Lifecycle.from_manifest(grammar, FIXTURE_MANIFEST)
    constraints = lc.state_constraints_for("lg:artifacts/ch", "lg:statuses/addressed")
    assert len(constraints) == 1
    sc = constraints[0]
    assert sc.subject_family_id == "lg:artifacts/ch"
    assert sc.status_id == "lg:statuses/addressed"
    assert len(sc.traversals) == 1

    tc = sc.traversals[0]
    assert tc.slot == "related_cis"
    assert tc.related_family_id == "lg:artifacts/ci"
    assert len(tc.rules) == 2

    exact_rule = tc.rules[0]
    assert exact_rule.statuses == ("lg:statuses/verified",)
    assert exact_rule.cardinality.exact == 1
    assert exact_rule.cardinality.is_all is False

    all_rule = tc.rules[1]
    assert all_rule.statuses == ("lg:statuses/verified", "lg:statuses/rejected")
    assert all_rule.cardinality.is_all is True
    assert all_rule.cardinality.exact is None


def test_query_state_constraints_all_statuses(grammar):
    lc = Lifecycle.from_manifest(grammar, FIXTURE_MANIFEST)
    all_constraints = lc.state_constraints_for("lg:artifacts/ch")
    addressed = lc.state_constraints_for("lg:artifacts/ch", "lg:statuses/addressed")
    assert len(all_constraints) >= len(addressed)


def test_public_imports():
    from lantern_grammar import (
        Cardinality,
        CardinalityRule,
        Lifecycle,
        StateConstraint,
        StatusBinding,
        TraversalConstraint,
        Transition,
        ValidationIssue,
        ValidationResult,
    )

    assert all(
        cls is not None
        for cls in [
            Cardinality,
            CardinalityRule,
            Lifecycle,
            StateConstraint,
            StatusBinding,
            TraversalConstraint,
            Transition,
            ValidationIssue,
            ValidationResult,
        ]
    )
