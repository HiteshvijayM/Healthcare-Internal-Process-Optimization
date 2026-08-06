## Purpose

Makes the accuracy and speed claims re-checkable on demand rather than asserted once: the same fixed dataset, the same graded checks, the same recorded protocol, producing a comparable result every time it is run.

## ADDED Requirements

### Requirement: Re-measure accuracy on demand against a fixed dataset

The system SHALL provide a harness that re-measures extraction accuracy, routing accuracy, completeness, duplicate detection, escalation completeness, and clearance-gate enforcement on demand, graded against the `SYN-CASESET-v1` dataset and its answer key in `data/sample/`. Each run SHALL report per-check results and an overall result, SHALL identify the dataset version, the policy version, and the build measured, and SHALL name the specific cases that failed rather than reporting only an aggregate. A run SHALL be executable without manual setup so that it can be repeated by anyone reviewing the work.

*Traces to F21 and `feature.md` §7. Value: fewer errors — regressions are caught by re-running rather than by noticing.*

#### Scenario: An operator re-runs the accuracy measurement

- **WHEN** an operator runs the evaluation harness against `SYN-CASESET-v1`
- **THEN** the harness reports per-check and overall results for extraction, routing, completeness, duplicate detection, escalation completeness, and clearance-gate enforcement
- **AND** identifies the dataset version, policy version, and build measured
- **AND** names each failing case individually

#### Scenario: The seeded traps are exercised

- **WHEN** the harness runs the full dataset
- **THEN** it grades the seeded omissions, the duplicate pairs, the near-duplicate guard, the misroute traps, the not-applicable false-positive traps, the field contradiction, the critical-condition escalation, and both clearance gates
- **AND** reports each trap category separately

#### Scenario: A run is repeatable without manual setup

- **WHEN** the harness is run twice against the same build, dataset version, and policy version
- **THEN** both runs complete without manual setup steps
- **AND** produce results that are directly comparable

### Requirement: Hold results stable within the defined drift tolerance

Repeated runs against the same build, dataset version, and policy version SHALL produce per-case classifications that are 100% identical, and aggregate metrics that vary by no more than the drift tolerance defined by policy **P7** in `feature.md` §5.4. Where a run exceeds that tolerance, the harness SHALL report it as a drift failure naming the diverging cases, and the result SHALL NOT be reported as evidence until the divergence is explained.

*Traces to F21 and P7. Value: fewer errors — a measurement that moves on its own cannot be trusted as evidence.*

#### Scenario: Repeated runs agree case by case

- **WHEN** the harness is run repeatedly against an unchanged build, dataset version, and policy version
- **THEN** the per-case classifications are identical across runs
- **AND** aggregate metrics vary by no more than the defined drift tolerance

#### Scenario: Drift beyond tolerance is a reportable failure

- **WHEN** a run exceeds the defined drift tolerance
- **THEN** the harness reports a drift failure and names the diverging cases
- **AND** the result is not reported as evidence until the divergence is explained

### Requirement: Measure speed against a recorded manual baseline protocol

The system SHALL measure the assisted path's elapsed time using the baseline protocol recorded in `feature.md` §13.3: identical inputs for both paths, the same endpoint of "ready for human approval", a manual median taken across the defined number of runs by an operator blind to the assisted result, and results reported as a range across sampled documents rather than a single figure. The harness SHALL record which protocol version, dataset version, and build a speed result was produced under, and SHALL NOT present a speed comparison produced outside that protocol as evidence.

*Traces to F21 and `feature.md` §13.3. Value: lower cycle time — the improvement claim is measured under stated conditions instead of estimated.*

#### Scenario: A speed comparison is produced under the recorded protocol

- **WHEN** an assisted-versus-manual speed comparison is produced
- **THEN** both paths used identical inputs and the same "ready for human approval" endpoint
- **AND** the manual figure is the median of the defined number of runs by a blind operator
- **AND** the result is reported as a range across sampled documents with the protocol version, dataset version, and build identified

#### Scenario: An off-protocol measurement is not presented as evidence

- **WHEN** a speed figure is produced outside the recorded baseline protocol
- **THEN** the harness marks it as non-comparable
- **AND** it is not presented as evidence of cycle-time improvement

### Requirement: Report results against the stated success targets

The harness SHALL compare each measured metric against the corresponding target in `feature.md` §7 and report, per metric, whether the target is met, the measured value, and the sample size the value was taken from. Where a metric is not met, the harness SHALL report the shortfall explicitly rather than omitting the metric. Targets SHALL be read from the recorded policy version so that a target change is itself versioned and visible.

*Traces to F21 and `feature.md` §7. Value: both — progress against the two expected values becomes reportable rather than anecdotal.*

#### Scenario: Each metric is reported against its target

- **WHEN** the harness completes a run
- **THEN** it reports each measured metric against its stated target with the measured value and sample size
- **AND** states explicitly whether each target is met

#### Scenario: A missed target is reported rather than omitted

- **WHEN** a measured metric falls short of its target
- **THEN** the harness reports the shortfall and the gap
- **AND** does not omit the metric from the report

#### Scenario: Targets are versioned with policy

- **WHEN** a success target is changed
- **THEN** the change is carried by a new policy version
- **AND** results produced before and after identify the differing policy versions
