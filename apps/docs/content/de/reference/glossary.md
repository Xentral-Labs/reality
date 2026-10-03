# Glossar

Die wichtigsten Begriffe aus Reality, dem interaktiven Kommandokatalog und den
Entwickler-Anleitungen. Die Einträge erklären Bedeutung, Zweck und Abgrenzung; technische
Modellnamen bleiben erkennbar.

**Als Orientierung:** Quellen liefern Originaldaten, Belege strukturieren Evidence,
Reality-Datensätze tragen die Geschäftslage. Commands führen Operationen aus, Projections berechnen
Antworten und Views zeigen sie.

## Produkt und Zugriff

### Reality

Das operative und finanzielle Modell eines Unternehmens: Verpflichtungen, Bestandszuordnungen,
Bewegungen und Buchungen. Diese Datensätze ermöglichen Aktionen und erklären die aktuelle Lage.
Belege liefern Evidence; Liefer- und Zahlungszustand werden aus den operativen Datensätzen
abgeleitet statt als Belegstatus gespeichert.

### Business Graph

Beziehungen und die Timeline zusammengehöriger Geschäftsdaten. Verfolge zum Beispiel einen Auftrag
über seine Positionen zu Lieferzusagen und Versandbewegungen. Der Graph zeigt den Kontext, den
Reality besitzt; er verspricht keine vollständige Historie aller Vorsysteme.
[Das Modell erkunden](/de/concepts/business-reality-guide).

### Business Facts

