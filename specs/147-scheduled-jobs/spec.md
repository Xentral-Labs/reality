# Feature Specification: Shared Scheduled Jobs

**Feature Branch**: Existing working branch retained; no branch created.
**Created**: 2026-09-09
**Status**: Approved by the product owner on 2026-09-09. Runtime implemented and architecture/schema review recorded in review.md; local verification is recorded in quickstart.md. No live deployment.
**Language**: English
**Input**: Specify a minimal portable scheduler where subsystems register jobs, supporting ordinary cron tasks and continuous demo arrivals, and document its use so future code changes reuse it.

## Context and Intent

### Problem

Subsystems need recurring work while users are offline. The repository already has a dedicated invitation-delivery loop, but no shared registration or durable scheduling contract. Adding separate timers to each subsystem would scatter recovery, tenant isolation and deployment behavior. The continuous Demo Data integration in spec 146 needs intervals shorter than host-provided cron may support.

### Scope

- Named, explicitly registered job types with validated configuration and one bounded unit of work.
- Durable tenant-scoped interval and UTC cron schedules, explicit activation/pause, run identity, retries, status and error history.
- Separate deployable `apps/scheduler/` and `apps/worker/` applications. Scheduler produces durable due jobs, continuously or once per host-cron invocation; worker consumes them independently. Both use the shared core and support bounded one-shot operation.
- A minimal real reference consumer for existing invitation-retention cleanup; no change to retention meaning or invitation delivery.
- A durable developer recipe, command contract, deployment runbook and agent-discovery rule. Demo integration behavior remains in spec 146.

### Non-Goals

- Workflow graphs, distributed message brokers, arbitrary executable strings, user-uploaded jobs, calendar exceptions, local-time/DST schedules, or a scheduling UI.
- Rewriting invitation delivery, its provider retry policy or all existing background work.
- Implementing the demo generator, vendor polling, payments or operational automation as part of the scheduler foundation.
- Guaranteeing exactly-once external side effects or precise real-time execution. Direct external I/O inside handlers is deferred; the initial contract permits database-transaction work and durable intake enqueueing only.
- Deployment or running scheduled mutations in an existing environment during this specification work.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md), [workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md), [architecture](../../docs/ARCHITECTURE.md), [storage ADR](../../docs/decisions/0004-production-storage-and-projections.md).
- [CLI](../../docs/CLI_SPEC.md), [test strategy](../../docs/TEST_STRATEGY.md), [Railway deployment](../../docs/RAILWAY_DEMO.md).
- [Company setup and Demo Data integration](../146-company-setup-demo/spec.md).
- Existing invitation-retention service in `packages/reality-core/src/reality/services/notifications.py`; the new registration delegates to its same retention meaning through a bounded, tenant-scoped entry.

## User Scenarios & Testing

### User Story 1 - Register and schedule subsystem work (Priority: P1)

A developer registers one job type, and an authorized operator creates a disabled schedule, previews future times, then activates it without adding another timer or deployment per tenant.

**Why this priority**: This is the shared capability that subsequent subsystems need.

**Independent Test**: Register a reference handler, create an interval and a cron schedule for two tenants, activate one, advance a controlled clock and observe only the authorized due work.

**Acceptance Scenarios**:

1. **Given** a registered handler, **When** configured, **Then** its name, configuration schema, authorization policy, work bound, timeout and retry classification are discoverable; duplicate names, unknown types and invalid configurations fail before execution.
2. **Given** an interval or five-field UTC cron expression, **When** a schedule is created, **Then** it is disabled by default, has a stable technical identity and displays its next five hypothetical occurrences without performing work. Invalid or impossible schedules fail with a useful error.
3. **Given** explicit activation, **When** a due time is reached, **Then** work runs within the specified tenant and current authorization. Foreign schedule/run identities behave as not found; disabled or archived tenants and revoked authority cannot execute.
4. **Given** a pause, interval change, worker outage or restart, **When** scheduling resumes, **Then** pause adds no new work, changed schedules use future times, and missed occurrences collapse to at most one due occurrence rather than an unbounded catch-up burst. Resume starts from a fresh interval or the next future cron time.
5. **Given** cleanup of old terminal invitations is scheduled, **When** run, **Then** only eligible records in that tenant are processed within the batch bound; existing 90-day retention and non-terminal invitation preservation remain unchanged, and no email is sent.

### User Story 2 - Recover work without duplicate business effects (Priority: P1)

An operator can tolerate process restarts and overlapping workers without silently losing work or duplicating effects.

