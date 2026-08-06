## Purpose

Turns an arriving patient case into a tracked, structured work item: it registers the arrival with an identifier and timestamp, extracts the key details required for safe administrative progression, and backfills missing required fields from available records with recorded provenance before any human is asked to supply them.

## ADDED Requirements

### Requirement: Register an arriving case as a tracked work item

The system SHALL register every arriving patient case as a tracked work item carrying a unique case identifier, the time of arrival, the source channel, a current stage, and an owner. Registration SHALL occur before any extraction, checking, or routing is attempted, so that no case can be processed without being trackable. Registration SHALL NOT be blocked by missing or malformed case content; an unreadable arrival SHALL still be registered and then flagged for human attention.

*Traces to F1. Value: lower cycle time — an arrival becomes visible and countable immediately.*

#### Scenario: A case arrives and is registered

- **WHEN** a patient case document arrives through a supported channel
- **THEN** the system creates a tracked work item with a unique case identifier, the arrival timestamp, the source channel, an initial stage, and an owner placeholder
- **AND** the work item is immediately visible in the status view
- **AND** the registration event is written to the audit trail

#### Scenario: An unreadable arrival is still registered

- **WHEN** a case document arrives whose content cannot be parsed
- **THEN** the system still registers a tracked work item with identifier and arrival timestamp
- **AND** the work item is flagged as requiring human attention with the reason stated
- **AND** the system does not silently discard the arrival

### Requirement: Extract a structured case record

The system SHALL produce, for each registered case, a structured case record containing the key details required for safe administrative progression. Each extracted field SHALL carry a source reference identifying where in the source document the value came from, and a confidence value. The system SHALL NOT invent, infer, or substitute a value that is not supported by the source document or by a record lookup; a field with no support SHALL be recorded as absent rather than guessed.

*Traces to F2. Value: both — removes re-typing (cycle time) and re-keying mistakes (errors).*

#### Scenario: A complete incoming request is submitted

- **WHEN** a complete case document is submitted
- **THEN** the system registers the case and extracts its key details into a structured case record
- **AND** each extracted field carries a source reference and a confidence value
- **AND** the extracted record is available for completeness checking without any manual re-typing

#### Scenario: A field has no support in the source document

- **WHEN** extraction finds no supported value for a required field
- **THEN** the system records that field as absent
- **AND** the system does not populate it with an inferred or default value
- **AND** the absence is passed to the completeness check rather than being suppressed

#### Scenario: Extraction accuracy is measurable against the fixed sample set

- **WHEN** extraction is run across the fixed synthetic sample set
- **THEN** per-field correctness is scored against the answer key
- **AND** the aggregate field-extraction accuracy is reported and comparable between runs

### Requirement: Backfill missing required fields from available records

The system SHALL, before requesting information from any human, search the available records for values that can reliably fill required fields left absent by extraction. The available records SHALL comprise the processed-case history, indexed on patient reference and covering cases already processed in the same environment, together with a declared prior-records fixture supplying values for patient references that have no earlier processed case. Every backfilled value SHALL be tagged with its provenance — the record consulted, the match basis, and the time of lookup — and SHALL be distinguishable from a value extracted from the arriving document. The system SHALL backfill a field only when the match basis meets the configured reliability policy; a weak or ambiguous match SHALL leave the field absent rather than fill it. The absence of any consultable record source SHALL leave the field absent and SHALL NOT be treated as licence to infer a value.

*Traces to F3. Value: both — removes a chase-the-sender round trip (cycle time) and avoids wrong values (errors).*

#### Scenario: Missing details are backfilled from records

- **WHEN** a case is submitted with required details missing
- **THEN** the system first searches available records for those values
- **AND** every value it can reliably resolve is filled in and tagged with its provenance
- **AND** backfilled values are distinguishable from values extracted from the arriving document
- **AND** the fields that remain unresolved after backfill are carried forward explicitly

#### Scenario: A field is backfilled from an earlier processed case

- **WHEN** a required field is absent and an earlier processed case holds that field for the same patient reference
- **THEN** the system fills the field from that earlier case
- **AND** the provenance names the source case identifier and the patient-reference match basis
- **AND** the value is marked as backfilled rather than extracted

#### Scenario: An ambiguous record match does not backfill

- **WHEN** a record lookup for a missing required field returns an ambiguous or weak match
- **THEN** the system leaves the field absent
- **AND** records that a lookup was attempted and why it did not resolve
- **AND** the field is carried forward to missing-data tasking rather than being filled

#### Scenario: Backfill runs before any human is asked

- **WHEN** required fields are absent after extraction
- **THEN** the system completes record backfill before creating any missing-data request or completion task
- **AND** any request subsequently sent to a human asks only for fields that backfill could not resolve
