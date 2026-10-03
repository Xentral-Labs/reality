"""Prove interface explanations follow real catalog relationships."""

import importlib.util
import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault(
    "REALITY_DATABASE_URL", "postgresql+psycopg://docs:docs@localhost/docs"
)

spec = importlib.util.spec_from_file_location(
    "interface_reference", Path(__file__).with_name("generate-catalog-reference.py")
)
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


class InterfaceGuideReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = reference.build_model()
        cls.entries = {row["id"]: row for row in cls.model["entries"]}

    def test_example_uses_actual_mapping_and_proposal_access(self):
        example = self.model["interface_guide"]["example"]
        action = self.entries[example["action"]]
        command = self.entries[example["command"]]
        tool = self.entries[example["tool"]]
        self.assertEqual(action["command"], command["key"])
        self.assertEqual(tool["command"], command["key"])
        self.assertEqual(tool["access"], "propose")
        self.assertIn(tool["key"], command["tools"])
        quantity = next(p for p in tool["parameters"] if p["name"] == "quantity")
        self.assertFalse(quantity["required"])

    def test_read_example_uses_actual_view_and_tool_projection_links(self):
        example = self.model["interface_guide"]["read_example"]
        view, projection, tool = [self.entries[key] for key in example["entries"]]
        self.assertEqual(view["projection"], projection["key"])
        self.assertIn(projection["key"], tool["projections"])
        for locale in ("en", "de"):
            renderer = reference.Renderer(self.model, "de" if locale == "de" else "")
            for page in (renderer.commands_page(), renderer.views_page()):
                self.assertIn(example["title"][locale], page)
                self.assertIn(example["description"][locale], page)

    def test_manuals_reuse_guide_in_both_languages(self):
        guide = self.model["interface_guide"]
        for locale in ("en", "de"):
            renderer = reference.Renderer(self.model, "de" if locale == "de" else "")
            for page in (renderer.commands_page(), renderer.views_page()):
                for definition in guide["kinds"].values():
                    self.assertIn(definition["label"][locale], page)
                    self.assertIn(definition["description"][locale], page)
                self.assertIn(guide["counts_note"][locale], page)
                for kind in ("action", "tool", "command"):
                    self.assertIn(renderer.named_ref(guide["example"][kind]), page)

    def test_first_extension_reuses_inventory_schema_and_read_handler(self):
        from reality.mcp import catalog

        root = Path(__file__).resolve().parents[3]
        expressions = []
        for locale in ("", "de"):
            page = (
                root / "apps/docs/content" / locale / "development/first-extension.md"
            )
            snippets = re.findall(r"```python\n(.*?)\n```", page.read_text(), re.DOTALL)
            compile(snippets[0], str(page), "exec")
            expression = snippets[1].strip().removesuffix(",")
            expressions.append(expression)
            # The source is the repository-owned tutorial, not external input.
            definition = eval(compile(expression, str(page), "eval"), vars(catalog))
            self.assertEqual(definition.name, "training_inventory_read")
            self.assertEqual(definition.access, "read")
            self.assertEqual(
                definition.input_schema,
                catalog.MCP_TOOL_REGISTRY["inventory_read"].input_schema,
            )
            arguments = {"view": "location", "item_id": "opaque-item-id"}
            with patch.object(
                catalog, "run_read_tool", return_value={"records": []}
            ) as read:
                result = definition.handler(None, "opaque-tenant-id", arguments)
            read.assert_called_once_with(
                None,
                "opaque-tenant-id",
                "inventory",
                {"response_format": "page", **arguments},
            )
            self.assertEqual(result, {"records": []})
            self.assertNotIn("training_inventory_read", catalog.MCP_TOOL_REGISTRY)
        self.assertEqual(expressions[0], expressions[1])

    def test_invalid_example_mapping_is_rejected(self):
        entries = [dict(row) for row in self.model["entries"]]
        action = next(row for row in entries if row["id"] == "action:reserve_stock")
        action["command"] = "missing_command"
        with self.assertRaisesRegex(ValueError, "reservation example"):
            reference.build_interface_guide(entries)


if __name__ == "__main__":
    unittest.main()
