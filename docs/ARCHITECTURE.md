# Architecture

```text
External payloads / human / agent
             |
             v
         SOURCE
      SourceRecord
             |
             v
        EVIDENCE
 Document --- DocumentLine
             |
             v
         REALITY
 Fact / Commitment / Reservation / Movement / LedgerEntry
             |
             v
     Services / Queries
             |
        +----+----+
        |         |
       CLI       Tools -> Chat
```

Dependency direction: `domain <- services <- tools <- cli/agent`. Integrations translate source payloads into application commands; they are not a second domain model.

Historical physical errors never rewrite a Movement. One shared application operation
atomically appends an exact `correction` Movement, an optional replacement, the durable
ternary correction relation, affected Commitment reconciliation, and one
`movement.corrected` BusinessEvent. Preview is read-only and server-derived; Web, CLI,
Chat, MCP, and API do not calculate alternative inverse or fulfilment rules.

## Runtime boundaries

The static public Site is an independent presentation deployment with no application
or tenant access. The static Product Web, Web/API, remote MCP, and workers are
independently operated adapters around one shared application core. Web/API owns browser authentication,
tenant APIs, settings, token administration, and human confirmation. Remote MCP owns
only authenticated Streamable HTTP, its protocol lifecycle, and its liveness/readiness
probes. It runs on its own configured public URL and process (port 8001 in Compose),
while Web/API does not mount or proxy `/mcp/`.

Both runtimes import the same canonical tool bindings, tenant-scoped repositories, and
application services and use the same PostgreSQL authority. MCP has no separate
business database, business rules, tenant selector, or direct ORM write path. The
internal Copilot dispatches canonical tools in process; it is not an MCP transport
client. MCP has no alternate local transport mode.

An optional operation context may carry an external operational or correlation ID
through commands, events, projections, logs, and responses for end-to-end tracing.
It is observability metadata, not business truth, identity, tenant authority, or a
replacement for opaque domain IDs and the Source → Evidence → Reality chain.

```text
Public visitor -> static Site (no application dependency)
Product user -> static Product Web -> Web/API ------+
Enterprise agent -> HTTP MCP runtime ---------------+-> application tools/services
Workers --------------------------------------------+          |
                                                              +-> PostgreSQL
                                                              +-> private object storage
```

Repository releases preserve these boundaries atomically through `apps/api`,
`apps/mcp`, `apps/web`, and `packages/reality-core`. Deployments must not mix paths or
artifacts from different repository releases. Rollback restores the complete previous
release so all adapters continue to consume the matching shared core.

## Storage

PostgreSQL is the only supported database in local development, tests, and production.
Production uses one shared managed database for all tenants, including authoritative
Reality records and rebuildable projections. See
[ADR 0004](decisions/0004-production-storage-and-projections.md).

RAM is disposable cache only. Object storage is for backups, exports, and proven large
payloads or attachments. Additional infrastructure such as Redis, Kafka, per-tenant
databases, and table partitioning is deferred until measurements justify it.

## Provenance
Document → SourceRecord; DocumentLine → Document; Commitment → optional DocumentLine/Document; Reservation → Commitment; Movement → optional Commitment/SourceRecord; LedgerEntry → optional Document/SourceRecord; LedgerReversal → original/reversing posting-group identities; Fact → optional SourceRecord. Never connect by document number. A reversing LedgerEntry does not duplicate original Evidence links: the reversal relation is the shortest true path to the original group and its provenance.

## Derived state
Fulfillment = commitments vs linked fulfillment movements. Availability = physical stock - active reservations. Projected availability considers due incoming/outgoing commitments. Risk is computed, not a document status.

## Executable vocabulary

Commands, Business Events, Projections, and stable Fact predicates have separate
machine-readable authorities under `packages/reality-core/config/`. `reality.catalogs` composes and
validates them as one application reference. Catalogs document executable behavior;
they never become business state or an alternative write path.

Validation is two-way: literal emitted Event types match the Event catalog and runtime
Projection registrations match catalog materialization names. The Command catalog
explicitly defines public use cases instead of treating every mutating helper as a
Command. The Fact predicate catalog stays empty until repeated core behavior proves a
stable vocabulary.

Runtime services and tools read this deployment vocabulary through one validated,
process-local application-catalog snapshot. Narrow consumers receive isolated copies of only the
section they need; API, MCP, Web, CLI and other adapters do not own separate catalog caches.
Mutable tenant records, authorization, service responses and mutations never enter this snapshot.
The raw catalog builder remains explicit for validation, generation and tests, while a failed
runtime initialization is not retained and can be retried.

## External Finance mapping boundary

Finance target maintenance uses the existing owner-confirmed application tools,
expected finance revision and atomic audit/result transaction. Mapping preview reads
the existing received component/source-classification/internal-assignment chain in
a separate REPEATABLE READ snapshot. It resolves exact destinations without mutating
evidence, classifications or operational ledger entries. UI, CLI, MCP and API consume
the same services. Target profiles, immutable export packages and external outcome
receipts remain the subsequent handoff boundary; a resolved mapping proves none of
those outcomes. See spec 148 target-mappings.md.

## Account default storage boundary (spec 332)

Default-account writes use existing finance services and the existing delivery/finance
lock order. A retained selection ID on the account replaces separate selection storage;
clear/flush and transfer happen in one transaction, without incrementing account revision.
Readable legacy selections are provided by a read-only DISTINCT view; unsupported
legacy writes cannot become an alternate account-identity mutation path. Shared schema
view support only installs explicit DDL and excludes logical views from Alembic storage
comparison. It owns no business rules or runtime schema migration.

## Finance catalog storage boundary (spec 324)

Two Finance-specific logical catalogs share one physical typed reference store.
PostgreSQL automatically writable filtered views with LOCAL CHECK OPTION retain
existing ORM/service write contracts; kind identifies the family without an additional
routing field. Incoming relationships use physical tenant/kind and target-qualified
keys. Existing finance locks, confirmations, revisions and historical snapshots remain
in canonical services. Migration 0111 copies exact fields and restores frozen original
catalog/FK/index structures on rollback. Physical company deletion/counting visits the
store once and skips its logical views.

### Receipt manifest membership boundary

The five receipt-cost input-membership resources share one typed physical store
(spec 330). Existing costing services and record inspectors retain their original
models and exact logical columns. Insert-only routing supplies a hidden family;
updates/deletes remain native view operations. Physical shape checks, family-scoped
uniqueness and true tenant-qualified FKs preserve integrity. This storage boundary
does not merge admitted financial inputs with captured observations or decisions,
and does not change historical review selection or hashes.

## Census membership storage (spec 327)

Four retained census member families share `cost_company_census_member`. Original
exact-column SQL interfaces, observations, hashes and tenant-qualified opaque IDs
remain intact. Generated document and line identities preserve the incoming typed
FKs without adding consumer fields. Physical admission locks the building census;
member updates/deletes and sealed inserts remain refused. Migration 0119 preserves
populated rollback, original header protection and complete FK indexes.

See [verification](../specs/327-consolidate-census-members/verification.md) for
acceptance evidence.
