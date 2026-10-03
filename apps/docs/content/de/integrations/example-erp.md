# Ein Beispiel-ERP schrittweise anbinden

Du baust ein autonomes System auf: **Dein Agent soll verstehen, was zugesagt wurde, was fehlt und
was als Nächstes zu tun ist.** Dafür braucht er eine verlässliche Faktenbasis in Reality. Du musst
nicht gleich ein ganzes ERP anbinden; starte mit einer Frage, die dein Agent beantworten soll.
Dieses Kapitel verwendet das fiktive **Beispiel-ERP** und zeigt, wie seine Fähigkeiten mit den
angebundenen Daten wachsen.

Der Agent liest über die gemeinsamen Anwendungs-Tools und Services von Reality. Der Connector
beschafft die Quelldaten, der Interpreter macht ihre Bedeutung nutzbar. Welche Operationen der Agent
ausführen darf, wird zusätzlich ausdrücklich festgelegt; mehr Daten allein geben ihm noch keine
Schreibrechte. Die einzelnen Agent-Fähigkeiten unten beschreiben den Zielumfang nach geprüfter
Umsetzung, keine bereits laufende autonome Integration.

**Anbinden bedeutet zunächst lesen:** Das ERP liefert Originaldaten, Reality interpretiert sie. Du
musst dafür keine Reservierungs-, Versand- oder Rechnungslogik im ERP neu programmieren. Du brauchst
einen freigegebenen Export oder lesenden API-Zugang und einen passenden Reality-Interpreter. Die
Beispiele beschreiben einen geplanten Integrationsumfang, keinen bereits implementierten
Beispiel-ERP-Connector. Die gezeigten Ergebnisse sind fachliche Beispielausgaben, keine Screenshots
oder ausführbaren API-Antworten.

## Der kleine Anfang

Unsere Firma verkauft den Artikel **Stuhl Blau**. Kundin **Mira** bestellt 10 Stück. Wir beginnen an
einem vereinbarten **Stichtag**, bevor dieser neue Auftrag geliefert, reserviert oder geändert
wurde. So gibt es für ihn keine unbekannte frühere Ausführung.

| Ausbaustufe | Was du zusätzlich übernimmst                     | Welche Frage dein Agent beantworten kann        |
| ----------- | ------------------------------------------------ | ----------------------------------------------- |
| 1           | Identitäten, Aufträge und Änderungen             | Wem hat unsere Firma welchen Artikel zugesagt?  |
| 2           | Tatsächliche Lieferungen                         | Wie viel davon muss noch raus?                  |
| 3           | Anfangsbestand und echte Lagerbewegungen         | Wie viel ist jetzt im Lager?                    |
| 4           | Lieferantenzusagen und zugeordnete Wareneingänge | Was soll noch reinkommen?                       |
| 5           | Bestehende Reservierungen                        | Was ist schon zugeteilt?                        |
| 6           | Rechnungen und Zahlungen                         | Was wurde berechnet und bezahlt?                |
| 7           | Bestätigte ausgehende Commands und Rückmeldungen | Was soll das ERP auf Anweisung von Reality tun? |

Die Stufen sind ein Lernweg, keine Pflichtreihenfolge. Du kannst nach 1 oder 2 aufhören oder direkt
Finanzdaten ergänzen, wenn das deine Frage ist. Nur die benötigten Abhängigkeiten müssen vorhanden
sein. Bei Bestandsaufträgen brauchst du bereits in Stufe 1 einen Vertrag über offene Zusagen und
frühere Ausführung; „keine Lieferung importiert“ heißt sonst **unbekannt**, nicht „nichts
geliefert“.

## 1. Artikel, Kunden und Aufträge: Zusagen sichtbar machen

**Aus dem ERP übernehmen:** die zur Interpretation nötigen Artikel- und Kundenidentitäten,
Einheiten, Auftrags- und Positions-IDs, zugesagte Mengen und Termine sowie relevante spätere
Änderungen/Stornierungen. Stammdaten können einmalig zugeordnet werden; nicht jedes Artikel- oder
Adressfeld muss synchronisiert werden. Externe IDs sind die Identität. SKU und Auftragsnummer sind
Anzeigewerte, keine stillschweigend eindeutigen Schlüssel.

Beispiel: Artikel-ID `item_b7`, Kunden-ID `party_m2`, Auftrags-ID `order_q9`, Positions-ID
`line_k4`. Die Position nennt 10 Stück Stuhl Blau für Mira. Original-Payload und Version bleiben
erhalten:

