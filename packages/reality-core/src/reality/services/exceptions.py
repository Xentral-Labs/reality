from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from itertools import pairwise
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from reality.db.core import (
    Commitment,
    CommitmentHold,
    Document,
    DocumentLine,
    ImportJob,
    Item,
    LedgerEntry,
    Location,
    Movement,
    MovementCorrection,
    Party,
    PartyHold,
    PriceList,
    PriceListEntry,
    Reservation,
    SourceCapability,
    SourceRecord,
    SourceSystem,
    Tenant,
)
from reality.services.exception_inputs import _exception_input_scope, _inputs

ZERO = Decimal(0)
# A source is judged against the rhythm it has shown itself, never against a
# configured interval. These four constants turn that history into a judgement
# and are the same for every tenant. They are deliberately set to fail late: a
# condition that cries wolf on a healthy source is worse than one that notices a
# day later.
SILENT_SOURCE_HISTORY = 20  # most recent arrivals considered
SILENT_SOURCE_MIN_HISTORY = 5  # below this, no rhythm is claimed at all
SILENT_SOURCE_MULTIPLE = 2  # of the longest pause the source has shown
SILENT_SOURCE_FLOOR = timedelta(hours=24)  # never report a shorter silence
# How long is long here is answered the way Spec 072 answers it for a silent
# source: from what this tenant has actually done, never from a setting. The
# statistic differs, and deliberately. A source's longest pause is bounded by
# nights and weekends, so the longest is safe there; an order's lag has no upper
# bound, and one order that took eight months would silence the class forever.
# A median moves with the business and no single case can capture it.
#
# These are product decisions, identical for every tenant, and none of them has
# been checked against a real business yet.
LEARNED_HISTORY = 20  # most recent completed cases considered
LEARNED_MINIMUM = 5  # below this no norm is claimed at all
LEARNED_MULTIPLE = 3  # two is inside normal variation; three is a statement
STALLED_ORDER_FLOOR = timedelta(days=7)  # a week is the shortest "stuck"
UNBILLED_RECEIPT_FLOOR = timedelta(days=14)  # an invoice inside a fortnight is ordinary
UNRESOLVED_RETURN_FLOOR = timedelta(
    days=14
)  # a fortnight to look at a return is ordinary
# Matched to the floor above on purpose: a fortnight for a parcel to travel is
# ordinary, and the two halves of a return's life should not disagree about what
# ordinary means.
UNARRIVED_ANNOUNCEMENT_FLOOR = timedelta(days=14)
# A hold is an active statement that somebody is on it, so a few days is
# ordinary and a week is the shortest span in which "forgotten" means anything.
# Matched to the stalled-order floor for the same reason.
UNLIFTED_HOLD_FLOOR = timedelta(days=7)
CREDIT_POSTING_FLOOR = timedelta(days=14)  # a fortnight to book one's own paperwork
SEVERITY_ORDER = {"critical": 0, "high": 1, "normal": 2, "low": 3}
CLASS_ORDER = {
    "overdue_outgoing_customer_commitment": 0,
    "outgoing_commitment_at_risk": 1,
    "order_stalled": 2,
    "overdue_incoming_supplier_commitment": 3,
    "shipped_not_billed": 4,
    "billed_not_received": 5,
    "invoice_price_differs": 6,
    "sold_below_purchase_price": 7,
    "returned_not_credited": 8,
    "credited_not_returned": 9,
    "supplier_return_not_credited": 10,
    "supplier_credit_not_returned": 11,
    "return_unresolved": 12,
    "receipt_unbilled": 13,
    "units_not_comparable": 14,
    "reservation_exceeds_stock": 15,
    "silent_source": 16,
    "source_interpretation_failure": 17,
    "unexplained_movement": 18,
    "sales_invoice_unposted": 19,
    "supplier_invoice_unposted": 20,
    "credit_note_unposted": 21,
    "credit_note_unsettled": 22,
    "supplier_credit_unposted": 23,
    "supplier_credit_unclaimed": 24,
    "overdue_receivable": 25,
    "credit_limit_exceeded": 26,
    "overdue_payable": 27,
    "purchase_discount_available": 28,
    "duplicate_supplier_invoice": 29,
    "unmatched_financial_event": 30,
    "announced_return_not_arrived": 31,
    "commitment_hold_unreleased": 32,
    "party_hold_unreleased": 33,
    "stock_expired": 34,
}


@dataclass(frozen=True)
class OperationalException:
    id: str
    class_id: str
    cause_ids: tuple[str, ...]
    severity: str
    title: str
    impact: str
    record_type: str
    record_id: str
    causal_values: dict[str, Any]
    trace: dict[str, Any]
    sort_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("sort_at")
        value["cause_ids"] = list(self.cause_ids)
        return value


def _identity(class_id: str, record_id: str) -> str:
    return f"exc__{class_id}__{record_id}"


def _quantity(
    session: Session, model: type[Any], tenant_id: str, *criteria: Any
) -> Decimal:
    return Decimal(
        session.scalar(
            select(func.coalesce(func.sum(model.quantity), 0)).where(
                model.tenant_id == tenant_id, *criteria
            )
        )
        or ZERO
    )


def _promise_due_at(
    session: Session, tenant_id: str, commitment: Commitment
) -> tuple[datetime | None, int]:
    """The date a promise is due on now, and how many times that has moved.

    Delegates to the one service-layer rule rather than reading revisions here.
    The date in force is the third derived figure this queue has had to keep
    single-sourced — unit comparability and the learned thresholds were the
    others — and two copies of it would eventually disagree.
    """
    from reality.services.core import commitment_due_at, commitment_revisions

    inputs = _inputs(session, tenant_id)
    if inputs is not None and commitment.id in inputs.terms:
        due_at, _, moves = inputs.terms[commitment.id]
        return due_at, moves
    moves = len(commitment_revisions(session, tenant_id, commitment.id))
    return commitment_due_at(session, tenant_id, commitment.id), moves


def _promise_quantity(
    session: Session, tenant_id: str, commitment: Commitment
) -> Decimal:
    """How much a promise is for now, through the one service-layer rule.

    A promise revised to eighty is judged against eighty, exactly as a promise
    revised to a later day is judged against that day.
    """
    from reality.services.core import commitment_quantity

    inputs = _inputs(session, tenant_id)
    if inputs is not None and commitment.id in inputs.terms:
        return inputs.terms[commitment.id][1]
    return commitment_quantity(session, tenant_id, commitment.id)


def _revision_values(commitment: Commitment, moves: int) -> dict[str, Any]:
    """What an entry adds when the promise has been moved, and nothing when not.

    Conditional on purpose: an entry for a promise nobody revised is identical
    to the one this queue produced before revisions existed.
    """
    if not moves:
        return {}
    return {"originally_due_at": commitment.due_at, "times_revised": moves}


def _overdue_causes(unreserved: Decimal, moves: int) -> tuple[str, ...]:
    return tuple(
        cause
        for cause, holds in (
            ("insufficient_reservation", unreserved > ZERO),
            ("promise_was_revised", bool(moves)),
        )
        if holds
    )


def _fulfilled_quantity(
    session: Session, tenant_id: str, commitment_id: str, movement_type: str
) -> Decimal:
    """How much has moved against one promise.

    Delegates to the service layer, which excludes movements a correction has
    voided. Counting them here instead of there is how the queue and the service
    came to disagree about a corrected shipment, so there is now one path.
    """
    from reality.services.core import movement_quantity

    inputs = _inputs(session, tenant_id)
    if inputs is not None and commitment_id in inputs.terms:
        return inputs.movements.get((commitment_id, movement_type), ZERO)
    return movement_quantity(session, tenant_id, commitment_id, movement_type)


def _commitment_trace(
    session: Session, tenant_id: str, row: Commitment
) -> dict[str, Any]:
    inputs = _inputs(session, tenant_id)
    if inputs is not None and row.id in inputs.terms:
        document = inputs.documents.get(row.document_id)
        line = inputs.lines.get(row.document_line_id)
    else:
        document = (
            session.scalar(
                select(Document).where(
                    Document.tenant_id == tenant_id, Document.id == row.document_id
                )
            )
            if row.document_id
            else None
        )
        line = (
            session.scalar(
                select(DocumentLine).where(
                    DocumentLine.tenant_id == tenant_id,
                    DocumentLine.id == row.document_line_id,
                )
            )
            if row.document_line_id
            else None
        )
    source_id = document.source_record_id if document else None
    return {
        "commitment_id": row.id,
        "document_line_id": line.id if line else None,
        "document_id": document.id if document else None,
        "document_number": document.number if document else None,
        "source_record_id": source_id,
        "source_absent": source_id is None,
    }


def _commitment_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    result: list[OperationalException] = []
    rows = session.scalars(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id, Commitment.status == "open"
        )
    )
    for row in rows:
        movement_type = "shipment" if row.type == "customer_delivery" else "receipt"
        fulfilled = _fulfilled_quantity(session, tenant_id, row.id, movement_type)
        # The date in force, not the date the promise was made with: a supplier
        # that acknowledged a later day is not late until that day passes. The
        # original stays on the promise, and the entry says below that it moved.
        due_at, moves = _promise_due_at(session, tenant_id, row)
        promised = _promise_quantity(session, tenant_id, row)
        remaining = max(ZERO, promised - fulfilled)
        if row.type == "customer_delivery":
            inputs = _inputs(session, tenant_id)
            reserved = (
                inputs.reserved.get(row.id, ZERO)
                if inputs is not None and row.id in inputs.terms
                else _quantity(
                    session,
                    Reservation,
                    tenant_id,
                    Reservation.commitment_id == row.id,
                    Reservation.status == "active",
                )
            )
            unreserved = max(ZERO, remaining - reserved)
            overdue = due_at is not None and due_at < as_of
            # An already broken promise says more than a risky one, so the
            # overdue class supersedes the at-risk class for the same
            # commitment and carries the reservation shortfall as its cause.
            if remaining > ZERO and overdue:
                impact = f"{remaining:g} remain overdue"
                if ZERO < unreserved < remaining:
                    impact = f"{impact}, {unreserved:g} of them unreserved"
                result.append(
                    OperationalException(
                        _identity("overdue_outgoing_customer_commitment", row.id),
                        "overdue_outgoing_customer_commitment",
                        _overdue_causes(unreserved, moves),
                        "high",
                        "Overdue outgoing customer commitment",
                        impact,
                        "commitment",
                        row.id,
                        {
                            "due_at": due_at,
                            "as_of": as_of,
                            **_revision_values(row, moves),
                            "committed_quantity": promised,
                            "fulfilled_quantity": fulfilled,
                            "remaining_quantity": remaining,
                            "reserved_quantity": reserved,
                            "unreserved_quantity": unreserved,
                        },
                        _commitment_trace(session, tenant_id, row),
                        due_at,
                    )
                )
            elif remaining > ZERO and unreserved > ZERO:
                result.append(
                    OperationalException(
                        _identity("outgoing_commitment_at_risk", row.id),
                        "outgoing_commitment_at_risk",
                        ("insufficient_reservation",),
                        "high",
                        "Customer commitment at risk",
                        f"{unreserved:g} remains unreserved",
                        "commitment",
                        row.id,
                        {
                            "committed_quantity": promised,
                            "fulfilled_quantity": fulfilled,
                            "remaining_quantity": remaining,
                            "reserved_quantity": reserved,
                            "unreserved_quantity": unreserved,
                        },
                        _commitment_trace(session, tenant_id, row),
                        due_at,
                    )
                )
        elif (
            row.type == "supplier_delivery"
            and due_at is not None
            and due_at < as_of
            and remaining > ZERO
        ):
            result.append(
                OperationalException(
                    _identity("overdue_incoming_supplier_commitment", row.id),
                    "overdue_incoming_supplier_commitment",
                    ("promise_was_revised",) if moves else (),
                    "high",
                    "Overdue incoming supplier commitment",
                    f"{remaining:g} remains overdue",
                    "commitment",
                    row.id,
                    {
                        "due_at": due_at,
                        "as_of": as_of,
                        **_revision_values(row, moves),
                        "committed_quantity": promised,
                        "received_quantity": fulfilled,
                        "remaining_quantity": remaining,
                    },
                    _commitment_trace(session, tenant_id, row),
                    due_at,
                )
            )
    return result


