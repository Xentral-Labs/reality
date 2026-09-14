# Aufträge, Bestand und Lieferungen

[Zurück zur Handbuchübersicht](../business-reality-guide)

## Hubers Auftrag durch Lager und Einkauf verfolgen {#orders-and-inventory}

Huber bestellt 30 Lampen. Acht liegen in Augsburg; Acme kauft die fehlenden 22 bei LightWorks ein.
Wir verfolgen jetzt, welche Aktionen neue Einträge anlegen und welche Zahlen sich daraus ergeben.
Rechnung und Zahlung folgen erst im nächsten Kapitel.

Im Grundablauf gibt es einen Artikel, einen Lagerort und keine weiteren Aufträge, Bewegungen oder
Sperren. „Bestand“ bedeutet hier den aus den erfassten Warenbewegungen ermittelten physischen
Bestand. „Verfügbar“ ist der Teil davon, der noch keiner Lieferzusage zugeordnet ist.

### 1. Den Ausgangspunkt erfassen

**Im Geschäft:** Im Lager liegen acht Lampen. **In Reality:** Acme erfasst diesen Anfangsbestand als
Warenbewegung in das Lager. Dafür entsteht ein **Movement** vom Typ `opening_stock`.

**Daraus ergibt sich:** acht physisch vorhanden, null reserviert, acht verfügbar. Diese Zahlen sind
berechnete Salden; sie werden nicht als zweite, unabhängige Wahrheit eingetragen.

### 2. Den Kundenauftrag erfassen

**Im Geschäft:** Huber bestellt 30 Lampen. **In Reality:** Die unterstützte manuelle Auftragsaktion
hält die ursprüngliche Eingabe als **SourceRecord**, den Auftrag `SO-1001` als **Document** und die
Position als **DocumentLine** fest. Sie legt ausdrücklich die **Lieferzusage (Commitment)** von Acme
an Huber über 30 Stück an.

**Daraus ergibt sich:** 30 sind noch zu liefern. Der Lagerbestand bleibt acht. Der Auftrag allein
reserviert keine Ware. Ein beliebiger Beleg erzeugt auch keine Zusage; dafür ist die vorgesehene
Auftragsaktion oder ein unterstützter Import zuständig.

### 3. Vorhandene Ware zuordnen

**Im Geschäft:** Acme möchte vorhandene Lampen für Huber vorsehen. **In Reality:** Eine
ausdrückliche Reservierungsaktion fordert 30 Stück für diese Zusage an. Der Dienst prüft den offenen
Bedarf und den verfügbaren Bestand. Er legt eine **Reservation** über die verfügbaren acht an.

**Daraus ergibt sich:** Acht sind Huber zugeordnet, 22 sind noch nicht reserviert, null sind frei.
Noch immer sind alle 30 zu liefern. Eine Zuordnung erfüllt keine Zusage.

Die Fehlmenge ist eine berechnete Antwort. Ist nichts verfügbar, wird keine Reservation angelegt.
Die Fehlmenge erzeugt nicht automatisch eine Bestellung.

### 4. Die fehlenden Lampen bestellen

**Im Geschäft:** Acme bestellt 22 Lampen bei LightWorks. **In Reality:** Die vorgesehene
Bestellaktion legt `PO-2001`, seine Position und eine Lieferantenzusage über 22 an. Das ist
ebenfalls ein **Commitment**, diesmal von LightWorks an Acme.

**Daraus ergibt sich:** Wir erwarten 22 Lampen. Im Lager liegen weiterhin acht, alle für Huber
reserviert. Eine zugesagte Lieferung ist Planungsinformation. Sie ist noch kein vorhandener Bestand
und darf nicht als solcher versendet werden.

### 5. Teil-Wareneingang: zehn Lampen

**Im Geschäft:** LightWorks liefert zehn. **In Reality:** Acme erfasst den tatsächlichen
Wareneingang als **Movement** vom Typ `receipt`, verknüpft mit der Lieferantenzusage.

**Daraus ergibt sich:** 18 liegen im Lager; acht sind reserviert, zehn sind frei. LightWorks
schuldet noch zwölf. Der Eingang ordnet die neue Ware nicht automatisch Huber zu.

Acme reserviert deshalb die zehn neu verfügbaren Lampen mit einer eigenen Aktion für Huber. Es
entsteht eine zusätzliche Reservation. Jetzt sind 18 zugeordnet und null frei.

### 6. Die übrigen zwölf annehmen und reservieren

Der zweite Wareneingang erzeugt ein weiteres Movement über zwölf. LightWorks hat damit alle 22
geliefert. Im Lager liegen 30 Lampen; 18 sind Huber bereits zugeordnet. Eine weitere ausdrückliche
Reservierungsaktion ordnet auch die restlichen zwölf zu.

