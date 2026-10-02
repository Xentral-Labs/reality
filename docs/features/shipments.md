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

Customer dispatch review and execution also call the canonical fulfillment-readiness service.
The review snapshot contains blocker codes, stated required/received/remaining payment amounts
and opaque evidence IDs, so any relevant allocation, reversal or hold change invalidates the old
review token. A blocked review creates no Shipment, Package or Movement. Deterministic handler
refusals with a rolled-back transaction become terminal `failed` proposals with a no-effect
receipt; only an outcome that cannot be proven remains `executing` for reconciliation.

The MCP `shipment_dispatch_propose` and `shipment_receive_propose` input schemas are
purpose-discriminated closed contracts. Their four branches publish the allowed purpose,
compatible Movement type, required counterparty and movement fields, and reject unknown fields.

The shared register filters before pagination by direction, purpose, counterparty, recorded date,
carrier, tracking text and a derived observation. Detail accepts a Shipment or Package opaque ID
and returns effective Movement contents, current and superseded event history, derived times,
promised/physical/external quantity boundaries and warehouse-versus-carrier discrepancies. An
announced quantity remains unknown unless a typed operational record states it; source payload
fields are never promoted or recomputed merely to fill the display.

Sales and Purchasing label promises as Commitments and actual consignments as Shipments. Sales
selects outbound customer shipments; Purchasing selects inbound supplier shipments.

## Delivery rules (spec 306)

A customer, or one order, can state how it is delivered, with a reason:
- **Partial allowed** is the default.
- **Ship complete** means the whole order goes in one shipment.
- **No backorders** means what does not ship with the first shipment is cancelled rather than delivered later.

An order's rule wins over its customer's. Every statement is a version of the subject's source stream, and the `delivery_rule` row names the version in force.

**Ship complete:**
- Readiness adds `ship_complete_incomplete` while any open line of the order cannot ship its whole open quantity.
- Every person-facing shipment path refuses a shipment that leaves an open line behind (`shipment_ship_complete_partial`): the reviewed tool and its execution, the movement endpoint, the CLI and packaged dispatch. Importers recording what a source states are not refused.
- Order waiting for completeness names orders whose ready lines wait only because of the rule. Stating partial allowed for that one order lifts the rule.

**No backorders:** Backorder against the customer's rule reports each open rest once part of the order has shipped. The reviewed cancellation with the rule as its reason clears it; nothing is cancelled by itself.
