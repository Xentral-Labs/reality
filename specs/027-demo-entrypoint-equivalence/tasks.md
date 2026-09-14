# Tasks: Demo Entrypoint Equivalence

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/demo-entrypoints.md`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the behavior they prove. `015/FR-010` remains open
until final product-owner approval.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm product-owner specification approval and zero clarification markers in `specs/027-demo-entrypoint-equivalence/spec.md` and `specs/027-demo-entrypoint-equivalence/checklists/requirements.md`
- [x] T002 Confirm product-owner plan approval and all Constitution Check rows PASS in `specs/027-demo-entrypoint-equivalence/plan.md`
- [x] T003 Run `$speckit-analyze` across `specs/027-demo-entrypoint-equivalence/spec.md`, `specs/027-demo-entrypoint-equivalence/plan.md`, and `specs/027-demo-entrypoint-equivalence/tasks.md`; resolve all CRITICAL/HIGH findings before implementation

## Phase 2: Shared Failing Proof and Vocabulary

- [x] T004 [US1] [FR-001] [FR-004] Run one real guided demo, inventory every directly or indirectly produced record family, and add a failing exact six-section manifest/multiplicity test in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T005 [P] [US1] [FR-006] [FR-013] Add failing canonical alias, narrow-normalization, topology-drift, and categorized-diagnostic unit cases in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T006 [P] [US1] [DR-001] [DR-002] [DR-003] Add failing Source → Evidence → Reality traversal and derived-authority assertions in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T007 [P] [US3] [FR-014] Add a scope-regression inventory proving guided demo, normal month, Chat, and bootstrap retain separate entry contracts in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T008 [FR-001] Define the explicit guided-demo manifest version and its inventory-driven drift rule in `docs/DEMO_SPEC.md`

**Checkpoint**: Manifest vocabulary fails because no complete cross-entrypoint harness or Web demo path exists.

## Phase 3: User Story 1 — Equivalent Guided Demo Outcome (P1, MVP)

**Goal**: Real interactive CLI, CLI auto, and authenticated Web/API executions produce
the same complete authoritative guided-demo state.

**Independent Test**: Run the three entrypoints in isolated empty tenants and compare
all six categorized manifests plus representative shortest-link traversal.

- [x] T009 [US1] [FR-002] [FR-003] Add a failing interactive CLI execution fixture that confirms the real `demo` command in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T010 [P] [US1] [FR-002] [FR-003] Add a failing CLI `--auto` execution fixture using the real command adapter in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T011 [P] [US1] [FR-002] [FR-003] Add a failing authenticated company-with-demo HTTP execution fixture in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T012 [US1] [FR-001] [FR-004] [FR-005] Implement fresh tenant-scoped manifest reads covering every inventoried family plus reference, Source, Evidence, Reality, derived financial-zero, and explanation sections in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T013 [US1] [FR-006] [FR-013] Implement semantic ID aliases, explicit date/time/order normalization, and per-section mismatch output in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T014 [US1] [DR-001] [DR-002] [DR-003] Implement shortest-link topology and Reality-derived inventory/fulfilment assertions in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T015 [US1] [FR-002] Expose the optional guided-demo choice through the authenticated company adapter while delegating to `ensure_demo` in `packages/reality-core/src/reality/web/api.py`
- [x] T016 [US1] [FR-002] Fix `packages/reality-core/src/reality/cli/app.py` or `packages/reality-core/src/reality/services/core.py` only if real adapter comparison exposes drift; otherwise record no change in `specs/027-demo-entrypoint-equivalence/quickstart.md`
- [x] T017 [US1] [FR-003] Compare all three real execution manifests for exact canonical equality in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T018 [US1] [DR-004] Assert the complete normalized Shopify payload and rerun source identity/version behavior in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T019 [US1] [FR-003] Run the independent three-entrypoint acceptance proof and record exact results in `specs/027-demo-entrypoint-equivalence/quickstart.md`

**Checkpoint**: The backend MVP proves identical complete demo state across three real adapters.

## Phase 4: User Story 2 — Explicit Demo or Empty Company Choice (P1)

**Goal**: Web onboarding clearly separates empty-company creation from a confirmed demo.

**Independent Test**: Exercise both authenticated request variants and prove actual Web
wiring, cancellation/no-request behavior, and success selection of the returned tenant.

- [x] T020 [P] [US2] [FR-007] [FR-008] Add a failing structural contract for distinct actions and pre-request confirmation in `apps/web/scripts/demo-entrypoint-contract.test.mjs`
- [x] T021 [P] [US2] [FR-009] Add a failing structural contract for API delegation, returned-tenant selection, and normal product routing in `apps/web/scripts/demo-entrypoint-contract.test.mjs`
- [x] T022 [P] [US2] [FR-010] Add failing authenticated HTTP assertions that omitted/false demo choice creates an empty company in `packages/reality-core/tests/test_user_access.py`
- [x] T023 [P] [US2] [FR-008] Add failing Web contract assertions that cancellation issues no company/demo request and renders API-owned failure in `apps/web/scripts/demo-entrypoint-contract.test.mjs`
- [x] T024 [US2] [FR-007] [FR-008] Implement distinct empty-company and guided-demo actions with preview/confirmation in `apps/web/src/App.tsx`
- [x] T025 [US2] [FR-009] [FR-010] Extend the Product Web company client with an explicit optional demo choice while preserving the empty default in `apps/web/src/api.ts`
- [x] T026 [US2] [FR-008] [FR-009] Wire only the confirmed demo action to the API client, refresh bootstrap with the returned tenant, and expose normal inspection routes in `apps/web/src/App.tsx`
- [x] T027 [US2] [FR-007] [FR-010] Add required English onboarding copy and complete `de`, `nl`, and `es` translations in `apps/web/src/localization.tsx`
- [x] T028 [US2] [FR-007] Add minimal responsive styling for the two onboarding choices and confirmation state in `apps/web/src/tailwind.css`
- [x] T029 [US2] [FR-007] [FR-008] [FR-009] [FR-010] Run the independent Web choice/confirmation acceptance proof and record exact results in `specs/027-demo-entrypoint-equivalence/quickstart.md`

**Checkpoint**: Empty onboarding remains empty; sample data is created only by a distinct confirmed action.

## Phase 5: User Story 3 — Safety and Durable Drift Detection (P2)

**Goal**: Cancellation, existing state, reruns, foreign access, and future drift fail safely and visibly.

**Independent Test**: Exercise each safety boundary and deliberately perturb every
canonical category to verify diagnostic failures.

- [x] T030 [P] [US3] [FR-011] Add populated-tenant, completed-rerun, and injected partial-failure tests proving preserved state, truthful errors, and no safe-retry claim in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T031 [P] [US3] [FR-012] [DR-005] Add authenticated two-user tests proving creator ownership and foreign demo inspection behaves as not found in `packages/reality-core/tests/test_user_access.py`
- [x] T032 [P] [US3] [FR-008] Add interactive CLI cancellation proof with zero demo records in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T033 [P] [US3] [FR-013] Add deliberate record, relationship, payload, derived-value, and explanation drift cases with category assertions in `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- [x] T034 [US3] [FR-011] [DR-004] Correct shared `ensure_demo` idempotency/provenance only if the failing safety tests expose drift in `packages/reality-core/src/reality/services/core.py`
- [x] T035 [US3] [FR-012] [DR-005] Correct authorization or tenant lookup only if focused tests expose drift in `packages/reality-core/src/reality/web/app.py`
- [x] T036 [US3] [FR-014] Run existing normal-month, Chat confirmation, and bootstrap regressions without folding them into the parity manifest in `packages/reality-core/tests/scenarios/test_normal_month.py`, `packages/reality-core/tests/test_chat_confirmation.py`, and `packages/reality-core/tests/test_bootstrap.py`
- [x] T037 [US3] Run the independent safety/drift acceptance proof and record exact results in `specs/027-demo-entrypoint-equivalence/quickstart.md`

