# Auswertungen: von der Frage zum Beleg

Frag im bestehenden Chat „Welche Kunden haben Produkt X in KW 7 bestellt?“ oder baue dieselbe Frage
unter **Analytics → Auswertungen → Erkunden** visuell auf. Beide Wege verwenden dieselben
Auswertungswerkzeuge innerhalb des gewählten Unternehmens.

## Die erste Auswertung erstellen

1. Wähle dein Unternehmen und öffne den Explorer. Wähle Verkaufsauftragspositionen.
2. Suche Produkt X im Produktfeld und wähle den passenden Artikel aus. Der Name hilft beim Finden;
   die ausgewählte Identität bestimmt den Filter.
3. Wähle Auftragsdatum, ISO-Kalenderwoche **7**, Jahr **2026** und die geschäftliche Zeitzone.
4. Gruppiere nach Kunde und wähle Auftragsanzahl oder bestellte Menge. Starte die Auswertung.
5. Öffne die zugrunde liegenden Datensätze einer Zahl. Folge den Auftragsbelegen im Inspector bis
   zur Originalquelle, soweit vorhanden.

Ein leeres Ergebnis bedeutet, dass keine gespeicherten Datensätze passen. Es beweist nicht, dass im
Quellsystem niemals ein solcher Auftrag eingegangen ist.

## Drei praktische Einstiege

- **Kunden für Produkt und Woche:** das Beispiel oben, nach Kunde gruppiert.
- **Produktnachfrage im Zeitverlauf:** Verkaufsauftragspositionen nach Woche und Produkt gruppieren.
  Mengen bleiben nach Einheit getrennt, angegebene Werte nach Währung.
- **Offene Rechnungen nach Fälligkeitswoche:** offene Posten nach Fälligkeitswoche und Währung
  gruppieren. Das beschreibt den aktuellen Stand und ist keine Liquiditätsprognose.

## Erkunden, speichern und exportieren

Ändere Filter, Kennzahlen, Gruppierung oder Sortierung und starte erneut. Änderungen am Entwurf
ändern nicht die Bedeutung des bereits angezeigten Ergebnisses. Bei einem Fehler oder Abbruch bleibt
das letzte erfolgreiche Ergebnis mit seinen ausgeführten Einstellungen sichtbar.

Wähle Tabelle, Balken, Linie oder eine passende Pivotdarstellung. Die zugrunde liegenden Datensätze
erklären eine Kennzahl. Eindeutige Auftragsanzahlen und Gesamtsummen lassen sich nicht immer aus den
sichtbaren Zeilen aufsummieren. Beim Vorperiodenvergleich prüfst du die konkreten Zeiträume; eine
prozentuale Änderung von null bleibt unbekannt.

Speichere die Definition unter **Meine Berichte**. Du kannst einen privaten Bericht öffnen,
umbenennen, duplizieren oder löschen. Beim Öffnen werden aktuelle Daten gelesen und relative
Zeiträume neu aufgelöst. Es entsteht kein eingefrorener Ergebnisstand. Der CSV-Export umfasst
innerhalb der ausgewiesenen Grenze alle passenden Ergebniszeilen.

Über die Aktion zum Besprechen der Auswertung hängst du die Definition an den bestehenden Chat an.
Der Agent kann seine unterstützte Auswertung wiederum im Explorer öffnen lassen.

## So bedient ein Agent die Auswertung

1. `analytics_catalog` liefert Datensätze, Dimensionen, Kennzahlen und unterstützte Beziehungen.
2. Die bestehenden Referenzwerkzeuge lösen Artikel und Kunden auf.
3. `analytics_query` führt eine strukturierte Definition aus.
4. Der Agent berücksichtigt Beobachtungszeitpunkt, Zeitraum, Einheiten, Währungen und fehlende
   Daten.
5. `analytics_contributors` erklärt eine Zahl anhand der ausgeführten Definition, Gruppe und
   Kennzahl. `analytics_export` liefert CSV.

Der Agent übergibt kein SQL. Lesen benötigt keine Bestätigung. Private Änderungen werden mit
`analytics_report_change_propose` vorbereitet und ausdrücklich bestätigt. Die Anwendung liefert die
vertrauenswürdige Benutzeridentität; der Agent erfindet sie nicht in Argumenten. Zugangsdaten nur
für ein Unternehmen können keine privaten Berichte besitzen.

