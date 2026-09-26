"""Process-local master-key custody shared by hosted and desktop runtimes."""

from __future__ import annotations

import os
from pathlib import Path

from cryptography.fernet import Fernet

from reality.db.core import ROOT

DEFAULT_KEY_PATH = ROOT / ".reality-secret.key"
_process_key: tuple[str, bytes] | None = None


def _validated(value: str | bytes) -> bytes:
    encoded = value.encode() if isinstance(value, str) else value
    if not encoded.strip():
        raise RuntimeError("A master key is required.")
    try:
        Fernet(encoded.strip())
    except (TypeError, ValueError) as error:
        raise RuntimeError("The master key must be a valid Fernet key.") from error
    return encoded.strip()


def install_process_key(value: str, *, installation_id: str) -> None:
    """Install one desktop-delivered key without permitting in-process rotation."""
    global _process_key
    installation = installation_id.strip()
    if not installation:
        raise RuntimeError("An installation identity is required.")
    encoded = _validated(value)
    if _process_key is not None:
        raise RuntimeError("The process master key is already initialized.")
    _process_key = (installation, encoded)


def master_key(
    *,
    installation_id: str | None = None,
    key_path: Path = DEFAULT_KEY_PATH,
    environment_names: tuple[str, ...] = (
        "REALITY_MASTER_KEY",
        "REALITY_SETTINGS_KEY",
    ),
) -> bytes:
    """Resolve desktop handoff first, preserving the existing hosted contract."""
    if _process_key is not None:
        bound_installation, encoded = _process_key
        if installation_id and installation_id != bound_installation:
            raise RuntimeError("The master key belongs to a different installation.")
        return encoded
    if os.environ.get("REALITY_DESKTOP", "").strip() == "1":
        raise RuntimeError("Desktop master key requires the private runtime handoff.")
    configured = next(
        (
            os.environ.get(name, "").strip()
            for name in environment_names
            if os.environ.get(name, "").strip()
        ),
        "",
    )
    if configured:
        return _validated(configured)
    if os.environ.get("REALITY_ENV", "").lower() in {"production", "prod"}:
        raise RuntimeError("REALITY_MASTER_KEY must be configured in production.")
    if not key_path.exists():
        key_path.write_bytes(Fernet.generate_key())
        key_path.chmod(0o600)
    return _validated(key_path.read_bytes())
