"""Harness tier — Passes 0 through 6 of docs/multipass-validation-harness.md.

These do not merely assert; they **compute** a pass score, because a pass verdict
that is asserted rather than measured is not evidence.

Where a precondition is missing the pass is recorded **Blocked**, never Failed
and never Passed — harness 4: "a Blocked run is also not a Pass."
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from admin_workflow.approvals.ledger import DesignationSet
from admin_workflow.audit.masking import scan_for_unmasked
from admin_workflow.audit.replay import project_case
from admin_workflow.decisions import critical_signal as cs
from admin_workflow.decisions.escalation_outcome import GovernanceBlocker, resolve_escalation_outcome
from admin_workflow.domain.models import Role
from admin_workflow.eval.runner import build_runtime, run_eval
from admin_workflow.policy.bundle import load_bundle
from admin_workflow.workflow.pipeline import run_intake

from tests.conftest import read_case


@pytest.fixture(scope="module")
def scorecard(repo_root):
    return run_eval(repo_root)


def metric(scorecard, name):
    return next(m for m in scorecard.metrics if m.name == name)


# ===========================================================================
# Pass 0 — Governance Pre-Check (HARD GATE)
# ===========================================================================


def test_pass0_constitution_is_byte_identical_in_both_locations(repo_root: Path) -> None:
    """The Spec Kit copy must not drift from the authoritative Constitution."""
    import hashlib

    a = hashlib.sha256((repo_root / "docs" / "constitution.md").read_bytes()).hexdigest()
    b = hashlib.sha256((repo_root / ".specify" / "memory" / "constitution.md").read_bytes()).hexdigest()
    assert a == b, "the Constitution and its Spec Kit mirror have diverged"


def test_pass0_dataset_is_synthetic_and_carries_provenance(repo_root: Path) -> None:
    key = json.loads((repo_root / "data" / "sample" / "answer-key.json").read_text(encoding="utf-8"))
    assert key["synthetic"] is True
    assert "No real patient data" in key["provenance"]


def test_pass0_no_real_patient_identifiers_in_the_dataset(repo_root: Path) -> None:
    """Constitution 3 — every patient reference uses the reserved synthetic prefix."""
    import re

    for path in (repo_root / "data" / "sample").glob("CASE-*.md"):
        text = path.read_text(encoding="utf-8")
        for reference in re.findall(r"\*\*Patient reference:\*\*\s*(\S+)", text):
            assert reference.startswith("SYN-PT-"), f"{path.name}: {reference}"


def test_pass0_policy_bundle_is_frozen_and_verifies(repo_root: Path) -> None:
    """Harness 4 entry criterion — CA-008-003."""
    bundle = load_bundle(repo_root / "config" / "policy" / "v1", repo_root)
    assert bundle.bundle_id
    assert bundle.frozen_at
    assert bundle.dataset_id == "SYN-CASESET-v1"


def test_pass0_all_four_designations_resolve_for_the_run(bundle) -> None:
    """Harness 4.2 — the run cannot be scored until every designation is named."""
    designations = DesignationSet(
        designated_clinical_recipient="clinical_authority:on-call",
        escalation_dispatch_approver=Role.INTAKE_COORDINATOR,
        escalation_dispatch_alternate=Role.TEAM_LEAD,
        dispatch_approval_deadline_seconds=bundle.dispatch_deadline_seconds,
        on_call_clinical_coverage="roster:default",
    )
    assert designations.absent() == []


def test_pass0_register_version_resolves(bundle) -> None:
    """P11 — an unresolvable register is a stop-run, never an empty register."""
    register = cs.load_register(bundle)
    assert register["register_id"] == "CCR-DEMO-v1"


def test_pass0_agent_holds_no_role_and_no_designation(bundle) -> None:
    constraints = bundle.approver_registry["constraints"]
    assert constraints["agent_may_hold_role"] is False
    assert constraints["agent_may_hold_designation"] is False


def test_pass0_change_is_recorded_in_the_progress_log(repo_root: Path) -> None:
    """Constitution 7 / FR-050 / F24 — the check that caught R1."""
    log = (repo_root / "docs" / "progress-log.md").read_text(encoding="utf-8")
    for change_id in ("CHG-021", "CHG-022", "CHG-023"):
        assert change_id in log, f"{change_id} is not recorded in the progress log"


# ===========================================================================
# Pass 1 — Intake Baseline Completeness
# ===========================================================================


def test_pass1_field_extraction_meets_the_threshold(scorecard) -> None:
    m = metric(scorecard, "field_extraction_accuracy")
    assert m.denominator == 140, "denominator must be 7 graded fields x 20 cases"
    assert m.pct >= 85.0, f"extraction {m.pct:.2f}% ({m.numerator}/{m.denominator}) below 85%"


def test_pass1_every_seeded_omission_is_detected(scorecard) -> None:
    m = metric(scorecard, "seeded_omission_detection")
    assert m.pct == 100.0, f"missed {m.denominator - m.numerator} seeded omissions"


def test_pass1_routing_accuracy_meets_the_threshold(scorecard) -> None:
    m = metric(scorecard, "routing_accuracy")
    assert m.numerator >= 9, f"routing {m.numerator}/{m.denominator}, target >= 9/10"


def test_pass1_first_pass_completeness_meets_the_threshold(scorecard) -> None:
    m = metric(scorecard, "first_pass_completeness")
    assert m.pct >= 90.0


def test_pass1_every_case_produced_a_routing_decision_with_a_trace(scorecard) -> None:
    for case_id, row in scorecard.per_case.items():
        if row["stage"] == "held":
            continue
        assert row["queue"], f"{case_id} produced no routing decision"
        assert row["rule_id"], f"{case_id} produced no firing rule"


# ===========================================================================
# Pass 2 — Intake Broken-Path Robustness
# ===========================================================================


def test_pass2_duplicate_flags_match_the_answer_key(scorecard) -> None:
    m = metric(scorecard, "duplicate_flag_correctness")
    assert m.pct == 100.0


def test_pass2_sc009_is_recorded_blocked_not_passed(scorecard) -> None:
    """Harness 4 — a Blocked run is not a Pass. The two fixtures SC-009 requires
    do not exist in SYN-CASESET-v1, so the criterion is ungradable and must be
    reported as such rather than quietly counted as satisfied."""
    criteria = [b["criterion"] for b in scorecard.blocked]
    assert "SC-009 duplicate detection" in criteria


def test_pass2_unreadable_input_is_registered_rather_than_discarded(runtime) -> None:
    """FR-005."""
    result = run_intake(runtime, case_id="CASE-UNREADABLE",
                        document_text="\ufffd\ufffd\ufffd illegible scan \ufffd\ufffd",
                        arrived_at="2026-07-17T10:00:00")
    assert runtime.store.for_case("CASE-UNREADABLE")[0].event_type == "case.registered"
    assert result.completion_tasks, "an unreadable item must raise blockers, not vanish"


# ===========================================================================
# Pass 3 — Approval and Escalation Reliability
# ===========================================================================


def test_pass3_escalation_outcomes_are_exactly_correct(scorecard) -> None:
    m = metric(scorecard, "escalation_outcome_correctness")
    assert m.pct == 100.0


def test_pass3_no_false_escalations(scorecard) -> None:
    """Escalating on administrative urgency would be the failure here."""
    assert metric(scorecard, "false_escalations").numerator == 0


def test_pass3_governance_outranks_completeness(bundle) -> None:
    """The FR-054 precedence check, scored rather than assumed."""
    from admin_workflow.domain.models import EscalationPacket

    packet = EscalationPacket(case_id="C", patient_reference="P", requester=None,
                              critical_signal_description="d", source_document_reference="s",
                              timestamp="t", designated_clinical_recipient=None)
    outcome = resolve_escalation_outcome(
        packet, bundle,
        DesignationSet(designated_clinical_recipient=None,
                       escalation_dispatch_approver=Role.INTAKE_COORDINATOR,
                       dispatch_approval_deadline_seconds=600,
                       on_call_clinical_coverage="roster"),
        1800,
    )
    assert isinstance(outcome, GovernanceBlocker)


def test_pass3_dispatch_alert_is_non_suppressible(repo_root, bundle) -> None:
    runtime = build_runtime(bundle)
    result = run_intake(runtime, case_id="CASE-008", document_text=read_case(repo_root, "CASE-008"),
                        arrived_at="2026-07-17T07:41:00", source_document_id="CASE-008.md")
    assert result.escalation.suppressible is False


def test_pass3_dispatch_deadline_is_shorter_than_the_applied_sla(bundle) -> None:
    assert bundle.dispatch_deadline_seconds < bundle.sla_table["defaults"]["critical_acknowledgement"]["seconds"]


def test_pass3_ccs003_is_reported_as_uncovered(scorecard) -> None:
    """A safety-bearing register entry with no fixture must be named, not assumed."""
    criteria = [b["criterion"] for b in scorecard.blocked]
    assert "CCS-003 register coverage" in criteria


# ===========================================================================
# Pass 4 — Clearance and Release Gating (HARD GATE)
# ===========================================================================


def test_pass4_no_release_path_exists_without_both_clearance_tokens(repo_root, bundle) -> None:
    from admin_workflow.decisions.clearance import evaluate_release_eligibility
    from admin_workflow.workflow.pipeline import record_clearance

    runtime = build_runtime(bundle)
    result = run_intake(runtime, case_id="CASE-009", document_text=read_case(repo_root, "CASE-009"),
                        arrived_at="2026-07-18T09:00:00")
    case = result.case
    assert not evaluate_release_eligibility(case).eligible
    record_clearance(runtime, case, "clinical", "dr-a", "2026-07-18T10:00:00")
    assert not evaluate_release_eligibility(case).eligible
    record_clearance(runtime, case, "financial", "fin-b", "2026-07-18T11:00:00")
    assert evaluate_release_eligibility(case).eligible


def test_pass4_release_routing_is_itself_a_gated_effect() -> None:
    from admin_workflow.approvals.action_gate import REQUIRED_ROLE

    assert "route_for_release" in REQUIRED_ROLE


# ===========================================================================
# Pass 5 — Safety, Audit, and Governance Enforcement (HARD GATE)
# ===========================================================================


def test_pass5_zero_unapproved_sends(scorecard) -> None:
    """SC-008 — the never-cut guarantee."""
    assert metric(scorecard, "unapproved_sends").numerator == 0


def test_pass5_every_case_is_reconstructable(repo_root, bundle) -> None:
    runtime = build_runtime(bundle)
    for case_id in ("CASE-001", "CASE-008", "CASE-013"):
        run_intake(runtime, case_id=case_id, document_text=read_case(repo_root, case_id),
                   arrived_at="2026-07-17T08:00:00", source_document_id=f"{case_id}.md")
    for case_id in ("CASE-001", "CASE-008", "CASE-013"):
        assert project_case(runtime.store, case_id).is_reconstructable(), case_id


def test_pass5_audit_chain_is_tamper_evident_after_a_full_run(repo_root, bundle) -> None:
    runtime = build_runtime(bundle)
    for path in sorted((repo_root / "data" / "sample").glob("CASE-*.md")):
        run_intake(runtime, case_id=path.stem, document_text=path.read_text(encoding="utf-8"),
                   arrived_at="2026-07-17T08:00:00", source_document_id=path.name)
    runtime.store.verify_chain()
    assert len(runtime.store) > 60


def test_pass5_no_unmasked_identifiers_across_a_full_run(repo_root, bundle) -> None:
    runtime = build_runtime(bundle)
    for path in sorted((repo_root / "data" / "sample").glob("CASE-*.md")):
        run_intake(runtime, case_id=path.stem, document_text=path.read_text(encoding="utf-8"),
                   arrived_at="2026-07-17T08:00:00", source_document_id=path.name)
    serialised = "\n".join(e.to_json() for e in runtime.store)
    assert scan_for_unmasked(serialised) == []


def test_pass5_every_decision_carries_its_policy_version(repo_root, bundle) -> None:
    """FR-045 / F23."""
    runtime = build_runtime(bundle)
    run_intake(runtime, case_id="CASE-008", document_text=read_case(repo_root, "CASE-008"),
               arrived_at="2026-07-17T07:41:00", source_document_id="CASE-008.md")
    decisions = [e for e in runtime.store
                 if e.event_type.startswith(("routing.", "escalation.", "sla.", "provisional."))]
    assert decisions
    assert all(e.policy_version == bundle.bundle_id for e in decisions)


# ===========================================================================
# Pass 6 — Harness Repeatability and Surface Readiness
# ===========================================================================


def test_pass6_reruns_produce_identical_per_case_classifications(repo_root: Path) -> None:
    """P7 — determinism is not negotiable. 100% identical, not 'within tolerance'."""
    first = run_eval(repo_root)
    second = run_eval(repo_root)
    assert first.per_case == second.per_case


def test_pass6_aggregate_scores_are_within_drift_tolerance(repo_root: Path, bundle) -> None:
    first = {m.name: m.pct for m in run_eval(repo_root).metrics}
    second = {m.name: m.pct for m in run_eval(repo_root).metrics}
    tolerance = bundle.p("P7_drift_tolerance")["aggregate_pp"]
    for name, value in first.items():
        assert abs(value - second[name]) <= tolerance


def test_pass6_scorecard_reports_every_denominator(scorecard) -> None:
    """feature.md 7 reporting rule — a percentage without a denominator is not a
    measurement and may not be cited as evidence."""
    for m in scorecard.metrics:
        assert m.denominator > 0, f"{m.name} has no denominator"
        assert "denominator" in m.as_dict()


def test_pass6_surface_commands_are_available() -> None:
    """P9 — one surface, and it is operable."""
    from admin_workflow.surface.cli import main

    assert main(["verify"]) == 0
