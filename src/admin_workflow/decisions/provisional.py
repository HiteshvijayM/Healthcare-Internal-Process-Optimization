"""Provisional routing eligibility — FR-010, FR-011, FR-012, FR-013, P1.

Safety-bearing. The confidence number alone is weak protection; the safety comes
from the conjunction around it — both mandatory fields present, no critical
signal active, no clearance gate pending, no unresolved register, and the routing
always reversible.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.models import Case, Resolution
from ..policy.bundle import PolicyBundle


@dataclass(frozen=True)
class ProvisionalDecision:
    permitted: bool
    reasons: tuple[str, ...]
    outstanding: tuple[str, ...]

    @property
    def refusal_reason(self) -> str:
        return "; ".join(self.reasons)


def may_route_provisionally(
    case: Case,
    confidence: float,
    bundle: PolicyBundle,
    *,
    register_unresolved: bool = False,
    clearance_pending: bool = False,
) -> ProvisionalDecision:
    reasons: list[str] = []

    threshold = bundle.min_routing_confidence
    if confidence < threshold:
        reasons.append(f"routing confidence {confidence:.2f} is below the P1 threshold of {threshold:.2f}")

    for name in bundle.provisional_required_fields:
        fv = case.record.get(name)
        if fv is None or fv.resolution is not Resolution.PRESENT:
            reasons.append(f"mandatory field {name} is not present")

    # FR-011 — never while a critical signal is active or a gate is pending.
    if case.critical_signal_active:
        reasons.append("a critical-condition signal is active on this case")
    if clearance_pending:
        reasons.append("a clearance gate is pending")
    if register_unresolved:
        reasons.append("the critical-condition register could not be resolved (FR-057)")

    outstanding = tuple(case.record.flagged_fields())
    return ProvisionalDecision(
        permitted=not reasons,
        reasons=tuple(reasons),
        outstanding=outstanding,
    )
