"""Read-only authoritative observations and independent exact comparison."""

from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session


def number(value: Any) -> str:
    return format(Decimal(value).normalize(), "f")


def differences(expected: Any, actual: Any, path: str = "") -> list[dict]:
    """Compare an explicit oracle subset; never derive expectations from Reality."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [{"path": path, "expected": expected, "actual": actual}]
        result = []
        for key, value in expected.items():
            result.extend(
                differences(value, actual.get(key), f"{path}.{key}".strip("."))
            )
        return result
    if expected == actual:
        return []
    delta = None
    try:
        delta = number(Decimal(str(actual)) - Decimal(str(expected)))
    except (InvalidOperation, ValueError, TypeError):
        pass
    return [{"path": path, "expected": expected, "actual": actual, "delta": delta}]


def observe(session: Session, tenant_id: str) -> dict:
    """Read complete scoped records; no sample limit, refresh writes or ORM mutation."""

    from reality.db.core import (
        BusinessEvent,
        Commitment,
        Document,
        DocumentLine,
        Item,
        LedgerEntry,
        Location,
        Movement,
        PartyRole,
        Reservation,
        ReturnAnnouncement,
        SourceRecord,
    )
    from reality.services.core import (
        active_reserved,
        announcement_outstanding,
        commitment_quantity,
        fulfilled_quantity,
        get_tenant,
        open_quantity,
        stock_at,
    )

    get_tenant(session, tenant_id)
    with session.no_autoflush:
        session.expire_all()

        def rows(model):
            return list(
                session.scalars(select(model).where(model.tenant_id == tenant_id))
            )

        items = rows(Item)
        locations = rows(Location)
        promises = rows(Commitment)
        documents = {row.id: row for row in rows(Document)}
        document_lines = {row.id: row for row in rows(DocumentLine)}
        sources = {row.id: row for row in rows(SourceRecord)}
        movements = rows(Movement)
        reservations = rows(Reservation)
        announcements = rows(ReturnAnnouncement)
        by_item = {item.id: item.sku for item in items}
        result = {
            "physical": {},
            "reserved": {},
            "free": {},
            "customer_open": {},
            "supplier_open": {},
            "return_open": {},
            "counts": {},
            "locations": {},
            "lines": {},
            "evidence_errors": [],
            "invariants": [],
            "movement_totals": {},
            "event_cutoff": session.scalar(
                select(func.max(BusinessEvent.sequence)).where(
                    BusinessEvent.tenant_id == tenant_id
                )
            )
            or 0,
            "freshness": "synchronous_authoritative_reads; projections_not_checked",
        }
        for item in items:
            physical = stock_at(session, tenant_id, item.id)
            reserved = active_reserved(session, tenant_id, item.id)
            result["physical"][item.sku] = number(physical)
            result["reserved"][item.sku] = number(reserved)
            result["free"][item.sku] = number(physical - reserved)
            result["customer_open"][item.sku] = "0"
            result["supplier_open"][item.sku] = "0"
            result["return_open"][item.sku] = "0"
            if physical < 0 or reserved < 0 or reserved > physical:
                result["invariants"].append(f"Invalid stock/allocation: {item.id}")
        for location in locations:
            result["locations"][location.name] = {}
            for item in items:
                physical = stock_at(session, tenant_id, item.id, location.id)
                reserved = active_reserved(session, tenant_id, item.id, location.id)
                result["locations"][location.name][item.sku] = number(physical)
                if reserved > physical or physical < 0:
                    result["invariants"].append(
                        f"Invalid location allocation: {location.id}/{item.id}"
                    )
        open_sales = set()
        for promise in promises:
            document = documents.get(promise.document_id)
            line = document_lines.get(promise.document_line_id)
            source = sources.get(document.source_record_id) if document else None
            sku = by_item.get(promise.item_id, "unknown")
            label = f"{document.number if document else promise.id}:{sku}"
            fulfilled = fulfilled_quantity(session, tenant_id, promise.id)
            quantity = commitment_quantity(session, tenant_id, promise.id)
            remaining = (
                open_quantity(session, tenant_id, promise.id)
                if promise.status != "cancelled"
                else Decimal(0)
            )
            reserved = sum(
                (
                    row.quantity
                    for row in reservations
                    if row.commitment_id == promise.id and row.status == "active"
                ),
                Decimal(0),
            )
            result["lines"][label] = {
                "quantity": number(quantity),
                "fulfilled": number(fulfilled),
                "open": number(remaining),
                "reserved": number(reserved),
                "status": promise.status,
                "commitment_id": promise.id,
                "document_id": promise.document_id,
                "document_line_id": promise.document_line_id,
                "source_record_id": source.id if source else None,
                "source_hash": source.payload_hash if source else None,
                "line_amount": number(line.gross_amount)
                if line and line.gross_amount is not None
                else None,
                "document_amount": number(document.gross_amount)
                if document and document.gross_amount is not None
                else None,
                "from_party_id": promise.from_party_id,
                "to_party_id": promise.to_party_id,
                "location_id": promise.location_id,
            }
            if not (
                document
                and line
                and source
                and line.document_id == document.id
                and line.item_id == promise.item_id
            ):
                result["evidence_errors"].append(f"Broken order lineage: {promise.id}")
            if reserved > remaining or (promise.status == "cancelled" and reserved):
                result["invariants"].append(f"Invalid promise allocation: {promise.id}")
            kind = "customer" if promise.type == "customer_delivery" else "supplier"
            if sku in result[f"{kind}_open"]:
                result[f"{kind}_open"][sku] = number(
                    Decimal(result[f"{kind}_open"][sku]) + remaining
                )
            if kind == "customer" and remaining:
                open_sales.add(promise.document_id)
        for movement in movements:
            sku = by_item.get(movement.item_id, "unknown")
            bucket = result["movement_totals"].setdefault(
                movement.type, {key: "0" for key in result["physical"]}
            )
            bucket[sku] = number(Decimal(bucket.get(sku, "0")) + movement.quantity)
            if movement.type in {"shipment", "receipt", "return"} and not any(
                p.id == movement.commitment_id for p in promises
            ):
                result["evidence_errors"].append(
                    f"Unlinked fulfillment movement: {movement.id}"
                )
        for announcement in announcements:
            promise = next(
                (p for p in promises if p.id == announcement.commitment_id), None
            )
            sku = by_item.get(promise.item_id) if promise else None
            if sku is None:
                result["evidence_errors"].append(
                    f"Unlinked return announcement: {announcement.id}"
                )
            elif announcement.status != "withdrawn":
                result["return_open"][sku] = number(
                    Decimal(result["return_open"][sku])
                    + announcement_outstanding(session, tenant_id, announcement)
                )
        roles = rows(PartyRole)
        result["counts"] = {
            "items": len(items),
            "locations": len(locations),
            "customers": len({row.party_id for row in roles if row.role == "customer"}),
            "suppliers": len({row.party_id for row in roles if row.role == "supplier"}),
            "sales_orders": sum(d.type == "sales_order" for d in documents.values()),
            "purchase_orders": sum(
                d.type == "purchase_order" for d in documents.values()
            ),
            "open_sales_orders": len(open_sales),
            "customer_commitments": sum(
                p.type == "customer_delivery" for p in promises
            ),
            "supplier_commitments": sum(
                p.type == "supplier_delivery" for p in promises
            ),
            "ledger_entries": len(rows(LedgerEntry)),
        }
        for kind in ("customer", "supplier"):
            for status in ("open", "fulfilled", "cancelled"):
                result["counts"][f"{kind}_{status}"] = sum(
                    p.type == f"{kind}_delivery" and p.status == status
                    for p in promises
                )
        result["record_ids"] = {
            "sources": sorted(sources),
            "documents": sorted(documents),
            "document_lines": sorted(document_lines),
            "commitments": sorted(p.id for p in promises),
            "movements": sorted(m.id for m in movements),
            "reservations": sorted(r.id for r in reservations),
            "return_announcements": sorted(a.id for a in announcements),
        }
        return result
