"""Current reference witnesses for the existing commercial master commands."""

import json
from hashlib import sha256

from sqlalchemy import select

from reality.db.core import Item, Party, PartyGroup, PaymentTerm, PriceList
from reality.domain.intake import canonical_json
from reality.services import core
from reality.services.tenant_policy import COMMERCIAL_MASTER_OPERATIONS

REVIEW_KEY = "_commercial_master_review"
_REFERENCES = {
    "payment_term_id": PaymentTerm,
    "price_list_id": PriceList,
    "item_id": Item,
    "party_id": Party,
    "party_group_id": PartyGroup,
}
_TERM_FIELDS = {"code", "name", "due_days", "discount_percent", "discount_days", "requires_prepayment"}
_SOURCE_FIELDS = {"source_system", "external_id", "source_payload"}
_PRICE_LIST_FIELDS = {"code", "name", "direction", "currency", "is_default"}
_PUBLIC_FIELDS = {
    "create_payment_term": _TERM_FIELDS | _SOURCE_FIELDS,
    "update_payment_term": _TERM_FIELDS | {"payment_term_id"},
    "create_price_list": _PRICE_LIST_FIELDS | _SOURCE_FIELDS | {"valid_from", "valid_until"},
    "update_price_list": _PRICE_LIST_FIELDS | {"price_list_id"},
    "create_price_list_entry": {"price_list_id", "item_id", "min_quantity", "unit_price", "unit", "valid_from", "valid_until"},
    "assign_party_price_list": {"party_id", "price_list_id", "priority"},
    "create_party_group": {"code", "name"},
    "update_party_group": {"party_group_id", "code", "name"},
    "add_party_group_member": {"party_group_id", "party_id"},
    "assign_group_price_list": {"party_group_id", "price_list_id", "priority"},
}


def _reference_state(session, tenant_id, arguments):
    """Read the current actual referenced records; never calculate a price."""
    result = {}
    for field, model in _REFERENCES.items():
        if field not in arguments:
            continue
        row = session.scalar(
            select(model).where(model.tenant_id == tenant_id, model.id == arguments[field])
            .execution_options(populate_existing=True)
        )
        if row is None:
            raise core.NotFound(code="record_not_found", values={"record": model.__name__})
        state = {column.name: getattr(row, column.name) for column in model.__table__.columns}
        result[field] = {"id": row.id, "state_hash": sha256(canonical_json(state).encode()).hexdigest()}
    return json.loads(canonical_json(result))


def prepare_commercial_master(session, tenant_id, tool, arguments):
    """Retain a server-produced current reference witness for the stated input."""
    operation = COMMERCIAL_MASTER_OPERATIONS[tool]
    public_fields = _PUBLIC_FIELDS[operation]
    if set(arguments) - public_fields:
        raise core.InvalidOperation(code="intake_review_invalid")
    return {**arguments, REVIEW_KEY: _reference_state(session, tenant_id, arguments)}


def require_current_commercial_master(session, tenant_id, intent):
    """A retained confirmation never silently adopts changed reference meaning."""
    arguments = json.loads(intent)
    if REVIEW_KEY not in arguments:
        raise core.InvalidOperation(code="intake_review_invalid")
    if arguments[REVIEW_KEY] != _reference_state(session, tenant_id, arguments):
        raise core.InvalidOperation(code="intake_review_stale")
