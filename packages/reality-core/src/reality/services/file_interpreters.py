from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    DocumentLine,
    Item,
    Location,
    Party,
    PartyRole,
    SourceRecord,
    uid,
)
from reality.services.artifacts import get_artifact, materialize_artifact
from reality.services.core import (
    InvalidOperation,
    create_document,
    create_item,
    create_location,
    create_party,
    decimal,
    emit_business_event,
    positive,
    record_customer_payment,
    record_movement,
    record_supplier_payment,
    stock_at,
    store_source_record,
    utc_datetime,
)

ALIASES = {
    "sku": ("sku", "article_number", "item_number"),
    "name": ("name", "title", "description"),
    "external_id": ("external_id", "id", "source_id"),
    "quantity": ("quantity", "qty", "stock"),
    "location": ("location", "location_name", "warehouse"),
    "amount": ("amount", "value", "total"),
    "currency": ("currency", "currency_code"),
    "effective_at": ("effective_at", "date", "booking_date"),
}

FILE_MAPPING_PROFILES = {
    "item": {
        "required": [("sku",), ("name",)],
        "fields": ["sku", "name", "unit", "item_type", "tracking_type", "purchase_unit", "conversion_factor", "lead_time_days"],
    },
    "party": {
        "required": [("name",)],
        "fields": ["name", "party_type", "roles", "accounting_code", "payment_term_code", "default_currency", "credit_limit", "tax_identifier"],
    },
    "location": {
        "required": [("name",)],
        "fields": ["name", "location_type", "allows_stock"],
    },
    "sales_order": {
        "required": [("order_id", "order_number"), ("sku",), ("quantity",), ("location",), ("party_accounting_code", "party_name")],
        "fields": ["order_id", "order_number", "line_id", "party_accounting_code", "party_name", "sku", "name", "quantity", "unit_price", "currency", "location", "ordered_at", "requested_delivery_at", "customer_reference"],
    },
    "inventory_snapshot": {
        "required": [("sku",), ("location",), ("quantity",)],
        "fields": ["sku", "location", "quantity"],
    },
    "bank_statement": {
        "required": [("amount",), ("party_accounting_code", "party_name")],
        "fields": ["payment_number", "external_id", "party_accounting_code", "party_name", "direction", "amount", "currency", "effective_at"],
    },
}

MAX_MATERIALIZED_JSON_BYTES = 64 * 1024 * 1024


def _value(row: dict[str, Any], name: str, default: Any = "") -> Any:
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for alias in ALIASES.get(name, (name,)):
        value = normalized.get(alias)
        if value not in (None, ""):
            return value
    return default


def suggested_mapping(columns: list[str], target: str) -> dict[str, str]:
    profile = FILE_MAPPING_PROFILES.get(target, {})
    mapping: dict[str, str] = {}
    for column in columns:
        normalized = column.strip().lower()
        for field in profile.get("fields", []):
            if normalized in ALIASES.get(field, (field,)):
                mapping[field] = column
                break
    return mapping


def validate_mapping(target: str, mapping: dict[str, str]) -> None:
    profile = FILE_MAPPING_PROFILES.get(target)
    if not profile:
        return
    missing = [" or ".join(group) for group in profile["required"] if not any(mapping.get(field) for field in group)]
    if missing:
        raise InvalidOperation("Map the required fields: " + ", ".join(missing))


