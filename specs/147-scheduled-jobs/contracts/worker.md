# Worker Interfaces

**Status**: Implemented; see quickstart.md for local verification. The dedicated executable supersedes the conversational sketch `reality scheduler ...` and avoids its existing migration-running CLI bootstrap.

## Registered definition

Module: `reality.jobs.registry`.

- `JobDefinition(name, version, config_model, authorize, handler)`; immutable code registration, no dynamic imports.
- `authorize(session, context, validated_config) -> None`; reuses existing tenant/membership/resource checks and raises a safe permanent refusal.
- `handler(session, context, validated_config) -> JobResult`; transaction-bound database work only, max 30s, no commit or network effects.
- `JobContext`: tenant_id, actor_id, run_id, scheduled_for (optional for manual), UTC deadline. The service passes validated context, never arbitrary caller-supplied authorization claims.
- `JobResult`: string-to-integer safe counts and optional list of typed opaque record references; total serialized size <=4 KiB.
- Configuration: Pydantic model, extra keys forbidden, <=16 KiB JSON, no embedded secrets. Store registered definition version in the frozen run configuration envelope; an unsupported version is a permanent refusal.
- Errors: transient database/lock/connect failures may retry; validation/permission/unknown type does not. Unexpected failure is safe-classified; retry only after proving no committed effect. Never use exception strings as public logs.

## Service boundary

`reality.services.scheduled_jobs` exports typed services:

- create_schedule(tenant_id, actor_id, job_type, config, interval_seconds OR cron, request_id): disabled schedule and revision.
- preview_schedule(tenant_id, actor_id, schedule_id): five hypothetical future UTC times, no write.
- control_schedule(tenant_id, actor_id, schedule_id, action, expected_revision, request_id, changes): resume/pause/update with compare-and-set control semantics.
- create_manual_run(tenant_id, actor_id, job_type, config, request_id): stable queued run identity, no alteration of schedules; CLI returns pending/current state and worker consumption is separate.
- materialize_due(tenant_id): scheduler-only transaction creates bounded pending runs and advances due times under schedule locks and unique occurrence constraints.
- claim_next(tenant_id): worker-only claim of one pending/retry or expired run after policy checks, assigning token; never calculate new occurrences.
- execute_claim(tenant_id, run_id, claim_token): fresh child session, fenced transaction including effect and success.
- record_failure/reconcile: token-checked administrative outcome; no forced-success API. Reconciliation may only mark successful by retained success evidence or retryable after proven non-execution; initial transaction-bound jobs normally settle by reading committed run state after process exit.
- list_schedules/list_runs: explicit tenant and actor, cursor pagination, limit default 50/max 200. Return next_cursor and has_more, stable `(created_at,id)` order and observation time; matching retained rows only, no snapshot promise under concurrent changes.

Request IDs are opaque caller keys, not human job names. Same request/different input conflicts. Schedule creation and manual runs retain unique keys. Controls use expected revision and latest request fingerprint; late replay either returns the already applied latest result or fails stale without effect. Actor context cannot default to the first available tenant. No new generic agent tool is exposed.

## CLI

Entrypoints in `packages/reality-core/pyproject.toml`:
`reality-scheduler = reality.scheduler.cli:app` and
`reality-worker = reality.worker.cli:app`.

All `jobs run` and `schedules` control/read commands require `--tenant TENANT_ID --actor ACTOR_ID`, except global `jobs list` (code metadata only). This is trusted operator access, like the existing local CLI; it is not an HTTP impersonation mechanism. The service validates current membership. Scheduler `work`/`tick` and worker `work`/`once` use trusted deployment credentials and never accept caller-supplied shell/callable input.

