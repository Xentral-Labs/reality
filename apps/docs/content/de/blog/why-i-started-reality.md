---
title: Warum ich Reality gestartet habe
description:
  Siebenhundert Tabellen, und ich konnte nie sagen, wo eine Zahl herkommt. Warum ich das für mich
  selbst baue, warum es offen ist, und warum du dir drei Wochen geben solltest.
date: 2026-09-04
author: Benedikt Sauter
order: 1
tags:
  - Founder note
sidebar: false
---

# Warum ich Reality gestartet habe

<PostMeta />

Ich habe jahrelang ERP auf relationalen Datenbanken gebaut. Als ich aufgehört habe zu zählen, hatte
das Schema siebenhundert Tabellen — und jede einzelne davon hat jemand angelegt, um ein echtes
Problem unter echtem Termindruck zu lösen. So wachsen Schemas.

Was ich trotzdem nie konnte: sagen, wo eine Zahl herkommt. Nicht, weil Protokolle gefehlt hätten.
Änderungsprotokolle hatten wir, und die sagen dir sauber, dass ein Feld sich geändert hat: wer,
wann, von was auf was. Was sie dir nie sagen, ist, was die Änderung bedeutet hat. Eine Menge geht um
14:03 von zwölf auf acht. Storno? Teillieferung? Tippfehler? Rundung? Um das zu beantworten, musste
ich drei Protokolle nebeneinanderlegen und rückwärts denken — und zwei sorgfältige Leute kamen dabei
zu verschiedenen Ergebnissen. Protokolliert war immer das Feld. Nie die Zusage.

Dann habe ich mir angesehen, was es braucht, damit ein Agent ein Unternehmen betreibt. Und in meinem
Kopf hat sich etwas neu sortiert.

Solange ich das mache, war ERP ein Cockpit für Menschen. Wer auf eine Anzeige geschaut hat, hat
alles mitgeliefert, was die Anzeige offengelassen hat: den Kunden, das Telefonat von letzter Woche,
das Gefühl dafür, dass eine Zahl nicht stimmen kann.

Ein Agent liefert nichts mit.

Wenn du für einen Leser baust, der kein Gedächtnis und kein Gefühl hat, ändert sich, was das System
überhaupt speichern muss. Und das ist der Teil, den ich selbst kaum glauben kann: Hör auf,
Ergebnisse zu speichern, speichere die Behauptungen — und die ganze Geschäftswahrheit passt in rund
ein Dutzend Tabellen. [Das ist ein eigener Beitrag.](/de/blog/eleven-tables) Aber es ist der Grund,
warum ich das nicht mehr losgelassen habe.

Reality habe ich für mich selbst angefangen. Ich kann über sowas nicht klar denken, ohne es zu
bauen. Ich wollte wissen, ob eine Firma wirklich auf belegten Behauptungen läuft statt auf
gespeicherten Statusfeldern. Und der einzige Weg, das rauszufinden, den ich kenne, ist: hinschreiben
und schauen, was bricht.

Es ist offen, weil das die Form ist, in der es etwas taugt. Kein Produkt zum Kaufen, sondern ein
Kern zum Lesen, Laufenlassen, Erweitern und Widersprechen. Nimm es auseinander. Und sag mir, wo ich
falsch liege — das wäre das Nützlichste, was du damit machen kannst.

## Eine Warnung, und die meine ich ernst

Nimm dir Zeit.

Als ich Objektorientierung zum ersten Mal verstanden habe, hat es nicht an einem Nachmittag klick
gemacht. Ich hatte darüber gelesen, ich war sicher, ich hätte es — und habe danach wochenlang
prozeduralen Code geschrieben, nur mit Klassen drumherum, ohne es zu merken. Ein abstraktes Modell
zu kennen ist nicht dasselbe, wie darin zu denken.

Hier ist es genauso. Du liest das, es klingt vernünftig, und dann setzt du dich hin und modellierst
irgendwas — und erwischst dich dabei, wie du nach einem Statusfeld greifst. Der Reflex ist dreißig
Jahre alt.

Plan also zwei bis drei Wochen ein. Kein Studium, sondern Wiederkommen. Ein Kapitel lesen, weglegen,
etwas modellieren, das du wirklich kennst, die Stelle finden, an der dein Instinkt gegen das Modell
kämpft, das Kapitel nochmal lesen. Es sitzt nicht, wenn du fertig gelesen hast. Es sitzt, wenn du
aufhörst, nach dem Statusfeld zu suchen.

## Wo du anfängst

- [Grundlagen: von ERP-Belegen zu Business Reality](/de/concepts/business-reality-guide/01-from-erp-documents-to-business-reality)
- [Die Rolle des Process Owners](/de/concepts/business-reality-guide/04-working-as-process-owner)

Als Nächstes in dieser Reihe: [die elf Tabellen](/de/blog/eleven-tables) — und was in ihnen bewusst
fehlt.

<Subscribe />
