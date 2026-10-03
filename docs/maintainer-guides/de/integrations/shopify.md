# Shopify anbinden

[Welche Daten brauche ich zuerst? Beispiel-ERP Schritt für Schritt](./example-erp.md) zeigt einen
kleinen Einstieg und seine Ausbaustufen.

Diese Anleitung führt vom fachlichen Umfang bis zur Abnahme. Sie trennt vorhandene Vorlagen von noch
zu entwickelnden Teilen.

## Was vollständig bedeutet

Vollständigkeit gilt **für die gewählte Betriebsart und Fragestellung**. Der kleine
Zuschauer-Einstieg braucht nicht die gesamte Matrix. Die folgenden Bereiche beschreiben den
möglichen Gesamtumfang, den du schrittweise erweitern kannst.

Decke Produkte/Varianten, Kunden, Aufträge, Änderungen, Fulfillment und Erstattungen des Shops ab.
Benenne zusätzliche Quellen für Einkauf, Lagerausführung und rechtsgültige Finanzbelege, wenn der
Shop dafür nicht autoritativ ist. Shopify plus ERP/Zahlungsanbieter kann den vereinbarten
Unternehmensumfang gemeinsam abdecken. „100 %“ ist dieser geprüfte Gesamtumfang, nicht jede
Shop-Einstellung, Marketinginhalt oder eine aus Auftragsstatus erfundene Buchhaltung.

## Betriebsarten

### A) Shopify zuschauen

**Shopify betreibt den Shop; Reality schaut zu und erklärt.** Die Anbindung greift nur lesend auf
Shopify zu. Aufträge, Artikel-/Variantenidentitäten, Lagerortmengen, Fulfillment, Erstattungen und
vereinbarte Zahlungsdaten kommen als originale `SourceRecord`-Payloads an. Unterstützte Interpreter
erzeugen daraus lokale Evidence- und Reality-Datensätze. „Zuschauen“ bedeutet keine Änderung im
Vorsystem, nicht keine Speicherung in Reality.

Shopify und die zuständigen Lager-/Zahlungsquellen entscheiden und führen Geschäftsvorgänge aus.
Reality zeigt unterstützte Beobachtungen und Ausnahmen mit ihren Belegen. In dieser Betriebsart
reserviert Reality keinen Shopbestand und löst weder Versand noch Erstattung oder Rechnung aus.
Fehlende Quellenabdeckung bleibt sichtbar; ein Shop-Bestandsstand beweist keine physische
Bewegungshistorie.

**Beispiel:** Shopify erfasst einen Auftrag über 10 Stück. Später meldet die zuständige Quelle den
Versand von 4 Stück. Reality kann die verbleibenden 6 erklären, sobald die nötigen Auftrags- und
Ausführungs-Interpreter samt Identitätsverknüpfungen umgesetzt sind. Reality erteilt keinen Auftrag,
diese 6 zu versenden. Eine angekündigte Erstattung beweist außerdem weder Warenrückkehr noch
erfolgreiche Geldrückgabe.

