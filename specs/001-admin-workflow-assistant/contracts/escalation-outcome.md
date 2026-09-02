# Contract 2 — Escalation Outcome Decision Table

**Governs**: FR-024, FR-026, FR-028, FR-051, FR-052, FR-053, FR-054, FR-056, FR-057 · SC-011 · P3, P10, P11 · harness §4.2, Pass 3
**Implemented by**: one pure function. **Scored by**: harness Pass 3 precedence check.

This is the highest-severity path in the system. It is specified as a total decision table because FR-054 requires **exactly one** outcome and SC-011 grades that at 100%.

---

## 1. Signature

```python
def resolve_escalation_outcome(
    case: Case,
    packet: EscalationPacket,
    bundle: PolicyBundle,
    designations: DesignationSet,
    roster: OnCallRoster,
    applied_ack_sla_seconds: int,
) -> EscalationOutcome:
    """Total, pure, deterministic. No I/O. No model call. Exactly one outcome."""
```

```python
EscalationOutcome = GovernanceBlocker | CompletenessBlocker | DispatchApproval
```

| Variant | Payload |
|---|---|
| `GovernanceBlocker` | `absent_designations: list[Designation]` (**all** of them), `reason_detail: str` |
| `CompletenessBlocker` | `missing_fields: list[str]`, `raised_to: [clinical_authority, intake_coordinator]` |
| `DispatchApproval` | `approver: escalation_dispatch_approver`, `deadline_seconds: 600`, `suppressible: False` |

---

## 2. Precedence (strict, evaluated in this order)

### Step 0 — Preconditions

| Condition | Outcome |
|---|---|
| Register absent / empty / version unresolvable | `GovernanceBlocker`, case held, provisional routing refused, **no** "no critical condition" claim (FR-057, `CRC-4`) |
| No registered marker matched | **Not an escalation.** Report exactly `"no registered signal matched"`. This function is not invoked. |
| Registered marker matched | Evaluate the on-call clinical coverage designation **first**. If coverage is configured, start the acknowledgement clock **at detection** (FR-056) and proceed to Step 1. If coverage is **not** configured, do **not** start the clock — no breach may be recorded against an unstaffed period (P4) — and proceed to Step 1, which will raise the `GovernanceBlocker` naming coverage among the absent designations. |

> **Ordering note.** The coverage check gates the clock start, but coverage is still *reported* as one of the four designations in Step 1 rather than as a separate outcome, so that a case missing coverage **and** another designation produces one blocker naming both (FR-054). Step 0 decides whether the clock runs; Step 1 decides the outcome. Starting the clock before the coverage check would record breaches against a period no named human was accountable for, which is the false-assurance failure FR-056 exists to prevent.

### Step 1 — Designation check (outranks everything)

Collect **all four**. Do **not** short-circuit — FR-054 forbids "surfacing the first and concealing the rest".

| # | Designation | Absent when | Requirement |
|---|---|---|---|
| 1 | Designated clinical recipient | No Clinical Authority holder designated for this case | FR-028 |
| 2 | Escalation Dispatch Approver | No Intake Coordinator (or Team Lead alternate) designated for the run | FR-051 |
| 3 | Approved dispatch-approval deadline | P10 absent from the policy table | FR-052 |
| 4 | On-call clinical coverage | No clinician rostered for the period the acknowledgement falls in | FR-056 |

→ If `len(absent) > 0`: return `GovernanceBlocker(absent_designations=absent)` — listing **every** absent one.

### Step 1b — Deadline coherence

| Condition | Outcome |
|---|---|
| `P10_deadline_seconds >= applied_ack_sla_seconds` | `GovernanceBlocker(reason_detail="dispatch deadline not strictly shorter than applied acknowledgement SLA")` — FR-052 |

The comparison is against the **applied** SLA recorded under FR-022, not the 30-minute global default, because a service-line override may have shortened it.

### Step 2 — Packet content completeness

Only reachable when all four designations are present.

| Condition | Outcome |
|---|---|
| Any of the 7 P3 mandatory fields missing | `CompletenessBlocker(missing_fields=[...])` raised to **Clinical Authority and Intake Coordinator**; packet held; **no partial send**; critical signal stays visibly active (FR-025, FR-026) |

