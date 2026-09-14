# Operational Exceptions

Operational exceptions are current, tenant-scoped observations derived from Business
Reality. They are not persisted tickets and do not add operational state to Documents.
Every consumer uses `reality.services.exceptions` for the same list and explanation.

## Initial Taxonomy

The business meaning of each class, the operational function that owns it and the path that clears
it are required fields of the catalog and are published on the
[generated reference](../../apps/docs/content/catalogs/exceptions.md). This table stays the
specification-level mapping only.

| Class | Cause | Authority |
|---|---|---|
| `overdue_outgoing_customer_commitment` | `insufficient_reservation` | Open customer-delivery Commitment with remaining unfulfilled quantity and `due_at < as_of` |
| `outgoing_commitment_at_risk` | `insufficient_reservation` | Open customer-delivery Commitment whose active Reservation quantity is below remaining unfulfilled quantity |
| `order_stalled` | — | Open customer-delivery Commitment with no `due_at`, quantity outstanding, and an age past the learned fulfilment threshold |
| `overdue_incoming_supplier_commitment` | — | Open supplier-delivery Commitment with remaining receipt quantity and `due_at < as_of` |
| `shipped_not_billed` | — | Sales order DocumentLine whose quantity delivered through its Commitment exceeds the quantity billed by invoice lines naming it |
| `billed_not_received` | — | Purchase order DocumentLine whose quantity billed by invoice lines naming it exceeds the quantity received through its Commitment |
| `invoice_price_differs` | — | Invoice DocumentLine whose unit price differs from the unit price on the order line it names |
| `sold_below_purchase_price` | — | Sales order DocumentLine agreed below the standing default purchase price for its item, currency and unit at the moment of agreement |
| `returned_not_credited` | — | Sales order DocumentLine whose returned quantity, limited to what invoice lines billed, exceeds what credit note lines credit |
| `credited_not_returned` | — | Sales order DocumentLine whose credited quantity exceeds what has come back, where some quantity has come back |
| `supplier_return_not_credited` | — | Purchase order DocumentLine whose goods went back to the supplier and were not credited, counting only what a supplier invoice billed |
| `supplier_credit_not_returned` | — | Purchase order DocumentLine credited by the supplier for more than actually went back, silent while nothing has gone back |
| `return_unresolved` | — | `return` Movement with quantity no later movement has settled, older than the learned resolution threshold |
| `receipt_unbilled` | — | Purchase order DocumentLine with goods received, an unbilled remainder, and a last receipt older than the learned billing threshold |
| `units_not_comparable` | — | Item whose order and referencing lines are recorded in units that cannot be reconciled, so quantity comparisons on them are being declined |
| `supplier_credit_unposted` | — | Supplier credit note Document recorded and never booked, standing longer than this company's own rhythm for booking supplier credits |
| `supplier_credit_unclaimed` | — | Booked supplier credit note Document neither netted against a supplier invoice nor refunded |
| `purchase_discount_available` | — | Unpaid supplier invoice Document whose payment term grants an early-payment discount whose deadline has not passed |
| `reservation_exceeds_stock` | — | Item whose active Reservation quantity exceeds observed stock across the tenant |
| `silent_source` | — | Active SourceCapability whose silence exceeds twice its longest observed pause and at least a day |
| `source_interpretation_failure` | — | Failed ImportJob linked to its immutable SourceRecord |
| `unexplained_movement` | — | Shipment, receipt, or return with neither Commitment nor SourceRecord |
| `sales_invoice_unposted` | — | Sales invoice Document recorded and never booked, standing longer than this company's own rhythm for booking sales invoices |
| `supplier_invoice_unposted` | — | Supplier invoice Document recorded and never booked, standing longer than its own separate rhythm |
| `credit_note_unposted` | — | Credit note Document with no posting, older than the learned booking threshold |
| `credit_note_unsettled` | — | Posted credit note Document with an amount neither allocated nor refunded |
| `overdue_receivable` | — | Sales invoice Document whose derived due date has passed with an outstanding amount above zero |
| `credit_limit_exceeded` | — | Party with a recorded credit limit above zero whose outstanding sales-invoice balance in its own default currency exceeds that limit |
| `overdue_payable` | — | Supplier invoice Document whose derived due date has passed with an outstanding amount above zero |
| `duplicate_supplier_invoice` | — | Supplier invoice Document whose Party and normalised number match an earlier, unreversed supplier invoice |
| `unmatched_financial_event` | — | Payment-side AR/AP control LedgerEntry with a positive tenant-scoped unallocated remainder |

