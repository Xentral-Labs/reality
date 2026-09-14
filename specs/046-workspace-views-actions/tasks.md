---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Workspace Views and Actions

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/application-reference.md`, `quickstart.md`
**Gate**: Constitution Check passed, scope approved on 2026-09-03, and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm product-scope review and absence of clarification markers in `specs/046-workspace-views-actions/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/046-workspace-views-actions/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve every CRITICAL finding across `specs/046-workspace-views-actions/`

## Phase 2: Foundational Failing Proof

- [x] T004 [P] [US3] [FR-001] [FR-002] [FR-003] [FR-006] [FR-009] [FR-015] [FR-018] Add failing workspace catalog composition and invalid-reference tests in `packages/reality-core/tests/test_application_catalog.py`
- [x] T005 [P] [US1] [FR-004] [FR-005] [FR-007] [FR-008] [FR-017] Add failing source-level desktop/mobile workspace navigation contract in `apps/web/scripts/workspace-actions-contract.test.mjs` and register it in `apps/web/package.json`
- [x] T006 [P] [US2] [FR-010] [FR-011] [FR-012] [FR-013] [FR-014] [DR-003] [DR-004] [DR-005] Add failing Web action confirmation, bounded-input, error, refresh, and trace contract assertions in `apps/web/scripts/workspace-actions-contract.test.mjs`
- [x] T007 [P] [US2] [DR-001] [DR-002] [DR-006] Add or confirm tenant, provenance, shortest-link, append-only, and opaque-identity assertions in `packages/reality-core/tests/test_http_boundary.py`, `packages/reality-core/tests/test_inventory_tracking_reservations.py`, `packages/reality-core/tests/test_movement_corrections.py`, and `packages/reality-core/tests/test_handling_units.py`
- [x] T008 [P] [US1] [FR-016] Add failing four-language workspace/action copy expectations in `apps/web/scripts/localization-contract.test.mjs`
- [x] T009 Run the focused failing proof and record expected failures in `specs/046-workspace-views-actions/quickstart.md`

## Phase 3: User Story 3 - Catalog Alignment (P2, foundational dependency)

**Goal**: Compose one validated application reference for every workspace View and eligible Action.

**Independent test**: Valid catalogs return five deterministic workspaces; fixtures with invalid keys, routes, Projection/Command references, duplicate order, adapter eligibility, or confirmation policy fail.

- [x] T010 [US3] [FR-001] [FR-002] [FR-003] [FR-006] Define five workspaces and their ordered View/Action references in `packages/reality-core/config/workspace_catalog.yaml`
- [x] T011 [US3] [FR-009] Mark only the explicitly exposed Warehouse commands Web-eligible in `packages/reality-core/config/command_catalog.yaml`
- [x] T012 [US3] [FR-015] [FR-018] Load, validate, and compose workspace metadata in `packages/reality-core/src/reality/catalogs.py`
- [x] T013 [US3] [FR-015] Preserve membership protection and expose the expanded reference through `packages/reality-core/src/reality/web/api.py`
- [x] T014 [US3] [FR-001] [FR-002] [FR-003] [FR-006] [FR-009] [FR-015] [FR-018] Run catalog/reference tests and update their result in `specs/046-workspace-views-actions/quickstart.md`

## Phase 4: User Story 1 - Discover the Selected Workspace (P1)

**Goal**: Render persistent navigation followed by separate, catalog-driven Views and Actions for the selected workspace.

**Independent test**: Each workspace produces deterministic desktop/mobile navigation for empty and populated companies without changing tenant or Reality state.

- [x] T015 [P] [US1] [FR-002] [FR-003] [FR-015] Add workspace, View, and Action reference types and fetch handling in `apps/web/src/api.ts`
- [x] T016 [US1] [FR-004] [FR-005] [FR-006] Replace the static contextual list with catalog-driven `Views` and `Actions` groups while preserving the current area-picker edits in `apps/web/src/App.tsx`
- [x] T017 [US1] [FR-007] [FR-008] Add empty-company prerequisite presentation without hiding explicit workspace navigation in `apps/web/src/App.tsx`
- [x] T018 [P] [US1] [FR-016] Add natural English, German, Dutch, and Spanish group and prerequisite labels in `apps/web/src/localization.tsx`
- [x] T019 [US1] [FR-017] Add responsive, keyboard-focus, expanded, and unavailable Action states using existing `br-*` patterns in `apps/web/src/tailwind.css`
- [x] T020 [US1] [FR-004] [FR-005] [FR-007] [FR-008] [FR-016] [FR-017] Run the independent navigation contract, localization audit, and production build and record results in `specs/046-workspace-views-actions/quickstart.md`

