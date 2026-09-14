---
description: "Requirement-traceable implementation tasks for auditable ledger reversals"
---

# Tasks: Auditable Ledger Reversals

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/ledger-reversal.md`, and `quickstart.md`
**Gate**: Constitution Check passed, specification and plan approved, and no unresolved
`[NEEDS CLARIFICATION]`

All artifacts MUST be written in English. Tests precede the behavior they prove.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Record product-owner specification approval in `specs/024-auditable-ledger-reversals/spec.md` and `specs/024-auditable-ledger-reversals/checklists/requirements.md`
- [x] T002 Record product-owner plan approval after all Constitution Check rows pass in `specs/024-auditable-ledger-reversals/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve every CRITICAL cross-artifact finding in `specs/024-auditable-ledger-reversals/`

## Phase 2: Foundational Persistence and Shared Posting Boundary

**Goal**: Establish the additive relation and reusable non-committing group append and
active-allocation semantics before story behavior.

- [ ] T004 [DR-001] [DR-002] Add failing migration/model parity, per-role uniqueness, cross-role group-lock concurrency, role-distinctness, tenant ownership, and guarded-downgrade tests in `packages/reality-core/tests/test_migrations.py` and `packages/reality-core/tests/test_ledger_reversals.py`
- [x] T005 [DR-001] [DR-002] Add `LedgerReversal` and additive guarded migration `0029_ledger_reversals.py` in `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0029_ledger_reversals.py`
- [x] T006 [DR-005] Refactor balanced posting-group validation, append, event, and commit boundaries without changing public posting behavior in `packages/reality-core/src/reality/services/core.py`

**Checkpoint**: Existing Ledger tests remain green and empty migration round-trip passes.

## Phase 3: User Story 1 — Reverse an Erroneous Posting Group (P1)

**Goal**: Preserve one complete group and atomically append one exact inverse group.

**Independent Test**: Reverse every supported group shape and prove immutable originals,
exact balance cancellation, durable audit, safe retry, and tenant isolation.

### Failing proof

- [ ] T007 [P] [US1] [FR-001] [FR-002] [FR-003] Add failing complete-group, every-shape, immutable-original, exact-inverse, balance, currency, party, and rejection stories in `packages/reality-core/tests/test_ledger_reversals.py`
- [ ] T008 [P] [US1] [FR-004] [FR-005] [DR-002] [DR-004] Add failing direct relation, required reason, UTC actor/time, opaque role, and non-duplicated Document/Source provenance stories in `packages/reality-core/tests/test_ledger_reversals.py`
- [ ] T009 [P] [US1] [FR-006] [FR-007] [FR-008] Add failing canonical retry, divergent/concurrent reversal, reversing-target rejection, uniqueness, and injected relation/event rollback stories in `packages/reality-core/tests/test_ledger_reversals.py`
- [ ] T010 [P] [US1] [FR-011] Add failing Document, SourceRecord, Movement, Reservation, Commitment, fulfilment, and inventory non-mutation story in `packages/reality-core/tests/test_ledger_reversals.py`
- [ ] T011 [P] [US1] [FR-016] Add failing exact `ledger.reversed` count, subject, payload, invalidations, replay, and rollback tests in `packages/reality-core/tests/test_business_events.py`
- [ ] T012 [P] [US1] [FR-017] [DR-005] Add failing foreign-group, foreign-member, cross-tenant relation/reference, and non-disclosure tests in `packages/reality-core/tests/test_ledger_reversals.py` and `packages/reality-core/tests/tenant_isolation/test_families.py`

### Implementation

- [x] T013 [US1] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [DR-001] [DR-002] Implement tenant-safe group load/integrity validation, snapshot/revision, exact inverse builder, and relation roles in `packages/reality-core/src/reality/services/core.py`
- [x] T014 [US1] [FR-006] [FR-007] [FR-008] Implement row locking, canonical fingerprint excluding actor, identical replay, conflict/race backstop, one-commit reversal, and rollback in `packages/reality-core/src/reality/services/core.py`
- [x] T015 [US1] [FR-011] Preserve all non-ledger state and reconcile only derived finance effects in `packages/reality-core/src/reality/services/core.py`
- [x] T016 [US1] [FR-016] Register and atomically emit `ledger.reversed` with complete financial consumer invalidations in `packages/reality-core/config/business_event_catalog.yaml` and `packages/reality-core/src/reality/services/core.py`
- [x] T017 [US1] [FR-017] Register reversal read/mutation/tool tenant classes and executable query evidence in `packages/reality-core/config/tenant_isolation_catalog.yaml`
- [x] T018 [US1] Run User Story 1 PostgreSQL acceptance and record exact results in `specs/024-auditable-ledger-reversals/quickstart.md`

