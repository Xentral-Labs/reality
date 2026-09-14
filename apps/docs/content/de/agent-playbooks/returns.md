# Playbook: Retouren

Vom Satz des Kunden „ich schicke es zurück" bis zur Ware im Regal und zum ausgeglichenen Geld. Eine
Retoure ist in Reality kein Workflow mit Status: Es sind wenige Datensätze, die einander nennen, und
vier Abweichungsklassen, die melden, was zwischen ihnen noch fehlt. Ankündigung,
Retourenwareneingang, das Schicksal der Ware, Gutschrift und Erstattung werden alle von außen
orchestriert und von einem Menschen entschieden.

Jede Situation ist eine Zeile Kontext und wenige nummerierte Schritte: was du aufrufst, was du
sagst, was der Agent vorbereitet, was du entscheidest, was du prüfst. Das Werkzeug hinter einem
Schritt steht am Zeilenende nach einem Pfeil.

Lies zuerst [Ein Unternehmen auf Reality mit Agenten führen](./) für den Kreislauf und die Regeln.

## Was Reality hält und ableitet

- Eine Kundenauftragszeile hat eine ausgehende Verpflichtung, die Lieferverpflichtung. Eine
  Warenausgangsbuchung erfüllt sie. Eine Retourenbuchung vom Typ `return` nennt dieselbe
  Verpflichtung und kehrt einen Teil dieser Lieferung um; sie kann nie mehr sein als versandt wurde.
- Eine Retourenankündigung (Spec 099) ist die Aussage des Kunden, dass Ware zurückkommt: die
  Lieferung, zu der sie gehört, die Menge, optional eine Referenz wie die Retourennummer des Kunden,
  ein Grund und ein Datum. Sie ist kein Bestand: Verfügbarkeit und Versandwarteschlange ändern sich
  nicht, bevor die Ware erfasst ist.
- Was mit zurückgekommener Ware geschieht, ist ebenfalls kein Status. Die Lagerbewegung, die die
  Retoure erledigt, eine Umlagerung zurück ins Lager, eine Bestandsanpassung nach außen
  (Bestandsanpassung), eine Lieferantenretoure, sagt, welche Retoure sie erledigt
  (`resolves_movement_id`, Spec 082). Eine Retoure, die nichts erledigt, ist Bestand, den die Firma
  besitzt und nicht verkaufen kann.
- Eine Gutschrift ist ein Dokument, dessen Zeilen sagen, welche Auftragszeile sie gutschreiben.
  Erfassen und Buchen sind zwei Schritte; nur eine gebuchte Gutschrift mindert die Forderung, und
  wie sie ausgeglichen wird, gegen eine Rechnung verrechnet oder erstattet, ist ein dritter Schritt.
  Eine Rücknahmegebühr ist eine Gebührenzeile auf derselben Gutschrift, keine kleinere Gutschrift
  (Spec 095).
- `return_announcements(commitment_id?, status?)` listet Ankündigungen mit dem, worauf jede noch
  wartet. `order_explain(order_reference)` zeigt Zeilen und Verpflichtungen des Auftrags, seine
  Lagerbewegungen, Warenausgang wie Retoure, und die Dokumentzeilen, die seine Zeilen abrechnen oder
  gutschreiben. `inventory_read(view="location")` zeigt, wo zurückgekommene Ware liegt;
  `finance_balances` und die offenen Posten in der App zeigen, was eine gebuchte Gutschrift mit der
  Forderung gemacht hat.

Abweichungen, die zu diesem Bereich gehören: `announced_return_not_arrived`, `return_unresolved`,
`returned_not_credited`, `credited_not_returned`, `credit_note_unposted`, `credit_note_unsettled`.

Die Beispiele führen die Müller GmbH weiter: Auftrag SO-1042, 5 Schreibtischlampen LAMP-01, versandt
und abgerechnet auf RE-2026-0917 zu je 48,00.

## Situationen

### Ein Kunde kündigt eine Retoure an

Müller schreibt: zwei Lampen haben die falsche Farbe, sie kommen zurück. Angekommen ist nichts; die
Ankündigung ist kein Bestand.

1. **Finden:** „Müller will 2 Lampen aus SO-1042 zurückgeben." → die Lieferverpflichtung →
   `order_explain`
