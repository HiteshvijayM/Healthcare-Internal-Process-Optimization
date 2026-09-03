"""Backfill from available records — F3, FR-003, FR-004.

DETERMINISTIC. Like every module in this package, it makes no model call and
imports nothing from ``extraction`` or ``drafting``.

The rule FR-003 states is narrow and deliberately so: backfill every missing
detail that is **reliably derivable** from available records, and infer nothing
that is not. "Available records" here means prior cases already registered for
the *same patient reference* — an exact identifier match, never a fuzzy one.

Two things this must never do:

* **Infer.** A value that is absent from every prior record stays missing and
  becomes a completion task. Guessing it would violate FR-002 and FR-003 alike.
* **Launder provenance.** Every backfilled value is tagged with the case it came
  from (FR-004), so a reviewer can always tell a derived value from a submitted
  one. An untagged backfill is indistinguishable from an invented one.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.models import CaseRecord, FieldSource, FieldValue, Resolution


@dataclass(frozen=True)
class BackfillCandidate:
    """A value found on a prior case for the same patient."""

    field_name: str
    value: str
    source_case_id: str


@dataclass(frozen=True)
class RecordEntry:
    """One prior case, as the record store sees it."""

    case_id: str
    patient_reference: str | None
    fields: dict[str, str]


def build_record_store(entries: list[RecordEntry]) -> dict[str, list[RecordEntry]]:
    """Index prior cases by patient reference. Exact match only."""
    store: dict[str, list[RecordEntry]] = {}
    for entry in entries:
        if entry.patient_reference:
            store.setdefault(entry.patient_reference, []).append(entry)
    return store


def find_backfill(
    record: CaseRecord,
    field_names: tuple[str, ...],
    store: dict[str, list[RecordEntry]],
    *,
    exclude_case_id: str | None = None,
) -> list[BackfillCandidate]:
    """Return a candidate for each named field that is missing here and present
    on a prior case for the same patient.

    Where two prior cases disagree on a value, **nothing is returned** for that
    field. A conflict is not a derivation, and picking one silently would be the
    inference FR-003 forbids — the field stays missing and a human resolves it.
    """
    patient = record.value_of("patient_reference")
    if not patient:
        return []

    candidates: list[BackfillCandidate] = []
    for name in field_names:
        current = record.get(name)
        if current is not None and current.resolution is not Resolution.MISSING:
            continue

        seen: dict[str, str] = {}
        for entry in store.get(patient, []):
            if entry.case_id == exclude_case_id:
                continue
            value = entry.fields.get(name)
            if value:
                seen[value] = entry.case_id

        if len(seen) == 1:
            value, source_case = next(iter(seen.items()))
            candidates.append(BackfillCandidate(name, value, source_case))
        # len(seen) == 0 → not derivable; len(seen) > 1 → conflicting records.
        # Both leave the field missing, which is the safe outcome.
    return candidates


def apply_backfill(record: CaseRecord, candidates: list[BackfillCandidate]) -> None:
    """Write each candidate onto the record, tagged with its source (FR-004)."""
    for candidate in candidates:
        record.fields[candidate.field_name] = FieldValue(
            name=candidate.field_name,
            value=candidate.value,
            source=FieldSource.BACKFILLED,
            resolution=Resolution.PRESENT,
            derived_from=candidate.source_case_id,
        )
