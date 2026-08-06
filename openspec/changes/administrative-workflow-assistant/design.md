## Context

The repository already carries the analysis this change depends on, and this design deliberately consumes it rather than restating or re-deriving it:

- `feature.md` §5 defines the feature catalogue **F1–F24**. Every requirement written in this change traces to one or more of those identifiers, and every identifier is claimed by exactly one capability.
- `feature.md` §5.4 defines policy thresholds **P1–P9** (provisional-routing confidence, duplicate window, escalation packet completeness, service-level targets, early warning, rework limit, drift tolerance, retention, surface scope). The delta specs reference these by identifier instead of hardcoding numbers, so a threshold change is a policy-version change rather than a spec rewrite.
- `feature.md` §7 defines the numeric success targets that resolve the brief's qualitative phrasing.
- `feature.md` §13.3 defines the manual-baseline measurement protocol.
- `docs/multipass-validation-harness.md` §4.1 defines the approver role model, the eleven roles, and the separation-of-duty rule that the agent may never occupy an approver role.
- `data/sample/` holds `SYN-CASESET-v1` — twenty synthetic cases plus an answer key, with seeded omissions, duplicate pairs, a near-duplicate guard, misroute traps, not-applicable false-positive traps, a field contradiction, a critical-condition escalation, and both clearance gates.
- `docs/constitution.md` is authoritative and non-overridable. `openspec/constitution.md` is a byte-identical copy that exists only so OpenSpec tooling has a local reference.

The binding constraint shaping every decision below is that this is an **administrative** assistant operating under a clinical safety boundary. It may prepare, collate, route, draft and escalate. It may not diagnose, recommend treatment, determine medical necessity, authorize clinical clearance, or authorize discharge or release. Where a design choice traded convenience against that boundary, the boundary won.

The second binding constraint is the two expected values: **lower cycle time** and **fewer errors**. Each requirement in this change carries an explicit trace line naming which of the two it serves. A requirement that served neither was not written.

## Goals / Non-Goals

**Goals:**

- Express the Administrative Workflow Assistant as a validated OpenSpec change consisting of a proposal, eleven capability delta specs, this design, and a task breakdown — with every one of the fourteen acceptance scenarios traceable to a written, testable requirement.
- Decompose the work into capabilities that partition F1–F24 exactly once, so there is no feature without an owner and no feature owned twice.
- Encode the human-decides principle structurally, so that no path exists through the specification in which a final or outbound action occurs without a recorded human approval.
- Encode the clinical safety boundary as a capability with its own requirements and refusal scenarios, rather than as a caveat attached to other capabilities.
- Resolve the brief's qualitative language ("large majority", "nine out of ten", "short time") against the numeric targets already recorded in `feature.md` §7, and record each such resolution as an assumption for human review rather than silently adopting it.
- Surface every question that genuinely needs a human answer, rather than inventing a plausible answer and burying it in a requirement.

**Non-Goals:**

- **Implementation of any kind.** This change produces specification artifacts only. No application code, schema, service, prompt, or configuration is written, and `tasks.md` is a forward-looking breakdown that is explicitly not executed in this change.
- Choosing a technology stack, framework, storage engine, model, or hosting arrangement. The delta specs are deliberately implementation-neutral so that a reviewer can assess behaviour before architecture.
- Connecting to any live electronic health record or production clinical system.
- Submitting anything to a real insurer, payer, or external body.
- Making prior-authorisation or coverage determinations of any kind.
- Handling real patient data. The entire change is scoped to synthetic or de-identified sample data.
- Resolving the production data-retention question. `feature.md` already records the gap between policy **P8** and what a production deployment would require; this change makes the gap explicit rather than closing it.

## Decisions

### Decision 1: Decompose into eleven capabilities partitioning F1–F24 exactly once

Each of F1–F24 is claimed by exactly one capability, so ownership is unambiguous and no feature is silently dropped or double-counted.

| Capability | Features | Acceptance scenarios |
|---|---|---|
| `case-intake` | F1, F2, F3 | 1, 2 |
| `case-data-quality` | F4, F5, F8 | 2, 3, 7 |
| `explainable-routing` | F6, F7, F23 | 3, 4 |
| `human-approval-control` | F9, F12 | 5, 6 |
| `approval-orchestration` | F10, F11, F15 | 8, 9 |
| `clinical-escalation` | F13 | 10 |
| `clearance-and-release-gates` | F16, F17, F18 | 11 |
| `workflow-visibility` | F14, F22 | 12 |
| `safety-boundary` | F19 | 13 |
| `audit-and-compliance-trail` | F20, F24 | 14 |
| `evaluation-harness` | F21 | success criteria |

