# Data Model: Journey Proof Stories, Round Three

## Changed: `document_line.unit_price`

| Field | Before | After | Why |
|---|---|---|---|
| `unit_price` | `NUMERIC(18,4) NOT NULL DEFAULT 0` | `NUMERIC(18,4) NULL` | Null states that the source gave no price (FR-006, DR-002). Every other path states a price, as today. |

The downgrade refuses while any line has a null price.

## Reused: change record `movement_reason_stated`

Stored in the existing `action` table (`ChangeProposal`). It has the same shape as `inventory_adjusted`:

- `type`: `movement_reason_stated`
- `input`: `{"reason": "<stated reason>"}`
- `output`: `{"movement_id": "<movement id>"}`

It is written only for a receipt without a commitment whose stated reason is not blank, and carried to a correction's replacement. Relationship: movement ← change record, which is the decision that recorded it. No field is added to movements or documents.

## New derived observation: `order_line_price_missing`

- Read at derivation time from sales-order lines that have a null `unit_price`, belong to a document with a source record, are billed by no sales invoice line and have no cancelled promise.
- Record type: `document_line`.
- Causal values: the order number, the line's stated SKU and quantity, and the source record.
- Nothing is stored.

## New refusal codes

- `manual_line_unit_price_missing`: a person entering a line gave an explicit null price; 0 states a free line.
- `source_line_quantity_missing`: a source order line states no quantity. A zero or negative quantity keeps its existing code, `master_data_field_not_positive`.

Billing needs no refusal: billable positions carry the order line's price through, so an unpriced position is offered with no price, and an invoice recorded from it states the gross amount the person gives and no unit price.
