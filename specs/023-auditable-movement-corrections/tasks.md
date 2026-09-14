---
description: "Requirement-traceable implementation tasks for auditable Movement corrections"
---

# Tasks: Auditable Movement Corrections

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/movement-correction.md`, and `quickstart.md`
**Gate**: Constitution Check passed, specification and plan approved, and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the behavior they prove.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Record product-owner specification approval and close clarification markers in `specs/023-auditable-movement-corrections/spec.md` and `specs/023-auditable-movement-corrections/checklists/requirements.md`
- [x] T002 Record product-owner plan approval after all Constitution Check rows pass in `specs/023-auditable-movement-corrections/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve every CRITICAL cross-artifact finding in `specs/023-auditable-movement-corrections/`

## Phase 2: Foundational Persistence and Shared Execution Boundary

**Goal**: Establish the additive relation and preserve one reusable Movement validation path before story behavior is implemented.

- [x] T004 [DR-004] Add failing migration/model parity, uniqueness, distinct-role, tenant ownership, and guarded-downgrade tests in `packages/reality-core/tests/test_migrations.py` and `packages/reality-core/tests/test_movement_corrections.py`
- [x] T005 [DR-004] Add `MovementCorrection` with tenant, role-link, reason, UTC actor-context, and fingerprint constraints in `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0028_movement_corrections.py`
- [x] T006 [DR-005] Refactor normal Movement normalization, validation, append, Reservation consumption, status reconciliation, event emission, and commit boundaries without behavior change in `packages/reality-core/src/reality/services/core.py`

**Checkpoint**: Existing Movement tests remain green and the empty migration round-trip is valid.

## Phase 3: User Story 1 — Void an Incorrect Movement (P1)

**Goal**: Preserve an original and atomically append one exact compensation so its stock and fulfilment effects no longer count.

**Independent Test**: Void each supported Movement type and prove exact net stock/fulfilment restoration, immutable history, one audit chain/event, safe retries, and tenant isolation.

### Failing proof

- [x] T007 [P] [US1] [FR-001] [FR-002] [FR-004] [FR-005] [DR-001] [DR-002] Add failing every-type void, immutable-original, exact-inverse, direct-link, required-reason, and actor/time tests in `packages/reality-core/tests/test_movement_corrections.py`
- [x] T008 [P] [US1] [FR-002] [FR-007] [FR-009] [FR-010] Add failing explicit correction-type, inverse-specific direction, compensation-target, later-dependent stock/identity, location, quantity, hold, and tracking-invariant tests in `packages/reality-core/tests/test_movement_corrections.py`
- [x] T009 [P] [US1] [FR-011] [FR-012] [DR-005] Add failing shipment/receipt fulfilment, Commitment status, physical inventory, and unchanged Reservation-history stories in `packages/reality-core/tests/test_inventory_and_fulfillment.py`
- [x] T010 [P] [US1] [FR-011] Add failing net lot/serial/handling-unit location, operational-exception, and projection refresh stories in `packages/reality-core/tests/test_inventory_tracking_reservations.py`, `packages/reality-core/tests/operational_exceptions/test_derivation.py`, and `packages/reality-core/tests/test_materialized_projections.py`
- [x] T011 [P] [US1] [FR-006] [FR-008] Add failing canonical retry, divergent/concurrent correction, relation uniqueness, and injected event-failure rollback tests in `packages/reality-core/tests/test_movement_corrections.py`
- [x] T012 [P] [US1] [FR-013] [FR-014] [DR-003] [DR-005] Add failing immutable-source, correction-evidence, foreign-original, and foreign-reference non-disclosure tests in `packages/reality-core/tests/test_movement_corrections.py` and `packages/reality-core/tests/tenant_isolation/test_families.py`
- [x] T013 [P] [US1] [FR-017] Add failing exact `movement.corrected` count, subject, payload, invalidation, and rollback tests in `packages/reality-core/tests/test_business_events.py`

### Implementation

