"""Spec 295 FR-005/FR-012: one dunning run behind Web, MCP/Chat and CLI."""

import json

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, DunningNotice
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.services.finance.accounts import list_accounts
from reality.tools.application import approve_and_execute_proposal, run_read_tool
from reality.web import api as api_module
from reality.web import app as web_module

FREE = [
    {"level": 1, "wait_days": 7, "fee_amount": "0"},
    {"level": 2, "wait_days": 14, "fee_amount": "0"},
    {"level": 3, "wait_days": 14, "fee_amount": "0"},
]


def _mcp(session, tenant, name, arguments):
    return MCP_TOOL_REGISTRY[name].handler(session, tenant, arguments)


def _confirm(session, tenant, proposed):
    return json.loads(
        approve_and_execute_proposal(
            session, tenant, proposed["proposal_id"], confirmed=True
        ).output
    )


def _overdue(session, business, number, day="2026-08-01", party=None):
    tenant = business.tenant.id
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        number,
        (party or business.customer).id,
        "100",
        document_date=day,
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    return invoice


def _schedule(session, tenant):
    revision = _mcp(session, tenant, "finance_dunning_schedule", {})["revision"]
    proposed = _mcp(
        session,
        tenant,
        "finance_dunning_schedule_set_propose",
        {"expected_revision": revision, "levels": FREE},
    )
    return _confirm(session, tenant, proposed)


def _notices(session):
    return session.scalar(select(func.count()).select_from(DunningNotice))


def test_the_mcp_schemas_are_strict_and_name_their_fields():
    schemas = {
        tool["function"]["name"]: tool["function"]["parameters"]
        for tool in model_tool_schemas()
    }
    run = schemas["finance_dunning_run_propose"]
    assert run["additionalProperties"] is False
    assert set(run["properties"]) == {
        "schedule_source_record_id",
        "run_date",
        "party_ids",
        "items",
    }
    assert set(run["required"]) == {"schedule_source_record_id", "run_date", "items"}
    handover = schemas["finance_dunning_collection_propose"]
    assert set(handover["properties"]) == {
        "expected_revision",
        "invoice_ids",
        "handover_date",
        "reason",
    }
    assert schemas["finance_dunning_run_context"]["required"] == ["run_date"]
    for name in (
        "finance_dunning_schedule",
        "finance_dunning_schedule_set_propose",
        "finance_dunning_collection_handovers",
        "finance_dunning_collection_handover",
    ):
        assert name in schemas


def test_an_agent_prepares_the_run_and_a_person_confirms_it(session, business):
    tenant = business.tenant.id
    _schedule(session, tenant)
    invoice = _overdue(session, business, "INV-T019-MCP")

    context = _mcp(
        session, tenant, "finance_dunning_run_context", {"run_date": "2026-09-01"}
    )
    assert context == run_read_tool(
        session, tenant, "finance.dunning.run_context", {"run_date": "2026-09-01"}
    )
    proposed = _mcp(
        session,
        tenant,
        "finance_dunning_run_propose",
        {
            "schedule_source_record_id": context["schedule_source_record_id"],
            "run_date": "2026-09-01",
            "items": [{"invoice_id": invoice.id, "level": 1}],
        },
    )
    assert proposed["next_step"]["required_principal"] == "authenticated_active_owner"
    # Proposing records nothing.
    assert _notices(session) == 0

    receipt = _confirm(session, tenant, proposed)

    assert [notice["invoice_ids"] for notice in receipt["notices"]] == [[invoice.id]]
    assert _notices(session) == 1


def test_an_agent_prepares_a_collection_handover(session, business):
    tenant = business.tenant.id
    _schedule(session, tenant)
    invoice = _overdue(session, business, "INV-T019-COL", day="2026-05-01")
    for level, day in ((1, "2026-06-01"), (2, "2026-07-01"), (3, "2026-08-01")):
        proposed = _mcp(
            session,
            tenant,
            "finance_dunning_record_propose",
            {
                "expected_revision": list_accounts(session, tenant)["revision"],
                "invoice_ids": [invoice.id],
                "level": level,
                "notice_date": day,
            },
        )
        _confirm(session, tenant, proposed)

    proposed = _mcp(
        session,
        tenant,
        "finance_dunning_collection_propose",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "invoice_ids": [invoice.id],
            "handover_date": "2026-09-01",
            "reason": "No payment after the third reminder",
        },
    )
    assert (
        json.loads(
            session.get(ChangeProposal, (tenant, proposed["proposal_id"])).output
        )["collection_handover"]["delivery_hold"]
        == "placed"
    )
    handover = _confirm(session, tenant, proposed)

    listed = _mcp(session, tenant, "finance_dunning_collection_handovers", {})
    assert [row["id"] for row in listed] == [handover["id"]]
    detail = _mcp(
        session,
        tenant,
        "finance_dunning_collection_handover",
        {"handover_id": handover["id"]},
    )
    assert detail["invoice_ids"] == [invoice.id]


