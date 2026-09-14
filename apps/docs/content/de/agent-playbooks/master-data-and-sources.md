# Playbook: Stammdaten und Quellen

Die Daten, auf denen jedes andere Playbook steht: Kunden, Lieferanten, Artikel, Standorte,
Einheiten, Preise, Zahlungsbedingungen, und die Systeme, die Datensätze liefern. Nichts davon ist
ein Geschäftsereignis; es ist, was das Unternehmen über sich selbst gesagt hat, und es ändert sich
selten und bewusst. Ein Agent hält es aktuell, indem er Aussagen vorschlägt, die ein Mensch
bestätigt. Reality erfindet nie einen Kunden, einen Artikel, eine Einheitenbeziehung oder einen
Preis.

Jede Situation ist eine Zeile Kontext und wenige nummerierte Schritte: was du aufrufst, was du
sagst, was der Agent vorbereitet, was du entscheidest, was du prüfst. Das Werkzeug hinter einem
Schritt steht am Zeilenende nach einem Pfeil.

Lies zuerst [Ein Unternehmen auf Reality mit Agenten führen](./) für den Kreislauf und die Regeln.

## Was Reality hält und ableitet

- Ein Geschäftspartner ist Firma, Kunde oder Lieferant, und kann mehreres zugleich sein (`roles`).
  Sie trägt Standardwährung, Kreditlimit, Buchhaltungskonto, Steuernummer und den Code ihrer
  Standard-Zahlungsbedingung. Ein Artikel trägt SKU, Lagereinheit, Artikelart (`stocked`, `service`,
  `charge`), Verfolgungsart (`none`, `lot`, `serial`), Wiederbeschaffungszeit und, wenn die Firma
  ihn in einer anderen Einheit kauft, eine `purchase_unit` mit `conversion_factor`. Ein Standort ist
  ein Lager oder ein Platz darin, in einer Hierarchie. Jeder Datensatz hat eine opake Id; SKUs,
  Namen und Codes sind, was Menschen sagen, nie Identität.
- Stammdaten werden nie gelöscht. `master_data_lifecycle_propose(model, record_id, is_active)`
  deaktiviert Geschäftspartner, Artikel, Standort oder Zahlungsbedingung; die Historie zeigt weiter
  darauf.
- Eine Preisliste hat eine Richtung (Verkauf oder Einkauf), eine Währung und eine Gültigkeit; ihre
  Staffeln nennen einen Stückpreis für einen Artikel ab einer Mindestmenge, in einer Einheit.
  `resolve_price` sieht die eigenen Listen des Geschäftspartners nach Priorität an, dann die Listen
  ihrer Partnergruppen, dann die Standardlisten, und nimmt die erste gültige Staffel. Eine Zeile mit
  frei genanntem Preis ist normal; aus dem Fehlen einer Liste wird nichts abgeleitet.
- Eine Zahlungsbedingung ist ein Code mit Fälligkeitstagen und optionalem Skonto. Rechnungen nennen
  die Bedingung; aus ihr kommen das Fälligkeitsdatum hinter `overdue_receivable` und der Skonto, der
  eine Minderzahlung erklärt. Eine Rechnung aus einer Quelle mit einer Bedingung, die Reality nicht
  hält, scheitert an der Interpretation, bis die Bedingung existiert.
- Ein Quellsystem ist ein registriertes externes System mit Fähigkeiten: welche Datensatzarten es
  liefern darf und was aus jeder wird. Jeder angenommene Datensatz wird zuerst verlustfrei
  gespeichert; die Interpretation ist ein zweiter Schritt mit einem Ergebnis (`interpreted`,
  `needs_review`, `unsupported`, `failed`, ...), das `interpretation_coverage` mit den erzeugten
  Datensätzen listet. Die Registrierung erklärt erlaubte Eingänge, sie ist keine Live-Verbindung.
- Lesezugriffe: `business_records_discover(family="party"|"item"|"location"|"document", query)`
  findet Datensätze nach Name, SKU, Code oder externer Id und liefert opake Ids.
  `interpretation_coverage(source_record_id?)` zeigt, was aus jedem Quelldatensatz wurde.
  `exceptions_list` und `exception_explain` tragen die drei Klassen unten. In der App: Stammdaten
  (Kunden, Lieferanten, Artikel, Standorte), Firma → Daten → Quellen & Eingang, und Verarbeitung.

Abweichungen, die zu diesem Bereich gehören: `units_not_comparable`, `silent_source`,
`source_interpretation_failure`. Stammdatenlücken zeigen sich sonst als Ablehnung in dem Moment, in
dem jemand den Datensatz braucht, und dort beginnt der größte Teil dieses Playbooks.