def _overdue_outgoing_customer_commitment(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return [
        row
        for row in _commitment_exceptions(session, tenant_id, as_of)
        if row.class_id == "overdue_outgoing_customer_commitment"
    ]


def _outgoing_commitment_at_risk(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return [
        row
        for row in _commitment_exceptions(session, tenant_id, as_of)
        if row.class_id == "outgoing_commitment_at_risk"
    ]


def _overdue_incoming_supplier_commitment(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return [
        row
        for row in _commitment_exceptions(session, tenant_id, as_of)
        if row.class_id == "overdue_incoming_supplier_commitment"
    ]


def _document_instant(document: Document) -> datetime | None:
    """When a document says it happened, as far as it says anything."""
    if document.ordered_at:
        return document.ordered_at
    text = document.document_date.strip()
    try:
        return datetime.combine(
            date.fromisoformat(text), datetime.min.time(), tzinfo=UTC
        )
    except ValueError:
        # A free-form period label is not a date. Nothing is invented from it.
        return None


def _billing_lines(
    session: Session, tenant_id: str, order_line_id: str
) -> list[DocumentLine]:
    inputs = _inputs(session, tenant_id)
    if inputs is not None and order_line_id in inputs.lines:
        direct = inputs.billing.get(order_line_id, [])
        invoice_ids = {
            line.id
            for line in direct
            if (document := inputs.documents.get(line.document_id)) is not None
            and document.type == "sales_invoice"
        }
        related = {line.id: line for line in direct}
        for identity in invoice_ids:
            related.update({line.id: line for line in inputs.billing.get(identity, [])})
        return sorted(related.values(), key=lambda line: line.id)
    invoice_ids = (
        select(DocumentLine.id)
        .join(
            Document,
            (Document.id == DocumentLine.document_id)
            & (Document.tenant_id == tenant_id),
        )
        .where(
            DocumentLine.tenant_id == tenant_id,
            DocumentLine.billed_document_line_id == order_line_id,
            Document.type == "sales_invoice",
        )
    )
    return list(
        session.scalars(
            select(DocumentLine)
            .where(
                DocumentLine.tenant_id == tenant_id,
                or_(
                    DocumentLine.billed_document_line_id == order_line_id,
                    DocumentLine.billed_document_line_id.in_(invoice_ids),
                ),
            )
            .order_by(DocumentLine.id)
        )
    )


def _invoice_lines(
    session: Session, tenant_id: str, order_line_id: str
) -> list[DocumentLine]:
    """The invoice lines billing one order line, credit notes excluded.

    Credit note lines reference the same order line and mean the opposite, so a
    class about billing must not count them.
    """
    return [
        line
        for line in _billing_lines(session, tenant_id, order_line_id)
        if _referencing_document_type(session, tenant_id, line)
        in {"sales_invoice", "supplier_invoice"}
    ]


@dataclass(frozen=True)
class _UnitDecline:
    """Lines a comparison refused to judge, and what would let it."""

    item_id: str
    agreed_unit: str
    recorded_unit: str
    reason: str
    line_ids: tuple[str, ...]


def _item(session: Session, tenant_id: str, item_id: str | None) -> Item | None:
    inputs = _inputs(session, tenant_id)
    if inputs is not None and item_id in inputs.items:
        return inputs.items.get(item_id)
    if not item_id:
        return None
    return session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == item_id)
    )


def _in_unit(
    item: Item | None, quantity: Decimal, recorded: str, target: str
) -> Decimal | None:
    """A quantity recorded in one unit, expressed in another, or None.

    The only relation Reality holds is the one an item states between its own
    stock unit and its own purchase unit — "we buy this in boxes of twelve",
    written down by the company. Multiplying a stated quantity by a stated
    factor at read time, storing nothing, is an observation over facts held and
    never a second authority for either of them.

    Three things stop it, and each is a company that has not said enough: no
    item to carry a statement, a factor that states nothing, and a pair the
    statement does not cover. A fourth stops it although everything was said —
    a conversion leaving a remainder, because a hundred and seven pieces are not
    a number of boxes and rounding them into one is the thing this product
    exists not to do.
    """
    if recorded == target:
        return quantity
    if item is None:
        return None
    factor = Decimal(item.conversion_factor)
    if factor <= ZERO:
        return None
    if recorded == item.purchase_unit and target == item.unit:
        return quantity * factor
    if recorded == item.unit and target == item.purchase_unit:
        whole, remainder = divmod(quantity, factor)
        return whole if remainder == ZERO else None
    return None


def _decline_reason(item: Item | None, recorded: str, target: str) -> str:
    """Which of the two went wrong, because their exits are different.

    A relation nobody stated is master data to fill in. A relation that is
    stated and does not divide is a company that ordered ten boxes and delivered
    a hundred and seven pieces, and telling it to state the relation would be
    advice it has already taken.
    """
    if item is None or Decimal(item.conversion_factor) <= ZERO:
        return "no_stated_relation"
    if {recorded, target} != {item.unit, item.purchase_unit}:
        return "no_stated_relation"
    return "conversion_leaves_a_remainder"


def _reconcile(
    session: Session,
    tenant_id: str,
    agreed: DocumentLine,
    lines: list[DocumentLine],
) -> tuple[Decimal | None, list[_UnitDecline]]:
    """What those lines add up to in the agreed line's unit, and what stopped it.

    One decision for every class that asks, so no two of them can disagree about
    whether a pair is comparable — and the class that reports the declines reads
    them from here instead of working them out a second time.

    Lines recorded in one unit are added up before being converted, because what
    is compared is the total carried against the agreement rather than each
    invoice on its own. A unit that cannot be expressed in the agreed one stops
    the whole sum: a partial total would understate and read as a real shortfall.
    """
    item = _item(session, tenant_id, agreed.item_id)
    groups: dict[str, list[DocumentLine]] = {}
    for line in lines:
        groups.setdefault(line.unit, []).append(line)
    total = ZERO
    declines: list[_UnitDecline] = []
    for unit in sorted(groups):
        group = groups[unit]
        recorded = sum((Decimal(row.quantity) for row in group), ZERO)
        converted = _in_unit(item, recorded, unit, agreed.unit)
        if converted is None:
            declines.append(
                _UnitDecline(
                    agreed.item_id or "",
                    agreed.unit,
                    unit,
                    _decline_reason(item, unit, agreed.unit),
                    tuple(row.id for row in group),
                )
            )
            continue
        total += converted
    return (None if declines else total), declines


def _quantity_in_agreed_unit(
    session: Session, tenant_id: str, agreed: DocumentLine, lines: list[DocumentLine]
) -> Decimal | None:
    """What those lines carry against one order line, or None if it cannot be said.

    Every referencing line counts, which is what makes a consolidated or partial
    invoice behave without special handling. Billing and crediting ask the same
    question and are answered the same way; which lines to pass is the caller's
    business.
    """
    total, _ = _reconcile(session, tenant_id, agreed, lines)
    return total


def _prices_comparable(billed: DocumentLine, agreed: DocumentLine) -> bool:
    """Whether two prices are figures of the same kind at all.

    Deliberately narrower than the quantity rule and kept apart from it, so that
    a price can never reach the converting one. A price per box divided by
    twelve is money nobody agreed, and where it does not divide it is the
    rounding this product exists to avoid.
    """
    return billed.unit == agreed.unit


def _order_line_promises(
    session: Session, tenant_id: str, commitment_type: str
) -> list[tuple[Commitment, DocumentLine, Document]]:
    """Order lines that promised a delivery, with the promise and the order.

    Starting from the Commitment is what excludes a freight, discount or service
    line: it promises no goods, can never be received, and must never be
    reported for failing to arrive.
    """
    return list(
        session.execute(
            select(Commitment, DocumentLine, Document)
            .join(
                DocumentLine,
                (DocumentLine.tenant_id == Commitment.tenant_id)
                & (DocumentLine.id == Commitment.document_line_id),
            )
            .join(
                Document,
                (Document.tenant_id == DocumentLine.tenant_id)
                & (Document.id == DocumentLine.document_id),
            )
            .where(
                Commitment.tenant_id == tenant_id,
                Commitment.type == commitment_type,
                Commitment.document_line_id.is_not(None),
            )
            .order_by(DocumentLine.id)
        ).all()
    )


def _order_line_trace(
    commitment: Commitment, line: DocumentLine, document: Document
) -> dict[str, Any]:
    return {
        "document_line_id": line.id,
        "document_id": document.id,
        "commitment_id": commitment.id,
        "source_record_id": document.source_record_id,
    }


def _last_movement_at(
    session: Session, tenant_id: str, commitment_id: str, movement_type: str
) -> datetime | None:
    inputs = _inputs(session, tenant_id)
    if inputs is not None and commitment_id in inputs.terms:
        return inputs.last_movements.get((commitment_id, movement_type))
    return session.scalar(
        select(func.max(Movement.occurred_at)).where(
            Movement.tenant_id == tenant_id,
            Movement.commitment_id == commitment_id,
            Movement.type == movement_type,
        )
    )


def _learned_threshold(
    ordered_lags: list[timedelta], *, floor: timedelta
) -> timedelta | None:
    """How long is too long here, or nothing if it cannot be said.

    Returning None rather than a large number matters: a tenant without history
    is not one with a lenient threshold, it is one this rule cannot speak about,
    and the caller has to be able to tell the difference.
    """
    recent = ordered_lags[-LEARNED_HISTORY:]
    if len(recent) < LEARNED_MINIMUM:
        return None
    ranked = sorted(recent)
    median = ranked[len(ranked) // 2]
    return max(median * LEARNED_MULTIPLE, floor)


def _lag(start: datetime, end: datetime) -> timedelta:
    # A movement may be recorded as having occurred before the promise existed.
    # That is a backdated entry, not a negative duration.
    return max(end - start, timedelta(0))


def _fulfilment_threshold(session: Session, tenant_id: str) -> timedelta | None:
    """How long this tenant normally takes to ship what it promised.

    Learned from promises that finished. An unfinished promise is what the class
    exists to judge, so counting it would let a backlog raise the bar that
    measures the backlog, and a cancelled one would teach a lag that never
    happened.
    """
    completed: list[tuple[datetime, timedelta]] = []
    rows = session.scalars(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.type == "customer_delivery",
            Commitment.status != "cancelled",
        )
    )
    for row in rows:
        shipped = _fulfilled_quantity(session, tenant_id, row.id, "shipment")
        if shipped < _promise_quantity(session, tenant_id, row) or shipped <= ZERO:
            continue
        last = _last_movement_at(session, tenant_id, row.id, "shipment")
        if last is None:
            continue
        completed.append((last, _lag(row.created_at, last)))
    completed.sort()
    return _learned_threshold([lag for _, lag in completed], floor=STALLED_ORDER_FLOOR)


def _billing_threshold(session: Session, tenant_id: str) -> timedelta | None:
    """How long this tenant's suppliers normally take to invoice a receipt."""
    billed: list[tuple[datetime, timedelta]] = []
    for commitment, line, _ in _order_line_promises(
        session, tenant_id, "supplier_delivery"
    ):
        last = _last_movement_at(session, tenant_id, commitment.id, "receipt")
        if last is None:
            continue
        instants = []
        for billing_line in _invoice_lines(session, tenant_id, line.id):
            document = _billing_document(session, tenant_id, billing_line)
            instant = _document_instant(document) if document else None
            if instant is not None:
                instants.append(instant)
        if not instants:
            continue
        first = min(instants)
        billed.append((first, _lag(last, first)))
    billed.sort()
    return _learned_threshold([lag for _, lag in billed], floor=UNBILLED_RECEIPT_FLOOR)


def _order_stalled_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A promise nobody dated that nobody has shipped.

    Every other delivery class is anchored to a due date, so a consumer order
    that states none can stand forever without being reportable. Taking only
    undated promises keeps this class disjoint from the overdue one by
    construction rather than by a precedence rule.
    """
    threshold = _fulfilment_threshold(session, tenant_id)
    if threshold is None:
        return []
    result: list[OperationalException] = []
    rows = session.scalars(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.type == "customer_delivery",
            Commitment.status == "open",
            Commitment.due_at.is_(None),
        )
    )
    for row in rows:
        # Somebody stating a date makes the order dated, so it stops being an
        # undated one and the overdue class takes it instead.
        if _promise_due_at(session, tenant_id, row)[0] is not None:
            continue
        shipped = _fulfilled_quantity(session, tenant_id, row.id, "shipment")
        if shipped >= _promise_quantity(session, tenant_id, row):
            continue
        standing = _lag(row.created_at, as_of)
        if standing <= threshold:
            continue
        norm = threshold / LEARNED_MULTIPLE
        result.append(
            OperationalException(
                _identity("order_stalled", row.id),
                "order_stalled",
                (),
                "high",
                "Order stalled",
                f"standing {standing.days:g} days with no agreed date",
                "commitment",
                row.id,
                {
                    "standing_for_days": standing.days,
                    "threshold_days": threshold.days,
                    "norm_days": norm.days,
                    "promised_quantity": _promise_quantity(session, tenant_id, row),
                    "shipped_quantity": shipped,
                },
                _commitment_trace(session, tenant_id, row),
                row.created_at,
            )
        )
    return result


def _receipt_unbilled_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """Goods in the building that no supplier has invoiced.

    Spec 076 left this out because a supplier invoice after the goods is the
    usual sequence. Time is the only thing that was missing: past this tenant's
    own norm it stops being ordinary and becomes an accrual nobody has made.
    """
    threshold = _billing_threshold(session, tenant_id)
    if threshold is None:
        return []
    result: list[OperationalException] = []
    for commitment, line, document in _order_line_promises(
        session, tenant_id, "supplier_delivery"
    ):
        # What the company still has, not what once arrived: it should not be
        # accruing an invoice for goods it sent back. The same correction spec
        # 079 made to Shipped and not billed on the selling side.
        received = _held_quantity(session, tenant_id, commitment.id)
        if received <= ZERO:
            continue
        billed = _quantity_in_agreed_unit(
            session, tenant_id, line, _invoice_lines(session, tenant_id, line.id)
        )
        if billed is None or billed >= received:
            continue
        last = _last_movement_at(session, tenant_id, commitment.id, "receipt")
        if last is None:
            continue
        standing = _lag(last, as_of)
        if standing <= threshold:
            continue
        norm = threshold / LEARNED_MULTIPLE
        result.append(
            OperationalException(
                _identity("receipt_unbilled", line.id),
                "receipt_unbilled",
                (),
                "high",
                "Receipt not invoiced",
                f"{received - billed:g} received {standing.days:g} days ago and "
                "still not invoiced",
                "document_line",
                line.id,
                {
                    "received_quantity": received,
                    "billed_quantity": billed,
                    "unbilled_quantity": received - billed,
                    "standing_for_days": standing.days,
                    "threshold_days": threshold.days,
                    "norm_days": norm.days,
                    "unit": line.unit,
                },
                _order_line_trace(commitment, line, document),
                last,
            )
        )
    return result


def _returns_with_resolutions(
    session: Session, tenant_id: str
) -> list[tuple[Movement, Decimal]]:
    """Every return this tenant recorded, with how much of it has been settled."""
    from reality.services.core import movement_quantity_resolving

    rows = session.scalars(
        select(Movement)
        .where(Movement.tenant_id == tenant_id, Movement.type == "return")
        .order_by(Movement.occurred_at, Movement.id)
    ).all()
    voided = set(
        session.scalars(
            select(MovementCorrection.original_movement_id).where(
                MovementCorrection.tenant_id == tenant_id
            )
        )
    )
    return [
        (row, movement_quantity_resolving(session, tenant_id, row.id))
        for row in rows
        if row.id not in voided
    ]


def _resolution_threshold(session: Session, tenant_id: str) -> timedelta | None:
    """How long this company normally takes to deal with a return.

    The fourth use of the learned rule, and learned only from returns that were
    actually settled: one still sitting is what the class exists to judge.
    """
    resolved: list[tuple[datetime, timedelta]] = []
    for row, settled in _returns_with_resolutions(session, tenant_id):
        if settled < Decimal(row.quantity):
            continue
        last = session.scalar(
            select(func.max(Movement.occurred_at)).where(
                Movement.tenant_id == tenant_id,
                Movement.resolves_movement_id == row.id,
            )
        )
        if last is None:
            continue
        resolved.append((last, _lag(row.occurred_at, last)))
    resolved.sort()
    return _learned_threshold(
        [lag for _, lag in resolved], floor=UNRESOLVED_RETURN_FLOOR
    )


def _return_unresolved_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """Goods that came back and are still sitting there.

    What happened to returned stock is not stored anywhere: it is whatever
    movement settled the return — a transfer back to stock, a write-off, a
    shipment to the supplier. A return nothing settles is stock the company owns
    and cannot sell, and it grows quietly because every record is correct.
    """
    threshold = _resolution_threshold(session, tenant_id)
    if threshold is None:
        return []
    result: list[OperationalException] = []
    for row, settled in _returns_with_resolutions(session, tenant_id):
        outstanding = Decimal(row.quantity) - settled
        if outstanding <= ZERO:
            continue
        standing = _lag(row.occurred_at, as_of)
        if standing <= threshold:
            continue
        result.append(
            OperationalException(
                _identity("return_unresolved", row.id),
                "return_unresolved",
                (),
                "normal",
                "Return not dealt with",
                f"{outstanding:g} back {standing.days:g} days ago and still sitting",
                "movement",
                row.id,
                {
                    "returned_quantity": Decimal(row.quantity),
                    "resolved_quantity": settled,
                    "outstanding_quantity": outstanding,
                    "standing_for_days": standing.days,
                    "threshold_days": threshold.days,
                    "norm_days": (threshold / LEARNED_MULTIPLE).days,
                },
                {
                    "movement_id": row.id,
                    "commitment_id": row.commitment_id,
                    "source_record_id": row.source_record_id,
                },
                row.occurred_at,
            )
        )
    return result


def _announcement_arrival_threshold(
    session: Session, tenant_id: str
) -> timedelta | None:
    """How long a parcel this company announced normally takes to arrive.

    The fifth use of the learned rule, and learned only from announcements that
    did arrive: one still waiting is what the class exists to judge, and a
    withdrawn one teaches a lag that never happened.

    The rule is shared and the history never is: a company's own settled cases
    stay inside its own tenant.
    """
    from reality.services.core import ReturnAnnouncement

    arrived: list[tuple[datetime, timedelta]] = []
    for announcement in session.scalars(
        select(ReturnAnnouncement).where(
            ReturnAnnouncement.tenant_id == tenant_id,
            ReturnAnnouncement.status == "fulfilled",
        )
    ):
        # When the goods actually arrived, not when the status changed. A
        # backdated parcel is recorded with the day it came back, and `closed_at`
        # is the instant somebody wrote it down — measuring that would learn how
        # fast this company types.
        last = session.scalar(
            select(func.max(Movement.occurred_at)).where(
                Movement.tenant_id == tenant_id,
                Movement.return_announcement_id == announcement.id,
            )
        )
        if last is None:
            continue
        arrived.append((last, _lag(announcement.announced_at, last)))
    arrived.sort()
    return _learned_threshold(
        [lag for _, lag in arrived], floor=UNARRIVED_ANNOUNCEMENT_FLOOR
    )


def _announced_return_not_arrived_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A customer said goods were coming back and they have not.

    Two ways in, and the entry says which one spoke. Where the customer named a
    day, their word is the measurement and nothing needs learning. Where they
    did not, this company's own rhythm decides, from the shared learned rule —
    and below five arrivals it decides nothing, because a company without
    history is not one with a lenient threshold, it is one the rule cannot speak
    about.

    A withdrawn announcement is not reported: the customer has said the parcel
    is not coming, and there is nothing left for anybody to do.

    One class rather than two, because it is one condition with one owner and
    one clearing path — the goods arriving. The only difference between the two
    ways in is how the date was arrived at, which belongs in the entry.
    """
    from reality.services.core import (
        ReturnAnnouncement,
        announcement_outstanding,
    )

    threshold = _announcement_arrival_threshold(session, tenant_id)
    result: list[OperationalException] = []
    for announcement in session.scalars(
        select(ReturnAnnouncement)
        .where(
            ReturnAnnouncement.tenant_id == tenant_id,
            ReturnAnnouncement.status == "open",
        )
        .order_by(ReturnAnnouncement.announced_at, ReturnAnnouncement.id)
    ):
        outstanding = announcement_outstanding(session, tenant_id, announcement)
        if outstanding <= ZERO:
            continue
        waiting = _lag(announcement.announced_at, as_of)
        if announcement.expected_by is not None:
            if announcement.expected_by >= as_of:
                continue
            judged_by = "the day the customer stated"
            late = _lag(announcement.expected_by, as_of)
            summary = (
                f"{outstanding:g} announced for {announcement.expected_by.date().isoformat()}"
                f" and {late.days:g} days past it"
            )
        else:
            if threshold is None or waiting <= threshold:
                continue
            judged_by = "this company's own rhythm"
            summary = f"{outstanding:g} announced {waiting.days:g} days ago with no day stated"
        result.append(
            OperationalException(
                _identity("announced_return_not_arrived", announcement.id),
                "announced_return_not_arrived",
                (),
                "normal",
                "Announced return has not arrived",
                summary,
                "return_announcement",
                announcement.id,
                {
                    "announced_quantity": Decimal(announcement.quantity),
                    "arrived_quantity": Decimal(announcement.quantity) - outstanding,
                    "outstanding_quantity": outstanding,
                    "waiting_for_days": waiting.days,
                    "expected_by": announcement.expected_by,
                    "reference": announcement.reference,
                    "judged_by": judged_by,
                    # Absent where the customer stated a day: nothing was
                    # learned, so reporting a norm would suggest one was.
                    "threshold_days": (
                        threshold.days
                        if threshold is not None and announcement.expected_by is None
                        else None
                    ),
                    "norm_days": (
                        (threshold / LEARNED_MULTIPLE).days
                        if threshold is not None and announcement.expected_by is None
                        else None
                    ),
                },
                {
                    "return_announcement_id": announcement.id,
                    "commitment_id": announcement.commitment_id,
                    "source_record_id": announcement.source_record_id,
                },
                announcement.expected_by or announcement.announced_at,
            )
        )
    return result


def _lifted_hold_threshold(session: Session, tenant_id: str, model) -> timedelta | None:
    """How long this company normally takes to lift a hold of one kind.

    Learned only from holds that were lifted: one still standing is what the
    class exists to judge, so counting it would let a backlog raise the bar that
    measures the backlog.

    Each hold kind learns from its own population. A promise hold and a customer
    delivery hold are different processes with different people behind them, and
    a rule is shared while a history never is.
    """
    lifted = [
        (row.released_at, _lag(row.created_at, row.released_at))
        for row in session.scalars(
            select(model).where(
                model.tenant_id == tenant_id, model.released_at.is_not(None)
            )
        )
    ]
    lifted.sort()
    return _learned_threshold([lag for _, lag in lifted], floor=UNLIFTED_HOLD_FLOOR)


def _unreleased_hold_exceptions(
    session: Session,
    tenant_id: str,
    as_of: datetime,
    *,
    model,
    class_id: str,
    title: str,
    record_type: str,
) -> list[OperationalException]:
    """A hold nobody has lifted.

    A hold is somebody saying they are dealing with something, and the
    stale-promise closure skips held promises for exactly that reason. That
    protection has no expiry: a hold raised for a check somebody finished a year
    ago goes on shielding its promise from the only sweep that could close it,
    and until this class existed nothing reported either fact.

    Nothing is released and nothing is suppressed. The reason, the note and who
    raised it are reported exactly as recorded; the only derived figures are how
    long it has stood and what it is holding back.
    """
    from reality.services.core import open_quantity

    threshold = _lifted_hold_threshold(session, tenant_id, model)
    if threshold is None:
        return []
    result: list[OperationalException] = []
    for hold in session.scalars(
        select(model)
        .where(model.tenant_id == tenant_id, model.released_at.is_(None))
        .order_by(model.created_at, model.id)
    ):
        standing = _lag(hold.created_at, as_of)
        if standing <= threshold:
            continue
        causal: dict[str, Any] = {
            "reason_code": hold.reason_code,
            "note": hold.note,
            "raised_by": hold.created_by,
            "standing_for_days": standing.days,
            "threshold_days": threshold.days,
            "norm_days": (threshold / LEARNED_MULTIPLE).days,
        }
        if model is CommitmentHold:
            commitment = session.scalar(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.id == hold.commitment_id,
                )
            )
            # A hold on a promise nobody is waiting for holds nothing back, so
            # there is nothing for anybody to clear by doing something useful.
            # Cancelling a promise does not release its holds, which is why such
            # holds exist at all; reporting them would be a wall.
            if commitment is None or commitment.status != "open":
                continue
            causal["held_quantity"] = open_quantity(session, tenant_id, commitment.id)
            # The promise's own unit, which lives on the order line it came
            # from. None where the promise names no line: that reference is
            # optional, and inventing a unit would be worse than saying nothing.
            line = (
                session.scalar(
                    select(DocumentLine).where(
                        DocumentLine.tenant_id == tenant_id,
                        DocumentLine.id == commitment.document_line_id,
                    )
                )
                if commitment.document_line_id
                else None
            )
            causal["unit"] = line.unit if line else None
            trace = {
                "commitment_hold_id": hold.id,
                "commitment_id": commitment.id,
                "document_id": commitment.document_id,
            }
            summary = (
                f"{causal['held_quantity']:g} held for {hold.reason_code} "
                f"{standing.days:g} days ago"
            )
        else:
            # Every hold type, named rather than filtered. Only delivery holds
            # exist today, and filtering is how a rule stays correct until a
            # second case arrives and then quietly stops being.
            blocked = session.scalar(
                select(func.count())
                .select_from(Commitment)
                .where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.type == "customer_delivery",
                    Commitment.status == "open",
                    Commitment.to_party_id == hold.party_id,
                )
            )
            causal["hold_type"] = hold.hold_type
            # A count, never a sum. Quantities across different items do not add
            # up, and a blocked count of nothing is still reported because the
            # hold will refuse the next order too.
            causal["blocked_commitments"] = int(blocked or 0)
            trace = {"party_hold_id": hold.id, "party_id": hold.party_id}
            summary = (
                f"{hold.hold_type} hold for {hold.reason_code} standing "
                f"{standing.days:g} days, blocking "
                f"{causal['blocked_commitments']:g} open deliveries"
            )
        result.append(
            OperationalException(
                _identity(class_id, hold.id),
                class_id,
                (),
                "normal" if model is CommitmentHold else "high",
                title,
                summary,
                record_type,
                hold.id,
                causal,
                trace,
                hold.created_at,
            )
        )
    return result


