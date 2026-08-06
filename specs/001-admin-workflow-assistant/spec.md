# Feature Specification: Administrative Workflow Assistant

**Feature Branch**: `001-admin-workflow-assistant`
**Created**: 2026-08-06
**Status**: Clarified — ready for spec review (not yet planned)
**Input**: User description: "Build an Administrative Workflow Assistant for a healthcare provider organisation" — administrative patient journey orchestration from arrival to release routing, with human-in-the-loop approvals, explainable routing, parallel role-based approvals, critical-condition escalation packets, clinical and financial clearance gates, and full audit reconstruction.

## Overview

Administrative work in a clinic or hospital is slow for three compounding reasons: it is **repetitive** (a request arrives as an unstructured document and a coordinator re-types the same handful of details, every time), it is **full of handoffs** (intake desk, completeness check, chase-the-sender loop, routing decision, drafting step, supervisor approval — each a different person and a different queue), and it is **full of delay** (most elapsed time on any item is spent waiting between steps, not being worked on).

The errors follow from the same causes: items advance with details missing, get sent to the wrong team, get re-keyed with mistakes, or get worked twice because nobody noticed the request had already arrived.

This feature reduces the **elapsed time** to process an administrative request and reduces the **number of mistakes** made while processing it, by having software do the reading, the typing, the checking and the routing — **while a human keeps every decision**.

The assistant assists; humans decide. It never performs autonomous diagnosis, treatment recommendation, medical-necessity determination, clinical clearance authorization, or discharge/release authorization.

**Governance**: `docs/constitution.md` is authoritative and non-overridable by execution agents or automation. Every implementation change must be logged in `docs/progress-log.md`.

## Clarifications

### Session 2026-08-06

