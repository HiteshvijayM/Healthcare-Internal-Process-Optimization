# Multipass Validation Run Record — CHG-024

**Run ID:** `RUN-CHG-024`
**Executed:** 2026-09-02
**Supersedes:** [`multipass-run-chg-023.md`](./multipass-run-chg-023.md) (CONDITIONAL GO)
**Verdict:** **GO** — every hard gate passes and **no criterion is Blocked**.

---

## 1. What changed since the previous run

`RUN-CHG-023` returned **CONDITIONAL GO**. Every hard gate passed, but two criteria could not be graded at all because `SYN-CASESET-v1` lacked the fixtures they needed. They were recorded **Blocked** rather than quietly counted as satisfied.

`SYN-CASESET-v2` adds exactly three fixtures and changes nothing else. Both criteria are now graded and both pass.

| Was Blocked | Closed by | Now |
|---|---|---|
| **SC-009 — duplicate detection** | **CASE-021** (post-window exact re-send, closed case) and **CASE-022** (same key, different content) | `sc009_duplicate_matcher_correctness` **8/8 = 100%** |
| **CCS-003 — register coverage** | **CASE-023** (laboratory critical-value marker) | `register_entry_coverage` **3/3 = 100%** |

---

## 2. Run declaration

| Item | Value |
|---|---|
| Build | `src/admin_workflow/` — 23 modules, deterministic core |
| Policy bundle | **`POLICY-v2`**, frozen and SHA-256 verified at load |
| Dataset | **`SYN-CASESET-v2`**, 23 synthetic cases (001–020 unchanged from v1) |
| Register | **`CCR-DEMO-v1`**, 3 entries, literal-marker matching only |
| Environment | Local dev sandbox, Python 3.14, no network, no model backend |
| Pre-registered in | `docs/progress-log.md` **CHG-024** |

### Acting role holders

Roles are authorities, not persons (§4.1 AC-2). For this run every role and designation is held by the automated test principal operating **under** the registry, never as a member of it. The agent holds no role and no designation; `Role` has no `AGENT` member, so an agent-authored approval is unrepresentable rather than merely rejected.

**A production run must name real people here before this record may be cited as organisational readiness evidence.**

---

## 3. Scorecard

Dataset `SYN-CASESET-v2` · bundle `POLICY-v2` · register `CCR-DEMO-v1`

| Metric | Result | Target | Verdict |
|---|---|---|---|
| Field extraction accuracy | **160 / 161 = 99.38%** | ≥ 85% | **Pass** |
| Seeded omission detection | **13 / 13 = 100%** | 100% | **Pass** |
| Routing accuracy | **12 / 12 = 100%** | ≥ 90% | **Pass** |
| First-pass completeness | **23 / 23 = 100%** | ≥ 90% | **Pass** |
| Escalation outcome correctness | **23 / 23 = 100%** | 100% | **Pass** |
| False escalations | **0** | 0 | **Pass** |
| Duplicate flag correctness | **23 / 23 = 100%** | 100% | **Pass** |
| **SC-009 duplicate matcher correctness** | **8 / 8 = 100%** | 100% | **Pass** |
| **Register entry coverage** | **3 / 3 = 100%** | 100% | **Pass** |
| Unapproved sends | **0** | 0 | **Pass** |
| *Mandatory fields resolved at intake* | *19 / 23 = 82.61%* | *diagnostic — no target* | *reported, not graded* |

**Blocked criteria: none.** This is the first run in the project's history where that is true.

**Denominators.** Extraction is graded over the seven fields in `graded_fields` across 23 cases (n = 161); `supporting_notes` is extracted but not graded. Every percentage above carries its denominator, because a percentage without one is not a measurement (feature.md §7).

---

## 4. Two measurement defects fixed, not worked around

These are worth naming, because in both cases the *previous* run reported a passing number that a broken implementation could also have produced.

### SC-009 graded the flag, not the matcher

Under `RUN-CHG-023`, duplicate detection was scored on whether the right prior case was identified. **A key-match-only implementation satisfies that completely** — it would flag CASE-005 and CASE-018 correctly, score 100%, and never invoke the identity matcher once. The unbounded document-identity match that FR-055 exists for could have been dead code and nothing would have noticed.

SC-009 now grades **which matcher fired**, per case, against a declared `duplicate_matcher_expected`. CASE-005 and CASE-018 were given explicit `key_match` expectations the v1 answer key never stated. CASE-021 asserts `identity_match` specifically — and because it arrives 39 days out against a closed case, a key matcher *cannot* produce it.

### Register coverage was assumed, not computed

§3 of the register previously *read* as full coverage while one of three safety-bearing entries had never fired on any fixture. Coverage is now computed from the register itself: every entry must match at least one fixture, and an entry matching none is reported Blocked automatically. If a future amendment adds a fourth entry without a fixture, the metric drops on the next run and no one has to remember to check.

**A claim that cannot fail is not evidence.** Both changes made a previously unfalsifiable claim falsifiable.

---

## 5. Two latent drift risks closed

| Risk | Was | Now |
|---|---|---|
| Bundle / dataset divergence | `bundle.lock.json` hardcoded `SYN-CASESET-v1`. A run could be scored against a dataset the bundle was never frozen for. | The lock reads the dataset ID from the answer key, and a Pass 0 check asserts they agree. |
| Stale test denominator | The Pass 1 extraction test hardcoded `140`. It would have stopped matching silently the moment the dataset grew. | The expected denominator is derived from the answer key. |

### BC-1 proved itself during this run

