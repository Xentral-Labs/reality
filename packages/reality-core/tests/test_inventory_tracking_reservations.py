import json
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from reality.services.core import (
    InvalidOperation,
    NotFound,
    correct_lot_expiry,
    create_commitment,
    create_handling_unit,
    create_item,
    create_lot,
    create_serial_unit,
    create_tenant,
    expired_lots,
    record_movement,
    reserve,
    state_lot_expiry,
)
from reality.tools.application import confirm_tool, propose_tool
from reality.web import api as api_module
from reality.web import app as web_module


def customer_commitment(session, business, item_id, quantity):
    return create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        item_id,
        business.location.id,
        quantity,
        "2026-09-10",
    )


def test_lot_quantity_can_be_received_reserved_and_shipped_on_a_pallet(
    session, business
):
    item = create_item(
        session, business.tenant.id, "LOT-ITEM", "Lot item", tracking_type="lot"
    )
    lot = create_lot(session, business.tenant.id, item.id, "LOT-2026-01")
    pallet = create_handling_unit(session, business.tenant.id, "003400599999999999")
    record_movement(
        session,
        business.tenant.id,
        "receipt",
        item.id,
        10,
        to_location_id=business.location.id,
        lot_id=lot.id,
        handling_unit_id=pallet.id,
    )
    commitment = customer_commitment(session, business, item.id, 6)

    result = reserve(
        session,
        business.tenant.id,
        commitment.id,
        6,
        lot_id=lot.id,
        handling_unit_id=pallet.id,
    )
    assert result.shortage == Decimal(0)
    assert result.reservation.lot_id == lot.id
    assert result.reservation.handling_unit_id == pallet.id

    movement = record_movement(
        session,
        business.tenant.id,
        "shipment",
        item.id,
        6,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        lot_id=lot.id,
        handling_unit_id=pallet.id,
    )
    assert movement.lot_id == lot.id
    assert result.reservation.status == "consumed"


def test_lot_tracked_item_requires_lot_for_movement_and_reservation(session, business):
    item = create_item(
        session, business.tenant.id, "LOT-REQ", "Lot required", tracking_type="lot"
    )
    commitment = customer_commitment(session, business, item.id, 1)

    with pytest.raises(InvalidOperation, match="require a lot"):
        record_movement(
            session,
            business.tenant.id,
            "receipt",
            item.id,
            1,
            to_location_id=business.location.id,
        )
    with pytest.raises(InvalidOperation, match="require a lot"):
        reserve(session, business.tenant.id, commitment.id, 1)


def test_serial_reservation_identifies_exact_unit_and_quantity_one(session, business):
    item = create_item(
        session,
        business.tenant.id,
        "SERIAL-ITEM",
        "Serialized item",
        tracking_type="serial",
    )
    lot = create_lot(session, business.tenant.id, item.id, "SERIAL-BATCH")
    serial = create_serial_unit(
        session,
        business.tenant.id,
        item.id,
        "SN-0001",
        lot_id=lot.id,
    )
    record_movement(
        session,
        business.tenant.id,
        "receipt",
        item.id,
        1,
        to_location_id=business.location.id,
        serial_unit_id=serial.id,
    )
    commitment = customer_commitment(session, business, item.id, 1)

    result = reserve(
        session,
        business.tenant.id,
        commitment.id,
        serial_unit_id=serial.id,
    )
    assert result.reserved == Decimal(1)
    assert result.reservation.serial_unit_id == serial.id
    assert result.reservation.lot_id == lot.id

    with pytest.raises(InvalidOperation, match="quantity 1"):
        record_movement(
            session,
            business.tenant.id,
            "shipment",
            item.id,
            2,
            from_location_id=business.location.id,
            serial_unit_id=serial.id,
        )


def test_untracked_item_rejects_lot_identity(session, business):
    tracked = create_item(
        session, business.tenant.id, "LOT-SOURCE", "Lot source", tracking_type="lot"
    )
    lot = create_lot(session, business.tenant.id, tracked.id, "LOT-X")
    with pytest.raises(InvalidOperation, match="does not belong"):
        record_movement(
            session,
            business.tenant.id,
            "receipt",
            business.item.id,
            1,
            to_location_id=business.location.id,
            lot_id=lot.id,
        )


