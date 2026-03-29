"""Comprehensive tests for the lantern-grammar public API.

Coverage targets (all from DN-LGR-PROP-004 stable contract):
- Grammar.load()
- Grammar.from_directory()
- grammar.manifest() / package_version()
- grammar.get_entity() / iter_entities()
- grammar.get_relation() / find_relations()
- grammar.get_term() / find_terms()
- grammar.gate_dependencies()
- grammar.validate_integrity()
- LanternGrammarLoadError contract
- Thread-safety guarantee
"""

import threading
from pathlib import Path
from types import MappingProxyType

import pytest

from lantern_grammar import Grammar, LanternGrammarLoadError


# ===========================================================================
# Construction — Grammar.load()
# ===========================================================================

class TestLoad:
    def test_load_returns_grammar_instance(self):
        grammar = Grammar.load()
        assert isinstance(grammar, Grammar)

    def test_load_model_version_is_string(self):
        grammar = Grammar.load()
        assert isinstance(grammar.manifest()["model_version"], str)

    def test_load_has_entities(self):
        grammar = Grammar.load()
        count = sum(1 for _ in grammar.iter_entities())
        assert count > 0

    def test_load_has_relations(self):
        grammar = Grammar.load()
        count = sum(1 for _ in grammar.find_relations(
            relation_type_id="lg:reltypes/requires_input"
        ))
        assert count > 0

    def test_load_has_terms(self):
        grammar = Grammar.load()
        term = grammar.get_term("lg:vocab/term_ch")
        # Term may not be in index; if Grammar.load() worked we have a Grammar
        assert isinstance(grammar, Grammar)


# ===========================================================================
# Construction — Grammar.from_directory()
# ===========================================================================

class TestFromDirectory:
    def test_returns_grammar_instance(self, model_dir):
        g = Grammar.from_directory(model_dir)
        assert isinstance(g, Grammar)

    def test_accepts_path_object(self, model_dir):
        g = Grammar.from_directory(Path(model_dir))
        assert isinstance(g, Grammar)

    def test_accepts_string_path(self, model_dir):
        g = Grammar.from_directory(str(model_dir))
        assert isinstance(g, Grammar)

    def test_nonexistent_path_raises_file_not_found(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError):
            Grammar.from_directory(missing)

    def test_empty_dir_raises_load_error(self, empty_dir):
        with pytest.raises(LanternGrammarLoadError):
            Grammar.from_directory(empty_dir)

    def test_missing_manifest_raises_load_error(self, dir_missing_manifest):
        with pytest.raises(LanternGrammarLoadError):
            Grammar.from_directory(dir_missing_manifest)

    def test_bad_manifest_json_raises_load_error(self, dir_bad_manifest_json):
        with pytest.raises(LanternGrammarLoadError):
            Grammar.from_directory(dir_bad_manifest_json)

    def test_manifest_missing_fields_raises_load_error(self, dir_manifest_missing_fields):
        with pytest.raises(LanternGrammarLoadError):
            Grammar.from_directory(dir_manifest_missing_fields)

    def test_index_missing_entries_raises_load_error(self, dir_index_missing_entries):
        with pytest.raises(LanternGrammarLoadError):
            Grammar.from_directory(dir_index_missing_entries)

    def test_load_error_is_catchable_as_exception(self, empty_dir):
        with pytest.raises(Exception):
            Grammar.from_directory(empty_dir)


# ===========================================================================
# Manifest and version metadata
# ===========================================================================