*Alternatives considered.* A single monolithic capability was rejected: it would have made the safety boundary a subsection rather than a first-class reviewable unit, and would have prevented a compliance reviewer from reading the boundary in isolation. A per-feature decomposition into twenty-four capabilities was rejected as fragmentation — F16, F17 and F18 in particular only make sense read together as a gate sequence, and splitting them would have hidden the ordering requirement that acceptance scenario 11 depends on.

### Decision 2: Make the safety boundary its own capability, not a cross-cutting caveat

`safety-boundary` (F19) is a standalone capability with its own requirements covering refusal, redirection, consistency under rephrasing and privilege, non-overridability by configuration, and — importantly — the requirement that permitted administrative actions are *not* over-refused.

*Rationale.* A boundary expressed as a caveat on eleven other capabilities is eleven places to get it wrong and no single place to review it. Making it a capability gives it its own scenarios, including the adversarial ones (rephrasing, privileged roles, configuration override), which is where such boundaries actually fail.

*Alternatives considered.* Attaching a "must not perform clinical judgement" clause to each capability was rejected for the reason above. Treating it purely as a runtime guardrail outside the spec was rejected because it would be untestable from the specification.

### Decision 3: Reference policy thresholds by identifier rather than inlining values

Requirements cite **P1**–**P9** by identifier and point to `feature.md` §5.4 for the values.

*Rationale.* Thresholds are policy, and policy changes. Inlining `0.80` or `72 hours` into a requirement means a policy change becomes a specification change and every downstream artifact drifts. Referencing by identifier keeps the spec stable and makes **F23** (policy versioning) meaningful — a threshold change produces a new policy version, and the `explainable-routing` and `evaluation-harness` capabilities require results to record which policy version produced them.

*Trade-off.* A reader must consult `feature.md` §5.4 to know the actual numbers. This is accepted: the alternative is numbers duplicated in twelve files that will diverge.

### Decision 4: Model provisional routing as a visible, blocking state rather than a soft hint

Under **P1**, a case may be routed provisionally only when confidence meets the threshold and the minimum identifying fields are present — and never while a critical-condition signal is active or a clearance is pending. A provisional flag is prominent in both list and detail views, lists the unresolved fields that caused it, and blocks release eligibility.

*Rationale.* The whole value of provisional routing is cycle time — work starts before every field is resolved. The whole risk is that "provisional" quietly becomes "final". Making the flag blocking at the release gate means the shortcut cannot survive to the point where it would cause harm.

*Alternatives considered.* Holding all progression until data is complete was rejected as forfeiting the cycle-time benefit the feature exists for. Treating provisional as advisory metadata was rejected as the failure mode described above.

### Decision 5: Enforce clearance ordering as clinical, then financial

Acceptance scenario 11 reads as a sequence. The `clearance-and-release-gates` capability implements it as one: clinical clearance must be recorded before the financial clearance gate opens, and separation of duty prevents one person holding both on the same case.

*Rationale.* A conservative literal reading of the acceptance scenario. If financial clearance could be granted first, a case could accrue financial approval it should never have been eligible for, and the rework is worse than the wait.

*Open point.* Whether the ordering is a genuine business rule or an artifact of how scenario 11 was written is recorded in Open Questions below. This design adopts the strict reading and flags it rather than assuming the looser one.

### Decision 6: Bind every accuracy and speed claim to a protocol and a version

The `evaluation-harness` capability requires every reported result to identify the dataset version, policy version and build, to name failing cases individually rather than reporting only aggregates, and to hold per-case classifications 100% identical across repeated runs under **P7**. Speed comparisons must be produced under the `feature.md` §13.3 baseline protocol — identical inputs, the same "ready for human approval" endpoint, a manual median from a blind operator — and reported as a range rather than a headline figure.

*Rationale.* The brief requires accuracy and speed to be "re-measurable on demand, producing a repeatable result". A number without a protocol and a version is not repeatable; it is an anecdote. Requiring the harness to *refuse* to present off-protocol figures as evidence is what makes the constraint bite.

### Decision 7: Resolve the brief's qualitative language against `feature.md` §7, and flag each resolution

The brief uses phrases like "a large majority", "nine out of ten", and "a short time". Rather than leave these untestable or invent thresholds, each was resolved against the numeric target already recorded in `feature.md` §7, and each resolution is recorded as an assumption in `docs/progress-log.md` for human confirmation.

| Brief phrase | Resolved to | Source |
|---|---|---|
| "large majority" of details extracted correctly | ≥85% extraction accuracy | `feature.md` §7 |
| routed correctly "nine out of ten times" | ≥90% routing accuracy | `feature.md` §7 |
| "large majority" reach progression complete first pass | ≥90% first-pass completeness | `feature.md` §7 |
| confidence threshold for provisional routing | **P1** | `feature.md` §5.4 |
| service-level targets and early warning | **P4**, **P5** | `feature.md` §5.4 |
| route plan ready "a short time" after arrival | <30s time-to-first-action | `feature.md` §7 |
| duplicate detection window | **P2** | `feature.md` §5.4 |