def test_api_uses_same_lot_reservation_flow(session, business, monkeypatch):
    item = create_item(
        session, business.tenant.id, "API-LOT", "API lot", tracking_type="lot"
    )
    commitment = customer_commitment(session, business, item.id, 2)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)
    prefix = f"/api/tenants/{business.tenant.id}"

    lot_response = client.post(
        f"{prefix}/lots", json={"item_id": item.id, "lot_number": "API-BATCH"}
    )
    assert lot_response.status_code == 201
    lot_id = lot_response.json()["id"]
    movement_response = client.post(
        f"{prefix}/movements",
        json={
            "type": "receipt",
            "item_id": item.id,
            "quantity": "2",
            "to_location_id": business.location.id,
            "lot_id": lot_id,
        },
    )
    assert movement_response.status_code == 201
    reservation_response = client.post(
        f"{prefix}/reservations",
        json={
            "commitment_id": commitment.id,
            "quantity": "2",
            "lot_id": lot_id,
        },
    )
    assert reservation_response.status_code == 201
    assert reservation_response.json()["lot_id"] == lot_id
    assert reservation_response.json()["shortage"] in {"0", "0.0000"}


def test_confirmed_chat_tool_reserves_exact_serial_unit(session, business):
    item = create_item(
        session,
        business.tenant.id,
        "CHAT-SERIAL",
        "Chat serialized item",
        tracking_type="serial",
    )
    serial = create_serial_unit(
        session, business.tenant.id, item.id, "CHAT-SN-0001"
    )
    record_movement(
        session,
        business.tenant.id,
        "receipt",
        item.id,
        1,
        to_location_id=business.location.id,
        serial_unit_id=serial.id,
    )
    commitment = customer_commitment(session, business, item.id, 1)
    proposal = propose_tool(
        session,
        business.tenant.id,
        "reserve",
        {
            "commitment_id": commitment.id,
            "serial_unit_id": serial.id,
        },
    )

    executed = confirm_tool(session, business.tenant.id, proposal.id, review_token=json.loads(proposal.input)["_delivery_review"]["token"], confirmed=True)

    assert executed.status == "executed"
    assert executed.output is not None
    assert serial.id in executed.output


# ---------------------------------------------------------------------------
# Spec 109: the best-before date somebody read off the goods.


def lot_tracked_item(session, business, sku="LOT-EXPIRY"):
    return create_item(
        session, business.tenant.id, sku, "Perishable", tracking_type="lot"
    )


def test_a_lot_carries_the_stated_best_before(session, business):
    item = lot_tracked_item(session, business)

    dated = create_lot(
        session,
        business.tenant.id,
        item.id,
        "LOT-2026-11",
        expires_at="2026-11-30",
    )
    assert dated.expires_at == date(2026, 11, 30)

    # A string and a date object state the same thing, and neither is adjusted.
    same = create_lot(
        session,
        business.tenant.id,
        item.id,
        "LOT-2026-12",
        expires_at=date(2026, 12, 31),
    )
    assert same.expires_at == date(2026, 12, 31)

    # A lot with no date asserts nothing in either direction: an item with no
    # shelf life and a label nobody read are indistinguishable here.
    undated = create_lot(session, business.tenant.id, item.id, "LOT-NO-DATE")
    assert undated.expires_at is None
    assert undated.id not in {
        row.id for row in expired_lots(session, business.tenant.id)
    }


def test_a_best_before_can_be_stated_afterwards(session, business):
    item = lot_tracked_item(session, business)
    lot = create_lot(session, business.tenant.id, item.id, "LOT-LATE-LABEL")
    assert lot.expires_at is None

    # Goods arrive before somebody reads the label, so the date is statable
    # later rather than forcing the lot to be recreated.
    stated = state_lot_expiry(
        session, business.tenant.id, lot.id, "2026-10-15"
    )
    assert stated is lot
    assert lot.expires_at == date(2026, 10, 15)


def test_a_different_best_before_is_refused(session, business):
    item = lot_tracked_item(session, business)
    lot = create_lot(
        session, business.tenant.id, item.id, "LOT-STATED", expires_at="2026-10-15"
    )

    # A received value is not adjusted. Two dates for one lot means one of them
    # is wrong in a way this product cannot adjudicate.
    with pytest.raises(InvalidOperation, match="received value"):
        state_lot_expiry(session, business.tenant.id, lot.id, "2026-10-16")
    assert lot.expires_at == date(2026, 10, 15)

    # Re-stating the same date is accepted and changes nothing, so a retry is
    # safe.
    assert (
        state_lot_expiry(
            session, business.tenant.id, lot.id, "2026-10-15"
        ).expires_at
        == date(2026, 10, 15)
    )

    # A date nobody could read is not a date.
    with pytest.raises(InvalidOperation, match="readable calendar day"):
        create_lot(
            session,
            business.tenant.id,
            item.id,
            "LOT-GARBLED",
            expires_at="best before summer",
        )
    fresh = create_lot(session, business.tenant.id, item.id, "LOT-FRESH")
    with pytest.raises(InvalidOperation, match="readable calendar day"):
        state_lot_expiry(session, business.tenant.id, fresh.id, "31.12.2026")

    # The positive control: the same lot takes an ISO day.
    assert state_lot_expiry(
        session, business.tenant.id, fresh.id, "2026-12-31"
    ).expires_at == date(2026, 12, 31)


