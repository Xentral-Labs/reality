from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Integer, Numeric, Text, and_, case, cast, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    HandlingUnit,
    Item,
    LedgerEntry,
    LedgerReversal,
    Location,
    Lot,
    Movement,
    Party,
    PaymentTerm,
    ProjectionRow,
    Reservation,
    SerialUnit,
    SettlementAllocation,
    SourceRecord,
    Tenant,
)
from reality.db.query_order import query_order
from reality.domain.calendar import as_day
from reality.services.delivery_reads import effective_value, fulfillment_expressions
from reality.services.projections import (
    MATERIALIZED_PROJECTIONS,
    OPEN_FINANCIAL_ITEMS,
    _read_without_flush,
    projection_metadata,
    projection_state_expressions,
)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
ZERO = Decimal(0)


def projection_payload_text(session, key: str):
    """Return one text value from a materialized projection payload."""
    return cast(ProjectionRow.payload, JSONB)[key].astext


@dataclass(frozen=True)
class Page:
    number: int
    size: int
    total: int

    @property
    def pages(self) -> int:
        return max(1, (self.total + self.size - 1) // self.size)

    @property
    def has_previous(self) -> bool:
        return self.number > 1

    @property
    def has_next(self) -> bool:
        return self.number < self.pages

    @property
    def offset(self) -> int:
        return (self.number - 1) * self.size


def page_for(total: int, number: int = 1, size: int = DEFAULT_PAGE_SIZE) -> Page:
    safe_size = max(1, min(size, MAX_PAGE_SIZE))
    safe_number = max(1, number)
    page = Page(safe_number, safe_size, total)
    if page.number > page.pages:
        return Page(page.pages, safe_size, total)
    return page


def model_count(session, model, tenant_id: str, *criteria) -> int:
    return int(
        session.scalar(
            select(func.count())
            .select_from(model)
            .where(model.tenant_id == tenant_id, *criteria)
        )
        or 0
    )


def _fulfillment_expressions():
    return fulfillment_expressions()


def exception_page(
    session, tenant_id: str, *, page: int = 1, size: int = DEFAULT_PAGE_SIZE
):
    from reality.services.exceptions import operational_exception_rows

    rows = operational_exception_rows(session, tenant_id)
    pager = page_for(len(rows), page, size)
    return rows[pager.offset : pager.offset + pager.size], pager


def exception_count(session, tenant_id: str) -> int:
    from reality.services.exceptions import operational_exceptions

    return len(operational_exceptions(session, tenant_id))


# Compatibility aliases for adapters migrating from the former UI terminology.
issue_page = exception_page
issue_count = exception_count


def commitment_page(
    session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    status: str = "open",
    query: str = "",
    commitment_type: str = "",
    due_from: str = "",
    due_to: str = "",
):
    reserved, _, open_quantity = _fulfillment_expressions()
    counterparty_name = func.coalesce(Party.name, "—")
    item_name = func.coalesce(Item.name, "—")
    criteria: list[Any] = [Commitment.tenant_id == tenant_id]
    if commitment_type:
        criteria.append(Commitment.type == commitment_type)
    if due_from:
        criteria.append(
            func.date(effective_value("due_at")) >= date.fromisoformat(due_from)
        )
    if due_to:
        criteria.append(
            func.date(effective_value("due_at")) <= date.fromisoformat(due_to)
        )
    if status in {"open", "fulfilled", "cancelled"}:
        criteria.append(Commitment.status == status)
    if query:
        pattern = f"%{query.strip().lower()}%"
        criteria.append(
            or_(
                func.lower(Commitment.id).like(pattern),
                func.lower(counterparty_name).like(pattern),
                func.lower(item_name).like(pattern),
            )
        )
    base = (
        select(
            Commitment,
            counterparty_name.label("counterparty"),
            item_name.label("item_name"),
            reserved.label("reserved"),
            open_quantity.label("open_quantity"),
        )
        .outerjoin(
            Party,
            and_(
                Party.tenant_id == Commitment.tenant_id,
                Party.id
                == func.coalesce(Commitment.to_party_id, Commitment.from_party_id),
            ),
        )
        .outerjoin(
            Item,
            and_(Item.tenant_id == Commitment.tenant_id, Item.id == Commitment.item_id),
        )
        .where(*criteria)
    )
    total = int(session.scalar(select(func.count()).select_from(base.subquery())) or 0)
    pager = page_for(total, page, size)
    records = session.execute(
        base.order_by(effective_value("due_at"), Commitment.id)
        .limit(pager.size)
        .offset(pager.offset)
    )
    rows = []
    for commitment, counterparty, item, reserved_value, open_value in records:
        risk = (
            "AT RISK"
            if commitment.type == "customer_delivery"
            and commitment.status == "open"
            and Decimal(reserved_value or 0) < Decimal(open_value or 0)
            else "OK"
        )
        rows.append(
            (
                commitment,
                risk,
                counterparty,
                item,
                Decimal(reserved_value or 0),
                Decimal(open_value or 0),
            )
        )
    return rows, pager


def inventory_page(
    session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    query: str = "",
    item_id: str | None = None,
    stock_state: str = "",
    available_min: Decimal | None = None,
    available_max: Decimal | None = None,
    projected_min: Decimal | None = None,
    projected_max: Decimal | None = None,
    sort: str = "",
    sort_direction: str = "asc",
):
    incoming = (
        select(
            Movement.item_id.label("item_id"), func.sum(Movement.quantity).label("qty")
        )
        .where(Movement.tenant_id == tenant_id, Movement.to_location_id.is_not(None))
        .group_by(Movement.item_id)
        .subquery()
    )
    outgoing = (
        select(
            Movement.item_id.label("item_id"), func.sum(Movement.quantity).label("qty")
        )
        .where(Movement.tenant_id == tenant_id, Movement.from_location_id.is_not(None))
        .group_by(Movement.item_id)
        .subquery()
    )
    reserved = (
        select(
            Reservation.item_id.label("item_id"),
            func.sum(Reservation.quantity).label("qty"),
        )
        .where(Reservation.tenant_id == tenant_id, Reservation.status == "active")
        .group_by(Reservation.item_id)
        .subquery()
    )
    supplier_open = (
        select(
            Commitment.item_id.label("item_id"),
            func.sum(Commitment.quantity).label("qty"),
        )
        .where(
            Commitment.tenant_id == tenant_id,
            Commitment.type == "supplier_delivery",
            Commitment.status == "open",
        )
        .group_by(Commitment.item_id)
        .subquery()
    )
    criteria = [Item.tenant_id == tenant_id]
    if item_id:
        criteria.append(Item.id == item_id)
    if query:
        pattern = f"%{query.strip().lower()}%"
        criteria.append(
            or_(func.lower(Item.name).like(pattern), func.lower(Item.sku).like(pattern))
        )
    physical = func.coalesce(incoming.c.qty, 0) - func.coalesce(outgoing.c.qty, 0)
    reserved_qty = func.coalesce(reserved.c.qty, 0)
    supplier_qty = func.coalesce(supplier_open.c.qty, 0)
    available = physical - reserved_qty
    projected = available + supplier_qty
    if stock_state == "shortage":
        criteria.append(available < 0)
    elif stock_state == "fully_allocated":
        criteria.append(available == 0)
    elif stock_state == "available":
        criteria.append(available > 0)
    for expression, minimum, maximum in (
        (available, available_min, available_max),
        (projected, projected_min, projected_max),
    ):
        if minimum is not None:
            criteria.append(expression >= minimum)
        if maximum is not None:
            criteria.append(expression <= maximum)
    base = (
        select(
            Item,
            physical.label("physical"),
            reserved_qty.label("reserved"),
            supplier_qty.label("supplier_open"),
        )
        .outerjoin(incoming, incoming.c.item_id == Item.id)
        .outerjoin(outgoing, outgoing.c.item_id == Item.id)
        .outerjoin(reserved, reserved.c.item_id == Item.id)
        .outerjoin(supplier_open, supplier_open.c.item_id == Item.id)
        .where(*criteria)
    )
    total = int(session.scalar(select(func.count()).select_from(base.subquery())) or 0)
    pager = page_for(total, page, size)
    records = session.execute(
        base.order_by(
            *query_order(
                sort,
                sort_direction,
                {
                    "id": Item.id,
                    "name": Item.name,
                    "physical": physical,
                    "reserved": reserved_qty,
                    "available": available,
                },
                Item.id,
                (
                    Item.name,
                    Item.id,
                ),
            )
        )
        .limit(pager.size)
        .offset(pager.offset)
    )
    rows = []
    for item, physical, reserved_value, supplier_value in records:
        physical, reserved_value, supplier_value = (
            Decimal(value or 0) for value in (physical, reserved_value, supplier_value)
        )
        available = physical - reserved_value
        rows.append(
            {
                "item": item,
                "physical": physical,
                "reserved": reserved_value,
                "available": available,
                "incoming": supplier_value,
                "projected": available + supplier_value,
                "receipts": [],
                "issues": [],
            }
        )
    return rows, pager


def document_page(
    session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    query: str = "",
    document_type: str = "",
    date_from: str = "",
    date_to: str = "",
    status: str = "",
    source_system: str = "",
    source_record_id: str = "",
    amount_min: Decimal | None = None,
    amount_max: Decimal | None = None,
    sort: str = "",
    sort_direction: str = "asc",
):
    criteria = [Document.tenant_id == tenant_id]
    if source_record_id:
        criteria.append(Document.source_record_id == source_record_id)
    if document_type:
        criteria.append(Document.type == document_type)
    if date_from:
        criteria.append(Document.document_date >= as_day(date_from))
    if date_to:
        criteria.append(Document.document_date <= as_day(date_to))
    if status:
        criteria.append(Document.status == status)
    if source_system:
        criteria.append(
            Document.source_record_id.in_(
                select(SourceRecord.id).where(
                    SourceRecord.tenant_id == tenant_id,
                    SourceRecord.source_system == source_system,
                )
            )
        )
    if amount_min is not None:
        criteria.append(Document.gross_amount >= amount_min)
    if amount_max is not None:
        criteria.append(Document.gross_amount <= amount_max)
    if query:
        pattern = f"%{query.strip().lower()}%"
        criteria.append(
            or_(
                func.lower(Document.number).like(pattern),
                func.lower(Document.id).like(pattern),
                func.lower(Document.party_id).like(pattern),
                func.lower(Document.type).like(pattern),
                func.lower(Document.status).like(pattern),
                Document.source_record_id.in_(
                    select(SourceRecord.id).where(
                        SourceRecord.tenant_id == tenant_id,
                        or_(
                            func.lower(SourceRecord.source_system).like(pattern),
                            func.lower(SourceRecord.source_type).like(pattern),
                            func.lower(SourceRecord.external_id).like(pattern),
                        ),
                    )
                ),
            )
        )
    total = int(
        session.scalar(select(func.count()).select_from(Document).where(*criteria)) or 0
    )
    pager = page_for(total, page, size)
    documents = list(
        session.scalars(
            select(Document)
            .where(*criteria)
            .order_by(
                *query_order(
                    sort,
                    sort_direction,
                    {
                        "id": Document.id,
                        "number": Document.number,
                        "date": Document.document_date,
                        "type": Document.type,
                        "status": Document.status,
                        "amount": Document.gross_amount,
                        "currency": Document.currency,
                    },
                    Document.id,
                    (
                        Document.document_date.desc(),
                        Document.id.desc(),
                    ),
                )
            )
            .limit(pager.size)
            .offset(pager.offset)
        )
    )
    document_ids = [row.id for row in documents]
    source_ids = [row.source_record_id for row in documents if row.source_record_id]
    sources = (
        {
            row.id: row
            for row in session.scalars(
                select(SourceRecord).where(
                    SourceRecord.tenant_id == tenant_id, SourceRecord.id.in_(source_ids)
                )
            )
        }
        if source_ids
        else {}
    )
    lines: dict[str, list[DocumentLine]] = {record_id: [] for record_id in document_ids}
    for line in (
        session.scalars(
            select(DocumentLine).where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id.in_(document_ids),
            )
        )
        if document_ids
        else []
    ):
        lines[line.document_id].append(line)
    commitments: dict[str, list[Commitment]] = {
        record_id: [] for record_id in document_ids
    }
    for commitment in (
        session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id.in_(document_ids),
            )
        )
        if document_ids
        else []
    ):
        commitments[commitment.document_id].append(commitment)
    return [
        (row, sources.get(row.source_record_id), lines[row.id], commitments[row.id])
        for row in documents
    ], pager


