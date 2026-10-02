# Feature Specification: Integrate account defaults

**Created**: 2026-10-02
**Status**: Approved scope. The owner accepted the concrete account-default consolidation proposal and instructed implementation.
**Language**: English
**Input**: Continue table consolidation by integrating `finance_role_destination` into the existing account model while preserving IDs, bookings and interfaces.

## Context and Intent

### Problem

A selected default repeats the account's existing tenant and role in a separate table.
An account has one role, and a company selects at most one default account for that role.
The selection can be owned by the account without adding a generic settings registry.

### Scope

Remove one physical default-selection table. Preserve exact existing selection identities,
accounts, financial provenance, service behavior and readable legacy SQL. Switch defaults
through the existing confirmed services and finance concurrency boundary. Provide a
transactional, lossless migration and rollback.

### Non-Goals

No new preference registry, AI/key changes, finance locking redesign, account-role
changes, new account deletion operation, financial recalculation, source rewriting,
new command or UI, live migration, deployment or merge. Do not alter spec 331 cost
semantics or unrelated demo behaviors.

## User Scenarios & Testing

### US1 - Select defaults without changing finance history (Priority: P1)

An owner selects a same-role active account. New operations resolve that default,
while invoices and payments tied to existing accounts retain their original provenance.

**Independent Test**: Change a default after recording an invoice, make a payment,
and compare account selections, exact postings, account revisions and event receipts.

**Acceptance Scenarios**:

1. Given a selected account, changing its default to another active same-role account
   preserves the selection identity and changes only the current choice.
2. Given prior invoice postings, changing the default does not rewrite them or move
   a subsequent settlement away from the invoice's held control account.
3. Given a blocked or wrong-role account, or another tenant's account, selection is
   refused with existing errors and no partial mutation.
4. Given no default, resolution reports the existing missing-default error; repeated
   initialization creates no duplicate accounts/defaults.
5. Given competing or stale confirmed changes, existing finance revision/lock rules
   preserve one default per role and reject stale previews without mixed state.

### US2 - Migrate safely and keep inspections readable (Priority: P1)

A maintainer retires old storage without losing historical IDs, mappings or inspection.

**Independent Test**: Upgrade and downgrade populated multi-tenant finance records,
compare every original mapping and retained record, and inspect the final table count.

**Acceptance Scenarios**:

1. Given old defaults, upgrade preserves every tenant, opaque destination ID, role and
   selected account ID, with one fewer physical table and readable legacy selections.
2. Given equal IDs in different tenants or a selected account subsequently blocked,
   migration preserves both valid states without repairing or dropping them.
3. Given a legacy role mismatch that cannot fit the account-owned model, upgrade
   aborts before retirement and leaves the original schema/data unchanged.
4. Given migrated selections, rollback recreates exact original selection rows and
   prior constraints/indexes without changing finance history.
5. Given a write through the legacy SQL name, it is explicitly refused without any
   account identity/state mutation. Shared services remain the supported write path.

### Edge Cases

- No selections, one selection and all supported role defaults.
- Selecting the same default again preserves current revision/event behavior.
- Two tenants may use the same selection or account IDs; local duplicates are rejected.
- Blocked selected accounts remain selected and resolution retains the existing refusal.
- A selection ID moves with a role's choice; it is never replaced on a switch.
- Rollback after post-migration selections retains those selections and their IDs.
- Migration racing with selection/account changes must neither lose nor mix writes.
- Reads remain read-only; no initialization, events or default creation as a side effect.

## Requirements

### Functional Requirements

- **FR-001**: Default choices MUST reside on existing accounts, retiring the physical `finance_role_destination` table without any replacement table.
- **FR-002**: Each tenant/role MUST have at most one default; original destination IDs MUST be unique within their tenant and preserved across selection changes.
- **FR-003**: Listing, initialization, resolution, default changes and transaction diagnostics MUST retain current service result shapes, errors and permissions.
- **FR-004**: Finance locks, expected revisions, confirmed actions and event audit MUST retain existing atomicity and retry/stale semantics.
- **FR-005**: Default changes MUST leave existing accounts' revisions and retained Sources, Evidence, LedgerEntries and held financial account references unchanged except existing finance change-event/revision effects.
- **FR-006**: Migration/rollback MUST preserve exact mappings and all retained finance authorities; incompatible legacy role mappings MUST abort without repair, loss or partial retirement.
- **FR-007**: The legacy SQL relation MUST preserve readable columns and identities; writes through it MUST be refused and MUST NOT modify account primary keys.
- **FR-008**: Every selection, read, write and migration relationship MUST preserve tenant isolation; reads MUST cause no mutations.

### Key Entities

- Account: existing tenant-owned account identity, role, state and revision; may hold the role's current selection identity.
- Default selection: retained opaque ID identifying one tenant/role choice and its selected account.
- Finance state: existing lock/revision boundary; unchanged.
- Existing postings: retained financial records referencing their original accounts; unchanged.

## Success Criteria

- **SC-001**: Storage inspection finds exactly one fewer physical business table, with no new replacement table.
- **SC-002**: Every original selection identity/mapping round-trips through populated migration and rollback, and every retained financial record remains equal.
- **SC-003**: All existing default-selection business scenarios retain their values, permissions, refusal messages and history behavior.
- **SC-004**: Competing selections cannot create two defaults for one tenant/role; stale changes cannot overwrite newer choices.

## Assumptions and Dependencies

The owner's latest continuation authorizes the concrete scope described in
[the audit](../../docs/ideas/settings-storage-consolidation.md), including the narrow
account extension and lossless rollback. No additional product behavior is introduced.
The old database FK does not enforce role agreement; the migration must check it.
Accounts have exactly one supported role, and current selection requires an active
same-role account. Blocking a previously selected account does not clear that selection.
The legacy interface is a read-only reporting/inspection contract, not a supported
alternate mutation service. Preserve current FinanceState, account/service contracts,
[Constitution](../../.specify/memory/constitution.md), [data model](../../docs/DATA_MODEL.md)
and [test strategy](../../docs/TEST_STRATEGY.md). Migration follows spec 328 revision 0115;
its existing backend acceptance limitations do not authorize unrelated fixes or release.

## Requirement Traceability

| Requirement | Acceptance stories | Planned proof |
| --- | --- | --- |
| FR-001 | US2.1 | Physical inventory and populated migration |
| FR-002 | US1.1/5, US2.2 | Identity transfer, uniqueness and concurrency |
| FR-003 | US1.1–4 | Existing finance service/refusal/initialization suites |
| FR-004 | US1.5 | Stale revision and competing selection |
| FR-005 | US1.2 | Invoice/settlement provenance and unchanged account revisions |
| FR-006 | US2.1–4 | Exact mapping/authority/schema roundtrip and safe abort |
| FR-007 | US2.5 | Legacy SELECT parity and INSERT/UPDATE/DELETE refusal |
| FR-008 | US1.3, US2.2 | Tenant isolation and mutation-free reads |
