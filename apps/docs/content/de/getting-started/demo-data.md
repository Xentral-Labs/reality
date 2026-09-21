---
pageClass: demo-data-page
---

# Demo-Datensatz

Die kanonische Demo-Firma ist ein reproduzierbares, synthetisches Handelsunternehmen. Hier siehst du
vollständige und problematische Geschäftsabläufe in Vertrieb, Einkauf, Lager, Finance und Analytics.
Die Referenzen unten sind suchbare Bezeichnungen und keine technischen IDs.

Jeder Demo-Beleg hat ein Belegdatum. Ein Strich beim Fälligkeitsdatum bedeutet nur, dass die Quelle
keine Fälligkeit genannt hat – nicht, dass der Beleg kein Datum hat.

## Firma und Verwendung der Referenzen

Die Basis enthält 18 Artikel (`ITEM-001`–`ITEM-018`), 20 Kunden, drei Lieferanten sowie die Lager
Rotterdam und Singapur. Mengen werden in Stück, Metern oder Kilogramm geführt. Die meisten Vorgänge
sind in EUR; zwei Rechnungen verwenden bewusst USD.

<details class="demo-data-inventory">
<summary><strong>Vollständige Stammdatenübersicht</strong> — 18 Artikel, 20 Kunden, 3 Lieferanten, 2 Lager und die gemeinsame Zahlungsbedingung</summary>

### Vollständige Stammdatenübersicht

| Art               | Enthaltene Datensätze                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Wo du sie findest                                                    |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| Artikel           | `ITEM-001` Summit Bottle; `ITEM-002` Trail Lantern; `ITEM-003` Ridge Backpack; `ITEM-004` Cedar Desk Lamp; `ITEM-005` Coast Storage Box; `ITEM-006` Harbor Travel Mug; `ITEM-007` Aurora Notebook; `ITEM-008` Vista Monitor Stand; `ITEM-009` Maple Serving Tray; `ITEM-010` Orbit Cable Kit; `ITEM-011` Meadow Picnic Set; `ITEM-012` Beacon Desk Organizer; `ITEM-013` Drift Cushion; `ITEM-014` Cove Glass Set; `ITEM-015` Meridian Fabric; `ITEM-016` Alpine Wax Pellets; `ITEM-017` Willow Batch Balm; `ITEM-018` Atlas Field Scanner | Stammdaten → Artikel; Lager → Artikel                                |
| Kunden            | Northstar Outdoor; Maple Retail; Solstice Living; Pacific Outfitters; Brightwater Home; Juniper Trading Co.; Lakeside Provisions; Fjord Outfitters; Harlow Interiors; Tidewater Sports; Evergreen Studio; Copperline Goods; Granite Peak Gear; Willow & Finch; Northbridge Office Supply; Blue Heron Living; Marlow Home Goods; Silverbirch Design; Cascade Trail Company; Amber Coast Retail                                                                                                                                              | Stammdaten → Geschäftspartner; außerdem auf Aufträgen und Rechnungen |
| Lieferanten       | Alpine Components (`ITEM-016`); Meridian Textiles (`ITEM-015`); Seabright Goods (`ITEM-011`)                                                                                                                                                                                                                                                                                                                                                                                                                                               | Stammdaten → Geschäftspartner; Einkauf → Bestellungen                |
| Lager             | Rotterdam Warehouse; Singapore Warehouse                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Lager → Artikel → Bestand nach Lagerort aufklappen                   |
| Zahlungsbedingung | `DEMO-14-2`: 14 Tage netto, 2 % Skonto innerhalb 7 Tagen                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Eine beliebige vorbereitete Kunden- oder Lieferantenrechnung öffnen  |

Northstar Outdoor, Maple Retail, Solstice Living und Blue Heron Living kommen in der datierten
Verkaufsserie mehrfach vor; die übrigen Kunden liefern gezielte Einzelvergleiche. Die Zuordnung der
Lieferanten zu ihren Artikeln ist ausdrücklich angegeben und wird nicht aus Wareneingängen geraten.

</details>

Die Referenz muss in der passenden Ansicht gesucht werden. Die wichtigsten Wege sind:

- **Vertrieb → Aufträge:** `SO-001`, `SO-011`, `SO-017` oder `SO-024` suchen.
- **Einkauf → Bestellungen:** `PO-001` bis `PO-009` suchen.
- **Finance → Forderungen/Verbindlichkeiten:** nach einer `INV-*`-/`SINV-*`-Nummer, einem
  Kunden/Lieferanten oder einer unten genannten `CPAY-*`-/`SPAY-*`-Zahlung suchen.
