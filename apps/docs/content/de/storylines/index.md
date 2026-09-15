---
aside: false
---

# Storylines

Storylines sind der Spielplatz, um Reality kennenzulernen. Wähle eine, drücke Starten und spiele
einen echten Geschäftsablauf Schritt für Schritt in einer eigenen Sandbox, einen Auftrag von der
Anlage bis zum Monatsrückblick oder einen Einkauf von der Bestellung bis zur Zahlung mit Skonto.
Nichts, was du hier tust, berührt ein echtes Unternehmen, also probiere aus: bestätige, verwirf,
nimm den anderen Abzweig, verlasse die Storyline und stöbere in der Sandbox, komm zurück. Jeder
Schritt ist ein gewöhnlicher Befehl oder eine gewöhnliche Lesung. Du siehst die Situation, bereitest
den Schritt vor, liest die Vorschau, bestätigst und liest dann, was Reality aufgezeichnet hat:
welche Ereignisse, Datensätze und Fakten dazukamen und welche Abweichungen eine Regel gehoben oder
geschlossen hat, und warum. Genau darum geht es: den Regeln bei der Arbeit auf Evidenz zuzusehen,
statt darüber zu lesen.

Öffne **Storyline** in der Navigation der App. Die Bibliothek zeigt die Storylines und wo du in
jeder stehst; eine Karte startet oder setzt fort. Beim Spielen erzählt die Schrittkarte links die
Geschichte, die Mitte zeigt die Ansicht, die der Schritt nennt, in der App selbst, und das Protokoll
rechts listet jeden Aufruf mit Eingabe, Ergebnis und Katalogeintrag, darunter, was der Schritt
hinzugefügt hat. Klicke auf einen Aufruf, einen Datensatz oder eine Abweichung, und du landest auf
der gewohnten Seite dazu. Im Sandbox-Chat arbeitest du frei in der Sandbox der aktuellen Storyline;
das Protokoll zeichnet weiter auf. **Freies Spiel** ist ein eigener Einstieg in Navigation und
Bibliothek. Wähle deine aktuelle oder eine andere zugängliche Firma oder erstelle eine dauerhafte
Sandbox mit Beispieldaten. Vorhandene Firmen verwenden ihre tatsächlichen Daten; Änderungen musst du
bestätigen. Dafür brauchst du keine Storyline und keine vorgegebenen Schritte. Aufgezeichnete
Antwortnachweise gibt es in Storyline- und Free-Play-Sandboxes; andernfalls wird auf fehlende
Nachweise hingewiesen. Die Automatik spielt die Schritte für eine Vorführung nach Zeit und hält bei
jedem Klick an.

Baue eigene und gib sie weiter. Die Dateien unten sind die Pakete, die Reality mitliefert, einfaches
YAML mit symbolischen Verweisen: Lade eines herunter, ändere Texte, Beträge oder Schritte und
importiere es in deine Bibliothek. Ein von Hand gespielter Durchlauf lässt sich als
Storyline-Entwurf exportieren; der schnellste Weg zu einer neuen ist also, sie einmal zu spielen und
die Texte zu ergänzen. Schick ein Paket einer Kollegin, einem Kunden oder uns; beim Import wird es
gegen die Kataloge geprüft und läuft unter genau den Regeln wie eine eingebaute. Das Schema lässt
einen Editor das Format vervollständigen.

Automatisch aus `packages/reality-core/storylines/*.storyline.yaml` erzeugt. Diese Seite nicht von
Hand bearbeiten.

- [Paketschema (JSON Schema)](/storylines/storyline.schema.json)

## Erste Runde {#storyline-first-round}

Sieben Schritte, etwa fünf Minuten. Ein Auftrag, eine Abweichung, die von selbst kommt und von
selbst geht, und ein Versand, den das System verweigert. Der kürzeste Weg zu sehen, wie Reality
arbeitet.

- [Paket herunterladen](/storylines/first-round.storyline.yaml) (`first-round` v1)

### Schritte

