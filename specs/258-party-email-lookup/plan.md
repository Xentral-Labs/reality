# Implementation plan

## Technical Context

Python 3.12, SQLAlchemy 2, PostgreSQL, Alembic, existing Party services/application tools/MCP discovery and pytest. No new dependency.

## Constitution Check

| Principle | Result | Reason |
| --- | --- | --- |
| Source → Evidence → Reality | PASS | Email is Party master data; external payload remains lossless and versioned. |
| Operational authority | PASS | No document or operational status field. |
| Proven schema | PASS | Exact sender matching repeatedly filters and joins on email. |
| Tenant/service boundaries | PASS | Composite tenant keys and existing services/tools only. |
| Spec/tests first | PASS | Issue, approved decisions, spec and failing tests precede implementation. |
| Explainable Web | PASS | Discovery exposes the typed basis; no browser rule. |
| Simplicity/storage | PASS | One narrow table; email only. |
| Received values | PASS | Display value is recorded; normalization is a lookup key, not a second business assertion. |

## Design

Add `PartyEmailAddress` with composite tenant/ID identity, tenant-scoped Party FK and unique
`(tenant_id, party_id, normalized_email)`. Extend Party create/update record schemas and snapshots.
Replace email collections atomically inside the existing Party transaction. Add an email `EXISTS`
predicate only for Party discovery and serialize ordered email objects. Update machine-readable data,
resource and tenant-isolation catalogs and regenerate Docs.

## Tests

Add service/MCP tests before implementation for normalization, duplicate rejection, replacement,
shared-address ambiguity and tenant isolation. Run migrations, focused tests, catalog generation,
spec policy, lint and full required suite.

## Migration / rollback

Migration 0092 adds only the new table and indexes; downgrade drops it. Existing Party rows need no
backfill. Rollback removes email lookup while leaving source payloads intact.

## Post-design Constitution Check

All rows remain PASS; there are no exceptions or unresolved clarifications.
