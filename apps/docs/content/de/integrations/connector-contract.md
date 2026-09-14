# Connector-Contract

## Verantwortlichkeiten

Ein Connector authentifiziert sich beim Quellsystem, wählt freigegebene Datensätze aus, erfasst sie
verlustfrei und liefert sie mit Mandanten- und Quellidentität über die Anwendungsgrenze von Reality
ein. Er schreibt keine Domänentabellen, leitet im Transportcode keinen operativen Status ab und
umgeht keine Bestätigung.

## Verlustfreie Payloads

Speichere den ursprünglichen Datensatz und die relevanten Metadaten des Umschlags. Verwirf keine
unbekannten Felder. Binäre Quelldateien gehören in privaten Objektspeicher und werden über
undurchsichtige Schlüssel referenziert; fachliche Identität und Metadaten bleiben in PostgreSQL.

## Idempotenz und Versionierung

Wird dieselbe Version aus dem Vorsystem erneut geliefert, darf das keine doppelten Geschäftsvorfälle
erzeugen. Ein geänderter Datensatz im Vorsystem erzeugt eine neue SourceRecord-Version oder ein
neues Ereignis, damit die Historie erklärbar bleibt. Belegnummern für Menschen sind keine
Idempotenzschlüssel, solange kein ausdrücklicher Contract der Quelle deren Gültigkeitsbereich und
Versionsverhalten belegt.

## Kriterien für Typisierung

Übernimm ein Quellfeld erst dann ins typisierte Modell, wenn die Kernlogik wiederholt

- damit rechnet,
- danach filtert oder darauf verknüpft,
- es einschränkt oder validiert,
- daraus Prognosen ableitet oder
- darauf handelt.

## Fehlermodell

Unterscheide Verbindungs- und Authentifizierungsfehler, ungültige Umschläge, nicht unterstützte
Interpretation und Ausfälle nachgelagerter Dienste. Bewahre die übernommene Quelleingabe, gib eine
unbedenkliche Meldung für den Betrieb aus, protokolliere diagnostischen Kontext ohne Geheimnisse und
mach das Wiederholverhalten ausdrücklich.

## Ergebnis: Nachvollziehbarkeit

Soweit zutreffend, führt der Weg von SourceRecord → Document/DocumentLine → Fact, Commitment,
Reservation, Movement oder LedgerEntry. Trifft eine Stufe nicht zu, erfindet der Connector sie
nicht.

> **Normative Invariante:** Connectors rufen gemeinsame Dienste und Werkzeuge auf. Sie schreiben
> niemals direkt über das ORM und implementieren keinen zweiten Satz Geschäftsregeln.
