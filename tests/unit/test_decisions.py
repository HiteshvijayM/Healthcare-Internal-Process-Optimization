"""Unit tests — one per deterministic decision function.

Every trap in the dataset gets its own separately-failing test rather than being
folded into a happy-path assertion, so a regression names itself.
"""

from __future__ import annotations

import pytest

from admin_workflow.decisions import critical_signal as cs
from admin_workflow.decisions.clearance import evaluate_release_eligibility, may_record_clearance
from admin_workflow.decisions.duplicates import CaseIndexEntry, content_hash, detect_duplicate, normalize_content
from admin_workflow.decisions.escalation_outcome import (
    CompletenessBlocker,
    DispatchApproval,
    GovernanceBlocker,
    decide_clock,
    resolve_escalation_outcome,
)
from admin_workflow.decisions.grammar import GrammarError, evaluate, uses_only_permitted_grammar
from admin_workflow.decisions.plausibility import find_contradictions
from admin_workflow.decisions.provisional import may_route_provisionally
from admin_workflow.decisions.routing import decide_route
from admin_workflow.decisions.sla import UrgencyClass, evaluate_sla, resolve_sla, urgency_from_text
from admin_workflow.approvals.ledger import DesignationSet
from admin_workflow.domain.models import (
    Case,
    CaseRecord,
    ClearanceGate,
    Designation,
    EscalationPacket,
    FieldSource,
    FieldValue,
    Resolution,
    Role,
)

NOW = "2026-07-17T08:00:00"


def make_case(**values) -> Case:
    record = CaseRecord()
    for name, value in values.items():
        if value is None:
            record.fields[name] = FieldValue(name, None, None, Resolution.MISSING)
        else:
            record.fields[name] = FieldValue(name, value, FieldSource.SUBMITTED, Resolution.PRESENT)
    return Case(case_id="CASE-TEST", arrived_at=NOW, record=record)


# ===========================================================================
# grammar — RC-5
# ===========================================================================


def test_grammar_contains_any_matches_case_insensitively() -> None:
    assert evaluate("requested_service contains_any ['imaging','lab']", {"requested_service": "MRI Imaging"})


def test_grammar_or_does_not_split_inside_a_literal_list() -> None:
    """'or' appearing inside a quoted list must not be treated as an operator."""
    expr = "requested_service contains_any ['records or notes'] or urgency equals 'stat'"
    assert evaluate(expr, {"requested_service": "records or notes", "urgency": "routine"})


def test_grammar_rejects_an_unknown_operator() -> None:
    with pytest.raises(GrammarError):
        evaluate("requested_service matches_regex '.*'", {"requested_service": "x"})


def test_permitted_grammar_check_rejects_code() -> None:
    assert not uses_only_permitted_grammar("__import__('os').system('x')")
    assert uses_only_permitted_grammar("always")


def test_missing_field_does_not_satisfy_a_rule() -> None:
    assert not evaluate("payer_plan is_present", {"payer_plan": None})
    assert evaluate("payer_plan is_missing", {"payer_plan": None})


# ===========================================================================
# routing — FR-017, FR-018
# ===========================================================================


def test_routing_trace_records_every_rule_not_only_the_one_that_fired(bundle) -> None:
    """RC-4 — a reviewer must see what was considered and rejected."""
    case = make_case(requested_service="Subpoena response preparation", patient_reference="SYN-PT-1")
    decision = decide_route(case, bundle)
    assert len(decision.trace) == len(bundle.routing_rules["rules"])
    assert sum(1 for t in decision.trace if t.result) >= 1


def test_routing_first_match_wins(bundle) -> None:
    """RC-1 — order is part of the contract."""
    case = make_case(requested_service="Records disclosure, billing statement enclosed")
    decision = decide_route(case, bundle)
    assert decision.rule_id == "R-010"  # Legal precedes Finance


def test_routing_reason_is_one_line_and_names_the_rule(bundle) -> None:
    case = make_case(requested_service="Ultrasound scheduling, renal")
    decision = decide_route(case, bundle)
    assert "\n" not in decision.reason
    assert decision.rule_id in decision.reason


def test_unmatched_case_falls_to_the_terminal_rule_with_low_confidence(bundle) -> None:
    case = make_case(requested_service="something entirely unanticipated")
    decision = decide_route(case, bundle)
    assert decision.rule_id == "R-999"
    assert decision.confidence < bundle.min_routing_confidence


