"""The journey pipeline — arrival to release routing.

Stages are executed in order and every human lockpoint is a **suspension**, not a
conditional: :class:`WorkflowResult` returns with ``awaiting`` populated and the
case parked. There is no code path that proceeds without a recorded approval,
because the only way to produce an outbound effect is through the
:class:`~admin_workflow.approvals.action_gate.ActionGate`.

In a live deployment these stages bind to Microsoft Agent Framework executors
with request/response pauses; the binding seam is :func:`run_intake`'s signature.
The deterministic core is deliberately independent of that binding so the harness
can score it without a model backend (P7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..approvals.action_gate import ActionGate, Effect
from ..approvals.ledger import ApprovalLedger, DesignationSet
from ..audit.store import EventStore
from ..decisions import critical_signal as cs
from ..decisions.backfill import RecordEntry, apply_backfill, find_backfill
from ..decisions.clearance import evaluate_release_eligibility
from ..decisions.duplicates import CaseIndexEntry, content_hash, detect_duplicate
from ..decisions.escalation_outcome import (
    CompletenessBlocker,
    DispatchApproval,
    GovernanceBlocker,
    decide_clock,
    resolve_escalation_outcome,
)
from ..decisions.plausibility import find_contradictions
from ..decisions.provisional import may_route_provisionally
from ..decisions.routing import decide_route
from ..decisions.sla import UrgencyClass, resolve_sla, urgency_from_text
from ..domain.models import (
    Case,
    CaseRecord,
    CompletionTask,
    DraftArtifact,
    EscalationPacket,
    Resolution,
    Role,
    Stage,
)
from ..drafting.drafter import (
    draft_escalation_packet_body,
    draft_handoff_summary,
    draft_information_request,
)
from ..extraction.extractor import Extractor
from ..policy.bundle import PolicyBundle
from ..policy.resolvers import owner_for_field
from ..safety.guard import check_inbound

#: Fields that must be resolved before an item may advance. ``supporting_notes``
#: is excluded: it is narrative and never blocks progression.
MANDATORY_FIELDS = ("requester", "patient_reference", "requested_service", "urgency")

#: Fields worth backfilling from prior records before asking a human (F3, FR-003).
#: Wider than MANDATORY_FIELDS: a derivable value should be filled whether or not
#: its absence would have blocked the case, because asking a human for something
#: already on file is exactly the re-typing this system exists to remove.
BACKFILLABLE_FIELDS = ("payer_plan", "ordering_reference", "requester", "urgency")


@dataclass
class WorkflowResult:
    case: Case
    routing: Any = None
    #: What the source document said, snapshotted before backfill. Extraction
    #: accuracy is graded against this; the live case record evolves past it.
    extracted: CaseRecord | None = None
    drafts: list[DraftArtifact] = field(default_factory=list)
    completion_tasks: list[CompletionTask] = field(default_factory=list)
    backfilled: list[Any] = field(default_factory=list)
    contradictions: list[Any] = field(default_factory=list)
    escalation: Any = None
    packet: EscalationPacket | None = None
    clock: Any = None
    applied_sla: Any = None
    signal_statement: str = cs.NO_MATCH_STATEMENT
    register_unresolved: bool = False
    awaiting: list[str] = field(default_factory=list)
    pending_effects: list[Effect] = field(default_factory=list)


@dataclass
class Runtime:
    bundle: PolicyBundle
    store: EventStore
    ledger: ApprovalLedger
    gate: ActionGate
    designations: DesignationSet
    extractor: Extractor = field(default_factory=Extractor)
    index: list[CaseIndexEntry] = field(default_factory=list)
    #: Prior cases keyed by patient reference — the "available records" FR-003
    #: permits backfilling from. Populated as cases are registered.
    record_store: dict[str, list[RecordEntry]] = field(default_factory=dict)


def run_intake(
    runtime: Runtime,
    *,
    case_id: str,
    document_text: str,
    arrived_at: str,
    source_document_id: str | None = None,
    service_line: str | None = None,
) -> WorkflowResult:
    bundle, store = runtime.bundle, runtime.store
    version = bundle.bundle_id

    # -- F1 / FR-001, FR-005: register first, always --------------------------
    # An unreadable item is still registered and raised as a blocker; discarding
    # it would lose work silently.
    case = Case(
        case_id=case_id,
        arrived_at=arrived_at,
        source_document_id=source_document_id,
        raw_text=document_text,
    )
    store.append(event_type="case.registered", actor="assistant", timestamp=arrived_at,
                 case_id=case_id, policy_version=version,
                 payload={"source_document_id": source_document_id})
    result = WorkflowResult(case=case)

    # -- F19 / FR-036: the safety boundary sits on the inbound edge ------------
    refusal = check_inbound(document_text)
    if refusal is not None:
        store.append(event_type="safety.refused", actor="assistant", timestamp=arrived_at,
                     case_id=case_id, policy_version=version,
                     payload={"act": refusal.act, "directed_to": refusal.directed_to,
                              "message": refusal.message})
        case.hold(f"refused: {refusal.act}")
        result.awaiting.append("clinical_authority_review")
        return result

    # -- F2 / FR-002: extract; never invent, never guess ----------------------
    case.record = runtime.extractor.extract(document_text)
    store.append(event_type="case.extracted", actor="assistant", timestamp=arrived_at,
                 case_id=case_id, policy_version=version,
                 payload={"fields": {n: f.resolution.value for n, f in case.record.fields.items()}})
    # Snapshot what the *document* said, before any backfill runs. Extraction
    # accuracy and omission detection are graded against this: a value backfilled
    # from records was still absent from the source, and reporting it as
    # extracted would overstate what the reader actually read (FR-002, FR-004).
    result.extracted = CaseRecord(fields=dict(case.record.fields))

    # -- F3 / FR-003, FR-004: backfill before asking a human -----------------
    # Derive what is reliably derivable from prior records for the same patient,
    # and infer nothing that is not. Every derived value is tagged with the case
    # it came from, so it stays distinguishable from a submitted one.
    candidates = find_backfill(case.record, BACKFILLABLE_FIELDS, runtime.record_store,
                               exclude_case_id=case_id)
    if candidates:
        apply_backfill(case.record, candidates)
        result.backfilled = list(candidates)
        for candidate in candidates:
            store.append(event_type="case.backfilled", actor="assistant", timestamp=arrived_at,
                         case_id=case_id, policy_version=version,
                         payload={"field": candidate.field_name,
                                  "derived_from": candidate.source_case_id})

    # -- F13 / FR-057: critical-signal detection, register-only ---------------
    try:
        match = cs.match_signals(document_text, bundle)
        result.signal_statement = match.statement()
        if match.matched:
            case.critical_signal_active = True
            case.matched_signal_ids = [m.signal_id for m in match.matches]
    except cs.RegisterUnresolvable as exc:
        # Prohibition 3 — a missing register holds the case. It is never treated
        # as an empty register, and never reported as "no critical condition".
        result.register_unresolved = True
        case.hold(f"critical-condition register unresolvable: {exc}")
        store.append(event_type="escalation.blocked", actor="assistant", timestamp=arrived_at,
                     case_id=case_id, policy_version=version,
                     payload={"reason": f"register unresolvable: {exc}"})
        result.awaiting.append("governance_resolution")
        return result

    # -- F8 / FR-014, FR-055: duplicate detection -----------------------------
    flag = detect_duplicate(case, runtime.index, bundle)
    if flag is not None:
        case.duplicate_flag = flag
        store.append(event_type="duplicate.flagged", actor="assistant", timestamp=arrived_at,
                     case_id=case_id, policy_version=version,
                     payload={"matched_case_id": flag.matched_case_id,
                              "matcher": flag.matcher.value, "matched_on": flag.matched_on})
        result.awaiting.append("duplicate_adjudication")

    # -- F4 / F5 / FR-006, FR-008, FR-009: completeness -----------------------
    for name in MANDATORY_FIELDS:
        fv = case.record.get(name)
        if fv is None or fv.resolution in (Resolution.MISSING, Resolution.UNREADABLE):
            owner = owner_for_field(name, bundle)
            result.completion_tasks.append(CompletionTask(field_name=name, owner=owner))
        elif fv.resolution is Resolution.DISPUTED:
            # Neither silently accepted nor silently downgraded — a human resolves it.
            result.completion_tasks.append(
                CompletionTask(field_name=name, owner=owner_for_field(name, bundle))
            )
            case.blockers.append(f"contradictory value for {name}")

    # FR-006 plausibility — a contradiction between two correctly-read values is
    # not an extraction error, so it is surfaced separately rather than by
    # marking either field disputed.
    for contradiction in find_contradictions(case):
        case.blockers.append(f"contradiction: {contradiction.detail}")
        result.contradictions.append(contradiction)
        store.append(event_type="case.contradiction", actor="assistant", timestamp=arrived_at,
                     case_id=case_id, policy_version=version,
                     payload={"fields": list(contradiction.fields), "detail": contradiction.detail})
        result.awaiting.append("contradiction_resolution")

    # -- F7 / FR-017, FR-018: routing with a full rule trace ------------------
    decision = decide_route(case, bundle)
    case.queue = decision.queue
    result.routing = decision
    store.append(event_type="routing.decided", actor="assistant", timestamp=arrived_at,
                 case_id=case_id, policy_version=version,
                 payload={"queue": decision.queue.value, "rule_id": decision.rule_id,
                          "reason": decision.reason, "confidence": decision.confidence,
                          "trace": [{"rule": t.rule_id, "result": t.result} for t in decision.trace]})

    # -- F6 / FR-010, FR-011: provisional routing eligibility -----------------
    if result.completion_tasks:
        provisional = may_route_provisionally(
            case, decision.confidence, bundle,
            register_unresolved=result.register_unresolved,
            clearance_pending=False,
        )
        if provisional.permitted:
            case.provisional = True
            case.provisional_outstanding = list(provisional.outstanding)
            case.stage = Stage.ROUTED
        else:
            case.hold(provisional.refusal_reason)
        store.append(event_type="provisional.evaluated", actor="assistant", timestamp=arrived_at,
                     case_id=case_id, policy_version=version,
                     payload={"permitted": provisional.permitted,
                              "reasons": list(provisional.reasons)})
        held = [n for n, f in case.record.fields.items() if f.is_usable()]
        result.drafts.append(draft_information_request(
            case, [t.field_name for t in result.completion_tasks], held))
        result.awaiting.append("data_completion")
    else:
        case.stage = Stage.ROUTED

    # -- P4 / FR-022: resolve the SLA and record which value applied ----------
    urgency = urgency_from_text(case.record.value_of("urgency"))
    result.applied_sla = resolve_sla(bundle, urgency, service_line)
    store.append(event_type="sla.applied", actor="assistant", timestamp=arrived_at,
                 case_id=case_id, policy_version=version,
                 payload={"urgency": urgency.value, "applied_seconds": result.applied_sla.seconds,
                          "resolved_from": result.applied_sla.resolved_from})

    # -- F9 / FR-029: draft the handoff, then wait for a human ----------------
    draft = draft_handoff_summary(case, decision)
    result.drafts.append(draft)
    effect = Effect(effect_id=f"{case_id}:handoff", kind="send_handoff_summary", case_id=case_id,
                    detail={"queue": decision.queue.value})
    result.pending_effects.append(effect)
    result.awaiting.append("handoff_approval")

    # -- F13 / FR-024, FR-054: escalation, if a signal is active --------------
    if case.critical_signal_active:
        result.clock = decide_clock(runtime.designations)
        ack = resolve_sla(bundle, UrgencyClass.CRITICAL_ACKNOWLEDGEMENT, service_line)
        packet = _build_packet(case, match, arrived_at, runtime.designations)
        result.packet = packet
        outcome = resolve_escalation_outcome(packet, bundle, runtime.designations, ack.seconds)
        result.escalation = outcome
        _record_escalation(store, case_id, version, arrived_at, outcome, result.clock)
        if isinstance(outcome, DispatchApproval):
            result.pending_effects.append(
                Effect(effect_id=f"{case_id}:dispatch", kind="dispatch_escalation_packet",
                       case_id=case_id, detail={"signal_ids": list(case.matched_signal_ids)})
            )
            result.awaiting.append("dispatch_approval")
        else:
            result.awaiting.append("escalation_blocked")

    runtime.index.append(CaseIndexEntry(
        case_id=case_id,
        sender=case.record.value_of("requester"),
        patient_reference=case.record.value_of("patient_reference"),
        requested_service=case.record.value_of("requested_service"),
        arrived_at=arrived_at,
        source_document_id=source_document_id,
        content_hash=content_hash(document_text),
        closed=False,
    ))
    # Register the case as an available record for later arrivals (F3). Only
    # values that are actually PRESENT are exposed — a missing or disputed value
    # must never become a backfill source for the next case.
    patient = case.record.value_of("patient_reference")
    if patient:
        runtime.record_store.setdefault(patient, []).append(RecordEntry(
            case_id=case_id,
            patient_reference=patient,
            fields={n: str(f.value) for n, f in case.record.fields.items()
                    if f.resolution is Resolution.PRESENT and f.value is not None},
        ))
    return result


def _build_packet(case: Case, match: cs.MatchResult, now: str,
                  designations: DesignationSet) -> EscalationPacket:
    description = match.description()
    # FR-027 — the body states only the observed signal and its source. The
    # safety guard verifies it before it can leave.
    draft_escalation_packet_body(case, description, f"{case.case_id} source document")
    return EscalationPacket(
        case_id=case.case_id,
        patient_reference=case.record.value_of("patient_reference"),
        requester=case.record.value_of("requester"),
        critical_signal_description=description,
        source_document_reference=case.source_document_id or f"{case.case_id}.md",
        timestamp=now,
        designated_clinical_recipient=designations.designated_clinical_recipient,
        matched_signal_ids=tuple(m.signal_id for m in match.matches),
    )


def _record_escalation(store: EventStore, case_id: str, version: str, now: str,
                       outcome: Any, clock: Any) -> None:
    if isinstance(outcome, GovernanceBlocker):
        store.append(event_type="escalation.blocked", actor="assistant", timestamp=now,
                     case_id=case_id, policy_version=version,
                     payload={"kind": "governance",
                              "absent_designations": [d.value for d in outcome.absent_designations],
                              "reason": outcome.reason_detail,
                              "clock_started": clock.started})
    elif isinstance(outcome, CompletenessBlocker):
        store.append(event_type="escalation.blocked", actor="assistant", timestamp=now,
                     case_id=case_id, policy_version=version,
                     payload={"kind": "completeness",
                              "missing_fields": list(outcome.missing_fields),
                              "reason": "packet incomplete",
                              "raised_to": [r.value for r in outcome.raised_to]})
    else:
        store.append(event_type="escalation.awaiting_dispatch_approval", actor="assistant",
                     timestamp=now, case_id=case_id, policy_version=version,
                     payload={"approver": outcome.approver.value,
                              "deadline_seconds": outcome.deadline_seconds,
                              "suppressible": outcome.suppressible,
                              "clock_started": clock.started})


def record_clearance(runtime: Runtime, case: Case, kind: str, principal: str, now: str) -> None:
    """FR-033, FR-034 — order-independent, separation of duty enforced on write."""
    from ..domain.models import ClearanceGate

    role = Role.CLINICAL_AUTHORITY if kind == "clinical" else Role.FINANCE_CLEARANCE_APPROVER
    effect_id = f"{case.case_id}:{kind}_clearance"
    runtime.ledger.record(
        approval_id=f"appr:{effect_id}", effect_id=effect_id, role=role, principal=principal,
        decision="approved", recorded_at=now, case_id=case.case_id, clearance_kind=kind,
    )
    gate = ClearanceGate(kind=kind, role=role, recorded_by=principal, recorded_at=now)
    if kind == "clinical":
        case.clinical_clearance = gate
    else:
        case.financial_clearance = gate
    runtime.store.append(event_type="approval.recorded", actor=principal, timestamp=now,
                         case_id=case.case_id, policy_version=runtime.bundle.bundle_id,
                         payload={"kind": f"{kind}_clearance", "role": role.value})
    if evaluate_release_eligibility(case).eligible:
        case.stage = Stage.RELEASE_ELIGIBLE
