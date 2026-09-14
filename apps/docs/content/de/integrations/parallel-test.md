# Reality parallel zu Shopify, Xentral oder Odoo testen

Du musst dein ERP nicht ersetzen, um Reality zu verstehen. Betreibe Reality zunächst als
**parallelen, gegenüber dem Vorsystem lesenden Beobachter**: Kopiere ausgewählte Datensätze in einen
isolierten Reality-Mandanten, lasse Reality daraus eigene Evidence und operative Sichten aufbauen
und vergleiche das Ergebnis gemeinsam mit Menschen, die den Geschäftsfall kennen.

Der erste Pilot beweist Verständnis, nicht Automatisierung. Reality schreibt eigene Source-,
Evidence- und Reality-Datensätze, aber nichts nach Shopify, Xentral oder Odoo zurück. Aktiviere in
dieser Phase keine ausgehenden Aktionen.

## Was ist heute bereits vorhanden?

| Quelle  | Im Repository vorhanden                                                                                 | Für eine Live-Anbindung noch nötig                                  |
| ------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Shopify | Connector-Shell und ein funktionierender Interpreter für `("shopify", "order")`                         | Anmeldung, Polling/Webhooks und produktives Mapping für deinen Shop |
| Xentral | Connector-Shell mit `order`, `purchase_order`, `article`, `contact` und `payment`                       | Vendor-Transport und ein Interpreter für jeden getesteten Quelltyp  |
| Odoo    | Connector-Shell mit `sale.order`, `purchase.order`, `product.product`, `res.partner` und `account.move` | Vendor-Transport und ein Interpreter für jeden getesteten Quelltyp  |

Eine Connector-Shell beschreibt mögliche Quelltypen. Sie ist keine fertige Schnittstelle und enthält
weder Zugangsdaten noch Vendor-API-Aufrufe oder Feld-Mapping. Die ausführbare Quelle ist
`packages/reality-core/config/connector_catalog.yaml`; registrierte Objekt-Interpreter stehen in
`SOURCE_INTERPRETERS` in `services/core.py`.

## Der Pilot in vier Phasen

### 1. Capture – einen engen Geschäftsfall wählen

Lege für den Test einen getrennten Reality-Mandanten oder ein getrenntes Unternehmen an. Wähle 10–50
Datensätze mit Normal- und Problemfällen, zum Beispiel einen offenen Auftrag, eine Teillieferung,
eine Stornierung und eine unbekannte SKU. Notiere Objekttyp, undurchsichtige externe ID und
Versionszeitpunkt oder Revision.

Beginne mit genau einem Ablauf:

- Shopify: Orders und später Fulfilment Events;
- Xentral: Aufträge und Artikel;
- Odoo: `sale.order` und `product.product`.

Lies die Daten über einen kleinen Adapter oder einen JSON-/CSV-Export. Übergib das originale Objekt
unverändert an die mandantenbezogene Ingest-Grenze. `source_record_ingest_propose` zeigt die
geplante Mutation und verlangt eine menschliche Bestätigung; die HTTP API bietet dieselbe
Anwendungsfähigkeit an. Schreibe niemals Zugangsdaten in Payload oder Log.

Dies sind repräsentative Lern-Envelopes, keine Verträge der Vendor-APIs:

```json
{
  "source_system": "shopify",
  "source_type": "order",
  "external_id": "gid://shopify/Order/4711",
  "payload": {
    "id": 4711,
    "name": "#1042",
    "line_items": [{ "sku": "CHAIR-BLACK", "quantity": 4 }]
  }
}
```

```json
{
  "source_system": "xentral",
  "source_type": "order",
  "external_id": "order-4711",
  "payload": {
    "number": "SO-4711",
    "status": "released",
    "positions": [{ "article": "CHAIR-BLACK", "quantity": "4" }]
  }
}
```

```json
{
  "source_system": "odoo",
  "source_type": "sale.order",
  "external_id": "sale.order:4711",
  "payload": {
    "name": "S04711",
    "state": "sale",
    "order_line": [{ "product_code": "CHAIR-BLACK", "product_uom_qty": 4 }]
  }
}
```

