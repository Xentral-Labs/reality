"""Spec 266 US1: every channel records one interaction at its own boundary."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

import pytest
from conftest import _drop_database, admin_engine, admin_url
from fastapi.testclient import TestClient
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker
from test_engine_room_recording import recording, rows  # noqa: F401

from reality.agent import mcp_chat
from reality.cli.app import _command_path
from reality.db.core import AppUser, Base, TenantMembership, now, uid
from reality.db.interactions import Interaction
from reality.mcp import server as mcp_module
from reality.mcp.auth import create_mcp_access_token
from reality.services import interaction_recorder as interactions
from reality.services.core import create_item, create_tenant
from reality.tools.application import create_change_proposal
from reality.web import api as api_module
from reality.web import app as web_module
from reality.web import auth as auth_module

PASSWORD = "a-long-account-password"


def member(session, tenant_id, role="owner"):
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash=auth_module.password_hasher.hash(PASSWORD),
        display_name="Anna Owner",
        status="active",
        email_verified_at=now(),
    )
    session.add(user)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("mem"),
            tenant_id=tenant_id,
            user_id=user.id,
            role=role,
            status="active",
        )
    )
    session.commit()
    return user


@pytest.fixture(scope="module")
def committed_engine():
    """A committed database for the web: request and recorder on their own
    connections, as in production. Sharing the test connection between the
    request thread and the recorder's thread is unsafe and loses rows."""
    database_name = f"reality_engine_room_{uuid.uuid4().hex[:10]}"
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    url = admin_url.set(database=database_name).render_as_string(hide_password=False)
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()
        _drop_database(database_name)


@dataclass
class Web:
    db: Session
    tenant_id: str
    sign_in: object


