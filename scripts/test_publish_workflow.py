"""The publish workflow ships exactly what the installer expects (spec 187 FR-001)."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / ".github" / "workflows" / "publish.yml"
INSTALLER_CI = ROOT / ".github" / "workflows" / "installer.yml"
INSTALL_SH = ROOT / "installer" / "install.sh"

PUBLISHED_ROLES = ["api", "mcp", "web", "scheduler", "worker"]


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class PublishWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = load(PUBLISH)
        self.jobs = self.workflow["jobs"]

    def test_triggers_on_main_and_release_tags(self) -> None:
        on = self.workflow[True] if True in self.workflow else self.workflow["on"]
        self.assertEqual(on["push"]["branches"], ["main"])
        self.assertEqual(on["push"]["tags"], ["v*"])

    def test_builds_the_five_runtime_images_for_both_architectures(self) -> None:
        build = self.jobs["images"]
        components = [entry["component"] for entry in build["strategy"]["matrix"]["include"]]
        self.assertEqual(components, PUBLISHED_ROLES)
        for entry in build["strategy"]["matrix"]["include"]:
            self.assertEqual(entry["dockerfile"], f"apps/{entry['component']}/Dockerfile")
        push_step = next(s for s in build["steps"] if s.get("uses", "").startswith("docker/build-push-action"))
        self.assertEqual(push_step["with"]["platforms"], "linux/amd64,linux/arm64")
        self.assertIn("REALITY_VERSION=", push_step["with"]["build-args"])
        self.assertIn("REALITY_COMMIT=", push_step["with"]["build-args"])
        self.assertEqual(build["permissions"]["packages"], "write")

    def test_images_are_named_the_way_the_compose_file_expects(self) -> None:
        meta_step = next(
            s for s in self.jobs["images"]["steps"] if s.get("uses", "").startswith("docker/metadata-action")
        )
        self.assertEqual(
            meta_step["with"]["images"].strip(),
            "ghcr.io/xentral-labs/reality-${{ matrix.component }}",
        )
        tags = meta_step["with"]["tags"]
        # Release tags: the bare version plus latest. Main: sha-<short> plus edge.
        self.assertIn("type=semver,pattern={{version}}", tags)
        self.assertIn("type=raw,value=latest,enable=${{ startsWith(github.ref, 'refs/tags/v') }}", tags)
        self.assertIn("type=sha,prefix=sha-", tags)
        self.assertIn("type=raw,value=edge,enable={{is_default_branch}}", tags)

    def test_release_job_ships_the_installer_assets_with_the_version_substituted(self) -> None:
        release = self.jobs["release"]
        self.assertEqual(release["if"], "startsWith(github.ref, 'refs/tags/v')")
        self.assertEqual(release["needs"], ["images"])
        script = "\n".join(step.get("run", "") for step in release["steps"])
        self.assertIn("__REALITY_INSTALLER_VERSION__", script)
        shipped = INSTALL_SH.read_text(encoding="utf-8").split('ASSETS="', 1)[1].split('"', 1)[0].split()
        for asset in [*shipped, "install.sh", ".env.example"]:
            self.assertIn(f"installer/{asset}", script, asset)
        # GitHub renames dot-files among release assets, so the example ships as env.example.
        self.assertIn("dist/env.example", script)
        self.assertIn("dist/env.example", release["steps"][-1]["with"]["files"])


class InstallerWorkflowTest(unittest.TestCase):
    def test_installer_ci_runs_shellcheck_dry_run_tests_and_the_end_to_end_proof(self) -> None:
        workflow = load(INSTALLER_CI)
        runs = "\n".join(
            step.get("run", "") for job in workflow["jobs"].values() for step in job["steps"]
        )
        self.assertIn("shellcheck", runs)
        self.assertIn("installer/tests", runs)
        self.assertIn("installer/tests/e2e.sh", runs)


if __name__ == "__main__":
    unittest.main()
