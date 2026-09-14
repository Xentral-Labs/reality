# Analytics data model

Status: architecture/schema accepted on 2026-09-13. Migration 0060 implemented and verified in isolation; final feature verification is complete.

## New persistence: analytics_report

Saved definitions are configuration. No results, Facts, stock, totals or business status are persisted by analytics.

| Field | Meaning / constraint |
|---|---|
| id | Opaque `anr_` identity; primary key |
| tenant_id | Required tenant FK, always included in queries and uniqueness |
| owner_user_id | Required AppUser FK; supplied by trusted Principal, not request JSON |
| name | Trimmed nonempty text, 1–120 characters; names are not identity |
| definition | Versioned JSON object validated against current catalog, at most 16 KiB |
| presentation | Versioned table/chart/pivot options; part of the definition size limit |
| revision | Positive integer, starting at 1; increments on update/rename/delete |
| create_request_id | Required client retry UUID, unique within tenant/owner |
| create_payload_hash | Hash of canonical initial name/definition/presentation; same key/different payload conflicts |
| last_request_id | Last accepted mutation retry UUID, scoped to this report |
| last_payload_hash | Canonical operation/payload/expected-revision hash for retry comparison |
| created_at / updated_at | UTC instants |
| deleted_at | Nullable UTC tombstone; excluded from ordinary list/get |

Indexes/constraints: unique `(tenant_id, owner_user_id, create_request_id)`; unique `(tenant_id, id)` for future same-tenant references; stable-continuation list index `(tenant_id, owner_user_id, id)`; name/revision checks as appropriate. Each get/update/delete requires tenant, owner and active membership. Platform role does not implicitly bypass private ownership. No FK to Evidence/Source is needed: the definition describes a question, not a new provenance relationship.

Lifecycle: active → revised; active → tombstoned. Duplicate creates a new identity and retry key; no relationship to the original is required. No restore or purge interface is introduced. Stored definitions are never executed without validation against the current schema and current authorization. Unknown old field IDs produce repairable errors.

Atomicity: create uniqueness serializes retry. Update/delete use conditional revision checks and return conflict on stale state. Replaying the last mutation requires the same payload hash. An older request cannot overwrite newer state. A replayed create returns the same identity/current state and never overrides subsequent edits or resurrects deletion. Agent receipts continue to use existing ChangeProposal history, bound to the original Principal and target revision.

## No business-schema expansion for descriptive analysis

Use existing typed fields and shortest links:

- Party ← Document → DocumentLine → Item for order evidence.
- DocumentLine ← Commitment ← Reservation/Movement for effective operational quantity.
- Agreed DocumentLine ← billed DocumentLine → invoice Document for billing evidence.
- Invoice LedgerEntry ← SettlementAllocation → payment LedgerEntry for allocations.
- SourceRecord links already on the authoritative records for origin and source coverage.

Extracting a shared SQL derivation is behavior-preserving and needs canonical parity tests. Any need to add order dates, payment-term snapshots, causal supply allocation or missing value-presence fields is outside this plan and must be brought back as a separately justified schema change.

## Transient domain objects

`AnalyticsDefinition` (schema version 1): dataset, dimensions, measures, predicate tree, time window, time grouping, compare, sort and presentation. No tenant/user selector, SQL fragment or arbitrary expression.

`AnalyticsExecutionContext`: trusted caller identity, authorized tenant, optional Principal, cancellation/deadline and transport capabilities. It is not serializable into model arguments.

`AnalyticsResult`: executed normalized definition, column descriptors, decimal-safe rows, population totals, comparison/pivot output, limits, coverage, observation, fingerprint and scoped contributor requests. It is not a persisted snapshot.

`AnalyticsDataset`: fixed grain, permissible predicates/measures/relations, authoritative row provider and contributor resolution. Catalog labels are business-facing and localized in the same four languages as the product.

## Migration

Add ORM model in `db/analytics.py`, import it through the established core metadata registration, and create the next free Alembic revision after rechecking heads. The final revision is `0060_analytics_reports`, following `0059_foreign_key_indexes` merged from main. Migration creates only the definition table/indexes. No source backfill, business data transformation or startup migration.

Rollback: older binaries ignore the additive table. Retain definitions when rolling back application code. Destructive downgrade is not part of deployment rollback; migration tests can exercise it only on isolated test databases. Any proven order query index is planned separately after EXPLAIN/benchmark evidence and requires its own reviewed migration if it changes existing tables.