Die Beispiele nutzen den Shop Nordshop als Quelle, den Artikel LAMP-01, den Kunden Müller GmbH und
den Lieferanten Nordlicht Leuchten GmbH.

## Situationen

### Anlegen, was eine Quelle braucht

Der Shop hat einen Auftrag geschickt, den Reality nicht interpretieren konnte: eine SKU, die kein
Artikel trägt. Verlustfrei gespeichert, wartet.

1. **Liste:** „Welche Importe sind gescheitert?" → Nordshop #1051, „Unknown SKU: LAMP-02" →
   `exceptions_list` · `source_interpretation_failure` · `interpretation_coverage`
2. **Duplikat?** „Haben wir LAMP-02 unter anderer SKU?" → nichts → `business_records_discover`
   `family="item"`
3. **Sagen:** „Leg LAMP-02 an, Schreibtischlampe schwarz, Stück, lagergeführt, aus Nordshop-Produkt
   8841."
4. **Agent:** Artikel mit der Quelle als Herkunft → `item_create_propose` · fehlende Bedingung →
   `payment_term_create_propose` · bekannter Artikel unter neuer SKU → `item_update_propose`
5. **Du:** freigeben.
6. **Neu anstoßen und prüfen:** fehlgeschlagenen Job in der App (Verarbeitung) neu anstoßen →
   interpretiert, Auftrag erzeugt → `interpretation_coverage` · Eintrag weg

Ein Quellauftrag nennt seinen Kunden über die Verbindung, nicht die Nutzlast; unbekannte Artikel
sind das, was scheitert.

### Stammdaten aus einer Datei übernehmen

Eine Tabelle aus dem Altsystem: 300 Artikel. Spalten werden gelesen, wie sie sind; die Datei bleibt
die Quelle, auf die jeder Artikel zeigt.

1. **Hochladen** in der App: Firma → Daten → Quellen & Eingang.
2. **Sagen:** „Importiere die hochgeladene Datei als Artikel."
3. **Agent:** Übernahme mit Ziel Artikel; `party`, `location`, `inventory_snapshot` für die anderen
   Arten; Spalten `sku`, `name`, `unit`, `purchase_unit`, `conversion_factor`, `lead_time_days` nach
   Namen → `source_ingest_propose`
4. **Du:** freigeben. Vorhandene SKUs werden abgelehnt, nicht zusammengeführt; Datei korrigieren,
   neu hochladen.
5. **Prüfen:** Artikel mit der Datei als Quelle gelistet → `business_records_discover` · ein
   Snapshot erscheint als Anfangsbestand → `inventory_read`

### Kunden, Lieferanten und Artikel aktuell halten

Müller bekommt ein höheres Kreditlimit und eine neue Standardbedingung; ein Lieferant geht in den
Ruhestand. Vorschläge zeigen Vorher und Nachher; gelöscht wird nichts.

1. **Finden:** „Such die Müller GmbH." → Kreditlimit 5.000, Bedingung NET14 →
   `business_records_discover` `family="party"`
2. **Sagen:** „Kreditlimit 8.000, Zahlungsbedingung NET30."
3. **Agent:** Änderung genau dieser Felder per opaker Id → `party_update_propose` · Artikel und
   Standorte genauso → `item_update_propose`, `location_update_propose` · neue Datensätze →
   `party_create_propose`, `item_create_propose`
4. **Du:** freigeben; jedes Feld von was zu was, protokolliert.
5. **Stilllegen:** „Deaktiviere den Lieferanten Altlicht." → `master_data_lifecycle_propose`
   `model="party"`, `is_active=false`; die Historie zeigt weiter darauf.
6. **Prüfen:** neue Werte → `business_records_discover` · ein deaktivierter Geschäftspartner nimmt
   keine neuen Aufträge an.

### Einheiten in Beziehung setzen

LAMP-01 wird in Kartons zu 12 gekauft, stückweise verkauft. Bis der Artikel das sagt, überspringen
sechs Prüfungen diese Zeilen stillschweigend.

1. **Liste:** „Welche Artikel haben Einheiten, die wir nicht vergleichen können?" → LAMP-01, keine
   Umrechnung, 14 Zeilen auf 3 Belegen → `exceptions_list` · `units_not_comparable` ·
   `exception_explain`
2. **Welches von zwei:** keine Beziehung genannt → eine Aussage am Artikel · Beziehung teilt nicht
   glatt (107 Stück sind keine Kartons) → die Zeile korrigieren, nicht den Artikel
