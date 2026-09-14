# ADR 0004: Production storage and projections

Status: accepted.

## Context

The expected production shape is roughly 5,000 tenants. A user tenant normally has
three to five concurrent writers; a large tenant can import about 20,000 orders per
day. Orders can arrive while users are inactive. Losing an acknowledged business
transaction is unacceptable. Tenant-local reads are sufficient, and projections may
lag by a few seconds.

The system should remain simple to deploy and should have almost no marginal compute
cost for an inactive tenant.

## Decision

Use one shared, managed PostgreSQL database for the production Fact Journal, Source,
Evidence, Reality, and projections. Keep every business row tenant-scoped and enforce
tenant scope in every repository query.

Use the existing domain tables as the journal of business reality. Journal-like
records such as SourceRecord, Fact, Movement, and LedgerEntry are append-only. Do not
introduce a second generic event store unless a proven business case requires it.

Store projections as ordinary tenant-scoped PostgreSQL tables. Update them from a
transactional outbox using a small worker when asynchronous processing is needed.
Commands that enforce business invariants must use authoritative Reality records in
their database transaction, never an eventually consistent projection.

Keep the initial deployable system to:

1. one application image for HTTP, CLI, and ingestion entry points;
2. one worker process using the same application services;
3. one managed PostgreSQL database with automated backups and point-in-time recovery.

The worker may initially run from the same image or service. PostgreSQL is the queue;
do not add Redis, Kafka, or a separate message broker for V0 production.

Use object storage only for backups, exports, and payloads or attachments that are
proven too large for the database. RAM is an optional disposable cache and is never a
system of record.

Keep PostgreSQL durability enabled. In particular, do not trade acknowledged data for
speed by disabling `fsync` or synchronous commit.

Local development, tests, demos, and production use PostgreSQL. Production uses one
shared database rather than one database per tenant.

## Why

- A shared database makes an inactive tenant almost free without creating 5,000 files,
  databases, backup schedules, or connection targets.
- PostgreSQL safely supports concurrent ingestion and transactional journal writes.
- The anticipated per-tenant order volume is modest for PostgreSQL; measured query
  patterns, not the headline tenant count, should drive later indexing or partitioning.
- Keeping journal, Reality, outbox, and projections in one database preserves atomic
  writes and minimizes operational components.
- Managed backups and point-in-time recovery address the durability requirement more
  directly than application-managed file replication.

## Consequences

- Tenant isolation is logical. It must be tested at every repository/service boundary;
  PostgreSQL Row-Level Security may later be added as defense in depth.
- Projection reads may be a few seconds stale. Their rows must record enough progress
  to detect lag and rebuild deterministically.
- Idempotency is mandatory for imports, outbox consumers, and projection updates.
- Connection pooling must be bounded because all tenants share the database.
- Composite indexes should begin with `tenant_id` and be added only for demonstrated
  filters, joins, ordering, or uniqueness constraints.
- Table partitioning, read replicas, Redis, Kafka, and per-tenant databases are deferred
  until measurements prove that the simpler design is insufficient.

## Delivery path

1. Require `REALITY_DATABASE_URL` and run the complete test suite on PostgreSQL.
2. Keep schema changes in Alembic rather than runtime mutation.
3. Add the transactional outbox only with the first asynchronous projection/import.
4. Add production backup/PITR, restore testing, connection limits, and health checks.
5. Measure real queries before adding composite indexes or partitioning.
