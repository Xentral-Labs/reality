---
description: "Requirement-traceable live demo cost readiness implementation tasks"
---

# Tasks: Live Demo Cost Readiness

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Gate**: Product scope approved, Constitution Check passed, no unresolved clarification

## Phase 1: Specification and design gates

- [X] T001 Confirm product approval and zero unresolved clarification markers in `specs/251-live-demo-cost-readiness/spec.md`
- [X] T002 Confirm every Constitution Check row is PASS and no migration is planned in `specs/251-live-demo-cost-readiness/plan.md`
- [X] T003 Run `$speckit-analyze` and resolve every CRITICAL finding across `specs/251-live-demo-cost-readiness/`

## Phase 2: Foundational failing proof

- [X] T004 [P] [US1] [FR-001] [FR-002] [DR-001] Add a failing canonical-profile census proving every positive-stock item has explicit positive retained acquisition evidence in `packages/reality-core/tests/test_demo_costing_profile.py`
- [X] T005 [P] [US1] [FR-003] [FR-004] [DR-002] Add failing current-generation and exact-cutoff assertions for all declared inventory and contribution scopes in `packages/reality-core/tests/test_demo_costing_profile.py`
- [X] T006 [P] [US1] [FR-005] [FR-006] [FR-012] [FR-014] Add setup ordering, retry, cutoff, timeout and bounded-diagnostic tests in `packages/reality-core/tests/test_company_setup_initialization.py`
- [X] T007 [P] [US2] [FR-007] [FR-008] [FR-009] [FR-010] Add relevant-event, batch invalidation and selling-cost withdrawal freshness proofs in existing costing service tests
- [X] T008 [P] [US3] [FR-011] [DR-004] Add fresh-demo shared Web/API, application-tool and MCP-equivalent costing response assertions in `packages/reality-core/tests/test_demo_costing_profile.py`
- [X] T009 [P] [US3] [FR-013] [DR-006] [DR-007] Reuse historical no-repair, foreign-scope refusal and schema-stability assertions in existing setup and costing tests

## Phase 3: User Story 1 — calculation-ready company (P1)

**Goal**: A newly ready canonical demo has current, explainable cost values without a manual refresh.

**Independent test**: Create a fresh canonical company and census every positive-stock item and declared contribution line at the readiness cutoff.

- [X] T010 [US1] [FR-001] [FR-002] [DR-001] [DR-003] Author lossless positive acquisition evidence and opaque movement bindings for every positive-stock profile item in `packages/reality-core/src/reality/services/demo_profile.py`
- [X] T011 [US1] [FR-003] [FR-004] [DR-002] Build one final batch inventory review and publish/verify existing inventory and contribution generations in `packages/reality-core/src/reality/services/demo_profile.py` and `packages/reality-core/src/reality/services/costing.py`
- [X] T012 [US1] [FR-006] [FR-012] Persist a compact idempotent cost-readiness cutoff and coverage summary in existing `PlaygroundRun.initialization_progress` through `packages/reality-core/src/reality/services/company_setup.py`
- [X] T013 [US1] [FR-003] [FR-004] [FR-006] [FR-014] Gate ready/live-source startup on verified cost coverage and retain bounded failures in `packages/reality-core/src/reality/jobs/handlers/company_setup.py`
- [X] T014 [US1] [FR-005] [FR-010] Present truthful calculation pending/running/succeeded/failed progress and retain success for at least 1.5 seconds in `apps/web/src/unified/setupProgress.ts`
- [X] T015 [US1] [FR-005] Run the setup browser acceptance proof and update evidence in `apps/web/scripts/company-setup-live-browser.mjs` and `specs/251-live-demo-cost-readiness/quickstart.md`

## Phase 4: User Story 2 — truthful freshness during live intake (P1)

**Goal**: Unrelated synthetic intake leaves retained scopes current; changed authority is stale until explicit review.

**Independent test**: Complete one deterministic order/settlement cycle and observe unchanged retained scopes remain current; then add a relevant movement and selling-cost withdrawal and observe truthful stale current reads with stable history.

