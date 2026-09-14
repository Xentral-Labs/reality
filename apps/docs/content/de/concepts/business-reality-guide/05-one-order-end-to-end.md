# Ein Auftrag von Anfang bis Ende

[Zurück zur Handbuchübersicht](../business-reality-guide)

## 1. Deine Verständnisprobe: Ist Hubers Auftrag erledigt?

Alle 30 Lampen sind als von Acme an Huber versendet erfasst. Zur Rechnung `INV-1001` über 1.470 EUR
sind 500 EUR Zahlung zugeordnet und 100 EUR Gutschrift angerechnet. Es gibt keine weiteren
Bewegungen, Reservierungen oder finanziellen Einträge in diesem Grundablauf.

Formuliere vor dem Weiterlesen eine Antwort auf „Ist Auftrag `SO-1001` abgeschlossen?“ Welche
Aussagen kannst du sicher treffen, und welche Information fehlt?

<details>
<summary>Antwort anzeigen</summary>

Die Lieferzusage ist erfüllt: 30 wurden zugesagt und 30 als versendet erfasst. Für diesen Auftrag
ist nichts mehr reserviert. Finanziell bleiben 870 EUR offen. Ob dieser Betrag überfällig ist, ist
ohne Fälligkeit und Bewertungsdatum nicht belegt. Die Versandbewegung allein beweist auch keine
Zustellung beim Kunden.

„Erledigt“ braucht daher eine fachliche Bedeutung. Lieferung und finanzieller Ausgleich haben
unterschiedliche Grundlagen.

</details>

## 2. Der Zusammenhang der Einträge

Diese kurze **Reality-Timeline** ist eine Erklärung, keine echte Agentenantwort und keine Zusage,
dass eine heutige Produktansicht genau diese Tabelle liefert. Sie verbindet den Lagerablauf aus
[Kapitel 2](./02-orders-stock-and-deliveries) mit der Rechnung aus
[Kapitel 3](./03-invoices-and-payments).

Die ursprüngliche Auftragsinformation ist als **SourceRecord** bewahrt. **Document** und
**DocumentLine** halten `SO-1001` fest. Das **Commitment** von Acme an Huber führt die Lieferzusage;
jede **Reservation** ordnet ihr Bestand zu und jedes erfüllende **Movement** belegt erfassten
Versand.

| Geschäftsfall                                | Maßgebliche Einträge                               | Ergebnis im Grundablauf                                 |
| -------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------- |
| Acht Lampen zu Beginn                        | Anfangsbestands-Movement                           | Acht vorhanden                                          |
| Huber bestellt 30                            | Auftrag, Position und Kunden-Commitment            | 30 zu liefern                                           |
| Vorhandene acht zuordnen                     | Reservation                                        | Acht reserviert, 22 nicht reserviert                    |
| 22 bei LightWorks bestellen                  | PO-2001 und Lieferanten-Commitment                 | 22 erwartet                                             |
| Zehn und zwölf annehmen, jeweils reservieren | Zwei Eingangs-Movement und zusätzliche Reservation | 30 vorhanden und zugeordnet                             |
| 18 und zwölf an Huber versenden              | Zwei Versand-Movement gegen das Kunden-Commitment  | 30 erfüllt, null offen; passende Reservation verbraucht |

Das Lager hat am Ende null Lampen aus diesem Grundablauf, null aktive Reservierungen und null
verfügbaren Bestand. Die Rechnung ist mit der abgerechneten Auftragsposition verknüpft; diese
Beziehung muss nicht nachträglich aus gleichen Beträgen geraten werden.

## 3. Geld bleibt eine eigene Achse

| Vorgang auf INV-1001              | Einträge und Beziehung                                             | Offener Betrag |
| --------------------------------- | ------------------------------------------------------------------ | -------------: |
| Rechnung über 1.470 EUR buchen    | Rechnungsbeleg und ausgeglichene LedgerEntry                       |      1.470 EUR |
| Zahlung über 500 EUR zuordnen     | Eigene Zahlungsbuchung und SettlementAllocation auf diese Rechnung |        970 EUR |
| Gutschrift über 100 EUR anrechnen | Eigene Gutschriftbuchung und Ausgleich dieser Rechnung             |        870 EUR |

Der Rechnungsbetrag ist ein übernommener Wert. Der offene Betrag ergibt sich aus Buchungen und
angerechneten Ausgleichen. Für diese Antworten wird kein zusätzlicher „bezahlt“-Fact angelegt.

## 4. So könnte der Agent antworten

> Die Lieferung zu Hubers Auftrag SO-1001 ist vollständig als versendet erfasst: 18 und zwölf Lampen
> gegen die Zusage über 30. Es bleibt keine aktive Reservierung für diesen Auftrag. Auf der
> verknüpften Rechnung INV-1001 sind 870 EUR offen: 1.470 EUR Rechnungsbetrag abzüglich 500 EUR
> zugeordneter Zahlung und 100 EUR angerechneter Gutschrift. Ob der Rest überfällig ist, kann ich
> ohne Prüfung der Fälligkeit nicht sagen. Als Nächstes würde ich Fälligkeit und weitere
> Zahlungseingänge prüfen. Ich habe keine Daten verändert.

In einer echten Antwort müssen Lieferung und Reservierung zu Hubers Commitment und seinen Einträgen
führen. Der offene Betrag muss zu Rechnungsbuchung, Zahlung, SettlementAllocation und Gutschrift
führen. Soweit vorhanden, lässt sich die Herkunft bis zur ursprünglichen Eingabe prüfen. Lesbare
Beispielnummern ersetzen diese technischen Verknüpfungen nicht.

Der Agent liest den aktuellen Stand und nennt seine Grenzen. Ein Vorschlag für einen nächsten
Schritt ist noch keine ausgeführte Aktion. Eine Änderung in Reality ändert nicht automatisch ein
externes ERP und löst keine Zahlung beim Anbieter aus.

## 5. Was du jetzt übertragen kannst

Retoure, Lagerkorrektur und Storno aus den Varianten in Kapitel 2 gehören **nicht zu diesem
Grundablauf**. Sobald ein solcher Fall tatsächlich eintritt, ändern seine eigenen Einträge die
Antwort. Historische Lieferungen oder Quellen werden dadurch nicht einfach gelöscht.

Für einen anderen Auftrag brauchst du dieselben Fragen: Was wurde erfasst, zugesagt, zugeordnet,
bewegt und gebucht? Welche Antwort ergibt sich daraus jetzt? Eine Arbeitsliste oder Projection hilft
beim Lesen, ersetzt aber nicht die Einträge, die sie erklären.

Offen bleibt eine andere Art von Frage: Was machst du mit einer zusätzlichen Kundeninformation wie
„Bitte am Seiteneingang liefern“? Das folgt in
[Facts und offene Fragen](./06-facts-and-open-questions).
