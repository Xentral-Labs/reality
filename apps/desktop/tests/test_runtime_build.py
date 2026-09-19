"""Guard the build boundary before downloaded archives or binaries are consumed."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import sys
import tarfile
from pathlib import Path

import pytest


@pytest.fixture
def builder():
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        spec = importlib.util.spec_from_file_location(
            "desktop_runtime_build", scripts / "build-runtime.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.path.remove(str(scripts))


def test_checksum_mismatch_stops_before_extraction(builder, tmp_path):
    archive = tmp_path / "archive"
    archive.write_bytes(b"changed download")
    with pytest.raises(ValueError, match="checksum"):
        builder.verify_archive(archive, "0" * 64)
    builder.verify_archive(archive, hashlib.sha256(archive.read_bytes()).hexdigest())


def test_archive_path_escape_is_rejected(builder, tmp_path):
    archive = tmp_path / "bad.tar"
    with tarfile.open(archive, "w") as output:
        info = tarfile.TarInfo("../outside")
        info.size = 1
        output.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(ValueError, match="archive"):
        builder.extract_archive(archive, tmp_path / "out", "python")
    assert not (tmp_path / "outside").exists()


def test_archive_symlink_escape_is_rejected(builder, tmp_path):
    archive = tmp_path / "bad.tar"
    with tarfile.open(archive, "w") as output:
        info = tarfile.TarInfo("python/escape")
        info.type = tarfile.SYMTYPE
        info.linkname = "../../outside"
        output.addfile(info)
    with pytest.raises((ValueError, tarfile.FilterError)):
        builder.extract_archive(archive, tmp_path / "out", "python")


def test_install_name_replacement_is_relative_to_each_binary(builder, tmp_path):
    root = tmp_path / "runtime"
    binary = root / "postgres/bin/psql"
    library = root / "postgres/lib/libpq.5.dylib"
    assert (
        builder.loader_reference(binary, library, root)
        == "@loader_path/../lib/libpq.5.dylib"
    )
    with pytest.raises(ValueError):
        builder.loader_reference(binary, tmp_path / "foreign.dylib", root)


def test_output_cannot_overwrite_existing_data(builder, tmp_path):
    output = tmp_path / "runtime"
    output.mkdir()
    (output / "keep").write_text("existing")
    with pytest.raises(FileExistsError):
        builder.require_new_output(output)
    assert (output / "keep").read_text() == "existing"


@pytest.mark.parametrize("filename", ["libexample.dylib", "extension.abi3.so"])
def test_dylib_install_id_is_normalized_before_dependency_audit(
    builder, tmp_path, monkeypatch, filename
):
    root = tmp_path / "runtime"
    root.mkdir()
    library = root / filename
    library.write_bytes(b"\xcf\xfa\xed\xfe")
    calls = []

    def run(args, env):
        calls.append(args)
        if args[:2] == ["/usr/bin/otool", "-D"]:
            return f"{filename}:\nbazel-out/build/{filename}\n"
        if args[:2] == ["/usr/bin/otool", "-L"]:
            assert any("-id" in call for call in calls)
            return "libexample.dylib:\n    @loader_path/libexample.dylib (compatibility version 1.0.0)\n"
        if args[:2] == ["/usr/bin/otool", "-l"]:
            return "cmd LC_BUILD_VERSION\nminos 11.0\n"
        if args[:2] == ["/usr/bin/lipo", "-archs"]:
            return "arm64"
        return ""

    monkeypatch.setattr(builder, "run", run)
    assert builder.relocate_libraries(root, {}) == 1
    assert sum("-id" in call for call in calls) == 1


def test_runtime_layout_requires_search_extension(builder, tmp_path):
    with pytest.raises(ValueError, match="pg_trgm"):
        builder.validate_runtime_layout(tmp_path)
    for relative in builder.REQUIRED_RUNTIME_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture")
    builder.validate_runtime_layout(tmp_path)


def test_assembly_rejects_output_nested_in_source_before_copying(builder, tmp_path):
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    spec = importlib.util.spec_from_file_location(
        "desktop_assembler", scripts / "assemble-runtime.py"
    )
    assembler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(assembler)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    with pytest.raises(ValueError, match="outside"):
        assembler.assemble(
            runtime, tmp_path / "wheels", tmp_path / "core.whl", runtime / "output"
        )
    assert list(runtime.iterdir()) == []