- [X] T016 [US2] [FR-007] [DR-003] [DR-005] Implement tenant-scoped item-relevant movement/correction freshness in `packages/reality-core/src/reality/services/inventory_costing.py`
- [X] T017 [US2] [FR-007] [FR-009] Prove unrelated finance and intake events do not invalidate retained inventory or contribution observations
- [X] T018 [US2] [FR-008] [FR-010] Preserve batch-review atomicity when one reviewed item receives a newer relevant movement in `packages/reality-core/src/reality/services/contribution_reviews.py`
- [X] T019 [US2] [FR-008] [FR-010] Detect superseded or withdrawn selling-cost attribution without replacing authority and preserve historical reviewed results
- [X] T020 [US2] [FR-009] [FR-010] Record the normal live-cycle and explicit stale-evidence acceptance in `specs/251-live-demo-cost-readiness/quickstart.md`

## Phase 5: User Story 3 — interface parity (P2)

**Goal**: People and agents receive the same value, cutoff, freshness and explanation.

**Independent test**: Compare three inventory and three contribution scopes through shared Web/API and MCP reads before and after one live cycle.

- [X] T021 [US3] [FR-010] [FR-011] [DR-004] Normalize the shared costing read outcome vocabulary without adding adapter business rules in `packages/reality-core/src/reality/services/cost_query.py`
- [X] T022 [US3] [FR-011] [DR-001] [DR-005] Prove Web/API/application-tool/MCP reuse the same scope, cutoff and explanation contract in `packages/reality-core/tests/test_demo_costing_profile.py` and existing adapter tests
- [X] T023 [US3] [FR-013] [DR-006] Prove deployment neither repairs historical companies nor reveals foreign scope existence through existing setup and costing tests

## Final Phase: Documentation and cross-cutting review

- [X] T024 [P] [FR-001] [FR-014] Update the durable setup/demo contract and catalog coverage wording in `docs/features/company-setup-demo.md` and `docs/features/demo-data-catalog.md`
- [X] T025 [P] [FR-007] [FR-012] Update shared job behavior and rollback evidence in `docs/features/scheduled-jobs.md`
- [X] T026 [FR-011] Run `make docs-generate`; generated catalog output is unchanged because no public tool schema changed
- [X] T027 [SC-007] Run the feature requirement-to-task audit and update only implementation task markers with green evidence in `specs/251-live-demo-cost-readiness/tasks.md`
- [ ] T028 [SC-001] [SC-003] Run the focused PostgreSQL stories and ten fresh setup cycles described in `specs/251-live-demo-cost-readiness/quickstart.md`
- [ ] T029 Run `make lint`, `make test`, `make web-build`, `cd apps/web && npm run i18n:audit`, and applicable browser tests
- [ ] T030 Review the migration chain (expect no new migration), rollback, tenant scope, shortest links and final diff against `.specify/memory/constitution.md`
- [ ] T031 Record final reviewer evidence without self-checking `specs/251-live-demo-cost-readiness/checklists/readiness.md`

## Dependencies

- Phase 1 blocks all implementation.
- Phase 2 failing proofs block the corresponding story implementation.
- US1 blocks US2 because relevant-event freshness requires a calculation-ready retained basis.
- US3 can begin after US1 and completes after US2 supplies the after-live-cycle state.
- Documentation and full verification follow all stories.

## Parallel opportunities

- T004–T009 can be authored in parallel because they target separate proof families.
- After T010–T013 establish the readiness service contract, T014 browser presentation can proceed independently.
- T016 relevant movement freshness and T019 selling-cost freshness can be developed in parallel against their service proofs.
- T024 and T025 can proceed in parallel after behavior stabilizes.

## Requirement coverage

| Requirement group | Test task(s) | Implementation/documentation task(s) |
|---|---|---|
| FR-001–FR-004 | T004–T005 | T010–T013, T024 |
| FR-005–FR-006 | T006, T015 | T012–T015 |
| FR-007–FR-010 | T007, T020 | T016–T020, T025 |
| FR-011 | T008, T022 | T021–T022, T026 |
| FR-012–FR-014 | T006, T009, T023 | T012–T013, T017, T023–T025 |
| DR-001–DR-003 | T004–T005 | T010–T011, T016, T022 |
| DR-004–DR-005 | T007–T008 | T016–T022, T025 |
| DR-006–DR-007 | T009, T023 | T023, T030 |
| SC-001–SC-007 | T015, T020, T022–T023, T027–T029 | T024–T031 |

## Implementation strategy

The MVP is US1: a fresh company cannot say ready until its canonical inventory and
contribution coverage is current and explainable. Then add scope-relevant live freshness (US2),
followed by explicit cross-interface parity proof (US3). Tests precede each behavior
change; no checklist or acceptance marker becomes complete while a required gate is red.
