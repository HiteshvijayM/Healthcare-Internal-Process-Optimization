# Phase 0 — Research: Administrative Workflow Assistant

**Feature**: `001-admin-workflow-assistant`
**Spec**: [spec.md](./spec.md)
**Date**: 2026-09-02
**Status**: All Technical Context unknowns resolved. No `NEEDS CLARIFICATION` remains.

---

## 0. How this document was produced

Every decision below was constrained, in this order of precedence:

1. [`docs/constitution.md`](../../docs/constitution.md) — immutable, non-overridable.
2. [`spec.md`](./spec.md) — FR-001..FR-057, SC-001..SC-015 (ratified under CHG-021).
3. [`feature.md`](../../feature.md) §5.4 policy table **P1–P11**, §6 priority tiers, §7 metrics, §9 technical notes.
4. [`docs/multipass-validation-harness.md`](../../docs/multipass-validation-harness.md) — the 7-pass gate that any build must pass.

Where the sources already decided something (stack, thresholds, queues, roles, register), it is **adopted, not reopened**. Research was therefore limited to *how* to realise already-approved decisions safely — not to *what* to build.

Each decision records **Decision / Rationale / Alternatives considered / Traces to**.

---

## 1. Platform and runtime

### D1 — Language and runtime: Python 3.11+ on the Microsoft Agent Framework (`agent-framework`) Python package

- **Decision**: Python 3.11+, MAF Python (`agent-framework`), with the Copilot SDK providing the single conversational surface required by **P9**.
- **Rationale**: `README.md` and `feature.md` §9 already fix the stack as *MAF + Copilot SDK*, and §9 further directs that the journey be modelled as a **workflow, not a single agent**. MAF's Python workflow layer supplies exactly the three primitives this specification needs and would otherwise have to be hand-built: typed **executors** in a directed graph, **checkpointing** per superstep (resumability across the long human waits that dominate this workflow — SLAs run to 2 business days under P4), and a first-class **human-in-the-loop request/response pause**. Python 3.11 is the floor because the deterministic decision core leans on `match` statements, `datetime` improvements and exception groups, and because it is the baseline the framework's Python packages target.
- **Alternatives considered**:
  - *.NET MAF* — equally capable, but the eval harness (F21), the answer-key grading and the dataset are all plain-text/JSON tooling where Python's iteration speed wins, and no other repository artifact assumes .NET.
  - *A single MAF agent with tools instead of a workflow* — rejected outright: it collapses the stage boundaries that FR-031 (return to the *stage that produced the rejected output*) and the harness state-machine checks in Pass 2 depend on, and it would place approval enforcement inside a prompt rather than inside the control flow.
- **Traces to**: `feature.md` §9, P9, FR-031.

### D2 — Workflow topology: one executor per journey stage, wired as a MAF graph

- **Decision**: Eight stage executors matching `feature.md` §9 exactly — `arrive/register` → `enrich/backfill` → `validate` → `route/provisional-route` → `approvals/escalation` → `clinical gate` → `finance gate` → `release route` — plus cross-cutting non-stage services (safety guard, audit writer, policy resolver, SLA clock) that every stage calls.
- **Rationale**: Stage identity is not cosmetic here; it is load-bearing for four separate requirements. FR-031 requires a rejection to return to the *specific* producing stage and forbids rewinding earlier than data completion. FR-039 requires the current stage to be displayed per case. Harness Pass 2 scores *state machine validity for each transition* and *no orphan states*. FR-042 requires an ordered history. Making the stage a first-class executor makes all four observable rather than inferred.
- **Alternatives considered**: A flat state field on the case mutated by service functions — rejected because it leaves transition legality unenforced and untestable; Pass 2's "no orphan states and no silent drops" check would have nothing structural to score against.
- **Traces to**: `feature.md` §9, FR-031, FR-039, FR-042, harness Pass 2.

### D3 — Human lockpoints are structural, not advisory: MAF request/response pauses

