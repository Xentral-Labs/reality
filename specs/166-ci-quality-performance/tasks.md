# Tasks: Faster Quality Gates

**Input**: Design documents from `/specs/166-ci-quality-performance/`

## Phase 1: Classification proof

- [x] T001 [US1] Add failing backend-path classification coverage in `scripts/test_ci_backend_changes.py` for frontend-only, backend, deployment, Compose, workflow, empty and unknown inputs (FR-001–004, SC-001–002).
- [x] T002 [US1] Implement the fail-safe standard-library classifier in `scripts/ci_backend_changes.py` (FR-001–004).

## Phase 2: Workflow integration

- [x] T003 [US1] Add `backend-changes` to `.github/workflows/quality.yml`, condition backend quality for pull requests, and preserve unconditional main runs (FR-001–004).
- [x] T004 [US2] Measure four work-stealing workers on one GitHub runner and record why its 10:36 result does not justify the design (FR-005–007).

## Phase 3: Verification and review

- [x] T005 Run classifier tests, workflow syntax validation, `make spec-check`, Ruff and the complete four-worker PostgreSQL suite; record collected/pass counts (FR-001–007, SC-001–003).
- [x] T006 Open the pull request, compare GitHub job time against 11:01, and record skip/full-run evidence in `specs/166-ci-quality-performance/quickstart.md` (SC-004–005).
- [x] T007 [US2] Add tested deterministic test-file sharding and two isolated runner jobs while preserving `backend-quality` as the required aggregate check (FR-004–007, SC-003–005).

## Dependencies

T001 precedes T002. T002 precedes T003. T003 and T004 share the workflow and remain
sequential. T005 follows implementation; T006 follows local verification.
