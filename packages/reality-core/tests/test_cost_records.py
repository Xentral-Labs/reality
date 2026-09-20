"""Retained costing references resolve through one tenant-scoped read boundary."""

import json
from contextlib import contextmanager

import pytest
import test_company_generation_jobs as company_jobs
import test_contribution_reviews as revenue
import test_cost_captured_basis_storage as captured
import test_inventory_costing_services as stock
import test_selling_costs as selling
from sqlalchemy import event, select
from typer.testing import CliRunner

from reality.db.core import Base, Item
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core, costing
from reality.services.cost_records import RECORDS
from reality.services.costing import cost_record
from reality.tools.application import run_read_tool

cost_owner = selling.cost_owner
company_database = company_jobs.company_database
captured_database = captured.scheduled_database


def prepared(session, business, owner):
    args, data = revenue.prepared(session, business, owner)
    doc = selling.costs.evidence(session, business, "114", "0")
    selling.costs.execute(
        session, business, owner, selling.selling(session, business, data[0], doc)
    )
    args = selling.refresh(
        session, business, owner, args, data, selling.categories("outbound_freight")
    )
    _, result = stock.commit_review(session, business, owner, args)
    return result, data, doc


def test_record_allowlist_covers_cost_authority_and_rejects_unknown(session, business):
    # Disposable result caches and mutable publication pointers are not retained
    # authority. Keep this exact list so future cost tables require classification.
    caches = {
        "cost_company_contribution_result",
        "cost_company_inventory_result",
        "cost_company_publication",
        "cost_contribution_generation",
        "cost_contribution_row",
        "cost_contribution_snapshot",
        "cost_generation",
        "cost_inventory_generation",
        "cost_inventory_publication",
        "cost_inventory_row",
        "cost_inventory_snapshot",
        "cost_publication",
    }
    assert caches <= set(Base.metadata.tables)
    assert not caches & set(RECORDS)
    assert {k for k in RECORDS if k.startswith("cost_")} == {
        n for n in Base.metadata.tables if n.startswith("cost_") and n not in caches
    }
    for kind in [
        "tenant",
        "app_user",
        "cost_missing",
        "cost_part; SELECT 1",
        *sorted(caches),
    ]:
        with pytest.raises(core.NotFound):
            cost_record(session, business.tenant.id, kind, "missing")


def test_later_retained_company_context_is_inspectable_but_results_stay_private(
    company_database,
):
    factory, tenant, manifest = company_jobs._manifest(company_database)
    with factory() as session:
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        session.commit()
    with factory() as session:
        other = core.create_tenant(session, "Inspector neighbor")
        pending = Item(
            id="unflushed_company_cost_inspector",
            tenant_id=tenant,
            sku="pending-company-cost",
            name="Pending company cost",
        )
        session.add(pending)
        writes = []
        connection = session.connection()
        event.listen(
            connection,
            "before_cursor_execute",
            lambda conn, cursor, statement, *args: (
                writes.append(statement)
                if statement.lstrip().split()[0].upper()
                in {"INSERT", "UPDATE", "DELETE"}
                else None
            ),
        )
        census = cost_record(
            session, tenant, "cost_company_census", manifest["census_id"]
        )
        held = cost_record(session, tenant, "cost_company_manifest", manifest["id"])
        generation = cost_record(
            session, tenant, "cost_company_generation", built["generation_id"]
        )
        assert census["fields"]["content_hash"]
        assert held["fields"]["census_id"] == manifest["census_id"]
        assert held["member_page"]["total"] == 2
        assert {"kind": "cost_company_census", "id": manifest["census_id"]} in [
            row["link"] for row in held["sections"][1]["rows"]
        ]
        assert generation["fields"]["manifest_id"] == manifest["id"]
        assert generation["member_page"]["total"] == 0
        assert {"kind": "cost_company_manifest", "id": manifest["id"]} in [
            row["link"] for row in generation["sections"][1]["rows"]
        ]
        with pytest.raises(core.NotFound):
            cost_record(
                session,
                other.id,
                "cost_company_generation",
                built["generation_id"],
            )
        for kind in (
            "cost_company_inventory_result",
            "cost_company_contribution_result",
            "cost_company_publication",
        ):
            with pytest.raises(core.NotFound):
                cost_record(session, tenant, kind, "hidden")
        assert not writes and pending in session.new
        session.expunge(pending)


