# Contract: Purchasing in a Purchase Unit

## Purchase order (`order_create` with direction purchase, `create_manual_order`)

- **A line in `Item.purchase_unit`**: the promise is the line quantity × `conversion_factor`, in `Item.unit`. The line keeps the stated quantity and unit.
- **A line in `Item.unit`**: unchanged.
- **Refused**:
  - `purchase_unit_not_convertible`: another unit, or an item without a factor.

## Receipt (`record_movement`, reviewed `movement_create`, `shipment_receive`, Web receipt)

- **New optional argument `unit`.**
- **In `Item.purchase_unit`**: `quantity` is converted to `Item.unit`, and `stated_quantity` and `stated_unit` keep what was said. The open-quantity check runs on the converted quantity.
- **In `Item.unit` or omitted**: unchanged.
- **Refused**:
  - `movement_unit_not_convertible`: another unit.
  - The existing `movement_exceeds_commitment_open_quantity` still applies, in the stock unit.
- **Review**: shows the stated and the converted quantity.

## Reads

- **Delivery case and open-work rows** of a supplier promise state open and received in the stock unit, and in the purchase unit where the line is in it and the division is exact.
- **Movement inspector**: `5 box (60 pcs)`.

## Findings

- **`receipt_unbilled` / `billed_not_received`**: they compare in the stock unit for new purchase orders, and agree with stock.
- **`units_not_comparable`**: it names an open supplier promise in a purchase unit recorded before this feature, with the cause `promise_in_purchase_unit`.
