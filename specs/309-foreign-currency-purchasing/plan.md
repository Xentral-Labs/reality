# Implementation Plan: Foreign-Currency Purchasing

**Branch**: `309-foreign-currency-purchasing` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

The company gets a company currency, and every ledger entry gets a second amount in it.

- **Company currency:** a reviewed statement in the finance settings, kept as a version of `internal_company_currency` (spec 320 pattern). It defaults to EUR and is refused once the company has a ledger entry.
- **Second amount:** `ledger_entry.company_amount` and `ledger_entry.exchange_rate`.
  - A company-currency entry carries its amount twice at rate 1.
  - A foreign supplier invoice is posted at the rate a person states.
  - Every posting group must balance in both currencies.
- **Paying across currencies:** a supplier payment of a foreign invoice states `amount` (settled, invoice currency) and `paid_amount` (company currency).
  - Its posting group stays in the invoice currency, so the allocation and the open items work unchanged.
  - The payable entry carries the invoice's company-currency value of the settled part, and the cash entry carries what was paid.
  - The difference is one more entry of the same group on the new `exchange_difference` account. It has a document-currency amount of 0 and carries only the company-currency difference, as a credit for a gain and a debit for a loss.
- **Landed cost:** the invoice rate is offered as a spec 242 currency conversion basis, with the invoice's source as evidence.

See [research.md](research.md), [data-model.md](data-model.md) and [contracts/foreign-currency.md](contracts/foreign-currency.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Storage**: PostgreSQL; migration `0115_company_currency`

**Testing**:
- ledger, posting, payment, reversal, settings, costing, adapter and story tests;
- the finance, payment, settlement, reversal and costing suites as regression;
- web checks, browser fixtures and the full suite.

**Performance Goals**: No extra query per entry; the payment reads the invoice's company-currency remainder from its control entry and its allocations, which the open-amount read already loads.

**Constraints**:
- unchanged results for companies that post only in their company currency;
- the one-currency-per-group invariant is kept;
- tenant-scoped;
- reviewed tools.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The stated rate and the stated paid amount are kept on the posting proposal and its event; the company currency is a source version. |
| II. Reality is the operational authority | PASS | No document status; open items stay derived from the ledger and its allocations. |
| III. Proven schema only | PASS | `company_amount` is summed by every company-currency balance, the group balance check and the remainder on each payment; `exchange_rate` is shown and checked on every posting. The company currency is read on every posting. |
| IV. Tenant and service boundaries | PASS | All posting stays in `post_ledger`; tools, MCP, Web and CLI call the same services. |
| V. Specification and test evidence | PASS | Tests planned per phase, with positive controls. |
| VI. Explainable Web product | PASS | A posting shows both amounts and the rate; a payment shows its difference and the invoice value it compares against. |
| VII. Simplicity and storage discipline | PASS | Two columns and one small table; no second ledger or translation groups. |
| VIII. Received values are recorded, never recomputed | PASS | The rate and both payment amounts are kept as stated; the difference is posted once, from them, and never recalculated. |

## Design

1. **Schema:** migration `0115`:
   - `company_currency` (tenant, currency, source).
   - `ledger_entry.company_amount` (Numeric 18,4) and `exchange_rate` (Numeric 18,8), both nullable.
   - Backfill: existing EUR entries get `company_amount = amount` and rate 1. Other currencies stay null, meaning unconverted.
   - Downgrade refuses while any entry carries a rate other than 1 or an exchange difference.
2. **Company currency:** `services/finance/company_currency.py`.
   - `company_currency(session, tenant)` reads it, with EUR as the default.
   - `set_company_currency` is reviewed, and refused once the company has a ledger entry.
3. **Posting:** `post_ledger(..., exchange_rate=None, company_amounts=None)`.
   - A posting in the company currency sets rate 1 and copies the amounts.
   - A foreign posting multiplies by the stated rate and rounds to cents. The last entry on each side takes the cent remainder, so the group balances in company currency.
   - Explicit `company_amounts` are used by the payment.
   - A foreign posting without a rate stays unconverted. The reviewed supplier invoice tools refuse it (`exchange_rate_required`).
   - `_ledger_group_entries` also checks the company-currency balance.
   - Zero document-currency amounts are allowed only for `exchange_difference` entries.
4. **Supplier invoice:** `supplier_invoice_record` and `supplier_invoice_post` take `exchange_rate`.
   - It is required when the invoice currency differs from the company currency, and refused when it is the same.
   - It is shown in the review and kept in the posting event.
5. **Supplier payment:** `post_supplier_payment` and `supplier_payment_post` take `paid_amount`.
   - It is required for a foreign invoice and refused for an unconverted one.
   - The payable side is the invoice's company-currency value of the settled part: settled amount × invoice rate, rounded to cents. A payment that settles the rest of the invoice takes the remaining company-currency value instead.
   - The cash side is `paid_amount`, and the difference goes to `exchange_difference`.
   - The review shows the payment rate, the invoice rate and the difference.
   - The allocation stays in the invoice currency, as today.
6. **Reversal:** a reversal copies `company_amount` and `exchange_rate` onto its reversing entries, so a reversed payment takes its difference back.
7. **Accounts:**
   - new role `exchange_difference` in `domain/finance.py`;
   - a default account, the resource catalog and the data model;
   - a company-currency balance per account in the ledger reads.
8. **Landed cost:** a receipt costing whose goods part comes from a foreign invoice offers `conversion_basis` prefilled with the invoice's rate and its source record as evidence. It is confirmed through the existing spec 242 review.
9. **Adapters:**
   - tools `company_currency_set` (reviewed) and `company_currency` (read);
   - the new arguments on the supplier invoice and payment tools;
   - MCP schemas;
   - Web `GET /finance/company-currency` and `POST /finance/company-currency/proposals`;
   - CLI `finance company-currency show|set`.
10. **Web:**
    - "Firmenwährung" in the finance settings.
    - "Kurs" on the supplier invoice form when its currency differs.
    - "Gezahlt in EUR" on the supplier payment.
    - Company-currency amounts, rate and exchange difference in the posting and payment views.
    - Translations.
11. **Stories and Guide:** G08, I11 and R06, then the promotion, coverage, roadmap, matrix and docs.

## Rollback

The downgrade refuses while converted foreign postings or exchange differences exist. Companies that post only in EUR are unaffected: their entries carry the same amount twice.
