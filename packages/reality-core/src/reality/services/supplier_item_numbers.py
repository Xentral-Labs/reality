"""Supplier item numbers: a supplier's own number and name for our items (spec 345).

A supplier confirms, delivers and invoices by its own article numbers. Per
supplier one number names one of our items, with the supplier's name for it; an
item may have several numbers at the same supplier, and every supplier has its
own. Lines are matched on a key that ignores case and spaces, so "lf 900-12"
and "LF900-12" are the supplier's LF900-12. The key is the one customer item
numbers use (spec 308).

Setting and removing a number are reviewed statements, each kept as a version
of one source stream per supplier and number (spec 320 pattern); the row names
the one in force. The number a line was ordered by stays on the line as stated,
whatever the mapping says later.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Item, Party, PartyRole, SupplierItemNumber, now, uid
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _require_business_mutation,
    _tenant_record,
    emit_business_event,
    store_source_record,
)
from reality.services.customer_item_numbers import match_key

SOURCE_SYSTEM = "internal_supplier_item_number"
SOURCE_TYPE = "supplier_item_number"
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
        raise InvalidOperation(code="supplier_item_number_party_not_supplier")
    return party


def _current(
    session: Session, tenant_id: str, party_id: str, key: str
) -> SupplierItemNumber | None:
    return session.scalar(
        select(SupplierItemNumber).where(
            SupplierItemNumber.tenant_id == tenant_id,
            SupplierItemNumber.party_id == party_id,
            SupplierItemNumber.match_key == key,
        )
    )


def mapping_values(row: SupplierItemNumber | None) -> dict[str, str] | None:
    """What a review shows and an execution compares, or None without a mapping."""
    if row is None:
        return None
    return {
        "item_id": row.item_id,
        "supplier_item_number": row.supplier_item_number,
        "supplier_item_name": row.supplier_item_name,
    }


def resolve_supplier_item(
    session: Session, tenant_id: str, party_id: str | None, number: str | None
) -> SupplierItemNumber | None:
    """
    The mapping a supplier's number names, or None.

    BUSINESS PURPOSE:
    The mapping a supplier's number names, or None.

    BUSINESS RULE services.supplier_item_numbers.resolve_supplier_item.result:
    Return the current mapping for this supplier and supplier item number, or no mapping if none is recorded. Do not guess an item from a similar number.
    """
    key = match_key(number or "")
    if not party_id or not key:
        return None
    # reality-rule: services.supplier_item_numbers.resolve_supplier_item.result
    return _current(session, tenant_id, party_id, key)


def validate_supplier_item_number(
    session: Session,
    tenant_id: str,
    party_id: str,
    item_id: str | None,
    number: str,
    *,
    removing: bool = False,
) -> tuple[Party, Item | None, str, str]:
    """The checks a statement makes, also run by its review so both refuse alike."""
    party = _supplier(session, tenant_id, party_id)
    stated = str(number or "").strip()
    key = match_key(stated)
    if not key:
        raise InvalidOperation(code="supplier_item_number_required")
    if removing:
        if _current(session, tenant_id, party.id, key) is None:
            raise NotFound(code="supplier_item_number_not_found")
        return party, None, stated, key
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == str(item_id or ""))
    )
    if item is None:
        raise InvalidOperation(code="supplier_item_number_item_not_found")
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


def _check(row: SupplierItemNumber | None, expected: Any) -> None:
    if expected is not UNCHECKED and mapping_values(row) != expected:
        raise InvalidOperation(code="supplier_item_number_changed_since_review")


def set_supplier_item_number(
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
) -> SupplierItemNumber:
    """
    State, or restate, which of our items a supplier's number names.

    BUSINESS PURPOSE:
    State, or restate, which of our items a supplier's number names.

    BUSINESS RULE services.supplier_item_numbers.set_supplier_item_number.step-13:
    Require the business permission for 'set_supplier_item_number' before changing company records.

    BUSINESS RULE services.supplier_item_numbers.set_supplier_item_number.step-15:
    Run the shared validate supplier item number check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.supplier_item_numbers.set_supplier_item_number.step-56:
    Record the supplier_item_number.set audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.supplier_item_numbers.set_supplier_item_number.result:
    Return row, as prepared by the preceding checks and service calls.
    """
    # reality-rule: services.supplier_item_numbers.set_supplier_item_number.step-13
    _require_business_mutation(session, tenant_id, "set_supplier_item_number")
    lock_delivery_state(session, tenant_id)
    # reality-rule: services.supplier_item_numbers.set_supplier_item_number.step-15
    party, item, stated, key = validate_supplier_item_number(
        session, tenant_id, party_id, item_id, number
    )
    row = _current(session, tenant_id, party.id, key)
    _check(row, _expected)
    previous = mapping_values(row)
    supplier_name = str(name or "").strip()
    source = _state(
        session,
        tenant_id,
        party,
        key,
        {
            "item_id": item.id,
            "supplier_item_number": stated,
            "supplier_item_name": supplier_name,
        },
        action_id,
    )
    if row is None:
        row = SupplierItemNumber(
            id=uid("sin"),
            tenant_id=tenant_id,
            party_id=party.id,
            item_id=item.id,
            supplier_item_number=stated,
            match_key=key,
            supplier_item_name=supplier_name,
            source_record_id=source.id,
        )
        session.add(row)
    elif row.source_record_id != source.id:
        row.item_id = item.id
        row.supplier_item_number = stated
        row.supplier_item_name = supplier_name
        row.source_record_id = source.id
        row.updated_at = now()
    else:
        # The same confirmation again: it already stated this.
        return row
    session.flush()
    # reality-rule: services.supplier_item_numbers.set_supplier_item_number.step-56
    emit_business_event(
        session,
        tenant_id,
        "supplier_item_number.set",
        "supplier_item_number",
        row.id,
        {
            "party_id": party.id,
            "item_id": item.id,
            "supplier_item_number": stated,
            "supplier_item_name": supplier_name,
            **({"previous": previous} if previous else {}),
        },
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.supplier_item_numbers.set_supplier_item_number.result
    return row


def remove_supplier_item_number(
    session: Session,
    tenant_id: str,
    party_id: str,
    number: str,
    *,
    action_id: str | None = None,
    _expected: Any = UNCHECKED,
    _commit: bool = True,
) -> dict[str, Any]:
    """
    Withdraw a supplier's number; lines that stated it keep it as stated.

    BUSINESS PURPOSE:
    Withdraw a supplier's number; lines that stated it keep it as stated.

    BUSINESS RULE services.supplier_item_numbers.remove_supplier_item_number.step-11:
    Require the business permission for 'remove_supplier_item_number' before changing company records.

    BUSINESS RULE services.supplier_item_numbers.remove_supplier_item_number.step-13:
    Run the shared validate supplier item number check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.supplier_item_numbers.remove_supplier_item_number.step-22:
    Record the supplier_item_number.removed audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.supplier_item_numbers.remove_supplier_item_number.result:
    Return the current result with source_record_id.
    """
    # reality-rule: services.supplier_item_numbers.remove_supplier_item_number.step-11
    _require_business_mutation(session, tenant_id, "remove_supplier_item_number")
    lock_delivery_state(session, tenant_id)
    # reality-rule: services.supplier_item_numbers.remove_supplier_item_number.step-13
    party, _, _, key = validate_supplier_item_number(
        session, tenant_id, party_id, None, number, removing=True
    )
    row = _current(session, tenant_id, party.id, key)
    _check(row, _expected)
    removed = {"id": row.id, "party_id": party.id, **mapping_values(row)}
    source = _state(session, tenant_id, party, key, {"removed": True}, action_id)
    session.delete(row)
    session.flush()
    # reality-rule: services.supplier_item_numbers.remove_supplier_item_number.step-22
    emit_business_event(
        session,
        tenant_id,
        "supplier_item_number.removed",
        "supplier_item_number",
        removed["id"],
        {key_: value for key_, value in removed.items() if key_ != "id"},
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.supplier_item_numbers.remove_supplier_item_number.result
    return {**removed, "source_record_id": source.id}


def supplier_item_numbers(
    session: Session,
    tenant_id: str,
    *,
    party_id: str | None = None,
    item_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    The company's supplier item numbers, of one supplier or one item.

    BUSINESS PURPOSE:
    The company's supplier item numbers, of one supplier or one item.

    BUSINESS RULE services.supplier_item_numbers.supplier_item_numbers.result:
    Return the selected records in the displayed response structure; preserve the source identifiers and stated values used by this comprehension.
    """
    query = (
        select(SupplierItemNumber, Item, Party)
        .join(
            Item,
            (Item.tenant_id == SupplierItemNumber.tenant_id)
            & (Item.id == SupplierItemNumber.item_id),
        )
        .join(
            Party,
            (Party.tenant_id == SupplierItemNumber.tenant_id)
            & (Party.id == SupplierItemNumber.party_id),
        )
        .where(SupplierItemNumber.tenant_id == tenant_id)
    )
    if party_id:
        query = query.where(SupplierItemNumber.party_id == party_id)
    if item_id:
        query = query.where(SupplierItemNumber.item_id == item_id)
    # reality-rule: services.supplier_item_numbers.supplier_item_numbers.result
    return [
        {
            "id": row.id,
            "party_id": party.id,
            "supplier": party.name,
            "item_id": item.id,
            "item": item.name,
            "sku": item.sku,
            "supplier_item_number": row.supplier_item_number,
            "supplier_item_name": row.supplier_item_name,
            "source_record_id": row.source_record_id,
            "updated_at": row.updated_at,
        }
        for row, item, party in session.execute(
            query.order_by(Party.name, SupplierItemNumber.match_key)
        )
    ]