- **Decision**: Every human decision point — role approvals (F11/F12), escalation dispatch approval (FR-051), clinical clearance (FR-033), financial clearance (FR-033), duplicate adjudication (FR-015) — is implemented as a MAF request/response pause (`RequestInfoExecutor` / `RequestInfoEvent`). The workflow **cannot** advance past an unfulfilled request; there is no code path that skips it.
- **Rationale**: FR-030 and SC-008 demand *exactly zero* unapproved sends. A conditional check (`if approved: send`) is a rule that can be bypassed by a future edit; a workflow that is physically suspended awaiting an external response cannot be. This converts the never-cut feature **F12** from a behaviour into an architectural property, which is what makes SC-008's "exactly zero" claim defensible rather than aspirational.
- **Alternatives considered**: Guard clauses at each send site — rejected as unenforceable at scale and impossible to prove exhaustively; a reviewer would have to audit every call site rather than one graph.
- **Traces to**: FR-029, FR-030, FR-038, FR-051, SC-008, F12 (never-cut).

---

## 2. The determinism problem (the single most consequential decision)

### D4 — Split *judgement* from *decision*: no model output is ever load-bearing for a classification

- **Decision**: Two strictly separated layers.
  - **Judgement layer (model-assisted, advisory)**: field extraction from the source document (F2) and natural-language drafting of handoff summaries / chase messages (F9). Output is always a *proposal* carrying provenance, always human-reviewable, and never a gate outcome.
  - **Decision layer (pure, deterministic, no model)**: routing (FR-017), duplicate detection (FR-014/FR-055), critical-signal matching (FR-057), escalation outcome precedence (FR-054), clearance and release gating (FR-033/FR-034), SLA computation (FR-022), provisional-routing eligibility (FR-010/FR-011), safety-boundary refusal (FR-036). All are pure functions of `(case record, policy bundle)` with no I/O and no model call.
