## Purpose

Holds the last line before a case is routed for release: clinical clearance and financial clearance are mandatory human gates, and release routing may only proceed when both are recorded and every other prerequisite is clear.

## ADDED Requirements

### Requirement: Require human clinical clearance before release eligibility

The system SHALL require a recorded clinical clearance, granted by an authorized human clinical role, before a case becomes eligible for release routing. The system SHALL NOT grant, infer, pre-populate, or recommend clinical clearance, and SHALL NOT treat the absence of a critical-condition signal as clearance. The clearance record SHALL identify the clearing human, the role exercised, the case version cleared, and the time. A case without recorded clinical clearance SHALL show it as an outstanding blocker.

*Traces to F16 and constitution §5. Value: fewer errors — nothing reaches release without a qualified human clearing it.*

#### Scenario: Clinical clearance is recorded by an authorized human

- **WHEN** an authorized clinical role grants clearance on a case
- **THEN** the system records the clearing human, the role exercised, the case version cleared, and the timestamp
- **AND** marks the clinical clearance gate satisfied for that case version

#### Scenario: The system cannot grant clinical clearance itself

- **WHEN** any automated process attempts to set, infer, or pre-populate clinical clearance
- **THEN** the system refuses and records the refused attempt
- **AND** the clinical clearance gate remains outstanding

#### Scenario: Absence of a critical signal is not clearance

- **WHEN** a case carries no detected critical-condition signal
- **THEN** the clinical clearance gate remains outstanding
- **AND** the case is not treated as cleared

### Requirement: Require human financial clearance before release eligibility

The system SHALL require a recorded financial clearance, granted by an authorized human finance role, before a case becomes eligible for release routing. The system SHALL NOT grant, infer, or recommend financial clearance. Clinical clearance SHALL be recorded before financial clearance is opened, so that the financial gate is never worked on a case that is not yet clinically cleared. The system SHALL enforce the separation-of-duty rule in `docs/multipass-validation-harness.md` §4.1: the same person SHALL NOT hold both the clinical authority and the finance clearance role on the same case.

*Traces to F17. Value: both — the gate is opened as soon as it is eligible (cycle time) and cannot be worked out of order or by one person (errors).*

#### Scenario: Finance clearance follows clinical clearance

- **WHEN** clinical clearance has been recorded on a case
- **THEN** the system opens the financial clearance gate for an authorized finance role
- **AND** does not open it before clinical clearance is recorded

#### Scenario: Separation of duty is enforced across the two gates

- **WHEN** the person who granted clinical clearance on a case attempts to grant financial clearance on the same case
- **THEN** the system refuses the action and records the refused attempt
- **AND** the financial clearance gate remains outstanding

#### Scenario: Financial clearance is recorded by an authorized human

- **WHEN** an authorized finance role grants financial clearance on a case
- **THEN** the system records the clearing human, the role exercised, the case version cleared, and the timestamp
- **AND** marks the financial clearance gate satisfied for that case version

### Requirement: Gate release routing on all mandatory prerequisites

The system SHALL route a case for release only when every mandatory prerequisite is satisfied: recorded clinical clearance, recorded financial clearance, all blocking approvals granted, no unresolved mandatory data, no active provisional flag, and no unconfirmed duplicate flag. The system SHALL NOT authorize release itself; release routing SHALL require the recorded human approval mandated by the `human-approval-control` capability. There SHALL be no bypass or override of a blocked prerequisite. When release is blocked, the system SHALL name every unsatisfied prerequisite rather than reporting a generic failure.

*Traces to F18 and constitution §5. Value: both — release proceeds the moment it legitimately can (cycle time), and never before (errors).*

#### Scenario: Both clearances complete and release becomes eligible

- **WHEN** clinical clearance is recorded, then financial clearance is recorded, and all other mandatory prerequisites are satisfied
- **THEN** the case becomes eligible for release routing
- **AND** release routing still requires an explicit recorded human approval before it occurs

#### Scenario: Release is blocked and every unsatisfied prerequisite is named

- **WHEN** release routing is attempted while any mandatory prerequisite is unsatisfied
- **THEN** the system blocks the release routing
- **AND** names every unsatisfied prerequisite individually
- **AND** offers no bypass or override

#### Scenario: The assistant does not authorize release

- **WHEN** all prerequisites are satisfied
- **THEN** the system marks the case eligible and presents it for human decision
- **AND** does not itself authorize discharge or release
