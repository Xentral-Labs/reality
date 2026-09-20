# Views, projections and actions

Where an operator looks and what they can trigger there. A view is either an authoritative register
or a materialized projection; an action starts a business command.

> Automatically generated from `workspace_catalog.yaml`, `projection_catalog.yaml`. Do not edit this
> page by hand.

## How this query runs {#read-execution}

**Stored — updated in background**

Reads the last completed projection. Opening or refreshing the page does not calculate or enqueue
it; the shared scheduler and worker update it after relevant committed business events.

**Live — read at request time**

Reads or derives results from the records currently held by Reality for this request. This does not
mean that external systems were just synchronized.

**Live — calculated for your inputs**

Calculates the answer when requested for the supplied customer, item, quantity, currency, unit and
date. Price resolution uses current canonical rules and does not read a stored price projection.

The mode belongs to a concrete query, not to a business name. The Inspector can read stored
inventory while the Warehouse page and the default MCP inventory page read live records. MCP page is
the default for the five operational page tools; explicit response_format=legacy reads stored
results. Direct application-tool callers retain the legacy default. The catalog's Art/Kind column
describes its view definition, not every Web screen with a similar name. All HTTP paths below are
tenant-scoped GET requests.

Events make stored results eligible for background work; they do not synchronously rebuild every
view. Unknown event types conservatively invalidate stored projections. During delays or worker
outages, the last completed result remains visible. Time-sensitive exceptions, commitment risk and
tenant activity also become eligible every minute. A new company or builder version is initialized
in the background. Command validation still uses authoritative records.

Snapshot metadata reports `uninitialized` (awaiting first calculation), `ready` (caught up to known
relevant events), `pending` (an update is due) or `failed` (calculation failed). `completed_at` is
the completed calculation time; processed and target event sequences describe local progress.
Missing data before the first calculation is not an empty business result. Upstream freshness
remains unknown.

## Workspaces

### `company` — Company Overview {#workspace-company}

