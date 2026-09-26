"""Release manifests are stable, complete and content-addressed."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/release-manifest.py"


@pytest.fixture
def release_manifest():
    spec = importlib.util.spec_from_file_location("desktop_release_manifest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_manifest_is_sorted_stable_and_detects_changed_bytes(
    release_manifest, tmp_path
):
    root = tmp_path / "Reality Local.app"
    (root / "z").mkdir(parents=True)
    (root / "z/last").write_bytes(b"last")
    (root / "first").write_bytes(b"first")
    (root / "link").symlink_to("first")

    first = release_manifest.manifest(root, version="1.2.3", artifact="app")
    repeated = release_manifest.manifest(root, version="1.2.3", artifact="app")
    (root / "first").write_bytes(b"changed")
    changed = release_manifest.manifest(root, version="1.2.3", artifact="app")

    assert first == repeated
    assert [entry["path"] for entry in first["entries"]] == ["first", "link", "z/last"]
    assert first != changed
    assert first["format_version"] == 1
    assert release_manifest.differences(first, repeated) == []
    assert release_manifest.differences(first, changed) == ["first"]
