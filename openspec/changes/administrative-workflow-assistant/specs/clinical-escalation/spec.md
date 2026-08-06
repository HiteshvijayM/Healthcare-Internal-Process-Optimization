## Purpose

Makes sure a critical-condition signal reaches a qualified human quickly and completely: it detects the signal in test and diagnostic inputs, assembles a complete escalation packet, and routes it to the designated clinical authority — while making no clinical judgement of its own.

## ADDED Requirements

### Requirement: Detect critical-condition signals in test and diagnostic inputs

The system SHALL monitor test and diagnostic inputs attached to a case for critical-condition signals defined in a reviewable, human-authored signal list. Detection SHALL be pattern-based against that list and SHALL NOT constitute a diagnosis, a severity assessment, or a clinical interpretation. A detected signal SHALL be recorded against the case with the source input, the matched list entry, and the detection time. The system SHALL NOT suppress, downgrade, or triage a detected signal on its own judgement.

*Traces to F13. Value: fewer errors — a critical finding is not left sitting in an administrative queue.*

#### Scenario: A critical-condition signal is detected

- **WHEN** a test or diagnostic input attached to a case matches an entry in the critical-condition signal list
- **THEN** the system records the detected signal against the case with the source input, the matched entry, and the detection time
- **AND** initiates escalation packet preparation

#### Scenario: Detection makes no clinical judgement

- **WHEN** the system records a detected critical-condition signal
- **THEN** it describes the signal and its source without asserting a diagnosis, severity, or clinical interpretation
- **AND** it does not filter, downgrade, or triage the signal on its own judgement

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

The system SHALL route each escalation packet to the clinical authority designated for that case, and SHALL record the acknowledgement when it is received, against the critical acknowledgement target in **P4**. The system SHALL NOT decide clinical urgency, SHALL NOT select a course of action, and SHALL NOT act on the escalation beyond preparing and routing it. Clinical escalation SHALL require the recorded human approval mandated by the `human-approval-control` capability before dispatch, and the escalation SHALL remain visible as an open blocker until acknowledged.

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

#### Scenario: Acknowledgement is tracked until received

- **WHEN** an escalation packet has been routed to the designated clinical authority
- **THEN** the system tracks acknowledgement against the critical acknowledgement target
- **AND** the escalation remains a visible open blocker on the case until acknowledgement is recorded
- **AND** a missed acknowledgement target is raised as a breach
