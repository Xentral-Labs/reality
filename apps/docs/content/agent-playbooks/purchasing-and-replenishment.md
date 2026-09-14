# Playbook: Purchasing and replenishment

From a shortage to a paid supplier invoice. Nothing on this side arrives by itself: Reality shows
uncovered demand, but the purchase order, the goods receipt, the supplier invoice, its booking and
the payment run are all orchestrated from outside and decided by a person.

Each situation is one line of context and a few numbered steps: what you pull up, what you say, what
the agent prepares, what you decide, what you check. The tool behind a step stands at the end of its
line after an arrow.

Read [Run a business on Reality with agents](./) first for the loop and the rules.

## What Reality holds and derives

- A purchase order is a Document with lines; each line has an incoming Commitment (the supplier's
  promise) with quantity and due date. An inbound Shipment/Package may carry carrier and tracking
  details; only its receipt Movement fulfils the promise and increases stock. The open quantity is
  derived.
- A supplier invoice is a Document whose lines name the purchase order lines they bill. Recording
  and booking are two steps; only a booked supplier invoice is a payable.
- `item_supply_demand` shows per item `physical`, `reserved`, `available`, `incoming` (open supplier
  promises), `open_customer_demand`, `uncovered_demand`, `projected` and `blocked_order_count`.
  `commitments_list` shows the supplier promises with their due dates.
  `inventory_read(view="aggregate"|"location")` shows stock as it is.
- `payment_run_preview(pay_by)` shows which supplier invoices are worth paying by that date, what
  each supplier is owed, which invoices are withheld and why (reversed, duplicate, settled) and
  where an early-payment discount is still available. `finance_balances` gives the payable position
  per currency.

Exceptions that belong to this area: `overdue_incoming_supplier_commitment`, `billed_not_received`,
`receipt_unbilled`, `invoice_price_differs`, `sold_below_purchase_price`, `units_not_comparable`,
`supplier_invoice_unposted`, `duplicate_supplier_invoice`, `overdue_payable`,
`purchase_discount_available`, `supplier_credit_unposted`, `supplier_credit_unclaimed`,
`supplier_return_not_credited`, `supplier_credit_not_returned`, `stock_expired`.

The examples use one supplier, Nordlicht Leuchten GmbH, one item, the desk lamp LAMP-01, and small
quantities.

## Situations

### Find what to buy

Customer demand that stock and open supplier promises do not cover. Reality shows the gap; the order
quantity is your rule.

1. **List:** "What do we need to buy this week?" → `item_supply_demand` · `fulfillment_blockers`
   LAMP-01 available 0, demand 12, incoming 0, uncovered 12, 2 orders blocked · CABLE-2M uncovered
   40, 50 incoming 18th
2. **Rule:** "Boxes of 12, keep 20 on the shelf; propose 36." The agent does your arithmetic and
   names supplier and price → `business_records_discover`
3. **Check:** nothing changed; the list is the input to the next situation.

### Place a purchase order

The purchase order is evidence of what you ordered; the supplier's promise becomes an incoming
promise per line.

1. **Say:** "Order 36 LAMP-01 from Nordlicht at list price, to the main warehouse by the 18th."
2. **Agent:** PO-0210, one line 36 × 30.00, `promised_at` 18th, supplier's payment term; amounts
   from the price list, never computed → `order_create_propose` `direction="purchase"`
3. **You:** approve; then send the order through your own channel.
4. **Check:** supplier promise 36 due 18th → `commitments_list` · incoming 36, uncovered 0 →
   `item_supply_demand` · blocked orders show the date → `fulfillment_blockers`

### Receive goods

The truck is at the door with 3 boxes. A receipt states what was counted, not what was ordered.

1. **See:** "What is due from Nordlicht?" → PO-0210, 36 LAMP-01, due 18th → `commitments_list` ·
   late ones → `overdue_incoming_supplier_commitment`
2. **Say:** "Received 36 LAMP-01 into the main warehouse." Damaged box: "Received 24, 12 go back."
3. **Agent:** inbound Package for Nordlicht with carrier/tracking when known and a receipt Movement
   of 36 against the promise; lot or serial when inventory is tracked → `shipment_receive_propose`
   `purpose="supplier_delivery"` · damaged goods sent back use an outbound Package with
   `shipment_dispatch_propose` `purpose="supplier_return"` (credit situation below)
4. **You:** approve the count. A partial receipt leaves the rest open.
5. **Check:** Package, tracking and receipt contents → `shipment_explain` · stock +36 →
   `inventory_read` · promise fulfilled or remainder → `commitments_list` · blocked customer orders
   ready → `fulfillment_queue`. A supplier or carrier `delivered` event alone does not increase
   stock.

### Record and book the supplier invoice

ER-4471 arrived: 36 lamps, 1,080.00. Record, then book; only the booked invoice is a payable.

1. **Say:** "Record Nordlicht's ER-4471, 1,080.00, for PO-0210, 36 at 30.00."
2. **Agent:** invoice with its line naming the PO line; amounts as the invoice states them →
   `supplier_invoice_record_propose`
3. **You:** approve the record; the booking is offered next → `supplier_invoice_post_propose`. Look
   at the check below before approving it.
4. **Check:** no longer unposted → `supplier_invoice_unposted` · payables +1,080.00 →
   `finance_balances` · ER-4471 in Open items with its due date

### The three-way check

Order, receipt and invoice should agree. Reality names the difference; it never rules for the
supplier.

