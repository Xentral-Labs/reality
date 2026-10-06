# Tasks

## Setup
- [x] T001 [US1] Create the day/week fixture in `packages/reality-core/scenarios/reference_week/scenario.yaml` (FR-001, FR-008).

## Tests first
- [x] T002 [US1] Add day/week, confirmation, repeat-run, mismatch/stop and report tests in `packages/reality-core/tests/scenarios/test_reference_week.py` (FR-001–FR-007).

## User Story 1
- [x] T003 [US1] Implement the supported simulator adapter in `packages/reality-core/scenarios/reference_week/simulator.py` (FR-002, FR-003).

## User Story 2
- [x] T004 [US2] Implement exact scoped observations in `packages/reality-core/scenarios/harness/observer.py` (FR-004).
- [x] T005 [US2] Implement orchestration/reporting in `packages/reality-core/scenarios/harness/runner.py` and `reporting.py` (FR-005, FR-006, FR-008).

## User Story 3 and verification
- [x] T006 [US3] Verify week continuation and regressions; document launch and coverage in `packages/reality-core/scenarios/reference_week/README.md`, `docs/scenarios/reality-reference-week.md` and `specs/372-reference-week-harness/quickstart.md` (FR-007, FR-008).
