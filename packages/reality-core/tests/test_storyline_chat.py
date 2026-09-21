"""Spec 195: real chat replies retain exact, owner-scoped call evidence."""

import pytest
from conftest import record_by_id, seed_company
from sqlalchemy import delete, func, select

from reality.db.core import ChatMessage, StorylineTraceEntry
from reality.services import core, storyline
from reality.storyline import recorder
from reality.tools.application import run_read_tool
from tests.test_storyline_library_api import http as storyline_http
from tests.test_storyline_library_api import start


@pytest.fixture
def http(session, monkeypatch, company_setup_login):
    yield from storyline_http.__wrapped__(session, monkeypatch, company_setup_login)


def test_real_chat_evidence_survives_reload_and_excludes_other_calls(
    http, session, monkeypatch
):
    from reality.agent import mcp_chat

    client, actor = http
    tenant = start(client)["tenant_id"]
    conversation = core.create_chat_session(session, tenant)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-no-network")

    async def provider(**kwargs):
        run_read_tool(kwargs["session"], kwargs["tenant_id"], "exceptions", {})
        return "Checked the recorded findings."

    monkeypatch.setattr(mcp_chat, "reply_via_anthropic_tools", provider)
    _, reply = core.send_chat_message(
        session, tenant, conversation.id, "What is open?", actor_user_id=actor.id
    )
    run_read_tool(session, tenant, "exceptions", {})
    _, other = core.send_chat_message(
        session, tenant, conversation.id, "Check again", actor_user_id=actor.id
    )
    first = client.get(f"/api/tenants/{tenant}/storyline/chat/{reply.id}")
    assert first.status_code == 200, first.text
    evidence = first.json()
    assert evidence["available"] and not evidence["has_more"]
    assert [item["name"] for item in evidence["items"]] == ["exceptions"]
    second = storyline.chat_evidence(session, actor.id, tenant, other.id)
    assert {item["id"] for item in evidence["items"]}.isdisjoint(
        item["id"] for item in second["items"]
    )
    assert not any(
        item["name"] == "chat.reply"
        for item in storyline.trace(session, actor.id, tenant, free=True)["items"]
    )
    session.expire_all()
    assert (
        storyline.chat_evidence(session, actor.id, tenant, reply.id)["items"][0]["id"]
        == evidence["items"][0]["id"]
    )
    session.execute(
        delete(StorylineTraceEntry).where(
            StorylineTraceEntry.id == evidence["items"][0]["id"]
        )
    )
    session.commit()
    assert storyline.chat_evidence(session, actor.id, tenant, reply.id)["has_more"]


def test_old_and_foreign_messages_do_not_gain_evidence(http, session):
    client, actor = http
    tenant = start(client)["tenant_id"]
    chat = core.create_chat_session(session, tenant)
    user = ChatMessage(
        id="old-user",
        tenant_id=tenant,
        session_id=chat.id,
        role="user",
        content="Hello",
    )
    reply = ChatMessage(
        id="old-answer",
        tenant_id=tenant,
        session_id=chat.id,
        role="assistant",
        content="Old reply",
    )
    session.add_all([user, reply])
    session.commit()
    assert storyline.chat_evidence(session, actor.id, tenant, reply.id) == {
        "available": False,
        "items": [],
        "has_more": False,
    }
    for message in [user.id, "unknown"]:
        assert (
            client.get(f"/api/tenants/{tenant}/storyline/chat/{message}").status_code
            == 404
        )
    # A different valid company is created through the normal setup service.
    from reality.services import company_setup

    other = company_setup.create_company(
        session, actor.id, "other", "Other", "sandbox", "empty", confirmed=True
    )["tenant_id"]
    foreign = core.create_chat_session(session, other)
    foreign_reply = ChatMessage(
        id="foreign",
        tenant_id=other,
        session_id=foreign.id,
        role="assistant",
        content="Private",
    )
    session.add(foreign_reply)
    session.commit()
    assert (
        client.get(f"/api/tenants/{tenant}/storyline/chat/foreign").status_code == 404
    )


def test_chat_collection_is_context_local_and_resets_on_error():
    from contextvars import Context

    with recorder.chat_call_scope("tenant") as outer:
        assert recorder.current_chat_calls() is outer
        assert Context().run(recorder.current_chat_calls) is None
        with pytest.raises(RuntimeError), recorder.chat_call_scope("tenant"):
            raise RuntimeError("provider failure")
        assert recorder.current_chat_calls() is outer
    assert recorder.current_chat_calls() is None