## Phase 5: User Story 2 - Governed Warehouse Intervention (P1)

**Goal**: Start and safely confirm every scoped Warehouse Action through existing shared services and inspect the result.

**Independent test**: Reservation, movement, correction, hold/release, handling-unit, lot, and serial actions complete from Warehouse Operations; stale, invalid, and cross-tenant inputs make no partial mutation.

- [x] T021 [P] [US2] [FR-011] [FR-012] Add typed API clients for existing reservation, movement, hold/release, handling-unit, lot, and serial routes in `apps/web/src/api.ts`
- [x] T022 [US2] [FR-010] [FR-011] [DR-005] Implement the shared two-step Warehouse Action dialog and exact-input confirmation summary in `apps/web/src/App.tsx`
- [x] T023 [US2] [FR-012] Implement reserve-stock and commitment hold/release forms through existing endpoints in `apps/web/src/App.tsx`
- [x] T024 [US2] [FR-012] Implement receipt, transfer, shipment, and adjustment variants of Record movement through the existing Movement endpoint in `apps/web/src/App.tsx`
- [x] T025 [US2] [FR-010] [FR-012] [FR-014] Reuse the existing movement-correction selection, server preview fingerprint, confirmation, and stale refusal flow in `apps/web/src/App.tsx`
- [x] T026 [US2] [FR-012] Implement handling-unit, lot, and serial identity forms through existing endpoints in `apps/web/src/App.tsx`
- [x] T027 [US2] [FR-013] Add authoritative result routing, affected-register refresh, and Inspector opening in `apps/web/src/App.tsx`
- [x] T028 [P] [US2] [FR-016] Add four-language form, confirmation, prerequisite, error, and success copy in `apps/web/src/localization.tsx`
- [x] T029 [US2] [FR-017] Add accessible responsive dialog and form styling using shared controls in `apps/web/src/tailwind.css`
- [x] T030 [US2] [FR-009] [FR-010] [FR-011] [FR-012] [FR-013] [FR-014] [DR-001] [DR-002] [DR-003] [DR-004] [DR-005] [DR-006] Run focused backend and frontend Warehouse stories and record results in `specs/046-workspace-views-actions/quickstart.md`

## Phase 6: Documentation and Cross-Cutting Review

- [x] T031 [FR-001] [FR-004] [FR-005] [FR-007] [FR-008] [FR-010] [FR-013] [DR-004] [DR-005] Document the canonical Views/Actions hierarchy and governed action boundary in `docs/WEB_SPEC.md`
- [x] T032 [FR-001] [FR-002] [FR-003] [FR-015] [FR-018] Document the validated workspace classification in `specs/046-workspace-views-actions/contracts/application-reference.md`
- [x] T033 [SC-008] Audit every FR/DR against acceptance scenarios, test tasks, and implementation tasks in `specs/046-workspace-views-actions/spec.md` and `specs/046-workspace-views-actions/tasks.md`
- [x] T034 [SC-007] Run `make spec-check`, `make lint`, and the complete backend PostgreSQL suite and record evidence in `specs/046-workspace-views-actions/quickstart.md`
- [ ] T035 [SC-001] [SC-002] [SC-003] [SC-004] [SC-005] [SC-006] [SC-007] Run frontend contracts, strict i18n audit, production build, and desktop/mobile visual checks and record evidence in `specs/046-workspace-views-actions/quickstart.md`
- [x] T036 Review the final diff against the Constitution, approved scope, current user-owned frontend changes, and rollback plan in `specs/046-workspace-views-actions/plan.md`

## Phase 7: Global Activity Navigation Amendment

- [x] T037 [US1] [FR-004a] Add failing global-only Activity navigation contracts in `apps/web/scripts/workspace-actions-contract.test.mjs` and `packages/reality-core/tests/test_application_catalog.py`
- [x] T038 [US1] [FR-004a] Remove Activity from every workspace View list in `packages/reality-core/config/workspace_catalog.yaml`
- [x] T039 [US1] [FR-004a] Add the drawer-to-full-Activity path and four-language label in `apps/web/src/App.tsx` and `apps/web/src/localization.tsx`
- [x] T040 [US1] [FR-004a] Run catalog, frontend contract, localization, build, and diff checks and record evidence in `specs/046-workspace-views-actions/quickstart.md`

## Phase 8: Company Activity Navigation Amendment

- [x] T041 [US1] [FR-004a] Replace the global-only Activity contracts with failing Company Overview-only navigation contracts
- [x] T042 [US1] [FR-004a] Add Activity once to Company Overview Views and nowhere else in the workspace catalog
- [x] T043 [US1] [FR-004a] Remove the desktop/mobile header controls and the global Activity drawer
- [x] T044 [US1] [FR-004a] Update documentation and run catalog, frontend contract, localization, build, and diff checks