**Why this priority**: A timer is useful only if its failures have defined outcomes.

**Independent Test**: Use two real database sessions and process interruption at claim, effect and completion boundaries, then verify stable occurrence identity and truthful results.

**Acceptance Scenarios**:

1. **Given** two workers claim one due occurrence, **When** both proceed, **Then** only one current claim wins and one active occurrence exists per schedule; another schedule remains eligible.
2. **Given** a worker fails before completion, **When** its claim expires, **Then** retry retains the original run identity and frozen inputs. A stale worker cannot overwrite the newer claim's result, and the handler's idempotency mechanism prevents duplicate effects.
3. **Given** a retryable failure, **When** retried, **Then** attempts and bounded delays are visible; terminal failure disables automatic future occurrences until explicit reactivation. A non-retryable or uncertain external outcome is not blindly redispatched.
4. **Given** pause or revoked authorization during work, **When** the control takes effect, **Then** no new dispatch begins; already handed-off effects may finish and remain visible. Reauthorization is checked before a retry. Resume does not hide an unresolved old occurrence.
5. **Given** a slow/failing handler or shutdown signal, **When** the runner reaches its bound, **Then** it stops new claims, limits in-flight work and reports unfinished work for recovery without claiming successful completion or blocking other jobs indefinitely.

### User Story 3 - Operate the same jobs on Railway or another host (Priority: P1)

An operator deploys the same application image as a continuous worker or a command that finishes after bounded work, and can inspect failures without querying business tables directly.

**Why this priority**: Hosting portability and simple cron operation are explicit user goals.

**Independent Test**: Run scheduler and worker as separate processes, then compare continuous, one-shot and manual enqueue/consume behavior and exit results.

**Acceptance Scenarios**:

1. **Given** continuous mode, **When** the browser is closed or API replicas change, **Then** job scheduling continues independently and requires no browser or API-process timer.
2. **Given** one-shot mode started by host cron, **When** its scheduling budget is reached or nothing is due, **Then** it exits, closes connections and reports enqueued counts without executing handlers. Worker consumption is separately required. Overlapping invocations use the same occurrence uniqueness rules. Five-minute polling does not promise twelve-second arrivals.
3. **Given** manual execution, **When** the same explicit request identity is submitted twice, **Then** one run is returned, with the same validation, authorization and effect semantics as scheduled execution. A manual invocation does not advance a recurring schedule.
4. **Given** status inspection, **When** schedules/runs are listed, **Then** bounded tenant-scoped results show enabled state, next due time, attempts, last outcome, safe error and handler-provided reference. Run success does not imply successful downstream interpretation or fulfillment.
5. **Given** missing database, unknown handler in an older deployment or process failure, **When** operated, **Then** failures are explicit, existing state is preserved and unrelated valid jobs remain usable where possible. A live readiness check does not stand in for business acceptance.

### User Story 4 - Discover and reuse the scheduler in future changes (Priority: P2)

A future contributor can find the scheduling contract from AGENTS.md and implement one conforming subsystem without copying orchestration rules.

**Why this priority**: Registration must remain usable and discoverable beyond the first consumer.

**Independent Test**: Follow the documented example using only linked repository files; compare the example to the registry and CLI contract tests.

**Acceptance Scenarios**:

1. **Given** a recurring-work task, **When** the contributor reads AGENTS.md, **Then** it points to the durable developer contract and states that runtime availability must be checked before use.
2. **Given** the developer recipe, **When** followed, **Then** it covers registration, validated parameters, tenant/actor context, schedule lifecycle, idempotency, tests, and one real bounded reference handler.
3. **Given** deployment instructions and spec 146, **When** read together, **Then** the scheduler is the shared timing owner, the subsystem owns its business policy, and planned versus implemented capabilities and host limitations are explicit.

### Edge Cases

- UTC boundaries, leap days, impossible cron dates, both day-of-month and weekday restrictions, and intervals shorter than host polling frequency.
- Duplicate schedule creation, manual retry with changed input, configuration edits while a run is pending, and unknown handler after downgrade.
- Lost claim/completion responses, expired claims with old processes still alive, provider timeout with unknown outcome, and pause with an in-flight effect.
- Tenant archive, actor removal, disabled demo source, and worker credentials that must not authorize new business actions.
- Full status page, large tenant catalog, empty queue, database outage, resource exhaustion and interruption during cleanup.

## Requirements

### Functional Requirements

