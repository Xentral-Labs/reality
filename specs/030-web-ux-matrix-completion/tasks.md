# Tasks: Web UX Matrix Completion

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/ux-matrix-coverage.md`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Test tasks precede the behavior they prove. `016/FR-006` remains open
until final product-owner approval; `016/FR-015` remains out of scope.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm product-owner specification approval and zero clarification markers in `specs/030-web-ux-matrix-completion/spec.md` and `specs/030-web-ux-matrix-completion/checklists/requirements.md`
- [x] T002 Confirm product-owner plan approval and all Constitution Check rows PASS in `specs/030-web-ux-matrix-completion/plan.md`
- [x] T003 Run `$speckit-analyze` across `specs/030-web-ux-matrix-completion/spec.md`, `specs/030-web-ux-matrix-completion/plan.md`, and `specs/030-web-ux-matrix-completion/tasks.md`; resolve all CRITICAL/HIGH findings before implementation

## Phase 2: Foundational Coverage Contract

**Purpose**: Freeze actual topology and matrix ownership before changing presentation.

- [x] T004 [P] [FR-001] [FR-002] [FR-018] Add `ux-matrix-v1` with every current route, nested destination, matrix surface, job, hierarchy, state, explanation, responsive case, and owner in `apps/web/scripts/fixtures/ux-matrix-v1.json`
- [x] T005 [P] [FR-001] [FR-002] [DR-006] Add a failing exact route/settings-destination inventory parser and duplicate/stale ownership proof in `apps/web/scripts/ux-matrix-contract.test.mjs`
- [x] T006 [P] [FR-014] [FR-015] [FR-018] Add failing required-state and desktop/mobile case validation with named drift categories in `apps/web/scripts/ux-matrix-contract.test.mjs`
- [x] T007 [P] [FR-013] [DR-001] [DR-003] [DR-004] Add failing explanation-entry and opaque-link boundary validation in `apps/web/scripts/ux-matrix-contract.test.mjs`
- [x] T008 [FR-018] [DR-006] Prove deliberate manifest mutations report every category defined by `specs/030-web-ux-matrix-completion/contracts/ux-matrix-coverage.md` in `apps/web/scripts/ux-matrix-contract.test.mjs`
- [x] T009 [FR-001] [FR-018] Register every new UX matrix, operational, finance/Evidence, configuration, support/trace, and responsive contract test in the standard `test:i18n` command in `apps/web/package.json`
- [x] T010 [FR-001] [FR-002] [DR-006] Record authentication and profile routes as explicit baseline-supporting out-of-scope destinations, while retaining topology drift detection, in `apps/web/scripts/fixtures/ux-matrix-v1.json` and `specs/030-web-ux-matrix-completion/contracts/ux-matrix-coverage.md`
- [x] T011 [FR-001] [FR-002] Reconcile actual topology and separately owned Spec 029 Activity integration in `docs/WEB_UX_MATRIX.md` without weakening any page job

**Checkpoint**: The exhaustive contract exists and fails on current unfulfilled hierarchy/state evidence.

## Phase 3: User Story 1 — Start With the Required Decision (P1, MVP)

**Goal**: Daily operational surfaces lead with attention, position, and truthful next action.

**Independent Test**: Exercise populated, attention, and empty states for Home, Facts,
Exceptions, Commitments, Inventory, Reservations, and Movements at desktop/mobile sizes.

### Tests

- [x] T012 [P] [US1] [FR-003] [FR-014] Add failing Home/Facts hierarchy and empty/loading/error contract cases in `apps/web/scripts/ux-operational-contract.test.mjs`
- [x] T013 [P] [US1] [FR-004] [FR-014] Add failing Exceptions search/priority behavior, hierarchy, state, and Inspect contract cases in `apps/web/scripts/ux-operational-contract.test.mjs`
- [x] T014 [P] [US1] [FR-004] [FR-013] Add failing Commitments/Reservations/Movements business-label, action, and explanation contract cases in `apps/web/scripts/ux-operational-contract.test.mjs`
- [x] T015 [P] [US1] [FR-005] [DR-002] Add failing tenant-scoped inventory state/location/filter and authoritative equation assertions in `packages/reality-core/tests/test_web_ux_reads.py`
- [x] T016 [P] [US1] [FR-004] [DR-002] [DR-003] Add failing tenant-resolved Reservation/Movement label and foreign-boundary assertions in `packages/reality-core/tests/test_web_ux_reads.py`

### Implementation

- [x] T017 [US1] [FR-003] [FR-014] Align Home/Facts first-viewport hierarchy and truthful shared states in `apps/web/src/App.tsx`
- [x] T018 [US1] [FR-004] [DR-002] Implement real Exceptions search/priority inputs through existing tenant-scoped reads in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T019 [US1] [FR-004] [FR-014] Wire Exceptions controls and attention-first result states in `apps/web/src/api.ts` and `apps/web/src/App.tsx`
- [x] T020 [US1] [FR-005] [DR-002] Extend the existing inventory read only as required for authoritative location filtering/explanation inputs in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T021 [US1] [FR-005] [FR-013] Implement inventory control totals, location/state controls, and equation-based shared Inspect entry in `apps/web/src/api.ts` and `apps/web/src/App.tsx`
- [x] T022 [US1] [FR-004] [DR-003] Expose tenant-resolved business labels for Reservations/Movements through bounded read responses in `packages/reality-core/src/reality/web/api.py`
- [x] T023 [US1] [FR-004] [FR-013] Make Commitments/Reservations/Movements business-first while retaining opaque IDs in Inspect in `apps/web/src/App.tsx`
- [x] T024 [US1] [FR-016] Apply only the shared operational hierarchy/state/responsive styles needed by three or more surfaces in `apps/web/src/tailwind.css`
- [x] T025 [US1] [FR-003] [FR-004] [FR-005] Record the independent operational acceptance result in `specs/030-web-ux-matrix-completion/quickstart.md`

**Checkpoint**: The P1 operational family is independently usable and explainable.

## Phase 4: User Story 2 — Control Financial Position and Evidence (P1)

**Goal**: Finance and Evidence surfaces provide authoritative controls and explanation.

**Independent Test**: Exercise receivable/payable, overdue, unmatched, balanced, corrected,
and empty states across Open Items, Payments, Journal, Documents, and document explanation.

### Tests

- [x] T026 [P] [US2] [FR-006] [DR-002] Add failing open-item overdue/flow totals and unmatched-payment ordering assertions in `packages/reality-core/tests/test_web_ux_reads.py`
- [x] T027 [P] [US2] [FR-006] [DR-002] Add failing tenant-scoped Journal rows, debit/credit totals, account/date filters, account/posting drill-down targets, boundedness, and foreign-boundary assertions in `packages/reality-core/tests/test_web_ux_reads.py`
- [x] T028 [P] [US2] [FR-006] [FR-014] Add failing Finance destination/hierarchy/state/primary-action contracts in `apps/web/scripts/ux-finance-evidence-contract.test.mjs`
- [x] T029 [P] [US2] [FR-007] [FR-013] [DR-001] Add failing Documents business-context and document-explanation section-order/raw-payload contracts in `apps/web/scripts/ux-finance-evidence-contract.test.mjs`

### Implementation

- [x] T030 [US2] [FR-006] [DR-002] Extend existing finance reads with authoritative overdue/flow totals and deterministic unmatched-first ordering in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T031 [US2] [FR-006] [DR-002] Expose existing journal/account truth and account/posting Inspect targets as one tenant-scoped bounded read contract in `packages/reality-core/src/reality/web/api.py`
- [x] T032 [US2] [FR-006] Add Journal types/client method and the canonical Finance navigation destination in `apps/web/src/api.ts` and `apps/web/src/App.tsx`
- [x] T033 [US2] [FR-006] [FR-014] Implement Open Items, Payments, and Journal control hierarchy, filters, worklists, account/posting drill-down, and truthful empty states in `apps/web/src/App.tsx`
- [x] T034 [US2] [FR-007] [DR-001] [DR-003] Reorder Documents and document Inspector around business context, Reality consequence, finance, Source metadata, and collapsed raw payload in `apps/web/src/App.tsx`
- [x] T035 [US2] [FR-016] Add only shared finance/Evidence table, control-total, disclosure, and responsive styles in `apps/web/src/tailwind.css`
- [x] T036 [US2] [FR-006] [FR-007] Record the independent finance/Evidence acceptance result in `specs/030-web-ux-matrix-completion/quickstart.md`

**Checkpoint**: Finance and Evidence are scannable, balanced, and traceable without technical-first presentation.

## Phase 5: User Story 3 — Maintain Minimal Operational Configuration (P2)

**Goal**: Reference, commercial, source, and company setup are focused and read-first.

**Independent Test**: Complete find/create/inspect/edit/lifecycle/empty journeys for reference
data, Commercial Terms/Pricing, Sources & Imports, and company settings.

### Tests

- [x] T037 [P] [US3] [FR-008] [FR-014] Add failing reference register/detail hierarchy, explicit-edit, lifecycle, and state contracts in `apps/web/scripts/ux-configuration-contract.test.mjs`
- [x] T038 [P] [US3] [FR-009] [FR-011] Add failing focused Commercial/Pricing and company-settings hierarchy contracts in `apps/web/scripts/ux-configuration-contract.test.mjs`
- [x] T039 [P] [US3] [FR-010] [DR-001] Add failing configured-source-first, readiness, test-intake separation, and recent-SourceRecord contracts in `apps/web/scripts/ux-configuration-contract.test.mjs`
- [x] T040 [P] [US3] [FR-008] [FR-010] [DR-002] Add focused API assertions for any newly required tenant-resolved context/read fields in `packages/reality-core/tests/test_web_ux_reads.py`

### Implementation

- [x] T041 [US3] [FR-008] [DR-003] Make Party/Item/Location registers business-first and details read-first with explicit edit and separated lifecycle controls in `apps/web/src/App.tsx`
- [x] T042 [US3] [FR-009] Focus Commercial/Pricing on lists, tiers, assignments, and groups with one active workflow and contextual empty guidance in `apps/web/src/App.tsx`
- [x] T043 [US3] [FR-010] [DR-001] Prioritize configured sources, separate catalog/configuration/test intake, and retain recent immutable records in `apps/web/src/App.tsx`
- [x] T044 [US3] [FR-011] Preserve one Company/Data/Agents settings hierarchy and canonical title in `apps/web/src/App.tsx`
- [x] T045 [US3] [FR-016] Add shared configuration tab/detail/edit/danger-zone responsive styles in `apps/web/src/tailwind.css`, `apps/web/src/commercial.css`, and `apps/web/src/companies.css`
- [x] T046 [US3] [FR-008] [FR-009] [FR-010] [FR-011] Record the independent configuration acceptance result in `specs/030-web-ux-matrix-completion/quickstart.md`

**Checkpoint**: Configuration supports Reality's minimal model without becoming a shadow ERP.

## Phase 6: User Story 4 — Ask, Learn, and Trace Without Losing Context (P2)

**Goal**: Conversation, guidance, technical inspection, and shared explanation stay distinct.

**Independent Test**: Traverse representative operational answers through Inspect and exercise
Ask Reality, Explorer, and Help in populated/empty desktop/mobile states.

### Tests

- [x] T047 [P] [US4] [FR-012] [FR-014] Add failing Ask Reality active/empty/evidence/proposal/confirmation preservation contracts in `apps/web/scripts/ux-support-trace-contract.test.mjs`
- [x] T048 [P] [US4] [FR-012] Add failing Explorer search/landmark/bounded-detail and Help search/task-first contracts in `apps/web/scripts/ux-support-trace-contract.test.mjs`
- [x] T049 [P] [US4] [FR-013] [DR-001] [DR-004] Add representative Answer → Reality → Evidence → Source traversal assertions in `packages/reality-core/tests/test_web_ux_reads.py`

### Implementation

- [x] T050 [US4] [FR-012] Preserve Spec 028 behavior while completing active Ask Reality business context, evidence, proposal, and confirmation hierarchy in `apps/web/src/App.tsx`
- [x] T051 [US4] [FR-012] Complete Explorer search/landmarks/detail context and Help task-first search/reference hierarchy in `apps/web/src/App.tsx`
- [x] T052 [US4] [FR-013] [DR-001] [DR-004] Complete shared Inspector context preservation and shortest true explanation links in `apps/web/src/App.tsx` and `packages/reality-core/src/reality/web/api.py`
- [x] T053 [US4] [FR-016] Add only shared support/trace responsive and progressive-disclosure styles in `apps/web/src/tailwind.css`
- [x] T054 [US4] [FR-012] [FR-013] Record the independent support/trace acceptance result in `specs/030-web-ux-matrix-completion/quickstart.md`

**Checkpoint**: Simple operational surfaces and deep explanation remain one product and one truth.

## Phase 7: User Story 5 — Trust a Consistent Responsive Product (P2)

**Goal**: Every destination has complete state and responsive evidence.

**Independent Test**: Run the versioned route/state audit and review all affected destinations
at desktop/mobile sizes with zero browser errors.

### Tests and evidence

- [x] T055 [P] [US5] [FR-014] [FR-015] Create the deterministic destination/state/viewport review sheet in `specs/030-web-ux-matrix-completion/checklists/visual-review.md`
- [x] T056 [P] [US5] [FR-015] [FR-016] Add structural contracts requiring the shared `br-*` page-header, control, form, table, dialog/drawer, and state primitives plus bounded mobile table scrolling in `apps/web/scripts/ux-responsive-contract.test.mjs`
- [x] T057 [P] [US5] [FR-017] [DR-002] [DR-005] Add a browser-boundary regression rejecting business aggregation, stored presentation authority, and schema/migration expansion in `apps/web/scripts/ux-responsive-contract.test.mjs` and `packages/reality-core/tests/test_spec_policy.py`
- [x] T058 [US5] [FR-014] [FR-015] Run and record every applicable populated/empty/loading/error/confirmation/destructive desktop/mobile case in `specs/030-web-ux-matrix-completion/checklists/visual-review.md`
- [x] T059 [US5] [FR-014] [FR-015] [FR-016] Correct only cross-surface state/responsive defects exposed by T055–T058 using shared `br-*` primitives in `apps/web/src/App.tsx` and `apps/web/src/tailwind.css`
- [x] T060 [US5] [FR-001] [FR-014] [FR-015] Run the complete UX manifest and visual acceptance proof and record exact results in `specs/030-web-ux-matrix-completion/quickstart.md`
- [x] T061 [US5] [FR-014] [FR-016] Add complete German, Dutch, and Spanish catalog entries for every new or changed user-facing string in `apps/web/src/localization.tsx`

**Checkpoint**: All in-scope destinations have executable and reviewed desktop/mobile evidence.

## Final Phase: Cross-Cutting Review and Baseline Closure

- [x] T062 [P] [DR-001] [DR-002] [DR-003] [DR-004] Update the implemented hierarchy, authoritative-read, and explanation contracts in `docs/WEB_SPEC.md`, `docs/WEB_UX_MATRIX.md`, and `docs/features/web.md`
- [x] T063 [P] [DR-005] Record pre/post model and migration inventories and confirm no schema expansion in `specs/030-web-ux-matrix-completion/quickstart.md`
- [x] T064 Run Ruff, focused PostgreSQL UX-read tests, and the complete PostgreSQL suite; record exact results in `specs/030-web-ux-matrix-completion/quickstart.md`
- [x] T065 Run all Product Web contracts, localization audit, production build, and `git diff --check`; record exact results in `specs/030-web-ux-matrix-completion/quickstart.md`
- [x] T066 Review final diff against Constitution, Spec 030, all FR/DR mappings, tenant boundaries, browser calculation boundaries, shortest links, and Spec 029 ownership in `specs/030-web-ux-matrix-completion/checklists/requirements.md`
- [x] T067 [FR-019] Before baseline closure, add a regression expecting `016/FR-006` verified, its gap row absent, and `016/FR-015` retained in `packages/reality-core/tests/test_spec_policy.py`
- [x] T068 [FR-019] After product-owner final approval, mark only `016/FR-006` verified in `specs/016-web-product/spec.md` and remove only its row from `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T069 Run final Spec policy, traceability, checklist, and diff gates; record exact results in `specs/030-web-ux-matrix-completion/quickstart.md`

