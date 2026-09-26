"""Assemble an ad-hoc development app from already audited local artifacts."""

from __future__ import annotations

import argparse
import plistlib
import shutil
import subprocess
from pathlib import Path

UNINSTALL = """#!/bin/sh
# Erase this Reality Local installation, including every company and document in it.
set -eu
resources=$(cd "$(dirname "$0")" && pwd)
exec "$resources/../MacOS/reality-local" --erase --confirm-erasure
"""

UNSIGNED_BETA_GUIDE = """Reality Local — Unsigned Tester Beta

This build is for named testers only. It is not notarized by Apple and must not be
redistributed or treated as a production release.

To open it, Control-click Reality Local Unsigned Beta in Finder, choose Open, then Open
again. If macOS still blocks it, use System Settings > Privacy & Security > Open Anyway.

Your Reality data remains in your user Application Support directory when the app quits
or the application is removed. Use the bundled uninstall command only to erase everything.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument(
        "--frontend", type=Path, help="Include the interactive product runtime"
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--disposable",
        action="store_true",
        help="Build the fresh-test harness that removes its data on quit",
    )
    modes.add_argument(
        "--unsigned-tester-beta",
        action="store_true",
        help="Build the explicitly labelled named-tester beta",
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
            "installation.py",
            "recovery.py",
            "backup.py",
            "beta-custody.py",
            "migrate-database.py",
            "cluster.py",
        ):
            shutil.copy2(Path(__file__).with_name(name), resources / "probe" / name)
        if args.disposable:
            (resources / "probe/disposable").write_text(
                "This build initializes a new database and removes it on quit.\n"
            )
        else:
            erase = resources / "uninstall.command"
            erase.write_text(UNINSTALL)
            erase.chmod(0o755)
        if args.unsigned_tester_beta:
            (resources / "probe/unsigned-tester-beta").write_text(
                "unsigned-tester-beta\n"
            )
            (resources / "UNSIGNED-BETA-INSTALL.txt").write_text(UNSIGNED_BETA_GUIDE)
            index = resources / "frontend/index.html"
            html = index.read_text()
            marker = '<meta name="reality-distribution-channel" content="unsigned-tester-beta">'
            if "</head>" not in html:
                parser.error("Frontend index has no closing head element")
            index.write_text(html.replace("</head>", f"  {marker}\n</head>", 1))
    if args.disposable:
        identifier, name, channel = (
            "ai.runreality.local.development",
            "Reality Local Development",
            "disposable-development",
        )
    elif args.unsigned_tester_beta:
        identifier, name, channel = (
            "ai.runreality.local",
            "Reality Local Unsigned Beta",
            "unsigned-tester-beta",
        )
    else:
        identifier, name, channel = "ai.runreality.local", "Reality Local", "release"
    with (contents / "Info.plist").open("wb") as stream:
        plistlib.dump(
            {
                "CFBundleExecutable": "reality-local",
                "CFBundleIdentifier": identifier,
                "CFBundleName": name,
                "CFBundleDisplayName": name,
                "CFBundleIconFile": "RealityLocal.icns",
                "CFBundlePackageType": "APPL",
                "CFBundleShortVersionString": args.version,
                "CFBundleVersion": args.version,
                "LSMinimumSystemVersion": "14.0",
                "NSHighResolutionCapable": True,
                "NSAppTransportSecurity": {"NSAllowsLocalNetworking": True},
                "RealityDistributionChannel": channel,
                "RealityReleaseLabel": (
                    f"{args.version}-unsigned-beta"
                    if args.unsigned_tester_beta
                    else args.version
                ),
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
    kind = (
        "fresh-test harness"
        if args.disposable
        else "unsigned tester beta"
        if args.unsigned_tester_beta
        else "persistent installation"
    )
    print(f"Ad-hoc {kind} ({identifier}): {args.output}")
    if not args.disposable:
        print(
            "Data is kept in ~/Library/Application Support/"
            f"{identifier}. Erase it with:\n"
            f"  '{args.output}/Contents/Resources/uninstall.command'"
        )


if __name__ == "__main__":
    main()
