# Implementation Plan: Reservations Waiting for an Unpaid Prepayment

**Branch**: `348-prepayment-reservations` | **Spec**: [spec.md](spec.md)

## Summary

`services/prepayment_reservations.py` reads, in one grouped query, the open customer promises of
prepayment orders with active reservations and the oldest reservation time, keeping those past
`PREPAYMENT_RESERVATION_FLOOR` (seven days). For each such order it asks the shared readiness
decision once (spec 275) and keeps the promises whose remaining prepayment is positive and not
ambiguous. `exceptions._reservation_awaiting_prepayment_exceptions` turns them into the class
`reservation_awaiting_prepayment`.

## Constitution Check

- No document status (II); derived at read time, never stored (XI).
- No typed field or table (III); no migration.
- Stated amounts are read, not recomputed (VIII); the unpaid amount is readiness' remainder.
- Tenant-scoped reads only; nothing is released, so no new mutation.

## Cost

One grouped query over active reservations, then one readiness read per waiting order (not per
line or reservation), and only for orders already past the floor.

## Gates

CLASS_ORDER, DERIVATION_REGISTRY, `catalogs.OPERATIONAL_EXCEPTION_CLASS_ORDER`, the exception
catalog, resource catalog (order resource and the reserve step, German label), translations of
label and clearing text, pinned class lists and the CLASS_ORDER count.
