"""Assemble an ad-hoc development app from already audited local artifacts."""

from __future__ import annotations

import argparse
import plistlib
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--frontend", type=Path, help="Include the disposable interactive setup runtime"
    )
    args = parser.parse_args()
    if args.output.exists() or args.output.suffix != ".app":
        parser.error("Output must be a new .app directory")
    contents = args.output / "Contents"
    executable = contents / "MacOS"
    executable.mkdir(parents=True)
    resources = contents / "Resources"
    resources.mkdir()
    icon = Path(__file__).resolve().parents[1] / "src-tauri/icons/RealityLocal.icns"
    if not icon.is_file():
        parser.error("Build the canonical macOS icon before packaging")
    shutil.copy2(icon, resources / "RealityLocal.icns")
    shutil.copy2(args.binary, executable / "reality-local")
    shutil.copytree(args.runtime, resources / "runtime", symlinks=True)
    (resources / "probe").mkdir()
    shutil.copy2(
        Path(__file__).with_name("native-probe.py"), resources / "probe/native-probe.py"
    )
    if args.frontend:
        shutil.copytree(args.frontend, resources / "frontend")
        for name in (
            "local-runtime.py",
            "local-product.py",
            "local-background.py",
            "runtime-smoke.py",
        ):
            shutil.copy2(Path(__file__).with_name(name), resources / "probe" / name)
    with (contents / "Info.plist").open("wb") as stream:
        plistlib.dump(
            {
                "CFBundleExecutable": "reality-local",
                "CFBundleIdentifier": "ai.runreality.local.development",
                "CFBundleName": "Reality Local Development",
                "CFBundleDisplayName": "Reality Local Development",
                "CFBundleIconFile": "RealityLocal.icns",
                "CFBundlePackageType": "APPL",
                "CFBundleShortVersionString": "0.1.0",
                "CFBundleVersion": "1",
                "LSMinimumSystemVersion": "14.0",
                "NSHighResolutionCapable": True,
                "NSAppTransportSecurity": {"NSAllowsLocalNetworking": True},
            },
            stream,
        )
    subprocess.run(
        ["/usr/bin/codesign", "--force", "--sign", "-", str(args.output)], check=True
    )
    subprocess.run(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(args.output)],
        check=True,
    )
    print(f"Ad-hoc development preview: {args.output}")


if __name__ == "__main__":
    main()
