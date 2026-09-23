# Shared Scheduled Jobs

**Status: implemented; not deployed by this change.** Local verification is recorded in [spec 147 quickstart](../../specs/147-scheduled-jobs/quickstart.md). New schedules remain disabled until explicitly activated.

## Ownership and vocabulary

- **Scheduler** determines when a registered job becomes due and records a durable run.
- **Queue** is pending/retryable run state in PostgreSQL, not a separate broker.
- **Runner** claims and executes bounded work with retry and ownership checks.
- **Scheduler app** materializes due runs into the PostgreSQL queue.
- **Worker app** independently consumes and executes queued runs.
- **Subsystem** owns payload generation, retention or other business meaning and authorization; it never reimplements scheduling.

The selected deployment has `apps/scheduler/` and `apps/worker/`, each installing the same shared `reality-core` package/revision. Shared rules/services live under `packages/reality-core/src/reality/`; the app directories own Docker packaging and deployment instructions only. Shared-core `scheduling/` owns timing, `jobs/` definitions/execution, `scheduler/cli.py` and `worker/cli.py` thin process adapters. Each service serves many tenants. Neither the browser nor an API replica provides the clock. See [ADR 0006](../decisions/0006-shared-scheduled-worker.md).

## Add one subsystem

1. Define a stable allowlisted job name and a Pydantic configuration type. Reject extra fields. Keep secrets outside configuration; store only references to tenant-owned resources.
2. Add a registration in `reality/jobs/registry.py`, naming the handler, permission validator, configuration schema and contract version. Duplicate names fail startup validation. Do not register a Python import path or shell command supplied by the caller.
3. Implement one short handler under the owning subsystem/service. It receives the existing session and `JobContext(tenant_id, actor_id, run_id, scheduled_for, deadline)`. Revalidate the referenced resource's current authorization. Never select a fallback tenant.
4. Return `JobResult` containing safe counts and optional typed opaque result references, not source payloads or commercial calculations. Success means this handler completed its stated effect, not that all downstream work succeeded.
5. Create a disabled schedule through `services/scheduled_jobs.py:create_schedule`; preview, then explicitly resume it. A source's Start/Pause/Stop controls call these same services. Stop pauses timing; the subsystem decides whether a later start has a fresh business run identity.
6. Add registry/parameter tests, tenant/actor refusal, same-run retry, real PostgreSQL concurrency and one business story. The generic runtime tests cannot prove a handler's own effect idempotency.

### Minimal reference registration

This reference is exercised by the executable documentation-contract test. Supporting signatures are defined in [the interface contract](../../specs/147-scheduled-jobs/contracts/worker.md).

```python
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from reality.services.notifications import cleanup_terminal_invitations
from reality.jobs.registry import (
    JobContext, JobDefinition, JobResult, require_company_owner,
)


class CleanupConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


def cleanup(session: Session, context: JobContext, config: CleanupConfig) -> JobResult:
    removed = cleanup_terminal_invitations(
        session, tenant_id=context.tenant_id, limit=100
    )
    return JobResult(counts={"invitations_removed": removed})


CLEANUP = JobDefinition(
    name="invitations.cleanup",
    version=1,
    config_model=CleanupConfig,
    authorize=require_company_owner,
    handler=cleanup,
)
```

`require_company_owner` is the registry authorization callback wrapping existing tenant/account membership rules; it is supplied by the registry module alongside the context/result definitions. Cleanup keeps the existing terminal states and 90-day cutoff, adds tenant scope and a maximum 100-record batch, and sends no email. It creates no schedule automatically.

### Transaction and effect contract

Initial handlers may do database-transaction work or enqueue durable source intake in that same transaction. They must not commit, open autonomous write transactions or perform direct network effects. Handler writes and run success commit together. A future external-I/O consumer needs its own reviewed idempotency/reconciliation adapter; adding a timer does not make external retries safe.

Every run has a stable ID across retries and frozen validated inputs. Claims have separate changing tokens. The child validates and locks its current claim, and validates it again before commit. A stale process cannot publish success or duplicate a database effect after reclaim. Domain services still enforce their own identity and concurrency rules.

For demo intake, derive upstream delivery identity from the subsystem's business run and scheduler run ID; reuse it on retry. SourceRecord → ImportJob intake occurs through the normal service with the supplied session. The producer never inserts operational rows directly. Later interpretation remains a separate processing outcome. If an existing intake entrypoint commits internally, adapt a shared transaction-bound service before registering it; do not weaken this contract.

## Registered subsystems

