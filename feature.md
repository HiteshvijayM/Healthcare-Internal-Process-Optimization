# Feature Request — Admin Workflow Agent

**Program:** AI Champs Hackathon
**Track:** Healthcare — Internal Process Optimization
**Stack:** Microsoft Agent Framework (MAF) + Copilot SDK
**Status:** Draft v2 — for review
**Owner:** Team Lead (role defined in [`docs/multipass-validation-harness.md`](docs/multipass-validation-harness.md) §4.1)

**Governance baseline (non-negotiable):**
- [`docs/constitution.md`](docs/constitution.md) defines system constraints and cannot be changed without explicit Team Lead + Compliance Reviewer approval.
- [`docs/progress-log.md`](docs/progress-log.md) is mandatory for tracking planned, in-progress, and implemented work. Every change must be logged.
- [`docs/multipass-validation-harness.md`](docs/multipass-validation-harness.md) is the one-stop validation gate; readiness claims require a passing multipass run.

---

## 1. The Assignment

| Field | Value |
|---|---|
| **Industry** | Healthcare |
| **Agent** | Internal Process Optimization |
| **Problem statement** | Administrative workflows involve repetitive tasks, handoffs, and delays. |
| **Expected value** | Lower cycle time; fewer errors |

**One-line pitch:** an administrative orchestration agent that carries a patient case from arrival through routing, approvals, escalation, and release readiness — minimizing delay while preserving human clinical authority.

---

## 2. The Problem, Concretely

The problem statement names three things. Here is what each one actually looks like on the ground:

| Named problem | What it looks like today |
|---|---|
| **Repetitive tasks** | A request arrives as a fax, PDF or email. A coordinator reads it and re-types the same 8–10 fields into a system. Every single time. |
| **Handoffs** | Intake desk → completeness check → chase the sender for missing info → decide which team owns it → write a handoff note → supervisor approves. Six desks, six queues. |
| **Delays** | The item sits between every one of those steps. Most of the elapsed time is waiting, not working. |

And the errors that follow: items advance with fields missing, get routed to the wrong team, get re-keyed with typos, or get worked twice because nobody noticed a duplicate.

---

## 3. What We're Building

**One orchestration assistant, one end-to-end patient journey, done safely.**

Chosen workflow: **patient administrative journey orchestration** from arrival to release routing. This keeps focus on administrative friction reduction while preserving strict boundaries around clinical decisions.

### Before → After

```
BEFORE (manual)
  Patient arrives → details captured repeatedly in separate desks
  → incomplete data creates loops and delays
  → case routing and approvals happen sequentially with queue waiting
  → critical findings are escalated manually
  → clinical clearance and finance clearance happen late and disconnected
  → release waits on handoffs
  ≈ many touchpoints, most elapsed time is waiting

AFTER (with assistant)
  Patient arrives → assistant collates known records + captures missing data
  → runs completeness checks + provisional routing rules
  → opens parallel admin approval tasks where possible
  → auto-prepares escalation packet for critical conditions
  → waits for human clinical clearance and human financial clearance
  → routes to release when all gates are complete
  ≈ fewer waits, fewer manual re-entry loops, faster progression
```

The assistant automates administrative coordination, collation, and routing. **Clinical decisions remain human-only.**

---

## 4. Scope

### In scope
- One patient journey, end to end, demo-able.
- **Synthetic / de-identified sample documents only.** No real PHI at any point.
- A happy path and broken paths (missing info, misroute, rejection, delayed approval) — all handled properly.
- Measurable before/after numbers for cycle time and errors.
- Mandatory compliance with [`docs/constitution.md`](docs/constitution.md).
- Mandatory change tracking in [`docs/progress-log.md`](docs/progress-log.md).

### Out of scope — say this in the review
- Live EHR integration (Epic / Oracle Health). We use realistically-shaped sample data instead.
- Any autonomous clinical, diagnostic, or medical-necessity decision. The assistant never approves or denies care.
- Real submissions to any payer or external body.
- Prior authorisation decisioning — deliberately avoided. It is heavily regulated (CMS-0057-F; California SB 1120 bars AI from making medical-necessity determinations) and is the wrong bet for a hackathon.
- Multi-tenancy, SSO, production hosting.

