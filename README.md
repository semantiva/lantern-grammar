# Lantern Grammar

**The authoritative language of governed development.**

Lantern Grammar defines the authoritative semantics of artifacts, gates, statuses, and
relations used across the Lantern governed-workflow surface. It is expressed as an
ECT-conforming model artifact set and evolves through structured change control.

## What it defines

- **Artifact classes** — the recognized artifact kinds in the workflow (CH, CI, DB, DC,
  DIP, SPEC, ARCH, TD, Initiative, Issue, Question, EV, DEC)
- **Gate entities** — the named semantic checkpoints (GT-030 through GT-130) and their
  input, evidence, and status dependencies
- **Status values** — twelve generic lifecycle states that artifacts may occupy
- **Relation types** — `requires_input`, `requires_evidence`, `requires_status`,
  `decomposes_to`
- **Vocabulary terms** — canonical labels and definitions for each artifact class and
  status value

## Documentation

| Document | Purpose |
|---|---|
| [docs/introduction.md](docs/introduction.md) | Model composition, core concepts, artifact classes, statuses, gates |
| [docs/gates/GATES.md](docs/gates/GATES.md) | Semantic summary of each gate |
| [docs/lifecycle.md](docs/lifecycle.md) | Authoring and validating lifecycle-policy bundles |
| [docs/upgrade-0.3-to-0.4.md](docs/upgrade-0.3-to-0.4.md) | Migration guide from 0.3.0 to 0.4.0 |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

## Repository layout

```
model/
  manifest.json           model identity, version, and namespace declaration
  index.json              flat index of all objects with file locators
  objects/
    Entity/               entities: artifacts, gates, statuses, relation types, records
    Relation/             typed directed links encoding the semantic dependency graph
    Term/                 vocabulary terms with canonical labels
docs/
  index.md                documentation entry page
  introduction.md         model composition and core concepts
  gates/GATES.md          semantic summary of each gate
  lifecycle.md            lifecycle-policy bundle authoring and validation
  upgrade-0.3-to-0.4.md   migration guide
src/
  lantern_grammar/        Python package
    _grammar.py           Grammar class (read-only model projection)
    _lifecycle.py         Lifecycle class (lifecycle bundle loader and validator)
    _schemas/             bundled JSON Schemas for the lifecycle bundle manifest and family files
tests/
  test_grammar.py         Grammar API tests
  test_lifecycle.py       Lifecycle API tests
  fixtures/               test fixture bundles
CHANGELOG.md              release history
```

## Authoritative semantics

The ECT-conforming JSON objects under `model/` are the model truth. `docs/` content is
documentation only and is not model truth.

---

## Python package

The `lantern-grammar` Python package exposes the model through a stable, read-only API.
Consumers should use this API rather than parsing the `model/` JSON files directly.

### Requirements

- Python ≥ 3.11

### Installation

```bash
# Install from the repository (editable, for development)
pip install -e .

# Install a released distribution
pip install lantern-grammar
```

### Grammar API — basic usage

```python
from lantern_grammar import Grammar, LanternGrammarLoadError

# Load the model bundled with the installed distribution
grammar = Grammar.load()

# Inspect manifest and version
manifest = grammar.manifest()
print(manifest["model_id"])       # "lantern-grammar.model"
print(manifest["model_version"])  # "0.4.0"
print(grammar.package_version())  # "0.4.0"

# Validate before using in CI or tooling
report = grammar.validate_integrity()
if not report["ok"]:
    raise RuntimeError(f"Lantern Grammar invalid: {report['errors']}")

# Resolve a model entity
ch = grammar.get_entity("lg:artifacts/ch")
print(ch["definition"])

# Iterate all gates
for gate in grammar.iter_entities(prefix="lg:gates/", status="Released"):
    print(gate["id"], "-", gate["definition"][:60])

# Query what GT-115 requires as inputs
deps = grammar.gate_dependencies("lg:gates/gt_115")
print("GT-115 requires inputs:", deps["requires_input"])
print("GT-115 requires statuses:", deps["requires_status"])

# Find all relations from GT-120
rels = list(grammar.find_relations(source_entity_id="lg:gates/gt_120"))
for r in rels:
    print(r["relation_type_id"], "->", r["target_entity_id"])

# Term lookup
term = grammar.get_term("lg:vocab/term_ch")
if term:
    print(term["definition"])
```

### Loading from an explicit directory

For local validation, development fixtures, or consumer smoke tests:

```python
from pathlib import Path
from lantern_grammar import Grammar, LanternGrammarLoadError

try:
    grammar = Grammar.from_directory(Path("path/to/lantern-grammar/model"))
except FileNotFoundError:
    print("directory not found")
except LanternGrammarLoadError as exc:
    print(f"model invalid: {exc}")
```

