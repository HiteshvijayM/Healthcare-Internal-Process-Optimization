# Interface Contracts — Administrative Workflow Assistant

**Feature**: `001-admin-workflow-assistant` · **Phase**: 1 · **Date**: 2026-09-02

These are the interfaces this project exposes to humans and to other systems. They are the surfaces a reviewer inspects and the harness scores against, so they are pinned here **before** implementation.

The project exposes no public network API — `feature.md` §4 excludes live EHR integration, payer submission and production hosting. The real contracts are therefore: the **declarative policy configuration** a non-technical reviewer must be able to read, the **conversational command surface** (P9), the **audit event record** a compliance reviewer replays, and the **evaluation scorecard** that carries every claim.

| # | Contract | File | Consumed by | Authority |
|---|---|---|---|---|
| 1 | Policy bundle configuration | [`policy-config.md`](./policy-config.md) | Reviewers, routing engine, SLA engine | `feature.md` §5.4, §9, §13.5; harness §4 |
| 2 | Escalation outcome decision table | [`escalation-outcome.md`](./escalation-outcome.md) | Escalation resolver, harness Pass 3 | FR-054, SC-011, harness §4.2 |
| 3 | Conversational command surface | [`agent-surface.md`](./agent-surface.md) | Copilot SDK surface, eval CLI | P9, F22, FR-029/FR-030 |
| 4 | Audit event record | [`audit-event.schema.json`](./audit-event.schema.json) | Compliance replay, harness Pass 5 | FR-042..FR-045, constitution §4 |
| 5 | Case record | [`case-record.schema.json`](./case-record.schema.json) | Extraction, validation, grading | FR-002..FR-009 |
| 6 | Evaluation scorecard | [`eval-scorecard.schema.json`](./eval-scorecard.schema.json) | Harness run record, demo | harness §9/§10, `feature.md` §7 |

## Contract test obligations

Each contract carries at least one **failing-first** test before its implementation exists:

| Contract | Test obligation |
|---|---|
| 1 | Every P1–P11 value is present and equals `feature.md` §5.4. Routing rules parse under the restricted grammar. The YAML register mirror matches `docs/critical-condition-register.md` entry-for-entry. `bundle.lock.json` hashes verify. |
| 2 | Exactly one outcome for every input combination; all absent designations reported together; governance outranks completeness for a missing clinical recipient. |
| 3 | Every command that produces an outbound effect refuses to execute without an approval reference; the agent principal never satisfies a role check. |
| 4 | Every emitted event validates; no unmasked identifier pattern appears in any event or trace; the hash chain verifies; replay reproduces state. |
| 5 | `not_applicable` is never reported as missing; `backfilled` always carries `source_detail`. |
| 6 | Every percentage carries its denominator `n`; every percentile names its estimator; the document maps onto harness §10 field-for-field. |
