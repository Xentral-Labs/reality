# Ein Geschäft mit Agenten auf Reality betreiben

[![Außensysteme oben; Aufträge und Zahlungen kommen von selbst in Reality an; Lieferungen, Retourenpakete, Kundenmails und Anrufe erreichen die Schicht darüber, die sie bucht; die Schicht liest, schlägt vor, entscheidet und prüft gegen Reality; Verfügbarkeit meldet die Schicht nach außen, nicht Reality](/agent-playbooks-layers-de.svg)](/agent-playbooks-layers-de.svg)

[Auswertungen](../analytics/#so-bedient-ein-agent-die-auswertung) ergänzt die operativen Playbooks:
`graph_catalog` liefert die Datensätze und ihre Verbindungen, `graph_ask` die Antwort. Kommt eine
Ablehnung zurück, nennt sie die Beziehung, die auffächert, oder die Einheit, die sich nicht addieren
lässt.

Reality bringt keine eigenen Agenten mit und keinen Workflow-Editor. Reality stellt die Strukturen
bereit, auf denen Agenten arbeiten können: Datensätze mit klarer Herkunft, Lesewerkzeuge, die den
Bedarf zeigen, Vorschlagswerkzeuge, die eine Änderung vorbereiten, und die Seite **Decisions**, auf
der ein Mensch freigibt. Die Agenten und Workflows selbst baust du außerhalb von Reality, mit dem
Framework oder Orchestrator deiner Wahl. Sie arbeiten über MCP, API oder CLI mit genau diesen
Werkzeugen und mit keinem anderen Weg in die Daten.

Von selbst empfängt Reality nur zwei Dinge: Aufträge aus einem Shop oder einer synthetischen Quelle
und Geld aus Kontoauszug, Zahlungsanbieter oder Demodaten. Alles andere, was einen Handelsbetrieb am
Laufen hält, reservieren, versenden, abrechnen, Geld zuordnen, einkaufen, Retouren annehmen, stößt
jemand von außen an: ein Mensch in der App, dein Workflow oder dein Agent. Alle drei nutzen
dieselben geregelten Werkzeuge, und für alle drei gilt derselbe Kreislauf aus Lesen, Vorschlagen,
Entscheiden und Prüfen.

Diese Playbooks richten sich an die Person, die solche Agenten und Workflows baut. Sie sagen je
Geschäftsbereich, welche Arbeit anfällt, welches Lesewerkzeug den Bedarf zeigt, welches
Vorschlagswerkzeug die Änderung vorbereitet, was der Sachbearbeiter entscheidet und wie der Agent
das Ergebnis prüft, ohne es zu behaupten. Wie der Agent selbst gebaut oder gehostet wird, legen sie
nicht fest; das ist deine Seite der Arbeit. Die technische Referenz jedes Werkzeugs ist die
[Tool-Referenz](../tool-usage/commands); das Denkmodell steht im Kapitel
[Agentenfähigkeiten](/de/tool-usage/#choosing-a-tool) und im Guide
[Als Prozessverantwortliche/r arbeiten](../concepts/business-reality-guide/04-working-as-process-owner).

## Playbooks

- [Betriebsrhythmus](./operating-rhythm): was jeden Tag, jede Woche und jeden Monat passieren muss,
  als konkrete Aufgaben mit ihren Signalen.
- [Vertrieb und Versand](./order-to-cash-fulfilment): vom eingehenden Auftrag zur versandten
  Verpflichtung, mit Teillieferungen, geänderten Verpflichtungen, Liefersperren und alten
  Verpflichtungen.
- [Forderungen und Zahlungen](./receivables-and-payments): vom versandten Auftrag zur ausgeglichenen
  Rechnung, mit Minder-, Über-, unzugeordneten und Sammelzahlungen, Abzügen, Gutschriften und
  Erstattungen.
- [Deckungsbeitrag](./contribution-margin): DB1 und DB2 je Rechnungsposition verfolgen, fehlende
  Grundlagen erkennen, Vertriebskosten erklären und späteres Wissen nachvollziehen, ohne die
  Historie zu überschreiben.
- [Einkauf und Nachschub](./purchasing-and-replenishment): von der Fehlmenge zur bezahlten
  Lieferantenrechnung, mit Bestellungen, Wareneingängen, Rechnungsprüfung, Zahllauf,
  Lieferantenabweichungen und Gutschriften.
- [Retouren](./returns): von der angekündigten Retoure zur wieder eingelagerten Ware und zur
  ausgeglichenen Gutschrift, mit Rücknahmegebühren, Ausbuchungen, Verrechnung und Erstattung.
- [Stammdaten und Quellen](./master-data-and-sources): Kunden, Lieferanten, Artikel, Einheiten,
  Preise und Zahlungsbedingungen, registrierte Quellen, verstummte Quellen und gescheiterte
  Interpretationen.

## Der Kreislauf, dem jedes Playbook folgt

```text
lesen  ──►  Vorschlag vorbereiten  ──►  ein Mensch entscheidet  ──►  prüfen
Werkzeuge   *_propose-Werkzeuge         Seite Decisions              erneut lesen
```

1. **Lesen.** Lesezugriffe laufen sofort und ändern nichts: `fulfillment_queue`, `exceptions_list`,
   `finance_settlement_context`, `order_explain` und die übrigen. Jede Antwort nennt die Datensätze,
   auf denen sie beruht; ein Lesezugriff ist auch die Art, wie ein Agent eine Aussage belegt.
2. **Vorbereiten.** Jede Änderung ist ein `*_propose`-Werkzeug. Es prüft die Eingabe, zeigt die
   genaue Wirkung und speichert einen Vorschlag. In Reality ändert sich noch nichts.
3. **Entscheiden.** Der Vorschlag erscheint in der App unter **Decisions** mit Vorschau, betroffenen
   Datensätzen und erwarteter Wirkung. Ein Mensch gibt frei oder lehnt ab. Ein Agent darf über
   `proposal_approve_and_execute` nur dort freigeben, wo dein Unternehmen ihm das für eine
   Fallklasse ausdrücklich erlaubt hat; ein „mach mal" im Chat ist keine Freigabe.
4. **Prüfen.** `proposal_execution_status` liefert den Beleg und gleicht ihn mit den jetzt
   vorhandenen Datensätzen ab; ein weiterer Lesezugriff (`order_explain`, `finance_balances`) zeigt
   das neue Bild. Ein Agent berichtet, was der Lesezugriff zeigt, nicht, was er wollte.

Zwei Regeln machen den Kreislauf sicher. Beträge und Mengen werden genannt, nie von Reality aus
einem Satz oder einer Formel berechnet; der Vorschlag trägt den Wert, den jemand genannt hat. Und
eine Lesezeit-Beobachtung, ein Kandidat, eine Fehlmenge, eine Abweichung, wird nie als Entscheidung
gespeichert.

## Was von selbst kommt und was nicht

Nur Aufträge und Zahlungen kommen von selbst (grün). Lieferungen an der Rampe, Retourenpakete,
Kundenmails und Anrufe erreichen die Schicht darüber (grau), die sie bucht: Wareneingänge, Retouren,
Ankündigungen, Liefersperren, Gutschriften, offene Fragen. Auch nach außen geht nichts von selbst
(orange): Die Verfügbarkeit für Shop oder Marktplatz liest ein Workflow und sendet sie. Die blaue
Schicht ist deine und liegt außerhalb von Reality: dein Agent oder Workflow. Reality gibt ihr
Leitplanken, Vorschlag, Vorschau, Ablehnung und Entscheidung; wie viel Routine ohne Rückfrage läuft,
legst du im Agenten fest, bei Zweifel und Neuem entscheidet ein Mensch. Reality hält die Datensätze,
leitet den Zustand ab und meldet Abweichungen.

| Kommt von selbst                                                                                                            | Muss orchestriert werden                                                                                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Aufträge aus einem angebundenen Shop oder aus Demodaten, als Auftragsbelege mit einer Lieferverpflichtung je Position       | Bestand reservieren, ganz oder in Teilen versenden, eine Verpflichtung ändern oder anhalten, alte Verpflichtungen schließen                                                                                                           |
| Kundenzahlungen aus Kontoauszug, Anbieter oder Demodaten, erfasst und bei eindeutigem Bezug zugeordnet                      | Rechnungen für versandte Ware, Entscheidungen zu Minder- und Überzahlungen, Zuordnung von Zahlungen ohne brauchbaren Bezug, Gutschriften und Erstattungen                                                                             |
| Abweichungen, die aus all dem abgeleitet werden                                                                             | Bestellungen, Wareneingänge, Lieferantenrechnungen, der Zahllauf, Retouren, Stammdaten                                                                                                                                                |
| Sonst nichts: Lieferungen an der Rampe, Retourenpakete, Kundenmails und Anrufe erreichen die Schicht darüber, nicht Reality | Wareneingänge und Retouren buchen, Mails und Anrufe in Ankündigungen, Liefersperren, Gutschriften oder offene Fragen verwandeln; Verfügbarkeit an Shop oder Marktplatz melden, indem ein Workflow Bestand und Bedarf liest und sendet |

## Das tägliche Minimum

Ein Agent oder Workflow, der diese sechs Dinge jeden Tag tut, hält einen kleinen Händler auf Reality
am Laufen:

1. **Die Versandliste leeren.** `fulfillment_queue` lesen; reservieren, was verfügbar ist,
   versenden, was bereit ist, anhalten, was warten muss. Siehe
   [Vertrieb und Versand](./order-to-cash-fulfilment).
2. **Abrechnen, was versandt ist.** `exceptions_list` auf `shipped_not_billed` und
   `sales_invoice_unposted` lesen; Rechnungen erfassen und buchen. Siehe
   [Forderungen und Zahlungen](./receivables-and-payments).
3. **Das Geld bearbeiten.** `exceptions_list` auf `unmatched_financial_event` und
   `overdue_receivable` lesen; Zuordnungen für Zahlungen mit Kandidaten vorschlagen; die
   Entscheidung über Reste und Guthaben dem Menschen lassen. Gleiches Playbook.
4. **Den Nachschub beobachten.** `item_supply_demand` auf `uncovered_demand` lesen und Bestellungen
   vorbereiten. Siehe [Einkauf und Nachschub](./purchasing-and-replenishment).
5. **Entscheiden.** `proposals_awaiting_approval` lesen; sicherstellen, dass ein Mensch jeden
   offenen Vorschlag sieht, oder die Klassen freigeben, die dein Unternehmen delegiert hat.
6. **Prüfen und berichten.** Lesen, was du geändert hast. Das Gelesene berichten.

## Wie ein Playbook zu lesen ist

Jedes Playbook hat dieselbe Form. Eine Situation ist eine Zeile Kontext und wenige nummerierte
Schritte mit festen Schlüsselwörtern: **Liste** oder **Sehen** (was du aufrufst und was es zeigt),
**Sagen** (was du dem Agenten sagst), **Agent** (was er vorbereitet), **Du** (was du entscheidest),
**Prüfen** (was es beweist). Der Lesezugriff, die Abweichungsklasse oder der Vorschlag hinter einem
Schritt steht am Zeilenende nach einem Pfeil. Freigegeben wird unter Entscheidungen in der App
(`proposals_awaiting_approval`), durch einen Menschen oder durch deinen Agenten für die Routine, die
du ihm überlassen hast. Ein Schlussabschnitt nennt, was noch nicht geht, damit ein Agent es nicht
verspricht.
