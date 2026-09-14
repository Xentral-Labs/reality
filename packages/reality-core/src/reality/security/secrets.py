from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ROOT, Secret, SecretAuditEvent, now, uid
from reality.services.core import NotFound, get_tenant
from reality.services.tenant_policy import require_business_operation

KEY_PATH = ROOT / ".reality-secret.key"
KEY_VERSION = 1


def _master_key() -> Fernet:
    """Resolve the key-encryption key without ever storing it in the database."""
    configured = (
        os.environ.get("REALITY_MASTER_KEY", "").strip()
        or os.environ.get("REALITY_SETTINGS_KEY", "").strip()
    )
    if configured:
        try:
            return Fernet(configured.encode())
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                "REALITY_MASTER_KEY must be a valid URL-safe base64 Fernet key."
            ) from error
    if os.environ.get("REALITY_ENV", "").lower() in {"production", "prod"}:
        raise RuntimeError("REALITY_MASTER_KEY must be configured in production.")
    if not KEY_PATH.exists():
        KEY_PATH.write_bytes(Fernet.generate_key())
        KEY_PATH.chmod(0o600)
    return Fernet(KEY_PATH.read_bytes().strip())


def _encoded(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode()


def _decoded(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode())


def _aad(record: Secret) -> bytes:
    return f"{record.tenant_id}:{record.id}:{record.purpose}:{record.key_version}".encode()


def _fingerprint(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) <= 4:
        return "••••"
    prefix = cleaned[:3] if cleaned.startswith(("sk-", "key", "tok")) else ""
    return f"{prefix}••••{cleaned[-4:]}"


def _audit(session: Session, record: Secret, event_type: str) -> None:
    session.add(
        SecretAuditEvent(
            id=uid("sae"),
            tenant_id=record.tenant_id,
            secret_id=record.id,
            event_type=event_type,
        )
    )


def put_secret(
    session: Session,
    tenant_id: str,
    *,
    purpose: str,
    value: str,
    label: str,
    provider: str = "",
) -> Secret:
    require_business_operation(session, tenant_id, "secret_create")
    get_tenant(session, tenant_id)
    clear_value = value.strip()
    if not clear_value:
        raise ValueError("A secret value is required.")
    record = Secret(
        id=uid("sec"),
        tenant_id=tenant_id,
        purpose=purpose.strip(),
        provider=provider.strip(),
        label=label.strip() or purpose.strip(),
        ciphertext="",
        nonce="",
        encrypted_data_key="",
        key_version=KEY_VERSION,
        fingerprint=_fingerprint(clear_value),
    )
    data_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    record.nonce = _encoded(nonce)
    record.ciphertext = _encoded(
        AESGCM(data_key).encrypt(nonce, clear_value.encode(), _aad(record))
    )
    record.encrypted_data_key = _master_key().encrypt(data_key).decode()
    session.add(record)
    _audit(session, record, "created")
    session.flush()
    return record


def resolve_secret(session: Session, tenant_id: str, secret_id: str) -> str:
    require_business_operation(session, tenant_id, "secret_resolve")
    record = session.scalar(
        select(Secret).where(
            Secret.id == secret_id,
            Secret.tenant_id == tenant_id,
            Secret.status == "active",
        )
    )
    if record is None:
        raise NotFound("Secret not found.")
    try:
        data_key = _master_key().decrypt(record.encrypted_data_key.encode())
        clear_value = AESGCM(data_key).decrypt(
            _decoded(record.nonce), _decoded(record.ciphertext), _aad(record)
        )
    except (InvalidToken, ValueError) as error:
        raise NotFound("The configured secret cannot be decrypted.") from error
    record.last_used_at = now()
    _audit(session, record, "used")
    session.flush()
    return clear_value.decode()


def revoke_secret(session: Session, tenant_id: str, secret_id: str) -> Secret:
    require_business_operation(session, tenant_id, "secret_revoke")
    record = session.scalar(
        select(Secret).where(Secret.id == secret_id, Secret.tenant_id == tenant_id)
    )
    if record is None:
        raise NotFound("Secret not found.")
    if record.status != "revoked":
        record.status = "revoked"
        record.revoked_at = now()
        record.updated_at = now()
        _audit(session, record, "revoked")
    session.flush()
    return record


def replace_secret(
    session: Session,
    tenant_id: str,
    secret_id: str | None,
    *,
    purpose: str,
    value: str,
    label: str,
    provider: str = "",
) -> Secret:
    require_business_operation(session, tenant_id, "secret_replace")
    previous = None
    if secret_id:
        previous = session.scalar(
            select(Secret).where(
                Secret.id == secret_id, Secret.tenant_id == tenant_id
            )
        )
        if previous is None:
            raise NotFound("Secret not found.")
    replacement = put_secret(
        session,
        tenant_id,
        purpose=purpose,
        value=value,
        label=label,
        provider=provider,
    )
    if previous is not None:
        previous.status = "revoked"
        previous.revoked_at = now()
        previous.rotated_at = now()
        previous.updated_at = now()
        _audit(session, previous, "rotated")
    return replacement


def secret_metadata(session: Session, tenant_id: str, secret_id: str | None) -> Secret | None:
    if not secret_id:
        return None
    return session.scalar(
        select(Secret).where(Secret.id == secret_id, Secret.tenant_id == tenant_id)
    )


def list_secret_metadata(session: Session, tenant_id: str) -> list[Secret]:
    get_tenant(session, tenant_id)
    return list(
        session.scalars(
            select(Secret)
            .where(Secret.tenant_id == tenant_id)
            .order_by(Secret.created_at.desc())
        ).all()
    )
