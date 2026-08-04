# Constitution — Healthcare Internal Process Optimization

## 1. Purpose
This document defines non-negotiable constraints for the system.
All specifications, plans, code, tests, and agent executions must comply with this Constitution.

## 2. Change Control (Immutable by Default)
- This file is immutable by default.
- Any change requires explicit approval from both:
  - Team Lead
  - Compliance Reviewer
- Approval must be recorded in the pull request with:
  - approver names
  - approval date
  - justification for change
  - risk impact statement
- If a requested implementation conflicts with this Constitution, work must pause and be escalated.

## 3. PHI and Data Handling
- Use synthetic or de-identified data only in this project.
- Real patient-identifiable data must never be ingested, stored, logged, or exported.
- Data access must follow minimum necessary access.
- Any dataset used for demos or evaluations must include provenance notes.
- Logs and traces must mask identifiers.

## 4. HIPAA and Privacy Guardrails
- Designs must preserve confidentiality, integrity, and availability of data.
- Access must be role-aware and restricted to approved users.
- Audit trails must support who/what/when/why reconstruction.
- Data sharing across teams must be purpose-limited.
- Privacy violations are release blockers.

## 5. Ethical and Clinical Safety Boundaries
- The system is an administrative assistant, not a clinical decision-maker.
- Prohibited autonomous actions:
  - diagnosis
  - treatment recommendation
  - medical-necessity determination
  - clinical clearance authorization
  - discharge or release authorization
- Allowed autonomous actions:
  - data collation
  - administrative routing
  - draft generation
  - escalation packet preparation
- Any critical clinical condition must be escalated to authorized clinical humans.

## 6. Security Baseline
- Secrets must not be hardcoded or stored in source-controlled files.
- Access controls and least privilege are required for all integrations.
- All security-relevant actions must be auditable.
- Sensitive logs must be redacted.
- Security exceptions require explicit risk sign-off in PR.

## 7. Code and Delivery Standards
- Changes must be traceable to feature requirements.
- Tests or validation evidence must accompany implemented behavior.
- Backward-incompatible changes require explicit justification.
- Major workflow changes require spec updates before code updates.
- All implementation changes must be recorded in docs/progress-log.md.

## 8. Enforcement
- Constitution violations are stop-ship issues.
- If ambiguity exists, default to safer behavior and escalate.
- Automation agents must not override Constitution constraints.