*Rationale.* Reusing the repository's own recorded targets keeps one source of truth. Flagging each resolution keeps the reviewer in control of a decision the agent should not make unilaterally.

### Decision 8: Keep delta specs implementation-neutral

No delta spec names a language, framework, datastore, model, or service. Requirements describe observable behaviour and the evidence that behaviour leaves behind.

*Rationale.* The purpose of this change is to get the *behaviour* reviewed and approved before anything is built. Architecture decisions embedded in a behavioural spec would smuggle unreviewed choices past the reviewer and make the spec harder to satisfy in more than one way.

## Traceability: acceptance scenarios to requirements

Every one of the fourteen acceptance scenarios from the brief maps to at least one written requirement.

Requirement names below are the exact `### Requirement:` headings in the delta specs, so the mapping can be checked mechanically.

| # | Acceptance scenario | Capability | Requirement |
|---|---|---|---|
| 1 | Complete request registered, key details extracted accurately | `case-intake` | Register an arriving case as a tracked work item; Extract a structured case record |
| 2 | Missing details backfilled; unresolved fields listed and routed to completion tasks | `case-intake`, `case-data-quality` | Backfill missing required fields from available records; Check completeness and plausibility before advancement; Create targeted completion tasks for unresolved mandatory data |
| 3 | Confidence-threshold policy applied — provisional routing with flags or hold, plus targeted missing-data requests | `explainable-routing`, `case-data-quality` | Permit provisional routing only under confidence policy; Create targeted completion tasks for unresolved mandatory data |
| 4 | Case routed to the right team with a one-line reason and visible rule trace | `explainable-routing` | Route cases using inspectable, declarative rules |
| 5 | Handoff summary prepared, reviewer edits and approves, edited version retained and used | `human-approval-control` | Present drafts and route proposals for human decision; Retain human-edited output as authoritative |
| 6 | Reviewer rejects; nothing final sent; case returns to correct stage with rationale | `human-approval-control` | Never act without a recorded human approval; Return rejected work to the correct prior stage with rationale |
| 7 | Duplicate submission flagged as probable duplicate, not reprocessed | `case-data-quality` | Detect and flag probable duplicate submissions |
| 8 | Test/medication administrative artifacts appended with timestamp and source context | `approval-orchestration` | Append administrative artifacts to the case record |
| 9 | Policy-eligible approvals opened in parallel; blocking approvals identified | `approval-orchestration` | Open role-based approvals in parallel where policy allows |
| 10 | Critical-condition signal triggers auto-prepared escalation to clinical authority, no clinical decision made | `clinical-escalation` | Detect critical-condition signals in test and diagnostic inputs; Auto-prepare a complete escalation packet; Route escalation to the designated clinical authority without deciding |
| 11 | Clinical clearance, then finance clearance, then release eligibility | `clearance-and-release-gates` | Require human clinical clearance before release eligibility; Require human financial clearance before release eligibility; Gate release routing on all mandatory prerequisites |
| 12 | Team lead sees stage, owner, elapsed time, approvals, blockers, provisional flags | `workflow-visibility` | Show stage, owner and elapsed time for every in-flight item; Show approval statuses, blockers and provisional flags |
| 13 | Assistant declines diagnosis / treatment / medical necessity / clinical clearance / discharge authorization | `safety-boundary` | Decline prohibited clinical requests and redirect to qualified humans; Enforce the safety boundary consistently at every stage |
| 14 | Compliance reviewer reconstructs full case history | `audit-and-compliance-trail` | Record a replay-grade lineage for every case; Mask personal identifiers in logs and audit records |

The non-negotiable constraints are likewise covered: synthetic-data-only and identifier masking by `audit-and-compliance-trail`; human approval for every final action by `human-approval-control`; the clinical prohibitions by `safety-boundary`; inspectable routing by `explainable-routing`; on-demand re-measurement by `evaluation-harness`; and constitution authority plus mandatory progress logging by `audit-and-compliance-trail`.

## Risks / Trade-offs

**[The critical-condition signal taxonomy is undefined] → Mitigation:** the `clinical-escalation` capability specifies detection behaviour, packet completeness under **P3**, and routing, but deliberately does not enumerate what counts as critical. That list is safety-bearing and must be authored and signed off by a qualified clinician. It is raised in Open Questions and must be resolved before implementation begins, not during it.

**[Provisional routing could quietly become permanent] → Mitigation:** the provisional flag is required to be prominent in both list and detail views, to enumerate the unresolved fields that caused it, and to block release eligibility outright. The shortcut cannot survive to the point of harm.

