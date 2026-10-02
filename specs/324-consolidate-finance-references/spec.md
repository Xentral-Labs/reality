# Feature Specification: Consolidate Finance Reference Storage

**Feature Branch**: Existing shared workspace; no branch switch.
**Created**: 2026-10-02
**Language**: English
**Status**: Accepted; implementation and verification complete
**Input**: Owner approved consolidating the two Finance reference catalogs after the mapping storage assessment ("ok mach").

## Context and Intent

### Problem
Internal classifications and target-owned accounting references repeat catalog storage. The owner wants fewer physical tables while preserving the existing Finance domain.

### Scope
Consolidate exactly the two reference catalogs into one physical typed store. Retain separate logical resources and every existing business contract.

### Non-Goals
Generic Settings, Facts as configuration, consolidation of mapping revisions, components or targets, new UI, live migration, deployment, commits and changes to unrelated concurrent work.

## User Scenarios & Testing

### User Story 1 - Maintain familiar catalogs (Priority: P1)
Finance owners continue creating, renaming, blocking and finding internal classifications and external accounting references through existing confirmed services.

**Independent Test**: Run catalog lifecycle, permissions, stale confirmation and competing-change scenarios.

**Acceptance Scenarios**:
1. **Given** two catalogs, **When** a confirmed change is performed, **Then** IDs, labels, revisions, audit and errors retain their existing meaning.
2. **Given** identical external codes in different targets, **When** searching or resolving, **Then** each target retains its own reference.
3. **Given** stale approval or another tenant, **When** changing a reference, **Then** the existing refusal remains effective.

### User Story 2 - Keep exact retained links (Priority: P1)
Assignments and mappings continue identifying the exact catalog entry selected at confirmation.

**Independent Test**: Exercise all reference relationships, invalid kinds and targets, and historical snapshots.

**Acceptance Scenarios**:
1. **Given** equal opaque IDs across catalog families or tenants, **When** resolving retained links, **Then** identity remains unambiguous without changing IDs.
2. **Given** a wrong kind, target or tenant, **When** recording a link, **Then** storage rejects it.
3. **Given** reviewed historical snapshots, **When** catalog names change, **Then** those snapshots remain unchanged.

### User Story 3 - Reduce storage reversibly (Priority: P2)
Maintainers can upgrade populated storage and reverse the change without losing catalog data or dependent authorities.

**Independent Test**: Populate both families and dependent records, upgrade, modify catalogs, downgrade and re-upgrade.

**Acceptance Scenarios**:
1. **Given** populated catalogs, **When** upgrading, **Then** every original column value and link is preserved and the physical catalog count decreases from two to one.
2. **Given** changes after upgrading, **When** downgrading, **Then** both original catalog structures and their exact current values are restored.

### Edge Cases
- Equal IDs in both families; equal IDs in separate tenants.
- External duplicate codes across targets; local code length 100 and external length 200.
- Local references have no timestamps; external timestamps remain exact.
- Blocked entries, incomplete inserts, invalid families and identity-changing writes.
- Earlier pinned migrations and metadata create/drop without a live-schema migration.

## Requirements

### Functional Requirements
- **FR-001**: Maintain distinct internal and target-owned logical catalogs, commands, outputs, permissions, error contracts, paging and confirmed service entrypoints.
- **FR-002**: Preserve opaque IDs and original per-family tenant identity namespaces, including collisions across families and tenants.
- **FR-003**: Preserve allowed kinds, code/name limits, state and positive revisions, code uniqueness and exact target ownership.
- **FR-004**: Preserve all existing typed incoming relationships and reject wrong tenant, kind or target without new routing fields on dependent business records.
- **FR-005**: Preserve finance locking, stale-preview refusal, immutable code/kind/target, revision increments and existing before/after audits.
- **FR-006**: Preserve all assignments, mapping history, reviewed snapshots, source payloads, received amounts and ledger authorities without recalculation.
- **FR-007**: Preserve external timestamps exactly and introduce no internal catalog timestamps or additional public fields.
- **FR-008**: Reduce two physical catalog tables to one while retaining both original logical names and safe existing catalog writes.
- **FR-009**: Provide transactional populated upgrade, downgrade and re-upgrade with exact values and relationship enforcement, including changes performed after upgrade.
- **FR-010**: Preserve supported metadata lifecycle, earlier pinned migration tests, company deletion and physical-record counting.

### Key Entities
- Internal Finance reference: tenant-owned cost center, case code or coding group.
- Target reference: account or tax code owned by an identified accounting destination.
- Retained mapping/assignment: unchanged decision pointing to the exact typed reference.

## Success Criteria

### Measurable Outcomes
- **SC-001**: Catalog physical storage decreases from two tables to one.
- **SC-002**: 100% of original catalog values and dependent identities survive populated upgrade and rollback.
- **SC-003**: All existing catalog lifecycle, isolation, invalid-link, concurrency and history scenarios pass without changing business assertions.
- **SC-004**: No new public field, command or preference storage is introduced.

## Assumptions and Dependencies
- Scope approval is the owner's explicit "ok mach" following the concrete two-to-one proposal; no additional product decision is needed.
- Existing Finance contracts in spec 148 and the mapping storage assessment remain authoritative.
- Specs 316/319 provide the shared compatibility-view mechanism and prior migrations 0109/0110.
- PostgreSQL is the only supported database. Verification uses disposable databases; no live migration is authorized.

## Requirements Review
All stories map to FR-001 through FR-010. Identity, target isolation, write compatibility and exact rollback are mandatory rather than optional optimizations. No unresolved clarification remains. Review completed before technical planning.

## Requirement Traceability

| Requirement | Story | Tests | Tasks |
|---|---|---|---|
| FR-001 | US1 | Store/migration and existing Finance regression families per plan | T004,T005,T006,T013 |
| FR-002 | US2 | Store/migration and existing Finance regression families per plan | T007,T008,T010,T013 |
| FR-003 | US1 | Store/migration and existing Finance regression families per plan | T004,T005,T010,T013 |
| FR-004 | US2 | Store/migration and existing Finance regression families per plan | T007,T008,T010,T013 |
| FR-005 | US1 | Store/migration and existing Finance regression families per plan | T004,T005,T006,T013 |
| FR-006 | US2 | Store/migration and existing Finance regression families per plan | T007,T008,T009,T010,T013 |
| FR-007 | US1 | Store/migration and existing Finance regression families per plan | T004,T005,T010,T013 |
| FR-008 | US1 | Store/migration and existing Finance regression families per plan | T004,T005,T013 |
| FR-009 | US3 | Store/migration and existing Finance regression families per plan | T010,T011,T012,T013 |
| FR-010 | US3 | Store/migration and existing Finance regression families per plan | T007,T008,T010,T011,T012,T013 |
