from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("generate-product-advisor-knowledge.py")


def _generator():
    spec = importlib.util.spec_from_file_location("product_advisor_generator", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProductAdvisorReferenceTest(unittest.TestCase):
    def test_generation_is_deterministic_and_references_are_valid(self) -> None:
        generator = _generator()

        first = generator.build_knowledge()
        second = generator.build_knowledge()

        self.assertEqual(first, second)
        source_ids = {source.id for source in first.sources}
        self.assertEqual(len(source_ids), len(first.sources))
        self.assertEqual(len({unit.id for unit in first.evidence}), len(first.evidence))
        self.assertTrue(all(unit.source_id in source_ids for unit in first.evidence))

        first_map = generator.build_capability_map(first)
        second_map = generator.build_capability_map(second)
        self.assertEqual(first_map, second_map)
        self.assertLessEqual(len(first_map.capabilities), 60)
        evidence_ids = {unit.id for unit in first.evidence}
        command_names = {
            unit.references[0]
            for unit in first.evidence
            if unit.id.startswith("evidence_command_")
        }
        for capability in first_map.capabilities:
            self.assertTrue(set(capability.evidence_ids) <= evidence_ids)
            self.assertTrue({tool.name for tool in capability.tools} <= command_names)
            self.assertTrue(
                all(tool.mode in {"read", "query", "mutation"} for tool in capability.tools)
            )
            self.assertFalse(hasattr(capability, "arguments"))

    def test_checked_in_output_is_current_and_public_safe(self) -> None:
        generator = _generator()

        expected = generator.build_knowledge().public_payload()
        actual = json.loads(generator.TARGET.read_text(encoding="utf-8"))
        expected_map = generator.build_capability_map(
            generator.build_knowledge()
        ).model_dump(mode="json")
        actual_map = json.loads(
            generator.CAPABILITY_TARGET.read_text(encoding="utf-8")
        )
        rendered = json.dumps(actual)

        self.assertEqual(actual, expected)
        self.assertEqual(actual_map, expected_map)
        self.assertNotIn("internal_evidence", rendered)
        self.assertNotIn("specs/", rendered)
        self.assertNotIn("tests/", rendered)
        self.assertNotIn("packages/", rendered)

    def test_missing_allowlisted_document_fails_generation(self) -> None:
        generator = _generator()

        with self.assertRaisesRegex(ValueError, "does not exist"):
            generator._document_evidence(
                {
                    "documents": [
                        {
                            "id": "missing",
                            "path": "docs/does-not-exist.md",
                            "title": "Missing",
                            "authority": "explanation",
                            "public_url": "https://docs.runreality.ai/missing",
                        }
                    ]
                }
            )


if __name__ == "__main__":
    unittest.main()
