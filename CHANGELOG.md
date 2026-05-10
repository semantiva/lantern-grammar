# Changelog — Lantern Grammar

All notable changes to the Lantern Grammar model and Python package are recorded here.

Format: `[package version] — model version` | release date

---

## [0.4.0] — model 0.4.0 | 2026-05-10

### Model changes

#### Complete generic status vocabulary (PROP-005)

The `_initiative`-suffixed status entities have been removed. Their generic equivalents
now cover all artifact families without a suffix.

**Removed status entities (5):**
- `lg:statuses/draft_initiative`
- `lg:statuses/proposed_initiative`
- `lg:statuses/ready_initiative`
- `lg:statuses/in_progress_initiative`
- `lg:statuses/concluded_initiative`

**Added status entities (2):**
- `lg:statuses/in_progress` — an artifact is in active execution following governed
  selection or readiness confirmation, before a completion or verification gate.
- `lg:statuses/concluded` — a bounded lifecycle object has reached its terminal state.

**Broadened definitions (5):** The definitions of `draft`, `proposed`, `ready`,
`addressed`, and `verified` previously referenced "Change Intent" or "Change Increment"
by name. They now use family-agnostic language applicable to any artifact class.

**Added vocabulary terms (3):** `lg:vocab/term_status_candidate`,
`lg:vocab/term_status_concluded`, `lg:vocab/term_status_in_progress` complete the
`term_status_*` coverage. All twelve generic status entities now have a corresponding
canonical vocabulary term.

**Generic status vocabulary — authoritative list (12 entities):**

| Entity ID | Label |
|---|---|
| `lg:statuses/addressed` | Addressed |
| `lg:statuses/approved` | Approved |
| `lg:statuses/candidate` | Candidate |
| `lg:statuses/concluded` | Concluded |
| `lg:statuses/draft` | Draft |
| `lg:statuses/in_progress` | In Progress |
| `lg:statuses/proposed` | Proposed |
| `lg:statuses/ready` | Ready |
| `lg:statuses/rejected` | Rejected |
| `lg:statuses/selected` | Selected |
| `lg:statuses/superseded` | Superseded |
| `lg:statuses/verified` | Verified |

#### SPEC/ARCH gate ordering correction (PROP-006)

GT-050 and GT-060 were mapped to the wrong artifact families in the prior model. The
assignment is now corrected to reflect that SPEC is semantically upstream of ARCH.

**GT-050** — now declares **Requirements Specification Readiness** (was Architecture
Definition Readiness). Requires a SPEC artifact as input; the DIP-input relation prose
updated accordingly.

**GT-060** — now declares **Architecture Definition Readiness** (was Requirements
Specification Readiness). Requires an ARCH artifact as input; the DIP-input relation
prose updated accordingly.

### Python package changes

#### New public API: `Lifecycle` (PROP-007)

The `Lifecycle` class and nine supporting types are now exported from `lantern_grammar`.
They implement loading, validating, and querying lifecycle declaration bundles.

**New exports:** `Lifecycle`, `StateConstraint`, `TraversalConstraint`, `CardinalityRule`,
`Cardinality`, `StatusBinding`, `Transition`, `ValidationResult`, `ValidationIssue`.

Two JSON Schemas are bundled with the package:
- `gscld-manifest-1.0.schema.json` — validates the lifecycle bundle `manifest.yaml`
- `gscld-family-1.0.schema.json` — validates each family declaration file

**New runtime dependencies:** `jsonschema>=4.0`, `pyyaml>=6.0`.

See [docs/lifecycle.md](docs/lifecycle.md) for usage and
[docs/upgrade-0.3-to-0.4.md](docs/upgrade-0.3-to-0.4.md) for migration guidance.

---

## [0.3.0] — model 0.3.0

First published release. Establishes the stable `Grammar` public API contract
(`Grammar.load()`, `from_directory()`, `get_entity()`, `iter_entities()`,
`get_relation()`, `find_relations()`, `get_term()`, `find_terms()`,
`gate_dependencies()`, `validate_integrity()`, `manifest()`, `package_version()`).
