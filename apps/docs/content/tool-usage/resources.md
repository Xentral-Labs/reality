# Business resources

The business objects an ERP professional works with, each with the lists that show it, the actions
that change it, the exceptions it can raise, and the technology underneath. Names follow ERP usage;
the technical key stands beside each one.

> Automatically generated from `resource_catalog.yaml`. Do not edit this page by hand.

| Object                                                           | Lists | Actions | Exceptions to clear |
| ---------------------------------------------------------------- | ----- | ------- | ------------------- |
| [Analytics report](#resource-analytics)                          | 0     | 1       | 0                   |
| [Business partner](#resource-party)                              | 1     | 6       | 2                   |
| [Item](#resource-item)                                           | 5     | 3       | 2                   |
| [Warehouse location](#resource-location)                         | 3     | 3       | 0                   |
| [Prices and payment terms](#resource-terms)                      | 2     | 6       | 2                   |
| [Order](#resource-order)                                         | 8     | 9       | 7                   |
| [Delivery and goods receipt](#resource-delivery)                 | 2     | 6       | 2                   |
| [Lot, serial number and pallet](#resource-lot)                   | 0     | 5       | 1                   |
| [Invoice and credit note](#resource-invoice)                     | 3     | 9       | 14                  |
| [Payment and settlement](#resource-payment)                      | 2     | 7       | 2                   |
| [Ledger and accounts](#resource-accounting)                      | 2     | 10      | 1                   |
| [Return](#resource-return)                                       | 0     | 2       | 6                   |
| [Document and source system](#resource-source)                   | 3     | 10      | 2                   |
| [Company and users](#resource-company)                           | 1     | 4       | 0                   |
| [Approvals, exceptions and open questions](#resource-governance) | 3     | 0       | 0                   |

## Analytics report {#resource-analytics}

_Composable questions and private definitions_

Read-time observations over retained evidence and operational services, with scoped contributors and
private saved definitions.

**Also called:** analytics, report, Auswertung, Bericht, graph, Graph

**Actions**

- [Change Private Graph Report](./commands#command-change_graph_report) (`change_graph_report`)

**Underneath:** Tables: `analytics_report` · Agent tools without a command:
[`graph_catalog`](./commands#tool-graph_catalog),
[`graph_templates`](./commands#tool-graph_templates), [`graph_ask`](./commands#tool-graph_ask),
[`graph_format`](./commands#tool-graph_format),
[`graph_interpret`](./commands#tool-graph_interpret),
[`graph_reports_list`](./commands#tool-graph_reports_list),
[`graph_report_get`](./commands#tool-graph_report_get),
[`graph_requests_list`](./commands#tool-graph_requests_list),
[`graph_request_get`](./commands#tool-graph_request_get),
[`graph_request_propose`](./commands#tool-graph_request_propose)

## Business partner {#resource-party}

_Customers, suppliers and your own company_

One record per company or person you trade with. Roles such as customer or supplier are stated on
the partner, not by keeping two address books. Delivery holds and pricing groups attach here.

**Also called:** customer, supplier, debtor, creditor, Kunde, Lieferant, Debitor, Kreditor, Adresse

**Lists**

- [Parties](./views#view-parties) (`parties`)

**Actions**

- [Create party](./commands#command-create_party) (`create_party`)
- [Update party](./commands#command-update_party) (`update_party`)
- [Change master-data lifecycle](./commands#command-set_master_data_active)
  (`set_master_data_active`)
- [Assign party price list](./commands#command-assign_party_price_list) (`assign_party_price_list`)
- [Create and assign pricing group](./commands#command-create_party_group) (`create_party_group`)
- [Set party delivery hold](./commands#command-hold_party_delivery) (`hold_party_delivery`)

**Exceptions to clear**

- [Credit limit exceeded](./exceptions#exception-credit_limit_exceeded) (`credit_limit_exceeded`)
- [Party hold not lifted](./exceptions#exception-party_hold_unreleased) (`party_hold_unreleased`)

**Appears in processes:** [Master data and sources](./processes#process-master_data)

**Underneath:** Tables: `party`, `party_role`, `party_group`, `party_group_member`, `party_hold` ·
Events: [`party.created`](./events#event-party-created),
[`party.updated`](./events#event-party-updated),
[`party.delivery_hold_placed`](./events#event-party-delivery_hold_placed),
[`party.delivery_hold_released`](./events#event-party-delivery_hold_released),
[`master_data.lifecycle_changed`](./events#event-master_data-lifecycle_changed),
[`party_price_list.assigned`](./events#event-party_price_list-assigned),
[`party_group.updated`](./events#event-party_group-updated),
[`party_group.created`](./events#event-party_group-created),
[`party_group_member.added`](./events#event-party_group_member-added) · Agent tools without a
command: [`finance_party_balances`](./commands#tool-finance_party_balances)

## Item {#resource-item}

_What you buy, stock and sell, and how much of it there is_

The operational identity of a product with its unit. Stock is never stored on the item; it is
derived from movements and reservations at read time, which is why the stock lists live here.

**Also called:** product, SKU, stock, inventory, Produkt, Bestand, Lagerbestand, Verfügbarkeit

**Lists**

- [Inventory](./views#view-inventory) (`inventory`)
- [Items](./views#view-items) (`items`)
- [Supply & demand](./views#view-supply_demand) (`supply_demand`)
- [Item supply and demand](./views#projection-item_supply_demand) (`item_supply_demand`)
- [Inventory](./views#projection-inventory) (`inventory`)

**Actions**

- [Create item](./commands#command-create_item) (`create_item`)
- [Update item](./commands#command-update_item) (`update_item`)
- [Change master-data lifecycle](./commands#command-set_master_data_active)
  (`set_master_data_active`)

**Exceptions to clear**

- [Units not comparable](./exceptions#exception-units_not_comparable) (`units_not_comparable`)
- [Reservation exceeds stock](./exceptions#exception-reservation_exceeds_stock)
  (`reservation_exceeds_stock`)

**Appears in processes:** [Procure to pay](./processes#process-procure_to_pay),
[Master data and sources](./processes#process-master_data)

**Underneath:** Tables: `item` · Events: [`item.created`](./events#event-item-created),
[`item.updated`](./events#event-item-updated),
[`master_data.lifecycle_changed`](./events#event-master_data-lifecycle_changed) · Agent tools
without a command: [`inventory_read`](./commands#tool-inventory_read),
[`item_supply_demand`](./commands#tool-item_supply_demand)

## Warehouse location {#resource-location}

_Warehouses, zones and logical places stock can be_

A physical or logical place. Only stock-capable locations can hold goods; a hierarchy is expressed
through the parent location.

**Also called:** warehouse, bin, zone, Lager, Lagerplatz

**Lists**

- [Inventory](./views#view-inventory) (`inventory`)
- [Locations](./views#view-locations) (`locations`)
- [Inventory](./views#projection-inventory) (`inventory`)

**Actions**

- [Create location](./commands#command-create_location) (`create_location`)
- [Update location](./commands#command-update_location) (`update_location`)
- [Change master-data lifecycle](./commands#command-set_master_data_active)
  (`set_master_data_active`)

**Underneath:** Tables: `location` · Events: [`location.created`](./events#event-location-created),
[`location.updated`](./events#event-location-updated),
[`master_data.lifecycle_changed`](./events#event-master_data-lifecycle_changed)

## Prices and payment terms {#resource-terms}

_Price lists, tiers, pricing groups and payment terms_

The commercial conditions an order or invoice is judged against. Price resolution shows which list
applies to which partner; payment terms drive due dates and early payment discounts.

**Also called:** price list, discount, tier, condition, Preisliste, Staffelpreis, Kondition, Skonto,
Zahlungsziel

**Lists**

- [Commercial terms](./views#view-commercial_terms) (`commercial_terms`)
- [Price resolution](./views#projection-price_resolution) (`price_resolution`)

**Actions**

- [Change master-data lifecycle](./commands#command-set_master_data_active)
  (`set_master_data_active`)
- [Create payment term](./commands#command-create_payment_term) (`create_payment_term`)
- [Create price list](./commands#command-create_price_list) (`create_price_list`)
- [Add price tier](./commands#command-create_price_list_entry) (`create_price_list_entry`)
- [Assign party price list](./commands#command-assign_party_price_list) (`assign_party_price_list`)
- [Create and assign pricing group](./commands#command-create_party_group) (`create_party_group`)

**Exceptions to clear**

- [Invoice price differs from the agreement](./exceptions#exception-invoice_price_differs)
  (`invoice_price_differs`)
- [Sold below the purchase price](./exceptions#exception-sold_below_purchase_price)
  (`sold_below_purchase_price`)

**Appears in processes:** [Master data and sources](./processes#process-master_data)

**Underneath:** Tables: `payment_term`, `price_list`, `price_list_entry`, `party_price_list`,
`party_group_price_list` · Events:
[`master_data.lifecycle_changed`](./events#event-master_data-lifecycle_changed),
[`payment_term.updated`](./events#event-payment_term-updated),
[`payment_term.created`](./events#event-payment_term-created),
[`price_list.updated`](./events#event-price_list-updated),
[`price_list.created`](./events#event-price_list-created),
[`price_list_entry.created`](./events#event-price_list_entry-created),
[`party_price_list.assigned`](./events#event-party_price_list-assigned),
[`party_group.created`](./events#event-party_group-created),
[`party_group_price_list.assigned`](./events#event-party_group_price_list-assigned)

## Order {#resource-order}

_Sales orders, purchase orders, reservations and holds_

A promise to deliver or to receive: Reality calls it a commitment. The order document is evidence;
open quantity, ship readiness and delays are derived from the commitment, its reservations and the
movements that fulfil it.

**Also called:** sales order, purchase order, commitment, reservation, backlog, Kundenauftrag,
Bestellung, Verpflichtung, Lieferverpflichtung, Reservierung, Rückstand, Liefersperre

**Lists**

- [Commitments](./views#view-commitments) (`commitments`)
- [Reservations](./views#view-reservations) (`reservations`)
- [Orders](./views#view-orders) (`orders`)
- [Warehouse Queue](./views#view-warehouse_queue) (`warehouse_queue`)
- [Fulfillment blockers](./views#view-fulfillment_blockers) (`fulfillment_blockers`)
- [Fulfillment queue](./views#projection-fulfillment_queue) (`fulfillment_queue`)
- [Fulfillment blockers](./views#projection-fulfillment_blockers) (`fulfillment_blockers`)
- [Commitment register](./views#projection-commitment_register) (`commitment_register`)

**Actions**

- [Create manual sales or purchase order](./commands#command-create_manual_order)
  (`create_manual_order`)
- [Reserve stock](./commands#command-reserve) (`reserve`)
- [Release reservation](./commands#command-release_reservation) (`release_reservation`)
- [Revise commitment](./commands#command-revise_commitment) (`revise_commitment`)
- [Hold commitment](./commands#command-hold_commitment) (`hold_commitment`)
- [Hold document commitments](./commands#command-hold_document_commitments)
  (`hold_document_commitments`)
- [Set party delivery hold](./commands#command-hold_party_delivery) (`hold_party_delivery`)
- [Close stale promises](./commands#command-close_stale_promises) (`close_stale_promises`)
- [Dispatch or receive shipment package](./commands#command-record_packaged_execution)
  (`record_packaged_execution`)

**Look up**

- [Preview stale promise closure](./commands#command-preview_stale_promise_closure)
  (`preview_stale_promise_closure`)

**Exceptions to clear**

- [Overdue outgoing customer commitment](./exceptions#exception-overdue_outgoing_customer_commitment)
  (`overdue_outgoing_customer_commitment`)
- [Customer commitment at risk](./exceptions#exception-outgoing_commitment_at_risk)
  (`outgoing_commitment_at_risk`)
- [Order stalled](./exceptions#exception-order_stalled) (`order_stalled`)
- [Overdue incoming supplier commitment](./exceptions#exception-overdue_incoming_supplier_commitment)
  (`overdue_incoming_supplier_commitment`)
- [Reservation exceeds stock](./exceptions#exception-reservation_exceeds_stock)
  (`reservation_exceeds_stock`)
- [Promise hold not lifted](./exceptions#exception-commitment_hold_unreleased)
  (`commitment_hold_unreleased`)
- [Party hold not lifted](./exceptions#exception-party_hold_unreleased) (`party_hold_unreleased`)

**Appears in processes:** [Order to cash](./processes#process-order_to_cash),
[Procure to pay](./processes#process-procure_to_pay)

**Underneath:** Tables: `commitment`, `commitment_hold`, `commitment_revision`, `reservation` ·
Events: [`order.recorded`](./events#event-order-recorded),
[`party.delivery_hold_placed`](./events#event-party-delivery_hold_placed),
[`commitment.created`](./events#event-commitment-created),
[`commitment.cancelled`](./events#event-commitment-cancelled),
[`commitment.revised`](./events#event-commitment-revised),
[`promises.closed`](./events#event-promises-closed),
[`commitment.held`](./events#event-commitment-held),
[`commitment.hold_released`](./events#event-commitment-hold_released),
[`reservation.created`](./events#event-reservation-created),
[`reservation.released`](./events#event-reservation-released) · Agent tools without a command:
[`commitments_list`](./commands#tool-commitments_list),
[`fulfillment_queue`](./commands#tool-fulfillment_queue),
[`fulfillment_blockers`](./commands#tool-fulfillment_blockers),
[`order_explain`](./commands#tool-order_explain)

## Delivery and goods receipt {#resource-delivery}

_Stock movements, shipments, packages and tracking_

Every physical change of stock is an append-only movement; corrections add a compensating movement
instead of editing. A shipment is the consignment that carries movements to or from a counterparty,
with carrier observations attached.

**Also called:** goods receipt, goods issue, shipment, movement, transfer, adjustment, Warenausgang,
Lagerbewegung, Umlagerung, Bestandsanpassung, Sendung, Packstück, Tracking

**Lists**

- [Movements](./views#view-movements) (`movements`)
- [Warehouse Queue](./views#view-warehouse_queue) (`warehouse_queue`)

**Actions**

- [Record movement](./commands#command-record_movement) (`record_movement`)
- [Correct movement](./commands#command-correct_movement) (`correct_movement`)
- [Record shipment notice](./commands#command-record_shipment_notice) (`record_shipment_notice`)
- [Dispatch or receive shipment package](./commands#command-record_packaged_execution)
  (`record_packaged_execution`)
- [Record shipment event](./commands#command-record_shipment_event) (`record_shipment_event`)
- [Supersede shipment event](./commands#command-supersede_shipment_event)
  (`supersede_shipment_event`)

**Exceptions to clear**

- [Return not dealt with](./exceptions#exception-return_unresolved) (`return_unresolved`)
- [Unexplained movement](./exceptions#exception-unexplained_movement) (`unexplained_movement`)

**Appears in processes:** [Order to cash](./processes#process-order_to_cash),
[Procure to pay](./processes#process-procure_to_pay),
[Customer returns](./processes#process-returns)

**Underneath:** Tables: `movement`, `movement_correction`, `shipment`, `shipment_package`,
`shipment_event`, `shipment_event_supersession` · Events:
[`shipment.notice_recorded`](./events#event-shipment-notice_recorded),
[`shipment.event_recorded`](./events#event-shipment-event_recorded),
[`shipment.event_superseded`](./events#event-shipment-event_superseded),
[`commitment.fulfilled`](./events#event-commitment-fulfilled),
[`reservation.consumed`](./events#event-reservation-consumed),
[`movement.recorded`](./events#event-movement-recorded),
[`movement.corrected`](./events#event-movement-corrected) · Agent tools without a command:
[`shipments_list`](./commands#tool-shipments_list),
[`shipment_explain`](./commands#tool-shipment_explain)

## Lot, serial number and pallet {#resource-lot}

_Identities below the item, and their best-before dates_

A lot or serial unit identifies a subset of an item; a handling unit identifies a pallet by its
NVE/SSCC. Best-before dates are stated by someone who read them, never computed.

**Also called:** batch, serial, handling unit, NVE, SSCC, best before, MHD, Charge, Ladeeinheit

**Actions**

- [Create handling unit](./commands#command-create_handling_unit) (`create_handling_unit`)
- [Create lot](./commands#command-create_lot) (`create_lot`)
- [State lot expiry](./commands#command-state_lot_expiry) (`state_lot_expiry`)
- [Correct lot expiry](./commands#command-correct_lot_expiry) (`correct_lot_expiry`)
- [Create serial unit](./commands#command-create_serial_unit) (`create_serial_unit`)

**Look up**

- [Read expired lots](./commands#command-expired_lots) (`expired_lots`)

**Exceptions to clear**

- [Expired stock on hand](./exceptions#exception-stock_expired) (`stock_expired`)

**Underneath:** Tables: `lot`, `serial_unit`, `handling_unit` · Events:
[`handling_unit.created`](./events#event-handling_unit-created),
[`lot.created`](./events#event-lot-created),
[`lot.expiry_stated`](./events#event-lot-expiry_stated),
[`lot.expiry_corrected`](./events#event-lot-expiry_corrected),
[`serial_unit.created`](./events#event-serial_unit-created)

## Invoice and credit note {#resource-invoice}

_Sales and supplier invoices, credit notes and what is still open_

Recording an invoice stores the evidence; booking it posts the ledger entries. Open items compare
what was billed with what was paid or credited, per partner and currency.

**Also called:** receivable, payable, open item, credit note, billing, Ausgangsrechnung,
Eingangsrechnung, Forderung, Verbindlichkeit, Offene Posten, Rechnungsprüfung, Gutschrift

**Lists**

- [Open items](./views#view-open_items) (`open_items`)
- [Documents](./views#view-documents) (`documents`)
- [Open financial items](./views#projection-open_financial_items) (`open_financial_items`)

**Actions**

- [Post sales invoice](./commands#command-post_sales_invoice) (`post_sales_invoice`)
- [Post supplier invoice](./commands#command-post_supplier_invoice) (`post_supplier_invoice`)
- [Record return credit](./commands#command-record_sales_credit) (`record_sales_credit`)
- [Record supplier invoice](./commands#command-record_supplier_invoice) (`record_supplier_invoice`)
- [Record sales invoice](./commands#command-record_sales_invoice) (`record_sales_invoice`)
- [Post credit note](./commands#command-post_sales_credit_note) (`post_sales_credit_note`)
- [Net credit note against invoice](./commands#command-allocate_credit_note)
  (`allocate_credit_note`)
- [Post supplier credit note](./commands#command-post_supplier_credit_note)
  (`post_supplier_credit_note`)
- [Net supplier credit against invoice](./commands#command-allocate_supplier_credit_note)
  (`allocate_supplier_credit_note`)

**Exceptions to clear**

- [Shipped and not billed](./exceptions#exception-shipped_not_billed) (`shipped_not_billed`)
- [Billed and not received](./exceptions#exception-billed_not_received) (`billed_not_received`)
- [Invoice price differs from the agreement](./exceptions#exception-invoice_price_differs)
  (`invoice_price_differs`)
- [Receipt not invoiced](./exceptions#exception-receipt_unbilled) (`receipt_unbilled`)
- [Sales invoice not booked](./exceptions#exception-sales_invoice_unposted)
  (`sales_invoice_unposted`)
- [Supplier invoice not booked](./exceptions#exception-supplier_invoice_unposted)
  (`supplier_invoice_unposted`)
- [Credit note not booked](./exceptions#exception-credit_note_unposted) (`credit_note_unposted`)
- [Credit note not given back](./exceptions#exception-credit_note_unsettled)
  (`credit_note_unsettled`)
- [Supplier credit not booked](./exceptions#exception-supplier_credit_unposted)
  (`supplier_credit_unposted`)
- [Supplier credit not claimed](./exceptions#exception-supplier_credit_unclaimed)
  (`supplier_credit_unclaimed`)
- [Overdue receivable](./exceptions#exception-overdue_receivable) (`overdue_receivable`)
- [Overdue payable](./exceptions#exception-overdue_payable) (`overdue_payable`)
- [Early payment discount still available](./exceptions#exception-purchase_discount_available)
  (`purchase_discount_available`)
- [Duplicate supplier invoice](./exceptions#exception-duplicate_supplier_invoice)
  (`duplicate_supplier_invoice`)

**Appears in processes:** [Order to cash](./processes#process-order_to_cash),
[Procure to pay](./processes#process-procure_to_pay),
[Customer returns](./processes#process-returns)

**Underneath:** Events: [`credit.recorded`](./events#event-credit-recorded),
[`invoice.recorded`](./events#event-invoice-recorded) · Agent tools without a command:
[`finance_credits`](./commands#tool-finance_credits),
[`finance_party_balances`](./commands#tool-finance_party_balances)

## Payment and settlement {#resource-payment}

_Incoming and outgoing payments, allocation, short payments and refunds_

A payment is evidence with a balanced posting behind it. Allocating it to invoices or credits is the
settlement; a short payment is accepted as an agreed deduction or left open. Payment runs pay
suppliers in bulk.

**Also called:** payment receipt, allocation, matching, short payment, refund, payment run,
Zahlungseingang, zuordnen, Minderzahlung, Abzug, Skontoabzug, Erstattung, Zahllauf, Saldo

**Lists**

- [Payments](./views#view-payments) (`payments`)
- [Payments](./views#projection-payments) (`payments`)

**Actions**

- [Post customer payment](./commands#command-post_customer_payment) (`post_customer_payment`)
- [Execute payment run](./commands#command-execute_payment_run) (`execute_payment_run`)
- [Post customer refund](./commands#command-post_customer_refund) (`post_customer_refund`)
- [Post supplier refund](./commands#command-post_supplier_refund) (`post_supplier_refund`)
- [Post supplier payment](./commands#command-post_supplier_payment) (`post_supplier_payment`)
- [Accept settlement reduction](./commands#command-accept_adjustment) (`accept_adjustment`)
- [Record payment or use existing credit](./commands#command-apply_settlement) (`apply_settlement`)

**Look up**

- [Preview payment run](./commands#command-preview_payment_run) (`preview_payment_run`)
- [Read settlement reduction context](./commands#command-adjustment_context) (`adjustment_context`)
- [Read payment and credit context](./commands#command-settlement_context) (`settlement_context`)

**Exceptions to clear**

- [Credit note not given back](./exceptions#exception-credit_note_unsettled)
  (`credit_note_unsettled`)
- [Unmatched financial event](./exceptions#exception-unmatched_financial_event)
  (`unmatched_financial_event`)

**Appears in processes:** [Order to cash](./processes#process-order_to_cash),
[Procure to pay](./processes#process-procure_to_pay),
[Customer returns](./processes#process-returns)

**Underneath:** Tables: `settlement_allocation` · Events:
[`payments.run`](./events#event-payments-run),
[`settlement.allocated`](./events#event-settlement-allocated) · Agent tools without a command:
[`finance_balances`](./commands#tool-finance_balances),
[`finance_party_balances`](./commands#tool-finance_party_balances),
[`finance_payments`](./commands#tool-finance_payments)

## Ledger and accounts {#resource-accounting}

_Journal, operational accounts, opening balances and the export configuration_

The balanced journal every posting lands in, the operational accounts it uses, and the configuration
that maps postings to an external accounting system. Reversals add an inverse posting group; nothing
is deleted.

**Also called:** journal, GL, chart of accounts, reversal, opening balance, export, DATEV, Journal,
Kontenrahmen, Storno, Eröffnungsbilanz, Sachkonto

**Lists**

- [Journal](./views#view-journal) (`journal`)
- [Journal](./views#projection-journal) (`journal`)

**Actions**

- [Maintain Target Configuration](./commands#command-maintain_target_configuration)
  (`maintain_target_configuration`)
- [Set source code mapping](./commands#command-set_source_mapping) (`set_source_mapping`)
- [Assign received financial component](./commands#command-assign_component) (`assign_component`)
- [Maintain finance reference](./commands#command-maintain_reference) (`maintain_reference`)
- [Initialize operational accounts](./commands#command-initialize_accounts) (`initialize_accounts`)
- [Create operational account](./commands#command-create_account) (`create_account`)
- [Update operational account](./commands#command-update_account) (`update_account`)
- [Set operational account default](./commands#command-set_default_account) (`set_default_account`)
- [Reverse ledger posting group](./commands#command-reverse_ledger_posting_group)
  (`reverse_ledger_posting_group`)
- [Import opening positions](./commands#command-import_opening) (`import_opening`)

**Look up**

- [List Targets](./commands#command-list_targets) (`list_targets`)
- [List Target References](./commands#command-list_target_references) (`list_target_references`)
- [List Mappings](./commands#command-list_mappings) (`list_mappings`)
- [Mapping History](./commands#command-mapping_history) (`mapping_history`)
- [Read source code mappings](./commands#command-list_source_mappings) (`list_source_mappings`)
- [Read source mapping history](./commands#command-source_mapping_history)
  (`source_mapping_history`)
- [Read received financial detail](./commands#command-component_context) (`component_context`)
- [Read component assignment history](./commands#command-component_history) (`component_history`)
- [Read finance references](./commands#command-list_references) (`list_references`)
- [Read reference history](./commands#command-reference_history) (`reference_history`)
- [Read operational transaction matrix](./commands#command-transaction_matrix)
  (`transaction_matrix`)
- [Read operational accounts](./commands#command-list_accounts) (`list_accounts`)
- [Read opening position context](./commands#command-opening_context) (`opening_context`)

**Exceptions to clear**

- [Unmatched financial event](./exceptions#exception-unmatched_financial_event)
  (`unmatched_financial_event`)

**Appears in processes:** [Finance set-up and period work](./processes#process-finance_setup)

**Underneath:** Tables: `ledger_entry`, `ledger_reversal`, `subledger_account`,
`finance_role_destination`, `accounting_target`, `accounting_target_reference`,
`finance_target_mapping_revision`, `source_classification_mapping_revision`, `financial_component`,
`component_assignment_revision`, `component_assignment_part`, `finance_reference`, `opening_scope`,
`opening_item_detail` · Events:
[`finance.target_configuration_changed`](./events#event-finance-target_configuration_changed),
[`finance.source_mapping_changed`](./events#event-finance-source_mapping_changed),
[`finance.component_assigned`](./events#event-finance-component_assigned),
[`finance.reference_changed`](./events#event-finance-reference_changed),
[`finance.account_changed`](./events#event-finance-account_changed),
[`ledger.posted`](./events#event-ledger-posted), [`ledger.reversed`](./events#event-ledger-reversed)

## Return {#resource-return}

_Customer returns, supplier returns and the credits they lead to_

A return is announced, arrives as a goods receipt, is decided on, and ends in a credit or refund.
Each step is its own record, so a return that stalls between two steps is visible.

**Also called:** RMA, return announcement, restocking fee, Retourenankündigung,
Retourenwareneingang, Lieferantenretoure, Wiedereinlagerungsgebühr

**Actions**

- [Announce customer return](./commands#command-announce_customer_return)
  (`announce_customer_return`)
- [Withdraw return announcement](./commands#command-withdraw_return_announcement)
  (`withdraw_return_announcement`)

**Look up**

- [Read announced returns](./commands#command-return_announcements) (`return_announcements`)

**Exceptions to clear**

- [Returned and not credited](./exceptions#exception-returned_not_credited)
  (`returned_not_credited`)
- [Credited and not returned](./exceptions#exception-credited_not_returned)
  (`credited_not_returned`)
- [Returned to supplier and not credited](./exceptions#exception-supplier_return_not_credited)
  (`supplier_return_not_credited`)
- [Supplier credited more than went back](./exceptions#exception-supplier_credit_not_returned)
  (`supplier_credit_not_returned`)
- [Return not dealt with](./exceptions#exception-return_unresolved) (`return_unresolved`)
- [Announced return has not arrived](./exceptions#exception-announced_return_not_arrived)
  (`announced_return_not_arrived`)

**Appears in processes:** [Procure to pay](./processes#process-procure_to_pay),
[Customer returns](./processes#process-returns)

**Underneath:** Tables: `return_announcement` · Events:
[`return.announced`](./events#event-return-announced),
[`return.announcement_withdrawn`](./events#event-return-announcement_withdrawn)

## Document and source system {#resource-source}

_Connected systems, imports, manual documents and stated facts_

Everything Reality knows arrives as an immutable source record from a system, a file or a person.
Documents are the normalized evidence; a fact is one stated observation about an existing record.
Interpretation failures and silent sources surface as exceptions.

**Also called:** ERP, shop, import, connector, interface, evidence, Schnittstelle, Import, Beleg,
Nachweis, Quelle

**Lists**

- [Documents](./views#view-documents) (`documents`)
- [Sources & imports](./views#view-sources_imports) (`sources_imports`)
- [Document register](./views#projection-document_register) (`document_register`)

**Actions**

- [Set source code mapping](./commands#command-set_source_mapping) (`set_source_mapping`)
- [Observe fact](./commands#command-observe_fact) (`observe_fact`)
- [Install mock connector shell](./commands#command-install_connector_shell)
  (`install_connector_shell`)
- [Define source system](./commands#command-create_source_system) (`create_source_system`)
- [Define source capability](./commands#command-create_source_capability)
  (`create_source_capability`)
- [Ingest arbitrary source](./commands#command-enqueue_source) (`enqueue_source`)
- [Correct manual document evidence](./commands#command-correct_manual_document)
  (`correct_manual_document`)
- [Record corrected document source](./commands#command-record_corrected_document_source)
  (`record_corrected_document_source`)
- [Hold document commitments](./commands#command-hold_document_commitments)
  (`hold_document_commitments`)
- [Record manual document](./commands#command-create_manual_document_with_lines)
  (`create_manual_document_with_lines`)

**Look up**

- [Preview Document](./commands#command-preview_document) (`preview_document`)
- [Read source code mappings](./commands#command-list_source_mappings) (`list_source_mappings`)
- [Read source mapping history](./commands#command-source_mapping_history)
  (`source_mapping_history`)

**Exceptions to clear**

- [Silent source](./exceptions#exception-silent_source) (`silent_source`)
- [Source interpretation failure](./exceptions#exception-source_interpretation_failure)
  (`source_interpretation_failure`)

**Appears in processes:** [Master data and sources](./processes#process-master_data)

**Underneath:** Tables: `source_system`, `source_capability`, `document`, `document_line`, `fact` ·
Events: [`finance.source_mapping_changed`](./events#event-finance-source_mapping_changed),
[`source_record.stored`](./events#event-source_record-stored),
[`fact.observed`](./events#event-fact-observed),
[`source_record.received`](./events#event-source_record-received),
[`source_record.unmapped`](./events#event-source_record-unmapped),
[`source_record.interpreted`](./events#event-source_record-interpreted),
[`document.recorded`](./events#event-document-recorded),
[`document.corrected`](./events#event-document-corrected) · Agent tools without a command:
[`interpretation_coverage`](./commands#tool-interpretation_coverage)

## Company and users {#resource-company}

_Members, invitations and what a company already uses_

Who may work in a company and how far its data has been set up. Every business record is scoped to
one company; another company's records behave as not found.

**Also called:** tenant, member, invitation, access, Mandant, Mitglied, Einladung, Zugang

**Lists**

- [Tenant usage](./views#projection-tenant_usage) (`tenant_usage`)

**Actions**

- [Invite company member](./commands#command-create_invitation) (`create_invitation`)
- [Resend company invitation](./commands#command-resend_invitation) (`resend_invitation`)
- [Revoke company invitation](./commands#command-revoke_invitation) (`revoke_invitation`)
- [Remove company member](./commands#command-remove_member) (`remove_member`)

**Underneath:** Tables: `company_invitation`, `invitation_delivery`, `tenant_membership`

## Approvals, exceptions and open questions {#resource-governance}

_What agents proposed, what needs attention, and what the records cannot answer_

An agent never changes business state directly: it proposes, a person approves, and the proposal
executes through the same command a clerk would use. Exceptions are the derived attention queue;
missing information collects questions the records cannot answer yet.

**Also called:** proposal, approval, exception, attention, missing information, Vorschlag, Freigabe,
Abweichung, Klärfall, Timeline, Verlauf

**Lists**

- [Activity](./views#view-activity) (`activity`)
- [Operational Exceptions](./views#projection-exceptions) (`exceptions`)
- [Timeline](./views#projection-timeline) (`timeline`)

**Underneath:** Agent tools without a command:
[`capability_describe`](./commands#tool-capability_describe),
[`business_records_discover`](./commands#tool-business_records_discover),
[`exceptions_list`](./commands#tool-exceptions_list),
[`exception_explain`](./commands#tool-exception_explain),
[`proposals_awaiting_approval`](./commands#tool-proposals_awaiting_approval),
[`proposal_execution_status`](./commands#tool-proposal_execution_status),
[`proposal_approve_and_execute`](./commands#tool-proposal_approve_and_execute),
[`reality_gaps`](./commands#tool-reality_gaps),
[`reality_gap_get`](./commands#tool-reality_gap_get),
[`reality_gap_simulate`](./commands#tool-reality_gap_simulate),
[`reality_gap_create_propose`](./commands#tool-reality_gap_create_propose),
[`reality_gap_entry_add_propose`](./commands#tool-reality_gap_entry_add_propose),
[`reality_gap_recommend_propose`](./commands#tool-reality_gap_recommend_propose),
[`reality_gap_decide_propose`](./commands#tool-reality_gap_decide_propose),
[`reality_gap_implementation_prepare_propose`](./commands#tool-reality_gap_implementation_prepare_propose),
[`reality_gap_rule_activate_propose`](./commands#tool-reality_gap_rule_activate_propose),
[`reality_gap_rule_disable_propose`](./commands#tool-reality_gap_rule_disable_propose),
[`reality_gap_rule_replay_propose`](./commands#tool-reality_gap_rule_replay_propose)
