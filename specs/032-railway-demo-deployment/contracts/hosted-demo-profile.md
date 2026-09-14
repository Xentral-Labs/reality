# Hosted Demo Deployment Contract

## Public boundary

| Service | Public | Port | Health path |
|---|---:|---:|---|
| Public Site (`site`) | yes, one generated HTTPS domain | 80 | `/` |
| Product App (`app`, repository path `apps/web`) | yes, one generated HTTPS domain | 80 | `/healthz` |
| Web/API (`api`) | no | 8000 | `/healthz` through Product Web |
| MCP runtime (`mcp`) | yes, authenticated origin root | 8001 | `/readyz` |
| PostgreSQL | no | provider managed | provider managed |

## Product Web runtime

| Variable | Required value |
|---|---|
| `API_UPSTREAM` | `api.railway.internal:8000` |

The browser uses same-origin relative `/api` routes. Product Web proxies `/api/` and `/healthz` privately to Web/API. The proxy re-resolves the private hostname while running so an API-only redeploy does not require a Product Web restart.

## Web/API runtime

| Variable | Contract |
|---|---|
| `REALITY_DATABASE_URL` | Private managed PostgreSQL connection reference using the supported SQLAlchemy/psycopg scheme |
| `SITE_URL` | Exact public Site HTTPS origin |
| `APP_URL` | Exact Product Web HTTPS origin |
| `API_URL` | Same Product Web HTTPS origin for the same-origin demo profile |
| `MCP_URL` | Exact public MCP HTTPS origin root with no extra path |
| `REALITY_AUTH_MODE` | `enabled` |
| `REALITY_COOKIE_SECURE` | `true` |
| `REALITY_AUTH_EXPOSE_CODES` | `false` |
| `REALITY_PUBLIC_SIGNUP_ENABLED` | `false` when no transactional email provider is configured |
| `REALITY_AUTO_APPROVE_LIMIT` | `0` |
| `REALITY_ARTIFACT_STORAGE` | `file` with uploads excluded from the demo |
| `REALITY_BOOTSTRAP_TENANT_NAME` | Synthetic demo tenant name |
| `REALITY_PLATFORM_ADMIN_EMAIL` | Secret provider variable |
| `REALITY_PLATFORM_ADMIN_PASSWORD` | Strong secret provider variable |
| `REALITY_MASTER_KEY` | Stable secret provider variable for the demo lifetime |

Pre-deploy command: `alembic upgrade head`.

## Security invariants

- No secret value is committed, printed in shared output, or stored as a build argument.
- No public domain or TCP proxy is assigned to API or PostgreSQL.
- Authentication remains enabled and verification codes are not exposed.
- Public signup is disabled while transactional email is absent; prepared-account login remains available.
- Only anonymised/synthetic data is used.
- The evaluator does not receive platform-admin credentials.

## Cleanup order

1. Remove the Site, Product App, and MCP public domains and verify all are unreachable.
2. Disable/revoke demo accounts and sessions if any environment is retained.
3. Delete application services and managed PostgreSQL only after explicit confirmation.
4. Confirm that no billable demo resource remains.
5. Revoke the Railway project token and remove it from the ignored local environment file.