def test_proposed_change_is_not_execution_and_later_decision_is_linked(
    http, session, monkeypatch
):
    from reality.agent import mcp_chat
    from reality.db.core import Item
    from reality.mcp.catalog import dispatch_tool
    from reality.services.memberships import Principal
    from reality.tools.application import approve_and_execute_proposal

    client, actor = http
    tenant = start(client)["tenant_id"]
    chat = core.create_chat_session(session, tenant)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-no-network")
    proposals = []

    async def provider(**kwargs):
        proposed = dispatch_tool(
            session,
            tenant,
            "item_create_propose",
            {"records": [{"sku": "FREE-CHAT", "name": "Free chat item"}]},
            allowed_access=("propose",),
        )
        proposals.append(proposed["proposal_id"])
        return "Please review the proposed item."

    monkeypatch.setattr(mcp_chat, "reply_via_anthropic_tools", provider)
    _, reply = core.send_chat_message(
        session, tenant, chat.id, "Create an item", actor_user_id=actor.id
    )
    evidence = storyline.chat_evidence(session, actor.id, tenant, reply.id)
    assert [row["kind"] for row in evidence["items"]] == ["propose"]
    assert (
        session.scalar(
            select(Item).where(Item.tenant_id == tenant, Item.sku == "FREE-CHAT")
        )
        is None
    )
    approve_and_execute_proposal(
        session,
        tenant,
        proposals[0],
        confirmed=True,
        confirming_principal=Principal(actor.id),
    )
    evidence = storyline.chat_evidence(session, actor.id, tenant, reply.id)
    assert [row["kind"] for row in evidence["items"]] == ["propose", "confirm"]
    assert (
        session.scalar(
            select(Item).where(Item.tenant_id == tenant, Item.sku == "FREE-CHAT")
        )
        is not None
    )
    assert evidence["items"][1]["marker"] is not None
    with pytest.raises(core.NotFound):
        storyline.chat_evidence(session, "another-owner", tenant, reply.id)


def test_trace_failure_does_not_repeat_a_saved_reply(http, session, monkeypatch):
    client, actor = http
    tenant = start(client)["tenant_id"]
    conversation = core.create_chat_session(session, tenant)
    original = recorder.record

    def failed_association(*args, **kwargs):
        if kwargs["name"] == "chat.reply":
            raise RuntimeError("Trace unavailable")
        return original(*args, **kwargs)

    monkeypatch.setattr(recorder, "record", failed_association)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _, reply = core.send_chat_message(
        session, tenant, conversation.id, "source evidence", actor_user_id=actor.id
    )
    assert record_by_id(session, ChatMessage, reply.id) is not None
    assert not storyline.chat_evidence(session, actor.id, tenant, reply.id)["available"]
    assert recorder.current_chat_calls() is None


def test_standalone_free_play_is_confirmed_idempotent_and_has_no_story(http, session):
    from reality.db.core import PlaygroundRun

    client, _actor = http
    path = "/api/storyline/free-play"
    before = session.scalar(select(func.count(PlaygroundRun.id)))
    assert client.get(path).json() == {"available": False}
    assert client.post(path, json={"confirmed": False}).status_code == 422
    assert session.scalar(select(func.count(PlaygroundRun.id))) == before
    created = client.post(path, json={"confirmed": True})
    assert created.status_code == 200, created.text
    result = created.json()
    # Feature 199: the request answers with the committed company; the worker seeds it.
    assert result["status"] == "initializing" and result["environment"] == "sandbox"
    assert seed_company(session, result["tenant_id"]) == "succeeded"
    assert client.get(path).json()["status"] == "ready"
    run = record_by_id(session, PlaygroundRun, result["run_id"])
    assert run.storyline_key is None and run.storyline_version is None
    assert (
        client.post(path, json={"confirmed": True}).json()["tenant_id"]
        == result["tenant_id"]
    )
    assert client.get(path).json()["tenant_id"] == result["tenant_id"]
    assert (
        client.get(f"/api/tenants/{result['tenant_id']}/storyline").status_code == 404
    )
    with pytest.raises(core.NotFound):
        storyline._evidence_run(session, "wrong-owner", result["tenant_id"])


def test_standalone_free_play_records_real_chat_and_preserves_archive(
    http, session, monkeypatch
):
    from reality.agent import mcp_chat
    from reality.db.core import PlaygroundRun
    from reality.services import playground

    client, actor = http
    result = client.post("/api/storyline/free-play", json={"confirmed": True}).json()
    tenant = result["tenant_id"]
    assert seed_company(session, tenant) == "succeeded"
    chat = core.create_chat_session(session, tenant)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-no-network")

    async def provider(**kwargs):
        run_read_tool(session, tenant, "exceptions", {})
        return "Read the Sandbox findings."

    monkeypatch.setattr(mcp_chat, "reply_via_anthropic_tools", provider)
    _, reply = core.send_chat_message(
        session, tenant, chat.id, "What is open?", actor_user_id=actor.id
    )
    assert (
        storyline.chat_evidence(session, actor.id, tenant, reply.id)["items"][0]["name"]
        == "exceptions"
    )
    assert storyline.trace(session, actor.id, tenant, free=True)["items"]
    playground.archive_run(session, actor.id, result["run_id"], confirmed=True)
    repeated = client.post("/api/storyline/free-play", json={"confirmed": True})
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["status"] == "archived"
    assert record_by_id(session, PlaygroundRun, result["run_id"]).status == "archived"


def test_free_play_never_opens_an_ordinary_company_with_a_conflicting_key(
    http, session
):
    from reality.services.company_setup import create_company

    client, actor = http
    result = create_company(
        session,
        actor.id,
        recorder.FREE_PLAY_REQUEST_KEY,
        "Ordinary company",
        "business",
        "empty",
        confirmed=True,
    )
    response = client.get("/api/storyline/free-play")
    assert response.status_code == 409, response.text
    with pytest.raises(core.NotFound):
        storyline._evidence_run(session, actor.id, result["tenant_id"])
