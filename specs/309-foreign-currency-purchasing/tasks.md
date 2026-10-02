# Tasks: Foreign-Currency Purchasing

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/foreign-currency.md](contracts/foreign-currency.md)

Tests come first in each phase where practical.

## Phase 1: Setup

- [x] T001 Clarify the spec with the owner (Clarifications 2026-10-02)
- [x] T002 Plan, research, data model, contract, quickstart
- [x] T003 Tasks

## Phase 2: Company currency and ledger amounts (FR-001, FR-005, SC-003)

- [x] T004 Tests:
  - the backfill;
  - every new posting carries its company amount, and a company-currency posting carries rate 1;
  - groups balance in both currencies, with rounding remainders;
  - zero amounts only on the exchange-difference account;
  - the company currency's default, its statement and its refusal after a posting;
  - tenant isolation;
  - the migration downgrade.
- [x] T005 Migration `0115`, models, `post_ledger` and group checks, `services/finance/company_currency.py`, the `exchange_difference` role and default account, events, refusals with translations

## Phase 3: Foreign invoices and payments (FR-001, FR-002)

- [x] T006 Tests:
  - an invoice posted at a stated rate, and refused without one;
  - a payment with a gain, and one with a loss;
  - two partial payments leaving nothing in either currency;
  - an unconverted invoice refused;
  - a stale payment review;
  - a reversal taking the difference back;
  - company-currency balances per account.
- [x] T007 Supplier invoice and payment services, reviews, reversal, ledger reads

## Phase 4: Landed cost (FR-006)

- [x] T008 Tests: the conversion basis offered from the invoice rate, with its source as evidence, and the receipt cost read in EUR
- [x] T009 The offer in the receipt costing preview

## Phase 5: Adapters and gates (FR-003)

- [x] T010 Tools, MCP, Web and CLI, with adapter tests
- [x] T011 Catalog gates:
  - data model and docs field rows;
  - reporting graph;
  - command and action catalogs, tool topics;
  - isolation catalog and counts;
  - events;
  - resource catalog and labels;
  - finance docs;
  - coverage matrix and docs generation.

## Phase 6: Web

- [x] T012 Firmenwährung in the finance settings; Kurs on the supplier invoice; Gezahlt in EUR on the supplier payment; both amounts, rate and difference in posting and payment views; translations; browser fixtures

## Phase 7: Stories and Guide (FR-004)

- [x] T013 Business stories G08, I11 and R06
- [x] T014 Promote G08, I11 and R06: Guide catalog, Guide tests, coverage, roadmap, docs

## Phase 8: Verification

- [ ] T015 Full backend suite and web checks
- [ ] T016 Manual check per `quickstart.md`
- [ ] T017 Review of the diff; fix findings
