---
aside: false
---

# Wie ein Agent das richtige Tool wählt {#choosing-a-tool}

[Zurück zur Tool-Übersicht](/de/tool-usage/)

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