def test_captured_basis_and_exact_members_are_inspectable(captured_database):
    factory, tenant, census_id, basis = captured.retained(captured_database)
    with factory() as session:
        held = cost_record(session, tenant, "cost_captured_basis", basis["basis_id"])
        assert held["fields"]["census_id"] == census_id
        assert held["fields"]["basis_digest"] == basis["digest"]
        assert held["member_page"]["total"] == 2
        assert {row["link"]["kind"] for row in held["sections"][2]["rows"]} == {
            "cost_captured_contribution_basis",
            "cost_captured_inventory_basis",
        }
        for row in held["sections"][2]["rows"]:
            member = cost_record(
                session, tenant, row["link"]["kind"], row["link"]["id"]
            )
            assert member["fields"]["basis_id"] == basis["basis_id"]


def test_real_cost_records_are_inspectable_and_tenant_scoped(
    session, business, cost_owner
):
    result, _, _ = prepared(session, business, cost_owner)
    other = core.create_tenant(session, "Neighbor")
    seen = set()
    for kind in RECORDS:
        table = Base.metadata.tables[kind]
        identity = session.scalar(
            select(table.c.id).where(table.c.tenant_id == business.tenant.id).limit(1)
        )
        if identity is None:
            continue
        record = cost_record(session, business.tenant.id, kind, identity)
        assert record["id"] == identity and record["kind"] == kind
        assert record["status"] == "recorded"
        assert record["persistence"] == {
            "business_writes": False,
            "projection_writes": False,
        }
        for foreign_id in [identity, "absent"]:
            with pytest.raises(core.NotFound):
                cost_record(session, other.id, kind, foreign_id)
        seen.add(kind)
    assert {
        "cost_contribution_review",
        "cost_selling_review_member",
        "cost_inventory_review",
        "cost_input_manifest",
        "financial_component",
        "action",
    } <= seen
    args = {"kind": "cost_contribution_review", "record_id": result["review_id"]}
    expected = cost_record(session, business.tenant.id, **args)
    assert (
        run_read_tool(session, business.tenant.id, "cost.record.get", args) == expected
    )
    assert (
        MCP_TOOL_REGISTRY["cost_record_get"].handler(session, business.tenant.id, args)
        == expected
    )


def test_source_links_exact_amounts_and_bridge_redaction(session, business, cost_owner):
    result, _, doc = prepared(session, business, cost_owner)
    part = result["trace"]["selling"]["parts"][0]
    component = cost_record(
        session, business.tenant.id, "financial_component", part["component"]["id"]
    )
    assert component["fields"]["stated_net"] == "114.0000"
    assert {"kind": "document", "id": doc.id} in [
        r.get("link") for s in component["sections"] for r in s["rows"]
    ]
    action = cost_record(session, business.tenant.id, "action", result["action_id"])
    assert "input" not in action["fields"] and "output" not in action["fields"]
    german = cost_record(
        session,
        business.tenant.id,
        "cost_contribution_review",
        result["review_id"],
        language="de",
    )
    assert "Deckungsbeitrag" in german["title"]
    assert (
        cost_record(
            session,
            business.tenant.id,
            "cost_contribution_review",
            result["review_id"],
            language="nl",
        )["title"]
        != german["title"]
    )


