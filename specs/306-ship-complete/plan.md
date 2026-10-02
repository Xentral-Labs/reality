# Implementation Plan: Ship-Complete and No-Backorder Rules

**Branch**: `306-ship-complete` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

A person states a delivery rule for a customer or for one order: partial allowed, ship complete or no backorders. Each statement is an append-only `delivery_rule` row with its reason. The latest statement for the order wins; otherwise the latest for the customer applies; otherwise partial allowed.

**Ship complete (B10):**
- Readiness gains the blocker `ship_complete_incomplete`, naming the lines that cannot ship in full.
- Every person-facing shipment path refuses a shipment that leaves an open line of the order behind (`shipment_ship_complete_partial`).
- The class `order_waiting_for_completeness` reports orders that wait only because of the rule while some lines are ready. It offers to lift the rule for that order.

**No backorders (M06):**
- After a shipment, the class `backorder_against_rule` reports each open rest of the order.
- It offers the reviewed `commitment_cancel` with the rule as the reason.

See [research.md](research.md), [data-model.md](data-model.md) and [contracts/delivery-rules.md](contracts/delivery-rules.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Storage**: PostgreSQL; migration `0112_delivery_rule`

**Testing**:
- service, readiness, shipment-path, exception, adapter and story tests;
- the readiness, shipment, dispatch and exception suites as regression;
- web checks, browser fixtures and the full suite.

**Performance Goals**:
- Readiness reads the order's rule and its sibling lines once per order, not per line.
- The classes read rules for the company in one grouped query.

**Constraints**:
- unchanged results without rules;
- importers not refused;
- tenant-scoped;
- reviewed tools.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | A rule is a person's statement with its reason, linked to the customer or the order it is about. |
| II. Reality is the operational authority | PASS | No document status: whether an order is complete is read from its promises, stock and reservations; the rule is a stated term. |
| III. Proven schema only | PASS | Readiness, every shipment path and two classes filter and act on the effective rule. |
| IV. Tenant and service boundaries | PASS | Composite tenant FKs; one service path behind every adapter. |
| V. Specification and test evidence | PASS | Tests planned per phase, with positive controls. |
| VI. Explainable Web product | PASS | The blocker and both findings name the rule, who stated it, why, and the lines concerned. |
| VII. Simplicity and storage discipline | PASS | One append-only table. No column on `party` or `document`, which also avoids the historical-schema trap of a new `document` column. |
| VIII. Received values are recorded, never recomputed | PASS | Rules are kept as stated; completeness is derived at read time. |

## Design

1. **Schema and service:**
   - migration `0112`, the `DeliveryRule` model and `services/delivery_rules.py`;
   - `effective_delivery_rule(order)`, `state_delivery_rule`, `delivery_rules` (read with history);
   - the event `delivery_rule.stated` and the refusals.
2. **Readiness:**
   - in `fulfillment_readiness`, under ship complete, add `ship_complete_incomplete` while any open line of the order cannot ship its whole open quantity, or the proposed quantity is less than the line's open quantity;
   - the queue and projections pick it up through readiness.
3. **Shipment paths:** `require_delivery_rule(movements)` groups a shipment's movements by order. Under ship complete it refuses unless every open line of each order is carried in full. It is called beside `require_paid_prepayment` in:
   - the reviewed tool and its execution;
   - the movement endpoint;
   - the CLI;
   - the packaged dispatch review and execution.
4. **Classes:**
   - `order_waiting_for_completeness` (record: document): some lines ready, others not;
   - `backorder_against_rule` (record: commitment): an open rest after a shipment, under no backorders.

   Both get catalog entries, the reference catalog, resource catalog labels and invalidation.
5. **Adapters:**
   - tools `delivery_rule_set` (reviewed) and `delivery_rules` (read);
   - MCP propose and read;
   - Web `GET /delivery-rules` and `POST /delivery-rules/proposals`;
   - CLI `delivery-rule show|set`.
6. **Web:**
   - "Lieferregel" on the customer and the order, with its history and a change through the review;
   - the blocker label;
   - the two findings with their next steps;
   - translations.
7. **Stories and Guide:** B10 and M06 as business stories, then the promotion, coverage, roadmap, matrix and docs.

## Rollback

The downgrade refuses while rules exist. Without rules, readiness, shipments and findings read as before.

## Complexity Tracking

No Constitution violations.
