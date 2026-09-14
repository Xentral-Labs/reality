# Proposed Capability Classification Inventory

**Status**: Approved taxonomy implemented in the shared discovery catalog; runtime verification recorded separately.
**Baseline**: Active integration worktree, 2026-09-10; 65 Commands and 13 workspace Actions.

One primary path per catalog identity. Related service aliases inherit their parent
Command path. Form variants and page placements are distinct from catalog identity.
Sales & Purchasing is shared because the order and commitment commands cover both
directions. Finance retains separate customer and supplier subgroups.

## Proposed directory

- Sales & Purchasing / Orders and commitments
- Sales & Purchasing / Delivery holds
- Sales & Purchasing / Return announcements
- Warehouse / Reservations
- Warehouse / Movements
- Warehouse / Tracking and expiry
- Finance / Customer invoices and credits
- Finance / Supplier invoices and credits
- Finance / Payments and refunds
- Finance / Journal
- Finance / Operational accounts
- Master data / Parties, items and locations
- Master data / Commercial terms
- Sources & Evidence / Integrations and intake
- Sources & Evidence / Documents
- Facts / Observations
- Company / Members and access

## Commands

| Command                                                               | Mode     | Primary path                                 |
| --------------------------------------------------------------------- | -------- | -------------------------------------------- |
| Initialize operational accounts (`initialize_accounts`)               | mutation | Finance / Operational accounts               |
| Create operational account (`create_account`)                         | mutation | Finance / Operational accounts               |
| Update operational account (`update_account`)                         | mutation | Finance / Operational accounts               |
| Set operational account default (`set_default_account`)               | mutation | Finance / Operational accounts               |
| Read operational accounts (`list_accounts`)                           | read     | Finance / Operational accounts               |
| Observe fact (`observe_fact`)                                         | mutation | Facts / Observations                         |
| Create manual sales or purchase order (`create_manual_order`)         | mutation | Sales & Purchasing / Orders and commitments  |
| Install mock connector shell (`install_connector_shell`)              | mutation | Sources & Evidence / Integrations and intake |
| Define source system (`create_source_system`)                         | mutation | Sources & Evidence / Integrations and intake |
| Define source capability (`create_source_capability`)                 | mutation | Sources & Evidence / Integrations and intake |
| Ingest arbitrary source (`enqueue_source`)                            | mutation | Sources & Evidence / Integrations and intake |
| Correct manual document evidence (`correct_manual_document`)          | mutation | Sources & Evidence / Documents               |
| Record corrected document source (`record_corrected_document_source`) | mutation | Sources & Evidence / Documents               |
| Create party (`create_party`)                                         | mutation | Master data / Parties, items and locations   |
| Update party (`update_party`)                                         | mutation | Master data / Parties, items and locations   |
| Create item (`create_item`)                                           | mutation | Master data / Parties, items and locations   |
| Update item (`update_item`)                                           | mutation | Master data / Parties, items and locations   |
| Create location (`create_location`)                                   | mutation | Master data / Parties, items and locations   |
| Update location (`update_location`)                                   | mutation | Master data / Parties, items and locations   |
| Create handling unit (`create_handling_unit`)                         | mutation | Warehouse / Tracking and expiry              |
| Create lot (`create_lot`)                                             | mutation | Warehouse / Tracking and expiry              |
| State lot expiry (`state_lot_expiry`)                                 | mutation | Warehouse / Tracking and expiry              |
| Correct lot expiry (`correct_lot_expiry`)                             | mutation | Warehouse / Tracking and expiry              |
| Read expired lots (`expired_lots`)                                    | query    | Warehouse / Tracking and expiry              |
| Create serial unit (`create_serial_unit`)                             | mutation | Warehouse / Tracking and expiry              |
| Change master-data lifecycle (`set_master_data_active`)               | mutation | Master data / Parties, items and locations   |
| Create payment term (`create_payment_term`)                           | mutation | Master data / Commercial terms               |
| Create price list (`create_price_list`)                               | mutation | Master data / Commercial terms               |
| Add price tier (`create_price_list_entry`)                            | mutation | Master data / Commercial terms               |
| Assign party price list (`assign_party_price_list`)                   | mutation | Master data / Commercial terms               |
| Create and assign pricing group (`create_party_group`)                | mutation | Master data / Commercial terms               |
| Reserve stock (`reserve`)                                             | mutation | Warehouse / Reservations                     |
| Release reservation (`release_reservation`)                           | mutation | Warehouse / Reservations                     |
| Record movement (`record_movement`)                                   | mutation | Warehouse / Movements                        |
| Correct movement (`correct_movement`)                                 | mutation | Warehouse / Movements                        |
| Reverse ledger posting group (`reverse_ledger_posting_group`)         | mutation | Finance / Journal                            |
| Revise commitment (`revise_commitment`)                               | mutation | Sales & Purchasing / Orders and commitments  |
| Hold commitment (`hold_commitment`)                                   | mutation | Sales & Purchasing / Delivery holds          |
| Hold document commitments (`hold_document_commitments`)               | mutation | Sales & Purchasing / Delivery holds          |
| Set party delivery hold (`hold_party_delivery`)                       | mutation | Sales & Purchasing / Delivery holds          |
| Post customer payment (`post_customer_payment`)                       | mutation | Finance / Payments and refunds               |
| Announce customer return (`announce_customer_return`)                 | mutation | Sales & Purchasing / Return announcements    |
| Withdraw return announcement (`withdraw_return_announcement`)         | mutation | Sales & Purchasing / Return announcements    |
| Read announced returns (`return_announcements`)                       | query    | Sales & Purchasing / Return announcements    |
| Preview payment run (`preview_payment_run`)                           | query    | Finance / Payments and refunds               |
| Execute payment run (`execute_payment_run`)                           | mutation | Finance / Payments and refunds               |
| Preview stale promise closure (`preview_stale_promise_closure`)       | query    | Sales & Purchasing / Orders and commitments  |
| Close stale promises (`close_stale_promises`)                         | mutation | Sales & Purchasing / Orders and commitments  |
| Record manual document (`create_manual_document_with_lines`)          | mutation | Sources & Evidence / Documents               |
| Post sales invoice (`post_sales_invoice`)                             | mutation | Finance / Customer invoices and credits      |
| Post supplier invoice (`post_supplier_invoice`)                       | mutation | Finance / Supplier invoices and credits      |
| Record return credit (`record_sales_credit`)                          | mutation | Finance / Customer invoices and credits      |
| Record supplier invoice (`record_supplier_invoice`)                   | mutation | Finance / Supplier invoices and credits      |
| Record sales invoice (`record_sales_invoice`)                         | mutation | Finance / Customer invoices and credits      |
| Post credit note (`post_sales_credit_note`)                           | mutation | Finance / Customer invoices and credits      |
| Net credit note against invoice (`allocate_credit_note`)              | mutation | Finance / Customer invoices and credits      |
| Post customer refund (`post_customer_refund`)                         | mutation | Finance / Payments and refunds               |
| Post supplier credit note (`post_supplier_credit_note`)               | mutation | Finance / Supplier invoices and credits      |
| Net supplier credit against invoice (`allocate_supplier_credit_note`) | mutation | Finance / Supplier invoices and credits      |
| Post supplier refund (`post_supplier_refund`)                         | mutation | Finance / Payments and refunds               |
| Post supplier payment (`post_supplier_payment`)                       | mutation | Finance / Payments and refunds               |
| Invite company member (`create_invitation`)                           | mutation | Company / Members and access                 |
| Resend company invitation (`resend_invitation`)                       | mutation | Company / Members and access                 |
| Revoke company invitation (`revoke_invitation`)                       | mutation | Company / Members and access                 |
| Remove company member (`remove_member`)                               | mutation | Company / Members and access                 |