2. **Bedingungen, außerhalb von Reality:** volle Gutschrift, Gebühr oder Umtausch; Label und Antwort
   über deinen Kanal.
3. **Sagen:** „Erfass die Ankündigung: 2 Lampen, RMA-M-31, falsche Farbe, erwartet bis 20."
4. **Agent:** Ankündigung gegen die Lieferung, begrenzt durch das Versandte →
   `return_announce_propose`
5. **Du:** freigeben.
6. **Prüfen:** offen gelistet → `return_announcements` `status="open"` · Verfügbarkeit unverändert ·
   bis 20. nichts da → `announced_return_not_arrived` · Kunde überlegt es sich anders →
   `return_announcement_withdraw_propose`

### Die Ware kommt an

Das Paket steht an der Tür, RMA-M-31 auf dem Label. Erst Prüfplatz; wo sie landet, ist die nächste
Entscheidung.

1. **Zuordnen:** „Retoure von Müller ist da, RMA-M-31, 2 Lampen." → offene Ankündigung und ihre
   Lieferung → `return_announcements`
2. **Sagen:** „Erfass 2 Lampen zurück auf den Prüfplatz."
3. **Agent:** Retourenbuchung über 2 auf den Prüfplatz, mit Lieferung und Ankündigung; die
   Ankündigung zu nennen erfüllt sie → `movement_create_propose` `movement_type="return"`,
   `commitment_id`, `return_announcement_id`
4. **Du:** die Zählung freigeben, egal in welchem Zustand.
5. **Prüfen:** 2 zurück → `order_explain` · Ankündigung erfüllt · Lampen am Prüfplatz, `available`
   unverändert → `inventory_read` `view="location"` · heute Abend: wartet auf Gutschrift →
   `returned_not_credited`

Ein Paket ohne zuordenbare Lieferung ist keine Retoure; erst den Auftrag finden.

### Entscheiden, was mit der Ware geschieht

Zwei Lampen im Regal: eine in Ordnung, eine verkratzt. Jeder Ausgang ist eine eigene Lagerbewegung,
die die Retoure nennt.

1. **Sehen:** „Welche Retouren liegen noch im Prüfregal?" → `inventory_read` am Prüfplatz · ältere →
   `return_unresolved`
2. **Sagen:** „Eine zurück ins Hauptlager, die andere als beschädigt ausbuchen."
3. **Agent:** Umlagerung von 1 ins Hauptlager → `movement_type="transfer"` · Bestandsanpassung um 1
   nach außen, Grund „Fuß beschädigt" → `movement_type="adjustment"` · beide mit
   `resolves_movement_id` · zurück an den Lieferanten wäre `supplier_return`
4. **Du:** beides freigeben. Die Bewertung ist Sache deiner Buchhaltung.
5. **Prüfen:** `available` +1 → `item_supply_demand` · Prüfplatz leer · nicht mehr unerledigt →
   `exceptions_list`

`return_unresolved` nutzt eine Schwelle aus den eigenen erledigten Retouren; ohne erledigte zeigt es
nichts.

### Dem Kunden gutschreiben

Zwei kamen zurück, RE-0917 hat fünf abgerechnet. 96,00 stehen dem Kunden zu. Gutschrift, Buchung,
Ausgleich: drei Schritte.

1. **Liste:** „Welche Retouren sind nicht gutgeschrieben?" → SO-1042, 2 zurück, 5 abgerechnet, 0
   gutgeschrieben → `exceptions_list` · `returned_not_credited`
2. **Sagen:** „Schreib Müller die zwei zurückgekommenen Lampen auf RE-0917 gut."
3. **Agent:** GS-0041, 96,00, Position nennt die Rechnungsposition über 2 zum Rechnungspreis →
   `sales_credit_record_propose` `invoice_id`, `lines`
4. **Du:** Gutschrift freigeben, dann Buchung → `credit_note_post_propose`
5. **Prüfen:** Abweichung weg · `credit_note_unposted` weg · GS-0041 96,00 verfügbar →
   `finance_credits`

_Gutgeschrieben und nicht zurück_ (`credited_not_returned`) ist bei einer Preiskorrektur ohne Ware
richtig; nachsehen, wenn Ware erwartet wurde.

