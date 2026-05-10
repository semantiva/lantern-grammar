# Introduction to Lantern Grammar

## What it is

Lantern Grammar is the authoritative semantic vocabulary for the Lantern governed-workflow
surface. It defines the named kinds of artifacts, the named checkpoints (gates) between
workflow stages, the lifecycle states an artifact may occupy, the types of relationships
between artifacts and gates, and the canonical vocabulary terms that bind natural-language
labels to those concepts.

Every system that participates in a Lantern-governed workflow — runtime engines,
validation tools, consumer configuration — speaks this vocabulary. Lantern Grammar is the
shared dictionary that makes their assertions interoperable.

## What it is not

Lantern Grammar does not define:

- **Workflow process** — the sequence of steps a team executes. The grammar names the
  checkpoints; a consuming product decides what work precedes each one.
- **Artifact content schema** — what fields a CH or CI must carry. The grammar names the
  artifact class; the class schema is owned by the consuming product.
- **Runtime posture** — whether a workspace runs in a governed or ungoverned mode. That
  decision is made by the runtime, not the grammar.
- **Instance data** — the actual CH-0001 or CI-0042 instances that live in a project.
  The grammar defines the kinds; instances are created and tracked by consumers.

## Model composition

The grammar model is a set of JSON objects stored under `model/`. Each object has a
stable URI-style identifier, a `kind` discriminator, a human-readable `definition`, and a
`status` field. The model is indexed in `model/index.json` for fast lookup.

There are three object kinds in the current model:

### Entity

An `Entity` is a named semantic concept. Entities carry an `id`, `kind`, `short_name`,
`definition`, and `status`. Gate entities additionally carry a `relation_ids` list that
enumerates the relations attached to that gate.

The model groups entities by namespace prefix:

| Prefix | Category | Examples |
|---|---|---|
| `lg:artifacts/` | Artifact classes | `lg:artifacts/ch`, `lg:artifacts/ci`, `lg:artifacts/spec` |
| `lg:gates/` | Semantic checkpoints | `lg:gates/gt_115`, `lg:gates/gt_120` |
| `lg:statuses/` | Lifecycle states | `lg:statuses/draft`, `lg:statuses/verified` |
| `lg:reltypes/` | Relation types | `lg:reltypes/requires_input`, `lg:reltypes/decomposes_to` |
| `lg:records/` | Record classes | `lg:records/ev`, `lg:records/dec` |

### Relation

A `Relation` is a directed, typed link between two entities. Every relation has a
`source_entity_id`, a `target_entity_id`, and a `relation_type_id` that names the
semantic role of the link. The four relation types in the current model are:

| Relation type | Meaning |
|---|---|
| `lg:reltypes/requires_input` | The source gate requires the target artifact as a direct input |
| `lg:reltypes/requires_evidence` | The source gate requires the target record class as evidence |
| `lg:reltypes/requires_status` | The source gate requires the target status to be satisfied |
| `lg:reltypes/decomposes_to` | The source artifact decomposes into instances of the target artifact class |

Relation instances are stored in `model/objects/Relation/` and referenced from gate
entities via `relation_ids`.

### Term

A `Term` is a vocabulary entry that binds a natural-language label and definition to one
or more entity IDs via `denotes_entity_ids`. Terms are stored in `model/objects/Term/`
and are the canonical source for display labels.

The `lg:vocab/term_status_*` group provides one term per generic status entity, giving
each a canonical display label (e.g. `lg:vocab/term_status_in_progress` → "In Progress").

## Artifact classes

The current model defines the following artifact classes:

| ID | Full name |
|---|---|
| `lg:artifacts/arch` | Architecture Definition |
| `lg:artifacts/ch` | Change Intent |
| `lg:artifacts/ci` | Change Increment |
| `lg:artifacts/db` | Design Baseline |
| `lg:artifacts/dc` | Design Candidate |
| `lg:artifacts/dip` | Design Input Pack |
| `lg:artifacts/initiative` | Initiative |
| `lg:artifacts/issue` | Issue |
| `lg:artifacts/question` | Question |
| `lg:artifacts/spec` | Requirements Specification |
| `lg:artifacts/td` | Test Definition |

## Lifecycle statuses

The current model defines twelve generic lifecycle statuses, applicable to any artifact
class. Status applicability per artifact class is declared by the consumer in a lifecycle
declaration (see [lifecycle.md](lifecycle.md)).

| ID | Label | Meaning |
|---|---|---|
| `lg:statuses/draft` | Draft | Being authored; not yet baselined or submitted for review |
| `lg:statuses/proposed` | Proposed | Submitted for review or gate evaluation; readiness gate not yet passed |
| `lg:statuses/ready` | Ready | Passed its readiness gate; eligible for governed downstream progression |
| `lg:statuses/candidate` | Candidate | Nominated as a candidate for selection at a gate |
| `lg:statuses/selected` | Selected | Chosen at a selection gate for downstream execution |
| `lg:statuses/in_progress` | In Progress | In active execution following governed selection or readiness confirmation |
| `lg:statuses/approved` | Approved | Passed approval review |
| `lg:statuses/verified` | Verified | Passed integration verification |
| `lg:statuses/addressed` | Addressed | Addressed by a verified downstream increment |
| `lg:statuses/rejected` | Rejected | Evaluated and not selected |
| `lg:statuses/superseded` | Superseded | Replaced by a newer version; no longer active |
| `lg:statuses/concluded` | Concluded | Reached terminal state — intended outcome complete or formally closed |

## Gates

Gates are named semantic checkpoints in the workflow. Each gate in the model declares
what artifact inputs it requires, what record evidence it needs, and what status
constraints must hold before the gate is satisfied. See [gates/GATES.md](gates/GATES.md)
for the full description of each gate.

The gates in the current model are:

| Gate ID | Semantic purpose |
|---|---|
| `lg:gates/gt_030` | Design Input Pack baseline lock |
| `lg:gates/gt_050` | Requirements Specification readiness |
| `lg:gates/gt_060` | Architecture Definition readiness |
| `lg:gates/gt_110` | Input Kit Readiness (entry gate) |
| `lg:gates/gt_115` | Design Baseline Selection (design lock gate) |
| `lg:gates/gt_120` | Change Increment Selection (implementation selection gate) |
| `lg:gates/gt_130` | Integration Verification (exit gate) |

## Version and identity

The model has its own version (`model_version` in `model/manifest.json`), separate from
the Python package version. Both follow semver. The pre-commit hook enforces that the two
versions are equal at each commit; they move together.

The model namespace prefix is `lg`, bound to
`https://lantern.semantiva.dev/grammar/ns#`.

## Python API

The `lantern_grammar` Python package exposes the model through a stable, read-only API.
See the [README](../README.md) for installation and basic usage. The main entry points are:

```python
from lantern_grammar import Grammar, Lifecycle

# Load the bundled model
grammar = Grammar.load()

# Query entities, relations, terms
entity = grammar.get_entity("lg:artifacts/ch")
deps   = grammar.gate_dependencies("lg:gates/gt_115")

# Load and validate a consumer lifecycle-policy bundle
lifecycle = Lifecycle.from_manifest(grammar, "lifecycle-policy/manifest.yaml")
result    = lifecycle.validate()
```