def test_lot_expiry_is_tenant_scoped(session, business):
    item = lot_tracked_item(session, business)
    lot = create_lot(
        session, business.tenant.id, item.id, "LOT-OWN", expires_at="2020-01-01"
    )
    other = create_tenant(session, "Foreign GmbH")

    assert expired_lots(session, other.id) == []
    with pytest.raises(NotFound):
        state_lot_expiry(session, other.id, lot.id, "2020-01-01")
    with pytest.raises(NotFound):
        expired_lots(session, "ten_missing")

    # The positive control: its own tenant sees it.
    assert [row.id for row in expired_lots(session, business.tenant.id)] == [lot.id]


def test_expiry_blocks_nothing(session, business):
    """Reality reports expired stock; it does not pretend it cannot ship."""
    item = lot_tracked_item(session, business)
    lot = create_lot(
        session, business.tenant.id, item.id, "LOT-GONE-OFF", expires_at="2020-01-01"
    )
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        item.id,
        5,
        to_location_id=business.location.id,
        lot_id=lot.id,
    )
    commitment = customer_commitment(session, business, item.id, 2)

    # Reserving expired stock is not refused: refusing would stop a company
    # recording what it is about to do, and Reality has never chosen a lot.
    assert reserve(session, business.tenant.id, commitment.id, lot_id=lot.id).reserved == Decimal(2)

    # Nor is shipping it. The customer has the goods either way; what the
    # product owes is a record and a report.
    shipped = record_movement(
        session,
        business.tenant.id,
        "shipment",
        item.id,
        2,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        lot_id=lot.id,
    )
    assert shipped.lot_id == lot.id


# ---------------------------------------------------------------------------
# Spec 110: saying the stated best-before was read wrong.


def test_a_misread_best_before_can_be_corrected(session, business):
    item = lot_tracked_item(session, business, sku="LOT-CORRECT")
    lot = create_lot(
        session, business.tenant.id, item.id, "LOT-MISREAD", expires_at="2026-10-15"
    )

    corrected = correct_lot_expiry(
        session,
        business.tenant.id,
        lot.id,
        "2026-10-16",
        expected_expires_at="2026-10-15",
        reason="Read the fifteenth off the label; the goods say the sixteenth",
    )

    # Exactly as stated. Nothing derived, and the product judged neither reading.
    assert corrected is lot
    assert lot.expires_at == date(2026, 10, 16)


def test_a_correction_records_what_it_replaced(session, business):
    import json

    from reality.services.core import business_events

    item = lot_tracked_item(session, business, sku="LOT-AUDIT")
    lot = create_lot(
        session, business.tenant.id, item.id, "LOT-AUDITED", expires_at="2026-10-15"
    )
    correct_lot_expiry(
        session,
        business.tenant.id,
        lot.id,
        "2026-10-16",
        expected_expires_at="2026-10-15",
        reason="Misread label",
        actor_context={"actor": "warehouse"},
    )

    (event,) = [
        entry
        for entry in business_events(session, business.tenant.id)
        if entry.event_type == "lot.expiry_corrected"
    ]
    payload = json.loads(event.payload)

    # The audit is the event, as a manual document's line correction already
    # does it. No new record type was needed for one scalar's history.
    assert payload["before"] == "2026-10-15"
    assert payload["after"] == "2026-10-16"
    assert payload["reason"] == "Misread label"
    assert payload["lot_number"] == "LOT-AUDITED"
    assert payload["actor_context"] == {"actor": "warehouse"}


