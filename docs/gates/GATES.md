> **OPTIONAL / Non-authoritative documentation — not model truth.**
>
> This file is preserved for context only. The authoritative semantic content is in the ECT-conforming model
> objects under `model/`. This document is a *semantic summary* of gate concepts and
> their dependencies on artifact classes, record classes, and status values. It is not a
> workflow/process specification.

# GATES - Gate Definitions

This document defines gate concepts and their semantic dependencies.

Gate ID convention: `GT-###`

## GT-030: Design Input Pack Lock (DIP baseline lock)
Purpose:
- Define the concept of establishing a Design Input Pack (DIP) baseline as an upstream anchor for downstream derivation.

Semantic dependencies:
- Artifact classes referenced:
  - Design Input Pack (DIP-####)
- Status values referenced:
  - Draft

Record classes referenced:
- Evidence record(s) (EV-###)
- Decision record(s) (DEC-###)

Essence alignment:
- Requirements
- Stakeholders
- Way of Working

## GT-035: SPEC Draft Derivation Preflight (from locked DIP)
Purpose:
- Define the concept of checking a SPEC draft for derivation linkage to a DIP baseline.

Semantic dependencies:
- Artifact classes referenced:
  - Design Input Pack (DIP-####)
  - Requirements Specification (SPEC-####)
- Status values referenced:
  - Approved (for DIP)
  - Draft (for SPEC)

Record classes referenced:
- Evidence record(s) (EV-###)
- Decision record(s) (DEC-###)

Essence alignment:
- Requirements
- Way of Working

## GT-036: ARCH Draft Derivation Preflight (from locked DIP)
Purpose:
- Define the concept of checking an ARCH draft for derivation linkage to a DIP baseline.

Semantic dependencies:
- Artifact classes referenced:
  - Design Input Pack (DIP-####)
  - Architecture Definition (ARCH-####)
- Status values referenced:
  - Approved (for DIP)
  - Draft (for ARCH)

Record classes referenced:
- Evidence record(s) (EV-###)
- Decision record(s) (DEC-###)

Essence alignment:
- Software System
- Way of Working

## GT-045: DIP/SPEC/ARCH Coherence Preflight
Purpose:
- Define the concept of checking semantic coherence between a DIP and its derived SPEC and ARCH.

Semantic dependencies:
- Artifact classes referenced:
  - Design Input Pack (DIP-####)
  - Requirements Specification (SPEC-####)
  - Architecture Definition (ARCH-####)
- Status values referenced:
  - Approved (for DIP)
  - Draft (for SPEC, ARCH)

Record classes referenced:
- Evidence record(s) (EV-###)
- Decision record(s) (DEC-###)

Essence alignment:
- Requirements
- Software System
- Way of Working


## GT-050: Architecture Definition Readiness (ARCH baseline readiness)
Purpose:
- Define the concept of ARCH baseline readiness as a prerequisite input for downstream change work.

Semantic dependencies:
- Artifact classes referenced:
  - Architecture Definition (ARCH-####)
- Status values referenced:
  - Draft
  - Approved
  - Superseded

Record classes referenced:
- Evidence record(s) (EV-###)
- Decision record(s) (DEC-###)

Essence alignment:
- Software System
- Way of Working

## GT-060: Requirements Specification Readiness (SPEC baseline readiness)
Purpose:
- Define the concept of SPEC baseline readiness as a prerequisite input for downstream change work.

Semantic dependencies:
- Artifact classes referenced:
  - Requirements Specification (SPEC-####)
- Status values referenced:
  - Draft
  - Approved
  - Superseded

Record classes referenced:
- Evidence record(s) (EV-###)
- Decision record(s) (DEC-###)

Essence alignment:
- Requirements
- Stakeholders
- Way of Working

## GT-110: Input Kit Readiness (Entry Gate)
Purpose:
- Define the concept of CH input-kit sufficiency for proceeding to CI authoring.

Semantic dependencies:
- Artifact classes referenced:
  - Change Intent (CH-####)
  - (Optional) Architecture Definition (ARCH-####)
  - (Optional) Requirements Specification (SPEC-####)
  - (Optional) Issue (IS-####)
- Status values referenced:
  - Proposed (for CH)
  - Ready
  - Approved (for ARCH/SPEC)
  - Draft (for ARCH/SPEC)
  - Superseded (for ARCH/SPEC)
  - Addressed (for dependency CH, if referenced)

Record classes referenced:
- Evidence record(s) (EV-###)
- Decision record(s) (DEC-###)

Essence alignment:
- Requirements
- Stakeholders
- Way of Working

## GT-120: Change Increment Selection (Selection Gate)
Purpose:
- Define the concept of selecting a single CI candidate to address a CH.

Semantic dependencies:
- Artifact classes referenced:
  - Change Intent (CH-####)
  - Change Increment (CI-####-*)
- Status values referenced:
  - Ready (for CH)
  - Candidate
  - Selected
  - Rejected

Record classes referenced:
- Evidence record(s) (EV-###)
- Decision record(s) (DEC-###)

Essence alignment:
- Requirements
- Work
- Way of Working

## GT-130: Integration Verification (Exit Gate)
Purpose:
- Define the concept of verifying integration for a selected CI and validating the target signal.

Semantic dependencies:
- Artifact classes referenced:
  - Change Intent (CH-####)
  - Change Increment (CI-####-*)
- Status values referenced:
  - Ready (for CH)
  - Selected (for CI)
  - Verified
  - Addressed

Record classes referenced:
- Evidence record(s) (EV-###)
- Decision record(s) (DEC-###)

Essence alignment:
- Software System
- Requirements
- Work