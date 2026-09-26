"""Opening stock can carry the acquisition cost its evidence states (spec 282 US3)."""

import json

import pytest
import test_costing_services as fixtures
import test_inventory_costing_services as stock
from sqlalchemy import select
from test_unified_opening_stock import confirm, prepare

from reality.db.core import Movement, SourceRecord
from reality.services.core import InvalidOperation, correct_movement, record_movement
from reality.services.cost_review_draft import cost_review_draft
from reality.services.costing import preview_cost_change
from reality.services.delivery_actions import delivery_proposal_detail

cost_owner = fixtures.cost_owner
STATED = {
    "amount": "63.00",
    "currency": "EUR",
    "evidence_reference": "Inventurliste 2025-12-31",
}


def opening_movement(session, proposal):
    movement_id = json.loads(proposal.output)["records"][0]["id"]
    return session.scalar(select(Movement).where(Movement.id == movement_id))


def draft(session, business, **answers):
    return cost_review_draft(
        session,
        business.tenant.id,
        kind="inventory",
        scope_id=business.item.id,
        answers=answers or None,
    )


def test_opening_with_cost_links_a_statement_of_the_stated_values(session, business):
    proposal = prepare(session, business, opening_cost=STATED)
    review = json.loads(proposal.input)["_delivery_review"]
    # The person confirms the stated value, so it is part of the reviewed intent.
    assert review["intent"]["opening_cost"] == STATED
    confirm(session, business, proposal)
    movement = opening_movement(session, proposal)
    record = session.scalar(
        select(SourceRecord).where(SourceRecord.id == movement.source_record_id)
    )
    assert record.tenant_id == business.tenant.id
    assert record.source_type == "opening_cost_statement"
    payload = json.loads(record.payload)
    # Received values are recorded as stated, never recomputed per unit.
    assert {key: payload[key] for key in STATED} == STATED
    assert payload["quantity"] == "5.25"
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"


def test_opening_without_cost_is_unchanged(session, business):
    proposal = prepare(session, business)
    confirm(session, business, proposal)
    assert opening_movement(session, proposal).source_record_id is None
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "verified"
    )


@pytest.mark.parametrize(
    "stated",
    [
        {**STATED, "amount": "-1"},
        {**STATED, "amount": "abc"},
        {**STATED, "currency": "EURO"},
        {**STATED, "evidence_reference": "  "},
        {"amount": "63.00", "currency": "EUR"},
        {**STATED, "unit_cost": "12"},
    ],
)
def test_invalid_opening_cost_is_refused(session, business, stated):
    # Positive control: the valid statement is accepted by the same review.
    prepare(session, business, request="valid", opening_cost=STATED)
    with pytest.raises(InvalidOperation):
        prepare(session, business, request="invalid", opening_cost=stated)


def test_open_input_opening_cost_missing(session, business):
    proposal = prepare(session, business)
    confirm(session, business, proposal)
    movement = opening_movement(session, proposal)
    entries = [
        e
        for e in draft(session, business, method="fifo")["open_inputs"]
        if e["code"] == "opening_cost_missing"
    ]
    assert entries == [
        {
            "code": "opening_cost_missing",
            "subject": {"kind": "movement", "id": movement.id},
        }
    ]


def test_opening_with_statement_is_drafted_and_accepted(session, business, cost_owner):
    proposal = prepare(session, business, opening_cost=STATED)
    confirm(session, business, proposal)
    movement = opening_movement(session, proposal)
    result = draft(session, business, method="fifo")
    assert result["open_inputs"] == []
    assert result["arguments"]["openings"] == [
        {
            "movement_id": movement.id,
            "evidence_source_record_id": movement.source_record_id,
            "acquisition_cost": "63.00",
        }
    ]
    assert result["arguments"]["currency"] == "EUR"
    # The summary names the quantity, so nobody reads the movement count as pieces.
    assert result["summary"]["openings"][0]["quantity"] == "5.2500"
    preview_cost_change(session, business.tenant.id, result["arguments"])
    _, review = stock.commit_review(session, business, cost_owner, result["arguments"])
    assert review["acquisition_value"] == "63.0000"


def test_an_earlier_opening_is_corrected_away_and_recorded_again_with_cost(
    session, business
):
    tid = business.tenant.id
    earlier = record_movement(
        session,
        tid,
        "opening_stock",
        business.item.id,
        "5.25",
        to_location_id=business.location.id,
    )
    assert "opening_cost_missing" in [
        e["code"] for e in draft(session, business, method="fifo")["open_inputs"]
    ]
    correct_movement(
        session, tid, earlier.id, reason="Record the opening again with its cost"
    )
    proposal = prepare(session, business, opening_cost=STATED)
    confirm(session, business, proposal)
    result = draft(session, business, method="fifo")
    assert result["open_inputs"] == []
    assert [row["movement_id"] for row in result["arguments"]["openings"]] == [
        opening_movement(session, proposal).id
    ]
