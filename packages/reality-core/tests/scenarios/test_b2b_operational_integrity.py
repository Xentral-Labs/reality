"""Independent B2B proof for the operational-integrity boundary (spec 250)."""

from decimal import Decimal

from sqlalchemy import select

from reality.db.core import (
    ChangeProposal,
    Commitment,
    Document,
    Movement,
    Reservation,
    uid,
)
from reality.services.core import (
    active_reserved,
    create_commitment,
    create_item,
    create_location,
    create_lot,
    record_movement,
    reserve,
    stock_at,
)
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
)
from reality.services.delivery_reads import delivery_case
from reality.services.return_dispositions import (
    record_return_disposition,
    return_disposition_summary,
)
from reality.tools.application import approve_and_execute_proposal


def confirm(session, tenant_id, tool, arguments, request_id):
    proposal = prepare_delivery_action(
        session, tenant_id, tool, arguments, request_id=request_id
    )
    review = delivery_proposal_detail(session, tenant_id, proposal.id)["review"]
    return approve_and_execute_proposal(
        session,
        tenant_id,
        proposal.id,
        review_token=review["token"],
        confirmed=True,
    )


def test_b2b_inventory_revision_return_and_cancellation_reconcile_exactly(
    session, business
):
    tenant_id = business.tenant.id
    item = create_item(
        session, tenant_id, "B2B-LOT", "B2B lot item", tracking_type="lot"
    )
    lot = create_lot(session, tenant_id, item.id, "B2B-LOT-2026")
    returns = create_location(session, tenant_id, "Returns inspection")
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        item.id,
        100,
        to_location_id=business.location.id,
        lot_id=lot.id,
    )

    revised = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        item.id,
        business.location.id,
        10,
        "2026-12-01",
    )
    original_reservation = reserve(
        session, tenant_id, revised.id, 10, lot_id=lot.id
    ).reservation
    confirm(
        session,
        tenant_id,
        "commitment_revise",
        {"commitment_id": revised.id, "quantity": "6", "note": "Customer reduced"},
        "story-revise",
    )
    session.refresh(original_reservation)
    assert original_reservation.status == "released"
    assert active_reserved(session, tenant_id, item.id, business.location.id) == 6

    shipped = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        item.id,
        business.location.id,
        5,
        "2026-12-02",
    )
    record_movement(
        session,
        tenant_id,
        "shipment",
        item.id,
        5,
        from_location_id=business.location.id,
        commitment_id=shipped.id,
        lot_id=lot.id,
    )
    arrived = record_movement(
        session,
        tenant_id,
        "return",
        item.id,
        2,
        to_location_id=returns.id,
        commitment_id=shipped.id,
        lot_id=lot.id,
    )
    scrapped = record_return_disposition(
        session,
        tenant_id,
        arrived.id,
        "scrap_loss",
        2,
        reason="Transport damage",
    )
    assert scrapped.resolves_movement_id == arrived.id
    assert scrapped.lot_id == lot.id
    assert scrapped.from_location_id == returns.id
    assert stock_at(session, tenant_id, item.id, returns.id) == 0
    assert stock_at(session, tenant_id, item.id, business.location.id) == 95
    disposition = return_disposition_summary(session, tenant_id, arrived.id)
    assert disposition["resolved"] == 2
    assert disposition["unresolved"] == 0

    supplier = create_commitment(
        session,
        tenant_id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        item.id,
        business.location.id,
        4,
        "2026-12-03",
    )
    confirm(
        session,
        tenant_id,
        "commitment_cancel",
        {"commitment_id": supplier.id, "reason": "Supplier discontinued item"},
        "story-cancel",
    )
    session.refresh(supplier)
    assert supplier.status == "cancelled"


def test_historical_over_reservation_is_visible_but_never_silently_repaired(
    session, business
):
    tenant_id = business.tenant.id
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        20,
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        3,
        "2026-12-04",
    )
    planted = Reservation(
        id=uid("res"),
        tenant_id=tenant_id,
        commitment_id=commitment.id,
        item_id=business.item.id,
        location_id=business.location.id,
        quantity=Decimal(5),
        status="active",
    )
    session.add(planted)
    session.commit()

    observed = delivery_case(session, tenant_id, commitment.id)

    assert Decimal(observed["case"]["reserved"]) == 5
    assert Decimal(observed["case"]["open"]) == 3
    assert session.scalar(
        select(Reservation).where(
            Reservation.tenant_id == tenant_id, Reservation.id == planted.id
        )
    ).status == "active"


def test_integrity_actions_reuse_existing_authorities_without_schema_shortcuts():
    document_columns = set(Document.__table__.columns.keys())
    reservation_columns = set(Reservation.__table__.columns.keys())
    commitment_columns = set(Commitment.__table__.columns.keys())
    movement_columns = set(Movement.__table__.columns.keys())
    proposal_columns = set(ChangeProposal.__table__.columns.keys())

    assert not {
        "delivery_status",
        "reservation_status",
        "purchase_fulfillment_status",
    } & document_columns
    assert not {"document_id", "document_line_id", "source_record_id"} & reservation_columns
    assert {"status", "cancelled_at"} <= commitment_columns
    assert {"resolves_movement_id", "lot_id", "serial_unit_id", "handling_unit_id"} <= movement_columns
    assert {"status", "input", "output"} <= proposal_columns
