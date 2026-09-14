# Von ERP-Belegen zur Business Reality

[Zurück zur Handbuchübersicht](../business-reality-guide)

## Grundlagen {#foundations}

### Das bekannte ERP-Bild

In deinem ERP findest du einen Kundenauftrag über Kopf, Positionen und verknüpfte Belege. Dort
siehst du, was bestellt, reserviert, geliefert und berechnet wurde. Lagerjournal, offene Posten und
Belegfluss helfen dir, diese Angaben zu erklären. Das bleibt vertrautes Fachwissen.

Reality trennt die Verantwortung für diese Aussagen ausdrücklich: Der Auftragsbeleg hält die
erfasste Bestellung fest. Eigene operative Einträge halten fest, was zugesagt, zugeordnet, bewegt
oder gebucht wurde. Der aktuelle Stand wird aus diesen Einträgen abgeleitet. Entscheidend ist diese
Aufteilung, nicht die Zahl der Tabellen.

### Ein Auftrag, mehrere Fragen

Huber bestellt 30 Fahrradlampen bei Acme. Der Auftrag ist erfasst und Acme hat eine Lieferzusage
über 30 Stück angelegt. Acht Lampen liegen im Lager. Noch ist nichts reserviert oder versendet.

Auf die Frage „Ist der Auftrag offen?“ brauchst du jetzt eine genauere Antwort:

| Geschäftsfrage                        | Antwort im Beispiel | Grundlage                                      |
| ------------------------------------- | ------------------- | ---------------------------------------------- |
| Was hat Huber bestellt?               | 30 Lampen           | Erfasster Auftrag mit Position                 |
| Was soll Acme noch liefern?           | 30 Lampen           | Lieferzusage, bisher ohne erfüllende Lieferung |
| Welche Ware ist für Huber vorgesehen? | Noch keine          | Noch keine aktive Reservierung                 |
| Was wurde bereits versendet?          | Nichts              | Noch keine erfasste Lieferung                  |

Die **Lieferzusage** heißt im Modell **Commitment**. Sie beschreibt, wer wem welche Menge liefern
soll. Die **Reservierung** heißt **Reservation**: Sie ordnet vorhandene Ware einer solchen Zusage
zu. Ein **Movement** erfasst eine physische Warenbewegung, beispielsweise einen Warenausgang.

Wenn Acme später 18 Lampen liefert und den Versand gegen diese Zusage erfasst, bleiben zwölf offen.
Das ergibt sich aus 30 zugesagten und 18 gelieferten Stück. Der Auftrag braucht dafür kein eigenes
Lieferstatusfeld. Eine Anzeige darf trotzdem „teilgeliefert“ heißen; ihre Grundlage sind Zusage und
Lieferung. So kannst du auch erklären, woher sie kommt.

### Warum der Auftrag trotzdem erhalten bleibt

Der Beleg beantwortet eine andere Frage: „Welche kaufmännische Aussage haben wir erfasst?“ In
Reality heißt der Beleg **Document**, seine Position **DocumentLine**. Beleg und Lieferzusage sind
verknüpft. Du kannst von der offenen Lieferung zur Position zurückgehen und prüfen, worauf die
Zusage beruht.

Diese Trennung hilft bei Änderungen. Meldet Huber später eine andere Menge, verschwindet dadurch
kein bereits erfasster Versand. Die neue Bestellung und die bereits erfolgte Abwicklung müssen
fachlich miteinander abgestimmt werden. Die Wege dafür folgen in Kapitel 2.

### Woher weiß Reality, was bestellt wurde?

Eine Bestellung kann über eine unterstützte Anbindung eintreffen oder mit einer vorgesehenen
manuellen Auftragsaktion erfasst werden. Reality bewahrt die ursprüngliche Eingabe unverändert auf.
Diesen Herkunftsnachweis nennen wir **SourceRecord**. Er ermöglicht die spätere Frage: „Stand das
wirklich so in der Eingabe?“ Eine Quelle kann sich irren; Aufbewahren macht ihre Aussage
überprüfbar, nicht automatisch richtig.

Der unterstützte Import oder die manuelle Auftragsaktion legt daraus die passenden Belege und
Lieferzusagen an. Das geschieht über definierte Regeln. Nicht jede beliebige Datei und nicht jeder
Beleg erzeugt automatisch eine Zusage.

Damit hat die Folge **Source → Evidence → Reality** eine praktische Bedeutung:

| Ebene                                    | In unserem Auftrag                            | Wozu sie dient                                     |
| ---------------------------------------- | --------------------------------------------- | -------------------------------------------------- |
| Source: ursprüngliche Eingabe            | Übermittelte oder manuell erfasste Bestellung | Nachsehen, was ursprünglich angegeben wurde        |
| Evidence: erfasste kaufmännische Aussage | Auftrag und Position                          | Festhalten, welche Bestellung wir übernommen haben |
| Reality: operative Einträge              | Zusage, später Reservierung und Lieferung     | Die Abwicklung führen und erklären                 |
| Abgeleitete Antwort                      | Nach 18 gelieferten Stück sind zwölf offen    | Eine aktuelle Geschäftsfrage beantworten           |

