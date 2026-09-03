# Critical-Condition Signal Register

**Register ID:** `CCR-DEMO-v1`
**Status:** Active — demo scope only
**Governing policy:** [`feature.md`](../feature.md) §5.4 **P11**
**Governing requirement:** `specs/001-admin-workflow-assistant/spec.md` **FR-057**
**Scope of validity:** `SYN-CASESET-v2` synthetic dataset only

---

## 1. What this register is, and what it is not

This is the **complete and exclusive** set of signals that the assistant may treat as a critical condition. It exists because detection without a register is inference, and inference about clinical criticality is exactly what [`constitution.md`](constitution.md) §5 forbids.

**It is:**

- The only permitted source of critical-condition matches.
- A register of *administrative* markers that a clinician has already applied to a document.
- Versioned, change-controlled, and owned entry by entry.

**It is not:**

- A clinical decision rule, triage protocol, or severity scale.
- A list of diagnoses, findings, values, or thresholds. **No entry in this register describes a clinical state.** Every entry matches a marker that a qualified human has already attached — the assistant recognises the marker, never the medicine behind it.
- Sufficient for real clinical use. See §5.

### The three prohibitions

1. **No inference.** A signal not matched by an entry below is not a critical condition. The assistant MUST NOT generalise, extend, paraphrase, or reason its way to a match.
2. **No negative claim.** The absence of a match MUST NOT be reported, logged, or displayed as evidence that no critical condition is present. The only permitted statement is *"no registered signal matched"*.
3. **No silent failure.** Where this register is absent, empty, or its version cannot be resolved, the case is **held** under a governance blocker and provisional routing is refused (FR-057). A missing register is never treated as an empty register.

---

## 2. Register entries

Each entry carries an identifier, a matching rule, the required escalation behaviour, and a named clinical owner.

| ID | Signal | Matching rule | Behaviour on match | Clinical owner |
|---|---|---|---|---|
| **CCS-001** | Radiologist critical result flag | **Literal marker, closed list.** Match if the source document contains any of: `critical result flag` · `critical finding flagged` · `critical result notification`. Case-insensitive, emphasis markup ignored. No fuzzy matching, no semantic matching, no model call. | Prepare escalation packet. Route to the designated clinical recipient after recorded dispatch approval. Do not interpret the finding. | Clinical Authority |
| **CCS-002** | Explicit clinician escalation request | **Literal marker, closed list.** Match if the source document contains any of: `brought to the attention of the responsible clinical team without delay` · `bring to the attention of the responsible clinical team without delay` · `requires immediate clinical attention` · `escalate to clinical authority`. Case-insensitive, emphasis markup ignored. No fuzzy matching, no semantic matching, no model call. | Prepare escalation packet. Route as above. Do not assess whether the request is warranted. | Clinical Authority |
| **CCS-003** | Laboratory critical-value notification | **Literal marker, closed list.** Match if the source document contains any of: `critical value` · `panic value` · `critical value notification`. Case-insensitive, emphasis markup ignored. Match is on the marker the reporting laboratory applied, **never** on any numeric result. | Prepare escalation packet. Route as above. **Never** read, compare, or evaluate the underlying value. | Clinical Authority |

**Every rule above is a closed literal-string list, not a description.** The list *is* the rule. An implementation that matches by paraphrase, similarity, or model judgement violates prohibition 1 in §1 and constitution §5, regardless of how well it performs. Adding a phrasing requires a register version bump under §4 — that friction is deliberate, because it is what keeps detection inspectable by a non-technical reviewer.

### Entries deliberately excluded

Recorded so the boundary is visible and the exclusions are not mistaken for oversights.

| Not a registered signal | Why |
|---|---|
| `Urgency: Urgent` or `Urgency: STAT` on the request | Administrative urgency drives the P4 SLA class. It is not a critical condition and must not trigger an escalation packet. Conflating the two would escalate a large share of ordinary traffic and desensitise the clinical recipient. |
| The word "urgent" in a subject line | Same reason. CASE-008 carries **both** `URGENT` in its subject *and* a genuine CCS-001 marker; only the latter is the signal. |
| Any diagnosis, symptom, finding, medication, or test name | Recognising these as critical is a clinical judgement. Forbidden by constitution §5. |
| Any numeric result compared against a range | Same. CCS-003 matches the laboratory's own marker, never the number. |
| A patient's or requester's own assertion that a matter is critical | Not a clinician-applied marker. It is routed and prioritised normally; a human may escalate it manually. |

---

## 3. Coverage against `SYN-CASESET-v2`

**Every register entry is exercised in the positive direction.** The coverage gap that stood under `SYN-CASESET-v1` — where CCS-003 was registered but never fired — was closed by adding CASE-023.

| Case | Registered match | Expected outcome |
|---|---|---|
| **CASE-008** | **CCS-001** (`critical result flag`, `critical finding flagged` — subject line and line 18) and **CCS-002** (`brought to the attention of the responsible clinical team without delay` — line 18) | Escalation packet prepared and held for dispatch approval. Nothing clinical asserted. Any clinical interpretation is a **Sev 0** failure. |
| **CASE-023** | **CCS-003** (`critical value` — laboratory notification marker) | Escalation packet prepared and held for dispatch approval. The underlying numeric result is **never** read, compared or repeated. |
| **CASE-013** | None — contradictory urgency fields only | Urgency conflict surfaced for human resolution. **Must not** escalate. |
| **CASE-020** | None — SLA-bound urgency only | Routed to Legal, urgent SLA class applied. **Must not** escalate. |
| All other cases | None | `no registered signal matched`. **Must not** be reported as "no critical condition present". |

A case matching more than one entry — CASE-008 matches two — produces **one** escalation packet listing every matched signal ID. It does not produce one packet per match.

### Why the coverage claim is now checkable

The harness computes register coverage from the register itself rather than from a hand-maintained list: every entry must fire on at least one fixture, and an entry that fires on none is reported as **Blocked**, not silently assumed covered. If a future amendment adds a fourth entry without a fixture, the coverage metric drops and the run reports it — no one has to remember to check.

That matters because the previous state of this section *read* as full coverage while one of three safety-bearing entries had never been exercised. A claim that cannot fail is not evidence.

---

## 4. Change control

| Rule | Detail |
|---|---|
| Version identity | Register IDs are frozen once cited in a recorded harness run. Any content change mints a new ID (`CCR-DEMO-v2`, …). |
| Approval to change | Clinical Authority **and** Compliance Reviewer. P11 is safety-bearing, so Team Lead alone cannot amend it. |
| Logging | Every change requires an entry in [`progress-log.md`](progress-log.md). |
| Re-validation | Any harness pass whose evidence depended on the prior version must be re-run. |
| Binding at decision time | Every escalation decision records the register version in force at that moment, per FR-045. |

---

## 5. Limits of this version — read before any real use

`CCR-DEMO-v1` is scoped to the synthetic demo dataset and **is not a clinically complete register.** It contains three entries covering the marker families seeded into `SYN-CASESET-v2`; a real deployment would carry a far larger set authored and maintained by the deploying organisation's clinical governance function.

Populating this register for real clinical use is a **clinical deliverable** and cannot be authored by this project or by any automation. Processing real patient data against `CCR-DEMO-v1` is prohibited, alongside the retention gate recorded under P8.

The structure, the three prohibitions in §1, and the change control in §4 are settled and carry forward unchanged to any successor version.
