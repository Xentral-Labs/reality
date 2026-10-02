"""Customer item numbers: a customer's own number and name for our items (spec 308).

A B2B customer orders by its own article number. Per customer one number names
one of our items, with the customer's name for it; an item may have several
numbers at the same customer. Lines are matched on a key that ignores case and
spaces, so "k-4711" and "K - 4711" are the customer's K-4711.

Setting and removing a number are reviewed statements, each kept as a version
of one source stream per customer and number (spec 320 pattern); the row names
the one in force. The number a line was ordered by stays on the line as stated,
whatever the mapping says later.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import CustomerItemNumber, Item, Party, PartyRole, now, uid
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _require_business_mutation,
    _tenant_record,
    emit_business_event,
    store_source_record,
)

SOURCE_SYSTEM = "internal_customer_item_number"
SOURCE_TYPE = "customer_item_number"
# A review that saw nothing, distinct from a call that checks nothing.
UNCHECKED: Any = object()


def match_key(number: str) -> str:
    """The number as lines are matched on it: upper case, without spaces."""
    return re.sub(r"\s+", "", str(number or "")).upper()


def _customer(session: Session, tenant_id: str, party_id: str) -> Party:
    party = _tenant_record(session, Party, tenant_id, party_id)
    if party.type != "customer" and (
        session.scalar(
            select(PartyRole.id).where(
                PartyRole.tenant_id == tenant_id,
                PartyRole.party_id == party.id,
                PartyRole.role == "customer",
            )
        )
        is None
    ):
        raise InvalidOperation(code="customer_item_number_party_not_customer")
    return party


def _current(
    session: Session, tenant_id: str, party_id: str, key: str
) -> CustomerItemNumber | None:
    return session.scalar(
        select(CustomerItemNumber).where(
            CustomerItemNumber.tenant_id == tenant_id,
            CustomerItemNumber.party_id == party_id,
            CustomerItemNumber.match_key == key,
        )
    )


def mapping_values(row: CustomerItemNumber | None) -> dict[str, str] | None:
    """What a review shows and an execution compares, or None without a mapping."""
    if row is None:
        return None
    return {
        "item_id": row.item_id,
        "customer_item_number": row.customer_item_number,
        "customer_item_name": row.customer_item_name,
    }


def resolve_customer_item(
    session: Session, tenant_id: str, party_id: str | None, number: str | None
) -> CustomerItemNumber | None:
    """The mapping a customer's number names, or None."""
    key = match_key(number or "")
    if not party_id or not key:
        return None
    return _current(session, tenant_id, party_id, key)


def validate_customer_item_number(
    session: Session,
    tenant_id: str,
    party_id: str,
    item_id: str | None,
    number: str,
    *,
    removing: bool = False,
) -> tuple[Party, Item | None, str, str]:
    """The checks a statement makes, also run by its review so both refuse alike."""
    party = _customer(session, tenant_id, party_id)
    stated = str(number or "").strip()
    key = match_key(stated)
    if not key:
        raise InvalidOperation(code="customer_item_number_required")
    if removing:
        if _current(session, tenant_id, party.id, key) is None:
            raise NotFound(code="customer_item_number_not_found")
        return party, None, stated, key
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == str(item_id or ""))
    )
    if item is None:
        raise InvalidOperation(code="customer_item_number_item_not_found")
    return party, item, stated, key


def _state(
    session: Session,
    tenant_id: str,
    party: Party,
    key: str,
    values: dict[str, Any],
    action_id: str | None,
):
    source, _, _ = store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        SOURCE_TYPE,
        f"{party.id}:{key}",
        {
            "party_id": party.id,
            **values,
            "statement_id": action_id or uid("stm"),
        },
    )
    return source


def _check(row: CustomerItemNumber | None, expected: Any) -> None:
    if expected is not UNCHECKED and mapping_values(row) != expected:
        raise InvalidOperation(code="customer_item_number_changed_since_review")


def set_customer_item_number(
    session: Session,
    tenant_id: str,
    party_id: str,
    item_id: str,
    number: str,
    name: str = "",
    *,
    action_id: str | None = None,
    _expected: Any = UNCHECKED,
    _commit: bool = True,
) -> CustomerItemNumber:
    """State, or restate, which of our items a customer's number names."""
    _require_business_mutation(session, tenant_id, "set_customer_item_number")
    lock_delivery_state(session, tenant_id)
    party, item, stated, key = validate_customer_item_number(
        session, tenant_id, party_id, item_id, number
    )
    row = _current(session, tenant_id, party.id, key)
    _check(row, _expected)
    previous = mapping_values(row)
    customer_name = str(name or "").strip()
    source = _state(
        session,
        tenant_id,
        party,
        key,
        {
            "item_id": item.id,
            "customer_item_number": stated,
            "customer_item_name": customer_name,
        },
        action_id,
    )
    if row is None:
        row = CustomerItemNumber(
            id=uid("cin"),
            tenant_id=tenant_id,
            party_id=party.id,
            item_id=item.id,
            customer_item_number=stated,
            match_key=key,
            customer_item_name=customer_name,
            source_record_id=source.id,
        )
        session.add(row)
    elif row.source_record_id != source.id:
        row.item_id = item.id
        row.customer_item_number = stated
        row.customer_item_name = customer_name
        row.source_record_id = source.id
        row.updated_at = now()
    else:
        # The same confirmation again: it already stated this.
        return row
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "customer_item_number.set",
        "customer_item_number",
        row.id,
        {
            "party_id": party.id,
            "item_id": item.id,
            "customer_item_number": stated,
            "customer_item_name": customer_name,
            **({"previous": previous} if previous else {}),
        },
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return row


