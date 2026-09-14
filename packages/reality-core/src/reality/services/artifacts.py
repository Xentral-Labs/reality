from __future__ import annotations

import hashlib
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ROOT, SourceArtifact, Tenant, now, uid
from reality.services.core import InvalidOperation, NotFound
from reality.services.tenant_policy import require_business_operation

CHUNK_SIZE = 1024 * 1024
DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024 * 1024


def artifact_root() -> Path:
    return Path(os.environ.get("REALITY_ARTIFACT_DIR", ROOT / "data" / "artifacts"))


def storage_backend() -> str:
    backend = os.environ.get("REALITY_ARTIFACT_STORAGE", "file").strip().lower()
    if backend not in {"file", "s3"}:
        raise InvalidOperation("REALITY_ARTIFACT_STORAGE must be 'file' or 's3'.")
    return backend


def _s3_bucket() -> str:
    bucket = os.environ.get("REALITY_S3_BUCKET", "").strip()
    if not bucket:
        raise InvalidOperation("REALITY_S3_BUCKET is required for S3 artifact storage.")
    return bucket


def _s3_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("REALITY_S3_ENDPOINT_URL") or None,
        region_name=os.environ.get("REALITY_S3_REGION", "eu-central-1"),
    )


def artifact_path(artifact: SourceArtifact) -> Path:
    if storage_backend() != "file":
        raise InvalidOperation("S3 artifacts must be accessed through materialize_artifact().")
    root = artifact_root().resolve()
    path = (root / artifact.storage_key).resolve()
    if root not in path.parents:
        raise InvalidOperation("Artifact storage key is invalid.")
    return path


@contextmanager
def materialize_artifact(artifact: SourceArtifact) -> Iterator[Path]:
    """Yield a local readable path regardless of the configured storage adapter."""
    if storage_backend() == "file":
        yield artifact_path(artifact)
        return
    suffix = Path(artifact.filename).suffix[:16]
    handle, temporary_name = tempfile.mkstemp(prefix="reality-artifact-", suffix=suffix)
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        _s3_client().download_file(_s3_bucket(), artifact.storage_key, str(temporary))
        yield temporary
    finally:
        temporary.unlink(missing_ok=True)


def stage_artifact(
    session: Session,
    tenant_id: str,
    stream: BinaryIO,
    *,
    filename: str,
    content_type: str,
) -> tuple[SourceArtifact, bytes]:
    require_business_operation(session, tenant_id, "artifact_stage")
    if session.scalar(select(Tenant.id).where(Tenant.id == tenant_id)) is None:
        raise NotFound("Tenant not found.")
    safe_filename = Path(filename or "upload.bin").name[:255]
    maximum = int(os.environ.get("REALITY_MAX_UPLOAD_BYTES", DEFAULT_MAX_UPLOAD_BYTES))
    root = artifact_root()
    staging = root / tenant_id / ".staging"
    staging.mkdir(parents=True, exist_ok=True)
    temporary = staging / f"{uid('upl')}.part"
    digest = hashlib.sha256()
    byte_size = 0
    sample = bytearray()
    try:
        with temporary.open("xb") as target:
            while chunk := stream.read(CHUNK_SIZE):
                byte_size += len(chunk)
                if byte_size > maximum:
                    raise InvalidOperation(
                        f"Upload exceeds the configured limit of {maximum} bytes."
                    )
                digest.update(chunk)
                if len(sample) < 65536:
                    sample.extend(chunk[: 65536 - len(sample)])
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        if byte_size == 0:
            raise InvalidOperation("The uploaded file is empty.")
        sha256 = digest.hexdigest()
        existing = session.scalar(
            select(SourceArtifact).where(
                SourceArtifact.tenant_id == tenant_id,
                SourceArtifact.sha256 == sha256,
            )
        )
        if existing:
            temporary.unlink(missing_ok=True)
            return existing, bytes(sample)
        storage_key = f"{tenant_id}/{sha256[:2]}/{sha256}"
        if storage_backend() == "s3":
            _s3_client().upload_file(
                str(temporary),
                _s3_bucket(),
                storage_key,
                ExtraArgs={"ContentType": content_type or "application/octet-stream"},
            )
            temporary.unlink(missing_ok=True)
        else:
            final = root / storage_key
            final.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temporary, final)
        artifact = SourceArtifact(
            id=uid("art"),
            tenant_id=tenant_id,
            filename=safe_filename,
            content_type=(content_type or "application/octet-stream")[:255],
            byte_size=byte_size,
            sha256=sha256,
            storage_key=storage_key,
            status="staged",
        )
        session.add(artifact)
        session.commit()
        return artifact, bytes(sample)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def get_artifact(session: Session, tenant_id: str, artifact_id: str) -> SourceArtifact:
    artifact = session.scalar(
        select(SourceArtifact).where(
            SourceArtifact.tenant_id == tenant_id,
            SourceArtifact.id == artifact_id,
        )
    )
    if artifact is None:
        raise NotFound("Source artifact not found.")
    return artifact


def mark_artifact_attached(artifact: SourceArtifact) -> None:
    artifact.status = "attached"
    artifact.attached_at = now()