def _commitment_hold_unreleased_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return _unreleased_hold_exceptions(
        session,
        tenant_id,
        as_of,
        model=CommitmentHold,
        class_id="commitment_hold_unreleased",
        title="Promise hold not lifted",
        record_type="commitment_hold",
    )


def _party_hold_unreleased_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return _unreleased_hold_exceptions(
        session,
        tenant_id,
        as_of,
        model=PartyHold,
        class_id="party_hold_unreleased",
        title="Party hold not lifted",
        record_type="party_hold",
    )


def _stock_expired_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """Stock a company holds whose stated best-before has passed.

    Two measurements, both real: the date somebody read off the goods, and the
    day the queue is asked. **No threshold, no horizon, no learned statistic.**

    That absence is deliberate and it is the design decision most likely to be
    questioned. "Expiring soon" is the more useful report and it needs a horizon
    that exists nowhere: nothing on an item states a shelf life and no term
    states a minimum remaining life. The one mechanism that could produce a
    number already governs ten of this catalog's classes on figures nobody has
    checked against a real business, and an eleventh would grow that risk to buy
    a threshold nobody could defend. Expired is unambiguous and costs nothing
    invented.

    Nothing is blocked, chosen or released. A picker can still ship expired
    stock: refusing the movement would stop a company recording something that
    already happened, and choosing which lot ships is an allocation policy this
    product has never had.
    """
    from reality.services.core import expired_lots, stock_by_identity

    result: list[OperationalException] = []
    for lot in expired_lots(session, tenant_id, as_of=as_of):
        # The one stock rule the product uses for a tracked identity, per
        # location, so this can never disagree with the inventory register.
        locations = session.scalars(
            select(Location.id)
            .where(Location.tenant_id == tenant_id)
            .order_by(Location.id)
        ).all()
        held = sum(
            (
                stock_by_identity(
                    session, tenant_id, lot.item_id, location_id, lot_id=lot.id
                )
                for location_id in locations
            ),
            ZERO,
        )
        # A lot with nothing left is not reported: nothing is held, so there is
        # nothing for anybody to do, and it would be a wall of history.
        if held <= ZERO:
            continue
        reserved = Decimal(
            session.scalar(
                select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                    Reservation.tenant_id == tenant_id,
                    Reservation.lot_id == lot.id,
                    Reservation.status == "active",
                )
            )
            or 0
        )
        expired_days = (as_of.date() - lot.expires_at).days
        result.append(
            OperationalException(
                _identity("stock_expired", lot.id),
                "stock_expired",
                # Same record, same owner, same clearing path; only the urgency
                # differs, which is what a cause is for. Stock a customer is
                # waiting for has to be stopped before it is written off.
                ("reserved_for_delivery",) if reserved > ZERO else (),
                "high",
                "Expired stock on hand",
                f"{held:g} held past {lot.expires_at.isoformat()}"
                + (
                    f", {reserved:g} reserved for a customer" if reserved > ZERO else ""
                ),
                "lot",
                lot.id,
                {
                    "expires_at": lot.expires_at,
                    "expired_days": expired_days,
                    "held_quantity": held,
                    "reserved_quantity": reserved,
                    "lot_number": lot.lot_number,
                },
                {
                    "lot_id": lot.id,
                    "item_id": lot.item_id,
                    "source_record_id": lot.source_record_id,
                },
                datetime(
                    lot.expires_at.year,
                    lot.expires_at.month,
                    lot.expires_at.day,
                    tzinfo=UTC,
                ),
            )
        )
    return result


