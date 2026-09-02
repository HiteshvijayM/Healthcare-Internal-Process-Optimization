# Contract 1 — Policy Bundle Configuration

**Governs**: FR-008, FR-010, FR-014, FR-017, FR-018, FR-022, FR-045, FR-052, FR-055, FR-057 · F7, F23 · P1–P11
**Read by**: non-technical reviewers (this is the contract that makes "inspectable" true), the routing engine, the SLA engine, the escalation resolver.

The bundle is a directory of commented YAML, loaded immutably at run start and frozen for a harness run (harness §4 entry criterion).

```text
config/policy/v1/
├── policy-table.yaml               # P1..P11
├── routing-rules.yaml              # F7 — ordered, declarative
├── approver-registry.yaml          # harness §4.1 roles + §4.2 designations
├── field-owner-map.yaml            # FR-008 completion-task ownership
├── sla-table.yaml                  # P4/P5 per urgency class × service line
├── critical-signal-register.yaml   # mirror of CCR-DEMO-v1 (authoritative source is the markdown)
└── bundle.lock.json                # bundle id + SHA-256 of every file above
```

---

## 1. `policy-table.yaml`

Every number the harness scores against, in one place, worded so §5.4 and this file can be diffed by eye.

```yaml
policy_table_version: "P-2026-08-06-CHG-021"
source: "feature.md §5.4"

P1_provisional_routing:
  min_confidence: 0.80
  required_fields: [patient_reference, requested_service]
  forbidden_while: [critical_signal_active, clearance_gate_pending, register_unresolved]
  safety_bearing: true

P2_duplicate_detection:
  key_match:
    window_hours: 72                      # a tunable parameter, never a constant
    key: [sender, patient_reference, requested_service]
    scope: in_progress_cases
    channel_sensitive: false
  identity_match:
    window_hours: null                    # unbounded — must never be suppressed by key_match window
    scope: all_cases                      # including closed cases
    matches_on: [source_document_id, normalized_content_hash]
    normalization_strips:                 # transport-added material ONLY
      - cover_sheets
      - routing_headers
      - arrival_timestamps
      - channel_watermarks
      - retransmission_banners
  on_match: flag_and_hold_for_adjudication  # never auto-discard, never auto-merge

P3_escalation_packet_completeness:
  required_fraction: 1.0
  mandatory_fields:
    [case_id, patient_reference, requester, critical_signal_description,
     source_document_reference, timestamp, designated_clinical_recipient]
  partial_sends_permitted: false
  safety_bearing: true

P4_approval_slas:
  defaults:
    routine: {value: 2, unit: business_days}
    urgent: {value: 4, unit: hours}
    critical_acknowledgement: {value: 30, unit: minutes}
  resolution: [urgency_class, service_line]     # see sla-table.yaml
  override_rule: shorter_only                   # a longer override needs Compliance Reviewer approval
  critical_clock_starts_at: detection           # FR-056 — NOT at dispatch
  requires_on_call_coverage: true               # absent coverage ⇒ governance blocker, clock does not start
  record_applied_value: true                    # FR-022 — breach audited against the value in force

P5_sla_alerts: {early_warning_at_pct: 80, breach_at_pct: 100, auto_advance_on_breach: false}

P6_rework_loop_limit: {max_loops: 2, on_exceed: escalate_to_human_owner}

P7_drift_tolerance: {aggregate_pp: 2, per_case_classification_identical: true}

P8_audit_retention: {minimum_days: 90, scope: project_lifetime, purge_before_signoff: false}

P9_surface_scope: {surfaces: [web_chat], tenants: 1, reviewer_sessions: 1}

P10_dispatch_approval_deadline:
  value: 10
  unit: minutes
  must_be_strictly_shorter_than: applied_critical_acknowledgement_sla   # FR-052
  on_breach: [record_breach, keep_undispatched, escalate_to_named_alternate]
  safety_bearing: true

P11_critical_signal_register:
  register_id: "CCR-DEMO-v1"
  authoritative_source: "docs/critical-condition-register.md"
  inference_permitted: false
  on_unresolvable: [governance_blocker, hold_case, refuse_provisional_routing]
  negative_claim_permitted: false        # only "no registered signal matched" may be stated
  safety_bearing: true
```

**Contract rules**

- `PC-1` — Every value must equal `feature.md` §5.4. A contract test asserts this; drift fails the build.
- `PC-2` — Loosening any entry marked `safety_bearing: true` (P1, P3, P10, P11) requires Compliance Reviewer approval, not Team Lead alone.
- `PC-3` — No consumer may hardcode any of these values. All reads go through the loaded bundle.

---

## 2. `routing-rules.yaml`

