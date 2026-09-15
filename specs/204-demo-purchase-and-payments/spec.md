# Feature Specification: The demo company also buys and gets paid

**Language**: English

**Created**: 2026-09-15
**Status**: Accepted scope (owner: no payments are in it; a few payments, purchase
orders and goods receipts would be good, supplier invoices fully or partly paid)

## Context and Intent
The canonical profile bills but never settles. It seeds 24 posted sales invoices and
not one customer payment, so every invoice is open, the party balances show one
undifferentiated receivable and nothing in Finance ever moves. The purchase side is
thinner still: three purchase orders, one partial goods receipt, no supplier invoice
and no supplier payment, so the whole purchase-to-pay chain is invisible in a company
meant to demonstrate it.

The continuous Demo Data stream does settle, but only the orders that arrive after the
company is created, and only for the sales side.

### Non-Goals
The customer pool and its order distribution (feature 200), the continuous stream, the
number of items or locations, dunning, period close, and any new business capability.
Nothing here may bypass the posting services a person would use.

## User Scenarios & Testing
### US1 — See money arrive (P1)
A new demo company shows customer payments against its own invoices: most of the older
ones settled in full, a few paid in part with a visible residual, the newest still open.
Open items, party balances and the journal therefore differ from one another.

### US2 — Follow a purchase from order to payment (P1)
The company holds purchase orders in every interesting state: ordered and nothing
received, partly received, received in full and awaiting an invoice, invoiced and
unpaid, invoiced and partly paid, invoiced and settled.

### US3 — Explain a residual (P2)
A partly paid invoice, on either side, states an amount that is genuinely less than
what it bills, so the difference is derivable rather than asserted.

### Edge cases
Payments are recorded through the same posting services a person uses, under the
profile's own initialization authority, and never by writing ledger rows directly.
Every payment belongs to an invoice of the same company and party. Seeded amounts are
authored, so two companies from the same profile version settle identically. Stock from
the new goods receipts must stay consistent with what the existing cases assert.

## Requirements
- **FR-001**: The profile seeds customer payments against its own sales invoices in
  three authored states — settled in full, paid in part, unpaid — with at least ten
  invoices settled, at least three carrying a residual and at least four untouched.
- **FR-002**: The profile seeds six purchase orders across its three suppliers covering
  six states: not received, partly received, received without an invoice, invoiced and
  unpaid, invoiced and partly paid, invoiced and settled.
- **FR-003**: Goods receipts are recorded against the purchase commitment they fulfil,
  so received quantity and stock follow from the movement rather than from a flag.
- **FR-004**: Supplier invoices are built the way the profile already builds a sales
  invoice — a document with lines that state the purchase order line they bill, then
  its posting entry point — and supplier payments are recorded against them.
- **FR-005**: The profile authority permits exactly the settlement operations this
  needs and nothing more. It stays bound to an initializing run of the canonical
  preset inside one transaction, as it is today.
- **FR-006**: Assignment of states to cases is authored versioned vocabulary, so the
  same profile version seeds the same settlement everywhere. Existing case keys,
  the manifest bound, the payload schema and the profile version are unchanged.

## Success Criteria
A freshly created demo company reports customer payments in all three states, a
receivable that is smaller than the amount invoiced, six purchase orders in six
distinct states, supplier invoices with a payable that is settled, partly settled and
untouched, and goods receipts that account for the received quantity. Two companies
from the same profile version report identical settlement. Existing stock, case and
count assertions are unchanged.

## Assumptions and Dependencies
`post_customer_payment`, `post_supplier_invoice` and `post_supplier_payment` already
exist and already enforce their own rules; this feature only makes them available to
the profile authority. `record_supplier_invoice` is deliberately not used: it commits
inside itself, which the profile scope forbids, and the sales invoice already shows the
transaction-bound way to do it. The seed grows by roughly 36 service calls, which the
verification records. No schema change and no migration.

## Requirement Traceability
| Requirement | Proof |
|---|---|
| FR-001, FR-003 | Scenario test over payments per state, the residual, and stock from receipts |
| FR-002, FR-004 | Scenario test over the six purchase states and their payables |
| FR-005 | The permitted operation set is asserted, and a denied operation stays denied |
| FR-006 | Two companies report identical settlement; existing suites stay green |
