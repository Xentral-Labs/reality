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

## External Finance mapping boundary

Finance target maintenance uses the existing owner-confirmed application tools,
expected finance revision and atomic audit/result transaction. Mapping preview reads
the existing received component/source-classification/internal-assignment chain in
a separate REPEATABLE READ snapshot. It resolves exact destinations without mutating
evidence, classifications or operational ledger entries. UI, CLI, MCP and API consume
the same services. Target profiles, immutable export packages and external outcome
receipts remain the subsequent handoff boundary; a resolved mapping proves none of
those outcomes. See spec 148 target-mappings.md.
