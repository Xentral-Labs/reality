"""Reorder points: the stock level at which a company reorders, per item and location.

Spec 302. A reorder point is a company statement and kept exactly as stated, in
the item's stock unit. Whether it is reached is never stored: the exception
class reads stock, reservations and supplier promises each time it is asked.

Setting and removing are reviewed actions. The review states what the point
was, and executing it refuses when the point has changed since, so a person
never confirms a change to a value they did not see.

Every setting and every removal is kept as a version of one source stream per
item and location (spec 320), so what a point was stays readable after it is
restated or withdrawn; the row names the statement in force.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Item, ItemReorderPoint, Location, SourceRecord, now, uid
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _require_business_mutation,
    _tenant_record,
    decimal,
    emit_business_event,
    get_tenant,
    store_source_record,
)

ZERO = Decimal(0)
SOURCE_SYSTEM = "internal_reorder_point"
LIMIT = Decimal(10) ** 14
# A review that saw no point, distinct from a call that checks nothing.
UNCHECKED: Any = object()


def _plain(value: Decimal) -> str:
    return f"{Decimal(value).normalize():f}"


def reorder_point_values(point: ItemReorderPoint | None) -> dict[str, str] | None:
    """What a review shows and an execution compares, or None without a point."""
    if point is None:
        return None
    return {
        "reorder_point": _plain(point.reorder_point),
        "reorder_quantity": _plain(point.reorder_quantity),
    }


def _row(point: ItemReorderPoint, item: Item, location: Location) -> dict[str, Any]:
    return {
        "id": point.id,
        "item_id": item.id,
        "item": item.name,
        "sku": item.sku,
        "unit": item.unit,
        "location_id": location.id,
        "location": location.name,
        "reorder_point": _plain(point.reorder_point),
        "reorder_quantity": _plain(point.reorder_quantity),
        "updated_at": point.updated_at,
        "source_record_id": point.source_record_id,
    }


def reorder_points(
    session: Session,
    tenant_id: str,
    *,
    item_id: str | None = None,
    location_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Every reorder point of the company, or those of one item or location.

    BUSINESS PURPOSE:
    Every reorder point of the company, or those of one item or location.

    BUSINESS RULE services.reorder_points.reorder_points.result:
    Return the selected records in the displayed response structure; preserve the source identifiers and stated values used by this comprehension.
    """
    get_tenant(session, tenant_id)
    query = (
        select(ItemReorderPoint, Item, Location)
        .join(
            Item,
            (Item.tenant_id == ItemReorderPoint.tenant_id)
            & (Item.id == ItemReorderPoint.item_id),
        )
        .join(
            Location,
            (Location.tenant_id == ItemReorderPoint.tenant_id)
            & (Location.id == ItemReorderPoint.location_id),
        )
        .where(ItemReorderPoint.tenant_id == tenant_id)
        .order_by(Item.sku, Location.name, ItemReorderPoint.id)
    )
    if item_id:
        query = query.where(ItemReorderPoint.item_id == item_id)
    if location_id:
        query = query.where(ItemReorderPoint.location_id == location_id)
    # reality-rule: services.reorder_points.reorder_points.result
    return [_row(*row) for row in session.execute(query)]


def current_reorder_point(
    session: Session, tenant_id: str, item_id: str, location_id: str
) -> ItemReorderPoint | None:
    return session.scalar(
        select(ItemReorderPoint).where(
            ItemReorderPoint.tenant_id == tenant_id,
            ItemReorderPoint.item_id == item_id,
            ItemReorderPoint.location_id == location_id,
        )
    )


def _subjects(
    session: Session, tenant_id: str, item_id: str, location_id: str
) -> tuple[Item, Location]:
    item = _tenant_record(session, Item, tenant_id, item_id)
    location = _tenant_record(session, Location, tenant_id, location_id)
    return item, location


def validate_reorder_point(
    session: Session,
    tenant_id: str,
    item_id: str,
    location_id: str,
    reorder_point: Decimal | float | str,
    reorder_quantity: Decimal | float | str,
) -> tuple[Item, Location, Decimal, Decimal]:
    """The checks a set makes, also run by its review so both refuse alike."""
    item, location = _subjects(session, tenant_id, item_id, location_id)
    # Only goods the company holds can run low; a service is never reordered.
    if not item.is_active or item.item_type != "stocked":
        raise InvalidOperation(code="reorder_point_item_not_stocked")
    if not location.is_active or not location.allows_stock:
        raise InvalidOperation(code="reorder_point_location_not_stock")
    try:
        point, quantity = decimal(reorder_point), decimal(reorder_quantity)
    except (ArithmeticError, ValueError, InvalidOperation) as error:
        raise InvalidOperation(code="reorder_point_values_invalid") from error
    if point < ZERO or quantity <= ZERO or not all(map(_storable, (point, quantity))):
        raise InvalidOperation(code="reorder_point_values_invalid")
    return item, location, point, quantity


