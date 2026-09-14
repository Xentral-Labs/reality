# Unified source definition management
**Language**: English
**Created**: 2026-09-08
**Status**: Accepted for implementation within the ongoing unified-app migration
**Input**: Owner requested continued implementation after Spec 129; source configuration is a retained B1 capability.

## Context and Intent
### Problem
Source definitions still require an old-screen link. Their existing labels can imply a live connection or intake control that the system does not provide.
### Scope
Register a source and review/change existing source and declared-type flags inside Data & sources. Keep source records and item CSV entry directly accessible.
### Non-Goals
Live vendor transport, credentials, connector template installation, new declared-type creation, mapping edits, renaming/deleting sources, new import profiles, backend behavior changes and complete legacy retirement.

## User Scenarios & Testing
### US1 — Register an origin (P1)
An authorized business member enters a code, name and optional description, reviews the normalized definition and confirms. Cancel creates nothing. The registered source appears in the same new app.
### US2 — Inspect and maintain definitions (P1)
From a source card, open its identity and declared data types. Review the exact source or type and desired registry state before changing a flag. View its received records without entering the old application.
### US3 — Handle uncertain results (P1)
After a lost response, confirmation stays disabled until an explicit read of current configuration. A present matching definition is shown as current state, never proof that this request created it. Reload preserves the need to check; changing company discards visible drafts and cannot replay a write.
### Edge Cases
Duplicate codes, empty required values, missing/foreign source ID, failed initial read, failed status check, multiple clicks, cancel/reload, company switch during a request and empty declared-type lists.

## Requirements
- **FR-001**: Expose source registration and contextual source configuration in Data & sources. Existing item import and evidence navigation remain available. A bookmarked existing source configuration reopens by opaque ID.
- **FR-002**: Show normalized code, name and description before registration. Required values are enforced; duplicate/error responses retain the form. Review/cancel is inert and confirmation is single-flight.
- **FR-003**: Show the selected source and its existing declared types, target declarations and interpreter availability. Flag changes review the exact record and desired state. Explain that flags are registry metadata, not connection, synchronization or intake controls.
- **FR-004**: Unknown writes require explicit current-state checking without automatic mutation retry. Persist an unresolved marker across reload. A failed check retains the block. Recovery reports current state, without claiming historical action attribution. Company switches isolate drafts, reads and requests.
- **FR-005**: Use existing tenant-authorized services, allow existing ordinary-member access and retain practice restrictions. Never add browser business rules or expose storage/secrets. Configuration does not create source payloads or operational records.
- **FR-006**: Four-language labels, keyboard focus, responsive light/dark layouts, accessible actions, bounded declared-type pagination and current error/empty states. Retain the source register's pagination and search.

## Assumptions and Dependencies
Existing source registration is tenant-unique by normalized code; IDs identify records. Existing flags do not enforce intake admission. Existing writes have no request receipt or optimistic state token. A successful current-state read is sufficient to permit a fresh user-directed review; it is not a recovered mutation receipt. Normal navigation moves selected capabilities only; connector template configuration remains outside this slice. The owner's continued migration instruction authorizes this existing-capability UI move without adding domain policy.

## Success Criteria
A member can register a source, inspect its declarations, change reviewed flags and open received records entirely in the unified app. No cancel/reload/unknown-response path causes an automatic write. All six requirements have passing browser or existing backend evidence; required checks remain green.

## Requirement Traceability
| Requirement | Tasks | Proof |
|---|---|---|
| FR-001/002 | T002/T003 | Registration/cancel/duplicate and source entry browser cases |
| FR-003 | T004 | Source/type flag review, metadata copy and pagination browser cases |
| FR-004 | T005 | Lost response, persisted marker, failed check and company switch cases |
| FR-005 | T002/T004/T005 | Existing backend access/service tests and browser company isolation |
| FR-006 | T004/T006/T007 | Four-language responsive layouts, pagination, build and i18n gates |
