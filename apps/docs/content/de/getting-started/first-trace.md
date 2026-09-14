# Verfolge dein erstes Ergebnis zurück

Ein brauchbares Ergebnis ist nicht nur sichtbar, es ist erklärbar. Beginne bei einer operativen
Antwort und arbeite dich über die kürzesten echten Verknüpfungen zurück.

## 1. Mit einer operativen Frage beginnen

Wähle ein Commitment, eine Reservation, ein Movement, einen Fact oder einen LedgerEntry, der die
heutige Arbeit betrifft. Frag:

- Was braucht Aufmerksamkeit?
- Wie ist die aktuelle operative oder finanzielle Position?
- Was hat sich geändert?
- Welche Aktion steht zur Verfügung?

## 2. Den Reality-Datensatz prüfen

Öffne „Prüfen“ aus der Seite, der Tabelle, einem Aktivitätseintrag oder einer Antwort von Ask
Reality. Kontrolliere Mandant, Geschäftszeitpunkt, Menge oder Betrag, Typ, Status und die direkten
Beziehungen.

Beim [Lampenbeispiel](./index) bleiben von 10 zugesagten Lampen nach 4 versendeten noch 6 offen; 2
davon sind reserviert. Prüfe die Zahlung getrennt: LedgerEntry hält die Buchung fest,
SettlementAllocation ordnet die Zahlung der Rechnung zu. Bezahlt heißt noch nicht geliefert.

## 3. Der Evidence folgen

Wenn ein Document oder eine DocumentLine den Datensatz stützt, prüfe sie als Evidence – nicht als
Eigentümer von Fulfilment-, Reservierungs-, Bestands- oder Zahlungsstatus. Die Evidence soll
erklären, was Reality beobachtet hat, ohne selbst zu einer konkurrierenden operativen
Zustandsmaschine zu werden.

## 4. Die Quelle erreichen

Öffne den SourceRecord und seine ursprüngliche Payload. Die Payload ist unveränderlich und
verlustfrei. Ein geänderter Datensatz im Vorsystem erzeugt eine weitere Version oder ein weiteres
Ereignis, statt Geschichte zu überschreiben.

Nicht jeder manuell angelegte Reality-Datensatz hat eine externe Quelle. Prüfe die tatsächliche
Herkunft. Eine neue Quellversion beweist nicht, dass die zugehörige Reality bereits aktualisiert
ist.

## 5. Das Ergebnis erklären

Jetzt solltest du die Antwort benennen können, dazu den Reality-Datensatz, dem sie gehört, die
Evidence, die sie stützt, und die Quell-Payload, aus der sie stammt. Fehlt ein erwarteter Beleg,
prüfe die Ursache – die Lücke darf nicht durch eine Annahme gefüllt werden.

> **Normative Invariante:** Auftrags-, Rechnungs-, Lieferungs- und Zahlungsnummern für Menschen
> helfen bei der Suche. Sie sind niemals Identität; Identität und Beziehungen tragen undurchsichtige
> IDs und mandantenbezogene Fremdschlüssel.
