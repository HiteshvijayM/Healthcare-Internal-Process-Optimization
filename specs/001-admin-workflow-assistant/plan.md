# Implementation Plan: Administrative Workflow Assistant

**Branch**: `001-admin-workflow-assistant` | **Date**: 2026-09-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-admin-workflow-assistant/spec.md` (Ratified — CHG-021)

**Governance**: [`docs/constitution.md`](../../docs/constitution.md) is authoritative and non-overridable by this plan or by any execution agent. Where this plan and the Constitution appear to conflict, the Constitution wins and work pauses for escalation (constitution §2, §8).

---

## Summary

Build an administrative workflow assistant that orchestrates a patient's *administrative* journey from arrival to release routing — registering the arriving request, extracting it into a structured case record, backfilling what is derivable, naming what is missing, routing it with an explainable reason, opening role approvals in parallel, escalating registered critical signals to clinical authority, and enforcing clinical and financial clearance gates — **while a human keeps every decision**.

The technical approach rests on four load-bearing choices, each of which converts a written rule into a structural property:

1. **A MAF workflow, not an agent** ([research.md](./research.md) D1–D2). Eight executors matching the journey stages named in `feature.md` §9, with checkpointing across the long human waits that dominate this workflow.
2. **Human lockpoints are suspensions, not conditionals** (D3). Every approval is a MAF request/response pause. There is no code path that proceeds without a response — which is what makes SC-008's "exactly zero unapproved sends" defensible rather than aspirational.
3. **Judgement is separated from decision** (D4 — the most consequential choice here). Models propose *extraction* and *prose*; they decide nothing. Routing, duplicate detection, critical-signal matching, escalation precedence, gating and SLA computation are pure deterministic functions over a frozen declarative policy bundle. This is simultaneously how FR-049/P7 determinism is achieved, how FR-017's "inspectable rules" claim stays true, and how constitution §5's prohibition on clinical inference is kept structural.
4. **The audit log is the system of record** (D14). All state is a projection built by replay, so FR-043's "reconstruct from the recorded history alone" cannot drift from reality — the history *is* the reality.

**Scope of this plan**: design artifacts only. No application source code is written at this stage.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Microsoft Agent Framework (`agent-framework`, Python) for the workflow graph, executors, checkpointing and human-in-the-loop request/response; Copilot SDK for the single conversational surface (P9); Pydantic for entity/contract validation; PyYAML for the declarative policy bundle; OpenTelemetry via MAF's built-in tracing
**Storage**: Append-only, hash-chained JSONL event log as the system of record; all read models (case state, status board, scorecards) are projections rebuilt by replay. No database required at this scale — retention is a file-retention policy under P8 (project lifetime, min 90 days, no purge before sign-off)
**Testing**: `pytest`, in four tiers — contract (config schemas, register-mirror equality, masking scan, effect-gate coverage), scenario (named for AS-1..AS-14 and the spec's edge cases), unit (one per deterministic decision function), harness (mapped to Passes 0–6 so a pass score is computed, not asserted)
**Target Platform**: Local / dev-container execution; a single demo tenant with one authenticated reviewer session (P9). Production hosting, multi-tenancy and SSO are explicitly out of scope (`feature.md` §4)
**Project Type**: Agent workflow application with a conversational surface and an evaluation harness — single Python project, not a frontend/backend split
**Performance Goals**: Draft ready in **< 30 s at p95** (nearest-rank, over every case admitted to the run, outliers itemised with cause) — SC-003. Escalation packet prepared within **30 s** of detection — FR-024
**Constraints**:
- **Determinism is non-negotiable** — 100% identical per-case classifications across runs, aggregates within ±2 pp (P7, FR-049, SC-013)
- **Synthetic data only** — `SYN-CASESET-v2`; no real patient data ingested, stored, logged or exported at any point (constitution §3, FR-046)
- **Zero unapproved outbound actions** (FR-030, SC-008); the agent holds **no** approver role and **no** designation (FR-038, harness §4.1/§4.2)
- **No inference on critical conditions** — literal matching against `CCR-DEMO-v1` only; a missing register blocks rather than reports a clean result (FR-057, P11)
- **Routing rules declarative and reviewer-readable**, in config rather than code (`feature.md` §9, §13.5)
- **Never-cut features**: F12 (human approval actions), F19 (safety boundary), F20 (audit trail), F24 (governance enforcement) — non-waivable under any circumstance (harness §11.1)

**Scale/Scope**: 20-case synthetic dataset; 5 fixed routing queues; 11 roles + 4 designations; 57 functional requirements; 15 success criteria; 24 features across 4 milestones; 7 validation passes

*No `NEEDS CLARIFICATION` items remain — all 14 unknowns are resolved in [research.md](./research.md) §7.*

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

Gates derived directly from [`docs/constitution.md`](../../docs/constitution.md) §2–§8. `.specify/memory/constitution.md` was verified byte-identical, so a single set of gates applies.

### Initial gate evaluation (pre-Phase 0)

| Gate | Constitutional source | Requirement on this plan | Result |
|---|---|---|---|
| **G1 — Change control** | §2 | Plan must not amend the Constitution, and must pause on conflict | ✅ PASS — no amendment proposed |
| **G2 — PHI and data handling** | §3 | Synthetic/de-identified only; provenance recorded; logs and traces mask identifiers | ✅ PASS — `SYN-CASESET-v1` with provenance in `data/README.md` |
| **G3 — HIPAA and privacy** | §4 | Role-aware access; who/what/when/why audit reconstruction; purpose-limited | ✅ PASS — role registry + audit event log |
| **G4 — Clinical safety boundary** | §5 | No autonomous diagnosis, treatment recommendation, medical-necessity determination, clinical clearance, or discharge/release authorisation; critical conditions escalated to authorised clinical humans | ✅ PASS — the five acts are refused at every stage; escalation is human-dispatched |
| **G5 — Security baseline** | §6 | No hardcoded/source-controlled secrets; least privilege; security-relevant actions auditable; sensitive logs redacted | ✅ PASS — env/managed identity only |
| **G6 — Code and delivery** | §7 | Traceable to requirements; validation evidence accompanies behaviour; spec before code; every change in `docs/progress-log.md` | ✅ PASS — **R1 closed**, see below |
| **G7 — Enforcement** | §8 | Violations are stop-ship; default to safer behaviour on ambiguity; agents must not override | ✅ PASS — every ambiguity in this plan resolved conservatively |

**G6 — finding R1, now closed.** At the time this plan was drafted the CHG-021 ratifications were live in `feature.md` §5.4, harness §4.2, `spec.md` and `docs/critical-condition-register.md`, but **no CHG-021 entry existed in `docs/progress-log.md`** — the change table ended at CHG-020 and §6 "Current Next Steps" still instructed that planning must not start. Constitution §7 and FR-050 require every change to be recorded there; F24 enforces it. The entry has since been written (CHG-021), along with CHG-022 covering these planning artifacts, and §4, §6, §7 and §8 of the log were brought current. G6 therefore passes. The finding is retained here rather than deleted because the sequence — artifacts changed before the change was logged — is exactly the failure mode F24 exists to catch, and the record of catching it is worth more than a clean-looking table.

### Post-design gate re-evaluation (after Phase 1)

| Gate | Design mechanism that satisfies it | Result |
|---|---|---|
| **G1** | Policy bundle is versioned and hashed; safety-bearing values (P1, P3, P10, P11) require Compliance Reviewer approval to loosen; register amendment requires Clinical Authority + Compliance Reviewer | ✅ PASS |
| **G2** | Masking filter at the **write** boundary, installed on the audit writer *and* the OTel exporter (D15); dataset ID pinned in the bundle lock; contract test scans every event and trace for unmasked identifier patterns | ✅ PASS |
| **G3** | Roles are authorities not persons; `ActionGate` enforces the role check at the point of effect; append-only hash-chained log supplies who/what/when/why; replay reproduces state (D12, D14) | ✅ PASS |
| **G4** | Critical detection is **literal marker matching only** against `CCR-DEMO-v1` — no embeddings, no similarity, no model call (D9). Stage-independent safety guard on both the inbound and outbound edge (D13). Escalation dispatch requires a recorded human approval; the agent is unrepresentable in the role type (D12). Packet asserts only the observed signal and its source | ✅ PASS |
| **G5** | Secrets from env/managed identity; `.env.example` placeholders only; policy files hold policy, never credentials; every effect is an audited event (D20) | ✅ PASS |
| **G6** | Every design element traces to a numbered FR (see §"Requirement coverage"); tests named for AS-1..AS-14; harness tier computes pass scores | ✅ PASS — R1 closed by the CHG-021/CHG-022 log entries |
| **G7** | Ambiguity resolved conservatively throughout: unresolvable register **blocks** rather than reports clean (D9); replay cache miss is a **hard error** rather than a live fallthrough (D5); default routing rule's confidence sits **below** the P1 threshold so a fallback can never provisionally route (`RC-6`); governance blockers **aggregate** all absent designations rather than short-circuiting (D10) | ✅ PASS |

**Verdict: PASS on all seven gates.** No design-level constitutional violation exists. No complexity deviation requires justification. R1 (the unlogged CHG-021) and R2 (the graded-field denominator) were both closed before the task list was executed; R3 (the Blocked harness run) is the expected pre-implementation state and M0 is scoped to clear it; R4 (demo-scoped register) is informational and carries a standing prohibition on real-data use.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-admin-workflow-assistant/
├── spec.md                       # ratified specification (input)
├── plan.md                       # this file
├── research.md                   # Phase 0 — D1..D20 decisions, findings R1..R4
├── data-model.md                 # Phase 1 — entities, invariants, state machines
├── quickstart.md                 # Phase 1 — developer/reviewer onboarding
├── contracts/                    # Phase 1
│   ├── README.md                 # contract index + test obligations
│   ├── policy-config.md          # the declarative policy bundle (the "inspectable rules")
│   ├── escalation-outcome.md     # FR-054 precedence decision table
│   ├── agent-surface.md          # conversational command surface (P9/F22)
│   ├── audit-event.schema.json   # the system of record
│   ├── case-record.schema.json   # extraction output
│   └── eval-scorecard.schema.json # harness §10 output template
├── checklists/requirements.md    # spec quality checklist (existing)
└── tasks.md                      # Phase 2 — NOT created by this command
```