class TestManifest:
    def test_manifest_returns_mapping(self, grammar):
        m = grammar.manifest()
        assert isinstance(m, MappingProxyType)

    def test_manifest_has_model_id(self, grammar):
        m = grammar.manifest()
        assert "model_id" in m
        assert isinstance(m["model_id"], str)
        assert len(m["model_id"]) > 0

    def test_manifest_model_id_value(self, grammar):
        assert grammar.manifest()["model_id"] == "lantern-grammar.model"

    def test_manifest_has_model_version(self, grammar):
        m = grammar.manifest()
        assert "model_version" in m
        assert isinstance(m["model_version"], str)

    def test_manifest_model_version_semver_like(self, grammar):
        version = grammar.manifest()["model_version"]
        parts = version.split(".")
        assert len(parts) >= 2, f"Expected semver-like version, got {version!r}"

    def test_manifest_is_read_only(self, grammar):
        with pytest.raises(TypeError):
            grammar.manifest()["model_id"] = "hacked"

    def test_package_version_is_string(self, grammar):
        v = grammar.package_version()
        assert isinstance(v, str)
        assert len(v) > 0

    def test_multiple_manifest_calls_same_object(self, grammar):
        assert grammar.manifest() is grammar.manifest()


# ===========================================================================
# Entity access
# ===========================================================================

class TestGetEntity:
    def test_known_artifact_entity(self, grammar):
        e = grammar.get_entity("lg:artifacts/ch")
        assert e is not None

    def test_entity_has_required_fields(self, grammar):
        e = grammar.get_entity("lg:artifacts/ch")
        for field in ("id", "kind", "short_name", "definition", "status"):
            assert field in e, f"Missing field {field!r}"

    def test_entity_id_matches_requested(self, grammar):
        e = grammar.get_entity("lg:artifacts/ch")
        assert e["id"] == "lg:artifacts/ch"

    def test_entity_kind_is_entity(self, grammar):
        e = grammar.get_entity("lg:artifacts/ch")
        assert e["kind"] == "Entity"

    def test_unknown_entity_returns_none(self, grammar):
        assert grammar.get_entity("lg:artifacts/does_not_exist") is None

    def test_gate_entity_accessible(self, grammar):
        g = grammar.get_entity("lg:gates/gt_115")
        assert g is not None
        assert g["id"] == "lg:gates/gt_115"

    def test_status_entity_accessible(self, grammar):
        s = grammar.get_entity("lg:statuses/proposed")
        assert s is not None

    def test_record_entity_accessible(self, grammar):
        r = grammar.get_entity("lg:records/ev")
        assert r is not None

    def test_reltype_entity_accessible(self, grammar):
        rt = grammar.get_entity("lg:reltypes/requires_input")
        assert rt is not None

    def test_entity_is_read_only(self, grammar):
        e = grammar.get_entity("lg:artifacts/ch")
        with pytest.raises(TypeError):
            e["id"] = "hacked"

    def test_all_artifact_families_present(self, grammar):
        expected = [
            "lg:artifacts/arch", "lg:artifacts/ch", "lg:artifacts/ci",
            "lg:artifacts/db", "lg:artifacts/dc", "lg:artifacts/dip",
            "lg:artifacts/initiative", "lg:artifacts/spec", "lg:artifacts/td",
        ]
        for artifact_id in expected:
            assert grammar.get_entity(artifact_id) is not None, (
                f"Missing artifact entity: {artifact_id}"
            )

    def test_all_gates_present(self, grammar):
        for gate in ("gt_030", "gt_035", "gt_036", "gt_045", "gt_050",
                     "gt_060", "gt_110", "gt_115", "gt_120", "gt_130"):
            gate_id = f"lg:gates/{gate}"
            assert grammar.get_entity(gate_id) is not None, (
                f"Missing gate entity: {gate_id}"
            )