- **FR-001**: Job types MUST be explicitly registered by stable name with validated configuration, authorization, bounded handler behavior and declared retry/idempotency semantics; arbitrary callable or shell strings MUST be rejected.
- **FR-002**: Schedules MUST support either a positive whole-second interval of at least five seconds or five-field UTC cron, with next-occurrence preview, strict validation and disabled initial state.
- **FR-003**: Schedule creation/control and execution MUST require explicit tenant and authorized actor context. The trusted worker may dispatch already authorized work but MUST NOT create its own business authority. Current tenant and handler-specific permissions MUST be checked on every attempt.
- **FR-004**: Create/update/pause/resume MUST be durable and idempotent for the same request. Only one unfinished occurrence per schedule is permitted. Configuration changes require no unresolved occurrence and apply prospectively; pause freezes undispatched retry work, and reactivation explicitly resumes it before new occurrences. The explicitly approved spec 146 `cancel_queued_run` control separately pauses and cancels only pending/retry occurrences, retaining their history; running or unresolved work is refused.
- **FR-005**: Missed times MUST coalesce into at most one occurrence; subsequent times are future times. No backlog of every missed interval is created. A resumed schedule with no unfinished run starts at a future time.
- **FR-006**: Claims MUST be exclusive for a current attempt, expire after bounded time and fence stale completion. Recovery MUST preserve stable run identity and frozen configuration; duplicate effects require handler/service idempotency, not an exactly-once claim.
- **FR-007**: Retryable failures MUST have bounded attempts and backoff. Unknown effects MUST require reconciliation or manual review; terminal or unknown outcomes suspend the schedule and cannot be hidden by new occurrences. Safe diagnostic history MUST remain available.
- **FR-008**: The scheduler and runner MUST bound work, queue size, concurrency and execution time (at most 1,000 unfinished runs per tenant and one unfinished occurrence per schedule). Queue saturation MUST defer visibly without losing due work. The runner MUST stop new claims on shutdown, and isolate job failures. Pauses/revocations prevent new dispatch but do not promise rollback of in-flight external effects.
- **FR-009**: Scheduler and worker MUST be independently deployable processes sharing application services and durable state. Scheduler work/tick only materialize due jobs; worker work/once only consume pending/retry jobs. Manual execution MUST enqueue using an explicit request identity without changing recurring schedules. Timed work requires both roles; host cron can replace the scheduler loop, not the worker.
- **FR-010**: Tenant-scoped status MUST be read-only and bounded, showing schedule state, next time, run/attempt identity, safe errors and result references. Logs MUST not expose tokens, source payloads or secrets.
- **FR-011**: A registered invitation-retention cleanup job MUST reuse the existing 90-day retention semantics, process a bounded tenant-scoped batch and preserve unrelated/non-terminal records. Activation remains explicit; the existing delivery worker remains unchanged.
- **FR-012**: Dedicated scheduler and worker applications/images built from the same shared core MUST support portable continuous and host-cron deployment, with documented startup, shutdown, configuration, migrations, health/exit interpretation and recovery. Neither process startup nor help/status commands may run migrations; migration ownership remains the release task. Railway's cron granularity MUST not be confused with the application's interval support.
- **FR-013**: AGENTS.md, architecture, CLI, developer and deployment docs MUST link a single durable contract, include one usable example, and identify current implementation status. Spec 146 MUST depend on this scheduler for timing without duplicating its mechanics.

### Domain and Traceability Requirements

- **DR-001**: Schedules and runs are execution infrastructure, not business truth. Handlers call shared services; generated source data retains Source → Evidence → Reality and lossless payloads. No document operational status or new source authority is introduced.
- **DR-002**: All schedule/run and handler business queries MUST enforce tenant scope, with opaque identities and same-tenant links. Cross-tenant enumeration is limited to the trusted dispatcher reading the tenant catalog before scoped job access.
- **DR-003**: Starting scheduled intake authorizes only its stated recurring scope; no job auto-confirms business proposals. Any future Chat control requires normal preview and confirmation. This increment exposes no generic scheduling mutation in Chat/MCP or the web CLI console.
- **DR-004**: UTC scheduling timestamps and execution audit MUST remain distinct from source business dates. Run results reference authoritative outcomes and MUST NOT store recomputed commercial values as authority.

### Key Entities

- **Job definition**: A named registered capability and its configuration, permission and retry contract.
- **Schedule**: Tenant-owned future timing and explicit authorization of a registered capability.
- **Run**: One durable logical occurrence, with frozen intent, recoverable attempts and safe result identity.
- **Tenant and actor**: Existing ownership and permission context, revalidated before dispatch.

