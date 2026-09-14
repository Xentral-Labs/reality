# Tasks: Physical Shipments and Tracking

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Gate**: Product scope approved; Constitution Check PASS; architecture review remains required

## Phase 1: Specification and Design Gates

- [x] T001 Record architecture/domain approval in `specs/173-physical-shipments-tracking/spec.md` and `checklists/requirements.md`
- [x] T002 Confirm every Constitution Check row remains PASS in `specs/173-physical-shipments-tracking/plan.md`
- [x] T003 Run `$speckit-analyze`, resolve every CRITICAL finding, and retain the final report in the approval conversation

## Phase 2: Foundational Failing Proof and Schema

- [x] T004 [P] [FR-001] [FR-002] [FR-003] [FR-007] [FR-010] [FR-025] [DR-004] [DR-010] Add failing model, constraint, tenant and immutability tests in `packages/reality-core/tests/test_shipments_domain.py`
- [x] T005 [P] [FR-004] [FR-005] [FR-006] [FR-027] [DR-002] [DR-003] [DR-009] Add failing compatibility/effective-Movement and no-backfill tests in `packages/reality-core/tests/test_shipments_migration.py`
- [x] T006 [FR-001] [FR-002] [FR-003] [FR-007] [FR-010] [FR-025] Add Shipment, ShipmentPackage, ShipmentEvent and ShipmentEventSupersession models plus nullable Movement Package link in `packages/reality-core/src/reality/db/core.py`
- [x] T007 [FR-001] [FR-003] [FR-004] [FR-007] [FR-010] [FR-025] [FR-027] Add the additive no-backfill migration, constraints and tenant-first indexes in `packages/reality-core/migrations/versions/`
- [x] T008 [FR-002] [FR-005] [FR-008] [FR-009] [DR-001] [DR-005] [DR-007] [DR-008] Add closed vocabularies, compatibility validation and pure observation derivation in `packages/reality-core/src/reality/domain/shipments.py`

## Phase 3: User Story 1 — Customer Dispatch (P1)

**Independent test**: Dispatch ten units in two Packages, append delivery evidence and reproduce exact contents and fulfillment.

- [x] T009 [P] [US1] [FR-004] [FR-005] [FR-006] [DR-002] [DR-003] [SC-001] [SC-002] [SC-003] Add failing package-content, partial/final dispatch, correction and existing-rule tests in `packages/reality-core/tests/test_shipment_story.py`
- [x] T010 [P] [US1] [FR-014] [FR-015] [FR-016] [FR-018] [SC-004] [SC-005] Add failing no-effect prepare, atomic confirm, stale, replay, concurrency and lost-response dispatch tests in `packages/reality-core/tests/test_shipment_actions.py`
- [x] T011 [US1] [FR-004] [FR-005] [FR-006] [FR-015] Implement atomic Package creation and existing `record_movement` orchestration in `packages/reality-core/src/reality/services/shipments.py`
- [x] T012 [US1] [FR-014] [FR-016] [FR-018] Implement reviewed `shipment_dispatch` preparation/execution/reconciliation in `packages/reality-core/src/reality/services/shipment_actions.py`

## Phase 4: User Story 2 — Supplier Notice and Receipt (P1)

**Independent test**: Record an inbound notice with zero stock effect, then receive partially and prove only Movements change stock/fulfillment.

- [x] T013 [P] [US2] [FR-005] [FR-007] [FR-008] [FR-009] [FR-011] [DR-005] [DR-006] Add failing notice/receipt, lossless-source, zero-effect and discrepancy tests in `packages/reality-core/tests/test_shipment_story.py`
- [x] T014 [P] [US2] [FR-014] [FR-015] [FR-016] Add failing notice/receive action atomicity and replay tests in `packages/reality-core/tests/test_shipment_actions.py`
- [x] T015 [US2] [FR-007] [FR-008] [FR-011] [DR-001] [DR-008] Implement source-backed Shipment/Package notice and event recording primitives in `packages/reality-core/src/reality/services/shipments.py`
- [x] T016 [US2] [FR-014] [FR-015] [FR-016] Implement `shipment_notice_record` and `shipment_receive` reviewed actions in `packages/reality-core/src/reality/services/shipment_actions.py`

## Phase 5: User Story 3 — Customer and Supplier Returns (P2)

