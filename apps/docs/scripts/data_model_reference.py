"""Offline storage metadata with business explanations for the docs explorer."""

from __future__ import annotations

from typing import Any

from sqlalchemy.dialects import postgresql


def bilingual(en: str, de: str) -> dict[str, str]:
    return {"en": en, "de": de}


# Reviewed meanings supplement, but never define, the storage schema.
MEANINGS: dict[str, dict[str, str]] = {}
for line in """
id|Opaque record identity, supplied by the application; never the document number.|Technische Identität, von der Anwendung vergeben; niemals die Belegnummer.
tenant_id|Company boundary, taken from the application context.|Unternehmensgrenze, aus dem Anwendungskontext übernommen.
source_record_id|Link to the original source version supporting this record.|Verweis auf die ursprüngliche Quellversion, die diesen Eintrag belegt.
created_at|When Reality created this record (UTC).|Wann Reality diesen Eintrag angelegt hat (UTC).
source_system|System that supplied the data.|System, aus dem die Daten stammen.
source_type|Kind of record in the supplying system.|Datensatzart im Quellsystem.
external_id|Identifier in the source system; not Reality identity.|Kennung im Quellsystem; nicht die Reality-Identität.
payload|Preserved source content, without discarding unused fields.|Erhaltener Quellinhalt, auch mit derzeit ungenutzten Feldern.
payload_hash|Fingerprint of canonicalized source content.|Fingerabdruck des kanonisierten Quellinhalts.
source_artifact_id|Link to an original file or binary artifact.|Verweis auf die ursprüngliche Datei oder ein Binärartefakt.
version|Version of this external record held by Reality.|Von Reality geführte Version dieses externen Datensatzes.
source_version_at|Version timestamp stated by the source, if supplied.|Versionszeitpunkt laut Quelle, sofern mitgeliefert.
supersedes_source_record_id|Previous source version replaced by this version.|Vorherige Quellversion, die durch diese Version abgelöst wird.
received_at|When Reality received this source version (UTC).|Wann Reality diese Quellversion empfangen hat (UTC).
type|Record kind interpreted by the relevant business tool; see its accepted inputs.|Datensatzart gemäß dem jeweiligen Geschäftstool; zulässige Eingaben stehen beim Tool.
number|Human-readable document number; never a foreign key.|Lesbare Belegnummer; niemals ein technischer Fremdschlüssel.
party_id|Business partner this entry concerns.|Geschäftspartner, auf den sich dieser Eintrag bezieht.
currency|Currency of the recorded amount; not an exchange rate.|Währung des erfassten Betrags; kein Wechselkurs.
gross_amount|Gross amount stated for this document or line; not recalculated from other fields.|Genannter Bruttobetrag des Belegs oder der Position; wird nicht aus anderen Feldern nachgerechnet.
status|Stored lifecycle state controlled by the responsible application tools.|Gespeicherter Lebenszyklusstatus, den die zuständigen Anwendungstools führen.
document_date|Document date as recorded from the source.|Aus der Quelle übernommenes Belegdatum.
ordered_at|When the order was placed, as stated.|Genannter Zeitpunkt der Bestellung.
requested_delivery_at|Delivery date requested on the document, not the effective operational promise.|Auf dem Beleg gewünschter Liefertermin; nicht die aktuell wirksame operative Zusage.
customer_reference|Customer reference stated on the document; not identity.|Kundenreferenz laut Beleg; keine technische Identität.
sales_channel|Sales channel stated for the document.|Für den Beleg genannter Vertriebskanal.
payment_term_id|Reference to the agreed payment terms.|Verweis auf die vereinbarten Zahlungsbedingungen.
ship_to_party_id|Business partner at the delivery address.|Geschäftspartner der Lieferadresse.
document_id|Related evidence document.|Zugehöriger Beleg als Nachweis.
source_line_id|Line identity supplied by the source within its document.|Von der Quelle gelieferte Positionskennung innerhalb des Belegs.
item_id|Reference to the item master record.|Verweis auf den Artikelstammsatz.
sku|Item code stated on the evidence line.|Auf der Belegposition genannte Artikelnummer.
description|Description stated for this line.|Für diese Position genannte Beschreibung.
quantity|Quantity recorded for this entry; see the object's business meaning.|Für diesen Eintrag erfasste Menge; ihre Bedeutung erklärt das Objekt oben.
unit_price|Unit price received for this line; no price recalculation.|Empfangener Stückpreis dieser Position; keine Preisneuberechnung.
promised_at|Promise date recorded on the evidence line; operative changes belong to CommitmentRevision.|Auf der Belegposition erfasster Zusagetermin; operative Änderungen gehören zu CommitmentRevision.
unit|Unit of measure of the stated quantity.|Maßeinheit der genannten Menge.
requested_at|Requested date stated for this line.|Für diese Position genannter Wunschtermin.
line_type|Kind of document line, such as item or service.|Art der Belegposition, etwa Artikel oder Dienstleistung.
price_list_entry_id|Price list entry associated with this agreed line.|Mit dieser vereinbarten Position verknüpfter Preislisteneintrag.
billed_document_line_id|Agreed order line that this invoice line bills, if any.|Vereinbarte Auftragsposition, die diese Rechnungsposition abrechnet, sofern vorhanden.
from_party_id|Party making the promise.|Geschäftspartner, der die Zusage macht.
to_party_id|Party receiving the promise.|Geschäftspartner, dem die Zusage gilt.
location_id|Location associated with the promise or stock allocation.|Ort, auf den sich die Zusage oder Bestandszuordnung bezieht.
amount|Amount recorded for this entry, in its currency.|Für diesen Eintrag erfasster Betrag in seiner Währung.
due_at|Date stated for the promise; see original versus revised values above.|Genannter Zusagetermin; ursprünglicher und geänderter Wert werden oben unterschieden.
document_line_id|Evidence line supporting this promise.|Belegposition, auf der diese Zusage beruht.
cancelled_at|When the promise was cancelled, if applicable.|Zeitpunkt der Stornierung der Zusage, sofern erfolgt.
priority|Operational priority of the promise.|Operative Priorität der Zusage.
commitment_id|Promise this entry belongs to; follow it to its evidence.|Zusage, zu der dieser Eintrag gehört; über sie gelangt man zum Beleg.
stated_at|When the counterparty stated the changed promise.|Wann der Geschäftspartner die geänderte Zusage genannt hat.
note|Explanation recorded with the business action.|Mit der Geschäftsaktion erfasste Erläuterung.
reserved_at|When stock was allocated to the promise (UTC).|Wann Bestand der Zusage zugeordnet wurde (UTC).
handling_unit_id|Specific handling unit, if identified.|Konkrete logistische Einheit, sofern zugeordnet.
lot_id|Specific batch or lot, if identified.|Konkrete Charge, sofern zugeordnet.
serial_unit_id|Specific serialized unit, if identified.|Konkrete Einheit mit Seriennummer, sofern zugeordnet.
from_location_id|Location the goods leave; may be absent for an external receipt.|Ort, den die Ware verlässt; kann bei externem Eingang fehlen.
to_location_id|Location the goods enter; may be absent for an external shipment.|Ort, an dem die Ware eingeht; kann bei externem Versand fehlen.
occurred_at|When the physical movement happened (UTC).|Wann die physische Warenbewegung stattgefunden hat (UTC).
shipment_package_id|Package in the physical shipment carrying these goods.|Packstück der physischen Sendung, in dem diese Ware liegt.
resolves_movement_id|Earlier return movement whose goods this movement disposes of.|Frühere Retourenbewegung, über deren Ware diese Bewegung verfügt.
return_announcement_id|Return announcement fulfilled by these arriving goods, if any.|Retourenankündigung, die mit dieser eingehenden Ware erfüllt wird, sofern vorhanden.
posting_group_id|Groups the entries of one balanced posting; not a document number.|Gruppiert die Einträge einer ausgeglichenen Buchung; keine Belegnummer.
account_id|Subledger account within this tenant; account role is read from it.|Nebenbuchkonto dieses Unternehmens; die Kontorolle wird daraus gelesen.
debit_credit|Debit or credit side of this posting entry.|Soll- oder Habenseite dieses Buchungseintrags.
effective_at|When the posting takes financial effect (UTC).|Zeitpunkt der finanziellen Wirksamkeit der Buchung (UTC).
subject_type|Kind of record the observation describes, restricted by the predicate.|Art des beschriebenen Datensatzes, durch das Prädikat eingeschränkt.
subject_id|Opaque identity of the described record; resolved together with subject_type.|Technische Identität des beschriebenen Datensatzes; wird zusammen mit subject_type aufgelöst.
predicate|Supported observation name defining the subject and value contract.|Unterstützter Beobachtungsname, der Bezug und Werteformat festlegt.
value|Predicate-validated value stored as text.|Gegen das Prädikat geprüfter Wert, als Text gespeichert.
observed_at|When the observation was made (UTC).|Wann die Beobachtung gemacht wurde (UTC).
request_fingerprint|Idempotency fingerprint preventing the same request being applied twice.|Fingerabdruck zur Idempotenz, damit dieselbe Anfrage nicht doppelt angewendet wird.
interpretation_rule_id|Rule that interpreted the observation, if applicable.|Regel, mit der die Beobachtung interpretiert wurde, sofern vorhanden.
""".strip().splitlines():
    key, en, de = line.split("|")
    MEANINGS[key] = bilingual(en, de)


