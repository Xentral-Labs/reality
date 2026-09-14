# Feature Specification: Sandbox read parity

**Feature Branch**: `155-sandbox-read-parity`
**Created**: 2026-09-09
**Status**: Reviewed
**Language**: English
**Input**: Sandbox companies should have the same business reads as real companies; find and remove remaining read restrictions.

## Context and Intent
### Problem
Warehouse reads reject a ready demo company with an instruction to use practice actions. The same obsolete restriction affects master data and source evidence, preventing normal investigation.
### Scope
All ordinary business register, detail, proposal inspection and original-file reads for an authorized Sandbox company must be available. Audit remaining purpose restrictions and distinguish business reads from privileged configuration and writes.
### Non-Goals
No changes to mutation confirmation, credentials, external integrations, admission, ownership, temporary lesson availability or company lifecycle. No schema or business calculation changes.
### Existing Contracts
- docs/WEB_SPEC.md
- docs/features/company-setup-demo.md
- specs/146-company-setup-demo/spec.md

## User Scenarios & Testing
### User Story 1 — Investigate Sandbox records (Priority: P1)
An authorized owner can use Warehouse, Master data and Integrations in a ready Sandbox as in a real company.
**Why this priority**: These reads currently fail despite visible navigation.
**Independent Test**: Open populated and empty registers and inspect their underlying records.
**Acceptance Scenarios**:
1. Given a ready Sandbox with stock, movements, reservations and master data, opening each register and a master-data detail succeeds with canonical values and filters.
2. Given source records and an original import file, source metadata and original-file download remain tenant-scoped and readable.
3. Given a master-data proposal, inspecting it succeeds without approving or executing it.
### User Story 2 — Preserve access boundaries (Priority: P1)
Reading a Sandbox grants no access to another company or permission to execute a change.
**Independent Test**: Repeat reads as anonymous/foreign users and attempt an existing restricted mutation.
**Acceptance Scenarios**:
1. Foreign identifiers return not found; unauthenticated and non-owner users cannot read a private Sandbox.
2. Existing confirmation, practice mutation, archived/unready and temporary lesson boundaries remain effective.
### Edge Cases
Empty registers, unknown tenants, foreign record IDs, inactive master data, filtered pagination, missing artifacts and existing proposals.

## Requirements
### Functional Requirements
- **FR-001**: Sandbox business registers and details MUST have the same read semantics as ordinary companies, including Warehouse, master data and sources.
- **FR-002**: Existing proposal and original-file inspection MUST work without mutation authority.
- **FR-003**: Ownership, tenant isolation, readiness and authentication MUST remain enforced.
- **FR-004**: Reads MUST NOT create or execute business changes, authorize integrations or expose credentials; existing write rules remain unchanged.
- **FR-005**: Remaining purpose-based restrictions MUST be inventoried and classified, with regression coverage for corrected reads.
### Domain and Traceability Requirements
- **DR-001**: Existing Source → Evidence → Reality links and canonical observations remain unchanged.
- **DR-002**: No duplicated authority or schema changes.
- **DR-003**: Existing shared services and tenant-scoped queries remain the only business read path.
### Key Entities
Sandbox company, master-data record, source record, proposal and original artifact retain their existing identities and ownership.

## Success Criteria
- **SC-001**: All identified affected business reads succeed for an authorized ready Sandbox.
- **SC-002**: Every FR and DR has executable coverage or recorded unchanged-code review evidence; required checks pass.

## Assumptions and Dependencies
The user's approval applies to business read parity. A private temporary lesson, credential retrieval and an outbound action are different capabilities and retain their existing restrictions. This builds on spec146 and the merged performance work.
## Open Questions
None.
## Requirement Traceability
| Requirement | Scenario | Evidence |
|---|---|---|
| FR-001, DR-001, DR-003 | US1.1–2 | Sandbox service and authenticated HTTP matrix |
| FR-002 | US1.2–3 | Proposal and artifact regression |
| FR-003 | US2.1–2 | Foreign/anonymous/not-ready tests |
| FR-004, DR-002 | US2.2 | No-write observer, existing mutation tests and diff review |
| FR-005 | All | Audit and regression inventory |