---

## 5. Features

Every feature traces to one of the two expected values. If it traces to neither, we don't build it.

### 5.1 Intake, Data Quality, and Routing

| ID | Feature | What it does | Done when | Value | Size |
|---|---|---|---|---|---|
| **F1** | Register arriving case | Registers arriving patient case as a tracked item with case ID and timestamp. | New case appears with stage and owner placeholders. | Cycle time | S |
| **F2** | Extract case details | Produces structured details needed for downstream admin processing. | Fields extracted correctly on sample set (§7). | Both | M |
| **F3** | Backfill from records | Searches available records to fill missing required fields before requesting new input. | Backfillable fields are auto-filled with provenance tag. | Both | M |
| **F4** | Completeness and plausibility checks | Flags missing, contradictory, or implausible data before unsafe progression. | Missing and implausible values are flagged with reasons. | Fewer errors | S |
| **F5** | Missing-data tasking | Creates targeted completion tasks for required expert/admin owners when mandatory data remains unresolved. | Open tasks exist with clear owner and due state. | Both | S |
| **F6** | Provisional routing policy | Allows provisional progression only when confidence threshold and policy rules are met. | Provisional cases are clearly marked and re-evaluated on new data, per **P1** (§5.4). | Cycle time | M |
| **F7** | Explainable routing | Routes cases using inspectable rules and returns one-line rationale. | Routing accuracy and reason visibility targets are met. | Both | S |
| **F8** | Duplicate detection | Flags likely duplicate case submissions and prevents reprocessing. | Duplicate sample cases are flagged consistently within the **P2** window (§5.4). | Fewer errors | S |

### 5.2 Workflow Orchestration and Approvals

| ID | Feature | What it does | Done when | Value | Size |
|---|---|---|---|---|---|
| **F9** | Handoff summary drafting | Drafts concise case handoff summaries for receiving teams. | Reviewer-ready draft appears with editable fields. | Cycle time | M |
| **F10** | Case record updates | Appends tests/medications-related administrative artifacts to case record with timestamp and source context. | New artifacts are persisted and traceable. | Fewer errors | M |
| **F11** | Parallel approval orchestration | Opens role-based approvals in parallel where policy allows (insurance, operations, diagnostics, legal, finance). | Approval state shows parallel tasks and blockers. | Cycle time | M |
| **F12** | Human approval actions | Supports approve/edit/reject/return-for-rework actions with rationale capture. | All actions work and state transitions are correct. | Both | M |
| **F13** | Critical escalation packet | Auto-prepares and routes escalation packet for critical-condition signals to clinical authority. | All mandatory packet fields present per **P3** (§5.4); no partial sends. | Fewer errors | M |
| **F14** | Status board and blockers | Displays stage, owner, elapsed time, approvals, blockers, and provisional flags. | Dashboard shows current state for all in-flight cases. | Cycle time | S |
| **F15** | SLA timers and alerts | Tracks approval and stage SLAs and flags breaches early. | Timers and alerts fire per **P4** and **P5** (§5.4); breaches are visible and actionable. | Cycle time | S |

### 5.3 Governance, Safety, and Release Gates

