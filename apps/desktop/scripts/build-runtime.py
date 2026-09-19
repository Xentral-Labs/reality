"""Build an isolated macOS runtime from checked, explicitly downloaded inputs.

Does not install system packages, migrate a database, or fetch unpinned inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

from runtime_audit import (
    external_dependencies,
    library_search_paths,
    minimum_macos_problems,
    tree_problems,
)

SCRIPTS = Path(__file__).resolve().parent
MACHO_MAGICS = {
    b"\xcf\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xca\xfe\xba\xbe",
    b"\xbe\xba\xfe\xca",
}


REQUIRED_RUNTIME_FILES = (
    "python/bin/python3.12",
    "postgres/bin/postgres",
    "postgres/bin/initdb",
    "postgres/bin/pg_isready",
    "postgres/bin/pg_dump",
    "postgres/bin/pg_restore",
    "postgres/lib/pg_trgm.dylib",
    "postgres/share/extension/pg_trgm.control",
)


def validate_runtime_layout(root: Path) -> None:
    missing = [name for name in REQUIRED_RUNTIME_FILES if not (root / name).is_file()]
    if missing:
        raise ValueError("Missing runtime components: " + ", ".join(missing))


def verify_archive(path: Path, expected: str) -> None:
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"Archive checksum mismatch: {path.name}")


def extract_archive(path: Path, destination: Path, expected_root: str) -> None:
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            if (
                name.is_absolute()
                or ".." in name.parts
                or not name.parts
                or name.parts[0] != expected_root
            ):
                raise ValueError(f"Unsafe archive entry: {member.name}")
        destination.mkdir(parents=True, exist_ok=True)
        archive.extractall(destination, filter="data")


def require_new_output(output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output already exists; choose a new path: {output}")


def loader_reference(binary: Path, library: Path, root: Path) -> str:
    if not binary.is_relative_to(root) or not library.is_relative_to(root):
        raise ValueError("Cannot relocate a library outside the bundle")
    return "@loader_path/" + os.path.relpath(library, binary.parent)


def build_environment(minimum_macos: str) -> dict[str, str]:
    # Do not inherit Homebrew compiler/linker paths, Python paths or application secrets.
    env = {
        key: os.environ[key] for key in ("HOME", "TMPDIR", "USER") if key in os.environ
    }
    env.update(
        PATH="/usr/bin:/bin:/usr/sbin:/sbin",
        LC_ALL="C",
        MACOSX_DEPLOYMENT_TARGET=minimum_macos,
    )
    clt = Path("/Library/Developer/CommandLineTools")
    if clt.is_dir():
        env["DEVELOPER_DIR"] = str(clt)
    return env


def run(args: list[str], env: dict[str, str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        args,
        env=env,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=1200,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"Build command failed: {args[0]}\n{result.stdout[-5000:]}\n{result.stderr[-5000:]}"
        )
    return result.stdout


def macho_files(root: Path) -> list[Path]:
    result = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            with path.open("rb") as stream:
                if stream.read(4) in MACHO_MAGICS:
                    result.append(path)
    return result


def relocate_libraries(root: Path, env: dict[str, str]) -> int:
    binaries = macho_files(root)
    for binary in binaries:
        # otool -L includes a dylib's own install ID as its first entry.
        # Normalize it before inspecting external dependency references.
        install_ids = run(["/usr/bin/otool", "-D", str(binary)], env).splitlines()
        if len(install_ids) > 1:
            run(
                [
                    "/usr/bin/install_name_tool",
                    "-id",
                    f"@loader_path/{binary.name}",
                    str(binary),
                ],
                env,
            )
        output = run(["/usr/bin/otool", "-L", str(binary)], env)
        changes = []
        for name in external_dependencies(output):
            library = Path(name)
            if not library.is_relative_to(root) or not library.is_file():
                raise ValueError(
                    f"Unbundled native dependency in {binary.relative_to(root)}: {name}"
                )
            changes.extend(["-change", name, loader_reference(binary, library, root)])
        if changes:
            run(["/usr/bin/install_name_tool", *changes, str(binary)], env)
        # All distributed binaries must be native arm64; do not silently ship host x86 builds.
        architectures = run(["/usr/bin/lipo", "-archs", str(binary)], env).split()
        if "arm64" not in architectures:
            raise ValueError(f"Missing arm64 slice: {binary.relative_to(root)}")
        load_commands = run(["/usr/bin/otool", "-l", str(binary)], env)
        for search_path in library_search_paths(load_commands):
            if search_path.startswith("/"):
                directory = Path(search_path)
                if not directory.is_relative_to(root):
                    raise ValueError(
                        f"External library search path in {binary.relative_to(root)}: {search_path}"
                    )
                run(
                    [
                        "/usr/bin/install_name_tool",
                        "-rpath",
                        search_path,
                        loader_reference(binary, directory, root),
                        str(binary),
                    ],
                    env,
                )
        if problems := minimum_macos_problems(
            load_commands, env.get("MACOSX_DEPLOYMENT_TARGET", "14.0")
        ):
            raise ValueError(f"{binary.relative_to(root)}: {problems}")
        run(["/usr/bin/codesign", "--force", "--sign", "-", str(binary)], env)
        if external_dependencies(run(["/usr/bin/otool", "-L", str(binary)], env)):
            raise ValueError(f"Absolute dependency remains: {binary.relative_to(root)}")
    return len(binaries)


def build(cache: Path, output: Path, jobs: int) -> dict:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise ValueError(
            "This build currently supports native Apple Silicon macOS only"
        )
    require_new_output(output)
    lock = json.loads((SCRIPTS / "runtime-dependencies.lock").read_text())
    env = build_environment(lock["minimum_macos"])
    for name in ("python", "postgresql"):
        verify_archive(cache / lock[name]["archive"], lock[name]["sha256"])
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="desktop-build-", dir=output.parent
    ) as working:
        work = Path(working)
        runtime = work / "runtime"
        print(
            "Extracting verified standalone Python and PostgreSQL sources", flush=True
        )
        extract_archive(cache / lock["python"]["archive"], runtime, "python")
        extract_archive(
            cache / lock["postgresql"]["archive"],
            work / "sources",
            lock["postgresql"]["root"],
        )
        pg_source = work / "sources" / lock["postgresql"]["root"]
        pg_root = runtime / "postgres"
        print("Configuring PostgreSQL without Homebrew dependencies", flush=True)
        run(
            [
                str(pg_source / "configure"),
                f"--prefix={pg_root}",
                "--without-readline",
                "--without-icu",
                "--without-zlib",
            ],
            env,
            cwd=pg_source,
        )
        print("Compiling PostgreSQL", flush=True)
        run(["/usr/bin/make", f"-j{jobs}"], env, cwd=pg_source)
        run(["/usr/bin/make", "install"], env, cwd=pg_source)
        # Required by the existing global-search migration, not an optional desktop feature.
        run(["/usr/bin/make", f"-j{jobs}"], env, cwd=pg_source / "contrib/pg_trgm")
        run(["/usr/bin/make", "install"], env, cwd=pg_source / "contrib/pg_trgm")
        (runtime / "licenses").mkdir()
        shutil.copy2(pg_source / "COPYRIGHT", runtime / "licenses/PostgreSQL-COPYRIGHT")
        print("Relocating and auditing native libraries", flush=True)
        validate_runtime_layout(runtime)
        count = relocate_libraries(runtime, env)
        if problems := tree_problems(runtime):
            raise ValueError("\n".join(problems))
        manifest = {
            "format_version": 1,
            "dependencies": lock,
            "native_binaries": count,
            "qualification": "unsigned-runtime-spike",
        }
        (runtime / "runtime-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
        require_new_output(output)
        runtime.rename(output)
    # The old build prefix is now gone. A successful --version is a first relocation check.
    python_version = run(
        [
            str(output / "python/bin/python3.12"),
            "-I",
            "-c",
            "import ssl, ctypes, multiprocessing; print(__import__('sys').version)",
        ],
        env,
    ).strip()
    pg_version = run([str(output / "postgres/bin/postgres"), "--version"], env).strip()
    return {
        "output": str(output),
        "python": python_version,
        "postgresql": pg_version,
        "native_binaries": count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target", choices=["aarch64-apple-darwin"], default="aarch64-apple-darwin"
    )
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4, choices=range(1, 17))
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                build(args.cache.resolve(), args.output.absolute(), args.jobs), indent=2
            )
        )
    except (
        ValueError,
        OSError,
        RuntimeError,
        tarfile.TarError,
        subprocess.TimeoutExpired,
    ) as error:
        parser.exit(1, f"Runtime build failed: {error}\n")


if __name__ == "__main__":
    main()