`projections.refresh`, `invitations.cleanup`, `demo.generate_orders`,
`demo.settle_orders`, `costing.inventory.refresh`, `costing.contribution.refresh`,
`costing.captured_report.refresh`, `costing.captured_report.publish` and `company_setup.initialize`. The last one seeds a confirmed
company profile outside the request that asked for it (feature 199); its ownership rule
is the playground run's own owner rather than `require_company_owner`, because a
verified account pending admission may create a Sandbox. `create_manual_run` authorizes
by job type, so a manually enqueued run and the same job on a timer share one rule.

A worker sweep discovers only the tenants that hold a claimable run — pending, retrying,
or running past its lease — through `due_tenants`, which uses the same predicate
`claim_next` claims by (feature 201). An idle installation therefore costs one query per
sweep instead of one per tenant, which is why the worker polls every second and a new
company is picked up almost at once. The scheduler keeps the full tenant catalog,
because it materializes schedules that no run represents yet.

## Timing and controls

- Intervals are whole seconds from 5 to 2,147,483,647 (the stored integer bound). Cron has five numeric UTC fields: minute, hour, day of month, month, weekday. Allow `*`, comma lists, inclusive ranges and positive steps; reject names, macros, seconds/year and extensions. Sunday is 0 or 7. Restricted day-of-month and weekday use OR semantics.
- Cron calculation uses a bounded library adapter; an expression with no occurrence within eight years fails. The preview uses the same calculation and returns the next five occurrences.
- Creation is disabled. Ordinary schedules activate/resume strictly after now; first interval work is due after one interval. Spec 207 adds an internal opt-in finite initial-offset sequence for interval schedules: first activation uses those offsets (including zero), then returns to the ordinary interval. Pause, ordinary resume and timing/configuration edits abandon remaining initial offsets. No existing schedule opts in implicitly.
- Downtime coalesces missed occurrences to one run. For interval work, preserve the interval grid by calculating the first grid time after now; for cron, use the next occurrence after now. Never loop to create every missed run.
- Only one unfinished run per schedule exists. Retry retains its original `scheduled_for` and inputs. Future schedule edits cannot rewrite it.
- Pause prevents new claims, including retries. Already handed-off work can finish; controls do not roll it back. Resume first retries a frozen unfinished run, if any; an unresolved outcome requires reconciliation before resume.
- Changes to job configuration, actor or timing require no unfinished run and expected revision. A new control request with a stale revision fails without mutation. Repeating the latest identical request returns its result; older requests fail stale rather than apply again.
- A third failed attempt or permanent failure halts the schedule, and how it halts depends on what failed (spec 256). An **infrastructure** failure — `database_error`, `handler_timeout`, `child_exited`, where the work never reached a business verdict — suspends it with `scheduled_job.resume_after` four to eight hours ahead, drawn per suspension so companies interrupted by one outage do not wake together. The scheduler revives such a schedule at the start of its sweep: `enabled` again, `resume_after` cleared, next occurrence at that moment. The suspended interval is never replayed, and the schedule stays disabled while it waits, so no backlog accumulates. Every other failure, including an authorization refusal, halts the schedule permanently as before and is never re-enabled automatically.
- Any owner control — pause, resume, stop, update — clears `resume_after`: what a person decided is no longer a source waiting for its own recovery.
- A failure retains a bounded `scheduled_job_run.failure_detail`: the exception class and a truncated message, cut before any statement or bound parameters. It is operator diagnosis; tenant-facing reads expose the error code and a translated cause, never this text.
- Explicit resume after a terminal failure acknowledges that occurrence and schedules future work. Unknown outcomes remain blocked until proven completed or not executed; operators cannot blindly mark success.

## Limits and failure handling

Defaults: five-second poll, one child at a time, 30-second child timeout, a lease 30 seconds longer than the registered timeout, three total attempts, and retry delays of 30s and 120s. The bounded canonical company-setup job declares a 120-second timeout because it seeds and verifies the complete profile in one transaction; its lease is therefore 150 seconds. Other registered jobs retain the 30-second timeout and 60-second lease. The worker derives both its child deadline and claim lease from the same registered definition so they cannot contradict each other. A worker once claims at most ten runs and stops new claims after 25 seconds. A child receives termination, then is killed after two seconds if needed. No lease renewal is required for these bounded jobs.

Use database statement timeout 20s, lock timeout 2s and connection timeout 5s. Open fresh child connections; never reuse inherited session/pool connections. Child failure affects its run, not registry availability or other jobs. Retry only classified transient failures. Unknown job/configuration is a visible permanent error. Database uncertainty is reconciled by reading run state before any redispatch; if it cannot be settled, leave it unresolved.

