# Playbook: Returns

From a customer saying "I am sending it back" to the goods on a shelf and the money settled. A
return in Reality is not a workflow with a status: it is a few records that name each other, and
four exception classes that report what is still missing between them. The announcement, the return
movement, what happens to the goods, the credit note and the refund are all orchestrated from
outside and decided by a person.

Each situation is one line of context and a few numbered steps: what you pull up, what you say, what
the agent prepares, what you decide, what you check. The tool behind a step stands at the end of its
line after an arrow.

Read [Run a business on Reality with agents](./) first for the loop and the rules.

## What Reality holds and derives

- A customer order line has an outgoing Commitment, the delivery promise. A shipment Movement
  fulfils it. A return Movement of type `return` names the same Commitment and reverses part of that
  delivery; it can never exceed what was shipped.
- Customer returns arrive as inbound Shipments/Packages; supplier returns leave as outbound ones.
  Packages may carry carrier and tracking numbers. Carrier events are append-only observations and
  never replace the return or supplier-return Movement that changes stock.
- A return announcement (spec 099) is the customer's statement that goods are coming back: the
  delivery it belongs to, the quantity, an optional reference such as the customer's return number,
  a reason and a date. It is not supply: nothing about availability or the fulfilment queue changes
  until the goods are recorded.
- What happens to returned goods is not a status either. The Movement that settles the return, a
  transfer back to stock, an outward adjustment for a write-off, a return to the supplier, says
  which return it resolves (`resolves_movement_id`, spec 082). A return nothing resolves is stock
  the company owns and cannot sell.
- A credit note is a Document whose lines say which order line they credit. Recording and booking
  are two steps; only a booked credit note is a receivable reduction, and how it is settled, netted
  against an invoice or refunded, is a third step. A restocking fee is a charge line on the same
  credit note, not a smaller credit (spec 095).
- `return_announcements(commitment_id?, status?)` lists announcements with what each still waits
  for. `order_explain(order_reference)` shows the order's lines and promises, its movements,
  shipments and returns alike, and the document lines that bill or credit its lines.
  `inventory_read(view="location")` shows where returned goods sit; `finance_balances` and Open
  items in the App show what a booked credit note did to the receivable.

Exceptions that belong to this area: `announced_return_not_arrived`, `return_unresolved`,
`returned_not_credited`, `credited_not_returned`, `credit_note_unposted`, `credit_note_unsettled`.

The examples continue with Müller GmbH, order SO-1042, 5 desk lamps LAMP-01 shipped and invoiced on
RE-2026-0917 at 48.00 each.

## Situations

### A customer announces a return

Müller writes: two lamps are the wrong colour, they are coming back. Nothing has arrived; the
announcement is not stock.

1. **Find:** "Müller wants to return 2 lamps from SO-1042." → the delivery promise → `order_explain`
2. **Terms, outside Reality:** full credit, fee or exchange; label and reply through your own
   channel.
3. **Say:** "Record the announcement: 2 lamps, RMA-M-31, wrong colour, expected by the 20th."
4. **Agent:** announcement against the delivery, bounded by what shipped → `return_announce_propose`
5. **You:** approve.
6. **Check:** listed open → `return_announcements` `status="open"` · availability unchanged ·
   nothing by the 20th → `announced_return_not_arrived` · customer changed their mind →
   `return_announcement_withdraw_propose`

### The goods arrive

The parcel is at the door, RMA-M-31 on the label. Inspection shelf first; where it ends up is the
next decision.

1. **Match:** "A return from Müller arrived, RMA-M-31, 2 lamps." → open announcement and its
   delivery → `return_announcements`
2. **Say:** "Record 2 lamps returned to the inspection location."
3. **Agent:** inbound Package from Müller, with carrier/tracking when stated, and a return Movement
   of 2 to inspection naming delivery and announcement; naming the announcement fulfils it →
   `shipment_receive_propose` `purpose="customer_return"`, Movement `type="return"`,
   `commitment_id`, `return_announcement_id`
4. **You:** approve the count, whatever the condition.
5. **Check:** Package, tracking and return contents → `shipment_explain` · 2 returned →
   `order_explain` · announcement fulfilled · lamps at inspection, `available` unchanged →
   `inventory_read` `view="location"` · tonight: waiting for its credit → `returned_not_credited`

A parcel nobody can trace to a delivery is not a return; find the order first.

### Decide what happens to the goods

