"""The single choke point for every outbound effect — F12, never-cut.

D12: every effect that leaves the system is declared as a typed ``Effect`` and can
only execute through :meth:`ActionGate.execute`. The gate verifies that an
approval record exists, that it references *this* effect, and that it was
recorded by a principal holding the required role.

A single choke point is what makes SC-008 auditable by inspecting one component,
rather than by proving a negative across every stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..audit.store import EventStore
from ..domain.models import Role
from .ledger import ApprovalLedger, UnauthorizedRole


class UnapprovedActionError(RuntimeError):
    """FR-030 / SC-008 — refused before any effect occurs."""


#: Which authority may authorise each kind of outbound effect.
REQUIRED_ROLE: dict[str, tuple[Role, ...]] = {
    "send_information_request": (Role.INTAKE_COORDINATOR,),
    "send_handoff_summary": (
        Role.INSURANCE_APPROVER,
        Role.OPERATIONS_APPROVER,
        Role.DIAGNOSTICS_APPROVER,
        Role.LEGAL_APPROVER,
        Role.FINANCE_APPROVER,
        Role.INTAKE_COORDINATOR,
    ),
    "dispatch_escalation_packet": (Role.INTAKE_COORDINATOR, Role.TEAM_LEAD),
    "record_clinical_clearance": (Role.CLINICAL_AUTHORITY,),
    "record_financial_clearance": (Role.FINANCE_CLEARANCE_APPROVER,),
    "route_for_release": (Role.OPERATIONS_APPROVER, Role.INTAKE_COORDINATOR),
}


@dataclass(frozen=True)
class Effect:
    """A declared outbound action. Declaring it is not performing it."""

    effect_id: str
    kind: str
    case_id: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionGate:
    ledger: ApprovalLedger
    store: EventStore
    policy_version: str
    _executed: set[str] = field(default_factory=set)

    def execute(self, effect: Effect, *, now: str, perform: Callable[[Effect], Any] | None = None) -> Any:
        if effect.kind not in REQUIRED_ROLE:
            raise UnapprovedActionError(
                f"effect kind {effect.kind!r} is not declared in REQUIRED_ROLE. "
                "An undeclared effect cannot be approved, so it cannot execute."
            )
        approval = self.ledger.approval_for(effect.effect_id)
        if approval is None:
            self.store.append(
                event_type="effect.refused",
                actor="assistant",
                timestamp=now,
                case_id=effect.case_id,
                policy_version=self.policy_version,
                payload={"effect_id": effect.effect_id, "kind": effect.kind,
                         "reason": "no recorded human approval"},
            )
            raise UnapprovedActionError(
                f"{effect.kind} on {effect.case_id} has no recorded human approval (FR-030)"
            )
        if approval.decision != "approved":
            raise UnapprovedActionError(
                f"{effect.kind} on {effect.case_id} carries a {approval.decision} decision, not an approval"
            )
        if approval.role not in REQUIRED_ROLE[effect.kind]:
            raise UnauthorizedRole(
                f"{approval.role.value} may not authorise {effect.kind}; "
                f"required one of {[r.value for r in REQUIRED_ROLE[effect.kind]]}"
            )
        if effect.effect_id in self._executed:
            raise UnapprovedActionError(
                f"effect {effect.effect_id} already executed; one approval authorises one effect"
            )

        result = perform(effect) if perform is not None else None
        self._executed.add(effect.effect_id)
        self.store.append(
            event_type="effect.executed",
            actor=approval.principal,
            timestamp=now,
            case_id=effect.case_id,
            policy_version=self.policy_version,
            payload={
                "effect_id": effect.effect_id,
                "kind": effect.kind,
                "approval_id": approval.approval_id,
                "approver_role": approval.role.value,
                **effect.detail,
            },
        )
        return result

    def executed_count(self) -> int:
        return len(self._executed)
