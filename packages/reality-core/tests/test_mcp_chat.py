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


def test_ordinary_chat_receives_decision_tools_and_decision_first_guidance():
    openai_names = {
        schema["function"]["name"]
        for schema in model_tool_schemas(access=("read", "propose", "confirm"))
    }
    anthropic_names = {
        schema["name"]
        for schema in _anthropic_tool_schemas(("read", "propose", "confirm"))
    }

    assert {"proposal_approve_and_execute", "proposal_reject"} <= openai_names
    assert {"proposal_approve_and_execute", "proposal_reject"} <= anthropic_names
    assert "person or agent" in SYSTEM_PROMPT
    assert "separate confirmation tool call" in SYSTEM_PROMPT
