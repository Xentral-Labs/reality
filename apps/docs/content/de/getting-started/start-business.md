# Ein Unternehmen von null aufbauen

Beginne mit einem leeren Unternehmen und lass deinen Agenten ein kleines, zusammenhängendes Geschäft
einrichten. Dein erstes Ergebnis ist ein prüfbarer Auftrag, nicht nur eine Liste neuer Stammdaten.

Das Beispiel beschreibt ein kleines Geschäft mit Schreibtischlampen. Nutze im eigenen Unternehmen
deine tatsächlichen Namen und angegebenen Werte. Zum Üben mit den Beispieldaten wählst du
stattdessen eine **leere Sandbox**.

## 1. Erstelle das leere Unternehmen

<ProductLink>Reality öffnen</ProductLink>, Account erstellen, E-Mail bestätigen und anmelden. Gib
deinen Firmennamen ein, wähle **Eigene Firma starten** und bestätige **Unternehmen erstellen**. Mit
vorhandenem Account kannst du es unter **Unternehmen** anlegen. Bei einem regulären Unternehmen
erfasst die Anlage auch den eigenen Geschäftspartner des Unternehmens.

Für eine Übung wählst du **Leere Sandbox erstellen**. Lass diese Sandbox während der gesamten Übung
ausgewählt. Der Agent soll prüfen, welche Einrichtungsdatensätze und Aktionen dort verfügbar sind.

## 2. Verbinde deinen Agenten

Folge [Deinen Agenten verbinden](./connect-agent) oder nutze den eingerichteten Reality-**Chat**.
Erlaube die Abfragen und Vorschlagswerkzeuge für Stammdaten- und Auftragsanlage. Registrierung und
Unternehmensanlage erledigst du im Browser; der Agent arbeitet im freigegebenen Unternehmen.

## 3. Beschreibe dem Agenten dein Geschäft

```text
Ich richte in diesem Reality-Unternehmen ein kleines Geschäft mit Schreibtischlampen
ein. Wir verkaufen bestandsgeführte Artikel in Stück (pcs) und verwenden EUR. Lies die
bereits vorhandenen Einrichtungsdatensätze. Sage mir, welche Datensätze für den eigenen
Geschäftspartner, Artikel, Kunden und Lager für einen ersten Kundenauftrag benötigt
werden. Frage nach fehlenden Angaben. Erfinde keine Bestände, Preise oder
Geschäftsvorfälle und bereite noch keine Änderungen vor.
```

**Prüfen:** Der Agent trennt vorhandene Datensätze von fehlender Einrichtung und fragt nach den
benötigten tatsächlichen Werten. Eine Geschäftsbeschreibung allein erzeugt keine Datensätze.

## 4. Bereite die minimalen Stammdaten vor

Für die Übung verwendest du diese ausdrücklich angegebenen Beispielwerte:

```text
Prüfe zuerst, ob diese Datensätze schon bestehen. Bereite getrennte Anlagevorschläge
für fehlende Datensätze vor: Artikel START-LAMP, Name Schreibtischlampe, Bestandseinheit
pcs, Typ stocked; Kunde Beispielkunde, Rolle customer; Standort Hauptlager, Typ
warehouse. Ermittle den eigenen Geschäftspartner aus vorhandenen Datensätzen. Wenn er
fehlt, frage vor einem Vorschlag nach dem genauen Namen. Zeige jeden Prüflink und seine
Wirkung. Führe keine Vorschläge aus und lege keine Duplikate an.
```

Prüfe und bestätige die Vorschläge in Reality. Lass den Agenten die angelegten Datensätze und ihre
IDs lesen, bevor du weitergehst. Bei fehlender Berechtigung oder nicht verfügbarer Aktion hältst du
den Schritt an und lässt erklären, was benötigt wird. Siehe das
[Stammdaten-Playbook](/de/agent-playbooks/master-data-and-sources).

## 5. Erfasse den ersten Auftrag

Nutze im eigenen Unternehmen eine tatsächliche Vereinbarung. Für die Sandbox-Übung gibst du
stattdessen diese fiktive Vereinbarung ausdrücklich an:

```text
Für diese Übung hat Beispielkunde 5 pcs START-LAMP bestellt. Der angegebene Stückpreis
ist EUR 20, der angegebene Bruttobetrag der Position EUR 100. Der angegebene Bruttoauftragsbetrag ist ebenfalls EUR 100. Bereite einen
Kundenauftragsvorschlag mit Nummer START-SO-001 vor. Verwende Hauptlager und die
tatsächlichen IDs für Unternehmen, Kunde, Artikel und Standort. Frage nach weiteren
benötigten Angaben. Übernimm die Beträge wie angegeben. Zeige den Prüflink. Führe den
Vorschlag nicht aus und erfasse keine Warenbewegung.
```

Prüfe den Auftrag, bestätige ihn und untersuche sein erfasstes Ergebnis. Ein Auftrag erfasst eine
Lieferzusage; er erzeugt keinen physischen Bestand. Erfasse Ware nur aus einem angegebenen
Anfangsbestand oder einem tatsächlichen Wareneingang. Ohne vorhandenen Bestand kann der erste
Auftrag korrekt einen ungedeckten Bedarf zeigen.

## 6. Gib dem Agenten seine erste operative Aufgabe

```text
Lies unseren ersten Auftrag und erkläre Lieferzusage, Bestand, Reservierungen und
offene Menge. Sage mir, welche nächste Aktion möglich ist, welche Belege benötigt
werden und welche Entscheidung bei mir liegt. Verändere keine Daten. Zeige die
Datensätze hinter deiner Antwort.
```

**Prüfen:** Du kannst vom Auftrag zur Lieferzusage folgen und erkennst, was noch benötigt wird. Wenn
eine zulässige Aktion verfügbar ist, folge dem [Vorschlags- und Prüfablauf](./first-action) im
bewusst ausgewählten Unternehmen; das allgemeine Beispiel dort verwendet eine Demo-Sandbox.

Wiederhole die Aufgabe bei neuen Aufträgen und erweitere sie anhand des
[Arbeitsrhythmus](/de/agent-playbooks/operating-rhythm). Wiederkehrende Agentenausführung wird
getrennt eingerichtet; der Prompt läuft morgen nicht von selbst.

**Andere Wege:** [Demo erleben](./demo-company) ·
[Mit bestehender Firma starten](./existing-business).