Die Tabelle weiter unten beschreibt Erstimport, Webhooks und Abgleich. Für Einkauf, rechtsgültige
Rechnungen und Lagerbelege außerhalb des Shops ergänzt du die zuständigen Quellen. Vergleiche
[B) Xentral zuschauen](./xentral.md#b-xentral-zuschauen), wenn das ERP diese Abläufe führt. Das sind
Zielverträge für den Betrieb; der Implementierungsstand darunter benennt vorhandene und fehlende
Fähigkeiten.

Wenn Reality später Entscheidungen übernehmen soll, lies
[C) Reality entscheidet, Xentral führt aus](./xentral.md#c-reality-entscheidet-xentral-führt-aus). Das
ist eine eigene Betriebsart mit geprüftem Rückweg.

## Bevor du beginnst

Nutze einen Entwicklungs-/Testshop und eine freigegebene App mit den Leserechten sowie
Auftrags-Historien-/Kundendatenzugriffen, die dein Umfang benötigt. Lege eine Admin-API-Version
fest. Verwende die GraphQL Admin API für Abfragen; prüfe HTTPS-Webhook-Lieferungen nach Shopifys
Signaturvertrag, bevor du sie annimmst. Bulk Operations können den Erstimport unterstützen. Halte
die tatsächlich empfangenen GraphQL-/Webhook-Formate fest. Lies den
[Von Quelldaten zu Reality](./connector-contract.md).

## Aktueller Implementierungsstand

Die Shell `shopify` in `packages/reality-core/config/connector_catalog.yaml` nennt
order/product/customer/fulfillment/refund. `SOURCE_INTERPRETERS` in `services/core.py` registriert
nur `("shopify", "order")` und `("shopify", "refund")`. `shop_order_changes.py` unterstützt
spezifizierte Mengenreduzierungen/Stornierungen; nicht unterstützte Änderungen bleiben prüfbar.
`shop_refunds.py` interpretiert unterstützte Erstattungen, beweist aber keine vollständige
Zahlungs-, Lager- oder Buchhaltungsabdeckung. Anmeldung, Live-Abfrage und Webhook-Transport liefert
die Shell nicht. Der Auftrags-Interpreter verarbeitet das Fixture-Format mit `line_items`, nicht
eine beliebige GraphQL-Antwort.

## Abdeckungsmatrix

**Kleiner Einstieg in A: Aufträge nachvollziehen.** Dafür brauchst du Aufträge und Positionen,
relevante Änderungen/Stornierungen sowie die zur Interpretation nötigen Artikel-, Partner- und
Quellidentitäten. Kontext kann aus vorhandenen Reality-Stammdaten kommen; ein vollständiger
Stammdatenimport ist dafür nicht automatisch nötig. Versand, Zahlungen, Einkauf und Retouren ergänzt
du erst für entsprechende Fragestellungen.

Diese Matrix ist **keine Pflichtliste für jeden Zuschauerbetrieb**. „Basis“ gilt für den genannten
Einstieg; weitere Zeilen werden erst für das jeweilige Ziel benötigt. Ohne Ausführungsdaten kannst
du beispielsweise einen Auftrag anzeigen, aber keine verlässlich offene Liefermenge behaupten.

| Quellbereich                          | Betriebsart und Bedarf               | Was übernommen wird                                                                                       | Fachlicher Zweck in Reality                                                         | Noch nötige Umsetzung                                                                                |
| ------------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Produkte/Varianten, Kunden, Lagerorte | A: Basis-Kontext nach Bedarf         | Objekt-/Varianten-IDs, Einheiten, Identitätslinks und zuständiges Lager                                   | Item-, Party-, Location-Referenzen                                                  | Keine registrierten product/customer/fulfillment-Interpreter; Identitäten ausdrücklich auflösen      |
| Aufträge und Positionen               | A: Basis                             | Auftrags-/Positions-IDs, Mengen, angegebene Beträge/Währung, Termine, Versionen                           | Document/DocumentLine und Kunden-Commitments                                        | Auftragsbeispiel registriert; echtes API-Format, Kontext und Änderungsvertrag prüfen                 |
| Änderungen/Stornierungen              | A: Basis                             | Neue Quellversion, betroffene Positionen und Ursache                                                      | Revision/Stornierung über gemeinsame Services                                       | Unterstützte Reduzierungen/Stornierungen vorhanden; andere Änderungen brauchen Prüfung/Erweiterung   |
| Fulfillment                           | A: Lieferfortschritt erklären        | Tatsächliche Ausführung und Positionsmengen; Routing-Anfrage ist kein abgeschlossener Versand             | Gemeinsame Fulfillment-/Movement-Services                                           | Transport/Interpreter fehlen; Shopify oder Lager als Autorität wählen, keine doppelten Ausgänge      |
| Bestand                               | A: Bestand beobachten                | Lager-Snapshot und autoritative spätere Änderungen                                                        | Angegebene Beobachtung oder Eröffnungs-/Bewegungsevidence nach vereinbartem Vertrag | Verkaufbare Menge von physischem Bestand unterscheiden; fehlende Historie nicht erfinden             |
| Erstattungen/Retouren                 | A: Erstattungen/Retouren prüfen      | Erstattungs-ID, Auftrags-/Positionsbezug, erfolgreiche Transaktion, Ankündigung und tatsächlicher Eingang | Vorhandene Erstattungs-/Retourenservices                                            | Refund-Interpreter vorhanden; physischer Eingang braucht eigene Lagerevidence                        |
| Zahlungen/Auszahlungen                | A: Geldfluss/Abrechnung prüfen       | Transaktionen, Zuordnungen, Gebühren, Auszahlungen und Streitfälle im Umfang                              | Gemeinsame Finanz-/Zahlungsservices                                                 | Shopify Payments/weitere Anbieter benötigen Transport/Interpreter; Refund-Unterstützung genügt nicht |
| Rechnungen/Gutschriften               | A: Berechnung prüfen; weitere Quelle | Tatsächliche Finanzbelege mit angegebenen Steuern und Summen                                              | Finanz-Evidence und unterstützte Finanzservices                                     | Aus zuständigem Rechnungs-/Buchhaltungssystem beziehen; Auftragssumme ist keine Rechnung             |
| Einkauf/Produktion                    | A: Nur bei zusätzlichem ERP-Umfang   | Lieferantenzusagen und Fertigungsrecords bei Bedarf                                                       | Lieferanten-/Domain-Services                                                        | Weitere zuständige Quelle ausdrücklich in die Abdeckung aufnehmen                                    |

## Schritt für Schritt

### Wie und wann du die Daten abholst

Hole nur die für deinen Matrix-Umfang gewählten Datenbereiche ab; die Tabelle verlangt nicht alle
Abfragen für jeden Modus. Im Zuschauerbetrieb reichen freigegebene Lesezugänge.

Die Grundidee: **Bulk für den Erstimport, Webhooks für Änderungen, API-Abfragen zum Abgleich**. Die
Intervalle sind **empfohlene Startwerte**, keine Shopify-Garantie und kein bereits implementierter
Reality-Connector. Passe sie an Datenmenge, API-Limits und die tolerierbare Datenverzögerung an.

| Daten                        | Erstimport                                                                    | Änderungsauslöser / Abfrage                                                                                         | Empfohlener Abgleich                                           |
| ---------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Artikel/Varianten und Kunden | GraphQL Bulk, soweit unterstützt                                              | `products/create`, `products/update`, `products/delete`; `customers/create`, `customers/update`, `customers/delete` | Täglich                                                        |
| Aufträge und Änderungen      | Bulk-Aufträge mit benötigten verknüpften Daten; nur freigegebene Historie     | `orders/create`, `orders/updated`, `orders/cancelled`; fehlende Details nachladen                                   | Alle 5–15 Minuten                                              |
| Fulfillment und Erstattungen | Verknüpfte Auftragsdaten oder separate paginierte Abfragen                    | `fulfillments/create`, `fulfillments/update`, `refunds/create`                                                      | Alle 5–15 Minuten; Retouren-Lebenszyklus bei Bedarf zusätzlich |
| Bestand und Lagerorte        | Aktuelle Mengen je Artikel/Lagerort; paginiert oder unterstützte Bulk-Abfrage | `inventory_levels/update`; betroffene Menge und Lagerkontext nachladen                                              | Aktive Lagerorte alle 15–30 Minuten                            |
| Zahlungen und Auszahlungen   | Auftragstransaktionen; Shopify Payments separat paginiert                     | `order_transactions/create`; `shopifyPaymentsAccount` für Auszahlungen und zugehörige Kontobewegungen abfragen      | Stündlich, zusätzlich täglicher Finanzabgleich                 |

Die Topics stehen in der [Shopify-Webhook-Referenz](https://shopify.dev/docs/api/webhooks/latest).
Sie sind fachlich zu interpretierende Signale, kein Beleg für physischen Wareneingang oder einen
erfolgreichen Geldfluss. Verkaufbarer Bestand ist nicht automatisch physischer Bestand.

[Bulk-Abfragen](https://shopify.dev/docs/apps/build/apis/graphql-admin/bulk-operations/queries) sind
asynchrone Exporte. `bulk_operations/finish` meldet den fertigen Export, keine Geschäftsänderung.
Prüfe die konkrete Abfrage mit der festgelegten API-Version; nicht jede Abfrage unterstützt Bulk.
Sonst paginiert lesen. Auszahlungen brauchen eigenen
[Shopify-Payments-Zugriff](https://shopify.dev/docs/api/admin-graphql/latest/queries/shopifyPaymentsAccount);
andere Zahlungsanbieter eine eigene Quelle. Dieser Plan setzt keinen Auszahlungs-Webhook voraus.

Aktiviere vor dem Erstimport die geprüfte Webhook-Annahme mit dauerhafter Speicherung. Halte die
Importgrenze fest, importiere den Ausgangsstand und spiele gepufferte Änderungen ohne doppelte
Bestandsbuchung nach. Das ist ein Abgleichverfahren, kein atomarer Snapshot aller Objekte.
Fortschritt als dauerhaften Checkpoint (Fortschrittsmarke) erst nach erfolgreicher Übernahme
speichern. Nutze unterstützte Änderungsfilter mit überlappenden Zeitfenstern, dedupliziere nach
Quellidentität/Version und gleiche den vereinbarten Umfang täglich ab (große Shops in Teilmengen).
Speichere Ereignis und nachgeladenes Originalobjekt getrennt. Zeige letzte erfolgreiche Übernahme,
Rückstau und fehlende Berechtigungen; Wiederholungen laufen mit API-Backoff über gemeinsame
Scheduled Jobs.

### Umsetzung

Der gemeinsame Ingest-Weg speichert den Original-Payload als `SourceRecord` und erzeugt einen
`ImportJob`. Erst der registrierte Interpreter ordnet seine Bedeutung zu Evidence und Reality.

1. Bestimme die Fakten, für die der Shop zuständig ist, und die aus ERP, Lager oder Zahlungsanbieter
   kommen. Bewahre Quellidentitäten, ohne Aufträge, Lieferungen oder Erstattungen doppelt zu
   erzeugen.
2. Erfasse originale Auftrags-/Refund-Fixtures sowie Produkte/Varianten und nötigen
   Kunden-/Lagerkontext. `fixtures/shopify/order_10473.json` und `tests/test_shop_refunds.py` zeigen
   die derzeit akzeptierten Formate.
3. Implementiere freigegebene GraphQL-Abfragen und Paginierung/Bulk-Erstimport. Bewahre die
   tatsächliche Originalantwort als Quelle. Nötige Anpassung gehört in den Interpreter; ersetze den
   Original-SourceRecord nicht durch eine verlustbehaftete REST-artige Rekonstruktion.
4. Übergib undurchsichtige `company_party_id`, `customer_party_id` und `location_id`. Löse
   Varianten-/Quell-IDs auf; die SKU-Suche des vorhandenen Beispiels beweist keine globale
   Eindeutigkeit und macht SKU nicht zur Identität. Unbekannte Positionen bleiben erklärbar statt
   still zugeordnet.
5. Verwende `enqueue_source`/`process_import_job` und die registrierten Auftrags-/Refund-Wege. Passe
   den Interpreter geprüft an dein Quellformat an. Ergänze weitere nötige Interpreter über den
   normalen Spec-Ablauf.
6. Prüfe Webhook-Signaturen, doppelte Lieferungen und vertauschte Reihenfolge; lade nötige
   autoritative Objektversionen nach. Nutze dauerhaftes Intake/Retry und regelmäßigen Abgleich über
   gemeinsame Scheduled Jobs, keine Browser-Timer.
7. Teste unterstützte Reduzierungen/Stornierungen, gehaltene Änderungen, fehlende Menge/Preis,
   erfolgreiche beziehungsweise ausstehende Erstattung und unbekannte Positionen. Eine Erstattung
   beweist keinen physischen Wareneingang.
8. Verbinde die zuständigen Lager-/Rechnungs-/Zahlungsquellen für den Gesamtumfang. Prüfe den
   gemeinsamen Abnahmefall vor laufender Übernahme; ausgehende Shop-Aktionen brauchen einen eigenen
   Entwurf und Bestätigungsgrenze.

## Durchgehender Abnahmefall

Der folgende Fall prüft einen erweiterten Umfang. Für den kleinen Zuschauer-Einstieg prüfst du
Auftragsimport, Änderungen, Identitätsauflösung und Replay. Weitere Schritte werden erst
Abnahmekriterien, wenn du die dazugehörige Fragestellung auswählst; bestätigte ausgehende
Operationen prüfst du separat für C.

Dies ist ein **geplanter Abnahmefall für deine Anbindung**, keine Behauptung, dass alle folgenden
Quelltypen bereits implementiert sind. Verwende originale Fixtures aus dem zuständigen System.
Beträge werden in diesen Fixtures ausdrücklich angegeben; die Anleitung berechnet sie nicht aus
Mengen neu.

| Schritt               | Quelldaten/Handlung                                                                                                  | Erwartetes Ergebnis                                                                                             |
| --------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 1. Ausgangslage       | Artikel, Kunde, Lager und Eröffnung mit 10 Stück; offener Auftrag über 10 Stück mit angegebenem Gesamtbetrag 100 EUR | Auftrags-/Positions-Evidence und Zusage; physisch 10, reserviert 0, verfügbar 10                                |
| 2. Zuteilung          | Zuständige Quelle oder bestätigter Reality-Command reserviert 4 Stück                                                | Physisch 10, reserviert 4, verfügbar 6; keine zweite Reservation für dieselbe Zuteilung                         |
| 3. Teillieferung      | Tatsächlicher Ausgang von 4 Stück mit Auftrags-/Positionsbezug                                                       | Physisch 6, reserviert 0, verfügbar 6; geliefert 4, offene Liefermenge 6                                        |
| 4. Rechnung/Zahlung   | Originalrechnung nennt 40 EUR; erfolgreiche Zahlung nennt 40 EUR und Rechnungszuordnung                              | Beide Werte unverändert; finanzielle Zuordnung prüfbar, keine Zahlung aus Auftragsstatus erfunden               |
| 5. Reststornierung    | Neue Auftragsversion storniert die noch offenen 6 Stück                                                              | Ursprüngliche Evidence bleibt; offene Liefermenge 0, historische Ausführung von 4 bleibt erhalten               |
| 6. Retoure/Erstattung | Rückgabe von 2 gelieferten Stück, belegter Wareneingang von 2, Gutschrift 20 EUR und erfolgreiche Rückzahlung 20 EUR | Physisch 8; Ankündigung, Eingang, Gutschrift und Geldbewegung getrennt verknüpft; keine doppelte Refund-Buchung |
| 7. Wiederholung       | Alle Originalversionen erneut liefern; alte Version nach neuer Version liefern                                       | Keine zweite Zusage, Lieferung, Erstattung oder Rücknahme; aktueller Zustand wird nicht zurückgesetzt           |

Für reine Leseanbindungen übernimmt Schritt 2 die bestehende externe Zuteilung. Ein bestätigter
Reality-Command ist eine gesonderte Betriebsart. Verwende nicht beides als zwei unabhängige
Reservierungen. Ein Retoureneingang öffnet die bereits erfüllte Lieferzusage nicht automatisch neu.

Ergänze einen Einkaufsfall: Lieferant verspricht 5 Stück, liefert zunächst 3 und später 2. Offene
Eingangsmenge: 5 → 2 → 0; Bestand steigt nur bei tatsächlichen Eingängen. Wenn Einkauf außerhalb
dieser Quelle liegt, stammt der Fall aus der im Umfang benannten weiteren Quelle.

## Prüfen und betreiben

Prüfe pro Quelltyp Original-Payload, stabile Identität, Version, Tenant, Herkunft und tatsächlichen
fachlichen Ausgang. Für den obigen Fall stimmen Stückzahlen und angegebene Geldbeträge mit der
zuständigen Quelle überein. Melde fehlende beziehungsweise nicht interpretierte Records
ausdrücklich; eine erfolgreiche HTTP-Antwort ist kein Abnahmenachweis.

Teste zusätzlich unbekannte Artikel/Partner, fehlende Mengen/Preise, Einheiten/Währungen, Sperren,
Mehrdeutigkeit, Löschung/Archivierung, Teilfehler, abgelaufene Rechte, API-Limits, Wiederholung nach
Ausfall und fremde Tenant-/Unternehmens-IDs. Eine nicht unterstützte Änderung bleibt im Review statt
still überschrieben zu werden. Abgleich darf keine erfundene Korrekturbewegung erzeugen.

Plane Aktualitätsziel, Übernahmerückstand, Fehler-/Review-Zuständigkeit, Alarmierung, regelmäßigen
Mengen-/Betragsabgleich und Wiederanlauf. Lies `docs/features/scheduled-jobs.md` vor wiederkehrendem
Intake. Für Vollständigkeit gilt die
[gemeinsame Abnahmeliste](./connector-contract.md#vollständigkeit-und-abnahme).

## Referenzen und nächste Schritte

Vendor-Referenzen wurden am 2026-10-03 geprüft. Verwende die zur Installation passende Version;
diese Links sind keine Implementierungszusage.

- [Shopify bulk retrieval](https://shopify.dev/docs/apps/build/apis/graphql-admin/bulk-operations/queries)
- [Shopify webhook verification](https://shopify.dev/docs/apps/build/webhooks/verify-deliveries)
- [Shopify order/fulfillment concepts](https://shopify.dev/docs/apps/build/orders-fulfillment/order-management-apps)

Repository-Vorlagen: `packages/reality-core/tests/test_source_ingestion.py`,
`test_shopify_and_explain.py`, `test_shop_order_changes.py`, `test_shop_refunds.py` und
`test_shop_line_gaps.py`. Sie beweisen ihre vorhandenen Services, nicht einen fertigen
Shopify-Live-Connector.

[Von Quelldaten zu Reality](./connector-contract.md) · [Erstpilot](./parallel-test.md) ·
[Interpreter entwickeln](../development/connectors.md)
