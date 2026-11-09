"""Spec 389: strict exact human-review proof and mapping-only wire contracts."""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field

PURPOSE = "shopify_source_buyer_mapping_only/1"
AUDIENCE = "reality:shopify-source-buyer-mapping/1"
ACTION_TYPE = "shopify_source_buyer_mapping/1"
APPROVAL_SOURCE = "shopify_buyer_mapping_approval"
HEX = r"^[a-f0-9]{64}$"
GID = r"^gid://shopify/Order/[0-9]{1,32}$"
SHOP = r"^[a-z0-9][a-z0-9-]{0,62}\.myshopify\.com$"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class BuyerMappingPolicy(Strict):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    tenant_id: str = Field(min_length=1, max_length=200)
    source_record_id: str = Field(min_length=1, max_length=200)
    import_job_id: str = Field(min_length=1, max_length=200)
    source_hash: str = Field(pattern=HEX)
    source_version: int = Field(gt=0)
    order_id: str = Field(pattern=GID)
    shop: str = Field(pattern=SHOP)
    query_digest: str = Field(pattern=HEX)
    issuer: str = Field(min_length=1, max_length=200)
    key_id: str = Field(min_length=1, max_length=200)
    public_key: str = Field(min_length=43, max_length=43)
    allowed_subjects: list[str] = Field(min_length=1, max_length=20)
    expires_at: str = Field(min_length=1, max_length=100)


class CandidateInput(Strict):
    source_record_id: str = Field(min_length=1, max_length=200)
    import_job_id: str = Field(min_length=1, max_length=200)
    query: str = Field(default="", max_length=120)
    limit: int = Field(default=20, ge=1, le=20)


class PrepareInput(Strict):
    request_id: str = Field(min_length=36, max_length=36)
    source_record_id: str = Field(min_length=1, max_length=200)
    import_job_id: str = Field(min_length=1, max_length=200)
    source_hash: str = Field(pattern=HEX)
    source_version: int = Field(gt=0)
    customer_party_id: str = Field(min_length=1, max_length=200)
    customer_digest: str = Field(pattern=HEX)


class CommitInput(Strict):
    review_id: str = Field(min_length=1, max_length=200)
    review_digest: str = Field(pattern=HEX)
    approval_proof: str = Field(min_length=1, max_length=16384)


class StatusInput(Strict):
    review_id: str = Field(min_length=1, max_length=200)


class ProofHeader(Strict):
    alg: Literal["EdDSA"]
    typ: Literal["tuesday-buyer-mapping+jwt"]
    kid: str = Field(min_length=1, max_length=200)


class ApprovalClaims(Strict):
    iss: str = Field(min_length=1, max_length=200)
    aud: Literal["reality:shopify-source-buyer-mapping/1"]
    sub: str = Field(min_length=1, max_length=200)
    iat: int
    exp: int
    jti: str = Field(min_length=36, max_length=36)
    tenant_id: str = Field(min_length=1, max_length=200)
    review_id: str = Field(min_length=1, max_length=200)
    review_digest: str = Field(pattern=HEX)
    purpose: Literal["shopify_source_buyer_mapping_only/1"]


def canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def proof_digest(value: str) -> str:
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def instant(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError("timezone_required")
    return result.astimezone(UTC)


def nonce(value: str) -> str:
    if str(UUID(value)) != value:
        raise ValueError("canonical_nonce_required")
    return value


def decode64(value: str) -> bytes:
    if not value or any(
        c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        for c in value
    ):
        raise ValueError("invalid_base64url")
    raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode() != value:
        raise ValueError("noncanonical_base64url")
    return raw


def _strict_json(raw: bytes) -> Any:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result

    return json.loads(
        raw.decode("utf-8", errors="strict"),
        object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(
            ValueError("invalid_json_constant")
        ),
    )


def verify_proof(
    value: str,
    policy: BuyerMappingPolicy,
    review_id: str,
    review_digest: str,
    now: datetime,
) -> ApprovalClaims:
    parts = value.split(".")
    if len(parts) != 3 or len(value) > 16384:
        raise ValueError("invalid_compact_proof")
    header = ProofHeader.model_validate(_strict_json(decode64(parts[0])))
    claims = ApprovalClaims.model_validate(_strict_json(decode64(parts[1])))
    nonce(claims.jti)
    key = decode64(policy.public_key)
    if len(key) != 32 or header.kid != policy.key_id:
        raise ValueError("wrong_issuer_key")
    Ed25519PublicKey.from_public_bytes(key).verify(
        decode64(parts[2]), f"{parts[0]}.{parts[1]}".encode("ascii")
    )
    at = int(now.timestamp())
    if (
        claims.iss != policy.issuer
        or claims.sub not in policy.allowed_subjects
        or claims.tenant_id != policy.tenant_id
        or claims.review_id != review_id
        or claims.review_digest != review_digest
        or claims.iat > at + 30
        or claims.exp <= at
        or claims.exp <= claims.iat
        or claims.exp > claims.iat + 300
    ):
        raise ValueError("approval_binding_or_expiry_changed")
    return claims