def record(
    key: str,
    name: str,
    en: str,
    de: str,
    example: dict[str, Any],
    note_en: str,
    note_de: str,
    derived_en: str,
    derived_de: str,
    related: list[str],
) -> dict[str, Any]:
    return {
        "key": key,
        "name": name,
        "purpose": bilingual(en, de),
        "example": example,
        "note": bilingual(note_en, note_de),
        "derived": bilingual(derived_en, derived_de),
        "related": related,
    }


RECORDS = [
    record(
        "source_record",
        "SourceRecord",
        "What arrived from outside?",
        "Was ist von außen angekommen?",
        {
            "source_system": "erp",
            "source_type": "order",
            "external_id": "SO-1001",
            "version": 1,
            "payload": '{"number":"SO-1001","delivery_note":"Side entrance"}',
        },
        "Original payloads stay lossless. Unused fields remain here; a new source version does not erase the old one.",
        "Originalinhalte bleiben verlustfrei erhalten. Ungenutzte Felder bleiben hier; eine neue Quellversion löscht die alte nicht.",
        "A source record alone is neither available stock nor an accepted promise. Interpretation creates evidence and supported Reality records.",
        "Ein Quelldatensatz allein ist weder verfügbarer Bestand noch eine angenommene Zusage. Die Interpretation erzeugt Belege und unterstützte Reality-Einträge.",
        ["document", "fact"],
    ),
    record(
        "document",
        "Document",
        "What does the business document state?",
        "Was steht auf dem Geschäftsbeleg?",
        {
            "type": "sales_order",
            "number": "SO-1001",
            "currency": "EUR",
            "gross_amount": "1470.0000",
        },
        "The order from Northstar is evidence. Its status is a document lifecycle state, never the delivery, reservation or payment balance.",
        "Northstars Auftrag ist ein Beleg. Sein Status beschreibt den Beleglebenszyklus, niemals Lieferstand, Reservierung oder Zahlungssaldo.",
        "Delivered, reserved and paid are read through commitments, movements, postings and allocations. They are not document fields.",
        "Geliefert, reserviert und bezahlt wird über Zusagen, Bewegungen, Buchungen und Zuordnungen gelesen. Das sind keine Belegfelder.",
        ["source_record", "document_line", "commitment", "ledger_entry"],
    ),
    record(
        "document_line",
        "DocumentLine",
        "What was stated for one line?",
        "Was wurde für eine Position genannt?",
        {
            "sku": "ITEM-004",
            "description": "Cedar Desk Lamp",
            "quantity": "30.0000",
            "unit": "pcs",
        },
        "Thirty lamps are the line's received quantity. A later shipment does not rewrite it. Invoice lines can link to the agreed line through billed_document_line_id.",
        "30 Lampen sind die empfangene Positionsmenge. Eine spätere Lieferung schreibt sie nicht um. Rechnungspositionen können über billed_document_line_id auf die vereinbarte Position zeigen.",
        "Fulfilled and remaining quantities come from operational records; source-stated prices and totals are preserved rather than recomputed.",
        "Erfüllte und offene Mengen entstehen aus operativen Einträgen; genannte Preise und Summen bleiben erhalten und werden nicht nachgerechnet.",
        ["document", "commitment"],
    ),
    record(
        "commitment",
        "Commitment",
        "What have we promised, and to whom?",
        "Was haben wir wem zugesagt?",
        {
            "type": "customer_delivery",
            "quantity": "30.0000",
            "due_at": "2026-09-18T12:00:00Z",
            "status": "open",
        },
        "The promise to Northstar starts with 30 lamps and an original date. Use revise_commitment for a newly stated date or quantity; original fields remain. Tools also control lifecycle state.",
        "Die Zusage an Northstar beginnt mit 30 Lampen und einem ursprünglichen Termin. Einen neu genannten Termin oder eine Menge erfasst revise_commitment; die ursprünglichen Felder bleiben. Tools führen auch den Lebenszyklusstatus.",
        "Effective date and quantity use the latest revision stating each value, otherwise the original. Open quantity uses effective quantity and net fulfilment. Reserved stock belongs to Reservation; execution belongs to Movement.",
        "Wirksamer Termin und wirksame Menge kommen jeweils aus der letzten Revision, die diesen Wert nennt, sonst aus der ursprünglichen Zusage. Die offene Menge berücksichtigt wirksame Menge und Nettoerfüllung. Reservierter Bestand gehört zu Reservation, Ausführung zu Movement.",
        ["document_line", "commitment_revision", "reservation", "movement", "fact"],
    ),
    record(
        "commitment_revision",
        "CommitmentRevision",
        "What did the partner change about the promise?",
        "Was hat der Partner an der Zusage geändert?",
        {"due_at": "2026-09-21T12:00:00Z", "note": "Northstar agreed a later delivery"},
        "revise_commitment adds the newly stated date, quantity or both. At least one is needed even though both storage columns allow null. It can also update the promise's lifecycle state.",
        "revise_commitment ergänzt den neu genannten Termin, die Menge oder beides. Mindestens eines ist erforderlich, obwohl beide Datenbankfelder leer sein dürfen. Die Aktion kann auch den Lebenszyklusstatus der Zusage ändern.",
        "This record is one statement. The effective promise is read across its original record and revisions; it is not another copied fact.",
        "Dieser Eintrag ist eine einzelne Aussage. Die wirksame Zusage wird aus Ursprung und Revisionen gelesen; sie wird nicht als zusätzlicher Fact kopiert.",
        ["commitment", "source_record"],
    ),
    record(
        "reservation",
        "Reservation",
        "Which stock is bound to which promise?",
        "Welcher Bestand ist an welche Zusage gebunden?",
        {"quantity": "8.0000", "status": "active"},
        "Eight available lamps are allocated to Northstar's promise. The shortest evidence path is Reservation → Commitment → DocumentLine. Releasing a reservation changes its status through a tool.",
        "Acht vorhandene Lampen werden Northstars Zusage zugeordnet. Der kürzeste Nachweisweg ist Reservation → Commitment → DocumentLine. Freigeben ändert den Reservierungsstatus über ein Tool.",
        "A reservation does not move goods. Reserved and available totals are derived from active allocations and stock movements.",
        "Eine Reservierung bewegt keine Ware. Reservierte und verfügbare Gesamtmengen werden aus aktiven Zuordnungen und Warenbewegungen abgeleitet.",
        ["commitment", "movement"],
    ),
    record(
        "movement",
        "Movement",
        "What physically happened to the goods?",
        "Was ist mit der Ware tatsächlich passiert?",
        {
            "type": "shipment",
            "quantity": "18.0000",
            "occurred_at": "2026-09-18T12:00:00Z",
        },
        "Eighteen lamps left the warehouse for Northstar. Corrections use correct_movement with correction evidence, not an untracked overwrite. Returns have their own meaning; they do not simply reopen a kept promise.",
        "18 Lampen haben das Lager für Northstar verlassen. Korrekturen erfolgen mit correct_movement und Korrekturbeleg, ohne unprotokolliertes Überschreiben. Retouren haben eine eigene Bedeutung; sie öffnen eine erfüllte Zusage nicht einfach wieder.",
        "Stock comes from movements. Fulfilment comes from the relevant movements net of corrections. Neither needs a duplicate 'shipped' Fact.",
        "Bestand entsteht aus Bewegungen. Erfüllung entsteht aus den relevanten Bewegungen unter Berücksichtigung von Korrekturen. Dafür braucht es keinen doppelten Fact „geliefert“.",
        ["commitment", "source_record"],
    ),
    record(
        "ledger_entry",
        "LedgerEntry",
        "What was financially posted?",
        "Was wurde finanziell gebucht?",
        {"amount": "500.0000", "currency": "EUR", "debit_credit": "debit"},
        "A received payment creates balanced entries in a posting group. This excerpt is only one side. SettlementAllocation connects a payment to an invoice; corrections use reversal tools.",
        "Eine eingegangene Zahlung erzeugt ausgeglichene Einträge einer Buchungsgruppe. Dieser Ausschnitt zeigt nur eine Seite. SettlementAllocation verbindet Zahlung und Rechnung; Korrekturen erfolgen über Stornotools.",
        "Balances and open items are derived from postings and allocations. The account role is read from account_id, not stored again as an account field.",
        "Salden und offene Posten entstehen aus Buchungen und Zuordnungen. Die Kontorolle wird über account_id gelesen und nicht nochmals als Feld account gespeichert.",
        ["document", "source_record"],
    ),
    record(
        "fact",
        "Fact",
        "What additional supported observation do we hold?",
        "Welche zusätzliche unterstützte Beobachtung liegt vor?",
        {
            "subject_type": "commitment",
            "predicate": "order.delivery_instruction",
            "value": "Side entrance",
        },
        "Use supported predicates and their value contracts. Northstar's delivery instruction adds context; a changed operational date belongs to a commitment revision. Not every extra ERP field automatically becomes a Fact.",
        "Verwende unterstützte Prädikate und deren Werteformat. Northstars Lieferanweisung ergänzt Kontext; ein geänderter operativer Termin gehört in eine Zusagenrevision. Nicht jedes zusätzliche ERP-Feld wird automatisch ein Fact.",
        "subject_type and subject_id jointly identify the observed record; this is a validated business link, not a database foreign key. Facts do not duplicate reserved quantities, deliveries or payments.",
        "subject_type und subject_id bestimmen gemeinsam den beschriebenen Datensatz; das ist ein fachlich geprüfter Bezug, kein Datenbank-Fremdschlüssel. Facts duplizieren keine Reservierungsmengen, Lieferungen oder Zahlungen.",
        ["commitment", "document", "document_line", "movement", "source_record"],
    ),
]

