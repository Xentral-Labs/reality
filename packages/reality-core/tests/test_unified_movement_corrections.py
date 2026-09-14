"""Unified corrections preserve history and prove exact projected effects."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, Movement, MovementCorrection
from reality.services.core import (
    InvalidOperation,
    NotFound,
    correct_movement,
    create_tenant,
    preview_movement_correction,
    record_movement,
    stock_at,
    update_item,
)
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def receipt(session, business, quantity="10"):
    return record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )


def replacement(business, quantity="7"):
    return {
        "type": "receipt",
        "item_id": business.item.id,
        "quantity": quantity,
        "to_location_id": business.location.id,
    }


def prepare(session, business, original, *, request="correction", replace=True):
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "movement_correct",
        {
            "movement_id": original.id,
            "reason": "Count corrected",
            **({"replacement": replacement(business)} if replace else {}),
        },
        request_id=request,
    )


def confirm(session, tid, proposal):
    return approve_and_execute_proposal(
        session,
        tid,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )


def test_selected_replacement_preview_and_invalid_replacement_are_read_only(
    session, business
):
    tid = business.tenant.id
    original = receipt(session, business)
    result = correct_movement(
        session, tid, original.id, reason="Count", replacement=replacement(business)
    )
    preview = preview_movement_correction(
        session,
        tid,
        result.replacement_movement_id,
        reason="Recheck",
        replacement=replacement(business, "6"),
    )
    assert preview["original"]["id"] == result.replacement_movement_id
    before = session.scalar(
        select(func.count()).select_from(Movement).where(Movement.tenant_id == tid)
    )
    for invalid in [{"quantity": "-1"}, {"item_id": "foreign"}, {"unexpected": True}]:
        with pytest.raises((InvalidOperation, NotFound)):
            preview_movement_correction(
                session,
                tid,
                result.replacement_movement_id,
                reason="Invalid",
                replacement={**replacement(business), **invalid},
            )
    assert (
        session.scalar(
            select(func.count()).select_from(Movement).where(Movement.tenant_id == tid)
        )
        == before
    )
    assert stock_at(session, tid, business.item.id, business.location.id) == 7


def test_review_confirmation_replay_and_history(session, business):
    tid = business.tenant.id
    original = receipt(session, business)
    proposal = prepare(session, business, original)
    assert stock_at(session, tid, business.item.id, business.location.id) == 10
    with pytest.raises(InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(session, tid, proposal.id)
    confirm(session, tid, proposal)
    confirm(session, tid, proposal)
    assert stock_at(session, tid, business.item.id, business.location.id) == 7
    result = delivery_proposal_detail(session, tid, proposal.id)
    assert result["verification"] == "verified"
    assert (
        result["observation"]["pools"][0]["after"]
        == result["observation"]["pools"][0]["physical"]
    )
    assert result["receipt"]["original_movement_id"] == original.id
    assert original.quantity == 10
    assert (
        session.scalar(
            select(func.count())
            .select_from(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tid, BusinessEvent.action_id == proposal.id
            )
        )
        == 1
    )
    correct_movement(
        session,
        tid,
        result["receipt"]["replacement_movement_id"],
        reason="Later count",
        replacement=replacement(business, "6"),
    )
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "verified"
    )


def test_stale_and_foreign_correction_review(session, business):
    tid = business.tenant.id
    original = receipt(session, business)
    proposal = prepare(session, business, original)
    receipt(session, business, "1")
    with pytest.raises(InvalidOperation, match="review"):
        confirm(session, tid, proposal)
    assert proposal.status == "proposed"
    other = create_tenant(session, "Other correction tenant")
    with pytest.raises(NotFound):
        prepare_delivery_action(
            session,
            other.id,
            "movement_correct",
            {"movement_id": original.id, "reason": "Foreign"},
            request_id="foreign",
        )
    assert (
        session.scalar(
            select(func.count())
            .select_from(MovementCorrection)
            .where(MovementCorrection.tenant_id == tid)
        )
        == 0
    )


def test_recovery_requires_attributable_correction_and_never_reexecutes(
    session, business
):
    tid = business.tenant.id
    original = receipt(session, business)
    proposal = prepare(session, business, original, replace=False)
    args = json.loads(proposal.input)
    proposal.status = "executing"
    session.commit()
    assert reconcile_delivery(session, tid, proposal.id)["verification"] == "unresolved"
    correct_movement(
        session, tid, original.id, reason=args["reason"], action_id=proposal.id
    )
    result = reconcile_delivery(session, tid, proposal.id)
    assert result["status"] == "executed" and result["verification"] == "verified"
    assert stock_at(session, tid, business.item.id, business.location.id) == Decimal(0)
    assert reconcile_delivery(session, tid, proposal.id)["receipt"] == result["receipt"]
    assert (
        session.scalar(
            select(func.count())
            .select_from(MovementCorrection)
            .where(MovementCorrection.tenant_id == tid)
        )
        == 1
    )


def test_canonical_chat_proposal_has_common_review(session, business):
    original = receipt(session, business)
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "movement_correct",
        {"movement_id": original.id, "reason": "Duplicate"},
    )
    assert "_delivery_review" in json.loads(proposal.input)
    confirm(session, business.tenant.id, proposal)
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "verified"
    )


def test_serial_replacement_validates_after_inverse_without_writes(session, business):
    from reality.services.core import create_item, create_serial_unit

    tid = business.tenant.id
    item = create_item(
        session, tid, "SERIAL-CORRECT", "Serialized", tracking_type="serial"
    )
    serial = create_serial_unit(session, tid, item.id, "ONE")
    original = record_movement(
        session,
        tid,
        "receipt",
        item.id,
        "1",
        to_location_id=business.location.id,
        serial_unit_id=serial.id,
    )
    values = {
        "type": "receipt",
        "item_id": item.id,
        "quantity": "1",
        "to_location_id": business.location.id,
        "serial_unit_id": serial.id,
    }
    review = preview_movement_correction(
        session, tid, original.id, reason="Reference corrected", replacement=values
    )
    assert review["replacement"]["serial_unit_id"] == serial.id
    assert stock_at(session, tid, item.id, business.location.id) == 1
    assert (
        session.scalar(
            select(func.count())
            .select_from(MovementCorrection)
            .where(MovementCorrection.tenant_id == tid)
        )
        == 0
    )
    result = correct_movement(
        session,
        tid,
        original.id,
        reason=review["reason"],
        replacement=review["replacement"],
        expected_revision=review["revision"],
        preview_fingerprint=review["request_fingerprint"],
    )
    assert (
        result.replacement_movement_id
        and stock_at(session, tid, item.id, business.location.id) == 1
    )


def test_tracked_inverse_cannot_use_another_lots_stock(session, business):
    from reality.services.core import create_item, create_lot

    tid = business.tenant.id
    item = create_item(session, tid, "LOT-CORRECT", "Tracked", tracking_type="lot")
    lot = create_lot(session, tid, item.id, "A")
    other = create_lot(session, tid, item.id, "B")
    original = record_movement(
        session,
        tid,
        "receipt",
        item.id,
        "2",
        to_location_id=business.location.id,
        lot_id=lot.id,
    )
    record_movement(
        session,
        tid,
        "shipment",
        item.id,
        "2",
        from_location_id=business.location.id,
        lot_id=lot.id,
    )
    record_movement(
        session,
        tid,
        "receipt",
        item.id,
        "5",
        to_location_id=business.location.id,
        lot_id=other.id,
    )
    with pytest.raises(InvalidOperation, match="tracked"):
        preview_movement_correction(session, tid, original.id, reason="Mistake")
    assert stock_at(session, tid, item.id, business.location.id) == 5


def test_shipment_correction_restores_stock_and_open_not_reservations(
    session, business
):
    from unified_fixtures import delivery_fixture

    from reality.services.core import active_reserved, open_quantity, reserve

    tid = business.tenant.id
    cid = delivery_fixture(session, business).commitment.id
    reserve(session, tid, cid, "12")
    original = record_movement(
        session,
        tid,
        "shipment",
        business.item.id,
        "12",
        from_location_id=business.location.id,
        commitment_id=cid,
    )
    args = {
        "movement_id": original.id,
        "reason": "Only nine left",
        "replacement": {
            "type": "shipment",
            "item_id": business.item.id,
            "quantity": "9",
            "from_location_id": business.location.id,
            "commitment_id": cid,
        },
    }
    proposal = prepare_delivery_action(
        session, tid, "movement_correct", args, request_id="shipment"
    )
    assert active_reserved(session, tid, business.item.id, business.location.id) == 0
    confirm(session, tid, proposal)
    assert stock_at(session, tid, business.item.id, business.location.id) == 11
    assert open_quantity(session, tid, cid) == 3
    assert active_reserved(session, tid, business.item.id, business.location.id) == 0
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "verified"
    )


@pytest.mark.parametrize("first", ["movement_correct", "reserve"])
def test_unresolved_overlap_blocks_both_directions(session, business, first):
    from unified_fixtures import delivery_fixture

    tid = business.tenant.id
    cid = delivery_fixture(session, business).commitment.id
    original = receipt(session, business)
    args = {"movement_id": original.id, "reason": "Check"}
    reserve_args = {"commitment_id": cid, "quantity": "1"}
    proposal = prepare_delivery_action(
        session,
        tid,
        first,
        args if first == "movement_correct" else reserve_args,
        request_id="pending",
    )
    proposal.status = "executing"
    session.commit()
    with pytest.raises(InvalidOperation, match="unresolved"):
        prepare_delivery_action(
            session,
            tid,
            "reserve" if first == "movement_correct" else "movement_correct",
            reserve_args if first == "movement_correct" else args,
            request_id="conflict",
        )


def test_correction_http_actor_practice_and_receipt_mismatch(session, business):
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Tenant
    from reality.services.core import uid
    from reality.web.api import database_session
    from reality.web.app import app

    tid = business.tenant.id
    original = receipt(session, business)
    proposal = prepare(session, business, original)
    with pytest.raises(NotFound):
        approve_and_execute_proposal(
            session,
            tid,
            proposal.id,
            confirmed=True,
            review_token=json.loads(proposal.input)["_delivery_review"]["token"],
            confirming_principal=SimpleNamespace(
                user_id="absent", is_platform_admin=False
            ),
        )
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{tid}"
            response = client.post(
                f"{base}/delivery-actions/prepare",
                json={
                    "tool": "movement_correct",
                    "request_id": "http",
                    "arguments": {"movement_id": original.id, "reason": "HTTP check"},
                },
            )
            assert response.status_code == 200, response.text
            value = response.json()
            result = client.post(
                f"{base}/change-proposals/{value['id']}/approve",
                json={"confirmed": True, "review_token": value["review"]["token"]},
            )
            assert result.status_code == 200, result.text
            assert (
                client.get(f"{base}/delivery-actions/{value['id']}").json()[
                    "verification"
                ]
                == "verified"
            )
    finally:
        app.dependency_overrides.clear()
    practice = Tenant(id=uid("ten"), name="Practice", purpose="playground")
    session.add(practice)
    session.commit()
    with pytest.raises(InvalidOperation, match="practice"):
        prepare_delivery_action(
            session,
            practice.id,
            "movement_correct",
            {"movement_id": original.id, "reason": "Forbidden"},
            request_id="practice",
        )


def test_invalid_replacement_is_atomic_and_receipt_mismatch_unverified(
    session, business
):
    tid = business.tenant.id
    original = receipt(session, business)
    with pytest.raises(InvalidOperation):
        correct_movement(
            session,
            tid,
            original.id,
            reason="Invalid",
            replacement=replacement(business, "-1"),
        )
    assert stock_at(session, tid, business.item.id, business.location.id) == 10
    proposal = prepare(session, business, original)
    confirm(session, tid, proposal)
    result = json.loads(proposal.output)
    result["replacement_movement_id"] = "wrong"
    proposal.output = json.dumps(result)
    session.commit()
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "unresolved"
    )


def test_review_refreshes_cached_master_references(session, business):
    original = receipt(session, business)
    proposal = prepare(session, business, original)
    item = business.item
    tid, item_id, sku, name, unit = (
        business.tenant.id,
        item.id,
        item.sku,
        item.name,
        item.unit,
    )
    with Session(
        bind=session.connection(), join_transaction_mode="create_savepoint"
    ) as other:
        update_item(other, tid, item_id, sku, name + " renamed", unit)
    assert item.name == name  # The confirmation session still holds the old instance.
    with pytest.raises(InvalidOperation, match="review"):
        confirm(session, tid, proposal)
    assert stock_at(session, tid, item_id, business.location.id) == 10
