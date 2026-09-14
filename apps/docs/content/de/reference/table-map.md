# Tabellenübersicht und häufige Missverständnisse

Zwei Anhänge des [Handbuchs](../concepts/business-reality-guide): welche Tabelle wofür
verantwortlich ist, und welche Annahmen aus der ERP-Welt hier nicht gelten.

## Tabellenübersicht nach Verantwortung

Der genaue aktuelle Stand wird im
[Datenmodell](https://github.com/Xentral-Labs/reality/blob/main/docs/DATA_MODEL.md) geführt.

| Verantwortung           | Wichtigste Tabellen                                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Unternehmenszugriff     | `tenant`, `tenant_membership`, `company_invitation`, `invitation_delivery`, `security_audit_event`                             |
| Stammdaten              | `party`, `party_role`, `party_hold`, `item`, `location`, `payment_term`                                                        |
| Preisfindung            | `price_list`, `price_list_entry`, `party_price_list`, `party_group`, `party_group_member`, `party_group_price_list`            |
| Integration             | `source_system`, `source_capability`                                                                                           |
| Quelleingang            | `source_stream`, `source_record`, `source_artifact`, `import_job`, `interpretation_outcome`, `interpretation_record_reference` |
| Evidence                | `document`, `document_line`                                                                                                    |
| Zusage und Ausführung   | `commitment`, `commitment_hold`, `reservation`, `movement`, `movement_correction`                                              |
| Lageridentität          | `handling_unit`, `lot`, `serial_unit`                                                                                          |
| Finanzen                | `ledger_entry`, `ledger_reversal`, `settlement_allocation`                                                                     |
| Beobachtung und Prüfung | `fact`, `action`, `business_event`                                                                                             |
| Leseoptimierung         | `projection_row`, `projection_checkpoint`                                                                                      |
| Dialog                  | `chat_session`, `chat_message`                                                                                                 |

## Häufige Missverständnisse

**„Der Kundenauftrag ist erfüllt, also muss die Rechnung bezahlt sein.“** Nein. Lieferung und
Zahlung sind unabhängige Achsen der Reality.

**„Reservierter Bestand hat das Lager verlassen.“** Nein. Nur ein Movement ändert den physischen
Bestand.

**„Erwartete Zugänge sind verfügbarer Bestand.“** Nein. Sie zählen zur erwarteten Verfügbarkeit,
können aber vor dem Wareneingang nicht versendet werden.

**„Eine neue Quellversion ändert den alten Auftrag.“** Nein. Sie bewahrt einen neuen SourceRecord.
Shopify-Updates benötigen derzeit eine Prüfung und lassen bisherige Evidence und Reality
unverändert.

**„Eine Korrektur löscht den Fehler.“** Nein. Sie fügt eine Inverse und optional einen Ersatz an und
bewahrt die Erklärung.

**„Eine Zahlung gehört direkt zu einer Rechnung.“** Die Zahlung hat ihre eigene Evidence und ihre
eigene Buchung. Die SettlementAllocation drückt aus, wie viel davon auf eine Rechnung entfällt.

**„Eine Projection ist eine weitere Quelle der Wahrheit.“** Nein. Sie ist ein wiederaufbaubares
Lesemodell.

**„Jedes Feld aus dem Vorsystem braucht eine Spalte.“** Nein. Der SourceRecord bewahrt die Payload.
Ein Feld wird erst typisiert, wenn wiederkehrendes Kernverhalten den Bedarf belegt.

## Das Datenmodell: Tabellen und Verantwortlichkeiten {#data-model}

### Mandantengrenze und Stammdaten

Jeder Geschäftsdatensatz gehört zu einem Mandanten, und jede Abfrage trägt diese Grenze; eine ID
eines anderen Mandanten verhält sich wie nicht vorhanden. Stammdaten werden deaktiviert, nie
gelöscht, damit alte Documents, Commitments und Movements lesbar bleiben. Typisiert werden nur
Felder, die wiederholt Berechnungen, Filter, Joins oder Entscheidungen treiben; den Rest bewahrt der
Roh-Payload.

| Tabelle        | Bedeutung in der Geschäftssprache                                           |
| -------------- | --------------------------------------------------------------------------- |
| `tenant`       | Die Unternehmensgrenze innerhalb der gemeinsamen Datenbank.                 |
| `party`        | Ein Unternehmen oder eine Person, die am Geschäft teilnimmt.                |
| `party_role`   | Ob eine Party als Unternehmen, Kunde, Lieferant oder mehreres auftritt.     |
| `party_hold`   | Ein aktueller oder historisch aufgehobener Lieferstopp für eine Party.      |
| `item`         | Ein Produkt oder eine Leistung; nur bestandsgeführte Items haben Movements. |
| `location`     | Ein Lager, ein Lagerplatz oder ein virtueller Ort.                          |
| `payment_term` | Eine wiederverwendbare Zahlungskondition mit undurchsichtiger Identität.    |
| Preistabellen  | Preislisten, Staffeln, Party-Zuordnungen und Party-Gruppen-Zuordnungen.     |

### Quelltabellen: bewahren, was angekommen ist

| Tabelle                           | Rolle                                                                            |
| --------------------------------- | -------------------------------------------------------------------------------- |
| `source_system`                   | Eine konfigurierte Herkunft, etwa ein Shopify-Shop.                              |
| `source_capability`               | Welche Art von Daten diese Herkunft liefern darf.                                |
| `source_stream`                   | Der stabile Kopf für `(System, Typ, externe ID)`.                                |
| `source_record`                   | Eine unveränderliche, verlustfreie Version einer Payload.                        |
| `source_artifact`                 | Unveränderliche Originaldatei samt Metadaten.                                    |
| `import_job`                      | Veränderlicher Warteschlangenzustand für die Interpretation eines SourceRecords. |
| `interpretation_outcome`          | Unveränderliches Ergebnis jedes abgeschlossenen Versuchs.                        |
| `interpretation_record_reference` | Prüfverweise auf erzeugte oder erkannte Datensätze.                              |

Ein `SourceStream` sagt „alle Versionen der Shopify-Bestellung 4711 gehören zusammen“; jeder
`SourceRecord` ist ein exakter Payload zu einem Zeitpunkt. Eine identische Lieferung wird am Hash
erkannt und ignoriert, eine geänderte wird eine neue Version, ein unbekanntes Format bleibt als
`unmapped` erhalten statt geraten zu werden. Eine fehlgeschlagene Interpretation hinterlässt keine
halb angelegten Geschäftsdatensätze, und jeder Versuch bleibt sichtbar.

### Evidence-Tabellen: Documents und Positionen

`document` ist ein minimaler Belegkopf: Art, Nummer, Geschäftspartner, Währung, vereinbarter
Gesamtbetrag, Daten, Zahlungsbedingung und Herkunft. `document_line` hält Artikel, Menge, Einheit
und Preis fest. Jeder Betrag ist der, den die Quelle genannt hat; Reality multipliziert nie Menge
mal Preis und summiert keine Positionen, und ein Gesamtbetrag, der nicht zu seinen Positionen passt,
bleibt als Befund über die Quelle stehen.

Ein Belegstatus beschreibt den Lebenszyklus der Aussage, etwa `recorded` oder `superseded`. Er
bedeutet nie Lieferung, Reservierung, Erfüllung oder Zahlung. „Ist Auftrag `SO-1042` offen?“ sind
vier Fragen: Ist die externe Version aktuell, ist noch Menge versprochen, ist noch Bestand
reserviert, ist ein Rechnungsbetrag unbezahlt. Kein einzelnes Statusfeld beantwortet alle vier
ehrlich.

### Commitments: gerichtete Zusagen

| Typ                 | Von       | An    | Erfüllt durch                   |
| ------------------- | --------- | ----- | ------------------------------- |
| `customer_delivery` | Acme      | Kunde | verknüpfte `shipment`-Movements |
| `supplier_delivery` | Lieferant | Acme  | verknüpfte `receipt`-Movements  |

Ein Commitment nennt Artikel, Lagerort, versprochene Menge, Fälligkeit und Priorität. Es kann durch
eine DocumentLine, nur durch ein Document oder durch keines von beiden gestützt sein; eine echte
Zusage kann also vor dem formalen Beleg existieren.

```text
erfüllte Menge = verknüpfte qualifizierende Movements
                 - qualifizierende ursprüngliche Movements, die korrigiert wurden

offene Menge = max(0, zugesagte Menge - erfüllte Menge)
```

Gespeichert wird `open`, `fulfilled` oder `cancelled`; „teilerfüllt“ ist abgeleitet.

### Reservations: Zuordnung ohne Bewegung

Eine Reservation ordnet Bestand an einem Lagerort einem ausgehenden Kunden-Commitment zu; ihre
einzige Herkunftsverknüpfung ist `commitment_id`.

```text
active --shipment--> consumed
active --release---> released
```

Beide Endzustände bleiben sichtbar. Ein Teilversand verbraucht das Original und legt für den Rest
eine neue aktive Reservation an. Eingehende Lieferanten-Commitments sind keine Reservierungen:
Künftige Ware erhöht die projizierte Verfügbarkeit, ist aber kein Bestand.

### Movements: das physische Journal

Bestand ist das Nettoergebnis des Movement-Journals, kein editierbarer Saldo.

| Movement-Typ    | Von              | Nach             | Bedeutung                                             |
| --------------- | ---------------- | ---------------- | ----------------------------------------------------- |
| `opening_stock` | keiner           | erforderlich     | Anfangsbestand physisch festlegen.                    |
| `receipt`       | keiner           | erforderlich     | Ware annehmen, optional gegen eine Lieferantenzusage. |
| `shipment`      | erforderlich     | keiner           | Ware versenden, optional gegen eine Kundenzusage.     |
| `transfer`      | erforderlich     | erforderlich     | Ware intern umlagern.                                 |
| `return`        | keiner           | erforderlich     | Retourware zurück in den Bestand nehmen.              |
| `adjustment`    | genau eine Seite | genau eine Seite | Eine gezählte Differenz mit Begründung erfassen.      |

Die Menge ist positiv, die Lagerorte geben die Richtung an, und ausgehende Movements können den
Bestand nicht überschreiten. Movements können Palette, Charge und Seriennummer tragen.

### Finanzielle Reality

`ledger_entry` ist ein unveränderlicher Nebenbuch-Eintrag; Einträge bilden ausgeglichene
Buchungsgruppen in einer Währung. Eine Zahlung hat ihr eigenes Document und ihre eigenen
LedgerEntries, und `settlement_allocation` verbindet den Kontrollkonto-Eintrag der Zahlung mit dem
der Rechnung. Eine Zahlung kann mehrere Rechnungen ausgleichen, eine Rechnung mehrere Zahlungen
aufnehmen. „Offen“, „teilbezahlt“ und „bezahlt“ werden abgeleitet, nie gespeichert.

### Facts, Ereignisse, Vorschläge und Projections

| Tabelle                     | Zweck                                                                   | Was sie nicht ist                           |
| --------------------------- | ----------------------------------------------------------------------- | ------------------------------------------- |
| `fact`                      | Unveränderliche, quellbelegte Beobachtung über ein geprüftes Predicate. | Aktueller Bestand oder kopiertes Stammfeld. |
| `business_event`            | Mitteilung, dass eine Domänenänderung festgeschrieben wurde.            | Der maßgebliche Geschäftsdatensatz.         |
| `action` (`ChangeProposal`) | Prüfspur einer vorbereiteten Änderung, ihrer Freigabe und Ausführung.   | Ein alternativer direkter Schreibweg.       |
| `projection_row`            | Wiederaufbaubare materialisierte Lesedaten.                             | Geschäftliche Wahrheit.                     |
| `projection_checkpoint`     | Letzte eingearbeitete Ereignissequenz des Mandanten.                    | Nachweis der zugrunde liegenden Aktion.     |

Eine Projection ist wie eine ERP-Arbeitsliste oder ein Index: Ist sie veraltet oder verloren, wird
sie aus den Datensätzen und BusinessEvents neu aufgebaut, und Kommandos vertrauen ihr nie, um
Überzuordnung oder Überlieferung zu erlauben. Facts, die einzige Datensatzart, die hier nicht
durchgegangen wird, haben ein eigenes Kapitel:
[Facts und offene Fragen](../concepts/business-reality-guide/06-facts-and-open-questions).
