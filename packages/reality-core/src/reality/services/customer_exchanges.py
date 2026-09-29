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

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    CustomerExchange,
    Item,
    Location,
    Movement,
    MovementCorrection,
    ReturnAnnouncement,
    SourceRecord,
)
from reality.services import core
from reality.services.core import emit_business_event

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


class _Accounting:
    """Which goods that came back on one delivery answer which exchange.

    Every returned unit is counted once. A return a correction voided counts as
    nothing. Goods arriving against an announcement answer its advance exchanges
    first, in the order they arrived; once the customer withdrew the announcement,
    a later ordinary return on the same delivery may answer them too. Whatever is
    left of a return answers the exchanges recorded on that return itself.
    """

    def __init__(self, session: Session, tenant_id: str, delivery_id: str) -> None:
        returns = list(
            session.scalars(
                select(Movement)
                .where(
                    Movement.tenant_id == tenant_id,
                    Movement.type == "return",
                    Movement.commitment_id == delivery_id,
                )
                .order_by(Movement.occurred_at, Movement.id)
            )
        )
        voided = set(
            session.scalars(
                select(MovementCorrection.original_movement_id).where(
                    MovementCorrection.tenant_id == tenant_id,
                    MovementCorrection.original_movement_id.in_(
                        [row.id for row in returns]
                    ),
                )
            )
        )
        self.effective = {
            row.id: ZERO if row.id in voided else Decimal(row.quantity)
            for row in returns
        }
        announcements = list(
            session.scalars(
                select(ReturnAnnouncement).where(
                    ReturnAnnouncement.tenant_id == tenant_id,
                    ReturnAnnouncement.commitment_id == delivery_id,
                )
            )
        )
        self.announcements = {row.id: row for row in announcements}
        movement_ids = [row.id for row in returns]
        exchanges = list(
            session.scalars(
                select(CustomerExchange)
                .where(
                    CustomerExchange.tenant_id == tenant_id,
                    or_(
                        CustomerExchange.return_movement_id.in_(movement_ids),
                        CustomerExchange.return_announcement_id.in_(
                            list(self.announcements)
                        ),
                    ),
                )
                .order_by(CustomerExchange.created_at, CustomerExchange.id)
            )
        )
        self.in_force = {
            row.id: _in_force(session, tenant_id, row) for row in exchanges
        }
        self.on_movement: dict[str, list[CustomerExchange]] = defaultdict(list)
        self.in_advance: dict[str, list[CustomerExchange]] = defaultdict(list)
        for row in exchanges:
            if row.return_movement_id:
                self.on_movement[row.return_movement_id].append(row)
            else:
                self.in_advance[row.return_announcement_id].append(row)
        self.arrived = {
            announcement_id: sum(
                (
                    self.effective[row.id]
                    for row in returns
                    if row.return_announcement_id == announcement_id
                ),
                ZERO,
            )
            for announcement_id in self.announcements
        }

        # Arrivals answer advance exchanges before anything else.
        self.answering: dict[str, Decimal] = defaultdict(lambda: ZERO)
        self.answered: dict[str, Decimal] = defaultdict(lambda: ZERO)
        remaining = {
            announcement_id: self._advance_total(announcement_id)
            for announcement_id in self.announcements
        }
        for row in returns:
            owner = row.return_announcement_id
            if owner in remaining and remaining[owner] > ZERO:
                share = min(self.effective[row.id], remaining[owner])
                self.answering[row.id] += share
                self.answered[owner] += share
                remaining[owner] -= share
        withdrawn = sorted(
            (
                row
                for row in announcements
                if row.status == "withdrawn" and remaining[row.id] > ZERO
            ),
            key=lambda row: (row.closed_at, row.id),
        )
        for announcement in withdrawn:
            for row in returns:
                if (
                    row.return_announcement_id is not None
                    or announcement.closed_at is None
                    or row.occurred_at < announcement.closed_at
                    or remaining[announcement.id] <= ZERO
                ):
                    continue
                share = min(self.free(row.id), remaining[announcement.id])
                if share > ZERO:
                    self.answering[row.id] += share
                    self.answered[announcement.id] += share
                    remaining[announcement.id] -= share

        # What each exchange settles of goods that are actually back.
        self.settles: dict[str, Decimal] = {}
        for announcement_id, rows in self.in_advance.items():
            left = self.answered[announcement_id]
            for row in rows:
                share = min(self.in_force[row.id], left)
                self.settles[row.id] = share
                left -= share
        for movement_id, rows in self.on_movement.items():
            left = self.effective.get(movement_id, ZERO) - self.answering[movement_id]
            for row in rows:
                share = max(min(self.in_force[row.id], left), ZERO)
                self.settles[row.id] = share
                left -= share

    def _advance_total(self, announcement_id: str) -> Decimal:
        return sum(
            (self.in_force[row.id] for row in self.in_advance.get(announcement_id, [])),
            ZERO,
        )

    def free(self, movement_id: str) -> Decimal:
        """What of one return neither an advance nor its own exchanges answer."""
        return (
            self.effective.get(movement_id, ZERO)
            - self.answering[movement_id]
            - sum(
                (
                    self.in_force[row.id]
                    for row in self.on_movement.get(movement_id, [])
                ),
                ZERO,
            )
        )

    def announcement_exchangeable(self, announcement: ReturnAnnouncement) -> Decimal:
        """Announced goods not yet back and not yet exchanged in advance."""
        return Decimal(announcement.quantity) - max(
            self._advance_total(announcement.id), self.arrived[announcement.id]
        )

    def settled(self) -> Decimal:
        return sum(self.settles.values(), ZERO)


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

    accounting = _Accounting(session, tenant_id, delivery.id)
    if movement is not None:
        exchangeable = accounting.free(movement.id)
        if delivery.document_line_id is not None:
            # Goods credited cannot also be exchanged: that would settle them twice.
            uncredited = (
                core.uncredited_return_quantity(
                    session, tenant_id, delivery.document_line_id
                )
                - accounting.settled()
            )
            if uncredited <= ZERO < exchangeable:
                raise core.InvalidOperation(code="customer_exchange_already_credited")
            exchangeable = min(exchangeable, uncredited)
        kind, return_id = "movement", movement.id
    else:
        exchangeable = accounting.announcement_exchangeable(announcement)
        kind, return_id = "announcement", announcement.id
    exchangeable = max(exchangeable, ZERO)
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
        emit_business_event(
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

    Goods announced and not yet back are not settled by an exchange; they are still
    owed by the customer. The per-delivery rule is `_Accounting`.
    """
    deliveries = set(
        session.scalars(
            select(Movement.commitment_id)
            .join(
                CustomerExchange,
                (CustomerExchange.tenant_id == Movement.tenant_id)
                & (CustomerExchange.return_movement_id == Movement.id),
            )
            .where(Movement.tenant_id == tenant_id)
        )
    ) | set(
        session.scalars(
            select(ReturnAnnouncement.commitment_id)
            .join(
                CustomerExchange,
                (CustomerExchange.tenant_id == ReturnAnnouncement.tenant_id)
                & (CustomerExchange.return_announcement_id == ReturnAnnouncement.id),
            )
            .where(ReturnAnnouncement.tenant_id == tenant_id)
        )
    )
    settled: dict[str, Decimal] = {}
    for delivery_id in sorted(deliveries):
        amount = _Accounting(session, tenant_id, delivery_id).settled()
        if amount > ZERO:
            settled[delivery_id] = amount
    return settled


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
    accounting = _Accounting(session, tenant_id, delivery.id)
    in_force = accounting.in_force[exchange.id]
    settles = accounting.settles.get(exchange.id, ZERO)
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
        "settles": str(settles),
        "outstanding": str(max(in_force - settles, ZERO)),
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
    said they would not. What the replacement answered is still owed. Goods count
    as returned exactly as `_Accounting` attributes them: arrivals against the
    announcement, then later ordinary returns on the same delivery nothing else
    claims.
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
        accounting = _Accounting(session, tenant_id, announcement.commitment_id)
        for exchange in exchanges:
            in_force = accounting.in_force[exchange.id]
            answered = accounting.settles.get(exchange.id, ZERO)
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