Two lamps on the shelf: one fine, one scratched. Each outcome is its own movement naming the return.

1. **See:** "Which returns are still on the inspection shelf?" → `inventory_read` at inspection ·
   older ones → `return_unresolved`
2. **Say:** "One back to the main warehouse, the other written off as damaged."
3. **Agent:** transfer of 1 to the main warehouse → `movement_type="transfer"` · adjustment of 1
   out, reason "damaged base" → `movement_type="adjustment"` · both with `resolves_movement_id` ·
   back to the supplier would be `supplier_return`
4. **You:** approve both. Valuation is your accounting's job.
5. **Check:** `available` +1 → `item_supply_demand` · inspection empty · no longer unresolved →
   `exceptions_list`

`return_unresolved` uses a threshold learned from your own resolved returns; nothing shows until you
have some.

### Credit the customer

Two came back, RE-0917 billed five. 96.00 owed. Credit note, booking, settlement: three steps.

1. **List:** "Which returns are not credited?" → SO-1042, 2 returned, 5 billed, 0 credited →
   `exceptions_list` · `returned_not_credited`
2. **Say:** "Credit Müller the two returned lamps on RE-0917."
3. **Agent:** GS-0041, 96.00, line names the invoice line for 2 at the invoice's price →
   `sales_credit_record_propose` `invoice_id`, `lines`
4. **You:** approve the note, then the booking → `credit_note_post_propose`
5. **Check:** exception gone · `credit_note_unposted` gone · GS-0041 96.00 available →
   `finance_credits`

_Credited and not returned_ (`credited_not_returned`) is correct for a price correction without
goods; check it when goods were expected.

### Keep a restocking fee

Terms keep 10 % on returns without a defect: 86.40, not 96.00. Crediting fewer units leaves the
return uncredited for ever; credit the goods in full and charge the fee.

1. **Say:** "Credit the two lamps in full and charge a restocking fee of 9.60."
2. **Agent:** credit note with a goods line 2 × 48.00 naming the order line
   (`billed_document_line_id`) and a charge line "Restocking fee" −9.60 (`line_type="charge"`),
   total 86.40 → `document_create_propose` `document_type="credit_note"` · booking →
   `credit_note_post_propose`
3. **You:** approve note and booking; fee and reason are stated, not derived.
4. **Check:** total 86.40 · `returned_not_credited` gone, the goods line credits both · the charge
   line names no order line and counts as no credit.

### Net or refund

GS-0041 is booked with 96.00 available. Either RE-0917 is still open, or it was paid and the
customer wants the money.

1. **See:** "Which credit notes are unsettled?" → GS-0041 96.00 available, RE-0917 open 240.00 →
   `exceptions_list` · `credit_note_unsettled` · `finance_credits`
2. **Say:** "Net it against RE-0917" → `credit_note_allocate_propose` · after your transfer:
   "Refunded Müller 96.00, RF-78" → `customer_refund_post_propose` · or leave it for the next
   invoice.
3. **You:** approve; a refund only after the money left.
4. **Check:** RE-0917 144.00 open, or the refund once in the journal → `finance_settlement_context`
   · gone from the credit list · unsettled entry gone

### Watch the return side

The weekly glance at everything that came back or is about to.

1. **Ask:** "Where do we stand with returns?" → announced not arrived, arrived not resolved,
   returned not credited, credited not settled, each with its age → `return_announcements`,
   `exceptions_list`
2. **Choose:** which get a proposal this week, which announcements to withdraw, which fees to waive.
3. **Next week:** the lists shrink; nothing older than your own threshold stays without a reason.

## How an agent should phrase results

- "Announcement `ann_…`: 2 of 3 announced units arrived 4 days after `expected_by`" is a read.
- "Prepared credit note `GS-…` for 10 units at 9.00 with a restocking fee of 18.00, total 72.00;
  decision `prp_…` pending" is a proposal.
- "Approved; `returned_not_credited` no longer lists order line `lin_…`" is verified.
- Never say "refunded" for a proposal that has not been approved, and never say "credited" for a
  credit note that is recorded but not booked.

## Not possible yet

- No return label, no RMA number of Reality's own, no message to the customer: the announcement
  stores the customer's reference; everything the customer receives leaves through your channel.
- No exchange as one action: an exchange is a return plus a new order line, recorded as two things.
- No valuation of returned or scrapped goods; movements carry quantities, your accounting carries
  the value.
- No automatic refund through a payment provider; the refund is recorded after the money moved.