## Phase 9: Empty Company Navigation Regression

- [x] T045 [US1] [FR-004a] Add a failing contract proving onboarding cannot replace Company Overview Views
- [x] T046 [US1] [FR-004a] Render catalog Views and the empty-company Get started entry as separate navigation groups
- [x] T047 [US1] [FR-004a] Run frontend contracts, localization, build, lint, spec policy, and diff checks

## Phase 10: Searchable Order Action Launcher

- [x] T048 [US4] [FR-019] [FR-020] [FR-021] Specify direct-versus-complete action discovery and confirm the Constitution Check remains PASS
- [x] T049 [US4] [FR-019] [FR-020] Add failing catalog and frontend contracts for complete Order membership, search, and explicit clients
- [x] T050 [US4] [FR-019] [FR-020] Add the complete Web-eligible Order action classification
- [x] T051 [US4] [FR-020] Add explicit document-hold and party-delivery-hold clients and confirmed forms
- [x] T052 [US4] [FR-019] [FR-021] Implement the responsive searchable `More actions` launcher with accessible empty and close states
- [x] T053 [US4] [FR-021] Add four-language launcher and Order action copy
- [x] T054 [US4] [SC-007] Run focused and repository verification and record evidence

## Phase 11: Generic Workspace Action Disclosure

- [x] T055 [US4] [FR-019] [FR-021] Add a failing contract requiring the same two-plus-launcher rule for every actionable workspace
- [x] T056 [US4] [FR-019] Remove workspace-specific promotion metadata and derive direct actions from canonical workspace order
- [x] T057 [US4] [FR-019] [FR-021] Show `More actions` for every workspace that has actions and reuse the generic searchable launcher
- [x] T058 [US4] [SC-007] Run catalog, frontend, localization, build, lint, spec, and diff verification

## Phase 12: Complete Business Web Adapters

- [x] T059 [US2] [FR-022] [FR-023] Specify the four missing Web adapters and their workspace classification without changing domain logic
- [x] T060 [US2] [FR-009] [FR-022] [FR-023] Add failing catalog, HTTP-boundary, and frontend client/form contracts
- [x] T061 [US2] [FR-022] [FR-023] Add typed request models and explicit Web endpoints delegating to the existing order, Fact, and payment services
- [x] T062 [US2] [FR-009] [FR-022] Mark the four commands Web-eligible and classify them under Company, Order, Finance, and Data workspaces
- [x] T063 [US2] [FR-010] [FR-011] [FR-022] Add explicit confirmed forms and typed clients for all four actions
- [x] T064 [US2] [FR-016] [FR-017] Add four-language labels and responsive form support
- [x] T065 [US2] [SC-007] Run focused and repository verification and record evidence

## Dependencies

```text
Specification approval (T001-T002)
  -> Analyze gate (T003)
  -> failing proof (T004-T009)
  -> catalog alignment (T010-T014)
  -> navigation (T015-T020)
  -> Warehouse actions (T021-T030)
  -> documentation and full gates (T031-T036)
```

US3 is implemented before the P1 UI stories because its catalog/reference is their shared foundation. US1 can be accepted after Phase 4 without Warehouse mutations. US2 depends on the catalog and navigation action launcher.

## Parallel Opportunities

- T004-T008 affect separate backend/frontend test files.
- T015 and T018 can proceed after the reference contract stabilizes.
- T021 and T028 affect separate API/copy files before dialog integration.
- Existing backend service suites can run in parallel with frontend contract and build checks.

## Implementation Strategy

The first independently useful slice is catalog alignment plus discoverable navigation (US3 + US1). The complete approved outcome adds the governed Warehouse Action flows (US2). Implementation remains test-first and uses existing endpoints/services; no schema or generic execution abstraction is introduced.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001-FR-003 | T004, T014 | T010-T12, T032 | Pending |
| FR-004-FR-008 | T005, T020 | T016-T019, T031 | Pending |
| FR-009 | T004, T006, T014, T030 | T011-T013, T021-T027 | Pending |
| FR-010-FR-014 | T006, T007, T030 | T022-T029, T031 | Pending |
| FR-015 | T004, T014 | T012-T015, T032 | Pending |
| FR-016-FR-017 | T005, T008, T020, T030 | T018-T019, T028-T029 | Pending |
| FR-018 | T004, T014 | T010-T012, T032 | Pending |
| DR-001-DR-006 | T006, T007, T030 | T021-T027, T031 | Pending |
| SC-001-SC-008 | T033-T035 | T031-T036 | Pending |