| ID | Feature | What it does | Done when | Value | Size |
|---|---|---|---|---|---|
| **F16** | Clinical clearance gate | Prevents release progression until authorized clinical clearance is recorded. | No case advances to release path without clearance token. | Fewer errors | M |
| **F17** | Financial clearance gate | Prevents release progression until required financial clearance is complete. | No case advances to release path without finance clearance token. | Both | M |
| **F18** | Release routing gate | Routes for release only when all mandatory gates and data completeness checks pass. | Release route never bypasses blocked prerequisites. | Both | S |
| **F19** | Stage-aware safety boundary | Enforces non-clinical-only autonomous behavior across all stages. | Out-of-bounds requests are consistently refused and escalated. | Fewer errors | M |
| **F20** | Audit and replay trail | Stores full case lineage for compliance reconstruction and replay. | Random sampled cases are fully reconstructable within the **P8** retention window (§5.4). | Fewer errors | M |
| **F21** | Eval harness | Fixed test set + run script + scorecard for repeatable quality and latency checks. | `run_eval` produces repeatable scorecard output. | Both | M |
| **F22** | Chat surface | Supports case submit, status checks, approvals, and escalations via conversation. | Full admin journey can be completed through the **P9** surface (§5.4). | Cycle time | S |
| **F23** | Policy version control | Tracks routing/approval policy versions and effective dates. | Each decision is traceable to a policy version. | Fewer errors | S |
| **F24** | Governance enforcement | Enforces constitution compliance and mandatory progress logging workflow. | No change proceeds without constitution and progress log checks. | Both | S |

**Nice-to-have, only if time permits:** bulk case ingestion, expanded explanation traces, and policy simulation tooling.

### 5.4 Policy Thresholds and SLAs

Every number the validation harness scores against lives here, in one place a non-technical reviewer can read. Changing any value requires a progress-log entry and re-running any harness pass that depended on it.

| ID | Policy | Value |
|---|---|---|
| **P1** | Provisional routing confidence (F6) | Permitted only when routing confidence is **≥ 0.80** *and* both `patient_reference` and `requested_service` are present. Never permitted while a critical signal is active or a clearance gate is pending. |
| **P2** | Duplicate detection (F8) | Two independent matches. **(a) Key match — 72 hours** from first receipt, on sender + patient reference + requested service. **(b) Identity match — no time bound**, on document identity: the same immutable source-document identifier, or identical normalized content where normalization strips transport-added material only (cover sheets, routing headers, arrival timestamps, watermarks, re-transmission banners). Channel does not matter for either — a fax resend of an email request is still a duplicate. The 72-hour window bounds the key match only and must never suppress an identity match. The window is a tunable policy parameter, not a constant. On match: flag and hold for human adjudication — never auto-discard, never auto-merge. |
| **P3** | Escalation packet completeness (F13) | **100% of mandatory fields**, no partial sends. Mandatory: case ID, patient reference, requester, critical-signal description, source document reference, timestamp, designated clinical recipient. |
| **P4** | Approval SLAs (F15) | **Defaults:** Routine **2 business days** · Urgent **4 hours** · Critical escalation acknowledgement **30 minutes**. **Resolution model:** an SLA resolves per **urgency class *and* service line**. A service line may register an override that is *shorter* than the default; a longer override requires Compliance Reviewer approval. **Floor:** a critical-acknowledgement override MUST remain strictly greater than **P10**, and the policy bundle MUST reject at freeze time any override that is not — otherwise the P10 deadline becomes unsatisfiable and every escalation in that service line would sit as a permanent governance blocker. Where a service line registers no override the default applies. Where a service line registers no override the default applies. The value actually applied must be recorded against the item, so a breach is audited against the value in force at the time. The critical acknowledgement clock starts **at detection of the critical signal**, not at dispatch, and must not start where no on-call clinical coverage is configured (see §4.2 of the harness — raise a governance blocker instead). |
| **P5** | SLA alert timing (F15) | Early-warning alert at **80% of SLA elapsed**. Breach recorded at 100%. |
| **P6** | Rework-loop limit | Maximum **2** rework loops per case, then mandatory human escalation. A third loop is a Sev 2 defect. |
| **P7** | Run-to-run drift tolerance (F21) | Aggregate scores within **±2 percentage points** between runs on the same dataset and build. Per-case outcome classifications must be **100% identical** — determinism is not negotiable. |
| **P8** | Audit retention (F20) | Full case lineage retained for the **entire project lifetime, minimum 90 days**. No purge before review sign-off. *Production would require 6 years under HIPAA — out of scope here, but named so the gap is visible. Raising this value is a hard precondition of ever processing real data.* |
| **P9** | Chat surface scope (F22) | A **single web/in-app conversational surface**, one demo tenant, one authenticated reviewer session. Teams, mobile, and email-in surfaces are out of scope. |
| **P10** | Escalation dispatch-approval deadline (F13) | **10 minutes** from the escalation packet becoming complete and dispatch approval being raised. Must always be **strictly shorter** than the critical acknowledgement SLA applied to the case under P4, which the P4 override floor guarantees. Dispatch approval is a completeness-and-addressing check, not a clinical judgement, so it consumes the minority of the acknowledgement window and leaves the clinician the remainder — two-thirds at the 30-minute default. On breach: record the breach, keep the packet undispatched, and escalate to the named alternate approver (harness §4.2). Breach never authorises dispatch without an approval. |
| **P11** | Critical-condition signal register (F13, F19) | Detection matches **only** against the versioned register in [`docs/critical-condition-register.md`](docs/critical-condition-register.md). No inference beyond registered entries. Where the register is absent, empty, or its version cannot be resolved: raise a governance blocker and hold the case. Absence of a match must never be reported as evidence that no critical condition is present. Register in force for this build: **`CCR-DEMO-v1`**. |

