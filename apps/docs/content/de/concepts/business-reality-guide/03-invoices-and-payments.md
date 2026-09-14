# Rechnungen und Zahlungen

[Zurück zur Handbuchübersicht](../business-reality-guide)

## Rechnung, Teilzahlung und Gutschrift {#payments-walkthrough}

Hubers Lieferung aus Auftrag `SO-1001` ist vollständig. Finanziell ist damit noch nichts erledigt.
Die zugehörige Rechnung `INV-1001` nennt **1.470 EUR**. Ihre Position ist mit der abgerechneten
Auftragsposition verknüpft. Diese Beziehung gilt von Anfang an in unserem Beispiel.

Den Betrag übernehmen wir aus der Rechnung. Wir rechnen ihn nicht aus Menge und Stückpreis neu aus.
Für das vereinfachte Buchungsbeispiel bleiben Steueraufteilungen außerhalb der Darstellung; es ist
keine Vorlage zur Erstellung einer Rechnung.

### 1. Rechnung erfassen: die Aussage festhalten

Eine Rechnung kommt aus dem System, das sie stellt, oder wird mit einer unterstützten Aktion in
Reality erfasst. Der Rechnungsbeleg hält die kaufmännische Aussage fest: Huber werden 1.470 EUR
berechnet. Wie beim Auftrag heißen Beleg und Position **Document** und **DocumentLine**.

Die Rechnung zu erfassen ist noch keine Buchung. Dass die Lieferung vollständig ist, erzeugt auch
nicht von selbst diese Rechnung. Lieferung und Rechnung sind verknüpft, aber eigenständige Vorgänge.

### 2. Rechnung buchen: die Forderung führen

Acme bucht `INV-1001`. Dabei entstehen zusammengehörige **Buchungseinträge (LedgerEntry)**:

| Konto        |      Soll |     Haben |
| ------------ | --------: | --------: |
| Forderungen  | 1.470 EUR |         — |
| Umsatzerlöse |         — | 1.470 EUR |

Jetzt besteht ein offener Posten über 1.470 EUR. Die Buchungsgruppe ist ausgeglichen. Diese
finanzielle Aussage ändert weder die gelieferte Menge noch den Lagerbestand.

### 3. Zahlung erfassen: das eingegangene Geld festhalten

Huber zahlt 500 EUR. Die übernommene Zahlungsinformation führt zu einem eigenen Zahlungsbeleg und
einer Buchung Bank im Soll, Forderungen im Haben. Reality hält den tatsächlich genannten Eingang
fest. Eine Zahlung kann bereits erfasst sein, obwohl noch unklar ist, zu welcher Rechnung sie
gehört.

Aus der Zahlung allein folgt deshalb noch nicht, dass `INV-1001` ausgeglichen ist.

### 4. Zahlung zuordnen: diese Rechnung ausgleichen

Die Zahlung wird mit 500 EUR auf `INV-1001` angerechnet. Diese **Ausgleichszuordnung** heißt im
Modell **SettlementAllocation**. Sie verbindet die passenden Buchungseinträge von Zahlung und
Rechnung.

Jetzt ergibt sich: **1.470 EUR Forderung − 500 EUR zugeordnet = 970 EUR offen.** Der ursprüngliche
Rechnungsbetrag bleibt 1.470 EUR. Der offene Betrag ist eine aktuelle Berechnung.

Eine Rechnung kann mehrere Zahlungen aufnehmen, eine Zahlung mehrere Rechnungen ausgleichen. Die
Zuordnung hält fest, welcher Betrag tatsächlich wohin gehört. Gleiche Beträge oder ein gleicher
Kundenname ersetzen diese Beziehung nicht.

### 5. Eine Gutschrift anrechnen

Acme erfasst und bucht eine Gutschrift über 100 EUR und rechnet sie auf `INV-1001` an. Erst mit
diesem Bezug ergibt sich für diese Rechnung: **970 EUR − 100 EUR = 870 EUR offen.** Eine ungenutzte
Gutschrift wäre zunächst Guthaben; sie würde nicht beliebig eine einzelne Rechnung schließen.

Die Gutschrift verändert die Forderung. Sie nimmt keine Lampe ins Lager zurück. Gibt Huber Ware
zurück, wird der tatsächliche Eingang separat als Retoure erfasst.

### Die Antworten auseinanderhalten

| Frage                                            | Antwort am Ende des Beispiels                                                  |
| ------------------------------------------------ | ------------------------------------------------------------------------------ |
| Welchen Betrag nennt die Rechnung?               | 1.470 EUR                                                                      |
| Wie viel Geld ist eingegangen?                   | 500 EUR                                                                        |
| Wie viel Zahlung ist dieser Rechnung zugeordnet? | 500 EUR                                                                        |
| Wie viel Gutschrift ist angerechnet?             | 100 EUR                                                                        |
| Was ist noch offen?                              | 870 EUR                                                                        |
| Ist der Rest überfällig?                         | Das erfordert Fälligkeit und Bewertungsdatum; beides ist hier nicht angegeben. |

