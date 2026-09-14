# Worker App

**Status: implemented; not deployed by this change.** Local verification is recorded in [spec 147 quickstart](../../specs/147-scheduled-jobs/quickstart.md). New schedules remain disabled until explicitly activated.

- Service name: `worker`.
- Shared-core entrypoint: planned `reality.worker.cli:app` / `reality-worker`.
- Continuous command: `reality-worker work --poll-seconds 5`.
- Bounded command: `reality-worker once --max-runs 10 --max-seconds 25`.
- Responsibility: claim queued pending/retry runs and execute registered, bounded application handlers.
- Does not create timed occurrences, expose HTTP or run migrations.

The independent [scheduler app](../scheduler/README.md) produces scheduled work. Both package the same `reality-core` revision and use PostgreSQL as the queue. Business behavior remains in application services. The existing invitation-delivery worker is not migrated by this feature.

See [developer contract](../../docs/features/scheduled-jobs.md), [deployment](../../docs/WORKER_DEPLOYMENT.md), and [CLI interfaces](../../specs/147-scheduled-jobs/contracts/worker.md). Run success describes the registered handler's result, not arbitrary downstream business completion.