**Checkpoint**: Unsafe behavior and every meaningful drift category have deterministic focused failures.

## Final Phase: Cross-Cutting Review and Baseline Closure

- [x] T038 [DR-001] [DR-002] [DR-004] Clarify the versioned guided-demo outcome, immutable source, Reality derivation, and rerun semantics in `docs/DEMO_SPEC.md` and `docs/features/demo.md`
- [x] T039 [DR-006] Record pre/post model and migration inventories, confirm no schema change, and record final evidence in `specs/027-demo-entrypoint-equivalence/quickstart.md`
- [x] T040 Run Ruff, focused PostgreSQL CLI/API/Web parity tests, and the complete PostgreSQL suite; record exact results in `specs/027-demo-entrypoint-equivalence/quickstart.md`
- [x] T041 Run Product Web demo contract, localization contract tests, production build, and responsive/manual review; record exact results in `specs/027-demo-entrypoint-equivalence/quickstart.md`
- [x] T042 Review the final diff against Constitution, `spec.md`, `plan.md`, all FR/DR mappings, tenant boundaries, shortest links, and unrelated concurrent work in `specs/027-demo-entrypoint-equivalence/checklists/requirements.md`
- [x] T043 [FR-015] Before baseline closure, add a regression expecting `015/FR-010` verified, its coverage row absent, and both unrelated `016` gaps retained in `packages/reality-core/tests/test_spec_policy.py`
- [x] T044 [FR-015] After product-owner final approval, mark only `015/FR-010` verified in `specs/015-demo-scenarios/spec.md` and remove only its row from `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T045 Run final Spec policy, traceability, checklist, and `git diff --check` gates; record exact results in `specs/027-demo-entrypoint-equivalence/quickstart.md`

## Dependencies

```text
T001–T003 specification/design gates
  → T004–T008 shared failing proof
    → T009–T019 US1 backend parity MVP
      → T020–T029 US2 explicit Web onboarding
        → T030–T037 US3 safety and drift detection
          → T038–T045 final review and baseline closure
