# Lantern Grammar

**The authoritative language of governed development.**

Lantern Grammar defines the authoritative semantics of artifacts, gates, statuses, and relations used across the Lantern governed-workflow surface. It is expressed as an ECT-conforming model artifact set and evolves through structured change control.

## What it defines

- **Artifact classes** — the recognized artifact kinds in the workflow (CH, CI, DB, DC, DIP, SPEC, ARCH, TD, Initiative, Issue, Question, EV, DEC)
- **Gate entities** — the named semantic checkpoints (GT-030 through GT-130) and their input dependencies
- **Status values** — the lifecycle states artifacts may occupy
- **Relation types** — `requires_input`, `requires_evidence`, `requires_status`, `decomposes_to`
- **Vocabulary terms** — canonical definitions for each artifact and status class

## Repository layout

```
model/
  manifest.json       model identity and namespace declaration
  index.json          flat index of all objects with locators
  objects/
    Entity/           entity objects (artifacts, gates, statuses, relation types)
    Relation/         relation instances encoding the semantic dependency graph
    Term/             vocabulary term definitions
docs/
  gates/GATES.md      non-authoritative semantic summary of gate definitions
```

## Authoritative semantics

The ECT-conforming JSON objects under `model/` are the model truth. `docs/` content is documentation only and is not model truth.