def _storable(value: Decimal) -> bool:
    """Whether the column keeps the value exactly as stated: four places, 18 digits.

    A fifth decimal would be rounded on the way in, and the record would then
    disagree with the review and the event that stated it.
    """
    return value < LIMIT and value.normalize().as_tuple().exponent >= -4


def _state(
    session: Session,
    tenant_id: str,
    item: Item,
    location: Location,
    values: dict[str, Any],
    action_id: str | None,
) -> SourceRecord:
    """Keep one statement about the point as the next version of its stream.

    The statement id makes each confirmation its own version, so restating an
    earlier value is not taken for that earlier statement, while a replay of
    the same confirmation is.
    """
    source, _, _ = store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        "reorder_point",
        f"{item.id}@{location.id}",
        {
            "item_id": item.id,
            "location_id": location.id,
            **values,
            "statement_id": action_id or uid("stm"),
        },
    )
    return source


def _check_expected(point: ItemReorderPoint | None, expected: Any) -> None:
    if expected is not UNCHECKED and reorder_point_values(point) != expected:
        raise InvalidOperation(code="reorder_point_changed_since_review")


def set_reorder_point(
    session: Session,
    tenant_id: str,
    item_id: str,
    location_id: str,
    reorder_point: Decimal | float | str,
    reorder_quantity: Decimal | float | str,
    *,
    action_id: str | None = None,
    _expected: Any = UNCHECKED,
    _commit: bool = True,
) -> ItemReorderPoint:
    """
    State, or restate, the reorder point and quantity of an item at a location.

    BUSINESS PURPOSE:
    State, or restate, the reorder point and quantity of an item at a location.

    BUSINESS RULE services.reorder_points.set_reorder_point.step-13:
    Require the business permission for 'set_reorder_point' before changing company records.

    BUSINESS RULE services.reorder_points.set_reorder_point.step-15:
    Run the shared validate reorder point check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.reorder_points.set_reorder_point.step-49:
    Record the reorder_point.set audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.reorder_points.set_reorder_point.result:
    Return point, as prepared by the preceding checks and service calls.
    """
    # reality-rule: services.reorder_points.set_reorder_point.step-13
    _require_business_mutation(session, tenant_id, "set_reorder_point")
    lock_delivery_state(session, tenant_id)
    # reality-rule: services.reorder_points.set_reorder_point.step-15
    item, location, point_value, quantity = validate_reorder_point(
        session, tenant_id, item_id, location_id, reorder_point, reorder_quantity
    )
    point = current_reorder_point(session, tenant_id, item.id, location.id)
    _check_expected(point, _expected)
    previous = reorder_point_values(point)
    source = _state(
        session,
        tenant_id,
        item,
        location,
        {"reorder_point": _plain(point_value), "reorder_quantity": _plain(quantity)},
        action_id,
    )
    if point is None:
        point = ItemReorderPoint(
            id=uid("rop"),
            tenant_id=tenant_id,
            item_id=item.id,
            location_id=location.id,
            reorder_point=point_value,
            reorder_quantity=quantity,
            source_record_id=source.id,
        )
        session.add(point)
    elif point.source_record_id != source.id:
        point.reorder_point = point_value
        point.reorder_quantity = quantity
        point.source_record_id = source.id
        point.updated_at = now()
    else:
        # The same confirmation again: it already stated this.
        return point
    session.flush()
    # reality-rule: services.reorder_points.set_reorder_point.step-49
    emit_business_event(
        session,
        tenant_id,
        "reorder_point.set",
        "reorder_point",
        point.id,
        {
            "item_id": item.id,
            "location_id": location.id,
            "reorder_point": _plain(point_value),
            "reorder_quantity": _plain(quantity),
            **({"previous": previous} if previous else {}),
        },
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.reorder_points.set_reorder_point.result
    return point


def remove_reorder_point(
    session: Session,
    tenant_id: str,
    item_id: str,
    location_id: str,
    *,
    action_id: str | None = None,
    _expected: Any = UNCHECKED,
    _commit: bool = True,
) -> dict[str, Any]:
    """
    Withdraw a reorder point; the event keeps what it was.

    BUSINESS PURPOSE:
    Withdraw a reorder point; the event keeps what it was.

    BUSINESS RULE services.reorder_points.remove_reorder_point.step-11:
    Require the business permission for 'remove_reorder_point' before changing company records.

    BUSINESS RULE services.reorder_points.remove_reorder_point.refusal-15:
    IF the selected item and location have no current reorder point:
        Refuse with reorder_point_not_found.

    BUSINESS RULE services.reorder_points.remove_reorder_point.step-27:
    Record the reorder_point.removed audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.reorder_points.remove_reorder_point.result:
    Return removed, as prepared by the preceding checks and service calls.
    """
    # reality-rule: services.reorder_points.remove_reorder_point.step-11
    _require_business_mutation(session, tenant_id, "remove_reorder_point")
    lock_delivery_state(session, tenant_id)
    item, location = _subjects(session, tenant_id, item_id, location_id)
    point = current_reorder_point(session, tenant_id, item.id, location.id)
    # reality-rule: services.reorder_points.remove_reorder_point.refusal-15
    if point is None:
        raise NotFound(code="reorder_point_not_found")
    _check_expected(point, _expected)
    source = _state(session, tenant_id, item, location, {"removed": True}, action_id)
    removed = {
        "id": point.id,
        "item_id": item.id,
        "location_id": location.id,
        **reorder_point_values(point),
    }
    session.delete(point)
    session.flush()
    # reality-rule: services.reorder_points.remove_reorder_point.step-27
    emit_business_event(
        session,
        tenant_id,
        "reorder_point.removed",
        "reorder_point",
        removed["id"],
        {key: value for key, value in removed.items() if key != "id"},
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    removed["source_record_id"] = source.id
    if _commit:
        session.commit()
    # reality-rule: services.reorder_points.remove_reorder_point.result
    return removed


REORDER_POINT_TOOLS = {"reorder_point_set", "reorder_point_remove"}


def review_reorder_point(
    session: Session, tenant_id: str, tool_name: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    The arguments a confirmation executes and what the person is shown.

    The review states the point as it is now, or none, beside what it becomes,
    and carries the current values into the arguments: executing them later
    refuses if the point has changed in between.

    BUSINESS PURPOSE:
    The arguments a confirmation executes and what the person is shown.

    BUSINESS RULE services.reorder_points.review_reorder_point.refusal-9:
    IF the requested operation is not registered for this review service:
        Refuse with proposal_tool_not_found.

    BUSINESS RULE services.reorder_points.review_reorder_point.refusal-32:
    IF the selected item and location have no current reorder point:
        Refuse with reorder_point_not_found.

    BUSINESS RULE services.reorder_points.review_reorder_point.result:
    Return normalized, preview, as prepared by the preceding checks and service calls.

    BUSINESS RULE services.reorder_points.review_reorder_point.effect-30:
    IF the requested operation sets a reorder point:
        Run the shared validate reorder point check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.
    """
    # reality-rule: services.reorder_points.review_reorder_point.refusal-9
    if tool_name not in REORDER_POINT_TOOLS:
        raise InvalidOperation(code="proposal_tool_not_found")
    item_id = str(arguments.get("item_id") or "")
    location_id = str(arguments.get("location_id") or "")
    if tool_name == "reorder_point_set":
        # reality-rule: services.reorder_points.review_reorder_point.effect-30
        item, location, point, quantity = validate_reorder_point(
            session,
            tenant_id,
            item_id,
            location_id,
            arguments.get("reorder_point", ""),
            arguments.get("reorder_quantity", ""),
        )
        proposed: dict[str, str] | None = {
            "reorder_point": _plain(point),
            "reorder_quantity": _plain(quantity),
        }
    else:
        item, location = _subjects(session, tenant_id, item_id, location_id)
        proposed = None
    current = reorder_point_values(
        current_reorder_point(session, tenant_id, item.id, location.id)
    )
    # reality-rule: services.reorder_points.review_reorder_point.refusal-32
    if tool_name == "reorder_point_remove" and current is None:
        raise NotFound(code="reorder_point_not_found")
    normalized = {
        "item_id": item.id,
        "location_id": location.id,
        **(proposed or {}),
        "reviewed": current,
    }
    preview = {
        "item_id": item.id,
        "item": item.name,
        "sku": item.sku,
        "unit": item.unit,
        "location_id": location.id,
        "location": location.name,
        "current": current,
        "proposed": proposed,
    }
    # reality-rule: services.reorder_points.review_reorder_point.result
    return normalized, preview
