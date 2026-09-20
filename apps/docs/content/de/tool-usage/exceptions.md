# Operative Ausnahmen

Deterministisch abgeleitete Zustände, die Aufmerksamkeit brauchen. Jede nennt, wer sie verantwortet,
was sie auflöst und welche Agenten-Tools sie auflisten und erklären.

> Automatisch aus `operational_exception_catalog.yaml` erzeugt. Diese Seite nicht von Hand
> bearbeiten.

| Schlüssel                                                                                 | Bezeichnung                              | Bereich                 | Schwere  | Verantwortlich                                                                              |
| ----------------------------------------------------------------------------------------- | ---------------------------------------- | ----------------------- | -------- | ------------------------------------------------------------------------------------------- |
| [`overdue_outgoing_customer_commitment`](#exception-overdue_outgoing_customer_commitment) | Overdue outgoing customer commitment     | Aufträge & Erfüllung    | `high`   | Order fulfilment or warehouse operations                                                    |
| [`outgoing_commitment_at_risk`](#exception-outgoing_commitment_at_risk)                   | Customer commitment at risk              | Aufträge & Erfüllung    | `high`   | Order fulfilment or warehouse operations                                                    |
| [`order_stalled`](#exception-order_stalled)                                               | Order stalled                            | Aufträge & Erfüllung    | `high`   | Order fulfilment                                                                            |
| [`overdue_incoming_supplier_commitment`](#exception-overdue_incoming_supplier_commitment) | Overdue incoming supplier commitment     | Aufträge & Erfüllung    | `high`   | Purchasing or inbound operations                                                            |
| [`shipped_not_billed`](#exception-shipped_not_billed)                                     | Shipped and not billed                   | Finanzen                | `high`   | Billing, with order fulfilment when the delivery is in doubt                                |
| [`billed_not_received`](#exception-billed_not_received)                                   | Billed and not received                  | Finanzen                | `high`   | Accounts payable, with purchasing when the goods are missing                                |
| [`invoice_price_differs`](#exception-invoice_price_differs)                               | Invoice price differs from the agreement | Finanzen                | `high`   | Accounts payable for a supplier invoice, billing for a customer invoice                     |
| [`sold_below_purchase_price`](#exception-sold_below_purchase_price)                       | Sold below the purchase price            | Finanzen                | `high`   | Sales management, with purchasing when the purchase price is the stale figure               |
| [`returned_not_credited`](#exception-returned_not_credited)                               | Returned and not credited                | Finanzen                | `high`   | Customer service, with billing when the credit note is the missing step                     |
| [`credited_not_returned`](#exception-credited_not_returned)                               | Credited and not returned                | Finanzen                | `high`   | Customer service, with credit control when the money is already gone                        |
| [`supplier_return_not_credited`](#exception-supplier_return_not_credited)                 | Returned to supplier and not credited    | Finanzen                | `high`   | Purchasing, with accounts payable when the money has already gone                           |
| [`supplier_credit_not_returned`](#exception-supplier_credit_not_returned)                 | Supplier credited more than went back    | Finanzen                | `high`   | Purchasing, with accounts payable at period end                                             |
| [`return_unresolved`](#exception-return_unresolved)                                       | Return not dealt with                    | Aufträge & Erfüllung    | `normal` | Warehouse control, with customer service when the decision is theirs                        |
| [`receipt_unbilled`](#exception-receipt_unbilled)                                         | Receipt not invoiced                     | Finanzen                | `high`   | Purchasing, with accounts payable at period end                                             |
| [`units_not_comparable`](#exception-units_not_comparable)                                 | Units not comparable                     | Bereichsübergreifend    | `normal` | Whoever maintains item master data, with purchasing                                         |
| [`reservation_exceeds_stock`](#exception-reservation_exceeds_stock)                       | Reservation exceeds stock                | Aufträge & Erfüllung    | `high`   | Warehouse control, with purchasing when stock has to be replaced                            |
| [`silent_source`](#exception-silent_source)                                               | Silent source                            | Belege, Quellen & Facts | `high`   | Integration operations, with the owner of the source system                                 |
| [`source_interpretation_failure`](#exception-source_interpretation_failure)               | Source interpretation failure            | Belege, Quellen & Facts | `high`   | Integration operations, with the owner of the source system                                 |
| [`unexplained_movement`](#exception-unexplained_movement)                                 | Unexplained movement                     | Lager & Logistik        | `normal` | Warehouse control                                                                           |
| [`sales_invoice_unposted`](#exception-sales_invoice_unposted)                             | Sales invoice not booked                 | Finanzen                | `high`   | Billing, with accounts receivable at period end                                             |
| [`supplier_invoice_unposted`](#exception-supplier_invoice_unposted)                       | Supplier invoice not booked              | Finanzen                | `high`   | Accounts payable                                                                            |
| [`credit_note_unposted`](#exception-credit_note_unposted)                                 | Credit note not booked                   | Finanzen                | `high`   | Accounts receivable                                                                         |
| [`credit_note_unsettled`](#exception-credit_note_unsettled)                               | Credit note not given back               | Finanzen                | `high`   | Accounts receivable, with treasury when the money has to leave                              |
| [`supplier_credit_unposted`](#exception-supplier_credit_unposted)                         | Supplier credit not booked               | Finanzen                | `high`   | Accounts payable                                                                            |
| [`supplier_credit_unclaimed`](#exception-supplier_credit_unclaimed)                       | Supplier credit not claimed              | Finanzen                | `high`   | Accounts payable, with purchasing when the supplier has to be chased                        |
| [`overdue_receivable`](#exception-overdue_receivable)                                     | Overdue receivable                       | Finanzen                | `high`   | Accounts receivable                                                                         |
| [`credit_limit_exceeded`](#exception-credit_limit_exceeded)                               | Credit limit exceeded                    | Finanzen                | `high`   | Credit control, with sales when the limit itself is the question                            |
| [`overdue_payable`](#exception-overdue_payable)                                           | Overdue payable                          | Finanzen                | `high`   | Accounts payable                                                                            |
| [`purchase_discount_available`](#exception-purchase_discount_available)                   | Early payment discount still available   | Finanzen                | `normal` | Accounts payable, with whoever schedules the payment run                                    |
| [`duplicate_supplier_invoice`](#exception-duplicate_supplier_invoice)                     | Duplicate supplier invoice               | Finanzen                | `high`   | Accounts payable                                                                            |
| [`unmatched_financial_event`](#exception-unmatched_financial_event)                       | Unmatched financial event                | Finanzen                | `high`   | Accounts receivable or accounts payable                                                     |
| [`announced_return_not_arrived`](#exception-announced_return_not_arrived)                 | Announced return has not arrived         | Aufträge & Erfüllung    | `normal` | Customer service, with the receiving desk once the parcel is expected                       |
| [`commitment_hold_unreleased`](#exception-commitment_hold_unreleased)                     | Promise hold not lifted                  | Aufträge & Erfüllung    | `normal` | Whoever raised the hold, named in the entry, with the reason code saying which team that is |
| [`party_hold_unreleased`](#exception-party_hold_unreleased)                               | Party hold not lifted                    | Aufträge & Erfüllung    | `high`   | Whoever raised the hold, named in the entry, with the reason code saying which team that is |
| [`stock_expired`](#exception-stock_expired)                                               | Expired stock on hand                    | Lager & Logistik        | `high`   | Warehouse control, with quality assurance where the goods are regulated                     |
| [`missing_acquisition_cost`](#exception-missing_acquisition_cost)                         | Missing acquisition cost                 | Bereichsübergreifend    | `high`   | Purchasing or inventory control                                                             |
| [`unassigned_cost_component`](#exception-unassigned_cost_component)                       | Unassigned cost component                | Finanzen                | `high`   | Purchasing or finance operations                                                            |
| [`stale_cost_review`](#exception-stale_cost_review)                                       | Stale cost review                        | Aufträge & Erfüllung    | `normal` | Finance operations                                                                          |
| [`negative_actual_db1`](#exception-negative_actual_db1)                                   | Negative actual DB1                      | Bereichsübergreifend    | `normal` | Sales management                                                                            |

## `overdue_outgoing_customer_commitment` — Overdue outgoing customer commitment {#exception-overdue_outgoing_customer_commitment}

A delivery promised to a customer is past its date and part of the quantity has still not shipped.
Reality takes every open customer-delivery commitment that carries a promised date, subtracts what
has already shipped against it, and compares the date with the moment the queue is read. The entry
appears when the date has passed and quantity remains; a promise due today is not yet late, and a
commitment with no date never appears at all. Until the date falls, the same order is reported as
Customer commitment at risk instead — and only if its reservation is short. Here the elapsed time is
what counts: an order fully reserved but never dispatched is overdue without ever having been at
risk. If the remainder is also unreserved, that shortfall rides along as a cause instead of
producing a second row, so one order is never listed twice. This is a promise your company made; the
mirror image, a supplier late towards you, is Overdue incoming supplier commitment. It also assumes
a date was agreed at all: an order nobody dated, standing far longer than this company normally
takes, is Order stalled, and no order is ever in both — and stating a date for an undated order
moves it from that class to this one. The date it is judged against is the last one anybody stated:
where the company has agreed a later day with the customer, that day is the promise now, and the
entry appears only once it too has passed. When that happens the entry carries the reason that the
promise was revised and names the day it was originally due, so a re-agreed date cannot buy silence.
What it cannot tell you is that a date has been moved repeatedly and always met, because a promise
kept is a promise kept.

- **Verantwortlich:** Order fulfilment or warehouse operations
- **Aufgelöst durch:** Shipping the outstanding quantity, or cancelling the commitment.
- **Schwere:** `high`
- **Datensatztyp:** `commitment`
- **Spezifikation:** `068/FR-001`
- **Nachweis:**
  `tests/operational_exceptions/test_derivation.py::test_overdue_outgoing_customer_commitment`

**Ursachen**

| ID                         | Bezeichnung              | Spezifikation |
| -------------------------- | ------------------------ | ------------- |
| `insufficient_reservation` | Insufficient reservation | `068/FR-003`  |
| `promise_was_revised`      | Promise was revised      | `093/FR-006`  |

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`commitments`](./views#view-commitments)

## `outgoing_commitment_at_risk` — Customer commitment at risk {#exception-outgoing_commitment_at_risk}

A customer delivery that is not yet late has quantity nothing is holding for it. Reality subtracts
the shipped quantity from the promised one and compares the remainder against the reservations still
active on that commitment; the entry appears while the reservations cover less than the remainder.
It is a warning about cover, not about time — once the promised date passes, the same order is
reported as Overdue outgoing customer commitment instead, whether or not it is reserved. It also
says nothing about whether the reserved goods still physically exist: a reservation can cover the
remainder on paper while the stock behind it has gone, and that is Reservation exceeds stock.

- **Verantwortlich:** Order fulfilment or warehouse operations
- **Aufgelöst durch:** Reserving the remaining quantity, shipping it, or cancelling the commitment.
- **Schwere:** `high`
- **Datensatztyp:** `commitment`
- **Spezifikation:** `020/FR-004`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_outgoing_commitment_at_risk`

**Ursachen**

| ID                         | Bezeichnung              | Spezifikation |
| -------------------------- | ------------------------ | ------------- |
| `insufficient_reservation` | Insufficient reservation | `020/FR-004`  |

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`commitments`](./views#view-commitments)

## `order_stalled` — Order stalled {#exception-order_stalled}

A customer order nobody agreed a date for has been standing far longer than this company normally
takes. Reality never asks how fast an order should ship; it measures how long this tenant's own
finished orders took, from the moment the promise was made to the last shipment against it, and
takes the middle of the most recent twenty. An order is reported once it has stood past three times
that, and never sooner than a week however fast the company is. Only orders that finished teach the
norm, so a backlog cannot raise the bar that measures the backlog, and a cancelled order teaches
nothing because it was never going to ship. Nothing at all is reported for a company with fewer than
five finished orders: a norm claimed from three is a guess. This is the condition that catches what
no other class can — a consumer order arrives with no requested date, is reserved in full, and then
simply sits, which every date-anchored class is blind to. Because the norm is the company's own, it
moves: a business that gets slower raises its own bar, and an entry can clear because the company
changed rather than because anything shipped. An order that does carry a date and has passed it is
Overdue outgoing customer commitment, and the two never both report the same order.

- **Verantwortlich:** Order fulfilment
- **Aufgelöst durch:** Shipping the outstanding quantity, cancelling the order, or agreeing a date
  with the customer.
- **Schwere:** `high`
- **Datensatztyp:** `commitment`
- **Spezifikation:** `080/FR-005`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_order_stalled`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`commitments`](./views#view-commitments)

## `overdue_incoming_supplier_commitment` — Overdue incoming supplier commitment {#exception-overdue_incoming_supplier_commitment}

A supplier has not delivered what it promised by the date it promised. Reality takes every open
supplier-delivery commitment with a due date, subtracts what has been received against it, and
compares the date with the moment the queue is read. The entry appears when the date has passed and
quantity is still outstanding. Its practical weight is downstream: goods that were counted on for
your own customer promises are not in the building. This is a promise made to your company; the
mirror image, your company late towards a customer, is Overdue outgoing customer commitment. It
concerns goods, not money: the same supplier waiting to be paid is Overdue payable. It also concerns
goods nobody has billed yet: a supplier that has already invoiced goods which have not arrived is
Billed and not received. The date it judges against is the last one the supplier stated: a supplier
that acknowledged a later day is not late until that day passes, and when it does the entry says the
promise was moved and names the day it was originally due. A supplier that keeps moving the date and
always beats the revised one is never reported here, because it is meeting the promises it actually
made.

- **Verantwortlich:** Purchasing or inbound operations
- **Aufgelöst durch:** Receiving the outstanding quantity, or cancelling the commitment.
- **Schwere:** `high`
- **Datensatztyp:** `commitment`
- **Spezifikation:** `020/FR-005`
- **Nachweis:**
  `tests/operational_exceptions/test_derivation.py::test_overdue_incoming_supplier_commitment`

**Ursachen**

| ID                    | Bezeichnung         | Spezifikation |
| --------------------- | ------------------- | ------------- |
| `promise_was_revised` | Promise was revised | `093/FR-006`  |

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`commitments`](./views#view-commitments)

## `shipped_not_billed` — Shipped and not billed {#exception-shipped_not_billed}

Goods left the building against a customer order line and no invoice line bills them. Reality takes
the quantity actually shipped against that line's promise, subtracts everything invoice lines have
billed against the same line, and reports what is left over. Every invoice line pointing at the
order line counts, so billing an order across two invoices, or in instalments, behaves without
special handling. Only lines that promised a delivery are considered — freight, a discount or a
service promises no goods, so it is never asked to have been shipped. A line with nothing shipped
says nothing at all, whatever has been billed: invoicing ahead of the goods is a prepayment, not a
finding. This is revenue the company has already earned and not asked for — which is what separates
it from Overdue receivable, where the invoice exists and the customer is late paying it. The same
comparison on the buying side, where an invoice runs ahead of the goods, is Billed and not received;
the third thing that can be wrong about one pair of lines is the price, which is Invoice price
differs from the agreement. Quantities are compared across the item's own stated units where it says
how they relate, and a pair that still cannot be reconciled is reported as Units not comparable
rather than skipped in silence. Goods that have come back are not counted here at all, and a return
nobody has credited is the second half of the same line's life: Returned and not credited.

- **Verantwortlich:** Billing, with order fulfilment when the delivery is in doubt
- **Aufgelöst durch:** Billing the outstanding quantity on an invoice line that names the order
  line.
- **Schwere:** `high`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `076/FR-004`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_shipped_not_billed`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `billed_not_received` — Billed and not received {#exception-billed_not_received}

A supplier has invoiced more of a purchase order line than has arrived. Reality sums what every
invoice line bills against that order line, subtracts what has been received against its promise,
and reports the excess. It is the mirror of Shipped and not billed on the other side of the
business, and only two of the four possible mismatches are worth reporting: goods received before
the supplier's invoice arrives is the usual sequence, so an unbilled receipt says nothing here. Only
lines that promised a delivery are considered, so a freight or service line is never reported for
failing to arrive. What is at stake is money leaving for goods the company does not have, and the
opposite direction — goods that arrived and no supplier ever invoiced — is Receipt not invoiced. The
third thing that can be wrong about the same pair of lines is the price, which is Invoice price
differs from the agreement. The same shape on the selling side, where money has gone back before the
goods did, is Credited and not returned. Goods that arrived and were later sent back still count as
received here, on purpose: the supplier delivered them, and netting returns off would report it as
having failed to deliver something it delivered. What it owes for them is Returned to supplier and
not credited. Quantities are compared across the item's own stated units where it says how they
relate, and a pair that still cannot be reconciled is reported as Units not comparable rather than
skipped in silence. Two neighbours concern the same supplier without concerning the same thing:
goods promised and not yet delivered at all is Overdue incoming supplier commitment, an invoice past
its payment date is Overdue payable, and the same invoice recorded twice is Duplicate supplier
invoice.

- **Verantwortlich:** Accounts payable, with purchasing when the goods are missing
- **Aufgelöst durch:** Receiving the outstanding quantity, or correcting the invoice.
- **Schwere:** `high`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `076/FR-005`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_billed_not_received`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `invoice_price_differs` — Invoice price differs from the agreement {#exception-invoice_price_differs}

An invoice line bills a unit price other than the one agreed on the order line it names. Reality
compares the two figures as they were recorded and reports the difference; it recalculates neither,
because both were stated by somebody. The entry sits on the invoice line rather than the order line,
because that is where the unexpected figure is. It asks only whether the invoice matches what was
agreed; whether the agreement itself lost money is the other half, and that is Sold below the
purchase price. A line billing nothing from an order has nothing to differ from and is never
reported. A pair recorded in different units is left alone and never converted: a price per box
divided by twelve is money nobody agreed. That is a rule rather than a limitation, which is why this
decline alone is not reported as Units not comparable — no conversion anybody could state would make
it possible. This is about the price on one pair of lines. Whether the right quantity was billed at
all is the other question, and it is answered by Shipped and not billed on the selling side and
Billed and not received on the buying side.

- **Verantwortlich:** Accounts payable for a supplier invoice, billing for a customer invoice
- **Aufgelöst durch:** Correcting the invoice line, or agreeing the new price on the order line.
- **Schwere:** `high`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `076/FR-006`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_invoice_price_differs`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `sold_below_purchase_price` — Sold below the purchase price {#exception-sold_below_purchase_price}

A sales order line was agreed at less than the company itself says the item costs. Reality compares
two figures somebody wrote down — the price on the agreed line, and the entry on the standing
default purchase price list as it stood when the sale was agreed — and reports the shortfall. It
calculates neither and converts neither: a pair in a different currency or unit is left alone rather
than translated. This is not accounting margin. It carries no freight, no duty, no handling and no
valuation of stock, so a line agreed slightly above the purchase price may still lose money and will
not appear here; the class understates, which is the safer direction. It is also silent for a
company that keeps no purchase price list, because then nobody has said what the item costs and
inventing a figure is the one thing this deliberately does not do. A line agreed at nothing is
treated as a decision — a sample, a replacement, a goodwill gesture — and selling at exactly the
purchase price is a thin deal rather than a mistake. The other thing that can be wrong about a price
is whether the invoice matches what was agreed, and that is Invoice price differs from the
agreement: this class asks whether the agreement itself was sound.

- **Verantwortlich:** Sales management, with purchasing when the purchase price is the stale figure
- **Aufgelöst durch:** Agreeing a price at or above the purchase price, or correcting the purchase
  price if that is what is wrong.
- **Schwere:** `high`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `086/FR-001`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_sold_below_purchase_price`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `returned_not_credited` — Returned and not credited {#exception-returned_not_credited}

A customer has sent goods back and has not been given the money back. Reality takes what has come
back against that order line's delivery promise, and compares it with what credit note lines credit
against the same line. Only goods somebody was actually charged for can need crediting: a return of
something no invoice line ever billed leaves the company owing nothing, so nothing is reported.
Every credit note line pointing at the order line counts, so crediting across two notes or in
instalments behaves without special handling. Quantities are compared across the item's own stated
units where it says how they relate, and a pair that still cannot be reconciled is not compared here
at all — it is reported as Units not comparable rather than ignored. A line with nothing returned
says nothing at all. A restocking fee, a damage deduction or a write-off is recorded as a charge
line beside a full credit — credit the goods that came back, charge for what is being kept — and the
charge names no order line, because it is not credit for goods. Recorded the other way, as a credit
note for fewer units than came back, the document says exactly that: the remainder is uncredited,
this class reports it, and nothing will ever clear it, because nobody is going to credit it. This is
the second half of one line's life: the first is Shipped and not billed, where goods went out and no
invoice followed. Money credited without goods arriving is the opposite direction, and that is
Credited and not returned. The same condition on the buying side, where the company sent goods back
to a supplier and no credit followed, is Returned to supplier and not credited. Whether the goods
that came back were ever dealt with is another half, and that is Return not dealt with. And this
class counts credit notes as written, not as paid: a credit note that was never booked is Credit
note not booked, and one booked and never given back is Credit note not given back. Seeing nothing
here means the paperwork exists, not that the customer has their money.

- **Verantwortlich:** Customer service, with billing when the credit note is the missing step
- **Aufgelöst durch:** Crediting the returned quantity on a credit note line that names the order
  line.
- **Schwere:** `high`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `079/FR-007`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_returned_not_credited`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `credited_not_returned` — Credited and not returned {#exception-credited_not_returned}

More has been credited against an order line than has actually come back. Reality compares what
credit note lines credit with what the delivery promise has received back, and reports the excess.
It waits for a return before saying anything: crediting a customer without asking for the goods is a
decision rather than a discrepancy, and in consumer trade telling somebody to keep an item is
ordinary, so a credit with nothing returned is never reported. Once goods have started coming back,
a credit larger than what arrived is a real difference and money the company has given away.
Quantities are compared across the item's own stated units where it says how they relate, and a pair
that still cannot be reconciled is reported as Units not comparable rather than being passed over in
silence. The opposite direction, goods back with no credit, is Returned and not credited; the same
shape on the buying side, where an invoice runs ahead of the goods, is Billed and not received.
Where it is a supplier that credited more than came back, that is Supplier credited more than went
back.

- **Verantwortlich:** Customer service, with credit control when the money is already gone
- **Aufgelöst durch:** The outstanding goods arriving, or correcting the credit note.
- **Schwere:** `high`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `079/FR-008`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_credited_not_returned`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `supplier_return_not_credited` — Returned to supplier and not credited {#exception-supplier_return_not_credited}

Goods went back to a supplier and the supplier has not credited them, so the company has paid or
owes for something it no longer has. Reality counts the movements that took goods out against that
purchase order line, subtracts what supplier credit note lines naming the same line credit, and
reports the difference. Only quantities a supplier invoice actually billed can need crediting: goods
returned before the invoice arrives leave nothing owing and are not reported until it does, which is
a window in which this class deliberately says less than an operator might want. It counts what was
recorded rather than what was agreed, so a movement a correction has voided stops counting. The
opposite direction, a supplier crediting more than went back, is Supplier credited more than went
back. The same condition on the selling side, where a customer's goods came back with no credit, is
Returned and not credited. Whether the credit was ever booked once the supplier sent it is Supplier
credit not booked, and whether the company ever took the money is Supplier credit not claimed. Note
that Billed and not received says nothing here on purpose: the goods did arrive, and a return does
not unmake a receipt.

- **Verantwortlich:** Purchasing, with accounts payable when the money has already gone
- **Aufgelöst durch:** The supplier's credit note naming the order line, or the goods coming back
  again.
- **Schwere:** `high`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `090/FR-009`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_supplier_return_not_credited`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `supplier_credit_not_returned` — Supplier credited more than went back {#exception-supplier_credit_not_returned}

A supplier has credited more than the company actually sent back. Reality compares what supplier
credit note lines credit against a purchase order line with what movements took out against the same
promise, and reports the excess. Nothing is reported while nothing has gone back at all: a rebate,
an allowance or a price correction is an ordinary supplier credit with no goods behind it, and
treating one as a discrepancy would report every quarter-end agreement a company makes. Once goods
have started going back, a credit larger than what went is a real difference and worth a question.
The opposite direction, goods back with no credit, is Returned to supplier and not credited; the
same shape on the selling side, where the company credited a customer for goods that never arrived,
is Credited and not returned.

- **Verantwortlich:** Purchasing, with accounts payable at period end
- **Aufgelöst durch:** The remaining goods going back, or the supplier correcting its credit note.
- **Schwere:** `high`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `090/FR-010`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_supplier_credit_not_returned`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `return_unresolved` — Return not dealt with {#exception-return_unresolved}

Goods came back and nobody has said what happened to them. Reality does not store an outcome: what
became of returned stock is whatever movement settled the return — put back on the shelf, written
off, or sent back to the supplier — and a movement that settles one says so by naming it. That last
one used to be the resolution the model could not express; goods going back to a supplier are now a
movement Reality records, so sending a customer's faulty item on to its maker settles the return. A
return nothing has settled is stock the company owns, cannot sell, and has stopped counting as a
problem. How long is too long is learned from this company's own settled returns, the middle of the
most recent twenty, and reported past three times that, never sooner than a fortnight; a company
with fewer than five settled returns is not judged at all. Part of a return may be restocked and
part written off, so the entry reports only what is still sitting and shrinks as each part is dealt
with. This is the goods half of a return's life. The money half — goods back and no credit note — is
Returned and not credited, and a return can be in either without the other.

- **Verantwortlich:** Warehouse control, with customer service when the decision is theirs
- **Aufgelöst durch:** Restocking, writing off, or sending the goods back to the supplier, saying
  which return it settles.
- **Schwere:** `normal`
- **Datensatztyp:** `movement`
- **Spezifikation:** `082/FR-007`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_return_unresolved`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`movements`](./views#view-movements)

## `receipt_unbilled` — Receipt not invoiced {#exception-receipt_unbilled}

Goods arrived against a purchase order line and no supplier invoice has ever billed them. On its own
that is the usual sequence and worth nothing; what makes it a finding is time. Reality measures how
long this company's own suppliers normally take, from the last receipt against a line to the date of
the first invoice that billed it, takes the middle of the most recent twenty, and reports a receipt
still unbilled past three times that — never sooner than a fortnight. A company with fewer than five
invoiced receipts is not judged at all. What is at stake is an accrual nobody has made and a
supplier nobody is chasing, and it grows quietly because nothing is wrong with any single record. It
counts what the company still holds rather than everything that once arrived: goods sent back to a
supplier stop being something to accrue an invoice for, and what the supplier owes for them is
Returned to supplier and not credited. Quantities are compared across the item's own stated units
where it says how they relate, and a pair that still cannot be reconciled is reported as Units not
comparable rather than skipped in silence. The opposite direction, an invoice arriving for goods
that never did, is Billed and not received.

- **Verantwortlich:** Purchasing, with accounts payable at period end
- **Aufgelöst durch:** The supplier invoice arriving and an invoice line naming the order line.
- **Schwere:** `high`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `080/FR-007`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_receipt_unbilled`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `units_not_comparable` — Units not comparable {#exception-units_not_comparable}

An item's lines are recorded in units Reality cannot reconcile, so several checks on them are being
skipped. Reality compares a quantity against an agreement only where the two are the same unit, or
where this item states how its own units relate — a purchase unit and a conversion factor, "we buy
this in boxes of twelve", written down by the company. Where it can, it converts at read time and
stores nothing; where it cannot, it says nothing about that line, and that silence used to be
indistinguishable from nothing being wrong. This entry is the silence made visible. While it stands,
Shipped and not billed, Billed and not received, Receipt not invoiced, Returned and not credited and
Credited and not returned are all skipping the affected lines, so an empty queue for those classes
does not mean this item is in order. It says which of two things is wrong. Either no conversion is
stated, and the fix is to state it once on the item; or one is stated and does not divide evenly — a
hundred and seven pieces are not a number of boxes — and the fix is to record the line in a unit
that comes out, because rounding a remainder is the thing this product exists not to do. One entry
per item, however many lines are affected, because one statement is missing and one statement fixes
it. Prices are a different matter and are never converted at all: a price per box divided by twelve
is money nobody agreed, so a price left uncompared for units is not reported here and no statement
would help it. What an invoice says about a price it did agree on is Invoice price differs from the
agreement.

- **Verantwortlich:** Whoever maintains item master data, with purchasing
- **Aufgelöst durch:** Stating the item's purchase unit and conversion factor, or recording the
  lines in a unit that reconciles.
- **Schwere:** `normal`
- **Datensatztyp:** `item`
- **Spezifikation:** `087/FR-007`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_units_not_comparable`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht [`items`](./views#view-items)

## `reservation_exceeds_stock` — Reservation exceeds stock {#exception-reservation_exceeds_stock}

More of an item is reserved than the company physically holds. Reality sums every movement of that
item across the whole company, in minus out, and compares the result with the sum of the
reservations still active on it. Because reserving never allocates more than is available, this can
only mean the goods left afterwards — a stocktake adjustment, a write-off, or a shipment against a
different promise. That is why nothing else reports it: each affected order still holds a
reservation covering its remainder, so none of them is flagged as Customer commitment at risk and
every one of them looks safe. The entry names every order competing for the item without saying
which one will fail, because no rule in the model decides who is served first. Cover is judged per
item across the company, so stock sitting in another location still counts.

- **Verantwortlich:** Warehouse control, with purchasing when stock has to be replaced
- **Aufgelöst durch:** Receiving stock, or releasing reservations until they fit what is there.
- **Schwere:** `high`
- **Datensatztyp:** `item`
- **Spezifikation:** `068/FR-005`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_reservation_exceeds_stock`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht [`items`](./views#view-items)

## `silent_source` — Silent source {#exception-silent_source}

A connected system has stopped delivering. Reality never asks how often a source should arrive; it
reads the receipt times of that capability's own recent records, takes the longest pause it has
shown, and reports when the current silence exceeds twice that pause — never sooner than a day.
Learning the rhythm rather than being told it is what lets a source that pauses every night and
every weekend stay quiet while a genuine stoppage still surfaces. Nothing is reported for a
capability that has delivered only a handful of times, or never at all, because no rhythm can be
claimed from that and a guess would be worse than silence. This is the dangerous failure, because
nothing breaks: every figure stays correct and quietly older by the day. Something that did arrive
and could not be understood is the other case, Source interpretation failure.

- **Verantwortlich:** Integration operations, with the owner of the source system
- **Aufgelöst durch:** A record arriving from that source.
- **Schwere:** `high`
- **Datensatztyp:** `source_capability`
- **Spezifikation:** `072/FR-001`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_silent_source`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `source_interpretation_failure` — Source interpretation failure {#exception-source_interpretation_failure}

Something arrived from a connected system and could not be turned into business records. Reality
stores every incoming record losslessly before interpreting it, so the failure happens after the
data is safe: the import job ends in the failed state and keeps the error, while the original
payload stays exactly as it was received. Nothing from that record reached documents, commitments or
postings, which is what makes it worth attention — the business is missing whatever it contained.
Retrying is safe for the same reason: the raw record is untouched. Something arrived here and could
not be used; a source that has stopped arriving at all is the other case, Silent source.

- **Verantwortlich:** Integration operations, with the owner of the source system
- **Aufgelöst durch:** A successful retry once the cause of the failure is removed.
- **Schwere:** `high`
- **Datensatztyp:** `import_job`
- **Spezifikation:** `020/FR-006`
- **Nachweis:**
  `tests/operational_exceptions/test_derivation.py::test_source_interpretation_failure`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `unexplained_movement` — Unexplained movement {#exception-unexplained_movement}

Stock physically moved and nothing records why. Reality looks at shipments, receipts and returns
that carry neither a commitment nor a source record, and ignores those that a later correction has
already replaced. A return may now name the customer delivery it reverses, so goods coming back
against a known order are explained and never reported here — and a movement may name the return it
settles, so a return is explainable at both ends. A return standing unsettled is not unexplained; it
is Return not dealt with. The quantities are not in doubt — the movement happened and the stock
figures include it — but there is no order and no incoming document that explains it, so the company
cannot say what the goods were for. It is the one condition with no way back.

- **Verantwortlich:** Warehouse control
- **Aufgelöst durch:** Nothing. The movement stays part of history; only a correction changes what
  follows from it.
- **Schwere:** `normal`
- **Datensatztyp:** `movement`
- **Spezifikation:** `020/FR-007`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_unexplained_movement`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`movements`](./views#view-movements)

## `sales_invoice_unposted` — Sales invoice not booked {#exception-sales_invoice_unposted}

A sales invoice exists on paper and has never been booked, so the company has billed a customer and
its own accounts know nothing about it. While it stands, nothing is owed as far as Reality is
concerned: the invoice reaches no aging register, no overdue receivable, no credit limit arithmetic,
and no credit note can be netted against it. Recording a document and booking it are two acts,
exactly as they are for a credit note, and the distance between them is a real business fact rather
than an oversight in the model. How long that distance may be is learned from this company's own
booked sales invoices — the middle of the most recent twenty, three times over, never sooner than a
fortnight — so a business that books at month end is not reported every month. It is learned from
sales invoices alone: booking one is a different process with a different owner from booking a
supplier invoice or either kind of credit note, and one rhythm must not judge another. A company
with fewer than five booked sales invoices is not judged at all, which is the safe direction and
also the case where an operator might most want telling. An invoice that was booked and then
deliberately reversed is not reported, because that is a decision rather than a forgotten act. The
same condition on a credit the company wrote is Credit note not booked; on the buying side it is
Supplier invoice not booked.

- **Verantwortlich:** Billing, with accounts receivable at period end
- **Aufgelöst durch:** Booking the invoice, or correcting it if it should never have been raised.
- **Schwere:** `high`
- **Datensatztyp:** `document`
- **Spezifikation:** `092/FR-001`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_sales_invoice_unposted`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`documents`](./views#view-documents)

## `supplier_invoice_unposted` — Supplier invoice not booked {#exception-supplier_invoice_unposted}

A supplier invoice exists on paper and has never been booked, so the company owes money its books do
not show. While it stands the invoice reaches no payment run, no overdue payable and no early
payment discount, and no supplier credit can be netted against it — the liability is simply absent.
It is the mirror of Sales invoice not booked and is judged the same way, from this company's own
booked supplier invoices rather than from any other document type: booking somebody else's invoice
is a different process with a different owner from booking one's own. A company with fewer than five
booked supplier invoices is not judged at all. An invoice booked and then deliberately reversed is
not reported. The same condition on a credit a supplier sent is Supplier credit not booked. Note
that an unbooked invoice is not the same as a missing one: goods received that no supplier has
invoiced at all is Receipt not invoiced.

- **Verantwortlich:** Accounts payable
- **Aufgelöst durch:** Booking the invoice, or rejecting it if the supplier should never have sent
  it.
- **Schwere:** `high`
- **Datensatztyp:** `document`
- **Spezifikation:** `092/FR-002`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_supplier_invoice_unposted`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`documents`](./views#view-documents)

## `credit_note_unposted` — Credit note not booked {#exception-credit_note_unposted}

A credit note exists on paper and has never been booked, so the customer has been promised money the
company's own accounts know nothing about. Recording a credit note and booking it are two acts,
exactly as they are for an invoice, and the distance between them is a real business fact rather
than an oversight in the model. How long that distance may be is learned from this company's own
booked credit notes — the middle of the most recent twenty, three times over, never sooner than a
fortnight — so a business that books at month end is not reported every month. A company with fewer
than five booked credit notes is not judged at all, which is the weak point of this class: credit
notes are rare in most businesses, so the very company most likely to forget one may never reach the
history that would catch it. Once booked, whether the money actually went back is the next question,
and that is Credit note not given back. The mirror on the buying side, a credit a supplier sent and
nobody booked, is Supplier credit not booked, and it is judged against its own rhythm rather than
this one. The same condition on the primary document is Sales invoice not booked, which is the one
more likely to speak: credit notes are rare enough that many companies never reach the history this
rule needs, and invoices are not. Whether the goods that came back were credited at all is the
question before it, and that is Returned and not credited.

- **Verantwortlich:** Accounts receivable
- **Aufgelöst durch:** Booking the credit note, or cancelling it if it should never have been
  raised.
- **Schwere:** `high`
- **Datensatztyp:** `document`
- **Spezifikation:** `084/FR-008`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_credit_note_unposted`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`documents`](./views#view-documents)

## `credit_note_unsettled` — Credit note not given back {#exception-credit_note_unsettled}

A booked credit note has been neither netted against an invoice nor refunded, so the company's own
books say it owes this customer money it has not moved. There is no waiting period: the obligation
exists from the moment the credit note is booked, and the entry reports what is still outstanding
and shrinks as each part is settled. A credit is settled the two ways a business settles one —
netted against an invoice the customer still owes, or paid back — and both go through the same
relation a payment uses. This is not the same as Unmatched financial event, which reports cash that
moved with nobody saying what it was for; a credit note moves no cash, which is why that class
cannot see it. The stage before this one, a credit note that was never booked at all, is Credit note
not booked. The mirror on the buying side, money a supplier owes this company, is Supplier credit
not claimed.

- **Verantwortlich:** Accounts receivable, with treasury when the money has to leave
- **Aufgelöst durch:** Netting the credit against an open invoice, or refunding the customer.
- **Schwere:** `high`
- **Datensatztyp:** `document`
- **Spezifikation:** `084/FR-009`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_credit_note_unsettled`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`documents`](./views#view-documents)

## `supplier_credit_unposted` — Supplier credit not booked {#exception-supplier_credit_unposted}

A supplier has sent a credit note and nobody has booked it, so the company's accounts say it owes
more than it does. This is the direction that costs money: a payment run built on an overstated
payable pays the supplier for something already credited, and nothing else in this queue can see it,
because every figure involved is correct on its own. Recording a credit and booking it are two acts,
exactly as they are for an invoice. How long the distance between them may be is learned from this
company's own booked supplier credits — the middle of the most recent twenty, three times over,
never sooner than a fortnight — and deliberately not from the credits it writes itself: booking a
credit somebody else sent is a different process with a different owner, and one rhythm must not
judge the other. A company with fewer than five booked supplier credits is not judged at all, which
is the weak point of this class in exactly the way it is the weak point of its mirror. Once booked,
whether the credit was ever taken is the next question and that is Supplier credit not claimed. The
same condition on a credit the company wrote itself is Credit note not booked, and on the supplier's
primary document it is Supplier invoice not booked.

- **Verantwortlich:** Accounts payable
- **Aufgelöst durch:** Booking the supplier credit note, or rejecting it if the supplier should
  never have sent it.
- **Schwere:** `high`
- **Datensatztyp:** `document`
- **Spezifikation:** `089/FR-009`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_supplier_credit_unposted`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`documents`](./views#view-documents)

## `supplier_credit_unclaimed` — Supplier credit not claimed {#exception-supplier_credit_unclaimed}

A booked supplier credit has been neither netted against an invoice nor refunded, so the company's
own working capital is sitting with a supplier and nobody is asking for it. There is no waiting
period: the claim exists from the moment the credit is booked, and the entry reports what is still
outstanding and shrinks as each part is settled. It is settled the two ways a business settles one —
netted against an invoice the company still owes that supplier, or refunded in money — and both go
through the same relation a payment uses, which is why a payable falls the same way whatever settled
it. This is not Unmatched financial event, which reports cash that moved with nobody saying what it
was for; a credit note moves no cash, which is why that class cannot see it. The stage before this
one is Supplier credit not booked, and the same condition on a credit the company wrote itself is
Credit note not given back. One thing this class cannot tell you is whether goods actually went
back: a return to a supplier cannot be recorded in Reality at all yet, so a credit for returned
goods is money with no evidence of the goods behind it.

- **Verantwortlich:** Accounts payable, with purchasing when the supplier has to be chased
- **Aufgelöst durch:** Netting the credit against an open supplier invoice, or having the supplier
  refund it.
- **Schwere:** `high`
- **Datensatztyp:** `document`
- **Spezifikation:** `089/FR-010`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_supplier_credit_unclaimed`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`documents`](./views#view-documents)

## `overdue_receivable` — Overdue receivable {#exception-overdue_receivable}

A customer has not paid an invoice by the date its terms promised. Reality derives the due date
rather than reading one, because none is stored: the invoice date advanced by the payment term on
the invoice, or by the customer's term when the invoice has none, and only when neither exists is
the invoice due on the day it was issued. The outstanding amount comes from the ledger after
payments, credit notes and allocations, so a partly paid invoice reports what is still owed rather
than its gross value. The entry appears when the derived date has passed and something remains
outstanding; an invoice whose date cannot be read asserts nothing. Money never arrived here. An
amount that did arrive but could not be assigned to anything is the opposite case, Unmatched
financial event; the same condition on a supplier invoice, where your company owes the money, is
Overdue payable. This one assumes the invoice exists: goods delivered that nobody has invoiced at
all is Shipped and not billed, where the customer has not been asked yet and is therefore not late.
It is also about one invoice rather than about the relationship: a customer owing more in total than
was agreed is Credit limit exceeded, and being late on an invoice is neither necessary nor
sufficient for that. One remainder is not a debt at all: where the term granted an early payment
discount, the customer paid inside that window, and what is left is no more than the agreed rate
allows, the entry carries the early payment discount reason. It still appears, because the amount
really is open — what is missing is the credit note recording the discount, not the money.

- **Verantwortlich:** Accounts receivable
- **Aufgelöst durch:** Settling the outstanding amount, or reversing the invoice.
- **Schwere:** `high`
- **Datensatztyp:** `document`
- **Spezifikation:** `069/FR-001`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_overdue_receivable`

**Ursachen**

| ID                             | Bezeichnung                  | Spezifikation |
| ------------------------------ | ---------------------------- | ------------- |
| `early_payment_discount_taken` | Early payment discount taken | `088/FR-010`  |

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`documents`](./views#view-documents)

## `credit_limit_exceeded` — Credit limit exceeded {#exception-credit_limit_exceeded}

A customer owes more than the company agreed to let it owe. Reality reads the credit limit recorded
on the Party and compares it with what that customer still owes on open sales invoices, taken from
the same settlement derivation the aging register and the overdue classes use, so the figure here
can never disagree with theirs. Only invoices in the customer's own currency count: a limit is one
number, and converting a foreign balance into it would be a guess. An amount exactly equal to the
limit is allowed, because that is the number that was agreed. A limit of zero means no limit has
been recorded, not a customer allowed to owe nothing — the field defaults to zero, so reading it the
other way would report every customer on the day this class ships. A customer meant to be cash-only
is therefore silent here, and belongs behind a delivery hold rather than a limit of zero. This is
about the total carried; a single invoice past its payment date is Overdue receivable, and a
customer can be in either without being in the other.

- **Verantwortlich:** Credit control, with sales when the limit itself is the question
- **Aufgelöst durch:** Settling enough of the open invoices, or agreeing and recording a higher
  limit.
- **Schwere:** `high`
- **Datensatztyp:** `party`
- **Spezifikation:** `078/FR-001`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_credit_limit_exceeded`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `overdue_payable` — Overdue payable {#exception-overdue_payable}

A supplier invoice is past the date its terms promised and money is still owed. It is the exact
mirror of the receivable and shares its rule: the due date is derived from the invoice date and the
payment term on the invoice, or the supplier's term when the invoice has none, and the outstanding
amount comes from the ledger after payments, credit notes and allocations. What is at stake is
different from a late delivery, though — a supplier waiting for money may stop shipping, a discount
lapses, a dunning fee arrives. A supplier late with goods rather than with money is Overdue incoming
supplier commitment, and the same condition on a customer invoice is Overdue receivable. Where the
company took an early payment discount the term granted and the residue is still sitting on the
invoice, the entry carries the early payment discount reason; the discount while it is still there
to take is Early payment discount still available. Whether the invoice should have been raised at
all is a different question: goods invoiced but never received is Billed and not received, and an
invoice recorded twice under one number is Duplicate supplier invoice.

- **Verantwortlich:** Accounts payable
- **Aufgelöst durch:** Paying the outstanding amount, or reversing the invoice.
- **Schwere:** `high`
- **Datensatztyp:** `document`
- **Spezifikation:** `074/FR-001`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_overdue_payable`

**Ursachen**

| ID                             | Bezeichnung                  | Spezifikation |
| ------------------------------ | ---------------------------- | ------------- |
| `early_payment_discount_taken` | Early payment discount taken | `088/FR-010`  |

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`documents`](./views#view-documents)

## `purchase_discount_available` — Early payment discount still available {#exception-purchase_discount_available}

A supplier invoice can still be paid for less, and the day it stops being true is approaching.
Reality takes the payment term governing the invoice — its own, else its supplier's — reads the
discount rate and the number of days that term states, places the deadline on the invoice's own
date, and reports every unpaid invoice whose deadline has not yet passed, soonest first. It names
the rate the company negotiated, the day it expires and the amount the ledger holds open. It never
says what the discount is worth: a rate applied to a gross amount is a division producing money
nobody agreed, with a remainder to round, and the amount follows from the invoice itself. Nothing
appears for a term that states no discount, which is most terms outside German-speaking trade.
**This entry goes quiet in two very different ways.** Paying the invoice ends it, and so does the
deadline passing — so silence here means the discount was taken or lost, and only the payment says
which. There is deliberately no class for a discount already lost, because nothing would clear it
and every condition in this queue is one somebody can end. An invoice past its payment date is a
different thing and is Overdue payable; a term whose discount window outlasts its own due date will
show both, and both are true. When a discount has been taken and the residue is still sitting on the
invoice, that shows as the early payment discount reason on Overdue payable or Overdue receivable
rather than here. A payment run reads these invoices for the same reason: `preview_payment_run`
proposes every payable invoice whose window is still open, alongside what is simply due, and names
the rate and the deadline there too. It states no discounted amount either. The person running it
states what to pay, and paying 98 of 100 leaves 2 open, which is the residue described above.

- **Verantwortlich:** Accounts payable, with whoever schedules the payment run
- **Aufgelöst durch:** Paying the invoice, on its own or in a payment run. It also stops appearing
  once the deadline passes, which is the loss rather than the fix.
- **Schwere:** `normal`
- **Datensatztyp:** `document`
- **Spezifikation:** `088/FR-007`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_purchase_discount_available`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`documents`](./views#view-documents)

## `duplicate_supplier_invoice` — Duplicate supplier invoice {#exception-duplicate_supplier_invoice}

A supplier invoice carries a number that supplier has already used. Reality groups supplier invoices
by Party and by number, ignoring surrounding spaces and letter case, and reports every document
after the first. Nothing is refused when the second arrives: the same invoice legitimately reaches
the company twice when two connectors carry it, and recording both is what preserves the evidence
that both arrived. The entry names the earlier document and both source records, which is what tells
an operator whether the second was typed in or came from a system. Documents are read before
postings, so a duplicate is visible before anyone pays it. An invoice whose posting has been
reversed is neither reported nor matched against, because a withdrawn invoice cannot be paid twice
and a supplier reissuing a corrected invoice under the same number is ordinary. An invoice with no
number is left out entirely, since an empty number is not something two documents can share. This is
one of three things that can be wrong about a supplier invoice: that it is past its payment date is
Overdue payable, and that it bills goods which never arrived is Billed and not received.

- **Verantwortlich:** Accounts payable
- **Aufgelöst durch:** Reversing whichever posting was made in error, or confirming the numbers
  differ.
- **Schwere:** `high`
- **Datensatztyp:** `document`
- **Spezifikation:** `078/FR-006`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_duplicate_supplier_invoice`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht
[`documents`](./views#view-documents)

## `unmatched_financial_event` — Unmatched financial event {#exception-unmatched_financial_event}

Money moved through the ledger and part of it is not assigned to anything. Reality looks at the
receivable or payable side of a payment posting and subtracts the settlement allocations recorded
against it; the entry appears while a positive remainder is left over. The cash is real and the
books balance — what is missing is the link that says which invoice it settled, so neither the
customer account nor the open-item list can be trusted until it is made. This is the opposite case
to Overdue receivable: there nothing arrived, here something arrived and nobody said what it was
for. It only ever concerns postings that moved cash, so a booked credit note nobody has settled is
not here — that is Credit note not given back.

- **Verantwortlich:** Accounts receivable or accounts payable
- **Aufgelöst durch:** Allocating the remainder to the invoices it pays.
- **Schwere:** `high`
- **Datensatztyp:** `ledger_entry`
- **Spezifikation:** `020/FR-008`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_unmatched_financial_event`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `announced_return_not_arrived` — Announced return has not arrived {#exception-announced_return_not_arrived}

A customer said goods were coming back and they have not. Until this existed a return was only
recordable once it was standing on the receiving dock, so a customer's own words — how much, why,
the number the parcel would carry, the day they said it would go — were kept in somebody's inbox and
nothing could notice when the parcel never came. The entry appears in two ways and says which one
spoke. Where the customer named a day, that day is the measurement and nothing needs learning: past
it, the entry appears and says how many days late the parcel is. Where they named none, this
company's own rhythm decides — the middle of the most recent twenty announcements that did arrive,
three times over, never sooner than a fortnight — and a company with fewer than five arrivals is not
judged at all, because a company without history is not one with a lenient threshold, it is one this
rule cannot speak about. The floor matches Return not dealt with on purpose: a fortnight for a
parcel to travel is ordinary, and the two halves of a return's life should not disagree about what
ordinary means. It is one class rather than two because it is one condition with one owner and one
clearing path; the only difference between the two ways in is how the date was arrived at, which
belongs in the entry rather than in this catalog. A withdrawn announcement is not reported: the
customer has said the parcel is not coming and there is nothing left for anybody to do. Nothing here
makes the goods available — an announced return is not supply, because goods a customer has promised
to send are not goods anybody can sell. This is the half of a return's life before the goods arrive.
The goods half after is Return not dealt with, and the money half is Returned and not credited.

- **Verantwortlich:** Customer service, with the receiving desk once the parcel is expected
- **Aufgelöst durch:** The goods arriving against the announcement, or the customer withdrawing it.
- **Schwere:** `normal`
- **Datensatztyp:** `return_announcement`
- **Spezifikation:** `099/FR-011`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_announced_return_not_arrived`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `commitment_hold_unreleased` — Promise hold not lifted {#exception-commitment_hold_unreleased}

A promise was put on hold and nobody has lifted the hold. A hold is how somebody says they are
dealing with something: it stops execution without changing or deleting the obligation, and it
carries the reason they gave, a note, who raised it and when. That is exactly why Closing stale
promises skips a held promise — a sweep must not close something out from under the person handling
it — and **that protection has no expiry**. A hold raised for a credit check somebody finished a
year ago goes on shielding its promise from the only operation that could close it, and until this
class existed nothing reported either the hold or the shielding. How long is too long is learned
from this company's own lifted promise holds, the middle of the most recent twenty, reported past
three times that and never sooner than a week, because a hold is an active statement and a few days
is ordinary. A company with fewer than five lifted promise holds is not judged at all. The entry
names the reason code, the note, who raised it, how long it has stood and the quantity still open on
the promise being held — a hold on nothing is a formality somebody forgot, and a hold on a real
backlog is money standing still. A hold on a promise that is no longer open is not reported. Since
spec 108 that is a legacy situation rather than an ordinary one: cancelling a promise releases its
holds, and so does a revision that settles one as fulfilled, so a promise that is not open no longer
carries an active hold. The skip stays because a tenant that was running before then may still hold
such rows and nothing tidies them; the release operation reaches them from every surface. That
release is not the automatic release this class refuses — a hold is not lifted because time passed,
it is lifted because its subject is gone. Nothing here releases or suppresses anything: the promise
appears in the queue exactly as it did, because a hold says somebody is dealing with it and not that
it is fine. The same condition on a whole customer is Party hold not lifted, and it is more serious.

- **Verantwortlich:** Whoever raised the hold, named in the entry, with the reason code saying which
  team that is
- **Aufgelöst durch:** Lifting the hold, or doing the thing it was raised for and then lifting it.
- **Schwere:** `normal`
- **Datensatztyp:** `commitment_hold`
- **Spezifikation:** `107/FR-001`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_commitment_hold_unreleased`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `party_hold_unreleased` — Party hold not lifted {#exception-party_hold_unreleased}

A hold on a whole counterparty that nobody has lifted, and the more serious of the two because of
what it blocks. While a customer delivery hold stands, **every** shipment to that customer is
refused when somebody tries to record it — including orders taken after the hold was raised, by
people who never knew about it — and every promise to that customer is also skipped by Closing stale
promises. So a forgotten party hold is a customer nobody can ship to, quietly, for as long as it
stands. How long is too long is learned from this company's own lifted party holds, a separate
population from promise holds because they are a different process with different people behind
them: the middle of the most recent twenty, three times over, never sooner than a week, silent below
five. The entry names the hold type, the reason code, the note, who raised it, how long it has
stood, and the **number** of open customer deliveries it is blocking. A count and never a summed
quantity, because quantities across different items do not add up — the rule Units not comparable
exists to protect. A hold blocking nothing is still reported, because it will refuse the next order
too. Every hold type is reported and named rather than filtered to the one that exists today, which
means a new hold type must arrive with its own way of being lifted. Nothing here releases or
suppresses anything. The same condition on a single promise is Promise hold not lifted.

- **Verantwortlich:** Whoever raised the hold, named in the entry, with the reason code saying which
  team that is
- **Aufgelöst durch:** Lifting the hold, or doing the thing it was raised for and then lifting it.
- **Schwere:** `high`
- **Datensatztyp:** `party_hold`
- **Spezifikation:** `107/FR-001`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_party_hold_unreleased`

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `stock_expired` — Expired stock on hand {#exception-stock_expired}

A company is holding goods whose best-before date has passed. Until spec 109 nothing in the model
could express a best-before at all — a Lot carried an item, a number and where it came from — so
expired stock looked exactly like good stock: it counted as available, it could be reserved, and the
first person to learn otherwise was the customer. The date is now recorded on the lot exactly as
somebody read it off the goods or off the delivery note. **It is never computed:** a shelf life in
days multiplied out from a production date would be a date nobody stated, which is what Reality
refuses everywhere. Reality compares that stated date with the day the queue is asked, and reports
every lot past it that still has stock on hand, counted through the one tracked-identity stock rule
the inventory register uses so the two can never disagree. Oldest expiry first. A lot with nothing
left is not reported: nothing is held, so there is nothing for anybody to do. A lot with **no**
stated date says nothing in either direction — there is no way to tell an item with no shelf life
from one whose label nobody read, and inventing that distinction would be worse than the silence.
**There is deliberately no entry for stock that is about to expire**, which is the more useful
report and the one a reader will look for. It needs a horizon, and no horizon exists on stated
ground: nothing on an item states a shelf life and no term states a minimum remaining life. The one
mechanism that could produce a number is the learned-expectation rule, which already governs ten of
this catalog's classes on figures nobody has checked against a real business; an eleventh would grow
that risk to buy a threshold nobody could defend. What would unblock it is a customer's stated
minimum remaining life, or a measured turnover from a real business — either a received or a
measured figure rather than an invented one. Nothing here blocks, chooses or releases anything. A
picker can still ship expired stock, because refusing the movement would stop a company recording
something that already happened, and choosing which lot ships is an allocation policy this product
has never had. So this entry reduces surprise rather than preventing loss.

- **Verantwortlich:** Warehouse control, with quality assurance where the goods are regulated
- **Aufgelöst durch:** Writing the stock off with an adjustment, sending it back to the supplier, or
  otherwise moving it out of stock.
- **Schwere:** `high`
- **Datensatztyp:** `lot`
- **Spezifikation:** `109/FR-006`
- **Nachweis:** `tests/operational_exceptions/test_derivation.py::test_stock_expired`

**Ursachen**

| ID                      | Bezeichnung             | Spezifikation |
| ----------------------- | ----------------------- | ------------- |
| `reserved_for_delivery` | Reserved for a delivery | `109/FR-008`  |

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `missing_acquisition_cost` — Missing acquisition cost {#exception-missing_acquisition_cost}

A company-generation subject has no supported actual acquisition cost. Missing evidence remains
unknown and is never treated as zero.

- **Verantwortlich:** Purchasing or inventory control
- **Aufgelöst durch:** Confirming the missing receipt-cost evidence and publishing a current
  complete company generation.
- **Schwere:** `high`
- **Datensatztyp:** `item`
- **Spezifikation:** `234/FR-025`
- **Nachweis:**
  `tests/test_cost_findings.py::test_missing_acquisition_cost_includes_unsold_inventory_subject`

**Ursachen**

| ID                                | Bezeichnung                     | Spezifikation |
| --------------------------------- | ------------------------------- | ------------- |
| `acquisition_cost_unknown`        | Acquisition cost unknown        | `234/FR-014`  |
| `contribution_goods_cost_unknown` | Contribution goods cost unknown | `234/FR-014`  |

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht [`items`](./views#view-items)

## `unassigned_cost_component` — Unassigned cost component {#exception-unassigned_cost_component}

Received cost evidence belongs to the company basis but has not been assigned to its economic cost
scope.

- **Verantwortlich:** Purchasing or finance operations
- **Aufgelöst durch:** Confirming an assignment or an evidenced not-applicable treatment and
  publishing a current generation.
- **Schwere:** `high`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `234/FR-025`
- **Nachweis:**
  `tests/test_cost_findings.py::test_unassigned_component_uses_existing_document_line_subject`

**Ursachen**

| ID                          | Bezeichnung               | Spezifikation |
| --------------------------- | ------------------------- | ------------- |
| `cost_component_unassigned` | Cost component unassigned | `234/FR-003`  |

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)

## `stale_cost_review` — Stale cost review {#exception-stale_cost_review}

Later relevant evidence exists after the retained financial review used by the published company
basis.

- **Verantwortlich:** Finance operations
- **Aufgelöst durch:** Reviewing the changed evidence and publishing a current company generation.
- **Schwere:** `normal`
- **Datensatztyp:** `item`
- **Spezifikation:** `234/FR-025`
- **Nachweis:**
  `tests/test_cost_findings.py::test_stale_review_identity_is_stable_across_generations`

**Ursachen**

| ID                        | Bezeichnung             | Spezifikation |
| ------------------------- | ----------------------- | ------------- |
| `later_relevant_evidence` | Later relevant evidence | `234/FR-015`  |

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain), Sicht [`items`](./views#view-items)

## `negative_actual_db1` — Negative actual DB1 {#exception-negative_actual_db1}

Complete supported actual goods cost exceeds the received net revenue of the reviewed sales line.

- **Verantwortlich:** Sales management
- **Aufgelöst durch:** Correcting the commercial evidence or accepting and reviewing a non-negative
  current contribution basis.
- **Schwere:** `normal`
- **Datensatztyp:** `document_line`
- **Spezifikation:** `234/FR-025`
- **Nachweis:**
  `tests/test_cost_findings.py::test_negative_actual_db1_requires_complete_supported_db1_not_db2`

**Ursachen**

| ID                              | Bezeichnung                   | Spezifikation |
| ------------------------------- | ----------------------------- | ------------- |
| `supported_actual_db1_negative` | Supported actual DB1 negative | `234/FR-011`  |

**Siehe auch:** Projection [`exceptions`](./views#projection-exceptions), Agenten-Tool
[`exceptions_list`](./commands#tool-exceptions_list), Agenten-Tool
[`exception_explain`](./commands#tool-exception_explain)
