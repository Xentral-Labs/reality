from __future__ import annotations

import unittest
from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "quality.yml"


class QualityWorkflowContractTests(unittest.TestCase):
    def test_postgresql_step_has_one_environment_block(self) -> None:
        workflow = WORKFLOW.read_text()
        step = workflow.split("- name: PostgreSQL test suite", 1)[1].split("\n\n", 1)[0]
        self.assertEqual(step.count("\n        env:"), 1)
        self.assertIn("TEST_POSTGRES_ADMIN_URL:", step)
        self.assertIn("REALITY_AUTH_MODE:", step)
        self.assertIn("SHARD:", step)

    def test_required_backend_check_aggregates_test_shards(self) -> None:
        workflow = WORKFLOW.read_text()
        aggregate = workflow.split("\n  backend-quality:", 1)[1].split("\n  frontend-quality:", 1)[0]
        self.assertIn("needs: [backend-changes, backend-tests]", aggregate)
        self.assertIn("if: always()", aggregate)
        self.assertIn('elif [ "$TEST_RESULT" != "success" ]', aggregate)


if __name__ == "__main__":
    unittest.main()
