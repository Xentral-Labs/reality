"""Read-only business summaries, composed from the existing operational authorities."""

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    PaymentTerm,
    Reservation,
    SubledgerAccount,
    now,
)
from reality.services.core import (
    NotFound,
    _financial_open_items,
    _payment_rows,
    active_reserved,
    active_settlement_allocations,
    document_detail,
    ledger_reversal_snapshot,
    stock_at,
    with_invoice_aging,
)
from reality.services.delivery_reads import delivery_case
from reality.services.inspector_presentation import display_parts, display_text, money
from reality.services.shipments import shipment_explain

Section = dict[str, Any]
LIMIT = 20


def _record(session: Session, tenant: str, model, record_id: str):
    record = session.scalar(
        select(model).where(model.tenant_id == tenant, model.id == record_id)
    )
    if record is None:
        raise NotFound("Preview record not found.")
    return record


def _optional(session: Session, tenant: str, model, record_id: str | None):
    if not record_id:
        return None
    return session.scalar(
        select(model).where(model.tenant_id == tenant, model.id == record_id)
    )


def _row(
    label: str,
    value: Any,
    kind: str = "",
    record_id: str | None = None,
    *,
    hint: str | None = None,
    original_label: bool = False,
) -> dict[str, Any]:
    translated = label in {"Status", "Direction", "Type", "Debit / credit"}
    if translated and value is not None:
        value = {"paid": "Settled", "partial": "Partially settled"}.get(
            str(value), str(value).replace("_", " ").capitalize()
        )
    parts = display_parts(value)
    return {
        "label": label,
        "original_label": original_label,
        "translate_value": translated,
        "value": str(value) if value is not None and value != "" else "—",
        **({"display_parts": parts} if parts else {}),
        "link": {"kind": kind, "id": record_id} if kind and record_id else None,
        **({"hint": hint} if hint else {}),
    }


def _section(title: str, rows: list[dict[str, Any]]) -> Section:
    return {"title": title, "rows": rows[:LIMIT], "has_more": len(rows) > LIMIT}


def _day(value: str) -> date | str:
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return value


def _quantity(value: Any, unit: str) -> str:
    return display_text(Decimal(str(value)), f" {unit}")


def _name(record) -> str | None:
    return record.name if record else None


def _party_label(document_type: str) -> str:
    return (
        "Supplier"
        if document_type.startswith(("purchase", "supplier", "opening_supplier"))
        else "Customer"
    )


def _context(
    session: Session, tenant: str, commitment: Commitment
) -> list[dict[str, Any]]:
    supplier = commitment.type == "supplier_delivery"
    party = _optional(
        session,
        tenant,
        Party,
        commitment.from_party_id if supplier else commitment.to_party_id,
    )
    line = _optional(session, tenant, DocumentLine, commitment.document_line_id)
    document = _optional(
        session, tenant, Document, line.document_id if line else commitment.document_id
    )
    rows = [
        _row(
            "Supplier" if supplier else "Customer",
            _name(party),
            "party",
            party.id if party else None,
        )
    ]
    if document:
        rows.append(_row("Document", document.number, "document", document.id))
    return rows


def _delivery(session: Session, tenant: str, commitment: Commitment) -> list[Section]:
    case = delivery_case(session, tenant, commitment.id)["case"]
    rows = _context(session, tenant, commitment)
    item = _optional(session, tenant, Item, commitment.item_id)
    rows += [
        _row(
            "Item",
            f"{item.sku} · {item.name}" if item else None,
            "item",
            item.id if item else None,
        ),
        _row("Location", case["location"], "location", case["location_id"]),
        _row("Due", case["due_at"]),
        _row("Status", case["status"]),
    ]
    quantities = [
        _row(label, _quantity(case[key], case["unit"]))
        for label, key in (
            ("Committed", "promised"),
            ("Reserved", "reserved"),
            ("Fulfilled", "fulfilled"),
            ("Open", "open"),
        )
    ]
    sections = [_section("Business context", rows), _section("Fulfillment", quantities)]
    if case["blockers"]:
        sections.append(
            _section(
                "Holds",
                [_row(b["reason"], b["note"] or b["scope"]) for b in case["blockers"]],
            )
        )
    return sections


