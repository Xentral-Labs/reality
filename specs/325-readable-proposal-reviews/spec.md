# Feature Specification: Readable Proposal Reviews

**Language**: English
**Created**: 2026-10-02
**Status**: Scope approved by owner; reviewed
**Input**: Replace ciphertext and default JSON in proposal decisions with understandable business information, preserving privacy and optional technical inspection.

## Context and Intent

### Problem
Private report review currently displays a sealed payload instead of the proposed change.
Shipment review defaults to JSON. Neither presentation gives the reader a clear basis for deciding.

### Scope
Common proposal review, private graph report/request changes, and the shipment review fallback.
Reuse existing review services and structured field presentation. Keep technical details collapsed.

### Non-Goals
No new approval rights, autonomous delegation, persistence, schema, shipment creation form redesign,
or wholesale redesign of other specialized review dialogs.

## User Scenarios & Testing

### User Story 1 — Review a private change (Priority: P1)
The original author reads the proposed report operation, report name and held question.
Other company readers see a private-content notice and may use their existing rejection path.

**Independent Test**: Prepare a sealed change as a member; review as its author, another owner,
without a principal and from a foreign tenant.

**Acceptance Scenarios**:
1. Given a private change, when its original active author reviews, then the held operation and report information are readable and ciphertext is absent.
2. Given another reader, when reviewing, then no decrypted question/name or ciphertext is returned, approval is unavailable in this review and existing rejection remains available.
3. Given a missing sealing key or retired payload, when reviewing, then a bounded unavailable notice appears without granting approval.

### User Story 2 — Review an operational change (Priority: P2)
A user sees structured shipment inputs/effect or recorded outcome and can expand technical details.

**Independent Test**: Open shipment and common proposal dialogs, inspect default visible content,
expand technical details and verify confirmation still uses the exact review token.

**Acceptance Scenarios**:
1. Given shipment review, when opened, then held fields and nested movements are rendered as labeled values rather than a JSON block.
2. Given technical inspection, when expanded, then relevant sanitized technical values are available.
3. Given an older payload, when opened, then sealed values remain hidden and a private-content fallback is shown.

### Edge Cases
Removed membership; foreign tenant; nonauthor company owner; no principal; unreadable sealing key;
missing/deleted report; create without a report ID; executed/rejected/reconciliation outcomes;
empty structured values; nested arrays and records; rolling deployment without new review fields.

## Requirements

### Functional Requirements
- **FR-001**: Sealed private payloads MUST never be presented as proposal decision information or returned in common review input, including technical inspection.
- **FR-002**: Only the original active author MUST receive readable held private operation/report/question details through existing author checks.
- **FR-003**: Other readers and unreadable private changes MUST receive a bounded privacy/unavailable notice; review MUST suppress approval while preserving existing rejection behavior.
- **FR-004**: Shipment fallback review MUST display structured inputs/effects/receipts by default.
- **FR-005**: Sanitized technical JSON MUST be available only in an initially collapsed inspection control; confirmation credentials and sealed contents MUST be omitted.
- **FR-006**: Existing exact confirmation, current-membership, tenant, stale-state, reconciliation and replay rules MUST remain unchanged.
- **FR-007**: Web MUST tolerate legacy payloads without rendering a sealed payload and MUST provide translations in all four existing languages.

### Data Requirements
- **DR-001**: Read-time presentation MUST NOT create new business authority or persistent fields; original sealed payloads remain unchanged in storage.

### Key Entities
Existing ChangeProposal, private report and requested-analysis definitions; derived private review information.

## Success Criteria
- **SC-001**: Author/nonauthor/anonymous/foreign-tenant tests prove privacy and held-value fidelity.
- **SC-002**: Browser proofs show no ciphertext or expanded JSON by default in scoped dialogs and verify unchanged decisions.
- **SC-003**: Required backend, Web, i18n, lint and spec checks pass; failures are recorded honestly.

## Assumptions and Dependencies
The owner's acceptance of the described display/privacy change approves this scope.
Existing sealed author validation and shared presentation components remain authoritative.
Technical details are inspection only and never a new execution input. Repository work unrelated
to this feature must be preserved.

## Requirement Traceability

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-001–FR-003, FR-006, DR-001 | Story 1; privacy edge cases | Private review, Web identity forwarding, existing decision and graph lifecycle tests |
| FR-004–FR-005 | Story 2 | Shared presentation contract and proposal review browser proof |
| FR-007 | Story 2.3 | Legacy carrier browser fixtures and four-language i18n audit |
