# Lantern Grammar — documentation

This directory contains non-authoritative documentation for the Lantern Grammar model
and its Python package. The authoritative semantic content is always the ECT-conforming
JSON objects under `model/`.

## What to read first

If you are new to Lantern Grammar, start here:

| Document | Purpose |
|---|---|
| [introduction.md](introduction.md) | What Lantern Grammar is, how the model is composed, and the core concepts |
| [../README.md](../README.md) | Installation, basic API usage, and release notes |

## Reference

| Document | Purpose |
|---|---|
| [gates/GATES.md](gates/GATES.md) | Semantic summary of each gate — its purpose and artifact dependencies |
| [lifecycle.md](lifecycle.md) | How to author and validate a lifecycle bundle |

## Migration

| Document | Purpose |
|---|---|
| [upgrade-0.3-to-0.4.md](upgrade-0.3-to-0.4.md) | Breaking changes and migration steps from 0.3.0 to 0.4.0 |

## Notes

- All documents in `docs/` are for human orientation only.
- Do not use prose in `docs/` as a source of truth for tooling. Read the model objects.
- When a doc conflicts with the model, the model is correct.
