# Scheduler and Worker Deployment

**Status: implemented; not deployed by this change.** Local verification is recorded in [spec 147 quickstart](../specs/147-scheduled-jobs/quickstart.md). New schedules remain disabled until explicitly activated.

## Names and roles

| App directory | Docker/Railway service | Executable | Responsibility |
|---|---|---|---|
| `apps/scheduler/` | `scheduler` | `reality-scheduler` | Materialize due jobs in PostgreSQL |
| `apps/worker/` | `worker` | `reality-worker` | Consume queued jobs and execute handlers |

Both images install the same `reality-core` version as API/MCP, share the existing database and expose no port. The queue is PostgreSQL run state, not another service. Pure timing is in `reality/scheduling/`, registration/execution support in `reality/jobs/`, shared persistence services in `reality/services/`. App directories contain packaging and a README linking these contracts.

```text
API / operator / integration controls
                  |
          schedules in PostgreSQL
                  ^
                  |
scheduler container: due-time calculation
                  |
          pending runs in PostgreSQL
                  |
worker container: claim -> handler -> shared application service
```

The canonical interfaces/bounds are in [Worker Interfaces](../specs/147-scheduled-jobs/contracts/worker.md), developer recipe in [Shared Scheduled Jobs](features/scheduled-jobs.md). No OS cron daemon runs inside either container.

## Railway continuous deployment

For an authorized deployment:

1. Create `scheduler` and `worker` services from the same repository/core revision. On Railway both use the repository-root `Dockerfile`; set `REALITY_BACKGROUND_ROLE=scheduler` and `REALITY_BACKGROUND_ROLE=worker` respectively. The dispatcher rejects every other role. Other container platforms may continue to use `apps/scheduler/Dockerfile` and `apps/worker/Dockerfile` directly.
2. Set `REALITY_DATABASE_URL` to the private PostgreSQL reference using the existing SQLAlchemy/Psycopg URL convention. Both images use the existing `REALITY_ROOT=/app/packages/reality-core` convention. Initial cleanup needs no mail/provider credentials.
3. Run the additive migration once through the existing API release migration gate. Neither image build nor either process startup runs migrations. Deploy these processes only after the migration succeeds.
4. Scheduler command: `reality-scheduler work --poll-seconds 5`. Worker command: `reality-worker work --poll-seconds 1` — an idle worker sweep costs one query because it discovers only tenants with claimable runs (feature 201), so a new company is picked up within a second. Initially one replica of each; multiple replicas must remain safe through database uniqueness/claims.
5. Configure no public domains/HTTP healthchecks. Keep both continuous services running; idle sleeping would interrupt work. Use host restart-on-failure for persistent services.
6. Bound each process's parent database pool to two connections, plus one fresh connection for the worker's active child. Scheduler never starts handler children. Additional worker replicas increase this connection budget and require capacity review.
7. Inspect `scheduler_sweep` / `worker_sweep` redacted logs, emitted at least every 30s during healthy idle operation. Process activity is distinct from run/effect success. Use tenant-scoped status reads to verify actual outcomes.

The Railway repeat deployment runs API migrations first, then deploys scheduler and
worker and waits for their respective sweep heartbeat before continuing with other
surfaces. A completed image build without a running sweep is a failed release. Use a
`postgresql+psycopg://` private URL; Railway's generic `postgresql://` URL selects the
uninstalled legacy Psycopg 2 dialect in SQLAlchemy.

Build and start the separate images:

```bash
docker build -f apps/scheduler/Dockerfile -t reality-scheduler .
docker build -f apps/worker/Dockerfile -t reality-worker .
docker run --rm --env-file /secure/reality-worker.env reality-scheduler
docker run --rm --env-file /secure/reality-worker.env reality-worker
```

Start the two `docker run` commands as separate services/terminals; Compose is the normal local equivalent. Both Dockerfiles use CMD, not a fixed ENTRYPOINT, so explicit command overrides work. No activation is performed automatically on startup.

## Linux crontab or host cron

For workloads that tolerate the host's interval, replace the continuous scheduler service with an external cron invocation:

```bash
reality-scheduler tick --max-runs 100 --max-seconds 25
```

A continuously running worker still consumes the queued work. Alternatively schedule worker one-shot consumption separately with `reality-worker once --max-runs 10 --max-seconds 25`, accepting extra latency. **Scheduler tick does not execute jobs.**

Example Linux host crontab:

```cron
*/5 * * * * docker run --rm --env-file /secure/reality-worker.env reality-scheduler reality-scheduler tick --max-runs 100 --max-seconds 25
```

The first `reality-scheduler` is the image, the second its executable override. Use the host's actual absolute Docker path and an operator-managed env file outside the repository. The host schedule wakes the process; the application schedule determines which tenant jobs are due. A host tick every five minutes cannot provide twelve-second arrivals.

