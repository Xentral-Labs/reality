# Research: Journey Proof Stories, Round Two

Code reading on 2026-09-29 against `origin/main` (`da66846a`). No story was run yet. Paths are
relative to `packages/reality-core/`.

## Per journey

| ID | Route | Expected | Condition or risk |
|---|---|---|---|
| D16 | `customer_exchange_record` against a return or an announcement, `reserve`, dispatch; `movement_explanation` | pass | No reviewed tool other than the exchange creates a document-less promise (`create_commitment` is service-only). The limitation names that a free replacement needs a return or an announcement; a lost parcel has no reviewed path. |
| G07 | purchase price list with tiers (`price_list_create`, `price_tier_create`, `party_price_list_assign`), purchase line with `price_list_entry_id`, guided `supplier_invoice_record`; second invoice via `document_create` | pass with limitation | `_validate_selected_price_entry` makes the tier price the line price. The guided supplier invoice copies the line price and states only gross, so it can never raise `invoice_price_differs`; the differing invoice goes through the reviewed `document_create`. Limitation: the guided supplier invoice cannot state a unit price. |
| H03 | `shipment_receive` of 7, reviewed `commitment_revise` to 7 with a note | pass | The reason is `CommitmentRevision.note`; the decision is the `commitment.revised` event's `action_id`, read through `record_decisions(..., "commitment", id)` and the proposal detail. |
| I06 | receive 8, guided `supplier_invoice_record` 6 and 4 | pass | Fully guided: `billed_not_received` reports `unreceived_quantity = 2`; a third guided invoice is refused with `invoice_quantity_exceeds_billable` (asserted). |
| I07 | carrier party with the supplier role, `supplier_invoice_free_record` with stated net, `cost.change` assign `inbound_freight` to the receipt movement as owner | pass | Needs an owner principal. `known_cost` includes the freight; the component names the carrier's invoice. No supplier match is required. |
| K05 | three items on one purchase, one `shipment_receive` with three movements, reviewed `reserve` per variant | pass | No parent item (out of scope, stays a limitation). |
| L06 | dated customer order without stock, supplier order, `supply_assign`; `fulfillment_readiness`, `supply_coverage`, `delivery_case` | pass | Protection does not clear `outgoing_commitment_at_risk`; the story shows shortage and protection side by side and says so. |
| O01 | reviewed `item_update` of the SKU after reserve, ship and invoice | pass | Movements, reservations and commitments carry `item_id` only; `DocumentLine.sku` keeps the stated number. Some reads (`order_explain`, projections) show the current SKU; the limitation names it. A replayed old payload is refused as an unknown SKU. |
| P04 | Shopify version with `cancelled_at` (held for review), reviewed `commitment_cancel` with `source_record_id` | pass | The `commitment.cancelled` event carries the source record and the reason. The `needs_review` interpretation outcome stays and is not claimed resolved. |
| P07 | declared source capability, daily `enqueue_shopify_order`, silence, backlog with exact repeats | pass with clock control | `SourceRecord.received_at` is the wall clock. The story moves time by patching `reality.db.core.datetime` (precedent: `test_clock_sensitivity.py`); time is environment, not business state, so this is not a shortcut. Repeats return the same record and job. |
| R01 | order, prepayment, partial payment, "released anyway", … | likely fail | No reviewed release overrides an unmet prepayment, as spec 275 FR-005 requires. R01 stays partial; its current limitation wrongly says the release works. |

## Defect found: a reviewed shipment movement bypasses payment readiness

The reviewed `movement_create` with `movement_type="shipment"` and a `commitment_id`
(`services/delivery_actions.py` review, `record_movement`) never consults `fulfillment_readiness`,
while `shipment_dispatch` refuses with `shipment_blocked_readiness`. An unpaid prepayment order can
therefore be shipped through *Record shipment*. This contradicts spec 275 FR-005 (a prepayment order
remains non-shippable until paid) and FR-008 (every tool consumes the shared readiness decision).
Under FR-006 of this spec it is fixed here with a regression test naming spec 275 FR-005.

## Decisions

- **Evidence routes**: reviewed tools where a person acts; shared services for setup, as in spec 292.
- **Clock control** for P07 is allowed; a patched clock only replaces waiting.
- **Keywords**: every promoted entry gets English and German keywords and question examples.
- **Story placement**: purchasing stories in `test_catalog_purchasing.py`; D16, L06, O01 in
  `test_catalog_orders_and_shipments.py`; P04, P07 in a new `test_catalog_sources.py`; R01 in
  `test_catalog_finance.py`.
