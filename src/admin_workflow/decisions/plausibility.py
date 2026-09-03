"""Plausibility checks — FR-006.

Distinct from extraction. Extraction records what the document says, faithfully.
Plausibility asks whether what it says can be true *together*, and surfaces the
conflict for a human rather than resolving it.

The distinction matters: a contradiction is not an extraction error, and marking
the field disputed would misreport a value that was read correctly. CASE-013
tests exactly this — the stated urgency must be neither silently accepted as STAT
nor silently downgraded to routine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain.models import Case

_HIGH_URGENCY = re.compile(r"\b(stat|immediate|emergen\w*)\b", re.I)
_ROUTINE_SERVICE = re.compile(r"\b(routine|annual|wellness|preventive|preventative)\b", re.I)


@dataclass(frozen=True)
class Contradiction:
    fields: tuple[str, ...]
    detail: str


def find_contradictions(case: Case) -> list[Contradiction]:
    found: list[Contradiction] = []
    urgency = case.record.value_of("urgency") or ""
    service = case.record.value_of("requested_service") or ""

    if _HIGH_URGENCY.search(urgency) and _ROUTINE_SERVICE.search(service):
        found.append(
            Contradiction(
                fields=("urgency", "requested_service"),
                detail=(
                    f"stated urgency ({urgency}) is inconsistent with the requested service class "
                    f"({service}), which is routine preventive work carrying no clinical indication. "
                    "Surfaced for human resolution — not accepted, and not downgraded."
                ),
            )
        )
    return found