OVERRIDES = {
    ("document_line", "payload"): bilingual(
        "Original line payload when captured by the interpreter; may be empty. The complete source remains in SourceRecord.",
        "Ursprünglicher Positionsinhalt, sofern vom Interpreter erfasst; kann leer sein. Die vollständige Quelle bleibt im SourceRecord.",
    ),
    ("ledger_entry", "tenant_id"): bilingual(
        "Company boundary. Together, tenant_id and account_id reference the subledger account; the account relationship is one composite key.",
        "Unternehmensgrenze. tenant_id und account_id verweisen gemeinsam auf das Nebenbuchkonto; dieser Kontobezug ist ein zusammengesetzter Schlüssel.",
    ),
    ("commitment", "quantity"): bilingual(
        "Original promised quantity; current and open quantities are derived separately.",
        "Ursprünglich zugesagte Menge; aktuelle und offene Mengen werden getrennt abgeleitet.",
    ),
    ("commitment", "due_at"): bilingual(
        "Original promise date; later stated dates belong to CommitmentRevision.",
        "Ursprünglicher Zusagetermin; später genannte Termine gehören zu CommitmentRevision.",
    ),
    ("commitment_revision", "quantity"): bilingual(
        "New quantity stated by the partner, if this revision changes it.",
        "Neu vom Partner genannte Menge, sofern diese Revision sie ändert.",
    ),
    ("commitment_revision", "due_at"): bilingual(
        "New date stated by the partner, if this revision changes it.",
        "Neu vom Partner genannter Termin, sofern diese Revision ihn ändert.",
    ),
    ("document", "status"): bilingual(
        "Document lifecycle only; not fulfilment or payment state.",
        "Nur der Beleglebenszyklus; kein Erfüllungs- oder Zahlungsstand.",
    ),
}