P1, P3, P10 and P11 are safety-bearing. Loosening any of them requires Compliance Reviewer approval, not just Team Lead.

**Amendment history.** P2 (identity match), P4 (per-service-line resolution model), P10 and P11 were ratified under CHG-021. P1 was re-confirmed at 0.80 unchanged.

---

## 6. Priority — what we cut first

| Tier | Features | Rule |
|---|---|---|
| **Must have** | F1, F2, F4, F7, F11, F12, F15, F16, F17, F18, F19, F20, F23, F24 | Without these there is no safe demo and no governance story |
| **Should have** | F3, F5, F6, F8, F9, F10, F13, F14, F21, F22 | Cut only if genuinely out of time |

**Never cut:** F12 (human approval actions), F19 (safety boundary), F20 (audit trail), F24 (governance enforcement). These are what make it a healthcare product rather than a script.

**Cutting rule.** F15 and F23 are Must-have because the multipass harness scores them inside hard-gate and near-hard-gate passes; they cannot be dropped without failing validation. Any Should-have feature that is cut must be recorded as a formal waiver under [`docs/multipass-validation-harness.md`](docs/multipass-validation-harness.md) §11 and logged in [`docs/progress-log.md`](docs/progress-log.md) before the affected pass is scored.

---

## 7. Success Metrics

Small, provable, and directly tied to the two expected values.

### Lower cycle time

| Metric | Target | How we measure |
|---|---|---|
| End-to-end time per item | Agent path measurably faster than manual | Stopwatch both paths under the §13.3 baseline protocol — same document, 3-run manual median, reported as a range |
| Avoidable serial handoffs per item | Reduced from ~6 sequential desks by parallelising eligible approvals and tasking | Count the steps that must happen *in sequence*, before vs after |
| Time to first action | **< 30 seconds at the 95th percentile** (nearest-rank) from intake to draft ready | Timestamped in the status board, over every graded case. The graded sample size is reported alongside the figure, and every case above the bound is itemised with its cause. |

> We measure *serial* handoffs, not total human touches. The journey deliberately keeps multiple humans in the loop — five role approvers (F11) plus mandatory clinical (F16) and financial (F17) clearance gates. The win is that those approvals run in parallel instead of queueing behind each other, not that people are removed.

Validation rule: cycle-time claims are valid only if confirmed through a passing run in [`docs/multipass-validation-harness.md`](docs/multipass-validation-harness.md).

### Fewer errors

| Metric | Target | How we measure |
|---|---|---|
| Field extraction accuracy | ≥ 85% of graded fields correct | 20 sample case documents × 7 graded fields (n = 140), human-graded against `data/sample/answer-key.json`. `supporting_notes` is extracted but not graded. |
| Missing-field detection | Catches every seeded omission | 10 documents with fields deliberately removed |
| Routing accuracy | ≥ 9 / 10 correct | 10 sample items with known correct queues |
| First-pass completeness | ≥ 90% of items reach routing with complete data | Count items that needed a rework loop |
| Unapproved sends | **0** | Verified live in demo |