def test_the_web_reads_schedule_run_and_handovers(session, business, monkeypatch):
    tenant = business.tenant.id
    _schedule(session, tenant)
    other_customer = reviewed_create_party(session, tenant, "Weber AG", "customer")
    mine = _overdue(session, business, "INV-T019-WEB")
    _overdue(session, business, "INV-T019-WEB-2", party=other_customer)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)
    prefix = f"/api/tenants/{tenant}/finance/dunning"

    schedule = client.get(f"{prefix}/schedule")
    assert schedule.status_code == 200, schedule.text
    assert [level["wait_days"] for level in schedule.json()["levels"]] == [7, 14, 14]

    run = client.get(
        f"{prefix}/run-context",
        params={"run_date": "2026-09-01", "party_ids": [business.customer.id]},
    )
    assert run.status_code == 200, run.text
    assert [
        item["invoice_id"]
        for notice in run.json()["notices"]
        for item in notice["items"]
    ] == [mine.id]

    prepared = client.post(
        f"/api/tenants/{tenant}/finance/commercial/proposals",
        json={
            "tool": "finance.dunning.run",
            "arguments": {
                "schedule_source_record_id": run.json()["schedule_source_record_id"],
                "run_date": "2026-09-01",
                "items": [{"invoice_id": mine.id, "level": 1}],
            },
        },
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["preview"]["dunning_run"]["notices"][0]["level"] == 1

    handovers = client.get(f"{prefix}/collection-handovers")
    assert handovers.status_code == 200, handovers.text
    assert handovers.json() == {"items": []}


def test_the_web_refuses_a_run_without_schedule_and_foreign_handovers(
    session, business, monkeypatch
):
    tenant = business.tenant.id
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)

    missing = client.get(
        f"/api/tenants/{tenant}/finance/dunning/run-context",
        params={"run_date": "2026-09-01"},
    )
    assert missing.status_code == 400, missing.text
    assert "dunning schedule" in missing.text

    other = core.create_tenant(session, "Other GmbH")
    foreign = client.get(
        f"/api/tenants/{other.id}/finance/dunning/collection-handovers/col_missing"
    )
    assert foreign.status_code == 404, foreign.text


def test_the_cli_previews_proposes_and_reads(session, business, monkeypatch):
    tenant = business.tenant.id
    _schedule(session, tenant)
    invoice = _overdue(session, business, "INV-T019-CLI")
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    runner = CliRunner()

    schedule = runner.invoke(
        cli_module.app, ["finance-dunning-schedule", "--tenant-id", tenant]
    )
    assert schedule.exit_code == 0, schedule.output
    context = runner.invoke(
        cli_module.app,
        [
            "finance-dunning-run-context",
            "2026-09-01",
            "--party-id",
            business.customer.id,
            "--tenant-id",
            tenant,
        ],
    )
    assert context.exit_code == 0, context.output
    source = json.loads(context.output)["schedule_source_record_id"]

    proposed = runner.invoke(
        cli_module.app,
        [
            "finance-dunning-run-propose",
            json.dumps(
                {
                    "schedule_source_record_id": source,
                    "run_date": "2026-09-01",
                    "items": [{"invoice_id": invoice.id, "level": 1}],
                }
            ),
            "--tenant-id",
            tenant,
        ],
    )
    assert proposed.exit_code == 0, proposed.output
    assert _notices(session) == 0
    approve_and_execute_proposal(
        session, tenant, json.loads(proposed.output)["id"], confirmed=True
    )
    assert _notices(session) == 1

    handovers = runner.invoke(
        cli_module.app, ["finance-dunning-collection", "--tenant-id", tenant]
    )
    assert handovers.exit_code == 0, handovers.output
    assert json.loads(handovers.output) == []


def test_the_cli_help_lists_the_dunning_commands():
    result = CliRunner().invoke(cli_module.app, ["--help"])
    for command in (
        "finance-dunning-schedule",
        "finance-dunning-schedule-propose",
        "finance-dunning-run-context",
        "finance-dunning-run-propose",
        "finance-dunning-collection-propose",
        "finance-dunning-collection",
    ):
        assert command in result.output


from intake_review_support import reviewed_create_party
