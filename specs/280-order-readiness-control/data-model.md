# Data Model: Order Readiness Control

No schema change.

- **Projection row**: existing order-level payload with `order_key`, `document_id`, party, due date,
  readiness, ship-ready flag, blockers and nested lines.
- **Line**: existing commitment identity, item/unit, open/fulfilled/reserved/shortage quantities,
  readiness/payment observations and blockers.
- **Metadata**: existing completed snapshot and pending-change description.

The UI stores none of these as authority.
