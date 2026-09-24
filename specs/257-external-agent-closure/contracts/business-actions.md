# Contract: Audit Closure Business Actions

## Free supplier invoice

One explicitly human-confirmed action accepts supplier identity, human invoice number, effective/document date,
currency, source-stated header amount and supported free positions. Positions state their item or
charge meaning, quantity/unit where applicable and received amount. Confirmation atomically records
source evidence, supplier-invoice document/lines and payable postings. It creates no purchase order,
supplier commitment, receipt or stock movement.

## Settlement differences and overpayment

The existing settlement contract remains authoritative:

- actual cash is separate from invoice allocation;
- supported reductions require explicit reason and configured account;
- excess cash remains reusable same-party/same-currency credit;
- existing credit allocation and refund are explicit actions;
- the legacy selected-invoice payment remains bounded by the invoice residual.

## Dunning

Public MCP exposes the existing manual notice context, record and reversal. A notice selects open
overdue invoices of one customer/currency, states date and level and may state an exact non-negative
fee. Reality neither calculates the fee nor sends a reminder.

## Customer credit

Invoice-linked credit uses `invoice_id` plus positions containing invoice-line identity, quantity
and stated amount, a header amount/number, reason and explicit allocation amount. Legacy return
credit retains its separate order-line shape. Invalid mixing is refused before approval.

The public proposal adapter retains the complete selected shape. It never replaces supplied input
with an empty object, and an empty or incomplete credit request creates no durable proposal.

## Received invoice amounts

Invoice positions may state net, tax and gross evidence through the existing finance-detail
contract. Each supplied value is retained exactly and contradictions are refused. Missing net or
tax remains missing; neither is derived from gross, a rate or ledger postings.

## Return disposition

Closed values are `restock`, `quarantine_repair`, `scrap_loss` and `return_to_supplier`.
Disposition targets the arrived return Movement, retains applicable tracking identity and never
implies customer credit. Refusals identify the missing or incompatible movement, commitment,
destination or tracking relationship.

## Operational document types

Public manual operational document creation accepts exactly `sales_order`, `purchase_order`,
`sales_invoice`, `supplier_invoice`, `credit_note` and `supplier_credit_note`. This allow-list
governs the public operational action, not lossless source intake. Unknown upstream labels may be
preserved in immutable source payloads but do not become typed Documents. Specialized business
actions remain preferred where they establish additional relationships or effects.

## Payment filters

Payment direction uses `incoming` or `outgoing`. Party-balance side uses `customer` or `supplier`.
These are different dimensions and are not aliases. Unsupported fields or values are rejected,
not ignored.
