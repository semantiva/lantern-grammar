# Lifecycle declarations

Lantern Grammar publishes a JSON Schema for lifecycle declarations. A lifecycle
declaration is a directory bundle declaring, per artifact family:

- which statuses apply,
- which status transitions are permitted, and
- which inter-artifact status constraints hold as workspace invariants.

The current schema version is **1.0**. Two schemas are published:

- `lantern_grammar/_schemas/gscld-manifest-1.0.schema.json` — validates `manifest.yaml`
- `lantern_grammar/_schemas/gscld-family-1.0.schema.json` — validates each family file

(The `gscld-` prefix in those filenames is an internal schema identifier; in code and
prose use `Lifecycle.manifest_schema()` and `Lifecycle.family_schema()` to access them.)

## Bundle layout

```
lifecycle-policy/
  manifest.yaml     # schema_version, grammar_compatibility, list of family files
  ch.yaml
  ci.yaml
  ...
```

Each family file declares `id`, `statuses`, `transitions`, and `state_constraints`.

## Loading and validating

```python
from lantern_grammar import Grammar, Lifecycle

grammar = Grammar.load()
lifecycle = Lifecycle.from_manifest(grammar, "lifecycle-policy/manifest.yaml")
result = lifecycle.validate()
if not result.ok:
    for issue in result.issues:
        print(f"{issue.path}: {issue.message}")
```

For per-file structural validation without a full bundle:

```python
import yaml
with open("lifecycle-policy/ch.yaml") as f:
    data = yaml.safe_load(f)
lc = Lifecycle.from_family_dict(grammar, data)
result = lc.validate()  # structural only; no cross-file checks
```

## State constraints and slot names

A `state_constraint` entry holds a `rules` map. Each key is a **slot name** — a
consumer-chosen identifier scoped to the family (e.g. `related_cis`,
`design_baseline_ref`). The slot value declares the related artifact family and a list of
cardinality rules that are AND-combined.

```yaml
state_constraints:
  - status: lg:statuses/addressed
    rules:
      related_cis:
        related_family_id: lg:artifacts/ci
        constraints:
          - statuses: [lg:statuses/verified]
            cardinality: {exact: 1}
          - statuses: [lg:statuses/verified, lg:statuses/rejected]
            cardinality: {all: true}
```

Cardinality forms (mutually exclusive):

- `exact: N` — exactly N related artifacts.
- `min: N` and/or `max: N` — at least / at most / range.
- `all: true` — every related artifact has a status in `statuses`.
- `none: true` — no related artifact has a status in `statuses`.

## Querying

```python
lifecycle.artifact_families()
lifecycle.statuses_for("lg:artifacts/ci")
lifecycle.transitions_for("lg:artifacts/ci")

constraints = lifecycle.state_constraints_for(
    "lg:artifacts/ch", "lg:statuses/addressed"
)
for sc in constraints:
    for tc in sc.traversals:
        print(tc.slot, tc.related_family_id)
        for rule in tc.rules:
            print(rule.statuses, rule.cardinality)
```

See `tests/fixtures/lifecycle-policy/` for a structurally valid example bundle.

For the structural specification, see
`lantern-grammar-governance/decisions/DN-LGR-PROP-007__grammar_lifecycle_declaration_schema.md`.
