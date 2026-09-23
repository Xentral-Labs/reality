# Facts und offene Fragen

[Zurück zur Handbuchübersicht](../business-reality-guide)

## „Dafür hätte ich im ERP ein Zusatzfeld angelegt“ {#facts}

Northstar ergänzt seinen Auftrag: „Bitte nur vormittags liefern, Seiteneingang benutzen.“ Der
Auftrag über 30 Lampen bleibt gleich. Bestand und Forderung ändern sich ebenfalls nicht. Trotzdem
soll die Lieferanweisung bei der Bearbeitung sichtbar und ihre Herkunft nachvollziehbar sein.

Im ERP würdest du vielleicht ein Zusatzfeld oder einen Hinweis an der Auftragsposition vorsehen. In
Reality prüfst du zuerst, welche Art von Information vorliegt. Brauchst du eine zusätzliche belegte
Beobachtung, einen bestehenden operativen Vorgang oder nur die ursprüngliche Eingabe?

Ein **Fact** hält eine unterstützte, durch eine Quelle belegte Beobachtung zu einem bestehenden
Geschäftsdatensatz fest. Hier beschreibt er Northstars Lieferzusage: Die Quelle nennt eine
Lieferanweisung. Er verschiebt keinen Liefertermin, reserviert keine Ware und erteilt keine
Ausführungsberechtigung.

### Eine Beobachtung hat eine feste Bedeutung

Damit alle Aufrufer dasselbe verstehen, besitzt jede unterstützte Beobachtung eine festgelegte
Bedeutung. Dieser Vertrag heißt **Predicate**. Er legt fest, was die Beobachtung aussagt, welchen
Datensatz sie beschreiben darf und welche Werte erlaubt sind.

Für Northstars Hinweis gibt es `order.delivery_instruction`: eine Lieferanweisung als Text am
Commitment. Der technische Name hilft beim Nachschlagen. Für das Verständnis genügt zunächst: **Wer
hat welche Information über welche Lieferzusage mitgeteilt?**

„Northstar hat das so geschrieben“ ist die belegte Aussage. Ob der Fahrer tatsächlich vormittags
kommt, ist damit nicht belegt. Auch eine notierte Zahlungszusage ist noch kein Geldeingang.

### Fact, operativer Datensatz oder ursprüngliche Quelle?

| Information im Alltag                         | Passender Ort                                                                        | Fachliche Wirkung                                                       |
| --------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| Northstar nennt eine Lieferanweisung          | Fact an der Lieferzusage                                                             | Zusätzlicher belegter Kontext                                           |
| Acme sagt einen anderen Liefertermin zu       | Terminänderung (`CommitmentRevision`) an der bestehenden Lieferzusage (`Commitment`) | Der gültige Termin ergibt sich aus der zuletzt erfassten Terminänderung |
| Zehn Lampen werden Northstar zugeordnet       | Reservation                                                                          | Ware wird für die Zusage gebunden                                       |
| Lampen verlassen tatsächlich das Lager        | Movement                                                                             | Der erfasste Bestand und gegebenenfalls die Erfüllung ändern sich       |
| Eine Zahlung wird gebucht                     | LedgerEntry                                                                          | Finanzielle Buchung                                                     |
| Ein externes Feld wird derzeit nicht benötigt | Original-SourceRecord                                                                | Eingabe bleibt erhalten, ohne zusätzliches Feld                         |

