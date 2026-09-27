# Data Model: Shared Runtime Catalog

## Persistence impact

No business or infrastructure data model changes. There is no schema, migration, table, stored
cache entry or backfill.

## Runtime concepts

### Fresh Application Catalog Build

The fully validated composition of source-controlled application-reference files for the current
deployment. It is created on explicit demand and is not itself cached.

### Runtime Catalog Snapshot

One successfully validated and enriched application catalog held within an application process.

- **Lifetime**: from first successful initialization until process exit or explicit test/development
  reset.
- **Contents**: deployment metadata only; never tenant IDs, business records, authorization
  results, service responses or mutation outcomes.
- **Publication rule**: visible only after the complete build succeeds.
- **Failure rule**: initialization exceptions leave no snapshot and a later call retries.
- **Concurrency rule**: concurrent first callers observe one complete snapshot or an explicit
  failure, never partial state.
- **Isolation rule**: callers receive copied data and cannot mutate the held snapshot.

### Runtime Catalog Section

An isolated copy of one top-level section from the Runtime Catalog Snapshot, used by a narrow
service/tool consumer.

- **Identity**: canonical top-level section name.
- **Validation**: only sections present in the validated snapshot can be returned.
- **Relationship**: derived from exactly one Runtime Catalog Snapshot in the current process.
- **Mutation**: caller changes affect only the returned copy.

## State transition

```text
empty ──initialize──> validating/enriching ──success──> ready
  ▲                         │                           │
  └──────── failure ────────┘                           └──explicit clear──> empty
```

Failure is not a stored terminal state. A subsequent caller may retry.
