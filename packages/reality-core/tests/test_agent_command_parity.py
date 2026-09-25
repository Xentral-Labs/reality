from reality.catalogs import CATALOG_READ_TOOLS, load_application_catalog
from reality.mcp.catalog import MCP_TOOL_CATALOG, MCP_TOOL_NAMES, model_tool_schemas
from reality.tools.application import TOOLS


def test_every_canonical_command_has_complete_agent_classification():
    catalog = load_application_catalog()
    command_services = {entry["service"] for entry in catalog["commands"]}
    coverage = catalog["agent_command_coverage"]

    assert set(coverage) == command_services
    assert all(
        entry["classification"] in {"eligible", "excluded", "blocked"}
        for entry in coverage.values()
    )
    assert all(
        entry.get("tools")
        for entry in coverage.values()
        if entry["classification"] == "eligible"
    )
    assert all(
        entry.get("reason")
        for entry in coverage.values()
        if entry["classification"] != "eligible"
    )
    assert all(entry["classification"] == "eligible" for entry in coverage.values())


def test_all_mapped_agent_tools_exist_and_chat_uses_same_schema_registry():
    catalog = load_application_catalog()
    mapped = {
        tool
        for entry in [
            *catalog["agent_command_coverage"].values(),
            *catalog["agent_additional_commands"].values(),
        ]
        for tool in entry.get("tools", [])
    }
    schemas = {schema["function"]["name"] for schema in model_tool_schemas()}

    assert mapped <= MCP_TOOL_NAMES
    assert mapped <= schemas | {"proposal_approve_and_execute"}


def test_every_public_schema_is_strict():
    for schema in model_tool_schemas(access=("read", "propose", "confirm")):
        parameters = schema["function"]["parameters"]
        assert parameters["type"] == "object"
        assert parameters["additionalProperties"] is False


def test_capability_description_is_a_shared_read_only_agent_tool():
    schemas = {
        schema["function"]["name"]: schema["function"]
        for schema in model_tool_schemas(access=("read",))
    }

    assert "capability_describe" in MCP_TOOL_NAMES
    assert schemas["capability_describe"]["parameters"]["required"] == ["tool_name"]


def test_read_guidance_maps_public_tools_to_non_mutating_application_tools():
    guidance = load_application_catalog()["capability_guidance"]
    read_guidance = {
        tool_name: entry
        for tool_name, entry in guidance.items()
        if entry["kind"] == "read"
    }

    assert read_guidance
    assert set(read_guidance) <= MCP_TOOL_NAMES
    assert all(
        not TOOLS[entry["application_tool"]].mutating
        for entry in read_guidance.values()
    )


def test_every_public_business_read_has_guidance():
    guidance = load_application_catalog()["capability_guidance"]
    public_business_reads = {
        tool.name
        for tool in MCP_TOOL_CATALOG
        if tool.access == "read" and tool.name not in CATALOG_READ_TOOLS
    }

    assert public_business_reads == {
        name for name, entry in guidance.items() if entry["kind"] == "read"
    }


def test_only_catalog_reads_are_exempt_from_guidance():
    """The exemption must not become a hole a business read can slip through.

    These two answer from the capability catalog, so they have no `data_basis` of
    real tables to declare. Every other read does, and must carry a guidance block.
    """
    assert CATALOG_READ_TOOLS == {"capability_describe", "capability_catalog"}
    assert CATALOG_READ_TOOLS <= MCP_TOOL_NAMES
    assert all(
        tool.access == "read"
        for tool in MCP_TOOL_CATALOG
        if tool.name in CATALOG_READ_TOOLS
    )
