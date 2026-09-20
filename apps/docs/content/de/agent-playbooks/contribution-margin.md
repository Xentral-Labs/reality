# Playbook: Deckungsbeitrag (DB1 und DB2)

Nutze dieses Playbook, wenn ein Agent eine Margenfrage für genau eine empfangene
Verkaufsrechnungsposition beantworten soll. Es ist der kurze operative Weg durch das Modell; das
Kapitel
[Bestandskosten und Deckungsbeitrag](../concepts/business-reality-guide/08-inventory-cost-and-contribution)
erklärt die fachliche Logik ausführlich.

## Was der Agent verfolgt

```text
DB1 = empfangener Nettoerlös − geprüfte verbrauchte Anschaffungskosten
DB2 = DB1 − geprüfte direkte Vertriebskosten − geprüfte umgelegte Vertriebskosten
```

Reality behandelt eine fehlende Grundlage niemals als null. Ein negativer DB2 ist ein gültiges
geprüftes Ergebnis; **Nicht belegt** bedeutet, dass noch kein ehrliches Ergebnis existiert.

## Situationsübersicht

| Geschäftssituation                         | Erster Lesezugriff                                   | Was er klärt                                                                | Nächster Schritt bei Lücken                                                                |
| ------------------------------------------ | ---------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| DB1/DB2 einer Rechnungsposition erklären   | `cost_query_get kind=contribution scope_id=<line>`   | Erlös, Verbrauch, Vertriebskosten, Stichtage und fehlende Grundlagen        | Der unten beschriebenen fehlenden Grundlage folgen                                         |
| Aktuellen Kandidaten vor der Prüfung sehen | `cost_contribution_preview document_line_id=<line>`  | Exakter Erlös-/Verbrauchskandidat und Candidate Hash                        | Benötigte Prüfung mit `cost_change_propose` vorbereiten                                    |
| DB1 fehlt                                  | `cost_commercial_match_get document_line_id=<line>`  | Ob die Position geprüft mit dem exakten Bestandsverbrauch verbunden ist     | Falls nötig zuerst Bestand prüfen, dann `commercial_match_review` vorschlagen              |
| DB2 fehlt                                  | `cost_query_get kind=contribution scope_id=<line>`   | Welche Vertriebskostenkategorie oder Zuordnung unbekannt ist                | `selling_assign`, danach `contribution_review` vorschlagen; echte null ausdrücklich prüfen |
| DB2 ist niedrig oder negativ               | `cost_query_get kind=contribution scope_id=<line>`   | Exakte Brücke vom Erlös über DB1 und Vertriebskosten zu DB2                 | Belege prüfen; ein gültiges negatives Ergebnis nicht „korrigieren“                         |
| Wissen kam später                          | `cost_query_get` mit `review_id` oder `knowledge_at` | Welche Antwort an dieser Wissensgrenze möglich war                          | Alte und neue Prüfung vergleichen; die alte Erklärung nie überschreiben                    |
| Portfolio vergleichen                      | `graph_contribution_reviews_list`, danach Analytics  | Bestätigte Prüfungen und anschließend eine ausdrücklich fixierte Population | Vor der Aggregation die gewünschte Deckungsbeitragsgrundlage festhalten                    |

Alle Identitäten sind opake IDs aus einem vorherigen Lesezugriff. Eine Rechnungsnummer hilft einem
Menschen beim Finden; sie ist niemals die technische Identität.

## Situation: einen geprüften DB1 und DB2 erklären

1. **Sehen:** Rechnung in **Finance** öffnen, Position aufklappen und die Deckungsbeitragserklärung
   öffnen.
2. **Agent:** `cost_query_get` mit `kind=contribution` und der opaken Positions-ID lesen.
3. **Prüfen:** zuerst Erlös, verbrauchte Anschaffungskosten und DB1; danach direkte und umgelegte
   Vertriebskosten und DB2. Bewertungs- und Wissensstichtag zusammen mit den Beträgen lesen.
4. **Berichten:** Ergebnis und Status nennen. Eine vollständige Antwort nennt die gehaltene Prüfung;
   eine unvollständige nennt `missing_basis` statt einer Schätzung.

Dieser Ablauf liest nur. Er erzeugt keine neue finanzielle Autorität.

## Situation: DB1 ist nicht belegt

1. **Agent:** `cost_contribution_preview` lesen. Die Antwort muss die fehlende Commercial- oder
   Bestandsgrundlage nennen, statt DB1 anzuzeigen.
2. **Agent:** `cost_commercial_match_get` lesen. Ein geprüfter Commercial Match muss genau diese
   Rechnungsposition mit dem exakten geprüften Verbrauch verbinden.
3. **Du:** Quellen für Zugang/Eröffnung, Eigentum, Abgang und Anschaffungsbetrag prüfen.
4. **Agent:** `cost_change_propose` für `inventory_review` oder `inventory_batch_review` und danach
   für `commercial_match_review` vorbereiten.