def remove_customer_item_number(
    session: Session,
    tenant_id: str,
    party_id: str,
    number: str,
    *,
    action_id: str | None = None,
    _expected: Any = UNCHECKED,
    _commit: bool = True,
) -> dict[str, Any]:
    """Withdraw a customer's number; lines ordered by it keep it as stated."""
    _require_business_mutation(session, tenant_id, "remove_customer_item_number")
    lock_delivery_state(session, tenant_id)
    party, _, _, key = validate_customer_item_number(
        session, tenant_id, party_id, None, number, removing=True
    )
    row = _current(session, tenant_id, party.id, key)
    _check(row, _expected)
    removed = {"id": row.id, "party_id": party.id, **mapping_values(row)}
    source = _state(session, tenant_id, party, key, {"removed": True}, action_id)
    session.delete(row)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "customer_item_number.removed",
        "customer_item_number",
        removed["id"],
        {key_: value for key_, value in removed.items() if key_ != "id"},
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return {**removed, "source_record_id": source.id}


def customer_item_numbers(
    session: Session,
    tenant_id: str,
    *,
    party_id: str | None = None,
    item_id: str | None = None,
) -> list[dict[str, Any]]:
    """The company's customer item numbers, of one customer or one item."""
    query = (
        select(CustomerItemNumber, Item, Party)
        .join(
            Item,
            (Item.tenant_id == CustomerItemNumber.tenant_id)
            & (Item.id == CustomerItemNumber.item_id),
        )
        .join(
            Party,
            (Party.tenant_id == CustomerItemNumber.tenant_id)
            & (Party.id == CustomerItemNumber.party_id),
        )
        .where(CustomerItemNumber.tenant_id == tenant_id)
    )
    if party_id:
        query = query.where(CustomerItemNumber.party_id == party_id)
    if item_id:
        query = query.where(CustomerItemNumber.item_id == item_id)
    return [
        {
            "id": row.id,
            "party_id": party.id,
            "customer": party.name,
            "item_id": item.id,
            "item": item.name,
            "sku": item.sku,
            "customer_item_number": row.customer_item_number,
            "customer_item_name": row.customer_item_name,
            "source_record_id": row.source_record_id,
            "updated_at": row.updated_at,
        }
        for row, item, party in session.execute(
            query.order_by(Party.name, CustomerItemNumber.match_key)
        )
    ]


STATED_KEYS = ("customer_item_number", "customer_article_number", "kundenartikelnummer")


def stated_number(line: Any) -> str | None:
    """The customer number a line was ordered by, as its payload states it."""
    import json

    try:
        payload = json.loads(getattr(line, "payload", None) or "{}")
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    lowered = {str(key).strip().lower(): value for key, value in payload.items()}
    for key in STATED_KEYS:
        value = lowered.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return None


def line_customer_item(
    session: Session, tenant_id: str, line: Any, party_id: str | None
) -> dict[str, str] | None:
    """The customer's number and name for a line, or None.

    An order line states it itself; an invoice line reaches it through the
    order line it bills. The number is shown as stated, and the name is the
    customer's current name for it, if the number is still mapped.
    """
    from reality.db.core import DocumentLine

    number = stated_number(line)
    if number is None and getattr(line, "billed_document_line_id", None):
        billed = session.get(DocumentLine, (tenant_id, line.billed_document_line_id))
        number = stated_number(billed) if billed is not None else None
    if number is None:
        return None
    mapping = resolve_customer_item(session, tenant_id, party_id, number)
    return {
        "customer_item_number": number,
        "customer_item_name": mapping.customer_item_name if mapping else "",
    }


CUSTOMER_ITEM_NUMBER_TOOLS = {"customer_item_number_set", "customer_item_number_remove"}


def review_customer_item_number(
    session: Session, tenant_id: str, tool_name: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The arguments a confirmation executes and what the person is shown.

    The review shows what the number names now, or nothing, beside what it
    will name, and carries the current mapping: a confirmation after it changed
    is refused.
    """
    if tool_name not in CUSTOMER_ITEM_NUMBER_TOOLS:
        raise InvalidOperation(code="proposal_tool_not_found")
    removing = tool_name == "customer_item_number_remove"
    party, item, stated, key = validate_customer_item_number(
        session,
        tenant_id,
        str(arguments.get("party_id") or ""),
        None if removing else str(arguments.get("item_id") or ""),
        str(arguments.get("customer_item_number") or ""),
        removing=removing,
    )
    current = mapping_values(_current(session, tenant_id, party.id, key))
    name = str(arguments.get("customer_item_name") or "").strip()
    normalized = {
        "party_id": party.id,
        "customer_item_number": stated,
        **({} if removing else {"item_id": item.id, "customer_item_name": name}),
        "reviewed": current,
    }
    current_item = (
        session.get(Item, (tenant_id, current["item_id"])) if current else None
    )
    preview = {
        "customer": party.name,
        "customer_item_number": stated,
        "current": (
            {
                **current,
                "item": current_item.name if current_item else current["item_id"],
            }
            if current
            else None
        ),
        "proposed": None
        if removing
        else {
            "item_id": item.id,
            "item": item.name,
            "sku": item.sku,
            "customer_item_name": name,
        },
    }
    return normalized, preview
