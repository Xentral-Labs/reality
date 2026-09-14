# Business processes

The processes a consultant walks through, step by step: which object, which action, which list to
check afterwards, and which exceptions a step can leave behind. The agent playbooks carry the
narrative; these pages index the executable vocabulary.

> Automatically generated from `resource_catalog.yaml`. Do not edit this page by hand.

## Order to cash {#process-order_to_cash}

From a customer order through reservation, dispatch and invoice to the settled payment.

[Read the playbook](../agent-playbooks/order-to-cash-fulfilment)

[Play it as a storyline: Order to close](../storylines/#storyline-order-to-close)

### 1. Record the customer order

**Object:** [Order](./resources#resource-order)

**Actions**

- [Create manual sales or purchase order](./commands#command-create_manual_order)
  (`create_manual_order`)

**Check afterwards:** [Orders](./views#view-orders) (`orders`),
[Commitments](./views#view-commitments) (`commitments`)

**Can leave behind:** [Order stalled](./exceptions#exception-order_stalled) (`order_stalled`)

### 2. Reserve stock for the promise

**Object:** [Order](./resources#resource-order)

**Actions**

- [Reserve stock](./commands#command-reserve) (`reserve`)
- [Release reservation](./commands#command-release_reservation) (`release_reservation`)

**Check afterwards:** [Supply & demand](./views#view-supply_demand) (`supply_demand`),
[Reservations](./views#view-reservations) (`reservations`)

**Can leave behind:**
[Customer commitment at risk](./exceptions#exception-outgoing_commitment_at_risk)
(`outgoing_commitment_at_risk`),
[Reservation exceeds stock](./exceptions#exception-reservation_exceeds_stock)
(`reservation_exceeds_stock`)

### 3. Hold or revise when the customer or credit requires it

**Object:** [Order](./resources#resource-order)

**Actions**

- [Hold commitment](./commands#command-hold_commitment) (`hold_commitment`)
- [Set party delivery hold](./commands#command-hold_party_delivery) (`hold_party_delivery`)
- [Revise commitment](./commands#command-revise_commitment) (`revise_commitment`)

**Check afterwards:** [Fulfillment blockers](./views#view-fulfillment_blockers)
(`fulfillment_blockers`)

**Can leave behind:** [Promise hold not lifted](./exceptions#exception-commitment_hold_unreleased)
(`commitment_hold_unreleased`),
[Party hold not lifted](./exceptions#exception-party_hold_unreleased) (`party_hold_unreleased`),
[Credit limit exceeded](./exceptions#exception-credit_limit_exceeded) (`credit_limit_exceeded`)

### 4. Dispatch the goods and follow the carrier

**Object:** [Delivery and goods receipt](./resources#resource-delivery)

**Actions**

- [Dispatch or receive shipment package](./commands#command-record_packaged_execution)
  (`record_packaged_execution`)
- [Record shipment notice](./commands#command-record_shipment_notice) (`record_shipment_notice`)
- [Record shipment event](./commands#command-record_shipment_event) (`record_shipment_event`)
- [Explain a physical shipment](./commands#tool-shipment_explain) (`shipment_explain`)

**Check afterwards:** [Warehouse Queue](./views#view-warehouse_queue) (`warehouse_queue`),
[Movements](./views#view-movements) (`movements`)

**Can leave behind:**
[Overdue outgoing customer commitment](./exceptions#exception-overdue_outgoing_customer_commitment)
(`overdue_outgoing_customer_commitment`)

### 5. Bill what shipped

**Object:** [Invoice and credit note](./resources#resource-invoice)

**Actions**

- [Record sales invoice](./commands#command-record_sales_invoice) (`record_sales_invoice`)
- [Post sales invoice](./commands#command-post_sales_invoice) (`post_sales_invoice`)

**Check afterwards:** [Open items](./views#view-open_items) (`open_items`)

**Can leave behind:** [Shipped and not billed](./exceptions#exception-shipped_not_billed)
(`shipped_not_billed`), [Sales invoice not booked](./exceptions#exception-sales_invoice_unposted)
(`sales_invoice_unposted`)

### 6. Record the payment and allocate it

**Object:** [Payment and settlement](./resources#resource-payment)

**Actions**

- [Post customer payment](./commands#command-post_customer_payment) (`post_customer_payment`)
- [Record payment or use existing credit](./commands#command-apply_settlement) (`apply_settlement`)
- [Accept settlement reduction](./commands#command-accept_adjustment) (`accept_adjustment`)
- [Payment and credit context](./commands#tool-finance_settlement_context)
  (`finance_settlement_context`)
- [Party balances](./commands#tool-finance_party_balances) (`finance_party_balances`)

**Check afterwards:** [Payments](./views#view-payments) (`payments`),
[Open items](./views#view-open_items) (`open_items`)

**Can leave behind:** [Overdue receivable](./exceptions#exception-overdue_receivable)
(`overdue_receivable`),
[Unmatched financial event](./exceptions#exception-unmatched_financial_event)
(`unmatched_financial_event`)

### 7. Close promises that will never ship

**Object:** [Order](./resources#resource-order)

**Actions**

- [Preview stale promise closure](./commands#command-preview_stale_promise_closure)
  (`preview_stale_promise_closure`)
- [Close stale promises](./commands#command-close_stale_promises) (`close_stale_promises`)

**Check afterwards:** [Commitments](./views#view-commitments) (`commitments`)

**Can leave behind:** [Order stalled](./exceptions#exception-order_stalled) (`order_stalled`)

## Procure to pay {#process-procure_to_pay}

From the replenishment need through purchase order, goods receipt and invoice check to the payment
run.

[Read the playbook](../agent-playbooks/purchasing-and-replenishment)

[Play it as a storyline: Purchase to pay](../storylines/#storyline-purchase-to-pay)

### 1. Find what to buy

**Object:** [Item](./resources#resource-item)

**Actions**

- [Read item supply and demand](./commands#tool-item_supply_demand) (`item_supply_demand`)
- [Read fulfillment blockers](./commands#tool-fulfillment_blockers) (`fulfillment_blockers`)

**Check afterwards:** [Supply & demand](./views#view-supply_demand) (`supply_demand`),
[Fulfillment blockers](./views#view-fulfillment_blockers) (`fulfillment_blockers`)

**Can leave behind:**
[Customer commitment at risk](./exceptions#exception-outgoing_commitment_at_risk)
(`outgoing_commitment_at_risk`)

### 2. Place the purchase order

**Object:** [Order](./resources#resource-order)

**Actions**

- [Create manual sales or purchase order](./commands#command-create_manual_order)
  (`create_manual_order`)

**Check afterwards:** [Commitments](./views#view-commitments) (`commitments`)

**Can leave behind:**
[Overdue incoming supplier commitment](./exceptions#exception-overdue_incoming_supplier_commitment)
(`overdue_incoming_supplier_commitment`)

### 3. Receive the goods

**Object:** [Delivery and goods receipt](./resources#resource-delivery)

**Actions**

- [Dispatch or receive shipment package](./commands#command-record_packaged_execution)
  (`record_packaged_execution`)
- [Record movement](./commands#command-record_movement) (`record_movement`)
- [Create lot](./commands#command-create_lot) (`create_lot`)
- [State lot expiry](./commands#command-state_lot_expiry) (`state_lot_expiry`)

**Check afterwards:** [Movements](./views#view-movements) (`movements`),
[Inventory](./views#view-inventory) (`inventory`)

**Can leave behind:** [Unexplained movement](./exceptions#exception-unexplained_movement)
(`unexplained_movement`), [Expired stock on hand](./exceptions#exception-stock_expired)
(`stock_expired`)

### 4. Record and book the supplier invoice

**Object:** [Invoice and credit note](./resources#resource-invoice)

**Actions**

- [Record supplier invoice](./commands#command-record_supplier_invoice) (`record_supplier_invoice`)
- [Post supplier invoice](./commands#command-post_supplier_invoice) (`post_supplier_invoice`)

**Check afterwards:** [Open items](./views#view-open_items) (`open_items`)

**Can leave behind:** [Receipt not invoiced](./exceptions#exception-receipt_unbilled)
(`receipt_unbilled`),
[Supplier invoice not booked](./exceptions#exception-supplier_invoice_unposted)
(`supplier_invoice_unposted`),
[Duplicate supplier invoice](./exceptions#exception-duplicate_supplier_invoice)
(`duplicate_supplier_invoice`)

### 5. Check the invoice against order and receipt

**Object:** [Invoice and credit note](./resources#resource-invoice)

**Actions**

- [List operational exceptions](./commands#tool-exceptions_list) (`exceptions_list`)
- [Explain an operational exception](./commands#tool-exception_explain) (`exception_explain`)

**Check afterwards:** [Open items](./views#view-open_items) (`open_items`)

**Can leave behind:** [Billed and not received](./exceptions#exception-billed_not_received)
(`billed_not_received`),
[Invoice price differs from the agreement](./exceptions#exception-invoice_price_differs)
(`invoice_price_differs`)

### 6. Pay suppliers with a payment run

**Object:** [Payment and settlement](./resources#resource-payment)

**Actions**

- [Preview payment run](./commands#command-preview_payment_run) (`preview_payment_run`)
- [Execute payment run](./commands#command-execute_payment_run) (`execute_payment_run`)
- [Post supplier payment](./commands#command-post_supplier_payment) (`post_supplier_payment`)

**Check afterwards:** [Payments](./views#view-payments) (`payments`)

**Can leave behind:** [Overdue payable](./exceptions#exception-overdue_payable) (`overdue_payable`),
[Early payment discount still available](./exceptions#exception-purchase_discount_available)
(`purchase_discount_available`)

### 7. Handle supplier credits and returns to the supplier

**Object:** [Return](./resources#resource-return)

**Actions**

- [Post supplier credit note](./commands#command-post_supplier_credit_note)
  (`post_supplier_credit_note`)
- [Net supplier credit against invoice](./commands#command-allocate_supplier_credit_note)
  (`allocate_supplier_credit_note`)
- [Post supplier refund](./commands#command-post_supplier_refund) (`post_supplier_refund`)

**Check afterwards:** [Open items](./views#view-open_items) (`open_items`)

**Can leave behind:**
[Returned to supplier and not credited](./exceptions#exception-supplier_return_not_credited)
(`supplier_return_not_credited`),
[Supplier credited more than went back](./exceptions#exception-supplier_credit_not_returned)
(`supplier_credit_not_returned`),
[Supplier credit not claimed](./exceptions#exception-supplier_credit_unclaimed)
(`supplier_credit_unclaimed`)

## Customer returns {#process-returns}

From the announcement through the goods receipt and the decision to credit note or refund.

[Read the playbook](../agent-playbooks/returns)

### 1. The customer announces a return

**Object:** [Return](./resources#resource-return)

**Actions**

- [Announce customer return](./commands#command-announce_customer_return)
  (`announce_customer_return`)
- [Withdraw return announcement](./commands#command-withdraw_return_announcement)
  (`withdraw_return_announcement`)
- [Read announced returns](./commands#command-return_announcements) (`return_announcements`)

**Can leave behind:**
[Announced return has not arrived](./exceptions#exception-announced_return_not_arrived)
(`announced_return_not_arrived`)

### 2. The goods arrive

**Object:** [Delivery and goods receipt](./resources#resource-delivery)

**Actions**

- [Dispatch or receive shipment package](./commands#command-record_packaged_execution)
  (`record_packaged_execution`)
- [Record movement](./commands#command-record_movement) (`record_movement`)

**Check afterwards:** [Movements](./views#view-movements) (`movements`),
[Inventory](./views#view-inventory) (`inventory`)

**Can leave behind:** [Return not dealt with](./exceptions#exception-return_unresolved)
(`return_unresolved`)

### 3. Credit the customer

**Object:** [Invoice and credit note](./resources#resource-invoice)

**Actions**

- [Record return credit](./commands#command-record_sales_credit) (`record_sales_credit`)
- [Post credit note](./commands#command-post_sales_credit_note) (`post_sales_credit_note`)
- [Record manual document](./commands#command-create_manual_document_with_lines)
  (`create_manual_document_with_lines`)

**Check afterwards:** [Open items](./views#view-open_items) (`open_items`)

**Can leave behind:** [Returned and not credited](./exceptions#exception-returned_not_credited)
(`returned_not_credited`), [Credited and not returned](./exceptions#exception-credited_not_returned)
(`credited_not_returned`), [Credit note not booked](./exceptions#exception-credit_note_unposted)
(`credit_note_unposted`)

### 4. Net the credit or refund the money

**Object:** [Payment and settlement](./resources#resource-payment)

**Actions**

- [Net credit note against invoice](./commands#command-allocate_credit_note)
  (`allocate_credit_note`)
- [Post customer refund](./commands#command-post_customer_refund) (`post_customer_refund`)
- [Available credit](./commands#tool-finance_credits) (`finance_credits`)

**Check afterwards:** [Payments](./views#view-payments) (`payments`),
[Open items](./views#view-open_items) (`open_items`)

**Can leave behind:** [Credit note not given back](./exceptions#exception-credit_note_unsettled)
(`credit_note_unsettled`)

## Master data and sources {#process-master_data}

Set up partners, items, locations, prices and terms, connect the systems that deliver them, and keep
them current.

[Read the playbook](../agent-playbooks/master-data-and-sources)

### 1. Create partners

**Object:** [Business partner](./resources#resource-party)

**Actions**

- [Create party](./commands#command-create_party) (`create_party`)
- [Create item](./commands#command-create_item) (`create_item`)
- [Create location](./commands#command-create_location) (`create_location`)
- [Change master-data lifecycle](./commands#command-set_master_data_active)
  (`set_master_data_active`)

**Check afterwards:** [Parties](./views#view-parties) (`parties`), [Items](./views#view-items)
(`items`), [Locations](./views#view-locations) (`locations`)

**Can leave behind:** [Units not comparable](./exceptions#exception-units_not_comparable)
(`units_not_comparable`)

### 2. Keep them current

**Object:** [Item](./resources#resource-item)

**Actions**

- [Update party](./commands#command-update_party) (`update_party`)
- [Update item](./commands#command-update_item) (`update_item`)
- [Update location](./commands#command-update_location) (`update_location`)

**Check afterwards:** [Parties](./views#view-parties) (`parties`), [Items](./views#view-items)
(`items`), [Locations](./views#view-locations) (`locations`)

### 3. Prices

**Object:** [Prices and payment terms](./resources#resource-terms)

**Actions**

- [Create price list](./commands#command-create_price_list) (`create_price_list`)
- [Add price tier](./commands#command-create_price_list_entry) (`create_price_list_entry`)
- [Assign party price list](./commands#command-assign_party_price_list) (`assign_party_price_list`)
- [Create and assign pricing group](./commands#command-create_party_group) (`create_party_group`)
- [Create payment term](./commands#command-create_payment_term) (`create_payment_term`)

**Check afterwards:** [Commercial terms](./views#view-commercial_terms) (`commercial_terms`)

**Can leave behind:**
[Invoice price differs from the agreement](./exceptions#exception-invoice_price_differs)
(`invoice_price_differs`),
[Sold below the purchase price](./exceptions#exception-sold_below_purchase_price)
(`sold_below_purchase_price`)

### 4. Register a source and what it may deliver

**Object:** [Document and source system](./resources#resource-source)

**Actions**

- [Define source system](./commands#command-create_source_system) (`create_source_system`)
- [Define source capability](./commands#command-create_source_capability)
  (`create_source_capability`)
- [Install mock connector shell](./commands#command-install_connector_shell)
  (`install_connector_shell`)
- [Ingest arbitrary source](./commands#command-enqueue_source) (`enqueue_source`)

**Check afterwards:** [Sources & imports](./views#view-sources_imports) (`sources_imports`),
[Documents](./views#view-documents) (`documents`)

**Can leave behind:** [Silent source](./exceptions#exception-silent_source) (`silent_source`),
[Source interpretation failure](./exceptions#exception-source_interpretation_failure)
(`source_interpretation_failure`)

### 5. State a fact the records are missing

**Object:** [Document and source system](./resources#resource-source)

**Actions**

- [Observe fact](./commands#command-observe_fact) (`observe_fact`)
- [List missing information](./commands#tool-reality_gaps) (`reality_gaps`)
- [Propose missing information](./commands#tool-reality_gap_create_propose)
  (`reality_gap_create_propose`)

**Check afterwards:** [Documents](./views#view-documents) (`documents`)

## Finance set-up and period work {#process-finance_setup}

Accounts, opening balances, the mapping to the external accounting system and reversals.

[Read the playbook](../agent-playbooks/receivables-and-payments)

### 1. Set up operational accounts

**Object:** [Ledger and accounts](./resources#resource-accounting)

**Actions**

- [Initialize operational accounts](./commands#command-initialize_accounts) (`initialize_accounts`)
- [Create operational account](./commands#command-create_account) (`create_account`)
- [Update operational account](./commands#command-update_account) (`update_account`)
- [Set operational account default](./commands#command-set_default_account) (`set_default_account`)

**Check afterwards:** [Journal](./views#view-journal) (`journal`)

### 2. Import opening positions

**Object:** [Ledger and accounts](./resources#resource-accounting)

**Actions**

- [Read opening position context](./commands#command-opening_context) (`opening_context`)
- [Import opening positions](./commands#command-import_opening) (`import_opening`)

**Check afterwards:** [Open items](./views#view-open_items) (`open_items`),
[Journal](./views#view-journal) (`journal`)

### 3. Map postings to the external accounting system

**Object:** [Ledger and accounts](./resources#resource-accounting)

**Actions**

- [Maintain Target Configuration](./commands#command-maintain_target_configuration)
  (`maintain_target_configuration`)
- [Maintain finance reference](./commands#command-maintain_reference) (`maintain_reference`)
- [Set source code mapping](./commands#command-set_source_mapping) (`set_source_mapping`)
- [Assign received financial component](./commands#command-assign_component) (`assign_component`)

**Check afterwards:** [Journal](./views#view-journal) (`journal`)

### 4. Reverse a wrong posting

**Object:** [Ledger and accounts](./resources#resource-accounting)

**Actions**

- [Reverse ledger posting group](./commands#command-reverse_ledger_posting_group)
  (`reverse_ledger_posting_group`)
- [Correct movement](./commands#command-correct_movement) (`correct_movement`)

**Check afterwards:** [Journal](./views#view-journal) (`journal`),
[Movements](./views#view-movements) (`movements`)

**Can leave behind:** [Unmatched financial event](./exceptions#exception-unmatched_financial_event)
(`unmatched_financial_event`)
