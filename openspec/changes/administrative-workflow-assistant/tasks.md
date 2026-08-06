> **This task list is NOT executed as part of this change.**
>
> This change delivers **specification artifacts only** — proposal, delta specs, design and this
> breakdown. No application code, schema, service, prompt or configuration is written here, and
> `openspec apply` must not be run against this change until the specification has been reviewed
> and approved by a human.
>
> The nine questions raised during authoring are now answered and recorded as Resolved Decisions in
> `design.md`. Group 1 no longer gates on decisions; it carries the two concrete artifacts those
> decisions created — the prior-records fixture and the clinician-approved criticality marker list —
> plus the role and wording follow-ups. Groups 2 onward still must not begin until group 1 is
> complete, because the fixture and the marker list are inputs to behaviour, not consequences of it.

## 1. Prerequisites carried from the resolved decisions

- [ ] 1.1 Author the prior-records fixture that backfill reads from when a patient reference has no earlier processed case, covering at minimum the values CASE-002, CASE-011 and CASE-017 cite (Resolved Decision 1)
- [ ] 1.2 Obtain a clinician-approved criticality marker list of declared markers, and version it alongside the routing and approval policy (Resolved Decision 2, safety-bearing)
- [ ] 1.3 Name the deputy or on-call holder of the Clinical Authority role so the **P4** critical acknowledgement target stays achievable when the primary holder is unavailable (Resolved Decision 5)
- [ ] 1.4 Replace the relative "approval SLA compliance improves" wording in `feature.md` §7 with the absolute criterion recorded in Resolved Decision 7
- [ ] 1.5 Record the P8 retention gap statement as a standing caveat wherever retention is documented or demonstrated (Resolved Decision 6)
- [ ] 1.6 Obtain human approval of this specification and record the approval in `docs/progress-log.md`

## 2. Architecture and foundations

- [ ] 2.1 Author a separate architecture change selecting stack, storage and execution model, since the delta specs are deliberately implementation-neutral
- [ ] 2.2 Define the canonical structured case record covering every field the delta specs reference
- [ ] 2.3 Define the append-only event lineage model that `audit-and-compliance-trail` requires, including event types for arrivals, extractions, backfills, rule evaluations, approvals, edits, escalations, clearances and refusals
- [ ] 2.4 Define the policy version object carrying P1–P9 so thresholds are referenced by identifier and never hardcoded
- [ ] 2.5 Implement identifier masking at write time so no unmasked identifier is ever persisted, while preserving case correlation
- [ ] 2.6 Establish the synthetic-data-only guard that prevents ingestion of any non-synthetic source

## 3. Safety-bearing capabilities (build and verify before any outbound path exists)

- [ ] 3.1 Implement `safety-boundary` refusal for diagnosis, treatment recommendation, medical-necessity determination, clinical clearance authorization and discharge or release authorization
- [ ] 3.2 Implement refusal redirection naming the qualified human role for each prohibited request category
- [ ] 3.3 Implement boundary consistency under rephrasing, task embedding, repetition and privileged roles
- [ ] 3.4 Implement non-overridability so no configuration, flag, prompt or agent instruction can relax the boundary, and override attempts are recorded
- [ ] 3.5 Implement the permitted-action allowlist so collation, administrative routing, drafting and escalation preparation are not over-refused
- [ ] 3.6 Verify every `safety-boundary` scenario against the delta spec before proceeding to group 4

## 4. Human approval control

- [ ] 4.1 Implement the recorded-approval requirement so no final or outbound action can occur without an explicit human approval
- [ ] 4.2 Implement handoff summary preparation for human review
- [ ] 4.3 Implement edit capture so the human-edited version is retained and used downstream, superseding the prepared draft
- [ ] 4.4 Implement rejection handling that halts finality, returns the case to the correct stage, and captures the rejecting human, role and rationale
- [ ] 4.5 Implement the P6 rework-loop limit with escalation when exceeded
- [ ] 4.6 Enforce the `docs/multipass-validation-harness.md` §4.1 rule that the agent may never occupy an approver role

## 5. Intake and extraction

- [ ] 5.1 Implement request registration from every supported channel with arrival time and source recorded
- [ ] 5.2 Implement key-detail extraction into the structured record with per-field source reference and confidence
- [ ] 5.3 Implement backfill from the prior-records fixture defined in task 1.2, with provenance recorded per backfilled value
- [ ] 5.4 Verify intake and extraction against acceptance scenarios 1 and 2 using `SYN-CASESET-v1`

## 6. Data quality and duplicates

- [ ] 6.1 Implement completeness checking that lists unresolved required fields explicitly rather than reporting a generic failure
- [ ] 6.2 Implement plausibility and contradiction detection, covering the seeded field-contradiction case
- [ ] 6.3 Implement routing of unresolved data to the correct expert or admin completion task
- [ ] 6.4 Implement targeted missing-data request preparation naming only the fields actually outstanding
- [ ] 6.5 Implement P2 duplicate detection over the defined window, flagging probable duplicates instead of reprocessing
- [ ] 6.6 Implement near-duplicate handling per the decision from task 1.10
- [ ] 6.7 Verify against acceptance scenarios 2, 3 and 7, including the not-applicable false-positive traps

## 7. Explainable routing

