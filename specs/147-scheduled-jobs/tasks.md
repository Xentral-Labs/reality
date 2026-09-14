# Tasks: Shared Scheduled Jobs

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/worker.md and quickstart.md.
**Gate**: Product specification approved on 2026-09-09; design Constitution Check PASS. Reliability/architecture/schema review and pre-implementation analysis are recorded in review.md.
**Status**: All 32 tasks are complete with local verification and review recorded in quickstart.md and review.md. No live deployment. Task completion is based on executable evidence, not documentation alone.

## Format and execution

Each checkbox is an independently reviewable task with an exact path. Requirements appear in test and implementation/documentation tasks. Observe meaningful failing tests before their code. No new public web/Chat/MCP adapter is in scope.

## Phase 1: Specification and Design Gates

- [x] T001 Use the product-owner specification approval recorded on 2026-09-09; assess the reviewer-owned `specs/147-scheduled-jobs/checklists/reliability.md` against `specs/147-scheduled-jobs/spec.md` and record findings in review.md without changing its owner markers.
- [x] T002 Review field-level schema proof, transaction/fencing and timeout defaults in `specs/147-scheduled-jobs/data-model.md` and `specs/147-scheduled-jobs/plan.md`; record architecture/schema acceptance before creating a migration.
- [x] T003 Re-run Spec Kit analysis over `specs/147-scheduled-jobs/spec.md`, `plan.md` and `tasks.md` after any accepted revision; resolve all critical findings before implementation.

## Phase 2: Foundation and Failing Schema Proof

- [x] T004 [FR-003] [FR-004] [FR-006] [DR-002] Add failing PostgreSQL upgrade/downgrade, unique occurrence/manual key, unfinished-run and composite tenant-FK tests in `packages/reality-core/tests/test_scheduled_job_migration.py`.
- [x] T005 [FR-003] [FR-004] [FR-006] [DR-002] Add proposed schedule/run models in `packages/reality-core/src/reality/db/scheduled_jobs.py`, register metadata in `packages/reality-core/src/reality/db/core.py`, and allocate the next Alembic revision under `packages/reality-core/migrations/versions/` for additive constraints/indexes without backfill or automatic activation.

## Phase 3: User Story 1 — Register and Schedule (P1)

Independent acceptance: register cleanup, create a disabled interval/cron schedule, preview and activate for one tenant, then materialize exactly one due run without executing it.

- [x] T006 [P] [US1] [FR-001] Add failing registry, duplicate/unknown/version, extra-parameter and bounded-result/configuration tests in `packages/reality-core/tests/test_scheduled_job_registry.py`.
- [x] T007 [P] [US1] [FR-002] [FR-005] Add failing interval-grid, UTC cron grammar/OR/leap/impossible, five-occurrence preview, pause/resume and missed-time coalescing tests in `packages/reality-core/tests/test_scheduled_job_timing.py`.
- [x] T008 [US1] [FR-003] [FR-004] [FR-010] [DR-002] [DR-003] Add failing service tests for tenant/actor/revocation, create/control replay and stale revision, configuration freeze, scoped status/read-only pagination, queue cap and no generic agent/web-console exposure in `packages/reality-core/tests/test_scheduled_jobs.py`.
- [x] T009 [US1] [FR-011] [DR-002] Add failing retention-boundary, tenant-isolation, terminal/nonterminal, bounded-batch, repeated-cleanup and no-email tests in `packages/reality-core/tests/test_scheduled_invitation_cleanup.py`.
- [x] T010 [US1] [FR-001] Implement pure definition/context/result validation and explicit registry in `packages/reality-core/src/reality/jobs/registry.py`, including required owner-policy callback and no dynamically supplied callables.
- [x] T011 [US1] [FR-002] [FR-005] Implement pure timing in `packages/reality-core/src/reality/scheduling/timing.py`, add a tested croniter version bound to `packages/reality-core/pyproject.toml`, and record the dependency license in `docs/THIRD_PARTY_NOTICES.md`.
- [x] T012 [US1] [FR-002] [FR-003] [FR-004] [FR-005] [FR-010] [DR-002] [DR-003] Implement create/preview/update/pause/resume, manual enqueue, read-only list/show and scheduler materialization in `packages/reality-core/src/reality/services/scheduled_jobs.py`; enforce actor, tenant catalog-only discovery, queue bounds and atomic occurrence/future-time persistence. Keep services unexposed to generic web/agent tools.
- [x] T013 [US1] [FR-011] [DR-002] Add required tenant scope and <=100-row batch to existing cleanup in `packages/reality-core/src/reality/services/notifications.py`, and register `invitations.cleanup` in `packages/reality-core/src/reality/jobs/handlers/invitations.py`; preserve 90-day semantics and existing invitation delivery.
- [x] T014 [US1] Record US1 targeted acceptance results in `specs/147-scheduled-jobs/quickstart.md`; do not claim handler execution until the recovery/execution phase passes.