```text
SourceRecord → Document → DocumentLine → Commitment
                                           Mira: 10 Stück Stuhl Blau zugesagt
```

**Ergebnis:** Dein Agent kann Zusagen nach Kunde oder Artikel auflisten. Für unseren ausdrücklich
neuen Auftrag sind 10 Stück zu liefern. Für einen älteren Auftrag mit unbekannter Lieferhistorie
kannst du zunächst nur die erfasste Zusage zeigen. Ohne vollständige Ausführungsabdeckung darf eine
rechnerisch offene Menge nicht als gesicherte Wahrheit dargestellt werden.

**Noch offen:** tatsächlicher Versand, Bestand, Zuteilung und Zahlung.

**Dein Agent:** Er kann kunden- oder artikelbezogene Zusagen nachschlagen und erklären. Für ältere
Aufträge mit unvollständiger Historie nennt er den Lieferfortschritt als unbekannt.

**Prüfen:** Derselbe Import zweimal erzeugt nur eine Zusage. Eine spätere Stornierung bleibt eine
neue Quellversion und wird nach dem geprüften Änderungsvertrag verarbeitet; sie wird nicht als
zweiter Auftrag angelegt.

## 2. Tatsächliche Lieferungen: Was muss noch raus?

**Zusätzlich übernehmen:** tatsächliche Ausführung mit eigener Ereignis-/Positionsidentität,
Artikel, Menge, Zeitpunkt und Bezug zur Auftragsposition. Auch Rücknahmen und Korrekturen gehören
zum gewählten Umfang. Ein Lieferschein, ein Label oder eine Versandfreigabe allein belegt noch
keinen physischen Abgang.

Das Lager meldet: 4 Stück aus `line_k4` wurden tatsächlich versendet. Ein geprüfter Interpreter
ordnet diese Ausführung über gemeinsame Services der Zusage zu; passende `Movement`-Datensätze
belegen die Ausführung.

| Kunde | Artikel    | Zugesagt | Geliefert | Noch zu liefern |
| ----- | ---------- | -------- | --------- | --------------- |
| Mira  | Stuhl Blau | 10       | 4         | 6               |

**Ergebnis:** Jetzt ist „Mira fehlen noch 6 Stühle“ belegt. Über alle vollständig erfassten Aufträge
kann dein Agent die offenen Mengen je Artikel zusammenfassen.

**Noch offen:** Ob diese 6 verfügbar sind. Eine ausgehende Lieferung allein liefert keinen
vollständigen Lagerbestand. Retoureneingang und Wiederaufleben einer Zusage brauchen außerdem einen
eigenen geprüften Vertrag; eine Retourenmenge wird nicht automatisch zur neuen Lieferpflicht.

**Dein Agent:** Er kann beantworten „Wem schulden wir noch welchen Artikel?“ und belegte Lieferreste
nach Kunde oder Artikel zusammenfassen. Er erteilt im Lesemodus keinen Versandauftrag.

**Prüfen:** Wiederhole dieselbe Ausführung. Geliefert bleibt 4, nicht 8; offen bleibt 6.

## 3. Anfangsbestand und Wareneingänge: Was ist im Lager?

**Zusätzlich übernehmen:** einen verlässlichen Anfangsbestand je Artikel/Lagerort/Einheit zu einem
festen Zeitpunkt und danach alle für diesen Lagerumfang relevanten physischen Bewegungen: Eingänge,
Ausgänge, Umlagerungen, Korrekturen und Retoureneingänge. Ein Warenzugang braucht eigene Identität,
Menge, Lagerort und Zeitpunkt. Ohne Bestellbezug ist die Bestandsfrage möglich, die Zuordnung zu
einer Lieferantenzusage bleibt offen.

Wir eröffnen den Bestand **nach der Lieferung aus Stufe 2**: Im Lager liegen jetzt 3 Stück. Die
frühere Lieferung über 4 zählt weiterhin zur Erfüllung des Auftrags, wird aber nicht noch einmal vom
späteren Anfangsbestand abgezogen. Danach kommen tatsächlich 3 Stück an.

```text
Anfangsbestand am Lagerstichtag: 3
Späterer Wareneingang:           3
Physischer Bestand jetzt:       6
Offene Kundenzusage:             6
```

**Ergebnis:** „6 im Lager, Mira fehlen 6.“ Das ist noch keine verbindliche Aussage, dass Mira alle 6
bekommen kann: Andere Reservierungen, Sperren, Lagerorte oder Bedingungen können relevant sein.

