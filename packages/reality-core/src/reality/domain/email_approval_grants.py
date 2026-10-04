"""Closed v1 external email approval and server-owned trust envelopes."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class AcceptEmailGrant(Closed):
    proposal_id: str = Field(min_length=1, max_length=200)
    grant: str = Field(
        min_length=1,
        max_length=16384,
        description="Compact Ed25519 JWS for the exact returned approval_digest. Issuer and subject require server-configured company authority; this operation does not grant token approval rights.",
    )


class GrantHeader(Closed):
    alg: Literal["EdDSA"]
    typ: Literal["reality-email-approval+jwt"]
    kid: str = Field(min_length=1, max_length=200)


class GrantClaims(Closed):
    version: Literal[1]
    iss: str = Field(min_length=1, max_length=500)
    sub: str = Field(min_length=1, max_length=200)
    aud: Literal["reality:email_dispatch"]
    jti: str = Field(min_length=1, max_length=200)
    tenant_id: str = Field(min_length=1, max_length=200)
    proposal_id: str = Field(min_length=1, max_length=200)
    approval_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: Literal["approve"]
    human_approved: Literal[True]
    iat: int = Field(ge=1)
    exp: int = Field(ge=1)


class CompanyMandate(Closed):
    subjects: dict[str, str]
    revoked_grant_ids: list[str] = Field(default_factory=list)
    revoked_before: int = Field(default=0, ge=0)


class IssuerTrust(Closed):
    keys: dict[str, str]
    tenants: dict[str, CompanyMandate]
