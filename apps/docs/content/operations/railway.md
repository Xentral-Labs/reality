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

## Separate product and marketing sources

`make railway-deploy` uploads only the product services from this checkout: API, scheduler, worker,
MCP, Docs, then App. It does not deploy the marketing site. Uploads use the script's repository root
even when the command runs from another directory.

The provider website lives in a separate private checkout. Deploy it explicitly:

```bash
export REALITY_RAILWAY_SITE_ROOT=/absolute/path/to/marketing-checkout
./scripts/deploy_railway_demo.sh --only site --dry-run
./scripts/deploy_railway_demo.sh --only site
```

Use `--only all` for a coordinated deployment from both checkouts. All selected Dockerfiles are
checked before the first upload. `--dry-run` shows service, checkout, commit and Dockerfile without
authenticating or deploying. The checkout contents are uploaded, including uncommitted files not
excluded by Git ignore rules; use reviewed clean checkouts for releases.

Set `REALITY_RAILWAY_PROJECT_ID` and optionally `REALITY_RAILWAY_ENVIRONMENT` (default
`production`). Product health checks require `APP_URL`, `DOCS_URL` and `MCP_URL`; site health checks
require `SITE_URL`. Authenticate with the Railway CLI or supply `RAILWAY_TOKEN` directly or through
the ignored file selected by `REALITY_RAILWAY_ENV_FILE`. The environment file is read for the token
only; export non-secret deployment settings explicitly.

In Railway, set `RAILWAY_DOCKERFILE_PATH` for each service to its repository-relative Dockerfile:
`apps/api/Dockerfile`, `apps/scheduler/Dockerfile`, `apps/worker/Dockerfile`, `apps/mcp/Dockerfile`,
`apps/docs/Dockerfile`, `apps/web/Dockerfile`, or `apps/site/Dockerfile.railway`. Build from the
checkout root. Changing the local Git remote does not configure Railway. This workflow retains CLI
uploads and does not enable GitHub autodeploys.
