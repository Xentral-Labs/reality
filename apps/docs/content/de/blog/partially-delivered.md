---
title: Dein ERP sagt „teilweise geliefert“. Frag es mal, was das heißt.
description:
  Ein Statusfeld beantwortet vier Fragen gleichzeitig und behält keine der Eingaben. Das ist der
  Defekt — und Agenten machen ihn teuer.
date: 2026-09-18
author: Benedikt Sauter
draft: true
tags:
  - Business Reality
sidebar: false
---

# Dein ERP sagt „teilweise geliefert“. Frag es mal, was das heißt.

<PostMeta />

Öffne in einem beliebigen klassischen ERP einen Kundenauftrag. Weit oben steht ein Statusfeld, und
heute steht dort _teilweise geliefert_. Die ganze Firma behandelt das als Tatsache. Es ist keine. Es
ist eine Zusammenfassung, die irgendein Code irgendwann berechnet hat — aus Eingaben, die das System
längst nicht mehr aufbewahrt.

Versuch mal, aus diesem einen Feld das hier zu beantworten:

- Hat der Kunde Ware bekommen, oder hat jemand im Lager auf einen Knopf gedrückt?
- Welche Menge ist dem Kunden noch zugesagt, und welche steht bloß noch auf einer Position?
- Wenn Bestand für diesen Auftrag gehalten wird: wegen der Zusage oder wegen der Lieferung?
- Und wenn der Kunde morgen sagt, er habe letzte Woche storniert — was passiert dann mit der
  Antwort?

Das Feld kann keine davon beantworten. Es war nie dafür gebaut. Es war dafür gebaut, dass sich ein
Mensch vor einem Bildschirm schnell einen groben Eindruck verschafft. Dreißig Jahre lang hat das
gereicht, weil dieser Mensch den fehlenden Kontext aus dem Kopf ergänzt hat.

## Vier Arten von Wahrheit in einem Kostüm

Unter diesem Status stecken mindestens vier verschiedene Behauptungen. Sie haben unterschiedliche
Lebensdauern, unterschiedliche Verantwortliche und unterschiedliche Folgen, wenn sie sich als falsch
herausstellen.

Da ist, was ein externes System **gesagt** hat. Ein Shop, ein Marktplatz, ein EDI-Partner hat ein
Payload geschickt. Das ist die Aufzeichnung einer Aussage, nicht der Wirklichkeit — und morgen kann
derselbe Absender sie durch eine neuere Aussage ersetzen.

Da ist, was deine Firma **zugesagt** hat. Zwölf Stück zum vereinbarten Preis. Diese Zusage überlebt
auch dann, wenn das Quell-Payload später korrigiert wird, denn du hast sie einem Gegenüber gegeben,
das sie jetzt erwartet.

Da ist, was sich **physisch bewegt** hat. Acht Stück haben ein Regal verlassen und gingen an den
Frachtführer. Das ist die einzige Behauptung hier, die du nicht durch das Ändern eines Feldes
rückgängig machen kannst, weil sie in der Welt passiert ist. Korrigieren heißt: eine weitere
Bewegung erfassen, nicht die erste überschreiben.

Da ist, was **gebucht** wurde. Eine Erlösposition, eine Forderung, später eine Teilzahlung, die
dagegen zugeordnet wird. Die Buchhaltung braucht, dass das aufgeht — und dass es rückwirkend
aufgeht.

Ein klassisches ERP presst alle vier in einen Status-String und eine Offen-Menge-Spalte. Das
funktioniert, bis zwei der vier sich widersprechen. Dann kann niemand mehr rekonstruieren, welche
sich wann und auf wessen Anweisung verändert hat. Jedes ERP-Team hat für genau diese Rekonstruktion
schon eine Arbeitswoche eines Menschen verbrannt.

## Warum das gerade jetzt dringend wird

Jahrzehntelang war das erträglich, weil der Leser des Statusfeldes ein Mensch war, der den Kunden
kannte, sich an das Telefonat erinnerte und eine unsinnige Zahl als solche erkannte.

Diese Annahme ist gerade zerbrochen. Der Leser ist zunehmend ein Agent. Und ein Agent, der
_teilweise geliefert_ liest, hat kein Gedächtnis, kein Telefonat und kein Gespür für eine Zahl, die
nicht stimmen kann. Er reserviert bereitwillig Bestand gegen eine zurückgezogene Zusage, mahnt eine
Rechnung an, die längst gutgeschrieben wurde, oder nennt dem Kunden einen Liefertermin aus einem
Feld, das drei Subsysteme den ganzen Vormittag überschrieben haben.

Das lässt sich nicht dadurch beheben, dass du den Agenten sorgfältiger anweist. Wer ein mehrdeutiges
Feld sorgfältig liest, liest immer noch ein mehrdeutiges Feld. Die Korrektur muss dort ansetzen, was
das System speichert.

## Wie die Alternative konkret aussieht

Reality hält die vier Behauptungen auseinander und verknüpft sie: **Source → Evidence → Reality**.

Das Quell-Payload wird verlustfrei gespeichert und nie bearbeitet. Was es bedeutet, wird zu Evidenz
interpretiert — ein Beleg und seine Positionen — und diese Interpretation ist wiederholbar und
ersetzbar. Was die Firma schuldet, ist ein Commitment. Was physisch gehalten wird, ist eine
Reservation. Was sich bewegt hat, ist eine Movement. Was die Buchhaltung anerkennt, ist ein
LedgerEntry. Keines davon überschreibt ein anderes, und keines ist ein Status-String.

„Teilweise geliefert“ hört damit auf, ein gespeichertes Feld zu sein. Es wird eine abgeleitete
Antwort, berechnet aus Zusage und Bewegungen, mit allen Eingaben weiterhin zur Hand. Das heißt: sie
lässt sich _erklären_. Du kannst nach dem Warum fragen und bekommst die konkreten Bewegungen und die
konkrete Zusage zurück, aus denen die Zahl entstanden ist — statt einer Vermutung.

Auch die Korrektur ändert sich. Nichts wird an Ort und Stelle überschrieben. Eine falsche Bewegung
wird durch die korrigierende Bewegung berichtigt, sodass die Historie beides enthält: was du
geglaubt hast und ab wann du es nicht mehr geglaubt hast. Genau das macht eine Behauptung sicher
genug, um sie einem Agenten zu geben. Nicht, dass man dem Agenten vertraut — sondern dass jede Zahl,
die er liest, ihre Evidenz mitbringt, und jede Zahl, die er schreibt, vorgeschlagen, freigegeben und
gegen dieselbe Evidenz geprüft wird.

## Wie es weitergeht

Das ganze Argument wird im Praxishandbuch entlang eines repräsentativen Geschäftsmonats bei einem
fiktiven Fahrradhersteller durchgespielt:

- [Grundlagen: von ERP-Belegen zu Business Reality](/de/concepts/business-reality-guide/01-from-erp-documents-to-business-reality)
- [Aufträge, Reservierungen und Bestand](/de/concepts/business-reality-guide/02-orders-stock-and-deliveries)
- [Die Rolle des Process Owners](/de/concepts/business-reality-guide/04-working-as-process-owner)

Als Nächstes in dieser Reihe: was mit alldem passiert, wenn der Kunde den Auftrag nach dem Versand
ändert.

<Subscribe />