Die [Tool-Referenz](../tool-usage/commands) enthält die exakten Eingaben. Die
[Agenten-Playbooks](../agent-playbooks/) zeigen weitere Abläufe.

## Grenzen der Aussage

Ergebnisse beschreiben interpretierte Datensätze im gewählten Unternehmen. Fehlende Beträge bleiben
unbekannt; Einheiten und Währungen werden nicht stillschweigend vermischt. Drilldowns und Exporte
sind neue Beobachtungen und können bei Datenänderungen abweichen. Zu breite Anfragen verlangen
engere Filter statt einer versteckten Stichprobe.

<details>
<summary>30 Geschäftsfragen und die unterstützten Aussagen</summary>

| Frage                                             | Was sich feststellen lässt                                         |
| ------------------------------------------------- | ------------------------------------------------------------------ |
| Kunden mit Produkt X in KW 7                      | Passende gespeicherte Aufträge mit Jahr und Zeitzone.              |
| Inaktive Kunden                                   | Früher beobachtete Käufer ohne Auftrag im Zeitraum.                |
| Neukunden                                         | Erster beobachteter Kauf im gespeicherten Verlauf.                 |
| Kundenwachstum                                    | Veränderung angegebener Auftragswerte je Währung.                  |
| Käufer von A ohne B                               | Vorhandene und fehlende Käufe im gewählten Zeitraum.               |
| Top-Produkte                                      | Rangfolge nach Aufträgen, Käufern oder vergleichbarer Menge.       |
| Wöchentliche Nachfrage                            | Mengen und angegebene Positionswerte je Einheit/Währung.           |
| Gemeinsam gekaufte Produkte                       | Eindeutige Produktpaare desselben Auftrags.                        |
| Kundenpreise                                      | Erfasste vereinbarte Preise, keine aktuelle Preisliste.            |
| Stornos und Retouren                              | Getrennte Stornoanzahlen und eingegangene Retourenmengen.          |
| Unvollständige Lieferungen                        | Aktuelle offene Lieferzusagen an Kunden.                           |
| Überfällige Kundenzusagen                         | Aktuelle überfällige Ausgangszusagen.                              |
| Lieferbereitschaft aus Bestand                    | Reservierungs- und Sperrstatus, keine Zuteilungsoptimierung.       |
| Fehlende Produkte                                 | Reservierungslücken oder Bestand gegen Bedarf, getrennt.           |
| Lieferdauer                                       | Datierte Sendungen, keine allgemeine Empfangskennzahl.             |
| Bestand je Lagerort                               | Aktueller physischer, reservierter und verfügbarer Bestand.        |
| Bestand ohne Abgang                               | Positiver Bestand ohne ausgewählte wirksame Abgangsbewegung.       |
| Bestand unter Bedarf                              | Unternehmensweiter Bestand gegen offenen Bedarf.                   |
| Bestellungen nächste Woche fällig                 | Lieferantenzusagen mit wirksamen Terminen, keine Ankunftsprognose. |
| Kunden bei Lieferantenverzug                      | Möglicher Bedarf desselben Artikels, keine belegte Zuteilung.      |
| Lieferantenpünktlichkeit                          | Aktuell überfällige Zusagen, keine historische Quote.              |
| Einkaufspreistrends                               | Historische angegebene Preise je Artikel, Währung und Einheit.     |
| Lieferanten für X                                 | Beobachteter Einkauf; bestellt und empfangen bleiben getrennt.     |
| Abhängigkeit von einem Lieferanten                | Ein beobachteter Lieferant, kein Nachweis fehlender Alternativen.  |
| Teilweise empfangene oder berechnete Bestellungen | Kanonische Empfangs- und Abrechnungsbeobachtungen.                 |
| Offene Kundenrechnungen                           | Aktuelle offene Posten und Altersstruktur.                         |
| Zahlungsverzug                                    | Erfasste Zahlungen und Fälligkeiten, kein erfundener Durchschnitt. |
| Versandt, aber nicht voll berechnet               | Versand-/Abrechnungsabweichungen mit Belegen.                      |
| Nicht zugeordnete Zahlungen                       | Erfasste zugeordnete und nicht zugeordnete Beträge.                |
| Forderungen/Verbindlichkeiten nach Woche          | Aktuelle offene Posten nach Fälligkeitswoche und Währung.          |

</details>
