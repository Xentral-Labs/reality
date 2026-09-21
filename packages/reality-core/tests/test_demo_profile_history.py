import json
from datetime import datetime
from decimal import Decimal

from conftest import record_by_id, seed_company
from reality.db.core import (
    Document,
    DocumentLine,
    LedgerEntry,
    PlaygroundRun,
    SourceRecord,
)
from reality.demo.international import HISTORY
from reality.services import company_setup
from sqlalchemy import select


def test_history_has_authored_comparison_dates_currencies_and_linked_credit(
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
    manifest = record_by_id(
        session, PlaygroundRun, result["run_id"]
    ).initialization_progress
    anchor = datetime.fromisoformat(manifest["anchor"])
    postings = list(
        session.scalars(
            select(LedgerEntry)
            .join(Document, Document.id == LedgerEntry.document_id)
            .join(SourceRecord, SourceRecord.id == Document.source_record_id)
            .where(
                LedgerEntry.tenant_id == tenant,
                LedgerEntry.account == "sales_revenue",
                SourceRecord.tenant_id == tenant,
                SourceRecord.external_id.in_({f"INV-{row[0]}" for row in HISTORY}),
            )
        )
    )
    assert {row.currency for row in postings} == {"EUR", "USD"}
    assert {
        (anchor - row.effective_at).days for row in postings if row.debit_credit == "credit"
    } == {row[2] for row in HISTORY}
    assert all(
        record_by_id(session, SourceRecord, row.source_record_id).received_at >= anchor
        for row in postings
    )
    invoice = session.scalar(
        select(Document)
        .join(SourceRecord, SourceRecord.id == Document.source_record_id)
        .where(
            Document.tenant_id == tenant,
            SourceRecord.tenant_id == tenant,
            SourceRecord.external_id == "INV-volume-current",
        )
    )
    assert invoice.gross_amount == Decimal(400)
    source = record_by_id(session, SourceRecord, invoice.source_record_id)
    assert json.loads(source.payload)["gross_amount"] == "400"
    # The profile seeds two credit notes. COST-LATE-CREDIT is deliberately unlinked,
    # because pretending it bills an order line would make that sale's fulfillment
    # scope ambiguous. Name the one this test is about instead of taking whichever
    # row the database returns first.
    credit = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant,
            Document.type == "credit_note",
            Document.number == "CR-001",
        )
    )
    assert credit is not None
    credit_line = session.scalar(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == credit.id
        )
    )
    assert credit_line.billed_document_line_id is None
    assert json.loads(
        record_by_id(session, SourceRecord, credit.source_record_id).payload
    )["invoice_external_reference"] == "INV-credit-origin"
    credit_posting = session.scalar(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.document_id == credit.id,
            LedgerEntry.account == "sales_revenue",
            LedgerEntry.debit_credit == "debit",
        )
    )
    assert credit_posting.amount == Decimal(120)
    assert manifest["capabilities"]["cost_basis"] == "bounded_cases"
