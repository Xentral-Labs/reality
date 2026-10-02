# Implementation Plan: Consolidate cost projections

**Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Language**: English

## Summary

Replace thirteen physical output tables with four typed shared cost-projection tables
(net nine fewer). Preserve the thirteen logical interfaces as PostgreSQL updatable
views over discriminator-filtered shared storage. Existing ORM classes, raw SQL,
opaque IDs and inspection/reporting contracts therefore retain their exact grain.
The views own no data or business rules; constraints and lifecycle triggers execute
on shared physical storage. The original input and Reality tables remain unchanged.

## Technical Context

Python 3.12+, SQLAlchemy 2, Alembic and PostgreSQL only. Decimal numerics and UTC times
retain existing types. No dependencies, public commands or frontend changes.
The schema contains retained authorities and disposable outputs; only outputs change.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | No authority or input history rewritten | PASS |
| Reality owns state | Outputs remain observations, no document status | PASS |
| Proven schema | Existing fields and constraints regrouped for existing four families | PASS |
| Tenant/services | Tenant+family identity and typed composite FKs; existing services unchanged | PASS |
| Specification/tests | Approved spec; populated migration and existing regression suites | PASS |
| Explainable web | Logical inspector/report identities and exact input links preserved | PASS |
| Received values | Migration copies values exactly, performs no recalculation | PASS |
| Smallest coherent design | Four physical tables; narrow cost namespace; reuse alternative researched | PASS |

## Repository Structure and Layer Changes

- `src/reality/db/cost_projections.py`: shared physical schema and view installation.
- `src/reality/db/core.py`: register shared storage before FK indexing.
- `src/reality/db/cost_projection_guards.sql`: shared lifecycle guards.
- `migrations/versions/0117_cost_projections.py`: static schema snapshot, transactional copy,
  bidirectional parity check, table retirement and view creation; reversible downgrade.
- `migrations/env.py`: exclude logical views from autogenerate comparisons.
- `tests/test_cost_projection_migration.py`: populated upgrade/downgrade and constraints.
- `tests/test_cost_projections.py`: physical inventory, view writes and family isolation.
- Existing schema-comparison/reporting coverage tests: distinguish logical views from storage.
- `docs/features/receipt-costing.md`, `docs/DATA_MODEL.md`: describe authority/storage boundary.

## Design

### Data and service flow

Existing services write their exact logical view. PostgreSQL routes the write to its
single shared table and applies family-scoped shape, uniqueness, foreign-key and lifecycle
checks. Readers and raw SQL join the same filtered views, so they cannot mix families.
Views expose legacy columns plus internal discriminator/link constants needed for write
routing. ORM mappers retain only their existing business fields. No parallel rule system
or direct writes from adapters is introduced.

### Storage proof

Four tables: generation, inventory result, contribution result and publication.
Identity is `(tenant_id, projection_family, id)` to preserve equal opaque IDs in formerly
separate tables. Columns are the union of existing typed columns, nullable outside the
owning family. Each family check requires its old nonnullable fields and forbids unrelated
columns. Foreign keys to a shared output include a family column constrained to the exact
legacy target. All retained-authority FKs preserve their existing tenant pairs.

Partial unique indexes preserve family-specific uniqueness, including inventory null
assessment identity. Nonpartial scoped unique keys support composite publication FKs.
Existing per-family lifecycle checks are dispatched on shared storage; retained company
manifest/input guards remain installed separately. Captured/company membership and
sealed-state checks must remain exactly as strong as existing behavior.

### Migration and rollback

Use a frozen DDL snapshot, not live ORM metadata, for Alembic. Lock all logical output interfaces against concurrent writes before copying. Copy all legacy values
and opaque IDs into shared storage while old storage remains present. Verify every
original column with bidirectional EXCEPT comparisons before dropping anything.
Drop output tables in reverse FK order, then create filtered writable views and their
constant defaults. Install shared guards only after copy. One transaction rolls back any
parity or constraint failure. Downgrade restores frozen legacy tables and copies original
values back before shared storage is removed; all original guards are restored.
No startup migration and no live business database migration in this task.

## Test Strategy and Traceability

| Requirements | Evidence |
|---|---|
| FR-001, FR-008 | Physical table/view inventory and net reduction tests |
| FR-002, FR-005, DR-001/002/004/005 | Existing inventory/contribution/captured/company, analytics, inspector and read-only suites |
| FR-003/004/007 | Existing retry/concurrency/publication/disposal tests plus migrated storage guards |
| FR-006 | Populated four-family migration, exact-value bidirectional parity, collision fixture and downgrade |
| DR-003 | Tenant and wrong-family FK/shape rejection tests |

New meaningful tests run red before schema changes. Then run focused tests, full backend
suite, lint, spec-check, docs generation/catalog check and required frontend/build gates.
Existing migration tests pinned to old revisions remain unchanged; head-schema tests
must compare physical storage separately from compatibility views.

## Review Risks

Views are an explicit compatibility boundary, not additional business entities. Autogenerate,
metadata creation, foreign-key indexing and tenant deletion must distinguish them from
physical storage. View defaults must supply family identifiers on inserts; scoped identity
must prevent changing them on updates. Trigger checks must execute even for direct shared
storage writes. Published cache protection and captured disposal nesting must remain valid.

## Complexity Tracking

No Constitution exception. Four shared tables replace thirteen, retaining their proven
fields and relational checks. Compatibility views avoid changing saved identifiers and
all typed SQL consumers at once. A generic JSON registry and unscoped polymorphic IDs
were rejected because they discard constraint and reporting proof.
