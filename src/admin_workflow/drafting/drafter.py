"""Prose generation — F9, FR-016, FR-027.

Model-assisted prose **only**. This module makes no decision: the queue, the
missing-field list, the matched signals and the outcome are all handed to it
already decided by ``decisions/``. That is the D4 split — and it is why this
module may never be imported from ``decisions/``.

Every outbound string passes the safety guard before it is returned, so a
drafting step cannot let clinical assertion into a packet (FR-027).
"""

from __future__ import annotations

from ..domain.models import Case, DraftArtifact, RoutingDecision
from ..safety.guard import assert_outbound_clean


def draft_handoff_summary(case: Case, decision: RoutingDecision) -> DraftArtifact:
    lines = [
        f"Case {case.case_id} — handoff to {decision.queue.value}",
        "",
        f"Requested service: {case.record.value_of('requested_service') or 'not stated'}",
        f"Patient reference: {case.record.value_of('patient_reference') or 'not stated'}",
        f"Requester: {case.record.value_of('requester') or 'not stated'}",
        f"Urgency (administrative): {case.record.value_of('urgency') or 'routine'}",
        "",
        f"Routing reason: {decision.reason}",
    ]
    if case.provisional:
        lines += ["", f"PROVISIONAL — outstanding: {', '.join(case.provisional_outstanding)}"]
    if case.duplicate_flag:
        lines += [
            "",
            f"PROBABLE DUPLICATE of {case.duplicate_flag.matched_case_id} "
            f"(matched on {case.duplicate_flag.matched_on}) — held for adjudication.",
        ]
    text = "\n".join(lines)
    assert_outbound_clean(text)
    return DraftArtifact(kind="handoff_summary", assistant_version=text)


def draft_information_request(case: Case, missing: list[str], held: list[str]) -> DraftArtifact:
    """FR-016 — asks for exactly what is missing, and never for what we already hold."""
    asked = [f for f in missing if f not in held]
    lines = [
        f"Case {case.case_id} — information needed before we can proceed",
        "",
        "We already hold everything else on file. To progress this request we still need:",
    ]
    lines += [f"  - {name.replace('_', ' ')}" for name in asked] or ["  - (nothing outstanding)"]
    text = "\n".join(lines)
    assert_outbound_clean(text)
    return DraftArtifact(kind="information_request", assistant_version=text)


def draft_escalation_packet_body(case: Case, signal_description: str, source_reference: str) -> str:
    """FR-027 — states the observed signal and its source. Asserts, implies and
    ranks nothing clinical."""
    text = "\n".join(
        [
            f"ESCALATION PACKET — case {case.case_id}",
            "",
            f"Observed signal: {signal_description}",
            f"Source: {source_reference}",
            "",
            "This packet reports an administrative observation only. It contains no "
            "clinical assessment, no interpretation of the signal, and no ranking of "
            "urgency or severity. Clinical judgement rests entirely with the recipient.",
        ]
    )
    assert_outbound_clean(text)
    return text
