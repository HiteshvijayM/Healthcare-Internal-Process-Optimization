# Contract 3 — Conversational Command Surface

**Governs**: F22, P9 · FR-029, FR-030, FR-036, FR-038, FR-039, FR-041 · harness Pass 6
**Surface**: a single web/in-app conversational surface (Copilot SDK), one demo tenant, one authenticated reviewer session.

The surface holds **no business logic**. It renders workflow state and submits human decisions to the same workflow API the eval CLI uses (research D17), so the demonstrated path and the graded path cannot diverge.

---

## 1. Command surface

Every command declares whether it produces an **outbound effect**. Effect-producing commands cannot execute without a recorded approval reference (Contract: `ActionGate`, FR-030).

| Command | Intent | Effect? | Required role | Requirements |
|---|---|---|---|---|
| `submit_case(document, channel)` | Register an arriving request | No | any authenticated | FR-001, FR-005 |
| `get_case(case_id)` | Full case view: stage, owner, elapsed, fields, provenance | No | any authenticated | FR-039, FR-041 |
| `get_status_board()` | All in-flight cases: stage, owner, elapsed, approvals, blockers, provisional flags | No | any authenticated | FR-039, FR-040, FR-041 |
| `list_blockers(case_id?)` | Open blockers incl. unresolved completion tasks with owners | No | any authenticated | FR-041 |
| `get_routing_explanation(case_id)` | One-line reason + full rule trace + policy version | No | any authenticated | FR-017, FR-018, FR-045 |
| `list_pending_approvals(role?)` | Approvals awaiting decision, blocking flagged | No | any authenticated | FR-020, FR-021 |
| `decide_approval(task_id, approve\|edit\|reject\|return_for_rework, rationale?, edited_text?)` | Record a human decision | **Yes** | the task's role | FR-029, FR-030, FR-031, FR-032 |
| `adjudicate_duplicate(flag_id, confirmed\|not_duplicate, rationale)` | Resolve a duplicate flag | **Yes** | Intake Coordinator | FR-015 |
| `approve_dispatch(packet_id, approve\|reject, rationale?)` | Escalation dispatch decision | **Yes** | Escalation Dispatch Approver | FR-051, FR-053 |
| `record_clearance(case_id, clinical\|financial)` | Record a clearance gate | **Yes** | Clinical Authority / Finance Clearance Approver | FR-033, FR-034 |
| `route_for_release(case_id)` | Terminal release routing | **Yes** | Operations Approver | FR-033 |
| `resolve_completion_task(task_id, value)` | Supply a missing field value | No (updates record) | the task's owner role | FR-008, FR-016 |
| `get_case_history(case_id)` | Ordered, masked audit reconstruction | No | Compliance Reviewer | FR-042, FR-043, FR-044 |
| `run_eval(dataset_id, mode=replay)` | Execute the graded run | No | Team Validation Lead | FR-048, FR-049 |

---

## 2. Enforcement rules

- `SC-A1` — **Every** `Effect? = Yes` command routes through `ActionGate.execute(effect, approval_ref)`. There is no other path to an outbound effect (FR-030, SC-008).
- `SC-A2` — The agent principal cannot satisfy any role check. It is unrepresentable in the role type, not merely rejected (FR-038, harness §4.1).
- `SC-A3` — `decide_approval` with `edit` stores the edited text as **authoritative**, and it stays authoritative even if the artifact is later rejected (FR-032).
- `SC-A4` — `reject` returns the case to the stage that produced the rejected output, never earlier than data completion, and captures rationale (FR-031). `rationale` is **required** for `reject` and `return_for_rework`.
- `SC-A5` — `return_for_rework` increments the loop count; the third attempt escalates to a human owner instead of looping (FR-035, P6).
- `SC-A6` — A pending dispatch approval surfaces as a **non-suppressible** alert that cannot be dismissed without a recorded approve or reject (FR-051).
- `SC-A7` — `record_clearance` accepts either gate first and refuses neither for ordering; it refuses a second clearance by the same principal on separation-of-duty grounds (FR-033, FR-034).
- `SC-A8` — `route_for_release` refuses while either clearance is outstanding and **names the outstanding gate** (FR-033).

---

## 3. Safety boundary on the conversational edge

Applied to **every inbound turn and every outbound response**, independent of stage (FR-036, research D13).

**Refused acts**: diagnosis · treatment recommendation · medical-necessity determination · clinical clearance authorisation · discharge/release authorisation.

**Refusal contract**

1. Decline the request.
2. State that the decision belongs to a qualified human.
3. Name the appropriate human authority (Clinical Authority for clinical acts; Finance Clearance Approver for financial clearance).
4. Write a Refusal Record to the case history (FR-037).

Refusal wording is a **fixed template** derived from `docs/constitution.md` §5 and canonical per `feature.md` §13.4. It is never model-generated and never softened. SC-014 requires 100% refusal, so the check is deterministic (research D13).

**Outbound checking matters as much as inbound**: it is what stops a drafting step from letting clinical assertion into an escalation packet, which FR-027 forbids and which CASE-008 grades as **Sev 0**.

---

## 4. Demo journey (harness Pass 6 — "chat-flow completion across core journey")

Mirrors `feature.md` §8:

```text
submit_case(CASE-001)            → registered, extracted, routed with reason, draft ready
get_routing_explanation()        → one-line reason + rule trace + policy version
submit_case(CASE-003)            → held; missing fields named; chase message drafted
decide_approval(edit → approve)  → edited text becomes authoritative
decide_approval(reject)          → returns a stage; nothing sent
<clinical question>              → refused, directed to Clinical Authority, recorded
submit_case(CASE-008)            → one packet (CCS-001 + CCS-002); non-suppressible dispatch approval
get_status_board()               → stages, owners, elapsed time, blockers, provisional flags
run_eval()                       → scorecard in harness §10 format
```
