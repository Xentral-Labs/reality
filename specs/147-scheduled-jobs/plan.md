# Implementation Plan: Shared Scheduled Jobs

**Branch**: Existing working branch retained; Spec Kit feature context is `147-scheduled-jobs`.
**Date**: 2026-09-09 | **Spec**: [spec.md](spec.md)
**Language**: English.
**Status**: Specification approved by the product owner on 2026-09-09, including separate `apps/scheduler/` and `apps/worker/` deployments. Architecture/schema review recorded in review.md; runtime and additive migration implemented. Local verification is recorded in quickstart.md; no live rollout.

## Summary

Create separate deployable scheduler and worker apps, with pure timing, named job registrations, tenant-scoped PostgreSQL schedules/runs and a bounded runner in the shared core. Scheduler materializes queued runs; worker consumes them independently. Both support continuous and one-shot modes through the same services. Use an opt-in tenant-scoped invitation-retention cleanup as the first real cron consumer. Demo generation remains in spec 146. Publish a single durable developer contract and link it from all discovery/deployment entry points.

## Technical Context

**Language/Version**: Python 3.12+. No frontend code change.
**Primary Dependencies**: Existing SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, Typer; add a tested bounded croniter version solely for calendar calculation.
**Storage**: Two tenant-scoped infrastructure tables; existing database, IDs and audit convention.
**Testing**: pytest unit/service/real PostgreSQL concurrency, subprocess lifecycle and CLI/container contract checks.
**Project Type**: `apps/scheduler/` and `apps/worker/` Docker packaging, shared-core implementation.
**Constraints**: UTC, opaque IDs, no direct external I/O handlers, no startup migrations, no new broker.
**Scale/Scope**: Initially one child per worker, 100-tenant discovery pages, 100-row cleanup batch, five-second poll; design for safe overlap rather than claiming arbitrary throughput.

## Constitution Check

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Scheduler is infrastructure; future intake uses normal source service with the supplied transaction, no direct operational writes | PASS |
| Reality owns operational state | Run outcome is execution status only; no document or business-state columns | PASS |
| Proven schema only | data-model.md maps every proposed field/index to timing, scope, retries or status requirements; additive schema reviewed in review.md | PASS |
| Tenant + shared service boundaries | Catalog-only trusted discovery; every claim/business/read/control scoped to tenant and current actor; handlers invoke services | PASS |
| Spec/test traceability | All 17 FR/DR map to stories, test categories and tasks; tests before implementation | PASS |
| Explainable web behavior | No new UI or generic web/agent control; result references preserve traceability for consuming features | PASS |
| Received values not recomputed | No commercial calculations; scheduling/run time distinct from source business time | PASS |
| Smallest coherent design | Explicit owner-selected scheduler/worker split + existing PostgreSQL, two infrastructure tables; no broker, heartbeat table, generic workflow or email-delivery migration | PASS |

Gate evaluated before and after design. PASS means design conformity, not approval to apply the proposed migration. T001/T002 review evidence is recorded in review.md. No constitutional exception is requested.

## Repository Structure and Layer Changes

```text
apps/scheduler/Dockerfile                      # scheduling image
apps/scheduler/README.md                       # links to canonical contracts
apps/worker/Dockerfile                         # worker image
apps/worker/README.md                          # app entry, links to canonical docs
packages/reality-core/src/reality/
  scheduling/__init__.py
  scheduler/__init__.py
  scheduler/cli.py                             # schedule process/control adapter
  scheduling/timing.py                        # pure interval/cron rules
  jobs/__init__.py
  jobs/registry.py                            # typed definitions/context/results
  jobs/runner.py                              # bounded child lifecycle
  jobs/handlers/__init__.py
  jobs/handlers/invitations.py                 # cleanup registration delegates service
  db/scheduled_jobs.py                        # schedule/run models
  db/core.py                                  # model registration for metadata only
  services/scheduled_jobs.py                   # controls/materialization/claims/status
  services/notifications.py                    # scope/bound existing cleanup
  worker/__init__.py
  worker/cli.py                               # dedicated Typer executable; no CLI boot
packages/reality-core/migrations/versions/<new_revision>_scheduled_jobs.py
packages/reality-core/pyproject.toml             # executable + tested croniter bound
compose.yml, compose.dev.yml                    # optional scheduler/worker services/profile
```

The exact migration revision is allocated from the actual head during implementation; do not preclaim it in documentation. `scheduling` and `jobs` are pure/runtime responsibilities in the shared core; transport code never owns their business policy. No production implementation code is placed in either `apps/scheduler/` or `apps/worker/`.

## Design

### Reality flow

A schedule creates a run (infrastructure). The cleanup handler calls the existing retention service; it does not create source/evidence. Future demo handler: run identity → synthetic upstream payload → shared atomic SourceRecord/ImportJob intake → existing interpretation → evidence/reality. The scheduler never constructs a Commitment or marks a proposal approved.

### Service and adapter flow

Registered job definition → disabled schedule through service → explicit control → scheduler tenant discovery → scoped due materialization → pending run; independent worker discovery → scoped claim → bounded child → scoped handler and effect/success transaction. CLI/continuous/cron share these services. Use dedicated `reality-scheduler` and `reality-worker` executables because the current general CLI unconditionally calls `init_db()` (Alembic). Never import that CLI's app or use its callback for startup.