Tenant discovery reads the existing tenant catalog in pages of 100; it does not read business rows across tenants. Due claims and status queries always include tenant_id. At most one run per tenant is claimed per sweep, continuing catalog pagination from a rotating cursor in continuous mode. Both one-shot commands accept an optional tenant scope; repeated cold starts of a global tick do not promise fairness across a very large catalog. Use continuous scheduler and worker modes for such workloads and expose budget-exhausted output. No new tenant-global scheduler metadata table is introduced.

Run identity/history remains retained in V1. Status queries are paginated; storage retention is a separate future decision so deleting retry identities cannot silently enable replay.

## Authorization and exposure

Schedule control uses an explicit existing actor with current owner membership for the reference cleanup. The worker is trusted infrastructure that dispatches existing authorization; it does not invent a user or bypass handler policy. Every attempt rechecks actor, tenant and referenced source. Archive/revocation prevents new handoff; no claim can cancel a transaction already committed.

The initial interface is operator CLI plus shared services. No scheduling tools are exposed to Chat/MCP or the web CLI console. Future user-facing controls need their own spec and ordinary confirmation rules. An explicit recurring source Start authorizes only that source intake, never downstream reservations, shipment, payments or proposal confirmation.

## How to operate and inspect

Use dedicated `reality-scheduler` and `reality-worker` CLIs, not `reality`'s existing bootstrap. See [commands](../../specs/147-scheduled-jobs/contracts/worker.md) and [worker deployment](../WORKER_DEPLOYMENT.md). List registered definitions, preview a schedule, inspect next due times and paginate run results. Status commands perform no scheduling, cache refresh or business writes.

Logs contain role-specific sweep counts, budget flags, safe infrastructure errors and tenant/run outcome identifiers with elapsed time; detailed attempts and safe error codes are available through scoped status reads. Results distinguish scheduled handler completion from downstream import/interpretation. There is no public worker port or HTTP-triggered cron endpoint. Migration runs once through the existing release task; worker startup only checks required schema availability.

## Ownership across specifications

Spec 147 owns timing, claims, retries and runtime contracts. [Spec 146](../../specs/146-company-setup-demo/spec.md) owns Demo Data configuration, international fixture references, synthetic order generation, source status/counts and isolation of the Atlas execution fixture. Its generator consumes an interval schedule; it does not own a second timer. Existing invitation delivery remains on its original worker until separately migrated.

## Separate process roles

`reality-scheduler work` checks timing every five seconds; `reality-scheduler tick` does a bounded scheduling pass, then exits. Both only insert pending runs and advance due times atomically. Scheduler never invokes handlers. Tick stops new work after 25s, uses 2s statement timeouts and exits within 30s under healthy host/database response.

`reality-worker work` consumes pending/retry jobs continuously; `reality-worker once` consumes a bounded batch then exits. Neither calculates new scheduled occurrences. Stopping scheduler leaves worker free to drain the queue. Stopping worker leaves durable pending jobs for later execution. Cron can trigger either one-shot executable, but running scheduler tick alone never completes a job.

The queue cap is 1,000 unfinished runs per tenant, including manually enqueued jobs. Serialize queue-cap checks through the tenant row before schedule/run locks. At the cap, defer materialization without advancing the due time and report backpressure. One unfinished run per schedule prevents a stopped worker producing an interval-sized backlog.

Optional process readiness is specified by [Home live status](home-live-status.md).
It uses volatile sweep observations, never scheduling/business persistence.

## Internal projection upkeep (spec 179)

The shared scheduler also discovers committed-outbox projection lag through
`services.projection_jobs.enqueue_due_projections`. It alternates eligible scheduled and cache work using retained run history,
including cold ticks, and coalesces dirty projection names into one unfinished
`projections.refresh` run per tenant. Queue capacity defers this work without
advancing a checkpoint or blocking an acknowledged business write. Missing caches
and builder-version changes use the same bootstrap path. Exceptions, commitment
risk and tenant activity become eligible every minute to account for time and
activity without business events. The browser never schedules this work.

These runs are explicitly infrastructure-owned: `actor_id` is NULL only for the
allowlisted projection job, and a database constraint rejects NULL for every other
job type. They have no schedule and cannot be created through manual/schedule
operator APIs. Every attempt validates the active tenant and scoped internal run.
This is permission to rebuild disposable caches only, never permission to reserve,
ship, post money, interpret a source, or perform an external effect. Existing
user job authorization and Demo Data schedules retain their rules.

Projection children select REPEATABLE READ before executing the claim. A
transaction advisory lock serializes builders for that tenant; rows, completed
event targets and run success commit together. Concurrent business commits remain
visible as lag after publication. The worker does not hold the tenant's business
writer lock while deriving rows. Explicit maintenance callers at READ COMMITTED
use that existing lock for a stable rebuild and should run during maintenance.