5. **Du:** Vorschläge unter **Decisions** freigeben.
6. **Prüfen:** `cost_contribution_preview` erneut lesen. DB1 erscheint erst, wenn empfangener
   Nettoerlös und geprüfter verbrauchter Anschaffungswert bekannt sind.

Trage keinen bequemen Einstandspreis ein, nur damit DB1 erscheint. Der Anschaffungsbetrag muss aus
empfangener Evidenz oder einer ausdrücklich geprüften Eröffnung stammen.

## Situation: DB1 existiert, DB2 aber nicht

1. **Agent:** `cost_query_get` lesen und jede fehlende Vertriebskostenkategorie nennen.
2. **Du:** echte Kosten von echter null unterscheiden. Fracht, Marktplatzprovision, Verpackung,
   Zahlungsgebühr, Vertriebsprovision und sonstige Vertriebskosten brauchen Evidenz oder eine
   ausdrücklich geprüfte Null-/Nicht-zutreffend-Entscheidung.
3. **Agent:** `cost_change_propose operation=selling_assign` für belegte Anteile einer
   Lieferantenaufwendung vorbereiten. Direkte Anteile gehören zu einer Verkaufsposition; umgelegte
   Anteile nennen ihre Verteilung.
4. **Agent:** `cost_contribution_preview` aktualisieren und
   `cost_change_propose operation=contribution_review` mit exaktem Candidate Hash und vollständiger
   Kategorienprüfung vorbereiten.
5. **Du:** freigeben. **Prüfen:** `cost_query_get` muss DB2 exakt als DB1 minus direkte und
   umgelegte Vertriebskosten abstimmen.

Null ist kein Standardwert. Der Demo-Fall ohne Vertriebskosten ist vollständig, weil jede Kategorie
als null oder nicht zutreffend geprüft wurde.

## Situation: DB2 ist unerwartet niedrig oder negativ

1. **Agent:** `cost_query_get` lesen und Prüfungs- sowie Stichtagsidentitäten festhalten.
2. **Prüfen:** die Brücke in dieser Reihenfolge lesen: empfangener Nettoerlös → verbrauchte
   Anschaffungskosten → DB1 → direkte Vertriebskosten → umgelegte Vertriebskosten → DB2.
3. **Agent:** Commercial Match, Bestandsprüfung, Zuordnungen und Source Records verfolgen und den
   treibenden Bestandteil benennen.
4. **Du:** nur ändern, wenn Evidenz oder Prüfung falsch ist. Ein negativer DB2 ist allein keine
   Abweichung; er kann einen unrentablen Verkauf wahrheitsgemäß zeigen.

## Situation: Kosten oder Wissen kommen später

1. **Agent:** die alte Antwort mit `review_id` oder `knowledge_at` lesen.
2. **Agent:** die aktuelle Antwort getrennt lesen.
3. **Berichten:** was damals und was heute bekannt ist. Eine spätere Lieferantenrechnung, Retoure
   oder Prüfung erzeugt eine neue Wissensgrenze; sie überschreibt die frühere nicht.
4. **Prüfen:** Freshness in `cost_query_get` lesen. Eine aktuelle Prüfung niemals so darstellen, als
   hätte sie bereits an einem früheren Stichtag existiert.

## Situation: Rechnungen oder ein Portfolio vergleichen

1. **Agent:** mit `graph_contribution_reviews_list` bestätigte Deckungsbeitragsprüfungen finden.
2. **Du:** Population und gehaltene Kostengrundlage für den Vergleich auswählen.
3. **Agent:** Analytics nur mit diesem ausdrücklichen Contribution-Cost-Kontext nutzen; unabhängig
   geprüfte Generationen dürfen nicht still vermischt werden.
4. **Prüfen:** Ausreißer vor einer Entscheidung mit der Einzelpositions-Erklärung aus
   `cost_query_get` nachvollziehen.

Für einen schnellen Rundgang legst du eine neue Firma mit Demodaten an und vergleichst die sechs
`COST-PORTFOLIO-*`-/Fixture-Ergebnisse aus dem
[durchgerechneten Demo-Portfolio](../concepts/business-reality-guide/08-inventory-cost-and-contribution#das-demo-portfolio-vergleichen).

## Was der Agent niemals behaupten darf

- Kein DB1 ohne geprüften Commercial Match und geprüfte verbrauchte Anschaffungskosten.
- Kein DB2, solange eine Vertriebskostenkategorie unbekannt ist.
- Niemals fehlend mit null gleichsetzen.
- Rechnungsnummern niemals als Datensatzidentität verwenden.
- Keine historische Aussage ohne gehaltenen Bewertungs- und Wissensstichtag.
- Kein direkter Write: Jede Prüfung oder Zuordnung ist ein Vorschlag über denselben Application
  Service wie App, CLI und API.