def test_routing_records_the_policy_version(bundle) -> None:
    """FR-045 — every decision carries the version in force."""
    decision = decide_route(make_case(requested_service="billing"), bundle)
    assert decision.policy_version == bundle.bundle_id


# ===========================================================================
# duplicates — FR-014, FR-055, P2
# ===========================================================================


def _entry(case_id: str, arrived: str, *, sender="A", patient="SYN-PT-1", service="S",
           doc_id=None, chash="h", closed=False) -> CaseIndexEntry:
    return CaseIndexEntry(case_id, sender, patient, service, arrived, doc_id, chash, closed)


def test_key_match_inside_the_window_flags(bundle) -> None:
    case = make_case(requester="A", patient_reference="SYN-PT-1", requested_service="S")
    case.arrived_at = "2026-07-14T15:00:00"
    case.raw_text = "body one"
    flag = detect_duplicate(case, [_entry("CASE-001", "2026-07-14T09:00:00")], bundle)
    assert flag and flag.matcher.value == "key_match"


def test_key_match_outside_the_window_does_not_flag(bundle) -> None:
    case = make_case(requester="A", patient_reference="SYN-PT-1", requested_service="S")
    case.arrived_at = "2026-07-20T09:00:00"      # 6 days later
    case.raw_text = "different body"
    assert detect_duplicate(case, [_entry("CASE-001", "2026-07-14T09:00:00")], bundle) is None


def test_identity_match_is_unbounded_in_time_and_covers_closed_cases(bundle) -> None:
    """FR-055 — the clinical re-fax on day five that the key window would miss."""
    body = "**Received:** 2026-07-14 09:12\n\nRequest body that is identical."
    case = make_case(requester="A", patient_reference="SYN-PT-1", requested_service="S")
    case.arrived_at = "2026-08-30T09:00:00"      # far outside the 72h window
    case.raw_text = body
    prior = _entry("CASE-001", "2026-07-14T09:00:00", chash=content_hash(body), closed=True)
    flag = detect_duplicate(case, [prior], bundle)
    assert flag and flag.matcher.value == "identity_match"
    assert flag.matched_case_id == "CASE-001"


def test_identity_match_ignores_transport_added_material(bundle) -> None:
    original = "**Received:** 2026-07-14 09:12\n\n---\n\nPlease schedule the patient."
    refax = ("FAX COVER SHEET\nPAGE 1 OF 2\n**Received:** 2026-07-20 11:44\n\n---\n\n"
             "Please schedule the patient.")
    assert normalize_content(original) == normalize_content(refax)


def test_identity_match_is_defeated_by_a_real_content_difference(bundle) -> None:
    """FR-055 — 'a difference in any retained content MUST prevent one'."""
    original = "Please schedule the patient for Tuesday."
    changed = "Please schedule the patient for Thursday."
    assert content_hash(original) != content_hash(changed)


def test_key_window_never_suppresses_an_identity_match(bundle) -> None:
    body = "identical body text"
    case = make_case(requester="A", patient_reference="SYN-PT-1", requested_service="S")
    case.arrived_at = "2027-01-01T00:00:00"
    case.raw_text = body
    prior = _entry("CASE-001", "2026-07-14T09:00:00", chash=content_hash(body), closed=True)
    assert detect_duplicate(case, [prior], bundle) is not None


# ===========================================================================
# critical signal — FR-057, P11, CRC-2..CRC-5
# ===========================================================================


def test_registered_marker_matches(bundle) -> None:
    result = cs.match_signals("A critical result flag was attached.", bundle)
    assert result.matched and result.matches[0].signal_id == "CCS-001"


def test_administrative_urgency_is_not_a_signal(bundle) -> None:
    """The exclusion that keeps CASE-013 and CASE-020 from escalating."""
    for text in ("Urgency: Urgent", "Subject: URGENT - please expedite", "Urgency: STAT / Immediate"):
        assert not cs.match_signals(text, bundle).matched


def test_non_match_statement_is_the_only_permitted_wording(bundle) -> None:
    """CRC-3 — reporting 'no critical condition present' is Sev 0."""
    result = cs.match_signals("An ordinary scheduling request.", bundle)
    assert result.statement() == cs.NO_MATCH_STATEMENT
    assert not cs.forbidden_negative_claim(result.statement())


def test_forbidden_negative_claim_is_detectable() -> None:
    assert cs.forbidden_negative_claim("Result: no critical condition present.")