- **Lager:** den Artikel, zum Beispiel `ITEM-008` oder `ITEM-016`, öffnen und Bestand sowie
  Bewegungen aufklappen.
- **Analytics/Deckungsbeitrag:** `SO-024` oder `SO-025` suchen und die Erklärung unter der
  Rechnungsposition öffnen.

Wenn eine Rechnung eine andere Nummer als ihr Auftrag besitzt, beginne im Auftrag und folge dem Link
zur Rechnung. Von wichtigen Werten gelangst du weiter über den Reality-Datensatz und den Beleg bis
zur ursprünglichen synthetischen Quelle. Dieselbe Profilversion erzeugt in jeder neuen Firma
dieselben Fälle.

## Verkauf und Lieferung

| Referenz           | Was du prüfen kannst      | Erwartetes Ergebnis                               | So findest du es                                            |
| ------------------ | ------------------------- | ------------------------------------------------- | ----------------------------------------------------------- |
| `SO-001`           | Reservierung              | 5 Stück reserviert                                | Vertrieb → Aufträge → `SO-001` suchen → Position aufklappen |
| `SO-002`           | Bestand ohne Reservierung | 5 bestellt, 10 auf Lager, nichts reserviert       | Vertrieb → Aufträge → `SO-002`                              |
| `SO-003`           | Bestandsengpass           | 5 bestellt, aber nur 2 verfügbar                  | Vertrieb → Aufträge → `SO-003` → Verfügbarkeit              |
| `SO-004`           | Teilreservierung          | 2 Stück eines überfälligen Auftrags reserviert    | Vertrieb → Aufträge → `SO-004` → Reservierungen             |
| `SO-005`           | Überfällige Reservierung  | 5 Stück reserviert; die Zusage ist überfällig     | Vertrieb → Aufträge → `SO-005` → Reservierungen/Historie    |
| `SO-006`           | Teillieferung             | 3 von 5 Stück versendet; 2 bleiben offen          | Vertrieb → Aufträge → `SO-006` → Lieferungen                |
| `SO-007`, `SO-008` | Manuelle Sperre           | Die Zusage ist gesperrt und weiter erklärbar      | Vertrieb → Aufträge → jeweilige Referenz → Zusage           |
| `SO-009`           | Vollständige Lieferung    | 5 von 5 Stück versendet                           | Vertrieb → Aufträge → `SO-009` → Lieferungen                |
| `SO-010`           | Storno vor Versand        | Die Reservierungshistorie bleibt sichtbar         | Vertrieb → Aufträge → `SO-010` → Historie                   |
| `SO-011`           | Storno nach Teillieferung | 2 Stück bleiben versendet; der Rest ist storniert | Vertrieb → Aufträge → `SO-011` → Lieferungen/Historie       |

Die datierten Aufträge `SO-012` bis `SO-023` und ihre Rechnungen zeigen vergleichbare Mengen-,
Preis-, Rückgangs-, Ausreißer-, Nullwert- und USD-Zeiträume. Es gibt offene, teilweise und
vollständig bezahlte Rechnungen.

Aufträge sind Nachweise, kein Lieferstatus. Die Lieferzusage ist ein Commitment, Reservierungen sind
eigene Datensätze und nur Movements verändern den physischen Bestand. Ein Storno von `SO-010` oder
`SO-011` löscht daher keine bereits erfolgte Reservierung oder Lieferung.

## Historische Verkäufe und Rechnungen

