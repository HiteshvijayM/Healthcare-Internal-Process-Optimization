# `/specify` Prompt — Admin Workflow Agent

**Track:** Healthcare — Internal Process Optimization
**How to use:** paste everything inside the fenced block in §1 into your `specify` agent as a single message.

**Governance baseline (must be enforced):**
- [`docs/constitution.md`](../docs/constitution.md) is non-negotiable and immutable by default.
- [`docs/progress-log.md`](../docs/progress-log.md) must be updated for every change.
- [`docs/multipass-validation-harness.md`](../docs/multipass-validation-harness.md) is the one-stop readiness gate for scenario coverage and release claims.

**Rule being followed:** `/specify` describes **WHAT** and **WHY**, never **HOW**. Technology choices are deliberately withheld and belong in `/plan` — see §2.

---

## 1. The prompt

```text
Build an Administrative Workflow Assistant for a healthcare provider organisation.

WHY THIS EXISTS
Administrative work in a clinic or hospital is slow for three specific reasons, and they compound. First, it is repetitive: a request arrives as an unstructured document and a coordinator re-types the same handful of details into a system, every single time, all day. Second, it is full of handoffs: the item passes through an intake desk, a completeness check, a chase-the-sender loop, a routing decision, a drafting step, and a supervisor approval, and each of those is a different person and a different queue. Third, it is full of delay: most of the elapsed time on any item is spent waiting between steps, not being worked on.

The errors follow from the same causes. Items advance with details missing. They get sent to the wrong team. They get re-keyed with mistakes. The same request gets worked twice because nobody noticed it had already arrived.

We want to reduce the elapsed time it takes to process an administrative request, and reduce the number of mistakes made while processing it. We want to do that by having software do the reading, the typing, the checking and the routing, while a human keeps every decision.

WHO USES IT
- An intake coordinator who captures arrivals and validates case detail completeness.
- Operations, diagnostics, insurance, legal, and finance approvers who review case steps relevant to their role.
- A clinical escalation recipient (department head or assigned clinical authority) for critical-condition escalation handling.
- A team lead who needs to see what is in flight, who owns it, and how long it has been sitting.
- A compliance reviewer who must be able to reconstruct exactly what happened to any single item and why.

THE WORKFLOW BEING AUTOMATED
Administrative patient journey orchestration from arrival to release routing. A patient case arrives and details are captured. The assistant validates completeness, looks up existing records for missing values, performs provisional routing when policy allows, opens role-based parallel approvals, prepares escalation packets for critical conditions, supports clinical and financial clearance gates, and routes for release only after required gates are complete.

---

WHAT THE ASSISTANT MUST DO

Intake and understanding
- Accept an arriving patient case and register it as a tracked work item with an identifier and time of arrival.
- Produce a structured case record of key details required for safe administrative progression.
- If required details are missing, look through available records to backfill what can be reliably inferred.

Checking
- Check that record for completeness and plausibility, and clearly name anything that is missing or does not make sense, before the item is allowed to advance.
- If mandatory data remains missing after record lookup, create completion tasks for the relevant expert/admin owner.
- Allow provisional routing only when policy confidence thresholds are met, and mark the case as provisional pending completion.
- Recognise when an incoming request appears to duplicate one already in progress, and flag it instead of allowing the same work to be done twice.

Progressing
- When details are missing, prepare targeted requests for exactly the missing information.
- Determine routing using explainable rules and state the reason in one line.
- Update patient records with administrative artifacts related to prescribed tests or medications as they become available.
- Open role-based approvals (insurance, operations, diagnostics, legal, finance) in parallel where policy allows.
- If critical conditions are detected from tests/diagnostics inputs, auto-prepare and route an escalation packet to clinical authority.

Human control
- Present all drafts and route proposals to authorized humans, who can approve, edit, reject, or return for rework.
- Never send, submit, escalate clinically, finalize clearance, or route for release without required explicit human approvals.
- When something is rejected, return the case to the correct prior stage with rationale.
- Retain human-edited outputs as the authoritative version.
- Clinical clearance and financial clearance are mandatory human gates before release routing.

Visibility
- Show, for every item in progress, which stage it is in, who owns it, and how long it has been in progress.
- Make the total elapsed time for a completed item visible, so it can be compared against doing the same work by hand.
- Make all approval statuses and blockers visible, including provisional routing flags and unresolved data tasks.

---

ACCEPTANCE SCENARIOS

1. A complete incoming request is submitted. The assistant registers it and extracts its key details accurately into a structured record.
2. A case with required details missing is submitted. The assistant first backfills from records; unresolved fields are explicitly listed and routed to the correct expert/admin completion task.
3. If unresolved required data remains, the assistant applies confidence-threshold policy and either sets provisional routing with clear flags or holds progression, then prepares targeted missing-data requests.
4. A case that clearly belongs to a particular team is routed with a one-line reason and visible rule trace.
5. The assistant prepares a handoff summary; a reviewer edits and approves it; the edited version is retained and used.
6. A reviewer rejects a prepared output; nothing final is sent; the case returns to the correct stage with rationale captured.
7. A duplicate submission is detected and flagged as probable duplicate instead of being reprocessed.
8. Tests/medications-related administrative artifacts are appended to the case record with timestamp and source context.
9. Policy-eligible approvals are opened in parallel across insurance/operations/diagnostics/legal/finance, and blocking approvals are clearly identified.
10. A critical-condition signal appears in test/diagnostic inputs; the assistant auto-prepares escalation details and routes to designated clinical authority without making a clinical decision.
11. Clinical clearance is completed by authorized humans, then finance clearance is completed, and only then is the case eligible for release routing.
12. A team lead opens status and sees stage, owner, elapsed time, approvals, blockers, and provisional flags.
13. A user asks for autonomous diagnosis, treatment, medical necessity, clinical clearance, or discharge authorization; the assistant declines and directs to qualified humans.
14. A compliance reviewer reconstructs end-to-end case history: arrivals, extracted/backfilled data, rules fired, approvals, edits, escalations, and timestamps.

---

NON-NEGOTIABLE CONSTRAINTS

- Only synthetic or de-identified sample data is ever used. No real patient information at any point.
- The assistant assists; humans decide. Every outbound or final action requires explicit recorded human approval.
- The assistant does not perform autonomous diagnosis, treatment recommendation, medical-necessity determination, clinical clearance authorization, or discharge/release authorization.
- Personal identifiers are masked in logs and audit records.
- The routing logic must be inspectable and explainable to a non-technical reviewer. A decision the reviewer cannot understand is not acceptable.
- The assistant's accuracy and speed must be re-measurable on demand against a fixed set of sample documents, producing a repeatable result.
- docs/constitution.md is authoritative and non-overridable by execution agents or automation.
- Every implementation change must be logged in docs/progress-log.md.

EXPLICITLY OUT OF SCOPE

- Connecting to any live electronic health record or production clinical system.
- Submitting anything to a real insurer, payer, or external body.
- Making prior authorisation or coverage determinations of any kind.
- Any autonomous clinical or diagnostic judgement.
- Multi-organisation tenancy, single sign-on, and production hosting concerns.
- Any claim of financial savings or headcount reduction.

SUCCESS CRITERIA

Lower cycle time
- Processing an item through the assistant takes measurably less elapsed time than doing the identical work by hand on the same document.
- The number of avoidable serial handoffs is reduced by parallelizing eligible approvals and tasking.
- A prepared route plan is ready within a short time of case arrival.

Fewer errors
- Key details are extracted correctly from the large majority of sample documents.
- Every deliberately introduced omission in a test document is detected.
- Items are assigned to the expected team in nine out of ten sample cases.
- The large majority of items reach progression with complete details or correctly flagged provisional routing without unsafe advancement.
- No item is ever sent or finalised without a recorded human approval.

Operational reliability
- Approval SLA compliance improves through role-based parallel approvals.
- Critical-condition escalations are routed to clinical authority with complete escalation packets.
- Audit reconstruction completeness remains 100% for sampled completed cases.

Flag any requirement above that is ambiguous or that needs a decision before implementation, rather than assuming an answer.
```

