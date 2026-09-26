# Tasks: Order Readiness Control

## Phase 1: Gates

- [x] T001 Review requirements and resolve clarifications in `specs/280-order-readiness-control/spec.md`
- [x] T002 Pass Constitution Check in `specs/280-order-readiness-control/plan.md`
- [x] T003 Analyze spec/plan/tasks consistency in `specs/280-order-readiness-control/`

## Phase 2: Failing Proof

- [x] T004 [P] [US1] [FR-001,FR-002,FR-003,FR-004,FR-005,FR-006] Add readiness view payload/presentation contract tests in `apps/web/scripts/order-readiness.test.mjs`
- [x] T005 [P] [US2] [FR-007,FR-008,FR-009,FR-010] Add current/stale/missing metadata and bounded API tests in existing projection/API coverage and `apps/web/scripts/order-readiness.test.mjs`
- [x] T006 [P] [US3] [FR-011,FR-012,DR-001,DR-002,DR-003,DR-004] Add exact Inspector navigation and no-mutation tests in `apps/web/scripts/order-readiness.test.mjs`

## Phase 3: User Story 1 — Readiness control

- [x] T007 [US1] [FR-002,FR-003,FR-004,FR-005] Add bounded typed fulfillment row/line contracts in `apps/web/src/api.ts`
- [x] T008 [US1] [FR-001,FR-006] Add the Sales readiness route and tab in `apps/web/src/unified/routing.ts` and `apps/web/src/unified/OrdersPage.tsx`
- [x] T009 [US1] [FR-003,FR-004,FR-005,FR-006] Render exact order/line readiness and blockers in `apps/web/src/unified/OrdersPage.tsx`

## Phase 4: User Story 2 — Freshness

- [x] T010 [US2] [FR-007,FR-008,FR-009] Render observation, pending and unavailable states in `apps/web/src/unified/OrdersPage.tsx`
- [x] T011 [US2] [FR-010] Preserve server search/paging through `api.specializedProjection` in `apps/web/src/api.ts` and `apps/web/src/unified/OrdersPage.tsx`

## Phase 5: User Story 3 — Trace

- [x] T012 [US3] [FR-011,FR-012] Wire exact Document/Commitment Inspector links with no direct mutation in `apps/web/src/unified/OrdersPage.tsx`
- [x] T013 [US3] [FR-013,FR-014] Add four-language labels and responsive/keyboard structural coverage in `apps/web/src/localization.tsx` and `apps/web/scripts/order-readiness.test.mjs`

## Final Phase

- [ ] T014 [FR-015] Run backend projection/Web/Chat/MCP parity regression suites
- [x] T015 Run `make spec-check`, `make lint`, Web tests/i18n/build and focused PostgreSQL tests
- [x] T016 Run `make docs-catalog-check` and confirm no catalog drift
- [x] T017 Review final diff against Constitution, specs 113/275 and all FR/DR requirements

## Dependencies

T004-T006 precede T007-T013. US2 and US3 depend on the US1 route/table skeleton. Final gates follow all stories.

## Requirement Coverage

| Requirement | Test tasks | Implementation tasks |
|---|---|---|
| FR-001–FR-006 | T004 | T007-T009 |
| FR-007–FR-010 | T005 | T010-T011 |
| FR-011–FR-014 | T006, T013 | T012-T013 |
| FR-015, DR-001–DR-004 | T006, T014 | T007-T012 |