def _mapped_row(row: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    mapped = dict(row)
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for target_field, source_column in mapping.items():
        if source_column:
            mapped[target_field] = normalized.get(source_column.strip().lower(), row.get(source_column))
    return mapped


def _rows(path: Path, content_type: str, filename: str) -> Iterator[dict[str, Any]]:
    suffix = Path(filename).suffix.lower()
    if suffix in {".csv", ".tsv"} or "csv" in content_type:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read(8192)
            handle.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel_tab if suffix == ".tsv" else csv.excel
            yield from csv.DictReader(handle, dialect=dialect)
        return
    if suffix == ".jsonl" or content_type == "application/x-ndjson":
        with path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                if line.strip():
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise InvalidOperation("Every JSONL row must be an object.")
                    yield value
        return
    if suffix == ".json" or "json" in content_type:
        if path.stat().st_size > MAX_MATERIALIZED_JSON_BYTES:
            raise InvalidOperation(
                "Large JSON arrays are retained losslessly but are not materialized in memory. "
                "Use CSV or JSONL for operational mapping."
            )
        with path.open("r", encoding="utf-8-sig") as handle:
            value = json.load(handle)
        values = value if isinstance(value, list) else [value]
        if any(not isinstance(row, dict) for row in values):
            raise InvalidOperation("JSON import must contain an object or array of objects.")
        yield from values
        return
    raise InvalidOperation("No tabular parser exists for this file type.")


def _item(session: Session, tenant_id: str, sku: str) -> Item:
    item = session.scalar(select(Item).where(Item.tenant_id == tenant_id, Item.sku == sku))
    if item is None:
        raise InvalidOperation(f"Unknown SKU: {sku}")
    return item


def _location(session: Session, tenant_id: str, reference: str) -> Location:
    rows = list(session.scalars(select(Location).where(Location.tenant_id == tenant_id, Location.name == reference)))
    if len(rows) != 1:
        raise InvalidOperation(f"Location must resolve uniquely by name: {reference}")
    return rows[0]


def _party(session: Session, tenant_id: str, row: dict[str, Any]) -> Party:
    accounting_code = str(row.get("party_accounting_code") or "").strip()
    name = str(row.get("party_name") or row.get("customer_name") or "").strip()
    query = select(Party).where(Party.tenant_id == tenant_id)
    if accounting_code:
        query = query.where(Party.accounting_code == accounting_code)
    elif name:
        query = query.where(Party.name == name)
    else:
        raise InvalidOperation("A party_accounting_code or party_name is required.")
    matches = list(session.scalars(query))
    if len(matches) != 1:
        raise InvalidOperation("Party reference must resolve uniquely.")
    return matches[0]


def _single_company(session: Session, tenant_id: str) -> Party:
    companies = list(session.scalars(select(Party).join(PartyRole).where(Party.tenant_id == tenant_id, PartyRole.role == "company")))
    if len(companies) != 1:
        raise InvalidOperation("Orders require exactly one company party in the tenant.")
    return companies[0]


def interpret_artifact(
    session: Session, tenant_id: str, source: SourceRecord, context: dict[str, Any]
) -> dict[str, Any]:
    from reality.services.tenant_policy import require_business_operation

    require_business_operation(session, tenant_id, "artifact_interpret")
    artifact = get_artifact(session, tenant_id, source.source_artifact_id or "")
    with materialize_artifact(artifact) as local_path:
        rows = list(_rows(local_path, artifact.content_type, artifact.filename))
    target = context.get("expected_target", "data_drop")
    mapping = context.get("column_mapping") or {}
    if mapping:
        validate_mapping(target, mapping)
    rows = (_mapped_row(row, mapping) for row in rows)
    count = 0
    created: list[str] = []
    if target == "item":
        from reality.services.business_locks import lock_delivery_state
        from reality.services.item_imports import _validate_new_rows
        lock_delivery_state(session, tenant_id)
        session.expire_all()
        rows = list(rows)
        _validate_new_rows(session, tenant_id, [
            {"sku": str(_value(row, "sku")).strip(), "name": str(_value(row, "name")).strip(), "unit": str(row.get("unit") or "pcs").strip()}
            for row in rows
        ])
        for row in rows:
            sku, name = str(_value(row, "sku")).strip(), str(_value(row, "name")).strip()
            item = create_item(
                session, tenant_id, sku, name, str(row.get("unit") or "pcs"),
                item_type=str(row.get("item_type") or "stocked"),
                tracking_type=str(row.get("tracking_type") or "none"),
                purchase_unit=str(row.get("purchase_unit") or row.get("unit") or "pcs"),
                conversion_factor=row.get("conversion_factor") or 1,
                lead_time_days=int(row.get("lead_time_days") or 0),
                source_record_id=source.id,
                _commit=False,
            )
            created.append(item.id)
            count += 1
    elif target == "location":
        for row in rows:
            allows_stock = str(row.get("allows_stock") or "true").strip().lower() in {"1", "true", "yes", "y"}
            location = create_location(
                session,
                tenant_id,
                str(_value(row, "name")),
                str(row.get("location_type") or "warehouse"),
                allows_stock=allows_stock,
                source_record_id=source.id,
            )
            created.append(location.id)
            count += 1
    elif target == "party":
        for row in rows:
            party_type = str(row.get("party_type") or row.get("type") or "customer")
            roles = [value.strip() for value in str(row.get("roles") or party_type).split(",") if value.strip()]
            party = create_party(
                session, tenant_id, str(_value(row, "name")), party_type,
                roles=roles,
                accounting_code=str(row.get("accounting_code") or ""),
                payment_term_code=str(row.get("payment_term_code") or ""),
                default_currency=str(row.get("default_currency") or "EUR"),
                credit_limit=row.get("credit_limit") or 0,
                tax_identifier=str(row.get("tax_identifier") or ""),
                source_record_id=source.id,
            )
            created.append(party.id)
            count += 1
    elif target == "inventory_snapshot":
        for row in rows:
            item = _item(session, tenant_id, str(_value(row, "sku")).strip())
            location = _location(session, tenant_id, str(_value(row, "location")).strip())
            asserted = decimal(_value(row, "quantity"))
            current = stock_at(session, tenant_id, item.id, location.id)
            delta = asserted - current
            if delta:
                movement = record_movement(
                    session, tenant_id, "adjustment", item.id, abs(delta),
                    to_location_id=location.id if delta > 0 else None,
                    from_location_id=location.id if delta < 0 else None,
                    source_record_id=source.id, reason="Imported inventory snapshot",
                )
                created.append(movement.id)
            count += 1
    elif target == "bank_statement":
        for row in rows:
            party = _party(session, tenant_id, row)
            direction = str(row.get("direction") or "incoming").strip().lower()
            if direction not in {"incoming", "outgoing"}:
                raise InvalidOperation("Payment direction must be incoming or outgoing.")
            arguments = {
                "session": session, "tenant_id": tenant_id, "party_id": party.id,
                "amount": _value(row, "amount"), "currency": str(_value(row, "currency", "EUR")),
                "payment_number": str(row.get("payment_number") or _value(row, "external_id") or uid("pay")),
                "source_record_id": source.id,
                "effective_at": utc_datetime(_value(row, "effective_at")) or datetime.now().astimezone(),
            }
            entries = record_customer_payment(**arguments) if direction == "incoming" else record_supplier_payment(**arguments)
            created.extend(entry.id for entry in entries)
            count += 1
    elif target == "sales_order":
        company = _single_company(session, tenant_id)
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            order_id = str(row.get("order_id") or row.get("order_number") or "").strip()
            if not order_id:
                raise InvalidOperation("order_id or order_number is required.")
            grouped.setdefault(order_id, []).append(row)
        for order_id, order_rows in grouped.items():
            first = order_rows[0]
            customer = _party(session, tenant_id, first)
            location = _location(session, tenant_id, str(_value(first, "location")).strip())
            total = sum((positive(_value(row, "quantity")) * decimal(row.get("unit_price") or row.get("price") or 0) for row in order_rows), Decimal(0))
            order_source, order_source_created, _ = store_source_record(
                session,
                tenant_id,
                source.source_system,
                "order",
                order_id,
                {"artifact_source_record_id": source.id, "rows": order_rows},
                source_artifact_id=artifact.id,
            )
            if order_source_created:
                emit_business_event(
                    session, tenant_id, "source_record.received", "source_record",
                    order_source.id, {"source_system": source.source_system, "source_type": "order", "external_id": order_id},
                    source_record_id=order_source.id,
                )
            session.commit()
            document = create_document(
                session, tenant_id, "sales_order", str(first.get("order_number") or order_id), customer.id, total,
                currency=str(_value(first, "currency", "EUR")), source_record_id=order_source.id,
                ordered_at=first.get("ordered_at") or None,
                requested_delivery_at=first.get("requested_delivery_at") or None,
                customer_reference=str(first.get("customer_reference") or ""),
                sales_channel=source.source_system,
            )
            for row in order_rows:
                item = _item(session, tenant_id, str(_value(row, "sku")).strip())
                quantity = positive(_value(row, "quantity")); price = decimal(row.get("unit_price") or row.get("price") or 0)
                line = DocumentLine(
                    id=uid("lin"), tenant_id=tenant_id, document_id=document.id,
                    source_line_id=str(row.get("line_id") or "") or None,
                    item_id=item.id, sku=item.sku,
                    description=str(_value(row, "name", item.name)), quantity=quantity,
                    unit_price=price, gross_amount=quantity * price, unit=item.unit,
                    requested_at=utc_datetime(row.get("requested_delivery_at")),
                    line_type="item", payload=json.dumps(row, ensure_ascii=False),
                )
                session.add(line); session.flush()
                commitment = Commitment(
                    id=uid("com"), tenant_id=tenant_id, type="customer_delivery",
                    from_party_id=company.id, to_party_id=customer.id,
                    item_id=item.id, location_id=location.id, quantity=quantity,
                    amount=quantity * price, currency=document.currency,
                    due_at=utc_datetime(row.get("requested_delivery_at")), status="open",
                    document_id=document.id, document_line_id=line.id,
                )
                session.add(commitment); created.append(commitment.id)
                emit_business_event(session, tenant_id, "commitment.created", "commitment", commitment.id, {"document_id": document.id, "item_id": item.id, "quantity": quantity}, source_record_id=order_source.id)
            session.commit()
            created.append(document.id)
            count += 1
    else:
        raise InvalidOperation(f"No file interpreter registered for target: {target}")
    return {"target": target, "rows": count, "created_ids": created}