## Success Criteria

- **SC-001**: Under a controlled healthy clock, ten twelve-second intervals yield ten distinct due occurrences; two concurrent workers add no duplicate business effect.
- **SC-002**: After an hour-long outage or pause, recovery creates at most one coalesced occurrence, then a future due time; no sixty-occurrence burst is created for a one-minute interval.
- **SC-003**: All crash-boundary, stale-claim, duplicate-request and foreign-tenant acceptance cases produce no unauthorized or duplicate committed effect; uncertain external effects are explicitly unresolved.
- **SC-004**: Scheduler tick terminates within its 30-second bound and worker once within its 60-second bound under healthy host/database response. Independent continuous processes operate with the browser closed using the same records and handler semantics.
- **SC-005**: The reference cleanup removes only eligible terminal records in its selected tenant and does not send mail or change the existing retention interval.
- **SC-006**: Every FR/DR maps to an acceptance scenario, test and implementation/documentation task; the developer example and documented CLI match executable contract checks before runtime completion is claimed.

## Assumptions and Dependencies

- The product owner explicitly approved this specification on 2026-09-09 after reviewing the design package and choosing separate scheduler and worker apps. This records acceptance of the specified scope and requirements. Runtime implementation, concrete architecture/schema review and deployment are not reported complete by this approval.
- Defaults are intentionally bounded: intervals plus standard five-field UTC cron, coalescing after downtime, serialized work per schedule, and code registration only. Platform-global jobs are deferred; all first-increment work has a tenant.
- PostgreSQL and existing service/CLI patterns are reused. The owner explicitly chose separate `apps/scheduler/` and `apps/worker/` deployments, named `scheduler` and `worker`. Dedicated `reality-scheduler` and `reality-worker` entrypoints avoid the existing general CLI bootstrap, which invokes migrations. The proposed two infrastructure entities require field-level review before implementation.
- Invitation retention is the reference cron consumer because it already exists; adding its schedule is opt-in and does not authorize deleting existing records during this task.
- The future demo handler remains owned by spec 146. It schedules one arrival per interval, validates active Sandbox/source authorization and preserves its source/run identity and separate Atlas execution isolation.
- Production scope is small bounded jobs. Long-running jobs must split into idempotent batches; a general parallel task queue is deferred.

## Open Questions

No unresolved product-scope clarification. Specification approval is recorded below. Architecture/schema and reliability assessment are recorded in review.md; there are no unresolved implementation clarifications. Deployment approval is not implied.

## Approval Record

- **Reviewer**: Benedikt Sauter, product owner.
- **Date**: 2026-09-09.
- **Decision**: Specification approved through explicit user confirmation.
- **Scope**: Shared scheduled jobs, separate `apps/scheduler/` and `apps/worker/`, PostgreSQL queue, registered bounded handlers, cron/interval operation and the documented developer/deployment contracts.
- **Implementation follow-through**: Architecture/schema and reliability review are recorded in review.md; execute and verify the existing test-first tasks. Product-scope approval must not be requested again unless scope changes.

## Requirement Traceability

| Requirement | Scenario(s) | Test/evidence |
|---|---|---|
| FR-001 | US1-1, US4-2 | Registry/parameter contract tests |
| FR-002, FR-005 | US1-2/4 | Clock, cron grammar, coalescing and preview unit/service tests |
| FR-003, DR-002 | US1-3, US2-4 | Tenant/actor isolation and revocation tests |
| FR-004 | US1-2/4, US2-4 | Idempotent lifecycle and frozen-configuration tests |
| FR-006 | US2-1/2 | Real PostgreSQL concurrency/crash/fencing proofs |
| FR-007 | US2-2/3/4 | Retry, terminal suspension and unknown-outcome reconciliation tests |
| FR-008 | US2-5, US3-5 | Timeout, fairness, interruption and bounded-work tests |
| FR-009 | US3-1/2/3 | CLI mode parity and explicit manual-request tests |
| FR-010 | US3-4/5 | Read-only pagination and redacted log tests |
| FR-011 | US1-5 | Existing retention regression plus bounded tenant cleanup story |
| FR-012 | US3-1/2/5 | Container/start/exit and deployment configuration checks |
| FR-013 | US4-1/2/3 | Documentation/example/registration drift checks |
| DR-001, DR-004 | US2-2, US3-4, US4-2 | Shared-service effect, source identity and audit-time assertions |
| DR-003 | US1-3, US4-3 | Command exposure and no auto-confirmation boundary tests |
