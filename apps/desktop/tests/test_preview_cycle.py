"""Disposable test installs must preserve their source, including on failure."""

import importlib.util
import plistlib
from pathlib import Path

import pytest


def helper():
    path = Path(__file__).resolve().parents[1] / "scripts/test-preview.py"
    spec = importlib.util.spec_from_file_location("preview_cycle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source(tmp_path):
    app = tmp_path / "Source.app"
    (app / "Contents/MacOS").mkdir(parents=True)
    (app / "Contents/Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleIdentifier": "ai.runreality.local.preview",
                "CFBundleExecutable": "reality-local",
            }
        )
    )
    (app / "Contents/MacOS/reality-local").write_text("source")
    return app


def test_distinct_copies_and_cleanup(tmp_path):
    module = helper()
    app = source(tmp_path)
    with module.installation(app) as first:
        assert first != app
        (first / "Contents/MacOS/reality-local").write_text("changed")
        with module.installation(app) as second:
            assert first != second
            assert (second / "Contents/MacOS/reality-local").read_text() == "source"
    assert not first.parent.exists()
    assert not second.parent.exists()
    assert (app / "Contents/MacOS/reality-local").read_text() == "source"


def test_failure_cleans_install(tmp_path):
    with pytest.raises(RuntimeError), helper().installation(source(tmp_path)) as app:
        raise RuntimeError("simulated test failure")
    assert not app.parent.exists()


def test_reject_foreign_app(tmp_path):
    app = source(tmp_path)
    (app / "Contents/Info.plist").write_bytes(
        plistlib.dumps({"CFBundleIdentifier": "other"})
    )
    with pytest.raises(ValueError), helper().installation(app):
        pytest.fail("Must not launch unrelated app")


def test_partial_copy_is_removed(tmp_path, monkeypatch):
    module = helper()
    destinations = []

    def failed_copy(source, destination, **kwargs):
        destinations.append(destination)
        destination.mkdir()
        (destination / "partial").write_text("incomplete")
        raise OSError("simulated disk full")

    monkeypatch.setattr(module.shutil, "copytree", failed_copy)
    with pytest.raises(OSError), module.installation(source(tmp_path)):
        pytest.fail("Failed copy cannot launch")
    assert not destinations[0].parent.exists()