**Independent test**: Receive a tracked customer return and dispatch a tracked supplier return without reopening original fulfillment.

- [x] T017 [P] [US3] [FR-002] [FR-006] [DR-009] Add failing four-quadrant return compatibility, bounds, settlement and fulfillment-regression tests in `packages/reality-core/tests/test_shipment_returns.py`
- [x] T018 [US3] [FR-002] [FR-006] [FR-015] Integrate Package validation with existing ReturnAnnouncement/customer-return/supplier-return services in `packages/reality-core/src/reality/services/shipments.py`
- [x] T019 [US3] [FR-014] [FR-016] Extend dispatch/receive reviewed snapshots and receipts for both return purposes in `packages/reality-core/src/reality/services/shipment_actions.py`

## Phase 6: User Story 4 — Shared Reads and Explanation (P1)

**Independent test**: Query the same Shipment and Package through every adapter and obtain equivalent tenant-scoped results and traces.

- [x] T020 [P] [US4] [FR-009] [FR-012] [FR-013] [FR-025] [FR-029] [FR-030] [DR-007] Add failing paged/filter/detail/derivation/tenant/query-plan tests in `packages/reality-core/tests/test_shipment_reads.py`
- [x] T021 [P] [US4] [FR-011] [FR-013] [DR-001] [DR-004] [DR-005] Add failing complete Source/Evidence/Reality Inspector-trace tests across `packages/reality-core/tests/test_shipment_reads.py`, `test_shipment_story.py`, and `test_shipment_api.py`
- [x] T022 [US4] [FR-009] [FR-012] [FR-013] [FR-025] [FR-029] Implement tenant-scoped list/explain queries and measured indexes in `packages/reality-core/src/reality/services/shipments.py`
- [x] T023 [US4] [FR-013] [FR-030] [DR-001] [DR-004] Implement Shipment/Package Inspector presentation and shortest links in `packages/reality-core/src/reality/web/api.py` using the shared Shipment explanation service
- [x] T024 [P] [US4] [FR-017] [FR-022] Add failing CLI list/show parity tests in `packages/reality-core/tests/test_shipment_cli.py`
- [x] T025 [P] [US4] [FR-017] [FR-023] Add failing HTTP list/explain auth/error/contract tests in `packages/reality-core/tests/test_shipment_api.py`
- [x] T026 [P] [US4] [FR-017] [FR-024] Add failing application-tool/MCP/catalog/guidance parity tests in `packages/reality-core/tests/test_shipment_tools.py`
- [x] T027 [US4] [FR-017] [FR-022] Expose CLI list/show as thin application-service callers in `packages/reality-core/src/reality/cli/app.py`
- [x] T028 [US4] [FR-017] [FR-023] Add HTTP read DTOs/routes as thin callers in `packages/reality-core/src/reality/web/api.py`
- [x] T029 [US4] [FR-017] [FR-024] Register `shipments_list` and `shipment_explain` tools and MCP guidance in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`

## Phase 7: User Story 5 — Safe Cross-Surface Mutations (P1)

**Independent test**: Each command produces one exact effect or none across prepare, stale, replay, concurrency and lost response through all adapters.

- [x] T030 [P] [US5] [FR-007] [FR-010] [FR-014] [FR-016] Add failing event append/supersede and correction-history action tests in `packages/reality-core/tests/test_shipment_actions.py`
- [x] T031 [P] [US5] [FR-017] [FR-018] [FR-022] [FR-023] [FR-024] Add failing CLI/API/MCP mutation-proposal and confirmation-parity tests across `packages/reality-core/tests/test_shipment_cli.py`, `test_shipment_api.py`, and `test_shipment_tools.py`
- [x] T032 [US5] [FR-007] [FR-010] [FR-014] [FR-016] Implement event record/supersede and exact action receipts in `packages/reality-core/src/reality/services/shipments.py` and `packages/reality-core/src/reality/services/shipment_actions.py`
- [x] T033 [US5] [FR-017] [FR-018] [FR-022] Expose five reviewed CLI workflows in `packages/reality-core/src/reality/cli/app.py`
- [x] T034 [US5] [FR-017] [FR-018] [FR-023] Expose prepare/review/receipt/reconcile HTTP DTOs/routes in `packages/reality-core/src/reality/web/api.py`
- [x] T035 [US5] [FR-017] [FR-018] [FR-024] Register five canonical command schemas, MCP proposals and Chat guidance in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T036 [US5] [FR-026] Add command/event/tenant/capability/projection catalog entries and invalidation metadata in `packages/reality-core/config/command_catalog.yaml`, `business_event_catalog.yaml`, `tenant_isolation_catalog.yaml`, `action_discovery.json`, and `projection_catalog.yaml`

## Phase 8: Web Product (US1–US5)

- [x] T037 [P] [US4] [FR-019] [FR-020] [FR-028] Add frontend contracts for Commitment/Shipment terminology, registers, detail and four locales in the shared Web contract/audit suite
- [x] T038 [P] [US5] [FR-021] [FR-028] Add a failing stateful browser journey for reads, five forms, confirmation, errors, responsive layouts, themes, keyboard and locales in `apps/web/scripts/unified-shipments-browser.mjs`
- [x] T039 [US4] [FR-017] [FR-019] [FR-020] Add typed Shipment transport in `apps/web/src/api.ts` and render separate Incoming/Outgoing Shipment registers/detail in `apps/web/src/unified/ShipmentsRegister.tsx`
- [x] T040 [US5] [FR-021] Add discovered notice/dispatch/receive/event/supersede forms using shared proposal UI in `apps/web/src/unified/ShipmentActions.tsx`
- [x] T041 [US4] [FR-019] [FR-020] Update Sales/Purchasing Commitment labels, routing and Inspector links in `apps/web/src/unified/OrdersPage.tsx` and `apps/web/src/unified/ShipmentsRegister.tsx`
- [x] T042 [US4] [FR-028] Add en/de/nl/es canonical logistics copy and complete the localization audit in `apps/web/src/localization.tsx`

## Final Phase: Documentation, Verification and Review

- [x] T043 [P] [FR-011] [FR-017] [FR-019] [FR-024] [FR-027] [DR-001] Update durable contracts in `docs/features/shipments.md`, `docs/features/movements.md`, `docs/DATA_MODEL.md`, `docs/WEB_SPEC.md`, and `docs/features/mcp_reads.md`
- [x] T044 [P] [FR-026] Run catalog, projection invalidation, tenant isolation and existing Movement/fulfillment/return regression suites and record commands/results in `specs/173-physical-shipments-tracking/quickstart.md`
- [x] T045 [P] [FR-027] [SC-006] Run forward/backward migration proof and legacy regressions on disposable PostgreSQL and record evidence in `specs/173-physical-shipments-tracking/quickstart.md`
- [x] T046 [P] [FR-029] [SC-007] Run representative PostgreSQL explain/performance proof and record dataset, budget and result in `specs/173-physical-shipments-tracking/quickstart.md`
- [x] T047 [FR-028] [SC-008] Run frontend contracts, Web build, i18n audit and stateful browser matrix and record results in `specs/173-physical-shipments-tracking/quickstart.md`
- [x] T048 Run `make spec-check`, `make lint`, full PostgreSQL backend suite and `git diff --check`, recording results in `specs/173-physical-shipments-tracking/quickstart.md`
- [x] T049 Review the final diff against every FR/DR, Constitution, shortest links, rollback and security risks in `specs/173-physical-shipments-tracking/review.md`
- [x] T050 Update `docs/V0_CHECKLIST.md` and task checkboxes only after every required check is green

## Dependencies and Parallel Opportunities

T001–T003 gate implementation. T004–T008 are foundational. US1 and US2 establish outgoing and
incoming execution; US3 reuses both. US4 reads can proceed after schema/domain foundations and is
required before Web. US5 action adapters follow canonical actions. `[P]` tests in distinct files
may be authored concurrently before their corresponding implementation; Web contracts/browser
proof may be authored together after API contracts stabilize.

## Implementation Strategy

The MVP is US1 plus foundational schema and explainable read support: one real outgoing customer
Package with exact Movements and optional tracking, without claiming carrier delivery. Increment 2
adds supplier notice/receipt, increment 3 returns, increment 4 full adapter reads, increment 5 safe
event/actions and Web parity. No increment is complete while its independent test is red.

## Requirement Coverage

FR-001–FR-030 and DR-001–DR-010 appear in at least one preceding failing-test task and one
implementation/documentation task. SC-001–SC-006 are exercised by T009–T038 and T044–T045;
SC-007 by T020/T046; SC-008 by T037–T042/T047.
