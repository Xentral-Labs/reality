# Example: From an ERP Order to Operations

This example shows the whole extension path. It is deliberately simplified for learning; the
production implementation must use the exact validations and services already present in the
repository.

## 1. The ERP sends one immutable source version

```json
{
  "id": "SO-4711-v3",
  "order_number": "SO-4711",
  "customer_id": "C-42",
  "lines": [{ "sku": "CHAIR-BLACK", "quantity": "4" }]
}
```

The connector submits this object through the shared ingest boundary with `source_system`,
`source_type`, `external_id` and an idempotency/version identity. Reality stores the complete object
as a `SourceRecord`; a later ERP correction creates another version instead of overwriting it.

## 2. Register what this source can mean

Add the ERP and source type to `packages/reality-core/config/connector_catalog.yaml`, then register
the implemented interpreter in `services/core.py`:

```python
SOURCE_INTERPRETERS = {
    ("my_erp", "sales_order"): _my_erp_sales_order_interpretation,
}
```

The catalog entry alone is not an implementation. Without the registry entry, the accepted import
remains `unmapped` and its payload is still preserved.

## 3. Interpret through shared services

This is an abridged extract of the real `_shopify_interpretation` pattern; omitted validation,
version handling and event emission remain required:

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

Use the complete `_shopify_interpretation` in `services/core.py` as the executable example. It also
creates `DocumentLine` Evidence, validates every tenant-scoped reference, handles idempotency and
emits Business Events. Changed Shopify source versions currently require review and preserve
existing Evidence, promises, reservations and movements; automatic amendment is not supported.

## 4. What becomes visible

```text
SourceRecord
  → Document → DocumentLine
               → outgoing Commitment
                    → fulfillment queue
                    → possible outgoing_commitment_at_risk Exception
                    → Reservation → Movement
```

No delivery status is copied onto the Document. The fulfillment queue and Exceptions derive the
current operational answer from Commitments, Reservations, Movements and holds.

## 5. What to test

Test first import, identical retry, changed upstream version, ambiguous customer or item, malformed
payload, tenant isolation and the trace back to `SourceRecord`. Also assert the resulting
Commitments, Business Events, Projection output and any Exception that should appear or clear.