@pytest.fixture
def web(committed_engine, monkeypatch):
    factory = sessionmaker(committed_engine, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    monkeypatch.setenv("REALITY_INTERACTIONS", "on")
    # In line, whatever writer an earlier test's app lifespan started.
    monkeypatch.setattr(interactions, "_queue", None)

    def sign_in(user):
        client = TestClient(web_module.app)
        login = client.post(
            "/api/auth/login", json={"email": user.email, "password": PASSWORD}
        )
        assert login.status_code == 200
        return client

    with factory() as db, interactions.use_session_factory(factory):
        tenant = create_tenant(db, f"Engine Room {uid('co')}")
        create_item(db, tenant.id, "BIKE-LIGHT", "Bike Light")
        db.commit()
        yield Web(db, tenant.id, sign_in)


def test_a_web_read_is_recorded_under_the_person_and_route_template(web):
    owner = member(web.db, web.tenant_id)
    response = web.sign_in(owner).get(
        f"/api/tenants/{web.tenant_id}/items",
        headers={"X-Reality-Correlation": "click_42"},
    )
    assert response.status_code == 200
    [row] = rows(web.db, web.tenant_id)
    assert (row.channel, row.kind, row.operation, row.outcome) == (
        "web",
        "read",
        "GET /items",
        "ok",
    )
    assert row.actor_user_id == owner.id and row.correlation_id == "click_42"


def test_a_web_write_links_the_events_it_committed(web):
    owner = member(web.db, web.tenant_id)
    response = web.sign_in(owner).post(
        f"/api/tenants/{web.tenant_id}/items",
        json={"sku": "SECRET-SKU-4711", "name": "Lamp for Müller"},
    )
    assert response.status_code == 201, response.text
    [row] = rows(web.db, web.tenant_id)
    assert (row.operation, row.kind) == ("POST /items", "write")
    assert row.event_ranges and row.event_first_sequence is not None
    # FR-003: nothing the caller sent reaches the row.
    stored = json.dumps(
        {c.name: str(getattr(row, c.name)) for c in Interaction.__table__.columns}
    )
    assert "SECRET-SKU-4711" not in stored and "Müller" not in stored


def test_web_approval_is_a_decision_linked_to_its_proposal(web):
    owner = member(web.db, web.tenant_id)
    proposal = create_change_proposal(
        web.db,
        web.tenant_id,
        "payment_term_create",
        {"code": "N14", "name": "Net 14", "due_days": 14},
    )
    web.db.commit()
    response = web.sign_in(owner).post(
        f"/api/tenants/{web.tenant_id}/change-proposals/{proposal.id}/approve",
        json={"confirmed": True},
    )
    assert response.status_code == 200, response.text
    [row] = rows(web.db, web.tenant_id)
    assert (row.kind, row.proposal_id, row.outcome) == ("decide", proposal.id, "ok")
    assert row.event_ranges


def test_refresh_requests_are_stored_but_flagged(web):
    owner = member(web.db, web.tenant_id)
    web.sign_in(owner).get(
        f"/api/tenants/{web.tenant_id}/items", headers={"X-Reality-Refresh": "1"}
    )
    [row] = rows(web.db, web.tenant_id)
    assert row.refresh is True


def test_the_engine_room_does_not_record_its_own_reads(web):
    owner = member(web.db, web.tenant_id)
    client = web.sign_in(owner)
    client.get(f"/api/tenants/{web.tenant_id}/interactions")
    assert rows(web.db, web.tenant_id) == []
    # Positive control: an ordinary read from the same client is recorded.
    client.get(f"/api/tenants/{web.tenant_id}/items")
    assert len(rows(web.db, web.tenant_id)) == 1


def test_a_request_refused_at_company_admission_is_recorded_nowhere(web):
    elsewhere = create_tenant(web.db, f"Elsewhere {uid('co')}")
    web.db.commit()
    stranger = member(web.db, elsewhere.id)
    response = web.sign_in(stranger).get(f"/api/tenants/{web.tenant_id}/items")
    assert response.status_code in {403, 404}
    assert rows(web.db, web.tenant_id) == []
    assert rows(web.db, elsewhere.id) == []


def test_a_refused_web_request_records_its_status_without_values(web):
    owner = member(web.db, web.tenant_id)
    response = web.sign_in(owner).get(
        f"/api/tenants/{web.tenant_id}/items/itm_no_such_item_secret"
    )
    assert response.status_code == 404
    [row] = rows(web.db, web.tenant_id)
    assert (row.outcome, row.error_code) == ("refused", "http_404")
    assert row.operation == "GET /items/{record_id}"


async def _call_mcp(session, monkeypatch, token, tool, arguments):
    monkeypatch.setattr(mcp_module, "Session", lambda: session)
    access = AccessToken(
        token="test",
        client_id=token.id,
        scopes=["reality:read", "reality:tool:*"],
        subject=token.tenant_id,
    )
    context = auth_context_var.set(AuthenticatedUser(access))
    try:
        return await mcp_module.build_server().call_tool(tool, arguments)
    finally:
        auth_context_var.reset(context)


@pytest.mark.anyio
async def test_an_mcp_call_is_attributed_to_its_token(
    session,
    business,
    monkeypatch,
    recording,  # noqa: F811
):
    token, _secret = create_mcp_access_token(
        session, business.tenant.id, "Claude Desktop"
    )
    session.commit()
    await _call_mcp(
        session,
        monkeypatch,
        token,
        "business_records_discover",
        {"family": "item", "limit": 3},
    )
    [row] = rows(session, business.tenant.id)
    assert (row.channel, row.operation, row.mcp_token_id) == (
        "mcp",
        "business_records_discover",
        token.id,
    )
    assert row.summary.get("arguments") == ["family", "limit"]
    assert row.summary.get("choices") == {"family": "item"}


def test_a_chat_tool_call_is_recorded_and_a_refusal_keeps_its_code(
    session,
    business,
    recording,  # noqa: F811
):
    tenant = business.tenant.id
    _, refused = mcp_chat._call_tool(
        session,
        tenant,
        "business_records_discover",
        {"family": "item", "limit": 2},
        ("read",),
    )
    assert refused is False
    _result, refused = mcp_chat._call_tool(
        session,
        tenant,
        "business_records_discover",
        {"family": "no-such-family"},
        ("read",),
    )
    assert refused is True
    recorded = rows(session, tenant)
    assert [(row.channel, row.outcome) for row in recorded] == [
        ("chat", "ok"),
        ("chat", "refused"),
    ]
    assert recorded[1].error_code


def test_a_cli_command_names_its_subcommands_but_never_its_values():
    assert _command_path(["party", "create", "--name", "Müller GmbH"]) == (
        "reality party create"
    )
    assert _command_path(["--help"]) == "reality"


def test_a_cli_command_learns_its_company_from_the_first_tool_call(
    session,
    business,
    recording,  # noqa: F811
):
    observation, token = interactions.begin(None, "cli", "reality inventory")
    with interactions.tool_boundary(business.tenant.id, "inventory.read"):
        pass
    interactions.end(observation, token)
    [row] = rows(session, business.tenant.id)
    assert (row.channel, row.operation) == ("cli", "reality inventory")


def test_a_cli_command_that_touches_no_company_records_nothing(
    session,
    business,
    recording,  # noqa: F811
):
    observation, token = interactions.begin(None, "cli", "reality status")
    interactions.end(observation, token)
    assert session.scalars(select(Interaction)).all() == []


def test_a_worker_run_is_one_interaction_and_empty_sweeps_are_none(
    scheduled_database, monkeypatch
):
    from test_scheduled_worker import setup_due

    from reality.db.scheduled_jobs import ScheduledJobRun
    from reality.jobs.runtime import ProcessLoop

    # The child process inherits the switch.
    monkeypatch.setenv("REALITY_INTERACTIONS", "on")
    engine, factory, tenant, actor = scheduled_database
    worker = ProcessLoop("worker", tenant_id=tenant)
    scheduler = ProcessLoop("scheduler", tenant_id=tenant)
    assert worker.sweep(engine, max_runs=10, max_seconds=25)["processed"] == 0
    setup_due(factory, tenant, actor)
    assert scheduler.sweep(engine, max_runs=100, max_seconds=25)["materialized"] == 1
    with factory() as db:
        # An idle poll and a materializing sweep are not company interactions.
        assert rows(db, tenant) == []
    assert worker.sweep(engine, max_runs=10, max_seconds=25)["succeeded"] == 1
    with factory() as db:
        run_id = db.scalar(
            select(ScheduledJobRun.id).where(ScheduledJobRun.tenant_id == tenant)
        )
        [row] = rows(db, tenant)
        assert (row.channel, row.kind, row.operation, row.outcome) == (
            "worker",
            "job",
            "invitations.cleanup",
            "ok",
        )
        assert row.job_id == run_id


SENTINEL = "zz-sentinel-9f3c"


def _sentinel_arguments(schema):
    arguments = {}
    for name, spec in schema.get("properties", {}).items():
        kind = spec.get("type")
        if "enum" in spec:
            arguments[name] = spec["enum"][0]
        elif kind == "string" or (isinstance(kind, list) and "string" in kind):
            arguments[name] = f"{SENTINEL}-{name}"
        elif kind == "integer":
            arguments[name] = 1
        elif kind == "boolean":
            arguments[name] = False
    return arguments


def test_no_argument_value_reaches_any_row_across_the_read_catalog(web):
    from reality.mcp.catalog import MCP_TOOL_REGISTRY

    tenant = web.tenant_id
    factory = sessionmaker(web.db.get_bind(), expire_on_commit=False)
    read_tools = [
        definition
        for definition in MCP_TOOL_REGISTRY.values()
        if definition.access == "read"
    ]
    # Positive control: the catalog is the real one, not an empty stand-in.
    assert len(read_tools) > 50
    for definition in read_tools:
        with factory() as db:
            try:
                mcp_chat._call_tool(
                    db,
                    tenant,
                    definition.name,
                    _sentinel_arguments(definition.input_schema),
                    ("read",),
                )
            except Exception:  # noqa: BLE001, S110 - a crash is still an interaction
                pass
            db.rollback()
    recorded = rows(web.db, tenant)
    assert len(recorded) == len(read_tools)
    for row in recorded:
        values = repr(
            {c.name: getattr(row, c.name) for c in Interaction.__table__.columns}
        )
        assert SENTINEL not in values, row.operation