### Source Code (repository root)

```text
src/admin_workflow/
├── workflow/
│   ├── graph.py                  # MAF WorkflowBuilder wiring
│   ├── checkpoint.py             # resumability across long human waits
│   └── stages/                   # one executor per journey stage (feature.md §9)
│       ├── register.py           #   arrive/register        F1
│       ├── enrich.py             #   enrich/backfill        F3
│       ├── validate.py           #   validate               F4
│       ├── route.py              #   route/provisional      F6, F7
│       ├── approvals.py          #   approvals/escalation   F11, F13
│       ├── clinical_gate.py      #   clinical clearance     F16
│       ├── financial_gate.py     #   financial clearance    F17
│       └── release.py            #   release routing        F18
├── domain/                       # entities + state machines (pure, no I/O)
├── policy/
│   ├── bundle.py                 # load, hash-verify, freeze
│   └── resolvers.py              # SLA, field-owner, designation resolution
├── decisions/                    # DETERMINISTIC — no model calls, ever
│   ├── routing.py                # FR-017, FR-018
│   ├── duplicates.py             # FR-014, FR-055
│   ├── critical_signal.py        # FR-057 — literal marker matching
│   ├── escalation_outcome.py     # FR-054 — the single precedence resolver
│   ├── provisional.py            # FR-010, FR-011
│   ├── clearance.py              # FR-033, FR-034
│   └── sla.py                    # FR-022, FR-023, FR-056
├── approvals/
│   ├── action_gate.py            # the single choke point for every outbound effect
│   ├── ledger.py                 # approval records
│   └── registry.py               # roles + designations; agent unrepresentable
├── safety/                       # F19 — stage-independent guard + refusal templates
├── audit/
│   ├── store.py                  # append-only, hash-chained JSONL
│   ├── masking.py                # write-boundary filter, incl. OTel exporter
│   └── replay.py                 # projections + compliance reconstruction
├── extraction/                   # F2 — model-assisted; live/record/replay modes
├── drafting/                     # F9 — model-assisted prose only
├── surface/                      # F22 — Copilot SDK conversational surface
└── eval/                         # F21 — harness runner + scorecard emitter

config/policy/v1/                 # the frozen declarative bundle (contracts/policy-config.md)
├── policy-table.yaml             #   P1..P11
├── routing-rules.yaml            #   F7 — ordered, plain-English, restricted grammar
├── approver-registry.yaml        #   harness §4.1 + §4.2
├── field-owner-map.yaml          #   FR-008
├── sla-table.yaml                #   P4/P5
├── critical-signal-register.yaml #   mirror of CCR-DEMO-v1 (markdown is authoritative)
└── bundle.lock.json              #   bundle id + SHA-256 of every file

tests/
├── contract/                     # schemas, register-mirror equality, masking scan, gate coverage
├── scenario/                     # AS-1..AS-14 + every edge case in spec.md
├── unit/                         # one per deterministic decision function
└── harness/                      # Pass 0..6 — computes coverage and quality scores
```

