# Von Quelldaten zu Reality

Originaldaten unverändert erfassen, als Evidence einordnen und mit Reality verknüpfen. Das ist das
gemeinsame Konzept hinter jeder Datenanbindung. Dadurch bekommt dein Agent Fakten, die er über
gemeinsame Anwendungs-Tools erklären und nutzen kann. Eine externe JSON-Datei zu kopieren reicht
dafür noch nicht.

## Die Idee: Source → Evidence → Reality

Jede Schicht beantwortet eine andere Frage:

| Schicht  | Frage                                              | Beispiel                                                                                                         |
| -------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Source   | Was hat das externe System tatsächlich geliefert?  | Unveränderlicher `SourceRecord` mit originalem ERP-Auftrags-Payload und Quell-/Versionsidentität                 |
| Evidence | Was sagt dieser Datensatz aus?                     | `Document` und `DocumentLine` halten den Auftrag und seine angegebene Positionsmenge fest                        |
| Reality  | Welche Verpflichtung oder Ausführung folgt daraus? | Eine `Commitment` sagt der Kundin 10 Stück zu; später belegt tatsächlicher Versand eine `Movement` und Erfüllung |

Evidence ist nicht bloß ein Dateianhang. Sie ordnet Quellangaben so ein, dass Verpflichtungen und
Ausführung auf den richtigen Beleg und die richtige Position verweisen können. Reality nutzt die
kürzeste wahre Beziehung: Quell-, Beleg- und Positionsbezüge werden nicht auf jeden verbundenen
Datensatz kopiert, wenn ein vorhandener Link die Spur bereits herstellt.

## Ein Auftrag, danach ein tatsächlicher Versand

Das ERP liefert einen neuen Auftrag: Mira sind 10 Stühle Blau zugesagt. Artikel-/Kundenidentitäten
und Einheiten sind aufgelöst. Der Connector bewahrt den vollständigen Original-Payload; der
registrierte Interpreter erzeugt über gemeinsame Services Evidence und Kundenzusage. Später liefert
das zuständige Lager den tatsächlichen Versand von 4 Stück mit eigener Identität und Bezug zur
Auftragsposition.

```text
Originaler Auftrags-SourceRecord → Document / DocumentLine → Commitment: zugesagt 10
Originale Ausführungsquelle      → Ausführungs-Evidence    → Movement: geliefert 4
                                                           mit Zusage verknüpft
Beobachtung beim Lesen: 6 noch zu liefern
```

Die verbleibenden 6 werden beim Lesen aus der gehaltenen Zusage und belegten Ausführung abgeleitet.
Sie werden weder als neue autoritative Quellangabe gespeichert noch als Lieferstatus auf das
Auftrags-Document kopiert. Das Beispiel setzt die vollständige relevante
Änderungs-/Ausführungshistorie ab dem vereinbarten Anfang voraus; sonst ist die Restmenge unbekannt.
Ein Lieferschein oder Label allein beweist keinen physischen Versand.

**Dein Agent** kann „Mira fehlen noch 6 Stühle“ erklären und über die Links bis zu den Originalen
zurückgehen. Für Bestand, Zahlung oder automatische Freigabe braucht er die zusätzlichen Quellen und
geprüften Regeln der jeweiligen Frage. Mehr erfasste Daten erlauben nicht automatisch eine Aktion im
Vorsystem.

## Original-Payload, eigener Datenbestand und spätere Änderungen

Ein Shopify-Auftrag, ein ERP-Datensatz oder ein ursprüngliches Tool-Ergebnis kann eine Quelle sein,
wenn es über einen vereinbarten Quellvertrag erfasst wird. Nicht jeder Agent-Tool-Aufruf erzeugt
neue Source-Daten: Eine Abfrage vorhandener Reality liest den eigenen Datenbestand.

1. **Original erfassen:** Der Connector liefert den empfangenen Payload unverändert samt
   Quellsystem, Objekttyp, externer ID und Versionskontext. Reality speichert ihn als
   `SourceRecord`. „Vollständig“ meint den empfangenen Payload des Objekts, nicht den gesamten
   Datenbestand des ERP.
2. **Fachlich einordnen:** Der passende Interpreter erzeugt über gemeinsame Services die Evidence
   und verknüpfte Reality. Reality besitzt damit einen eigenen fachlichen Datenbestand und eine
   nachvollziehbare Änderungshistorie. Er ist keine bloße Live-Ansicht des Fremdsystems.
