# Analysis: Party balances (170)

**Date**: 2026-09-11 · **Artifacts**: spec.md, plan.md, tasks.md · **Result**: consistent after two corrections

## Findings

1. **Overdue rule named wrongly (corrected).** Spec FR-003 and the plan said "original due date".
   The open items rows carry `original_due_date` only for imported opening items; invoices get
   their due date from the payment-term rule in `with_invoice_aging` / `aging_register`, and the
   `overdue_*` classes consume that register with the condition `status in {open, partial}` and
   `due_date < as_of.date()`. Spec FR-003, the existing-contracts bullet, the edge case and the
   plan's service design now name the aging register. The implementation consumes it.
2. **Party identity across the two derivations (checked).** Open item rows carry the document's
   `party_id`; credit rows carry the ledger entry's `party_id`. Both are the same Party ids, so
   grouping by `(party_id, currency)` is safe. Party names come with the rows; no extra lookup.
3. **Credit rows are paged (planned).** `available_credit_items` sorts and pages internally; the
   aggregation needs every outstanding row. The refactor into `available_credit_rows` plus the
   paging wrapper (T007) keeps the wrapper's output identical; the existing credit tests guard it.
4. **Sides and control accounts (checked).** Open items mark `flow` by the control account
   (`accounts_receivable` → receivable); credits take `side` and resolve the same account role.
   The balances service maps side customer → receivable rows + customer credits, supplier →
   payable rows + supplier credits.
5. **Web labels (checked).** "Customers", "Suppliers" and "Balance" exist in de, nl and es;
   "Balances", "Credit only", "Of which overdue", "Oldest due", "Open documents" and
   "Credit documents" are new and must be added in all three locales for the i18n audit.
6. **Register profile (checked).** `RegisterTable` keys profiles by `route:view`; a
   `finance:balances` profile with widths and sort keys is required for header sorting.
7. **No spec gap on currencies.** Two rows per party for two currencies; totals per currency,
   never summed across, matching `finance_balances`.

## Traceability

Every FR and DR has a test task and an implementation task in `tasks.md`; no `[NEEDS
CLARIFICATION]` remains; no schema, no migration.