---

## 2. Hold these back for `/plan`, not `/specify`

Do **not** put these in the prompt above. They are HOW, and naming them during `/specify` turns the spec into a design document:

- Microsoft Agent Framework (MAF), agents vs. workflows, executors, checkpointing
- Copilot SDK, chat surface implementation
- PDF / OCR / document parsing libraries
- FHIR, HL7, X12 data shapes
- Rules engine or config format choices
- OpenTelemetry / tracing implementation
- Language, runtime, and storage choices

---

## 3. Pre-agreed answers to likely clarification questions

The specify agent will probably ask these. Answer from here rather than improvising:

| Likely question | Our answer |
|---|---|
| Which administrative workflow? | Full patient administrative journey orchestration from arrival to release routing, with strict clinical human lockpoints. |
| What are the "key details" to extract? | Requester, patient reference (synthetic), requested service, urgency, payer/plan, supporting notes, date. |
| What document formats arrive? | Text-layer documents generally. The current sample set uses Markdown as a stand-in for the inbound email and fax-cover shapes, so the extraction path can be built and graded without a parsing dependency. Real text-layer PDF and raw email follow once the clean path works. Scanned/OCR documents are a later addition, not a day-one requirement. |
| Which teams can an item be routed to? | A fixed set of five, matching the F11 approver roles: **Insurance, Operations, Diagnostics, Legal, Finance.** Not dynamic, not customer-configurable during the hackathon. See [`../data/README.md`](../data/README.md). |
| What makes a routing decision "correct"? | Graded against a fixed answer key in the sample set. |
| How is a duplicate defined? | Same sender and same patient reference and same requested service within a short window. Keep it simple and explainable. |
| What does "measurably faster" mean? | A stopwatched manual walkthrough of the same document, compared against the assistant path. |
| Who approves? | Role-based approvers (insurance, operations, diagnostics, legal, finance) with parallel approvals where policy allows, plus human clinical and financial clearance gates before release. |
| What happens after approval? | The case progresses stage-by-stage; release routing occurs only after mandatory human clearances are complete. |
| What if required data is missing? | Backfill from records first; then provisional routing by confidence threshold if policy allows; unresolved fields route to expert/admin completion tasks. |

