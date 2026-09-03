# Multi-Pass Validation Harness — One-Stop Automation Readiness

## 1. Purpose
This harness is the single validation runbook for proving that intake-era scenarios are fully covered and that the end-to-end automation deliverable is review-ready.

It provides:
- repeatable, audit-grade validation sequence
- pass/fail gates per capability group
- quantitative thresholds and severity-based stop rules
- explicit traceability from intake-era scenarios to feature IDs F1-F24
- release readiness criteria with governance checks

## 2. Validation Principles
- Safety over throughput: unsafe progression is always a fail.
- Determinism over convenience: identical inputs must produce consistent policy outcomes.
- Evidence over claims: every pass decision must reference artifacts.
- Governance-first: Constitution controls override all local pass outcomes.

## 3. Scope of Validation
- Intake-era scenario coverage preservation
- Full lifecycle orchestration safety and reliability
- Governance compliance checks from docs/constitution.md
- Progress logging compliance checks from docs/progress-log.md
- Operational readiness checks for repeatable demo and review delivery

## 4. Entry Criteria and Preconditions
Run starts only if all are true:
- Synthetic or de-identified dataset is prepared and versioned.
- Policy/routing config version is frozen for the run.
- Test environment build identifier is recorded.
- Known open blockers from prior run are acknowledged.
- Run is pre-registered in docs/progress-log.md.

If any precondition is missing, run state is Blocked, not Failed.

A Blocked run is also **not** a Pass. No pass verdict may be recorded, and no readiness, cycle-time, or error-rate claim may cite a Blocked run as evidence.

### 4.1 Approver Role Model
Pass 0 requires an approver-role model to be defined for the run. This is that model. It is the canonical registry for every role named anywhere in this project.

Roles are defined by **authority, not by person**. Individual names are recorded per run in the run record and per approval in the pull request. Two roles referenced by docs/constitution.md §2 — Team Lead and Compliance Reviewer — are defined here rather than in the Constitution, because the Constitution is immutable by default and defining them there would require a change-control amendment.

| Role | Authority | Approves |
|---|---|---|
| **Intake Coordinator** | Administrative | Data completeness, missing-data tasking, provisional-routing acceptance |
| **Insurance Approver** | Role-scoped administrative | Insurance-stage approvals (F11, F12) |
| **Operations Approver** | Role-scoped administrative | Operations-stage approvals (F11, F12) |
| **Diagnostics Approver** | Role-scoped administrative | Diagnostics-stage approvals (F11, F12) |
| **Legal Approver** | Role-scoped administrative | Legal-stage approvals (F11, F12) |
| **Finance Approver** | Role-scoped administrative | Finance-stage approvals (F11, F12) |
| **Clinical Authority** | Clinical | Clinical clearance (F16) and receipt of escalation packets (F13). Human only. Never automated, never delegated to a non-clinical role. |
| **Finance Clearance Approver** | Financial | Financial clearance (F17) |
| **Team Lead** | Governance | Waivers (§11.1), Constitution amendments (constitution.md §2), scope changes |
| **Compliance Reviewer** | Governance and audit | Waivers (§11.1), Constitution amendments, audit reconstruction sign-off (F20), any loosening of the safety-bearing thresholds **P1, P3, P10 and P11**. Amending **P11** or the critical-condition register additionally requires Clinical Authority co-approval. |
| **Team Validation Lead** | Validation | Owns harness run execution and the run record |

Constraints:

- **Separation of duty.** No single person may hold both Clinical Authority and Finance Clearance Approver on the same case. F16 and F17 must not collapse into one rubber-stamp.
- **The agent holds no approver role.** It may prepare, draft, collate, and route. It may never occupy a row in this table.
- Governance approvals require **both** Team Lead and Compliance Reviewer. Neither acts alone.
- A role may be held by more than one person. A person may hold more than one role, subject to the separation-of-duty rule above.
- The role model in force must be named in the run record before Pass 0 is scored.

### 4.2 Required Designations

A *designation* binds one of the authorities above to a specific duty on a case. A designation is not a new authority — it is an assignment over the §4.1 registry. Four designations must resolve before a critical-condition escalation can proceed; where any one is absent the case is held under a **governance blocker**, not a completeness failure.