3. **Spätere Fassung erfassen:** Ändert sich das externe Objekt, liefert der Connector eine neue
   Fassung unter derselben Quellidentität. Ein bisher nicht erfasster Inhalt erzeugt eine weitere
   unveränderliche Quellversion; die frühere bleibt erhalten. Ein identischer Payload wird als
   Wiederholung erkannt und erzeugt keine zusätzliche SourceRecord-Version.
4. **Änderung interpretieren:** Erst der Interpreter entscheidet anhand seines geprüften Vertrags,
   was die neue Fassung fachlich bedeutet. Unterstützte Änderungen laufen über gemeinsame Services;
   nicht unterstützte oder widersprüchliche Fälle bleiben zur Prüfung sichtbar. Eine neue Source
   allein bedeutet noch keine erfolgreiche Änderung der Reality.

Die Fassungen eines externen Objekts gehören zu einem `SourceStream`. Seine Identität besteht aus
Tenant, `source_system`, `source_type` und `external_id`. Reality erkennt identischen Inhalt über
einen kanonischen Payload-Hash innerhalb dieses Streams. Auch eine bereits bekannte frühere Fassung
ist eine Wiederholung. Die Versionsnummer ist die Reihenfolge der gespeicherten Quellfassungen,
nicht automatisch die fachliche Reihenfolge der Änderungen im Vorsystem.

Wenn ein verlässlicher `source_version_at` vorliegt, kann Reality verspätete Fassungen als veraltet
und unterschiedliche Inhalte mit demselben Quellzeitpunkt als Konflikt einordnen. Ohne diesen
Versionskontext kann es die ursprüngliche zeitliche Reihenfolge nicht aus dem Inhalt erraten; dafür
braucht die Anbindung einen geprüften Vertrag.

```text
Externer Auftrag, gleiche Objekt-ID
  → SourceRecord v1: zugesagt 10 → Evidence → Commitment
  → SourceRecord v2: zugesagt  8 → geprüfte Interpretation derselben Verpflichtung
  → derselbe Payload erneut    → bekannte Quellfassung; kein zweiter Auftrag
```

Bei bereits belegter Lieferung von 4 bedeutet eine unterstützte Reduzierung der Zusage von 10 auf 8:
noch 4 offen. Das gilt unter vollständiger Ausführungsabdeckung und dem geprüften Änderungsvertrag.
Die vorhandene Shopify-Auftragsinterpretation unterstützt bestimmte Reduzierungen und Stornierungen;
andere Änderungen benötigen Prüfung. Sie vergleicht die gewünschte Änderung auch mit der aktuellen
Reality, damit Replay oder eine spätere Quellfassung bereits erfolgte Ausführung und menschliche
Revisionen nicht einfach zurückdrehen. Das ist **kein allgemeiner automatischer Feldvergleich**, der
beliebige Fremddaten ohne fachlichen Interpreter versteht.

Manche Quellen liefern Ereignisse oder nur eine Änderungsmeldung statt eines vollständigen Objekts.
Auch diesen Original-Payload bewahrt der Connector; nötige Objektdetails lädt er nach dem
Quellvertrag autoritativ nach und erfasst sie nachvollziehbar. Reality erfindet aus fehlenden
Feldern keine neue Wahrheit.

Die Herkunft heißt hier **Source**, nicht **Surface**. Eine Surface ist ein Zugang beziehungsweise
eine Oberfläche. Die Spur zu einer Quelle führt zum Beispiel über Commitment → DocumentLine →
Document → SourceRecord; sie braucht keinen zusätzlichen direkten Source-Link an jedem Datensatz.
Weitere Quellen wie tatsächlicher Versand ergänzen diesen Datenbestand mit eigener Identität und
ihrer belegten Verbindung zur Zusage.

## Wer macht welchen Teil?

- **Connector:** meldet sich an, liest freigegebene Originaldatensätze und erfasst sie verlustfrei
  an der Anwendungsgrenze von Reality. Er liefert Tenant, Quellidentität und Versionskontext.
- **Interpreter:** kennt die Bedeutung dieses Quelltyps, löst Identitäten auf und ruft gemeinsame
  Services auf, um Evidence und Reality aufzubauen. Nicht unterstützte Bedeutung bleibt sichtbar
  `unmapped` oder benötigt Prüfung.
- **Services, Views und Projections:** berechnen aktuelle Beobachtungen aus den gehaltenen
  Datensätzen. Agent Tools machen dieselben Anwendungsfähigkeiten zugänglich, ohne eigene
  alternative Geschäftsregeln.

