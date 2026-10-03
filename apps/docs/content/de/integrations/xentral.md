# Xentral anbinden

[Welche Daten brauche ich zuerst? Beispiel-ERP Schritt für Schritt](./example-erp) zeigt einen
kleinen Einstieg und seine Ausbaustufen.

Diese Anleitung führt vom fachlichen Umfang bis zur Abnahme. Sie trennt vorhandene Vorlagen von noch
zu entwickelnden Teilen.

## Was vollständig bedeutet

Vollständigkeit gilt **für die gewählte Betriebsart und Fragestellung**. Der kleine
Zuschauer-Einstieg braucht nicht die gesamte Matrix. Die folgenden Bereiche beschreiben den
möglichen Gesamtumfang, den du schrittweise erweitern kannst.

Binde Verkauf, Einkauf, Lager und Finanzen für einen vereinbarten
Xentral-Unternehmens-/Projektumfang an. Retouren, Umlagerungen und Korrekturen gehören dazu, wenn
sie genutzt werden. Produktion, Stücklisten, Chargen/Seriennummern, Preiskonditionen und weitere
Module kommen auf das Umfangsblatt, sobald Geschäftsabläufe davon abhängen; das Basisbeispiel
beweist diese Module nicht. „100 %“ bedeutet geprüfte Abdeckung aller vereinbarten Abläufe oder eine
ausdrücklich benannte weitere Quelle, nicht jedes Xentral-Feld.

## Betriebsarten

### B) Xentral zuschauen

**Xentral führt die ERP-Abläufe; Reality schaut zu und erklärt.** Der Adapter greift nur lesend auf
Xentral zu. Er übernimmt Artikel, Geschäftspartner, Aufträge, Bestellungen, Bestand/Lagerausführung,
Rechnungen, Gutschriften, Zahlungen und Retouren im vereinbarten Umfang. Jeder originale
`SourceRecord` wird über gemeinsame Services in lokale Evidence- und Reality-Datensätze
interpretiert; diese Betriebsart ändert nichts in Xentral.

Xentral und benannte weitere Quellen verantworten Zuteilung, Freigabe, Versand, Berechnung und
Finanzen. Reality erklärt unterstützte Bestände, offene Mengen, Verpflichtungen und Ausnahmen aus
den übernommenen Fakten. Reality trifft keine eigenen operativen Entscheidungen. Quellseitige
Belegstatus bleiben als Quellangaben erhalten; Liefer-, Reservierungs- und Zahlungszustand werden
aus Reality-Datensätzen abgeleitet und nicht als solche Statusfelder an Documents ergänzt.

**Beispiel:** Xentral erfasst einen Auftrag über 10 Stück, einen tatsächlichen Abgang von 4 und eine
Rechnung mit ihrem angegebenen Betrag. Reality verknüpft diese Fakten und erklärt den verbleibenden
Liefer- und Berechnungsbedarf, sobald die nötigen Interpreter umgesetzt sind. Ein angelegter
Lieferschein allein beweist noch keinen Versand. Eine erkannte Abweichung korrigiert Xentral nicht
automatisch.

