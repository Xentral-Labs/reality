# Railway

A short-lived, independently hosted demonstration of Site, App and MCP on Railway with managed
PostgreSQL. It is a demo profile, not the production architecture: uploaded source binaries are
ephemeral in this profile, so it uses bundled synthetic data only.

## Resources

One Railway project with these services, all built from the repository root:

| Service    | Dockerfile             | Network                                |
| ---------- | ---------------------- | -------------------------------------- |
| `Postgres` | Railway managed        | private only                           |
| `api`      | `apps/api/Dockerfile`  | private only, port 8000                |
| `app`      | `apps/web/Dockerfile`  | public domain, port 80                 |
| `mcp`      | `apps/mcp/Dockerfile`  | public authenticated origin, port 8001 |
| `docs`     | `apps/docs/Dockerfile` | public domain, port 80 (optional)      |

The Web App reaches the API through Railway private DNS: set
`API_UPSTREAM=api.railway.internal:8000` on the `app` service.

## Deploy

The repository script deploys the services in order and waits for their health:

```bash
make railway-deploy
```

It reads the public URLs from `SITE_URL`, `APP_URL`, `DOCS_URL` and `MCP_URL` and expects the
Railway CLI to be logged in. Runtime secrets (`REALITY_DATABASE_URL`, `REALITY_MASTER_KEY`, the
platform admin credentials) belong in Railway variables, never in Git or build arguments.

The Railway-specific Site image requires the exact Railway `SITE_URL`, `APP_URL` and `DOCS_URL` and
rejects missing URL build inputs. It serves final Railway-specific legal pages for this
non-canonical, non-indexable demo. The approved `runreality.ai` candidate and its digest-bound
secret remain exclusive to the AWS release Dockerfile.

## Safety boundary

Use synthetic or anonymised data only, keep authentication enabled with a strong demo administrator
password, keep public signup disabled while no email provider is configured, and do not connect live
shop, email, AI, payment or accounting credentials.