**Structure Decision**: A **single Python project**. There is no frontend/backend split to make — P9 fixes the surface at one conversational web/in-app surface with one tenant and one reviewer session, and `feature.md` §4 excludes production hosting and multi-tenancy. The internal division is by *trust boundary* rather than by layer, which is the division this specification actually cares about:

- `decisions/` is pure, deterministic, and **must not** import `extraction/` or `drafting/`. A lint rule and a contract test enforce this. It is the single mechanism protecting P7/FR-049 determinism and FR-017 inspectability.
- `approvals/`, `safety/` and `audit/` are cross-cutting and correspond one-to-one with the never-cut features F12, F19 and F20. They are built **first** (M0), because retrofitting an approval gate onto working stages is how gates end up with holes.
- `config/policy/` is deliberately outside `src/` — it is a **reviewer-facing artifact**, not an implementation detail. `feature.md` §9 requires routing rules to be readable rather than buried in code, and §5.4 requires every scored number to live in one place a non-technical reviewer can read.

---

## Phase mapping to milestones and validation

`feature.md` §11 milestones are gated by completion, not calendar. Each gate is a harness pass.

| Milestone | Features | Design artifacts consumed | Harness exit gate |
|---|---|---|---|
| **M0 — Foundation** | Policy bundle, event store + masking, role registry, `ActionGate`, safety guard | `policy-config.md`, `audit-event.schema.json`, D12, D13, D15 | **Pass 0** (hard gate) — clears CA-008-003 |
| **M1 — Intake baseline** | F1–F8 | `case-record.schema.json`, data-model §2.1–2.5, D5, D7, D11 | **Passes 1, 2** |
| **M2 — Orchestration** | F9–F15 | `escalation-outcome.md`, data-model §2.6–2.7, §3.2, D9, D10, D16 | **Pass 3** |
| **M3 — Governance** | F16–F24 | `agent-surface.md`, `eval-scorecard.schema.json`, D14, D17, D18 | **Passes 4, 5, 6** (4 and 5 hard gates) |
| **M4 — Review** | Scorecard, demo, production-gap statement | All | Full run recorded **Go** in `docs/progress-log.md` |