# ERP records use the same schema extraction and reviewed business annotations.
for line in """
name|Readable name of this master record.|Lesbarer Name dieses Stammdatensatzes.
code|Human-readable business code; technical links still use id.|Lesbares fachliches Kürzel; technische Verknüpfungen verwenden weiterhin id.
is_active|Whether the record can be used for new business actions; old references remain.|Ob der Datensatz für neue Geschäftsaktionen verwendet werden kann; alte Bezüge bleiben erhalten.
accounting_code|Partner code used for accounting references, not technical identity.|Partnerkennung für Buchhaltungsbezüge, keine technische Identität.
default_currency|Currency proposed from this partner's master data.|Aus den Partnerstammdaten vorgeschlagene Währung.
credit_limit|Recorded credit limit used by the application's credit checks.|Erfasstes Kreditlimit für die Kreditprüfung der Anwendung.
tax_identifier|Tax identifier stated for the business partner.|Für den Geschäftspartner genannte Steuerkennung.
role|Business role of this record; see its object-specific meaning and tool contract.|Fachliche Rolle dieses Eintrags; Bedeutung und zulässige Werte stehen beim Objekt und Tool.
default_location_id|Default location associated with this master record.|Mit diesem Stammdatensatz verknüpfter Standardort.
hold_type|Kind of business restriction, such as a delivery hold.|Art der fachlichen Sperre, etwa eine Liefersperre.
reason_code|Machine-readable reason for the restriction.|Technisches Kürzel für den Sperrgrund.
created_by|Actor label recorded when the restriction was created.|Beim Setzen der Sperre erfasste Akteursangabe.
released_at|When this restriction was released; empty while it has not been released.|Zeitpunkt der Freigabe dieser Sperre; leer, solange keine Freigabe erfolgt ist.
item_type|Whether the item represents stocked goods or a supported other item kind.|Ob der Artikel lagergeführte Ware oder eine andere unterstützte Artikelart darstellt.
tracking_type|Tracking requirement of the item, such as none, lot or serial tracking.|Verfolgungsanforderung des Artikels, etwa ohne, mit Charge oder Seriennummer.
purchase_unit|Unit used when purchasing this item.|Beim Einkauf dieses Artikels verwendete Einheit.
conversion_factor|Recorded conversion between purchasing and base units.|Erfasster Umrechnungsfaktor zwischen Einkaufs- und Basiseinheit.
lead_time_days|Lead time recorded in the item master, in days.|In den Artikelstammdaten erfasste Beschaffungszeit in Tagen.
parent_location_id|Parent in the location hierarchy, if any.|Übergeordneter Ort in der Ortshierarchie, sofern vorhanden.
allows_stock|Whether physical stock may be held at this location.|Ob an diesem Ort physischer Bestand geführt werden darf.
due_days|Agreed number of days until payment is due.|Vereinbarte Anzahl Tage bis zur Zahlungsfälligkeit.
requires_prepayment|Explicit policy requiring qualifying allocated payment before customer dispatch.|Explizite Regel, die vor dem Kundenversand eine qualifizierende zugeordnete Zahlung verlangt.
discount_percent|Stated early-payment discount percentage; empty means no such offer is recorded.|Genannter Skontosatz; leer bedeutet, dass kein solches Angebot erfasst ist.
discount_days|Stated time window for the early-payment discount, in days.|Genannte Skontofrist in Tagen.
direction|Business direction of the record; the object explains which directions apply.|Fachliche Richtung des Eintrags; das Objekt erläutert die jeweiligen Richtungen.
valid_from|Start of the recorded validity period, if bounded.|Beginn des erfassten Gültigkeitszeitraums, sofern begrenzt.
valid_until|End of the recorded validity period, if bounded.|Ende des erfassten Gültigkeitszeitraums, sofern begrenzt.
is_default|Marks a default price list within its business scope.|Kennzeichnet eine Standardpreisliste innerhalb ihres fachlichen Geltungsbereichs.
price_list_id|Price list referenced by this entry or assignment.|Preisliste, auf die dieser Eintrag oder diese Zuordnung verweist.
min_quantity|Quantity threshold at which this price tier applies.|Mengenschwelle, ab der diese Preisstaffel gilt.
group_type|Purpose of the partner group, currently used for pricing.|Zweck der Partnergruppe, derzeit für Preisfindung verwendet.
party_group_id|Partner group referenced by this membership or price assignment.|Partnergruppe dieser Mitgliedschaft oder Preiszuordnung.
nve|Stated shipping-unit number, if available; not the technical identity.|Genannte Nummer der Versandeinheit, sofern vorhanden; nicht die technische Identität.
lot_number|Batch number stated for this item.|Für diesen Artikel genannte Chargennummer.
expires_at|Best-before calendar date read from the goods; no time of day is invented.|Von der Ware abgelesenes Mindesthaltbarkeitsdatum; es wird keine Uhrzeit ergänzt.
serial_number|Serial number stated for this individual item unit.|Genannte Seriennummer dieser einzelnen Artikeleinheit.
purpose|Business purpose of the transport: delivery or return for customer or supplier.|Fachlicher Transportzweck: Lieferung oder Retoure für Kunde oder Lieferant.
counterparty_id|Business partner at the other end of the shipment.|Geschäftspartner am anderen Ende der Sendung.
shipment_id|Physical shipment this package or report belongs to.|Physische Sendung, zu der dieses Packstück oder diese Meldung gehört.
carrier|Carrier name recorded for the package, if known.|Für das Packstück erfasster Transportdienstleister, sofern bekannt.
tracking_number|Tracking number supplied for the package; not a Reality ID.|Für das Packstück gelieferte Trackingnummer; keine Reality-ID.
event_type|Reported transport event, such as handed_over, in_transit or delivered.|Gemeldetes Transportereignis, etwa handed_over, in_transit oder delivered.
reporter_type|Who reported the event: company, counterparty, carrier or integration.|Wer das Ereignis meldet: Unternehmen, Geschäftspartner, Transportdienstleister oder Integration.
recorded_at|When Reality recorded the report (UTC).|Wann Reality die Meldung erfasst hat (UTC).
location_text|Location text supplied with the report; not a stock-location reference.|Mit der Meldung gelieferte Ortsangabe; kein Verweis auf einen Bestandsort.
external_event_id|Event identifier supplied by the reporting system, if available.|Vom meldenden System gelieferte Ereigniskennung, sofern vorhanden.
superseded_event_id|Earlier transport report being withdrawn or replaced.|Frühere Transportmeldung, die zurückgezogen oder ersetzt wird.
replacement_event_id|Replacement transport report; empty for a withdrawal without replacement.|Ersatzmeldung; leer bei Rücknahme ohne Ersatz.
reason|Recorded explanation for this action.|Erfasste Begründung dieser Aktion.
actor_context|Recorded actor context for traceability, stored as JSON text.|Zur Nachvollziehbarkeit erfasster Akteurskontext als JSON-Text.
reference|Human reference stated for the return; not a generated identity.|Für die Retoure genannte lesbare Referenz; keine erzeugte Identität.
announced_at|When the return was announced (UTC).|Wann die Retoure angekündigt wurde (UTC).
expected_by|Date the customer stated the goods would go, if one was stated.|Vom Kunden genannter Termin für die Rücksendung, sofern genannt.
closed_at|When the return announcement was closed, if applicable.|Zeitpunkt des Abschlusses der Retourenankündigung, sofern erfolgt.
original_movement_id|Original movement being corrected; retained as evidence.|Ursprüngliche, zu korrigierende Bewegung; bleibt als Nachweis erhalten.
compensating_movement_id|Movement compensating the original movement's effect.|Bewegung, die die Wirkung der ursprünglichen Bewegung ausgleicht.
replacement_movement_id|Correct replacement movement, if one is needed.|Richtige Ersatzbewegung, sofern erforderlich.
corrected_at|When the correction was recorded (UTC).|Wann die Korrektur erfasst wurde (UTC).
state|Whether this account is active or blocked for new postings.|Ob dieses Konto für neue Buchungen aktiv oder gesperrt ist.
revision|Version used to detect conflicting changes.|Version zur Erkennung konkurrierender Änderungen.
original_posting_group_id|Posting group whose entries are reversed.|Buchungsgruppe, deren Einträge storniert werden.
reversing_posting_group_id|Posting group containing the inverse entries.|Buchungsgruppe mit den Gegenbuchungen.
reversed_at|When the reversal was recorded (UTC).|Wann die Stornierung erfasst wurde (UTC).
payment_ledger_entry_id|Payment-side posting entry used for the allocation.|Für die Zuordnung verwendeter zahlungsseitiger Buchungseintrag.
invoice_ledger_entry_id|Invoice-side posting entry settled by the allocation.|Rechnungsseitiger Buchungseintrag, der durch die Zuordnung ausgeglichen wird.
allocated_at|When payment and invoice entries were allocated (UTC).|Wann Zahlungs- und Rechnungseintrag einander zugeordnet wurden (UTC).
""".strip().splitlines():
    key, en, de = line.split("|")
    MEANINGS[key] = bilingual(en, de)

