# Application Capability Contract

## Reads

`shipments_list` accepts page/size and optional query, direction, purpose, counterparty, date,
carrier and derived observation. It returns items, normalized scope, page and `observed_at`, with
filters before count/pagination.

`shipment_explain` accepts an opaque Shipment or Package ID and returns Shipment, Packages,
effective Movement contents, current/history events, derived observations, discrepancies and
shortest trace links. Foreign and unknown IDs are indistinguishable.

## Reviewed commands

- `shipment_notice_record`: Shipment/Package and stated notice/event; no Movement.
- `shipment_dispatch`: outgoing Package plus compatible customer shipment/supplier-return Movements.
- `shipment_receive`: incoming Package plus compatible supplier receipt/customer-return Movements.
- `shipment_event_record`: append attributed logistics event.
- `shipment_event_supersede`: append reasoned correction/retraction and optional replacement.

Each supports prepare, review, confirm, exact receipt and reconcile. Preparation has no effect;
confirmation binds all inputs and relevant current state. Receipts include replay/fingerprint and
all created IDs. Failure creates no partial effect.

## Adapter mapping

FastAPI DTOs, Typer arguments, MCP schemas, Chat guidance and Web forms translate these same
inputs/results. They may preselect purpose/direction but add no eligibility or derivation rules.
Reads execute directly; mutations cannot bypass confirmation.