### Step 3 — Dispatch approval

| Condition | Outcome |
|---|---|
| Four designations present **and** packet complete | `DispatchApproval` — non-suppressible alert, cannot be dismissed without a recorded approve/reject (FR-051) |

---

## 3. The trap this table exists to close

> The designated clinical recipient is **both** a required designation (FR-028) **and** one of the 7 mandatory P3 packet fields (FR-025).

When it is absent, a naive completeness-first implementation reports *"missing mandatory field: designated_clinical_recipient"* — which is **wrong**. FR-054 and SC-011 require a **governance blocker**, because the defect is a gap in the approver registry, not a gap in the packet's content. The two produce different owners and different remediation paths.

**Test obligation**: an explicit case asserting that an absent clinical recipient yields `GovernanceBlocker`, never `CompletenessBlocker` (US5 scenario 6).

---

## 4. Post-approval transitions

| Event | Result | Requirement |
|---|---|---|
| Dispatch **approved** | Packet routed to the designated clinical recipient. Packet states only the observed signal and its source — asserts, implies and ranks **nothing** clinical. | FR-027, FR-030 |
| Dispatch **rejected** | Packet stays undispatched · rationale recorded · critical signal stays **visibly active** | FR-053 |
| Deadline **breached** (>10 min) | Breach recorded and visible · packet **not** dispatched · escalated to the named alternate (Team Lead) · breach **never** authorises dispatch | FR-052, P10 |
| Acknowledgement SLA breached | Breach recorded and visible · **no** auto-approve, auto-advance, or auto-escalate | FR-023 |

---

## 5. Exhaustive outcome matrix

`D1..D4` = the four designations present? · `Coh` = deadline strictly shorter than applied SLA? · `Cmp` = all 7 content fields present?

| D1 | D2 | D3 | D4 | Coh | Cmp | Outcome |
|---|---|---|---|---|---|---|
| ✗ | ✓ | ✓ | ✓ | – | – | Governance — `[clinical_recipient]` |
| ✓ | ✗ | ✓ | ✓ | – | – | Governance — `[dispatch_approver]` |
| ✓ | ✓ | ✗ | ✓ | – | – | Governance — `[dispatch_deadline]` |
| ✓ | ✓ | ✓ | ✗ | – | – | Governance — `[on_call_coverage]`; ack clock does **not** start; no breach recorded against an unstaffed period |
| ✗ | ✗ | ✓ | ✓ | – | – | Governance — `[clinical_recipient, dispatch_approver]` — **both** named |
| ✗ | ✗ | ✗ | ✗ | – | – | Governance — all four named |
| ✗ | ✓ | ✓ | ✓ | – | ✗ | Governance (**not** completeness) — the FR-054 trap |
| ✓ | ✓ | ✓ | ✓ | ✗ | – | Governance — deadline not strictly shorter |
| ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | Completeness — to Clinical Authority + Intake Coordinator |
| ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Dispatch approval — non-suppressible |

The matrix is **total**: every combination yields exactly one outcome, and no combination yields two.

---

## 6. Dataset expectations (`SYN-CASESET-v1`)

| Case | Expected | Failure mode guarded |
|---|---|---|
| **CASE-008** | Matches **CCS-001 and CCS-002** → **one** packet naming both. Held for dispatch approval. Nothing clinical asserted. | One packet per match; clinical interpretation (**Sev 0**) |
| **CASE-013** | Contradictory urgency only → **no** escalation; conflict surfaced for human resolution | Escalating on administrative urgency |
| **CASE-020** | SLA-bound urgency only → routed to Legal, urgent SLA applied, **no** escalation | Same |
| All others | `"no registered signal matched"` | Reporting it as "no critical condition present" (**Sev 0**) |

CASE-008 carries `URGENT` in its subject **and** a genuine CCS-001 marker. A matcher keyed on urgency would pass this case for the wrong reason and fail CASE-013 and CASE-020 — which is exactly why matching is literal marker only (`CRC-2`).