## Dependencies and Execution Order

```text
T001–T003 approvals and analysis
  → T004–T011 executable foundation
    → T012–T025 US1 operational MVP
    → T026–T036 US2 finance/Evidence
    → T037–T046 US3 configuration
    → T047–T054 US4 support/trace
      → T055–T060 US5 responsive proof
        → T062–T069 final review and baseline closure
```

- US1 and US2 are P1 slices but share the foundational coverage contract.
- US3 and US4 can be reviewed independently after shared patterns stabilize.
- US5 integrates all prior stories and therefore follows their implementation.
- Baseline closure cannot precede complete green evidence and owner final approval.

## Parallel Opportunities

- T004, T005, T006, and T007 use independent fixture/contract concerns.
- Within US1, frontend contract tasks T012–T014 can run beside backend T015–T016.
- Within US2, backend T026–T027 can run beside frontend T028–T029.
- Within US3, configuration contract families T037–T039 can run beside T040.
- T047–T049 cover separate Ask/Explorer/backend trace surfaces.
- T055–T057 prepare independent responsive, boundary, and review evidence.
- T062 and T063 are independent documentation/inventory work before final gates.
- T070–T072 restore the specified company lifecycle-action hierarchy.

## Implementation Strategy

1. Freeze exact topology and ownership before UI work.
2. Deliver US1 as the operational MVP and review it independently.
3. Add finance/Evidence, configuration, and support families sequentially.
4. Perform one cross-surface responsive audit only after family behavior is stable.
5. Close only `016/FR-006` after final owner approval.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-002 | T004–T010 | T011, T060 | Pending |
| FR-003 | T012 | T017, T025 | Pending |
| FR-004 | T013–T014, T016 | T018–T019, T022–T025 | Pending |
| FR-005 | T015 | T020–T021, T025 | Pending |
| FR-006 | T026–T028 | T030–T033, T036 | Pending |
| FR-007 | T029 | T034–T036 | Pending |
| FR-008 | T037, T040 | T041, T045–T046 | Pending |
| FR-009 | T038 | T042, T045–T046 | Pending |
| FR-010 | T039–T040 | T043, T045–T046 | Pending |
| FR-011 | T038, T070 | T044, T046, T071–T072 | Complete |
| FR-012 | T047–T048 | T050–T051, T054 | Pending |
| FR-013 | T007, T014, T029, T049 | T021, T023, T034, T052, T054 | Pending |
| FR-014 | T006, T012–T013, T028, T037, T047, T055 | T017, T019, T024, T033, T045, T053, T058–T061 | Pending |
| FR-015–FR-016 | T006, T056 | T024, T035, T045, T053, T058–T061 | Pending |
| FR-017 | T057 | T059, T063, T066 | Pending |
| FR-018 | T004–T008 | T060 | Pending |
| FR-019 | T067, T069 | T068 | Pending |
| DR-001–DR-004 | T007, T015–T016, T026–T027, T029, T040, T049 | T018, T020–T023, T030–T034, T041–T043, T052, T062, T066 | Pending |
| DR-005 | T057 | T063, T066, T069 | Pending |
| DR-006 | T005, T008, T010 | T011, T066 | Pending |
| SC-001–SC-009 | T004–T069 | T025, T036, T046, T054, T060–T069 | Pending |

## Phase 9: Company Lifecycle Action Hierarchy

- [x] T070 [US3] [FR-011] Add a failing configuration contract that rejects Archive in the company page header and requires it in the General Danger zone
- [x] T071 [US3] [FR-011] Move the active-company Archive button into the existing Danger zone while retaining permanent deletion for archived companies
- [x] T072 [US3] [FR-011] Run Product Web contracts, translation audit, production build, Spec policy, and final diff review
