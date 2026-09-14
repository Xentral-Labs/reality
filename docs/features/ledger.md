# Feature: Ledger

## Scope

V0 provides a minimal operational subledger, not statutory accounting or a tax
engine. It records observed financial postings linked to their evidence.

## Settleable documents

Settlement links two control entries on opposite sides of one account. Four document types
carry such an entry, and a wrong side here would balance and still be wrong:

| Document | Control account | Side |
|---|---|---|
| `sales_invoice` | `accounts_receivable` | debit |
| `supplier_invoice` | `accounts_payable` | credit |
| `credit_note` | `accounts_receivable` | credit |
| `customer_refund` | `accounts_receivable` | debit |

A credit note posts the exact reverse of a sales invoice, for the total it states, and needs no
invoice to exist: the receivable going negative is the statement that the company owes the
customer, which is the ordinary consumer return. It is then settled the two ways a business
settles one — netted against an invoice the customer still owes, or refunded — and both go
through the relation payments already use, so the aging register and every money class see the
credit without being told about it.

`open_invoice_amount` answers what any settleable document still owes or claims. Its name is
narrower than what it does, and it subtracts every allocation touching the document's control
entry rather than only those where it is the settled side: an invoice is only ever settled,
while a credit note settles an invoice and is settled by a refund.

## V0 behavior

- Posting a sales invoice creates balanced receivable and revenue entries.
- Posting a supplier invoice creates balanced expense/inventory and payable entries.
- Customer and supplier payments reduce the relevant open balance.
- Every payment is separate evidence (`payment` document, optionally backed by an
  immutable bank/PSP SourceRecord); it never reuses the invoice as its evidence.
- A `settlement_allocation` links the payment's control-account LedgerEntry to the
  invoice's control-account LedgerEntry. One payment may therefore settle several
  invoices and one invoice may receive several payments.
- Credits reverse the relevant invoice amount without changing fulfillment state.
- Partial payments and partial credits remain visible as separate postings.
- Financial status is derived from ledger entries, never stored on delivery documents.
- Reversing a posting appends one complete exact-inverse posting group and records a
  durable `ledger_reversal` relation. The original entries and their Evidence remain
  immutable; inverse entries reach that provenance through the relation.
- Existing settlement allocations remain immutable history. An allocation is inactive
  for operational calculations when either linked posting group is a reversed original.

## Invariants

- A posting group balances to zero in one currency.
- Amounts are positive Decimal values; debit/credit determines direction.
- Every entry is tenant-scoped and has document or source provenance.
- Entries are append-only; mistakes are corrected by reversal.
- A posting group may be reversed once. A reversing group cannot itself be reversed;
  replacement postings are separate normal posting operations.
- Allocations are tenant-scoped, positive, same-currency, and cannot exceed either
  the unallocated payment amount or the invoice's open amount.
- `open`, `partially paid`, and `paid` are derived views; they are never persisted
  on invoice documents.

## Non-goals

Chart-of-accounts administration, tax returns, bank reconciliation, FX revaluation,
period closing, and statutory reporting are outside V0.

## Acceptance stories

1. A EUR 1,470 sales invoice creates equal receivable and revenue postings.
2. A EUR 500 payment leaves EUR 970 customer receivable open.
3. A EUR 100 credit leaves EUR 870 open and does not alter shipped quantity.
4. Supplier invoice/payment mirrors the flow through payable postings.
5. The payment LedgerEntries retain payment evidence while an allocation provides
   the shortest true link to the invoice control entry.
6. Cross-tenant, cross-currency, duplicate, and over-allocation are rejected.
7. Reversing a payment releases its allocations operationally and reopens the invoice
   without deleting allocation history or changing physical fulfillment.

## The Discount Window

The aging register places two dates on every open item and both come from the same place: the
due date is the invoice's own date advanced by the payment term's `due_days`, and the discount
deadline is the same date advanced by that term's `discount_days` where the term states one.
Which term governs an invoice is resolved once — the invoice's own, else its party's, else none
— and passed to both, so a window and a due date are always about the same term.

A term granting no discount places no window, and neither does an invoice whose own date cannot
be read. Every row the register returns carries `due_date`, `discount_date` and the resolved
`payment_term`, so no consumer derives any of them a second time.

## The Credit That Comes the Other Way

A supplier credit note posts as the exact reverse of the supplier invoice — `accounts_payable`
debit, `inventory` credit — with the credit note's own gross amount and nothing derived. The
reverse of the original posting is the one answer that needs no judgement; whether a rebate
rather than a returned item ought to land elsewhere is an accounting argument this product does
not adjudicate.

It posts whether or not any supplier invoice is open, exactly as its selling-side mirror does.
The claim exists either way, and a payable on the other side is the statement that the supplier
owes this company — which is what a credit arriving after the invoice was paid is.

`SETTLEMENT_CONTROL` now names six settleable documents. It records, per type, which control
account settles it and which side of that account the entry sits on, and `open_invoice_amount`
needs no knowledge of any particular type: it takes the balance for that document and flips its
sign by the recorded side. A supplier credit on the debit side of `accounts_payable` therefore
reads as a claim on the supplier with no special handling anywhere.

Settling one is netting it against a supplier invoice of the same supplier, or having the
supplier refund it. Both go through the one allocation service, so a payable falls exactly as a
payment makes it fall and nothing downstream — the aging register, `overdue_payable`,
`purchase_discount_available` — needs telling that a credit was involved.

## Recording and Booking Are Two Acts

A document is recorded as evidence and booked into the ledger by two separate operations, and
both are reachable from the API, the agent tools and the chat surface:

| | Record | Book |
|---|---|---|
| Sales invoice | `POST /documents` | `POST /finance/sales-invoices/postings` |
| Supplier invoice | `POST /documents` | `POST /finance/supplier-invoices/postings` |
| Credit note | `POST /documents` | `POST /finance/credit-notes/postings` |
| Supplier credit note | `POST /documents` | `POST /finance/supplier-credit-notes/postings` |

Keeping them apart is what makes the gap between them representable — `credit_note_unposted`
exists precisely because a credit promised on paper and never booked is a real condition. The
same is true of an invoice.

Until spec 091 the booking half existed for credit notes only. `post_sales_invoice` and
`post_supplier_invoice` were called by the demo and the test suite and by nothing else, so on any
tenant that had never run the demo the aging register was empty by construction and five
conditions could not fire: `overdue_receivable`, `overdue_payable`, `credit_limit_exceeded`,
`purchase_discount_available` and the `early_payment_discount_taken` reason. The postings
themselves were correct throughout; only their reachability was missing.

## The Distance Between Recording and Booking

Because the two acts are separate, the gap between them is reportable, and it is reported for all
four settleable document types: `sales_invoice_unposted`, `supplier_invoice_unposted`,
`credit_note_unposted` and `supplier_credit_unposted`.

Each asks whether the document has a non-zero balance on one control account — the same account
its own posting operation checks to refuse a second posting, so the class and the operation
cannot disagree about what "booked" means. Each learns how long that gap may normally be from
that document type's own history, never from another's.

A reversal posts inverse entries with no document reference, so a reversed document still reads
as booked and is not reported as unbooked. It was booked and then deliberately unbooked, which is
a decision rather than an omission.
