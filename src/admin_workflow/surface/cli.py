"""CLI entry points — freeze the bundle, run the eval, print a scorecard.

The conversational surface (F22, P9) binds to these same operations through the
Copilot SDK. Keeping them behind a plain CLI is what lets the harness score the
system without a model backend, which P7 determinism requires.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from admin_workflow.eval.runner import run_eval  # noqa: E402
from admin_workflow.policy.bundle import freeze_bundle, load_bundle  # noqa: E402


def cmd_freeze(args: argparse.Namespace) -> int:
    root = REPO_ROOT / "config" / "policy" / "v1"
    lock = freeze_bundle(
        root, REPO_ROOT,
        bundle_id=args.bundle_id,
        frozen_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    print(f"Froze {lock['bundle_id']} ({len(lock['files'])} files hashed)")
    print(f"  register: {lock['register_version']}   dataset: {lock['dataset_id']}")
    return 0


def cmd_verify(_args: argparse.Namespace) -> int:
    bundle = load_bundle(REPO_ROOT / "config" / "policy" / "v1", REPO_ROOT)
    print(f"Bundle {bundle.bundle_id} verified — hashes match, contract rules hold.")
    print(f"  P1 confidence   : {bundle.min_routing_confidence}")
    print(f"  P2 window hours : {bundle.duplicate_window_hours}")
    print(f"  P10 deadline    : {bundle.dispatch_deadline_seconds}s")
    print(f"  P11 register    : {bundle.register_id}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    scorecard = run_eval(REPO_ROOT)
    if args.json:
        print(json.dumps(scorecard.as_dict(), indent=2))
        return 0

    print(f"Scorecard — {scorecard.dataset_id} / {scorecard.bundle_id} / {scorecard.register_version}")
    print("-" * 78)
    for metric in scorecard.metrics:
        print(f"  {metric.name:<34} {metric.numerator:>4}/{metric.denominator:<4} "
              f"= {metric.pct:6.2f}%   target {metric.target}")
    print("-" * 78)
    for note in scorecard.notes:
        print(f"  note: {note}")
    for blocked in scorecard.blocked:
        print(f"  BLOCKED: {blocked['criterion']} — {blocked['reason']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="admin-workflow")
    sub = parser.add_subparsers(dest="command", required=True)

    freeze = sub.add_parser("freeze", help="freeze the policy bundle (CA-008-003)")
    freeze.add_argument("--bundle-id", default="POLICY-v1")
    freeze.set_defaults(func=cmd_freeze)

    verify = sub.add_parser("verify", help="verify bundle integrity and contract rules")
    verify.set_defaults(func=cmd_verify)

    ev = sub.add_parser("eval", help="run the evaluation harness (F21)")
    ev.add_argument("--json", action="store_true")
    ev.set_defaults(func=cmd_eval)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
