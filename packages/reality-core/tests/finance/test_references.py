"""Managed references preserve identity, confirmation and historical decisions."""

import json

import pytest
from sqlalchemy import func, select

from reality.db.core import LedgerEntry
from reality.services import core
from reality.services.finance import references as refs
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def propose(session, tenant, **values):
    return create_change_proposal(
        session,
        tenant,
        "finance.reference.update"
        if "reference_id" in values
        else "finance.reference.create",
        {
            "expected_revision": refs.list_references(session, tenant)["revision"],
            "reason": "Approved internal classification",
            **values,
        },
    )


def confirm(session, tenant, proposal):
    return json.loads(approve_and_execute_proposal(session, tenant, proposal.id).output)


@pytest.mark.parametrize("kind", ["cost_center", "case_code", "coding_group"])
def test_reference_lifecycle_and_immutable_history(session, business, kind):
    tenant = business.tenant.id
    proposal = propose(session, tenant, kind=kind, code="EU", name="European sales")
    assert refs.list_references(session, tenant)["total"] == 0
    assert json.loads(proposal.output)["reference"]["before"] is None
    first = confirm(session, tenant, proposal)
    assert confirm(session, tenant, proposal) == first
    assert refs.resolve_reference(session, tenant, first["id"], kind).id == first["id"]
    changed = confirm(
        session,
        tenant,
        propose(
            session, tenant, reference_id=first["id"], name="Export", state="blocked"
        ),
    )
    assert changed["id"] == first["id"] and changed["revision"] == 2
    with pytest.raises(core.InvalidOperation, match="blocked"):
        refs.resolve_reference(session, tenant, first["id"], kind)
    history = refs.reference_history(session, tenant, first["id"])
    assert history["total"] == 2
    assert history["items"][0]["before"] == first
    assert history["items"][0]["after"] == changed
    assert history["items"][1]["after"]["name"] == "European sales"
    assert history["items"][1]["action_id"] == proposal.id
    confirm(
        session,
        tenant,
        propose(
            session, tenant, reference_id=first["id"], name="Export", state="active"
        ),
    )
    assert refs.resolve_reference(session, tenant, first["id"], kind).state == "active"
    assert (
        session.scalar(
            select(func.count())
            .select_from(LedgerEntry)
            .where(LedgerEntry.tenant_id == tenant)
        )
        == 0
    )


def test_reference_tenant_kind_validation_and_paging(session, business):
    tenant = business.tenant.id
    rows = [
        confirm(
            session, tenant, propose(session, tenant, kind=kind, code="SAME", name=kind)
        )
        for kind in refs.REFERENCE_KINDS
    ]
    with pytest.raises(core.Conflict, match="already"):
        propose(session, tenant, kind="cost_center", code="SAME", name="Duplicate")
    other = core.create_tenant(session, "Other reference owner").id
    confirm(
        session,
        other,
        propose(session, other, kind="cost_center", code="SAME", name="Foreign"),
    )
    with pytest.raises(core.NotFound):
        refs.reference_history(session, other, rows[0]["id"])
    with pytest.raises(core.NotFound):
        refs.resolve_reference(session, other, rows[0]["id"], "cost_center")
    with pytest.raises(core.InvalidOperation, match="kind"):
        refs.resolve_reference(session, tenant, rows[0]["id"], "case_code")
    page = refs.list_references(session, tenant, query="SAME", limit=1, offset=1)
    assert page["total"] == 3 and len(page["items"]) == 1
    assert refs.list_references(session, tenant, kind="coding_group")["total"] == 1
    assert refs.list_references(session, tenant, state="blocked")["total"] == 0
    for values in (
        {"kind": "guess"},
        {"state": "guess"},
        {"limit": 201},
        {"offset": -1},
    ):
        with pytest.raises(core.InvalidOperation):
            refs.list_references(session, tenant, **values)
    with pytest.raises(core.InvalidOperation):
        propose(session, tenant, kind="cost_center", code=" ", name="Invalid")