def _standing_purchase_price(
    session: Session,
    tenant_id: str,
    *,
    item_id: str,
    currency: str,
    unit: str,
    quantity: Decimal,
    at: datetime | None,
    book: tuple[PriceList, dict[str, list[PriceListEntry]]] | None = None,
) -> PriceListEntry | None:
    """What the company says this item costs it, as it stood at that moment.

    Deliberately not `resolve_price`. That answers "what price applies for this
    party" and needs a party to walk its links with — and the party on a sales
    line is a customer, not a supplier, so reaching the default list through it
    would mean inventing a relationship to satisfy a signature. This answers the
    smaller question: what does the standing default purchase list say.

    A retired list is not a standing price, and a quantity break is applied the
    way the resolver applies one: the highest break at or below the quantity.
    """
    moment = at or datetime.now(UTC)
    if book is None:
        book = _purchase_price_book(session, tenant_id, currency)
    if book is None:
        return None
    price_list, entries = book
    if (price_list.valid_from is not None and price_list.valid_from > moment) or (
        price_list.valid_until is not None and price_list.valid_until <= moment
    ):
        return None
    breaks = [
        entry
        for entry in entries.get(item_id, [])
        if entry.unit == unit and Decimal(entry.min_quantity) <= quantity
    ]
    return max(breaks, key=lambda entry: Decimal(entry.min_quantity), default=None)


def _cached(session: Session, tenant_id: str, key: Any, load: Callable[[], Any]) -> Any:
    """One read per evaluation for facts several classes consume; plain read outside a scope."""
    inputs = _inputs(session, tenant_id)
    if inputs is None:
        return load()
    if key not in inputs.cache:
        inputs.cache[key] = load()
    return inputs.cache[key]


def _open_items(session: Session, tenant_id: str) -> list[dict[str, Any]]:
    from reality.services.core import financial_open_items

    return _cached(
        session,
        tenant_id,
        "open_items",
        lambda: financial_open_items(session, tenant_id),
    )


def _aging_register(
    session: Session, tenant_id: str, as_of: datetime
) -> list[dict[str, Any]]:
    """`aging_register`, computed from the one open items read this evaluation makes."""
    from reality.services.core import _payment_terms_by_id, with_invoice_aging

    return _cached(
        session,
        tenant_id,
        ("aging", as_of),
        lambda: with_invoice_aging(
            _open_items(session, tenant_id),
            _payment_terms_by_id(session, tenant_id),
            as_of,
        ),
    )


def _purchase_price_book(
    session: Session, tenant_id: str, currency: str
) -> tuple[PriceList, dict[str, list[PriceListEntry]]] | None:
    """The standing default purchase list for a currency with its entries by item.

    Read once per currency; the sold-below-cost class used to ask for the list
    once per sales order line.
    """
    price_list = session.scalars(
        select(PriceList)
        .where(
            PriceList.tenant_id == tenant_id,
            PriceList.direction == "purchase",
            PriceList.currency == currency,
            PriceList.is_default.is_(True),
            PriceList.is_active.is_(True),
        )
        .order_by(PriceList.code)
    ).first()
    if price_list is None:
        return None
    entries: dict[str, list[PriceListEntry]] = {}
    for entry in session.scalars(
        select(PriceListEntry).where(
            PriceListEntry.tenant_id == tenant_id,
            PriceListEntry.price_list_id == price_list.id,
        )
    ):
        entries.setdefault(entry.item_id, []).append(entry)
    return price_list, entries


