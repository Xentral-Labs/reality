from __future__ import annotations

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
from reality.db.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Page, page_for
from reality.db.query_order import query_order
from reality.domain.calendar import as_day
from reality.domain.stock_scope import movement_at, reservation_at
from reality.services.delivery_reads import effective_value, fulfillment_expressions
from reality.services.projections import (
    MATERIALIZED_PROJECTIONS,
    OPEN_FINANCIAL_ITEMS,
    _read_without_flush,
    projection_metadata,
    projection_state_expressions,
)

ZERO = Decimal(0)


def projection_payload_text(session, key: str):
    """Return one text value from a materialized projection payload."""
    return cast(ProjectionRow.payload, JSONB)[key].astext


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
    """
    BUSINESS PURPOSE:
    Reuse the shared delivery-quantity formulas when displaying the promise register.

    BUSINESS RULE web.read_models._fulfillment_expressions.shared_formulas:
    Read reserved, fulfilled and open quantities from reality.services.delivery_reads.fulfillment_expressions. This web adapter does not implement a second fulfillment calculation.
    """
    # reality-rule: web.read_models._fulfillment_expressions.shared_formulas
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


def _local_day(session, tenant_id: str, column):
    """A stored instant as the company's business day, in SQL (spec 349).

    A register filtered by day shows what happened on that day in the company's
    own calendar, not on the UTC day.
    """
    from reality.services.company_time_zone import _zone_name

    utc = func.timezone("UTC", column)
    # A stated day travels as midnight UTC and keeps its day, as in Python.
    return func.date(
        case(
            (utc == func.date_trunc("day", utc), utc),
            else_=func.timezone(_zone_name(session, tenant_id), column),
        )
    )


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
    """
    BUSINESS PURPOSE:
    Read a filtered page of this company's delivery promises with active reservations, remaining delivery quantity and reservation-shortage risk.

    BUSINESS RULE web.read_models.commitment_page.company_scope:
    Select promises only from the requested company. Joined partner and item names remain company-scoped; missing names display as a dash. The partner join prefers the receiving partner and falls back to the supplying partner.

    BUSINESS RULE web.read_models.commitment_page.type_filter:
    IF a promise type was selected:
        Include only that type. Without a type filter, this reader does not restrict promise type.

    BUSINESS RULE web.read_models.commitment_page.due_from:
    IF a start date was supplied:
        Include promises whose effective due date is on or after that date. Use the latest stated due-date revision.

    BUSINESS RULE web.read_models.commitment_page.due_to:
    IF an end date was supplied:
        Include promises whose effective due date is on or before that date.

    BUSINESS RULE web.read_models.commitment_page.status_filter:
    IF status is open, fulfilled or cancelled:
        Include only promises with that stored promise status. Other status values add no status restriction; this filter does not itself recalculate status from open quantity.

    BUSINESS RULE web.read_models.commitment_page.search:
    IF search text was supplied:
        Match it within the promise identity, counterparty name or item name, ignoring case and surrounding whitespace.

    BUSINESS RULE web.read_models.commitment_page.page_order:
    Count the complete filtered result, apply the shared page bounds, then read the selected page ordered by effective due date and promise identity.

    BUSINESS RULE web.read_models.commitment_page.reservation_risk:
    IF a customer-delivery promise is open AND active reserved quantity is less than its remaining delivery quantity:
        Mark it AT RISK.
    ELSE:
        Mark it OK. This indicator compares reservations with open quantity; it does not prove physical stock or shipment readiness.

    BUSINESS RULE web.read_models.commitment_page.result:
    Return the page's promise records, reservation-risk indicator, counterparty and item names, reserved quantity, open quantity and pagination evidence.
    """
    reserved, _, open_quantity = _fulfillment_expressions()
    counterparty_name = func.coalesce(Party.name, "—")
    item_name = func.coalesce(Item.name, "—")
    # reality-rule: web.read_models.commitment_page.company_scope
    criteria: list[Any] = [Commitment.tenant_id == tenant_id]
    # reality-rule: web.read_models.commitment_page.type_filter
    if commitment_type:
        criteria.append(Commitment.type == commitment_type)
    # reality-rule: web.read_models.commitment_page.due_from
    if due_from:
        criteria.append(
            _local_day(session, tenant_id, effective_value("due_at"))
            >= date.fromisoformat(due_from)
        )
    # reality-rule: web.read_models.commitment_page.due_to
    if due_to:
        criteria.append(
            _local_day(session, tenant_id, effective_value("due_at"))
            <= date.fromisoformat(due_to)
        )
    # reality-rule: web.read_models.commitment_page.status_filter
    if status in {"open", "fulfilled", "cancelled"}:
        criteria.append(Commitment.status == status)
    # reality-rule: web.read_models.commitment_page.search
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
    # reality-rule: web.read_models.commitment_page.page_order
    records = session.execute(
        base.order_by(effective_value("due_at"), Commitment.id)
        .limit(pager.size)
        .offset(pager.offset)
    )
    rows = []
    for commitment, counterparty, item, reserved_value, open_value in records:
        # reality-rule: web.read_models.commitment_page.reservation_risk
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
    # reality-rule: web.read_models.commitment_page.result
    return rows, pager


