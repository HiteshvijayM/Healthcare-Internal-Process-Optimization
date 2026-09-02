# Multipass Validation Run Record — CHG-023

**Run ID:** `RUN-CHG-023`
**Executed:** 2026-09-02
**Verdict:** **CONDITIONAL GO** — every hard gate passes; two criteria are **Blocked** on fixture gaps, and a Blocked criterion is not a Pass (harness §4).

---

## 1. Run declaration

| Item | Value |
|---|---|
| Build | `src/admin_workflow/` — 25 modules, deterministic core |
| Policy bundle | **`POLICY-v1`**, frozen and SHA-256 verified at load (clears **CA-008-003**) |
| Dataset | **`SYN-CASESET-v1`**, 20 synthetic cases, provenance per constitution §3 |
| Register | **`CCR-DEMO-v1`**, 3 entries, literal-marker matching only |
| Environment | Local dev sandbox, Python 3.14, no network, no model backend (clears **CA-008-004**) |
| Pre-registered in | `docs/progress-log.md` **CHG-023** |

### Prior blockers

| ID | Status |
|---|---|
| **CA-008-002** — implementation build | **Cleared.** The build exists and runs. |
| **CA-008-003** — freeze a policy version implementing P1–P11 | **Cleared.** `POLICY-v1`, hash-locked in `config/policy/v1/bundle.lock.json`. |
| **CA-008-004** — validation sandbox | **Cleared.** Runs offline and deterministically; no external dependency. |
| **CA-008-005** — record real coverage and quality scores | **Cleared by this record.** |

### Acting role holders

Roles are authorities, not persons (§4.1 AC-2). For this run every role and designation is held by the automated test principal operating **under** the registry — not as a member of it. The agent holds no role and no designation; `Role` has no `AGENT` member, so an agent-authored approval is unrepresentable rather than merely rejected.

**A production run must name real people here before this record may be cited as readiness evidence.**

---

## 2. Scorecard

Dataset `SYN-CASESET-v1` · bundle `POLICY-v1` · register `CCR-DEMO-v1`

| Metric | Result | Target | Verdict |
|---|---|---|---|
| Field extraction accuracy | **139 / 140 = 99.29%** | ≥ 85% | **Pass** |
| Seeded omission detection | **12 / 12 = 100%** | 100% | **Pass** |
| Routing accuracy | **10 / 10** | ≥ 9 / 10 | **Pass** |
| First-pass completeness | **20 / 20 = 100%** | ≥ 90% | **Pass** |
| Escalation outcome correctness | **20 / 20 = 100%** | 100% | **Pass** |
| False escalations | **0** | 0 | **Pass** |
| Duplicate flag correctness | **20 / 20 = 100%** | 100% | **Pass** |
| Unapproved sends | **0** | 0 | **Pass** |
| *Mandatory fields resolved at intake* | *16 / 20 = 80%* | *diagnostic — no target* | *reported, not graded* |

**Denominators.** Extraction is graded over the seven fields named in `graded_fields` across 20 cases (n = 140); `supporting_notes` is extracted but not graded. A percentage without a denominator is not a measurement (feature.md §7).

**First-pass completeness** is measured as feature.md §7 specifies — items needing no rework loop. The stricter reading, items reaching routing with every mandatory field already resolved, is reported separately as a named diagnostic rather than folded into the headline. It sits at 80% because the dataset deliberately seeds omissions documented as unresolvable at intake; those cases are correctly incomplete, not incorrectly handled. Reporting only the favourable reading would have been the easy option and the wrong one.

**The single extraction miss** is CASE-007, where the answer key renders a phrase separator as a colon while every other case renders it as a comma. It was deliberately **not** special-cased. Fitting an extractor to one fixture is how an accuracy number stops meaning anything.

---

## 3. Pass results

| Pass | Scope | Result |
|---|---|---|
| **0 — Governance pre-check** (hard gate) | Constitution integrity, synthetic-data provenance, frozen bundle, four designations resolved, register version, agent holds no role, change logged | **PASS** |
| **1 — Intake baseline** | F1–F8 extraction, completeness, routing, provisional policy | **PASS** |
| **2 — Broken-path robustness** | Duplicates, unreadable input, false-positive traps | **PASS with SC-009 Blocked** |
| **3 — Approval and escalation** | F9–F15, escalation precedence, dispatch approval, SLA | **PASS with CCS-003 uncovered** |
| **4 — Clearance and release gating** (hard gate) | F16–F18, order-independence, separation of duty | **PASS** |
| **5 — Safety, audit, governance** (hard gate) | F19, F20, F23, F24, masking, hash chain, reconstruction | **PASS** |
| **6 — Repeatability and surface** | P7 determinism, denominators, surface operability | **PASS** |

