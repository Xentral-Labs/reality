from conftest import record_by_id
from sqlalchemy import select

from reality.db.core import Commitment, Document, DocumentLine, SourceRecord
from reality.mcp.catalog import dispatch_tool


def test_sales_order_proposal_is_inert_then_creates_complete_trace(session, business):
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "order_create_propose",
        {
            "direction": "sales",
            "number": "SO-AGENT-1",
            "company_party_id": business.company.id,
            "counterparty_id": business.customer.id,
            "location_id": business.location.id,
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "2",
                    "unit": "pcs",
                    "unit_price": "12.50",
                    "gross_amount": "25.00",
                }
            ],
            "gross_amount": "25.00",
        },
        allowed_access=("propose",),
    )
    assert (
        session.scalar(select(Document).where(Document.number == "SO-AGENT-1")) is None
    )

    result = dispatch_tool(
        session,
        business.tenant.id,
        "proposal_approve_and_execute",
        {
            "proposal_id": proposal["proposal_id"],
            "approved": True,
            "review_token": proposal["preview"]["token"],
        },
        allowed_access=("confirm",),
    )["output"]

    source = record_by_id(session, SourceRecord, result["source_record_id"])
    document = record_by_id(session, Document, result["document_id"])
    line = record_by_id(session, DocumentLine, result["document_line_ids"][0])
    commitment = record_by_id(session, Commitment, result["commitment_ids"][0])
    assert document.source_record_id == source.id
    assert line.document_id == document.id
    assert commitment.document_id == document.id
    assert commitment.document_line_id == line.id
    assert commitment.type == "customer_delivery"


def test_purchase_order_derives_incoming_commitment(session, business):
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "order_create_propose",
        {
            "direction": "purchase",
            "number": "PO-AGENT-1",
            "company_party_id": business.company.id,
            "counterparty_id": business.supplier.id,
            "location_id": business.location.id,
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "5",
                    "unit": "pcs",
                    "unit_price": "4",
                    "gross_amount": "20",
                }
            ],
            "gross_amount": "20",
        },
        allowed_access=("propose",),
    )
    output = dispatch_tool(
        session,
        business.tenant.id,
        "proposal_approve_and_execute",
        {
            "proposal_id": proposal["proposal_id"],
            "approved": True,
            "review_token": proposal["preview"]["token"],
        },
        allowed_access=("confirm",),
    )["output"]
    commitment = record_by_id(session, Commitment, output["commitment_ids"][0])
    assert commitment.type == "supplier_delivery"
    assert commitment.from_party_id == business.supplier.id
    assert commitment.to_party_id == business.company.id