3. **Sagen:** „LAMP-01 wird in Kartons zu 12 gekauft."
4. **Agent:** `purchase_unit="box"`, `conversion_factor="12"` → `item_update_propose`
5. **Du:** freigeben. Kein Einheitensystem; Reality rechnet nur mit diesem Faktor um, beim Lesen.
6. **Prüfen:** Eintrag weg · sechs Klassen beurteilen die Zeilen wieder. Preise werden nie
   umgerechnet.

### Preise: Listen, Staffeln und wer welche bekommt

Müller hat 45,00 je Lampe ab 10 Stück verhandelt, gültig dieses Jahr. Listen mit Staffeln;
Zuordnungen entscheiden, wer welche bekommt.

1. **Sagen:** „Verkaufsliste KEY-2026, EUR, bis 31. Dezember: LAMP-01 45,00 ab 10, 48,00 darunter.
   Müller zuordnen, erste Priorität."
2. **Agent:** Liste → `price_list_create_propose` · Staffeln → `price_tier_create_propose` ·
   Zuordnung → `party_price_list_assign_propose` · Gruppen → `party_group_create_propose`,
   `party_group_member_add_propose`, `group_price_list_assign_propose`. Preise genannt, nie
   gerechnet.
3. **Du:** jeden freigeben. Reihenfolge bei mehreren: Partnerlisten nach Priorität, dann
   Gruppenlisten, dann Standard.
4. **Prüfen:** Müllers nächster vom Agenten vorbereiteter Auftrag trägt die Staffel
   (`price_list_entry_id`) · Einkaufsseite: `invoice_price_differs`, `sold_below_purchase_price`

### Zahlungsbedingungen

Nordlicht bietet 2 % innerhalb 10 Tagen, 30 netto. Ein Code mit Fälligkeitstagen und Skonto;
Rechnungen nennen ihn.

1. **Sagen:** „Leg NET30-2 an: 30 Tage, 2 % innerhalb 10, Nordlichts Standard."
2. **Agent:** Bedingung → `payment_term_create_propose` `due_days=30`, `discount_percent=2`,
   `discount_days=10` · Lieferantenstandard → `party_update_propose` · bestehende ändern →
   `payment_term_update_propose`
3. **Du:** freigeben. Nur künftige Belege; erfasste behalten ihre Bedingung.
4. **Prüfen:** nächste Rechnung zeigt Fälligkeit und Skontofenster → `payment_run_preview` ·
   `purchase_discount_available` · Kundenseite: eine Minderzahlung in Skontohöhe ist erklärt →
   `overdue_receivable` Tag `early_payment_discount_taken`

### Eine Quelle registrieren und was sie liefern darf

Südshop soll Aufträge liefern. Die Registrierung erklärt, was das System aussagen darf; sie ist
keine Live-Verbindung.

1. **Sagen:** „Registriere Südshop als Shopify-Quelle für Aufträge."
2. **Agent:** Connector-Hülle → `connector_install_propose` `connector_code="shopify"` · ohne
   Connector: `source_system_create_propose` + je Datensatzart ein
   `source_capability_create_propose` · später beenden → `source_capability_lifecycle_propose`,
   `source_system_lifecycle_propose`
3. **Du:** freigeben. Nicht erklärte Fähigkeiten werden am Eingang abgelehnt; das ist der Sinn.
4. **Selbst verbinden:** Zugangsdaten, Webhooks, Senden leben im Shop oder deiner
   Integrationsschicht; der Connector-Vertrag sagt, was ein Datensatz trägt.
5. **Prüfen:** System und Fähigkeiten unter Quellen & Eingang · erste Datensätze und ihr Ergebnis →
   `interpretation_coverage`

### Eine Quelle ist verstummt

Nordshop liefert alle paar Minuten und pausiert nachts. Seit zwei Tagen still. Nichts ist kaputt;
die Zahlen werden leise älter.

1. **Sehen:** verstummt → `exceptions_list` · `silent_source` · „Erklär es." → letzter Datensatz Di
   22:14, längste gelernte Pause 11 h, still seit 50 h → `exception_explain`
2. **Außerhalb fragen:** Shop down, Webhook kaputt, Token abgelaufen, Saison vorbei? Ankommende
   Datensätze sind die Lösung.
3. **Gewolltes Schweigen:** „Deaktiviere Nordshops Auftragsfähigkeit." →
   `source_capability_lifecycle_propose` `is_active=false`
4. **Prüfen:** verschwindet, sobald ein Datensatz ankommt · Ergebnis gelistet →
   `interpretation_coverage`

Eine Fähigkeit mit nur einer Handvoll Lieferungen wird nie gemeldet; daraus lernt sich kein
Rhythmus.

