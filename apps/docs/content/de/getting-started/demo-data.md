# Demo-Datensatz

Die kanonische Demo-Firma ist ein reproduzierbares, synthetisches Handelsunternehmen.
Hier siehst du vollständige und problematische Geschäftsabläufe in Vertrieb, Einkauf,
Lager, Finance und Analytics. Die Referenzen unten sind suchbare Bezeichnungen und
keine technischen IDs.

Jeder Demo-Beleg hat ein Belegdatum. Ein Strich beim Fälligkeitsdatum bedeutet nur,
dass die Quelle keine Fälligkeit genannt hat – nicht, dass der Beleg kein Datum hat.

## Firma und Verwendung der Referenzen

Die Basis enthält 16 Artikel (`P01`–`P16`), 20 Kunden, drei Lieferanten sowie die Lager
Rotterdam und Singapur. Mengen werden in Stück, Metern oder Kilogramm geführt. Die
meisten Vorgänge sind in EUR; zwei Rechnungen verwenden bewusst USD.

Suche nach einer Referenz und öffne danach den Auftrag, die Rechnung, Bewegung oder den
Finance-Eintrag. Von wichtigen Werten gelangst du über den Reality-Datensatz und den
Beleg bis zur ursprünglichen synthetischen Quelle. Dieselbe Profilversion erzeugt in
jeder neuen Firma dieselben Fälle.

## Verkauf und Lieferung

| Referenz | Was du prüfen kannst | Erwartetes Ergebnis |
| --- | --- | --- |
| `O01` | Reservierung | 5 Stück reserviert |
| `O02` | Bestand ohne Reservierung | 5 bestellt, 10 auf Lager, nichts reserviert |
| `O03` | Bestandsengpass | 5 bestellt, aber nur 2 verfügbar |
| `O04` | Teilreservierung | 2 Stück eines überfälligen Auftrags reserviert |
| `O06` | Teillieferung | 3 von 5 Stück versendet; 2 bleiben offen |
| `O07`, `O08` | Manuelle Sperre | Die Zusage ist gesperrt und weiter erklärbar |
| `O09` | Vollständige Lieferung | 5 von 5 Stück versendet |
| `O10` | Storno vor Versand | Die Reservierungshistorie bleibt sichtbar |
| `O11` | Storno nach Teillieferung | 2 Stück bleiben versendet; der Rest ist storniert |

Die datierten `H-*`-Aufträge und Rechnungen zeigen vergleichbare Mengen-, Preis-,
Rückgangs-, Ausreißer-, Nullwert- und USD-Zeiträume. Es gibt offene, teilweise und
vollständig bezahlte Rechnungen.

Aufträge sind Nachweise, kein Lieferstatus. Die Lieferzusage ist ein Commitment,
Reservierungen sind eigene Datensätze und nur Movements verändern den physischen
Bestand. Ein Storno von `O10` oder `O11` löscht daher keine bereits erfolgte
Reservierung oder Lieferung.

## Historische Verkäufe und Rechnungen

| Referenz | Angegebener Vorgang | Ausgleich | Zweck |
| --- | --- | --- | --- |
| `H-volume-prior` | 10 × `P11`, 200 EUR | Bezahlt | Frühere Mengenbasis |
| `H-volume-current` | 20 × `P11`, 400 EUR | Bezahlt | Aktueller Mengenvergleich |
| `H-price-prior` | 10 × `P12`, 200 EUR | Bezahlt | Frühere Preisbasis |
| `H-price-current` | 10 × `P12`, 250 EUR | Teilbezahlt | Gleiche Menge, höherer Preis |
| `H-decline-prior` | 20 × `P13`, 300 EUR | Bezahlt | Frühere Nachfragebasis |
| `H-decline-current` | 5 × `P13`, 75 EUR | Offen | Sichtbarer Absatzrückgang |
| `H-credit-origin` | 10 × `P14`, 120 EUR | Durch Gutschrift ausgeglichen | Ursprung der Vollretoure |
| `H-outlier-prior` | 10 × `P15`, 50 EUR | Bezahlt | Normaler Vergleichswert |
| `H-outlier-current` | 1.000 × `P15`, 5.000 EUR | Offen | Bewusster Ausreißer |
| `H-zero-current` | 8 × `P16`, 80 EUR | Offen | Angegebener Vergleich, kein fehlender Wert |
| `H-usd-prior` | 4 × `P09`, 88 USD | Bezahlt | Frühere Fremdwährungsdaten |
| `H-usd-current` | 6 × `P09`, 132 USD | Bezahlt | Aktuelle Fremdwährungsdaten |

Jeder Fall enthält Auftrag, Liefer-Commitment, datierte Rechnung, Anfangsbestand und
Versandbewegung. Zahlungen sind eigene Belege und Buchungen: Bezahlt bedeutet nicht
geliefert, und geliefert bedeutet nicht bezahlt.

## Kundenretouren und Gutschriften

