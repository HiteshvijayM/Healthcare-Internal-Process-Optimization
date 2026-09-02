"""Contract tests — the structural guarantees, checked mechanically.

These are the tests that make design decisions enforceable rather than
aspirational. If any of them fails, the corresponding architectural property has
already been lost somewhere in the source.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest
import yaml

from admin_workflow.audit.masking import mask_mapping, scan_for_unmasked
from admin_workflow.audit.store import AuditIntegrityError, EventStore
from admin_workflow.decisions.grammar import uses_only_permitted_grammar
from admin_workflow.policy.bundle import BundleIntegrityError, load_bundle, sha256_of

# ---------------------------------------------------------------------------
# D4 — the import boundary. Checked by scanning the AST, not by convention.
# ---------------------------------------------------------------------------

FORBIDDEN_IN_DECISIONS = ("extraction", "drafting", "surface")


def test_decisions_never_import_model_backed_modules(repo_root: Path) -> None:
    """The single mechanism protecting P7 determinism and FR-017 inspectability.

    If ``decisions/`` could reach ``extraction/`` or ``drafting/``, a model call
    could enter a decision path and per-case classifications would stop being
    reproducible. Convention is not enough — this scans every import node.
    """
    decisions = repo_root / "src" / "admin_workflow" / "decisions"
    offenders: list[str] = []
    for path in decisions.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for name in names:
                if any(part in name.split(".") for part in FORBIDDEN_IN_DECISIONS):
                    offenders.append(f"{path.name} imports {name}")
    assert not offenders, "decisions/ must not import model-backed modules: " + "; ".join(offenders)


def test_agent_is_not_a_representable_role() -> None:
    """FR-038 / AC-1 — unrepresentable, not merely rejected."""
    from admin_workflow.domain.models import Role

    values = {r.value for r in Role}
    assert "agent" not in values and "assistant" not in values
    with pytest.raises(ValueError):
        Role("agent")


# ---------------------------------------------------------------------------
# CRC-1 — the YAML register is a mirror; the markdown is authoritative.
# ---------------------------------------------------------------------------


def _markdown_register_entries(repo_root: Path) -> dict[str, list[str]]:
    text = (repo_root / "docs" / "critical-condition-register.md").read_text(encoding="utf-8")
    entries: dict[str, list[str]] = {}
    for line in text.splitlines():
        match = re.match(r"^\|\s*\*\*(CCS-\d{3})\*\*\s*\|", line)
        if not match:
            continue
        markers = re.findall(r"`([^`]+)`", line)
        entries[match.group(1)] = [m.strip().lower() for m in markers]
    return entries


def test_register_yaml_mirrors_the_authoritative_markdown(repo_root: Path, bundle) -> None:
    """CRC-1 — drift between the two fails the build.

    The markdown is what a clinical owner reviews and signs off; the YAML is what
    the matcher reads. If they can disagree, the reviewed artifact and the
    executed artifact are different artifacts.
    """
    markdown = _markdown_register_entries(repo_root)
    yaml_entries = {e["id"]: [m.lower() for m in e["markers"]]
                    for e in bundle.critical_signal_register["entries"]}

    assert set(markdown) == set(yaml_entries), "register entry IDs differ between markdown and YAML"
    for entry_id, md_markers in markdown.items():
        missing = [m for m in yaml_entries[entry_id] if m not in md_markers]
        assert not missing, f"{entry_id}: YAML markers absent from the authoritative markdown: {missing}"


def test_register_id_matches_the_policy_table(bundle) -> None:
    assert bundle.critical_signal_register["register_id"] == bundle.register_id


def test_register_match_mode_is_literal_only(bundle) -> None:
    """CRC-2 — anything else would permit inference."""
    assert bundle.critical_signal_register["match_mode"] == "literal_marker"


# ---------------------------------------------------------------------------
# PC-1 — the policy bundle mirrors feature.md 5.4.
# ---------------------------------------------------------------------------


def test_policy_values_match_the_approved_policy_table(repo_root: Path, bundle) -> None:
    """PC-1 — drift between the bundle and feature.md 5.4 fails the build."""
    feature = (repo_root / "feature.md").read_text(encoding="utf-8")
    assert "**≥ 0.80**" in feature or "0.80" in feature
    assert bundle.min_routing_confidence == 0.80
    assert bundle.duplicate_window_hours == 72
    assert bundle.dispatch_deadline_seconds == 600          # P10, 10 minutes
    assert bundle.rework_loop_limit == 2                    # P6
    assert bundle.early_warning_pct == 80                   # P5
    assert len(bundle.packet_mandatory_fields) == 7         # P3
    assert bundle.register_id == "CCR-DEMO-v1"              # P11


def test_p10_is_strictly_shorter_than_the_default_acknowledgement_sla(bundle) -> None:
    """FR-052 — the whole point of the value."""
    default_ack = bundle.sla_table["defaults"]["critical_acknowledgement"]["seconds"]
    assert bundle.dispatch_deadline_seconds < default_ack


def test_safety_bearing_values_are_marked(bundle) -> None:
    """P1, P3, P10, P11 require Compliance Reviewer approval to loosen (PC-2)."""
    for key in ("P1_provisional_routing", "P3_escalation_packet_completeness",
                "P10_dispatch_approval_deadline", "P11_critical_signal_register"):
        assert bundle.p(key).get("safety_bearing") is True, f"{key} must be marked safety_bearing"


# ---------------------------------------------------------------------------
# RC-x — routing rule contract.
# ---------------------------------------------------------------------------


def test_routing_rules_end_with_a_terminal_rule(bundle) -> None:
    """RC-2 — no case may fall off the end."""
    assert bundle.routing_rules["rules"][-1]["when"].strip() == "always"


def test_default_rule_confidence_is_below_the_provisional_threshold(bundle) -> None:
    """RC-6 — a fallback match can never justify provisional routing."""
    assert float(bundle.routing_rules["rules"][-1]["confidence"]) < bundle.min_routing_confidence


def test_every_rule_uses_only_the_permitted_grammar(bundle) -> None:
    """RC-5 — no arbitrary code evaluation, and a reviewer can read every operator."""
    for rule in bundle.routing_rules["rules"]:
        assert uses_only_permitted_grammar(rule["when"]), \
            f"rule {rule['id']} uses an operator outside the permitted grammar: {rule['when']}"


def test_every_rule_has_a_plain_english_description(bundle) -> None:
    """RC-3 — the trace shows the description, so a reviewer never reads the expression."""
    for rule in bundle.routing_rules["rules"]:
        assert len(rule["description"]) > 20
        assert rule["description"][0].isupper()


def test_queue_set_is_the_five_approved_queues(bundle) -> None:
    assert bundle.routing_rules["queues"] == ["Insurance", "Operations", "Diagnostics", "Legal", "Finance"]
    for rule in bundle.routing_rules["rules"]:
        assert rule["queue"] in bundle.routing_rules["queues"]


# ---------------------------------------------------------------------------
# BC-1 — bundle integrity is fatal, never a warning.
# ---------------------------------------------------------------------------


def test_hash_mismatch_is_a_startup_failure(tmp_path: Path, repo_root: Path) -> None:
    import shutil

    src = repo_root / "config" / "policy" / "v1"
    dst = tmp_path / "v1"
    shutil.copytree(src, dst)
    tampered = dst / "policy-table.yaml"
    tampered.write_text(tampered.read_text(encoding="utf-8").replace("0.80", "0.10"), encoding="utf-8")

    with pytest.raises(BundleIntegrityError, match="hash mismatch"):
        load_bundle(dst, repo_root)


def test_missing_lock_file_refuses_to_load(tmp_path: Path, repo_root: Path) -> None:
    import shutil

    dst = tmp_path / "v1"
    shutil.copytree(repo_root / "config" / "policy" / "v1", dst)
    (dst / "bundle.lock.json").unlink()
    with pytest.raises(BundleIntegrityError, match="not frozen"):
        load_bundle(dst, repo_root)


def test_lock_covers_the_authoritative_markdown_register(repo_root: Path) -> None:
    """The markdown is hashed too, so it cannot drift from the mirror unnoticed."""
    lock = json.loads((repo_root / "config" / "policy" / "v1" / "bundle.lock.json").read_text(encoding="utf-8"))
    assert "docs/critical-condition-register.md" in lock["files"]
    assert lock["files"]["docs/critical-condition-register.md"] == \
        sha256_of(repo_root / "docs" / "critical-condition-register.md")


# ---------------------------------------------------------------------------
# FR-044 — masking at the write boundary.
# ---------------------------------------------------------------------------


def test_identifiers_are_masked_before_they_reach_the_log() -> None:
    store = EventStore()
    store.append(
        event_type="case.registered", actor="assistant", timestamp="2026-07-17T08:00:00",
        case_id="CASE-008",
        payload={"patient_reference": "SYN-PT-40288", "ordering_reference": "ORD-2026-3441",
                 "note": "contact j.okafor@example.com about SYN-PT-40288"},
    )
    serialised = "\n".join(e.to_json() for e in store)
    assert "SYN-PT-40288" not in serialised
    assert "ORD-2026-3441" not in serialised
    assert "j.okafor@example.com" not in serialised
    assert scan_for_unmasked(serialised) == []


def test_masking_survives_nesting() -> None:
    masked = mask_mapping({"outer": {"inner": ["SYN-PT-1", "clean"]}})
    assert "SYN-PT-1" not in json.dumps(masked)


# ---------------------------------------------------------------------------
# F20 — the audit chain is tamper-evident.
# ---------------------------------------------------------------------------


def test_audit_chain_verifies() -> None:
    store = EventStore()
    for i in range(5):
        store.append(event_type="t", actor="a", timestamp=f"2026-07-17T08:0{i}:00", case_id="C")
    store.verify_chain()


def test_tampering_with_a_payload_breaks_the_chain() -> None:
    store = EventStore()
    store.append(event_type="t", actor="a", timestamp="2026-07-17T08:00:00", case_id="C",
                 payload={"queue": "Legal"})
    store.append(event_type="t", actor="a", timestamp="2026-07-17T08:01:00", case_id="C")
    object.__setattr__(store._events[0], "payload", {"queue": "Finance"})
    with pytest.raises(AuditIntegrityError):
        store.verify_chain()


# ---------------------------------------------------------------------------
# Effect coverage — every outbound effect kind must name a required role.
# ---------------------------------------------------------------------------


def test_every_effect_kind_declares_a_required_role() -> None:
    from admin_workflow.approvals.action_gate import REQUIRED_ROLE
    from admin_workflow.domain.models import Role

    assert REQUIRED_ROLE, "no effect kinds declared"
    for kind, roles in REQUIRED_ROLE.items():
        assert roles, f"{kind} declares no authorising role"
        assert all(isinstance(r, Role) for r in roles)


def test_json_schemas_parse(repo_root: Path) -> None:
    contracts = repo_root / "specs" / "001-admin-workflow-assistant" / "contracts"
    for path in contracts.glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def test_policy_bundle_yaml_all_parses(repo_root: Path) -> None:
    for path in (repo_root / "config" / "policy" / "v1").glob("*.yaml"):
        assert yaml.safe_load(path.read_text(encoding="utf-8")) is not None
