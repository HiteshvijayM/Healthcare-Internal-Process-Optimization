"""Scenario tests — one per acceptance scenario AS-1..AS-14, plus the spec's edge cases.

Named for the scenarios so a failure points straight at the requirement it broke.
These run the real pipeline over the real fixtures; nothing is stubbed.
"""

from __future__ import annotations

import pytest

from admin_workflow.approvals.action_gate import UnapprovedActionError
from admin_workflow.approvals.ledger import SeparationOfDutyError, UnauthorizedRole
from admin_workflow.audit.replay import project_case
from admin_workflow.decisions import critical_signal as cs
from admin_workflow.decisions.clearance import evaluate_release_eligibility
from admin_workflow.decisions.escalation_outcome import DispatchApproval
from admin_workflow.domain.models import FieldSource, Resolution, Role, Stage
from admin_workflow.safety.guard import ClinicalBoundaryViolation, assert_outbound_clean, check_inbound
from admin_workflow.workflow.pipeline import record_clearance, run_intake
from tests.conftest import read_case

NOW = "2026-07-17T09:00:00"


def intake(runtime, repo_root, case_id: str, **kwargs):
    doc = read_case(repo_root, case_id)
    import re
    match = re.search(r"^\*\*Received:\*\*\s*(.+?)\s*$", doc, re.M)
    arrived = match.group(1).strip().replace(" ", "T") if match else NOW
    return run_intake(runtime, case_id=case_id, document_text=doc, arrived_at=arrived,
                      source_document_id=f"{case_id}.md", **kwargs)


# ===========================================================================
# AS-1 — Complete request registered; key details extracted accurately
# ===========================================================================