| Referenz | Angegebener Vorgang           | Ausgleich                                          | Zweck                                              | So findest du es                                           |
| -------- | ----------------------------- | -------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------- |
| `SO-012` | 10 × `ITEM-011`, 200 EUR      | Bezahlt                                            | Frühere Mengenbasis                                | Vertrieb → Aufträge → `SO-012`                             |
| `SO-013` | 20 × `ITEM-011`, 400 EUR      | Bezahlt                                            | Aktueller Mengenvergleich                          | Vertrieb → Aufträge → `SO-013`                             |
| `SO-014` | 10 × `ITEM-012`, 200 EUR      | Bezahlt                                            | Frühere Preisbasis                                 | Vertrieb → Aufträge → `SO-014`                             |
| `SO-015` | 10 × `ITEM-012`, 250 EUR      | Teilbezahlt                                        | Gleiche Menge, höherer Preis                       | Vertrieb → Aufträge → `SO-015`                             |
| `SO-016` | 20 × `ITEM-013`, 300 EUR      | Bezahlt                                            | Frühere Nachfragebasis                             | Vertrieb → Aufträge → `SO-016`                             |
| `SO-017` | 5 × `ITEM-013`, 75 EUR        | 74,50 EUR bezahlt; 0,50 EUR akzeptierter Kleinrest | Sichtbarer Absatzrückgang und expliziter Abschluss | Vertrieb → Aufträge → `SO-017`; Rechnung öffnen            |
| `SO-018` | 10 × `ITEM-014`, 120 EUR      | Durch Gutschrift ausgeglichen                      | Ursprung der Vollretoure                           | Vertrieb → Aufträge → `SO-018`; Rechnung/Gutschrift öffnen |
| `SO-019` | 10 × `ITEM-015`, 50 EUR       | Bezahlt                                            | Normaler Vergleichswert                            | Vertrieb → Aufträge → `SO-019`                             |
| `SO-020` | 1.000 × `ITEM-015`, 5.000 EUR | Bezahlt; 10 EUR Kundenguthaben                     | Bewusster Ausreißer plus Überzahlung               | Vertrieb → Aufträge → `SO-020`; Rechnung öffnen            |
| `SO-021` | 8 × `ITEM-016`, 80 EUR        | Offen                                              | Angegebener Vergleich, kein fehlender Wert         | Vertrieb → Aufträge → `SO-021`                             |
| `SO-022` | 4 × `ITEM-009`, 88 USD        | Bezahlt                                            | Frühere Fremdwährungsdaten                         | Vertrieb → Aufträge → `SO-022`                             |
| `SO-023` | 6 × `ITEM-009`, 132 USD       | Bezahlt                                            | Aktuelle Fremdwährungsdaten                        | Vertrieb → Aufträge → `SO-023`                             |

Jeder Fall enthält Auftrag, Liefer-Commitment, datierte Rechnung, Anfangsbestand und
Versandbewegung. Zahlungen sind eigene Belege und Buchungen: Bezahlt bedeutet nicht geliefert, und
geliefert bedeutet nicht bezahlt.

## Kundenretouren und Gutschriften

| Referenz            | Was du prüfen kannst                | Erwartetes Ergebnis                                     | So findest du es                                               |
| ------------------- | ----------------------------------- | ------------------------------------------------------- | -------------------------------------------------------------- |
| `SO-018` / `CN-001` | Vollständige Retoure und Gutschrift | 10 von 10 Stück retourniert; 120 EUR zugeordnet         | Vertrieb → Aufträge → `SO-018`; Rechnung und Gutschrift öffnen |
| `SO-024` / `CN-002` | Teilretoure mit Kosten              | 10 von 60 Stück retourniert, mit exakter Kostenherkunft | Vertrieb → Aufträge → `SO-024`; Rechnung → DB-Erklärung        |

`SO-024` ist das ausführliche Retouren- und Deckungsbeitragsbeispiel. Der ursprüngliche Lagerabgang,
die retournierte Bestandsschicht, die Kundengutschrift und die Vertriebskosten gehören zu einer
gemeinsamen geprüften Kostenbasis.

`CN-001` ist ausdrücklich der ursprünglichen Rechnung zugeordnet; die Forderung ist danach null.
`CN-002` behält für die zehn retournierten Stück exakt die ursprüngliche Kostenschicht, statt einen
neuen Einkaufspreis zu erfinden.

## Einkauf und Verbindlichkeiten