def test_multiple_matches_yield_one_result_naming_every_id(bundle) -> None:
    """CRC-5 — one packet, not one per match."""
    text = ("critical result flag attached; please ensure it is brought to the attention of "
            "the responsible clinical team without delay")
    result = cs.match_signals(text, bundle)
    assert {m.signal_id for m in result.matches} == {"CCS-001", "CCS-002"}


def test_absent_register_raises_rather_than_reporting_clean(bundle) -> None:
    """CRC-4 — a missing register is never treated as an empty one."""

    class NoRegister:
        critical_signal_register = None
        register_id = "CCR-DEMO-v1"

    with pytest.raises(cs.RegisterUnresolvable):
        cs.match_signals("anything", NoRegister())


def test_empty_register_raises(bundle) -> None:
    class Empty:
        critical_signal_register = {"register_id": "CCR-DEMO-v1", "entries": [],
                                    "match_mode": "literal_marker"}
        register_id = "CCR-DEMO-v1"

    with pytest.raises(cs.RegisterUnresolvable):
        cs.match_signals("anything", Empty())


def test_version_mismatch_is_unresolvable(bundle) -> None:
    class Mismatched:
        critical_signal_register = {"register_id": "CCR-DEMO-v2", "entries": [{"id": "x"}],
                                    "match_mode": "literal_marker"}
        register_id = "CCR-DEMO-v1"

    with pytest.raises(cs.RegisterUnresolvable, match="version unresolvable"):
        cs.match_signals("anything", Mismatched())


def test_non_literal_match_mode_is_refused(bundle) -> None:
    class Fuzzy:
        critical_signal_register = {"register_id": "CCR-DEMO-v1", "entries": [{"id": "x"}],
                                    "match_mode": "semantic"}
        register_id = "CCR-DEMO-v1"

    with pytest.raises(cs.RegisterUnresolvable, match="literal_marker"):
        cs.match_signals("anything", Fuzzy())


def test_packet_description_states_signal_and_source_only(bundle) -> None:
    """FR-027 — no clinical assertion, no ranking."""
    result = cs.match_signals("critical result flag", bundle)
    description = result.description()
    assert "CCS-001" in description and "observed marker" in description
    for word in ("likely", "severe", "recommend", "diagnos"):
        assert word not in description.lower()


# ===========================================================================
# escalation outcome — FR-054, SC-011. The exhaustive matrix.
# ===========================================================================


def complete_packet(recipient="clinical_authority:on-call") -> EscalationPacket:
    return EscalationPacket(
        case_id="CASE-008", patient_reference="SYN-PT-40288", requester="Dr. L. Fontaine",
        critical_signal_description="CCS-001 observed", source_document_reference="CASE-008.md",
        timestamp=NOW, designated_clinical_recipient=recipient,
    )


def designations(**overrides) -> DesignationSet:
    base = dict(
        designated_clinical_recipient="clinical_authority:on-call",
        escalation_dispatch_approver=Role.INTAKE_COORDINATOR,
        escalation_dispatch_alternate=Role.TEAM_LEAD,
        dispatch_approval_deadline_seconds=600,
        on_call_clinical_coverage="roster:default",
    )
    base.update(overrides)
    return DesignationSet(**base)


def test_all_designations_present_and_complete_yields_dispatch_approval(bundle) -> None:
    outcome = resolve_escalation_outcome(complete_packet(), bundle, designations(), 1800)
    assert isinstance(outcome, DispatchApproval)
    assert outcome.suppressible is False
    assert outcome.deadline_seconds == 600
    assert outcome.alternate is Role.TEAM_LEAD


def test_absent_clinical_recipient_is_governance_never_completeness(bundle) -> None:
    """THE FR-054 TRAP.

    The designated clinical recipient is both a required designation and one of
    the seven P3 packet fields. A completeness-first implementation reports a
    missing field — which routes the defect to the wrong owner entirely.
    """
    packet = complete_packet(recipient=None)
    outcome = resolve_escalation_outcome(
        packet, bundle, designations(designated_clinical_recipient=None), 1800
    )
    assert isinstance(outcome, GovernanceBlocker), "must NOT be a CompletenessBlocker"
    assert Designation.DESIGNATED_CLINICAL_RECIPIENT in outcome.absent_designations


def test_absent_dispatch_approver_is_governance(bundle) -> None:
    outcome = resolve_escalation_outcome(
        complete_packet(), bundle, designations(escalation_dispatch_approver=None), 1800
    )
    assert isinstance(outcome, GovernanceBlocker)
    assert Designation.ESCALATION_DISPATCH_APPROVER in outcome.absent_designations


