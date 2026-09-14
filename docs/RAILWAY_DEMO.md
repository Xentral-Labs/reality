# Railway Demo Deployment

**Purpose:** Short-lived, independently hosted Product App, Docs and MCP demonstration
**Spec impact:** `specs/032-railway-demo-deployment`

This profile is not the permanent production architecture described in
[`infra/README.md`](../infra/README.md). It deploys the Product App, Docs,
canonical Web/API runtime, remote MCP runtime, and managed PostgreSQL. `app`, `docs`
and `mcp` receive separate public domains. The `api` and PostgreSQL services remain
on private networking.

## Safety boundary

- Use synthetic or anonymised demonstration data only.
- Keep authentication enabled and use a dedicated strong demo administrator password.
- Do not share the platform-administrator credential with an evaluator.
- Keep public signup disabled while no transactional email provider is configured.
- Do not connect live Shopify, email, AI, payment, or accounting credentials.
- Do not upload evidence files in this minimal profile.
- Never add the Railway token or runtime secrets to Git or deployment build arguments.

`REALITY_ARTIFACT_STORAGE=file` is intentionally ephemeral in this profile. An API
redeploy can remove uploaded binaries while PostgreSQL retains their metadata. The
demo therefore uses bundled synthetic data and makes no durable-artifact claim.

## Provider resources

Create these resources in one Railway project and one environment:

| Railway service | Source                                          | Network                                    |
| --------------- | ----------------------------------------------- | ------------------------------------------ |
| `Postgres-oQQF` | Railway managed PostgreSQL                      | private only; no TCP proxy                 |
| `api`           | repository root, `apps/api/Dockerfile`          | private only; port 8000                    |
| `app`           | repository root, `apps/web/Dockerfile`          | public app domain; port 80                 |
| `docs`          | repository root, `apps/docs/Dockerfile`         | public documentation domain; port 80       |
| `mcp`           | repository root, `apps/mcp/Dockerfile`          | public authenticated MCP origin; port 8001 |

Railway private DNS for the API is `api.railway.internal`. Configure Product Web:

```text
API_UPSTREAM=api.railway.internal:8000
```

The image default remains `api:8000` for local Compose.
Product Web derives the container's active nameserver from `/etc/resolv.conf` and
resolves the private API hostname at request time with a short validity window. This
works with both local Docker DNS and Railway private DNS. An API-only redeploy therefore
does not require Product Web to restart when Railway assigns the API a new private
address.

## API variables

Set these as Railway runtime variables. Secret values must be sealed/provider-managed.

```text
REALITY_DATABASE_URL=<private Postgres connection reference using postgresql+psycopg>
SITE_URL=https://<provider-marketing-site>
APP_URL=https://<generated-app-domain>
API_URL=https://<generated-app-domain>
DOCS_URL=https://<generated-docs-domain>
MCP_URL=https://<generated-mcp-domain>/
REALITY_AUTH_MODE=enabled
REALITY_COOKIE_SECURE=true
REALITY_AUTH_EXPOSE_CODES=false
REALITY_PUBLIC_SIGNUP_ENABLED=false
REALITY_AUTO_APPROVE_LIMIT=0
REALITY_ARTIFACT_STORAGE=file
REALITY_BOOTSTRAP_TENANT_NAME=Reality Demo
REALITY_PLATFORM_ADMIN_EMAIL=<secret owner-controlled email>
REALITY_PLATFORM_ADMIN_PASSWORD=<secret strong generated password>
REALITY_MASTER_KEY=<secret stable Fernet key>
REALITY_DB_POOL_SIZE=5
REALITY_DB_MAX_OVERFLOW=2
REALITY_DB_POOL_TIMEOUT=5
```

Railway's Postgres reference commonly supplies a `postgresql://` URL. Reality uses
the Psycopg 3 dialect, so the effective `REALITY_DATABASE_URL` must begin with
`postgresql+psycopg://`. Keep the connection private and do not create a public
Postgres TCP proxy.

Normal public signup is intentionally unavailable in this profile because the log
email provider would expose verification codes to operator logs. Prepared-account
login remains available at `/login`. To provide an evaluator account later, configure
a real transactional email provider, enable signup temporarily, approve the account,
create its tenant membership, and disable signup again before the demo.

## Release gate and health

Configure this API pre-deploy command:

```text
alembic upgrade head
```

Configure the API health path as `/healthz`. A failed migration must block release.
Configure the Product Web health path as `/healthz`; this checks Nginx and the private
API connection. Database readiness is proven separately by the migration gate and an
authenticated database-backed request.

Do not create a separate long-running migration service. Do not run database
migrations while building the container image.

## Initial deployment