- [x] T014 [US1] [FR-001] [FR-002] [FR-004] [FR-005] [FR-006] [FR-007] [FR-008] [FR-009] [FR-010] [FR-013] [FR-014] [DR-001] [DR-002] [DR-003] [DR-005] Implement tenant-safe snapshot, canonical revision/fingerprint excluding actor context, preview, row lock, explicit correction-type inverse without duplicated Commitment/Source provenance, relation, retry/conflict, dependency guard, audit, and one-commit void correction in `packages/reality-core/src/reality/services/core.py`
- [x] T015 [US1] [FR-011] [FR-012] [DR-001] Implement one shared correction-aware fulfilment expression and affected Commitment-status reconciliation without Reservation mutation in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/web/read_models.py`
- [x] T016 [US1] [FR-011] [DR-001] Replace newest-row identity inference with net physical-leg derivation and make operational-exception/projection reads correction-aware in `packages/reality-core/src/reality/services/core.py`, `packages/reality-core/src/reality/services/exceptions.py`, and `packages/reality-core/src/reality/services/projections.py`
- [x] T017 [US1] [FR-017] Register and emit exactly one atomic `movement.corrected` event with the required consumer invalidations in `packages/reality-core/config/business_event_catalog.yaml` and `packages/reality-core/src/reality/services/core.py`
- [x] T018 [US1] Run the User Story 1 focused PostgreSQL acceptance slice and record observed results in `specs/023-auditable-movement-corrections/quickstart.md`

**Checkpoint**: User Story 1 independently closes the void path without an API or UI dependency.

## Phase 4: User Story 2 — Replace a Movement with Intended Reality (P1)

**Goal**: Atomically add a normally validated replacement after exact compensation and derive only the intended net result.

**Independent Test**: Replace quantity, location, Commitment, tracking identity, source, and occurrence time; prove all-or-nothing validation and a correctable replacement chain.

### Failing proof

- [x] T019 [P] [US2] [FR-003] [FR-007] Add failing quantity/location/time replacement, void-versus-replace, replacement-chain, and compensation-noncorrectable tests in `packages/reality-core/tests/test_movement_corrections.py`
- [x] T020 [P] [US2] [FR-003] [FR-009] [FR-013] Add failing replacement Commitment, SourceRecord, lot, serial, handling-unit, stock, hold, and cross-tenant validation tests in `packages/reality-core/tests/test_movement_corrections.py`
- [x] T021 [P] [US2] [FR-006] [FR-008] Add failing replacement-validation rollback, identical replacement retry, and divergent second replacement tests in `packages/reality-core/tests/test_movement_corrections.py`
- [x] T022 [P] [US2] [FR-011] [FR-012] Add failing old/new Commitment fulfilment/status, inventory projection, identity location, and unchanged Reservation-history replacement stories in `packages/reality-core/tests/test_inventory_and_fulfillment.py` and `packages/reality-core/tests/test_inventory_tracking_reservations.py`

### Implementation

- [x] T023 [US2] [FR-003] [FR-006] [FR-007] [FR-008] [FR-009] [FR-013] Extend shared preview/execute behavior with optional normally validated replacement, post-compensation validation state, correction chaining, and atomic rollback in `packages/reality-core/src/reality/services/core.py`
- [x] T024 [US2] [FR-011] [FR-012] Reconcile original and replacement Commitment, projection, exception, and tracked-identity effects exactly once in `packages/reality-core/src/reality/services/core.py`, `packages/reality-core/src/reality/services/exceptions.py`, and `packages/reality-core/src/reality/web/read_models.py`
- [x] T025 [US2] Run the User Story 2 focused PostgreSQL acceptance slice and record observed results in `specs/023-auditable-movement-corrections/quickstart.md`

**Checkpoint**: Service consumers can void or replace one Movement with deterministic net results.

## Phase 5: User Story 3 — Preview, Confirm, and Explain (P2)

**Goal**: Expose the same server-derived preview, explicit confirmation, retry behavior, and correction chain through operational interfaces.

**Independent Test**: Preview and confirm through each supported boundary, then inspect any chain member and reproduce the same net result and audit context.

### Failing proof

- [x] T026 [P] [US3] [FR-015] Add failing snapshot, preview, execute, abort/no-effect, replay, stale-refresh, validation, and tenant-safe API contract tests in `packages/reality-core/tests/test_master_data_api.py`
- [x] T027 [P] [US3] [FR-016] Add failing Movement register role/status and Inspector chain-from-every-member tests in `packages/reality-core/tests/test_master_data_api.py`
- [x] T028 [P] [US3] [FR-015] Add failing CLI preview, abort, confirmation, and explicit `--yes` tests in `packages/reality-core/tests/test_cli.py`
- [x] T029 [P] [US3] [FR-015] [DR-005] Add failing application-tool proposal-before-effect, approved execution, MCP propose-only, replay, and tenant tests in `packages/reality-core/tests/test_application_tools.py` and `packages/reality-core/tests/test_ai_mcp.py`
- [x] T030 [P] [US3] [FR-016] [FR-017] Add failing full-chain event/source/audit explanation and catalog drift tests in `packages/reality-core/tests/test_business_events.py` and `packages/reality-core/tests/test_application_catalog.py`
- [x] T031 [P] [US3] [FR-015] [FR-016] Add failing EN/DE/NL/ES correction-label, preview, confirmation, guidance, and protected-content localization contracts in `apps/web/scripts/localization-contract.test.mjs` and `apps/web/scripts/product-boundary.test.mjs`

### Implementation

- [x] T032 [US3] [FR-015] Implement correction snapshot, preview, and execute transport models/endpoints with conflict and safe guidance mapping in `packages/reality-core/src/reality/web/api.py`
- [x] T033 [US3] [FR-016] Add tenant-safe role/status/chain read models and complete Movement Inspector explanation from every member in `packages/reality-core/src/reality/web/read_models.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T034 [US3] [FR-015] Implement CLI preview, confirmation, abort, and explicit automation behavior through shared services in `packages/reality-core/src/reality/cli/app.py`
- [x] T035 [US3] [FR-015] [DR-005] Implement the mutating application tool plus Chat/MCP proposal-only exposure through existing approval execution in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T036 [US3] [FR-015] [FR-016] Implement typed Web client calls, register badges/action, server preview, explicit confirmation, stale refresh, and Inspector links in `apps/web/src/api.ts` and `apps/web/src/App.tsx`
- [x] T037 [US3] [FR-015] [FR-016] Add complete EN/DE/NL/ES correction copy and responsive/mobile presentation in `apps/web/src/localization.tsx` and `apps/web/src/App.tsx`
- [x] T038 [US3] [FR-015] [FR-016] [DR-003] [DR-005] Update Movement, data-model, architecture, CLI, Web, and traceability contracts in `docs/features/movements.md`, `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/CLI_SPEC.md`, and `docs/WEB_SPEC.md`
- [x] T039 [US3] Run API/Web/CLI/tool parity plus manual EN/DE/NL/ES desktop/mobile acceptance and record observed results in `specs/023-auditable-movement-corrections/quickstart.md`