| Schritt                          | Art    | Befehl oder Lesungen                      | Ansicht                     | Erwartete Abweichungen          |
| -------------------------------- | ------ | ----------------------------------------- | --------------------------- | ------------------------------- |
| 1. Auftrag anlegen               | Befehl | `order_create`                            | `view:orders`               | ▲ `outgoing_commitment_at_risk` |
| 2. Abweichung erklären lassen    | Lesung | `exception_explain`, `item_supply_demand` | `view:supply_demand`        |                                 |
| 3. Zu kleine Lieferung einbuchen | Befehl | `movement_create`                         | `view:movements`            |                                 |
| 4. Bestand reservieren           | Befehl | `reserve`                                 | `view:reservations`         | ✓ `outgoing_commitment_at_risk` |
| 5. Versand versuchen             | Befehl | `movement_create`                         | `view:fulfillment_blockers` |                                 |
| 6. Sperre aufheben               | Befehl | `party_delivery_hold_release`             | `view:fulfillment_blockers` |                                 |
| 7. Ware versenden                | Befehl | `movement_create`                         | `view:movements`            | ▲ `shipped_not_billed`          |

## Auftrag bis Abschluss {#storyline-order-to-close}

Ein Kundenauftrag, eine zu kleine Lieferung, ein gesperrter Versand, eine Überzahlung und ein
Monatsrückblick. Schritt für Schritt spielen und lesen, was jeder Schritt aufgezeichnet hat.

- [Paket herunterladen](/storylines/order-to-close.storyline.yaml) (`order-to-close` v1)

### Schritte

| Schritt                                                       | Art    | Befehl oder Lesungen                                       | Ansicht                     | Erwartete Abweichungen                                       |
| ------------------------------------------------------------- | ------ | ---------------------------------------------------------- | --------------------------- | ------------------------------------------------------------ |
| 1. Auftrag anlegen                                            | Befehl | `order_create`                                             | `view:orders`               | ▲ `outgoing_commitment_at_risk`                              |
| 2. Kundenreferenz festhalten                                  | Befehl | `fact_observe`                                             | `view:documents`            |                                                              |
| 3. Zu kleine Lieferung einbuchen                              | Befehl | `movement_create`                                          | `view:movements`            |                                                              |
| 4. Bestand reservieren                                        | Befehl | `reserve`                                                  | `view:reservations`         | ✓ `outgoing_commitment_at_risk`                              |
| 5. Versand versuchen                                          | Befehl | `movement_create`                                          | `view:fulfillment_blockers` |                                                              |
| 6. Sperre erklären                                            | Lesung | `exception_explain`, `finance.party_balances.list`         | `view:open_items`           |                                                              |
| 7. Saldo ansehen (Alternative über eine Abzweigung)           | Lesung | `finance.party_balances.list`, `commitments`               | `view:commitments`          |                                                              |
| 8. Überzahlung erfassen                                       | Befehl | `finance.settlement.apply`                                 | `view:payments`             | ▲ `unmatched_financial_event`, ✓ `overdue_receivable`        |
| 9. Sperre aufheben                                            | Befehl | `party_delivery_hold_release`                              | `view:fulfillment_blockers` |                                                              |
| 10. Ware versenden                                            | Befehl | `movement_create`                                          | `view:movements`            | ▲ `shipped_not_billed`                                       |
| 11. Auftrag fakturieren                                       | Befehl | `sales_invoice_record`                                     | `view:open_items`           | ✓ `shipped_not_billed`                                       |
| 12. Guthaben verrechnen                                       | Befehl | `finance.settlement.apply`                                 | `view:open_items`           | ✓ `unmatched_financial_event`                                |
| 13. Guthaben erstatten (Alternative über eine Abzweigung)     | Befehl | `finance.settlement.apply`                                 | `view:payments`             | ▲ `unmatched_financial_event`, ✓ `unmatched_financial_event` |
| 14. Guthaben stehen lassen (Alternative über eine Abzweigung) | Lesung | `finance.credits.list`                                     | `view:payments`             |                                                              |
| 15. Bestand prüfen                                            | Lesung | `inventory`, `commitments`                                 | `view:inventory`            |                                                              |
| 16. 40 nachbestellen                                          | Befehl | `order_create`                                             | `view:orders`               |                                                              |
| 17. 20 nachbestellen (Alternative über eine Abzweigung)       | Befehl | `order_create`                                             | `view:orders`               |                                                              |
| 18. Monatsrückblick                                           | Lesung | `exceptions`, `finance.party_balances.list`, `commitments` | `view:activity`             |                                                              |

