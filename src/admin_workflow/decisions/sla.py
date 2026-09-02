"""SLA resolution, alerting and breach — FR-022, FR-023, FR-056, P4, P5.

An SLA resolves per **urgency class and service line**. The applied value is
recorded on the item so a breach is audited against the value in force at the
time, rather than against a global constant that may since have changed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain.models import UrgencyClass
from ..policy.bundle import PolicyBundle

_BUSINESS_DAY_SECONDS = 8 * 3600  # one work day under the configured calendar

#: Administrative urgency vocabulary. Deliberately small and explicit — it must
#: never grow into anything that looks like clinical triage.
_URGENT_TOKENS = frozenset({"urgent", "stat", "immediate", "asap", "emergency", "expedite"})


class SLAUnresolvable(RuntimeError):
    """No approved value exists for this urgency class."""


@dataclass(frozen=True)
class ResolvedSLA:
    seconds: int
    resolved_from: str          # FR-022 — which entry supplied the value
    urgency: UrgencyClass
    service_line: str | None


def resolve_sla(bundle: PolicyBundle, urgency: UrgencyClass, service_line: str | None = None) -> ResolvedSLA:
    table = bundle.sla_table
    for override in table.get("service_line_overrides") or []:
        if override["urgency_class"] == urgency.value and override["service_line"] == service_line:
            return ResolvedSLA(
                seconds=int(override["seconds"]),
                resolved_from=f"service_line_override:{service_line}:{urgency.value}",
                urgency=urgency,
                service_line=service_line,
            )

    default = table["defaults"].get(urgency.value)
    if default is None:
        raise SLAUnresolvable(f"no approved SLA for urgency class {urgency.value}")
    seconds = default.get("seconds")
    if seconds is None:
        seconds = int(default["business_days"]) * _BUSINESS_DAY_SECONDS
    return ResolvedSLA(
        seconds=int(seconds),
        resolved_from=f"default:{urgency.value}",
        urgency=urgency,
        service_line=service_line,
    )


@dataclass(frozen=True)
class SLAStatus:
    elapsed_seconds: int
    applied_seconds: int
    early_warning: bool
    breached: bool
    auto_advance_permitted: bool = False   # P5 — never, under any elapsed time


def evaluate_sla(bundle: PolicyBundle, applied: ResolvedSLA, elapsed_seconds: int) -> SLAStatus:
    pct = (elapsed_seconds / applied.seconds * 100) if applied.seconds else 0
    return SLAStatus(
        elapsed_seconds=elapsed_seconds,
        applied_seconds=applied.seconds,
        early_warning=pct >= bundle.early_warning_pct,
        breached=pct >= 100,
    )


def urgency_from_text(value: str | None) -> UrgencyClass:
    """Map the document's stated urgency onto an SLA class.

    This is an *administrative* classification and carries no clinical meaning.
    It never triggers an escalation — only the critical-signal register can do
    that (P11), which is why CASE-013 and CASE-020 must not escalate.

    Matching is on tokens rather than the whole string, because the fixture
    format writes compound values such as "STAT / Immediate".
    """
    tokens = set(re.findall(r"[a-z]+", (value or "").lower()))
    return UrgencyClass.URGENT if tokens & _URGENT_TOKENS else UrgencyClass.ROUTINE