---

## 4. After `/specify`

1. Check the generated spec against [`../feature.md`](../feature.md) — every feature ID **F1–F24** should map to at least one requirement.
2. Resolve every `[NEEDS CLARIFICATION]` using §3 above.
3. Confirm the spec still contains no technology choices. If it does, strip them.
4. Verify all generated requirements comply with [`docs/constitution.md`](../docs/constitution.md) before any planning or implementation.
5. Update [`docs/progress-log.md`](../docs/progress-log.md) with any requirement or scope changes produced by `/specify`.
6. Validate coverage and acceptance against [`docs/multipass-validation-harness.md`](../docs/multipass-validation-harness.md) and record results.
7. Then run `/plan` and introduce implementation choices.

---

## 5. Feature coverage checklist

Use this to verify the generated spec is complete:

| Feature | Covered by prompt section |
|---|---|
| F1 Register arriving case | "Intake and understanding" · Scenario 1 |
| F2 Extract case details | "Intake and understanding" · Scenario 1 |
| F3 Backfill from records | "Intake and understanding" · Scenario 2 |
| F4 Completeness and plausibility checks | "Checking" · Scenario 2 |
| F5 Missing-data tasking | "Checking" · Scenario 2 |
| F6 Provisional routing policy | "Checking" · Scenario 3 |
| F7 Explainable routing | "Progressing" · Scenario 4 |
| F8 Duplicate detection | "Checking" · Scenario 7 |
| F9 Handoff summary drafting | "Progressing" · Scenario 5 |
| F10 Case record updates | "Progressing" · Scenario 8 |
| F11 Parallel approval orchestration | "Progressing" · Scenario 9 |
| F12 Human approval actions | "Human control" · Scenario 6 |
| F13 Critical escalation packet | "Progressing" · Scenario 10 |
| F14 Status board and blockers | "Visibility" · Scenario 12 |
| F15 SLA timers and alerts | "Visibility" · Success criteria |
| F16 Clinical clearance gate | "Human control" · Scenario 11 |
| F17 Financial clearance gate | "Human control" · Scenario 11 |
| F18 Release routing gate | "Human control" · Scenario 11 |
| F19 Stage-aware safety boundary | Constraints · Scenario 13 |
| F20 Audit and replay trail | Constraints · Scenario 14 |
| F21 Eval harness | Constraints — "re-measurable on demand" |
| F22 Chat surface | Personas + interaction flow |
| F23 Policy version control | Constraints + audit traceability |
| F24 Governance enforcement | Constraints + §4 steps 4-5 |
