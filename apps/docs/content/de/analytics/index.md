# Analytics auf deiner Geschäftsrealität

Reality verbindet operative Datensätze zu einem abfragbaren Business Graph. Untersuche Aufträge,
Bestände und Zahlungen, folge ihren Beziehungen und erstelle Berichte über die Daten, die Reality
bereits enthält. Deine Agenten nutzen dasselbe Modell und dieselben Prüfungen wie der Analyseeditor.

**Keine zusätzliche Analytics-Datenbank, die synchron gehalten werden muss.** Der Graph beschreibt
vorhandene Datensätze in PostgreSQL. Sie müssen nicht in eine zweite Graphdatenbank exportiert
werden. Externe Quellen müssen weiterhin in Reality aufgenommen und interpretiert werden, bevor sie
ausgewertet werden können.

## Warum die gemeinsame Grundlage wichtig ist

Ein Auftrag enthält einen angegebenen Wert von 1.000 EUR und vier Positionen. Ein unbedachter Join
kann den Auftragswert viermal wiederholen und 4.000 EUR ausweisen. Reality kennt die Bedeutung: Der
Betrag gehört zum Auftrag, die Beziehung zu den Positionen erreicht mehrere Datensätze. Das Modell
lehnt eine unsichere Summe ab, statt eine plausible, aber falsche Zahl auszugeben.

Dasselbe Prinzip gilt für Währungen, Einheiten und Zeit: Euro werden nicht zu Dollar addiert, Stück
nicht zu Kilogramm und aktuelle Lagerbestände nicht über Monate aufsummiert.

| Geschäftsfrage                                 | Was das Modell beiträgt                                                      |
| ---------------------------------------------- | ---------------------------------------------------------------------------- |
| Welche Kunden haben den höchsten Auftragswert? | Kundenidentität, übernommene Auftragsbeträge und getrennte Währungen         |
| Was ist noch zu liefern?                       | Mit Warenbewegungen verbundene Zusagen und deklarierte Restmengen            |
| Was schulden uns Kunden?                       | Dieselben maßgeblichen Berechnungen finanzieller Positionen wie in Finance   |
| Bei welchen Artikeln fehlt Bestand?            | Aktuelle physische und reservierte Mengen aus dem operativen Bestandsservice |

Auftragswert ist **kein realisierter Umsatz**, eine Reservierung **keine Lieferung** und verfügbarer
Bestand **keine Versandfreigabe**. Das Modell bewahrt diese Unterschiede.

## Architektur: ein Graph über vorhandenen Datensätzen

Zwei Wege greifen ineinander: wie Geschäftsdaten in Reality ankommen und wie eine Analyse sie liest.

```text
SourceRecord → Document / DocumentLine → operative Reality-Datensätze
                                             ↑
Frage → deklariertes Geschäftsmodell → geprüfte Abfrage → PostgreSQL / gemeinsame Services
                                             ↓
                                Ergebnis + Abfrageerklärung
```

Die Grundlage umfasst **Facts, Commitments, Reservations, Movements und Ledger Entries** sowie
Quellbelege, Dokumente, Geschäftspartner und Artikel. Der Graph basiert also nicht ausschließlich
auf der Tabelle `Fact`. „Business Facts“ bezeichnet den Produktbereich zur Datensatzprüfung; `Fact`
ist ein bestimmter Datensatztyp.

Eine Deklaration beschreibt die Bedeutung der Daten:

| Baustein | Bedeutung                                     | Beispiel                                                             |
| -------- | --------------------------------------------- | -------------------------------------------------------------------- |
| Node     | Was ein Datensatz darstellt                   | Ein Kundenauftrag oder ein Artikel                                   |
| Edge     | Welche Datensätze tatsächlich zusammengehören | Auftrag enthält Positionen; Position verweist auf Artikel            |
| Grain    | Was eine Ergebniszeile zählt                  | Ein Auftrag, nicht ein je Position wiederholter Auftrag              |
| Measure  | Welche Zahl wie aggregiert werden darf        | Übernommener Auftragsbetrag, getrennt nach Währung                   |
| Coverage | Welche Betrachtung unterstützt wird           | Aktueller Zustand, Aktivität im Zeitraum oder unterstützter Stichtag |

