"""Identifier masking — installed at the WRITE boundary.

FR-044, constitution 3. D15: the filter sits on the audit writer and on the
telemetry exporter, not on the read path. Masking after the fact leaves raw
identifiers at rest, which is why this module is built before the event store.
"""

from __future__ import annotations

import re
from typing import Any

# Synthetic identifier families used by SYN-CASESET-v1. Real deployments extend
# this list; the dataset uses reserved prefixes so a leak is unambiguous.
_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("patient", re.compile(r"\bSYN-PT-\d+\b"), "SYN-PT-***"),
    ("order", re.compile(r"\bORD-\d{4}-\d+\b"), "ORD-****-***"),
    ("mrn", re.compile(r"\bMRN[-:\s]?\d+\b", re.IGNORECASE), "MRN-***"),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "***-**-****"),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "***@***"),
    ("phone", re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"), "***-***-****"),
)

# Fields that carry a bare identifier with no surrounding text to pattern-match.
_IDENTIFIER_FIELDS = frozenset({"patient_reference", "ordering_reference"})


def mask_text(text: str) -> str:
    for _, pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _mask_bare_identifier(value: str) -> str:
    masked = mask_text(value)
    if masked != value:
        return masked
    # A bare identifier that matches no pattern is still an identifier when it
    # sits in an identifier-typed field. Keep a short prefix for traceability,
    # redact the rest — full redaction would defeat FR-043 reconstruction.
    if len(value) <= 4:
        return "***"
    return value[:4] + "***"


def mask_value(key: str, value: Any) -> Any:
    if isinstance(value, str):
        if key in _IDENTIFIER_FIELDS:
            return _mask_bare_identifier(value)
        return mask_text(value)
    if isinstance(value, dict):
        return mask_mapping(value)
    if isinstance(value, (list, tuple)):
        return [mask_value(key, item) for item in value]
    return value


def mask_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: mask_value(key, value) for key, value in payload.items()}


def scan_for_unmasked(text: str) -> list[str]:
    """Contract-test helper. Returns every unmasked identifier found."""
    found: list[str] = []
    for _, pattern, _replacement in _PATTERNS:
        found.extend(pattern.findall(text))
    return found