1. Deploy managed PostgreSQL and wait until its private connection is available.
2. Configure API variables, pre-deploy command, and health path, then deploy `api`.
3. Configure `API_UPSTREAM` and the health path, then deploy `app` from `apps/web/Dockerfile`.
4. Generate a Railway domain for `app` on port 80.
5. Set `APP_URL` and `API_URL` on `api` to the exact generated HTTPS origin and redeploy it.
6. Verify `app` recovers through runtime private-DNS resolution without restarting it.
7. Deploy `docs`, generate its HTTPS domain, and set `APP_URL`, `SITE_URL`, and `DOCS_URL` on the
   Docs service. These values are Docker build arguments and therefore require a new deployment, not
   only a container restart.
8. Set `DOCS_URL` on App and Docs, rebuild all affected static surfaces, and verify their outbound
   links against the exact generated HTTPS origins.
9. Deploy `mcp`, generate its HTTPS domain, and configure its origin-root `MCP_URL`.
10. Verify MCP `/healthz` and `/readyz`, then confirm `/` rejects anonymous access.
11. Sign in through the app and verify the synthetic tenant.

## Smoke checks

```bash
curl --fail --silent --show-error "https://<generated-web-domain>/healthz"
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' \
  "https://<generated-web-domain>/api/auth/me"
```

Expected results are HTTP 200 from `/healthz` and HTTP 401 from unauthenticated
`/api/auth/me`. In a browser, verify that login sets a Secure, HttpOnly, SameSite=Lax
session cookie and that authenticated pages show only synthetic demo data.

In Railway networking, verify that `docs`, `app`, and `mcp` each have one
intended public domain and neither `api` nor PostgreSQL has a public domain or TCP proxy.

## Repeat deployment from GitHub

Railway project tokens can deploy existing services but cannot connect a GitHub
repository source. Until an account owner connects each code service to
`Xentral-Labs/reality` on branch `main` in the Railway dashboard, deploy a current
checkout with:

```bash
git pull --ff-only origin main
make railway-deploy
```

The command reads `RAILWAY_TOKEN` from the ignored root `.env` when it is not already
exported, deploys `api`, `scheduler`, `worker`, `mcp`, `docs`, and `app` in
dependency-safe order, requires a database-backed sweep heartbeat from both private
background services, and verifies every public readiness endpoint. Override the demo project with
`REALITY_RAILWAY_PROJECT_ID` or the environment with
`REALITY_RAILWAY_ENVIRONMENT` when required.

Create the private `scheduler` and `worker` services once, without public domains.
Both use the repository-root `Dockerfile`; set `REALITY_BACKGROUND_ROLE` to
`scheduler` and `worker` respectively. Configure each with
`REALITY_BACKGROUND_HEALTH_PORT=8081`, a pool size of two with zero overflow, and a
private Psycopg 3 URL assembled from PostgreSQL references:

```text
postgresql+psycopg://${{Postgres-oQQF.PGUSER}}:${{Postgres-oQQF.PGPASSWORD}}@${{Postgres-oQQF.PGHOST}}:${{Postgres-oQQF.PGPORT}}/${{Postgres-oQQF.PGDATABASE}}
```

Set the API's private probes to
`http://scheduler.railway.internal:8081/healthz` and
`http://worker.railway.internal:8081/healthz`. The API remains the only migration
gate; neither background process runs Alembic. A missing role, database driver mismatch,
crash, or absent sweep heartbeat fails the repeat deployment instead of reporting a
false success.

## Logs and restart proof

Use the Railway service logs for deployment failures and the API pre-deploy logs for
migration failures. Do not copy environment-variable output into tickets or chat.

Record one stable tenant ID and one stable Reality record ID, restart only `api`, wait
for Product Web `/healthz` to recover, and re-read both IDs. Their values must remain
unchanged because managed PostgreSQL owns the persistent state. Do not restart `app`
during this check: its proxy must discover the API's new private address within 30
seconds.

## Shutdown and cleanup

Stopping public access is non-destructive; deleting PostgreSQL or the project is
destructive and requires explicit owner confirmation.

1. Remove the public domains from `app`, `docs`, and `mcp` and verify all are unreachable.
2. Revoke demo user sessions if the environment will be retained.
3. Inspect project usage and identify every remaining service, volume, bucket, and database.
4. After explicit confirmation, delete `web`, `api`, and managed PostgreSQL or delete the dedicated project.
5. Confirm that no billable demo resource remains.
6. Revoke the Railway project token in project settings.
7. Remove `RAILWAY_TOKEN` from the local ignored `.env` file.

The database cannot be recovered after destructive project/database deletion unless a
separate provider backup exists. Demo data is disposable by design.