## Einkauf bis Zahlung {#storyline-purchase-to-pay}

Eine Bestellung, eine zu kleine Lieferung, eine Rechnung über mehr als angekommen ist zu einem
Preis, den niemand vereinbart hat, dieselbe Rechnung ein zweites Mal und ein Skonto mit Frist.
Schritt für Schritt spielen und zusehen, wie Regeln ihre Abweichungen heben und schließen.

- [Paket herunterladen](/storylines/purchase-to-pay.storyline.yaml) (`purchase-to-pay` v1)

### Schritte

| Schritt                                                                           | Art    | Befehl oder Lesungen              | Ansicht            | Erwartete Abweichungen                                          |
| --------------------------------------------------------------------------------- | ------ | --------------------------------- | ------------------ | --------------------------------------------------------------- |
| 1. Bestellung anlegen                                                             | Befehl | `order_create`                    | `view:orders`      |                                                                 |
| 2. Lieferavis erfassen                                                            | Befehl | `shipment_notice_record`          | `view:commitments` |                                                                 |
| 3. Wareneingang buchen                                                            | Befehl | `movement_create`                 | `view:movements`   |                                                                 |
| 4. Eingangsrechnung erfassen                                                      | Befehl | `document_create`                 | `view:documents`   | ▲ `billed_not_received`, ▲ `invoice_price_differs`              |
| 5. Rechnung buchen                                                                | Befehl | `supplier_invoice_post`           | `view:open_items`  | ▲ `purchase_discount_available`                                 |
| 6. Konten für Abzüge einrichten                                                   | Befehl | `finance.account.initialize`      | `view:journal`     |                                                                 |
| 7. Die drei Abweichungen lesen                                                    | Lesung | `exception_explain`, `exceptions` | `view:open_items`  |                                                                 |
| 8. Die Rechnung kommt ein zweites Mal                                             | Befehl | `document_create`                 | `view:documents`   | ▲ `duplicate_supplier_invoice`                                  |
| 9. Auch die Kopie wird gebucht                                                    | Befehl | `supplier_invoice_post`           | `view:open_items`  | ▲ `purchase_discount_available`                                 |
| 10. Die falsche Buchung stornieren                                                | Befehl | `ledger_reverse`                  | `view:journal`     | ✓ `duplicate_supplier_invoice`, ✓ `purchase_discount_available` |
| 11. Die fehlenden zehn kommen an                                                  | Befehl | `movement_create`                 | `view:movements`   | ✓ `billed_not_received`                                         |
| 12. Innerhalb der Skontofrist zahlen                                              | Befehl | `supplier_payment_post`           | `view:payments`    |                                                                 |
| 13. Das Skonto ziehen, mit Nachweis                                               | Befehl | `finance.adjustment.accept`       | `view:open_items`  | ✓ `purchase_discount_available`                                 |
| 14. Monatsrückblick                                                               | Lesung | `exceptions`                      | `view:open_items`  |                                                                 |
| 15. Die Gutschrift des Lieferanten erfassen (Alternative über eine Abzweigung)    | Befehl | `document_create`                 | `view:documents`   |                                                                 |
| 16. Die Gutschrift buchen (Alternative über eine Abzweigung)                      | Befehl | `supplier_credit_note_post`       | `view:open_items`  | ▲ `supplier_credit_unclaimed`                                   |
| 17. Die Gutschrift mit der Rechnung verrechnen (Alternative über eine Abzweigung) | Befehl | `supplier_credit_note_allocate`   | `view:open_items`  | ✓ `supplier_credit_unclaimed`                                   |
| 18. Den Nettobetrag innerhalb der Frist zahlen (Alternative über eine Abzweigung) | Befehl | `supplier_payment_post`           | `view:payments`    |                                                                 |
| 19. Das Skonto ziehen, mit Nachweis (Alternative über eine Abzweigung)            | Befehl | `finance.adjustment.accept`       | `view:open_items`  | ✓ `purchase_discount_available`                                 |