**[Strict clinical-then-financial ordering may be wrong] → Mitigation:** the conservative reading is adopted and explicitly flagged in Open Questions. If the intended rule is that both are required without ordering, only the `clearance-and-release-gates` capability changes, and the change is small and localised.

**[Numeric targets adopted from `feature.md` §7 may not be what the brief author intended] → Mitigation:** every resolution is tabulated in Decision 7 and recorded as an assumption in `docs/progress-log.md` under "Assumptions — flag for review". None is buried inside a requirement.

**[Eleven capabilities is a large surface to review at once] → Mitigation:** the capability table maps each one to its features and acceptance scenarios, so a reviewer can review by scenario or by capability. The safety-bearing capabilities — `safety-boundary`, `clinical-escalation`, `clearance-and-release-gates`, `human-approval-control` — can be reviewed first and independently.

**[Policy references by identifier add a lookup step] → Mitigation:** accepted deliberately. Decision 3 records the trade-off; the alternative is threshold values duplicated across twelve files that will drift apart.

**[Implementation-neutral specs may under-constrain a builder] → Mitigation:** accepted deliberately. `tasks.md` carries the forward-looking breakdown, and architecture is expected to be decided in a subsequent change once behaviour is approved.

**[The tooling copy of the constitution could drift from the authoritative one] → Mitigation:** `audit-and-compliance-trail` requires divergence between `openspec/constitution.md` and `docs/constitution.md` to be reported as a governance defect, with `docs/constitution.md` always winning and the tooling copy restored from it.

**[Retention configured here is shorter than production would require] → Mitigation:** `audit-and-compliance-trail` requires the gap to be stated explicitly wherever retention is documented or demonstrated, and forbids any claim of production retention compliance.

## Migration Plan

No migration is required. This change introduces eleven new capabilities and modifies none, so there is no existing specified behaviour to transition, no data to move, and no consumer to notify.

The sequencing that follows *approval* of this specification — not part of this change — is: resolve the Open Questions below, then design architecture in a separate change, then implement in the priority order recorded in `feature.md` §6, validating each increment against `SYN-CASESET-v1` through the `evaluation-harness` capability. The safety-bearing capabilities (`safety-boundary`, `clinical-escalation`, `clearance-and-release-gates`, `human-approval-control`) should be implemented and verified before any capability that could cause an outbound action.

## Open Questions

These need a human decision. None was answered unilaterally; each is carried into `docs/progress-log.md` under "Needs human decision".

1. **Backfill record source.** F3 and acceptance scenario 2 require backfilling from existing records, but `SYN-CASESET-v1` contains only inbound cases — there is no prior-records store to backfill *from*. A synthetic prior-records fixture must be defined, or the backfill requirement must be rescoped. **Owner: Team Lead.**

2. **Critical-condition signal taxonomy.** What constitutes a "critical condition signal" in test or diagnostic inputs is nowhere defined. This is safety-bearing and requires a clinician-authored, clinician-reviewed list. **Owner: Compliance Reviewer with clinical input.**

3. **Is Legal a clearance gate or approval-only?** F16 and F17 name clinical and financial clearance. Legal appears in the parallel approval set but not as a gate. This design assumes Legal is approval-only and not a release gate. **Owner: Team Lead.**

4. **Clinical-then-financial clearance ordering.** Acceptance scenario 11 reads as a strict sequence and this design enforces it as one (Decision 5). Confirm whether the ordering is a real business rule or incidental phrasing. **Owner: Compliance Reviewer.**

5. **Designated clinical authority routing table.** F13 requires escalation to "the designated clinical authority", but which authority receives which case is undefined. A routing table keyed on case attributes is needed. **Owner: Team Lead with clinical input.**

6. **Retention period gap.** Policy **P8** sets a minimum retention that is shorter than a production healthcare deployment would require. `feature.md` records this as out of scope, but it remains visible in the specification and should carry an explicit decision rather than an omission. **Owner: Compliance Reviewer.**

7. **Approval service-level baseline.** The success criteria require approval SLA compliance to "improve", but no manual SLA baseline exists to improve against. Either a baseline must be measured under the `feature.md` §13.3 protocol, or the criterion must be restated as an absolute target. **Owner: Team Lead.**

8. **Provisional routing reversal procedure.** If a case routed provisionally under **P1** later proves to have been routed wrongly, the recall and re-route procedure — and what happens to work already performed in the wrong queue — is unspecified. **Owner: Team Lead.**

9. **Near-duplicate detection sensitivity.** Policy **P2** defines duplicate detection as exact-tuple matching within the defined window, but `SYN-CASESET-v1` includes a deliberate near-duplicate guard case that exact matching would not catch. Either the near-duplicate threshold must be defined, or the guard case's expected outcome must be confirmed as "not flagged". **Owner: Team Lead.**