def _document(session: Session, tenant: str, record_id: str) -> list[Section]:
    detail = document_detail(session, tenant, record_id)
    doc, party = detail["document"], detail["party"]
    rows = [
        _row(
            _party_label(doc.type), _name(party), "party", party.id if party else None
        ),
        _row("Document", doc.number, "document", doc.id),
        _row("Date", _day(doc.document_date)),
        _row("Gross amount", money(doc.gross_amount, doc.currency)),
    ]
    for label, value in [
        ("Customer reference", doc.customer_reference),
        ("Requested delivery", doc.requested_delivery_at),
    ]:
        if value:
            rows.append(_row(label, value))
    if detail["ship_to_party"]:
        ship_to = detail["ship_to_party"]
        rows.append(_row("Ship to", ship_to.name, "party", ship_to.id))
    lines = []
    for line in sorted(
        detail["lines"], key=lambda line: (line.source_line_id or "", line.id)
    ):
        item = detail["items_by_id"].get(line.item_id)
        description = line.description or _name(item)
        label = " · ".join(value for value in (line.sku, description) if value) or "—"
        lines.append(
            _row(
                label,
                display_text(
                    line.quantity,
                    f" {line.unit} · ",
                    money(line.gross_amount, doc.currency),
                ),
                "document_line",
                line.id,
                hint="Current item name" if not line.description and item else None,
                original_label=True,
            )
        )
    sections = [_section("Document", rows), _section("Lines", lines)]
    deliveries = [
        c
        for c in detail["commitments"]
        if c.type in {"customer_delivery", "supplier_delivery"}
    ]
    if deliveries:
        operational = []
        for commitment in deliveries[:LIMIT]:
            case = delivery_case(session, tenant, commitment.id)["case"]
            # Each commitment keeps its own unit and effective quantities; no mixed-unit total.
            operational.append(
                {
                    **_row(
                        case["item"] or "—",
                        display_text(
                            Decimal(case["promised"]),
                            " / ",
                            Decimal(case["reserved"]),
                            " / ",
                            Decimal(case["fulfilled"]),
                            " / ",
                            Decimal(case["open"]),
                            f" {case['unit']}",
                        ),
                        "commitment",
                        commitment.id,
                    ),
                    "hint": "Committed / reserved / fulfilled / open",
                    "original_label": True,
                }
            )
            if case["due_at"]:
                operational.append(
                    _row("Due", case["due_at"], "commitment", commitment.id)
                )
            if case["blockers"]:
                operational.append(
                    _row("Holds", " · ".join(b["reason"] for b in case["blockers"]))
                )
        section = _section("Operational Reality", operational)
        section["has_more"] = section["has_more"] or len(deliveries) > LIMIT
        sections.append(section)
    financial = _financial_open_items(session, tenant, document_ids={doc.id})
    if financial:
        term_ids = {doc.payment_term_id, party.payment_term_id if party else None} - {
            None
        }
        terms = {
            term.id: term
            for term in session.scalars(
                select(PaymentTerm).where(
                    PaymentTerm.tenant_id == tenant, PaymentTerm.id.in_(term_ids)
                )
            )
        }
        position = with_invoice_aging(financial, terms, now())[0]
        sections.insert(
            1,
            _section(
                "Settlement",
                [
                    _row("Settled", money(position["settled"], doc.currency)),
                    _row("Open amount", money(position["open"], doc.currency)),
                    _row("Due", position["due_date"]),
                    _row("Status", position["status"]),
                ],
            ),
        )
    return sections


