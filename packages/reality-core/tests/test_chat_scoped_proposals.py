"""A chat shows the proposals its own turns created, where they were made (spec 328)."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import ChangeProposal, ChatSession
from reality.services.core import (
    NotFound,
    archive_chat_session,
    chat_messages,
    chat_proposals,
    create_chat_session,
    create_tenant,
    pending_proposals_elsewhere,
    proposal_anchor,
    remove_chat_session,
    send_chat_message,
)
from reality.tools.application import (
    CHAT_SESSION,
    propose_tool,
    reject_proposal,
)
from reality.web import api as api_module
from reality.web import app as web_module

app = web_module.app


@pytest.fixture(autouse=True)
def local_provider(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def _api_client(session):
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def override_session():
        with factory() as api_session:
            yield api_session

    app.dependency_overrides[api_module.database_session] = override_session
    return TestClient(app)


def _propose_in_chat(session, tenant_id, chat_id):
    send_chat_message(session, tenant_id, chat_id, "run normal month")
    return session.scalars(
        select(ChangeProposal)
        .where(ChangeProposal.tenant_id == tenant_id)
        .order_by(ChangeProposal.created_at.desc())
    ).first()


def test_a_chat_turn_links_its_proposal_and_other_paths_do_not(session):
    tenant = create_tenant(session, "Chat link company")
    chat = create_chat_session(session, tenant.id)

    proposal = _propose_in_chat(session, tenant.id, chat.id)
    outside = propose_tool(session, tenant.id, "demo_seed", {})

    assert proposal.chat_session_id == chat.id
    assert outside.chat_session_id is None
    # The turn does not leave its conversation behind for the next caller.
    assert CHAT_SESSION.get() is None


def test_a_model_backed_turn_links_proposals_its_tools_create(session, monkeypatch):
    tenant = create_tenant(session, "Model chat company")
    chat = create_chat_session(session, tenant.id)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        "reality.services.free_playground.reserve_managed_question",
        lambda *args, **kwargs: None,
    )
    created = []

    async def fake_reply(*, session, tenant_id, **_):
        created.append(propose_tool(session, tenant_id, "normal_month", {}))
        return "Prepared it."

    monkeypatch.setattr("reality.agent.mcp_chat.reply_via_anthropic_tools", fake_reply)

    send_chat_message(session, tenant.id, chat.id, "Run the normal month please")

    assert [row.chat_session_id for row in created] == [chat.id]


def test_a_session_returns_only_its_own_proposals_in_every_state(session):
    tenant = create_tenant(session, "Scoped chat company")
    first = create_chat_session(session, tenant.id)
    second = create_chat_session(session, tenant.id)
    empty = create_chat_session(session, tenant.id)

    mine = _propose_in_chat(session, tenant.id, first.id)
    theirs = _propose_in_chat(session, tenant.id, second.id)
    legacy = propose_tool(session, tenant.id, "demo_seed", {})
    reject_proposal(session, tenant.id, mine.id)

    assert [row.id for row in chat_proposals(session, tenant.id, first.id)] == [mine.id]
    assert [row.id for row in chat_proposals(session, tenant.id, second.id)] == [
        theirs.id
    ]
    assert chat_proposals(session, tenant.id, empty.id) == []
    assert chat_proposals(session, tenant.id, first.id)[0].status == "rejected"
    # Pending elsewhere: the other chat's and the unlinked one, never your own.
    assert pending_proposals_elsewhere(session, tenant.id, first.id) == 2
    assert pending_proposals_elsewhere(session, tenant.id, second.id) == 1
    assert legacy.chat_session_id is None


def test_a_foreign_session_is_refused(session):
    tenant = create_tenant(session, "Own chat company")
    other = create_tenant(session, "Foreign chat company")
    chat = create_chat_session(session, other.id)

    with pytest.raises(NotFound):
        chat_proposals(session, tenant.id, chat.id)


def test_a_proposal_follows_the_answer_of_the_turn_that_made_it(session):
    tenant = create_tenant(session, "Placement company")
    chat = create_chat_session(session, tenant.id)

    send_chat_message(session, tenant.id, chat.id, "Explain Source Evidence Reality")
    proposal = _propose_in_chat(session, tenant.id, chat.id)
    send_chat_message(session, tenant.id, chat.id, "Explain Source Evidence Reality")

    messages = chat_messages(session, tenant.id, chat.id)
    roles = [row.role for row in messages]
    assert roles == ["user", "assistant"] * 3
    # The proposal's own question was sent before it was made.
    assert messages[2].created_at <= proposal.created_at <= messages[3].created_at
    assert proposal_anchor(messages, proposal) == messages[3].id


def test_the_last_turn_anchors_to_the_last_message_and_none_without_messages(session):
    tenant = create_tenant(session, "Anchor company")
    chat = create_chat_session(session, tenant.id)
    proposal = _propose_in_chat(session, tenant.id, chat.id)

    messages = chat_messages(session, tenant.id, chat.id)

    assert proposal_anchor(messages, proposal) == messages[-1].id
    assert proposal_anchor([], proposal) is None


def test_archived_sessions_keep_their_proposals_and_removal_never_deletes_them(session):
    tenant = create_tenant(session, "Archive chat company")
    chat = create_chat_session(session, tenant.id)
    proposal = _propose_in_chat(session, tenant.id, chat.id)

    archive_chat_session(session, tenant.id, chat.id)

    assert [row.id for row in chat_proposals(session, tenant.id, chat.id)] == [
        proposal.id
    ]
    session.refresh(proposal)
    assert proposal.status == "proposed"


def test_removing_a_session_that_holds_only_a_proposal_archives_it(session):
    tenant = create_tenant(session, "Failed turn company")
    chat = create_chat_session(session, tenant.id)
    token = CHAT_SESSION.set(chat.id)
    try:
        proposal = propose_tool(session, tenant.id, "demo_seed", {})
    finally:
        CHAT_SESSION.reset(token)

    remove_chat_session(session, tenant.id, chat.id)

    kept = session.get(ChatSession, (tenant.id, chat.id))
    assert kept is not None and kept.archived_at is not None
    session.refresh(proposal)
    assert proposal.chat_session_id == chat.id


def test_the_conversation_read_scopes_places_and_counts(session):
    tenant = create_tenant(session, "Payload chat company")
    client = _api_client(session)
    try:
        first = client.post(f"/api/tenants/{tenant.id}/copilot/sessions").json()["id"]
        second = client.post(f"/api/tenants/{tenant.id}/copilot/sessions").json()["id"]
        client.post(
            f"/api/tenants/{tenant.id}/copilot/sessions/{first}/messages",
            json={"message": "run normal month"},
        )
        outside = propose_tool(session, tenant.id, "demo_seed", {})

        own = client.get(
            f"/api/tenants/{tenant.id}/copilot", params={"session_id": first}
        ).json()
        other = client.get(
            f"/api/tenants/{tenant.id}/copilot", params={"session_id": second}
        ).json()

        assert [row["tool"] for row in own["proposals"]] == ["normal_month"]
        assert own["proposals"][0]["after_message_id"] == own["messages"][-1]["id"]
        assert own["pending_elsewhere"] == 1
        assert other["proposals"] == []
        assert other["pending_elsewhere"] == 2
        assert outside.id not in {row["id"] for row in own["proposals"]}

        proposal_id = own["proposals"][0]["id"]
        reject_proposal(session, tenant.id, proposal_id)
        settled = client.get(
            f"/api/tenants/{tenant.id}/copilot", params={"session_id": first}
        ).json()["proposals"]
        assert [(row["id"], row["status"]) for row in settled] == [
            (proposal_id, "rejected")
        ]
        assert settled[0]["decided_at"]
        assert json.dumps(settled[0]["decider"])

        client.delete(f"/api/tenants/{tenant.id}/copilot/sessions/{first}")
        archived = client.get(
            f"/api/tenants/{tenant.id}/copilot",
            params={"session_id": first, "archived": True},
        ).json()
        assert [row["id"] for row in archived["proposals"]] == [proposal_id]
    finally:
        app.dependency_overrides.clear()
