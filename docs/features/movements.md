# Feature: Movements

## Purpose

A movement is an observed physical change. Stock is always calculated from these
records; no mutable stock balance is authoritative.

## V0 behavior

- `opening_stock`, `receipt`, `shipment`, `transfer`, `return`, and `adjustment`.
- Receipt/return require a destination; shipment requires a source; transfer both.
- A receipt may fulfill a supplier commitment; a shipment may fulfill a customer
  commitment.
- Any movement may name the `return` it settles, and only a return: the goods must be the
  same item, must leave the location they came back to, and the settlements of one return may
  never total more than came back. A movement naming none settles none, which is a statement
  rather than a gap. What happened to the goods is what the settling movement is; no outcome
  is stored.
- A return disposition inherits the arrival Movement's applicable handling-unit, lot and serial
  identity. Callers do not restate it, so a balanced company total cannot hide movement or
  write-off of the wrong stock at location or identity level.
- Any movement may name the `return` it settles, and only a return: the goods must be the
  same item, must leave the location they came back to, and the settlements of one return may
  never total more than came back. A movement naming none settles none, which is a statement
  rather than a gap. What happened to the goods is what the settling movement is; no outcome
  is stored.
- A return may name the customer commitment it reverses, and only a customer one:
  goods going back to a supplier are the mirror flow. It never changes fulfilment,
  because the promise was kept when the goods went out, and it may not exceed what
  actually went out against that commitment. A return that names no commitment is
  still accepted and is reported as an unexplained movement.
- Adjustments carry an explicit reason in their immutable source/action evidence.
- A movement may reference one handling unit representing the physical pallet on
  which that quantity moved. The handling unit and its NVE/SSCC are optional.
- If one item quantity is split across pallets, each pallet has its own movement.
  Multiple item movements may reference the same pallet.
- Lot-tracked movements reference a tenant-scoped lot. Serial-tracked movements
  reference one serial unit and always carry quantity one. Reservations use the
  same optional pallet, lot, and serial dimensions as movements.
- Movements appear in the tenant timeline.
- A Movement may name one `ShipmentPackage`. Tracking observations never replace the Movement as
  stock or fulfillment authority.

## Invariants

- Quantity is positive; direction is expressed by movement type and locations.
- Item, locations, commitment, and source record are tenant-owned.
- A movement is never updated or deleted by normal application services.
- An incorrect movement is corrected by one tenant-scoped `MovementCorrection` relation
  connecting the immutable original, an exact positive-quantity `correction` Movement
  with swapped locations, and an optional normally validated replacement. The relation
  retains the reason, correction time, actor context, and semantic retry fingerprint.
- The correction Movement carries no duplicated Commitment or SourceRecord provenance;
  fulfilment reversal and original evidence are reached through the original Movement.
- A compensation cannot be corrected. A replacement is a normal Movement and may start
  its own later correction chain.
- A referenced handling unit belongs to the same tenant as the movement.
- Outbound movement cannot exceed physical stock in V0.

## Acceptance stories

1. Opening 20, receiving 10, and shipping 7 results in physical stock 23.
2. A transfer decreases one location and increases the other without changing total.
3. Partial receipts and shipments produce partial commitment fulfillment.
4. Correcting a receipt of 10 with a replacement of 7 preserves the complete chain and
   leaves net physical stock and applicable fulfilment at 7.

## Goods Going Back to a Supplier

`supplier_return` takes goods out of a location against the supplier delivery they arrived on.
It is its own kind rather than a `return` with the direction reversed, because the two are
opposite physical facts: a customer return brings goods in and this takes them out. A single
type inferring its direction from the commitment would stop a movement being a plain statement
about what happened.

What bounds it is what actually arrived against that delivery, less what has already gone back —
never the promise's open quantity. On a supplier delivery received in full that figure is zero,
which is exactly when a company is most likely to want to send something back. The customer side
is bounded the same way and for the same reason.

It does not change fulfilment. The supplier kept its word when the goods arrived, and sending
some back does not unmake that, exactly as a customer return does not reopen a delivery the
company kept.

It can settle a customer return. Spec 082 let a return name the movement that settles it and
listed "a shipment to the supplier" among the things that settle one; that movement did not
exist until now. The existing rules apply unchanged — the goods must leave the location the
return came back to, and settlements must not exceed what came back — so the most ordinary
resolution there is needed no new concept at all.

## A Return Announced Before It Arrives

A return is a Movement, so until spec 099 the only moment a company could record one was the
moment the goods were already on the receiving dock. Everything before that — *"I want to send
back two of the five lights from order 4711, they are the wrong colour"* — lived in somebody's
inbox.

`announce_customer_return` records it against the customer delivery the goods went out on: the
quantity, the reason, the reference the parcel will carry and the day the customer said it would
go, all exactly as stated. **Nothing is generated**, the reference least of all: a number this
product invented would become the number somebody has to tell the customer, and there is no way
to do that from here. A customer who names no day is not a customer promising *soon* — the
absence is the statement, and the queue judges the two differently.

How much may be announced is what the delivery can still return, less what other open
announcements already claim. Without that second term a customer could announce the same five
items twice and the desk would expect ten. It is one rule, `returnable_quantity`, and the
returning-movement path asks it too — the movement path became its caller rather than its owner.

When the parcel arrives, the movement can name the announcement it fulfils through a nullable
reference, exactly as a resolution names the return it settles. Matching by item and quantity was
considered and refused: two announcements against one delivery would make it a guess, and a guess
about which of a customer's returns arrived is worse than no link. The return **still names the
delivery it reverses** — that link bounds it and four classes read it, and the announcement is an
additional statement about the same event rather than a substitute.

Both references are stated through every adapter: the MCP tool `movement_create_propose`, the web
movement write, which also returns them on read and list, and the CLI's `movement record` flags.
The service refuses a foreign or closed announcement the same way whichever adapter named it.

The announcement is settled as fulfilled **at the moment** what has arrived reaches what was
announced, not at some later read, because there may be no later event. More arriving than was
announced is accepted within what the delivery allows: the customer said two and sent three, both
are true, and refusing would lose a movement that happened. A customer who changes their mind has
the announcement withdrawn, which keeps what they announced and returns what may be announced to
what the delivery allows.

**A record of its own rather than a third `Commitment.type`.** A Commitment is a directional
promise and a customer promising to send goods back is one, so that is the obvious home. It was
rejected on a measurement: `customer_delivery` is read in thirty-two places across eight modules,
seventeen of them a two-way branch whose `else` silently means *supplier delivery*. A third value
would make all seventeen wrong and most would keep passing their tests. If the commitment
vocabulary is ever widened deliberately, with those branches audited, this is the first table that
should be folded into it.

**An announced return is not supply.** Nothing here touches availability, replenishment or the
fulfilment queue, because goods a customer has promised to send are not goods anybody can sell,
and treating them as supply is how a warehouse commits stock that never arrives.

`announced_return_not_arrived` reports an open announcement nothing has come back against. See
[operational exceptions](./operational_exceptions.md).
