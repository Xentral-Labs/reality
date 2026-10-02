# Implementation Plan: Consolidate Finance Reference Storage

**Branch**: Existing shared workspace | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Language**: English.

## Summary
Replace two physical catalogs with a typed Finance reference store and two automatically writable filtered logical views. Reuse existing disjoint kind sets to distinguish identities without new dependent fields or business rules.

## Technical Context
Python 3.12+, SQLAlchemy 2, Alembic, PostgreSQL; pytest integration/service/migration tests. No dependencies or frontend implementation added. Scope: exactly two catalogs and eight incoming typed FK constraints.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Source, evidence and retained decisions remain exact | PASS |
| Reality owns operational state | No document or operational state changes | PASS |
| Proven schema only | Existing repeatedly joined and constrained typed catalog fields only; target association retained | PASS |
| Tenant + shared services | Tenant-qualified keys and unchanged canonical services | PASS |
| Spec/test traceability | Ten requirements mapped below; tests first | PASS |
| Explainable web behavior | No UI change; existing tracing and logical resources retained | PASS |
| Received values not recomputed | Exact copies and immutable snapshots; no recalculation | PASS |
| Smallest coherent design | Kind already identifies family; writable views avoid triggers and service rewrites | PASS |

Post-design gate must confirm these rows remain PASS; no exception requested. Owner approved bounded consolidation, not broader schema expansion.

## Repository Structure and Layer Changes
- `packages/reality-core/src/reality/db/finance_reference_store.py`: shared physical table, view registration, FK redirection.
- `packages/reality-core/src/reality/db/core.py`: import registration after all catalogs/dependents and before index construction.
- `packages/reality-core/migrations/versions/0119_finance_references.py`: frozen transactional upgrade/downgrade.
- `packages/reality-core/tests/test_finance_reference_store.py`: metadata, namespace, constraints, view writes and deletion proof.
- `packages/reality-core/tests/test_finance_reference_migration.py`: exact populated upgrade/rollback and all FK semantics.
- Existing finance service/migration/index tests remain unchanged unless pinned fixture setup needs an explicitly test-only adjustment.
- Docs/data model generator describe physical store and retained logical catalogs.

Domain → service → tool → adapter: existing domain and canonical service/tool contracts are retained. Only storage changes underneath them. No alternative writes in transports.

## Design

### Reality flow
Existing assignment and mapping decisions retain their original IDs, typed relationship columns and reviewed snapshots. No evidence/source/ledger authority changes.

### Service and adapter flow
Existing FinanceReference and AccountingTargetReference ORM classes continue selecting and writing the original logical names. Simple views with LOCAL CHECK OPTION enforce catalog family; PostgreSQL propagates writes to physical storage. Existing permissions, confirmations, locks, immutable code/kind/target, stale checks and audit remain in shared services.

### Data and migration impact
See [data-model.md](data-model.md). Physical identity tenant/id/kind plus partial tenant/id uniqueness per family preserves original namespaces. Original incoming FK shapes reference physical store. Shared index generation still covers incoming keys. Views depend on physical store for metadata ordering; existing generic view compiler handles DDL and skips logical indexes. Company count/delete skips views already; physical store appears exactly once.

Migration freezes old catalog DDL, indexes and incoming constraint names. Acquire ACCESS EXCLUSIVE locks; copy all columns, preserve external times and null internal times; bidirectional parity before retirement. No CASCADE shortcuts. Downgrade creates legacy storage, copies and verifies values, restores original FK constraints/backing keys, removes shared storage. Earlier pinned schemas continue using original logical names.

### Failure, security, and tenant behavior
Invalid kind, tenant, target, labels, widths and duplicate identity fail transactionally. Existing cross-tenant service not-found behavior unchanged. Family-changing view writes fail check option. Source stated values and snapshots remain byte-for-byte unchanged.

## Test Strategy and Traceability

| Requirement | Planned proof |
|---|---|
| FR-001 | Existing finance reference/target-mapping lifecycle, permissions, paging tests |
| FR-002 | New store and migration collision tests across families/tenants |
| FR-003 | Store checks, code widths, uniqueness, kind and target rejection |
| FR-004 | Enumerate all eight incoming FKs, verify target-qualified semantics; existing components/source/target tests |
| FR-005 | Existing stale/locking/race/audit tests unchanged |
| FR-006 | Populated migration authority snapshots and existing retained assignment/mapping stories |
| FR-007 | Exact column/view shapes and timestamp parity |
| FR-008 | Initial failing physical two-to-one test; ORM view CRUD/RETURNING |
| FR-009 | Populated exact schema upgrade/downgrade/re-upgrade including post-upgrade writes |
| FR-010 | Partial/full metadata lifecycle, migration/index tests and company deletion suites |

## Rollout and Rollback
No live rollout. Migration 0111 follows 0110. Disposable PostgreSQL proves both directions; frozen DDL permits exact rollback. Required gates: lint, spec-check, focused tests, complete backend suite, docs generation/build/catalog check, web build/i18n for unchanged interface regression. Complete backend suite may run on an isolated source snapshot/dedicated PostgreSQL to avoid unrelated concurrent changes; record exact source and actual failures.

## Review Risks
- View INSERT/UPDATE RETURNING and ORM rowcount.
- Equal IDs across kind families; partial uniqueness must enforce original family identity.
- All incoming keys must target a physical unique constraint, never a view.
- Frozen index and FK names on rollback; partial metadata dependency ordering.
- Concurrent workspace edits must be preserved.

## Complexity Tracking
None. No Constitution exception.
