# Contract: Delivery Rules

## `delivery_rule_set` (reviewed, mutating)

**Arguments:** exactly one of `party_id` and `document_id`, plus `rule` (`partial_allowed`, `ship_complete` or `no_backorders`) and `reason`.

**Review:** shows the subject, the rule in force now (and where it comes from), the rule after confirming, and the open orders it affects.

**Refusals:**
- `delivery_rule_subject_required`: neither or both subjects are given;
- `delivery_rule_unknown`;
- `delivery_rule_reason_required`;
- `delivery_rule_party_not_customer`;
- `delivery_rule_document_not_order`.

**Adapters:**
- MCP `delivery_rule_set_propose`;
- Web `POST /api/tenants/{t}/delivery-rules/proposals`;
- CLI `reality delivery-rule set (--party ID | --order ID) RULE --reason TEXT [--yes]`.

## `delivery_rules` (read)

**Arguments:** `party_id` or `document_id`.

**Returns:** the effective rule (`rule`, `source`: order, customer or default), the statement in force, and the history.

**Adapters:**
- MCP `delivery_rules`;
- Web `GET /api/tenants/{t}/delivery-rules?party_id=|document_id=`;
- CLI `reality delivery-rule show`.

## Readiness and shipments

- **Blocker** `ship_complete_incomplete`, linking the order. Order waiting for completeness names the ready and the waiting lines.
- **Refusal** `shipment_ship_complete_partial` on every person-facing shipment path, naming the order and how many open lines the shipment would leave behind.

## Classes

- `order_waiting_for_completeness`:
  - record: document;
  - next step: `delivery_rule_set_propose` with `partial_allowed` for the order.
- `backorder_against_rule`:
  - record: commitment;
  - next step: `commitment_cancel_propose` with the rule as the reason.
