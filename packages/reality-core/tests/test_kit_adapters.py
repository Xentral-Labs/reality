"""Spec 333 FR-005: kits behind MCP/Chat, Web and CLI, through the shared review."""

import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, KitComponent
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _schema(name):
    return next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == name
    )


def _parts(session, business):
    tenant = business.tenant.id
    kit = reviewed_create_item(session, tenant, "KIT-BIKE", "Bike kit")
    frame = reviewed_create_item(session, tenant, "FRAME", "Frame")
    wheel = reviewed_create_item(session, tenant, "WHEEL", "Wheel")
    for item, quantity in ((frame, "2"), (wheel, "4")):
        core.record_movement(
            session,
            tenant,
            "receipt",
            item.id,
            quantity,
            to_location_id=business.location.id,
        )
    return kit, frame, wheel


def _components(session, tenant):
    session.expire_all()
    return list(
        session.scalars(select(KitComponent).where(KitComponent.tenant_id == tenant))
    )


def _client(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    return TestClient(web_module.app)


def test_the_mcp_schemas_are_strict():
    define = _schema("kit_define_propose")
    assert define["additionalProperties"] is False
    assert set(define["required"]) == {"kit_item_id", "components"}
    component = define["properties"]["components"]["items"]
    assert component["additionalProperties"] is False
    assert set(component["properties"]) == {"item_id", "quantity", "share"}
    assemble = _schema("kit_assemble_propose")
    assert assemble["additionalProperties"] is False
    assert set(assemble["required"]) == {"kit_item_id", "location_id", "quantity"}
    assert _schema("kits")["additionalProperties"] is False
    assert _schema("kit_split")["required"] == ["document_line_id"]


def test_an_agent_defines_and_assembles_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    kit, frame, wheel = _parts(session, business)

    proposed = MCP_TOOL_REGISTRY["kit_define_propose"].handler(
        session,
        tenant,
        {
            "kit_item_id": kit.id,
            "components": [
                {"item_id": frame.id, "quantity": "1", "share": "0.6"},
                {"item_id": wheel.id, "quantity": "2", "share": "0.4"},
            ],
        },
    )
    review = proposed["preview"]["kit"]
    assert [part["sku"] for part in review["components"]] == ["FRAME", "WHEEL"]
    # Nothing is stated until a person confirms.
    assert _components(session, tenant) == []
    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )
    assert len(_components(session, tenant)) == 2

    (read,) = MCP_TOOL_REGISTRY["kits"].handler(session, tenant, {"item_id": kit.id})
    assert read["availability"][0]["buildable"] == "2"

    assembly = MCP_TOOL_REGISTRY["kit_assemble_propose"].handler(
        session,
        tenant,
        {"kit_item_id": kit.id, "location_id": business.location.id, "quantity": "2"},
    )
    assert [part["quantity"] for part in assembly["preview"]["kit"]["consumes"]] == [
        "2",
        "4",
    ]
    approve_and_execute_proposal(
        session, tenant, assembly["proposal_id"], confirmed=True
    )
    assert core.stock_at(session, tenant, kit.id, business.location.id) == 2


def test_a_review_refuses_what_the_execution_refuses(session, business):
    tenant = business.tenant.id
    kit, frame, wheel = _parts(session, business)
    try:
        MCP_TOOL_REGISTRY["kit_define_propose"].handler(
            session,
            tenant,
            {
                "kit_item_id": kit.id,
                "components": [
                    {"item_id": frame.id, "quantity": "1", "share": "0.6"},
                    {"item_id": wheel.id, "quantity": "2", "share": "0.6"},
                ],
            },
        )
    except core.InvalidOperation as error:
        assert error.code == "kit_shares_invalid"
    else:
        raise AssertionError("shares above one were proposed")
    assert (
        session.scalar(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:kit_define",
            )
        )
        is None
    )

    # An assembly reviewed while the parts were there, confirmed after they left.
    from reality.services.kits import define_kit

    define_kit(
        session,
        tenant,
        kit.id,
        [
            {"item_id": frame.id, "quantity": "1"},
            {"item_id": wheel.id, "quantity": "2"},
        ],
    )
    assembly = MCP_TOOL_REGISTRY["kit_assemble_propose"].handler(
        session,
        tenant,
        {"kit_item_id": kit.id, "location_id": business.location.id, "quantity": "2"},
    )
    core.record_movement(
        session,
        tenant,
        "adjustment",
        wheel.id,
        "1",
        from_location_id=business.location.id,
        reason="Broken",
    )
    try:
        approve_and_execute_proposal(
            session, tenant, assembly["proposal_id"], confirmed=True
        )
    except core.InvalidOperation as error:
        assert error.code == "kit_component_short"
    else:
        raise AssertionError("an assembly short of a wheel was executed")
    assert core.stock_at(session, tenant, frame.id, business.location.id) == 2


