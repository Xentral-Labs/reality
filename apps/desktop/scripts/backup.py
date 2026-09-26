"""Versioned authenticated encryption for Reality Local logical backups."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import struct
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MAGIC = b"REALITY-BACKUP\x00"
FORMAT_VERSION = 1
NONCE_BYTES = 12
TAG_BYTES = 16
MAX_MANIFEST_BYTES = 64 * 1024
CHUNK_BYTES = 1024 * 1024
MANIFEST_FIELDS = {
    "format_version",
    "installation_id",
    "application_version",
    "schema_revision",
    "created_at",
    "archive_bytes",
    "archive_sha256",
}


class BackupError(RuntimeError):
    """A backup cannot be authenticated or admitted safely."""


def key_from_vault(vault_master_key: str, *, installation_id: str) -> bytes:
    """Derive a domain-separated backup key from installation Keychain custody."""
    try:
        material = base64.urlsafe_b64decode(vault_master_key.encode())
    except (ValueError, TypeError) as error:
        raise BackupError("Vault master key is invalid.") from error
    if len(material) != 32:
        raise BackupError("Vault master key is invalid.")
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=installation_id.encode(),
        info=b"reality-local-backup-v1",
    ).derive(material)


def _key(value: bytes) -> bytes:
    if not isinstance(value, bytes) or len(value) != 32:
        raise BackupError("Backup key must contain exactly 32 bytes.")
    return value


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK_BYTES), b""):
            value.update(block)
    return value.hexdigest()


def _publish(partial: Path, destination: Path) -> None:
    with partial.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(partial, destination)
    directory = os.open(destination.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def encrypt_archive(
    archive: Path,
    destination: Path,
    key: bytes,
    *,
    installation_id: str,
    application_version: str,
    schema_revision: str,
) -> dict:
    """Encrypt and atomically publish one custom-format PostgreSQL archive."""
    key = _key(key)
    if not archive.is_file() or archive.stat().st_size == 0:
        raise BackupError("Backup source archive is empty or missing.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format_version": FORMAT_VERSION,
        "installation_id": installation_id,
        "application_version": application_version,
        "schema_revision": schema_revision,
        "created_at": datetime.now(UTC).isoformat(),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _digest(archive),
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise BackupError("Backup manifest is too large.")
    nonce = os.urandom(NONCE_BYTES)
    prefix = MAGIC + bytes([FORMAT_VERSION]) + nonce
    partial = destination.parent / f".{destination.name}.{uuid4()}.partial"
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(prefix)
    try:
        with partial.open("xb") as output, archive.open("rb") as source:
            output.write(prefix)
            output.write(encryptor.update(struct.pack(">I", len(encoded))))
            output.write(encryptor.update(encoded))
            for block in iter(lambda: source.read(CHUNK_BYTES), b""):
                output.write(encryptor.update(block))
            output.write(encryptor.finalize())
            output.write(encryptor.tag)
        _publish(partial, destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return manifest


def decrypt_archive(
    source: Path,
    destination: Path,
    key: bytes,
    *,
    expected_installation_id: str,
    supported_revisions: set[str],
) -> dict:
    """Authenticate and admit a backup into a private archive path."""
    key = _key(key)
    prefix_bytes = len(MAGIC) + 1 + NONCE_BYTES
    try:
        size = source.stat().st_size
    except OSError as error:
        raise BackupError("Backup is missing.") from error
    if size <= prefix_bytes + TAG_BYTES + 4:
        raise BackupError("Backup is incomplete.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.parent / f".{destination.name}.{uuid4()}.partial"
    try:
        with source.open("rb") as encrypted:
            prefix = encrypted.read(prefix_bytes)
            if prefix[: len(MAGIC)] != MAGIC or prefix[len(MAGIC)] != FORMAT_VERSION:
                raise BackupError("Backup format is unsupported.")
            nonce = prefix[-NONCE_BYTES:]
            encrypted.seek(-TAG_BYTES, os.SEEK_END)
            tag = encrypted.read(TAG_BYTES)
            ciphertext_bytes = size - prefix_bytes - TAG_BYTES
            encrypted.seek(prefix_bytes)
            decryptor = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
            decryptor.authenticate_additional_data(prefix)
            length_bytes = decryptor.update(encrypted.read(4))
            if len(length_bytes) != 4:
                raise BackupError("Backup manifest is incomplete.")
            manifest_bytes = struct.unpack(">I", length_bytes)[0]
            if (
                manifest_bytes > MAX_MANIFEST_BYTES
                or manifest_bytes > ciphertext_bytes - 4
            ):
                raise BackupError("Backup manifest length is invalid.")
            encoded = decryptor.update(encrypted.read(manifest_bytes))
            remaining = ciphertext_bytes - 4 - manifest_bytes
            digest = hashlib.sha256()
            written = 0
            with partial.open("xb") as output:
                while remaining:
                    block = encrypted.read(min(CHUNK_BYTES, remaining))
                    if not block:
                        raise BackupError("Backup ciphertext is incomplete.")
                    remaining -= len(block)
                    plain = decryptor.update(block)
                    output.write(plain)
                    digest.update(plain)
                    written += len(plain)
                final = decryptor.finalize()
                output.write(final)
                digest.update(final)
                written += len(final)
            manifest = json.loads(encoded)
            if set(manifest) != MANIFEST_FIELDS or manifest.get("format_version") != 1:
                raise BackupError("Backup manifest is invalid.")
            if manifest.get("installation_id") != expected_installation_id:
                raise BackupError("Backup belongs to another installation.")
            if manifest.get("schema_revision") not in supported_revisions:
                raise BackupError("Backup schema is not supported by this application.")
            if manifest.get("archive_bytes") != written:
                raise BackupError("Backup archive size does not match its manifest.")
            if manifest.get("archive_sha256") != digest.hexdigest():
                raise BackupError("Backup archive digest does not match its manifest.")
        _publish(partial, destination)
        return manifest
    except (
        BackupError,
        InvalidTag,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        partial.unlink(missing_ok=True)
        if isinstance(error, BackupError):
            raise
        raise BackupError("Backup authentication or decoding failed.") from error