def test_as1_complete_request_is_registered_and_extracted(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-001")
    case = result.case
    assert case.case_id == "CASE-001"
    assert case.arrived_at
    assert case.record.value_of("patient_reference") == "SYN-PT-40182"
    assert case.record.value_of("requested_service")
    assert [e.event_type for e in runtime.store.for_case("CASE-001")][0] == "case.registered"


def test_as1_extraction_never_invents_a_value(runtime, repo_root) -> None:
    """FR-002 — a field absent from the source is marked missing, not guessed."""
    result = intake(runtime, repo_root, "CASE-002")
    payer = result.case.record.get("payer_plan")
    assert payer.resolution is Resolution.MISSING
    assert payer.value is None


# ===========================================================================
# AS-2 — Missing details listed and routed to completion tasks
# ===========================================================================


def test_as2_unresolved_fields_become_owned_completion_tasks(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-012")
    assert result.completion_tasks
    for task in result.completion_tasks:
        assert isinstance(task.owner, Role)   # FC-1 — exactly one accountable owner


def test_as2_backfill_precedes_asking_a_human(runtime, repo_root) -> None:
    """AS-2 / FR-003 — derive from records before requesting new input.

    CASE-021 arrives with no ordering reference. CASE-009 carries one for the
    same patient, so the value is derivable and must be derived rather than
    chased. Asking a human for something already on file is exactly the
    re-typing this system exists to remove.
    """
    intake(runtime, repo_root, "CASE-009")
    result = intake(runtime, repo_root, "CASE-021")
    assert result.backfilled, "a derivable value was not derived"
    names = {c.field_name for c in result.backfilled}
    assert "ordering_reference" in names
    assert "ordering_reference" not in {t.field_name for t in result.completion_tasks}


def test_as2_backfilled_value_is_distinguishable_from_a_submitted_one(runtime, repo_root) -> None:
    """FR-004 — provenance is what separates a derived value from an invented one."""
    intake(runtime, repo_root, "CASE-009")
    result = intake(runtime, repo_root, "CASE-021")
    fv = result.case.record.get("ordering_reference")
    assert fv.source is FieldSource.BACKFILLED
    assert fv.derived_from == "CASE-009"
    kinds = [e.event_type for e in runtime.store.for_case("CASE-021")]
    assert "case.backfilled" in kinds


def test_as2_extraction_snapshot_still_shows_the_field_as_absent(runtime, repo_root) -> None:
    """A backfilled value was still missing from the document. Grading extraction
    against the post-backfill record would overstate what was actually read."""
    intake(runtime, repo_root, "CASE-009")
    result = intake(runtime, repo_root, "CASE-021")
    assert result.extracted.get("ordering_reference").resolution is Resolution.MISSING
    assert result.case.record.get("ordering_reference").resolution is Resolution.PRESENT


def test_as2_not_applicable_never_raises_a_completion_task(runtime, repo_root) -> None:
    """FR-009 — the false-positive trap on CASE-012, CASE-014 and CASE-020."""
    for case_id in ("CASE-012", "CASE-014", "CASE-020"):
        result = intake(runtime, repo_root, case_id)
        payer = result.case.record.get("payer_plan")
        assert payer.resolution is Resolution.NOT_APPLICABLE, case_id
        assert "payer_plan" not in [t.field_name for t in result.completion_tasks], case_id


# ===========================================================================
# AS-3 — Provisional routing or hold; targeted requests prepared
# ===========================================================================


def test_as3_incomplete_case_gets_a_targeted_request_for_exactly_what_is_missing(runtime, repo_root) -> None:
    """FR-016 — asks for what is missing, never for what we already hold."""
    result = intake(runtime, repo_root, "CASE-012")
    request = next(d for d in result.drafts if d.kind == "information_request")
    assert "urgency" in request.authoritative
    assert "patient reference" not in request.authoritative  # already held


def test_as3_provisional_flag_names_what_is_outstanding(runtime, repo_root) -> None:
    """FR-012."""
    result = intake(runtime, repo_root, "CASE-012")
    if result.case.provisional:
        assert result.case.provisional_outstanding


# ===========================================================================
# AS-4 — Routed with a one-line reason and a visible rule trace
# ===========================================================================


def test_as4_routing_carries_a_reason_a_trace_and_a_policy_version(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-020")
    decision = result.routing
    assert decision.queue.value == "Legal"
    assert "\n" not in decision.reason
    assert len(decision.trace) == len(runtime.bundle.routing_rules["rules"])
    assert decision.policy_version == runtime.bundle.bundle_id


def test_as4_misroute_traps_are_not_taken(runtime, repo_root) -> None:
    """CASE-006 reads like Insurance but coverage is settled; CASE-020 has
    'Insurance' in the requester's name but is a Legal records matter."""
    assert intake(runtime, repo_root, "CASE-006").routing.queue.value == "Finance"
    assert intake(runtime, repo_root, "CASE-020").routing.queue.value == "Legal"


# ===========================================================================
# AS-5 / AS-6 — Human control over every output
# ===========================================================================


def test_as5_edited_version_is_the_authoritative_one(runtime, repo_root) -> None:
    """FR-032."""
    from admin_workflow.domain.models import DraftArtifact

    draft = DraftArtifact(kind="handoff_summary", assistant_version="assistant text")
    edited = DraftArtifact(kind="handoff_summary", assistant_version="assistant text",
                           human_version="reviewer text")
    assert draft.authoritative == "assistant text"
    assert edited.authoritative == "reviewer text"


def test_as6_nothing_is_sent_without_a_recorded_approval(runtime, repo_root) -> None:
    """FR-030 / SC-008 — the single most important test in the suite."""
    result = intake(runtime, repo_root, "CASE-001")
    effect = result.pending_effects[0]
    with pytest.raises(UnapprovedActionError, match="no recorded human approval"):
        runtime.gate.execute(effect, now=NOW)
    assert runtime.gate.executed_count() == 0


def test_as6_refusal_is_recorded_in_the_audit_trail(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-001")
    with pytest.raises(UnapprovedActionError):
        runtime.gate.execute(result.pending_effects[0], now=NOW)
    kinds = [e.event_type for e in runtime.store.for_case("CASE-001")]
    assert "effect.refused" in kinds


def test_as6_approved_effect_executes_and_is_recorded(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-001")
    effect = result.pending_effects[0]
    runtime.ledger.record(approval_id="a1", effect_id=effect.effect_id,
                          role=Role.OPERATIONS_APPROVER, principal="ops-1",
                          decision="approved", recorded_at=NOW)
    runtime.gate.execute(effect, now=NOW)
    assert runtime.gate.executed_count() == 1


def test_as6_a_rejected_decision_does_not_authorise_the_effect(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-001")
    effect = result.pending_effects[0]
    runtime.ledger.record(approval_id="a1", effect_id=effect.effect_id,
                          role=Role.OPERATIONS_APPROVER, principal="ops-1",
                          decision="rejected", recorded_at=NOW, rationale="not ready")
    with pytest.raises(UnapprovedActionError):
        runtime.gate.execute(effect, now=NOW)


def test_as6_wrong_role_cannot_authorise(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-001")
    effect = result.pending_effects[0]
    runtime.ledger.record(approval_id="a1", effect_id=effect.effect_id,
                          role=Role.TEAM_VALIDATION_LEAD, principal="val-1",
                          decision="approved", recorded_at=NOW)
    with pytest.raises(UnauthorizedRole):
        runtime.gate.execute(effect, now=NOW)


def test_one_approval_authorises_exactly_one_effect(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-001")
    effect = result.pending_effects[0]
    runtime.ledger.record(approval_id="a1", effect_id=effect.effect_id,
                          role=Role.OPERATIONS_APPROVER, principal="ops-1",
                          decision="approved", recorded_at=NOW)
    runtime.gate.execute(effect, now=NOW)
    with pytest.raises(UnapprovedActionError, match="already executed"):
        runtime.gate.execute(effect, now=NOW)


# ===========================================================================
# AS-7 — Duplicate detected and flagged rather than reprocessed
# ===========================================================================


def test_as7_true_duplicates_are_flagged_and_held(runtime, repo_root) -> None:
    intake(runtime, repo_root, "CASE-001")
    result = intake(runtime, repo_root, "CASE-005")
    assert result.case.duplicate_flag is not None
    assert result.case.duplicate_flag.matched_case_id == "CASE-001"
    assert result.case.duplicate_flag.adjudication_state == "held_for_adjudication"
    assert "duplicate_adjudication" in result.awaiting


def test_as7_near_duplicate_guard_is_not_falsely_flagged(runtime, repo_root) -> None:
    """CASE-017 shares a requester with CASE-016 and CASE-018 but has a different
    patient and a different service. Flagging it is a false positive."""
    intake(runtime, repo_root, "CASE-016")
    result = intake(runtime, repo_root, "CASE-017")
    assert result.case.duplicate_flag is None


def test_as7_second_true_duplicate_pair(runtime, repo_root) -> None:
    intake(runtime, repo_root, "CASE-016")
    intake(runtime, repo_root, "CASE-017")
    result = intake(runtime, repo_root, "CASE-018")
    assert result.case.duplicate_flag is not None
    assert result.case.duplicate_flag.matched_case_id == "CASE-016"
    assert result.case.duplicate_flag.matcher.value == "key_match"


def test_as7_post_window_resend_of_a_closed_case_is_caught_by_identity(runtime, repo_root) -> None:
    """CASE-021 — the fixture the key matcher structurally cannot catch.

    An exact re-fax arriving 39 days after CASE-014, against a case that is
    already closed. The 72-hour window has long shut and the key matcher's scope
    excludes closed cases, so only the unbounded identity matcher can see it.
    This is the clinical re-fax on day five that FR-055 exists for.
    """
    intake(runtime, repo_root, "CASE-014")
    runtime.index[-1] = runtime.index[-1].__class__(
        **{**runtime.index[-1].__dict__, "closed": True}
    )
    result = intake(runtime, repo_root, "CASE-021")
    assert result.case.duplicate_flag is not None, "identity matcher failed to fire"
    assert result.case.duplicate_flag.matched_case_id == "CASE-014"
    assert result.case.duplicate_flag.matcher.value == "identity_match"
    assert "duplicate_adjudication" in result.awaiting


def test_as7_same_key_different_content_outside_the_window_is_not_flagged(runtime, repo_root) -> None:
    """CASE-022 — the negative direction of the identity matcher.

    Same sender, same patient reference, same requested service as CASE-016, but
    a genuinely different request under a new order reference, 30 days later.
    Flagging it would mean the normaliser is erasing real content differences —
    exactly what FR-055's 'a difference in any retained content MUST prevent one'
    forbids.
    """
    intake(runtime, repo_root, "CASE-016")
    result = intake(runtime, repo_root, "CASE-022")
    assert result.case.duplicate_flag is None
    assert result.routing.queue.value == "Diagnostics"


# ===========================================================================
# AS-9 — Policy-eligible approvals opened in parallel
# ===========================================================================


def test_as9_multi_step_case_is_coordinated_rather_than_split(runtime, repo_root) -> None:
    """CASE-007 — the parallel approval fan-out case."""
    result = intake(runtime, repo_root, "CASE-007")
    assert result.routing.queue.value == "Operations"
    assert result.routing.rule_id == "R-005"


# ===========================================================================
# AS-10 — Critical signal prepares an escalation, asserts nothing clinical
# ===========================================================================


def test_as10_case008_matches_both_registered_signals_and_yields_one_packet(runtime, repo_root) -> None:
    """CRC-5 — one packet naming every matched ID, not one packet per match."""
    result = intake(runtime, repo_root, "CASE-008")
    assert result.case.critical_signal_active
    assert set(result.case.matched_signal_ids) == {"CCS-001", "CCS-002"}
    assert result.packet is not None
    assert set(result.packet.matched_signal_ids) == {"CCS-001", "CCS-002"}


def test_as10_case008_is_held_for_dispatch_approval(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-008")
    assert isinstance(result.escalation, DispatchApproval)
    assert result.escalation.suppressible is False
    assert result.escalation.approver is Role.INTAKE_COORDINATOR
    assert result.escalation.deadline_seconds == 600
    assert result.packet.dispatch_state == "undispatched"


def test_as10_packet_asserts_nothing_clinical(runtime, repo_root) -> None:
    """FR-027 — Sev 0 if violated."""
    result = intake(runtime, repo_root, "CASE-008")
    description = result.packet.critical_signal_description
    assert_outbound_clean(description)
    for word in ("diagnos", "recommend", "severe", "likely", "triage"):
        assert word not in description.lower()


def test_as10_escalation_needs_an_approval_before_dispatch(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-008")
    dispatch = next(e for e in result.pending_effects if e.kind == "dispatch_escalation_packet")
    with pytest.raises(UnapprovedActionError):
        runtime.gate.execute(dispatch, now=NOW)


def test_as10_case013_carries_urgency_only_and_must_not_escalate(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-013")
    assert not result.case.critical_signal_active
    assert result.signal_statement == cs.NO_MATCH_STATEMENT
    assert result.escalation is None


def test_as10_case020_carries_urgency_only_and_must_not_escalate(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-020")
    assert not result.case.critical_signal_active
    assert result.escalation is None


def test_as10_laboratory_critical_value_matches_ccs003(runtime, repo_root) -> None:
    """CASE-023 — the only fixture that exercises CCS-003.

    Until this existed, a safety-bearing register entry sat unexercised while the
    register read as fully covered.
    """
    result = intake(runtime, repo_root, "CASE-023")
    assert result.case.critical_signal_active
    assert result.case.matched_signal_ids == ["CCS-003"]
    assert isinstance(result.escalation, DispatchApproval)


def test_as10_ccs003_packet_never_reports_a_numeric_result(runtime, repo_root) -> None:
    """The laboratory's marker is the signal. The value behind it is a clinical
    fact the assistant must never read, compare or repeat."""
    result = intake(runtime, repo_root, "CASE-023")
    description = result.packet.critical_signal_description
    assert "critical value" in description.lower()
    assert not any(ch.isdigit() for ch in description.replace("CCS-003", "")), \
        "no numeric result may appear in the packet description"


def test_as10_non_match_never_claims_no_critical_condition(runtime, repo_root) -> None:
    """CRC-3 — Sev 0. The only permitted wording is 'no registered signal matched'."""
    for case_id in ("CASE-001", "CASE-013", "CASE-020"):
        result = intake(runtime, repo_root, case_id)
        assert result.signal_statement == cs.NO_MATCH_STATEMENT
        assert not cs.forbidden_negative_claim(result.signal_statement)


def test_as10_case013_contradiction_is_surfaced_not_resolved(runtime, repo_root) -> None:
    """Neither silently accepted as STAT nor silently downgraded."""
    result = intake(runtime, repo_root, "CASE-013")
    assert result.contradictions
    assert result.case.record.value_of("urgency") == "STAT / Immediate"   # read faithfully
    assert "contradiction_resolution" in result.awaiting


def test_unresolvable_register_holds_the_case_and_refuses_progression(runtime, repo_root) -> None:
    """FR-057 — the blocker must actually stop progression, not merely be raised."""
    runtime.bundle.critical_signal_register["entries"] = []
    try:
        result = intake(runtime, repo_root, "CASE-001")
        assert result.register_unresolved
        assert result.case.stage is Stage.HELD
        assert result.routing is None            # progression genuinely stopped
        assert "governance_resolution" in result.awaiting
    finally:
        runtime.bundle.critical_signal_register.update(
            {"entries": __import__("yaml").safe_load(
                (repo_root / "config" / "policy" / "v1" / "critical-signal-register.yaml")
                .read_text(encoding="utf-8"))["entries"]}
        )


# ===========================================================================
# AS-11 — Clearance gates, then release eligibility
# ===========================================================================


def test_as11_release_requires_both_gates_clinical_first(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-009")
    case = result.case
    record_clearance(runtime, case, "clinical", "dr-a", NOW)
    assert not evaluate_release_eligibility(case).eligible
    record_clearance(runtime, case, "financial", "fin-b", NOW)
    assert evaluate_release_eligibility(case).eligible
    assert case.stage is Stage.RELEASE_ELIGIBLE


def test_as11_financial_first_is_equally_accepted(runtime, repo_root) -> None:
    """FR-033 order-independence — the superset of the source scenario."""
    result = intake(runtime, repo_root, "CASE-010")
    case = result.case
    record_clearance(runtime, case, "financial", "fin-b", NOW)
    assert not evaluate_release_eligibility(case).eligible
    record_clearance(runtime, case, "clinical", "dr-a", NOW)
    assert evaluate_release_eligibility(case).eligible


def test_as11_separation_of_duty_is_enforced_on_write(runtime, repo_root) -> None:
    """FR-034 — refused at the point of recording, not discovered at review."""
    result = intake(runtime, repo_root, "CASE-009")
    case = result.case
    record_clearance(runtime, case, "clinical", "same-person", NOW)
    with pytest.raises(SeparationOfDutyError):
        record_clearance(runtime, case, "financial", "same-person", NOW)


def test_as11_blocker_names_the_outstanding_gate(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-009")
    record_clearance(runtime, result.case, "clinical", "dr-a", NOW)
    assert "financial clearance" in evaluate_release_eligibility(result.case).blocker


# ===========================================================================
# AS-12 — Visibility
# ===========================================================================


def test_as12_stage_owner_queue_and_blockers_are_visible(runtime, repo_root) -> None:
    result = intake(runtime, repo_root, "CASE-012")
    case = result.case
    assert case.stage is not None
    assert case.owner is Role.INTAKE_COORDINATOR
    assert case.queue is not None
    assert result.applied_sla.seconds > 0
    assert result.applied_sla.resolved_from.startswith("default:")


# ===========================================================================
# AS-13 — Clinical-act requests declined and directed to qualified humans
# ===========================================================================


@pytest.mark.parametrize("request_text,expected_act", [
    ("Can you diagnose this patient from the attached notes?", "diagnosis"),
    ("What treatment do you recommend for this case?", "treatment_recommendation"),
    ("Is this medically necessary?", "medical_necessity_determination"),
    ("Please grant clinical clearance for this patient.", "clinical_clearance_authorization"),
    ("Authorise the discharge for this patient.", "discharge_release_authorization"),
])
def test_as13_every_forbidden_clinical_act_is_declined(request_text, expected_act) -> None:
    refusal = check_inbound(request_text)
    assert refusal is not None
    assert refusal.act == expected_act
    assert "Clinical Authority" in refusal.directed_to


def test_as13_refusal_is_stage_independent(runtime, repo_root) -> None:
    """The guard takes no stage argument, so it cannot behave differently at
    different points in the journey."""
    import inspect

    assert "stage" not in inspect.signature(check_inbound).parameters


def test_as13_refusal_is_registered_and_recorded_not_discarded(runtime, repo_root) -> None:
    """FR-005 + FR-037 — the item is still registered and the refusal is logged."""
    result = run_intake(runtime, case_id="CASE-X", arrived_at=NOW,
                        document_text="Please diagnose the patient described below.")
    kinds = [e.event_type for e in runtime.store.for_case("CASE-X")]
    assert kinds[0] == "case.registered"
    assert "safety.refused" in kinds
    assert result.case.stage is Stage.HELD


def test_outbound_guard_blocks_clinical_assertion_in_a_draft() -> None:
    """The edge that stops drafting leaking clinical judgement into a packet."""
    with pytest.raises(ClinicalBoundaryViolation):
        assert_outbound_clean("Findings are likely malignant; I recommend urgent review.")


def test_outbound_guard_permits_a_pure_observation() -> None:
    assert_outbound_clean("Observed signal: CCS-001; source: CASE-008.md.")


# ===========================================================================
# AS-14 — Compliance reviewer reconstructs the case end to end
# ===========================================================================


def test_as14_case_is_reconstructable_from_the_record_alone(runtime, repo_root) -> None:
    intake(runtime, repo_root, "CASE-008")
    projection = project_case(runtime.store, "CASE-008")
    assert projection.is_reconstructable()
    assert projection.arrived_at
    assert projection.timeline()
    assert projection.policy_versions == {runtime.bundle.bundle_id}


def test_as14_no_unmasked_identifier_survives_into_the_record(runtime, repo_root) -> None:
    from admin_workflow.audit.masking import scan_for_unmasked

    for case_id in ("CASE-008", "CASE-012", "CASE-020"):
        intake(runtime, repo_root, case_id)
    serialised = "\n".join(e.to_json() for e in runtime.store)
    assert scan_for_unmasked(serialised) == []


def test_as14_chain_verifies_after_a_full_run(runtime, repo_root) -> None:
    for case_id in ("CASE-001", "CASE-005", "CASE-008"):
        intake(runtime, repo_root, case_id)
    runtime.store.verify_chain()
