# Deine erste Aktion vorbereiten

Du hast [einen Auftrag und seinen Stand gelesen](./first-question). Lass den Agenten jetzt eine
kleine geschäftliche Änderung vorbereiten: verfügbaren Bestand für eine offene Lieferzusage
reservieren.

Lass deine **Demo-Sandbox** ausgewählt. Gib für einen externen Agenten zuerst bewusst die benötigten
Vorschlagswerkzeuge frei. Die Demo nutzt dieselben Berechtigungs- und Bestätigungsgrenzen wie andere
Unternehmen; eine reine Leseverbindung kann keine Änderung vorbereiten.

## 1. Bitte um einen Vorschlag

```text
Bleibe bei dem gerade untersuchten Auftrag. Prüfe, ob sich Bestand für seine offene
Lieferzusage reservieren lässt. Wenn eine zulässige Menge und ein Standort vorliegen,
bereite mit den tatsächlichen Datensatz-IDs einen Reservierungsvorschlag vor. Erkläre
Menge, Standort und Auswirkung auf die Verfügbarkeit und gib mir den Reality-Prüflink.
Führe ihn nicht aus. Wenn die Aktion nicht verfügbar ist oder Datensätze fehlen,
erkläre den Grund und halte an.
```

**Das solltest du sehen:** Entweder einen Vorschlag für eine konkrete Reservierung oder die
Erklärung, warum die Aktion nicht vorbereitet werden kann. Ein Vorschlag ist keine ausgeführte
Reservierung. Nicht jeder Demo-Auftrag hat geeigneten Bestand; nicht jede Sandbox-Aktion muss
zulässig sein.

## 2. Prüfe und bestätige in Reality

Öffne den Prüflink des Vorschlags. Prüfe Unternehmen, Lieferzusage, Artikel, Standort und Menge.
Lies die vorgeschlagene Wirkung. Bestätige nur, wenn du genau diese Änderung möchtest; andernfalls
lehne sie ab.

Eine Reservierung ordnet Bestand einer Zusage zu. Sie versendet keine Ware und verändert keinen
physischen Bestand. Deine Bestätigung gilt für diesen Vorschlag, nicht für zukünftige Aktionen des
Agenten.

## 3. Kontrolliere das Ergebnis

Kehre nach der Ausführung in dieselbe Unterhaltung zurück:

```text
Lies den Ausführungsstatus des Vorschlags sowie die aktuellen Reservierungen und die
Bestandsverfügbarkeit des Auftrags. Sage mir, ob die Reservierung tatsächlich erfasst
wurde, was sich verändert hat und was noch offen ist. Zeige die zugrunde liegenden
Datensätze. Nimm keine weiteren Änderungen vor.
```

**Das solltest du sehen:** Ausführungsergebnis und aktuelle Datensätze. Die Lieferung bleibt offen,
bis tatsächlich Ware versendet wurde. Läuft die Ausführung noch oder ist ihr Ausgang unbekannt,
prüfe ihren Status, bevor du einen weiteren Vorschlag einreichst.

Du hast jetzt den Arbeitsablauf durchlaufen: **lesen → vorschlagen → prüfen und bestätigen →
verifizieren**.

Weiter mit [Vertrieb und Versand](/de/agent-playbooks/order-to-cash-fulfilment) für weitere
operative Fragen oder [einer Storyline](/de/storylines/) für einen vollständigen geführten Prozess.
