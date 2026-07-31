# Healthcare Agents — AI Champs Hackathon

Two agents for the **Healthcare** track, built on **Microsoft Agent Framework (MAF)** + **Copilot SDK**.

| Agent | Problem statement | Expected value |
|---|---|---|
| **Clinical Knowledge Assistant** | Clinical and scientific information is fragmented across systems and difficult to find. | Faster answers; reduced staff workload |
| **Admin Workflow Assistant** | Administrative workflows involve repetitive tasks, handoffs, and delays. | Lower cycle time; fewer errors |

## Start here

- [`feature.md`](./feature.md) — the feature request / spec. Read this first.

## Layout

```
.
├── feature.md        # feature request (v1)
├── docs/             # design notes, review feedback
└── data/sample/      # synthetic sample documents (NO real PHI)
```

## Ground rules

- **Synthetic data only.** No real patient data, ever.
- The agents assist; a **human approves** every write action.
- No clinical, diagnostic, or medical-necessity decisions.