**Views:** [`commitments`](./views#view-commitments), [`inventory`](./views#view-inventory),
[`open_items`](./views#view-open_items), [`documents`](./views#view-documents),
[`activity`](./views#view-activity)

**Actions:** [`observe_fact`](./views#action-observe_fact)

### `operations` — Order Operations {#workspace-operations}

**Views:** [`orders`](./views#view-orders), [`commitments`](./views#view-commitments),
[`reservations`](./views#view-reservations), [`inventory`](./views#view-inventory),
[`fulfillment_blockers`](./views#view-fulfillment_blockers),
[`supply_demand`](./views#view-supply_demand), [`documents`](./views#view-documents)

**Actions:** [`create_manual_order`](./views#action-create_manual_order),
[`reserve_stock`](./views#action-reserve_stock),
[`hold_commitment`](./views#action-hold_commitment),
[`hold_document_commitments`](./views#action-hold_document_commitments),
[`party_delivery_hold`](./views#action-party_delivery_hold)

### `warehouse` — Warehouse Operations {#workspace-warehouse}

**Views:** [`inventory`](./views#view-inventory), [`warehouse_queue`](./views#view-warehouse_queue),
[`reservations`](./views#view-reservations), [`movements`](./views#view-movements),
[`fulfillment_blockers`](./views#view-fulfillment_blockers),
[`supply_demand`](./views#view-supply_demand), [`commitments`](./views#view-commitments),
[`locations`](./views#view-locations)

**Actions:** [`record_movement`](./views#action-record_movement),
[`reserve_stock`](./views#action-reserve_stock),
[`hold_commitment`](./views#action-hold_commitment),
[`correct_movement`](./views#action-correct_movement),
[`create_handling_unit`](./views#action-create_handling_unit),
[`create_lot`](./views#action-create_lot), [`create_serial_unit`](./views#action-create_serial_unit)

### `finance` — Finance Control {#workspace-finance}

**Views:** [`open_items`](./views#view-open_items), [`payments`](./views#view-payments),
[`journal`](./views#view-journal), [`documents`](./views#view-documents),
[`parties`](./views#view-parties)

**Actions:** [`post_customer_payment`](./views#action-post_customer_payment),
[`post_supplier_payment`](./views#action-post_supplier_payment)

### `data` — Data Management {#workspace-data}

**Views:** [`parties`](./views#view-parties), [`items`](./views#view-items),
[`locations`](./views#view-locations), [`documents`](./views#view-documents),
[`commercial_terms`](./views#view-commercial_terms)

## Views

| Key                                                  | Label                | Route                  | Kind                      | Projection             |
| ---------------------------------------------------- | -------------------- | ---------------------- | ------------------------- | ---------------------- |
| [`commitments`](#view-commitments)                   | Commitments          | `commitments`          | `authoritative_register`  | —                      |
| [`inventory`](#view-inventory)                       | Inventory            | `inventory`            | `materialized_projection` | `inventory`            |
| [`open_items`](#view-open_items)                     | Open items           | `open-items`           | `materialized_projection` | `open_financial_items` |
| [`documents`](#view-documents)                       | Documents            | `documents`            | `authoritative_register`  | —                      |
| [`reservations`](#view-reservations)                 | Reservations         | `reservations`         | `authoritative_register`  | —                      |
| [`movements`](#view-movements)                       | Movements            | `movements`            | `authoritative_register`  | —                      |
| [`locations`](#view-locations)                       | Locations            | `locations`            | `authoritative_register`  | —                      |
| [`payments`](#view-payments)                         | Payments             | `payments`             | `authoritative_register`  | —                      |
| [`journal`](#view-journal)                           | Journal              | `journal`              | `authoritative_register`  | —                      |
| [`parties`](#view-parties)                           | Parties              | `parties`              | `authoritative_register`  | —                      |
| [`items`](#view-items)                               | Items                | `items`                | `authoritative_register`  | —                      |
| [`commercial_terms`](#view-commercial_terms)         | Commercial terms     | `commercial`           | `authoritative_register`  | —                      |
| [`sources_imports`](#view-sources_imports)           | Sources & imports    | `integrations`         | `authoritative_register`  | —                      |
| [`activity`](#view-activity)                         | Activity             | `timeline`             | `authoritative_register`  | —                      |
| [`orders`](#view-orders)                             | Orders               | `orders`               | `materialized_projection` | `fulfillment_queue`    |
| [`warehouse_queue`](#view-warehouse_queue)           | Warehouse Queue      | `warehouse-queue`      | `materialized_projection` | `fulfillment_queue`    |
| [`fulfillment_blockers`](#view-fulfillment_blockers) | Fulfillment blockers | `fulfillment-blockers` | `materialized_projection` | `fulfillment_blockers` |
| [`supply_demand`](#view-supply_demand)               | Supply & demand      | `supply-demand`        | `materialized_projection` | `item_supply_demand`   |

### `commitments` — Commitments {#view-commitments}

Obligations and their derived execution position

**Route:** `commitments` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                                 | Kind                        | Default |
| ---------------------------------------------- | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/commitment-control` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`company`](./views#workspace-company), workspace
[`operations`](./views#workspace-operations), workspace [`warehouse`](./views#workspace-warehouse)

### `inventory` — Inventory {#view-inventory}

Physical

**Route:** `inventory` · **Kind:** `materialized_projection`

**How this query runs**

| Concrete query                                             | Kind                           | Default |
| ---------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/inventory` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/warehouse/stock`                | Live — read at request time    | —       |

[How this query runs](./views#read-execution)

**See also:** projection [`inventory`](./views#projection-inventory), workspace
[`company`](./views#workspace-company), workspace [`operations`](./views#workspace-operations),
workspace [`warehouse`](./views#workspace-warehouse)

### `open_items` — Open items {#view-open_items}

Financial items with their authoritative open amount

**Route:** `open-items` · **Kind:** `materialized_projection`

**How this query runs**

| Concrete query                                                        | Kind                           | Default |
| --------------------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/open_financial_items` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/finance/open-items?flow=receivable`        | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/finance/open-items?flow=payable`           | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/finance/open-items?flow=customer-credit`   | Live — read at request time    | —       |
| `GET /api/tenants/{tenant}/finance/open-items?flow=customer-balance`  | Live — read at request time    | —       |
| `GET /api/tenants/{tenant}/finance/open-items?flow=supplier-balance`  | Live — read at request time    | —       |
| `GET /api/tenants/{tenant}/finance/open-items?flow=customer-balances` | Live — read at request time    | —       |
| `GET /api/tenants/{tenant}/finance/open-items?flow=supplier-balances` | Live — read at request time    | —       |

[How this query runs](./views#read-execution)

**See also:** projection [`open_financial_items`](./views#projection-open_financial_items),
workspace [`company`](./views#workspace-company), workspace [`finance`](./views#workspace-finance)

### `documents` — Documents {#view-documents}

Normalized Evidence and its links into Reality

**Route:** `documents` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                                 | Kind                        | Default |
| ---------------------------------------------- | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/evidence-documents` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`company`](./views#workspace-company), workspace
[`operations`](./views#workspace-operations), workspace [`finance`](./views#workspace-finance),
workspace [`data`](./views#workspace-data)

### `reservations` — Reservations {#view-reservations}

Active stock allocations linked to Commitments

**Route:** `reservations` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                           | Kind                        | Default |
| ---------------------------------------- | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/reservations` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`operations`](./views#workspace-operations), workspace
[`warehouse`](./views#workspace-warehouse)

### `movements` — Movements {#view-movements}

Append-only physical inventory journal

**Route:** `movements` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                        | Kind                        | Default |
| ------------------------------------- | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/movements` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`warehouse`](./views#workspace-warehouse)

### `locations` — Locations {#view-locations}

Stock-capable and logical locations

**Route:** `locations` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                        | Kind                        | Default |
| ------------------------------------- | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/locations` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`warehouse`](./views#workspace-warehouse), workspace
[`data`](./views#workspace-data)

### `payments` — Payments {#view-payments}

Payment postings and allocations

**Route:** `payments` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                               | Kind                        | Default |
| -------------------------------------------- | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/finance/payments` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`finance`](./views#workspace-finance)

### `journal` — Journal {#view-journal}

Immutable balanced ledger entries

**Route:** `journal` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                              | Kind                        | Default |
| ------------------------------------------- | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/finance/journal` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`finance`](./views#workspace-finance)

### `parties` — Parties {#view-parties}

Customers

**Route:** `parties` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                      | Kind                        | Default |
| ----------------------------------- | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/parties` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`finance`](./views#workspace-finance), workspace
[`data`](./views#workspace-data)

### `items` — Items {#view-items}

Operational item identities

**Route:** `items` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                    | Kind                        | Default |
| --------------------------------- | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/items` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`data`](./views#workspace-data)

### `commercial_terms` — Commercial terms {#view-commercial_terms}

Payment and pricing references

**Route:** `commercial` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                             | Kind                        | Default |
| ------------------------------------------ | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/payment-terms`  | Live — read at request time | —       |
| `GET /api/tenants/{tenant}/price-lists`    | Live — read at request time | —       |
| `GET /api/tenants/{tenant}/pricing-groups` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`data`](./views#workspace-data)

### `sources_imports` — Sources & imports {#view-sources_imports}

Source definitions and immutable intake

**Route:** `integrations` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                           | Kind                        | Default |
| ---------------------------------------- | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/integrations` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

### `activity` — Activity {#view-activity}

Cross-functional operational and financial event history

**Route:** `timeline` · **Kind:** `authoritative_register`

**How this query runs**

| Concrete query                       | Kind                        | Default |
| ------------------------------------ | --------------------------- | ------- |
| `GET /api/tenants/{tenant}/timeline` | Live — read at request time | —       |

[How this query runs](./views#read-execution)

**See also:** workspace [`company`](./views#workspace-company)

### `orders` — Orders {#view-orders}

Customer orders with readiness

**Route:** `orders` · **Kind:** `materialized_projection`

**How this query runs**

| Concrete query                                                     | Kind                           | Default |
| ------------------------------------------------------------------ | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/fulfillment_queue` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projection-views/fulfillment_queue`     | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**See also:** projection [`fulfillment_queue`](./views#projection-fulfillment_queue), workspace
[`operations`](./views#workspace-operations)

### `warehouse_queue` — Warehouse Queue {#view-warehouse_queue}

Orders prioritized for warehouse execution and shipment readiness

**Route:** `warehouse-queue` · **Kind:** `materialized_projection`

**How this query runs**

| Concrete query                                                     | Kind                           | Default |
| ------------------------------------------------------------------ | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/fulfillment_queue` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projection-views/fulfillment_queue`     | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**See also:** projection [`fulfillment_queue`](./views#projection-fulfillment_queue), workspace
[`warehouse`](./views#workspace-warehouse)

### `fulfillment_blockers` — Fulfillment blockers {#view-fulfillment_blockers}

Commitment shortages and active execution holds blocking fulfillment

**Route:** `fulfillment-blockers` · **Kind:** `materialized_projection`

**How this query runs**

| Concrete query                                                        | Kind                           | Default |
| --------------------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/fulfillment_blockers` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projection-views/fulfillment_blockers`     | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**See also:** projection [`fulfillment_blockers`](./views#projection-fulfillment_blockers),
workspace [`operations`](./views#workspace-operations), workspace
[`warehouse`](./views#workspace-warehouse)

### `supply_demand` — Supply & demand {#view-supply_demand}

Item-level physical stock

**Route:** `supply-demand` · **Kind:** `materialized_projection`

**How this query runs**

| Concrete query                                                      | Kind                           | Default |
| ------------------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/item_supply_demand` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projection-views/item_supply_demand`     | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**See also:** projection [`item_supply_demand`](./views#projection-item_supply_demand), workspace
[`operations`](./views#workspace-operations), workspace [`warehouse`](./views#workspace-warehouse)

## Projections

### `fulfillment_queue` — Fulfillment queue {#projection-fulfillment_queue}

Groups open customer-delivery commitments by their shortest order/evidence link and derives ship
readiness from active reservations and execution holds.

**Consumers:** MCP, Copilot, Operations · **Reads:** `business_event`, `document`, `source_record`,
`party`, `item`, `commitment`, `commitment_hold`, `party_hold`, `reservation`, `movement`

**Outputs:** `order_key`, `source_system`, `external_order_id`, `party`, `due_at`, `priority`,
`ship_ready`, `blocking_reasons`, `lines`

**How this query runs**

| Concrete query                                                     | Kind                           | Default |
| ------------------------------------------------------------------ | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/fulfillment_queue` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/fulfillment_queue`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `commitment.fulfilled`, `reservation.consumed`, `fact.observed`,
`source_record.interpreted`, `party.created`, `party.updated`, `party.delivery_hold_placed`,
`party.delivery_hold_released`, `item.updated`, `document.recorded`, `document.corrected`,
`commitment.created`, `commitment.cancelled`, `commitment.revised`, `promises.closed`,
`commitment.held`, `commitment.hold_released`, `reservation.created`, `reservation.released`,
`movement.recorded`, `movement.corrected`

**See also:** view [`orders`](./views#view-orders), view
[`warehouse_queue`](./views#view-warehouse_queue), agent tool
[`fulfillment_queue`](./commands#tool-fulfillment_queue)

### `fulfillment_blockers` — Fulfillment blockers {#projection-fulfillment_blockers}

Emits one rebuildable blocker row per open commitment and reason, including reservation shortages
and active order or party delivery holds.

**Consumers:** MCP, Copilot, Operational Exceptions · **Reads:** `business_event`, `document`,
`item`, `commitment`, `commitment_hold`, `party_hold`, `reservation`, `movement`

**Outputs:** `blocker_id`, `blocker_type`, `order_key`, `commitment_id`, `item_id`,
`shortage_quantity`, `due_at`

**How this query runs**

| Concrete query                                                        | Kind                           | Default |
| --------------------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/fulfillment_blockers` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/fulfillment_blockers`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `commitment.fulfilled`, `reservation.consumed`, `fact.observed`,
`source_record.interpreted`, `party.delivery_hold_placed`, `party.delivery_hold_released`,
`item.updated`, `document.recorded`, `document.corrected`, `commitment.created`,
`commitment.cancelled`, `commitment.revised`, `promises.closed`, `commitment.held`,
`commitment.hold_released`, `reservation.created`, `reservation.released`, `movement.recorded`,
`movement.corrected`

**See also:** view [`fulfillment_blockers`](./views#view-fulfillment_blockers), agent tool
[`fulfillment_blockers`](./commands#tool-fulfillment_blockers)

### `item_supply_demand` — Item supply and demand {#projection-item_supply_demand}

Materializes physical, allocated, incoming, open-demand, uncovered-demand and affected-order
quantities per item.

**Consumers:** MCP, Copilot, Inventory · **Reads:** `business_event`, `item`, `commitment`,
`reservation`, `movement`

**Outputs:** `item_id`, `sku`, `physical`, `reserved`, `available`, `incoming`,
`open_customer_demand`, `uncovered_demand`, `projected`, `blocked_order_count`

**How this query runs**

| Concrete query                                                      | Kind                           | Default |
| ------------------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/item_supply_demand` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/item_supply_demand`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `commitment.fulfilled`, `reservation.consumed`, `fact.observed`,
`party.delivery_hold_placed`, `party.delivery_hold_released`, `item.created`, `item.updated`,
`location.created`, `location.updated`, `commitment.created`, `commitment.cancelled`,
`commitment.revised`, `promises.closed`, `commitment.held`, `commitment.hold_released`,
`reservation.created`, `reservation.released`, `movement.recorded`, `movement.corrected`

**See also:** view [`supply_demand`](./views#view-supply_demand), agent tool
[`item_supply_demand`](./commands#tool-item_supply_demand)

### `tenant_usage` — Tenant usage {#projection-tenant_usage}

Uses a fixed number of tenant-scoped aggregate queries to classify the workspace as empty,
configured, or in use and derives the latest timestamp across source, operational, financial, event,
Change Proposal, and chat activity without loading business rows or querying once per tenant.

**Consumers:** Tenant management · **Reads:** `tenant`, `source_system`, `party`, `item`,
`location`, `source_record`, `document`, `commitment`, `reservation`, `movement`, `ledger_entry`,
`business_event`

**Outputs:** `state`, `source_count`, `evidence_count`, `reality_count`, `configured_count`,
`last_activity_at`

**How this query runs**

| Concrete query                                                | Kind                           | Default |
| ------------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/tenant_usage` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/tenant_usage`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `cost.attributed`, `cost.reviewed`, `shipment.notice_recorded`,
`shipment.event_recorded`, `shipment.event_superseded`, `finance.target_configuration_changed`,
`finance.source_mapping_changed`, `finance.component_assigned`, `finance.reference_changed`,
`finance.account_changed`, `credit.recorded`, `invoice.recorded`, `order.recorded`,
`source_record.stored`, `commitment.fulfilled`, `reservation.consumed`, `fact.observed`,
`source_record.received`, `source_record.unmapped`, `source_record.interpreted`, `party.created`,
`party.updated`, `party.delivery_hold_placed`, `party.delivery_hold_released`, `item.created`,
`item.updated`, `location.created`, `location.updated`, `master_data.lifecycle_changed`,
`payment_term.updated`, `payment_term.created`, `price_list.updated`, `price_list.created`,
`price_list_entry.created`, `party_price_list.assigned`, `party_group.updated`,
`party_group.created`, `party_group_member.added`, `party_group_price_list.assigned`,
`document.recorded`, `document.corrected`, `commitment.created`, `commitment.cancelled`,
`commitment.revised`, `promises.closed`, `payments.run`, `return.announced`,
`return.announcement_withdrawn`, `commitment.held`, `commitment.hold_released`,
`reservation.created`, `reservation.released`, `handling_unit.created`, `lot.created`,
`lot.expiry_stated`, `lot.expiry_corrected`, `serial_unit.created`, `movement.recorded`,
`movement.corrected`, `ledger.posted`, `ledger.reversed`, `settlement.allocated`

### `inventory` — Inventory {#projection-inventory}

Physical movement balance minus active reservations; incoming commitments are added for projected
stock.

**Consumers:** Home, Inventory, Chat, CLI · **Reads:** `item`, `location`, `movement`,
`reservation`, `commitment`

**Outputs:** `physical`, `reserved`, `available`, `incoming`, `projected`

**How this query runs**

| Concrete query                                             | Kind                           | Default |
| ---------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/inventory` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/inventory`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `commitment.fulfilled`, `reservation.consumed`, `fact.observed`,
`item.created`, `item.updated`, `location.created`, `location.updated`,
`master_data.lifecycle_changed`, `commitment.created`, `commitment.cancelled`, `commitment.revised`,
`promises.closed`, `reservation.created`, `reservation.released`, `movement.recorded`,
`movement.corrected`

**See also:** view [`inventory`](./views#view-inventory), agent tool
[`inventory_read`](./commands#tool-inventory_read), agent tool
[`reservation_propose`](./commands#tool-reservation_propose), agent tool
[`movement_create_propose`](./commands#tool-movement_create_propose)

### `exceptions` — Operational Exceptions {#projection-exceptions}

Finds operational exceptions such as shortages, overdue obligations, and active execution
restrictions.

**Consumers:** Home, Exceptions · **Reads:** `commitment`, `commitment_hold`, `party_hold`,
`movement`, `reservation`

**Outputs:** `severity`, `title`, `context`, `object_link`

**How this query runs**

| Concrete query                                              | Kind                           | Default |
| ----------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/exceptions` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/exceptions`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `shipment.notice_recorded`, `shipment.event_recorded`,
`shipment.event_superseded`, `source_record.stored`, `commitment.fulfilled`, `reservation.consumed`,
`fact.observed`, `source_record.received`, `source_record.unmapped`, `source_record.interpreted`,
`party.created`, `party.updated`, `party.delivery_hold_placed`, `party.delivery_hold_released`,
`item.created`, `item.updated`, `location.updated`, `document.recorded`, `document.corrected`,
`commitment.created`, `commitment.cancelled`, `commitment.revised`, `promises.closed`,
`payments.run`, `return.announced`, `return.announcement_withdrawn`, `commitment.held`,
`commitment.hold_released`, `reservation.created`, `reservation.released`, `lot.expiry_stated`,
`lot.expiry_corrected`, `movement.recorded`, `movement.corrected`, `ledger.posted`,
`ledger.reversed`, `settlement.allocated`

Also eligible for background refresh every 60 seconds, without a new business event.

**See also:** exception
[`overdue_outgoing_customer_commitment`](./exceptions#exception-overdue_outgoing_customer_commitment),
exception [`outgoing_commitment_at_risk`](./exceptions#exception-outgoing_commitment_at_risk),
exception [`order_stalled`](./exceptions#exception-order_stalled), exception
[`overdue_incoming_supplier_commitment`](./exceptions#exception-overdue_incoming_supplier_commitment),
exception [`shipped_not_billed`](./exceptions#exception-shipped_not_billed), exception
[`billed_not_received`](./exceptions#exception-billed_not_received), exception
[`invoice_price_differs`](./exceptions#exception-invoice_price_differs), exception
[`sold_below_purchase_price`](./exceptions#exception-sold_below_purchase_price), exception
[`returned_not_credited`](./exceptions#exception-returned_not_credited), exception
[`credited_not_returned`](./exceptions#exception-credited_not_returned), exception
[`supplier_return_not_credited`](./exceptions#exception-supplier_return_not_credited), exception
[`supplier_credit_not_returned`](./exceptions#exception-supplier_credit_not_returned), exception
[`return_unresolved`](./exceptions#exception-return_unresolved), exception
[`receipt_unbilled`](./exceptions#exception-receipt_unbilled), exception
[`units_not_comparable`](./exceptions#exception-units_not_comparable), exception
[`reservation_exceeds_stock`](./exceptions#exception-reservation_exceeds_stock), exception
[`silent_source`](./exceptions#exception-silent_source), exception
[`source_interpretation_failure`](./exceptions#exception-source_interpretation_failure), exception
[`unexplained_movement`](./exceptions#exception-unexplained_movement), exception
[`sales_invoice_unposted`](./exceptions#exception-sales_invoice_unposted), exception
[`supplier_invoice_unposted`](./exceptions#exception-supplier_invoice_unposted), exception
[`credit_note_unposted`](./exceptions#exception-credit_note_unposted), exception
[`credit_note_unsettled`](./exceptions#exception-credit_note_unsettled), exception
[`supplier_credit_unposted`](./exceptions#exception-supplier_credit_unposted), exception
[`supplier_credit_unclaimed`](./exceptions#exception-supplier_credit_unclaimed), exception
[`overdue_receivable`](./exceptions#exception-overdue_receivable), exception
[`credit_limit_exceeded`](./exceptions#exception-credit_limit_exceeded), exception
[`overdue_payable`](./exceptions#exception-overdue_payable), exception
[`purchase_discount_available`](./exceptions#exception-purchase_discount_available), exception
[`duplicate_supplier_invoice`](./exceptions#exception-duplicate_supplier_invoice), exception
[`unmatched_financial_event`](./exceptions#exception-unmatched_financial_event), exception
[`announced_return_not_arrived`](./exceptions#exception-announced_return_not_arrived), exception
[`commitment_hold_unreleased`](./exceptions#exception-commitment_hold_unreleased), exception
[`party_hold_unreleased`](./exceptions#exception-party_hold_unreleased), exception
[`stock_expired`](./exceptions#exception-stock_expired), exception
[`missing_acquisition_cost`](./exceptions#exception-missing_acquisition_cost), exception
[`unassigned_cost_component`](./exceptions#exception-unassigned_cost_component), exception
[`stale_cost_review`](./exceptions#exception-stale_cost_review), exception
[`negative_actual_db1`](./exceptions#exception-negative_actual_db1)

### `commitment_register` — Commitment register {#projection-commitment_register}

Combines obligations with allocated and physically fulfilled quantities without storing fulfillment
status on documents.

**Consumers:** Commitments · **Reads:** `commitment`, `reservation`, `movement`, `party`, `item`,
`location`

**Outputs:** `commitment`, `reserved`, `fulfilled`, `open_quantity`, `counterparty`

**How this query runs**

| Concrete query                                                       | Kind                           | Default |
| -------------------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/commitment_register` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/commitment_register`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `order.recorded`, `commitment.fulfilled`, `reservation.consumed`,
`fact.observed`, `party.created`, `party.updated`, `party.delivery_hold_placed`,
`party.delivery_hold_released`, `item.updated`, `location.updated`, `commitment.created`,
`commitment.cancelled`, `commitment.revised`, `promises.closed`, `commitment.held`,
`commitment.hold_released`, `reservation.created`, `reservation.released`, `movement.recorded`,
`movement.corrected`

**See also:** agent tool [`commitments_list`](./commands#tool-commitments_list), agent tool
[`reservation_propose`](./commands#tool-reservation_propose), agent tool
[`order_create_propose`](./commands#tool-order_create_propose), agent tool
[`movement_create_propose`](./commands#tool-movement_create_propose)

### `document_register` — Document register {#projection-document_register}

Presents evidence and counts its shortest links into operational Reality.

**Consumers:** Documents · **Reads:** `document`, `document_line`, `commitment`, `source_record`

**Outputs:** `document`, `line_count`, `commitment_count`, `source`

**How this query runs**

| Concrete query                                                     | Kind                           | Default |
| ------------------------------------------------------------------ | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/document_register` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/document_register`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `order.recorded`, `commitment.fulfilled`, `source_record.interpreted`,
`party.created`, `party.updated`, `payment_term.updated`, `document.recorded`, `document.corrected`,
`commitment.created`, `commitment.cancelled`

**See also:** agent tool [`order_create_propose`](./commands#tool-order_create_propose)

### `open_financial_items` — Open financial items {#projection-open_financial_items}

Invoice-side ledger amount minus explicit payment allocations; document status is not used as
payment truth.

**Consumers:** Open Items, Home · **Reads:** `ledger_entry`, `settlement_allocation`, `document`,
`party`

**Outputs:** `invoice`, `party`, `original_amount`, `allocated_amount`, `open_amount`

**How this query runs**

| Concrete query                                                        | Kind                           | Default |
| --------------------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/open_financial_items` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/open_financial_items`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `credit.recorded`, `invoice.recorded`, `party.updated`,
`payment_term.updated`, `document.recorded`, `document.corrected`, `payments.run`, `ledger.posted`,
`ledger.reversed`, `settlement.allocated`

**See also:** view [`open_items`](./views#view-open_items)

### `payments` — Payments {#projection-payments}

Groups payment postings with their explicit invoice allocations.

**Consumers:** Payments · **Reads:** `ledger_entry`, `settlement_allocation`, `document`, `party`

**Outputs:** `payment`, `party`, `amount`, `allocations`

**How this query runs**

| Concrete query                                            | Kind                           | Default |
| --------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/payments` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/payments`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `party.created`, `party.updated`, `document.corrected`,
`payments.run`, `ledger.posted`, `ledger.reversed`, `settlement.allocated`

### `journal` — Journal {#projection-journal}

Orders immutable ledger postings by effective time and posting group.

**Consumers:** Journal · **Reads:** `ledger_entry`

**Outputs:** `posting_group`, `account`, `party`, `debit_credit`, `amount`, `currency`

**How this query runs**

| Concrete query                                           | Kind                           | Default |
| -------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/journal` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/journal`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `finance.account_changed`, `payments.run`, `ledger.posted`,
`ledger.reversed`

### `timeline` — Timeline {#projection-timeline}

Normalizes important evidence and reality timestamps into one chronological operational history.

**Consumers:** Timeline · **Reads:** `source_record`, `document`, `commitment`, `reservation`,
`movement`, `shipment`, `shipment_package`, `shipment_event`, `ledger_entry`, `action`

**Outputs:** `occurred_at`, `record_type`, `title`, `detail`, `object_link`

**How this query runs**

| Concrete query                                            | Kind                           | Default |
| --------------------------------------------------------- | ------------------------------ | ------- |
| `GET /api/tenants/{tenant}/projection-snapshots/timeline` | Stored — updated in background | —       |
| `GET /api/tenants/{tenant}/projections/timeline`          | Stored — updated in background | —       |

[How this query runs](./views#read-execution)

**Background refresh after:** `cost.attributed`, `cost.reviewed`, `shipment.notice_recorded`,
`shipment.event_recorded`, `shipment.event_superseded`, `finance.component_assigned`,
`credit.recorded`, `invoice.recorded`, `order.recorded`, `source_record.stored`,
`commitment.fulfilled`, `reservation.consumed`, `fact.observed`, `source_record.received`,
`source_record.unmapped`, `source_record.interpreted`, `party.created`, `party.updated`,
`item.created`, `item.updated`, `location.created`, `location.updated`, `document.recorded`,
`document.corrected`, `commitment.created`, `commitment.cancelled`, `commitment.revised`,
`promises.closed`, `payments.run`, `return.announced`, `return.announcement_withdrawn`,
`commitment.held`, `commitment.hold_released`, `reservation.created`, `reservation.released`,
`handling_unit.created`, `lot.created`, `lot.expiry_stated`, `lot.expiry_corrected`,
`serial_unit.created`, `movement.recorded`, `movement.corrected`, `ledger.posted`,
`ledger.reversed`, `settlement.allocated`

**See also:** agent tool [`fact_observe_propose`](./commands#tool-fact_observe_propose), agent tool
[`movement_create_propose`](./commands#tool-movement_create_propose), agent tool
[`finance_initialize_accounts_propose`](./commands#tool-finance_initialize_accounts_propose), agent
tool [`finance_create_account_propose`](./commands#tool-finance_create_account_propose), agent tool
[`finance_update_account_propose`](./commands#tool-finance_update_account_propose), agent tool
[`finance_set_default_account_propose`](./commands#tool-finance_set_default_account_propose)

### `price_resolution` — Price resolution {#projection-price_resolution}

Direct party lists precede group lists and the default list; the highest valid minimum-quantity tier
wins. Each parameterized question is calculated live from the current canonical pricing rules; no
stored result or unrelated projection refresh is used.

**Consumers:** Pricing, API, CLI · **Reads:** `price_list`, `price_list_entry`, `party_price_list`,
`party_group`, `party_group_member`, `party_group_price_list`

**Outputs:** `unit_price`, `currency`, `unit`, `price_list_id`, `price_list_entry_id`, `source`

**How this query runs**

| Concrete query                             | Kind                              | Default |
| ------------------------------------------ | --------------------------------- | ------- |
| `GET /api/tenants/{tenant}/prices/resolve` | Live — calculated for your inputs | —       |

[How this query runs](./views#read-execution)

## Actions

| Key                                                              | Label                                 | Command                                                                     | Confirmation     | Prerequisites                                       |
| ---------------------------------------------------------------- | ------------------------------------- | --------------------------------------------------------------------------- | ---------------- | --------------------------------------------------- |
| [`create_manual_order`](#action-create_manual_order)             | Create manual sales or purchase order | [`create_manual_order`](./commands#command-create_manual_order)             | `summary`        | `company_party`, `counterparty`, `location`, `item` |
| [`observe_fact`](#action-observe_fact)                           | Observe source-supported fact         | [`observe_fact`](./commands#command-observe_fact)                           | `summary`        | `source_record`, `subject`                          |
| [`post_customer_payment`](#action-post_customer_payment)         | Post customer payment                 | [`post_customer_payment`](./commands#command-post_customer_payment)         | `summary`        | `customer_invoice`                                  |
| [`post_supplier_payment`](#action-post_supplier_payment)         | Post supplier payment                 | [`post_supplier_payment`](./commands#command-post_supplier_payment)         | `summary`        | `supplier_invoice`                                  |
| [`reserve_stock`](#action-reserve_stock)                         | Reserve stock                         | [`reserve`](./commands#command-reserve)                                     | `summary`        | `commitment`                                        |
| [`record_movement`](#action-record_movement)                     | Record movement                       | [`record_movement`](./commands#command-record_movement)                     | `summary`        | `item`, `location`                                  |
| [`correct_movement`](#action-correct_movement)                   | Correct movement                      | [`correct_movement`](./commands#command-correct_movement)                   | `server_preview` | `movement`                                          |
| [`hold_commitment`](#action-hold_commitment)                     | Hold or release commitment            | [`hold_commitment`](./commands#command-hold_commitment)                     | `summary`        | `commitment`                                        |
| [`hold_document_commitments`](#action-hold_document_commitments) | Hold or release document commitments  | [`hold_document_commitments`](./commands#command-hold_document_commitments) | `summary`        | `document`                                          |
| [`party_delivery_hold`](#action-party_delivery_hold)             | Set or release party delivery hold    | [`hold_party_delivery`](./commands#command-hold_party_delivery)             | `summary`        | `party`                                             |
| [`create_handling_unit`](#action-create_handling_unit)           | Create handling unit                  | [`create_handling_unit`](./commands#command-create_handling_unit)           | `summary`        | —                                                   |
| [`create_lot`](#action-create_lot)                               | Create lot                            | [`create_lot`](./commands#command-create_lot)                               | `summary`        | `item`                                              |
| [`create_serial_unit`](#action-create_serial_unit)               | Create serial unit                    | [`create_serial_unit`](./commands#command-create_serial_unit)               | `summary`        | `item`                                              |

### `create_manual_order` — Create manual sales or purchase order {#action-create_manual_order}

**Command:** [`create_manual_order`](./commands#command-create_manual_order) · **Confirmation:**
`summary` · **Prerequisites:** `company_party`, `counterparty`, `location`, `item`

**See also:** command [`create_manual_order`](./commands#command-create_manual_order), view
[`documents`](./views#view-documents), workspace [`operations`](./views#workspace-operations)

### `observe_fact` — Observe source-supported fact {#action-observe_fact}

**Command:** [`observe_fact`](./commands#command-observe_fact) · **Confirmation:** `summary` ·
**Prerequisites:** `source_record`, `subject`

**See also:** command [`observe_fact`](./commands#command-observe_fact), workspace
[`company`](./views#workspace-company)

### `post_customer_payment` — Post customer payment {#action-post_customer_payment}

**Command:** [`post_customer_payment`](./commands#command-post_customer_payment) · **Confirmation:**
`summary` · **Prerequisites:** `customer_invoice`

**See also:** command [`post_customer_payment`](./commands#command-post_customer_payment), view
[`payments`](./views#view-payments), workspace [`finance`](./views#workspace-finance)

### `post_supplier_payment` — Post supplier payment {#action-post_supplier_payment}

**Command:** [`post_supplier_payment`](./commands#command-post_supplier_payment) · **Confirmation:**
`summary` · **Prerequisites:** `supplier_invoice`

**See also:** command [`post_supplier_payment`](./commands#command-post_supplier_payment), view
[`payments`](./views#view-payments), workspace [`finance`](./views#workspace-finance)

### `reserve_stock` — Reserve stock {#action-reserve_stock}

**Command:** [`reserve`](./commands#command-reserve) · **Confirmation:** `summary` ·
**Prerequisites:** `commitment`

**See also:** command [`reserve`](./commands#command-reserve), view
[`reservations`](./views#view-reservations), workspace [`operations`](./views#workspace-operations),
workspace [`warehouse`](./views#workspace-warehouse)

### `record_movement` — Record movement {#action-record_movement}

**Command:** [`record_movement`](./commands#command-record_movement) · **Confirmation:** `summary` ·
**Prerequisites:** `item`, `location`

**See also:** command [`record_movement`](./commands#command-record_movement), view
[`movements`](./views#view-movements), workspace [`warehouse`](./views#workspace-warehouse)

### `correct_movement` — Correct movement {#action-correct_movement}

**Command:** [`correct_movement`](./commands#command-correct_movement) · **Confirmation:**
`server_preview` · **Prerequisites:** `movement`

**See also:** command [`correct_movement`](./commands#command-correct_movement), view
[`movements`](./views#view-movements), workspace [`warehouse`](./views#workspace-warehouse)

### `hold_commitment` — Hold or release commitment {#action-hold_commitment}

**Command:** [`hold_commitment`](./commands#command-hold_commitment) · **Confirmation:** `summary` ·
**Prerequisites:** `commitment`

**See also:** command [`hold_commitment`](./commands#command-hold_commitment), view
[`commitments`](./views#view-commitments), workspace [`operations`](./views#workspace-operations),
workspace [`warehouse`](./views#workspace-warehouse)

### `hold_document_commitments` — Hold or release document commitments {#action-hold_document_commitments}

**Command:** [`hold_document_commitments`](./commands#command-hold_document_commitments) ·
**Confirmation:** `summary` · **Prerequisites:** `document`

**See also:** command [`hold_document_commitments`](./commands#command-hold_document_commitments),
view [`documents`](./views#view-documents), workspace [`operations`](./views#workspace-operations)

### `party_delivery_hold` — Set or release party delivery hold {#action-party_delivery_hold}

**Command:** [`hold_party_delivery`](./commands#command-hold_party_delivery) · **Confirmation:**
`summary` · **Prerequisites:** `party`

**See also:** command [`hold_party_delivery`](./commands#command-hold_party_delivery), view
[`parties`](./views#view-parties), workspace [`operations`](./views#workspace-operations)

### `create_handling_unit` — Create handling unit {#action-create_handling_unit}

**Command:** [`create_handling_unit`](./commands#command-create_handling_unit) · **Confirmation:**
`summary` · **Prerequisites:** —

**See also:** command [`create_handling_unit`](./commands#command-create_handling_unit), view
[`movements`](./views#view-movements), workspace [`warehouse`](./views#workspace-warehouse)

### `create_lot` — Create lot {#action-create_lot}

**Command:** [`create_lot`](./commands#command-create_lot) · **Confirmation:** `summary` ·
**Prerequisites:** `item`

**See also:** command [`create_lot`](./commands#command-create_lot), view
[`movements`](./views#view-movements), workspace [`warehouse`](./views#workspace-warehouse)

### `create_serial_unit` — Create serial unit {#action-create_serial_unit}

**Command:** [`create_serial_unit`](./commands#command-create_serial_unit) · **Confirmation:**
`summary` · **Prerequisites:** `item`

**See also:** command [`create_serial_unit`](./commands#command-create_serial_unit), view
[`movements`](./views#view-movements), workspace [`warehouse`](./views#workspace-warehouse)