STATED_KEYS = (
    "supplier_item_number",
    "supplier_article_number",
    "lieferantenartikelnummer",
)


def stated_number(line: Any) -> str | None:
    """The supplier number a line states, as its payload keeps it."""
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


def line_supplier_item(
    session: Session, tenant_id: str, line: Any, party_id: str | None
) -> dict[str, str] | None:
    """The supplier's number and name for a line, or None.

    A purchase line states it itself; a supplier invoice line reaches it
    through the purchase line it bills. The number is shown as stated, and the name is the
    supplier's current name for it, if the number is still mapped.
    """
    from reality.db.core import DocumentLine

    number = stated_number(line)
    if number is None and getattr(line, "billed_document_line_id", None):
        billed = session.get(DocumentLine, (tenant_id, line.billed_document_line_id))
        number = stated_number(billed) if billed is not None else None
    if number is None:
        return None
    mapping = resolve_supplier_item(session, tenant_id, party_id, number)
    return {
        "supplier_item_number": number,
        "supplier_item_name": mapping.supplier_item_name if mapping else "",
    }


SUPPLIER_ITEM_NUMBER_TOOLS = {"supplier_item_number_set", "supplier_item_number_remove"}


def review_supplier_item_number(
    session: Session, tenant_id: str, tool_name: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    The arguments a confirmation executes and what the person is shown.

    The review shows what the number names now, or nothing, beside what it
    will name, and carries the current mapping: a confirmation after it changed
    is refused.

    BUSINESS PURPOSE:
    The arguments a confirmation executes and what the person is shown.

    BUSINESS RULE services.supplier_item_numbers.review_supplier_item_number.refusal-9:
    IF the requested operation is not registered for this review service:
        Refuse with proposal_tool_not_found.

    BUSINESS RULE services.supplier_item_numbers.review_supplier_item_number.step-12:
    Run the shared validate supplier item number check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.supplier_item_numbers.review_supplier_item_number.result:
    Return normalized, preview, as prepared by the preceding checks and service calls.
    """
    # reality-rule: services.supplier_item_numbers.review_supplier_item_number.refusal-9
    if tool_name not in SUPPLIER_ITEM_NUMBER_TOOLS:
        raise InvalidOperation(code="proposal_tool_not_found")
    removing = tool_name == "supplier_item_number_remove"
    # reality-rule: services.supplier_item_numbers.review_supplier_item_number.step-12
    party, item, stated, key = validate_supplier_item_number(
        session,
        tenant_id,
        str(arguments.get("party_id") or ""),
        None if removing else str(arguments.get("item_id") or ""),
        str(arguments.get("supplier_item_number") or ""),
        removing=removing,
    )
    current = mapping_values(_current(session, tenant_id, party.id, key))
    name = str(arguments.get("supplier_item_name") or "").strip()
    normalized = {
        "party_id": party.id,
        "supplier_item_number": stated,
        **({} if removing else {"item_id": item.id, "supplier_item_name": name}),
        "reviewed": current,
    }
    current_item = (
        session.get(Item, (tenant_id, current["item_id"])) if current else None
    )
    preview = {
        "supplier": party.name,
        "supplier_item_number": stated,
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
            "supplier_item_name": name,
        },
    }
    # reality-rule: services.supplier_item_numbers.review_supplier_item_number.result
    return normalized, preview
