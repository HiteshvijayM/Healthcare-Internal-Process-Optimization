# Phase 1 — Data Model: Administrative Workflow Assistant

**Feature**: `001-admin-workflow-assistant`
**Source**: [spec.md](./spec.md) *Key Entities*, FR-001..FR-057 · [research.md](./research.md) D1–D20
**Date**: 2026-09-02

> **Modelling rule** (from [research.md](./research.md) D14): the **Audit Event log is the system of record**. Every other entity below is a *projection* rebuilt by replaying events. No entity is mutated in place; corrections are new events that supersede. This is what makes FR-043 ("reconstruct from the recorded history alone") true by construction rather than by assertion.

---

## 1. Entity map

```text
                          ┌──────────────────┐
                          │  Policy Bundle   │  frozen, hashed, versioned
                          │  (P1..P11, rules)│  referenced by every decision
                          └────────┬─────────┘
                                   │ policy_version
   ┌───────────────────────────────┼────────────────────────────────┐
   │                               │                                │
┌──▼───┐   1      1..1   ┌─────────▼────────┐  1     0..*  ┌────────▼────────┐
│ Case ├─────────────────► Case Record      ├──────────────► Case Record     │
│      │                 │                  │              │ Field           │
└──┬───┘                 └──────────────────┘              └─────────────────┘
   │
   ├── 0..*  Data Completion Task
   ├── 0..1  Routing Decision  (current; superseded ones retained)
   ├── 0..1  Duplicate Flag
   ├── 0..*  Approval Task
   ├── 0..1  Escalation Packet ──── 1..* Matched Signal (→ Register Entry)
   ├── 0..2  Clearance Gate     (clinical | financial)
   ├── 0..*  Draft Artifact
   ├── 0..*  Blocker            (governance | completeness | data | duplicate)
   ├── 0..*  Refusal Record
   └── 1..*  Audit Event        ◄── the system of record

                          ┌──────────────────┐
                          │ Approver Registry│  roles (§4.1) + designations (§4.2)
                          └──────────────────┘  the agent appears in neither
```

---

## 2. Core entities

### 2.1 Case

The tracked administrative work item created on arrival (FR-001).

| Field | Type | Rules |
|---|---|---|
| `case_id` | string, unique | Assigned on arrival. Immutable. |
| `arrival_timestamp` | datetime (UTC) | Recorded even when the document is unreadable (FR-005). |
| `arrival_channel` | enum `email \| fax \| portal` | Recorded but **never** part of the duplicate key (FR-014, P2). |
| `source_document_ref` | string | Immutable channel-supplied identifier where available; used by identity matching (FR-055). |
| `stage` | enum (see §3.1) | Current workflow stage. |
| `owner_role` | Role ref | Current accountable role, never a person. |
| `lifecycle_state` | enum `active \| held \| closed` | `held` whenever any blocker is open. |
| `elapsed_seconds` | derived | Arrival → now, or arrival → completion (FR-039, FR-040). |
| `rework_loop_count` | int, 0..2 | At 2, a third loop escalates to a human owner instead (FR-035, P6). |
| `urgency_class` | enum `routine \| urgent` | Administrative only. **Never** a critical-condition signal (register §2 exclusions). |
| `service_line` | string | Used with `urgency_class` to resolve the applied SLA (FR-022, P4). |

**Invariants**

- `INV-C1` — A case is registered *before* extraction is attempted, so an unreadable document still yields a tracked item plus a blocker (FR-005).
- `INV-C2` — `lifecycle_state = held` whenever any open blocker exists; no stage transition may occur while held, except transitions that resolve the blocker.
- `INV-C3` — `rework_loop_count` never exceeds 2 (FR-035).

### 2.2 Case Record and Case Record Field

The structured extraction result (FR-002). Modelled as a collection of fields so that value, provenance and resolution state are carried **per field** — this is what lets FR-004, FR-006 and FR-009 be answered field-by-field rather than for the record as a whole.

| Field | Type | Rules |
|---|---|---|
| `field_name` | enum | The graded set: `requester`, `patient_reference`, `requested_service`, `urgency`, `payer_plan`, `ordering_reference`, `date` (see finding **R2**). |
| `value` | string \| null | Never invented or guessed (FR-002). |
| `source` | enum `submitted \| backfilled \| human_entered` | Backfilled values are always distinguishable (FR-004). |
| `source_detail` | string \| null | **Required** when `source = backfilled` — the record it was derived from (FR-004). |
| `resolution_state` | enum `present \| missing \| not_applicable \| unreadable \| disputed` | See below. |
| `is_mandatory` | bool | Drives completion-task creation (FR-008). |
| `confidence` | float 0..1 \| null | Advisory only; never a gate outcome (research D4). |

