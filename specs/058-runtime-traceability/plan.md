# Implementation Plan: Packaged Runtime Traceability

## Technical Context

Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, pytest. Existing
`SourceRecord.supersedes_source_record_id`, public `SourceRead`, agent discovery catalog, and
platform deployment posture are changed without a migration.

## Constitution Check

| Principle | Result | Evidence |
| --- | --- | --- |
| Source → Evidence → Reality | PASS | Exposes the existing direct immutable-source link only. |
| Reality operational authority | PASS | No operational state moves to SourceRecord. |
| Proven schema only | PASS | No schema change. |
| Tenant/service boundaries | PASS | Existing tenant-scoped services and public adapters remain in use. |
| Evidence before completion | PASS | Regression tests precede implementation and full gates follow. |
| Explainable product | PASS | Operators and agents gain missing traceability. |
| Simplicity/storage discipline | PASS | Small path-resolution and serialization changes only. |

## Design

Package Alembic revision files as distribution data and resolve the first existing migration path
from the source checkout and installed distribution layouts. Keep `None` for missing/ambiguous
heads. Add the already-stored predecessor ID to `SourceRead` and the SourceRecord discovery field
allowlist. Extend existing tests; add no repository or transport-specific business logic.

## Test Strategy

1. A planted installed-layout path returns the same head as the repository layout.
2. API serialization returns null for v1 and the v1 ID for v2.
3. MCP discovery returns the same values and preserves tenant isolation/no payload.
4. A failed Shopify interpretation produces `source_interpretation_failure`; successful retry removes it.
5. Run lint, spec policy, full backend, migrations and packaging checks.

## Migration and Rollback

No database migration. Rollback removes the additional response field and restores prior package
data/path resolution; stored source history remains unchanged.

## Risks

- Packaging paths can drift: test both wheel contents and runtime resolution.
- Public response addition is backward compatible but snapshots/contracts require updates.