def _sold_below_purchase_price_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A sale agreed below what the company says the item costs it.

    Both figures were stated by a person — the price on the line and the entry
    on the purchase list — so nothing here is computed. It is not accounting
    margin: freight, duty and handling are not in the figure it compares
    against, so the class understates rather than overstates.
    """
    result: list[OperationalException] = []
    rows = session.execute(
        select(DocumentLine, Document)
        .join(
            Document,
            (Document.tenant_id == DocumentLine.tenant_id)
            & (Document.id == DocumentLine.document_id),
        )
        .where(
            DocumentLine.tenant_id == tenant_id,
            Document.type == "sales_order",
        )
        .order_by(DocumentLine.id)
    ).all()
    books: dict[str, tuple[PriceList, dict[str, list[PriceListEntry]]] | None] = {}
    for line, document in rows:
        # Freight and services have no purchase price of their own here.
        if not line.item_id:
            continue
        agreed = Decimal(line.unit_price)
        # A sample or a replacement is priced at nothing on purpose.
        if agreed <= ZERO:
            continue
        if document.currency not in books:
            books[document.currency] = _purchase_price_book(
                session, tenant_id, document.currency
            )
        # No standing list for the currency means no standing price for any line.
        if books[document.currency] is None:
            continue
        entry = _standing_purchase_price(
            session,
            tenant_id,
            item_id=line.item_id,
            currency=document.currency,
            unit=line.unit,
            quantity=Decimal(line.quantity),
            at=_document_instant(document),
            book=books[document.currency],
        )
        # No standing price means the company has not said what it costs.
        if entry is None:
            continue
        cost = Decimal(entry.unit_price)
        # Selling at cost is a thin deal, and thin is a decision.
        if agreed >= cost:
            continue
        result.append(
            OperationalException(
                _identity("sold_below_purchase_price", line.id),
                "sold_below_purchase_price",
                (),
                "high",
                "Sold below the purchase price",
                f"{cost - agreed:g} {document.currency} per {line.unit} below "
                "what the company says it pays",
                "document_line",
                line.id,
                {
                    "agreed_unit_price": agreed,
                    "purchase_unit_price": cost,
                    "shortfall": cost - agreed,
                    "unit": line.unit,
                    "currency": document.currency,
                },
                {
                    "document_line_id": line.id,
                    "document_id": document.id,
                    "price_list_entry_id": entry.id,
                    "source_record_id": document.source_record_id,
                },
                _document_instant(document),
            )
        )
    return result


def _shipped_not_billed_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    result: list[OperationalException] = []
    for commitment, line, document in _order_line_promises(
        session, tenant_id, "customer_delivery"
    ):
        # What the customer kept, not what went out: goods that came back are
        # not something anybody should be invoiced for.
        delivered = _kept_quantity(session, tenant_id, commitment.id)
        # A line with nothing delivered says nothing, whatever has been billed:
        # an invoice ahead of the goods is a prepayment, not a finding.
        if delivered <= ZERO:
            continue
        billed = _quantity_in_agreed_unit(
            session, tenant_id, line, _invoice_lines(session, tenant_id, line.id)
        )
        if billed is None:
            continue
        unbilled = delivered - billed
        if unbilled <= ZERO:
            continue
        result.append(
            OperationalException(
                _identity("shipped_not_billed", line.id),
                "shipped_not_billed",
                (),
                "high",
                "Shipped and not billed",
                f"{unbilled:g} delivered without an invoice line",
                "document_line",
                line.id,
                {
                    "delivered_quantity": delivered,
                    "billed_quantity": billed,
                    "unbilled_quantity": unbilled,
                    "unit": line.unit,
                },
                _order_line_trace(commitment, line, document),
                _last_movement_at(session, tenant_id, commitment.id, "shipment"),
            )
        )
    return result


def _kept_quantity(session: Session, tenant_id: str, commitment_id: str) -> Decimal:
    """How much of a delivery the customer still has.

    Shipped less returned. Fulfilment is deliberately a different figure: the
    promise was kept when the goods went out, and a return does not undo that.
    """
    shipped = _fulfilled_quantity(session, tenant_id, commitment_id, "shipment")
    return shipped - _fulfilled_quantity(session, tenant_id, commitment_id, "return")


def _held_quantity(session: Session, tenant_id: str, commitment_id: str) -> Decimal:
    """How much of a receipt the company still has.

    Received less sent back, the mirror of what the customer kept. Only the
    class about an invoice nobody has sent uses it: an accrual for goods that
    went back is money the company is not going to owe.

    Billed and not received deliberately does *not* use it. The goods did
    arrive, and subtracting returns there would accuse a supplier of failing to
    deliver something it delivered.
    """
    received = _fulfilled_quantity(session, tenant_id, commitment_id, "receipt")
    return received - _fulfilled_quantity(
        session, tenant_id, commitment_id, "supplier_return"
    )


# The two directions of a return, and what each of them is made of. A customer
# sends goods back and the company credits them; the company sends goods back to
# a supplier and the supplier credits them. Same shape, different documents, and
# neither may quietly start reading the other's.
CUSTOMER_RETURN = ("customer_delivery", "return", "credit_note")
SUPPLIER_RETURN = ("supplier_delivery", "supplier_return", "supplier_credit_note")


def _return_exceptions(
    session: Session,
    tenant_id: str,
    class_id: str,
    *,
    side: tuple[str, str, str] = CUSTOMER_RETURN,
    uncredited_title: str = "Returned and not credited",
    overcredited_title: str = "Credited and not returned",
) -> list[OperationalException]:
    """Goods back without money back, or money back without goods.

    Two directions of one difference, so an order line produces at most one of
    them. Sharing the body is what keeps the four classes agreeing about what
    "returned" and "credited" mean — and it is what makes the buying side cost
    one parameter rather than a second implementation to drift away from the
    first.
    """
    commitment_type, movement_type, credit_type = side
    uncredited = class_id in {"returned_not_credited", "supplier_return_not_credited"}
    result: list[OperationalException] = []
    for commitment, line, document in _order_line_promises(
        session, tenant_id, commitment_type
    ):
        returned = _fulfilled_quantity(session, tenant_id, commitment.id, movement_type)
        referencing = _billing_lines(session, tenant_id, line.id)
        crediting = [
            row
            for row in referencing
            if _referencing_document_type(session, tenant_id, row) == credit_type
            and (uncredited or row.billed_document_line_id == line.id)
        ]
        billing = [
            row
            for row in referencing
            if _referencing_document_type(session, tenant_id, row)
            in {"sales_invoice", "supplier_invoice"}
        ]
        credited = _quantity_in_agreed_unit(session, tenant_id, line, crediting)
        billed = _quantity_in_agreed_unit(session, tenant_id, line, billing)
        if credited is None or billed is None:
            continue
        if uncredited:
            # Only goods somebody was charged for can need crediting. A return of
            # something never invoiced leaves nothing owing back, whichever way
            # the goods travelled.
            owed = min(returned, billed) - credited
            if returned <= ZERO or owed <= ZERO:
                continue
            title = uncredited_title
            impact = f"{owed:g} back without a credit note line"
            values = {
                "returned_quantity": returned,
                "billed_quantity": billed,
                "credited_quantity": credited,
                "uncredited_quantity": owed,
                "unit": line.unit,
            }
        else:
            # A credit with nothing coming back is a decision — "keep it" is
            # ordinary in consumer trade, and a rebate, an allowance or a price
            # correction is ordinary from a supplier — so the class waits for a
            # return before it says anything at all.
            excess = credited - returned
            if returned <= ZERO or excess <= ZERO:
                continue
            title = overcredited_title
            impact = f"{excess:g} credited without arriving"
            values = {
                "credited_quantity": credited,
                "returned_quantity": returned,
                "unreturned_quantity": excess,
                "unit": line.unit,
            }
        result.append(
            OperationalException(
                _identity(class_id, line.id),
                class_id,
                (),
                "high",
                title,
                impact,
                "document_line",
                line.id,
                values,
                _order_line_trace(commitment, line, document),
                _last_movement_at(session, tenant_id, commitment.id, movement_type),
            )
        )
    return result


def _supplier_return_not_credited_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """Goods sent back to a supplier that the supplier has not credited."""
    return _return_exceptions(
        session,
        tenant_id,
        "supplier_return_not_credited",
        side=SUPPLIER_RETURN,
        uncredited_title="Returned to supplier and not credited",
    )


def _supplier_credit_not_returned_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A supplier credit larger than what actually went back."""
    return _return_exceptions(
        session,
        tenant_id,
        "supplier_credit_not_returned",
        side=SUPPLIER_RETURN,
        overcredited_title="Supplier credited more than went back",
    )


def _referencing_document_type(
    session: Session, tenant_id: str, line: DocumentLine
) -> str:
    document = _billing_document(session, tenant_id, line)
    return document.type if document else ""


def _returned_not_credited_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return _return_exceptions(session, tenant_id, "returned_not_credited")


def _credited_not_returned_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return _return_exceptions(session, tenant_id, "credited_not_returned")


def _billing_document(
    session: Session, tenant_id: str, line: DocumentLine
) -> Document | None:
    inputs = _inputs(session, tenant_id)
    if inputs is not None and line.document_id in inputs.documents:
        return inputs.documents.get(line.document_id)
    return session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id, Document.id == line.document_id
        )
    )


def _billed_not_received_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    result: list[OperationalException] = []
    for commitment, line, document in _order_line_promises(
        session, tenant_id, "supplier_delivery"
    ):
        billing = _invoice_lines(session, tenant_id, line.id)
        # Received and not yet billed is the usual sequence, so an order line
        # nobody has billed says nothing at all.
        if not billing:
            continue
        billed = _quantity_in_agreed_unit(session, tenant_id, line, billing)
        if billed is None or billed <= ZERO:
            continue
        # The raw receipt on purpose. Goods that arrived and went back were
        # still received, and netting returns off here would report a supplier
        # as not having delivered what it delivered. What the company no longer
        # holds is Receipt not invoiced' business, and what the supplier owes
        # for it is Returned to supplier and not credited.
        received = _fulfilled_quantity(session, tenant_id, commitment.id, "receipt")
        unreceived = billed - received
        if unreceived <= ZERO:
            continue
        billing_documents = [
            _billing_document(session, tenant_id, billed_line)
            for billed_line in billing
        ]
        instants = [
            _document_instant(billing_document)
            for billing_document in billing_documents
            if billing_document is not None
            and _document_instant(billing_document) is not None
        ]
        result.append(
            OperationalException(
                _identity("billed_not_received", line.id),
                "billed_not_received",
                (),
                "high",
                "Billed and not received",
                f"{unreceived:g} billed without arriving",
                "document_line",
                line.id,
                {
                    "billed_quantity": billed,
                    "received_quantity": received,
                    "unreceived_quantity": unreceived,
                    "unit": line.unit,
                },
                _order_line_trace(commitment, line, document),
                min(instants) if instants else commitment.due_at,
            )
        )
    return result


def _units_not_comparable_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """Items whose lines the quantity classes are declining to judge.

    A decline was the right answer every time it was made and it was silent
    every time, and silence here cannot be told apart from nothing being wrong.
    The declines are read out of the same reconciliation the classes use, so
    this can never report a pair they are in fact comparing.

    One entry per item, because the statement that is missing belongs to the
    item and so does the fix. Per line it would be a wall for one thing nobody
    wrote down.

    Nothing is reported for a price left uncompared. No statement anybody could
    make would let that comparison happen, so an entry offering one would be a
    lie.
    """
    declines: list[_UnitDecline] = []
    for commitment_type in ("customer_delivery", "supplier_delivery"):
        for _commitment, line, _document in _order_line_promises(
            session, tenant_id, commitment_type
        ):
            referencing = _billing_lines(session, tenant_id, line.id)
            _, refused = _reconcile(
                session,
                tenant_id,
                line,
                [
                    row
                    for row in referencing
                    if _referencing_document_type(session, tenant_id, row)
                    in {"sales_invoice", "supplier_invoice"}
                ],
            )
            declines.extend(refused)
            # Each side is credited by its own kind of note, and each is
            # compared, so a decline on either has to be reported.
            credit_type = (
                CUSTOMER_RETURN[2]
                if commitment_type == "customer_delivery"
                else SUPPLIER_RETURN[2]
            )
            _, refused = _reconcile(
                session,
                tenant_id,
                line,
                [
                    row
                    for row in referencing
                    if _referencing_document_type(session, tenant_id, row)
                    == credit_type
                ],
            )
            declines.extend(refused)
    by_item: dict[str, list[_UnitDecline]] = {}
    for decline in declines:
        # A line naming no item has nothing to state a relation on and no entry
        # to carry it, so it is left exactly where it was.
        if decline.item_id:
            by_item.setdefault(decline.item_id, []).append(decline)
    result: list[OperationalException] = []
    for item_id in sorted(by_item):
        item = _item(session, tenant_id, item_id)
        if item is None:
            continue
        rows = by_item[item_id]
        units = sorted(
            {unit for row in rows for unit in (row.agreed_unit, row.recorded_unit)}
        )
        line_ids = sorted({line_id for row in rows for line_id in row.line_ids})
        affected = len(line_ids)
        # A relation nobody stated is the more fundamental of the two and its
        # exit is a different one, so it is what the entry says when both appear.
        missing = any(row.reason == "no_stated_relation" for row in rows)
        factor = Decimal(item.conversion_factor)
        result.append(
            OperationalException(
                _identity("units_not_comparable", item_id),
                "units_not_comparable",
                (),
                "normal",
                "Units cannot be reconciled",
                f"{affected} {'line' if affected == 1 else 'lines'} in "
                f"{' and '.join(units)} left unjudged: "
                + (
                    "this item states no conversion between them"
                    if missing
                    else f"the stated conversion of {factor:g} does not divide evenly"
                ),
                "item",
                item_id,
                {
                    "units": units,
                    "stock_unit": item.unit,
                    "purchase_unit": item.purchase_unit,
                    "conversion_factor": factor,
                    "reason": (
                        "no_stated_relation"
                        if missing
                        else "conversion_leaves_a_remainder"
                    ),
                    "affected_lines": affected,
                },
                {"item_id": item_id, "document_line_ids": line_ids},
                # There is no moment at which a company failed to state a
                # relation, so these order by the item's own identity.
                None,
            )
        )
    return result


