# Geschäftsprozesse

Die Prozesse, die ein Berater Schritt für Schritt durchgeht: welches Objekt, welche Aktion, welche
Liste danach zu prüfen ist und welche Klärfälle ein Schritt hinterlassen kann. Die Agenten-Playbooks
erzählen den Ablauf; diese Seiten sind der Index in das ausführbare Vokabular.

> Automatisch aus `resource_catalog.yaml` erzeugt. Diese Seite nicht von Hand bearbeiten.

## Order-to-Cash {#process-order_to_cash}

Vom Kundenauftrag über Reservierung, Versand und Rechnung bis zur ausgeglichenen Zahlung.

[Playbook lesen](../agent-playbooks/order-to-cash-fulfilment)

[Als Storyline spielen: Erste Runde](../storylines/#storyline-first-round)

[Als Storyline spielen: Auftrag bis Abschluss](../storylines/#storyline-order-to-close)

### 1. Kundenauftrag erfassen

**Objekt:** [Auftrag](./resources#resource-order)

**Aktionen**

- [Kundenauftrag oder Bestellung anlegen](./commands#command-create_manual_order)
  (`create_manual_order`)

**Danach prüfen:** [Aufträge](./views#view-orders) (`orders`),
[Verpflichtungen](./views#view-commitments) (`commitments`)

**Kann hinterlassen:** [Auftrag hängt](./exceptions#exception-order_stalled) (`order_stalled`)

### 2. Bestand für die Verpflichtung reservieren

**Objekt:** [Auftrag](./resources#resource-order)

**Aktionen**

- [Bestand reservieren](./commands#command-reserve) (`reserve`)
- [Reservierung aufheben](./commands#command-release_reservation) (`release_reservation`)

**Danach prüfen:** [Zulauf & Bedarf](./views#view-supply_demand) (`supply_demand`),
[Reservierungen](./views#view-reservations) (`reservations`)

**Kann hinterlassen:**
[Lieferverpflichtung gefährdet](./exceptions#exception-outgoing_commitment_at_risk)
(`outgoing_commitment_at_risk`),
[Reservierung übersteigt Bestand](./exceptions#exception-reservation_exceeds_stock)
(`reservation_exceeds_stock`)

### 3. Sperren oder ändern

**Objekt:** [Auftrag](./resources#resource-order)

**Aktionen**

- [Verpflichtung sperren oder freigeben](./commands#command-hold_commitment) (`hold_commitment`)
- [Liefersperre setzen oder aufheben](./commands#command-hold_party_delivery)
  (`hold_party_delivery`)
- [Verpflichtung ändern](./commands#command-revise_commitment) (`revise_commitment`)

**Danach prüfen:** [Lieferhindernisse](./views#view-fulfillment_blockers) (`fulfillment_blockers`)

**Kann hinterlassen:**
[Sperre der Verpflichtung nicht aufgehoben](./exceptions#exception-commitment_hold_unreleased)
(`commitment_hold_unreleased`),
[Liefersperre nicht aufgehoben](./exceptions#exception-party_hold_unreleased)
(`party_hold_unreleased`), [Kreditlimit überschritten](./exceptions#exception-credit_limit_exceeded)
(`credit_limit_exceeded`)

### 4. Ware versenden und den Spediteur verfolgen

**Objekt:** [Lieferung und Wareneingang](./resources#resource-delivery)

**Aktionen**

- [Packstück versenden oder Wareneingang buchen](./commands#command-record_packaged_execution)
  (`record_packaged_execution`)
- [Sendungsavis erfassen](./commands#command-record_shipment_notice) (`record_shipment_notice`)
- [Sendungsereignis erfassen](./commands#command-record_shipment_event) (`record_shipment_event`)
- [Explain a physical shipment](./commands#tool-shipment_explain) (`shipment_explain`)

**Danach prüfen:** [Lagerarbeitsvorrat](./views#view-warehouse_queue) (`warehouse_queue`),
[Lagerbewegungen](./views#view-movements) (`movements`)

**Kann hinterlassen:**
[Lieferverzug an Kunden](./exceptions#exception-overdue_outgoing_customer_commitment)
(`overdue_outgoing_customer_commitment`)

### 5. Geliefertes fakturieren

**Objekt:** [Rechnung und Gutschrift](./resources#resource-invoice)

**Aktionen**

- [Ausgangsrechnung erfassen](./commands#command-record_sales_invoice) (`record_sales_invoice`)
- [Ausgangsrechnung buchen](./commands#command-post_sales_invoice) (`post_sales_invoice`)

**Danach prüfen:** [Offene Posten](./views#view-open_items) (`open_items`)

**Kann hinterlassen:** [Geliefert, nicht fakturiert](./exceptions#exception-shipped_not_billed)
(`shipped_not_billed`),
[Ausgangsrechnung nicht gebucht](./exceptions#exception-sales_invoice_unposted)
(`sales_invoice_unposted`)

### 6. Zahlungseingang erfassen und zuordnen

**Objekt:** [Zahlung und Ausgleich](./resources#resource-payment)

**Aktionen**

- [Zahlungseingang buchen](./commands#command-post_customer_payment) (`post_customer_payment`)
- [Zahlung zuordnen oder Guthaben verwenden](./commands#command-apply_settlement)
  (`apply_settlement`)
- [Abzug akzeptieren](./commands#command-accept_adjustment) (`accept_adjustment`)
- [Payment and credit context](./commands#tool-finance_settlement_context)
  (`finance_settlement_context`)
- [Party balances](./commands#tool-finance_party_balances) (`finance_party_balances`)

**Danach prüfen:** [Zahlungen](./views#view-payments) (`payments`),
[Offene Posten](./views#view-open_items) (`open_items`)

**Kann hinterlassen:** [Überfällige Forderung](./exceptions#exception-overdue_receivable)
(`overdue_receivable`),
[Nicht zugeordneter Finanzvorgang](./exceptions#exception-unmatched_financial_event)
(`unmatched_financial_event`)

### 7. Verpflichtungen schließen

**Objekt:** [Auftrag](./resources#resource-order)

**Aktionen**

- [Schließen alter Verpflichtungen vorschauen](./commands#command-preview_stale_promise_closure)
  (`preview_stale_promise_closure`)
- [Alte Verpflichtungen schließen](./commands#command-close_stale_promises) (`close_stale_promises`)

**Danach prüfen:** [Verpflichtungen](./views#view-commitments) (`commitments`)

**Kann hinterlassen:** [Auftrag hängt](./exceptions#exception-order_stalled) (`order_stalled`)

## Purchase-to-Pay {#process-procure_to_pay}

Vom Bedarf über Bestellung, Wareneingang und Rechnungsprüfung bis zum Zahllauf.

[Playbook lesen](../agent-playbooks/purchasing-and-replenishment)

[Als Storyline spielen: Einkauf bis Zahlung](../storylines/#storyline-purchase-to-pay)

### 1. Bedarf ermitteln

**Objekt:** [Artikel](./resources#resource-item)

**Aktionen**

- [Read item supply and demand](./commands#tool-item_supply_demand) (`item_supply_demand`)
- [Read fulfillment blockers](./commands#tool-fulfillment_blockers) (`fulfillment_blockers`)

**Danach prüfen:** [Zulauf & Bedarf](./views#view-supply_demand) (`supply_demand`),
[Lieferhindernisse](./views#view-fulfillment_blockers) (`fulfillment_blockers`)

**Kann hinterlassen:**
[Lieferverpflichtung gefährdet](./exceptions#exception-outgoing_commitment_at_risk)
(`outgoing_commitment_at_risk`)

### 2. Bestellung anlegen

**Objekt:** [Auftrag](./resources#resource-order)

**Aktionen**

- [Kundenauftrag oder Bestellung anlegen](./commands#command-create_manual_order)
  (`create_manual_order`)

**Danach prüfen:** [Verpflichtungen](./views#view-commitments) (`commitments`)

**Kann hinterlassen:**
[Lieferverzug des Lieferanten](./exceptions#exception-overdue_incoming_supplier_commitment)
(`overdue_incoming_supplier_commitment`)

### 3. Wareneingang buchen

**Objekt:** [Lieferung und Wareneingang](./resources#resource-delivery)

**Aktionen**

- [Packstück versenden oder Wareneingang buchen](./commands#command-record_packaged_execution)
  (`record_packaged_execution`)
- [Lagerbewegung buchen](./commands#command-record_movement) (`record_movement`)
- [Charge anlegen](./commands#command-create_lot) (`create_lot`)
- [Mindesthaltbarkeit angeben](./commands#command-state_lot_expiry) (`state_lot_expiry`)

**Danach prüfen:** [Lagerbewegungen](./views#view-movements) (`movements`),
[Bestand](./views#view-inventory) (`inventory`)

**Kann hinterlassen:** [Unerklärte Lagerbewegung](./exceptions#exception-unexplained_movement)
(`unexplained_movement`), [Abgelaufener Bestand](./exceptions#exception-stock_expired)
(`stock_expired`)

### 4. Eingangsrechnung erfassen und buchen

**Objekt:** [Rechnung und Gutschrift](./resources#resource-invoice)

**Aktionen**

- [Eingangsrechnung erfassen](./commands#command-record_supplier_invoice)
  (`record_supplier_invoice`)
- [Eingangsrechnung buchen](./commands#command-post_supplier_invoice) (`post_supplier_invoice`)

**Danach prüfen:** [Offene Posten](./views#view-open_items) (`open_items`)

**Kann hinterlassen:** [Wareneingang ohne Rechnung](./exceptions#exception-receipt_unbilled)
(`receipt_unbilled`),
[Eingangsrechnung nicht gebucht](./exceptions#exception-supplier_invoice_unposted)
(`supplier_invoice_unposted`),
[Doppelte Eingangsrechnung](./exceptions#exception-duplicate_supplier_invoice)
(`duplicate_supplier_invoice`)

### 5. Rechnungsprüfung gegen Bestellung und Wareneingang

**Objekt:** [Rechnung und Gutschrift](./resources#resource-invoice)

**Aktionen**

- [List operational exceptions](./commands#tool-exceptions_list) (`exceptions_list`)
- [Explain an operational exception](./commands#tool-exception_explain) (`exception_explain`)

**Danach prüfen:** [Offene Posten](./views#view-open_items) (`open_items`)

**Kann hinterlassen:** [Fakturiert, nicht geliefert](./exceptions#exception-billed_not_received)
(`billed_not_received`),
[Rechnungspreis weicht von der Vereinbarung ab](./exceptions#exception-invoice_price_differs)
(`invoice_price_differs`)

### 6. Lieferanten per Zahllauf bezahlen

**Objekt:** [Zahlung und Ausgleich](./resources#resource-payment)

**Aktionen**

- [Zahllauf vorschauen](./commands#command-preview_payment_run) (`preview_payment_run`)
- [Zahllauf ausführen](./commands#command-execute_payment_run) (`execute_payment_run`)
- [Zahlungsausgang buchen](./commands#command-post_supplier_payment) (`post_supplier_payment`)

**Danach prüfen:** [Zahlungen](./views#view-payments) (`payments`)

**Kann hinterlassen:** [Überfällige Verbindlichkeit](./exceptions#exception-overdue_payable)
(`overdue_payable`), [Skonto noch möglich](./exceptions#exception-purchase_discount_available)
(`purchase_discount_available`)

### 7. Lieferantengutschriften und Lieferantenretouren

**Objekt:** [Retoure](./resources#resource-return)

**Aktionen**

- [Lieferantengutschrift buchen](./commands#command-post_supplier_credit_note)
  (`post_supplier_credit_note`)
- [Lieferantengutschrift mit Rechnung verrechnen](./commands#command-allocate_supplier_credit_note)
  (`allocate_supplier_credit_note`)
- [Lieferantenerstattung buchen](./commands#command-post_supplier_refund) (`post_supplier_refund`)

**Danach prüfen:** [Offene Posten](./views#view-open_items) (`open_items`)

**Kann hinterlassen:**
[Lieferantenretoure nicht gutgeschrieben](./exceptions#exception-supplier_return_not_credited)
(`supplier_return_not_credited`),
[Lieferant hat mehr gutgeschrieben als zurückging](./exceptions#exception-supplier_credit_not_returned)
(`supplier_credit_not_returned`),
[Lieferantengutschrift nicht eingefordert](./exceptions#exception-supplier_credit_unclaimed)
(`supplier_credit_unclaimed`)

## Kundenretouren {#process-returns}

Von der Ankündigung über den Retourenwareneingang und die Entscheidung bis zu Gutschrift oder
Erstattung.

[Playbook lesen](../agent-playbooks/returns)

### 1. Der Kunde kündigt eine Retoure an

**Objekt:** [Retoure](./resources#resource-return)

**Aktionen**

- [Retoure ankündigen](./commands#command-announce_customer_return) (`announce_customer_return`)
- [Retourenankündigung zurückziehen](./commands#command-withdraw_return_announcement)
  (`withdraw_return_announcement`)
- [Angekündigte Retouren anzeigen](./commands#command-return_announcements) (`return_announcements`)

**Kann hinterlassen:**
[Angekündigte Retoure nicht eingetroffen](./exceptions#exception-announced_return_not_arrived)
(`announced_return_not_arrived`)

### 2. Die Ware kommt an

**Objekt:** [Lieferung und Wareneingang](./resources#resource-delivery)

**Aktionen**

- [Packstück versenden oder Wareneingang buchen](./commands#command-record_packaged_execution)
  (`record_packaged_execution`)
- [Lagerbewegung buchen](./commands#command-record_movement) (`record_movement`)

**Danach prüfen:** [Lagerbewegungen](./views#view-movements) (`movements`),
[Bestand](./views#view-inventory) (`inventory`)

**Kann hinterlassen:** [Retoure nicht bearbeitet](./exceptions#exception-return_unresolved)
(`return_unresolved`)

### 3. Gutschrift erteilen

**Objekt:** [Rechnung und Gutschrift](./resources#resource-invoice)

**Aktionen**

- [Retourengutschrift erfassen](./commands#command-record_sales_credit) (`record_sales_credit`)
- [Gutschrift buchen](./commands#command-post_sales_credit_note) (`post_sales_credit_note`)
- [Manuellen Beleg erfassen](./commands#command-create_manual_document_with_lines)
  (`create_manual_document_with_lines`)

**Danach prüfen:** [Offene Posten](./views#view-open_items) (`open_items`)

**Kann hinterlassen:**
[Retourniert, nicht gutgeschrieben](./exceptions#exception-returned_not_credited)
(`returned_not_credited`),
[Gutgeschrieben, nicht retourniert](./exceptions#exception-credited_not_returned)
(`credited_not_returned`), [Gutschrift nicht gebucht](./exceptions#exception-credit_note_unposted)
(`credit_note_unposted`)

### 4. Gutschrift verrechnen oder erstatten

**Objekt:** [Zahlung und Ausgleich](./resources#resource-payment)

**Aktionen**

- [Gutschrift mit Rechnung verrechnen](./commands#command-allocate_credit_note)
  (`allocate_credit_note`)
- [Kundenerstattung buchen](./commands#command-post_customer_refund) (`post_customer_refund`)
- [Available credit](./commands#tool-finance_credits) (`finance_credits`)

**Danach prüfen:** [Zahlungen](./views#view-payments) (`payments`),
[Offene Posten](./views#view-open_items) (`open_items`)

**Kann hinterlassen:** [Gutschrift nicht ausgeglichen](./exceptions#exception-credit_note_unsettled)
(`credit_note_unsettled`)

## Stammdaten und Quellen {#process-master_data}

Geschäftspartner, Artikel, Lagerorte, Preise und Konditionen anlegen, die liefernden Systeme
anbinden und aktuell halten.

[Playbook lesen](../agent-playbooks/master-data-and-sources)

### 1. Geschäftspartner

**Objekt:** [Geschäftspartner](./resources#resource-party)

**Aktionen**

- [Geschäftspartner anlegen](./commands#command-create_party) (`create_party`)
- [Artikel anlegen](./commands#command-create_item) (`create_item`)
- [Lagerort anlegen](./commands#command-create_location) (`create_location`)
- [Stammdatensatz aktivieren oder deaktivieren](./commands#command-set_master_data_active)
  (`set_master_data_active`)

**Danach prüfen:** [Geschäftspartner](./views#view-parties) (`parties`),
[Artikel](./views#view-items) (`items`), [Lagerorte](./views#view-locations) (`locations`)

**Kann hinterlassen:** [Einheiten nicht vergleichbar](./exceptions#exception-units_not_comparable)
(`units_not_comparable`)

### 2. Aktuell halten

**Objekt:** [Artikel](./resources#resource-item)

**Aktionen**

- [Geschäftspartner ändern](./commands#command-update_party) (`update_party`)
- [Artikel ändern](./commands#command-update_item) (`update_item`)
- [Lagerort ändern](./commands#command-update_location) (`update_location`)

**Danach prüfen:** [Geschäftspartner](./views#view-parties) (`parties`),
[Artikel](./views#view-items) (`items`), [Lagerorte](./views#view-locations) (`locations`)

### 3. Preise

**Objekt:** [Preise und Zahlungsbedingungen](./resources#resource-terms)

**Aktionen**

- [Preisliste anlegen](./commands#command-create_price_list) (`create_price_list`)
- [Staffelpreis anlegen](./commands#command-create_price_list_entry) (`create_price_list_entry`)
- [Preisliste zuweisen](./commands#command-assign_party_price_list) (`assign_party_price_list`)
- [Preisgruppe anlegen und zuweisen](./commands#command-create_party_group) (`create_party_group`)
- [Zahlungsbedingung anlegen](./commands#command-create_payment_term) (`create_payment_term`)

**Danach prüfen:** [Konditionen](./views#view-commercial_terms) (`commercial_terms`)

**Kann hinterlassen:**
[Rechnungspreis weicht von der Vereinbarung ab](./exceptions#exception-invoice_price_differs)
(`invoice_price_differs`),
[Unter Einkaufspreis verkauft](./exceptions#exception-sold_below_purchase_price)
(`sold_below_purchase_price`)

### 4. Quelle registrieren und festlegen

**Objekt:** [Beleg und Quellsystem](./resources#resource-source)

**Aktionen**

- [Quellsystem anlegen](./commands#command-create_source_system) (`create_source_system`)
- [Quellfähigkeit festlegen](./commands#command-create_source_capability)
  (`create_source_capability`)
- [Connector einrichten](./commands#command-install_connector_shell) (`install_connector_shell`)
- [Quelldaten importieren](./commands#command-enqueue_source) (`enqueue_source`)

**Danach prüfen:** [Quellen & Importe](./views#view-sources_imports) (`sources_imports`),
[Belege](./views#view-documents) (`documents`)

**Kann hinterlassen:** [Quelle verstummt](./exceptions#exception-silent_source) (`silent_source`),
[Quelle nicht interpretierbar](./exceptions#exception-source_interpretation_failure)
(`source_interpretation_failure`)

### 5. Einen fehlenden Sachverhalt als Fact erfassen

**Objekt:** [Beleg und Quellsystem](./resources#resource-source)

**Aktionen**

- [Fact erfassen](./commands#command-observe_fact) (`observe_fact`)
- [List missing information](./commands#tool-reality_gaps) (`reality_gaps`)
- [Propose missing information](./commands#tool-reality_gap_create_propose)
  (`reality_gap_create_propose`)

**Danach prüfen:** [Belege](./views#view-documents) (`documents`)

## Finanzeinrichtung und Periodenarbeit {#process-finance_setup}

Konten, Eröffnungsbuchungen, die Zuordnung zum externen Buchhaltungssystem und Stornos.

[Playbook lesen](../agent-playbooks/receivables-and-payments)

### 1. Operative Konten einrichten

**Objekt:** [Buchhaltung und Konten](./resources#resource-accounting)

**Aktionen**

- [Operative Konten anlegen](./commands#command-initialize_accounts) (`initialize_accounts`)
- [Operatives Konto anlegen](./commands#command-create_account) (`create_account`)
- [Operatives Konto ändern](./commands#command-update_account) (`update_account`)
- [Standardkonto festlegen](./commands#command-set_default_account) (`set_default_account`)

**Danach prüfen:** [Journal](./views#view-journal) (`journal`)

### 2. Eröffnungsposten importieren

**Objekt:** [Buchhaltung und Konten](./resources#resource-accounting)

**Aktionen**

- [Kontext der Eröffnungsposten anzeigen](./commands#command-opening_context) (`opening_context`)
- [Eröffnungsposten importieren](./commands#command-import_opening) (`import_opening`)

**Danach prüfen:** [Offene Posten](./views#view-open_items) (`open_items`),
[Journal](./views#view-journal) (`journal`)

### 3. Buchungen dem externen Buchhaltungssystem zuordnen

**Objekt:** [Buchhaltung und Konten](./resources#resource-accounting)

**Aktionen**

- [Buchhaltungsziel pflegen](./commands#command-maintain_target_configuration)
  (`maintain_target_configuration`)
- [Finanzreferenz pflegen](./commands#command-maintain_reference) (`maintain_reference`)
- [Quellcode zuordnen](./commands#command-set_source_mapping) (`set_source_mapping`)
- [Finanzkomponente zuordnen](./commands#command-assign_component) (`assign_component`)

**Danach prüfen:** [Journal](./views#view-journal) (`journal`)

### 4. Eine falsche Buchung stornieren

**Objekt:** [Buchhaltung und Konten](./resources#resource-accounting)

**Aktionen**

- [Buchung stornieren](./commands#command-reverse_ledger_posting_group)
  (`reverse_ledger_posting_group`)
- [Lagerbewegung korrigieren](./commands#command-correct_movement) (`correct_movement`)

**Danach prüfen:** [Journal](./views#view-journal) (`journal`),
[Lagerbewegungen](./views#view-movements) (`movements`)

**Kann hinterlassen:**
[Nicht zugeordneter Finanzvorgang](./exceptions#exception-unmatched_financial_event)
(`unmatched_financial_event`)
