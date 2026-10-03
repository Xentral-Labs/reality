# Business Scenario Coverage

Spec impact: none. This records test evidence for [catalog.md](catalog.md); it changes no behavior.

Assessed against `main` at 4dc658f9 (2026-09-26) by reading tests, services and specs; spec 292 (2026-09-28) proved A04, A06, A07, A19, C04, F01, F05, M08, N01, N02 and N06; spec 293 (2026-09-29) proved F07 with the customer exchange; spec 294 (2026-09-29) proved D16, G07, H03, I06, I07, K05, L06, O01, P04 and P07 and pinned R01; spec 299 (2026-10-01) proved E03, E11, C14 and Q01; spec 300 (2026-10-01) proved B14, L02 and L07; spec 301 (2026-10-01) proved O05; spec 302 (2026-10-01) proved G02; spec 303 (2026-10-01) proved A02, B06 and D02; spec 304 (2026-10-02) proved B05, J05, H08 and H15; spec 335 (2026-10-03) proved D07, D08 and D09; spec 336 (2026-10-02) proved L03, R04, C09, C10 and C13; spec 333 (2026-10-02) proved K01, K02, K04 and K06 and made K03 partial; spec 334 (2026-10-02) proved A08, A11, A21, A24, D04, D13 and M05; spec 337 (2026-10-03) proved D10, D11 and G15 and made R03 partial; spec 339 (2026-10-03) proved L10 and O02; spec 338 (2026-10-03) proved H04, H05, H06, H07, H17, G16 and D05; spec 340 (2026-10-03) proved Q04 and set L11 and Q02 out of scope; spec 344 (2026-10-03) proved J07. Rows
pointing at `tests/scenarios/test_catalog_*.py` were proven by running those tests. Evidence paths are relative to `packages/reality-core/` unless they
start with `packages/`, `specs/` or `docs/`. Re-measure a row before building on it.

## Summary

228 scenarios: 182 covered, 10 partial, 0 missing, 31 gap, 5 out.

| Section | covered | partial | missing | gap | out |
|---|---|---|---|---|---|
| A Order intake and changes | 20 |  |  | 4 |  |
| B Availability and reservation | 12 |  |  | 6 |  |
| C Payment and release | 17 |  |  | 1 |  |
| D Shipment, split and merge | 15 | 1 |  | 3 |  |
| E Customer invoice and credit | 12 |  |  |  |  |
| F Returns and complaints | 12 |  |  | 1 |  |
| G Purchase demand and order | 14 |  |  | 3 |  |
| H Receipt and supplier deviations | 19 |  |  |  |  |
| I Supplier invoice and payment | 12 |  |  |  |  |
| J Warehouse and stock | 7 | 1 |  | 3 |  |
| K Kits and variants | 5 | 1 |  |  |  |
| L E-commerce and marketplaces | 9 |  |  | 2 | 1 |
| M B2B specifics | 4 | 2 |  | 6 |  |
| N Finance, tax, currency | 5 |  |  | 1 | 2 |
| O Master data and identity | 4 |  |  | 1 | 1 |
| P Sources and integration | 7 | 1 |  |  |  |
| Q Time and period | 3 | 1 |  |  | 1 |
| R Combined stress stories | 5 | 3 |  |  |  |

Strongest where an operational exception class exists (at-risk, reservation_exceeds_stock,
shipped_not_billed, returned_not_credited, billed_not_received, duplicate supplier invoice) and in
finance settlement. Weakest in physical execution before dispatch, source interpretation beyond
Shopify, and B2B structures.

## Gap themes

Most of the 74 gaps come from a few structural decisions or absences, not from single cases.

1. **Nothing existed between reservation and dispatch.** Since spec 334 a planned outbound
   delivery states its recipient, address and booked slot, picking moves goods and their
   reservation into staging, and the shipment keeps where it went (A08, A11, A21, A24, D04, D13,
   M05). Pick lists by bin path, waves and handheld scanning are still not modelled.
2. **A movement had to match its commitment exactly.** Since spec 338 a receipt may state a
   surplus, a wrong item names the line it was meant for without fulfilling it, a buyer may
   accept a substitute for a purchase line, and an inbound notice states advised quantities per
   purchase line (H04, H05, H06, H07, H17, G16, D05). F03 stays related.
3. **A return never reopens a kept promise (spec 079).** Undeliverable, refused and lost parcels
   cannot be told apart from a customer return. D07, D08, D09. Since spec 335 they are failed
   deliveries: the shipment is reversed through the movement correction, the promise is open again,
   and a lost parcel may open a claim against the carrier.
4. **Drop shipping since spec 337.** A purchase order shipping to the customer is assigned to its line and the supplier's dispatch keeps both orders without touching stock (D10, D11, G15 covered); the wrong item a supplier sent cannot be named (R03 partial, see D05).
5. **No allocation policy.** Priority between promises, reserving by requested date, ship-complete,
   reservation lapse, channel quotas and shelf-life eligibility are all absent; spec 068 names
   allocation a non-goal. A12, B03, B11, B12, B15, B16, B17. Since spec 306 a customer or order states ship
   complete or no backorders (B10, M06). Since spec 305 a
   receipt is served through a reviewed proposal in a stated order (assigned first, then due date),
   and available-to-promise names the purchases it relies on (B07, B08, B09, H16). Since spec 303 a person can reserve the rest of a promise
   at another warehouse and each warehouse ships its part (D02), but nothing distributes a
   reservation across warehouses by itself.
6. **In-transit stock is not modelled.** Since spec 304 quarantine, inspection and expiry are stock
   blocks where the goods lie (B05, H08, H15, J05); stock on its way between locations still exists
   only as "move it to another location". J01.
7. **Shopify orders and refunds are interpreted, other sources are not.** Later Shopify versions
   apply reductions of unshipped quantity and hold everything else (specs 081, 296); refunds
   become evidence. Shipments, marketplace, 3PL and EDI sources have no interpreter.
   D17, M03 (L01, M04 partial). Since spec 336 a payout statement is stated through a reviewed
   command (L03); provider report formats are not read.
8. **No framework contracts or schedule lines.** One supplier commitment per PO line; no blanket
   order or call-off. A23, G04, G05, M01.
9. **Party roles and identity are thin.** No bill-to/payer role, supplier item numbers, or
   receivable/payable netting. M10, M11, O06. Duplicate partners are merged since spec 339
   (L10, O02 covered).
10. **Spec 148 trade finance is specified, not built.** Vouchers and the accounting export
    package. C18, N07. A person records chargebacks and returned direct debits since spec 297
    (C15 covered); since spec 336 a stated payout statement settles marketplace, provider and
    cash-on-delivery payouts, and authorizations and captures are recorded (C09, C10, C13, L03,
    R04 covered).
11. **Kits are one level deep since spec 333.** A returned component is not linked to its kit's delivery (K03 partial); component cost is not rolled into the kit.
12. **No accounting periods, by decision (spec 340).** Reality is not the bookkeeping system:
    there is no period close or posting lock (Q02 out), and open promises cross the year end
    unchanged (Q04 covered).
13. **Foreign currency on the purchase side only.** Supplier invoices and payments convert at
    stated rates and realise exchange differences (spec 309); sales in another currency,
    revaluation of open items and foreign payment runs are not converted. (N03 out.) Wherever
    Reality would have to convert, it names the other currency instead: the credit limit counts
    only its own currency and holds an order in another one for a person (spec 341); a payment
    is allocated only to an invoice in its currency, so a prepayment in another currency does not
    release the order; a contribution needs the invoice in the order's currency.
14. **Other single gaps:** loans and samples with a return obligation (M12), repair round trip
    (F10), returnable packaging (D19), subscriptions (L08), customs data (L12, D14), negative stock (J06 is refused by design),
    re-labelling pairs (J11), unconfirmed purchase orders (G10),
    quote documents (A14), variant swap on an
    open order (A10), customer delivery documents (M07).

