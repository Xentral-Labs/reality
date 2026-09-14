"""Keep documented MCP modes aligned with the actual adapter dispatch."""

import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault(
    "REALITY_DATABASE_URL", "postgresql+psycopg://docs:docs@localhost/docs"
)

from reality.mcp.catalog import tool_definitions

spec = importlib.util.spec_from_file_location(
    "catalog_reference", Path(__file__).with_name("generate-catalog-reference.py")
)
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


class ReadExecutionReferenceTests(unittest.TestCase):
    def test_mcp_defaults_and_legacy_follow_documented_service_paths(self):
        for tool in tool_definitions(access=["read"]):
            if tool.name not in reference.MCP_PROJECTION_READS:
                continue
            modes = reference.tool_read_modes(tool)
            for arguments, expected in [
                ({}, "live"),
                ({"response_format": "page"}, "live"),
                ({"response_format": "legacy"}, "stored"),
            ]:
                with self.subTest(tool=tool.name, arguments=arguments):
                    with (
                        patch(
                            "reality.tools.application.projection_rows",
                            return_value="stored",
                        ) as stored,
                        patch(
                            "reality.services.read_contracts.operational_page",
                            return_value="live",
                        ) as live,
                    ):
                        self.assertEqual(
                            tool.handler(None, "tenant-doc-test", arguments), expected
                        )
                        called = live if expected == "live" else stored
                        self.assertEqual(called.call_args.args[1], "tenant-doc-test")
                        self.assertEqual(
                            called.call_args.args[2],
                            reference.MCP_PROJECTION_READS[tool.name],
                        )
                        (stored if expected == "live" else live).assert_not_called()
                    documented = (
                        next(mode for mode in modes if mode.get("default"))
                        if not arguments
                        else next(
                            mode
                            for mode in modes
                            if "response_format=" + arguments["response_format"]
                            in mode["query"]
                        )
                    )
                    self.assertEqual(documented["mode"], expected)
