"""Prove interface explanations follow real catalog relationships."""

import importlib.util
import os
import unittest
from pathlib import Path

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

    def test_invalid_example_mapping_is_rejected(self):
        entries = [dict(row) for row in self.model["entries"]]
        action = next(row for row in entries if row["id"] == "action:reserve_stock")
        action["command"] = "missing_command"
        with self.assertRaisesRegex(ValueError, "reservation example"):
            reference.build_interface_guide(entries)


if __name__ == "__main__":
    unittest.main()
