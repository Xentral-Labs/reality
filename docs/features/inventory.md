# Feature: Inventory

## Calculations

- Physical = movements into location minus movements out of location.
- Reserved = active reservations at that location.
- Available = physical minus reserved.
- Incoming = open quantity on supplier commitments for that location.
- Projected = available plus incoming.

Calculations are tenant-, item-, and location-scoped and use Decimal values. Transfers
have both source and destination. Adjustments require a reason/source trail. There is
no authoritative stock-balance column.

## Acceptance stories

1. Stock reconciles exactly to movements for every item/location.
2. Released and consumed reservations do not reduce availability.
3. Commitments and movements from a second tenant never affect a result.

## A Lot Can Expire

A lot carries the best-before date somebody read off the goods or off the delivery note, as a
**calendar day**. Until spec 109 nothing in the schema could hold it — a lot had an item, a number
and where it came from — so expired stock looked exactly like good stock: it counted as available,
it could be reserved, it could be picked and shipped, and the first person to learn otherwise was
the customer.

**The date is never computed.** A shelf life in days multiplied out from a production date would be
a date nobody stated, and a batch that left the factory late would carry a figure nobody printed.
It is a calendar day rather than an instant because a best-before has no time of day, and inventing
one would be inventing precision.

The date is statable when the lot is created and once afterwards, because goods arrive before
anybody reads the label. **Re-stating a different date is refused**: a best-before read off the
goods is a received value, and two dates for one lot means one of them is wrong in a way this
product cannot adjudicate. Re-stating the same date is accepted and changes nothing, so a retry is
safe. The refusal names the correction, because a refusal without a way forward is how a typo stays
stuck.

### Correcting a misread date

`correct_lot_expiry` records that the stated date was read wrong and what it says instead. This is
a **correction**, not a restatement, and the difference decides the shape: a counterparty moving a
delivery date is the world moving, which is why that keeps every statement, while a best-before is
printed on a box and does not move. A second date means the first reading was wrong, and keeping
both as equally valid statements would record a contradiction as though it were history. So the
value is corrected in place and the audit goes in a `lot.expiry_corrected` event carrying the
before, the after and the reason — the way a manual document's line correction already carries its
own.

A correction costs two things. **A reason**, because this is somebody saying the record was wrong
and the reason is the only part of that a later reader can use. And **the date they believe is
stored**, including naming that none is: an operation that overwrites what a person got wrong must
not be reachable by somebody who has not looked at it, which is the same argument behind the
confirmed count of a stale closure, the confirmed total of a payment run and the expected revision
of a document correction. A correction that would change nothing is refused.

A correction may set the date to **nothing** — a date read off the wrong label, on an item with no
shelf life, can only honestly be fixed by saying the lot has no date. The cost is stated rather
than hidden: afterwards the record looks exactly like a lot nobody ever dated, and the event
history is the only place that distinction survives.

Reality judges neither reading. It cannot know which label was misread; it records that somebody
says the first one was wrong. `stock_expired` derives from the stated date per read, so a
correction moves what the queue reports on the next read with nothing stored.

A lot with **no** stated date says nothing in either direction. There is no way to tell an item
with no shelf life from one whose label nobody read, and inventing that distinction would be worse
than the silence.

**Nothing is blocked, chosen or released.** Expired stock can still be reserved and still be
shipped: refusing the movement would stop a company recording something that already happened — the
customer has the goods either way — and choosing which lot ships is an allocation policy this
product has never had. First-expiring-first-out is a policy, not a record.

`stock_expired` reports every lot past its stated date that still has stock on hand, counted
through the same tracked-identity stock rule the inventory register uses, with a
`reserved_for_delivery` reason when a customer is waiting for it. See
[operational exceptions](./operational_exceptions.md).