| Referenz |              Wareneingang | Rechnung und Zahlung                          | Zweck                                          | So findest du es                                             |
| -------- | ------------------------: | --------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------ |
| `PO-001` |                   2 von 5 | Keine Rechnung                                | Teilwareneingang                               | Einkauf → Bestellungen → `PO-001`                            |
| `PO-002` |                   5 von 5 | `SINV-002`, `SPAY-002`: 49 EUR + 1 EUR Skonto | Vollständiger Skonto-Ablauf                    | Einkauf → `PO-002`; Finance → Verbindlichkeiten → `SINV-002` |
| `PO-003` |                   0 von 5 | Keine Rechnung                                | Offene Einkaufsbestellung                      | Einkauf → Bestellungen → `PO-003`                            |
| `PO-004` |                   5 von 5 | `SINV-004`, `SPAY-004`: teilbezahlt           | Teilzahlung an Lieferanten                     | Finance → Verbindlichkeiten → `SINV-004`                     |
| `PO-005` |                   5 von 5 | `SINV-005`, `SPAY-005`: 60 EUR auf 50 EUR     | 10 EUR Lieferantenguthaben                     | Finance → Verbindlichkeiten → `SINV-005`                     |
| `PO-006` |                   5 von 5 | Keine Rechnung                                | Wareneingang wartet auf Rechnung               | Einkauf → Bestellungen → `PO-006`                            |
| `PO-007` | 5 erhalten, 2 retourniert | `SINV-007`, `SCN-007`                         | Lieferantenretoure mit zugeordneter Gutschrift | Einkauf → `PO-007`; Finance → `SINV-007`                     |
| `PO-008` | 5 erhalten, 1 retourniert | `SINV-008`, keine Gutschrift                  | Retoure wartet auf Lieferantengutschrift       | Einkauf → `PO-008`; Finance → `SINV-008`                     |
| `PO-009` |                    Keiner | Keine                                         | Einkaufsstorno vor Wareneingang                | Einkauf → Bestellungen → `PO-009`                            |

Ein Lieferanten-Commitment beschreibt die Erwartung, ein Wareneingang die tatsächlich erhaltene
Menge, eine Eingangsrechnung die Verbindlichkeit und eine Zahlung deren Ausgleich. `PO-006` zeigt,
warum erhalten und berechnet getrennte Zustände sind. `PO-008` bleibt bewusst offen, damit „an
Lieferanten retourniert, aber nicht gutgeschrieben“ echte erklärbare Nachweise hat.

## Skonto, Überzahlungen und akzeptierte Kleinreste

| Fangfrage                                                | Sicherer Demofall             | So findest du es                                                                       | Erwartetes Ergebnis                                                                              |
| -------------------------------------------------------- | ----------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Wurde Skonto wirklich gebucht?                           | `SINV-002` / `SPAY-002`       | Finance → Verbindlichkeiten → `SINV-002`; danach Zahlung/Zuordnungen öffnen            | 49 EUR Bankzahlung plus separat begründete 1-EUR-Skontoanpassung; offen 0 EUR                    |
| Was passiert bei Kundenüberzahlung?                      | Auftrag `SO-020` / `CPAY-009` | Vertrieb → Aufträge → `SO-020` → Rechnung; alternativ Finance → Zahlungen → `CPAY-009` | 5.000 EUR zugeordnet, 10 EUR als verfügbares Kundenguthaben                                      |
| Was passiert bei Lieferantenüberzahlung?                 | `SINV-005` / `SPAY-005`       | Finance → Verbindlichkeiten → `SINV-005`; Zahlung/Zuordnungen öffnen                   | 50 EUR zugeordnet, 10 EUR als verfügbares Lieferantenguthaben                                    |
| Kann ein alter Kleinrest als erledigt akzeptiert werden? | Auftrag `SO-017` / `CPAY-006` | Vertrieb → Aufträge → `SO-017` → Rechnung → Ausgleich/Erklärung                        | 74,50 EUR Zahlung plus eigene 0,50-EUR-Anpassung mit Grund „akzeptierter Kleinrest“; offen 0 EUR |

Eine Unter- oder Überzahlung wird nicht umgedeutet: Die Zahlung zeigt ausschließlich das tatsächlich
geflossene Geld. Skonto und akzeptierter Kleinrest sind eigene begründete Buchungen. Ein
Überzahlungsrest bleibt dagegen sichtbar und kann später zugeordnet oder erstattet werden.

## Belege in der Basis

