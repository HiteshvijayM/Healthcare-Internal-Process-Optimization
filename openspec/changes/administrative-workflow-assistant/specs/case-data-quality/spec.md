## Purpose

Stops unsafe or wasted work before it starts: it checks the structured case record for completeness and plausibility, names exactly what is missing or does not make sense, raises targeted completion tasks against named owners for anything still unresolved, and flags probable duplicate submissions rather than letting the same request be worked twice.

## ADDED Requirements

### Requirement: Check completeness and plausibility before advancement

The system SHALL check every case record for completeness and plausibility before the case is allowed to advance, and SHALL name each problem it finds in reviewer-readable language. A completeness failure SHALL identify the specific missing field; a plausibility failure SHALL identify the specific contradictory or implausible value and state why it is implausible. A case with an unresolved mandatory-data failure SHALL NOT advance except under the provisional routing policy defined in the `explainable-routing` capability. The check SHALL distinguish a field that is genuinely absent from a field explicitly marked not applicable, and SHALL NOT report the latter as missing.

*Traces to F4. Value: fewer errors — items stop advancing with details missing.*

#### Scenario: Missing and implausible values are named

- **WHEN** a case record is checked for completeness and plausibility
- **THEN** the system lists every missing mandatory field by name
- **AND** lists every contradictory or implausible value together with the reason it is implausible
- **AND** the case does not advance on the strength of an unresolved mandatory-data failure

#### Scenario: A not-applicable field is not reported as missing

- **WHEN** a case record contains a field explicitly marked not applicable
- **THEN** the system does not report that field as missing
- **AND** does not raise a completion task for it

#### Scenario: A contradiction between two fields is surfaced

- **WHEN** two fields in the case record carry values that cannot both be true
- **THEN** the system flags the contradiction, naming both fields and the conflict
- **AND** the case is held for human resolution rather than advancing on one of the two values

#### Scenario: Every seeded omission in the sample set is detected

- **WHEN** the completeness check is run across the sample documents containing deliberately removed fields
- **THEN** every seeded omission is detected and reported
- **AND** no seeded omission passes the check undetected

### Requirement: Create targeted completion tasks for unresolved mandatory data

The system SHALL, when mandatory data remains unresolved after record backfill, create a completion task for each unresolved item, addressed to the relevant expert or administrative owner. Each task SHALL name exactly the missing item, the case it belongs to, the owner responsible, and its due state. The system SHALL request only fields that backfill could not resolve, and SHALL NOT re-request a field it already holds. Open completion tasks SHALL be visible as blockers in the status view until resolved.

*Traces to F5. Value: both — one precise request instead of a chase loop (cycle time), and the right owner is asked (errors).*

#### Scenario: Unresolved fields are routed to the correct completion owner

- **WHEN** mandatory data remains unresolved after record backfill
- **THEN** the system creates a completion task for each unresolved item
- **AND** each task names the missing item, the case, the responsible expert or administrative owner, and a due state
- **AND** the open tasks appear as blockers in the status view

#### Scenario: Targeted missing-data requests ask only for what is missing

- **WHEN** the system prepares a request to the sender or owner for missing information
- **THEN** the request names exactly the unresolved fields and nothing else
- **AND** fields already resolved by extraction or backfill are not re-requested

#### Scenario: A completion task is resolved and the case re-checked

- **WHEN** an owner supplies the missing value for an open completion task
- **THEN** the system records the supplied value with its provenance and closes the task
- **AND** re-runs the completeness and plausibility check on the updated record
- **AND** clears the corresponding blocker from the status view

### Requirement: Detect and flag probable duplicate submissions

The system SHALL compare each arriving case against cases already in progress and SHALL flag a probable duplicate rather than reprocessing it. Duplicate matching SHALL apply the duplicate-detection policy **P2** defined in `feature.md` §5.4 as an exact match on the policy-defined attribute tuple within the policy window, and SHALL be independent of the arrival channel, so that a resend of the same request through a different channel is still recognised. The system SHALL NOT apply similarity or fuzzy matching beyond that tuple, so that a case sharing a sender with an in-progress case but differing on patient reference or requested service is not flagged. A flagged duplicate SHALL be held for human confirmation and SHALL NOT be advanced, routed, or worked as a new case. A case that resembles but is not a duplicate SHALL NOT be flagged.

*Traces to F8. Value: fewer errors — the same request is not worked twice.*

#### Scenario: A duplicate submission is detected and flagged

- **WHEN** a case arrives that matches a case already in progress under the duplicate-detection policy
- **THEN** the system flags it as a probable duplicate and links it to the original case
- **AND** the duplicate is held for human confirmation rather than being reprocessed
- **AND** no routing, tasking, or approval work is opened for the duplicate

#### Scenario: A resend through a different channel is still a duplicate

- **WHEN** a request already received through one channel is resent through a different channel within the duplicate-detection window
- **THEN** the system flags it as a probable duplicate
- **AND** the differing channel is not treated as evidence that it is a new request

#### Scenario: A near-duplicate that is genuinely distinct is not flagged

- **WHEN** a case arrives that resembles an in-progress case but differs on a policy-significant attribute
- **THEN** the system does not flag it as a duplicate
- **AND** the case proceeds through normal intake and checking

#### Scenario: A human confirms or rejects the duplicate flag

- **WHEN** a human reviews a case flagged as a probable duplicate
- **THEN** the human can confirm it as a duplicate or reject the flag with rationale
- **AND** a confirmed duplicate is closed against the original case
- **AND** a rejected flag returns the case to normal processing with the rationale recorded in the audit trail
