"""Spec 301 FR-004: a receipt in the purchase unit behind MCP/Chat, Web and CLI."""

import json
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, Movement
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.services.delivery_actions import delivery_proposal_detail
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _cartons_ordered(session, business, number="PO-301-A"):
    business.item.purchase_unit = "box"
    business.item.conversion_factor = Decimal(12)
    session.commit()
    _, _, _, commitments = core.create_manual_order(
        session,
        business.tenant.id,
        "purchase",
        number,
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "5",
                "unit": "box",
                "unit_price": "60",
                "gross_amount": "300",
            }
        ],
        "300",
    )
    return commitments[0]


def _receipt(business, commitment, quantity="5", unit="box"):
    return {
        "movement_type": "receipt",
        "item_id": business.item.id,
        "quantity": quantity,
        "to_location_id": business.location.id,
        "commitment_id": commitment.id,
        "unit": unit,
    }


def _schema(name):
    return next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == name
    )


def _received(session, business):
    session.expire_all()
    return [
        (row.quantity, row.stated_quantity, row.stated_unit)
        for row in session.scalars(
            select(Movement).where(
                Movement.tenant_id == business.tenant.id, Movement.type == "receipt"
            )
        )
    ]


def test_the_mcp_schemas_carry_the_stated_unit():
    movement = _schema("movement_create_propose")
    assert movement["additionalProperties"] is False
    assert "unit" in movement["properties"]
    assert "unit" not in movement["required"]
    branches = {
        branch["properties"]["purpose"]["const"]: branch["properties"]["movements"][
            "items"
        ]
        for branch in _schema("shipment_receive_propose")["oneOf"]
    }
    receipt = branches["supplier_delivery"]
    assert receipt["additionalProperties"] is False
    assert "unit" in receipt["properties"]
    # Only a receipt is stated in the purchase unit.
    assert all(
        "unit" not in movement["properties"]
        for purpose, movement in branches.items()
        if purpose != "supplier_delivery"
    )


def test_an_agent_proposes_a_receipt_in_cartons_and_a_person_confirms(
    session, business
):
    tenant = business.tenant.id
    commitment = _cartons_ordered(session, business)

    proposed = MCP_TOOL_REGISTRY["movement_create_propose"].handler(
        session, tenant, _receipt(business, commitment)
    )
    proposal = session.get(ChangeProposal, (tenant, proposed["proposal_id"]))
    review = json.loads(proposal.input)["_delivery_review"]
    # The person reviews what was stated and what stock receives.
    assert (review["intent"]["quantity"], review["intent"]["unit"]) == ("5", "box")
    assert review["effect"]["received"] == "60"
    assert review["effect"]["stated"] == {"quantity": "5", "unit": "box"}
    assert _received(session, business) == []

    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=review["token"], confirmed=True
    )

    assert _received(session, business) == [
        (Decimal("60.0000"), Decimal("5.0000"), "box")
    ]
    assert delivery_proposal_detail(session, tenant, proposal.id)["verification"] == (
        "verified"
    )


def _client(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    return TestClient(web_module.app)


def test_the_web_prepares_and_confirms_a_receipt_in_cartons(
    session, business, monkeypatch
):
    commitment = _cartons_ordered(session, business)
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{business.tenant.id}"

    prepared = client.post(
        f"{prefix}/delivery-actions/prepare",
        json={
            "tool": "movement_create",
            "request_id": "web-cartons",
            "arguments": _receipt(business, commitment),
        },
    )
    assert prepared.status_code == 200, prepared.text
    preview = prepared.json()
    assert preview["review"]["effect"]["received"] == "60"
    confirmed = client.post(
        f"{prefix}/change-proposals/{preview['id']}/approve",
        json={"confirmed": True, "review_token": preview["review"]["token"]},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert _received(session, business) == [
        (Decimal("60.0000"), Decimal("5.0000"), "box")
    ]

    # A unit the item states no conversion for is refused with its reason.
    refused = client.post(
        f"{prefix}/delivery-actions/prepare",
        json={
            "tool": "movement_create",
            "request_id": "web-pallets",
            "arguments": _receipt(business, commitment, "1", "pallet"),
        },
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "movement_unit_not_convertible" in refused.text


def test_another_company_cannot_receive_into_the_order(session, business, monkeypatch):
    commitment = _cartons_ordered(session, business)
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)

    foreign = client.post(
        f"/api/tenants/{other.id}/delivery-actions/prepare",
        json={
            "tool": "movement_create",
            "request_id": "foreign-cartons",
            "arguments": _receipt(business, commitment),
        },
    )

    assert foreign.status_code == 404, foreign.text
    assert _received(session, business) == []


def test_the_cli_records_a_receipt_in_cartons(session, business, monkeypatch):
    commitment = _cartons_ordered(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)

    result = CliRunner().invoke(
        cli_module.app,
        [
            "movement",
            "record",
            "receipt",
            business.item.id,
            "5",
            "--tenant",
            business.tenant.id,
            "--to-location-id",
            business.location.id,
            "--commitment-id",
            commitment.id,
            "--unit",
            "box",
        ],
    )

    assert result.exit_code == 0, result.output
    assert _received(session, business) == [
        (Decimal("60.0000"), Decimal("5.0000"), "box")
    ]


def test_the_movement_inspector_shows_what_a_receipt_stated(session, business):
    from reality.web.api import movement_inspector

    commitment = _cartons_ordered(session, business)
    movement = core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "5",
        to_location_id=business.location.id,
        commitment_id=commitment.id,
        unit="box",
    )
    plain = core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "3",
        to_location_id=business.location.id,
    )

    labels = {
        row["label"]: row["value"]
        for row in movement_inspector(session, business.tenant.id, movement.id)[
            "metrics"
        ]
    }
    assert labels["Quantity"] == "60"
    assert labels["As stated"] == "5 box"
    # Control: a movement in the stock unit states nothing else.
    assert "As stated" not in {
        row["label"]
        for row in movement_inspector(session, business.tenant.id, plain.id)["metrics"]
    }
