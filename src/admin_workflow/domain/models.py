"""Domain entities and state machines.

Pure data. No I/O, no model calls, no policy values. Every numeric threshold
lives in the policy bundle (contract rule PC-3), never here.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


# --------------------------------------------------------------------------
# Roles and designations — AC-1: `agent` is unrepresentable, not merely rejected
# --------------------------------------------------------------------------


class Role(enum.Enum):
    """Approver authorities from harness 4.1.

    There is deliberately no ``AGENT`` member. FR-038 and harness 4.1 require the
    assistant to be *unable* to occupy an approver role, not merely disallowed
    from doing so. Because every approval record is typed against this enum, an
    agent-authored approval cannot be constructed at all.
    """

    INTAKE_COORDINATOR = "intake_coordinator"
    INSURANCE_APPROVER = "insurance_approver"
    OPERATIONS_APPROVER = "operations_approver"
    DIAGNOSTICS_APPROVER = "diagnostics_approver"
    LEGAL_APPROVER = "legal_approver"
    FINANCE_APPROVER = "finance_approver"
    CLINICAL_AUTHORITY = "clinical_authority"
    FINANCE_CLEARANCE_APPROVER = "finance_clearance_approver"
    TEAM_LEAD = "team_lead"
    COMPLIANCE_REVIEWER = "compliance_reviewer"
    TEAM_VALIDATION_LEAD = "team_validation_lead"


class Designation(enum.Enum):
    """Harness 4.2 required designations — assignments over Role, not new authorities."""

    DESIGNATED_CLINICAL_RECIPIENT = "designated_clinical_recipient"
    ESCALATION_DISPATCH_APPROVER = "escalation_dispatch_approver"
    DISPATCH_APPROVAL_DEADLINE = "dispatch_approval_deadline"
    ON_CALL_CLINICAL_COVERAGE = "on_call_clinical_coverage"


QUEUES = ("Insurance", "Operations", "Diagnostics", "Legal", "Finance")


class Queue(enum.Enum):
    INSURANCE = "Insurance"
    OPERATIONS = "Operations"
    DIAGNOSTICS = "Diagnostics"
    LEGAL = "Legal"
    FINANCE = "Finance"


class UrgencyClass(enum.Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    CRITICAL_ACKNOWLEDGEMENT = "critical_acknowledgement"


# --------------------------------------------------------------------------
# Case record — per-field provenance and resolution state
# --------------------------------------------------------------------------


class FieldSource(enum.Enum):
    SUBMITTED = "submitted"
    BACKFILLED = "backfilled"
    HUMAN_ENTERED = "human_entered"


class Resolution(enum.Enum):
    """FR-002, FR-006, FR-009.

    ``NOT_APPLICABLE`` is deliberately distinct from ``MISSING``: FR-009 forbids
    raising a completion task for a legitimately inapplicable field, and the
    dataset seeds three false-positive traps on exactly this distinction.
    ``UNREADABLE`` is distinct again — FR-002 requires marking a value unreadable
    rather than recording a guess.
    """

    PRESENT = "present"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"
    DISPUTED = "disputed"
    UNREADABLE = "unreadable"


@dataclass(frozen=True)
class FieldValue:
    name: str
    value: Any
    source: FieldSource | None
    resolution: Resolution
    derived_from: str | None = None  # FR-004 — backfill provenance

    def is_usable(self) -> bool:
        """FR-007 — an item may not advance on a flagged value."""
        return self.resolution in (Resolution.PRESENT, Resolution.NOT_APPLICABLE)


@dataclass
class CaseRecord:
    fields: dict[str, FieldValue] = field(default_factory=dict)

    def get(self, name: str) -> FieldValue | None:
        return self.fields.get(name)

    def value_of(self, name: str) -> Any:
        fv = self.fields.get(name)
        if fv is None or fv.resolution is not Resolution.PRESENT:
            return None
        return fv.value

    def missing_fields(self) -> list[str]:
        return sorted(n for n, f in self.fields.items() if f.resolution is Resolution.MISSING)

    def flagged_fields(self) -> list[str]:
        return sorted(
            n
            for n, f in self.fields.items()
            if f.resolution in (Resolution.MISSING, Resolution.DISPUTED, Resolution.UNREADABLE)
        )


# --------------------------------------------------------------------------
# Case lifecycle
# --------------------------------------------------------------------------


class Stage(enum.Enum):
    REGISTERED = "registered"
    ENRICHED = "enriched"
    VALIDATED = "validated"
    ROUTED = "routed"
    APPROVALS_OPEN = "approvals_open"
    CLEARANCE = "clearance"
    RELEASE_ELIGIBLE = "release_eligible"
    HELD = "held"
    CLOSED = "closed"


@dataclass
class Case:
    case_id: str
    arrived_at: str
    source_document_id: str | None = None
    raw_text: str = ""
    record: CaseRecord = field(default_factory=CaseRecord)
    stage: Stage = Stage.REGISTERED
    owner: Role = Role.INTAKE_COORDINATOR
    queue: Queue | None = None
    provisional: bool = False
    provisional_outstanding: list[str] = field(default_factory=list)
    critical_signal_active: bool = False
    matched_signal_ids: list[str] = field(default_factory=list)
    duplicate_flag: DuplicateFlag | None = None
    rework_loops: int = 0
    blockers: list[str] = field(default_factory=list)
    held_reason: str | None = None
    clinical_clearance: ClearanceGate | None = None
    financial_clearance: ClearanceGate | None = None
    closed: bool = False

    def hold(self, reason: str) -> None:
        self.stage = Stage.HELD
        self.held_reason = reason
        if reason not in self.blockers:
            self.blockers.append(reason)


# --------------------------------------------------------------------------
# Supporting entities
# --------------------------------------------------------------------------


class DuplicateMatcher(enum.Enum):
    KEY = "key_match"
    IDENTITY = "identity_match"


@dataclass(frozen=True)
class DuplicateFlag:
    """FR-014, FR-055. Records WHICH matcher fired — that is what makes SC-009's
    false-positive claim auditable rather than a bare count."""

    matched_case_id: str
    matcher: DuplicateMatcher
    matched_on: str
    adjudication_state: str = "held_for_adjudication"


@dataclass(frozen=True)
class RuleEvaluation:
    rule_id: str
    description: str
    result: bool


@dataclass(frozen=True)
class RoutingDecision:
    """FR-017, FR-018, FR-045."""

    queue: Queue
    reason: str
    rule_id: str
    confidence: float
    trace: tuple[RuleEvaluation, ...]
    provisional: bool
    policy_version: str


@dataclass(frozen=True)
class CompletionTask:
    field_name: str
    owner: Role
    open: bool = True


@dataclass
class ApprovalTask:
    approval_id: str
    role: Role
    subject: str
    blocking: bool
    urgency: UrgencyClass
    applied_sla_seconds: int | None
    sla_resolved_from: str
    outcome: str | None = None
    rationale: str | None = None
    elapsed_seconds: int = 0


@dataclass(frozen=True)
class ClearanceGate:
    kind: str  # "clinical" | "financial"
    role: Role
    recorded_by: str
    recorded_at: str


@dataclass
class EscalationPacket:
    """FR-025 — the seven P3 mandatory fields plus dispatch state."""

    case_id: str | None
    patient_reference: str | None
    requester: str | None
    critical_signal_description: str | None
    source_document_reference: str | None
    timestamp: str | None
    designated_clinical_recipient: str | None
    matched_signal_ids: tuple[str, ...] = ()
    dispatch_state: str = "undispatched"
    rejection_rationale: str | None = None

    def field_map(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "patient_reference": self.patient_reference,
            "requester": self.requester,
            "critical_signal_description": self.critical_signal_description,
            "source_document_reference": self.source_document_reference,
            "timestamp": self.timestamp,
            "designated_clinical_recipient": self.designated_clinical_recipient,
        }


@dataclass(frozen=True)
class DraftArtifact:
    kind: str
    assistant_version: str
    human_version: str | None = None

    @property
    def authoritative(self) -> str:
        """FR-032 — a human-edited output is the authoritative version."""
        return self.human_version if self.human_version is not None else self.assistant_version
