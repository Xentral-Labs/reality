# Operating rhythm: daily, weekly, monthly

What a trading business on Reality has to do, and how often. Only the concrete tasks; the playbooks
hold the detail. Each line names the signal that starts the task and, where a playbook already
describes it, links to the situation. Lines marked _example to follow_ have no worked example yet.

The rhythm assumes the two automatic inflows: orders arrive from the shop or Demo Data, payments
arrive from the bank, a provider or Demo Data. Everything below is what a person, a workflow or an
agent has to add.

## Every day

1. **Ship what is ready.** Read `fulfillment_queue`; reserve available stock, record the shipments
   the warehouse made, in full or in parts.
   [Fulfilment: what can ship, reserve, ship in full, ship in parts](./order-to-cash-fulfilment#situations)
2. **Receive what arrived.** Record every delivery as a receipt with the counted quantity; send back
   what is wrong. [Purchasing: receive goods](./purchasing-and-replenishment#receive-goods)
3. **Bill what shipped.** `exceptions_list` → `shipped_not_billed`, `sales_invoice_unposted`: record
   and post the invoices.
   [Receivables: bill what shipped](./receivables-and-payments#bill-what-shipped)
4. **Work the incoming money.** `exceptions_list` → `unmatched_financial_event`: propose allocations
   for payments with candidates; record payments that did not come through a source.
   [Receivables: a payment nobody can match](./receivables-and-payments#a-payment-nobody-can-match)
5. **Look at today's differences.** New short payments and overpayments: decide leave open, explain,
   accept a reduction, reuse or refund credit.
   [Receivables: short payment](./receivables-and-payments#short-payment),
   [overpayment](./receivables-and-payments#overpayment-and-using-the-excess-later)
6. **Read the exceptions once.** `exceptions_list`: promises at risk, stalled orders, reservations
   that no longer fit, interpretation failures, silent sources. Decide which need a proposal today.
   [Master data: a source went quiet](./master-data-and-sources#a-source-went-quiet),
   [something arrived and could not be understood](./master-data-and-sources#something-arrived-and-could-not-be-understood)
7. **Decide.** `proposals_awaiting_approval`: every open proposal gets a decision; nothing waits
   overnight without a reason. [Index: the loop](./#the-loop-every-playbook-follows)
8. **Verify and report.** Read what changed today (`order_explain`, `finance_balances`) and report
   the read, not the intention.

## Every week

1. **Replenish.** `item_supply_demand`: uncovered demand, projected stock, late supplier promises;
   place the purchase orders.
   [Purchasing: find what to buy](./purchasing-and-replenishment#find-what-to-buy),
   [place a purchase order](./purchasing-and-replenishment#place-a-purchase-order)
2. **Pay suppliers.** `payment_run_preview(pay_by = end of next week)`: take the discounts worth
   taking, pay what is due, confirm the total.
   [Purchasing: pay suppliers with a payment run](./purchasing-and-replenishment#pay-suppliers-with-a-payment-run)
3. **Clear the three-way check.** `billed_not_received`, `receipt_unbilled`,
   `invoice_price_differs`, `duplicate_supplier_invoice`: settle each with the buyer, then book or
   send back. [Purchasing: the three-way check](./purchasing-and-replenishment#the-three-way-check)
4. **Review overdue receivables.** `overdue_receivable`, `credit_limit_exceeded`: remind the
   customer outside Reality, place a delivery hold where the risk is real, accept or refuse the
   reductions collected during the week.
   [Fulfilment: hold an order or a customer](./order-to-cash-fulfilment#hold-an-order-or-a-customer)
5. **Close what will not ship.** `stale_closure_preview` for promises an import left behind; release
   reservations and holds that no longer have a reason.
   [Fulfilment: close promises that will never ship](./order-to-cash-fulfilment#close-promises-that-will-never-ship)
6. **Handle returns.** `return_announcements` open, `announced_return_not_arrived`,
   `returned_not_credited`, `credited_not_returned`: record the return movement, the credit note,
   the refund. [Returns: the goods arrive](./returns#the-goods-arrive),
   [credit the customer](./returns#credit-the-customer), [net or refund](./returns#net-or-refund)
7. **Tidy the data that blocks.** `units_not_comparable`, price list gaps, missing payment terms,
   new customers or items the sources introduced.
   [Master data: state how units relate](./master-data-and-sources#state-how-units-relate),
   [create what a source needs](./master-data-and-sources#create-what-a-source-needs)

## Every month

1. **Prepare the finance handoff.** No unposted invoices or credit notes, no unexplained unallocated
   payments, open items and available credit reviewed; export the journal to the accounting target.
   _Example to follow (finance handoff, spec 148 targets and mappings)._
2. **Review the aging.** Receivables and payables by age; decide reductions, refunds and holds for
   what stays open; review credit limits.
   [Receivables: watch the money](./receivables-and-payments#watch-the-money),
   [Purchasing: watch the supply side](./purchasing-and-replenishment#watch-the-supply-side)
3. **Count and correct stock.** Physical count against `inventory_read`; adjustments as movements
   with a reason; expired lots (`expired_lots`, `stock_expired`) removed or re-dated. _Example to
   follow._
4. **Review the agent's authority.** Decision history: which proposal classes were approved
   automatically, which were rejected and why; adjust the delegated classes. _Example to follow._
5. **Check the sources.** `interpretation_coverage`: what each source delivered, what failed, what
   needs review; source updates that require a decision.
   [Master data: review what the sources delivered](./master-data-and-sources#review-what-the-sources-delivered)
6. **Refresh terms and prices.** Payment terms, price lists and tiers, supplier agreements that
   changed during the month.
   [Master data: prices](./master-data-and-sources#prices-lists-tiers-and-who-gets-which),
   [payment terms](./master-data-and-sources#payment-terms)

## How the rhythm relates to the playbooks

The daily list is the [daily minimum](./#the-daily-minimum) of the index in working order. Weekly
and monthly tasks are the same loop applied to slower signals: supply, payables, aging, stock,
sources. Nothing in the rhythm is done by Reality itself; every line is a read followed by proposals
and decisions.
