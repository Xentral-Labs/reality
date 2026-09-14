# Data Model: Shared Scheduled Jobs

**Status**: Implemented in migration `0045_scheduled_jobs`; architecture/schema review is recorded in review.md. All timestamps use UTC, IDs use existing opaque-ID conventions. No business entity changes.

## scheduled_job

| Fields | Proven use / requirement |
|---|---|
| id, tenant_id | Scope and opaque target for controls/claims; FR-003, DR-002 |
| job_type, configuration (JSON) | Select allowlisted handler and validate its declared parameters; FR-001 |
| actor_id | Recheck current initiating actor's membership/policy on each attempt; FR-003 |
| interval_seconds OR cron_expression | Calculate future times; exactly one present; FR-002 |
| enabled, next_run_at | Select due work and pause/suspend; FR-004/005 |
| revision | Reject stale control/configuration updates; FR-004 |
| create_request_id, create_fingerprint | Retry-safe creation; same key/different input conflicts; FR-004 |
| last_control_request_id, last_control_fingerprint | Replay latest control without applying twice; older requests fail expected-revision check; FR-004 |
| created_at, updated_at | Administrative timing, not business dates; DR-004 |

Unique `(tenant_id, id)` and `(tenant_id, create_request_id)`. Index `(tenant_id, enabled, next_run_at, id)`. Validate interval >=5, numeric five-field cron, immutable tenant, registered type and configured argument schema. Actor references the existing account; authority is checked via current tenant membership, not inferred from the FK. No automatic schedule creation in migration.

Creation starts disabled with next_run_at null. Preview calculates hypothetical times. Resume sets next_run_at strictly after current time, unless an unfinished run must resume first. Scheduler materialization records the prior due instant and advances next_run_at to the first future time; interval coalescing advances directly by arithmetic, not one loop per missed interval. While a run is unfinished, later occurrences are not created.

A terminal failure or unresolved run sets enabled=false. It remains visible through the newest run; no duplicated failure field is needed on the schedule. Re-enable after terminal failure explicitly acknowledges that occurrence; future work starts after now. An unresolved occurrence must be reconciled first. Pause does not delete run state.

## scheduled_job_run

| Fields | Proven use / requirement |
|---|---|
| id, tenant_id, schedule_id nullable | Stable occurrence/retry identity; manual runs have no schedule; FR-006/009 |
| actor_id, job_type, configuration (JSON), schedule_revision nullable | Immutable invocation snapshot; necessary because schedules can later change or manual runs have none; FR-004/006 |
| scheduled_for nullable | Identify one recurring occurrence, never actual business time; FR-005 |
| request_id nullable, request_fingerprint nullable | Idempotency of explicit manual requests; FR-009 |
| status | pending, running, retry, succeeded, failed, unresolved, cancelled; recovery/inspection; FR-007/010 |
| attempt_count, next_attempt_at | Bounded retries; FR-007 |
| claim_token nullable, lease_expires_at nullable | Ownership/fencing and crash recovery; FR-006 |
| created_at, started_at nullable, finished_at nullable | Execution observability; FR-010 |
| last_error_code nullable, result (bounded JSON) nullable | Safe classification and outcome reference/count only; FR-010, DR-004 |

Same-tenant composite FK `(tenant_id, schedule_id)` to schedule. Unique scheduled occurrence `(tenant_id, schedule_id, scheduled_for)` for scheduled runs, unique `(tenant_id, request_id)` for manual runs. Check that schedule_id/scheduled_for/schedule_revision occur together, or request_id/fingerprint for manual mode. Partial unique index `(tenant_id, schedule_id)` for pending/running/retry/unresolved prevents two unfinished occurrences. Tenant-leading due/retry and `(tenant_id, created_at, id)` indexes support bounded claim/status reads.

Only scheduling intent is snapshotted; no source/evidence ancestor keys or business quantities are copied. Result JSON is capped at 4 KiB and restricted to safe counters and typed record references; never raw payloads/credentials. Configuration is capped at 16 KiB, cannot embed secrets, and refers to scoped integration identities when needed.

## Transitions and transactions

1. Scheduler locks the due schedule, verifies no unfinished occurrence and the pending-queue bound, inserts one pending run with frozen intent, and advances next_run_at atomically. It does not assign a claim token or attempt. Worker separately locks schedule/run in that order, claims a pending/retry run or reclaims an expired attempt, assigns a fresh token, increments attempt count and commits before child execution. Never claim a whole batch whose leases would age before execution. Uniqueness constraints protect overlapping scheduler replicas; token fencing protects worker replicas.
2. Child opens a fresh session, locks schedule then run, validates token/lease, enabled state, tenant/actor and handler policy. Manual runs lock only their run. It calls a handler that does not commit and performs no external I/O.
3. Handler database writes or durable intake enqueueing and `succeeded` are committed together, provided token/lease still match before commit. Database transaction/statement bounds prevent an old child holding locks forever. All business services receive the same tenant and transaction.
4. On retryable rollback, parent records retry only if its token is current. Wait 30s then 120s; third failed attempt becomes failed and suspends schedule. Permanent invalid configuration, unknown type or revoked authority fails without repeated attempts. Revocation never hands work to a new actor implicitly.
5. If completion is uncertain, read run state using a fresh connection. A committed success is returned; never replay it. A dead child with rolled-back database work can retry after lease expiration. If process/transaction outcome cannot be established, retain unresolved and suspend until operator reconciliation; record only proven success/non-execution. No "force succeeded" command.
6. Pause blocks new claims/retries. It may wait for a bounded in-flight transaction; acknowledgment does not promise cancellation of prior handoff. Resume retries the frozen occurrence with remaining attempt budget before new times. Configuration/actor changes require no unfinished occurrence. Lock-order tests cover concurrent controls.

At most one active scheduled occurrence does not serialize separately requested manual runs; handlers must also preserve their own domain concurrency invariants.

## Retention, audit and migration

Retain schedule/run identity and outcome in V1; bounded reads do not imply bounded lifetime storage. Do not purge idempotency keys and accidentally permit replay. Future compaction needs an explicit retention/tombstone contract. Use existing SecurityAuditEvent for schedule create/control and operator reconciliation, with tenant, actor, action and opaque IDs, never secret configuration. Attempt counters and redacted process logs suffice; no third generic event store.

Additive migration creates two tables/indexes/checks only. Test upgrade from the current Alembic head, tenant-FK rejection and downgrade in a disposable database. Production rollback stops workers and keeps additive tables/history; dropping them is destructive and not automatic. No existing business data backfill or default activation.

## Queue bounds and role separation

At most 1,000 unfinished runs per tenant, including manual runs, and one unfinished scheduled occurrence per schedule. Scheduler and manual-enqueue service serialize queue-cap checks through the tenant row before schedule/run locks; worker never acquires tenant after schedule/run. At the cap, materialization defers visibly without advancing due time or losing the occurrence. Pending runs survive either process stopping. No schedule or handler payload is kept only in process memory. Scheduling saturation is distinct from failed execution.
