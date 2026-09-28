"""Customer exchanges: a replacement that settles a return instead of a credit (spec 293).

An exchange is a confirmed statement that one replacement promise answers a
stated quantity of one customer return — goods already back, or goods the
customer announced. It moves no money and creates no document. What it settles
is read, never stored: from the returned goods, from what has arrived against an
announcement, and from whether the replacement was cancelled.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from decimal import InvalidOperation as DecimalError
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    CustomerExchange,
    Item,
    Location,
    Movement,
    ReturnAnnouncement,
    SourceRecord,
)
from reality.services import core

ZERO = Decimal(0)


def _quantity(value: Any) -> Decimal:
    try:
        quantity = Decimal(str(value))
    except (DecimalError, ValueError) as error:
        raise core.InvalidOperation(
            code="customer_exchange_quantity_not_positive"
        ) from error
    if not quantity.is_finite() or quantity <= ZERO:
        raise core.InvalidOperation(code="customer_exchange_quantity_not_positive")
    return quantity


def _exchanges(
    session: Session,
    tenant_id: str,
    *,
    return_movement_id: str | None = None,
    return_announcement_id: str | None = None,
) -> list[CustomerExchange]:
    query = select(CustomerExchange).where(CustomerExchange.tenant_id == tenant_id)
    if return_movement_id is not None:
        query = query.where(CustomerExchange.return_movement_id == return_movement_id)
    if return_announcement_id is not None:
        query = query.where(
            CustomerExchange.return_announcement_id == return_announcement_id
        )
    return list(session.scalars(query.order_by(CustomerExchange.created_at)))


def _in_force(session: Session, tenant_id: str, exchange: CustomerExchange) -> Decimal:
    """How much of the return an exchange still answers.

    All of it while its replacement stands. A replacement cancelled before it
    left answers nothing; one cancelled after part of it left answers that part,
    in the ratio the exchange stated between what came back and what went out.
    """
    replacement = core._tenant_record(
        session, Commitment, tenant_id, exchange.replacement_commitment_id
    )
    if replacement.status != "cancelled":
        return Decimal(exchange.quantity)
    promised = core.commitment_quantity(session, tenant_id, replacement.id)
    shipped = core.fulfilled_quantity(session, tenant_id, replacement.id)
    if promised <= ZERO or shipped <= ZERO:
        return ZERO
    return min(
        Decimal(exchange.quantity), Decimal(exchange.quantity) * shipped / promised
    )


def _in_force_total(
    session: Session, tenant_id: str, exchanges: list[CustomerExchange]
) -> Decimal:
    return sum((_in_force(session, tenant_id, row) for row in exchanges), ZERO)


def _returned_delivery(
    session: Session,
    tenant_id: str,
    return_movement_id: str | None,
    return_announcement_id: str | None,
) -> tuple[Commitment, Movement | None, ReturnAnnouncement | None]:
    if (return_movement_id is None) == (return_announcement_id is None):
        raise core.InvalidOperation(code="customer_exchange_fields_invalid")
    if return_movement_id is not None:
        movement = core._tenant_record(session, Movement, tenant_id, return_movement_id)
        if movement.type != "return":
            raise core.InvalidOperation(code="customer_exchange_return_not_customer")
        if movement.commitment_id is None:
            raise core.InvalidOperation(code="customer_exchange_return_unlinked")
        delivery = core._tenant_record(
            session, Commitment, tenant_id, movement.commitment_id
        )
        if delivery.type != "customer_delivery":
            raise core.InvalidOperation(code="customer_exchange_return_not_customer")
        return delivery, movement, None
    announcement = core._tenant_record(
        session, ReturnAnnouncement, tenant_id, return_announcement_id
    )
    if announcement.status != "open":
        raise core.InvalidOperation(code="customer_exchange_announcement_not_open")
    delivery = core._tenant_record(
        session, Commitment, tenant_id, announcement.commitment_id
    )
    return delivery, None, announcement


def _exchanged_on_delivery(
    session: Session, tenant_id: str, delivery_id: str
) -> Decimal:
    """What exchanges answer of goods that have actually come back on a delivery."""
    return settled_by_delivery(session, tenant_id).get(delivery_id, ZERO)


def preview_customer_exchange(
    session: Session,
    tenant_id: str,
    *,
    quantity: Any,
    replacement_item_id: str,
    replacement_quantity: Any,
    reason: str,
    return_movement_id: str | None = None,
    return_announcement_id: str | None = None,
    location_id: str | None = None,
    due_at: datetime | str | None = None,
) -> dict[str, Any]:
    """Check an exchange and state exactly what recording it would create."""
    delivery, movement, announcement = _returned_delivery(
        session, tenant_id, return_movement_id, return_announcement_id
    )
    exchanged = _quantity(quantity)
    sent = _quantity(replacement_quantity)
    stated_reason = reason.strip() if isinstance(reason, str) else ""
    if not stated_reason:
        raise core.InvalidOperation(code="customer_exchange_reason_required")
    item = core._tenant_record(session, Item, tenant_id, replacement_item_id)
    location = core._tenant_record(
        session, Location, tenant_id, location_id or delivery.location_id
    )

    if movement is not None:
        exchangeable = Decimal(movement.quantity) - _in_force_total(
            session,
            tenant_id,
            _exchanges(session, tenant_id, return_movement_id=movement.id),
        )
        if movement.return_announcement_id:
            exchangeable -= _in_force_total(
                session,
                tenant_id,
                _exchanges(
                    session,
                    tenant_id,
                    return_announcement_id=movement.return_announcement_id,
                ),
            )
        if delivery.document_line_id is not None:
            # Goods credited cannot also be exchanged: that would settle them twice.
            uncredited = core.uncredited_return_quantity(
                session, tenant_id, delivery.document_line_id
            ) - _exchanged_on_delivery(session, tenant_id, delivery.id)
            if uncredited <= ZERO < exchangeable:
                raise core.InvalidOperation(code="customer_exchange_already_credited")
            exchangeable = min(exchangeable, uncredited)
        kind, return_id = "movement", movement.id
    else:
        exchangeable = Decimal(announcement.quantity) - _in_force_total(
            session,
            tenant_id,
            _exchanges(session, tenant_id, return_announcement_id=announcement.id),
        )
        kind, return_id = "announcement", announcement.id
    if exchanged > exchangeable:
        raise core.InvalidOperation(code="customer_exchange_exceeds_exchangeable")

    return {
        "returned_delivery_id": delivery.id,
        "return": {
            "kind": kind,
            "id": return_id,
            "exchangeable": str(exchangeable),
        },
        "exchanged_quantity": exchanged,
        "replacement": {
            "item_id": item.id,
            "quantity": sent,
            "location_id": location.id,
            "due_at": core.utc_datetime(due_at) if due_at else None,
        },
        "customer_id": delivery.to_party_id,
        "company_id": delivery.from_party_id,
        "reason": stated_reason,
        "money_moves": False,
    }


def record_customer_exchange(
    session: Session,
    tenant_id: str,
    *,
    quantity: Any,
    replacement_item_id: str,
    replacement_quantity: Any,
    reason: str,
    return_movement_id: str | None = None,
    return_announcement_id: str | None = None,
    location_id: str | None = None,
    due_at: datetime | str | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> CustomerExchange:
    """Record a confirmed exchange and the free replacement it promises."""
    core._require_business_mutation(session, tenant_id, "record_customer_exchange")
    with session.begin_nested():
        delivery, _, _ = _returned_delivery(
            session, tenant_id, return_movement_id, return_announcement_id
        )
        session.scalar(
            select(Commitment)
            .where(Commitment.tenant_id == tenant_id, Commitment.id == delivery.id)
            .with_for_update()
        )
        reviewed = preview_customer_exchange(
            session,
            tenant_id,
            quantity=quantity,
            replacement_item_id=replacement_item_id,
            replacement_quantity=replacement_quantity,
            reason=reason,
            return_movement_id=return_movement_id,
            return_announcement_id=return_announcement_id,
            location_id=location_id,
            due_at=due_at,
        )
        replacement_spec = reviewed["replacement"]
        source = core.create_master_source_record(
            session,
            tenant_id,
            "customer_exchange",
            "manual",
            action_id or core.uid("customer-exchange"),
            {
                "return_movement_id": return_movement_id,
                "return_announcement_id": return_announcement_id,
                "quantity": str(reviewed["exchanged_quantity"]),
                "replacement_item_id": replacement_spec["item_id"],
                "replacement_quantity": str(replacement_spec["quantity"]),
                "location_id": replacement_spec["location_id"],
                "due_at": replacement_spec["due_at"].isoformat()
                if replacement_spec["due_at"]
                else None,
                "reason": reviewed["reason"],
            },
            action_id=action_id,
            _commit=False,
        )
        replacement = core.create_commitment(
            session,
            tenant_id,
            "customer_delivery",
            reviewed["company_id"],
            reviewed["customer_id"],
            replacement_spec["item_id"],
            replacement_spec["location_id"],
            replacement_spec["quantity"],
            replacement_spec["due_at"],
            amount="0",
            action_id=action_id,
            _commit=False,
        )
        exchange = CustomerExchange(
            id=core.uid("cex"),
            tenant_id=tenant_id,
            return_movement_id=return_movement_id,
            return_announcement_id=return_announcement_id,
            replacement_commitment_id=replacement.id,
            quantity=reviewed["exchanged_quantity"],
            reason=reviewed["reason"],
            source_record_id=source.id,
        )
        session.add(exchange)
        session.flush()
        core.emit_business_event(
            session,
            tenant_id,
            "exchange.recorded",
            "customer_exchange",
            exchange.id,
            {
                "returned_delivery_id": delivery.id,
                "replacement_commitment_id": replacement.id,
                "quantity": str(exchange.quantity),
                "reason": exchange.reason,
            },
            source_record_id=source.id,
            action_id=action_id,
        )
    if _commit:
        session.commit()
    return exchange


def settled_by_delivery(session: Session, tenant_id: str) -> dict[str, Decimal]:
    """Per returned customer delivery, how much of what came back exchanges answer.

    Capped by what has arrived: goods announced and not yet back are not settled
    by an exchange, they are still owed by the customer.
    """
    rows = list(
        session.execute(
            select(CustomerExchange, Movement, ReturnAnnouncement)
            .outerjoin(
                Movement,
                (Movement.tenant_id == CustomerExchange.tenant_id)
                & (Movement.id == CustomerExchange.return_movement_id),
            )
            .outerjoin(
                ReturnAnnouncement,
                (ReturnAnnouncement.tenant_id == CustomerExchange.tenant_id)
                & (ReturnAnnouncement.id == CustomerExchange.return_announcement_id),
            )
            .where(CustomerExchange.tenant_id == tenant_id)
        )
    )
    by_return: dict[tuple[str, str], list[CustomerExchange]] = defaultdict(list)
    caps: dict[tuple[str, str], Decimal] = {}
    deliveries: dict[tuple[str, str], str] = {}
    for exchange, movement, announcement in rows:
        if movement is not None:
            key = ("movement", movement.id)
            caps[key] = Decimal(movement.quantity)
            deliveries[key] = movement.commitment_id
        else:
            key = ("announcement", announcement.id)
            if key not in caps:
                caps[key] = core.arrived_against_announcement(
                    session, tenant_id, announcement.id
                )
            deliveries[key] = announcement.commitment_id
        by_return[key].append(exchange)
    settled: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for key, exchanges in by_return.items():
        answered = min(_in_force_total(session, tenant_id, exchanges), caps[key])
        if answered > ZERO:
            settled[deliveries[key]] += answered
    return dict(settled)


def customer_exchange_detail(
    session: Session,
    tenant_id: str,
    *,
    exchange_id: str | None = None,
    return_movement_id: str | None = None,
    replacement_commitment_id: str | None = None,
) -> dict[str, Any]:
    """What an exchange replaced, what it sent, and what it still settles."""
    query = select(CustomerExchange).where(CustomerExchange.tenant_id == tenant_id)
    if exchange_id is not None:
        query = query.where(CustomerExchange.id == exchange_id)
    elif return_movement_id is not None:
        query = query.where(CustomerExchange.return_movement_id == return_movement_id)
    elif replacement_commitment_id is not None:
        query = query.where(
            CustomerExchange.replacement_commitment_id == replacement_commitment_id
        )
    else:
        raise core.InvalidOperation(code="customer_exchange_fields_invalid")
    exchange = session.scalars(query.order_by(CustomerExchange.created_at)).first()
    if exchange is None:
        raise core.NotFound(code="customer_exchange_not_found")
    delivery, movement, announcement = _returned_delivery_of(
        session, tenant_id, exchange
    )
    replacement = core._tenant_record(
        session, Commitment, tenant_id, exchange.replacement_commitment_id
    )
    source = core._tenant_record(
        session, SourceRecord, tenant_id, exchange.source_record_id
    )
    arrived = (
        Decimal(movement.quantity)
        if movement is not None
        else core.arrived_against_announcement(session, tenant_id, announcement.id)
    )
    in_force = _in_force(session, tenant_id, exchange)
    return {
        "id": exchange.id,
        "returned_delivery_id": delivery.id,
        "return": {
            "kind": "movement" if movement is not None else "announcement",
            "id": movement.id if movement is not None else announcement.id,
        },
        "quantity": str(exchange.quantity),
        "reason": exchange.reason,
        "replacement": {
            "commitment_id": replacement.id,
            "item_id": replacement.item_id,
            "quantity": str(
                core.commitment_quantity(session, tenant_id, replacement.id)
            ),
            "fulfilled": str(
                core.fulfilled_quantity(session, tenant_id, replacement.id)
            ),
            "status": replacement.status,
        },
        "settles": str(min(in_force, arrived)),
        "outstanding": str(max(in_force - arrived, ZERO)),
        "source_record_id": source.id,
        "action_id": source.external_id,
        "created_at": exchange.created_at.isoformat(),
    }


def _returned_delivery_of(
    session: Session, tenant_id: str, exchange: CustomerExchange
) -> tuple[Commitment, Movement | None, ReturnAnnouncement | None]:
    if exchange.return_movement_id is not None:
        movement = core._tenant_record(
            session, Movement, tenant_id, exchange.return_movement_id
        )
        return (
            core._tenant_record(session, Commitment, tenant_id, movement.commitment_id),
            movement,
            None,
        )
    announcement = core._tenant_record(
        session, ReturnAnnouncement, tenant_id, exchange.return_announcement_id
    )
    return (
        core._tenant_record(session, Commitment, tenant_id, announcement.commitment_id),
        None,
        announcement,
    )


def exchanges_by_announcement(
    session: Session, tenant_id: str
) -> dict[str, list[CustomerExchange]]:
    """Every advance exchange, grouped by the announcement it answers."""
    grouped: dict[str, list[CustomerExchange]] = defaultdict(list)
    for exchange in session.scalars(
        select(CustomerExchange)
        .where(
            CustomerExchange.tenant_id == tenant_id,
            CustomerExchange.return_announcement_id.is_not(None),
        )
        .order_by(CustomerExchange.created_at, CustomerExchange.id)
    ):
        grouped[exchange.return_announcement_id].append(exchange)
    return dict(grouped)


def exchanges_without_return(session: Session, tenant_id: str) -> list[dict[str, Any]]:
    """Advance exchanges whose announcement was withdrawn after the replacement left.

    The customer said the goods would come back, received a replacement, and then
    said they would not. What the replacement answered is still owed. Goods count as
    returned when they arrived against the announcement before it was withdrawn, or
    later as an ordinary return on the same delivery that nothing else has claimed,
    in the order the exchanges were recorded.
    """
    result: list[dict[str, Any]] = []
    for announcement_id, exchanges in exchanges_by_announcement(
        session, tenant_id
    ).items():
        announcement = core._tenant_record(
            session, ReturnAnnouncement, tenant_id, announcement_id
        )
        if announcement.status != "withdrawn":
            continue
        arrived = core.arrived_against_announcement(
            session, tenant_id, announcement_id
        ) + _later_unclaimed_returns(session, tenant_id, announcement)
        for exchange in exchanges:
            in_force = _in_force(session, tenant_id, exchange)
            answered = min(in_force, arrived)
            arrived -= answered
            shipped = core.fulfilled_quantity(
                session, tenant_id, exchange.replacement_commitment_id
            )
            if shipped <= ZERO or in_force - answered <= ZERO:
                continue
            result.append(
                {
                    "exchange": exchange,
                    "announcement": announcement,
                    "exchanged_quantity": in_force,
                    "arrived_quantity": answered,
                    "unreturned_quantity": in_force - answered,
                    "replacement_shipped_quantity": shipped,
                }
            )
    return result


def _later_unclaimed_returns(
    session: Session, tenant_id: str, announcement: ReturnAnnouncement
) -> Decimal:
    """Ordinary returns on the delivery after the withdrawal, not exchanged themselves."""
    later = session.scalars(
        select(Movement).where(
            Movement.tenant_id == tenant_id,
            Movement.type == "return",
            Movement.commitment_id == announcement.commitment_id,
            Movement.return_announcement_id.is_(None),
            Movement.occurred_at >= announcement.closed_at,
        )
    )
    unclaimed = ZERO
    for movement in later:
        claimed = _in_force_total(
            session,
            tenant_id,
            _exchanges(session, tenant_id, return_movement_id=movement.id),
        )
        unclaimed += max(Decimal(movement.quantity) - claimed, ZERO)
    return unclaimed


def exchange_links(
    session: Session,
    tenant_id: str,
    *,
    movement: Movement | None = None,
    commitment_id: str | None = None,
) -> list[dict[str, str]]:
    """The records an exchange connects, seen from a return or from a replacement.

    From returned goods: the exchange and the replacement it sent. From a
    replacement: the exchange, the delivery it replaces and the goods that came
    back. Read only for explanations; nothing about settlement is decided here.
    """
    links: list[dict[str, str]] = []
    if movement is not None and movement.type == "return":
        answering = _exchanges(session, tenant_id, return_movement_id=movement.id)
        if movement.return_announcement_id:
            answering += _exchanges(
                session,
                tenant_id,
                return_announcement_id=movement.return_announcement_id,
            )
        for exchange in answering:
            links += [
                {"kind": "customer_exchange", "id": exchange.id, "label": "Exchange"},
                {
                    "kind": "commitment",
                    "id": exchange.replacement_commitment_id,
                    "label": "Replacement delivery",
                },
            ]
        return links
    replacement_id = commitment_id or (movement.commitment_id if movement else None)
    if replacement_id is None:
        return links
    exchange = session.scalar(
        select(CustomerExchange).where(
            CustomerExchange.tenant_id == tenant_id,
            CustomerExchange.replacement_commitment_id == replacement_id,
        )
    )
    if exchange is None:
        return links
    delivery, returned, announcement = _returned_delivery_of(
        session, tenant_id, exchange
    )
    links += [
        {"kind": "customer_exchange", "id": exchange.id, "label": "Exchange"},
        {"kind": "commitment", "id": delivery.id, "label": "Replaced delivery"},
    ]
    if returned is not None:
        links.append({"kind": "movement", "id": returned.id, "label": "Returned goods"})
    else:
        links.append(
            {
                "kind": "return_announcement",
                "id": announcement.id,
                "label": "Return announcement",
            }
        )
    return links