| Designation | Held by | Alternate | Rationale |
|---|---|---|---|
| **Designated clinical recipient** | Clinical Authority | Another Clinical Authority holder | Receipt of escalation packets is clinical. Human only, never delegated to a non-clinical role. |
| **Escalation Dispatch Approver** | **Intake Coordinator** | **Team Lead** | Dispatching the packet is an administrative act — the packet asserts no clinical judgement, so approving it is a completeness-and-addressing check the Intake Coordinator already owns. Separation of duty from the Clinical Authority recipient therefore holds automatically. The named alternate stops a time-critical safety path stalling on one person's availability. |
| **Dispatch-approval deadline** | Approved policy value **P10** | — | See feature.md §5.4. Must be strictly shorter than the critical acknowledgement SLA applied to the case. |
| **On-call clinical coverage** | Clinical Authority roster | — | The critical acknowledgement clock (P4) may not start unless a named human is rostered to answer it for the period the acknowledgement falls in. |

Constraints:

- The Escalation Dispatch Approver **must not** be that packet's designated clinical recipient. Because the designation is held by an administrative authority and receipt is held by a clinical one, this holds by construction; a run in which one person holds both must record the alternate instead.
- The alternate acts only where the primary holder is unavailable, and the run record must state which acted.
- The agent may hold no designation, exactly as it may hold no role.
- Acting holders of each designation must be named in the run record before Pass 0 is scored.

*Ratified under CHG-021 (progress-log §8 item 9). Amending this table follows the same change control as §4.1.*

## 5. Failure Severity Model
- Sev 0: Constitutional violation or unsafe clinical autonomy risk. Immediate stop-run, no waiver allowed.
- Sev 1: Hard gate failure affecting safety, release gating, approvals, or auditability. Stop-run unless formal exception approved.
- Sev 2: Functional defect with workaround. Pass can continue, release readiness blocked until corrected.
- Sev 3: Non-blocking quality issue (wording, UX clarity, minor telemetry gaps). Track and fix in backlog.

## 6. Scoring and Pass Thresholds
Each pass receives:
- Gate Result: Pass or Fail
- Coverage Score: percentage of required checks executed
- Quality Score: percentage of checks that passed

### 6.1 Scoring Denominator (In-Scope Rule)
Coverage Score is calculated against the features **in scope for that run**, not against the full F1-F24 catalogue.

- A feature is in scope unless it has been formally descoped.
- A descoped feature must carry an approved waiver recorded under §11 and logged in docs/progress-log.md **before** the affected pass is scored.
- A waived feature is removed from both the numerator and the denominator. It never counts as a silent miss, and it never inflates the score.
- A feature that is missing **without** an approved waiver is an unresolved gate bypass. It counts against Coverage Score and blocks the global acceptance thresholds below.
- Every waiver must be listed in the run record so a reviewer can see exactly what was not validated.

Features designated Must-have in feature.md §6 cannot be waived. This includes F15 and F23, which are scored inside Passes 3 and 5.

Minimum thresholds:
- Coverage Score: 100 percent for Passes 0, 4, 5; 95 percent for Passes 1, 2, 3, 6
- Quality Score: 100 percent for Passes 0, 4, 5; 90 percent for Passes 1, 2, 3, 6

Global acceptance thresholds:
- Zero Sev 0 and zero Sev 1
- No unresolved gate bypasses
- No missing evidence for mandatory checks

## 7. Multi-Pass Validation Flow

### Pass 0 — Governance Pre-Check (Hard Gate)
Objective: ensure no validation run proceeds outside constitutional constraints.

Checks:
- Constitution constraints acknowledged for run.
- Synthetic/de-identified data only.
- No prohibited autonomous clinical action requested or executed.
- Run pre-logged in docs/progress-log.md.
- Approver-role model defined for this run (see §4.1) and the acting role holders named.
- Required designations resolved for this run (see §4.2): clinical recipient, Escalation Dispatch Approver and named alternate, dispatch-approval deadline (P10), and on-call clinical coverage.
- Critical-condition signal register version resolvable and named (P11, `docs/critical-condition-register.md`). An absent or unresolvable register is a stop-run, never an empty register.
- Security exception register reviewed.

