"""Spec 298 FR-006: one credit release and one exposure read behind Web, MCP/Chat and CLI."""

import json
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.services.credit_exposure import active_credit_holds
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _held_order(session, business, number="SO-CA-1"):
    tenant = business.tenant.id
    party = reviewed_create_party(
        session, tenant, f"Adapter Kunde {number}", "customer", credit_limit="100"
    )
    _, order, _, commitments = core.create_manual_order(
        session,
        tenant,
        "sales",
        number,
        business.company.id,
        party.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "4",
                "unit_price": "100.00",
                "gross_amount": "400.00",
            }
        ],
        "400.00",
    )
    assert active_credit_holds(session, tenant, [commitments[0].id])
    return party, order, commitments


def _held(session, business, commitments):
    session.expire_all()
    return active_credit_holds(session, business.tenant.id, [c.id for c in commitments])


def test_the_mcp_release_schema_is_strict():
    """
    BUSINESS TEST:
    The mcp release schema is strict.
    GIVEN:
    Public MCP credit-hold release schema is registered.
    WHEN:
    Inspect its fields and required arguments.
    THEN:
    Only document_id and reason are allowed and both are required.
    """
    schema = next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == "credit_hold_release_propose"
    )
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"document_id", "reason"}
    assert set(schema["required"]) == {"document_id", "reason"}


def test_an_agent_proposes_the_release_and_reads_the_exposure(session, business):
    """
    BUSINESS TEST:
    An agent proposes the release and reads the exposure.
    GIVEN:
    Order 400 exceeds limit 100.
    WHEN:
    Read MCP exposure, propose release and approve with review token.
    THEN:
    Exposure excess is 300; proposal alone retains hold, confirmation clears it.
    """
    tenant = business.tenant.id
    party, order, commitments = _held_order(session, business)

    exposure = MCP_TOOL_REGISTRY["credit_exposure"].handler(
        session, tenant, {"party_id": party.id}
    )
    assert (exposure["over_limit"], Decimal(exposure["excess"])) == (True, 300)

    proposed = MCP_TOOL_REGISTRY["credit_hold_release_propose"].handler(
        session, tenant, {"document_id": order.id, "reason": "Prepayment received"}
    )
    # Proposing releases nothing.
    assert _held(session, business, commitments)
    proposal = session.get(ChangeProposal, (tenant, proposed["proposal_id"]))
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True
    )

    assert _held(session, business, commitments) == []


def test_the_web_prepares_the_release_and_reads_the_exposure(
    session, business, monkeypatch
):
    """
    BUSINESS TEST:
    The web prepares the release and reads the exposure.
    GIVEN:
    A credit-held order is exposed through the tenant HTTP API.
    WHEN:
    Read exposure, prepare release and confirm with review token.
    THEN:
    Read shows order amount 400, review requires owner and confirmed release clears hold.
    """
    party, order, commitments = _held_order(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)
    prefix = f"/api/tenants/{business.tenant.id}"

    exposure = client.get(f"{prefix}/parties/{party.id}/credit-exposure")
    assert exposure.status_code == 200, exposure.text
    assert Decimal(exposure.json()["open_orders"]["amount"]) == 400

    prepared = client.post(
        f"{prefix}/delivery-actions/prepare",
        json={
            "tool": "credit_hold_release",
            "request_id": "web-credit-release",
            "arguments": {"document_id": order.id, "reason": "Prepayment received"},
        },
    )
    assert prepared.status_code == 200, prepared.text
    preview = prepared.json()
    assert preview["review"]["effect"]["owner_required"] is True
    confirmed = client.post(
        f"{prefix}/change-proposals/{preview['id']}/approve",
        json={"confirmed": True, "review_token": preview["review"]["token"]},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert _held(session, business, commitments) == []


def test_the_web_refuses_another_companys_order_and_party(
    session, business, monkeypatch
):
    """
    BUSINESS TEST:
    The web refuses another companys order and party.
    GIVEN:
    A credit-held order and customer belong to one tenant.
    WHEN:
    Request release and exposure through another tenant's HTTP routes.
    THEN:
    Both return 404 and original hold remains.
    """
    party, order, commitments = _held_order(session, business)
    other = core.create_tenant(session, "Other GmbH")
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)

    foreign = client.post(
        f"/api/tenants/{other.id}/delivery-actions/prepare",
        json={
            "tool": "credit_hold_release",
            "request_id": "foreign-credit-release",
            "arguments": {"document_id": order.id, "reason": "Not ours"},
        },
    )
    assert foreign.status_code == 404, foreign.text
    exposure = client.get(f"/api/tenants/{other.id}/parties/{party.id}/credit-exposure")
    assert exposure.status_code == 404, exposure.text
    assert _held(session, business, commitments)


def test_the_cli_proposes_the_release_and_reads_the_exposure(
    session, business, monkeypatch
):
    """
    BUSINESS TEST:
    The cli proposes the release and reads the exposure.
    GIVEN:
    A credit-held order is exposed to CLI with the business tenant.
    WHEN:
    Read exposure, propose release and confirm returned proposal/token.
    THEN:
    CLI succeeds and reports over-limit; preparation retains hold and confirmation clears it.
    """
    tenant = business.tenant.id
    party, order, commitments = _held_order(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    runner = CliRunner()

    exposure = runner.invoke(
        cli_module.app, ["credit-exposure", party.id, "--tenant-id", tenant]
    )
    assert exposure.exit_code == 0, exposure.output
    assert json.loads(exposure.output)["over_limit"] is True

    proposed = runner.invoke(
        cli_module.app,
        [
            "credit-hold-release-propose",
            json.dumps({"document_id": order.id, "reason": "Prepayment received"}),
            "cli-credit-release",
            "--tenant-id",
            tenant,
        ],
    )
    assert proposed.exit_code == 0, proposed.output
    assert _held(session, business, commitments)
    detail = json.loads(proposed.output)
    approve_and_execute_proposal(
        session,
        tenant,
        detail["id"],
        review_token=detail["review"]["token"],
        confirmed=True,
    )
    assert _held(session, business, commitments) == []


def test_the_cli_help_lists_the_credit_commands():
    """
    BUSINESS TEST:
    The cli help lists the credit commands.
    GIVEN:
    CLI application is registered.
    WHEN:
    Request top-level help.
    THEN:
    Help contains credit-hold-release-propose and credit-exposure.
    """
    result = CliRunner().invoke(cli_module.app, ["--help"])
    for command in ("credit-hold-release-propose", "credit-exposure"):
        assert command in result.output


def test_the_party_inspector_shows_the_exposure_for_a_limited_customer(
    session, business
):
    """
    BUSINESS TEST:
    The party inspector shows the exposure for a limited customer.
    GIVEN:
    One customer has a credit limit and held order; fixture customer has no limit.
    WHEN:
    Read both party inspectors.
    THEN:
    Only limited customer gets credit exposure section with invoice, order, credit, exposure and limit rows.
    """
    from reality.web.api import party_inspector

    party, _, _ = _held_order(session, business)
    # Positive control: a customer without a limit has no exposure section.
    plain = party_inspector(session, business.tenant.id, business.customer.id)
    assert "Credit exposure" not in [section["title"] for section in plain["sections"]]

    inspector = party_inspector(session, business.tenant.id, party.id)

    section = next(s for s in inspector["sections"] if s["title"] == "Credit exposure")
    labels = [row["label"] for row in section["rows"]]
    assert labels[:5] == [
        "Open invoices",
        "Open orders not yet invoiced",
        "Available credits",
        "Exposure",
        "Credit limit",
    ]
    assert "Above the limit" in labels


from intake_review_support import reviewed_create_party