Anders als bei [A) Shopify zuschauen](./shopify#a-shopify-zuschauen) kann dieser Umfang auch
Lieferantenzusagen, Wareneingänge und rechtsgültige Finanzbelege aus dem ERP enthalten. Nutze die
Abholtabelle weiter unten und prüfe jeden Quellbereich in der Abdeckungsmatrix. Das sind
Zielverträge für den Betrieb, keine Behauptung einer bereits implementierten Xentral-Anbindung.

### C) Reality entscheidet, Xentral führt aus

**Reality verantwortet die vereinbarten operativen Entscheidungen; Xentral führt sie aus.** Nutze
zuerst den Leseweg aus B und ergänze danach separat geprüfte ausgehende Operationen. Xentral kann
die Oberfläche für Artikel-/Adresspflege, Auftragserfassung, Lagerausführung, Labels, rechtsgültige
Rechnungserstellung und Buchhaltungsexport bleiben. Die Zuständigkeit gilt je Entscheidung, nicht
pauschal für jedes Feld einer Anwendung.

**Reality steuert, Xentral führt angeforderte Vorgänge aus.** „Passiv“ bezieht sich hier auf die
übertragenen Entscheidungen: Xentral stößt diese Vorgänge nicht unabhängig an. Die Verarbeitung der
Commands, technische Prüfungen und die Lagerabläufe bleiben aktiv.

**Konkret heißt „führt aus“: Reality gibt das Command, was Xentral wann tun soll.** Zum Beispiel:
„Auftrag X mit diesen Positionen zum Versand freigeben“ oder „Rechnung für Auftrag X anlegen“.
Xentral verarbeitet die angeforderte Operation und meldet Erfolg, Fehler und entstandene Belege
zurück. Das sind fachliche Beispiele, keine bereits implementierten Command-Namen oder geprüften
API-Aufrufe. Eine Versandfreigabe steuert den Lagerablauf; den physischen Versand erledigt weiterhin
das Lager.

| Bereich                                                             | Verantwortliches System                                                  |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Stammdaten und ursprüngliche Auftragserfassung                      | Xentral oder die benannte ursprüngliche Quelle                           |
| Zuteilung, Kredit-/Zahlungsfreigabe und Auswahl für Versand         | Reality, für ausdrücklich übertragene Entscheidungen                     |
| Kommissionieren, Verpacken, Labels und tatsächliche Lagerausführung | Xentral / das zuständige Lager                                           |
| Entscheidung, eine Rechnung anzufordern                             | Reality, wenn im geprüften Umfang vereinbart                             |
| Rechtsgültige Rechnungsbeträge, Steuern, PDF und Buchhaltungsexport | Xentral / zuständige Buchhaltungsquelle; angegebene Werte übernehmen     |
| Zahlungs- und Lagerfakten                                           | Tatsächliche Ausführungsquelle; kommen als unveränderliche Belege zurück |

**Beispiel:** Ein Auftrag über 10 Stück kommt aus Xentral an. Reality schlägt die Freigabe von 4
Stück vor, nachdem gemeinsame Services die relevanten Bedingungen geprüft haben. Eine Person
bestätigt einen mutierenden Agent-/Chat-Command ausdrücklich. Ein separat entworfener ausgehender
Adapter fordert die unterstützte Xentral-Operation mit Idempotenzschlüssel an. Xentral führt
Kommissionierung und Versand aus. Erst wenn die zuständige Quelle die tatsächliche Ausführung für
diese 4 Stück belegt, erfasst Reality die Erfüllung; Anfrage, angelegter Lieferschein oder
Trackingnummer allein reichen nicht. Eine vereinbarte Rechnungsanforderung folgt demselben Muster
aus Anfrage, Ausführung und Beleg. Timeout oder widersprüchliche Rückmeldung bleiben zur Prüfung
sichtbar.

Übertrage jeweils eine Entscheidung. Prüfe vor der Aktivierung konkurrierende Xentral-Automatiken
für genau diese Entscheidung und schalte sie ab oder koordiniere sie. Andere Zuständigkeiten bleiben
bei Xentral. Halte Bestätigung, Korrelation, Wiederholungen und Abgleich fest; ein Retry darf keinen
zweiten Versand oder eine zweite Rechnung erzeugen. Mutierende Agent-/Chat-Aufrufe brauchen
menschliche Bestätigung. Automatische Regeln benötigen einen eigenen ausdrücklich geprüften
Ausführungsvertrag; eine Regel ersetzt diese Bestätigungsgrenze nicht.

Diese Betriebsart ist **durch die Connector-Shell nicht implementiert**. Ein ausgehender
Ausgangskorb mit Handlern für externe Effekte braucht ein separat geprüftes Scheduling-Design. Der
vorhandene Leseweg und die vorgeschlagenen Abfrageintervalle implementieren keine ausgehende
Ausführung. Starte in B, prüfe die Belegkette und übertrage danach eine eng begrenzte Entscheidung
unter diesem Design.

## Bevor du beginnst

Nutze eine Testinstanz oder einen freigegebenen Export. Bestimme die vorhandenen
API-/Resource-Versionen und prüfe Anmeldung und Rechte dieser Instanz. Xentral dokumentiert Artikel
und Aufträge über unterschiedliche API-Versionen; ein Versionspräfix gilt nicht automatisch für alle
Objekte. Halte Unternehmens-/Projektgrenzen, Lagerorte, Einheiten, Währungen, Zeitzonen, Paginierung
und Sichtbarkeit von Änderungen/Löschungen fest. Zugangsdaten gehören in die geheime
Adapter-Konfiguration, nicht in Payloads oder Fixtures. Lies den
[Von Quelldaten zu Reality](./connector-contract).

## Aktueller Implementierungsstand

Die Shell `xentral` in `packages/reality-core/config/connector_catalog.yaml` nennt `order`,
`purchase_order`, `article`, `contact` und `payment`. In `SOURCE_INTERPRETERS` in `services/core.py`
ist kein Xentral-Paar registriert. Vendor-Transport, Objekt-Interpreter, Identitätsauflösung und
Produktionsnachweise fehlen. Weitere benötigte Quelltypen für Rechnungen, Bewegungen oder andere
Bereiche brauchen ebenfalls geprüfte Katalog-/Capability-Ergänzungen. Ein gespeicherter Payload ist
noch keine fachliche Interpretation.

## Abdeckungsmatrix

**Kleiner Einstieg in B: Aufträge nachvollziehen.** Dafür brauchst du Aufträge und Positionen,
relevante Änderungen/Stornierungen sowie die zur Interpretation nötigen Artikel-, Partner- und
Quellidentitäten. Kontext kann aus vorhandenen Reality-Stammdaten kommen; ein vollständiger
Stammdatenimport ist dafür nicht automatisch nötig. Versand, Zahlungen, Einkauf und Retouren ergänzt
du erst für entsprechende Fragestellungen.

Diese Matrix ist **keine Pflichtliste für jeden Zuschauerbetrieb**. „Basis“ gilt für den genannten
Einstieg; weitere Zeilen werden erst für das jeweilige Ziel benötigt. Ohne Ausführungsdaten kannst
du beispielsweise einen Auftrag anzeigen, aber keine verlässlich offene Liefermenge behaupten.

Für C gilt ebenfalls der gewählte Umfang: Wer nur Rechnungserstellung steuert, muss nicht zugleich
Einkauf oder Produktion anbinden. Benötigt werden die Daten für die übernommenen Entscheidungen
sowie der geprüfte Command-Rückweg und die Ergebnisbelege.

| Quellbereich                          | Betriebsart und Bedarf                                        | Was übernommen wird                                                                   | Fachlicher Zweck in Reality                                                       | Noch nötige Umsetzung                                                                         |
| ------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Artikel, Kontakte, Lagerorte          | B: Basis-Kontext; C: Entscheidungskontext                     | Stabile IDs, Varianten, Einheiten, Partnerrollen und Lageridentität                   | Item, Party, Location und Quellreferenzen                                         | Stammdaten-Transport/-Interpreter; Mehrdeutigkeit ausdrücklich behandeln                      |
| Aufträge und Positionen               | B: Basis; C: auftragsbezogene Entscheidungen                  | IDs, angegebene Mengen/Beträge/Termine, Revisionen, Stornierungen                     | Document/DocumentLine und Kunden-Commitments                                      | `order`-Interpreter und Änderungsvertrag                                                      |
| Bestellungen und Wareneingänge        | B: Einkauf beobachten; C: Einkauf steuern                     | Lieferantenzusagen, Positions-IDs, erwartete und tatsächliche Eingänge                | Lieferanten-Commitments und Eingangs-Movements                                    | `purchase_order` sowie Eingangs-Transport/-Interpretation                                     |
| Bestand                               | B: Bestand beobachten; C: Bestandsentscheidungen              | Stichtagsmengen pro Lager; spätere Bewegungen, Umlagerungen, Korrekturen              | Eröffnungs- und weitere Bestandsevidence/Movements                                | Quelltypen, Stichtag und Bewegungs-Interpreter                                                |
| Reservierungen und Lieferungen        | B: Zuteilung/Lieferung erklären; C: Versand/Zuteilung steuern | Zuteilungsidentität, tatsächliche Lieferpositionen, Rücknahmen                        | Reservations und Fulfillment-Movements                                            | Zuteilung und Ausführung getrennt interpretieren; keine Lieferung aus Auftragsstatus erfinden |
| Rechnungen und Gutschriften           | B: Berechnung prüfen; C: Rechnungen anfordern                 | Verkaufs-/Einkaufsrichtung, Positionsbeträge, Steuern, Währung, Fälligkeit            | Finanz-Evidence und passende gemeinsame Finanzservices                            | Finanz-Quelltypen und Interpreter; keine Ledger-Regel im Transport                            |
| Zahlungen und Zuordnungen             | B: Geldfluss prüfen; C: Zahlungs-/Kreditfreigabe              | Transaktions-IDs, Beträge, Währung, Rechnungsbezug                                    | Gemeinsamer Zahlungs-/Settlement-Weg; LedgerEntry nur nach dessen Buchungsvertrag | `payment`-Interpreter und Zuordnungssemantik                                                  |
| Retouren und Erstattungen             | B: Retouren prüfen; C: entsprechende Entscheidungen           | Ankündigung, Eingang, Gutschrift und Geldrückgabe getrennt                            | Retouren- und Finanzservices                                                      | Unterstützte Quelltypen und Auflösungslinks                                                   |
| Weitere Module                        | B/C: Nur bei genutztem Modul                                  | Produktion/Stückliste, Chargen/Seriennummern, Preise oder weitere vereinbarte Records | Vorhandene Domain-Services oder separat spezifizierte Erweiterung                 | Jedes Modul bewerten; Verkauf/Bestand allein deckt es nicht ab                                |
| Ausgehende Commands und Rückmeldungen | Nur C: für jede übertragene Operation                         | Bestätigte Anfrage, Idempotenz-/Korrelationsschlüssel, Ergebnis und Ausführungsbeleg  | Angeforderte Operation von nachgewiesener Ausführung trennen                      | Separat geprüftes Adapter-/Scheduling-Design; B benötigt keine Schreibrechte                  |

## Schritt für Schritt

### Wie und wann du die Daten abholst

Hole nur die für deinen Matrix-Umfang gewählten Datenbereiche ab; die Tabelle verlangt nicht alle
Abfragen für jeden Modus. Im Zuschauerbetrieb reichen freigegebene Lesezugänge.

Beginne mit **paginierten API-Abfragen** und ergänze geprüfte Webhooks je Datenbereich. Setze keine
Bulk-API wie bei Shopify voraus. Die Intervalle sind **empfohlene Startwerte**, keine
Herstellergarantie und kein bereits implementierter Reality-Connector. Prüfe Ressourcen, Filter,
Berechtigungen und abonnierbare Ereignisse in der konkreten Installation.

| Daten                                               | Erstimport                                                 | Laufende Übernahme                                                              | Empfohlenes Intervall                                     |
| --------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Artikel, Kontakte und Lagerorte                     | Benötigte Stammdaten seitenweise lesen                     | Unterstützte Änderungsabfragen, sonst paginierter Vergleich                     | Aktive Stammdaten stündlich; umfassender Abgleich täglich |
| Aufträge und Bestellungen                           | Offene Vorgänge mit Positionen; benötigte Historie separat | Unterstützte Änderungsabfragen; verfügbare Webhooks erst nach Prüfung           | Alle 5–15 Minuten                                         |
| Bestand und Bewegungen                              | Anfangsbestand je Lagerort zum vereinbarten Stichtag       | `/api/v3/stockMovements` lesen; aktuellen Bestand regelmäßig vergleichen        | Alle 5–15 Minuten; täglicher Abgleich                     |
| Lieferung und Lagerausführung                       | Lieferscheine, Sendungen und benötigte Ausführungsbelege   | `salesOrder.dispatched`, `deliveryNote.created`; danach Objektdetails nachladen | Auf Ereignis reagieren; alle 5–15 Minuten abgleichen      |
| Rechnungen, Gutschriften, Zahlungen und Zuordnungen | Offene Posten und vereinbarte Originalbelege               | Paginierte Abfragen; geprüfte Ressourcen-Ereignisse ergänzen, falls verfügbar   | Alle 15–60 Minuten; täglicher Finanzabgleich              |
| Retouren und Zusatzmodule                           | Jede vereinbarte Quelle separat lesen                      | Ressourcenbezogene Abfragen/Ereignisse; Abdeckung vor Aktivierung nachweisen    | Start mit 15–60 Minuten; bei operativem Bedarf kürzer     |

Xentral dokumentiert [Bestandsabfragen](https://developer.xentral.com/docs/read-stock) und
[Bestandsbewegungen](https://developer.xentral.com/reference/getapi-v3-stockmovements). Trenne
Anfangsbestand von anschließenden Bewegungen. Erfinde keine Bewegungshistorie aus
Snapshot-Differenzen. Nutze Änderungsfilter nur, wenn der jeweilige Endpunkt sie unterstützt; sonst
paginiert vergleichen und Quellidentitäten/Versionen behalten.

Die [Fulfillment-Anleitung](https://developer.xentral.com/docs/fulfillment) beschreibt die beiden
genannten Webhooks und Detailabfragen wie `/api/v1/salesOrders/{id}` und
`/api/v3/deliveryNotes/{id}`. `salesOrder.dispatched` startet die Abwicklung und belegt keinen
physischen Versand. Lieferscheinstatus `sent` beschreibt die Dokumentkommunikation. Auch angelegte
Trackingdaten allein beweisen keine Übergabe an den Paketdienst. Dafür übernimmst du den
Ausführungsbeleg der verantwortlichen Lagerquelle.

Puffere verfügbare Ereignisse dauerhaft vor dem Erstimport. Halte den Stichtag fest und spiele nach
den Anfangsdaten spätere Versionen nach; gleiche Änderungen während des seitenweisen Lesens ab. Ein
dauerhafter Checkpoint (Fortschrittsmarke) wird erst nach erfolgreicher Übernahme fortgeschrieben.
Nutze überlappende Änderungsfenster, soweit unterstützt, idempotentes Nachspielen, begrenzte
Wiederholungen und gemeinsame Scheduled Jobs mit API-Backoff. Gleiche die vereinbarten Identitäten
und Mengen täglich ab; zeige letzte erfolgreiche Übernahme und Rückstau. Fehlende Ereignisse oder
Filter brauchen eine dokumentierte Abfragestrategie, keine Behauptung einer vollständigen
Live-Anbindung.

### Umsetzung

Der gemeinsame Ingest-Weg speichert den Original-Payload als `SourceRecord` und erzeugt einen
`ImportJob`. Erst der registrierte Interpreter ordnet seine Bedeutung zu Evidence und Reality.

1. Vereinbare eine Quellen-Zuständigkeitsmatrix. Liefert Shopify denselben Verkauf, wähle eine
   Auftragsautorität und bewahre beide Quellidentitäten, ohne zwei Zusagen zu erzeugen.
2. Erfasse echte Fixtures für Artikel, Kontakt, Lagerort und Auftrag. Notiere Objekt-ID,
   Positions-ID, Version und Xentral-Projekt-/Unternehmensgrenze. Bewahre Originalantworten
   verlustfrei auf.
3. Implementiere den Adapter über `services/core.py::enqueue_source` mit
   `(source_system, source_type)`, Original-Payload und Kontext. Folge `process_import_job` und dem
   gemeinsamen Quellen-Lifecycle. Ohne Interpreter bleibt der Import sichtbar `unmapped`.
4. Implementiere und registriere jeden nötigen Interpreter. Beginne mit Stammdatenidentitäten und
   `order`, dann Einkauf, Lager/Lieferung und Finanzen. `_shopify_interpretation` ist eine Vorlage
   für Version/Herkunft, kein Xentral-Feldmapping.
5. Wähle einen Stichtag. Übernimm Eröffnungsbestand und offene Finanzpositionen über unterstützte
   Services; verarbeite spätere Bewegungen einmal. Addiere nicht die gesamte frühere
   Bewegungshistorie zum Eröffnungsbestand.
6. Implementiere Änderungen mit dauerhaftem Checkpoint, überlappenden Reads und idempotenter
   Wiederholung. Prüfe, ob diese Installation geeignete Webhooks bietet; andernfalls nutze Polling
   über gemeinsame Scheduled Jobs. Setze keinen undokumentierten Webhook voraus.
7. Teste Auftragsrevision, Lieferrücknahme, Gutschrift und Zahlungszuordnung getrennt. Bewahre
   angegebene Beträge und historische Evidence. Verwende Finanzservices, statt Buchungen aus
   Belegstatus zu berechnen.
8. Gleiche Quellidentitäten und fachliche Werte ab und aktiviere erst dann laufende Übernahme.
   Rückschreiben bleibt eine separat geprüfte Operation.

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
[gemeinsame Abnahmeliste](./connector-contract#vollständigkeit-und-abnahme).

## Referenzen und nächste Schritte

Vendor-Referenzen wurden am 2026-10-03 geprüft. Verwende die zur Installation passende Version;
diese Links sind keine Implementierungszusage.

- [Xentral product/API example](https://developer.xentral.com/docs/create-a-product-v2-api)
- [Xentral sales-order lifecycle](https://developer.xentral.com/docs/create-sales-order-xentral-api-guide)
- [Xentral stock reads](https://developer.xentral.com/docs/read-stock)
- [Xentral stock movements](https://developer.xentral.com/reference/getapi-v3-stockmovements)

Repository-Vorlagen: `packages/reality-core/tests/test_source_ingestion.py`,
`test_shopify_and_explain.py`, `test_shop_order_changes.py`, `test_shop_refunds.py` und
`test_shop_line_gaps.py`. Sie beweisen ihre vorhandenen Services, nicht einen fertigen
Xentral-Live-Connector.

[Von Quelldaten zu Reality](./connector-contract) · [Erstpilot](./parallel-test) ·
[Interpreter entwickeln](../development/connectors)
