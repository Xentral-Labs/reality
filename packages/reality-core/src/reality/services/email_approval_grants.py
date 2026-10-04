"""Provider-neutral signed email approval recognition (spec 354).

Only operator-configured issuer/company/subject mandates authorize approval. The
submitting executor credential is never an identity or mandate for the approver.
"""

import base64
import binascii
import json
import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, SourceRecord, now
from reality.domain.email_approval_grants import (
    AcceptEmailGrant,
    GrantClaims,
    GrantHeader,
    IssuerTrust,
)
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    NotFound,
    enqueue_source,
    executing_proposal,
)
from reality.services.emails import (
    _hash,
    _validate,
    authorize_dispatch,
    prepare_dispatch,
)
from reality.services.tenant_policy import require_business_operation


def _json(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("Duplicate JSON member")
        data[key] = value
    return data


def _decode(value: str) -> bytes:
    result = base64.b64decode(
        value + "=" * (-len(value) % 4), altchars=b"-_", validate=True
    )
    if base64.urlsafe_b64encode(result).decode().rstrip("=") != value:
        raise ValueError("Noncanonical base64url")
    return result


def _verify(grant: str, tenant_id: str, proposal_id: str, digest: str):
    """Verify fixed-format proof against current server-owned authority, never the request."""
    try:
        encoded_header, encoded_claims, signature = grant.split(".")
        header = GrantHeader.model_validate(
            json.loads(_decode(encoded_header), object_pairs_hook=_json)
        )
        raw = json.loads(_decode(encoded_claims), object_pairs_hook=_json)
        # Python bool equals 1; Literal validation alone is insufficient here.
        if type(raw.get("version")) is not int or raw.get("human_approved") is not True:
            raise ValueError("Invalid v1 assurance")
        claims = GrantClaims.model_validate(raw)
        registry = json.loads(
            os.environ.get("REALITY_EMAIL_APPROVAL_TRUST_JSON", "{}"),
            object_pairs_hook=_json,
        )
        trust = IssuerTrust.model_validate(registry[claims.iss])
        mandate = trust.tenants[tenant_id]
        name = mandate.subjects[claims.sub]
        if not name.strip():
            raise ValueError("Unnamed mandated person")
        key = Ed25519PublicKey.from_public_bytes(_decode(trust.keys[header.kid]))
        key.verify(
            _decode(signature), f"{encoded_header}.{encoded_claims}".encode("ascii")
        )
        current = int(now().timestamp())
        if (
            claims.tenant_id != tenant_id
            or claims.proposal_id != proposal_id
            or claims.approval_digest != digest
            or claims.iat > current + 30
            or claims.exp <= current
            or not 0 < claims.exp - claims.iat <= 600
            or claims.iat <= mandate.revoked_before
            or claims.jti in mandate.revoked_grant_ids
        ):
            raise ValueError("Invalid grant binding, lifetime or authority")
        return (
            claims,
            name,
            {
                "algorithm": "EdDSA",
                "kid": header.kid,
                "public_key": trust.keys[header.kid],
                "verified_at": now().isoformat(),
                "mandate": "email_dispatch_authorize",
            },
        )
    except (
        ValueError,
        RecursionError,
        TypeError,
        KeyError,
        AttributeError,
        UnicodeError,
        binascii.Error,
        ValidationError,
        InvalidSignature,
    ) as error:
        raise InvalidOperation(code="email_approval_grant_invalid") from error


def _grant_source(session: Session, tenant_id: str, proposal: ChangeProposal):
    output = json.loads(proposal.output or "{}")
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.id == output.get("grant_source_id"),
            SourceRecord.source_system == "email_approval",
            SourceRecord.source_type == "email_approval_grant",
        )
    )
    if source is None or json.loads(source.payload)["proposal_id"] != proposal.id:
        raise InvalidOperation(code="email_approval_grant_invalid")
    return source


def _revalidate_claim(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> None:
    if proposal.decided_via_channel != "external_grant":
        return
    source = _grant_source(session, tenant_id, proposal)
    _verify(
        json.loads(source.payload)["grant"],
        tenant_id,
        proposal.id,
        _hash(json.loads(proposal.input)),
    )


def accept_grant(session: Session, tenant_id: str, arguments: dict):
    """
    BUSINESS PURPOSE:
    Recognize one exact externally approved email as an explainable Reality Decision.

    BUSINESS RULE email_approval_grants.accept_grant.boundary:
    Verify configured issuer/person authority and exact proof before atomically retaining
    its immutable Source and authorizing through the canonical email service. Serialize
    replay and competing decisions, roll back all effects on refusal, never send mail.
    """
    # reality-rule: email_approval_grants.accept_grant.boundary
    require_business_operation(session, tenant_id, "email_dispatch_accept_grant")
    request = _validate(AcceptEmailGrant, arguments)
    try:
        lock_delivery_state(session, tenant_id)
        proposal = session.scalar(
            select(ChangeProposal)
            .where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == request.proposal_id,
                ChangeProposal.type == "tool:email_dispatch_authorize",
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if proposal is None:
            raise NotFound(code="email_dispatch_not_found")
        data = json.loads(proposal.input)
        claims, name, verification = _verify(
            request.grant, tenant_id, proposal.id, _hash(data)
        )
        if data.get("retry_acknowledgements"):
            raise InvalidOperation(code="email_decision_required")
        identity = _hash([claims.iss, claims.jti])
        existing = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == "email_approval",
                SourceRecord.source_type == "email_approval_grant",
                SourceRecord.external_id == identity,
            )
        )
        if existing is not None:
            held = json.loads(existing.payload)
            if (
                held["grant"] == request.grant
                and held["proposal_id"] == proposal.id
                and proposal.status == "executed"
                and proposal.decided_via_channel == "external_grant"
                and json.loads(proposal.output).get("grant_source_id") == existing.id
            ):
                result = json.loads(proposal.output)
                session.commit()
                return result
            raise InvalidOperation(code="email_approval_grant_reused")
        if proposal.status != "proposed":
            raise InvalidOperation(code="email_decision_required")
        prepare_dispatch(session, tenant_id, data)
        source, _ = enqueue_source(
            session,
            tenant_id,
            "email_approval",
            "email_approval_grant",
            identity,
            {
                "grant": request.grant,
                "claims": claims.model_dump(),
                "name": name,
                "verification": verification,
                "proposal_id": proposal.id,
            },
            _commit=False,
        )
        with executing_proposal(tenant_id, proposal.id):
            result = authorize_dispatch(session, tenant_id, data)
        result |= {"proposal_id": proposal.id, "grant_source_id": source.id}
        proposal.status = "executed"
        proposal.decided_at = now()
        proposal.decided_by_user_id = None
        proposal.decided_via_token_id = None
        proposal.decided_via_channel = "external_grant"
        proposal.output = json.dumps(result, sort_keys=True)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
