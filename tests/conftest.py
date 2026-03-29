"""Shared pytest fixtures for lantern-grammar tests."""

import json
from pathlib import Path

import pytest

from lantern_grammar import Grammar

# ---------------------------------------------------------------------------
# Model-directory fixture
# ---------------------------------------------------------------------------
# Tests that need to load from a specific path use this fixture; tests that
# exercise Grammar.load() (bundled data) can call it directly.

_PROJECT_ROOT = Path(__file__).parent.parent
_MODEL_DIR = _PROJECT_ROOT / "model"


@pytest.fixture(scope="session")
def model_dir() -> Path:
    """Return the path to the authoritative model/ directory."""
    assert _MODEL_DIR.is_dir(), (
        f"model/ not found at {_MODEL_DIR}. "
        "Run tests from the lantern-grammar project root."
    )
    return _MODEL_DIR


@pytest.fixture(scope="session")
def grammar(model_dir: Path) -> Grammar:
    """A Grammar instance loaded from the project model/ directory."""
    return Grammar.from_directory(model_dir)


# ---------------------------------------------------------------------------
# Malformed-model fixtures (created in tmp_path)
# ---------------------------------------------------------------------------

@pytest.fixture()
def empty_dir(tmp_path: Path) -> Path:
    """A directory with no files at all."""
    d = tmp_path / "empty"
    d.mkdir()
    return d


@pytest.fixture()
def dir_missing_manifest(tmp_path: Path) -> Path:
    """A directory with index.json but no manifest.json."""
    d = tmp_path / "no_manifest"
    d.mkdir()
    (d / "index.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
    return d


@pytest.fixture()
def dir_bad_manifest_json(tmp_path: Path) -> Path:
    """A directory with manifest.json that is not valid JSON."""
    d = tmp_path / "bad_json"
    d.mkdir()
    (d / "manifest.json").write_text("{ not valid json !!!", encoding="utf-8")
    (d / "index.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
    return d


@pytest.fixture()
def dir_manifest_missing_fields(tmp_path: Path) -> Path:
    """A directory with a manifest.json that lacks required fields."""
    d = tmp_path / "missing_fields"
    d.mkdir()
    (d / "manifest.json").write_text(
        json.dumps({"representation_version": "0.1.0"}), encoding="utf-8"
    )
    (d / "index.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
    return d


@pytest.fixture()
def dir_index_missing_entries(tmp_path: Path) -> Path:
    """A directory with manifest.json but index.json missing 'entries' key."""
    d = tmp_path / "no_entries"
    d.mkdir()
    (d / "manifest.json").write_text(
        json.dumps({"model_id": "x", "model_version": "0.0.1"}), encoding="utf-8"
    )
    (d / "index.json").write_text(json.dumps({"other": []}), encoding="utf-8")
    return d


@pytest.fixture()
def dir_broken_xref(tmp_path: Path, model_dir: Path) -> Path:
    """A model copy with one relation that references a non-existent entity."""
    import shutil
    d = tmp_path / "broken_xref"
    shutil.copytree(model_dir, d)
    # Corrupt one relation file
    rel_file = d / "objects" / "Relation" / "lg__rel__gt_115.requires_input.ch.json"
    obj = json.loads(rel_file.read_text(encoding="utf-8"))
    obj["source_entity_id"] = "lg:gates/NONEXISTENT_GATE"
    rel_file.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return d