def entity_page(
    session,
    model,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    query: str = "",
    search_columns: tuple = (),
    order_columns: tuple = (),
    criteria: tuple = (),
):
    filters = [model.tenant_id == tenant_id, *criteria]
    if query and search_columns:
        pattern = f"%{query.strip().lower()}%"
        filters.append(
            or_(*(func.lower(column).like(pattern) for column in search_columns))
        )
    total = int(
        session.scalar(select(func.count()).select_from(model).where(*filters)) or 0
    )
    pager = page_for(total, page, size)
    ordering = order_columns or (model.id,)
    rows = list(
        session.scalars(
            select(model)
            .where(*filters)
            .order_by(*ordering)
            .limit(pager.size)
            .offset(pager.offset)
        )
    )
    return rows, pager


def _records_by_id(session, model, tenant_id: str, record_ids: set[str | None]):
    ids = {record_id for record_id in record_ids if record_id}
    if not ids:
        return {}
    return {
        row.id: row
        for row in session.scalars(
            select(model).where(model.tenant_id == tenant_id, model.id.in_(ids))
        )
    }


def reservation_page(
    session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    query: str = "",
    item_id: str | None = None,
    status: str = "",
    date_from: str = "",
    date_to: str = "",
    sort: str = "",
    sort_direction: str = "asc",
):
    criteria = []
    if item_id:
        criteria.append(Reservation.item_id == item_id)
    if status:
        criteria.append(Reservation.status == status)
    if date_from:
        criteria.append(
            func.date(Reservation.reserved_at) >= date.fromisoformat(date_from)
        )
    if date_to:
        criteria.append(
            func.date(Reservation.reserved_at) <= date.fromisoformat(date_to)
        )
    records, pager = entity_page(
        session,
        Reservation,
        tenant_id,
        page=page,
        size=size,
        query=query,
        search_columns=(
            Reservation.id,
            Reservation.commitment_id,
            Reservation.item_id,
            Reservation.location_id,
            Reservation.handling_unit_id,
            Reservation.lot_id,
            Reservation.serial_unit_id,
        ),
        criteria=tuple(criteria),
        order_columns=query_order(
            sort,
            sort_direction,
            {
                "id": Reservation.id,
                "date": Reservation.reserved_at,
                "quantity": Reservation.quantity,
                "status": Reservation.status,
            },
            Reservation.id,
            (
                Reservation.reserved_at.desc(),
                Reservation.id.desc(),
            ),
        ),
    )
    items = _records_by_id(session, Item, tenant_id, {row.item_id for row in records})
    locations = _records_by_id(
        session, Location, tenant_id, {row.location_id for row in records}
    )
    handling_units = _records_by_id(
        session, HandlingUnit, tenant_id, {row.handling_unit_id for row in records}
    )
    lots = _records_by_id(session, Lot, tenant_id, {row.lot_id for row in records})
    serials = _records_by_id(
        session, SerialUnit, tenant_id, {row.serial_unit_id for row in records}
    )
    return [
        {
            "reservation": row,
            "item": items.get(row.item_id),
            "location": locations.get(row.location_id),
            "handling_unit": handling_units.get(row.handling_unit_id),
            "lot": lots.get(row.lot_id),
            "serial_unit": serials.get(row.serial_unit_id),
        }
        for row in records
    ], pager


