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

It is written only for a receipt, shipment or return without a commitment whose stated reason is not blank. Relationship: movement ← change record, which is the decision that recorded it. No field is added to movements or documents.

## New derived observation: `order_line_price_missing`

- Read at derivation time from sales-order lines that have a null `unit_price` and belong to a document with a source record.
- Record type: `document_line`.
- Causal values: the order number, the line's stated SKU and quantity, and the source record.
- Nothing is stored.

## New refusal codes

- `source_line_quantity_missing`: a source order line states no positive quantity.
- `billable_position_price_missing`: a billing proposal names a position without a stated price.
