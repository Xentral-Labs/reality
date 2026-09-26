# Contract: Shipment Proposal Schemas

`shipment_dispatch_propose` is a discriminated union:

- `customer_delivery` requires customer `counterparty_id` and one or more `shipment` movements.
- `supplier_return` requires supplier `counterparty_id` and one or more `supplier_return` movements.

`shipment_receive_propose` is a discriminated union:

- `supplier_delivery` requires supplier `counterparty_id` and one or more `receipt` movements.
- `customer_return` requires customer `counterparty_id` and one or more `return` movements.

Every branch publishes:

- `purpose` as a branch constant;
- `counterparty_id`;
- `movements` with at least one item;
- movement `movement_type` as the purpose-compatible constant;
- movement `item_id` and positive decimal-string `quantity`;
- optional location, commitment, handling-unit, lot, serial-unit and reason fields valid for that
  branch; and
- optional carrier, tracking, source and occurrence-time fields.

Both the top-level object and nested movements reject unknown fields. Runtime validation and the
published MCP schema use the same purpose/movement vocabulary. Capability description accepts the
canonical public proposal names and points to readiness and shipment verification reads.
