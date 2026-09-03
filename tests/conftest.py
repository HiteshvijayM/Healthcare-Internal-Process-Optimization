"""Shared fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from admin_workflow.approvals.action_gate import ActionGate  # noqa: E402
from admin_workflow.approvals.ledger import ApprovalLedger, DesignationSet  # noqa: E402
from admin_workflow.audit.store import EventStore  # noqa: E402
from admin_workflow.domain.models import Role  # noqa: E402
from admin_workflow.extraction.extractor import Extractor  # noqa: E402
from admin_workflow.policy.bundle import load_bundle  # noqa: E402
from admin_workflow.workflow.pipeline import Runtime  # noqa: E402

NOW = "2026-07-17T08:00:00"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def bundle():
    return load_bundle(REPO_ROOT / "config" / "policy" / "v1", REPO_ROOT)


@pytest.fixture
def full_designations(bundle) -> DesignationSet:
    return DesignationSet(
        designated_clinical_recipient="clinical_authority:on-call",
        escalation_dispatch_approver=Role.INTAKE_COORDINATOR,
        escalation_dispatch_alternate=Role.TEAM_LEAD,
        dispatch_approval_deadline_seconds=bundle.dispatch_deadline_seconds,
        on_call_clinical_coverage="roster:default",
    )


@pytest.fixture
def runtime(bundle, full_designations) -> Runtime:
    store = EventStore()
    ledger = ApprovalLedger()
    gate = ActionGate(ledger=ledger, store=store, policy_version=bundle.bundle_id)
    return Runtime(bundle=bundle, store=store, ledger=ledger, gate=gate,
                   designations=full_designations, extractor=Extractor())


@pytest.fixture(scope="session")
def sample_dir(repo_root) -> Path:
    return repo_root / "data" / "sample"


def read_case(repo_root: Path, case_id: str) -> str:
    return (repo_root / "data" / "sample" / f"{case_id}.md").read_text(encoding="utf-8")
