from typer.testing import CliRunner

from reality.catalogs import runtime_application_catalog
from reality.cli.app import app, movement_app
from reality.mcp.catalog import MCP_TOOL_NAMES
from reality.tools.application import TOOLS


def test_supply_assignment_is_exposed_through_shared_tools_and_mcp():
    assert TOOLS["supply_assign"].mutating is True
    assert TOOLS["supply_coverage"].mutating is False
    assert {"supply_assign_propose", "supply_coverage"} <= MCP_TOOL_NAMES


def test_supply_assignment_cli_commands_are_discoverable():
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "supply-assign-propose" in result.stdout
    assert "supply-assign-confirm" in result.stdout
    assert "supply-coverage" in result.stdout
    assert "return-disposition-propose" in result.stdout
    assert "return-disposition-confirm" in result.stdout
    assert "return-disposition" in result.stdout


def test_movement_explanation_is_shared_and_cli_discoverable():
    assert TOOLS["movement_explanation"].mutating is False
    assert "movement_explanation" in MCP_TOOL_NAMES

    assert "explain" in {command.name for command in movement_app.registered_commands}


def test_movement_explanation_loads_in_the_runtime_catalog():
    catalog = runtime_application_catalog()
    entry = next(
        row
        for row in catalog["tool_catalog"]["entries"]
        if row["id"] == "mcp:movement_explanation"
    )
    assert entry["topic"] == "shipping"
