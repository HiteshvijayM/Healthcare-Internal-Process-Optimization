# Admin Workflow Agent — AI Champs Hackathon

**Track:** Healthcare — Internal Process Optimization
**Stack:** Microsoft Agent Framework (MAF) + Copilot SDK

| Field | Value |
|---|---|
| **Problem statement** | Administrative workflows involve repetitive tasks, handoffs, and delays. |
| **Expected value** | Lower cycle time; fewer errors |

An agent that takes an incoming administrative request, reads it, checks it, routes it, and drafts the next step — so humans review and approve instead of re-typing and chasing. Approvals that used to queue behind each other now run in parallel.

**Chosen workflow:** full patient administrative journey orchestration from arrival to release routing, with strict clinical human lockpoints.

```
Document arrives → agent extracts fields, flags gaps, picks the queue, drafts the note
                 → humans review and approve in parallel → item moves
```

## Status — built, tested, validated

| | |
|---|---|
| **Build** | `src/admin_workflow/` — 25 modules |
| **Tests** | **154 passing** across contract, unit, scenario and harness tiers |
| **Harness verdict** | **CONDITIONAL GO** — all three hard gates pass ([run record](./docs/multipass-run-chg-023.md)) |
| **Policy bundle** | `POLICY-v1`, frozen and SHA-256 verified at load |

| Metric | Result | Target |
|---|---|---|
| Field extraction accuracy | **139/140 = 99.29%** | ≥ 85% |
| Seeded omission detection | **12/12 = 100%** | 100% |
| Routing accuracy | **10/10** | ≥ 9/10 |
| First-pass completeness | **20/20 = 100%** | ≥ 90% |
| Escalation outcome correctness | **20/20 = 100%** | 100% |
| Unapproved sends | **0** | 0 |
| False escalations | **0** | 0 |

Two criteria are recorded **Blocked, not passed** — SC-009 and CCS-003 lack fixtures in `SYN-CASESET-v1`. A Blocked criterion is not a Pass, so they are named rather than counted. See the run record §5.

## Run it

```bash
pip install pyyaml pytest

python src/admin_workflow/surface/cli.py verify   # check bundle integrity
python src/admin_workflow/surface/cli.py eval     # score against the 20-case dataset
python -m pytest -q                               # 154 tests
```

## The one design decision that matters

**Judgement is separated from decision.** Models do extraction and prose only. Routing, duplicate detection, critical-signal matching, escalation precedence, clearance gating and SLA computation are pure deterministic functions over a frozen policy bundle — and `decisions/` is forbidden from importing `extraction/` or `drafting/`, enforced by a contract test that parses every module's AST.

That single boundary is what lets three properties hold at once instead of trading against each other: run-to-run determinism (P7), routing decisions a non-technical reviewer can inspect (FR-017), and the constitution's prohibition on clinical inference (§5).

## Start here

| File | What it is |
|---|---|
| [`feature.md`](./feature.md) | The feature request — scope, F1-F24, thresholds P1-P11, decisions. **Read this first.** |
| [`specs/001-admin-workflow-assistant/spec.md`](./specs/001-admin-workflow-assistant/spec.md) | The formal specification — 57 requirements, 15 success criteria, full scenario traceability |
| [`docs/multipass-run-chg-023.md`](./docs/multipass-run-chg-023.md) | **The validation run record** — scores, evidence, blocked criteria, production gaps |
| [`docs/constitution.md`](./docs/constitution.md) | Non-negotiable constraints. Immutable by default. |
| [`docs/critical-condition-register.md`](./docs/critical-condition-register.md) | `CCR-DEMO-v1` — the exclusive set of signals that may be treated as critical. No inference beyond it. |
| [`config/policy/v1/`](./config/policy/v1/) | The declarative policy bundle — every scored number and every routing rule, in reviewer-readable YAML |
| [`docs/multipass-validation-harness.md`](./docs/multipass-validation-harness.md) | The readiness gate. No claim ships without a passing run. |
| [`data/README.md`](./data/README.md) | Synthetic dataset — 20 sample cases, the grading answer key, and the known coverage gaps |

Operational records live in [`docs/`](./docs/): the change system-of-record is [`progress-log.md`](./docs/progress-log.md).

## Layout

```
.
├── README.md
├── feature.md                            # feature request (v2)
├── src/admin_workflow/
│   ├── decisions/                        # DETERMINISTIC — no model calls, ever
│   ├── approvals/                        # F12 — ActionGate, the single outbound choke point
│   ├── safety/                           # F19 — clinical boundary, both edges
│   ├── audit/                            # F20 — hash-chained store, write-boundary masking
│   ├── extraction/ · drafting/           # model-assisted; may never be imported by decisions/
│   ├── workflow/ · policy/ · domain/
│   ├── eval/                             # F21 — harness runner and scorecard
│   └── surface/                          # F22 — CLI / conversational surface
├── config/policy/v1/                     # the frozen, hash-locked declarative bundle
├── tests/
│   ├── contract/ · unit/ · scenario/ · harness/
├── specs/001-admin-workflow-assistant/   # spec, plan, research, data model, contracts, 180 tasks
├── docs/                                 # constitution, register, harness, run records, progress log
└── data/sample/                          # 20 synthetic cases + answer key (NO real PHI)
```

## Ground rules

- **Synthetic data only.** No real patient data, ever.
- The agent assists; a **human approves** every outbound action.
- No clinical, diagnostic, or medical-necessity decisions.
- Routing rules must be readable by a non-technical reviewer.

## Never cut

`F12` human approval actions · `F19` safety boundary · `F20` audit trail · `F24` governance enforcement

These are what make it a healthcare product rather than a script.