**Priority discipline** (`feature.md` §6): Must-have features (F1, F2, F4, F7, F11, F12, F15, F16, F17, F18, F19, F20, F23, F24) **cannot be waived**. Should-have features (F3, F5, F6, F8, F9, F10, F13, F14, F21, F22) may be cut only under a formal §11.1 waiver approved by **both** Team Lead and Compliance Reviewer, logged in `docs/progress-log.md` *before* the affected pass is scored. F12, F19, F20 and F24 are non-waivable under any circumstance.

---

## Requirement coverage

Every one of the 57 functional requirements maps to a design element. Full entity-level mapping is in [data-model.md](./data-model.md) §4; this is the component view.

| Component | Requirements | Features |
|---|---|---|
| `workflow/stages/register` | FR-001, FR-005 | F1 |
| `extraction/` | FR-002 | F2 |
| `workflow/stages/enrich` | FR-003, FR-004 | F3 |
| `workflow/stages/validate` | FR-006, FR-007, FR-008, FR-009, FR-016 | F4, F5 |
| `decisions/provisional` | FR-010, FR-011, FR-012, FR-013 | F6 |
| `decisions/routing` | FR-017, FR-018, FR-045 | F7 |
| `decisions/duplicates` | FR-014, FR-015, FR-055 | F8 |
| `drafting/` | FR-029, FR-032 | F9 |
| `workflow/stages/approvals` | FR-019, FR-020, FR-021 | F10, F11 |
| `approvals/action_gate` | FR-029, FR-030, FR-031, FR-032, FR-035, FR-038 | **F12** |
| `decisions/critical_signal` | FR-057 | F13, F19 |
| `decisions/escalation_outcome` | FR-024, FR-025, FR-026, FR-027, FR-028, FR-051, FR-052, FR-053, FR-054 | F13 |
| `decisions/sla` | FR-022, FR-023, FR-056 | F15 |
| `surface/` (status board) | FR-039, FR-040, FR-041 | F14, F22 |
| `decisions/clearance` | FR-033, FR-034 | F16, F17, F18 |
| `safety/` | FR-036, FR-037 | **F19** |
| `audit/` | FR-042, FR-043, FR-044, FR-047 | **F20** |
| `eval/` | FR-048, FR-049 | F21 |
| `policy/bundle` | FR-045, FR-046, FR-050 | F23, **F24** |

