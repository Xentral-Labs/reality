# Playbook: Sales and fulfilment

From an incoming order to a shipped promise. Reality records the order and derives one delivery
promise (a Commitment) per line. Reserving, shipping, changing the promise, holding it and closing
what will never ship are orchestrated from outside.

Each situation is one line of context and a few numbered steps: what you pull up, what you say, what
the agent prepares, what you decide, what you check. The tool behind a step stands at the end of its
line after an arrow.

Read [Run a business on Reality with agents](./) first for the loop and the rules.

## What Reality holds and derives

- An order is a Document with DocumentLines; each line has an outgoing Commitment with quantity and
  due date. Nothing on the document says "shipped"; that is derived.
- A Reservation allocates available stock to a Commitment. A Shipment is the physical consignment;
  its Package carries the carrier and tracking number. Only the Package's shipment Movements fulfil
  Commitments and reduce stock. Open quantity is what was promised minus what physically moved, at
  read time.
- A shipment notice records what a company, counterparty, carrier or integration says is coming. It
  does not move stock. Tracking events are append-only observations: `delivered` is not silently
  treated as warehouse dispatch, receipt or Commitment fulfilment.
- `fulfillment_queue` is the work list: per order `order_key`, `party`, `due_at`, `priority`,
  `ship_ready`, `blocking_reasons` and the lines. `fulfillment_blockers` lists the reasons with
  `blocker_type`, `commitment_id`, `item_id`, `shortage_quantity`. `item_supply_demand` shows per
  item `physical`, `reserved`, `available`, `incoming`, `open_customer_demand`, `uncovered_demand`,
  `projected` and `blocked_order_count`.
- `order_explain(order_reference)` traces one order from the source record through the document, the
  promises, reservations and movements to the derived state. Use it before and after every change to
  an order.

Exceptions that belong to this area: `outgoing_commitment_at_risk`,
`overdue_outgoing_customer_commitment`, `order_stalled`, `reservation_exceeds_stock`,
`commitment_hold_unreleased`, `party_hold_unreleased`, `stock_expired`, and, once goods left,
`shipped_not_billed` (handled in the receivables playbook).

The examples use one customer, Müller GmbH, one item, the desk lamp LAMP-01, and small quantities.

## Situations

### What can ship today

The morning list for the warehouse: stock present, nothing in the way. Reality keeps it current.

1. **List:** "What can ship today?" → `fulfillment_queue`, `ship_ready` true, no `blocking_reasons`
   · App: Work SO-1042 Müller due today, 5 lamps reserved, ready · SO-1045 due tomorrow, ready ·
   SO-1044 not ready, 3 short
2. **Doubt one:** "Show me SO-1042." → promised 5, reserved 5, shipped 0 → `order_explain`
3. **You:** tell the warehouse what to pick. The queue is a list, not an instruction; nothing
   changed yet.
4. **Check:** shipped orders leave the queue (next situations).

### Reserve stock for a promise

An order that could ship but has no stock set aside, or one listed as short while the item shows
available stock.

1. **See:** "Why is SO-1044 not ready?" → shortage 3 → `fulfillment_blockers` · LAMP-01 physical 20,
   reserved 17, available 3, incoming 50 next week → `item_supply_demand`
2. **Say:** "Reserve the three available lamps for SO-1044." Another order with a better claim:
   reserve for that one; the agent will not choose.
3. **Agent:** reservation of 3 for the promise on SO-1044; without a quantity it takes the whole
   open quantity → `reservation_propose`
4. **You:** approve. More than available is refused.
5. **Check:** SO-1044 3 reserved → `order_explain` · item reserved 20, available 0. A later stock
   correction that makes a reservation too large shows up → `exceptions_list` ·
   `reservation_exceeds_stock`; release with `reservation_release_propose`.

### Ship in full

The warehouse reports the goods left. Reality knows nothing until somebody says so.

1. **Say:** "SO-1042 shipped complete this morning, 5 lamps from the main warehouse."
2. **Agent:** one outgoing Package for Müller, carrier and tracking number when known, plus the
   exact shipment Movement for quantity 5, location, promise and time; lot or serial when inventory
   is tracked → `shipment_dispatch_propose` `purpose="customer_delivery"`
