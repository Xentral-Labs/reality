from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("ci_backend_changes.py")


def load_classifier():
    spec = importlib.util.spec_from_file_location("ci_backend_changes", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load CI backend path classifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BackendChangeClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.classifier = load_classifier()

    def test_frontend_and_feature_spec_do_not_require_backend(self) -> None:
        paths = ["apps/web/src/App.tsx", "specs/166-ci-quality-performance/spec.md"]
        self.assertFalse(self.classifier.requires_backend(paths))

    def test_backend_sources_and_tests_require_backend(self) -> None:
        for path in (
            "packages/reality-core/src/reality/services/core.py",
            "packages/reality-core/tests/test_postgresql_integration.py",
            "packages/reality-core/migrations/versions/0049_example.py",
        ):
            with self.subTest(path=path):
                self.assertTrue(self.classifier.requires_backend([path]))

    def test_backend_deployment_surfaces_require_backend(self) -> None:
        for path in (
            "apps/api/Dockerfile",
            "apps/mcp/Dockerfile",
            "apps/scheduler/main.py",
            "apps/worker/main.py",
            "compose.yml",
            "compose.dev.yml",
        ):
            with self.subTest(path=path):
                self.assertTrue(self.classifier.requires_backend([path]))

    def test_classifier_and_quality_workflow_require_backend(self) -> None:
        for path in (
            "scripts/ci_backend_changes.py",
            "scripts/ci_backend_test_shard.py",
            ".github/workflows/quality.yml",
        ):
            with self.subTest(path=path):
                self.assertTrue(self.classifier.requires_backend([path]))

    def test_empty_or_malformed_input_fails_safe(self) -> None:
        self.assertTrue(self.classifier.requires_backend([]))
        self.assertTrue(self.classifier.requires_backend(["", "/absolute/path"]))


if __name__ == "__main__":
    unittest.main()