Die Graphschicht prüft Pfade und Kennzahlen und übersetzt gewöhnliche Fragen in eine SQL-Aggregation
über vorhandene PostgreSQL-Tabellen. Jeder Knoten wird auf das ausgewählte Unternehmen
eingeschränkt. Für Bestände und finanzielle Positionen rufen registrierte Adapter die **bestehenden
maßgeblichen Services** auf und aggregieren deren temporäre Ergebnisse. Diese Pfade können mehrere
begrenzte Lesezugriffe benötigen. Sie pflegen weder eine zweite dauerhafte Datenkopie noch eine
konkurrierende Saldenberechnung.

Das ist eine semantische Graph-Abfrageschicht auf PostgreSQL mit **Cypher-ähnlicher Syntax**. Es ist
keine separate Graphdatenbank und keine vollständig kompatible Cypher-Implementierung. Zusätzliche
deklarierte Pfade über vorhandene Daten erfordern keine Kopie in eine andere Datenbank.

Technische Details stehen in der
[Graphdeklaration](https://github.com/Xentral-Labs/reality/blob/main/packages/reality-core/config/reporting_graph.yaml),
den
[Abfrageprüfungen](https://github.com/Xentral-Labs/reality/blob/main/packages/reality-core/src/reality/services/analytics/traversal.py)
und dem
[SQL-Compiler](https://github.com/Xentral-Labs/reality/blob/main/packages/reality-core/src/reality/services/analytics/compile_sql.py).

## Den Graph erkunden und einen Bericht erstellen

Du kannst auf drei Wegen starten — eine Abfragesprache musst du dafür nicht beherrschen:

- **Mit einer Vorlage:** Öffne **Analytics → Analyse** und wähle zum Beispiel **Auftragswert je
  Monat**, **Auftragseingang je Kunde**, **Fehlbestände** oder **Überfällige Kundenforderungen**.
  Eine Vorlage öffnet eine bearbeitbare, noch nicht gespeicherte Analyse. Passe Zeitraum, Filter
  oder Gruppierung an, führe sie aus und speichere die Frage bei Bedarf unter **Meine Berichte**.
- **Mit Chat:** Nutze **Mit Chat erstellen** und beschreibe deine Frage, etwa „Zeige den
  Auftragswert je Kunde für diesen Monat in EUR.“ Die Aktion bereitet einen Entwurf im bestehenden
  Chat vor, den du prüfst und selbst absendest. Einen unterstützten Analysevorschlag kannst du mit
  **In Analyse öffnen** vor dem Speichern prüfen und anpassen.
- **Über die Daten:** Der **Data Explorer** unter **Daten erkunden** zeigt verfügbare
  Geschäftsobjekte, durchsuchbare Felder, Beziehungen und Datensatzvorschauen. Starte von einem Feld
  oder Pfad aus eine ungespeicherte Analyse, wenn du zunächst entdecken möchtest, welche Fragen die
  vorhandenen Daten beantworten können.

Im Analyseeditor wählst du über den bearbeitbaren Satz Datensätze, Bedingungen, Kennzahlen,
Gruppierung und Sortierung. Alle drei Einstiege nutzen dasselbe geprüfte Modell.

Drei Ansichten erklären dieselbe Frage:

- **Ergebnis / Result** zeigt die zurückgegebenen Werte und ihre verfügbare Tabellen- oder
  Diagrammdarstellung.
- **Verbindungen / Connections** zeigt die Datensätze und Beziehungen der Frage. Diese Ansicht
  erklärt den Abfragepfad; sie ist keine zusätzliche Datenbank mit einer Kopie deines Unternehmens.
- **Cypher** macht den Pfad als bearbeitbaren Text mit separaten Parametern zugänglich.

Führe die Frage nach einer Änderung aus. Nicht unterstützte Pfade oder Kennzahlen können weiterhin
abgelehnt werden. Die Eingabefelder helfen beim Aufbau, garantieren aber nicht, dass jede
Kombination beantwortbar ist. Ein früheres Ergebnis beantwortet keine inzwischen geänderte oder
fehlgeschlagene Frage.

Für operative Positionen gibt es Vorlagen zu Bestand, Fehlmengen, offenen und überfälligen
Zahlungen. Historische Salden und physische Bestände erfordern einen expliziten Stichtag.
Historische Reservierungen, Verfügbarkeit und Altersstrukturen werden nicht unterstützt.

Erkunde das vollständige [Analytics-Modell](../tool-usage/#analytics:): durchsuchbare Objekte,
Felder, Beziehungen, Kennzahlen und Startvorlagen.

## Beispielabfragen

Füge diese Pfade im Reiter **Cypher** ein und übergib die Parameter separat. Die Beispiele nutzen
deklarierte Datensatz- und Kennzahlnamen, keine beliebigen SQL-Spalten. Die Datumsgrenzen schließen
den Beginn ein und das Ende aus. Ergebnisse hängen von den interpretierten Daten deines Unternehmens
ab.

### Auftragswert je Monat und Währung

```cypher
MATCH (o:order)
WHERE o.ordered_at >= $from AND o.ordered_at < $until
RETURN month(o.ordered_at), o.currency, sum(stated_order_amount), count(order_count)
```

```json
{ "from": "2026-01-01T00:00:00Z", "until": "2027-01-01T00:00:00Z" }
```

Die Abfrage summiert die von der Quelle übernommenen Auftragsbeträge. Sie berechnet keinen Umsatz
und rekonstruiert Beträge nicht aus Menge mal Preis.

### Die zehn Kunden mit dem höchsten Auftragswert

```cypher
MATCH (o:order)-[:ordered_by]->(customer:party)
WHERE o.ordered_at >= $from AND o.ordered_at < $until
RETURN customer.id, customer.name, o.currency, sum(stated_order_amount)
ORDER BY sum(stated_order_amount) DESC
LIMIT 10
```

Verwende dieselben Datumsparameter. Die Kunden-ID trennt gleichnamige Kunden. Das Limit wählt zehn
Kunden-/Währungsgruppen aus. Es ist keine Währungsumrechnung und keine vergleichbare Rangliste über
mehrere Währungen. Beschränke die Frage für diesen Vergleich auf eine Währung.

### Auftragspositionswert für einen Artikel

```cypher
MATCH (o:order)-[:contains]->(line:order_line)-[:of_item]->(item:item)
WHERE item.sku = $sku AND o.ordered_at >= $from AND o.ordered_at < $until
RETURN item.id, item.sku, o.currency, sum(line_amount)
```

```json
{ "sku": "LAMP-001", "from": "2026-01-01T00:00:00Z", "until": "2027-01-01T00:00:00Z" }
```

Setze deine eigene Artikelnummer ein. Gezählt werden übernommene **Positionswerte**, nicht der je
Position wiederholte Auftragsbetrag. Es geht um bestellten Wert, nicht um gelieferte Menge oder
bezahlten Umsatz.

### Eine absichtlich abgelehnte Frage

```cypher
MATCH (o:order)-[:contains]->(line:order_line)
RETURN line.sku, o.currency, sum(stated_order_amount)
```

Die Gruppierung nach Position würde den Auftragsbetrag über seine Positionen wiederholen. Die
Ablehnung `fan_out` verlangt eine Anpassung der Frage, statt die Summe unbemerkt aufzublähen. Nutze
`line_amount` für eine Summe auf Positionsebene. Auch `sum(o.gross_amount)` umgeht die Prüfung
nicht: Aggregationen müssen deklarierte Kennzahlen verwenden.

## Performance: Ausführung, Grenzen und Nachweise

Ohne zusätzliche Datenbank entfällt das Synchronisieren einer Analytics-Kopie. Abfragen benötigen
trotzdem PostgreSQL-Ressourcen und bei servicebasierten Kennzahlen auch Anwendungsressourcen.
Filter, Datenmenge, Indizes, Beziehungen und gleichzeitige operative Arbeit beeinflussen die
Laufzeit.

| Eigenschaft                          | Aktuelles Verhalten                                                                               |
| ------------------------------------ | ------------------------------------------------------------------------------------------------- |
| Gewöhnliche Graphfrage               | Eine aggregierende SQL-Anweisung statt einer Abfrage je Ergebnisdatensatz                         |
| Servicepfade für Bestand und Finance | Begrenzte maßgebliche Lesezugriffe plus Aggregation; tatsächliche Lesezugriffe werden ausgewiesen |
| Pfadgrenzen                          | Höchstens 8 Pfadschritte und Rekursionstiefe 6                                                    |
| Ergebnisbudget                       | Höchstens 10.000 Ergebniszeilen; Standardseitengröße 200                                          |
| Statement-Timeout                    | 30 Sekunden; eine Schutzgrenze, kein Antwortzeitversprechen                                       |
| Große Serviceeingaben                | Explizite Ablehnung beim Überschreiten des Adapterbudgets; keine still abgeschnittene Gesamtsumme |

Eingabebudgets unterscheiden sich je Service. Beim aktuellen Artikelbestand sind beispielsweise
Artikel und offene Lieferantenzusagen auf jeweils 20.000 begrenzt, Bewegungen und Zusagerevisionen
auf jeweils 100.000. Ein kleines Ergebnislimit umgeht nicht den Aufwand für eine korrekte
Aggregation.

### Aufgezeichnete Messungen

Ein dokumentierter Vergleich mit 10.233 Belegen und 13.590 Ledger Entries maß nach den
Abfrageverbesserungen monatliche Rechnungsbeträge mit 3 ms, Auftragseingang je Kunde mit 6 ms und
unternehmensweite Salden mit 753 ms. Siebzehn Fragen lieferten vor und nach der Änderung identische
Ergebnisse. Das sind die besten Werte aus jeweils drei abwechselnden Läufen auf einem nicht
unbelasteten Rechner, keine p95-Messungen oder Produktionsgarantien. Siehe
[Messbedingungen und vollständige Ergebnisse](https://github.com/Xentral-Labs/reality/blob/main/specs/234-analysis-derivation-cost/verification.md).

Der Unterschied zeigt, warum die Abfrageform wichtig ist: Filter vor einer maßgeblichen Berechnung
können deren Eingabemenge reduzieren. Ein ungefilterter Gesamtsaldo braucht weiterhin die
umfassendere Berechnung. Ein eigenes Statement-Budget für Ableitungen schützt zusätzlich vor
versehentlichen Datenbankabfragen je Datensatz.

### Ein sinnvoller Lasttestplan

Miss drei Lastprofile getrennt: monatliche Auftragssummen, die mehrstufige Artikelabfrage oben und
eine Vorlage für aktuellen Bestand oder finanzielle Positionen. Prüfe zuerst die erwarteten
Ergebnisse. Erhöhe anschließend Datenmengen und Parallelität, etwa auf 1, 5 und 10 Leser.

Halte PostgreSQL-Version, Rechnerressourcen, Datenmenge und -verteilung, Abfrageparameter,
Indexzustand, SQL-Lesezugriffe, warme/kalte Bedingungen, p50/p95 der gesamten Antwortzeit, Fehler
und Auswirkungen auf operative Schreibvorgänge fest. Trenne Chat-Interpretation von
Abfrageausführung. Verwende ausschließlich dedizierte Benchmarkdaten.

Hier gibt es **keine veröffentlichte Analytics-spezifische Skalierungs- oder p95-Garantie**. Der
[Engine-Vergleich](https://github.com/Xentral-Labs/reality/blob/main/specs/224-native-reporting-platform/engine-comparison.md)
ist weiterhin zurückgestellt. Laufzeiten anderer operativer Subsysteme sind kein Nachweis für diese
Analytics-Engine.

## Agentenzugriff und gespeicherte Berichte

Agenten entdecken das Modell über `graph_catalog` und übergeben `graph_ask` entweder eine typisierte
Frage oder einen Cypher-ähnlichen Pfad mit Parametern. Sie übergeben kein SQL. Unternehmensgrenzen
und Ausführungsprüfungen kommen aus der Anwendung, nicht aus einer Anweisung, an die sich der Agent
erinnern muss.

Speichere eine Frage unter **Meine Berichte**, um sie erneut zu verwenden. Gespeichert wird die
**Frage**, kein eingefrorenes Ergebnis. Beim Öffnen läuft sie erneut. Speichern über den Chat
verwendet `graph_report_change_propose` und eine explizite Bestätigung. Die vertrauenswürdige
Nutzeridentität kommt aus der Anwendung; reine Unternehmenszugangsdaten können keine privaten
Berichte besitzen. Lesen benötigt keine Bestätigung.

Siehe [Tool-Schemas](../tool-usage/commands) und [Agenten-Playbooks](../agent-playbooks/).

## Was eine Antwort abdeckt

Eine Antwort beschreibt interpretierte Datensätze im ausgewählten Unternehmen innerhalb der Filter
und unterstützten Historie. Ein leeres Ergebnis beweist nicht, dass eine externe Quelle nie einen
Auftrag erhalten hat. Fehlende Beträge bleiben unbekannt. Quellbeträge bleiben erfasste Werte;
abgeleitete Bestände und Salden bleiben Beobachtungen. Prüfe Abfrageerklärung, Verbindungen und
zugrunde liegende Datensätze, wenn du eine Zahl verstehen möchtest.
