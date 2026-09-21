# Data Model: Commercial Edge Workflows

## DunningNotice

Tenant-scoped opaque identity; evidence document/source; customer, currency, notice date, level 1–3 and exact non-negative fee. Immutable after creation. Effective reversal derives from events and fee posting reversal.

## DunningNoticeInvoice

Tenant-scoped opaque membership between one notice and one customer invoice, unique per pair. Service rules enforce party, currency, posted/open and overdue constraints.

## Financial effects

- Dunning fee: separate `dunning_fee_charge`; debit receivables, credit dunning-fee revenue.
- Bad debt: existing customer settlement adjustment; credit receivables, debit bad-debt expense; allocation to invoice.
- Customer deposit: debit cash, credit receivables.
- Supplier deposit: debit payables, credit cash.
- Deposit clearing: existing SettlementAllocation connects deposit and final-invoice control entries.

No derived balance is stored. Active allocations and reversals determine open amounts and deposit availability.

## Increased commitment quantity

The Commitment retains its original quantity. Existing CommitmentRevision records a greater positive quantity. Quantity in force remains the latest statement and movements stay bounded by it.

## State transitions

- Notice: absent → recorded → reversed; fee independently open/partial/settled/reversed.
- Bad debt: proposed → confirmed → reversed.
- Deposit: available → partially/fully cleared → clearing reversed.
- Commitment: open original → open revised higher → fulfilled; closed commitments cannot revise.
