"""Policy bundle — load, hash-verify, freeze.

BC-1: verified at load; a hash mismatch is a startup failure, never a warning.
BC-2: ``bundle_id`` is recorded on every routing and approval decision (FR-045).
PC-3: no consumer may hardcode a policy value — all reads go through here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

BUNDLE_FILES = (
    "policy-table.yaml",
    "routing-rules.yaml",
    "approver-registry.yaml",
    "field-owner-map.yaml",
    "sla-table.yaml",
    "critical-signal-register.yaml",
)

EXTERNAL_FILES = ("docs/critical-condition-register.md",)


class BundleIntegrityError(RuntimeError):
    """Raised when the bundle cannot be trusted. Always fatal — never a warning."""


class PolicyViolation(RuntimeError):
    """Raised when the bundle content violates a contract rule at load time."""


def sha256_of(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class PolicyBundle:
    bundle_id: str
    frozen_at: str
    dataset_id: str
    register_version: str
    policy_table: dict[str, Any]
    routing_rules: dict[str, Any]
    approver_registry: dict[str, Any]
    field_owner_map: dict[str, Any]
    sla_table: dict[str, Any]
    critical_signal_register: dict[str, Any]
    root: Path

    # -- policy accessors (PC-3: everything goes through these) -------------

    def p(self, key: str) -> Any:
        try:
            return self.policy_table[key]
        except KeyError as exc:  # pragma: no cover - defensive
            raise PolicyViolation(f"policy {key} absent from the approved policy table") from exc

    def has(self, key: str) -> bool:
        return key in self.policy_table

    @property
    def min_routing_confidence(self) -> float:
        return float(self.p("P1_provisional_routing")["min_confidence"])

    @property
    def provisional_required_fields(self) -> list[str]:
        return list(self.p("P1_provisional_routing")["required_fields"])

    @property
    def duplicate_window_hours(self) -> int:
        return int(self.p("P2_duplicate_detection")["key_match"]["window_hours"])

    @property
    def packet_mandatory_fields(self) -> list[str]:
        return list(self.p("P3_escalation_packet_completeness")["mandatory_fields"])

    @property
    def rework_loop_limit(self) -> int:
        return int(self.p("P6_rework_loop_limit")["max_loops"])

    @property
    def early_warning_pct(self) -> int:
        return int(self.p("P5_sla_alerts")["early_warning_at_pct"])

    @property
    def dispatch_deadline_seconds(self) -> int | None:
        """P10. Returns None when no deadline has been approved — FR-052 requires a
        governance blocker in that case, never a default."""
        if not self.has("P10_dispatch_approval_deadline"):
            return None
        entry = self.p("P10_dispatch_approval_deadline")
        unit = entry["unit"]
        value = int(entry["value"])
        return value * {"seconds": 1, "minutes": 60, "hours": 3600}[unit]

    @property
    def register_id(self) -> str | None:
        if not self.has("P11_critical_signal_register"):
            return None
        return self.p("P11_critical_signal_register")["register_id"]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _verify_hashes(root: Path, lock: dict[str, Any], repo_root: Path) -> None:
    for name, expected in lock["files"].items():
        target = (repo_root / name) if "/" in name else (root / name)
        if not target.exists():
            raise BundleIntegrityError(f"bundle file missing: {name}")
        actual = sha256_of(target)
        if actual != expected:
            raise BundleIntegrityError(
                f"bundle hash mismatch for {name}: locked {expected}, found {actual}. "
                "Refusing to start — BC-1 makes this fatal, never a warning."
            )


def _validate_contract_rules(bundle: PolicyBundle) -> None:
    """Contract rules enforced at load time, so a bad bundle can never run."""
    rules = bundle.routing_rules["rules"]

    # RC-2 — a terminal `always` rule is mandatory, so no case falls off the end.
    if not rules or rules[-1]["when"].strip() != "always":
        raise PolicyViolation("RC-2: routing rules must end with a terminal `when: always` rule")

    # RC-3 — every rule carries a plain-English description.
    for rule in rules:
        if not rule.get("description"):
            raise PolicyViolation(f"RC-3: rule {rule['id']} has no plain-English description")

    # RC-6 — the default rule's confidence must sit below P1, so a fallback can
    # never justify provisional routing.
    if float(rules[-1]["confidence"]) >= bundle.min_routing_confidence:
        raise PolicyViolation(
            "RC-6: the default routing rule's confidence must be below the P1 threshold, "
            "otherwise a fallback match could provisionally route"
        )

    # AC-1 — `agent` may hold no role and no designation.
    constraints = bundle.approver_registry["constraints"]
    if constraints.get("agent_may_hold_role") or constraints.get("agent_may_hold_designation"):
        raise PolicyViolation("AC-1: the agent may hold no approver role and no designation")
    role_ids = {r["id"] for r in bundle.approver_registry["roles"]}
    if "agent" in role_ids or "assistant" in role_ids:
        raise PolicyViolation("AC-1: `agent` is not a valid role id")

    # SC-2 / SC-4 — SLA override floor. An override must be shorter than its
    # default, and a critical-acknowledgement override must stay strictly greater
    # than P10, or P10 becomes unsatisfiable and every escalation in that service
    # line would sit behind a permanent governance blocker.
    defaults = bundle.sla_table["defaults"]
    p10 = bundle.dispatch_deadline_seconds
    for override in bundle.sla_table.get("service_line_overrides") or []:
        urgency = override["urgency_class"]
        seconds = int(override["seconds"])
        default_seconds = defaults.get(urgency, {}).get("seconds")
        if default_seconds is not None and seconds > int(default_seconds):
            if not override.get("compliance_reviewer_approval"):
                raise PolicyViolation(
                    f"SC-2: override for {urgency}/{override['service_line']} is longer than the "
                    "approved default and carries no recorded Compliance Reviewer approval"
                )
        if urgency == "critical_acknowledgement" and p10 is not None and seconds <= p10:
            raise PolicyViolation(
                f"SC-4: critical acknowledgement override for {override['service_line']} "
                f"({seconds}s) is not strictly greater than the P10 dispatch deadline ({p10}s). "
                "P10 would be unsatisfiable and every escalation in that service line would "
                "sit behind a permanent governance blocker."
            )


def load_bundle(root: Path | str, repo_root: Path | str | None = None) -> PolicyBundle:
    root = Path(root)
    repo_root = Path(repo_root) if repo_root else root.parents[2]
    lock_path = root / "bundle.lock.json"
    if not lock_path.exists():
        raise BundleIntegrityError(
            f"bundle.lock.json absent from {root}. The bundle is not frozen, so no harness "
            "pass may be scored against it (harness 4 entry criterion)."
        )
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    _verify_hashes(root, lock, repo_root)

    bundle = PolicyBundle(
        bundle_id=lock["bundle_id"],
        frozen_at=lock["frozen_at"],
        dataset_id=lock["dataset_id"],
        register_version=lock["register_version"],
        policy_table=_load_yaml(root / "policy-table.yaml"),
        routing_rules=_load_yaml(root / "routing-rules.yaml"),
        approver_registry=_load_yaml(root / "approver-registry.yaml"),
        field_owner_map=_load_yaml(root / "field-owner-map.yaml"),
        sla_table=_load_yaml(root / "sla-table.yaml"),
        critical_signal_register=_load_yaml(root / "critical-signal-register.yaml"),
        root=root,
    )
    _validate_contract_rules(bundle)
    return bundle


def freeze_bundle(root: Path | str, repo_root: Path | str, bundle_id: str, frozen_at: str) -> dict[str, Any]:
    """Write bundle.lock.json — CA-008-003, 'freeze the policy version for the run'.

    The dataset ID is read from the answer key rather than hardcoded, so the
    bundle and the dataset cannot silently drift apart. BC-3: any content change
    mints a new bundle_id and requires re-running every dependent harness pass.
    """
    root, repo_root = Path(root), Path(repo_root)
    files = {name: sha256_of(root / name) for name in BUNDLE_FILES}
    for name in EXTERNAL_FILES:
        files[name] = sha256_of(repo_root / name)
    register = _load_yaml(root / "critical-signal-register.yaml")
    answer_key = json.loads(
        (repo_root / "data" / "sample" / "answer-key.json").read_text(encoding="utf-8")
    )
    lock = {
        "bundle_id": bundle_id,
        "frozen_at": frozen_at,
        "dataset_id": answer_key["dataset_id"],
        "register_version": register["register_id"],
        "files": files,
    }
    (root / "bundle.lock.json").write_text(
        json.dumps(lock, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return lock
