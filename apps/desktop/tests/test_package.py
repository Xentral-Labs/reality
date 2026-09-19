"""A release must not silently depend on the developer's checkout or Homebrew."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/runtime_audit.py"


@pytest.fixture
def audit():
    spec = importlib.util.spec_from_file_location("desktop_runtime_audit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_absolute_developer_library_is_rejected(audit):
    output = """python3.12:
    /opt/homebrew/opt/python@3.12/Frameworks/Python.framework/Versions/3.12/Python (compatibility version 3.12.0, current version 3.12.0)
    /usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1345.100.2)
"""
    assert audit.external_dependencies(output) == [
        "/opt/homebrew/opt/python@3.12/Frameworks/Python.framework/Versions/3.12/Python"
    ]


def test_system_and_relative_dependencies_are_classified(audit):
    output = """postgres:
    @loader_path/../lib/libpq.5.dylib (compatibility version 5.0.0, current version 5.17.0)
    @rpath/libssl.3.dylib (compatibility version 3.0.0, current version 3.0.0)
    /System/Library/Frameworks/Security.framework/Versions/A/Security (compatibility version 1.0.0, current version 61123.0.0)
    /usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1345.100.2)
"""
    assert audit.external_dependencies(output) == []
    # Relative paths are separately reported for loader/rpath qualification, never certified here.
    assert audit.relative_dependencies(output) == [
        "@loader_path/../lib/libpq.5.dylib",
        "@rpath/libssl.3.dylib",
    ]


def test_malicious_system_prefix_is_not_treated_as_system_library(audit):
    output = "app:\n    /usr/library/private.dylib (compatibility version 1.0.0)\n"
    assert audit.external_dependencies(output) == ["/usr/library/private.dylib"]


def test_runtime_tree_rejects_escaping_and_broken_symlinks(audit, tmp_path):
    root = tmp_path / "runtime"
    root.mkdir()
    outside = tmp_path / "external"
    outside.write_text("not bundled")
    (root / "outside").symlink_to(outside)
    (root / "broken").symlink_to("missing")
    problems = audit.tree_problems(root)
    assert any("outside" in item and "escapes" in item for item in problems)
    assert any("broken" in item and "broken" in item for item in problems)


def test_runtime_tree_accepts_internal_relative_symlinks(audit, tmp_path):
    (tmp_path / "versioned").write_text("bundled")
    (tmp_path / "current").symlink_to("versioned")
    assert audit.tree_problems(tmp_path) == []


def test_core_wheel_requires_migrations_catalogs_and_demo_resources(audit, tmp_path):
    import zipfile

    wheel = tmp_path / "core.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("reality/__init__.py", "")
    missing = audit.wheel_problems(wheel)
    assert any("migrations" in item for item in missing)
    assert any("config" in item for item in missing)
    assert any("storylines" in item for item in missing)


def test_core_wheel_rejects_archive_escape(audit, tmp_path):
    import zipfile

    wheel = tmp_path / "core.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("../escaped", "content")
    assert any("unsafe" in item for item in audit.wheel_problems(wheel))


def test_absolute_internal_symlink_would_break_after_relocation(audit, tmp_path):
    (tmp_path / "versioned").write_text("bundled")
    (tmp_path / "current").symlink_to(tmp_path / "versioned")
    assert any("not relocatable" in item for item in audit.tree_problems(tmp_path))


def test_native_minimum_os_is_checked_including_universal_slices(audit):
    output = """Load command 10
      cmd LC_BUILD_VERSION
  cmdsize 32
 platform 1
    minos 11.0
      sdk 14.0
Load command 11
      cmd LC_VERSION_MIN_MACOSX
  cmdsize 16
  version 10.9
      sdk 13.0
"""
    assert audit.minimum_macos_versions(output) == [(11, 0), (10, 9)]
    assert not audit.minimum_macos_problems(output, "14.0")
    assert audit.minimum_macos_problems(
        output.replace("minos 11.0", "minos 15.0"), "14.0"
    )
    assert audit.minimum_macos_problems("not a supported Mach-O load command", "14.0")


def test_rpaths_are_parsed_without_confusing_dependency_names(audit):
    output = """Load command 12
          cmd LC_RPATH
      cmdsize 48
         path /tmp/build with spaces/postgres/lib (offset 12)
Load command 13
          cmd LC_LOAD_DYLIB
         name @rpath/libpq.5.dylib (offset 24)
Load command 14
          cmd LC_RPATH
         path @loader_path/../lib (offset 12)
"""
    assert audit.library_search_paths(output) == [
        "/tmp/build with spaces/postgres/lib",
        "@loader_path/../lib",
    ]