3. **You:** approve what physically happened; four left, say four.
4. **Check:** Package, tracking number and Movement contents → `shipment_explain` · shipped 5, open
   0 → `order_explain` · left the queue · tonight on the billing list → `shipped_not_billed`,
   [Receivables](./receivables-and-payments#bill-what-shipped)

### Ship in parts

3 of 5 lamps left; the rest is short. The promise stays whole, the remainder stays open.

1. **Say:** "SO-1043 shipped 3 of 5 today."
2. **Agent:** outgoing Package with a shipment Movement of 3; the promise is untouched, 2 remain
   open → `shipment_dispatch_propose` `purpose="customer_delivery"`, Movement `quantity=3`
3. **You:** approve. Whether 2 ship later or the customer takes 3 is the next situation.
4. **Check:** shipped 3, open 2 → `order_explain` · queue keeps SO-1043 with the rest. Report the
   last 2 the same way.

### Record a notice and follow the carrier

The carrier reference exists before the warehouse reports dispatch, or the carrier later reports a
scan. Keep those statements separate from physical stock.

1. **Notice:** "DHL announced package 00340434161094000001 for Müller." →
   `shipment_notice_record_propose` `direction="outbound"`, `purpose="customer_delivery"`, carrier
   and tracking number. Approve; `shipment_explain` shows an announced Package and no Movement.
2. **Dispatch:** when the warehouse reports that the goods left, record the Package and exact
   Movements with `shipment_dispatch_propose`. A notice is not a shortcut for dispatch.
3. **Track:** "DHL reports that package `pkg_…` was delivered at 14:10." →
   `shipment_event_record_propose` `event_type="delivered"`, `reporter_type="carrier"`, exact
   `occurred_at` and optional source. Approve only the stated observation.
4. **Correct:** append the replacement observation, then supersede the wrong event with a reason →
   `shipment_event_record_propose`, `shipment_event_supersede_propose`. The original remains in
   history.
5. **Find and explain:** search carrier, tracking number or Shipment ID → `shipments_list`; inspect
   Packages, current/history events, Movements, evidence and discrepancies → `shipment_explain`.

### The customer accepts less or later

The remaining 2 cannot be covered soon; the customer agreed to 3 only, or to wait until the 25th.

1. **See:** promise at risk, no incoming before due → `exceptions_list` ·
   `outgoing_commitment_at_risk` · `item_supply_demand`
2. **Agree outside Reality:** call Müller; they accept 3.
3. **Say:** "Müller accepts 3 on SO-1043, agreed by phone with Ms Weber today."
4. **Agent:** revision to 3 with who and when; `due_at` instead when the date moves; never below
   what shipped → `commitment_revise_propose`
5. **You:** approve only with the agreement in hand.
6. **Check:** promised 3, shipped 3, open 0, revision in history → `order_explain` · risk entry
   gone. The other 2 later as their own delivery: a new order → `order_create_propose`. No "split
   into two deliveries" command.

### Hold an order or a customer

"Do not ship this yet": credit limit, undeliverable address, compliance. A hold blocks shipment;
orders and reservations stay.

1. **See:** Müller over the credit limit → `exceptions_list` · `credit_limit_exceeded`; or a
   colleague reports a wrong address.
2. **Say:** "Hold SO-1045 until the address is clarified." · "Delivery hold on Müller GmbH, credit
   check."
3. **Agent:** hold on the promise → `commitment_hold_propose`, `reason_code` in `credit_check`,
   `customer_request`, `address_clarification`, `compliance`, `manual_review`, `other` · or on the
   customer → `party_delivery_hold_propose`
4. **You:** approve.
5. **Check:** hold under the order's blocking reasons → `fulfillment_queue` · visible until lifted →
   `commitment_hold_unreleased`, `party_hold_unreleased`. Lift: "Release the hold on SO-1045" →
   `commitment_hold_release_propose`, `party_delivery_hold_release_propose`

### Close promises that will never ship

An import left hundreds of delivered-long-ago promises open. A person closes them in bulk, with a
reason.

1. **Preview:** "How many sales promises due before 1 July are still open?" → 212, with a sample of
   ten → `stale_closure_preview` `direction="sales"`, `due_before`
2. **Sample:** a real open order among them? Ship or revise it first; the closure takes everything
   counted.
3. **Say:** "Close them, reason: migrated from the old system, delivered before go-live."
4. **Agent:** bulk closure with exactly the previewed count; a changed count is refused →
   `stale_closure_propose` `expected_count=212`
5. **You:** approve.
6. **Check:** no longer open → `commitments_list` · each order shows the closure and reason →
   `order_explain`

### Explain an order to a customer or colleague

"Can my order ship today?" "Why is SO-1044 late?" A read; nothing is decided.

1. **Find:** "Find Müller's order from 8 September." → SO-1044 → `business_records_discover`
   `family="document"`
2. **Trace:** 5 promised, 3 reserved, 0 shipped, short 2, 50 incoming on the 18th → `order_explain`
   · why an exception is reported → `exception_explain`
3. **Answer:** "Three today, two after the 18th." Name records and quantities; say what it does not
   prove: the supplier's date is the supplier's promise.

## How an agent should phrase results

- "Promise `cmt_…` for 6 units: 4 shipped on 10 Sept, 2 open, 2 reserved" is a read.
- "Prepared shipment of 2 units against `cmt_…`; awaiting decision `prp_…`" is a proposal.
- "Approved `prp_…`; `order_explain` now shows 6 shipped, 0 open" is a verified result.
- Never say "shipped" for a proposal that has not been approved.

## Not possible yet

- No pick lists, carrier booking, label creation or live carrier polling; Reality records stated
  carrier/tracking observations and what physically moved.
- No automatic reservation on order arrival and no automatic release on hold; both are proposals.
- No split of one promise into two dated promises; use partial shipments or a revision plus a new
  order.
- No backorder or replenishment suggestion; `item_supply_demand` shows uncovered demand, the agent
  proposes the purchase ([purchasing playbook](./purchasing-and-replenishment)).
