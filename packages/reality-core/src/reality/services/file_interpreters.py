from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    Item,
    Location,
    Party,
    PartyRole,
    SourceRecord,
)
from reality.services.core import (
    InvalidOperation,
    decimal,
)

ALIASES = {
    "sku": ("sku", "article_number", "item_number"),
    # Spec 308: the customer's own article number for our item.
    "customer_item_number": (
        "customer_item_number",
        "customer_article_number",
        "kundenartikelnummer",
    ),
    "name": ("name", "title", "description"),
    "external_id": ("external_id", "id", "source_id"),
    "quantity": ("quantity", "qty", "stock"),
    "location": ("location", "location_name", "warehouse"),
    "amount": ("amount", "value", "total"),
    "currency": ("currency", "currency_code"),
    "effective_at": ("effective_at", "date", "booking_date"),
    # Spec 344: when an external stock statement says the stock was there.
    "stated_at": ("stated_at", "as_of", "reported_at", "snapshot_at"),
}

FILE_MAPPING_PROFILES = {
    "item": {
        "required": [("sku",), ("name",)],
        "fields": [
            "sku",
            "name",
            "unit",
            "item_type",
            "tracking_type",
            "purchase_unit",
            "conversion_factor",
            "lead_time_days",
        ],
    },
    "party": {
        "required": [("name",)],
        "fields": [
            "name",
            "party_type",
            "roles",
            "accounting_code",
            "payment_term_code",
            "default_currency",
            "credit_limit",
            "tax_identifier",
        ],
    },
    "location": {
        "required": [("name",)],
        "fields": ["name", "location_type", "allows_stock"],
    },
    "sales_order": {
        "required": [
            ("order_id", "order_number"),
            ("sku", "customer_item_number"),
            ("quantity",),
            ("location",),
            ("party_accounting_code", "party_name"),
        ],
        "fields": [
            "order_id",
            "order_number",
            "line_id",
            "party_accounting_code",
            "party_name",
            "sku",
            "customer_item_number",
            "name",
            "quantity",
            "unit_price",
            "currency",
            "location",
            "ordered_at",
            "requested_delivery_at",
            "customer_reference",
        ],
    },
    # Takes the file's stock over: the difference is posted as an adjustment.
    "inventory_snapshot": {
        "required": [("sku",), ("location",), ("quantity",)],
        "fields": ["sku", "location", "quantity"],
    },
    # Spec 344: compares, never takes over; a difference is a finding.
    "external_stock": {
        "required": [("sku",), ("location",), ("quantity",)],
        "fields": [
            "sku",
            "location",
            "quantity",
            "stated_at",
            "party_accounting_code",
            "party_name",
        ],
    },
    "bank_statement": {
        "required": [("amount",), ("party_accounting_code", "party_name")],
        "fields": [
            "payment_number",
            "external_id",
            "party_accounting_code",
            "party_name",
            "direction",
            "amount",
            "currency",
            "effective_at",
        ],
    },
}

MAX_MATERIALIZED_JSON_BYTES = 64 * 1024 * 1024


def _stated_price(row: dict[str, Any]) -> Decimal | None:
    """The row's stated unit price, or None when the file states none.

    A stated 0 is a free line, not a missing price, so each column is read for
    presence rather than truth.
    """
    for column in ("unit_price", "price"):
        value = row.get(column)
        if value is not None and str(value).strip() != "":
            return decimal(value)
    return None


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
    missing = [
        " or ".join(group)
        for group in profile["required"]
        if not any(mapping.get(field) for field in group)
    ]
    if missing:
        raise InvalidOperation("Map the required fields: " + ", ".join(missing))


def _mapped_row(row: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    mapped = dict(row)
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for target_field, source_column in mapping.items():
        if source_column:
            mapped[target_field] = normalized.get(
                source_column.strip().lower(), row.get(source_column)
            )
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
            raise InvalidOperation(
                "JSON import must contain an object or array of objects."
            )
        yield from values
        return
    raise InvalidOperation("No tabular parser exists for this file type.")


def _item(session: Session, tenant_id: str, sku: str) -> Item:
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.sku == sku)
    )
    if item is None:
        raise InvalidOperation(f"Unknown SKU: {sku}")
    return item


def _location(session: Session, tenant_id: str, reference: str) -> Location:
    rows = list(
        session.scalars(
            select(Location).where(
                Location.tenant_id == tenant_id, Location.name == reference
            )
        )
    )
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
    # Spec 339: a row naming a merged partner lands on its survivor, and a
    # duplicate and its survivor matched together are one partner.
    from reality.services.party_merges import survivors_of

    survivors = survivors_of(session, tenant_id, {party.id for party in matches})
    resolved = {survivors.get(party.id, party.id) for party in matches}
    if len(resolved) != 1:
        raise InvalidOperation("Party reference must resolve uniquely.")
    (party_id,) = resolved
    return next(
        (party for party in matches if party.id == party_id),
        None,
    ) or session.get(Party, (tenant_id, party_id))


def _single_company(session: Session, tenant_id: str) -> Party:
    companies = list(
        session.scalars(
            select(Party)
            .join(PartyRole)
            .where(Party.tenant_id == tenant_id, PartyRole.role == "company")
        )
    )
    if len(companies) != 1:
        raise InvalidOperation(
            "Orders require exactly one company party in the tenant."
        )
    return companies[0]


def interpret_artifact(
    session: Session, tenant_id: str, source: SourceRecord, context: dict[str, Any]
) -> dict[str, Any]:
    """Retired writer: prepare and confirm the canonical intake proposal instead."""
    raise InvalidOperation(code="intake_approval_required")