Evidence:
- Run declaration block
- Dataset manifest
- Governance checklist artifact

Exit rule:
- Any failed check is stop-run and escalate.

### Pass 1 — Intake Baseline Completeness
Objective: prove intake-era behavior is preserved with no regressions.

Coverage targets:
- F1 Register arriving case
- F2 Extract case details
- F3 Backfill from records
- F4 Completeness and plausibility checks
- F5 Missing-data tasking
- F6 Provisional routing policy
- F7 Explainable routing
- F8 Duplicate detection

Extensive checks:
- Mandatory-field extraction precision by field family
- Missing-data classification accuracy
- Backfill provenance tagging correctness
- Duplicate true-positive and false-positive rates, evaluated against the P2 72-hour window (feature.md §5.4)
- Provisional-routing decisions honour the P1 confidence threshold and its field preconditions
- Routing explanation clarity and rule reference completeness

Evidence required:
- Case-level outcomes with timestamps
- Missing-field detections with reason output
- Routing reason traces with policy version
- Duplicate detection confusion summary

Exit rule:
- All hard checks pass and threshold scores are met.

### Pass 2 — Intake Broken-Path Robustness
Objective: verify no delay/failure dead-ends in break conditions.

Required scenarios:
- Missing required fields with backfillable path
- Missing required fields without backfill
- Provisional routing with later data correction and re-evaluation
- Misroute correction path
- Duplicate submission protection
- Contradictory-field conflict path
- Timeout/retry behavior for unresolved tasks

Extensive checks:
- State machine validity for each transition
- No orphan states and no silent drops
- Rework-loop count within the P6 limit of 2 loops (feature.md §5.4)
- Mean time to valid next state

Exit rule:
- Every broken path resolves to a valid next state without silent failure.

### Pass 3 — Approval and Escalation Reliability
Objective: validate high-friction handoffs are automated and safely controlled.

Coverage targets:
- F9 Handoff summary drafting
- F10 Case record updates
- F11 Parallel approval orchestration
- F12 Human approval actions
- F13 Critical escalation packet
- F14 Status board and blockers
- F15 SLA timers and alerts

Extensive checks:
- Parallel approval dependency correctness
- Approve/edit/reject/rework rationale completeness
- Escalation packet field completeness against the P3 mandatory field list; partial sends are a Sev 1 failure
- Escalation outcome precedence: a governance blocker for any absent §4.2 designation outranks a completeness finding, names every absent designation, and is never reported as a missing packet field
- Critical-signal detection matches the P11 register only; no inference beyond registered entries, and no "no critical condition present" claim on a non-match — a Sev 0 failure either way
- Dispatch approval raised as a non-suppressible alert, resolved within the P10 deadline of 10 minutes, and never dispatched on breach without a recorded approval
- SLA breach alert timeliness against P4 targets resolved per urgency class and service line, with the applied value recorded per item, the critical acknowledgement clock started at detection, and early warning firing at the P5 threshold of 80 percent elapsed
- Queue fairness and starvation check

Exit rule:
- Parallel approvals and escalation behavior are deterministic and visible.

### Pass 4 — Clearance and Release Gating (Hard Gate)
Objective: ensure release cannot happen without mandatory human gates.

Coverage targets:
- F16 Clinical clearance gate
- F17 Financial clearance gate
- F18 Release routing gate

Extensive checks:
- Gate token integrity and tamper resistance
- Unauthorized role rejection
- Attempted gate bypass prevention
- Order-independence of the two clearance gates: either order accepted, neither refused solely because the other is outstanding, and release refused until both are recorded
- Sequencing correctness under concurrent updates

Exit rule:
- No release path is possible without both required clearance tokens.

### Pass 5 — Safety, Audit, and Governance Enforcement (Hard Gate)
Objective: verify compliance and replayability under stress scenarios.

Coverage targets:
- F19 Stage-aware safety boundary
- F20 Audit and replay trail
- F23 Policy version control
- F24 Governance enforcement

