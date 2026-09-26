# Feature: Reservations

## Purpose

A reservation allocates physical stock at one location to one outgoing commitment.
Its shortest provenance link is `commitment_id`; document/source links are reached
through that commitment.

## V0 behavior

- Reserve up to currently available quantity and report any shortage explicitly.
- Support `active`, `released`, and `consumed` states.
- Releasing is idempotent and does not delete history.
- Shipping consumes active reservations at the shipment's own location up to the shipped
  quantity. Shipping from another location consumes nothing held elsewhere; what stays
  reserved there beyond the open quantity is released with cause
  `shipped_from_another_location`, keeping the remainder.
- Availability equals physical stock minus active reservations.
- A confirmed downward commitment revision releases homogeneous excess and retains the exact
  smaller allocation. Different locations or tracking identities require an explicit retained
  allocation decision rather than an automatic choice.

## Invariants

- Commitment, item, and location must belong to the same tenant.
- Reservations are allowed only for outgoing customer commitments.
- Quantity is positive and uses Decimal application values.
- Total active reservation may not exceed the commitment's open quantity.
- A reservation holds stock at exactly one place, so a place scope partitions the
  active reservations completely (spec 262).

## Acceptance stories

1. With 20 on hand for a promise of 30, reserving 30 allocates 20 and reports 10 short.
2. Releasing a reservation restores availability without changing physical stock.
3. Shipping consumes the allocation and reduces physical stock through a Movement.

## Public proposal receipt

The MCP proposal and confirmation path uses the same reservation service as Web and CLI. A
confirmed receipt distinguishes command execution from business effect:

- `effect=none` means zero quantity was allocated, the complete request remains as shortage and
  no Reservation or `reservation.created` event exists;
- `effect=partial` means some quantity was allocated and `remaining_work` is the exact shortage;
- `effect=complete` means the requested quantity was allocated and `remaining_work` is zero.

Availability is evaluated only at the commitment's exact location. Stock in a parent, child or
sibling location is not silently aggregated. The receipt names `proposal_execution_status` for
lost-response reconciliation and current reservation/inventory reads for independent
verification. A technically executed proposal therefore never presents a zero allocation as a
successful business allocation.
