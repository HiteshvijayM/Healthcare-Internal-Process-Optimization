# Admin Workflow Agent — AI Champs Hackathon

**Track:** Healthcare — Internal Process Optimization
**Stack:** Microsoft Agent Framework (MAF) + Copilot SDK

| Field | Value |
|---|---|
| **Problem statement** | Administrative workflows involve repetitive tasks, handoffs, and delays. |
| **Expected value** | Lower cycle time; fewer errors |

An agent that takes an incoming administrative request, reads it, checks it, routes it, and drafts the next step — so a human only reviews and approves instead of re-typing and chasing.

**Chosen workflow:** incoming referral / service-request intake. One request type, end to end, done properly.

```
Document arrives → agent extracts fields, flags gaps, picks the queue, drafts the note
                 → ONE human reviews and approves → item moves
```

## Start here

| File | What it is |
|---|---|
| [`feature.md`](./feature.md) | The feature request. **Read this first.** |
| [`docs/specify-prompt.md`](./docs/specify-prompt.md) | Ready-to-paste prompt for the `specify` agent |

## Layout

```
.
├── feature.md              # feature request (v2)
├── docs/
│   └── specify-prompt.md   # /specify input + clarification answers
└── data/sample/            # synthetic sample documents (NO real PHI)
```

## Ground rules

- **Synthetic data only.** No real patient data, ever.
- The agent assists; a **human approves** every outbound action.
- No clinical, diagnostic, or medical-necessity decisions.
- Routing rules must be readable by a non-technical reviewer.

## Never cut

`F7` human approval gate · `F10` safety boundary · `F11` audit log

These are what make it a healthcare product rather than a script.
