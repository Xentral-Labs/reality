"""Source translation preserves evidence and never invents classification."""

import json

import pytest
from sqlalchemy import func, select

from reality.db.core import LedgerEntry
from reality.services import core
from reality.services.finance import components
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from tests.finance.test_components import fixture
from tests.finance.test_references import confirm, propose


def setup(session, business, detail=None, lines=False):
    tenant = business.tenant.id
    source = core.create_source_system(
        session, tenant, "declared-finance-test", "Finance source"
    )
    case = confirm(
        session,
        tenant,
        propose(session, tenant, kind="case_code", code="EU", name="Declared EU case"),
    )
    doc, _ = fixture(session, business, detail=detail, lines=lines)
    return tenant, source, case, doc


def prepare(session, tenant, source, case, **extra):
    from reality.services.finance import source_mappings as mappings

    return create_change_proposal(
        session,
        tenant,
        "finance.source_mapping.set",
        {
            "source_system_id": source.id,
            "namespace": "supplier-v1",
            "field_kind": "case_code",
            "source_code": "EU",
            "reference_id": case["id"],
            "state": "active",
            "reason": "Reviewed source declaration",
            "expected_revision": mappings.list_source_mappings(session, tenant)[
                "revision"
            ],
            **extra,
        },
    )


def test_source_mapping_preview_confirmation_and_no_financial_effect(session, business):
    from reality.services.finance import source_mappings as mappings

    tenant, source, case, doc = setup(session, business)
    before = components.component_context(session, tenant, doc.id)
    count = session.scalar(
        select(func.count())
        .select_from(LedgerEntry)
        .where(LedgerEntry.tenant_id == tenant)
    )
    assert before["items"][0]["source_resolution"]["case"]["status"] == "unmapped"
    pending = prepare(session, tenant, source, case)
    assert mappings.list_source_mappings(session, tenant)["total"] == 0
    row = json.loads(approve_and_execute_proposal(session, tenant, pending.id).output)
    assert (
        json.loads(approve_and_execute_proposal(session, tenant, pending.id).output)
        == row
    )
    after = components.component_context(session, tenant, doc.id)["items"][0]
    resolved = after["source_resolution"]["case"]
    assert (
        resolved["status"] == "resolved" and resolved["reference"]["id"] == case["id"]
    )
    assert resolved["mapping_id"] == row["id"]
    assert after["evidence_hash"] == before["items"][0]["evidence_hash"]
    assert after["current"] is None and after["component_id"] is None
    assert (
        session.scalar(
            select(func.count())
            .select_from(LedgerEntry)
            .where(LedgerEntry.tenant_id == tenant)
        )
        == count
    )


def test_source_mapping_revision_block_and_stale_confirmation(session, business):
    from reality.services.finance import source_mappings as mappings

    tenant, source, case, doc = setup(session, business)
    first = confirm(session, tenant, prepare(session, tenant, source, case))
    stale = prepare(session, tenant, source, case, state="blocked")
    blocked = confirm(
        session, tenant, prepare(session, tenant, source, case, state="blocked")
    )
    with pytest.raises(core.Conflict):
        approve_and_execute_proposal(session, tenant, stale.id)
    session.rollback()
    assert (
        components.component_context(session, tenant, doc.id)["items"][0][
            "source_resolution"
        ]["case"]["status"]
        == "blocked_mapping"
    )
    active = confirm(session, tenant, prepare(session, tenant, source, case))
    history = mappings.source_mapping_history(session, tenant, active["id"])
    assert [r["revision"] for r in history["items"]] == [3, 2, 1]
    assert [r["state"] for r in history["items"]] == ["active", "blocked", "active"]
    assert [r["is_current"] for r in history["items"]] == [True, False, False]
    assert (
        active["replaces_id"] == blocked["id"] and blocked["replaces_id"] == first["id"]
    )
    assert all(r["reason"] and r["action_id"] for r in history["items"])