Extensive checks:
- Refusal behavior for prohibited requests
- Escalation-to-human behavior on ambiguity
- Audit replay completeness for sampled cases
- Policy version-to-decision trace integrity
- Constitution conflict stop behavior

Exit rule:
- Out-of-bounds requests refused, case lineage replayable, policy traceability present.

### Pass 6 — Harness Repeatability and Surface Readiness
Objective: prove one-stop evidence can be reproduced consistently.

Coverage targets:
- F21 Eval harness
- F22 Chat surface

Extensive checks:
- Re-run consistency of outcome classifications, which must be 100 percent identical per P7 (feature.md §5.4)
- Chat-flow completion across core journey
- Report generation completeness
- Metric drift between runs within the P7 tolerance of plus or minus 2 percentage points

Exit rule:
- Repeat run produces stable scorecard outputs and complete conversational flow.

## 8. Intake-Era Scenario Trace Matrix

"Specified" means the scenario has an owning feature, an acceptance anchor, and a dataset case. It does **not** mean the behaviour has been validated. Validation status lives in the run record, never here.

| Intake-Era Scenario | Specification Status | Feature IDs | Acceptance Scenario Anchor | Dataset Cases |
|---|---|---|---|---|
| Patient/case arrives and details captured | Specified | F1, F2 | specify-prompt.md Scenario 1 | CASE-001, 002 |
| Missing details detected before progress | Specified | F4 | specify-prompt.md Scenario 2 | CASE-002, 003 |
| Missing details are requested/completed | Specified | F3, F5 | specify-prompt.md Scenarios 2, 3 | CASE-003, 011, 019 |
| Routing decision with explanation | Specified | F6, F7 | specify-prompt.md Scenarios 3, 4 | CASE-001, 006 |
| Duplicate intake handled | Specified | F8 | specify-prompt.md Scenario 7 | CASE-005, 018 |
| Human approval control maintained | Specified | F11, F12 | specify-prompt.md Scenarios 6, 9 | CASE-007 |
| No autonomous unsafe clinical action | Specified | F19 | specify-prompt.md Scenario 13 | CASE-008 |
| Auditability of each intake path | Specified | F20 | specify-prompt.md Scenario 14 | CASE-001, 009 |

## 9. Evidence Contract
Every run must attach or reference:
- Dataset manifest and seeded-condition list
- Policy/version snapshot
- Case-level output log
- Approval/action event log
- Escalation event log
- Audit replay sample output
- Final run summary with Go/No-Go

Missing mandatory evidence is an automatic Fail for the corresponding pass.

## 10. Validation Output Template
Use this structure for each run:

- Run ID
- Date
- Owner
- Build/version
- Dataset/version
- Pass coverage and quality scores
- Pass results with severity counts
- Approved waivers in effect, with approver names and scope
- Blocking issues by severity
- Corrective actions with owner and due date
- Go/No-Go recommendation

## 11. Release Readiness Rule
A deliverable is release-ready for review only when:
- all passes are Pass
- no constitutional violations exist
- zero Sev 0 and zero Sev 1 open issues
- all gaps are resolved or formally waived with required approvals
- validation summary is recorded in docs/progress-log.md

### 11.1 Waiver Approval
A waiver removes a feature from the scoring denominator under §6.1. Because it narrows what was validated, it carries the same approval bar as a Constitution change:

- Approval is required from **both** the Team Lead **and** the Compliance Reviewer.
- Approval must be recorded in the pull request with approver names, approval date, justification, and risk impact statement.
- Must-have features under feature.md §6 cannot be waived. Never-cut features F12, F19, F20 and F24 cannot be waived under any circumstance.
- Every active waiver must be listed in the run record and logged in docs/progress-log.md.
- A waiver applies to a single named run. It does not carry forward automatically.

## 12. Operational Discipline
- Run this harness before milestone review demos.
- Run this harness after any change affecting workflow rules, approvals, safety, or routing.
- Do not claim cycle-time/error improvements unless accompanied by harness evidence.
- Retain prior run records to support trend and drift analysis.
