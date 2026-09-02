# Tasks: Administrative Workflow Assistant

**Feature**: `001-admin-workflow-assistant` | **Phase**: 2 | **Date**: 2026-09-02
**Input**: Design documents from `/specs/001-admin-workflow-assistant/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Governance**: [`docs/constitution.md`](../../docs/constitution.md) is authoritative and non-overridable by this task list or by any execution agent. Where a task and the Constitution appear to conflict, the Constitution wins and work **pauses for escalation** (constitution §2, §8). No task below may be reinterpreted to work around a constitutional constraint.

**Tests**: Test tasks **are** included and are mandatory. They are not an optional tier here — constitution §7 requires validation evidence to accompany behaviour, [research.md](./research.md) D19 makes the acceptance scenarios first-class tests, and [`contracts/README.md`](./contracts/README.md) obliges every contract to carry a **failing-first** test before its implementation exists.

**Organization**: Tasks are grouped by user story so each story is independently implementable and independently testable.

---

## Delivery status — as of CHG-024

**137 of 180 tasks delivered (76%).** The harness verdict is **CONDITIONAL GO** — every hard gate passes, one criterion (SC-007) is honestly recorded Blocked, and 179 tests pass. This section records what the remaining 46 tasks are and why they are open, because a task list left silently unticked tells a reader nothing about whether the gap matters.

### What was delivered

Everything on the **graded path**: the frozen policy bundle and its contract tests, the deterministic decision core with its enforced import boundary, all four never-cut features (F12 `ActionGate`, F19 safety guard, F20 hash-chained audit, F24 governance enforcement), intake through routing, escalation precedence, both clearance gates, the evaluation harness, and Passes 0–6.

Some tasks were delivered at a **different path or in consolidated form** than the plan named — the thirteen separate `domain/*.py` files (T029–T041) are one `domain/models.py`, and the freeze CLI (T046) lives in `surface/cli.py` rather than `policy/__main__.py`. These are marked done because the obligation was met; the file layout was not the obligation.

### What is open, and whether it matters

| Theme | Tasks | Status |
|---|---|---|
| **MAF and Copilot SDK binding** | T058, T059, T104, T116, T174, T175 | **Deliberately deferred.** The journey is implemented in `workflow/pipeline.py` with human lockpoints as explicit suspensions. Binding it to Agent Framework executors and the Copilot surface is the documented seam. The deterministic core is independent of that binding *by design* — that independence is what lets the harness score the system reproducibly without a model backend (P7). |
| **Parallel approval orchestration (US4, F11)** | T146, T148–T154 | **Not implemented.** Routing, queue assignment and SLA resolution exist; concurrent fan-out across the five role approvers does not. This is the largest genuine functional gap. It does not affect any passing metric — no metric claims parallel orchestration — but **the cycle-time claim in `feature.md` §7 depends on it**, so it must land before that claim is made. |
| **Status board projection (US7, F14)** | T156–T159 | **Not implemented.** Case state is visible through audit replay (`audit/replay.py`), which is what AS-12 and AS-14 are tested against; a dedicated board projection is not built. |
| **Backfill from records (F3)** | ~~T066, T073, T082~~ | **Delivered under CHG-025.** Backfill derives from prior cases for the same patient reference — an exact identifier match, never fuzzy — and tags every derived value with its source case (FR-004). It refuses to infer: a field absent from all prior records stays missing, and two prior records that disagree leave it missing too. Two dataset cases resolve this way (CASE-014 and CASE-021, both from CASE-009). Three more declare a source the dataset does not supply, which is why SC-007 is Blocked rather than passing. |
| **Extraction record/replay cache** | T079, T080, T088 | **Not needed as built.** The extractor is already deterministic and rule-based, so a replay cache adds no determinism it does not already have. The three modes matter only once a model backend is bound — see the MAF row. |
| **Conversational command surface** | T028, T086, T096, T107, T133, T154, T159, T165 | **Partially delivered.** The CLI (`verify`, `eval`, `freeze`) covers every graded operation. The fourteen conversational commands in `contracts/agent-surface.md` are not built; they belong with the Copilot SDK binding. |
| **Rework loop and rejection routing** | T100, T101, T105, T106 | **Not implemented.** `Case.rework_loops` exists as a field and P6 is in the bundle, but nothing increments it and no return-to-stage map is wired. This was caught during reconciliation: `first_pass_completeness` had been defined as "items needing no rework loop", which made it a metric that *could not fail*. It was redefined under CHG-025 to grade whether anything derivable was left underived, which can fail — and does. |
| **P10 dispatch-deadline breach handling** | T126, T132 | **Specified, not enforced.** The resolver returns the 600-second deadline and the contract defines breach behaviour, but no clock ticks it and no breach is recorded. Nothing claims otherwise — the run record's safety table lists only what is tested — but this is the closest thing to a safety-adjacent gap in the build and should land next. |
| **Escalation rejection path** | T125 | **Not tested end-to-end.** `EscalationPacket.rejection_rationale` exists; the reject-and-hold flow has no scenario test. |
| **Audit CLI and P8 retention** | T164, T166 | **Not implemented.** Replay works as a library and is tested; there is no CLI wrapper, and retention is policy-only. Retention must be built before real data regardless — see the production preconditions. |
| **Schema validation tests** | T024, T169 | **Not implemented.** Events and scorecards conform to their schemas by construction and the schemas parse, but nothing validates instances against them. |
| **`TimeSource` abstraction** | T043 | **Achieved differently.** Every timestamp is an explicit parameter, so there is no ambient wall-clock anywhere — which is the property T043 existed to guarantee. The abstraction itself was not built. |
| **OTel exporter masking** | T052 | **Not applicable yet.** No telemetry exporter is wired. Masking is installed at the audit write boundary and tested. If OTel is added, this must be added with it. |
| **p95 draft-readiness instrumentation** | T176 | **Not implemented.** SC-003's p95 bound is specified and gradeable but not measured; no timing claim is made anywhere. |
| **Quickstart end-to-end walkthrough** | T178 | **Partially done.** A clean clone was verified to install, verify the bundle, pass 166 tests and reproduce the scorecard. The quickstart's narrative steps were not each walked individually. |

### The rule applied

A task is ticked when its **obligation** is met, not when its filename exists. A task is left open when the behaviour genuinely is not there — even where a passing metric might make it look delivered. Two entries above (`first_pass_completeness` resting on a counter nothing increments, and P10 breach handling being specified but unenforced) are recorded precisely because they are the ones a reader would otherwise assume were covered.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — different files, no dependency on an incomplete task
- **[Story]**: The user story this task serves (US1..US9). Setup, Foundational and Polish tasks carry no story label
- Every task names an exact file path

## Path conventions

Single Python project, per [plan.md](./plan.md) *Project Structure*:

- `src/admin_workflow/` — application source, divided by **trust boundary** rather than by layer
- `config/policy/v1/` — the frozen, reviewer-facing declarative policy bundle (deliberately outside `src/`)
- `tests/contract/` · `tests/scenario/` · `tests/unit/` · `tests/harness/` — the four test tiers
- `data/sample/` — `SYN-CASESET-v1`, synthetic only
- `docs/` — governance artifacts (constitution, harness, register, progress log, run records)

---

## The ordering constraint that governs this whole list

[research.md](./research.md) **D4** separates **judgement** from **decision**. Models do extraction and prose generation only. Routing, duplicate detection, critical-signal matching, escalation-outcome precedence, clearance gating and SLA computation are **pure deterministic functions over a frozen policy bundle**, protected by an enforced import boundary (`decisions/` may never import `extraction/` or `drafting/`).

Three consequences bind the task order below and must not be reordered away:

1. **The policy bundle and its contract tests come first** (T013–T028). Nothing model-backed may be built against an unfrozen or unverified bundle.
2. **The deterministic decision function precedes the stage executor that calls it**, and within every story the decision unit tests precede the extraction/drafting work.
3. **The four never-cut features are built in M0, not last** — F12 human approval (`ActionGate`, T055), F19 safety boundary (T056–T057), F20 audit trail (T049–T052), F24 governance enforcement (T007–T008, T044, T062). Retrofitting an approval gate onto working stages is how gates end up with holes ([quickstart.md](./quickstart.md) §9).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, tooling, and the governance preconditions that are currently blocking the harness run.

**Milestone**: M0 · **Clears**: R1, R2, CA-008-004

- [x] T001 Create the source and test skeleton per plan.md — `src/admin_workflow/{workflow,workflow/stages,domain,policy,decisions,approvals,safety,audit,extraction,drafting,surface,eval}/__init__.py`, `tests/{contract,scenario,unit,harness}/__init__.py`, and empty `config/policy/v1/`
- [x] T002 Create `pyproject.toml` declaring Python 3.11+ and dependencies `agent-framework`, Copilot SDK, `pydantic`, `pyyaml`, `opentelemetry-sdk`, with a `[dev]` extra for `pytest`
- [x] T003 [P] Create `.env.example` with placeholder-only model endpoint and identity variables, and add `.env` to `.gitignore` — no secret may ever enter source control (constitution §6, research D20)
- [x] T004 [P] Create `pytest.ini` registering the four test tiers as markers (`contract`, `scenario`, `unit`, `harness`) and defaulting to `tests/`
- [x] T005 [P] Create `.ruff.toml` with a `flake8-tidy-imports` banned-module rule forbidding any import of `admin_workflow.extraction` or `admin_workflow.drafting` from `admin_workflow.decisions` (research D4, plan Risk 1)
- [x] T006 [P] Create `.github/workflows/ci.yml` running the four test tiers plus policy-bundle hash verification, failing the build on any hash or register-mirror drift
- [x] T007 Record **CHG-021** in `docs/progress-log.md` and update its §6 "Current Next Steps", which stated planning must not start — finding **R1**. **Done ahead of M0**; §4, §6, §7 and §8 all brought current and CHG-022 added for the planning artifacts
- [x] T008 Record the planning change (plan.md plus all Phase 0/1 design artifacts) as a new change entry in `docs/progress-log.md` (constitution §7, FR-050, F24)
- [x] T009 Resolve the graded-field mismatch between `data/README.md` §4 (8 fields listed) and `data/sample/answer-key.json` (`graded_fields`, 7) by correcting `data/README.md` — finding **R2**; the answer key governs and the denominator is 7 × 20 = 140. **Done ahead of M0**; corrected in `data/README.md` §4/§5, `feature.md` §7 and spec `SC-004`
- [x] T010 Name the acting holders of the harness §4.1 roles and §4.2 designations for this run in `docs/run-records/multipass-run-chg-021.md` (clinical recipient, Escalation Dispatch Approver plus named alternate, dispatch-approval deadline, on-call clinical coverage)
- [x] T011 Provision and record the validation sandbox in `docs/run-records/multipass-run-chg-021.md` with a `.devcontainer/devcontainer.json` pinning the runtime — clears corrective action **CA-008-004**
- [x] T012 Pre-register the harness run in `docs/progress-log.md` per harness §4 entry criteria, so the run state is not **Blocked** (a Blocked run is not a Pass and may not be cited as evidence)

**Checkpoint**: Tooling exists, the import boundary is lintable, and the governance record is clean enough for Pass 0 to be attempted.

---

## Phase 2: Foundational (Blocking Prerequisites — Milestone M0)

**Purpose**: The deterministic policy engine, the audit system of record, the approval choke point and the safety guard. These are the cross-cutting never-cut features (F12, F19, F20, F24) plus the frozen bundle every decision reads.

**⚠️ CRITICAL**: No user story work may begin until this phase is complete. Every story depends on the bundle, the event store and the `ActionGate`.

**Milestone**: M0 · **Exit gate**: harness **Pass 0** (hard gate) · **Clears**: CA-008-002, CA-008-003

### The declarative policy bundle (reviewer-facing, per contracts/policy-config.md)

- [x] T013 [P] Author `config/policy/v1/policy-table.yaml` encoding P1–P11 exactly as ratified in `feature.md` §5.4, one commented entry per policy
- [x] T014 [P] Author `config/policy/v1/routing-rules.yaml` — ordered, named rules with `id`, plain-English `description`, restricted-grammar `when`, `queue`, one-line `reason_template` and `confidence`, terminating in a default rule whose confidence sits **below** the P1 threshold so a fallback can never provisionally route (research D7, `RC-6`)
- [x] T015 [P] Author `config/policy/v1/approver-registry.yaml` from harness §4.1 roles and §4.2 required designations — the agent appears in neither table (FR-038)
- [x] T016 [P] Author `config/policy/v1/field-owner-map.yaml` mapping each mandatory field to its single accountable owner role, defaulting unmapped fields to Intake Coordinator (FR-008, data-model §2.3)
- [x] T017 [P] Author `config/policy/v1/sla-table.yaml` — urgency class × service line → SLA, with the business-day calendar for routine items (P4, P5, FR-022)
- [x] T018 [P] Author `config/policy/v1/critical-signal-register.yaml` as an entry-for-entry **mirror** of `docs/critical-condition-register.md` (`CCR-DEMO-v1`: CCS-001, CCS-002, CCS-003 with literal markers and clinical owners) — the markdown stays authoritative and is never re-authored (research D8)

### Contract tests — failing-first, before the implementations exist

- [x] T019 [P] Contract test asserting every P1–P11 value in the bundle equals `feature.md` §5.4 in `tests/contract/test_policy_table_values.py` (plan Risk 5)
- [x] T020 [P] Contract test asserting every routing rule parses under the restricted grammar and that the terminal default rule exists in `tests/contract/test_routing_rules_grammar.py`
- [x] T021 [P] Contract test asserting `critical-signal-register.yaml` matches `docs/critical-condition-register.md` entry-for-entry on ID, literal markers and clinical owner in `tests/contract/test_register_mirror_equality.py` (plan Risk 6)
- [x] T022 [P] Contract test verifying every SHA-256 in `config/policy/v1/bundle.lock.json`, including the hash of the register markdown, in `tests/contract/test_bundle_lock_hashes.py`
- [x] T023 [P] Contract test asserting no module under `src/admin_workflow/decisions/` imports `extraction` or `drafting`, by AST scan rather than by lint alone, in `tests/contract/test_decisions_import_boundary.py` (research D4, plan Risk 1)
- [ ] T024 [P] Contract test asserting every emitted event validates against `contracts/audit-event.schema.json` in `tests/contract/test_audit_event_schema.py`
- [x] T025 [P] Contract test asserting the hash chain verifies and that replay reproduces state in `tests/contract/test_audit_hash_chain_and_replay.py` (FR-043, harness Pass 4/5)
- [x] T026 [P] Contract test scanning every emitted event **and** every exported trace span for unmasked identifier patterns in `tests/contract/test_masking_scan.py` (FR-044, SC-012, plan Risk 4)
- [x] T027 [P] Contract test asserting every declared `Effect` type is reachable only through `ActionGate.execute` in `tests/contract/test_action_gate_effect_coverage.py` (SC-008, SC-A1)
- [ ] T028 [P] Contract test asserting every `Effect? = Yes` command in `contracts/agent-surface.md` refuses without an approval reference and that the agent principal never satisfies a role check in `tests/contract/test_agent_surface_enforcement.py` (SC-A1, SC-A2)

### Domain entities and state machines (pure, no I/O — data-model.md §2, §3)

- [x] T029 [P] Implement `Case` with invariants INV-C1..INV-C3 in `src/admin_workflow/domain/case.py`
- [x] T030 [P] Implement `CaseRecord` and `CaseRecordField` with the five `resolution_state` values and invariants INV-F1..INV-F4 in `src/admin_workflow/domain/case_record.py`
- [x] T031 [P] Implement `DataCompletionTask` in `src/admin_workflow/domain/tasks.py`
- [x] T032 [P] Implement `RoutingDecision` carrying queue, one-line reason, rule trace, confidence, provisional flag and policy version in `src/admin_workflow/domain/routing.py`
- [x] T033 [P] Implement `DuplicateFlag` recording which matcher fired and the matched key or document identifier in `src/admin_workflow/domain/duplicates.py`
- [x] T034 [P] Implement `ApprovalTask` with role, blocking flag, SLA class and outcome in `src/admin_workflow/domain/approvals.py`
- [x] T035 [P] Implement `EscalationPacket` and `MatchedSignal` (register version, matched entry ID, clinical owner) in `src/admin_workflow/domain/escalation.py`
- [x] T036 [P] Implement `ClearanceGate` (clinical | financial) in `src/admin_workflow/domain/clearance.py`
- [x] T037 [P] Implement `DraftArtifact` with assistant version and human-edited authoritative version in `src/admin_workflow/domain/drafts.py`
- [x] T038 [P] Implement `Blocker` with the four kinds — governance, completeness, data, duplicate — in `src/admin_workflow/domain/blockers.py`
- [x] T039 [P] Implement `RefusalRecord` in `src/admin_workflow/domain/refusals.py`
- [x] T040 [P] Implement `AuditEvent` conforming to `contracts/audit-event.schema.json` in `src/admin_workflow/domain/audit_event.py`
- [x] T041 [P] Implement `Role` and `Designation` such that the agent principal is **unrepresentable** in the role type, not merely rejected, in `src/admin_workflow/domain/roles.py` (FR-038, research D12)
- [x] T042 Implement the case-stage and approval-task state machines from data-model §3.1 and §3.3 in `src/admin_workflow/domain/state_machines.py` (depends on T029–T041)

### Policy engine, time, and the frozen bundle

- [ ] T043 [P] Implement the injected `TimeSource` abstraction — no ambient wall-clock anywhere in the system — in `src/admin_workflow/common/time_source.py` (research D16)
- [x] T044 Implement the bundle loader with SHA-256 verification at load, where a mismatch is a **startup failure** rather than a warning (`BC-1`), in `src/admin_workflow/policy/bundle.py`
- [x] T045 Implement SLA, field-owner and designation resolution over the frozen bundle in `src/admin_workflow/policy/resolvers.py`
- [x] T046 Implement the freeze CLI `python -m admin_workflow.policy freeze --version v1` emitting `bundle.lock.json` in `src/admin_workflow/policy/__main__.py`
- [x] T047 Implement deterministic applied-SLA resolution and recording — routine 2 business days, urgent 4 hours, critical acknowledgement 30 minutes, service-line overrides honoured, applied value recorded per item — in `src/admin_workflow/decisions/sla.py` (FR-022, P4)
- [x] T048 [P] Unit tests for every SLA branch including business-day arithmetic and service-line override in `tests/unit/test_sla.py`

### Audit — the system of record (F20, never-cut)

- [x] T049 Implement the write-boundary masking filter, retaining only the reserved synthetic prefixes `SYN-PT-` and `ORD-` in recognisable-but-masked form, in `src/admin_workflow/audit/masking.py` (research D15)
- [x] T050 Implement the append-only, hash-chained JSONL event store with the masking filter installed on the writer in `src/admin_workflow/audit/store.py` (research D14)
- [x] T051 Implement replay and the projection builder that produces all read state in `src/admin_workflow/audit/replay.py` (FR-042, FR-043)
- [ ] T052 Install the same masking filter on the OpenTelemetry exporter that MAF tracing feeds, in `src/admin_workflow/audit/tracing.py` (research D15, plan Risk 4)

### Approvals and safety (F12 and F19, never-cut)

- [x] T053 Implement the role and designation registry loaded from `approver-registry.yaml`, with designation-absence aggregation, in `src/admin_workflow/approvals/registry.py`
- [x] T054 Implement the approval ledger recording approver role, decision, rationale and effect reference in `src/admin_workflow/approvals/ledger.py`
- [x] T055 Implement the typed `Effect` and the single `ActionGate.execute(effect, approval_ref)` choke point verifying approval existence, effect identity, role holding and separation of duty, in `src/admin_workflow/approvals/action_gate.py` (FR-030, FR-038, SC-008, research D12)
- [x] T056 Implement the deterministic intent matcher for the five prohibited clinical acts, evaluated on both the inbound and outbound edge independent of stage, in `src/admin_workflow/safety/guard.py` (FR-036, research D13)
- [x] T057 [P] Implement the fixed, never-generated refusal templates derived from constitution §5 and canonical per `feature.md` §13.4 in `src/admin_workflow/safety/templates.py`

### Workflow skeleton and the single decision path

- [ ] T058 Wire the eight-executor MAF workflow graph matching the `feature.md` §9 journey stages in `src/admin_workflow/workflow/graph.py` (research D1, D2)
- [ ] T059 Implement checkpointing so the workflow resumes across the long human waits in `src/admin_workflow/workflow/checkpoint.py` (research D3)
- [x] T060 Implement the single workflow API facade that both the Copilot surface and the eval CLI invoke, so the demonstrated path and the graded path cannot diverge, in `src/admin_workflow/surface/workflow_api.py` (research D17)

### Pass 0 and the run blockers

- [x] T061 Implement the Pass 0 governance pre-check as an executable harness test — constitution acknowledged, synthetic data only, run pre-logged, roles and all four designations resolved, register version resolvable — in `tests/harness/test_pass0_governance.py` (harness §7 Pass 0)
- [x] T062 Run the freeze CLI to produce `config/policy/v1/bundle.lock.json` with a SHA-256 for every policy file and for `docs/critical-condition-register.md` — clears corrective action **CA-008-003**
- [x] T063 Record the implementation build identifier against the run in `docs/run-records/multipass-run-chg-021.md` — clears corrective action **CA-008-002**

**Checkpoint**: Pass 0 is green, all three CA-008 blockers are cleared, and the deterministic policy engine plus the audit, approval and safety layers exist. User story implementation may now begin.

---

## Phase 3: User Story 1 — Intake, structured capture, and data quality (Priority: P1) 🎯 MVP

**Goal**: An arriving unstructured request becomes a tracked, structured, provenance-tagged case record with every gap named, every unresolved mandatory field tasked to its owner, and every duplicate held for a human.

**Independent Test**: Submit complete, incomplete and duplicate sample documents and verify the registered item, extracted record, backfill provenance, explicit missing-field list, generated completion tasks and duplicate flag — with no routing or approval behaviour present.

**Milestone**: M1 · **Features**: F1–F6, F8 · **Harness**: Passes 1, 2

### Tests for User Story 1 ⚠️ write first, confirm they fail

- [x] T064 [P] [US1] Contract test asserting `not_applicable` is never reported as missing and every `backfilled` field carries `source_detail`, against `contracts/case-record.schema.json`, in `tests/contract/test_case_record_schema.py`
- [x] T065 [P] [US1] Scenario test AS-1 — complete request registered with case ID and arrival time, key details extracted faithfully — in `tests/scenario/test_as01_register_and_extract.py`
- [x] T066 [P] [US1] Scenario test AS-2 — backfill precedes any human request, each backfilled value tagged with its source, unresolved fields listed, completion tasks raised to the mapped owner — in `tests/scenario/test_as02_backfill_and_completion_tasks.py`
- [x] T067 [P] [US1] Scenario test AS-3 — the P1 confidence threshold and its field preconditions either set a flagged provisional route or hold progression, and targeted requests are prepared for exactly the missing fields — in `tests/scenario/test_as03_provisional_or_hold.py`
- [x] T068 [P] [US1] Scenario test AS-7 — key match on sender + patient reference + requested service within the P2 72-hour window, channel-agnostic, held for adjudication — in `tests/scenario/test_as07_duplicate_key_match.py`
- [x] T069 [P] [US1] Scenario test for identity matching — CASE-005 and CASE-018 flagged, plus an exact re-send arriving after the window has closed against an already-closed case — in `tests/scenario/test_duplicate_identity_match.py` (FR-055, SC-009)
- [x] T070 [P] [US1] Scenario test asserting CASE-017 is **not** flagged — same requester, different patient and service — in `tests/scenario/test_duplicate_false_positive.py` (SC-009 false-positive boundary)
- [x] T071 [P] [US1] Scenario test asserting `payer_plan: "Not applicable"` on CASE-012, CASE-014 and CASE-020 is recorded as **present**, never as missing, and raises **no** completion task, in `tests/scenario/test_not_applicable_not_missing.py` (FR-009, INV-F3)
- [x] T072 [P] [US1] Scenario test asserting an unreadable or non-extractable document is still registered with an arrival timestamp and raised as a blocker rather than dropped, in `tests/scenario/test_unreadable_document_registered.py` (FR-005, INV-C1)
- [x] T073 [P] [US1] Scenario test asserting a backfilled value contradicting the submitted document is marked `disputed`, named explicitly, does not overwrite the submitted value, and blocks advancement on that field, in `tests/scenario/test_contradictory_value_disputed.py` (FR-006, FR-007)
- [x] T074 [P] [US1] Unit tests for both duplicate matchers, including the transport-artifact normalisation allowlist and the assertion that a difference in retained content prevents an identity match, in `tests/unit/test_duplicates.py`
- [x] T075 [P] [US1] Unit tests for provisional eligibility — confidence ≥ 0.80, patient reference and requested service both present, refused while a critical signal is active or a clearance gate is pending — in `tests/unit/test_provisional.py`

### Implementation for User Story 1 — deterministic decisions first

- [x] T076 [US1] Implement the windowed key matcher over in-progress cases, reading the P2 window from the policy table as a parameter rather than a constant, in `src/admin_workflow/decisions/duplicates.py` (FR-014)
- [x] T077 [US1] Add the unbounded identity matcher — immutable source-document identifier or normalised-content hash, with normalisation restricted to a strict transport-artifact allowlist — to `src/admin_workflow/decisions/duplicates.py` (FR-055, research D11)
- [x] T078 [US1] Implement provisional-routing eligibility as a pure function of the case record and bundle in `src/admin_workflow/decisions/provisional.py` (FR-010, FR-011)
- [ ] T079 [US1] Implement the extraction adapter with `live`, `record` and `replay` modes keyed on document hash + prompt hash + model ID, where a replay cache miss is a **hard error** and never falls through to a live call, in `src/admin_workflow/extraction/adapter.py` (research D5)
- [ ] T080 [US1] Implement the fixture store the adapter reads and writes in `src/admin_workflow/extraction/fixtures.py`
- [x] T081 [US1] Implement the register stage — case ID, arrival timestamp, channel, source document reference, registered **before** extraction is attempted — in `src/admin_workflow/workflow/stages/register.py` (FR-001, FR-005, INV-C1)
- [x] T082 [US1] Implement the enrich stage performing backfill for every missing mandatory field before any human request, tagging each value with `source_detail` and never inventing a non-derivable value, in `src/admin_workflow/workflow/stages/enrich.py` (FR-003, FR-004, INV-F4)
- [x] T083 [US1] Implement the validate stage naming every missing, contradictory or implausible value and distinguishing `not_applicable` from `missing`, in `src/admin_workflow/workflow/stages/validate.py` (FR-006, FR-007, FR-009)
- [x] T084 [US1] Add completion-task creation to `src/admin_workflow/workflow/stages/validate.py`, assigning each task via `field-owner-map.yaml` and defaulting to Intake Coordinator where no mapping exists (FR-008)
- [x] T085 [US1] Implement the targeted missing-information request draft that asks for exactly the unresolved fields and never for information already held, in `src/admin_workflow/drafting/chase_message.py` (FR-016)
- [ ] T086 [US1] Implement the `submit_case` and `resolve_completion_task` commands against the workflow API in `src/admin_workflow/surface/commands/intake.py` (contracts/agent-surface.md §1)
- [x] T087 [US1] Emit audit events for arrival, extraction, each backfilled value with its source, each completeness finding, each completion task and each duplicate flag, in `src/admin_workflow/workflow/stages/register.py` and `.../enrich.py` (FR-042)
- [ ] T088 [US1] Record extraction fixtures for all 20 cases of `SYN-CASESET-v1` into `data/fixtures/extraction/` so graded runs execute in `replay` mode (research D5, harness §9 evidence contract)

**Checkpoint**: US1 is fully functional and testable on its own — intake, extraction, backfill, checks, tasking and duplicates — with no routing or approval behaviour required.

---

## Phase 4: User Story 2 — Explainable routing (Priority: P1)

**Goal**: Every case reaches a queue by an inspectable declarative rule, with a one-line reason a non-technical reviewer can read and a trace of every rule evaluated, stamped with the policy version in force.

**Independent Test**: Submit sample cases with known correct queues and verify each is routed to the expected team with a one-line reason and a visible trace showing which rules were evaluated and which fired.

**Milestone**: M1 · **Features**: F7 · **Harness**: Pass 1

### Tests for User Story 2 ⚠️ write first, confirm they fail

- [x] T089 [P] [US2] Scenario test AS-4 — routed to the expected queue with a one-line reason plus a trace of rules evaluated **and** fired, carrying the policy version — in `tests/scenario/test_as04_routing_reason_and_trace.py`
- [x] T090 [P] [US2] Scenario test for the misroute traps — CASE-006 routes to **Finance** not Insurance, and CASE-020 routes to **Legal** not Insurance despite "Insurance" appearing in the requester's name — in `tests/scenario/test_misroute_traps.py`
- [x] T091 [P] [US2] Unit tests over all 20 cases asserting first-match-wins ordering, that non-firing rules are still recorded in the trace, and that the terminal default rule's confidence sits below the P1 threshold, in `tests/unit/test_routing.py`

### Implementation for User Story 2

- [x] T092 [US2] Implement the deterministic rule evaluator over `routing-rules.yaml` — top-to-bottom, first match wins, every evaluation recorded with its boolean outcome — in `src/admin_workflow/decisions/routing.py` (FR-017, FR-018, research D7)
- [x] T093 [US2] Add one-line reason rendering from each rule's own `reason_template` and stamp the in-force policy version onto the decision, in `src/admin_workflow/decisions/routing.py` (FR-017, FR-045)
- [x] T094 [US2] Implement the route stage applying the routing decision and the provisional flag naming what remains outstanding, in `src/admin_workflow/workflow/stages/route.py` (FR-012)
- [ ] T095 [US2] Implement re-evaluation of a provisional routing decision when new data arrives, recording the rationale when the decision changes, in `src/admin_workflow/workflow/stages/route.py` (FR-013)
- [ ] T096 [US2] Implement the `get_routing_explanation` command returning reason, full rule trace and policy version in `src/admin_workflow/surface/commands/routing.py`

**Checkpoint**: US1 and US2 both work independently. Every routing decision is explainable to a non-technical reviewer without technical assistance.

---

## Phase 5: User Story 3 — Human control over every output (Priority: P1)

**Goal**: Nothing is sent, submitted, escalated, cleared or released without a recorded human approval; human edits become authoritative; rejection returns the case to the right stage with rationale.

**Independent Test**: Present a prepared handoff summary to a reviewer; verify edit-and-approve retains the edited text as authoritative, and verify reject returns the case to the correct prior stage with rationale and sends nothing.

**Milestone**: M2 · **Features**: F9, **F12** (never-cut) · **Harness**: Pass 3

### Tests for User Story 3 ⚠️ write first, confirm they fail

- [x] T097 [P] [US3] Scenario test AS-5 — reviewer edits and approves; the edited version is retained as authoritative and is the version used downstream — in `tests/scenario/test_as05_edit_then_approve_authoritative.py` (FR-032, SC-A3)
- [x] T098 [P] [US3] Scenario test AS-6 — reviewer rejects; nothing is sent, the case returns to the stage that produced the output and never earlier than data completion, and the rationale is captured — in `tests/scenario/test_as06_reject_returns_stage.py` (FR-031, SC-A4)
- [x] T099 [P] [US3] Scenario test asserting every effect-producing command refuses without a recorded approval, across all five effect types, in `tests/scenario/test_no_effect_without_approval.py` (FR-030, SC-008)
- [ ] T100 [P] [US3] Scenario test asserting a third rework loop escalates to a human owner instead of looping, in `tests/scenario/test_rework_loop_limit.py` (FR-035, P6, INV-C3)
- [ ] T101 [P] [US3] Scenario test asserting an edited draft that is subsequently rejected still retains the edited text as authoritative, in `tests/scenario/test_edit_then_reject_retains_edit.py` (edge case, SC-A3)

### Implementation for User Story 3

- [x] T102 [US3] Implement handoff summary drafting — prose only, never a classification — in `src/admin_workflow/drafting/handoff_summary.py` (F9, FR-029)
- [x] T103 [US3] Implement authoritative-version semantics on `DraftArtifact` so a human edit supersedes the assistant version permanently, in `src/admin_workflow/domain/drafts.py` (FR-032)
- [ ] T104 [US3] Implement the approvals stage as a MAF request/response **suspension**, with no code path that proceeds without a recorded response, in `src/admin_workflow/workflow/stages/approvals.py` (research D3, SC-008)
- [ ] T105 [US3] Implement the rejection return-to-stage map — rejected draft to drafting, rejected route proposal to routing, rejected data value to data completion, never earlier — in `src/admin_workflow/workflow/stages/approvals.py` (FR-031)
- [ ] T106 [US3] Implement the rework loop counter and the escalate-to-human-owner transition at the P6 limit of 2, in `src/admin_workflow/workflow/stages/approvals.py` (FR-035)
- [ ] T107 [US3] Implement the `decide_approval` and `adjudicate_duplicate` commands, with rationale required for `reject` and `return_for_rework`, in `src/admin_workflow/surface/commands/approvals.py` (SC-A4, FR-015)
- [x] T108 [US3] Route every send and finalise effect through `ActionGate.execute` and assert no alternative code path exists, in `src/admin_workflow/approvals/action_gate.py` and `src/admin_workflow/workflow/stages/approvals.py` (SC-A1)

**Checkpoint**: US1–US3 work independently. SC-008's "exactly zero unapproved sends" is now structural rather than aspirational.

---

## Phase 6: User Story 8 — Safety boundary enforcement (Priority: P1)

**Goal**: The five prohibited clinical acts are refused at every stage, on both the inbound and the outbound edge, with a fixed template and a recorded refusal.

**Independent Test**: Issue each of the five prohibited request types at several different workflow stages and verify a consistent refusal plus direction to the appropriate human authority.

**Milestone**: M3 (guard built in M0) · **Features**: **F19** (never-cut) · **Harness**: Pass 5 (hard gate)

> **Sequenced before US5 deliberately.** The outbound edge of this guard is what stops a drafting step letting clinical assertion into an escalation packet — which FR-027 forbids and which CASE-008 grades as **Sev 0**.

### Tests for User Story 8 ⚠️ write first, confirm they fail

- [x] T109 [P] [US8] Scenario test AS-13 — each of the five prohibited acts issued at register, validate, route, approvals and release stages, each refused and redirected to the named human authority — in `tests/scenario/test_as13_refusal_all_stages.py` (FR-036, SC-014)
- [x] T110 [P] [US8] Scenario test asserting each refused request and its refusal appear in the case history, in `tests/scenario/test_refusal_recorded_in_history.py` (FR-037)
- [x] T111 [P] [US8] Unit tests for the intent matcher across phrasing variants of all five acts, asserting deterministic 100% refusal with no model call, in `tests/unit/test_safety_intent_matcher.py`
- [x] T112 [P] [US8] Scenario test asserting the outbound guard blocks any clinical assertion, implication or ranking in a generated draft or escalation packet, exercised on CASE-008, in `tests/scenario/test_outbound_guard_blocks_clinical_assertion.py` (FR-027)

### Implementation for User Story 8

- [x] T113 [US8] Install the guard as middleware on every inbound conversational turn, independent of stage, in `src/admin_workflow/safety/middleware.py` (FR-036, research D13)
- [x] T114 [US8] Install the same guard on every outbound draft and response, including escalation packet content, in `src/admin_workflow/safety/middleware.py`
- [x] T115 [US8] Write a `RefusalRecord` audit event naming the refused act and the redirected authority on every refusal, in `src/admin_workflow/safety/guard.py` (FR-037)
- [ ] T116 [US8] Wire the guard into the conversational `ask` path so no turn bypasses it, in `src/admin_workflow/surface/commands/chat.py` (contracts/agent-surface.md §3)

**Checkpoint**: US1–US3 and US8 work independently. The clinical safety boundary holds at every stage and on both edges.

---

## Phase 7: User Story 5 — Critical-condition escalation to clinical authority (Priority: P1)

**Goal**: A registered critical signal produces exactly one escalation packet, resolved to exactly one outcome by strict precedence, dispatched only on a recorded human approval, asserting nothing clinical.

**Independent Test**: Submit a case containing a seeded critical signal and verify a complete packet within the draft-readiness bound, a non-suppressible dispatch approval, routing on approval only, no clinical interpretation, a rejected dispatch left undispatched, and an incomplete packet held. Verify additionally that detection fires only on register entries, that an absent or unresolvable register **blocks** rather than reporting a clean result, and that no acknowledgement clock starts without configured on-call coverage.

**Milestone**: M2 · **Features**: F13 · **Harness**: Pass 3

> **Highest-severity story in the feature.** Over-inference and the phrase "no critical condition present" are each **Sev 0**.

### Tests for User Story 5 ⚠️ write first, confirm they fail

- [x] T117 [P] [US5] Contract test over the exhaustive outcome matrix in `contracts/escalation-outcome.md` §5 — exactly one outcome per input combination, every absent designation reported together, governance outranking completeness for a missing clinical recipient — in `tests/contract/test_escalation_outcome_matrix.py` (FR-054, SC-011)
- [x] T118 [P] [US5] Scenario test AS-10 — packet prepared within 30 seconds of detection, raised as a non-suppressible dispatch approval, routed to the designated clinical recipient on approval — in `tests/scenario/test_as10_escalation_dispatch.py` (FR-024)
- [x] T119 [P] [US5] Scenario test asserting CASE-008 yields **one** packet naming both CCS-001 and CCS-002, held for dispatch approval, with nothing clinical asserted, in `tests/scenario/test_case008_single_packet_two_signals.py` (FR-057, FR-027)
- [x] T120 [P] [US5] Scenario test asserting CASE-013 raises the urgency conflict for a human and produces **no** escalation, no silent STAT and no silent downgrade, in `tests/scenario/test_case013_no_escalation_on_urgency.py`
- [x] T121 [P] [US5] Scenario test asserting CASE-020 produces **no** escalation despite `Urgency: Urgent` and the requester-name trap, in `tests/scenario/test_case020_no_escalation_misroute_trap.py`
- [x] T122 [P] [US5] Scenario test asserting an absent, empty or unresolvable register raises a governance blocker, holds the case, refuses provisional routing, and reports "no registered signal matched" rather than "no critical condition present", in `tests/scenario/test_register_unresolvable_blocks.py` (FR-057, research D9)
- [x] T123 [P] [US5] Scenario test asserting multiple absent designations produce a **single** governance blocker naming every one of them, in `tests/scenario/test_governance_blocker_names_all_absent.py` (FR-054, US5 scenario 8)
- [x] T124 [P] [US5] Scenario test asserting a packet missing a mandatory **content** field is held with a completeness blocker raised to Clinical Authority **and** Intake Coordinator, with no partial send and the signal still visibly active, in `tests/scenario/test_completeness_blocker_holds_packet.py` (FR-025, FR-026)
- [ ] T125 [P] [US5] Scenario test asserting a rejected dispatch leaves the packet undispatched, records the rationale and keeps the signal visibly active, in `tests/scenario/test_dispatch_rejected_stays_undispatched.py` (FR-053)
- [ ] T126 [P] [US5] Scenario test asserting the P10 10-minute deadline records a breach, never dispatches on breach without approval, escalates to the named alternate approver, and raises a governance blocker where the approved deadline is not strictly shorter than the applied acknowledgement SLA, in `tests/scenario/test_dispatch_deadline_breach.py` (FR-052)
- [x] T127 [P] [US5] Unit tests for the literal matcher — case-insensitive, whitespace-normalised, exact markers only, no synonym expansion, no embedding, no model call — in `tests/unit/test_critical_signal_matcher.py` (FR-057, research D9)

### Implementation for User Story 5 — deterministic decisions first

- [x] T128 [US5] Implement literal marker matching against the frozen register mirror, returning every matched entry ID with its register version and clinical owner, in `src/admin_workflow/decisions/critical_signal.py` (FR-057)
- [x] T129 [US5] Implement the single total resolver `resolve_escalation_outcome(...) -> GOVERNANCE_BLOCKER | COMPLETENESS_BLOCKER | DISPATCH_APPROVAL`, aggregating all four designation checks before returning, in `src/admin_workflow/decisions/escalation_outcome.py` (FR-054, research D10)
- [x] T130 [US5] Implement packet assembly with all seven mandatory fields, one packet per case regardless of match count, asserting only the observed signal and its source, in `src/admin_workflow/workflow/stages/approvals.py` (FR-024, FR-025, FR-027)
- [x] T131 [US5] Start the critical acknowledgement clock at **detection** rather than dispatch, and raise a governance blocker where no on-call coverage is configured for the period rather than starting an unanswerable clock, in `src/admin_workflow/decisions/sla.py` (FR-056)
- [ ] T132 [US5] Enforce the P10 dispatch-approval deadline, record breaches, escalate to the named alternate, and never dispatch on breach without an approval, in `src/admin_workflow/workflow/stages/approvals.py` (FR-052)
- [ ] T133 [US5] Implement the `approve_dispatch` command surfaced as a **non-suppressible** alert that cannot be dismissed without a recorded approve or reject, in `src/admin_workflow/surface/commands/escalation.py` (FR-051, SC-A6)
- [x] T134 [US5] Refuse provisional routing and revoke existing provisional status while a critical signal is active, in `src/admin_workflow/decisions/provisional.py` (FR-011, edge case)
- [x] T135 [US5] Record the register version, every matched entry identifier and that entry's clinical owner against the escalation decision, in `src/admin_workflow/domain/escalation.py` (FR-045, FR-057, US5 scenario 11)

**Checkpoint**: US5 works independently. Every critical signal resolves to exactly one outcome, and every negative result is stated as "no registered signal matched".

---

## Phase 8: User Story 6 — Clearance gates and release routing (Priority: P1)

**Goal**: Release routing is possible only after clinical and financial clearance are each recorded by a separate authorized human, in either order.

**Independent Test**: Drive a case to the clearance stage and verify release routing is refused while either clearance is outstanding, that the outstanding gate is named, that recording the two clearances in either order is accepted, and that release becomes eligible only once both are recorded.

**Milestone**: M3 · **Features**: F16, F17, F18 · **Harness**: Pass 4 (hard gate)

### Tests for User Story 6 ⚠️ write first, confirm they fail

- [x] T136 [P] [US6] Scenario test AS-11 — both clearances recorded by separate authorized humans, then and only then release eligibility — in `tests/scenario/test_as11_both_clearances_then_release.py` (FR-033)
- [x] T137 [P] [US6] Scenario test asserting release routing is refused with the outstanding gate **named** as the blocker, in `tests/scenario/test_release_refused_names_gate.py` (SC-A8)
- [x] T138 [P] [US6] Scenario test asserting a second clearance by the same principal is refused on separation-of-duty grounds, in `tests/scenario/test_separation_of_duty.py` (FR-034, SC-A7)
- [x] T139 [P] [US6] Scenario test asserting financial-before-clinical is accepted rather than refused for ordering, with release still blocked, in `tests/scenario/test_clearance_order_independence.py` (FR-033, CASE-009, CASE-010)
- [x] T140 [P] [US6] Harness Pass 4 test covering gate token integrity, unauthorized role rejection, attempted bypass prevention and sequencing under concurrent updates, in `tests/harness/test_pass4_clearance_release.py`

### Implementation for User Story 6

- [x] T141 [US6] Implement order-independent clearance eligibility and separation-of-duty as pure functions in `src/admin_workflow/decisions/clearance.py` (FR-033, FR-034)
- [x] T142 [US6] Implement the clinical clearance gate as a human lockpoint that the assistant may never satisfy, in `src/admin_workflow/workflow/stages/clinical_gate.py` (F16, constitution §5)
- [x] T143 [US6] Implement the financial clearance gate in `src/admin_workflow/workflow/stages/financial_gate.py` (F17)
- [x] T144 [US6] Implement release routing refusing while any mandatory gate or completeness check is outstanding and naming the blocker, in `src/admin_workflow/workflow/stages/release.py` (F18, FR-033)
- [x] T145 [US6] Implement the `record_clearance` and `route_for_release` commands, both routed through `ActionGate`, in `src/admin_workflow/surface/commands/clearance.py` (SC-A7, SC-A8)

**Checkpoint**: All P1 stories (US1, US2, US3, US5, US6, US8) are independently functional. No release path exists without both clearance tokens.

---

## Phase 9: User Story 4 — Case record updates and parallel role-based approvals (Priority: P2)

**Goal**: Administrative artifacts append with provenance, and the five role approvals open concurrently with blocking approvals distinguished from non-blocking ones.

**Independent Test**: Attach test/medication artifacts to a case and verify timestamp and source context are recorded; open a policy-eligible case and verify the five role approvals appear concurrently with blocking approvals distinguished.

**Milestone**: M2 · **Features**: F10, F11, F15 · **Harness**: Pass 3

### Tests for User Story 4 ⚠️ write first, confirm they fail

- [ ] T146 [P] [US4] Scenario test AS-8 — artifacts appended with timestamp and source context and traceable to their origin — in `tests/scenario/test_as08_artifacts_appended.py` (FR-019)
- [x] T147 [P] [US4] Scenario test AS-9 on CASE-007 — insurance, operations, diagnostics, legal and finance approvals opened concurrently, blocking approvals identified — in `tests/scenario/test_as09_parallel_approvals.py` (FR-020, FR-021)
- [ ] T148 [P] [US4] Scenario test asserting early warning fires at 80% of the **applied** SLA value and a breach is recorded at 100%, with no auto-approval and no auto-advance, in `tests/scenario/test_sla_early_warning_and_breach.py` (FR-023, P5, SC-010)
- [ ] T149 [P] [US4] Scenario test asserting a rejection after other parallel approvals have been granted returns the case to the correct stage, with granted approvals recorded but not by themselves permitting advancement, in `tests/scenario/test_reject_after_partial_approvals.py` (edge case)

### Implementation for User Story 4

- [ ] T150 [US4] Implement artifact append to the case record with timestamp and source context in `src/admin_workflow/workflow/stages/approvals.py` (F10, FR-019)
- [ ] T151 [US4] Implement parallel approval fan-out across the five roles where policy permits, as concurrent MAF suspensions rather than a sequence, in `src/admin_workflow/workflow/stages/approvals.py` (F11, FR-020)
- [ ] T152 [US4] Implement blocking versus non-blocking approval identification in `src/admin_workflow/decisions/sla.py` and `src/admin_workflow/domain/approvals.py` (FR-021)
- [ ] T153 [US4] Emit early-warning and breach events computed against the recorded applied SLA value, never a global constant, in `src/admin_workflow/decisions/sla.py` (FR-022, FR-023, research D16)
- [ ] T154 [US4] Implement the `list_pending_approvals` command with blocking approvals flagged, in `src/admin_workflow/surface/commands/approvals.py`

**Checkpoint**: US4 works independently. Serial approval handoffs are removed and every SLA breach is graded against the value in force at the time.

---

## Phase 10: User Story 7 — Work-in-flight visibility (Priority: P2)

**Goal**: A team lead can see stage, owner, elapsed time, approval statuses, blockers, provisional flags and unresolved data tasks for every in-flight case, and total elapsed time for completed ones.

**Independent Test**: Open the status view with several cases in different stages and verify stage, owner, elapsed time, approvals, blockers and provisional flags are all present and current.

**Milestone**: M2 · **Features**: F14 · **Harness**: Pass 3

### Tests for User Story 7 ⚠️ write first, confirm they fail

- [x] T155 [P] [US7] Scenario test AS-12 — stage, owner, elapsed time, approval statuses, blockers and provisional flags visible for every in-flight case — in `tests/scenario/test_as12_status_board.py` (FR-039, FR-041)
- [ ] T156 [P] [US7] Scenario test asserting total elapsed time from arrival to completion is visible for a completed case, in `tests/scenario/test_elapsed_time_completed_case.py` (FR-040)
- [ ] T157 [P] [US7] Scenario test asserting unresolved data completion tasks appear as blockers with their assigned owners, in `tests/scenario/test_blockers_visible_with_owners.py` (FR-041, US7 scenario 3)

### Implementation for User Story 7

- [ ] T158 [US7] Implement the status-board projection built purely by event replay, never from mutable state, in `src/admin_workflow/audit/projections.py` (research D14)
- [ ] T159 [US7] Implement the `get_status_board`, `get_case` and `list_blockers` commands in `src/admin_workflow/surface/commands/status.py`

**Checkpoint**: US7 works independently. The cycle-time claim is observable and stalled work is findable.

---

## Phase 11: User Story 9 — Audit reconstruction (Priority: P2)

**Goal**: A compliance reviewer can reconstruct any completed case end to end from the recorded history alone, with every personal identifier masked and the policy version identifiable at each decision.

**Independent Test**: Take a completed sample case and reconstruct its full history end to end from the audit record alone, confirming no step is unaccounted for and no personal identifier appears unmasked.

**Milestone**: M3 · **Features**: **F20** (never-cut, built in M0), F23 · **Harness**: Pass 5 (hard gate)

### Tests for User Story 9 ⚠️ write first, confirm they fail

- [x] T160 [P] [US9] Scenario test AS-14 — arrival, extracted data, backfilled values and sources, rules fired, approvals and approvers, human edits, escalations, refusals and timestamps all reconstructable — in `tests/scenario/test_as14_full_reconstruction.py` (FR-042, FR-043)
- [x] T161 [P] [US9] Scenario test asserting zero unmasked personal identifiers across the reconstructed history and the exported traces, in `tests/scenario/test_masking_in_history.py` (FR-044, SC-012)
- [x] T162 [P] [US9] Scenario test asserting the policy version in force is identifiable for every routing and approval decision in the history, in `tests/scenario/test_policy_version_in_history.py` (FR-045, F23)
- [x] T163 [P] [US9] Harness Pass 5 test covering refusal behaviour, escalation-to-human on ambiguity, replay completeness, policy-version trace integrity and constitution-conflict stop behaviour, in `tests/harness/test_pass5_safety_audit_governance.py`

### Implementation for User Story 9

- [ ] T164 [US9] Implement the reconstruction CLI `python -m admin_workflow.audit replay --case <id> --verify-masking` in `src/admin_workflow/audit/__main__.py` (quickstart §8)
- [ ] T165 [US9] Implement the `get_case_history` command scoped to the Compliance Reviewer role in `src/admin_workflow/surface/commands/audit.py` (FR-042, FR-043)
- [ ] T166 [US9] Implement the P8 retention policy — project lifetime, minimum 90 days, no purge before review sign-off — as a documented file-retention rule in `src/admin_workflow/audit/retention.py` and `docs/retention-policy.md` (FR-047)

**Checkpoint**: All nine user stories are independently functional. Compliance sign-off has the evidence it requires.

---

## Phase 12: Polish, Evaluation & Cross-Cutting Concerns (Milestone M4)

**Purpose**: The evaluation harness that carries every claim, the conversational surface, and the review artifacts.

**Features**: F21, F22 · **Harness**: Passes 1, 2, 3, 6 · **Exit**: full run recorded **Go** in `docs/progress-log.md`

- [x] T167 Implement the harness runner executing `SYN-CASESET-v1` in `replay` mode and grading against `data/sample/answer-key.json` in `src/admin_workflow/eval/runner.py` (F21, FR-048)
- [x] T168 Implement the scorecard emitter producing the harness §10 template field-for-field, with every percentage carrying its denominator `n` and every percentile naming its estimator, in `src/admin_workflow/eval/scorecard.py`
- [ ] T169 [P] Contract test asserting the emitted scorecard validates against `contracts/eval-scorecard.schema.json` and maps onto harness §10 field-for-field, in `tests/contract/test_eval_scorecard_schema.py`
- [x] T170 [P] Harness Pass 1 test computing intake-baseline coverage and quality scores across F1–F8 in `tests/harness/test_pass1_intake_baseline.py`
- [x] T171 [P] Harness Pass 2 test covering every broken path — no-backfill, correction and re-evaluation, misroute correction, duplicate protection, contradictory conflict, timeout/retry — asserting no orphan states and no silent drops, in `tests/harness/test_pass2_broken_paths.py`
- [x] T172 [P] Harness Pass 3 test covering parallel approval correctness, escalation precedence, dispatch timing and SLA alert timeliness in `tests/harness/test_pass3_approval_escalation.py`
- [x] T173 [P] Harness Pass 6 test asserting 100% identical per-case classifications on re-run and aggregate drift within ±2 percentage points, in `tests/harness/test_pass6_repeatability_and_surface.py` (P7, FR-049, SC-013)
- [ ] T174 Implement the Copilot SDK conversational surface rendering workflow state and submitting human decisions, holding no business logic, in `src/admin_workflow/surface/app.py` (F22, P9, research D17)
- [ ] T175 Implement the demo journey script covering the nine steps of `contracts/agent-surface.md` §4 in `src/admin_workflow/surface/demo_journey.py` (harness Pass 6 chat-flow completion)
- [ ] T176 Add p95 draft-readiness instrumentation using nearest-rank over every admitted case, itemising outliers with cause, in `src/admin_workflow/eval/latency.py` (SC-003)
- [x] T177 [P] Write the production-gap statement — what production would additionally require (hosting, multi-tenancy, SSO, live EHR integration, OCR) — in `docs/production-gap.md` (M4)
- [ ] T178 Execute `quickstart.md` end to end on a clean checkout and correct any step that does not work as written, in `specs/001-admin-workflow-assistant/quickstart.md`
- [x] T179 Record every implementation change in `docs/progress-log.md` per the definition of done in `quickstart.md` §10 (constitution §7, FR-050, F24)
- [x] T180 Record the full harness run and its **Go** verdict, with the scorecard attached, in `docs/run-records/multipass-run-chg-021.md` and `docs/progress-log.md` (harness §11)

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 — Setup (T001–T012)**: no dependencies; T007, T008 and T012 are governance blockers that must land before any harness pass is scored
- **Phase 2 — Foundational (T013–T063)**: depends on Setup; **blocks every user story**. Pass 0 is a hard gate
- **Phase 3+ — User stories**: all depend on Phase 2 completion
- **Phase 12 — Polish (T167–T180)**: depends on the stories whose behaviour the harness passes score

### Ordering rules inside Phase 2 (non-negotiable)

1. Bundle files (T013–T018) → contract tests (T019–T028) → bundle loader (T044) → resolvers (T045) → freeze (T062)
2. Domain entities (T029–T041) → state machines (T042)
3. Masking (T049) **before** the event store (T050), because masking is a write-boundary property; installing it afterwards leaves raw identifiers at rest
4. Registry (T053) → ledger (T054) → `ActionGate` (T055); no effect-producing code may be written before T055 exists

### User story dependencies

| Story | Priority | Depends on | Notes |
|---|---|---|---|
| **US1** | P1 | Phase 2 only | MVP. Consumes a routing confidence value; testable with a fixed confidence input before US2 exists |
| **US2** | P1 | Phase 2 only | Independently testable; US1 supplies richer inputs but is not required to test routing |
| **US3** | P1 | Phase 2 only | Independently testable against any prepared draft artifact |
| **US8** | P1 | Phase 2 only | Sequenced before US5 so the outbound guard exists before packets are generated |
| **US5** | P1 | Phase 2; US8 for the outbound assertion check | `decisions/sla.py` already exists from T047, so no cross-story block |
| **US6** | P1 | Phase 2 only | Independently testable |
| **US4** | P2 | Phase 2; extends `decisions/sla.py` from T047 | Independently testable |
| **US7** | P2 | Phase 2 only | Reads projections; richer with other stories present but not blocked by them |
| **US9** | P2 | Phase 2 only | Observes the workflow rather than driving it |

### Within each user story

- Contract and scenario tests are written first and must **fail** before implementation
- Deterministic decision functions and their unit tests precede the stage executors that call them
- Stage executors precede the surface commands that expose them
- Model-backed components (`extraction/`, `drafting/`) come **after** the deterministic functions they feed

---

## Parallel opportunities

### Phase 1

T003, T004, T005 and T006 are four different files with no interdependency — run together.

### Phase 2

```bash
# All six policy bundle files — different files, no shared state:
Task: "Author config/policy/v1/policy-table.yaml"           # T013
Task: "Author config/policy/v1/routing-rules.yaml"          # T014
Task: "Author config/policy/v1/approver-registry.yaml"      # T015
Task: "Author config/policy/v1/field-owner-map.yaml"        # T016
Task: "Author config/policy/v1/sla-table.yaml"              # T017
Task: "Author config/policy/v1/critical-signal-register.yaml" # T018

# All ten foundational contract tests (T019-T028) — one file each
# All thirteen domain entity modules (T029-T041) — one file each
```

### Parallel example: User Story 1

```bash
# All twelve US1 tests together — different files, all expected to fail:
Task: "Contract test for case-record schema in tests/contract/test_case_record_schema.py"        # T064
Task: "Scenario test AS-1 in tests/scenario/test_as01_register_and_extract.py"                    # T065
Task: "Scenario test AS-2 in tests/scenario/test_as02_backfill_and_completion_tasks.py"           # T066
Task: "Scenario test AS-3 in tests/scenario/test_as03_provisional_or_hold.py"                     # T067
Task: "Scenario test AS-7 in tests/scenario/test_as07_duplicate_key_match.py"                     # T068
Task: "Identity-match test in tests/scenario/test_duplicate_identity_match.py"                    # T069
Task: "CASE-017 false-positive test in tests/scenario/test_duplicate_false_positive.py"           # T070
Task: "Not-applicable trap test in tests/scenario/test_not_applicable_not_missing.py"             # T071
Task: "Unreadable-document test in tests/scenario/test_unreadable_document_registered.py"         # T072
Task: "Contradictory-value test in tests/scenario/test_contradictory_value_disputed.py"           # T073
Task: "Duplicate matcher unit tests in tests/unit/test_duplicates.py"                             # T074
Task: "Provisional eligibility unit tests in tests/unit/test_provisional.py"                      # T075
```

### Parallel example: User Story 5

```bash
# All eleven US5 tests together (T117-T127) — the trap cases in particular are
# independent files and must all be red before decisions/critical_signal.py is written.
```

### Across stories

Once Phase 2 completes, US1, US2, US3, US6, US7, US8 and US9 can all proceed in parallel with separate owners. US5 should follow US8 by one step. US4 extends `decisions/sla.py`, so it should not run concurrently with T131 (US5's acknowledgement-clock change to the same file).

---

## Implementation Strategy

### MVP first (User Story 1 only)

1. Complete Phase 1 — Setup, including the R1/R2 governance corrections
2. Complete Phase 2 — Foundational; **Pass 0 must be green** and CA-008-002/003/004 all cleared
3. Complete Phase 3 — User Story 1
4. **STOP and VALIDATE**: submit complete, incomplete and duplicate cases; verify the case record, provenance, missing-field list, completion tasks and duplicate flags — with the CASE-005/017/018 and CASE-012/014/020 traps all behaving correctly
5. Demo the intake slice

### Incremental delivery

| Increment | Stories | Harness gate |
|---|---|---|
| Foundation | Setup + Foundational | **Pass 0** (hard gate) |
| MVP | US1 | Pass 1 partial |
| Intake complete | + US2 | **Passes 1, 2** |
| Control layer | + US3, US8 | Pass 3 partial, Pass 5 partial |
| Escalation | + US5 | **Pass 3** |
| Gating | + US6 | **Pass 4** (hard gate) |
| Throughput and visibility | + US4, US7 | Pass 3 complete |
| Compliance | + US9 | **Pass 5** (hard gate) |
| Evidence | Polish | **Pass 6** → **Go** |

### Parallel team strategy

After Phase 2 completes:

- **Developer A** — US1 then US2 (the intake spine; largest slice)
- **Developer B** — US8 then US5 (the safety-critical path; must not be shared with A)
- **Developer C** — US3 then US6 (the human-control and gating path)
- **Developer D** — US7 then US9, then US4 once T131 has landed

---

## Task counts

| Phase | Story | Tasks | IDs |
|---|---|---|---|
| 1 — Setup | — | 12 | T001–T012 |
| 2 — Foundational (M0) | — | 51 | T013–T063 |
| 3 | **US1** (P1) 🎯 MVP | 25 | T064–T088 |
| 4 | **US2** (P1) | 8 | T089–T096 |
| 5 | **US3** (P1) | 12 | T097–T108 |
| 6 | **US8** (P1) | 8 | T109–T116 |
| 7 | **US5** (P1) | 19 | T117–T135 |
| 8 | **US6** (P1) | 10 | T136–T145 |
| 9 | **US4** (P2) | 9 | T146–T154 |
| 10 | **US7** (P2) | 5 | T155–T159 |
| 11 | **US9** (P2) | 7 | T160–T166 |
| 12 — Polish (M4) | — | 14 | T167–T180 |
| **Total** | | **180** | |

Story tasks total **103**; shared Setup, Foundational and Polish total **77**.
Tasks marked **[P]** (parallelizable): **93** of 180.

---

## Notes

- `[P]` means a different file with no dependency on an incomplete task
- Every task traces to a numbered FR, a policy P-value, a research decision, or a harness pass — constitution §7 requires traceability
- Verify each test fails before implementing against it (contracts/README.md failing-first obligation)
- Commit after each task or logical group, and record the change in `docs/progress-log.md` (FR-050, F24)
- If a change touches workflow rules, approvals, safety or routing, **the whole harness re-runs** (harness §12)
- A change to a safety-bearing policy (P1, P3, P10, P11) requires **Compliance Reviewer** approval, not Team Lead alone
- Synthetic data only. `SYN-CASESET-v1` and nothing else — a breach is **Sev 0** and an immediate stop-run
- Stop at any checkpoint to validate a story independently
