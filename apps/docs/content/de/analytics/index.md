# Auswertungen: von der Frage zur Antwort

Frag im bestehenden Chat „Welche Kunden haben Produkt X dieses Jahr bestellt?" oder öffne
**Analytics → Geschäftsgraph** und baue dieselbe Frage als Schrittstapel auf. Beide Wege gehen durch
dasselbe deklarierte Modell und bleiben im gewählten Unternehmen.

## Die erste Frage bauen

Die Seite liest sich von oben nach unten wie ein Satz. Jeder Schritt bietet nur an, was an dieser
Stelle gültig ist — deshalb lässt sich gar keine Frage zusammenstellen, die anschließend abgelehnt
werden müsste.

1. **Daten** — beginne bei den Datensätzen, die du ansehen willst: Aufträge, Rechnungen,
   Warenbewegungen.
2. **Nur** — grenze sie ein. Ein Datum bietet benannte Zeiträume (dieses Jahr, letzter Monat, die
   letzten 30 Tage) oder einen selbst gewählten Bereich; Text und Zahlen bieten Vergleiche; ein
   Ja-Nein-Feld bietet Ja oder Nein.
3. **Dann** — geh über eine deklarierte Beziehung weiter. Jede sagt vorher, ob sie **eine** oder
   **viele** Datensätze erreicht.
4. **Kennzahl** — wähle die Zahlen. Angeboten wird nur, was dieser Weg tatsächlich erreicht.
5. **Aufteilen nach** — wähle die Achsen. Ein Zeitstempel wird nach Monat aufgeteilt, denn eine
   Zeile je Zeitpunkt ist eine Liste und keine Antwort.
6. **Sortieren** und **Höchstens** — größte zuerst, kleinste zuerst oder unsortiert; zehn Zeilen
   oder deine eigene Zahl.

Entfernst du einen Schritt, verschwindet alles mit, was auf die dort erreichten Datensätze zeigte.

## Drei brauchbare Ausgangspunkte

- **Umsatz je Währung und Monat:** bei Aufträgen beginnen, Auftragswert zählen, nach Währung und
  Bestelldatum aufteilen. Beträge in verschiedenen Währungen werden nie zusammengezählt.
- **Deine größten Kunden:** bei Aufträgen beginnen, zum bestellenden Geschäftspartner weitergehen,
  nach Name und Währung aufteilen, nach Auftragswert sortieren, zehn behalten.
- **Was ein Artikel verkauft hat:** bei Aufträgen beginnen, zu den Auftragspositionen weitergehen,
  auf die Artikelnummer filtern, den Positionswert zählen.

## Wenn es Nein sagt

Manche Fragen lassen sich nicht richtig beantworten. Dann sagt die Seite das, statt eine falsche
Zahl zu zeigen:

- **„Hier zu summieren würde die Summe vervielfachen."** Ein Auftrag hat viele Positionen. Sobald
  der Weg die Positionen erreicht, würde der Auftragswert einmal je Position gezählt. Nimm eine
  Positions-Kennzahl oder den Schritt zurück.
- **„Diese Werte sind nicht in derselben Einheit gemessen."** Euro und Dollar, Stück und Kilogramm.
- **„Diese Zahl ist ein Zustand, kein Fluss."** Ein Lagerbestand lässt sich nicht über Monate
  aufaddieren.
- **„Dieses Feld ist nicht als Datum hinterlegt."** Manche Belegdaten liegen als Text vor; filtern
  und auflisten geht, nach Monat aufteilen nicht.

Weitergehen, ohne das Erreichte zu verwenden, vervielfacht nichts: der Schritt wird zur Prüfung, ob
es die Datensätze gibt, nicht zu einer Verknüpfung. Deshalb kannst du nach Aufträgen fragen, _die
einen Artikel enthalten_, ohne dass sich die Auftragssumme ändert.

## Speichern

Speichere eine Frage unter **Meine Auswertungen**. Wieder öffnen, umbenennen, duplizieren oder
löschen — sie gehört nur dir.

Gespeichert wird die **Frage**, nie ihre Antwort. Beim Öffnen läuft sie erneut gegen die Datensätze,
wie sie jetzt sind; ein benannter Zeitraum löst sich also neu auf, und die Zahlen können abweichen.
Speichern friert kein Ergebnis ein — eine eingefrorene Zahl hört in dem Moment auf zu stimmen, in
dem jemand einen Datensatz korrigiert.

## So bedient ein Agent die Auswertung

1. `graph_catalog` liefert die Datensätze, die dieses Unternehmen deklariert, ihre Verbindungen und
   die Bedeutung jeder Zahl — in der Sprache des Lesers.
2. `graph_ask` beantwortet eine Traversierung oder einen Pfad in der Cypher-nahen Syntax.
3. Kommt eine Ablehnung zurück, nennt sie die Beziehung, die auffächert, oder die Einheit, die sich
   nicht addieren lässt. Nochmal fragen ändert daran nichts.

Der Agent reicht kein SQL ein, und das Mandantenprädikat setzt der Compiler, nicht der Fragende.
Lesen braucht keine Bestätigung. Eine private Auswertung zu speichern läuft über
`graph_report_change_propose` mit ausdrücklicher Bestätigung; die vertrauenswürdige
Benutzeridentität liefert die Anwendung, sie wird nie in Werkzeugargumenten erfunden. Reine
Mandanten-Zugangsdaten können keine privaten Auswertungen besitzen.

Siehe die [genauen Werkzeugschemata](../tool-usage/commands) und die
[Agenten-Playbooks](../agent-playbooks/).

## Was die Antwort abdeckt

Ergebnisse beschreiben interpretierte Datensätze im gewählten Unternehmen. Ein leeres Ergebnis
heißt, dass keine übernommenen Datensätze passen — es beweist nicht, dass das Quellsystem nie einen
solchen Auftrag erhalten hat. Fehlende Beträge bleiben unbekannt, Einheiten und Währungen werden nie
stillschweigend zusammengeführt. Zu jeder Antwort lässt sich die Anweisung anzeigen, zu der sie
wurde, und der Weg, den sie genommen hat.
