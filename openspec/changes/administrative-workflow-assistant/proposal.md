## Why

Administrative work in a clinic or hospital is slow for three compounding reasons: it is **repetitive** (an unstructured document arrives and a coordinator re-types the same handful of details into a system, every time, all day), it is **full of handoffs** (intake desk → completeness check → chase-the-sender loop → routing decision → drafting step → supervisor approval, each a different person and a different queue), and it is **full of delay** (most elapsed time on any item is spent waiting between steps, not being worked on).

The errors follow from the same causes: items advance with details missing, get sent to the wrong team, get re-keyed with mistakes, and the same request gets worked twice because nobody noticed it had already arrived. This change proposes an **Administrative Workflow Assistant** that reduces elapsed time and mistakes by having software do the reading, typing, checking and routing — while **a human keeps every decision**.

## What Changes

The assistant orchestrates a patient case from arrival through release routing. Every capability below is administrative; none is clinical.

**Intake and understanding**
- Register an arriving patient case as a tracked work item with an identifier and arrival timestamp.
- Produce a structured case record of the key details required for safe administrative progression.
- Backfill missing required details from available records before asking a human for them, recording provenance for each backfilled value.

**Checking**
- Check the record for completeness and plausibility, naming anything missing or implausible before the item is allowed to advance.
- Create targeted completion tasks for the relevant expert/admin owner when mandatory data remains unresolved after backfill.
- Permit provisional routing only when policy confidence thresholds are met (**P1**), marking the case provisional pending completion.
- Recognise and flag probable duplicate submissions (**P2**) instead of allowing the same work to be done twice.

**Progressing**
- Prepare targeted requests for exactly the missing information.
- Determine routing using explainable, declarative rules and state the reason in one line, with an inspectable rule trace.
- Append tests/medications-related administrative artifacts to the case record with timestamp and source context.
- Open role-based approvals (insurance, operations, diagnostics, legal, finance) in parallel where policy allows, and identify blocking approvals.
- Auto-prepare and route a complete escalation packet (**P3**) to the designated clinical authority when a critical-condition signal appears in test/diagnostic inputs.

**Human control**
- Present all drafts and route proposals to authorized humans, who can approve, edit, reject, or return for rework.
- **BREAKING (relative to any fully-automated alternative):** the assistant SHALL NOT send, submit, escalate clinically, finalize clearance, or route for release without a recorded explicit human approval. There is no bypass, no override flag, and no "auto-approve" configuration.
- Return rejected cases to the correct prior stage with captured rationale, bounded by the rework-loop limit (**P6**).
- Retain human-edited output as the authoritative version.
- Enforce clinical clearance and financial clearance as mandatory human gates before release routing.

**Visibility, safety and proof**
- Show stage, owner, elapsed time, approval statuses, blockers, provisional flags and unresolved data tasks for every in-flight item; show total elapsed time for completed items so it can be compared against doing the same work by hand.
- Refuse requests for autonomous diagnosis, treatment recommendation, medical-necessity determination, clinical clearance authorization, or discharge/release authorization, and direct them to qualified humans.
- Retain a replay-grade audit trail sufficient to reconstruct any single case end to end, with personal identifiers masked.
- Provide a repeatable evaluation harness that re-measures accuracy and speed on demand against the fixed `SYN-CASESET-v1` sample set.

**Governance (non-negotiable)**
- [`docs/constitution.md`](../../../docs/constitution.md) is **authoritative and non-overridable by any execution agent or automation**. A verbatim copy is kept at `openspec/constitution.md` solely so OpenSpec tooling has a local reference; `docs/constitution.md` remains the single source of truth and wins on any divergence. No proposal, design, task, prompt, model instruction, or configuration may relax, reinterpret, or work around it. A conflicting request stops work and escalates to Team Lead + Compliance Reviewer (constitution §2, §8).
- Only synthetic or de-identified data is ever used (`SYN-CASESET-v1`). No real patient information at any point.
- Every implementation change is logged in [`docs/progress-log.md`](../../../docs/progress-log.md).

## Capabilities

### New Capabilities

