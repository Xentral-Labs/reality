---
aside: false
---

# Tools nutzen

Alles, was Reality kann, geordnet, wie ein ERP-Berater denkt: nach Fachobjekt und nach Prozess.
Wähle ein Objekt wie **Auftrag**, **Rechnung** oder **Geschäftspartner**, und du siehst die Listen,
die es zeigen, die Aktionen, die es verändern, die Klärfälle, die es auslösen kann, und was ein
Mensch für jede Aktion angeben muss. Wähle einen Prozess wie **Order-to-Cash**, und du gehst ihn
Schritt für Schritt durch. Die technische Sicht darunter ist derselbe Inhalt nach Systemteilen
sortiert, für Entwickler und Process Owners.

Alles hier wird aus den ausführbaren Katalogen des laufenden Codes erzeugt. Was auf diesen Seiten
fehlt, kann Reality noch nicht.

Im Tab **Datenmodell** findest du die zentralen Datensatzarten mit Beispielen, allen gespeicherten
Feldern, Standardwerten und passenden Aktionen. Beginne zum Beispiel beim
[Commitment](#model:commitment).

<ToolUsage />

## So liest du es

- **Beim Objekt oder Prozess anfangen, nicht beim Tool.** Eine Aktion wie _Zahlungseingang buchen_
  ist die fachliche Operation. CLI, Web, API, Chat und MCP sind nur Türen dorthin; die Parameter
  sind hinter jeder Tür dieselben.
- **Pflichtparameter sind das Minimum, das eine Quelle nennen muss.** Opake IDs wie `commitment_id`
  stammen aus einer vorherigen Liste oder Abfrage, nie aus einer menschlichen Nummer.
- **Agenten-Tools mit der Endung `_propose` ändern von sich aus nie etwas.** Sie bereiten einen
  Vorschlag vor, den ein Mensch freigibt. Lese-Tools antworten sofort. Das Freigabemodell steht in
  den [Agentenfunktionen](/de/tool-usage/#choosing-a-tool).
- **Jede Aktion nennt, was danach zu prüfen ist.** Diese Liste oder Projection ist der Beweis, dass
  die Operation getan hat, was sie behauptet.
- **Die [Agenten-Playbooks](../agent-playbooks/)** erzählen dieselben Prozesse als Geschichten mit
  Sachbearbeiter und Agent. Die Prozesssicht hier ist der Index dazu.

## Wie ein Agent das richtige Tool wählt {#choosing-a-tool}

Jede Fähigkeit hat eine Beschreibung, die sagt, wann man sie nutzt, was ihr Ergebnis beweist und was
nicht, und welche Abfrage die Wirkung prüft. Agenten schreiben nie direkt in Tabellen und halten
keine eigene Kopie der Geschäftsregeln; Chat und MCP lesen dieselben Beschreibungen und rufen
dieselben Anwendungs-Tools auf wie die Web-App.

### Die geregelte Arbeitsschleife

```text
Datensätze und undurchsichtige IDs finden
        ↓
die infrage kommende Funktion beschreiben lassen
        ↓
auswählen und begründen – oder sicher ablehnen
        ↓
das typisierte Kommando vorschlagen
        ↓
Bestätigung durch einen Menschen oder eine beschlossene Policy
        ↓
der gemeinsame Reality-Dienst führt aus
        ↓
die deklarierte fachliche Projection erneut lesen
        ↓
verifiziert / abgelehnt / unbekannt / Abstimmung nötig
```

Mit `business_records_discover` findet ein Agent mandantenbezogene Datensätze und ihre opaken IDs,
dann ruft er `capability_describe` mit dem öffentlichen Tool-Namen auf, etwa
`{"tool_name": "reservation_propose"}`. Die Abfrage ist rein lesend. Für Vorschlags-Tools liefert
sie Voraussetzungen, Bestätigungs- und Wiederholungsregeln, Ablehnungen, Events und
Prüf-Projections; für Lese-Tools Datenbasis, Aktualität, Grenzen, die Bedeutung eines leeren
Ergebnisses und was die Abfrage beweist oder ausdrücklich nicht beweist.

### Auch Lesen ist eine Fähigkeit

| Lesefunktion                  | Wofür sie da ist                                                                            | Was sie nicht belegt                                                            |
| ----------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `business_records_discover`   | Mandantenbezogene Datensätze, aktuelle Werte und undurchsichtige IDs finden                 | Dass ein gefundener Datensatz ein Ergebnis von Anfang bis Ende belegt           |
| `interpretation_coverage`     | Sehen, wie ein SourceRecord interpretiert wurde und welche Reality-Identitäten entstanden   | Dass die Interpretation vollständig oder richtig ist, nur weil sie gelaufen ist |
| `order_explain`               | Einen Auftrag über Source, Evidence, Commitments, Reservations und Movements nachvollziehen | Externe Lieferung oder Zahlung ohne entsprechende Reality-Datensätze            |
| `commitments_list`            | Zusagen und ihren abgeleiteten Fulfilment-Zustand lesen                                     | Physischen Bestand, Zuordnung, Lieferung oder Zahlung                           |
| `inventory_read`              | Physische, reservierte und verfügbare Mengen lesen                                          | Dass Ware zugesagt, extern versendet oder bezahlt wurde                         |
| `exceptions_list`             | Registrierte operative Aufmerksamkeitsbedingungen lesen                                     | Dass eine leere Liste das ganze Geschäft als korrekt belegt                     |
| `fulfillment_queue`           | Abgeleitete Auftragsbereitschaft und Arbeitszustand priorisieren                            | Dass ein bereiter Auftrag physisch versendet wurde                              |
| `fulfillment_blockers`        | Registrierte Ursachen prüfen, die Aufträge oder Artikel blockieren                          | Dass jeder mögliche Blocker modelliert ist                                      |
| `item_supply_demand`          | Zugänge, Bedarf und Fehlmengen je Artikel vergleichen                                       | Dass erwartete Zugänge physisch eintreffen                                      |
| `exception_explain`           | Eine ausgewählte aktuelle Ausnahme über ihren Reality-Kontext erklären                      | Externe Grundursache oder erfolgreiche Behebung                                 |
| `proposals_awaiting_approval` | Geregelte Absichten prüfen, die auf menschliche Freigabe warten                             | Berechtigung, Ausführung oder daraus entstandene Reality                        |
| `proposal_execution_status`   | Eine Bestätigung abgleichen und ihren Beleg mit der aktuellen Reality prüfen                | Fulfilment, Lieferung oder das endgültige Kundenergebnis                        |
| `finance_balances`            | Aus LedgerEntries abgeleitete Forderungen und Verbindlichkeiten lesen                       | Bankausgleich, Abstimmung oder buchhalterische Vollständigkeit                  |

Eine Abfrage wird mit ihrem öffentlichen MCP-Namen beschrieben, auch wenn das interne
Anwendungs-Tool anders heißt; das zurückgegebene `application_tool` ist Routing, keine zweite
Identität. Bevor ein Ergebnis zur Behauptung wird, gehören `data_basis`, `freshness`, `limitations`,
`empty_result`, `unknown_when` und `verification` geprüft.

### Fact oder typisierte Reality?

Nimm den kürzesten Datensatz, der ehrlich wiedergibt, was passiert ist:

| Geschäftliche Bedeutung                                                               | Funktion                  |
| ------------------------------------------------------------------------------------- | ------------------------- |
| Eine Quelle sagt ausdrücklich eine freigegebene Kontextbeobachtung aus                | `fact_observe_propose`    |
| Ein neuer Auftrag begründet Zusagen gegenüber Kunden oder Lieferanten                 | `order_create_propose`    |
| Verfügbarer Bestand wird einer bestehenden Zusage zugeordnet                          | `reservation_propose`     |
| Ware ist physisch eingetroffen, umgelagert, versendet, zurückgekommen oder korrigiert | `movement_create_propose` |

Ein Fact spiegelt keine typisierte Reality, und eine Modellvorhersage ist kein Fact. Eine
Reservation beweist nicht, dass Ware bewegt wurde, ein Movement ersetzt nicht das Commitment, das
erklärt, warum geliefert werden sollte, und unbekannte Felder bleiben im SourceRecord, bis ein
geprüftes Fact-Prädikat oder ein typisierter Anwendungsfall existiert.

### Bestätigung und unbekannte Ergebnisse

Vorschlags-Tools legen einen `ChangeProposal` an und ändern nichts. Die Ausführung braucht die
Bestätigungs- oder Richtliniengrenze: Ein Mensch gibt frei, und der bestätigende Client ruft
`proposal_approve_and_execute` mit `approved=true` auf. Reality beansprucht einen Vorschlag atomar,
genau ein Aufrufer bringt ihn von `proposed` nach `executing`; ein späterer Aufruf gegen `executed`
liefert die gespeicherte Quittung, ein Aufruf gegen `executing` wird abgelehnt, weil das Ergebnis
unbekannt sein kann.

Zur Prüfung liest man die Projection neu, die die Beschreibung nennt. Nach einer Reservierung sollte
`inventory_read` mehr reservierte und weniger verfügbare Menge zeigen; das beweist die Zuordnung,
nie eine Warenbewegung. Nach einem Timeout oder einer verlorenen Antwort ruft man
`proposal_execution_status` mit der Vorschlags-ID: Es prüft die Quittung gegen Proposal,
Reservation, Commitment und Event des Mandanten und nennt `business_outcome=not_proven`
ausdrücklich. Bleibt der Status `executing` oder widerspricht eine ID, Menge oder ein Event, bleibt
das Ergebnis unbekannt. Eine erfolgreiche Antwort ist kein ausreichender Beweis; eskaliere und prüfe
die genannten Datensätze, statt aus einer verschwundenen Ausnahme auf Erfolg zu schließen.

### Ablehnungen tragen einen Code

Lehnt ein Tool ab, ist das Ergebnis ein MCP-Fehlerergebnis, dessen Text ein JSON-Objekt ist:
`{"code": "...", "message": "...", "tool": "..."}`. Der Code ist stabil und sagt, warum Reality
abgelehnt hat: `not_found` (der in den Argumenten genannte Datensatz existiert in diesem Mandanten
nicht), `invalid_operation` (die Anfrage ist für diesen Datensatz oder diese Argumente nicht
gültig), `conflict` (die Anfrage war in der Form gültig, beruhte aber auf veraltetem Zustand),
`needs_review` (ein Interpreter hat abgelehnt, weil die fachliche Bedeutung mehrdeutig ist),
`reality_error` (jede andere fachlich lesbare Ablehnung). Die Nachricht ist der Satz, den ein Mensch
liest; sie ist für Menschen und darf nicht geparst werden. Ein Agent, der entscheiden muss, ob er
wiederholt, nachfragt oder aufhört, liest den Code und zeigt die Nachricht. Fehler, die keine
Ablehnungen sind, etwa ein fehlender Scope oder ein unbekanntes Tool, behalten ihren Klartext ohne
Code; sie sind keine fachlichen Ergebnisse.

### Leitfaden für eine weitere Fähigkeit ergänzen

1. Nenne das exakte öffentliche MCP-Tool; teile keine Beschreibung zwischen Tools mit
   unterschiedlicher Absicht, etwa Reservierung anlegen und aufheben.
2. Für einen Vorschlag: Zweck, Verwenden- und Nicht-verwenden-Bedingungen, Voraussetzungen,
   Bestätigung, Idempotenz, Ablehnungen, Events, Prüfabfragen und Beispiele. Für eine Abfrage:
   Zweck, Datenbasis, Grenzen, Aktualität, Bedeutung eines leeren Ergebnisses, unbekannte
   Bedingungen und nächste Schritte.
3. Verweise nur auf registrierte Business Events, bekannte Reality-Datensätze und rein lesende
   Projections, und nutze opake IDs, nie Belegnummern.
4. Ergänze Auswahl- und Drift-Tests, bevor die Fähigkeit beworben wird. Die Validierung bleibt im
   Anwendungsservice; der Leitfaden erklärt die Grenze, er autorisiert nichts, und kein Gespräch
   aktiviert von selbst neue Leitfäden oder Fact-Prädikate.

## So liest du die Listen {#how-to-read-the-lists}

Bestand, offene Arbeit und Erklärungen werden beim Lesen aus den Datensätzen berechnet. Das
behauptet eine Liste, und das nicht.

### Bestandsformeln

```text
physisch  = Mengen in einen Lagerort - Mengen aus ihm heraus
reserviert = Mengen aktiver Reservations
verfügbar  = physisch - reserviert
eingehend  = offene Mengen aus Lieferanten-Commitments
erwartet   = verfügbar + eingehend
```

Physisch ist, was jetzt am Lagerort erfasst ist, reserviert, was ausgehenden Zusagen zugeordnet ist,
verfügbar, was ohne Doppelzusage noch zugeordnet werden kann, im Zulauf, was Lieferanten noch
versprechen, projiziert, was verfügbar sein könnte, sobald sie liefern.

### Was ist offen?

| Dimension              | Offen, wenn                                              | Geschlossen, wenn                                         |
| ---------------------- | -------------------------------------------------------- | --------------------------------------------------------- |
| Kunden-Commitment      | die Zusage die qualifizierenden Lieferungen übersteigt   | Lieferungen sie erfüllen oder es storniert wird           |
| Lieferanten-Commitment | die Zusage die qualifizierenden Wareneingänge übersteigt | Wareneingänge sie erfüllen oder es storniert wird         |
| Reservation            | der Status `active` ist                                  | eine Lieferung sie verbraucht oder eine Freigabe sie löst |
| Kundenrechnung         | eine aktive Forderung bleibt                             | der abgeleitete Betrag null erreicht                      |
| Lieferantenrechnung    | eine aktive Verbindlichkeit bleibt                       | der abgeleitete Betrag null erreicht                      |

Es gibt keine allgemeine Regel „Beleg offen“. Eine Rechnung kann nach vollständiger Lieferung
finanziell offen bleiben, ein Kundenauftrag kann keine offene Liefermenge haben, während seine
Rechnung unbezahlt ist, und eine stornierte Zusage kann noch eine ungeklärte Gutschrift oder Retoure
tragen.

### Risiko, Projections und Erklärungen

Risiko wird berechnet, nicht auf einen Beleg kopiert: Es vergleicht die offene Menge eines
ausgehenden Commitments mit Bestand und Zulauf, mit Priorität, Fälligkeit und Sperren als Kontext,
sodass eine Erklärung „30 versprochen, 18 erfüllt, 12 offen, sieben reserviert, fünf fehlen“ sagen
kann statt eines unerklärten roten Status. Projections werden aus Datensätzen und BusinessEvents neu
aufgebaut; ein Prüfpunkt hinter dem letzten Event markiert eine veraltete Sicht, und Kommandos
vertrauen ihr nie, um Überlieferung oder Überzuordnung zu erlauben.

`explain commitment` liefert Zusage, Parteien, Artikel, Lagerort, Fälligkeit, Zustand, Reservations,
Movements, erfüllte und offene Menge, Risiko und die Kette DocumentLine → Document → SourceRecord
mit Roh-Payload, wenn vorhanden. Fehlende Nachweise werden ehrlich gemeldet. Die Timeline
verschränkt die Datensatzarten:

```text
09-02  SOURCE       Shopify-Auftrag 4711 v1 eingegangen
09-02  COMMITMENT   12 BIKE-LIGHT liefern
09-02  RESERVATION  12 BIKE-LIGHT zuordnen
09-03  MOVEMENT     Lieferung 5 BIKE-LIGHT
09-04  MOVEMENT     Lieferung 7 BIKE-LIGHT
09-22  LEDGER       Forderung Soll 1.470 EUR
09-25  LEDGER       Forderung Haben 500 EUR
```

### Interpretationsabdeckung {#interpretation-coverage}

Eine gespeicherte Quelle ist nicht automatisch verstanden. Jeder Versuch, einen SourceRecord zu
interpretieren, hinterlässt ein Ergebnis und die erzeugten Identitäten:

| Einordnung     | Bedeutung                                                                              |
| -------------- | -------------------------------------------------------------------------------------- |
| `interpreted`  | Die Verarbeitung war erfolgreich und benennt die erzeugten Reality-Datensätze.         |
| `needs_review` | Die fachliche Bedeutung blieb unklar; es wurde keine Reality erfunden.                 |
| `unsupported`  | Für diesen Quelltyp gibt es keinen Interpreter.                                        |
| `stale`        | Eine neuere Version aus dem Vorsystem ist bereits aktuell.                             |
| `conflict`     | Eine Version aus dem Vorsystem benennt unterschiedliche Payloads.                      |
| `failed`       | Die Verarbeitung scheiterte; begonnene fachliche Schreibzugriffe wurden zurückgerollt. |

`pending` und `processing` sind laufende Job-Zustände. Ist eine SKU unbekannt, überlebt kein halber
Auftrag: Versuch 1 ist `failed`, und nach korrigierten Stammdaten kann Versuch 2 `interpreted` sein,
beide Versuche bleiben sichtbar. Agenten lesen das über `interpretation_coverage`; das Ergebnis
lässt Payloads, Zugangsdaten und Stacktraces weg.

## Handbuchseiten

Derselbe Inhalt als einfache Seiten für Suchmaschinen, Druck und Permalinks. Die Suche funktioniert
wie `apropos` auf einer Linux-Konsole:

- [Ressourcen](./resources) — jedes Fachobjekt mit seinen Listen, Aktionen und Klärfällen.
- [Geschäftsprozesse](./processes) — die Schrittfolgen mit Aktionen, Prüfungen und Klärfällen.
- [Geschäftsaktionen](./commands) — jede Operation, ihre Agenten-Tools und deren Parameter.
- [Sichten, Projections und Aktionen](./views) — was jeder Arbeitsbereich zeigt und auslösen lässt.
- [Operative Ausnahmen](./exceptions) — die abgeleiteten Zustände, die Aufmerksamkeit brauchen.
- [Business Events](./events) — wie Geschäftsaktionen die Timeline erreichen.

Nach einer Änderung an einem Katalog oder einem MCP-Schema neu erzeugen:

```bash
make docs-generate
```