Mit [den Beispiel-ERP-Stufen](./example-erp.md) wählst du die Fakten aus, die dein Agent braucht.
[Die technische Umsetzung eines Auftragsimports](./order-example.md) hilft beim Einstieg in die
Implementierung. Die folgenden Regeln beschreiben, wie jede Anbindung verlustfrei, wiederholbar und
nachvollziehbar bleibt.

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

## Vollständigkeit und Abnahme

„100 %“ bedeutet **vollständig für einen schriftlich vereinbarten Unternehmens-, Prozess- und
Zeitumfang**. Es bedeutet weder jedes API-Feld noch die gesamte Historie einer Quelle. Eine
Abdeckung ab Stichtag ist keine vollständige Rekonstruktion der früheren Historie. Nicht enthaltene
Module und nicht verfügbare Daten werden ausdrücklich benannt.

Die durchgehenden Anleitungen zeigen Umfang, konkrete Quellbereiche und Umsetzungslücken:
[Xentral](./xentral.md), [Shopify](./shopify.md), [Odoo](./odoo.md).

### Die gemeinsame Abdeckungsmatrix

Die Matrix beschreibt mögliche Bereiche, keine Pflichtliste für jedes Zuschauen. Wähle nur die
Zeilen für deine Betriebsart und Fragestellung. Auch der Abnahmefall prüft nur diesen vereinbarten
Umfang.

Ergänze für jede Zeile **zuständige Quelle, originale Objekt-/Positions-ID, Quelltyp/Interpreter,
Umfang, Status und Prüfnachweis**. Zulässige Status: geplant, nur erfasst, interpretiert, geprüft
oder außerhalb des vereinbarten Umfangs mit Begründung. Ein Shell-Eintrag ist nur eine mögliche
Capability; ein SourceRecord beweist nur Capture. Keine dieser Stufen bedeutet bereits „geprüft“.

| Bereich                  | Benötigte Quelle/Evidence                                                                              | Fachlicher Zweck                                                         | Nachweis für die Abnahme                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| Identität/Stammdaten     | Unternehmen, Partnerrollen, Artikel/Varianten, Einheiten, Lagerorte und Quell-IDs                      | Eindeutige tenant-begrenzte Referenzen                                   | Keine Mehrdeutigkeit; Quell-IDs bleiben erhalten; fremde IDs werden abgewiesen          |
| Verkauf                  | Auftragskopf/-positionen, Mengen/Termine, Änderungen/Stornierung                                       | Document/DocumentLine und Commitment                                     | Zusage entspricht Quelle; neue Version und Wiederholung sind nachvollziehbar            |
| Einkauf                  | Bestellpositionen, Lieferantenzusagen, Eingangsbelege                                                  | Lieferanten-Commitment und Eingang                                       | Teillieferung, Restmenge und Stornierung stimmen                                        |
| Bestand                  | Belegter Anfangsbestand plus spätere Eingänge/Ausgänge/Umlagerungen/Korrekturen                        | Bestands-Evidence und Movement                                           | Abgleich pro Artikel/Lager/Einheit; kein doppelter Eröffnungsbestand                    |
| Reservierung/Fulfillment | Bestehende Zuteilung und tatsächliche Lieferpositionen                                                 | Reservation, ausgeführter Movement und kürzeste Zusagenverknüpfung       | Reserviert ist nicht geliefert; keine doppelte Zuteilung oder Ausführung                |
| Rechnungen/Gutschriften  | Angegebene Beträge, Steuern, Währung, Zahlungsbedingungen, Beleg-/Positionsbezug                       | Finanz-Evidence und gemeinsame Finanzservices                            | Werte unverändert übernommen; keine Rechnung aus Auftragssumme erfunden                 |
| Zahlung/Settlement       | Erfolgreiche Transaktion, Rechnungszuordnung, gegebenenfalls Gebühren/Auszahlung                       | Zahlungs-/Settlement-Services; LedgerEntry nach gültigem Buchungsvertrag | Offene Position und Geldbewegung erklärbar; Doppelimport ausgeschlossen                 |
| Retoure/Erstattung       | Ankündigung, physischer Eingang, Gutschrift und Geldrückgabe                                           | Separate Lager-/Finanzvorgänge                                           | Kein Bestand aus Erstattung erfinden; kein doppelter Finanzvorgang aus mehreren Quellen |
| Weitere Module           | Produktion/Stückliste, Chargen/Seriennummern, Konditionen, Dienste/Abos/Kostenrechnung, sofern genutzt | Vorhandene Fähigkeit oder separat spezifizierte Erweiterung              | Jede fachliche Abhängigkeit geprüft oder begründet außerhalb des Umfangs                |
| Betrieb                  | Erstimport, Änderungen, Löschung/Archivierung, Wiederholung, Rückstand und Abgleich                    | Dauerhaftes nachvollziehbares Intake                                     | Wiederanlauf, Tenant-Isolation, Fehler-/Review-Zuständigkeit und Aktualitätsziel belegt |

