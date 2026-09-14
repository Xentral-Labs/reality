# Quickstart: A Lot Can Expire

**Language**: English

Five tests in `tests/test_inventory_tracking_reservations.py` and four in the derivation suite. One
migration adding one nullable date.

## Story one — the date on the delivery note

A lot-tracked item and three lots: one with a best-before stated as a string, one with a date
object, one with nothing. The first two carry exactly what was stated. The third asserts nothing in
either direction, because an item with no shelf life and a label nobody read are indistinguishable.

A lot created before somebody read the label takes the date afterwards. **Re-stating a different
date is refused** — a received value is not adjusted — while re-stating the *same* date is accepted
and changes nothing, so a retry is safe. `best before summer` and `31.12.2026` are refused; the
same lot then takes an ISO day, so the refusal is the rule speaking and not the field being broken.

**Result**: passes.

## Story two — stock that cannot be sold

Six units of a lot whose best-before was eleven days ago. Reported as high, naming the stated date,
the eleven days, the six units held and the lot number. A lot still ahead of its date says nothing.
An expired lot with nothing left says nothing either — it appears in `expired_lots` and not in the
queue, which is the distinction between *expired* and *expired and still held*.

Writing the stock off with an adjustment ends the entry, with nothing stored. And nothing was
blocked on the way: a separate test reserves and ships expired stock successfully, because refusing
would stop a company recording what already happened.

Stock of one lot split across two locations is one quantity held, and each location's figure comes
from the same tracked-identity stock rule the inventory register uses.

**Result**: passes.

## Story three — about to be shipped

Expired stock with an active reservation naming its lot carries the `reserved_for_delivery` reason
and names how much is reserved. Releasing the reservation removes the reason and **leaves the
entry**, because the stock is still expired.

**Result**: passes.

## What the story taught

**The interesting part of this feature is the report that is not in it.** "Expiring in thirty days"
is what anybody would ask for first, and it needs a horizon that exists nowhere on stated ground:
nothing on an item states a shelf life, and no term states a minimum remaining life. The one
mechanism that could produce a number is the learned-expectation rule — which, measured rather than
guessed, already reaches **ten of the thirty-four classes** on figures nobody has checked against a
real business. Adding an eleventh to buy a threshold nobody could defend is the wrong trade, and
the specification names exactly what would unblock it: a customer's stated minimum remaining life,
or a measured turnover from a real tenant.

**Reporting what has actually expired costs nothing invented.** Two measurements, both real: the
date somebody stated and the day of the read.

**One cause instead of a second class.** Expired-and-reserved is the same record with the same
owner and the same clearing path; only the urgency differs, which is exactly what a cause is for.
Two classes would have meant two ids for one lot and an operator reconciling them.

**The first `Date` column in the schema.** Every other business date here is a string
(`document_date`, because a source may state a free-form period label) or a timestamp. A
best-before is neither — it is a calendar day, and a timestamp would invent a time of day nobody
stated. Being first is a novelty worth naming; it is still the honest type.

**Three test-only mistakes, each cheap.** `OperationalException` carries `impact`, not `summary`;
`reserve` returns a `ReservationResult` with one `reservation`, not a list; and there is no
`reservations` read on the service. All three were my assumptions about the API, all three surfaced
in seconds, and none of them was a bug in the product.

## What this deliberately does not do

**Nothing is blocked, chosen or released.** A picker can still ship expired stock. Refusing the
movement would stop a company recording something that already happened — the customer has the
goods either way — and first-expiring-first-out is an allocation policy this product has never had.
So this **reduces surprise rather than preventing loss**, and the catalog says so.

**A stated date cannot be corrected.** A typo is stuck until somebody builds the append-only
restatement Spec 093 built for promises. Silently overwriting a received value would be worse;
refusing at least makes the typo visible.

**Serial units carry no date.** A serial-tracked unit could have its own, and nothing asks for it
yet. Named rather than half-built.