On Railway, configure a cron service using the scheduler image and tick command, for example `*/5 * * * *`, instead of the continuous scheduler loop. Railway currently uses UTC, has a five-minute minimum, skips overlapping execution and expects the process to finish. Exact start precision is not guaranteed. Recheck at deployment. [Railway cron documentation](https://docs.railway.com/cron-jobs)

Use no always-restart policy for one-shot containers. Expected persisted retry returns exit 0 from worker once; newly terminal/unresolved or infrastructure failure returns 1. Avoid immediate repeated manual invocations with new request keys. Global one-shot budget exhaustion can leave tenants/work for later; use continuous modes for short intervals or large tenant catalogs.

Docker Compose services, Kubernetes Deployments and ordinary container platforms use the two continuous commands. A Kubernetes CronJob or scheduled container task can use either one-shot command with the same role distinction and shared database.

## Failure, shutdown and rollback

- Stopping scheduler stops new timed occurrences; worker can drain existing work. Stopping worker leaves queued work durable. Repeated scheduler sweeps do not create an unbounded backlog for a blocked schedule.
- Scheduler stops new materialization on SIGTERM/SIGINT, uses 2s statement timeouts and a 25s tick budget, and exits within 30s under healthy host/database response. Give it at least 5s graceful termination for a current bounded transaction.
- Worker stops new claims on signal. Give it at least 125s grace for the longest registered child (the 120s canonical company setup) and cleanup. Ordinary jobs retain a 30s child timeout. Worker once stops new claims after 25s; an already claimed setup may finish within its registered bound before the process exits.
- Neither command runs Alembic. Missing schema is an explicit startup failure. Help and registry metadata listing need no database; status is read-only.
- Queue cap is 1,000 unfinished runs per tenant, one unfinished scheduled occurrence per schedule. At the cap, scheduler reports deferral and preserves the due occurrence instead of dropping it.
- Pause schedules before intentionally stopping future intake. Roll back code by stopping both services first, keeping additive tables/history intact. Unsupported handler/version remains visibly suspended. Do not reset business data or drop the queue as recovery.
- The existing `invitation-worker` is not replaced. Its provider delivery loop remains a separate prior capability until separately migrated.

## Validation and live evidence

Follow [quickstart](../specs/147-scheduled-jobs/quickstart.md) in disposable PostgreSQL first. Live rollout records revision, migration head, both process modes, schedule/run IDs and observed effects. A running container, log heartbeat or repository test does not alone prove deployed business behavior.

## Optional Demo Data source

Spec 146 registers `demo.generate_orders` alongside invitation cleanup. Deploy matching
API, scheduler and worker images and apply migration `0046_company_setup_demo` once
through the release command. Private practice companies and Storylines are regular
capabilities under existing account policies (spec 193); their availability does not
activate their sources. Connect Demo Data in
an eligible Sandbox and explicitly Start it, or select Live simulation during canonical
demo company creation to provision and start it automatically. Rates 10/60/300 per hour map to intervals
360/60/12 seconds; the existing five-second polling loop is sufficient.

The producer uses the durable delivery's creation timestamp rather than an old missed
due time. Retries reuse existing source payloads and the same delivery identity.
Source orders are synthetic, have no provider credentials and trigger no reservation,
shipment, procurement or payment. Closing the browser has no effect on delivery.
Paused, stopped and disconnected sources retain all history. At 20 pending/failed
imports the source pauses; retry the failed immutable inputs and explicitly Resume.
See [Company setup and Demo Data](features/company-setup-demo.md) for service entrypoints,
source inspection and authorization. No additional deployed app or queue is needed.

## Optional private readiness (spec 149)

Continuous processes can expose `/healthz` on `REALITY_BACKGROUND_HEALTH_PORT`.
Compose uses private port8081 with no published host port. API configuration and
Railway private-network setup are documented in [Home readiness](features/home-live-status.md).
This is a health endpoint only; scheduler and worker remain CLI job processes.


## Projection deployment and rollback (spec 179)

Apply migration `0057_projection_jobs` through the release migration task before
running the updated scheduler, worker and API from the same revision. Scheduler
sweeps initialize old/new companies and detect dirty projections from the committed
outbox; no manual per-company schedule or user actor is needed for cache upkeep.
Run `reality-scheduler tick --help` and `reality-worker once --help` for existing
bounded, optional tenant-scoped commands. Scheduler tick alone does not calculate
data; the worker must consume its runs. Existing user schedules are unchanged.

An unavailable worker leaves the last completed data with pending/failed metadata;
reads do not repair it. Inspect the existing scoped run status for failures and
retry outcomes. An explicit trusted maintenance call to
`refresh_operational_projections(session, tenant_id, force=True)` can rebuild and
acknowledge terminal cache failure, using the existing service rather than ORM
writes. Reconcile unresolved running outcomes first. Do not expose this internal
maintenance capability as a user business action.

For code rollback, stop updated dispatch/consumption before restoring older code
and retain the additive queue schema and internal history. Schema downgrade
intentionally refuses while actor-less internal runs exist; it never deletes
history or fabricates an actor. Startup never migrates the database.
