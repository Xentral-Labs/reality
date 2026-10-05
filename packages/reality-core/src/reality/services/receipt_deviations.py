"""Receipt and shipment deviations (spec 338).

Three things goods do that an order did not ask for:

- **A wrong item.** A movement may name the line it was meant for while
  carrying another item. It moves what it carries, so stock is true, and names
  no commitment, so the line stays open for the right goods. One
  ``misdelivery`` row links the two. What is still out the wrong way, per line
  and item, is read from those rows and their movements.
- **A substitute.** A person may accept another item for a purchase line.
  Receipts of it name the line and fulfil it; the line keeps what it ordered.
- **An advice.** An inbound notice may state how much it brings for each
  purchase line. A receipt recorded into that shipment is what arrived for it.
  Advised against received, and what is still in transit, are read each time.

Nothing here is stored as a derivation (DR-002).
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    CommitmentSubstitute,
    Item,
    Misdelivery,
    Movement,
    MovementCorrection,
    ShipmentAdviceLine,
    ShipmentPackage,
    uid,
)
from reality.services.business_locks import lock_delivery_state
from reality.services.core import InvalidOperation, NotFound

ZERO = Decimal(0)
LIMIT = Decimal(10) ** 14
SUBSTITUTE_SYSTEM = "internal_substitute"

#: Per side of the trade: the movement that sends goods the wrong way, and the
#: one that brings them back.
WRONG_WAY = {
    "supplier_delivery": ("receipt", "supplier_return"),
    "customer_delivery": ("shipment", "return"),
}


def _plain(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _standing(tenant_id: str):
    """Movements no correction has voided."""
    return ~exists().where(
        MovementCorrection.tenant_id == tenant_id,
        MovementCorrection.original_movement_id == Movement.id,
    )


# --- Substitutes -----------------------------------------------------------


def accepted_substitute(
    session: Session, tenant_id: str, commitment: Commitment, item_id: str
) -> bool:
    """Whether a substitute item was accepted for this purchase promise."""
    if commitment.type != "supplier_delivery" or commitment.item_id == item_id:
        return False
    return bool(
        session.scalar(
            select(
                exists().where(
                    CommitmentSubstitute.tenant_id == tenant_id,
                    CommitmentSubstitute.commitment_id == commitment.id,
                    CommitmentSubstitute.item_id == item_id,
                )
            )
        )
    )


def substitutes_by_commitment(
    session: Session, tenant_id: str, commitment_ids: list[str]
) -> dict[str, list[CommitmentSubstitute]]:
    if not commitment_ids:
        return {}
    result: dict[str, list[CommitmentSubstitute]] = defaultdict(list)
    for row in session.scalars(
        select(CommitmentSubstitute)
        .where(
            CommitmentSubstitute.tenant_id == tenant_id,
            CommitmentSubstitute.commitment_id.in_(commitment_ids),
        )
        .order_by(CommitmentSubstitute.created_at, CommitmentSubstitute.id)
    ):
        result[row.commitment_id].append(row)
    return dict(result)


def validate_substitute(
    session: Session,
    tenant_id: str,
    commitment_id: Any,
    item_id: Any,
    reason: Any,
) -> tuple[Commitment, Item, str]:
    """
    What accepting a substitute would state, or the reason it cannot.

    BUSINESS PURPOSE:
    What accepting a substitute would state, or the reason it cannot.

    BUSINESS RULE services.receipt_deviations.validate_substitute.refusal-13:
    IF the selected delivery promise does not exist in this company:
        Refuse with commitment_not_found.

    BUSINESS RULE services.receipt_deviations.validate_substitute.refusal-15:
    IF the selected promise is not a supplier delivery:
        Refuse with substitute_purchase_only.

    BUSINESS RULE services.receipt_deviations.validate_substitute.refusal-17:
    IF the purchase promise is cancelled:
        Refuse with substitute_line_cancelled.

    BUSINESS RULE services.receipt_deviations.validate_substitute.refusal-22:
    IF the selected item does not exist in this company:
        Refuse with item_not_found.

    BUSINESS RULE services.receipt_deviations.validate_substitute.refusal-24:
    IF the proposed substitute is the originally ordered item:
        Refuse with substitute_same_item.

    BUSINESS RULE services.receipt_deviations.validate_substitute.refusal-26:
    IF the proposed substitute is not a stocked item:
        Refuse with substitute_item_not_stocked.

    BUSINESS RULE services.receipt_deviations.validate_substitute.refusal-29:
    IF the original item exists and its stock unit differs from the substitute's stock unit:
        Refuse with substitute_unit_differs.

    BUSINESS RULE services.receipt_deviations.validate_substitute.refusal-35:
    IF the reason is empty after trimming whitespace:
        Refuse with substitute_reason_required.

    BUSINESS RULE services.receipt_deviations.validate_substitute.refusal-37:
    IF this substitute has already been accepted for the purchase promise:
        Refuse with substitute_already_accepted.

    BUSINESS RULE services.receipt_deviations.validate_substitute.result:
    Return commitment, item, stated, as prepared by the preceding checks and service calls.
    """
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id, Commitment.id == str(commitment_id or "")
        )
    )
    # reality-rule: services.receipt_deviations.validate_substitute.refusal-13
    if commitment is None:
        raise NotFound(code="commitment_not_found")
    # reality-rule: services.receipt_deviations.validate_substitute.refusal-15
    if commitment.type != "supplier_delivery":
        raise InvalidOperation(code="substitute_purchase_only")
    # reality-rule: services.receipt_deviations.validate_substitute.refusal-17
    if commitment.status == "cancelled":
        raise InvalidOperation(code="substitute_line_cancelled")
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == str(item_id or ""))
    )
    # reality-rule: services.receipt_deviations.validate_substitute.refusal-22
    if item is None:
        raise NotFound(code="item_not_found")
    # reality-rule: services.receipt_deviations.validate_substitute.refusal-24
    if item.id == commitment.item_id:
        raise InvalidOperation(code="substitute_same_item")
    # reality-rule: services.receipt_deviations.validate_substitute.refusal-26
    if item.item_type != "stocked":
        raise InvalidOperation(code="substitute_item_not_stocked")
    ordered = session.get(Item, (tenant_id, commitment.item_id))
    # reality-rule: services.receipt_deviations.validate_substitute.refusal-29
    if ordered is not None and ordered.unit != item.unit:
        raise InvalidOperation(
            code="substitute_unit_differs",
            values={"ordered": ordered.unit, "substitute": item.unit},
        )
    stated = str(reason or "").strip()
    # reality-rule: services.receipt_deviations.validate_substitute.refusal-35
    if not stated:
        raise InvalidOperation(code="substitute_reason_required")
    # reality-rule: services.receipt_deviations.validate_substitute.refusal-37
    if accepted_substitute(session, tenant_id, commitment, item.id):
        raise InvalidOperation(code="substitute_already_accepted")
    # reality-rule: services.receipt_deviations.validate_substitute.result
    return commitment, item, stated


def review_substitute(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    The arguments a confirmation executes and what the person is shown.

    BUSINESS PURPOSE:
    The arguments a confirmation executes and what the person is shown.

    BUSINESS RULE services.receipt_deviations.review_substitute.refusal-4:
    IF arguments contain fields other than commitment_id, item_id and reason:
        Refuse with substitute_fields_invalid.

    BUSINESS RULE services.receipt_deviations.review_substitute.step-6:
    Run the shared validate substitute check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.receipt_deviations.review_substitute.result:
    Return normalized confirmation arguments and a review showing the ordered item, proposed substitute, purchase promise, document and stated reason.
    """
    # reality-rule: services.receipt_deviations.review_substitute.refusal-4
    if set(arguments) - {"commitment_id", "item_id", "reason"}:
        raise InvalidOperation(code="substitute_fields_invalid")
    # reality-rule: services.receipt_deviations.review_substitute.step-6
    commitment, item, reason = validate_substitute(
        session,
        tenant_id,
        arguments.get("commitment_id"),
        arguments.get("item_id"),
        arguments.get("reason"),
    )
    ordered = session.get(Item, (tenant_id, commitment.item_id))
    # reality-rule: services.receipt_deviations.review_substitute.result
    return (
        {"commitment_id": commitment.id, "item_id": item.id, "reason": reason},
        {
            "commitment_id": commitment.id,
            "document_id": commitment.document_id,
            "ordered_item": {
                "id": commitment.item_id,
                "sku": ordered.sku if ordered else None,
                "name": ordered.name if ordered else None,
            },
            "substitute_item": {"id": item.id, "sku": item.sku, "name": item.name},
            "reason": reason,
        },
    )


