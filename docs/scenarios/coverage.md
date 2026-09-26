# Business Scenario Coverage

Spec impact: none. This records test evidence for [catalog.md](catalog.md); it changes no behavior.

Assessed against `main` at 4dc658f9 (2026-09-26) by reading tests, services and specs. Rows
pointing at `tests/scenarios/test_catalog_*.py` were proven by running those tests. Evidence paths are relative to `packages/reality-core/` unless they
start with `packages/`, `specs/` or `docs/`. Re-measure a row before building on it.

## Summary

228 scenarios: 69 covered, 82 partial, 0 missing, 74 gap, 3 out.

| Section | covered | partial | missing | gap | out |
|---|---|---|---|---|---|
| A Order intake and changes | 7 | 9 |  | 8 |  |
| B Availability and reservation | 5 | 7 |  | 6 |  |
| C Payment and release | 9 | 5 |  | 4 |  |
| D Shipment, split and merge | 3 | 4 |  | 12 |  |
| E Customer invoice and credit | 7 | 5 |  |  |  |
| F Returns and complaints | 6 | 6 |  | 1 |  |
| G Purchase demand and order | 5 | 7 |  | 5 |  |
| H Receipt and supplier deviations | 9 | 3 |  | 7 |  |
| I Supplier invoice and payment | 8 | 3 |  | 1 |  |
| J Warehouse and stock | 3 | 3 |  | 5 |  |
| K Kits and variants |  | 1 |  | 5 |  |
| L E-commerce and marketplaces | 2 | 5 |  | 5 |  |
| M B2B specifics |  | 4 |  | 8 |  |
| N Finance, tax, currency | 1 | 4 |  | 1 | 2 |
| O Master data and identity | 1 | 2 |  | 2 | 1 |
| P Sources and integration | 2 | 6 |  |  |  |
| Q Time and period | 1 | 2 |  | 2 |  |
| R Combined stress stories |  | 6 |  | 2 |  |

Strongest where an operational exception class exists (at-risk, reservation_exceeds_stock,
shipped_not_billed, returned_not_credited, billed_not_received, duplicate supplier invoice) and in
finance settlement. Weakest in physical execution before dispatch, source interpretation beyond
Shopify, and B2B structures.

## Gap themes

Most of the 74 gaps come from a few structural decisions or absences, not from single cases.

1. **Nothing exists between reservation and dispatch.** No picking record, no planned outbound
   delivery, no per-shipment address or recipient. A08, A11, A21, A24, D04, D13, M05.
2. **A movement must match its commitment exactly.** Over-receipt, wrong item and substitutes
   cannot be tied to the purchase or order; they appear only as `unexplained_movement`.
   H04, H05, H06, H07, D05 (F03 related).
3. **A return never reopens a kept promise (spec 079).** Undeliverable, refused and lost parcels
   cannot be told apart from a customer return. D07, D08, D09.
4. **No drop-ship path.** Fulfilment derives only from own-stock movements. D10, D11, G15, R03.
5. **No allocation policy.** Priority between promises, reserving by requested date, serving
   backorders on receipt, ship-complete, reservation lapse, channel quotas and shelf-life
   eligibility are all absent; spec 068 names allocation a non-goal. A12, B03, B11, B12, B15,
   B16, B17, M06 (B08, B10 partial). Reservation and dispatch readiness are also bound to the
   commitment's own location, so one promise cannot be served from two warehouses (D02).
6. **Locations have no availability status.** Quarantine, inspection and in-transit exist only as
   "move it to another location". B05, H08, H15, J01 (J05 partial by design).
7. **Only Shopify first-version orders are interpreted.** Changed orders are held for review
   (spec 081); shipments, refunds, marketplace, 3PL and EDI sources have no interpreter.
   D17, L03, M03 (A16, L01, L04, L05, M04, P04 partial).
8. **No framework contracts or schedule lines.** One supplier commitment per PO line; no blanket
   order or call-off. A23, G04, G05, M01.
9. **Party roles and identity are thin.** No bill-to/payer role, party merge, customer or
   supplier item numbers, or receivable/payable netting. L10, M10, M11, O02, O06 (M02 partial).
10. **Spec 148 trade finance is specified, not built.** Authorization/capture, chargeback,
    marketplace payout, cash on delivery, vouchers and the accounting export package.
    C09, C10, C13, C18, L03, N07, R04 (C15 partial).
11. **No kits or bills of material.** K01, K02, K03, K04, K06.
12. **No period record (spec 184 is a stub).** Q02, Q04. There is also no sales-side
    "invoiced not shipped" class (E03, Q01 partial).
13. **Single-currency settlement.** Cross-currency allocation is refused and no realized FX
    difference is posted. I11 (N03 out; G08 partial).
14. **Other single gaps:** loans and samples with a return obligation (M12), repair round trip
    (F10), returnable packaging (D19), subscriptions (L08), stored tax rate and customs data (L11,
    L12, D14), negative stock (J06 is refused by design), 3PL stock reconciliation (J07),
    cycle-count sessions (J03), re-labelling pairs (J11), unconfirmed purchase orders (G10),
    advised versus received quantity (G16, H17), quote documents (A14), variant swap on an
    open order (A10), customer delivery documents (M07).

Several gaps may be deliberate. They should become an explicit **out** with a reason in a scope
document rather than stay open (candidates: M07 labels, L11/N08 tax determination, J06 negative
stock, K kits if the core stays trading-only).

## Tests added for the former "missing" rows