def _invoice_price_differs_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    result: list[OperationalException] = []
    agreed_line = aliased(DocumentLine)
    agreed_document = aliased(Document)
    rows = session.execute(
        select(DocumentLine, Document, agreed_line, agreed_document)
        .join(
            Document,
            (Document.tenant_id == DocumentLine.tenant_id)
            & (Document.id == DocumentLine.document_id),
        )
        .join(
            agreed_line,
            (agreed_line.tenant_id == DocumentLine.tenant_id)
            & (agreed_line.id == DocumentLine.billed_document_line_id),
        )
        .join(
            agreed_document,
            (agreed_document.tenant_id == agreed_line.tenant_id)
            & (agreed_document.id == agreed_line.document_id),
        )
        .where(
            DocumentLine.tenant_id == tenant_id,
            DocumentLine.billed_document_line_id.is_not(None),
        )
        .order_by(DocumentLine.id)
    ).all()
    for line, document, agreed, order in rows:
        # A credit note names the same order line and is not a bill, so it is not
        # something an agreed price can be compared against.
        if document.type not in {"sales_invoice", "supplier_invoice"}:
            continue
        # A price per box and a price per piece are not the same figure, so a
        # pair recorded in different units is left alone rather than compared.
        if not _prices_comparable(line, agreed):
            continue
        difference = Decimal(line.unit_price) - Decimal(agreed.unit_price)
        if difference == ZERO:
            continue
        result.append(
            OperationalException(
                _identity("invoice_price_differs", line.id),
                "invoice_price_differs",
                (),
                "high",
                "Invoice price differs from the agreement",
                f"{abs(difference):g} {document.currency} per {line.unit} "
                + ("above" if difference > ZERO else "below")
                + " the agreed price",
                "document_line",
                line.id,
                {
                    "agreed_unit_price": Decimal(agreed.unit_price),
                    "billed_unit_price": Decimal(line.unit_price),
                    "unit_price_difference": difference,
                    "unit": line.unit,
                    "currency": document.currency,
                },
                {
                    "document_line_id": line.id,
                    "document_id": document.id,
                    "billed_document_line_id": agreed.id,
                    "billed_document_id": order.id,
                    "source_record_id": document.source_record_id,
                },
                _document_instant(document),
            )
        )
    return result


def _source_failures(session: Session, tenant_id: str) -> list[OperationalException]:
    result = []
    rows = session.execute(
        select(ImportJob, SourceRecord)
        .join(
            SourceRecord,
            (SourceRecord.tenant_id == ImportJob.tenant_id)
            & (SourceRecord.id == ImportJob.source_record_id),
        )
        .where(ImportJob.tenant_id == tenant_id, ImportJob.status == "failed")
    )
    for job, source in rows:
        error = job.error.strip() or "Source interpretation failed without details."
        result.append(
            OperationalException(
                _identity("source_interpretation_failure", job.id),
                "source_interpretation_failure",
                (),
                "high",
                "Source interpretation failure",
                error,
                "import_job",
                job.id,
                {"status": job.status, "error": error, "attempts": job.attempts},
                {"import_job_id": job.id, "source_record_id": source.id},
                job.created_at,
            )
        )
    return result


def _silent_source_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    # Only a declared, active capability promises delivery. Ingestion does not
    # check that arriving records belong to one, so a capability with no records
    # and records with no capability both exist; only the declared side is
    # watched.
    result = []
    declared = session.execute(
        select(SourceCapability, SourceSystem)
        .join(
            SourceSystem,
            (SourceSystem.tenant_id == SourceCapability.tenant_id)
            & (SourceSystem.id == SourceCapability.source_system_id),
        )
        .where(
            SourceCapability.tenant_id == tenant_id,
            SourceCapability.is_active.is_(True),
        )
    )
    for capability, system in declared:
        records = list(
            session.scalars(
                select(SourceRecord)
                .where(
                    SourceRecord.tenant_id == tenant_id,
                    SourceRecord.source_system == system.code,
                    SourceRecord.source_type == capability.source_type,
                )
                .order_by(SourceRecord.received_at.desc(), SourceRecord.id.desc())
                .limit(SILENT_SOURCE_HISTORY)
            )
        )
        if len(records) < SILENT_SOURCE_MIN_HISTORY:
            continue
        moments = sorted(row.received_at for row in records)
        expected_pause = max(
            (later - earlier for earlier, later in pairwise(moments)),
            default=timedelta(0),
        )
        last_received_at = moments[-1]
        silence = as_of - last_received_at
        if silence <= max(expected_pause * SILENT_SOURCE_MULTIPLE, SILENT_SOURCE_FLOOR):
            continue
        silent_hours = int(silence.total_seconds() // 3600)
        expected_hours = int(expected_pause.total_seconds() // 3600)
        result.append(
            OperationalException(
                _identity("silent_source", capability.id),
                "silent_source",
                (),
                "high",
                "Silent source",
                f"Silent for {silent_hours} hours, "
                + (
                    "with no pause ever observed"
                    if expected_hours == 0
                    else f"against a usual pause of at most {expected_hours}"
                ),
                "source_capability",
                capability.id,
                {
                    "last_received_at": last_received_at,
                    "as_of": as_of,
                    "silent_hours": silent_hours,
                    "expected_pause_hours": expected_hours,
                    "history_size": len(records),
                },
                {
                    "source_capability_id": capability.id,
                    "source_system_id": system.id,
                    "source_record_id": records[0].id,
                },
                last_received_at,
            )
        )
    return result


def _movement_exceptions(
    session: Session, tenant_id: str
) -> list[OperationalException]:
    rows = session.scalars(
        select(Movement).where(
            Movement.tenant_id == tenant_id,
            Movement.type.in_(("shipment", "receipt", "return")),
            Movement.commitment_id.is_(None),
            Movement.source_record_id.is_(None),
            ~Movement.id.in_(
                select(MovementCorrection.original_movement_id).where(
                    MovementCorrection.tenant_id == tenant_id
                )
            ),
        )
    )
    return [
        OperationalException(
            _identity("unexplained_movement", row.id),
            "unexplained_movement",
            (),
            "normal",
            "Unexplained movement",
            f"{row.type} of {row.quantity:g} has no commitment or source",
            "movement",
            row.id,
            {
                "movement_type": row.type,
                "quantity": row.quantity,
                "occurred_at": row.occurred_at,
            },
            {
                "movement_id": row.id,
                "commitment_id": None,
                "source_record_id": None,
                "commitment_absent": True,
                "source_absent": True,
            },
            row.occurred_at,
        )
        for row in rows
    ]


def _stock_coverage_exceptions(
    session: Session, tenant_id: str
) -> list[OperationalException]:
    # Reserving cannot over-allocate, so this reports a reservation that lost
    # its backing afterwards. The commitment-level classes cannot see it: the
    # reservation still exists and still covers the remaining quantity.
    from reality.services.core import active_reserved, stock_at

    result = []
    item_ids = session.scalars(
        select(Reservation.item_id)
        .where(Reservation.tenant_id == tenant_id, Reservation.status == "active")
        .distinct()
    ).all()
    for item_id in item_ids:
        observed = stock_at(session, tenant_id, item_id)
        reserved = active_reserved(session, tenant_id, item_id)
        if reserved <= observed:
            continue
        rows = session.scalars(
            select(Reservation)
            .where(
                Reservation.tenant_id == tenant_id,
                Reservation.item_id == item_id,
                Reservation.status == "active",
            )
            .order_by(Reservation.reserved_at, Reservation.id)
        ).all()
        commitment_ids = sorted({row.commitment_id for row in rows})
        shortfall = reserved - observed
        promises = len(commitment_ids)
        result.append(
            OperationalException(
                _identity("reservation_exceeds_stock", item_id),
                "reservation_exceeds_stock",
                (),
                "high",
                "Reservation exceeds stock",
                f"{shortfall:g} reserved without stock across {promises} "
                + ("promise" if promises == 1 else "promises"),
                "item",
                item_id,
                {
                    "observed_stock": observed,
                    "reserved_quantity": reserved,
                    "shortfall": shortfall,
                    "competing_commitments": promises,
                },
                # Which promise fails is a decision, not an observation: the
                # model defines no allocation priority, so every competing
                # promise is named and none is blamed.
                {
                    "item_id": item_id,
                    "reservation_ids": [row.id for row in rows],
                    "commitment_ids": commitment_ids,
                },
                rows[0].reserved_at if rows else None,
            )
        )
    return result


def _open_item_exceptions(
    session: Session,
    tenant_id: str,
    as_of: datetime,
    *,
    document_type: str,
    class_id: str,
    title: str,
) -> list[OperationalException]:
    """One overdue open item, whichever side of the ledger it sits on.

    The receivable and the payable differ only in the document type and the
    words. Sharing the body is what keeps them agreeing about what "due" and
    "outstanding" mean.
    """
    # The queue consumes the one aging rule rather than deriving a due date of
    # its own, so it cannot disagree with any other consumer of that rule.
    result = []
    for row in _aging_register(session, tenant_id, as_of):
        document = row["document"]
        outstanding = Decimal(row["open"])
        due_date = row["due_date"]
        if (
            document.type != document_type
            or row["status"] not in {"open", "partial"}
            or outstanding <= ZERO
            or due_date is None
            or due_date >= as_of.date()
        ):
            continue
        days_overdue = row["days_overdue"]
        # A customer who took the discount they were offered has not underpaid,
        # and this queue used to accuse them of it every day. The reason rides
        # along rather than suppressing the entry: the remainder is genuinely
        # open, and hiding a real balance would be a worse lie than the one it
        # was fixing.
        discounted = _discount_explains_remainder(session, tenant_id, row)
        result.append(
            OperationalException(
                _identity(class_id, document.id),
                class_id,
                ("early_payment_discount_taken",) if discounted else (),
                "high",
                title,
                f"{outstanding:g} {document.currency} overdue by "
                + ("1 day" if days_overdue == 1 else f"{days_overdue} days"),
                "document",
                document.id,
                {
                    "due_date": due_date,
                    "as_of": as_of,
                    "days_overdue": days_overdue,
                    "gross_amount": Decimal(document.gross_amount),
                    "settled_amount": Decimal(row["settled"]),
                    "outstanding_amount": outstanding,
                    "currency": document.currency,
                },
                {
                    "document_id": document.id,
                    "ledger_entry_id": row["control"].id,
                    "source_record_id": document.source_record_id,
                },
                datetime(due_date.year, due_date.month, due_date.day, tzinfo=UTC),
            )
        )
    return result


def _settlement_instants(
    session: Session, tenant_id: str, control: LedgerEntry
) -> list[datetime]:
    """When each settlement of one open item actually happened.

    The counterpart of every active allocation touching this document's control
    entry, whichever side of the allocation it sits on.
    """
    from reality.services.core import active_settlement_allocations

    counterparts = []
    for row in active_settlement_allocations(
        session, tenant_id, entry_ids={control.id}
    ):
        if row.invoice_ledger_entry_id == control.id:
            counterparts.append(row.payment_ledger_entry_id)
        elif row.payment_ledger_entry_id == control.id:
            counterparts.append(row.invoice_ledger_entry_id)
    if not counterparts:
        return []
    return [
        entry.effective_at
        for entry in session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.id.in_(counterparts),
            )
        )
    ]