## Workspace Actions

| Action                                | Key                         | Primary path                                |
| ------------------------------------- | --------------------------- | ------------------------------------------- |
| Create manual sales or purchase order | `create_manual_order`       | Sales & Purchasing / Orders and commitments |
| Observe source-supported fact         | `observe_fact`              | Facts / Observations                        |
| Post customer payment                 | `post_customer_payment`     | Finance / Payments and refunds              |
| Post supplier payment                 | `post_supplier_payment`     | Finance / Payments and refunds              |
| Reserve stock                         | `reserve_stock`             | Warehouse / Reservations                    |
| Record movement                       | `record_movement`           | Warehouse / Movements                       |
| Correct movement                      | `correct_movement`          | Warehouse / Movements                       |
| Hold or release commitment            | `hold_commitment`           | Sales & Purchasing / Delivery holds         |
| Hold or release document commitments  | `hold_document_commitments` | Sales & Purchasing / Delivery holds         |
| Set or release party delivery hold    | `party_delivery_hold`       | Sales & Purchasing / Delivery holds         |
| Create handling unit                  | `create_handling_unit`      | Warehouse / Tracking and expiry             |
| Create lot                            | `create_lot`                | Warehouse / Tracking and expiry             |
| Create serial unit                    | `create_serial_unit`        | Warehouse / Tracking and expiry             |

## Existing form variants and destinations

The launcher currently contains 16 entries, while its form type also supports supplier
invoice and supplier payment variants selected inside shared forms. These counts are
not the same as the 13 workspace Actions. Implementation must inventory these variants
explicitly instead of assuming that either current list is complete.

| Form family                      | Contextual placement                                                                                                        |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Order                            | Sales customer orders; Purchasing supplier orders                                                                           |
| Customer/supplier invoice        | Applicable Finance open items; global direction selector                                                                    |
| Customer/supplier payment        | Applicable Finance open items and Payments                                                                                  |
| Customer credit/refund           | Customer Finance contexts only                                                                                              |
| Ledger reversal                  | Finance Journal and eligible financial records                                                                              |
| Opening stock                    | Warehouse Movements                                                                                                         |
| Reserve/release                  | Warehouse Reservations and applicable customer commitment detail                                                            |
| Receipt/shipment                 | Warehouse Movements; corresponding supplier/customer commitment detail                                                      |
| Movement correction              | Warehouse Movements and eligible movement rows                                                                              |
| Commitment hold/release          | Customer commitment detail                                                                                                  |
| Party hold/release               | Customer master-data detail and customer commitment detail                                                                  |
| Existing master-data management  | Navigate to Customers, Suppliers, Items or Locations                                                                        |
| Existing integrations management | Navigate to source registration/configuration or item import                                                                |
| Existing company management      | Navigate to company creation, members, operational accounts or available Demo Data controls, preserving access restrictions |

