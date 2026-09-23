# Playbook: Einkauf und Nachschub

Von der Fehlmenge zur bezahlten Lieferantenrechnung. Auf dieser Seite kommt nichts von selbst:
Reality zeigt ungedeckte Nachfrage, aber Bestellung, Wareneingang, Lieferantenrechnung, ihre Buchung
und der Zahllauf werden alle von außen orchestriert und von einem Menschen entschieden.

Jede Situation ist eine Zeile Kontext und wenige nummerierte Schritte: was du aufrufst, was du
sagst, was der Agent vorbereitet, was du entscheidest, was du prüfst. Das Werkzeug hinter einem
Schritt steht am Zeilenende nach einem Pfeil.

Lies zuerst [Ein Geschäft mit Agenten auf Reality betreiben](./) für den Kreislauf und die Regeln.

## Was Reality hält und ableitet

- Eine Bestellung ist ein Document mit Positionen; jede Position hat ein eingehendes Commitment (die
  Verpflichtung des Lieferanten) mit Menge und Fälligkeit. Ein Wareneingangs-Movement erfüllt es;
  die offene Menge wird abgeleitet.
- Eine Lieferantenrechnung ist ein Document, dessen Positionen die Bestellpositionen nennen, die sie
  abrechnen. Erfassen und Buchen sind zwei Schritte; erst eine gebuchte Lieferantenrechnung ist eine
  Verbindlichkeit.
- `item_supply_demand` zeigt je Artikel `physical`, `reserved`, `available`, `incoming` (offene
  Bestellbestätigungen der Lieferanten), `open_customer_demand`, `uncovered_demand`, `projected` und
  `blocked_order_count`. `commitments_list` zeigt die Bestellbestätigungen der Lieferanten mit
  Fälligkeit. `inventory_read(view="aggregate"|"location")` zeigt den Bestand, wie er ist.
- `payment_run_preview(pay_by)` zeigt, welche Lieferantenrechnungen bis zu diesem Datum zu zahlen
  sind, was jeder Lieferant bekommt, welche Rechnungen zurückgehalten werden und warum (storniert,
  doppelt, ausgeglichen) und wo noch Skonto möglich ist. `finance_balances` liefert die
  Verbindlichkeiten je Währung.

Abweichungen dieses Bereichs: `overdue_incoming_supplier_commitment`, `billed_not_received`,
`receipt_unbilled`, `invoice_price_differs`, `sold_below_purchase_price`, `units_not_comparable`,
`supplier_invoice_unposted`, `duplicate_supplier_invoice`, `overdue_payable`,
`purchase_discount_available`, `supplier_credit_unposted`, `supplier_credit_unclaimed`,
`supplier_return_not_credited`, `supplier_credit_not_returned`, `stock_expired`.

Die Beispiele nutzen Alpine Components als Lieferanten, den Artikel Cedar Desk Lamp (`ITEM-004`) und
kleine Mengen.

## Situationen

### Finden, was zu kaufen ist

Kundenbedarf, den Bestand und offene Bestellbestätigungen nicht decken. Reality zeigt die Lücke; die
Bestellmenge ist deine Regel.

1. **Liste:** „Was müssen wir diese Woche kaufen?" → `item_supply_demand` · `fulfillment_blockers`
   ITEM-004 verfügbar 0, Bedarf 12, Zulauf 0, ungedeckt 12, 2 Aufträge blockiert · CABLE-2M
   ungedeckt 40, 50 im Zulauf am 18.
2. **Regel:** „Kartons zu 12, 20 im Regal halten; schlag 36 vor." Der Agent rechnet deine Regel und
   nennt Lieferant und Preis → `business_records_discover`
3. **Prüfen:** nichts geändert; die Liste ist die Eingabe für die nächste Situation.

### Eine Bestellung anlegen

Die Bestellung ist der Beleg dafür, was du bestellt hast; die Bestätigung des Lieferanten wird je
Position eine eingehende Verpflichtung.

1. **Sagen:** „Bestell 36 ITEM-004 bei Alpine zum Listenpreis, ins Hauptlager bis zum 18."
2. **Agent:** PO-0210, eine Position 36 × 30,00, `promised_at` 18., Zahlungsbedingung des
   Lieferanten; Beträge aus der Preisliste, nie gerechnet → `order_create_propose`
   `direction="purchase"`
3. **Du:** freigeben; dann die Bestellung über deinen Kanal abschicken.
4. **Prüfen:** Bestellbestätigung 36 zum 18. → `commitments_list` · Zulauf 36, ungedeckt 0 →
   `item_supply_demand` · blockierte Aufträge zeigen den Termin → `fulfillment_blockers`

### Wareneingang buchen

Der Lkw steht mit 3 Kartons an der Tür. Ein Wareneingang sagt, was gezählt wurde, nicht, was
bestellt war.

