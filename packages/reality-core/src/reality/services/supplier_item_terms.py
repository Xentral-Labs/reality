"""Supplier item terms: a supplier's minimum order quantity and order multiple (spec 310).

Per supplier and item, both in the item's purchase unit. Stating and removing
them are reviewed statements, each kept as a version of one source stream per
supplier and item (spec 320 pattern); the row names the one in force.

The terms never refuse an order. A purchase below the minimum or off the
multiple is named in its review with the next quantity that meets them, and the
person decides; surplus becomes stock or is assigned, as any other.
"""

from __future__ import annotations

from decimal import ROUND_CEILING, Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Item, Party, PartyRole, SupplierItemTerms, now, uid
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _require_business_mutation,
    _tenant_record,
    decimal,
    emit_business_event,
    store_source_record,
)

SOURCE_SYSTEM = "internal_supplier_item_terms"
SOURCE_TYPE = "supplier_item_terms"
# A review that saw nothing, distinct from a call that checks nothing.
UNCHECKED: Any = object()


def _supplier(session: Session, tenant_id: str, party_id: str) -> Party:
    party = _tenant_record(session, Party, tenant_id, party_id)
    if party.type != "supplier" and (
        session.scalar(
            select(PartyRole.id).where(
                PartyRole.tenant_id == tenant_id,
                PartyRole.party_id == party.id,
                PartyRole.role == "supplier",
            )
        )
        is None
    ):
        raise InvalidOperation(code="supplier_item_terms_party_not_supplier")
    return party


def _current(
    session: Session, tenant_id: str, party_id: str, item_id: str
) -> SupplierItemTerms | None:
    return session.scalar(
        select(SupplierItemTerms).where(
            SupplierItemTerms.tenant_id == tenant_id,
            SupplierItemTerms.party_id == party_id,
            SupplierItemTerms.item_id == item_id,
        )
    )


def _text(value: Decimal | None) -> str | None:
    return None if value is None else format(decimal(value).normalize(), "f")


def terms_values(row: SupplierItemTerms | None) -> dict[str, str | None] | None:
    """What a review shows and an execution compares, or None without terms."""
    if row is None:
        return None
    return {
        "minimum_quantity": _text(row.minimum_quantity),
        "order_multiple": _text(row.order_multiple),
    }


def _quantity(value: Any) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        stated = decimal(value)
        exact = stated == stated.quantize(Decimal("0.0001"))
    except (ArithmeticError, ValueError, TypeError) as error:
        raise InvalidOperation(code="supplier_item_terms_invalid") from error
    if stated <= 0 or not exact:
        raise InvalidOperation(code="supplier_item_terms_invalid")
    return stated


def validate_supplier_item_terms(
    session: Session,
    tenant_id: str,
    party_id: str,
    item_id: str,
    minimum_quantity: Any = None,
    order_multiple: Any = None,
    *,
    removing: bool = False,
) -> tuple[Party, Item, Decimal | None, Decimal | None]:
    """The checks a statement makes, also run by its review so both refuse alike."""
    party = _supplier(session, tenant_id, party_id)
    item = _tenant_record(session, Item, tenant_id, item_id)
    if removing:
        if _current(session, tenant_id, party.id, item.id) is None:
            raise NotFound(code="supplier_item_terms_not_found")
        return party, item, None, None
    minimum, multiple = _quantity(minimum_quantity), _quantity(order_multiple)
    if minimum is None and multiple is None:
        raise InvalidOperation(code="supplier_item_terms_empty")
    return party, item, minimum, multiple


def _check(row: SupplierItemTerms | None, expected: Any) -> None:
    if expected is not UNCHECKED and terms_values(row) != expected:
        raise InvalidOperation(code="supplier_item_terms_changed_since_review")


def _state(session, tenant_id, party, item, values, action_id):
    source, _, _ = store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        SOURCE_TYPE,
        f"{party.id}:{item.id}",
        {
            "party_id": party.id,
            "item_id": item.id,
            **values,
            "statement_id": action_id or uid("stm"),
        },
    )
    return source


def set_supplier_item_terms(
    session: Session,
    tenant_id: str,
    party_id: str,
    item_id: str,
    minimum_quantity: Any = None,
    order_multiple: Any = None,
    *,
    action_id: str | None = None,
    _expected: Any = UNCHECKED,
    _commit: bool = True,
) -> SupplierItemTerms:
    """State, or restate, a supplier's minimum order quantity and order multiple."""
    _require_business_mutation(session, tenant_id, "set_supplier_item_terms")
    lock_delivery_state(session, tenant_id)
    party, item, minimum, multiple = validate_supplier_item_terms(
        session, tenant_id, party_id, item_id, minimum_quantity, order_multiple
    )
    row = _current(session, tenant_id, party.id, item.id)
    _check(row, _expected)
    previous = terms_values(row)
    values = {"minimum_quantity": _text(minimum), "order_multiple": _text(multiple)}
    source = _state(session, tenant_id, party, item, values, action_id)
    if row is None:
        row = SupplierItemTerms(
            id=uid("sit"),
            tenant_id=tenant_id,
            party_id=party.id,
            item_id=item.id,
            minimum_quantity=minimum,
            order_multiple=multiple,
            source_record_id=source.id,
        )
        session.add(row)
    elif row.source_record_id != source.id:
        row.minimum_quantity = minimum
        row.order_multiple = multiple
        row.source_record_id = source.id
        row.updated_at = now()
    else:
        # The same confirmation again: it already stated this.
        return row
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "supplier_item_terms.set",
        "supplier_item_terms",
        row.id,
        {
            "party_id": party.id,
            "item_id": item.id,
            **values,
            **({"previous": previous} if previous else {}),
        },
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return row


