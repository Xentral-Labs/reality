# Tasks: Party balances

**Input**: [spec.md](spec.md), [plan.md](plan.md)
**Gate**: Constitution Check passed; no clarification markers

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Phase 1: Failing proof (service and tool)

- [x] T001 [US1] [FR-001] [FR-002] [FR-004] [FR-005] Add `packages/reality-core/tests/finance/test_party_balances.py::test_party_rows_sum_open_items_and_credits`: one customer with three posted invoices (one paid, one partially paid, one overpaid) and one booked credit note; assert one EUR row with `open`, `credit`, `balance = open - credit`, `open_count 2`, `credit_count 2`, `oldest_due_date`; a second customer with everything settled produces no row; an invoice in USD for the first customer produces a second row and no converted total
- [x] T002 [US1] [FR-003] Add `::test_overdue_follows_original_due_date_and_as_of`: with `as_of` before every due date `overdue` is `0`; with `as_of` after the oldest due date `overdue` equals that invoice's open amount; an invoice without a due date never counts
- [x] T003 [US2] [FR-001] [FR-005] Add `::test_credit_only_lists_each_party_once`: two overpayments and one credit note for one party give one row with the summed credit and `credit_count 3`; `credit_only=True` hides parties without credit; a credit used up by a later allocation no longer counts
- [x] T004 [US4] [FR-008] Add `::test_tool_matches_view_and_is_tenant_scoped`: `TOOLS["finance.party_balances.list"]` returns the same rows as the service for the same arguments; a second tenant sees no rows; the tool is not mutating
- [x] T005 [FR-002] Keep `tests/finance/test_available_credits.py` and `tests/finance/test_credit_reads.py` green through the refactor of T007 (no change to those files)

## Phase 2: Service

- [x] T006 [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] Add `packages/reality-core/src/reality/services/finance/balances.py` with `party_balances(session, tenant_id, *, side, credit_only=False, query="", page=1, size=50, sort="balance", sort_direction="desc", as_of=None)` aggregating `core.financial_open_items` (flow by side, status not settled; `open`, `overdue` by `original_due_date < as_of`, count, minimum due date) and the credit rows of T007 per `(party_id, currency)`; drop empty rows; `credit_only`; name search; sort keys `party`, `open`, `overdue`, `credit`, `balance`, `oldest_due`; totals per currency before paging; Decimal only, amounts as strings
- [x] T007 [FR-002] Split `available_credit_items` in `packages/reality-core/src/reality/services/finance/credits.py` into an unpaged `available_credit_rows(session, tenant_id, *, side, status, party_id=None)` and the existing paging wrapper; output of the wrapper stays identical
- [x] T008 [FR-007] Add an optional `party_id` filter to `core.financial_open_items` consumers used by the open items register and to `available_credit_rows`, so both registers can be opened for one party

## Phase 3: API and App

- [x] T009 [FR-006] [FR-007] `packages/reality-core/src/reality/web/api.py::tenant_open_items`: route `flow` values `customer-balances` and `supplier-balances` to `party_balances` with `as_of` = request instant, accept `credit_only` and `party_id` query parameters, and pass `party_id` into the open items and credit flows
- [x] T010 [FR-006] `apps/web/src/unified/routing.ts`: `financeView` gains `"balances"`; add `partyId` and `creditOnly` selection fields with URL round-trip; extend `apps/web/scripts/finance-settings-routing.test.mjs` (or a sibling) with the round-trip assertions
- [x] T011 [FR-006] [FR-007] `apps/web/src/unified/FinancePage.tsx`: tab "Balances" with side selector, search, "Credit only" checkbox, `RegisterTable` profile `balances` (party, currency, open, of which overdue, credit, balance, open documents, credits, oldest due; numeric columns right-aligned, sortable), row actions "Open items" and "Credits" that navigate to the existing flows with `partyId`; `apps/web/src/api.ts` gains `partyBalances(...)` and `openItems(..., partyId)`
- [x] T012 [FR-006] Add the new labels to `apps/web/src/localization.tsx` in de, nl and es (Balances, Customers, Suppliers, Credit only, Balance, Of which overdue, Oldest due, Open documents, Credits) and keep `npm run i18n:audit` green
- [x] T013 [FR-006] [FR-007] [DR-004] Extend `apps/web/scripts/unified-finance-browser.mjs`: open Balances, assert the fixture row, sort by balance and by overdue, open the row's open items and assert only that party's documents are listed, open its credits likewise