1. **Sehen:** „Was ist von Alpine fällig?" → PO-0210, 36 ITEM-004, fällig 18. → `commitments_list` ·
   verspätete → `overdue_incoming_supplier_commitment`
2. **Sagen:** „36 ITEM-004 ins Hauptlager eingegangen." Karton beschädigt: „24 eingegangen, 12 gehen
   zurück."
3. **Agent:** Wareneingang 36 gegen die Bestellbestätigung; Charge oder Seriennummer bei geführten
   Artikeln → `movement_create_propose` `movement_type="receipt"` · beschädigte Ware →
   `"supplier_return"` (Gutschrift unten)
4. **Du:** die Zählung freigeben. Ein Teileingang lässt den Rest offen.
5. **Prüfen:** Bestand +36 → `inventory_read` · Bestätigung erfüllt oder Rest → `commitments_list` ·
   blockierte Kundenaufträge bereit → `fulfillment_queue`

### Die Lieferantenrechnung erfassen und buchen

ER-4471 kam: 36 Lampen, 1.080,00. Erfassen, dann buchen; erst die gebuchte Rechnung ist eine
Verbindlichkeit.

1. **Sagen:** „Erfass Alpines ER-4471, 1.080,00, zu PO-0210, 36 zu 30,00."
2. **Agent:** Rechnung mit Position auf die Bestellposition; Beträge, wie die Rechnung sie nennt →
   `supplier_invoice_record_propose`
3. **Du:** Erfassung freigeben; die Buchung wird als Nächstes angeboten →
   `supplier_invoice_post_propose`. Vorher die Rechnungsprüfung unten ansehen.
4. **Prüfen:** nicht mehr ungebucht → `supplier_invoice_unposted` · Verbindlichkeiten +1.080,00 →
   `finance_balances` · ER-4471 in Offene Posten mit Fälligkeit

### Die Rechnungsprüfung

Bestellung, Wareneingang und Rechnung sollen zusammenpassen. Reality nennt die Differenz; es gibt
dem Lieferanten nie recht.

1. **Liste:** „Welche Lieferantenrechnungen passen nicht?" → `exceptions_list`:
   `billed_not_received`, `receipt_unbilled`, `invoice_price_differs`, `duplicate_supplier_invoice`,
   `units_not_comparable`
2. **Ein Fall:** „Erklär die Preisabweichung auf ER-4471." → Bestellung 30,00, Rechnung 31,50, 36
   Lampen, 54,00 mehr → `exception_explain`
3. **Mit dem Einkäufer klären:** die Erhöhung war nicht vereinbart.
4. **Sagen:** „Wie gestellt buchen und 54,00 zurückfordern" (Buchung, dann Lieferantengutschrift
   unten) · „Positionen auf das Bestätigte korrigieren" → `document_lines_correct_propose`, nur bei
   von Hand erfassten Rechnungen · „Nicht buchen, geht zurück."
5. **Du:** den gewählten Vorschlag freigeben, oder keinen.
6. **Prüfen:** Eintrag verschwindet, wenn die Datensätze übereinstimmen → `exceptions_list`; bis
   dahin bleibt die Rechnung durch deine Wahl aus dem Zahllauf.

### Lieferanten mit einem Zahllauf bezahlen

Freitag: was bis nächste Woche bezahlt wird, welche Skonti sich lohnen, was zurückgehalten wird. Die
Überweisung ist deine.

1. **Vorschau:** „Zahllauf, Zahlung bis nächsten Freitag." → ER-4471 Alpine 1.080,00 fällig 20. ·
   ER-4460 Kabelwerk 640,00, 2 % bis Dienstag = 12,80 · zurückgehalten ER-4402, Dublette · Summe
   1.720,00 → `payment_run_preview` `pay_by` · `overdue_payable`, `purchase_discount_available`
2. **Auswählen:** „Zahl beide, nimm den Skonto auf ER-4460, also 627,20." Weglassen ist heute die
   einzige Zahlsperre.
3. **Agent:** Lauf mit genau diesen Rechnungen und Beträgen; eine abweichende Summe wird abgelehnt →
   `payment_run_propose` `expected_total=1707.20` · eine Rechnung allein →
   `supplier_payment_post_propose`
4. **Du:** freigeben, dann bei der Bank überweisen. Reality hat erfasst, was du zu zahlen
   entschieden hast.
5. **Prüfen:** beide ausgeglichen, ER-4460 12,80 Skonto, 627,20 bezahlt →
   `finance_settlement_context` · Verbindlichkeiten −1.707,20 → `finance_balances` · Einträge weg →
   `exceptions_list`

### Abweichungen bei Lieferantenzahlungen

Spiegelbild der Kundenseite: weniger gezahlt mit Zustimmung des Lieferanten, oder zu viel gezahlt.