## Was automatisch zugeordnet wird und was eine Entscheidung braucht

Eine übernommene Zahlung wird zuerst erfasst. Nennt die Quelle einen eindeutigen Bezug zu genau
einer passenden gebuchten Rechnung desselben Kunden und derselben Währung, kann der vorhandene
Zuordnungsablauf sie darauf anrechnen. Er ordnet höchstens den noch offenen Betrag zu.

Fehlt ein eindeutiger Bezug, zeigt Reality begründete Kandidaten. Eine berechtigte Person prüft die
Zuordnung. Ein Agent kann die Lage lesen und einen genauen Vorschlag vorbereiten. Daraus folgt keine
allgemeine Erlaubnis, Änderungen selbst zu bestätigen; die unterstützten Freigabewege erklärt
[Kapitel 4](./04-working-as-process-owner).

| Situation      | Was sichtbar bleibt                                  | Nächste fachliche Entscheidung                                              |
| -------------- | ---------------------------------------------------- | --------------------------------------------------------------------------- |
| Teilzahlung    | Rest auf der Rechnung                                | Offen lassen oder einen belegten Abzug separat prüfen                       |
| Überzahlung    | Rechnung ausgeglichen, überschüssiges Kundenguthaben | Guthaben anders zuordnen oder eine tatsächlich erfolgte Erstattung erfassen |
| Unklarer Bezug | Zahlung ohne Zuordnung und mögliche Kandidaten       | Bezug prüfen und passende Zuordnung bestätigen                              |

Kein Rest verschwindet still als Toleranz. Ein akzeptierter Abzug braucht seine eigene begründete
Buchung. Automatisches Zuordnen mit eindeutigem Bezug und eine bestätigungspflichtige Agentenaktion
sind unterschiedliche Wege; beide nutzen die Regeln der gemeinsamen Anwendungsdienste.

## Fehler korrigieren und Ergebnisse prüfen

Eine falsche Buchung wird mit einer vollständigen Gegenbuchungsgruppe storniert. Das Original bleibt
sichtbar. Zuordnungen an einer stornierten Ursprungsbuchung werden inaktiv; ein zuvor ausgeglichener
Posten kann dadurch wieder offen werden. Eine Ersatzzahlung braucht ihre eigene Buchung und
Zuordnung.

Von der Rechnung führen Verweise zu Buchungen, Zahlungen und Kürzungen. Von der Zahlung erreichst du
die ursprüngliche Bank- oder Anbieterinformation. Ein Agent darf daraus den offenen Betrag erklären.
Er darf den genannten Rechnungs- oder Zahlungsbetrag nicht durch eine eigene Neuberechnung ersetzen.

### Prüfe dein Verständnis

Die Zahlung über 500 EUR ist gebucht, aber noch keiner Rechnung zugeordnet. Darfst du allein deshalb
für `INV-1001` schon 970 EUR offen anzeigen?

<details>
<summary>Antwort anzeigen</summary>

Nein. Erst die Zuordnung der Zahlung zu dieser Rechnung reduziert ihren offenen Betrag. Erfasstes
Geld und ausgeglichene Rechnung sind verschiedene Aussagen.

</details>

<details>
<summary>Vertiefung: Referenzarten, automatische Zuordnung und Partnersalden</summary>

### Die drei Stufen des Zahlungseingangs

Jede Kundenzahlung, die Reality erreicht, aus Kontoauszug, Zahlungsanbieter oder Demodaten,
durchläuft dieselben drei Stufen. Jede Stufe hat eine Voraussetzung, eine feste Handlung und Dinge,
die sie nie tut.

| Stufe             | Voraussetzung                                                                                               | Reality tut                                                                                          | Nie                                                                        | Du siehst                                                            |
| ----------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **1 Erfassen**    | Eine Zahlung ist angekommen. Sonst nichts                                                                   | Ein Zahlungsbeleg und eine ausgeglichene Buchung Bank an Forderung, verknüpft mit dem Quelldatensatz | Interpretieren, zuordnen, Geld ablehnen                                    | Eine neue Zeile in Zahlungen, _nicht zugeordnet_                     |
| **2 Zuordnen**    | Die Quelle nennt einen Bezug, der genau eine gebuchte Rechnung desselben Kunden in derselben Währung trifft | Ordnet den kleineren Wert aus Betrag und offenem Betrag dieser Rechnung zu                           | Raten, überzuordnen, ausbuchen, Skonto akzeptieren, eine Rechnung erfinden | Rechnung _bezahlt_ oder _teilbezahlt_; Überschuss als Kundenguthaben |
| **3 Vorschlagen** | Geld ist nicht zugeordnet und kein eindeutiger Bezug existiert                                              | Berechnet Kandidaten beim Lesen, jeden mit Begründung; ein Mensch oder Agent bestätigt einen         | Kandidaten speichern, sie als Wahrheit ordnen, ohne Bestätigung zuordnen   | Die Zahlung mit Kandidatenliste in Zahlungen und über MCP            |