## Phase 4: User Story 2 — Recover and Bound Execution (P1)

Independent acceptance: two schedulers and two workers cannot duplicate a scheduled occurrence or committed database effect; crashes, stale claims and pause/retry retain truthful outcomes.

- [x] T015 [US2] [FR-006] [FR-007] [DR-001] [DR-004] Add failing real PostgreSQL dual-materialization/claim, crash-before/after-commit, stale-token, frozen-config/identity, retry-exhaustion, unresolved and atomic-effect tests in `packages/reality-core/tests/test_scheduled_job_recovery.py`.
- [x] T016 [US2] [FR-003] [FR-004] [FR-008] [DR-002] Add failing bounded child kill, signal, fresh-session, pause/revoke during execution, queue-cap, cursor fairness and unrelated-job failure-isolation tests in `packages/reality-core/tests/test_scheduled_worker.py`.
- [x] T017 [US2] [FR-006] [FR-007] [DR-001] [DR-004] Implement scoped claim/reclaim, fixed run snapshot/version, token-fenced completion/failure and evidence-based reconciliation in `packages/reality-core/src/reality/services/scheduled_jobs.py`; lock in documented order and commit handler effect plus success together.
- [x] T018 [US2] [FR-003] [FR-004] [FR-008] [DR-002] Implement bounded subprocess execution, fresh child sessions, deadline/statement/lock/connect limits, 30s/120s retry policy coordination and shutdown in `packages/reality-core/src/reality/jobs/runner.py`; reject direct network/independent-commit handlers by documented registration contract and dedicated handler review/tests.
- [x] T019 [US2] Record crash/concurrency acceptance and remaining uncertainty in `specs/147-scheduled-jobs/quickstart.md` before enabling a real scheduled handler.

## Phase 5: User Story 3 — Portable Separate Processes (P1)

Independent acceptance: scheduler tick creates pending work only; worker once consumes it only; each process survives the other being stopped, with no startup migrations.

- [x] T020 [US3] [FR-009] [FR-010] Add failing CLI continuous/tick/once/manual enqueue parity, stable request, explicit scope, exit-code, JSON status/redaction and stop-one-role tests in `packages/reality-core/tests/test_scheduled_worker.py` and `packages/reality-core/tests/test_scheduled_jobs.py`.
- [x] T021 [US3] [FR-012] Add failing migration-free bootstrap/help/schema-check and separate Docker command/port/configuration tests in `packages/reality-core/tests/test_scheduled_worker_deployment.py`.
- [x] T022 [US3] [FR-009] [FR-010] Implement separate thin Typer adapters in `packages/reality-core/src/reality/scheduler/cli.py` and `packages/reality-core/src/reality/worker/cli.py`, plus package initializers and both entrypoints in `packages/reality-core/pyproject.toml`. Do not import the general CLI bootstrap. Route every operation through shared services and log role-specific bounded sweeps.
- [x] T023 [US3] [FR-012] Add `apps/scheduler/Dockerfile` and `apps/worker/Dockerfile` installing the same core with distinct CMDs, no exposed HTTP port and no startup migrations; add opt-in `background` profile services to `compose.yml` and matching development configuration to `compose.dev.yml` without replacing `invitation-worker`.
- [x] T024 [US3] [FR-012] Validate both images and Compose configuration locally, recording continuous/one-shot/termination behavior in `specs/147-scheduled-jobs/quickstart.md`; follow `docs/WORKER_DEPLOYMENT.md` for a separately authorized live rollout, without automatically deploying it.

## Phase 6: User Story 4 — Durable Discovery and Usage (P2)

