> **Non-authoritative documentation — not model truth.**
>
> This file is a semantic summary of the gates defined in the Lantern Grammar model. The
> authoritative content is the ECT-conforming JSON objects under `model/objects/Entity/`
> (gate definitions) and `model/objects/Relation/` (gate dependencies). When this document
> conflicts with the model, the model is correct.

# Gate definitions

Lantern Grammar defines seven named gates. Each gate is a semantic checkpoint: a named
concept declaring what artifact inputs, evidence records, and status conditions must be
present before the gate is satisfied. Gates carry no process instructions; they name the
conditions, not the steps.

Gate IDs follow the convention `GT-###`. The numeric ordering is meaningful: lower-numbered
gates precede higher-numbered gates in the overall workflow sequence.

---

## GT-030 — Design Input Pack baseline lock

**Model ID:** `lg:gates/gt_030`

**Purpose:** Establishes that a Design Input Pack (DIP) has been locked as a stable
upstream anchor for downstream derivation work.

**Artifact inputs required:**
- Design Input Pack (`lg:artifacts/dip`)

**Status conditions:**
- DIP: `draft`

**Evidence required:**
- Decision record (`lg:records/dec`)
- Evidence record (`lg:records/ev`)

---

## GT-050 — Requirements Specification readiness

**Model ID:** `lg:gates/gt_050`

**Purpose:** Establishes that a Requirements Specification (SPEC) is complete and stable
enough to be baselined as an upstream input. A locked DIP is required as the approved
upstream anchor for the SPEC being baselined.

**Artifact inputs required:**
- Requirements Specification (`lg:artifacts/spec`)
- Design Input Pack (`lg:artifacts/dip`)

**Status conditions:**
- SPEC: `draft`, `approved`

**Evidence required:**
- Decision record (`lg:records/dec`)
- Evidence record (`lg:records/ev`)

---

## GT-060 — Architecture Definition readiness

**Model ID:** `lg:gates/gt_060`

**Purpose:** Establishes that an Architecture Definition (ARCH) is complete and stable
enough to be baselined as an upstream input. A locked DIP is required as the approved
upstream anchor for the ARCH being baselined.

**Artifact inputs required:**
- Architecture Definition (`lg:artifacts/arch`)
- Design Input Pack (`lg:artifacts/dip`)

**Status conditions:**
- ARCH: `draft`, `approved`

**Evidence required:**
- Decision record (`lg:records/dec`)
- Evidence record (`lg:records/ev`)

---

## GT-110 — Input Kit Readiness (entry gate)

**Model ID:** `lg:gates/gt_110`

**Purpose:** Establishes that a Change Intent (CH) has sufficient upstream inputs to
proceed to design selection. All upstream baseline artifacts (ARCH, SPEC, TD) must be in
an approved state.

**Artifact inputs required:**
- Change Intent (`lg:artifacts/ch`)
- Test Definition (`lg:artifacts/td`)
- Architecture Definition (`lg:artifacts/arch`)
- Requirements Specification (`lg:artifacts/spec`)

**Status conditions:**
- CH: `proposed`
- TD, ARCH, SPEC: `approved`

**Evidence required:**
- Decision record (`lg:records/dec`)
- Evidence record (`lg:records/ev`)

---

## GT-115 — Design Baseline Selection (design lock gate)

**Model ID:** `lg:gates/gt_115`

**Purpose:** Establishes that a single Design Candidate has been selected and a Design
Baseline has been approved, locking the design before implementation begins.

**Artifact inputs required:**
- Change Intent (`lg:artifacts/ch`)
- Design Candidate (`lg:artifacts/dc`)
- Test Definition (`lg:artifacts/td`)
- Architecture Definition (`lg:artifacts/arch`)
- Requirements Specification (`lg:artifacts/spec`)

**Status conditions:**
- CH: `ready`
- DC: `candidate`
- TD, ARCH, SPEC: `approved`

**Evidence required:**
- Decision record (`lg:records/dec`)
- Evidence record (`lg:records/ev`)

---

## GT-120 — Change Increment Selection (implementation selection gate)

**Model ID:** `lg:gates/gt_120`

**Purpose:** Establishes that a single Change Increment (CI) has been selected against a
locked Change Intent, Design Baseline, and Test Definition set, committing an
implementation path.

**Artifact inputs required:**
- Change Intent (`lg:artifacts/ch`)
- Design Baseline (`lg:artifacts/db`)
- Test Definition (`lg:artifacts/td`)
- Change Increment (`lg:artifacts/ci`)

**Status conditions:**
- CH: `ready`
- DB, TD: `approved`
- CI: `candidate`

**Evidence required:**
- Decision record (`lg:records/dec`)
- Evidence record (`lg:records/ev`)

---

## GT-130 — Integration Verification (exit gate)

**Model ID:** `lg:gates/gt_130`

**Purpose:** Establishes that a selected Change Increment has passed integration
verification against the locked CH, Design Baseline, and TD baseline, completing the
governed change cycle.

**Artifact inputs required:**
- Change Intent (`lg:artifacts/ch`)
- Design Baseline (`lg:artifacts/db`)
- Test Definition (`lg:artifacts/td`)
- Change Increment (`lg:artifacts/ci`)

**Status conditions:**
- CH: `ready`
- DB, TD: `approved`
- CI: `selected`

**Evidence required:**
- Decision record (`lg:records/dec`)
- Evidence record (`lg:records/ev`)