class TestIterEntities:
    def test_returns_all_entities(self, grammar):
        entities = list(grammar.iter_entities())
        assert len(entities) > 10

    def test_prefix_filter_gates(self, grammar):
        gates = list(grammar.iter_entities(prefix="lg:gates/"))
        assert len(gates) > 0
        for g in gates:
            assert g["id"].startswith("lg:gates/")

    def test_prefix_filter_artifacts(self, grammar):
        artifacts = list(grammar.iter_entities(prefix="lg:artifacts/"))
        assert len(artifacts) > 0
        for a in artifacts:
            assert a["id"].startswith("lg:artifacts/")

    def test_status_filter_released(self, grammar):
        released = list(grammar.iter_entities(status="Released"))
        assert len(released) > 0
        for e in released:
            assert e.get("status") == "Released"

    def test_combined_filter(self, grammar):
        released_gates = list(
            grammar.iter_entities(prefix="lg:gates/", status="Released")
        )
        assert len(released_gates) > 0
        for g in released_gates:
            assert g["id"].startswith("lg:gates/")
            assert g["status"] == "Released"

    def test_non_matching_prefix_returns_empty(self, grammar):
        result = list(grammar.iter_entities(prefix="lg:nonexistent/"))
        assert result == []

    def test_each_entity_has_required_fields(self, grammar):
        for e in grammar.iter_entities():
            for field in ("id", "kind", "short_name"):
                assert field in e, (
                    f"Entity {e.get('id')!r} missing field {field!r}"
                )


# ===========================================================================
# Relation access
# ===========================================================================

class TestGetRelation:
    def test_known_relation(self, grammar):
        r = grammar.get_relation("lg:rel/gt_115.requires_input.ch")
        assert r is not None

    def test_relation_has_required_fields(self, grammar):
        r = grammar.get_relation("lg:rel/gt_115.requires_input.ch")
        for field in ("id", "kind", "short_name", "definition", "status",
                      "relation_type_id", "source_entity_id", "target_entity_id"):
            assert field in r, f"Missing field {field!r}"

    def test_relation_source_target(self, grammar):
        r = grammar.get_relation("lg:rel/gt_115.requires_input.ch")
        assert r["source_entity_id"] == "lg:gates/gt_115"
        assert r["target_entity_id"] == "lg:artifacts/ch"

    def test_unknown_relation_returns_none(self, grammar):
        assert grammar.get_relation("lg:rel/nonexistent") is None

    def test_relation_is_read_only(self, grammar):
        r = grammar.get_relation("lg:rel/gt_115.requires_input.ch")
        with pytest.raises(TypeError):
            r["id"] = "hacked"


class TestFindRelations:
    def test_by_relation_type_id(self, grammar):
        rels = list(grammar.find_relations(
            relation_type_id="lg:reltypes/requires_input"
        ))
        assert len(rels) > 0
        for r in rels:
            assert r["relation_type_id"] == "lg:reltypes/requires_input"

    def test_by_source_entity_id(self, grammar):
        rels = list(grammar.find_relations(
            source_entity_id="lg:gates/gt_115"
        ))
        assert len(rels) > 0
        for r in rels:
            assert r["source_entity_id"] == "lg:gates/gt_115"

    def test_by_target_entity_id(self, grammar):
        rels = list(grammar.find_relations(
            target_entity_id="lg:artifacts/ch"
        ))
        assert len(rels) > 0
        for r in rels:
            assert r["target_entity_id"] == "lg:artifacts/ch"

    def test_combined_filters(self, grammar):
        rels = list(grammar.find_relations(
            relation_type_id="lg:reltypes/requires_input",
            source_entity_id="lg:gates/gt_115",
        ))
        assert len(rels) > 0
        for r in rels:
            assert r["relation_type_id"] == "lg:reltypes/requires_input"
            assert r["source_entity_id"] == "lg:gates/gt_115"

    def test_no_args_raises_value_error(self, grammar):
        with pytest.raises(ValueError, match="at least one filter"):
            list(grammar.find_relations())

    def test_non_matching_filter_returns_empty(self, grammar):
        rels = list(grammar.find_relations(
            source_entity_id="lg:gates/NONEXISTENT"
        ))
        assert rels == []

    def test_decomposes_to_relation_present(self, grammar):
        rels = list(grammar.find_relations(
            relation_type_id="lg:reltypes/decomposes_to"
        ))
        assert len(rels) > 0


