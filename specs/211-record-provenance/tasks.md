# Tasks: Visible record provenance and source addressing

## Phase 1: Specification and Design Gates
- [ ] T001 Confirm user-approved scope and requirements quality in `specs/211-record-provenance/spec.md` and `checklists/requirements.md`.
- [x] T002 Review the Constitution Check and the recorded product-scope approval for FR-007 in `specs/211-record-provenance/plan.md`; approval obtained on 2026-09-16.
- [ ] T003 Analyze specification, plan and tasks; record the result in `specs/211-record-provenance/verification.md`.

## Phase 2: User Story 1 - Origin on operational surfaces
- [ ] T004 [US1] [FR-001] [FR-002] [FR-012] [FR-013] Add failing tests in `packages/reality-core/tests/test_provenance.py` for batched origin resolution over a bounded page, the manual-origin fallback, the retained textual code join, a missing source system, and cross-tenant behavior; assert the statement count is independent of row count.
- [ ] T005 [US1] [FR-001] [FR-002] [FR-012] [FR-013] Implement `packages/reality-core/src/reality/services/provenance.py` and enrich the bounded page reads in `services/reference_workspace.py` and the operational register reads in `services/core.py`; expose the contract from `web/api.py`.

## Phase 3: User Story 2 - Inspect the original payload in place
- [ ] T006 [US2] [FR-004] [FR-005] Add failing tests in `packages/reality-core/tests/test_provenance.py` for the extended `source_record` inspection: bounded payload with truncation notice, terminal interpretation outcome, the not-recorded label for sources without one, produced-record links, and unmapped sources.
- [ ] T007 [US2] [FR-004] [FR-005] Extend the `source_record` branch of `packages/reality-core/src/reality/services/delivery_reads.py` with payload, outcome and the resolved link, leaving existing rows and the full Inspector contract compatible.

## Phase 4: User Story 3 - External addressing
- [ ] T008 [US3] [FR-006] [FR-007] [FR-008] [FR-010] [FR-013] Add failing tests in `packages/reality-core/tests/test_provenance.py` for address validation (scheme, user information, length, clearing), template resolution and encoding, the absent-template and absent-address states, payload fields rejected as template inputs, and tenant scope. Add `packages/reality-core/tests/test_source_system_addressing_migration.py` covering the backfill: code equality, longest-name-first description matching, an ambiguous description left null, and a hand-created system left null.
- [ ] T009a [US3] [FR-007] Add a failing regression in `packages/reality-core/tests/test_provenance.py` proving that a `shopify_payments` instance is listed under exactly one connector shell; it fails against the current description-prefix inference.
- [ ] T009 [US3] [FR-006] [FR-007] Add migration `packages/reality-core/migrations/versions/0061_source_system_addressing.py` with the two nullable columns and the one-time unambiguous `connector_code` backfill, plus the columns in `db/core.py`; record the shell in `install_connector_shell`, switch `connector_shells` to read the column and delete the description-prefix test, and add `set_source_system_base_url` in `services/core.py`.
- [ ] T010 [US3] [FR-008] [FR-010] Add optional `deep_links` to `packages/reality-core/config/connector_catalog.yaml`, relax the fixed key-set check in `integrations/catalog.py`, and compose links in `services/provenance.py`.

## Phase 5: Shared UI, localization and review
- [ ] T011 [FR-014] Add label assertions in `apps/web/scripts/provenance-labels.test.mjs` covering all four languages and the German vocabulary Quellsystem, Originalquelle, Herkunft.
- [ ] T012 [US1] [US2] [US3] [FR-003] [FR-009] [FR-010] Add browser acceptance in `apps/web/scripts/record-provenance-browser.mjs`: origin in registers and details, default column visibility per register family, manual origin, in-place inspection, link presence and absence, target host visibility, and 390px behavior.
- [ ] T013 [US1] [US2] [US3] [FR-001] [FR-003] [FR-009] [FR-010] [FR-014] Add `apps/web/src/unified/SourceBadge.tsx`; render it from `MasterDataPage.tsx`, `OrdersPage.tsx`, `CommitmentsPage.tsx`, `ShipmentsRegister.tsx`, `FinancePage.tsx` and `InlinePreview.tsx`; add the column profiles in `RegisterTable.tsx`, the address field in `SourceConfiguration.tsx`, the contract in `api.ts` and the labels in `localization.tsx`.

## Phase 6: User Story 4 - Multiple contributing sources
- [ ] T014 [US4] [FR-011] Add failing tests in `packages/reality-core/tests/test_provenance.py` for a record whose Facts reference several distinct source systems, including the bound on how many are disclosed and the unchanged register row.
- [ ] T015 [US4] [FR-011] Derive the contributing-source disclosure in `services/provenance.py` and render it in the detail views only.

## Phase 7: Catalogs, documentation and gates
- [ ] T016 [FR-013] Classify every new public function in `packages/reality-core/config/tenant_isolation_catalog.yaml` and bump the pinned count in `tests/test_application_catalog.py`; rebase before pushing, because a parallel branch adding functions conflicts on that number.
- [ ] T017 Update `docs/features/source_ingestion.md` (addressing is descriptive configuration, still no credentials or transport), `docs/DATA_MODEL.md`, `docs/WEB_SPEC.md` and `docs/SPEC_COVERAGE_MATRIX.md`; run every check listed in the plan and record the evidence in `specs/211-record-provenance/verification.md`.

## Dependencies and Strategy
T001–T003 gate implementation; T002 gated T009 and is complete. T009a precedes T009. T004, T006, T008 and T014 precede their implementation. T005 precedes T007 and T013 because both consume the shared contract. T011 and T012 precede T013. T016 runs last and is rebased immediately before the pull request. US1 and US2 are independently shippable without US3; US4 is independently droppable.

## Requirement Coverage
| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T004, T012 | T005, T013 |
| FR-002 | T004 | T005 |
| FR-003 | T012 | T013 |
| FR-004 | T006 | T007 |
| FR-005 | T006 | T007 |
| FR-006 | T008 | T009, T013 |
| FR-007 | T008, T009a | T009 |
| FR-008 | T008 | T010 |
| FR-009 | T012 | T013 |
| FR-010 | T008, T012 | T010, T013 |
| FR-011 | T014 | T015 |
| FR-012 | T004 | T005 |
| FR-013 | T004, T008 | T005, T009, T016 |
| FR-014 | T011 | T013 |
