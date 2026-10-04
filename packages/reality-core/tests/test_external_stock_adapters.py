"""Spec 344 FR-002: external stock through a file, MCP/Chat, Web and CLI."""
import csv
import json
from datetime import timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from intake_review_support import accept_import_job
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ExternalStockStatement, Movement
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.mcp.server import _reject_unknown_fields
from reality.services import core
from reality.services.external_stock import external_stock
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _schema(name):
    return next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == name
    )


def _statements(session, tenant):
    session.expire_all()
    return list(
        session.scalars(
            select(ExternalStockStatement).where(
                ExternalStockStatement.tenant_id == tenant
            )
        )
    )


def _movements(session, tenant):
    return session.scalar(
        select(func.count()).select_from(Movement).where(Movement.tenant_id == tenant)
    )


def test_the_mcp_schema_is_strict():
    state = _schema("external_stock_state_propose")
    assert state["additionalProperties"] is False
    assert state["required"] == ["lines"]
    line = state["properties"]["lines"]["items"]
    assert line["additionalProperties"] is False
    assert set(line["required"]) == {"item_id", "location_id", "quantity"}
    assert set(_schema("external_stock")["properties"]) == {
        "item_id",
        "location_id",
        "differing_only",
    }


def test_an_agent_states_external_stock_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    definition = MCP_TOOL_REGISTRY["external_stock_state_propose"]
    arguments = {
        "lines": [
            {
                "item_id": business.item.id,
                "location_id": business.location.id,
                "quantity": "7",
            }
        ]
    }
    _reject_unknown_fields(definition.input_schema, arguments)

    proposed = definition.handler(session, tenant, arguments)

    assert proposed["requires_confirmation"] is True
    assert not _statements(session, tenant)
    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )
    (row,) = _statements(session, tenant)
    assert Decimal(row.quantity) == 7
    read = MCP_TOOL_REGISTRY["external_stock"].handler(
        session, tenant, {"differing_only": True}
    )
    assert [entry["stated_quantity"] for entry in read] == ["7"]


def test_the_web_and_the_cli_state_and_read_it(session, business, monkeypatch):
    tenant = business.tenant.id
    session.commit()
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)
    line = {
        "item_id": business.item.id,
        "location_id": business.location.id,
        "quantity": "3",
    }

    response = client.post(
        f"/api/tenants/{tenant}/external-stock/proposals", json={"lines": [line]}
    )

    assert response.status_code == 200, response.text
    (previewed,) = response.json()["preview"]["external_stock"]["lines"]
    assert previewed["difference"] == "3"
    refused = client.post(
        f"/api/tenants/{tenant}/external-stock/proposals",
        json={"lines": [{**line, "quantity": "-1"}]},
    )
    assert refused.status_code == 400

    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    result = CliRunner().invoke(
        cli_module.app,
        [
            "external-stock",
            "state",
            "--line",
            f"{business.item.id}@{business.location.id}=4",
            "--tenant",
            tenant,
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    # The web proposal waits for its confirmation; the CLI confirmed its own.
    assert [Decimal(row.quantity) for row in _statements(session, tenant)] == [4]
    rows = client.get(f"/api/tenants/{tenant}/external-stock").json()["rows"]
    assert [row["stated_quantity"] for row in rows] == ["4"]


def test_a_file_states_external_stock_and_moves_nothing(
    session, business, tmp_path, monkeypatch
):
    from reality.services.artifacts import stage_artifact
    from reality.services.file_interpreters import suggested_mapping
    from reality.tools.application import confirm_tool, propose_tool

    tenant = business.tenant.id
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    stated = core.now() - timedelta(days=1)
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "100",
        to_location_id=business.location.id,
        occurred_at=stated - timedelta(hours=1),
    )
    three_pl = core.create_party(
        session, tenant, "Fulfil GmbH", "supplier", accounting_code="3PL-1"
    )
    before = _movements(session, tenant)
    path = tmp_path / "3pl-stock.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["sku", "location", "quantity", "as_of", "party_accounting_code"]
        )
        writer.writerow(
            [
                business.item.sku,
                business.location.name,
                "95",
                stated.isoformat(),
                "3PL-1",
            ]
        )
    header = next(csv.reader(path.open(encoding="utf-8")))
    with path.open("rb") as handle:
        artifact, _ = stage_artifact(
            session, tenant, handle, filename=path.name, content_type="text/csv"
        )
    proposal = propose_tool(
        session,
        tenant,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "fulfil_3pl",
            "source_type": "stock_report",
            "expected_target": "external_stock",
            "column_mapping": suggested_mapping(header, "external_stock"),
        },
    )
    job_id = json.loads(confirm_tool(session, tenant, proposal.id).output)[
        "import_job_id"
    ]
    accept_import_job(session, tenant, job_id)

    (row,) = external_stock(session, tenant)
    assert (row["stated_quantity"], row["reality_quantity"], row["difference"]) == (
        "95",
        "100",
        "-5",
    )
    assert row["reporter_party_id"] == three_pl.id
    assert row["source_system"] == "fulfil_3pl"
    assert row["stated_at"] == stated.isoformat()
    assert _movements(session, tenant) == before
