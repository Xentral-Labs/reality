# Implementation Plan: Releasing a Partly Prepaid Order

**Branch**: `347-prepayment-release` | **Spec**: [spec.md](spec.md)

## Summary

`fulfillment_readiness` computes the prepayment gate per promise. After it finds the payment
blockers, it reads the newest `prepayment_release` of the order that covers the order's stated
gross amount (`covering_prepayment_release`) and drops `prepayment_required` and
`prepayment_invoice_missing`; the readiness names the release. Every shipping route, the
fulfillment queue and the delivery case read this one decision.

A new reviewed tool, `prepayment_release`, mirrors `credit_hold_release` (spec 298): preview with
refusals, a review token that pins the order and the amount, owner-only confirmation through the
proposal decision policy, an append-only row and an `order.prepayment_released` event on the order
(document subject, so projections narrow by the order).

**Storage**: migration `0136_prepayment_releases`, one table `prepayment_release`.

## Constitution Check

- Source → Evidence → Reality: the release is a decision record; it never changes the invoice,
  payment or document.
- No document status (II); readiness derives from the release at read time.
- Typed table justified (III): readiness reads it for every prepayment order.
- Tenant scope on the table, its FK and every query; the tool is in the isolation catalog.
- Mutations are reviewed; an owner confirms (confirmation required).

## Surfaces

MCP `prepayment_release_propose`, CLI `prepayment-release-propose`, the shared delivery-action
route, and a "Release prepayment" button on the delivery case for owners.

## Tests

Service tests in `tests/test_prepayment_release.py`; the R01 story in
`tests/scenarios/test_catalog_finance.py`.
