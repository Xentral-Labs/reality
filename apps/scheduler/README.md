# Scheduler App

**Status: implemented; not deployed by this change.** Local verification is recorded in [spec 147 quickstart](../../specs/147-scheduled-jobs/quickstart.md). New schedules remain disabled until explicitly activated.

- Service name: `scheduler`.
- Shared-core entrypoint: planned `reality.scheduler.cli:app` / `reality-scheduler`.
- Continuous command: `reality-scheduler work --poll-seconds 5`.
- Host-cron command: `reality-scheduler tick --max-runs 100 --max-seconds 25`.
- Responsibility: determine due schedules and atomically enqueue pending runs in PostgreSQL.
- Does not execute handlers, expose HTTP or run migrations.

The independent [worker app](../worker/README.md) consumes the queue. Both package the same `reality-core` revision. All timing, registry and persistence behavior belongs in the shared core, not this app directory.

See [developer contract](../../docs/features/scheduled-jobs.md), [deployment](../../docs/WORKER_DEPLOYMENT.md), and [CLI interfaces](../../specs/147-scheduled-jobs/contracts/worker.md). Do not add an OS cron daemon or duplicate these canonical contracts here.