- **Rationale**: FR-049 requires **identical** per-case outcome classifications across runs, P7 states "determinism is not negotiable", and SC-013 grades it. A sampled language model cannot supply that guarantee, and temperature-0 is a mitigation rather than a guarantee. Separating the layers means run-to-run variance can only ever appear in *advisory* text a human is already reviewing — never in a routing queue, a duplicate flag, a critical-signal match, or a gate outcome. It also directly satisfies FR-017's requirement that routing be *inspectable and declarative*, and constitution §5, which permits autonomous "administrative routing" only when nothing clinical is being judged.
- **Alternatives considered**:
  - *LLM-based routing with a generated explanation* — rejected on three independent grounds: non-deterministic (fails P7/FR-049), the explanation is a post-hoc narration rather than the actual cause (fails FR-018's *rule trace*), and it is not inspectable by a non-technical reviewer (fails FR-017 and the `README.md` ground rule).
  - *Temperature 0 alone* — reduces but does not eliminate drift, and pins determinism to a vendor's serving behaviour, which is not a property this project controls.
- **Traces to**: FR-010, FR-014, FR-017, FR-018, FR-036, FR-049, FR-054, FR-055, FR-057, P7, SC-006, SC-013, constitution §5.

### D5 — Extraction determinism for graded runs: record/replay fixtures

- **Decision**: The extraction adapter supports three modes: `live` (calls the model), `record` (calls the model and writes the raw proposal to a versioned fixture keyed by document hash + prompt hash + model ID), and `replay` (reads fixtures only; a cache miss is a hard error, never a silent fallthrough to `live`). **Graded harness runs execute in `replay`.**
- **Rationale**: SC-013 requires a re-run on the same dataset *and build* to reproduce identical per-case classifications and aggregate scores within ±2 points. With `replay`, the entire pipeline downstream of extraction is deterministic by D4, so the whole run is reproducible bit-for-bit — and the recorded fixtures become part of the harness §9 evidence contract. A cache miss must fail loudly, because a silent fallthrough would turn a reproducibility failure into an invisible one.
- **Alternatives considered**: Re-running live for every graded run — rejected: it makes SC-013 depend on model-serving stability and makes a failed run unattributable between "our regression" and "their model changed".
- **Traces to**: FR-048, FR-049, SC-013, P7, harness Pass 6 and §9.

---

## 3. Policy, rules, and versioning

### D6 — The policy bundle: one frozen, versioned, human-readable directory

- **Decision**: All declarative policy lives in `config/policy/<version>/` as commented YAML, loaded as one immutable **policy bundle** at run start:

  | File | Encodes | Authority |
  |---|---|---|
  | `policy-table.yaml` | P1–P11 values | `feature.md` §5.4 |
  | `routing-rules.yaml` | Ordered routing rules → 5 fixed queues | F7, §13.5 |
  | `approver-registry.yaml` | §4.1 roles + §4.2 required designations | harness §4.1/§4.2 |
  | `field-owner-map.yaml` | Field → completion-task owner | FR-008 |
  | `sla-table.yaml` | Urgency class × service line → SLA | P4/P5, FR-022 |
  | `critical-signal-register.yaml` | `CCR-DEMO-v1` entries | P11, FR-057 |
  | `bundle.lock.json` | Bundle ID + SHA-256 of every file above | FR-045, F23 |

- **Rationale**: Harness §4 makes "policy/routing config version is frozen for the run" a **Pass 0 entry criterion**, and its absence is one of the three blockers currently holding `multipass-run-chg-008` in the Blocked state (CA-008-003). FR-045 requires every routing and approval decision to carry the policy version in force *at that moment*. A single hashed bundle makes the version a real, checkable identity rather than a label, and keeps every number the harness scores against in one place a non-technical reviewer can read — which is precisely what §5.4 asks for.
- **Alternatives considered**: Thresholds as Python constants — rejected: invisible to a non-technical reviewer, unfreezable, and would silently reopen change-logged decisions on every edit.
- **Traces to**: FR-017, FR-045, F23, P1–P11, harness §4 and Pass 0, CA-008-003.

### D7 — Routing rules format: ordered, named, single-line-reasoned YAML

- **Decision**: Each rule carries `id`, `description` (plain English), `when` (a restricted expression over a fixed, documented set of case fields and operators), `queue`, `reason_template` (one line), and `confidence`. Evaluation is top-to-bottom, first match wins, **every** rule evaluation is recorded in the trace with its boolean outcome, and an explicit terminal default rule guarantees no case falls off the end.
- **Rationale**: FR-017 requires a one-line reason a non-technical reviewer understands; FR-018 requires a trace of rules *evaluated* as well as *fired* — so non-firing rules must be recorded, not skipped. US2 scenario 2 requires the reviewer to identify the producing rule *without technical assistance*, which forces the rule's own English description to be the explanation source. The restricted expression grammar (no arbitrary code) is what keeps the config reviewable and keeps the "declarative" claim honest.
- **Alternatives considered**: Python predicate functions in a rules module (fails "not buried in code", §9); a general expression language such as full Python `eval` (unreviewable, and an injection surface).
- **Traces to**: FR-017, FR-018, US2, `feature.md` §9, §13.5, harness Pass 1.

### D8 — The critical-condition register is mirrored, never re-authored

- **Decision**: `docs/critical-condition-register.md` (`CCR-DEMO-v1`) stays the authoritative artifact. `config/policy/<version>/critical-signal-register.yaml` is a machine-readable **mirror**, and a contract test asserts the mirror matches the markdown table entry-for-entry (IDs, literal markers, clinical owners). Drift fails the build. `bundle.lock.json` records both the register ID and the SHA-256 of the markdown source.
- **Rationale**: P11 and the register's own §4 place change approval with **Clinical Authority + Compliance Reviewer** — a bar that a YAML file edited during implementation would quietly bypass. Mirroring with an enforced equality test preserves the human-curated document as the single source of clinical truth while still giving the matcher something to load, and makes any divergence a build failure rather than a silent safety regression.
- **Alternatives considered**: Parsing the markdown directly at runtime (fragile, and couples the runtime to prose formatting); maintaining only YAML (severs the change-control chain — unacceptable for a safety-bearing policy).
- **Traces to**: FR-057, P11, register §4, constitution §5.

---

## 4. Safety-critical mechanisms

### D9 — Critical-signal detection: literal marker matching only

- **Decision**: Detection is literal, case-insensitive, whitespace-normalised matching of the register's stated marker phrases against the source document text. **No** embeddings, no fuzzy matching, no synonym expansion, no model call. Register resolution failure (absent / empty / unresolvable version) raises a **governance blocker**, holds the case, and refuses provisional routing. A non-match is reported with the exact phrase *"no registered signal matched"* — never as "no critical condition present". A case matching several entries yields **one** packet naming every matched ID.
- **Rationale**: The register's §1 states the three prohibitions explicitly, and FR-057 encodes them. Any similarity-based matcher *is* inference, and inference about clinical criticality is forbidden by constitution §5; harness Pass 3 grades both over-inference and the negative claim as **Sev 0**. The dataset is built to catch exactly this: CASE-013 (contradictory urgency) and CASE-020 (`Urgency: Urgent`) must **not** escalate, while CASE-008 must — and CASE-008 carries `URGENT` in its subject line *alongside* a genuine CCS-001 marker, so a matcher keying on urgency would look correct on the positive case while being catastrophically wrong.
- **Alternatives considered**: Semantic/embedding similarity (Sev 0 by construction); an LLM classifier with the register in-prompt (non-deterministic *and* inference — fails P7 and constitution §5 simultaneously).
- **Traces to**: FR-057, FR-011, P11, register §1–§3, SC-011, harness Pass 3, constitution §5.

### D10 — Escalation outcome: one pure resolver, evaluated in strict precedence

- **Decision**: A single pure function `resolve_escalation_outcome(case, packet, bundle, roster) -> EscalationOutcome` returns **exactly one** of `GOVERNANCE_BLOCKER | COMPLETENESS_BLOCKER | DISPATCH_APPROVAL`, in this order:
  1. Collect **all four** designations — clinical recipient (FR-028), Escalation Dispatch Approver (FR-051), approved dispatch-approval deadline (FR-052), on-call clinical coverage (FR-056). If **any** are absent → `GOVERNANCE_BLOCKER` listing **every** absent designation. Additionally, if the approved deadline is present but **not strictly shorter** than the acknowledgement SLA *applied to this case*, that too is a governance blocker (FR-052).
  2. Else if any mandatory **content** field of P3 is missing → `COMPLETENESS_BLOCKER` to Clinical Authority **and** Intake Coordinator (FR-026).
  3. Else → `DISPATCH_APPROVAL`, raised as a non-suppressible alert (FR-051).
- **Rationale**: FR-054 and SC-011 specify this precedence exactly, including the subtle trap that a missing clinical recipient is *both* a missing designation and a mandatory P3 packet field — and must be reported as the former. Concentrating it in one total function with a single return value is the only structure that makes "exactly one outcome" provable rather than emergent from scattered branches, and it gives harness Pass 3's precedence check a single unit under test.
- **Alternatives considered**: Sequential checks that raise on first failure — rejected because FR-054 explicitly forbids "surfacing the first and concealing the rest"; the resolver must *aggregate* absent designations before returning.
- **Traces to**: FR-024, FR-026, FR-028, FR-051, FR-052, FR-054, FR-056, SC-011, harness Pass 3.

### D11 — Duplicate detection: two independent, separately-reported matchers

- **Decision**: Two matchers run independently, and either one flags:
  - **Key match** — `(sender, patient_reference, requested_service)` against **in-progress** cases within the P2 window (72h, read from the policy table as a parameter, never hardcoded). Channel-agnostic.
  - **Identity match** — **unbounded in time**, and applies whether the earlier case is open or closed. Matches on the immutable source-document identifier supplied by the arrival channel, or on a hash of **normalised** content where normalisation strips transport-added material only (cover sheets, routing headers, arrival timestamps, channel watermarks, re-transmission banners) and alters no clinical or administrative content.
  The flag records **which** matcher fired and the matched key or document identifier. Every match is held for human adjudication — never auto-discarded, never auto-merged.
- **Rationale**: FR-055 and the amended P2 define both matches, and SC-009 requires the sample set to exercise the window boundary and the identity boundary *in both directions*. Recording which matcher fired is what makes SC-009's false-positive claim auditable rather than a bare count. Normalisation is deliberately a strict allowlist of transport artifacts, because a broader normaliser would erase genuine content differences and turn FR-055's "a difference in any retained content MUST prevent one" into a false positive generator.
- **⚠️ Fixture gap — SC-009 is not gradable against `SYN-CASESET-v1` as it stands.** The dataset supplies the *key-match* traps only: CASE-005 (of CASE-001, ~6h apart) and CASE-018 (of CASE-016, ~20h apart) both fall **inside** the 72h window, so both are key matches; CASE-017 is a different key, not same-key-different-content. Neither of the two fixtures SC-009 explicitly requires exists:
  1. an exact re-send arriving **after** the key window has closed, against an already-closed case — the only fixture that exercises the identity matcher independently of the key matcher; and
  2. a later submission sharing the sender/patient/service key but carrying **genuinely different content** — the negative direction of the identity matcher.
  Without (1) the identity matcher is never exercised on its own and a key-match-only implementation passes SC-009 by accident; without (2) an over-broad normaliser goes undetected. **Both fixtures must be authored before harness Pass 2 is scored**, which mints a new dataset ID under `data/README.md` §7. Until then Pass 2 records SC-009 as *Blocked*, not as passed. T069 assumes fixture (1) exists and must not be marked complete against `SYN-CASESET-v1`.
- **Alternatives considered**: A single fuzzy similarity score with a threshold — rejected: it conflates two policies with different time semantics, is not explainable to an adjudicator, and would flag CASE-017.
- **Traces to**: FR-014, FR-015, FR-055, P2, SC-009, harness Pass 1 and Pass 2.

### D12 — Outbound actions pass through one `ActionGate`

- **Decision**: Every effect that leaves the system — send, submit, escalate/dispatch, record clearance, route for release — is declared as a typed `Effect` and can only execute through a single `ActionGate.execute(effect, approval_ref)`. The gate verifies: an approval record exists, it references *this* effect, it was recorded by a principal holding the required role in the approver registry, and separation-of-duty holds. The agent principal is structurally incapable of satisfying the role check.
- **Rationale**: FR-030 plus FR-038 ("System MUST NOT occupy any approver role") plus harness §4.1 ("the agent holds no approver role... may never occupy a row in this table") together demand that agent identity be *unable* to authorise, not merely *disallowed* from doing so. A single choke point makes SC-008 auditable by inspecting one component, and gives Pass 4's "attempted gate bypass prevention" and "unauthorized role rejection" checks a concrete target.
- **Alternatives considered**: Per-stage authorisation checks — rejected: exhaustiveness becomes an audit burden rather than a structural guarantee.
- **Traces to**: FR-030, FR-033, FR-034, FR-038, SC-008, harness §4.1, Pass 4, F12 (never-cut).

### D13 — Safety boundary as stage-independent middleware

- **Decision**: A guard evaluated on **both** edges — every inbound conversational turn and every outbound draft/response — independent of stage, using a deterministic intent matcher for the five prohibited acts (diagnosis, treatment recommendation, medical-necessity determination, clinical clearance authorisation, discharge/release authorisation). On match: refuse with a fixed template naming the qualified human authority, and write a refusal event to the case history.
- **Rationale**: FR-036 says "at every workflow stage" and US8's independent test issues each prohibited request type *at several different stages*, so the guard cannot live in any one stage. Checking outbound as well as inbound catches the case where a drafting step drifts into clinical assertion — which matters because FR-027 forbids the escalation packet from asserting, implying, or ranking a clinical judgement, and CASE-008 grades any clinical interpretation as **Sev 0**. Refusal wording is drawn from constitution §5 and is canonical per `feature.md` §13.4, so it must be a fixed template rather than generated prose.
- **Alternatives considered**: A model-based refusal policy in the system prompt — rejected: not deterministic (SC-014 requires 100%), and it puts a non-negotiable constitutional boundary inside a channel that user input can influence.
- **Traces to**: FR-027, FR-036, FR-037, SC-014, F19 (never-cut), constitution §5, `feature.md` §13.4.

---

## 5. Audit, data handling, and time

### D14 — Append-only event log as the system of record; all state is a projection

- **Decision**: An append-only, hash-chained JSONL event log is authoritative. Case state, the status board (F14) and every report are **projections** rebuilt by replaying events. Nothing mutates history; corrections are new events that supersede.
- **Rationale**: FR-042 (complete ordered history), FR-043 (reconstruct end-to-end *from the recorded history alone*) and harness Pass 5 ("audit replay completeness") are trivially satisfied when replay is the only way state is ever produced — the audit trail cannot drift from reality because it *is* reality. It also directly answers constitution §4's who/what/when/why requirement, and the hash chain gives Pass 4's "gate token integrity and tamper resistance" something real to verify. P8 retention (project lifetime, min 90 days, no purge before sign-off) is then a file-retention policy rather than a schema concern.
- **Alternatives considered**: Mutable records with a side audit table — rejected: the two can diverge, and FR-043's "from the recorded history alone" would become an unverified claim.
- **Traces to**: FR-042, FR-043, FR-047, P8, F20 (never-cut), constitution §4, harness Pass 4 and Pass 5.

### D15 — Masking at the write boundary, applied to every sink including traces

- **Decision**: A single masking filter sits on the audit writer and on the OpenTelemetry exporter that MAF's built-in tracing feeds. Identifier-shaped values are masked on write; only the reserved synthetic prefixes (`SYN-PT-`, `ORD-`) are retained in a recognisable-but-masked form so cases stay discussable. A contract test scans every emitted log and trace for unmasked identifier patterns.
- **Rationale**: Constitution §3 requires logs *and traces* to mask identifiers; FR-044 and SC-012 require zero unmasked identifiers with a scan as evidence. Masking on write rather than on read is the only ordering that survives a log being copied, and putting the filter on the exporter closes the gap that `feature.md` §9's "turn on MAF tracing from day one" would otherwise open — tracing is the sink most likely to leak, because nobody writes it by hand.
- **Alternatives considered**: Masking at display time — rejected: raw identifiers persist at rest, which §3 forbids independently of who reads them.
- **Traces to**: FR-044, FR-046, SC-012, constitution §3 and §6, `feature.md` §9.

### D16 — Time is injected, never ambient

- **Decision**: All clocks come from an injected `TimeSource`. The critical acknowledgement clock starts **at detection** (FR-056). Routine SLA uses a business-day calendar defined in `sla-table.yaml`. The SLA value *applied* to each item is recorded on the item at the moment it is resolved (FR-022). Breach and 80% early-warning are computed against the recorded applied value, never a global constant.
- **Rationale**: FR-022 requires the applied value to be auditable after the fact, P4's per-service-line override model means the applied value is not knowable from the class alone, and P5 warns at 80% of *that* value. Injected time is also what makes SLA behaviour testable at all — harness Pass 3 grades "SLA breach alert timeliness", which is untestable against a wall clock in a run that must complete in seconds.
- **Alternatives considered**: Wall-clock time with sleep-based tests — rejected: non-deterministic (violates P7) and would make a 2-business-day SLA untestable.
- **Traces to**: FR-022, FR-023, FR-056, P4, P5, SC-010, harness Pass 3.

---

## 6. Surface, evaluation, and delivery

### D17 — One decision path behind two front ends

- **Decision**: The Copilot SDK chat surface (F22/P9) and the eval harness CLI (F21) both invoke the *same* workflow API. The surface holds no business logic; it renders workflow state and submits human decisions.
- **Rationale**: If the demo path and the graded path could diverge, the scorecard would not describe the thing being demonstrated — and `feature.md` §8 puts the eval run and the live demo side by side in the same script. One path also means Pass 6's "chat-flow completion across core journey" and Pass 1–5's case-level evidence describe identical behaviour.
- **Alternatives considered**: A separate batch pipeline for grading — rejected: two implementations, two behaviours, one misleading scorecard.
- **Traces to**: F21, F22, P9, harness Pass 6, `feature.md` §8.

### D18 — Eval harness emits the harness §10 template directly

- **Decision**: `run_eval` grades against `data/sample/answer-key.json` and emits a scorecard whose structure *is* the harness §10 Validation Output Template (run ID, date, owner, build/version, dataset/version, per-pass coverage and quality scores, severity counts, active waivers, blocking issues, corrective actions, Go/No-Go), plus every §9 evidence artifact.
- **Rationale**: `feature.md` §7 states that no cycle-time or error-rate claim is valid without a passing harness run, and §11's M4 gate requires a recorded Go. Emitting the exact template removes the manual transcription step where evidence is usually lost, and makes the missing-evidence failure mode in §9 mechanically detectable. Percentages are emitted **with their denominator `n`** and percentiles **name their estimator**, per §7's reporting rule.
- **Alternatives considered**: A free-form scorecard transcribed by hand into the run record — rejected: §9 makes missing mandatory evidence an automatic Fail, so transcription is an avoidable failure mode.
- **Traces to**: FR-048, FR-049, SC-001..SC-015, harness §9/§10/§11, `feature.md` §7.

### D19 — Testing strategy: pytest, with acceptance scenarios as first-class tests

- **Decision**: `pytest`. Three tiers: **contract** tests (config schemas, register mirror equality, masking scan, effect-gate coverage), **scenario** tests named for AS-1..AS-14 and the spec's edge cases, and **unit** tests for each deterministic decision function. A separate `tests/harness/` maps tests to Passes 0–6 so a pass score can be computed from test results.
- **Rationale**: Constitution §7 requires validation evidence to accompany implemented behaviour and changes to be traceable to requirements. Naming tests after AS IDs makes the spec's traceability table executable rather than documentary, and the harness tier is what turns Pass scoring from a manual review into a computed artifact.
- **Alternatives considered**: Unit tests only — rejected: leaves AS-1..AS-14 and the seven passes unverified, which is precisely the evidence the harness demands.
- **Traces to**: FR-048, constitution §7, harness §6/§9.

### D20 — Secrets and configuration

- **Decision**: No secrets in source control. Model endpoint credentials come from environment variables or a managed identity, resolved at startup; the repository carries only a `.env.example` with placeholder names. Config files hold policy, never credentials.
- **Rationale**: Constitution §6 forbids hardcoded or source-controlled secrets and requires least privilege; harness Pass 0 reviews the security exception register.
- **Traces to**: constitution §6, harness Pass 0.

---

## 7. Resolved unknowns — summary

| # | Unknown from Technical Context | Resolution | Decision |
|---|---|---|---|
| 1 | Language and version | Python 3.11+ | D1 |
| 2 | Agent framework binding | MAF Python `agent-framework`, workflow (not single agent) | D1, D2 |
| 3 | Conversational surface | Copilot SDK, single web surface, one tenant/session (P9) | D1, D17 |
| 4 | How FR-049/P7 determinism is achieved | Deterministic decision layer + record/replay extraction | D4, D5 |
| 5 | Where declarative routing rules live | `config/policy/<version>/routing-rules.yaml`, restricted grammar | D6, D7 |
| 6 | Storage | Append-only hash-chained JSONL event log; state is a projection | D14 |
| 7 | Critical-register representation | Markdown authoritative, YAML mirror, equality enforced by test | D8 |
| 8 | Approval enforcement mechanism | MAF request/response pauses + single `ActionGate` | D3, D12 |
| 9 | Identifier masking point | Write boundary, incl. OTel exporter | D15 |
| 10 | Time and SLA handling | Injected `TimeSource`; applied SLA recorded per item | D16 |
| 11 | Testing framework and structure | pytest; contract / scenario (AS-*) / unit / harness tiers | D19 |
| 12 | Target platform | Local/dev container; single demo tenant; no production hosting (out of scope) | D1, P9 |
| 13 | Performance goal | Draft ready < 30s at p95, nearest-rank, over all admitted cases | D18, SC-003 |
| 14 | Scale | 20-case `SYN-CASESET-v1`; one tenant; one reviewer session | P9, §13.2 |

**No `NEEDS CLARIFICATION` markers remain.**

---

## 8. Findings raised during research

Recorded here because they affect the build but are **not** decisions this plan may take unilaterally.

| # | Finding | Impact | Severity | Owner |
|---|---|---|---|---|
| R1 | **CHG-021 is not recorded in `docs/progress-log.md`.** The ratification is reflected in `feature.md` §5.4 (P10/P11), harness §4.2, `spec.md` and the new `docs/critical-condition-register.md`, but the change-entry table ends at CHG-020 and §6 "Current Next Steps" still instructs that planning must not start. | Constitution §7 and FR-050 require every change to be recorded in the progress log; F24 enforces it. The system-of-record currently contradicts the artifacts. | Governance (Sev 1 by harness §5 — auditability) | Team Lead + Compliance Reviewer |
| R2 | **Graded-field list mismatch.** `data/README.md` §4 lists **8** graded fields (including `supporting_notes`); `answer-key.json.graded_fields` lists **7** (excluding it), and no `expected_fields` block contains it. | SC-004 (≥85%) has an ambiguous denominator; `feature.md` §7's reporting rule requires every percentage to carry a defined `n`. | Sev 2 | Team Validation Lead |
| R3 | **`docs/multipass-run-chg-008.md` remains Blocked**, with CA-008-002 (build), CA-008-003 (frozen policy version) and CA-008-004 (sandbox) open. | Pass 0 cannot be scored until this plan's Phase 1 policy bundle and a build identifier exist. Expected at this stage, but it gates every claim. | Blocked-run, not a failure | Team Validation Lead |
| R4 | **Register scope is demo-only.** `CCR-DEMO-v1` §5 states it is not clinically complete and that processing real data against it is prohibited. | Not a defect — but the plan must not imply escalation coverage beyond `SYN-CASESET-v1`. Recorded so the boundary stays visible in the demo. | Informational | Clinical Authority |

R1 is the only finding that must be closed **before implementation begins**; R2 should be closed before SC-004 is first scored.
