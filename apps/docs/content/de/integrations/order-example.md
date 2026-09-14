# Beispiel: vom ERP-Auftrag in den Betrieb

Dieses Beispiel zeigt den gesamten Erweiterungsweg. Es ist zum Lernen bewusst vereinfacht; die
produktive Umsetzung muss die genauen Prüfungen und vorhandenen Services des Repositorys verwenden.

## 1. Das ERP liefert eine unveränderliche Quellversion

```json
{
  "id": "SO-4711-v3",
  "order_number": "SO-4711",
  "customer_id": "C-42",
  "lines": [{ "sku": "CHAIR-BLACK", "quantity": "4" }]
}
```

Der Connector übergibt das Objekt mit `source_system`, `source_type`, `external_id` und einer
Idempotenz-/Versionsidentität an den gemeinsamen Ingest-Einstieg. Reality speichert das vollständige
Objekt als `SourceRecord`. Eine spätere ERP-Korrektur erzeugt eine weitere Version, statt die alte
zu überschreiben.

## 2. Registrieren, was diese Quelle bedeuten kann

Ergänze ERP und Quelltyp in `packages/reality-core/config/connector_catalog.yaml` und registriere
den implementierten Interpreter in `services/core.py`:

```python
SOURCE_INTERPRETERS = {
    ("my_erp", "sales_order"): _my_erp_sales_order_interpretation,
}
```

Der Katalogeintrag allein ist keine Implementierung. Ohne Registry-Eintrag bleibt der angenommene
Import `unmapped`; sein Payload bleibt trotzdem erhalten.

## 3. Über gemeinsame Services interpretieren

Dies ist ein gekürzter Auszug nach dem echten Muster von `_shopify_interpretation`. Die
ausgelassenen Prüfungen, Versionsbehandlung und Events bleiben zwingend erforderlich:

```python
def _my_erp_sales_order_interpretation(session, tenant_id, source, context):
    customer_party_id = context["customer_party_id"]
    location_id = context["location_id"]
    payload = json.loads(source.payload)

    item = session.scalar(
        select(Item).where(
            Item.tenant_id == tenant_id,
            Item.sku == payload["lines"][0]["sku"],
        )
    )
    document = Document(
        id=uid("doc"),
        tenant_id=tenant_id,
        type="sales_order",
        number=payload["order_number"],
        source_record_id=source.id,
        party_id=customer_party_id,
    )
    session.add(document)
    session.flush()
    commitment = Commitment(
        id=uid("com"),
        tenant_id=tenant_id,
        type="customer_delivery",
        document_id=document.id,
        to_party_id=customer_party_id,
        item_id=item.id,
        location_id=location_id,
        quantity=Decimal(payload["lines"][0]["quantity"]),
        status="open",
    )
    session.add(commitment)
    return document, commitment
```

Nutze die vollständige `_shopify_interpretation` in `services/core.py` als ausführbares Beispiel.
Sie erzeugt auch `DocumentLine`-Evidence, prüft jede mandantenbezogene Referenz, behandelt
Idempotenz und erzeugt Business Events. Geänderte Shopify-Quellversionen benötigen derzeit eine
Prüfung. Bestehende Evidence, Zusagen, Reservierungen und Bewegungen bleiben erhalten; automatische
Anpassungen werden nicht unterstützt.

## 4. Was anschließend sichtbar wird

```text
SourceRecord
  → Document → DocumentLine
               → outgoing Commitment
                    → Fulfillment Queue
                    → mögliche Exception outgoing_commitment_at_risk
                    → Reservation → Movement
```

Am Document wird kein Lieferstatus gespeichert. Fulfillment Queue und Exceptions leiten die aktuelle
operative Antwort aus Commitments, Reservations, Movements und Sperren ab.

## 5. Was getestet werden muss

Teste Erstimport, identische Wiederholung, geänderte Quellversion, mehrdeutige Kunden oder Artikel,
fehlerhaften Payload, Mandantentrennung und die Spur zum `SourceRecord`. Prüfe außerdem entstandene
Commitments, Business Events, Projection-Ausgabe sowie Exceptions, die erscheinen oder verschwinden
müssen.