`insufficient_reservation` is nested evidence for an outgoing row and never a second
visible exception. One outgoing Commitment produces at most one entry: when the promise is
late, `overdue_outgoing_customer_commitment` supersedes `outgoing_commitment_at_risk` and
carries the reservation shortfall as its cause. A queue row states the condition of its
class and appends a clause for an attached cause only where that clause adds a value the
condition does not already state, so a partial shortfall on an overdue promise stays
readable without opening the explanation and a total one is not said twice.

`overdue_receivable` derives its due date rather than reading one: the invoice date
advanced by the payment term, and the invoice date itself when no term applies, so an
invoice without a term is due on issue. An invoice date that cannot be read asserts
nothing. That rule lives once in the application layer and is shared with the aging
register, so no surface may compute a due date of its own. The reported amount is the
outstanding remainder from the existing settlement derivation, never a recomputed balance,
and fully settled or reversed invoices are excluded by that same derivation. Payables are
deliberately absent: the condition is symmetric but dunning and paying are different
decisions.

`overdue_payable` is the receivable's mirror and shares its derivation: one rule answers
when an invoice is due on either side of the ledger, so the two can never disagree about
what "due" or "outstanding" means. It is easily confused with
`overdue_incoming_supplier_commitment`, which reports the same supplier being late with
goods rather than with money.

`sold_below_purchase_price` compares two figures somebody stated and computes neither: the
price on an agreed sales line, and the entry on the standing default purchase price list as it
stood when the sale was agreed. It exists because the assumption that margin needs a cost model
was wrong about this product — a purchase price list is a first-class concept and the price on
it is received rather than derived. It is not accounting margin: no freight, no duty, no
handling and no valuation of stock, so it understates, and it is silent altogether for a company
that keeps no purchase price list. Both of those are written into its own guidance rather than
left in a specification.

The two credit classes are the money half of a return, and there are two of them because two
different people act. A credit note recorded and never booked is bookkeeping that has not
happened; a booked credit nobody settled is money the company owes and has not moved.
`unmatched_financial_event` covers neither and must not be widened to — it walks postings that
moved cash, and a credit note moves none. `returned_not_credited` counts credit notes as
written rather than as paid, and its guidance now says so: seeing nothing there means the
paperwork exists, not that the customer has their money.

`credit_limit_exceeded` is the first class carried by a Party rather than by a transaction,
because the condition is about a relationship and the operator's next act is a decision about
the customer. It reads `party.credit_limit` as recorded and takes the outstanding amount from
the shared open-item derivation, so it can never disagree with the aging register or the
overdue classes. Three conventions bound it: a limit of zero means none is recorded rather
than a customer allowed to owe nothing, only invoices in the Party's own default currency
count because a limit is one number and converting would guess, and an amount equal to the
limit is allowed because that is what was agreed. A customer meant to be cash-only is
therefore silent here and belongs behind a delivery hold.

`duplicate_supplier_invoice` reports rather than refuses, which is the model's principle
rather than an oversight: Reality records what a source states and judges afterwards, and the
same invoice legitimately arrives twice when two connectors carry it. Refusing the second
would destroy the evidence that both arrived. It reads Documents rather than open items, so a
duplicate is visible before anyone posts or pays it, and it skips an invoice whose posting has
been reversed on both sides of the comparison — a withdrawn invoice cannot be paid twice, and
a supplier reissuing a corrected invoice under its original number is ordinary. Numbers are
compared with surrounding whitespace removed and case ignored; an empty number is neither
reported nor matched against.

A `return` Movement may name the customer delivery it reverses, and any movement may name the
return it settles, so a return is explainable at both ends. What happened to returned goods is
never stored as a label: it is whatever movement settled the return — a transfer back to stock,
a write-off, a shipment to the supplier — because a label could disagree with the movements it
summarises. A resolution must take the goods out of the location they came back to and may
never total more than came back, which is what makes the link mean something.

