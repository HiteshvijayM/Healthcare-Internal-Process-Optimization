# Sample Dataset — Provenance and Structure

## 1. Provenance Statement

**Every document in this dataset is synthetic.** It was authored by hand for this project. It is not derived from, sampled from, anonymised from, or inspired by any real patient record, any real clinical system, or any real organisation.

- No real patient data was accessed, ingested, transformed, or referenced at any point.
- All patient references use the reserved synthetic prefix `SYN-PT-`.
- All people, practices, payers, plan names, and organisations are fictional.
- All ordering references use the reserved synthetic prefix `ORD-`.

This satisfies [`docs/constitution.md`](../docs/constitution.md) §3, which requires synthetic or de-identified data only and mandates provenance notes for any dataset used in demos or evaluations.

If a document in `sample/` ever fails to meet the statement above, it is a **Sev 0 constitutional violation** under [`docs/multipass-validation-harness.md`](../docs/multipass-validation-harness.md) §5 and is an immediate stop-run.

## 2. Dataset Identity

| Field | Value |
|---|---|
| Dataset ID | `SYN-CASESET-v1` |
| Case count | 20 (`CASE-001` … `CASE-020`) |
| Document format | Markdown, simulating inbound email and fax-cover administrative requests |
| Answer key | [`sample/answer-key.json`](sample/answer-key.json) |

Scanned and OCR documents are deliberately **not** included. Per [`prompts/specify-prompt.md`](../prompts/specify-prompt.md) §3, text-layer documents come first; OCR is a later addition once the clean path works.

## 3. Routing Queues

A case routes to exactly one of five fixed queues. The set matches the F11 approver roles and is not dynamic or customer-configurable.

| Queue | Handles |
|---|---|
| **Insurance** | Eligibility verification, coverage confirmation, benefits enquiries |
| **Operations** | Scheduling, transfer coordination, release preparation, general intake |
| **Diagnostics** | Imaging and test scheduling, diagnostic order handling |
| **Legal** | Records disclosure, subpoena response, compliance and audit retrieval |
| **Finance** | Billing, statements, payment plans, financial clearance |

## 4. Extracted Fields

Per [`prompts/specify-prompt.md`](../prompts/specify-prompt.md) §3, the fields extracted from every case are:

`requester` · `patient_reference` · `requested_service` · `urgency` · `payer_plan` · `ordering_reference` · `supporting_notes` · `date`

**Seven of these are graded** for extraction accuracy, and they are the seven listed in `graded_fields` in [`sample/answer-key.json`](sample/answer-key.json):

`requester` · `patient_reference` · `requested_service` · `urgency` · `payer_plan` · `ordering_reference` · `date`

`supporting_notes` is **extracted but not graded**. It is free narrative text with no single correct value, so scoring it as an exact match would be meaningless and scoring it by judgement would make the accuracy figure irreproducible — which P7 forbids. It is still carried on the case record and still appears in drafts and escalation packets; it simply contributes no denominator to the ≥ 85% extraction target.

**The answer key is the operative artifact.** Where this README and `answer-key.json` ever disagree on which fields are graded, the answer key governs and the discrepancy is a defect in this file. The graded denominator is therefore **7 fields × 20 cases = 140**, and every reported percentage states it (see `feature.md` §7 reporting rule).

`payer_plan` is recorded as `"Not applicable"` — not as missing — on records and legal requests where no payer is involved. Treating it as a seeded omission is a **false positive**.

## 5. Grading Subsets

The answer key defines which cases feed which metric in [`feature.md`](../feature.md) §7.

| Metric | Cases | Count |
|---|---|---|
| Field extraction accuracy (≥ 85%) | All cases, 7 graded fields each (n = 140) | 20 |
| Missing-field detection (catch every seeded omission) | `seeded_omission` subset | 10 |
| Routing accuracy (≥ 9/10) | `routing_graded` subset, covering all five queues | 10 |

## 6. Seeded Conditions

| Condition | Cases |
|---|---|
| Seeded omissions | CASE-002, 003, 004, 011, 012, 013, 014, 017, 019, 020 |
| — resolved by backfill from records | CASE-002, 011, 014, 017 |
| — resolved by a later correction from the requester | CASE-004 |
| — not resolvable; must raise a completion task | CASE-003, 012, 013, 019 |
| — not resolvable; a new internal reference must be assigned | CASE-020 |
| Duplicate submissions | CASE-005 (of CASE-001), CASE-018 (of CASE-016) |
| Near-duplicate guard — must **not** flag | CASE-017 |
| Contradictory fields | CASE-013 |
| Misroute traps | CASE-006, CASE-020 |
| `Not applicable` false-positive traps | CASE-012, CASE-014, CASE-020 |
| Critical-condition escalation trigger | CASE-008 (matches **CCS-001** and **CCS-002** in `CCR-DEMO-v1`) |
| Clinical clearance gate | CASE-009 |
| Financial clearance gate | CASE-010 |
| Provisional routing then correction | CASE-004 |
| Parallel approval fan-out | CASE-007 |
| SLA-bound urgency | CASE-008, CASE-020 |

### 6.1 Deliberate Traps

These exist to catch over-eager behaviour, not just under-detection:

- **CASE-006** reads like an Insurance matter but coverage is already settled; it belongs to Finance.
- **CASE-020** has "Insurance" in the requester's name but is a Legal records matter.
- **CASE-017** shares a requester with CASE-016 and CASE-018 but has a different patient and a different service. Flagging it as a duplicate is a false positive.
- **CASE-012, 014, 020** carry `payer_plan: "Not applicable"`. Reporting these as missing is a false positive.
- **CASE-013** must be neither silently accepted as STAT nor silently downgraded. The conflict is surfaced; a human resolves it.
- **CASE-008** must produce an escalation packet and nothing more. Any clinical interpretation of the critical flag is a Sev 0 failure under [`docs/constitution.md`](../docs/constitution.md) §5.

### 6.2 Known Coverage Gaps

`SYN-CASESET-v1` does not exercise everything the specification requires graded. These gaps are recorded rather than left to be discovered, and each blocks a specific harness pass until a successor dataset closes it.

| Gap | What is missing | Blocks | Closing it |
|---|---|---|---|
| **SC-009 identity matcher** | An exact re-send arriving **after** the 72-hour key window has closed, against an already-closed case. Both existing duplicates (CASE-005 at ~6h, CASE-018 at ~20h) fall inside the window, so both are *key* matches — the unbounded document-identity matcher (FR-055) is never exercised on its own, and a key-match-only implementation would pass by accident. | Pass 2 | New fixture case |
| **SC-009 identity false positive** | A later submission sharing the sender/patient/service key but carrying **genuinely different content**, which must **not** be identity-flagged. CASE-017 is a *different-key* guard, not this one, so an over-broad content normaliser would go undetected. | Pass 2 | New fixture case |
| **CCS-003** | No case carries a laboratory critical-value or panic-value marker, so the third register entry in `CCR-DEMO-v1` is registered but never fires. Its negative direction is covered; its positive direction is not. | Pass 3 evidence must name CCS-003 as uncovered | New fixture case |

Adding any of these mints a new dataset ID under §7. Until then, the affected checks are recorded as **Blocked**, never as passed — a Blocked run is not a Pass (harness §4).

## 7. Change Control

This dataset is versioned. Any change to case content or to the answer key requires:

1. A new dataset ID (`SYN-CASESET-v2`, and so on) — existing IDs are frozen once used in a recorded run.
2. An entry in [`docs/progress-log.md`](../docs/progress-log.md).
3. Re-running any harness pass whose evidence depended on the previous version.