Several gaps may be deliberate. They should become an explicit **out** with a reason in a scope
document rather than stay open (candidates: M07 labels, J06 negative stock). Tax determination (L11, N08) and accounting
periods (Q02) are out by spec 340.

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
- **R02 assignment survives cancellation (fixed in #205).** A cancelled customer promise kept its
  purchase supply assignment until someone reversed it by hand; since #205 it ends at read time,
  and spec 305 proves it in the R02 and G13 stories.

The combined stories R01, R02, R05, R06, R07 and R08 can be written today as end-to-end
scenario tests from existing pieces. Each will show whether the pieces reconcile together.

## A. Order intake and order changes

| ID | Status | Evidence | Note |
|---|---|---|---|
| A01 | covered | packages/reality-core/tests/scenarios/test_order_to_cash.py::test_order_to_cash_business_story | Shopify order is reserved with no shortage and shipped in two parts, then invoiced, partly paid and credited; open quantity and open amount are asserted, and the trace reaches the raw payload. |
| A02 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_an_order_with_many_lines_is_served_from_two_warehouses | Twelve lines, half stocked at home and half in Munich: the Munich lines are named, reserved there, all lines are ready and each warehouse ships its own lines in one parcel (spec 303). |
| A03 | covered | packages/reality-core/tests/test_unified_order_entry.py::test_multiline_review_trace_and_replay | The same `item_id` on two lines gives two commitments with their own amounts. The discounted-versus-free case itself is not tested. |
| A04 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_raising_the_quantity_after_a_partial_delivery_opens_only_the_rest | 10 ordered, 4 shipped, raised to 12 through the reviewed revision: 8 open, 4 delivered; the rest is reserved again and ships in full. |
| A05 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_customer_lowers_a_line_below_what_already_shipped | The revision stands, and Shipped beyond the order reports the excess until it comes back or the line is raised again (spec 313). |
| A06 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_cancelling_one_line_leaves_the_other_lines_open_and_reserved | Reviewed cancellation of one of three reserved lines: only that line is cancelled and unreserved; the other two stay open with their reservations. |
| A07 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_cancelling_every_line_of_a_reserved_order_releases_all_its_stock | Every line of a reserved two-item order cancelled through the reviewed action: no active reservation remains and stock is unchanged. |
| A08 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_an_order_cancelled_after_picking_goes_back_to_its_bin | Picking moves the goods into staging; after the cancellation they show as to put back until the put-back returns them to the bin (spec 334). |
| A09 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_a_cancellation_after_shipment_becomes_an_expected_return | After shipment the cancellation cancels nothing, waits with cancelled_after_shipment naming return_announce, and a confirmed announcement expects the goods back (spec 296). |
| A10 | gap | packages/reality-core/tests/test_document_corrections.py::test_manual_line_economic_changes_lock_after_reality_but_description_remains_correctable | Adding a line is blocked once Reality exists, and Shopify changes are held for review, so no path swaps a variant on the same order while keeping its history. |
| A11 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_changed_address_before_shipment_is_the_one_used | A revision before dispatch states the new address; both statements are kept and the shipment keeps the one it used (spec 334). |
| A12 | gap | packages/reality-core/src/reality/services/core.py::reserve | Reservation is explicit, and no rule uses `due_at` or `requested_delivery_at` to decide when to reserve. |
| A13 | covered | tests/scenarios/test_catalog_orders_and_shipments.py::test_each_order_line_keeps_its_own_promised_date | Two lines carry their own promised date; a third falls back to the order's requested delivery date. |
| A14 | gap | packages/reality-core/src/reality/services/core.py::MANUAL_OPERATIONAL_DOCUMENT_TYPES | There is no quote document type and no quote-to-order link. Spec 259 is a pricing preview only. |
| A15 | covered | packages/reality-core/tests/test_shopify_and_explain.py::test_shopify_ingestion_is_lossless_idempotent_and_traceable | Re-sending the payload with its keys reordered still gives exactly one SourceRecord, Document and Commitment. |
| A16 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_a_new_shop_version_revises_the_promise_and_keeps_the_old_version | A second version lowering a line revises the promise citing the version, releases the reservation above it, and keeps the first version as evidence (spec 296). |
| A17 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_a_shop_order_with_an_unknown_item_keeps_the_known_lines | Known lines are promised, the unknown line is kept and reported by order_line_item_unknown, and a reviewed assignment creates its promise (spec 296). |
| A18 | covered | packages/reality-core/tests/test_pricing.py::test_document_line_retains_agreed_entry_when_current_price_changes, ::test_manual_agreement_remains_valid_without_pricing_entry | The stated price is kept against the list price. Order entry also keeps a stated gross of 24.91 against 2 x 12.50. |
| A19 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_zero_price_line_ships_and_is_invoiced_without_revenue | A zero-price line beside a priced one is reserved, shipped and invoiced at zero through document_create and sales_invoice_post; revenue is the priced line only and shipped_not_billed clears (positive control first). |
| A20 | covered | tests/scenarios/test_catalog_orders_and_shipments.py::test_one_shipment_fulfils_two_orders_of_the_same_customer | One shipment and one package fulfil two orders (3 and 5); 8 promised, 8 dispatched. |
| A21 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_one_order_goes_to_two_addresses | One promise split across two planned deliveries up to what is open, each shipment with its own address (spec 334). |
| A22 | covered | packages/reality-core/tests/test_commitment_holds.py::test_hold_blocks_reservation_and_movement_until_released, ::test_the_release_is_recorded_by_the_release_operation; tests/operational_exceptions/test_derivation.py (`commitment_hold_unreleased`) | The hold's reason code blocks execution, the release is recorded, and an unreleased hold is surfaced. |
| A23 | gap | (see M01); no blanket or call-off concept in src/reality | There is no frame-contract or call-off structure. |
| A24 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_line_added_later_rides_with_the_open_delivery | A follow-up order's promise joins the open planned delivery and ships in the same shipment (spec 334). |

## B. Availability, reservation and backorder

| ID | Status | Evidence | Note |
|---|---|---|---|
| B01 | covered | packages/reality-core/tests/test_inventory_and_fulfillment.py::test_shortage_reservation_and_release; tests/test_application_tools.py::test_reservation_receipts_classify_none_partial_and_complete | Reserving 30 against 20 on hand reserves 20 and reports 10 short; the receipt reports `effect=partial` with `remaining_work`. |
| B02 | covered | tests/operational_exceptions/test_derivation.py::test_outgoing_commitment_at_risk; tests/test_application_tools.py::test_reservation_receipts_classify_none_partial_and_complete | With no stock the whole promise is `outgoing_commitment_at_risk` (cause insufficient_reservation), and the receipt reports `effect=none`. |
| B03 | gap | specs/068-promise-coverage-exceptions/spec.md (Non-Goals); tests/operational_exceptions/test_derivation.py::test_reservation_exceeds_stock_impact | No allocation or priority rule exists: whoever reserves first gets the units, and only a `competing_commitments` count is reported. |
| B04 | covered | tests/scenarios/test_catalog_stock_and_returns.py::test_stock_reserved_for_one_customer_can_be_moved_to_a_more_important_one | Release then reserve moves the stock with exact per-commitment figures and ordered events. Nothing links the two steps unless the caller passes one action id. |
| B05 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_blocked_stock_is_not_available_until_quality_releases_it | 20 in stock, 5 blocked for quality: an order of 20 reserves 15; quality releases the 5 with its reason and the order reserves all 20 (spec 304). |
| B06 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_stock_in_the_wrong_warehouse_is_transferred_and_then_reserved | All stock in Munich: the finding names it, the reviewed transfer moves five home, the finding clears, and the order reserves and ships at home (spec 303). |
| B07 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_stock_only_on_order_is_promised_by_its_purchase_date | No stock and a purchase of 10 due 12 Oct with 4 assigned: available-to-promise shows nothing now and 6 more from 12 Oct, naming the purchase and supplier (spec 305). |
| B08 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_receipt_serves_the_earlier_due_backorder_first | Two orders of 3 wait and 4 arrive: Serve backorders proposes 3 for the one due first and 1 for the other, reserves nothing until a person confirms, and only the second stays at risk (spec 305). |
| B09 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_partial_receipt_names_the_backorders_left_uncovered | A receipt of 4 against 3 + 3 + 3 shows 3/0, 1/2 and 0/3 arrived and still to come; serving reserves 3 and 1 and the other two stay at risk (spec 305). |
| B10 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_customer_who_refuses_partial_delivery_gets_the_whole_order_at_once | Ship complete stated for the customer: the reserved bikes wait with the blocker named, a partial shipment is refused, Order waiting for completeness names the missing lamps, and the whole order ships together (spec 306). |
| B11 | gap | services/fulfillment_readiness.py (blocker set) | No per-order or per-customer limit on partial deliveries or parcel count exists. |
| B12 | gap | db/core.py `Reservation` (no deadline column); tests/scenarios/test_fulfillment_safety_parity.py::test_two_order_story_keeps_unpaid_prepayment_stock_inside | Prepayment only blocks shipment; a reservation has no lapse date and is never released automatically. |
| B13 | covered | tests/operational_exceptions/test_derivation.py::test_reservation_exceeds_stock, ::test_reservation_exceeds_stock_references_are_opaque | A stocktake loss raises `reservation_exceeds_stock` naming the reservations; it is judged per item across locations and blames no single promise. |
| B14 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_an_item_oversold_in_the_shop_and_on_a_marketplace_names_both | An item sold in the shop and on a marketplace beyond stock and supply is reported with both channels; a purchase order covers it (spec 300). |
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
| C04 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_one_payment_releases_two_prepaid_orders | One confirmed settlement payment of 200 is booked on the first prepayment invoice and allocated to the second; both invoices close and both orders become ship-ready. |
| C05 | covered | tests/test_payment_intake.py::test_candidates_have_reasons_and_write_nothing; ::test_ambiguous_reference_produces_candidates_and_allocation_ends_them | Money is recorded unallocated, tier-3 candidates carry reasons and write nothing, and an explicit allocate_settlement ends them. |
| C06 | covered | tests/scenarios/test_catalog_finance.py::test_payment_after_a_cancelled_prepayment_order_stays_credit_and_is_refunded | Payment after cancellation stays unallocated as customer credit (119) and is refunded through the confirmed settlement proposal. |
| C07 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_an_order_over_the_limit_is_held_and_released_by_an_owner | An order past the credit limit is held at entry with the facts; an owner releases it with a reason recorded with the person (spec 298). An order in another currency than the limit is held for a person rather than converted (spec 341). |
| C08 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_the_credit_hold_names_the_overdue_items_behind_it | The hold and the credit-limit finding name the overdue invoices apart from those not yet due, on an exposure that counts open orders and credits (spec 298). |
| C09 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_authorization_and_capture_are_separate_facts | An authorization of 100 is captured as 60 and 40 through reviewed commands; authorized, captured and left are read apart, and a further capture is refused (spec 336). |
| C10 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_an_expired_authorization_shows_the_uncovered_rest_of_a_late_shipment | 600 of 1000 captured with the first parcel; the authorization lapses before the rest ships, Payment authorization expired names the uncovered 400, and a new authorization clears it (spec 336). |
| C11 | covered | tests/test_payment_terms.py::test_the_discount_deadline_is_one_shared_rule; tests/test_ledger.py::test_invoice_due_date_rule | Due date and discount date come from one shared rule in the aging register; the fixture is a supplier invoice, and sales invoices use the same rule. |
| C12 | covered | tests/operational_exceptions/test_derivation.py::test_a_discount_taken_explains_the_remainder | A discount deducted after the window gets no `early_payment_discount_taken` reason, so it stays a plain overdue receivable. |
| C13 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_cash_on_delivery_is_tied_to_the_parcel_it_was_collected_for | The carrier's remittance is a payout whose line states the parcel's tracking number; it pays the order's invoice and the payout read names the shipment. The shipment does not state the amount to collect (spec 336). |
| C14 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_a_30_percent_down_payment_holds_the_shipment_until_the_rest_is_paid | A paid 30 % down-payment invoice counts towards the prepayment, the shipment waits for the rest, and the final invoice offsets the down payment (spec 299). |
| C15 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_a_returned_direct_debit_reopens_the_invoice_and_charges_the_fee | A returned direct debit or chargeback is recorded with its stated reason and fee; the invoice reopens and is reported until paid again, the fee is an expense or charged on (spec 297). Bank return files and provider disputes are not read. |
| C16 | covered | tests/test_party_delivery_holds.py::test_customer_delivery_hold_blocks_only_shipment; tests/test_fulfillment_readiness.py::test_readiness_combines_stock_reservation_and_active_hold | A party hold with reason and note blocks only shipments; readiness names the hold. There is no dedicated dunning or insolvency reason code. |
| C17 | covered | tests/test_commitment_holds.py::test_hold_blocks_reservation_and_movement_until_released; ::test_the_release_is_recorded_by_the_release_operation | Hold and release are both recorded generically (`compliance`/`manual_review`); there is no fraud reason and no hold driven by a source fraud signal. |
| C18 | gap | services/finance/settlement.py REASONS (no voucher) | Vouchers and gift cards are not a settlement instrument; only cash, credit notes, deposits and the four adjustment reasons exist. |

## D. Picking, shipment, split and merge

| ID | Status | Evidence | Note |
|---|---|---|---|
| D01 | covered | packages/reality-core/tests/test_inventory_and_fulfillment.py::test_partial_shipments_derive_fulfillment_and_consume_reservations | Asserts fulfilled 10 / open 20, then fulfilled after the remainder ships; the remaining reservation is used up too. |
| D02 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_two_warehouses_ship_one_order_line_as_two_parcels | Six reserved at home and four in Munich for one line: ready to ship, two parcels from their own warehouses fulfil the one promise (spec 303). |
| D03 | covered | tests/scenarios/test_catalog_orders_and_shipments.py::test_one_package_carries_several_commitments_of_one_customer | One package fulfils three commitments over two items by their own quantities (0, 0 and 1 open). |
| D04 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_picking_error_is_caught_before_shipment | An over-pick is refused before anything moves; a wrong pick goes back by a put-back; the dispatch waits until the delivery is picked (spec 334). |
| D05 | covered | packages/reality-core/tests/scenarios/test_catalog_receipt_deviations.py::test_a_picking_error_found_by_the_customer | The recorded shipment is corrected to the bells that left, meant for the line: the line is open again, both stocks are true, Wrong item delivered names the line until the bells come back, and the lights ship (spec 338). |
| D06 | covered | packages/reality-core/tests/operational_exceptions/test_derivation.py::test_reservation_exceeds_stock | A stocktake-loss adjustment raises reservation_exceeds_stock with the shortfall; the entry clears on receipt. |
| D07 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_lost_parcel_is_claimed_from_the_carrier_and_sent_again | A lost parcel is a failed delivery: the shipment no longer counts, the goods stay written off, the promise is open again, and a claim against the carrier is an open receivable its payment settles (spec 335). |
| D08 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_an_undeliverable_parcel_comes_back_and_is_sent_again | An undeliverable parcel is a failed delivery, not a return: stock is back, the promise is open again, and the issued invoice is invoiced and not shipped until the order ships again (spec 335). |
| D09 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_refused_delivery_keeps_the_reason_and_the_rest_is_cancelled | A refused delivery keeps its stated reason on the shipment; the promise is open again and here the customer's withdrawal cancels it (spec 335). |
| D10 | covered | packages/reality-core/tests/scenarios/test_catalog_drop_shipping.py::test_the_supplier_ships_straight_to_the_customer | A purchase shipping to the customer, assigned to the line; the reviewed drop shipment keeps both orders with a tracked shipment and leaves stock unchanged (spec 337). |
| D11 | covered | packages/reality-core/tests/scenarios/test_catalog_drop_shipping.py::test_one_order_is_served_partly_from_stock_and_partly_by_the_supplier | 6 shipped from stock and 4 drop-shipped keep one order of 10 in full; stock ends at 0 (spec 337). |
| D12 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_3pl_confirms_on_thursday_what_left_on_monday | Movements carry when the goods left; the shipment shows when it was recorded and the lag, and overdue clears (spec 312). |
| D13 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_pallet_freight_ships_with_its_booked_slot | The planned delivery states its booked slot, the shipment keeps it, and a slot that closed unshipped shows as missed (spec 334). |
| D14 | gap | db/core.py Shipment/Document (no customs or export-proof link) | Export evidence could only sit in a lossless payload; nothing typed links it to the shipment. |
| D15 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_customer_collects_the_order_at_the_counter | A pickup is a stated delivery mode with who collected, without carrier (spec 312). |
| D16 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_free_replacement_ships_without_an_order_and_explains_itself | Free replacement recorded as an advance customer exchange against the announced faulty unit: a document-less zero-amount promise is reserved, shipped and explained; only the original unbilled order line is reported (positive control). |
| D17 | gap | packages/reality-core/src/reality/services/core.py SOURCE_INTERPRETERS (no shipment interpreter) | No shipment source is interpreted, so nothing holds an early confirmation and links it later. |
| D18 | partial | tests/test_shipment_actions.py::test_receive_confirmation_replays_one_atomic_package; tests/test_unified_delivery_actions.py::test_same_preparation_and_confirmation_have_one_effect | Replaying a proposal is idempotent. A duplicate shipment report from a source is never ingested, so that case is untested. |
| D19 | gap | db/core.py (no deposit or returnable-packaging concept) | Nothing tracks returnable packaging or the deposit owed. |

## E. Customer invoice and credit note

| ID | Status | Evidence | Note |
|---|---|---|---|
| E01 | covered | tests/operational_exceptions/test_derivation.py::test_shipped_not_billed; ::test_billing_sums_across_invoices | Unbilled quantity per order line falls to zero as partial invoices arrive. |
| E02 | covered | tests/scenarios/test_catalog_finance.py::test_one_monthly_invoice_bills_the_deliveries_of_three_orders | The month's deliveries of three orders are read from `invoice_billable_positions` and billed on one guided invoice; `shipped_not_billed` clears and nothing remains billable (spec 283). |
| E03 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_a_proforma_and_an_early_invoice_are_visible_until_the_goods_ship | A pro-forma is evidence only; an invoice before shipment is reported as invoiced and not shipped until the goods ship (spec 299). |
| E04 | covered | tests/test_partial_invoicing_rebilling.py::test_partial_reversal_rebilling_and_historical_proof; tests/test_ledger_reversals.py::test_reversal_appends_exact_inverse_and_preserves_original | The exact inverse is appended and the original stays; billing becomes available again for the new invoice. |
| E05 | covered | tests/test_unified_invoice_credit.py::test_partial_multi_credit_without_return_and_exact_recovery; ::test_financial_credit_does_not_require_return_exception | The receivable drops with zero Movements and no `credited_not_returned`. |
| E06 | covered | tests/operational_exceptions/test_derivation.py::test_returned_not_credited; ::test_invoice_linked_credit_clears_returned_not_credited_through_shortest_links | Return and credit meet on the order line through the shortest links, not through a direct link from the credit to the return movement. |
| E07 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_an_invoice_that_differs_from_the_order_is_reported_each_way | Over-billing, under-billing and another price are each reported per line (specs 299, 313). |
| E08 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_freight_surcharge_and_a_deducted_payment_fee_stay_apart_from_the_goods | Freight and surcharge lines on a sales invoice are no goods finding; a fee the provider deducts settles the invoice as payment-fee expense (spec 297). |
| E09 | covered | tests/scenarios/test_catalog_finance.py::test_invoice_billed_to_the_orderer_keeps_a_different_ship_to_party | Invoice, AR and balance name the orderer; ship-to is reachable through the billed order line. The invoice document itself carries no ship-to. |
| E10 | covered | tests/scenarios/test_catalog_finance.py::test_e_invoice_xml_is_stored_losslessly_as_traceable_source_evidence | XRechnung bytes (BOM, CRLF, umlauts) round-trip exactly with hash and size; the source stays unmapped, no interpreter exists. |
| E11 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_the_final_invoice_states_the_down_payment_it_deducts | A down-payment invoice is paid and offset in the final invoice by a stated amount; both name each other (spec 299). |
| E12 | covered | tests/test_multi_position_invoices.py::test_stated_values_and_recovery; tests/test_credit_notes.py::test_the_stated_total_is_what_posts; tests/test_documents.py::test_recording_requires_a_stated_total | The header total (209.1234) is kept and posted independently of the line amounts. |

## F. Returns and complaints

| ID | Status | Evidence | Note |
|---|---|---|---|
| F01 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_a_b2c_withdrawal_brings_the_goods_back_and_refunds_in_full | Paid delivery, full return, reviewed credit citing the invoice line, reviewed refund: stock back, invoice, credit, receivable and cash at 0, no return or billing signal (positive control first). |
| F02 | covered | tests/operational_exceptions/test_derivation.py::test_returned_goods_are_not_reported_as_unbilled, ::test_returned_not_credited | Returned 4 or 6 against kept quantity is asserted through shipped_not_billed and returned_not_credited. |
| F03 | covered | tests/scenarios/test_catalog_stock_and_returns.py::test_a_different_item_returned_does_not_fulfil_the_announcement | A foreign item cannot fulfil the announcement; it stands unexplained, and the announcement stays outstanding until the announced item arrives. |
| F04 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_an_unannounced_return_is_linked_to_its_delivery_later | An unannounced return is reported, linked to its delivery by a reviewed correction and settled by a credit (spec 314). A correction cannot fulfil an announcement. |
| F05 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_a_damaged_return_is_disposed_and_credited_independently | Two back, one restocked and one scrapped through reviewed dispositions; full-quantity credit with a damage charge line, refunded; dispositions and credit each reconcile with no signal (positive control first). |
| F06 | covered | tests/test_returns.py::test_return_disposition_reconciles_four_partial_outcomes; tests/scenarios/test_b2b_operational_chain.py::test_supply_and_return_reconciliations_are_exact | Arrived 5 = restock 2 + quarantine 1 + scrap 1 + back to supplier 1; over-disposition is refused. |
| F07 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_an_exchange_returns_one_unit_and_sends_another_without_money | A paid delivery is returned and exchanged for a larger size through the reviewed exchange tool (spec 293): the free replacement ships and no credit, invoice, payment or refund exists, with no finding. |
| F08 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_a_goodwill_refund_is_paid_while_the_return_is_still_expected | Credit and refund paid ahead of the goods; the announced return stays expected, is reported when overdue and fulfilled on arrival (spec 314). A credit through the invoice is not counted by credited_not_returned. |
| F09 | covered | tests/operational_exceptions/test_derivation.py::test_announced_return_not_arrived, ::test_an_announcement_with_no_stated_day_is_judged_by_the_learned_rhythm | A stale announcement is reported by the stated date or the learned rhythm, and clears on arrival. |
| F10 | gap | packages/reality-core/src/reality/services/return_dispositions.py (return_to_supplier is terminal) | Goods cannot go out for repair and come back while staying owned. |
| F11 | covered | tests/operational_exceptions/test_derivation.py::test_credited_not_returned (first assertion); tests/scenarios/test_international_demo.py price_only_credit | A credit with no return raises nothing ("a decision, not a discrepancy"); the price-only allowance reduces the invoice. |
| F12 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_a_refund_before_the_goods_come_back_keeps_the_return_expected | A Shopify refund stating a return announces it; it stays outstanding with no credit finding until the goods arrive (spec 296). |
| F13 | covered | tests/scenarios/test_catalog_finance.py::test_return_credit_after_month_end_books_in_the_next_month | Invoice ledger entries fall in August, the credit in September, by stated dates. |

## G. Purchasing: demand and purchase order

| ID | Status | Evidence | Note |
|---|---|---|---|
| G01 | covered | packages/reality-core/tests/test_supply_assignments.py::test_customer_and_stock_supply_reconcile_without_implying_receipt; tests/scenarios/test_b2b_operational_chain.py::test_supply_and_return_reconciliations_are_exact | An explicit `customer_demand` assignment links the PO commitment to the customer commitment (`protecting_supply`). |
| G02 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_reorder_for_stock_at_the_reorder_point | A reorder point of 20 and quantity of 48 per warehouse: only Hamburg at 12 is proposed, 4 cartons from the one listed supplier at 54; the reviewed purchase order covers it and the entry clears; raising the point brings it back with 48 incoming (spec 302). |
| G03 | covered | tests/scenarios/test_b2b_operational_chain.py::test_supply_and_return_reconciliations_are_exact | Asserts 10 = 6 customer + 2 stock + 2 unassigned for PO-010. |
| G04 | gap | src/reality/db/core.py `uq_commitment_document_line_type` | Only one supplier_delivery commitment is allowed per PO line, so several schedule lines per line cannot be represented. |
| G05 | gap | — | No framework agreement or call-off concept exists. |
| G06 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_minimum_and_a_pack_size_are_named_and_the_surplus_is_stock | Minimum and multiple per supplier and item are named in the review; the surplus stays free stock (spec 310). |
| G07 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_supplier_tier_price_is_kept_and_a_different_price_is_reported | Purchase price list with a 10-unit tier; the order line takes the tier entry; the guided supplier invoice is kept as stated with no finding; a second invoice at the single-unit tier recorded through document_create is reported as invoice_price_differs. |
| G08 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_usd_purchase_is_invoiced_at_its_stated_rate | A USD purchase keeps its currency; its invoice is posted at the stated rate with both amounts on every entry (spec 309). |
| G09 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_supplier_confirms_less_later_and_dearer_and_is_billed_as_confirmed | A confirmation restates quantity, date and price; the invoice follows the confirmed price (spec 310). |
| G10 | gap | — | No acknowledgement expectation, so an unconfirmed PO is never flagged (only overdue after the due date). |
| G11 | covered | tests/test_commitment_revisions.py::test_a_new_date_never_erases_the_old_one, ::test_the_date_in_force_is_the_latest_stated | Append-only revisions; the latest one is in force. |
| G12 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_purchase_cancelled_after_production_records_the_suppliers_charge | The cancellation charge is a supplier invoice against the cancelled line, without purchase findings (spec 310). |
| G13 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_cancelled_order_frees_its_purchase_before_the_purchase_is_reduced | Cancelling the order ends its assignment, so all 10 of the purchase are unassigned and promisable; the reviewed revision to 6 then reduces the purchase (spec 305). |
| G14 | covered | tests/scenarios/test_catalog_purchasing.py::test_two_suppliers_purchases_together_protect_one_customer_promise | 6 + 4 from two suppliers protect a demand of 10. Defect found: protection could reach 11 of 10; fixed in #201. |
| G15 | covered | packages/reality-core/tests/scenarios/test_catalog_drop_shipping.py::test_a_drop_ship_purchase_order_is_linked_to_the_customer_order | The purchase order states the customer as ship-to and is assigned to the order line; the line is no longer at risk and nothing is incoming to the warehouse (spec 337). |
| G16 | covered | packages/reality-core/tests/scenarios/test_catalog_receipt_deviations.py::test_one_container_shows_in_transit_per_purchase | One container notice advises three purchase orders: each order's three-way match shows its quantity in transit until the container is received into that shipment (spec 338). |
| G17 | covered | tests/operational_exceptions/test_derivation.py::test_non_deliverable_lines_are_never_reported; tests/test_free_supplier_invoice.py::test_free_supplier_invoice_is_source_backed_atomic_and_has_no_stock_effect | A PO line with no commitment expects no receipt. |

## H. Goods receipt and supplier deviations

| ID | Status | Evidence | Note |
|---|---|---|---|
| H01 | covered | tests/scenarios/test_procure_to_pay.py::test_procure_to_pay_business_story | Fulfilled 20 of 20 through two receipts. |
| H02 | covered | tests/test_unified_receipt_release.py::test_partial_receipt_review_replay_and_trace; tests/scenarios/test_storyline_purchase_to_pay.py (receipt/rest-receipt) | Open remainder 5 after 3 of 8. |
| H03 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_an_under_delivery_is_closed_with_its_reason_and_decision | 7 of 10 received and overdue (positive control), then a reviewed commitment_revise to 7 with a note: nothing open, not overdue, the revision keeps its note and the decision trail names the proposal. |
| H04 | covered | packages/reality-core/tests/scenarios/test_catalog_receipt_deviations.py::test_an_over_delivery_is_received_and_kept | 105 received for 100 with the surplus stated: Received beyond the order reports 5 until the line is raised to 105 (spec 338). |
| H05 | covered | packages/reality-core/tests/scenarios/test_catalog_receipt_deviations.py::test_an_over_delivery_goes_back_to_the_supplier | 110 received for 100; ten go back to the supplier against the purchase line, which clears the surplus (spec 338). |
| H06 | covered | packages/reality-core/tests/scenarios/test_catalog_receipt_deviations.py::test_a_wrong_item_is_tied_to_its_purchase_and_sent_back | Bells received meant for an order of lights: the line stays open, Wrong item delivered names it, and the bells going back against the line clear it (spec 338). |
| H07 | covered | packages/reality-core/tests/scenarios/test_catalog_receipt_deviations.py::test_a_successor_item_is_accepted_against_the_purchase | The buyer accepts the successor for the purchase line; its receipt fulfils the line and the three-way match names the substitute (spec 338). |
| H08 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_damaged_goods_are_received_blocked_and_scrapped | A reviewed receipt of 20 blocks 5 damaged in the same confirmation: 15 available; scrapping the 5 leaves 15 physical (spec 304). |
| H09 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_receipt_without_a_purchase_order_says_why_it_arrived | A receipt without a purchase keeps its stated reason and is explained by it; a delivery-path receipt without one is reported (spec 314). |
| H10 | covered | tests/scenarios/test_catalog_purchasing.py::test_one_inbound_package_is_split_across_several_purchase_orders | One package receives 5 for PO-A and 4 for PO-B; shipment_explain reports 9. |
| H11 | covered | tests/scenarios/test_catalog_purchasing.py::test_early_receipt_fulfils_the_purchase_and_keeps_its_due_date | Receipt before the due date fulfils the purchase and keeps the due date; no read names a receipt "early", it is derivable. |
| H12 | covered | tests/scenarios/test_catalog_purchasing.py::test_receipt_before_purchase_order_is_linked_later_by_replacement | An unexplained receipt is linked to the later PO by correct_movement; stock unchanged, PO fulfilled, exception cleared. |
| H13 | covered | tests/test_inventory_tracking_reservations.py::test_lot_quantity_can_be_received_reserved_and_shipped_on_a_pallet, ::test_a_lot_carries_the_stated_best_before; tests/scenarios/test_international_demo.py (SER-0001 receipt) | Lot, expiry and serial on receipt, though not against a PO commitment. |
| H14 | covered | tests/test_movement_corrections.py::test_void_receipt_appends_exact_correction_and_preserves_original | A compensating movement; the original is preserved. |
| H15 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_a_receipt_awaiting_inspection_is_released_days_later | A package of 12 received blocked for inspection reserves nothing; quality releases 10 and the order reserves them (spec 304). |
| H16 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_customer_specific_purchase_goes_to_its_order | A purchase assigned to an order due 25 Oct is served to it first on receipt, before an order due 10 Oct, once a person confirms (spec 305). |
| H17 | covered | packages/reality-core/tests/scenarios/test_catalog_receipt_deviations.py::test_advised_and_received_differ_by_four | 100 advised, 96 received into the announced shipment: the shipment reads advised 100, received 96, difference 4 (spec 338). |
| H18 | covered | tests/operational_exceptions/test_derivation.py::test_supplier_return_not_credited, ::test_supplier_credit_not_returned; tests/test_returns.py::test_goods_go_back_to_the_supplier | Return and credit reconciled per PO line. |
| H19 | covered | tests/test_costing_services.py::test_receipt_a_and_retained_review_survive_late_cost | Late duty makes the reviewed receipt cost stale; the old manifest is kept. |

## I. Supplier invoice and payment

| ID | Status | Evidence | Note |
|---|---|---|---|
| I01 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_purchase_receipt_and_invoice_that_agree_are_matched | A positive three-way match per purchase line, and the difference where it is not (spec 310). |
| I02 | covered | tests/operational_exceptions/test_derivation.py::test_received_but_not_yet_billed_is_not_reported; tests/scenarios/test_storyline_purchase_to_pay.py (billed_not_received raised/cleared) | |
| I03 | covered | tests/scenarios/test_storyline_purchase_to_pay.py::test_the_default_path_raises_and_clears_every_finding_by_rule | `invoice_price_differs` on the supplier invoice remains at month end. |
| I04 | covered | tests/operational_exceptions/test_derivation.py::test_billed_not_received | Billed 6, received 0, clears on receipt. |
| I05 | covered | tests/scenarios/test_catalog_purchasing.py::test_one_supplier_invoice_bills_lines_of_two_purchase_orders | One guided supplier invoice bills lines of two purchase orders, allocated per purchase (spec 283). |
| I06 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_several_partial_supplier_invoices_are_summed_against_the_purchase | 8 of 10 received; guided supplier invoices of 6 (no finding) and 4 sum to 10 and billed_not_received reports 2; a third guided invoice is refused with invoice_quantity_exceeds_billable. |
| I07 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_carrier_freight_invoice_is_attributed_to_the_receipt_cost | A carrier other than the goods supplier bills freight through supplier_invoice_free_record with stated net; the owner assigns it as inbound_freight to the receipt through cost.change; the receipt's known cost is 20.00. |
| I08 | covered | tests/test_credit_notes.py::test_netting_leaves_the_remainder_open; tests/scenarios/test_storyline_purchase_to_pay.py::test_the_credit_branch_pays_less_and_keeps_the_quantity_finding | |
| I09 | covered | tests/finance/test_commercial_edges.py::test_deposit_is_explicit_credit_and_clears_final_invoice[supplier] | The deposit is not linked to the PO. |
| I10 | covered | tests/scenarios/test_storyline_purchase_to_pay.py (discount-full, credit-allocate, discount-net); tests/test_ledger.py::test_supplier_invoice_and_partial_payment_leave_open_payable | |
| I11 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_a_usd_invoice_paid_in_eur_realises_its_exchange_difference | A USD invoice paid in EUR in two parts realises a loss and a gain against its invoice rate and leaves nothing open (spec 309). |
| I12 | covered | tests/operational_exceptions/test_derivation.py::test_duplicate_supplier_invoice; tests/test_payment_runs.py::test_the_duplicate_rule_has_one_home; tests/test_ledger.py::test_duplicate_invoice_posting_and_overpayment_are_rejected | Detected, and payment runs refuse it. |

## J. Warehouse and stock

| ID | Status | Evidence | Note |
|---|---|---|---|
| J01 | gap | docs/features/movements.md (transfer has both source and destination) | A transfer is one instant movement with no in-transit state; spec 242 FR-008 mentions transit for valuation only. |
| J02 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_a_count_posts_its_gain_and_its_loss | A count of 17 and 9 against 20 and 8 shows the book beside each line and posts -3 and +1 in one confirmation, each adjustment linked to its count line (spec 307). |
| J03 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_a_cycle_count_during_operation_keeps_the_picks_after_it | A line counted at 10:00 is posted against the book then; a pick of 2 at 10:30 stays, so the bin is never frozen (spec 307). |
| J04 | covered | tests/test_inventory_and_fulfillment.py::test_transfer_return_and_reasoned_adjustment_reconcile_by_location, ::test_adjustment_requires_reason | A write-off adjustment requires a reason and reconciles by location; the reason is free text, not a code. |
| J05 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_an_expired_lot_is_blocked_from_its_finding_and_scrapped | An expired lot is named with its location, blocked from the finding (which then clears) and scrapped (spec 304). |
| J06 | gap | services/core.py ("Movement exceeds physical stock."); tests/test_inventory_and_fulfillment.py::test_cannot_ship_more_than_stock | Outbound movements above physical stock are refused, so negative stock cannot occur or be explained. |
| J07 | covered | packages/reality-core/tests/scenarios/test_catalog_external_stock.py::test_a_3pl_stock_report_that_differs_is_visible_until_resolved | A 3PL's report is stated without moving stock and compared with Reality's stock at the stated time; External stock differs names both quantities until a count at that time, the missing movement or a matching report resolves it (spec 344). |
| J08 | covered | tests/scenarios/test_catalog_stock_and_returns.py::test_consignment_stock_at_a_customer_site_stays_counted_as_ours | Stock at a consignment location stays in the company total and is available only there. Ownership and valuation are not asserted (a location has no party link). |
| J09 | partial | tests/test_inventory_costing_services.py::test_inventory_two_owner_receipt_excludes_consigned_stock | Valuation leaves out the supplier-owned part of a receipt; physical stock and availability do not distinguish owner. |
| J10 | covered | tests/test_inventory_costing_services.py::test_inventory_late_cost_requires_receipt_review_and_preserves_old_basis | Late inbound freight re-derives acquisition value (420 → 440) after a fresh review and keeps the old basis. |
| J11 | gap | docs/features/movements.md (movement types) | Re-labelling can only be two unrelated adjustments; no relation pairs the out-movement of A with the in-movement of B. |

## K. Kits, bills of material and variants

| ID | Status | Evidence | Note |
|---|---|---|---|
| K01 | covered | packages/reality-core/tests/scenarios/test_catalog_kits.py::test_a_kit_is_sold_and_shipped_from_its_components | Availability is the free kits plus what the free parts build, limited by the scarcest part; packing assembles the kit, which then ships as itself (spec 333). |
| K02 | covered | packages/reality-core/tests/scenarios/test_catalog_kits.py::test_a_kit_missing_one_component_is_held_back_whole | One part short refuses the whole assembly naming it; nothing is consumed and the order waits whole (spec 333). |
| K03 | partial | packages/reality-core/tests/scenarios/test_catalog_kits.py::test_a_single_component_comes_back_from_a_kit | The part comes back to stock and its credit share is read from the split, but the return is not linked to the kit's delivery and reads as Unexplained movement (spec 333). |
| K04 | covered | packages/reality-core/tests/scenarios/test_catalog_kits.py::test_a_light_assembly_consumes_components_and_produces_the_item | One reviewed assembly writes paired movements under one statement; they are not corrected one by one. Cost is not rolled up (spec 333). |
| K05 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_variants_bought_together_each_hold_and_reserve_their_own_stock | Three sizes on one purchase, one receipt; each size holds its own stock and reserves only its own, with a shortage only on the over-reserved size. |
| K06 | covered | packages/reality-core/tests/scenarios/test_catalog_kits.py::test_a_bundle_price_is_split_across_its_components | Shares are stated on the kit; the line's stated net, tax and gross split at read time and add up exactly (spec 333). |

## L. E-commerce and marketplaces

| ID | Status | Evidence | Note |
|---|---|---|---|
| L01 | covered | tests/scenarios/test_catalog_stock_and_returns.py::test_stock_at_an_external_fulfilment_location_is_sold_from_there | Stock at an external fulfilment location is reserved and shipped from there. No marketplace report interpreter exists. |
| L02 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_marketplace_order_due_tomorrow_is_at_risk_until_it_ships | A reserved marketplace order a day before its deadline is reported until it ships, and overdue once the date passes (spec 300). |
| L03 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_a_marketplace_payout_settles_each_order_and_books_the_fees | One payout pays six orders minus a refund and fees on the provider's own cash account; the net reaches the bank. The statement is stated through the reviewed command; provider report formats are not read (spec 336). |
| L04 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_a_partial_shopify_refund_is_recorded_from_its_source | A partial refund becomes its own shopify/refund source and a sales_refund document on the order without a posting (spec 296). |
| L05 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_an_edited_shopify_order_applies_a_removed_line_and_holds_an_added_one | A removed line is cancelled citing the version; an added line waits with line_added (spec 296). |
| L06 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_pre_order_shows_its_shortage_and_the_supply_that_protects_it | Dated customer order without stock; an incoming purchase is assigned through supply_assign; readiness names insufficient_stock and supply_coverage shows 5 protecting (0 before, as control). |
| L07 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_black_friday_burst_is_interpreted_once_and_never_over_reserved; specs/300-multichannel-oversell/results.md | 10,000 shop orders interpreted in 404 s by one process, each once, never over-reserved (spec 300). |
| L08 | gap | db/core.py Commitment (no recurrence) | No recurring or subscription commitment; holds exist only per single commitment. |
| L09 | covered | tests/scenarios/test_catalog_orders_and_shipments.py::test_shopify_free_promotion_item_is_its_own_zero_price_line_and_commitment | A Shopify gift line at 0.00 becomes its own line and commitment; the raw line payload is kept. |
| L10 | covered | packages/reality-core/tests/scenarios/test_catalog_party_merges.py::test_a_guest_order_later_with_an_account | A guest shop order and invoice merge into the account through the review: the account's detail and balance include them, the guest order still names the guest, and the next shop order naming the guest lands on the account (spec 339). |
| L11 | out | specs/340-accounting-boundary/spec.md Non-Goals (no tax rate determined or derived) | Tax is kept as the source states it (spec 284); a rate the shop states stays in the source payload, and none is ever derived from amounts. |
| L12 | gap | db/core.py (no incoterm, duty or customs fields) | Duties and incoterms are not represented beyond the lossless payload. |

## M. B2B specifics

| ID | Status | Evidence | Note |
|---|---|---|---|
| M01 | gap | packages/reality-core/src/reality/db/core.py (Commitment, CommitmentRevision) | There's no blanket-order or call-off relation, so "called off vs remaining" across child orders can't be represented. |
| M02 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_customer_orders_by_its_own_item_numbers; tests/test_pricing.py::test_pricing_resolves_direct_group_default_and_quantity_tiers | Customer prices are proven; per customer a number names an item, typed and imported orders resolve it, and an unknown number waits for an assignment that can remember it (spec 308). |
| M03 | gap | tests/test_master_data_api.py::test_api_ingests_arbitrary_source_as_unmapped | EDI messages can only be stored as unmapped sources; there are no ORDERS/ORDRSP/DESADV/INVOIC/REMADV interpreters or links between messages. |
| M04 | partial | tests/test_commitment_revisions.py::test_the_quantity_in_force_is_the_latest_stated; tests/scenarios/test_b2b_operational_integrity.py::test_b2b_inventory_revision_return_and_cancellation_reconcile_exactly; tests/test_shopify_update_guard.py::test_changed_order_preserves_every_business_record | Manual `commitment_revise` is proven; a customer ORDCHG source does not create a revision (a changed Shopify order is held for review instead). |
| M05 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_retail_chain_order_is_delivered_to_its_stores | Planned deliveries name a store each as recipient and split one order between them; each shipment keeps its recipient (spec 334). |
| M06 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_customer_who_wants_no_backorders_has_the_rest_cancelled | No backorders stated for the customer: 6 of 10 ship, Backorder against the customer's rule reports the open 4 with its reason, and the reviewed cancellation clears it (spec 306). |
| M07 | gap | docs/ideas/attachments.md (HandlingUnit label idea only) | No label or delivery-note output exists, and no doc states it is out of core scope, so "out" can't be cited. |
| M08 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_a_customer_deduction_with_an_agreed_reason_leaves_nothing_open | Customer short payment with an agreed_deduction reduction through finance.settlement.apply: invoice open 0, reason on the review and the adjustment source record. |
| M09 | partial | tests/test_unified_invoice_credit.py::test_financial_credit_does_not_require_return_exception; specs/004-master-data/spec.md Non-Goals ("rebates") | A credit without goods can carry a rebate; rebate agreements and year-end accrual are an explicit non-goal. |
| M10 | gap | db/core.py Document (party_id, ship_to_party_id); tests/test_operational_fields.py::test_document_and_commitment_operational_fields | Only orderer and ship-to are typed; there is no bill-to or payer role on documents or settlement. |
| M11 | gap | services/core.py allocate_settlement ("must be opposite sides of one control account"); specs/170-party-balances/spec.md Non-Goals | One party can hold both roles, but a receivable can't be offset against a payable. |
| M12 | gap | db/core.py ReturnAnnouncement; `create_commitment` allows only customer_delivery/supplier_delivery | There's no loan or sample commitment. A shipment would count as a sale (shipped_not_billed); a ReturnAnnouncement only comes close. |

## N. Finance, tax and currency

| ID | Status | Evidence | Note |
|---|---|---|---|
| N01 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_an_intra_community_supply_keeps_its_stated_zero_tax_and_case | Customer with VAT ID; reviewed sales invoice with stated net 250 and tax 0; EU case as an internal case_code reference; nothing computed. |
| N02 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_a_reverse_charge_supplier_invoice_keeps_its_stated_amounts | Reviewed supplier invoice with stated net 400 and tax 0 kept as stated; stating the self-assessed tax is refused with stated_invoice_net_tax_gross_mismatch. |
| N03 | out | docs/features/ledger.md Non-goals (FX revaluation); specs/148-accounting-journal-cost-centers/spec.md (no accounting-currency conversion) | Foreign-currency invoices are supported, but cross-currency allocation is refused, so a EUR payment on a CHF invoice stays unallocated and no FX difference exists. |
| N04 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_three_levels_of_dunning_then_collection | A company schedule and reviewed runs over three customers: level 1 for all, a paid item left out, an item paid after the review skipped, levels 2 and 3 with posted fees, a collection handover with a delivery hold, and the handed-over item never dunned again (spec 295). |
| N05 | covered | tests/finance/test_commercial_edges.py::test_bad_debt_uses_dedicated_expense_and_never_creates_credit | A partial `bad_debt` adjustment with a reason posts to bad-debt expense and creates no credit. |
| N06 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_the_party_balance_counts_credits_deposits_and_prepayments_once | Open 700 (ordinary and unpaid prepayment invoice), credit 430 (credit note, deposit, unallocated prepayment), balance 270. |
| N07 | gap | specs/148-accounting-journal-cost-centers/spec.md FR-012 (export package specified, not implemented) | No handoff or export package exists, so "reversal after export" cannot be represented; the reversal itself exists. |
| N08 | out | specs/148-accounting-journal-cost-centers/spec.md Non-goals (no tax engine or tax calculation) | Reality stores stated tax and never determines a rate, so rate by invoice date is the source's job. |

## O. Master data and identity

| ID | Status | Evidence | Note |
|---|---|---|---|
| O01 | covered | packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py::test_a_renamed_item_number_keeps_every_record_on_the_same_item | After reserve, a partial shipment and an invoice, a reviewed item update renames the SKU: movements, reservations and the promise keep the item, stock is unchanged, order and invoice lines keep the old number, and the rest ships. |
| O02 | covered | packages/reality-core/tests/scenarios/test_catalog_party_merges.py::test_two_partners_merged_as_duplicates | Two halves of one customer merge; the credit exposure and balance sum both, the duplicate names its survivor, and a further merge into the duplicate is refused (spec 339). |
| O03 | out | specs/004-master-data/spec.md Non-Goals ("postal addresses") | Addresses exist only in lossless party or source payloads; no test proves an old order shows the old address. |
| O04 | covered | tests/scenarios/test_catalog_orders_and_shipments.py::test_delisted_item_still_serves_its_open_commitment | An inactive item is still reserved and shipped for its open commitment. |
| O05 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_bought_in_cartons_of_twelve_and_held_in_pieces | Bought in cartons of 12, received in cartons and held in pieces; stock, open quantity and the supplier invoice in cartons agree (spec 301). |
| O06 | gap | db/core.py Item (no supplier reference table) | There's no supplier item number or per-supplier item mapping. |

## P. Sources and integration

| ID | Status | Evidence | Note |
|---|---|---|---|
| P01 | covered | packages/reality-core/tests/test_shopify_and_explain.py::test_shopify_ingestion_is_lossless_idempotent_and_traceable; tests/test_source_ingestion.py::test_unknown_source_is_stored_idempotently_as_unmapped; tests/test_payment_intake.py::test_replay_of_the_same_source_records_no_second_cash_entry | Idempotency is proven for orders, unmapped sources and payments. |
| P02 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_records_arriving_before_their_order_are_linked_once_it_is_in | A refund before its order links itself on retry; a payment before its order is offered for the invoice its reference names, and a person allocates it (spec 314). |
| P03 | covered | packages/reality-core/tests/test_shopify_and_explain.py::test_changed_source_creates_version_without_replacing_interpretation; tests/test_document_corrections.py::test_external_document_correction_appends_immutable_source_version | A correction creates a new version with a supersedes link and keeps the original payload. |
| P04 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_a_source_cancellation_closes_the_line_with_the_source_as_its_reason | A Shopify order is interpreted and reserved; its cancelled version is held for review; a reviewed commitment_cancel citing that source record closes the line, releases the reservation and the event carries the source and the reason. |
| P05 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_an_incomplete_shop_order_is_accepted_and_its_gap_reported | A line without a price is kept without one and reported by order_line_price_missing; a line without a quantity fails its order with a code while the batch goes on (spec 314). |
| P06 | partial | packages/reality-core/tests/test_shipment_story.py::test_supplier_source_payload_and_carrier_warehouse_discrepancy_remain_distinct; tests/test_provenance.py::test_several_contributing_systems_are_disclosed | Only the carrier-versus-warehouse contradiction is surfaced. There is no general check when two systems state different values. |
| P07 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_a_day_long_outage_is_reported_and_its_backlog_arrives_without_duplicates | Daily Shopify arrivals under a controlled clock; after four quiet days silent_source reports 96 hours; the backlog of new orders plus exact repeats creates ten records, ten orders and ten promises and the silence clears. |
| P08 | covered | packages/reality-core/tests/scenarios/test_catalog_sources.py::test_an_open_order_partly_delivered_before_go_live_is_traceable | An open order partly delivered before go-live is imported with its original quantity and a reviewed revision to the open rest, both citing the legacy source (spec 314). The delivered quantity stays in the payload. |

## Q. Time and period

| ID | Status | Evidence | Note |
|---|---|---|---|
| Q01 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_the_month_end_lists_both_directions_from_the_same_findings | The month-end billing lists shipped-not-invoiced and invoiced-not-shipped lines from the same findings (spec 299). |
| Q02 | out | specs/340-accounting-boundary/spec.md Non-Goals (no accounting periods, close or posting locks) | Reality is not the bookkeeping system; closing periods belongs to the accounting system that receives the records. |
| Q03 | covered | tests/test_analysis_positions_history.py::test_detail_inventory_conserves_locations_and_unknown_tracking, ::test_later_stock_compensation_does_not_rewrite_earlier_snapshot, ::test_cutoff_excludes_next_midnight_and_late_allocation_endpoint | Point-in-time stock with an explicit cutoff is asserted, including that later corrections don't rewrite it. |
| Q04 | covered | packages/reality-core/tests/scenarios/test_catalog_time.py::test_open_orders_and_purchases_carry_over_the_year_end | An order and a purchase with 4 of 10 delivered in December keep 6 open across the year end; January's delivery fulfils both with December's still counted (spec 340). |
| Q05 | partial | tests/test_operational_fields.py::test_document_and_commitment_operational_fields | Offset timestamps are proven to normalize to UTC; there is no company time zone, and no test pins the day a late-evening local order falls on (`domain/calendar.as_day` takes the text's local day). |

## R. Combined stress stories

| ID | Status | Evidence | Note |
|---|---|---|---|
| R01 | partial | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_a_partly_paid_prepayment_order_cannot_be_released_anyway | The 80 % prepaid order is refused by shipment_dispatch and by movement_create (spec 294 fix); spec 275 FR-005 keeps it unshippable and no reviewed release exists. |
| R02 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_two_customers_an_under_delivery_a_key_customer_and_a_cancellation | Two orders of 3 assigned to a purchase of 6 that delivers 4 and is reduced: the key customer is reserved 3 by stated quantities, the other 1; its cancellation ends its assignment and the key customer is no longer at risk (spec 305). |
| R03 | partial | packages/reality-core/tests/scenarios/test_catalog_drop_shipping.py::test_a_drop_shipped_return_comes_to_us_and_both_sides_are_credited | Returned to us, credited, sent on to the supplier and credited by it; both sides net out. The wrong item itself cannot be named (D05) (spec 337). |
| R04 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_a_payout_of_400_orders_with_refunds_chargebacks_and_fees_books_every_line | 400 charges, 12 refunds, 3 chargebacks and fees in one reviewed settlement; every position is booked and the provider account is empty (spec 336). |
| R05 | partial | tests/test_commitment_revisions.py::test_a_promise_can_shrink_below_what_arrived, ::test_shrinking_to_what_arrived_finishes_the_promise | Revising after a partial fulfilment is proven on commitments; there's no EDI ORDCHG or advice source. |
| R06 | covered | packages/reality-core/tests/scenarios/test_catalog_purchasing.py::test_an_import_container_lands_in_eur_with_freight_and_duty | Five USD purchases from two suppliers; the invoice rate as conversion basis lands one receipt in EUR with freight and duty, and the waiting orders are served (spec 309). |
| R07 | covered | packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py::test_a_month_end_loss_uncovers_three_reservations_and_releases_none | Three reservations of 4 against 12, a count of 9: the review names all three, Reservation exceeds stock raises, and none is released by itself (spec 307). |
| R08 | covered | packages/reality-core/tests/scenarios/test_catalog_finance.py::test_a_customer_who_is_also_a_supplier_is_held_with_every_fact | Overdue receivable, ordered value and open credit make the exposure; the payable to the same party is named, not netted (spec 298). |
