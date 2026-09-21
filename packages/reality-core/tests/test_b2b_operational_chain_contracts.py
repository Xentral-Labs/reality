from reality.cli.app import app
from reality.mcp.catalog import MCP_TOOL_NAMES
from reality.tools.application import TOOLS
from typer.testing import CliRunner


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