**`resolution_state` semantics**

| State | Meaning | Consequence |
|---|---|---|
| `present` | A value is recorded and trusted. | May be advanced on. |
| `missing` | Absent and required. | Completion task (FR-008); blocks advancement on that value (FR-007). |
| `not_applicable` | Legitimately irrelevant to this request type. | **Not** missing. **No** completion task (FR-009). Traps: CASE-012, 014, 020. |
| `unreadable` | Source text absent, illegible, or admits more than one distinct reading. | Recorded as `unreadable`, never as a guessed value (FR-002). |
| `disputed` | Backfill contradicts the submitted document. | Contradiction named explicitly; submitted value **not** silently overwritten; case may not advance on this field alone (FR-006, FR-007, edge case). |

**Invariants**

- `INV-F1` — `source = backfilled` ⟹ `source_detail` is non-null (FR-004).
- `INV-F2` — `resolution_state ∈ {missing, disputed, unreadable}` ⟹ that field cannot be used to justify advancement (FR-007, SC-015).
- `INV-F3` — `not_applicable` never generates a Data Completion Task (FR-009).
- `INV-F4` — Backfill is attempted for every missing mandatory field **before** any human request is raised (FR-003), and never invents a non-derivable value.

### 2.3 Data Completion Task

An open request for one unresolved mandatory field (FR-008).

| Field | Type | Rules |
|---|---|---|
| `task_id` | string | |
| `case_id` / `field_name` | refs | One task per unresolved mandatory field. |
| `owner_role` | Role ref | From `field-owner-map.yaml`; **defaults to Intake Coordinator** where the field has no mapping (FR-008). |
| `state` | enum `open \| closed` | |
| `raised_at` / `closed_at` | datetime | Visible as a blocker while open (FR-041, US7 scenario 3). |

**Default mapping** (ratified CHG-021, queue-aligned so no new taxonomy is introduced): insurance → Insurance Approver · operations → Operations Approver · diagnostics → Diagnostics Approver · legal → Legal Approver · finance → Finance Approver · **unmapped → Intake Coordinator**.

### 2.4 Routing Decision

| Field | Type | Rules |
|---|---|---|
| `queue` | enum `Insurance \| Operations \| Diagnostics \| Legal \| Finance` | Fixed five-queue set (§13.5). |
| `reason` | string, one line | Understandable to a non-technical reviewer (FR-017). |
| `rule_trace` | list of `{rule_id, description, evaluated, fired}` | **All** rules evaluated are listed, not only the one that fired (FR-018). |
| `confidence` | float 0..1 | |
| `is_provisional` | bool | |
| `provisional_outstanding` | list[string] \| null | **Required** when provisional — names what remains outstanding (FR-012, SC-015). |
| `policy_version` | Policy Bundle ref | The version in force at decision time (FR-045). |
| `superseded_by` | Routing Decision ref \| null | Re-evaluation creates a **new** decision; the old one is retained (FR-013). |
| `change_rationale` | string \| null | Required when this decision supersedes another (FR-013). |

**Provisional-routing eligibility** (FR-010, FR-011, P1) — all must hold:

1. `confidence ≥ 0.80`; **and**
2. `patient_reference` and `requested_service` are both `present`; **and**
3. no critical-condition signal is active on the case; **and**
4. no clearance gate is pending; **and**
5. the critical-condition register resolved successfully (FR-057 — an unresolvable register holds the case and refuses provisional routing).

Condition 5 is easy to miss: with no signal detected, FR-011 alone would not engage, so FR-057's hold is the mechanism that stops an unresolvable register from silently permitting provisional routing.

### 2.5 Duplicate Flag

| Field | Type | Rules |
|---|---|---|
| `matched_case_id` | Case ref | May be **in progress or already closed** (FR-055). |
| `match_rule` | enum `key_match \| identity_match` | Which matcher fired — recorded so SC-009 is auditable. |
| `matched_on` | string | The composite key, or the document identifier / normalised-content hash. |
| `adjudication_state` | enum `pending \| confirmed_duplicate \| not_duplicate` | Human-adjudicated only (FR-015). |