def _stock(session: Session, tenant: str, record_id: str) -> list[Section]:
    item = _record(session, tenant, Item, record_id)
    physical = stock_at(session, tenant, item.id)
    reserved = active_reserved(session, tenant, item.id)
    # Locations are discovered from this item's records, never from an unrelated default.
    location_ids = set(
        session.scalars(
            select(Reservation.location_id).where(
                Reservation.tenant_id == tenant, Reservation.item_id == item.id
            )
        )
    )
    for origin, destination in session.execute(
        select(Movement.from_location_id, Movement.to_location_id).where(
            Movement.tenant_id == tenant, Movement.item_id == item.id
        )
    ):
        location_ids.update((origin, destination))
    locations = session.scalars(
        select(Location)
        .where(Location.tenant_id == tenant, Location.id.in_(location_ids - {None}))
        .order_by(Location.name, Location.id)
        .limit(LIMIT + 1)
    ).all()
    location_rows = []
    for location in locations[:LIMIT]:
        held = stock_at(session, tenant, item.id, location.id)
        assigned = active_reserved(session, tenant, item.id, location.id)
        location_rows.append(
            _row(
                location.name,
                _quantity(held - assigned, item.unit),
                "location",
                location.id,
                hint="Available stock",
                original_label=True,
            )
        )
    scope = _section("Available stock by location", location_rows)
    scope["has_more"] = len(locations) > LIMIT
    return [
        _section(
            "Stock across all locations",
            [
                _row("Item", f"{item.sku} · {item.name}", "item", item.id),
                _row("Physical", _quantity(physical, item.unit)),
                _row("Reserved", _quantity(reserved, item.unit)),
                _row("Available", _quantity(physical - reserved, item.unit)),
            ],
        ),
        scope,
    ]


def _warehouse(
    session: Session, tenant: str, kind: str, record_id: str
) -> list[Section]:
    record = _record(
        session, tenant, Reservation if kind == "reservation" else Movement, record_id
    )
    item = _optional(session, tenant, Item, record.item_id)
    rows = [
        _row(
            "Item",
            f"{item.sku} · {item.name}" if item else None,
            "item",
            item.id if item else None,
        ),
        _row("Quantity", _quantity(record.quantity, item.unit if item else "")),
    ]
    if kind == "reservation":
        rows += [_row("Status", record.status), _row("Reserved at", record.reserved_at)]
        locations = [("Location", record.location_id)]
    else:
        rows += [_row("Type", record.type), _row("Occurred", record.occurred_at)]
        locations = [("From", record.from_location_id), ("To", record.to_location_id)]
    for label, location_id in locations:
        location = _optional(session, tenant, Location, location_id)
        rows.append(
            _row(label, _name(location), "location", location.id if location else None)
        )
    sections = [_section("Business context", rows)]
    commitment = _optional(session, tenant, Commitment, record.commitment_id)
    if commitment:
        sections.append(
            _section(
                "Commitment",
                _context(session, tenant, commitment)
                + [_row("Commitment", commitment.type, "commitment", commitment.id)],
            )
        )
    return sections


