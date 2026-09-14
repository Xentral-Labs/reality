# Tasks: Demo Data pays its orders

**Input**: [spec.md](spec.md), [plan.md](plan.md), [payment matching contract](../../docs/features/payment_matching.md)
**Gate**: Constitution Check passed in plan.md; spec.md carries no `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

`[P]` marks tasks that can run in parallel with their neighbours. Test tasks precede the code
they prove. Every FR and DR appears in at least one test task and one implementation or
documentation task (see Requirement Coverage).

## Phase 1: Specification and design gates

- [x] T001 Confirm the owner's spec review; spec.md has no clarification markers and the seven decisions are reflected in Assumptions and Dependencies
- [x] T002 Confirm all eight Constitution Check rows are PASS in `plan.md` and Complexity Tracking is empty
- [x] T003 Run `$speckit-analyze` over spec.md, plan.md and this file; resolve every CRITICAL finding before Phase 2
- [x] T004 Record the stacked-branch condition in `specs/168-demo-order-to-cash/review.md`: rebase onto main after 165 merges, before opening the PR

## Phase 2: Settlement planner and payloads (producer, no Reality dependency)

- [x] T005 [P] [US1] [US2] [FR-002] [FR-003] [FR-004] [FR-008] [DR-007] Add failing tests in `packages/reality-core/tests/test_demo_data_settlement_plan.py`: same inputs give the same plan; 10,000 seeds land within one percentage point of the outcome and money-path tables; every difference lies on the bank path; stated amounts are Decimals with at most two places; delays are ordered and within the stated ranges; an AST walk over `services/payment_intake.py` finds no multiplication or division touching a rate (mirror the spec 088 test)
- [x] T006 [P] [US1] [US3] [FR-005] [FR-006] Add failing payload tests in the same file: order payload carries `shop_id`, `number` and `customer_reference` as distinct values; invoice payload carries order identity, number, dates, term code, currency, amounts and lines naming order source lines; payment payload carries bank-statement field names, `money_path`, typed `references`, `remittance_text`, `payment_index`; identities are `{order external id}:invoice` and `{order external id}:payment:{n}`; unmatched plans use customer-number-only, PO-without-order or one-digit typo references
- [x] T007 [US1] [US2] [FR-002] [FR-003] [FR-004] [FR-008] Implement `OUTCOME_WEIGHTS`, `MONEY_PATH_WEIGHTS`, `DELAYS`, `SettlementPlan`, `PlannedPayment` and `settlement_plan(...)` in `packages/reality-core/src/reality/integrations/demo_data.py`, drawing with the existing `_draw` under `settle:*` purposes
- [x] T008 [US1] [US3] [FR-005] [FR-006] Extend `produce` with optional `shop_id` and `customer_reference`; add `DemoInvoice`, `DemoPayment`, `produce_invoice`, `produce_payment` in `packages/reality-core/src/reality/integrations/demo_data.py`; keep `DemoOrder` at schema version 1 with the new fields optional
- [x] T009 [US1] [FR-005] Store `shop_id` and `customer_reference` on the order document in the existing `interpret` (customer reference through `create_manual_document_with_lines(customer_reference=...)`; shop id stays the source `external_id` plus payload) and add the assertion to `packages/reality-core/tests/test_demo_data_generator.py`

## Phase 3: Shared payment intake core (US1, US2, US3 service behaviour)

- [x] T010 [P] [US1] [FR-009] [DR-001] [DR-002] Add failing tests in `packages/reality-core/tests/test_payment_intake.py`: `interpret_sales_invoice` creates one `sales_invoice` whose lines carry `billed_document_line_id` to the order lines, attaches the payment term, posts balanced AR/revenue entries once, returns the existing document on replay, and rolls back on an unknown order or unknown order line
- [x] T011 [P] [US1] [US2] [FR-010] [FR-011] [FR-013] [DR-002] [DR-003] Add failing tests in the same file for `interpret_customer_payment`: exact (allocation equals total, open zero), short (allocation equals amount, residual open, no reduction booked), over (allocation equals open, remainder unallocated), second payment closes a partial, duplicate after paid allocates nothing, replay creates no second cash entry, payment pinned to the invoice's control account, blocked control account records to an allowed account without allocation, unposted or reversed invoice never allocates
- [x] T012 [P] [US3] [FR-012] Add failing resolver tests: invoice number, shop id (through the order source record and billed lines), shop order number, customer reference each resolve; customer number narrows only; wrong party, wrong currency, two invoices for one order and a consolidated invoice yield no allocation with stated reasons; lookups are tenant- and party-scoped (a matching number in another tenant or party never resolves)
- [x] T013 [P] [US3] [FR-014] [DR-003] Add failing candidate tests: amount-equals-open, invoice-number substring and ambiguous stated reference produce candidates with reasons; reading twice yields identical results; table row counts are unchanged by a read; an allocated payment yields no candidates for the allocated amount
- [x] T014 [P] [FR-016] [DR-006] Add `packages/reality-core/tests/finance/test_component_boundaries.py::test_payment_intake_imports_only_core` (module imports nothing from `web`, `mcp`, `tools`, `jobs`, `integrations`) and a producer boundary assertion that `integrations/demo_data.py` imports no `services.payment_intake` symbol at module level
- [x] T015 [US1] [US2] [US3] [FR-009] [FR-010] [FR-011] [FR-012] [FR-013] [FR-014] [FR-016] Implement `packages/reality-core/src/reality/services/payment_intake.py`: `Reference`, `NormalisedInvoice`, `NormalisedPayment`, `Candidate`, `resolve_references`, `interpret_sales_invoice`, `interpret_customer_payment`, `payment_candidates`, composing `create_manual_document_with_lines`, `post_sales_invoice`, `record_customer_payment`, `_settlement_control_entry`, `allocate_settlement`, `open_invoice_amount` and `active_settlement_allocations` only
- [x] T016 [US1] [FR-017] Add `normalise_invoice`, `normalise_payment`, `interpret_invoice`, `interpret_payment` to `packages/reality-core/src/reality/integrations/demo_data.py`, calling `require_demo_intake(..., settlement=True)` then the shared core; add normaliser tests (one-to-one mapping, unknown schema version and missing synthetic marker rejected) to `packages/reality-core/tests/test_demo_data_settlement_plan.py`

## Phase 4: Policy scope and bound processing

- [x] T017 [P] [FR-021] [DR-004] Add failing tests in `packages/reality-core/tests/test_demo_data_security.py`: the order intake scope cannot call `post_sales_invoice`, `record_customer_payment`, `allocate_settlement` or `post_ledger`; the settlement scope can call exactly those plus the intake set and nothing else (no reduction, refund, credit note, reservation, movement); the settlement scope is refused for ordinary tenants, execution fixtures and non-owners
- [x] T018 [P] [US1] [FR-017] Add failing tests in `packages/reality-core/tests/test_demo_data_intake.py`: `process_import_job_bound` accepts `("demo_data", "invoice")` and `("demo_data", "payment")`, keeps savepoint rollback with a `failed` outcome for validation errors of each type, propagates unexpected errors, and still refuses foreign sources
- [x] T019 [FR-021] Add `_SETTLEMENT_OPERATIONS` and the `settlement` flag on `require_demo_intake` in `packages/reality-core/src/reality/services/tenant_policy.py`; add `create_payment_term` to `_CONNECT_OPERATIONS` in `packages/reality-core/src/reality/services/demo_data.py`
- [x] T020 [US1] [FR-017] Generalise `process_import_job_bound` in `packages/reality-core/src/reality/services/core.py` to `SYNTHETIC_SOURCES`, derive interpreter name and failure summary from the source type, and register `("demo_data", "invoice")` and `("demo_data", "payment")` in `SOURCE_INTERPRETERS`

## Phase 5: Demo Data service, second schedule and job (US1, US4)

- [x] T021 [P] [US4] [FR-007] [FR-019] [DR-005] Add failing tests in `packages/reality-core/tests/test_demo_data.py`: preview lists the payment term `DEMO-14-2` under `add` for an empty company and matches it by code for a seeded one; connect creates it; start creates both schedules and the connection references the settlement schedule; pause/stop/disconnect cancel queued work of both; resume resumes both; `set_rate` changes only the order schedule; stop then start mints new ids for both; a pre-existing connection with `NULL` settlement schedule gets one on start
- [x] T022 [P] [US4] [FR-023] Add failing status tests in the same file: `order_to_cash` block with invoices issued, payments received, allocated amount, settled invoices, open residuals, credit created, unmatched payments, last and next settlement; values derive from source records and read services; the block is present with zeros when nothing settled yet
- [x] T023 [P] [US1] [US4] [FR-018] [FR-020] [DR-001] Add failing job tests in `packages/reality-core/tests/test_demo_data_intake.py`: an occurrence emits only due records, oldest first, at most ten, through `enqueue_source` and the bound processor; the invoice precedes payments; an order whose invoice failed yields a recorded but unallocated payment; a "never" plan emits nothing; the seed is read from the generating order schedule (two schedules with different seeds in one connection); orders older than 30 days are not scanned; after a long pause the backlog drains ten per occurrence with no burst; twenty pending or failed imports of any type pause both schedules; retried occurrences reuse stored payloads and identities
- [x] T024 [P] [FR-021] [DR-004] Add failing authorisation tests for the settlement job in `packages/reality-core/tests/test_demo_data_security.py`: wrong connection, disconnected connection, inactive source, changed references, schedule id not matching `settlement_schedule_id`, lost eligibility
- [x] T025 [DR-005] Add `settlement_schedule_id` to `packages/reality-core/src/reality/db/demo_data.py`, migration `packages/reality-core/migrations/versions/0055_demo_settlement_schedule.py` (`down_revision = "0054_target_mappings"`, additive, reversible), and the round-trip test in `packages/reality-core/tests/test_company_setup_migration.py`
- [x] T026 [US4] [FR-007] [FR-019] [FR-020] [FR-023] Implement in `packages/reality-core/src/reality/services/demo_data.py`: payment term prerequisite in `preview`/`connect`, `settlement_scope`, generalised `_imports(source_types, job_types)` and typed `_import_classification`, both-schedule handling in `control`, saturation over all types, `order_to_cash` in `status`
- [x] T027 [US1] [US4] [FR-018] [FR-020] [FR-021] Implement `SettleConfig`, `authorize_settle`, `settle` and `SETTLE = JobDefinition("demo.settle_orders", 1, ...)` in `packages/reality-core/src/reality/jobs/handlers/demo_data.py`; register it in `packages/reality-core/src/reality/jobs/registry.py`
- [x] T028 [US1] Run the independent US1 story end to end with the scheduler test harness (`_tick`) and record the result in `specs/168-demo-order-to-cash/quickstart.md`

## Phase 6: Business stories and exceptions (US2, US3, US5)

- [x] T029 [P] [US1] [US2] [US3] [US5] [DR-001] [DR-002] [DR-003] Add `packages/reality-core/tests/scenarios/test_demo_order_to_cash.py`: order → invoice → exact/short/over/unmatched/late/never through public read services; open items show paid and remaining claim separately; available credit shows the overpayment; candidates appear for the unmatched payment; confirming one through `apply_settlement` in mode `allocate_credit` settles it; a later accepted small remainder (spec 148) closes the short case; every record traces to its SourceRecord and run
- [x] T030 [P] [US2] [US5] [FR-025] Add `packages/reality-core/tests/operational_exceptions/test_payment_differences_from_demo.py`: `unmatched_financial_event` for the overpayment remainder and the unmatched payment; `overdue_receivable` for late and never after the due date, clearing when the late payment settles; the `early_payment_discount_taken` tag when the term explains the short amount
- [x] T031 [US2] [US5] [FR-025] Adjust exception facts or wording only if T030 reveals a gap in `packages/reality-core/src/reality/services/exceptions.py`; otherwise record "no change needed" in `quickstart.md`
- [x] T032 [US2] [US3] [US5] Run the independent US2, US3 and US5 stories and record results in `quickstart.md`

## Phase 7: Candidate confirmation adapters (US3)

- [x] T033 [P] [US3] [FR-014] [FR-015] Add the failing adapter test `packages/reality-core/tests/finance/test_settlement_flows.py::test_payment_credit_context_carries_candidate_reasons`: the guided settlement context and the existing MCP read tool `finance_settlement_context` carry candidate reasons for an unallocated customer payment, and a confirmation through `finance.settlement.apply` mode `allocate_credit` allocates within bounds. (Design simplification recorded in review.md: no new route or tool; the existing context read is extended.)
- [x] T034 [US3] [FR-014] [FR-015] Extend `services/finance/settlement_flows.py::settlement_context` with per-choice `reasons` and a `candidates` list from `payment_intake.payment_candidates`; update the `finance_settlement_context` guidance in `config/command_catalog.yaml`
- [x] T035 [US3] [FR-015] Show suggested invoices with reasons inside the existing settlement dialog (`apps/web/src/finance/SettlementFlow.tsx`, helper `settlementCandidates.ts`), reached from the Payments register's existing "Use available credit" action; contract test `apps/web/scripts/demo-order-to-cash.test.mjs`; localisation keys in all four languages

## Phase 8: Integration panel (US4)

- [x] T036 [P] [US4] [FR-024] Add `apps/web/scripts/demo-order-to-cash.test.mjs` for the `order_to_cash` block helper: rows in reading order, attention rule, finance links naming the synthetic source; four-language i18n audit passes
- [x] T037 [US4] [FR-023] [FR-024] Extend `DemoDataStatus` in `apps/web/src/api.ts`, render the block in `apps/web/src/components/DemoDataIntegration.tsx`, update the preview and catalog copy ("orders, invoices and customer payments"), add localisation keys
- [x] T038 [US4] [FR-024] Saved browser script `apps/web/scripts/demo-data-payments-browser.mjs` run against the local stack in two parts (2026-09-10 start, panel, first settlement, Open items; 2026-09-11 short-payment residual, candidates with reasons, confirmed allocation); results in `quickstart.md`.

## Phase 9: Catalogs, contract amendments and documentation

- [x] T039 [P] [FR-001] Update `packages/reality-core/config/connector_catalog.yaml` (`demo_data` capabilities `order`, `invoice`, `payment`) and the capability assertion in `packages/reality-core/tests/test_integrations.py`
- [x] T040 [P] [DR-004] Update `packages/reality-core/config/tenant_isolation_catalog.yaml`: `settlement_scope`, the settlement job, `payment_intake` operations and the candidates route with their evidence tests; run `tests/tenant_isolation/`
- [x] T041 [P] [DR-005] Document the new column: neither `docs/DATA_MODEL.md` nor `config/data_model.yaml` lists the scheduler or Demo Data tables, so the column is documented in `docs/features/company-setup-demo.md` and the tenant isolation catalog; new test files added to `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T042 [FR-022] Amend `specs/146-company-setup-demo/spec.md` (FR-018, SC-009), `specs/146-company-setup-demo/contracts/demo-data.md` (line "never ... pays", "at most one SourceRecord per occurrence" to the current burst behaviour plus settlement records) and `docs/features/company-setup-demo.md`; reference feature 168
- [x] T043 Update `docs/features/payment_matching.md` status from proposed to implemented for the customer side, and `docs/features/order_to_cash.md` step 7; move `docs/ideas/payment-matching-guide/payments-and-matching.md` and `.de.md` into `apps/docs/content/product-guides/` and `apps/docs/content/de/product-guides/`, link them from sources-and-imports, daily-control and exceptions-and-approvals guides, add the "record first, allocate separately" paragraph to `apps/docs/content/concepts/business-reality-guide/05-finance.md`; run the docs build
- [x] T044 Update `docs/ideas/demo-order-to-cash.md` status to "specified and implemented as feature 168"