def accept_substitute(
    session: Session,
    tenant_id: str,
    commitment_id: str,
    item_id: str,
    reason: str,
    *,
    action_id: str | None = None,
    _commit: bool = True,
) -> CommitmentSubstitute:
    """
    Accept an item in place of what a purchase line ordered.

    BUSINESS PURPOSE:
    Accept an item in place of what a purchase line ordered.

    BUSINESS RULE services.receipt_deviations.accept_substitute.step-17:
    Require the business permission for 'accept_substitute' before changing company records.

    BUSINESS RULE services.receipt_deviations.accept_substitute.step-19:
    Run the shared validate substitute check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.receipt_deviations.accept_substitute.step-22:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.receipt_deviations.accept_substitute.step-46:
    Record the commitment.substitute_accepted audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.receipt_deviations.accept_substitute.result:
    Return row, as prepared by the preceding checks and service calls.
    """
    from reality.services.case_action_guards import guard_operation

    guard_operation(session, tenant_id, "accept_substitute", locals())
    from reality.services.core import (
        _require_business_mutation,
        emit_business_event,
        store_source_record,
    )

    # reality-rule: services.receipt_deviations.accept_substitute.step-17
    _require_business_mutation(session, tenant_id, "accept_substitute")
    lock_delivery_state(session, tenant_id)
    # reality-rule: services.receipt_deviations.accept_substitute.step-19
    commitment, item, stated = validate_substitute(
        session, tenant_id, commitment_id, item_id, reason
    )
    # reality-rule: services.receipt_deviations.accept_substitute.step-22
    source, _, _ = store_source_record(
        session,
        tenant_id,
        SUBSTITUTE_SYSTEM,
        "commitment_substitute",
        f"{commitment.id}:{item.id}",
        {
            "commitment_id": commitment.id,
            "ordered_item_id": commitment.item_id,
            "item_id": item.id,
            "reason": stated,
            "statement_id": action_id or uid("stm"),
        },
    )
    row = CommitmentSubstitute(
        id=uid("csb"),
        tenant_id=tenant_id,
        commitment_id=commitment.id,
        item_id=item.id,
        reason=stated,
        source_record_id=source.id,
    )
    session.add(row)
    session.flush()
    # reality-rule: services.receipt_deviations.accept_substitute.step-46
    emit_business_event(
        session,
        tenant_id,
        "commitment.substitute_accepted",
        "commitment",
        commitment.id,
        {
            "commitment_id": commitment.id,
            "ordered_item_id": commitment.item_id,
            "item_id": item.id,
            "reason": stated,
        },
        source_record_id=source.id,
        action_id=action_id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.receipt_deviations.accept_substitute.result
    return row


# --- Wrong items -----------------------------------------------------------


def wrong_goods_out(
    session: Session,
    tenant_id: str,
    commitment_ids: list[str] | None = None,
    *,
    excluding: str | None = None,
) -> dict[tuple[str, str], Decimal]:
    """What is still out the wrong way, per line and item: sent minus back.

    ``excluding`` leaves one movement out, so a correction's preview is judged
    as if the movement it replaces were already gone.
    """
    rows = session.execute(
        select(
            Misdelivery.commitment_id,
            Movement.item_id,
            Movement.type,
            func.sum(Movement.quantity),
        )
        .join(
            Movement,
            (Movement.tenant_id == Misdelivery.tenant_id)
            & (Movement.id == Misdelivery.movement_id),
        )
        .where(
            Misdelivery.tenant_id == tenant_id,
            _standing(tenant_id),
            *(
                [Misdelivery.commitment_id.in_(commitment_ids)]
                if commitment_ids is not None
                else []
            ),
            *([Movement.id != excluding] if excluding else []),
        )
        .group_by(Misdelivery.commitment_id, Movement.item_id, Movement.type)
    )
    out: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
    sent = {pair[0] for pair in WRONG_WAY.values()}
    for commitment_id, item_id, movement_type, quantity in rows:
        sign = 1 if movement_type in sent else -1
        out[(commitment_id, item_id)] += sign * Decimal(quantity or 0)
    return dict(out)


def validate_meant_for(
    session: Session,
    tenant_id: str,
    movement_type: str,
    item_id: str,
    quantity: Decimal,
    meant_for_commitment_id: str,
    *,
    commitment_id: str | None = None,
    _correcting: Movement | None = None,
) -> Commitment:
    """The line a wrong-item movement names, or the reason it cannot."""
    if commitment_id:
        raise InvalidOperation(code="misdelivery_commitment_both")
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.id == meant_for_commitment_id,
        )
    )
    if commitment is None:
        raise NotFound(code="commitment_not_found")
    kinds = WRONG_WAY.get(commitment.type)
    if kinds is None or movement_type not in kinds:
        raise InvalidOperation(
            code="misdelivery_movement_type",
            values={"allowed": ", ".join(kinds or ())},
        )
    if commitment.item_id == item_id or accepted_substitute(
        session, tenant_id, commitment, item_id
    ):
        raise InvalidOperation(code="misdelivery_same_item")
    if movement_type == kinds[1]:
        out = wrong_goods_out(
            session,
            tenant_id,
            [commitment.id],
            excluding=_correcting.id if _correcting is not None else None,
        ).get((commitment.id, item_id), ZERO)
        if quantity > out:
            raise InvalidOperation(
                code="misdelivery_back_exceeds_out", values={"out": _plain(out)}
            )
    return commitment


