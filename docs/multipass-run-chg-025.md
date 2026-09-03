# Multipass Validation Run Record — CHG-025

**Run ID:** `RUN-CHG-025`
**Executed:** 2026-09-02
**Supersedes:** [`multipass-run-chg-024.md`](./multipass-run-chg-024.md)
**Verdict:** **CONDITIONAL GO** — all three hard gates pass; **one criterion is Blocked** on a fixture gap.

---

## 1. Why this run supersedes a GO with a CONDITIONAL GO

`RUN-CHG-024` reported **GO** with zero Blocked criteria. That verdict rested on a metric that could not fail.

`first_pass_completeness` had been defined as *"items that needed no rework loop"*, following the method named in `feature.md` §7. But **no rework path is implemented** — `Case.rework_loops` is a field nothing increments. The counter was structurally stuck at zero, so every item scored, and the metric read 23/23 = 100% while measuring nothing at all.

This was found during the task-list reconciliation, not by a failing test. No test could have found it: the metric was *correct* by its own definition. The definition was the defect.

**Two things followed.** The metric was redefined to grade something falsifiable — whether the system left underived anything that was reliably derivable from available records (FR-003). And the capability that metric assumes, **backfill (F3), was implemented**, because grading a capability that does not exist is not grading.

The redefined metric **fails**, at 20/23 = 86.96% against a ≥ 90% target. It is recorded **Blocked** rather than **Failed**, because the shortfall is caused entirely by absent fixtures rather than by defective behaviour — see §4.

Reporting a worse verdict than the previous run is the correct outcome here. The system did not get worse; the measurement got honest.

---

## 2. Run declaration

| Item | Value |
|---|---|
| Build | `src/admin_workflow/` — 24 modules, deterministic core |
| Policy bundle | **`POLICY-v2`**, frozen and SHA-256 verified at load |
| Dataset | **`SYN-CASESET-v2`**, 23 synthetic cases |
| Register | **`CCR-DEMO-v1`**, 3 entries, literal-marker matching only |
| Environment | Local dev sandbox, Python 3.14, no network, no model backend |
| Pre-registered in | `docs/progress-log.md` **CHG-025** |

Roles and designations are held by the automated test principal operating **under** the registry, never as a member of it. A production run must name real people before this record is cited as organisational readiness evidence.

---

## 3. Scorecard

| Metric | Result | Target | Verdict |
|---|---|---|---|
| Field extraction accuracy | **160 / 161 = 99.38%** | ≥ 85% | **Pass** |
| Seeded omission detection | **13 / 13 = 100%** | 100% | **Pass** |
| Routing accuracy | **12 / 12 = 100%** | ≥ 90% | **Pass** |
| **First-pass completeness** | **20 / 23 = 86.96%** | ≥ 90% | **BLOCKED** — §4 |
| Escalation outcome correctness | **23 / 23 = 100%** | 100% | **Pass** |
| False escalations | **0** | 0 | **Pass** |
| Duplicate flag correctness | **23 / 23 = 100%** | 100% | **Pass** |
| SC-009 duplicate matcher correctness | **8 / 8 = 100%** | 100% | **Pass** |
| Register entry coverage | **3 / 3 = 100%** | 100% | **Pass** |
| Unapproved sends | **0** | 0 | **Pass** |
| *Mandatory fields resolved at intake* | *19 / 23 = 82.61%* | *diagnostic* | *reported* |
| *Cases backfilled from records* | *2 / 23* | *diagnostic* | *reported* |

Extraction and omission detection are graded against the **extraction snapshot**, taken before backfill runs. A value derived from prior records was still absent from *this* document; crediting it as extracted would overstate what was read.

---

## 4. The Blocked criterion

**SC-007 first-pass completeness — Blocked, not Failed.**

Backfill is implemented and works. Two cases resolve from real prior records: CASE-014 and CASE-021 both derive their ordering reference from CASE-009, the same patient's earlier case. The value is tagged with the case it came from, so it stays distinguishable from a submitted value (FR-004).

Three cases declare a backfillable field whose source is an **external record store that `SYN-CASESET-v2` does not contain**:

| Case | Field | Declared source |
|---|---|---|
| CASE-002 | `payer_plan` | "Existing patient record; prior encounters are on file" |
| CASE-011 | `payer_plan` | "Established patient record" |
| CASE-017 | `ordering_reference` | "Shared practice order log" |

None of those records exists. The system therefore cannot derive the values, correctly raises completion tasks instead, and scores 20/23.

**Why Blocked and not Failed.** The behaviour is right; the fixtures are absent. Grading an implementation against sources it was never given is not a measurement of the implementation. This is the same judgement applied to SC-009 and CCS-003 under `SYN-CASESET-v1`, and closing it needs the same remedy: prior-encounter records for those three patients, which mints a new dataset ID.

**Why not simply author those records.** They could be written in minutes, and the metric would go green. It was already once true this session that a green number meant nothing, and adding fixtures specifically to move a number is how that happens again. If they are added, they should be added because the dataset should model a record store — not because SC-007 is uncomfortable.

---

## 5. What backfill does and refuses to do

F3 is narrow by design. FR-003 permits deriving what is *reliably derivable* and forbids inferring anything else.

| Behaviour | Rule |
|---|---|
| Derives from prior cases for the **same patient reference** | Exact identifier match, never fuzzy. A value from another patient's record is not a derivation. |
| Tags every derived value with its **source case** | FR-004. An untagged backfill is indistinguishable from an invented one. |
| Leaves a field **missing** when no record holds it | Guessing would violate FR-002 and FR-003 alike. |
| Leaves a field **missing** when two records disagree | A conflict is not a derivation. Picking one silently is the inference FR-003 forbids. |
| **Never** overwrites a submitted value | The document outranks the record store. |
| **Never** backfills from the case being processed | A case cannot be its own source. |

Eight unit tests cover these, including every refusal path — the refusals matter more than the successes.

---

## 6. Pass results

| Pass | Result |
|---|---|
| **0 — Governance pre-check** (hard gate) | **PASS** |
| **1 — Intake baseline** | **PASS with SC-007 Blocked** |
| **2 — Broken-path robustness** | **PASS** |
| **3 — Approval and escalation** | **PASS** |
| **4 — Clearance and release gating** (hard gate) | **PASS** |
| **5 — Safety, audit, governance** (hard gate) | **PASS** |
| **6 — Repeatability and surface** | **PASS** |

**179 tests, all passing** — 25 contract, 61 unit, 52 scenario, 41 harness. Lint clean, including the `decisions/` import boundary rule.

The harness now asserts against a **named allowlist** of documented Blocked criteria rather than against an empty list. A new Blocked criterion fails the build; a known one does not. An allowlist that must be edited to grow is the point.

---

## 7. Delivery honesty

`specs/001-admin-workflow-assistant/tasks.md` carries a delivery-status section reconciling all 180 tasks: **137 delivered (76%)**, with the 43 open tasks grouped by theme and each stating whether the gap matters. The largest genuine functional gaps are parallel approval orchestration (US4) and the MAF/Copilot binding, both deferred deliberately and both named.

Two gaps are called out there specifically because a reader would otherwise assume they were covered: the rework loop (which caused this run's metric defect) and P10 dispatch-deadline breach handling, which is specified in the contract but not enforced in code.

---

## 8. Production gap statement — unchanged

Before any real data:

1. **P8 retention** must rise from 90 days to the six years HIPAA requires.
2. **`CCR-DEMO-v1` must be replaced** by a clinically authored register. Full coverage of a three-entry demo register is not clinical completeness.
3. **Real people must be named** against the §4.1 roles and §4.2 designations.

Multi-tenancy, SSO, production hosting and live EHR integration remain out of scope (`feature.md` §4).

---

## 9. Verdict

**CONDITIONAL GO.**

All three hard gates pass. All four never-cut features are implemented and structurally enforced. Nine of ten graded metrics meet or exceed target.

The condition is SC-007, Blocked on three absent fixtures. It is recorded that way rather than quietly redefined into a pass — which is precisely what the previous run's verdict turned out to have done.

**Not Go for anything involving real patient data.** See §8.