# One compact, bilingual definition per business responsibility. Examples are excerpts.
for key, name, en, de, example, note_en, note_de, derived_en, derived_de, related in [
    (
        "party",
        "Party",
        "Who do we do business with?",
        "Mit wem machen wir Geschäfte?",
        {"name": "Northstar", "type": "customer", "default_currency": "EUR"},
        "One partner record can hold customer and supplier roles. Addresses and commercial defaults belong to the partner; role assignments remain separate.",
        "Ein Partnerdatensatz kann Kunden- und Lieferantenrollen haben. Adress- und kaufmännische Angaben gehören zum Partner; die Rollen werden separat zugeordnet.",
        "Receivables and payables are read from postings, not stored as partner balance fields.",
        "Forderungen und Verbindlichkeiten werden aus Buchungen gelesen und nicht als Partnersaldo gespeichert.",
        [
            "party_role",
            "party_hold",
            "payment_term",
            "party_price_list",
            "party_group_member",
            "document",
        ],
    ),
    (
        "party_role",
        "PartyRole",
        "Is this partner a customer, supplier or our own company?",
        "Ist dieser Partner Kunde, Lieferant oder das eigene Unternehmen?",
        {"role": "customer"},
        "Northstar's customer role points to the existing Party. Adding a supplier role does not create a second address book.",
        "Northstars Kundenrolle verweist auf den vorhandenen Party-Datensatz. Eine zusätzliche Lieferantenrolle erzeugt kein zweites Adressbuch.",
        "A role classifies the partner; it does not establish stock, credit or open balances.",
        "Eine Rolle ordnet den Partner ein; sie begründet weder Bestand noch Kredit oder offene Salden.",
        ["party", "location"],
    ),
    (
        "party_hold",
        "PartyHold",
        "Why are deliveries to this partner restricted?",
        "Warum sind Lieferungen an diesen Partner gesperrt?",
        {"hold_type": "delivery", "note": "Clarify overdue payment"},
        "A partner delivery hold records a reason and later release. It is a business restriction, not a replacement for a recorded payment.",
        "Eine Liefersperre am Partner hält Grund und spätere Freigabe fest. Sie ist eine fachliche Einschränkung und ersetzt keine erfasste Zahlung.",
        "Whether a particular promise can proceed is read together with its other blockers.",
        "Ob eine konkrete Zusage ausgeführt werden kann, wird zusammen mit ihren weiteren Hindernissen gelesen.",
        ["party", "commitment", "commitment_hold"],
    ),
    (
        "item",
        "Item",
        "What do we buy, hold and sell?",
        "Was kaufen, lagern und verkaufen wir?",
        {
            "sku": "ITEM-004",
            "name": "Cedar Desk Lamp",
            "unit": "pcs",
            "item_type": "stocked",
        },
        "The lamp's master record holds its unit, tracking requirements and defaults. SKU is a business code; links use the opaque item ID.",
        "Der Lampenstammsatz hält Einheit, Verfolgungsanforderungen und Vorgaben fest. SKU ist eine fachliche Artikelnummer; Verknüpfungen verwenden die technische Artikel-ID.",
        "Physical stock is derived from Movement; reserved stock from Reservation. Neither is an Item field.",
        "Physischer Bestand entsteht aus Movement, reservierter Bestand aus Reservation. Beides ist kein Item-Feld.",
        [
            "location",
            "price_list_entry",
            "lot",
            "serial_unit",
            "movement",
            "reservation",
        ],
    ),
    (
        "location",
        "Location",
        "Where may goods be held or moved?",
        "Wo darf Ware liegen oder bewegt werden?",
        {"name": "Main warehouse", "type": "warehouse", "allows_stock": True},
        "Locations can form a hierarchy. The record describes the place; movements describe goods entering and leaving it.",
        "Orte können eine Hierarchie bilden. Der Datensatz beschreibt den Ort; Bewegungen beschreiben Warenzugänge und -abgänge.",
        "Stock at this location is calculated from linked movements rather than stored in Location.",
        "Bestand an diesem Ort wird aus verknüpften Bewegungen berechnet und nicht in Location gespeichert.",
        ["item", "movement", "reservation"],
    ),
    (
        "payment_term",
        "PaymentTerm",
        "Which payment terms were agreed?",
        "Welche Zahlungsbedingungen wurden vereinbart?",
        {"code": "NET30", "name": "30 days net", "due_days": 30},
        "The term holds the agreed payment window and any stated discount offer. Empty discount fields mean no such offer is recorded.",
        "Die Bedingung hält Zahlungsfrist und ein gegebenenfalls genanntes Skontoangebot fest. Leere Skontofelder bedeuten, dass kein solches Angebot erfasst ist.",
        "A term is not a payment or an allocation. Whether an invoice is settled comes from financial records.",
        "Eine Zahlungsbedingung ist keine Zahlung oder Zuordnung. Ob eine Rechnung ausgeglichen ist, ergibt sich aus den Finanzeinträgen.",
        ["party", "document", "settlement_allocation"],
    ),
    (
        "price_list",
        "PriceList",
        "Which commercial price list applies?",
        "Welche kaufmännische Preisliste gilt?",
        {
            "code": "SALES-EUR",
            "name": "Standard sales",
            "direction": "sales",
            "currency": "EUR",
        },
        "A price list holds its direction, currency and validity. Item prices are separate entries, and partner applicability is assigned explicitly.",
        "Eine Preisliste hält Richtung, Währung und Gültigkeit fest. Artikelpreise sind eigene Einträge; die Geltung für Partner wird ausdrücklich zugeordnet.",
        "Price selection uses entries and assignments; the price actually agreed on a document line remains evidence.",
        "Die Preisauswahl verwendet Einträge und Zuordnungen; der tatsächlich vereinbarte Preis auf einer Belegposition bleibt der Nachweis.",
        [
            "price_list_entry",
            "party_price_list",
            "party_group_price_list",
            "document_line",
        ],
    ),
    (
        "price_list_entry",
        "PriceListEntry",
        "What price was stated for this item and quantity tier?",
        "Welcher Preis gilt für Artikel und Mengenstaffel?",
        {"min_quantity": "1.000000", "unit_price": "49.0000", "unit": "pcs"},
        "One entry states an item's price from a quantity threshold within a price list. Its validity can be bounded separately.",
        "Ein Eintrag nennt den Artikelpreis ab einer Mengenschwelle innerhalb einer Preisliste. Seine Gültigkeit kann separat begrenzt sein.",
        "This is a price basis, not a recalculated invoice total or stock valuation.",
        "Das ist eine Preisgrundlage, keine nachgerechnete Rechnungssumme oder Bestandsbewertung.",
        ["price_list", "item", "document_line"],
    ),
    (
        "party_price_list",
        "PartyPriceList",
        "Which list is assigned directly to the partner?",
        "Welche Preisliste ist dem Partner direkt zugeordnet?",
        {"priority": 100},
        "The assignment connects Northstar to a price list with priority and optional validity. It does not copy the list's prices.",
        "Die Zuordnung verbindet Northstar mit einer Preisliste samt Priorität und optionaler Gültigkeit. Sie kopiert nicht deren Preise.",
        "The applicable price is selected using assignments and entries at read time.",
        "Der passende Preis wird beim Lesen anhand von Zuordnungen und Einträgen ausgewählt.",
        ["party", "price_list"],
    ),
    (
        "party_group",
        "PartyGroup",
        "Which partners share a pricing group?",
        "Welche Partner teilen eine Preisgruppe?",
        {"code": "RETAIL", "name": "Retail customers", "group_type": "pricing"},
        "A pricing group is named once. Membership and assigned price lists are separate records.",
        "Eine Preisgruppe wird einmal benannt. Mitgliedschaften und zugeordnete Preislisten sind eigene Einträge.",
        "A group alone neither assigns a partner nor establishes a price.",
        "Eine Gruppe allein ordnet weder einen Partner zu noch legt sie einen Preis fest.",
        ["party_group_member", "party_group_price_list"],
    ),
    (
        "party_group_member",
        "PartyGroupMember",
        "When does this partner belong to this group?",
        "Wann gehört dieser Partner zu dieser Gruppe?",
        {"valid_from": "2026-09-01T00:00:00Z"},
        "Membership connects an existing partner to a group and can have a validity period.",
        "Die Mitgliedschaft verbindet einen bestehenden Partner mit einer Gruppe und kann zeitlich begrenzt sein.",
        "Membership affects price selection through the group's assignments; no price is stored in this record.",
        "Die Mitgliedschaft wirkt über die Zuordnungen der Gruppe auf die Preisauswahl; dieser Eintrag speichert keinen Preis.",
        ["party", "party_group", "party_group_price_list"],
    ),
    (
        "party_group_price_list",
        "PartyGroupPriceList",
        "Which list is assigned to the whole group?",
        "Welche Preisliste ist der ganzen Gruppe zugeordnet?",
        {"priority": 100},
        "This assignment connects a group to a list with priority and optional validity.",
        "Diese Zuordnung verbindet eine Gruppe mit einer Preisliste samt Priorität und optionaler Gültigkeit.",
        "Group membership and the price entries determine applicability; do not duplicate those entries per customer.",
        "Gruppenmitgliedschaft und Preiseinträge bestimmen die Anwendbarkeit; die Einträge werden nicht je Kunde dupliziert.",
        ["party_group", "price_list", "party_group_member"],
    ),
    (
        "handling_unit",
        "HandlingUnit",
        "Which physical handling unit carries goods?",
        "Welche logistische Einheit trägt die Ware?",
        {"nve": "003400000000000001"},
        "A pallet or other handling unit has an opaque identity and may carry a stated shipping-unit number. It is distinct from a shipment package.",
        "Eine Palette oder andere logistische Einheit hat eine technische Identität und gegebenenfalls eine genannte NVE. Sie ist von einem Sendungspackstück zu unterscheiden.",
        "Its physical contents and location are read through movements; reservations show allocations. There is no second stock balance here.",
        "Physischer Inhalt und Ort werden über Bewegungen gelesen; Reservierungen zeigen Zuordnungen. Hier liegt kein zweiter Bestand.",
        ["movement", "reservation", "shipment_package"],
    ),
    (
        "lot",
        "Lot",
        "Which batch do these goods belong to?",
        "Zu welcher Charge gehört diese Ware?",
        {"lot_number": "LAMP-2026-09"},
        "The batch belongs to an item. A best-before date is stored only when stated, as a calendar day without an invented time.",
        "Die Charge gehört zu einem Artikel. Ein Mindesthaltbarkeitsdatum wird nur als genannter Kalendertag gespeichert, ohne erfundene Uhrzeit.",
        "Batch stock and quality observations come from movements and supported Facts; the batch identity itself is not a stock quantity.",
        "Chargenbestand und Qualitätsbeobachtungen kommen aus Bewegungen und unterstützten Facts; die Chargenidentität selbst ist keine Bestandsmenge.",
        ["item", "serial_unit", "movement", "fact"],
    ),
    (
        "serial_unit",
        "SerialUnit",
        "Which individual physical unit is this?",
        "Welche einzelne physische Einheit ist das?",
        {"serial_number": "LAMP-SN-001"},
        "A serialized unit belongs to an item and may also belong to a lot. Its number is supplied, while links use its opaque ID.",
        "Eine serialisierte Einheit gehört zu einem Artikel und gegebenenfalls zu einer Charge. Ihre Nummer ist eine genannte Angabe; Verknüpfungen verwenden die technische ID.",
        "Where the unit is and what happened to it are read through movements.",
        "Wo die Einheit liegt und was mit ihr passiert ist, wird über Bewegungen gelesen.",
        ["item", "lot", "movement", "reservation"],
    ),
    (
        "shipment",
        "Shipment",
        "Which physical transport connects us to the partner?",
        "Welche physische Sendung verbindet uns mit dem Partner?",
        {"direction": "outbound", "purpose": "customer_delivery"},
        "A shipment groups the transport to Northstar. Packages hold tracking details; transport events report progress. Goods are linked through package movements.",
        "Eine Sendung bündelt den Transport zu Northstar. Packstücke halten Trackingangaben; Transportereignisse melden den Verlauf. Die Ware ist über Packstückbewegungen verknüpft.",
        "Shipment progress is read from events. Movement remains the authority for physical stock; a delivered report does not post stock again.",
        "Der Sendungsverlauf wird aus Ereignissen gelesen. Movement bleibt die Autorität für physischen Bestand; eine Zustellmeldung bucht Bestand nicht erneut.",
        ["party", "shipment_package", "shipment_event", "movement"],
    ),
    (
        "shipment_package",
        "ShipmentPackage",
        "Which package and tracking number belong to this shipment?",
        "Welches Packstück mit welcher Trackingnummer gehört zur Sendung?",
        {"carrier": "Example carrier", "tracking_number": "TRACK-HUBER-01"},
        "The package belongs to one shipment. Carrier and tracking number may be unknown; they are not its technical identity.",
        "Das Packstück gehört zu einer Sendung. Dienstleister und Trackingnummer dürfen unbekannt sein; sie sind nicht seine technische Identität.",
        "Its item quantities come from linked movements; its transport progress comes from reports.",
        "Seine Artikelmengen kommen aus verknüpften Bewegungen; sein Transportverlauf kommt aus Meldungen.",
        ["shipment", "movement", "shipment_event"],
    ),
    (
        "shipment_event",
        "ShipmentEvent",
        "Who reported what about the transport, and when?",
        "Wer hat was wann über den Transport gemeldet?",
        {
            "event_type": "in_transit",
            "reporter_type": "carrier",
            "location_text": "Sorting hub",
        },
        "A report records both its reporter and when it was recorded. An unknown occurrence time stays unknown. A report may concern the shipment or a package.",
        "Eine Meldung hält Absender und Erfassungszeit fest. Ein unbekannter Ereigniszeitpunkt bleibt unbekannt. Eine Meldung kann Sendung oder Packstück betreffen.",
        "Transport progress is read from the applicable reports, excluding superseded ones; reports do not replace warehouse movements.",
        "Der Transportverlauf wird aus den geltenden Meldungen gelesen, unter Ausschluss abgelöster Meldungen; sie ersetzen keine Lagerbewegungen.",
        ["shipment", "shipment_package", "shipment_event_supersession"],
    ),
    (
        "shipment_event_supersession",
        "ShipmentEventSupersession",
        "Which transport report was withdrawn or corrected?",
        "Welche Transportmeldung wurde zurückgenommen oder korrigiert?",
        {"reason": "Carrier corrected the report"},
        "This evidence links a superseded report and an optional replacement. The earlier report remains traceable.",
        "Dieser Nachweis verknüpft eine abgelöste Meldung und einen optionalen Ersatz. Die frühere Meldung bleibt nachvollziehbar.",
        "The current transport interpretation excludes superseded reports instead of deleting their history.",
        "Die aktuelle Transportauswertung schließt abgelöste Meldungen aus, statt ihre Historie zu löschen.",
        ["shipment_event", "source_record"],
    ),
    (
        "return_announcement",
        "ReturnAnnouncement",
        "What did the customer say they would send back?",
        "Was hat der Kunde zur Rücksendung angekündigt?",
        {"quantity": "2.0000", "reference": "RETURN-HUBER-01", "status": "open"},
        "An announced return refers to the original customer delivery promise. It is not proof that the goods have arrived.",
        "Eine Retourenankündigung verweist auf die ursprüngliche Kundenzusage. Sie belegt nicht, dass die Ware bereits eingetroffen ist.",
        "Actual receipt and later handling are read from movements; an announcement itself changes no stock.",
        "Tatsächlicher Eingang und weitere Behandlung werden aus Bewegungen gelesen; die Ankündigung selbst ändert keinen Bestand.",
        ["commitment", "movement", "shipment"],
    ),
    (
        "movement_correction",
        "MovementCorrection",
        "How was an incorrect movement compensated?",
        "Wie wurde eine falsche Bewegung ausgeglichen?",
        {"reason": "Incorrect shipment quantity"},
        "The correction links the original movement, its compensation and an optional replacement. It preserves the explanation for the changed stock picture.",
        "Die Korrektur verknüpft ursprüngliche Bewegung, Ausgleich und optionalen Ersatz. Sie erhält die Erklärung für das geänderte Bestandsbild.",
        "Net stock and fulfilment include the relevant correcting movements rather than an overwritten original quantity.",
        "Nettobestand und Erfüllung berücksichtigen die relevanten Korrekturbewegungen statt einer überschriebenen Ursprungsmenge.",
        ["movement", "commitment"],
    ),
    (
        "subledger_account",
        "SubledgerAccount",
        "Which operational financial account receives postings?",
        "Auf welches operative Finanzkonto wird gebucht?",
        {
            "code": "AR",
            "name": "Customer receivables",
            "role": "accounts_receivable",
            "state": "active",
        },
        "An account has a code, an operational role and a state. It is not a complete statutory chart of accounts. Postings link to the account within the same tenant.",
        "Ein Konto hat Kürzel, operative Rolle und Zustand. Es ist kein vollständiger gesetzlicher Kontenplan. Buchungen verweisen innerhalb desselben Unternehmens auf das Konto.",
        "The account balance is derived from LedgerEntry; blocking an account does not erase previous postings.",
        "Der Kontosaldo entsteht aus LedgerEntry; das Sperren eines Kontos löscht keine früheren Buchungen.",
        ["ledger_entry", "finance_role_destination"],
    ),
    (
        "finance_role_destination",
        "FinanceRoleDestination",
        "Which account is the default destination for this posting role?",
        "Welches Konto ist das Standardziel dieser Buchungsrolle?",
        {"role": "accounts_receivable"},
        "The role destination maps a financial role to an account. tenant_id and account_id jointly reference the account in the same company.",
        "Das Rollenziel ordnet einer Finanzrolle ein Konto zu. tenant_id und account_id verweisen gemeinsam auf das Konto desselben Unternehmens.",
        "This selects a posting destination; it neither holds a balance nor rewrites earlier postings.",
        "Das wählt ein Buchungsziel aus; es hält keinen Saldo und schreibt keine früheren Buchungen um.",
        ["subledger_account", "ledger_entry"],
    ),
    (
        "ledger_reversal",
        "LedgerReversal",
        "Which posting group reverses the original booking?",
        "Welche Buchungsgruppe storniert die ursprüngliche Buchung?",
        {"reason": "Payment was posted twice"},
        "A reversal records the link between the original group and its exact inverse, with reason and actor context. Original entries remain.",
        "Eine Stornierung hält die Verbindung zwischen Ursprungsgruppe und Gegenbuchung samt Grund und Akteurskontext fest. Die ursprünglichen Einträge bleiben.",
        "The financial effect is read from original and reversing LedgerEntries; the reversal record explains their relationship.",
        "Die finanzielle Wirkung wird aus ursprünglichen und stornierenden LedgerEntries gelesen; der Stornoeintrag erklärt ihre Beziehung.",
        ["ledger_entry", "settlement_allocation"],
    ),
    (
        "settlement_allocation",
        "SettlementAllocation",
        "How much of a payment settles which invoice?",
        "Wie viel einer Zahlung gleicht welche Rechnung aus?",
        {"amount": "500.0000", "currency": "EUR"},
        "The allocation links a payment-side and invoice-side posting entry with an amount. One payment may be allocated across invoices.",
        "Die Zuordnung verbindet einen zahlungsseitigen und einen rechnungsseitigen Buchungseintrag mit einem Betrag. Eine Zahlung kann auf mehrere Rechnungen verteilt werden.",
        "The invoice's remaining open amount is read from postings and allocations; allocation is not another payment.",
        "Der noch offene Rechnungsbetrag wird aus Buchungen und Zuordnungen gelesen; eine Zuordnung ist keine weitere Zahlung.",
        ["ledger_entry", "document"],
    ),
    (
        "commitment_hold",
        "CommitmentHold",
        "Why is this particular promise on hold?",
        "Warum ist diese konkrete Zusage gesperrt?",
        {"reason_code": "manual_review", "note": "Clarify delivery details"},
        "This hold belongs to one promise rather than the whole partner. It records the reason and any later release.",
        "Diese Sperre gehört zu einer einzelnen Zusage statt zum ganzen Partner. Sie hält Grund und spätere Freigabe fest.",
        "Read readiness together with all other blockers; releasing this hold does not itself deliver goods.",
        "Die Ausführbarkeit wird zusammen mit allen weiteren Hindernissen gelesen; die Freigabe dieser Sperre liefert selbst keine Ware.",
        ["commitment", "party_hold"],
    ),
]:
    RECORDS.append(
        record(
            key,
            name,
            en,
            de,
            example,
            note_en,
            note_de,
            derived_en,
            derived_de,
            related,
        )
    )