def movement_page(
    session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    query: str = "",
    item_id: str | None = None,
    movement_type: str = "",
    date_from: str = "",
    date_to: str = "",
    sort: str = "",
    sort_direction: str = "asc",
):
    criteria = []
    if item_id:
        criteria.append(Movement.item_id == item_id)
    if movement_type:
        criteria.append(Movement.type == movement_type)
    if date_from:
        criteria.append(
            func.date(Movement.occurred_at) >= date.fromisoformat(date_from)
        )
    if date_to:
        criteria.append(func.date(Movement.occurred_at) <= date.fromisoformat(date_to))
    records, pager = entity_page(
        session,
        Movement,
        tenant_id,
        page=page,
        size=size,
        query=query,
        search_columns=(
            Movement.id,
            Movement.item_id,
            Movement.from_location_id,
            Movement.to_location_id,
            Movement.handling_unit_id,
            Movement.lot_id,
            Movement.serial_unit_id,
        ),
        criteria=tuple(criteria),
        order_columns=query_order(
            sort,
            sort_direction,
            {
                "id": Movement.id,
                "date": Movement.occurred_at,
                "quantity": Movement.quantity,
                "type": Movement.type,
            },
            Movement.id,
            (
                Movement.occurred_at.desc(),
                Movement.id.desc(),
            ),
        ),
    )
    items = _records_by_id(session, Item, tenant_id, {row.item_id for row in records})
    location_ids = {row.from_location_id for row in records} | {
        row.to_location_id for row in records
    }
    locations = _records_by_id(session, Location, tenant_id, location_ids)
    handling_units = _records_by_id(
        session, HandlingUnit, tenant_id, {row.handling_unit_id for row in records}
    )
    lots = _records_by_id(session, Lot, tenant_id, {row.lot_id for row in records})
    serials = _records_by_id(
        session, SerialUnit, tenant_id, {row.serial_unit_id for row in records}
    )
    return [
        {
            "movement": row,
            "item": items.get(row.item_id),
            "from_location": locations.get(row.from_location_id),
            "to_location": locations.get(row.to_location_id),
            "handling_unit": handling_units.get(row.handling_unit_id),
            "lot": lots.get(row.lot_id),
            "serial_unit": serials.get(row.serial_unit_id),
        }
        for row in records
    ], pager