**Invariants**

- `INV-D1` — `key_match` applies only within the P2 window (72h, a policy parameter) and only against in-progress cases.
- `INV-D2` — `identity_match` is **unbounded in time** and applies regardless of the earlier case's state; the P2 window must never suppress it (FR-055).
- `INV-D3` — A flagged duplicate is never auto-discarded, auto-merged, or reprocessed (FR-015).

### 2.6 Approval Task

| Field | Type | Rules |
|---|---|---|
| `role` | Role ref | Insurance · Operations · Diagnostics · Legal · Finance (FR-020). |
| `is_blocking` | bool | Blocking vs non-blocking is explicit (FR-021). |
| `sla_class` | enum `routine \| urgent \| critical_ack` | |
| `applied_sla_seconds` | int | The value **actually applied**, recorded at resolution time (FR-022). |
| `sla_resolved_from` | string | `default` or the service-line override that supplied it. |
| `warned_at_80pct` / `breached_at` | datetime \| null | P5. |
| `outcome` | enum `pending \| approved \| edited \| rejected \| returned_for_rework` | |
| `rationale` | string | Required for `rejected` and `returned_for_rework` (FR-031). |
| `decided_by_role` | Role ref | Never the agent (FR-038). |

**Invariants**

- `INV-A1` — Policy-eligible approvals are opened **concurrently**, not in sequence (FR-020, SC-002).
- `INV-A2` — An SLA breach never auto-approves, auto-advances, or auto-escalates clinically (FR-023).
- `INV-A3` — Granted approvals alone never permit advancement while a blocking approval is outstanding (edge case: rejection after other parallel approvals granted).

### 2.7 Escalation Packet

| Field | Type | Rules |
|---|---|---|
| `matched_signals` | list of `{signal_id, register_version, clinical_owner}` | **One packet** naming every matched entry, never one packet per match (FR-057, register §3). |
| `case_id`, `patient_reference`, `requester`, `signal_description`, `source_document_ref`, `timestamp`, `designated_clinical_recipient` | — | The **7 mandatory content fields** of P3 / FR-025. |
| `outcome` | enum `governance_blocker \| completeness_blocker \| dispatch_approval` | **Exactly one**, by the §4 precedence rule (FR-054, SC-011). |
| `absent_designations` | list[enum] | Populated on `governance_blocker`; lists **every** absent designation (FR-054). |
| `dispatch_state` | enum `not_raised \| pending \| approved \| rejected \| deadline_breached` | |
| `dispatch_deadline_seconds` | int | P10 = 600s; must be **strictly shorter** than `applied_ack_sla_seconds` (FR-052). |
| `detected_at` | datetime | Start of the acknowledgement clock (FR-056) — **detection**, not dispatch. |
| `routing_state` | enum `undispatched \| dispatched` | `dispatched` requires a recorded approval (FR-030, FR-051). |

**Invariants**

- `INV-E1` — No partial packet is ever sent (FR-025, P3). Partial send is **Sev 1** (harness Pass 3).
- `INV-E2` — The packet states only the observed signal and its source; it asserts, implies and ranks nothing clinical (FR-027). Violation is **Sev 0**.
- `INV-E3` — The Escalation Dispatch Approver is never the packet's designated clinical recipient (FR-051, §4.2).
- `INV-E4` — A rejected dispatch leaves the packet undispatched, records the rationale, and keeps the signal visibly active (FR-053).
- `INV-E5` — Deadline breach records a breach and escalates to the named alternate; it **never** authorises dispatch (FR-052, P10).
- `INV-E6` — Preparation completes within 30 seconds of detection (FR-024, SC-003).

### 2.8 Clearance Gate

| Field | Type | Rules |
|---|---|---|
| `gate_type` | enum `clinical \| financial` | |
| `recorded_by_principal` | principal ref | Used for the separation-of-duty check (FR-034). |
| `recorded_by_role` | Role ref | Clinical Authority · Finance Clearance Approver. |
| `recorded_at` | datetime | |

**Invariants**

- `INV-G1` — Release eligibility requires **both** gates recorded (FR-033).
- `INV-G2` — Gates are **order-independent**; neither is refused solely because the other is outstanding (FR-033, US6 scenario 4).
- `INV-G3` — The same principal may not record both gates on one case (FR-034, harness §4.1 separation of duty).
- `INV-G4` — Release routing refused while either is outstanding, and the **outstanding gate is named** as the blocker (FR-033).

