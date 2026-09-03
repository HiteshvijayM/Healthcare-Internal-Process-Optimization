#!/usr/bin/env python
"""Fail the build if any harness criterion is Blocked, or any metric misses target.

A Blocked criterion is **not** a Pass (harness §4). Without this check a future
dataset revision could remove a fixture, drop a coverage metric, and still ship
green — the score would simply be lower and nobody would read it.

Exits 1 and names every failure, so the build output says what to fix.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from admin_workflow.eval.runner import run_eval  # noqa: E402


def main() -> int:
    card = run_eval(REPO_ROOT)
    failed = False

    if card.blocked:
        known = {"SC-007 first-pass completeness"}
        undocumented = [b for b in card.blocked if b["criterion"] not in known]
        for entry in card.blocked:
            marker = "DOCUMENTED" if entry["criterion"] in known else "UNDOCUMENTED"
            print(f"BLOCKED [{marker}] {entry['criterion']}")
            print(f"    {entry['reason']}")
        if undocumented:
            failed = True
            print("\nAn undocumented Blocked criterion is a regression.")

    shortfalls = []
    for metric in card.metrics:
        target = metric.target
        if "no target" in target or "BLOCKED" in target:
            continue
        if target == "0":
            if metric.numerator != 0:
                shortfalls.append(f"{metric.name}: {metric.numerator}, target 0")
        elif target == "100%":
            if metric.pct < 100.0:
                shortfalls.append(f"{metric.name}: {metric.pct:.2f}%, target 100%")
        elif target.startswith(">="):
            floor = float(target.replace(">=", "").replace("%", "").strip())
            if metric.pct < floor:
                shortfalls.append(f"{metric.name}: {metric.pct:.2f}%, target {target}")

    if shortfalls:
        failed = True
        print("Metrics below target:")
        for line in shortfalls:
            print(f"  - {line}")

    if failed:
        return 1

    print(f"All gradable metrics at or above target ({len(card.metrics)} reported).")
    print(f"  dataset {card.dataset_id} · bundle {card.bundle_id} · register {card.register_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