def test_source_mapping_tenant_and_kind_boundaries(session, business):
    from reality.services.finance import source_mappings as mappings

    tenant, source, case, doc = setup(session, business)
    other = core.create_tenant(session, "Other mapping tenant")
    foreign = core.create_source_system(session, other.id, source.code, "Other source")
    with pytest.raises(core.NotFound):
        prepare(session, tenant, source, case, source_system_id=foreign.id)
    wrong = confirm(
        session,
        tenant,
        propose(session, tenant, kind="cost_center", code="CC", name="Center"),
    )
    with pytest.raises(core.InvalidOperation, match="wrong kind"):
        prepare(session, tenant, source, wrong)
    row = confirm(session, tenant, prepare(session, tenant, source, case))
    with pytest.raises(core.NotFound):
        mappings.source_mapping_history(session, other.id, row["id"])
    assert mappings.list_source_mappings(session, other.id)["total"] == 0
    with pytest.raises(core.NotFound):
        components.component_context(session, other.id, doc.id)
    with pytest.raises(core.InvalidOperation):
        mappings.list_source_mappings(session, tenant, limit=0)


@pytest.mark.parametrize(
    "codes,status",
    [
        ({}, "missing"),
        ({"case": "EU"}, "malformed"),
        ({"case": {"code": "EU"}}, "malformed"),
        ({"case": {"namespace": "supplier-v1", "code": 0}}, "malformed"),
        ({"case": {"namespace": "OTHER", "code": "EU"}}, "unmapped"),
        ({"case": {"namespace": "supplier-v1", "code": "eu"}}, "unmapped"),
    ],
)
def test_source_mapping_exact_declaration_only(session, business, codes, status):
    tenant, source, case, doc = setup(session, business, detail={"codes": codes})
    confirm(session, tenant, prepare(session, tenant, source, case))
    assert (
        components.component_context(session, tenant, doc.id)["items"][0][
            "source_resolution"
        ]["case"]["status"]
        == status
    )


def test_source_mapping_blocked_source_reference_and_internal_conflict(
    session, business
):
    tenant, source, case, doc = setup(session, business)
    confirm(session, tenant, prepare(session, tenant, source, case))
    source.is_active = False
    session.flush()

    def read():
        return components.component_context(session, tenant, doc.id)["items"][0][
            "source_resolution"
        ]["case"]

    assert read()["status"] == "blocked_source"
    source.is_active = True
    session.flush()
    confirm(
        session,
        tenant,
        propose(
            session, tenant, reference_id=case["id"], name=case["name"], state="blocked"
        ),
    )
    assert read()["status"] == "blocked_reference"
    confirm(
        session,
        tenant,
        propose(
            session, tenant, reference_id=case["id"], name=case["name"], state="active"
        ),
    )
    different = confirm(
        session,
        tenant,
        propose(
            session, tenant, kind="case_code", code="OTHER", name="Other declared case"
        ),
    )
    context = components.component_context(session, tenant, doc.id)
    assignment = create_change_proposal(
        session,
        tenant,
        "finance.component.assign",
        {
            "expected_revision": context["revision"],
            "document_id": doc.id,
            "expected_evidence_hash": context["items"][0]["evidence_hash"],
            "basis": "gross",
            "case_reference_id": different["id"],
            "reason": "Deliberate internal classification",
        },
    )
    confirm(session, tenant, assignment)
    assert read()["status"] == "conflict" and read()["reference"]["id"] == case["id"]