Four classes now learn their expectation rather than being told it, and they do not share a
statistic. `silent_source` uses the longest pause a source has shown, because a source's
pauses are bounded by nights and weekends. `order_stalled` and `receipt_unbilled` use the
median of the most recent twenty finished cases, because a fulfilment or billing lag has no
upper bound and one eight-month case would otherwise silence the class permanently. All three
share the shape: a multiple of what this tenant has actually done, an absolute floor beneath
which nothing is reported however fast the tenant is, and a minimum history below which no
expectation is claimed at all. Nothing is stored, so a norm is a description of the business
rather than a setting with a life of its own — which also means an entry can clear because the
business got slower rather than because anything happened, and the guidance says so.

`order_stalled` closes the largest blind spot in consumer trade. Every other delivery class is
anchored to `due_at`, so a webshop order that states no date, is reserved in full and is then
never picked was reportable by nothing at any age. Taking only undated promises keeps it
disjoint from `overdue_outgoing_customer_commitment` by construction rather than by
precedence. `receipt_unbilled` reverses a deliberate non-goal of Spec 076 — a supplier invoice
after the goods is the usual sequence — by adding the only thing that was missing, which is
time.

`silent_source` is the only class whose expectation is learned rather than stated. It reads
the receipt times of a capability's own recent records, takes the longest pause that
capability has shown, and reports a silence longer than twice that pause, never below an
absolute floor of a day. The four constants behind that judgement — twenty records of
history, five as the minimum before any rhythm is claimed, the multiple of two, and the
floor — are product decisions identical for every tenant, recorded in Spec 072 rather than
exposed as settings. A capability that has never delivered is deliberately outside the
class: that is "never started" rather than "stopped", and it would light up every tenant on
the day it was connected.

The three line classes are the only ones that read an edge rather than a record: an
invoice line names the order line it bills, and `null` there means the line bills nothing
an order promised — freight, a service, a rounding line — rather than "unknown". That
reading is what lets `shipped_not_billed` conclude from an absence, and it holds only while
every order-billing line sets the reference.

All three consider only order lines that carry a Commitment, so a line that promised no
delivery is never reported for failing to arrive, and all three compare quantities as
recorded: a pair in different units is skipped rather than converted, because a converted
figure would be a guess and an unconverted one would be wrong. `shipped_not_billed` and
`billed_not_received` are the same comparison on opposite sides of the business; the other
two cells of that square — an invoice ahead of the goods on the sales side, goods ahead of
the invoice on the purchase side — are ordinary and are deliberately not reported.
`billed_not_received` is easily confused with `overdue_incoming_supplier_commitment`, which
reports a supplier late with goods it has not yet billed, and with `overdue_payable`, which
reports the same supplier invoice unpaid rather than unmatched.

The two return classes complete the line's life. A `return` Movement may name the
customer-delivery Commitment it reverses, which is what makes them derivable at all; before
that a return could only be recorded orphaned, and every one produced an unexplained movement
while the goods it brought back were still counted as delivered and unbilled.

A return never changes fulfilment. The promise was kept when the goods went out, and
subtracting returns there would reopen a kept promise as overdue and make a fully returned
order look undelivered. What returns do change is the quantity the customer kept, which is
what `shipped_not_billed` measures and what the two return classes compare against crediting.
Only goods somebody was charged for can need crediting, so a return of something no invoice
line billed is never reported. Crediting without any return is not reported either: telling a
customer to keep an item is a decision rather than a discrepancy.

Whether two quantities can be compared at all is one decision, in one place, used by every
class that asks. Two figures in the same unit are comparable. Two in different units are
comparable only where the Item states the relation between its own stock unit and its own
purchase unit — a `purchase_unit` and a `conversion_factor`, "we buy this in boxes of twelve",
written down by the company — and only where the conversion is exact. The conversion happens at
read time and stores nothing, which is why it is an observation over received values rather
than a recomputation of one. Lines recorded in one unit are added up before being converted,
because what is compared is the total carried against the agreement rather than each invoice on
its own.

Prices are never converted, and that is a rule rather than an omission. A price per box divided
by twelve is a money figure nobody agreed, and where it does not divide evenly it is exactly the
rounding this product exists to avoid. `invoice_price_differs` therefore keeps a deliberately
narrower rule: units equal, or no comparison.