def _discount_explains_remainder(
    session: Session, tenant_id: str, row: dict[str, Any]
) -> bool:
    """Whether what is left unpaid is the discount the term granted.

    Three things must hold. The term states a discount at all; every settlement
    of the invoice arrived on or before the deadline, because an invoice paid in
    two parts with one of them late was not settled early; and the remainder is
    no more than the agreed rate allows.

    That last test is the one that could have authored money and does not. It
    would be natural to work out what the rate is worth and compare against it,
    and that is a division producing a figure nobody agreed, with a remainder to
    round. Both sides are multiplied out instead:

        remainder x 100  <=  rate x gross

    **A division anywhere near this function is a defect regardless of what it
    produces.** DR-007 of spec 088 exists to be reviewed, and a test walks the
    syntax tree of this function to keep it true.

    The comparison is against the gross amount, which is what a discount is
    agreed against in the ordinary case. Where a company grants it on the net
    amount the test is slightly generous, which is the safe direction for
    something whose whole purpose is to stop a false accusation.
    """
    term = row.get("payment_term")
    deadline = row.get("discount_date")
    if term is None or deadline is None or term.discount_percent is None:
        return False
    settled_at = _settlement_instants(session, tenant_id, row["control"])
    if not settled_at:
        return False
    if any(instant.date() > deadline for instant in settled_at):
        return False
    remainder = Decimal(row["open"])
    gross = Decimal(row["document"].gross_amount)
    return remainder * Decimal(100) <= Decimal(term.discount_percent) * gross


def _purchase_discount_available_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A supplier invoice the company can still pay less for.

    Everything here was recorded and everything is correct; the money goes
    because nobody looked before the date. The entry names the rate the company
    negotiated and the day it stops applying, and the amount the ledger holds
    open — never what the discount is worth, because that is a division
    producing money nobody agreed.

    It ends in two very different ways. Settling the invoice ends it, and so
    does the deadline passing, so silence here means the discount was taken
    *or* lost and only the payment says which. That is in the class's own
    guidance because an operator who does not know it will read silence as
    success.

    A class for a discount already lost was considered and refused: nothing
    clears it, and every class in this catalog is a condition somebody can end.
    """
    result = []
    for row in _aging_register(session, tenant_id, as_of):
        document = row["document"]
        outstanding = Decimal(row["open"])
        deadline = row["discount_date"]
        term = row["payment_term"]
        if (
            document.type != "supplier_invoice"
            or row["status"] not in {"open", "partial"}
            or outstanding <= ZERO
            or deadline is None
            or term is None
            or deadline < as_of.date()
        ):
            continue
        remaining = (deadline - as_of.date()).days
        # Normalised only for display: a rate stated as 2 must not read as
        # 2.000 because a numeric column gave it trailing zeros.
        rate = Decimal(term.discount_percent)
        result.append(
            OperationalException(
                _identity("purchase_discount_available", document.id),
                "purchase_discount_available",
                (),
                "normal",
                "Early payment discount still available",
                f"{outstanding:g} {document.currency} outstanding with "
                f"{rate.normalize():g}% "
                f"available until {deadline.isoformat()}",
                "document",
                document.id,
                {
                    "discount_percent": rate,
                    "discount_date": deadline,
                    "days_remaining": remaining,
                    "due_date": row["due_date"],
                    "outstanding_amount": outstanding,
                    "currency": document.currency,
                },
                {
                    "document_id": document.id,
                    "ledger_entry_id": row["control"].id,
                    "source_record_id": document.source_record_id,
                },
                # Soonest to expire first: it is the only one where waiting
                # another day costs anything.
                datetime(deadline.year, deadline.month, deadline.day, tzinfo=UTC),
            )
        )
    return result


def _receivable_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return _open_item_exceptions(
        session,
        tenant_id,
        as_of,
        document_type="sales_invoice",
        class_id="overdue_receivable",
        title="Overdue receivable",
    )


def _payable_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return _open_item_exceptions(
        session,
        tenant_id,
        as_of,
        document_type="supplier_invoice",
        class_id="overdue_payable",
        title="Overdue payable",
    )


def _credit_limit_exceeded_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A customer owing more than the company agreed to carry.

    The limit is read as recorded and the outstanding amount comes from the one
    open-item derivation every other money class consumes, so the figure here can
    never disagree with the aging register.
    """
    # Zero is not a limit of nothing. The column defaults to zero, so reading it
    # that way would report every customer holding a single open invoice on the
    # day this class ships.
    parties = list(
        session.scalars(
            select(Party)
            .where(Party.tenant_id == tenant_id, Party.credit_limit > ZERO)
            .order_by(Party.id)
        )
    )
    if not parties:
        return []
    rows = _open_items(session, tenant_id)
    result: list[OperationalException] = []
    for party in parties:
        # Only what is owed in the party's own currency. Converting would guess,
        # which is the rule Spec 076 applied to units.
        items = [
            row
            for row in rows
            if row["document"].party_id == party.id
            and row["document"].type == "sales_invoice"
            and row["document"].currency == party.default_currency
            and Decimal(row["open"]) > ZERO
        ]
        outstanding = sum((Decimal(row["open"]) for row in items), ZERO)
        limit = Decimal(party.credit_limit)
        # The agreed number is allowed; only past it is an excess.
        if outstanding <= limit:
            continue
        instants = [
            instant
            for instant in (_document_instant(row["document"]) for row in items)
            if instant is not None
        ]
        result.append(
            OperationalException(
                _identity("credit_limit_exceeded", party.id),
                "credit_limit_exceeded",
                (),
                "high",
                "Credit limit exceeded",
                f"{outstanding - limit:g} {party.default_currency} above the agreed limit",
                "party",
                party.id,
                {
                    "credit_limit": limit,
                    "outstanding_amount": outstanding,
                    "excess_amount": outstanding - limit,
                    "currency": party.default_currency,
                    "open_invoice_count": len(items),
                },
                {
                    "party_id": party.id,
                    "document_ids": [row["document"].id for row in items],
                },
                min(instants) if instants else None,
            )
        )
    return result


def _duplicate_supplier_invoice_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """The same supplier invoice number recorded twice.

    The grouping itself lives in the service layer, because a payment run refuses
    to pay a duplicate and has to ask the same question. This class is one of its
    two consumers, and it decides only what to say about the answer.
    """
    from reality.services.core import duplicate_supplier_invoices

    result: list[OperationalException] = []
    for duplicate, original in duplicate_supplier_invoices(
        session, tenant_id, _open_items=_open_items(session, tenant_id)
    ):
        result.append(
            OperationalException(
                _identity("duplicate_supplier_invoice", duplicate.id),
                "duplicate_supplier_invoice",
                (),
                "high",
                "Duplicate supplier invoice",
                f"{duplicate.gross_amount:g} {duplicate.currency} under a number "
                "this supplier already used",
                "document",
                duplicate.id,
                {
                    "number": duplicate.number.strip(),
                    "original_number": original.number.strip(),
                    "gross_amount": Decimal(duplicate.gross_amount),
                    "original_gross_amount": Decimal(original.gross_amount),
                    "currency": duplicate.currency,
                },
                # Both source records, because whether the second arrived
                # from a connector or was typed in decides what happens next.
                {
                    "document_id": duplicate.id,
                    "original_document_id": original.id,
                    "source_record_id": duplicate.source_record_id,
                    "original_source_record_id": original.source_record_id,
                },
                _document_instant(duplicate),
            )
        )
    return result


# Recording a document and booking it are two acts, and the distance between them
# is a business fact for four document types rather than for credit notes alone.
# Each helper below therefore takes the type it is asking about and the account
# that says that type was booked, so no two can silently start reading the same
# documents or disagree about what "booked" means.
#
# The account is always the one the document's own posting operation uses to
# refuse a second posting. `supplier_credit_note` asked `inventory` between specs
# 089 and 092 — equivalent in practice, because one posting touches both accounts
# — and was aligned so a class and its operation cannot drift apart.
SALES_INVOICE = ("sales_invoice", "sales_revenue")
SUPPLIER_INVOICE = ("supplier_invoice", "accounts_payable")
SALES_CREDIT = ("credit_note", "sales_revenue")
SUPPLIER_CREDIT = ("supplier_credit_note", "accounts_payable")


def _documents_of_type(
    session: Session, tenant_id: str, document_type: str = "credit_note"
) -> list[Document]:
    return list(
        session.scalars(
            select(Document)
            .where(Document.tenant_id == tenant_id, Document.type == document_type)
            .order_by(Document.document_date, Document.id)
        )
    )


def _account_postings(
    session: Session, tenant_id: str, account: str, documents: list[Document]
) -> dict[str, tuple[Decimal, datetime | None]]:
    """Signed balance and first effective instant per document on one account.

    One read for every document instead of two per document; a document with no
    entry on the account is absent, which is what `_is_posted` reports as unposted.
    """
    if not documents:
        return {}
    postings: dict[str, tuple[Decimal, datetime | None]] = {}
    for document_id, side, amount, effective in session.execute(
        select(
            LedgerEntry.document_id,
            LedgerEntry.debit_credit,
            func.sum(LedgerEntry.amount),
            func.min(LedgerEntry.effective_at),
        )
        .where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.account == account,
            LedgerEntry.document_id.in_([document.id for document in documents]),
        )
        .group_by(LedgerEntry.document_id, LedgerEntry.debit_credit)
    ):
        balance, first = postings.get(document_id, (ZERO, None))
        signed = Decimal(amount) if side == "debit" else -Decimal(amount)
        earliest = (
            effective
            if first is None or (effective is not None and effective < first)
            else first
        )
        postings[document_id] = (balance + signed, earliest)
    return postings


def _is_posted(
    session: Session,
    tenant_id: str,
    document: Document,
    account: str = "sales_revenue",
) -> bool:
    from reality.services.core import account_balance

    return account_balance(session, tenant_id, account, document.id) != ZERO


def _posting_threshold(
    session: Session,
    tenant_id: str,
    document_type: str = "credit_note",
    account: str = "sales_revenue",
) -> timedelta | None:
    """How long this company normally takes to book a kind of document.

    Learned from the ones it did book. Credit notes are low-volume in most
    businesses, so a company issuing a handful a year may never reach the
    minimum history and will never be judged — the weakest point of this class
    and a property of the rule rather than of the condition.

    The rule is shared between all four callers and the history deliberately is
    not. Booking a credit the company wrote itself is accounts receivable doing
    its own paperwork; booking one a supplier sent is a different process with a
    different owner; and booking a sales or supplier invoice is two more again.
    One rhythm must not judge another. Spec 080 set the same precedent when it
    gave the learned-expectation rule two more users with two different
    populations.
    """
    posted: list[tuple[datetime, timedelta]] = []
    documents = _documents_of_type(session, tenant_id, document_type)
    postings = _account_postings(session, tenant_id, account, documents)
    for document in documents:
        balance, effective = postings.get(document.id, (ZERO, None))
        if balance == ZERO:
            continue
        recorded = _document_instant(document)
        if recorded is None or effective is None:
            continue
        posted.append((effective, _lag(recorded, effective)))
    posted.sort()
    return _learned_threshold([lag for _, lag in posted], floor=CREDIT_POSTING_FLOOR)


def _sales_invoice_unposted_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A sales invoice recorded and never booked.

    The company has billed a customer and its own accounts know nothing about
    it, so nothing is owed as far as Reality is concerned: no aging, no
    reminder, no credit-limit arithmetic. The money is invisible until somebody
    books it.
    """
    return _unposted_document_exceptions(
        session,
        tenant_id,
        as_of,
        class_id="sales_invoice_unposted",
        document_type=SALES_INVOICE[0],
        account=SALES_INVOICE[1],
        title="Sales invoice not booked",
        owed_to="billed",
    )


def _supplier_invoice_unposted_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A supplier invoice recorded and never booked.

    The company owes money its books do not show, so the invoice reaches no
    payment run and no early-payment discount is offered for it.
    """
    return _unposted_document_exceptions(
        session,
        tenant_id,
        as_of,
        class_id="supplier_invoice_unposted",
        document_type=SUPPLIER_INVOICE[0],
        account=SUPPLIER_INVOICE[1],
        title="Supplier invoice not booked",
        owed_to="invoiced by the supplier",
    )


