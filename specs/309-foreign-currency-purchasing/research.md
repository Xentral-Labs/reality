# Research: Foreign-Currency Purchasing

## Today

- `Document`, `Commitment`, `LedgerEntry` and `SettlementAllocation` each carry one `currency`. No entry has a rate or a second amount, and the company has no currency of its own (`Tenant` has none; "EUR" is a column default).
- Cross-currency work is refused in many places:
  - `allocate_settlement` (`settlement_entries_currency_mixed`);
  - `_ledger_group_entries` (`ledger_posting_group_currency_mixed`);
  - payment runs;
  - stated invoice amounts;
  - payment intake;
  - credit, deposit and down-payment settlement.
- `post_supplier_invoice` posts inventory against accounts payable in the document currency. `post_supplier_payment` posts accounts payable against cash in the invoice currency and allocates it to the invoice.
- Open items are derived as the control entry's balance minus active allocations, in the document currency.
- Spec 242 already has an owner-confirmed, source-backed currency `conversion_basis` for receipt costing (`CostConversionBasisRevision`), applied at read time. Nothing is posted from it.

## Decisions

- **Keep one currency per posting group.** A foreign payment stays in the invoice currency, so allocation, open items and every refusal above keep working. Only the company-currency amounts differ between the payable and the cash side.
- **The difference lives in the payment's group.** A separate group would need a company-currency control entry and a cross-currency allocation. A zero document-currency entry on `exchange_difference` balances the group in both currencies without either.
- **The rate is stated, not looked up.** A person states the invoice rate, and the payment states the amount paid. The payment rate is `paid_amount / amount`, kept for display only.
- **Rounding:** company amounts are rounded to cents, and the last entry per side takes the remainder. The payment that settles an invoice's rest takes the invoice's remaining company-currency value, so a fully paid invoice leaves 0 in both currencies.
- **Unconverted legacy postings:** foreign entries posted before this feature keep a null company amount. They are shown as unconverted and cannot be paid across currencies. Adding a rate later is a non-goal.
- **Company currency is fixed once posted.** Changing it would invalidate every company amount, so the change is refused after the first ledger entry.

## Alternatives rejected

- **A company rate table:** more upkeep, and the bank's rate differs from it anyway. The owner chose stated rates.
- **Translation groups beside the postings:** doubles the groups and splits one fact over two records.
- **Converting the document amounts:** loses the stated foreign amounts (Constitution VIII).
