# Data Model: Deployable Application Layout

## Business data impact

None. This feature introduces no business entity, typed field, relationship, table,
index, constraint, or migration.

## Repository ownership concepts

These are filesystem/deployment concepts only and are not persisted as business data.

### Deployable Application

- Stable name: `web`, `api`, or `mcp`.
- Owns: image/build definition, runtime entry point, exposed port, and health contract.
- Depends on: shared core where applicable.
- Must not own: duplicated domain rules, repositories, or business persistence.

### Shared Reality Core

- Stable path: `packages/reality-core`.
- Owns: Python package, domain, services, repositories, tools, adapters, catalogs,
  migrations, fixtures, CLI, and tests.
- Remains one compatibility and release boundary for API, MCP, CLI, and workers.

### Repository Release

- One commit/version containing compatible application definitions and shared core.
- Old and new filesystem layouts are not mixed within one supported release.

## Invariants

- Source → Evidence → Reality remains unchanged.
- PostgreSQL remains the only business database.
- All business tables and queries remain tenant-scoped.
- API and MCP consume the same `reality` package build.
- Application/directory names are not domain identity.