| Beleg                 | Beispiele                                                                          | Bedeutung                                             | So findest du es                               |
| --------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------- |
| Kundenauftrag         | `SO-001`–`SO-035`                                                                  | Angegebener Kundenbedarf und kaufmännische Positionen | Vertrieb → Aufträge → `SO-…` suchen            |
| Einkaufsbestellung    | `PO-001`–`PO-009`                                                                  | Bestellung beim Lieferanten                           | Einkauf → Bestellungen → `PO-…` suchen         |
| Ausgangsrechnung      | `INV-YYYYMMDD-*`                                                                   | Forderung mit Rechnungspositionen                     | Finance → Forderungen → `INV-…` suchen         |
| Eingangsrechnung      | `SINV-002`, `SINV-004`, `SINV-005`, `SINV-007`, `SINV-008`, `SINV-010`, `SINV-011` | Verbindlichkeit unabhängig vom Wareneingang           | Finance → Verbindlichkeiten → `SINV-…` suchen  |
| Kundengutschrift      | `CN-001`, `CN-002`                                                                 | Vollständige und teilweise Wertkorrektur              | Finance → Forderungen → `CN-…` suchen          |
| Lieferantengutschrift | `SCN-007`                                                                          | Einer Eingangsrechnung zugeordnete Wertkorrektur      | Finance → Verbindlichkeiten → `SCN-007` suchen |
| Kundenzahlung         | `CPAY-001` ff.                                                                     | Vollständiger oder teilweiser Forderungsausgleich     | Finance → Zahlungen → `CPAY-…` suchen          |
| Lieferantenzahlung    | `SPAY-002`, `SPAY-004`, `SPAY-005`                                                 | Skonto-, Teil- und Überzahlung                        | Finance → Zahlungen → `SPAY-…` suchen          |

Alle Belege tragen ein Belegdatum. Lesbare Nummern helfen bei der Suche; die echte Identität bleibt
eine mandantenspezifische, nicht sprechende ID.

## Physische Bewegungen in der Basis

| Bewegung           | Beispiele                                        | Physischer Effekt                                | So findest du es                                                       |
| ------------------ | ------------------------------------------------ | ------------------------------------------------ | ---------------------------------------------------------------------- |
| Anfangsbestand     | Artikelbestand                                   | Fügt eine angegebene Startmenge hinzu            | Lager → Artikel → z. B. `ITEM-001` → Bewegungen                        |
| Wareneingang       | Zu `PO-001`–`PO-008`                             | Fügt erhaltene Lieferantenware hinzu             | Einkauf → Bestellung öffnen → Wareneingang; alternativ Lager → Artikel |
| Versand            | Zu `SO-006`, `SO-009` und historischen Aufträgen | Entfernt an Kunden versendete Ware               | Vertrieb → Auftrag öffnen → Lieferungen                                |
| Kundenretoure      | Zu `SO-018`, `SO-024`                            | Fügt zuvor versendete Ware wieder hinzu          | Vertrieb → Auftrag → Rechnung/Gutschrift; Lager → Artikelbewegungen    |
| Lieferantenretoure | Zu `PO-007`, `PO-008`                            | Entfernt an den Lieferanten zurückgesendete Ware | Einkauf → Bestellung → Bewegungen                                      |
| Korrektur          | Bei `ITEM-016`                                   | Bewahrt das Original und erfasst die Korrektur   | Lager → Artikel → `ITEM-016` → Bewegungen                              |

Bestand ist die vorzeichenrichtige Summe dieser Bewegungen je Lagerort. Kein Rechnungs- oder
Belegstatus besitzt die physische Menge.

## Lager, Deckungsbeitrag und Finance

- `ITEM-008` hat Bestand im anderen Lager und zeigt einen lagerortspezifischen Engpass.
- `ITEM-016` enthält eine nachvollziehbare Bewegungskorrektur.
- `SO-024` verbindet Einkauf, Bestand, Verkauf, Retoure und Vertriebskosten.
- Die Aufträge `SO-025` bis `SO-029` zeigen gesunde, niedrige, negative, explizit null gesetzte und
  stark durch Umlagen belastete DB2-Ergebnisse.
- Fehlende Nachweise bleiben als **Nicht nachgewiesen** sichtbar. 0 EUR erscheint nur, wenn null
  ausdrücklich angegeben oder geprüft wurde.
- Kunden- und Lieferantengutschriften reduzieren Rechnungen über explizite Zuordnungen.

### Exakte DB1- und DB2-Beispiele

