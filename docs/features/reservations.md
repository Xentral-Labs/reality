# Feature: Reservations

## Purpose

A reservation allocates physical stock at one location to one outgoing commitment.
Its shortest provenance link is `commitment_id`; document/source links are reached
through that commitment.

## V0 behavior

- Reserve up to currently available quantity and report any shortage explicitly.
- Support `active`, `released`, and `consumed` states.
- Releasing is idempotent and does not delete history.
- Shipping consumes active reservations up to the shipped quantity.
- Availability equals physical stock minus active reservations.

## Invariants

- Commitment, item, and location must belong to the same tenant.
- Reservations are allowed only for outgoing customer commitments.
- Quantity is positive and uses Decimal application values.
- Total active reservation may not exceed the commitment's open quantity.

## Acceptance stories

1. With 20 on hand for a promise of 30, reserving 30 allocates 20 and reports 10 short.
2. Releasing a reservation restores availability without changing physical stock.
3. Shipping consumes the allocation and reduces physical stock through a Movement.