Retries retain run identity and existing claim fencing. Final failure or unresolved
execution is visible through snapshot metadata and job status. Do not blindly
recreate failed runs: an explicit successful maintenance rebuild acknowledges a
terminal failed cache generation; unresolved claims first need the existing runner
reconciliation. Historical failed runs remain retained. Ordinary reads never
refresh or enqueue a projection.

Required schema: migration `0057_projection_jobs`. It preserves existing data and
adds no table. Downgrade refuses while internal job history exists; code rollback
should retain this additive schema. No process startup runs migrations. Validation
and current implementation evidence: [spec 179 quickstart](../../specs/179-background-projections/quickstart.md).


## Finite initial timing (spec 207)

`create_schedule` may receive `initial_offsets_seconds`: at most ten nonnegative,
ascending offsets within one hour, spaced at least five seconds apart, for interval
schedules only. Demo Start selects `(0, 12, 24)`. The existing configuration envelope
holds these offsets and the first activation anchor; no migration is required. The
scheduler freezes an `initial_occurrence` marker into each initial run, allowing the
demo handler to produce one order without controlling timing. Fresh dictionary values
keep frozen run inputs independent of later schedule changes. Missed offsets coalesce;
queue capacity and one-unfinished-run rules still apply. Other jobs and public scheduling
command schemas retain their existing defaults. Tests: `test_scheduled_job_startup.py`
and `test_demo_data_startup.py`.

## Retained inventory cache (spec 234)

`costing.inventory.refresh` is an owner-authorized, database-only job with strict
`{"review_id": "<confirmed-inventory-review-id>"}` configuration. Each execution
revalidates the active owner and tenant review, then calls the shared costing service.
It rebuilds one bounded retained item scope and publishes a disposable observation in
the same transaction as run success. Existing claim fencing and deadlines apply.
Retry and duplicate jobs retain one generation per review/algorithm. The result holds
safe counts and a `cost_inventory_generation` reference; it does not return monetary
values in job logs or approve new cost evidence.

Registration creates no schedule or automatic cache upkeep. Use the existing confirmed
operator workflow to enqueue a manual run; reads never enqueue. Freshness and source
traceability are described in [receipt costing](receipt-costing.md). Migration0069
must precede execution, never run at worker startup. Before schema rollback, remove the
registration and drain/cancel unfinished runs; the migration refuses while any remain.

The existing `costing.inventory.refresh` definition also accepts a confirmed batch
`action_id`, mutually exclusive with `review_id`. Its handler uses the shared joint
inventory builder and the same actor, claim, deadline and transaction checks. It reports
only created-generation/row counts and opaque member references. Existing review-only
configuration serialization is preserved for request-fingerprint compatibility. Batch
support adds no registration, automatic schedule or startup migration. Drain pending batch
configs before rolling back that config extension; migration0069's existing job guard
covers both forms because the job name is unchanged.


### Retained joint contribution refresh

`costing.contribution.refresh` accepts exactly `action_id` for an executed
contribution_batch_review. The shared registry/worker checks the active owner and
tenant-bound confirmed membership at admission and execution. Its handler calls
`build_contribution_generation` with the shared deadline and returns counts plus an
opaque cost_contribution_generation reference. All calculations precede cache writes;
publication is atomic and same-basis retries reuse verified output. It does not approve
revenue, costs or policy, and no schedule is created or resumed automatically. Migration
0070 refuses cache removal while this job has unfinished runs.

### Bounded captured report refresh

`costing.captured_report.refresh` accepts exactly one sealed retained `basis_id`. The
shared registry revalidates the active company owner and same-tenant basis at admission and
execution. Its child transaction uses REPEATABLE READ and calls the shared captured-report
builder; retries reuse the verified generation. The result contains one opaque
`cost_generation` reference and a generation count, never amounts. The job does not retain
a new census/basis, publish the generation, activate a schedule or grant financial approval.
The current ten-subject report bound remains unchanged. CAS publication stays a separate
READ COMMITTED operation; larger-company chunking requires a separately reviewed design.

`costing.captured_report.publish` is the separate owner-authorized READ COMMITTED step.
Its strict configuration names one sealed `generation_id` and nullable
`expected_previous_id`. It calls the shared tenant-serialized CAS service, so an obsolete,
ambiguous or stale queued request fails without changing the pointer; same-generation retry
is unchanged. The result reports only whether the pointer changed plus the opaque generation
reference. It neither builds a cache nor changes financial eligibility.