def journal_page(
    session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    query: str = "",
    account: str = "",
    side: str = "",
    date_from: str = "",
    date_to: str = "",
    sort: str = "",
    sort_direction: str = "asc",
):
    criteria: list[Any] = []
    if account:
        criteria.append(LedgerEntry.account == account)
    if side:
        criteria.append(LedgerEntry.debit_credit == side)
    if date_from:
        criteria.append(
            func.date(LedgerEntry.effective_at) >= date.fromisoformat(date_from)
        )
    if date_to:
        criteria.append(
            func.date(LedgerEntry.effective_at) <= date.fromisoformat(date_to)
        )
    rows, pager = entity_page(
        session,
        LedgerEntry,
        tenant_id,
        page=page,
        size=size,
        query=query,
        search_columns=(
            LedgerEntry.id,
            LedgerEntry.posting_group_id,
            LedgerEntry.account,
            LedgerEntry.party_id,
            LedgerEntry.document_id,
            LedgerEntry.source_record_id,
        ),
        criteria=tuple(criteria),
        order_columns=query_order(
            sort,
            sort_direction,
            {
                "id": LedgerEntry.id,
                "date": LedgerEntry.effective_at,
                "amount": LedgerEntry.amount,
                "currency": LedgerEntry.currency,
                "account": LedgerEntry.account,
                "side": LedgerEntry.debit_credit,
            },
            LedgerEntry.id,
            (
                LedgerEntry.effective_at.desc(),
                LedgerEntry.id.desc(),
            ),
        ),
    )
    aggregate_criteria: list[Any] = [LedgerEntry.tenant_id == tenant_id, *criteria]
    if query:
        pattern = f"%{query.strip().lower()}%"
        aggregate_criteria.append(
            or_(
                func.lower(LedgerEntry.id).like(pattern),
                func.lower(LedgerEntry.posting_group_id).like(pattern),
                func.lower(LedgerEntry.account).like(pattern),
                func.lower(func.coalesce(LedgerEntry.party_id, "")).like(pattern),
                func.lower(func.coalesce(LedgerEntry.document_id, "")).like(pattern),
                func.lower(func.coalesce(LedgerEntry.source_record_id, "")).like(
                    pattern
                ),
            )
        )
    totals = list(
        session.execute(
            select(
                LedgerEntry.currency,
                func.coalesce(
                    func.sum(
                        case(
                            (LedgerEntry.debit_credit == "debit", LedgerEntry.amount),
                            else_=0,
                        )
                    ),
                    0,
                ).label("debit"),
                func.coalesce(
                    func.sum(
                        case(
                            (LedgerEntry.debit_credit == "credit", LedgerEntry.amount),
                            else_=0,
                        )
                    ),
                    0,
                ).label("credit"),
            )
            .where(*aggregate_criteria)
            .group_by(LedgerEntry.currency)
            .order_by(LedgerEntry.currency)
        )
    )
    return rows, pager, totals