### Quellenautorität und Stichtag festlegen

Shop und ERP können denselben Auftrag melden. Bewahre beide Originalquellen, aber definiere pro Fakt
und Phase eine fachliche Autorität sowie den belegten Verknüpfungsweg. Shop-Auftrag, ERP-Lieferung
und Zahlungsanbieter dürfen verschiedene Bereiche verantworten. Eine spätere Übergabe braucht einen
Vertrag; gleicher Betrag, SKU oder Belegnummer beweist keine Identität. Nicht geklärte Duplikate
bleiben im Review.

Ein Bestands-Snapshot beschreibt einen Zustand und beweist keine historische Bewegung. Lege fest, ob
er als Beobachtung oder belegte Eröffnung über einen vorhandenen Service interpretiert wird. Bei
Eröffnung zu Zeitpunkt T kommen nur die vereinbarten Folgebewegungen hinzu; frühere Historie wird
nicht nochmals addiert. Für offene Finanzpositionen gilt derselbe Stichtagsgedanke.
Reservierte/verfügbare Mengen sind nicht automatisch physischer Bestand.

Änderungen und Löschungen brauchen einen eigenen Vertrag: Eine verschwundene API-Zeile ist ohne
Beleg keine Stornierung, Lieferung oder Korrekturbewegung. Bewahre frühere SourceRecords,
Versionsfolge und Review-Ergebnis. Finanzwerte, die die Quelle nennt, werden nicht neu berechnet.

### Checkliste für „vollständig“

- [ ] Unternehmen/Tenants, Quellen, Module, Betriebsart, Stichtag und ausgeschlossene Bereiche sind
      schriftlich vereinbart.
- [ ] Jeder Bereich im Umfang hat zuständige Quelle, Identitäts-/Versionsvertrag, Interpreter und
      Prüfnachweis; „nur erfasst“ zählt nicht als fachlich abgedeckt.
- [ ] Stammdaten und Beziehungen sind eindeutig aufgelöst; Original-Payloads und unbekannte Felder
      bleiben erhalten.
- [ ] Die relevanten Schritte des Abnahmefalls bestehen mit echten Quell-Fixtures; Teilmengen,
      Stornierung, Retoure und Finanzzuordnung werden geprüft, soweit sie im Umfang liegen.
- [ ] Erstimport und Folgeänderungen stimmen auf Record-Ebene sowie bei Mengen/Beträgen überein;
      Differenzen sind erklärt. Summengleichheit allein genügt nicht.
- [ ] Wiederholung, vertauschte Versionen, Teilfehler, fehlende Records, Mehrdeutigkeit und fremde
      Tenant-IDs haben geprüfte Ergebnisse.
- [ ] Zugangserneuerung, API-Limits, dauerhafter Checkpoint, Wiederanlauf, Aktualitätsziel und
      regelmäßiger Abgleich sind überprüft. Wiederkehrendes Intake folgt
      `docs/features/scheduled-jobs.md`.
- [ ] Nicht unterstützte Fälle sind sichtbar und haben eine verantwortliche Rolle; sie werden nicht
      als erfolgreiche Interpretation ausgegeben.

### Rückschreiben ist ein eigener Umfang

Eine vollständig lesende Anbindung kann fertig sein, ohne im Vorsystem zu schreiben. Definiere
ausgehende Aktionen einzeln mit erlaubter Wirkung, Berechtigung, Server-Vorschau/Bestätigung,
Idempotenz, Fehlerbehandlung und anschließendem Read zur Prüfung. Ändernde Agent Tools benötigen
ausdrückliche Freigabe. Externe Effekte oder neue Scheduling-Infrastruktur brauchen den separat
geprüften Entwurf nach dem Scheduling-Vertrag. Eine Capture-Freigabe autorisiert kein beliebiges
Rückschreiben.
