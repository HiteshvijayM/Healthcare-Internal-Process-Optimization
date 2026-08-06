## Purpose

Guarantees that the assistant assists and humans decide: it prepares drafts and route proposals for authorized humans, gives them approve, edit, reject and return-for-rework actions, keeps any human edit as the authoritative version, and makes it impossible for the system to send, submit, escalate clinically, clear or release anything without a recorded human approval.

## ADDED Requirements

### Requirement: Present drafts and route proposals for human decision

The system SHALL present every draft output and every route proposal to an authorized human before it takes effect. The presenting view SHALL show the draft content, the case it belongs to, the routing reason and rule trace where applicable, and the fields whose values were backfilled or are still unresolved. Authorized humans SHALL be able to approve, edit, reject, or return the item for rework. Authorization SHALL be role-based, following the approver role model in `docs/multipass-validation-harness.md` §4.1, and the system itself SHALL NOT occupy an approver role or approve on a human's behalf.

*Traces to F9 and F12. Value: both — a ready draft removes the writing step (cycle time) while the human check catches mistakes (errors).*

#### Scenario: A handoff summary is prepared for review

- **WHEN** a case reaches the handoff stage
- **THEN** the system prepares a concise handoff summary for the receiving team
- **AND** presents it to an authorized reviewer with editable fields
- **AND** shows the routing reason, the rule trace, and any backfilled or unresolved fields alongside it

#### Scenario: Only an authorized role may act on a draft

- **WHEN** a user without the required approver role attempts to approve, reject, or return a draft
- **THEN** the system refuses the action and records the refused attempt
- **AND** the draft remains in its pending state

#### Scenario: The system cannot approve on a human's behalf

- **WHEN** any automated process attempts to record an approval
- **THEN** the system refuses to register it as a human approval
- **AND** the item remains pending a decision by an authorized human

### Requirement: Retain human-edited output as authoritative

The system SHALL retain the human-edited version of any draft as the authoritative version, and SHALL use that version for all downstream steps. The system SHALL NOT regenerate over, silently merge with, or revert a human edit. Both the original generated draft and the human-edited version SHALL be preserved in the audit trail, together with the editor's identity and the time of the edit, so the difference between what the assistant proposed and what the human decided is always reconstructable.

*Traces to F12. Value: fewer errors — the human's correction is what actually gets used.*

#### Scenario: A reviewer edits and approves a prepared summary

- **WHEN** a reviewer edits a prepared handoff summary and approves it
- **THEN** the system retains the edited version as authoritative
- **AND** the edited version is what is used downstream
- **AND** both the original draft and the edited version are preserved in the audit trail with editor identity and timestamp

#### Scenario: A later step does not overwrite a human edit

- **WHEN** a downstream step would regenerate content a human has already edited
- **THEN** the system preserves the human-edited version
- **AND** surfaces any proposed change as a new draft for human decision rather than applying it

### Requirement: Return rejected work to the correct prior stage with rationale

The system SHALL, when a reviewer rejects a prepared output or returns it for rework, send the case back to the correct prior stage and record the reviewer's rationale against the case. Nothing prepared SHALL be sent, submitted, or finalised as a result of a rejection. The rationale SHALL be visible to whoever picks the case up next. The system SHALL enforce the rework-loop limit **P6** defined in `feature.md` §5.4, escalating to a human owner rather than looping indefinitely once the limit is reached.

*Traces to F12. Value: both — rework is targeted rather than restarted (cycle time), and the reason is not lost (errors).*

#### Scenario: A reviewer rejects a prepared output

- **WHEN** a reviewer rejects a prepared output
- **THEN** nothing is sent, submitted, or finalised
- **AND** the case returns to the correct prior stage
- **AND** the reviewer's rationale is captured against the case and visible to the next owner

#### Scenario: The rework-loop limit is reached

- **WHEN** a case is returned for rework more times than the rework-loop limit permits
- **THEN** the system stops the loop and escalates the case to a human owner
- **AND** records that the limit was reached

### Requirement: Never act without a recorded human approval

The system SHALL NOT send, submit, escalate clinically, finalize a clearance, or route for release without an explicit recorded human approval from an authorized role. This requirement SHALL hold with no bypass, no override flag, no auto-approval configuration, and no timeout-based auto-advance: an unanswered approval SHALL remain pending and visible as a blocker rather than proceeding by default. Every approval record SHALL identify the approving human, the role exercised, the exact artifact version approved, and the time of approval.

*Traces to F12 and constitution §5. Value: fewer errors — nothing final happens without a person choosing it.*

#### Scenario: No unapproved outbound or final action occurs

- **WHEN** any step would send, submit, escalate clinically, finalize a clearance, or route for release
- **THEN** the system requires an explicit recorded approval from an authorized human first
- **AND** the action does not occur while that approval is absent

#### Scenario: An approval times out and does not auto-advance

- **WHEN** a pending approval passes its service-level target without a human response
- **THEN** the system records a breach and raises it as a blocker
- **AND** does not treat the elapsed time as approval
- **AND** the action remains blocked

#### Scenario: An approval record is complete and attributable

- **WHEN** a human approves an item
- **THEN** the system records the approving human, the role exercised, the exact artifact version approved, and the approval timestamp
- **AND** that record is retrievable from the audit trail
