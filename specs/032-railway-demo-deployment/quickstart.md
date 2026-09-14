# Quickstart: Verify the Hosted Reality Demo

## Preconditions

- The dedicated provider project/environment exists.
- Only anonymised or synthetic data is permitted.
- The project-scoped deployment token is stored outside version control.
- Product Web, API, and PostgreSQL match [the hosted profile](contracts/hosted-demo-profile.md).

## Local contract verification

```bash
python3 scripts/check_spec_policy.py
make lint
make test
make web-build
```

## Hosted smoke verification

Set `DEMO_URL` to the generated Product Web HTTPS origin without a trailing slash.

```bash
curl --fail --silent --show-error "$DEMO_URL/healthz"
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' \
  "$DEMO_URL/api/auth/me"
```

Expected results:

- `/healthz` returns HTTP 200 and `{"status":"ok"}`.
- unauthenticated `/api/auth/me` returns HTTP 401.
- the browser login response sets a Secure, HttpOnly, SameSite=Lax cookie.
- authenticated bootstrap and tenant pages show only authorised synthetic demo data.

## Persistence verification

1. Record the prepared tenant ID and one stable Reality record ID.
2. Restart only the API service.
3. Wait for Product Web `/healthz` to return 200.
4. Re-read the same tenant and record through the authenticated Product Web.
5. Confirm that both IDs and business values are unchanged.
6. Without restarting Product Web, confirm `/healthz` and `/api/auth/me` recover within 30 seconds after the API receives its new private address.

## Exposure verification

Inspect provider networking and confirm:

- Site and Product App each have exactly one public HTTPS domain.
- API has no public domain.
- PostgreSQL has no public TCP proxy.
- Product Web reaches API only through the provider's private network.

## Cleanup rehearsal

Follow the cleanup order in the hosted profile. Database/project deletion is destructive and requires explicit owner confirmation. Verify that the public URL is unavailable and the project token is revoked after the demonstration.

## Hosted verification record — 2026-09-02

- Railway project: `reality-demo` (`<redacted-id>`)
- Environment: `production` (`<redacted-id>`)
- Public Product Web: `https://<generated-railway-domain>`
- Public Site: `https://<generated-railway-domain>`
- Public MCP: `https://<generated-railway-domain>/`
- API service: private only (`<redacted-id>`)
- Product Web service: public HTTPS only (`<redacted-id>`)
- Public Site service: public HTTPS only (`<redacted-id>`)
- MCP service: authenticated public HTTPS origin (`<redacted-id>`)
- Active database selected by the API: private Railway PostgreSQL service
- API migration log: upgrades `0001_initial` through `0029_ledger_reversals` completed
- Product Web `/healthz`: HTTP 200 with `{"status":"ok"}`
- Anonymous `/api/auth/me`: HTTP 401
- Schema-valid `/api/auth/signup`: HTTP 403
- Prepared administrator login: HTTP 200
- Authenticated `/api/auth/me`: HTTP 200
- Session cookie: `Secure`, `HttpOnly`, and `SameSite=Lax`
- Public Site root: HTTP 200
- Public Site account origin: Product App HTTPS origin verified in the deployed bundle
- MCP `/healthz`: HTTP 200
- MCP database-backed `/readyz`: HTTP 200
- Anonymous MCP origin request: HTTP 401
- Product App runtime-DNS deployment: `<redacted-id>`
- API-only restart deployment: `<redacted-id>`
- Product App deployment ID remained unchanged during the API-only restart
- Post-restart Product App `/healthz`: HTTP 200
- Post-restart anonymous `/api/auth/me`: HTTP 401
- Private API address recovery required no Product App restart

No API domain or PostgreSQL TCP proxy was created. Persistence across an API restart
still requires a named synthetic Reality record and remains an explicit follow-up
before claiming the US2 acceptance criterion.

## Background deployment record — 2026-09-09

- Scheduler service: private only (`<redacted-id>`)
- Worker service: private only (`<redacted-id>`)
- Shared application revision: `cebd097`
- Scheduler deployment: `<redacted-id>`, `SUCCESS`
- Worker deployment: `<redacted-id>`, `SUCCESS`
- Both use private PostgreSQL references with the explicit Psycopg 3 dialect.
- Repeated `scheduler_sweep` and `worker_sweep` events proved database-backed idle loops.
- Both services have no public domain; API private health URLs target port 8081.
- API was redeployed after the private health configuration changed.
