from reality.agent.mcp_chat import _anthropic_tool_schemas
from reality.catalogs import load_application_catalog
from reality.mcp.catalog import model_tool_schemas
from reality.tools.application import TOOLS

COMMITMENT_PROPOSALS = {
    "commitment_revise_propose": ("revise_commitment", "commitment_revise"),
    "commitment_cancel_propose": ("cancel_commitment", "commitment_cancel"),
}


def test_chat_discovers_reviewed_commitment_actions_from_shared_registry():
    openai_schemas = {
        schema["function"]["name"]: schema["function"]
        for schema in model_tool_schemas(access=("read", "propose"))
    }
    anthropic_names = {schema["name"] for schema in _anthropic_tool_schemas()}
    coverage = load_application_catalog()["agent_command_coverage"]

    for proposal_tool, (service, application_tool) in COMMITMENT_PROPOSALS.items():
        assert proposal_tool in openai_schemas
        assert proposal_tool in anthropic_names
        assert coverage[service] == {
            "classification": "eligible",
            "tools": [proposal_tool],
        }
        assert TOOLS[application_tool].mutating is True


def test_chat_commitment_action_schemas_require_safe_review_inputs():
    schemas = {
        schema["function"]["name"]: schema["function"]["parameters"]
        for schema in model_tool_schemas(access=("propose",))
    }

    revision = schemas["commitment_revise_propose"]
    cancellation = schemas["commitment_cancel_propose"]
    assert revision["required"] == ["commitment_id"]
    assert revision["properties"]["retained_allocations"]["items"]["required"] == [
        "reservation_id",
        "quantity",
    ]
    assert cancellation["required"] == ["commitment_id", "reason"]
    assert revision["additionalProperties"] is False
    assert cancellation["additionalProperties"] is False
