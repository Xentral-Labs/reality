---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Explainable B2B Operational Chain

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be written in
English. Tests precede the implementation they prove.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the product/domain review accepts scope, priorities, non-goals, assumptions, and zero clarification markers in `specs/248-b2b-operational-chain/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and the SupplyAssignment schema proof is accepted in `specs/248-b2b-operational-chain/plan.md` and `specs/248-b2b-operational-chain/data-model.md`
- [x] T003 Run `$speckit-analyze`, resolve every CRITICAL/HIGH finding in `specs/248-b2b-operational-chain/`, and record the clean result in `specs/248-b2b-operational-chain/checklists/requirements.md`

## Phase 2: Foundational Failing Proof and Schema

- [ ] T004 [P] [FR-019] [DR-005] [DR-006] Add cross-tenant not-found, preview/confirmation, replay, and Web/tool/MCP/CLI parity contract tests for the planned mutations in `packages/reality-core/tests/test_b2b_operational_chain_contracts.py` and `packages/reality-core/tests/test_cli.py`
- [ ] T005 [P] [FR-020] Add failing shared projection-readiness and last-completed-result tests in `packages/reality-core/tests/test_projection_readiness.py`
- [ ] T006 [P] [DR-008] Add failing model-shape, composite-tenant-FK, append-only, and forbidden-duplicate-link assertions in `packages/reality-core/tests/test_reference_integrity.py` and `packages/reality-core/tests/test_schema_constraints.py`
- [x] T007 [DR-003] [DR-005] [DR-008] Add migration 0090 with the tenant-scoped append-only SupplyAssignment table and downgrade in `packages/reality-core/migrations/versions/0090_supply_assignments.py`
- [x] T008 [DR-003] [DR-005] [DR-008] Add the SupplyAssignment ORM mapping and constraints without document/line duplication in `packages/reality-core/src/reality/db/core.py`
- [ ] T009 [P] [FR-019] Register shared permission vocabulary and German labels for planned actions/reads in `packages/reality-core/config/resource_catalog.yaml` and `packages/reality-core/src/reality/catalogs.py`
- [ ] T010 [FR-020] Implement the shared projection-due/readiness helper through the existing job registry in `packages/reality-core/src/reality/services/projections.py` and `packages/reality-core/src/reality/services/company_setup.py`

**Checkpoint**: Migration, tenant boundary, action policy, and projection lifecycle are ready for independently testable stories.

## Phase 3: User Story 1 — Invoice a Delivered B2B Sale With Contribution (P1)

**Goal**: Preserve ordinary invoice lines and expose traceable DB1/DB2 without a first manual refresh.

**Independent test**: Receive valued stock, fulfil a customer order, invoice only the delivered
quantity, and inspect revenue, retained consumed cost, DB1, reviewed costs, DB2, evidence, freshness,
and the uninvoiced remainder.

- [ ] T011 [P] [US1] [FR-001] [FR-002] [DR-001] [DR-002] Add failing ordinary confirmed sales- and supplier-invoice line/evidence tests in `packages/reality-core/tests/test_unified_invoice_entry.py` and `packages/reality-core/tests/test_multi_position_invoices.py`
- [ ] T012 [P] [US1] [FR-003] Add failing partial/multiple invoice and concurrent over-billing tests in `packages/reality-core/tests/test_partial_invoicing_rebilling.py`
- [ ] T013 [P] [US1] [FR-004] [FR-005] Add failing contribution tests for supported line revenue/cost/DB1/DB2 and non-zero unavailable semantics in `packages/reality-core/tests/test_contribution_reviews.py`
- [ ] T014 [P] [US1] [FR-006] [FR-020] Add failing automatic initial calculation and stale/failed freshness tests in `packages/reality-core/tests/test_projection_readiness.py`
- [ ] T015 [US1] [FR-001] [FR-002] [FR-003] [DR-001] [DR-002] Preserve reviewed source-stated invoice lines and shortest billed-line links in `packages/reality-core/src/reality/services/invoice_actions.py` and `packages/reality-core/src/reality/services/order_actions.py`
- [ ] T016 [US1] [FR-003] Enforce eligible delivered/billed quantities under transaction locking and idempotent replay in `packages/reality-core/src/reality/services/invoice_actions.py`
- [ ] T017 [US1] [FR-004] [FR-005] Extend supported ordinary billed-line matching and stable unavailable reasons in `packages/reality-core/src/reality/services/contribution_reviews.py` and `packages/reality-core/src/reality/services/finance/components.py`
- [ ] T018 [US1] [FR-006] [FR-020] Mark existing finance/contribution projections due after confirmed commercial writes and expose readiness/freshness in `packages/reality-core/src/reality/services/invoice_actions.py` and `packages/reality-core/src/reality/services/projections.py`
- [ ] T019 [P] [US1] [FR-001] [FR-004] [FR-005] [DR-006] Extend shared tool/MCP/API/CLI schemas and contract tests for invoice lines and contribution explanations in `packages/reality-core/src/reality/tools/application.py`, `packages/reality-core/src/reality/mcp/catalog.py`, `packages/reality-core/src/reality/web/api.py`, `packages/reality-core/src/reality/cli/app.py`, and `packages/reality-core/tests/test_b2b_operational_chain_contracts.py`
- [ ] T020 [US1] [FR-004] [FR-005] [FR-020] Render line-level DB1/DB2, missing-basis next action, trace links, and freshness in `apps/web/src/unified/CostExplanation.tsx` and `apps/web/src/unified/ProjectionFreshness.tsx`
- [ ] T021 [US1] [FR-001] [FR-003] [FR-004] Run the US1 independent acceptance test and record exact evidence in `specs/248-b2b-operational-chain/quickstart.md`

**Checkpoint**: A delivered ordinary sale is independently invoiceable and financially explainable.

## Phase 4: User Story 2 — Distinguish Customer Supply From Stock Replenishment (P2)

**Goal**: Explicitly assign supplier quantity to customer demand or stock without implying receipt or reservation.

**Independent test**: Split two supplier commitments between two customer commitments and stock,
partially receive/cancel supply, and reconcile assigned, unassigned, received, open, and shortage
quantities across purchasing, sales, and inventory.

- [x] T022 [P] [US2] [FR-007] [FR-008] [DR-003] Add failing domain tests for customer-demand, stock, unassigned, and reversal semantics in `packages/reality-core/tests/test_supply_assignments.py`
- [x] T023 [P] [US2] [FR-009] [DR-005] Add failing concurrency, over-allocation, compatibility, and tenant-isolation service tests in `packages/reality-core/tests/test_supply_assignments.py`
- [x] T024 [P] [US2] [FR-010] Add failing three-view reconciliation and no-double-counting tests in `packages/reality-core/tests/test_supply_coverage.py`
- [x] T025 [US2] [FR-007] [FR-008] [FR-009] [DR-003] Implement pure effective-assignment/reversal and bound rules in `packages/reality-core/src/reality/domain/supply.py`
- [ ] T026 [US2] [FR-007] [FR-009] [FR-019] [DR-005] Implement tenant-scoped preview/confirm/reverse services with locks and idempotency in `packages/reality-core/src/reality/services/supply_assignments.py`
- [x] T027 [US2] [FR-008] [FR-010] Implement purchasing/customer coverage observations separately from receipt/reservation/fulfilment in `packages/reality-core/src/reality/services/supply_assignments.py` and `packages/reality-core/src/reality/services/delivery_reads.py`
- [x] T028 [P] [US2] [FR-007] [FR-010] [FR-019] [DR-006] Expose assignment and coverage through shared tools, MCP, API and CLI with adapter tests in `packages/reality-core/src/reality/tools/application.py`, `packages/reality-core/src/reality/mcp/catalog.py`, `packages/reality-core/src/reality/web/api.py`, `packages/reality-core/src/reality/cli/app.py`, and `packages/reality-core/tests/test_b2b_operational_chain_contracts.py`
- [x] T029 [US2] [FR-007] [FR-008] [FR-010] Add simple Assign supply review and reconciled coverage UI to `apps/web/src/unified/OrdersPage.tsx` and `apps/web/src/unified/DeliveryCase.tsx`
- [x] T030 [US2] [FR-007] [FR-009] [FR-010] Run the US2 independent acceptance test and record exact evidence in `specs/248-b2b-operational-chain/quickstart.md`

**Checkpoint**: Supply intent is explicit, quantity-safe, tenant-safe, and independently understandable.

## Phase 5: User Story 3 — Resolve an Arrived Customer Return (P2)

**Goal**: Guide partial physical disposition while keeping goods and credits independent.

**Independent test**: Receive five returned units, restock two, quarantine one, scrap one, return one
to the supplier, and verify exact quantity reconciliation plus independent credit state.

- [x] T031 [P] [US3] [FR-011] [FR-012] [DR-004] [DR-007] Add failing mixed/partial disposition, over-resolution, correction, and history tests in `packages/reality-core/tests/test_returns.py`
- [x] T032 [P] [US3] [FR-013] Add failing returned-not-credited and credited-not-returned lifecycle tests in `packages/reality-core/tests/test_commercial_matching_services.py`
- [x] T033 [P] [US3] [FR-011] [FR-013] [FR-019] [DR-006] Add failing return-disposition tool/API parity and tenant tests in `packages/reality-core/tests/test_return_announcement_adapters.py`
- [x] T034 [US3] [FR-011] [FR-012] [DR-004] [DR-007] Implement preview/confirm disposition orchestration over resolving movements in `packages/reality-core/src/reality/services/delivery_actions.py`
- [x] T035 [US3] [FR-011] [FR-012] Implement derived disposition labels and arrived/resolved/unresolved quantity reads in `packages/reality-core/src/reality/services/delivery_reads.py`
- [x] T036 [US3] [FR-013] Preserve independent goods/credit mismatch explanations and links in `packages/reality-core/src/reality/services/exceptions.py` and `packages/reality-core/src/reality/services/credit_actions.py`
- [x] T037 [P] [US3] [FR-011] [FR-019] [DR-006] Expose return disposition through shared tools, MCP, API and CLI in `packages/reality-core/src/reality/tools/application.py`, `packages/reality-core/src/reality/mcp/catalog.py`, `packages/reality-core/src/reality/web/api.py`, and `packages/reality-core/src/reality/cli/app.py`
- [x] T038 [US3] [FR-011] [FR-012] [FR-013] Add the four-choice partial return flow and separate goods/credit sections in `apps/web/src/unified/DeliveryWorkPage.tsx` and `apps/web/src/unified/ShipmentActions.tsx`
- [x] T039 [US3] [FR-011] [FR-012] [FR-013] Run the US3 independent acceptance test and record exact evidence in `specs/248-b2b-operational-chain/quickstart.md`

**Checkpoint**: Returned goods are completely dispositioned without overstating stock or implying finance.

## Phase 6: User Story 4 — Explain Every Covered Movement (P3)

**Goal**: Give every covered movement one shortest truthful explanation and preserve deliberate exceptions.

**Independent test**: Inspect every movement in the B2B story; each reaches an allowed explanation in
at most two navigation steps and the story produces zero unexplained-movement exceptions.

- [x] T040 [P] [US4] [FR-014] [DR-001] [DR-004] Add failing precedence, provenance, correction, and Inspector-target tests in `packages/reality-core/tests/test_movement_explanations.py`
- [x] T041 [P] [US4] [FR-015] Add failing preview-warning and persistent-exception tests in `packages/reality-core/tests/operational_exceptions/test_derivation.py`
- [x] T042 [US4] [FR-014] [DR-001] [DR-004] Implement the non-persisted shortest-link explanation read in `packages/reality-core/src/reality/services/movement_explanations.py`
- [x] T043 [US4] [FR-015] Add a clear pre-confirmation warning without suppressing canonical exceptions in `packages/reality-core/src/reality/services/delivery_actions.py`
- [x] T044 [P] [US4] [FR-014] [FR-019] [DR-006] Expose movement explanation through shared tools, MCP, API and CLI with parity tests in `packages/reality-core/src/reality/tools/application.py`, `packages/reality-core/src/reality/mcp/catalog.py`, `packages/reality-core/src/reality/web/api.py`, `packages/reality-core/src/reality/cli/app.py`, and `packages/reality-core/tests/test_b2b_operational_chain_contracts.py`
- [x] T045 [US4] [FR-014] [FR-015] Add Why did this happen presentation, source/Inspector links, and warning text in `apps/web/src/unified/WarehousePage.tsx` and a focused new `apps/web/src/unified/MovementExplanation.tsx` component
- [x] T046 [US4] [FR-014] [FR-015] Run the US4 independent acceptance test and record exact evidence in `specs/248-b2b-operational-chain/quickstart.md`

**Checkpoint**: Movement provenance is shared, concise, and complete without storing a second authority.

## Phase 7: Integrated B2B Story, Documentation, and UX

- [ ] T047 [P] [FR-016] [FR-017] [DR-006] Add the failing deterministic empty-company multi-day business story with dated, consistently numbered, non-zero commercial evidence in `packages/reality-core/tests/scenarios/test_b2b_operational_chain.py`
- [ ] T048 [P] [FR-018] Add failing manifest completeness and exact-reference/UI-path contract tests in `packages/reality-core/tests/scenarios/test_b2b_operational_chain_catalog.py`
- [ ] T049 [P] [SC-002] [SC-003] [SC-004] [SC-005] Add exact invoice/contribution, supply, and return reconciliation assertions in `packages/reality-core/tests/scenarios/test_b2b_operational_chain.py`
- [ ] T050 [P] [SC-006] [SC-008] Add zero-unexplained-movement and idempotent-replay assertions in `packages/reality-core/tests/scenarios/test_b2b_operational_chain.py`
- [ ] T051 [FR-016] [FR-017] [DR-006] Implement the deterministic story exclusively through application services in `packages/reality-core/src/reality/services/demo_profile.py` and `packages/reality-core/src/reality/integrations/demo_data.py`
- [ ] T052 [FR-018] Publish exact story references, expected results, intentional exceptions, and UI paths in `docs/features/b2b-operational-chain.md` and `apps/docs/content/getting-started/demo-data.md`
- [ ] T053 [FR-019] [DR-006] Regenerate executable command/tool/reference documentation with `make docs-generate` and commit outputs under `apps/docs/content/tool-usage/` and `apps/docs/.vitepress/data/tool-usage.json`
- [ ] T054 [P] [SC-001] [SC-007] Add a timed first-user browser acceptance test for finding the key objects without database access in `packages/reality-core/tests/browser/b2b_operational_chain.py`
- [ ] T055 [SC-001] [SC-007] Refine progress, completion, and navigation copy so the user always knows the current and next step in `apps/web/src/unified/` and `apps/web/src/localization.tsx`
- [ ] T056 [FR-016] [FR-018] [SC-001] [SC-007] Run the complete fresh-company browser story and record exact references, timing, screenshots, and observed results in `specs/248-b2b-operational-chain/quickstart.md`

## Final Phase: Cross-Cutting Verification and Review

- [ ] T057 [SC-009] Run `make spec-check` and audit every FR/DR row against tests and implementation in `specs/248-b2b-operational-chain/spec.md` and `specs/248-b2b-operational-chain/tasks.md`
- [ ] T058 [SC-009] Run Ruff, focused tests, the complete PostgreSQL backend suite, and migration tests; record commands/results in `specs/248-b2b-operational-chain/quickstart.md`
- [ ] T059 [SC-001] [SC-007] Run frontend unit tests, browser test, production build, and i18n audit; record commands/results in `specs/248-b2b-operational-chain/quickstart.md`
- [ ] T060 [DR-008] Review migration upgrade/downgrade, concurrent assignment locks, rollback order, and absence of inferred backfill in `packages/reality-core/migrations/versions/0090_supply_assignments.py`
- [ ] T061 [DR-001] [DR-002] [DR-003] [DR-004] [DR-005] [DR-006] [DR-007] [DR-008] Review the final diff against Source → Evidence → Reality, shortest links, tenant boundaries, immutability, shared services, and received-value authority in `specs/248-b2b-operational-chain/checklists/requirements.md`
- [ ] T062 [FR-001] [FR-020] Update durable feature contracts and `docs/V0_CHECKLIST.md` only for behavior whose required checks are green in `docs/features/b2b-operational-chain.md` and `docs/V0_CHECKLIST.md`

## Dependencies

- Phase 1 blocks every implementation phase.
- Phase 2 blocks all stories because it establishes the schema, tenant contract, permissions, and
  projection lifecycle.
- US1 is the MVP and can ship independently after Phase 2.
- US2 and US3 can proceed in parallel after Phase 2; neither depends on the other's model.
- US4 can begin after Phase 2, but its complete acceptance proof consumes the movements produced by
  US1 and US3.
- The integrated story requires US1–US4. Final verification requires the integrated story and docs.

```text
Phase 1 → Phase 2 → US1 ─────────┐
                   ├→ US2 ──────┤
                   ├→ US3 ──────┼→ Integrated story/docs → Final verification
                   └→ US4* ─────┘
