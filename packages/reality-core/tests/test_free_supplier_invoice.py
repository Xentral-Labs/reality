import json

import pytest
from sqlalchemy import select

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    LedgerEntry,
    Movement,
    SourceRecord,
)
from reality.services.core import NotFound
from reality.services.proposal_reviews import proposal_next_step
from reality.tools.application import confirm_tool, propose_tool


def _arguments(business):
    return {
        "supplier_id": business.supplier.id,
        "number": "FREE-SINV-257",
        "currency": "EUR",
        "gross_amount": "34.50",
        "document_date": "2026-09-23",
        "lines": [
            {
                "item_id": business.item.id,
                "description": "Source-stated goods position",
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "10.00",
                "gross_amount": "10.00",
                "line_type": "item",
            },
            {
                "item_id": business.item.id,
                "description": "Source-stated handling charge",
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "24.50",
                "gross_amount": "24.50",
                "line_type": "charge",
            }
        ],
    }


def test_free_supplier_invoice_is_source_backed_atomic_and_has_no_stock_effect(
    session, business
):
    proposal = propose_tool(
        session, business.tenant.id, "supplier_invoice_free_record", _arguments(business)
    )
    assert proposal_next_step(proposal)["required_principal"] == "authorized_human"
    executed = confirm_tool(session, business.tenant.id, proposal.id, confirmed=True)
    receipt = json.loads(executed.output)
    replay = confirm_tool(session, business.tenant.id, proposal.id, confirmed=True)
    assert replay.output == executed.output
    records = receipt["records"]
    source_id = next(row["id"] for row in records if row["family"] == "source_record")
    document_id = next(row["id"] for row in records if row["family"] == "document")
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == business.tenant.id, SourceRecord.id == source_id
        )
    )
    document = session.scalar(
        select(Document).where(
            Document.tenant_id == business.tenant.id, Document.id == document_id
        )
    )

    assert document.type == "supplier_invoice"
    assert document.source_record_id == source.id
    assert json.loads(source.payload)["gross_amount"] == "34.50"
    retained_lines = list(
        session.scalars(
            select(DocumentLine).where(
                DocumentLine.tenant_id == business.tenant.id,
                DocumentLine.document_id == document.id,
            )
        )
    )
    assert {(line.line_type, line.description) for line in retained_lines} == {
        ("item", "Source-stated goods position"),
        ("charge", "Source-stated handling charge"),
    }
    assert len(
        list(
            session.scalars(
                select(LedgerEntry).where(
                    LedgerEntry.tenant_id == business.tenant.id,
                    LedgerEntry.document_id == document.id,
                )
            )
        )
    ) == 2
    assert session.query(Commitment).count() == 0
    assert session.query(Movement).count() == 0


def test_free_supplier_invoice_is_tenant_scoped_before_effect(session, business):
    values = _arguments(business)
    values["supplier_id"] = "pty_foreign"
    before = session.query(Document).count()
    with pytest.raises(NotFound):
        propose_tool(session, business.tenant.id, "supplier_invoice_free_record", values)
    assert session.query(Document).count() == before


def test_free_supplier_invoice_rolls_back_all_evidence_on_posting_refusal(
    session, business, monkeypatch
):
    from reality.services import core

    before = {
        "sources": session.query(SourceRecord).count(),
        "documents": session.query(Document).count(),
        "lines": session.query(DocumentLine).count(),
        "entries": session.query(LedgerEntry).count(),
    }

    def refuse(*args, **kwargs):
        raise core.InvalidOperation("Injected posting refusal")

    monkeypatch.setattr(core, "post_supplier_invoice", refuse)
    proposal = propose_tool(
        session, business.tenant.id, "supplier_invoice_free_record", _arguments(business)
    )
    with pytest.raises(core.InvalidOperation, match="Injected posting refusal"):
        confirm_tool(session, business.tenant.id, proposal.id, confirmed=True)

    assert session.query(SourceRecord).count() == before["sources"]
    assert session.query(Document).count() == before["documents"]
    assert session.query(DocumentLine).count() == before["lines"]
    assert session.query(LedgerEntry).count() == before["entries"]