1. **Weniger, vereinbart:** „Wir haben 1.026,00 auf ER-4471 gezahlt; Alpine verzichtet auf 54,00,
   Mail vom 19." → Zahlung 1.026,00 → `finance_settlement_propose` Modus `payment` · Abzug 54,00 mit
   der Mail als `agreement` → `finance_adjustment_context`, `finance_adjustment_propose`. Beides
   freigeben. Unser Wunsch mindert nichts; die Zustimmung des Lieferanten tut es.
2. **Zu viel:** „Wir haben versehentlich 1.180,00 auf ER-4471 gezahlt." → 1.080,00 zugeordnet,
   100,00 Lieferantenguthaben → Modus `payment`, `allocation_amount` < `amount` · später „nutze die
   100,00 auf ER-4490" → Modus `allocate_credit` · oder „Alpine hat 100,00 erstattet" → Modus
   `refund_credit`
3. **Prüfen:** gezahlt, Abzug und Restverbindlichkeit getrennt in Offene Posten · Guthaben gelistet
   bis zur Nutzung → `finance_credits` Lieferantenseite

### Lieferantengutschriften und Lieferantenretouren

Ware geht zurück, oder der Lieferant korrigiert einen Preis. Drei Tatsachen: Ware weg, Gutschrift
da, Gutschrift genutzt.

1. **Zurückschicken:** „12 beschädigte ITEM-004 sind zu PO-0210 an Alpine zurück." →
   `movement_create_propose` `movement_type="supplier_return"`. Freigeben; die Retoure wartet nun
   auf ihre Gutschrift → `supplier_return_not_credited`
2. **Gutschrift erfassen:** „Erfass Alpines Gutschrift GS-N-118, 360,00, für die 12 Lampen." →
   Position nennt die Bestellposition → `document_create_propose`
   `document_type="supplier_credit_note"` · Buchung → `supplier_credit_note_post_propose`. Beides
   freigeben.
3. **Nutzen:** „Verrechne GS-N-118 mit ER-4471" → `supplier_credit_note_allocate_propose` · Geld
   zurück: „Alpine hat 360,00 erstattet, NL-2211" → `supplier_refund_post_propose`
4. **Prüfen:** Retouren-, Ungebucht- und Ungenutzt-Einträge weg → `supplier_credit_unposted`,
   `supplier_credit_unclaimed` · Verrechnung oder Erstattung in Offene Posten. Eine Gutschrift
   bewegt keine Ware; eine Retoure erzeugt keine Gutschrift.

### Die Beschaffungsseite im Blick behalten

Der tägliche Blick auf den Einkauf.

1. **Fragen:** „Wie sieht die Beschaffungsseite aus?" → ungedeckter Bedarf, säumige Lieferanten,
   Wareneingänge ohne Rechnung, zu buchende Rechnungen, fällige Verbindlichkeiten, Skonti →
   `item_supply_demand`, `commitments_list`, `exceptions_list`, `payment_run_preview` · je
   Lieferant: geschuldet, überfällig, Guthaben (Saldenliste) → `finance_party_balances`
   Lieferantenseite
2. **Reihenfolge:** säumige Lieferanten mit blockierten Kundenaufträgen zuerst, dann Rechnungen
   buchen, dann der Zahllauf.
3. **Abends:** dieselbe Frage; der Agent berichtet, was sich geändert hat.

## Wie ein Agent Ergebnisse formuliert

- „Artikel `itm_…`: 3 verfügbar, 12 offene Kundennachfrage, 0 erwarteter Zugang; 2 Aufträge
  blockiert" ist ein Lesezugriff.
- „Bestellung `PO-…` über 20 Stück zum Listenpreis vorbereitet; Entscheidung `prp_…` steht aus" ist
  ein Vorschlag.
- „Freigegeben; `commitments_list` zeigt die Bestellbestätigung des Lieferanten über 20 zum 18.
  Sept." ist geprüft.
- Nie „bestellt" oder „bezahlt" sagen für einen Vorschlag, der nicht freigegeben wurde.

## Geht noch nicht

- Kein Bestellvorschlag oder Meldebestand: Reality zeigt ungedeckte Nachfrage, der Agent wendet
  deine Regeln an und nennt die Menge.
- Kein Lieferantenkatalog, keine Preisverhandlung, kein Versand der Bestellung; die Bestellung
  belegt, was du bestellt hast, die Nachricht an den Lieferanten geht über deinen eigenen Kanal.
- Keine Zahlsperre: eine Lieferantenrechnung lässt sich nur aus dem Zahllauf heraushalten, indem sie
  nicht ausgewählt wird (Spec 148 beschreibt die Zahlsperre; sie ist nicht gebaut).
- Keine Überweisung: der Zahllauf erfasst, was beschlossen wurde; das Geld bewegt sich außerhalb.
- Kein automatischer Abgleich eingehender Bankzeilen auf der Lieferantenseite; Lieferantenzahlungen
  werden per Vorschlag erfasst.