```yaml
rules_version: "ROUTE-v1"
queues: [Insurance, Operations, Diagnostics, Legal, Finance]   # fixed set, §13.5

rules:
  - id: R-010
    description: "Records disclosure, subpoena, or compliance/audit retrieval requests go to Legal."
    when: "requested_service contains_any ['records disclosure','subpoena','audit retrieval','compliance retrieval']"
    queue: Legal
    reason_template: "Routed to Legal: the request is for {requested_service}, which is a records-disclosure matter (rule R-010)."
    confidence: 0.95

  - id: R-020
    description: "Billing, statements, payment plans, or already-settled coverage go to Finance."
    when: "requested_service contains_any ['billing','statement','payment plan'] or coverage_status equals 'settled'"
    queue: Finance
    reason_template: "Routed to Finance: {reason_detail} (rule R-020)."
    confidence: 0.90

  # ... Insurance, Diagnostics, Operations rules ...

  - id: R-999
    description: "Anything not matched above is general intake and goes to Operations."
    when: "always"
    queue: Operations
    reason_template: "Routed to Operations: no more specific rule matched, so this is handled as general intake (rule R-999)."
    confidence: 0.50          # below P1's 0.80 — a default match can never justify provisional routing
```

**Contract rules**

- `RC-1` — Ordered; **first match wins**. Order is meaningful and is part of the contract.
- `RC-2` — A terminal `when: "always"` rule is **mandatory**, so no case can fall off the end.
- `RC-3` — Every rule carries a plain-English `description`. The trace shows the description, so a non-technical reviewer never reads the `when` expression to understand the outcome (FR-017, US2 scenario 2).
- `RC-4` — The trace records **every** rule evaluated with its boolean result, not only the one that fired (FR-018).
- `RC-5` — `when` uses a restricted grammar only: field references, string/number literals, and the operators `equals`, `contains`, `contains_any`, `in`, `is_present`, `is_missing`, `and`, `or`, `not`, `always`. **No arbitrary code evaluation.**
- `RC-6` — The default rule's confidence must be below P1's threshold, so a fallback never provisionally routes.

**Reviewability check (the real acceptance test for this file)**: a non-technical reviewer, given only this file and a routing trace, can name the rule that produced any decision without assistance.

---

## 3. `approver-registry.yaml`

```yaml
registry_version: "ROLES-v1"
source: "docs/multipass-validation-harness.md §4.1 and §4.2"

roles:
  - {id: intake_coordinator,       authority: administrative, approves: [data_completeness, missing_data_tasking, provisional_routing_acceptance]}
  - {id: insurance_approver,       authority: role_scoped,    approves: [insurance_stage]}
  - {id: operations_approver,      authority: role_scoped,    approves: [operations_stage]}
  - {id: diagnostics_approver,     authority: role_scoped,    approves: [diagnostics_stage]}
  - {id: legal_approver,           authority: role_scoped,    approves: [legal_stage]}
  - {id: finance_approver,         authority: role_scoped,    approves: [finance_stage]}
  - {id: clinical_authority,       authority: clinical,       approves: [clinical_clearance, escalation_receipt], human_only: true}
  - {id: finance_clearance_approver, authority: financial,    approves: [financial_clearance]}
  - {id: team_lead,                authority: governance,     approves: [waivers, constitution_amendments, scope_changes]}
  - {id: compliance_reviewer,      authority: governance,     approves: [waivers, constitution_amendments, audit_signoff, safety_threshold_loosening]}
  - {id: team_validation_lead,     authority: validation,     approves: [harness_run_record]}

designations:                                    # §4.2 — assignments, not new authorities
  designated_clinical_recipient: {held_by: clinical_authority, alternate: clinical_authority}
  escalation_dispatch_approver:  {held_by: intake_coordinator, alternate: team_lead}
  dispatch_approval_deadline:    {held_by: policy_value, ref: P10_dispatch_approval_deadline}
  on_call_clinical_coverage:     {held_by: clinical_authority_roster}

constraints:
  agent_may_hold_role: false                     # FR-038, §4.1
  agent_may_hold_designation: false              # §4.2
  separation_of_duty:
    - {not_both: [clinical_authority, finance_clearance_approver], scope: same_case}
    - {not_both: [escalation_dispatch_approver, designated_clinical_recipient], scope: same_packet}
  governance_approval_requires_both: [team_lead, compliance_reviewer]
```

**Contract rules**

- `AC-1` — `agent` is not a valid value for any role or designation field. The type system must make it unrepresentable, not merely rejected (FR-038).
- `AC-2` — Acting holders are named **per run** in the run record, never in this file (roles are authorities, not persons).
- `AC-3` — Separation-of-duty constraints are enforced at the point of recording, not at review time (FR-034).

---

## 4. `field-owner-map.yaml`

