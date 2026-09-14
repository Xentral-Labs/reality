# Contract: Repository Application Layout

## Stable current-state tree

```text
apps/api/Dockerfile
apps/mcp/Dockerfile
apps/web/Dockerfile
packages/reality-core/pyproject.toml
packages/reality-core/src/reality/
packages/reality-core/migrations/
packages/reality-core/config/
packages/reality-core/fixtures/
packages/reality-core/tests/
packages/reality-core/alembic.ini
```

## Ownership rules

- `apps/api` owns only the API image/runtime boundary.
- `apps/mcp` owns only the MCP image/runtime boundary.
- `apps/web` owns browser/static presentation and nginx configuration.
- `packages/reality-core` owns all shared Python behavior and operational resources.
- No application directory may contain a copied `reality` business module.
- Active tooling and documentation use only current paths.

## Build contracts

- API and MCP build from repository root context using their own Dockerfiles.
- Both install exactly `packages/reality-core` from the same checkout.
- Web builds from `apps/web` inputs and remains independently cacheable.
- Migration execution uses the same shared-core image content and Alembic chain.

## Runtime contracts

- API command: authenticated Web/API ASGI process on port 8000.
- MCP command: authenticated HTTP-only MCP ASGI process on port 8001.
- Web: static assets on port 80 inside its image.
- Existing public URLs, health endpoints, dependencies, and pool budgets remain
  unchanged.
