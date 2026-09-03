"""Append-only, hash-chained event store — the system of record.

FR-042, FR-043, FR-045, FR-047, F20 (never-cut). D14: all read models are
projections rebuilt by replay, so there is no second source of truth to drift.

Every payload passes through the masking filter on the way in (D15). Masking is
a property of the write boundary, not of the reader.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from .masking import mask_mapping

GENESIS = "0" * 64


class AuditIntegrityError(RuntimeError):
    """Raised when the hash chain does not verify. Tamper evidence, always fatal."""


@dataclass(frozen=True)
class AuditEvent:
    seq: int
    case_id: str | None
    event_type: str
    actor: str
    timestamp: str
    policy_version: str | None
    payload: dict[str, Any]
    prev_hash: str
    hash: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "seq": self.seq,
                "case_id": self.case_id,
                "event_type": self.event_type,
                "actor": self.actor,
                "timestamp": self.timestamp,
                "policy_version": self.policy_version,
                "payload": self.payload,
                "prev_hash": self.prev_hash,
                "hash": self.hash,
            },
            sort_keys=True,
        )


def _digest(seq: int, case_id: str | None, event_type: str, actor: str, timestamp: str,
            policy_version: str | None, payload: dict[str, Any], prev_hash: str) -> str:
    body = json.dumps(
        {
            "seq": seq,
            "case_id": case_id,
            "event_type": event_type,
            "actor": actor,
            "timestamp": timestamp,
            "policy_version": policy_version,
            "payload": payload,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


@dataclass
class EventStore:
    """Append-only. There is no update and no delete — P8 forbids purge before
    sign-off, and FR-042 requires an ordered history."""

    path: Path | None = None
    _events: list[AuditEvent] = field(default_factory=list)

    def append(
        self,
        *,
        event_type: str,
        actor: str,
        timestamp: str,
        case_id: str | None = None,
        policy_version: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditEvent:
        masked = mask_mapping(payload or {})
        seq = len(self._events) + 1
        prev_hash = self._events[-1].hash if self._events else GENESIS
        digest = _digest(seq, case_id, event_type, actor, timestamp, policy_version, masked, prev_hash)
        event = AuditEvent(
            seq=seq,
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            timestamp=timestamp,
            policy_version=policy_version,
            payload=masked,
            prev_hash=prev_hash,
            hash=digest,
        )
        self._events.append(event)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(event.to_json() + "\n")
        return event

    def __iter__(self) -> Iterator[AuditEvent]:
        return iter(self._events)

    def __len__(self) -> int:
        return len(self._events)

    def for_case(self, case_id: str) -> list[AuditEvent]:
        return [e for e in self._events if e.case_id == case_id]

    def verify_chain(self) -> None:
        prev = GENESIS
        for index, event in enumerate(self._events, start=1):
            if event.seq != index:
                raise AuditIntegrityError(f"sequence gap at {event.seq}: expected {index}")
            if event.prev_hash != prev:
                raise AuditIntegrityError(f"chain break at seq {event.seq}")
            expected = _digest(
                event.seq, event.case_id, event.event_type, event.actor, event.timestamp,
                event.policy_version, event.payload, event.prev_hash,
            )
            if expected != event.hash:
                raise AuditIntegrityError(f"payload tampered at seq {event.seq}")
            prev = event.hash
