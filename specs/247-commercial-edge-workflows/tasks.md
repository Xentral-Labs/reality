# Tasks: Commercial Edge Workflows

## Phase 1: Setup and failing proof

- [x] T001 Add failing dunning service, bad-debt, deposit and increased-quantity story tests in `packages/reality-core/tests/finance/test_commercial_edges.py`, `packages/reality-core/tests/finance/test_adjustments.py`, and `packages/reality-core/tests/test_commitment_revisions.py`
- [ ] T002 Add failing application-tool, API and tenant-isolation tests in `packages/reality-core/tests/test_application_tools.py` and `packages/reality-core/tests/test_web_api.py`
- [x] T003 Add failing profile-v9 and demo discovery assertions in `packages/reality-core/tests/scenarios/test_international_demo.py`

## Phase 2: Foundations

- [ ] T004 [FR-001..FR-004, DR-003..DR-005] Add DunningNotice and membership models plus migration in `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0089_commercial_edge_workflows.py`
- [ ] T005 [FR-002, FR-005, DR-004] Add dunning-fee revenue and bad-debt expense roles/defaults in `packages/reality-core/src/reality/domain/finance.py` and finance account services
- [ ] T006 [FR-012, DR-005] Add explicit operations to tenant policy and business mutation catalogs in `packages/reality-core/src/reality/services/tenant_policy.py` and `packages/reality-core/src/reality/services/core.py`

## Phase 3: User Story 1 — Dunning

- [ ] T007 [US1] [FR-001..FR-004] Implement preview, record, read and reverse services in `packages/reality-core/src/reality/services/dunning.py`
- [ ] T008 [US1] [FR-001..FR-004, FR-012] Register dunning tools and schemas in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/tools/finance.py`
- [ ] T009 [US1] [FR-001..FR-004] Expose dunning read/write adapters in `packages/reality-core/src/reality/web/api.py`

## Phase 4: User Story 2 — Bad debt

- [ ] T010 [US2] [FR-005..FR-006] Add customer-only bad-debt semantics and dedicated account routing in `packages/reality-core/src/reality/services/finance/settlement.py`
- [ ] T011 [US2] [FR-005..FR-006] Extend financial reversal, labels and inspector explanation in finance services and catalogs

## Phase 5: User Story 3 — Deposits

- [ ] T012 [US3] [FR-007..FR-009] Implement deposit record/preview/clear services in `packages/reality-core/src/reality/services/finance/deposits.py`
- [ ] T013 [US3] [FR-007..FR-009] Include deposit types and origins in `packages/reality-core/src/reality/services/finance/credits.py`, open items and inspector reads
- [ ] T014 [US3] [FR-007..FR-009, FR-012] Register deposit tools, policy and API adapters in application and web modules

## Phase 6: User Story 4 — Controlled overdelivery

- [ ] T015 [US4] [FR-010..FR-011] Prove higher revision and guarded movement through domain/service tests and correct public quantity labels in tool schemas
- [ ] T016 [US4] [FR-010..FR-011] Add the confirmed quantity-revision control to the order/commitment web flow in `apps/web/src/`

## Phase 7: User Story 5 — Demo and UX

- [ ] T017 [US5] [FR-013..FR-014, DR-006] Add deterministic dunning, bad-debt, customer/supplier deposit and revised-overdelivery cases through shared services in `packages/reality-core/src/reality/services/demo_profile.py`; bump profile v9
- [ ] T018 [US5] [FR-015] Update English/German demo guides and durable contracts under `apps/docs/content/demo-data/` and `docs/features/`
- [ ] T019 [US1..US4] [FR-012] Add simple confirmed web actions, clear before/after summaries and inspector links in `apps/web/src/`

## Phase 8: Verification and review

- [ ] T020 Run focused backend, frontend and migration tests and resolve failures
- [ ] T021 Run `make docs-generate`, `make docs-catalog-check`, `make spec-check`, lint, full backend tests, web tests/build and i18n audit
- [ ] T022 Create a fresh company in the visible browser, execute all four documented journeys and record discrepancies
- [ ] T023 Review Source → Evidence → Reality links, tenant isolation, idempotency, rollback and final diff; update task status only with green evidence

## Phase 9: Demo catalog closure

- [x] T024 [US5] [FR-016] Add a failing profile assertion that every seeded sales and supplier invoice carries `DEMO-14-2`, then create/reuse the term and bind it through the normal document service; bump the canonical profile version.
- [x] T025 [US5] [FR-017..FR-018] Add `SO-005` and complete item, customer, supplier, location and relationship inventories to both public guides.
- [x] T026 [US5] [FR-019..FR-020] Document continuous live intake plus every exceptional movement and finance/cost record with exact references and UI paths in both languages and the durable catalog.
- [x] T027 [US5] [FR-021] Document the international, reduced execution and `normal-month` demo modes with their distinct start paths and purposes.
- [x] T028 Run profile, setup, documentation-format, catalog-generation, spec-policy and PR quality gates; verify a fresh profile exposes the exact payment term on seeded invoice reads.

## Dependencies

- T001–T003 precede implementation.
- T004–T006 block T007–T016.
- Dunning, bad debt, deposits and controlled overdelivery are independently testable after foundations.
- T017 requires all four services; T018–T019 require stable contracts; T020–T023 are final gates.

## Independent test criteria

- **US1**: One overdue invoice produces a level-2 notice and exact EUR 5 charge; reversal restores the balance.
- **US2**: Partial and full bad debt reduce only the selected receivable and reverse exactly.
- **US3**: Customer and supplier deposits clear partially/fully with excess credit preserved.
- **US4**: Twelve may move only after ten is revised to twelve; original ten remains visible.
- **US5**: A fresh demo company exposes searchable examples without manual projection refresh.
