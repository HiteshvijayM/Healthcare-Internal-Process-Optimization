"""Clearance gates — FR-033, FR-034.

The two clearances are **order-independent**. The property that protects the
patient is the *conjunction* of both gates, not their sequence: financial
clearance cannot cause clinical harm, so mandating an order adds latency and
failure modes without adding safety. Order-independence is a superset of the
source acceptance scenario, so AS-11 still passes exactly as written.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.models import Case


@dataclass(frozen=True)
class ReleaseEligibility:
    eligible: bool
    outstanding: tuple[str, ...]
    blocker: str | None


def evaluate_release_eligibility(case: Case) -> ReleaseEligibility:
    outstanding: list[str] = []
    if case.clinical_clearance is None:
        outstanding.append("clinical")
    if case.financial_clearance is None:
        outstanding.append("financial")

    if not outstanding:
        return ReleaseEligibility(True, (), None)

    names = " and ".join(f"{kind} clearance" for kind in outstanding)
    return ReleaseEligibility(
        False,
        tuple(outstanding),
        f"release routing refused: {names} outstanding",
    )


def may_record_clearance(case: Case, kind: str) -> tuple[bool, str | None]:
    """Either order is accepted. A clearance is never refused solely because the
    other is still outstanding (FR-033)."""
    if kind == "clinical" and case.clinical_clearance is not None:
        return False, "clinical clearance is already recorded on this case"
    if kind == "financial" and case.financial_clearance is not None:
        return False, "financial clearance is already recorded on this case"
    return True, None
