# Playbook: Vertrieb und Versand

Vom eingehenden Auftrag zur versandten Verpflichtung. Reality erfasst den Auftrag und leitet je
Position eine Lieferverpflichtung (ein Commitment) ab. Reservieren, Versenden, die Verpflichtung
ändern, sie anhalten und schließen, was nie versandt wird, wird von außen orchestriert.

Jede Situation ist eine Zeile Kontext und wenige nummerierte Schritte: was du aufrufst, was du
sagst, was der Agent vorbereitet, was du entscheidest, was du prüfst. Das Werkzeug hinter einem
Schritt steht am Zeilenende nach einem Pfeil.

Lies zuerst [Ein Geschäft mit Agenten auf Reality betreiben](./) für den Kreislauf und die Regeln.

## Was Reality hält und ableitet

- Ein Auftrag ist ein Document mit DocumentLines; jede Position hat ein ausgehendes Commitment mit
  Menge und Fälligkeit. Nichts am Beleg sagt „versandt"; das wird abgeleitet.
- Eine Reservation ordnet verfügbaren Bestand einem Commitment zu. Ein Versand-Movement erfüllt es.
  Die offene Menge ist zugesagt minus versandt, zur Lesezeit.
- `fulfillment_queue` ist die Arbeitsliste: je Auftrag `order_key`, `party`, `due_at`, `priority`,
  `ship_ready`, `blocking_reasons` und die Positionen. `fulfillment_blockers` nennt die Gründe mit
  `blocker_type`, `commitment_id`, `item_id`, `shortage_quantity`. `item_supply_demand` zeigt je
  Artikel `physical`, `reserved`, `available`, `incoming`, `open_customer_demand`,
  `uncovered_demand`, `projected` und `blocked_order_count`.
- `order_explain(order_reference)` verfolgt einen Auftrag vom Quelldatensatz über Beleg,
  Verpflichtungen, Reservierungen und Lagerbewegungen bis zum abgeleiteten Zustand. Nutze es vor und
  nach jeder Änderung an einem Auftrag.

Abweichungen dieses Bereichs: `outgoing_commitment_at_risk`, `overdue_outgoing_customer_commitment`,
`order_stalled`, `reservation_exceeds_stock`, `commitment_hold_unreleased`, `party_hold_unreleased`,
`stock_expired` und, sobald Ware das Haus verlassen hat, `shipped_not_billed` (im Playbook
Forderungen behandelt).

Die Beispiele nutzen Maple Retail als Kunden, den Artikel Cedar Desk Lamp (`ITEM-004`) und kleine
Mengen.

## Situationen

### Was heute versandt werden kann

Die Morgenliste fürs Lager: Bestand da, nichts im Weg. Reality hält sie aktuell.

1. **Liste:** „Was kann heute raus?" → `fulfillment_queue`, `ship_ready` wahr, keine
   `blocking_reasons` · App: Arbeit SO-1042 Maple heute fällig, 5 Lampen reserviert, bereit ·
   SO-1045 morgen fällig, bereit · SO-1044 nicht bereit, 3 fehlen
2. **Bei Zweifel:** „Zeig mir SO-1042." → zugesagt 5, reserviert 5, versandt 0 → `order_explain`
3. **Du:** dem Lager sagen, was gepickt wird. Die Warteschlange ist eine Liste, keine Anweisung;
   nichts hat sich geändert.
4. **Prüfen:** gebuchte Warenausgänge verlassen die Warteschlange (nächste Situationen).

### Bestand für eine Verpflichtung reservieren

Ein Auftrag, der raus könnte, aber keinen Bestand zurückgelegt hat, oder einer, der als fehlend
gilt, obwohl der Artikel verfügbar ist.

1. **Sehen:** „Warum ist SO-1044 nicht bereit?" → Fehlmenge 3 → `fulfillment_blockers` · ITEM-004
   physisch 20, reserviert 17, verfügbar 3, 50 im Zulauf nächste Woche → `item_supply_demand`