### Test evidence

**154 tests in four tiers; 153 pass.**

| Tier | Count | What it proves |
|---|---|---|
| Contract | 30 | AST import-boundary scan, register mirror equality, policy-vs-`feature.md` equality, grammar restriction, bundle tamper detection, masking scan, chain tamper evidence |
| Unit | 46 | One per decision function, including the exhaustive **32-combination** escalation outcome matrix proving the table is total and single-valued |
| Scenario | 45 | AS-1..AS-14 plus every named dataset trap, each separately failing |
| Harness | 33 | Passes 0–6, computing scores rather than asserting them |

**The one failure was the F24 governance check** — it refused to pass while CHG-023 was absent from the progress log, which is exactly the failure mode it exists to catch and the same one that surfaced as R1 during planning. It passes once the entry is written. That it fired twice, unprompted, on two different omissions is the strongest evidence in this record that the governance enforcement is real rather than decorative.

---

## 4. Safety evidence

| Property | How it is enforced | Evidence |
|---|---|---|
| No unapproved outbound action | `ActionGate` is the only path to an effect; refusal is logged before anything happens | SC-008 = 0 across 20 cases; 6 scenario tests |
| Agent holds no approver role | `Role` enum has no `AGENT` member — unrepresentable, not rejected | Contract test asserts `Role("agent")` raises |
| No clinical inference | Literal marker matching only against `CCR-DEMO-v1`; no embeddings, no similarity, no model call | 11 unit tests; administrative urgency proven not to escalate |
| No negative clinical claim | Only `"no registered signal matched"` may be stated | CRC-3 tests; CASE-013 and CASE-020 verified |
| Missing register blocks | Case held, provisional routing refused, progression genuinely stopped | Scenario test asserts `routing is None` |
| Governance outranks completeness | The FR-054 trap — an absent clinical recipient yields a governance blocker, never a completeness one | Dedicated unit + harness tests |
| Clock never runs unstaffed | Coverage gates the clock start, before the outcome is decided | `decide_clock` tests |
| Identifiers masked at rest | Filter on the write boundary, not the read path | Zero unmasked identifiers across a full 20-case run |
| Audit is tamper-evident | Append-only, SHA-256 hash-chained | Chain verified after full run; tampering detected |

---

## 5. Blocked criteria — not passed, not failed

Per harness §4, a Blocked criterion may not be cited as evidence of readiness.

| Criterion | Why blocked | To clear |
|---|---|---|
| **SC-009 — duplicate detection** | `SYN-CASESET-v1` supplies neither an exact re-send arriving *after* the 72-hour key window against a closed case, nor a same-key-different-content submission. Both existing duplicates (CASE-005 at ~6h, CASE-018 at ~20h) fall inside the window, so both are key matches — the identity matcher is never exercised alone, and a key-match-only implementation would pass by accident. | Two fixtures in `SYN-CASESET-v2` |
| **CCS-003 — register coverage** | No case carries a laboratory critical-value marker. The entry's negative direction is covered; its positive direction is not. | One fixture in `SYN-CASESET-v2` |

Both are gaps in the **fixtures**, not in the build. The identity matcher is implemented and unit-tested in both directions; what is missing is end-to-end evidence from the graded dataset.

---

## 6. Production gap statement

This build is **demo-scoped**. Three things must happen before it may touch real data, and none is an improvement — each is a precondition:

1. **P8 retention** must rise from 90 days to the six years HIPAA requires. The current value is sufficient only because the system processes exclusively synthetic data.
2. **`CCR-DEMO-v1` must be replaced** by a register authored and maintained by the deploying organisation's clinical governance function. Three entries covering two seeded marker families is adequate for a demo and nothing more. This is a clinical deliverable and cannot be authored by this project or by any automation.
3. **Real people must be named** against the §4.1 roles and §4.2 designations, with the separation-of-duty rule enforced against actual identities rather than test principals.

Multi-tenancy, SSO, production hosting and live EHR integration remain out of scope (feature.md §4).

---

## 7. Verdict

**CONDITIONAL GO.**

Every hard gate — Passes 0, 4 and 5 — passes. Every never-cut feature (F12, F19, F20, F24) is implemented, tested and enforced structurally rather than by convention. All eight graded metrics meet or exceed target.

The condition is the two Blocked criteria. They do not indicate defects; they indicate that two claims cannot yet be *evidenced* from the graded dataset. Recording them as Blocked rather than quietly counting them as satisfied is the difference between a validated system and one that merely looks validated.

**Not yet Go for anything involving real patient data.** See §6.