def payment_page(
    session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    query: str = "",
    direction: str = "",
    date_from: str = "",
    date_to: str = "",
    sort: str = "",
    sort_direction: str = "asc",
):
    criteria = [LedgerEntry.account == "cash"]
    if direction == "incoming":
        criteria.append(LedgerEntry.debit_credit == "debit")
    elif direction == "outgoing":
        criteria.append(LedgerEntry.debit_credit == "credit")
    if date_from:
        criteria.append(
            func.date(LedgerEntry.effective_at) >= date.fromisoformat(date_from)
        )
    if date_to:
        criteria.append(
            func.date(LedgerEntry.effective_at) <= date.fromisoformat(date_to)
        )
    cash_entries, pager = entity_page(
        session,
        LedgerEntry,
        tenant_id,
        page=page,
        size=size,
        query=query,
        search_columns=(
            LedgerEntry.id,
            LedgerEntry.posting_group_id,
            LedgerEntry.party_id,
            LedgerEntry.document_id,
        ),
        criteria=tuple(criteria),
        order_columns=query_order(
            sort,
            sort_direction,
            {
                "id": LedgerEntry.id,
                "date": LedgerEntry.effective_at,
                "amount": LedgerEntry.amount,
                "currency": LedgerEntry.currency,
            },
            LedgerEntry.id,
            (
                LedgerEntry.effective_at.desc(),
                LedgerEntry.id.desc(),
            ),
        ),
    )
    posting_groups = {row.posting_group_id for row in cash_entries}
    controls = (
        {
            row.posting_group_id: row
            for row in session.scalars(
                select(LedgerEntry).where(
                    LedgerEntry.tenant_id == tenant_id,
                    LedgerEntry.posting_group_id.in_(posting_groups),
                    LedgerEntry.account.in_(
                        ("accounts_receivable", "accounts_payable")
                    ),
                )
            )
        }
        if posting_groups
        else {}
    )
    control_ids = {row.id for row in controls.values()}
    controls_by_id = {row.id: row for row in controls.values()}
    allocations = (
        list(
            session.scalars(
                select(SettlementAllocation).where(
                    SettlementAllocation.tenant_id == tenant_id,
                    SettlementAllocation.payment_ledger_entry_id.in_(control_ids),
                )
            )
        )
        if control_ids
        else []
    )
    invoice_entries = _records_by_id(
        session,
        LedgerEntry,
        tenant_id,
        {row.invoice_ledger_entry_id for row in allocations},
    )
    relevant_groups = posting_groups | {
        entry.posting_group_id for entry in invoice_entries.values()
    }
    reversals = (
        list(
            session.scalars(
                select(LedgerReversal).where(
                    LedgerReversal.tenant_id == tenant_id,
                    or_(
                        LedgerReversal.original_posting_group_id.in_(relevant_groups),
                        LedgerReversal.reversing_posting_group_id.in_(relevant_groups),
                    ),
                )
            )
        )
        if relevant_groups
        else []
    )
    reversed_groups = {row.original_posting_group_id for row in reversals}
    allocated = {
        payment_id: sum(
            (
                Decimal(row.amount)
                for row in allocations
                if row.payment_ledger_entry_id == payment_id
                and controls_by_id[payment_id].posting_group_id not in reversed_groups
                and invoice_entries[row.invoice_ledger_entry_id].posting_group_id
                not in reversed_groups
            ),
            ZERO,
        )
        for payment_id in control_ids
    }
    reversal_roles = {
        group_id: role
        for relation in reversals
        for group_id, role in (
            (relation.original_posting_group_id, "reversed_original"),
            (relation.reversing_posting_group_id, "reversing"),
        )
    }
    documents = _records_by_id(
        session, Document, tenant_id, {row.document_id for row in cash_entries}
    )
    parties = _records_by_id(
        session, Party, tenant_id, {row.party_id for row in cash_entries}
    )
    rows = []
    for cash in cash_entries:
        control = controls.get(cash.posting_group_id)
        if control is None or cash.document_id not in documents:
            continue
        allocated_value = allocated.get(control.id, ZERO)
        rows.append(
            {
                "cash_entry": cash,
                "control_entry": control,
                "document": documents[cash.document_id],
                "party": parties[cash.party_id].name
                if cash.party_id in parties
                else "—",
                "direction": "incoming" if cash.debit_credit == "debit" else "outgoing",
                "allocated": allocated_value,
                "unallocated": ZERO
                if reversal_roles.get(cash.posting_group_id) == "reversed_original"
                else Decimal(cash.amount) - allocated_value,
                "reversal_role": reversal_roles.get(cash.posting_group_id, "normal"),
            }
        )
    return rows, pager