GROUPS = {
    "core": (
        "Evidence & operational core",
        "Belege & operativer Kern",
        "source_record document document_line commitment commitment_revision commitment_hold reservation movement fact",
    ),
    "master": (
        "Master data",
        "Stammdaten",
        "party party_role party_hold item location payment_term",
    ),
    "pricing": (
        "Pricing & assignments",
        "Preise & Zuordnungen",
        "price_list price_list_entry party_price_list party_group party_group_member party_group_price_list",
    ),
    "warehouse": (
        "Warehouse & shipping",
        "Lager & Versand",
        "handling_unit lot serial_unit shipment shipment_package shipment_event shipment_event_supersession return_announcement movement_correction",
    ),
    "finance": (
        "Finance",
        "Finanzen",
        "ledger_entry subledger_account finance_role_destination ledger_reversal settlement_allocation",
    ),
}
for definition in RECORDS:
    for group, (en, de, keys) in GROUPS.items():
        if definition["key"] in keys.split():
            definition.update(group=group, groupLabel=bilingual(en, de))

for table in ("party_price_list", "party_group_price_list"):
    OVERRIDES[table, "priority"] = bilingual(
        "Priority used when selecting between price list assignments; see the pricing tool's selection rules.",
        "Priorität zur Auswahl zwischen Preislistenzuordnungen; die Auswahlregeln stehen beim Preistool.",
    )