`units_not_comparable` is what a decline looks like when it is said out loud. Every decline was
the right answer and every one of them was silent, and silence there cannot be told apart from
nothing being wrong. It reports one entry per Item — the missing statement belongs to the item
and so does the fix — and says which of two things is wrong, because their exits differ: no
conversion is stated, or one is stated and does not divide evenly. A price left uncompared for
units is not reported, because no statement anybody could make would resolve it. The class is
loud on a tenant that has never maintained conversion factors; that is the condition being
reported, and its volume is bounded by items rather than by lines.

A restocking fee, a damage deduction or a write-off has one shape: **credit the goods that came
back, and charge for what is being kept.** The charge line names no order line, because it is not
credit for goods, and `returned_not_credited` counts only lines that name the order line — so the
return clears and the customer still receives the reduced amount.

Recorded the other way, as a credit note for fewer units than came back, the document says
exactly that: the remainder is uncredited, the class reports it, and nothing will ever clear it.
That entry is a true statement about the tenant's own document rather than a defect, which is why
the remedy is guidance rather than a rule — Reality cannot know that a credit note for eight was
meant as ten credited and two charged.

Both recordings are pinned by one test, deliberately. The second is the one at risk: it is
correct, it looks exactly like a bug report titled "false entry on restocking fees", and removing
it would be the wrong fix.

Returns now run in both directions, and the four classes over them share one body. A customer
sends goods back and the company credits them; the company sends goods back to a supplier and the
supplier credits them. The body takes three parameters — which promise it walks, which movement
kind reverses it, which document credits it — so neither side can drift in what "returned" and
"credited" mean, and neither can quietly start reading the other's documents.

Both over-credited classes wait for a return before saying anything. On the selling side that is
because telling a customer to keep an item is ordinary; on the buying side it is because a
rebate, an allowance or a price correction is an ordinary supplier credit with no goods behind
it, and reporting one would flag every quarter-end agreement a company makes.

One shipped class changed with this: `receipt_unbilled` counts what the company still holds
rather than everything that once arrived, because it should not accrue an invoice for goods it
sent back. That is the same correction spec 079 made to `shipped_not_billed`.

`billed_not_received` deliberately did **not** change. The goods arrived; netting returns off
there would report a supplier as having failed to deliver something it delivered. What the
supplier owes for returned goods is `supplier_return_not_credited`'s business, not that class's.
The two look inconsistent until you write down the question each one asks.

The two overdue classes judge a promise by **the date in force**, not by the date the promise was
made with. A supplier that acknowledged a later day is not late until that day passes, and a
company that agreed a later day with its customer is not late either.

On its own that would let a promise be moved for ever and never be late, so the entry says what
happened. Once the revised date has also passed, the entry carries the `promise_was_revised`
reason and its causal values name the day it was originally due and how many times it has moved.
Nothing is suppressed and no threshold was invented: a promise late against a date its own
counterparty chose is exactly as overdue as any other, and now it says so. Those extra values
appear only when the promise was in fact moved, so an entry for an unrevised promise is identical
to the one this queue produced before revisions existed.

**The blind spot is stated rather than hidden**: a supplier that moves the date repeatedly and
always beats the revised one is never reported. It is meeting the promises it actually made. A
company that agreed to the first date may see that differently, and Reality says nothing about
the difference — reporting it would need a number for how often a promise may move, and nobody
has measured one.

Stating a date for an order nobody dated moves it out of `order_stalled` and into the overdue
class, which is the one existing behaviour this changed.

Four classes now report the same idea: a document recorded and never booked. Recording evidence
and booking it into the ledger are two acts, and the distance between them is a business fact —
one this queue could report for credit notes since spec 084 and could not report for the document
both chains hang on until spec 092.

They are four rather than one because the owner and the money differ. A sales invoice nobody
booked hides money owed *to* the company and belongs to billing; a supplier invoice hides money
the company owes and belongs to accounts payable; the two credit classes are the same split for
credits. All four share one body, so none can drift in what "booked" means, and each judges a
document booked by **the account its own posting operation uses to refuse a second posting** —
so a class and its operation cannot disagree.

Each learns from its own document type alone. A company that books its sales invoices daily and
its supplier invoices at month end has two honest rhythms, and one judging the other would
accuse it of both. That is spec 080's rule and spec 089's correction, applied a third time.

