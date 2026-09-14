# Als Prozessverantwortliche/r arbeiten

[Zurück zur Handbuchübersicht](../business-reality-guide)

## „Kann Hubers Auftrag heute raus?“ {#process-owner}

Gehen wir in unserem Beispiel kurz zurück: LightWorks hat die ersten zehn Lampen geliefert. Die acht
Lampen aus dem Anfangsbestand sind Huber zugeordnet, die zehn neuen noch nicht. Insgesamt schuldet
Acme Huber weiterhin 30 Lampen.

Ein Agent soll erklären, ob eine Teillieferung von 18 heute möglich ist. Die Antwort braucht mehr
als den Auftragskopf. Sie muss vier Fragen auseinanderhalten:

| Prüfung                               | Ergebnis an diesem Punkt                                                                   |
| ------------------------------------- | ------------------------------------------------------------------------------------------ |
| Was ist noch zugesagt?                | 30 Lampen sind offen.                                                                      |
| Was ist vorhanden?                    | 18 Lampen liegen im Lager Augsburg.                                                        |
| Was ist Huber zugeordnet?             | Acht; für die geplante Teillieferung fehlen zehn in der Zuordnung.                         |
| Was könnte die Ausführung verhindern? | Aktuelle Sperren, Berechtigungen und weitere Ausführungsbedingungen müssen geprüft werden. |

Der Agent kann die fehlende Zuordnung erklären und eine Reservierung der zehn verfügbaren Lampen
vorschlagen. Er darf noch keine erfolgte Reservierung oder Lieferung behaupten. Ein Vorschlag ändert
den Bestand nicht.

### Was du prüfst

Du vergleichst die Vorschau mit der Absicht: Ist es Hubers richtige Lieferzusage? Geht es um den
richtigen Artikel, Augsburg und zehn Stück? Ist die Ware noch verfügbar? Gibt es eine Sperre?

Nach berechtigter Bestätigung führt der Anwendungsdienst die Reservierung aus und prüft dabei die
aktuellen Bedingungen erneut. Erst die anschließende Leseprüfung zeigt, dass nun 18 Lampen Huber
zugeordnet sind. Das belegt weiterhin keinen Versand. Der tatsächliche Lagervorgang und seine
Erfassung kommen später.

## Die Rolle des Process Owners

Die oder der Prozessverantwortliche ist die fachlich verantwortliche Person, die festlegt, welche
Informationen eine Entscheidung tragen und wer welche Aktion ausführen darf. Das kann je nach
Vorgang eine Person aus Beratung, Auftragsabwicklung, Lager, Einkauf, Finanzen oder Integration
sein. Es ist eine Verantwortung, keine zwingend neue Stellenbezeichnung.

Deine ERP-Erfahrung bleibt dabei wichtig: Du kennst die Bedeutung von Lieferfähigkeit, Sperren,
Teilrechnungen und Buchungen. Hinzu kommt die Prüfung, ob ein Agent seine Aussage aus den richtigen
Datensätzen ableitet und die Grenze zwischen Lesen, Vorschlagen und Ausführen einhält.

### Die geregelte Arbeitsschleife

1. **Frage klären:** Geht es um Lieferfähigkeit, eine tatsächliche Lieferung oder eine offene
   Zahlung?
2. **Grundlagen lesen:** Zusage, Zuordnung, Bewegung oder Buchung sowie ihre Belege prüfen.
3. **Änderung vorschlagen:** Werkzeug, betroffene Datensätze und genaue Wirkung in der Vorschau
   sehen.
4. **Entscheiden und ausführen:** Eine berechtigte Bestätigung gilt für genau diesen Vorschlag.
5. **Ergebnis prüfen:** Die aktuellen operativen Einträge und Arbeitslisten erneut lesen.

Eine reine Frage braucht keine Freigabe. Eine ändernde Chat- oder MCP-Aktion bereitet zunächst einen
**Änderungsvorschlag (ChangeProposal)** vor. Eine erfolgreiche Vorbereitung beweist nur, dass dieser
Vorschlag existiert. Sie beweist nicht, dass seine geschäftliche Wirkung eingetreten ist.

### Wer bestätigt und was darf behauptet werden?

Im hier gezeigten Chat-Ablauf bestätigt eine berechtigte Person. Ein Agent darf sich die Zustimmung
nicht aus der vermuteten Absicht des Gesprächs ableiten. Die Bestätigung gilt für die konkrete
Vorschau; veränderte Argumente sind keine stillschweigend mitgenehmigte Aktion.

Eine ausdrücklich eingeräumte Entscheidungsbefugnis muss zum tatsächlich unterstützten
Ausführungsweg und zur Fallklasse passen. Sie ist keine allgemeine Selbstfreigabe für Chat- oder
MCP-Vorschläge. Auch die automatische Zahlungszuordnung aus Kapitel 3 folgt eigenen begrenzten
Importregeln; sie erteilt dem Agenten keine zusätzlichen Rechte. Maßgeblich sind die aktuelle
Werkzeugfreigabe und die serverseitigen Prüfungen, nicht ein Satz im Prompt.

„18 reserviert“ darf der Agent nach Prüfung der aktiven Reservierungen sagen. „18 versendet“
erfordert die entsprechenden erfassten Lieferbewegungen. „Bei Huber angekommen“ braucht wiederum
einen passenden Zustellnachweis. Derselbe Auftrag kann also mehrere zutreffende, aber verschieden
weit reichende Aussagen haben.

