# Implementation Plan: Unconfirmed Purchase Orders

**Branch**: `346-unconfirmed-purchase-orders` | **Spec**: [spec.md](spec.md)

## Summary

A new operational exception class `purchase_order_unconfirmed` over the purchase-line promises
(`_order_line_promises`): an open line with no `CommitmentRevision` stated by the reading moment
and no receipt is reported `CONFIRMATION_EXPECTED_WITHIN` (three days) after its order was
placed. Two set-based reads (revisions, receipts) cover all candidate lines.

## Constitution Check

- No document status (II): the verdict is derived from revisions and movements.
- No new typed field or table (III): the confirmation is the existing revision.
- Stated values are kept as stated (VIII); the finding is derived at read time.
- Tenant scope on every read.

## Clock

The class ages from the order time. It is not a dated candidate in `next_clock_moment`; the
catalog's idle floor bounds its lateness to a day, as for the other age-based classes.

## Gates

`CLASS_ORDER`, `DERIVATION_REGISTRY`, `OPERATIONAL_EXCEPTION_CLASS_ORDER`, the exception
catalog, the reference catalog consumer and its pinned counts, resource catalog exceptions and
German label, translations, `WITHOUT_A_SCENARIO` in the clock probe, coverage tests, generated
docs.