The two invoice classes will be the first learned classes live on almost every tenant. Their
credit-note siblings are usually silent because credit notes are rare and the minimum history is
never reached; invoices are the opposite. If the learned constants are wrong — and they have
never been checked against a real business — this is where it will show first.

A document booked and then deliberately reversed is not reported by any of the four. The
reversing entries carry no document reference, so the original still reads as booked, which is
also the right answer: unbooking something on purpose is not the same as never getting round to
it.

The two credit classes have mirrors on the buying side. `supplier_credit_unposted` and
`supplier_credit_unclaimed` report a credit a supplier sent and nobody booked, and a booked one
nobody has netted or asked for. The conditions look identical to their mirrors and the jobs are
not: a credit the company owes is settled by its own accounts receivable, and a credit a supplier
owes is claimed from that supplier by accounts payable. One row for two jobs would be a worklist
nobody owns.

The two sides share the learned rule for "never booked" and deliberately share no history.
Booking a credit the company wrote itself is one process; booking one somebody else sent is
another, with a different owner, and one rhythm must not judge the other. `_credit_notes`,
`_credit_is_posted` and `_credit_posting_threshold` each take the document type and control
account they are asking about, so neither side can silently start reading the other's documents
— and a test asserts that separation rather than leaving it to be read.

When spec 089 shipped, `supplier_credit_unclaimed` carried a limitation: a return to a supplier
could not be recorded at all, so a credit for goods that went back was money with no evidence of
the goods behind it. Spec 090 closed that.

An early-payment discount is two figures a company states on its own payment term: a rate and a
number of days. Where a term states them, the discount deadline is placed by the same rule that
places the due date, in the same aging register, so the queue and the register cannot disagree
about when a window closes. `purchase_discount_available` reports every unpaid supplier invoice
whose deadline has not passed, soonest first.

**No discount amount is ever computed.** A rate applied to a gross amount is a division that
produces money nobody agreed, with a remainder to round, so the entry names the rate, the
deadline and the amount the ledger holds open, and never what the discount is worth. The same
rule governs the `early_payment_discount_taken` cause: instead of working out what the rate
allows and comparing against it, both sides are multiplied out — `remainder x 100 <= rate x
gross` — so nothing is divided and no reported figure depends on a rounding decision.

That cause is on `overdue_receivable` and `overdue_payable`, and it exists because those classes
were wrong. A customer who takes the discount it was offered pays short by design, and the
residue sat on the invoice reporting as an overdue debt for ever — one false entry per invoice,
on every business that grants a discount. The entry is not suppressed, because the remainder
genuinely is open; what was missing was a way to tell that customer from one who has not paid.
What is outstanding is a credit note recording the discount, not the money.

`purchase_discount_available` goes quiet in two very different ways: paying the invoice ends it,
and so does the deadline passing. Silence there means the discount was taken *or* lost, and only
the payment says which. There is deliberately no class for a discount already lost, because
nothing would clear it and every condition in this queue is one somebody can end.

Its guidance named its owner as "accounts payable, with whoever schedules the payment run" before
there was a payment run to schedule. There is one now, and it reads these invoices for the same
reason: the run's proposal includes every payable invoice whose window is still open, alongside
what is simply due. It names the rate and the deadline there too, and states no discounted amount
there either — the person running it states what to pay. See
[procure to pay](./procure_to_pay.md).

`announced_return_not_arrived` is the half of a return's life *before* the goods arrive, and the
first class whose authoritative record is a return announcement. It reports an open announcement
nothing has come back against, and it comes in two ways while remaining **one class**. Where the
customer named a day, that day is the measurement and nothing needs learning: past it, the entry
appears and says how many days late the parcel is. Where they named none, this company's own
rhythm decides, from the same learned rule as every other expectation here — the middle of the
most recent twenty announcements that did arrive, three times over, never sooner than a fortnight,
and silent below five. The entry says which of the two judged it, so an operator knows whether
they are looking at a promise the customer broke or a parcel that is simply slower than usual
here.

