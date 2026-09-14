# Feature: Physical Shipments and Tracking

A Delivery Commitment states what a party owes. A Shipment records one real physical
consignment. Its Packages carry carrier and tracking references; linked Movements remain the
authority for goods that physically entered or left stock.

| Purpose | Direction | Compatible Movement | Counterparty |
| --- | --- | --- | --- |
| Customer delivery | Outbound | `shipment` | Customer |
| Supplier delivery | Inbound | `receipt` | Supplier |
| Customer return | Inbound | `return` | Customer |
| Supplier return | Outbound | `supplier_return` | Supplier |

A notice or carrier event never changes stock or fulfillment. `ShipmentEvent` records attributed
observations; `ShipmentEventSupersession` corrects one without deletion. The shortest content link
is `Movement.shipment_package_id`. Existing Movements are not backfilled into guessed Shipments.

Notice, dispatch, receive, event append and supersession use state-bound proposals, explicit
confirmation, replay-safe execution and reconciliation. CLI, HTTP, Web, MCP and Chat call the same
application tools. Reads are `shipments_list` and `shipment_explain`.

The shared register filters before pagination by direction, purpose, counterparty, recorded date,
carrier, tracking text and a derived observation. Detail accepts a Shipment or Package opaque ID
and returns effective Movement contents, current and superseded event history, derived times,
promised/physical/external quantity boundaries and warehouse-versus-carrier discrepancies. An
announced quantity remains unknown unless a typed operational record states it; source payload
fields are never promoted or recomputed merely to fill the display.

Sales and Purchasing label promises as Commitments and actual consignments as Shipments. Sales
selects outbound customer shipments; Purchasing selects inbound supplier shipments.
