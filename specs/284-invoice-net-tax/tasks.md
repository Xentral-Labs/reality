---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Invoices state net and tax

**Input**: `spec.md`, `plan.md`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

`core/` stands for `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Close clarification markers in `specs/284-invoice-net-tax/spec.md` (per position only; owner decision 2026-09-26)
- [x] T002 All Constitution Check rows PASS in `specs/284-invoice-net-tax/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings (2026-09-26: no CRITICAL findings; SC-001 depends on spec 282, recorded in plan and quickstart)

## Phase 2: Stated amounts check (blocks all stories)

- [ ] T004 [P] [FR-004] [DR-001] Write failing `core/tests/test_invoice_stated_amounts.py`:
  - `::test_net_plus_tax_contradiction_is_refused_and_records_nothing` (with a consistent positive control);
  - unknown keys, a negative or over-precise value, a mismatched detail gross and a mismatched currency are each refused.
- [ ] T005 [FR-004] Implement `_stated_invoice_amounts` and call it from `_preview_order_invoice` for the single and each selected position (`core/src/reality/services/core.py`).

## Phase 3: User Story 1 — single position (P1)

- [ ] T006 [P] [US1] [FR-002] [FR-007] [DR-001] [DR-003] Write failing tests:
  - `::test_single_position_records_stated_net_and_tax` for sales and supplier, through the tool and through MCP `sales_invoice_record_propose` with confirmation; the line detail and the source payload equal the stated strings;
  - `::test_stated_net_makes_the_contribution_a_candidate`;
  - `::test_gross_only_is_unchanged`;
  - `::test_ledger_entries_equal_a_gross_only_invoice` (DR-004);
  - `::test_credit_notes_are_unchanged`.
- [ ] T007 [US1] [FR-002] Add `reality_finance_v1` to `record_sales_invoice`, `record_supplier_invoice` and `_record_order_invoice`: intent binding, preview arguments and source payload (`core/src/reality/services/core.py`).
- [ ] T008 [US1] [FR-002] Add the top-level `reality_finance_v1` to the MCP single-position schemas (`core/src/reality/mcp/catalog.py`), then `make docs-generate`.

## Phase 4: User Story 2 — multi position (P1)

- [ ] T009 [P] [US2] [FR-003] Write failing tests:
  - `::test_multi_position_keeps_each_positions_amounts` through `prepare_delivery_action`, review and confirmation;
  - `::test_position_without_detail_stays_gross_only`;
  - `::test_gross_only_review_token_is_unchanged`.
- [ ] T010 [US2] [FR-003] Carry the stated detail in `creation["selections"]` when present (`core/src/reality/services/core.py`), and bind it in the post-execution verification (`core/src/reality/services/invoice_actions.py`).

## Phase 5: Web (FR-001, FR-005)

- [ ] T011 [P] [FR-001] [FR-005] Write failing `apps/web/scripts/invoice-net-tax-contract.test.mjs`:
  - the per-position fields are sent as `reality_finance_v1`;
  - gross is never filled from net + tax;
  - the review reads the stated amounts.
- [ ] T012 [FR-001] [FR-005] In `apps/web/src/unified/InvoiceCard.tsx`, add the per-position net and tax inputs and show them in the review. Add the types to `apps/web/src/api.ts` and de/nl/es to `apps/web/src/localization.tsx`.
- [ ] T013 [FR-001] [FR-005] Browser proof: extend `apps/web/scripts/unified-invoice-entry-browser.mjs`, or add `invoice-net-tax-browser.mjs` if the existing script is broken on main.

## Phase 6: User Story 3 — supplier invoices (P2)

- [ ] T014 [P] [US3] Write failing `::test_supplier_invoice_net_basis_is_available_to_cost_evidence`.
- [ ] T015 [US3] Confirm or adjust how `cost_evidence` reads the stated net for a supplier invoice line (`core/src/reality/services/costing.py`).

## Final Phase

- [ ] T900 `make spec-check`; add the new test family to `docs/SPEC_COVERAGE_MATRIX.md`.
- [ ] T901 Ruff (own files only, `--no-cache`) and the complete backend suite from a clean detached worktree.
- [ ] T902 `make web-build`, i18n audit, node contracts, browser test.
- [ ] T903 `make docs-generate`, with `apps/docs/node_modules` present in the worktree.
- [ ] T904 [SC-001] Live: a local integration of 282 and 284 on the isolated stack. Record an invoice with net and tax through the form, prepare and confirm the contribution review, and DB1 appears. Record the result in `quickstart.md`.
- [ ] T905 Update `docs/features/order_to_cash.md` and `docs/features/procure_to_pay.md`.
- [ ] T906 Review the final diff against the Constitution and every FR and DR.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T011, T013 | T012 | Pending |
| FR-002 | T006 | T007, T008 | Pending |
| FR-003 | T009 | T010 | Pending |
| FR-004 | T004 | T005 | Pending |
| FR-005 | T011, T013 | T012 | Pending |
| FR-006 | T006, T009 | T005, T010 | Pending |
| FR-007 | T006 | T007 | Pending |
| DR-001 | T004, T006 | T005, T007 | Pending |
| DR-002 | T906 | — | Pending |
| DR-003 | T006 | T007, T008 | Pending |
| DR-004 | T006 | T007 | Pending |
| SC-001 | T904 | — | Pending |
