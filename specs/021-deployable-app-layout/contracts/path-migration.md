# Contract: Atomic Path Migration

| Retired path | Current path |
|---|---|
| `backend/` | `packages/reality-core/` |
| `backend/Dockerfile` | `apps/api/Dockerfile` and `apps/mcp/Dockerfile` |
| `frontend/` | `apps/web/` |

All current commands, CI globs, Compose build definitions, policy inputs, coverage
ownership rows, and documentation must use the current path. Historical specs and ADR
decision history may mention retired paths only when clearly describing history.

No compatibility symlink, duplicated directory, or mixed-layout release is supported.
Rollback is a full repository release rollback, not a partial directory fallback.