### 2.9 Draft Artifact

| Field | Type | Rules |
|---|---|---|
| `artifact_type` | enum `handoff_summary \| missing_info_request \| route_proposal \| escalation_packet` | |
| `generated_version` | text | Assistant-produced. |
| `authoritative_version` | text | The human-edited version once edited; otherwise the generated one (FR-032). |
| `edited_by_role` | Role ref \| null | |

**Invariant** — `INV-DR1`: once edited, the edited text remains authoritative **even if the artifact is subsequently rejected** (FR-032, edge case).

### 2.10 Blocker

One type with a discriminator, so precedence is expressible in one place.

| Field | Type | Rules |
|---|---|---|
| `blocker_type` | enum `governance \| completeness \| data \| duplicate` | `governance` outranks `completeness` (FR-054). |
| `detail` | string | For governance blockers, names **every** absent designation (FR-054). |
| `raised_to_roles` | list[Role] | Completeness blockers go to Clinical Authority **and** Intake Coordinator (FR-026). |
| `state` | enum `open \| resolved` | While open, the case is `held` (INV-C2). |

### 2.11 Refusal Record

| Field | Type | Rules |
|---|---|---|
| `requested_act` | enum | diagnosis · treatment recommendation · medical-necessity determination · clinical clearance authorisation · discharge/release authorisation. |
| `stage` | enum | Refusal is stage-independent (FR-036). |
| `directed_to_role` | Role ref | The qualified human authority. |

**Invariant** — `INV-R1`: every refused request and its refusal is recorded in the case record (FR-037).

### 2.12 Audit Event — the system of record

| Field | Type | Rules |
|---|---|---|
| `event_id` / `sequence` | string / int | Monotonic per case; gives the **ordered** history (FR-042). |
| `event_type` | enum | arrival · extraction · backfill · validation · rule_fired · routing · duplicate_flag · task · approval · edit · escalation · clearance · refusal · blocker · sla. |
| `timestamp` | datetime | Every event carries one (FR-042). |
| `actor_role` | Role ref \| `agent` | `agent` may never appear on an approval event (FR-038). |
| `policy_version` | Policy Bundle ref | Required on every routing and approval event (FR-045). |
| `payload` | object | **Masked at write** (FR-044, D15). |
| `prev_hash` / `hash` | string | Hash chain — tamper evidence (harness Pass 4). |

**Invariants**

- `INV-AU1` — Append-only. No update, no delete (FR-042, FR-047, P8).
- `INV-AU2` — Zero unmasked personal identifiers in any event or trace (FR-044, SC-012).
- `INV-AU3` — Replaying all events for a case reproduces its full state — arrival, extracted data, backfilled values *and their sources*, rules fired, approvals *and approvers*, human edits, escalations, refusals, timestamps (FR-043, SC-012).

### 2.13 Policy Bundle

| Field | Type | Rules |
|---|---|---|
| `bundle_id` | string, e.g. `POLICY-v1` | Frozen for a run (harness §4). |
| `file_hashes` | map filename → SHA-256 | Includes the SHA-256 of `docs/critical-condition-register.md` (research D8). |
| `register_version` | string | `CCR-DEMO-v1` (P11). |
| `dataset_id` | string | `SYN-CASESET-v1`. |

**Invariant** — `INV-P1`: immutable once loaded; a change mints a new `bundle_id` and re-runs any dependent harness pass.

### 2.14 Role and Designation

**Roles** (harness §4.1, authorities not persons): Intake Coordinator · Insurance / Operations / Diagnostics / Legal / Finance Approver · Clinical Authority · Finance Clearance Approver · Team Lead · Compliance Reviewer · Team Validation Lead.

**Designations** (harness §4.2, assignments over the registry — *not* new authorities):

| Designation | Held by | Alternate |
|---|---|---|
| Designated clinical recipient | Clinical Authority | Another Clinical Authority holder |
| Escalation Dispatch Approver | **Intake Coordinator** | **Team Lead** |
| Dispatch-approval deadline | Policy value **P10** (10 min) | — |
| On-call clinical coverage | Clinical Authority roster | — |

**Invariant** — `INV-RO1`: **the agent holds no role and no designation** (FR-038, §4.1, §4.2). The agent principal is structurally unable to satisfy a role check (research D12).

