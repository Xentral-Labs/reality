# Contract: Shared Runtime Application Catalog

## Ownership

`reality.catalogs` exclusively owns fresh construction, validation, runtime snapshot publication,
bounded section access and explicit clearing. Services and tools consume this boundary. API, MCP,
Web, CLI and other adapters do not add catalog caches.

## Operations

### Build fresh catalog

- Produces a newly composed and validated catalog from deployment files.
- May be called by validation, generation and tests.
- Does not read or populate runtime cached state unless invoked by runtime initialization.
- Propagates validation failures.

### Read full runtime catalog

- Initializes the process snapshot once when absent.
- Returns an isolated copy of the complete validated/enriched snapshot.
- Never returns a partially initialized value.
- Does not retain failed initialization as a result.

### Read runtime catalog section

- Uses the same process snapshot as the full read.
- Returns an isolated copy of exactly one requested top-level section.
- Rejects an unknown section explicitly.
- Does not copy unrelated sections.

### Clear runtime catalog

- Removes the successful process snapshot for explicit development/test use.
- The next full or section read performs a new initialization.
- Is not a production hot-reload protocol.

## Consumer rule

Production services/tools that need unchanged deployed catalog metadata use the full or section
runtime operation. Direct fresh-build calls are allowed only where fresh construction is the
purpose, such as validation, generation and tests. A source-level inventory enforces this split.

## Business-state exclusion

The runtime snapshot never contains tenant-scoped rows, proposal state, decision attribution,
authorization results, service responses or mutation outcomes. Those remain fresh application
service concerns.
