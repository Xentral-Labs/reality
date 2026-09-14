# Tasks: Operational read performance

## Setup and review
- [x] T001 Record baseline and approve bounded scope in spec.md and research.md (FR-001–005).
- [x] T002 Review Constitution and specify read-only input and selective-refresh design in plan.md (FR-001–004).

## US1 — Exceptions
- [x] T003 [US1] Add and observe failing query-budget, parity, freshness, failure-cleanup and tenant tests in packages/reality-core/tests/test_operational_read_performance.py (FR-001, FR-002, FR-004, FR-005).
- [x] T004 [US1] Share correction-aware scalar/batch movement query in packages/reality-core/src/reality/services/core.py (FR-001).
- [x] T005 [US1] Implement scoped bulk inputs in packages/reality-core/src/reality/services/exception_inputs.py and reuse them in services/exceptions.py (FR-001, FR-002).

## US2 — Finance
- [x] T006 [US2] Add and observe failing unrelated-refresh, freshness, parity, page/totals and isolation tests in packages/reality-core/tests/test_operational_read_performance.py (FR-003–005).
- [x] T007 [US2] Extract financial builder and selective refresh in packages/reality-core/src/reality/services/projections.py; integrate web/read_models.py (FR-003, FR-004).

## Verification and review
- [x] T008 Run required backend, lint, specification and frontend/site gates; record results in quickstart.md (FR-005, SC-002).
- [x] T009 Review scoped diff, deploy matching local services and remeasure browser clicks on port 8080; record values and limitations in quickstart.md (FR-005, SC-001).

Dependencies: T001 → T002 → analysis → T003 → T004 → T005; T006 precedes T007; T008/T009 follow both stories. Independent test-file cases for US1 and US2 could be authored in parallel, but execution here is sequential. Deliver both stories before local acceptance; no partial claim of completion.