**Success criteria**: SC-001/002 → parallel approvals + status-board timing · SC-003 → p95 draft readiness · SC-004..SC-007, SC-009, SC-015 → `eval/` graded against the answer key · SC-008 → `ActionGate` (structural) · SC-010 → applied-SLA recording · SC-011 → the escalation precedence resolver · SC-012 → replay + masking scan · SC-013 → deterministic decisions + replay fixtures · SC-014 → the safety guard.

---

## Risks and mitigations

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| 1 | A model call leaks into the decision path | Fails P7/FR-049 determinism **and** FR-017 inspectability at once, and may constitute clinical inference under §5 | Hard import boundary: `decisions/` may not import `extraction/` or `drafting/`; enforced by lint rule **and** contract test |
| 2 | Critical detection generalises beyond the register | **Sev 0** — the exact failure the register exists to prevent | Literal marker matching only; negative-direction tests on CASE-013 and CASE-020; the phrase "no critical condition present" is forbidden in every output path |
| 3 | An absent clinical recipient is reported as a completeness failure | Fails FR-054/SC-011 precedence; sends the defect to the wrong owner | One total resolver with an exhaustive outcome matrix and an explicit test for this exact case |
| 4 | Identifier leakage via MAF/OTel traces | Fails constitution §3 and SC-012; traces are the sink nobody writes by hand | Masking filter installed on the exporter itself, not just the audit writer; a scan across all events *and* traces is a contract test |
| 5 | Policy value drifts from `feature.md` §5.4 | Harness scores against a value no reviewer approved | Contract test asserts every P1–P11 value equals §5.4; bundle hashes verified at load; mismatch is a startup failure |
| 6 | Register YAML mirror diverges from the markdown | Bypasses the Clinical Authority + Compliance Reviewer change bar on a safety-bearing policy | Entry-for-entry equality test; markdown SHA-256 recorded in `bundle.lock.json`; drift fails the build |
| 7 | A demo shortcut bypasses an approval | Fails SC-008 and never-cut F12 | Approvals are workflow suspensions, not conditionals — there is no path to bypass |
| 8 | The harness run stays Blocked | No claim may cite it; §4 states a Blocked run is not a Pass | M0 explicitly delivers the build ID (CA-008-002), frozen policy version (CA-008-003) and sandbox (CA-008-004) |
| 9 | SC-004 denominator ambiguity (finding **R2**) | A percentage without an agreed denominator is not a measurement (`feature.md` §7) | Close R2 before SC-004 is first scored; the case-record contract currently follows the answer key and says so explicitly |

