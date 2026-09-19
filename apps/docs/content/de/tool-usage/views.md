# Sichten, Projections und Aktionen

Wo jemand hinschaut und was er dort auslösen kann. Eine Sicht ist entweder ein autoritatives
Register oder eine materialisierte Projection; eine Aktion startet eine Geschäftsaktion.

> Automatisch aus `workspace_catalog.yaml`, `projection_catalog.yaml` erzeugt. Diese Seite nicht von
> Hand bearbeiten.

## So wird diese Abfrage ausgeführt {#read-execution}

**Vorberechnet — im Hintergrund aktualisiert**

Liest die zuletzt fertig berechnete Projektion. Öffnen oder Aktualisieren der Seite berechnet sie
nicht neu und stellt keinen Job ein; Scheduler und Worker aktualisieren sie nach relevanten
abgeschlossenen Business Events.

**Live — beim Aufruf gelesen**

Liest oder berechnet das Ergebnis beim Aufruf aus den aktuell in Reality vorhandenen Datensätzen.
Das bedeutet nicht, dass externe Systeme gerade synchronisiert wurden.

**Live — für deine Eingaben berechnet**

Berechnet die Antwort beim Aufruf für den angegebenen Geschäftspartner, Artikel, die Menge, Währung,
Einheit und den Zeitpunkt. Die Preisermittlung verwendet die aktuellen Preisregeln und keine
gespeicherte Preisprojektion.

Der Modus gehört zur konkreten Abfrage, nicht zum Geschäftsbegriff. Der Inspector kann den
vorberechneten Bestand lesen, während die Lagerseite und die normale MCP-Bestandsabfrage live lesen.
Bei den fünf operativen MCP-Seitenabfragen ist page der Standard; response_format=legacy liest
gespeicherte Ergebnisse. Direkte Aufrufe der Anwendungstools behalten legacy als Standard. Die
Spalte Art beschreibt die Katalogsicht und nicht jeden ähnlich benannten Web-Bildschirm. Alle
HTTP-Pfade unten sind firmenbezogene GET-Abfragen.

Events melden Aktualisierungsbedarf; sie berechnen nicht synchron jede Sicht neu. Unbekannte
Event-Typen machen gespeicherte Projektionen vorsorglich aktualisierungsbedürftig. Bei Verzögerungen
oder einem ausgefallenen Worker bleibt das letzte fertige Ergebnis sichtbar. Zeitabhängige
Abweichungen, Verpflichtungsrisiken und Firmenaktivität werden zusätzlich jede Minute
berücksichtigt. Neue Firmen und neue Berechnungsversionen werden im Hintergrund initialisiert.
Aktionen prüfen weiterhin die maßgeblichen Datensätze.

Die Metadaten melden `uninitialized` (erste Berechnung ausstehend), `ready` (bekannte relevante
Events verarbeitet), `pending` (Aktualisierung ausstehend) oder `failed` (Berechnung
fehlgeschlagen). `completed_at` nennt den Zeitpunkt der fertigen Berechnung; verarbeitete und
angestrebte Event-Sequenz zeigen den lokalen Fortschritt. Fehlende Daten vor der ersten Berechnung
bedeuten nicht, dass es keine Geschäftsdaten gibt. Die Aktualität externer Quellen bleibt unbekannt.

## Arbeitsbereiche

### `company` — Company Overview {#workspace-company}