def test_stale_confirmation_and_rollback(session, business, monkeypatch):
    tenant = business.tenant.id
    first = propose(session, tenant, kind="cost_center", code="A", name="A")
    stale = propose(session, tenant, kind="case_code", code="B", name="B")
    confirm(session, tenant, first)
    with pytest.raises(core.Conflict, match="stale"):
        confirm(session, tenant, stale)
    pending = propose(session, tenant, kind="coding_group", code="C", name="C")
    with monkeypatch.context() as patch:

        def fail(*args, **kwargs):
            raise RuntimeError("audit failure")

        patch.setattr(core, "emit_business_event", fail)
        with pytest.raises(RuntimeError, match="audit failure"):
            confirm(session, tenant, pending)
    assert refs.list_references(session, tenant)["total"] == 1
    assert confirm(session, tenant, pending)["code"] == "C"


def test_reference_owner_confirmation_and_adapter_parity(
    session, business, monkeypatch, scheduled_owner
):
    from fastapi.testclient import TestClient

    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.services.memberships import Principal
    from reality.web.api import database_session
    from reality.web.app import app

    tenant = business.tenant.id
    proposal = propose(
        session, tenant, kind="cost_center", code="OWNER", name="Warehouse"
    )
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    with pytest.raises(core.InvalidOperation, match="owner"):
        confirm(session, tenant, proposal)
    principal = Principal(user_id=scheduled_owner.id)
    receipt = json.loads(
        approve_and_execute_proposal(
            session, tenant, proposal.id, confirming_principal=principal
        ).output
    )
    history = refs.reference_history(session, tenant, receipt["id"])
    assert history["items"][0]["actor_id"] == scheduled_owner.id
    monkeypatch.setenv("REALITY_AUTH_MODE", "disabled")
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{tenant}/finance/references"
            assert client.get(base).json() == MCP_TOOL_REGISTRY[
                "finance_references"
            ].handler(session, tenant, {})
            assert client.get(base + f"/{receipt['id']}/history").json() == history
            assert client.get(base + "?limit=201").status_code == 400
            args = {
                "kind": "coding_group",
                "code": "GOODS",
                "name": "Goods",
                "reason": "Explicit grouping",
                "expected_revision": refs.list_references(session, tenant)["revision"],
            }
            response = client.post(
                base + "/proposals",
                json={"tool": "finance.reference.create", "arguments": args},
            )
            assert response.status_code == 200, response.text
            assert (
                response.json()["preview"]["reference"]
                == MCP_TOOL_REGISTRY["finance_reference_create_propose"].handler(
                    session, tenant, args
                )["preview"]["reference"]
            )
            assert refs.list_references(session, tenant)["total"] == 1
            assert (
                client.post(
                    f"/api/tenants/{tenant}/change-proposals/{response.json()['id']}/approve",
                    json={},
                ).status_code
                == 200
            )
    finally:
        app.dependency_overrides.clear()


def test_reference_migration_preserves_postings_and_blocks_destructive_downgrade(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.orm import Session

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0050_opening_subledger")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as db:
            tenant = core.create_tenant(db, "Preserved finance").id
            party = core.create_party(db, tenant, "Customer", "customer")
            invoice = core.create_document(
                db, tenant, "sales_invoice", "INV", party.id, "119"
            )
            core.post_sales_invoice(db, tenant, invoice.id)
            before = (
                db.execute(
                    text(
                        "SELECT row_to_json(e)::text FROM ledger_entry e WHERE tenant_id=:tenant ORDER BY id"
                    ),
                    {"tenant": tenant},
                )
                .scalars()
                .all()
            )
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text(
                        "SELECT row_to_json(e)::text FROM ledger_entry e WHERE tenant_id=:tenant ORDER BY id"
                    ),
                    {"tenant": tenant},
                )
                .scalars()
                .all()
                == before
            )
        command.downgrade(config, "0050_opening_subledger")
        assert "finance_reference" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        with Session(engine) as db:
            confirm(
                db,
                tenant,
                propose(
                    db, tenant, kind="cost_center", code="WAREHOUSE", name="Warehouse"
                ),
            )
        with pytest.raises(RuntimeError, match="history"):
            command.downgrade(config, "0050_opening_subledger")
    finally:
        engine.dispose()