Das ist ein Weg zur Nachvollziehbarkeit. Nicht jeder Geschäftsfall braucht jede Stufe: Ein
unerwarteter Wareneingang kann erfasst werden, auch wenn noch keine Lieferantenzusage existiert.
Fehlende Belege werden dadurch nicht erfunden.

## Was du aus dem ERP weiterverwenden kannst {#data-model}

Kunden, Lieferanten, Artikel, Lagerorte und Buchungen bleiben vertraute fachliche Begriffe. Ein
Geschäftspartner kann mehrere Rollen haben, etwa Kunde und Lieferant. Die Verantwortung für eine
operative Aussage wandert aber nicht deshalb zum Partner oder Beleg, weil du sie dort anzeigst.

| Vertraute Frage                            | Maßgebliche Grundlage in Reality                  |
| ------------------------------------------ | ------------------------------------------------- |
| Was liegt im Lager?                        | Erfasste Zu- und Abgänge: Movement                |
| Was davon ist noch frei?                   | Bestand abzüglich aktiver Reservation             |
| Welche Menge schulden wir dem Kunden?      | Commitment abzüglich erfüllender Movement         |
| Was schuldet der Kunde auf einer Rechnung? | Buchungen und angerechnete Ausgleiche             |
| Was hat die Quelle zusätzlich gesagt?      | Originaleingabe, gegebenenfalls ein belegter Fact |

Finanzielle Buchungen heißen **LedgerEntry**. Ihre Zuordnung zu einer Rechnung lernst du in
Kapitel 3. Ein **Fact** hält bestimmte belegte Zusatzinformationen fest; dafür ist Kapitel 6
vorgesehen. Du musst beide Begriffe hier noch nicht im Detail kennen.

Arbeitslisten bereiten die Antworten für Menschen und Agenten auf. Eine solche Sicht heißt **View**;
eine wiederaufbaubare vorbereitete Lesesicht heißt **Projection**. Die Liste hilft dir beim
Arbeiten, die zugrunde liegenden Einträge erklären ihre Zahlen. Eine veraltete Liste berechtigt
keine Aktion, mehr Ware zu reservieren oder zu versenden, als die aktuellen operativen Datensätze
erlauben.

## Drei Regeln zum Mitnehmen {#reality-model}

1. **Beleg und Abwicklung getrennt lesen.** Die Bestellung belegt noch keinen Versand. Eine
   Reservierung belegt noch keinen Warenausgang.
2. **Übernommene Werte von berechneten Antworten unterscheiden.** Ein genannter Rechnungsbetrag wird
   unverändert übernommen. Offene Menge, Bestand und offener Betrag werden aus ihren jeweiligen
   Grundlagen abgeleitet.
3. **Die Grundlage jeder Antwort prüfen können.** Von einer Zahl führt ein Weg zu den operativen
   Einträgen und, soweit vorhanden, über die Belege zur ursprünglichen Eingabe.

<details>
<summary>Technische Vertiefung: Identität, Herkunft und Tabellen</summary>

Auftragsnummern wie `SO-1001` helfen Menschen beim Suchen. Beziehungen verwenden interne, opake IDs,
damit gleiche Nummern aus verschiedenen Systemen nicht verwechselt werden. Alle Geschäftsdatensätze
und Abfragen gehören zu einem Mandanten. Fremde Datensätze verhalten sich wie nicht vorhanden.

Eine Reservation verweist direkt auf ihr Commitment. Dessen Beleg- und Quellenverknüpfungen machen
zusätzliche Herkunftsverweise an der Reservation unnötig. SourceRecord bleiben unveränderlich; neue
externe Inhalte werden als neue Version bewahrt. Operative Lebenszykluszustände können sich ändern.
Das Modell verspricht deshalb keine vollständige Rekonstruktion jedes früheren Zustands.

Die [Tabellenübersicht mit Detailerklärungen](../../reference/table-map) beschreibt Stammdaten,
Quellverarbeitung, Belege, Zusagen, Bewegungen, Buchungen und Lesesichten. Für den Lernweg genügt
zunächst ihre fachliche Verantwortung.

</details>

### Prüfe dein Verständnis

Hubers 30 Lampen sind bestellt. Acht sind reserviert, noch keine versendet. Wie viel ist noch zu
liefern, und wie viel dieser Menge ist schon zugeordnet?

<details>
<summary>Antwort anzeigen</summary>

Noch 30 sind zu liefern; acht davon sind zugeordnet. Die Reservierung erfüllt keine Lieferzusage.
Dafür braucht es die erfasste tatsächliche Lieferung gegen das Commitment.

</details>

Weiter: [Hubers Auftrag durch Lager und Einkauf verfolgen](./02-orders-stock-and-deliveries).