## Final Phase: Cross-cutting review

- [x] T900 Run `make spec-check` and the requirement traceability audit against this table
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite from `packages/reality-core` with `../../.venv/bin/pytest -q --tb=short`
- [x] T902 Run the web build, format check, four-language i18n audit, web contract tests and the saved browser scripts
- [x] T903 Review migration 0055 upgrade and downgrade against a disposable database; confirm no automatic reset
- [ ] T904 Review the final diff against the Constitution and every FR/DR; confirm the order interpreter still cannot book money
- [ ] T905 Update `quickstart.md`, `review.md` and `docs/V0_CHECKLIST.md` only after every required check is green
- [ ] T906 Rebase onto main after 165 merges; open the PR with the attribution footer

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T039 | T039 | Done |
| FR-002 | T005 | T007 | Done |
| FR-003 | T005 | T007 | Done |
| FR-004 | T005 | T007 | Done |
| FR-005 | T006 | T008, T009 | Done |
| FR-006 | T006 | T008 | Done |
| FR-007 | T021 | T026 | Done |
| FR-008 | T005 | T007 | Done |
| FR-009 | T010 | T015 | Done |
| FR-010 | T011 | T015 | Done |
| FR-011 | T011 | T015 | Done |
| FR-012 | T012 | T015 | Done |
| FR-013 | T011 | T015 | Done |
| FR-014 | T013, T033 | T015, T034 | Done |
| FR-015 | T033 | T034, T035 | Done |
| FR-016 | T014 | T015 | Done |
| FR-017 | T018 | T016, T020 | Done |
| FR-018 | T023 | T027 | Done |
| FR-019 | T021 | T026 | Done |
| FR-020 | T023 | T026, T027 | Done |
| FR-021 | T017, T024 | T019, T027 | Done |
| FR-022 | T900 (review) | T042 | Done |
| FR-023 | T022 | T026, T037 | Done |
| FR-024 | T036, T038 | T037 | Done |
| FR-025 | T030 | T031 | Done |
| DR-001 | T010, T023, T029 | T015, T027 | Done |
| DR-002 | T010, T011, T029 | T015 | Done |
| DR-003 | T011, T013, T029 | T015 | Done |
| DR-004 | T017, T024, T040 | T019, T040 | Done |
| DR-005 | T021, T025 | T025, T041 | Done |
| DR-006 | T014 | T015, T016 | Done |
| DR-007 | T005 | T007, T015 | Done |
