# Feature: Customer delivery holds

## Goal

Temporarily block physical delivery to a customer without blocking order entry,
reservation, purchasing, invoicing, or payment processing.

## Model and behavior

PartyHold links directly to Party. V0 supports `hold_type=delivery` and retains
reason, note, creator, creation time, and release time for auditability.

An active delivery hold blocks only a `shipment` Movement linked to a
`customer_delivery` Commitment whose `to_party_id` is the held Party. Movements
without a Commitment cannot infer a customer and are unaffected. Existing
reservations remain active and new reservations are allowed.

The hold is active while `released_at` is empty. Web mutations require explicit
confirmation. CLI, API, and web call the same tenant-scoped services.

## A Hold Nobody Lifted

`party_hold_unreleased` reports a party hold standing longer than this company's own rhythm for
lifting them — a separate population from promise holds, because it is a different process. It is
**high** severity: while the hold stands, every shipment to that customer is refused when somebody
tries to record it, including orders taken after it was raised. The entry names the hold type, the
reason, who raised it and the **number** of open customer deliveries it blocks — a count and never
a summed quantity, since quantities across items do not add up. A hold blocking nothing is still
reported, because it will refuse the next order too. Every hold type is reported and named, so a
new type must arrive with its own way of being lifted. See
[operational exceptions](./operational_exceptions.md).
