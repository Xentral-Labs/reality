# Bestandskosten, DB1 und DB2

[Zurück zur Übersicht](../business-reality-guide)

## Was die beiden Deckungsbeiträge bedeuten

Das Deckungsbeitragsprofil `commercial_v1` beantwortet, was vom empfangenen Nettoerlös nach zwei
getrennt geprüften Kostenstufen übrig bleibt:

```text
DB1 = empfangener Nettoerlös − verbrauchte Anschaffungskosten
DB2 = DB1 − direkte Vertriebskosten − zugeordnete Vertriebskosten
DB2-Quote = DB2 ÷ empfangener Nettoerlös, sofern dieser positiv ist
```

DB1 zeigt damit, ob der Verkauf die Kosten der verbrauchten Ware oder direkt verbrauchten Leistung
deckt. DB2 berücksichtigt zusätzlich die belegten Vertriebskosten dieses Verkaufs. Das ist eine
kaufmännische Deckungsbeitragsrechnung, keine handelsrechtliche Gewinn-und-Verlust-Rechnung.
Produktfixkosten, allgemeine Gemeinkosten, Steuerergebnis, Cashflow und gesetzliche
Bestandsbewertung sind andere Fragen, solange kein weiteres benanntes Profil sie ausdrücklich
einschließt.

Die wichtigste Regel lautet: **Reality erfindet aus unvollständigen Eingaben keinen vollständigen
Deckungsbeitrag.** DB1 kann belastbar sein, während DB2 unbekannt bleibt. Unbekannt ist nicht null.

## Vom Beleg bis zur angezeigten Zahl

```text
Lieferantenbeleg
  → empfangene finanzielle Kostenbestandteile
  → ausdrückliche Zuordnung und Prüfung der Anschaffungskosten
  → geprüfte Wareneingangskosten
  → geprüfte Bestandsmethode, Eigentümerschaft und Bewegungshistorie
  → verbrauchte Anschaffungskosten der fakturierten und erfüllten Verkaufsposition

Kundenrechnungsposition
  → empfangener Nettoerlös des exakten kaufmännischen Umfangs
  → DB1

Belege zu Vertriebskosten
  → direkte oder zugeordnete Zuordnung zur Verkaufsposition
  → eigenständige Prüfung aller Vertriebskosten-Kategorien
  → DB2

Jedes Ergebnis
  → festgehaltenes Review und Generation
  → Inspector-Links zu Entscheidungen, Belegen und ursprünglichem Quellpayload
```

Der Browser rechnet diese Werte nicht selbst. Er fragt den gemeinsamen Kostenservice ab und zeigt
dessen Ergebnis, Status und Nachweiskette. CLI, Chat, MCP und Webanwendung verwenden dieselben
Services.

## Welche Werte in die Rechnung eingehen

| Stufe                       | Was Reality verwendet                                                                                                                             | Was Reality bewusst nicht ableitet                                                      |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Erlös                       | Empfangener Nettoerlös der unterstützten Kundenrechnungsposition und ihrer zugeordneten erfüllten Menge                                           | Erlös aus Zahlung, Brutto minus selbst rekonstruierter Steuer oder fremde Auftragssumme |
| Warenkosten                 | Tatsächlich verbrauchte Kosten aus geprüften Wareneingangs- oder Anfangsbestands-Schichten nach bestätigtem FIFO oder spezifischer Identifikation | Aktueller Einkaufspreis, Listenpreis, Lagerort oder erfundener Durchschnitt             |
| Anschaffungsnebenkosten     | Zugeordnete Eingangsfracht, Zoll, sonstige Anschaffungskosten und belegte nicht abzugsfähige Vorsteuer                                            | Abzugsfähige Vorsteuer oder nicht zugeordnete Lieferantenbelastung                      |
| Einkaufsminderungen         | Ausdrücklich belegte und zugeordnete Lieferantenminderungen                                                                                       | Zahlungsdifferenz als Skonto ohne Beleg                                                 |
| Direkte Vertriebskosten     | Direkt dieser Verkaufsposition zugeordnete Kostenbelege                                                                                           | Implizite Zuordnung über Betrag, Kunde oder Datum                                       |
| Zugeordnete Vertriebskosten | Kostenbeleg, der mit einer ausdrücklich gewählten unterstützten Verteilung zugeordnet wurde                                                       | Automatisch gewählter Verteilungsschlüssel oder pauschale Gemeinkostenumlage            |

Anschaffungs- und Vertriebskosten sind getrennte Familien. Derselbe empfangene Kostenbestandteil
darf nicht in DB1 und erneut in DB2 eingehen. Geprüfte Vertriebskosten-Kategorien sind
Ausgangsfracht, Fulfilment, Verpackung, Zahlungsgebühr, Marktplatzprovision, Vertriebsprovision und
sonstige Vertriebskosten.

## Ein vollständiges Beispiel

Das kanonische vollständige Beispiel umfasst 60 erfüllte und fakturierte Stück:

| Deckungsbeitragsbrücke         |      Betrag |
| ------------------------------ | ----------: |
| Empfangener Nettoerlös         |   1.200 EUR |
| Verbrauchte Anschaffungskosten |   − 630 EUR |
| **DB1**                        | **570 EUR** |
| Direkte Vertriebskosten        |    − 90 EUR |
| Zugeordnete Vertriebskosten    |    − 24 EUR |
| **DB2**                        | **456 EUR** |
| **DB2-Quote**                  |    **38 %** |

Die 630 EUR sind nicht `60 × heutiger Einkaufspreis`. Es sind die exakt verbrauchten Kosten aus den
geprüften Bestandsschichten. Die 90 EUR und 24 EUR bleiben getrennt sichtbar, damit prüfbar ist,
welche Vertriebskosten direkt und welche verteilt zugeordnet wurden.

Ist das Vertriebskosten-Review unvollständig, kann derselbe Fall weiterhin einen belastbaren DB1 von
570 EUR zeigen, während DB2 unbekannt bleibt. Wurden alle sieben Kategorien ausdrücklich mit null
oder „nicht anwendbar“ geprüft, darf DB2 gleich DB1 sein. Eine leere Prüfliste bedeutet nie null.

## Wann das Ergebnis berechnet wird

Reality leitet die Geldbeträge beim Lesen aus festgehaltenen Eingaben ab. DB1 und DB2 werden nicht
als neue finanzielle Autorität gespeichert. Für verlässliche Unternehmensauswertungen kann ein
Hintergrundjob aus einer eingefrorenen Bestandsaufnahme eine Generation erzeugen und diese nach
Prüfung veröffentlichen. Auch dann bleiben die Werte abgeleitete Beobachtungen mit exakt
festgehaltener Mitgliedschaft.

Zwei Zeitpunkte sind immer wichtig:

- **Bewertungsstichtag:** die wirtschaftliche Grenze. Nur unterstützte Bewegungen und Vorgänge bis
  zu diesem Zeitpunkt gehören in die Antwort.
- **Wissensstand:** welche Belege und Reviews beim Versiegeln der Grundlage vorlagen.

Eine spätere Rechnung, Zuordnung, Bewegungskorrektur oder relevante Prüfung überschreibt keine alte
Antwort. Sie erfordert ein neues Review oder eine neue Generation. Eine historische Auswahl stellt
die frühere Grundlage exakt wieder her.

## Erst den Status verstehen, dann den Betrag lesen

| Status                        | Geschäftliche Bedeutung                                                     | Richtiger Umgang                                                         |
| ----------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **Bereit / aktuell**          | Mitgliedschaft und erforderliche Reviews sind für die Stichtage vollständig | Ergebnis für den angegebenen Umfang verwenden                            |
| **Historisch**                | Ein bestimmtes früheres Review oder eine Generation wurde gewählt           | Erklärt den damaligen Wissensstand, nicht den heutigen Wert              |
| **Veraltet**                  | Spätere relevante Evidenz liegt vor                                         | Grundlage prüfen und ein aktualisiertes Review bestätigen                |
| **Ausstehend**                | Eine angeforderte Generation ist noch nicht geprüft und veröffentlicht      | Auf den gemeinsamen Worker warten; alten Wert nicht als aktuell ausgeben |
| **Unbekannt / unvollständig** | Beleg, Zuordnung oder Review fehlt                                          | Benannte Lücke schließen; niemals als null interpretieren                |
| **Keine Aktivität**           | Der vollständig geprüfte Umfang enthält keinen passenden Vorgang            | Geprüfter leerer Umfang, klar getrennt von fehlender Evidenz             |

Summen bewahren ihre Abdeckung. Ein Bericht kann den bekannten DB1 der abgedeckten Positionen zeigen
und getrennt nennen, wie viele Positionen insgesamt erforderlich sind. Er darf nie unvollständige
Kostensummen von allen Erlösen abziehen und das Ergebnis als vollständig bezeichnen.

## So wird der Prozess bedient

1. **Evidenz empfangen.** Lieferantenrechnungen, Gutschriften, Kundenrechnungen und Bewegungen
   gelangen über die normalen Quellen und Anwendungen in Reality. Quellwerte bleiben unverändert.
2. **Kostenbestandteile zuordnen.** Ein Owner sieht eine Vorschau und bestätigt, wohin ein
   empfangener Anschaffungs- oder Vertriebskostenbestandteil gehört. Restbeträge bleiben sichtbar.
3. **Wareneingang prüfen.** Alle Anschaffungskosten-Kategorien erhalten eine begründete Beurteilung.
   Null und „nicht anwendbar“ sind ausdrückliche Entscheidungen; Fehlen ist keine.
4. **Bestand prüfen.** Der Owner bestätigt wirtschaftliches Eigentum, Währung, Basiseinheit,
   Stichtag, vollständige Bewegungshistorie und FIFO oder spezifische Identifikation. Reality prüft,
   dass im begrenzten Umfang nichts ausgelassen wurde.
