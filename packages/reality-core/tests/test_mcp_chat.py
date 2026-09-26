from reality.agent.mcp_chat import SYSTEM_PROMPT, _anthropic_tool_schemas
from reality.mcp.catalog import model_tool_schemas


def test_copilot_prompt_declares_manual_master_data_and_optional_source():
    prompt = SYSTEM_PROMPT.lower()
    assert "parties, items, and locations" in prompt
    assert "created manually" in prompt
    assert "source provenance is optional" in prompt
    assert "required" in prompt


def test_both_provider_adapters_receive_master_data_proposal_schemas():
    openai_names = {
        schema["function"]["name"]
        for schema in model_tool_schemas(access=("read", "propose"))
    }
    anthropic_names = {schema["name"] for schema in _anthropic_tool_schemas()}
    expected = {
        "party_create_propose",
        "item_create_propose",
        "location_create_propose",
    }
    assert expected <= openai_names
    assert expected <= anthropic_names


def test_ordinary_chat_prepares_but_does_not_receive_decision_tools():
    openai_names = {
        schema["function"]["name"]
        for schema in model_tool_schemas(access=("read", "propose"))
    }
    anthropic_names = {
        schema["name"]
        for schema in _anthropic_tool_schemas(("read", "propose"))
    }

    decision_tools = {"proposal_approve_and_execute", "proposal_reject"}
    assert decision_tools.isdisjoint(openai_names)
    assert decision_tools.isdisjoint(anthropic_names)
    prompt = " ".join(SYSTEM_PROMPT.lower().split())
    assert "human review" in prompt
    assert "no change has happened" in prompt
    assert "separate confirmation tool call" not in SYSTEM_PROMPT


def test_copilot_prompt_requires_readiness_first_for_prepayment_and_partial_shipment():
    prompt = " ".join(SYSTEM_PROMPT.lower().split())
    assert "prepayment" in prompt
    assert "partial shipment" in prompt
    assert "fulfillment readiness" in prompt
    assert "future requested delivery date" in prompt
    assert "fresh canonical read" in prompt
    assert "already links an invoice" in prompt
    assert "do not propose another invoice" in prompt


def test_both_provider_adapters_expose_readiness_invoice_and_shipment_proposals_only():
    openai_names = {
        schema["function"]["name"]
        for schema in model_tool_schemas(access=("read", "propose"))
    }
    anthropic_names = {
        schema["name"] for schema in _anthropic_tool_schemas(("read", "propose"))
    }
    required = {
        "fulfillment_readiness",
        "sales_invoice_record_propose",
        "shipment_dispatch_propose",
    }
    assert required <= openai_names
    assert required <= anthropic_names
    assert "proposal_approve_and_execute" not in openai_names | anthropic_names
