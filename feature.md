# Feature Request — Admin Workflow Agent

**Program:** AI Champs Hackathon
**Track:** Healthcare — Internal Process Optimization
**Stack:** Microsoft Agent Framework (MAF) + Copilot SDK
**Status:** Draft v2 — for review
**Owner:** _(team name)_
**Date:** 2026-07-31

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
| **F6** | Provisional routing policy | Allows provisional progression only when confidence threshold and policy rules are met. | Provisional cases are clearly marked and re-evaluated on new data. | Cycle time | M |
| **F7** | Explainable routing | Routes cases using inspectable rules and returns one-line rationale. | Routing accuracy and reason visibility targets are met. | Both | S |
| **F8** | Duplicate detection | Flags likely duplicate case submissions and prevents reprocessing. | Duplicate sample cases are flagged consistently. | Fewer errors | S |

### 5.2 Workflow Orchestration and Approvals

| ID | Feature | What it does | Done when | Value | Size |
|---|---|---|---|---|---|
| **F9** | Handoff summary drafting | Drafts concise case handoff summaries for receiving teams. | Reviewer-ready draft appears with editable fields. | Cycle time | M |
| **F10** | Case record updates | Appends tests/medications-related administrative artifacts to case record with timestamp and source context. | New artifacts are persisted and traceable. | Fewer errors | M |
| **F11** | Parallel approval orchestration | Opens role-based approvals in parallel where policy allows (insurance, operations, diagnostics, legal, finance). | Approval state shows parallel tasks and blockers. | Cycle time | M |
| **F12** | Human approval actions | Supports approve/edit/reject/return-for-rework actions with rationale capture. | All actions work and state transitions are correct. | Both | M |
| **F13** | Critical escalation packet | Auto-prepares and routes escalation packet for critical-condition signals to clinical authority. | Escalation packet completeness target is met. | Fewer errors | M |
| **F14** | Status board and blockers | Displays stage, owner, elapsed time, approvals, blockers, and provisional flags. | Dashboard shows current state for all in-flight cases. | Cycle time | S |
| **F15** | SLA timers and alerts | Tracks approval and stage SLAs and flags breaches early. | SLA breaches are visible and actionable. | Cycle time | S |

### 5.3 Governance, Safety, and Release Gates

| ID | Feature | What it does | Done when | Value | Size |
|---|---|---|---|---|---|
| **F16** | Clinical clearance gate | Prevents release progression until authorized clinical clearance is recorded. | No case advances to release path without clearance token. | Fewer errors | M |
| **F17** | Financial clearance gate | Prevents release progression until required financial clearance is complete. | No case advances to release path without finance clearance token. | Both | M |
| **F18** | Release routing gate | Routes for release only when all mandatory gates and data completeness checks pass. | Release route never bypasses blocked prerequisites. | Both | S |
| **F19** | Stage-aware safety boundary | Enforces non-clinical-only autonomous behavior across all stages. | Out-of-bounds requests are consistently refused and escalated. | Fewer errors | M |
| **F20** | Audit and replay trail | Stores full case lineage for compliance reconstruction and replay. | Random sampled cases are fully reconstructable. | Fewer errors | M |
| **F21** | Eval harness | Fixed test set + run script + scorecard for repeatable quality and latency checks. | `run_eval` produces repeatable scorecard output. | Both | M |
| **F22** | Chat surface | Supports case submit, status checks, approvals, and escalations via conversation. | Full admin journey can be completed through chat flow. | Cycle time | S |
| **F23** | Policy version control | Tracks routing/approval policy versions and effective dates. | Each decision is traceable to a policy version. | Fewer errors | S |
| **F24** | Governance enforcement | Enforces constitution compliance and mandatory progress logging workflow. | No change proceeds without constitution and progress log checks. | Both | S |

**Nice-to-have, only if time permits:** bulk case ingestion, expanded explanation traces, and policy simulation tooling.

---

## 6. Priority — what we cut first

| Tier | Features | Rule |
|---|---|---|
| **Must have** | F1, F2, F4, F7, F11, F12, F16, F17, F18, F19, F20, F24 | Without these there is no safe demo and no governance story |
| **Should have** | F3, F5, F6, F8, F9, F10, F13, F14, F21, F22 | Cut only if genuinely out of time |
| **Nice to have** | F15, F23 | Cut freely |

