## Purpose

Keeps the assistant inside its administrative lane at every stage: when asked for a clinical judgement it declines, says why, and directs the requester to qualified humans, rather than answering, hedging, or complying partially.

## ADDED Requirements

### Requirement: Decline prohibited clinical requests and redirect to qualified humans

The system SHALL decline any request for autonomous diagnosis, treatment recommendation, medical-necessity determination, clinical clearance authorization, or discharge or release authorization. On declining, the system SHALL state plainly that it is an administrative assistant and cannot make that decision, and SHALL direct the requester to the qualified human role that can. The system SHALL NOT answer such a request partially, SHALL NOT hedge with a caveated opinion, and SHALL NOT restate the request back as guidance. Declining SHALL NOT terminate the case; the administrative work already in progress SHALL continue unaffected.

*Traces to F19 and constitution §5. Value: fewer errors — the assistant never substitutes for a clinician.*

#### Scenario: A user asks for a prohibited clinical judgement

- **WHEN** a user asks the assistant for a diagnosis, a treatment recommendation, a medical-necessity determination, a clinical clearance authorization, or a discharge or release authorization
- **THEN** the system declines the request
- **AND** states that it is an administrative assistant and cannot make that decision
- **AND** directs the requester to the qualified human role responsible for it
- **AND** does not provide a partial answer, a hedged opinion, or the judgement restated as guidance

#### Scenario: Declining does not disrupt administrative work

- **WHEN** the system declines a prohibited clinical request on a case
- **THEN** the administrative work in progress on that case continues unaffected
- **AND** the case is not closed, halted, or reset as a result of the refusal

#### Scenario: The refusal is recorded

- **WHEN** the system declines a prohibited clinical request
- **THEN** it records the refusal in the audit trail with the request category, the acting user, and the timestamp
- **AND** the record is retrievable during compliance reconstruction

### Requirement: Enforce the safety boundary consistently at every stage

The system SHALL apply the same refusal behaviour at every stage of the workflow and on every surface, including the conversational surface. The boundary SHALL NOT be relaxed by phrasing, by role, by stage, by repeated asking, or by embedding the request inside another task. There SHALL be no configuration, flag, prompt, or instruction that permits an execution agent or automation to override it, consistent with constitution §8. A refusal SHALL be identical in substance regardless of who asks.

*Traces to F19 and constitution §8. Value: fewer errors — the boundary holds under pressure rather than only in the happy path.*

#### Scenario: Rephrasing does not defeat the boundary

- **WHEN** a user rephrases a prohibited clinical request, embeds it inside an administrative task, or asks repeatedly
- **THEN** the system declines consistently on each attempt
- **AND** the substance of the refusal is unchanged

#### Scenario: A privileged role cannot unlock a prohibited action

- **WHEN** a user holding any role, including a clinical or supervisory role, asks the system to make the clinical decision autonomously
- **THEN** the system still declines
- **AND** directs the request to be exercised by that human directly rather than performed by the system

#### Scenario: No configuration can disable the boundary

- **WHEN** any configuration, flag, prompt, or agent instruction attempts to disable or relax the safety boundary
- **THEN** the system continues to enforce the boundary
- **AND** records the override attempt for compliance review

### Requirement: Allow the administrative actions that are in bounds

The system SHALL continue to perform the administrative actions permitted by constitution §5 — data collation, administrative routing, draft generation, and escalation packet preparation — without treating them as prohibited. The safety boundary SHALL NOT be applied so broadly that legitimate administrative work is refused, and the system SHALL be able to describe a clinical fact recorded in a source document as administrative content without that constituting a clinical judgement.

*Traces to F19. Value: both — the boundary stays precise, so it protects without stalling the workflow.*

#### Scenario: Permitted administrative actions are not refused

- **WHEN** a user asks the system to collate case data, route a case administratively, draft a handoff summary, or prepare an escalation packet
- **THEN** the system performs the action
- **AND** does not refuse it as a prohibited clinical request

#### Scenario: Reporting a recorded clinical fact is not a clinical judgement

- **WHEN** a user asks what a source document records about tests or medications on a case
- **THEN** the system reports the recorded content with its source reference
- **AND** does not interpret, assess, or act on it clinically