def test_absent_deadline_is_governance_and_never_defaults(bundle) -> None:
    """FR-052 — raise a blocker rather than adopting a default value."""
    outcome = resolve_escalation_outcome(
        complete_packet(), bundle, designations(dispatch_approval_deadline_seconds=None), 1800
    )
    assert isinstance(outcome, GovernanceBlocker)
    assert Designation.DISPATCH_APPROVAL_DEADLINE in outcome.absent_designations


def test_absent_coverage_is_governance_and_stops_the_clock(bundle) -> None:
    """FR-056 — no breach may be recorded against an unstaffed period."""
    d = designations(on_call_clinical_coverage=None)
    clock = decide_clock(d)
    assert clock.started is False
    outcome = resolve_escalation_outcome(complete_packet(), bundle, d, 1800)
    assert isinstance(outcome, GovernanceBlocker)
    assert Designation.ON_CALL_CLINICAL_COVERAGE in outcome.absent_designations


def test_clock_starts_at_detection_when_coverage_exists() -> None:
    clock = decide_clock(designations())
    assert clock.started is True
    assert "detection" in clock.reason


def test_multiple_absent_designations_are_all_named(bundle) -> None:
    """FR-054 forbids 'surfacing the first and concealing the rest'."""
    outcome = resolve_escalation_outcome(
        complete_packet(recipient=None), bundle,
        designations(designated_clinical_recipient=None, escalation_dispatch_approver=None), 1800,
    )
    assert isinstance(outcome, GovernanceBlocker)
    assert set(outcome.absent_designations) == {
        Designation.DESIGNATED_CLINICAL_RECIPIENT,
        Designation.ESCALATION_DISPATCH_APPROVER,
    }


def test_all_four_absent_are_all_named(bundle) -> None:
    outcome = resolve_escalation_outcome(
        complete_packet(recipient=None), bundle,
        designations(designated_clinical_recipient=None, escalation_dispatch_approver=None,
                     dispatch_approval_deadline_seconds=None, on_call_clinical_coverage=None), 1800,
    )
    assert len(outcome.absent_designations) == 4


def test_deadline_not_shorter_than_applied_sla_is_governance(bundle) -> None:
    """Step 1b — compared against the APPLIED SLA, not the global default."""
    outcome = resolve_escalation_outcome(complete_packet(), bundle, designations(), 600)
    assert isinstance(outcome, GovernanceBlocker)
    assert "strictly shorter" in outcome.reason_detail


def test_incomplete_packet_with_all_designations_is_completeness(bundle) -> None:
    packet = complete_packet()
    object.__setattr__(packet, "requester", None)
    outcome = resolve_escalation_outcome(packet, bundle, designations(), 1800)
    assert isinstance(outcome, CompletenessBlocker)
    assert "requester" in outcome.missing_fields
    assert set(outcome.raised_to) == {Role.CLINICAL_AUTHORITY, Role.INTAKE_COORDINATOR}


def test_outcome_matrix_is_total_and_single_valued(bundle) -> None:
    """Every combination yields exactly one outcome, and no combination yields two."""
    import itertools

    seen = []
    for d1, d2, d3, d4, complete in itertools.product([True, False], repeat=5):
        d = designations(
            designated_clinical_recipient="r" if d1 else None,
            escalation_dispatch_approver=Role.INTAKE_COORDINATOR if d2 else None,
            dispatch_approval_deadline_seconds=600 if d3 else None,
            on_call_clinical_coverage="c" if d4 else None,
        )
        packet = complete_packet(recipient="r" if d1 else None)
        if not complete:
            object.__setattr__(packet, "timestamp", None)
        outcome = resolve_escalation_outcome(packet, bundle, d, 1800)
        assert isinstance(outcome, (GovernanceBlocker, CompletenessBlocker, DispatchApproval))
        seen.append(outcome.outcome)
    assert len(seen) == 32


# ===========================================================================
# provisional routing — FR-010, FR-011, P1
# ===========================================================================


def test_provisional_permitted_when_every_condition_holds(bundle) -> None:
    case = make_case(patient_reference="SYN-PT-1", requested_service="scheduling")
    assert may_route_provisionally(case, 0.95, bundle).permitted


def test_provisional_refused_below_the_confidence_threshold(bundle) -> None:
    case = make_case(patient_reference="SYN-PT-1", requested_service="scheduling")
    decision = may_route_provisionally(case, 0.50, bundle)
    assert not decision.permitted and "below the P1 threshold" in decision.refusal_reason


