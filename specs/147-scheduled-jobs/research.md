# Research: Shared Scheduled Jobs

**Date**: 2026-09-09. Read-only repository research plus official upstream documentation. No live deployment verified.

## Packaging and startup

- **Decision**: Add `apps/scheduler/Dockerfile` and `apps/worker/Dockerfile`, each with a README linking the common contracts. Both install the same `reality-core` revision and expose dedicated `reality-scheduler` / `reality-worker` entrypoints. Runtime code lives under shared-core `reality/scheduling`, `reality/jobs`, `reality/services`, and thin `reality/scheduler` / `reality/worker` adapters.
- **Rationale**: Owner explicitly refined the design to separate scheduler and worker apps for deployment clarity. Existing `apps/api/Dockerfile` demonstrates package installation. No public HTTP port is needed. `reality.cli.app:boot()` calls `init_db()`, which runs migrations; importing/reusing that root command would violate single release-task migration ownership.
- **Alternatives**: A start-command override on the API image works technically, but makes the deployment purpose less visible. Running scheduling inside API replicas couples scaling and lifecycle. A separate business service would duplicate the core.

## Existing workers and first consumer

- **Decision**: Leave `invitation-worker-once` and `compose.yml` invitation-worker unchanged. Register `invitations.cleanup` as an opt-in, database-only reference handler. Adapt `services/notifications.py:cleanup_terminal_invitations` to require tenant scope and a bounded batch while preserving its default 90-day cutoff and terminal states.
- **Rationale**: Existing cleanup is an actual cron use case. The existing notification claim uses `SKIP LOCKED`; delivery includes provider I/O and an internal commit, so it is not a valid transaction-bound scheduler handler without a separate redesign.
- **Alternatives**: A no-op proves timing but no useful work. Migrating email dispatch would enlarge failure semantics; implementing the demo here would couple independent specifications.

## Persistence, claiming and effects

- **Decision**: Two tenant-scoped infrastructure tables: schedules and logical runs. Use bounded tenant catalog discovery, then only scoped queries; short claim transactions with opaque claim tokens and expiring leases. A handler runs in a bounded child process, using a fresh session and committing its database effects with run success in one transaction after ownership validation.
- **Rationale**: Restart recovery needs durable timing and occurrence identity. A lease is not an exactly-once guarantee. Stale completion must be rejected, and database effect/success atomicity removes the ambiguous commit gap for permitted handlers.
- **Alternatives**: In-memory timers lose state; Redis/Celery adds deployment components contrary to ADR 0004; a general workflow/task queue is unnecessary. Direct network side effects require a separate reviewed idempotency/reconciliation adapter and are not allowed by this first registry contract.

## Cron calculation

- **Decision**: Add a bounded `croniter` dependency during implementation, behind a pure timing adapter. Limit accepted syntax to five numeric UTC fields, `*`, lists, ranges and positive steps. Use day-of-month/day-of-week OR semantics, Sunday 0 or 7; reject extensions and expressions without a match within eight years. Preview five successive occurrences with the same bounded calculation.
- **Rationale**: Standard calendar rules should not be rebuilt. The library only computes times; persistence, claims and execution remain our services. The [official croniter documentation](https://github.com/pallets-eco/croniter) describes day matching and bounded searches. Select/pin the tested compatible release and record its license at implementation, without relying on newer grammar extensions.
- **Alternatives**: Interval-only scheduling does not meet the requested cron use case. A full scheduler library introduces a second persistence/execution model.

## Railway and portability

- **Decision**: Continuous scheduler plus continuous worker for sub-five-minute activity. Host cron may run `reality-scheduler tick` instead of the scheduler loop; an independent worker still consumes jobs. Worker one-shot mode is `reality-worker once`. Same shared-core version and database, no host scheduler API in domain. Start one replica of each; prove concurrent materialization and claims.
- **Rationale**: [Railway cron](https://docs.railway.com/cron-jobs) currently uses UTC, has a five-minute minimum, skips an overlapping next execution and expects the process to exit. It does not promise exact start-time precision. The app's five-second poll is an eligibility check, not a real-time guarantee.
- **Alternatives**: Platform cron alone cannot deliver the twelve-second demo cadence; separate cron service per tenant is not viable.

## Default operational bounds

- **Decision**: One in-flight child per worker; poll every five seconds; 30-second handler timeout; 60-second claim lease; at most three attempts with 30s/120s retry delays. A worker once claims at most ten runs, stops new claims after 25 seconds and exits within 60 seconds including child termination under healthy OS/database response. Database statement timeout 20s, lock timeout 2s, bounded connection timeout 5s. Termination grace for a child is 2s before kill.
- **Rationale**: The first cleanup and intake jobs are short database batches. Hard child isolation provides a real bound rather than pretending a Python thread timeout cancels work.
- **Alternatives**: An unbounded loop over tenants/rows or a cooperative-only timeout can starve cron and conceal stuck work. Scale bounds only with measurements and updated tests.

## Design status

All planning questions have a chosen default. No infrastructure code, migration or dependency change is included in this documentation turn. Field-level schema proof and deployment commands are proposed contracts, subject to the recorded implementation review tasks.

## Owner clarification: separate roles

The final design supersedes the initial combined-process sketch. Scheduler materialization commits pending runs and future due times atomically; it never claims or executes handlers. Worker claims pending/retry rows; it never advances schedules or invents occurrences. Both use tenant-scoped services. Scheduler tick stops new materialization after 25 seconds and exits within 30 seconds under healthy host/database response, with 2-second per-statement timeout and bounded pages. Independent role deployment is an explicit owner preference, not a new broker requirement.