2. **Sagen:** „Reserviere die drei verfügbaren Lampen für SO-1044." Hat ein anderer Auftrag den
   besseren Anspruch, für den; der Agent wählt nicht.
3. **Agent:** Reservierung von 3 für die Verpflichtung auf SO-1044; ohne Menge die ganze offene
   Menge → `reservation_propose`
4. **Du:** freigeben. Mehr als verfügbar wird abgelehnt.
5. **Prüfen:** SO-1044 3 reserviert → `order_explain` · Artikel reserviert 20, verfügbar 0. Wird
   eine Reservierung durch eine Bestandskorrektur zu groß → `exceptions_list` ·
   `reservation_exceeds_stock`; freigeben mit `reservation_release_propose`.

### Komplett versenden

Das Lager meldet, die Ware ist raus. Reality weiß nichts, bis es jemand sagt.

1. **Sagen:** „SO-1042 ist heute Morgen komplett raus, 5 Lampen aus dem Hauptlager."
2. **Agent:** ein Warenausgang je Auftragsposition, Menge 5, Standort, Verpflichtung, Zeit; Charge
   oder Seriennummer bei geführten Artikeln → `movement_create_propose` `movement_type="shipment"`
3. **Du:** freigeben, was physisch passiert ist; sind vier raus, sag vier.
4. **Prüfen:** versandt 5, offen 0 → `order_explain` · aus der Warteschlange · heute Abend auf der
   Abrechnungsliste → `shipped_not_billed`,
   [Forderungen](./receivables-and-payments#abrechnen-was-versandt-ist)

### In Teilen versenden

3 von 5 Lampen sind raus, der Rest fehlt. Die Verpflichtung bleibt ganz, der Rest bleibt offen.

1. **Sagen:** „SO-1043 ist heute mit 3 von 5 raus."
2. **Agent:** Warenausgang über 3; die Verpflichtung bleibt unberührt, 2 offen →
   `movement_create_propose` `quantity=3`
3. **Du:** freigeben. Ob 2 nachkommen oder der Kunde 3 nimmt, ist die nächste Situation.
4. **Prüfen:** versandt 3, offen 2 → `order_explain` · Warteschlange behält SO-1043 mit dem Rest.
   Die letzten 2 genauso melden.

### Der Kunde akzeptiert weniger oder später

Die restlichen 2 sind so bald nicht zu decken; der Kunde nimmt nur 3, oder wartet bis zum 25.

1. **Sehen:** Verpflichtung gefährdet, kein Zulauf vor Fälligkeit → `exceptions_list` ·
   `outgoing_commitment_at_risk` · `item_supply_demand`
2. **Außerhalb von Reality einigen:** Maple anrufen; sie nehmen 3.
3. **Sagen:** „Maple akzeptiert 3 auf SO-1043, telefonisch mit Frau Weber heute vereinbart."
4. **Agent:** Revision auf 3 mit wer und wann; `due_at` stattdessen, wenn der Termin wandert; nie
   unter dem Versandten → `commitment_revise_propose`
5. **Du:** nur mit der Vereinbarung in der Hand freigeben.
6. **Prüfen:** zugesagt 3, versandt 3, offen 0, Revision in der Historie → `order_explain` ·
   Risikoeintrag weg. Die anderen 2 später als eigene Lieferung: ein neuer Auftrag →
   `order_create_propose`. Kein Kommando „in zwei Lieferungen teilen".

### Einen Auftrag oder einen Kunden anhalten

„Das noch nicht versenden": Kreditlimit, unzustellbare Adresse, Compliance. Eine Liefersperre
blockiert den Versand; Aufträge und Reservierungen bleiben.

1. **Sehen:** Maple über dem Kreditlimit → `exceptions_list` · `credit_limit_exceeded`; oder ein
   Kollege meldet eine falsche Adresse.
2. **Sagen:** „Halte SO-1045 an, bis die Adresse geklärt ist." · „Liefersperre für Maple Retail,
   Kreditprüfung."
3. **Agent:** Sperre auf der Verpflichtung → `commitment_hold_propose`, `reason_code` aus
   `credit_check`, `customer_request`, `address_clarification`, `compliance`, `manual_review`,
   `other` · oder auf dem Kunden → `party_delivery_hold_propose`
4. **Du:** freigeben.
5. **Prüfen:** Sperre unter den Blockgründen des Auftrags → `fulfillment_queue` · sichtbar bis zur
   Aufhebung → `commitment_hold_unreleased`, `party_hold_unreleased`. Aufheben: „Hebe die
   Liefersperre auf SO-1045 auf" → `commitment_hold_release_propose`,
   `party_delivery_hold_release_propose`

### Verpflichtungen schließen, die nie versandt werden

Ein Import hat Hunderte längst gelieferte Verpflichtungen offen gelassen. Ein Mensch schließt sie
gesammelt, mit Grund.

1. **Vorschau:** „Wie viele Verkaufsverpflichtungen mit Fälligkeit vor dem 1. Juli sind offen?" →
   212, mit Stichprobe von zehn → `stale_closure_preview` `direction="sales"`, `due_before`
2. **Stichprobe:** ein echter offener Auftrag dabei? Vorher versenden oder revidieren; die
   Schließung nimmt alles Gezählte.
3. **Sagen:** „Schließ sie, Grund: aus dem Altsystem migriert, vor Go-live geliefert."
4. **Agent:** Sammelschließung mit genau der Vorschauzahl; eine geänderte Zahl wird abgelehnt →
   `stale_closure_propose` `expected_count=212`
5. **Du:** freigeben.
6. **Prüfen:** nicht mehr offen → `commitments_list` · jeder Auftrag zeigt Schließung und Grund →
   `order_explain`

### Einen Auftrag einem Kunden oder Kollegen erklären

„Kann mein Auftrag heute raus?" „Warum ist SO-1044 spät?" Ein Lesezugriff; nichts wird entschieden.

1. **Finden:** „Such Maples Auftrag vom 8. September." → SO-1044 → `business_records_discover`
   `family="document"`
2. **Verfolgen:** 5 zugesagt, 3 reserviert, 0 versandt, 2 fehlen, 50 im Zulauf am 18. →
   `order_explain` · warum eine Abweichung gemeldet wird → `exception_explain`
3. **Antworten:** „Drei heute, zwei nach dem 18." Datensätze und Mengen nennen; sagen, was es nicht
   beweist: Der Termin des Lieferanten ist dessen Versprechen.

## Wie ein Agent Ergebnisse formuliert

- „Verpflichtung `cmt_…` über 6 Stück: 4 versandt am 10. Sept., 2 offen, 2 reserviert" ist ein
  Lesezugriff.
- „Versand von 2 Stück gegen `cmt_…` vorbereitet; Entscheidung `prp_…` steht aus" ist ein Vorschlag.
- „Freigegeben `prp_…`; `order_explain` zeigt jetzt 6 versandt, 0 offen" ist ein geprüftes Ergebnis.
- Nie „versandt" sagen für einen Vorschlag, der nicht freigegeben wurde.

## Geht noch nicht

- Keine Picklisten oder Versandetiketten; Reality erfasst, dass Ware das Haus verlassen hat, es
  führt nicht das Lager.
- Keine automatische Reservierung beim Auftragseingang und keine automatische Freigabe bei
  Liefersperre; beides sind Vorschläge.
- Kein Split einer Verpflichtung in zwei terminierte Verpflichtungen; Teillieferungen oder Änderung
  plus neuer Auftrag.
- Kein Rückstands- oder Nachschubvorschlag; `item_supply_demand` zeigt ungedeckte Nachfrage, der
  Agent schlägt den Einkauf vor ([Playbook Einkauf](./purchasing-and-replenishment)).