def _shipment(
    session: Session, tenant: str, kind: str, record_id: str
) -> list[Section]:
    detail = shipment_explain(session, tenant, record_id)
    packages = [
        p for p in detail["packages"] if kind == "shipment" or p["id"] == record_id
    ]
    if kind == "shipment_package" and not packages:
        raise NotFound("Shipment package not found.")
    package_ids = {p["id"] for p in packages}
    movements = [m for m in detail["movements"] if m["package_id"] in package_ids]
    item_ids = {m["item_id"] for m in movements}
    items = {
        item.id: item
        for item in session.scalars(
            select(Item).where(Item.tenant_id == tenant, Item.id.in_(item_ids))
        )
    }
    party = _optional(session, tenant, Party, detail["counterparty_id"])
    contents = []
    for movement in movements:
        item = items.get(movement["item_id"])
        contents.append(
            _row(
                f"{item.sku} · {item.name}" if item else "—",
                _quantity(movement["quantity"], item.unit if item else ""),
                "movement",
                movement["id"],
                hint=movement["type"].replace("_", " ").capitalize(),
                original_label=True,
            )
        )
    events = [
        e
        for e in detail["events"]
        if e["package_id"] is None or e["package_id"] in package_ids
    ]
    events.sort(
        key=lambda event: (event["occurred_at"] is not None, event["occurred_at"]),
        reverse=True,
    )
    return [
        _section(
            "Business context",
            [
                _row(
                    "Supplier"
                    if detail["purpose"].startswith("supplier")
                    else "Customer",
                    _name(party),
                    "party",
                    party.id if party else None,
                ),
                _row("Direction", detail["direction"]),
                _row("Recorded at", detail["created_at"]),
            ],
        ),
        _section(
            "Packages",
            [
                _row(
                    p["carrier"] or "Package",
                    p["tracking_number"],
                    "shipment_package",
                    p["id"],
                    original_label=bool(p["carrier"]),
                )
                for p in packages
            ],
        ),
        _section("Effective physical contents", contents),
        _section(
            "Current tracking observations",
            [
                _row(
                    e["event_type"].replace("_", " ").capitalize(),
                    e["occurred_at"],
                    hint=e["reporter_type"].capitalize(),
                )
                for e in events
            ],
        ),
    ]


def _finance(session: Session, tenant: str, kind: str, record_id: str) -> list[Section]:
    entry = _record(session, tenant, LedgerEntry, record_id)
    party = _optional(session, tenant, Party, entry.party_id)
    doc = _optional(session, tenant, Document, entry.document_id)
    account = _optional(session, tenant, SubledgerAccount, entry.account_id)
    reversal = ledger_reversal_snapshot(session, tenant, entry.posting_group_id)
    rows = [
        *([_row("Status", reversal["status"])] if kind == "ledger_entry" else []),
        _row("Counterparty", _name(party), "party", party.id if party else None),
        _row(
            "Document", doc.number if doc else None, "document", doc.id if doc else None
        ),
        _row("Amount", money(entry.amount, entry.currency)),
        _row("Effective", entry.effective_at),
        _row(
            "Account", f"{account.code} · {account.name}" if account else entry.account
        ),
        _row("Debit / credit", entry.debit_credit),
    ]
    sections = [_section("Financial Reality", rows)]
    if kind == "payment":
        payments = _payment_rows(session, tenant, cash_entry_ids={entry.id})
        if payments:
            payment = payments[0]
            rows.extend(
                [
                    _row("Direction", payment["direction"]),
                    _row("Allocated", money(payment["allocated"], entry.currency)),
                    _row("Unallocated", money(payment["unallocated"], entry.currency)),
                    _row(
                        "Status",
                        "Reversed"
                        if payment["reversal_role"] == "reversed_original"
                        else "Posted",
                    ),
                ]
            )
            sections[0] = _section("Financial Reality", rows)
            allocations = [
                a
                for a in active_settlement_allocations(
                    session, tenant, entry_ids={payment["control_entry"].id}
                )
                if a.payment_ledger_entry_id == payment["control_entry"].id
            ]
            invoice_entries = {
                e.id: e
                for e in session.scalars(
                    select(LedgerEntry).where(
                        LedgerEntry.tenant_id == tenant,
                        LedgerEntry.id.in_(
                            {a.invoice_ledger_entry_id for a in allocations}
                        ),
                    )
                )
            }
            documents = {
                d.id: d
                for d in session.scalars(
                    select(Document).where(
                        Document.tenant_id == tenant,
                        Document.id.in_(
                            {e.document_id for e in invoice_entries.values()}
                        ),
                    )
                )
            }
            linked = []
            for allocation in allocations:
                invoice_entry = invoice_entries.get(allocation.invoice_ledger_entry_id)
                invoice = (
                    documents.get(invoice_entry.document_id) if invoice_entry else None
                )
                linked.append(
                    _row(
                        invoice.number if invoice else "—",
                        money(allocation.amount, allocation.currency),
                        "document",
                        invoice.id if invoice else None,
                        original_label=True,
                    )
                )
            sections.append(_section("Allocated invoices", linked))
    return sections


