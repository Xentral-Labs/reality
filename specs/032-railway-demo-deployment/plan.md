# Implementation Plan: Temporary Hosted Product Demo

**Branch**: `codex/railway-demo-deployment` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Deploy the existing Product Web and Web/API images as two private-networked Railway services backed by managed PostgreSQL, with only Product Web receiving a public HTTPS domain. Make the existing Nginx API upstream configurable and runtime-resolved while retaining its Compose default, run Alembic as the API pre-deploy gate, use secure hosted authentication, prohibit uploads in the ephemeral-file demo profile, and add a tested operator guide. No domain, service, API, or persistence behavior changes.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript where frontend is in scope
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite as applicable
**Storage**: PostgreSQL; immutable object storage only for proven source binaries
**Testing**: pytest business stories/integration/unit; frontend build and focused UI tests
**Project Type**: backend services/API/CLI plus independent frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope
**Scale/Scope**: One short-lived demo environment, one public Product Web instance, one private Web/API instance, one managed PostgreSQL database, synthetic data only

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Existing storage and application services are unchanged; the hosted profile only transports existing records. | PASS |
| Reality owns operational state | Nginx remains a same-origin transport proxy and adds no calculations or document status. | PASS |
| Proven schema only | No database schema, typed field, or business record is added. | PASS |
| Tenant + shared service boundaries | Browser calls remain `/api` → Web/API → shared tenant-scoped services; PostgreSQL is private. | PASS |
| Spec/test traceability | Every FR/DR maps to contract tests, existing auth/tenant/migration suites, or an explicit external smoke check. | PASS |
| Explainable web behavior | Existing Inspector and projections are unchanged and are verified through the hosted Product Web. | PASS |
| Smallest coherent design | Existing Site, App, API, MCP and PostgreSQL remain; only the two required PostgreSQL-backed background processes are added, without another queue or public endpoint. | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Background deployment follow-up

FR-013 adds deployment adapters only. A repository-root Dockerfile packages the same
`reality-core` revision and dispatches through an allowlist to `reality-scheduler` or
`reality-worker` according to the provider-set `REALITY_BACKGROUND_ROLE`. The Railway
script deploys API first so migrations remain the sole schema gate, then scheduler and
worker, and requires their redacted sweep heartbeat before continuing. PostgreSQL stays
the only queue and neither background process receives a public domain. Rollback stops
the two services and reverts the adapter/script change; stored schedules and runs remain.
The Constitution Check remains PASS: no schema, business rule, tenant boundary or
Source → Evidence → Reality behavior changes.

## Repository Structure and Layer Changes

```text
apps/web/Dockerfile                              # configurable Nginx upstream defaults
apps/web/default.conf.template                   # same-origin proxy, Compose/Railway compatible
apps/web/scripts/product-boundary.test.mjs      # proxy/deployment boundary assertions
Dockerfile                                      # allowlisted Railway background-role image
scripts/deploy_railway_demo.sh                  # ordered deploy and sweep verification
docs/RAILWAY_DEMO.md                             # operator setup, smoke, restart, cleanup
docs/WORKER_DEPLOYMENT.md                        # durable background deployment contract
packages/reality-core/tests/test_repository_layout.py  # hosted profile contract checks
specs/032-railway-demo-deployment/               # intent, plan, tasks, contracts, evidence
```

**Files/layers affected**: Deployment/container adapters and documentation only. Domain, services, tools, Web/API routes, React presentation, and database schema remain unchanged.

## Design

### Reality flow

Existing `SourceRecord → Document/DocumentLine → Fact/Commitment/Reservation/Movement/LedgerEntry` flows remain authoritative in managed PostgreSQL. The deployment introduces no record, foreign key, copied status, or alternate projection.

### Service and adapter flow

