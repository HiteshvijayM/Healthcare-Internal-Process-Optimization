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
- Approver-role model defined for this run.
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
- Duplicate true-positive and false-positive rates
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
- Rework-loop count within acceptable limit
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
- Escalation packet field completeness and delivery path
- SLA breach alert timeliness
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
- Re-run consistency of outcome classifications
- Chat-flow completion across core journey
- Report generation completeness
- Metric drift between runs within tolerance

Exit rule:
- Repeat run produces stable scorecard outputs and complete conversational flow.

## 8. Intake-Era Scenario Trace Matrix

| Intake-Era Scenario | Current Coverage | Feature IDs | Acceptance Scenario Anchor |
|---|---|---|---|
| Patient/case arrives and details captured | Covered | F1, F2 | docs/specify-prompt.md Scenario 1 |
| Missing details detected before progress | Covered | F4 | docs/specify-prompt.md Scenario 2 |
| Missing details are requested/completed | Covered | F3, F5 | docs/specify-prompt.md Scenarios 2, 3 |
| Routing decision with explanation | Covered | F6, F7 | docs/specify-prompt.md Scenarios 3, 4 |
| Duplicate intake handled | Covered | F8 | docs/specify-prompt.md Scenario 7 |
| Human approval control maintained | Covered | F11, F12 | docs/specify-prompt.md Scenarios 6, 9 |
| No autonomous unsafe clinical action | Covered | F19 | docs/specify-prompt.md Scenario 13 |
| Auditability of each intake path | Covered | F20 | docs/specify-prompt.md Scenario 14 |

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

## 12. Operational Discipline
- Run this harness before milestone review demos.
- Run this harness after any change affecting workflow rules, approvals, safety, or routing.
- Do not claim cycle-time/error improvements unless accompanied by harness evidence.
- Retain prior run records to support trend and drift analysis.