def open_item_page(
    session, tenant_id: str, *, page: int = 1, size: int = DEFAULT_PAGE_SIZE
):
    from reality.services.core import InvalidOperation, open_invoice_amount

    documents, pager = entity_page(
        session,
        Document,
        tenant_id,
        page=page,
        size=size,
        criteria=(Document.type.in_(("sales_invoice", "supplier_invoice")),),
        order_columns=(Document.document_date.desc(), Document.id.desc()),
    )
    parties = _records_by_id(
        session, Party, tenant_id, {row.party_id for row in documents}
    )
    rows = []
    for document in documents:
        try:
            open_amount = open_invoice_amount(session, tenant_id, document.id)
        except InvalidOperation:
            continue
        gross = Decimal(document.gross_amount)
        rows.append(
            {
                "document": document,
                "party": parties[document.party_id].name
                if document.party_id in parties
                else "—",
                "party_payment_term_id": parties[document.party_id].payment_term_id
                if document.party_id in parties
                else None,
                "open": open_amount,
                "settled": gross - open_amount,
                "status": "paid"
                if open_amount == ZERO
                else "partial"
                if open_amount < gross
                else "open",
            }
        )
    return rows, pager


# Default order of a projection register when the caller does not sort explicitly.
# Document registers show the newest document first; other projections keep the
# stable record-key order. Work queues (commitments) are ordered by due date elsewhere.
PROJECTION_DEFAULT_ORDER: dict[str, tuple[str, str]] = {
    OPEN_FINANCIAL_ITEMS: ("date", "desc"),
}