```

- US1 is the MVP and establishes the manifest and company-with-demo adapter.
- US2 depends on the Web/API contract from US1 but independently proves explicit choice.
- US3 depends on the stable manifest but independently proves safety and future drift.
- Baseline closure cannot precede green complete evidence and final owner approval.

## Parallel Execution Examples

- **Foundation**: T005, T006, T007, and T008 touch independent proof/document sections.
- **US1**: T009–T011 define separate real entrypoint fixtures; T012–T014 then integrate them.
- **US2**: T020–T023 define Web/API failures in separate files before T024–T028 implementation.
- **US3**: T030–T033 cover independent safety categories before conditional fixes.
- **Final gates**: T040 and T041 may run in parallel after documentation is complete.

## Implementation Strategy

1. Freeze the exact guided-demo manifest and normalization boundary.
2. Prove real interactive CLI and auto state first.
3. Add the smallest authenticated Web company-with-demo adapter and compare it.
4. Expose the explicit confirmed Web choice without changing empty-company defaults.
5. Lock cancellation, populated/rerun, tenant, provenance, and diagnostic drift behavior.
6. Close only `015/FR-010` after final owner approval.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T004, T012 | T008, T038 | Complete |
| FR-002–FR-003 | T009–T011, T017, T019 | T015–T016 | Complete |
| FR-004–FR-005 | T004, T012, T017 | T038 | Complete |
| FR-006 | T005, T013, T017 | T038 | Complete |
| FR-007 | T020, T029 | T024, T027–T028 | Complete |
| FR-008–FR-009 | T020–T023, T029, T032 | T024–T026 | Complete |
| FR-010 | T022, T029 | T025 | Complete |
| FR-011 | T030, T037 | T034, T038 | Complete |
| FR-012 | T031, T037 | T035 | Complete |
| FR-013 | T005, T033, T037 | T013 | Complete |
| FR-014 | T007, T036 | T038 | Complete |
| FR-015 | T043, T045 | T044 | Complete |
| DR-001–DR-003 | T006, T014, T017 | T038, T042 | Complete |
| DR-004 | T018, T030 | T034, T038 | Complete |
| DR-005 | T031 | T035, T042 | Complete |
| DR-006 | T008, T039, T045 | T042 | Complete |
| SC-001–SC-008 | T004–T045 | T038, T042, T044 | Complete |