Nutze die Feldnamen und die vollständige Payload, die dein System wirklich liefert. Forme sie vor
dem Speichern nicht in das Beispiel um.

### 2. Interpret – nur belegte Bedeutung übersetzen

Beginne bei Shopify Orders mit dem vorhandenen Interpreter und seinem notwendigen Mandantenkontext.
Bei Xentral oder Odoo bleiben die ersten übernommenen Datensätze `unmapped`, bis du den exakten
Interpreter für `(source_system, source_type)` implementierst und registrierst. Das ist sicher: Die
unveränderliche Payload bleibt erhalten, ohne bekannte fachliche Bedeutung vorzutäuschen.

Ordne nur zu, was der gewählte Ablauf benötigt. Eine Auftragsinterpretation löst typischerweise
Party, Item und Location auf, erstellt Document/DocumentLine als Evidence und leitet ein ausgehendes
Commitment ab. Folge dem [vollständigen Auftragsbeispiel](./order-example) und
[Ein weiteres ERP anbinden](../development/connectors).

### 3. Compare – Bedeutung statt Zeilenanzahl abstimmen

Mit `interpretation_coverage` siehst du, ob eine Quelle interpretiert wurde, geprüft werden muss,
fehlgeschlagen oder noch `unmapped` ist und welche Reality-Datensätze entstanden sind. Vergleiche
danach diese Fragen mit dem ERP-Verantwortlichen:

| Frage                                           | In Reality prüfen                        |
| ----------------------------------------------- | ---------------------------------------- |
| Was hat das ERP tatsächlich geliefert?          | unveränderliche SourceRecord-Payload     |
| Welcher Beleg und welche Zeilen wurden erkannt? | Document und DocumentLine                |
| Was ist noch versprochen?                       | offene Menge des Commitment              |
| Was wurde reserviert oder physisch bewegt?      | Reservation und Movement                 |
| Warum ist ein Auftrag gefährdet?                | Projection, Exception und Rückverfolgung |

Eine leere Queue beweist nicht, dass keine Arbeit existiert: Prüfe zuerst die
Interpretationsabdeckung. Ordne jede Abweichung einer von vier Ursachen zu – fehlende Quelldaten,
falsches Mapping, fehlende Kernregel oder falsche Erwartung – und korrigiere die richtige Schicht.

### 4. Act – Automatisierung erst nach Abnahme aktivieren

Reality bleibt beobachtend, bis die Stichprobe erklärbar und wiederholbar ist. Kläre vor jeder
aktiven Aktion:

- fachlich verantwortliche Person und erlaubten Umfang;
- Vorschau und ausdrückliche Bestätigung jeder Mutation;
- Idempotenz und Identität für das Zurückschreiben;
- Prüfung der Wirkung in Reality und im ERP;
- Abschaltung der Integration ohne Verlust der Evidence.

Beginne mit lesenden Fragen und Projections. Ergänze erst dann eine vorgeschlagene Aktion, wenn die
oder der Prozessverantwortliche die Vergleichsergebnisse abgenommen hat. Auch ein Pilot, der einen
fehlenden Interpreter oder eine fehlende Geschäftsregel sichtbar macht, ist erfolgreich.

## Fertig für den ersten Pilot

- [ ] Ein isolierter Mandant und ein enger Geschäftsfall sind festgelegt.
- [ ] Original-Payloads für Normal- und Problemfälle sind verlustfrei gespeichert.
- [ ] Wiederholungen erzeugen keine doppelten Quellversionen oder Geschäftswirkungen.
- [ ] Jeder Datensatz hat ein eindeutiges Ergebnis: interpretiert, zu prüfen, fehlgeschlagen oder
      `unmapped`.
- [ ] Entstandene Datensätze führen über Evidence zu ihrem SourceRecord zurück.
- [ ] Abweichungen zum ERP sind klassifiziert und fachlich geprüft.
- [ ] Keine ausgehende ERP-Mutation ist aktiviert.

Lies als Nächstes den [Connector-Contract](./connector-contract), bevor du aus dem Pilotadapter eine
produktive Integration machst.