Independent acceptance: a contributor follows AGENTS.md to the single contract, registers the documented cleanup example and uses CLI examples that match the actual executable.

- [x] T025 [US4] [FR-001] [FR-013] Add an executable documentation example/registration contract test in `packages/reality-core/tests/test_scheduled_job_registry.py` and named command/default/role documentation checks in `packages/reality-core/tests/test_scheduled_worker_deployment.py`.
- [x] T026 [US4] [FR-013] Reconcile prepared `docs/features/scheduled-jobs.md`, `docs/WORKER_DEPLOYMENT.md`, `docs/decisions/0006-shared-scheduled-worker.md` and `specs/147-scheduled-jobs/contracts/worker.md` with verified implementation; finalize the prepared `apps/scheduler/README.md` and `apps/worker/README.md` links/status against those canonical contracts.
- [x] T027 [US4] [FR-013] Reconcile discovery links/status in `AGENTS.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/CLI_SPEC.md`, `docs/TEST_STRATEGY.md`, `docs/RAILWAY_DEMO.md` and `infra/README.md`; retain planned/deployed distinction and keep `specs/146-company-setup-demo/spec.md` dependent on this scheduler without implementing its generator here.

## Final Phase: Verification and Review

- [x] T028 Run spec/link/requirement coverage checks and Spec Kit analysis for `specs/147-scheduled-jobs/`; record the final findings and no-critical status in review evidence.
- [x] T029 Run `make lint` and the complete PostgreSQL `make test` suite from `Makefile`, including existing invitation-delivery regressions; record output in `specs/147-scheduled-jobs/quickstart.md`.
- [x] T030 Run disposable upgrade/downgrade, composite FK/idempotency constraints and both container smoke checks from `packages/reality-core/tests/test_scheduled_job_migration.py` and `packages/reality-core/tests/test_scheduled_worker_deployment.py`; verify non-destructive rollback guidance.
- [x] T031 Run `make spec-check`, `make site-build`, `make web-build`, `make docs-build` and the web i18n audit from repository `Makefile` / `apps/web/package.json`; record any required failures without marking completion.
- [x] T032 Review the diff against `specs/147-scheduled-jobs/spec.md`, its Constitution Check, and all FR/DR; update runtime status in canonical docs and `docs/V0_CHECKLIST.md` only after required checks and review are green. No automatic merge or deployment.

## Dependencies and Delivery Strategy

T001–T003 precede implementation; T004 precedes T005. US1 starts with tests T006–T009, then domain definitions/timing T010–T011, services T012 and handler T013. US2 follows US1 and completes effect safety before running jobs. US3 follows US2; adapter/deployment tests precede implementation. US4 can prepare docs independently but finalizes only after US3. Final verification follows every story.

MVP is US1 + US2 + the two minimal US3 executables with the opt-in cleanup consumer. Timing without fenced execution is not a production MVP. US4's discoverability is required before feature completion. Demo handler implementation remains spec 146 work.

Parallel opportunities: US1 test files T006 and T007 can be authored independently; US2 concurrency and process-test cases can be designed independently but share the final service contract; US3 packaging checks can be prepared alongside CLI tests; US4 link review can proceed alongside example-test preparation. These describe potential work organization, not authorization to bypass dependencies.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T006, T025 | T010 | Verified locally |
| FR-002 | T007 | T011, T012 | Verified locally |
| FR-003 | T004, T008, T016 | T005, T012, T018 | Verified locally |
| FR-004 | T004, T008, T016 | T005, T012, T018 | Verified locally |
| FR-005 | T007 | T011, T012 | Verified locally |
| FR-006 | T004, T015 | T005, T017 | Verified locally |
| FR-007 | T015 | T017 | Verified locally |
| FR-008 | T016 | T018 | Verified locally |
| FR-009 | T020 | T022 | Verified locally |
| FR-010 | T008, T020 | T012, T022 | Verified locally |
| FR-011 | T009 | T013 | Verified locally |
| FR-012 | T021 | T023, T024 | Verified locally |
| FR-013 | T025 | T026, T027 | Verified locally |
| DR-001 | T015 | T017 | Verified locally |
| DR-002 | T004, T008, T009, T016 | T005, T012, T013, T018 | Verified locally |
| DR-003 | T008 | T012 | Verified locally |
| DR-004 | T015 | T017 | Verified locally |