**Never cut:** F12 (human approval actions), F19 (safety boundary), F20 (audit trail), F24 (governance enforcement). These are what make it a healthcare product rather than a script.

---

## 7. Success Metrics

Small, provable, and directly tied to the two expected values.

### Lower cycle time

| Metric | Target | How we measure |
|---|---|---|
| End-to-end time per item | Agent path measurably faster than manual | Stopwatch both paths in the demo, same document |
| Human touches per item | Down from ~6 to 1 | Count the handoffs, before vs after |
| Time to first action | < 30 seconds from intake to draft ready | Timestamped in the status board |

Validation rule: cycle-time claims are valid only if confirmed through a passing run in [`docs/multipass-validation-harness.md`](docs/multipass-validation-harness.md).

### Fewer errors

| Metric | Target | How we measure |
|---|---|---|
| Field extraction accuracy | ≥ 85% of fields correct | 20 sample case documents, human-graded |
| Missing-field detection | Catches every seeded omission | 10 documents with fields deliberately removed |
| Routing accuracy | ≥ 9 / 10 correct | 10 sample items with known correct queues |
| First-pass completeness | ≥ 90% of items reach routing with complete data | Count items that needed a rework loop |
| Unapproved sends | **0** | Verified live in demo |

Validation rule: error-rate claims are valid only if confirmed through a passing run in [`docs/multipass-validation-harness.md`](docs/multipass-validation-harness.md).

> We are deliberately **not** claiming dollar savings or FTE reduction. We claim cycle time and error rate, because those are the stated expected values and we can actually measure them in three weeks.

---

## 8. Demo Script

1. **The manual baseline.** Show a sample arriving case document. Walk through what a coordinator does by hand. Put a stopwatch on it.
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
- **Routing rules (F5)** — keep them declarative and in a config file, not buried in code. A reviewer must be able to read them.
- **Observability** — turn on MAF's built-in tracing from day one; F20 replay-grade audit then costs us very little.
- **Data** — all synthetic. Generate representative sample patient-case artifacts. Record provenance in `data/README.md`.

---

## 10. Assumptions & Constraints

- No production system access; no real patient data.
- The agent is an **assistant**, not a decision-maker. Every outbound action is human-approved.
- One patient-journey scope only. Resist extra domain expansion during the hackathon — design for future extension, do not build it now.
- Routing rules must be explainable to a non-technical reviewer.

---

## 11. Milestones

| Date | Deliverable |
|---|---|
| **7/30** | This spec + repo skeleton + sample documents |
| Week 1 | F1-F8 working. Intake, backfill, quality checks, and routing baseline stable. |
| Week 2 | F9-F15 working. Approvals, escalation packet, visibility, and SLA behavior stable. |
| Week 3 | F16-F24 working. Clearance gates, release gating, safety, audit, governance, and eval run complete. |
| Review | Scorecard + live demo + "what production would need" slide |

---

## 12. Governance and Execution Discipline

1. Constitution-first rule: if any planned implementation conflicts with [`docs/constitution.md`](docs/constitution.md), implementation stops and is escalated.
2. Immutable-by-default Constitution: edits to [`docs/constitution.md`](docs/constitution.md) require explicit Team Lead + Compliance Reviewer approval recorded in PR.
3. Mandatory progress tracking: every change to requirements, design, code, test, or docs must be logged in [`docs/progress-log.md`](docs/progress-log.md).
4. No silent scope drift: any expansion to features, approvals, or automation boundaries requires a corresponding update in both this feature spec and the progress log before build work continues.
5. Mandatory multipass gate: delivery milestones and demo claims must pass the multipass harness in [`docs/multipass-validation-harness.md`](docs/multipass-validation-harness.md).

---

## 13. Open Questions for the Reviewers

1. **Journey scope.** We picked full patient administrative journey orchestration to remove friction across intake, approvals, escalation, and release. Confirm this scope is acceptable for review.
2. **Sample data.** Is there a synthetic dataset the program wants us to standardise on, or do we generate our own?
3. **Baseline.** For the cycle-time claim, is a stopwatched manual walkthrough acceptable evidence, or do you want something stronger?
4. **Guardrail wording.** Is there required compliance or safety language the program wants reused across all teams?
5. **Packaging.** For the marketplace offer, should the routing rules be customer-configurable at install time, or fixed?