### Eine Rücknahmegebühr einbehalten

Bedingungen behalten 10 % bei Retouren ohne Mangel ein: 86,40, nicht 96,00. Weniger Einheiten
gutschreiben lässt die Retoure für immer offen; Ware voll gutschreiben und die Gebühr berechnen.

1. **Sagen:** „Schreib die zwei Lampen voll gut und berechne 9,60 Rücknahmegebühr."
2. **Agent:** Gutschrift mit Warenzeile 2 × 48,00 auf die Auftragsposition
   (`billed_document_line_id`) und Gebührenzeile „Rücknahmegebühr" −9,60 (`line_type="charge"`),
   Summe 86,40 → `document_create_propose` `document_type="credit_note"` · Buchung →
   `credit_note_post_propose`
3. **Du:** Gutschrift und Buchung freigeben; Gebühr und Grund sind genannt, nicht abgeleitet.
4. **Prüfen:** Summe 86,40 · `returned_not_credited` weg, die Warenzeile schreibt beide gut · die
   Gebührenzeile nennt keine Auftragsposition und zählt als keine Gutschrift.

### Verrechnen oder erstatten

GS-0041 ist gebucht, 96,00 verfügbar. Entweder ist RE-0917 noch offen, oder bezahlt und der Kunde
will das Geld.

1. **Sehen:** „Welche Gutschriften sind nicht ausgeglichen?" → GS-0041 96,00 verfügbar, RE-0917
   offen 240,00 → `exceptions_list` · `credit_note_unsettled` · `finance_credits`
2. **Sagen:** „Verrechne sie mit RE-0917" → `credit_note_allocate_propose` · nach deiner
   Überweisung: „Müller 96,00 erstattet, RF-78" → `customer_refund_post_propose` · oder für die
   nächste Rechnung stehen lassen.
3. **Du:** freigeben; eine Erstattung erst, nachdem das Geld floss.
4. **Prüfen:** RE-0917 144,00 offen, oder die Erstattung einmal im Journal →
   `finance_settlement_context` · weg von der Guthabenliste · Eintrag weg

### Die Retourenseite im Blick behalten

Der wöchentliche Blick auf alles, was zurückkam oder gleich kommt.

1. **Fragen:** „Wo stehen wir bei Retouren?" → angekündigt nicht da, da nicht erledigt, zurück nicht
   gutgeschrieben, gutgeschrieben nicht ausgeglichen, je mit Alter → `return_announcements`,
   `exceptions_list`
2. **Wählen:** welche diese Woche einen Vorschlag bekommen, welche Ankündigungen zurückgezogen,
   welche Gebühren erlassen werden.
3. **Nächste Woche:** die Listen schrumpfen; nichts älter als die eigene Schwelle bleibt ohne Grund.

## Wie ein Agent Ergebnisse formulieren sollte

- „Ankündigung `ann_…`: 2 von 3 angekündigten Einheiten 4 Tage nach `expected_by` angekommen" ist
  ein Lesezugriff.
- „Gutschrift `GS-…` über 10 Einheiten zu 9,00 mit Rücknahmegebühr 18,00, Summe 72,00 vorbereitet;
  Entscheidung `prp_…` offen" ist ein Vorschlag.
- „Freigegeben; `returned_not_credited` listet Auftragszeile `lin_…` nicht mehr" ist geprüft.
- Nie „erstattet" sagen für einen Vorschlag, der nicht freigegeben ist, und nie „gutgeschrieben" für
  eine Gutschrift, die erfasst, aber nicht gebucht ist.

## Noch nicht möglich

- Kein Retourenlabel, keine eigene RMA-Nummer von Reality, keine Nachricht an den Kunden: Die
  Ankündigung speichert die Referenz des Kunden; alles, was der Kunde erhält, geht über den eigenen
  Kanal.
- Kein Umtausch als eine Aktion: Ein Umtausch ist eine Retoure plus eine neue Auftragszeile, als
  zwei Dinge erfasst.
- Keine Bewertung zurückgekommener oder verschrotteter Ware; Lagerbewegungen tragen Mengen, die
  eigene Buchhaltung den Wert.
- Keine automatische Erstattung über einen Zahlungsanbieter; die Erstattung wird erfasst, nachdem
  das Geld geflossen ist.
