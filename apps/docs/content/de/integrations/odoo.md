# Odoo anbinden

[Welche Daten brauche ich zuerst? Beispiel-ERP Schritt für Schritt](./example-erp) zeigt einen
kleinen Einstieg und seine Ausbaustufen.

Diese Anleitung führt vom fachlichen Umfang bis zur Abnahme. Sie trennt vorhandene Vorlagen von noch
zu entwickelnden Teilen.

## Was vollständig bedeutet

Vollständigkeit gilt **für die gewählte Betriebsart und Fragestellung**. Die folgenden Bereiche
beschreiben den möglichen Gesamtumfang, nicht den Pflichtumfang eines kleinen Zuschauer-Einstiegs.

Lege die Abdeckung nach installierten Modulen und Unternehmen fest: Verkauf, Einkauf, Lager und
Buchhaltung bilden die Basis, soweit genutzt. Fertigung/Stückliste, Projekte/Dienstleistungen,
Abonnements, Chargen/Seriennummern, Preise, Kostenrechnung und eigene Module brauchen ausdrücklich
eigene Abdeckung. „100 %“ bedeutet geprüfte vereinbarte Unternehmen/Abläufe, nicht den Import jedes
Odoo-Modells.

## Betriebsarten

### Nur lesen: Odoo zuschauen

**Odoo führt die Abläufe; Reality liest und erklärt.** Der Integration werden nur die nötigen
Leserechte für die ausgewählten Unternehmen und Datenbereiche gegeben. Originale
`SourceRecord`-Payloads werden über Interpreter in lokale Evidence- und Reality-Datensätze
überführt. Reality schreibt in dieser Betriebsart nichts nach Odoo zurück und stößt dort keine
Operation an.

Für einen kleinen Einstieg reichen Aufträge, Positionen, relevante Änderungen und die erforderlichen
Identitäten. Bestands-, Liefer-, Rechnungs- oder Zahlungsdaten brauchst du erst, wenn entsprechende
Beobachtungen und Ausnahmen erklärt werden sollen. Alle installierten Odoo-Module zu übernehmen ist
keine Voraussetzung fürs Zuschauen.

**Beispiel:** Reality übernimmt einen Auftrag über 10 Stück und zeigt die angegebene Zusage. Soll es
erklären, dass noch 6 Stück zu liefern sind, braucht es zusätzlich die belegte Ausführung über 4
Stück. Ohne diese Quelle bleibt der Lieferfortschritt unbekannt; Reality fordert keinen Versand an.
Bestehende Odoo-Automatiken können die Abläufe weiterhin steuern.

### Reality steuert, Odoo führt aus

**Reality gibt vor, was Odoo wann tun soll.** Beispielsweise „Auftrag X mit diesen Positionen zum
Versand freigeben“ oder „Rechnung für Auftrag X anlegen“. Odoo verarbeitet die angeforderte
Operation, führt seine fachlichen und technischen Prüfungen aus und meldet Ergebnis und entstandene
Belege zurück. Das sind fachliche Beispiele, keine bereits implementierten Command-Namen oder
geprüften API-Aufrufe. Unterstützte Methoden, Rechte und Abläufe müssen für die konkrete Version und
installierten Module geprüft werden.

Die Zuständigkeit wird je Entscheidung übertragen. Odoo kann weiterhin Stammdatenpflege,
Auftragserfassung, Kommissionierung, tatsächlichen Versand, rechtsgültige Rechnungserstellung und
Buchhaltung übernehmen. Für übertragene Entscheidungen werden konkurrierende Odoo-Automatiken vor
Aktivierung geprüft und abgeschaltet oder koordiniert. „Passiv ausführen“ bedeutet hier keine
unabhängige Steuerung dieser Entscheidungen; technische Prüfungen und Lagerarbeit bleiben aktiv.

**Beispiel:** Reality schlägt für Auftrag X eine Versandfreigabe über 4 Stück vor. Mutierende
Agent-/Chat-Commands brauchen menschliche Bestätigung. Der separat geprüfte Adapter fordert die
Operation mit Idempotenz- und Korrelationsschlüssel an. Erst tatsächliche Ausführungsbelege lassen
Reality die Erfüllung erfassen; Anfrage, geplantes Picking oder Label allein beweisen keinen
physischen Versand. Ein Timeout bleibt sichtbar und ein Retry darf keinen zweiten Vorgang erzeugen.

Diese Ausführung ist **nicht durch die Connector-Shell implementiert**. Sie braucht einen separat
geprüften ausgehenden Adapter mit dauerhaftem Rückweg, Wiederholungen und Abgleich nach dem
gemeinsamen Scheduling-Vertrag. Automatische Regeln benötigen einen eigenen ausdrücklich geprüften
Ausführungsvertrag. Beginne mit Lesen und übertrage danach eine begrenzte Entscheidung; Einkauf oder
Fertigung sind dafür nicht pauschal Pflicht.

