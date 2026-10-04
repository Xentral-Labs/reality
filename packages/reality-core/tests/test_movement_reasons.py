"""A receipt without a purchase order explains itself by its stated reason (spec 314).

FR-003: a stated reason on a receipt without a commitment is kept, shown and
explains it. FR-004: a delivery-path receipt without a commitment is reported
like any other unexplained receipt.
"""

import json
from datetime import UTC, datetime

import pytest
from intake_review_support import reviewed_manual_order
from sqlalchemy import select

from reality.db.core import Movement
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.exceptions import operational_exceptions
from reality.services.movement_explanations import movement_explanation
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)

RECEIVED_AT = datetime(2026, 9, 10, 8, tzinfo=UTC)


def _reviewed(session, business, tool, arguments, request_id):
    proposal = prepare_delivery_action(
        session, business.tenant.id, tool, arguments, request_id=request_id
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    assert executed.status == "executed"
    return proposal


def _receipt_ids(session, business):
    return set(
        session.scalars(
            select(Movement.id).where(
                Movement.tenant_id == business.tenant.id, Movement.type == "receipt"
            )
        )
    )


def _new_receipt(session, business, before):
    (movement_id,) = _receipt_ids(session, business) - before
    return session.get(Movement, (business.tenant.id, movement_id))


def _receipt(session, business, request_id, **extra):
    before = _receipt_ids(session, business)
    _reviewed(
        session,
        business,
        "movement_create",
        {
            "movement_type": "receipt",
            "item_id": business.item.id,
            "quantity": "2",
            "to_location_id": business.location.id,
            "occurred_at": RECEIVED_AT.isoformat(),
            **extra,
        },
        request_id,
    )
    return _new_receipt(session, business, before)


def _unexplained(session, business):
    return {
        row.record_id
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == "unexplained_movement"
    }


def test_a_receipt_with_a_stated_reason_is_explained_by_it(session, business):
    # Positive control: without a reason the receipt is reported.
    bare = _receipt(session, business, "h09-bare")
    assert bare.id in _unexplained(session, business)
    assert movement_explanation(session, business.tenant.id, bare.id)["kind"] == (
        "unexplained"
    )

    sample = _receipt(
        session, business, "h09-sample", reason="Free sample from Nordlicht"
    )

    explanation = movement_explanation(session, business.tenant.id, sample.id)
    assert (explanation["kind"], explanation["reason"]) == (
        "explicit_reason",
        "Free sample from Nordlicht",
    )
    assert sample.id not in _unexplained(session, business)
    assert bare.id in _unexplained(session, business)


@pytest.mark.parametrize("reason", ["", "   "])
def test_a_blank_reason_is_no_reason(session, business, reason):
    receipt = _receipt(session, business, f"h09-blank-{len(reason)}", reason=reason)

    assert receipt.id in _unexplained(session, business)


def test_a_delivery_path_receipt_without_a_purchase_is_reported(session, business):
    tenant = business.tenant.id
    # Positive control: a delivery-path receipt against a purchase is explained.
    _, _, _, commitments = reviewed_manual_order(
        session,
        tenant,
        "purchase",
        "PO-H09",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
        "20",
    )

    def receive(tracking, commitment_id=None, **extra):
        movement = {
            "item_id": business.item.id,
            "to_location_id": business.location.id,
            "quantity": "2",
            **({"commitment_id": commitment_id} if commitment_id else {}),
            **extra,
        }
        before = _receipt_ids(session, business)
        proposal = create_change_proposal(
            session,
            tenant,
            "shipment_receive",
            {
                "purpose": "supplier_delivery",
                "counterparty_id": business.supplier.id,
                "tracking_number": tracking,
                "movements": [movement],
            },
        )
        token = json.loads(proposal.input)["_delivery_review"]["token"]
        approve_and_execute_proposal(
            session, tenant, proposal.id, review_token=token, confirmed=True
        )
        return _new_receipt(session, business, before)

    ordered = receive("TRK-PO", commitments[0].id)
    assert ordered.id not in _unexplained(session, business)

    misdelivered = receive("TRK-MIS")
    assert misdelivered.id in _unexplained(session, business)

    explained = receive("TRK-FREE", reason="Misdelivery, kept for the supplier")
    assert explained.id not in _unexplained(session, business)
    assert movement_explanation(session, tenant, explained.id)["reason"] == (
        "Misdelivery, kept for the supplier"
    )


def test_a_correction_onto_a_purchase_clears_an_unexplained_receipt(session, business):
    tenant = business.tenant.id
    receipt = _receipt(session, business, "h09-late")
    assert receipt.id in _unexplained(session, business)
    _, _, _, commitments = reviewed_manual_order(
        session,
        tenant,
        "purchase",
        "PO-H09-LATE",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
        "20",
    )

    result = core.correct_movement(
        session,
        tenant,
        receipt.id,
        reason="Receipt belongs to PO-H09-LATE",
        replacement={
            "type": "receipt",
            "item_id": business.item.id,
            "quantity": "2",
            "to_location_id": business.location.id,
            "commitment_id": commitments[0].id,
            "occurred_at": RECEIVED_AT,
        },
    )

    unexplained = _unexplained(session, business)
    assert receipt.id not in unexplained
    assert result.replacement_movement_id not in unexplained


@pytest.mark.parametrize(
    ("movement_type", "direction"),
    [("shipment", "from_location_id"), ("return", "to_location_id")],
)
def test_a_reason_does_not_explain_goods_leaving_or_returning_without_an_order(
    session, business, movement_type, direction
):
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    movement = core.record_movement(
        session,
        tenant,
        movement_type,
        business.item.id,
        "1",
        reason="Given to a trade-fair visitor",
        **{direction: business.location.id},
    )

    # Billing and crediting follow from the order, so these stay reported.
    assert movement.id in _unexplained(session, business)


def test_a_corrected_sample_receipt_keeps_its_reason(session, business):
    sample = _receipt(session, business, "h09-corrected", reason="Free sample")
    result = core.correct_movement(
        session,
        business.tenant.id,
        sample.id,
        reason="Three came, not two",
        replacement={
            "type": "receipt",
            "item_id": business.item.id,
            "quantity": "3",
            "to_location_id": business.location.id,
            "occurred_at": RECEIVED_AT,
        },
    )

    unexplained = _unexplained(session, business)
    assert sample.id not in unexplained
    assert result.replacement_movement_id not in unexplained
    # Positive control: a corrected receipt that never had a reason stays reported.
    bare = _receipt(session, business, "h09-corrected-bare")
    bare_result = core.correct_movement(
        session,
        business.tenant.id,
        bare.id,
        reason="Three came, not two",
        replacement={
            "type": "receipt",
            "item_id": business.item.id,
            "quantity": "3",
            "to_location_id": business.location.id,
            "occurred_at": RECEIVED_AT,
        },
    )
    assert bare_result.replacement_movement_id in _unexplained(session, business)