**Sichten:** [`commitments`](./views#view-commitments), [`inventory`](./views#view-inventory),
[`open_items`](./views#view-open_items), [`documents`](./views#view-documents),
[`activity`](./views#view-activity)

**Aktionen:** [`observe_fact`](./views#action-observe_fact)

### `operations` — Order Operations {#workspace-operations}

**Sichten:** [`orders`](./views#view-orders), [`commitments`](./views#view-commitments),
[`reservations`](./views#view-reservations), [`inventory`](./views#view-inventory),
[`fulfillment_blockers`](./views#view-fulfillment_blockers),
[`supply_demand`](./views#view-supply_demand), [`documents`](./views#view-documents)

**Aktionen:** [`create_manual_order`](./views#action-create_manual_order),
[`reserve_stock`](./views#action-reserve_stock),
[`hold_commitment`](./views#action-hold_commitment),
[`hold_document_commitments`](./views#action-hold_document_commitments),
[`party_delivery_hold`](./views#action-party_delivery_hold)

### `warehouse` — Warehouse Operations {#workspace-warehouse}

**Sichten:** [`inventory`](./views#view-inventory),
[`warehouse_queue`](./views#view-warehouse_queue), [`reservations`](./views#view-reservations),
[`movements`](./views#view-movements), [`fulfillment_blockers`](./views#view-fulfillment_blockers),
[`supply_demand`](./views#view-supply_demand), [`commitments`](./views#view-commitments),
[`locations`](./views#view-locations)

**Aktionen:** [`record_movement`](./views#action-record_movement),
[`reserve_stock`](./views#action-reserve_stock),
[`hold_commitment`](./views#action-hold_commitment),
[`correct_movement`](./views#action-correct_movement),
[`create_handling_unit`](./views#action-create_handling_unit),
[`create_lot`](./views#action-create_lot), [`create_serial_unit`](./views#action-create_serial_unit)

### `finance` — Finance Control {#workspace-finance}

**Sichten:** [`open_items`](./views#view-open_items), [`payments`](./views#view-payments),
[`journal`](./views#view-journal), [`documents`](./views#view-documents),
[`parties`](./views#view-parties)

**Aktionen:** [`post_customer_payment`](./views#action-post_customer_payment),
[`post_supplier_payment`](./views#action-post_supplier_payment)

### `data` — Data Management {#workspace-data}

**Sichten:** [`parties`](./views#view-parties), [`items`](./views#view-items),
[`locations`](./views#view-locations), [`documents`](./views#view-documents),
[`commercial_terms`](./views#view-commercial_terms)

## Sichten

| Schlüssel                                            | Bezeichnung          | Route                  | Art                       | Projection             |
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

**Route:** `commitments` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                               | Art                        | Standard |
| ---------------------------------------------- | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/commitment-control` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`company`](./views#workspace-company), Arbeitsbereich
[`operations`](./views#workspace-operations), Arbeitsbereich
[`warehouse`](./views#workspace-warehouse)

### `inventory` — Inventory {#view-inventory}

Physical

**Route:** `inventory` · **Art:** `materialized_projection`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                           | Art                                        | Standard |
| ---------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/inventory` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/warehouse/stock`                | Live — beim Aufruf gelesen                 | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Projection [`inventory`](./views#projection-inventory), Arbeitsbereich
[`company`](./views#workspace-company), Arbeitsbereich [`operations`](./views#workspace-operations),
Arbeitsbereich [`warehouse`](./views#workspace-warehouse)

### `open_items` — Open items {#view-open_items}

Financial items with their authoritative open amount

**Route:** `open-items` · **Art:** `materialized_projection`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                      | Art                                        | Standard |
| --------------------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/open_financial_items` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/finance/open-items?flow=receivable`        | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/finance/open-items?flow=payable`           | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/finance/open-items?flow=customer-credit`   | Live — beim Aufruf gelesen                 | —        |
| `GET /api/tenants/{tenant}/finance/open-items?flow=customer-balance`  | Live — beim Aufruf gelesen                 | —        |
| `GET /api/tenants/{tenant}/finance/open-items?flow=supplier-balance`  | Live — beim Aufruf gelesen                 | —        |
| `GET /api/tenants/{tenant}/finance/open-items?flow=customer-balances` | Live — beim Aufruf gelesen                 | —        |
| `GET /api/tenants/{tenant}/finance/open-items?flow=supplier-balances` | Live — beim Aufruf gelesen                 | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Projection [`open_financial_items`](./views#projection-open_financial_items),
Arbeitsbereich [`company`](./views#workspace-company), Arbeitsbereich
[`finance`](./views#workspace-finance)

### `documents` — Documents {#view-documents}

Normalized Evidence and its links into Reality

**Route:** `documents` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                               | Art                        | Standard |
| ---------------------------------------------- | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/evidence-documents` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`company`](./views#workspace-company), Arbeitsbereich
[`operations`](./views#workspace-operations), Arbeitsbereich [`finance`](./views#workspace-finance),
Arbeitsbereich [`data`](./views#workspace-data)

### `reservations` — Reservations {#view-reservations}

Active stock allocations linked to Commitments

**Route:** `reservations` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                         | Art                        | Standard |
| ---------------------------------------- | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/reservations` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`operations`](./views#workspace-operations), Arbeitsbereich
[`warehouse`](./views#workspace-warehouse)

### `movements` — Movements {#view-movements}

Append-only physical inventory journal

**Route:** `movements` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                      | Art                        | Standard |
| ------------------------------------- | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/movements` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`warehouse`](./views#workspace-warehouse)

### `locations` — Locations {#view-locations}

Stock-capable and logical locations

**Route:** `locations` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                      | Art                        | Standard |
| ------------------------------------- | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/locations` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`warehouse`](./views#workspace-warehouse), Arbeitsbereich
[`data`](./views#workspace-data)

### `payments` — Payments {#view-payments}

Payment postings and allocations

**Route:** `payments` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                             | Art                        | Standard |
| -------------------------------------------- | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/finance/payments` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`finance`](./views#workspace-finance)

### `journal` — Journal {#view-journal}

Immutable balanced ledger entries

**Route:** `journal` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                            | Art                        | Standard |
| ------------------------------------------- | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/finance/journal` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`finance`](./views#workspace-finance)

### `parties` — Parties {#view-parties}

Customers

**Route:** `parties` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                    | Art                        | Standard |
| ----------------------------------- | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/parties` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`finance`](./views#workspace-finance), Arbeitsbereich
[`data`](./views#workspace-data)

### `items` — Items {#view-items}

Operational item identities

**Route:** `items` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                  | Art                        | Standard |
| --------------------------------- | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/items` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`data`](./views#workspace-data)

### `commercial_terms` — Commercial terms {#view-commercial_terms}

Payment and pricing references

**Route:** `commercial` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                           | Art                        | Standard |
| ------------------------------------------ | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/payment-terms`  | Live — beim Aufruf gelesen | —        |
| `GET /api/tenants/{tenant}/price-lists`    | Live — beim Aufruf gelesen | —        |
| `GET /api/tenants/{tenant}/pricing-groups` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`data`](./views#workspace-data)

### `sources_imports` — Sources & imports {#view-sources_imports}

Source definitions and immutable intake

**Route:** `integrations` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                         | Art                        | Standard |
| ---------------------------------------- | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/integrations` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

### `activity` — Activity {#view-activity}

Cross-functional operational and financial event history

**Route:** `timeline` · **Art:** `authoritative_register`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                     | Art                        | Standard |
| ------------------------------------ | -------------------------- | -------- |
| `GET /api/tenants/{tenant}/timeline` | Live — beim Aufruf gelesen | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Arbeitsbereich [`company`](./views#workspace-company)

### `orders` — Orders {#view-orders}

Customer orders with readiness

**Route:** `orders` · **Art:** `materialized_projection`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                   | Art                                        | Standard |
| ------------------------------------------------------------------ | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/fulfillment_queue` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projection-views/fulfillment_queue`     | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Projection [`fulfillment_queue`](./views#projection-fulfillment_queue),
Arbeitsbereich [`operations`](./views#workspace-operations)

### `warehouse_queue` — Warehouse Queue {#view-warehouse_queue}

Orders prioritized for warehouse execution and shipment readiness

**Route:** `warehouse-queue` · **Art:** `materialized_projection`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                   | Art                                        | Standard |
| ------------------------------------------------------------------ | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/fulfillment_queue` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projection-views/fulfillment_queue`     | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Projection [`fulfillment_queue`](./views#projection-fulfillment_queue),
Arbeitsbereich [`warehouse`](./views#workspace-warehouse)

### `fulfillment_blockers` — Fulfillment blockers {#view-fulfillment_blockers}

Commitment shortages and active execution holds blocking fulfillment

**Route:** `fulfillment-blockers` · **Art:** `materialized_projection`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                      | Art                                        | Standard |
| --------------------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/fulfillment_blockers` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projection-views/fulfillment_blockers`     | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Projection [`fulfillment_blockers`](./views#projection-fulfillment_blockers),
Arbeitsbereich [`operations`](./views#workspace-operations), Arbeitsbereich
[`warehouse`](./views#workspace-warehouse)

### `supply_demand` — Supply & demand {#view-supply_demand}

Item-level physical stock

**Route:** `supply-demand` · **Art:** `materialized_projection`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                    | Art                                        | Standard |
| ------------------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/item_supply_demand` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projection-views/item_supply_demand`     | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Siehe auch:** Projection [`item_supply_demand`](./views#projection-item_supply_demand),
Arbeitsbereich [`operations`](./views#workspace-operations), Arbeitsbereich
[`warehouse`](./views#workspace-warehouse)

## Projections

### `fulfillment_queue` — Fulfillment queue {#projection-fulfillment_queue}

Groups open customer-delivery commitments by their shortest order/evidence link and derives ship
readiness from active reservations and execution holds.

**Verbraucher:** MCP, Copilot, Operations · **Liest:** `business_event`, `document`,
`source_record`, `party`, `item`, `commitment`, `commitment_hold`, `party_hold`, `reservation`,
`movement`

**Ausgaben:** `order_key`, `source_system`, `external_order_id`, `party`, `due_at`, `priority`,
`ship_ready`, `blocking_reasons`, `lines`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                   | Art                                        | Standard |
| ------------------------------------------------------------------ | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/fulfillment_queue` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/fulfillment_queue`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `commitment.fulfilled`, `reservation.consumed`, `fact.observed`,
`source_record.interpreted`, `party.created`, `party.updated`, `party.delivery_hold_placed`,
`party.delivery_hold_released`, `item.updated`, `document.recorded`, `document.corrected`,
`commitment.created`, `commitment.cancelled`, `commitment.revised`, `promises.closed`,
`commitment.held`, `commitment.hold_released`, `reservation.created`, `reservation.released`,
`movement.recorded`, `movement.corrected`

**Siehe auch:** Sicht [`orders`](./views#view-orders), Sicht
[`warehouse_queue`](./views#view-warehouse_queue), Agenten-Tool
[`fulfillment_queue`](./commands#tool-fulfillment_queue)

### `fulfillment_blockers` — Fulfillment blockers {#projection-fulfillment_blockers}

Emits one rebuildable blocker row per open commitment and reason, including reservation shortages
and active order or party delivery holds.

**Verbraucher:** MCP, Copilot, Operational Exceptions · **Liest:** `business_event`, `document`,
`item`, `commitment`, `commitment_hold`, `party_hold`, `reservation`, `movement`

**Ausgaben:** `blocker_id`, `blocker_type`, `order_key`, `commitment_id`, `item_id`,
`shortage_quantity`, `due_at`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                      | Art                                        | Standard |
| --------------------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/fulfillment_blockers` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/fulfillment_blockers`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `commitment.fulfilled`, `reservation.consumed`, `fact.observed`,
`source_record.interpreted`, `party.delivery_hold_placed`, `party.delivery_hold_released`,
`item.updated`, `document.recorded`, `document.corrected`, `commitment.created`,
`commitment.cancelled`, `commitment.revised`, `promises.closed`, `commitment.held`,
`commitment.hold_released`, `reservation.created`, `reservation.released`, `movement.recorded`,
`movement.corrected`

**Siehe auch:** Sicht [`fulfillment_blockers`](./views#view-fulfillment_blockers), Agenten-Tool
[`fulfillment_blockers`](./commands#tool-fulfillment_blockers)

### `item_supply_demand` — Item supply and demand {#projection-item_supply_demand}

Materializes physical, allocated, incoming, open-demand, uncovered-demand and affected-order
quantities per item.

**Verbraucher:** MCP, Copilot, Inventory · **Liest:** `business_event`, `item`, `commitment`,
`reservation`, `movement`

**Ausgaben:** `item_id`, `sku`, `physical`, `reserved`, `available`, `incoming`,
`open_customer_demand`, `uncovered_demand`, `projected`, `blocked_order_count`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                    | Art                                        | Standard |
| ------------------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/item_supply_demand` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/item_supply_demand`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `commitment.fulfilled`, `reservation.consumed`, `fact.observed`,
`party.delivery_hold_placed`, `party.delivery_hold_released`, `item.created`, `item.updated`,
`location.created`, `location.updated`, `commitment.created`, `commitment.cancelled`,
`commitment.revised`, `promises.closed`, `commitment.held`, `commitment.hold_released`,
`reservation.created`, `reservation.released`, `movement.recorded`, `movement.corrected`

**Siehe auch:** Sicht [`supply_demand`](./views#view-supply_demand), Agenten-Tool
[`item_supply_demand`](./commands#tool-item_supply_demand)

### `tenant_usage` — Tenant usage {#projection-tenant_usage}

Uses a fixed number of tenant-scoped aggregate queries to classify the workspace as empty,
configured, or in use and derives the latest timestamp across source, operational, financial, event,
Change Proposal, and chat activity without loading business rows or querying once per tenant.

**Verbraucher:** Tenant management · **Liest:** `tenant`, `source_system`, `party`, `item`,
`location`, `source_record`, `document`, `commitment`, `reservation`, `movement`, `ledger_entry`,
`business_event`

**Ausgaben:** `state`, `source_count`, `evidence_count`, `reality_count`, `configured_count`,
`last_activity_at`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                              | Art                                        | Standard |
| ------------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/tenant_usage` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/tenant_usage`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `shipment.notice_recorded`, `shipment.event_recorded`,
`shipment.event_superseded`, `finance.target_configuration_changed`,
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

**Verbraucher:** Home, Inventory, Chat, CLI · **Liest:** `item`, `location`, `movement`,
`reservation`, `commitment`

**Ausgaben:** `physical`, `reserved`, `available`, `incoming`, `projected`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                           | Art                                        | Standard |
| ---------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/inventory` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/inventory`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `commitment.fulfilled`, `reservation.consumed`, `fact.observed`,
`item.created`, `item.updated`, `location.created`, `location.updated`,
`master_data.lifecycle_changed`, `commitment.created`, `commitment.cancelled`, `commitment.revised`,
`promises.closed`, `reservation.created`, `reservation.released`, `movement.recorded`,
`movement.corrected`

**Siehe auch:** Sicht [`inventory`](./views#view-inventory), Agenten-Tool
[`inventory_read`](./commands#tool-inventory_read), Agenten-Tool
[`reservation_propose`](./commands#tool-reservation_propose), Agenten-Tool
[`movement_create_propose`](./commands#tool-movement_create_propose)

### `exceptions` — Operational Exceptions {#projection-exceptions}

Finds operational exceptions such as shortages, overdue obligations, and active execution
restrictions.

**Verbraucher:** Home, Exceptions · **Liest:** `commitment`, `commitment_hold`, `party_hold`,
`movement`, `reservation`

**Ausgaben:** `severity`, `title`, `context`, `object_link`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                            | Art                                        | Standard |
| ----------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/exceptions` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/exceptions`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `shipment.notice_recorded`, `shipment.event_recorded`,
`shipment.event_superseded`, `source_record.stored`, `commitment.fulfilled`, `reservation.consumed`,
`fact.observed`, `source_record.received`, `source_record.unmapped`, `source_record.interpreted`,
`party.created`, `party.updated`, `party.delivery_hold_placed`, `party.delivery_hold_released`,
`item.created`, `item.updated`, `location.updated`, `document.recorded`, `document.corrected`,
`commitment.created`, `commitment.cancelled`, `commitment.revised`, `promises.closed`,
`payments.run`, `return.announced`, `return.announcement_withdrawn`, `commitment.held`,
`commitment.hold_released`, `reservation.created`, `reservation.released`, `lot.expiry_stated`,
`lot.expiry_corrected`, `movement.recorded`, `movement.corrected`, `ledger.posted`,
`ledger.reversed`, `settlement.allocated`

Zusätzlich alle 60 Sekunden für eine Hintergrundaktualisierung vorgesehen, auch ohne neues Business
Event.

**Siehe auch:** Ausnahme
[`overdue_outgoing_customer_commitment`](./exceptions#exception-overdue_outgoing_customer_commitment),
Ausnahme [`outgoing_commitment_at_risk`](./exceptions#exception-outgoing_commitment_at_risk),
Ausnahme [`order_stalled`](./exceptions#exception-order_stalled), Ausnahme
[`overdue_incoming_supplier_commitment`](./exceptions#exception-overdue_incoming_supplier_commitment),
Ausnahme [`shipped_not_billed`](./exceptions#exception-shipped_not_billed), Ausnahme
[`billed_not_received`](./exceptions#exception-billed_not_received), Ausnahme
[`invoice_price_differs`](./exceptions#exception-invoice_price_differs), Ausnahme
[`sold_below_purchase_price`](./exceptions#exception-sold_below_purchase_price), Ausnahme
[`returned_not_credited`](./exceptions#exception-returned_not_credited), Ausnahme
[`credited_not_returned`](./exceptions#exception-credited_not_returned), Ausnahme
[`supplier_return_not_credited`](./exceptions#exception-supplier_return_not_credited), Ausnahme
[`supplier_credit_not_returned`](./exceptions#exception-supplier_credit_not_returned), Ausnahme
[`return_unresolved`](./exceptions#exception-return_unresolved), Ausnahme
[`receipt_unbilled`](./exceptions#exception-receipt_unbilled), Ausnahme
[`units_not_comparable`](./exceptions#exception-units_not_comparable), Ausnahme
[`reservation_exceeds_stock`](./exceptions#exception-reservation_exceeds_stock), Ausnahme
[`silent_source`](./exceptions#exception-silent_source), Ausnahme
[`source_interpretation_failure`](./exceptions#exception-source_interpretation_failure), Ausnahme
[`unexplained_movement`](./exceptions#exception-unexplained_movement), Ausnahme
[`sales_invoice_unposted`](./exceptions#exception-sales_invoice_unposted), Ausnahme
[`supplier_invoice_unposted`](./exceptions#exception-supplier_invoice_unposted), Ausnahme
[`credit_note_unposted`](./exceptions#exception-credit_note_unposted), Ausnahme
[`credit_note_unsettled`](./exceptions#exception-credit_note_unsettled), Ausnahme
[`supplier_credit_unposted`](./exceptions#exception-supplier_credit_unposted), Ausnahme
[`supplier_credit_unclaimed`](./exceptions#exception-supplier_credit_unclaimed), Ausnahme
[`overdue_receivable`](./exceptions#exception-overdue_receivable), Ausnahme
[`credit_limit_exceeded`](./exceptions#exception-credit_limit_exceeded), Ausnahme
[`overdue_payable`](./exceptions#exception-overdue_payable), Ausnahme
[`purchase_discount_available`](./exceptions#exception-purchase_discount_available), Ausnahme
[`duplicate_supplier_invoice`](./exceptions#exception-duplicate_supplier_invoice), Ausnahme
[`unmatched_financial_event`](./exceptions#exception-unmatched_financial_event), Ausnahme
[`announced_return_not_arrived`](./exceptions#exception-announced_return_not_arrived), Ausnahme
[`commitment_hold_unreleased`](./exceptions#exception-commitment_hold_unreleased), Ausnahme
[`party_hold_unreleased`](./exceptions#exception-party_hold_unreleased), Ausnahme
[`stock_expired`](./exceptions#exception-stock_expired)

### `commitment_register` — Commitment register {#projection-commitment_register}

Combines obligations with allocated and physically fulfilled quantities without storing fulfillment
status on documents.

**Verbraucher:** Commitments · **Liest:** `commitment`, `reservation`, `movement`, `party`, `item`,
`location`

**Ausgaben:** `commitment`, `reserved`, `fulfilled`, `open_quantity`, `counterparty`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                     | Art                                        | Standard |
| -------------------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/commitment_register` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/commitment_register`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `order.recorded`, `commitment.fulfilled`,
`reservation.consumed`, `fact.observed`, `party.created`, `party.updated`,
`party.delivery_hold_placed`, `party.delivery_hold_released`, `item.updated`, `location.updated`,
`commitment.created`, `commitment.cancelled`, `commitment.revised`, `promises.closed`,
`commitment.held`, `commitment.hold_released`, `reservation.created`, `reservation.released`,
`movement.recorded`, `movement.corrected`

**Siehe auch:** Agenten-Tool [`commitments_list`](./commands#tool-commitments_list), Agenten-Tool
[`reservation_propose`](./commands#tool-reservation_propose), Agenten-Tool
[`order_create_propose`](./commands#tool-order_create_propose), Agenten-Tool
[`movement_create_propose`](./commands#tool-movement_create_propose)

### `document_register` — Document register {#projection-document_register}

Presents evidence and counts its shortest links into operational Reality.

**Verbraucher:** Documents · **Liest:** `document`, `document_line`, `commitment`, `source_record`

**Ausgaben:** `document`, `line_count`, `commitment_count`, `source`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                   | Art                                        | Standard |
| ------------------------------------------------------------------ | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/document_register` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/document_register`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `order.recorded`, `commitment.fulfilled`,
`source_record.interpreted`, `party.created`, `party.updated`, `payment_term.updated`,
`document.recorded`, `document.corrected`, `commitment.created`, `commitment.cancelled`

**Siehe auch:** Agenten-Tool [`order_create_propose`](./commands#tool-order_create_propose)

### `open_financial_items` — Open financial items {#projection-open_financial_items}

Invoice-side ledger amount minus explicit payment allocations; document status is not used as
payment truth.

**Verbraucher:** Open Items, Home · **Liest:** `ledger_entry`, `settlement_allocation`, `document`,
`party`

**Ausgaben:** `invoice`, `party`, `original_amount`, `allocated_amount`, `open_amount`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                                      | Art                                        | Standard |
| --------------------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/open_financial_items` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/open_financial_items`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `credit.recorded`, `invoice.recorded`, `party.updated`,
`payment_term.updated`, `document.recorded`, `document.corrected`, `payments.run`, `ledger.posted`,
`ledger.reversed`, `settlement.allocated`

**Siehe auch:** Sicht [`open_items`](./views#view-open_items)

### `payments` — Payments {#projection-payments}

Groups payment postings with their explicit invoice allocations.

**Verbraucher:** Payments · **Liest:** `ledger_entry`, `settlement_allocation`, `document`, `party`

**Ausgaben:** `payment`, `party`, `amount`, `allocations`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                          | Art                                        | Standard |
| --------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/payments` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/payments`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `party.created`, `party.updated`, `document.corrected`,
`payments.run`, `ledger.posted`, `ledger.reversed`, `settlement.allocated`

### `journal` — Journal {#projection-journal}

Orders immutable ledger postings by effective time and posting group.

**Verbraucher:** Journal · **Liest:** `ledger_entry`

**Ausgaben:** `posting_group`, `account`, `party`, `debit_credit`, `amount`, `currency`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                         | Art                                        | Standard |
| -------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/journal` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/journal`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `finance.account_changed`, `payments.run`, `ledger.posted`,
`ledger.reversed`

### `timeline` — Timeline {#projection-timeline}

Normalizes important evidence and reality timestamps into one chronological operational history.

**Verbraucher:** Timeline · **Liest:** `source_record`, `document`, `commitment`, `reservation`,
`movement`, `shipment`, `shipment_package`, `shipment_event`, `ledger_entry`, `action`

**Ausgaben:** `occurred_at`, `record_type`, `title`, `detail`, `object_link`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                                          | Art                                        | Standard |
| --------------------------------------------------------- | ------------------------------------------ | -------- |
| `GET /api/tenants/{tenant}/projection-snapshots/timeline` | Vorberechnet — im Hintergrund aktualisiert | —        |
| `GET /api/tenants/{tenant}/projections/timeline`          | Vorberechnet — im Hintergrund aktualisiert | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

**Hintergrundaktualisierung nach:** `shipment.notice_recorded`, `shipment.event_recorded`,
`shipment.event_superseded`, `finance.component_assigned`, `credit.recorded`, `invoice.recorded`,
`order.recorded`, `source_record.stored`, `commitment.fulfilled`, `reservation.consumed`,
`fact.observed`, `source_record.received`, `source_record.unmapped`, `source_record.interpreted`,
`party.created`, `party.updated`, `item.created`, `item.updated`, `location.created`,
`location.updated`, `document.recorded`, `document.corrected`, `commitment.created`,
`commitment.cancelled`, `commitment.revised`, `promises.closed`, `payments.run`, `return.announced`,
`return.announcement_withdrawn`, `commitment.held`, `commitment.hold_released`,
`reservation.created`, `reservation.released`, `handling_unit.created`, `lot.created`,
`lot.expiry_stated`, `lot.expiry_corrected`, `serial_unit.created`, `movement.recorded`,
`movement.corrected`, `ledger.posted`, `ledger.reversed`, `settlement.allocated`

**Siehe auch:** Agenten-Tool [`fact_observe_propose`](./commands#tool-fact_observe_propose),
Agenten-Tool [`movement_create_propose`](./commands#tool-movement_create_propose), Agenten-Tool
[`finance_initialize_accounts_propose`](./commands#tool-finance_initialize_accounts_propose),
Agenten-Tool [`finance_create_account_propose`](./commands#tool-finance_create_account_propose),
Agenten-Tool [`finance_update_account_propose`](./commands#tool-finance_update_account_propose),
Agenten-Tool
[`finance_set_default_account_propose`](./commands#tool-finance_set_default_account_propose)

### `price_resolution` — Price resolution {#projection-price_resolution}

Direct party lists precede group lists and the default list; the highest valid minimum-quantity tier
wins. Each parameterized question is calculated live from the current canonical pricing rules; no
stored result or unrelated projection refresh is used.

**Verbraucher:** Pricing, API, CLI · **Liest:** `price_list`, `price_list_entry`,
`party_price_list`, `party_group`, `party_group_member`, `party_group_price_list`

**Ausgaben:** `unit_price`, `currency`, `unit`, `price_list_id`, `price_list_entry_id`, `source`

**So wird diese Abfrage ausgeführt**

| Konkrete Abfrage                           | Art                                 | Standard |
| ------------------------------------------ | ----------------------------------- | -------- |
| `GET /api/tenants/{tenant}/prices/resolve` | Live — für deine Eingaben berechnet | —        |

[So wird diese Abfrage ausgeführt](./views#read-execution)

## Aktionen

| Schlüssel                                                        | Bezeichnung                           | Geschäftsaktion                                                             | Bestätigung      | Voraussetzungen                                     |
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

**Geschäftsaktion:** [`create_manual_order`](./commands#command-create_manual_order) ·
**Bestätigung:** `summary` · **Voraussetzungen:** `company_party`, `counterparty`, `location`,
`item`

**Siehe auch:** Geschäftsaktion [`create_manual_order`](./commands#command-create_manual_order),
Sicht [`documents`](./views#view-documents), Arbeitsbereich
[`operations`](./views#workspace-operations)

### `observe_fact` — Observe source-supported fact {#action-observe_fact}

**Geschäftsaktion:** [`observe_fact`](./commands#command-observe_fact) · **Bestätigung:** `summary`
· **Voraussetzungen:** `source_record`, `subject`

**Siehe auch:** Geschäftsaktion [`observe_fact`](./commands#command-observe_fact), Arbeitsbereich
[`company`](./views#workspace-company)

### `post_customer_payment` — Post customer payment {#action-post_customer_payment}

**Geschäftsaktion:** [`post_customer_payment`](./commands#command-post_customer_payment) ·
**Bestätigung:** `summary` · **Voraussetzungen:** `customer_invoice`

**Siehe auch:** Geschäftsaktion [`post_customer_payment`](./commands#command-post_customer_payment),
Sicht [`payments`](./views#view-payments), Arbeitsbereich [`finance`](./views#workspace-finance)

### `post_supplier_payment` — Post supplier payment {#action-post_supplier_payment}

**Geschäftsaktion:** [`post_supplier_payment`](./commands#command-post_supplier_payment) ·
**Bestätigung:** `summary` · **Voraussetzungen:** `supplier_invoice`

**Siehe auch:** Geschäftsaktion [`post_supplier_payment`](./commands#command-post_supplier_payment),
Sicht [`payments`](./views#view-payments), Arbeitsbereich [`finance`](./views#workspace-finance)

### `reserve_stock` — Reserve stock {#action-reserve_stock}

**Geschäftsaktion:** [`reserve`](./commands#command-reserve) · **Bestätigung:** `summary` ·
**Voraussetzungen:** `commitment`

**Siehe auch:** Geschäftsaktion [`reserve`](./commands#command-reserve), Sicht
[`reservations`](./views#view-reservations), Arbeitsbereich
[`operations`](./views#workspace-operations), Arbeitsbereich
[`warehouse`](./views#workspace-warehouse)

### `record_movement` — Record movement {#action-record_movement}

**Geschäftsaktion:** [`record_movement`](./commands#command-record_movement) · **Bestätigung:**
`summary` · **Voraussetzungen:** `item`, `location`

**Siehe auch:** Geschäftsaktion [`record_movement`](./commands#command-record_movement), Sicht
[`movements`](./views#view-movements), Arbeitsbereich [`warehouse`](./views#workspace-warehouse)

### `correct_movement` — Correct movement {#action-correct_movement}

**Geschäftsaktion:** [`correct_movement`](./commands#command-correct_movement) · **Bestätigung:**
`server_preview` · **Voraussetzungen:** `movement`

**Siehe auch:** Geschäftsaktion [`correct_movement`](./commands#command-correct_movement), Sicht
[`movements`](./views#view-movements), Arbeitsbereich [`warehouse`](./views#workspace-warehouse)

### `hold_commitment` — Hold or release commitment {#action-hold_commitment}

**Geschäftsaktion:** [`hold_commitment`](./commands#command-hold_commitment) · **Bestätigung:**
`summary` · **Voraussetzungen:** `commitment`

**Siehe auch:** Geschäftsaktion [`hold_commitment`](./commands#command-hold_commitment), Sicht
[`commitments`](./views#view-commitments), Arbeitsbereich
[`operations`](./views#workspace-operations), Arbeitsbereich
[`warehouse`](./views#workspace-warehouse)

### `hold_document_commitments` — Hold or release document commitments {#action-hold_document_commitments}

**Geschäftsaktion:** [`hold_document_commitments`](./commands#command-hold_document_commitments) ·
**Bestätigung:** `summary` · **Voraussetzungen:** `document`

**Siehe auch:** Geschäftsaktion
[`hold_document_commitments`](./commands#command-hold_document_commitments), Sicht
[`documents`](./views#view-documents), Arbeitsbereich [`operations`](./views#workspace-operations)

### `party_delivery_hold` — Set or release party delivery hold {#action-party_delivery_hold}

**Geschäftsaktion:** [`hold_party_delivery`](./commands#command-hold_party_delivery) ·
**Bestätigung:** `summary` · **Voraussetzungen:** `party`

**Siehe auch:** Geschäftsaktion [`hold_party_delivery`](./commands#command-hold_party_delivery),
Sicht [`parties`](./views#view-parties), Arbeitsbereich [`operations`](./views#workspace-operations)

### `create_handling_unit` — Create handling unit {#action-create_handling_unit}

**Geschäftsaktion:** [`create_handling_unit`](./commands#command-create_handling_unit) ·
**Bestätigung:** `summary` · **Voraussetzungen:** —

**Siehe auch:** Geschäftsaktion [`create_handling_unit`](./commands#command-create_handling_unit),
Sicht [`movements`](./views#view-movements), Arbeitsbereich
[`warehouse`](./views#workspace-warehouse)

### `create_lot` — Create lot {#action-create_lot}

**Geschäftsaktion:** [`create_lot`](./commands#command-create_lot) · **Bestätigung:** `summary` ·
**Voraussetzungen:** `item`

**Siehe auch:** Geschäftsaktion [`create_lot`](./commands#command-create_lot), Sicht
[`movements`](./views#view-movements), Arbeitsbereich [`warehouse`](./views#workspace-warehouse)

### `create_serial_unit` — Create serial unit {#action-create_serial_unit}

**Geschäftsaktion:** [`create_serial_unit`](./commands#command-create_serial_unit) ·
**Bestätigung:** `summary` · **Voraussetzungen:** `item`

**Siehe auch:** Geschäftsaktion [`create_serial_unit`](./commands#command-create_serial_unit), Sicht
[`movements`](./views#view-movements), Arbeitsbereich [`warehouse`](./views#workspace-warehouse)