**Noch offen:** zukünftige Eingänge und bestehende Zuteilung. Ein Bestandssnapshot ersetzt keine
Bewegungshistorie. Fehlende Bewegungen werden nicht aus Snapshot-Differenzen erfunden; ein nur
verkaufbarer Quellbestand wird nicht als physischer Bestand ausgegeben.

**Dein Agent:** Er kann offenen Bedarf mit dem erfassten physischen Bestand vergleichen und
erklären, welche zusätzlichen Zuteilungs- oder Sperrdaten für eine belastbare Freigabe fehlen.

**Prüfen:** Eröffnungsbestand und spätere Bewegungen einmal zählen. Stichtagsmengen mit dem ERP
abgleichen. Eine verspätet gelieferte frühere Bewegung darf den späteren Snapshot nicht doppelt
verändern.

## 4. Bestellungen: Was soll noch reinkommen?

**Zusätzlich übernehmen:** Lieferantenidentität, Bestellung und Positionen mit zugesagten Mengen und
Terminen, Änderungen/Stornierungen sowie den Bezug tatsächlicher Wareneingänge zur Position. Eine
Bestellung ist eine Zusage, noch kein Bestand.

Eine Lieferantin hat 5 Stück zugesagt. Die 3 eingegangenen Stück aus Stufe 3 gehören zu dieser
Bestellung. Der Interpreter erzeugt eine Lieferanten-`Commitment` und ordnet den vorhandenen Eingang
zu, ohne ihn noch einmal als neue Lagerbewegung zu buchen.

**Ergebnis:** „3 erhalten, 2 noch erwartet.“ Im Lager bleiben aktuell 6; die erwarteten 2 erhöhen es
erst bei tatsächlichem Eingang. Wenn der Termin vorliegt, kann dein Agent erwartete Eingänge
zeitlich einordnen; eine Prognose bleibt von der aktuellen Bestandswahrheit getrennt.

**Noch offen:** welche Ware bereits einem Kunden zugeteilt ist.

**Dein Agent:** Er kann noch erwartete Lieferantenmengen und zugesagte Termine erklären und sie
neben den Kundenbedarf stellen. Erwartete Ware behandelt er nicht als bereits vorhandenen Bestand.

**Prüfen:** Bestellung und Wareneingang in vertauschter Reihenfolge übernehmen. Am Ende bleibt der
Eingang genau einmal gezählt und der Bestellrest beträgt 2.

## 5. Reservierungen: Was ist schon zugeteilt?

**Zusätzlich übernehmen:** vorhandene Zuteilungen mit stabiler Identität, Bezug zur Kundenzusage,
Artikel, Lagerort und Menge sowie Freigaben und Verbrauch. Einem ERP-Feld „reserviert: 2“ ohne
Zuordnungs- und Versionsvertrag fehlt noch die nötige Bedeutung.

Im vereinbarten Lagerumfang sind 2 der 6 Stück für eine andere Kundenzusage reserviert. Gemeinsame
Services halten die Zuordnung als `Reservation` zur passenden `Commitment`.

**Ergebnis:** „Physisch 6, reserviert 2, rechnerisch verfügbar 4; für Mira offen 6.“ Das begründet
eine Mengenlücke im betrachteten Umfang. Eine operative Freigabe kann zusätzliche Sperren oder
Regeln benötigen. Im Zuschauerbetrieb erzeugt Reality keine konkurrierende eigene ERP-Zuteilung.

**Dein Agent:** Er kann Mengenlücken trotz physischem Bestand erkennen und eine mögliche Zuteilung
zur Prüfung vorschlagen. Eine eigene Reservierung ist eine gesondert freizugebende Operation.

**Prüfen:** Wiederholung, Freigabe und tatsächlicher Verbrauch verändern dieselbe Zuordnung nach dem
Vertrag, ohne Reservierung oder Abgang doppelt zu zählen.

## 6. Rechnungen und Zahlungen: Was ist finanziell offen?

**Zusätzlich übernehmen:** originale Finanzbelege mit angegebenen Beträgen, Währung, Steuern,
Fristen und Auftrags-/Positionsbezügen; tatsächliche Zahlungen mit eigener Identität, Betrag,
Währung und Zuordnung. Gutschrift und Erstattung sind eigene Ereignisse.

Eine Rechnung nennt 80 EUR; eine zugeordnete erfolgreiche Zahlung nennt 30 EUR. Unter dem
vereinbarten Finanzvertrag sind 50 EUR offen. Beide Quellbeträge bleiben unverändert; Reality
berechnet keinen Ersatz-Rechnungsbetrag aus Stückzahl und Preis.