## Bevor du beginnst

Bestimme Odoo-Version, Hosting/Edition, Module, Unternehmen und Record-/Feldrechte des eigenen
Integrationsbenutzers. Für Odoo 19 JSON-2 beschreibt die offizielle Dokumentation
`/json/2/<model>/<method>`, Bearer-API-Keys und datenbankspezifische Modelle/Felder unter `/doc`;
prüfe die veröffentlichten Tarifbedingungen für deine Bereitstellung. Andere Versionen brauchen
einen eigenen API-Vertrag. Prüfe tatsächliche Felder und Beziehungen statt identische Installationen
vorauszusetzen. Lies den [Von Quelldaten zu Reality](./connector-contract).

## Aktueller Implementierungsstand

Die Shell `odoo` in `packages/reality-core/config/connector_catalog.yaml` nennt `sale.order`,
`purchase.order`, `product.product`, `res.partner` und `account.move`. In `SOURCE_INTERPRETERS` in
`services/core.py` ist kein Odoo-Paar registriert. Transport und alle Objekt-Interpreter müssen
implementiert werden. Die folgenden Positions-/Lager-/Zahlungsmodelle sind eine Prüfliste für die
installierte Datenbank, keine registrierten Reality-Capabilities oder garantierten API-Schemas.

## Abdeckungsmatrix

**Basis fürs Zuschauen:** Aufträge/Positionen, relevante Änderungen sowie nötige Identitäten und
Kontext. Vorhandene Reality-Stammdaten können Kontext liefern; ein vollständiger Stammdatenimport
ist nicht automatisch erforderlich. Diese Matrix ist **keine Pflichtliste**. Weitere Daten werden
für die genannte Fragestellung benötigt. Für die Ausführung ergänzt du nur die Daten und den
Command-Rückweg für die übernommenen Entscheidungen.

| Quellbereich                          | Betriebsart und Bedarf                                          | Zu prüfende Modelle/Records                                                                   | Fachlicher Zweck in Reality                                        | Noch nötige Umsetzung                                                                                           |
| ------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Stammdatenidentitäten                 | Lesen: Basis-Kontext; Ausführung: Entscheidungskontext          | `product.product`, `res.partner`, Unternehmen, Einheiten, Lager-/Lagerortbeziehungen          | Item, Party, Location und Quellreferenzen                          | Identitäts-Interpreter; Unternehmensgrenze und gemeinsame Partner klären                                        |
| Verkauf                               | Lesen: Basis; Ausführung: Auftragsentscheidungen                | `sale.order` und zugehörige Positionen, Termine/Revisionen/Stornierung                        | Document/DocumentLine und Kunden-Commitments                       | `sale.order`-Interpreter; Positions-/Versionsvertrag                                                            |
| Einkauf                               | Lesen: Einkauf beobachten; Ausführung: Einkauf steuern          | `purchase.order`, Positionen und Eingänge                                                     | Lieferanten-Commitments und Eingangs-Evidence                      | `purchase.order` und Wareneingangsinterpretation                                                                |
| Bestand                               | Lesen: Bestand beobachten; Ausführung: Bestandsentscheidungen   | Lagerortmengen, ausgeführte `stock.move`-/Positionsrecords und Umlagerungen                   | Eröffnungs-/Eingangs-/Ausgangs-/Umlagerungs-Movements              | Installierte Felder, tatsächliche Mengen, Einheiten und Stichtag prüfen; geplante Bewegung ist keine Ausführung |
| Reservierung/Lieferung                | Lesen: Lieferfortschritt; Ausführung: Versand/Zuteilung steuern | Picking-/Positionszuteilungen und ausgeführte Vorgänge                                        | Reservations und Fulfillment-Verknüpfungen                         | Zuteilung, geplante und tatsächliche Menge unterscheiden                                                        |
| Finanzbelege                          | Lesen: Berechnung prüfen; Ausführung: Rechnungen anfordern      | `account.move` mit Positionen, Belegart, angegebenen Beträgen/Steuern/Währung/Fristen         | Finanz-Evidence und gemeinsame Finanzservices                      | Rechnung, Eingangsrechnung, Gutschrift und Journal klassifizieren; keine pauschale Rechnungsinterpretation      |
| Zahlung/Settlement                    | Lesen: Geldfluss prüfen; Ausführung: Zahlungs-/Kreditfreigabe   | Installierte Zahlungs-/Abgleichrecords und Rechnungsbezüge                                    | Gemeinsame Zahlungs-/Settlement-Services                           | Zahlungs-/Zuordnungs-Interpreter; gebuchte Rechnung beweist keine Zahlung                                       |
| Retouren                              | Beide: Nur für Retourenfragen/-entscheidungen                   | Rückführende Lagervorgänge, Gutschriften und Geldrückgabe                                     | Retoureneingang und Finanzservices                                 | Physische und finanzielle Identität getrennt halten; Originalbezüge bewahren                                    |
| Weitere Module                        | Beide: Nur bei genutztem Modul                                  | Installierte Fertigung/Stückliste, Chargen/Seriennummern, Dienste/Abos, Preise/Kostenrechnung | Vorhandene Domain-Fähigkeit oder separat spezifizierte Erweiterung | Jede Abhängigkeit abgrenzen und testen; keine pauschale Basisabdeckung                                          |
| Ausgehende Commands und Rückmeldungen | Nur Ausführung: jede übertragene Operation                      | Bestätigte Anfrage, Idempotenz-/Korrelationsschlüssel, Ergebnis und Ausführungsbelege         | Anfrage und tatsächliche Ausführung getrennt nachweisen            | Separat geprüfter Adapter und Scheduling-Vertrag; Lesen braucht keine Schreibrechte                             |