def test_membership_pages_no_flush_and_no_business_writes(
    session, business, cost_owner
):
    result, _, _ = prepared(session, business, cost_owner)
    first = cost_record(
        session, business.tenant.id, "cost_contribution_review", result["review_id"]
    )
    assert first["member_page"]["total"] == 8
    assert first["member_page"]["size"] == 25
    for page in [0, -1, 10001]:
        with pytest.raises(core.InvalidOperation):
            cost_record(
                session,
                business.tenant.id,
                "cost_contribution_review",
                result["review_id"],
                page=page,
            )
    pending = Item(
        id="unflushed_cost_inspector",
        tenant_id=business.tenant.id,
        sku="pending",
        name="pending",
    )
    session.add(pending)
    writes = []

    def watch(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            writes.append(statement)

    conn = session.connection()
    event.listen(conn, "before_cursor_execute", watch)
    try:
        assert (
            cost_record(
                session,
                business.tenant.id,
                "cost_contribution_review",
                result["review_id"],
            )
            == first
        )
    finally:
        event.remove(conn, "before_cursor_execute", watch)
    assert not writes and pending in session.new
    session.expunge(pending)


def test_web_and_cli_use_same_cost_record_service(
    session, business, cost_owner, monkeypatch
):
    import importlib

    from test_http_boundary import client_for

    cli = importlib.import_module("reality.cli.app")
    result, _, _ = prepared(session, business, cost_owner)
    expected = cost_record(
        session, business.tenant.id, "cost_contribution_review", result["review_id"]
    )
    client = client_for(session, monkeypatch)
    response = client.get(
        f"/api/tenants/{business.tenant.id}/inspector/cost_contribution_review/{result['review_id']}"
    )
    assert response.status_code == 200
    assert response.json()["fields"] == expected["fields"]
    assert response.json()["member_page"] == expected["member_page"]

    @contextmanager
    def scope():
        yield session

    monkeypatch.setattr(cli, "Session", scope)
    monkeypatch.setattr(
        cli, "init_db", lambda: pytest.fail("A record read must not initialize schema")
    )
    output = CliRunner().invoke(
        cli.app,
        [
            "cost-record",
            "cost_contribution_review",
            result["review_id"],
            "--tenant-id",
            business.tenant.id,
        ],
    )
    assert output.exit_code == 0, output.output
    assert json.loads(output.output) == expected


def test_membership_pages_cover_all_retained_parts_without_duplicates(
    session, business, cost_owner
):
    _, data, _ = prepared(session, business, cost_owner)
    for _ in range(26):
        doc = selling.costs.evidence(session, business, "1", "0")
        selling.costs.execute(
            session,
            business,
            cost_owner,
            selling.selling(session, business, data[0], doc, "1"),
        )
    args = {
        "operation": "contribution_review",
        "document_line_id": data[0].id,
        "profile": "commercial_v1",
        "profile_confirmed": True,
        "revenue_complete": True,
        "economic_at": data[4].occurred_at.isoformat(),
        "reason": "Review full member page",
    }
    args = selling.refresh(
        session,
        business,
        cost_owner,
        args,
        data,
        selling.categories("outbound_freight"),
    )
    _, result = stock.commit_review(session, business, cost_owner, args)
    first = cost_record(
        session, business.tenant.id, "cost_contribution_review", result["review_id"]
    )
    second = cost_record(
        session,
        business.tenant.id,
        "cost_contribution_review",
        result["review_id"],
        page=2,
    )
    assert first["member_page"]["total"] == 34
    assert first["member_page"]["has_next"] and second["member_page"]["has_previous"]
    members = [
        r["link"]["id"] for page in [first, second] for r in page["sections"][2]["rows"]
    ]
    assert len(members) == len(set(members)) == 34
    assert len(first["sections"][2]["rows"]) == 25
    assert len(second["sections"][2]["rows"]) == 9


def test_register_discovers_cost_records_without_foreign_rows(
    session, business, cost_owner
):
    from reality.services.inspector_register import inspector_records

    result, _, _ = prepared(session, business, cost_owner)
    page = inspector_records(
        session, business.tenant.id, kind="cost_contribution_review", language="de"
    )
    assert page["items"][0]["id"] == result["review_id"]
    assert "Deckungsbeitrag" in page["items"][0]["label"]
    other = core.create_tenant(session, "Neighbor")
    assert (
        inspector_records(session, other.id, kind="cost_contribution_review")["page"][
            "total"
        ]
        == 0
    )
