"""Exercise deployment source selection without contacting Railway."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("deploy_railway_demo.sh")
PRODUCT = ["api", "scheduler", "worker", "mcp", "docs", "app"]


class RailwayRepositorySplitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.product = self.root / "product checkout"
        self.site = self.root / "site checkout"
        for root in [self.product, self.site]:
            root.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "--allow-empty",
                    "-qm",
                    "fixture",
                ],
                check=True,
            )
        (self.product / "scripts").mkdir()
        self.script = self.product / "scripts/deploy_railway_demo.sh"
        self.script.write_text(SCRIPT.read_text())
        for app in ["api", "scheduler", "worker", "mcp", "docs", "web"]:
            path = self.product / f"apps/{app}/Dockerfile"
            path.parent.mkdir(parents=True)
            path.touch()
        path = self.site / "apps/site/Dockerfile.railway"
        path.parent.mkdir(parents=True)
        path.touch()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls"
        railway = self.bin / "railway"
        railway.write_text(
            '#!/usr/bin/env python3\nimport os,sys,json\nwith open(os.environ["CALL_LOG"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\nif sys.argv[1]=="logs": print(\'event="scheduler_sweep" event="worker_sweep"\')\n'
        )
        railway.chmod(0o755)
        curl = self.bin / "curl"
        curl.write_text("#!/bin/sh\nexit 0\n")
        curl.chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "CALL_LOG": str(self.log),
            "RAILWAY_TOKEN": "test-only",
            "REALITY_RAILWAY_PROJECT_ID": "test-project",
            "SITE_URL": "https://site.example.com",
            "APP_URL": "https://app.example.com",
            "DOCS_URL": "https://docs.example.com",
            "MCP_URL": "https://mcp.example.com",
            "REALITY_RAILWAY_SITE_ROOT": str(self.site),
        }

    def run_script(self, *args):
        return subprocess.run(
            ["bash", str(self.script), *args],
            check=False,
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def calls(self):
        import json

        return (
            [json.loads(line) for line in self.log.read_text().splitlines()]
            if self.log.exists()
            else []
        )

    def test_default_uploads_product_root_from_unrelated_directory(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        uploads = [c for c in self.calls() if c[0] == "up"]
        self.assertEqual([c[c.index("--service") + 1] for c in uploads], PRODUCT)
        for call in uploads:
            self.assertIn(str(self.product), call)
            self.assertIn("--path-as-root", call)

    def test_site_only_uses_separate_checkout(self):
        result = self.run_script("--only", "site")
        self.assertEqual(result.returncode, 0, result.stderr)
        uploads = [c for c in self.calls() if c[0] == "up"]
        self.assertEqual(len(uploads), 1)
        self.assertIn(str(self.site), uploads[0])
        self.assertEqual(uploads[0][uploads[0].index("--service") + 1], "site")

    def test_combined_preflight_fails_before_any_upload(self):
        self.env.pop("REALITY_RAILWAY_SITE_ROOT")
        result = self.run_script("--only", "all")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])
        self.assertIn("REALITY_RAILWAY_SITE_ROOT", result.stderr)

    def test_dry_run_has_no_external_calls_and_lists_both_sources(self):
        self.env.pop("RAILWAY_TOKEN")
        result = self.run_script("--only", "all", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(self.site), result.stdout)
        self.assertIn(str(self.product), result.stdout)
        self.assertIn("apps/site/Dockerfile.railway", result.stdout)
        self.assertEqual(self.calls(), [])

    def test_missing_product_dockerfile_fails_before_upload(self):
        (self.product / "apps/worker/Dockerfile").unlink()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])

    def test_combined_routes_site_and_preserves_app_last(self):
        result = self.run_script("--only", "all")
        self.assertEqual(result.returncode, 0, result.stderr)
        uploads = [c for c in self.calls() if c[0] == "up"]
        self.assertEqual(
            [c[c.index("--service") + 1] for c in uploads],
            PRODUCT[:-1] + ["site", "app"],
        )
        self.assertIn(str(self.site), uploads[-2])
        self.assertIn(str(self.product), uploads[-1])

    def test_site_only_does_not_require_product_health_urls(self):
        for key in ["APP_URL", "DOCS_URL", "MCP_URL"]:
            self.env.pop(key)
        result = self.run_script("--only", "site")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_mode_fails(self):
        self.assertNotEqual(self.run_script("--only", "everything").returncode, 0)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