def test_source_mapping_replacement_keeps_snapshot_and_kind_scope(session, business):
    from reality.services.finance import source_mappings as mappings

    tenant, source, case, doc = setup(session, business)
    first = confirm(session, tenant, prepare(session, tenant, source, case))
    group = confirm(
        session,
        tenant,
        propose(
            session,
            tenant,
            kind="coding_group",
            code="SOURCE_GOODS",
            name="Source goods",
        ),
    )
    confirm(
        session,
        tenant,
        prepare(session, tenant, source, group, field_kind="coding_group"),
    )
    other = confirm(
        session,
        tenant,
        propose(session, tenant, kind="case_code", code="OTHER", name="Replacement"),
    )
    replaced = confirm(session, tenant, prepare(session, tenant, source, other))
    history = mappings.source_mapping_history(session, tenant, first["id"])
    assert history["items"][1]["reference_snapshot"]["name"] == case["name"]
    assert (
        replaced["replaces_id"] == first["id"]
        and mappings.list_source_mappings(session, tenant)["total"] == 2
    )
    assert (
        components.component_context(session, tenant, doc.id)["items"][0][
            "source_resolution"
        ]["case"]["reference"]["id"]
        == other["id"]
    )


def test_source_mapping_summary_is_not_inherited_by_lines(session, business):
    tenant, source, case, doc = setup(session, business, lines=True)
    from reality.db.core import DocumentLine

    line = session.scalar(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == doc.id
        )
    )
    line.payload = json.dumps({"reality_finance_v1": {"net": "1000", "tax": "190"}})
    session.flush()
    confirm(session, tenant, prepare(session, tenant, source, case))
    context = components.component_context(session, tenant, doc.id)
    assert context["summary"]["source_codes"]["case"]["code"] == "EU"
    assert all(
        row["source_resolution"]["case"]["status"] == "missing"
        for row in context["items"]
    )


def test_source_mapping_owner_adapters_and_atomic_rollback(
    session, business, monkeypatch, scheduled_owner
):
    from fastapi.testclient import TestClient
    from typer.testing import CliRunner

    from reality.cli.app import app as cli
    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.services.finance import source_mappings as mappings
    from reality.services.memberships import Principal
    from reality.web.api import database_session
    from reality.web.app import app

    tenant, source, case, _ = setup(session, business)
    pending = prepare(session, tenant, source, case)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    with pytest.raises(core.InvalidOperation, match="owner"):
        confirm(session, tenant, pending)
    row = json.loads(
        approve_and_execute_proposal(
            session,
            tenant,
            pending.id,
            confirming_principal=Principal(scheduled_owner.id),
        ).output
    )
    assert row["actor_id"] == scheduled_owner.id
    monkeypatch.setenv("REALITY_AUTH_MODE", "disabled")
    app.dependency_overrides[database_session] = lambda: session
    from contextlib import contextmanager

    @contextmanager
    def shared_session():
        yield session

    monkeypatch.setattr("reality.cli.app.Session", shared_session)
    monkeypatch.setattr("reality.cli.app.init_db", lambda: None)
    try:
        with TestClient(app) as client:
            path = f"/api/tenants/{tenant}/finance/source-mappings"
            http = client.get(path).json()
            assert http == MCP_TOOL_REGISTRY["finance_source_mappings"].handler(
                session, tenant, {}
            )
            result = CliRunner().invoke(
                cli, ["finance-source-mappings", "--tenant-id", tenant]
            )
            assert result.exit_code == 0, result.output
            assert json.loads(result.output) == http
            assert client.get(
                path + f"/{row['id']}/history"
            ).json() == MCP_TOOL_REGISTRY["finance_source_mapping_history"].handler(
                session, tenant, {"mapping_id": row["id"]}
            )
            assert client.get(path + "?limit=201").status_code == 400
    finally:
        app.dependency_overrides.clear()
    # Failed audit must roll back head replacement and allow retry.
    pending = prepare(session, tenant, source, case, state="blocked")

    def fail(*args, **kwargs):
        raise RuntimeError("audit failed")

    with monkeypatch.context() as patch:
        patch.setattr(mappings, "emit_business_event", fail)
        with pytest.raises(RuntimeError, match="audit failed"):
            confirm(session, tenant, pending)
    assert (
        mappings.list_source_mappings(session, tenant)["items"][0]["state"] == "active"
    )
    assert confirm(session, tenant, pending)["state"] == "blocked"