def record_misdelivery(
    session: Session,
    tenant_id: str,
    movement: Movement,
    commitment: Commitment,
    reason: str | None,
) -> Misdelivery:
    row = Misdelivery(
        id=uid("mis"),
        tenant_id=tenant_id,
        movement_id=movement.id,
        commitment_id=commitment.id,
        reason=(reason or "").strip() or None,
    )
    session.add(row)
    session.flush()
    return row


def misdeliveries_for(
    session: Session, tenant_id: str, movement_ids: list[str] | set[str]
) -> dict[str, Misdelivery]:
    ids = list(movement_ids)
    if not ids:
        return {}
    return {
        row.movement_id: row
        for row in session.scalars(
            select(Misdelivery).where(
                Misdelivery.tenant_id == tenant_id,
                Misdelivery.movement_id.in_(ids),
            )
        )
    }


def outstanding_misdeliveries(session: Session, tenant_id: str) -> list[dict[str, Any]]:
    """Every line with wrong goods still out, with what is out and since when."""
    out = wrong_goods_out(session, tenant_id)
    open_lines: dict[str, dict[str, Decimal]] = defaultdict(dict)
    for (commitment_id, item_id), quantity in out.items():
        if quantity > ZERO:
            open_lines[commitment_id][item_id] = quantity
    if not open_lines:
        return []
    first = dict(
        session.execute(
            select(Misdelivery.commitment_id, func.min(Movement.occurred_at))
            .join(
                Movement,
                (Movement.tenant_id == Misdelivery.tenant_id)
                & (Movement.id == Misdelivery.movement_id),
            )
            .where(
                Misdelivery.tenant_id == tenant_id,
                Misdelivery.commitment_id.in_(list(open_lines)),
                _standing(tenant_id),
            )
            .group_by(Misdelivery.commitment_id)
        ).all()
    )
    commitments = {
        row.id: row
        for row in session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.id.in_(list(open_lines)),
            )
        )
    }
    return [
        {
            "commitment": commitments[commitment_id],
            "items": items,
            "since": first.get(commitment_id),
        }
        for commitment_id, items in sorted(open_lines.items())
        if commitment_id in commitments
    ]