### Etwas kam an und wurde nicht verstanden

Ein Datensatz ist an der Interpretation gescheitert: unbekannte SKU, fehlende Bedingung, nicht
unterstützte Art, Versionskonflikt. Der Datensatz ist sicher und wird nie bearbeitet.

1. **Grund:** „Warum ist Nordshop #1052 gescheitert?" → „Unknown SKU: LAMP-02" →
   `interpretation_coverage` `source_record_id` · `exception_explain`
2. **Ursache beseitigen:** Artikel oder Bedingung anlegen, Mapping im Quellsystem ändern, oder
   entscheiden, dass er nicht interpretiert wird.
3. **Neu anstoßen** in der App unter Verarbeitung; ein Agentenwerkzeug dafür gibt es heute nicht.
4. **Prüfen:** interpretiert → `interpretation_coverage` · Eintrag weg →
   `source_interpretation_failure`, oder der nächste Grund.

### Eine Frage, die die Daten nicht beantworten

Der Vertrieb fragt: „Welche offenen Aufträge wollten Expressversand?" Kein Feld hält das. Die Frage
festhalten, wie sie gestellt wurde.

1. **Festhalten:** „Erfass die Frage … der Vertrieb braucht das für den täglichen Pick." →
   `reality_gap_create_propose`
2. **Belege:** „Nordshop-Nutzlasten tragen `shipping_lines.title`, zwei Beispiele." →
   `reality_gap_entry_add_propose`
3. **Empfehlen und entscheiden:** eine Fact-Regel über die Nutzlast →
   `reality_gap_recommend_propose`, `reality_gap_decide_propose`. Siehe
   [Reality fehlt etwas Wichtiges](/de/concepts/business-reality-guide/06-facts-and-open-questions#missing-information).
4. **Prüfen:** Entscheidung an der Lücke → `reality_gaps`, `reality_gap_get` · Probelauf einer
   aktiven Regel → `reality_gap_simulate`

### Was die Quellen geliefert haben, durchsehen

Der monatliche Blick auf jede Quelle vor der Finanzübergabe.

1. **Fragen:** „Wie haben sich die Quellen diesen Monat gemacht?" → interpretiert, zu prüfen, nicht
   unterstützt, gescheitert je System und Fähigkeit; offene Einträge zu Schweigen und Fehlschlägen;
   ungenutzte Fähigkeiten → `interpretation_coverage`, `exceptions_list`
2. **Entscheiden:** welche Fehlschläge eine Lösung bekommen, welche Fähigkeiten deaktiviert werden →
   `source_capability_lifecycle_propose`, welche Datensätze vor der Übergabe geprüft werden.
3. **Nächsten Monat:** gescheitert und zu prüfen sinken; nichts schweigt, das liefern sollte.

## Wie ein Agent Ergebnisse formulieren sollte

- „Artikel `itm_…` nennt keine Einkaufseinheit; 14 Zeilen auf 3 Belegen werden nicht verglichen" ist
  ein Lesezugriff.
- „Artikeländerung vorbereitet: Einkaufseinheit Karton, Faktor 12; Entscheidung `prp_…` offen" ist
  ein Vorschlag.
- „Freigegeben; `units_not_comparable` listet den Artikel nicht mehr" ist geprüft.
- Nie „angelegt" oder „verbunden" sagen für einen Vorschlag, der nicht freigegeben ist, und eine
  registrierte Quelle nie als Live-Verbindung darstellen.

## Noch nicht möglich

- Kein Einheitensystem: Reality weiß, was eine Firma über ihre eigenen Artikel sagt, nicht, dass ein
  Kilogramm tausend Gramm sind.
- Keine Preisumrechnung zwischen Einheiten und keine Preisvorschläge; Preise kommen aus
  Vereinbarungen.
- Keine Duplikaterkennung oder Zusammenführung für Geschäftspartner und Artikel; der Agent prüft vor
  dem Vorschlag mit `business_records_discover`, ein Mensch entscheidet.
- Kein Löschen; nur Deaktivieren über den Lebenszyklus.
- Kein erneuter Interpretationsversuch über die Agentenwerkzeuge; der Neuversuch ist eine App-Aktion
  am fehlgeschlagenen Job.
- Keine Live-Verbindung durch Registrierung: Zugangsdaten, Webhooks und Zustellung leben im externen
  System oder in der Integrationsschicht.
- Kunden entstehen nicht aus Quellaufträgen: Die Verbindung nennt den Geschäftspartner, dem ihre
  Aufträge gehören; ein Shop mit vielen Kunden braucht eine Integration, die sie vor dem Eingang
  auflöst.