## Schritt für Schritt

Setze die folgenden Schritte nur für deine ausgewählten Quellbereiche um. Der kleine Lese-Einstieg
verlangt keinen vollständigen Lager-, Einkaufs- oder Finanzimport. Schreibaktionen gehören
ausschließlich zur separat geprüften Ausführung.

Der gemeinsame Ingest-Weg speichert den Original-Payload als `SourceRecord` und erzeugt einen
`ImportJob`. Erst der registrierte Interpreter ordnet seine Bedeutung zu Evidence und Reality.

1. Halte Unternehmens-, Modul- und Quellenumfang fest. Ordne Odoo-Unternehmen Reality-Tenants zu und
   kläre gemeinsame Partner/Artikel; impliziter Unternehmenskontext ist keine Tenant-Freigabe.
2. Prüfe Modelle/Felder dieser Datenbank. Erfasse echte
   Stammdaten-/Auftrags-/Positions-/Lager-/Finanz-Fixtures mit Beziehungen. Notiere originale
   Quell-ID, Unternehmen und Versions-/Änderungsidentität.
3. Implementiere den zur Version passenden authentifizierten Adapter. Erfasse Positionen zusätzlich
   zum Kopf; Beziehungs-IDs allein liefern keine Mengen, Beträge oder Ausführungsevidence. Bewahre
   Originalwerte und Umschläge.
4. Übergib über `enqueue_source`/`process_import_job`, implementiere tenant-begrenzte Interpretation
   und registriere jedes Quellpaar. Erweitere die Shell nur um nachgewiesene weitere Quelltypen.
   Nutze Importtests für unbekannte/gehaltene/fehlerhafte Ergebnisse.
5. Definiere den Stichtag mit offenen Verkaufs-/Einkaufszusagen, Bestand und offenen
   Finanzpositionen. Klassifiziere historische, geplante, reservierte und ausgeführte Vorgänge vor
   Folgeänderungen; zähle Picking und Bewegungspositionen nicht doppelt.
6. Lies Änderungen mit einem für diese Installation belegten Cursor, stabiler Sortierung,
   Überlappung und Abgleich. Bewahre Archivierungs-/Löschsignale oder dokumentiere die Untersuchung
   fehlender Records. Polling läuft über gemeinsame Scheduled Jobs, sofern kein gesondert belegter
   Event-Adapter existiert.
7. Übertrage Rechnung/Gutschrift/Zahlung/Zuordnung über gemeinsame Finanzservices. Bewahre
   angegebene Preise, Steuern und Summen; prüfe Einheiten/Währungen statt empfangene Beträge neu zu
   berechnen.
8. Prüfe den Abnahmefall je Unternehmen und relevantem Modul, einschließlich Unternehmensisolation
   und eingeschränkter Records. Aktiviere laufende Übernahme nach dem Abgleich; Odoo-Schreibaktionen
   bleiben separat freigegebene Fähigkeiten.

## Durchgehender Abnahmefall

Dieser Fall prüft einen erweiterten Umfang. Für den kleinen Lese-Einstieg prüfst du Auftragsimport,
Änderungen, Identitätsauflösung und Replay. Weitere Schritte gelten erst für die ausgewählte
Fragestellung; ausgehende Commands und Rückmeldungen prüfst du zusätzlich nur bei Ausführung.

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
[gemeinsame Abnahmeliste](./connector-contract#vollständigkeit-und-abnahme).

## Referenzen und nächste Schritte

Vendor-Referenzen wurden am 2026-10-03 geprüft. Verwende die zur Installation passende Version;
diese Links sind keine Implementierungszusage.

- [Odoo 19 external JSON-2 API](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)

Repository-Vorlagen: `packages/reality-core/tests/test_source_ingestion.py`,
`test_shopify_and_explain.py`, `test_shop_order_changes.py`, `test_shop_refunds.py` und
`test_shop_line_gaps.py`. Sie beweisen ihre vorhandenen Services, nicht einen fertigen
Odoo-Live-Connector.

[Von Quelldaten zu Reality](./connector-contract) · [Erstpilot](./parallel-test) ·
[Interpreter entwickeln](../development/connectors)