Validation rule: error-rate claims are valid only if confirmed through a passing run in [`docs/multipass-validation-harness.md`](docs/multipass-validation-harness.md).

**Reporting rule.** Every percentage above is reported with its graded sample size (`n`), and every percentile figure names its estimator. A percentage without a denominator is not a measurement and may not be cited as evidence.

> We are deliberately **not** claiming dollar savings or FTE reduction. We claim cycle time and error rate, because those are the stated expected values and they are the ones we can actually measure within this build's scope.

---

## 8. Demo Script

1. **The manual baseline.** Show a sample arriving case document. Walk through what a coordinator does by hand. Time it under the §13.3 protocol — the median of three runs is the number we quote, not the run happening on stage.
2. **The agent path.** Drop the same document in. Fields extracted, item registered, queue chosen with a reason, handoff note drafted. Stop the watch. Compare.
3. **The broken path.** Drop in a document with a missing field. Agent holds the item, names what's missing, drafts the chase message.
4. **Human control.** Reviewer edits the draft, approves. Then reject one and show it goes back a stage. Show that nothing ever sent itself.
5. **Safety.** Ask the agent a clinical question. It declines and escalates.
6. **Proof.** Open the status board — stages, owners, elapsed time. Run the eval script live and show the scorecard.
7. **Multipass validation proof.** Present the latest run summary from [`docs/multipass-validation-harness.md`](docs/multipass-validation-harness.md), including intake-era coverage status and go/no-go outcome.

---

## 9. Technical Notes

- **MAF** — model this as a **workflow**, not a single agent. The stages (arrive/register → enrich/backfill → validate → route/provisional-route → approvals/escalation → clinical gate → finance gate → release route) map onto workflow executors, giving checkpointing, resumability, and safe human lockpoints.
- **Copilot SDK** — the conversational surface for F22: submit a case, ask for status, approve, and monitor escalations.
- **Document reading** — start with text-layer PDFs and email text. Add scanned/OCR documents only once the clean path works.
- **Routing rules (F7)** — keep them declarative and in a config file, not buried in code. A reviewer must be able to read them.
- **Observability** — turn on MAF's built-in tracing from day one; F20 replay-grade audit then costs us very little.
- **Data** — all synthetic. Sample patient-case artifacts live in [`data/sample/`](data/sample/), with provenance recorded in [`data/README.md`](data/README.md).

---

## 10. Assumptions & Constraints

- No production system access; no real patient data.
- The agent is an **assistant**, not a decision-maker. Every outbound action is human-approved.
- One patient-journey scope only. Resist extra domain expansion during the hackathon — design for future extension, do not build it now.
- Routing rules must be explainable to a non-technical reviewer.

---

## 11. Milestones

Milestones are sequential and gated by completion, not by calendar date. A milestone is reached only when its exit gate passes.

| Milestone | Deliverable | Exit gate |
|---|---|---|
| **M0 — Foundation** | Spec, governance baseline, repo skeleton, synthetic sample dataset | Pass 0 governance pre-check clean; dataset manifest recorded |
| **M1 — Intake baseline** | F1-F8 working. Intake, backfill, quality checks, and routing baseline stable. | Harness Passes 1 and 2 |
| **M2 — Orchestration** | F9-F15 working. Approvals, escalation packet, visibility, and SLA behavior stable. | Harness Pass 3 |
| **M3 — Governance** | F16-F24 working. Clearance gates, release gating, safety, audit, governance, and eval run complete. | Harness Passes 4, 5 and 6 |
| **M4 — Review** | Scorecard + live demo + "what production would need" slide | Full multipass run recorded as Go in [`docs/progress-log.md`](docs/progress-log.md) |

---

## 12. Governance and Execution Discipline

