## Purpose

Decides which team owns a case using rules a non-technical reviewer can read, states the reason in one line, exposes the full rule trace behind that decision, and governs when a case may move provisionally on incomplete data versus when it must be held.

## ADDED Requirements

### Requirement: Route cases using inspectable, declarative rules

The system SHALL determine the owning team for each case using declarative routing rules held in a reviewable configuration rather than embedded in code. Each routing decision SHALL be accompanied by a one-line reason stated in plain language, and by a rule trace listing every rule evaluated, the outcome of each, and the case attributes that drove them. A decision a non-technical reviewer cannot understand SHALL be treated as a defect. Where no rule matches, the system SHALL NOT guess a queue; it SHALL mark the case unroutable and refer it to a human.

*Traces to F7. Value: both — removes the routing decision step (cycle time) and reduces misroutes (errors).*

#### Scenario: A case that clearly belongs to a team is routed with a reason

- **WHEN** a case whose attributes match a routing rule is evaluated
- **THEN** the system routes it to the team that rule designates
- **AND** states a one-line reason for the routing decision in plain language
- **AND** exposes a rule trace showing every rule evaluated, its outcome, and the case attributes that drove it

#### Scenario: No routing rule matches

- **WHEN** a case matches no routing rule
- **THEN** the system marks the case unroutable rather than selecting a default or best-guess queue
- **AND** refers it to a human with the attributes that failed to match

#### Scenario: A reviewer inspects why a case went where it did

- **WHEN** a reviewer opens the routing decision for any case
- **THEN** the reviewer can read the one-line reason, the rule trace, and the version of the routing policy that produced it
- **AND** can do so without reading source code

#### Scenario: Routing accuracy is measurable against the fixed sample set

- **WHEN** routing is run across the sample cases with known correct queues
- **THEN** the proportion routed to the expected team is reported
- **AND** each incorrect routing is attributable to a specific rule in the trace

### Requirement: Permit provisional routing only under confidence policy

The system SHALL allow a case with unresolved required data to progress provisionally only when the provisional-routing policy **P1** defined in `feature.md` §5.4 is satisfied. When the policy is not satisfied, the system SHALL hold progression and prepare targeted requests for the missing information instead. A provisionally routed case SHALL be clearly and persistently marked as provisional, SHALL list the unresolved fields that made it provisional, and SHALL be re-evaluated whenever new data arrives. Provisional status SHALL NOT satisfy any clearance gate and SHALL NOT permit release routing. Where re-evaluation after the missing data arrives yields a different owning team from the provisional one, the system SHALL re-route the case, notify the team it was originally routed to, mark work already performed in that team as void while retaining it in the audit trail rather than deleting it, and count the reversal against the rework limit **P6** defined in `feature.md` §5.4; exceeding **P6** SHALL escalate the case to the Team Lead.

*Traces to F6. Value: lower cycle time — eligible work advances instead of queueing, without advancing unsafely.*

#### Scenario: Confidence policy is met and the case routes provisionally

- **WHEN** required data remains unresolved and the provisional-routing policy is satisfied
- **THEN** the system routes the case provisionally to the indicated team
- **AND** marks the case provisional with the unresolved fields listed
- **AND** the provisional flag is visible in the status view

#### Scenario: Confidence policy is not met and progression is held

- **WHEN** required data remains unresolved and the provisional-routing policy is not satisfied
- **THEN** the system holds progression
- **AND** prepares targeted requests for exactly the missing information
- **AND** states in the status view why the case is held

#### Scenario: A provisional case is re-evaluated when data arrives

- **WHEN** previously unresolved data is supplied for a provisionally routed case
- **THEN** the system re-runs the completeness check and re-evaluates routing
- **AND** clears the provisional flag once no unresolved required fields remain
- **AND** records both the provisional period and its resolution in the audit trail

#### Scenario: A provisional route proves wrong and is reversed

- **WHEN** re-evaluation of a provisionally routed case yields a different owning team
- **THEN** the system re-routes the case to the corrected team
- **AND** notifies the team it was originally routed to that the case has moved
- **AND** marks work already performed in the original queue as void while retaining it in the audit trail
- **AND** counts the reversal against the rework limit

#### Scenario: Provisional status cannot satisfy a gate

- **WHEN** a provisionally routed case reaches a clearance gate or release routing
- **THEN** the system blocks progression while the provisional flag remains set
- **AND** names the provisional flag as the blocker

### Requirement: Version the routing and approval policy

The system SHALL version the routing and approval policy and record an effective date for each version. Every routing decision, provisional-routing determination, and approval-opening decision SHALL record the policy version under which it was made, so that a past decision can be re-read against the rules that were actually in force at the time. A policy change SHALL NOT retroactively alter the recorded basis of a decision already made.

*Traces to F23. Value: fewer errors — decisions stay explainable after the rules change.*

#### Scenario: A decision records its policy version

- **WHEN** the system makes a routing or approval-opening decision
- **THEN** it records the policy version and effective date in force at that moment alongside the decision
- **AND** the version is visible in the rule trace

#### Scenario: A past decision is re-read after a policy change

- **WHEN** the routing policy is changed and a reviewer inspects a decision made before the change
- **THEN** the reviewer sees the policy version that was actually applied to that decision
- **AND** the recorded basis of that decision is unchanged by the new policy version