One class rather than two because it is one condition with one owner and one clearing path — the
goods arriving. Spec 080 split the dated and undated cases into two classes because an undated
*order* is a genuinely different operational situation from a late one; here the only difference
is how the date was arrived at, which belongs in the entry. The floor matches `return_unresolved`
on purpose: a fortnight for a parcel to travel is ordinary, and the two halves of a return's life
should not disagree about what ordinary means.

The learned lag is measured from when the customer announced it to when the goods actually
arrived, taken from the movement's own date rather than from when the status changed — otherwise
the rule would learn how fast this company types. A withdrawn announcement is not reported at all:
the customer has said the parcel is not coming, and there is nothing left for anybody to do. See
[movements](./movements.md).

`reservation_exceeds_stock` and `units_not_comparable` are the two classes whose authoritative
record is not a transaction. Reserving cannot over-allocate — the shared reserve operation allocates at
most the available quantity — so this class reports a reservation that lost its backing
afterwards, through an adjustment, a write-off, or a shipment on another promise. The
commitment-level classes cannot see that: the reservation still exists and still covers
the remaining quantity. Coverage is judged per Item across the tenant, so stock held in
another Location still counts. The explanation names every competing Reservation and
Commitment and blames none of them, because the model defines no allocation priority.

## Identity and Explanation

The stable derived identity is `exc__{class_id}__{authoritative_record_id}`. Explanation
re-derives the current tenant queue before returning causal values and the shortest
available Source → Evidence → Reality trace. Malformed, unknown, stale, resolved, and
foreign identities all produce the same not-found response.

The list contract preserves `severity`, `title`, `id`, and `impact` and also exposes
`class_id`, `cause_ids`, `record_type`, `record_id`, `causal_values`, and `trace`.

## Coverage Gate

`packages/reality-core/config/operational_exception_catalog.yaml` is the closed, ordered product
authority. Application catalog validation rejects class, cause, registry, metadata,
order, or executable-evidence drift. The catalog is trusted source-controlled metadata,
not business state or runtime authorization.

## The References The Queue Leans On

Four references on the queue's own records are nullable, meaningful and unenforced:
`DocumentLine.billed_document_line_id` (which order line an invoice or credit line bills),
`Movement.resolves_movement_id` (which return a movement settles),
`Movement.return_announcement_id` (which announcement goods fulfil) and
`Commitment.document_line_id` (which order line raised a promise).

Each is optional on purpose. A manual invoice for a service bills no order line, a transfer
settles no return, a promise can be raised without one. Making them required would refuse honest
records to protect a derivation, which is the wrong way round.

**Sixteen of thirty-two classes read one of them and eleven reason from one** — twenty-five
reference-and-class pairs. A missing reference does not make one thing go wrong; it makes two
opposite things go wrong.

**Six pairs cry wolf.** The class concludes from the reference being *absent*, so a missing one
reports work that was actually done. `shipped_not_billed` says ten pieces were never invoiced when
they were invoiced by a line that did not say so. The cost is a queue that stops being believed.

**Thirteen pairs go blind.** The class *starts* from the reference, so a missing one means it never
looks at the record. `billed_not_received` going quiet means a company is being billed for goods
that never arrived and nothing reports it. This is the direction worth losing sleep over, because
the class did not get it wrong — it never looked.

**The remaining six pairs only trace.** A class that puts a reference in the evidence it reports is
unharmed when it is absent.

Four classes are in both directions at once. `shipped_not_billed` cries wolf when an invoice line
does not say what it bills, and goes blind when the promise does not say which order line it came
from — the same class, two references, two opposite failures.

`config/reference_catalog.yaml` writes all of this down, and four gates keep it true. Each composes
one fact **discovered** from the mapper, the source or the command catalog with one fact a person
**declared**, and each fails in both directions, because a stale exemption hides the next real gap:

- every nullable reference on those four records is classified load-bearing or trace-only;
- the classes declared to read a load-bearing reference are exactly those whose derivations do;
- every place that builds one of those records passes the reference, or is exempt with a reason;
- every adapter of a command that builds one can carry the reference, and the shared input glossary
  describes it.

The reading — cries wolf, goes blind, only traces — is the one thing **only a person can say**.
Discovery proves which classes read a reference; it cannot tell a conclusion from a mention,
because both are the same attribute access.

