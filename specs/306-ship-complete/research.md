# Research: Ship-Complete and No-Backorder Rules

## What exists

- **Readiness.** `fulfillment_readiness` derives blockers per customer promise: hold, party delivery hold, reservation, stock and prepayment. The fulfillment queue, the dispatch review and the shipment paths read it.
- **The payment gate.** `require_paid_prepayment` is the one gate every person-facing single shipment calls: the reviewed tool, its execution, the movement endpoint and the CLI. Packaged dispatch checks readiness per movement in `shipment_actions` and `shipments`. Importers do not come through these paths (spec 294 FR-006).
- **An order.** It is a `document` whose lines carry one customer promise each (`commitment.document_id`).
- **Customer settings.** They are typed columns on `party` (`payment_term_id`, `credit_limit`). A new column on `document` breaks eleven historical migration tests, a trap recorded in memory.

## Decisions

- **One append-only table, `delivery_rule`.** It holds a party or a document (exactly one), the rule, a reason, who stated it and when. Its history is the explanation. Lifting the rule for an order is a new statement of partial allowed for that order. No column on `party` or `document`.
- **Effective rule.** The latest statement for the order wins over the latest for its customer (the order's counterparty). Without either, partial allowed.
- **Completeness.** The whole order counts, over its open customer promises. A cancelled or fulfilled line counts as complete. A line is complete for shipping when its whole open quantity can ship: reserved, or physically available where it is shipped from, under the same rule the readiness stock check uses.
- **A shipment as a group.** Readiness sees one line at a time, so the shipment paths check the group: every open line of an order under ship complete must be in the same shipment with its whole open quantity.
- **No backorders.** Partial shipments stay allowed. Only after at least one shipment of the order does the open rest become a finding, and nothing is cancelled without a person.
- **Importers.** Not refused: a source stating that goods left is recorded as stated.