**Checkpoint**: The service-level complete reversal is independently usable without UI.

## Phase 4: User Story 2 — Reconcile Settlement and Financial Views (P1)

**Goal**: Retain allocation history while every finance consumer derives the same active
settlement and reversal-aware result.

**Independent Test**: Reverse payment-side and invoice-side groups with partial, full,
many-to-many allocations and compare all financial views and unaffected physical state.

### Failing proof

- [ ] T019 [P] [US2] [FR-009] [DR-003] Add failing payment-side, invoice-side, partial/full, multi-allocation, immutable-history, and released-counterparty settlement stories in `packages/reality-core/tests/test_ledger_reversals.py` and `packages/reality-core/tests/test_ledger.py`
- [ ] T020 [P] [US2] [FR-010] Add failing account/party/running/open-item/payment/control/journal/posting-group parity and role/status stories in `packages/reality-core/tests/test_ledger.py`
- [ ] T021 [P] [US2] [FR-009] [FR-010] Add failing unmatched-financial-event clearing/reappearance and derived explanation stories in `packages/reality-core/tests/operational_exceptions/test_derivation.py` and `packages/reality-core/tests/operational_exceptions/test_explanation.py`
- [ ] T022 [P] [US2] [FR-009] [FR-010] Add failing projection refresh, checkpoint, and reversal invalidation stories in `packages/reality-core/tests/test_materialized_projections.py`
- [ ] T023 [P] [US2] [FR-011] [DR-003] Add failing settlement-history-versus-operational-state and fulfilment/inventory independence story in `packages/reality-core/tests/test_ledger_reversals.py`

### Implementation

- [x] T024 [US2] [FR-009] [DR-003] Implement one shared active-allocation semantic and replace settlement/open/payment calculations in `packages/reality-core/src/reality/services/core.py`
- [x] T025 [US2] [FR-010] Add reversal-aware allocation status and posting-group roles to finance read models in `packages/reality-core/src/reality/web/read_models.py` and `packages/reality-core/src/reality/services/core.py`
- [x] T026 [US2] [FR-009] [FR-010] Make financial exceptions and projections consume the shared reversal-aware settlement semantics in `packages/reality-core/src/reality/services/exceptions.py` and `packages/reality-core/src/reality/services/projections.py`
- [x] T027 [US2] Run User Story 2 PostgreSQL acceptance and record exact results in `specs/024-auditable-ledger-reversals/quickstart.md`

**Checkpoint**: Every backend financial consumer reconciles from the same reversal truth.

## Phase 5: User Story 3 — Preview, Confirm, and Explain (P2)

**Goal**: Expose shared preview, explicit confirmation, retry, and complete explanation
through every supported operational interface.

**Independent Test**: Preview/abort/confirm/retry/stale through each boundary and inspect
either role to reproduce one chain and identical financial results.

### Failing proof

- [x] T028 [P] [US3] [FR-012] [FR-013] Add failing snapshot, preview, execute, abort/no-effect, replay, stale, validation, and tenant-safe API contract tests in `packages/reality-core/tests/test_master_data_api.py`
- [ ] T029 [P] [US3] [FR-014] Add failing CLI preview, abort, confirmation, and explicit `--yes` tests in `packages/reality-core/tests/test_cli.py`
- [ ] T030 [P] [US3] [FR-014] [DR-005] Add failing application-tool proposal-before-effect, approved execution, MCP propose-only, replay, and tenant tests in `packages/reality-core/tests/test_application_tools.py` and `packages/reality-core/tests/test_ai_mcp.py`
- [ ] T031 [P] [US3] [FR-015] Add failing journal roles, inactive allocation presentation, and Inspector chain-from-either-role tests in `packages/reality-core/tests/test_master_data_api.py`
- [ ] T032 [P] [US3] [FR-015] [FR-016] Add failing full-chain event/Evidence/allocation/net-effect explanation plus event/command catalog drift tests in `packages/reality-core/tests/test_business_events.py` and `packages/reality-core/tests/test_application_catalog.py`
- [ ] T033 [P] [US3] [FR-014] [FR-015] Add failing EN/DE/NL/ES reversal-label, preview, confirmation, guidance, role, and protected-content contracts in `apps/web/scripts/localization-contract.test.mjs` and `apps/web/scripts/product-boundary.test.mjs`

### Implementation

