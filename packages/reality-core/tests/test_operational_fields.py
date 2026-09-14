from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import Document, DocumentLine, PartyRole
from reality.services.core import (
    InvalidOperation,
    cancel_commitment,
    create_commitment,
    create_document,
    create_item,
    create_location,
    create_party,
    create_payment_term,
    record_movement,
    update_location,
)


def test_document_and_commitment_operational_fields(session, business):
    term = create_payment_term(
        session, business.tenant.id, "NET_30", "Net 30 days", 30
    )
    document = create_document(
        session,
        business.tenant.id,
        "sales_order",
        "SO-FIELDS",
        business.customer.id,
        100,
        ordered_at="2026-09-01T08:00:00Z",
        requested_delivery_at="2026-09-05T12:00:00+02:00",
        customer_reference="PO-42",
        sales_channel="edi",
        payment_term_code="net_30",
        ship_to_party_id=business.customer.id,
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        2,
        "2026-09-05T12:00:00+02:00",
        document_id=document.id,
        priority="urgent",
    )

    assert document.ordered_at.isoformat() == "2026-09-01T08:00:00+00:00"
    assert document.requested_delivery_at.isoformat() == "2026-09-05T10:00:00+00:00"
    assert document.customer_reference == "PO-42"
    assert document.payment_term_id == term.id
    assert commitment.due_at.isoformat() == "2026-09-05T10:00:00+00:00"
    assert commitment.priority == "urgent"

    cancel_commitment(session, business.tenant.id, commitment.id)
    assert commitment.cancelled_at is not None


def test_document_line_correction_adds_no_operational_or_revision_state():
    forbidden = {
        "delivery_status",
        "fulfillment_status",
        "inventory_status",
        "payment_status",
        "correction_status",
        "correction_version",
    }
    assert forbidden.isdisjoint(Document.__table__.columns.keys())
    assert forbidden.isdisjoint(DocumentLine.__table__.columns.keys())


def test_master_data_fields_roles_and_constraints(session, business):
    term = create_payment_term(
        session, business.tenant.id, "NET_30", "Net 30 days", 30
    )
    party = create_party(
        session,
        business.tenant.id,
        "Dual Role GmbH",
        "customer",
        roles=["customer", "supplier"],
        accounting_code="10042",
        payment_term_code="net_30",
        default_currency="usd",
        credit_limit="25000.50",
        tax_identifier="DE123",
    )
    roles = set(
        session.scalars(select(PartyRole.role).where(PartyRole.party_id == party.id))
    )
    item = create_item(
        session,
        business.tenant.id,
        "BOX-1",
        "Boxed Item",
        item_type="stocked",
        tracking_type="lot",
        default_location_id=business.location.id,
        purchase_unit="box",
        conversion_factor="20",
        lead_time_days=7,
    )
    virtual = create_location(
        session,
        business.tenant.id,
        "Virtual",
        "virtual",
        allows_stock=False,
    )

    assert roles == {"customer", "supplier"}
    assert party.default_currency == "USD"
    assert party.credit_limit == Decimal("25000.5000")
    assert party.payment_term_id == term.id
    assert item.conversion_factor == Decimal("20.000000")
    with pytest.raises(InvalidOperation, match="does not allow"):
        record_movement(
            session,
            business.tenant.id,
            "opening_stock",
            item.id,
            1,
            to_location_id=virtual.id,
        )


def test_location_hierarchy_rejects_cycles(session, business):
    child = create_location(
        session,
        business.tenant.id,
        "Shelf",
        parent_location_id=business.location.id,
    )
    with pytest.raises(InvalidOperation, match="cycle"):
        update_location(
            session,
            business.tenant.id,
            business.location.id,
            business.location.name,
            business.location.type,
            parent_location_id=child.id,
        )