5. **Deckungsbeitrag prüfen.** Erlös und erfüllte Menge werden der exakten Verkaufsposition
   zugeordnet. Damit kann DB1 final werden. Die eigenständige Vertriebskosten-Prüfliste kann danach
   DB2 finalisieren.
6. **Berichtsumfang erzeugen und veröffentlichen.** Unternehmensweite Bestandsaufnahme,
   festgehaltene Grundlage und Generation frieren die exakte Mitgliedschaft für wiederholbare
   Berichte ein. Worker rechnen; sie genehmigen keine finanziellen Entscheidungen.
7. **Prüfen und aktualisieren.** Operative Hinweise melden fehlende Anschaffungskosten, nicht
   zugeordnete Kosten, veraltete Reviews oder negativen tatsächlichen DB1. Ein Mensch folgt der
   Nachweiskette, korrigiert die Evidenz oder bestätigt ein neues Review und baut anschließend den
   betroffenen Berichtsumfang neu.

Jede verändernde Kostenentscheidung verlangt Vorschau und ausdrückliche Owner-Bestätigung. Weder
Scheduler noch Worker oder Agent dürfen still eine Methode aktivieren oder eine Kostenzuordnung
genehmigen.

## Die Erklärung im Produkt lesen

Die Deckungsbeitragserklärung zeigt empfangenen Nettoerlös, verbrauchte Anschaffungskosten, DB1,
geprüfte Vertriebskosten, DB2 sowie Bewertungsstichtag und Wissensstand. Die normale Geldanzeige
folgt dem Zahlenformat des Benutzers; daneben bewahrt der exakte gespeicherte Wert die vier
Nachkommastellen des Services. Stückkosten behalten bis zu sechs Nachkommastellen, sofern geliefert.

Über **Kostengrundlage prüfen** lässt sich das Ergebnis durch Deckungsbeitrags-Review,
Bestands-Review, Wareneingangsmanifeste, Kostenzuordnungen, Belege und ursprüngliche Quellen
verfolgen. Der Inspector ist der Prüfpfad; es gibt keine zweite Rechnung nur im Browser.

Für ein Management-Review helfen diese Fragen in genau dieser Reihenfolge:

1. Ist das Ergebnis aktuell, historisch, veraltet, ausstehend oder unvollständig?
2. Welche Bewertungs- und Wissensstichtage gelten?
3. Wie viele erforderliche Positionen sind abgedeckt?
4. Welche Beträge sind Nettoerlös, verbrauchte Anschaffungskosten, direkte und zugeordnete
   Vertriebskosten?
5. Welche bestätigten Reviews und Quellbelege tragen diese Werte?
6. Sind Währungen, Basiseinheiten und wirtschaftliches Eigentum kompatibel oder ist ein
   Umrechnungsbeleg angegeben?

## Häufige Missverständnisse

- **„Es gibt keinen Vertriebskostenbeleg, also ist DB2 gleich DB1.“** Nein. DB2 bleibt unbekannt,
  bis jede Vertriebskosten-Kategorie belegt, ausdrücklich null oder nicht anwendbar ist.
- **„Die Rechnung existiert, also reicht der Erlös.“** Nein. Finaler DB1 braucht außerdem eine
  kompatible erfüllte Menge und geprüfte verbrauchte Anschaffungskosten.
- **„Nimm einfach den neuesten Lieferantenpreis.“** Nein. Reality folgt den bestätigten verbrauchten
  Bestandsschichten.
- **„Eine Zahlung beweist den Erlös für DB1.“** Nein. Zahlung und Zuordnung beantworten Cash- und
  Forderungsfragen; die unterstützte Rechnungsposition liefert den kaufmännischen Erlös.
- **„Der Lagerort zeigt, wem der Bestand gehört.“** Nein. Physischer Besitz und wirtschaftliches
  Eigentum sind getrennt; Misch-, Konsignations- und Transitbestand brauchen ausdrückliche Evidenz.
- **„Ein neuer Vorgang aktualisiert den alten Bericht.“** Nein. Historie bleibt reproduzierbar; es
  braucht eine neue Grundlage und Generation.
- **„DB2 ist der Unternehmensgewinn.“** Nein. DB2 ist das Ergebnis des benannten Umfangs
  `commercial_v1`.

## Das Kontrollprinzip

Reality trennt, was eine Quelle ausgesagt hat, was ein Owner entschieden hat und was das System
daraus ableitet. Deshalb lässt sich der Deckungsbeitrag wiederholen, hinterfragen und erklären, ohne
die Berechnung zu einer zweiten finanziellen Autorität zu machen.

Weiter: [Zusammenfassung](./07-model-at-a-glance). Die exakten Datensätze und Werkzeuge findest du
unter [Tools nutzen](../../tool-usage/) und in der [Tabellenübersicht](../../reference/table-map).
