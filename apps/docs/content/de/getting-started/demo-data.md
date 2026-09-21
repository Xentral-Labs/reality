# Demo-Datensatz

Die kanonische Demo-Firma ist ein reproduzierbares, synthetisches Handelsunternehmen.
Hier siehst du vollständige und problematische Geschäftsabläufe in Vertrieb, Einkauf,
Lager, Finance und Analytics. Die Referenzen unten sind suchbare Bezeichnungen und
keine technischen IDs.

Jeder Demo-Beleg hat ein Belegdatum. Ein Strich beim Fälligkeitsdatum bedeutet nur,
dass die Quelle keine Fälligkeit genannt hat – nicht, dass der Beleg kein Datum hat.

## Verkauf und Lieferung

| Referenz | Was du prüfen kannst | Erwartetes Ergebnis |
| --- | --- | --- |
| `O01` | Reservierung | 5 Stück reserviert |
| `O04` | Teilreservierung | 2 Stück eines überfälligen Auftrags reserviert |
| `O06` | Teillieferung | 3 von 5 Stück versendet; 2 bleiben offen |
| `O07`, `O08` | Manuelle Sperre | Die Zusage ist gesperrt und weiter erklärbar |
| `O09` | Vollständige Lieferung | 5 von 5 Stück versendet |
| `O10` | Storno vor Versand | Die Reservierungshistorie bleibt sichtbar |
| `O11` | Storno nach Teillieferung | 2 Stück bleiben versendet; der Rest ist storniert |

Die datierten `H-*`-Aufträge und Rechnungen zeigen vergleichbare Mengen-, Preis-,
Rückgangs-, Ausreißer-, Nullwert- und USD-Zeiträume. Es gibt offene, teilweise und
vollständig bezahlte Rechnungen.

## Kundenretouren und Gutschriften

| Referenz | Was du prüfen kannst | Erwartetes Ergebnis |
| --- | --- | --- |
| `H-credit-origin` / `CR-001` | Vollständige Retoure und Gutschrift | 10 von 10 Stück retourniert; 120 EUR zugeordnet |
| `COST-A` / `COST-LATE-CREDIT` | Teilretoure mit Kosten | 10 von 60 Stück retourniert, mit exakter Kostenherkunft |

`COST-A` ist das ausführliche Retouren- und Deckungsbeitragsbeispiel. Der ursprüngliche
Lagerabgang, die retournierte Bestandsschicht, die Kundengutschrift und die
Vertriebskosten gehören zu einer gemeinsamen geprüften Kostenbasis.

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

## Lager, Deckungsbeitrag und Finance

- `P08` hat Bestand im anderen Lager und zeigt einen lagerortspezifischen Engpass.
- `P16` enthält eine nachvollziehbare Bewegungskorrektur.
- `COST-A` verbindet Einkauf, Bestand, Verkauf, Retoure und Vertriebskosten.
- Die fünf `COST-PORTFOLIO-*`-Fälle zeigen gesunde, niedrige, negative, explizit null
  gesetzte und stark durch Umlagen belastete DB2-Ergebnisse.
- Fehlende Nachweise bleiben als **Nicht nachgewiesen** sichtbar. 0 EUR erscheint nur,
  wenn null ausdrücklich angegeben oder geprüft wurde.
- Kunden- und Lieferantengutschriften reduzieren Rechnungen über explizite Zuordnungen.

## Stabile Basis und Live-Daten

Die Fälle oben gehören zur stabilen Basis. Die Live-Simulation ergänzt separat neue
Kundenaufträge und später Rechnungen und Zahlungen. Sie reserviert, versendet,
retourniert oder beschafft Waren nicht automatisch. Dadurch bleiben die Referenzfälle
reproduzierbar.

Noch nicht enthalten sind reine Preisnachlässe, Umtausch, Storno nach Rechnungsstellung,
Überlieferung, Fertigung, Lohnabrechnung und gesetzliche Berichte.