1. **List:** "Which supplier invoices do not match?" → `exceptions_list`: `billed_not_received`,
   `receipt_unbilled`, `invoice_price_differs`, `duplicate_supplier_invoice`, `units_not_comparable`
2. **One case:** "Explain the price difference on ER-4471." → order 30.00, invoice 31.50, 36 lamps,
   54.00 more → `exception_explain`
3. **Settle with the buyer:** the rise was not agreed.
4. **Say:** "Book as stated and claim 54.00 back" (booking, then supplier credit below) · "Correct
   the lines to what the supplier confirms" → `document_lines_correct_propose`, manual invoices only
   · "Do not book it, I am sending it back."
5. **You:** approve the chosen proposal, or none.
6. **Check:** entry clears when the records agree → `exceptions_list`; until then the invoice stays
   out of the payment run by your choice.

### Pay suppliers with a payment run

Friday: what to pay by next week, which discounts are worth taking, what is withheld and why. The
bank transfer is yours.

1. **Preview:** "Payment run, pay by next Friday." → ER-4471 Nordlicht 1,080.00 due 20th · ER-4460
   Kabelwerk 640.00, 2 % by Tuesday = 12.80 · withheld ER-4402, duplicate · total 1,720.00 →
   `payment_run_preview` `pay_by` · `overdue_payable`, `purchase_discount_available`
2. **Select:** "Pay both, take the discount on ER-4460, so 627.20." Leaving one out is the only hold
   today.
3. **Agent:** run with exactly those invoices and amounts; a mismatching total is refused →
   `payment_run_propose` `expected_total=1707.20` · one invoice alone →
   `supplier_payment_post_propose`
4. **You:** approve, then transfer at the bank. Reality recorded what you decided to pay.
5. **Check:** both settled, ER-4460 12.80 discount, 627.20 paid → `finance_settlement_context` ·
   payables −1,707.20 → `finance_balances` · entries gone → `exceptions_list`

### Supplier payment differences

Mirror of the customer side: paid less with the supplier's agreement, or paid too much.

1. **Paid less, agreed:** "We paid 1,026.00 on ER-4471; Nordlicht waived 54.00, mail of the 19th." →
   payment 1,026.00 → `finance_settlement_propose` mode `payment` · reduction 54.00 with the mail as
   `agreement` → `finance_adjustment_context`, `finance_adjustment_propose`. Approve both. Our wish
   to withhold reduces nothing; their agreement does.
2. **Paid too much:** "We paid 1,180.00 on ER-4471 by mistake." → 1,080.00 allocated, 100.00
   supplier credit → mode `payment`, `allocation_amount` < `amount` · later "use the 100.00 on
   ER-4490" → mode `allocate_credit` · or "Nordlicht refunded 100.00" → mode `refund_credit`
3. **Check:** paid, reduction and remaining payable shown separately in Open items · credit listed
   until used → `finance_credits` side supplier

### Supplier credit notes and returns to the supplier

Goods go back, or the supplier corrects a price. Three facts: goods left, a credit exists, the
credit is used.

1. **Send back:** "12 damaged LAMP-01 went back to Nordlicht against PO-0210, DHL tracking
   00340434161094000002." → `shipment_dispatch_propose` `purpose="supplier_return"` with a
   `supplier_return` Movement. Approve; the Package carries the tracking number and the return now
   waits for its credit → `shipment_explain` · `supplier_return_not_credited`
2. **Record the credit:** "Record Nordlicht's credit note GS-N-118, 360.00, for the 12 returned
   lamps." → line names the PO line → `document_create_propose`
   `document_type="supplier_credit_note"` · booking → `supplier_credit_note_post_propose`. Approve
   both.
3. **Use it:** "Net GS-N-118 against ER-4471" → `supplier_credit_note_allocate_propose` · money
   back: "Nordlicht refunded 360.00, NL-2211" → `supplier_refund_post_propose`
4. **Check:** return, unposted and unclaimed entries gone → `supplier_credit_unposted`,
   `supplier_credit_unclaimed` · netting or refund in Open items. A credit note moves no goods; a
   return creates no credit.

### Watch the supply side

The daily glance at purchasing.

1. **Ask:** "How does the supply side look?" → uncovered demand, late suppliers, receipts without
   invoice, invoices to book, payables due, discounts → `item_supply_demand`, `commitments_list`,
   `exceptions_list`, `payment_run_preview` · per supplier: owed, overdue, credit →
   `finance_party_balances` side supplier
2. **Order:** late suppliers with blocked customer orders first, then invoices to book, then the
   payment run.
3. **Evening:** same question; the agent reports what changed.

## How an agent should phrase results

- "Item `itm_…`: 3 available, 12 open customer demand, 0 incoming; 2 orders blocked" is a read.
- "Prepared purchase order `PO-…` for 20 units at the list price; decision `prp_…` pending" is a
  proposal.
- "Approved; `commitments_list` shows the supplier promise for 20 due 18 Sept" is verified.
- Never say "ordered" or "paid" for a proposal that has not been approved.

## Not possible yet

- No order proposal or reorder point: Reality shows uncovered demand, the agent applies your rules
  and states the quantity.
- No supplier catalogue, price negotiation or sending of the purchase order; the order is evidence
  of what you ordered, the message to the supplier leaves through your own channel.
- No payable hold: a supplier invoice cannot be blocked from the payment run other than by leaving
  it out of the selected payments (spec 148 describes the hold; it is not built).
- No bank transfer: the payment run records what was decided; the money moves outside.
- No supplier-side automatic matching of incoming bank lines; supplier payments are recorded by
  proposal.
