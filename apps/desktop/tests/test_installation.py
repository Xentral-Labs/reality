"""A released installation keeps its data until the owner erases it explicitly."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/installation.py"


@pytest.fixture
def installation():
    spec = importlib.util.spec_from_file_location("desktop_installation", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_identity_and_layout_survive_a_second_start(installation, tmp_path):
    first = installation.resolve(tmp_path)
    second = installation.resolve(tmp_path)
    assert first.identifier == second.identifier
    assert first.root == second.root
    assert first.created and not second.created
    assert first.root.is_dir()
    assert (tmp_path / "current").read_text().strip() == first.identifier
    recorded = json.loads((first.root / "installation.json").read_text())
    assert recorded["installation_id"] == first.identifier
    assert recorded["layout_version"] == installation.LAYOUT_VERSION


def test_identity_is_an_opaque_uuid_the_owner_bootstrap_accepts(installation, tmp_path):
    from uuid import UUID

    identifier = installation.resolve(tmp_path).identifier
    assert str(UUID(identifier)) == identifier


def test_private_directories_are_not_readable_by_other_accounts(installation, tmp_path):
    root = installation.resolve(tmp_path).root
    for directory in (root, root.parent, tmp_path, root / "data", root / "backups"):
        assert (directory.stat().st_mode & 0o077) == 0, directory


def test_second_start_of_the_same_installation_is_refused(installation, tmp_path):
    root = installation.resolve(tmp_path).root
    with (
        installation.exclusive(root),
        pytest.raises(installation.AlreadyRunning),
        installation.exclusive(root),
    ):
        pytest.fail("Two live processes must not share one installation")


def test_reopening_while_the_previous_process_stops_waits_briefly(
    installation, tmp_path
):
    import threading

    root = installation.resolve(tmp_path).root
    holder = installation.exclusive(root)
    holder.__enter__()
    threading.Timer(0.4, lambda: holder.__exit__(None, None, None)).start()
    with installation.exclusive(root, wait_seconds=10):
        pass


def test_waiting_still_ends_in_a_clear_refusal(installation, tmp_path):
    root = installation.resolve(tmp_path).root
    with (
        installation.exclusive(root),
        pytest.raises(installation.AlreadyRunning),
        installation.exclusive(root, wait_seconds=1),
    ):
        pytest.fail("A held installation must not be opened twice")


def test_lock_is_released_after_a_normal_stop(installation, tmp_path):
    root = installation.resolve(tmp_path).root
    with installation.exclusive(root):
        pass
    with installation.exclusive(root):
        pass


def test_socket_directory_stays_within_the_macos_path_limit(installation, tmp_path):
    with installation.private_socket_directory() as socket_directory:
        assert socket_directory.is_dir()
        assert (socket_directory.stat().st_mode & 0o077) == 0
        assert len(str(socket_directory / ".s.PGSQL.5432").encode()) < 104
    assert not socket_directory.exists()


def test_a_dead_postmaster_file_is_cleared_but_a_live_one_is_reported(
    installation, tmp_path
):
    data = tmp_path / "data"
    data.mkdir()
    marker = data / "postmaster.pid"
    marker.write_text("999999\n/somewhere\n")
    assert installation.stale_postmaster(data) is None
    assert not marker.exists()
    marker.write_text(f"{os.getpid()}\n/somewhere\n")
    assert installation.stale_postmaster(data) == os.getpid()
    assert marker.exists()


def test_checkpoints_keep_only_the_newest_three(installation, tmp_path):
    backups = tmp_path / "backups"
    backups.mkdir()
    for index in range(6):
        archive = backups / f"2026-01-0{index}T00-00-00.dump"
        archive.write_text(str(index))
        os.utime(archive, (index, index))
    installation.retain_checkpoints(backups, keep=3)
    remaining = sorted(item.name for item in backups.iterdir())
    assert remaining == [
        "2026-01-03T00-00-00.dump",
        "2026-01-04T00-00-00.dump",
        "2026-01-05T00-00-00.dump",
    ]


def test_erasure_removes_one_installation_and_leaves_its_sibling(
    installation, tmp_path
):
    first = installation.resolve(tmp_path)
    (first.root / "artifacts").mkdir(exist_ok=True)
    (first.root / "artifacts/evidence").write_text("business payload")
    second_identifier = installation.create(tmp_path).identifier
    installation.erase(tmp_path, first.identifier)
    assert not first.root.exists()
    assert (tmp_path / "installations" / second_identifier).is_dir()
    assert tmp_path.is_dir()


def test_erasure_is_refused_while_the_application_runs(installation, tmp_path):
    prepared = installation.resolve(tmp_path)
    with (
        installation.exclusive(prepared.root),
        pytest.raises(installation.AlreadyRunning),
    ):
        installation.erase(tmp_path, prepared.identifier)
    assert prepared.root.is_dir()


def test_erasure_refuses_a_directory_it_does_not_own(installation, tmp_path):
    foreign = tmp_path / "installations/not-ours"
    foreign.mkdir(parents=True)
    (foreign / "important").write_text("someone else")
    with pytest.raises(ValueError):
        installation.erase(tmp_path, "not-ours")
    assert (foreign / "important").exists()
    with pytest.raises(ValueError):
        installation.erase(tmp_path, "../../etc")
    assert foreign.is_dir()


def test_erasing_the_active_installation_clears_the_pointer(installation, tmp_path):
    prepared = installation.resolve(tmp_path)
    installation.erase(tmp_path, prepared.identifier)
    assert not (tmp_path / "current").exists()
    replacement = installation.resolve(tmp_path)
    assert replacement.identifier != prepared.identifier
    assert replacement.created
