# Tasks: Free Playground Operations
- [x] T018 [FR-013] Add backend master-data regression tests before implementation; implement strict reviewed shared-tool execution and exact policy binding.
- [x] T019 [FR-013] Add master-data chooser/editor and readable review, Back, four languages and refreshed references; test browser and contracts.
- [x] T020 [FR-013] Verify backend/security, web build/audit/contracts/browser and spec gates; review and record evidence. Import simulation remains the next increment.
- [x] T015 Specify and implement independent customer/supplier invoice selection and reviewed posting using shared finance services. Backend/browser checks pass; locally deployed.
- [x] T016 Implement independent open-item payment selection, editable partial amount and reviewed allocation through shared tools. Four finance browser paths including reload pass; locally deployed.
- [x] T017 Specify and test reviewed reservation release with shared tool, tenant safeguards and stale-state checks; group the completed individual entries by business area. Backend/security/browser and web gates pass; API/web rebuilt locally.
- [x] T014 Add independent reserve/shipment/receipt chooser shortcuts with action-scoped open-order selection and Back; verify browser/contracts/build. Finance and reservation-release independent entry remain follow-up work.

## Design gates

- [x] T001 Record approved first increment and research in spec.md and plan.md; verify Constitution PASS and no unresolved clarification.
- [x] T002 Analyze spec.md, plan.md and tasks.md before implementation. All eight FR/DR mapped to tasks; no unresolved questions or critical findings; requirements checklist 6/6 PASS.

## US1 — Independent creation

- [x] T003 [US1] [FR-001] [FR-002] [FR-005] [DR-001] Add failing free editor/intent contracts in apps/web/scripts/playground-free-operations.test.mjs.
- [x] T004 [US1] [FR-001] [FR-002] [FR-005] [DR-001] Implement FreeOperations.tsx and PlaygroundPage.tsx mode/refresh wiring using existing reviewed steps.

## US2 — Open work

- [x] T005 [US2] [FR-003] [FR-004] [FR-005] [DR-002] Add backend tests in packages/reality-core/tests/test_playground_free_operations.py for response targets and stale selected work.
- [x] T006 [US2] [FR-003] [FR-004] [FR-005] [DR-002] Extend web/api.py response and services/playground.py freshness, and api.ts paging/types without widening policy.
- [x] T007 [US2] [FR-003] [FR-004] [FR-006] Implement OpenWork.tsx and PlaygroundWorkspace.tsx integrated table with selected actions and scoped refresh.

## Verification

- [x] T008 [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] [DR-001] [DR-002] [SC-001] [SC-002] Add and run the mixed-operation browser story in apps/web/scripts/playground-free-browser.mjs, all languages, pending/archived/reload and desktop/mobile states.
- [x] T009 [FR-006] Complete localization.tsx and CSS token styling, update docs/WEB_SPEC.md; run full backend, Ruff, web contracts/audit/build, spec policy and record evidence in quickstart.md.

## Dependencies and execution

T001 → T002 → T003/T005 failing proof → T006 → T004/T007 → T008 → T009.
US1 and US2 are independently testable but ship together for the first useful free
operation increment. Backend and UI contract tests can run independently. No schema.
Later bulk/picking and Shopify-import work is explicitly outside this increment.

## Grouped chooser refinement

- [x] T013 [FR-009] Add execution-state/polling regression checks, implement ExecutionStatus.tsx and localized messages, verify web contracts/build/browser fixtures, then deploy only web.

- [x] T012 [FR-008] [FR-005] Add regression tests for overdelivery preparation/confirmation, proven legacy discard and refusal cases; implement shared validator, guarded recovery and UI quantity/navigation fixes; verify full backend and browser gates and repair only the identified failed attempt through the service.

- [x] T011 [FR-007] Add register-separation contracts; implement OpenItems.tsx, server-filtered paging in api.ts, central slots and attention-only right pane; verify contracts, audit/build, browser states and local web deployment.

- [x] T010 [FR-001] [FR-005] [FR-006] Add failing grouped chooser contract; replace mode tabs with two simultaneously visible groups, preserve pending review and guided progression; verify web gates and both browser journeys, then rebuild only web.
- [x] T021 [FR-014] Add compact-chooser regression coverage; implement native disclosure and localization; verify web contracts/build/audit/browser and spec policy, review and deploy web only.