- `case-intake`: Registering an arriving case as a tracked work item, extracting a structured case record, and backfilling missing required fields from available records with provenance. Covers **F1–F3**.
- `case-data-quality`: Completeness and plausibility checking, targeted missing-data tasking to named owners, and probable-duplicate detection. Covers **F4, F5, F8**.
- `explainable-routing`: Declarative, inspectable routing rules producing a one-line reason plus a rule trace, plus the confidence-gated provisional routing policy and policy versioning. Covers **F6, F7, F23**.
- `human-approval-control`: Draft preparation and the approve / edit / reject / return-for-rework action set, retention of human edits as authoritative, and the absolute no-unapproved-action rule. Covers **F9, F12**.
- `approval-orchestration`: Parallel role-based approvals across insurance, operations, diagnostics, legal and finance, blocking-approval identification, case-record artifact appends, and SLA timers and alerts. Covers **F10, F11, F15**.
- `clinical-escalation`: Detecting a critical-condition signal in test/diagnostic inputs and auto-preparing plus routing a complete escalation packet to the designated clinical authority, without making a clinical decision. Covers **F13**.
- `clearance-and-release-gates`: Mandatory human clinical clearance, mandatory human financial clearance, and the release-routing gate that cannot be bypassed. Covers **F16–F18**.
- `workflow-visibility`: The status view showing stage, owner, elapsed time, approvals, blockers and provisional flags for in-flight items, total elapsed time for completed items, and the conversational surface used to drive it. Covers **F14, F22**.
- `safety-boundary`: Consistent refusal and redirection of out-of-bounds clinical requests at every stage. Covers **F19**.
- `audit-and-compliance-trail`: Replay-grade case lineage for compliance reconstruction, identifier masking, retention, and governance enforcement of the constitution and progress-log workflow. Covers **F20, F24**.
- `evaluation-harness`: The fixed-dataset, repeatable accuracy and latency scorecard used to substantiate every quality and cycle-time claim. Covers **F21**.

### Modified Capabilities

None. `openspec/specs/` is empty — this is the first change in the repository, so every capability above is new.

## Impact

**Affected artifacts (this change is spec-only; no implementation code is created).**

- New: `openspec/changes/administrative-workflow-assistant/` — `proposal.md`, 11 delta specs, `design.md`, `tasks.md`.
- New: `openspec/constitution.md` — verbatim, unaltered copy of `docs/constitution.md` for OpenSpec tooling.
- Modified: `openspec/config.yaml` — project context and per-artifact rules encoding the governance constraints.
- Modified: [`docs/progress-log.md`](../../../docs/progress-log.md) — change entry, recorded assumptions, and the "Needs human decision" list.

**Traceability to existing project artifacts.** This proposal deliberately reuses, and does not restate or fork, the identifiers already agreed in the repository:

| Source | What is reused |
|---|---|
| [`feature.md`](../../../feature.md) §5 | Feature catalogue **F1–F24**; every capability above names the features it covers |
| [`feature.md`](../../../feature.md) §5.4 | Policy thresholds **P1–P9** (confidence, duplicate window, packet completeness, SLAs, alerts, rework limit, drift tolerance, retention, surface scope) |
| [`feature.md`](../../../feature.md) §7 | Success metric targets (extraction ≥ 85%, routing ≥ 9/10, first-pass completeness ≥ 90%, unapproved sends = 0, time-to-first-action < 30s) |
| [`feature.md`](../../../feature.md) §13.3 | Manual-baseline measurement protocol used for cycle-time claims |
| [`docs/multipass-validation-harness.md`](../../../docs/multipass-validation-harness.md) §4.1 | Approver role model and separation-of-duty rules |
| [`data/README.md`](../../../data/README.md) | `SYN-CASESET-v1` — 20 synthetic cases + answer key, with provenance |

**No impact on:** live EHR or production clinical systems, real insurers/payers/external bodies, prior-authorisation or coverage determination logic, autonomous clinical judgement, multi-organisation tenancy, SSO, or production hosting. All are explicitly out of scope and no interface to them is proposed.

**Deliberately not claimed:** financial savings or headcount reduction. The claimed values are lower cycle time and fewer errors, because those are the stated expected values and the only ones measurable within this scope.
