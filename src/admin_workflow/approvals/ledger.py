"""Approval ledger and the role/designation registry.

AC-3: separation-of-duty is enforced at the point of recording, not at review
time (FR-034). A violation cannot be written, so it cannot be discovered later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..domain.models import Designation, Role


class SeparationOfDutyError(RuntimeError):
    """FR-034 — refused at the point of recording."""


class UnauthorizedRole(RuntimeError):
    """FR-030 — the recording principal does not hold the required authority."""


@dataclass(frozen=True)
class Approval:
    """A recorded human decision.

    ``role`` is typed as :class:`Role`, which has no ``AGENT`` member. An
    agent-authored approval is therefore unrepresentable rather than merely
    rejected (FR-038, AC-1).
    """

    approval_id: str
    effect_id: str
    role: Role
    principal: str
    decision: str  # approved | rejected | edited | returned_for_rework
    rationale: str | None
    recorded_at: str


@dataclass
class ApprovalLedger:
    _approvals: dict[str, Approval] = field(default_factory=dict)
    _by_effect: dict[str, str] = field(default_factory=dict)
    _case_clearances: dict[str, dict[str, str]] = field(default_factory=dict)

    def record(
        self,
        *,
        approval_id: str,
        effect_id: str,
        role: Role,
        principal: str,
        decision: str,
        recorded_at: str,
        rationale: str | None = None,
        case_id: str | None = None,
        clearance_kind: str | None = None,
    ) -> Approval:
        if clearance_kind is not None and case_id is not None:
            self._check_separation_of_duty(case_id, clearance_kind, principal)

        approval = Approval(
            approval_id=approval_id,
            effect_id=effect_id,
            role=role,
            principal=principal,
            decision=decision,
            rationale=rationale,
            recorded_at=recorded_at,
        )
        self._approvals[approval_id] = approval
        if decision == "approved":
            self._by_effect[effect_id] = approval_id
        if clearance_kind is not None and case_id is not None and decision == "approved":
            self._case_clearances.setdefault(case_id, {})[clearance_kind] = principal
        return approval

    def _check_separation_of_duty(self, case_id: str, clearance_kind: str, principal: str) -> None:
        other = "financial" if clearance_kind == "clinical" else "clinical"
        holder = self._case_clearances.get(case_id, {}).get(other)
        if holder is not None and holder == principal:
            raise SeparationOfDutyError(
                f"{principal} already recorded the {other} clearance on {case_id}; "
                "FR-034 forbids one person holding both gates on the same case"
            )

    def approval_for(self, effect_id: str) -> Approval | None:
        approval_id = self._by_effect.get(effect_id)
        return self._approvals.get(approval_id) if approval_id else None

    def get(self, approval_id: str) -> Approval | None:
        return self._approvals.get(approval_id)

    def all(self) -> list[Approval]:
        return list(self._approvals.values())


@dataclass
class DesignationSet:
    """Harness 4.2. An absent designation is ``None`` — never a default.

    FR-054 requires a governance blocker naming every absent designation, so the
    absence must be representable and inspectable rather than silently filled.
    """

    designated_clinical_recipient: str | None = None
    escalation_dispatch_approver: Role | None = None
    escalation_dispatch_alternate: Role | None = None
    dispatch_approval_deadline_seconds: int | None = None
    on_call_clinical_coverage: str | None = None

    def absent(self) -> list[Designation]:
        missing: list[Designation] = []
        if not self.designated_clinical_recipient:
            missing.append(Designation.DESIGNATED_CLINICAL_RECIPIENT)
        if self.escalation_dispatch_approver is None:
            missing.append(Designation.ESCALATION_DISPATCH_APPROVER)
        if self.dispatch_approval_deadline_seconds is None:
            missing.append(Designation.DISPATCH_APPROVAL_DEADLINE)
        if not self.on_call_clinical_coverage:
            missing.append(Designation.ON_CALL_CLINICAL_COVERAGE)
        return missing


def designations_from_bundle(bundle: Any, *, clinical_recipient: str | None,
                             on_call_coverage: str | None) -> DesignationSet:
    """Build the run's designation set from the frozen registry plus the two
    per-run assignments that the run record supplies (AC-2)."""
    registry = bundle.approver_registry["designations"]
    dispatch = registry.get("escalation_dispatch_approver", {})
    held_by = dispatch.get("held_by")
    alternate = dispatch.get("alternate")
    return DesignationSet(
        designated_clinical_recipient=clinical_recipient,
        escalation_dispatch_approver=Role(held_by) if held_by else None,
        escalation_dispatch_alternate=Role(alternate) if alternate else None,
        dispatch_approval_deadline_seconds=bundle.dispatch_deadline_seconds,
        on_call_clinical_coverage=on_call_coverage,
    )
