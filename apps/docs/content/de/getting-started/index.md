# Dein erster Produktdurchlauf

Du möchtest eine Geschäftsfrage beantworten? [Auswertungen](../analytics/) führt dich durch „Welche
Kunden haben Produkt X in KW 7 bestellt?“ – von der Antwort bis zu den Auftragsbelegen.

## App öffnen

<ProductLink>Reality öffnen</ProductLink>, anmelden und ein Unternehmen auswählen. Lege zum Lernen
ein separates Unternehmen mit Beispieldaten an. Aktionen in der App verändern Datensätze im
ausgewählten Unternehmen; prüfe das Unternehmen vor der Bestätigung.

Dieser Weg führt von einem leeren Unternehmen zu einem nachvollziehbaren Geschäftsergebnis. Wenn
Reality noch nicht läuft, beginne mit dem [Einzeiler-Setup](/de/operations/installation).

Wenn du Reality als ERP-Fachperson zuerst verstehen möchtest, lies vor der Bedienung die
[Grundlagen](/de/concepts/business-reality-guide/01-from-erp-documents-to-business-reality) und
[die Rolle des Process Owners](/de/concepts/business-reality-guide/04-working-as-process-owner).
Dieser Produktdurchlauf ist der praktische zweite Schritt der 30-Minuten-Lernreise.

## Ein Unternehmen anlegen oder auswählen

Öffne Product Web, melde dich an und lege ein Unternehmen an oder wähle eines aus. Das Unternehmen
ist die Mandantengrenze für jeden Geschäftsdatensatz, jede Abfrage, jeden Agenten und jede
Konfiguration. Der Name hilft Menschen beim Wiedererkennen; eine undurchsichtige ID schafft
Identität.

## Echten Eingang oder geführte Demo wählen

Öffne für eine echte Quelle Unternehmen → **Integrationen** → **Quellsysteme**, registriere das
Vorsystem und lege fest, welche Datensatzarten es liefern darf. Nutze zum Lernen die geführte Demo.
Sie erzeugt über dieselben Anwendungsservices einen zusammenhängenden Geschäftsfall, ohne externe
Zugangsdaten zu verlangen.

Reality speichert angenommene externe Payloads verlustfrei. Es verwirft keine unbekannten Felder und
erzeugt nicht allein deshalb typisierte geschäftliche Bedeutung, weil eine Quelle ein Feld liefert.

Die Registrierung einer Quelle stellt noch keine Verbindung zum Vorsystem her. Plane für eigene
Daten zuerst einen [begrenzten Piloten](/de/integrations/parallel-test).

## Oder eine Storyline spielen

Eine Storyline ist ein geführter Geschäftsablauf, den du Schritt für Schritt in einer eigenen
Sandbox spielst: ein Auftrag von der Anlage bis zum Monatsrückblick oder ein Einkauf von der
Bestellung bis zur Zahlung mit Skonto. Jeder Schritt ist ein gewöhnlicher Befehl; daneben liest du
jeden Aufruf, den Reality gemacht hat, und was es aufgezeichnet hat. Öffne **Storyline** in der
Navigation, wähle eine in der Bibliothek und drücke Starten. Die [Storyline-Seite](/de/storylines/)
erklärt die Maske und listet die Pakete, die Reality mitliefert.

## Das erste Ergebnis lesen

Öffne **Start** für die aktuelle Position. Nutze **Ausnahmen** für Zustände, die Aufmerksamkeit
brauchen, **Ereignisverlauf** für aufgezeichnete Ereignisse und die passende Ansicht des
Arbeitsbereichs für das maßgebliche Register. Wähle ein wichtiges Ergebnis und öffne **Prüfen**.

## Business Graph, Business Facts und Tools

Beginne mit derselben Frage wie im Arbeitsalltag: „Warum sind sechs Lampen noch offen?“

- **Business Facts** zeigt die Elemente des Geschäftsfalls: etwa Source Records, Documents,
  Commitments, Reservations, Movements und Ledger Entries. Öffne einen Datensatz, um seine Details
  und die vorhandenen Belege zu prüfen.
- **Business Graph** zeigt, wie diese Elemente zusammenhängen und was im Zeitverlauf passiert ist.
  Folge von der Lieferzusage zur Reservierung und zum Versand und dann zu den vorhandenen
  Quelldaten. Graph und Timeline zeigen die erfasste Historie.
- **Tools** zeigt, was Reality damit tun kann. Unter **Aktionen** findest du Commands; unter
  **Berechnete Sichten** Views und Projections. Eine Sicht beantwortet eine Frage, etwa nach offenen
  Lieferungen. Eine Aktion verändert Datensätze und nutzt den vorgesehenen Vorschau- und
  Bestätigungsablauf.

**Business Facts ist der Gruppenname für Datensätze.** Der Datentyp **Fact** bezeichnet weiterhin
eine bestimmte, durch eine Quelle belegte Beobachtung. Ein Commitment oder Movement wird durch die
Gruppierung nicht zu einem Fact. Berechnete Sichten gehören zu Tools; sie werden nicht als neue
Quelldaten gespeichert. Bei gespeicherten Projections gehört der Berechnungsstand zur
Interpretation.

Der separate **Ereignisverlauf** listet aufgezeichnete Business Events chronologisch. Im Business
Graph betrachtest du dagegen die Beziehungen und die Timeline eines Geschäftskontexts. Für
Fähigkeiten und Parameter dient die [Tools-Referenz](/de/tool-usage/).

## Ein Beispiel zum Mitdenken

**Illustratives Beispiel, kein Live-Datenstrom und keine zugesagte Demo-Konfiguration.** Angenommen,
die passenden Auftrags-, Liefer-, Reservierungs- und Zahlungsdaten wurden erfasst. Die geführte Demo
kann einen anderen Fall zeigen.

| Erfasste Position       | Bedeutung                                                                     |
| ----------------------- | ----------------------------------------------------------------------------- |
| 10 Lampen zugesagt      | Das ausgehende Commitment umfasst zehn Lampen.                                |
| 4 versendet             | Zugeordnete Movements erfassen vier Lampen, die den Standort verlassen haben. |
| 6 noch zu liefern       | Zehn zugesagt minus vier erfüllt.                                             |
| 2 reserviert            | Aktive Reservations decken zwei der sechs offenen Lampen ab.                  |
| 4 noch nicht reserviert | Dieser Bedarf ist nicht zugeteilt, aber nicht zwingend unverfügbar.           |
| Rechnung ausgeglichen   | Buchungen und eine zugeordnete Zahlung lassen keinen offenen Betrag.          |

Bezahlt heißt nicht geliefert. Nicht reserviert heißt nicht automatisch nicht verfügbar. Ob Ware
fehlt oder eine Lieferung verspätet ist, braucht Bestandsdaten und einen zugesagten Termin.

Folge mit [Verfolge dein erstes Ergebnis zurück](./first-trace) dem Weg durch Reality, Evidence und
die ursprüngliche SourceRecord. Lies danach
[Business Reality in der Praxis](/de/concepts/business-reality-guide) für das vollständige operative
Modell oder [Agenten-Playbooks](/de/agent-playbooks/) für aufgabenorientierte Abläufe.

Prüfe vor einer Entscheidung, ob die relevanten Daten angekommen, verarbeitet und aktuell sind. Eine
leere Exception-Liste beweist keine Vollständigkeit. Ändernde Chat-Aktionen brauchen Vorschau und
Bestätigung; eine Reservation in Reality reserviert nicht automatisch Bestand in Xentral.