| Fall     |    Umsatz | Wareneinsatz |     DB1 | Vertriebskosten |     DB2 |      Quote | So findest du es                                         |
| -------- | --------: | -----------: | ------: | --------------: | ------: | ---------: | -------------------------------------------------------- |
| `SO-024` | 1.200 EUR |      630 EUR | 570 EUR |         114 EUR | 456 EUR |       38 % | Vertrieb → Aufträge → `SO-024` → Rechnung → DB-Erklärung |
| `SO-025` |   250 EUR |      100 EUR | 150 EUR |          25 EUR | 125 EUR |       50 % | Vertrieb → Aufträge → `SO-025` → Rechnung → DB-Erklärung |
| `SO-026` |   150 EUR |      100 EUR |  50 EUR |          40 EUR |  10 EUR |   6,6667 % | Vertrieb → Aufträge → `SO-026` → Rechnung → DB-Erklärung |
| `SO-027` |   130 EUR |      100 EUR |  30 EUR |          60 EUR | −30 EUR | −23,0769 % | Vertrieb → Aufträge → `SO-027` → Rechnung → DB-Erklärung |
| `SO-028` |   180 EUR |      100 EUR |  80 EUR |           0 EUR |  80 EUR |  44,4444 % | Vertrieb → Aufträge → `SO-028` → Rechnung → DB-Erklärung |
| `SO-029` |   220 EUR |      100 EUR | 120 EUR |          60 EUR |  60 EUR |  27,2727 % | Vertrieb → Aufträge → `SO-029` → Rechnung → DB-Erklärung |

Beim Nullkostenfall wurden 0 EUR ausdrücklich geprüft; der Wert fehlt nicht. Jede vorbereitete
Ausgangsrechnungsposition besitzt eine geprüfte DB-Basis. **Nicht nachgewiesen** bedeutet, dass
Reality fehlende Nachweise bewusst nicht in 0 EUR umgewandelt hat.

## Abdeckung und bewusste Lücken

| Typischer Prozess                                    | Enthalten | Nachweis oder Einschränkung                     | So findest du es                                           |
| ---------------------------------------------------- | --------- | ----------------------------------------------- | ---------------------------------------------------------- |
| Offener Auftrag, Engpass und Reservierung            | Ja        | `SO-001`–`SO-005`                               | Vertrieb → Aufträge → Referenz suchen                      |
| Teil-/Vollauslieferung und Sperre                    | Ja        | `SO-006`–`SO-009`                               | Vertrieb → Aufträge → Referenz suchen                      |
| Storno vor/nach Versand                              | Ja        | `SO-010`, `SO-011`                              | Vertrieb → Aufträge → Referenz → Historie                  |
| Offene, teilweise und bezahlte Forderung             | Ja        | `SO-012`–`SO-023`, `CPAY-*`                     | Vertrieb → Auftrag → Rechnung; Finance → Forderungen       |
| Skonto mit eigener Reduktionsbuchung                 | Ja        | `SINV-002`, `SPAY-002`                          | Finance → Verbindlichkeiten → `SINV-002`                   |
| Kunden- und Lieferantenüberzahlung/Guthaben          | Ja        | `CPAY-009`, `SPAY-005`                          | Finance → Zahlungen → Referenz suchen                      |
| Akzeptierter Kleinrest                               | Ja        | `CPAY-006`                                      | Vertrieb → `SO-017` → Rechnung → Ausgleich                 |
| Vollständige und teilweise Kundenretoure/-gutschrift | Ja        | `CN-001`, `CN-002`                              | Finance → Forderungen → Gutschriftnummer suchen            |
| Kein, teilweiser und vollständiger Wareneingang      | Ja        | `PO-001`–`PO-003`                               | Einkauf → Bestellungen → Referenz suchen                   |
| Wareneingang ohne Rechnung                           | Ja        | `PO-006`                                        | Einkauf → Bestellungen → `PO-006`                          |
| Offene, teilweise und bezahlte Verbindlichkeit       | Ja        | `SINV-005`, `SINV-004`, `SINV-002`              | Finance → Verbindlichkeiten → Referenz suchen              |
| Lieferantenretoure mit/ohne Gutschrift               | Ja        | `PO-007`, `PO-008`                              | Einkauf → Bestellungen → Referenz öffnen                   |
| Einkaufsstorno vor Wareneingang                      | Ja        | `PO-009`                                        | Einkauf → Bestellungen → `PO-009`                          |
| Lagerortengpass und Korrektur                        | Ja        | `ITEM-008`, `ITEM-016`                          | Lager → Artikel → Referenz suchen                          |
| Vollständige DB1-/DB2-Erklärungen                    | Ja        | `SO-024`–`SO-029`                               | Vertrieb → Auftrag → Rechnung → DB-Erklärung               |
| Reine Preisgutschrift                                | Ja        | `SO-030`, `CN-003`                              | Vertrieb → Aufträge → `SO-030`; Finance → `CN-003` suchen  |
| Umtausch oder Ersatzlieferung                        | Ja        | `SO-033` Retoure, `SO-034` Ersatz               | Vertrieb → beide Aufträge; Lager → `ITEM-007` → Bewegungen |
| Rechnungsstorno/Gegenbuchung                         | Ja        | `SO-031`, exakte Gegenbuchung                   | Vertrieb → Aufträge → `SO-031` → Rechnung → Buchungen      |
| Mehrere Teilrechnungen je Auftrag                    | Ja        | `SO-032`, Mengen 4 und 6                        | Vertrieb → Aufträge → `SO-032` → Rechnungen                |
| Endgültige Unterlieferung                            | Ja        | `SO-011`: 2 versendet, Rest storniert           | Vertrieb → Aufträge → `SO-011` → Historie                  |
| Kundenvorauszahlung vor Versand                      | Ja        | `SO-035`, `CPAY-010`                            | Vertrieb → `SO-035` → Rechnung; Finance → Zahlung          |
| Kontrollierte Überlieferung                          | Ja        | `SO-039`: Menge 10 auf 12 erhöht, dann versandt | Vertrieb → Aufträge → `SO-039` → Zusagenhistorie           |
| Umlagerung                                           | Ja        | `ITEM-017`, 3 Stück Rotterdam → Singapur        | Lager → Artikel → `ITEM-017` → Bewegungen                  |
| Schaden, Verlust und Verschrottung                   | Ja        | `ITEM-010`, je eine Korrektur                   | Lager → Artikel → `ITEM-010` → Bewegungen                  |
| Charge und Ablaufdatum                               | Ja        | `ITEM-017`, `LOT-2026-001` abgelaufen           | Lager → Artikel → `ITEM-017` → Chargen/Bewegungen          |
| Seriennummer                                         | Ja        | `ITEM-018`, `SER-0001`                          | Lager → Artikel → `ITEM-018` → Serien/Bewegungen           |
| Kundenanzahlung mit Schlussrechnung                  | Ja        | `CDEP-001`, `SO-038`; 20 EUR Guthaben bleiben   | Finance → Kundenguthaben → `CDEP-001`; Vertrieb → `SO-038` |
| Lieferantenanzahlung mit Schlussrechnung             | Ja        | `SDEP-001`, `SINV-010`; 20 EUR bleiben          | Finance → Lieferantenguthaben → `SDEP-001`                 |
| Mahnung mit angegebener Gebühr                       | Ja        | `DN-2026-0001`; Stufe 2 plus 5 EUR              | Finance → Forderungen → Mahnung/Rechnung suchen            |
| Teilweiser Forderungsausfall                         | Ja        | `SO-037`; 25 EUR Ausfall, 15 EUR offen          | Vertrieb → `SO-037` → Rechnung → Ausgleichserklärung       |
| Bankabstimmung, Steuer oder Währungsneubertung       | Nein      | Nicht in Profilversion 10                       | Nicht vorhanden; siehe Einschränkung                       |