**Checkpoint**: All operational surfaces expose one correction meaning and the complete chain is explainable.

## Final Phase: Cross-Cutting Review and Baseline Closure

- [x] T040 [DR-004] Run migration upgrade/downgrade/upgrade, guarded-downgrade, and schema/model parity checks and record results in `specs/023-auditable-movement-corrections/quickstart.md`
- [x] T041 Run all focused correction, inventory, tracking, exception, projection, event, API, CLI, tool, MCP, catalog, and tenant-isolation tests listed in `specs/023-auditable-movement-corrections/quickstart.md`
- [x] T042 Run Ruff and the complete PostgreSQL backend suite and record exact results in `specs/023-auditable-movement-corrections/quickstart.md`
- [x] T043 Run the Web production build, EN/DE/NL/ES audit/tests, and responsive manual review and record exact results in `specs/023-auditable-movement-corrections/quickstart.md`
- [x] T044 Review the final diff against the Constitution, `spec.md`, `plan.md`, all FR/DR mappings, shortest links, tenant boundaries, migration safety, and unrelated concurrent work; record final owner approval in `specs/023-auditable-movement-corrections/checklists/requirements.md`
- [x] T045 [FR-001] [FR-017] After T044 owner approval, run the final Spec policy/traceability audit and mark `009/FR-009` plus only its coverage-matrix gap verified in `specs/009-inventory-execution/spec.md` and `docs/SPEC_COVERAGE_MATRIX.md`

## Dependencies

```text
T001–T003 specification/design gates
  → T004–T006 foundational persistence/shared boundary
    → T007–T018 US1 exact void (MVP)
      → T019–T025 US2 optional replacement
        → T026–T039 US3 interfaces and explanation
          → T040–T045 final gates and baseline closure
```

- US1 is the MVP and proves immutable correction semantics without UI dependency.
- US2 depends on the US1 compensation/retry boundary and adds replacement only.
- US3 depends on stable US1/US2 contracts so adapters remain translation-only.
- Within each failing-proof subsection, `[P]` tasks may run in parallel before the
  corresponding implementation tasks.

## Parallel Execution Examples

### User Story 1

- T007, T008, T009, T010, T011, T012, and T013 target separable proof concerns and may
  run concurrently after T006.
- After T014 establishes the correction transaction, T015, T016, and T017 touch distinct
  derived/event concerns and may be coordinated in parallel with overlap review.

### User Story 2

- T019–T022 may run concurrently against the approved service contract.
- T023 precedes T024 because derived replacement behavior requires appended replacement records.

### User Story 3

- T026–T031 may run concurrently across API, Inspector, CLI, tools/MCP, events/catalogs,
  and Web contract tests.
- After stable service/API contracts, T033, T034, T035, and T037 may proceed in parallel;
  T036 integrates the final typed Web contract.

## Implementation Strategy

1. Deliver the US1 service-level MVP: exact void, audit, derivation, retry, and isolation.
2. Add optional replacement as a separately proven increment.
3. Expose server preview and explicit confirmation through adapters only after semantics stabilize.
4. Close `009/FR-009` only after automated, manual, migration, and owner review gates pass.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-002 | T007–T008 | T014, T045 | Verified |
| FR-003 | T019–T020 | T023 | Verified |
| FR-004–FR-005 | T007 | T014 | Verified |
| FR-006 | T011, T021 | T014, T023 | Verified |
| FR-007–FR-008 | T008, T011, T019, T021 | T014, T023 | Verified |
| FR-009–FR-010 | T008, T020 | T014, T023 | Verified |
| FR-011–FR-012 | T009–T010, T022 | T015–T016, T024 | Verified |
| FR-013–FR-014 | T012, T020 | T014, T023 | Verified |
| FR-015 | T026, T028–T029, T031 | T032, T034–T038 | Verified |
| FR-016 | T027, T030–T031 | T033, T036–T038 | Verified |
| FR-017 | T013, T030 | T017, T045 | Verified |
| DR-001–DR-003 | T007, T009–T010, T012 | T014–T016, T038 | Verified |
| DR-004 | T004 | T005, T040 | Verified |
| DR-005 | T009, T012, T029 | T006, T014, T032, T035, T038 | Verified |
