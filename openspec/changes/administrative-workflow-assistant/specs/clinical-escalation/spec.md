## Purpose

Makes sure a critical-condition signal reaches a qualified human quickly and completely: it detects the signal in test and diagnostic inputs, assembles a complete escalation packet, and routes it to the designated clinical authority — while making no clinical judgement of its own.

## ADDED Requirements

### Requirement: Detect critical-condition signals in test and diagnostic inputs

The system SHALL monitor test and diagnostic inputs attached to a case for **declared** critical-condition markers — criticality asserted by the source document or by the qualified human who produced it — matched against a reviewable, clinician-approved marker list versioned alongside the routing and approval policy. Detection SHALL be pattern-based against that list, SHALL NOT constitute a diagnosis, a severity assessment, or a clinical interpretation, and SHALL NOT infer criticality that the source has not declared. A detected marker SHALL be recorded against the case with the source input, the matched list entry, and the detection time. Where an input carries a criticality-adjacent marker that is absent from the list or whose meaning is ambiguous, the system SHALL fail closed by raising it for human review rather than concluding that it is not critical. The system SHALL NOT suppress, downgrade, or triage a detected signal on its own judgement.

*Traces to F13. Value: fewer errors — a critical finding is not left sitting in an administrative queue.*

#### Scenario: A critical-condition signal is detected

- **WHEN** a test or diagnostic input attached to a case carries a declared criticality marker matching an entry in the approved marker list
- **THEN** the system records the detected signal against the case with the source input, the matched entry, and the detection time
- **AND** initiates escalation packet preparation

#### Scenario: Detection makes no clinical judgement

- **WHEN** the system records a detected critical-condition signal
- **THEN** it describes the signal and its source without asserting a diagnosis, severity, or clinical interpretation
- **AND** it does not filter, downgrade, or triage the signal on its own judgement

#### Scenario: An unrecognised criticality marker fails closed

- **WHEN** a test or diagnostic input carries a criticality-adjacent marker that is absent from the approved marker list or whose meaning is ambiguous
- **THEN** the system raises the input for human review rather than concluding it is not critical
- **AND** records the unmatched marker and the reason it could not be classified
- **AND** makes no determination of the marker's clinical significance itself

### Requirement: Auto-prepare a complete escalation packet

The system SHALL automatically prepare an escalation packet whenever a critical-condition signal is detected. The packet SHALL satisfy the escalation packet completeness policy **P3** defined in `feature.md` §5.4, which requires all mandatory fields to be present and forbids partial sends. If any mandatory field cannot be populated, the system SHALL block the send, name the missing field, and raise it for immediate human attention rather than dispatching an incomplete packet. Personal identifiers within the packet SHALL be handled under the masking rules of the `audit-and-compliance-trail` capability.

*Traces to F13. Value: both — the packet is assembled instantly (cycle time) and is never incomplete (errors).*

#### Scenario: A complete escalation packet is prepared and routed

- **WHEN** a critical-condition signal is detected on a case
- **THEN** the system auto-prepares an escalation packet containing every mandatory field
- **AND** routes it to the designated clinical authority for that case
- **AND** records the preparation and routing in the audit trail

#### Scenario: An incomplete packet is never sent

- **WHEN** a mandatory escalation packet field cannot be populated
- **THEN** the system blocks the send
- **AND** names the missing field and raises it for immediate human attention
- **AND** no partial packet is dispatched

### Requirement: Route escalation to the designated clinical authority without deciding

The system SHALL route each escalation packet to the Clinical Authority role registered in the approver role model, and SHALL record the acknowledgement when it is received, against the critical acknowledgement target in **P4**. Where the primary holder of that role is unavailable, the system SHALL route to the designated deputy or on-call holder of the same role so that the acknowledgement target can still be met, and SHALL record which holder received the packet. The system SHALL NOT decide clinical urgency, SHALL NOT select a course of action, and SHALL NOT act on the escalation beyond preparing and routing it. Clinical escalation SHALL require the recorded human approval mandated by the `human-approval-control` capability before dispatch, and the escalation SHALL remain visible as an open blocker until acknowledged.

*Traces to F13 and constitution §5. Value: fewer errors — the decision stays with a qualified human, and the handoff is provably closed.*

#### Scenario: Escalation is routed to clinical authority without a clinical decision

- **WHEN** an escalation packet is prepared for a case with a detected critical-condition signal
- **THEN** the system routes it to the designated clinical authority
- **AND** makes no clinical decision, urgency judgement, or recommendation of its own
- **AND** the case record states that the clinical decision rests with the receiving authority

#### Scenario: Escalation dispatch requires human approval

- **WHEN** an escalation packet is ready to dispatch
- **THEN** the system requires an explicit recorded human approval before it is sent
- **AND** does not dispatch on its own initiative

#### Scenario: Escalation reaches a deputy when the primary holder is unavailable

- **WHEN** an escalation packet is ready and the primary holder of the Clinical Authority role is unavailable
- **THEN** the system routes the packet to the designated deputy or on-call holder of that role
- **AND** records which holder received it
- **AND** the critical acknowledgement target continues to run rather than being reset

#### Scenario: Acknowledgement is tracked until received

- **WHEN** an escalation packet has been routed to the designated clinical authority
- **THEN** the system tracks acknowledgement against the critical acknowledgement target
- **AND** the escalation remains a visible open blocker on the case until acknowledgement is recorded
- **AND** a missed acknowledgement target is raised as a breach
