# Tasks: default operational cases

## Foundation and test-first proofs

- [x] T001 Read main/spec371, imported handoff; review scope and Constitution (FR-001–011).
- [x] T002 Plan bounded rollout, internal authority and immutable history; analyze (FR-006,007,011).
- [x] T003 Add meaningful failing PostgreSQL default/backfill/no-owner/invariant tests in `packages/reality-core/tests/test_default_operational_cases.py` (FR-001,002,003,006,007,010).
- [x] T004 Add migration/history/concurrency and adapter/browser proofs in `tests/test_default_operational_cases.py`, `tests/test_operational_case_migration.py`, `apps/web/scripts/operational-cases-browser.mjs` (FR-004,005,006,008,011).

## Story 1: ordinary default acceptance

- [x] T005 Remove opt-in eligibility, enforce migration checks and immediate accepted/corrected goal coverage in `services/operational_cases.py`, `services/core.py`, `services/case_action_guards.py` (FR-001,002,003,005).

## Story 2: historical rollout and shared jobs

- [x] T006 Add CaseRollout and migration 0145 with bounded durable traversal in `db/operational_cases.py`, `services/operational_cases.py` (FR-003,006,010,011).
- [x] T007 Discover every active tenant and enqueue narrowly authorized internal runs in `services/case_jobs.py`, `jobs/handlers/operational_cases.py`, `services/scheduled_jobs.py` (FR-001,006,007).

## Story 3: preserve intervention and compatibility

- [x] T008 Keep existing takeover/handback, stale reviews/bindings/uncertainty; update legacy opt-in tests without weakening safety assertions in `tests/test_operational_cases.py`, `tests/test_operational_case_jobs.py`, adapters and migration tests (FR-004,005,008,011).
- [x] T009 Remove activation UI; report readiness/failures and validate compatibility in `web/operational_cases.py`, `apps/web/src/unified/OperationalCaseDetail.tsx`, localization and browser proof (FR-008).

## Story 4: simulator and public contract

- [x] T010 Update supplied simulator LIVE/README, regression and spec376 FR-019, durable/Web/public guides and generated docs (FR-009,011). External-runner and multi-day gates stay pending.
- [ ] T011 Run required full backend/migration/Web/browser/localization/docs/spec checks, review diff and record exact evidence before PR (FR-001–011; SC-001–004).

## Dependencies and traceability

T001 → T002 → T003/T004 → T005/T006 → T007 → T008/T009 → T010 → T011.
Tests for T003/T004 precede implementation. T005–T009 prove stories 1–3; T010
proves story 4 integration. Every requirement maps to tests and implementation above.
No parallel edits required. Completion requires green checks; dependency-specific
simulator runtime gates are explicitly reported if unavailable on main.