- Q: What confidence threshold and preconditions permit provisional routing before required data is complete? → A: Routing confidence **≥ 0.80** *and* both `patient_reference` and `requested_service` present; never permitted while a critical-condition signal is active or a clearance gate is pending. Adopted from the project's already-approved policy **P1**; it is safety-bearing and may only be loosened with Compliance Reviewer approval.
- Q: What quantifies the "large majority" targets for extraction accuracy and first-pass completeness? → A: Field extraction accuracy **≥ 85%** of graded fields; first-pass completeness **≥ 90%** of items; routing accuracy **≥ 9 of 10** graded cases; seeded-omission detection **100%**; unapproved sends **exactly 0**. Adopted from the project's approved success metrics.
- Q: What are the approval SLA targets and when does the system warn? → A: Routine **2 business days**, urgent **4 hours**, critical-escalation acknowledgement **30 minutes**; early-warning alert at **80% of SLA elapsed**, breach recorded at **100%**. Adopted from approved policy **P4**/**P5**.
- Q: What defines a duplicate submission, over what window, and what happens on match? → A: Match on **sender + patient reference + requested service** within **72 hours** of first receipt, independent of arrival channel. On match the item is **flagged as a probable duplicate and held for human adjudication** — never auto-discarded and never auto-merged. Adopted from approved policy **P2**, with flag-not-discard chosen as the conservative behavior.
- Q: What completeness is required before an escalation packet may be routed to clinical authority, and what happens if it cannot be met? → A: **100% of mandatory packet fields**, with **no partial sends**. Mandatory fields: case ID, patient reference, requester, critical-signal description, source document reference, timestamp, designated clinical recipient. If a mandatory **content** field is missing the packet is **held**, a blocker is raised to both the designated Clinical Authority and the Intake Coordinator, and the critical signal remains visibly active until the packet is complete and routed. Absence of a required **designation** — the clinical recipient, the Escalation Dispatch Approver, or an approved dispatch-approval deadline — is instead handled as a *governance* blocker under the precedence rule in FR-054, since it is a gap in the approver registry or policy table rather than a gap in the packet's content. Adopted from approved policy **P3**; safety-bearing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Intake, structured capture, and data quality (Priority: P1)

An administrative request for a patient arrives as an unstructured document. Instead of a coordinator re-typing the same details, the assistant registers the arrival as a tracked work item, reads the document into a structured case record, backfills what it can from records already available, names anything still missing or implausible, raises completion tasks to the right owner, and recognises when the same request has already arrived.

**Why this priority**: Nothing downstream can be trusted if the case record is wrong, incomplete, or duplicated. This is the slice that removes the re-typing and stops bad data advancing.

**Independent Test**: Submit sample case documents (complete, incomplete, and duplicate) and verify the registered item, extracted record, backfill provenance, explicit missing-field list, generated completion tasks, and duplicate flag — without any routing or approval behavior present.

**Acceptance Scenarios**:

1. **Given** a complete incoming request, **When** it is submitted, **Then** the assistant registers it as a tracked work item with a case identifier and time of arrival, and extracts its key details accurately into a structured case record. *(AS-1)*
2. **Given** a case with required details missing, **When** it is submitted, **Then** the assistant first backfills what can be reliably inferred from available records (tagging each backfilled value with its source), explicitly lists the fields it could not resolve, and creates completion tasks assigned to the correct expert/admin owner. *(AS-2)*
3. **Given** required data remains unresolved after backfill, **When** the assistant evaluates progression, **Then** it applies the confidence-threshold policy and either sets provisional routing with visible provisional flags or holds progression, and in both cases prepares targeted requests for exactly the missing information. *(AS-3)*
4. **Given** a request matching one already in progress on sender, patient reference and requested service within the duplicate window, **When** it is submitted, **Then** it is flagged as a probable duplicate and held for human adjudication instead of being reprocessed. *(AS-7)*
5. **Given** a case record containing a contradictory or implausible value, **When** completeness checking runs, **Then** the conflict is named explicitly and the case is not allowed to advance on that value alone.

---

### User Story 2 - Explainable routing (Priority: P1)

A coordinator or team lead needs to know not just where a case went, but why. The assistant determines the receiving team using inspectable rules and states the reason in one line that a non-technical reviewer can read.

**Why this priority**: Routing is where the misroute errors happen, and an unexplainable routing decision is not acceptable under the project's governance constraints.

**Independent Test**: Submit sample cases with known correct queues and verify each is routed to the expected team with a one-line reason and a visible trace of which rules fired.

**Acceptance Scenarios**:

1. **Given** a case that clearly belongs to a particular team, **When** routing runs, **Then** the case is routed to that team with a one-line reason and a visible rule trace showing which rules were evaluated and which fired. *(AS-4)*
2. **Given** any routing decision, **When** a non-technical reviewer inspects it, **Then** the reviewer can identify the rule that produced it and the policy version in force at that time, without needing technical assistance.

---

### User Story 3 - Human control over every output (Priority: P1)

Every draft and every route proposal is presented to an authorized human, who may approve, edit, reject, or return it for rework. Nothing is sent, submitted, escalated clinically, cleared, or routed for release without a recorded human approval. Human edits become the authoritative version.

**Why this priority**: This is the constraint that makes the system safe to operate at all. Without it there is no product, only a script.

**Independent Test**: Present a prepared handoff summary to a reviewer; verify edit-and-approve retains the edited text as authoritative, and verify reject returns the case to the correct prior stage with rationale and sends nothing.

**Acceptance Scenarios**:

1. **Given** the assistant has prepared a handoff summary, **When** a reviewer edits it and approves, **Then** the edited version is retained as the authoritative version and is the version used downstream. *(AS-5)*
2. **Given** the assistant has prepared an output, **When** a reviewer rejects it, **Then** nothing final is sent, the case returns to the correct prior stage, and the rejection rationale is captured against the case. *(AS-6)*
3. **Given** any outbound, escalation, clearance, or release-routing action, **When** no explicit human approval is recorded, **Then** the action does not occur.
4. **Given** a case has been returned for rework twice, **When** a third rework loop would begin, **Then** the case is escalated to a human owner instead of looping again.

---

### User Story 4 - Case record updates and parallel role-based approvals (Priority: P2)

Administrative artifacts related to prescribed tests or medications are appended to the case record as they become available. Approvals across insurance, operations, diagnostics, legal and finance are opened in parallel where policy allows, rather than queueing behind one another, and whichever approvals are blocking progression are clearly identified.

**Why this priority**: This is the main cycle-time win — it removes avoidable serial handoffs — but it depends on a trustworthy case record and explainable routing existing first.

**Independent Test**: Attach test/medication artifacts to a case and verify timestamp and source context are recorded; open a policy-eligible case and verify the five role approvals appear concurrently with blocking approvals distinguished from non-blocking ones.

**Acceptance Scenarios**:

1. **Given** administrative artifacts related to prescribed tests or medications become available, **When** they are added, **Then** they are appended to the case record with a timestamp and source context, and remain traceable to their origin. *(AS-8)*
2. **Given** a case whose policy permits parallel approvals, **When** approvals are opened, **Then** insurance, operations, diagnostics, legal and finance approvals are opened concurrently and the approvals that block progression are clearly identified as blocking. *(AS-9)*
3. **Given** an approval has been open beyond its early-warning point, **When** the status is viewed, **Then** the approaching or breached SLA is visible and attributable to an owner.

---

### User Story 5 - Critical-condition escalation to clinical authority (Priority: P1)

When a critical-condition signal appears in test or diagnostic inputs, the assistant assembles a complete escalation packet and, on recorded human dispatch approval, routes it to the designated clinical authority — without making any clinical decision itself.

**Why this priority**: A missed or incomplete critical escalation is the highest-severity failure mode in the whole workflow.

**Independent Test**: Submit a case containing a seeded critical-condition signal and verify a complete escalation packet is prepared within the draft-readiness bound, raised as a non-suppressible dispatch approval, routed to the designated clinical recipient once that approval is recorded, that no clinical interpretation is asserted, that a rejected dispatch stays undispatched, and that an incomplete packet is held rather than partially sent.

**Acceptance Scenarios**:

1. **Given** a critical-condition signal appears in test or diagnostic inputs, **When** the assistant detects it, **Then** it prepares the escalation packet within the draft-readiness bound and, once the clinical recipient, the Escalation Dispatch Approver and an approved dispatch-approval deadline are all designated and the packet is complete, raises it as a non-suppressible dispatch approval, and on approval routes it to the designated clinical authority, stating the observed signal and its source without making, implying, or ranking any clinical judgement. *(AS-10)*
2. **Given** all three required designations are present but the escalation packet is missing a mandatory content field, **When** routing is attempted, **Then** the packet is held, a completeness blocker is raised to the designated Clinical Authority and the Intake Coordinator, and no partial packet is sent.
3. **Given** a critical signal is active on a case, **When** provisional routing is evaluated, **Then** provisional routing is not permitted for that case.
4. **Given** a dispatch approval is rejected, **When** the rejection is recorded, **Then** the packet remains undispatched, the rationale is recorded, and the critical signal stays visibly active.
5. **Given** no Escalation Dispatch Approver has been designated, **When** a packet becomes ready for dispatch, **Then** it is held and a governance blocker is raised rather than being dispatched or routed via a substitute role.
6. **Given** no designated clinical recipient is configured, **When** the packet is evaluated, **Then** a governance blocker is raised rather than a completeness blocker, even though the clinical recipient is also a mandatory packet field.

---

### User Story 6 - Clearance gates and release routing (Priority: P1)

Clinical clearance and financial clearance are mandatory human gates. A case becomes eligible for release routing only after both are recorded by authorized humans and all other required gates are complete.

**Why this priority**: Release routing is the terminal action of the journey and the point at which an unsafe advance would have real consequence.

**Independent Test**: Drive a case to the clearance stage and verify release routing is refused until clinical clearance is recorded, then still refused until financial clearance is recorded, then permitted.

**Acceptance Scenarios**:

1. **Given** a case awaiting release, **When** clinical clearance is completed by an authorized human and then financial clearance is completed by an authorized human, **Then** and only then does the case become eligible for release routing. *(AS-11)*
2. **Given** a case with either clearance missing, **When** release routing is attempted, **Then** it is refused and the missing gate is named as the blocker.
3. **Given** a single person holds both clinical and financial clearance authority, **When** they attempt to record both clearances on the same case, **Then** the second clearance is refused on separation-of-duty grounds.

---

### User Story 7 - Work-in-flight visibility (Priority: P2)

A team lead can see, for every item in progress, which stage it is in, who owns it, and how long it has been sitting — plus all approval statuses, blockers, provisional flags and unresolved data tasks. Total elapsed time for a completed item is visible so it can be compared against doing the same work by hand.

**Why this priority**: This is how the cycle-time claim is observed and how stalled work is found, but the workflow can function without it.

**Independent Test**: Open the status view with several cases in different stages and verify stage, owner, elapsed time, approvals, blockers and provisional flags are all present and current.

**Acceptance Scenarios**:

1. **Given** several cases are in flight, **When** a team lead opens the status view, **Then** they see for each case its stage, owner, elapsed time, approval statuses, blockers, and provisional routing flags. *(AS-12)*
2. **Given** a completed case, **When** its record is viewed, **Then** total elapsed time from arrival to completion is visible for comparison against the manual baseline.
3. **Given** unresolved data completion tasks exist on a case, **When** the status view is opened, **Then** those tasks are visible as blockers with their assigned owners.

---

### User Story 8 - Safety boundary enforcement (Priority: P1)

When asked to perform a clinical act — diagnose, recommend treatment, determine medical necessity, authorize clinical clearance, or authorize discharge/release — the assistant declines and directs the requester to qualified humans.

**Why this priority**: This boundary is a non-negotiable constraint of the project's constitution and applies at every stage.

**Independent Test**: Issue each of the five prohibited request types at several different workflow stages and verify a consistent refusal plus direction to the appropriate human authority.

**Acceptance Scenarios**:

1. **Given** a user asks for autonomous diagnosis, treatment recommendation, medical-necessity determination, clinical clearance, or discharge/release authorization, **When** the request is made at any stage, **Then** the assistant declines, states that the decision belongs to a qualified human, and directs the request to the appropriate human authority. *(AS-13)*
2. **Given** a refusal occurs, **When** the case history is inspected, **Then** the refused request and the refusal are recorded in the case record.

---

### User Story 9 - Audit reconstruction (Priority: P2)

A compliance reviewer can reconstruct exactly what happened to any single item and why — arrivals, extracted and backfilled data, rules fired, approvals, edits, escalations, refusals, and timestamps — with personal identifiers masked.

**Why this priority**: Required for compliance sign-off, but it observes the workflow rather than driving it.

**Independent Test**: Take a completed sample case and reconstruct its full history end to end from the audit record alone, confirming no step is unaccounted for and no personal identifier appears unmasked.

**Acceptance Scenarios**:

1. **Given** a completed case, **When** a compliance reviewer requests its history, **Then** they can reconstruct end to end: arrival, extracted data, backfilled values and their sources, rules fired, approvals and approvers, human edits, escalations, refusals, and timestamps for each. *(AS-14)*
2. **Given** any audit or log record, **When** it is read, **Then** personal identifiers are masked.
3. **Given** a routing or approval decision in the history, **When** it is inspected, **Then** the policy version in force at the time of that decision is identifiable.

### Edge Cases

- **Backfill produces a value that contradicts the submitted document.** The contradiction is named explicitly, the submitted value is not silently overwritten, and the case does not advance on the disputed field alone.
- **A near-duplicate that is genuinely a different request.** The duplicate check must not flag it; the match key is sender + patient reference + requested service, so a different requested service is a different case.
- **A duplicate arrives on a different channel** (e.g. a fax resend of an emailed request). Channel is not part of the match key, so it is still flagged.
- **A required field is legitimately "Not applicable".** This must not be treated as a missing field and must not generate a completion task.
- **New data arrives after provisional routing was set.** The provisional decision is re-evaluated; if the new data invalidates it, the case is re-routed and the change is recorded with rationale.
- **An escalation packet cannot be completed.** The packet is held, never partially sent, and a blocker is raised to Clinical Authority and Intake Coordinator; the critical signal stays visibly active.
- **A critical signal appears on a case already provisionally routed.** Provisional status is revoked and progression holds pending escalation handling.
- **An approver rejects after other parallel approvals have already been granted.** The case returns to the correct prior stage; already-granted approvals are recorded but do not by themselves permit advancement.
- **A case exceeds the rework-loop limit.** After two rework loops the case is escalated to a human owner rather than looping a third time.
- **An approval SLA is breached.** The breach is recorded and made visible; it does not auto-approve, auto-advance, or auto-escalate clinically.
- **A reviewer edits a draft and then rejects it.** The edited text is retained as the authoritative draft; the rejection routes the case back with rationale.
- **An arriving document is unreadable or contains no extractable detail.** The item is still registered with an arrival timestamp and raised as a blocker; it is never silently dropped.
- **No designated clinical recipient is configured** when an escalation is required. Escalation is held and raised as a governance blocker rather than routed to a default or non-clinical recipient.
- **No Escalation Dispatch Approver is designated** when a packet becomes ready. The packet is held under a governance blocker; dispatch is never delegated to a substitute role and never performed by the assistant.
- **A dispatch approval is rejected.** The packet stays undispatched, the rationale is recorded, and the critical signal remains visibly active.
- **The dispatch-approval deadline elapses.** The breach is recorded and made visible; the packet is not dispatched without an approval.

## Requirements *(mandatory)*

### Functional Requirements

**Intake and understanding**

- **FR-001**: System MUST register each arriving patient case as a tracked work item with a unique case identifier and a recorded time of arrival.
- **FR-002**: System MUST produce a structured case record of the key details required for safe administrative progression, in which every extracted value faithfully reflects the submitted source document. System MUST NOT invent, guess at, or substitute a value, and MUST mark a value as unreadable rather than recording it whenever the source text for that value is absent, illegible, or admits more than one distinct reading.
- **FR-003**: System MUST backfill every missing required detail that is reliably derivable from available records before requesting new input from a human, and MUST NOT infer a value that is not so derivable.
- **FR-004**: System MUST tag every backfilled value with the source it was derived from, so it is distinguishable from a value present in the submitted document.
- **FR-005**: System MUST register an arriving item even when its content is unreadable or non-extractable, and raise it as a blocker rather than discarding it.

**Checking**

- **FR-006**: System MUST check the case record for completeness and plausibility and explicitly name every value that is missing, contradictory, or implausible, before the item is allowed to advance.
- **FR-007**: System MUST NOT allow an item to advance on a value that has been flagged as missing, contradictory, or implausible, and MUST hold progression whenever the provisional-routing eligibility conditions in FR-010 and FR-011 are not met.
- **FR-008**: System MUST create completion tasks for every mandatory field still unresolved after backfill, assigning each task to the single accountable owner given by an inspectable field-to-role mapping drawn from the approver role registry, and MUST assign the task to the Intake Coordinator where no mapping exists for that field.
- **FR-009**: System MUST distinguish a legitimate "not applicable" value from a missing value and MUST NOT raise a completion task for the former.
- **FR-010**: System MUST permit provisional routing only when routing confidence is at least 0.80 and both patient reference and requested service are present.
- **FR-011**: System MUST NOT permit provisional routing while a critical-condition signal is active on the case or while a clearance gate is pending.
- **FR-012**: System MUST mark every provisionally routed case with a visible provisional flag that names what remains outstanding.
- **FR-013**: System MUST re-evaluate a provisional routing decision when new data arrives, and MUST record the rationale if the decision changes.
- **FR-014**: System MUST flag an arriving request as a probable duplicate when it matches an in-progress case on sender, patient reference and requested service within 72 hours of the first receipt, independent of arrival channel.
- **FR-015**: System MUST hold a flagged duplicate for human adjudication and MUST NOT auto-discard, auto-merge, or reprocess it.

**Progressing**

- **FR-016**: System MUST prepare targeted requests for exactly the missing information when required details are unresolved, and MUST NOT request information it already holds.
- **FR-017**: System MUST determine routing using inspectable, declarative rules and MUST state the reason for each routing decision in one line understandable to a non-technical reviewer.
- **FR-018**: System MUST expose, for each routing decision, a trace of the rules evaluated and the rules that fired.
- **FR-019**: System MUST append administrative artifacts related to prescribed tests or medications to the case record with a timestamp and source context.
- **FR-020**: System MUST open role-based approvals for insurance, operations, diagnostics, legal and finance in parallel where policy allows, rather than in sequence.
- **FR-021**: System MUST identify which open approvals are blocking progression and which are not.
- **FR-022**: System MUST track approval SLAs of 2 business days for routine items, 4 hours for urgent items, and 30 minutes for acknowledgement of a critical escalation.
- **FR-023**: System MUST raise an early-warning alert at 80% of elapsed SLA and record a breach at 100%, and MUST NOT auto-approve or auto-advance an item on SLA breach.
- **FR-024**: System MUST prepare an escalation packet within 30 seconds of detecting a critical-condition signal in test or diagnostic inputs, consistent with the draft-readiness bound in SC-003, and MUST present that packet for dispatch approval only once the outcome-precedence rule in FR-054 selects the approval outcome — that is, once the clinical recipient, the Escalation Dispatch Approver, and an approved dispatch-approval deadline are all designated *and* the packet satisfies the completeness requirement in FR-025. System MUST NOT dispatch it to the designated clinical authority without the recorded human approval required by FR-030 and FR-051.
- **FR-025**: System MUST include 100% of the mandatory escalation packet fields — case ID, patient reference, requester, critical-signal description, source document reference, timestamp, and designated clinical recipient — and MUST NOT send a partial packet.
- **FR-026**: System MUST hold an escalation packet that is missing a mandatory **content** field and raise a completeness blocker to the designated Clinical Authority and the Intake Coordinator, keeping the critical signal visibly active until the packet is complete and routed. Absence of a required designation is handled as a governance blocker under FR-054 instead.
- **FR-027**: System MUST state only the observed signal and its source in an escalation packet, and MUST NOT assert, imply, or rank a clinical judgement.
- **FR-028**: System MUST hold escalation and raise a governance blocker when no designated clinical recipient is configured, rather than routing to a default or non-clinical recipient.
- **FR-051**: System MUST require escalation-packet dispatch to be approved by a designated Escalation Dispatch Approver drawn from the approver role registry, who MUST NOT be that packet's designated clinical recipient, and MUST surface a pending dispatch as a non-suppressible alert that cannot be dismissed without a recorded approve or reject decision. Where no Escalation Dispatch Approver has been designated, System MUST hold the packet and raise a governance blocker rather than dispatching it or defaulting to another role.
- **FR-052**: System MUST enforce a dispatch-approval deadline drawn from the approved policy table that is strictly shorter than the 30-minute critical acknowledgement SLA in FR-022, so the remainder of that window stays available for clinical acknowledgement. System MUST record a breach when the deadline elapses, MUST NOT dispatch on breach without an approval, and MUST raise a governance blocker rather than adopting a default value where no such deadline has been approved.
- **FR-053**: System MUST keep a rejected escalation packet undispatched, record the rejection rationale, and keep the critical signal visibly active.
- **FR-054**: System MUST resolve every critical-condition signal to exactly one escalation outcome, evaluating a governance blocker first. Where any required designation is absent — the clinical recipient (FR-028), the Escalation Dispatch Approver (FR-051), or an approved dispatch-approval deadline (FR-052) — System MUST raise a governance blocker and MUST NOT instead report the absence as a packet completeness failure, even where the missing designation is also a mandatory packet field under FR-025. Only where all three designations are present MUST System evaluate packet completeness and raise a completeness blocker under FR-026, and only where the packet is additionally complete MUST System raise the dispatch approval under FR-051.

**Human control**

- **FR-029**: System MUST present every draft and route proposal to an authorized human who can approve, edit, reject, or return it for rework.
- **FR-030**: System MUST NOT send, submit, escalate clinically, finalize clearance, or route for release without an explicit recorded human approval by a human holding the required role.
- **FR-031**: System MUST return a rejected case to the stage that produced the rejected output — a rejected draft returns to drafting, a rejected route proposal returns to routing, a rejected data value returns to data completion — MUST NOT rewind it to a stage earlier than data completion, and MUST capture the rejection rationale against the case.
- **FR-032**: System MUST retain a human-edited output as the authoritative version and use that version downstream.
- **FR-033**: System MUST require clinical clearance first and financial clearance second, each recorded by an authorized human, before a case becomes eligible for release routing, and MUST refuse a financial clearance recorded while clinical clearance is outstanding.
- **FR-034**: System MUST refuse a clearance recorded by a person who already holds the other clearance on the same case, enforcing separation of duty between clinical and financial clearance.
- **FR-035**: System MUST escalate a case to a human owner after two rework loops rather than permitting a third.
- **FR-036**: System MUST decline any request for autonomous diagnosis, treatment recommendation, medical-necessity determination, clinical clearance authorization, or discharge/release authorization, at every workflow stage, and direct the requester to the appropriate qualified human authority.
- **FR-037**: System MUST record every refused request and its refusal in the case record.
- **FR-038**: System MUST NOT occupy any approver role; it may prepare, draft, collate and route only.

**Visibility**

- **FR-039**: System MUST show, for every item in progress, its current stage, its owner, and how long it has been in progress.
- **FR-040**: System MUST make the total elapsed time for a completed item visible so it can be compared against the manual baseline for the same document.
- **FR-041**: System MUST make all approval statuses, blockers, provisional routing flags, and unresolved data completion tasks visible.

**Audit, governance and data handling**

- **FR-042**: System MUST record a complete, ordered case history covering arrival, extracted data, backfilled values and their sources, rules fired, approvals and approvers, human edits, escalations, refusals, and a timestamp for each.
- **FR-043**: System MUST enable a compliance reviewer to reconstruct any sampled completed case end to end from the recorded history alone.
- **FR-044**: System MUST mask personal identifiers in all logs and audit records.
- **FR-045**: System MUST associate every routing and approval decision with the policy version in force at the time of that decision.
- **FR-046**: System MUST use only synthetic or de-identified sample data, and MUST NOT ingest, store, log, or export real patient-identifiable information at any point.
- **FR-047**: System MUST retain full case lineage for the project lifetime and at minimum 90 days, with no purge before review sign-off.
- **FR-048**: System MUST support re-measuring its own accuracy and speed on demand against a fixed sample document set, producing a repeatable result.
- **FR-049**: System MUST produce identical per-case outcome classifications across runs on the same dataset and build, with aggregate scores varying by no more than 2 percentage points.
- **FR-050**: System MUST treat `docs/constitution.md` as authoritative and non-overridable by any execution agent or automation, and MUST record every implementation change in `docs/progress-log.md`.

### Acceptance Scenario Traceability

Every acceptance scenario from the feature request is traceable to at least one written requirement.

| # | Acceptance scenario | User story | Requirements |
|---|---|---|---|
| AS-1 | Complete request registered; key details extracted accurately | US1 | FR-001, FR-002 |
| AS-2 | Missing details backfilled; unresolved fields listed and routed to completion tasks | US1 | FR-003, FR-004, FR-006, FR-008, FR-009 |
| AS-3 | Confidence-threshold policy sets provisional routing or holds; targeted requests prepared | US1 | FR-007, FR-010, FR-011, FR-012, FR-013, FR-016 |
| AS-4 | Case routed with one-line reason and visible rule trace | US2 | FR-017, FR-018, FR-045 |
| AS-5 | Reviewer edits and approves handoff summary; edited version retained and used | US3 | FR-029, FR-032 |
| AS-6 | Reviewer rejects; nothing sent; case returns to correct stage with rationale | US3 | FR-030, FR-031 |
| AS-7 | Duplicate detected and flagged rather than reprocessed | US1 | FR-014, FR-015 |
| AS-8 | Tests/medications artifacts appended with timestamp and source context | US4 | FR-019 |
| AS-9 | Policy-eligible approvals opened in parallel; blocking approvals identified | US4 | FR-020, FR-021 |
| AS-10 | Critical signal auto-prepares escalation to clinical authority, no clinical decision | US5 | FR-024, FR-025, FR-026, FR-027, FR-028, FR-051, FR-052, FR-053, FR-054 |
| AS-11 | Clinical clearance then finance clearance, then release eligibility | US6 | FR-033, FR-034, FR-030 |
| AS-12 | Team lead sees stage, owner, elapsed time, approvals, blockers, provisional flags | US7 | FR-039, FR-040, FR-041 |
| AS-13 | Clinical-act requests declined and directed to qualified humans | US8 | FR-036, FR-037, FR-038 |
| AS-14 | Compliance reviewer reconstructs end-to-end case history | US9 | FR-042, FR-043, FR-044, FR-045 |

### Key Entities

- **Case**: The tracked administrative work item created on arrival. Carries a unique identifier, arrival timestamp, current stage, current owner, elapsed time, and lifecycle state.
- **Case Record**: The structured set of extracted and backfilled details required for safe administrative progression. Each field carries its value, its source (submitted / backfilled / human-entered), and its resolution state (present / missing / not applicable / disputed).
- **Data Completion Task**: An open request for a specific unresolved mandatory field, with an assigned expert or administrative owner and an open/closed state.
- **Routing Decision**: The assignment of a case to a receiving team, carrying the one-line reason, the rule trace, the confidence value, whether it is provisional, and the policy version in force.
- **Duplicate Flag**: A probable-duplicate marker linking a newly arrived request to an in-progress case, with the matched key and the adjudication state.
- **Approval Task**: A role-scoped request for human approval, carrying the role, whether it blocks progression, its SLA class, its elapsed time, and its outcome (approved / edited / rejected / returned for rework) with rationale.
- **Escalation Packet**: The assembled critical-condition notification, carrying all mandatory fields, the designated clinical recipient, its completeness state, its dispatch-approval state, and its routing state.
- **Clearance Gate**: A mandatory human gate (clinical or financial) recorded against a case, carrying the authorizing human's role, the timestamp, and its effect on release eligibility.
- **Draft Artifact**: A prepared output (handoff summary, missing-information request, route proposal) with its assistant-generated version and any human-edited authoritative version.
- **Audit Event**: An immutable, timestamped, identifier-masked record of one thing that happened to a case, sufficient in aggregate to reconstruct the case end to end.
- **Policy Version**: The identified, dated version of the routing and approval rules in force, referenced by every routing and approval decision.
- **Role**: An authority (not a person) that may act on a case — Intake Coordinator, the five role-scoped approvers, Clinical Authority, Finance Clearance Approver, Team Lead, Compliance Reviewer, Team Validation Lead. **Escalation Dispatch Approver** is a required designation over this registry rather than a new authority; which registry role holds it is an open governance decision.

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Lower cycle time**

- **SC-001**: Processing an item through the assistant takes measurably less elapsed time than performing the identical work by hand on the same document, measured from arrival to "ready for human approval", with the manual path reported as the median of three runs and the claim stated as a range across sampled documents.
- **SC-002**: The number of steps that must occur in sequence is lower than the manual baseline, achieved by running eligible approvals and data-completion tasking in parallel rather than in a queue.
- **SC-003**: A draft is ready in under 30 seconds, measured from intake to draft ready.

**Fewer errors**

- **SC-004**: Key details are extracted correctly for at least 85% of graded fields across the fixed sample document set.
- **SC-005**: 100% of deliberately introduced omissions in test documents are detected.
- **SC-006**: Items are assigned to the expected team in at least 9 of 10 graded sample cases.
- **SC-007**: At least 90% of items reach routing with complete data.
- **SC-015**: Every provisionally routed item carries a correct provisional flag naming what remains outstanding, and exactly zero items advance on a value flagged as missing, contradictory, or implausible.
- **SC-008**: Exactly zero items are sent or finalised without a recorded human approval.
- **SC-009**: 100% of duplicate submissions in the sample set are flagged, and no non-duplicate is falsely flagged.

**Operational reliability**

- **SC-010**: Approval SLA compliance improves relative to the sequential baseline, measured as the proportion of approvals closed within their SLA class (2 business days routine, 4 hours urgent, 30 minutes critical acknowledgement).
- **SC-011**: For 100% of critical-condition signals in the sample set the system produces exactly one outcome, selected in this precedence order: (1) a **governance blocker** where any required designation is absent — the clinical recipient (FR-028), the Escalation Dispatch Approver (FR-051), or an approved dispatch-approval deadline (FR-052) — which takes precedence over any completeness finding, including a missing recipient that would otherwise read as a missing mandatory field; (2) a **completeness blocker** where all three designations are present but the packet is missing a mandatory field (FR-025, FR-026); (3) a **dispatch approval** carrying a complete packet where all three designations are present and no mandatory field is missing. 100% of approved packets are routed to the designated clinical authority, zero partial packets are sent, and a rejected packet remains undispatched with its rationale recorded.
- **SC-012**: Audit reconstruction completeness is 100% for sampled completed cases, with zero unmasked personal identifiers found.
- **SC-013**: Re-running the measurement on the same sample set and build produces identical per-case classifications and aggregate scores within 2 percentage points.
- **SC-014**: 100% of requests for autonomous clinical acts are declined and redirected to a qualified human.

## Assumptions

Reasonable defaults chosen where the feature request did not specify a value. Each is the most conservative option consistent with the non-negotiable constraints, and each is flagged in `docs/progress-log.md` for human review.

- **Numeric policy values are adopted from the project's already-approved policy table** (`feature.md` §5.4, P1–P9) rather than invented, because those values were decided and change-logged before this specification and reopening them would contradict an approved decision.
- **"Policy confidence thresholds"** for provisional routing means routing confidence ≥ 0.80 with mandatory field preconditions (P1). This is safety-bearing.
- **"Large majority"** means ≥ 85% for field extraction accuracy and ≥ 90% for first-pass completeness (`feature.md` §7).
- **"A short time of case arrival"** for draft readiness means under 30 seconds from intake to draft ready (`feature.md` §7).
- **Approval SLA targets** are 2 business days routine / 4 hours urgent / 30 minutes critical acknowledgement, warning at 80% elapsed (P4, P5).
- **The duplicate window** is 72 hours with a sender + patient reference + requested service match key (P2), and a match results in a flag held for human adjudication rather than any automated resolution.
- **The set of "critical conditions"** is assumed to be a fixed, human-curated, reviewable list of signal patterns. The assistant matches against that list and never infers new critical conditions on its own. The contents of that list require clinical input and are not decided here.
- **Rework loops** are capped at 2 before mandatory human escalation (P6).
- **Audit retention** is the project lifetime, minimum 90 days (P8). Production HIPAA retention of 6 years is explicitly out of scope for this build but named so the gap is visible.
- **Repeatability tolerance** is ±2 aggregate percentage points with 100% identical per-case classifications (P7).
- **The interaction surface** is a single conversational web/in-app surface with one demo tenant and one authenticated reviewer session (P9).
- **The routing queue set** is fixed at five queues — Insurance, Operations, Diagnostics, Legal, Finance — and routing rules are fixed and declarative, not customer-configurable (`feature.md` §13.5).
- **Sample data** is `SYN-CASESET-v1` (20 hand-authored synthetic case documents with a JSON answer key in `data/`), with provenance recorded per constitution §3. No external dataset is adopted and no real patient data is used at any point.
- **Roles are authorities, not individuals**, per the project's approver role registry; the assistant holds no role in that registry.
- **Documents are assumed to have a readable text layer** for the primary path; scanned/OCR-only documents are handled as the unreadable-input edge case rather than as a primary flow.
- **Escalation-packet dispatch requires recorded approval by a designated Escalation Dispatch Approver**, who must not be the packet's own clinical recipient, and where no such approver is designated the packet is held under a governance blocker rather than dispatched. The source request described escalation as automatic; the non-negotiable constraint that every outbound action carries a recorded human approval takes precedence, so automation was limited to packet preparation plus a non-suppressible approval prompt. The approver role registry currently names **no** role authorized to approve escalation dispatch, so this specification deliberately does not assign one — it requires the designation to exist. Naming that role is a governance decision and may require a registry amendment.
- **A dispatch-approval deadline of 15 minutes is *proposed*, not asserted.** `feature.md` §5.4 requires every scored numeric threshold to live in the approved policy table, and no dispatch-approval deadline exists there today. FR-052 therefore requires only that an approved deadline exists and is strictly shorter than the 30-minute critical acknowledgement window (P4), and raises a governance blocker where none has been approved. 15 minutes is offered as the candidate value — chosen so it sits inside that window and leaves the remainder available for clinical acknowledgement — but it is **not normative** until added to the policy table under change control.
- **Clearance ordering is clinical first, then financial**, read from the acceptance scenario wording. If the two clearances are in fact order-independent in the target organisation, the ordering requirement should be relaxed.
- **Completion-task ownership** is determined by an inspectable field-to-role mapping over the approver role registry, defaulting to the Intake Coordinator where a field has no mapped owner. The mapping itself is a policy artifact and is not enumerated here.

## Out of Scope

- Connecting to any live electronic health record or production clinical system.
- Submitting anything to a real insurer, payer, or external body.
- Making prior authorisation or coverage determinations of any kind.
- Any autonomous clinical or diagnostic judgement.
- Multi-organisation tenancy, single sign-on, and production hosting concerns.
- Any claim of financial savings or headcount reduction.