def test_the_web_reads_prepares_and_confirms(session, business, monkeypatch):
    kit, frame, wheel = _parts(session, business)
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{business.tenant.id}"

    prepared = client.post(
        f"{prefix}/kits/proposals",
        json={
            "operation": "define",
            "kit_item_id": kit.id,
            "components": [
                {"item_id": frame.id, "quantity": "1"},
                {"item_id": wheel.id, "quantity": "2"},
            ],
        },
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["preview"]["kit"]["operation"] == "define"
    assert client.get(f"{prefix}/kits").json()["rows"] == []
    confirmed = client.post(
        f"{prefix}/change-proposals/{body['id']}/approve", json={"confirmed": True}
    )
    assert confirmed.status_code == 200, confirmed.text
    (row,) = client.get(f"{prefix}/kits", params={"item_id": frame.id}).json()["rows"]
    assert row["availability"][0]["available"] == "2"

    refused = client.post(
        f"{prefix}/kits/proposals",
        json={
            "operation": "assemble",
            "kit_item_id": kit.id,
            "location_id": business.location.id,
            "quantity": "3",
        },
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "kit_component_short" in refused.text
    assembled = client.post(
        f"{prefix}/kits/proposals",
        json={
            "operation": "assemble",
            "kit_item_id": kit.id,
            "location_id": business.location.id,
            "quantity": "1",
        },
    )
    assert assembled.status_code == 200, assembled.text
    assert assembled.json()["preview"]["kit"]["consumes"][1]["quantity"] == "2"


def test_another_company_cannot_read_or_change_the_kits(session, business, monkeypatch):
    kit, frame, _wheel = _parts(session, business)
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)

    assert client.get(f"/api/tenants/{other.id}/kits").json()["rows"] == []
    foreign = client.post(
        f"/api/tenants/{other.id}/kits/proposals",
        json={
            "operation": "define",
            "kit_item_id": kit.id,
            "components": [{"item_id": frame.id, "quantity": "1"}],
        },
    )
    assert foreign.status_code == 404, foreign.text
    assert _components(session, business.tenant.id) == []


def test_the_cli_defines_assembles_shows_and_declines(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    kit, frame, wheel = _parts(session, business)
    runner = CliRunner()

    defined = runner.invoke(
        cli_module.app,
        [
            "kit",
            "define",
            kit.id,
            "--component",
            f"{frame.id}:1:0.6",
            "--component",
            f"{wheel.id}:2:0.4",
            "--tenant",
            tenant,
            "--yes",
        ],
    )
    assert defined.exit_code == 0, defined.output
    assert len(_components(session, tenant)) == 2

    declined = runner.invoke(
        cli_module.app,
        ["kit", "assemble", kit.id, business.location.id, "1", "--tenant", tenant],
        input="n\n",
    )
    assert declined.exit_code == 0, declined.output
    session.expire_all()
    assert core.stock_at(session, tenant, kit.id, business.location.id) == 0
    assembled = runner.invoke(
        cli_module.app,
        [
            "kit",
            "assemble",
            kit.id,
            business.location.id,
            "1",
            "--tenant",
            tenant,
            "--yes",
        ],
    )
    assert assembled.exit_code == 0, assembled.output
    session.expire_all()
    assert core.stock_at(session, tenant, kit.id, business.location.id) == 1

    shown = runner.invoke(cli_module.app, ["kit", "show", "--tenant", tenant])
    assert shown.exit_code == 0, shown.output
    assert json.loads(shown.output)[0]["availability"][0]["kits_on_hand"] == "1"


from intake_review_support import reviewed_create_item