## Phase 4: Agent read and catalogs

- [x] T014 [FR-008] Add `TOOLS["finance.party_balances.list"]` in `packages/reality-core/src/reality/tools/application.py` (arguments `side`, `credit_only`, `query`, `limit`; non-mutating) and `MCPToolDefinition("finance_party_balances", …, "read", "finance", …)` in `packages/reality-core/src/reality/mcp/catalog.py` with `side` required and enumerated
- [x] T015 [FR-008] Add `capability_guidance.finance_party_balances` to `packages/reality-core/config/command_catalog.yaml`: purpose, `use_when` (who owes the most, who holds credit, a party's position before a call or a payment run), `do_not_use_when` (deciding that a credit may be netted, judging creditworthiness, converting currencies), `required_context`, `verification` (the drill-down documents are the proof; a balance proves a position, not that a customer will pay), examples with `reason` and `do_not_use`
- [x] T016 [FR-008] Add `tool:finance.party_balances.list` to the `agent_credit_reads` family in `packages/reality-core/config/tenant_isolation_catalog.yaml` (widen the description to balances); update the count assertions in `packages/reality-core/tests/test_application_catalog.py`; keep `tests/test_capability_guidance.py` and `tests/test_mcp_read_contract.py` green
- [x] T017 [FR-008] Add the `finance_party_balances` row by hand to `apps/docs/content/catalogs/mcp-tools.md` and `apps/docs/content/de/catalogs/mcp-tools.md` (the generator drifts unrelated tables)

## Phase 5: Documentation

- [x] T018 [FR-009] Receivables playbook, EN and DE: in "Overpayment, and using the excess later" the step "Ask: who paid too much?" reads `finance_party_balances` with `credit_only` and shows one row per customer; "Watch the money" names the view and the tool. Purchasing playbook "Watch the supply side" names the supplier side. German uses Saldenliste, Geschäftspartner, Minderzahlung
- [x] T019 [FR-009] Add a "Balances" paragraph to the finance chapter `apps/docs/content/concepts/business-reality-guide/05-finance.md` (EN, DE): what the view sums, the overdue rule, what it does not prove; link it from the playbooks
- [x] T020 [DR-001] [DR-002] Record the derivation and its limits in `docs/features/payment_matching.md` or the finance feature doc, and add a row to `docs/SPEC_COVERAGE_MATRIX.md` for `tests/finance/test_party_balances.py`

## Phase 6: Review

- [x] T021 Run `make lint`, `make spec-check`, `tests/finance`, `tests/test_application_catalog.py`, `tests/test_capability_guidance.py`, `tests/test_mcp_read_contract.py`, then the complete backend suite; `npm run i18n:audit`, `npx tsc -b`, `node --test scripts/*.test.mjs` in `apps/web`; the Finance browser suite against the local stack; `npm test` and `npm run build` in `apps/docs`
- [x] T022 Review the diff against the Constitution and the review risks in `plan.md`: no migration, no division in amounts, credit register output unchanged, every row explainable through the drill-down
- [x] T023 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T001, T003 | T006 | Done |
| FR-002 | T001, T005 | T006, T007 | Done |
| FR-003 | T002 | T006 | Done |
| FR-004 | T001 | T006 | Done |
| FR-005 | T001, T003 | T006 | Done |
| FR-006 | T010, T013 | T009, T010, T011, T012 | Done |
| FR-007 | T013 | T008, T009, T011 | Done |
| FR-008 | T004, T016 | T014, T015, T016, T017 | Done |
| FR-009 | T021 (docs build) | T018, T019 | Done |
| DR-001, DR-002 | T022 | T020 | Done |
| DR-003 | T022 | T006 | Done |
| DR-004 | T013 | T011 | Done |

## Dependencies

- T006 depends on T007 (credit rows) ; T008 depends on T007.
- T009 depends on T006 and T008; T011 depends on T009 and T010; T013 depends on T011 and T012.
- T014 depends on T006; T015–T017 depend on T014.
- T018 and T019 depend on T014 (tool name) but not on the App.
- Parallel: T001–T004 (tests) with each other; T010 and T012 with the service work; T015–T017 with each other.
