# Implementation Plan: Over-Billing and Quantity Lowered Below Delivered

**Branch**: `313-billing-deviations` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

- One new derived exception class, `shipped_beyond_order`, over customer promises. It reports the shipped quantity net of customer returns beyond the quantity in force.
- A05 is proven with a reviewed revision. E07 is proven with the existing *Invoiced and not shipped*, *Shipped and not billed* and *Invoice price differs* classes.
- No schema, no new tool.

## Technical Context

**Language/Version**: Python 3.12

**Storage**: none new

**Testing**:
- class tests with positive controls;
- the exception, revision and billing suites as regression;
- stories and the full suite.

**Constraints**:
- derived at read time;
- tenant-scoped;
- unchanged results where nothing is shipped beyond.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Read from promises, revisions and movements. |
| II. Reality is the operational authority | PASS | No document status. |
| III. Proven schema only | PASS | No schema. |
| IV. Tenant and service boundaries | PASS | One derivation in the shared registry. |
| V. Specification and test evidence | PASS | Tests planned first. |
| VI. Explainable Web product | PASS | The finding names the order, the shipped, the in-force and the excess quantity. |
| VII. Simplicity and storage discipline | PASS | One class. |
| VIII. Received values are recorded, never recomputed | PASS | The revision is kept as stated. |

## Design

1. **Derivation:** `_shipped_beyond_order_exceptions` in `services/exceptions.py`.
   - It runs over `_order_line_promises(..., "customer_delivery")` for promises that are not cancelled.
   - shipped = shipments − customer returns on the promise; excess = shipped − quantity in force.
   - It reports when the excess is above 0. The causal values are shipped, in force, ordered and excess, in the promise's unit.
2. **Catalogs:**
   - the class order and registry;
   - `catalogs.OPERATIONAL_EXCEPTION_CLASS_ORDER`;
   - `operational_exception_catalog.yaml`;
   - `reference_catalog.yaml`;
   - resource catalog exceptions and German label;
   - pinned class lists and counts;
   - the label and clears-through translations.
3. **Stories and Guide:** A05 and E07, then the promotion, coverage, roadmap and matrix.

## Rollback

Removing the class removes the finding; nothing is stored.