**A gate cannot make a person type.** Every path can carry the reference and nobody is forced to
set one. What the gates buy is that the next writing path and the next surface cannot silently
lack the ability — which is how the field ends up unset in practice. On their first run they found
two such gaps: the MCP schema declared invoice lines as a free-form object and so never named the
reference, and the web app's manual document form had no box for it at all. A passthrough is a
capability for a person and an absence for an agent, which is why an MCP schema may never be
exempted for forwarding.

## A Hold Nobody Lifted

A hold is how somebody says *I am dealing with this*. `hold_commitment` stops one promise from
being executed; `hold_party_delivery` stops every shipment to a customer. Neither changes or
deletes what it holds — that is the point of them.

Until spec 107, **nothing in the queue watched them.** There was a hold register a person could go
and read, and nothing that ever told anybody to.

What makes a forgotten hold worse than untidy is the second-order effect. `close_stale_promises`
skips held promises on purpose — a sweep must not close something out from under the person
handling it — and **that protection has no expiry.** A hold raised for a credit check somebody
finished a year ago goes on shielding its promise from the only operation that could close it.

`commitment_hold_unreleased` and `party_hold_unreleased` report a hold standing longer than this
company's own rhythm for lifting one. Two classes because a class carries one record type and these
are two records; one derivation body serves both, and **each learns from its own population**,
because a promise hold and a customer delivery hold are different processes with different people
behind them. The floor is a week: a hold is an active statement that somebody is on it, so a few
days is ordinary.

The party hold is **high** and the promise hold **normal**, because their blast radii differ. A
forgotten promise hold blocks one promise. A forgotten party hold refuses **every** shipment to
that customer, including orders taken after it was raised by people who never knew about it.

Each entry says what the hold is holding back, which is what makes the class useful rather than
decorative — a hold on nothing is a formality somebody forgot, a hold on a real backlog is money
standing still. A promise hold reports the quantity still open, in that promise's own unit. A party
hold reports the **number** of open customer deliveries it blocks — a count and never a summed
quantity, because quantities across different items do not add up. A hold blocking nothing is
still reported, because it will refuse the next order too.

Every party hold type is reported and named rather than filtered to the one that exists today,
which means a new hold type must arrive with its own way of being lifted.

**Nothing is released and nothing is suppressed by these classes.** A held promise appears exactly
as it did, because a hold says somebody is dealing with it and not that it is fine.

A hold on a promise that is no longer open is not reported, and since spec 108 that is a legacy
situation rather than an ordinary one: cancelling a promise releases its holds, and so does a
revision that settles one as fulfilled, so **a promise that is not open no longer carries an active
hold**. The skip stays for tenants that were running before then, whose older rows nothing tidies.
That release is not the automatic release this class refuses — spec 107 refuses lifting a hold
because *time passed*; spec 108 lifts one because its *subject is gone*. See
[commitment holds](./commitment_holds.md).

## Stock Past Its Date, And The Horizon That Is Not There

`stock_expired` reports every lot whose stated best-before has passed and which still has stock on
hand. Two measurements, both real: the date somebody read off the goods, and the day the queue is
asked. The quantity held comes from the same tracked-identity stock rule the inventory register
uses, so the two can never disagree. Oldest expiry first. A lot with nothing left is not reported —
nothing is held, so there is nothing for anybody to do — and a lot with no stated date says nothing
in either direction.

The `reserved_for_delivery` reason says a customer is waiting for that stock, which is a different
urgency on the same record with the same owner and the same clearing path: that is what a cause is
for, and it is why this is one class rather than two. Releasing the reservation removes the reason
and leaves the entry, because the stock is still expired.

**There is deliberately no entry for stock that is about to expire**, and the reason is worth
stating plainly because it is the report most people would ask for first. It needs a horizon, and
no horizon exists on stated ground: nothing on an item states a shelf life and no term states a
minimum remaining life. The one mechanism that could produce a number is the learned-expectation
rule, which already governs **ten of this catalog's classes** on figures nobody has checked against
a real business. An eleventh would grow the largest standing risk here to buy a threshold nobody
could defend. What would unblock it is a customer's stated minimum remaining life, or a measured
turnover from a real business — a received or measured figure rather than an invented one.

So this class reduces surprise rather than preventing loss, and says so. Nothing is blocked: a
picker can still ship expired stock and the entry reports it afterwards. See
[inventory](./inventory.md).