OVERRIDES["party", "payload"] = bilingual(
    "Additional partner data captured by the application. The complete external source remains in SourceRecord.",
    "Von der Anwendung erfasste zusätzliche Partnerdaten. Die vollständige externe Quelle bleibt im SourceRecord.",
)
OVERRIDES["item", "sku"] = bilingual(
    "Business item code, not the opaque ID used by relationships.",
    "Fachliche Artikelnummer, nicht die technische ID für Verknüpfungen.",
)
OVERRIDES["price_list_entry", "unit_price"] = bilingual(
    "Stated unit price in this price tier, in the price list currency.",
    "Genannter Stückpreis dieser Preisstaffel in der Währung der Preisliste.",
)
OVERRIDES["shipment", "direction"] = bilingual(
    "Physical transport direction: inbound or outbound.",
    "Physische Transportrichtung: inbound (eingehend) oder outbound (ausgehend).",
)
OVERRIDES["price_list", "direction"] = bilingual(
    "Commercial direction of the list: sales or purchase.",
    "Kaufmännische Richtung der Liste: sales (Verkauf) oder purchase (Einkauf).",
)
OVERRIDES["shipment_event", "occurred_at"] = bilingual(
    "When the reporter says the event occurred; empty if unknown. recorded_at is the separate intake time.",
    "Vom Meldenden genannter Ereigniszeitpunkt; leer, falls unbekannt. recorded_at ist der getrennte Erfassungszeitpunkt.",
)
OVERRIDES["finance_role_destination", "tenant_id"] = OVERRIDES[
    "ledger_entry", "tenant_id"
]
# Extend the original overview links as related objects become covered.
for definition in RECORDS:
    additions = {
        "movement": [
            "item",
            "location",
            "shipment_package",
            "movement_correction",
            "return_announcement",
        ],
        "ledger_entry": [
            "subledger_account",
            "settlement_allocation",
            "ledger_reversal",
        ],
        "commitment": ["party", "item", "commitment_hold"],
        "reservation": ["item", "location", "handling_unit", "lot", "serial_unit"],
    }.get(definition["key"], [])
    definition["related"].extend(additions)


