## Purpose

Answers "what is in flight, who owns it, and how long has it been sitting" for anyone who needs to know, and exposes the elapsed time of completed work so the assisted path can be compared honestly against doing the same work by hand.

## ADDED Requirements

### Requirement: Show stage, owner and elapsed time for every in-flight item

The system SHALL show, for every item in progress, the stage it is currently in, the owner responsible for it, and how long it has been in progress — both total elapsed time since arrival and time in the current stage. This view SHALL cover all in-flight items, not a filtered subset, and SHALL be current rather than a periodic snapshot. Elapsed time SHALL be derived from recorded event timestamps so that it is reconstructable from the audit trail.

*Traces to F14. Value: lower cycle time — waiting becomes visible, which is the precondition for reducing it.*

#### Scenario: A team lead opens the status view

- **WHEN** a team lead opens the status view
- **THEN** the view lists every in-flight item with its current stage and responsible owner
- **AND** shows total elapsed time since arrival and time in the current stage for each
- **AND** the elapsed values are derived from recorded event timestamps

#### Scenario: An item with no assigned owner is still visible

- **WHEN** an in-flight item has not yet been assigned an owner
- **THEN** the item still appears in the status view with an explicit unassigned owner state
- **AND** its elapsed time continues to accrue and remain visible

### Requirement: Show approval statuses, blockers and provisional flags

The system SHALL show, for every item in progress, the status of each opened approval, every current blocker, every provisional routing flag, and every unresolved data task. Blocking approvals SHALL be distinguishable from non-blocking ones. Each blocker SHALL state what it is waiting on and who owns resolving it. A service-level breach or early-warning alert SHALL be visible in the same view rather than only in a separate alerting channel.

*Traces to F14 and F15. Value: lower cycle time — the thing holding an item up is identifiable without asking anyone.*

#### Scenario: A team lead sees approvals, blockers and flags

- **WHEN** a team lead opens the status detail for a case
- **THEN** the view shows each opened approval and its status, distinguishing blocking from non-blocking
- **AND** shows every current blocker with what it awaits and who owns resolving it
- **AND** shows any provisional routing flag and every unresolved data task
- **AND** shows any service-level early warning or breach on that case

#### Scenario: A provisional flag is prominent rather than incidental

- **WHEN** a case is routed provisionally
- **THEN** the provisional flag is visible on the case in both the list view and the detail view
- **AND** the unresolved fields that caused it are listed with it

### Requirement: Expose total elapsed time for completed items

The system SHALL make the total elapsed time for each completed item visible, measured from arrival to the endpoint defined by the baseline protocol in `feature.md` §13.3, so that the assisted path can be compared against the manual path for the same document. Reported comparisons SHALL be stated as a range across sampled documents rather than a single headline figure, and SHALL identify the build and dataset version they were measured against. The system SHALL NOT report a cycle-time comparison that has not been produced under that protocol.

*Traces to F14 and F21. Value: lower cycle time — the claim becomes measurable rather than asserted.*

#### Scenario: Total elapsed time is visible for a completed item

- **WHEN** an item completes
- **THEN** the system shows its total elapsed time from arrival to the protocol endpoint
- **AND** the value is attributable to recorded event timestamps

#### Scenario: A cycle-time comparison is reported honestly

- **WHEN** an assisted-versus-manual cycle-time comparison is reported
- **THEN** it is stated as a range across the sampled documents
- **AND** it identifies the build and dataset version measured
- **AND** a comparison not produced under the baseline protocol is not reported as evidence

### Requirement: Support the workflow through a conversational surface

The system SHALL support case submission, status enquiry, approval actions, and escalation handling through the conversational surface scoped by **P9** in `feature.md` §5.4. Actions taken through the conversational surface SHALL be subject to exactly the same authorization checks, approval requirements, and audit recording as actions taken through any other surface; the conversational route SHALL NOT be a weaker path. Where a request through this surface is out of bounds, the `safety-boundary` capability governs the response.

*Traces to F22. Value: lower cycle time — the journey can be driven without switching between six queues.*

#### Scenario: A full administrative journey is driven conversationally

- **WHEN** an authorized user submits a case, checks its status, and records an approval through the conversational surface
- **THEN** each action takes effect on the case
- **AND** each action is recorded in the audit trail with the acting user and timestamp

#### Scenario: The conversational surface is not a weaker path

- **WHEN** a user attempts an action through the conversational surface for which they lack the required role
- **THEN** the system refuses the action exactly as it would on any other surface
- **AND** records the refused attempt