---

## 3. State machines

### 3.1 Case stage

```text
                    ┌──────────── hold (blocker open) ────────────┐
                    │                                             │
 registered ──► enriched ──► validated ──► routed ──► approvals ──► clinical_gate
     │                                        ▲          │              │
     │                                        │          │              ▼
     │                            (re-evaluate on new    │        financial_gate
     │                             data — FR-013)        │              │
     │                                                   │              ▼
     └──► [unreadable] ──► blocker raised, item retained │        release_routed
                                                          │              │
                            rejection returns to the      │              ▼
                            producing stage (FR-031)  ◄───┘          completed
```

**Transition rules**

- `T1` — Registration always succeeds, including for unreadable input (FR-005).
- `T2` — `validated → routed` requires either full data completeness or provisional eligibility (§2.4); otherwise the case **holds** (FR-007).
- `T3` — Rejection returns the case to the stage that produced the rejected output; **never earlier than data completion** (FR-031).
- `T4` — A third rework loop is not permitted; the case escalates to a human owner (FR-035, P6).
- `T5` — `financial_gate → release_routed` requires both clearance gates recorded, in **either** order (FR-033).
- `T6` — Any open blocker suspends transitions (INV-C2). A newly detected critical signal **revokes** provisional status and holds progression (FR-011, edge case).

### 3.2 Escalation outcome (FR-054 precedence — exactly one outcome)

```text
critical signal detected (register match, FR-057)
        │
        ├─ start acknowledgement clock at DETECTION (FR-056)
        │
        ▼
 all four designations present?
 (clinical recipient · dispatch approver · approved deadline · on-call coverage)
        │
        ├── NO ──► GOVERNANCE BLOCKER  ── lists EVERY absent designation
        │           (outranks completeness, even for a missing recipient
        │            that is also a mandatory P3 packet field)
        ▼ YES
 deadline strictly shorter than applied ack SLA?
        ├── NO ──► GOVERNANCE BLOCKER (FR-052)
        ▼ YES
 all 7 mandatory content fields present?
        ├── NO ──► COMPLETENESS BLOCKER ─► Clinical Authority + Intake Coordinator
        │                                   signal stays visibly active (FR-026)
        ▼ YES
 DISPATCH APPROVAL (non-suppressible) ──► approved ──► dispatched to recipient
                                     └──► rejected ──► undispatched, rationale
                                                        recorded, signal active
                                     └──► deadline breach ──► breach recorded,
                                                        escalate to alternate,
                                                        NEVER dispatched
```

### 3.3 Approval task

```text
opened ──► pending ──┬──► approved
                     ├──► edited (edited text becomes authoritative — FR-032)
                     ├──► rejected ──► case returns to producing stage (FR-031)
                     └──► returned_for_rework ──► rework_loop_count += 1
                                                  (at 2 ⇒ human escalation)
        │
        ├─ at 80% applied SLA ──► early warning (P5)
        └─ at 100% applied SLA ──► breach recorded — no auto-approve (FR-023)
```

---

## 4. Requirement → entity coverage

| Entity | Requirements realised |
|---|---|
| Case | FR-001, FR-005, FR-035, FR-039, FR-040 |
| Case Record / Field | FR-002, FR-003, FR-004, FR-006, FR-007, FR-009 |
| Data Completion Task | FR-008, FR-016, FR-041 |
| Routing Decision | FR-010, FR-011, FR-012, FR-013, FR-017, FR-018, FR-045 |
| Duplicate Flag | FR-014, FR-015, FR-055 |
| Approval Task | FR-019, FR-020, FR-021, FR-022, FR-023, FR-029, FR-030, FR-056 |
| Escalation Packet | FR-024..FR-028, FR-051..FR-054, FR-057 |
| Clearance Gate | FR-033, FR-034 |
| Draft Artifact | FR-029, FR-031, FR-032 |
| Blocker | FR-007, FR-026, FR-028, FR-041, FR-054 |
| Refusal Record | FR-036, FR-037 |
| Audit Event | FR-042, FR-043, FR-044, FR-045, FR-047 |
| Policy Bundle | FR-045, FR-046, FR-048, FR-049, FR-050 |
| Role / Designation | FR-030, FR-034, FR-038, FR-051 |

All 57 functional requirements are covered by at least one entity or invariant.