@_read_without_flush
def projection_page(
    session,
    tenant_id: str,
    projection_name: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    query: str = "",
    readiness: str = "",
    source_system: str = "",
    date_from: str = "",
    date_to: str = "",
    status: str = "",
    flow: str = "",
    party_id: str = "",
    amount_min: Decimal | None = None,
    amount_max: Decimal | None = None,
    sort: str = "",
    sort_direction: str = "asc",
    amount_fields: tuple[str, ...] = (),
    with_metadata: bool = False,
):
    """One SQL snapshot for completed rows, count, totals and freshness."""
    from reality.services.core import NotFound

    if projection_name not in MATERIALIZED_PROJECTIONS:
        raise ValueError("Unknown stored projection.")
    size = max(1, min(size, MAX_PAGE_SIZE))
    page = max(1, page)
    if not sort:
        sort, sort_direction = PROJECTION_DEFAULT_ORDER.get(
            projection_name, ("", "asc")
        )
    criteria = [
        ProjectionRow.tenant_id == tenant_id,
        ProjectionRow.projection_name == projection_name,
    ]
    value = lambda key: projection_payload_text(session, key)
    if query:
        pattern = f"%{query.strip().lower()}%"
        criteria.append(
            or_(
                func.lower(ProjectionRow.record_key).like(pattern),
                func.lower(ProjectionRow.payload).like(pattern),
            )
        )
    if readiness:
        criteria.append(value("readiness") == readiness)
    if source_system:
        criteria.append(value("source_system") == source_system)
    if status == "outstanding":
        criteria.append(value("status").in_(("open", "partial")))
    elif status:
        criteria.append(value("status") == status)
    if flow:
        criteria.append(value("flow") == flow)
    if party_id:
        criteria.append(value("party_id") == party_id)
    date_value = func.date(func.coalesce(value("due_at"), value("document_date")))
    if date_from:
        criteria.append(date_value >= date.fromisoformat(date_from))
    if date_to:
        criteria.append(date_value <= date.fromisoformat(date_to))
    amount_value = cast(func.coalesce(value("open"), value("gross")), Numeric(18, 4))
    if amount_min is not None:
        criteria.append(amount_value >= amount_min)
    if amount_max is not None:
        criteria.append(amount_value <= amount_max)
    order = query_order(
        sort,
        sort_direction,
        {
            "id": ProjectionRow.record_key,
            "number": value("number"),
            "party": value("party"),
            "date": value("document_date"),
            "status": value("status"),
            "gross": cast(value("gross"), Numeric(18, 4)),
            "settled": cast(value("settled"), Numeric(18, 4)),
            "open": cast(value("open"), Numeric(18, 4)),
        },
        ProjectionRow.record_key,
        (ProjectionRow.record_key,),
    )
    filtered = (
        select(
            ProjectionRow.payload.label("payload"),
            func.row_number().over(order_by=order).label("position"),
        )
        .where(*criteria)
        .cte("filtered_projection")
    )
    total = select(func.count()).select_from(filtered).scalar_subquery()
    last_page = func.greatest(1, func.ceil(cast(total, Numeric) / size))
    offset = cast((func.least(page, last_page) - 1) * size, Integer)
    visible = (
        select(filtered.c.payload, filtered.c.position)
        .where(
            filtered.c.position > offset,
            filtered.c.position <= offset + size,
        )
        .order_by(filtered.c.position)
        .limit(size)
        .subquery()
    )
    from sqlalchemy.dialects.postgresql import aggregate_order_by

    items = select(
        func.json_agg(
            aggregate_order_by(cast(visible.c.payload, JSONB), visible.c.position)
        )
    ).scalar_subquery()
    columns = [items.label("items"), total.label("total")]
    if amount_fields:
        payload = cast(filtered.c.payload, JSONB)
        currency = payload["currency"].astext
        grouped = (
            select(
                currency.label("currency"),
                *[
                    cast(
                        func.coalesce(
                            func.sum(cast(payload[field].astext, Numeric(18, 4))), 0
                        ),
                        Text,
                    ).label(field)
                    for field in amount_fields
                ],
            )
            .group_by(currency)
            .subquery()
        )
        fields = ["currency", grouped.c.currency]
        for field in amount_fields:
            fields.extend([field, grouped.c[field]])
        columns.append(
            select(func.json_agg(func.json_build_object(*fields)))
            .scalar_subquery()
            .label("totals")
        )
    columns.extend(
        value.label(key)
        for key, value in projection_state_expressions(
            tenant_id, projection_name
        ).items()
    )
    response = (
        session.execute(select(*columns).where(Tenant.id == tenant_id))
        .mappings()
        .first()
    )
    if response is None:
        raise NotFound("Tenant not found.")
    pager = page_for(response["total"], page, size)
    rows = response["items"] or []
    if not with_metadata:
        return rows, pager
    return {
        "items": rows,
        "page": {
            "number": pager.number,
            "size": pager.size,
            "total": pager.total,
            "pages": pager.pages,
            "has_previous": pager.has_previous,
            "has_next": pager.has_next,
        },
        "metadata": projection_metadata(projection_name, response),
        **({"totals": response["totals"] or []} if amount_fields else {}),
    }


