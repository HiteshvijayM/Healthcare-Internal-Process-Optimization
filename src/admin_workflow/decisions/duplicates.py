"""Duplicate detection — FR-014, FR-055, P2.

Two matchers run independently and either one flags:

* **Key match** — ``(sender, patient_reference, requested_service)`` against
  in-progress cases within the P2 window. The window is read from the bundle as a
  parameter, never hardcoded.
* **Identity match** — unbounded in time, across open *and closed* cases. This is
  what catches a clinical re-fax arriving on day five, which the windowed key
  match would let through as new work.

The flag records **which** matcher fired. That is what makes SC-009's
false-positive claim auditable rather than a bare count.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from ..domain.models import Case, DuplicateFlag, DuplicateMatcher
from ..policy.bundle import PolicyBundle

#: Transport-added material only. A broader normaliser would erase genuine
#: content differences and turn FR-055's "a difference in any retained content
#: MUST prevent one" into a false-positive generator.
_TRANSPORT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*\*\*Received(\s+via)?:\*\*.*$", re.M | re.I),
    re.compile(r"^\s*\*\*Received:\*\*.*$", re.M | re.I),
    re.compile(r"^\s*-{3,}\s*$", re.M),
    re.compile(r"^\s*\[?RE-?TRANSMISSION.*$", re.M | re.I),
    re.compile(r"^\s*FAX COVER SHEET.*$", re.M | re.I),
    re.compile(r"^\s*PAGE \d+ OF \d+\s*$", re.M | re.I),
    re.compile(r"^\s*CONFIDENTIAL - TRANSMITTED VIA.*$", re.M | re.I),
)


def normalize_content(text: str) -> str:
    """Strip transport-added material only; alter no clinical or administrative content."""
    for pattern in _TRANSPORT_PATTERNS:
        text = pattern.sub("", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_content(text).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CaseIndexEntry:
    case_id: str
    sender: str | None
    patient_reference: str | None
    requested_service: str | None
    arrived_at: str
    source_document_id: str | None
    content_hash: str
    closed: bool


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def detect_duplicate(
    case: Case,
    prior: Iterable[CaseIndexEntry],
    bundle: PolicyBundle,
) -> DuplicateFlag | None:
    """Identity match is evaluated first, because the key window must never be
    able to suppress it (FR-055)."""
    incoming_hash = content_hash(case.raw_text)
    sender = case.record.value_of("requester")
    patient = case.record.value_of("patient_reference")
    service = case.record.value_of("requested_service")

    for entry in prior:
        if entry.case_id == case.case_id:
            continue
        # Identity match — unbounded in time, all cases including closed ones.
        if case.source_document_id and entry.source_document_id and \
                case.source_document_id == entry.source_document_id:
            return DuplicateFlag(entry.case_id, DuplicateMatcher.IDENTITY, "source_document_id")
        if entry.content_hash == incoming_hash:
            return DuplicateFlag(entry.case_id, DuplicateMatcher.IDENTITY, "normalized_content_hash")

    window_hours = bundle.duplicate_window_hours
    for entry in prior:
        if entry.case_id == case.case_id or entry.closed:
            continue  # key match scope is in-progress cases only
        if not (sender and patient and service):
            continue
        same_key = (
            _norm(entry.sender) == _norm(sender)
            and _norm(entry.patient_reference) == _norm(patient)
            and _norm(entry.requested_service) == _norm(service)
        )
        if not same_key:
            continue
        delta_hours = abs((_parse(case.arrived_at) - _parse(entry.arrived_at)).total_seconds()) / 3600
        if delta_hours <= window_hours:
            return DuplicateFlag(entry.case_id, DuplicateMatcher.KEY, "sender+patient_reference+requested_service")
    return None


def _norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip().lower()