- [x] T034 [US3] [FR-012] [FR-013] Implement snapshot, preview, and execute transport models/endpoints with conflict and safe guidance in `packages/reality-core/src/reality/web/api.py`
- [x] T035 [US3] [FR-014] Implement CLI preview, confirmation, abort, and explicit automation through shared services in `packages/reality-core/src/reality/cli/app.py`
- [x] T036 [US3] [FR-014] [DR-005] Implement mutating application tool, command catalog entry, and Chat/MCP proposal-only exposure through existing approval in `packages/reality-core/src/reality/tools/application.py`, `packages/reality-core/src/reality/mcp/catalog.py`, and `packages/reality-core/config/command_catalog.yaml`
- [x] T037 [US3] [FR-015] Implement journal/allocation roles and complete Inspector traversal from either group in `packages/reality-core/src/reality/web/api.py` and `packages/reality-core/src/reality/web/read_models.py`
- [x] T038 [US3] [FR-014] [FR-015] Implement typed Web calls, action, server preview, confirmation, stale refresh, role badges, Inspector links, responsive layout, and EN/DE/NL/ES copy in `apps/web/src/api.ts`, `apps/web/src/App.tsx`, and `apps/web/src/localization.tsx`
- [x] T039 [US3] Run API/Web/CLI/tool parity plus manual EN/DE/NL/ES desktop/mobile acceptance and record results in `specs/024-auditable-ledger-reversals/quickstart.md`

**Checkpoint**: Every interface exposes one reversal meaning and explainable chain.

## Final Phase: Cross-Cutting Review and Baseline Closure

- [x] T040 [DR-001] [DR-002] Update Ledger, data-model, architecture, CLI, Web, and traceability contracts in `docs/features/ledger.md`, `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/CLI_SPEC.md`, and `docs/WEB_SPEC.md`
- [x] T041 Run migration upgrade/downgrade/upgrade, guarded-downgrade, schema/model parity, and all focused tests from `specs/024-auditable-ledger-reversals/quickstart.md`
- [x] T042 Run Ruff and the complete parallel PostgreSQL backend suite and record exact results in `specs/024-auditable-ledger-reversals/quickstart.md`
- [x] T043 Run Web production build, EN/DE/NL/ES audit/tests, and responsive manual review and record results in `specs/024-auditable-ledger-reversals/quickstart.md`
- [x] T044 Review final diff against Constitution, `spec.md`, `plan.md`, all FR/DR mappings, shortest links, tenant boundaries, migration safety, and unrelated concurrent work; record owner approval in `specs/024-auditable-ledger-reversals/checklists/requirements.md`
- [x] T045 [FR-001] [FR-016] After T044 approval, run final Spec policy/traceability audit and mark `012/FR-008` plus only its coverage-matrix gap verified in `specs/012-ledger-finance/spec.md` and `docs/SPEC_COVERAGE_MATRIX.md`

## Dependencies

```text
T001–T003 specification/design gates
  → T004–T006 foundation
    → T007–T018 US1 exact reversal (MVP)
      → T019–T027 US2 settlement/read reconciliation
        → T028–T039 US3 interfaces/explanation
          → T040–T045 final gates and baseline closure
```

- US1 is the MVP and owns the durable reversal boundary.
- US2 depends on US1 role state to derive allocation activity.
- US3 depends on stable US1/US2 preview and financial-effect contracts.
- `[P]` test tasks within a failing-proof section may run in parallel before code.

## Parallel Execution Examples

- **US1**: T007–T012 split model, domain, failure, event, independence, and tenant proof.
- **US2**: T019–T023 split settlement, registers, exceptions, projections, and physical independence.
- **US3**: T028–T033 split API, CLI, tools/MCP, Inspector, events/catalogs, and Web contracts.

## Implementation Strategy

1. Deliver exact service-level whole-group reversal and audit as the MVP.
2. Make every settlement and finance read consumer share reversal-aware derivation.
3. Expose preview/confirmation only after domain and read semantics stabilize.
4. Close `012/FR-008` only after automated/manual/migration and owner-review gates.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-005 | T007–T008 | T013, T040, T045 | Pending |
| FR-006–FR-008 | T009 | T014 | Pending |
| FR-009 | T019, T021–T023 | T024, T026 | Pending |
| FR-010–FR-011 | T010, T020, T023 | T015, T025–T026 | Pending |
| FR-012–FR-014 | T028–T030, T033 | T034–T036, T038 | Pending |
| FR-015–FR-016 | T011, T031–T033 | T016, T037–T040, T045 | Pending |
| FR-017 | T012, T028, T030 | T017, T034, T036 | Pending |
| DR-001–DR-002 | T004, T007–T008 | T005, T013, T040 | Pending |
| DR-003 | T019, T023 | T024, T026 | Pending |
| DR-004–DR-005 | T008, T012, T030 | T013, T017, T036, T040 | Pending |
