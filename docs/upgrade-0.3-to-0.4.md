# Upgrade guide — 0.3.0 to 0.4.0

This guide covers the breaking changes in the 0.4.0 model and package release and the
steps required to migrate a consumer that targets `lantern-grammar 0.3.0`.

---

## Breaking changes

### 1. Five status entities removed

The five `_initiative`-suffixed status entities have been removed from the model. Any
code or configuration that holds one of these IDs will no longer resolve.

| Removed ID | Generic replacement |
|---|---|
| `lg:statuses/draft_initiative` | `lg:statuses/draft` |
| `lg:statuses/proposed_initiative` | `lg:statuses/proposed` |
| `lg:statuses/ready_initiative` | `lg:statuses/ready` |
| `lg:statuses/in_progress_initiative` | `lg:statuses/in_progress` |
| `lg:statuses/concluded_initiative` | `lg:statuses/concluded` |

**Action required:** Replace every occurrence of a `_initiative`-suffixed ID with the
corresponding generic ID listed above. This includes:

- Runtime configuration files and YAML contracts that enumerate allowed status values.
- Hardcoded status comparisons in application code.
- Database rows or document fields that store status IDs.
- Test fixtures that reference the old IDs.

`lg:statuses/in_progress` and `lg:statuses/concluded` are new in 0.4.0. If your 0.3.0
model accessed those concepts via `in_progress_initiative` or `concluded_initiative`,
the replacement IDs resolve correctly in 0.4.0.

### 2. GT-050 and GT-060 swapped artifact classes

The artifact class each gate operates on has been corrected:

| Gate | 0.3.0 (wrong) | 0.4.0 (correct) |
|---|---|---|
| `lg:gates/gt_050` | Architecture Definition readiness | Requirements Specification readiness |
| `lg:gates/gt_060` | Requirements Specification readiness | Architecture Definition readiness |

**Action required if you hardcoded gate-to-artifact mappings:**

If your tooling queries `grammar.gate_dependencies("lg:gates/gt_050")` and expects
`lg:artifacts/arch` in `requires_input`, that assumption is now wrong. The corrected
mapping is:

- GT-050 requires `lg:artifacts/spec` as input.
- GT-060 requires `lg:artifacts/arch` as input.

Update any code, tests, or configuration that relied on the prior (inverted) mapping.

### 3. Status definition text changed (not a runtime break, but verify)

The `definition` field of `draft`, `proposed`, `ready`, `addressed`, and `verified`
changed to remove the phrases "Change Intent" and "Change Increment". If your tooling
reads or displays status definitions directly from the model, the text will differ.
This is not a structural break but verify display-facing strings in your product.

---

## New features

### New status entities

`lg:statuses/in_progress` and `lg:statuses/concluded` are now first-class generic
status entities. Both are returned by `Grammar.iter_entities(prefix="lg:statuses/")` and
are accessible via `Grammar.get_entity()`.

### New vocabulary terms

`lg:vocab/term_status_candidate`, `lg:vocab/term_status_concluded`, and
`lg:vocab/term_status_in_progress` complete the `term_status_*` coverage. Every generic
status now has a canonical vocabulary term with a display label.

### Lifecycle declaration API

The `Lifecycle` class and nine supporting types are now available in the `lantern_grammar`
package. They provide loading, validation, and querying of lifecycle declaration bundles —
consumer-authored YAML files that declare which
statuses apply to each artifact family, what transitions are permitted, and what
inter-artifact status invariants hold.

See [lifecycle.md](lifecycle.md) for full usage. The quick path:

```python
from lantern_grammar import Grammar, Lifecycle

grammar   = Grammar.load()
lifecycle = Lifecycle.from_manifest(grammar, "lifecycle-policy/manifest.yaml")
result    = lifecycle.validate()
if not result.ok:
    for issue in result.issues:
        print(f"{issue.path}: {issue.message}")
```

The lifecycle bundle JSON Schemas are bundled with the package and accessible via
`Lifecycle.manifest_schema()` and `Lifecycle.family_schema()`.

---

## Migration steps

1. **Update your dependency pin** to `lantern-grammar>=0.4.0`.

2. **Replace `_initiative`-suffixed status IDs** wherever they appear (config files,
   application code, test fixtures, database content). Use the table in breaking change 1.

3. **Check gate assumptions.** If your code tests which artifact a gate requires,
   verify that GT-050 now expects SPEC and GT-060 now expects ARCH.

4. **Replace `artifact_status_contract.yaml` status IDs** (if your product maintains
   such a file). Any `_initiative`-suffixed IDs in that contract must be updated to the
   generic equivalents. Add `in_progress` and `concluded` to the allowed status sets for
   the artifact families that need them.

5. **Optionally adopt the Lifecycle API.** If your product currently maintains a
   hand-rolled artifact-status contract, consider migrating it to a lifecycle bundle. The
   Lifecycle class validates the bundle against the grammar and provides typed query
   access to its declarations.

---

## Verification

After migration, verify with:

```python
from lantern_grammar import Grammar

grammar = Grammar.load()
assert grammar.manifest()["model_version"] == "0.4.0"

# Confirm new statuses are accessible
assert grammar.get_entity("lg:statuses/in_progress") is not None
assert grammar.get_entity("lg:statuses/concluded") is not None

# Confirm removed statuses are gone
assert grammar.get_entity("lg:statuses/draft_initiative") is None

# Confirm corrected gate mapping
deps_050 = grammar.gate_dependencies("lg:gates/gt_050")
assert "lg:artifacts/spec" in deps_050["requires_input"]
deps_060 = grammar.gate_dependencies("lg:gates/gt_060")
assert "lg:artifacts/arch" in deps_060["requires_input"]
```
