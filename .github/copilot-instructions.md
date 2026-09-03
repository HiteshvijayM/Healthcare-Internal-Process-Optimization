# v-hvijay1-shiny-telegram Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-09-02

## Governance precedence (read first)

`docs/constitution.md` is authoritative and non-overridable. This file is a convenience summary and is
**subordinate** to it. Policy values (P1–P11) live only in `feature.md` §5.4 and the policy bundle at
`config/policy/v1/` — never restate or hardcode them here or anywhere else.

Non-waivable features: **F12** human approval actions, **F19** clinical safety boundary,
**F20** audit trail, **F24** governance enforcement.

## Active Technologies

- **Python 3.11+**
- **Microsoft Agent Framework** (`agent-framework`, Python) — workflow graph, typed executors,
  checkpointing, human-in-the-loop request/response
- **Copilot SDK** — the single conversational surface (P9)
- Pydantic (entity/contract validation), PyYAML (declarative policy bundle), OpenTelemetry via MAF tracing

(001-admin-workflow-assistant)

## Project Structure

```text
src/admin_workflow/   workflow/ domain/ policy/ decisions/ approvals/
                      safety/ audit/ extraction/ drafting/ surface/ eval/
config/policy/v1/     the frozen, reviewer-readable policy bundle
tests/                contract/ scenario/ unit/ harness/
```

See `specs/001-admin-workflow-assistant/plan.md` for the full layout and its rationale.

## Commands

```bash
pytest                 # all tiers
pytest tests/contract  # schemas, register mirror, masking scan, gate coverage
ruff check .
```

## Code Style

Python 3.11+: standard conventions. Two project-specific rules:

- `decisions/` is **pure and deterministic** and must never import `extraction/` or `drafting/`,
  and must never make a model call. This is what protects P7/FR-049 determinism.
- Every outbound effect goes through the single `approvals/action_gate.py` choke point.
  The agent holds no approver role and no designation.

## Recent Changes

- 001-admin-workflow-assistant: planning artifacts added (plan, research, data model, contracts, quickstart);
  stack set to Python 3.11+ on Microsoft Agent Framework + Copilot SDK

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
