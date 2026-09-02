"""Audit replay — projections and compliance reconstruction.

FR-043: a compliance reviewer must be able to reconstruct any sampled completed
case end to end from the recorded history alone. D14: all read models are
projections rebuilt by replay, so there is no second source of truth to drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .store import AuditEvent, EventStore

#: The questions FR-043 and constitution 4 require an audit to answer.
RECONSTRUCTION_DIMENSIONS = ("who", "what", "when", "why")


@dataclass
class CaseProjection:
    case_id: str
    events: list[AuditEvent] = field(default_factory=list)
    arrived_at: str | None = None
    stage: str | None = None
    queue: str | None = None
    approvals: list[dict[str, Any]] = field(default_factory=list)
    refusals: list[dict[str, Any]] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    policy_versions: set[str] = field(default_factory=set)

    def timeline(self) -> list[str]:
        return [f"{e.timestamp}  {e.event_type}  by {e.actor}" for e in self.events]

    def is_reconstructable(self) -> bool:
        """Every dimension answerable from the record alone."""
        if not self.events or self.arrived_at is None:
            return False
        who = all(e.actor for e in self.events)
        what = all(e.event_type for e in self.events)
        when = all(e.timestamp for e in self.events)
        # "why" — every decision event carries the policy version in force,
        # so the rule that produced it is recoverable (FR-045).
        why = all(
            e.policy_version
            for e in self.events
            if e.event_type.startswith(("routing.", "approval.", "effect.", "escalation."))
        )
        return who and what and when and why


def project_case(store: EventStore, case_id: str) -> CaseProjection:
    projection = CaseProjection(case_id=case_id)
    for event in store.for_case(case_id):
        projection.events.append(event)
        if event.policy_version:
            projection.policy_versions.add(event.policy_version)
        if event.event_type == "case.registered":
            projection.arrived_at = event.timestamp
            projection.stage = "registered"
        elif event.event_type == "routing.decided":
            projection.queue = event.payload.get("queue")
            projection.stage = "routed"
        elif event.event_type == "approval.recorded":
            projection.approvals.append(event.payload)
        elif event.event_type in ("safety.refused", "effect.refused"):
            projection.refusals.append(event.payload)
        elif event.event_type.endswith(".blocked"):
            reason = event.payload.get("reason")
            if reason:
                projection.blockers.append(reason)
        elif event.event_type == "case.closed":
            projection.stage = "closed"
    return projection


def reconstruct_all(store: EventStore) -> dict[str, CaseProjection]:
    case_ids = {e.case_id for e in store if e.case_id}
    return {cid: project_case(store, cid) for cid in sorted(case_ids)}