Alle 30 sind nun vorhanden und reserviert. Noch keine Lampe wurde an Huber geliefert.

### 7. In zwei Teilen liefern

**Im Geschäft:** Acme versendet zunächst 18 Lampen an Huber. **In Reality:** Acme erfasst diesen
Versand als **Movement** vom Typ `shipment` gegen Hubers Commitment. Die Aktion verbraucht die
passenden aktiven Reservierungen automatisch; dafür ist keine gesonderte Freigabe der Zuordnung
nötig.

**Daraus ergibt sich:** 18 geliefert, zwölf noch zu liefern. Zwölf liegen noch im Lager und bleiben
reserviert. Beim zweiten Versand über zwölf entstehen ein weiteres Movement und eine vollständig
erfüllte Lieferzusage. Bestand und aktive Reservierungen sind danach null.

Das Erfassen eines Movement bewegt keine Ware. Es hält den tatsächlichen Lagervorgang fest. Ob die
Ware physisch ausgegeben wurde und ob der Eintrag stimmt, bleibt eine betriebliche Verantwortung.

### Die Mengen im Zusammenhang

Alle Werte beziehen sich auf denselben Artikel und Lagerort. „Offen“ meint Hubers offene Lieferung.

| Nach diesem Schritt      | Physisch | Für Huber reserviert | Verfügbar | An Huber geliefert | Offen |
| ------------------------ | -------: | -------------------: | --------: | -----------------: | ----: |
| Anfangsbestand           |        8 |                    0 |         8 |                  0 |     0 |
| Auftrag über 30          |        8 |                    0 |         8 |                  0 |    30 |
| Erste Reservierung       |        8 |                    8 |         0 |                  0 |    30 |
| Eingang von zehn         |       18 |                    8 |        10 |                  0 |    30 |
| Weitere zehn reserviert  |       18 |                   18 |         0 |                  0 |    30 |
| Eingang von zwölf        |       30 |                   18 |        12 |                  0 |    30 |
| Weitere zwölf reserviert |       30 |                   30 |         0 |                  0 |    30 |
| Versand von 18           |       12 |                   12 |         0 |                 18 |    12 |
| Restversand von zwölf    |        0 |                    0 |         0 |                 30 |     0 |

Der Auftrag bleibt der Beleg für die Bestellung. „Teilgeliefert“ oder „vollständig geliefert“ ergibt
sich aus Commitment und den verknüpften Lieferbewegungen. Auf dem Document wird dafür kein
Lieferstatus geführt.

### Prüfe dein Verständnis

Die ersten zehn Lampen vom Lieferanten sind eingegangen, aber noch nicht reserviert. Wie viel ist
physisch vorhanden, wie viel für Huber vorgesehen und wie viel noch an ihn zu liefern?

<details>
<summary>Antwort anzeigen</summary>

Physisch 18, für Huber reserviert acht, an Huber noch zu liefern 30. Wareneingang, Zuordnung und
Kundenlieferung beantworten drei verschiedene Fragen.

</details>

<details>
<summary>Technische Vertiefung: Einträge und Teilreservierungen</summary>

Die Reservierungen in diesem Grundfall sind drei Einträge gegen dasselbe Kunden-Commitment:

```text
Reservation: commitment = HUBER-..., quantity = 8, status = active
Reservation: commitment = HUBER-..., quantity = 10, status = active
Reservation: commitment = HUBER-..., quantity = 12, status = active
```

Ein Teilversand innerhalb einer Reservation verbraucht ihren ursprünglichen Eintrag (`consumed`) und
erzeugt für den Rest einen neuen aktiven Eintrag. Die ursprüngliche Menge wird nicht überschrieben.
Ist eine Zusage vollständig erfüllt, setzt der Dienst sie auf `fulfilled`.

Eine reale Lieferantenzusage kann vor ihrem Beleg existieren. Ein tatsächlicher Wareneingang kann
auch ohne bekannte Zusage erfasst werden. Die fehlenden Beziehungen werden offengelegt.

</details>

Zum Ausprobieren: <ProductLink>Reality öffnen</ProductLink>. Nutze ein separates Lernunternehmen und
prüfe es vor jeder Bestätigung. Die Aktionen verändern dort tatsächlich Datensätze.

## Varianten getrennt vom Grundablauf

Die folgenden Fälle verändern die obige Rechnung nicht. Sie zeigen, wie du vorgehst, wenn der
Geschäftsfall anders verläuft. Überspringe die Vertiefung beim ersten Lesen und fahre mit
[Hubers Rechnung und Zahlung](./03-invoices-and-payments) fort.

<details>
<summary>Storno, Retoure, Erfassungsfehler und geänderte Aufträge</summary>

## Änderungen, Retouren und Korrekturen {#changes-and-corrections}

### Storno, Retoure und Bestandsdifferenz

