# Zusammenfassung

[Zurück zur Handbuchübersicht](../business-reality-guide)

## Ein gemeinsames Geschäftsjournal

Stell dir Reality als ein gemeinsames Geschäftsjournal vor, das mit deinem Unternehmen weiterwächst.
Darin bleiben die ursprünglichen Eingaben, die erfassten Belege und die Einträge zur Abwicklung
miteinander verbunden. Du kannst nachsehen, was vereinbart, zugeordnet, bewegt oder gebucht wurde
und worauf diese Angaben beruhen.

Menschen, Agenten und Workflows arbeiten mit diesem gemeinsamen Stand. Mit den passenden Rechten
lesen sie ihn über Reality-Werkzeuge, entscheiden über den nächsten Schritt und erfassen dessen
Ergebnis wieder über diese Werkzeuge. Der nächste Bearbeiter kann daran anknüpfen.

**Lesen → verstehen → entscheiden → über ein Werkzeug handeln → Ergebnis prüfen.**

So wächst das Geschäftsjournal mit jeder Bestellung, jeder Zuordnung, jeder Lieferung und jeder
Zahlung weiter. Eine Liste zeigt dir daraus den aktuellen Stand; die verknüpften Einträge erklären,
wie er entstanden ist.

## Wenige Grundbegriffe, unterschiedliche Aufgaben

| Eintrag                     | Was du dir darunter merken kannst                                                                          |
| --------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **SourceRecord**            | „Das ist die ursprüngliche Eingabe, auf die wir uns beziehen.“                                             |
| **Document / DocumentLine** | „Diese Bestellung oder Rechnung mit ihren Positionen haben wir erfasst.“                                   |
| **Commitment**              | „Wir sollen dem Kunden diese Menge liefern“ oder „der Lieferant soll sie uns liefern“.                     |
| **Reservation**             | „Diese vorhandene Ware ist für diese Lieferzusage vorgesehen.“                                             |
| **Movement**                | „Diesen tatsächlichen Wareneingang oder Warenausgang haben wir erfasst.“                                   |
| **LedgerEntry**             | „Diesen finanziellen Vorgang haben wir gebucht.“                                                           |
| **Fact**                    | „Diese zusätzliche, unterstützte Beobachtung hat eine Quelle über einen bestehenden Datensatz mitgeteilt.“ |

Die Einträge stehen nicht bloß in zeitlicher Reihenfolge nebeneinander. Sie verweisen aufeinander:
Die Reservierung gehört zur Lieferzusage, die Lieferzusage zum betreffenden Auftrag. Eine Zahlung
hat ihre eigene Buchung; eine **SettlementAllocation** ordnet sie einer Rechnung zu. Diese
Beziehungen machen aus einer Folge von Einträgen einen erklärbaren Geschäftsfall.

## Ein kurzer Streifen aus Northstars Geschäft

```text
Northstar bestellt 30 Lampen
  → Eingabe und Auftrag werden erfasst; die Lieferzusage entsteht.

Acht Lampen werden für Northstar vorgesehen
  → Eine Reservierung wird erfasst. Noch ist nichts geliefert.

Northstar schreibt: „Seiteneingang benutzen“
  → Die Quelle bleibt erhalten; ein unterstützter Fact ergänzt die Lieferzusage.

Acme versendet Ware und erfasst den Versand
  → Eine Warenbewegung entsteht; die passenden Reservierungen werden verbraucht.

Jemand fragt: „Was müssen wir noch liefern?“
  → Reality liest Zusage und erfasste Lieferungen und berechnet die offene Menge.
```

Ob die nächste Frage von einer Mitarbeiterin, einem Workflow oder einem Agenten kommt, ändert die
fachliche Grundlage nicht. Alle verwenden die gemeinsamen Werkzeuge und Regeln. Neue Informationen
von außen müssen erst nachvollziehbar erfasst werden, bevor sie als belegte Grundlage dienen. Ein
Agent braucht dafür die relevanten Einträge zum Vorgang, nicht die gesamte Datenbank.

## Was wichtig wird, bekommt den passenden Platz

Ist dir eine zusätzliche Auftragsinformation wichtig, beginnt die Frage bei ihrer Bedeutung.
Northstars Lieferanweisung kann als Fact an der Zusage sichtbar werden, weil ein passendes Predicate
diese Beobachtung unterstützt. Ein bislang ungenutztes Quellfeld bleibt zunächst in der
Originaleingabe erhalten.

Ein neuer operativer Liefertermin, eine Reservierung oder ein Zahlungsausgleich gehört dagegen in
den jeweiligen dafür vorgesehenen Datensatz. Facts sind ergänzender Kontext, kein zweiter Ort für
bereits geführten Bestand oder Lieferstatus. Fehlt eine benötigte Bedeutung, beschreibst du die
Lücke unter Offene Fragen und wählst den passenden Erweiterungsweg.

## Die Historie bleibt erklärbar

Das Journal ist ein Denkbild: Reality ist keine einzelne endlose Tabelle, und nicht jeder Datensatz
ist unveränderlich. Eine Reservierung kann etwa von aktiv zu verbraucht wechseln. Ursprüngliche
SourceRecord bleiben unverändert; falsche Lagerbewegungen und Buchungen werden durch
nachvollziehbare Gegen- und gegebenenfalls Ersatzeinträge korrigiert. Frühere Angaben verschwinden
dabei nicht einfach.

Deshalb lautet die Regel nicht „jeder darf nur etwas an eine Tabelle anhängen“, sondern:
**Geschäftsvorgänge laufen über die vorgesehenen Reality-Werkzeuge und erhalten ihre Prüfspur.**
Berechtigungen und erforderliche Bestätigungen gelten auch für Agenten und Workflows. Die Historie
erklärt die erfassten Vorgänge; sie verspricht keine vollständige Zeitreise zu jedem früheren
Systemzustand.

## Das ist der Kern

Du baust dein Business auf gemeinsamen, nachvollziehbaren Geschäftsdatensätzen auf. Menschen,
Agenten und Workflows können daraus den Stand verstehen, ihren nächsten Schritt entscheiden und über
dieselben Regeln weiterarbeiten. Die neuen Einträge werden wieder zur Grundlage der nächsten Frage.
**Reality hält diese gemeinsame Grundlage zusammen.**

Zum Anwenden: [Tools nutzen](../../tool-usage/). Zum Nachschlagen:
[Tabellenübersicht](../../reference/table-map). Zurück zu
[Facts und offenen Fragen](./06-facts-and-open-questions).

[Die Bausteine mit ihren Feldern und Aktionen erkunden](/de/tool-usage/#model:commitment).