```yaml
map_version: "OWNERS-v1"
default_owner: intake_coordinator        # FR-008 — where no mapping exists
mappings:
  insurance:   insurance_approver
  operations:  operations_approver
  diagnostics: diagnostics_approver
  legal:       legal_approver
  finance:     finance_approver
field_families:
  payer_plan:          insurance
  coverage_reference:  insurance
  appointment_slot:    operations
  ordering_reference:  diagnostics
  disclosure_scope:    legal
  billing_reference:   finance
```

`FC-1` — Exactly **one** accountable owner per task. Unmapped fields resolve to `intake_coordinator`, never to "unassigned".

---

## 5. `sla-table.yaml`

```yaml
sla_version: "SLA-v1"
defaults:
  routine:                  {seconds: null, business_days: 2}
  urgent:                   {seconds: 14400}
  critical_acknowledgement: {seconds: 1800}
business_calendar: {work_days: [mon,tue,wed,thu,fri], work_hours: "09:00-17:00", timezone: "UTC"}
service_line_overrides: []      # each entry must be SHORTER than the default (P4 shorter_only)
```

**Contract rules**

- `SC-1` — Resolution is by `(urgency_class, service_line)`; where no override exists the default applies.
- `SC-2` — An override longer than the default is **rejected at load** unless it carries a recorded Compliance Reviewer approval (P4).
- `SC-3` — The resolved value is written onto the item as `applied_sla_seconds` with `sla_resolved_from`, so breaches are audited against the value in force (FR-022).
- `SC-4` — If a `critical_acknowledgement` override would make P10's 10 minutes **not strictly shorter**, the escalation resolver raises a governance blocker (FR-052) rather than adjusting either value.

---

## 6. `critical-signal-register.yaml` — mirror only

```yaml
register_id: "CCR-DEMO-v1"
authoritative_source: "docs/critical-condition-register.md"
source_sha256: "<hash recorded in bundle.lock.json>"
match_mode: literal_marker            # no fuzzy, no semantic, no model call
entries:
  - id: CCS-001
    signal: "Radiologist critical result flag"
    markers: ["critical result flag", "critical finding flagged", "critical result notification"]
    clinical_owner: clinical_authority
  - id: CCS-002
    signal: "Explicit clinician escalation request"
    markers:
      - "brought to the attention of the responsible clinical team without delay"
      - "bring to the attention of the responsible clinical team without delay"
      - "requires immediate clinical attention"
      - "escalate to clinical authority"
    clinical_owner: clinical_authority
  - id: CCS-003
    signal: "Laboratory critical-value notification"
    markers: ["critical value", "panic value", "critical value notification"]
    clinical_owner: clinical_authority
    # No fixture in SYN-CASESET-v1. Registered but unexercised — see
    # docs/critical-condition-register.md §3 "Known coverage gap".
    fixture_coverage: none
    never_evaluate_numeric_value: true
excluded_explicitly:                  # recorded so the boundary is visible, register §2
  - "Urgency: Urgent / STAT"
  - "the word 'urgent' in a subject line"
  - "any diagnosis, symptom, finding, medication or test name"
  - "any numeric result compared against a range"
  - "a patient's or requester's own assertion that a matter is critical"
```

**Contract rules**

- `CRC-1` — This file is a **mirror**. `docs/critical-condition-register.md` is authoritative; a contract test asserts entry-for-entry equality and fails the build on drift.
- `CRC-2` — Matching is literal, case-insensitive, whitespace-normalised. No inference, generalisation, paraphrase, or extension (register §1 prohibition 1).
- `CRC-3` — A non-match is reported **only** as `"no registered signal matched"` — never as "no critical condition present" (prohibition 2). A violation is **Sev 0**.
- `CRC-4` — Absent / empty / unresolvable register ⇒ governance blocker, case held, provisional routing refused. A missing register is never treated as an empty one (prohibition 3).
- `CRC-5` — Multiple matches on one case produce **one** packet naming every matched ID (register §3).
- `CRC-6` — Amending this content requires Clinical Authority **and** Compliance Reviewer, and mints a new register ID.

---

## 7. `bundle.lock.json`

```json
{
  "bundle_id": "POLICY-v1",
  "frozen_at": "<iso-8601>",
  "dataset_id": "SYN-CASESET-v1",
  "register_version": "CCR-DEMO-v1",
  "files": {
    "policy-table.yaml": "sha256:...",
    "routing-rules.yaml": "sha256:...",
    "approver-registry.yaml": "sha256:...",
    "field-owner-map.yaml": "sha256:...",
    "sla-table.yaml": "sha256:...",
    "critical-signal-register.yaml": "sha256:...",
    "docs/critical-condition-register.md": "sha256:..."
  }
}
```

**Contract rules**

- `BC-1` — Verified at load; a hash mismatch is a **startup failure**, never a warning.
- `BC-2` — `bundle_id` is recorded on **every** routing and approval decision (FR-045).
- `BC-3` — Any content change mints a new `bundle_id` and requires re-running every harness pass whose evidence depended on the previous one.