### Lifecycle API — lifecycle bundle loading and validation

The `Lifecycle` class loads and validates lifecycle declaration bundles. A lifecycle bundle
is a consumer-authored directory that declares, per artifact family, which statuses apply,
what transitions are permitted, and what inter-artifact status invariants hold.

```python
from lantern_grammar import Grammar, Lifecycle

grammar = Grammar.load()

# Load a full bundle from a manifest file
lifecycle = Lifecycle.from_manifest(grammar, "lifecycle-policy/manifest.yaml")

# Two-level validation: per-file JSON Schema + bundle-level referential checks
result = lifecycle.validate()
if not result.ok:
    for issue in result.issues:
        print(f"{issue.path}: {issue.message}")

# Query declarations
families    = lifecycle.artifact_families()
statuses    = lifecycle.statuses_for("lg:artifacts/ch")
transitions = lifecycle.transitions_for("lg:artifacts/ch")

# Query inter-artifact constraints for a given status
constraints = lifecycle.state_constraints_for("lg:artifacts/ch", "lg:statuses/addressed")
for sc in constraints:
    for tc in sc.traversals:
        print(f"slot '{tc.slot}' → {tc.related_family_id}")
        for rule in tc.rules:
            print(f"  {rule.statuses} cardinality={rule.cardinality}")
```

For per-file structural validation without a full bundle:

```python
import yaml
with open("lifecycle-policy/ch.yaml") as f:
    data = yaml.safe_load(f)
lc = Lifecycle.from_family_dict(grammar, data)
result = lc.validate()  # structural only; no cross-file checks
```

Two JSON Schemas are accessible for direct integration:

```python
manifest_schema = Lifecycle.manifest_schema()  # validates manifest.yaml
family_schema   = Lifecycle.family_schema()    # validates each family file
```

See [docs/lifecycle.md](docs/lifecycle.md) for the full bundle format specification.

### Authority boundary

The `Grammar` API is a **read-only projection** over the authoritative `model/`
artifacts. It does not invent or reinterpret model meaning.

What it provides:
- model entities (artifacts, gates, statuses, relation types, record classes)
- model relations
- vocabulary terms
- manifest and version metadata
- integrity validation
- gate-dependency queries

What stays outside this package:
- workbench IDs and entry/exit policy
- intent classification
- runtime posture and stage resolution
- workflow resource grouping
- guided execution logic

### Running the tests

```bash
pip install -e ".[dev]"
pytest
```

### Release readiness

The authoritative Python package version source is `[project].version` in
`pyproject.toml`. The authoritative semantic model version source is `model_version` in
`model/manifest.json`. A pre-commit hook enforces that the two values are equal at every
commit.

Run the same checks locally that the CI release lane enforces:

```bash
pip install -e ".[dev,release]"
python scripts/check_version_alignment.py --require-package-model-equality
pylint --fail-under=7.5 src/lantern_grammar/
ruff check src/lantern_grammar/ tests/ scripts/ setup.py
mypy src/lantern_grammar/
black --check src/lantern_grammar/ tests/ scripts/ setup.py
python scripts/check_license_headers.py
coverage run -m pytest --maxfail=1 -q
coverage report
python -m build
python -m twine check dist/*

python -m venv .venv-smoke
. .venv-smoke/bin/activate
python -m pip install --upgrade pip
python -m pip install dist/*.whl
python scripts/smoke_test_installed_package.py \
    --expected-package-version "$(python scripts/check_version_alignment.py --print-package-version)" \
    --expected-model-version "$(python scripts/check_version_alignment.py --print-model-version)"
python scripts/generate_license_report.py --output artifacts/license-report.json
deactivate
python scripts/generate_sbom.py --python .venv-smoke/bin/python --output artifacts/sbom.cyclonedx.json
```

### Publishing

```bash
PACKAGE_VERSION="$(python scripts/check_version_alignment.py --print-package-version)"
git tag -a "v${PACKAGE_VERSION}" -m "lantern-grammar ${PACKAGE_VERSION}"
git push origin "v${PACKAGE_VERSION}"
```

The tagged GitHub Actions run will re-run lint, typing, tests, build, `twine check`, and
clean-environment smoke validation, then publish verified distributions to PyPI via
GitHub OIDC trusted publishing.

### Compatibility posture

The `Grammar` class, the `Lifecycle` class, and the methods documented above constitute
the **stability-governed public core** (`lantern_grammar` namespace). Breaking changes to
this core require a major version increment. Additive stable-core changes may land in
minor versions.

## License

Lantern Grammar is released under the **Apache License 2.0**.

See [LICENSE](LICENSE) for the full license text.

**Copyright 2025 Lantern Authors**
