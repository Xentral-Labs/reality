# Implementation Plan: Credit Limit and Orders in Another Currency

**Branch**: `341-credit-limit-currency` | **Spec**: [spec.md](spec.md)

## Summary

`hold_if_over_credit_limit` (spec 298) returned early for an order in another currency than the
customer's. It now reads the exposure and, when the order still has something to invoice (it is
listed among the amounts not counted), places the ordinary credit hold with a currency reason.
The hold placement is shared with the over-limit case through one private helper. A line assigned
later to a held order copies the order's hold reason instead of recomputing an over-limit note.

## Constitution Check

- Stated values are never recomputed (VIII): nothing is converted; the reason names both currencies.
- No document status; the hold is the existing `commitment_hold` record (II).
- No new typed field or table (III); tenant scope unchanged.
- Mutations stay reviewed: release is the existing owner-only reviewed action.

## Tests

Service tests in `tests/test_credit_hold.py` replace the test that pinned the unchecked order.
