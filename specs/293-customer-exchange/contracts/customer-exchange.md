# Contract: Customer Exchange Tools

## `customer_exchange_record` (reviewed mutation)

Prepared through `prepare_delivery_action`; executed only with the review token and explicit
confirmation. Surfaces: Web (`POST /tenants/{tenant}/delivery-actions`), MCP/Chat
(`customer_exchange_propose`), CLI (`customer-exchange-propose`, `customer-exchange-confirm`).

Input (strict, no other fields):

| Field | Required | Meaning |
|---|---|---|
| `return_movement_id` | one of the two | received customer return to exchange |
| `return_announcement_id` | one of the two | open announcement to exchange in advance |
| `quantity` | yes | exchanged quantity of the returned item, positive |
| `replacement_item_id` | yes | item to send; may differ from the returned item |
| `replacement_quantity` | yes | quantity to send, positive |
| `location_id` | no | where the replacement ships from; default the returned delivery's location |
| `due_at` | no | promised date of the replacement |
| `reason` | yes | stated reason, not empty |

Review (`_delivery_review.effect`):

```json
{
  "returned_delivery_id": "com_…",
  "return": {"kind": "movement|announcement", "id": "…", "exchangeable": "1"},
  "exchanged_quantity": "1",
  "replacement": {"item_id": "itm_…", "quantity": "1", "location_id": "loc_…"},
  "money_moves": false,
  "creates": ["customer_exchange", "commitment"]
}
```

Receipt: `{"exchange_id", "replacement_commitment_id", "source_record_id"}`.
Verification: `verified` when the exchange and its replacement exist as reviewed.

Coded refusals:

| Code | When |
|---|---|
| `customer_exchange_fields_invalid` | unknown or missing fields, both or neither return side |
| `customer_exchange_return_not_customer` | the movement is not a customer return |
| `customer_exchange_return_unlinked` | the return names no delivery |
| `customer_exchange_announcement_not_open` | the announcement is fulfilled or withdrawn |
| `customer_exchange_exceeds_exchangeable` | quantity above what may still be exchanged |
| `customer_exchange_already_credited` | the returned quantity is fully credited |
| `customer_exchange_quantity_not_positive` | a quantity is zero or negative |
| `review_customer_exchange_changed` | the reviewed state changed before confirmation |

Event: `exchange.recorded`, subject `customer_exchange`, with the proposal as `action_id`.

## `customer_exchange` (read)

Input: `exchange_id`, or `return_movement_id`, or `replacement_commitment_id`.
Output: the exchange, the returned delivery, the return side, the replacement with its
fulfilled quantity, `settles` (exchanged and arrived quantity), `outstanding` (announced but
not arrived), and the decision (actor, time, reason). Confirmation: none; side effects: none.
