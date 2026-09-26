"""Generate and verify the exact macOS release-signing contract."""

from __future__ import annotations

import argparse
import plistlib
import subprocess
from pathlib import Path


class SigningError(RuntimeError):
    """A release signing input or resulting signature is not qualified."""


MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce",
    b"\xce\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe",
    b"\xbe\xba\xfe\xca",
    b"\xca\xfe\xba\xbf",
    b"\xbf\xba\xfe\xca",
}


def is_macho(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    try:
        with path.open("rb") as stream:
            return stream.read(4) in MACHO_MAGICS
    except OSError:
        return False


def nested_macho_files(app: Path) -> list[Path]:
    """Return every nested Mach-O leaf in deterministic deepest-first order."""
    executable = app / "Contents/MacOS/reality-local"
    paths = [path for path in app.rglob("*") if is_macho(path) and path != executable]
    return sorted(paths, key=lambda path: (-len(path.parts), path.as_posix()))


def sign_nested(app: Path, *, identity: str) -> list[Path]:
    if not identity.strip():
        raise SigningError("Developer ID signing identity is required.")
    signed = nested_macho_files(app)
    for path in signed:
        result = subprocess.run(
            [
                "/usr/bin/codesign",
                "--force",
                "--timestamp",
                "--options",
                "runtime",
                "--sign",
                identity,
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode:
            raise SigningError(f"Nested signing failed: {path.relative_to(app)}")
    return signed


def entitlement_values(team_id: str, bundle_id: str) -> dict:
    if not team_id.isalnum() or not team_id:
        raise SigningError("Apple team ID must be non-empty and alphanumeric.")
    if not bundle_id or any(part == "" for part in bundle_id.split(".")):
        raise SigningError("Bundle identifier is invalid.")
    application_id = f"{team_id}.{bundle_id}"
    return {
        "com.apple.application-identifier": application_id,
        "com.apple.developer.team-identifier": team_id,
        "keychain-access-groups": [application_id],
    }


def write_entitlements(output: Path, *, team_id: str, bundle_id: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as stream:
        plistlib.dump(
            entitlement_values(team_id, bundle_id),
            stream,
            fmt=plistlib.FMT_XML,
            sort_keys=True,
        )


def signed_entitlements(app: Path) -> dict:
    result = subprocess.run(
        ["/usr/bin/codesign", "--display", "--entitlements", ":-", str(app)],
        capture_output=True,
        timeout=30,
        check=False,
    )
    if result.returncode:
        raise SigningError("codesign could not read the application entitlements.")
    try:
        return plistlib.loads(result.stdout)
    except plistlib.InvalidFileException as error:
        raise SigningError(
            "Signed entitlements are not a valid property list."
        ) from error


def verify(app: Path, *, team_id: str, bundle_id: str) -> None:
    profile = app / "Contents/embedded.provisionprofile"
    if not profile.is_file() or profile.stat().st_size == 0:
        raise SigningError("Developer ID provisioning profile is missing.")
    expected = entitlement_values(team_id, bundle_id)
    actual = signed_entitlements(app)
    for key, value in expected.items():
        if actual.get(key) != value:
            raise SigningError(f"Signed entitlement does not match: {key}")
    forbidden = {"com.apple.security.get-task-allow"}
    if forbidden.intersection(actual):
        raise SigningError("Release signature contains a development-only entitlement.")
    checked = subprocess.run(
        [
            "/usr/bin/codesign",
            "--verify",
            "--deep",
            "--strict",
            "--verbose=2",
            str(app),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if checked.returncode:
        raise SigningError("Application signature verification failed.")


def verify_dmg(dmg: Path) -> None:
    """Require a valid signature, stapled ticket, and Gatekeeper acceptance."""
    if not dmg.is_file() or dmg.is_symlink():
        raise SigningError("Signed disk image is missing.")
    commands = [
        ["/usr/bin/codesign", "--verify", "--strict", "--verbose=2", str(dmg)],
        ["/usr/bin/xcrun", "stapler", "validate", str(dmg)],
        [
            "/usr/sbin/spctl",
            "--assess",
            "--type",
            "open",
            "--context",
            "context:primary-signature",
            "--verbose=2",
            str(dmg),
        ],
    ]
    for command in commands:
        checked = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if checked.returncode:
            raise SigningError(f"Disk image qualification failed: {command[0]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    prepare = subcommands.add_parser("prepare")
    prepare.add_argument("--team-id", required=True)
    prepare.add_argument("--bundle-id", required=True)
    prepare.add_argument("--output", type=Path, required=True)
    qualify = subcommands.add_parser("verify")
    qualify.add_argument("--team-id", required=True)
    qualify.add_argument("--bundle-id", required=True)
    qualify.add_argument("--app", type=Path, required=True)
    nested = subcommands.add_parser("sign-nested")
    nested.add_argument("--identity", required=True)
    nested.add_argument("--app", type=Path, required=True)
    disk_image = subcommands.add_parser("verify-dmg")
    disk_image.add_argument("--dmg", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.command == "prepare":
        write_entitlements(
            arguments.output,
            team_id=arguments.team_id,
            bundle_id=arguments.bundle_id,
        )
    elif arguments.command == "verify":
        verify(
            arguments.app,
            team_id=arguments.team_id,
            bundle_id=arguments.bundle_id,
        )
    elif arguments.command == "sign-nested":
        sign_nested(arguments.app, identity=arguments.identity)
    else:
        verify_dmg(arguments.dmg)


if __name__ == "__main__":
    main()
