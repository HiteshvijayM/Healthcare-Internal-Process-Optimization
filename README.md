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
| **Build** | `src/admin_workflow/` — 24 modules |
| **Tests** | **179 passing** — 25 contract, 61 unit, 52 scenario, 41 harness |
| **Harness verdict** | **CONDITIONAL GO** — all three hard gates pass; one criterion Blocked ([run record](./docs/multipass-run-chg-025.md)) |
| **Policy bundle** | `POLICY-v2`, frozen and SHA-256 verified at load |
| **Dataset** | `SYN-CASESET-v2`, 23 synthetic cases |
| **Plan delivery** | 137 of 180 tasks, with every open task named and justified ([tasks.md](./specs/001-admin-workflow-assistant/tasks.md)) |

| Metric | Result | Target |
|---|---|---|
| Field extraction accuracy | **160/161 = 99.38%** | ≥ 85% |
| Seeded omission detection | **13/13 = 100%** | 100% |
| Routing accuracy | **12/12 = 100%** | ≥ 90% |
| Escalation outcome correctness | **23/23 = 100%** | 100% |
| SC-009 duplicate matcher correctness | **8/8 = 100%** | 100% |
| Register entry coverage | **3/3 = 100%** | 100% |
| Unapproved sends / false escalations | **0 / 0** | 0 |
| First-pass completeness | **20/23 = 86.96%** | ≥ 90% — **Blocked**, see below |

**One criterion is Blocked, and that is deliberate.** SC-007 falls short because three cases declare a backfillable field whose source is an external record store the dataset does not contain. The behaviour is correct — the system raises completion tasks rather than inventing values — so the shortfall is a fixture gap, not a defect. It is recorded Blocked rather than quietly redefined into a pass. Those fixtures were **not** authored to close it, because writing fixtures to move a number is precisely how the earlier measurement defect arose.

## How we know the tests mean something

Three metrics were strengthened before they were allowed to pass, and one of those changes lowered the verdict:

- **SC-009 grades which duplicate matcher fired**, not merely that a duplicate was found. A key-match-only implementation would have scored 100% on the flag alone while the unbounded identity matcher sat as dead code. `CASE-021` arrives 39 days out against a closed case, so only the identity matcher can catch it.
- **Register coverage is computed from the register**, not from a maintained list. Every entry must fire on a fixture; one that fires on none is reported Blocked automatically.
- **First-pass completeness was a metric that could not fail.** It had been defined as "items needing no rework loop" — but no rework path is implemented, so the counter never moved and it read 100% while measuring nothing. Redefining it to grade whether anything *derivable* was left underived made it falsifiable, and it promptly failed. That found a real missing capability (backfill, F3), which was then built.

A claim that cannot fail is not evidence. The third case is the honest one: fixing the measurement made the verdict worse, and the verdict was lowered rather than the measurement softened.

## Run it

```bash
pip install -e ".[dev]"

python src/admin_workflow/surface/cli.py verify   # bundle integrity — a hash mismatch is fatal
python src/admin_workflow/surface/cli.py eval     # score against the 23-case dataset
python scripts/assert_not_blocked.py              # the CI gate
python -m pytest -q                               # 179 tests
ruff check .                                      # includes the decisions/ import boundary
```

## The one design decision that matters

**Judgement is separated from decision.** Models do extraction and prose only. Routing, duplicate detection, critical-signal matching, escalation precedence, clearance gating and SLA computation are pure deterministic functions over a frozen policy bundle — and `decisions/` is forbidden from importing `extraction/` or `drafting/`, enforced by a contract test that parses every module's AST.

That single boundary is what lets three properties hold at once instead of trading against each other: run-to-run determinism (P7), routing decisions a non-technical reviewer can inspect (FR-017), and the constitution's prohibition on clinical inference (§5).

## Start here

| File | What it is |
|---|---|
| [`feature.md`](./feature.md) | The feature request — scope, F1-F24, thresholds P1-P11, decisions. **Read this first.** |
| [`specs/001-admin-workflow-assistant/spec.md`](./specs/001-admin-workflow-assistant/spec.md) | The formal specification — 57 requirements, 15 success criteria, full scenario traceability |
| [`docs/multipass-run-chg-025.md`](./docs/multipass-run-chg-025.md) | **The validation run record** — scores, the Blocked criterion, and the production gaps that remain |
| [`docs/constitution.md`](./docs/constitution.md) | Non-negotiable constraints. Immutable by default. |
| [`docs/critical-condition-register.md`](./docs/critical-condition-register.md) | `CCR-DEMO-v1` — the exclusive set of signals that may be treated as critical. No inference beyond it. |
| [`config/policy/v1/`](./config/policy/v1/) | The declarative policy bundle — every scored number and every routing rule, in reviewer-readable YAML |
| [`docs/multipass-validation-harness.md`](./docs/multipass-validation-harness.md) | The readiness gate. No claim ships without a passing run. |
| [`data/README.md`](./data/README.md) | Synthetic dataset — 23 cases, the grading answer key, and what each trap catches |

Operational records live in [`docs/`](./docs/): the change system-of-record is [`progress-log.md`](./docs/progress-log.md).

## Layout

```
.
├── README.md
├── feature.md                            # feature request (v2)
├── pyproject.toml · .ruff.toml · pytest.ini · .env.example
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
├── scripts/assert_not_blocked.py         # the CI gate
├── tests/
│   ├── contract/ · unit/ · scenario/ · harness/
├── .github/workflows/ci.yml              # four tiers + bundle verification
├── specs/001-admin-workflow-assistant/   # spec, plan, research, data model, contracts, 180 tasks
├── docs/                                 # constitution, register, harness, run records, progress log
└── data/sample/                          # 23 synthetic cases + answer key (NO real PHI)
```

## Ground rules

- **Synthetic data only.** No real patient data, ever.
- The agent assists; a **human approves** every outbound action.
- No clinical, diagnostic, or medical-necessity decisions.
- Routing rules must be readable by a non-technical reviewer.

## Never cut

`F12` human approval actions · `F19` safety boundary · `F20` audit trail · `F24` governance enforcement

These are what make it a healthcare product rather than a script.
