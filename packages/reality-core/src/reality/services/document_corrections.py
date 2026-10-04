"""Retained current reference witnesses for existing manual corrections."""

import json
from hashlib import sha256

from sqlalchemy import select

from reality.db.core import (
    Document,
    DocumentLine,
    Item,
    Party,
    PaymentTerm,
    PriceList,
    PriceListEntry,
)
from reality.domain.intake import canonical_json
from reality.services import core

REVIEW_KEY = "_document_correction_review"
_HEADER_FIELDS = {"document_id", "document_type", "number", "party_id", "amount", "currency", "document_date", "ordered_at", "requested_delivery_at", "customer_reference", "sales_channel", "payment_term_code", "ship_to_party_id"}
_LINE_FIELDS = {"document_id", "expected_revision", "lines", "actor_context"}


def _row_witness(row):
    state = {column.name: getattr(row, column.name) for column in row.__table__.columns}
    return {"id": row.id, "state_hash": sha256(canonical_json(state).encode()).hexdigest()}


def _reference_state(session, tenant_id, arguments):
    def current(model, identity):
        row = session.scalar(select(model).where(model.tenant_id == tenant_id, model.id == identity).execution_options(populate_existing=True))
        if row is None:
            raise core.NotFound(code="record_not_found", values={"record": model.__name__})
        return row

    document = current(Document, arguments["document_id"])
    result = {"document": _row_witness(document), "lines": [
        _row_witness(row) for row in session.scalars(select(DocumentLine).where(DocumentLine.tenant_id == tenant_id, DocumentLine.document_id == document.id).order_by(DocumentLine.id).execution_options(populate_existing=True))
    ], "references": {}}
    for field in ("party_id", "ship_to_party_id"):
        if arguments.get(field):
            result["references"][field] = _row_witness(current(Party, arguments[field]))
    if arguments.get("payment_term_code", "").strip():
        term = core.payment_term_by_code(session, tenant_id, arguments["payment_term_code"])
        result["references"]["payment_term"] = _row_witness(current(PaymentTerm, term.id))
    for line in arguments.get("lines", []):
        for field, model in (("item_id", Item), ("billed_document_line_id", DocumentLine), ("price_list_entry_id", PriceListEntry)):
            if not line.get(field):
                continue
            row = current(model, line[field])
            result["references"][f"{field}:{row.id}"] = _row_witness(row)
            if model is PriceListEntry:
                result["references"][f"price_list:{row.price_list_id}"] = _row_witness(current(PriceList, row.price_list_id))
    return result


def prepare_document_correction(session, tenant_id, tool, arguments):
    public = _HEADER_FIELDS if tool == "document_correct" else _LINE_FIELDS
    if set(arguments) - public:
        raise core.InvalidOperation(code="intake_review_invalid")
    from reality.services.intake import _INTENT_DEFAULTS

    operation = "correct_manual_document" if tool == "document_correct" else "correct_manual_document_lines"
    defaults = {key: value for key, value in _INTENT_DEFAULTS[operation].items() if key in public}
    normalized = json.loads(canonical_json({**defaults, **arguments}))
    return {**normalized, REVIEW_KEY: _reference_state(session, tenant_id, normalized)}


def require_current_document_correction(session, tenant_id, intent):
    arguments = json.loads(intent)
    if REVIEW_KEY not in arguments:
        raise core.InvalidOperation(code="intake_review_invalid")
    if arguments[REVIEW_KEY] != _reference_state(session, tenant_id, arguments):
        raise core.InvalidOperation(code="intake_review_stale")