**Ergebnis:** Dein Agent kann Berechnung und Zahlung erklären. Eine gebuchte Rechnung beweist noch
keine Zahlung, eine Zahlung keine Lieferung. Benötigst du nur Lieferfragen, ist diese Stufe nicht
Pflicht.

**Dein Agent:** Er kann offene Rechnungsbeträge und belegte Zahlungseingänge erklären. Zahlungs-
oder Kreditfreigabe benötigt zusätzlich die dafür geprüften Regeln und Berechtigungen.

**Prüfen:** Rechnung, Teilzahlung, Gutschrift und Replay getrennt prüfen; Originalbelege und
Zuordnung bleiben nachvollziehbar.

## 7. Vom Zuschauen zum Steuern

Bis hierher genügt ein lesender Adapter. **Erst jetzt kommt der Rückweg dazu:** Reality gibt einen
Command wie „Auftrag X zum Versand freigeben“ oder „Rechnung für Auftrag X anlegen“; das ERP führt
die vereinbarte Operation aus. Nur die Daten für die übertragene Entscheidung sind Pflicht, nicht
alle vorherigen Stufen.

Mutierende Agent-/Chat-Aufrufe brauchen **menschliche Bestätigung**. Der Rückweg benötigt ein
separat geprüftes Design mit unterstützter ERP-Operation, Rechten, Idempotenz, Korrelation,
Wiederholungen und Ergebnisabgleich. Konkurrierende ERP-Automatiken werden für die übertragene
Entscheidung geprüft und koordiniert. Automatische Regeln benötigen einen eigenen geprüften
Ausführungsvertrag.

**Ergebnis:** Reality kann angeforderte Vorgänge steuern. Eine erfolgreiche Anfrage ist weiterhin
kein physischer Versandbeleg. Ausführung und entstehende Belege kommen über den Leseweg zurück;
Timeouts und Widersprüche bleiben sichtbar. Diese Beispiele implementieren keinen Rückweg.

**Dein Agent:** Er kann erlaubte Vorgänge vorbereiten, über die gemeinsamen Tools anfordern und
Rückmeldungen prüfen. Für ausdrücklich geprüfte automatische Abläufe entsteht eine Schleife aus
Beobachten, Bewerten, Handeln und Ergebnisprüfung. Fehlen Daten oder passt die Rückmeldung nicht,
bleibt der Fall sichtbar offen statt als erfolgreich erledigt zu gelten.

**Prüfen:** Wiederholte Anfrage erzeugt keinen zweiten Vorgang. Fehlende Rückmeldung wird nicht als
erledigte Ausführung angezeigt.

## Welche Daten dein Agent über Reality braucht

Im externen System brauchst du lesbaren Zugriff auf die gewählten Originalobjekte samt Positionen,
IDs, Beziehungen, Versionen und benötigten Ausführungsbelegen. Starte für den Lernfall mit einem
freigegebenen Fixture/Export; für laufenden Betrieb ergänze Erstimport, Änderungen und Abgleich. Ein
Webhook kann eine Änderung melden; fehlende Details werden über die autoritative API nachgeladen.
Ein täglicher Export zeigt entsprechend nur den zuletzt übernommenen Stand.

In Reality brauchst du Transport zur gemeinsamen Grenze `enqueue_source`,
Kontext-/Identitätsauflösung und registrierte Interpreter für die gewählten Quelltypen. Der
Transport schreibt keine eigenen Domänentabellen und speichert den Original-Payload verlustfrei.
Ohne Interpreter bleibt ein Datensatz sichtbar `unmapped`; bloßes Synchronisieren einer JSON-Datei
erzeugt noch keine fachliche Antwort.

Halte pro Quellbereich fest: Was deckt der erste Import ab? Seit welchem Zeitpunkt ist die Historie
vollständig? Wie werden Änderungen, Stornierungen, Löschungen und Wiederholungen erkannt? Wie frisch
sind die Daten? Bei einem Ausfall wird eine Antwort als veraltet oder unvollständig erkennbar.
Wiederkehrende Übernahme läuft über gemeinsame Scheduled Jobs, nicht über Browser-Timer.

Für deinen ersten Versuch: **Stufe 1 mit einem neuen Auftrag, dann Stufe 2 mit einer echten
Teillieferung.** Damit wird der Unterschied zwischen Zusage und Erfüllung greifbar. Danach ergänzt
du Bestand und Wareneingänge, wenn dein Agent Verfügbarkeit erklären soll.

[Technisches Auftragsbeispiel](./order-example) · [Von Quelldaten zu Reality](./connector-contract)
· [Shopify](./shopify) · [Xentral](./xentral) · [Odoo](./odoo)