def test_reference_concurrent_confirmation_has_one_decision(scheduled_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from reality.db.core import BusinessEvent

    _, factory, tenant, _ = scheduled_database
    with factory() as db:
        proposal_id = propose(db, tenant, kind="cost_center", code="ONE", name="One").id
    barrier = Barrier(2)

    def execute():
        with factory() as db:
            barrier.wait(timeout=10)
            return json.loads(
                approve_and_execute_proposal(db, tenant, proposal_id).output
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: execute(), range(2)))
    assert results[0] == results[1]
    with factory() as db:
        assert refs.list_references(db, tenant)["total"] == 1
        assert (
            db.scalar(
                select(func.count())
                .select_from(BusinessEvent)
                .where(
                    BusinessEvent.tenant_id == tenant,
                    BusinessEvent.event_type == "finance.reference_changed",
                )
            )
            == 1
        )


def test_reference_member_cannot_confirm_and_foreign_update_is_unavailable(
    session, business, scheduled_owner
):
    from reality.db.core import TenantMembership
    from reality.services.memberships import Principal

    tenant = business.tenant.id
    proposal = propose(session, tenant, kind="cost_center", code="A", name="A")
    member = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    member.role = "member"
    session.flush()
    with pytest.raises(core.InvalidOperation):
        approve_and_execute_proposal(
            session,
            tenant,
            proposal.id,
            confirming_principal=Principal(scheduled_owner.id),
        )
    assert refs.list_references(session, tenant)["total"] == 0
    member.role = "owner"
    session.flush()
    row = confirm(session, tenant, proposal)
    other = core.create_tenant(session, "Foreign classifications").id
    with pytest.raises(core.NotFound):
        propose(
            session, other, reference_id=row["id"], name="Foreign edit", state="blocked"
        )
    assert refs.resolve_reference(session, tenant, row["id"], "cost_center").name == "A"


def test_reference_competing_changes_reject_stale_intent(scheduled_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    _, factory, tenant, _ = scheduled_database
    with factory() as db:
        row = confirm(
            db,
            tenant,
            propose(db, tenant, kind="cost_center", code="SHARED", name="Original"),
        )
        proposal_ids = [
            propose(db, tenant, reference_id=row["id"], name=name, state="active").id
            for name in ("First intent", "Second intent")
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
        outcomes = list(pool.map(execute, proposal_ids))
    assert sorted(outcomes) == ["executed", "stale"]
    with factory() as db:
        assert refs.reference_history(db, tenant, row["id"])["total"] == 2


def test_reference_cli_reads_and_proposal_use_shared_services(
    scheduled_database, monkeypatch
):
    from typer.testing import CliRunner

    from reality.cli import app as cli_module

    _, factory, tenant, _ = scheduled_database
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    runner = CliRunner()
    result = runner.invoke(
        cli_module.app, ["finance-references", "--tenant-id", tenant]
    )
    assert result.exit_code == 0, result.output
    current = json.loads(result.output)
    arguments = {
        "kind": "cost_center",
        "code": "CLI",
        "name": "CLI center",
        "reason": "Owner-defined center",
        "expected_revision": current["revision"],
    }
    result = runner.invoke(
        cli_module.app,
        [
            "finance-reference-propose",
            "finance.reference.create",
            json.dumps(arguments),
            "--tenant-id",
            tenant,
        ],
    )
    assert result.exit_code == 0, result.output
    proposal_id = json.loads(result.output)["id"]
    with factory() as db:
        assert refs.list_references(db, tenant)["total"] == 0
        row = json.loads(approve_and_execute_proposal(db, tenant, proposal_id).output)
    result = runner.invoke(
        cli_module.app, ["finance-reference-history", row["id"], "--tenant-id", tenant]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["items"][0]["action_id"] == proposal_id
