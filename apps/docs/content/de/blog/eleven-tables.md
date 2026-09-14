---
title: Elf Tabellen
description:
  Elf Arten von Dingen, die über ein Geschäft wahr sein können — als Antwort auf vier Fragen. Und
  vier Antworten, die bewusst nicht dabei sind.
date: 2026-09-04
author: Benedikt Sauter
order: 2
tags:
  - Business Reality
sidebar: false
---

# Elf Tabellen

<PostMeta />

Das Modell kennt elf Arten von Behauptung. Nicht elf Tabellen in einer Datenbank — elf Arten von
Dingen, die über ein Geschäft wahr sein können.

Es sind elf, weil ein Geschäft vier verschiedene Fragen beantworten muss. Die Antworten zu
vermischen ist genau das, was ein klassisches Schema unbegrenzt wachsen lässt. Eine Behauptung, eine
Frage.

## Was hat jemand gesagt?

- `source_record` — das Payload, das ein externes System geschickt hat. Wörtlich aufbewahrt, nie
  bearbeitet. Noch keine Wahrheit über dein Geschäft: die Aufzeichnung, dass jemand etwas gesagt
  hat.

## Wie haben wir es verstanden?

- `document` und `document_line` — deine Lesart dieses Payloads. Ein Auftrag über zwölf Laufräder.
  Wiederholbar: lies es später neu, und du bekommst eine neue Interpretation — nicht eine mutierte
  alte.

## Was ist im Geschäft wahr?

- `commitment` — was du zugesagt hast. Zwölf Laufräder zum vereinbarten Preis. Das gehört jetzt dir,
  nicht dem Absender: korrigier morgen das Payload, die Zusage steht, denn ein Kunde erwartet sie.
- `reservation` — was gegen diese Zusage gehalten wird. Acht im Regal. Gehalten ist nicht geliefert
  und nicht zugesagt; es ist ein Drittes, und es lässt sich freigeben.
- `movement` — was sich physisch bewegt hat. Acht haben das Regal verlassen. Die einzige Behauptung,
  die in der Welt passiert ist — kein geändertes Feld macht sie rückgängig. Du korrigierst sie mit
  einer weiteren Bewegung.
- `ledger_entry` — was die Buchhaltung anerkannt hat. Zeilen, die aufgehen, und rückwirkend weiter
  aufgehen.
- `settlement_allocation` — welche Zahlung welche Forderung ausgeglichen hat, und um wie viel. Kein
  Bezahlt-Kennzeichen: eine Zahlung kann mehrere Rechnungen ausgleichen, eine Rechnung mehrere
  Zahlungen aufnehmen.
- `fact` — eine beobachtete Eigenschaft, für die keine andere Art von Behauptung zuständig ist. Dass
  dieser Auftrag Priorität hat.

## Was ist passiert, und was folgt daraus?

- `business_event` — dass etwas passiert ist, und wann.
- `projection_row` — eine Antwort, abgeleitet aus allem Vorstehenden. Alles, was du auf einem
  Bildschirm liest, ist eine.

## Ein Auftrag, einmal ganz durch

Zwölf Laufräder bestellt, acht geliefert, ein Teil der Rechnung bezahlt. Nichts überschreibt etwas
anderes.

| Was passiert                      | Was geschrieben wird        |
| --------------------------------- | --------------------------- |
| Der Shop schickt den Auftrag      | `source_record`             |
| Wir lesen ihn als Auftrag über 12 | `document`, `document_line` |
| Wir sagen 12 zu                   | `commitment`                |
| Das Lager hält 8                  | `reservation`               |
| 8 verlassen das Regal             | `movement`                  |
| Wir stellen die 8 in Rechnung     | `ledger_entry`              |
| Der Kunde zahlt einen Teil        | `settlement_allocation`     |
| „Wie viel ist noch offen?“        | `projection_row`            |

Die letzte Zeile ist der Punkt. „Vier noch offen“ steht nirgends gespeichert. Es ist die Zusage über
zwölf verglichen mit der Bewegung über acht, berechnet in dem Moment, in dem du fragst — und beide
Eingaben sind noch da.

Das Handbuch schickt denselben Auftrag durch einen ganzen Geschäftsmonat, mit Fehlmenge,
Teil-Wareneingang und Endlieferung:
[Aufträge, Reservations und Bestand](/de/concepts/business-reality-guide/02-orders-stock-and-deliveries).

## Die vier Antworten, die nicht in der Liste stehen

Kein Auftragsstatus. Keine offene Menge. Kein Bestandssaldo. Kein Bezahlt-Kennzeichen.

Jedes davon ist ein Ergebnis, keine Behauptung. „Teilweise geliefert“ ist die Zusage verglichen mit
den Bewegungen. Die offene Menge ist derselbe Vergleich als Zahl. Bestand ist die Summe der
Bewegungen an einem Lagerort. Bezahlt ist die Forderung verglichen mit ihren Zuordnungen.

Speicher sie, und du besitzt vier Kopien der Wahrheit, die sich widersprechen dürfen. Leite sie ab,
und die Frage „wo kommt diese Zahl her“ beantwortet sich selbst: aus diesen Eingaben, und die sind
noch da.

## Warum sie getrennt bleiben

Weil sie unterschiedliche Lebensdauern und unterschiedliche Verantwortliche haben. Ein Payload kann
der Absender ersetzen. Eine Zusage überlebt das Payload. Eine Bewegung überlebt alles, weil sie
passiert ist.

Wirf zwei davon zusammen, und du verlierst eine Frage, die du beantworten musst.

## Wo du nachschaust

- [Das Datenmodell](/de/concepts/business-reality-guide/01-from-erp-documents-to-business-reality#data-model)
  — jede Art von Behauptung und wofür sie zuständig ist
- [Die Tool-Referenz](/de/tool-usage/) — aus dem laufenden Code erzeugt, inklusive des Details und
  der Infrastruktur, die um diese elf herum liegt

Als Nächstes in dieser Reihe: was dein ERP eigentlich meint, wenn es „teilweise geliefert“ sagt.

<Subscribe />