- [ ] 7.1 Implement the fixed five-queue routing decision over Insurance, Operations, Diagnostics, Legal and Finance
- [ ] 7.2 Implement the inspectable rule trace recording every rule evaluated, its outcome, and the policy version applied
- [ ] 7.3 Implement the one-line plain-language reason readable by a non-technical reviewer
- [ ] 7.4 Implement P1 confidence-threshold provisional routing, including the prohibition while a critical signal is active or a clearance is pending
- [ ] 7.5 Implement the provisional flag surfacing unresolved fields and blocking release eligibility
- [ ] 7.6 Implement F23 policy versioning so a threshold change produces a new version recorded on every affected decision
- [ ] 7.7 Verify against acceptance scenarios 3 and 4, including both misroute traps

## 8. Approval orchestration and record appends

- [ ] 8.1 Implement parallel opening of policy-eligible approvals across insurance, operations, diagnostics, legal and finance
- [ ] 8.2 Implement blocking versus non-blocking approval classification with a visible count of outstanding blockers
- [ ] 8.3 Implement explicit approval dependency declaration where policy requires sequencing
- [ ] 8.4 Implement additive artifact appends for tests and medications with append timestamp and source context, never overwriting
- [ ] 8.5 Implement P4 service-level tracking and P5 early-warning alerting, with breaches recorded and surfaced as blockers
- [ ] 8.6 Ensure elapsed service-level targets never advance approval state automatically
- [ ] 8.7 Verify against acceptance scenarios 8 and 9

## 9. Clinical escalation

- [ ] 9.1 Implement critical-condition signal detection using the taxonomy from task 1.3
- [ ] 9.2 Implement automatic escalation packet preparation meeting P3 mandatory-field completeness with no partial sends
- [ ] 9.3 Implement routing to the designated clinical authority using the table from task 1.6
- [ ] 9.4 Ensure escalation preparation and routing make no clinical determination of any kind
- [ ] 9.5 Implement the P4 critical acknowledgement target and its escalation on breach
- [ ] 9.6 Verify against acceptance scenario 10 using the seeded critical-condition case

## 10. Clearance and release gates

- [ ] 10.1 Implement the mandatory human clinical clearance gate, refusing any automated grant, inference or pre-population
- [ ] 10.2 Ensure absence of a critical signal is never treated as clinical clearance
- [ ] 10.3 Implement the financial clearance gate opening only after clinical clearance is recorded, per the decision from task 1.5
- [ ] 10.4 Implement separation of duty preventing one person from holding both gates on the same case
- [ ] 10.5 Implement the release routing gate checking all clearances, blocking approvals, unresolved data, provisional flags and duplicate flags
- [ ] 10.6 Ensure blocked release names every unsatisfied prerequisite individually with no bypass or override path
- [ ] 10.7 Verify against acceptance scenario 11 using both seeded clearance-gate cases

## 11. Visibility and conversational surface

- [ ] 11.1 Implement the status view showing stage, owner, total elapsed time and time in current stage for every in-flight item
- [ ] 11.2 Implement unassigned-owner visibility so unowned items still appear and accrue elapsed time
- [ ] 11.3 Implement approval status, blocker, provisional flag and unresolved task display, distinguishing blocking from non-blocking
- [ ] 11.4 Implement total elapsed time reporting for completed items against the `feature.md` §13.3 endpoint
- [ ] 11.5 Implement the P9 conversational surface for submission, status enquiry, approval and escalation
- [ ] 11.6 Ensure conversational actions carry identical authorization, approval and audit requirements to every other surface
- [ ] 11.7 Verify against acceptance scenario 12

## 12. Audit, compliance and governance

- [ ] 12.1 Implement replay-grade lineage capture across every event type defined in task 2.3
- [ ] 12.2 Implement append-only semantics so corrections append and superseded events remain retrievable
- [ ] 12.3 Implement end-to-end case reconstruction requiring no external system
- [ ] 12.4 Implement P8 retention with no purge before review sign-off, and document the production retention gap explicitly
- [ ] 12.5 Implement the constitution override refusal path that stops work and escalates to Team Lead and Compliance Reviewer
- [ ] 12.6 Implement the drift check reporting divergence between `openspec/constitution.md` and the authoritative `docs/constitution.md`
- [ ] 12.7 Implement the mandatory `docs/progress-log.md` completion check
- [ ] 12.8 Verify against acceptance scenario 14 by reconstructing a completed case end to end

## 13. Evaluation harness

- [ ] 13.1 Implement on-demand grading against `SYN-CASESET-v1` and its answer key with no manual setup required
- [ ] 13.2 Implement per-check and overall reporting for extraction, routing, completeness, duplicates, escalation completeness and clearance-gate enforcement
- [ ] 13.3 Implement separate reporting for each seeded trap category, naming failing cases individually
- [ ] 13.4 Implement dataset, policy and build version stamping on every result
- [ ] 13.5 Implement the P7 drift check requiring identical per-case classifications across repeated runs, reporting diverging cases on failure
- [ ] 13.6 Implement the `feature.md` §13.3 manual-baseline speed comparison with range reporting, and mark off-protocol figures non-comparable
- [ ] 13.7 Implement per-metric reporting against the `feature.md` §7 targets, reporting shortfalls rather than omitting missed metrics

## 14. Acceptance and sign-off

- [ ] 14.1 Verify all fourteen acceptance scenarios end to end against `SYN-CASESET-v1`
- [ ] 14.2 Confirm the `feature.md` §7 targets are met, or record each shortfall with its gap
- [ ] 14.3 Run the drift check across repeated runs and confirm results fall within P7
- [ ] 14.4 Complete a compliance review against every constitution section
- [ ] 14.5 Record the implementation in `docs/progress-log.md` with impacted files, summary and validation evidence
