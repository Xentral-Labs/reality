# Geschäftsaktionen

Jede gemeinsam implementierte ändernde oder lesende Operation, geschrieben wie eine Handbuchseite:
was sie tut, wie ein Agent sie aufruft, welche Parameter sie nimmt und was danach zu lesen ist. CLI,
Web, API, Chat und MCP erreichen dieselbe Operation.

> Automatisch aus `command_catalog.yaml`, `reality/mcp/catalog.py` erzeugt. Diese Seite nicht von
> Hand bearbeiten.

| Schlüssel                                                                         | Bezeichnung                               | Bereich                 | Agenten-Tools                                                                                                                                                                                | Erreichbar über                         |
| --------------------------------------------------------------------------------- | ----------------------------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| [`create_invitation`](#command-create_invitation)                                 | Invite company member                     | Unternehmen & Zugang    | `member_invite_propose`                                                                                                                                                                      | Web · API · MCP · Chat                  |
| [`remove_member`](#command-remove_member)                                         | Remove company member                     | Unternehmen & Zugang    | `member_remove_propose`                                                                                                                                                                      | Web · API · MCP · Chat                  |
| [`resend_invitation`](#command-resend_invitation)                                 | Resend company invitation                 | Unternehmen & Zugang    | `invitation_resend_propose`                                                                                                                                                                  | Web · API · MCP · Chat                  |
| [`revoke_invitation`](#command-revoke_invitation)                                 | Revoke company invitation                 | Unternehmen & Zugang    | `invitation_revoke_propose`                                                                                                                                                                  | Web · API · MCP · Chat                  |
| [`assign_supply`](#command-assign_supply)                                         | Assign incoming supply to customer demand | Bereichsübergreifend    | `supply_assign_propose`                                                                                                                                                                      | CLI · Web · API · MCP · Chat            |
| [`change_graph_report`](#command-change_graph_report)                             | Change Private Graph Report               | Bereichsübergreifend    | `graph_report_change_propose`                                                                                                                                                                | Web · MCP · Chat                        |
| [`execute_cost_change`](#command-execute_cost_change)                             | Confirm cost and contribution decision    | Bereichsübergreifend    | `cost_change_propose`                                                                                                                                                                        | CLI · Web · MCP · Chat                  |
| [`cost_review_draft`](#command-cost_review_draft)                                 | Draft a cost review                       | Bereichsübergreifend    | `cost_review_draft`                                                                                                                                                                          | Web · MCP · Chat                        |
| [`cost_record`](#command-cost_record)                                             | Inspect retained cost record              | Bereichsübergreifend    | `cost_record_get`                                                                                                                                                                            | CLI · Web · MCP · Chat                  |
| [`notices`](#command-notices)                                                     | List dunning notices                      | Bereichsübergreifend    | `finance_dunning_notices`                                                                                                                                                                    | Web · MCP · Chat                        |
| [`contribution_preview`](#command-contribution_preview)                           | Preview current contribution candidate    | Bereichsübergreifend    | `cost_contribution_preview`                                                                                                                                                                  | CLI · Web · MCP · Chat                  |
| [`cost_query`](#command-cost_query)                                               | Read cost query context                   | Bereichsübergreifend    | `cost_query_get`                                                                                                                                                                             | CLI · Web · MCP · Chat                  |
| [`dunning_context`](#command-dunning_context)                                     | Read dunning context                      | Bereichsübergreifend    | `finance_dunning_context`                                                                                                                                                                    | Web · MCP · Chat                        |
| [`notice_detail`](#command-notice_detail)                                         | Read dunning notice                       | Bereichsübergreifend    | `finance_dunning_notice`                                                                                                                                                                     | Web · MCP · Chat                        |
| [`receipt_cost`](#command-receipt_cost)                                           | Read receipt acquisition costs            | Bereichsübergreifend    | `cost_receipt_get`                                                                                                                                                                           | CLI · Web · MCP · Chat                  |
| [`cost_evidence`](#command-cost_evidence)                                         | Read received acquisition-cost evidence   | Bereichsübergreifend    | `cost_evidence_get`                                                                                                                                                                          | CLI · Web · MCP · Chat                  |
| [`reviewed_contribution`](#command-reviewed_contribution)                         | Read reviewed commercial contribution     | Bereichsübergreifend    | `cost_contribution_get`                                                                                                                                                                      | CLI · Web · MCP · Chat                  |
| [`record_notice`](#command-record_notice)                                         | Record dunning notice                     | Bereichsübergreifend    | `finance_dunning_record_propose`                                                                                                                                                             | Web · MCP · Chat                        |
| [`reverse_notice`](#command-reverse_notice)                                       | Reverse dunning notice                    | Bereichsübergreifend    | `finance_dunning_reverse_propose`                                                                                                                                                            | Web · MCP · Chat                        |
| [`accept_adjustment`](#command-accept_adjustment)                                 | Accept settlement reduction               | Finanzen                | `finance_adjustment_propose`                                                                                                                                                                 | CLI · Web · MCP · Chat                  |
| [`assign_component`](#command-assign_component)                                   | Assign received financial component       | Finanzen                | `finance_component_assign_propose`                                                                                                                                                           | CLI · Web · MCP · Chat                  |
| [`create_account`](#command-create_account)                                       | Create operational account                | Finanzen                | `finance_create_account_propose`                                                                                                                                                             | CLI · Web · MCP · Chat                  |
| [`execute_payment_run`](#command-execute_payment_run)                             | Execute payment run                       | Finanzen                | `payment_run_propose`                                                                                                                                                                        | Web · MCP · Chat                        |
| [`import_opening`](#command-import_opening)                                       | Import opening positions                  | Finanzen                | `finance_opening_propose`                                                                                                                                                                    | CLI · Web · MCP · Chat                  |
| [`initialize_accounts`](#command-initialize_accounts)                             | Initialize operational accounts           | Finanzen                | `finance_initialize_accounts_propose`                                                                                                                                                        | CLI · Web · MCP · Chat                  |
| [`list_mappings`](#command-list_mappings)                                         | List Mappings                             | Finanzen                | `finance_target_mappings`                                                                                                                                                                    | CLI · Web · MCP · Chat                  |
| [`list_target_references`](#command-list_target_references)                       | List Target References                    | Finanzen                | `finance_target_references`                                                                                                                                                                  | CLI · Web · MCP · Chat                  |
| [`list_targets`](#command-list_targets)                                           | List Targets                              | Finanzen                | `finance_targets`                                                                                                                                                                            | CLI · Web · MCP · Chat                  |
| [`maintain_target_configuration`](#command-maintain_target_configuration)         | Maintain Target Configuration             | Finanzen                | `finance_target_create_propose`, `finance_target_update_propose`, `finance_target_reference_create_propose`, `finance_target_reference_update_propose`, `finance_target_mapping_set_propose` | CLI · Web · MCP · Chat                  |
| [`maintain_reference`](#command-maintain_reference)                               | Maintain finance reference                | Finanzen                | `finance_reference_create_propose`, `finance_reference_update_propose`                                                                                                                       | CLI · Web · MCP · Chat                  |
| [`mapping_history`](#command-mapping_history)                                     | Mapping History                           | Finanzen                | `finance_target_mapping_history`                                                                                                                                                             | CLI · Web · MCP · Chat                  |
| [`allocate_credit_note`](#command-allocate_credit_note)                           | Net credit note against invoice           | Finanzen                | `credit_note_allocate_propose`                                                                                                                                                               | Web · MCP · Chat                        |
| [`allocate_supplier_credit_note`](#command-allocate_supplier_credit_note)         | Net supplier credit against invoice       | Finanzen                | `supplier_credit_note_allocate_propose`                                                                                                                                                      | Web · MCP · Chat                        |
| [`post_sales_credit_note`](#command-post_sales_credit_note)                       | Post credit note                          | Finanzen                | `credit_note_post_propose`                                                                                                                                                                   | Web · MCP · Chat                        |
| [`post_customer_payment`](#command-post_customer_payment)                         | Post customer payment                     | Finanzen                | `customer_payment_post_propose`                                                                                                                                                              | CLI · Web · MCP · Chat                  |
| [`post_customer_refund`](#command-post_customer_refund)                           | Post customer refund                      | Finanzen                | `customer_refund_post_propose`                                                                                                                                                               | Web · MCP · Chat                        |
| [`post_sales_invoice`](#command-post_sales_invoice)                               | Post sales invoice                        | Finanzen                | `sales_invoice_post_propose`                                                                                                                                                                 | Web · MCP · Chat                        |
| [`post_supplier_credit_note`](#command-post_supplier_credit_note)                 | Post supplier credit note                 | Finanzen                | `supplier_credit_note_post_propose`                                                                                                                                                          | Web · MCP · Chat                        |
| [`post_supplier_invoice`](#command-post_supplier_invoice)                         | Post supplier invoice                     | Finanzen                | `supplier_invoice_post_propose`                                                                                                                                                              | Web · MCP · Chat                        |
| [`post_supplier_payment`](#command-post_supplier_payment)                         | Post supplier payment                     | Finanzen                | `supplier_payment_post_propose`                                                                                                                                                              | CLI · Web · MCP · Chat                  |
| [`post_supplier_refund`](#command-post_supplier_refund)                           | Post supplier refund                      | Finanzen                | `supplier_refund_post_propose`                                                                                                                                                               | Web · MCP · Chat                        |
| [`preview_payment_run`](#command-preview_payment_run)                             | Preview payment run                       | Finanzen                | `payment_run_preview`                                                                                                                                                                        | Web · MCP · Chat                        |
| [`component_history`](#command-component_history)                                 | Read component assignment history         | Finanzen                | `finance_component_history`                                                                                                                                                                  | CLI · Web · MCP · Chat                  |
| [`list_references`](#command-list_references)                                     | Read finance references                   | Finanzen                | `finance_references`                                                                                                                                                                         | CLI · Web · MCP · Chat                  |
| [`invoice_credit_context`](#command-invoice_credit_context)                       | Read invoice credit context               | Finanzen                | `invoice_credit_context`                                                                                                                                                                     | Web · MCP · Chat                        |
| [`opening_context`](#command-opening_context)                                     | Read opening position context             | Finanzen                | `finance_opening_context`                                                                                                                                                                    | CLI · Web · MCP · Chat                  |
| [`list_accounts`](#command-list_accounts)                                         | Read operational accounts                 | Finanzen                | `finance_accounts`                                                                                                                                                                           | CLI · Web · MCP · Chat                  |
| [`transaction_matrix`](#command-transaction_matrix)                               | Read operational transaction matrix       | Finanzen                | `finance_matrix`                                                                                                                                                                             | CLI · Web · MCP · Chat                  |
| [`settlement_context`](#command-settlement_context)                               | Read payment and credit context           | Finanzen                | `finance_settlement_context`                                                                                                                                                                 | CLI · Web · MCP · Chat                  |
| [`component_context`](#command-component_context)                                 | Read received financial detail            | Finanzen                | `finance_components`                                                                                                                                                                         | CLI · Web · MCP · Chat                  |
| [`reference_history`](#command-reference_history)                                 | Read reference history                    | Finanzen                | `finance_reference_history`                                                                                                                                                                  | CLI · Web · MCP · Chat                  |
| [`adjustment_context`](#command-adjustment_context)                               | Read settlement reduction context         | Finanzen                | `finance_adjustment_context`                                                                                                                                                                 | CLI · Web · MCP · Chat                  |
| [`list_source_mappings`](#command-list_source_mappings)                           | Read source code mappings                 | Finanzen                | `finance_source_mappings`                                                                                                                                                                    | CLI · Web · MCP · Chat                  |
| [`source_mapping_history`](#command-source_mapping_history)                       | Read source mapping history               | Finanzen                | `finance_source_mapping_history`                                                                                                                                                             | CLI · Web · MCP · Chat                  |
| [`record_free_supplier_invoice`](#command-record_free_supplier_invoice)           | Record free supplier invoice              | Finanzen                | `supplier_invoice_free_record_propose`                                                                                                                                                       | Web · MCP · Chat                        |
| [`apply_settlement`](#command-apply_settlement)                                   | Record payment or use existing credit     | Finanzen                | `finance_settlement_propose`                                                                                                                                                                 | CLI · Web · MCP · Chat                  |
| [`record_sales_credit`](#command-record_sales_credit)                             | Record return credit                      | Finanzen                | `sales_credit_record_propose`                                                                                                                                                                | Web · API · MCP · Chat                  |
| [`record_sales_invoice`](#command-record_sales_invoice)                           | Record sales invoice                      | Finanzen                | `sales_invoice_record_propose`                                                                                                                                                               | Web · API · MCP · Chat                  |
| [`record_supplier_invoice`](#command-record_supplier_invoice)                     | Record supplier invoice                   | Finanzen                | `supplier_invoice_record_propose`                                                                                                                                                            | Web · API · MCP · Chat                  |
| [`reverse_ledger_posting_group`](#command-reverse_ledger_posting_group)           | Reverse ledger posting group              | Finanzen                | `ledger_reversal_propose`                                                                                                                                                                    | CLI · Web · API · Chat · MCP            |
| [`set_default_account`](#command-set_default_account)                             | Set operational account default           | Finanzen                | `finance_set_default_account_propose`                                                                                                                                                        | CLI · Web · MCP · Chat                  |
| [`set_source_mapping`](#command-set_source_mapping)                               | Set source code mapping                   | Finanzen                | `finance_source_mapping_propose`                                                                                                                                                             | CLI · Web · MCP · Chat                  |
| [`update_account`](#command-update_account)                                       | Update operational account                | Finanzen                | `finance_update_account_propose`                                                                                                                                                             | CLI · Web · MCP · Chat                  |
| [`create_price_list_entry`](#command-create_price_list_entry)                     | Add price tier                            | Stammdaten & Preise     | `price_tier_create_propose`                                                                                                                                                                  | CLI · Web · API · MCP · Chat            |
| [`assign_party_price_list`](#command-assign_party_price_list)                     | Assign party price list                   | Stammdaten & Preise     | `party_price_list_assign_propose`                                                                                                                                                            | CLI · Web · API · MCP · Chat            |
| [`set_master_data_active`](#command-set_master_data_active)                       | Change master-data lifecycle              | Stammdaten & Preise     | `master_data_lifecycle_propose`                                                                                                                                                              | CLI · Web · API · MCP · Chat            |
| [`create_party_group`](#command-create_party_group)                               | Create and assign pricing group           | Stammdaten & Preise     | `party_group_create_propose`, `party_group_update_propose`, `party_group_member_add_propose`, `group_price_list_assign_propose`                                                              | CLI · Web · API · MCP · Chat            |
| [`create_item`](#command-create_item)                                             | Create item                               | Stammdaten & Preise     | `item_create_propose`                                                                                                                                                                        | CLI · Web · API · MCP · Chat            |
| [`create_location`](#command-create_location)                                     | Create location                           | Stammdaten & Preise     | `location_create_propose`                                                                                                                                                                    | CLI · Web · API · MCP · Chat            |
| [`create_party`](#command-create_party)                                           | Create party                              | Stammdaten & Preise     | `party_create_propose`                                                                                                                                                                       | CLI · Web · API · MCP · Chat            |
| [`create_payment_term`](#command-create_payment_term)                             | Create payment term                       | Stammdaten & Preise     | `payment_term_create_propose`, `payment_term_update_propose`                                                                                                                                 | CLI · Web · API · MCP · Chat            |
| [`create_price_list`](#command-create_price_list)                                 | Create price list                         | Stammdaten & Preise     | `price_list_create_propose`, `price_list_update_propose`                                                                                                                                     | CLI · Web · API · MCP · Chat            |
| [`commercial_match`](#command-commercial_match)                                   | Read reviewed partial commercial match    | Stammdaten & Preise     | `cost_commercial_match_get`                                                                                                                                                                  | CLI · Web · MCP · Chat                  |
| [`resolve_price`](#command-resolve_price)                                         | Resolve authoritative price quote         | Stammdaten & Preise     | `price_quote_read`                                                                                                                                                                           | CLI · Web · API · MCP · Chat            |
| [`update_item`](#command-update_item)                                             | Update item                               | Stammdaten & Preise     | `item_update_propose`                                                                                                                                                                        | CLI · Web · API · MCP · Chat            |
| [`update_location`](#command-update_location)                                     | Update location                           | Stammdaten & Preise     | `location_update_propose`                                                                                                                                                                    | CLI · Web · API · MCP · Chat            |
| [`update_party`](#command-update_party)                                           | Update party                              | Stammdaten & Preise     | `party_update_propose`                                                                                                                                                                       | CLI · Web · API · MCP · Chat            |
| [`announce_customer_return`](#command-announce_customer_return)                   | Announce customer return                  | Aufträge & Erfüllung    | `return_announce_propose`                                                                                                                                                                    | Web · API · MCP · Chat                  |
| [`cancel_commitment`](#command-cancel_commitment)                                 | Cancel commitment remainder               | Aufträge & Erfüllung    | `commitment_cancel_propose`                                                                                                                                                                  | CLI · Web · API · MCP · Chat            |
| [`close_stale_promises`](#command-close_stale_promises)                           | Close stale promises                      | Aufträge & Erfüllung    | `stale_closure_propose`                                                                                                                                                                      | Web · MCP · Chat                        |
| [`create_manual_order`](#command-create_manual_order)                             | Create manual sales or purchase order     | Aufträge & Erfüllung    | `order_create_propose`                                                                                                                                                                       | Web · MCP · Chat                        |
| [`hold_commitment`](#command-hold_commitment)                                     | Hold commitment                           | Aufträge & Erfüllung    | `commitment_hold_propose`, `commitment_hold_release_propose`                                                                                                                                 | CLI · Web · API · MCP · Chat            |
| [`hold_document_commitments`](#command-hold_document_commitments)                 | Hold document commitments                 | Aufträge & Erfüllung    | `document_hold_propose`, `document_hold_release_propose`                                                                                                                                     | CLI · Web · API · MCP · Chat            |
| [`preview_stale_promise_closure`](#command-preview_stale_promise_closure)         | Preview stale promise closure             | Aufträge & Erfüllung    | `stale_closure_preview`                                                                                                                                                                      | Web · MCP · Chat                        |
| [`return_announcements`](#command-return_announcements)                           | Read announced returns                    | Aufträge & Erfüllung    | `return_announcements`                                                                                                                                                                       | Web · API · MCP · Chat                  |
| [`release_reservation`](#command-release_reservation)                             | Release reservation                       | Aufträge & Erfüllung    | `reservation_release_propose`                                                                                                                                                                | CLI · Web · API · MCP · Chat            |
| [`reserve`](#command-reserve)                                                     | Reserve stock                             | Aufträge & Erfüllung    | `reservation_propose`                                                                                                                                                                        | CLI · Web · API · MCP · Chat            |
| [`record_return_disposition`](#command-record_return_disposition)                 | Resolve arrived customer-return goods     | Aufträge & Erfüllung    | `return_disposition_propose`                                                                                                                                                                 | CLI · Web · API · MCP · Chat            |
| [`revise_commitment`](#command-revise_commitment)                                 | Revise commitment                         | Aufträge & Erfüllung    | `commitment_revise_propose`                                                                                                                                                                  | Web · MCP · Chat                        |
| [`hold_party_delivery`](#command-hold_party_delivery)                             | Set party delivery hold                   | Aufträge & Erfüllung    | `party_delivery_hold_propose`, `party_delivery_hold_release_propose`                                                                                                                         | CLI · Web · API · MCP · Chat            |
| [`withdraw_return_announcement`](#command-withdraw_return_announcement)           | Withdraw return announcement              | Aufträge & Erfüllung    | `return_announcement_withdraw_propose`                                                                                                                                                       | Web · API · MCP · Chat                  |
| [`correct_manual_document`](#command-correct_manual_document)                     | Correct manual document evidence          | Belege, Quellen & Facts | `document_correct_propose`, `document_lines_correct_propose`                                                                                                                                 | Web · API · MCP · Chat                  |
| [`create_source_capability`](#command-create_source_capability)                   | Define source capability                  | Belege, Quellen & Facts | `source_capability_create_propose`, `source_capability_lifecycle_propose`                                                                                                                    | CLI · Web · API · MCP · Chat            |
| [`create_source_system`](#command-create_source_system)                           | Define source system                      | Belege, Quellen & Facts | `source_system_create_propose`, `source_system_lifecycle_propose`                                                                                                                            | CLI · Web · API · MCP · Chat            |
| [`enqueue_source`](#command-enqueue_source)                                       | Ingest arbitrary source                   | Belege, Quellen & Facts | `source_ingest_propose`, `source_record_ingest_propose`                                                                                                                                      | CLI · Web · API · MCP · Chat            |
| [`install_connector_shell`](#command-install_connector_shell)                     | Install mock connector shell              | Belege, Quellen & Facts | `connector_install_propose`                                                                                                                                                                  | CLI · Web · API · MCP · Chat            |
| [`observe_fact`](#command-observe_fact)                                           | Observe fact                              | Belege, Quellen & Facts | `fact_observe_propose`                                                                                                                                                                       | Web · MCP · Chat                        |
| [`preview_document`](#command-preview_document)                                   | Preview Document                          | Belege, Quellen & Facts | `finance_target_mapping_preview`                                                                                                                                                             | CLI · Web · MCP · Chat                  |
| [`record_corrected_document_source`](#command-record_corrected_document_source)   | Record corrected document source          | Belege, Quellen & Facts | `document_source_correct_propose`                                                                                                                                                            | Web · API · MCP · Chat                  |
| [`create_manual_document_with_lines`](#command-create_manual_document_with_lines) | Record manual document                    | Belege, Quellen & Facts | `document_create_propose`                                                                                                                                                                    | Web · API · MCP · Chat                  |
| [`correct_lot_expiry`](#command-correct_lot_expiry)                               | Correct lot expiry                        | Lager & Logistik        | `lot_expiry_correct_propose`                                                                                                                                                                 | CLI · Web · API · MCP · Chat            |
| [`correct_movement`](#command-correct_movement)                                   | Correct movement                          | Lager & Logistik        | `movement_correction_propose`                                                                                                                                                                | CLI · Web · API · Chat · MCP            |
| [`create_handling_unit`](#command-create_handling_unit)                           | Create handling unit                      | Lager & Logistik        | `handling_unit_create_propose`                                                                                                                                                               | CLI · Web · API · MCP · Chat            |
| [`create_lot`](#command-create_lot)                                               | Create lot                                | Lager & Logistik        | `lot_create_propose`                                                                                                                                                                         | CLI · Web · API · MCP · Chat            |
| [`create_serial_unit`](#command-create_serial_unit)                               | Create serial unit                        | Lager & Logistik        | `serial_unit_create_propose`                                                                                                                                                                 | CLI · Web · API · MCP · Chat            |
| [`record_packaged_execution`](#command-record_packaged_execution)                 | Dispatch or receive shipment package      | Lager & Logistik        | `shipment_dispatch_propose`, `shipment_receive_propose`                                                                                                                                      | CLI · Web · API · MCP · Chat            |
| [`expired_lots`](#command-expired_lots)                                           | Read expired lots                         | Lager & Logistik        | `expired_lots`                                                                                                                                                                               | Web · API · MCP · Chat                  |
| [`inventory_cost`](#command-inventory_cost)                                       | Read reviewed inventory acquisition costs | Lager & Logistik        | `cost_inventory_get`                                                                                                                                                                         | CLI · Web · MCP · Chat                  |
| [`record_movement`](#command-record_movement)                                     | Record movement                           | Lager & Logistik        | `movement_create_propose`                                                                                                                                                                    | CLI · Web · API · scenario · MCP · Chat |
| [`record_shipment_event`](#command-record_shipment_event)                         | Record shipment event                     | Lager & Logistik        | `shipment_event_record_propose`                                                                                                                                                              | CLI · Web · API · MCP · Chat            |
| [`record_shipment_notice`](#command-record_shipment_notice)                       | Record shipment notice                    | Lager & Logistik        | `shipment_notice_record_propose`                                                                                                                                                             | CLI · Web · API · MCP · Chat            |
| [`state_lot_expiry`](#command-state_lot_expiry)                                   | State lot expiry                          | Lager & Logistik        | `lot_expiry_state_propose`                                                                                                                                                                   | CLI · Web · API · MCP · Chat            |
| [`supersede_shipment_event`](#command-supersede_shipment_event)                   | Supersede shipment event                  | Lager & Logistik        | `shipment_event_supersede_propose`                                                                                                                                                           | CLI · Web · API · MCP · Chat            |

## Unternehmen & Zugang

### `create_invitation` — Invite company member {#command-create_invitation}

Creates an owner-authorized company invitation and atomically queues its first delivery.

**Aufruf**

```text
member_invite_propose email [locale]
```

**Erreichbar über:** Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `tenant`, `tenant_membership`, `company_invitation` · Schreibt:
`company_invitation`, `invitation_delivery`, `security_audit_event`

**Siehe auch:** Agenten-Tool [`member_invite_propose`](./commands#tool-member_invite_propose)

#### `member_invite_propose` — Invite company member {#tool-member_invite_propose}

Prepare this business mutation without changing state. Invite company member. Human confirmation is
required.

**Aufruf**

```text
member_invite_propose email [locale]
```

**Zugriff:** `propose`

**Parameter**

| Name     | Typ      | Pflicht | Beschreibung                                                                                                   | Standard |
| -------- | -------- | ------- | -------------------------------------------------------------------------------------------------------------- | -------- |
| `email`  | `string` | ja      | Email address supplied for the named business purpose.                                                         | —        |
| `locale` | `string` | nein    | Preferred supported language for invitation delivery, with the documented fallback when absent or unsupported. | `en`     |

**Siehe auch:** Geschäftsaktion [`create_invitation`](./commands#command-create_invitation)

### `remove_member` — Remove company member {#command-remove_member}

Archives a non-owner company membership after owner reauthorization.

**Aufruf**

```text
member_remove_propose membership_id
```

**Erreichbar über:** Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `tenant_membership` · Schreibt: `tenant_membership`, `security_audit_event`

**Siehe auch:** Agenten-Tool [`member_remove_propose`](./commands#tool-member_remove_propose)

#### `member_remove_propose` — Remove company member {#tool-member_remove_propose}

Prepare this business mutation without changing state. Remove company member. Human confirmation is
required.

**Aufruf**

```text
member_remove_propose membership_id
```

**Zugriff:** `propose`

**Parameter**

| Name            | Typ      | Pflicht | Beschreibung                                         | Standard |
| --------------- | -------- | ------- | ---------------------------------------------------- | -------- |
| `membership_id` | `string` | ja      | Opaque identity of the company membership to remove. | —        |

**Siehe auch:** Geschäftsaktion [`remove_member`](./commands#command-remove_member)

### `resend_invitation` — Resend company invitation {#command-resend_invitation}

Invalidates older delivery generations and queues a fresh invitation delivery after owner
reauthorization.

**Aufruf**

```text
invitation_resend_propose invitation_id
```

**Erreichbar über:** Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `tenant_membership`, `company_invitation`, `invitation_delivery` · Schreibt:
`company_invitation`, `invitation_delivery`, `security_audit_event`

**Siehe auch:** Agenten-Tool
[`invitation_resend_propose`](./commands#tool-invitation_resend_propose)

#### `invitation_resend_propose` — Resend company invitation {#tool-invitation_resend_propose}

Prepare this business mutation without changing state. Resend company invitation. Human confirmation
is required.

**Aufruf**

```text
invitation_resend_propose invitation_id
```

**Zugriff:** `propose`

**Parameter**

| Name            | Typ      | Pflicht | Beschreibung                                                   | Standard |
| --------------- | -------- | ------- | -------------------------------------------------------------- | -------- |
| `invitation_id` | `string` | ja      | Opaque identity of the company invitation to resend or revoke. | —        |

**Siehe auch:** Geschäftsaktion [`resend_invitation`](./commands#command-resend_invitation)

### `revoke_invitation` — Revoke company invitation {#command-revoke_invitation}

Revokes a pending invitation after owner reauthorization.

**Aufruf**

```text
invitation_revoke_propose invitation_id
```

**Erreichbar über:** Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `tenant_membership`, `company_invitation` · Schreibt: `company_invitation`,
`security_audit_event`

**Siehe auch:** Agenten-Tool
[`invitation_revoke_propose`](./commands#tool-invitation_revoke_propose)

#### `invitation_revoke_propose` — Revoke company invitation {#tool-invitation_revoke_propose}

Prepare this business mutation without changing state. Revoke company invitation. Human confirmation
is required.

**Aufruf**

```text
invitation_revoke_propose invitation_id
```

**Zugriff:** `propose`

**Parameter**

| Name            | Typ      | Pflicht | Beschreibung                                                   | Standard |
| --------------- | -------- | ------- | -------------------------------------------------------------- | -------- |
| `invitation_id` | `string` | ja      | Opaque identity of the company invitation to resend or revoke. | —        |

**Siehe auch:** Geschäftsaktion [`revoke_invitation`](./commands#command-revoke_invitation)

## Stammdaten & Preise

### `create_price_list_entry` — Add price tier {#command-create_price_list_entry}

Adds an item price selected from an inclusive minimum quantity.

**Aufruf**

```text
price_tier_create_propose price_list_id item_id min_quantity unit_price unit [valid_from] [valid_until]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `price_list`, `item` · Schreibt: `price_list_entry` · Erzeugt:
`price_list_entry.created`

**Siehe auch:** Agenten-Tool
[`price_tier_create_propose`](./commands#tool-price_tier_create_propose), Event
[`price_list_entry.created`](./events#event-price_list_entry-created)

#### `price_tier_create_propose` — Add price tier {#tool-price_tier_create_propose}

Prepare this business mutation without changing state. Add price tier. Human confirmation is
required.

**Aufruf**

```text
price_tier_create_propose price_list_id item_id min_quantity unit_price unit [valid_from] [valid_until]
```

**Zugriff:** `propose`

**Parameter**

| Name            | Typ      | Pflicht | Beschreibung                                                                      | Standard |
| --------------- | -------- | ------- | --------------------------------------------------------------------------------- | -------- |
| `price_list_id` | `string` | ja      | Opaque identity of the sales or purchase price list.                              | —        |
| `item_id`       | `string` | ja      | Opaque identity of the operational item reference.                                | —        |
| `min_quantity`  | `string` | ja      | Inclusive quantity threshold from which a price tier applies.                     | —        |
| `unit_price`    | `string` | ja      | Decimal monetary amount for one unit before quantity multiplication.              | —        |
| `unit`          | `string` | ja      | Unit of measure in which the quantity is expressed.                               | —        |
| `valid_from`    | `string` | nein    | Inclusive UTC instant from which a rule or price may be selected.                 | —        |
| `valid_until`   | `string` | nein    | Optional inclusive UTC instant after which a rule or price is no longer selected. | —        |

**Siehe auch:** Geschäftsaktion
[`create_price_list_entry`](./commands#command-create_price_list_entry)

### `assign_party_price_list` — Assign party price list {#command-assign_party_price_list}

Gives a customer or supplier a directly prioritized price list.

**Aufruf**

```text
party_price_list_assign_propose party_id price_list_id [priority]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `party`, `price_list` · Schreibt: `party_price_list` · Erzeugt:
`party_price_list.assigned`

**Siehe auch:** Agenten-Tool
[`party_price_list_assign_propose`](./commands#tool-party_price_list_assign_propose), Event
[`party_price_list.assigned`](./events#event-party_price_list-assigned)

#### `party_price_list_assign_propose` — Assign party price list {#tool-party_price_list_assign_propose}

Prepare this business mutation without changing state. Assign party price list. Human confirmation
is required.

**Aufruf**

```text
party_price_list_assign_propose party_id price_list_id [priority]
```

**Zugriff:** `propose`

**Parameter**

| Name            | Typ       | Pflicht | Beschreibung                                                           | Standard |
| --------------- | --------- | ------- | ---------------------------------------------------------------------- | -------- |
| `party_id`      | `string`  | ja      | Opaque identity of the customer, supplier, or other operational party. | —        |
| `price_list_id` | `string`  | ja      | Opaque identity of the sales or purchase price list.                   | —        |
| `priority`      | `integer` | nein    | Ordering used when more than one eligible rule could apply.            | `100`    |

**Siehe auch:** Geschäftsaktion
[`assign_party_price_list`](./commands#command-assign_party_price_list)

### `set_master_data_active` — Change master-data lifecycle {#command-set_master_data_active}

Activates or deactivates master data without deleting historical relationships.

**Aufruf**

```text
master_data_lifecycle_propose model record_id is_active
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `party`, `item`, `location`, `payment_term` · Schreibt: `party`, `item`,
`location`, `payment_term` · Erzeugt: `master_data.lifecycle_changed`

**Siehe auch:** Agenten-Tool
[`master_data_lifecycle_propose`](./commands#tool-master_data_lifecycle_propose), Event
[`master_data.lifecycle_changed`](./events#event-master_data-lifecycle_changed)

#### `master_data_lifecycle_propose` — Change master-data lifecycle {#tool-master_data_lifecycle_propose}

Prepare this business mutation without changing state. Change master-data lifecycle. Human
confirmation is required.

**Aufruf**

```text
master_data_lifecycle_propose model record_id is_active
```

**Zugriff:** `propose`

**Parameter**

| Name        | Typ       | Pflicht | Beschreibung                                                                                           | Standard |
| ----------- | --------- | ------- | ------------------------------------------------------------------------------------------------------ | -------- |
| `model`     | `string`  | ja      | Target master-data model whose lifecycle is being changed. `party`, `item`, `location`, `payment_term` | —        |
| `record_id` | `string`  | ja      | Opaque identity of the master-data record whose lifecycle is being changed.                            | —        |
| `is_active` | `boolean` | ja      | Whether the record remains selectable for new operational work.                                        | —        |

**Siehe auch:** Geschäftsaktion
[`set_master_data_active`](./commands#command-set_master_data_active)

### `create_party_group` — Create and assign pricing group {#command-create_party_group}

Builds reusable customer or supplier group pricing without copying prices onto parties.

**Aufruf**

```text
party_group_create_propose code name
party_group_update_propose party_group_id code name
party_group_member_add_propose party_group_id party_id
group_price_list_assign_propose party_group_id price_list_id [priority]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `party`, `price_list`, `party_group` · Schreibt: `party_group`,
`party_group_member`, `party_group_price_list` · Erzeugt: `party_group.created`

**Siehe auch:** Agenten-Tool
[`party_group_create_propose`](./commands#tool-party_group_create_propose), Agenten-Tool
[`party_group_update_propose`](./commands#tool-party_group_update_propose), Agenten-Tool
[`party_group_member_add_propose`](./commands#tool-party_group_member_add_propose), Agenten-Tool
[`group_price_list_assign_propose`](./commands#tool-group_price_list_assign_propose), Event
[`party_group.created`](./events#event-party_group-created)

#### `party_group_create_propose` — Create party group {#tool-party_group_create_propose}

Prepare this business mutation without changing state. Create party group. Human confirmation is
required.

**Aufruf**

```text
party_group_create_propose code name
```

**Zugriff:** `propose`

**Parameter**

| Name   | Typ      | Pflicht | Beschreibung                                                             | Standard |
| ------ | -------- | ------- | ------------------------------------------------------------------------ | -------- |
| `code` | `string` | ja      | Short tenant-scoped business code used to find the record operationally. | —        |
| `name` | `string` | ja      | Human-readable display name; it is not used as internal identity.        | —        |

**Siehe auch:** Geschäftsaktion [`create_party_group`](./commands#command-create_party_group)

#### `party_group_update_propose` — Update party group {#tool-party_group_update_propose}

Prepare this business mutation without changing state. Update party group. Human confirmation is
required.

**Aufruf**

```text
party_group_update_propose party_group_id code name
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ      | Pflicht | Beschreibung                                                             | Standard |
| ---------------- | -------- | ------- | ------------------------------------------------------------------------ | -------- |
| `party_group_id` | `string` | ja      | Opaque identity of a pricing or operational party group.                 | —        |
| `code`           | `string` | ja      | Short tenant-scoped business code used to find the record operationally. | —        |
| `name`           | `string` | ja      | Human-readable display name; it is not used as internal identity.        | —        |

**Siehe auch:** Geschäftsaktion [`create_party_group`](./commands#command-create_party_group)

#### `party_group_member_add_propose` — Add party group member {#tool-party_group_member_add_propose}

Prepare this business mutation without changing state. Add party group member. Human confirmation is
required.

**Aufruf**

```text
party_group_member_add_propose party_group_id party_id
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ      | Pflicht | Beschreibung                                                           | Standard |
| ---------------- | -------- | ------- | ---------------------------------------------------------------------- | -------- |
| `party_group_id` | `string` | ja      | Opaque identity of a pricing or operational party group.               | —        |
| `party_id`       | `string` | ja      | Opaque identity of the customer, supplier, or other operational party. | —        |

**Siehe auch:** Geschäftsaktion [`create_party_group`](./commands#command-create_party_group)

#### `group_price_list_assign_propose` — Assign group price list {#tool-group_price_list_assign_propose}

Prepare this business mutation without changing state. Assign group price list. Human confirmation
is required.

**Aufruf**

```text
group_price_list_assign_propose party_group_id price_list_id [priority]
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ       | Pflicht | Beschreibung                                                | Standard |
| ---------------- | --------- | ------- | ----------------------------------------------------------- | -------- |
| `party_group_id` | `string`  | ja      | Opaque identity of a pricing or operational party group.    | —        |
| `price_list_id`  | `string`  | ja      | Opaque identity of the sales or purchase price list.        | —        |
| `priority`       | `integer` | nein    | Ordering used when more than one eligible rule could apply. | `100`    |

**Siehe auch:** Geschäftsaktion [`create_party_group`](./commands#command-create_party_group)

### `create_item` — Create item {#command-create_item}

Creates an operational item identity with inventory and purchasing behavior.

**Aufruf**

```text
item_create_propose records
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `location` · Schreibt: `source_record`, `item` · Erzeugt:
`item.created`

**Siehe auch:** Agenten-Tool [`item_create_propose`](./commands#tool-item_create_propose), Event
[`item.created`](./events#event-item-created)

#### `item_create_propose` — Propose Item creation {#tool-item_create_propose}

Prepare manual creation of one or more Items. SKU and name are required, unit defaults to pcs, and
source provenance is optional. Human confirmation is required.

**Aufruf**

```text
item_create_propose records
```

**Zugriff:** `propose`

**Parameter**

| Name                            | Typ       | Pflicht | Beschreibung                                                                                            | Standard  |
| ------------------------------- | --------- | ------- | ------------------------------------------------------------------------------------------------------- | --------- |
| `records`                       | `array`   | ja      | Several master-data records stated together, each with the same fields the single-record command takes. | —         |
| `records[].sku`                 | `string`  | ja      | Human-facing stock-keeping code used to find an item; internal joins use item_id.                       | —         |
| `records[].name`                | `string`  | ja      | Human-readable display name; it is not used as internal identity.                                       | —         |
| `records[].unit`                | `string`  | nein    | Unit of measure in which the quantity is expressed.                                                     | `pcs`     |
| `records[].item_type`           | `string`  | nein    | Operational classification such as product, service, or charge. `stocked`, `service`, `charge`          | `stocked` |
| `records[].tracking_type`       | `string`  | nein    | Inventory identity policy; untracked, lot, or serial. `none`, `lot`, `serial`                           | `none`    |
| `records[].default_location_id` | `string`  | nein    | Opaque identity of the item's preferred operational stock location.                                     | —         |
| `records[].purchase_unit`       | `string`  | nein    | Unit in which the item is normally purchased from suppliers.                                            | —         |
| `records[].conversion_factor`   | `string`  | nein    | Quantity of base units represented by one purchase unit.                                                | `1`       |
| `records[].lead_time_days`      | `integer` | nein    | Expected calendar days required before supply becomes available.                                        | `0`       |
| `records[].source_system`       | `string`  | nein    | Tenant-scoped code naming the external origin of a record.                                              | —         |
| `records[].external_id`         | `string`  | nein    | Identifier assigned by the named external source system; never internal identity.                       | —         |
| `records[].source_payload`      | `object`  | nein    | Lossless external JSON evidence from which typed operational fields were selected.                      | —         |

**Siehe auch:** Geschäftsaktion [`create_item`](./commands#command-create_item)

### `create_location` — Create location {#command-create_location}

Creates a stock-capable or logical location and validates its parent.

**Aufruf**

```text
location_create_propose records
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `location` · Schreibt: `source_record`, `location` · Erzeugt:
`location.created`

**Siehe auch:** Agenten-Tool [`location_create_propose`](./commands#tool-location_create_propose),
Event [`location.created`](./events#event-location-created)

#### `location_create_propose` — Propose Location creation {#tool-location_create_propose}

Prepare manual creation of one or more Locations. Name is required and type defaults to warehouse.
For a hierarchy created in this batch, give parents a ref and children a parent_ref;
parent_location_id accepts only an existing opaque ID, never a name. Source provenance is optional.
Human confirmation is required.

**Aufruf**

```text
location_create_propose records
```

**Zugriff:** `propose`

**Parameter**

| Name                           | Typ       | Pflicht | Beschreibung                                                                                                                                                     | Standard    |
| ------------------------------ | --------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| `records`                      | `array`   | ja      | Several master-data records stated together, each with the same fields the single-record command takes.                                                          | —           |
| `records[].ref`                | `string`  | nein    | Optional local reference used by later records in the same batch.                                                                                                | —           |
| `records[].name`               | `string`  | ja      | Human-readable display name; it is not used as internal identity.                                                                                                | —           |
| `records[].type`               | `string`  | nein    | Closed kind of the record where one is stated, such as a party's primary role or a location's type; the roles list, not this field, decides what a party may do. | `warehouse` |
| `records[].parent_ref`         | `string`  | nein    | Local ref of an earlier Location in the same batch. Use this for newly created hierarchies.                                                                      | —           |
| `records[].parent_location_id` | `string`  | nein    | Opaque ID of an existing Location. Never pass a name here.                                                                                                       | —           |
| `records[].allows_stock`       | `boolean` | nein    | Whether physical inventory may be held at this location.                                                                                                         | `True`      |
| `records[].source_system`      | `string`  | nein    | Tenant-scoped code naming the external origin of a record.                                                                                                       | —           |
| `records[].external_id`        | `string`  | nein    | Identifier assigned by the named external source system; never internal identity.                                                                                | —           |
| `records[].source_payload`     | `object`  | nein    | Lossless external JSON evidence from which typed operational fields were selected.                                                                               | —           |

**Siehe auch:** Geschäftsaktion [`create_location`](./commands#command-create_location)

### `create_party` — Create party {#command-create_party}

Creates a tenant-scoped party, optional immutable source evidence, operational roles, and exact
correspondence addresses.

**Aufruf**

```text
party_create_propose records
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `source_record`, `party` · Schreibt: `source_record`, `party`,
`party_role`, `party_email_address` · Erzeugt: `party.created`

**Siehe auch:** Agenten-Tool [`party_create_propose`](./commands#tool-party_create_propose), Event
[`party.created`](./events#event-party-created)

#### `party_create_propose` — Propose Party creation {#tool-party_create_propose}

Prepare manual creation of one or more Parties. Name and roles are required; source provenance is
optional. Human confirmation is required.

**Aufruf**

```text
party_create_propose records
```

**Zugriff:** `propose`

**Parameter**

| Name                          | Typ      | Pflicht | Beschreibung                                                                                                                                                                                       | Standard |
| ----------------------------- | -------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `records`                     | `array`  | ja      | Several master-data records stated together, each with the same fields the single-record command takes.                                                                                            | —        |
| `records[].name`              | `string` | ja      | Human-readable display name; it is not used as internal identity.                                                                                                                                  | —        |
| `records[].roles`             | `array`  | ja      | Operational roles assigned to a party, for example customer or supplier. `company`, `customer`, `supplier`                                                                                         | —        |
| `records[].type`              | `string` | nein    | Closed kind of the record where one is stated, such as a party's primary role or a location's type; the roles list, not this field, decides what a party may do. `company`, `customer`, `supplier` | —        |
| `records[].accounting_code`   | `string` | nein    | Accounting reference used when postings or exports need a stable account mapping.                                                                                                                  | —        |
| `records[].payment_term_code` | `string` | nein    | Tenant-scoped code of the payment condition to apply.                                                                                                                                              | —        |
| `records[].default_currency`  | `string` | nein    | ISO 4217 currency used when an operation provides no explicit currency.                                                                                                                            | `EUR`    |
| `records[].credit_limit`      | `string` | nein    | Optional monetary exposure limit used by operational credit checks.                                                                                                                                | `0`      |
| `records[].tax_identifier`    | `string` | nein    | External tax or VAT identifier retained when operational matching requires it.                                                                                                                     | —        |
| `records[].emails`            | `array`  | nein    | Bounded labelled email addresses recorded for exact Party matching.                                                                                                                                | `[]`     |
| `records[].emails[].email`    | `string` | ja      | Email address supplied for the named business purpose.                                                                                                                                             | —        |
| `records[].emails[].label`    | `string` | nein    | Optional human-readable description of a value's business purpose.                                                                                                                                 | —        |
| `records[].source_system`     | `string` | nein    | Tenant-scoped code naming the external origin of a record.                                                                                                                                         | —        |
| `records[].external_id`       | `string` | nein    | Identifier assigned by the named external source system; never internal identity.                                                                                                                  | —        |
| `records[].source_payload`    | `object` | nein    | Lossless external JSON evidence from which typed operational fields were selected.                                                                                                                 | —        |

**Siehe auch:** Geschäftsaktion [`create_party`](./commands#command-create_party)

### `create_payment_term` — Create payment term {#command-create_payment_term}

Creates a reusable payment condition identified by an opaque ID.

**Aufruf**

```text
payment_term_create_propose code name due_days [discount_percent] [discount_days] [requires_prepayment] [source_system] [external_id] [source_payload]
payment_term_update_propose payment_term_id code name due_days [discount_percent] [discount_days] [requires_prepayment]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `payment_term` · Schreibt: `source_record`, `payment_term` · Erzeugt:
`payment_term.created`

**Siehe auch:** Agenten-Tool
[`payment_term_create_propose`](./commands#tool-payment_term_create_propose), Agenten-Tool
[`payment_term_update_propose`](./commands#tool-payment_term_update_propose), Event
[`payment_term.created`](./events#event-payment_term-created)

#### `payment_term_create_propose` — Create payment term {#tool-payment_term_create_propose}

Prepare this business mutation without changing state. Create payment term. Human confirmation is
required.

**Aufruf**

```text
payment_term_create_propose code name due_days [discount_percent] [discount_days] [requires_prepayment] [source_system] [external_id] [source_payload]
```

**Zugriff:** `propose`

**Parameter**

| Name                  | Typ       | Pflicht | Beschreibung                                                                                                            | Standard |
| --------------------- | --------- | ------- | ----------------------------------------------------------------------------------------------------------------------- | -------- |
| `code`                | `string`  | ja      | Short tenant-scoped business code used to find the record operationally.                                                | —        |
| `name`                | `string`  | ja      | Human-readable display name; it is not used as internal identity.                                                       | —        |
| `due_days`            | `integer` | ja      | Number of calendar days from the document date until payment is due.                                                    | —        |
| `discount_percent`    | `string`  | nein    | Early-payment discount rate the term grants, above zero and below 100; stated together with the days or not at all.     | —        |
| `discount_days`       | `integer` | nein    | Days from the invoice date within which an early-payment discount applies; stated together with the rate or not at all. | —        |
| `requires_prepayment` | `boolean` | nein    | Whether customer delivery requires qualifying allocated payment evidence before dispatch.                               | —        |
| `source_system`       | `string`  | nein    | Tenant-scoped code naming the external origin of a record.                                                              | —        |
| `external_id`         | `string`  | nein    | Identifier assigned by the named external source system; never internal identity.                                       | —        |
| `source_payload`      | `object`  | nein    | Lossless external JSON evidence from which typed operational fields were selected.                                      | —        |

**Siehe auch:** Geschäftsaktion [`create_payment_term`](./commands#command-create_payment_term)

#### `payment_term_update_propose` — Update payment term {#tool-payment_term_update_propose}

Prepare this business mutation without changing state. Update payment term. Human confirmation is
required.

**Aufruf**

```text
payment_term_update_propose payment_term_id code name due_days [discount_percent] [discount_days] [requires_prepayment]
```

**Zugriff:** `propose`

**Parameter**

| Name                  | Typ       | Pflicht | Beschreibung                                                                                                            | Standard |
| --------------------- | --------- | ------- | ----------------------------------------------------------------------------------------------------------------------- | -------- |
| `payment_term_id`     | `string`  | ja      | Opaque identity of the payment condition whose lifecycle is changed.                                                    | —        |
| `code`                | `string`  | ja      | Short tenant-scoped business code used to find the record operationally.                                                | —        |
| `name`                | `string`  | ja      | Human-readable display name; it is not used as internal identity.                                                       | —        |
| `due_days`            | `integer` | ja      | Number of calendar days from the document date until payment is due.                                                    | —        |
| `discount_percent`    | `string`  | nein    | Early-payment discount rate the term grants, above zero and below 100; stated together with the days or not at all.     | —        |
| `discount_days`       | `integer` | nein    | Days from the invoice date within which an early-payment discount applies; stated together with the rate or not at all. | —        |
| `requires_prepayment` | `boolean` | nein    | Whether customer delivery requires qualifying allocated payment evidence before dispatch.                               | —        |

**Siehe auch:** Geschäftsaktion [`create_payment_term`](./commands#command-create_payment_term)

### `create_price_list` — Create price list {#command-create_price_list}

Creates a sales or purchase list and enforces one active default per direction and currency.

**Aufruf**

```text
price_list_create_propose code name direction currency [valid_from] [valid_until] [is_default] [source_system] [external_id] [source_payload]
price_list_update_propose price_list_id code name direction currency [is_default]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `price_list` · Schreibt: `source_record`, `price_list` · Erzeugt:
`price_list.created`

**Siehe auch:** Agenten-Tool
[`price_list_create_propose`](./commands#tool-price_list_create_propose), Agenten-Tool
[`price_list_update_propose`](./commands#tool-price_list_update_propose), Event
[`price_list.created`](./events#event-price_list-created)

#### `price_list_create_propose` — Create price list {#tool-price_list_create_propose}

Prepare this business mutation without changing state. Create price list. Human confirmation is
required.

**Aufruf**

```text
price_list_create_propose code name direction currency [valid_from] [valid_until] [is_default] [source_system] [external_id] [source_payload]
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ       | Pflicht | Beschreibung                                                                                  | Standard |
| ---------------- | --------- | ------- | --------------------------------------------------------------------------------------------- | -------- |
| `code`           | `string`  | ja      | Short tenant-scoped business code used to find the record operationally.                      | —        |
| `name`           | `string`  | ja      | Human-readable display name; it is not used as internal identity.                             | —        |
| `direction`      | `string`  | ja      | Business flow direction, such as sales or purchase, incoming or outgoing. `sales`, `purchase` | —        |
| `currency`       | `string`  | ja      | ISO 4217 currency code for monetary values.                                                   | —        |
| `valid_from`     | `string`  | nein    | Inclusive UTC instant from which a rule or price may be selected.                             | —        |
| `valid_until`    | `string`  | nein    | Optional inclusive UTC instant after which a rule or price is no longer selected.             | —        |
| `is_default`     | `boolean` | nein    | Whether this rule is the fallback for its direction and currency.                             | `False`  |
| `source_system`  | `string`  | nein    | Tenant-scoped code naming the external origin of a record.                                    | —        |
| `external_id`    | `string`  | nein    | Identifier assigned by the named external source system; never internal identity.             | —        |
| `source_payload` | `object`  | nein    | Lossless external JSON evidence from which typed operational fields were selected.            | —        |

**Siehe auch:** Geschäftsaktion [`create_price_list`](./commands#command-create_price_list)

#### `price_list_update_propose` — Update price list {#tool-price_list_update_propose}

Prepare this business mutation without changing state. Update price list. Human confirmation is
required.

**Aufruf**

```text
price_list_update_propose price_list_id code name direction currency [is_default]
```

**Zugriff:** `propose`

**Parameter**

| Name            | Typ       | Pflicht | Beschreibung                                                                                  | Standard |
| --------------- | --------- | ------- | --------------------------------------------------------------------------------------------- | -------- |
| `price_list_id` | `string`  | ja      | Opaque identity of the sales or purchase price list.                                          | —        |
| `code`          | `string`  | ja      | Short tenant-scoped business code used to find the record operationally.                      | —        |
| `name`          | `string`  | ja      | Human-readable display name; it is not used as internal identity.                             | —        |
| `direction`     | `string`  | ja      | Business flow direction, such as sales or purchase, incoming or outgoing. `sales`, `purchase` | —        |
| `currency`      | `string`  | ja      | ISO 4217 currency code for monetary values.                                                   | —        |
| `is_default`    | `boolean` | nein    | Whether this rule is the fallback for its direction and currency.                             | `False`  |

**Siehe auch:** Geschäftsaktion [`create_price_list`](./commands#command-create_price_list)

### `commercial_match` — Read reviewed partial commercial match {#command-commercial_match}

Derive DB1 from one confirmed partial commercial match or reproduce an exact retained revision
without creating financial authority.

**Aufruf**

```text
cost_commercial_match_get document_line_id [match_revision_id]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document_line`, `cost_commercial_match_revision`,
`cost_commercial_inventory_part`, `cost_commercial_direct_part`, `cost_inventory_member`,
`cost_inventory_review`, `cost_policy_revision`, `cost_movement_basis`, `cost_attribution_revision`,
`cost_attribution_part`, `cost_component_basis`, `financial_component` · Schreibt: —

**Siehe auch:** Agenten-Tool
[`cost_commercial_match_get`](./commands#tool-cost_commercial_match_get)

#### `cost_commercial_match_get` — Reviewed partial commercial match {#tool-cost_commercial_match_get}

Read one confirmed partial commercial match or exact historical revision from retained revenue and
frozen cost evidence.

**Aufruf**

```text
cost_commercial_match_get document_line_id [match_revision_id]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                | Art                        | Standard |
| ------------------------------- | -------------------------- | -------- |
| `MCP cost_commercial_match_get` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read a confirmed partial commercial match and derive DB1 from its retained revenue and frozen cost
references.

**Verwenden, wenn**

- Explain split billing, partial fulfilment, direct service input or an exact historical
  credit/return match.

**Nicht verwenden, wenn**

- Infer a match, allocate a partial direct component, or request company-wide contribution
  reporting.

**Parameter**

| Name                | Typ      | Pflicht | Beschreibung                                                                                              | Standard |
| ------------------- | -------- | ------- | --------------------------------------------------------------------------------------------------------- | -------- |
| `document_line_id`  | `string` | ja      | Opaque same-tenant received document line identity; must belong to the selected document.                 | —        |
| `match_revision_id` | `string` | nein    | Exact retained commercial match revision identity; absence selects the latest revision for the sold line. | `None`   |

**Siehe auch:** Geschäftsaktion [`commercial_match`](./commands#command-commercial_match)

### `resolve_price` — Resolve authoritative price quote {#command-resolve_price}

Selects the currently applicable quantity tier and exposes the direct, group, or default assignment
path without copying a price.

**Aufruf**

```text
price_quote_read party_id item_id quantity direction currency unit [at]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `party`, `item`, `party_price_list`, `party_group`, `party_group_member`,
`party_group_price_list`, `price_list`, `price_list_entry` · Schreibt: —

**Siehe auch:** Agenten-Tool [`price_quote_read`](./commands#tool-price_quote_read)

#### `price_quote_read` — Read authoritative price quote {#tool-price_quote_read}

Resolve the applicable party-aware quantity tier and explain its assignment path; returns an
explicit no-match result when no price applies.

**Aufruf**

```text
price_quote_read party_id item_id quantity direction currency unit [at]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage       | Art                        | Standard |
| ---------------------- | -------------------------- | -------- |
| `MCP price_quote_read` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read the authoritative price tier for one party, item, quantity and commercial context, including
why that list won.

**Verwenden, wenn**

- A quote or order needs the currently applicable sales or purchase unit price.

**Nicht verwenden, wenn**

- A price list or assignment must be changed
- or an already agreed document price must be reconstructed.

**Parameter**

| Name        | Typ      | Pflicht | Beschreibung                                                                                  | Standard |
| ----------- | -------- | ------- | --------------------------------------------------------------------------------------------- | -------- |
| `party_id`  | `string` | ja      | Opaque identity of the customer, supplier, or other operational party.                        | —        |
| `item_id`   | `string` | ja      | Opaque identity of the operational item reference.                                            | —        |
| `quantity`  | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                       | —        |
| `direction` | `string` | ja      | Business flow direction, such as sales or purchase, incoming or outgoing. `sales`, `purchase` | —        |
| `currency`  | `string` | ja      | ISO 4217 currency code for monetary values.                                                   | —        |
| `unit`      | `string` | ja      | Unit of measure in which the quantity is expressed.                                           | —        |
| `at`        | `string` | nein    | UTC instant at which the projection or rule should be evaluated.                              | —        |

**Siehe auch:** Geschäftsaktion [`resolve_price`](./commands#command-resolve_price)

### `update_item` — Update item {#command-update_item}

Updates operational item fields while preserving external evidence versions and emitting an exact
before/after audit diff.

**Aufruf**

```text
item_update_propose records
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `item`, `location`, `source_record` · Schreibt: `source_record`, `item`,
`business_event` · Erzeugt: `item.updated`

**Siehe auch:** Agenten-Tool [`item_update_propose`](./commands#tool-item_update_propose), Event
[`item.updated`](./events#event-item-updated)

#### `item_update_propose` — Propose Item update {#tool-item_update_propose}

Prepare updates to existing Items identified only by opaque ID. Exact changes are previewed and a
separate decision is required.

**Aufruf**

```text
item_update_propose records
```

**Zugriff:** `propose`

**Parameter**

| Name                            | Typ       | Pflicht | Beschreibung                                                                                            | Standard |
| ------------------------------- | --------- | ------- | ------------------------------------------------------------------------------------------------------- | -------- |
| `records`                       | `array`   | ja      | Several master-data records stated together, each with the same fields the single-record command takes. | —        |
| `records[].id`                  | `string`  | ja      | Opaque Item ID.                                                                                         | —        |
| `records[].sku`                 | `string`  | ja      | Human-facing stock-keeping code used to find an item; internal joins use item_id.                       | —        |
| `records[].name`                | `string`  | ja      | Human-readable display name; it is not used as internal identity.                                       | —        |
| `records[].unit`                | `string`  | ja      | Unit of measure in which the quantity is expressed.                                                     | —        |
| `records[].item_type`           | `string`  | nein    | Operational classification such as product, service, or charge. `stocked`, `service`, `charge`          | —        |
| `records[].tracking_type`       | `string`  | nein    | Inventory identity policy; untracked, lot, or serial. `none`, `lot`, `serial`                           | —        |
| `records[].default_location_id` | `string`  | nein    | Opaque identity of the item's preferred operational stock location.                                     | —        |
| `records[].purchase_unit`       | `string`  | nein    | Unit in which the item is normally purchased from suppliers.                                            | —        |
| `records[].conversion_factor`   | `string`  | nein    | Quantity of base units represented by one purchase unit.                                                | —        |
| `records[].lead_time_days`      | `integer` | nein    | Expected calendar days required before supply becomes available.                                        | —        |
| `records[].source_system`       | `string`  | nein    | Tenant-scoped code naming the external origin of a record.                                              | —        |
| `records[].external_id`         | `string`  | nein    | Identifier assigned by the named external source system; never internal identity.                       | —        |
| `records[].source_payload`      | `object`  | nein    | Lossless external JSON evidence from which typed operational fields were selected.                      | —        |

**Siehe auch:** Geschäftsaktion [`update_item`](./commands#command-update_item)

### `update_location` — Update location {#command-update_location}

Updates location behavior, rejects hierarchy cycles, and emits an exact before/after audit diff.

**Aufruf**

```text
location_update_propose records
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `location`, `source_record` · Schreibt: `source_record`, `location`,
`business_event` · Erzeugt: `location.updated`

**Siehe auch:** Agenten-Tool [`location_update_propose`](./commands#tool-location_update_propose),
Event [`location.updated`](./events#event-location-updated)

#### `location_update_propose` — Propose Location update {#tool-location_update_propose}

Prepare updates to existing Locations identified only by opaque ID. Parent locations also use opaque
IDs. Exact changes are previewed and a separate decision is required.

**Aufruf**

```text
location_update_propose records
```

**Zugriff:** `propose`

**Parameter**

| Name                           | Typ       | Pflicht | Beschreibung                                                                                                                                                     | Standard |
| ------------------------------ | --------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `records`                      | `array`   | ja      | Several master-data records stated together, each with the same fields the single-record command takes.                                                          | —        |
| `records[].id`                 | `string`  | ja      | Opaque Location ID.                                                                                                                                              | —        |
| `records[].ref`                | `string`  | nein    | Optional local reference used by later records in the same batch.                                                                                                | —        |
| `records[].name`               | `string`  | ja      | Human-readable display name; it is not used as internal identity.                                                                                                | —        |
| `records[].type`               | `string`  | ja      | Closed kind of the record where one is stated, such as a party's primary role or a location's type; the roles list, not this field, decides what a party may do. | —        |
| `records[].parent_ref`         | `string`  | nein    | Local ref of an earlier Location in the same batch. Use this for newly created hierarchies.                                                                      | —        |
| `records[].parent_location_id` | `string`  | nein    | Opaque ID of an existing Location. Never pass a name here.                                                                                                       | —        |
| `records[].allows_stock`       | `boolean` | nein    | Whether physical inventory may be held at this location.                                                                                                         | —        |
| `records[].source_system`      | `string`  | nein    | Tenant-scoped code naming the external origin of a record.                                                                                                       | —        |
| `records[].external_id`        | `string`  | nein    | Identifier assigned by the named external source system; never internal identity.                                                                                | —        |
| `records[].source_payload`     | `object`  | nein    | Lossless external JSON evidence from which typed operational fields were selected.                                                                               | —        |

**Siehe auch:** Geschäftsaktion [`update_location`](./commands#command-update_location)

### `update_party` — Update party {#command-update_party}

Changes operational party fields, roles and exact correspondence addresses; changed external
identity creates new source evidence and every effective change emits an exact before/after audit
diff.

**Aufruf**

```text
party_update_propose records
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `party`, `party_role`, `party_email_address`, `source_record` · Schreibt:
`source_record`, `party`, `party_role`, `party_email_address`, `business_event` · Erzeugt:
`party.updated`

**Siehe auch:** Agenten-Tool [`party_update_propose`](./commands#tool-party_update_propose), Event
[`party.updated`](./events#event-party-updated)

#### `party_update_propose` — Propose Party update {#tool-party_update_propose}

Prepare updates to existing Parties identified only by opaque ID. Exact changes are previewed and a
separate decision is required.

**Aufruf**

```text
party_update_propose records
```

**Zugriff:** `propose`

**Parameter**

| Name                          | Typ      | Pflicht | Beschreibung                                                                                                                                                                                       | Standard |
| ----------------------------- | -------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `records`                     | `array`  | ja      | Several master-data records stated together, each with the same fields the single-record command takes.                                                                                            | —        |
| `records[].id`                | `string` | ja      | Opaque Party ID.                                                                                                                                                                                   | —        |
| `records[].name`              | `string` | ja      | Human-readable display name; it is not used as internal identity.                                                                                                                                  | —        |
| `records[].roles`             | `array`  | ja      | Operational roles assigned to a party, for example customer or supplier. `company`, `customer`, `supplier`                                                                                         | —        |
| `records[].type`              | `string` | ja      | Closed kind of the record where one is stated, such as a party's primary role or a location's type; the roles list, not this field, decides what a party may do. `company`, `customer`, `supplier` | —        |
| `records[].accounting_code`   | `string` | nein    | Accounting reference used when postings or exports need a stable account mapping.                                                                                                                  | —        |
| `records[].payment_term_code` | `string` | nein    | Tenant-scoped code of the payment condition to apply.                                                                                                                                              | —        |
| `records[].default_currency`  | `string` | nein    | ISO 4217 currency used when an operation provides no explicit currency.                                                                                                                            | —        |
| `records[].credit_limit`      | `string` | nein    | Optional monetary exposure limit used by operational credit checks.                                                                                                                                | —        |
| `records[].tax_identifier`    | `string` | nein    | External tax or VAT identifier retained when operational matching requires it.                                                                                                                     | —        |
| `records[].emails`            | `array`  | nein    | Bounded labelled email addresses recorded for exact Party matching.                                                                                                                                | —        |
| `records[].emails[].email`    | `string` | ja      | Email address supplied for the named business purpose.                                                                                                                                             | —        |
| `records[].emails[].label`    | `string` | nein    | Optional human-readable description of a value's business purpose.                                                                                                                                 | —        |
| `records[].source_system`     | `string` | nein    | Tenant-scoped code naming the external origin of a record.                                                                                                                                         | —        |
| `records[].external_id`       | `string` | nein    | Identifier assigned by the named external source system; never internal identity.                                                                                                                  | —        |
| `records[].source_payload`    | `object` | nein    | Lossless external JSON evidence from which typed operational fields were selected.                                                                                                                 | —        |

**Siehe auch:** Geschäftsaktion [`update_party`](./commands#command-update_party)

## Finanzen

### `accept_adjustment` — Accept settlement reduction {#command-accept_adjustment}

Creates a separately evidenced noncash reduction only with explicit owner confirmation.

**Aufruf**

```text
finance_adjustment_propose expected_revision invoice_id amount reason_category reason [agreement] [source_record_id] [source_effect_id]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation`, `subledger_account`,
`finance_state` · Schreibt: `source_record`, `document`, `ledger_entry`, `settlement_allocation`,
`action`

**Siehe auch:** Agenten-Tool
[`finance_adjustment_propose`](./commands#tool-finance_adjustment_propose)

#### `finance_adjustment_propose` — Accept a stated settlement reduction {#tool-finance_adjustment_propose}

Prepare a noncash reduction with evidence and owner confirmation. Supplier agreement is mandatory.
Never calculate a discount or execute autonomously.

**Aufruf**

```text
finance_adjustment_propose expected_revision invoice_id amount reason_category reason [agreement] [source_record_id] [source_effect_id]
```

**Zugriff:** `propose`

Prepare an explicit noncash customer or supplier settlement reduction.

**Verwenden, wenn**

- Accept a stated agreed reduction of an open invoice.

**Nicht verwenden, wenn**

- Record actual cash or calculate a discount or tax.

**Voraussetzungen**

- Active compatible accounts, remaining claim and explicit owner confirmation.

**Abgelehnt, wenn**

- `invalid_reduction` — Missing agreement, stale preview, duplicate evidence, unsupported account or
  amount.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                                                                                                   | Standard |
| ------------------- | --------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.                                                                                    | —        |
| `invoice_id`        | `string`  | ja      | Opaque identity of the invoice evidence associated with a payment or allocation.                                                                               | —        |
| `amount`            | `string`  | ja      | Monetary amount of the payment or financial observation.                                                                                                       | —        |
| `reason_category`   | `string`  | ja      | Explicit accepted discount, agreed deduction or small remainder category. `early_payment_discount`, `agreed_deduction`, `accepted_small_remainder`, `bad_debt` | —        |
| `reason`            | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                        | —        |
| `agreement`         | `string`  | nein    | Stated supplier entitlement or agreement authorizing the reduction.                                                                                            | —        |
| `source_record_id`  | `string`  | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                                   | `None`   |
| `source_effect_id`  | `string`  | nein    | Stable effect reference within the original evidence, consumed at most once.                                                                                   | `None`   |

**Prüfen mit:** `finance.adjustment.context` — Remaining invoice claim.

**Siehe auch:** Geschäftsaktion [`accept_adjustment`](./commands#command-accept_adjustment)

### `assign_component` — Assign received financial component {#command-assign_component}

Separate received values from owner-confirmed internal classification and exact cost-center shares;
preserve postings.

**Aufruf**

```text
finance_component_assign_propose expected_revision document_id [document_line_id] basis expected_evidence_hash [case_reference_id] [group_reference_id] [parts] reason
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document`, `document_line`, `source_record`, `financial_component`,
`component_assignment_revision`, `component_assignment_part`, `finance_reference`, `finance_state` ·
Schreibt: `financial_component`, `component_assignment_revision`, `component_assignment_part`,
`finance_state`, `business_event` · Erzeugt: `finance.component_assigned`

**Siehe auch:** Agenten-Tool
[`finance_component_assign_propose`](./commands#tool-finance_component_assign_propose), Event
[`finance.component_assigned`](./events#event-finance-component_assigned)

#### `finance_component_assign_propose` — Assign financial component {#tool-finance_component_assign_propose}

Review explicit cost-center shares and case/group references against a received basis. Requires
owner confirmation; no posting effect.

**Aufruf**

```text
finance_component_assign_propose expected_revision document_id [document_line_id] basis expected_evidence_hash [case_reference_id] [group_reference_id] [parts] reason
```

**Zugriff:** `propose`

Prepare explicit classification and cost-center shares for a received component.

**Verwenden, wenn**

- Assign or replace internal attribution on an invoice/credit component.

**Nicht verwenden, wenn**

- Record money or determine tax treatment.

**Voraussetzungen**

- Owner confirmation, unchanged evidence and active same-kind references.

**Abgelehnt, wenn**

- `invalid_assignment` — Unknown basis, excess shares, foreign/wrong-kind/blocked references or
  stale evidence/revision.

**Parameter**

| Name                               | Typ       | Pflicht | Beschreibung                                                                              | Standard |
| ---------------------------------- | --------- | ------- | ----------------------------------------------------------------------------------------- | -------- |
| `expected_revision`                | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.               | —        |
| `document_id`                      | `string`  | ja      | Opaque identity of the evidence document to inspect or correct.                           | —        |
| `document_line_id`                 | `string`  | nein    | Opaque same-tenant received document line identity; must belong to the selected document. | `None`   |
| `basis`                            | `string`  | ja      | `net`, `gross`, `base`                                                                    | —        |
| `expected_evidence_hash`           | `string`  | ja      | —                                                                                         | —        |
| `case_reference_id`                | `string`  | nein    | —                                                                                         | `None`   |
| `group_reference_id`               | `string`  | nein    | —                                                                                         | `None`   |
| `parts`                            | `array`   | nein    | —                                                                                         | —        |
| `parts[].cost_center_reference_id` | `string`  | ja      | —                                                                                         | —        |
| `parts[].amount`                   | `string`  | ja      | Monetary amount of the payment or financial observation.                                  | —        |
| `reason`                           | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                   | —        |

**Prüfen mit:** `finance.component.history` — Immutable received-component assignment revision and
exact shares.

**Siehe auch:** Geschäftsaktion [`assign_component`](./commands#command-assign_component)

### `create_account` — Create operational account {#command-create_account}

Uses shared tenant-scoped operational account configuration with explicit owner confirmation for
changes.

**Aufruf**

```text
finance_create_account_propose expected_revision code name role
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `subledger_account`, `finance_role_destination`, `finance_state` ·
Schreibt: `subledger_account`, `finance_role_destination`, `finance_state`, `business_event`

**Siehe auch:** Agenten-Tool
[`finance_create_account_propose`](./commands#tool-finance_create_account_propose)

#### `finance_create_account_propose` — Configure operational accounts {#tool-finance_create_account_propose}

Prepare an owner-confirmed operational account change; never execute it autonomously.

**Aufruf**

```text
finance_create_account_propose expected_revision code name role
```

**Zugriff:** `propose`

Prepare an owner-confirmed operational account configuration change.

**Verwenden, wenn**

- Configure an allowed account or default.

**Nicht verwenden, wenn**

- Record money or determine tax treatment.

**Voraussetzungen**

- Owner confirmation, valid same-tenant role and account.

**Abgelehnt, wenn**

- `invalid_account_configuration` — Stale revision, duplicate code, wrong role or foreign account.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                                                                                                                                                                                                                     | Standard |
| ------------------- | --------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.                                                                                                                                                                                                      | —        |
| `code`              | `string`  | ja      | Short tenant-scoped business code used to find the record operationally.                                                                                                                                                                                                         | —        |
| `name`              | `string`  | ja      | Human-readable display name; it is not used as internal identity.                                                                                                                                                                                                                | —        |
| `role`              | `string`  | ja      | Repeatable operational role assigned to a party, for example customer or supplier. `accounts_receivable`, `accounts_payable`, `cash`, `sales_revenue`, `inventory`, `customer_reduction`, `supplier_reduction`, `bad_debt_expense`, `dunning_fee_revenue`, `opening_counterpart` | —        |

**Prüfen mit:** `timeline` — The account change event and identity.

**Siehe auch:** Geschäftsaktion [`create_account`](./commands#command-create_account), Projection
[`timeline`](./views#projection-timeline)

### `execute_payment_run` — Execute payment run {#command-execute_payment_run}

Pays the supplier invoices and amounts somebody confirmed, in one transaction, and records that they
were one decision.

**Aufruf**

```text
payment_run_propose payments currency expected_total reason
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation`, `party`, `payment_term` ·
Schreibt: `source_record`, `document`, `ledger_entry`, `settlement_allocation`, `business_event` ·
Erzeugt: `payments.run`

**Siehe auch:** Agenten-Tool [`payment_run_propose`](./commands#tool-payment_run_propose), Event
[`payments.run`](./events#event-payments-run), Geschäftsaktion
[`post_supplier_payment`](./commands#command-post_supplier_payment)

#### `payment_run_propose` — Execute payment run {#tool-payment_run_propose}

Prepare this business mutation without changing state. Execute payment run. Human confirmation is
required.

**Aufruf**

```text
payment_run_propose payments currency expected_total reason
```

**Zugriff:** `propose`

**Parameter**

| Name                        | Typ      | Pflicht | Beschreibung                                                                                                                      | Standard |
| --------------------------- | -------- | ------- | --------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `payments`                  | `array`  | ja      | The invoices a payment run pays and the amount stated against each; every amount is received, never derived from a discount rate. | —        |
| `payments[].invoice_id`     | `string` | ja      | Opaque identity of the invoice evidence associated with a payment or allocation.                                                  | —        |
| `payments[].amount`         | `string` | ja      | Monetary amount of the payment or financial observation.                                                                          | —        |
| `payments[].payment_number` | `string` | nein    | Human-facing payment reference used for matching and investigation.                                                               | —        |
| `currency`                  | `string` | ja      | ISO 4217 currency code for monetary values.                                                                                       | —        |
| `expected_total`            | `string` | ja      | The sum of money the caller confirmed; a run is refused unless the stated amounts still add up to it.                             | —        |
| `reason`                    | `string` | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                                                           | —        |

**Siehe auch:** Geschäftsaktion [`execute_payment_run`](./commands#command-execute_payment_run)

### `import_opening` — Import opening positions {#command-import_opening}

Records stated residual customer/supplier positions against a neutral counterpart after owner
confirmation, without cash or turnover.

**Aufruf**

```text
finance_opening_propose expected_revision source_namespace snapshot_key cutover_date coverage_kind reason items
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `party`, `subledger_account`, `finance_state`, `opening_scope`,
`opening_item_detail`, `document`, `ledger_entry` · Schreibt: `source_record`, `document`,
`opening_scope`, `opening_item_detail`, `ledger_entry`, `action`

**Siehe auch:** Agenten-Tool [`finance_opening_propose`](./commands#tool-finance_opening_propose)

#### `finance_opening_propose` — Import opening positions {#tool-finance_opening_propose}

Review stated customer/supplier residual debt or credit from a cutover snapshot. No cash or turnover
effect. Requires owner confirmation.

**Aufruf**

```text
finance_opening_propose expected_revision source_namespace snapshot_key cutover_date coverage_kind reason items
```

**Zugriff:** `propose`

Prepare explicit customer/supplier opening residuals with stable source coverage.

**Verwenden, wenn**

- Migrate outstanding debt or credit from an external system.

**Nicht verwenden, wenn**

- Record an actual payment or create new turnover.

**Voraussetzungen**

- Active compatible accounts and parties, no overlapping coverage, explicit owner confirmation.

**Abgelehnt, wenn**

- `invalid_opening` — Duplicate or overlapping scope, stale revision, foreign reference,
  incompatible party or account, invalid amount/date.

**Parameter**

| Name                             | Typ       | Pflicht | Beschreibung                                                                                                                                     | Standard |
| -------------------------------- | --------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| `expected_revision`              | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.                                                                      | —        |
| `source_namespace`               | `string`  | ja      | —                                                                                                                                                | —        |
| `snapshot_key`                   | `string`  | ja      | —                                                                                                                                                | —        |
| `cutover_date`                   | `string`  | ja      | —                                                                                                                                                | —        |
| `coverage_kind`                  | `string`  | ja      | `individual`, `summary`                                                                                                                          | —        |
| `reason`                         | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                                                                          | —        |
| `items`                          | `array`   | ja      | —                                                                                                                                                | —        |
| `items[].party_id`               | `string`  | ja      | Opaque identity of the customer, supplier, or other operational party.                                                                           | —        |
| `items[].direction`              | `string`  | ja      | Business flow direction, such as sales or purchase, incoming or outgoing. `customer_debt`, `customer_credit`, `supplier_debt`, `supplier_credit` | —        |
| `items[].currency`               | `string`  | ja      | ISO 4217 currency code for monetary values.                                                                                                      | —        |
| `items[].amount`                 | `string`  | ja      | Monetary amount of the payment or financial observation.                                                                                         | —        |
| `items[].external_item_key`      | `string`  | ja      | —                                                                                                                                                | —        |
| `items[].reference`              | `string`  | nein    | The number the returning parcel will carry, as the customer or the company stated it; never generated.                                           | —        |
| `items[].original_document_date` | `string`  | nein    | —                                                                                                                                                | `None`   |
| `items[].due_date`               | `string`  | nein    | —                                                                                                                                                | `None`   |
| `items[].original_total`         | `string`  | nein    | —                                                                                                                                                | `None`   |
| `items[].source_record_id`       | `string`  | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                     | `None`   |

**Prüfen mit:** `finance.opening.context` — Current finance revision and account setup; inspect
receipt document and ledger identities for balances.

**Siehe auch:** Geschäftsaktion [`import_opening`](./commands#command-import_opening)

### `initialize_accounts` — Initialize operational accounts {#command-initialize_accounts}

Uses shared tenant-scoped operational account configuration with explicit owner confirmation for
changes.

**Aufruf**

```text
finance_initialize_accounts_propose expected_revision
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `subledger_account`, `finance_role_destination`, `finance_state` ·
Schreibt: `subledger_account`, `finance_role_destination`, `finance_state`, `business_event`

**Siehe auch:** Agenten-Tool
[`finance_initialize_accounts_propose`](./commands#tool-finance_initialize_accounts_propose)

#### `finance_initialize_accounts_propose` — Configure operational accounts {#tool-finance_initialize_accounts_propose}

Prepare an owner-confirmed operational account change; never execute it autonomously.

**Aufruf**

```text
finance_initialize_accounts_propose expected_revision
```

**Zugriff:** `propose`

Prepare an owner-confirmed operational account configuration change.

**Verwenden, wenn**

- Configure an allowed account or default.

**Nicht verwenden, wenn**

- Record money or determine tax treatment.

**Voraussetzungen**

- Owner confirmation, valid same-tenant role and account.

**Abgelehnt, wenn**

- `invalid_account_configuration` — Stale revision, duplicate code, wrong role or foreign account.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |

**Prüfen mit:** `timeline` — The account change event and identity.

**Siehe auch:** Geschäftsaktion [`initialize_accounts`](./commands#command-initialize_accounts),
Projection [`timeline`](./views#projection-timeline)

### `list_mappings` — List Mappings {#command-list_mappings}

Maintain and explain explicit external destinations without changing financial evidence.

**Aufruf**

```text
finance_target_mappings target_id [query] [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `accounting_target`, `accounting_target_reference`,
`finance_target_mapping_revision`, `finance_reference`, `finance_state`, `document`,
`document_line`, `ledger_entry` · Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_target_mappings`](./commands#tool-finance_target_mappings)

#### `finance_target_mappings` — Finance Target Mappings {#tool-finance_target_mappings}

Inspect Finance target references and explicit mapping resolution.

**Aufruf**

```text
finance_target_mappings target_id [query] [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage              | Art                        | Standard |
| ----------------------------- | -------------------------- | -------- |
| `MCP finance_target_mappings` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read Finance-only target configuration and explicit mapping resolution.

**Verwenden, wenn**

- Configure or inspect an explicitly selected external accounting destination.

**Nicht verwenden, wenn**

- Determine tax treatment, change local financial amounts, or claim a remote posting.

**Voraussetzungen**

- Same-tenant target/references; owner confirmation for configuration changes.

**Parameter**

| Name        | Typ       | Pflicht | Beschreibung                                                              | Standard |
| ----------- | --------- | ------- | ------------------------------------------------------------------------- | -------- |
| `target_id` | `string`  | ja      | Opaque same-tenant external accounting destination identity.              | —        |
| `query`     | `string`  | nein    | Optional invoice-number search within matching same-party credit targets. | —        |
| `limit`     | `integer` | nein    | Maximum number of records or jobs processed by this invocation.           | —        |
| `offset`    | `integer` | nein    | Number of matching rows to skip for bounded pagination.                   | —        |

**Siehe auch:** Geschäftsaktion [`list_mappings`](./commands#command-list_mappings)

### `list_target_references` — List Target References {#command-list_target_references}

Maintain and explain explicit external destinations without changing financial evidence.

**Aufruf**

```text
finance_target_references target_id [kind] [query] [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `accounting_target`, `accounting_target_reference`,
`finance_target_mapping_revision`, `finance_reference`, `finance_state`, `document`,
`document_line`, `ledger_entry` · Schreibt: —

**Siehe auch:** Agenten-Tool
[`finance_target_references`](./commands#tool-finance_target_references)

#### `finance_target_references` — Finance Target References {#tool-finance_target_references}

Inspect Finance target references and explicit mapping resolution.

**Aufruf**

```text
finance_target_references target_id [kind] [query] [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                | Art                        | Standard |
| ------------------------------- | -------------------------- | -------- |
| `MCP finance_target_references` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read Finance-only target configuration and explicit mapping resolution.

**Verwenden, wenn**

- Configure or inspect an explicitly selected external accounting destination.

**Nicht verwenden, wenn**

- Determine tax treatment, change local financial amounts, or claim a remote posting.

**Voraussetzungen**

- Same-tenant target/references; owner confirmation for configuration changes.

**Parameter**

| Name        | Typ       | Pflicht | Beschreibung                                                                    | Standard |
| ----------- | --------- | ------- | ------------------------------------------------------------------------------- | -------- |
| `target_id` | `string`  | ja      | Opaque same-tenant external accounting destination identity.                    | —        |
| `kind`      | `string`  | nein    | Explicit internal or target reference kind; no inferred tax or country meaning. | —        |
| `query`     | `string`  | nein    | Optional invoice-number search within matching same-party credit targets.       | —        |
| `limit`     | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                 | —        |
| `offset`    | `integer` | nein    | Number of matching rows to skip for bounded pagination.                         | —        |

**Siehe auch:** Geschäftsaktion
[`list_target_references`](./commands#command-list_target_references)

### `list_targets` — List Targets {#command-list_targets}

Maintain and explain explicit external destinations without changing financial evidence.

**Aufruf**

```text
finance_targets [query] [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `accounting_target`, `accounting_target_reference`,
`finance_target_mapping_revision`, `finance_reference`, `finance_state`, `document`,
`document_line`, `ledger_entry` · Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_targets`](./commands#tool-finance_targets)

#### `finance_targets` — Finance Targets {#tool-finance_targets}

Inspect Finance target references and explicit mapping resolution.

**Aufruf**

```text
finance_targets [query] [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage      | Art                        | Standard |
| --------------------- | -------------------------- | -------- |
| `MCP finance_targets` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read Finance-only target configuration and explicit mapping resolution.

**Verwenden, wenn**

- Configure or inspect an explicitly selected external accounting destination.

**Nicht verwenden, wenn**

- Determine tax treatment, change local financial amounts, or claim a remote posting.

**Voraussetzungen**

- Same-tenant target/references; owner confirmation for configuration changes.

**Parameter**

| Name     | Typ       | Pflicht | Beschreibung                                                              | Standard |
| -------- | --------- | ------- | ------------------------------------------------------------------------- | -------- |
| `query`  | `string`  | nein    | Optional invoice-number search within matching same-party credit targets. | —        |
| `limit`  | `integer` | nein    | Maximum number of records or jobs processed by this invocation.           | —        |
| `offset` | `integer` | nein    | Number of matching rows to skip for bounded pagination.                   | —        |

**Siehe auch:** Geschäftsaktion [`list_targets`](./commands#command-list_targets)

### `maintain_target_configuration` — Maintain Target Configuration {#command-maintain_target_configuration}

Maintain and explain explicit external destinations without changing financial evidence.

**Aufruf**

```text
finance_target_create_propose expected_revision reason namespace name
finance_target_update_propose expected_revision reason target_id name state
finance_target_reference_create_propose expected_revision reason target_id kind code name
finance_target_reference_update_propose expected_revision reason reference_id name state
finance_target_mapping_set_propose expected_revision reason target_id mapping_kind [local_account_id] [transaction_kind] [case_reference_id] [group_mode] [group_reference_id] external_account_id [external_tax_code_id] [state]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `accounting_target`, `accounting_target_reference`,
`finance_target_mapping_revision`, `finance_reference`, `finance_state`, `document`,
`document_line`, `ledger_entry` · Schreibt: `accounting_target`, `accounting_target_reference`,
`finance_target_mapping_revision`, `finance_state`, `business_event` · Erzeugt:
`finance.target_configuration_changed`

**Siehe auch:** Agenten-Tool
[`finance_target_create_propose`](./commands#tool-finance_target_create_propose), Agenten-Tool
[`finance_target_update_propose`](./commands#tool-finance_target_update_propose), Agenten-Tool
[`finance_target_reference_create_propose`](./commands#tool-finance_target_reference_create_propose),
Agenten-Tool
[`finance_target_reference_update_propose`](./commands#tool-finance_target_reference_update_propose),
Agenten-Tool
[`finance_target_mapping_set_propose`](./commands#tool-finance_target_mapping_set_propose), Event
[`finance.target_configuration_changed`](./events#event-finance-target_configuration_changed)

#### `finance_target_create_propose` — Review Finance target configuration {#tool-finance_target_create_propose}

Review a Finance-only target configuration change; owner confirmation required.

**Aufruf**

```text
finance_target_create_propose expected_revision reason namespace name
```

**Zugriff:** `propose`

Review Finance-only target configuration.

**Verwenden, wenn**

- Configure or inspect an explicitly selected external accounting destination.

**Nicht verwenden, wenn**

- Determine tax treatment, change local financial amounts, or claim a remote posting.

**Voraussetzungen**

- Same-tenant target/references; owner confirmation for configuration changes.

**Abgelehnt, wenn**

- `invalid_target_configuration` — Stale review, overlapping scope, blocked or foreign reference,
  invalid kind or missing reason.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |
| `reason`            | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.     | —        |
| `namespace`         | `string`  | ja      | —                                                                           | —        |
| `name`              | `string`  | ja      | Human-readable display name; it is not used as internal identity.           | —        |

**Prüfen mit:** `finance.target_mappings.list` — Current rules; mapping history preserves reviewed
revisions.

**Siehe auch:** Geschäftsaktion
[`maintain_target_configuration`](./commands#command-maintain_target_configuration)

#### `finance_target_update_propose` — Review Finance target configuration {#tool-finance_target_update_propose}

Review a Finance-only target configuration change; owner confirmation required.

**Aufruf**

```text
finance_target_update_propose expected_revision reason target_id name state
```

**Zugriff:** `propose`

Review Finance-only target configuration.

**Verwenden, wenn**

- Configure or inspect an explicitly selected external accounting destination.

**Nicht verwenden, wenn**

- Determine tax treatment, change local financial amounts, or claim a remote posting.

**Voraussetzungen**

- Same-tenant target/references; owner confirmation for configuration changes.

**Abgelehnt, wenn**

- `invalid_target_configuration` — Stale review, overlapping scope, blocked or foreign reference,
  invalid kind or missing reason.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |
| `reason`            | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.     | —        |
| `target_id`         | `string`  | ja      | Opaque same-tenant external accounting destination identity.                | —        |
| `name`              | `string`  | ja      | Human-readable display name; it is not used as internal identity.           | —        |
| `state`             | `string`  | ja      | Active or blocked eligibility for new account postings. `active`, `blocked` | —        |

**Prüfen mit:** `finance.target_mappings.list` — Current rules; mapping history preserves reviewed
revisions.

**Siehe auch:** Geschäftsaktion
[`maintain_target_configuration`](./commands#command-maintain_target_configuration)

#### `finance_target_reference_create_propose` — Review Finance target configuration {#tool-finance_target_reference_create_propose}

Review a Finance-only target configuration change; owner confirmation required.

**Aufruf**

```text
finance_target_reference_create_propose expected_revision reason target_id kind code name
```

**Zugriff:** `propose`

Review Finance-only target configuration.

**Verwenden, wenn**

- Configure or inspect an explicitly selected external accounting destination.

**Nicht verwenden, wenn**

- Determine tax treatment, change local financial amounts, or claim a remote posting.

**Voraussetzungen**

- Same-tenant target/references; owner confirmation for configuration changes.

**Abgelehnt, wenn**

- `invalid_target_configuration` — Stale review, overlapping scope, blocked or foreign reference,
  invalid kind or missing reason.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                                          | Standard |
| ------------------- | --------- | ------- | ----------------------------------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.                           | —        |
| `reason`            | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                               | —        |
| `target_id`         | `string`  | ja      | Opaque same-tenant external accounting destination identity.                                          | —        |
| `kind`              | `string`  | ja      | Explicit internal or target reference kind; no inferred tax or country meaning. `account`, `tax_code` | —        |
| `code`              | `string`  | ja      | Short tenant-scoped business code used to find the record operationally.                              | —        |
| `name`              | `string`  | ja      | Human-readable display name; it is not used as internal identity.                                     | —        |

**Prüfen mit:** `finance.target_mappings.list` — Current rules; mapping history preserves reviewed
revisions.

**Siehe auch:** Geschäftsaktion
[`maintain_target_configuration`](./commands#command-maintain_target_configuration)

#### `finance_target_reference_update_propose` — Review Finance target configuration {#tool-finance_target_reference_update_propose}

Review a Finance-only target configuration change; owner confirmation required.

**Aufruf**

```text
finance_target_reference_update_propose expected_revision reason reference_id name state
```

**Zugriff:** `propose`

Review Finance-only target configuration.

**Verwenden, wenn**

- Configure or inspect an explicitly selected external accounting destination.

**Nicht verwenden, wenn**

- Determine tax treatment, change local financial amounts, or claim a remote posting.

**Voraussetzungen**

- Same-tenant target/references; owner confirmation for configuration changes.

**Abgelehnt, wenn**

- `invalid_target_configuration` — Stale review, overlapping scope, blocked or foreign reference,
  invalid kind or missing reason.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |
| `reason`            | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.     | —        |
| `reference_id`      | `string`  | ja      | Opaque same-tenant managed reference identity.                              | —        |
| `name`              | `string`  | ja      | Human-readable display name; it is not used as internal identity.           | —        |
| `state`             | `string`  | ja      | Active or blocked eligibility for new account postings. `active`, `blocked` | —        |

**Prüfen mit:** `finance.target_mappings.list` — Current rules; mapping history preserves reviewed
revisions.

**Siehe auch:** Geschäftsaktion
[`maintain_target_configuration`](./commands#command-maintain_target_configuration)

#### `finance_target_mapping_set_propose` — Review Finance target configuration {#tool-finance_target_mapping_set_propose}

Review a Finance-only target configuration change; owner confirmation required.

**Aufruf**

```text
finance_target_mapping_set_propose expected_revision reason target_id mapping_kind [local_account_id] [transaction_kind] [case_reference_id] [group_mode] [group_reference_id] external_account_id [external_tax_code_id] [state]
```

**Zugriff:** `propose`

Review Finance-only target configuration.

**Verwenden, wenn**

- Configure or inspect an explicitly selected external accounting destination.

**Nicht verwenden, wenn**

- Determine tax treatment, change local financial amounts, or claim a remote posting.

**Voraussetzungen**

- Same-tenant target/references; owner confirmation for configuration changes.

**Abgelehnt, wenn**

- `invalid_target_configuration` — Stale review, overlapping scope, blocked or foreign reference,
  invalid kind or missing reason.

**Parameter**

| Name                   | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ---------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `expected_revision`    | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |
| `reason`               | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.     | —        |
| `target_id`            | `string`  | ja      | Opaque same-tenant external accounting destination identity.                | —        |
| `mapping_kind`         | `string`  | ja      | `local_account`, `case_routing`                                             | —        |
| `local_account_id`     | `string`  | nein    | —                                                                           | `None`   |
| `transaction_kind`     | `string`  | nein    | `sales_invoice`, `supplier_invoice`, `credit_note`, `supplier_credit_note`  | `None`   |
| `case_reference_id`    | `string`  | nein    | —                                                                           | `None`   |
| `group_mode`           | `string`  | nein    | `none`, `exact`                                                             | `None`   |
| `group_reference_id`   | `string`  | nein    | —                                                                           | `None`   |
| `external_account_id`  | `string`  | ja      | —                                                                           | —        |
| `external_tax_code_id` | `string`  | nein    | —                                                                           | `None`   |
| `state`                | `string`  | nein    | Active or blocked eligibility for new account postings. `active`, `blocked` | `active` |

**Prüfen mit:** `finance.target_mappings.list` — Current rules; mapping history preserves reviewed
revisions.

**Siehe auch:** Geschäftsaktion
[`maintain_target_configuration`](./commands#command-maintain_target_configuration)

### `maintain_reference` — Maintain finance reference {#command-maintain_reference}

Read or maintain defined internal references with immutable reasoned decisions and owner
confirmation for changes.

**Aufruf**

```text
finance_reference_create_propose expected_revision kind code name reason
finance_reference_update_propose expected_revision reference_id name state reason
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `finance_reference`, `finance_state`, `business_event` · Schreibt:
`finance_reference`, `finance_state`, `business_event` · Erzeugt: `finance.reference_changed`

**Siehe auch:** Agenten-Tool
[`finance_reference_create_propose`](./commands#tool-finance_reference_create_propose), Agenten-Tool
[`finance_reference_update_propose`](./commands#tool-finance_reference_update_propose), Event
[`finance.reference_changed`](./events#event-finance-reference_changed)

#### `finance_reference_create_propose` — Create finance reference {#tool-finance_reference_create_propose}

Review a defined cost center, case code or coding group. Requires owner confirmation.

**Aufruf**

```text
finance_reference_create_propose expected_revision kind code name reason
```

**Zugriff:** `propose`

Prepare a reasoned reference catalog change for owner confirmation.

**Verwenden, wenn**

- Create a defined cost center, case code or coding group.

**Nicht verwenden, wenn**

- Record money or determine tax treatment.

**Voraussetzungen**

- Owner confirmation and valid same-tenant reference kind.

**Abgelehnt, wenn**

- `invalid_reference` — Stale revision, duplicate code, invalid kind/state, foreign identity or
  missing reason.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                                                               | Standard |
| ------------------- | --------- | ------- | -------------------------------------------------------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.                                                | —        |
| `kind`              | `string`  | ja      | Explicit internal or target reference kind; no inferred tax or country meaning. `cost_center`, `case_code`, `coding_group` | —        |
| `code`              | `string`  | ja      | Short tenant-scoped business code used to find the record operationally.                                                   | —        |
| `name`              | `string`  | ja      | Human-readable display name; it is not used as internal identity.                                                          | —        |
| `reason`            | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                                                    | —        |

**Prüfen mit:** `finance.references.history` — Immutable before/after decision and confirming
action.

**Siehe auch:** Geschäftsaktion [`maintain_reference`](./commands#command-maintain_reference)

#### `finance_reference_update_propose` — Update finance reference {#tool-finance_reference_update_propose}

Review reference rename, blocking or reactivation with a reason. Requires owner confirmation.

**Aufruf**

```text
finance_reference_update_propose expected_revision reference_id name state reason
```

**Zugriff:** `propose`

Prepare a reasoned reference catalog change for owner confirmation.

**Verwenden, wenn**

- Rename, block or reactivate an existing internal reference.

**Nicht verwenden, wenn**

- Record money or determine tax treatment.

**Voraussetzungen**

- Owner confirmation and valid same-tenant reference kind.

**Abgelehnt, wenn**

- `invalid_reference` — Stale revision, duplicate code, invalid kind/state, foreign identity or
  missing reason.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |
| `reference_id`      | `string`  | ja      | Opaque same-tenant managed reference identity.                              | —        |
| `name`              | `string`  | ja      | Human-readable display name; it is not used as internal identity.           | —        |
| `state`             | `string`  | ja      | Active or blocked eligibility for new account postings. `active`, `blocked` | —        |
| `reason`            | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.     | —        |

**Prüfen mit:** `finance.references.history` — Immutable before/after decision and confirming
action.

**Siehe auch:** Geschäftsaktion [`maintain_reference`](./commands#command-maintain_reference)

### `mapping_history` — Mapping History {#command-mapping_history}

Maintain and explain explicit external destinations without changing financial evidence.

**Aufruf**

```text
finance_target_mapping_history mapping_id [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `accounting_target`, `accounting_target_reference`,
`finance_target_mapping_revision`, `finance_reference`, `finance_state`, `document`,
`document_line`, `ledger_entry` · Schreibt: —

**Siehe auch:** Agenten-Tool
[`finance_target_mapping_history`](./commands#tool-finance_target_mapping_history)

#### `finance_target_mapping_history` — Finance Target Mapping History {#tool-finance_target_mapping_history}

Inspect Finance target references and explicit mapping resolution.

**Aufruf**

```text
finance_target_mapping_history mapping_id [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                     | Art                        | Standard |
| ------------------------------------ | -------------------------- | -------- |
| `MCP finance_target_mapping_history` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read Finance-only target configuration and explicit mapping resolution.

**Verwenden, wenn**

- Configure or inspect an explicitly selected external accounting destination.

**Nicht verwenden, wenn**

- Determine tax treatment, change local financial amounts, or claim a remote posting.

**Voraussetzungen**

- Same-tenant target/references; owner confirmation for configuration changes.

**Parameter**

| Name         | Typ       | Pflicht | Beschreibung                                                                      | Standard |
| ------------ | --------- | ------- | --------------------------------------------------------------------------------- | -------- |
| `mapping_id` | `string`  | ja      | Opaque Finance mapping revision identity; history follows its exact owning scope. | —        |
| `limit`      | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                   | —        |
| `offset`     | `integer` | nein    | Number of matching rows to skip for bounded pagination.                           | —        |

**Siehe auch:** Geschäftsaktion [`mapping_history`](./commands#command-mapping_history)

### `allocate_credit_note` — Net credit note against invoice {#command-allocate_credit_note}

Settles a posted credit note against an invoice the same customer still owes.

**Aufruf**

```text
credit_note_allocate_propose credit_note_id invoice_id amount
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation` · Schreibt:
`settlement_allocation`

**Siehe auch:** Agenten-Tool
[`credit_note_allocate_propose`](./commands#tool-credit_note_allocate_propose)

#### `credit_note_allocate_propose` — Net credit note against invoice {#tool-credit_note_allocate_propose}

Prepare this business mutation without changing state. Net credit note against invoice. Human
confirmation is required.

**Aufruf**

```text
credit_note_allocate_propose credit_note_id invoice_id amount
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ      | Pflicht | Beschreibung                                                                     | Standard |
| ---------------- | -------- | ------- | -------------------------------------------------------------------------------- | -------- |
| `credit_note_id` | `string` | ja      | Opaque identity of the credit note being posted, netted or refunded.             | —        |
| `invoice_id`     | `string` | ja      | Opaque identity of the invoice evidence associated with a payment or allocation. | —        |
| `amount`         | `string` | ja      | Monetary amount of the payment or financial observation.                         | —        |

**Siehe auch:** Geschäftsaktion [`allocate_credit_note`](./commands#command-allocate_credit_note)

### `allocate_supplier_credit_note` — Net supplier credit against invoice {#command-allocate_supplier_credit_note}

Settles a booked supplier credit against an invoice the company still owes that supplier.

**Aufruf**

```text
supplier_credit_note_allocate_propose credit_note_id invoice_id amount
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation` · Schreibt:
`settlement_allocation`

**Siehe auch:** Agenten-Tool
[`supplier_credit_note_allocate_propose`](./commands#tool-supplier_credit_note_allocate_propose)

#### `supplier_credit_note_allocate_propose` — Net supplier credit against invoice {#tool-supplier_credit_note_allocate_propose}

Prepare this business mutation without changing state. Net supplier credit against invoice. Human
confirmation is required.

**Aufruf**

```text
supplier_credit_note_allocate_propose credit_note_id invoice_id amount
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ      | Pflicht | Beschreibung                                                                     | Standard |
| ---------------- | -------- | ------- | -------------------------------------------------------------------------------- | -------- |
| `credit_note_id` | `string` | ja      | Opaque identity of the credit note being posted, netted or refunded.             | —        |
| `invoice_id`     | `string` | ja      | Opaque identity of the invoice evidence associated with a payment or allocation. | —        |
| `amount`         | `string` | ja      | Monetary amount of the payment or financial observation.                         | —        |

**Siehe auch:** Geschäftsaktion
[`allocate_supplier_credit_note`](./commands#command-allocate_supplier_credit_note)

### `post_sales_credit_note` — Post credit note {#command-post_sales_credit_note}

Posts a credit note as the exact reverse of a sales invoice, leaving the customer owed what it
states.

**Aufruf**

```text
credit_note_post_propose credit_note_id [effective_at]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry` · Schreibt: `ledger_entry`

**Siehe auch:** Agenten-Tool [`credit_note_post_propose`](./commands#tool-credit_note_post_propose)

#### `credit_note_post_propose` — Post credit note {#tool-credit_note_post_propose}

Prepare this business mutation without changing state. Post credit note. Human confirmation is
required.

**Aufruf**

```text
credit_note_post_propose credit_note_id [effective_at]
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ      | Pflicht | Beschreibung                                                         | Standard |
| ---------------- | -------- | ------- | -------------------------------------------------------------------- | -------- |
| `credit_note_id` | `string` | ja      | Opaque identity of the credit note being posted, netted or refunded. | —        |
| `effective_at`   | `string` | nein    | UTC instant from which the observation or rule takes effect.         | —        |

**Siehe auch:** Geschäftsaktion
[`post_sales_credit_note`](./commands#command-post_sales_credit_note)

### `post_customer_payment` — Post customer payment {#command-post_customer_payment}

Records payment evidence, posts balanced ledger entries, and allocates the payment to an invoice.

**Aufruf**

```text
customer_payment_post_propose invoice_id amount [payment_number] [source_record_id] [effective_at]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation` · Schreibt: `source_record`,
`document`, `ledger_entry`, `settlement_allocation`

**Siehe auch:** Agenten-Tool
[`customer_payment_post_propose`](./commands#tool-customer_payment_post_propose), Aktion
[`post_customer_payment`](./views#action-post_customer_payment)

#### `customer_payment_post_propose` — Post customer payment {#tool-customer_payment_post_propose}

Prepare this business mutation without changing state. Post customer payment. Human confirmation is
required.

**Aufruf**

```text
customer_payment_post_propose invoice_id amount [payment_number] [source_record_id] [effective_at]
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                     | Standard |
| ------------------ | -------- | ------- | -------------------------------------------------------------------------------- | -------- |
| `invoice_id`       | `string` | ja      | Opaque identity of the invoice evidence associated with a payment or allocation. | —        |
| `amount`           | `string` | ja      | Monetary amount of the payment or financial observation.                         | —        |
| `payment_number`   | `string` | nein    | Human-facing payment reference used for matching and investigation.              | —        |
| `source_record_id` | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.     | —        |
| `effective_at`     | `string` | nein    | UTC instant from which the observation or rule takes effect.                     | —        |

**Siehe auch:** Geschäftsaktion [`post_customer_payment`](./commands#command-post_customer_payment)

### `post_customer_refund` — Post customer refund {#command-post_customer_refund}

Returns money to a credited customer and settles the credit note it repays.

**Aufruf**

```text
customer_refund_post_propose credit_note_id amount [refund_number] [source_record_id] [effective_at]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation` · Schreibt: `source_record`,
`document`, `ledger_entry`, `settlement_allocation`

**Siehe auch:** Agenten-Tool
[`customer_refund_post_propose`](./commands#tool-customer_refund_post_propose)

#### `customer_refund_post_propose` — Post customer refund {#tool-customer_refund_post_propose}

Prepare this business mutation without changing state. Post customer refund. Human confirmation is
required.

**Aufruf**

```text
customer_refund_post_propose credit_note_id amount [refund_number] [source_record_id] [effective_at]
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                  | Standard |
| ------------------ | -------- | ------- | ----------------------------------------------------------------------------- | -------- |
| `credit_note_id`   | `string` | ja      | Opaque identity of the credit note being posted, netted or refunded.          | —        |
| `amount`           | `string` | ja      | Monetary amount of the payment or financial observation.                      | —        |
| `refund_number`    | `string` | nein    | Caller-supplied number for the refund document; one is generated when absent. | —        |
| `source_record_id` | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.  | —        |
| `effective_at`     | `string` | nein    | UTC instant from which the observation or rule takes effect.                  | —        |

**Siehe auch:** Geschäftsaktion [`post_customer_refund`](./commands#command-post_customer_refund)

### `post_sales_invoice` — Post sales invoice {#command-post_sales_invoice}

Books a recorded sales invoice, so what the customer owes becomes visible to settlement and the
queue.

**Aufruf**

```text
sales_invoice_post_propose document_id [effective_at]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry` · Schreibt: `ledger_entry`

**Siehe auch:** Agenten-Tool
[`sales_invoice_post_propose`](./commands#tool-sales_invoice_post_propose)

#### `sales_invoice_post_propose` — Post sales invoice {#tool-sales_invoice_post_propose}

Prepare this business mutation without changing state. Post sales invoice. Human confirmation is
required.

**Aufruf**

```text
sales_invoice_post_propose document_id [effective_at]
```

**Zugriff:** `propose`

**Parameter**

| Name           | Typ      | Pflicht | Beschreibung                                                    | Standard |
| -------------- | -------- | ------- | --------------------------------------------------------------- | -------- |
| `document_id`  | `string` | ja      | Opaque identity of the evidence document to inspect or correct. | —        |
| `effective_at` | `string` | nein    | UTC instant from which the observation or rule takes effect.    | —        |

**Siehe auch:** Geschäftsaktion [`post_sales_invoice`](./commands#command-post_sales_invoice)

### `post_supplier_credit_note` — Post supplier credit note {#command-post_supplier_credit_note}

Books a credit a supplier sent as the exact reverse of its invoice, leaving the supplier owing what
it states.

**Aufruf**

```text
supplier_credit_note_post_propose credit_note_id [effective_at]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry` · Schreibt: `ledger_entry`

**Siehe auch:** Agenten-Tool
[`supplier_credit_note_post_propose`](./commands#tool-supplier_credit_note_post_propose)

#### `supplier_credit_note_post_propose` — Post supplier credit note {#tool-supplier_credit_note_post_propose}

Prepare this business mutation without changing state. Post supplier credit note. Human confirmation
is required.

**Aufruf**

```text
supplier_credit_note_post_propose credit_note_id [effective_at]
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ      | Pflicht | Beschreibung                                                         | Standard |
| ---------------- | -------- | ------- | -------------------------------------------------------------------- | -------- |
| `credit_note_id` | `string` | ja      | Opaque identity of the credit note being posted, netted or refunded. | —        |
| `effective_at`   | `string` | nein    | UTC instant from which the observation or rule takes effect.         | —        |

**Siehe auch:** Geschäftsaktion
[`post_supplier_credit_note`](./commands#command-post_supplier_credit_note)

### `post_supplier_invoice` — Post supplier invoice {#command-post_supplier_invoice}

Books a recorded supplier invoice, so what the company owes becomes visible to settlement and the
queue.

**Aufruf**

```text
supplier_invoice_post_propose document_id [effective_at]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry` · Schreibt: `ledger_entry`

**Siehe auch:** Agenten-Tool
[`supplier_invoice_post_propose`](./commands#tool-supplier_invoice_post_propose)

#### `supplier_invoice_post_propose` — Post supplier invoice {#tool-supplier_invoice_post_propose}

Prepare this business mutation without changing state. Post supplier invoice. Human confirmation is
required.

**Aufruf**

```text
supplier_invoice_post_propose document_id [effective_at]
```

**Zugriff:** `propose`

**Parameter**

| Name           | Typ      | Pflicht | Beschreibung                                                    | Standard |
| -------------- | -------- | ------- | --------------------------------------------------------------- | -------- |
| `document_id`  | `string` | ja      | Opaque identity of the evidence document to inspect or correct. | —        |
| `effective_at` | `string` | nein    | UTC instant from which the observation or rule takes effect.    | —        |

**Siehe auch:** Geschäftsaktion [`post_supplier_invoice`](./commands#command-post_supplier_invoice)

### `post_supplier_payment` — Post supplier payment {#command-post_supplier_payment}

Records an outgoing payment and explicitly settles a supplier invoice entry.

**Aufruf**

```text
supplier_payment_post_propose invoice_id amount [payment_number] [source_record_id] [effective_at]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation` · Schreibt: `source_record`,
`document`, `ledger_entry`, `settlement_allocation`

**Siehe auch:** Agenten-Tool
[`supplier_payment_post_propose`](./commands#tool-supplier_payment_post_propose), Aktion
[`post_supplier_payment`](./views#action-post_supplier_payment)

#### `supplier_payment_post_propose` — Post supplier payment {#tool-supplier_payment_post_propose}

Prepare this business mutation without changing state. Post supplier payment. Human confirmation is
required.

**Aufruf**

```text
supplier_payment_post_propose invoice_id amount [payment_number] [source_record_id] [effective_at]
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                     | Standard |
| ------------------ | -------- | ------- | -------------------------------------------------------------------------------- | -------- |
| `invoice_id`       | `string` | ja      | Opaque identity of the invoice evidence associated with a payment or allocation. | —        |
| `amount`           | `string` | ja      | Monetary amount of the payment or financial observation.                         | —        |
| `payment_number`   | `string` | nein    | Human-facing payment reference used for matching and investigation.              | —        |
| `source_record_id` | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.     | —        |
| `effective_at`     | `string` | nein    | UTC instant from which the observation or rule takes effect.                     | —        |

**Siehe auch:** Geschäftsaktion [`post_supplier_payment`](./commands#command-post_supplier_payment)

### `post_supplier_refund` — Post supplier refund {#command-post_supplier_refund}

Takes money back from a supplier and settles the credit note it repays.

**Aufruf**

```text
supplier_refund_post_propose credit_note_id amount [refund_number] [source_record_id] [effective_at]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation` · Schreibt: `source_record`,
`document`, `ledger_entry`, `settlement_allocation`

**Siehe auch:** Agenten-Tool
[`supplier_refund_post_propose`](./commands#tool-supplier_refund_post_propose)

#### `supplier_refund_post_propose` — Post supplier refund {#tool-supplier_refund_post_propose}

Prepare this business mutation without changing state. Post supplier refund. Human confirmation is
required.

**Aufruf**

```text
supplier_refund_post_propose credit_note_id amount [refund_number] [source_record_id] [effective_at]
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                  | Standard |
| ------------------ | -------- | ------- | ----------------------------------------------------------------------------- | -------- |
| `credit_note_id`   | `string` | ja      | Opaque identity of the credit note being posted, netted or refunded.          | —        |
| `amount`           | `string` | ja      | Monetary amount of the payment or financial observation.                      | —        |
| `refund_number`    | `string` | nein    | Caller-supplied number for the refund document; one is generated when absent. | —        |
| `source_record_id` | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.  | —        |
| `effective_at`     | `string` | nein    | UTC instant from which the observation or rule takes effect.                  | —        |

**Siehe auch:** Geschäftsaktion [`post_supplier_refund`](./commands#command-post_supplier_refund)

### `preview_payment_run` — Preview payment run {#command-preview_payment_run}

Shows which supplier invoices are worth paying now, what each supplier is owed, and what was
withheld, without paying anything.

**Aufruf**

```text
payment_run_preview pay_by
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation`, `party`, `payment_term` ·
Schreibt: —

**Siehe auch:** Agenten-Tool [`payment_run_preview`](./commands#tool-payment_run_preview)

#### `payment_run_preview` — Preview a payment run {#tool-payment_run_preview}

Show which supplier invoices are worth paying now, what each supplier is owed and what was withheld,
without paying anything. Names an early-payment rate and its deadline; never states what a discount
is worth.

**Aufruf**

```text
payment_run_preview pay_by
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage          | Art                        | Standard |
| ------------------------- | -------------------------- | -------- |
| `MCP payment_run_preview` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Show which supplier invoices are worth paying now, what each supplier is owed, what the run totals
per currency, and what was withheld.

**Verwenden, wenn**

- Somebody is deciding what should go out on a payment day
- or is checking which invoices can still be paid for less.

**Nicht verwenden, wenn**

- One invoice is in question
- or the amounts have already been confirmed and the run is ready to execute.

**Parameter**

| Name     | Typ      | Pflicht | Beschreibung                                                                                                                                      | Standard |
| -------- | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `pay_by` | `string` | ja      | The day the payment run is being made for; invoices due on or before it are proposed, as is any invoice whose early-payment window is still open. | —        |

**Siehe auch:** Geschäftsaktion [`preview_payment_run`](./commands#command-preview_payment_run)

### `component_history` — Read component assignment history {#command-component_history}

Separate received values from owner-confirmed internal classification and exact cost-center shares;
preserve postings.

**Aufruf**

```text
finance_component_history component_id [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document`, `document_line`, `source_record`, `financial_component`,
`component_assignment_revision`, `component_assignment_part`, `finance_reference`, `finance_state` ·
Schreibt: —

**Siehe auch:** Agenten-Tool
[`finance_component_history`](./commands#tool-finance_component_history)

#### `finance_component_history` — Attribution history {#tool-finance_component_history}

Read immutable internal component assignment revisions and their author/action/reason.

**Aufruf**

```text
finance_component_history component_id [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                | Art                        | Standard |
| ------------------------------- | -------------------------- | -------- |
| `MCP finance_component_history` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read received component values and internal attribution history.

**Verwenden, wenn**

- Inspect received detail separately from explicit internal attribution.

**Nicht verwenden, wenn**

- Prove balances or external posting.

**Parameter**

| Name           | Typ       | Pflicht | Beschreibung                                                    | Standard |
| -------------- | --------- | ------- | --------------------------------------------------------------- | -------- |
| `component_id` | `string`  | ja      | Opaque normalized financial component identity.                 | —        |
| `limit`        | `integer` | nein    | Maximum number of records or jobs processed by this invocation. | —        |
| `offset`       | `integer` | nein    | Number of matching rows to skip for bounded pagination.         | —        |

**Siehe auch:** Geschäftsaktion [`component_history`](./commands#command-component_history)

### `list_references` — Read finance references {#command-list_references}

Read or maintain defined internal references with immutable reasoned decisions and owner
confirmation for changes.

**Aufruf**

```text
finance_references [kind] [state] [query] [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `finance_reference`, `finance_state`, `business_event` · Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_references`](./commands#tool-finance_references)

#### `finance_references` — Finance references {#tool-finance_references}

Read defined cost centers, case codes and coding groups; no inferred financial meaning.

**Aufruf**

```text
finance_references [kind] [state] [query] [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage         | Art                        | Standard |
| ------------------------ | -------------------------- | -------- |
| `MCP finance_references` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read defined internal cost centers, case codes and coding groups.

**Verwenden, wenn**

- Find permitted internal classification references.

**Nicht verwenden, wenn**

- Prove balances or external posting.

**Parameter**

| Name     | Typ       | Pflicht | Beschreibung                                                                                                               | Standard |
| -------- | --------- | ------- | -------------------------------------------------------------------------------------------------------------------------- | -------- |
| `kind`   | `string`  | nein    | Explicit internal or target reference kind; no inferred tax or country meaning. `cost_center`, `case_code`, `coding_group` | —        |
| `state`  | `string`  | nein    | Active or blocked eligibility for new account postings. `active`, `blocked`                                                | —        |
| `query`  | `string`  | nein    | Optional invoice-number search within matching same-party credit targets.                                                  | —        |
| `limit`  | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                                                            | —        |
| `offset` | `integer` | nein    | Number of matching rows to skip for bounded pagination.                                                                    | —        |

**Siehe auch:** Geschäftsaktion [`list_references`](./commands#command-list_references)

### `invoice_credit_context` — Read invoice credit context {#command-invoice_credit_context}

Shows exact customer-invoice positions and remaining credit capacity without recording a credit.

**Aufruf**

```text
invoice_credit_context invoice_id
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `document_line`, `ledger_entry`, `ledger_reversal`,
`settlement_allocation` · Schreibt: —

**Siehe auch:** Agenten-Tool [`invoice_credit_context`](./commands#tool-invoice_credit_context)

#### `invoice_credit_context` — Invoice credit context {#tool-invoice_credit_context}

Read eligible customer-invoice positions, remaining quantities, amount capacity and blockers.

**Aufruf**

```text
invoice_credit_context invoice_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage             | Art                        | Standard |
| ---------------------------- | -------------------------- | -------- |
| `MCP invoice_credit_context` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read one customer invoice's eligible opaque line identities and remaining credit capacity.

**Verwenden, wenn**

- An invoice-linked customer credit must be prepared from current posted evidence.

**Nicht verwenden, wenn**

- A return-only legacy credit or a physical return disposition is required.

**Parameter**

| Name         | Typ      | Pflicht | Beschreibung                                                                     | Standard |
| ------------ | -------- | ------- | -------------------------------------------------------------------------------- | -------- |
| `invoice_id` | `string` | ja      | Opaque identity of the invoice evidence associated with a payment or allocation. | —        |

**Siehe auch:** Geschäftsaktion
[`invoice_credit_context`](./commands#command-invoice_credit_context)

### `opening_context` — Read opening position context {#command-opening_context}

Reads permitted opening counterpart, tenant parties and confirmation revision.

**Aufruf**

```text
finance_opening_context [query]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `party`, `subledger_account`, `finance_state` · Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_opening_context`](./commands#tool-finance_opening_context)

#### `finance_opening_context` — Opening positions {#tool-finance_opening_context}

Read permitted accounts, parties and revision for opening residual positions.

**Aufruf**

```text
finance_opening_context [query]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage              | Art                        | Standard |
| ----------------------------- | -------------------------- | -------- |
| `MCP finance_opening_context` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read permitted opening account, active parties and current review revision.

**Verwenden, wenn**

- Prepare an opening residual import from the previous system.

**Nicht verwenden, wenn**

- Infer historic balances or reconstruct missing due dates.

**Parameter**

| Name    | Typ      | Pflicht | Beschreibung                                                              | Standard |
| ------- | -------- | ------- | ------------------------------------------------------------------------- | -------- |
| `query` | `string` | nein    | Optional invoice-number search within matching same-party credit targets. | —        |

**Siehe auch:** Geschäftsaktion [`opening_context`](./commands#command-opening_context)

### `list_accounts` — Read operational accounts {#command-list_accounts}

Uses shared tenant-scoped operational account configuration with explicit owner confirmation for
changes.

**Aufruf**

```text
finance_accounts
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `subledger_account`, `finance_role_destination`, `finance_state` ·
Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_accounts`](./commands#tool-finance_accounts)

#### `finance_accounts` — Operational accounts {#tool-finance_accounts}

Read allowed accounts, roles, defaults and preview revision.

**Aufruf**

```text
finance_accounts
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage       | Art                        | Standard |
| ---------------------- | -------------------------- | -------- |
| `MCP finance_accounts` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read permitted operational accounts, role defaults and the current finance revision.

**Verwenden, wenn**

- Find permitted destinations before configuring an account.

**Nicht verwenden, wenn**

- Prove balances or external posting.

**Parameter**

Keine Parameter.

**Siehe auch:** Geschäftsaktion [`list_accounts`](./commands#command-list_accounts)

### `transaction_matrix` — Read operational transaction matrix {#command-transaction_matrix}

Describes configured defaults and fixed operation roles; no posting or authorization.

**Aufruf**

```text
finance_matrix
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `subledger_account`, `finance_role_destination`, `finance_state` ·
Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_matrix`](./commands#tool-finance_matrix)

#### `finance_matrix` — Operational transaction matrix {#tool-finance_matrix}

Read fixed directions, stated amount bases and configured local defaults. Does not authorize a
transaction or infer external tax coding.

**Aufruf**

```text
finance_matrix
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage     | Art                        | Standard |
| -------------------- | -------------------------- | -------- |
| `MCP finance_matrix` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read fixed operational directions, received amount bases and configured default accounts.

**Verwenden, wenn**

- Find permitted destinations before configuring an account.

**Nicht verwenden, wenn**

- Prove balances or external posting.

**Parameter**

Keine Parameter.

**Siehe auch:** Geschäftsaktion [`transaction_matrix`](./commands#command-transaction_matrix)

### `settlement_context` — Read payment and credit context {#command-settlement_context}

Reads the selected invoice or available credit and matching invoice choices.

**Aufruf**

```text
finance_settlement_context document_id [query]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation`, `subledger_account`,
`finance_state` · Schreibt: —

**Siehe auch:** Agenten-Tool
[`finance_settlement_context`](./commands#tool-finance_settlement_context)

#### `finance_settlement_context` — Payment and credit context {#tool-finance_settlement_context}

Read an invoice or original credit and matching invoice choices.

**Aufruf**

```text
finance_settlement_context document_id [query]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                 | Art                        | Standard |
| -------------------------------- | -------------------------- | -------- |
| `MCP finance_settlement_context` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read invoice/payment-credit context and matching invoice choices; for an unallocated customer
payment each choice carries the reasons it is a candidate.

**Verwenden, wenn**

- Prepare actual payment, credit allocation or refund.

**Nicht verwenden, wenn**

- Determine tax or calculate a discount.

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung                                                              | Standard |
| ------------- | -------- | ------- | ------------------------------------------------------------------------- | -------- |
| `document_id` | `string` | ja      | Opaque identity of the evidence document to inspect or correct.           | —        |
| `query`       | `string` | nein    | Optional invoice-number search within matching same-party credit targets. | —        |

**Siehe auch:** Geschäftsaktion [`settlement_context`](./commands#command-settlement_context)

### `component_context` — Read received financial detail {#command-component_context}

Separate received values from owner-confirmed internal classification and exact cost-center shares;
preserve postings.

**Aufruf**

```text
finance_components document_id [reference_query] [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document`, `document_line`, `source_record`, `financial_component`,
`component_assignment_revision`, `component_assignment_part`, `finance_reference`, `finance_state` ·
Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_components`](./commands#tool-finance_components)

#### `finance_components` — Financial detail {#tool-finance_components}

Read received invoice/credit detail separately from internal attribution; no inferred net or tax.

**Aufruf**

```text
finance_components document_id [reference_query] [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage         | Art                        | Standard |
| ------------------------ | -------------------------- | -------- |
| `MCP finance_components` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read received component values and internal attribution history.

**Verwenden, wenn**

- Inspect received detail separately from explicit internal attribution.

**Nicht verwenden, wenn**

- Prove balances or external posting.

**Parameter**

| Name              | Typ       | Pflicht | Beschreibung                                                     | Standard |
| ----------------- | --------- | ------- | ---------------------------------------------------------------- | -------- |
| `document_id`     | `string`  | ja      | Opaque identity of the evidence document to inspect or correct.  | —        |
| `reference_query` | `string`  | nein    | Literal search for active same-tenant classification references. | —        |
| `limit`           | `integer` | nein    | Maximum number of records or jobs processed by this invocation.  | —        |
| `offset`          | `integer` | nein    | Number of matching rows to skip for bounded pagination.          | —        |

**Siehe auch:** Geschäftsaktion [`component_context`](./commands#command-component_context)

### `reference_history` — Read reference history {#command-reference_history}

Read or maintain defined internal references with immutable reasoned decisions and owner
confirmation for changes.

**Aufruf**

```text
finance_reference_history reference_id [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `finance_reference`, `finance_state`, `business_event` · Schreibt: —

**Siehe auch:** Agenten-Tool
[`finance_reference_history`](./commands#tool-finance_reference_history)

#### `finance_reference_history` — Reference history {#tool-finance_reference_history}

Read immutable before/after decisions, reason and action for one reference.

**Aufruf**

```text
finance_reference_history reference_id [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                | Art                        | Standard |
| ------------------------------- | -------------------------- | -------- |
| `MCP finance_reference_history` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read immutable reference decision history.

**Verwenden, wenn**

- Inspect an existing reference and its reasoned changes.

**Nicht verwenden, wenn**

- Prove balances or external posting.

**Parameter**

| Name           | Typ       | Pflicht | Beschreibung                                                    | Standard |
| -------------- | --------- | ------- | --------------------------------------------------------------- | -------- |
| `reference_id` | `string`  | ja      | Opaque same-tenant managed reference identity.                  | —        |
| `limit`        | `integer` | nein    | Maximum number of records or jobs processed by this invocation. | —        |
| `offset`       | `integer` | nein    | Number of matching rows to skip for bounded pagination.         | —        |

**Siehe auch:** Geschäftsaktion [`reference_history`](./commands#command-reference_history)

### `adjustment_context` — Read settlement reduction context {#command-adjustment_context}

Reads the remaining claim and permitted noncash counterpart.

**Aufruf**

```text
finance_adjustment_context invoice_id
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation`, `subledger_account`,
`finance_state` · Schreibt: —

**Siehe auch:** Agenten-Tool
[`finance_adjustment_context`](./commands#tool-finance_adjustment_context)

#### `finance_adjustment_context` — Settlement reduction context {#tool-finance_adjustment_context}

Read the current invoice claim, accounts and review revision.

**Aufruf**

```text
finance_adjustment_context invoice_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                 | Art                        | Standard |
| -------------------------------- | -------------------------- | -------- |
| `MCP finance_adjustment_context` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read the remaining claim and reduction account configuration.

**Verwenden, wenn**

- Prepare a separately accepted settlement reduction.

**Nicht verwenden, wenn**

- Determine tax or calculate a discount.

**Parameter**

| Name         | Typ      | Pflicht | Beschreibung                                                                     | Standard |
| ------------ | -------- | ------- | -------------------------------------------------------------------------------- | -------- |
| `invoice_id` | `string` | ja      | Opaque identity of the invoice evidence associated with a payment or allocation. | —        |

**Siehe auch:** Geschäftsaktion [`adjustment_context`](./commands#command-adjustment_context)

### `list_source_mappings` — Read source code mappings {#command-list_source_mappings}

Resolve explicit source codes with reviewed immutable classification revisions; never change
received evidence or postings.

**Aufruf**

```text
finance_source_mappings [query] [source_query] [reference_query] [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `source_system`, `finance_reference`, `finance_state`,
`source_classification_mapping_revision` · Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_source_mappings`](./commands#tool-finance_source_mappings)

#### `finance_source_mappings` — Source code mappings {#tool-finance_source_mappings}

Read exact source classification mappings and existing references. No tax inference.

**Aufruf**

```text
finance_source_mappings [query] [source_query] [reference_query] [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage              | Art                        | Standard |
| ----------------------------- | -------------------------- | -------- |
| `MCP finance_source_mappings` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read or propose exact source-code classification with separate source and internal provenance.

**Verwenden, wenn**

- Find permitted internal classification references.

**Nicht verwenden, wenn**

- Prove balances or external posting.

**Parameter**

| Name              | Typ       | Pflicht | Beschreibung                                                                       | Standard |
| ----------------- | --------- | ------- | ---------------------------------------------------------------------------------- | -------- |
| `query`           | `string`  | nein    | Optional invoice-number search within matching same-party credit targets.          | —        |
| `source_query`    | `string`  | nein    | Literal search for registered source systems available to classify received codes. | —        |
| `reference_query` | `string`  | nein    | Literal search for active same-tenant classification references.                   | —        |
| `limit`           | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                    | —        |
| `offset`          | `integer` | nein    | Number of matching rows to skip for bounded pagination.                            | —        |

**Siehe auch:** Geschäftsaktion [`list_source_mappings`](./commands#command-list_source_mappings)

### `source_mapping_history` — Read source mapping history {#command-source_mapping_history}

Resolve explicit source codes with reviewed immutable classification revisions; never change
received evidence or postings.

**Aufruf**

```text
finance_source_mapping_history mapping_id [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `source_system`, `finance_reference`, `finance_state`,
`source_classification_mapping_revision` · Schreibt: —

**Siehe auch:** Agenten-Tool
[`finance_source_mapping_history`](./commands#tool-finance_source_mapping_history)

#### `finance_source_mapping_history` — Source mapping history {#tool-finance_source_mapping_history}

Read source classification revisions and actor/reason/action.

**Aufruf**

```text
finance_source_mapping_history mapping_id [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                     | Art                        | Standard |
| ------------------------------------ | -------------------------- | -------- |
| `MCP finance_source_mapping_history` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read or propose exact source-code classification with separate source and internal provenance.

**Verwenden, wenn**

- Inspect an existing reference and its reasoned changes.

**Nicht verwenden, wenn**

- Prove balances or external posting.

**Parameter**

| Name         | Typ       | Pflicht | Beschreibung                                                                      | Standard |
| ------------ | --------- | ------- | --------------------------------------------------------------------------------- | -------- |
| `mapping_id` | `string`  | ja      | Opaque Finance mapping revision identity; history follows its exact owning scope. | —        |
| `limit`      | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                   | —        |
| `offset`     | `integer` | nein    | Number of matching rows to skip for bounded pagination.                           | —        |

**Siehe auch:** Geschäftsaktion
[`source_mapping_history`](./commands#command-source_mapping_history)

### `record_free_supplier_invoice` — Record free supplier invoice {#command-record_free_supplier_invoice}

Records stated supplier invoice evidence without a purchase-order line and posts its payable
atomically without inventing a commitment or Movement.

**Aufruf**

```text
supplier_invoice_free_record_propose supplier_id number currency gross_amount [document_date] [effective_at] lines
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `party`, `item` · Schreibt: `source_record`, `document`, `document_line`,
`ledger_entry`, `business_event`

**Siehe auch:** Agenten-Tool
[`supplier_invoice_free_record_propose`](./commands#tool-supplier_invoice_free_record_propose)

#### `supplier_invoice_free_record_propose` — Record free supplier invoice {#tool-supplier_invoice_free_record_propose}

Prepare this business mutation without changing state. Record free supplier invoice. Human
confirmation is required.

**Aufruf**

```text
supplier_invoice_free_record_propose supplier_id number currency gross_amount [document_date] [effective_at] lines
```

**Zugriff:** `propose`

Record source-stated supplier invoice evidence and post its payable without inventing a purchase
order.

**Verwenden, wenn**

- A supplier invoice contains supported free goods
- service or charge positions with no purchase-order line.

**Nicht verwenden, wenn**

- The invoice positions belong to existing purchase-order lines.

**Voraussetzungen**

- The Party has supplier role and every stated line is valid tenant evidence.

**Abgelehnt, wenn**

- `invalid_supplier_invoice` — Supplier

**Parameter**

| Name                   | Typ      | Pflicht | Beschreibung                                                                                 | Standard |
| ---------------------- | -------- | ------- | -------------------------------------------------------------------------------------------- | -------- |
| `supplier_id`          | `string` | ja      | Opaque same-tenant identity of the supplier Party stated on the invoice.                     | —        |
| `number`               | `string` | ja      | Human-facing document or transaction number; it is not internal identity.                    | —        |
| `currency`             | `string` | ja      | ISO 4217 currency code for monetary values.                                                  | —        |
| `gross_amount`         | `string` | ja      | Total the source states for the document; recorded as received and never calculated.         | —        |
| `document_date`        | `string` | nein    | Business date printed on or asserted by the evidence document.                               | —        |
| `effective_at`         | `string` | nein    | UTC instant from which the observation or rule takes effect.                                 | —        |
| `lines`                | `array`  | ja      | Complete intended normalized DocumentLine Evidence snapshot for an atomic manual correction. | —        |
| `lines[].item_id`      | `string` | nein    | Opaque identity of the operational item reference.                                           | —        |
| `lines[].sku`          | `string` | nein    | Human-facing stock-keeping code used to find an item; internal joins use item_id.            | —        |
| `lines[].description`  | `string` | nein    | Human-readable explanation of the record or rule.                                            | —        |
| `lines[].quantity`     | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                      | —        |
| `lines[].unit`         | `string` | nein    | Unit of measure in which the quantity is expressed.                                          | —        |
| `lines[].unit_price`   | `string` | ja      | Decimal monetary amount for one unit before quantity multiplication.                         | —        |
| `lines[].gross_amount` | `string` | ja      | Total the source states for the document; recorded as received and never calculated.         | —        |
| `lines[].line_type`    | `string` | nein    | Closed kind of a document line, such as goods or a charge, taken from the source statement.  | —        |

**Prüfen mit:** `document_register` — The supplier invoice and stated lines are retained.;
`finance_balances` — The payable derives from posted LedgerEntries.

**Siehe auch:** Geschäftsaktion
[`record_free_supplier_invoice`](./commands#command-record_free_supplier_invoice), Projection
[`document_register`](./views#projection-document_register)

### `apply_settlement` — Record payment or use existing credit {#command-apply_settlement}

Atomically records stated cash, explicit allocation and optional reduction, or consumes existing
credit after owner confirmation.

**Aufruf**

```text
finance_settlement_propose expected_revision document_id amount [reference] [effective_at] [source_record_id] [source_effect_id] mode [allocation_amount] [reduction] [invoice_id]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation`, `subledger_account`,
`finance_state` · Schreibt: `source_record`, `document`, `ledger_entry`, `settlement_allocation`,
`action`

**Siehe auch:** Agenten-Tool
[`finance_settlement_propose`](./commands#tool-finance_settlement_propose)

#### `finance_settlement_propose` — Record payment or use credit {#tool-finance_settlement_propose}

Prepare actual payment with explicit allocation and optional stated reduction, allocate existing
credit, or record an actual refund. Requires owner confirmation; never initiates a bank transfer.

**Aufruf**

```text
finance_settlement_propose expected_revision document_id amount [reference] [effective_at] [source_record_id] [source_effect_id] mode [allocation_amount] [reduction] [invoice_id]
```

**Zugriff:** `propose`

Prepare actual payment with explicit allocation/reduction, or consume existing credit.

**Verwenden, wenn**

- Record actual money or allocate an existing available credit.

**Nicht verwenden, wenn**

- Initiate a bank transfer or infer a discount.

**Voraussetzungen**

- Active compatible accounts, available claim/credit, current revision and explicit owner
  confirmation.

**Abgelehnt, wenn**

- `invalid_settlement` — Stale revision, duplicate source effect, invalid or excessive amount,
  incompatible account/party/currency or missing supplier agreement.

**Parameter**

| Name                         | Typ       | Pflicht | Beschreibung                                                                                                                                                                                                                                                                            | Standard |
| ---------------------------- | --------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `expected_revision`          | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.                                                                                                                                                                                                             | —        |
| `document_id`                | `string`  | ja      | Opaque identity of the evidence document to inspect or correct.                                                                                                                                                                                                                         | —        |
| `amount`                     | `string`  | ja      | Monetary amount of the payment or financial observation.                                                                                                                                                                                                                                | —        |
| `reference`                  | `string`  | nein    | The number the returning parcel will carry, as the customer or the company stated it; never generated.                                                                                                                                                                                  | —        |
| `effective_at`               | `string`  | nein    | UTC instant from which the observation or rule takes effect.                                                                                                                                                                                                                            | —        |
| `source_record_id`           | `string`  | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                                                                                                                                                            | `None`   |
| `source_effect_id`           | `string`  | nein    | Stable effect reference within the original evidence, consumed at most once.                                                                                                                                                                                                            | `None`   |
| `mode`                       | `string`  | ja      | Payment requires allocation_amount, reference and effective_at; allocate_credit requires invoice_id; refund_credit requires reference and effective_at. Only payment accepts reduction. Cash evidence fields are only for payment/refund. `payment`, `allocate_credit`, `refund_credit` | —        |
| `allocation_amount`          | `string`  | nein    | Explicit stated amount to offset against the selected invoice; zero leaves the credit unsettled.                                                                                                                                                                                        | —        |
| `reduction`                  | `object`  | nein    | —                                                                                                                                                                                                                                                                                       | `None`   |
| `reduction.amount`           | `string`  | ja      | Monetary amount of the payment or financial observation.                                                                                                                                                                                                                                | —        |
| `reduction.reason_category`  | `string`  | ja      | Explicit accepted discount, agreed deduction or small remainder category. `early_payment_discount`, `agreed_deduction`, `accepted_small_remainder`, `bad_debt`                                                                                                                          | —        |
| `reduction.reason`           | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                                                                                                                                                 | —        |
| `reduction.agreement`        | `string`  | nein    | Stated supplier entitlement or agreement authorizing the reduction.                                                                                                                                                                                                                     | —        |
| `reduction.source_record_id` | `string`  | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                                                                                                                                                            | `None`   |
| `reduction.source_effect_id` | `string`  | nein    | Stable effect reference within the original evidence, consumed at most once.                                                                                                                                                                                                            | `None`   |
| `invoice_id`                 | `string`  | nein    | Opaque identity of the invoice evidence associated with a payment or allocation.                                                                                                                                                                                                        | —        |

**Prüfen mit:** `finance.settlement.context` — Current remaining invoice claim or available credit.

**Siehe auch:** Geschäftsaktion [`apply_settlement`](./commands#command-apply_settlement)

### `record_sales_credit` — Record return credit {#command-record_sales_credit}

Records a stated invoice-linked customer credit with explicit optional netting, or legacy return
credit through an order line; no refund or stock movement.

**Aufruf**

```text
sales_credit_record_propose [order_line_id] [quantity] [invoice_id] [reason] [allocation_amount] [lines] gross_amount number [effective_at]
```

**Erreichbar über:** Web · API · MCP · Chat

**Wirkung:** Liest: `document`, `document_line`, `commitment`, `movement`, `ledger_entry`,
`ledger_reversal`, `settlement_allocation` · Schreibt: `source_record`, `document`, `document_line`,
`ledger_entry`, `settlement_allocation`, `business_event` · Erzeugt: `credit.recorded`

**Siehe auch:** Agenten-Tool
[`sales_credit_record_propose`](./commands#tool-sales_credit_record_propose), Event
[`credit.recorded`](./events#event-credit-recorded)

#### `sales_credit_record_propose` — Record customer credit {#tool-sales_credit_record_propose}

Prepare this business mutation without changing state. Record customer credit. Human confirmation is
required.

**Aufruf**

```text
sales_credit_record_propose [order_line_id] [quantity] [invoice_id] [reason] [allocation_amount] [lines] gross_amount number [effective_at]
```

**Zugriff:** `propose`

Record either an invoice-linked financial credit or the retained legacy order-line return credit
shape.

**Verwenden, wenn**

- A human has stated the exact credit amount and selected one complete supported evidence shape.

**Nicht verwenden, wenn**

- Returned goods need a physical disposition; use the return disposition action separately.

**Voraussetzungen**

- Invoice-linked and legacy fields are mutually exclusive and every opaque identity belongs to the
  tenant.

**Abgelehnt, wenn**

- `invalid_credit_shape` — Required fields are missing

**Parameter**

| Name                      | Typ      | Pflicht | Beschreibung                                                                                     | Standard |
| ------------------------- | -------- | ------- | ------------------------------------------------------------------------------------------------ | -------- |
| `order_line_id`           | `string` | nein    | Opaque sales-order line identity linked by invoice billing evidence.                             | —        |
| `quantity`                | `string` | nein    | Decimal quantity expressed in the item's relevant unit.                                          | —        |
| `invoice_id`              | `string` | nein    | Opaque identity of the invoice evidence associated with a payment or allocation.                 | —        |
| `reason`                  | `string` | nein    | Human-readable explanation for a hold, correction, or lifecycle change.                          | —        |
| `allocation_amount`       | `string` | nein    | Explicit stated amount to offset against the selected invoice; zero leaves the credit unsettled. | —        |
| `lines`                   | `array`  | nein    | Complete intended normalized DocumentLine Evidence snapshot for an atomic manual correction.     | —        |
| `lines[].invoice_line_id` | `string` | ja      | Opaque identity of the invoice line this credit line refers back to.                             | —        |
| `lines[].quantity`        | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                          | —        |
| `lines[].gross_amount`    | `string` | ja      | Total the source states for the document; recorded as received and never calculated.             | —        |
| `gross_amount`            | `string` | ja      | Total the source states for the document; recorded as received and never calculated.             | —        |
| `number`                  | `string` | ja      | Human-facing document or transaction number; it is not internal identity.                        | —        |
| `effective_at`            | `string` | nein    | UTC instant from which the observation or rule takes effect.                                     | —        |

**Prüfen mit:** `invoice_credit_context` — Remaining invoice-linked position and amount capacity
derives independently after execution.; `document_register` — The retained credit and its shortest
line links exist.

**Siehe auch:** Geschäftsaktion [`record_sales_credit`](./commands#command-record_sales_credit),
Projection [`document_register`](./views#projection-document_register)

### `record_sales_invoice` — Record sales invoice {#command-record_sales_invoice}

Records a stated invoice against one order line and posts its receivable atomically.

**Aufruf**

```text
sales_invoice_record_propose [order_line_id] [quantity] [lines] gross_amount number [effective_at] [delivery_guard]
```

**Erreichbar über:** Web · API · MCP · Chat

**Wirkung:** Liest: `document`, `document_line` · Schreibt: `source_record`, `document`,
`document_line`, `ledger_entry` · Erzeugt: `invoice.recorded`

**Siehe auch:** Agenten-Tool
[`sales_invoice_record_propose`](./commands#tool-sales_invoice_record_propose), Event
[`invoice.recorded`](./events#event-invoice-recorded)

#### `sales_invoice_record_propose` — Record sales invoice {#tool-sales_invoice_record_propose}

Prepare this business mutation without changing state. Record sales invoice. Human confirmation is
required.

**Aufruf**

```text
sales_invoice_record_propose [order_line_id] [quantity] [lines] gross_amount number [effective_at] [delivery_guard]
```

**Zugriff:** `propose`

**Parameter**

| Name                                  | Typ       | Pflicht | Beschreibung                                                                                                                                                                 | Standard |
| ------------------------------------- | --------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `order_line_id`                       | `string`  | nein    | Opaque sales-order line identity linked by invoice billing evidence.                                                                                                         | —        |
| `quantity`                            | `string`  | nein    | Decimal quantity expressed in the item's relevant unit.                                                                                                                      | —        |
| `lines`                               | `array`   | nein    | Complete intended normalized DocumentLine Evidence snapshot for an atomic manual correction.                                                                                 | —        |
| `lines[].order_line_id`               | `string`  | ja      | Opaque sales-order line identity linked by invoice billing evidence.                                                                                                         | —        |
| `lines[].quantity`                    | `string`  | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                      | —        |
| `lines[].gross_amount`                | `string`  | ja      | Total the source states for the document; recorded as received and never calculated.                                                                                         | —        |
| `lines[].reality_finance_v1`          | `object`  | nein    | —                                                                                                                                                                            | —        |
| `lines[].reality_finance_v1.version`  | `integer` | nein    | `1`                                                                                                                                                                          | —        |
| `lines[].reality_finance_v1.net`      | `string`  | nein    | —                                                                                                                                                                            | —        |
| `lines[].reality_finance_v1.tax`      | `string`  | nein    | —                                                                                                                                                                            | —        |
| `lines[].reality_finance_v1.base`     | `string`  | nein    | —                                                                                                                                                                            | —        |
| `lines[].reality_finance_v1.gross`    | `string`  | nein    | —                                                                                                                                                                            | —        |
| `lines[].reality_finance_v1.currency` | `string`  | nein    | ISO 4217 currency code for monetary values.                                                                                                                                  | —        |
| `lines[].reality_finance_v1.codes`    | `object`  | nein    | —                                                                                                                                                                            | —        |
| `gross_amount`                        | `string`  | ja      | Total the source states for the document; recorded as received and never calculated.                                                                                         | —        |
| `number`                              | `string`  | ja      | Human-facing document or transaction number; it is not internal identity.                                                                                                    | —        |
| `effective_at`                        | `string`  | nein    | UTC instant from which the observation or rule takes effect.                                                                                                                 | —        |
| `delivery_guard`                      | `object`  | nein    | Optional single-line sales-invoice precondition binding the unit and unbilled quantity read for the invoiced order line; rechecked under the delivery lock before recording. | —        |
| `delivery_guard.unbilled_quantity`    | `string`  | ja      | —                                                                                                                                                                            | —        |
| `delivery_guard.unit`                 | `string`  | ja      | Unit of measure in which the quantity is expressed.                                                                                                                          | —        |

**Siehe auch:** Geschäftsaktion [`record_sales_invoice`](./commands#command-record_sales_invoice)

### `record_supplier_invoice` — Record supplier invoice {#command-record_supplier_invoice}

Records stated supplier invoice evidence linked to a purchase order line and posts its payable
atomically.

**Aufruf**

```text
supplier_invoice_record_propose [order_line_id] [quantity] [lines] gross_amount number [effective_at]
```

**Erreichbar über:** Web · API · MCP · Chat

**Wirkung:** Liest: `document`, `document_line` · Schreibt: `source_record`, `document`,
`document_line`, `ledger_entry`, `business_event`

**Siehe auch:** Agenten-Tool
[`supplier_invoice_record_propose`](./commands#tool-supplier_invoice_record_propose)

#### `supplier_invoice_record_propose` — Record supplier invoice {#tool-supplier_invoice_record_propose}

Prepare this business mutation without changing state. Record supplier invoice. Human confirmation
is required.

**Aufruf**

```text
supplier_invoice_record_propose [order_line_id] [quantity] [lines] gross_amount number [effective_at]
```

**Zugriff:** `propose`

**Parameter**

| Name                                  | Typ       | Pflicht | Beschreibung                                                                                 | Standard |
| ------------------------------------- | --------- | ------- | -------------------------------------------------------------------------------------------- | -------- |
| `order_line_id`                       | `string`  | nein    | Opaque sales-order line identity linked by invoice billing evidence.                         | —        |
| `quantity`                            | `string`  | nein    | Decimal quantity expressed in the item's relevant unit.                                      | —        |
| `lines`                               | `array`   | nein    | Complete intended normalized DocumentLine Evidence snapshot for an atomic manual correction. | —        |
| `lines[].order_line_id`               | `string`  | ja      | Opaque sales-order line identity linked by invoice billing evidence.                         | —        |
| `lines[].quantity`                    | `string`  | ja      | Decimal quantity expressed in the item's relevant unit.                                      | —        |
| `lines[].gross_amount`                | `string`  | ja      | Total the source states for the document; recorded as received and never calculated.         | —        |
| `lines[].reality_finance_v1`          | `object`  | nein    | —                                                                                            | —        |
| `lines[].reality_finance_v1.version`  | `integer` | nein    | `1`                                                                                          | —        |
| `lines[].reality_finance_v1.net`      | `string`  | nein    | —                                                                                            | —        |
| `lines[].reality_finance_v1.tax`      | `string`  | nein    | —                                                                                            | —        |
| `lines[].reality_finance_v1.base`     | `string`  | nein    | —                                                                                            | —        |
| `lines[].reality_finance_v1.gross`    | `string`  | nein    | —                                                                                            | —        |
| `lines[].reality_finance_v1.currency` | `string`  | nein    | ISO 4217 currency code for monetary values.                                                  | —        |
| `lines[].reality_finance_v1.codes`    | `object`  | nein    | —                                                                                            | —        |
| `gross_amount`                        | `string`  | ja      | Total the source states for the document; recorded as received and never calculated.         | —        |
| `number`                              | `string`  | ja      | Human-facing document or transaction number; it is not internal identity.                    | —        |
| `effective_at`                        | `string`  | nein    | UTC instant from which the observation or rule takes effect.                                 | —        |

**Siehe auch:** Geschäftsaktion
[`record_supplier_invoice`](./commands#command-record_supplier_invoice)

### `reverse_ledger_posting_group` — Reverse ledger posting group {#command-reverse_ledger_posting_group}

Preserves one complete immutable posting group, appends its exact inverse, and derives corrected
settlement and financial views.

**Aufruf**

```text
ledger_reversal_propose posting_group_id reason
```

**Erreichbar über:** CLI · Web · API · Chat · MCP · **Bestätigung:** `required`

**Wirkung:** Liest: `ledger_entry`, `ledger_reversal`, `settlement_allocation`, `document`,
`source_record` · Schreibt: `ledger_entry`, `ledger_reversal`, `business_event` · Erzeugt:
`ledger.reversed`

**Siehe auch:** Agenten-Tool [`ledger_reversal_propose`](./commands#tool-ledger_reversal_propose),
Event [`ledger.reversed`](./events#event-ledger-reversed)

#### `ledger_reversal_propose` — Propose Ledger reversal {#tool-ledger_reversal_propose}

Preview a complete inverse posting group without executing before a separate decision.

**Aufruf**

```text
ledger_reversal_propose posting_group_id reason
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                               | Standard |
| ------------------ | -------- | ------- | -------------------------------------------------------------------------- | -------- |
| `posting_group_id` | `string` | ja      | Opaque identity shared by the balanced LedgerEntries in one posting group. | —        |
| `reason`           | `string` | ja      | Human-readable explanation for a hold, correction, or lifecycle change.    | —        |

**Siehe auch:** Geschäftsaktion
[`reverse_ledger_posting_group`](./commands#command-reverse_ledger_posting_group)

### `set_default_account` — Set operational account default {#command-set_default_account}

Uses shared tenant-scoped operational account configuration with explicit owner confirmation for
changes.

**Aufruf**

```text
finance_set_default_account_propose expected_revision role account_id
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `subledger_account`, `finance_role_destination`, `finance_state` ·
Schreibt: `subledger_account`, `finance_role_destination`, `finance_state`, `business_event`

**Siehe auch:** Agenten-Tool
[`finance_set_default_account_propose`](./commands#tool-finance_set_default_account_propose)

#### `finance_set_default_account_propose` — Configure operational accounts {#tool-finance_set_default_account_propose}

Prepare an owner-confirmed operational account change; never execute it autonomously.

**Aufruf**

```text
finance_set_default_account_propose expected_revision role account_id
```

**Zugriff:** `propose`

Prepare an owner-confirmed operational account configuration change.

**Verwenden, wenn**

- Configure an allowed account or default.

**Nicht verwenden, wenn**

- Record money or determine tax treatment.

**Voraussetzungen**

- Owner confirmation, valid same-tenant role and account.

**Abgelehnt, wenn**

- `invalid_account_configuration` — Stale revision, duplicate code, wrong role or foreign account.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                       | Standard |
| ------------------- | --------- | ------- | ---------------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.        | —        |
| `role`              | `string`  | ja      | Repeatable operational role assigned to a party, for example customer or supplier. | —        |
| `account_id`        | `string`  | ja      | Opaque same-tenant operational account identity.                                   | —        |

**Prüfen mit:** `timeline` — The account change event and identity.

**Siehe auch:** Geschäftsaktion [`set_default_account`](./commands#command-set_default_account),
Projection [`timeline`](./views#projection-timeline)

### `set_source_mapping` — Set source code mapping {#command-set_source_mapping}

Resolve explicit source codes with reviewed immutable classification revisions; never change
received evidence or postings.

**Aufruf**

```text
finance_source_mapping_propose expected_revision source_system_id namespace field_kind source_code reference_id [state] reason
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `source_system`, `finance_reference`, `finance_state`,
`source_classification_mapping_revision` · Schreibt: `source_classification_mapping_revision`,
`finance_state`, `business_event` · Erzeugt: `finance.source_mapping_changed`

**Siehe auch:** Agenten-Tool
[`finance_source_mapping_propose`](./commands#tool-finance_source_mapping_propose), Event
[`finance.source_mapping_changed`](./events#event-finance-source_mapping_changed)

#### `finance_source_mapping_propose` — Review source mapping {#tool-finance_source_mapping_propose}

Review an exact source-code mapping revision; requires owner confirmation and never alters evidence
or postings.

**Aufruf**

```text
finance_source_mapping_propose expected_revision source_system_id namespace field_kind source_code reference_id [state] reason
```

**Zugriff:** `propose`

Read or propose exact source-code classification with separate source and internal provenance.

**Verwenden, wenn**

- Create a defined cost center, case code or coding group.

**Nicht verwenden, wenn**

- Record money or determine tax treatment.

**Voraussetzungen**

- Owner confirmation and valid same-tenant reference kind.

**Abgelehnt, wenn**

- `invalid_reference` — Stale revision, duplicate code, invalid kind/state, foreign identity or
  missing reason.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |
| `source_system_id`  | `string`  | ja      | Opaque identity of the registered external source instance.                 | —        |
| `namespace`         | `string`  | ja      | —                                                                           | —        |
| `field_kind`        | `string`  | ja      | `case_code`, `coding_group`                                                 | —        |
| `source_code`       | `string`  | ja      | —                                                                           | —        |
| `reference_id`      | `string`  | ja      | Opaque same-tenant managed reference identity.                              | —        |
| `state`             | `string`  | nein    | Active or blocked eligibility for new account postings. `active`, `blocked` | `active` |
| `reason`            | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.     | —        |

**Prüfen mit:** `finance.references.history` — Immutable before/after decision and confirming
action.

**Siehe auch:** Geschäftsaktion [`set_source_mapping`](./commands#command-set_source_mapping)

### `update_account` — Update operational account {#command-update_account}

Uses shared tenant-scoped operational account configuration with explicit owner confirmation for
changes.

**Aufruf**

```text
finance_update_account_propose expected_revision account_id [code] [name] [state]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `subledger_account`, `finance_role_destination`, `finance_state` ·
Schreibt: `subledger_account`, `finance_role_destination`, `finance_state`, `business_event` ·
Erzeugt: `finance.account_changed`

**Siehe auch:** Agenten-Tool
[`finance_update_account_propose`](./commands#tool-finance_update_account_propose), Event
[`finance.account_changed`](./events#event-finance-account_changed)

#### `finance_update_account_propose` — Configure operational accounts {#tool-finance_update_account_propose}

Prepare an owner-confirmed operational account change; never execute it autonomously.

**Aufruf**

```text
finance_update_account_propose expected_revision account_id [code] [name] [state]
```

**Zugriff:** `propose`

Prepare an owner-confirmed operational account configuration change.

**Verwenden, wenn**

- Configure an allowed account or default.

**Nicht verwenden, wenn**

- Record money or determine tax treatment.

**Voraussetzungen**

- Owner confirmation, valid same-tenant role and account.

**Abgelehnt, wenn**

- `invalid_account_configuration` — Stale revision, duplicate code, wrong role or foreign account.

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |
| `account_id`        | `string`  | ja      | Opaque same-tenant operational account identity.                            | —        |
| `code`              | `string`  | nein    | Short tenant-scoped business code used to find the record operationally.    | `None`   |
| `name`              | `string`  | nein    | Human-readable display name; it is not used as internal identity.           | `None`   |
| `state`             | `string`  | nein    | Active or blocked eligibility for new account postings. `active`, `blocked` | `None`   |

**Prüfen mit:** `timeline` — The account change event and identity.

**Siehe auch:** Geschäftsaktion [`update_account`](./commands#command-update_account), Projection
[`timeline`](./views#projection-timeline)

## Aufträge & Erfüllung

### `announce_customer_return` — Announce customer return {#command-announce_customer_return}

Records that a customer says goods are coming back, bounded by what the delivery can still return.

**Aufruf**

```text
return_announce_propose commitment_id quantity [reference] [reason] [expected_by]
```

**Erreichbar über:** Web · API · MCP · Chat

**Wirkung:** Liest: `commitment`, `movement`, `return_announcement` · Schreibt:
`return_announcement`, `business_event` · Erzeugt: `return.announced`

**Siehe auch:** Agenten-Tool [`return_announce_propose`](./commands#tool-return_announce_propose),
Event [`return.announced`](./events#event-return-announced)

#### `return_announce_propose` — Announce customer return {#tool-return_announce_propose}

Prepare this business mutation without changing state. Announce customer return. Human confirmation
is required.

**Aufruf**

```text
return_announce_propose commitment_id quantity [reference] [reason] [expected_by]
```

**Zugriff:** `propose`

**Parameter**

| Name            | Typ      | Pflicht | Beschreibung                                                                                           | Standard |
| --------------- | -------- | ------- | ------------------------------------------------------------------------------------------------------ | -------- |
| `commitment_id` | `string` | ja      | Opaque identity of the obligation being reserved, held, or executed.                                   | —        |
| `quantity`      | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                | —        |
| `reference`     | `string` | nein    | The number the returning parcel will carry, as the customer or the company stated it; never generated. | —        |
| `reason`        | `string` | nein    | Human-readable explanation for a hold, correction, or lifecycle change.                                | —        |
| `expected_by`   | `string` | nein    | The day the customer says the goods will go back; absent means they did not say.                       | —        |

**Siehe auch:** Geschäftsaktion
[`announce_customer_return`](./commands#command-announce_customer_return)

### `cancel_commitment` — Cancel commitment remainder {#command-cancel_commitment}

Cancels only the open remainder for an explicit reason while retaining fulfilment history and
releasing active reservations and holds.

**Aufruf**

```text
commitment_cancel_propose commitment_id reason [source_record_id]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `commitment`, `reservation`, `commitment_hold`, `source_record` · Schreibt:
`commitment`, `reservation`, `commitment_hold`, `business_event` · Erzeugt: `commitment.cancelled`

**Siehe auch:** Agenten-Tool
[`commitment_cancel_propose`](./commands#tool-commitment_cancel_propose), Event
[`commitment.cancelled`](./events#event-commitment-cancelled)

#### `commitment_cancel_propose` — Cancel commitment remainder {#tool-commitment_cancel_propose}

Prepare this business mutation without changing state. Cancel commitment remainder. Human
confirmation is required.

**Aufruf**

```text
commitment_cancel_propose commitment_id reason [source_record_id]
```

**Zugriff:** `propose`

Cancel the complete open remainder of an existing commitment with an explicit business reason while
preserving evidence and physical history.

**Verwenden, wenn**

- A customer or supplier withdraws every remaining promised unit and active allocations or holds
  must be released.

**Nicht verwenden, wenn**

- Only quantity or due date changes and the commitment remains active; use commitment_revise_propose
  instead.
- Goods physically moved, were returned, or must be scrapped.

**Voraussetzungen**

- The commitment exists in the selected tenant and a non-empty business reason is supplied.

**Abgelehnt, wenn**

- `missing_reason` — Cancellation requires an explicit business reason.
- `commitment_closed` — A fully settled or already cancelled commitment has no open remainder to
  cancel.

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                 | Standard |
| ------------------ | -------- | ------- | ---------------------------------------------------------------------------- | -------- |
| `commitment_id`    | `string` | ja      | Opaque identity of the obligation being reserved, held, or executed.         | —        |
| `reason`           | `string` | ja      | Human-readable explanation for a hold, correction, or lifecycle change.      | —        |
| `source_record_id` | `string` | nein    | Opaque identity of the immutable source record supporting this typed record. | —        |

**Prüfen mit:** `commitment_register` — The commitment is cancelled and no open remainder remains.;
`inventory` — Released reservations no longer reduce available stock.

**Siehe auch:** Geschäftsaktion [`cancel_commitment`](./commands#command-cancel_commitment),
Projection [`commitment_register`](./views#projection-commitment_register), Projection
[`inventory`](./views#projection-inventory)

### `close_stale_promises` — Close stale promises {#command-close_stale_promises}

Closes the promises somebody previewed and counted, releasing their reservations and recording the
reason once.

**Aufruf**

```text
stale_closure_propose direction due_before expected_count reason
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `commitment`, `movement`, `reservation`, `commitment_hold`, `party_hold` ·
Schreibt: `commitment`, `reservation`, `business_event` · Erzeugt: `promises.closed`

**Siehe auch:** Agenten-Tool [`stale_closure_propose`](./commands#tool-stale_closure_propose), Event
[`promises.closed`](./events#event-promises-closed), Geschäftsaktion
[`cancel_commitment`](./commands#command-cancel_commitment)

#### `stale_closure_propose` — Close stale promises {#tool-stale_closure_propose}

Prepare this business mutation without changing state. Close stale promises. Human confirmation is
required.

**Aufruf**

```text
stale_closure_propose direction due_before expected_count reason
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ       | Pflicht | Beschreibung                                                                                  | Standard |
| ---------------- | --------- | ------- | --------------------------------------------------------------------------------------------- | -------- |
| `direction`      | `string`  | ja      | Business flow direction, such as sales or purchase, incoming or outgoing. `sales`, `purchase` | —        |
| `due_before`     | `string`  | ja      | Promises due strictly before this instant are considered; nothing later matches.              | —        |
| `expected_count` | `integer` | ja      | The number the caller saw in the preview; a closure is refused unless it still matches.       | —        |
| `reason`         | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                       | —        |

**Siehe auch:** Geschäftsaktion [`close_stale_promises`](./commands#command-close_stale_promises)

### `create_manual_order` — Create manual sales or purchase order {#command-create_manual_order}

Atomically records lossless manual Source evidence, typed order Evidence, and the derived outgoing
or incoming Commitments without storing operational status on the Document.

**Aufruf**

```text
order_create_propose direction number company_party_id counterparty_id location_id lines gross_amount [currency] [document_date] [ordered_at] [requested_delivery_at] [customer_reference] [sales_channel] [payment_term_code] [ship_to_party_id]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `party`, `item`, `location`, `payment_term` · Schreibt:
`source_stream`, `source_record`, `document`, `document_line`, `commitment`, `business_event` ·
Erzeugt: `order.recorded`

**Siehe auch:** Agenten-Tool [`order_create_propose`](./commands#tool-order_create_propose), Aktion
[`create_manual_order`](./views#action-create_manual_order), Event
[`order.recorded`](./events#event-order-recorded)

#### `order_create_propose` — Create order {#tool-order_create_propose}

Prepare this business mutation without changing state. Create order. Human confirmation is required.

**Aufruf**

```text
order_create_propose direction number company_party_id counterparty_id location_id lines gross_amount [currency] [document_date] [ordered_at] [requested_delivery_at] [customer_reference] [sales_channel] [payment_term_code] [ship_to_party_id]
```

**Zugriff:** `propose`

Record a manual order as Source and Document Evidence with derived Commitments.

**Verwenden, wenn**

- A human supplies a complete manual order whose parties
- items
- locations
- quantities
- and prices are known.

**Nicht verwenden, wenn**

- The source only reports stock allocation, physical execution, or payment.
- An existing order needs correction rather than a new source identity.

**Voraussetzungen**

- All referenced master data belongs to the selected tenant and lines form a complete intended
  order.

**Abgelehnt, wenn**

- `invalid_order_context` — Required party
- `duplicate_source_identity` — The proposed source identity conflicts with existing evidence.

**Parameter**

| Name                          | Typ      | Pflicht | Beschreibung                                                                                                                | Standard |
| ----------------------------- | -------- | ------- | --------------------------------------------------------------------------------------------------------------------------- | -------- |
| `direction`                   | `string` | ja      | Business flow direction, such as sales or purchase, incoming or outgoing. `sales`, `purchase`                               | —        |
| `number`                      | `string` | ja      | Human-facing document or transaction number; it is not internal identity.                                                   | —        |
| `company_party_id`            | `string` | ja      | Opaque identity of the tenant's company Party in an order flow.                                                             | —        |
| `counterparty_id`             | `string` | ja      | Opaque identity of the customer or supplier Party in an order flow.                                                         | —        |
| `location_id`                 | `string` | ja      | Opaque identity of the operational or physical location.                                                                    | —        |
| `lines`                       | `array`  | ja      | Complete intended normalized DocumentLine Evidence snapshot for an atomic manual correction.                                | —        |
| `lines[].item_id`             | `string` | ja      | Opaque identity of the operational item reference.                                                                          | —        |
| `lines[].quantity`            | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                     | —        |
| `lines[].unit`                | `string` | ja      | Unit of measure in which the quantity is expressed.                                                                         | —        |
| `lines[].unit_price`          | `string` | ja      | Decimal monetary amount for one unit before quantity multiplication.                                                        | —        |
| `lines[].gross_amount`        | `string` | ja      | Total the source states for the document; recorded as received and never calculated.                                        | —        |
| `lines[].description`         | `string` | nein    | Human-readable explanation of the record or rule.                                                                           | —        |
| `lines[].promised_at`         | `string` | nein    | UTC instant by which the line's quantity is promised; it becomes the due time of the derived Commitment.                    | —        |
| `lines[].line_type`           | `string` | nein    | Closed kind of a document line, such as goods or a charge, taken from the source statement.                                 | `item`   |
| `lines[].price_list_entry_id` | `string` | nein    | Opaque identity of the price tier the line price came from, when a list price was applied; provenance, not a recalculation. | —        |
| `gross_amount`                | `string` | ja      | Total the source states for the document; recorded as received and never calculated.                                        | —        |
| `currency`                    | `string` | nein    | ISO 4217 currency code for monetary values.                                                                                 | `EUR`    |
| `document_date`               | `string` | nein    | Business date printed on or asserted by the evidence document.                                                              | —        |
| `ordered_at`                  | `string` | nein    | UTC instant at which an order was placed in its source context.                                                             | —        |
| `requested_delivery_at`       | `string` | nein    | UTC instant by which the customer or operation requests delivery.                                                           | —        |
| `customer_reference`          | `string` | nein    | Reference supplied by the customer for matching and communication.                                                          | —        |
| `sales_channel`               | `string` | nein    | Operational sales-channel reference used for repeated routing or pricing decisions.                                         | —        |
| `payment_term_code`           | `string` | nein    | Tenant-scoped code of the payment condition to apply.                                                                       | —        |
| `ship_to_party_id`            | `string` | nein    | Opaque identity of the party receiving the physical delivery.                                                               | —        |

**Prüfen mit:** `document_register` — Document Evidence links to its immutable source.;
`commitment_register` — Promised quantities exist as Commitments rather than document status.

**Siehe auch:** Geschäftsaktion [`create_manual_order`](./commands#command-create_manual_order),
Projection [`commitment_register`](./views#projection-commitment_register), Projection
[`document_register`](./views#projection-document_register)

### `hold_commitment` — Hold commitment {#command-hold_commitment}

Prevents execution without changing or deleting the underlying obligation.

**Aufruf**

```text
commitment_hold_propose commitment_id reason_code [note]
commitment_hold_release_propose commitment_id
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `commitment`, `commitment_hold` · Schreibt: `commitment_hold` · Erzeugt:
`commitment.held`

**Siehe auch:** Agenten-Tool [`commitment_hold_propose`](./commands#tool-commitment_hold_propose),
Agenten-Tool [`commitment_hold_release_propose`](./commands#tool-commitment_hold_release_propose),
Aktion [`hold_commitment`](./views#action-hold_commitment), Event
[`commitment.held`](./events#event-commitment-held)

#### `commitment_hold_propose` — Hold commitment {#tool-commitment_hold_propose}

Prepare this business mutation without changing state. Hold commitment. Human confirmation is
required.

**Aufruf**

```text
commitment_hold_propose commitment_id reason_code [note]
```

**Zugriff:** `propose`

**Parameter**

| Name            | Typ      | Pflicht | Beschreibung                                                             | Standard |
| --------------- | -------- | ------- | ------------------------------------------------------------------------ | -------- |
| `commitment_id` | `string` | ja      | Opaque identity of the obligation being reserved, held, or executed.     | —        |
| `reason_code`   | `string` | ja      | Stable machine-readable reason used for filtering and automation.        | —        |
| `note`          | `string` | nein    | Free-text record of what the counterparty said, kept with the statement. | —        |

**Siehe auch:** Geschäftsaktion [`hold_commitment`](./commands#command-hold_commitment)

#### `commitment_hold_release_propose` — Release commitment hold {#tool-commitment_hold_release_propose}

Prepare this business mutation without changing state. Release commitment hold. Human confirmation
is required.

**Aufruf**

```text
commitment_hold_release_propose commitment_id
```

**Zugriff:** `propose`

**Parameter**

| Name            | Typ      | Pflicht | Beschreibung                                                         | Standard |
| --------------- | -------- | ------- | -------------------------------------------------------------------- | -------- |
| `commitment_id` | `string` | ja      | Opaque identity of the obligation being reserved, held, or executed. | —        |

**Siehe auch:** Geschäftsaktion [`hold_commitment`](./commands#command-hold_commitment)

### `hold_document_commitments` — Hold document commitments {#command-hold_document_commitments}

Places individual holds on the open commitments evidenced by a document.

**Aufruf**

```text
document_hold_propose document_id reason_code [note]
document_hold_release_propose document_id
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `document`, `commitment`, `commitment_hold` · Schreibt: `commitment_hold`

**Siehe auch:** Agenten-Tool [`document_hold_propose`](./commands#tool-document_hold_propose),
Agenten-Tool [`document_hold_release_propose`](./commands#tool-document_hold_release_propose),
Aktion [`hold_document_commitments`](./views#action-hold_document_commitments)

#### `document_hold_propose` — Hold document commitments {#tool-document_hold_propose}

Prepare this business mutation without changing state. Hold document commitments. Human confirmation
is required.

**Aufruf**

```text
document_hold_propose document_id reason_code [note]
```

**Zugriff:** `propose`

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung                                                             | Standard |
| ------------- | -------- | ------- | ------------------------------------------------------------------------ | -------- |
| `document_id` | `string` | ja      | Opaque identity of the evidence document to inspect or correct.          | —        |
| `reason_code` | `string` | ja      | Stable machine-readable reason used for filtering and automation.        | —        |
| `note`        | `string` | nein    | Free-text record of what the counterparty said, kept with the statement. | —        |

**Siehe auch:** Geschäftsaktion
[`hold_document_commitments`](./commands#command-hold_document_commitments)

#### `document_hold_release_propose` — Release document holds {#tool-document_hold_release_propose}

Prepare this business mutation without changing state. Release document holds. Human confirmation is
required.

**Aufruf**

```text
document_hold_release_propose document_id
```

**Zugriff:** `propose`

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung                                                    | Standard |
| ------------- | -------- | ------- | --------------------------------------------------------------- | -------- |
| `document_id` | `string` | ja      | Opaque identity of the evidence document to inspect or correct. | —        |

**Siehe auch:** Geschäftsaktion
[`hold_document_commitments`](./commands#command-hold_document_commitments)

### `preview_stale_promise_closure` — Preview stale promise closure {#command-preview_stale_promise_closure}

Shows how many stale promises match, what would be released, and a bounded sample, without changing
anything.

**Aufruf**

```text
stale_closure_preview direction due_before
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `commitment`, `movement`, `reservation`, `commitment_hold`, `party_hold` ·
Schreibt: —

**Siehe auch:** Agenten-Tool [`stale_closure_preview`](./commands#tool-stale_closure_preview)

#### `stale_closure_preview` — Preview a stale promise closure {#tool-stale_closure_preview}

Show how many promises an import left behind would close, and a sample of them, without changing
anything.

**Aufruf**

```text
stale_closure_preview direction due_before
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage            | Art                        | Standard |
| --------------------------- | -------------------------- | -------- |
| `MCP stale_closure_preview` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Show how many promises an import left behind a closure would close, and a sample of them, without
changing anything.

**Verwenden, wenn**

- An imported history has filled the queue with promises nobody is going to keep and somebody is
  deciding what to close.

**Nicht verwenden, wenn**

- A single promise is in question
- or the criteria have not been decided by a person.

**Parameter**

| Name         | Typ      | Pflicht | Beschreibung                                                                                  | Standard |
| ------------ | -------- | ------- | --------------------------------------------------------------------------------------------- | -------- |
| `direction`  | `string` | ja      | Business flow direction, such as sales or purchase, incoming or outgoing. `sales`, `purchase` | —        |
| `due_before` | `string` | ja      | Promises due strictly before this instant are considered; nothing later matches.              | —        |

**Siehe auch:** Geschäftsaktion
[`preview_stale_promise_closure`](./commands#command-preview_stale_promise_closure)

### `return_announcements` — Read announced returns {#command-return_announcements}

Lists the returns customers have announced, in the order they said so, with what is still expected.

**Aufruf**

```text
return_announcements [commitment_id] [status]
```

**Erreichbar über:** Web · API · MCP · Chat

**Wirkung:** Liest: `commitment`, `movement`, `return_announcement` · Schreibt: —

**Siehe auch:** Agenten-Tool [`return_announcements`](./commands#tool-return_announcements)

#### `return_announcements` — Read announced returns {#tool-return_announcements}

List the returns customers have announced, in the order they said so, with what each is still
waiting for. An announced return is not supply: nothing here makes the goods available.

**Aufruf**

```text
return_announcements [commitment_id] [status]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage           | Art                        | Standard |
| -------------------------- | -------------------------- | -------- |
| `MCP return_announcements` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

List the returns customers have announced, in the order they said so, with what each is still
waiting for.

**Verwenden, wenn**

- The receiving desk needs to know what parcels are expected
- or somebody is chasing a return a customer promised.

**Nicht verwenden, wenn**

- Goods have already arrived and what to do with them is the question; that is the return itself.

**Parameter**

| Name            | Typ      | Pflicht | Beschreibung                                                                                          | Standard |
| --------------- | -------- | ------- | ----------------------------------------------------------------------------------------------------- | -------- |
| `commitment_id` | `string` | nein    | Opaque identity of the obligation being reserved, held, or executed.                                  | —        |
| `status`        | `string` | nein    | Lifecycle state to filter by, such as open, fulfilled, or withdrawn. `open`, `fulfilled`, `withdrawn` | —        |

**Siehe auch:** Geschäftsaktion [`return_announcements`](./commands#command-return_announcements)

### `release_reservation` — Release reservation {#command-release_reservation}

Gives reserved stock back to whatever needs it next, without touching the promise that held it.

**Aufruf**

```text
reservation_release_propose reservation_id
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `reservation`, `commitment` · Schreibt: `reservation`, `business_event` ·
Erzeugt: `reservation.released`

**Siehe auch:** Agenten-Tool
[`reservation_release_propose`](./commands#tool-reservation_release_propose), Event
[`reservation.released`](./events#event-reservation-released)

#### `reservation_release_propose` — Release reservation {#tool-reservation_release_propose}

Prepare this business mutation without changing state. Release reservation. Human confirmation is
required.

**Aufruf**

```text
reservation_release_propose reservation_id
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ      | Pflicht | Beschreibung                                         | Standard |
| ---------------- | -------- | ------- | ---------------------------------------------------- | -------- |
| `reservation_id` | `string` | ja      | Opaque identity of the reservation being given back. | —        |

**Siehe auch:** Geschäftsaktion [`release_reservation`](./commands#command-release_reservation)

### `reserve` — Reserve stock {#command-reserve}

Allocates available stock to one commitment, optionally by pallet, lot, or exact serial unit, and
reports any shortage.

**Aufruf**

```text
reservation_propose commitment_id [quantity] [handling_unit_id] [lot_id] [serial_unit_id]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat · **Bestätigung:** `required for Chat`

**Wirkung:** Liest: `commitment`, `movement`, `reservation`, `item`, `location`, `handling_unit`,
`lot`, `serial_unit` · Schreibt: `reservation` · Erzeugt: `reservation.created`

**Siehe auch:** Agenten-Tool [`reservation_propose`](./commands#tool-reservation_propose), Aktion
[`reserve_stock`](./views#action-reserve_stock), Event
[`reservation.created`](./events#event-reservation-created)

#### `reservation_propose` — Propose reservation {#tool-reservation_propose}

Prepare a stock reservation without allocating before confirmation.

**Aufruf**

```text
reservation_propose commitment_id [quantity] [handling_unit_id] [lot_id] [serial_unit_id]
```

**Zugriff:** `propose`

Allocate currently available stock to an existing outgoing Commitment.

**Verwenden, wenn**

- An existing outgoing Commitment needs bounded stock allocation before fulfillment.

**Nicht verwenden, wenn**

- Goods have already physically moved.
- A source expresses only a preference or future promise.

**Voraussetzungen**

- The commitment is open and matching stock identity is available in the selected tenant.

**Abgelehnt, wenn**

- `insufficient_stock` — The requested allocation exceeds matching available stock.
- `commitment_closed` — The commitment no longer accepts allocation.

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                         | Standard |
| ------------------ | -------- | ------- | ------------------------------------------------------------------------------------ | -------- |
| `commitment_id`    | `string` | ja      | Opaque identity of the obligation being reserved, held, or executed.                 | —        |
| `quantity`         | `string` | nein    | Decimal quantity expressed in the item's relevant unit.                              | —        |
| `handling_unit_id` | `string` | nein    | Optional pallet or handling-unit identity, for example an NVE/SSCC-labelled pallet.  | —        |
| `lot_id`           | `string` | nein    | Exact batch or lot identity to reserve or move.                                      | —        |
| `serial_unit_id`   | `string` | nein    | Exact serial-unit identity to reserve or move; serialized quantities are always one. | —        |

**Prüfen mit:** `inventory` — Reserved quantity increases and available quantity decreases.;
`commitment_register` — Allocation links to the intended Commitment.

**Siehe auch:** Geschäftsaktion [`reserve`](./commands#command-reserve), Projection
[`commitment_register`](./views#projection-commitment_register), Projection
[`inventory`](./views#projection-inventory)

### `record_return_disposition` — Resolve arrived customer-return goods {#command-record_return_disposition}

Records one explicit physical outcome for part or all of an arrived customer return without implying
a credit.

**Aufruf**

```text
return_disposition_propose return_movement_id disposition quantity [destination_location_id] [reason]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `movement`, `movement_correction`, `source_record`, `location` · Schreibt:
`movement`, `source_record`, `business_event`

**Siehe auch:** Agenten-Tool
[`return_disposition_propose`](./commands#tool-return_disposition_propose)

#### `return_disposition_propose` — Resolve returned goods {#tool-return_disposition_propose}

Prepare this business mutation without changing state. Resolve returned goods. Human confirmation is
required.

**Aufruf**

```text
return_disposition_propose return_movement_id disposition quantity [destination_location_id] [reason]
```

**Zugriff:** `propose`

Resolve arrived customer-return goods through one of the four canonical physical outcomes without
changing credit evidence.

**Verwenden, wenn**

- A return Movement has arrived and a human has chosen restock
- quarantine_repair
- scrap_loss or return_to_supplier for an exact quantity.

**Nicht verwenden, wenn**

- A financial credit must be recorded; use the invoice-linked or legacy customer-credit action
  separately.

**Voraussetzungen**

- The return Movement retains its customer-delivery commitment
- arrival location and any handling-unit
- lot or serial identity.

**Abgelehnt, wenn**

- `invalid_return_relationship` — Return Movement

**Parameter**

| Name                      | Typ      | Pflicht | Beschreibung                                                                                                                                                                        | Standard |
| ------------------------- | -------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `return_movement_id`      | `string` | ja      | Opaque identity of the arrived customer-return Movement whose physical outcome is being decided.                                                                                    | —        |
| `disposition`             | `string` | ja      | Closed physical outcome for returned goods; restock, quarantine or repair, scrap or loss, or return to supplier. `restock`, `quarantine_repair`, `scrap_loss`, `return_to_supplier` | —        |
| `quantity`                | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                             | —        |
| `destination_location_id` | `string` | nein    | Opaque destination location required when returned goods are transferred to saleable stock or quarantine.                                                                           | —        |
| `reason`                  | `string` | nein    | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                                             | —        |

**Prüfen mit:** `return_disposition_summary` — Each resolving Movement preserves the arrived return
identity and reconciles the remaining quantity.; `inventory` — The resulting exact-location stock
effect is visible independently.

**Siehe auch:** Geschäftsaktion
[`record_return_disposition`](./commands#command-record_return_disposition), Projection
[`inventory`](./views#projection-inventory)

### `revise_commitment` — Revise commitment {#command-revise_commitment}

Records that a counterparty now states a different date, a different quantity, or both for a
promise, without erasing what it replaces.

**Aufruf**

```text
commitment_revise_propose commitment_id [due_at] [quantity] [note] [stated_at] [source_record_id] [retained_allocations]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `commitment`, `source_record` · Schreibt: `commitment_revision`,
`business_event` · Erzeugt: `commitment.revised`

**Siehe auch:** Agenten-Tool
[`commitment_revise_propose`](./commands#tool-commitment_revise_propose), Event
[`commitment.revised`](./events#event-commitment-revised)

#### `commitment_revise_propose` — Revise commitment {#tool-commitment_revise_propose}

Prepare this business mutation without changing state. Revise commitment. Human confirmation is
required.

**Aufruf**

```text
commitment_revise_propose commitment_id [due_at] [quantity] [note] [stated_at] [source_record_id] [retained_allocations]
```

**Zugriff:** `propose`

Revise the still-open quantity or due date of an existing commitment while preserving its evidence
and fulfillment history.

**Verwenden, wenn**

- A customer or supplier changes the remaining promised quantity or due date and the commitment must
  stay active.

**Nicht verwenden, wenn**

- The complete open remainder is cancelled; use commitment_cancel_propose instead.
- Goods physically moved or an order document must be rewritten.

**Voraussetzungen**

- The commitment exists in the selected tenant and the requested total is not below the quantity
  already fulfilled.
- When multiple active reservations exist, retained_allocations explicitly identifies the opaque
  reservation IDs and retained quantities.

**Abgelehnt, wenn**

- `invalid_revision` — The requested quantity conflicts with fulfillment already recorded or another
  current constraint.
- `allocation_selection_required` — Multiple reservations require an explicit retained allocation
  selection.

**Parameter**

| Name                                    | Typ      | Pflicht | Beschreibung                                                                                                                                     | Standard |
| --------------------------------------- | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| `commitment_id`                         | `string` | ja      | Opaque identity of the obligation being reserved, held, or executed.                                                                             | —        |
| `due_at`                                | `string` | nein    | The date the counterparty now states the promise is due on; optional if a quantity is stated.                                                    | —        |
| `quantity`                              | `string` | nein    | Decimal quantity expressed in the item's relevant unit.                                                                                          | —        |
| `note`                                  | `string` | nein    | Free-text record of what the counterparty said, kept with the statement.                                                                         | —        |
| `stated_at`                             | `string` | nein    | When the counterparty stated the new date, defaulting to now.                                                                                    | —        |
| `source_record_id`                      | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                     | —        |
| `retained_allocations`                  | `array`  | nein    | Exact active reservation identities and quantities the operator chooses to preserve when a reduced promise spans different physical allocations. | —        |
| `retained_allocations[].reservation_id` | `string` | ja      | Opaque identity of the reservation being given back.                                                                                             | —        |
| `retained_allocations[].quantity`       | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                          | —        |

**Prüfen mit:** `commitment_register` — The current open commitment reflects the reviewed revision.;
`inventory` — Only the reviewed reservation quantities remain allocated.

**Siehe auch:** Geschäftsaktion [`revise_commitment`](./commands#command-revise_commitment),
Projection [`commitment_register`](./views#projection-commitment_register), Projection
[`inventory`](./views#projection-inventory)

### `hold_party_delivery` — Set party delivery hold {#command-hold_party_delivery}

Blocks customer shipment execution while orders and reservations remain possible.

**Aufruf**

```text
party_delivery_hold_propose party_id reason_code [note]
party_delivery_hold_release_propose party_id
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `party`, `party_hold` · Schreibt: `party_hold` · Erzeugt:
`party.delivery_hold_placed`

**Siehe auch:** Agenten-Tool
[`party_delivery_hold_propose`](./commands#tool-party_delivery_hold_propose), Agenten-Tool
[`party_delivery_hold_release_propose`](./commands#tool-party_delivery_hold_release_propose), Aktion
[`party_delivery_hold`](./views#action-party_delivery_hold), Event
[`party.delivery_hold_placed`](./events#event-party-delivery_hold_placed)

#### `party_delivery_hold_propose` — Place party delivery hold {#tool-party_delivery_hold_propose}

Prepare this business mutation without changing state. Place party delivery hold. Human confirmation
is required.

**Aufruf**

```text
party_delivery_hold_propose party_id reason_code [note]
```

**Zugriff:** `propose`

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung                                                             | Standard |
| ------------- | -------- | ------- | ------------------------------------------------------------------------ | -------- |
| `party_id`    | `string` | ja      | Opaque identity of the customer, supplier, or other operational party.   | —        |
| `reason_code` | `string` | ja      | Stable machine-readable reason used for filtering and automation.        | —        |
| `note`        | `string` | nein    | Free-text record of what the counterparty said, kept with the statement. | —        |

**Siehe auch:** Geschäftsaktion [`hold_party_delivery`](./commands#command-hold_party_delivery)

#### `party_delivery_hold_release_propose` — Release party delivery hold {#tool-party_delivery_hold_release_propose}

Prepare this business mutation without changing state. Release party delivery hold. Human
confirmation is required.

**Aufruf**

```text
party_delivery_hold_release_propose party_id
```

**Zugriff:** `propose`

**Parameter**

| Name       | Typ      | Pflicht | Beschreibung                                                           | Standard |
| ---------- | -------- | ------- | ---------------------------------------------------------------------- | -------- |
| `party_id` | `string` | ja      | Opaque identity of the customer, supplier, or other operational party. | —        |

**Siehe auch:** Geschäftsaktion [`hold_party_delivery`](./commands#command-hold_party_delivery)

### `withdraw_return_announcement` — Withdraw return announcement {#command-withdraw_return_announcement}

Records that the customer is not sending the goods back after all, keeping what they announced.

**Aufruf**

```text
return_announcement_withdraw_propose announcement_id [note]
```

**Erreichbar über:** Web · API · MCP · Chat

**Wirkung:** Liest: `return_announcement` · Schreibt: `return_announcement`, `business_event` ·
Erzeugt: `return.announcement_withdrawn`

**Siehe auch:** Agenten-Tool
[`return_announcement_withdraw_propose`](./commands#tool-return_announcement_withdraw_propose),
Event [`return.announcement_withdrawn`](./events#event-return-announcement_withdrawn)

#### `return_announcement_withdraw_propose` — Withdraw return announcement {#tool-return_announcement_withdraw_propose}

Prepare this business mutation without changing state. Withdraw return announcement. Human
confirmation is required.

**Aufruf**

```text
return_announcement_withdraw_propose announcement_id [note]
```

**Zugriff:** `propose`

**Parameter**

| Name              | Typ      | Pflicht | Beschreibung                                                             | Standard |
| ----------------- | -------- | ------- | ------------------------------------------------------------------------ | -------- |
| `announcement_id` | `string` | ja      | Opaque identity of the announced customer return.                        | —        |
| `note`            | `string` | nein    | Free-text record of what the counterparty said, kept with the statement. | —        |

**Siehe auch:** Geschäftsaktion
[`withdraw_return_announcement`](./commands#command-withdraw_return_announcement)

## Lager & Logistik

### `correct_lot_expiry` — Correct lot expiry {#command-correct_lot_expiry}

Records that a stated best-before was read wrong and what it says instead, against a confirmed
current value and a stated reason.

**Aufruf**

```text
lot_expiry_correct_propose lot_id [expires_at] [expected_expires_at] reason
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `lot` · Schreibt: `lot`, `business_event` · Erzeugt: `lot.expiry_corrected`

**Siehe auch:** Agenten-Tool
[`lot_expiry_correct_propose`](./commands#tool-lot_expiry_correct_propose), Event
[`lot.expiry_corrected`](./events#event-lot-expiry_corrected)

#### `lot_expiry_correct_propose` — Correct lot expiry {#tool-lot_expiry_correct_propose}

Prepare this business mutation without changing state. Correct lot expiry. Human confirmation is
required.

**Aufruf**

```text
lot_expiry_correct_propose lot_id [expires_at] [expected_expires_at] reason
```

**Zugriff:** `propose`

**Parameter**

| Name                  | Typ      | Pflicht | Beschreibung                                                                                                                                                                            | Standard |
| --------------------- | -------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `lot_id`              | `string` | ja      | Exact batch or lot identity to reserve or move.                                                                                                                                         | —        |
| `expires_at`          | `string` | nein    | The best-before date somebody read off the goods or the delivery note, as a calendar day; never computed from a shelf life, and never adjusted once stated.                             | —        |
| `expected_expires_at` | `string` | nein    | The best-before date the caller believes is stated now, or absent to say none is; a correction is refused unless it still matches, so it cannot be made by somebody who has not looked. | —        |
| `reason`              | `string` | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                                                 | —        |

**Siehe auch:** Geschäftsaktion [`correct_lot_expiry`](./commands#command-correct_lot_expiry)

### `correct_movement` — Correct movement {#command-correct_movement}

Preserves an immutable original, appends one exact correction and optional replacement, and derives
the auditable net physical effect.

**Aufruf**

```text
movement_correction_propose movement_id reason [replacement]
```

**Erreichbar über:** CLI · Web · API · Chat · MCP · **Bestätigung:** `required`

**Wirkung:** Liest: `movement`, `movement_correction`, `item`, `location`, `commitment`,
`handling_unit`, `lot`, `serial_unit`, `source_record` · Schreibt: `movement`,
`movement_correction`, `commitment`, `business_event` · Erzeugt: `movement.corrected`

**Siehe auch:** Agenten-Tool
[`movement_correction_propose`](./commands#tool-movement_correction_propose), Aktion
[`correct_movement`](./views#action-correct_movement), Event
[`movement.corrected`](./events#event-movement-corrected)

#### `movement_correction_propose` — Propose Movement correction {#tool-movement_correction_propose}

Preview an exact compensating Movement and optional replacement without executing before a separate
decision.

**Aufruf**

```text
movement_correction_propose movement_id reason [replacement]
```

**Zugriff:** `propose`

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung                                                                     | Standard |
| ------------- | -------- | ------- | -------------------------------------------------------------------------------- | -------- |
| `movement_id` | `string` | ja      | Opaque identity of the immutable physical Movement being inspected or corrected. | —        |
| `reason`      | `string` | ja      | Human-readable explanation for a hold, correction, or lifecycle change.          | —        |
| `replacement` | `object` | nein    | Optional complete intended Movement that replaces the compensated original.      | —        |

**Siehe auch:** Geschäftsaktion [`correct_movement`](./commands#command-correct_movement)

### `create_handling_unit` — Create handling unit {#command-create_handling_unit}

Records an optional tenant-scoped pallet identity with an optional NVE/SSCC and immutable source
evidence.

**Aufruf**

```text
handling_unit_create_propose [nve] [source_record_id]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `source_record`, `handling_unit` · Schreibt: `handling_unit`,
`business_event` · Erzeugt: `handling_unit.created`

**Siehe auch:** Agenten-Tool
[`handling_unit_create_propose`](./commands#tool-handling_unit_create_propose), Aktion
[`create_handling_unit`](./views#action-create_handling_unit), Event
[`handling_unit.created`](./events#event-handling_unit-created)

#### `handling_unit_create_propose` — Create handling unit {#tool-handling_unit_create_propose}

Prepare this business mutation without changing state. Create handling unit. Human confirmation is
required.

**Aufruf**

```text
handling_unit_create_propose [nve] [source_record_id]
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                    | Standard |
| ------------------ | -------- | ------- | ------------------------------------------------------------------------------- | -------- |
| `nve`              | `string` | nein    | Optional Nummer der Versandeinheit / SSCC printed on a pallet or handling unit. | —        |
| `source_record_id` | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.    | —        |

**Siehe auch:** Geschäftsaktion [`create_handling_unit`](./commands#command-create_handling_unit)

### `create_lot` — Create lot {#command-create_lot}

Creates a tenant-scoped batch identity for a lot- or serial-tracked item without storing a stock
balance.

**Aufruf**

```text
lot_create_propose item_id lot_number [expires_at] [source_record_id]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `item`, `source_record`, `lot` · Schreibt: `lot`, `business_event` ·
Erzeugt: `lot.created`

**Siehe auch:** Agenten-Tool [`lot_create_propose`](./commands#tool-lot_create_propose), Aktion
[`create_lot`](./views#action-create_lot), Event [`lot.created`](./events#event-lot-created)

#### `lot_create_propose` — Create lot {#tool-lot_create_propose}

Prepare this business mutation without changing state. Create lot. Human confirmation is required.

**Aufruf**

```text
lot_create_propose item_id lot_number [expires_at] [source_record_id]
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                                                                                                | Standard |
| ------------------ | -------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `item_id`          | `string` | ja      | Opaque identity of the operational item reference.                                                                                                          | —        |
| `lot_number`       | `string` | ja      | Human-readable batch number supplied by production or an external system.                                                                                   | —        |
| `expires_at`       | `string` | nein    | The best-before date somebody read off the goods or the delivery note, as a calendar day; never computed from a shelf life, and never adjusted once stated. | —        |
| `source_record_id` | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                                | —        |

**Siehe auch:** Geschäftsaktion [`create_lot`](./commands#command-create_lot)

### `create_serial_unit` — Create serial unit {#command-create_serial_unit}

Creates the identity of one serialized unit, optionally linked to its lot, without storing its
location or status.

**Aufruf**

```text
serial_unit_create_propose item_id serial_number [lot_id] [source_record_id]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `item`, `lot`, `source_record`, `serial_unit` · Schreibt:
`serial_unit`, `business_event` · Erzeugt: `serial_unit.created`

**Siehe auch:** Agenten-Tool
[`serial_unit_create_propose`](./commands#tool-serial_unit_create_propose), Aktion
[`create_serial_unit`](./views#action-create_serial_unit), Event
[`serial_unit.created`](./events#event-serial_unit-created)

#### `serial_unit_create_propose` — Create serial unit {#tool-serial_unit_create_propose}

Prepare this business mutation without changing state. Create serial unit. Human confirmation is
required.

**Aufruf**

```text
serial_unit_create_propose item_id serial_number [lot_id] [source_record_id]
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                 | Standard |
| ------------------ | -------- | ------- | ---------------------------------------------------------------------------- | -------- |
| `item_id`          | `string` | ja      | Opaque identity of the operational item reference.                           | —        |
| `serial_number`    | `string` | ja      | Human-readable unique serial identifier carried by one physical unit.        | —        |
| `lot_id`           | `string` | nein    | Exact batch or lot identity to reserve or move.                              | —        |
| `source_record_id` | `string` | nein    | Opaque identity of the immutable source record supporting this typed record. | —        |

**Siehe auch:** Geschäftsaktion [`create_serial_unit`](./commands#command-create_serial_unit)

### `record_packaged_execution` — Dispatch or receive shipment package {#command-record_packaged_execution}

Atomically records one physical package and its exact existing Movement effects.

**Aufruf**

```text
shipment_dispatch_propose purpose counterparty_id movements [carrier] [tracking_number] [source_record_id] [occurred_at]
shipment_receive_propose purpose counterparty_id movements [carrier] [tracking_number] [source_record_id] [occurred_at]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `party`, `party_role`, `commitment`, `return_announcement`, `item`, `location`,
`reservation`, `movement` · Schreibt: `shipment`, `shipment_package`, `shipment_event`, `movement`,
`reservation`, `business_event`

**Siehe auch:** Agenten-Tool
[`shipment_dispatch_propose`](./commands#tool-shipment_dispatch_propose), Agenten-Tool
[`shipment_receive_propose`](./commands#tool-shipment_receive_propose), Geschäftsaktion
[`record_movement`](./commands#command-record_movement)

#### `shipment_dispatch_propose` — Propose package dispatch {#tool-shipment_dispatch_propose}

Prepare one outgoing package and its exact physical Movements; execution requires explicit
confirmation.

**Aufruf**

```text
shipment_dispatch_propose purpose counterparty_id movements [carrier] [tracking_number] [source_record_id] [occurred_at]
```

**Zugriff:** `propose`

**Parameter**

| Name                           | Typ      | Pflicht | Beschreibung                                                                                                                                                      | Standard |
| ------------------------------ | -------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `purpose`                      | `string` | ja      | Closed business purpose that determines the shipment's counterparty role and compatible Movement type.                                                            | —        |
| `counterparty_id`              | `string` | ja      | Opaque identity of the customer or supplier Party in an order flow.                                                                                               | —        |
| `movements`                    | `array`  | ja      | Exact existing Movement command inputs to record atomically as the physical contents of one Package.                                                              | —        |
| `movements[].movement_type`    | `string` | nein    | Physical event kind — opening_stock, receipt, shipment, transfer, adjustment, return (goods back from a customer), or supplier_return (goods back to a supplier). | —        |
| `movements[].item_id`          | `string` | ja      | Opaque identity of the operational item reference.                                                                                                                | —        |
| `movements[].quantity`         | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                           | —        |
| `movements[].from_location_id` | `string` | nein    | Opaque identity of the location from which physical stock leaves.                                                                                                 | —        |
| `movements[].to_location_id`   | `string` | nein    | Opaque identity of the location into which physical stock arrives.                                                                                                | —        |
| `movements[].commitment_id`    | `string` | nein    | Opaque identity of the obligation being reserved, held, or executed.                                                                                              | —        |
| `movements[].handling_unit_id` | `string` | nein    | Optional pallet or handling-unit identity, for example an NVE/SSCC-labelled pallet.                                                                               | —        |
| `movements[].lot_id`           | `string` | nein    | Exact batch or lot identity to reserve or move.                                                                                                                   | —        |
| `movements[].serial_unit_id`   | `string` | nein    | Exact serial-unit identity to reserve or move; serialized quantities are always one.                                                                              | —        |
| `movements[].reason`           | `string` | nein    | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                           | —        |
| `carrier`                      | `string` | nein    | Carrier name stated for a physical package; it is descriptive and not an internal identity.                                                                       | —        |
| `tracking_number`              | `string` | nein    | Carrier-assigned package reference used for operational lookup; it is not internal identity.                                                                      | —        |
| `source_record_id`             | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                                      | —        |
| `occurred_at`                  | `string` | nein    | UTC instant at which the physical or business event occurred.                                                                                                     | —        |

**Siehe auch:** Geschäftsaktion
[`record_packaged_execution`](./commands#command-record_packaged_execution)

#### `shipment_receive_propose` — Propose package receipt {#tool-shipment_receive_propose}

Prepare one incoming package and its exact physical Movements; execution requires explicit
confirmation.

**Aufruf**

```text
shipment_receive_propose purpose counterparty_id movements [carrier] [tracking_number] [source_record_id] [occurred_at]
```

**Zugriff:** `propose`

**Parameter**

| Name                           | Typ      | Pflicht | Beschreibung                                                                                                                                                      | Standard |
| ------------------------------ | -------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `purpose`                      | `string` | ja      | Closed business purpose that determines the shipment's counterparty role and compatible Movement type.                                                            | —        |
| `counterparty_id`              | `string` | ja      | Opaque identity of the customer or supplier Party in an order flow.                                                                                               | —        |
| `movements`                    | `array`  | ja      | Exact existing Movement command inputs to record atomically as the physical contents of one Package.                                                              | —        |
| `movements[].movement_type`    | `string` | nein    | Physical event kind — opening_stock, receipt, shipment, transfer, adjustment, return (goods back from a customer), or supplier_return (goods back to a supplier). | —        |
| `movements[].item_id`          | `string` | ja      | Opaque identity of the operational item reference.                                                                                                                | —        |
| `movements[].quantity`         | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                           | —        |
| `movements[].from_location_id` | `string` | nein    | Opaque identity of the location from which physical stock leaves.                                                                                                 | —        |
| `movements[].to_location_id`   | `string` | nein    | Opaque identity of the location into which physical stock arrives.                                                                                                | —        |
| `movements[].commitment_id`    | `string` | nein    | Opaque identity of the obligation being reserved, held, or executed.                                                                                              | —        |
| `movements[].handling_unit_id` | `string` | nein    | Optional pallet or handling-unit identity, for example an NVE/SSCC-labelled pallet.                                                                               | —        |
| `movements[].lot_id`           | `string` | nein    | Exact batch or lot identity to reserve or move.                                                                                                                   | —        |
| `movements[].serial_unit_id`   | `string` | nein    | Exact serial-unit identity to reserve or move; serialized quantities are always one.                                                                              | —        |
| `movements[].reason`           | `string` | nein    | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                           | —        |
| `carrier`                      | `string` | nein    | Carrier name stated for a physical package; it is descriptive and not an internal identity.                                                                       | —        |
| `tracking_number`              | `string` | nein    | Carrier-assigned package reference used for operational lookup; it is not internal identity.                                                                      | —        |
| `source_record_id`             | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                                      | —        |
| `occurred_at`                  | `string` | nein    | UTC instant at which the physical or business event occurred.                                                                                                     | —        |

**Siehe auch:** Geschäftsaktion
[`record_packaged_execution`](./commands#command-record_packaged_execution)

### `expired_lots` — Read expired lots {#command-expired_lots}

Lists lots whose stated best-before has passed, oldest first; a lot with no stated date is absent in
both directions.

**Aufruf**

```text
expired_lots
```

**Erreichbar über:** Web · API · MCP · Chat

**Wirkung:** Liest: `lot` · Schreibt: —

**Siehe auch:** Agenten-Tool [`expired_lots`](./commands#tool-expired_lots)

#### `expired_lots` — Read expired lots {#tool-expired_lots}

List the batches whose stated best-before date has passed, oldest first. A lot with no stated date
is absent in both directions. There is deliberately no way to ask what is about to expire: no
horizon is stated anywhere and Reality does not invent one.

**Aufruf**

```text
expired_lots
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage   | Art                        | Standard |
| ------------------ | -------------------------- | -------- |
| `MCP expired_lots` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

List the batches whose stated best-before date has passed, oldest first.

**Verwenden, wenn**

- Somebody is deciding what to write off
- send back
- or stop shipping
- or is checking what expired stock the company still holds.

**Nicht verwenden, wenn**

- The question is what is about to expire; nothing states a horizon
- so nothing here answers it.

**Parameter**

Keine Parameter.

**Siehe auch:** Geschäftsaktion [`expired_lots`](./commands#command-expired_lots)

### `inventory_cost` — Read reviewed inventory acquisition costs {#command-inventory_cost}

Derive stock acquisition value and consumption from a bounded confirmed ownership/policy scope, and
derive a separate carrying value only from an exact source-backed retained assessment.

**Aufruf**

```text
cost_inventory_get item_id [review_id] [assessment_revision_id]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `item`, `business_event`, `source_record`, `cost_policy_revision`,
`cost_movement_basis`, `cost_ownership_revision`, `cost_inventory_review`, `cost_inventory_member`,
`cost_valuation_assessment_revision`, `cost_valuation_assessment_part`,
`cost_conversion_basis_revision`, `cost_receipt_basis`, `cost_input_manifest`,
`cost_attribution_revision`, `cost_attribution_part`, `cost_scope_review` · Schreibt: —

**Siehe auch:** Agenten-Tool [`cost_inventory_get`](./commands#tool-cost_inventory_get)

#### `cost_inventory_get` — Reviewed inventory acquisition value {#tool-cost_inventory_get}

Read bounded confirmed stock and consumption at a retained cutoff; carrying value is unavailable.

**Aufruf**

```text
cost_inventory_get item_id [review_id] [assessment_revision_id]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage         | Art                        | Standard |
| ------------------------ | -------------------------- | -------- |
| `MCP cost_inventory_get` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read stock acquisition value and economic consumption at an explicitly confirmed bounded cutoff.

**Verwenden, wenn**

- Explain a confirmed inventory review and its original receipt costs.

**Nicht verwenden, wenn**

- Request HGB carrying value, DB margins or unreviewed live whole-company inventory.

**Parameter**

| Name                     | Typ      | Pflicht | Beschreibung                                                                                                                                                             | Standard |
| ------------------------ | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| `item_id`                | `string` | ja      | Opaque identity of the operational item reference.                                                                                                                       | —        |
| `review_id`              | `string` | nein    | Exact retained inventory or contribution review identity for the selected tool; absence selects its latest review.                                                       | `None`   |
| `assessment_revision_id` | `string` | nein    | Optional exact retained carrying-value assessment identity paired with the selected inventory review; absence selects the latest verified assessment for a current read. | `None`   |

**Siehe auch:** Geschäftsaktion [`inventory_cost`](./commands#command-inventory_cost)

### `record_movement` — Record movement {#command-record_movement}

Records an immutable physical event with the same optional pallet, lot, and serial identity used by
reservations.

**Aufruf**

```text
movement_create_propose movement_type item_id quantity [from_location_id] [to_location_id] [commitment_id] [source_record_id] [handling_unit_id] [lot_id] [serial_unit_id] [occurred_at] [reason] [resolves_movement_id] [return_announcement_id] [opening_cost]
```

**Erreichbar über:** CLI · Web · API · scenario · MCP · Chat

**Wirkung:** Liest: `item`, `location`, `commitment`, `handling_unit`, `lot`, `serial_unit` ·
Schreibt: `movement`, `reservation`, `commitment`, `action`, `business_event` · Erzeugt:
`commitment.fulfilled`, `reservation.consumed`, `movement.recorded`

**Siehe auch:** Agenten-Tool [`movement_create_propose`](./commands#tool-movement_create_propose),
Aktion [`record_movement`](./views#action-record_movement), Event
[`commitment.fulfilled`](./events#event-commitment-fulfilled), Event
[`reservation.consumed`](./events#event-reservation-consumed), Event
[`movement.recorded`](./events#event-movement-recorded)

#### `movement_create_propose` — Record Movement {#tool-movement_create_propose}

Prepare this business mutation without changing state. Record Movement. Human confirmation is
required.

**Aufruf**

```text
movement_create_propose movement_type item_id quantity [from_location_id] [to_location_id] [commitment_id] [source_record_id] [handling_unit_id] [lot_id] [serial_unit_id] [occurred_at] [reason] [resolves_movement_id] [return_announcement_id] [opening_cost]
```

**Zugriff:** `propose`

Record an immutable physical receipt, transfer, shipment, return, or adjustment.

**Verwenden, wenn**

- A physical stock event occurred with known item
- quantity
- time
- and applicable locations.

**Nicht verwenden, wenn**

- The source expresses only a promise, planned allocation, preference, or prediction.
- An existing Movement is wrong and requires a compensating correction.

**Voraussetzungen**

- Item and locations belong to the selected tenant and the movement type has a valid physical
  direction.

**Abgelehnt, wenn**

- `invalid_physical_direction` — Movement type and source or destination locations are inconsistent.
- `invalid_tracking_identity` — Tracking identity does not satisfy item rules.

**Parameter**

| Name                              | Typ      | Pflicht | Beschreibung                                                                                                                                                                                                                                                    | Standard |
| --------------------------------- | -------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `movement_type`                   | `string` | ja      | Physical event kind — opening_stock, receipt, shipment, transfer, adjustment, return (goods back from a customer), or supplier_return (goods back to a supplier). `opening_stock`, `receipt`, `shipment`, `transfer`, `return`, `supplier_return`, `adjustment` | —        |
| `item_id`                         | `string` | ja      | Opaque identity of the operational item reference.                                                                                                                                                                                                              | —        |
| `quantity`                        | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                                                                                                         | —        |
| `from_location_id`                | `string` | nein    | Opaque identity of the location from which physical stock leaves.                                                                                                                                                                                               | —        |
| `to_location_id`                  | `string` | nein    | Opaque identity of the location into which physical stock arrives.                                                                                                                                                                                              | —        |
| `commitment_id`                   | `string` | nein    | Opaque identity of the obligation being reserved, held, or executed.                                                                                                                                                                                            | —        |
| `source_record_id`                | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                                                                                                                                    | —        |
| `handling_unit_id`                | `string` | nein    | Optional pallet or handling-unit identity, for example an NVE/SSCC-labelled pallet.                                                                                                                                                                             | —        |
| `lot_id`                          | `string` | nein    | Exact batch or lot identity to reserve or move.                                                                                                                                                                                                                 | —        |
| `serial_unit_id`                  | `string` | nein    | Exact serial-unit identity to reserve or move; serialized quantities are always one.                                                                                                                                                                            | —        |
| `occurred_at`                     | `string` | nein    | UTC instant at which the physical or business event occurred.                                                                                                                                                                                                   | —        |
| `reason`                          | `string` | nein    | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                                                                                                                         | —        |
| `resolves_movement_id`            | `string` | nein    | Opaque identity of the return this movement settles; absent means it settles none.                                                                                                                                                                              | —        |
| `return_announcement_id`          | `string` | nein    | Opaque identity of the announced return these goods fulfil; absent means they were not announced.                                                                                                                                                               | —        |
| `opening_cost`                    | `object` | nein    | Opening stock only: the total acquisition value its evidence states, recorded as received for the cost review (spec 282).                                                                                                                                       | —        |
| `opening_cost.amount`             | `string` | ja      | Total acquisition value exactly as the evidence states it; never a computed unit cost.                                                                                                                                                                          | —        |
| `opening_cost.currency`           | `string` | ja      | Three-letter currency code of the stated value.                                                                                                                                                                                                                 | —        |
| `opening_cost.evidence_reference` | `string` | ja      | Names the document the value comes from, for example an inventory list.                                                                                                                                                                                         | —        |

**Prüfen mit:** `inventory` — Physical stock reflects the immutable Movement.; `commitment_register`
— Fulfillment derives from Movements linked to the Commitment.; `timeline` — The physical event is
visible with its opaque identity.

**Siehe auch:** Geschäftsaktion [`record_movement`](./commands#command-record_movement), Projection
[`commitment_register`](./views#projection-commitment_register), Projection
[`inventory`](./views#projection-inventory), Projection [`timeline`](./views#projection-timeline)

### `record_shipment_event` — Record shipment event {#command-record_shipment_event}

Appends one attributed logistics observation without changing stock.

**Aufruf**

```text
shipment_event_record_propose shipment_id [shipment_package_id] event_type reporter_type [occurred_at] [location_text] [source_record_id] [external_event_id]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `shipment`, `shipment_package`, `source_record` · Schreibt: `shipment_event`,
`business_event` · Erzeugt: `shipment.event_recorded`

**Siehe auch:** Agenten-Tool
[`shipment_event_record_propose`](./commands#tool-shipment_event_record_propose), Event
[`shipment.event_recorded`](./events#event-shipment-event_recorded)

#### `shipment_event_record_propose` — Propose shipment event {#tool-shipment_event_record_propose}

Prepare one attributed logistics observation; execution requires explicit confirmation.

**Aufruf**

```text
shipment_event_record_propose shipment_id [shipment_package_id] event_type reporter_type [occurred_at] [location_text] [source_record_id] [external_event_id]
```

**Zugriff:** `propose`

**Parameter**

| Name                  | Typ      | Pflicht | Beschreibung                                                                                                                                                | Standard |
| --------------------- | -------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `shipment_id`         | `string` | ja      | Opaque identity of the tenant-scoped physical consignment.                                                                                                  | —        |
| `shipment_package_id` | `string` | nein    | Opaque identity of the physical shipment package that carried this exact movement quantity; absent means no package was recorded.                           | —        |
| `event_type`          | `string` | ja      | Closed logistics observation kind stated for a Shipment or Package. `announced`, `handed_over`, `in_transit`, `delivered`, `delivery_exception`, `received` | —        |
| `reporter_type`       | `string` | ja      | Closed attribution for who stated a shipment observation, such as company, counterparty, or carrier. `company`, `counterparty`, `carrier`, `integration`    | —        |
| `occurred_at`         | `string` | nein    | UTC instant at which the physical or business event occurred.                                                                                               | —        |
| `location_text`       | `string` | nein    | Optional location text exactly as reported with a logistics observation.                                                                                    | —        |
| `source_record_id`    | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                                | —        |
| `external_event_id`   | `string` | nein    | Optional source-assigned event identity used to make repeated intake idempotent.                                                                            | —        |

**Siehe auch:** Geschäftsaktion [`record_shipment_event`](./commands#command-record_shipment_event)

### `record_shipment_notice` — Record shipment notice {#command-record_shipment_notice}

Records a stated consignment and package without moving stock.

**Aufruf**

```text
shipment_notice_record_propose direction purpose counterparty_id [carrier] [tracking_number] [source_record_id] [occurred_at] [reporter_type]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `party`, `party_role`, `source_record` · Schreibt: `shipment`,
`shipment_package`, `shipment_event`, `business_event` · Erzeugt: `shipment.notice_recorded`

**Siehe auch:** Agenten-Tool
[`shipment_notice_record_propose`](./commands#tool-shipment_notice_record_propose), Event
[`shipment.notice_recorded`](./events#event-shipment-notice_recorded)

#### `shipment_notice_record_propose` — Propose shipment notice {#tool-shipment_notice_record_propose}

Prepare a shipment/package notice without moving stock; execution requires explicit confirmation.

**Aufruf**

```text
shipment_notice_record_propose direction purpose counterparty_id [carrier] [tracking_number] [source_record_id] [occurred_at] [reporter_type]
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                                                                                                                          | Standard       |
| ------------------ | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `direction`        | `string` | ja      | Business flow direction, such as sales or purchase, incoming or outgoing. `inbound`, `outbound`                                                                                       | —              |
| `purpose`          | `string` | ja      | Closed business purpose that determines the shipment's counterparty role and compatible Movement type. `customer_delivery`, `supplier_delivery`, `customer_return`, `supplier_return` | —              |
| `counterparty_id`  | `string` | ja      | Opaque identity of the customer or supplier Party in an order flow.                                                                                                                   | —              |
| `carrier`          | `string` | nein    | Carrier name stated for a physical package; it is descriptive and not an internal identity.                                                                                           | —              |
| `tracking_number`  | `string` | nein    | Carrier-assigned package reference used for operational lookup; it is not internal identity.                                                                                          | —              |
| `source_record_id` | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.                                                                                                          | —              |
| `occurred_at`      | `string` | nein    | UTC instant at which the physical or business event occurred.                                                                                                                         | —              |
| `reporter_type`    | `string` | nein    | Closed attribution for who stated a shipment observation, such as company, counterparty, or carrier. `company`, `counterparty`, `carrier`, `integration`                              | `counterparty` |

**Siehe auch:** Geschäftsaktion
[`record_shipment_notice`](./commands#command-record_shipment_notice)

### `state_lot_expiry` — State lot expiry {#command-state_lot_expiry}

Records the best-before date somebody read off the goods; refuses a different date, because a
received value is not adjusted.

**Aufruf**

```text
lot_expiry_state_propose lot_id expires_at
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `lot` · Schreibt: `lot`, `business_event` · Erzeugt: `lot.expiry_stated`

**Siehe auch:** Agenten-Tool [`lot_expiry_state_propose`](./commands#tool-lot_expiry_state_propose),
Event [`lot.expiry_stated`](./events#event-lot-expiry_stated)

#### `lot_expiry_state_propose` — State lot expiry {#tool-lot_expiry_state_propose}

Prepare this business mutation without changing state. State lot expiry. Human confirmation is
required.

**Aufruf**

```text
lot_expiry_state_propose lot_id expires_at
```

**Zugriff:** `propose`

**Parameter**

| Name         | Typ      | Pflicht | Beschreibung                                                                                                                                                | Standard |
| ------------ | -------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `lot_id`     | `string` | ja      | Exact batch or lot identity to reserve or move.                                                                                                             | —        |
| `expires_at` | `string` | ja      | The best-before date somebody read off the goods or the delivery note, as a calendar day; never computed from a shelf life, and never adjusted once stated. | —        |

**Siehe auch:** Geschäftsaktion [`state_lot_expiry`](./commands#command-state_lot_expiry)

### `supersede_shipment_event` — Supersede shipment event {#command-supersede_shipment_event}

Appends a reasoned correction or retraction without deleting the original event.

**Aufruf**

```text
shipment_event_supersede_propose event_id reason [replacement_event_id] [source_record_id]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `shipment_event`, `source_record` · Schreibt: `shipment_event_supersession`,
`business_event` · Erzeugt: `shipment.event_superseded`

**Siehe auch:** Agenten-Tool
[`shipment_event_supersede_propose`](./commands#tool-shipment_event_supersede_propose), Event
[`shipment.event_superseded`](./events#event-shipment-event_superseded)

#### `shipment_event_supersede_propose` — Propose shipment event correction {#tool-shipment_event_supersede_propose}

Prepare an append-only correction or retraction; execution requires explicit confirmation.

**Aufruf**

```text
shipment_event_supersede_propose event_id reason [replacement_event_id] [source_record_id]
```

**Zugriff:** `propose`

**Parameter**

| Name                   | Typ      | Pflicht | Beschreibung                                                                               | Standard |
| ---------------------- | -------- | ------- | ------------------------------------------------------------------------------------------ | -------- |
| `event_id`             | `string` | ja      | Opaque identity of the immutable ShipmentEvent being corrected.                            | —        |
| `reason`               | `string` | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                    | —        |
| `replacement_event_id` | `string` | nein    | Optional opaque identity of another ShipmentEvent that replaces the corrected observation. | —        |
| `source_record_id`     | `string` | nein    | Opaque identity of the immutable source record supporting this typed record.               | —        |

**Siehe auch:** Geschäftsaktion
[`supersede_shipment_event`](./commands#command-supersede_shipment_event)

## Belege, Quellen & Facts

### `correct_manual_document` — Correct manual document evidence {#command-correct_manual_document}

Corrects typed internal header or complete line evidence snapshots while protecting economic fields
after Reality records have been derived.

**Aufruf**

```text
document_correct_propose document_id document_type number party_id amount [currency] [document_date] [ordered_at] [requested_delivery_at] [customer_reference] [sales_channel] [payment_term_code] [ship_to_party_id]
document_lines_correct_propose document_id expected_revision lines [actor_context]
```

**Erreichbar über:** Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `document`, `document_line`, `commitment`, `ledger_entry`, `party`,
`item`, `payment_term` · Schreibt: `document`, `document_line`, `business_event` · Erzeugt:
`document.corrected`

**Siehe auch:** Agenten-Tool [`document_correct_propose`](./commands#tool-document_correct_propose),
Agenten-Tool [`document_lines_correct_propose`](./commands#tool-document_lines_correct_propose),
Event [`document.corrected`](./events#event-document-corrected)

#### `document_correct_propose` — Correct manual document {#tool-document_correct_propose}

Prepare this business mutation without changing state. Correct manual document. Human confirmation
is required.

**Aufruf**

```text
document_correct_propose document_id document_type number party_id amount [currency] [document_date] [ordered_at] [requested_delivery_at] [customer_reference] [sales_channel] [payment_term_code] [ship_to_party_id]
```

**Zugriff:** `propose`

**Parameter**

| Name                    | Typ      | Pflicht | Beschreibung                                                                        | Standard |
| ----------------------- | -------- | ------- | ----------------------------------------------------------------------------------- | -------- |
| `document_id`           | `string` | ja      | Opaque identity of the evidence document to inspect or correct.                     | —        |
| `document_type`         | `string` | ja      | Evidence kind, such as sales order, purchase order, or invoice.                     | —        |
| `number`                | `string` | ja      | Human-facing document or transaction number; it is not internal identity.           | —        |
| `party_id`              | `string` | ja      | Opaque identity of the customer, supplier, or other operational party.              | —        |
| `amount`                | `string` | ja      | Monetary amount of the payment or financial observation.                            | —        |
| `currency`              | `string` | nein    | ISO 4217 currency code for monetary values.                                         | `EUR`    |
| `document_date`         | `string` | nein    | Business date printed on or asserted by the evidence document.                      | —        |
| `ordered_at`            | `string` | nein    | UTC instant at which an order was placed in its source context.                     | —        |
| `requested_delivery_at` | `string` | nein    | UTC instant by which the customer or operation requests delivery.                   | —        |
| `customer_reference`    | `string` | nein    | Reference supplied by the customer for matching and communication.                  | —        |
| `sales_channel`         | `string` | nein    | Operational sales-channel reference used for repeated routing or pricing decisions. | —        |
| `payment_term_code`     | `string` | nein    | Tenant-scoped code of the payment condition to apply.                               | —        |
| `ship_to_party_id`      | `string` | nein    | Opaque identity of the party receiving the physical delivery.                       | —        |

**Siehe auch:** Geschäftsaktion
[`correct_manual_document`](./commands#command-correct_manual_document)

#### `document_lines_correct_propose` — Correct manual document lines {#tool-document_lines_correct_propose}

Prepare this business mutation without changing state. Correct manual document lines. Human
confirmation is required.

**Aufruf**

```text
document_lines_correct_propose document_id expected_revision lines [actor_context]
```

**Zugriff:** `propose`

**Parameter**

| Name                | Typ      | Pflicht | Beschreibung                                                                                 | Standard |
| ------------------- | -------- | ------- | -------------------------------------------------------------------------------------------- | -------- |
| `document_id`       | `string` | ja      | Opaque identity of the evidence document to inspect or correct.                              | —        |
| `expected_revision` | `string` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.                  | —        |
| `lines`             | `array`  | ja      | Complete intended normalized DocumentLine Evidence snapshot for an atomic manual correction. | —        |
| `actor_context`     | `object` | nein    | Optional authenticated actor metadata retained with the correction audit when available.     | —        |

**Siehe auch:** Geschäftsaktion
[`correct_manual_document`](./commands#command-correct_manual_document)

### `create_source_capability` — Define source capability {#command-create_source_capability}

Declares which upstream type a source may provide and the operational target it is intended to
produce.

**Aufruf**

```text
source_capability_create_propose source_system_id source_type target_type
source_capability_lifecycle_propose capability_id is_active
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `source_system`, `source_capability` · Schreibt: `source_capability`

**Siehe auch:** Agenten-Tool
[`source_capability_create_propose`](./commands#tool-source_capability_create_propose), Agenten-Tool
[`source_capability_lifecycle_propose`](./commands#tool-source_capability_lifecycle_propose)

#### `source_capability_create_propose` — Create source capability {#tool-source_capability_create_propose}

Prepare this business mutation without changing state. Create source capability. Human confirmation
is required.

**Aufruf**

```text
source_capability_create_propose source_system_id source_type target_type
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                    | Standard |
| ------------------ | -------- | ------- | ------------------------------------------------------------------------------- | -------- |
| `source_system_id` | `string` | ja      | Opaque identity of the registered external source instance.                     | —        |
| `source_type`      | `string` | ja      | Upstream record kind as named by its source, before operational interpretation. | —        |
| `target_type`      | `string` | ja      | Operational Reality type the source capability is intended to produce.          | —        |

**Siehe auch:** Geschäftsaktion
[`create_source_capability`](./commands#command-create_source_capability)

#### `source_capability_lifecycle_propose` — Change source capability lifecycle {#tool-source_capability_lifecycle_propose}

Prepare this business mutation without changing state. Change source capability lifecycle. Human
confirmation is required.

**Aufruf**

```text
source_capability_lifecycle_propose capability_id is_active
```

**Zugriff:** `propose`

**Parameter**

| Name            | Typ       | Pflicht | Beschreibung                                                    | Standard |
| --------------- | --------- | ------- | --------------------------------------------------------------- | -------- |
| `capability_id` | `string`  | ja      | Opaque identity of the source capability to change.             | —        |
| `is_active`     | `boolean` | ja      | Whether the record remains selectable for new operational work. | —        |

**Siehe auch:** Geschäftsaktion
[`create_source_capability`](./commands#command-create_source_capability)

### `create_source_system` — Define source system {#command-create_source_system}

Defines one tenant-specific external origin without pretending that a connector or credentials
already exist.

**Aufruf**

```text
source_system_create_propose code name [description]
source_system_lifecycle_propose source_system_id is_active
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `source_system` · Schreibt: `source_system`

**Siehe auch:** Agenten-Tool
[`source_system_create_propose`](./commands#tool-source_system_create_propose), Agenten-Tool
[`source_system_lifecycle_propose`](./commands#tool-source_system_lifecycle_propose)

#### `source_system_create_propose` — Create source system {#tool-source_system_create_propose}

Prepare this business mutation without changing state. Create source system. Human confirmation is
required.

**Aufruf**

```text
source_system_create_propose code name [description]
```

**Zugriff:** `propose`

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung                                                             | Standard |
| ------------- | -------- | ------- | ------------------------------------------------------------------------ | -------- |
| `code`        | `string` | ja      | Short tenant-scoped business code used to find the record operationally. | —        |
| `name`        | `string` | ja      | Human-readable display name; it is not used as internal identity.        | —        |
| `description` | `string` | nein    | Human-readable explanation of the record or rule.                        | —        |

**Siehe auch:** Geschäftsaktion [`create_source_system`](./commands#command-create_source_system)

#### `source_system_lifecycle_propose` — Change source system lifecycle {#tool-source_system_lifecycle_propose}

Prepare this business mutation without changing state. Change source system lifecycle. Human
confirmation is required.

**Aufruf**

```text
source_system_lifecycle_propose source_system_id is_active
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ       | Pflicht | Beschreibung                                                    | Standard |
| ------------------ | --------- | ------- | --------------------------------------------------------------- | -------- |
| `source_system_id` | `string`  | ja      | Opaque identity of the registered external source instance.     | —        |
| `is_active`        | `boolean` | ja      | Whether the record remains selectable for new operational work. | —        |

**Siehe auch:** Geschäftsaktion [`create_source_system`](./commands#command-create_source_system)

### `enqueue_source` — Ingest arbitrary source {#command-enqueue_source}

Stores any JSON object losslessly and idempotently, then queues a registered interpreter or marks
the job unmapped.

**Aufruf**

```text
source_ingest_propose artifact_id [source_system] [source_type] [external_id] [expected_target]
source_record_ingest_propose source_system source_type external_id payload [source_version_at] [context] [source_artifact_id]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `source_stream`, `source_record`, `import_job` · Schreibt:
`source_stream`, `source_record`, `import_job`, `business_event` · Erzeugt:
`source_record.received`, `source_record.unmapped`

**Siehe auch:** Agenten-Tool [`source_ingest_propose`](./commands#tool-source_ingest_propose),
Agenten-Tool [`source_record_ingest_propose`](./commands#tool-source_record_ingest_propose), Event
[`source_record.received`](./events#event-source_record-received), Event
[`source_record.unmapped`](./events#event-source_record-unmapped)

#### `source_ingest_propose` — Propose source ingestion {#tool-source_ingest_propose}

Attach an uploaded artifact to immutable Source evidence after confirmation.

**Aufruf**

```text
source_ingest_propose artifact_id [source_system] [source_type] [external_id] [expected_target]
```

**Zugriff:** `propose`

**Parameter**

| Name              | Typ      | Pflicht | Beschreibung                                                                      | Standard        |
| ----------------- | -------- | ------- | --------------------------------------------------------------------------------- | --------------- |
| `artifact_id`     | `string` | ja      | —                                                                                 | —               |
| `source_system`   | `string` | nein    | Tenant-scoped code naming the external origin of a record.                        | `manual_upload` |
| `source_type`     | `string` | nein    | Upstream record kind as named by its source, before operational interpretation.   | `data_drop`     |
| `external_id`     | `string` | nein    | Identifier assigned by the named external source system; never internal identity. | —               |
| `expected_target` | `string` | nein    | —                                                                                 | `data_drop`     |

**Siehe auch:** Geschäftsaktion [`enqueue_source`](./commands#command-enqueue_source)

#### `source_record_ingest_propose` — Ingest arbitrary source record {#tool-source_record_ingest_propose}

Prepare this business mutation without changing state. Ingest arbitrary source record. Human
confirmation is required.

**Aufruf**

```text
source_record_ingest_propose source_system source_type external_id payload [source_version_at] [context] [source_artifact_id]
```

**Zugriff:** `propose`

**Parameter**

| Name                 | Typ      | Pflicht | Beschreibung                                                                           | Standard |
| -------------------- | -------- | ------- | -------------------------------------------------------------------------------------- | -------- |
| `source_system`      | `string` | ja      | Tenant-scoped code naming the external origin of a record.                             | —        |
| `source_type`        | `string` | ja      | Upstream record kind as named by its source, before operational interpretation.        | —        |
| `external_id`        | `string` | ja      | Identifier assigned by the named external source system; never internal identity.      | —        |
| `payload`            | `object` | ja      | Lossless JSON object received from or prepared for an external context.                | —        |
| `source_version_at`  | `string` | nein    | Upstream version timestamp used to order immutable source versions.                    | —        |
| `context`            | `object` | nein    | Optional structured metadata retained with the operation for traceability.             | —        |
| `source_artifact_id` | `string` | nein    | Optional opaque identity of the immutable streamed file supporting this source record. | —        |

**Siehe auch:** Geschäftsaktion [`enqueue_source`](./commands#command-enqueue_source)

### `install_connector_shell` — Install mock connector shell {#command-install_connector_shell}

Creates one named source instance with only explicitly selected source and target type declarations,
without credentials, synchronization, or vendor API calls.

**Aufruf**

```text
connector_install_propose connector_code [source_types] [system_code] [system_name]
```

**Erreichbar über:** CLI · Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `source_system` · Schreibt: `source_system`, `source_capability`

**Siehe auch:** Agenten-Tool
[`connector_install_propose`](./commands#tool-connector_install_propose)

#### `connector_install_propose` — Install connector shell {#tool-connector_install_propose}

Prepare this business mutation without changing state. Install connector shell. Human confirmation
is required.

**Aufruf**

```text
connector_install_propose connector_code [source_types] [system_code] [system_name]
```

**Zugriff:** `propose`

**Parameter**

| Name             | Typ      | Pflicht | Beschreibung                                                           | Standard |
| ---------------- | -------- | ------- | ---------------------------------------------------------------------- | -------- |
| `connector_code` | `string` | ja      | Template code identifying the connector shell to install.              | —        |
| `source_types`   | `array`  | nein    | Explicit set of upstream record kinds enabled for the connector shell. | —        |
| `system_code`    | `string` | nein    | Unique tenant-scoped code for one external source instance.            | —        |
| `system_name`    | `string` | nein    | Human-readable name of the external source instance.                   | —        |

**Siehe auch:** Geschäftsaktion
[`install_connector_shell`](./commands#command-install_connector_shell)

### `observe_fact` — Observe fact {#command-observe_fact}

Appends one idempotent source-supported observation about an existing tenant-scoped subject after
confirmation without copying typed operational state.

**Aufruf**

```text
fact_observe_propose source_record_id subject_type subject_id predicate value observed_at idempotency_key
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `source_record`, `commitment` · Schreibt: `fact`, `business_event` ·
Erzeugt: `fact.observed`

**Siehe auch:** Agenten-Tool [`fact_observe_propose`](./commands#tool-fact_observe_propose), Aktion
[`observe_fact`](./views#action-observe_fact), Event [`fact.observed`](./events#event-fact-observed)

#### `fact_observe_propose` — Propose Fact observation {#tool-fact_observe_propose}

Prepare one source-supported observation about an existing opaque Reality subject. Human
confirmation is required and model output alone is not a Fact.

**Aufruf**

```text
fact_observe_propose source_record_id subject_type subject_id predicate value observed_at idempotency_key
```

**Zugriff:** `propose`

Record one reviewed, source-supported observation without replacing a typed business transition.

**Verwenden, wenn**

- An immutable SourceRecord explicitly supports an approved Fact predicate about an existing
  subject.

**Nicht verwenden, wenn**

- The statement is only model output, an unsupported inference, or an organizational policy.
- A Commitment, Reservation, Movement, or LedgerEntry already represents the business meaning.

**Voraussetzungen**

- Source and subject exist in the selected tenant and the predicate accepts the subject and value.

**Abgelehnt, wenn**

- `unsupported_predicate` — The Fact predicate is not registered for the subject or value.
- `missing_source` — The immutable supporting SourceRecord does not exist in the selected tenant.

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                                       | Standard |
| ------------------ | -------- | ------- | -------------------------------------------------------------------------------------------------- | -------- |
| `source_record_id` | `string` | ja      | Opaque identity of the immutable source record supporting this typed record.                       | —        |
| `subject_type`     | `string` | ja      | Cataloged Reality record type described by an observation.                                         | —        |
| `subject_id`       | `string` | ja      | Opaque identity of the existing Reality record described by an observation.                        | —        |
| `predicate`        | `string` | ja      | Stable reviewed name of the observed property.                                                     | —        |
| `value`            | `string` | ja      | Scalar observation value validated and canonicalized by its predicate contract.                    | —        |
| `observed_at`      | `string` | ja      | UTC instant at which a source-supported Fact was observed.                                         | —        |
| `idempotency_key`  | `string` | ja      | Caller-stable retry identity for one intended operation; reuse with different content is rejected. | —        |

**Prüfen mit:** `timeline` — The Fact observation event and opaque identity appear in tenant
history.

**Siehe auch:** Geschäftsaktion [`observe_fact`](./commands#command-observe_fact), Projection
[`timeline`](./views#projection-timeline)

### `preview_document` — Preview Document {#command-preview_document}

Maintain and explain explicit external destinations without changing financial evidence.

**Aufruf**

```text
finance_target_mapping_preview target_id document_id [limit] [offset]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `accounting_target`, `accounting_target_reference`,
`finance_target_mapping_revision`, `finance_reference`, `finance_state`, `document`,
`document_line`, `ledger_entry`, `action`, `financial_component`, `component_assignment_revision`,
`component_assignment_part`, `source_record`, `source_system`,
`source_classification_mapping_revision` · Schreibt: —

**Siehe auch:** Agenten-Tool
[`finance_target_mapping_preview`](./commands#tool-finance_target_mapping_preview)

#### `finance_target_mapping_preview` — Finance Target Mapping Preview {#tool-finance_target_mapping_preview}

Inspect Finance target references and explicit mapping resolution.

**Aufruf**

```text
finance_target_mapping_preview target_id document_id [limit] [offset]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                     | Art                        | Standard |
| ------------------------------------ | -------------------------- | -------- |
| `MCP finance_target_mapping_preview` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read Finance-only target configuration and explicit mapping resolution.

**Verwenden, wenn**

- Configure or inspect an explicitly selected external accounting destination.

**Nicht verwenden, wenn**

- Determine tax treatment, change local financial amounts, or claim a remote posting.

**Voraussetzungen**

- Same-tenant target/references; owner confirmation for configuration changes.

**Parameter**

| Name          | Typ       | Pflicht | Beschreibung                                                    | Standard |
| ------------- | --------- | ------- | --------------------------------------------------------------- | -------- |
| `target_id`   | `string`  | ja      | Opaque same-tenant external accounting destination identity.    | —        |
| `document_id` | `string`  | ja      | Opaque identity of the evidence document to inspect or correct. | —        |
| `limit`       | `integer` | nein    | Maximum number of records or jobs processed by this invocation. | —        |
| `offset`      | `integer` | nein    | Number of matching rows to skip for bounded pagination.         | —        |

**Siehe auch:** Geschäftsaktion [`preview_document`](./commands#command-preview_document)

### `record_corrected_document_source` — Record corrected document source {#command-record_corrected_document_source}

Appends a lossless immutable version to the original source stream and queues normal interpretation.

**Aufruf**

```text
document_source_correct_propose document_id payload [source_version_at]
```

**Erreichbar über:** Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `document`, `source_record`, `import_job` · Schreibt: `source_stream`,
`source_record`, `import_job`, `business_event`

**Siehe auch:** Agenten-Tool
[`document_source_correct_propose`](./commands#tool-document_source_correct_propose)

#### `document_source_correct_propose` — Append corrected document source {#tool-document_source_correct_propose}

Prepare this business mutation without changing state. Append corrected document source. Human
confirmation is required.

**Aufruf**

```text
document_source_correct_propose document_id payload [source_version_at]
```

**Zugriff:** `propose`

**Parameter**

| Name                | Typ      | Pflicht | Beschreibung                                                            | Standard |
| ------------------- | -------- | ------- | ----------------------------------------------------------------------- | -------- |
| `document_id`       | `string` | ja      | Opaque identity of the evidence document to inspect or correct.         | —        |
| `payload`           | `object` | ja      | Lossless JSON object received from or prepared for an external context. | —        |
| `source_version_at` | `string` | nein    | Upstream version timestamp used to order immutable source versions.     | —        |

**Siehe auch:** Geschäftsaktion
[`record_corrected_document_source`](./commands#command-record_corrected_document_source)

### `create_manual_document_with_lines` — Record manual document {#command-create_manual_document_with_lines}

Records normalized document evidence and its lines without booking anything or creating a promise.

**Aufruf**

```text
document_create_propose document_type number party_id lines gross_amount [currency] [document_date] [payment_term_code]
```

**Erreichbar über:** Web · API · MCP · Chat

**Wirkung:** Liest: `tenant`, `party`, `item`, `price_list`, `document_line` · Schreibt: `document`,
`document_line`

**Siehe auch:** Agenten-Tool [`document_create_propose`](./commands#tool-document_create_propose)

#### `document_create_propose` — Record manual document {#tool-document_create_propose}

Prepare this business mutation without changing state. Record manual document. Human confirmation is
required.

**Aufruf**

```text
document_create_propose document_type number party_id lines gross_amount [currency] [document_date] [payment_term_code]
```

**Zugriff:** `propose`

**Parameter**

| Name                              | Typ      | Pflicht | Beschreibung                                                                                                                                                                | Standard |
| --------------------------------- | -------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `document_type`                   | `string` | ja      | Evidence kind, such as sales order, purchase order, or invoice. `sales_order`, `purchase_order`, `sales_invoice`, `supplier_invoice`, `credit_note`, `supplier_credit_note` | —        |
| `number`                          | `string` | ja      | Human-facing document or transaction number; it is not internal identity.                                                                                                   | —        |
| `party_id`                        | `string` | ja      | Opaque identity of the customer, supplier, or other operational party.                                                                                                      | —        |
| `lines`                           | `array`  | ja      | Complete intended normalized DocumentLine Evidence snapshot for an atomic manual correction.                                                                                | —        |
| `lines[].item_id`                 | `string` | nein    | Opaque identity of the operational item reference.                                                                                                                          | —        |
| `lines[].sku`                     | `string` | nein    | Human-facing stock-keeping code used to find an item; internal joins use item_id.                                                                                           | —        |
| `lines[].description`             | `string` | nein    | Human-readable explanation of the record or rule.                                                                                                                           | —        |
| `lines[].quantity`                | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                     | —        |
| `lines[].unit`                    | `string` | nein    | Unit of measure in which the quantity is expressed.                                                                                                                         | —        |
| `lines[].unit_price`              | `string` | ja      | Decimal monetary amount for one unit before quantity multiplication.                                                                                                        | —        |
| `lines[].gross_amount`            | `string` | ja      | Total the source states for the document; recorded as received and never calculated.                                                                                        | —        |
| `lines[].line_type`               | `string` | nein    | Closed kind of a document line, such as goods or a charge, taken from the source statement.                                                                                 | —        |
| `lines[].promised_at`             | `string` | nein    | UTC instant by which the line's quantity is promised; it becomes the due time of the derived Commitment.                                                                    | —        |
| `lines[].price_list_entry_id`     | `string` | nein    | Opaque identity of the price tier the line price came from, when a list price was applied; provenance, not a recalculation.                                                 | —        |
| `lines[].billed_document_line_id` | `string` | nein    | Opaque identity of the billed order line, or selected invoice line for an invoice-linked credit; the shortest typed evidence relationship.                                  | —        |
| `gross_amount`                    | `string` | ja      | Total the source states for the document; recorded as received and never calculated.                                                                                        | —        |
| `currency`                        | `string` | nein    | ISO 4217 currency code for monetary values.                                                                                                                                 | —        |
| `document_date`                   | `string` | nein    | Business date printed on or asserted by the evidence document.                                                                                                              | —        |
| `payment_term_code`               | `string` | nein    | Tenant-scoped code of the payment condition to apply.                                                                                                                       | —        |

**Siehe auch:** Geschäftsaktion
[`create_manual_document_with_lines`](./commands#command-create_manual_document_with_lines)

## Bereichsübergreifend

### `assign_supply` — Assign incoming supply to customer demand {#command-assign_supply}

Assigns an explicit quantity of an incoming supplier commitment to a compatible customer commitment
without moving or reserving stock.

**Aufruf**

```text
supply_assign_propose supplier_commitment_id [customer_commitment_id] purpose quantity
```

**Erreichbar über:** CLI · Web · API · MCP · Chat · **Bestätigung:** `required`

**Wirkung:** Liest: `commitment`, `supply_assignment`, `source_record` · Schreibt:
`supply_assignment`, `source_record`

**Siehe auch:** Agenten-Tool [`supply_assign_propose`](./commands#tool-supply_assign_propose)

#### `supply_assign_propose` — Assign supplier supply {#tool-supply_assign_propose}

Prepare this business mutation without changing state. Assign supplier supply. Human confirmation is
required.

**Aufruf**

```text
supply_assign_propose supplier_commitment_id [customer_commitment_id] purpose quantity
```

**Zugriff:** `propose`

**Parameter**

| Name                     | Typ      | Pflicht | Beschreibung                                                                                                                                                  | Standard |
| ------------------------ | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `supplier_commitment_id` | `string` | ja      | Opaque identity of the incoming supplier commitment whose quantity is being assigned.                                                                         | —        |
| `customer_commitment_id` | `string` | nein    | Optional opaque identity of the outgoing customer commitment that the incoming supply is intended to cover; absence explicitly assigns the quantity to stock. | —        |
| `purpose`                | `string` | ja      | Closed business purpose that determines the shipment's counterparty role and compatible Movement type. `customer_demand`, `stock_replenishment`               | —        |
| `quantity`               | `string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                       | —        |

**Siehe auch:** Geschäftsaktion [`assign_supply`](./commands#command-assign_supply)

### `change_graph_report` — Change Private Graph Report {#command-change_graph_report}

Save, rename, duplicate or delete the authenticated user's private graph question, recording the
model version that gave it meaning, with revision and retry protection.

**Aufruf**

```text
graph_report_change_propose operation request_id [report_id] [expected_revision] [name] [question]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `tenant`, `app_user`, `tenant_membership`, `analytics_report` · Schreibt:
`analytics_report`

**Siehe auch:** Agenten-Tool
[`graph_report_change_propose`](./commands#tool-graph_report_change_propose)

#### `graph_report_change_propose` — Change private graph report {#tool-graph_report_change_propose}

Prepare a private graph report change. Requires trusted authenticated user context; confirm
explicitly before it is saved.

**Aufruf**

```text
graph_report_change_propose operation request_id [report_id] [expected_revision] [name] [question]
```

**Zugriff:** `propose`

**Parameter**

| Name                                           | Typ       | Pflicht | Beschreibung                                                                                                                                                                                                                                             | Standard     |
| ---------------------------------------------- | --------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| `operation`                                    | `string`  | ja      | The private graph report change to prepare for confirmation. `create`, `update`, `rename`, `duplicate`, `delete`                                                                                                                                         | —            |
| `request_id`                                   | `string`  | ja      | A fresh UUID for this change. Generate a new one every time; reuse one only to retry the identical change after a failed response. The same key with different content is refused, because it cannot be told apart from a change that was already saved. | —            |
| `report_id`                                    | `string`  | nein    | Opaque owned report ID; omitted only when creating.                                                                                                                                                                                                      | `None`       |
| `expected_revision`                            | `integer` | nein    | Revision shown to the caller; required for every existing report change.                                                                                                                                                                                 | `None`       |
| `name`                                         | `string`  | nein    | Private report name for create, rename or duplicate.                                                                                                                                                                                                     | `None`       |
| `question`                                     | `object`  | nein    | The whole question.                                                                                                                                                                                                                                      | `None`       |
| `question.from`                                | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.inventory_cost_context`              | `object`  | nein    | One retained joint confirmation, never an implicit latest valuation.                                                                                                                                                                                     | `None`       |
| `question.inventory_cost_context.action_id`    | `string`  | ja      | Optional opaque Change Proposal identity linking an emitted Business Event to its confirmed action.                                                                                                                                                      | —            |
| `question.inventory_cost_context.mode`         | `string`  | nein    | —                                                                                                                                                                                                                                                        | `historical` |
| `question.contribution_cost_context`           | `object`  | nein    | One retained joint scope, optionally requiring unchanged knowledge.                                                                                                                                                                                      | `None`       |
| `question.contribution_cost_context.action_id` | `string`  | ja      | Optional opaque Change Proposal identity linking an emitted Business Event to its confirmed action.                                                                                                                                                      | —            |
| `question.contribution_cost_context.mode`      | `string`  | nein    | `historical`, `current`                                                                                                                                                                                                                                  | `historical` |
| `question.captured_cost_context`               | `object`  | nein    | One sealed captured report generation, never a mutable latest pointer.                                                                                                                                                                                   | `None`       |
| `question.captured_cost_context.generation_id` | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.company_cost_context`                | `object`  | nein    | One verified financial company generation, never an implicit latest pointer.                                                                                                                                                                             | `None`       |
| `question.company_cost_context.generation_id`  | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.as`                                  | `string`  | nein    | —                                                                                                                                                                                                                                                        | `root`       |
| `question.follow`                              | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.follow[].edge`                       | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.follow[].direction`                  | `string`  | nein    | Business flow direction, such as sales or purchase, incoming or outgoing. `out`, `in`                                                                                                                                                                    | `out`        |
| `question.follow[].as`                         | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.follow[].from`                       | `string`  | nein    | —                                                                                                                                                                                                                                                        | `None`       |
| `question.follow[].depth`                      | `array`   | nein    | —                                                                                                                                                                                                                                                        | `None`       |
| `question.filter`                              | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.filter[].field`                      | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.filter[].op`                         | `string`  | ja      | `eq`, `ne`, `in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `is_null`, `is_not_null`                                                                                                                                                                           | —            |
| `question.filter[].value`                      | `any`     | nein    | Scalar observation value validated and canonicalized by its predicate contract.                                                                                                                                                                          | `None`       |
| `question.measures`                            | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.group_by`                            | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.group_by[].field`                    | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.group_by[].bucket`                   | `string`  | nein    | `day`, `week`, `month`, `quarter`, `year`                                                                                                                                                                                                                | `None`       |
| `question.group_by[].as`                       | `string`  | nein    | —                                                                                                                                                                                                                                                        | `None`       |
| `question.having`                              | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.having[].measure`                    | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.having[].op`                         | `string`  | ja      | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`                                                                                                                                                                                                                     | —            |
| `question.having[].value`                      | `number`  | ja      | Scalar observation value validated and canonicalized by its predicate contract.                                                                                                                                                                          | —            |
| `question.exists`                              | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.exists[].follow`                     | `array`   | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.exists[].follow[].edge`              | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.exists[].follow[].direction`         | `string`  | nein    | Business flow direction, such as sales or purchase, incoming or outgoing. `out`, `in`                                                                                                                                                                    | `out`        |
| `question.exists[].follow[].as`                | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.exists[].follow[].from`              | `string`  | nein    | —                                                                                                                                                                                                                                                        | `None`       |
| `question.exists[].follow[].depth`             | `array`   | nein    | —                                                                                                                                                                                                                                                        | `None`       |
| `question.exists[].filter`                     | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.exists[].filter[].field`             | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.exists[].filter[].op`                | `string`  | ja      | `eq`, `ne`, `in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `is_null`, `is_not_null`                                                                                                                                                                           | —            |
| `question.exists[].filter[].value`             | `any`     | nein    | Scalar observation value validated and canonicalized by its predicate contract.                                                                                                                                                                          | `None`       |
| `question.exists[].negated`                    | `boolean` | nein    | —                                                                                                                                                                                                                                                        | `False`      |
| `question.order_by`                            | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.order_by[].by`                       | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.order_by[].descending`               | `boolean` | nein    | —                                                                                                                                                                                                                                                        | `False`      |
| `question.limit`                               | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                                                                                                                                                                                          | `200`        |

**Siehe auch:** Geschäftsaktion [`change_graph_report`](./commands#command-change_graph_report)

### `execute_cost_change` — Confirm cost and contribution decision {#command-execute_cost_change}

Derive receipt costs from exact received amounts and explicit owner decisions; retain sealed
reviewed knowledge and keep incomplete costs unknown.

**Aufruf**

```text
cost_change_propose expected_event_sequence reason operation [document_id] [document_line_id] [expected_evidence_hash] [basis] [selected_basis_tax_inclusion] [tax_treatment] [nonrecoverable_tax_amount] [parts] [allocation_total] [category] [cost_effect] [amount_bucket] [driver_kind] [conversion_basis_revision_id] [targets] [movement_id] [categories] [previous_component_basis_id] [component_basis_id] [item_id] [owner_party_id] [method] [currency] [base_unit] [history_start] [effective_at] [history_complete_from_zero] [receipt_cost_scopes_confirmed] [economic_issue_ids] [loss_movement_ids] [supplier_return_ids] [customer_return_ids] [receipts] [openings] [specific_selections] [return_parts] [ownership_parts] [scopes] [expected_candidate_hash] [profile] [profile_confirmed] [revenue_complete] [economic_at] [selling_categories] [positions] [goods_cost_disposition] [inventory_parts] [direct_parts] [direct_cost_complete] [selling_expense_confirmed] [evidence_source_record_id] [kind] [from_code] [to_code] [numerator] [denominator] [supersedes_id] [inventory_review_id]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `movement`, `document`, `document_line`, `source_record`, `financial_component`,
`cost_receipt_basis`, `cost_attribution_revision`, `cost_attribution_part`, `cost_scope_review`,
`cost_input_manifest`, `cost_inventory_review`, `cost_inventory_member`,
`cost_valuation_assessment_revision`, `cost_valuation_assessment_part`,
`cost_conversion_basis_revision` · Schreibt: `cost_revenue_match_basis`, `cost_contribution_review`,
`cost_selling_attribution_part`, `cost_selling_review_category`, `cost_selling_review_member`,
`cost_policy_revision`, `cost_movement_basis`, `cost_ownership_revision`, `cost_inventory_review`,
`cost_inventory_member`, `cost_valuation_assessment_revision`, `cost_valuation_assessment_part`,
`cost_conversion_basis_revision`, `financial_component`, `cost_receipt_basis`,
`cost_component_basis`, `cost_attribution_revision`, `cost_attribution_part`,
`cost_component_replacement`, `cost_scope_review`, `cost_scope_review_category`,
`cost_input_manifest`, `cost_manifest_receipt`, `cost_manifest_component`,
`cost_manifest_attribution`, `cost_manifest_correction`, `cost_manifest_replacement`,
`business_event`, `action` · Erzeugt: `cost.attributed`, `cost.reviewed`

**Siehe auch:** Agenten-Tool [`cost_change_propose`](./commands#tool-cost_change_propose), Event
[`cost.attributed`](./events#event-cost-attributed), Event
[`cost.reviewed`](./events#event-cost-reviewed)

#### `cost_change_propose` — Review cost and contribution decision {#tool-cost_change_propose}

Prepare explicit received-cost attribution, replacement, withdrawal, inventory scope or whole-line
contribution review. An active owner must explicitly confirm the unchanged proposal.

**Aufruf**

```text
cost_change_propose expected_event_sequence reason operation [document_id] [document_line_id] [expected_evidence_hash] [basis] [selected_basis_tax_inclusion] [tax_treatment] [nonrecoverable_tax_amount] [parts] [allocation_total] [category] [cost_effect] [amount_bucket] [driver_kind] [conversion_basis_revision_id] [targets] [movement_id] [categories] [previous_component_basis_id] [component_basis_id] [item_id] [owner_party_id] [method] [currency] [base_unit] [history_start] [effective_at] [history_complete_from_zero] [receipt_cost_scopes_confirmed] [economic_issue_ids] [loss_movement_ids] [supplier_return_ids] [customer_return_ids] [receipts] [openings] [specific_selections] [return_parts] [ownership_parts] [scopes] [expected_candidate_hash] [profile] [profile_confirmed] [revenue_complete] [economic_at] [selling_categories] [positions] [goods_cost_disposition] [inventory_parts] [direct_parts] [direct_cost_complete] [selling_expense_confirmed] [evidence_source_record_id] [kind] [from_code] [to_code] [numerator] [denominator] [supersedes_id] [inventory_review_id]
```

**Zugriff:** `propose`

Prepare acquisition or selling-cost decisions, bounded inventory reviews and explicitly confirmed
whole-line DB1/DB2 reviews. For inventory_review and contribution_review, call cost_review_draft
first and propose its arguments unchanged.

**Verwenden, wenn**

- Assign received acquisition amounts, review their completeness, confirm bounded inventory scope or
  approve an exact whole-line commercial contribution.

**Nicht verwenden, wenn**

- Automatically choose company policies, post ledger entries, certify HGB book value or calculate
  unsupported tax/FX or company-wide margins.

**Voraussetzungen**

- Explicit active owner confirmation; unchanged event sequence and received evidence.

**Abgelehnt, wenn**

- `invalid_cost_decision` — Missing/foreign evidence, stale sequence, non-owner, unconfirmed action,
  excess shares, mixed currency, unsupported corrected receipt or invalid tax shares.

**Parameter**

| Name                                                   | Typ                | Pflicht | Beschreibung                                                                                                                                                                   | Standard         |
| ------------------------------------------------------ | ------------------ | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------- |
| `expected_event_sequence`                              | `integer`          | ja      | —                                                                                                                                                                              | —                |
| `reason`                                               | `string`           | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                                        | —                |
| `operation`                                            | `string`           | ja      | —                                                                                                                                                                              | —                |
| `document_id`                                          | `string`           | nein    | Opaque identity of the evidence document to inspect or correct.                                                                                                                | —                |
| `document_line_id`                                     | `string`           | nein    | Opaque same-tenant received document line identity; must belong to the selected document.                                                                                      | `None`           |
| `expected_evidence_hash`                               | `string`           | nein    | —                                                                                                                                                                              | —                |
| `basis`                                                | `string`           | nein    | `net`, `gross`, `base`                                                                                                                                                         | —                |
| `selected_basis_tax_inclusion`                         | `string`           | nein    | `included`, `excluded`, `unknown`                                                                                                                                              | —                |
| `tax_treatment`                                        | `string`           | nein    | `recoverable`, `nonrecoverable`, `mixed`, `not_applicable`, `unknown`                                                                                                          | —                |
| `nonrecoverable_tax_amount`                            | `number \| string` | nein    | —                                                                                                                                                                              | `0`              |
| `parts`                                                | `array`            | nein    | —                                                                                                                                                                              | —                |
| `parts[].movement_id`                                  | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `parts[].category`                                     | `string`           | ja      | `goods`, `inbound_freight`, `duty`, `other_acquisition`, `purchase_reduction`, `nonrecoverable_tax`                                                                            | —                |
| `parts[].source_share`                                 | `number \| string` | ja      | Explicit signed share of the selected received amount; total shares cannot exceed that source bucket.                                                                          | —                |
| `parts[].cost_effect`                                  | `integer`          | ja      | Explicit economic cost direction, separate from the retained source sign. `-1`, `1`                                                                                            | —                |
| `parts[].amount_bucket`                                | `string`           | nein    | `selected_basis`, `nonrecoverable_tax`                                                                                                                                         | `selected_basis` |
| `parts[].assignment_kind`                              | `string`           | nein    | Direct cost attribution or explicitly allocated share, kept separate in contribution output. `direct`, `allocated`                                                             | `direct`         |
| `parts[].conversion_basis_revision_id`                 | `string`           | nein    | —                                                                                                                                                                              | `None`           |
| `allocation_total`                                     | `number \| string` | nein    | —                                                                                                                                                                              | —                |
| `category`                                             | `string`           | nein    | `goods`, `inbound_freight`, `duty`, `other_acquisition`, `purchase_reduction`, `nonrecoverable_tax`                                                                            | —                |
| `cost_effect`                                          | `integer`          | nein    | Explicit economic cost direction, separate from the retained source sign. `-1`, `1`                                                                                            | —                |
| `amount_bucket`                                        | `string`           | nein    | `selected_basis`, `nonrecoverable_tax`                                                                                                                                         | —                |
| `driver_kind`                                          | `string`           | nein    | `quantity`, `equal`, `manual`                                                                                                                                                  | —                |
| `conversion_basis_revision_id`                         | `string`           | nein    | —                                                                                                                                                                              | `None`           |
| `targets`                                              | `array`            | nein    | —                                                                                                                                                                              | —                |
| `targets[].movement_id`                                | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `targets[].weight`                                     | `number \| string` | nein    | —                                                                                                                                                                              | `None`           |
| `movement_id`                                          | `string`           | nein    | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `categories`                                           | `array`            | nein    | —                                                                                                                                                                              | —                |
| `categories[].category`                                | `string`           | ja      | `goods`, `inbound_freight`, `duty`, `other_acquisition`, `purchase_reduction`, `nonrecoverable_tax`                                                                            | —                |
| `categories[].disposition`                             | `string`           | ja      | Closed physical outcome for returned goods; restock, quarantine or repair, scrap or loss, or return to supplier. `evidenced`, `confirmed_zero`, `not_applicable`, `unresolved` | —                |
| `categories[].reason`                                  | `string`           | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                                        | —                |
| `previous_component_basis_id`                          | `string`           | nein    | —                                                                                                                                                                              | —                |
| `component_basis_id`                                   | `string`           | nein    | —                                                                                                                                                                              | —                |
| `item_id`                                              | `string`           | nein    | Opaque identity of the operational item reference.                                                                                                                             | —                |
| `owner_party_id`                                       | `string`           | nein    | —                                                                                                                                                                              | —                |
| `method`                                               | `string`           | nein    | `fifo`, `specific`                                                                                                                                                             | —                |
| `currency`                                             | `string`           | nein    | ISO 4217 currency code for monetary values.                                                                                                                                    | —                |
| `base_unit`                                            | `string`           | nein    | —                                                                                                                                                                              | —                |
| `history_start`                                        | `string`           | nein    | —                                                                                                                                                                              | —                |
| `effective_at`                                         | `string`           | nein    | UTC instant from which the observation or rule takes effect.                                                                                                                   | —                |
| `history_complete_from_zero`                           | `boolean`          | nein    | —                                                                                                                                                                              | —                |
| `receipt_cost_scopes_confirmed`                        | `boolean`          | nein    | —                                                                                                                                                                              | —                |
| `economic_issue_ids`                                   | `array`            | nein    | —                                                                                                                                                                              | —                |
| `loss_movement_ids`                                    | `array`            | nein    | —                                                                                                                                                                              | —                |
| `supplier_return_ids`                                  | `array`            | nein    | —                                                                                                                                                                              | —                |
| `customer_return_ids`                                  | `array`            | nein    | —                                                                                                                                                                              | —                |
| `receipts`                                             | `array`            | nein    | —                                                                                                                                                                              | —                |
| `receipts[].movement_id`                               | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `receipts[].manifest_id`                               | `string`           | ja      | Opaque sealed receipt review input set; absence requests current retained knowledge.                                                                                           | —                |
| `receipts[].ownership_source_record_id`                | `string`           | ja      | —                                                                                                                                                                              | —                |
| `openings`                                             | `array`            | nein    | —                                                                                                                                                                              | —                |
| `openings[].movement_id`                               | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `openings[].evidence_source_record_id`                 | `string`           | ja      | —                                                                                                                                                                              | —                |
| `openings[].acquisition_cost`                          | `number \| string` | ja      | —                                                                                                                                                                              | —                |
| `specific_selections`                                  | `array`            | nein    | —                                                                                                                                                                              | —                |
| `specific_selections[].movement_id`                    | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `specific_selections[].entry_movement_id`              | `string`           | ja      | —                                                                                                                                                                              | —                |
| `specific_selections[].receipt_movement_id`            | `string`           | ja      | —                                                                                                                                                                              | —                |
| `specific_selections[].quantity`                       | `number \| string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                        | —                |
| `return_parts`                                         | `array`            | nein    | —                                                                                                                                                                              | —                |
| `return_parts[].movement_id`                           | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `return_parts[].entry_movement_id`                     | `string`           | ja      | —                                                                                                                                                                              | —                |
| `return_parts[].receipt_movement_id`                   | `string`           | ja      | —                                                                                                                                                                              | —                |
| `return_parts[].quantity`                              | `number \| string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                        | —                |
| `return_parts[].issue_movement_id`                     | `string`           | ja      | —                                                                                                                                                                              | —                |
| `ownership_parts`                                      | `array`            | nein    | —                                                                                                                                                                              | —                |
| `ownership_parts[].movement_id`                        | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `ownership_parts[].owner_party_id`                     | `string`           | ja      | —                                                                                                                                                                              | —                |
| `ownership_parts[].evidence_source_record_id`          | `string`           | ja      | —                                                                                                                                                                              | —                |
| `ownership_parts[].quantity`                           | `number \| string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                        | —                |
| `scopes`                                               | `array`            | nein    | —                                                                                                                                                                              | —                |
| `scopes[].item_id`                                     | `string`           | ja      | Opaque identity of the operational item reference.                                                                                                                             | —                |
| `scopes[].owner_party_id`                              | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].method`                                      | `string`           | ja      | `fifo`, `specific`                                                                                                                                                             | —                |
| `scopes[].currency`                                    | `string`           | ja      | ISO 4217 currency code for monetary values.                                                                                                                                    | —                |
| `scopes[].base_unit`                                   | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].history_start`                               | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].effective_at`                                | `string`           | ja      | UTC instant from which the observation or rule takes effect.                                                                                                                   | —                |
| `scopes[].history_complete_from_zero`                  | `boolean`          | ja      | —                                                                                                                                                                              | —                |
| `scopes[].receipt_cost_scopes_confirmed`               | `boolean`          | ja      | —                                                                                                                                                                              | —                |
| `scopes[].economic_issue_ids`                          | `array`            | ja      | —                                                                                                                                                                              | —                |
| `scopes[].loss_movement_ids`                           | `array`            | nein    | —                                                                                                                                                                              | —                |
| `scopes[].supplier_return_ids`                         | `array`            | nein    | —                                                                                                                                                                              | —                |
| `scopes[].customer_return_ids`                         | `array`            | nein    | —                                                                                                                                                                              | —                |
| `scopes[].receipts`                                    | `array`            | nein    | —                                                                                                                                                                              | —                |
| `scopes[].receipts[].movement_id`                      | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `scopes[].receipts[].manifest_id`                      | `string`           | ja      | Opaque sealed receipt review input set; absence requests current retained knowledge.                                                                                           | —                |
| `scopes[].receipts[].ownership_source_record_id`       | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].openings`                                    | `array`            | nein    | —                                                                                                                                                                              | —                |
| `scopes[].openings[].movement_id`                      | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `scopes[].openings[].evidence_source_record_id`        | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].openings[].acquisition_cost`                 | `number \| string` | ja      | —                                                                                                                                                                              | —                |
| `scopes[].specific_selections`                         | `array`            | nein    | —                                                                                                                                                                              | —                |
| `scopes[].specific_selections[].movement_id`           | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `scopes[].specific_selections[].entry_movement_id`     | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].specific_selections[].receipt_movement_id`   | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].specific_selections[].quantity`              | `number \| string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                        | —                |
| `scopes[].return_parts`                                | `array`            | nein    | —                                                                                                                                                                              | —                |
| `scopes[].return_parts[].movement_id`                  | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `scopes[].return_parts[].entry_movement_id`            | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].return_parts[].receipt_movement_id`          | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].return_parts[].quantity`                     | `number \| string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                        | —                |
| `scopes[].return_parts[].issue_movement_id`            | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].ownership_parts`                             | `array`            | nein    | —                                                                                                                                                                              | —                |
| `scopes[].ownership_parts[].movement_id`               | `string`           | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.                                                                                               | —                |
| `scopes[].ownership_parts[].owner_party_id`            | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].ownership_parts[].evidence_source_record_id` | `string`           | ja      | —                                                                                                                                                                              | —                |
| `scopes[].ownership_parts[].quantity`                  | `number \| string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                        | —                |
| `expected_candidate_hash`                              | `string`           | nein    | Exact fingerprint returned by the current contribution preview; changed evidence requires a new preview.                                                                       | —                |
| `profile`                                              | `string`           | nein    | —                                                                                                                                                                              | —                |
| `profile_confirmed`                                    | `boolean`          | nein    | Explicit owner confirmation of the declared commercial profile for this reviewed scope.                                                                                        | —                |
| `revenue_complete`                                     | `boolean`          | nein    | Explicit owner confirmation that received revenue covers this entire matched quantity.                                                                                         | —                |
| `economic_at`                                          | `string`           | nein    | Confirmed UTC recognition time; this whole-line contribution scope requires the exact shipment time.                                                                           | —                |
| `selling_categories`                                   | `array`            | nein    | Complete seven-category commercial_v1 selling checklist; omitted means DB2 remains unknown.                                                                                    | `None`           |
| `selling_categories[].category`                        | `string`           | ja      | `outbound_freight`, `fulfilment`, `packaging`, `payment_fee`, `marketplace_commission`, `sales_commission`, `other_selling`                                                    | —                |
| `selling_categories[].disposition`                     | `string`           | ja      | Closed physical outcome for returned goods; restock, quarantine or repair, scrap or loss, or return to supplier. `evidenced`, `confirmed_zero`, `not_applicable`, `unresolved` | —                |
| `selling_categories[].reason`                          | `string`           | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                                        | —                |
| `positions`                                            | `array`            | nein    | —                                                                                                                                                                              | —                |
| `positions[].document_line_id`                         | `string`           | ja      | Opaque same-tenant received document line identity; must belong to the selected document.                                                                                      | —                |
| `positions[].expected_candidate_hash`                  | `string`           | ja      | Exact fingerprint returned by the current contribution preview; changed evidence requires a new preview.                                                                       | —                |
| `positions[].profile`                                  | `string`           | ja      | —                                                                                                                                                                              | —                |
| `positions[].profile_confirmed`                        | `boolean`          | ja      | Explicit owner confirmation of the declared commercial profile for this reviewed scope.                                                                                        | —                |
| `positions[].revenue_complete`                         | `boolean`          | ja      | Explicit owner confirmation that received revenue covers this entire matched quantity.                                                                                         | —                |
| `positions[].economic_at`                              | `string`           | ja      | Confirmed UTC recognition time; this whole-line contribution scope requires the exact shipment time.                                                                           | —                |
| `positions[].selling_categories`                       | `array`            | nein    | Complete seven-category commercial_v1 selling checklist; omitted means DB2 remains unknown.                                                                                    | `None`           |
| `positions[].selling_categories[].category`            | `string`           | ja      | `outbound_freight`, `fulfilment`, `packaging`, `payment_fee`, `marketplace_commission`, `sales_commission`, `other_selling`                                                    | —                |
| `positions[].selling_categories[].disposition`         | `string`           | ja      | Closed physical outcome for returned goods; restock, quarantine or repair, scrap or loss, or return to supplier. `evidenced`, `confirmed_zero`, `not_applicable`, `unresolved` | —                |
| `positions[].selling_categories[].reason`              | `string`           | ja      | Human-readable explanation for a hold, correction, or lifecycle change.                                                                                                        | —                |
| `goods_cost_disposition`                               | `string`           | nein    | `inventory`, `direct_evidence`, `not_applicable`, `unresolved`                                                                                                                 | —                |
| `inventory_parts`                                      | `array`            | nein    | —                                                                                                                                                                              | —                |
| `inventory_parts[].inventory_member_id`                | `string`           | ja      | —                                                                                                                                                                              | —                |
| `inventory_parts[].entry_movement_basis_id`            | `string`           | ja      | —                                                                                                                                                                              | —                |
| `inventory_parts[].receipt_movement_basis_id`          | `string`           | ja      | —                                                                                                                                                                              | —                |
| `inventory_parts[].original_issue_member_id`           | `string`           | nein    | —                                                                                                                                                                              | `None`           |
| `inventory_parts[].quantity`                           | `number \| string` | ja      | Decimal quantity expressed in the item's relevant unit.                                                                                                                        | —                |
| `direct_parts`                                         | `array`            | nein    | —                                                                                                                                                                              | —                |
| `direct_parts[].attribution_revision_id`               | `string`           | ja      | —                                                                                                                                                                              | —                |
| `direct_parts[].input_role`                            | `string`           | ja      | `service_input`, `shipping_input`, `kit_input`, `production_input`                                                                                                             | —                |
| `direct_cost_complete`                                 | `boolean`          | nein    | —                                                                                                                                                                              | `False`          |
| `selling_expense_confirmed`                            | `boolean`          | nein    | Explicit owner confirmation of selling expense, excluding acquisition costs, inventory purchases, general overhead and already included manufacturing cost.                    | —                |
| `evidence_source_record_id`                            | `string`           | nein    | —                                                                                                                                                                              | —                |
| `kind`                                                 | `string`           | nein    | Explicit internal or target reference kind; no inferred tax or country meaning. `unit`, `currency`                                                                             | —                |
| `from_code`                                            | `string`           | nein    | —                                                                                                                                                                              | —                |
| `to_code`                                              | `string`           | nein    | —                                                                                                                                                                              | —                |
| `numerator`                                            | `number \| string` | nein    | —                                                                                                                                                                              | —                |
| `denominator`                                          | `number \| string` | nein    | —                                                                                                                                                                              | —                |
| `supersedes_id`                                        | `string`           | nein    | —                                                                                                                                                                              | `None`           |
| `inventory_review_id`                                  | `string`           | nein    | —                                                                                                                                                                              | —                |

**Prüfen mit:** `cost.contribution.get` — Confirmed whole-line revenue and inventory basis, plus
independently reviewed selling-cost coverage for DB2.; `cost.receipt.get` — Retained received-cost
shares and reviewed completeness.; `cost.inventory.get` — Confirmed bounded policy, ownership,
acquisition value and consumption at an exact retained cutoff.

**Siehe auch:** Geschäftsaktion [`execute_cost_change`](./commands#command-execute_cost_change)

### `cost_review_draft` — Draft a cost review {#command-cost_review_draft}

Draft the inventory or contribution review the held records support, or name the inputs a person
must provide; nothing is stored or proposed.

**Aufruf**

```text
cost_review_draft kind scope_id [answers]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `item`, `movement`, `movement_correction`, `party`, `party_role`,
`source_record`, `document`, `document_line`, `financial_component`, `cost_input_manifest`,
`cost_receipt_basis`, `cost_attribution_revision`, `cost_attribution_part`, `cost_component_basis`,
`cost_scope_review`, `cost_inventory_review` · Schreibt: —

**Siehe auch:** Agenten-Tool [`cost_review_draft`](./commands#tool-cost_review_draft)

#### `cost_review_draft` — Draft a cost review {#tool-cost_review_draft}

Draft the inventory or contribution review the held records support: complete cost_change_propose
arguments, or the open inputs a person must decide. Call it before cost_change_propose.

**Aufruf**

```text
cost_review_draft kind scope_id [answers]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage        | Art                        | Standard |
| ----------------------- | -------------------------- | -------- |
| `MCP cost_review_draft` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Draft the inventory or contribution cost review that held records support, so nobody has to supply
identifiers.

**Verwenden, wenn**

- Before cost_change_propose for inventory_review or contribution_review, including when a person
  asks in plain language to prepare a cost review.

**Nicht verwenden, wenn**

- Assign supplier invoice lines to receipts or review selling costs; those have their own
  operations.

**Parameter**

| Name                     | Typ      | Pflicht | Beschreibung                                                                                                | Standard |
| ------------------------ | -------- | ------- | ----------------------------------------------------------------------------------------------------------- | -------- |
| `kind`                   | `string` | ja      | Explicit internal or target reference kind; no inferred tax or country meaning. `inventory`, `contribution` | —        |
| `scope_id`               | `string` | ja      | Exact item identity for inventory or received invoice-line identity for contribution.                       | —        |
| `answers`                | `object` | nein    | What a person decided for the open inputs; nothing else is accepted.                                        | `None`   |
| `answers.method`         | `string` | nein    | `fifo`, `specific`                                                                                          | `None`   |
| `answers.owner_party_id` | `string` | nein    | —                                                                                                           | `None`   |

**Siehe auch:** Geschäftsaktion [`cost_review_draft`](./commands#command-cost_review_draft)

### `cost_record` — Inspect retained cost record {#command-cost_record}

Inspect retained evidence and decision fields with tenant-safe source links and paged exact
membership; no current valuation claim or business writes.

**Aufruf**

```text
cost_record_get kind record_id [page] [language]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `cost_receipt_basis`, `cost_component_basis`, `cost_conversion_basis_revision`,
`cost_attribution_revision`, `cost_attribution_part`, `cost_component_replacement`,
`cost_correction_basis`, `cost_input_manifest`, `cost_scope_review`, `cost_scope_review_category`,
`cost_manifest_receipt`, `cost_manifest_component`, `cost_manifest_attribution`,
`cost_manifest_correction`, `cost_manifest_replacement`, `cost_policy_revision`,
`cost_movement_basis`, `cost_ownership_revision`, `cost_inventory_review`, `cost_inventory_member`,
`cost_valuation_assessment_revision`, `cost_valuation_assessment_part`, `cost_revenue_match_basis`,
`cost_contribution_review`, `cost_selling_attribution_part`, `cost_selling_review_category`,
`cost_selling_review_member`, `cost_company_census`, `cost_company_census_movement`,
`cost_company_census_document`, `cost_company_census_line`, `cost_company_census_source`,
`cost_captured_basis`, `cost_captured_inventory_basis`, `cost_captured_contribution_basis`,
`cost_company_manifest`, `cost_company_inventory_input`, `cost_company_contribution_input`,
`cost_company_generation`, `financial_component`, `action`, `movement_correction`,
`interpretation_outcome` · Schreibt: —

**Siehe auch:** Agenten-Tool [`cost_record_get`](./commands#tool-cost_record_get)

#### `cost_record_get` — Inspect retained cost record {#tool-cost_record_get}

Read exact cost evidence, decision references and bounded retained membership; no current valuation
claim.

**Aufruf**

```text
cost_record_get kind record_id [page] [language]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage      | Art                        | Standard |
| --------------------- | -------------------------- | -------- |
| `MCP cost_record_get` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Inspect one retained cost record with exact values, source links and paged membership through the
same reader as the web Inspector and CLI.

**Verwenden, wenn**

- Follow an opaque cost, policy, inventory or contribution review reference to its retained
  evidence.

**Nicht verwenden, wenn**

- Calculate a current cost or margin, change a policy, or request an arbitrary database table.

**Parameter**

| Name        | Typ       | Pflicht | Beschreibung                                                                            | Standard |
| ----------- | --------- | ------- | --------------------------------------------------------------------------------------- | -------- |
| `kind`      | `string`  | ja      | Explicit internal or target reference kind; no inferred tax or country meaning.         | —        |
| `record_id` | `string`  | ja      | Opaque identity of the master-data record whose lifecycle is being changed.             | —        |
| `page`      | `integer` | nein    | One-based page of retained membership, bounded to 25 records per page.                  | `1`      |
| `language`  | `string`  | nein    | Requested inspection labels (en/de); nl/es use English fallback. `en`, `de`, `nl`, `es` | `en`     |

**Siehe auch:** Geschäftsaktion [`cost_record`](./commands#command-cost_record)

### `notices` — List dunning notices {#command-notices}

Lists retained manual reminders with their invoice membership, optional fee and reversal trace.

**Aufruf**

```text
finance_dunning_notices
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `source_record`, `document`, `ledger_entry`, `business_event` · Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_dunning_notices`](./commands#tool-finance_dunning_notices)

#### `finance_dunning_notices` — Dunning notices {#tool-finance_dunning_notices}

List recorded manual dunning notices with fee and reversal trace.

**Aufruf**

```text
finance_dunning_notices
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage              | Art                        | Standard |
| ----------------------------- | -------------------------- | -------- |
| `MCP finance_dunning_notices` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

List recorded manual reminder evidence with invoice, fee and reversal trace.

**Verwenden, wenn**

- Recorded reminders must be reconciled or selected for reversal.

**Nicht verwenden, wenn**

- Overdue invoices must first be selected for a new reminder.

**Parameter**

Keine Parameter.

**Siehe auch:** Geschäftsaktion [`notices`](./commands#command-notices)

### `contribution_preview` — Preview current contribution candidate {#command-contribution_preview}

Follow an exact whole invoice/order/shipment scope to received net revenue and reviewed consumption;
show known DB1 only, with missing commercial review and selling costs.

**Aufruf**

```text
cost_contribution_preview document_line_id
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `document`, `document_line`, `commitment`, `commitment_revision`, `movement`,
`movement_correction`, `business_event`, `cost_inventory_review`, `cost_inventory_member`,
`cost_policy_revision`, `cost_movement_basis`, `cost_ownership_revision`, `cost_input_manifest` ·
Schreibt: —

**Siehe auch:** Agenten-Tool
[`cost_contribution_preview`](./commands#tool-cost_contribution_preview)

#### `cost_contribution_preview` — Current contribution candidate {#tool-cost_contribution_preview}

Read a bounded exact invoice/shipment candidate and known DB1; no confirmed or historical margin.

**Aufruf**

```text
cost_contribution_preview document_line_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                | Art                        | Standard |
| ------------------------------- | -------------------------- | -------- |
| `MCP cost_contribution_preview` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Preview a current exact revenue and consumption candidate with known DB1 and explicit missing review
basis.

**Verwenden, wenn**

- Explain a single fully billed and shipped item line with current reviewed inventory costs.

**Nicht verwenden, wenn**

- Request final DB1/DB2, historical margin, partial billing, returns or company-wide reports.

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                              | Standard |
| ------------------ | -------- | ------- | ----------------------------------------------------------------------------------------- | -------- |
| `document_line_id` | `string` | ja      | Opaque same-tenant received document line identity; must belong to the selected document. | —        |

**Siehe auch:** Geschäftsaktion [`contribution_preview`](./commands#command-contribution_preview)

### `cost_query` — Read cost query context {#command-cost_query}

Read one admitted inventory or contribution scope with exact retained cutoffs and explicit current
or historical freshness; no global generation claim.

**Aufruf**

```text
cost_query_get kind scope_id [review_id] [effective_at] [knowledge_at] [policy_revision_id]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `business_event`, `cost_attribution_part`, `cost_attribution_revision`,
`cost_component_basis`, `cost_contribution_review`, `cost_input_manifest`, `cost_inventory_member`,
`cost_inventory_review`, `cost_movement_basis`, `cost_ownership_revision`, `cost_policy_revision`,
`cost_receipt_basis`, `cost_revenue_match_basis`, `cost_scope_review`,
`cost_selling_attribution_part`, `cost_selling_review_category`, `cost_selling_review_member`,
`document_line`, `financial_component`, `item` · Schreibt: —

**Siehe auch:** Agenten-Tool [`cost_query_get`](./commands#tool-cost_query_get)

#### `cost_query_get` — Read cost query context {#tool-cost_query_get}

Read one admitted cost scope with its exact retained basis and explicit freshness; not a
company-wide generation.

**Aufruf**

```text
cost_query_get kind scope_id [review_id] [effective_at] [knowledge_at] [policy_revision_id]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage     | Art                        | Standard |
| -------------------- | -------------------------- | -------- |
| `MCP cost_query_get` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read one admitted inventory or contribution scope with constrained cutoffs, exact basis identity and
independent freshness.

**Verwenden, wenn**

- Explain the exact retained basis of an inventory or DB1/DB2 answer.

**Nicht verwenden, wenn**

- Group multiple independently reviewed scopes or activate valuation policies.

**Parameter**

| Name                 | Typ      | Pflicht | Beschreibung                                                                                                                 | Standard |
| -------------------- | -------- | ------- | ---------------------------------------------------------------------------------------------------------------------------- | -------- |
| `kind`               | `string` | ja      | Explicit internal or target reference kind; no inferred tax or country meaning. `inventory`, `contribution`                  | —        |
| `scope_id`           | `string` | ja      | Exact item identity for inventory or received invoice-line identity for contribution.                                        | —        |
| `review_id`          | `string` | nein    | Exact retained inventory or contribution review identity for the selected tool; absence selects its latest review.           | `None`   |
| `effective_at`       | `string` | nein    | UTC instant from which the observation or rule takes effect.                                                                 | `None`   |
| `knowledge_at`       | `string` | nein    | Optional exact retained knowledge cutoff in UTC; mismatches refuse instead of reinterpreting current evidence as historical. | `None`   |
| `policy_revision_id` | `string` | nein    | Optional exact retained valuation-policy constraint; mismatches refuse without activating policy.                            | `None`   |

**Siehe auch:** Geschäftsaktion [`cost_query`](./commands#command-cost_query)

### `dunning_context` — Read dunning context {#command-dunning_context}

Validates one selected reminder scope and returns the finance revision without recording or sending
anything.

**Aufruf**

```text
finance_dunning_context invoice_ids level notice_date [fee_amount] [reason] [number]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation`, `party` · Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_dunning_context`](./commands#tool-finance_dunning_context)

#### `finance_dunning_context` — Dunning context {#tool-finance_dunning_context}

Preview one manual notice from currently overdue invoices and return the finance revision required
for confirmation.

**Aufruf**

```text
finance_dunning_context invoice_ids level notice_date [fee_amount] [reason] [number]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage              | Art                        | Standard |
| ----------------------------- | -------------------------- | -------- |
| `MCP finance_dunning_context` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Validate one manual reminder against current overdue invoices and expose its finance revision.

**Verwenden, wenn**

- A person has selected overdue invoices
- level
- date and optional exact fee for review.

**Nicht verwenden, wenn**

- A reminder should be generated
- escalated or sent automatically.

**Parameter**

| Name          | Typ       | Pflicht | Beschreibung                                                                                   | Standard |
| ------------- | --------- | ------- | ---------------------------------------------------------------------------------------------- | -------- |
| `invoice_ids` | `array`   | ja      | Opaque same-tenant customer-invoice identities explicitly selected for one reminder.           | —        |
| `level`       | `integer` | ja      | Explicit manual reminder level; only the closed levels 1, 2, and 3 are accepted. `1`, `2`, `3` | —        |
| `notice_date` | `string`  | ja      | Calendar date explicitly stated for the manual reminder and its overdue check.                 | —        |
| `fee_amount`  | `string`  | nein    | Exact non-negative reminder fee stated by the confirming human; zero records no fee posting.   | `0`      |
| `reason`      | `string`  | nein    | Human-readable explanation for a hold, correction, or lifecycle change.                        | —        |
| `number`      | `string`  | nein    | Human-facing document or transaction number; it is not internal identity.                      | —        |

**Siehe auch:** Geschäftsaktion [`dunning_context`](./commands#command-dunning_context)

### `notice_detail` — Read dunning notice {#command-notice_detail}

Reads one retained manual reminder with its exact invoice membership, optional fee and reversal
trace.

**Aufruf**

```text
finance_dunning_notice notice_id
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `source_record`, `document`, `ledger_entry`, `business_event` · Schreibt: —

**Siehe auch:** Agenten-Tool [`finance_dunning_notice`](./commands#tool-finance_dunning_notice)

#### `finance_dunning_notice` — Dunning notice {#tool-finance_dunning_notice}

Read one recorded manual dunning notice with fee and reversal trace.

**Aufruf**

```text
finance_dunning_notice notice_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage             | Art                        | Standard |
| ---------------------------- | -------------------------- | -------- |
| `MCP finance_dunning_notice` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read one retained manual reminder with its exact invoice membership, fee and reversal.

**Verwenden, wenn**

- One known notice identity needs authoritative reconciliation.

**Nicht verwenden, wenn**

- A notice has not yet been discovered or recorded.

**Parameter**

| Name        | Typ      | Pflicht | Beschreibung                                                 | Standard |
| ----------- | -------- | ------- | ------------------------------------------------------------ | -------- |
| `notice_id` | `string` | ja      | Opaque same-tenant identity of the retained manual reminder. | —        |

**Siehe auch:** Geschäftsaktion [`notice_detail`](./commands#command-notice_detail)

### `receipt_cost` — Read receipt acquisition costs {#command-receipt_cost}

Derive receipt costs from exact received amounts and explicit owner decisions; retain sealed
reviewed knowledge and keep incomplete costs unknown.

**Aufruf**

```text
cost_receipt_get movement_id [manifest_id]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `movement`, `document`, `document_line`, `source_record`, `financial_component`,
`cost_receipt_basis`, `cost_attribution_revision`, `cost_attribution_part`, `cost_scope_review`,
`cost_input_manifest` · Schreibt: —

**Siehe auch:** Agenten-Tool [`cost_receipt_get`](./commands#tool-cost_receipt_get)

#### `cost_receipt_get` — Receipt acquisition costs {#tool-cost_receipt_get}

Read known costs, reviewed completeness and an exact retained manifest. Missing costs stay unknown.

**Aufruf**

```text
cost_receipt_get movement_id [manifest_id]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage       | Art                        | Standard |
| ---------------------- | -------------------------- | -------- |
| `MCP cost_receipt_get` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read receipt acquisition costs, category coverage and exact retained review history.

**Verwenden, wenn**

- Explain receipt costs before or after explicit review.

**Nicht verwenden, wenn**

- Determine inventory book value or contribution margin.

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung                                                                         | Standard |
| ------------- | -------- | ------- | ------------------------------------------------------------------------------------ | -------- |
| `movement_id` | `string` | ja      | Opaque identity of the immutable physical Movement being inspected or corrected.     | —        |
| `manifest_id` | `string` | nein    | Opaque sealed receipt review input set; absence requests current retained knowledge. | `None`   |

**Siehe auch:** Geschäftsaktion [`receipt_cost`](./commands#command-receipt_cost)

### `cost_evidence` — Read received acquisition-cost evidence {#command-cost_evidence}

Derive receipt costs from exact received amounts and explicit owner decisions; retain sealed
reviewed knowledge and keep incomplete costs unknown.

**Aufruf**

```text
cost_evidence_get document_id [document_line_id]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `movement`, `document`, `document_line`, `source_record`, `financial_component`,
`cost_receipt_basis`, `cost_attribution_revision`, `cost_attribution_part`, `cost_scope_review`,
`cost_input_manifest` · Schreibt: —

**Siehe auch:** Agenten-Tool [`cost_evidence_get`](./commands#tool-cost_evidence_get)

#### `cost_evidence_get` — Received cost evidence {#tool-cost_evidence_get}

Read stated supplier invoice or credit amounts and their evidence fingerprint without writing.

**Aufruf**

```text
cost_evidence_get document_id [document_line_id]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage        | Art                        | Standard |
| ----------------------- | -------------------------- | -------- |
| `MCP cost_evidence_get` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read stated supplier invoice or credit amounts and their evidence fingerprint without writing.

**Verwenden, wenn**

- Explain receipt costs before or after explicit review.

**Nicht verwenden, wenn**

- Determine inventory book value or contribution margin.

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                              | Standard |
| ------------------ | -------- | ------- | ----------------------------------------------------------------------------------------- | -------- |
| `document_id`      | `string` | ja      | Opaque identity of the evidence document to inspect or correct.                           | —        |
| `document_line_id` | `string` | nein    | Opaque same-tenant received document line identity; must belong to the selected document. | `None`   |

**Siehe auch:** Geschäftsaktion [`cost_evidence`](./commands#command-cost_evidence)

### `reviewed_contribution` — Read reviewed commercial contribution {#command-reviewed_contribution}

Derive confirmed whole-line DB1 and independently reviewed DB2, or reproduce their exact retained
historical basis.

**Aufruf**

```text
cost_contribution_get document_line_id [review_id]
```

**Erreichbar über:** CLI · Web · MCP · Chat

**Wirkung:** Liest: `cost_selling_attribution_part`, `cost_selling_review_category`,
`cost_selling_review_member`, `cost_attribution_revision`, `cost_component_basis`,
`cost_conversion_basis_revision`, `financial_component`, `document_line`, `business_event`,
`cost_revenue_match_basis`, `cost_contribution_review`, `cost_inventory_member`,
`cost_inventory_review`, `cost_movement_basis`, `cost_input_manifest` · Schreibt: —

**Siehe auch:** Agenten-Tool [`cost_contribution_get`](./commands#tool-cost_contribution_get)

#### `cost_contribution_get` — Reviewed commercial contribution {#tool-cost_contribution_get}

Read confirmed DB1 and independently reviewed DB2 for one whole invoice/shipment scope or its exact
historical review.

**Aufruf**

```text
cost_contribution_get document_line_id [review_id]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage            | Art                        | Standard |
| --------------------------- | -------------------------- | -------- |
| `MCP cost_contribution_get` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read confirmed DB1 and independently reviewed DB2 for one full invoice line and shipment from
retained inputs.

**Verwenden, wenn**

- Explain a confirmed single-line DB1 or reproduce a specific historical contribution review.

**Nicht verwenden, wenn**

- Request partial revenue matching, rematching, HGB value or company-wide reports.

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                                                       | Standard |
| ------------------ | -------- | ------- | ------------------------------------------------------------------------------------------------------------------ | -------- |
| `document_line_id` | `string` | ja      | Opaque same-tenant received document line identity; must belong to the selected document.                          | —        |
| `review_id`        | `string` | nein    | Exact retained inventory or contribution review identity for the selected tool; absence selects its latest review. | `None`   |

**Siehe auch:** Geschäftsaktion [`reviewed_contribution`](./commands#command-reviewed_contribution)

### `record_notice` — Record dunning notice {#command-record_notice}

Records one explicitly reviewed manual reminder and optional exact stated fee without sending a
message.

**Aufruf**

```text
finance_dunning_record_propose expected_revision invoice_ids level notice_date [fee_amount] [reason] [number]
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `document`, `ledger_entry`, `settlement_allocation`, `party` · Schreibt:
`source_record`, `document`, `ledger_entry`, `business_event` · Erzeugt: `dunning.notice_recorded`

**Siehe auch:** Agenten-Tool
[`finance_dunning_record_propose`](./commands#tool-finance_dunning_record_propose), Event
[`dunning.notice_recorded`](./events#event-dunning-notice_recorded)

#### `finance_dunning_record_propose` — Record dunning notice {#tool-finance_dunning_record_propose}

Prepare a manual dunning notice and optional exact stated fee for owner confirmation.

**Aufruf**

```text
finance_dunning_record_propose expected_revision invoice_ids level notice_date [fee_amount] [reason] [number]
```

**Zugriff:** `propose`

Record one owner-confirmed manual reminder and optional exact stated fee.

**Verwenden, wenn**

- A person has reviewed eligible overdue invoices and explicitly chosen the level and fee.

**Nicht verwenden, wenn**

- A reminder should be calculated
- escalated or sent automatically.

**Voraussetzungen**

- Invoices belong to one customer and currency and remain open and overdue.

**Abgelehnt, wenn**

- `invalid_dunning_scope` — Invoice eligibility

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                                   | Standard |
| ------------------- | --------- | ------- | ---------------------------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.                    | —        |
| `invoice_ids`       | `array`   | ja      | Opaque same-tenant customer-invoice identities explicitly selected for one reminder.           | —        |
| `level`             | `integer` | ja      | Explicit manual reminder level; only the closed levels 1, 2, and 3 are accepted. `1`, `2`, `3` | —        |
| `notice_date`       | `string`  | ja      | Calendar date explicitly stated for the manual reminder and its overdue check.                 | —        |
| `fee_amount`        | `string`  | nein    | Exact non-negative reminder fee stated by the confirming human; zero records no fee posting.   | `0`      |
| `reason`            | `string`  | nein    | Human-readable explanation for a hold, correction, or lifecycle change.                        | —        |
| `number`            | `string`  | nein    | Human-facing document or transaction number; it is not internal identity.                      | —        |

**Prüfen mit:** `finance.dunning.notice` — Exact notice membership and fee effect are retained.

**Siehe auch:** Geschäftsaktion [`record_notice`](./commands#command-record_notice)

### `reverse_notice` — Reverse dunning notice {#command-reverse_notice}

Retains the original reminder and explicitly reverses its fee effect and reminder state.

**Aufruf**

```text
finance_dunning_reverse_propose expected_revision notice_id reason
```

**Erreichbar über:** Web · MCP · Chat

**Wirkung:** Liest: `source_record`, `document`, `ledger_entry`, `business_event` · Schreibt:
`ledger_reversal`, `ledger_entry`, `business_event` · Erzeugt: `dunning.notice_reversed`

**Siehe auch:** Agenten-Tool
[`finance_dunning_reverse_propose`](./commands#tool-finance_dunning_reverse_propose), Event
[`dunning.notice_reversed`](./events#event-dunning-notice_reversed)

#### `finance_dunning_reverse_propose` — Reverse dunning notice {#tool-finance_dunning_reverse_propose}

Prepare reversal of one manual dunning notice and any posted fee for owner confirmation.

**Aufruf**

```text
finance_dunning_reverse_propose expected_revision notice_id reason
```

**Zugriff:** `propose`

Reverse one owner-confirmed manual reminder and its fee effect without deleting evidence.

**Verwenden, wenn**

- A recorded notice was issued in error and a person explicitly decides to reverse it.

**Nicht verwenden, wenn**

- The notice is correct or only its external message needs correction.

**Voraussetzungen**

- The tenant-owned notice exists and is not already reversed.

**Abgelehnt, wenn**

- `invalid_dunning_reversal` — Notice is foreign

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |
| `notice_id`         | `string`  | ja      | Opaque same-tenant identity of the retained manual reminder.                | —        |
| `reason`            | `string`  | ja      | Human-readable explanation for a hold, correction, or lifecycle change.     | —        |

**Prüfen mit:** `finance.dunning.notice` — Reversal identity and fee outcome are retained.

**Siehe auch:** Geschäftsaktion [`reverse_notice`](./commands#command-reverse_notice)

## Agenten-Tools ohne Geschäftsaktion

Diese Agenten-Tools stehen für keine einzelne Geschäftsaktion. Lese-Tools beantworten eine Sicht
oder Projection; Steuerungs-Tools tragen Vorschläge, Erkundung und fehlende Informationen.

| Schlüssel                                                                                        | Bezeichnung                                    | Zugriff   | Beantwortet            |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------- | --------- | ---------------------- |
| [`capability_catalog`](#tool-capability_catalog)                                                 | Discover business capabilities                 | `read`    | —                      |
| [`capability_describe`](#tool-capability_describe)                                               | Describe an agent capability                   | `read`    | —                      |
| [`business_records_discover`](#tool-business_records_discover)                                   | Discover business records                      | `read`    | —                      |
| [`inventory_read`](#tool-inventory_read)                                                         | Read inventory                                 | `read`    | `inventory`            |
| [`commitments_list`](#tool-commitments_list)                                                     | List commitments                               | `read`    | `commitment_register`  |
| [`shipments_list`](#tool-shipments_list)                                                         | List physical shipments                        | `read`    | —                      |
| [`shipment_explain`](#tool-shipment_explain)                                                     | Explain a physical shipment                    | `read`    | —                      |
| [`fulfillment_queue`](#tool-fulfillment_queue)                                                   | Read fulfillment queue                         | `read`    | `fulfillment_queue`    |
| [`fulfillment_readiness`](#tool-fulfillment_readiness)                                           | Read fulfillment readiness                     | `read`    | —                      |
| [`fulfillment_blockers`](#tool-fulfillment_blockers)                                             | Read fulfillment blockers                      | `read`    | `fulfillment_blockers` |
| [`item_supply_demand`](#tool-item_supply_demand)                                                 | Read item supply and demand                    | `read`    | `item_supply_demand`   |
| [`order_explain`](#tool-order_explain)                                                           | Explain an order                               | `read`    | —                      |
| [`exceptions_list`](#tool-exceptions_list)                                                       | List operational exceptions                    | `read`    | —                      |
| [`interpretation_coverage`](#tool-interpretation_coverage)                                       | Read interpretation coverage                   | `read`    | —                      |
| [`exception_explain`](#tool-exception_explain)                                                   | Explain an operational exception               | `read`    | —                      |
| [`proposals_awaiting_approval`](#tool-proposals_awaiting_approval)                               | List proposals awaiting approval               | `read`    | —                      |
| [`proposal_execution_status`](#tool-proposal_execution_status)                                   | Reconcile proposal execution                   | `read`    | —                      |
| [`proposal_approve_and_execute`](#tool-proposal_approve_and_execute)                             | Approve and execute a proposal                 | `confirm` | —                      |
| [`proposal_reject`](#tool-proposal_reject)                                                       | Reject a proposal                              | `confirm` | —                      |
| [`finance_balances`](#tool-finance_balances)                                                     | Read finance balances                          | `read`    | —                      |
| [`reality_gaps`](#tool-reality_gaps)                                                             | List missing information                       | `read`    | —                      |
| [`reality_gap_get`](#tool-reality_gap_get)                                                       | Inspect missing information                    | `read`    | —                      |
| [`reality_gap_simulate`](#tool-reality_gap_simulate)                                             | Simulate Fact rule                             | `read`    | —                      |
| [`reality_gap_create_propose`](#tool-reality_gap_create_propose)                                 | Propose missing information                    | `propose` | —                      |
| [`reality_gap_entry_add_propose`](#tool-reality_gap_entry_add_propose)                           | Propose investigation entry                    | `propose` | —                      |
| [`reality_gap_recommend_propose`](#tool-reality_gap_recommend_propose)                           | Propose modeling recommendation                | `propose` | —                      |
| [`reality_gap_decide_propose`](#tool-reality_gap_decide_propose)                                 | Propose classification decision                | `propose` | —                      |
| [`reality_gap_implementation_prepare_propose`](#tool-reality_gap_implementation_prepare_propose) | Propose gap implementation                     | `propose` | —                      |
| [`reality_gap_rule_activate_propose`](#tool-reality_gap_rule_activate_propose)                   | Propose rule activation                        | `propose` | —                      |
| [`reality_gap_rule_disable_propose`](#tool-reality_gap_rule_disable_propose)                     | Propose rule disablement                       | `propose` | —                      |
| [`reality_gap_rule_replay_propose`](#tool-reality_gap_rule_replay_propose)                       | Propose historical replay                      | `propose` | —                      |
| [`supply_coverage`](#tool-supply_coverage)                                                       | Supply coverage                                | `read`    | —                      |
| [`movement_explanation`](#tool-movement_explanation)                                             | Movement explanation                           | `read`    | —                      |
| [`return_disposition_summary`](#tool-return_disposition_summary)                                 | Return disposition summary                     | `read`    | —                      |
| [`finance_credits`](#tool-finance_credits)                                                       | Available credit                               | `read`    | —                      |
| [`finance_party_balances`](#tool-finance_party_balances)                                         | Party balances                                 | `read`    | —                      |
| [`finance_payments`](#tool-finance_payments)                                                     | Recorded payments                              | `read`    | —                      |
| [`graph_company_generation_current`](#tool-graph_company_generation_current)                     | Read current published company cost generation | `read`    | —                      |
| [`graph_captured_reports_list`](#tool-graph_captured_reports_list)                               | List captured report generations               | `read`    | —                      |
| [`graph_contribution_reviews_list`](#tool-graph_contribution_reviews_list)                       | List confirmed contribution valuations         | `read`    | —                      |
| [`graph_inventory_reviews_list`](#tool-graph_inventory_reviews_list)                             | List confirmed inventory valuations            | `read`    | —                      |
| [`graph_catalog`](#tool-graph_catalog)                                                           | Discover the business graph                    | `read`    | —                      |
| [`graph_templates`](#tool-graph_templates)                                                       | List report templates                          | `read`    | —                      |
| [`graph_ask`](#tool-graph_ask)                                                                   | Ask the business graph                         | `read`    | —                      |
| [`graph_format`](#tool-graph_format)                                                             | Format an analysis query                       | `read`    | —                      |
| [`graph_interpret`](#tool-graph_interpret)                                                       | Interpret an analysis question                 | `read`    | —                      |
| [`graph_reports_list`](#tool-graph_reports_list)                                                 | List my graph reports                          | `read`    | —                      |
| [`graph_report_get`](#tool-graph_report_get)                                                     | Read my graph report                           | `read`    | —                      |
| [`graph_requests_list`](#tool-graph_requests_list)                                               | List my requested analyses                     | `read`    | —                      |
| [`graph_request_get`](#tool-graph_request_get)                                                   | Collect a requested analysis                   | `read`    | —                      |
| [`graph_request_propose`](#tool-graph_request_propose)                                           | Request an analysis                            | `propose` | —                      |

### `capability_catalog` — Discover business capabilities {#tool-capability_catalog}

Start here. Without arguments it lists the business areas this company's Reality covers; with one
topic it lists that area's capabilities, the tools behind each, and whether this credential may call
them.

**Aufruf**

```text
capability_catalog [topic]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage         | Art                        | Standard |
| ------------------------ | -------------------------- | -------- |
| `MCP capability_catalog` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Parameter**

| Name    | Typ      | Pflicht | Beschreibung | Standard |
| ------- | -------- | ------- | ------------ | -------- |
| `topic` | `string` | nein    | —            | —        |

### `capability_describe` — Describe an agent capability {#tool-capability_describe}

Read when one public mutation should or should not be used, its expected refusals, and how to verify
its outcome.

**Aufruf**

```text
capability_describe tool_name
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage          | Art                        | Standard |
| ------------------------- | -------------------------- | -------- |
| `MCP capability_describe` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Parameter**

| Name        | Typ      | Pflicht | Beschreibung | Standard |
| ----------- | -------- | ------- | ------------ | -------- |
| `tool_name` | `string` | ja      | —            | —        |

### `business_records_discover` — Discover business records {#tool-business_records_discover}

Read tenant-scoped business records as complete cursor pages with metadata; explicit legacy mode is
a bounded lookup.

**Aufruf**

```text
business_records_discover [response_format] [limit] [cursor] family [query] [record_id]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                | Art                        | Standard |
| ------------------------------- | -------------------------- | -------- |
| `MCP business_records_discover` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Find bounded tenant-owned business records and their opaque identities before a precise read or
proposal.

**Verwenden, wenn**

- The correct opaque record identity is not yet known.

**Nicht verwenden, wenn**

- A selected record needs complete explanation or an effect needs verification.

**Parameter**

| Name              | Typ       | Pflicht | Beschreibung                                                                                                                                                                                                                                                    | Standard |
| ----------------- | --------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `response_format` | `string`  | nein    | Page returns records, continuation and metadata; legacy preserves the old list shape. `page`, `legacy`                                                                                                                                                          | `page`   |
| `limit`           | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                                                                                                                                                                                                 | `25`     |
| `cursor`          | `string`  | nein    | Continuation for the same tenant, read and filters. Live pages are not a snapshot.                                                                                                                                                                              | `None`   |
| `family`          | `string`  | ja      | `party`, `item`, `location`, `document`, `commitment`, `movement`, `reservation`, `handling_unit`, `lot`, `serial_unit`, `payment_term`, `price_list`, `price_list_entry`, `party_group`, `ledger_entry`, `source_system`, `source_capability`, `source_record` | —        |
| `query`           | `string`  | nein    | Optional invoice-number search within matching same-party credit targets.                                                                                                                                                                                       | —        |
| `record_id`       | `string`  | nein    | Opaque identity of the master-data record whose lifecycle is being changed.                                                                                                                                                                                     | —        |

### `inventory_read` — Read inventory {#tool-inventory_read}

Read inventory as cursor pages: labelled item totals or item/location rows with units. Page mode
does not write projection caches.

**Aufruf**

```text
inventory_read [response_format] [limit] [cursor] [view] [item_id] [location_id]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                             | Art                                        | Standard |
| -------------------------------------------- | ------------------------------------------ | -------- |
| `MCP inventory_read(response_format=page)`   | Live — beim Aufruf gelesen                 | ja       |
| `MCP inventory_read(response_format=legacy)` | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read physical, reserved, and available stock with explicit item aggregation or item/location scope;
page mode supports item_id and location_id filters.

**Verwenden, wenn**

- A stock
- allocation
- or availability consequence must be inspected.

**Nicht verwenden, wenn**

- A customer promise
- source interpretation
- or external delivery event is the question.

**Parameter**

| Name              | Typ       | Pflicht | Beschreibung                                                                                           | Standard    |
| ----------------- | --------- | ------- | ------------------------------------------------------------------------------------------------------ | ----------- |
| `response_format` | `string`  | nein    | Page returns records, continuation and metadata; legacy preserves the old list shape. `page`, `legacy` | `page`      |
| `limit`           | `integer` | nein    | Maximum records per page; legacy operational lists retain their full-list behavior.                    | `25`        |
| `cursor`          | `string`  | nein    | Continuation for the same tenant, read and filters. Live pages are not a snapshot.                     | `None`      |
| `view`            | `string`  | nein    | `aggregate`, `location`                                                                                | `aggregate` |
| `item_id`         | `string`  | nein    | Opaque identity of the operational item reference.                                                     | —           |
| `location_id`     | `string`  | nein    | Opaque identity of the operational or physical location.                                               | —           |

**Siehe auch:** Projection [`inventory`](./views#projection-inventory)

### `commitments_list` — List commitments {#tool-commitments_list}

Customer and supplier obligations with quantity, due date, and status.

**Aufruf**

```text
commitments_list [response_format] [limit] [cursor]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                               | Art                                        | Standard |
| ---------------------------------------------- | ------------------------------------------ | -------- |
| `MCP commitments_list(response_format=page)`   | Live — beim Aufruf gelesen                 | ja       |
| `MCP commitments_list(response_format=legacy)` | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read current customer and supplier obligations and their derived fulfillment state.

**Verwenden, wenn**

- Promises
- due quantities
- allocation context
- or fulfillment progress must be inspected.

**Nicht verwenden, wenn**

- Physical stock across commitments or source-processing success is the question.

**Parameter**

| Name              | Typ       | Pflicht | Beschreibung                                                                                           | Standard |
| ----------------- | --------- | ------- | ------------------------------------------------------------------------------------------------------ | -------- |
| `response_format` | `string`  | nein    | Page returns records, continuation and metadata; legacy preserves the old list shape. `page`, `legacy` | `page`   |
| `limit`           | `integer` | nein    | Maximum records per page; legacy operational lists retain their full-list behavior.                    | `25`     |
| `cursor`          | `string`  | nein    | Continuation for the same tenant, read and filters. Live pages are not a snapshot.                     | `None`   |

**Siehe auch:** Projection [`commitment_register`](./views#projection-commitment_register)

### `shipments_list` — List physical shipments {#tool-shipments_list}

List real incoming or outgoing consignments and packages; these are distinct from delivery
commitments.

**Aufruf**

```text
shipments_list [page] [size] [query] [direction] [purpose] [counterparty_id] [carrier] [tracking] [created_from] [created_to] [observation]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage     | Art                        | Standard |
| -------------------- | -------------------------- | -------- |
| `MCP shipments_list` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

List real physical consignments and packages separately from delivery commitments.

**Verwenden, wenn**

- Physical dispatch
- receipt
- carrier
- tracking
- or externally reported delivery must be inspected.

**Nicht verwenden, wenn**

- The question is only what was promised or currently remains open.

**Parameter**

| Name              | Typ       | Pflicht | Beschreibung                                                                                                                                                                              | Standard |
| ----------------- | --------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `page`            | `integer` | nein    | One-based page of retained membership, bounded to 25 records per page.                                                                                                                    | `1`      |
| `size`            | `integer` | nein    | —                                                                                                                                                                                         | `50`     |
| `query`           | `string`  | nein    | Optional invoice-number search within matching same-party credit targets.                                                                                                                 | —        |
| `direction`       | `string`  | nein    | Business flow direction, such as sales or purchase, incoming or outgoing. ``, `inbound`, `outbound`                                                                                       | —        |
| `purpose`         | `string`  | nein    | Closed business purpose that determines the shipment's counterparty role and compatible Movement type. ``, `customer_delivery`, `supplier_delivery`, `customer_return`, `supplier_return` | —        |
| `counterparty_id` | `string`  | nein    | Opaque identity of the customer or supplier Party in an order flow.                                                                                                                       | —        |
| `carrier`         | `string`  | nein    | Carrier name stated for a physical package; it is descriptive and not an internal identity.                                                                                               | —        |
| `tracking`        | `string`  | nein    | —                                                                                                                                                                                         | —        |
| `created_from`    | `string`  | nein    | —                                                                                                                                                                                         | —        |
| `created_to`      | `string`  | nein    | —                                                                                                                                                                                         | —        |
| `observation`     | `string`  | nein    | ``, `announced`, `dispatched`, `received`, `externally_delivered`, `has_exception`                                                                                                        | —        |

### `shipment_explain` — Explain a physical shipment {#tool-shipment_explain}

Explain one consignment through packages, tracking observations, effective Movements, and source
links without treating dispatch as delivery.

**Aufruf**

```text
shipment_explain shipment_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage       | Art                        | Standard |
| ---------------------- | -------------------------- | -------- |
| `MCP shipment_explain` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Explain one physical Shipment through Packages, current events, effective Movements, and sources.

**Verwenden, wenn**

- One known Shipment needs exact contents
- tracking history
- and proof boundaries.

**Nicht verwenden, wenn**

- The Shipment identity is unknown or only aggregate promise fulfillment is required.

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung                                               | Standard |
| ------------- | -------- | ------- | ---------------------------------------------------------- | -------- |
| `shipment_id` | `string` | ja      | Opaque identity of the tenant-scoped physical consignment. | —        |

### `fulfillment_queue` — Read fulfillment queue {#tool-fulfillment_queue}

Orders with ship readiness, lines, shortages, holds, and source identity.

**Aufruf**

```text
fulfillment_queue [response_format] [limit] [cursor]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                | Art                                        | Standard |
| ----------------------------------------------- | ------------------------------------------ | -------- |
| `MCP fulfillment_queue(response_format=page)`   | Live — beim Aufruf gelesen                 | ja       |
| `MCP fulfillment_queue(response_format=legacy)` | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read the derived open-order work queue with readiness, shortages, holds, and source identity.

**Verwenden, wenn**

- Fulfillment work must be prioritized or readiness compared across orders.

**Nicht verwenden, wenn**

- One blocker needs causal detail or one order needs its full trace.

**Parameter**

| Name              | Typ       | Pflicht | Beschreibung                                                                                           | Standard |
| ----------------- | --------- | ------- | ------------------------------------------------------------------------------------------------------ | -------- |
| `response_format` | `string`  | nein    | Page returns records, continuation and metadata; legacy preserves the old list shape. `page`, `legacy` | `page`   |
| `limit`           | `integer` | nein    | Maximum records per page; legacy operational lists retain their full-list behavior.                    | `25`     |
| `cursor`          | `string`  | nein    | Continuation for the same tenant, read and filters. Live pages are not a snapshot.                     | `None`   |

**Siehe auch:** Projection [`fulfillment_queue`](./views#projection-fulfillment_queue)

### `fulfillment_readiness` — Read fulfillment readiness {#tool-fulfillment_readiness}

Canonical blockers, payment amounts, and evidence for one delivery commitment.

**Aufruf**

```text
fulfillment_readiness commitment_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage            | Art                        | Standard |
| --------------------------- | -------------------------- | -------- |
| `MCP fulfillment_readiness` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read the canonical current fulfillment decision for one customer-delivery commitment.

**Verwenden, wenn**

- A shipment decision needs exact blocker codes
- prepayment amounts
- and opaque evidence identifiers.

**Nicht verwenden, wenn**

- A shipment or payment should be created or changed.

**Parameter**

| Name            | Typ      | Pflicht | Beschreibung                                                         | Standard |
| --------------- | -------- | ------- | -------------------------------------------------------------------- | -------- |
| `commitment_id` | `string` | ja      | Opaque identity of the obligation being reserved, held, or executed. | —        |

### `fulfillment_blockers` — Read fulfillment blockers {#tool-fulfillment_blockers}

Current order and item blockers with their affected operational records.

**Aufruf**

```text
fulfillment_blockers [response_format] [limit] [cursor]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                   | Art                                        | Standard |
| -------------------------------------------------- | ------------------------------------------ | -------- |
| `MCP fulfillment_blockers(response_format=page)`   | Live — beim Aufruf gelesen                 | ja       |
| `MCP fulfillment_blockers(response_format=legacy)` | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read registered order and item conditions that currently block fulfillment.

**Verwenden, wenn**

- An order is not ready and its derived blocker and affected Reality records are needed.

**Nicht verwenden, wenn**

- A complete order trace or proof that every possible blocker is modeled is required.

**Parameter**

| Name              | Typ       | Pflicht | Beschreibung                                                                                           | Standard |
| ----------------- | --------- | ------- | ------------------------------------------------------------------------------------------------------ | -------- |
| `response_format` | `string`  | nein    | Page returns records, continuation and metadata; legacy preserves the old list shape. `page`, `legacy` | `page`   |
| `limit`           | `integer` | nein    | Maximum records per page; legacy operational lists retain their full-list behavior.                    | `25`     |
| `cursor`          | `string`  | nein    | Continuation for the same tenant, read and filters. Live pages are not a snapshot.                     | `None`   |

**Siehe auch:** Projection [`fulfillment_blockers`](./views#projection-fulfillment_blockers)

### `item_supply_demand` — Read item supply and demand {#tool-item_supply_demand}

Stock, incoming supply, customer demand, shortages, and blocked orders by item.

**Aufruf**

```text
item_supply_demand [response_format] [limit] [cursor]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                 | Art                                        | Standard |
| ------------------------------------------------ | ------------------------------------------ | -------- |
| `MCP item_supply_demand(response_format=page)`   | Live — beim Aufruf gelesen                 | ja       |
| `MCP item_supply_demand(response_format=legacy)` | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read derived stock, incoming supply, demand, shortages, and affected orders by item.

**Verwenden, wenn**

- Item-level supply pressure or demand contributing to shortages must be assessed.

**Nicht verwenden, wenn**

- Exact location stock or external supplier delivery must be proven.

**Parameter**

| Name              | Typ       | Pflicht | Beschreibung                                                                                           | Standard |
| ----------------- | --------- | ------- | ------------------------------------------------------------------------------------------------------ | -------- |
| `response_format` | `string`  | nein    | Page returns records, continuation and metadata; legacy preserves the old list shape. `page`, `legacy` | `page`   |
| `limit`           | `integer` | nein    | Maximum records per page; legacy operational lists retain their full-list behavior.                    | `25`     |
| `cursor`          | `string`  | nein    | Continuation for the same tenant, read and filters. Live pages are not a snapshot.                     | `None`   |

**Siehe auch:** Projection [`item_supply_demand`](./views#projection-item_supply_demand)

### `order_explain` — Explain an order {#tool-order_explain}

Explain retained open, fulfilled or cancelled orders by opaque ID with Source, Evidence and Reality
links; not a historical snapshot.

**Aufruf**

```text
order_explain order_reference
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage    | Art                        | Standard |
| ------------------- | -------------------------- | -------- |
| `MCP order_explain` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Trace one selected order through immutable source, Document Evidence, Commitments, reservations,
movements, and derived fulfillment.

**Verwenden, wenn**

- One known order needs an explainable Source-to-Reality trace.

**Nicht verwenden, wenn**

- The order identity is unknown or aggregate inventory across orders is required.

**Parameter**

| Name              | Typ      | Pflicht | Beschreibung | Standard |
| ----------------- | -------- | ------- | ------------ | -------- |
| `order_reference` | `string` | ja      | —            | —        |

### `exceptions_list` — List operational exceptions {#tool-exceptions_list}

Current tenant-scoped derived conditions that require attention; these are not tickets.

**Aufruf**

```text
exceptions_list
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage      | Art                        | Standard |
| --------------------- | -------------------------- | -------- |
| `MCP exceptions_list` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

List currently derived tenant conditions that require operational attention.

**Verwenden, wenn**

- An agent needs a bounded queue of known operational blockers or inconsistencies.

**Nicht verwenden, wenn**

- A complete health audit or proof that no unknown problem exists is required.

**Parameter**

Keine Parameter.

### `interpretation_coverage` — Read interpretation coverage {#tool-interpretation_coverage}

List source interpretation outcomes and produced Reality identities without raw payloads.

**Aufruf**

```text
interpretation_coverage [source_record_id]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage              | Art                        | Standard |
| ----------------------------- | -------------------------- | -------- |
| `MCP interpretation_coverage` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Explain whether immutable sources were interpreted and which opaque Reality identities each attempt
produced.

**Verwenden, wenn**

- A source-processing outcome
- retry history
- or produced-record identity is needed.

**Nicht verwenden, wenn**

- Current business state or proof that a produced record remains operationally valid is required.

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                 | Standard |
| ------------------ | -------- | ------- | ---------------------------------------------------------------------------- | -------- |
| `source_record_id` | `string` | nein    | Opaque identity of the immutable source record supporting this typed record. | —        |

### `exception_explain` — Explain an operational exception {#tool-exception_explain}

Return one current exception and the Reality context from which it is derived.

**Aufruf**

```text
exception_explain exception_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage        | Art                        | Standard |
| ----------------------- | -------------------------- | -------- |
| `MCP exception_explain` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Explain one selected current exception through the Reality context from which it derives.

**Verwenden, wenn**

- A known exception identity needs its current derivation and affected records.

**Nicht verwenden, wenn**

- Exceptions must first be discovered or historical conditions are requested.

**Parameter**

| Name           | Typ      | Pflicht | Beschreibung | Standard |
| -------------- | -------- | ------- | ------------ | -------- |
| `exception_id` | `string` | ja      | —            | —        |

### `proposals_awaiting_approval` — List proposals awaiting approval {#tool-proposals_awaiting_approval}

Auditable changes that have been prepared but not executed.

**Aufruf**

```text
proposals_awaiting_approval
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                  | Art                        | Standard |
| --------------------------------- | -------------------------- | -------- |
| `MCP proposals_awaiting_approval` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

List tenant change proposals that still await an explicit authorized decision.

**Verwenden, wenn**

- The current governed review queue is needed before approval or rejection.

**Nicht verwenden, wenn**

- Executed Reality
- rejected history
- or proof of an effect is required.

**Parameter**

Keine Parameter.

### `proposal_execution_status` — Reconcile proposal execution {#tool-proposal_execution_status}

Read one proposal lifecycle and verify its stored receipt against authoritative Reality records.

**Aufruf**

```text
proposal_execution_status proposal_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                | Art                        | Standard |
| ------------------------------- | -------------------------- | -------- |
| `MCP proposal_execution_status` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Reconcile one confirmation lifecycle and validate its stored receipt against authoritative Reality
records.

**Verwenden, wenn**

- A confirmation response was lost
- execution is indeterminate
- or an exact effect needs verification.

**Nicht verwenden, wenn**

- A caller wants to approve
- retry
- or infer downstream fulfilment from a reservation.

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung | Standard |
| ------------- | -------- | ------- | ------------ | -------- |
| `proposal_id` | `string` | ja      | —            | —        |

### `proposal_approve_and_execute` — Approve and execute a proposal {#tool-proposal_approve_and_execute}

Settle one exact proposal by explicit authorized decision and execute it through the shared
application boundary.

**Aufruf**

```text
proposal_approve_and_execute proposal_id [approved] [review_token]
```

**Zugriff:** `confirm`

Apply one exact prepared mutation after an explicit authorized decision through a single-use Reality
execution boundary.

**Verwenden, wenn**

- An authorized person or agent explicitly decides the exact pending proposal preview.

**Nicht verwenden, wenn**

- Approval is inferred from model output, credentials, connection, or prior similar decisions.
- The proposal is executing, rejected, unknown, foreign, or no longer matches the intended action.

**Voraussetzungen**

- The proposal belongs to the selected tenant
- remains proposed
- and approved is explicitly true.

**Abgelehnt, wenn**

- `approval_required` — approved=true was not supplied for an explicit authorized decision.
- `execution_unknown` — The proposal is already executing and cannot be safely retried.
- `proposal_settled` — The proposal was rejected or otherwise cannot be confirmed.
- `proposal_not_found` — No proposal is visible in the selected tenant.

**Parameter**

| Name           | Typ       | Pflicht | Beschreibung | Standard |
| -------------- | --------- | ------- | ------------ | -------- |
| `proposal_id`  | `string`  | ja      | —            | —        |
| `approved`     | `boolean` | nein    | —            | `False`  |
| `review_token` | `string`  | nein    | —            | —        |

**Prüfen mit:** `proposal_execution_status` — Correlated execution evidence and current
Reservation/Commitment values match the stored receipt.; `business_records_discover` — Named
operational records remain visible with current tenant-scoped values.

### `proposal_reject` — Reject a proposal {#tool-proposal_reject}

Reject one pending proposal by explicit authorized decision without business effect.

**Aufruf**

```text
proposal_reject proposal_id rejected
```

**Zugriff:** `confirm`

**Parameter**

| Name          | Typ       | Pflicht | Beschreibung | Standard |
| ------------- | --------- | ------- | ------------ | -------- |
| `proposal_id` | `string`  | ja      | —            | —        |
| `rejected`    | `boolean` | ja      | —            | —        |

### `finance_balances` — Read finance balances {#tool-finance_balances}

Read balances per recorded currency with metadata. Never converts or adds different currencies;
returns balances, not legacy EUR fields.

**Aufruf**

```text
finance_balances
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage       | Art                        | Standard |
| ---------------------- | -------------------------- | -------- |
| `MCP finance_balances` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read receivable and payable positions derived from tenant LedgerEntries.

**Verwenden, wenn**

- Current ledger-derived receivables and payables separated by represented currency are needed.

**Nicht verwenden, wenn**

- Bank settlement
- reconciliation
- invoice evidence
- or cash availability must be proven.

**Parameter**

Keine Parameter.

### `reality_gaps` — List missing information {#tool-reality_gaps}

List the tenant's durable missing-information queue.

**Aufruf**

```text
reality_gaps [status] [destination] [origin]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage   | Art                        | Standard |
| ------------------ | -------------------------- | -------- |
| `MCP reality_gaps` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

List tenant-scoped missing-information investigations and their current workflow state.

**Verwenden, wenn**

- An operator or agent needs the queue of reported information gaps.

**Nicht verwenden, wenn**

- A caller wants to infer that an unreported gap does not exist.

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung                                                         | Standard |
| ------------- | -------- | ------- | -------------------------------------------------------------------- | -------- |
| `status`      | `string` | nein    | Lifecycle state to filter by, such as open, fulfilled, or withdrawn. | —        |
| `destination` | `string` | nein    | —                                                                    | —        |
| `origin`      | `string` | nein    | —                                                                    | —        |

### `reality_gap_get` — Inspect missing information {#tool-reality_gap_get}

Read one gap, its investigation, decision, and implementation history.

**Aufruf**

```text
reality_gap_get gap_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage      | Art                        | Standard |
| --------------------- | -------------------------- | -------- |
| `MCP reality_gap_get` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Inspect one missing-information investigation with its evidence, decision, rule, and outcomes.

**Verwenden, wenn**

- An operator or agent needs the traceable detail behind one reported gap.

**Nicht verwenden, wenn**

- A caller lacks the opaque gap identity or wants to mutate the investigation.

**Parameter**

| Name     | Typ      | Pflicht | Beschreibung | Standard |
| -------- | -------- | ------- | ------------ | -------- |
| `gap_id` | `string` | ja      | —            | —        |

### `reality_gap_simulate` — Simulate Fact rule {#tool-reality_gap_simulate}

Dry-run a reviewed declarative rule without changing Reality.

**Aufruf**

```text
reality_gap_simulate rule_id [limit]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage           | Art                        | Standard |
| -------------------------- | -------------------------- | -------- |
| `MCP reality_gap_simulate` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Preview deterministic matches and normalized Fact values for a draft or accepted interpretation rule
without writing Reality.

**Verwenden, wenn**

- An operator needs to validate a SourceRecord-to-Fact rule before activation.

**Nicht verwenden, wenn**

- The intended change creates typed Evidence
- operational Reality
- projections
- or exceptions.

**Parameter**

| Name      | Typ       | Pflicht | Beschreibung                                                    | Standard |
| --------- | --------- | ------- | --------------------------------------------------------------- | -------- |
| `rule_id` | `string`  | ja      | —                                                               | —        |
| `limit`   | `integer` | nein    | Maximum number of records or jobs processed by this invocation. | `100`    |

### `reality_gap_create_propose` — Propose missing information {#tool-reality_gap_create_propose}

Capture an unanswered business question after confirmation.

**Aufruf**

```text
reality_gap_create_propose question intended_use origin idempotency_key [origin_reference]
```

**Zugriff:** `propose`

**Parameter**

| Name               | Typ      | Pflicht | Beschreibung                                                                                       | Standard |
| ------------------ | -------- | ------- | -------------------------------------------------------------------------------------------------- | -------- |
| `question`         | `string` | ja      | Concise 3–7 word queue label; put explanation in intended_use.                                     | —        |
| `intended_use`     | `string` | ja      | —                                                                                                  | —        |
| `origin`           | `string` | ja      | `chat`, `mcp`, `web`                                                                               | —        |
| `idempotency_key`  | `string` | ja      | Caller-stable retry identity for one intended operation; reuse with different content is rejected. | —        |
| `origin_reference` | `string` | nein    | —                                                                                                  | —        |

### `reality_gap_entry_add_propose` — Propose investigation entry {#tool-reality_gap_entry_add_propose}

Append a guided answer or bounded evidence after confirmation.

**Aufruf**

```text
reality_gap_entry_add_propose gap_id entry_type payload expected_revision
```

**Zugriff:** `propose`

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `gap_id`            | `string`  | ja      | —                                                                           | —        |
| `entry_type`        | `string`  | ja      | `answer`, `context`, `evidence`, `note`                                     | —        |
| `payload`           | `object`  | ja      | Lossless JSON object received from or prepared for an external context.     | —        |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |

### `reality_gap_recommend_propose` — Propose modeling recommendation {#tool-reality_gap_recommend_propose}

Prepare an evidence-grounded destination recommendation.

**Aufruf**

```text
reality_gap_recommend_propose gap_id expected_revision
```

**Zugriff:** `propose`

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `gap_id`            | `string`  | ja      | —                                                                           | —        |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |

### `reality_gap_decide_propose` — Propose classification decision {#tool-reality_gap_decide_propose}

Accept, override, or reject a modeling destination.

**Aufruf**

```text
reality_gap_decide_propose gap_id destination rationale expected_revision
```

**Zugriff:** `propose`

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                         | Standard |
| ------------------- | --------- | ------- | ------------------------------------------------------------------------------------ | -------- |
| `gap_id`            | `string`  | ja      | —                                                                                    | —        |
| `destination`       | `string`  | ja      | `source_only`, `fact`, `typed_evidence`, `typed_reality`, `derived_view`, `rejected` | —        |
| `rationale`         | `string`  | ja      | —                                                                                    | —        |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based.          | —        |

### `reality_gap_implementation_prepare_propose` — Propose gap implementation {#tool-reality_gap_implementation_prepare_propose}

Prepare a safe Fact rule or governed developer package.

**Aufruf**

```text
reality_gap_implementation_prepare_propose gap_id [draft] expected_revision
```

**Zugriff:** `propose`

**Parameter**

| Name                | Typ       | Pflicht | Beschreibung                                                                | Standard |
| ------------------- | --------- | ------- | --------------------------------------------------------------------------- | -------- |
| `gap_id`            | `string`  | ja      | —                                                                           | —        |
| `draft`             | `object`  | nein    | —                                                                           | —        |
| `expected_revision` | `integer` | ja      | Canonical revision of the Evidence snapshot on which a correction is based. | —        |

### `reality_gap_rule_activate_propose` — Propose rule activation {#tool-reality_gap_rule_activate_propose}

Activate one reviewed declarative Fact rule.

**Aufruf**

```text
reality_gap_rule_activate_propose rule_id
```

**Zugriff:** `propose`

**Parameter**

| Name      | Typ      | Pflicht | Beschreibung | Standard |
| --------- | -------- | ------- | ------------ | -------- |
| `rule_id` | `string` | ja      | —            | —        |

### `reality_gap_rule_disable_propose` — Propose rule disablement {#tool-reality_gap_rule_disable_propose}

Stop one Fact rule for future sources without deleting Facts.

**Aufruf**

```text
reality_gap_rule_disable_propose rule_id
```

**Zugriff:** `propose`

**Parameter**

| Name      | Typ      | Pflicht | Beschreibung | Standard |
| --------- | -------- | ------- | ------------ | -------- |
| `rule_id` | `string` | ja      | —            | —        |

### `reality_gap_rule_replay_propose` — Propose historical replay {#tool-reality_gap_rule_replay_propose}

Run one reviewed Fact rule over a bounded source scope.

**Aufruf**

```text
reality_gap_rule_replay_propose rule_id [source_ids] [cursor] [limit]
```

**Zugriff:** `propose`

**Parameter**

| Name         | Typ       | Pflicht | Beschreibung                                                    | Standard |
| ------------ | --------- | ------- | --------------------------------------------------------------- | -------- |
| `rule_id`    | `string`  | ja      | —                                                               | —        |
| `source_ids` | `array`   | nein    | —                                                               | —        |
| `cursor`     | `string`  | nein    | —                                                               | —        |
| `limit`      | `integer` | nein    | Maximum number of records or jobs processed by this invocation. | `500`    |

### `supply_coverage` — Supply coverage {#tool-supply_coverage}

Read customer-assigned, stock-replenishment, received, open and unassigned supplier quantity.

**Aufruf**

```text
supply_coverage [supplier_commitment_id] [customer_commitment_id]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage      | Art                        | Standard |
| --------------------- | -------------------------- | -------- |
| `MCP supply_coverage` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read explicit links between incoming supplier commitments and customer commitments, including
assigned quantity and current reversals.

**Verwenden, wenn**

- A user needs to understand which incoming purchase supply is intended to cover which customer
  demand.

**Nicht verwenden, wenn**

- Physical receipt
- stock availability
- reservation
- or customer shipment must be proven.

**Parameter**

| Name                     | Typ      | Pflicht | Beschreibung                                                                                                                                                  | Standard |
| ------------------------ | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `supplier_commitment_id` | `string` | nein    | Opaque identity of the incoming supplier commitment whose quantity is being assigned.                                                                         | —        |
| `customer_commitment_id` | `string` | nein    | Optional opaque identity of the outgoing customer commitment that the incoming supply is intended to cover; absence explicitly assigns the quantity to stock. | —        |

### `movement_explanation` — Movement explanation {#tool-movement_explanation}

Explain why a stock movement exists through its shortest authoritative links.

**Aufruf**

```text
movement_explanation movement_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage           | Art                        | Standard |
| -------------------------- | -------------------------- | -------- |
| `MCP movement_explanation` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Explain why one physical stock movement exists through its shortest authoritative relationships.

**Verwenden, wenn**

- A user asks for the business reason behind a goods movement.

**Nicht verwenden, wenn**

- A user wants to mutate a movement.

**Parameter**

| Name          | Typ      | Pflicht | Beschreibung                                                                     | Standard |
| ------------- | -------- | ------- | -------------------------------------------------------------------------------- | -------- |
| `movement_id` | `string` | ja      | Opaque identity of the immutable physical Movement being inspected or corrected. | —        |

### `return_disposition_summary` — Return disposition summary {#tool-return_disposition_summary}

Read arrived, resolved and unresolved returned-goods quantity by physical outcome.

**Aufruf**

```text
return_disposition_summary return_movement_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                 | Art                        | Standard |
| -------------------------------- | -------------------------- | -------- |
| `MCP return_disposition_summary` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read arrived, resolved and unresolved customer-return quantity with append-only physical outcome
history.

**Verwenden, wenn**

- Warehouse or customer service needs to decide or explain what happened to returned goods.

**Nicht verwenden, wenn**

- A customer credit
- refund or commercial settlement must be proven.

**Parameter**

| Name                 | Typ      | Pflicht | Beschreibung                                                                                     | Standard |
| -------------------- | -------- | ------- | ------------------------------------------------------------------------------------------------ | -------- |
| `return_movement_id` | `string` | ja      | Opaque identity of the arrived customer-return Movement whose physical outcome is being decided. | —        |

### `finance_credits` — Available credit {#tool-finance_credits}

Read customer or supplier credit that is not used yet: overpayments and credit notes with their
original, used and available amounts.

**Aufruf**

```text
finance_credits [side] [status] [query] [limit]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage      | Art                        | Standard |
| --------------------- | -------------------------- | -------- |
| `MCP finance_credits` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read available customer or supplier credit, that is payments and credit notes with an original, used
and still available amount.

**Verwenden, wenn**

- Answer who holds credit from overpayments or credit notes, and how much.
- Find an original credit before allocating it to an invoice or recording a refund.

**Nicht verwenden, wenn**

- Read open receivables or payables; use finance_balances or the open items.
- Decide that a credit belongs to a particular invoice.

**Parameter**

| Name     | Typ       | Pflicht | Beschreibung                                                                              | Standard |
| -------- | --------- | ------- | ----------------------------------------------------------------------------------------- | -------- |
| `side`   | `string`  | nein    | `customer`, `supplier`                                                                    | —        |
| `status` | `string`  | nein    | Lifecycle state to filter by, such as open, fulfilled, or withdrawn. `outstanding`, `all` | —        |
| `query`  | `string`  | nein    | Optional invoice-number search within matching same-party credit targets.                 | —        |
| `limit`  | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                           | —        |

### `finance_party_balances` — Party balances {#tool-finance_party_balances}

Read where each customer or supplier stands: open amount, of which overdue, available credit and
balance per party and currency, summed from the open items and the credit register at read time.

**Aufruf**

```text
finance_party_balances side [credit_only] [query] [limit]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage             | Art                        | Standard |
| ---------------------------- | -------------------------- | -------- |
| `MCP finance_party_balances` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read where each customer or supplier stands, one row per party and currency, with open amount, of
which overdue, available credit and the balance of the two.

**Verwenden, wenn**

- Answer who owes the most, who is overdue, or who holds credit, per party rather than per document.
- Read a party's position before a call, a delivery hold decision or a payment run.

**Nicht verwenden, wenn**

- Decide that a party's credit may be netted against an invoice; that is a confirmed settlement.
- Judge creditworthiness or predict payment; a balance is a position, not a forecast.
- Add amounts across currencies; rows are per currency and nothing is converted.

**Parameter**

| Name          | Typ       | Pflicht | Beschreibung                                                              | Standard |
| ------------- | --------- | ------- | ------------------------------------------------------------------------- | -------- |
| `side`        | `string`  | ja      | `customer`, `supplier`                                                    | —        |
| `credit_only` | `boolean` | nein    | —                                                                         | —        |
| `query`       | `string`  | nein    | Optional invoice-number search within matching same-party credit targets. | —        |
| `limit`       | `integer` | nein    | Maximum number of records or jobs processed by this invocation.           | —        |

### `finance_payments` — Recorded payments {#tool-finance_payments}

Read recorded payments with allocated and unallocated amounts, optionally only those with money left
to allocate.

**Aufruf**

```text
finance_payments [direction] [only_unallocated] [query] [limit]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage       | Art                        | Standard |
| ---------------------- | -------------------------- | -------- |
| `MCP finance_payments` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Read recorded incoming and outgoing payments with their allocated and unallocated amounts,
optionally only those with money left to allocate.

**Verwenden, wenn**

- Answer which payments are not, or not fully, allocated to an invoice.
- Find a payment by number or party before reading its settlement context.

**Nicht verwenden, wenn**

- Record or allocate a payment; that is finance_settlement_propose.
- Read invoice open amounts; use the open items or finance_balances.

**Parameter**

| Name               | Typ       | Pflicht | Beschreibung                                                                                     | Standard |
| ------------------ | --------- | ------- | ------------------------------------------------------------------------------------------------ | -------- |
| `direction`        | `string`  | nein    | Business flow direction, such as sales or purchase, incoming or outgoing. `incoming`, `outgoing` | —        |
| `only_unallocated` | `boolean` | nein    | —                                                                                                | —        |
| `query`            | `string`  | nein    | Optional invoice-number search within matching same-party credit targets.                        | —        |
| `limit`            | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                                  | —        |

### `graph_company_generation_current` — Read current published company cost generation {#tool-graph_company_generation_current}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_company_generation_current family
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                       | Art                        | Standard |
| -------------------------------------- | -------------------------- | -------- |
| `MCP graph_company_generation_current` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Discover the verified currently published company cost generation for explicit fixed analysis
selection.

**Verwenden, wenn**

- Select the published financial company generation for inventory or contribution analysis.

**Nicht verwenden, wenn**

- Build or publish a generation
- or treat independent member reviews as one company policy.

**Parameter**

| Name     | Typ      | Pflicht | Beschreibung                | Standard |
| -------- | -------- | ------- | --------------------------- | -------- |
| `family` | `string` | ja      | `inventory`, `contribution` | —        |

### `graph_captured_reports_list` — List captured report generations {#tool-graph_captured_reports_list}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_captured_reports_list [limit] [cursor] family
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                  | Art                        | Standard |
| --------------------------------- | -------------------------- | -------- |
| `MCP graph_captured_reports_list` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Discover sealed captured report generations for an explicit fixed analysis selection.

**Verwenden, wenn**

- Select one captured inventory or contribution generation by its opaque identity.

**Nicht verwenden, wenn**

- Treat publication as financial approval or silently choose the latest generation.

**Parameter**

| Name     | Typ       | Pflicht | Beschreibung                                                    | Standard |
| -------- | --------- | ------- | --------------------------------------------------------------- | -------- |
| `limit`  | `integer` | nein    | Maximum number of records or jobs processed by this invocation. | `20`     |
| `cursor` | `string`  | nein    | —                                                               | `None`   |
| `family` | `string`  | ja      | `inventory`, `contribution`                                     | —        |

### `graph_contribution_reviews_list` — List confirmed contribution valuations {#tool-graph_contribution_reviews_list}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_contribution_reviews_list [limit] [cursor]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                      | Art                        | Standard |
| ------------------------------------- | -------------------------- | -------- |
| `MCP graph_contribution_reviews_list` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Discover retained joint contribution confirmations for explicit historical report selection.

**Verwenden, wenn**

- Select a confirmed historical contribution scope by cutoff and economic owner.

**Nicht verwenden, wenn**

- Treat discovery as cache readiness or financial approval.

**Parameter**

| Name     | Typ       | Pflicht | Beschreibung                                                    | Standard |
| -------- | --------- | ------- | --------------------------------------------------------------- | -------- |
| `limit`  | `integer` | nein    | Maximum number of records or jobs processed by this invocation. | `20`     |
| `cursor` | `string`  | nein    | —                                                               | `None`   |

### `graph_inventory_reviews_list` — List confirmed inventory valuations {#tool-graph_inventory_reviews_list}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_inventory_reviews_list [limit] [cursor]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                   | Art                        | Standard |
| ---------------------------------- | -------------------------- | -------- |
| `MCP graph_inventory_reviews_list` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Discover retained joint inventory confirmations for explicit historical report selection.

**Verwenden, wenn**

- Select a confirmed historical inventory scope by cutoff and economic owner.

**Nicht verwenden, wenn**

- Treat discovery as cache readiness or financial approval.

**Parameter**

| Name     | Typ       | Pflicht | Beschreibung                                                    | Standard |
| -------- | --------- | ------- | --------------------------------------------------------------- | -------- |
| `limit`  | `integer` | nein    | Maximum number of records or jobs processed by this invocation. | `20`     |
| `cursor` | `string`  | nein    | —                                                               | `None`   |

### `graph_catalog` — Discover the business graph {#tool-graph_catalog}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_catalog [language] [node]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage    | Art                        | Standard |
| ------------------- | -------------------------- | -------- |
| `MCP graph_catalog` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Discover the business nodes, how they connect, which edges fan out, and what each measure means.

**Verwenden, wenn**

- Decide which nodes, edges and measures a question can use before asking it.

**Nicht verwenden, wenn**

- Invent a node, edge or measure that the catalog does not list, or assume a relationship exists
  because two records look related.

**Parameter**

| Name       | Typ      | Pflicht | Beschreibung                                                                                         | Standard |
| ---------- | -------- | ------- | ---------------------------------------------------------------------------------------------------- | -------- |
| `language` | `string` | nein    | Language for the business words in the catalog.                                                      | `en`     |
| `node`     | `string` | nein    | Optional exact node key; omit to discover every node, how they connect, and what each measure means. | `None`   |

### `graph_templates` — List report templates {#tool-graph_templates}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_templates [language]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage      | Art                        | Standard |
| --------------------- | -------------------------- | -------- |
| `MCP graph_templates` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

List the questions worth starting from, each already resolved against the declared model.

**Verwenden, wenn**

- Offer somebody a starting point instead of an empty builder, or find the shape of a common report.

**Nicht verwenden, wenn**

- Treat a template as an answer; it is a question that still has to be executed.

**Parameter**

| Name       | Typ      | Pflicht | Beschreibung                                      | Standard |
| ---------- | -------- | ------- | ------------------------------------------------- | -------- |
| `language` | `string` | nein    | Language for the template names and explanations. | `en`     |

### `graph_ask` — Ask the business graph {#tool-graph_ask}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_ask [question] [path] [parameters]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage | Art                        | Standard |
| ---------------- | -------------------------- | -------- |
| `MCP graph_ask`  | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Ask a question as a path through declared edges with declared measures, grouping and filters.

**Verwenden, wenn**

- Answer an explicit question about retained company records by combining declared nodes.

**Nicht verwenden, wenn**

- Sum a property directly, combine currencies or units, or attribute an order-level amount to one of
  its articles.

**Parameter**

| Name                                           | Typ       | Pflicht | Beschreibung                                                                                                                                                                                                                                             | Standard     |
| ---------------------------------------------- | --------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| `question`                                     | `object`  | nein    | The whole question.                                                                                                                                                                                                                                      | `None`       |
| `question.from`                                | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.inventory_cost_context`              | `object`  | nein    | One retained joint confirmation, never an implicit latest valuation.                                                                                                                                                                                     | `None`       |
| `question.inventory_cost_context.action_id`    | `string`  | ja      | Optional opaque Change Proposal identity linking an emitted Business Event to its confirmed action.                                                                                                                                                      | —            |
| `question.inventory_cost_context.mode`         | `string`  | nein    | —                                                                                                                                                                                                                                                        | `historical` |
| `question.contribution_cost_context`           | `object`  | nein    | One retained joint scope, optionally requiring unchanged knowledge.                                                                                                                                                                                      | `None`       |
| `question.contribution_cost_context.action_id` | `string`  | ja      | Optional opaque Change Proposal identity linking an emitted Business Event to its confirmed action.                                                                                                                                                      | —            |
| `question.contribution_cost_context.mode`      | `string`  | nein    | `historical`, `current`                                                                                                                                                                                                                                  | `historical` |
| `question.captured_cost_context`               | `object`  | nein    | One sealed captured report generation, never a mutable latest pointer.                                                                                                                                                                                   | `None`       |
| `question.captured_cost_context.generation_id` | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.company_cost_context`                | `object`  | nein    | One verified financial company generation, never an implicit latest pointer.                                                                                                                                                                             | `None`       |
| `question.company_cost_context.generation_id`  | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.as`                                  | `string`  | nein    | —                                                                                                                                                                                                                                                        | `root`       |
| `question.follow`                              | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.follow[].edge`                       | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.follow[].direction`                  | `string`  | nein    | Business flow direction, such as sales or purchase, incoming or outgoing. `out`, `in`                                                                                                                                                                    | `out`        |
| `question.follow[].as`                         | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.follow[].from`                       | `string`  | nein    | —                                                                                                                                                                                                                                                        | `None`       |
| `question.follow[].depth`                      | `array`   | nein    | —                                                                                                                                                                                                                                                        | `None`       |
| `question.filter`                              | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.filter[].field`                      | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.filter[].op`                         | `string`  | ja      | `eq`, `ne`, `in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `is_null`, `is_not_null`                                                                                                                                                                           | —            |
| `question.filter[].value`                      | `any`     | nein    | Scalar observation value validated and canonicalized by its predicate contract.                                                                                                                                                                          | `None`       |
| `question.measures`                            | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.group_by`                            | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.group_by[].field`                    | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.group_by[].bucket`                   | `string`  | nein    | `day`, `week`, `month`, `quarter`, `year`                                                                                                                                                                                                                | `None`       |
| `question.group_by[].as`                       | `string`  | nein    | —                                                                                                                                                                                                                                                        | `None`       |
| `question.having`                              | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.having[].measure`                    | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.having[].op`                         | `string`  | ja      | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`                                                                                                                                                                                                                     | —            |
| `question.having[].value`                      | `number`  | ja      | Scalar observation value validated and canonicalized by its predicate contract.                                                                                                                                                                          | —            |
| `question.exists`                              | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.exists[].follow`                     | `array`   | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.exists[].follow[].edge`              | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.exists[].follow[].direction`         | `string`  | nein    | Business flow direction, such as sales or purchase, incoming or outgoing. `out`, `in`                                                                                                                                                                    | `out`        |
| `question.exists[].follow[].as`                | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.exists[].follow[].from`              | `string`  | nein    | —                                                                                                                                                                                                                                                        | `None`       |
| `question.exists[].follow[].depth`             | `array`   | nein    | —                                                                                                                                                                                                                                                        | `None`       |
| `question.exists[].filter`                     | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.exists[].filter[].field`             | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.exists[].filter[].op`                | `string`  | ja      | `eq`, `ne`, `in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `is_null`, `is_not_null`                                                                                                                                                                           | —            |
| `question.exists[].filter[].value`             | `any`     | nein    | Scalar observation value validated and canonicalized by its predicate contract.                                                                                                                                                                          | `None`       |
| `question.exists[].negated`                    | `boolean` | nein    | —                                                                                                                                                                                                                                                        | `False`      |
| `question.order_by`                            | `array`   | nein    | —                                                                                                                                                                                                                                                        | `[]`         |
| `question.order_by[].by`                       | `string`  | ja      | —                                                                                                                                                                                                                                                        | —            |
| `question.order_by[].descending`               | `boolean` | nein    | —                                                                                                                                                                                                                                                        | `False`      |
| `question.limit`                               | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                                                                                                                                                                                          | `200`        |
| `path`                                         | `string`  | nein    | The same question in the path syntax, for example MATCH (o:order) RETURN o.currency, sum(stated_order_amount). RETURN names declared measures; arithmetic on properties is refused, because summing one along a path that fans out multiplies the total. | `None`       |
| `parameters`                                   | `object`  | nein    | Values for $name placeholders used by the path syntax.                                                                                                                                                                                                   | —            |

### `graph_format` — Format an analysis query {#tool-graph_format}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_format question
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage   | Art                        | Standard |
| ------------------ | -------------------------- | -------- |
| `MCP graph_format` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Format a checked reporting question as an editable path with separate parameters.

**Verwenden, wenn**

- Show the exact technical representation of an analysis without executing it.

**Nicht verwenden, wenn**

- Read business values or execute arbitrary Cypher.

**Parameter**

| Name                                           | Typ       | Pflicht | Beschreibung                                                                                        | Standard     |
| ---------------------------------------------- | --------- | ------- | --------------------------------------------------------------------------------------------------- | ------------ |
| `question`                                     | `object`  | ja      | The whole question.                                                                                 | —            |
| `question.from`                                | `string`  | ja      | —                                                                                                   | —            |
| `question.inventory_cost_context`              | `object`  | nein    | One retained joint confirmation, never an implicit latest valuation.                                | `None`       |
| `question.inventory_cost_context.action_id`    | `string`  | ja      | Optional opaque Change Proposal identity linking an emitted Business Event to its confirmed action. | —            |
| `question.inventory_cost_context.mode`         | `string`  | nein    | —                                                                                                   | `historical` |
| `question.contribution_cost_context`           | `object`  | nein    | One retained joint scope, optionally requiring unchanged knowledge.                                 | `None`       |
| `question.contribution_cost_context.action_id` | `string`  | ja      | Optional opaque Change Proposal identity linking an emitted Business Event to its confirmed action. | —            |
| `question.contribution_cost_context.mode`      | `string`  | nein    | `historical`, `current`                                                                             | `historical` |
| `question.captured_cost_context`               | `object`  | nein    | One sealed captured report generation, never a mutable latest pointer.                              | `None`       |
| `question.captured_cost_context.generation_id` | `string`  | ja      | —                                                                                                   | —            |
| `question.company_cost_context`                | `object`  | nein    | One verified financial company generation, never an implicit latest pointer.                        | `None`       |
| `question.company_cost_context.generation_id`  | `string`  | ja      | —                                                                                                   | —            |
| `question.as`                                  | `string`  | nein    | —                                                                                                   | `root`       |
| `question.follow`                              | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.follow[].edge`                       | `string`  | ja      | —                                                                                                   | —            |
| `question.follow[].direction`                  | `string`  | nein    | Business flow direction, such as sales or purchase, incoming or outgoing. `out`, `in`               | `out`        |
| `question.follow[].as`                         | `string`  | ja      | —                                                                                                   | —            |
| `question.follow[].from`                       | `string`  | nein    | —                                                                                                   | `None`       |
| `question.follow[].depth`                      | `array`   | nein    | —                                                                                                   | `None`       |
| `question.filter`                              | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.filter[].field`                      | `string`  | ja      | —                                                                                                   | —            |
| `question.filter[].op`                         | `string`  | ja      | `eq`, `ne`, `in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `is_null`, `is_not_null`                      | —            |
| `question.filter[].value`                      | `any`     | nein    | Scalar observation value validated and canonicalized by its predicate contract.                     | `None`       |
| `question.measures`                            | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.group_by`                            | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.group_by[].field`                    | `string`  | ja      | —                                                                                                   | —            |
| `question.group_by[].bucket`                   | `string`  | nein    | `day`, `week`, `month`, `quarter`, `year`                                                           | `None`       |
| `question.group_by[].as`                       | `string`  | nein    | —                                                                                                   | `None`       |
| `question.having`                              | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.having[].measure`                    | `string`  | ja      | —                                                                                                   | —            |
| `question.having[].op`                         | `string`  | ja      | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`                                                                | —            |
| `question.having[].value`                      | `number`  | ja      | Scalar observation value validated and canonicalized by its predicate contract.                     | —            |
| `question.exists`                              | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.exists[].follow`                     | `array`   | ja      | —                                                                                                   | —            |
| `question.exists[].follow[].edge`              | `string`  | ja      | —                                                                                                   | —            |
| `question.exists[].follow[].direction`         | `string`  | nein    | Business flow direction, such as sales or purchase, incoming or outgoing. `out`, `in`               | `out`        |
| `question.exists[].follow[].as`                | `string`  | ja      | —                                                                                                   | —            |
| `question.exists[].follow[].from`              | `string`  | nein    | —                                                                                                   | `None`       |
| `question.exists[].follow[].depth`             | `array`   | nein    | —                                                                                                   | `None`       |
| `question.exists[].filter`                     | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.exists[].filter[].field`             | `string`  | ja      | —                                                                                                   | —            |
| `question.exists[].filter[].op`                | `string`  | ja      | `eq`, `ne`, `in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `is_null`, `is_not_null`                      | —            |
| `question.exists[].filter[].value`             | `any`     | nein    | Scalar observation value validated and canonicalized by its predicate contract.                     | `None`       |
| `question.exists[].negated`                    | `boolean` | nein    | —                                                                                                   | `False`      |
| `question.order_by`                            | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.order_by[].by`                       | `string`  | ja      | —                                                                                                   | —            |
| `question.order_by[].descending`               | `boolean` | nein    | —                                                                                                   | `False`      |
| `question.limit`                               | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                                     | `200`        |

### `graph_interpret` — Interpret an analysis question {#tool-graph_interpret}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_interpret text [language] [timezone]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage      | Art                        | Standard |
| --------------------- | -------------------------- | -------- |
| `MCP graph_interpret` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Interpret a business question into a checked traversal using the configured AI provider.

**Verwenden, wenn**

- A reader asks a business question without knowing model identifiers.

**Nicht verwenden, wenn**

- Execute writes or treat an interpretation as a calculated answer.

**Parameter**

| Name       | Typ      | Pflicht | Beschreibung                                                     | Standard |
| ---------- | -------- | ------- | ---------------------------------------------------------------- | -------- |
| `text`     | `string` | ja      | Business question to interpret; no actions are executed.         | —        |
| `language` | `string` | nein    | Requested inspection labels (en/de); nl/es use English fallback. | `en`     |
| `timezone` | `string` | nein    | —                                                                | `UTC`    |

### `graph_reports_list` — List my graph reports {#tool-graph_reports_list}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_reports_list [query] [limit] [cursor]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage         | Art                        | Standard |
| ------------------------ | -------------------------- | -------- |
| `MCP graph_reports_list` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

List the authenticated caller's own saved graph questions.

**Verwenden, wenn**

- Offer a question the caller saved earlier instead of rebuilding it.

**Nicht verwenden, wenn**

- Read another person's reports, or treat a saved report as a stored result.

**Parameter**

| Name     | Typ       | Pflicht | Beschreibung                                           | Standard |
| -------- | --------- | ------- | ------------------------------------------------------ | -------- |
| `query`  | `string`  | nein    | Optional report-name search.                           | —        |
| `limit`  | `integer` | nein    | Maximum private reports to return.                     | `50`     |
| `cursor` | `string`  | nein    | Opaque continuation from the same owner-scoped search. | `None`   |

### `graph_report_get` — Read my graph report {#tool-graph_report_get}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_report_get report_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage       | Art                        | Standard |
| ---------------------- | -------------------------- | -------- |
| `MCP graph_report_get` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Open one of the authenticated caller's own saved graph questions.

**Verwenden, wenn**

- Re-ask a question the caller saved, exactly as it was saved.

**Nicht verwenden, wenn**

- Open a report saved by the configured generation, or one owned by somebody else.

**Parameter**

| Name        | Typ      | Pflicht | Beschreibung                                             | Standard |
| ----------- | -------- | ------- | -------------------------------------------------------- | -------- |
| `report_id` | `string` | ja      | Opaque ID of a private graph report owned by the caller. | —        |

### `graph_requests_list` — List my requested analyses {#tool-graph_requests_list}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_requests_list [limit]
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage          | Art                        | Standard |
| ------------------------- | -------------------------- | -------- |
| `MCP graph_requests_list` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

List the authenticated caller's own requested analyses and where each one stands.

**Verwenden, wenn**

- Check whether a question asked earlier has been answered.

**Nicht verwenden, wenn**

- Look for somebody else's requests; they are private to whoever asked them.

**Parameter**

| Name    | Typ       | Pflicht | Beschreibung                                                    | Standard |
| ------- | --------- | ------- | --------------------------------------------------------------- | -------- |
| `limit` | `integer` | nein    | Maximum number of records or jobs processed by this invocation. | `50`     |

### `graph_request_get` — Collect a requested analysis {#tool-graph_request_get}

Discover the nodes and measures first; a refusal names the edge that fanned out or the unit that
cannot be added, and is more useful than a total that is wrong.

**Aufruf**

```text
graph_request_get analysis_request_id
```

**Zugriff:** `read`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage        | Art                        | Standard |
| ----------------------- | -------------------------- | -------- |
| `MCP graph_request_get` | Live — beim Aufruf gelesen | ja       |

[So wird diese Abfrage ausgeführt](./views#read-execution)

Collect a requested analysis, with the question and the moment it was answered.

**Verwenden, wenn**

- Read the answer to a question this caller asked and that is ready.

**Nicht verwenden, wenn**

- Use a collected answer as a current figure; it was true of one moment and of no other.

**Parameter**

| Name                  | Typ      | Pflicht | Beschreibung                                            | Standard |
| --------------------- | -------- | ------- | ------------------------------------------------------- | -------- |
| `analysis_request_id` | `string` | ja      | Opaque ID of a requested analysis the caller asked for. | —        |

### `graph_request_propose` — Request an analysis {#tool-graph_request_propose}

Prepare an analysis question that may be answered by the worker rather than in this call. Requires
trusted authenticated user context; confirm explicitly. A question the model cannot express is
refused here, not minutes later.

**Aufruf**

```text
graph_request_propose [question] [path] [parameters] request_id
```

**Zugriff:** `propose`

**Parameter**

| Name                                           | Typ       | Pflicht | Beschreibung                                                                                        | Standard     |
| ---------------------------------------------- | --------- | ------- | --------------------------------------------------------------------------------------------------- | ------------ |
| `question`                                     | `object`  | nein    | The whole question.                                                                                 | `None`       |
| `question.from`                                | `string`  | ja      | —                                                                                                   | —            |
| `question.inventory_cost_context`              | `object`  | nein    | One retained joint confirmation, never an implicit latest valuation.                                | `None`       |
| `question.inventory_cost_context.action_id`    | `string`  | ja      | Optional opaque Change Proposal identity linking an emitted Business Event to its confirmed action. | —            |
| `question.inventory_cost_context.mode`         | `string`  | nein    | —                                                                                                   | `historical` |
| `question.contribution_cost_context`           | `object`  | nein    | One retained joint scope, optionally requiring unchanged knowledge.                                 | `None`       |
| `question.contribution_cost_context.action_id` | `string`  | ja      | Optional opaque Change Proposal identity linking an emitted Business Event to its confirmed action. | —            |
| `question.contribution_cost_context.mode`      | `string`  | nein    | `historical`, `current`                                                                             | `historical` |
| `question.captured_cost_context`               | `object`  | nein    | One sealed captured report generation, never a mutable latest pointer.                              | `None`       |
| `question.captured_cost_context.generation_id` | `string`  | ja      | —                                                                                                   | —            |
| `question.company_cost_context`                | `object`  | nein    | One verified financial company generation, never an implicit latest pointer.                        | `None`       |
| `question.company_cost_context.generation_id`  | `string`  | ja      | —                                                                                                   | —            |
| `question.as`                                  | `string`  | nein    | —                                                                                                   | `root`       |
| `question.follow`                              | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.follow[].edge`                       | `string`  | ja      | —                                                                                                   | —            |
| `question.follow[].direction`                  | `string`  | nein    | Business flow direction, such as sales or purchase, incoming or outgoing. `out`, `in`               | `out`        |
| `question.follow[].as`                         | `string`  | ja      | —                                                                                                   | —            |
| `question.follow[].from`                       | `string`  | nein    | —                                                                                                   | `None`       |
| `question.follow[].depth`                      | `array`   | nein    | —                                                                                                   | `None`       |
| `question.filter`                              | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.filter[].field`                      | `string`  | ja      | —                                                                                                   | —            |
| `question.filter[].op`                         | `string`  | ja      | `eq`, `ne`, `in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `is_null`, `is_not_null`                      | —            |
| `question.filter[].value`                      | `any`     | nein    | Scalar observation value validated and canonicalized by its predicate contract.                     | `None`       |
| `question.measures`                            | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.group_by`                            | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.group_by[].field`                    | `string`  | ja      | —                                                                                                   | —            |
| `question.group_by[].bucket`                   | `string`  | nein    | `day`, `week`, `month`, `quarter`, `year`                                                           | `None`       |
| `question.group_by[].as`                       | `string`  | nein    | —                                                                                                   | `None`       |
| `question.having`                              | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.having[].measure`                    | `string`  | ja      | —                                                                                                   | —            |
| `question.having[].op`                         | `string`  | ja      | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`                                                                | —            |
| `question.having[].value`                      | `number`  | ja      | Scalar observation value validated and canonicalized by its predicate contract.                     | —            |
| `question.exists`                              | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.exists[].follow`                     | `array`   | ja      | —                                                                                                   | —            |
| `question.exists[].follow[].edge`              | `string`  | ja      | —                                                                                                   | —            |
| `question.exists[].follow[].direction`         | `string`  | nein    | Business flow direction, such as sales or purchase, incoming or outgoing. `out`, `in`               | `out`        |
| `question.exists[].follow[].as`                | `string`  | ja      | —                                                                                                   | —            |
| `question.exists[].follow[].from`              | `string`  | nein    | —                                                                                                   | `None`       |
| `question.exists[].follow[].depth`             | `array`   | nein    | —                                                                                                   | `None`       |
| `question.exists[].filter`                     | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.exists[].filter[].field`             | `string`  | ja      | —                                                                                                   | —            |
| `question.exists[].filter[].op`                | `string`  | ja      | `eq`, `ne`, `in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `is_null`, `is_not_null`                      | —            |
| `question.exists[].filter[].value`             | `any`     | nein    | Scalar observation value validated and canonicalized by its predicate contract.                     | `None`       |
| `question.exists[].negated`                    | `boolean` | nein    | —                                                                                                   | `False`      |
| `question.order_by`                            | `array`   | nein    | —                                                                                                   | `[]`         |
| `question.order_by[].by`                       | `string`  | ja      | —                                                                                                   | —            |
| `question.order_by[].descending`               | `boolean` | nein    | —                                                                                                   | `False`      |
| `question.limit`                               | `integer` | nein    | Maximum number of records or jobs processed by this invocation.                                     | `200`        |
| `path`                                         | `string`  | nein    | Cypher-shaped path, as the immediate ask accepts one.                                               | `None`       |
| `parameters`                                   | `object`  | nein    | —                                                                                                   | —            |
| `request_id`                                   | `string`  | ja      | Caller-chosen identity; the same one returns the same request.                                      | —            |