# --- Advice ----------------------------------------------------------------


def validate_advice(
    session: Session,
    tenant_id: str,
    *,
    direction: str,
    purpose: str,
    counterparty_id: str,
    advised: Any,
) -> list[tuple[Commitment, Decimal]]:
    """The advised lines a notice may state, or the reason it cannot."""
    if advised in (None, []):
        return []
    if direction != "inbound" or purpose != "supplier_delivery":
        raise InvalidOperation(code="advice_supplier_delivery_only")
    if not isinstance(advised, list):
        raise InvalidOperation(code="advice_lines_invalid")
    rows: list[tuple[Commitment, Decimal]] = []
    seen: set[str] = set()
    for line in advised:
        if not isinstance(line, dict) or set(line) - {"commitment_id", "quantity"}:
            raise InvalidOperation(code="advice_lines_invalid")
        commitment_id = str(line.get("commitment_id") or "")
        commitment = session.scalar(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id, Commitment.id == commitment_id
            )
        )
        if commitment is None:
            raise NotFound(code="commitment_not_found")
        if (
            commitment.type != "supplier_delivery"
            or commitment.from_party_id != counterparty_id
            or commitment.status == "cancelled"
        ):
            raise InvalidOperation(code="advice_line_not_this_supplier")
        if commitment.id in seen:
            raise InvalidOperation(code="advice_line_repeated")
        seen.add(commitment.id)
        try:
            quantity = Decimal(str(line.get("quantity")))
        except (ArithmeticError, ValueError):
            raise InvalidOperation(code="advice_quantity_invalid") from None
        if (
            not quantity.is_finite()
            or quantity <= ZERO
            or quantity >= LIMIT
            or quantity != quantity.quantize(Decimal("0.0001"))
        ):
            raise InvalidOperation(code="advice_quantity_invalid")
        rows.append((commitment, quantity))
    return rows


