"""Exact current references for existing standalone financial evidence commands."""

import json
from hashlib import sha256

from sqlalchemy import or_, select

from reality.db.core import (
    CompanyCurrency,
    Document,
    DocumentLine,
    LedgerEntry,
    LedgerReversal,
    Party,
    SettlementAllocation,
    SourceRecord,
    SubledgerAccount,
)
from reality.domain.intake import canonical_json
from reality.services import core
from reality.services.finance.accounts import resolve_account
from reality.services.review_references import party_role_reference

REVIEW_KEY = "_financial_posting_review"
from reality.services.tenant_policy import FINANCIAL_POSTING_OPERATIONS as OPERATIONS

_REQUIRED = {
    tool: {"document_id" if "invoice_post" in tool else "credit_note_id"}
    | (
        {"invoice_id", "amount"}
        if tool.endswith("allocate")
        else {"amount"}
        if tool == "supplier_refund_post"
        else set()
    )
    for tool in OPERATIONS
}
_FIELDS = {
    tool: required
    | (set() if tool.endswith("allocate") else {"effective_at"})
    | ({"exchange_rate"} if tool == "supplier_invoice_post" else set())
    | (
        {"refund_number", "source_record_id"}
        if tool == "supplier_refund_post"
        else set()
    )
    for tool, required in _REQUIRED.items()
}
_ROLES = {
    "sales_invoice_post": ("accounts_receivable", "sales_revenue"),
    "supplier_invoice_post": ("inventory", "accounts_payable"),
    "credit_note_post": ("sales_revenue", "accounts_receivable"),
    "supplier_credit_note_post": ("accounts_payable", "inventory"),
    "supplier_refund_post": ("cash",),
}


def _hash(rows):
    return sha256(
        canonical_json(
            [
                {
                    column.name: getattr(row, column.name)
                    for column in row.__table__.columns
                }
                for row in rows
            ]
        ).encode()
    ).hexdigest()


def _rows(session, tenant_id, model, condition):
    return list(
        session.scalars(
            select(model)
            .where(model.tenant_id == tenant_id, condition)
            .order_by(model.id)
            .execution_options(populate_existing=True)
        )
    )


def _reference_state(session, tenant_id, tool, arguments):
    identities = {
        arguments[field]
        for field in ("document_id", "credit_note_id", "invoice_id")
        if arguments.get(field)
    }
    documents = _rows(session, tenant_id, Document, Document.id.in_(identities))
    if {row.id for row in documents} != identities:
        raise core.NotFound(code="record_not_found", values={"record": "Document"})
    lines = _rows(
        session, tenant_id, DocumentLine, DocumentLine.document_id.in_(identities)
    )
    entries = _rows(
        session, tenant_id, LedgerEntry, LedgerEntry.document_id.in_(identities)
    )
    entry_ids = {row.id for row in entries}
    groups = {row.posting_group_id for row in entries if row.posting_group_id}
    allocations = _rows(
        session,
        tenant_id,
        SettlementAllocation,
        or_(
            SettlementAllocation.payment_ledger_entry_id.in_(entry_ids),
            SettlementAllocation.invoice_ledger_entry_id.in_(entry_ids),
        ),
    )
    reversals = _rows(
        session,
        tenant_id,
        LedgerReversal,
        or_(
            LedgerReversal.original_posting_group_id.in_(groups),
            LedgerReversal.reversing_posting_group_id.in_(groups),
        ),
    )
    party_ids = {row.party_id for row in documents if row.party_id}
    parties = _rows(session, tenant_id, Party, Party.id.in_(party_ids))
    source_ids = {row.source_record_id for row in documents if row.source_record_id}
    if arguments.get("source_record_id"):
        source_ids.add(arguments["source_record_id"])
    sources = _rows(session, tenant_id, SourceRecord, SourceRecord.id.in_(source_ids))
    if {row.id for row in sources} != source_ids:
        raise core.NotFound(code="record_not_found", values={"record": "SourceRecord"})
    account_ids = {row.account_id for row in entries if row.account_id}
    account_ids.update(
        resolve_account(session, tenant_id, role).id for role in _ROLES.get(tool, ())
    )
    accounts = _rows(
        session, tenant_id, SubledgerAccount, SubledgerAccount.id.in_(account_ids)
    )
    company_currency = list(
        session.scalars(
            select(CompanyCurrency)
            .where(CompanyCurrency.tenant_id == tenant_id)
            .execution_options(populate_existing=True)
        )
    )
    return {
        "documents": _hash(documents),
        "lines": _hash(lines),
        "entries": _hash(entries),
        "allocations": _hash(allocations),
        "reversals": _hash(reversals),
        "parties": _hash(parties),
        "roles": {
            row.id: party_role_reference(session, tenant_id, row.id) for row in parties
        },
        "sources": _hash(sources),
        "accounts": _hash(accounts),
        "company_currency": _hash(company_currency),
    }


def prepare_financial_posting(session, tenant_id, tool, arguments):
    from reality.services.intake import _INTENT_DEFAULTS

    if set(arguments) - _FIELDS[tool]:
        raise core.InvalidOperation(code="intake_review_invalid")
    if not _REQUIRED[tool] <= arguments.keys():
        raise core.InvalidOperation(code="intake_review_invalid")
    defaults = {
        key: value
        for key, value in _INTENT_DEFAULTS[OPERATIONS[tool]].items()
        if key in _FIELDS[tool]
    }
    normalized = json.loads(canonical_json({**defaults, **arguments}))
    return {
        **normalized,
        REVIEW_KEY: _reference_state(session, tenant_id, tool, normalized),
    }


def require_current_financial_posting(session, tenant_id, tool, intent):
    arguments = json.loads(intent)
    if REVIEW_KEY not in arguments:
        raise core.InvalidOperation(code="intake_review_invalid")
    try:
        current = _reference_state(session, tenant_id, tool, arguments)
    except (core.InvalidOperation, core.NotFound) as error:
        raise core.InvalidOperation(code="intake_review_stale") from error
    if arguments[REVIEW_KEY] != current:
        raise core.InvalidOperation(code="intake_review_stale")
