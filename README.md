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

## Start here

| File | What it is |
|---|---|
| [`feature.md`](./feature.md) | The feature request — scope, F1-F24, thresholds P1-P11, decisions. **Read this first.** |
| [`specs/001-admin-workflow-assistant/spec.md`](./specs/001-admin-workflow-assistant/spec.md) | The formal specification — 57 requirements, 15 success criteria, full scenario traceability |
| [`docs/constitution.md`](./docs/constitution.md) | Non-negotiable constraints. Immutable by default. |
| [`docs/critical-condition-register.md`](./docs/critical-condition-register.md) | `CCR-DEMO-v1` — the exclusive set of signals that may be treated as critical. No inference beyond it. |
| [`prompts/specify-prompt.md`](./prompts/specify-prompt.md) | Ready-to-paste prompt for the `specify` agent |
| [`docs/multipass-validation-harness.md`](./docs/multipass-validation-harness.md) | The readiness gate. No claim ships without a passing run. |
| [`data/README.md`](./data/README.md) | Synthetic dataset — 20 sample cases and the grading answer key |

Operational records live in [`docs/`](./docs/): the change system-of-record is [`progress-log.md`](./docs/progress-log.md) and the latest harness run is [`multipass-run-chg-008.md`](./docs/multipass-run-chg-008.md).

## Layout

```
.
├── README.md
├── feature.md                            # feature request (v2)
├── prompts/
│   └── specify-prompt.md                 # /specify input + clarification answers
├── specs/001-admin-workflow-assistant/
│   ├── spec.md                           # formal specification (FR-001..FR-057, SC-001..SC-015)
│   ├── plan.md                           # implementation plan
│   ├── tasks.md                          # dependency-ordered task breakdown
│   └── checklists/requirements.md        # spec quality checklist
├── docs/
│   ├── constitution.md                   # non-negotiable constraints
│   ├── critical-condition-register.md    # CCR-DEMO-v1 — registered critical signals
│   ├── multipass-validation-harness.md   # 7-pass readiness gate
│   ├── multipass-run-chg-008.md          # harness run record
│   └── progress-log.md                   # change system-of-record
└── data/
    ├── README.md                         # dataset provenance
    └── sample/                           # 20 synthetic cases + answer key (NO real PHI)
```

## Ground rules

- **Synthetic data only.** No real patient data, ever.
- The agent assists; a **human approves** every outbound action.
- No clinical, diagnostic, or medical-necessity decisions.
- Routing rules must be readable by a non-technical reviewer.

## Never cut

`F12` human approval actions · `F19` safety boundary · `F20` audit trail · `F24` governance enforcement

These are what make it a healthcare product rather than a script.