Velo Store bestellt zehn Helme, sechs werden reserviert. Der Kunde storniert vor der Lieferung. Das
Commitment zu stornieren hält den Stornozeitpunkt fest und gibt aktive Reservations frei. Es
entsteht kein Movement, weil nichts bewegt wurde. Der physische Bestand bleibt unverändert; der
verfügbare Bestand steigt um sechs.

In einer eigenen Variante sendet Huber später zwei gelieferte Lampen zurück. Ein `return`-Movement
in den Retourenbereich erhöht dort den Bestand. Es löscht nicht die historische Lieferung und öffnet
nicht die erfüllte Lieferzusage erneut. Eine kaufmännische Gutschrift ist ein eigener finanzieller
Vorfall.

Eine Zählung findet dann eine fehlende Lampe. Ein ausgehendes `adjustment` aus Augsburg mit
Begründung hält die Differenz fest. Es bearbeitet keinen Bestandssaldo.

### Eine falsche Lagererfassung korrigieren

Angenommen, der Wareneingang von zehn hätte sieben sein müssen. Das Original wird nicht bearbeitet.
Eine Korrekturoperation fügt an:

1. ein exakt inverses `correction`-Movement mit Menge zehn;
2. ein normales ersetzendes `receipt`-Movement mit Menge sieben;
3. eine MovementCorrection-Beziehung, die alle drei verbindet;
4. die Abstimmung des betroffenen Commitments;
5. ein Business Event `movement.corrected`.

Netto ergeben Bestand und Erfüllung sieben. Der Inspector zeigt weiterhin, was zuerst erfasst wurde
und warum es sich geändert hat. Eine Kompensation kann selbst nicht korrigiert werden; ein falscher
Ersatz beginnt eine neue Korrekturkette.

## Kundenänderungen, Sperren und Lebenszyklus {#lifecycle}

### Wenn ein externer Kunde einen Auftrag ändert

In dieser Integrationsvariante kommt ein Auftrag aus dem Shop-System Shopify. Dessen Auftrag 4711
enthält zuerst zehn Lampen und später sieben. Die strukturierten Daten dieser Übermittlung heißen
Payload; JSON ist das verwendete Austauschformat. Version 2 überschreibt Version 1 nicht. Sie
erzeugt einen neuen SourceRecord im selben SourceStream.

Der aktuelle Shopify-Interpreter hält dieses Update als `needs_review` zur Prüfung zurück. Bisherige
Documents, Commitments, Reservations und Movements bleiben einschließlich versendeter Mengen
unverändert. Auch reine Metadatenänderungen brauchen eine Prüfung, bis automatische Anpassungen
unterstützt werden. Ein Retry umgeht diese Grenze nicht. Neues JSON macht kein physisches Ereignis
rückgängig.

Verspätete oder widersprüchliche Versionen werden eingeordnet, nicht geraten. Das
InterpretationOutcome zeigt, ob eine Version interpretiert wurde, veraltet oder widersprüchlich war
oder eine Prüfung brauchte.

### Wenn sich ein manuell erfasster Auftrag ändert

Manuelle Evidence hat eine geprüfte Korrekturoperation über einen vollständigen Snapshot.
Darstellende Felder und Referenzdaten dürfen korrigiert werden. Wirtschaftliche Positionsfelder –
Item, Menge, Einheit, Preis, Betrag, zugesagter Zeitpunkt, Positionstyp und Preisherkunft – können
nicht mehr umgeschrieben werden, sobald das Document oder die Position verknüpfte Reality hat.

Das verhindert, aus „10“ eine „7“ zu machen, während darunter ein Commitment, eine Reservation oder
ein Movement für zehn hängt. Sobald Reality existiert, gilt der ausdrückliche Lebenszyklus: offene
Zusage stornieren, Zuordnung freigeben und korrekt belegte Ersatzabsicht erzeugen. Abgeschlossene
physische oder finanzielle Vorfälle brauchen ihre eigene Retoure, Korrektur, Gutschrift oder ihr
eigenes Storno.

### Sperren und Deaktivierung

Eine Commitment-Sperre blockiert Reservierung und Fulfilment bis zur Freigabe. Ein Lieferstopp für
eine Party blockiert Kundenlieferungen für diese Party. Sperren sind eigene Datensätze mit
Begründung, Notiz, Erfasser und Freigabezeitpunkt; sie löschen die Zusage nicht.

Stammdaten zu deaktivieren verhindert neue Nutzung gemäß den Regeln des Dienstes, macht die Historie
aber nicht ungültig. Eine Rechnung behält ihre vereinbarte PaymentTerm, und eine Auftragsposition
behält ihren vereinbarten Preis samt optionaler Herkunft aus einem PriceListEntry. Spätere
Preisänderungen schreiben Evidence niemals um.

</details>

Weiter: [Rechnungen und Zahlungen](./03-invoices-and-payments).
