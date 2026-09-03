"""The single escalation outcome resolver — FR-054, SC-011.

One total, pure, deterministic function. Exactly one outcome, never two, never
zero. SC-011 grades that at 100%, so it is specified as a decision table and
implemented as one.

**The trap this exists to close.** The designated clinical recipient is *both* a
required designation (FR-028) and one of the seven mandatory P3 packet fields
(FR-025). When it is absent, a completeness-first implementation reports
"missing mandatory field: designated_clinical_recipient" — which is wrong. The
defect is a gap in the approver registry, not in the packet's content, and the
two have different owners and different remediation paths.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..approvals.ledger import DesignationSet
from ..domain.models import Designation, EscalationPacket, Role
from ..policy.bundle import PolicyBundle


@dataclass(frozen=True)
class GovernanceBlocker:
    absent_designations: tuple[Designation, ...]
    reason_detail: str

    @property
    def outcome(self) -> str:
        return "governance_blocker"


@dataclass(frozen=True)
class CompletenessBlocker:
    missing_fields: tuple[str, ...]
    raised_to: tuple[Role, ...] = (Role.CLINICAL_AUTHORITY, Role.INTAKE_COORDINATOR)

    @property
    def outcome(self) -> str:
        return "completeness_blocker"


@dataclass(frozen=True)
class DispatchApproval:
    approver: Role
    alternate: Role | None
    deadline_seconds: int
    suppressible: bool = False

    @property
    def outcome(self) -> str:
        return "dispatch_approval"


EscalationOutcome = GovernanceBlocker | CompletenessBlocker | DispatchApproval


@dataclass
class ClockDecision:
    """Step 0. Whether the acknowledgement clock runs, decided *before* the
    outcome. Coverage gates the clock; Step 1 still reports coverage among the
    absent designations, so a case missing coverage and another designation
    produces one blocker naming both."""

    started: bool
    reason: str


def decide_clock(designations: DesignationSet) -> ClockDecision:
    if designations.on_call_clinical_coverage:
        return ClockDecision(True, "acknowledgement clock started at detection (FR-056)")
    return ClockDecision(
        False,
        "acknowledgement clock NOT started: no on-call clinical coverage is configured, "
        "so no breach may be recorded against an unstaffed period (P4, FR-056)",
    )


def resolve_escalation_outcome(
    packet: EscalationPacket,
    bundle: PolicyBundle,
    designations: DesignationSet,
    applied_ack_sla_seconds: int,
) -> EscalationOutcome:
    """Total, pure, deterministic. No I/O. No model call. Exactly one outcome."""

    # --- Step 1: designation check. Outranks everything. Never short-circuits. --
    absent = designations.absent()
    if absent:
        names = ", ".join(d.value for d in absent)
        return GovernanceBlocker(
            absent_designations=tuple(absent),
            reason_detail=(
                f"required designation(s) absent: {names}. This is a gap in the approver "
                "registry or the policy table, not a gap in the packet's content, so it is "
                "reported as a governance blocker (FR-054)."
            ),
        )

    # --- Step 1b: deadline coherence, against the APPLIED SLA, not the default. -
    deadline = designations.dispatch_approval_deadline_seconds
    assert deadline is not None  # guaranteed by Step 1
    if deadline >= applied_ack_sla_seconds:
        return GovernanceBlocker(
            absent_designations=(),
            reason_detail=(
                f"dispatch deadline ({deadline}s) is not strictly shorter than the applied "
                f"acknowledgement SLA ({applied_ack_sla_seconds}s). FR-052 refuses to adjust "
                "either value; the configuration must be corrected."
            ),
        )

    # --- Step 2: packet content completeness. Only reachable when all four ------
    #     designations are present, which is what keeps the FR-054 trap closed.
    fields = packet.field_map()
    missing = tuple(name for name in bundle.packet_mandatory_fields if not fields.get(name))
    if missing:
        return CompletenessBlocker(missing_fields=missing)

    # --- Step 3: dispatch approval. Non-suppressible. --------------------------
    approver = designations.escalation_dispatch_approver
    assert approver is not None  # guaranteed by Step 1
    return DispatchApproval(
        approver=approver,
        alternate=designations.escalation_dispatch_alternate,
        deadline_seconds=deadline,
        suppressible=False,
    )
