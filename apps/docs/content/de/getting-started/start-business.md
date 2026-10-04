# Ein Unternehmen von null aufbauen

Beginne mit einem leeren Unternehmen und lass deinen Agenten ein kleines, zusammenhängendes Geschäft
einrichten. Dein erstes Ergebnis ist ein prüfbarer Auftrag, nicht nur eine Liste neuer Stammdaten.

Beschreibe dein Geschäft und gib seine tatsächlichen Namen und Werte an. Zum Üben wählst du eine
**leere Sandbox** und gibst ausdrücklich fiktive Werte für die Übung vor.

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
Hilf mir, in diesem ausgewählten Reality-Unternehmen ein kleines Geschäft aufzubauen.
Lies vorhandene Einrichtungsdatensätze und frage, was wir verkaufen, welche Einheiten
und Währung wir nutzen und welchen Kunden und welches Lager wir für den ersten
Auftrag brauchen. Trenne vorhandene Datensätze von fehlenden Angaben. Erfinde keine
Bestände, Preise oder Geschäftsvorfälle. Bereite noch keine Änderungen vor.
```

**Prüfen:** Der Agent trennt vorhandene Datensätze von fehlender Einrichtung und fragt nach den
benötigten tatsächlichen Werten. Eine Geschäftsbeschreibung allein erzeugt keine Datensätze.

## 4. Bereite die minimalen Stammdaten vor

Halte deine Geschäftswerte bereit; der Agent fragt nach fehlenden Angaben:

```text
Bereite getrennte Vorschläge für fehlende Artikel, Kunden, Lager und den eigenen
Geschäftspartner vor. Prüfe zuerst vorhandene Datensätze, um Duplikate zu vermeiden.
Frage nach benötigten Namen, Artikelnummern, Einheiten und weiteren fehlenden Werten.
Nutze nur meine Angaben. Zeige jeweils Wirkung und Prüflink. Führe nichts ohne meine
Freigabe aus.
```

Prüfe und bestätige die Vorschläge in Reality. Lass den Agenten die angelegten Datensätze und ihre
IDs lesen, bevor du weitergehst. Bei fehlender Berechtigung oder nicht verfügbarer Aktion hältst du
den Schritt an und lässt erklären, was benötigt wird. Siehe das
[Stammdaten-Playbook](/de/agent-playbooks/master-data-and-sources).

## 5. Erfasse den ersten Auftrag

Nutze im eigenen Unternehmen eine tatsächliche Vereinbarung. Für die Sandbox gibst du ausdrücklich
fiktive Auftragswerte vor, einschließlich Preisen, Positions- und Auftragsbeträgen:

```text
Bereite unseren ersten Kundenauftrag als Vorschlag vor. Frage nach Kunde, Artikel,
Menge, Lager, vereinbartem Termin, benötigter Auftragsreferenz sowie ausdrücklich
angegebenen Preisen, Positions- und Auftragsbeträgen. Ermittle tatsächliche
Datensatz-IDs und übernimm die Beträge unverändert; berechne keine fehlenden Werte.
Zeige Wirkung und Prüflink. Führe den Vorschlag nicht aus und erfasse keine Warenbewegung.
```

Prüfe den Auftrag, bestätige ihn und untersuche sein erfasstes Ergebnis. Ein Auftrag erfasst eine
Lieferzusage; er erzeugt keinen physischen Bestand. Erfasse Ware nur aus einem angegebenen
Anfangsbestand oder einem tatsächlichen Wareneingang. Ohne vorhandenen Bestand kann der erste
Auftrag korrekt einen ungedeckten Bedarf zeigen.

## 6. Gib dem Agenten seine erste operative Aufgabe

```text
Beobachte unsere offenen Aufträge täglich um 09:00. Erkläre Lieferzusagen, Bestand,
Reservierungen, offene Mengen und Hindernisse anhand der Reality-Datensätze.
Priorisiere nächste Schritte und frage nur nach Informationen, die du nicht selbst
beschaffen kannst. Erfinde keine Daten oder Regeln. Lies nur; Änderungen brauchen
konkrete Vorschläge und meine Freigabe.
Starte jetzt mit einer Runde. Richte danach die Wiederholung im Agentensystem ein,
wenn Tools sowie gespeicherter Arbeitsauftrag und Bearbeitungsstand verfügbar sind.
Kläre Zeitzone und Arbeitstage, nutze bestehende Routinen und zeige den geprüften
nächsten Lauf sowie Pausieren. Sage klar, welche Einrichtung noch fehlt.
```

**Prüfen:** Du kannst vom Auftrag zur Lieferzusage folgen und erkennst, was noch benötigt wird. Wenn
eine zulässige Aktion verfügbar ist, folge dem [Vorschlags- und Prüfablauf](./first-action) im
bewusst ausgewählten Unternehmen; das allgemeine Beispiel dort verwendet eine Demo-Sandbox.

Erweitere die Aufgabe anhand des [Arbeitsrhythmus](/de/agent-playbooks/operating-rhythm). Die
tägliche Prüfung um 09:00 ist ein Beispiel, keine Firmenvorgabe. Wiederkehrende Ausführung gilt erst
nach geprüfter Einrichtung im Agentensystem; ohne diese Fähigkeit wiederholst du die Abfrage
manuell.

**Andere Wege:** [Demo erleben](./demo-company) ·
[Mit bestehender Firma starten](./existing-business).