1. Constitution-first rule: if any planned implementation conflicts with [`docs/constitution.md`](docs/constitution.md), implementation stops and is escalated.
2. Immutable-by-default Constitution: edits to [`docs/constitution.md`](docs/constitution.md) require explicit Team Lead + Compliance Reviewer approval recorded in PR.
3. Mandatory progress tracking: every change to requirements, design, code, test, or docs must be logged in [`docs/progress-log.md`](docs/progress-log.md).
4. No silent scope drift: any expansion to features, approvals, or automation boundaries requires a corresponding update in both this feature spec and the progress log before build work continues.
5. Mandatory multipass gate: delivery milestones and demo claims must pass the multipass harness in [`docs/multipass-validation-harness.md`](docs/multipass-validation-harness.md).

---

## 13. Resolved Decisions

These were previously open questions for reviewers. They are now decided. Each records the decision, the reasoning, and where it takes effect. Reopening any of them requires a progress-log entry and re-running any harness pass that depended on it.

### 13.1 Journey scope — **Decided: full patient administrative journey orchestration**

Scope is arrival through release routing, covering intake, data quality, routing, parallel approvals, escalation, and the clinical and financial clearance gates. This is the scope the F1-F24 catalogue, the seven harness passes, and `SYN-CASESET-v1` are all built against.

It is deliberately bounded by §4: no live EHR integration, no payer submissions, no prior-authorisation decisioning, and no autonomous clinical judgement. The scope is wide across *administrative* steps and deliberately narrow on *clinical* ones.

### 13.2 Sample data — **Decided: we generate our own, and it is `SYN-CASESET-v1`**

No external dataset is adopted. [`data/sample/`](data/sample/) holds 20 hand-authored synthetic case documents with a JSON answer key, and [`data/README.md`](data/README.md) carries the provenance statement required by [`docs/constitution.md`](docs/constitution.md) §3.

Generating our own was the right call because the dataset needs seeded conditions an off-the-shelf set would not contain — deliberate omissions across four resolution modes, duplicates, a near-duplicate that must *not* flag, misroute traps, and false-positive traps on `Not applicable` fields. Those traps are what make the error-rate metric meaningful rather than decorative.

### 13.3 Baseline evidence — **Decided: stopwatched manual walkthrough, under a defined protocol**

A stopwatched manual walkthrough is accepted, but only if it is run properly. A single casual timing is not evidence. The protocol is:

| Rule | Requirement |
|---|---|
| Same input | Both paths process the identical document from the identical starting state |
| Same endpoint | Both timed from document arrival to "ready for human approval" — not to final send, which is human-paced and would flatter the agent |
| Repetition | **3 runs of the manual path**, median reported. Single runs are discarded. |
| Operator | Manual path performed by someone who has not seen the agent's output for that document |
| Recording | All timings recorded in the run record with timestamps, alongside the build and dataset versions |
| Reporting | Claim stated as a **range across the sampled documents**, never as a single headline number |

This is honest about what it is: a small-sample demonstration, not a controlled study. The three-run median and the range-based reporting are what stop it overstating.

### 13.4 Guardrail wording — **Decided: our own, and it is canonical**

No external program language is adopted. The guardrail language for this project is [`docs/constitution.md`](docs/constitution.md) §5 together with the non-negotiable constraints block in [`prompts/specify-prompt.md`](prompts/specify-prompt.md).

Those two sources are canonical. Any safety or compliance wording that appears in a demo, README, slide, or agent response must be traceable to them, and must not soften them. If a program-level standard is issued later, adopting it is a Constitution amendment under §2 and requires Team Lead plus Compliance Reviewer approval.

### 13.5 Packaging — **Decided: out of scope, question withdrawn**

The prior question asked whether routing rules should be customer-configurable "for the marketplace offer". There is no marketplace offer. §4 already excludes multi-tenancy, SSO, and production hosting, so the question contradicted the stated scope.

Routing rules are **fixed and declarative** for this build, held in a config file and readable by a non-technical reviewer per §9. They are not customer-configurable, and configurability is not a deliverable.