*US4 service work is parallel; its full story assertion waits for US1 and US3.
```

## Parallel Execution Examples

- After Phase 2, run T011–T014 concurrently because they add independent failing US1 proofs.
- Run US2 service/model work and US3 return work concurrently because they touch separate domain
  services; serialize edits to shared tool, MCP, API, catalog, and localization files.
- Within US2, run T022–T024 concurrently before T025–T027.
- Within US3, run T031–T033 concurrently before T034–T038.
- Within US4, run T040 and T041 concurrently before T042–T045.
- Run T047, T048, and T054 concurrently once all story contracts are stable; consolidate exact
  references only in T056.

## Implementation Strategy

1. Deliver US1 first as the smallest user-visible MVP: an ordinary delivered sale produces retained
   invoice lines and trustworthy DB1/DB2 without manual initial refresh.
2. Add US2 and US3 as independent operational slices, each with its own tenant, concurrency and
   quantity reconciliation proof.
3. Add US4 as a shared read/explanation layer over authoritative records, not new authority.
4. Assemble the service-driven B2B story only after all individual slices pass.
5. Mark tasks complete only after the named proof is green; never use the final browser run as a
   substitute for lower-level tenant, invariant, migration, or idempotency tests.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-002 | T011 | T015, T019 | Pending |
| FR-003 | T012 | T015–T016 | Pending |
| FR-004–FR-005 | T013 | T017, T019–T020 | Pending |
| FR-006 | T014 | T018 | Pending |
| FR-007–FR-008 | T022 | T025–T029 | Pending |
| FR-009 | T023 | T025–T026 | Pending |
| FR-010 | T024 | T027–T029 | Pending |
| FR-011–FR-012 | T031, T033 | T034–T035, T037–T038 | Pending |
| FR-013 | T032 | T036, T038 | Pending |
| FR-014 | T040 | T042, T044–T045 | Pending |
| FR-015 | T041 | T043, T045 | Pending |
| FR-016–FR-017 | T047, T049–T050 | T051, T056 | Pending |
| FR-018 | T048 | T052, T056 | Pending |
| FR-019 | T004, T033 | T009, T019, T026, T028, T037, T044, T053 | Pending |
| FR-020 | T005, T014 | T010, T018, T020 | Pending |
| DR-001–DR-002 | T011, T040 | T015, T017, T042, T061 | Pending |
| DR-003 | T022 | T025–T027, T061 | Pending |
| DR-004 | T031, T040 | T034–T035, T042, T061 | Pending |
| DR-005 | T004, T023 | T007–T008, T026, T061 | Pending |
| DR-006 | T004, T033, T047 | T019, T028, T037, T044, T051, T053, T061 | Pending |
| DR-007 | T031 | T034, T061 | Pending |
| DR-008 | T006 | T007–T008, T060–T061 | Pending |
| SC-001–SC-009 | T049–T050, T054, T057–T059 | T051–T056, T060–T062 | Pending |