def remove_supplier_item_terms(
    session: Session,
    tenant_id: str,
    party_id: str,
    item_id: str,
    *,
    action_id: str | None = None,
    _expected: Any = UNCHECKED,
    _commit: bool = True,
) -> dict[str, Any]:
    """Withdraw a supplier's terms for an item."""
    _require_business_mutation(session, tenant_id, "remove_supplier_item_terms")
    lock_delivery_state(session, tenant_id)
    party, item, _, _ = validate_supplier_item_terms(
        session, tenant_id, party_id, item_id, removing=True
    )
    row = _current(session, tenant_id, party.id, item.id)
    _check(row, _expected)
    removed = {
        "id": row.id,
        "party_id": party.id,
        "item_id": item.id,
        **terms_values(row),
    }
    source = _state(session, tenant_id, party, item, {"removed": True}, action_id)
    session.delete(row)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "supplier_item_terms.removed",
        "supplier_item_terms",
        removed["id"],
        {key: value for key, value in removed.items() if key != "id"},
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return {**removed, "source_record_id": source.id}


def supplier_item_terms(
    session: Session,
    tenant_id: str,
    *,
    party_id: str | None = None,
    item_id: str | None = None,
) -> list[dict[str, Any]]:
    """The company's supplier item terms, of one supplier or one item."""
    query = (
        select(SupplierItemTerms, Item, Party)
        .join(
            Item,
            (Item.tenant_id == SupplierItemTerms.tenant_id)
            & (Item.id == SupplierItemTerms.item_id),
        )
        .join(
            Party,
            (Party.tenant_id == SupplierItemTerms.tenant_id)
            & (Party.id == SupplierItemTerms.party_id),
        )
        .where(SupplierItemTerms.tenant_id == tenant_id)
    )
    if party_id:
        query = query.where(SupplierItemTerms.party_id == party_id)
    if item_id:
        query = query.where(SupplierItemTerms.item_id == item_id)
    return [
        {
            "id": row.id,
            "party_id": party.id,
            "supplier": party.name,
            "item_id": item.id,
            "item": item.name,
            "sku": item.sku,
            "unit": item.purchase_unit or item.unit,
            **terms_values(row),
            "source_record_id": row.source_record_id,
            "updated_at": row.updated_at,
        }
        for row, item, party in session.execute(query.order_by(Party.name, Item.sku))
    ]


def order_terms_check(
    session: Session,
    tenant_id: str,
    party_id: str,
    item_id: str,
    quantity: Decimal,
) -> dict[str, Any] | None:
    """How a purchase quantity meets the supplier's terms, or None without terms.

    The quantity is in the order line's unit, which for a purchase is the item's
    purchase unit (spec 301). The suggestion is the smallest quantity at or above
    both the minimum and the asked quantity that is a whole number of multiples.
    """
    row = _current(session, tenant_id, party_id, item_id)
    if row is None:
        return None
    asked = decimal(quantity)
    minimum = (
        decimal(row.minimum_quantity) if row.minimum_quantity is not None else None
    )
    multiple = decimal(row.order_multiple) if row.order_multiple is not None else None
    target = max(asked, minimum) if minimum is not None else asked
    if multiple is not None:
        target = (target / multiple).to_integral_value(
            rounding=ROUND_CEILING
        ) * multiple
    below = minimum is not None and asked < minimum
    off = (
        multiple is not None
        and (asked / multiple) != (asked / multiple).to_integral_value()
    )
    return {
        **terms_values(row),
        "below_minimum": below,
        "off_multiple": off,
        "suggested_quantity": _text(target),
    }


SUPPLIER_ITEM_TERMS_TOOLS = {"supplier_item_terms_set", "supplier_item_terms_remove"}


def review_supplier_item_terms(
    session: Session, tenant_id: str, tool_name: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The arguments a confirmation executes and what the person is shown."""
    if tool_name not in SUPPLIER_ITEM_TERMS_TOOLS:
        raise InvalidOperation(code="proposal_tool_not_found")
    removing = tool_name == "supplier_item_terms_remove"
    party, item, minimum, multiple = validate_supplier_item_terms(
        session,
        tenant_id,
        str(arguments.get("party_id") or ""),
        str(arguments.get("item_id") or ""),
        arguments.get("minimum_quantity"),
        arguments.get("order_multiple"),
        removing=removing,
    )
    current = terms_values(_current(session, tenant_id, party.id, item.id))
    proposed = (
        None
        if removing
        else {"minimum_quantity": _text(minimum), "order_multiple": _text(multiple)}
    )
    normalized = {
        "party_id": party.id,
        "item_id": item.id,
        **({} if removing else {k: v for k, v in proposed.items() if v is not None}),
        "reviewed": current,
    }
    preview = {
        "supplier": party.name,
        "item": item.name,
        "sku": item.sku,
        "unit": item.purchase_unit or item.unit,
        "current": current,
        "proposed": proposed,
    }
    return normalized, preview