**Wo erfasst du einen neuen Liefertermin?** Über die Aktion
[Verpflichtung ändern (`revise_commitment`)](../../tool-usage/#command:revise_commitment) für die
bestehende, noch offene Lieferzusage. Du gibst die Zusage und den neu genannten Termin (`due_at`)
an. Reality speichert dazu einen eigenen `CommitmentRevision`-Eintrag; der ursprüngliche Termin am
Commitment bleibt erhalten. Die aktuelle Sicht verwendet den zuletzt genannten Termin. Ein Agent
bereitet diese Änderung mit `commitment_revise_propose` zur Freigabe vor. Es entsteht kein
zusätzlicher Fact und der Auftragsbeleg wird dafür nicht umgeschrieben.

Normale Kommandos für Commitment, Reservation, Movement und Ledger erzeugen **keine** Spiegel-Facts.
Ein weiterer Fact „zehn reserviert“ würde den bereits vorhandenen Zuordnungszustand doppeln. Ein
**Business Event** meldet dagegen eine ausgeführte Änderung; es ersetzt nicht deren Einträge.

## Wie die Zusatzinformation ins System kommt {#how-facts-arise}

Für jeden Fact braucht Reality einen vorhandenen Bezugsdatensatz und eine gespeicherte Quelle. Die
Quelle heißt **SourceRecord**; das beschriebene Objekt wird technisch **Subjekt** genannt.

1. **Die Quelle ist schon vorhanden.** Hat eine unterstützte Anbindung Northstars Hinweis
   übernommen, wählst du diese Quelle und das passende Commitment. Die Web-Aktion
   **Quellengestützten Fakt erfassen** nutzt ein registriertes Predicate. Ein Agent bereitet
   denselben Vorgang mit `fact_observe_propose` vor; die Änderung braucht eine berechtigte Freigabe.
2. **Die Information kommt per Telefon, Mail oder Papier.** Zuerst wird die Aussage als manuelle
   Quelle gespeichert, mit Inhalt und nachvollziehbarer Herkunft. Danach kann ein unterstützter Fact
   daran anknüpfen. Ohne gespeicherte Quelle gibt es keinen Fact.
3. **Die Information kommt regelmäßig in Quelldaten vor.** Ein Inhaber kann über Offene Fragen eine
   begrenzte Fact-Regel vorbereiten, prüfen und aktivieren. Sie übernimmt künftig die unterstützte
   Beobachtung aus passenden Quellen. Die Regel und ihre Version bleiben nachvollziehbar.

Die ersten beiden Wege nutzen den registrierten Predicate-Katalog. Eine konfigurierte Fact-Regel hat
ihren eigenen geprüften Vertrag und unterstützte Zielobjekte. Sie darf nicht beliebige Beobachtungen
erfinden oder beliebigen Code ausführen. Beide Wege schreiben nachvollziehbare Facts; ihre
Konfiguration und Freigabe sind unterschiedlich.

## Reality fehlt etwas Wichtiges {#missing-information}

Nehmen wir an, du möchtest wissen: „Welche offenen Aufträge enthalten besondere Lieferanweisungen?“
Die Information kommt in Quellen vor, ist aber noch nicht so nutzbar, wie du sie brauchst. Das ist
eine **offene Frage**: eine Lücke zwischen deinem Arbeitsbedarf und dem, was das Modell bereits
beantwortet. Sie ist kein operativer Klärfall und keine festgestellte Beobachtung.

Halte unter **Open questions** die Frage, ihre Bedeutung im Betrieb und passende Quellbeispiele
fest. Mitglieder können Fragen erfassen; der Unternehmensinhaber steuert Einordnung und Regeln. Die
erste Entscheidung lautet, wo die benötigte Information hingehört:

| Was fehlt?                                                    | Passender Weg                                                                 |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Eine belegte Zusatzinformation zu einem vorhandenen Datensatz | Unterstützter Fact oder geprüfte Fact-Regel                                   |
| Eine wiederkehrende Berechnung oder Arbeitsliste              | View oder Projection; neue Ableitung über Entwicklung                         |
| Eine neue operative Warnbedingung                             | Geprüfte Exception-Klasse über Entwicklung                                    |
| Eine neue Geschäftswirkung oder ein neuer operativer Zustand  | Anwendungsoperation beziehungsweise Domänenmodell mit Spezifikation und Tests |
| Nur die Aufbewahrung eines bislang ungenutzten Quellfelds     | Bereits im Original-SourceRecord möglich                                      |

Ein Fact ist also kein universeller Ersatz für ERP-Zusatzfelder. Wenn das Kernverhalten wiederholt
mit einer Bedeutung rechnet, filtert, verknüpft oder darauf handelt, muss ihr Platz im typisierten
Modell geprüft werden. Ein neues Feld entsteht aus einem belegten Anwendungsfall, nicht allein aus
seiner Verfügbarkeit in einem Vorsystem.

### Regeln für Inhaber sind ein eigener Zugangsweg

Für eine unterstützte Fact-Regel gehst du schrittweise vor:

1. **Vorbereiten:** Wähle Quelle, Bedeutung und ein unterstütztes vorhandenes Ziel, etwa ein
   Commitment oder eine DocumentLine. Uninterpretierte Quellen liefern das Ziel nicht von selbst.
2. **Simulieren:** Prüfe an typischen Quellen, welche Beobachtungen entstehen würden. Fehlende
   Werte, fehlende Ziele und Konflikte gehören in diese Prüfung. Fehlend bedeutet nicht automatisch
   „nein“.
3. **Aktivieren:** Die geprüfte Regel darf für künftige Auswertungen verwendet werden. Das
   verarbeitet keine alten Quellen stillschweigend mit.
4. **Nachverarbeiten:** Ein eigener Replay kann ältere Quellen in begrenzten Schritten auswerten.
   Prüfe die Ergebnisse. Wiederholte Verarbeitung soll keine doppelten Beobachtungen anlegen.
5. **Bei Bedarf deaktivieren:** Künftige Auswertungen enden; bereits erfasste Facts werden nicht
   gelöscht.

Jeder regelbasierte Fact behält Quelle, Bezugsobjekt und Regelversion. Die Regel selbst reserviert
keinen Bestand, ändert keine Fälligkeit, führt keine Zahlung aus und definiert keine eigene
Exception-Klasse. Eine Zusatzinformation kann einen begründeten Vorschlag unterstützen. Die
operative Wirkung braucht weiterhin ihren normalen kontrollierten Vorgang.

## Was heute unterstützt wird

Die folgenden sieben Bedeutungen sind für die direkte Erfassung registriert. Das ist der aktuelle
Produktumfang, kein frei erweiterbarer Laufzeitkatalog. Regeln aus Offenen Fragen nutzen den oben
beschriebenen separaten Weg.

### Registrierte Predicates {#registered-predicates}

Das Vokabular ist absichtlich klein und wächst durch Prüfung, nie durch ein Gespräch.

| Predicate                      | Subjekt       | Wert                      | Typische Aussage                                 |
| ------------------------------ | ------------- | ------------------------- | ------------------------------------------------ |
| `order.shipping_priority`      | Commitment    | `standard` oder `express` | Die Auftragsquelle nennt eine Versandpriorität   |
| `order.delivery_instruction`   | Commitment    | Text                      | „Nur vormittags liefern, Seiteneingang benutzen“ |
| `order.customer_reference`     | Beleg         | Text                      | Die eigene Bestellnummer des Kunden              |
| `invoice.payment_promise_date` | Beleg         | Kalendertag               | „Wir zahlen RE-1042 bis 30. September“           |
| `invoice_line.dispute_reason`  | Belegposition | Text                      | „Der Preis weicht vom Angebot ab“                |
| `lot.quality_release`          | Charge        | `released` oder `blocked` | Der Prüfbericht gibt Charge 4711 frei            |
| `movement.damage_report`       | Movement      | Text                      | „Zwei Kartons kamen zerdrückt an“                |

Eine neue Art von Beobachtung braucht ein neues Predicate, das mit Tests in den Katalog kommt; siehe
[Ein weiteres Predicate ergänzen](#ein-weiteres-predicate-erganzen). Eine Regel bringt ihren Vertrag
selbst mit und braucht keinen Katalogeintrag.

### Prüfe dein Verständnis

Northstar sagt am Telefon, die offenen 870 EUR nächste Woche zu zahlen. Darf das die Rechnung
schließen?

<details>
<summary>Antwort anzeigen</summary>

Nein. Die Aussage kann zuerst als manuelle Quelle und danach als unterstützte Zahlungszusage an
`INV-1001` festgehalten werden. Der offene Betrag bleibt 870 EUR. Erst tatsächlich erfasste und
angerechnete Zahlungen oder andere passende Ausgleiche verändern ihn.

</details>

<details>
<summary>Technische Vertiefung: vollständiges Beispiel, Prüfung und Predicate-Erweiterung</summary>

Das folgende Integrationsbeispiel ist eine eigene Variante. Shopify steht hier für einen Shop, der
strukturierte Auftragsdaten liefert; JSON ist deren Austauschformat. Du brauchst diesen Abschnitt
nur, wenn du die Herkunft und den Werkzeugaufruf bis auf Feldebene nachvollziehen möchtest.

Jeder neue Fact braucht Quelle und Bezugsobjekt desselben Unternehmens, interne IDs, ein geprüftes
Predicate, den passenden Wert, einen Beobachtungszeitpunkt und eine Wiederholungsidentität. Agenten
schreiben niemals direkt in die Fact-Tabelle.

### Vollständiges Beispiel: Versandpriorität

Angenommen, Shopify hat dieses Auftragsfragment gesendet:

```json
{
  "id": "ORDER-42",
  "shipping_priority": "express",
  "customer_note": "Use the loading dock"
}
```

Reality bewahrt zuerst die vollständige Payload unverändert:

```text
SourceRecord src_7f...
source_system: shopify
source_type: order
external_id: ORDER-42
payload: vollständiges Original-JSON
```

Nachdem ein Auftragsinterpreter das zugehörige Commitment erzeugt hat, kann ein Agent oder ein
deterministischer Interpreter diese Beobachtung vorschlagen:

```json
{
  "source_record_id": "src_7f...",
  "subject_type": "commitment",
  "subject_id": "com_91...",
  "predicate": "order.shipping_priority",
  "value": "express",
  "observed_at": "2026-09-02T14:06:00Z",
  "idempotency_key": "shopify:ORDER-42:v1:shipping-priority"
}
```

Der aktuelle Predicate-Contract erlaubt nur ein Commitment als Subjekt und die Werte `standard` oder
`express`. Ein unbekanntes Predicate, eine Quelle oder ein Subjekt eines anderen Unternehmens oder
ein Wert wie `overnight` wird abgewiesen.

### Wie Agenten einen Fact sicher erzeugen

Chat und externe MCP-Agenten nutzen `fact_observe_propose`. Der Aufruf erzeugt einen
`ChangeProposal`, keinen Fact. Der Vorschlag zeigt Quelle, Subjekt, Predicate, Wert und
Beobachtungszeitpunkt genau so, wie sie geprüft werden können.

```text
fact_observe_propose
        ↓ noch keine Änderung an Reality
ChangeProposal(status=proposed)
        ↓ ausdrückliche Bestätigung durch einen Menschen
fact_observe
        ↓ eine Transaktion
Fact + fact.observed
```

Die bestätigte Anwendungsoperation prüft für jeden Aufrufer dieselben Regeln. Eine wiederholte
Anfrage mit demselben Idempotenzschlüssel und identischem Inhalt liefert den ursprünglichen Fact
zurück. Denselben Schlüssel für anderen Inhalt zu verwenden schlägt fehl, statt die erste
Beobachtung still zu verändern.

> **Aktuelles Verhalten:** Das öffentliche Vokabular für Fact-Beobachtungen umfasst die sieben
> [registrierten Predicates](#registered-predicates). Quellspezifische Extraktion und automatische
> Überführung in typisierte Reality sind nicht Teil des Fact-Kerns.

### Wie Facts genutzt werden

Facts liefern erklärbaren Kontext für Menschen, für den Betrieb und für spätere Entscheidungen. Der
Weg lässt sich verfolgen:

```text
Fact
  → Subjekt: Commitment
  → SourceRecord
  → ursprüngliche Shopify-Payload
```

Eine spätere Operation darf den Fact als Evidence nutzen, wenn sie eine typisierte Aktion
vorschlägt, aber der Übergang ist ausdrücklich. Eine Beobachtung `express` kann etwa helfen, dem
Betrieb einen früheren Fälligkeitszeitpunkt für das Commitment zu empfehlen. Der Fact selbst ändert
das Commitment nicht, reserviert keinen Bestand und autorisiert keine Wirkung.

Nutze das Register **Fakten** für die geschäftlich lesbare Liste und **Prüfen** für die interne
Identität, Predicate, Beobachtungszeitpunkt, Quelldetails, Ereignishistorie und die ursprüngliche
Payload.

### Ein weiteres Predicate ergänzen

Lass Parser oder Modelle keine Predicate-Namen zur Laufzeit erfinden. Dokumentiere vor dem Ergänzen
ein echtes Geschäftsbeispiel und beantworte:

- Welchen bestehenden Subjekttyp beschreibt es?
- Welchen kanonischen Werttyp oder welche erlaubten Werte nutzt es?
- Warum ist die Beobachtung operativ relevant?
- Warum besitzt kein bestehender typisierter Reality-Datensatz sie schon?
- Welche Quelle und welcher Abnahmetest belegen die vollständige Rückverfolgung?

Wenn die Kernlogik wiederholt mit dem Wert rechnet, danach filtert, darauf verknüpft, ihn
einschränkt, daraus Prognosen ableitet oder darauf handelt, dann überführe das Konzept über eine
eigene Spezifikation in ein passendes typisiertes Feld oder eine eigene Entität. Lass kein
unbegrenztes Fact-Vokabular als Ersatz für ein belegtes Domänenmodell wachsen.

</details>

Zum Abschluss: [Zusammenfassung](./07-model-at-a-glance) fasst die Grundbegriffe und die gemeinsame
Arbeit von Menschen, Agenten und Workflows zusammen.