## Stabile Basis und Live-Daten

Die Fälle oben gehören zur stabilen Basis. Die Live-Simulation ergänzt separat neue Kundenaufträge
und später Rechnungen und Zahlungen. Sie reserviert, versendet, retourniert oder beschafft Waren
nicht automatisch. Dadurch bleiben die Referenzfälle reproduzierbar.

Der Live-Generator erzeugt pro geplantem Lauf null bis sechs Aufträge. Zwei bis zehn Minuten später
folgt jeweils eine Rechnung mit `DEMO-14-2`. Der deterministische Langzeitmix lautet: 91 % exakt
bezahlt, 2 % mit angegebenem Skonto gekürzt, je 1 % Frachtabzug, zwei Teilzahlungen, Überzahlung
oder Doppelzahlung und nicht zuordenbar, 2 % verspätet sowie 1 % nie bezahlt. Exakte und verspätete
Zahlungen können über Provider oder Bank kommen; Abweichungen laufen über den Bankpfad. Die
Prozentsätze beschreiben den Generator und garantieren nicht, dass eine kleine sichtbare Stichprobe
jeden Fall enthält.

## Besondere Nachweise und Bewegungen

| Quellenreferenz                                 | Was sie beweist                                                                    | So findest du es                                                                      |
| ----------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `wrong-location`                                | 8 × `ITEM-008` liegen in Singapur; Rotterdam kann trotzdem Unterbestand haben      | Lager → Artikel → `ITEM-008` → Bestand nach Lagerort und Quellnachweis                |
| `shipment-cancelled-remainder`                  | Die zwei versendeten Stück von `SO-011` bleiben trotz Reststorno erhalten          | Vertrieb → Aufträge → `SO-011` → Lieferungen/Historie                                 |
| `COST-LATE-CLEANUP`                             | Ein angegebener Abgang von 10 Stück lässt 40 × `ITEM-003` in der geprüften Schicht | Lager → `ITEM-003` → Bewegungen; danach DB-Erklärung von `SO-024`                     |
| `correction-original`, `correction-replacement` | Eine falsche `ITEM-016`-Bewegung bleibt erhalten und wird berichtigt               | Lager → `ITEM-016` → Bewegungen/Quellnachweise                                        |
| `history-receipt-*`, `history-shipment-*`       | Jeder historische Verkauf besitzt Eingangs- und Versandnachweis                    | `SO-012`–`SO-023` öffnen und den Artikelbewegungen folgen                             |
| `purchase-receipt-S01`, `S02`, `S04`–`S08`      | Wareneingänge gibt es nur dort, wo Ware eingetroffen ist                           | Einkauf → passendes `PO-*` → Wareneingänge; `PO-003` hat bewusst keine Eingangsquelle |
| `COST-A-SELLING`                                | 114 EUR Vertriebskosten für den vollständigen DB-Fall `SO-024`                     | Finance → Verbindlichkeiten → Referenz suchen; mit DB2 im Auftrag vergleichen         |
| `COST-PORTFOLIO-SELLING`                        | Vertriebskostenverteilung auf fünf Portfoliofälle                                  | Finance → Verbindlichkeiten → Referenz suchen; `SO-025`–`SO-029` vergleichen          |

