"""Private generated-secret custody for explicitly packaged unsigned tester betas."""

from __future__ import annotations

import json
import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

FORMAT_VERSION = 1
RECORD = "beta-custody.json"


class CustodyError(RuntimeError):
    """The beta custody record cannot safely supply the installation secrets."""


@dataclass(frozen=True)
class Values:
    database_password: str
    vault_master_key: str


def _read(path: Path, installation_id: str) -> Values:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        if path.is_symlink():
            raise CustodyError("Beta custody must be a regular file.") from error
        raise CustodyError("Beta custody is missing or unreadable.") from error
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise CustodyError("Beta custody must be a regular file.")
        if metadata.st_uid != os.getuid():
            raise CustodyError("Beta custody belongs to another user.")
        if stat.S_IMODE(metadata.st_mode) != 0o600:
            raise CustodyError("Beta custody permissions must be exactly 0600.")
        with os.fdopen(descriptor, encoding="utf-8") as stream:
            descriptor = -1
            value = json.load(stream)
    except (OSError, UnicodeError, ValueError) as error:
        raise CustodyError("Beta custody record is invalid.") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    required = {
        "format_version",
        "installation_id",
        "database_password",
        "vault_master_key",
    }
    if set(value) != required or value.get("format_version") != FORMAT_VERSION:
        raise CustodyError("Beta custody record is invalid.")
    if value.get("installation_id") != installation_id:
        raise CustodyError("Beta custody belongs to another installation.")
    database_password = value.get("database_password")
    vault_master_key = value.get("vault_master_key")
    if (
        not isinstance(database_password, str)
        or len(database_password) != 64
        or any(character not in "0123456789abcdef" for character in database_password)
        or not isinstance(vault_master_key, str)
        or len(vault_master_key) < 43
    ):
        raise CustodyError("Beta custody record is invalid.")
    return Values(database_password, vault_master_key)


def _create(path: Path, installation_id: str) -> None:
    value = {
        "format_version": FORMAT_VERSION,
        "installation_id": installation_id,
        "database_password": secrets.token_hex(32),
        "vault_master_key": secrets.token_urlsafe(32),
    }
    temporary = path.with_name(f".{path.stem}.{uuid4()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            json.dump(value, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink()


def load_or_create(
    root: Path, installation_id: str, *, existing_installation: bool
) -> Values:
    """Read exact values, creating them only for a genuinely new beta installation."""
    path = root / RECORD
    if not path.exists() and not path.is_symlink():
        if existing_installation:
            raise CustodyError("Beta custody is missing for an existing installation.")
        _create(path, installation_id)
    return _read(path, installation_id)


def complete_migration(root: Path, installation_id: str, expected: Values) -> None:
    """Remove beta custody only while it still contains the migrated exact values."""
    path = root / RECORD
    if _read(path, installation_id) != expected:
        raise CustodyError("Beta custody changed during Keychain migration.")
    path.unlink()
    directory = os.open(root, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