The canonical signatures, command names and exit behavior are [contracts/worker.md](contracts/worker.md). Developer example and ownership are in [the durable contract](../../docs/features/scheduled-jobs.md), deploy modes in [the runbook](../../docs/WORKER_DEPLOYMENT.md). Avoid duplicating those defaults elsewhere in code docs.

### Data and migration impact

Implement [data-model.md](data-model.md): schedule plus run table; composite tenant FK, unique create/manual keys and scheduled occurrence, partial unique unfinished run, tenant-leading due/status indexes. Snapshot definition version in frozen run input envelope. Existing SecurityAuditEvent records control intent. Keep V1 run identity/history; no destructive purge or new audit store.

Migration is additive and creates no active schedules. Correct the cleanup function to require tenant_id and limit<=100 and maintain its 90-day cutoff. Do not touch invitation provider dispatch or its separate commit/retry loop.

### Failure, security, and tenant behavior

Scheduler inserts pending run and advances timing atomically without executing it; worker separately assigns a claim token in a short transaction; child obtains schedule/run locks in that order, checks current token/lease/actor/tenant, runs transaction-bound work and commits effect plus success together. No inherited database sessions across processes. A parent records failure only with matching token. Read committed state after uncertain completion before deciding retry; unresolved state suspends schedule. Pauses stop new dispatch, not committed or handed-off effects.

The runner is initially database-only: no arbitrary external-I/O callbacks, no handlers that commit internally. Future connectors enqueue durable intake/outbox work or add a separately reviewed effect contract. Fixed attempt/timeout/backoff limits and signal termination are in the durable contract. Tenant discovery is catalog-only with bounded pages; subsequent access is always scoped. Independent continuous cursor rotation avoids constant first-page preference. Global one-shot completion over large catalogs is not promised; use scoped tick or continuous worker.

## Test Strategy and Traceability

The following proofs are implemented; initial missing-module/entrypoint and behavior failures were observed before corresponding code. Verification results are recorded in quickstart.md.

| Requirements | Test level | Path and proof |
|---|---|---|
| FR-001, FR-013 | unit/contract | `packages/reality-core/tests/test_scheduled_job_registry.py`: allowlist, schema, duplicate, executable docs example |
| FR-002, FR-005 | unit/service | `packages/reality-core/tests/test_scheduled_job_timing.py`: interval grid, numeric cron/OR/leap/impossible, coalesce, five-time preview |
| FR-003, FR-004, DR-002, DR-003 | service/boundary | `packages/reality-core/tests/test_scheduled_jobs.py`: explicit actor, tenant isolation, create/control retry, pause/edit/revoke, no agent/web-console escape |
| FR-006, FR-007, DR-001, DR-004 | PostgreSQL/concurrency | `packages/reality-core/tests/test_scheduled_job_recovery.py`: dual materialization/claim, crash/commit, stale token, stable run/input, atomic effect, safe errors and audit times |
| FR-008, FR-009 | process/CLI | `packages/reality-core/tests/test_scheduled_worker.py`: shutdown/kill, bounded child, fresh connections, mode/manual parity, cursor progress, separate scheduler tick/worker once bounds and stop-one-role independence |
| FR-010 | service/CLI | `packages/reality-core/tests/test_scheduled_jobs.py`: bounded pages/read-only SQL, safe status/logs |
| FR-011, DR-002 | business story | `packages/reality-core/tests/test_scheduled_invitation_cleanup.py`: 90-day boundary, terminal/nonterminal, second tenant, 100-row batches and no sender |
| FR-012, FR-013 | adapter/docs | `packages/reality-core/tests/test_scheduled_worker_deployment.py`: startup/help never migrate, Docker CMD override/no port, docs CLI/registration links |
| FR-003, FR-004, FR-006, DR-002 | migration | `packages/reality-core/tests/test_scheduled_job_migration.py`: upgrade/downgrade on disposable DB, composite FK/unique checks, no auto-activation |

Run targeted tests then complete `make lint`, `make test`, `make spec-check`, migration roundtrip and both container smoke tests. Repository release gates also include `make site-build`, `make web-build`, `make docs-build` and web i18n audit. Frontend behavior is unchanged; no new browser behavior tests are required for this backend feature. Record failures accurately rather than checking tasks complete.

## Rollout and Rollback

Release migration once; build API, scheduler and worker from compatible core revision; deploy both processes only after successful migration. Start with one replica of each and no enabled schedule. Opt-in one disposable tenant cleanup schedule, then verify run outcomes. Expose no public scheduler/worker domain or embedded cron daemon. Continuous scheduler plus worker for demo intervals; host cron may replace the scheduler loop only when its cadence suffices, and worker consumption remains required.

Stop scheduler and worker before code rollback; retain additive tables/runs. Unknown handler/version pauses affected schedules with clear diagnostics. Do not downgrade production schema or delete history automatically. Leave invitation delivery unchanged. Runtime code is implemented; no deployment was performed.

## Review Risks

- Expiring leases alone do not fence business effects; transaction-bound handler enforcement and crash tests are essential.
- Existing general CLI runs migrations; dedicated entrypoint must be independently proven.
- New schema field/index proof needs concrete architecture review before migration implementation.
- Bounded global ticks over many tenants are not an all-work completion guarantee.
- A cleanup batch may retain additional eligible rows until the next run; preserve retention policy and make its count visible.
- Docs must not imply spec 146's generator or any scheduler command exists before implementation.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