The 19 scenarios first assessed as missing were written as tests in
`packages/reality-core/tests/scenarios/test_catalog_*.py` (#203): 18 pass and are now covered, and D02
turned out to be a gap. Where a test passes only through a narrower path, the row says so.

Found while writing them, deliberately not pinned by those tests:

- **G14 over-protection (defect, fix in #201).** `preview_supply_assignment` checked each new
  customer assignment against the customer's open quantity, not open minus what is already
  assigned, so supply assignments could protect 11 of a demand of 10 (spec 248 FR-009).
- **D02 reservation consumed at the wrong location (defect, fix in #202).** Shipping part of a
  promise from a second location consumed the reservation held at the promise's own location
  (spec 009 FR-006).
- **Historical balances use recording time for allocations.** `active_settlement_allocations`
  filters by `allocated_at` (wall clock), not the stated business date, so a balance as of a
  past cutoff can still show a credit that was refunded before that cutoff (seen in C06).
- **R02 assignment survives cancellation.** A cancelled customer promise keeps its purchase
  supply assignment until someone reverses it by hand.

The combined stories R01, R02, R05, R06, R07 and R08 can be written today as end-to-end
scenario tests from existing pieces. Each will show whether the pieces reconcile together.

## A. Order intake and order changes

| ID | Status | Evidence | Note |
|---|---|---|---|
| A01 | covered | packages/reality-core/tests/scenarios/test_order_to_cash.py::test_order_to_cash_business_story | Shopify order is reserved with no shortage and shipped in two parts, then invoiced, partly paid and credited; open quantity and open amount are asserted, and the trace reaches the raw payload. |
| A02 | partial | packages/reality-core/tests/test_unified_order_entry.py::test_multiline_review_trace_and_replay | Only 2 lines are tested. `order_create` takes one `location_id` per order (services/order_actions.py), so no test shows open quantity per line and per location across warehouses. |
| A03 | covered | packages/reality-core/tests/test_unified_order_entry.py::test_multiline_review_trace_and_replay | The same `item_id` on two lines gives two commitments with their own amounts. The discounted-versus-free case itself is not tested. |
| A04 | partial | packages/reality-core/tests/finance/test_commercial_edges.py::test_higher_revision_allows_only_the_new_quantity; tests/test_commitment_revisions.py::test_the_quantity_in_force_is_the_latest_stated | An upward revision is tested only with no delivery before it. No test raises the quantity after a partial shipment and asserts what is still open. |
| A05 | partial | packages/reality-core/tests/test_commitment_revisions.py::test_a_promise_can_shrink_below_what_arrived | The revision is accepted and marks the commitment fulfilled, neither refused nor turned into a return demand. Only the supplier side is tested, and no exception class reports the excess delivery. |
| A06 | partial | packages/reality-core/tests/test_commitment_actions.py::test_reviewed_cancellation_closes_open_remainder_and_releases_controls | Cancelling one commitment releases its reservation and hold. No multi-line order test asserts that the other lines stay open and reserved. |
| A07 | partial | packages/reality-core/tests/test_inventory_and_fulfillment.py::test_cancel_preserves_commitment_and_releases_allocation | There is no order-level cancel, only `cancel_commitment` per commitment. No test cancels every line of a reserved order. |
| A08 | gap | packages/reality-core/src/reality/services/core.py (no picking concept) | There is no picking or staging record, so "picked but not shipped" and the stock going back cannot be represented. |
| A09 | partial | packages/reality-core/tests/test_shopify_update_guard.py::test_changed_order_preserves_every_business_record[cancelled_at-10]; services/core.py::cancel_commitment | A `cancelled_at` sent after full shipment is held for review with no effect, and a direct cancel of a fulfilled commitment is refused. Neither is a test that classifies it as a return or a refusal. |
| A10 | gap | packages/reality-core/tests/test_document_corrections.py::test_manual_line_economic_changes_lock_after_reality_but_description_remains_correctable | Adding a line is blocked once Reality exists, and Shopify changes are held for review, so no path swaps a variant on the same order while keeping its history. |
| A11 | gap | packages/reality-core/src/reality/db/core.py (Document.ship_to_party_id; Shipment has only counterparty_id) | Ship-to exists only on the document. A shipment carries no address, so which address a shipment used cannot be answered. |
| A12 | gap | packages/reality-core/src/reality/services/core.py::reserve | Reservation is explicit, and no rule uses `due_at` or `requested_delivery_at` to decide when to reserve. |
| A13 | covered | tests/scenarios/test_catalog_orders_and_shipments.py::test_each_order_line_keeps_its_own_promised_date | Two lines carry their own promised date; a third falls back to the order's requested delivery date. |
| A14 | gap | packages/reality-core/src/reality/services/core.py::MANUAL_OPERATIONAL_DOCUMENT_TYPES | There is no quote document type and no quote-to-order link. Spec 259 is a pricing preview only. |
| A15 | covered | packages/reality-core/tests/test_shopify_and_explain.py::test_shopify_ingestion_is_lossless_idempotent_and_traceable | Re-sending the payload with its keys reordered still gives exactly one SourceRecord, Document and Commitment. |
| A16 | partial | packages/reality-core/tests/test_shopify_update_guard.py::test_changed_order_preserves_every_business_record; tests/test_shopify_and_explain.py::test_changed_source_creates_version_without_replacing_interpretation | A new version with a supersedes link is stored without overwriting, but the commitment is never revised: the change is held as `needs_review` (spec 081). |
| A17 | partial | packages/reality-core/tests/test_shopify_and_explain.py::test_source_survives_interpretation_failure; tests/operational_exceptions/test_derivation.py::test_source_interpretation_failure | The source is kept and the failure is visible, but the whole order is not interpreted. The line is not kept as a DocumentLine alongside the gap. |
| A18 | covered | packages/reality-core/tests/test_pricing.py::test_document_line_retains_agreed_entry_when_current_price_changes, ::test_manual_agreement_remains_valid_without_pricing_entry | The stated price is kept against the list price. Order entry also keeps a stated gross of 24.91 against 2 x 12.50. |
| A19 | partial | packages/reality-core/tests/test_commercial_matching_services.py::test_free_goods_keep_inventory_cost_and_zero_revenue | Only the zero-revenue invoice side is tested. No zero-price order line is shown committed and shipped. |
| A20 | covered | tests/scenarios/test_catalog_orders_and_shipments.py::test_one_shipment_fulfils_two_orders_of_the_same_customer | One shipment and one package fulfil two orders (3 and 5); 8 promised, 8 dispatched. |
| A21 | gap | packages/reality-core/src/reality/db/core.py (Commitment.to_party_id, Shipment.counterparty_id) | A commitment has no per-line recipient or address, so lines cannot be split across two delivery addresses. |
| A22 | covered | packages/reality-core/tests/test_commitment_holds.py::test_hold_blocks_reservation_and_movement_until_released, ::test_the_release_is_recorded_by_the_release_operation; tests/operational_exceptions/test_derivation.py (`commitment_hold_unreleased`) | The hold's reason code blocks execution, the release is recorded, and an unreleased hold is surfaced. |
| A23 | gap | (see M01); no blanket or call-off concept in src/reality | There is no frame-contract or call-off structure. |
| A24 | gap | packages/reality-core/src/reality/services/shipments.py::record_packaged_execution | Outbound shipments only exist at dispatch, with no pending delivery to join, and adding a line after Reality exists is blocked. |

## B. Availability, reservation and backorder

| ID | Status | Evidence | Note |
|---|---|---|---|
| B01 | covered | packages/reality-core/tests/test_inventory_and_fulfillment.py::test_shortage_reservation_and_release; tests/test_application_tools.py::test_reservation_receipts_classify_none_partial_and_complete | Reserving 30 against 20 on hand reserves 20 and reports 10 short; the receipt reports `effect=partial` with `remaining_work`. |
| B02 | covered | tests/operational_exceptions/test_derivation.py::test_outgoing_commitment_at_risk; tests/test_application_tools.py::test_reservation_receipts_classify_none_partial_and_complete | With no stock the whole promise is `outgoing_commitment_at_risk` (cause insufficient_reservation), and the receipt reports `effect=none`. |
| B03 | gap | specs/068-promise-coverage-exceptions/spec.md (Non-Goals); tests/operational_exceptions/test_derivation.py::test_reservation_exceeds_stock_impact | No allocation or priority rule exists: whoever reserves first gets the units, and only a `competing_commitments` count is reported. |
| B04 | covered | tests/scenarios/test_catalog_stock_and_returns.py::test_stock_reserved_for_one_customer_can_be_moved_to_a_more_important_one | Release then reserve moves the stock with exact per-commitment figures and ordered events. Nothing links the two steps unless the caller passes one action id. |
| B05 | partial | docs/features/inventory.md ("Nothing is blocked"); tests/test_returns.py::test_return_disposition_reconciles_four_partial_outcomes | There is no blocked-stock state; exclusion only works by moving goods to another location (for example a quarantine disposition transfer), and expired stock is deliberately still available. |
| B06 | partial | tests/test_stock_at_location.py::test_quantities_stay_at_the_exact_location, ::test_scoped_reservations_hold_that_location_only; docs/features/reservations.md | Availability is judged at the exact location, but nothing proposes the transfer, and no test reserves against stock that sits elsewhere. |
| B07 | partial | tests/test_supply_assignments.py::test_customer_and_stock_supply_reconcile_without_implying_receipt | Open PO quantity can be assigned to protect a customer promise (`protecting_supply`); there is no dated available-to-promise calculation. |
| B08 | partial | tests/test_supply_coverage.py::test_purchasing_sales_and_inventory_views_reconcile_without_double_counting | A receipt reserves nothing automatically (the test asserts 0 reservations); a supply assignment names the intended customer, but no serving order exists. |
| B09 | partial | tests/test_supply_coverage.py::test_purchasing_sales_and_inventory_views_reconcile_without_double_counting | The partial receipt is reconciled on the supplier side, but no test asserts which customer promises stay uncovered afterwards. |
| B10 | partial | tests/test_fulfillment_readiness.py::test_readiness_combines_stock_reservation_and_active_hold; tests/test_commitment_holds.py::test_a_held_promise_cannot_be_shipped | A reasoned commitment hold can explain "reserved but not shipped"; there is no ship-complete or no-partial-delivery rule. |
| B11 | gap | services/fulfillment_readiness.py (blocker set) | No per-order or per-customer limit on partial deliveries or parcel count exists. |
| B12 | gap | db/core.py `Reservation` (no deadline column); tests/scenarios/test_fulfillment_safety_parity.py::test_two_order_story_keeps_unpaid_prepayment_stock_inside | Prepayment only blocks shipment; a reservation has no lapse date and is never released automatically. |
| B13 | covered | tests/operational_exceptions/test_derivation.py::test_reservation_exceeds_stock, ::test_reservation_exceeds_stock_references_are_opaque | A stocktake loss raises `reservation_exceeds_stock` naming the reservations; it is judged per item across locations and blames no single promise. |
| B14 | partial | tests/operational_exceptions/test_derivation.py::test_outgoing_commitment_at_risk | Each unreserved promise is flagged, but there is no channel dimension and no aggregate "demand exceeds stock" view. |
| B15 | gap | docs/features/inventory.md (Available = physical − reserved) | Availability is one number per item and location; there is no safety stock and no per-channel or per-party availability. |
| B16 | gap | db/core.py `Reservation`/`Location` | There is no earmark or quota concept for a channel. |
| B17 | gap | docs/features/inventory.md ("choosing which lot ships is an allocation policy this product has never had") | A lot may be reserved explicitly, but no minimum-remaining-shelf-life eligibility check exists. |
| B18 | covered | tests/test_inventory_tracking_reservations.py::test_serial_reservation_identifies_exact_unit_and_quantity_one, ::test_confirmed_chat_tool_reserves_exact_serial_unit | The reservation names the exact serial unit, with quantity one. |

## C. Payment and release

| ID | Status | Evidence | Note |
|---|---|---|---|
| C01 | covered | packages/reality-core/tests/test_fulfillment_readiness.py::test_prepayment_readiness_uses_stated_order_and_active_allocation; tests/scenarios/test_fulfillment_safety_parity.py::test_two_order_story_keeps_unpaid_prepayment_stock_inside | Blockers `prepayment_invoice_missing`/`prepayment_required` block dispatch and clear once the payment is allocated; order_explain reports the reason. |
| C02 | covered | tests/scenarios/test_fulfillment_safety_parity.py::test_two_order_story_keeps_unpaid_prepayment_stock_inside (pays 40 of 100, stays blocked); tests/finance/test_settlement_flows.py::test_underpayment_optional_reduction_and_independent_inverse | Tolerance is zero on purpose (docs/features/payment_matching.md); a residual closes only through a confirmed `accepted_small_remainder` adjustment. |
| C03 | covered | tests/test_payment_intake.py::test_over_payment_settles_the_invoice_and_keeps_the_excess_as_credit; tests/finance/test_settlement_flows.py::test_excess_credit_reuse_refund_and_refund_inverse | The excess shows as available customer credit; it is tested on a plain invoice, not on a prepayment order. |
| C04 | partial | tests/test_ledger.py::test_one_payment_can_settle_multiple_invoices_tenant_safely | One payment settling several invoices is proven, but no test checks fulfillment_readiness of two prepaid orders fed by one payment. |
| C05 | covered | tests/test_payment_intake.py::test_candidates_have_reasons_and_write_nothing; ::test_ambiguous_reference_produces_candidates_and_allocation_ends_them | Money is recorded unallocated, tier-3 candidates carry reasons and write nothing, and an explicit allocate_settlement ends them. |
| C06 | covered | tests/scenarios/test_catalog_finance.py::test_payment_after_a_cancelled_prepayment_order_stays_credit_and_is_refunded | Payment after cancellation stays unallocated as customer credit (119) and is refunded through the confirmed settlement proposal. |
| C07 | partial | tests/operational_exceptions/test_derivation.py::test_credit_limit_exceeded; tests/test_unified_customer_holds.py::test_review_place_release_history_and_replay | The exception and a reviewed hold/release (with actor) are each tested; nothing links the exception to a hold, and there is no automatic credit hold. |
| C08 | partial | src/reality/services/exceptions.py::_credit_limit_exceeded_exceptions; tests/operational_exceptions/test_derivation.py::test_credit_exposure_uses_the_shared_open_items | Exposure comes from open invoices only (order value never counts) and names all open invoice ids, not the overdue ones; no test asserts the named items. |
| C09 | gap | specs/148-accounting-journal-cost-centers/spec.md FR-049/FR-050 (specified, not implemented) | No authorization or capture record; payment intake has only an unused `money_path` string. |
| C10 | gap | specs/148-accounting-journal-cost-centers/trade-finance-controls.md | Authorizations are not modeled, so an expired authorization and the uncovered remainder cannot be shown. |
| C11 | covered | tests/test_payment_terms.py::test_the_discount_deadline_is_one_shared_rule; tests/test_ledger.py::test_invoice_due_date_rule | Due date and discount date come from one shared rule in the aging register; the fixture is a supplier invoice, and sales invoices use the same rule. |
| C12 | covered | tests/operational_exceptions/test_derivation.py::test_a_discount_taken_explains_the_remainder | A discount deducted after the window gets no `early_payment_discount_taken` reason, so it stays a plain overdue receivable. |
| C13 | gap | none | No cash-on-delivery payment path; payments cannot be tied to a shipment. |
| C14 | partial | tests/scenarios/test_fulfillment_safety_parity.py (40 then 60 releases only at 100); tests/finance/test_commercial_edges.py::test_deposit_is_explicit_credit_and_clears_final_invoice | Release only after the remainder is proven; a 30 % deposit before any invoice is not tied to the order (the FR-051 earmark is not built) and readiness reports `prepayment_invoice_missing`. |
| C15 | partial | tests/test_ledger_reversals.py::test_payment_reversal_preserves_allocation_history_and_reopens_invoice | Reversing a payment reopens the receivable; there is no chargeback or returned-debit event, fee or provider dispute (spec 148 FR-050, not built). |
| C16 | covered | tests/test_party_delivery_holds.py::test_customer_delivery_hold_blocks_only_shipment; tests/test_fulfillment_readiness.py::test_readiness_combines_stock_reservation_and_active_hold | A party hold with reason and note blocks only shipments; readiness names the hold. There is no dedicated dunning or insolvency reason code. |
| C17 | covered | tests/test_commitment_holds.py::test_hold_blocks_reservation_and_movement_until_released; ::test_the_release_is_recorded_by_the_release_operation | Hold and release are both recorded generically (`compliance`/`manual_review`); there is no fraud reason and no hold driven by a source fraud signal. |
| C18 | gap | services/finance/settlement.py REASONS (no voucher) | Vouchers and gift cards are not a settlement instrument; only cash, credit notes, deposits and the four adjustment reasons exist. |

## D. Picking, shipment, split and merge

| ID | Status | Evidence | Note |
|---|---|---|---|
| D01 | covered | packages/reality-core/tests/test_inventory_and_fulfillment.py::test_partial_shipments_derive_fulfillment_and_consume_reservations | Asserts fulfilled 10 / open 20, then fulfilled after the remainder ships; the remaining reservation is used up too. |
| D02 | gap | packages/reality-core/src/reality/services/fulfillment_readiness.py (readiness at the commitment location only) | A reservation sits only at the commitment's location and dispatch readiness checks only that location, so part-stock in a second warehouse blocks the shipment. Shipping from the second location consumed the first location's reservation; fixed in #202. |
| D03 | covered | tests/scenarios/test_catalog_orders_and_shipments.py::test_one_package_carries_several_commitments_of_one_customer | One package fulfils three commitments over two items by their own quantities (0, 0 and 1 open). |
| D04 | gap | packages/reality-core/src/reality/db/core.py (no picking record; only Reservation → Movement) | Picking is not modelled, so there is no record for a caught picking error to correct. |
| D05 | gap | packages/reality-core/src/reality/services/core.py `_append_movement` ("Movement does not match the commitment") | A shipment of the wrong item cannot name the commitment it was meant for; it can only be recorded unlinked, as an unexplained movement. |
| D06 | covered | packages/reality-core/tests/operational_exceptions/test_derivation.py::test_reservation_exceeds_stock | A stocktake-loss adjustment raises reservation_exceeds_stock with the shortfall; the entry clears on receipt. |
| D07 | gap | packages/reality-core/src/reality/db/core.py ShipmentEvent (`delivery_exception` only) | No carrier-claim receivable. The lost shipment still counts as fulfilment unless it is corrected. No test uses delivery_exception. |
| D08 | gap | specs/079-returns-connect/spec.md (kept promise stays kept); tests/test_returns.py::test_a_return_leaves_the_promise_kept | Stock comes back, but a return can never reopen the commitment. "Undeliverable" and "returned by customer" are not told apart. |
| D09 | gap | same as D08 | Same as D08. Also, a return Movement has no reason; only ReturnAnnouncement carries one. |
| D10 | gap | packages/reality-core/src/reality/services/core.py (fulfilment derives only from own stock `shipment` Movements) | No drop-ship path: a commitment cannot be fulfilled without a movement out of own stock. |
| D11 | gap | same as D10 | Same as D10: no supplier-direct fulfilment path to combine with own stock. |
| D12 | partial | tests/operational_exceptions/test_derivation.py::test_order_stalled, ::test_lag_classes_clear_through_reality, ::test_a_backdated_shipment_cannot_drag_the_norm | The lag shows as order_stalled and clears on shipment. No test separates when the goods left from when the 3PL confirmed it. |
| D13 | gap | packages/reality-core/src/reality/db/core.py Shipment/ShipmentEvent (no slot/appointment field) | There is no booked delivery slot record, only movement occurred_at and carrier events. |
| D14 | gap | db/core.py Shipment/Document (no customs or export-proof link) | Export evidence could only sit in a lossless payload; nothing typed links it to the shipment. |
| D15 | partial | tests/test_inventory_and_fulfillment.py::test_partial_shipments_derive_fulfillment_and_consume_reservations | Fulfilment without carrier or package works, but pickup is not recorded or tested as a mode of its own. |
| D16 | partial | tests/scenarios/test_international_demo.py::test_supported_edge_cases_are_source_backed_and_traceable (exchange_replacement, SO-033/SO-034) | The replacement uses a new zero-price order. A commitment without a document is possible but untested. |
| D17 | gap | packages/reality-core/src/reality/services/core.py SOURCE_INTERPRETERS (no shipment interpreter) | No shipment source is interpreted, so nothing holds an early confirmation and links it later. |
| D18 | partial | tests/test_shipment_actions.py::test_receive_confirmation_replays_one_atomic_package; tests/test_unified_delivery_actions.py::test_same_preparation_and_confirmation_have_one_effect | Replaying a proposal is idempotent. A duplicate shipment report from a source is never ingested, so that case is untested. |
| D19 | gap | db/core.py (no deposit or returnable-packaging concept) | Nothing tracks returnable packaging or the deposit owed. |

## E. Customer invoice and credit note

| ID | Status | Evidence | Note |
|---|---|---|---|
| E01 | covered | tests/operational_exceptions/test_derivation.py::test_shipped_not_billed; ::test_billing_sums_across_invoices | Unbilled quantity per order line falls to zero as partial invoices arrive. |
| E02 | partial | specs/122-multi-position-invoices/spec.md (multi-order consolidation is a non-goal); tests/test_multi_position_invoices.py::test_invalid_is_inert[mixed] | Line-level `billed_document_line_id` could express it, but the shared invoice entry refuses lines from several orders; there is no collective-invoice test. |
| E03 | partial | tests/test_fulfillment_readiness.py::test_prepayment_readiness_uses_stated_order_and_active_allocation | Invoicing before shipment works; there is no sales-side "billed not shipped" observation (only purchase-side `billed_not_received`) and no pro-forma document type. |
| E04 | covered | tests/test_partial_invoicing_rebilling.py::test_partial_reversal_rebilling_and_historical_proof; tests/test_ledger_reversals.py::test_reversal_appends_exact_inverse_and_preserves_original | The exact inverse is appended and the original stays; billing becomes available again for the new invoice. |
| E05 | covered | tests/test_unified_invoice_credit.py::test_partial_multi_credit_without_return_and_exact_recovery; ::test_financial_credit_does_not_require_return_exception | The receivable drops with zero Movements and no `credited_not_returned`. |
| E06 | covered | tests/operational_exceptions/test_derivation.py::test_returned_not_credited; ::test_invoice_linked_credit_clears_returned_not_credited_through_shortest_links | Return and credit meet on the order line through the shortest links, not through a direct link from the credit to the return movement. |
| E07 | partial | tests/operational_exceptions/test_derivation.py::test_invoice_price_differs; ::test_shipped_not_billed | Price differences and under-billing are visible; billing more than was shipped on the sales side is not reported. |
| E08 | partial | tests/operational_exceptions/test_derivation.py::test_a_restocking_fee_is_a_charge_not_a_smaller_credit; ::test_non_deliverable_lines_are_never_reported | Fee as a separate charge and freight lines are handled (the freight test is purchase-side); no sales-invoice freight or surcharge test, and PSP payment fees are not built. |
| E09 | covered | tests/scenarios/test_catalog_finance.py::test_invoice_billed_to_the_orderer_keeps_a_different_ship_to_party | Invoice, AR and balance name the orderer; ship-to is reachable through the billed order line. The invoice document itself carries no ship-to. |
| E10 | covered | tests/scenarios/test_catalog_finance.py::test_e_invoice_xml_is_stored_losslessly_as_traceable_source_evidence | XRechnung bytes (BOM, CRLF, umlauts) round-trip exactly with hash and size; the source stays unmapped, no interpreter exists. |
| E11 | partial | tests/finance/test_commercial_edges.py::test_deposit_is_explicit_credit_and_clears_final_invoice | Deposit clearing into the final invoice is proven; there is no down-payment invoice document, and the final invoice does not state the offset. |
| E12 | covered | tests/test_multi_position_invoices.py::test_stated_values_and_recovery; tests/test_credit_notes.py::test_the_stated_total_is_what_posts; tests/test_documents.py::test_recording_requires_a_stated_total | The header total (209.1234) is kept and posted independently of the line amounts. |

## F. Returns and complaints

| ID | Status | Evidence | Note |
|---|---|---|---|
| F01 | partial | tests/test_credit_notes.py::test_a_paid_invoice_can_still_be_credited, ::test_a_credit_may_be_refunded; tests/test_returns.py::test_a_return_may_name_the_delivery_it_reverses | Each piece is tested alone; no one story runs return, credit and paid refund on one order. |
| F02 | covered | tests/operational_exceptions/test_derivation.py::test_returned_goods_are_not_reported_as_unbilled, ::test_returned_not_credited | Returned 4 or 6 against kept quantity is asserted through shipped_not_billed and returned_not_credited. |
| F03 | covered | tests/scenarios/test_catalog_stock_and_returns.py::test_a_different_item_returned_does_not_fulfil_the_announcement | A foreign item cannot fulfil the announcement; it stands unexplained, and the announcement stays outstanding until the announced item arrives. |
| F04 | partial | tests/test_return_announcements.py::test_the_parcel_names_its_announcement; tests/scenarios/test_normal_month.py::test_the_month_ends_with_exactly_these_exceptions | Accepting an unannounced return is tested. Linking an orphan return later (e.g. via correct_movement) is not. |
| F05 | partial | tests/operational_exceptions/test_derivation.py::test_a_restocking_fee_is_a_charge_not_a_smaller_credit; tests/test_returns.py::test_return_disposition_reconciles_four_partial_outcomes | A reduced credit and the disposition are tested separately; no damaged-return story combines them. |
| F06 | covered | tests/test_returns.py::test_return_disposition_reconciles_four_partial_outcomes; tests/scenarios/test_b2b_operational_chain.py::test_supply_and_return_reconciliations_are_exact | Arrived 5 = restock 2 + quarantine 1 + scrap 1 + back to supplier 1; over-disposition is refused. |
| F07 | partial | tests/scenarios/test_international_demo.py::test_supported_edge_cases_are_source_backed_and_traceable (exchange_replacement) | Only the order of the return and replacement movements is asserted; "no refund / no money moved" is not. |
| F08 | partial | tests/operational_exceptions/test_derivation.py::test_credited_not_returned | A credit before the goods arrive is covered. The refund payment and a "return still expected" signal are not asserted. |
| F09 | covered | tests/operational_exceptions/test_derivation.py::test_announced_return_not_arrived, ::test_an_announcement_with_no_stated_day_is_judged_by_the_learned_rhythm | A stale announcement is reported by the stated date or the learned rhythm, and clears on arrival. |
| F10 | gap | packages/reality-core/src/reality/services/return_dispositions.py (return_to_supplier is terminal) | Goods cannot go out for repair and come back while staying owned. |
| F11 | covered | tests/operational_exceptions/test_derivation.py::test_credited_not_returned (first assertion); tests/scenarios/test_international_demo.py price_only_credit | A credit with no return raises nothing ("a decision, not a discrepancy"); the price-only allowance reduces the invoice. |
| F12 | partial | tests/operational_exceptions/test_derivation.py::test_credited_not_returned | Credit and return are independent, but no marketplace refund source is interpreted or tested. |
| F13 | covered | tests/scenarios/test_catalog_finance.py::test_return_credit_after_month_end_books_in_the_next_month | Invoice ledger entries fall in August, the credit in September, by stated dates. |

## G. Purchasing: demand and purchase order

| ID | Status | Evidence | Note |
|---|---|---|---|
| G01 | covered | packages/reality-core/tests/test_supply_assignments.py::test_customer_and_stock_supply_reconcile_without_implying_receipt; tests/scenarios/test_b2b_operational_chain.py::test_supply_and_return_reconciliations_are_exact | An explicit `customer_demand` assignment links the PO commitment to the customer commitment (`protecting_supply`). |
| G02 | partial | tests/test_supply_assignments.py (purpose `stock_replenishment`) | The purpose of stock demand can be stated, but there is no reorder point or trigger (no `reorder` concept anywhere in src). |
| G03 | covered | tests/scenarios/test_b2b_operational_chain.py::test_supply_and_return_reconciliations_are_exact | Asserts 10 = 6 customer + 2 stock + 2 unassigned for PO-010. |
| G04 | gap | src/reality/db/core.py `uq_commitment_document_line_type` | Only one supplier_delivery commitment is allowed per PO line, so several schedule lines per line cannot be represented. |
| G05 | gap | — | No framework agreement or call-off concept exists. |
| G06 | partial | tests/test_supply_assignments.py::test_customer_and_stock_supply_reconcile_without_implying_receipt | Surplus shows up as stock or unassigned supply; MOQ and pack size are not modelled or tested. |
| G07 | partial | tests/operational_exceptions/test_derivation.py::test_invoice_price_differs; services/core.py::create_price_list_entry | The stated line `unit_price` is kept and compared; supplier tiered prices are not tested (price tiers look sales-side). |
| G08 | partial | db/core.py Commitment.currency; tests/test_payment_runs.py::test_a_run_is_one_currency | Currency is kept and cross-currency is refused; nothing converts at posting (docs/features/ledger.md Non-goals: FX revaluation). |
| G09 | partial | tests/test_commitment_revisions.py::test_the_quantity_in_force_is_the_latest_stated, ::test_one_statement_can_restate_both | Confirmed quantity/date are revisions against the original; a confirmed *price* cannot be stated. |
| G10 | gap | — | No acknowledgement expectation, so an unconfirmed PO is never flagged (only overdue after the due date). |
| G11 | covered | tests/test_commitment_revisions.py::test_a_new_date_never_erases_the_old_one, ::test_the_date_in_force_is_the_latest_stated | Append-only revisions; the latest one is in force. |
| G12 | partial | tests/scenarios/test_international_demo.py::test_purchases_cover_the_whole_chain (S09 cancelled) | Cancellation before receipt works; cancellation cost or supplier refusal cannot be recorded. |
| G13 | partial | tests/test_supply_assignments.py::test_partial_reversal_is_append_only_and_idempotent | The assignment is reversed manually with a reason; nothing ties the customer cancellation to the purchase reduction. |
| G14 | covered | tests/scenarios/test_catalog_purchasing.py::test_two_suppliers_purchases_together_protect_one_customer_promise | 6 + 4 from two suppliers protect a demand of 10. Defect found: protection could reach 11 of 10; fixed in #201. |
| G15 | gap | specs/242-inventory-cost-contribution/spec.md (drop shipping only listed as edge case) | No drop-ship commitment type or supplier-to-customer link. |
| G16 | gap | src/reality/services/shipments.py (`announced` quantity always None) | Inbound notices/`in_transit` events carry no per-commitment contents, so in-transit per purchase cannot be derived. |
| G17 | covered | tests/operational_exceptions/test_derivation.py::test_non_deliverable_lines_are_never_reported; tests/test_free_supplier_invoice.py::test_free_supplier_invoice_is_source_backed_atomic_and_has_no_stock_effect | A PO line with no commitment expects no receipt. |

## H. Goods receipt and supplier deviations

| ID | Status | Evidence | Note |
|---|---|---|---|
| H01 | covered | tests/scenarios/test_procure_to_pay.py::test_procure_to_pay_business_story | Fulfilled 20 of 20 through two receipts. |
| H02 | covered | tests/test_unified_receipt_release.py::test_partial_receipt_review_replay_and_trace; tests/scenarios/test_storyline_purchase_to_pay.py (receipt/rest-receipt) | Open remainder 5 after 3 of 8. |
| H03 | partial | tests/test_commitment_revisions.py::test_shrinking_to_what_arrived_finishes_the_promise | A downward revision closes the rest; the revision's note and who made it are not asserted. |
| H04 | gap | services/core.py "Movement exceeds the commitment's open quantity"; tests/test_unified_receipt_release.py (excess refused) | Over-receipt is refused. Workaround: revise upward first (finance/test_commercial_edges.py::test_higher_revision_allows_only_the_new_quantity, sales-side); no surplus signal. |
| H05 | gap | services/core.py supplier_return bound | A supplier return must reference a received delivery, and the surplus cannot be received against the PO. |
| H06 | gap | services/core.py "Movement does not match the commitment" | Wrong item cannot be tied to the PO; it only appears as an unexplained receipt. |
| H07 | gap | — | No substitute/successor item link on receipt. |
| H08 | gap | services/return_dispositions.py (customer returns only) | Location has no availability status; inbound quarantine is not modelled. |
| H09 | partial | tests/operational_exceptions/test_derivation.py::test_unexplained_movement_warning_does_not_suppress_exception | An unlinked receipt is flagged; a stated reason (sample/free) is not tested. |
| H10 | covered | tests/scenarios/test_catalog_purchasing.py::test_one_inbound_package_is_split_across_several_purchase_orders | One package receives 5 for PO-A and 4 for PO-B; shipment_explain reports 9. |
| H11 | covered | tests/scenarios/test_catalog_purchasing.py::test_early_receipt_fulfils_the_purchase_and_keeps_its_due_date | Receipt before the due date fulfils the purchase and keeps the due date; no read names a receipt "early", it is derivable. |
| H12 | covered | tests/scenarios/test_catalog_purchasing.py::test_receipt_before_purchase_order_is_linked_later_by_replacement | An unexplained receipt is linked to the later PO by correct_movement; stock unchanged, PO fulfilled, exception cleared. |
| H13 | covered | tests/test_inventory_tracking_reservations.py::test_lot_quantity_can_be_received_reserved_and_shipped_on_a_pallet, ::test_a_lot_carries_the_stated_best_before; tests/scenarios/test_international_demo.py (SER-0001 receipt) | Lot, expiry and serial on receipt, though not against a PO commitment. |
| H14 | covered | tests/test_movement_corrections.py::test_void_receipt_appends_exact_correction_and_preserves_original | A compensating movement; the original is preserved. |
| H15 | gap | specs/116-unified-receipt-release (reservation release, not QC) | No inspection hold or received-but-not-released state. |
| H16 | partial | docs/features/b2b-operational-chain.md; tests/test_supply_assignments.py | The assignment states intent; the receipt does not reserve for the waiting commitment and no test asserts it. |
| H17 | gap | tests/test_shipment_story.py::test_supplier_notice_has_zero_effect_then_package_receipt_changes_stock (`announced` None) | Advised quantities are not recorded, so advised vs received cannot be compared. |
| H18 | covered | tests/operational_exceptions/test_derivation.py::test_supplier_return_not_credited, ::test_supplier_credit_not_returned; tests/test_returns.py::test_goods_go_back_to_the_supplier | Return and credit reconciled per PO line. |
| H19 | covered | tests/test_costing_services.py::test_receipt_a_and_retained_review_survive_late_cost | Late duty makes the reviewed receipt cost stale; the old manifest is kept. |

## I. Supplier invoice and payment

| ID | Status | Evidence | Note |
|---|---|---|---|
| I01 | partial | tests/scenarios/test_storyline_purchase_to_pay.py; tests/operational_exceptions/test_derivation.py::test_received_but_not_yet_billed_is_not_reported | A match shows only as no findings; no positive "matched" answer and no clean three-way test. |
| I02 | covered | tests/operational_exceptions/test_derivation.py::test_received_but_not_yet_billed_is_not_reported; tests/scenarios/test_storyline_purchase_to_pay.py (billed_not_received raised/cleared) | |
| I03 | covered | tests/scenarios/test_storyline_purchase_to_pay.py::test_the_default_path_raises_and_clears_every_finding_by_rule | `invoice_price_differs` on the supplier invoice remains at month end. |
| I04 | covered | tests/operational_exceptions/test_derivation.py::test_billed_not_received | Billed 6, received 0, clears on receipt. |
| I05 | covered | tests/scenarios/test_catalog_purchasing.py::test_one_supplier_invoice_bills_lines_of_two_purchase_orders | Only the free supplier invoice path accepts lines of two POs; the order-line invoice command refuses them ("Invoice positions must belong to the same order."). |
| I06 | partial | tests/operational_exceptions/test_derivation.py::test_billing_sums_across_invoices | Summing across invoices is tested on the sales side only. |
| I07 | partial | tests/test_costing_services.py (inbound_freight attribution) | Freight is attributed to a receipt, but the evidence is from the goods supplier; a third-party carrier invoice is untested. |
| I08 | covered | tests/test_credit_notes.py::test_netting_leaves_the_remainder_open; tests/scenarios/test_storyline_purchase_to_pay.py::test_the_credit_branch_pays_less_and_keeps_the_quantity_finding | |
| I09 | covered | tests/finance/test_commercial_edges.py::test_deposit_is_explicit_credit_and_clears_final_invoice[supplier] | The deposit is not linked to the PO. |
| I10 | covered | tests/scenarios/test_storyline_purchase_to_pay.py (discount-full, credit-allocate, discount-net); tests/test_ledger.py::test_supplier_invoice_and_partial_payment_leave_open_payable | |
| I11 | gap | docs/features/ledger.md Non-goals (FX revaluation); ledger rejects cross-currency | No realized FX difference posting; revaluation is out, the realized difference is not stated either way. |
| I12 | covered | tests/operational_exceptions/test_derivation.py::test_duplicate_supplier_invoice; tests/test_payment_runs.py::test_the_duplicate_rule_has_one_home; tests/test_ledger.py::test_duplicate_invoice_posting_and_overpayment_are_rejected | Detected, and payment runs refuse it. |

## J. Warehouse and stock

| ID | Status | Evidence | Note |
|---|---|---|---|
| J01 | gap | docs/features/movements.md (transfer has both source and destination) | A transfer is one instant movement with no in-transit state; spec 242 FR-008 mentions transit for valuation only. |
| J02 | partial | tests/operational_exceptions/test_derivation.py::test_reservation_exceeds_stock ("stocktake loss"); tests/test_inventory_and_fulfillment.py::test_adjustment_requires_reason | Losses and gains are recorded as reasoned adjustments; there is no count record (counted vs book quantity) and no test of a stocktake gain. |
| J03 | gap | services/ (no count or pick concept) | There are no count sessions and no picking state, so a cycle count during open picks cannot be represented. |
| J04 | covered | tests/test_inventory_and_fulfillment.py::test_transfer_return_and_reasoned_adjustment_reconcile_by_location, ::test_adjustment_requires_reason | A write-off adjustment requires a reason and reconciles by location; the reason is free text, not a code. |
| J05 | partial | tests/test_inventory_tracking_reservations.py::test_expiry_blocks_nothing; tests/operational_exceptions/test_derivation.py::test_stock_expired | Expired lots are reported (`stock_expired`) but deliberately not excluded from availability; scrapping is a plain adjustment. |
| J06 | gap | services/core.py ("Movement exceeds physical stock."); tests/test_inventory_and_fulfillment.py::test_cannot_ship_more_than_stock | Outbound movements above physical stock are refused, so negative stock cannot occur or be explained. |
| J07 | gap | — | No external or 3PL stock observation exists to compare with movement-derived stock. |
| J08 | covered | tests/scenarios/test_catalog_stock_and_returns.py::test_consignment_stock_at_a_customer_site_stays_counted_as_ours | Stock at a consignment location stays in the company total and is available only there. Ownership and valuation are not asserted (a location has no party link). |
| J09 | partial | tests/test_inventory_costing_services.py::test_inventory_two_owner_receipt_excludes_consigned_stock | Valuation leaves out the supplier-owned part of a receipt; physical stock and availability do not distinguish owner. |
| J10 | covered | tests/test_inventory_costing_services.py::test_inventory_late_cost_requires_receipt_review_and_preserves_old_basis | Late inbound freight re-derives acquisition value (420 → 440) after a fresh review and keeps the old basis. |
| J11 | gap | docs/features/movements.md (movement types) | Re-labelling can only be two unrelated adjustments; no relation pairs the out-movement of A with the in-movement of B. |

## K. Kits, bills of material and variants

| ID | Status | Evidence | Note |
|---|---|---|---|
| K01 | gap | services/core.py create_item (`item_type` in stocked/service/charge) | There is no kit or bill-of-materials structure, so kit availability cannot be derived from components. |
| K02 | gap | services/core.py create_item | There is no kit concept, so the whole kit cannot be held when one component is missing. |
| K03 | gap | services/core.py create_item | A component can be returned as its own item, but there is no kit link, so no partial kit credit can be derived. |
| K04 | gap | specs/242-inventory-cost-contribution/spec.md (Non-Goals: no production/WIP) | There is no assembly or production movement that pairs components consumed with the finished item produced. |
| K05 | partial | tests/test_stock_at_location.py::test_pair_holds_only_this_item_at_this_location | Each variant as its own item gets its own stock; there is no parent/variant grouping and no test with several variants. |
| K06 | gap | tests/test_commercial_matching_services.py::test_shipping_kit_production_direct_cost_and_unresolved_wip_are_explicit | A `kit_input` role exists for cost matching only; there is no bundle-to-component revenue or tax split, so lines carry only stated amounts. |

## L. E-commerce and marketplaces

| ID | Status | Evidence | Note |
|---|---|---|---|
| L01 | covered | tests/scenarios/test_catalog_stock_and_returns.py::test_stock_at_an_external_fulfilment_location_is_sold_from_there | Stock at an external fulfilment location is reserved and shipped from there. No marketplace report interpreter exists. |
| L02 | partial | tests/operational_exceptions/test_derivation.py::test_overdue_outgoing_customer_commitment, ::test_at_risk_unchanged_before_due_date | Generic due_at classes only. A fully reserved order near its deadline is not flagged until overdue. No marketplace source. |
| L03 | gap | specs/148-accounting-journal-cost-centers/spec.md FR-050; docs/features/payment_matching.md Non-goals | Payout and fee matching is specified but not implemented: no payout or provider-clearing code exists. |
| L04 | partial | tests/test_unified_customer_refund.py::test_original_refund_source_is_preserved; specs/081-shopify-update-guard | A refund can cite a SourceRecord. The Shopify interpreter ignores refunds, and a refunded (changed) order goes to needs_review. |
| L05 | partial | tests/test_shopify_update_guard.py::test_changed_order_preserves_every_business_record; tests/test_shopify_and_explain.py::test_changed_source_creates_version_without_replacing_interpretation | The new version is stored, but the commitment is deliberately not revised: it is held as needs_review. |
| L06 | partial | tests/test_inventory_and_fulfillment.py::test_shortage_reservation_and_release; tests/operational_exceptions/test_derivation.py::test_at_risk_unchanged_before_due_date | A dated commitment without stock shows as a shortage or at_risk. A pre-order backed by expected supply is not tested. |
| L07 | partial | specs/033-large-tenant-register-benchmark; tests/test_unified_delivery_actions.py::test_two_connections_cannot_overallocate_or_execute_two_stale_reviews; specs/181-scale-foundations (Draft) | Concurrent reservation safety and the 10k read baseline are proven. Ingest throughput is not. |
| L08 | gap | db/core.py Commitment (no recurrence) | No recurring or subscription commitment; holds exist only per single commitment. |
| L09 | covered | tests/scenarios/test_catalog_orders_and_shipments.py::test_shopify_free_promotion_item_is_its_own_zero_price_line_and_commitment | A Shopify gift line at 0.00 becomes its own line and commitment; the raw line payload is kept. |
| L10 | gap | services/ (no party merge or duplicate-of service) | Duplicate parties cannot be merged with history kept. |
| L11 | gap | db/core.py Document/DocumentLine (no tax fields); docs/features/demo-data-catalog.md "Deliberate limitations" | The tax rate lives only in the raw payload; the Shopify interpreter does not record it. |
| L12 | gap | db/core.py (no incoterm, duty or customs fields) | Duties and incoterms are not represented beyond the lossless payload. |

## M. B2B specifics

| ID | Status | Evidence | Note |
|---|---|---|---|
| M01 | gap | packages/reality-core/src/reality/db/core.py (Commitment, CommitmentRevision) | There's no blanket-order or call-off relation, so "called off vs remaining" across child orders can't be represented. |
| M02 | partial | tests/test_pricing.py::test_pricing_resolves_direct_group_default_and_quantity_tiers; tests/test_price_quote_mcp.py::test_price_quote_matches_canonical_service_and_exposes_direct_provenance | Customer-specific prices are proven, but there is no model for a customer item number or name mapped to an Item. |
| M03 | gap | tests/test_master_data_api.py::test_api_ingests_arbitrary_source_as_unmapped | EDI messages can only be stored as unmapped sources; there are no ORDERS/ORDRSP/DESADV/INVOIC/REMADV interpreters or links between messages. |
| M04 | partial | tests/test_commitment_revisions.py::test_the_quantity_in_force_is_the_latest_stated; tests/scenarios/test_b2b_operational_integrity.py::test_b2b_inventory_revision_return_and_cancellation_reconcile_exactly; tests/test_shopify_update_guard.py::test_changed_order_preserves_every_business_record | Manual `commitment_revise` is proven; a customer ORDCHG source does not create a revision (a changed Shopify order is held for review instead). |
| M05 | gap | db/core.py Document.ship_to_party_id | Only one ship-to per document header, so several recipients per order can't be stated. |
| M06 | gap | tests/test_commitment_revisions.py::test_shrinking_to_what_arrived_finishes_the_promise; specs/085-close-stale-promises/spec.md | There is no party-level "no backorders" rule; the remainder can only be closed by hand (revise or cancel with a reason). |
| M07 | gap | docs/ideas/attachments.md (HandlingUnit label idea only) | No label or delivery-note output exists, and no doc states it is out of core scope, so "out" can't be cited. |
| M08 | partial | tests/finance/test_settlement_flows.py::test_underpayment_optional_reduction_and_independent_inverse, ::test_supplier_reduction_requires_agreement_and_combined_limit; services/finance/settlement.py REASONS | The `agreed_deduction` reason exists and is tested on the supplier side only; no customer penalty or marketing-contribution short payment is tested. |
| M09 | partial | tests/test_unified_invoice_credit.py::test_financial_credit_does_not_require_return_exception; specs/004-master-data/spec.md Non-Goals ("rebates") | A credit without goods can carry a rebate; rebate agreements and year-end accrual are an explicit non-goal. |
| M10 | gap | db/core.py Document (party_id, ship_to_party_id); tests/test_operational_fields.py::test_document_and_commitment_operational_fields | Only orderer and ship-to are typed; there is no bill-to or payer role on documents or settlement. |
| M11 | gap | services/core.py allocate_settlement ("must be opposite sides of one control account"); specs/170-party-balances/spec.md Non-Goals | One party can hold both roles, but a receivable can't be offset against a payable. |
| M12 | gap | db/core.py ReturnAnnouncement; `create_commitment` allows only customer_delivery/supplier_delivery | There's no loan or sample commitment. A shipment would count as a sale (shipped_not_billed); a ReturnAnnouncement only comes close. |

## N. Finance, tax and currency

| ID | Status | Evidence | Note |
|---|---|---|---|
| N01 | partial | tests/finance/test_components.py::test_zero_unknown_and_gross_basis_are_distinct; tests/finance/test_source_mappings.py::test_source_mapping_preview_confirmation_and_no_financial_effect ("EU" case) | Stated net/tax and explicit case codes are kept; no intra-community sale story (zero tax plus Party.tax_identifier). |
| N02 | partial | tests/finance/test_components.py::test_received_net_split_and_partial_revision_preserve_gross (supplier kind) | Stated components on supplier invoices are kept; no reverse-charge case is tested. |
| N03 | out | docs/features/ledger.md Non-goals (FX revaluation); specs/148-accounting-journal-cost-centers/spec.md (no accounting-currency conversion) | Foreign-currency invoices are supported, but cross-currency allocation is refused, so a EUR payment on a CHF invoice stays unallocated and no FX difference exists. |
| N04 | partial | tests/finance/test_commercial_edges.py::test_dunning_notice_keeps_invoice_and_posts_optional_fee; ::test_mcp_dunning_context_record_detail_list_and_reverse | Manual notices at levels 1–3 with a fee exist (only levels 1 and 2 are tested); no escalation sequence, no collection handover, and runs from open items are a non-goal (spec 247). |
| N05 | covered | tests/finance/test_commercial_edges.py::test_bad_debt_uses_dedicated_expense_and_never_creates_credit | A partial `bad_debt` adjustment with a reason posts to bad-debt expense and creates no credit. |
| N06 | partial | tests/finance/test_party_balances.py::test_party_rows_sum_open_items_and_credits | Open items, overpayments and credit notes per party and currency are correct; deposits and prepayments are not part of any balance test. |
| N07 | gap | specs/148-accounting-journal-cost-centers/spec.md FR-012 (export package specified, not implemented) | No handoff or export package exists, so "reversal after export" cannot be represented; the reversal itself exists. |
| N08 | out | specs/148-accounting-journal-cost-centers/spec.md Non-goals (no tax engine or tax calculation) | Reality stores stated tax and never determines a rate, so rate by invoice date is the source's job. |

## O. Master data and identity

| ID | Status | Evidence | Note |
|---|---|---|---|
| O01 | partial | tests/test_reference_workspace.py::test_full_item_edit_changes_inventory_behaviour; tests/test_master_data_parity.py::test_cli_and_api_produce_equivalent_authoritative_lifecycle_state; tests/test_operational_previews.py::test_document_keeps_description_sku_and_received_totals | SKU edits are proven and lines keep the SKU they stated; no test asserts that movements, stock and old documents stay intact after a rename. |
| O02 | gap | — (no merge service in services/) | There is no party merge or duplicate-resolution operation. |
| O03 | out | specs/004-master-data/spec.md Non-Goals ("postal addresses") | Addresses exist only in lossless party or source payloads; no test proves an old order shows the old address. |
| O04 | covered | tests/scenarios/test_catalog_orders_and_shipments.py::test_delisted_item_still_serves_its_open_commitment | An inactive item is still reserved and shipped for its open commitment. |
| O05 | partial | tests/operational_exceptions/test_derivation.py::test_a_stated_conversion_lets_the_comparison_happen, ::test_an_inexact_conversion_is_declined, ::test_units_not_comparable | The purchase_unit/conversion_factor comparison only runs inside exception classes; receipts and stock are not converted (receipt-costing.md excludes unit conversion). |
| O06 | gap | db/core.py Item (no supplier reference table) | There's no supplier item number or per-supplier item mapping. |

## P. Sources and integration

| ID | Status | Evidence | Note |
|---|---|---|---|
| P01 | covered | packages/reality-core/tests/test_shopify_and_explain.py::test_shopify_ingestion_is_lossless_idempotent_and_traceable; tests/test_source_ingestion.py::test_unknown_source_is_stored_idempotently_as_unmapped; tests/test_payment_intake.py::test_replay_of_the_same_source_records_no_second_cash_entry | Idempotency is proven for orders, unmapped sources and payments. |
| P02 | partial | packages/reality-core/tests/test_shopify_and_explain.py::test_stale_and_conflicting_webhooks_are_stored_but_not_interpreted, ::test_first_version_failure_retries_but_changed_version_requires_review | A stale webhook is stored but ignored, and an order is linked once its item exists. No test covers cross-record ordering, such as a payment or invoice arriving before its order and linking later. |
| P03 | covered | packages/reality-core/tests/test_shopify_and_explain.py::test_changed_source_creates_version_without_replacing_interpretation; tests/test_document_corrections.py::test_external_document_correction_appends_immutable_source_version | A correction creates a new version with a supersedes link and keeps the original payload. |
| P04 | partial | packages/reality-core/tests/test_shopify_update_guard.py::test_changed_order_preserves_every_business_record[cancelled_at-*] | A source cancellation is stored and held for review, and the commitment stays open. `cancel_commitment(source_record_id=...)` exists, but no test closes a commitment with a source reason. |
| P05 | partial | packages/reality-core/tests/test_interpretation_coverage.py::test_unsupported_and_historical_sources_have_explicit_coverage; tests/test_unified_order_entry.py::test_missing_or_ambiguous_evidence_is_not_success | Unsupported and failed payloads are visible. No test accepts a partially complete payload and flags the missing field. |
| P06 | partial | packages/reality-core/tests/test_shipment_story.py::test_supplier_source_payload_and_carrier_warehouse_discrepancy_remain_distinct; tests/test_provenance.py::test_several_contributing_systems_are_disclosed | Only the carrier-versus-warehouse contradiction is surfaced. There is no general check when two systems state different values. |
| P07 | partial | packages/reality-core/tests/operational_exceptions/test_derivation.py::test_silent_source, ::test_silent_source_clears_when_delivery_resumes | Silence is detected and clears when deliveries resume. No test replays a day's backlog and asserts no duplicates in the same story. |
| P08 | partial | packages/reality-core/tests/test_unified_opening_stock.py::test_opening_review_adds_and_replay_is_inert; tests/finance/test_opening.py::test_four_directions_are_residual_positions_without_cash_or_turnover | Opening stock and opening open items are traceable. Open orders already partly delivered at go-live are not proven. |

## Q. Time and period

| ID | Status | Evidence | Note |
|---|---|---|---|
| Q01 | partial | tests/scenarios/test_normal_month.py::test_the_month_ends_with_exactly_these_exceptions | Shipped-not-invoiced is proven; the sales side has no invoiced-not-shipped class (billed_not_received is purchase side only). |
| Q02 | gap | specs/184-period-close/spec.md (stub, "no period record") | There's no period or close record, so a backdated posting is neither refused nor flagged. |
| Q03 | covered | tests/test_analysis_positions_history.py::test_detail_inventory_conserves_locations_and_unknown_tracking, ::test_later_stock_compensation_does_not_rewrite_earlier_snapshot, ::test_cutoff_excludes_next_midnight_and_late_allocation_endpoint | Point-in-time stock with an explicit cutoff is asserted, including that later corrections don't rewrite it. |
| Q04 | gap | specs/184-period-close/spec.md | With no period concept there is no carry-over; open promises simply stay open, and no test crosses a year boundary. |
| Q05 | partial | tests/test_operational_fields.py::test_document_and_commitment_operational_fields | Offset timestamps are proven to normalize to UTC; there is no company time zone, and no test pins the day a late-evening local order falls on (`domain/calendar.as_day` takes the text's local day). |

## R. Combined stress stories

| ID | Status | Evidence | Note |
|---|---|---|---|
| R01 | partial | tests/scenarios/test_fulfillment_safety_parity.py::test_two_order_story_keeps_unpaid_prepayment_stock_inside; tests/scenarios/test_b2b_operational_integrity.py::test_b2b_inventory_revision_return_and_cancellation_reconcile_exactly; tests/scenarios/test_procure_to_pay.py::test_procure_to_pay_business_story; tests/test_returns.py::test_return_disposition_reconciles_four_partial_outcomes | Prepayment gating, revise/cancel, partial receipt and damaged-return pieces exist separately; no one test reconciles every quantity and euro. |
| R02 | partial | tests/test_supply_assignments.py::test_customer_and_stock_supply_reconcile_without_implying_receipt, ::test_partial_reversal_is_append_only_and_idempotent; tests/test_incremental_derivation.py::test_a_cancelled_promise_leaves_the_demand_it_was_counted_in | `supply_assignments._effective_rows` ignores customer status, so a cancelled demand keeps its purchase assignment until someone reverses it by hand; there's no combined test. |
| R03 | gap | specs/242-inventory-cost-contribution/spec.md (drop shipping listed only as an edge case) | There is no drop-shipment model (supplier ships to the customer, no own stock). |
| R04 | gap | services/payment_intake.py (refuses references to several invoices); tests/test_payment_intake.py::test_two_invoices_for_one_order_and_a_consolidated_invoice_yield_no_allocation | There's no payout, fee or chargeback allocation across many orders. |
| R05 | partial | tests/test_commitment_revisions.py::test_a_promise_can_shrink_below_what_arrived, ::test_shrinking_to_what_arrived_finishes_the_promise | Revising after a partial fulfilment is proven on commitments; there's no EDI ORDCHG or advice source. |
| R06 | partial | docs/features/receipt-costing.md (freight/duty categories; FX excluded); tests/test_cost_allocation_services.py::test_weighted_preview_and_confirmation_retain_exact_existing_parts; tests/test_supply_assignments.py::test_customer_and_stock_supply_reconcile_without_implying_receipt | Freight/duty landed cost and customer assignment exist; USD rate conversion is out of the costing slice, and there's no combined container test. |
| R07 | partial | tests/operational_exceptions/test_derivation.py::test_reservation_exceeds_stock, ::test_reservation_exceeds_stock_impact, ::test_reservation_exceeds_stock_references_are_opaque | A stocktake loss surfaces the competing reservations (2, not 3), and by design no promise is named as postponed. |
| R08 | partial | tests/operational_exceptions/test_derivation.py::test_credit_limit_exceeded; tests/test_unified_customer_holds.py::test_customer_hold_http_actor_and_practice | credit_limit_exceeded sums open invoices only; it ignores the new order, available credit and payables, and no hold reason combines them. |