**Was ein genannter Bezug sein muss.** Stufe 2 weiß, wofür jede Nummer steht, und folgt ihr zur
Rechnung; menschliche Nummern werden zum Nachschlagen benutzt, nie als Verknüpfung gespeichert.

| Die Zahlung nennt                                | Reality löst auf                                     | Stufe 2 ordnet zu                                    |
| ------------------------------------------------ | ---------------------------------------------------- | ---------------------------------------------------- |
| deine Rechnungsnummer                            | die gebuchte Rechnung                                | ja, wenn genau eine                                  |
| die Shop-ID des Auftrags (Karte, PayPal, Wallet) | den Auftrag, dann die Rechnung, die ihn abrechnet    | ja, wenn genau eine Rechnung ihn abrechnet           |
| die Shop-Bestellnummer (`#1001`)                 | den Auftrag, dann seine Rechnung                     | ja, wenn genau eine                                  |
| die Bestellnummer des Kunden                     | den Auftrag mit dieser Referenz, dann seine Rechnung | ja, wenn genau eine                                  |
| nur deine Kundennummer                           | den Kunden                                           | nein; grenzt die Kandidaten der Stufe 3 ein          |
| eine Transaktions-ID des Anbieters               | die Zahlung selbst                                   | nein; sie identifiziert das Geld, nicht die Rechnung |
| nichts Brauchbares                               | nichts                                               | nein; Stufe 3                                        |

Zwei Rechnungen zu einem Auftrag oder eine Rechnung zu mehreren Aufträgen sind keine Fehler; sie
erzeugen Kandidaten statt einer Zuordnung.

**Ergebnisse der Stufe 2.** Keine Toleranz schließt einen Rest still; jede Minderung einer Forderung
ist eine eigene, bestätigte Buchung mit Grund, nie Teil der Zuordnung.

| Gezahlt gegen offen | Zuordnung           | Ergebnis                                                                                                       | Zu entscheiden bleibt                                                    |
| ------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| gleich              | voll                | Rechnung _bezahlt_                                                                                             | nichts                                                                   |
| weniger             | der gezahlte Betrag | Rechnung _teilbezahlt_; `overdue_receivable` nach Fälligkeit, markiert, wenn die Bedingungen den Rest erklären | offen lassen, einen genannten Abzug akzeptieren oder ihn erklären        |
| mehr                | der offene Betrag   | Rechnung _bezahlt_; der Überschuss ist Kundenguthaben, gemeldet als `unmatched_financial_event`                | das Guthaben einer anderen Rechnung zuordnen oder eine Erstattung buchen |

Der [Grundablauf am Anfang dieses Kapitels](#payments-walkthrough) zeigt die Schritte an Hubers
Rechnung; das [Playbook Forderungen](../../agent-playbooks/receivables-and-payments) zeigt die
Schreibtischarbeit hinter jedem Ergebnis.

### Salden je Kunde und Lieferant

Die Saldenliste beantwortet, wo ein Geschäftspartner steht. Sie wird zur Lesezeit abgeleitet, eine
Zeile je Partner und Währung: offener Betrag (die Summe seiner offenen Posten), davon überfällig
(die offenen Posten, deren Fälligkeit aus dem Fälligkeitsregister vor dem Lesezeitpunkt liegt),
verfügbares Guthaben (die Summe seiner ungenutzten Zahlungen und Gutschriften) und der Saldo, offen
minus Guthaben. Nichts wird gespeichert, nichts zwischen Währungen umgerechnet und nichts in den
Büchern verrechnet: Guthaben gegen eine Rechnung zu nutzen bleibt ein bestätigter Ausgleich. Jede
Zeile öffnet die offenen Posten und Guthaben des Partners, genau die Belege, die summiert wurden. In
der App ist die Liste Finanzen → Salden; für Agenten der Lesezugriff `finance_party_balances`. Ein
Saldo beweist eine Position zu einem Zeitpunkt, nicht, dass ein Kunde zahlen wird.

</details>

Für die tägliche Bearbeitung:
[Playbook Forderungen und Zahlungen](../../agent-playbooks/receivables-and-payments). Weiter im
Lernweg: [Als Prozessverantwortliche/r arbeiten](./04-working-as-process-owner).
