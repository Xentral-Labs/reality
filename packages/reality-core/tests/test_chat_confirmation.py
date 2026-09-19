import json

from reality.agent.provider import DummyProvider
from reality.db.core import Party
from reality.services.core import (
    active_reserved,
    chat_messages,
    chat_suggestions,
    create_chat_session,
    create_commitment,
    create_tenant,
    record_movement,
    send_chat_message,
)
from reality.tools.application import confirm_tool, proposed_tools
from sqlalchemy import func, select


def test_dummy_provider_is_deterministic():
    provider = DummyProvider()
    assert provider.reply("inventory") == provider.reply("inventory")
    assert "confirmation" in provider.reply("reserve com_123").content.lower()


def test_unconfigured_ai_explains_how_to_enable_chat(session, business, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    chat = create_chat_session(session, business.tenant.id)

    _, answer = send_chat_message(
        session,
        business.tenant.id,
        chat.id,
        "Which customer orders are still open?",
    )

    assert answer.content == (
        "AI is not configured for this company. Add an Anthropic API key in "
        "AI configuration, then ask again."
    )
    assert "V0 local agent" not in answer.content


def test_chat_mutation_is_visible_as_proposal_before_confirmation(session, business):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        5,
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        5,
        "2026-09-03",
    )
    chat = create_chat_session(session, business.tenant.id)

    send_chat_message(session, business.tenant.id, chat.id, f"reserve {commitment.id}")

    proposals = proposed_tools(session, business.tenant.id)
    assert len(proposals) == 1
    assert active_reserved(session, business.tenant.id, business.item.id) == 0
    assert (
        "Prepared reservation proposal"
        in chat_messages(session, business.tenant.id, chat.id)[-1].content
    )

    confirm_tool(session, business.tenant.id, proposals[0].id, review_token=json.loads(proposals[0].input)["_delivery_review"]["token"], confirmed=True)
    assert active_reserved(session, business.tenant.id, business.item.id) == 5


def test_empty_tenant_demo_idea_uses_confirmation_and_shared_demo_service(session):
    tenant = create_tenant(session, "Chat Demo GmbH")
    chat = create_chat_session(session, tenant.id)

    ideas = chat_suggestions(session, tenant.id)
    assert ideas[0]["message"] == "start demo"
    send_chat_message(session, tenant.id, chat.id, ideas[0]["message"])
    proposal = proposed_tools(session, tenant.id)[0]
    assert proposal.type == "tool:demo_seed"
    assert (
        session.scalar(
            select(func.count()).select_from(Party).where(Party.tenant_id == tenant.id)
        )
        == 0
    )

    confirm_tool(session, tenant.id, proposal.id)

    assert (
        session.scalar(
            select(func.count()).select_from(Party).where(Party.tenant_id == tenant.id)
        )
        == 3
    )
    assert {idea["label"] for idea in chat_suggestions(session, tenant.id)} >= {
        "Explain inventory",
        "Show fulfillment risks",
        "Reserve available stock",
    }


def test_demo_library_read_ideas_have_supported_chat_answers(session, business):
    chat = create_chat_session(session, business.tenant.id)
    read_ideas = [
        idea
        for idea in chat_suggestions(session, business.tenant.id)
        if not idea["message"].startswith("reserve ") and not idea.get("disabled")
    ]

    for idea in read_ideas:
        _, answer = send_chat_message(
            session, business.tenant.id, chat.id, idea["message"]
        )
        assert "V0 local agent" not in answer.content
        assert answer.content.strip()


def test_normal_month_can_be_proposed_and_run_from_chat(session):
    tenant = create_tenant(session, "Chat Month GmbH")
    chat = create_chat_session(session, tenant.id)
    month_idea = next(
        idea
        for idea in chat_suggestions(session, tenant.id)
        if idea["message"] == "run normal month"
    )

    send_chat_message(session, tenant.id, chat.id, month_idea["message"])
    proposal = proposed_tools(session, tenant.id)[0]

    assert proposal.type == "tool:normal_month"
    assert (
        session.scalar(
            select(func.count()).select_from(Party).where(Party.tenant_id == tenant.id)
        )
        == 0
    )

    executed = confirm_tool(session, tenant.id, proposal.id)
    result = json.loads(executed.output)

    assert executed.status == "executed"
    assert result["physical"] == "6.0000"
    assert result["receivable"] == "870.0000"
    assert (
        session.scalar(
            select(func.count()).select_from(Party).where(Party.tenant_id == tenant.id)
        )
        == 6
    )