def build_data_models(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from reality.db.core import Base

    result = []
    keys = {r["key"] for r in RECORDS}
    for r in RECORDS:
        if not r.get("group") or set(r["related"]) - keys:
            raise ValueError(f"Invalid group or related record for {r['key']}")
    for definition in RECORDS:
        model = dict(definition)
        table = Base.metadata.tables[model["key"]]
        if set(model["example"]) - set(table.columns.keys()):
            raise ValueError(f"Unknown example field for {model['key']}")
        fields = []
        for column in table.columns:
            default = {"kind": "none", "value": ""}
            if column.server_default is not None:
                default = {"kind": "server", "value": str(column.server_default.arg)}
            elif column.default is not None:
                if column.default.is_callable:
                    default = {
                        "kind": "generated",
                        "value": column.default.arg.__name__,
                    }
                else:
                    default = {"kind": "scalar", "value": column.default.arg}
            meaning = OVERRIDES.get(
                (model["key"], column.name), MEANINGS.get(column.name)
            )
            if meaning is None:
                raise ValueError(
                    f"Missing field explanation: {model['key']}.{column.name}"
                )
            fields.append(
                {
                    "name": column.name,
                    "type": str(column.type.compile(dialect=postgresql.dialect())),
                    "nullable": column.nullable,
                    "default": default,
                    "meaning": meaning,
                    # A set, because since spec 181 FR-005 a company column takes
                    # part in every composite reference its table makes, and the
                    # same parent would otherwise be listed once per reference.
                    "references": sorted(
                        {fk.target_fullname for fk in column.foreign_keys}
                    ),
                }
            )
        model["fields"] = fields
        model["actions"] = [
            e["id"]
            for e in entries
            if e["kind"] == "command"
            and (
                model["key"] in e.get("writes", [])
                or model["key"] == "commitment"
                and e["key"] == "revise_commitment"
            )
        ]
        result.append(model)
    return result
