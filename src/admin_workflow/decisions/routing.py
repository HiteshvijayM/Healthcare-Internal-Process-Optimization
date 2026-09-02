"""Routing — FR-017, FR-018, FR-045.

DETERMINISTIC. This module must not import ``extraction`` or ``drafting``; the
import boundary is checked by a lint rule and by a contract test (T023). That
boundary is the single mechanism protecting P7 determinism and FR-017
inspectability at the same time.
"""

from __future__ import annotations

from typing import Any

from ..domain.models import Case, Queue, RoutingDecision, RuleEvaluation
from ..policy.bundle import PolicyBundle
from .grammar import evaluate


def build_context(case: Case) -> dict[str, Any]:
    """Flatten the case record into the context the rules read.

    Only PRESENT values are exposed. A missing or disputed value must not be able
    to satisfy a routing rule (FR-007).
    """
    ctx: dict[str, Any] = {}
    for name, fv in case.record.fields.items():
        ctx[name] = fv.value if fv.is_usable() else None
    ctx.setdefault("coverage_status", ctx.get("coverage_status"))
    ctx["requester"] = case.record.value_of("requester")
    return ctx


def decide_route(case: Case, bundle: PolicyBundle) -> RoutingDecision:
    """Evaluate every rule in order; first match wins (RC-1).

    The trace records **every** rule evaluated with its boolean result, not only
    the one that fired (RC-4) — otherwise a reviewer cannot see what was
    considered and rejected.
    """
    ctx = build_context(case)
    trace: list[RuleEvaluation] = []
    fired: dict[str, Any] | None = None

    for rule in bundle.routing_rules["rules"]:
        result = evaluate(rule["when"], ctx)
        trace.append(RuleEvaluation(rule_id=rule["id"], description=rule["description"], result=result))
        if result and fired is None:
            fired = rule

    if fired is None:  # pragma: no cover — RC-2 makes this unreachable
        raise RuntimeError("RC-2 violated: no rule matched and no terminal rule exists")

    reason = fired["reason_template"].format(
        requested_service=ctx.get("requested_service") or "the requested service",
        reason_detail=_reason_detail(ctx),
    )
    return RoutingDecision(
        queue=Queue(fired["queue"]),
        reason=reason,
        rule_id=fired["id"],
        confidence=float(fired["confidence"]),
        trace=tuple(trace),
        provisional=False,
        policy_version=bundle.bundle_id,
    )


def _reason_detail(ctx: dict[str, Any]) -> str:
    if str(ctx.get("coverage_status") or "").lower() == "settled":
        return "coverage is already settled, so what remains is a financial matter"
    return f"the request is for {ctx.get('requested_service') or 'a financial matter'}"
