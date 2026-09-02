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
| **Build** | `src/admin_workflow/` — 23 modules |
| **Tests** | **166 passing** — 25 contract, 53 unit, 49 scenario, 39 harness |
| **Harness verdict** | **GO** — all hard gates pass, **zero Blocked criteria** ([run record](./docs/multipass-run-chg-024.md)) |
| **Policy bundle** | `POLICY-v2`, frozen and SHA-256 verified at load |
| **Dataset** | `SYN-CASESET-v2`, 23 synthetic cases |

| Metric | Result | Target |
|---|---|---|
| Field extraction accuracy | **160/161 = 99.38%** | ≥ 85% |
| Seeded omission detection | **13/13 = 100%** | 100% |
| Routing accuracy | **12/12 = 100%** | ≥ 90% |
| First-pass completeness | **23/23 = 100%** | ≥ 90% |
| Escalation outcome correctness | **23/23 = 100%** | 100% |
| SC-009 duplicate matcher correctness | **8/8 = 100%** | 100% |
| Register entry coverage | **3/3 = 100%** | 100% |
| Unapproved sends / false escalations | **0 / 0** | 0 |

## Run it

```bash
pip install pyyaml pytest

python src/admin_workflow/surface/cli.py verify   # check bundle integrity
python src/admin_workflow/surface/cli.py eval     # score against the 23-case dataset
python -m pytest -q                               # 166 tests
```

## The one design decision that matters

**Judgement is separated from decision.** Models do extraction and prose only. Routing, duplicate detection, critical-signal matching, escalation precedence, clearance gating and SLA computation are pure deterministic functions over a frozen policy bundle — and `decisions/` is forbidden from importing `extraction/` or `drafting/`, enforced by a contract test that parses every module's AST.

That single boundary is what lets three properties hold at once instead of trading against each other: run-to-run determinism (P7), routing decisions a non-technical reviewer can inspect (FR-017), and the constitution's prohibition on clinical inference (§5).

## How we know the tests mean something

Two metrics were strengthened before they were allowed to pass:

- **SC-009 grades which duplicate matcher fired**, not merely that a duplicate was found. A key-match-only implementation would have scored 100% on the flag alone while the unbounded identity matcher sat as dead code. `CASE-021` arrives 39 days out against a closed case, so only the identity matcher can catch it.
- **Register coverage is computed from the register**, not from a maintained list. Every entry must fire on a fixture; one that fires on none is reported Blocked automatically. Previously this section *read* as full coverage while a safety-bearing entry had never been exercised.

A claim that cannot fail is not evidence. Both were unfalsifiable; both are now falsifiable.

## Start here

| File | What it is |
|---|---|
| [`feature.md`](./feature.md) | The feature request — scope, F1-F24, thresholds P1-P11, decisions. **Read this first.** |
| [`specs/001-admin-workflow-assistant/spec.md`](./specs/001-admin-workflow-assistant/spec.md) | The formal specification — 57 requirements, 15 success criteria, full scenario traceability |
| [`docs/multipass-run-chg-024.md`](./docs/multipass-run-chg-024.md) | **The validation run record** — scores, evidence, and the production gaps that remain |
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
