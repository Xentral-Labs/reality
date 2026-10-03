# Mit einer bestehenden Firma starten

Gib dem Agenten eine nützliche Aufgabe aus deinem heutigen Geschäft, bevor du seine Verantwortung
erweiterst. Eine gute Startfrage ist: **Welche Kundenaufträge müssen noch geliefert werden, und was
verhindert das?**

## 1. Wähle eine Frage und ihre Grenzen

Nimm eine Aufgabe, die dein Team schon versteht und prüfen kann. Kläre, welches Quellsystem die
Aufträge hält, welche Bestands- und Versanddatensätze benötigt werden und wer die Antwort prüft.

```text
Hilf mir, einen ersten Reality-Piloten für unser bestehendes Unternehmen abzugrenzen.
Die Aufgabe ist, offene Kundenlieferungen zu erklären. Frage, welche Systeme Aufträge,
Bestand und Versand halten, welchen Zeitraum und welches Unternehmen wir betrachten
und wer die Antwort prüfen kann. Liste die benötigten Datensätze. Behaupte keine
bestehende Quellenverbindung und verändere keine Daten.
```

**Prüfen:** Du hast eine begrenzte Frage und eine Liste benötigter Daten, kein Versprechen, alle
Systeme anzubinden oder das gesamte Unternehmen zu automatisieren.

## 2. Erstelle ein separates Pilotunternehmen

<ProductLink>Reality öffnen</ProductLink>, Account erstellen und E-Mail bestätigen. Lege danach das
Unternehmen für diesen Piloten an oder wähle es aus. Halte Demodatensätze getrennt von den
Geschäftsdatensätzen, die du vergleichen möchtest. Wähle **Eigene Firma starten**, um leer zu
beginnen, statt Demoinhalte auszuwählen.

## 3. Organisiere den ersten Dateneingang

Kläre Quellenverbindung und Interpretation mit der Person, die die Integration umsetzt. Ein
registriertes Quellsystem ist keine ERP-Verbindung. Ein Katalogeintrag für Shopify, Xentral oder
Odoo beweist keine funktionierende Live-Anbindung.

Beginne mit wenigen bekannten Fällen: einem offenen Auftrag, einer Teillieferung und einem
blockierten Auftrag. Lass den Piloten gegenüber dem Vorsystem lesend. Die
[Pilotanleitung](/de/integrations/parallel-test) und der
[Einstieg in die ERP-Anbindung](/de/development/connectors) erklären den Umsetzungsweg.

## 4. Verbinde den Agenten und vergleiche eine Antwort

[Verbinde deinen Agenten](./connect-agent) mit dem Pilotunternehmen und den benötigten
Lesewerkzeugen. Sobald die Datensätze angekommen und interpretiert sind, nutze diesen Prompt:

```text
Erkläre die offene Lieferarbeit in unserem Pilotumfang ausschließlich anhand der
Datensätze in diesem Reality-Unternehmen. Zeige bestellte, erfüllte und offene Mengen
sowie belegte Hindernisse. Nenne die zugrunde liegenden Datensätze und Lücken in
Quellenabdeckung oder Aktualität. Verändere keine Daten und ersetze Lücken nicht durch
Annahmen.
```

Vergleiche einen bekannten Auftrag mit dem Vorsystem. Prüfe Lieferzusage, zugehörige Bewegungen und
vorhandene Herkunftsverweise in Reality. Fehlende oder nicht interpretierte Daten bleiben eine
ausdrückliche Lücke; ein leeres Ergebnis beweist keine vollständige Erledigung im Vorsystem.

## 5. Gib dem Agenten eine begrenzte Aktion

Wenn die Abfrage zum Geschäftsfall passt, wähle eine Aktion, zum Beispiel einen
Reservierungsvorschlag für zulässigen Bestand. Erlaube bewusst die benötigten Vorschlagswerkzeuge.
Lass Wirkung und Prüflink erklären, bestätige die genaue Wirkung in Reality und lies danach die
entstandenen Datensätze.

Nutze den [Vorschlags- und Prüfablauf](./first-action) mit deinem ausgewählten Pilotunternehmen. Das
Beispiel dort verwendet Demodatensätze; dein Vorschlag muss die tatsächlichen Pilotdatensätze
nutzen. Ein Vorschlag in Reality autorisiert kein Zurückschreiben in dein ERP.

## 6. Mache aus dem Piloten eine wiederholbare Aufgabe

```text
Beschreibe unsere vereinbarte Prüfung offener Lieferungen als wiederholbare Aufgabe:
Umfang, benötigte Quelldatensätze, Auslöser, erlaubte Abfragen und Vorschläge,
Entscheidungen mit meiner Freigabe, Ergebnisprüfung und den Punkt, an dem du anhalten
und Hilfe anfordern musst. Plane keine Ausführung und ändere keine Berechtigungen.
```

**Prüfen:** Eine Person kann Aufgabe und Grenzen überprüfen. Führe sie bei geänderten Quelldaten
erneut aus und prüfe das neue Ergebnis. Wiederkehrende Ausführung, Quellenüberwachung und externe
Aktionen benötigen getrennte Einrichtung und Autorisierung. Erweitere eine Aufgabe nach der anderen
anhand des [Arbeitsrhythmus](/de/agent-playbooks/operating-rhythm).

**Andere Wege:** [Demo erleben](./demo-company) · [Von null aufbauen](./start-business).