| Command | Meaning |
|---|---|
| `reality-scheduler work --poll-seconds 5` | Continuous due-job materialization; optional `--tenant` |
| `reality-scheduler tick --max-runs 100 --max-seconds 25` | Materialize bounded pending jobs then exit; optional `--tenant`; no handler execution |
| `reality-worker work --poll-seconds 5` | Consume pending/retry work continuously; optional `--tenant` |
| `reality-worker once --max-runs 10 --max-seconds 25` | Consume one bounded batch, optional `--tenant`, then exit |
| `reality-worker jobs list` | Registered type/schema/version and bounds; read-only |
| `reality-worker jobs run TYPE --tenant ID --actor ID --config-json '{}' --request-id KEY` | Enqueue one idempotent manual run; worker consumes it separately |
| `reality-scheduler schedules create TYPE --tenant ID --actor ID --config-json '{}' --cron '0 3 * * *' --request-id KEY` | Disabled schedule; `--every-seconds 12` is mutually exclusive with cron |
| `reality-scheduler schedules preview SCHEDULE_ID --tenant ID --actor ID` | Read-only next five hypothetical times |
| `reality-scheduler schedules resume SCHEDULE_ID --tenant ID --actor ID --revision N --request-id KEY` | Explicit enable/re-enable |
| `reality-scheduler schedules pause SCHEDULE_ID --tenant ID --actor ID --revision N --request-id KEY` | Block new dispatch; retain in-flight/history |
| `reality-scheduler schedules update SCHEDULE_ID --tenant ID --actor ID --revision N --request-id KEY ...` | Validated future configuration/timing/actor changes; refuse unfinished run |
| `reality-scheduler schedules list --tenant ID --actor ID --limit 50 --cursor TOKEN` | Bounded status |
| `reality-worker runs list --tenant ID --actor ID --limit 50 --cursor TOKEN` | Bounded run history; optional `--schedule ID` |
| `reality-worker runs show RUN_ID --tenant ID --actor ID` | Frozen scope, attempts, safe outcome and references |

All commands support `--json` for stable structured output. Work limits may be lowered but not raised above V1 bounds without reviewed configuration changes; poll minimum 1s, default 5s, no claim of real-time execution. Work shuts down on SIGTERM/SIGINT and does not spawn new children after signal receipt.

Exit codes: 0 completed invocation (including no work or recorded retry); 1 infrastructure/unsettled execution failure or a newly terminal/unresolved run; 2 invalid command/configuration/authorization. Recorded retry is visible in JSON and run history, not hidden as success. Continuous work logs individual job failure and continues; infrastructure failure uses bounded backoff and exits 1 after three consecutive failed sweeps. Jobs list/help do not connect or mutate; status/work/tick/once may validate schema but never migrate.

Scheduler tick reports materialized/deferred counts and budget_exhausted; worker once reports processed/succeeded/retry/failed/unresolved counts and budget_exhausted. A bounded successful invocation can leave more due work; process exit zero does not certify all jobs complete. Host restart policy must not blindly replay manual requests with fresh keys. Refer to the deployment runbook for polling limits and timeout interpretation.

Scheduler tick never forks handler children and exits within 30s; worker once retains the 60s bound. Work log heartbeat names identify the role (`scheduler_sweep`, `worker_sweep`). Both help commands are database-free; startup schema checks never migrate. Manual enqueue reports its durable run identity and current status, never claims completion unless the run is already succeeded from a previous request.


## Approved queued cancellation extension (spec 146)

`cancel_queued_run(session, tenant_id, actor_id, schedule_id, expected_revision, request_id)` locks the scoped schedule before its unfinished occurrence, validates current owner/revision, disables timing and marks only pending/retry work cancelled. It retains the occurrence and audit; a repeated identical control is idempotent. Running and unresolved occurrences return `unfinished_run` before changing state. Ordinary pause behavior remains unchanged. Demo Data uses this control for future-only pause/resume and rate changes.

The worker commit guard permits SAVEPOINT release but refuses root `session.commit()`, including a handler attempting to commit from inside a savepoint. This allows bounded shared interpretation while preserving atomic business effects plus run completion.