Der Produktbereich zum Prüfen einzelner Datensätze, einschließlich Quellen, Belegen und operativer
Records. Der Name umfasst mehr als den speziellen Datentyp [Fact](#fact). Hier untersuchst du die
konkreten Datensätze hinter einer Graph-Beziehung oder einem berechneten Ergebnis.

### Tools

Geschäftsfunktionen für Menschen und Agenten: Operationen, Sichten und berechnete Ergebnisse. Manche
Tools lesen nur; andere bereiten Änderungen vor oder führen sie unter ihren Berechtigungs- und
Bestätigungsregeln aus. Der [interaktive Kommandokatalog](/de/tool-usage/) erklärt verfügbare
Funktionen, Eingaben und Wirkungen.

### Mandant

Die Isolationsgrenze für Geschäftsdaten, normalerweise das für die Anfrage gewählte Unternehmen.
Jede geschäftliche Abfrage und Operation erzwingt diese Grenze. Eine Datensatz-ID aus einer anderen
Firma erlaubt keinen Zugriff darauf. Account und Unternehmenszugriff sind von den Geschäftsdaten
selbst getrennt.

### Sandbox und Live-Demo

Eine Sandbox ist ein Unternehmen zum Üben mit Testdaten. Live-Demo ergänzt synthetische
Geschäftseingänge über die gemeinsamen Hintergrunddienste. Neue Demo-Aufträge bedeuten nicht, dass
ein Agent sie erfüllt hat: Quelleingang und nachgelagerte Agentenarbeit sind getrennt.
[Eine Demo-Firma erleben](/de/getting-started/demo-company).

## Quellen und Belege

### SourceRecord

Unveränderliche, verlustfrei übernommene Eingabe einer Quelle, etwa die Originaldaten eines
ERP-Auftrags. Reality bewahrt, was die Quelle tatsächlich geschickt hat, einschließlich noch nicht
typisierter Felder. Geänderte Eingaben erzeugen eine neue Version oder ein Ereignis, statt das
Original zu überschreiben.

### Payload

Der Originalinhalt, den ein externes System liefert. Er kann Geschäftsfelder, verschachtelte
Strukturen und quellenspezifische Metadaten enthalten. Die verlustfreie Aufbewahrung zeigt, was
eingegangen ist, ohne jedes externe Feld zum Bestandteil des Kernmodells zu machen.

### Document und DocumentLine

Aus Quelldaten interpretierte, strukturierte Geschäftsbelege, etwa ein Auftrag mit seinen einzelnen
Positionen. Übernommene Beträge und Mengen bleiben die von der Quelle angegebenen Werte. Ein Beleg
besitzt keinen Reservierungs-, Liefer- oder Zahlungszustand: Diese Antworten kommen aus verknüpften
Reality-Datensätzen.

### Evidence

Die strukturierte Grundlage einer geschäftlichen Aussage oder Aktion, die sie mit übernommenen
Quelldaten verbindet. Eine Auftragsposition belegt zum Beispiel eine Lieferzusage; ihr Beleg
verweist auf den ursprünglichen SourceRecord. Evidence erklärt, warum ein Datensatz existiert; sie
ist keine weitere Kopie operativen Zustands.

### Provenienz und Nachvollziehbarkeit

Der Weg von einem Ergebnis zu seinen zugrunde liegenden Datensätzen, Belegen und Originalquellen.
Verfolge zum Beispiel verfügbaren Bestand zu Bewegungen und aktiven Reservierungen und von dort zu
vorhandenen Belegverknüpfungen. Eine Erklärung muss diesen Weg prüfbar machen, statt nur eine
plausible Geschichte zu erzählen.

### Connector

Der Transport, der Daten aus einem externen System nach Reality bringt. Er übernimmt Quellenzugriff
und Payload-Übertragung; er erzeugt nicht allein deshalb Bestands- oder Finanzwirkungen, weil ein
Feld im Vorsystem existiert. Die fachliche Interpretation übernimmt der Interpreter.
[ERP und Datenquellen anbinden](/de/development/connectors).

### Interpreter

Die Komponente, die übernommenen Quelldaten fachliche Bedeutung gibt. Ein Auftrags-Interpreter kann
strukturierte Auftragsbelege und belegte Zusagen erzeugen; ein tatsächlicher Versand benötigt seine
eigene Quelle und Interpretation. Payload-Transport und Verständnis seiner Geschäftswirkung sind
getrennte Aufgaben. [Quelleninterpretation](/de/integrations/connector-contract).

### Idempotenz

Die Wiederholung derselben übernommenen Anfrage oder Quellversion darf keine doppelten
Geschäftswirkungen erzeugen. Wird dieselbe Versandmeldung zweimal geliefert, darf sich die
Bestandsbewegung nicht verdoppeln. Eine tatsächlich geänderte Quellversion bleibt eine eigene
Eingabe mit eigener Historie.

### Quellenverantwortung

Die vereinbarte Zuständigkeit für eine geschäftliche Aussage oder Wirkung: Welche Quelle liefert den
Auftrag, den tatsächlichen Versand oder die Zahlung? Zwei Systeme können dasselbe Ereignis melden;
der Import beider Meldungen darf seine Wirkung nicht doppelt erfassen. Empfangene Werte bleiben wie
angegeben erhalten; Beobachtungen wie aktueller Bestand werden aus vorhandenen Datensätzen
abgeleitet. [Quellenverantwortung vereinbaren](/de/integrations/connector-contract).

## Operative und finanzielle Datensätze

### Fact

Eine unveränderliche Beobachtung, die ein SourceRecord desselben Mandanten ausdrücklich belegt und
die über ein geprüftes Predicate an ein bestehendes Reality-Subjekt gebunden ist. Sie ist keine
Agentenvermutung und keine Kopie typisierten operativen Zustands. Ein Fact hält eine belegte
Beobachtung fest; ein aktuell berechneter Bestand ist dagegen ein abgeleitetes Ergebnis.
[Facts und offene Fragen](/de/concepts/business-reality-guide/06-facts-and-open-questions#facts).

### Predicate

Die festgelegte Bedeutung eines Facts: Was wird über sein Subjekt ausgesagt, und welche Evidence
belegt es? Predicates benötigen geprüfte Semantik; ein beliebiges Agentenlabel begründet keinen
neuen verbindlichen Geschäftsbegriff. Sie unterscheiden sich von typisierten Mengen, mit denen
Bestands- oder Zahlungsservices arbeiten.

### Commitment

Eine Verpflichtung zu liefern, zu empfangen, zu zahlen oder zu vereinnahmen. Eine Verkaufsposition
kann eine ausgehende Lieferzusage belegen, erwartete Beschaffung eine eingehende. Die verbleibende
Arbeit ergibt sich aus der Zusage und ihren verknüpften Erfüllungsdatensätzen statt aus einem
Lieferstatus am Auftragsbeleg.

### Reservation

Eine Zuordnung von Bestand oder Kapazität direkt zu einem Commitment. Reservierter Bestand steht
anderen Zusagen nicht mehr zur Verfügung, wurde aber noch nicht physisch versendet. Die kürzeste
fachliche Beziehung lautet Reservation → Commitment; doppelte Verknüpfungen zu Auftrag und Quelle
sind nicht nötig.

### Movement

Eine erfasste Mengenbewegung zwischen Lagerorten oder Bestandspositionen, etwa Wareneingang oder
Versand. Physischer Bestand wird aus Movements abgeleitet; Auftrag oder Reservierung allein
verändern ihn nicht. Korrekturen erhalten die ursprüngliche Bewegung und schaffen eine ausdrückliche
Prüfspur.

### LedgerEntry

Eine Soll- oder Habenbuchung in der ausgeglichenen finanziellen Reality. Zusammengehörige Buchungen
erklären eine Finanzwirkung und tragen die Berechnung finanzieller Positionen. Ein Storno erzeugt
ausdrückliche Gegenbuchungen und ihre Beziehung zur ursprünglichen Gruppe, statt die
Originalbuchungen zu bearbeiten.

### Physischer, reservierter und verfügbarer Bestand

Physischer Bestand ergibt sich aus erfassten Bewegungen. Reservierter Bestand ist aktiven Zusagen
zugeordnet; verfügbarer Bestand ist physischer Bestand abzüglich aktiver Reservierungen. Projizierte
Verfügbarkeit berücksichtigt zusätzlich eingehende und ausgehende Zusagen. Diese Zahlen beantworten
unterschiedliche Fragen; verfügbarer Bestand allein ist keine Versandfreigabe.

### Undurchsichtige ID

Eine Systemidentität ohne fachliche Bedeutung, mit der der exakte Datensatz angesprochen und
verknüpft wird. Auftragsnummer oder SKU sind für die menschliche Suche nützlich, aber keine
Datensatzidentität. Löse eine Nummer vor einer Operation zur tatsächlichen ID auf, damit ähnliche
Nummern oder andere Unternehmen nicht verwechselt werden.

### Kürzeste echte Verknüpfungen

Beziehungen zeigen direkt auf den Datensatz, dem ihre Bedeutung gehört. Eine Reservierung verweist
auf ihre Zusage; vorhandene Evidence ist über diese Zusage erreichbar. Der Verzicht auf doppelte
indirekte Links vermeidet konkurrierende Beziehungen und hält Erklärungen konsistent.

### Stammdaten: Geschäftspartner, Artikel und Lagerort

Geschäftspartner identifizieren Parteien wie Kunden, Lieferanten und das eigene Unternehmen. Artikel
bestimmen, was gehandelt wird; Lagerorte bestimmen, wo Bestand liegt oder bewegt wird. Operative
Datensätze verweisen auf ihre undurchsichtigen IDs. Namen, SKUs und Adressen helfen beim Finden und
Verstehen, ersetzen aber nicht die Identität.

### Hold

Eine ausdrückliche Einschränkung einer Operation, etwa eine Liefersperre an einer Zusage oder einem
Geschäftspartner. Sie verhindert den betroffenen Versand auch bei verfügbarem Bestand. Ein Hold
unterscheidet sich von einer Exception: Die Exception meldet einen Zustand; eine Sperre setzen oder
aufheben ist eine berechtigte Geschäftsänderung.
[Liefersperren](/de/agent-playbooks/order-to-cash-fulfilment).

### Zahlungszuordnung

Die Zuordnung eines eingegangenen oder gezahlten Betrags zu einer bestimmten Rechnung oder
finanziellen Verpflichtung. Geld erfassen und zuordnen beantworten unterschiedliche Fragen: Was ist
geflossen, und welchen offenen Posten gleicht es aus? Ein Mehrbetrag kann unzugeordnet bleiben; er
darf nicht stillschweigend eine andere Rechnung ausgleichen.
[Forderungen und Zahlungen](/de/agent-playbooks/receivables-and-payments).

## Commands, Berechnungen und Agenten

### Command

Eine definierte Anwendungsoperation mit Eingaben, Ergebnissen und fachlichem Zweck. Ein Command kann
lesen, etwa eine Kreditbelastung, oder ändern, etwa Bestand reservieren; der Name bedeutet nicht
automatisch einen Schreibvorgang. Sein gemeinsamer Service besitzt die Geschäftsregel, seine
Änderungsgrenze bestimmt die Bestätigung. [Commands entwickeln](/de/development/commands).

### Application Tool

Die gemeinsam aufrufbare Anwendungsfunktion, die einen Service mit stabilen Eingaben und Ergebnissen
zugänglich macht. Web, Chat, MCP, API und CLI verwenden diese Grenze gemeinsam. Das
Reservierungstool ruft zum Beispiel den Reservierungsservice auf; jede Schnittstelle darf keine
eigenen Bestandsregeln implementieren.

### Agent Tool

Eine für Agenten zugängliche Funktion mit auffindbarem Namen und Eingabeschema. Sie übersetzt
Agenteneingaben in bestehende Application Tools oder Reader. Bestand lesen und einen
Änderungsvorschlag vorbereiten sind unterschiedliche Funktionen; die Agentenschnittstelle umgeht
weder Mandantengrenze noch Berechtigungen oder Bestätigung.
[Agentenschnittstellen](/de/development/agent-tools).

### View

Eine fachliche Lesesicht, die Datensätze oder berechnete Antworten zeigt, etwa eine Auftragsliste
oder Lagerwarteschlange. Eine View kann ein Register oder eine Projection wiederverwenden; eine neue
Seite braucht nicht automatisch eine neue Berechnung. Sie bietet Filter und einen Weg zu den
zugrunde liegenden Datensätzen. [Views erkunden](/de/tool-usage/views).

### Projection

Ein wiederverwendbares Lesemodell, das aus maßgeblichen Reality-Datensätzen abgeleitet wird, etwa
physischer, reservierter und verfügbarer Bestand. Es kann beim Lesen berechnet oder als
wiederaufbaubarer Cache materialisiert werden. Es ist keine zweite Wahrheit. Eine View zeigt eine
Antwort; eine Projection liefert die abgeleiteten Daten dafür.
[Projections erkunden](/de/tool-usage/views).

### Register

Eine Leseschnittstelle für eine definierte Menge von Datensätzen mit Filtern und eindeutiger
Seitennavigation. Ein Register zeigt zum Beispiel einzelne Bewegungen statt nur einen Bestandswert.
Grunddatensätze auflisten und eine Summe berechnen sind unterschiedliche Aufgaben, auch wenn beide
in Views erscheinen.

### Exception

Ein abgeleiteter Geschäftszustand mit Handlungsbedarf, etwa eine gefährdete ausgehende Zusage.
Gemeint ist ein operativer Hinweis, kein Programmierfehler und kein manuell geschlossenes Ticket. Er
erscheint, solange seine definierte Bedingung erfüllt ist, und verschwindet, wenn die Ursache
entfällt; geändert wird die Geschäftslage über normale Commands.
[Exceptions erkunden](/de/tool-usage/exceptions).

### Business Event

Ein erfasstes Ereignis, das eine Geschäftsänderung beschreibt, etwa eine angelegte Reservierung.
Events liefern Historie und können abgeleitete Lesemodelle als veraltet markieren. Sie beschreiben
eine eingetretene Wirkung; sie sind weder ein Command, der eine Wirkung anfordert, noch eine
aktuelle Exception, die ein Risiko anzeigt. [Events erkunden](/de/tool-usage/events).

### Katalog

Eine strukturierte Beschreibung verfügbarer Commands, Views, Projections, Exceptions oder Events.
Kataloge dokumentieren ausführbare Begriffe und ermöglichen Auffindbarkeit sowie die interaktive
Referenz. Ein Eintrag erzeugt keinen Geschäftszustand und beweist nicht, dass eine externe
Integration verbunden und aktiv ist. [Katalog durchsuchen](/de/tool-usage/).

### Änderungsvorschlag und Bestätigung

Ein Vorschlag bereitet eine konkrete Operation mit ihren Argumenten und einer serverseitigen
Vorschau zur Prüfung vor. Seine Erstellung führt die Geschäftsänderung nicht aus. Der berechtigte
Mensch prüft die beabsichtigte Wirkung und bestätigt getrennt; danach werden die Datensätze erneut
gelesen, um das Ergebnis zu kontrollieren.
[Die erste Aktion vorbereiten](/de/getting-started/first-action).

### MCP, API und CLI

Unterschiedliche Schnittstellen zu gemeinsamen Funktionen. MCP (Model Context Protocol) macht Tools
für verbundene Agenten zugänglich; eine API bedient programmatische Anfragen; eine CLI bietet
Operationen im Terminal. Sie übersetzen Eingaben und Antworten, während Geschäftsregeln in
gemeinsamen Services bleiben. [Einen Agenten verbinden](/de/getting-started/connect-agent).

### Service und Adapter

Ein Service besitzt eine fachliche Anwendungsregel und ihre mandantenbezogene Ausführung. Ein
Adapter übersetzt eine Schnittstelle, etwa eine HTTP- oder MCP-Anfrage, in diese gemeinsame
Funktion. Eine neue Schnittstelle verwendet dieselbe Regel; sie schafft keine zweite Umsetzung der
Reservierungs- oder Zahlungslogik. [Anwendungsschnittstellen](/de/development/application-surfaces).

### Scheduled Job

Eine Aufgabe mit ausdrücklich eingerichteter wiederkehrender oder eingereihter Ausführung. Ein
Prompt über tägliche Arbeit plant noch keinen Agentenlauf. Hintergrundarbeit nutzt gemeinsame
Scheduling-Services und Handler, die Mandantengrenzen und Freigaberegeln erhalten; Quelleingang
autorisiert keine nachgelagerten Änderungen.
[Einen Arbeitsrhythmus definieren](/de/agent-playbooks/operating-rhythm).

## Analytics-Begriffe

### Analytics

Der Analyseeditor und die Agentenfunktionen zum Abfragen des Business Graph über vorhandenen
Reality-Datensätzen. Abfragen nutzen deklarierte Beziehungen, Kennzahlen sowie gemeinsame Bestands-
oder Finanzberechnungen. Eine Analyse kann nur die tatsächlich vorhandenen Daten und unterstützten
Beobachtungsarten erklären. [Analytics-Anleitung](/de/analytics/).

### Node und Edge

Ein Node beschreibt, was ein Datensatz repräsentiert, etwa einen Auftrag oder Artikel. Eine Edge
beschreibt eine echte Beziehung, etwa die Positionen eines Auftrags. Der Analytics-Graph beschreibt
vorhandene Datensätze und Beziehungen in PostgreSQL; er benötigt keine separate Graphdatenbank.

### Grain

Die fachliche Ebene einer Ergebniszeile: ein Auftrag, eine Auftragsposition oder ein
Artikel-Lagerort-Paar. Die Verknüpfung eines Auftrags mit vier Positionen kann seinen Betrag viermal
wiederholen. Der deklarierte Grain verhindert, diese Wiederholungen als vier eigene Aufträge zu
behandeln und falsch zu summieren.

### Measure

Eine deklarierte Kennzahl mit festgelegter fachlicher Bedeutung und Aggregationsregeln. Übernommener
Auftragswert wird zum Beispiel nach Währung getrennt und ist kein realisierter Umsatz. Mengen
behalten ihre Einheiten; nicht sicher kombinierbare Werte werden nicht stillschweigend addiert.

### Coverage

Die Beobachtungsart, die eine Abfrage unterstützt: aktueller Zustand, Aktivität in einem Zeitraum
oder ein unterstützter datierter Snapshot. Aktueller Bestand belegt nicht den historischen Bestand
jedes vergangenen Monats. Coverage macht diese Grenzen sichtbar, damit Antwort, Frage und verfügbare
Datensätze zusammenpassen.