## Every-screen review scope

Home; Commitments (customer/supplier); Exceptions; Decisions; Sales; Purchasing;
Warehouse (Stock/Reservations/Movements); Finance (Open items/Payments/Journal and
every direction); Facts; Reports; Inspector Context (Timeline/Graph), Facts
(All records/Calculated views), Rules (Fact/Exception rules), Actions (History/Catalog);
Master data (Customers/Suppliers/Items/Locations); Integrations (Systems/Source records/
Documents); Companies and settings (profile/access/AI/agents/accounts); Demo Data;
Chat and remaining reachable work/detail surfaces. Read-only screens may explicitly
have no mutation entrypoint. Dedicated management flows remain dedicated.

## Review boundary

Classification completeness is proven against the current two catalog files. This is
not proof that every application service is cataloged or every backend capability has
a Web form. Runtime placement and browser verification remain implementation work.

## Integration additions during implementation

The parallel settlement-reduction work added two Commands after the approved baseline.
Both are classified under Finance / Payments and refunds: `adjustment_context` (read)
and `accept_adjustment` (mutation). The current total is 67 Commands and 13 Actions.
The existing owner-only reduction form remains on eligible Finance rows; global and
catalog navigation link to its Finance page. No reduction behavior was implemented here.

## Completed screen placement review

| Screen / tabs                                | Discovery placement and retained behavior                                                             |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Home                                         | Read-only overview; global grouped launcher available                                                 |
| Commitments: customer                        | Shared reserve/shipment and state-selected own/customer hold forms; existing record target retained   |
| Commitments: supplier                        | Shared receipt form for an open commitment; existing record target retained                           |
| Exceptions                                   | Open affected record / discuss; no fabricated mutation forms                                          |
| Decisions                                    | Existing proposal review/confirm/reject; global launches clear unrelated proposal selection           |
| Sales / Purchasing orders                    | Shared order entry definition; page supplies sales/purchase direction                                 |
| Delivery detail / remaining work surfaces    | Same DeliveryCase context actions as Commitments                                                      |
| Warehouse Stock                              | Read-only derived position; existing stock Inspect links                                              |
| Warehouse Reservations                       | Reserve and release; active row release retains reservation ID                                        |
| Warehouse Movements                          | Opening, receipt, shipment, correction; row correction retains movement ID                            |
| Finance Open items: receivable               | Customer invoice/payment/credit; record actions preserved                                             |
| Finance Open items: payable                  | Supplier invoice/payment; no customer credit/refund entries                                           |
| Finance customer credits/balance             | Applicable customer credit/payment/refund entries                                                     |
| Finance supplier balance                     | Supplier payment; no customer credit/refund entries                                                   |
| Finance Payments                             | Payment form follows retained customer/supplier flow                                                  |
| Finance Journal                              | Reversal; eligible row reversal retains posting group                                                 |
| Finance settlement reduction                 | Parallel owner-only form retained; owner-only management destination                                  |
| Facts                                        | Search, evidence and subject inspection; observe_fact remains cataloged without a fabricated form     |
| Reports                                      | Read-only analysis and drilldowns; global launcher available                                          |
| Inspector Context: Timeline/Graph            | Existing read-only exploration                                                                        |
| Inspector Facts: records/views               | Existing registers, projections and details                                                           |
| Inspector Rules: fact/exception rules        | Existing dedicated rule controls retained                                                             |
| Inspector Actions: history/catalog           | Existing event history; new directory, form variants and management links                             |
| Master data: customer/supplier/item/location | Existing create/edit/lifecycle and customer hold forms retained; explicit global/catalog destinations |
| Integrations: systems/records/documents      | Existing registration/configuration/import and read controls retained; global/catalog management link |
| Companies/profile/access/AI/agents/accounts  | Existing management pages and access checks retained; owner-only links for members/accounts           |
| Demo Data                                    | Existing conditional page/controls; global link only for demo/source-enabled company                  |
| Chat                                         | Existing shared confirmed application tools unchanged                                                 |

Coverage distinguishes accessible entrypoints from unsupported capabilities. Existing
row eligibility remains in its established form/service; metadata does not calculate
business permissions or introduce alternative rules.

## Target-main reconciliation

The tables above retain the original local audit. This PR targets main at `2bc3a65`:
60 Commands, 13 Actions, 18 form variants and eight management links. The five
operational-account Commands and two settlement-reduction Commands above are
deferred with their separate Finance feature. Their management links are excluded
from this PR. Exact-coverage validation rejects unclassified future Commands.