## Welchen Demo-Modus verwende ich?

| Modus                                 | Zweck                                                                          | Startweg                                                                               |
| ------------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| Internationale Demo                   | Vollständige, reproduzierbare Referenzfirma dieser Seite                       | Firmen → Neue Firma → Sandbox → Demo-Firma                                             |
| Internationale Demo mit Live-Daten    | Dieselbe feste Basis plus fortlaufender synthetischer Auftragseingang          | Bei der Demo-Firma während der Anlage Live-Simulation aktivieren                       |
| Ausführungsprofil (`atlas-execution`) | Kleine Übungsfirma mit zwei Artikeln, zwei Aufträgen und einem Lager           | Ausführungsinhalt der Firmenanlage; für geführte Übungen, nicht für Vertriebsabdeckung |
| Szenario `normal-month`               | Kompakter September-2026-Fall nur für CLI-, Engineering- und Service-Prüfungen | `reality scenario run normal-month --tenant TENANT_ID`                                 |

## So funktionieren die vier neuen Vertriebsfälle

- **Kontrollierte Überlieferung:** `SO-039` sagt zuerst 10 Stück zu. Die unveränderliche Historie
  hält anschließend die bestätigte neue Menge 12 fest. Erst danach akzeptiert dieselbe normale
  Versandprüfung 12 Stück. Die ursprünglichen 10 bleiben sichtbar.
- **Dedizierte Anzahlungen:** `CDEP-001` ist Kundengeld vor der Schlussrechnung zu `SO-038`;
  `SDEP-001` ist die Lieferantenzahlung vor `SINV-010`. Die Verrechnung ist jeweils eine explizite
  Zuordnung. Nicht verbrauchte 20 EUR bleiben als Guthaben sichtbar.
- **Mahnwesen:** `DN-2026-0001` mahnt eine überfällige Rechnung auf Stufe 2. Die manuell angegebene
  Gebühr von 5 EUR ist eine eigene Forderungsposition und verändert die Originalrechnung nicht. Es
  wird keine E-Mail versendet und weder Eskalation, Einzug noch Steuer automatisch erfunden.
- **Forderungsausfall:** Die Rechnung zu `SO-037` zeigt 60 EUR Zahlung, 25 EUR separat bestätigten
  Forderungsausfall und 15 EUR Restforderung. Aus dem Ausfall entsteht kein Kundenguthaben.

Weiterhin nicht enthalten sind automatische Mahnläufe/-zustellung, länderspezifische
Steuerbehandlung, Bankabstimmung, Steuer-/Währungsneubewertung, Fertigung, Lohnabrechnung und
gesetzliche Berichte.
