"""Retained pre-379 sales evidence for reader compatibility tests.

New order admission must refuse unsupported units. Readers must still explain
historical records. Build that retained shape with the existing explicit source,
evidence and commitment writers; never bypass the new admission validator.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from reality.db.core import Commitment, Document, DocumentLine, SourceRecord
from reality.services import core


def legacy_sales_order(
    session: Session,
    tenant_id: str,
    direction: str,
    number: str,
    company_party_id: str,
    counterparty_id: str,
    location_id: str,
    lines: list[dict[str, Any]],
    gross_amount: str,
    **document_fields: Any,
) -> tuple[SourceRecord, Document, list[DocumentLine], list[Commitment]]:
    """Reproduce the unchanged pre-379 shape solely in historical reader fixtures."""
    assert direction == "sales"
    currency = document_fields.get("currency", "EUR")
    source = core.create_master_source_record(
        session,
        tenant_id,
        "sales_order",
        "manual",
        number,
        {
            "direction": direction,
            "number": number,
            "company_party_id": company_party_id,
            "counterparty_id": counterparty_id,
            "location_id": location_id,
            "lines": lines,
            "gross_amount": gross_amount,
            "currency": currency,
            **{
                key: str(value) if isinstance(value, (date, datetime)) else value
                for key, value in document_fields.items()
            },
        },
        _commit=False,
    )
    assert source is not None
    document, recorded_lines = core.create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_order",
        number,
        counterparty_id,
        lines,
        gross_amount,
        source_record_id=source.id,
        _commit=False,
        **document_fields,
    )
    commitments = [
        core.create_commitment(
            session,
            tenant_id,
            "customer_delivery",
            company_party_id,
            counterparty_id,
            line.item_id,
            location_id,
            line.quantity,
            line.requested_at or document_fields.get("requested_delivery_at"),
            amount=line.gross_amount,
            currency=currency,
            document_id=document.id,
            document_line_id=line.id,
            _commit=False,
        )
        for line in recorded_lines
    ]
    session.commit()
    return source, document, recorded_lines, commitments
