---
aside: false
---

# So liest du die Listen {#how-to-read-the-lists}

[Zurück zur Tool-Übersicht](/de/tool-usage/)

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
