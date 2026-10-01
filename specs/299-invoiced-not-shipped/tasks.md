# Tasks: Invoiced Not Shipped, Down-Payment and Pro-Forma Invoices

**Input**: Design documents from `/specs/299-invoiced-not-shipped/`

**Tests**: Tests precede each phase. Every "not reported" or "not counted" assertion has a positive control; every refusal asserts its code. `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the owner's four decisions in `specs/299-invoiced-not-shipped/spec.md`
- [x] T002 Record today's behaviour and the design in `research.md`, `data-model.md` and `contracts/billing-documents.md`
- [x] T003 Complete the Constitution Check and design in `plan.md`

## Phase 2: Schema and roles

- [x] T004 Failing tests:
  - `document.order_document_id` refuses another tenant's order;
  - `down_payment_offset` refuses a non-positive amount;
  - the `customer_down_payments` role exists and gets a default;
  - the migration upgrades and downgrades, refusing while rows exist.
- [x] T005 Migration `0105_down_payments`; model, `ACCOUNT_ROLES`, transaction matrix, `initialize_accounts`, `SETTLEMENT_CONTROL`, open-item types, `data_model.yaml`; schema-index and reporting-graph gates.

## Phase 3: Down-payment invoice and readiness (FR-002)

- [x] T006 [US1] Failing tests in `core/tests/test_down_payments.py`:
  - a down-payment invoice of 300 for an order of 1,000 is a receivable tied to the order and bills no quantity (no billing reader counts it);
  - a payment settles it;
  - a prepayment order counts the paid 300 as received with 700 required, and is not ready (C14);
  - `prepayment_invoice_missing` is no longer reported once a down-payment invoice exists;
  - refusals for another currency, a non-sales order, a blank number and a non-positive amount (the party is the order's, so no other party can be stated);
  - a reversed down-payment invoice no longer counts.
- [x] T007 [US1] `services/down_payments.py` record and preview, the reviewed tool `down_payment_invoice_record`, and readiness reading the order's down-payment invoices.

## Phase 4: Final invoice offset (FR-003)

- [ ] T008 [US1] Failing tests:
  - recording the final invoice offers the paid 300;
  - stating it posts the offset, the final invoice is open for 700, and the offset row is recorded;
  - a second final invoice offers only what is left;
  - refusals: exceeds paid, another order, a reversed down payment, exceeds the invoice;
  - no offset stated keeps today's behaviour (control);
  - readiness after the rest is paid is ready.
- [ ] T009 [US1] Offers and offsets in `_preview_order_invoice` / `_record_order_invoice` and the reviewed `sales_invoice_record`; refusal codes with translations.

## Phase 5: Pro-forma (FR-004)

- [ ] T010 [US3] Failing tests in `core/tests/test_proforma_invoices.py`:
  - a pro-forma for an order posts nothing and is no open item;
  - it counts neither as invoiced quantity nor as prepayment, with a goods invoice as control;
  - the order inspector lists it;
  - refusals.
- [ ] T011 [US3] `proforma_invoice_record` service and reviewed tool; the inspector section for the order's down-payment and pro-forma invoices and offsets.

## Phase 6: Invoiced but not shipped (FR-001)

- [ ] T012 [US2] Failing tests in `core/tests/test_billed_not_shipped.py`:
  - an invoice for 5 with nothing shipped is reported; it clears after shipping 5, and partly after 3;
  - a down-payment invoice reports nothing (control: a goods invoice does);
  - a cancelled order line;
  - `month_end_billing` returns both lists from the same findings (SC-003).
- [ ] T013 [US2] Class `billed_not_shipped` with every class gate (registry, catalogs, test lists, reference catalog, labels, de/nl/es for label and resolution); the read `month_end_billing`.

## Phase 7: Adapters and Web (FR-005)

- [ ] T014 Failing adapter tests in `core/tests/test_billing_document_adapters.py`: MCP strict schemas, propose then confirm, the read; Web pass-through and the month-end endpoint; another company refused; CLI.
- [ ] T015 MCP, Web API and CLI wiring; command catalog, coverage, guidance, discovery and the web fixture, labels, isolation catalog and counts.
- [ ] T016 Web:
  - order actions "Down-payment invoice" and "Pro-forma";
  - the final-invoice dialog with offers and the offset;
  - the order inspector section;
  - the finance month-end billing section;
  - translations, with `npm run test:i18n`, the audit, prettier and the build.

## Phase 8: Stories and Guide (FR-006)

- [ ] T017 Business stories E03, Q01, E11 and C14 in `core/tests/scenarios/test_catalog_finance.py`.
- [ ] T018 Promote E03, Q01, E11 and C14 with story-first evidence and English and German keywords; check neighbouring questions. Update coverage, the roadmap and the coverage matrix, then run `make docs-generate`.

## Phase 9: Verification

- [ ] T019 Full backend suite from a clean worktree and the web checks (run alone, not beside a stack build)
- [ ] T020 Manual check per `quickstart.md` on an isolated stack
- [ ] T021 Review of the diff; fix findings
