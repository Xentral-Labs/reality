# Was kann angepasst werden?

Diese Seite richtet sich an ERP-Berater und Integrationsentwickler. Beginne mit dem fachlichen
Ergebnis und wähle danach die kleinste notwendige Erweiterung.

Wenn du Reality zuerst mit Daten aus einem vertrauten System verstehen möchtest, folge
[Reality parallel zum ERP testen](./parallel-test). Der Ablauf bleibt gegenüber dem ERP zunächst
lesend und zeigt, wann Konfiguration genügt und wann noch ein kleiner Adapter oder Interpreter nötig
ist.

| Fachlicher Wunsch                                | Was wird angepasst?                          | Typischerweise nötig                   |
| ------------------------------------------------ | -------------------------------------------- | -------------------------------------- |
| Aufträge aus einem weiteren ERP übernehmen       | Connector-Transport und Auftrags-Interpreter | Integrationscode                       |
| andere CSV-Spaltennamen zuordnen                 | Datei-Mapping                                | Konfiguration oder kleine Codeänderung |
| einen zusätzlichen ERP-Objekttyp übernehmen      | Source Capability und Interpreter            | Integrationscode                       |
| eine vorhandene Reality-Aktion aufrufen          | HTTP API oder MCP-Tool                       | Integrationskonfiguration              |
| eine vorhandene Aktion anders platzieren         | Workspace-Katalog                            | Konfiguration                          |
| eine wirklich neue Geschäftsposition berechnen   | Projection                                   | Reality-Core-Entwicklung               |
| ein neues operatives Risiko erkennen             | Exception-Ableitung                          | Reality-Core-Entwicklung               |
| einen neuen geregelten Geschäftsablauf einführen | Service und Command                          | Reality-Core-Entwicklung               |

## Was normalerweise unverändert bleiben kann

Eine ERP-Anbindung braucht kein zweites Auftrags-, Bestands- oder Finanzmodell. Der Connector erhält
den Original-Payload; der Interpreter übersetzt verstandene Bedeutung in vorhandene Evidence- und
Reality-Datensätze. Unbekannte Felder bleiben im `SourceRecord.payload` verfügbar.

Prüfe vor neuem Code die generierten [Geschäftsaktionen und Agenten-Tools](../tool-usage/commands)
sowie die [Sichten, Projections und Aktionen](../tool-usage/views). Häufig existiert die benötigte
Fähigkeit bereits und nur Transport oder Interpretation des ERP fehlen.

## Das passende nächste Kapitel

- Für neue Datenquellen: [Ein weiteres ERP anbinden](../development/connectors).
- Für den vollständigen Weg: [Beispiel eines ERP-Auftrags](./order-example).
- Für Anmeldung, Versionierung, Wiederholung und Fehler: [Connector-Contract](./connector-contract).
- Für vorhandene Funktionen: [API und Agentenschnittstellen](../api-tools/).
- Nur bei wirklich fehlendem Geschäftsverhalten: [Reality-Core-Entwicklung](../development/).

## Belegte Beobachtungen ohne neuen Connector ergänzen

Inhaber können begrenzte Fact-Regeln für gespeicherte Quellen und vorhandene Bezugsobjekte
konfigurieren. Beginne bei
[fehlenden Informationen](/de/concepts/business-reality-guide/06-facts-and-open-questions#missing-information):
erst simulieren, dann aktivieren, ältere Quellen getrennt nachverarbeiten. Das kann eine Beobachtung
auslesen oder eine geprüfte Einordnung erzeugen. Es ist kein allgemeiner Feldeditor, keine
Datenanbindung, keine freie Formelmaschine und kein Exception-Baukasten.
