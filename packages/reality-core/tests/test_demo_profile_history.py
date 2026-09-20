import json
from datetime import datetime, timedelta
from decimal import Decimal

from conftest import seed_company
from sqlalchemy import select

from reality.db.core import (
    Document,
    DocumentLine,
    LedgerEntry,
    PlaygroundRun,
    SourceRecord,
)
from reality.services import company_setup


def test_history_has_twelve_weeks_distinct_currencies_and_linked_credit(
    session, scheduled_owner, monkeypatch
):
    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "history",
        "Harbor Supply",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    assert result["status"] == "initializing"
    tenant = result["tenant_id"]
    assert seed_company(session, tenant) == "succeeded"
    manifest = session.get(PlaygroundRun, result["run_id"]).initialization_progress
    anchor = datetime.fromisoformat(manifest["anchor"])
    postings = list(
        session.scalars(
            select(LedgerEntry)
            .join(Document, Document.id == LedgerEntry.document_id)
            .where(
                LedgerEntry.tenant_id == tenant,
                LedgerEntry.account == "sales_revenue",
                ~Document.number.like("COST-%"),
            )
        )
    )
    assert {row.currency for row in postings} == {"EUR", "USD"}
    assert {
        (row.effective_at - (anchor - timedelta(days=84))).days // 7 for row in postings
    } == set(range(12))
    assert all(
        session.get(SourceRecord, row.source_record_id).received_at >= anchor
        for row in postings
    )
    invoice = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant, Document.number == "INV-volume-current"
        )
    )
    assert invoice.gross_amount == Decimal(400)
    source = session.get(SourceRecord, invoice.source_record_id)
    assert json.loads(source.payload)["gross_amount"] == "400"
    credit = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant, Document.type == "credit_note"
        )
    )
    assert credit is not None
    credit_line = session.scalar(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == credit.id
        )
    )
    assert credit_line.billed_document_line_id is not None
    assert any(
        row.debit_credit == "debit" and row.amount == Decimal(24) for row in postings
    )
    assert manifest["capabilities"]["cost_basis"] == "bounded_cases"