The browser sends same-origin `/api` requests to the Product Web. Nginx proxies them over Railway private networking to the canonical Web/API runtime, which continues to authenticate the user and call existing application services. Local Compose keeps the `api:8000` default; Railway supplies `api.railway.internal:8000` through runtime configuration. Container startup derives the active nameserver from `/etc/resolv.conf`; Nginx uses that resolver and a variable upstream so the private hostname is re-resolved after an API-only deployment instead of pinning the address resolved at Product Web startup. A transport-level hosted setting disables signup and verification-code issuance when transactional email is intentionally absent; login remains unchanged.

### Data and migration impact

No schema or data migration is added. Existing Alembic migrations run as a pre-deploy gate against managed PostgreSQL. PostgreSQL persists business records across application restarts. File artifacts are explicitly unsupported for durable demo retention and uploads are avoided.

### Failure, security, and tenant behavior

Only Product Web receives a public domain. API and PostgreSQL have private network endpoints only. Authentication stays enabled, cookies are Secure/HttpOnly/SameSite=Lax, verification codes are neither returned nor intentionally exercised through public signup, and a strong dedicated bootstrap administrator is used only by the owner for the initial demo. The evaluator uses an approved non-admin account and tenant membership. Secrets remain provider variables/local ignored files. A failed pre-deploy migration blocks rollout; rollback redeploys the prior image while preserving PostgreSQL.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-002, FR-002a, FR-006 | deployment contract + external smoke | `apps/web/scripts/product-boundary.test.mjs`; public `/healthz`; API-only restart/recovery; domain inventory | Runtime DNS re-resolution and hosted checks are absent. |
| FR-003 | integration + external smoke | existing PostgreSQL integration; record/restart/re-read | No hosted persistence proof exists. |
| FR-004, FR-008 | deployment contract + migration tests | repository contract for pre-deploy command; existing migration suite; hosted health check | Railway release contract is absent. |
| FR-005, FR-007, FR-012 | auth + deployment contract | user-access test for disabled signup; environment/guide assertions; cookie smoke test | Hosted secure settings and signup control are absent. |
| FR-009–FR-011 | documentation contract | `packages/reality-core/tests/test_repository_layout.py` | No setup/cleanup/ephemeral-storage guide exists. |
| DR-001–DR-004 | regression suites | backend tests, tenant isolation, Product Web build/tests | Existing behavior must remain unchanged. |

## Rollout and Rollback

1. Deploy managed PostgreSQL privately.
2. Configure and deploy API with a blocking `alembic upgrade head` pre-deploy command and `/healthz` health check.
3. Configure Product Web with the private API upstream and deploy it with `/healthz` health check.
4. Generate a public domain only for Product Web and set the exact public origin on API.
5. Run authentication, tenant, persistence, and exposure smoke checks.
6. Roll back application failures by redeploying the last healthy versions; never roll back schema by destructive commands.
7. Cleanup removes the public domain first, then sessions/services/database/project after explicit confirmation, and finally revokes the token.

## Review Risks

- Public signup without a configured mail provider can place verification messages in logs; the demo must avoid public signup until a real provider or explicit restriction exists.
- A bootstrap platform administrator can access all tenants and must not be shared with evaluators.
- Railway's generated domain must exactly match `APP_URL` before authentication redirect/cookie verification.
- Nginx must use runtime DNS resolution for the variable upstream; resolving the hostname only at Product Web startup pins a stale address after an API-only redeploy.
- Default file artifact storage is ephemeral and may leave metadata without binaries after redeploy; uploads are out of scope.
- A project-scoped token may deploy but may not provision all infrastructure; automation must stop cleanly if Railway refuses a scoped operation.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Repository split amendment
Use explicit --only product|site|all and --dry-run modes in the existing Bash entrypoint. Resolve product root from script location and site root from REALITY_RAILWAY_SITE_ROOT. Upload each absolute root with --path-as-root. Preflight selected Dockerfiles and Git revision before authentication or deployment. No service, schema, domain or recurring-job changes. Constitution check PASS. Regression tests mock Railway/curl and verify routing, preflight failure and dry-run behavior before implementation.
