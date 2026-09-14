# ADR 0006: Separate scheduler and worker apps over PostgreSQL

**Status**: Owner selected this deployment split on 2026-09-09; implemented with schema review recorded in spec 147. Refines ADR 0004 packaging, not its PostgreSQL/shared-core boundary.

## Context

Subsystems need calendar jobs and short intervals without browser activity. The owner requested Docker-oriented app/service naming and explicitly selected separate scheduler and worker deployments after considering a combined process.

## Decision

Create `apps/scheduler/` and `apps/worker/`, deployed as services `scheduler` and `worker`. Both package the same `reality-core` revision and connect to existing PostgreSQL. Neither has a public port, another business database, a broker or an in-container cron daemon.

- Scheduler calculates due times and atomically inserts pending runs into PostgreSQL.
- Worker independently claims pending/retry runs and executes registered application handlers.
- Queue means pending/retry run state in PostgreSQL; it is not a third service.

Shared core responsibilities:

- `reality/scheduling/`: pure interval/cron calculation.
- `reality/jobs/`: definitions, handler registration and bounded execution support.
- `reality/services/scheduled_jobs.py`: tenant-scoped schedule/materialization/claim/outcome services.
- `reality/db/scheduled_jobs.py`: schedule/run records.
- `reality/scheduler/cli.py` and `reality/worker/cli.py`: thin process adapters.

`reality-scheduler work` provides the continuous clock; `reality-scheduler tick` materializes once and exits. Linux crontab, Railway cron or another host can invoke tick instead of the scheduler service. Worker consumption is still required: `reality-worker work` or bounded `reality-worker once`. Neither one-shot command performs the other role's work.

Use dedicated entrypoints because the existing `reality` CLI bootstrap invokes migrations. Only the existing release task performs migrations. Initial handlers perform transaction-bound database work/durable intake only; direct external side effects need a later reviewed retry/reconciliation contract.

## Why and alternatives

The split makes logs, restart policies and independent scaling explicit. These are deployment roles over one application core, not separate business services. A combined process or API-image command override would be smaller operationally; the owner preferred the clear deployment split. Small Docker packaging files install the same package, avoiding a duplicate business implementation.

This refines ADR 0004's one-image/one-worker sketch without introducing a broker or new business boundary. A host cron provides a wake-up schedule; the application scheduler determines due tenant work; the PostgreSQL queue preserves it for workers. Coarse host cron does not promise the demo's short intervals.

## Consequences

Two tenant-scoped infrastructure tables are justified in [the data model](../../specs/147-scheduled-jobs/data-model.md). Start one scheduler and one worker replica, but prove scheduler uniqueness and worker claim fencing under overlap. A stopped worker cannot grow one pending run per missed interval because only one unfinished occurrence per schedule is allowed. Queue caps defer scheduling visibly.

Run identity and effect idempotency remain mandatory; leases alone cannot prevent duplicate effects. Existing invitation delivery remains unchanged; new retention cleanup is opt-in. Spec 146 owns the Demo Data integration and consumes this timing contract.

## References

- [Developer contract](../features/scheduled-jobs.md)
- [Deployment](../WORKER_DEPLOYMENT.md)
- [Spec 147](../../specs/147-scheduled-jobs/spec.md)
- [ADR 0004](0004-production-storage-and-projections.md)
