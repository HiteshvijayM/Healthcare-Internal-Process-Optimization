## Purpose

Lets a compliance reviewer reconstruct exactly what happened to any single case and why — every arrival, extracted and backfilled value, rule fired, approval, edit, escalation and timestamp — with personal identifiers masked, and enforces the constitution and progress-log discipline that make that record trustworthy.

## ADDED Requirements

### Requirement: Record a replay-grade lineage for every case

The system SHALL record, for every case, a complete event lineage sufficient to reconstruct the case end to end without reference to any external system. The lineage SHALL include: the arrival and its source; every extracted value with its source reference and confidence; every backfilled value with its provenance; every completeness or plausibility finding; every routing rule evaluated with its outcome and the policy version applied; every approval, rejection, edit and return with the acting human, role and timestamp; every escalation prepared, routed and acknowledged; every clearance recorded; and every refusal. Lineage entries SHALL be append-only — the system SHALL NOT rewrite or delete a recorded event.

*Traces to F20 and constitution §4. Value: fewer errors — what happened is knowable rather than inferred.*

#### Scenario: A compliance reviewer reconstructs a case end to end

- **WHEN** a compliance reviewer opens the history for a completed case
- **THEN** the reviewer can see the arrival and its source, every extracted and backfilled value with provenance, every rule that fired with its outcome and policy version, every approval, edit, rejection and return with the acting human and role, every escalation and its acknowledgement, every clearance, and every timestamp
- **AND** can do so without consulting any external system

#### Scenario: The lineage is append-only

- **WHEN** a case is corrected, edited, or reprocessed
- **THEN** the system appends the correction as a new event
- **AND** the superseded event remains present and retrievable
- **AND** no recorded event is rewritten or deleted

#### Scenario: Audit reconstruction completeness is sampled and measurable

- **WHEN** completed cases are sampled for audit reconstruction
- **THEN** the proportion for which a full end-to-end reconstruction succeeds is reported
- **AND** any reconstruction gap identifies the specific missing event type

### Requirement: Mask personal identifiers in logs and audit records

The system SHALL mask personal identifiers in all logs, traces, and audit records, consistent with constitution §3. Masking SHALL be applied at the point of writing, not only at the point of display, so that an unmasked identifier is never persisted. Masking SHALL preserve the ability to correlate events belonging to the same case, so that reconstruction remains possible without exposing identity. The system SHALL operate on synthetic or de-identified data only and SHALL NOT ingest, store, log, or export real patient-identifiable data at any point.

*Traces to F20 and constitution §3. Value: fewer errors — the audit record is usable without becoming a privacy exposure.*

#### Scenario: Identifiers are masked at write time

- **WHEN** the system writes any log, trace, or audit entry containing a personal identifier
- **THEN** the identifier is masked in the persisted record
- **AND** no unmasked identifier is persisted anywhere

#### Scenario: Masked records remain correlatable

- **WHEN** a reviewer reconstructs a case from masked audit records
- **THEN** all events belonging to that case can still be correlated to it
- **AND** the reconstruction succeeds without revealing identity

#### Scenario: Only synthetic or de-identified data is processed

- **WHEN** any data is ingested into the system
- **THEN** it is synthetic or de-identified sample data with recorded provenance
- **AND** no real patient-identifiable data is ingested, stored, logged, or exported

### Requirement: Retain case lineage for the defined retention period

The system SHALL retain full case lineage for the retention period defined by policy **P8** in `feature.md` §5.4, and SHALL NOT purge a case's lineage before review sign-off. Where the retention configured for this build is shorter than what a production deployment would require, the system SHALL make that gap explicit in its documentation rather than implying production readiness.

*Traces to F20. Value: fewer errors — the record survives long enough to be reviewed.*

#### Scenario: Lineage survives the retention window

- **WHEN** a completed case reaches the end of processing
- **THEN** its full lineage remains retrievable for the defined retention period
- **AND** it is not purged before review sign-off

#### Scenario: The production retention gap is stated rather than implied away

- **WHEN** retention behaviour is documented or demonstrated
- **THEN** the difference between the retention configured here and what a production deployment would require is stated explicitly
- **AND** no claim of production retention compliance is made

### Requirement: Enforce constitution compliance and mandatory progress logging

The system and its delivery process SHALL treat `docs/constitution.md` as authoritative and non-overridable by any execution agent or automation. No configuration, prompt, model instruction, agent, or automated process SHALL relax, reinterpret, or work around it; a request that conflicts with it SHALL stop work and escalate to the Team Lead and Compliance Reviewer named in constitution §2. The copy held at `openspec/constitution.md` exists solely so OpenSpec tooling has a local reference and SHALL remain byte-identical to `docs/constitution.md`, which wins on any divergence. Every implementation change SHALL be recorded in `docs/progress-log.md` before the change is considered complete.

*Traces to F24 and constitution §2, §7, §8. Value: both — governance is enforced rather than aspirational.*

#### Scenario: An automated process attempts to override the constitution

- **WHEN** any agent, automation, configuration, or instruction attempts to relax, reinterpret, or bypass a constitution constraint
- **THEN** the attempt is refused
- **AND** work stops and is escalated to the Team Lead and Compliance Reviewer
- **AND** the attempt is recorded for compliance review

#### Scenario: The tooling copy of the constitution diverges

- **WHEN** `openspec/constitution.md` differs from `docs/constitution.md`
- **THEN** the divergence is reported as a governance defect
- **AND** `docs/constitution.md` is treated as authoritative
- **AND** the tooling copy is restored from it rather than the reverse

#### Scenario: A change is not complete until it is logged

- **WHEN** an implementation change is made
- **THEN** a corresponding entry is recorded in `docs/progress-log.md` with date, owner, status, impacted files, summary, and validation evidence
- **AND** the change is not treated as complete until that entry exists