Mid-work, `docs/critical-condition-register.md` was edited after the bundle had been frozen. The next test run **refused to start**: `bundle hash mismatch for docs/critical-condition-register.md`. Not a warning, not a skipped check — a hard startup failure that stopped the whole suite dead until the bundle was re-frozen.

That is the reviewed artifact and the executed artifact being held to each other, demonstrated rather than asserted.

---

## 6. Pass results

| Pass | Scope | Result |
|---|---|---|
| **0 — Governance pre-check** (hard gate) | Constitution integrity, synthetic provenance, frozen bundle, bundle/dataset agreement, four designations, register version, agent holds no role, change logged | **PASS** |
| **1 — Intake baseline** | F1–F8 extraction, completeness, routing, provisional policy | **PASS** |
| **2 — Broken-path robustness** | Duplicates on both boundaries in both directions, unreadable input, false-positive traps | **PASS** |
| **3 — Approval and escalation** | F9–F15, escalation precedence, dispatch approval, SLA, full register coverage | **PASS** |
| **4 — Clearance and release gating** (hard gate) | F16–F18, order-independence, separation of duty | **PASS** |
| **5 — Safety, audit, governance** (hard gate) | F19, F20, F23, F24, masking, hash chain, reconstruction | **PASS** |
| **6 — Repeatability and surface** | P7 determinism, denominators, surface operability | **PASS** |

### Test evidence — 166 tests, all passing

| Tier | Count | What it proves |
|---|---|---|
| Contract | 25 | AST import-boundary scan, register mirror equality, policy-vs-`feature.md` equality, grammar restriction, bundle tamper detection, masking scan, chain tamper evidence |
| Unit | 53 | One per decision function, including the exhaustive **32-combination** escalation outcome matrix proving totality and single-valuedness |
| Scenario | 49 | AS-1..AS-14 plus every named dataset trap, each separately failing |
| Harness | 39 | Passes 0–6, computing scores rather than asserting them |

### The three new fixtures, verified individually

| Fixture | Asserted | Failure it would have exposed |
|---|---|---|
| **CASE-021** | Flags `CASE-014` via `identity_match` | A dead identity matcher — nothing else in the graded set would have exposed it |
| **CASE-022** | **Not** flagged at all | An over-broad normaliser erasing real content differences |
| **CASE-023** | Matches `CCS-003`, reaches dispatch approval, **no digit** in the packet description | A registered signal that never fires; or reading the numeric result behind the marker (**Sev 0**) |

> **What CASE-021 does and does not prove.** It proves the identity matcher is live and reaches a closed case outside the window. It does **not** independently prove the key window is enforced: `detect_duplicate` evaluates identity first and returns before the key loop runs, so this fixture would report `identity_match` whatever the window were set to. The window itself is covered by `test_key_match_outside_the_window_does_not_flag`. Both properties are covered; they are covered by different tests, and saying otherwise would overstate this fixture.

---

## 7. Safety evidence

| Property | How it is enforced | Evidence |
|---|---|---|
| No unapproved outbound action | `ActionGate` is the only path to an effect; refusal logged before anything happens | SC-008 = 0 across 23 cases; 6 scenario tests |
| Agent holds no approver role | `Role` enum has no `AGENT` member — unrepresentable, not rejected | Contract test asserts `Role("agent")` raises |
| No clinical inference | Literal marker matching only; no embeddings, no similarity, no model call | 11 unit tests; administrative urgency proven not to escalate |
| No numeric clinical evaluation | CCS-003 matches the laboratory's marker; the value behind it is never read | `never_evaluate_numeric_value`; digit assertion on CASE-023's packet |
| No negative clinical claim | Only `"no registered signal matched"` may be stated | CRC-3 tests; CASE-013 and CASE-020 verified |
| Missing register blocks | Case held, provisional routing refused, progression genuinely stopped | Scenario test asserts `routing is None` |
| Governance outranks completeness | The FR-054 trap — absent clinical recipient yields governance, never completeness | Dedicated unit + harness tests |
| Clock never runs unstaffed | Coverage gates the clock start, before the outcome is decided | `decide_clock` tests |
| Identifiers masked at rest | Filter on the write boundary, not the read path | Zero unmasked identifiers across a full 23-case run |
| Audit is tamper-evident | Append-only, SHA-256 hash-chained | Chain verified after full run; tampering detected |
| Policy cannot drift unnoticed | Bundle hash-locked, including the authoritative markdown register | BC-1 fired during this run — see §5 |

---

## 8. Production gap statement — unchanged

This build remains **demo-scoped**. Three things must happen before it may touch real data. None is an improvement; each is a precondition:

1. **P8 retention** must rise from 90 days to the six years HIPAA requires. The current value is sufficient *only* because the system processes exclusively synthetic data.
2. **`CCR-DEMO-v1` must be replaced** by a register authored and maintained by the deploying organisation's clinical governance function. Three entries is adequate for a demo and nothing more. This is a clinical deliverable and cannot be authored by this project or by any automation. Full coverage of a three-entry demo register is not evidence of clinical completeness.
3. **Real people must be named** against the §4.1 roles and §4.2 designations, with separation of duty enforced against actual identities rather than test principals.

Multi-tenancy, SSO, production hosting and live EHR integration remain out of scope (feature.md §4).

---

## 9. Verdict

**GO.**

All three hard gates pass. Every never-cut feature — F12, F19, F20, F24 — is implemented and enforced structurally rather than by convention. All ten graded metrics meet or exceed target. **No criterion is Blocked.**

The two criteria that were Blocked in the previous run are not merely passing now; the *way they are graded* was strengthened first, so that passing them means something a broken implementation could not also achieve. That distinction is the substance of this run.

**Not Go for anything involving real patient data.** See §8.