def operational_preview(
    session: Session, tenant_id: str, kind: str, record_id: str
) -> list[Section] | None:
    """Return explicitly selected business sections, or no override for other kinds."""
    if kind == "document":
        return _document(session, tenant_id, record_id)
    if kind == "commitment":
        record = _record(session, tenant_id, Commitment, record_id)
        return (
            _delivery(session, tenant_id, record)
            if record.type in {"customer_delivery", "supplier_delivery"}
            else None
        )
    if kind == "item":
        return _stock(session, tenant_id, record_id)
    if kind in {"reservation", "movement"}:
        return _warehouse(session, tenant_id, kind, record_id)
    if kind in {"shipment", "shipment_package"}:
        return _shipment(session, tenant_id, kind, record_id)
    if kind in {"payment", "ledger_entry"}:
        return _finance(session, tenant_id, kind, record_id)
    return None


def master_data_preview(detail: dict[str, Any]) -> list[Section]:
    """Present recorded reference fields without altering edit/revision inputs."""

    def field(label: str, key: str, *, enum: bool = False, numeric: bool = False):
        value = detail.get(key)
        if numeric and value is not None and value != "":
            value = Decimal(str(value))
        if enum and value is not None:
            value = {"none": "No tracking"}.get(
                str(value), str(value).replace("_", " ").capitalize()
            )
        row = _row(label, value)
        if enum:
            row["translate_value"] = True
        return row

    identity = [_row("Status", "Active" if detail["is_active"] else "Inactive")]
    family = detail["family"]
    if family in {"customer", "supplier"}:
        identity += [field("Type", "type", enum=True)]
        identity += [
            {**_row("Role", role.capitalize()), "translate_value": True}
            for role in detail.get("roles", [])
        ]
        credit = detail.get("credit_limit")
        commercial = [
            field("Accounting code", "accounting_code"),
            _row(
                "Payment term",
                " · ".join(
                    v
                    for v in (
                        detail.get("payment_term_code"),
                        detail.get("payment_term_name"),
                    )
                    if v
                ),
            ),
            field("Default currency", "default_currency"),
            _row(
                "Credit limit",
                money(Decimal(str(credit)), detail.get("default_currency"))
                if credit is not None
                else None,
            ),
            field("Tax identifier", "tax_identifier"),
        ]
        return [
            _section("Identity", identity),
            _section("Commercial defaults", commercial),
        ]
    if family == "item":
        identity += [
            field("SKU", "sku"),
            field("Unit", "unit"),
            field("Item type", "item_type", enum=True),
        ]
        return [
            _section("Identity", identity),
            _section(
                "Inventory behaviour",
                [
                    field("Tracking", "tracking_type", enum=True),
                    _row(
                        "Default location",
                        detail.get("default_location_name"),
                        "location",
                        detail.get("default_location_id")
                        if detail.get("default_location_name")
                        else None,
                    ),
                    field("Purchase unit", "purchase_unit"),
                    field("Conversion factor", "conversion_factor", numeric=True),
                    field("Lead time (days)", "lead_time_days", numeric=True),
                ],
            ),
        ]
    identity += [field("Type", "type", enum=True)]
    return [
        _section("Identity", identity),
        _section(
            "Hierarchy",
            [
                _row(
                    "Parent location",
                    detail.get("parent_location_name"),
                    "location",
                    detail.get("parent_location_id")
                    if detail.get("parent_location_name")
                    else None,
                ),
                {
                    **_row(
                        "Allows physical stock",
                        "Yes" if detail.get("allows_stock") else "No",
                    ),
                    "translate_value": True,
                },
            ],
        ),
    ]
