# Ressourcen

Die Fachobjekte, mit denen ein ERP-Berater arbeitet, jeweils mit den Listen, die es zeigen, den
Aktionen, die es verändern, den Klärfällen, die es auslösen kann, und der Technik darunter. Die
Namen folgen dem ERP-Sprachgebrauch; der technische Schlüssel steht daneben.

> Automatisch aus `resource_catalog.yaml` erzeugt. Diese Seite nicht von Hand bearbeiten.

| Objekt                                                         | Listen | Aktionen | Klärfälle |
| -------------------------------------------------------------- | ------ | -------- | --------- |
| [Auswertung](#resource-analytics)                              | 0      | 1        | 0         |
| [Geschäftspartner](#resource-party)                            | 1      | 6        | 2         |
| [Artikel](#resource-item)                                      | 5      | 4        | 3         |
| [Lagerort](#resource-location)                                 | 3      | 3        | 0         |
| [Preise und Zahlungsbedingungen](#resource-terms)              | 2      | 6        | 2         |
| [Auftrag](#resource-order)                                     | 8      | 10       | 9         |
| [Lieferung und Wareneingang](#resource-delivery)               | 2      | 6        | 2         |
| [Charge, Seriennummer und Palette](#resource-lot)              | 0      | 5        | 1         |
| [Rechnung und Gutschrift](#resource-invoice)                   | 3      | 10       | 14        |
| [Zahlung und Ausgleich](#resource-payment)                     | 2      | 7        | 2         |
| [Buchhaltung und Konten](#resource-accounting)                 | 2      | 13       | 3         |
| [Deckungsbeitrag](#resource-contribution)                      | 0      | 1        | 4         |
| [Retoure](#resource-return)                                    | 0      | 3        | 6         |
| [Beleg und Quellsystem](#resource-source)                      | 3      | 11       | 2         |
| [Unternehmen und Benutzer](#resource-company)                  | 1      | 4        | 0         |
| [Freigaben, Klärfälle und offene Fragen](#resource-governance) | 3      | 0        | 0         |

## Auswertung {#resource-analytics}

_Flexible Fragen und private Auswertungen_

Auswertungen über vorhandene Belege und operative Dienste mit nachvollziehbaren Datensätzen und
privaten gespeicherten Einstellungen.

**Auch genannt:** analytics, report, Auswertung, Bericht, graph, Graph

**Aktionen**

- [Private Graph-Auswertung ändern](./commands#command-change_graph_report) (`change_graph_report`)

**Darunter:** Tabellen: `analytics_report` · Agenten-Tools ohne Geschäftsaktion:
[`graph_company_generation_current`](./commands#tool-graph_company_generation_current),
[`graph_captured_reports_list`](./commands#tool-graph_captured_reports_list),
[`graph_contribution_reviews_list`](./commands#tool-graph_contribution_reviews_list),
[`graph_inventory_reviews_list`](./commands#tool-graph_inventory_reviews_list),
[`graph_catalog`](./commands#tool-graph_catalog),
[`graph_templates`](./commands#tool-graph_templates), [`graph_ask`](./commands#tool-graph_ask),
[`graph_format`](./commands#tool-graph_format),
[`graph_interpret`](./commands#tool-graph_interpret),
[`graph_reports_list`](./commands#tool-graph_reports_list),
[`graph_report_get`](./commands#tool-graph_report_get),
[`graph_requests_list`](./commands#tool-graph_requests_list),
[`graph_request_get`](./commands#tool-graph_request_get),
[`graph_request_propose`](./commands#tool-graph_request_propose)

## Geschäftspartner {#resource-party}

_Kunden, Lieferanten und das eigene Unternehmen_

Ein Datensatz je Unternehmen oder Person, mit der du Geschäfte machst. Rollen wie Kunde oder
Lieferant stehen am Geschäftspartner, es gibt keine zwei Adressbücher. Liefersperren und
Preisgruppen hängen hier.

**Auch genannt:** customer, supplier, debtor, creditor, Kunde, Lieferant, Debitor, Kreditor, Adresse

**Listen**

- [Geschäftspartner](./views#view-parties) (`parties`)

**Aktionen**

- [Geschäftspartner anlegen](./commands#command-create_party) (`create_party`)
- [Geschäftspartner ändern](./commands#command-update_party) (`update_party`)
- [Stammdatensatz aktivieren oder deaktivieren](./commands#command-set_master_data_active)
  (`set_master_data_active`)
- [Preisliste zuweisen](./commands#command-assign_party_price_list) (`assign_party_price_list`)
- [Preisgruppe anlegen und zuweisen](./commands#command-create_party_group) (`create_party_group`)
- [Liefersperre setzen oder aufheben](./commands#command-hold_party_delivery)
  (`hold_party_delivery`)

**Nachschlagen**

- [Mahnkontext anzeigen](./commands#command-dunning_context) (`dunning_context`)

**Klärfälle**

- [Kreditlimit überschritten](./exceptions#exception-credit_limit_exceeded)
  (`credit_limit_exceeded`)
- [Liefersperre nicht aufgehoben](./exceptions#exception-party_hold_unreleased)
  (`party_hold_unreleased`)

**Kommt vor in:** [Stammdaten und Quellen](./processes#process-master_data)

**Darunter:** Tabellen: `party`, `party_role`, `party_group`, `party_group_member`, `party_hold` ·
Events: [`party.created`](./events#event-party-created),
[`party.updated`](./events#event-party-updated),
[`party.delivery_hold_placed`](./events#event-party-delivery_hold_placed),
[`party.delivery_hold_released`](./events#event-party-delivery_hold_released),
[`master_data.lifecycle_changed`](./events#event-master_data-lifecycle_changed),
[`party_price_list.assigned`](./events#event-party_price_list-assigned),
[`party_group.updated`](./events#event-party_group-updated),
[`party_group.created`](./events#event-party_group-created),
[`party_group_member.added`](./events#event-party_group_member-added) · Agenten-Tools ohne
Geschäftsaktion: [`finance_party_balances`](./commands#tool-finance_party_balances)

## Artikel {#resource-item}

_Was du kaufst, lagerst und verkaufst, und wie viel davon da ist_

Die operative Identität eines Produkts mit seiner Einheit. Bestand wird nie am Artikel gespeichert,
sondern beim Lesen aus Bewegungen und Reservierungen abgeleitet. Deshalb stehen die Bestandslisten
hier.

**Auch genannt:** product, SKU, stock, inventory, Produkt, Bestand, Lagerbestand, Verfügbarkeit

**Listen**

- [Bestand](./views#view-inventory) (`inventory`)
- [Artikel](./views#view-items) (`items`)
- [Zulauf & Bedarf](./views#view-supply_demand) (`supply_demand`)
- [Zulauf und Bedarf je Artikel](./views#projection-item_supply_demand) (`item_supply_demand`)
- [Bestand](./views#projection-inventory) (`inventory`)

**Aktionen**

- [Artikel anlegen](./commands#command-create_item) (`create_item`)
- [Artikel ändern](./commands#command-update_item) (`update_item`)
- [Stammdatensatz aktivieren oder deaktivieren](./commands#command-set_master_data_active)
  (`set_master_data_active`)
- [Zulauf einem Kundenbedarf zuordnen](./commands#command-assign_supply) (`assign_supply`)

**Nachschlagen**

- [Bestand zu Anschaffungskosten anzeigen](./commands#command-inventory_cost) (`inventory_cost`)

**Klärfälle**

- [Einheiten nicht vergleichbar](./exceptions#exception-units_not_comparable)
  (`units_not_comparable`)
- [Reservierung übersteigt Bestand](./exceptions#exception-reservation_exceeds_stock)
  (`reservation_exceeds_stock`)
- [Anschaffungskosten fehlen](./exceptions#exception-missing_acquisition_cost)
  (`missing_acquisition_cost`)

**Kommt vor in:** [Purchase-to-Pay](./processes#process-procure_to_pay),
[Stammdaten und Quellen](./processes#process-master_data)

**Darunter:** Tabellen: `item`, `supply_assignment` · Events:
[`item.created`](./events#event-item-created), [`item.updated`](./events#event-item-updated),
[`master_data.lifecycle_changed`](./events#event-master_data-lifecycle_changed) · Agenten-Tools ohne
Geschäftsaktion: [`inventory_read`](./commands#tool-inventory_read),
[`item_supply_demand`](./commands#tool-item_supply_demand),
[`supply_coverage`](./commands#tool-supply_coverage),
[`graph_inventory_reviews_list`](./commands#tool-graph_inventory_reviews_list)

## Lagerort {#resource-location}

_Lager, Zonen und logische Orte, an denen Bestand liegen kann_

Ein physischer oder logischer Ort. Nur lagerfähige Orte können Ware halten; eine Hierarchie entsteht
über den übergeordneten Lagerort.

**Auch genannt:** warehouse, bin, zone, Lager, Lagerplatz

**Listen**

- [Bestand](./views#view-inventory) (`inventory`)
- [Lagerorte](./views#view-locations) (`locations`)
- [Bestand](./views#projection-inventory) (`inventory`)

**Aktionen**

- [Lagerort anlegen](./commands#command-create_location) (`create_location`)
- [Lagerort ändern](./commands#command-update_location) (`update_location`)
- [Stammdatensatz aktivieren oder deaktivieren](./commands#command-set_master_data_active)
  (`set_master_data_active`)

**Darunter:** Tabellen: `location` · Events: [`location.created`](./events#event-location-created),
[`location.updated`](./events#event-location-updated),
[`master_data.lifecycle_changed`](./events#event-master_data-lifecycle_changed)

## Preise und Zahlungsbedingungen {#resource-terms}

_Preislisten, Staffeln, Preisgruppen und Zahlungsbedingungen_

Die kaufmännischen Konditionen, an denen Auftrag und Rechnung gemessen werden. Die Preisfindung
zeigt, welche Liste für welchen Geschäftspartner gilt; Zahlungsbedingungen bestimmen Fälligkeit und
Skonto.

**Auch genannt:** price list, discount, tier, condition, Preisliste, Staffelpreis, Kondition,
Skonto, Zahlungsziel

**Listen**

- [Konditionen](./views#view-commercial_terms) (`commercial_terms`)
- [Preisfindung](./views#projection-price_resolution) (`price_resolution`)

**Aktionen**

- [Stammdatensatz aktivieren oder deaktivieren](./commands#command-set_master_data_active)
  (`set_master_data_active`)
- [Zahlungsbedingung anlegen](./commands#command-create_payment_term) (`create_payment_term`)
- [Preisliste anlegen](./commands#command-create_price_list) (`create_price_list`)
- [Staffelpreis anlegen](./commands#command-create_price_list_entry) (`create_price_list_entry`)
- [Preisliste zuweisen](./commands#command-assign_party_price_list) (`assign_party_price_list`)
- [Preisgruppe anlegen und zuweisen](./commands#command-create_party_group) (`create_party_group`)

**Nachschlagen**

- [Gültigen Preis ermitteln](./commands#command-resolve_price) (`resolve_price`)

**Klärfälle**

- [Rechnungspreis weicht von der Vereinbarung ab](./exceptions#exception-invoice_price_differs)
  (`invoice_price_differs`)
- [Unter Einkaufspreis verkauft](./exceptions#exception-sold_below_purchase_price)
  (`sold_below_purchase_price`)

**Kommt vor in:** [Stammdaten und Quellen](./processes#process-master_data)

**Darunter:** Tabellen: `payment_term`, `price_list`, `price_list_entry`, `party_price_list`,
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

## Auftrag {#resource-order}

_Kundenaufträge, Bestellungen, Reservierungen und Sperren_

Ein Versprechen zu liefern oder zu erhalten: Reality nennt es Verpflichtung. Der Auftragsbeleg ist
der Nachweis; offene Menge, Versandfähigkeit und Verzug werden aus der Verpflichtung, ihren
Reservierungen und den erfüllenden Bewegungen abgeleitet.

**Auch genannt:** sales order, purchase order, commitment, reservation, backlog, Kundenauftrag,
Bestellung, Verpflichtung, Lieferverpflichtung, Reservierung, Rückstand, Liefersperre

**Listen**

- [Verpflichtungen](./views#view-commitments) (`commitments`)
- [Reservierungen](./views#view-reservations) (`reservations`)
- [Aufträge](./views#view-orders) (`orders`)
- [Lagerarbeitsvorrat](./views#view-warehouse_queue) (`warehouse_queue`)
- [Lieferhindernisse](./views#view-fulfillment_blockers) (`fulfillment_blockers`)
- [Versandvorrat](./views#projection-fulfillment_queue) (`fulfillment_queue`)
- [Lieferhindernisse](./views#projection-fulfillment_blockers) (`fulfillment_blockers`)
- [Verpflichtungsregister](./views#projection-commitment_register) (`commitment_register`)

**Aktionen**

- [Kundenauftrag oder Bestellung anlegen](./commands#command-create_manual_order)
  (`create_manual_order`)
- [Bestand reservieren](./commands#command-reserve) (`reserve`)
- [Reservierung aufheben](./commands#command-release_reservation) (`release_reservation`)
- [Verpflichtung ändern](./commands#command-revise_commitment) (`revise_commitment`)
- [Verpflichtung stornieren](./commands#command-cancel_commitment) (`cancel_commitment`)
- [Verpflichtung sperren oder freigeben](./commands#command-hold_commitment) (`hold_commitment`)
- [Beleg sperren oder freigeben](./commands#command-hold_document_commitments)
  (`hold_document_commitments`)
- [Liefersperre setzen oder aufheben](./commands#command-hold_party_delivery)
  (`hold_party_delivery`)
- [Alte Verpflichtungen schließen](./commands#command-close_stale_promises) (`close_stale_promises`)
- [Packstück versenden oder Wareneingang buchen](./commands#command-record_packaged_execution)
  (`record_packaged_execution`)

**Nachschlagen**

- [Schließen alter Verpflichtungen vorschauen](./commands#command-preview_stale_promise_closure)
  (`preview_stale_promise_closure`)

**Klärfälle**

- [Lieferverzug an Kunden](./exceptions#exception-overdue_outgoing_customer_commitment)
  (`overdue_outgoing_customer_commitment`)
- [Lieferverpflichtung gefährdet](./exceptions#exception-outgoing_commitment_at_risk)
  (`outgoing_commitment_at_risk`)
- [Auftrag hängt](./exceptions#exception-order_stalled) (`order_stalled`)
- [Lieferverzug des Lieferanten](./exceptions#exception-overdue_incoming_supplier_commitment)
  (`overdue_incoming_supplier_commitment`)
- [Reservierung übersteigt Bestand](./exceptions#exception-reservation_exceeds_stock)
  (`reservation_exceeds_stock`)
- [Sperre der Verpflichtung nicht aufgehoben](./exceptions#exception-commitment_hold_unreleased)
  (`commitment_hold_unreleased`)
- [Liefersperre nicht aufgehoben](./exceptions#exception-party_hold_unreleased)
  (`party_hold_unreleased`)
- [Kostenprüfung veraltet](./exceptions#exception-stale_cost_review) (`stale_cost_review`)
- [Tatsächlicher DB1 negativ](./exceptions#exception-negative_actual_db1) (`negative_actual_db1`)

**Kommt vor in:** [Order-to-Cash](./processes#process-order_to_cash),
[Purchase-to-Pay](./processes#process-procure_to_pay)

**Darunter:** Tabellen: `commitment`, `commitment_hold`, `commitment_revision`, `reservation` ·
Events: [`order.recorded`](./events#event-order-recorded),
[`party.delivery_hold_placed`](./events#event-party-delivery_hold_placed),
[`commitment.created`](./events#event-commitment-created),
[`commitment.cancelled`](./events#event-commitment-cancelled),
[`commitment.revised`](./events#event-commitment-revised),
[`promises.closed`](./events#event-promises-closed),
[`commitment.held`](./events#event-commitment-held),
[`commitment.hold_released`](./events#event-commitment-hold_released),
[`reservation.created`](./events#event-reservation-created),
[`reservation.released`](./events#event-reservation-released) · Agenten-Tools ohne Geschäftsaktion:
[`commitments_list`](./commands#tool-commitments_list),
[`fulfillment_queue`](./commands#tool-fulfillment_queue),
[`fulfillment_readiness`](./commands#tool-fulfillment_readiness),
[`fulfillment_blockers`](./commands#tool-fulfillment_blockers),
[`order_explain`](./commands#tool-order_explain)

## Lieferung und Wareneingang {#resource-delivery}

_Lagerbewegungen, Sendungen, Packstücke und Tracking_

Jede physische Bestandsänderung ist eine unveränderliche Lagerbewegung; Korrekturen ergänzen eine
Gegenbuchung statt zu editieren. Eine Sendung ist die Lieferung, die Bewegungen zu einem
Geschäftspartner oder von ihm trägt, mit Beobachtungen des Spediteurs.

**Auch genannt:** goods receipt, goods issue, shipment, movement, transfer, adjustment,
Warenausgang, Lagerbewegung, Umlagerung, Bestandsanpassung, Sendung, Packstück, Tracking

**Listen**

- [Lagerbewegungen](./views#view-movements) (`movements`)
- [Lagerarbeitsvorrat](./views#view-warehouse_queue) (`warehouse_queue`)

**Aktionen**

- [Lagerbewegung buchen](./commands#command-record_movement) (`record_movement`)
- [Lagerbewegung korrigieren](./commands#command-correct_movement) (`correct_movement`)
- [Sendungsavis erfassen](./commands#command-record_shipment_notice) (`record_shipment_notice`)
- [Packstück versenden oder Wareneingang buchen](./commands#command-record_packaged_execution)
  (`record_packaged_execution`)
- [Sendungsereignis erfassen](./commands#command-record_shipment_event) (`record_shipment_event`)
- [Sendungsereignis korrigieren](./commands#command-supersede_shipment_event)
  (`supersede_shipment_event`)

**Klärfälle**

- [Retoure nicht bearbeitet](./exceptions#exception-return_unresolved) (`return_unresolved`)
- [Unerklärte Lagerbewegung](./exceptions#exception-unexplained_movement) (`unexplained_movement`)

**Kommt vor in:** [Order-to-Cash](./processes#process-order_to_cash),
[Purchase-to-Pay](./processes#process-procure_to_pay), [Kundenretouren](./processes#process-returns)

**Darunter:** Tabellen: `movement`, `movement_correction`, `shipment`, `shipment_package`,
`shipment_event`, `shipment_event_supersession` · Events:
[`shipment.notice_recorded`](./events#event-shipment-notice_recorded),
[`shipment.event_recorded`](./events#event-shipment-event_recorded),
[`shipment.event_superseded`](./events#event-shipment-event_superseded),
[`commitment.fulfilled`](./events#event-commitment-fulfilled),
[`reservation.consumed`](./events#event-reservation-consumed),
[`movement.recorded`](./events#event-movement-recorded),
[`movement.corrected`](./events#event-movement-corrected) · Agenten-Tools ohne Geschäftsaktion:
[`shipments_list`](./commands#tool-shipments_list),
[`shipment_explain`](./commands#tool-shipment_explain),
[`movement_explanation`](./commands#tool-movement_explanation)

## Charge, Seriennummer und Palette {#resource-lot}

_Identitäten unterhalb des Artikels und ihre Mindesthaltbarkeit_

Charge und Seriennummer identifizieren eine Teilmenge eines Artikels; eine Ladeeinheit identifiziert
eine Palette über ihre NVE/SSCC. Mindesthaltbarkeit wird von jemandem angegeben, der sie gelesen
hat, nie berechnet.

**Auch genannt:** batch, serial, handling unit, NVE, SSCC, best before, MHD, Charge, Ladeeinheit

**Aktionen**

- [Palette anlegen](./commands#command-create_handling_unit) (`create_handling_unit`)
- [Charge anlegen](./commands#command-create_lot) (`create_lot`)
- [Mindesthaltbarkeit angeben](./commands#command-state_lot_expiry) (`state_lot_expiry`)
- [Mindesthaltbarkeit korrigieren](./commands#command-correct_lot_expiry) (`correct_lot_expiry`)
- [Seriennummer anlegen](./commands#command-create_serial_unit) (`create_serial_unit`)

**Nachschlagen**

- [Abgelaufene Chargen anzeigen](./commands#command-expired_lots) (`expired_lots`)

**Klärfälle**

- [Abgelaufener Bestand](./exceptions#exception-stock_expired) (`stock_expired`)

**Darunter:** Tabellen: `lot`, `serial_unit`, `handling_unit` · Events:
[`handling_unit.created`](./events#event-handling_unit-created),
[`lot.created`](./events#event-lot-created),
[`lot.expiry_stated`](./events#event-lot-expiry_stated),
[`lot.expiry_corrected`](./events#event-lot-expiry_corrected),
[`serial_unit.created`](./events#event-serial_unit-created)

## Rechnung und Gutschrift {#resource-invoice}

_Ausgangs- und Eingangsrechnungen, Gutschriften und offene Posten_

Erfassen einer Rechnung speichert den Beleg; Buchen erzeugt die Journalbuchungen. Offene Posten
vergleichen Fakturiertes mit Bezahltem oder Gutgeschriebenem, je Geschäftspartner und Währung.

**Auch genannt:** receivable, payable, open item, credit note, billing, Ausgangsrechnung,
Eingangsrechnung, Forderung, Verbindlichkeit, Offene Posten, Rechnungsprüfung, Gutschrift

**Listen**

- [Offene Posten](./views#view-open_items) (`open_items`)
- [Belege](./views#view-documents) (`documents`)
- [Offene Posten](./views#projection-open_financial_items) (`open_financial_items`)

**Aktionen**

- [Ausgangsrechnung buchen](./commands#command-post_sales_invoice) (`post_sales_invoice`)
- [Eingangsrechnung buchen](./commands#command-post_supplier_invoice) (`post_supplier_invoice`)
- [Retourengutschrift erfassen](./commands#command-record_sales_credit) (`record_sales_credit`)
- [Eingangsrechnung erfassen](./commands#command-record_supplier_invoice)
  (`record_supplier_invoice`)
- [Freie Eingangsrechnung erfassen](./commands#command-record_free_supplier_invoice)
  (`record_free_supplier_invoice`)
- [Ausgangsrechnung erfassen](./commands#command-record_sales_invoice) (`record_sales_invoice`)
- [Gutschrift buchen](./commands#command-post_sales_credit_note) (`post_sales_credit_note`)
- [Gutschrift mit Rechnung verrechnen](./commands#command-allocate_credit_note)
  (`allocate_credit_note`)
- [Lieferantengutschrift buchen](./commands#command-post_supplier_credit_note)
  (`post_supplier_credit_note`)
- [Lieferantengutschrift mit Rechnung verrechnen](./commands#command-allocate_supplier_credit_note)
  (`allocate_supplier_credit_note`)

**Nachschlagen**

- [Gutschriftfähige Rechnungspositionen anzeigen](./commands#command-invoice_credit_context)
  (`invoice_credit_context`)

**Klärfälle**

- [Geliefert, nicht fakturiert](./exceptions#exception-shipped_not_billed) (`shipped_not_billed`)
- [Fakturiert, nicht geliefert](./exceptions#exception-billed_not_received) (`billed_not_received`)
- [Rechnungspreis weicht von der Vereinbarung ab](./exceptions#exception-invoice_price_differs)
  (`invoice_price_differs`)
- [Wareneingang ohne Rechnung](./exceptions#exception-receipt_unbilled) (`receipt_unbilled`)
- [Ausgangsrechnung nicht gebucht](./exceptions#exception-sales_invoice_unposted)
  (`sales_invoice_unposted`)
- [Eingangsrechnung nicht gebucht](./exceptions#exception-supplier_invoice_unposted)
  (`supplier_invoice_unposted`)
- [Gutschrift nicht gebucht](./exceptions#exception-credit_note_unposted) (`credit_note_unposted`)
- [Gutschrift nicht ausgeglichen](./exceptions#exception-credit_note_unsettled)
  (`credit_note_unsettled`)
- [Lieferantengutschrift nicht gebucht](./exceptions#exception-supplier_credit_unposted)
  (`supplier_credit_unposted`)
- [Lieferantengutschrift nicht eingefordert](./exceptions#exception-supplier_credit_unclaimed)
  (`supplier_credit_unclaimed`)
- [Überfällige Forderung](./exceptions#exception-overdue_receivable) (`overdue_receivable`)
- [Überfällige Verbindlichkeit](./exceptions#exception-overdue_payable) (`overdue_payable`)
- [Skonto noch möglich](./exceptions#exception-purchase_discount_available)
  (`purchase_discount_available`)
- [Doppelte Eingangsrechnung](./exceptions#exception-duplicate_supplier_invoice)
  (`duplicate_supplier_invoice`)

**Kommt vor in:** [Order-to-Cash](./processes#process-order_to_cash),
[Purchase-to-Pay](./processes#process-procure_to_pay), [Kundenretouren](./processes#process-returns)

**Darunter:** Events: [`credit.recorded`](./events#event-credit-recorded),
[`invoice.recorded`](./events#event-invoice-recorded) · Agenten-Tools ohne Geschäftsaktion:
[`finance_credits`](./commands#tool-finance_credits),
[`finance_party_balances`](./commands#tool-finance_party_balances)

## Zahlung und Ausgleich {#resource-payment}

_Zahlungseingänge und -ausgänge, Zuordnung, Minderzahlungen und Erstattungen_

Eine Zahlung ist ein Beleg mit einer ausgeglichenen Buchung dahinter. Die Zuordnung zu Rechnungen
oder Gutschriften ist der Ausgleich; eine Minderzahlung wird als vereinbarter Abzug akzeptiert oder
bleibt offen. Zahlläufe bezahlen Lieferanten gesammelt. Öffentliche Zahlungsabfragen filtern die
Richtung nur als eingehend oder ausgehend; Kunde oder Lieferant ist eine Saldo-Seite und keine
Zahlungsrichtung.

**Auch genannt:** payment receipt, allocation, matching, short payment, refund, payment run,
Zahlungseingang, zuordnen, Minderzahlung, Abzug, Skontoabzug, Erstattung, Zahllauf, Saldo

**Listen**

- [Zahlungen](./views#view-payments) (`payments`)
- [Zahlungen](./views#projection-payments) (`payments`)

**Aktionen**

- [Zahlungseingang buchen](./commands#command-post_customer_payment) (`post_customer_payment`)
- [Zahllauf ausführen](./commands#command-execute_payment_run) (`execute_payment_run`)
- [Kundenerstattung buchen](./commands#command-post_customer_refund) (`post_customer_refund`)
- [Lieferantenerstattung buchen](./commands#command-post_supplier_refund) (`post_supplier_refund`)
- [Zahlungsausgang buchen](./commands#command-post_supplier_payment) (`post_supplier_payment`)
- [Abzug akzeptieren](./commands#command-accept_adjustment) (`accept_adjustment`)
- [Zahlung zuordnen oder Guthaben verwenden](./commands#command-apply_settlement)
  (`apply_settlement`)

**Nachschlagen**

- [Zahllauf vorschauen](./commands#command-preview_payment_run) (`preview_payment_run`)
- [Mahnkontext anzeigen](./commands#command-dunning_context) (`dunning_context`)
- [Kontext für Abzug anzeigen](./commands#command-adjustment_context) (`adjustment_context`)
- [Kontext für Zahlung und Gutschrift anzeigen](./commands#command-settlement_context)
  (`settlement_context`)

**Klärfälle**

- [Gutschrift nicht ausgeglichen](./exceptions#exception-credit_note_unsettled)
  (`credit_note_unsettled`)
- [Nicht zugeordneter Finanzvorgang](./exceptions#exception-unmatched_financial_event)
  (`unmatched_financial_event`)

**Kommt vor in:** [Order-to-Cash](./processes#process-order_to_cash),
[Purchase-to-Pay](./processes#process-procure_to_pay), [Kundenretouren](./processes#process-returns)

**Darunter:** Tabellen: `settlement_allocation` · Events:
[`payments.run`](./events#event-payments-run),
[`settlement.allocated`](./events#event-settlement-allocated) · Agenten-Tools ohne Geschäftsaktion:
[`finance_balances`](./commands#tool-finance_balances),
[`finance_party_balances`](./commands#tool-finance_party_balances),
[`finance_payments`](./commands#tool-finance_payments)

## Buchhaltung und Konten {#resource-accounting}

_Journal, operative Konten, Eröffnungsbuchungen und die Export-Konfiguration_

Das ausgeglichene Journal, in dem jede Buchung landet, die operativen Konten, die es nutzt, und die
Konfiguration, die Buchungen einem externen Buchhaltungssystem zuordnet. Stornos ergänzen eine
Gegenbuchung; nichts wird gelöscht.

**Auch genannt:** journal, GL, chart of accounts, reversal, opening balance, export, DATEV, Journal,
Kontenrahmen, Storno, Eröffnungsbilanz, Sachkonto

**Listen**

- [Journal](./views#view-journal) (`journal`)
- [Journal](./views#projection-journal) (`journal`)

**Aktionen**

- [Kostenentscheidung bestätigen](./commands#command-execute_cost_change) (`execute_cost_change`)
- [Buchhaltungsziel pflegen](./commands#command-maintain_target_configuration)
  (`maintain_target_configuration`)
- [Quellcode zuordnen](./commands#command-set_source_mapping) (`set_source_mapping`)
- [Finanzkomponente zuordnen](./commands#command-assign_component) (`assign_component`)
- [Finanzreferenz pflegen](./commands#command-maintain_reference) (`maintain_reference`)
- [Operative Konten anlegen](./commands#command-initialize_accounts) (`initialize_accounts`)
- [Operatives Konto anlegen](./commands#command-create_account) (`create_account`)
- [Operatives Konto ändern](./commands#command-update_account) (`update_account`)
- [Standardkonto festlegen](./commands#command-set_default_account) (`set_default_account`)
- [Buchung stornieren](./commands#command-reverse_ledger_posting_group)
  (`reverse_ledger_posting_group`)
- [Mahnung erfassen](./commands#command-record_notice) (`record_notice`)
- [Mahnung stornieren](./commands#command-reverse_notice) (`reverse_notice`)
- [Eröffnungsposten importieren](./commands#command-import_opening) (`import_opening`)

**Nachschlagen**

- [Geprüfte Teilzuordnung anzeigen](./commands#command-commercial_match) (`commercial_match`)
- [Kosten mit Bewertungsbasis abfragen](./commands#command-cost_query) (`cost_query`)
- [Kostennachweis prüfen](./commands#command-cost_record) (`cost_record`)
- [Geprüfte Deckungsbeiträge anzeigen](./commands#command-reviewed_contribution)
  (`reviewed_contribution`)
- [Deckungsbeitragsvorschau prüfen](./commands#command-contribution_preview)
  (`contribution_preview`)
- [Bestand zu Anschaffungskosten anzeigen](./commands#command-inventory_cost) (`inventory_cost`)
- [Empfangene Anschaffungskosten anzeigen](./commands#command-cost_evidence) (`cost_evidence`)
- [Anschaffungskosten des Wareneingangs anzeigen](./commands#command-receipt_cost) (`receipt_cost`)
- [Buchhaltungsziele anzeigen](./commands#command-list_targets) (`list_targets`)
- [Zielreferenzen anzeigen](./commands#command-list_target_references) (`list_target_references`)
- [Kontenzuordnungen anzeigen](./commands#command-list_mappings) (`list_mappings`)
- [Verlauf der Kontenzuordnung](./commands#command-mapping_history) (`mapping_history`)
- [Quellcode-Zuordnungen anzeigen](./commands#command-list_source_mappings) (`list_source_mappings`)
- [Verlauf der Quellcode-Zuordnung](./commands#command-source_mapping_history)
  (`source_mapping_history`)
- [Empfangene Finanzdetails anzeigen](./commands#command-component_context) (`component_context`)
- [Verlauf der Komponentenzuordnung](./commands#command-component_history) (`component_history`)
- [Finanzreferenzen anzeigen](./commands#command-list_references) (`list_references`)
- [Verlauf der Finanzreferenz](./commands#command-reference_history) (`reference_history`)
- [Buchungsmatrix anzeigen](./commands#command-transaction_matrix) (`transaction_matrix`)
- [Operative Konten anzeigen](./commands#command-list_accounts) (`list_accounts`)
- [Mahnkontext anzeigen](./commands#command-dunning_context) (`dunning_context`)
- [Mahnungen anzeigen](./commands#command-notices) (`notices`)
- [Mahnung anzeigen](./commands#command-notice_detail) (`notice_detail`)
- [Kontext der Eröffnungsposten anzeigen](./commands#command-opening_context) (`opening_context`)

**Klärfälle**

- [Nicht zugeordneter Finanzvorgang](./exceptions#exception-unmatched_financial_event)
  (`unmatched_financial_event`)
- [Kostenkomponente nicht zugeordnet](./exceptions#exception-unassigned_cost_component)
  (`unassigned_cost_component`)
- [Kostenprüfung veraltet](./exceptions#exception-stale_cost_review) (`stale_cost_review`)

**Kommt vor in:** [Finanzeinrichtung und Periodenarbeit](./processes#process-finance_setup)

**Darunter:** Tabellen: `cost_company_manifest`, `cost_company_inventory_input`,
`cost_company_contribution_input`, `cost_company_generation`, `cost_company_inventory_result`,
`cost_company_contribution_result`, `cost_company_publication`, `cost_generation`,
`cost_inventory_row`, `cost_contribution_row`, `cost_publication`, `cost_captured_basis`,
`cost_captured_inventory_basis`, `cost_captured_contribution_basis`, `cost_company_census`,
`cost_company_census_movement`, `cost_company_census_document`, `cost_company_census_line`,
`cost_company_census_source`, `cost_contribution_generation`, `cost_contribution_snapshot`,
`cost_inventory_generation`, `cost_inventory_snapshot`, `cost_inventory_publication`,
`cost_commercial_match_revision`, `cost_commercial_inventory_part`, `cost_commercial_direct_part`,
`cost_selling_attribution_part`, `cost_selling_review_category`, `cost_selling_review_member`,
`cost_revenue_match_basis`, `cost_contribution_review`, `cost_policy_revision`,
`cost_movement_basis`, `cost_ownership_revision`, `cost_inventory_review`, `cost_inventory_member`,
`cost_valuation_assessment_revision`, `cost_valuation_assessment_part`,
`cost_conversion_basis_revision`, `cost_attribution_part`, `cost_attribution_revision`,
`cost_component_basis`, `cost_component_replacement`, `cost_correction_basis`,
`cost_input_manifest`, `cost_manifest_attribution`, `cost_manifest_component`,
`cost_manifest_correction`, `cost_manifest_receipt`, `cost_manifest_replacement`,
`cost_receipt_basis`, `cost_scope_review`, `cost_scope_review_category`, `ledger_entry`,
`ledger_reversal`, `subledger_account`, `finance_role_destination`, `accounting_target`,
`accounting_target_reference`, `finance_target_mapping_revision`,
`source_classification_mapping_revision`, `financial_component`, `component_assignment_revision`,
`component_assignment_part`, `finance_reference`, `opening_scope`, `opening_item_detail` · Events:
[`cost.attributed`](./events#event-cost-attributed),
[`cost.reviewed`](./events#event-cost-reviewed),
[`finance.target_configuration_changed`](./events#event-finance-target_configuration_changed),
[`finance.source_mapping_changed`](./events#event-finance-source_mapping_changed),
[`finance.component_assigned`](./events#event-finance-component_assigned),
[`finance.reference_changed`](./events#event-finance-reference_changed),
[`finance.account_changed`](./events#event-finance-account_changed),
[`dunning.notice_recorded`](./events#event-dunning-notice_recorded),
[`dunning.notice_reversed`](./events#event-dunning-notice_reversed),
[`ledger.posted`](./events#event-ledger-posted), [`ledger.reversed`](./events#event-ledger-reversed)

## Deckungsbeitrag {#resource-contribution}

_Geprüfter DB1 und DB2 für konkrete Ausgangsrechnungspositionen_

Die nachvollziehbare Brücke vom empfangenen Nettoerlös über geprüfte verbrauchte Anschaffungskosten
zu DB1 und über direkte und umgelegte Vertriebskosten zu DB2. Fehlende Evidenz bleibt unbekannt;
jedes bestätigte Ergebnis behält seine Prüfung und Wissensgrenze.

**Auch genannt:** contribution margin, gross margin, DB1, DB2, Deckungsbeitrag, Rohertrag, Marge

**Aktionen**

- [Kostenentscheidung bestätigen](./commands#command-execute_cost_change) (`execute_cost_change`)

**Nachschlagen**

- [Geprüfte Teilzuordnung anzeigen](./commands#command-commercial_match) (`commercial_match`)
- [Kosten mit Bewertungsbasis abfragen](./commands#command-cost_query) (`cost_query`)
- [Kostennachweis prüfen](./commands#command-cost_record) (`cost_record`)
- [Geprüfte Deckungsbeiträge anzeigen](./commands#command-reviewed_contribution)
  (`reviewed_contribution`)
- [Deckungsbeitragsvorschau prüfen](./commands#command-contribution_preview)
  (`contribution_preview`)
- [Bestand zu Anschaffungskosten anzeigen](./commands#command-inventory_cost) (`inventory_cost`)
- [Empfangene Anschaffungskosten anzeigen](./commands#command-cost_evidence) (`cost_evidence`)
- [Anschaffungskosten des Wareneingangs anzeigen](./commands#command-receipt_cost) (`receipt_cost`)

**Klärfälle**

- [Anschaffungskosten fehlen](./exceptions#exception-missing_acquisition_cost)
  (`missing_acquisition_cost`)
- [Kostenkomponente nicht zugeordnet](./exceptions#exception-unassigned_cost_component)
  (`unassigned_cost_component`)
- [Kostenprüfung veraltet](./exceptions#exception-stale_cost_review) (`stale_cost_review`)
- [Tatsächlicher DB1 negativ](./exceptions#exception-negative_actual_db1) (`negative_actual_db1`)

**Darunter:** Tabellen: `cost_commercial_match_revision`, `cost_commercial_inventory_part`,
`cost_commercial_direct_part`, `cost_revenue_match_basis`, `cost_contribution_review`,
`cost_selling_attribution_part`, `cost_selling_review_category`, `cost_selling_review_member` ·
Events: [`cost.attributed`](./events#event-cost-attributed),
[`cost.reviewed`](./events#event-cost-reviewed) · Agenten-Tools ohne Geschäftsaktion:
[`graph_contribution_reviews_list`](./commands#tool-graph_contribution_reviews_list)

## Retoure {#resource-return}

_Kundenretouren, Lieferantenretouren und die Gutschriften daraus_

Eine Retoure wird angekündigt, kommt als Retourenwareneingang an, wird entschieden und endet in
Gutschrift oder Erstattung. Jeder Schritt ist ein eigener Datensatz, deshalb ist eine Retoure
sichtbar, die zwischen zwei Schritten hängt.

**Auch genannt:** RMA, return announcement, restocking fee, Retourenankündigung,
Retourenwareneingang, Lieferantenretoure, Wiedereinlagerungsgebühr

**Aktionen**

- [Retoure ankündigen](./commands#command-announce_customer_return) (`announce_customer_return`)
- [Retourenankündigung zurückziehen](./commands#command-withdraw_return_announcement)
  (`withdraw_return_announcement`)
- [Retourenware entscheiden](./commands#command-record_return_disposition)
  (`record_return_disposition`)

**Nachschlagen**

- [Angekündigte Retouren anzeigen](./commands#command-return_announcements) (`return_announcements`)

**Klärfälle**

- [Retourniert, nicht gutgeschrieben](./exceptions#exception-returned_not_credited)
  (`returned_not_credited`)
- [Gutgeschrieben, nicht retourniert](./exceptions#exception-credited_not_returned)
  (`credited_not_returned`)
- [Lieferantenretoure nicht gutgeschrieben](./exceptions#exception-supplier_return_not_credited)
  (`supplier_return_not_credited`)
- [Lieferant hat mehr gutgeschrieben als zurückging](./exceptions#exception-supplier_credit_not_returned)
  (`supplier_credit_not_returned`)
- [Retoure nicht bearbeitet](./exceptions#exception-return_unresolved) (`return_unresolved`)
- [Angekündigte Retoure nicht eingetroffen](./exceptions#exception-announced_return_not_arrived)
  (`announced_return_not_arrived`)

**Kommt vor in:** [Purchase-to-Pay](./processes#process-procure_to_pay),
[Kundenretouren](./processes#process-returns)

**Darunter:** Tabellen: `return_announcement` · Events:
[`return.announced`](./events#event-return-announced),
[`return.announcement_withdrawn`](./events#event-return-announcement_withdrawn) · Agenten-Tools ohne
Geschäftsaktion: [`return_disposition_summary`](./commands#tool-return_disposition_summary)

## Beleg und Quellsystem {#resource-source}

_Angebundene Systeme, Importe, manuelle Belege und Facts_

Alles, was Reality weiß, kommt als unveränderlicher Quelldatensatz aus einem System, einer Datei
oder von einer Person. Belege sind der normalisierte Nachweis; ein Fact ist eine einzelne Aussage
über einen bestehenden Datensatz. Fehlgeschlagene Interpretationen und verstummte Quellen erscheinen
als Klärfälle.

**Auch genannt:** ERP, shop, import, connector, interface, evidence, Schnittstelle, Import, Beleg,
Nachweis, Quelle

**Listen**

- [Belege](./views#view-documents) (`documents`)
- [Quellen & Importe](./views#view-sources_imports) (`sources_imports`)
- [Belegregister](./views#projection-document_register) (`document_register`)

**Aktionen**

- [Quellcode zuordnen](./commands#command-set_source_mapping) (`set_source_mapping`)
- [Fact erfassen](./commands#command-observe_fact) (`observe_fact`)
- [Connector einrichten](./commands#command-install_connector_shell) (`install_connector_shell`)
- [Quellsystem anlegen](./commands#command-create_source_system) (`create_source_system`)
- [Quellfähigkeit festlegen](./commands#command-create_source_capability)
  (`create_source_capability`)
- [Quelldaten importieren](./commands#command-enqueue_source) (`enqueue_source`)
- [Manuellen Beleg korrigieren](./commands#command-correct_manual_document)
  (`correct_manual_document`)
- [Korrigierten Quellbeleg erfassen](./commands#command-record_corrected_document_source)
  (`record_corrected_document_source`)
- [Beleg sperren oder freigeben](./commands#command-hold_document_commitments)
  (`hold_document_commitments`)
- [Manuellen Beleg erfassen](./commands#command-create_manual_document_with_lines)
  (`create_manual_document_with_lines`)
- [Mahnung erfassen](./commands#command-record_notice) (`record_notice`)

**Nachschlagen**

- [Geprüfte Teilzuordnung anzeigen](./commands#command-commercial_match) (`commercial_match`)
- [Belegzuordnung vorschauen](./commands#command-preview_document) (`preview_document`)
- [Quellcode-Zuordnungen anzeigen](./commands#command-list_source_mappings) (`list_source_mappings`)
- [Verlauf der Quellcode-Zuordnung](./commands#command-source_mapping_history)
  (`source_mapping_history`)
- [Mahnkontext anzeigen](./commands#command-dunning_context) (`dunning_context`)
- [Mahnungen anzeigen](./commands#command-notices) (`notices`)
- [Mahnung anzeigen](./commands#command-notice_detail) (`notice_detail`)

**Klärfälle**

- [Quelle verstummt](./exceptions#exception-silent_source) (`silent_source`)
- [Quelle nicht interpretierbar](./exceptions#exception-source_interpretation_failure)
  (`source_interpretation_failure`)

**Kommt vor in:** [Stammdaten und Quellen](./processes#process-master_data)

**Darunter:** Tabellen: `source_system`, `source_capability`, `document`, `document_line`, `fact` ·
Events: [`finance.source_mapping_changed`](./events#event-finance-source_mapping_changed),
[`dunning.notice_recorded`](./events#event-dunning-notice_recorded),
[`source_record.stored`](./events#event-source_record-stored),
[`fact.observed`](./events#event-fact-observed),
[`source_record.received`](./events#event-source_record-received),
[`source_record.unmapped`](./events#event-source_record-unmapped),
[`source_record.interpreted`](./events#event-source_record-interpreted),
[`document.recorded`](./events#event-document-recorded),
[`document.corrected`](./events#event-document-corrected) · Agenten-Tools ohne Geschäftsaktion:
[`interpretation_coverage`](./commands#tool-interpretation_coverage)

## Unternehmen und Benutzer {#resource-company}

_Mitglieder, Einladungen und was ein Unternehmen bereits nutzt_

Wer in einem Unternehmen arbeiten darf und wie weit dessen Daten eingerichtet sind. Jeder
Geschäftsdatensatz gehört zu genau einem Unternehmen; fremde Datensätze verhalten sich wie nicht
vorhanden.

**Auch genannt:** tenant, member, invitation, access, Mandant, Mitglied, Einladung, Zugang

**Listen**

- [Nutzung des Unternehmens](./views#projection-tenant_usage) (`tenant_usage`)

**Aktionen**

- [Mitglied einladen](./commands#command-create_invitation) (`create_invitation`)
- [Einladung erneut senden](./commands#command-resend_invitation) (`resend_invitation`)
- [Einladung zurückziehen](./commands#command-revoke_invitation) (`revoke_invitation`)
- [Mitglied entfernen](./commands#command-remove_member) (`remove_member`)

**Darunter:** Tabellen: `company_invitation`, `invitation_delivery`, `tenant_membership`

## Freigaben, Klärfälle und offene Fragen {#resource-governance}

_Was Agenten vorgeschlagen haben, was Aufmerksamkeit braucht und was die Daten nicht beantworten_

Ein Agent ändert nie direkt den Geschäftszustand: Er schlägt vor, ein Mensch gibt frei, und der
Vorschlag läuft über dieselbe Geschäftsaktion, die auch ein Sachbearbeiter nutzt. Klärfälle sind die
abgeleitete Abweichungsliste; fehlende Informationen sammeln Fragen, die die Daten noch nicht
beantworten.

**Auch genannt:** proposal, approval, exception, attention, missing information, Vorschlag,
Freigabe, Abweichung, Klärfall, Timeline, Verlauf

**Listen**

- [Verlauf](./views#view-activity) (`activity`)
- [Abweichungen](./views#projection-exceptions) (`exceptions`)
- [Verlauf](./views#projection-timeline) (`timeline`)

**Darunter:** Agenten-Tools ohne Geschäftsaktion:
[`capability_catalog`](./commands#tool-capability_catalog),
[`capability_describe`](./commands#tool-capability_describe),
[`business_records_discover`](./commands#tool-business_records_discover),
[`exceptions_list`](./commands#tool-exceptions_list),
[`exception_explain`](./commands#tool-exception_explain),
[`proposals_awaiting_approval`](./commands#tool-proposals_awaiting_approval),
[`proposal_execution_status`](./commands#tool-proposal_execution_status),
[`proposal_approve_and_execute`](./commands#tool-proposal_approve_and_execute),
[`proposal_reject`](./commands#tool-proposal_reject),
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
