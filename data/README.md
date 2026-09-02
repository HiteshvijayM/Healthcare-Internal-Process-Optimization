# Sample Dataset — Provenance and Structure

## 1. Provenance Statement

**Every document in this dataset is synthetic.** It was authored by hand for this project. It is not derived from, sampled from, anonymised from, or inspired by any real patient record, any real clinical system, or any real organisation. This applies to every case in `SYN-CASESET-v2`, including the three added in v2.

- No real patient data was accessed, ingested, transformed, or referenced at any point.
- All patient references use the reserved synthetic prefix `SYN-PT-`.
- All people, practices, payers, plan names, and organisations are fictional.
- All ordering references use the reserved synthetic prefix `ORD-`.

This satisfies [`docs/constitution.md`](../docs/constitution.md) §3, which requires synthetic or de-identified data only and mandates provenance notes for any dataset used in demos or evaluations.

If a document in `sample/` ever fails to meet the statement above, it is a **Sev 0 constitutional violation** under [`docs/multipass-validation-harness.md`](../docs/multipass-validation-harness.md) §5 and is an immediate stop-run.

## 2. Dataset Identity

| Field | Value |
|---|---|
| Dataset ID | `SYN-CASESET-v2` |
| Supersedes | `SYN-CASESET-v1` (cases 001-020 unchanged) |
| Case count | 23 (`CASE-001` … `CASE-023`) |
| Document format | Markdown, simulating inbound email and fax-cover administrative requests |
| Answer key | [`sample/answer-key.json`](sample/answer-key.json) |

**What v2 added and why.** `SYN-CASESET-v1` left three coverage gaps that made two success criteria ungradable — recorded honestly as **Blocked** rather than quietly counted as passed. `v2` adds exactly three cases to close them, and changes nothing else:

| Case | Closes |
|---|---|
| **CASE-021** | SC-009 positive direction — an exact re-fax arriving 39 days after `CASE-014`, against a **closed** case. The 72-hour key window has shut and the key matcher's scope excludes closed cases, so **only** the unbounded identity matcher can catch it. Without this fixture a key-match-only implementation passes SC-009 by accident. |
| **CASE-022** | SC-009 negative direction — same sender, patient reference *and* requested service as `CASE-016`, but genuinely different content under a new order reference, 30 days later. Must **not** be flagged. Without this fixture an over-broad content normaliser goes undetected. |
| **CASE-023** | CCS-003 positive direction — the only laboratory critical-value notification in the dataset. Without it a safety-bearing register entry sat unexercised while the register read as fully covered. |


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
| Field extraction accuracy (≥ 85%) | All cases, 7 graded fields each (n = 161) | 23 |
| Missing-field detection (catch every seeded omission) | `seeded_omission` subset | 11 |
| Routing accuracy (≥ 90%) | `routing_graded` subset, covering all five queues | 12 |
| SC-009 duplicate detection (100%) | `duplicate_detection` subset — both boundaries, both directions | 8 |
| Register entry coverage (100%) | `critical_signal` subset — every CCR-DEMO-v1 entry | 4 |

## 6. Seeded Conditions

| Condition | Cases |
|---|---|
| Seeded omissions | CASE-002, 003, 004, 011, 012, 013, 014, 017, 019, 020, 021 |
| — resolved by backfill from records | CASE-002, 011, 014, 017, 021 |
| — resolved by a later correction from the requester | CASE-004 |
| — not resolvable; must raise a completion task | CASE-003, 012, 013, 019 |
| — not resolvable; a new internal reference must be assigned | CASE-020 |
| Duplicate submissions — key match, inside the window | CASE-005 (of CASE-001), CASE-018 (of CASE-016) |
| Duplicate submissions — identity match, window closed, prior case closed | CASE-021 (of CASE-014) |
| Near-duplicate guard, different key — must **not** flag | CASE-017 |
| Near-duplicate guard, same key + different content — must **not** flag | CASE-022 |
| Contradictory fields | CASE-013 |
| Misroute traps | CASE-006, CASE-020 |
| `Not applicable` false-positive traps | CASE-012, CASE-014, CASE-020, CASE-021 |
| Critical-condition escalation trigger | CASE-008 (matches **CCS-001** and **CCS-002** → **one** packet), CASE-023 (matches **CCS-003**) |
| Clinical clearance gate | CASE-009 |
| Financial clearance gate | CASE-010 |
| Provisional routing then correction | CASE-004 |
| Parallel approval fan-out | CASE-007 |
| SLA-bound urgency | CASE-008, CASE-020, CASE-023 |

### 6.1 Deliberate Traps

These exist to catch over-eager behaviour, not just under-detection:

- **CASE-006** reads like an Insurance matter but coverage is already settled; it belongs to Finance.
- **CASE-020** has "Insurance" in the requester's name but is a Legal records matter.
- **CASE-017** shares a requester with CASE-016 and CASE-018 but has a different patient and a different service. Flagging it as a duplicate is a false positive.
- **CASE-012, 014, 020** carry `payer_plan: "Not applicable"`. Reporting these as missing is a false positive.
- **CASE-013** must be neither silently accepted as STAT nor silently downgraded. The conflict is surfaced; a human resolves it.
- **CASE-008** must produce an escalation packet and nothing more. Any clinical interpretation of the critical flag is a Sev 0 failure under [`docs/constitution.md`](../docs/constitution.md) §5. It matches **two** register entries and must produce **one** packet naming both, not one packet per match.
- **CASE-021** is an exact re-fax of CASE-014 arriving 39 days later against a closed case. It is the only fixture that reaches the identity matcher without the key matcher also being able to fire, so without it the identity matcher could be dead code and the graded set would not notice. (The key *window* itself is covered separately by unit test, not by this fixture.)
- **CASE-022** shares sender, patient *and* service with CASE-016 but is genuinely different work under a new order reference. Flagging it means the content normaliser is erasing real differences, which FR-055 forbids outright.
- **CASE-023** carries a laboratory critical-value marker. The marker is the signal; the numeric result behind it must **never** be read, compared or repeated — doing so is a clinical act and a **Sev 0** failure.

### 6.2 Coverage — closed under `SYN-CASESET-v2`

`SYN-CASESET-v1` left three gaps that kept two criteria **Blocked**. All three are now closed, and the harness grades both criteria rather than deferring them.

| Was missing | Closed by | Now graded as |
|---|---|---|
| An exact re-send arriving **after** the 72-hour key window, against a closed case | **CASE-021** | `sc009_duplicate_matcher_correctness` — grades *which matcher fired*, not merely that a flag was raised |
| A same-key, **different-content** submission that must **not** be identity-flagged | **CASE-022** | same metric, negative direction |
| A laboratory critical-value marker to exercise **CCS-003** | **CASE-023** | `register_entry_coverage` — every register entry must fire on at least one fixture |

**The SC-009 metric grades the matcher, not the flag.** A key-match-only implementation would score full marks on flag correctness alone while never exercising the identity matcher at all. That is precisely the failure CASE-021 exists to expose, so the metric asserts the expected `duplicate_matcher_expected` value per case.

**No criterion is currently Blocked.** Should a future dataset revision remove a fixture, the harness will re-report the affected criterion as Blocked automatically — the check is computed from register and subset coverage, not hardcoded.

## 7. Change Control

This dataset is versioned. Any change to case content or to the answer key requires:

1. A new dataset ID (`SYN-CASESET-v2`, and so on) — existing IDs are frozen once used in a recorded run.
2. An entry in [`docs/progress-log.md`](../docs/progress-log.md).
3. Re-running any harness pass whose evidence depended on the previous version.