| Referenz | Was du prüfen kannst | Erwartetes Ergebnis |
| --- | --- | --- |
| `H-credit-origin` / `CR-001` | Vollständige Retoure und Gutschrift | 10 von 10 Stück retourniert; 120 EUR zugeordnet |
| `COST-A` / `COST-LATE-CREDIT` | Teilretoure mit Kosten | 10 von 60 Stück retourniert, mit exakter Kostenherkunft |

`COST-A` ist das ausführliche Retouren- und Deckungsbeitragsbeispiel. Der ursprüngliche
Lagerabgang, die retournierte Bestandsschicht, die Kundengutschrift und die
Vertriebskosten gehören zu einer gemeinsamen geprüften Kostenbasis.

`CR-001` ist ausdrücklich der ursprünglichen Rechnung zugeordnet; die Forderung ist
danach null. `COST-LATE-CREDIT` behält für die zehn retournierten Stück exakt die
ursprüngliche Kostenschicht, statt einen neuen Einkaufspreis zu erfinden.

## Einkauf und Verbindlichkeiten

| Referenz | Wareneingang | Rechnung und Zahlung | Zweck |
| --- | ---: | --- | --- |
| `PO-001` / `S01` | 2 von 5 | Keine Rechnung | Teilwareneingang |
| `PO-002` / `S02` | 5 von 5 | Bezahlt | Vollständiger Purchase-to-Pay-Ablauf |
| `PO-003` / `S03` | 0 von 5 | Keine Rechnung | Offene Einkaufsbestellung |
| `PO-004` / `S04` | 5 von 5 | Teilbezahlt | Teilzahlung an Lieferanten |
| `PO-005` / `S05` | 5 von 5 | Unbezahlt | Offene Verbindlichkeit |
| `PO-006` / `S06` | 5 von 5 | Keine Rechnung | Wareneingang wartet auf Rechnung |
| `PO-007` / `S07` | 5 erhalten, 2 retourniert | `SINV-S07`, `SCN-S07` | Lieferantenretoure mit zugeordneter Gutschrift |
| `PO-008` / `S08` | 5 erhalten, 1 retourniert | `SINV-S08`, keine Gutschrift | Retoure wartet auf Lieferantengutschrift |
| `PO-009` / `S09` | Keiner | Keine | Einkaufsstorno vor Wareneingang |

Ein Lieferanten-Commitment beschreibt die Erwartung, ein Wareneingang die tatsächlich
erhaltene Menge, eine Eingangsrechnung die Verbindlichkeit und eine Zahlung deren
Ausgleich. `S06` zeigt, warum erhalten und berechnet getrennte Zustände sind. `S08`
bleibt bewusst offen, damit „an Lieferanten retourniert, aber nicht gutgeschrieben“
echte erklärbare Nachweise hat.

## Belege in der Basis

| Beleg | Beispiele | Bedeutung |
| --- | --- | --- |
| Kundenauftrag | `O01`–`O11`, `H-*`, `COST-*` | Angegebener Kundenbedarf und kaufmännische Positionen |
| Einkaufsbestellung | `PO-001`–`PO-009` | Bestellung beim Lieferanten |
| Ausgangsrechnung | `INV-YYYYMMDD-*` | Forderung mit Rechnungspositionen |
| Eingangsrechnung | `SINV-S02`, `SINV-S04`, `SINV-S05`, `SINV-S07`, `SINV-S08` | Verbindlichkeit unabhängig vom Wareneingang |
| Kundengutschrift | `CR-001`, `COST-LATE-CREDIT` | Vollständige und teilweise Wertkorrektur |
| Lieferantengutschrift | `SCN-S07` | Einer Eingangsrechnung zugeordnete Wertkorrektur |
| Kundenzahlung | `PAY-*` | Vollständiger oder teilweiser Forderungsausgleich |
| Lieferantenzahlung | `SPAY-S02`, `SPAY-S04` | Vollständiger oder teilweiser Verbindlichkeitsausgleich |

Alle Belege tragen ein Belegdatum. Lesbare Nummern helfen bei der Suche; die echte
Identität bleibt eine mandantenspezifische, nicht sprechende ID.

## Physische Bewegungen in der Basis

| Bewegung | Beispiele | Physischer Effekt |
| --- | --- | --- |
| Anfangsbestand | `opening-P01`, historische und Kosten-Anfangsbestände | Fügt eine angegebene Startmenge hinzu |
| Wareneingang | `purchase-receipt-S01`–`S08` | Fügt erhaltene Lieferantenware hinzu |
| Versand | `shipment-P06`, `shipment-P09`, `H-*`, `COST-*` | Entfernt an Kunden versendete Ware |
| Kundenretoure | `return-001`, `COST-LATE-RETURN` | Fügt zuvor versendete Ware wieder hinzu |
| Lieferantenretoure | `supplier-return-S07`, `supplier-return-S08` | Entfernt an den Lieferanten zurückgesendete Ware |
| Korrektur | Korrekturpaar bei `P16` | Bewahrt das Original und erfasst die Korrektur |

Bestand ist die vorzeichenrichtige Summe dieser Bewegungen je Lagerort. Kein
Rechnungs- oder Belegstatus besitzt die physische Menge.