@_read_without_flush
def projection_totals(
    session,
    tenant_id: str,
    projection_name: str,
    amount_fields: tuple[str, ...],
    *,
    query: str = "",
    payload_filters: dict[str, str] | None = None,
):
    """Aggregate a complete filtered projection without using the visible page."""
    value = lambda key: projection_payload_text(session, key)
    criteria: list[Any] = [
        ProjectionRow.tenant_id == tenant_id,
        ProjectionRow.projection_name == projection_name,
    ]
    if query:
        pattern = f"%{query.strip().lower()}%"
        criteria.append(
            or_(
                func.lower(ProjectionRow.record_key).like(pattern),
                func.lower(ProjectionRow.payload).like(pattern),
            )
        )
    for key, expected in (payload_filters or {}).items():
        if key == "status" and expected == "outstanding":
            criteria.append(value(key).in_(("open", "partial")))
        elif expected:
            criteria.append(value(key) == expected)
    filtered = (
        select(
            value("currency").label("currency"),
            *[
                cast(value(field), Numeric(18, 4)).label(field)
                for field in amount_fields
            ],
        )
        .where(*criteria)
        .subquery()
    )
    columns = [
        func.coalesce(func.sum(filtered.c[field]), 0).label(field)
        for field in amount_fields
    ]
    return list(
        session.execute(
            select(filtered.c.currency, *columns)
            .group_by(filtered.c.currency)
            .order_by(filtered.c.currency)
        )
    )


def aging_page(
    session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    as_of: datetime | None = None,
):
    from reality.services.core import with_invoice_aging

    rows, pager = open_item_page(session, tenant_id, page=page, size=size)
    term_ids = {
        term_id
        for row in rows
        for term_id in (
            row["document"].payment_term_id,
            row["party_payment_term_id"],
        )
        if term_id
    }
    terms = _records_by_id(session, PaymentTerm, tenant_id, term_ids)
    return with_invoice_aging(rows, terms, as_of or datetime.now(UTC)), pager


@_read_without_flush
def payment_totals(session, tenant_id: str, *, query: str = "", direction: str = ""):
    """Live totals from the canonical payment derivation, using page filters."""
    from collections import defaultdict

    from reality.services.core import payment_rows

    totals = defaultdict(lambda: [ZERO, ZERO, ZERO])
    query = query.strip().lower()
    for row in payment_rows(session, tenant_id):
        cash = row["cash_entry"]
        if direction and row["direction"] != direction:
            continue
        if query and not any(
            query in str(value or "").lower()
            for value in (
                cash.id,
                cash.posting_group_id,
                cash.party_id,
                cash.document_id,
            )
        ):
            continue
        total = totals[cash.currency]
        for index, value in enumerate(
            (cash.amount, row["allocated"], row["unallocated"])
        ):
            total[index] += value
    from types import SimpleNamespace

    return [
        SimpleNamespace(
            currency=currency,
            amount=amounts[0],
            allocated=amounts[1],
            unallocated=amounts[2],
        )
        for currency, amounts in sorted(totals.items())
    ]