def test_a_correction_refuses(session, business):
    item = lot_tracked_item(session, business, sku="LOT-REFUSE")
    lot = create_lot(
        session, business.tenant.id, item.id, "LOT-GUARDED", expires_at="2026-10-15"
    )
    tenant_id = business.tenant.id

    with pytest.raises(InvalidOperation, match="requires a reason"):
        correct_lot_expiry(
            session, tenant_id, lot.id, "2026-10-16",
            expected_expires_at="2026-10-15", reason="   ",
        )

    # A correction confirms what it replaces, so it cannot be made by somebody
    # who has not looked.
    with pytest.raises(InvalidOperation, match="no longer matches what is stated"):
        correct_lot_expiry(
            session, tenant_id, lot.id, "2026-10-16",
            expected_expires_at="2026-10-14", reason="Guessing",
        )
    with pytest.raises(InvalidOperation, match="no longer matches what is stated"):
        correct_lot_expiry(
            session, tenant_id, lot.id, "2026-10-16",
            expected_expires_at=None, reason="Pretending none is stated",
        )

    # A correction that corrects nothing is a claim about nothing.
    with pytest.raises(InvalidOperation, match="changes nothing"):
        correct_lot_expiry(
            session, tenant_id, lot.id, "2026-10-15",
            expected_expires_at="2026-10-15", reason="No change",
        )

    # Unreadable in either position, through the one stated-date rule.
    with pytest.raises(InvalidOperation, match="readable calendar day"):
        correct_lot_expiry(
            session, tenant_id, lot.id, "next Tuesday",
            expected_expires_at="2026-10-15", reason="Garbled",
        )
    with pytest.raises(InvalidOperation, match="readable calendar day"):
        correct_lot_expiry(
            session, tenant_id, lot.id, "2026-10-16",
            expected_expires_at="15.10.2026", reason="Garbled confirmation",
        )

    # Nothing above changed anything.
    assert lot.expires_at == date(2026, 10, 15)

    # The positive control: correctly stated, it goes through.
    assert correct_lot_expiry(
        session, tenant_id, lot.id, "2026-10-16",
        expected_expires_at="2026-10-15", reason="Misread label",
    ).expires_at == date(2026, 10, 16)


def test_a_best_before_can_be_corrected_to_nothing(session, business):
    item = lot_tracked_item(session, business, sku="LOT-WRONG-LABEL")
    lot = create_lot(
        session, business.tenant.id, item.id, "LOT-NO-SHELF", expires_at="2026-10-15"
    )

    # A date read off the wrong label, on an item with no shelf life, can only
    # honestly be fixed by saying the lot has no date.
    correct_lot_expiry(
        session,
        business.tenant.id,
        lot.id,
        None,
        expected_expires_at="2026-10-15",
        reason="The date came off a neighbouring pallet; this item does not expire",
    )
    assert lot.expires_at is None
    assert lot.id not in {row.id for row in expired_lots(session, business.tenant.id)}

    # And a date can be corrected back in, as long as the absence is named.
    with pytest.raises(InvalidOperation, match="no longer matches what is stated"):
        correct_lot_expiry(
            session,
            business.tenant.id,
            lot.id,
            "2026-11-01",
            expected_expires_at="2026-10-15",
            reason="Wrong again",
        )
    correct_lot_expiry(
        session,
        business.tenant.id,
        lot.id,
        "2026-11-01",
        expected_expires_at=None,
        reason="Found the right label",
    )
    assert lot.expires_at == date(2026, 11, 1)


def test_stating_a_different_date_names_the_correction(session, business):
    """A refusal without a way forward is how a stuck typo stays stuck."""
    item = lot_tracked_item(session, business, sku="LOT-POINTER")
    lot = create_lot(
        session, business.tenant.id, item.id, "LOT-SIGNPOST", expires_at="2026-10-15"
    )

    with pytest.raises(InvalidOperation) as refused:
        state_lot_expiry(session, business.tenant.id, lot.id, "2026-10-16")

    assert "Correct it instead" in str(refused.value)
    assert "why it was wrong" in str(refused.value)


def test_correcting_expiry_is_tenant_scoped(session, business):
    item = lot_tracked_item(session, business, sku="LOT-SCOPED")
    lot = create_lot(
        session, business.tenant.id, item.id, "LOT-MINE", expires_at="2026-10-15"
    )
    other = create_tenant(session, "Foreign GmbH")

    with pytest.raises(NotFound):
        correct_lot_expiry(
            session, other.id, lot.id, "2026-10-16",
            expected_expires_at="2026-10-15", reason="Not mine",
        )
    assert lot.expires_at == date(2026, 10, 15)

    # The positive control: its own tenant corrects it.
    assert correct_lot_expiry(
        session, business.tenant.id, lot.id, "2026-10-16",
        expected_expires_at="2026-10-15", reason="Mine",
    ).expires_at == date(2026, 10, 16)