def record_advice(
    session: Session,
    tenant_id: str,
    shipment_id: str,
    rows: list[tuple[Commitment, Decimal]],
) -> list[ShipmentAdviceLine]:
    created = [
        ShipmentAdviceLine(
            id=uid("adv"),
            tenant_id=tenant_id,
            shipment_id=shipment_id,
            commitment_id=commitment.id,
            quantity=quantity,
        )
        for commitment, quantity in rows
    ]
    session.add_all(created)
    session.flush()
    return created


def _received_into(
    session: Session, tenant_id: str, shipment_ids: list[str]
) -> dict[tuple[str, str | None], Decimal]:
    """Receipts recorded into the shipments, per shipment and promise."""
    rows = session.execute(
        select(
            ShipmentPackage.shipment_id,
            Movement.commitment_id,
            func.sum(Movement.quantity),
        )
        .join(
            ShipmentPackage,
            (ShipmentPackage.tenant_id == Movement.tenant_id)
            & (ShipmentPackage.id == Movement.shipment_package_id),
        )
        .where(
            Movement.tenant_id == tenant_id,
            ShipmentPackage.shipment_id.in_(shipment_ids),
            Movement.type == "receipt",
            _standing(tenant_id),
        )
        .group_by(ShipmentPackage.shipment_id, Movement.commitment_id)
    )
    return {
        (shipment_id, commitment_id): Decimal(quantity or 0)
        for shipment_id, commitment_id, quantity in rows
    }


def advice_by_shipment(
    session: Session, tenant_id: str, shipment_ids: list[str]
) -> dict[str, list[dict[str, Any]]]:
    """Advised, received and the difference per promise, for each shipment."""
    if not shipment_ids:
        return {}
    lines = list(
        session.scalars(
            select(ShipmentAdviceLine)
            .where(
                ShipmentAdviceLine.tenant_id == tenant_id,
                ShipmentAdviceLine.shipment_id.in_(shipment_ids),
            )
            .order_by(ShipmentAdviceLine.created_at, ShipmentAdviceLine.id)
        )
    )
    if not lines:
        return {}
    received = _received_into(
        session, tenant_id, sorted({line.shipment_id for line in lines})
    )
    arrived = {shipment_id for shipment_id, _ in received}
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in lines:
        advised = Decimal(line.quantity)
        got = received.get((line.shipment_id, line.commitment_id), ZERO)
        result[line.shipment_id].append(
            {
                "commitment_id": line.commitment_id,
                "advised": _plain(advised),
                "received": _plain(got),
                "difference": _plain(got - advised),
                # Nothing received into the shipment yet: the goods are on the way.
                "in_transit": _plain(advised)
                if line.shipment_id not in arrived
                else "0",
            }
        )
    return dict(result)


def in_transit_by_commitment(
    session: Session, tenant_id: str, commitment_ids: list[str]
) -> dict[str, Decimal]:
    """What advices that have not arrived yet bring for each promise."""
    if not commitment_ids:
        return {}
    lines = list(
        session.execute(
            select(
                ShipmentAdviceLine.shipment_id,
                ShipmentAdviceLine.commitment_id,
                ShipmentAdviceLine.quantity,
            ).where(
                ShipmentAdviceLine.tenant_id == tenant_id,
                ShipmentAdviceLine.commitment_id.in_(commitment_ids),
            )
        )
    )
    if not lines:
        return {}
    arrived = {
        shipment_id
        for shipment_id, _ in _received_into(
            session, tenant_id, sorted({row.shipment_id for row in lines})
        )
    }
    result: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for shipment_id, commitment_id, quantity in lines:
        if shipment_id not in arrived:
            result[commitment_id] += Decimal(quantity)
    return dict(result)