def inventory_page(
    session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    query: str = "",
    item_id: str | None = None,
    location_id: str | None = None,
    stock_state: str = "",
    available_min: Decimal | None = None,
    available_max: Decimal | None = None,
    projected_min: Decimal | None = None,
    projected_max: Decimal | None = None,
    sort: str = "",
    sort_direction: str = "asc",
) -> tuple[list[dict[str, Any]], Page]:
    from reality.services.inventory_reads import inventory_page as read_inventory_page

    return read_inventory_page(
        session,
        tenant_id,
        page=page,
        size=size,
        query=query,
        item_id=item_id,
        location_id=location_id,
        stock_state=stock_state,
        available_min=available_min,
        available_max=available_max,
        projected_min=projected_min,
        projected_max=projected_max,
        sort=sort,
        sort_direction=sort_direction,
    )


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
    location_id: str | None = None,
    status: str = "",
    date_from: str = "",
    date_to: str = "",
    sort: str = "",
    sort_direction: str = "asc",
):
    criteria = []
    if item_id:
        criteria.append(Reservation.item_id == item_id)
    if location_id:
        criteria.append(reservation_at(location_id))
    if status:
        criteria.append(Reservation.status == status)
    if date_from:
        criteria.append(
            _local_day(session, tenant_id, Reservation.reserved_at)
            >= date.fromisoformat(date_from)
        )
    if date_to:
        criteria.append(
            _local_day(session, tenant_id, Reservation.reserved_at)
            <= date.fromisoformat(date_to)
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
    location_id: str | None = None,
    movement_type: str = "",
    date_from: str = "",
    date_to: str = "",
    sort: str = "",
    sort_direction: str = "asc",
):
    criteria = []
    if item_id:
        criteria.append(Movement.item_id == item_id)
    if location_id:
        criteria.append(movement_at(location_id))
    if movement_type:
        criteria.append(Movement.type == movement_type)
    if date_from:
        criteria.append(
            _local_day(session, tenant_id, Movement.occurred_at)
            >= date.fromisoformat(date_from)
        )
    if date_to:
        criteria.append(
            _local_day(session, tenant_id, Movement.occurred_at)
            <= date.fromisoformat(date_to)
        )
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
            _local_day(session, tenant_id, LedgerEntry.effective_at)
            >= date.fromisoformat(date_from)
        )
    if date_to:
        criteria.append(
            _local_day(session, tenant_id, LedgerEntry.effective_at)
            <= date.fromisoformat(date_to)
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
            _local_day(session, tenant_id, LedgerEntry.effective_at)
            >= date.fromisoformat(date_from)
        )
    if date_to:
        criteria.append(
            _local_day(session, tenant_id, LedgerEntry.effective_at)
            <= date.fromisoformat(date_to)
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
    from reality.domain.finance import OPEN_ITEM_TYPES
    from reality.services.core import financial_open_items

    documents, pager = entity_page(
        session,
        Document,
        tenant_id,
        page=page,
        size=size,
        criteria=(Document.type.in_(OPEN_ITEM_TYPES),),
        order_columns=(Document.document_date.desc(), Document.id.desc()),
    )
    rows = financial_open_items(
        session, tenant_id, document_ids={row.id for row in documents}
    )
    by_id = {row["document"].id: row for row in rows}
    return [by_id[document.id] for document in documents if document.id in by_id], pager


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
    overdue: bool = False,
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
    if overdue:
        if projection_name != OPEN_FINANCIAL_ITEMS:
            raise ValueError(
                "Overdue filtering requires the financial open-item reader."
            )
        from reality.services.finance.worklists import overdue_document_ids

        criteria.append(
            ProjectionRow.record_key.in_(overdue_document_ids(session, tenant_id))
        )
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
    from reality.services.company_time_zone import company_day

    today = company_day(session, tenant_id, as_of or datetime.now(UTC))
    return with_invoice_aging(rows, terms, today), pager


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