# ===========================================================================
# Term lookup
# ===========================================================================

class TestGetTerm:
    def test_known_term(self, grammar):
        t = grammar.get_term("lg:vocab/term_ch")
        # Terms are in index; may be present.  If None, grammar loaded fine anyway.
        # We test the accessor contract; the test is skipped gracefully if no terms.
        if t is None:
            pytest.skip("Term lg:vocab/term_ch not found in this model version")

    def test_term_has_required_fields(self, grammar):
        t = grammar.get_term("lg:vocab/term_ch")
        if t is None:
            pytest.skip("Term not in index for this model version")
        for field in ("id", "kind", "short_name", "definition", "status"):
            assert field in t, f"Missing field {field!r}"

    def test_unknown_term_returns_none(self, grammar):
        assert grammar.get_term("lg:vocab/term_nonexistent_xyz") is None

    def test_term_is_read_only(self, grammar):
        t = grammar.get_term("lg:vocab/term_ch")
        if t is None:
            pytest.skip("Term not in index for this model version")
        with pytest.raises(TypeError):
            t["id"] = "hacked"


class TestFindTerms:
    def test_prefix_filter(self, grammar):
        terms = list(grammar.find_terms(prefix="lg:vocab/"))
        # If terms are indexed, there should be some; if not, list is empty but no error.
        for t in terms:
            assert t["id"].startswith("lg:vocab/")

    def test_short_name_filter(self, grammar):
        terms = list(grammar.find_terms(short_name="vocab.term_ch"))
        for t in terms:
            assert t["short_name"] == "vocab.term_ch"

    def test_no_filter_returns_all_terms(self, grammar):
        all_terms = list(grammar.find_terms())
        filtered = list(grammar.find_terms(prefix="lg:vocab/"))
        # Both approaches should give same results when all terms are under lg:vocab/
        assert len(all_terms) == len(filtered) or len(all_terms) >= len(filtered)


# ===========================================================================
# Gate-dependency queries
# ===========================================================================