## Lager, Deckungsbeitrag und Finance

- `P08` hat Bestand im anderen Lager und zeigt einen lagerortspezifischen Engpass.
- `P16` enthält eine nachvollziehbare Bewegungskorrektur.
- `COST-A` verbindet Einkauf, Bestand, Verkauf, Retoure und Vertriebskosten.
- Die fünf `COST-PORTFOLIO-*`-Fälle zeigen gesunde, niedrige, negative, explizit null
  gesetzte und stark durch Umlagen belastete DB2-Ergebnisse.
- Fehlende Nachweise bleiben als **Nicht nachgewiesen** sichtbar. 0 EUR erscheint nur,
  wenn null ausdrücklich angegeben oder geprüft wurde.
- Kunden- und Lieferantengutschriften reduzieren Rechnungen über explizite Zuordnungen.

### Exakte DB1- und DB2-Beispiele

| Fall | Umsatz | Wareneinsatz | DB1 | Vertriebskosten | DB2 | Quote |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `COST-A` | 1.200 EUR | 630 EUR | 570 EUR | 114 EUR | 456 EUR | 38 % |
| `COST-PORTFOLIO-HEALTHY` | 250 EUR | 100 EUR | 150 EUR | 25 EUR | 125 EUR | 50 % |
| `COST-PORTFOLIO-LOW` | 150 EUR | 100 EUR | 50 EUR | 40 EUR | 10 EUR | 6,6667 % |
| `COST-PORTFOLIO-NEGATIVE` | 130 EUR | 100 EUR | 30 EUR | 60 EUR | −30 EUR | −23,0769 % |
| `COST-PORTFOLIO-ZERO-SELLING` | 180 EUR | 100 EUR | 80 EUR | 0 EUR | 80 EUR | 44,4444 % |
| `COST-PORTFOLIO-ALLOCATED-HEAVY` | 220 EUR | 100 EUR | 120 EUR | 60 EUR | 60 EUR | 27,2727 % |

Beim Nullkostenfall wurden 0 EUR ausdrücklich geprüft; der Wert fehlt nicht. Jede
vorbereitete Ausgangsrechnungsposition besitzt eine geprüfte DB-Basis. **Nicht
nachgewiesen** bedeutet, dass Reality fehlende Nachweise bewusst nicht in 0 EUR
umgewandelt hat.

## Abdeckung und bewusste Lücken

| Typischer Prozess | Enthalten | Nachweis oder Einschränkung |
| --- | --- | --- |
| Offener Auftrag, Engpass und Reservierung | Ja | `O01`–`O05` |
| Teil-/Vollauslieferung und Sperre | Ja | `O06`–`O09` |
| Storno vor/nach Versand | Ja | `O10`, `O11` |
| Offene, teilweise und bezahlte Forderung | Ja | `H-*`, `PAY-*` |
| Vollständige und teilweise Kundenretoure/-gutschrift | Ja | `CR-001`, `COST-LATE-CREDIT` |
| Kein, teilweiser und vollständiger Wareneingang | Ja | `S01`–`S03` |
| Wareneingang ohne Rechnung | Ja | `S06` |
| Offene, teilweise und bezahlte Verbindlichkeit | Ja | `S05`, `S04`, `S02` |
| Lieferantenretoure mit/ohne Gutschrift | Ja | `S07`, `S08` |
| Einkaufsstorno vor Wareneingang | Ja | `S09` |
| Lagerortengpass und Korrektur | Ja | `P08`, `P16` |
| Vollständige DB1-/DB2-Erklärungen | Ja | `COST-A`, `COST-PORTFOLIO-*` |
| Reine Preisgutschrift | Nein | Nicht in Profilversion 4 |
| Umtausch oder Ersatzlieferung | Nein | Nicht in Profilversion 4 |
| Rechnungsstorno/Gegenbuchung | Nein | Nicht in Profilversion 4 |
| Mehrere Teilrechnungen je Auftrag | Nein | Nicht in Profilversion 4 |
| Überlieferung/endgültige Unterlieferung | Nein | Nicht in Profilversion 4 |
| Umlagerung, Schaden, Verlust oder Verschrottung | Nein | Nicht in Profilversion 4 |
| Chargen, Seriennummern oder Ablaufdaten | Nein | Nicht in Profilversion 4 |
| Anzahlungen, Mahnungen oder Forderungsausfall | Nein | Nicht in Profilversion 4 |
| Bankabstimmung, Steuer oder Währungsneubewertung | Nein | Nicht in Profilversion 4 |

## Stabile Basis und Live-Daten

Die Fälle oben gehören zur stabilen Basis. Die Live-Simulation ergänzt separat neue
Kundenaufträge und später Rechnungen und Zahlungen. Sie reserviert, versendet,
retourniert oder beschafft Waren nicht automatisch. Dadurch bleiben die Referenzfälle
reproduzierbar.

Noch nicht enthalten sind reine Preisnachlässe, Umtausch, Storno nach Rechnungsstellung,
Überlieferung, Fertigung, Lohnabrechnung und gesetzliche Berichte.
