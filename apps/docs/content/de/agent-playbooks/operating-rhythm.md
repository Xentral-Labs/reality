# Betriebsrhythmus: täglich, wöchentlich, monatlich

Was ein Handelsbetrieb auf Reality tun muss, und wie oft. Nur die konkreten Aufgaben; die Details
stehen in den Playbooks. Jede Zeile nennt das Signal, das die Aufgabe auslöst, und verlinkt, wo ein
Playbook den Fall schon beschreibt, auf die Situation. Zeilen mit _Beispiel folgt_ haben noch kein
durchgespieltes Beispiel.

Der Rhythmus setzt die zwei automatischen Eingänge voraus: Aufträge kommen aus dem Shop oder den
Demodaten, Zahlungen aus Bank, Anbieter oder Demodaten. Alles darunter ist das, was ein Mensch, ein
Workflow oder ein Agent hinzufügen muss.

## Jeden Tag

1. **Versenden, was bereit ist.** `fulfillment_queue` lesen; verfügbaren Bestand reservieren, die
   Warenausgänge des Lagers buchen, ganz oder in Teilen.
   [Versand: Situationen](./order-to-cash-fulfilment#situationen)
2. **Annehmen, was gekommen ist.** Jede Lieferung als Wareneingang mit der gezählten Menge erfassen;
   Falsches zurückschicken.
   [Einkauf: Wareneingang buchen](./purchasing-and-replenishment#wareneingang-buchen)
3. **Abrechnen, was versandt ist.** `exceptions_list` → `shipped_not_billed`,
   `sales_invoice_unposted`: Rechnungen erfassen und buchen.
   [Forderungen: Abrechnen, was versandt ist](./receivables-and-payments#abrechnen-was-versandt-ist)
4. **Das eingehende Geld bearbeiten.** `exceptions_list` → `unmatched_financial_event`: Zuordnungen
   für Zahlungen mit Kandidaten vorschlagen; Zahlungen erfassen, die nicht über eine Quelle kamen.
   [Forderungen: Eine Zahlung, die niemand zuordnen kann](./receivables-and-payments#eine-zahlung-die-niemand-zuordnen-kann)
5. **Die Abweichungen des Tages ansehen.** Neue Kurz- und Überzahlungen: offen lassen, erklären,
   Skontoabzug akzeptieren, Guthaben nutzen oder erstatten.
   [Forderungen: Minderzahlung](./receivables-and-payments#minderzahlung) und die Situation zur
   Überzahlung darunter
6. **Die Abweichungen einmal lesen.** `exceptions_list`: gefährdete Verpflichtungen, stockende
   Aufträge, Reservierungen, die nicht mehr passen, Interpretationsfehler, stille Quellen.
   Entscheiden, welche heute einen Vorschlag brauchen.
   [Stammdaten: Eine Quelle ist verstummt](./master-data-and-sources#eine-quelle-ist-verstummt),
   [Etwas kam an und wurde nicht verstanden](./master-data-and-sources#etwas-kam-an-und-wurde-nicht-verstanden)
7. **Entscheiden.** `proposals_awaiting_approval`: jeder offene Vorschlag bekommt eine Entscheidung;
   nichts wartet ohne Grund über Nacht.
   [Index: der Kreislauf](./#der-kreislauf-dem-jedes-playbook-folgt)
8. **Prüfen und berichten.** Lesen, was sich heute geändert hat (`order_explain`,
   `finance_balances`), und das Gelesene berichten, nicht die Absicht.

## Jede Woche

1. **Nachschub.** `item_supply_demand`: ungedeckte Nachfrage, projizierter Bestand, säumige
   Bestellbestätigungen der Lieferanten; Bestellungen anlegen.
   [Einkauf: Finden, was zu kaufen ist](./purchasing-and-replenishment#finden-was-zu-kaufen-ist),
   [Eine Bestellung anlegen](./purchasing-and-replenishment#eine-bestellung-anlegen)
2. **Lieferanten bezahlen.** `payment_run_preview(pay_by = Ende nächster Woche)`: lohnende Skonti
   nehmen, Fälliges zahlen, Summe bestätigen.
   [Einkauf: Lieferanten mit einem Zahllauf bezahlen](./purchasing-and-replenishment#lieferanten-mit-einem-zahllauf-bezahlen)
3. **Die Rechnungsprüfung bereinigen.** `billed_not_received`, `receipt_unbilled`,
   `invoice_price_differs`, `duplicate_supplier_invoice`: jeden Fall mit dem Einkäufer klären, dann
   buchen oder zurückschicken.
   [Einkauf: Die Rechnungsprüfung](./purchasing-and-replenishment#die-rechnungsprufung)
4. **Überfällige Forderungen durchsehen.** `overdue_receivable`, `credit_limit_exceeded`: den Kunden
   außerhalb von Reality erinnern, eine Liefersperre setzen, wo das Risiko real ist, gesammelte
   Abzüge akzeptieren oder ablehnen.
   [Versand: Einen Auftrag oder einen Kunden anhalten](./order-to-cash-fulfilment#einen-auftrag-oder-einen-kunden-anhalten)
5. **Schließen, was nicht versandt wird.** `stale_closure_preview` für Verpflichtungen, die ein
   Import zurückgelassen hat; Reservierungen und Liefersperren ohne Grund aufheben.
   [Versand: Situationen](./order-to-cash-fulfilment#situationen)
6. **Retouren bearbeiten.** Offene `return_announcements`, `announced_return_not_arrived`,
   `returned_not_credited`, `credited_not_returned`: Retourenwareneingang, Gutschrift, Erstattung
   buchen. [Retouren: Die Ware kommt an](./returns#die-ware-kommt-an),
   [Dem Kunden gutschreiben](./returns#dem-kunden-gutschreiben),
   [Verrechnen oder erstatten](./returns#verrechnen-oder-erstatten)
7. **Daten aufräumen, die blockieren.** `units_not_comparable`, Lücken in Preislisten, fehlende
   Zahlungsbedingungen, neue Kunden oder Artikel aus den Quellen.
   [Stammdaten: Einheiten in Beziehung setzen](./master-data-and-sources#einheiten-in-beziehung-setzen),
   [Anlegen, was eine Quelle braucht](./master-data-and-sources#anlegen-was-eine-quelle-braucht)

## Jeden Monat

1. **Die Finanzübergabe vorbereiten.** Keine ungebuchten Rechnungen oder Gutschriften, keine
   unerklärten unzugeordneten Zahlungen, offene Posten und verfügbares Guthaben durchgesehen; das
   Journal an das Buchhaltungsziel übergeben. _Beispiel folgt (Finanzübergabe, Spec 148 Ziele und
   Zuordnungen)._
2. **Die Altersstruktur prüfen.** Forderungen und Verbindlichkeiten nach Alter; Abzüge, Erstattungen
   und Liefersperren für das entscheiden, was offen bleibt; Kreditlimits prüfen.
   [Forderungen: Das Geld im Blick behalten](./receivables-and-payments#das-geld-im-blick-behalten),
   [Einkauf: Die Beschaffungsseite im Blick behalten](./purchasing-and-replenishment#die-beschaffungsseite-im-blick-behalten)
3. **Bestand zählen und korrigieren.** Inventur gegen `inventory_read`; Korrekturen als
   Lagerbewegungen mit Grund; abgelaufene Chargen (`expired_lots`, `stock_expired`) ausbuchen oder
   neu datieren. _Beispiel folgt._
4. **Die Befugnis des Agenten prüfen.** Entscheidungshistorie: welche Vorschlagsklassen automatisch
   freigegeben, welche abgelehnt wurden und warum; die delegierten Klassen anpassen. _Beispiel
   folgt._
5. **Die Quellen prüfen.** `interpretation_coverage`: was jede Quelle geliefert hat, was
   fehlgeschlagen ist, was Prüfung braucht; Quellen-Updates, die eine Entscheidung verlangen.
   [Stammdaten: Was die Quellen geliefert haben, durchsehen](./master-data-and-sources#was-die-quellen-geliefert-haben-durchsehen)
6. **Bedingungen und Preise auffrischen.** Zahlungsbedingungen, Preislisten und Staffeln,
   Lieferantenvereinbarungen, die sich im Monat geändert haben.
   [Stammdaten: Preise](./master-data-and-sources#preise-listen-staffeln-und-wer-welche-bekommt),
   [Zahlungsbedingungen](./master-data-and-sources#zahlungsbedingungen)

## Wie der Rhythmus zu den Playbooks passt

Die Tagesliste ist das tägliche Minimum des Index in Arbeitsreihenfolge. Wochen- und Monatsaufgaben
sind derselbe Kreislauf auf langsamere Signale angewandt: Nachschub, Verbindlichkeiten,
Altersstruktur, Bestand, Quellen. Nichts im Rhythmus tut Reality von selbst; jede Zeile ist ein
Lesezugriff, gefolgt von Vorschlägen und Entscheidungen.
