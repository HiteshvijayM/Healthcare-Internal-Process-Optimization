## Purpose

Removes the queueing that dominates elapsed time by opening role-based approvals in parallel instead of in sequence, making blocking approvals obvious, keeping the case record current as administrative artifacts arrive, and tracking service-level targets so a stalled approval is seen before it breaches.

## ADDED Requirements

### Requirement: Open role-based approvals in parallel where policy allows

The system SHALL open approvals for the insurance, operations, diagnostics, legal and finance roles in parallel wherever the approval policy permits, rather than queueing them behind one another. Where the policy requires an approval to follow another, the system SHALL state the dependency explicitly rather than serialising silently. The system SHALL identify which open approvals block progression and which do not, and SHALL make the count of remaining blocking approvals visible. Opening an approval SHALL NOT constitute granting it.

*Traces to F11. Value: lower cycle time — eligible approvals run at the same time instead of waiting in six queues.*

#### Scenario: Policy-eligible approvals are opened in parallel

- **WHEN** a case reaches the approval stage and policy permits parallel approval
- **THEN** the system opens the eligible insurance, operations, diagnostics, legal and finance approvals at the same time
- **AND** identifies which of the open approvals block progression
- **AND** shows how many blocking approvals remain outstanding

#### Scenario: A dependent approval is stated rather than silently serialised

- **WHEN** the approval policy requires one approval to complete before another may open
- **THEN** the system states the dependency and the approval it waits on
- **AND** opens the dependent approval as soon as its predecessor completes

#### Scenario: A blocking approval is rejected

- **WHEN** a blocking approval is rejected by its role approver
- **THEN** progression is halted with the rejecting role and rationale named as the blocker
- **AND** the remaining open approvals and their states are still visible

#### Scenario: Serial handoffs are countable before and after

- **WHEN** a completed case is inspected
- **THEN** the number of steps that had to happen in sequence is reported
- **AND** that count is comparable against the sequential manual path for the same case

### Requirement: Append administrative artifacts to the case record

The system SHALL append administrative artifacts relating to prescribed tests or medications to the case record as they become available. Each appended artifact SHALL carry the time it was appended and the source context it came from. Appends SHALL be additive: the system SHALL NOT overwrite or remove a previously recorded artifact, so the record remains a complete chronological account. An appended artifact SHALL be visible to any human reviewing the case.

*Traces to F10. Value: fewer errors — the record stays current and traceable rather than being reassembled by hand.*

#### Scenario: A tests or medications artifact is appended

- **WHEN** an administrative artifact relating to prescribed tests or medications becomes available for a case
- **THEN** the system appends it to the case record
- **AND** records the append timestamp and the source context
- **AND** the artifact is visible to reviewers of that case

#### Scenario: A later artifact does not overwrite an earlier one

- **WHEN** a further artifact arrives for a case that already holds one
- **THEN** the system appends the new artifact alongside the existing one
- **AND** the earlier artifact and its timestamp remain intact and retrievable

### Requirement: Track approval service levels and alert before breach

The system SHALL track elapsed time against the approval and stage service-level targets **P4** defined in `feature.md` §5.4, and SHALL raise an early-warning alert at the threshold defined by **P5** before a target is breached. A breach SHALL be recorded against the case and surfaced as a blocker. Service-level tracking SHALL NOT cause any item to advance automatically; an elapsed target changes visibility and alerting only, never approval state.

*Traces to F15. Value: lower cycle time — stalled approvals become visible while there is still time to act.*

#### Scenario: An early-warning alert fires before breach

- **WHEN** an open approval reaches the early-warning threshold of its service-level target
- **THEN** the system raises an alert against the case
- **AND** the alert names the approval, the role, and the time remaining

#### Scenario: A service-level target is breached

- **WHEN** an open approval passes its service-level target without a decision
- **THEN** the system records a breach against the case
- **AND** surfaces the breach as a visible, actionable blocker
- **AND** the approval remains pending rather than advancing

#### Scenario: Elapsed time never substitutes for a decision

- **WHEN** any service-level target elapses on a pending approval
- **THEN** the approval state is unchanged
- **AND** no downstream step is unblocked as a result of the elapsed time alone