def _credit_note_unposted_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A credit promised on paper and never booked."""
    return _unposted_document_exceptions(
        session,
        tenant_id,
        as_of,
        class_id="credit_note_unposted",
        document_type=SALES_CREDIT[0],
        account=SALES_CREDIT[1],
        title="Credit note not booked",
        owed_to="promised",
    )


def _credit_note_unsettled_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """Money the company's own books say it owes a customer.

    The existing unmatched-money class does not cover this and must not be
    widened to — it walks postings that moved cash, and a credit note moves
    none.
    """
    return _unsettled_credit_exceptions(
        session,
        tenant_id,
        class_id="credit_note_unsettled",
        document_type=SALES_CREDIT[0],
        account=SALES_CREDIT[1],
        title="Credit note not given back",
        impact="owed to the customer",
    )


def _unposted_document_exceptions(
    session: Session,
    tenant_id: str,
    as_of: datetime,
    *,
    class_id: str,
    document_type: str,
    account: str,
    title: str,
    owed_to: str,
) -> list[OperationalException]:
    """Something recorded on paper and never booked, whichever kind it is.

    The four callers differ in which documents they read, which account says the
    document was booked, and whose money is wrong as a result. Sharing the body
    is what keeps them agreeing about what "booked" means.
    """
    threshold = _posting_threshold(session, tenant_id, document_type, account)
    if threshold is None:
        return []
    result: list[OperationalException] = []
    documents = _documents_of_type(session, tenant_id, document_type)
    postings = _account_postings(session, tenant_id, account, documents)
    for document in documents:
        if postings.get(document.id, (ZERO, None))[0] != ZERO:
            continue
        recorded = _document_instant(document)
        if recorded is None:
            continue
        standing = _lag(recorded, as_of)
        if standing <= threshold:
            continue
        result.append(
            OperationalException(
                _identity(class_id, document.id),
                class_id,
                (),
                "high",
                title,
                f"{document.gross_amount:g} {document.currency} {owed_to} "
                f"{standing.days:g} days ago and never booked",
                "document",
                document.id,
                {
                    "gross_amount": Decimal(document.gross_amount),
                    "currency": document.currency,
                    "standing_for_days": standing.days,
                    "threshold_days": threshold.days,
                    "norm_days": (threshold / LEARNED_MULTIPLE).days,
                },
                {
                    "document_id": document.id,
                    "source_record_id": document.source_record_id,
                },
                recorded,
            )
        )
    return result


def _unsettled_credit_exceptions(
    session: Session,
    tenant_id: str,
    *,
    class_id: str,
    document_type: str,
    account: str,
    title: str,
    impact: str,
) -> list[OperationalException]:
    """A booked credit nobody has acted on, whichever way it points.

    No threshold on either side: the obligation or the claim exists from the
    moment the credit is booked.
    """
    from reality.services.core import open_invoice_amount

    result: list[OperationalException] = []
    for document in _documents_of_type(session, tenant_id, document_type):
        if not _is_posted(session, tenant_id, document, account):
            continue
        outstanding = open_invoice_amount(session, tenant_id, document.id)
        if outstanding <= ZERO:
            continue
        result.append(
            OperationalException(
                _identity(class_id, document.id),
                class_id,
                (),
                "high",
                title,
                f"{outstanding:g} {document.currency} {impact}",
                "document",
                document.id,
                {
                    "gross_amount": Decimal(document.gross_amount),
                    "outstanding_amount": outstanding,
                    "currency": document.currency,
                },
                {
                    "document_id": document.id,
                    "source_record_id": document.source_record_id,
                },
                _document_instant(document),
            )
        )
    return result


def _supplier_credit_unposted_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A credit a supplier sent and nobody booked.

    The direction that costs money: until it is booked the payable is too high,
    and a payment run built on it pays the supplier more than it is owed.
    """
    return _unposted_document_exceptions(
        session,
        tenant_id,
        as_of,
        class_id="supplier_credit_unposted",
        document_type=SUPPLIER_CREDIT[0],
        account=SUPPLIER_CREDIT[1],
        title="Supplier credit not booked",
        owed_to="credited by the supplier",
    )


def _supplier_credit_unclaimed_exceptions(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    """A booked supplier credit nobody has netted or asked for.

    The company's own working capital sitting with a supplier.
    """
    return _unsettled_credit_exceptions(
        session,
        tenant_id,
        class_id="supplier_credit_unclaimed",
        document_type=SUPPLIER_CREDIT[0],
        account=SUPPLIER_CREDIT[1],
        title="Supplier credit not claimed",
        impact="claimable from the supplier",
    )


def _financial_exceptions(
    session: Session, tenant_id: str
) -> list[OperationalException]:
    from reality.services.core import (
        _ledger_reversal_roles,
        active_settlement_allocations,
    )

    result = []
    # Only the payment side counts here: what a control entry has given to invoices.
    allocated_by_payment: dict[str, Decimal] = {}
    for row in active_settlement_allocations(session, tenant_id):
        allocated_by_payment[row.payment_ledger_entry_id] = allocated_by_payment.get(
            row.payment_ledger_entry_id, ZERO
        ) + Decimal(row.amount)
    controls = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.account.in_(("accounts_receivable", "accounts_payable")),
            )
        )
    )
    if not controls:
        return result
    # Three reads for every control entry instead of a cash lookup and a full
    # reversal snapshot per entry; the snapshot alone hashed the whole posting
    # group each time and made this class the slowest on a large ledger.
    cash_groups = set(
        session.scalars(
            select(LedgerEntry.posting_group_id)
            .where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.account == "cash",
                LedgerEntry.posting_group_id.in_(
                    {control.posting_group_id for control in controls}
                ),
            )
            .distinct()
        )
    )
    roles = _ledger_reversal_roles(session, tenant_id, cash_groups)
    for control in controls:
        if control.posting_group_id not in cash_groups:
            continue
        if (
            roles.get(control.posting_group_id, (None, "normal"))[1]
            == "reversed_original"
        ):
            continue
        allocated = allocated_by_payment.get(control.id, ZERO)
        remaining = Decimal(control.amount) - allocated
        if remaining <= ZERO:
            continue
        result.append(
            OperationalException(
                _identity("unmatched_financial_event", control.id),
                "unmatched_financial_event",
                (),
                "high",
                "Unmatched financial event",
                f"{remaining:g} {control.currency} remains unallocated",
                "ledger_entry",
                control.id,
                {
                    "amount": control.amount,
                    "allocated_amount": allocated,
                    "unallocated_amount": remaining,
                    "currency": control.currency,
                },
                {
                    "ledger_entry_id": control.id,
                    "document_id": control.document_id,
                    "source_record_id": control.source_record_id,
                },
                control.effective_at,
            )
        )
    return result


Derivator = Callable[[Session, str, datetime], list[OperationalException]]


def _source_failure_derivator(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return _source_failures(session, tenant_id)


def _movement_derivator(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return _movement_exceptions(session, tenant_id)


def _stock_coverage_derivator(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return _stock_coverage_exceptions(session, tenant_id)


def _financial_derivator(
    session: Session, tenant_id: str, as_of: datetime
) -> list[OperationalException]:
    return _financial_exceptions(session, tenant_id)


DERIVATION_REGISTRY: dict[str, Derivator] = {
    "overdue_outgoing_customer_commitment": _overdue_outgoing_customer_commitment,
    "outgoing_commitment_at_risk": _outgoing_commitment_at_risk,
    "order_stalled": _order_stalled_exceptions,
    "overdue_incoming_supplier_commitment": _overdue_incoming_supplier_commitment,
    "shipped_not_billed": _shipped_not_billed_exceptions,
    "billed_not_received": _billed_not_received_exceptions,
    "invoice_price_differs": _invoice_price_differs_exceptions,
    "sold_below_purchase_price": _sold_below_purchase_price_exceptions,
    "returned_not_credited": _returned_not_credited_exceptions,
    "credited_not_returned": _credited_not_returned_exceptions,
    "supplier_return_not_credited": _supplier_return_not_credited_exceptions,
    "supplier_credit_not_returned": _supplier_credit_not_returned_exceptions,
    "return_unresolved": _return_unresolved_exceptions,
    "receipt_unbilled": _receipt_unbilled_exceptions,
    "units_not_comparable": _units_not_comparable_exceptions,
    "reservation_exceeds_stock": _stock_coverage_derivator,
    "silent_source": _silent_source_exceptions,
    "source_interpretation_failure": _source_failure_derivator,
    "unexplained_movement": _movement_derivator,
    "sales_invoice_unposted": _sales_invoice_unposted_exceptions,
    "supplier_invoice_unposted": _supplier_invoice_unposted_exceptions,
    "credit_note_unposted": _credit_note_unposted_exceptions,
    "credit_note_unsettled": _credit_note_unsettled_exceptions,
    "supplier_credit_unposted": _supplier_credit_unposted_exceptions,
    "supplier_credit_unclaimed": _supplier_credit_unclaimed_exceptions,
    "overdue_receivable": _receivable_exceptions,
    "credit_limit_exceeded": _credit_limit_exceeded_exceptions,
    "overdue_payable": _payable_exceptions,
    "purchase_discount_available": _purchase_discount_available_exceptions,
    "duplicate_supplier_invoice": _duplicate_supplier_invoice_exceptions,
    "unmatched_financial_event": _financial_derivator,
    "announced_return_not_arrived": _announced_return_not_arrived_exceptions,
    "commitment_hold_unreleased": _commitment_hold_unreleased_exceptions,
    "party_hold_unreleased": _party_hold_unreleased_exceptions,
    "stock_expired": _stock_expired_exceptions,
}


def operational_exceptions(
    session: Session, tenant_id: str, *, as_of: datetime | None = None
) -> list[OperationalException]:
    if session.scalar(select(Tenant.id).where(Tenant.id == tenant_id)) is None:
        from reality.services.core import NotFound

        raise NotFound("Tenant not found.")
    instant = as_of or datetime.now(UTC)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=UTC)
    commitment_classes = {
        "overdue_outgoing_customer_commitment",
        "outgoing_commitment_at_risk",
        "overdue_incoming_supplier_commitment",
    }
    with _exception_input_scope(session, tenant_id):
        rows = _commitment_exceptions(session, tenant_id, instant)
        rows.extend(
            row
            for class_id, derivator in DERIVATION_REGISTRY.items()
            if class_id not in commitment_classes
            for row in derivator(session, tenant_id, instant)
        )
    return sorted(
        rows,
        key=lambda row: (
            SEVERITY_ORDER[row.severity],
            CLASS_ORDER[row.class_id],
            row.sort_at or datetime.max.replace(tzinfo=UTC),
            row.record_id,
        ),
    )


def operational_exception_rows(
    session: Session, tenant_id: str, *, as_of: datetime | None = None
) -> list[dict[str, Any]]:
    return [
        row.to_dict() for row in operational_exceptions(session, tenant_id, as_of=as_of)
    ]


def explain_operational_exception(
    session: Session,
    tenant_id: str,
    exception_id: str,
    *,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    from reality.services.core import NotFound

    if not exception_id.startswith("exc__"):
        raise NotFound("Current operational exception not found.")
    try:
        current = operational_exceptions(session, tenant_id, as_of=as_of)
    except NotFound:
        raise NotFound("Current operational exception not found.") from None
    row = next((item for item in current if item.id == exception_id), None)
    if row is None:
        raise NotFound("Current operational exception not found.")
    result = row.to_dict()
    if row.record_type == "import_job":
        source_id = row.trace["source_record_id"]
        source = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id, SourceRecord.id == source_id
            )
        )
        result["raw_source"] = source.payload if source else None
    else:
        result["raw_source"] = None
    return result