def test_provisional_refused_when_a_mandatory_field_is_absent(bundle) -> None:
    case = make_case(patient_reference=None, requested_service="scheduling")
    assert not may_route_provisionally(case, 0.99, bundle).permitted


def test_provisional_refused_while_a_critical_signal_is_active(bundle) -> None:
    """FR-011 — high confidence never overrides an active signal."""
    case = make_case(patient_reference="SYN-PT-1", requested_service="scheduling")
    case.critical_signal_active = True
    decision = may_route_provisionally(case, 0.99, bundle)
    assert not decision.permitted and "critical-condition signal is active" in decision.refusal_reason


def test_provisional_refused_while_a_clearance_gate_is_pending(bundle) -> None:
    case = make_case(patient_reference="SYN-PT-1", requested_service="scheduling")
    assert not may_route_provisionally(case, 0.99, bundle, clearance_pending=True).permitted


def test_provisional_refused_when_the_register_is_unresolved(bundle) -> None:
    """FR-057 — the blocker must actually stop progression."""
    case = make_case(patient_reference="SYN-PT-1", requested_service="scheduling")
    assert not may_route_provisionally(case, 0.99, bundle, register_unresolved=True).permitted


# ===========================================================================
# clearance — FR-033, FR-034
# ===========================================================================


def gate(kind: str, who: str) -> ClearanceGate:
    role = Role.CLINICAL_AUTHORITY if kind == "clinical" else Role.FINANCE_CLEARANCE_APPROVER
    return ClearanceGate(kind=kind, role=role, recorded_by=who, recorded_at=NOW)


def test_release_refused_until_both_gates_recorded() -> None:
    case = make_case()
    case.clinical_clearance = gate("clinical", "dr-a")
    result = evaluate_release_eligibility(case)
    assert not result.eligible and "financial clearance" in result.blocker


def test_release_eligible_with_both_gates_in_either_order() -> None:
    for first, second in (("clinical", "financial"), ("financial", "clinical")):
        case = make_case()
        setattr(case, f"{first}_clearance", gate(first, "p1"))
        setattr(case, f"{second}_clearance", gate(second, "p2"))
        assert evaluate_release_eligibility(case).eligible


def test_a_clearance_is_never_refused_because_the_other_is_outstanding() -> None:
    """FR-033 — order-independence, the AS-11 superset."""
    case = make_case()
    permitted, reason = may_record_clearance(case, "financial")
    assert permitted and reason is None


# ===========================================================================
# SLA — FR-022, FR-023, P4, P5
# ===========================================================================


def test_sla_resolves_to_the_default_and_records_where_from(bundle) -> None:
    resolved = resolve_sla(bundle, UrgencyClass.URGENT)
    assert resolved.seconds == 14400
    assert resolved.resolved_from == "default:urgent"


def test_business_days_convert_to_seconds(bundle) -> None:
    assert resolve_sla(bundle, UrgencyClass.ROUTINE).seconds == 2 * 8 * 3600


def test_early_warning_fires_at_eighty_percent(bundle) -> None:
    applied = resolve_sla(bundle, UrgencyClass.URGENT)
    status = evaluate_sla(bundle, applied, int(applied.seconds * 0.80))
    assert status.early_warning and not status.breached


def test_breach_never_authorises_auto_advance(bundle) -> None:
    """P5 — no elapsed time authorises advancing an item."""
    applied = resolve_sla(bundle, UrgencyClass.URGENT)
    status = evaluate_sla(bundle, applied, applied.seconds * 10)
    assert status.breached and status.auto_advance_permitted is False


def test_urgency_classification_is_administrative_only() -> None:
    assert urgency_from_text("STAT / Immediate") is UrgencyClass.URGENT
    assert urgency_from_text(None) is UrgencyClass.ROUTINE


# ===========================================================================
# plausibility — FR-006
# ===========================================================================


def test_stat_on_a_routine_service_is_surfaced_as_a_contradiction() -> None:
    """CASE-013 — neither silently accepted nor silently downgraded."""
    case = make_case(urgency="STAT / Immediate",
                     requested_service="Routine annual wellness visit scheduling")
    found = find_contradictions(case)
    assert len(found) == 1
    assert set(found[0].fields) == {"urgency", "requested_service"}


def test_urgent_on_a_time_sensitive_service_is_not_a_contradiction() -> None:
    case = make_case(urgency="Urgent", requested_service="Urgent imaging review scheduling")
    assert find_contradictions(case) == []