## Ausnahmen, Freigaben und Verantwortung {#exceptions-and-approvals}

Eine Arbeitsliste zeigt, worauf du achten solltest. Reality nennt einen aus den aktuellen Daten
abgeleiteten Klärfall eine **Exception**. Beispielsweise kann ein offener Lieferbedarf ohne
ausreichende Zuordnung als gefährdet erscheinen. Die konkrete Bedingung wird mit angezeigt und ist
im [Ausnahmenkatalog](../../tool-usage/exceptions) nachlesbar.

| Art des Eintrags      | Seine Frage                                     | Wie er sich erledigt                                                                               |
| --------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Ausnahme              | Welcher erfasste Zustand braucht Untersuchung?  | Die Ursache wird über einen normalen Geschäftsvorgang behoben; die Bedingung trifft nicht mehr zu. |
| Ausstehende Freigabe  | Soll diese konkrete Änderung ausgeführt werden? | Eine berechtigte Person bestätigt oder lehnt den Vorschlag ab.                                     |
| Entscheidungshistorie | Was wurde entschieden und ausgeführt?           | Die Prüfspur bleibt erhalten; Ausführung und Ergebnis müssen unterscheidbar sein.                  |

Eine Ausnahme ist kein Ticket, das du unabhängig von seiner Ursache schließen kannst. Ein Vorschlag
ist kein Beweis, dass ein Problem bereits behoben wurde. Beides kann unabhängig voneinander
auftreten.

Bei Huber bleibt nach Reservierung der zehn neu eingegangenen Lampen noch ein nicht reservierter
Bedarf von zwölf. Eine Warnung über diese verbleibende Lücke verschwindet nicht deshalb, weil du die
erste Reservierung freigegeben hast. Du liest die Mengen und die konkrete Ableitungsbedingung
erneut. Sind die nächsten zwölf angekommen und zugeordnet, kann die entsprechende Lücke geschlossen
sein.

## Entscheidungshilfe für den Alltag {#decision-guide}

Wenn sich ein Vorgang ändert, benenne zuerst, welche fachliche Aussage betroffen ist:

| Fall                                  | Passender Vorgang                                          | Was dadurch nicht automatisch geschieht   |
| ------------------------------------- | ---------------------------------------------------------- | ----------------------------------------- |
| Kunde storniert die offene Lieferung  | Lieferzusage stornieren und aktive Zuordnungen freigeben   | Kein physischer Warenausgang              |
| Ware kommt zurück                     | Tatsächlichen Rückeingang erfassen                         | Keine finanzielle Gutschrift              |
| Ein erfasster Wareneingang war falsch | Gegen- und gegebenenfalls Ersatzbewegung erfassen          | Kein Löschen der ursprünglichen Erfassung |
| Kunde erhält eine Gutschrift          | Finanzielle Gutschrift buchen und gegebenenfalls anrechnen | Kein Rücktransport von Ware               |

Der Unterschied zwischen Lagerzählung und Erfassungsfehler bleibt ebenfalls wichtig. Bei einer
heutigen Zähldifferenz erfasst du die beobachtete Differenz. Ist eine bestimmte frühere Bewegung
falsch, korrigierst du genau diese Erfassung. Gleicher Endbestand kann verschiedene Ursachen haben.

<details>
<summary>Technische Vertiefung: gemeinsame Werkzeuge und Prüfspur</summary>

Web, CLI, API, MCP und Chat nutzen dieselben Anwendungsdienste. Agenten schreiben nicht direkt in
die Datenbank und führen keine eigenen Bestands- oder Buchungsregeln ein. Die Dienste prüfen den
Mandanten, Berechtigungen, Verknüpfungen und die aktuellen Ausführungsbedingungen.

Ein ChangeProposal enthält Werkzeug, normalisierte Argumente und serverseitige Vorschau. Ablehnung
führt die vorgeschlagene Wirkung nicht aus. Bestätigung und Ausführung sind nachvollziehbar; bei
Fehlern oder unklarem Ergebnis muss die tatsächliche Wirkung geprüft werden. Eine Änderung in
Reality belegt keine automatische Änderung im ERP oder beim Zahlungsanbieter.

Werkzeuge und ihre Aussagegrenzen findest du in [Tools nutzen](../../tool-usage/#choosing-a-tool).
Die verbindlichen Details stehen im
[Chat-Contract](https://github.com/Xentral-Labs/reality/blob/main/docs/features/chat.md) und in den
jeweiligen Werkzeug- und Finanzverträgen.

</details>

### Prüfe dein Verständnis

Der Aufruf `reservation_propose` ist erfolgreich. Daneben bleibt ein Klärfall sichtbar. Ist die
fehlende Zuordnung damit behoben?

<details>
<summary>Antwort anzeigen</summary>

Nein. Zunächst existiert nur ein Vorschlag. Erst nach berechtigter Bestätigung, erfolgreicher
Ausführung und erneuter Prüfung der Mengen ist eine tatsächliche Zuordnung belegt. Ob die Ausnahme
verschwindet, hängt von ihrer vollständigen Bedingung ab.

</details>

### Lernziel

Du kannst jetzt unterscheiden, was ein Agent gelesen, vorgeschlagen und tatsächlich verändert hat.
Du prüfst seine Antwort an Belegen und Ergebnissen, nicht allein daran, ob sie plausibel klingt.

Weiter: [Ein Auftrag von Anfang bis Ende](./05-one-order-end-to-end).