---

## Complexity Tracking

> Filled only if the Constitution Check has violations that must be justified.

**No constitutional violations require justification.** The Constitution Check returned PASS on all seven gates at both evaluation points, with one open *governance action* (R1 — the missing CHG-021 progress-log entry), which is a record-keeping gap in an existing artifact rather than a design deviation.

Two design choices add structure beyond the simplest possible implementation. Both are recorded here for transparency, and both are **required** by the specification rather than chosen for elegance:

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Separate deterministic `decisions/` layer with an enforced import boundary | P7 states determinism is not negotiable; FR-049 requires identical per-case classifications; FR-017 requires inspectable declarative rules; constitution §5 forbids clinical inference | Letting the model route and explain is simpler and fails all four at once — non-deterministic, post-hoc explanations rather than real traces, unreadable by a non-technical reviewer, and inference on clinical criticality |
| Event-sourced audit log with state as a projection | FR-043 requires reconstruction **from the recorded history alone**; harness Pass 4 scores tamper resistance; P8 requires full lineage retention | Mutable state plus a side audit table is simpler but the two can diverge, which would make FR-043 an unverified claim precisely where verification is the point |

---

## Progress

- [x] Pre-execution: extension hooks checked — `.specify/extensions.yml` absent, none registered
- [x] Setup: `setup-plan.sh --json` executed (via `SPECIFY_FEATURE`, as the worktree branch name is not a feature-branch name)
- [x] Context loaded: spec.md, constitution.md, feature.md §5.4/§6/§7/§9/§11/§13, harness §4.1/§4.2/§5–§11, critical-condition-register.md, data/README.md, answer-key.json, progress-log.md
- [x] Technical Context filled — 14 unknowns resolved, zero `NEEDS CLARIFICATION`
- [x] Constitution Check (initial) — PASS on all seven gates (G6 conditional at drafting on finding R1; R1 closed by the CHG-021/CHG-022 log entries)
- [x] Phase 0 — [research.md](./research.md): decisions D1–D20, findings R1–R4
- [x] Phase 1 — [data-model.md](./data-model.md), [contracts/](./contracts/) (6 contracts), [quickstart.md](./quickstart.md)
- [x] Constitution Check (post-design) — PASS, R1 still open
- [x] Agent context update — `.specify/scripts/bash/update-agent-context.sh copilot` (generated `.github/copilot-instructions.md`; template placeholders removed and a governance-precedence header added by hand)
- [ ] **Phase 2 — `tasks.md`: NOT created by this command** (run `/speckit.tasks`)

**Agent context note**: the repository already carries a curated `.github/` agent configuration and a governance doc set that is authoritative under constitution §2. The Spec Kit context script writes an agent-facing summary file; running it is safe, but any content it generates is subordinate to `docs/constitution.md` and must not restate policy values — those live only in `feature.md` §5.4 and the policy bundle.

---

## Actions required before implementation begins

| # | Action | Owner | Blocking |
|---|---|---|---|
| 1 | Record **CHG-021** in `docs/progress-log.md` and update §6 "Current Next Steps", which still states planning must not start (finding **R1**) | Team Lead + Compliance Reviewer | **Yes** — constitution §7, FR-050 |
| 2 | Record this planning change (plan.md + design artifacts) in `docs/progress-log.md` | Team Lead | **Yes** — constitution §7 |
| 3 | Resolve the graded-field mismatch between `data/README.md` §4 (8 fields) and `answer-key.json` (7 fields) — finding **R2** | Team Validation Lead | Before SC-004 is first scored |
| 4 | Name acting holders of the §4.1 roles and §4.2 designations in the run record | Team Validation Lead | Before Pass 0 |
| 5 | Freeze the policy bundle and record a build identifier — clears CA-008-002 / CA-008-003 | Team Lead | Before Pass 0 |

---

## Next command

```text
/speckit.tasks
```

Generates `tasks.md`, the dependency-ordered breakdown, from this plan and its design artifacts.