def test_source_mapping_concurrent_scope_activation(scheduled_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    from reality.services.finance import source_mappings as mappings

    _, factory, tenant, _ = scheduled_database
    with factory() as db:
        customer = core.create_party(db, tenant, "Concurrent customer", "customer")
        tenant, source, case, _ = setup(
            db, SimpleNamespace(tenant=SimpleNamespace(id=tenant), customer=customer)
        )
        ids = [
            prepare(db, tenant, source, case).id,
            prepare(db, tenant, source, case).id,
        ]
    barrier = Barrier(2)

    def execute(proposal_id):
        with factory() as db:
            barrier.wait(timeout=10)
            try:
                return approve_and_execute_proposal(db, tenant, proposal_id).status
            except core.Conflict:
                return "stale"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(execute, ids)) == ["executed", "stale"]
    with factory() as db:
        assert mappings.list_source_mappings(db, tenant)["total"] == 1


def test_source_mapping_migration_preserves_ledger_and_history(
    postgres_database, monkeypatch
):
    from types import SimpleNamespace

    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0052_component_assignments")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as db:
            tenant = core.create_tenant(db, "Source mapping migration").id
            customer = core.create_party(db, tenant, "Customer", "customer")
            doc = core.create_document(
                db, tenant, "sales_invoice", "PRESERVED", customer.id, "119"
            )
            core.post_sales_invoice(db, tenant, doc.id)
            customer = SimpleNamespace(id=customer.id)
            before = (
                db.execute(
                    text("SELECT row_to_json(e)::text FROM ledger_entry e ORDER BY id")
                )
                .scalars()
                .all()
            )
        command.upgrade(config, "head")
        with Session(engine) as db:
            assert (
                db.execute(
                    text("SELECT row_to_json(e)::text FROM ledger_entry e ORDER BY id")
                )
                .scalars()
                .all()
                == before
            )
        command.downgrade(config, "0052_component_assignments")
        command.upgrade(config, "head")
        with Session(engine) as db:
            tenant, source, case, _ = setup(
                db,
                SimpleNamespace(tenant=SimpleNamespace(id=tenant), customer=customer),
            )
            confirm(db, tenant, prepare(db, tenant, source, case))
        with pytest.raises(RuntimeError, match="history"):
            command.downgrade(config, "0052_component_assignments")
    finally:
        engine.dispose()


def test_source_mapping_searches_are_independent_and_group_resolution_is_exact(
    session, business
):
    from reality.services.finance import source_mappings as mappings

    tenant, source, case, doc = setup(
        session,
        business,
        detail={
            "codes": {
                "case": {"namespace": "supplier-v1", "code": "EU"},
                "group": {"namespace": "supplier-v1", "code": "EU"},
            }
        },
    )
    group = confirm(
        session,
        tenant,
        propose(session, tenant, kind="coding_group", code="SHIP", name="Freight"),
    )
    confirm(session, tenant, prepare(session, tenant, source, case))
    confirm(
        session,
        tenant,
        prepare(session, tenant, source, group, field_kind="coding_group"),
    )
    result = mappings.list_source_mappings(
        session,
        tenant,
        query="supplier-v1",
        source_query="Finance source",
        reference_query="Freight",
    )
    assert result["total"] == 2 and result["sources_total"] == 1
    assert result["references"]["case_code"]["total"] == 0
    assert result["references"]["coding_group"]["items"][0]["id"] == group["id"]
    resolution = components.component_context(session, tenant, doc.id)["items"][0][
        "source_resolution"
    ]
    assert resolution["case"]["reference"]["id"] == case["id"]
    assert resolution["group"]["reference"]["id"] == group["id"]
    assert resolution["case"]["mapping_id"] != resolution["group"]["mapping_id"]
