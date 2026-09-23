# Playbook: Forderungen und Zahlungen

Vom versandten Auftrag zur ausgeglichenen Rechnung. Reality erfasst jede Zahlung, die es erreicht,
und ordnet nur zu, was die Quelle eindeutig nennt. Alles rund um Abweichungen, Kurz- und
Überzahlungen, Zahlungen ohne brauchbaren Bezug, eine Überweisung für mehrere Rechnungen,
Gutschriften und Erstattungen, bereitet ein Agent vor und entscheidet ein Mensch.

Jede Situation ist eine Zeile Kontext und wenige nummerierte Schritte: was du aufrufst, was du
sagst, was der Agent vorbereitet, was du entscheidest, was du prüfst. Das Werkzeug hinter einem
Schritt steht am Zeilenende nach einem Pfeil.

Lies zuerst [Ein Geschäft mit Agenten auf Reality betreiben](./) und den Product Guide
[Kundenzahlungen erfassen, zuordnen und ausgleichen](/de/concepts/business-reality-guide/03-invoices-and-payments#payments-walkthrough)
für die drei Stufen, die eine Zahlung von selbst durchläuft.

## Was Reality hält und ableitet

- Eine Ausgangsrechnung ist ein Document, dessen Positionen die Auftragspositionen nennen, die sie
  abrechnen. Erfassen und Buchen sind zwei Schritte; erst eine gebuchte Rechnung ist ein offener
  Posten.
- Eine Zahlung ist ein eigenes Document mit ausgeglichener Buchung Kasse an Forderung. Eine
  SettlementAllocation verbindet den Forderungseintrag der Zahlung mit dem der Rechnung. Offener
  Betrag, bezahlt, teilbezahlt und verfügbares Guthaben werden zur Lesezeit abgeleitet.
- `finance_balances` liefert Forderungs- und Verbindlichkeitspositionen je Währung.
  `finance_settlement_context(document_id)` liest eine Rechnung (offener Betrag, Skontobedingungen)
  oder eine Zahlung (verfügbares Guthaben, passende Rechnungen, jede mit den Gründen, warum sie
  Kandidat ist). `finance_adjustment_context` liest, was an einer Rechnung gekürzt werden darf.
- Jeder Finanzvorschlag trägt `expected_revision` aus dem Kontext-Lesezugriff; eine veraltete
  Revision wird abgelehnt statt angewendet.

Abweichungen dieses Bereichs: `shipped_not_billed`, `sales_invoice_unposted`, `overdue_receivable`
(mit dem Tag `early_payment_discount_taken`, wenn die Bedingungen der Rechnung eine Minderzahlung
erklären), `unmatched_financial_event`, `credit_limit_exceeded`, `credit_note_unposted`,
`credit_note_unsettled`.

Die Beispiele nutzen Maple Retail als Kunden und kleine runde Zahlen, damit die Schritte sichtbar
bleiben.

## Situationen

### Abrechnen, was versandt ist

Versandt, aber noch keine Rechnung. Reality listet, stellt nicht selbst Rechnungen.

1. **Liste:** „Zeig mir versandt und nicht abgerechnet." → `exceptions_list` · `shipped_not_billed`
   · App: Abweichungen SO-1042 Maple, 5/5 versandt, 240,00 · SO-1043 Maple, 3/5 versandt, 150,00
2. **Sagen:** „Rechne SO-1042 komplett ab, SO-1043 für die drei versandten." Versandmenge wird
   vorher geprüft → `order_explain`
3. **Agent:** zwei Rechnungsentwürfe, RE-0917 240,00 und RE-0918 150,00, Preise aus dem Auftrag,
   nichts neu gerechnet → `sales_invoice_record_propose`
4. **Du:** Entwurf freigeben, dann Buchung freigeben → `sales_invoice_post_propose`. Erst gebucht
   ist offener Posten.
5. **Prüfen:** Liste leer · Offene Posten zeigt beide Rechnungen · Forderungen +390,00 →
   `finance_balances`

### Eine Zahlung passt genau zur Rechnung

Geld für genau das, was offen ist. Eine Bankzeile, die die Rechnung nennt, ordnet Reality selbst zu;
hier geht es um eine von Hand gemeldete Zahlung.

1. **Sagen:** „Maple hat 240,00 für RE-0917 gezahlt, heute eingegangen." →
   `finance_settlement_context(invoice)`: offen 240,00
2. **Agent:** ein Zahlungseingang 240,00, voll zugeordnet; Vorschau eingegangen 240,00, zugeordnet
   240,00, Rest 0,00 → `finance_settlement_propose` Modus `payment`
3. **Du:** freigeben.
4. **Prüfen:** RE-0917 bezahlt in Offene Posten · Zahlungseingang ohne Rest in Zahlungen →
   `finance_payments` · Forderungen −240,00

Mehr als offen wird abgelehnt; das ist die
[Überzahlung](#uberzahlung-und-den-uberschuss-spater-nutzen).

### Minderzahlung

Rechnung 1.000,00, Bank 980,00. Zwei Entscheidungen: Geld buchen, Rest klären.

1. **Sehen:** Offene Posten RE-0920 teilbezahlt, 20,00 offen; Zahlungen 980,00 zugeordnet →
   [Stufe 2 des Zahlungseingangs](../concepts/business-reality-guide/03-invoices-and-payments#die-drei-stufen-des-zahlungseingangs).
   Von Hand stattdessen: „980,00 für RE-0920 eingegangen", freigeben; die 20,00 bleiben von selbst
   offen.
2. **Fragen:** „Warum 20 zu wenig?" → Agent: 2 % Skonto bis Tag 7, Geld kam Tag 4, 2 % von 1.000 =
   20 → `finance_settlement_context`, `finance_adjustment_context`
3. **Sagen:** offen lassen · als Skonto akzeptieren · als vereinbarten Abzug oder kleinen Rest
   akzeptieren, mit Grund
4. **Agent:** Abzug 20,00, Kategorie Skonto, dein Grund als Text → `finance_adjustment_propose`
5. **Du:** freigeben. Kein stilles Ausbuchen; der Abzug ist eine eigene Buchung.
6. **Prüfen:** 980 bezahlt, 20 Abzug, 0 offen. Nirgends „1.000 gezahlt".

Reality rechnet Skonto nie aus dem Satz; der Agent nennt, was der Kunde einbehalten hat.

### Überzahlung, und den Überschuss später nutzen

Rechnung 1.000,00, Kunde schickt 1.020,00. Rechnung bezahlt; 20,00 sind Kundenguthaben, kein Umsatz.

1. **Sehen:** Zahlungen zeigt 1.020,00 zu RE-0921: 1.000,00 zugeordnet, 20,00 _verfügbar_ →
   `finance_settlement_context(payment)`. Von Hand: „1.020,00 für RE-0921 eingegangen", Agent ordnet
   1.000,00 zu und lässt 20,00 als Guthaben → `finance_settlement_propose` Modus `payment`,
   `allocation_amount` < `amount`
2. **Fragen:** „Wer hat zu viel gezahlt?" → eine Zeile je Kunde: Maple, Guthaben 20,00, Saldo −20,00
   → `finance_party_balances` `credit_only` · App: Finanzen → Salden · je Zahlungseingang →
   `finance_credits`
3. **Später nutzen:** RE-0930 offen 300,00. „Nutze Maples 20,00 auf RE-0930." →
   `finance_settlement_propose` Modus `allocate_credit`. Freigeben; RE-0930 280,00 offen, Guthaben
   0,00.
4. **Oder erstatten:** erst überweisen, dann „wir haben Maple 20,00 erstattet, Referenz RF-77" →
   Modus `refund_credit`. Reality erfasst, dass Geld floss; es überweist nie.
5. **Prüfen:** Maple weg von der Guthabenliste.

### Eine Zahlung, die niemand zuordnen kann

Bankzeile 1.250,00 von Maple, Text „Zahlung Rechnungen September". Erfasst, nichts zugeordnet.

1. **Liste:** „Welche Zahlungen sind nicht zugeordnet?" → `finance_payments` unzugeordnet ·
   `exceptions_list` · `unmatched_financial_event`
2. **Fragen:** „Wofür könnte das sein?" → Kandidaten mit Grund: RE-0925 offen 1.250,00, _Betrag
   gleich offen_; RE-0922 + RE-0923, 800 + 450, _Summe gleich Betrag_ →
   `finance_settlement_context(payment)` `candidates`
3. **Sagen:** „Ordne sie RE-0925 zu." Oder: „Als Guthaben stehen lassen, ich frage Maple." Nur das
   Erste ändert die Bücher.
4. **Agent:** Zuordnung 1.250,00 auf RE-0925, Grund steht im Vorschlag →
   `finance_settlement_propose` Modus `allocate_credit`
5. **Du:** freigeben.
6. **Prüfen:** Liste leer · RE-0925 bezahlt.

Der Agent wählt nie allein nach Betrag, wenn mehrere passen; er zeigt alle Kandidaten oder fragt den
Kunden.

### Eine Überweisung für mehrere Rechnungen

Einmal 1.000,00, Avis nennt RE-0926 400,00, RE-0927 350,00, RE-0928 250,00. Heute ein Schritt je
Rechnung.

1. **Sagen:** „Maple hat 1.000,00 für RE-0926, 0927, 0928 gezahlt."
2. **Agent:** Zahlungseingang gegen RE-0926: 400,00 zugeordnet, 600,00 Guthaben →
   `finance_settlement_propose` Modus `payment`. Freigeben.
3. **Agent:** bietet 350,00 auf RE-0927, dann 250,00 auf RE-0928 an → Modus `allocate_credit`, je
   ein Vorschlag. Jeden freigeben; Guthaben 600 → 250 → 0.
4. **Prüfen:** drei Rechnungen bezahlt · Zahlungseingang 0,00 verfügbar. Eine Differenz bliebe als
   Guthaben.

### Gutschriften und Erstattungen dagegen

Etwas war falsch oder kam zurück; dem Kunden steht Geld zu. Gutschrift, Buchung, Ausgleich: drei
Schritte.

1. **Sehen:** _zurück und nicht gutgeschrieben_ für SO-1042: 2 von 5 zurück, abgerechnet auf RE-0917
   zu 48,00 → `exceptions_list` · `returned_not_credited`
2. **Sagen:** „Schreib Maple die zwei zurückgekommenen Einheiten auf RE-0917 gut."
3. **Agent:** Gutschrift GS-0041, 96,00, Position nennt die Rechnungsposition →
   `sales_credit_record_propose`. Rücknahmegebühr: eine Gebührenzeile, Ware voll gutgeschrieben
   ([Retouren](./returns)).
4. **Du:** Gutschrift freigeben, dann Buchung → `credit_note_post_propose`
5. **Ausgleichen:** „Verrechne sie mit RE-0917" → `credit_note_allocate_propose` · oder nach deiner
   Überweisung „96,00 erstattet, RF-78" → `customer_refund_post_propose` · oder verfügbar lassen →
   `finance_credits`
6. **Prüfen:** Abweichung weg · Offene Posten zeigt Verrechnung, Erstattung oder das Guthaben.

### Das Geld im Blick behalten

Der tägliche Blick, bevor etwas entschieden wird.

1. **Fragen:** „Wie sieht die Forderungsseite aus?" → offen je Währung, überfällig, unzugeordnete
   Zahlungen, verfügbares Guthaben, neue Fälle → `finance_balances`, `exceptions_list`,
   `finance_payments`, `finance_credits` · je Kunde: offen, überfällig, Guthaben, Saldo
   (Saldenliste) → `finance_party_balances` · App: Finanzen → Salden
2. **Reihenfolge:** unzugeordnete Zahlungen zuerst (Geld ist schon da), dann die Abweichungen des
   Tages, dann Überfälliges.
3. **Abends:** dieselbe Frage; der Agent berichtet, was sich geändert hat, nicht, was er vorhatte.

## Wie ein Agent Ergebnisse formuliert

- „Rechnung `doc_…` offen 20,00 EUR nach Zahlungseingang von 980,00; die Bedingungen erlauben 2 %
  innerhalb 7 Tagen und die Zahlung kam an Tag 4" ist ein Lesezugriff mit Kontext.
- „Akzeptanz eines Skontos von 20,00 auf `doc_…` vorbereitet; Entscheidung `prp_…` steht aus" ist
  ein Vorschlag.
- „Freigegeben; Offene Posten zeigen 980,00 bezahlt, 20,00 akzeptierter Abzug, 0,00 offen" ist
  geprüft.
- Nie „der Kunde hat 1.000 gezahlt" sagen, wenn 980 ankamen.

## Geht noch nicht

- Zahlungen von Stripe, PayPal oder Shopify Payments werden nicht empfangen; heute liefern nur die
  Kontoauszugsdatei und die Demodaten Zahlungen. Der gemeinsame Eingangskern für diese Anbieter
  existiert, ihre Normalisierer nicht.
- Keine einzelne Aktion verteilt einen Zahlungseingang auf mehrere Rechnungen; siehe die Schritte
  oben.
- Kein Mahnlauf und keine automatische Liefersperre aus `credit_limit_exceeded`; die Liefersperre
  ist ein Vorschlag im Playbook Versand.
- Keine Lieferantenseite in diesem Playbook; Lieferantenrechnungen und Zahllauf stehen im
  [Playbook Einkauf](./purchasing-and-replenishment).