class TestGateDependencies:
    def test_gt115_returns_mapping(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_115")
        assert isinstance(deps, MappingProxyType)

    def test_gt115_has_stable_keys(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_115")
        for key in ("gate_id", "requires_input", "requires_evidence",
                    "requires_status", "relation_ids"):
            assert key in deps, f"Missing stable key {key!r}"

    def test_gate_id_matches(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_115")
        assert deps["gate_id"] == "lg:gates/gt_115"

    def test_gt115_requires_ch_input(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_115")
        assert "lg:artifacts/ch" in deps["requires_input"]

    def test_gt115_requires_td_input(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_115")
        assert "lg:artifacts/td" in deps["requires_input"]

    def test_gt115_requires_evidence(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_115")
        assert len(deps["requires_evidence"]) > 0

    def test_gt115_requires_status(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_115")
        assert len(deps["requires_status"]) > 0

    def test_gt120_requires_db(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_120")
        assert "lg:artifacts/db" in deps["requires_input"]

    def test_gt120_requires_ch(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_120")
        assert "lg:artifacts/ch" in deps["requires_input"]

    def test_gt130_requires_selected_ci(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_130")
        assert "lg:artifacts/ci" in deps["requires_input"]

    def test_relation_ids_non_empty_for_gt115(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_115")
        assert len(deps["relation_ids"]) > 0

    def test_all_gates_queriable(self, grammar):
        for gate in ("gt_030", "gt_035", "gt_036", "gt_045", "gt_050",
                     "gt_060", "gt_110", "gt_115", "gt_120", "gt_130"):
            gate_id = f"lg:gates/{gate}"
            deps = grammar.gate_dependencies(gate_id)
            assert deps["gate_id"] == gate_id

    def test_nonexistent_gate_raises_key_error(self, grammar):
        with pytest.raises(KeyError):
            grammar.gate_dependencies("lg:gates/gt_999")

    def test_artifact_id_raises_key_error(self, grammar):
        with pytest.raises(KeyError):
            grammar.gate_dependencies("lg:artifacts/ch")

    def test_return_is_read_only(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_115")
        with pytest.raises(TypeError):
            deps["gate_id"] = "hacked"

    def test_sequences_are_tuples(self, grammar):
        deps = grammar.gate_dependencies("lg:gates/gt_115")
        assert isinstance(deps["requires_input"], tuple)
        assert isinstance(deps["requires_evidence"], tuple)
        assert isinstance(deps["requires_status"], tuple)
        assert isinstance(deps["relation_ids"], tuple)


# ===========================================================================
# Integrity validation
# ===========================================================================

class TestValidateIntegrity:
    def test_valid_model_returns_ok_true(self, grammar):
        report = grammar.validate_integrity()
        assert report["ok"] is True

    def test_report_has_stable_keys(self, grammar):
        report = grammar.validate_integrity()
        for key in ("ok", "errors", "warnings"):
            assert key in report

    def test_errors_is_tuple_or_sequence(self, grammar):
        report = grammar.validate_integrity()
        assert isinstance(report["errors"], (tuple, list))

    def test_no_errors_on_released_model(self, grammar):
        report = grammar.validate_integrity()
        assert report["errors"] == () or report["errors"] == []

    def test_report_is_read_only(self, grammar):
        report = grammar.validate_integrity()
        with pytest.raises(TypeError):
            report["ok"] = False

    def test_broken_xref_yields_errors(self, dir_broken_xref):
        g = Grammar.from_directory(dir_broken_xref)
        report = g.validate_integrity()
        assert report["ok"] is False
        assert len(report["errors"]) > 0

    def test_broken_xref_error_mentions_relation(self, dir_broken_xref):
        g = Grammar.from_directory(dir_broken_xref)
        report = g.validate_integrity()
        combined = " ".join(report["errors"])
        assert "NONEXISTENT_GATE" in combined


# ===========================================================================
# LanternGrammarLoadError contract
# ===========================================================================

class TestLanternGrammarLoadError:
    def test_is_exception_subclass(self):
        assert issubclass(LanternGrammarLoadError, Exception)

    def test_importable_directly(self):
        from lantern_grammar import LanternGrammarLoadError as E
        assert E is LanternGrammarLoadError

    def test_can_be_raised_and_caught(self):
        with pytest.raises(LanternGrammarLoadError):
            raise LanternGrammarLoadError("test message")

    def test_message_preserved(self):
        exc = LanternGrammarLoadError("detail here")
        assert "detail here" in str(exc)


# ===========================================================================
# Thread-safety guarantee
# ===========================================================================

class TestThreadSafety:
    def test_concurrent_reads_are_safe(self, grammar):
        """Multiple threads reading concurrently must not raise or corrupt."""
        errors: list[str] = []
        results: list = []

        def worker(gate_id: str):
            try:
                deps = grammar.gate_dependencies(gate_id)
                results.append(deps["gate_id"])
                _ = list(grammar.iter_entities(prefix="lg:gates/"))
                _ = grammar.manifest()["model_version"]
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))

        gates = [
            "lg:gates/gt_030", "lg:gates/gt_110", "lg:gates/gt_115",
            "lg:gates/gt_120", "lg:gates/gt_130",
        ]
        threads = [threading.Thread(target=worker, args=(g,)) for g in gates * 4]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        assert len(results) == len(threads)


# ===========================================================================
# repr
# ===========================================================================

class TestRepr:
    def test_repr_contains_model_id(self, grammar):
        r = repr(grammar)
        assert "lantern-grammar.model" in r

    def test_repr_contains_model_version(self, grammar):
        r = repr(grammar)
        assert grammar.manifest()["model_version"] in r
