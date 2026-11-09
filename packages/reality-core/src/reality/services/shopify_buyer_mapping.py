"""Spec 389: recognized reviewed Source -> existing customer mapping, no order effects.

Uses only records/services present in schema99 as well as current Reality.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
    Document,
    ImportJob,
    MCPAccessToken,
    Party,
    PartyRole,
    SourceRecord,
    SourceStream,
)
from reality.domain.shopify_buyer_mapping import (
    ACTION_TYPE,
    APPROVAL_SOURCE,
    PURPOSE,
    BuyerMappingPolicy,
    CandidateInput,
    CommitInput,
    PrepareInput,
    StatusInput,
    canonical,
    decode64,
    digest,
    instant,
    nonce,
    proof_digest,
    verify_proof,
)
from reality.services import core
from reality.services.business_locks import lock_delivery_state

MESSAGES = {
    "unavailable": "This retained source is not available for buyer mapping under the current authority.",
    "basis": "The source or existing customer changed. Search again and review the current buyer mapping.",
    "approval": "This exact buyer mapping needs a current verified human approval from the trusted Main issuer.",
    "recorded": "A buyer mapping is already recorded for this source. Read the existing receipt; replacement needs a separate review.",
    "request": "This buyer-mapping request was already used for different review terms.",
}


def _unavailable():
    if hasattr(core.InvalidOperation, "_init_refusal"):
        return core.InvalidOperation(code="shopify_buyer_mapping_unavailable")
    return core.InvalidOperation(MESSAGES["unavailable"])


def _basis_changed():
    if hasattr(core.InvalidOperation, "_init_refusal"):
        return core.InvalidOperation(code="shopify_buyer_mapping_basis_changed")
    return core.InvalidOperation(MESSAGES["basis"])


def _approval_invalid():
    if hasattr(core.InvalidOperation, "_init_refusal"):
        return core.InvalidOperation(code="shopify_buyer_mapping_approval_invalid")
    return core.InvalidOperation(MESSAGES["approval"])


def _already_recorded():
    if hasattr(core.InvalidOperation, "_init_refusal"):
        return core.InvalidOperation(code="shopify_buyer_mapping_already_recorded")
    return core.InvalidOperation(MESSAGES["recorded"])


def _request_changed():
    if hasattr(core.InvalidOperation, "_init_refusal"):
        return core.InvalidOperation(code="shopify_buyer_mapping_request_changed")
    return core.InvalidOperation(MESSAGES["request"])


def _now() -> datetime:
    return datetime.now(UTC)


def _policy(
    tenant_id: str, supplied: BuyerMappingPolicy | None, *, historical: bool = False
) -> BuyerMappingPolicy:
    try:
        if supplied is None:
            path = Path(os.environ["REALITY_SHOPIFY_SOURCE_BUYER_MAPPING_POLICY_FILE"])
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                info = os.fstat(fd)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_mode & 0o077
                    or info.st_size > 65536
                ):
                    raise ValueError("private_policy_required")
                with os.fdopen(fd, "rb", closefd=False) as handle:
                    raw = handle.read(65537)
                supplied = BuyerMappingPolicy.model_validate_json(raw)
            finally:
                os.close(fd)
        if (
            supplied.tenant_id != tenant_id
            or len(set(supplied.allowed_subjects)) != len(supplied.allowed_subjects)
            or any(
                not subject or len(subject) > 200
                for subject in supplied.allowed_subjects
            )
            or len(decode64(supplied.public_key)) != 32
            or (not historical and _now() >= instant(supplied.expires_at))
        ):
            raise ValueError("policy_scope_unavailable")
        return supplied
    except (KeyError, OSError, ValueError, TypeError, ValidationError) as error:
        raise _unavailable() from error


def _input(model, raw):
    try:
        return model.model_validate(raw)
    except (ValueError, TypeError, ValidationError) as error:
        raise _unavailable() from error


def _submitter(session: Session, tenant_id: str, tool: str) -> str | None:
    """Transport token submits an exact proof; it is never the human approver."""
    from reality.mcp.principal import current_mcp_principal

    principal = current_mcp_principal()
    if principal is None:
        if os.environ.get("REALITY_AUTH_MODE") == "disabled":
            return None  # Trusted local/disposable service call, never a model tool bypass.
        raise _unavailable()
    if principal.tenant_id != tenant_id or principal.authentication_kind != "manual":
        raise _unavailable()
    token = session.scalar(
        select(MCPAccessToken)
        .where(
            MCPAccessToken.tenant_id == tenant_id,
            MCPAccessToken.id == principal.credential_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if (
        token is None
        or token.revoked_at is not None
        or tool not in json.loads(token.allowed_tools)
        and "*" not in json.loads(token.allowed_tools)
    ):
        raise _unavailable()
    return token.id


def _source(
    session: Session,
    tenant_id: str,
    policy: BuyerMappingPolicy,
    *,
    lock: bool = False,
    allow_mapped: bool = False,
):
    source_query = select(SourceRecord).where(
        SourceRecord.tenant_id == tenant_id, SourceRecord.id == policy.source_record_id
    )
    job_query = select(ImportJob).where(
        ImportJob.tenant_id == tenant_id, ImportJob.id == policy.import_job_id
    )
    stream_query = select(SourceStream).where(
        SourceStream.tenant_id == tenant_id,
        SourceStream.source_system == "shopify",
        SourceStream.source_type == "order_graphql",
        SourceStream.external_id == policy.order_id.rsplit("/", 1)[1],
    )
    if lock:
        stream_query = stream_query.with_for_update()
        source_query = source_query.with_for_update()
        job_query = job_query.with_for_update()
    stream = session.scalar(stream_query.execution_options(populate_existing=True))
    source = session.scalar(source_query.execution_options(populate_existing=True))
    job = session.scalar(job_query.execution_options(populate_existing=True))
    if (
        source is None
        or job is None
        or stream is None
        or stream.current_source_record_id != source.id
        or source.source_system != "shopify"
        or source.source_type != "order_graphql"
        or source.source_artifact_id is not None
        or source.payload_hash != policy.source_hash
        or source.version != policy.source_version
        or source.external_id != policy.order_id.rsplit("/", 1)[1]
        or job.source_record_id != source.id
        or job.status != "review_required"
    ):
        raise _basis_changed()
    context = json.loads(job.input)
    acquisition = context.get("acquisition") or {}
    raw = json.loads(source.payload)
    if (
        acquisition.get("shop") != policy.shop
        or acquisition.get("query_digest") != policy.query_digest
        or raw.get("id") != policy.order_id
        or context.get("customer_party_id")
        or context.get("intake_proposal_id")
    ):
        raise _basis_changed()
    if not allow_mapped and _approval_source(session, tenant_id, source.id) is not None:
        raise _already_recorded()
    accepted = session.scalar(
        select(Document.id)
        .where(
            Document.tenant_id == tenant_id,
            Document.source_record_id.in_(
                select(SourceRecord.id).where(
                    SourceRecord.tenant_id == tenant_id,
                    SourceRecord.source_system == "shopify",
                    SourceRecord.external_id == source.external_id,
                )
            ),
        )
        .limit(1)
    )
    if accepted:
        raise _basis_changed()
    binding = {
        "source_record_id": source.id,
        "import_job_id": job.id,
        "source_hash": source.payload_hash,
        "source_version": source.version,
        "external_id": source.external_id,
        "order_id": policy.order_id,
        "order_label": str(raw.get("name") or source.external_id)[:500],
        "shop": policy.shop,
        "query_digest": policy.query_digest,
    }
    return source, job, binding


def _customer(session: Session, tenant_id: str, party_id: str, *, lock: bool = False):
    query = select(Party).where(Party.tenant_id == tenant_id, Party.id == party_id)
    roles = (
        select(PartyRole.role)
        .where(PartyRole.tenant_id == tenant_id, PartyRole.party_id == party_id)
        .order_by(PartyRole.role)
    )
    if lock:
        query = query.with_for_update()
        roles = roles.with_for_update()
    party = session.scalar(query.execution_options(populate_existing=True))
    selected = list(session.scalars(roles))
    if party is None or not party.is_active or "customer" not in selected:
        raise _basis_changed()
    basis = {
        "party_id": party.id,
        "label": party.name,
        "type": party.type,
        "is_active": party.is_active,
        "roles": selected,
        "source_record_id": party.source_record_id,
    }
    return {"party_id": party.id, "label": party.name, "digest": digest(basis)}


def _approval_source(session: Session, tenant_id: str, source_id: str):
    stream = session.scalar(
        select(SourceStream).where(
            SourceStream.tenant_id == tenant_id,
            SourceStream.source_system == "tuesday",
            SourceStream.source_type == APPROVAL_SOURCE,
            SourceStream.external_id == source_id,
        )
    )
    if stream is None or stream.current_source_record_id is None:
        return None
    return session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.id == stream.current_source_record_id,
        )
    )


def buyer_candidates(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    *,
    policy: BuyerMappingPolicy | None = None,
):
    """
    BUSINESS PURPOSE:
    Inspect existing eligible customers for one exact retained source without creating buyer identity.

    BUSINESS RULE shopify_buyer_mapping.candidates:
    Require current source policy and bound source/job, then return a bounded active customer-role selection with minimal fresh identity digests.
    """
    # reality-rule: shopify_buyer_mapping.candidates
    value = _input(CandidateInput, arguments)
    trusted = _policy(tenant_id, policy)
    if (value.source_record_id, value.import_job_id) != (
        trusted.source_record_id,
        trusted.import_job_id,
    ):
        raise _unavailable()
    _, _, binding = _source(session, tenant_id, trusted, allow_mapped=True)
    statement = select(Party.id).where(
        Party.tenant_id == tenant_id,
        Party.is_active.is_(True),
        Party.id.in_(
            select(PartyRole.party_id).where(
                PartyRole.tenant_id == tenant_id, PartyRole.role == "customer"
            )
        ),
    )
    if value.query:
        statement = statement.where(Party.name.icontains(value.query, autoescape=True))
    ids = list(
        session.scalars(statement.order_by(Party.name, Party.id).limit(value.limit + 1))
    )
    items = [_customer(session, tenant_id, key) for key in ids[: value.limit]]
    return {
        "purpose": PURPOSE,
        "source_binding": binding,
        "observed_at": _now().isoformat(),
        "items": items,
        "has_more": len(ids) > value.limit,
        "coverage": "bounded_matching_existing_customers",
        "existing_mapping": get_verified_buyer_mapping(
            session, tenant_id, trusted.source_record_id, trusted.import_job_id
        ),
    }


def _action(session: Session, tenant_id: str, review_id: str, *, lock: bool = False):
    query = select(ChangeProposal).where(
        ChangeProposal.tenant_id == tenant_id,
        ChangeProposal.id == review_id,
        ChangeProposal.type == ACTION_TYPE,
    )
    if lock:
        query = query.with_for_update()
    action = session.scalar(query.execution_options(populate_existing=True))
    if action is None:
        raise _unavailable()
    review = json.loads(action.input)
    if (
        review.get("purpose") != PURPOSE
        or review.get("tenant_id") != tenant_id
        or review.get("review_id") != review_id
    ):
        raise _unavailable()
    return action, review


def _pending_view(review, *, expired: bool = False):
    return {
        "purpose": PURPOSE,
        "review_id": review["review_id"],
        "review_digest": digest(review),
        "expires_at": review["expires_at"],
        "state": "expired" if expired else "proposed",
        "source_binding": review["source_binding"],
        "customer": review["customer"],
        "business_effects_accepted": False,
        "original_source_unchanged": True,
        "import_job_input_unchanged": True,
        "sales_order_created": False,
    }


def prepare_buyer_mapping(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    *,
    policy: BuyerMappingPolicy | None = None,
):
    """
    BUSINESS PURPOSE:
    Freeze one proposed source-to-existing-buyer choice for a separate exact human decision.

    BUSINESS RULE shopify_buyer_mapping.prepare:
    Lock current source/customer evidence, preserve stable request identity and retain a mapping-only proposed Action without any accepted effects.
    """
    # reality-rule: shopify_buyer_mapping.prepare
    value = _input(PrepareInput, arguments)
    trusted = _policy(tenant_id, policy)
    try:
        nonce(value.request_id)
    except ValueError as error:
        raise _request_changed() from error
    if (
        value.source_record_id,
        value.import_job_id,
        value.source_hash,
        value.source_version,
    ) != (
        trusted.source_record_id,
        trusted.import_job_id,
        trusted.source_hash,
        trusted.source_version,
    ):
        raise _basis_changed()
    _submitter(session, tenant_id, "shopify_source_buyer_mapping_prepare")
    lock_delivery_state(session, tenant_id)
    _, _, binding = _source(session, tenant_id, trusted, lock=True)
    customer = _customer(session, tenant_id, value.customer_party_id, lock=True)
    if customer["digest"] != value.customer_digest:
        raise _basis_changed()
    review_id = (
        "act_sbm_"
        + hashlib.sha256(f"{tenant_id}\0{value.request_id}".encode()).hexdigest()[:32]
    )
    existing = session.scalar(
        select(ChangeProposal)
        .where(ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == review_id)
        .with_for_update()
    )
    if existing:
        action, review = _action(session, tenant_id, review_id)
        if (
            review["source_binding"] != binding
            or review["customer"] != customer
            or review["policy_digest"] != digest(trusted.model_dump())
        ):
            raise _request_changed()
        return (
            _pending_view(review, expired=_now() >= instant(review["expires_at"]))
            if action.status == "proposed"
            else buyer_mapping_status(
                session, tenant_id, {"review_id": review_id}, policy=trusted
            )
        )
    at = _now()
    expires = min(at + timedelta(minutes=5), instant(trusted.expires_at))
    review = {
        "version": 1,
        "purpose": PURPOSE,
        "review_id": review_id,
        "request_id": value.request_id,
        "tenant_id": tenant_id,
        "source_binding": binding,
        "customer": customer,
        "created_at": at.isoformat(),
        "expires_at": expires.isoformat(),
        "policy_digest": digest(trusted.model_dump()),
    }
    session.add(
        ChangeProposal(
            id=review_id,
            tenant_id=tenant_id,
            type=ACTION_TYPE,
            actor_type="agent",
            status="proposed",
            input=canonical(review),
            output=canonical({"state": "proposed"}),
        )
    )
    session.commit()
    return _pending_view(review)


def get_verified_buyer_mapping(
    session: Session, tenant_id: str, source_record_id: str, import_job_id: str
):
    """Recognized applied mapping from immutable approval + exact executed Action.

    This relationship grants no order/payment/stock authority. Its live basis is
    separately reported so historical human decisions never masquerade as fresh.
    """
    approved = _approval_source(session, tenant_id, source_record_id)
    if approved is None:
        return None
    payload = json.loads(approved.payload)
    review = payload.get("review") or {}
    if (
        review.get("source_binding", {}).get("source_record_id") != source_record_id
        or review.get("source_binding", {}).get("import_job_id") != import_job_id
    ):
        raise _basis_changed()
    action, retained = _action(session, tenant_id, review.get("review_id", ""))
    receipt = json.loads(action.output)
    if (
        action.status != "executed"
        or retained != review
        or receipt.get("review_digest") != digest(review)
        or receipt.get("approval_source_record_id") != approved.id
        or receipt.get("approval_source_hash") != approved.payload_hash
        or receipt.get("approval", {}).get("proof_digest")
        != proof_digest(payload.get("approval_proof", ""))
    ):
        raise _basis_changed()
    try:
        accepted_policy = BuyerMappingPolicy.model_validate(payload["trusted_policy"])
        recorded_at = instant(receipt["recorded_at"])
        if (
            accepted_policy.tenant_id != tenant_id
            or accepted_policy.source_record_id != source_record_id
            or accepted_policy.import_job_id != import_job_id
            or digest(accepted_policy.model_dump()) != review["policy_digest"]
            or recorded_at >= instant(accepted_policy.expires_at)
        ):
            raise ValueError("historical_authority_changed")
        claims = verify_proof(
            payload["approval_proof"],
            accepted_policy,
            action.id,
            digest(review),
            recorded_at,
        )
        if (
            receipt["source_binding"] != review["source_binding"]
            or receipt["customer"] != review["customer"]
            or receipt["approval"]["issuer"] != claims.iss
            or receipt["approval"]["subject"] != claims.sub
            or receipt["approval"]["jti"] != claims.jti
            or payload.get("approval_jti") != claims.jti
        ):
            raise ValueError("historical_approval_changed")
    except Exception as error:
        raise _basis_changed() from error
    customer_current = False
    source_current = False
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id, SourceRecord.id == source_record_id
        )
    )
    stream = session.scalar(
        select(SourceStream).where(
            SourceStream.tenant_id == tenant_id,
            SourceStream.source_system == "shopify",
            SourceStream.source_type == "order_graphql",
            SourceStream.external_id == review["source_binding"]["external_id"],
        )
    )
    job = session.scalar(
        select(ImportJob).where(
            ImportJob.tenant_id == tenant_id, ImportJob.id == import_job_id
        )
    )
    if source is not None and stream is not None and job is not None:
        source_current = (
            stream.current_source_record_id == source.id
            and source.payload_hash == review["source_binding"]["source_hash"]
            and source.version == review["source_binding"]["source_version"]
            and job.source_record_id == source.id
        )
    try:
        customer_current = (
            _customer(session, tenant_id, review["customer"]["party_id"])
            == review["customer"]
        )
    except core.InvalidOperation:
        pass
    return {
        "mapping_state": "applied_to_source",
        "customer": review["customer"],
        "approval_source_record_id": approved.id,
        "review_id": action.id,
        "review_digest": digest(review),
        "current_basis": {
            "source_current": source_current,
            "customer_current": customer_current,
        },
        "remaining_review": "full_intake_review_not_prepared",
    }


def buyer_mapping_status(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    *,
    policy: BuyerMappingPolicy | None = None,
):
    """
    BUSINESS PURPOSE:
    Read exact pending review or historical applied buyer mapping without dispatch.

    BUSINESS RULE shopify_buyer_mapping.status:
    Scope by authenticated tenant and host-pinned source; revalidate pending basis while preserving a recorded receipt after proof/review expiry.
    """
    # reality-rule: shopify_buyer_mapping.status
    value = _input(StatusInput, arguments)
    trusted = _policy(tenant_id, policy, historical=True)
    action, review = _action(session, tenant_id, value.review_id)
    if (
        review["source_binding"]["source_record_id"] != trusted.source_record_id
        or review["source_binding"]["import_job_id"] != trusted.import_job_id
    ):
        raise _unavailable()
    if action.status == "executed":
        verified = get_verified_buyer_mapping(
            session, tenant_id, trusted.source_record_id, trusted.import_job_id
        )
        if verified is None or verified["review_id"] != action.id:
            raise _basis_changed()
        return {**json.loads(action.output), "current_basis": verified["current_basis"]}
    if action.status != "proposed":
        raise _unavailable()
    if _now() >= instant(review["expires_at"]):
        return _pending_view(review, expired=True)
    if review["policy_digest"] != digest(trusted.model_dump()):
        raise _basis_changed()
    _, _, binding = _source(session, tenant_id, trusted)
    if (
        review["source_binding"] != binding
        or _customer(session, tenant_id, review["customer"]["party_id"])
        != review["customer"]
    ):
        raise _basis_changed()
    return _pending_view(review)


def commit_buyer_mapping(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    *,
    policy: BuyerMappingPolicy | None = None,
):
    """
    BUSINESS PURPOSE:
    Recognize only an issuer-attested exact Main human choice of an existing buyer, never accept an order.

    BUSINESS RULE shopify_buyer_mapping.commit:
    Recheck locked current source/customer and live trust/proof, retain immutable original approval, and record one source mapping while the import remains held.
    """
    # reality-rule: shopify_buyer_mapping.commit
    value = _input(CommitInput, arguments)
    trusted = _policy(tenant_id, policy, historical=True)
    token_id = _submitter(session, tenant_id, "shopify_source_buyer_mapping_commit")
    lock_delivery_state(session, tenant_id)
    action, review = _action(session, tenant_id, value.review_id, lock=True)
    if (
        review["source_binding"]["source_record_id"] != trusted.source_record_id
        or review["source_binding"]["import_job_id"] != trusted.import_job_id
        or digest(review) != value.review_digest
    ):
        raise _approval_invalid()
    if action.status == "executed":
        receipt = buyer_mapping_status(
            session, tenant_id, {"review_id": value.review_id}, policy=trusted
        )
        if receipt["approval"]["proof_digest"] != proof_digest(value.approval_proof):
            raise _approval_invalid()
        return receipt
    if action.status != "proposed":
        raise _approval_invalid()
    source, job, binding = _source(session, tenant_id, trusted, lock=True)
    customer = _customer(session, tenant_id, review["customer"]["party_id"], lock=True)
    # Re-read host trust after database waits; no proof or policy clock is frozen.
    latest = _policy(tenant_id, policy)
    if (
        review["policy_digest"] != digest(latest.model_dump())
        or review["source_binding"] != binding
        or review["customer"] != customer
        or _now() >= instant(review["expires_at"])
    ):
        raise _basis_changed()
    try:
        claims = verify_proof(
            value.approval_proof, latest, action.id, value.review_digest, _now()
        )
    except Exception as error:
        # Never include compact proof, credentials or parsing internals in errors.
        raise _approval_invalid() from error
    original_input = job.input
    approved_payload = {
        "version": 1,
        "purpose": PURPOSE,
        "review": review,
        "approval_proof": value.approval_proof,
        "verification": {
            "issuer": claims.iss,
            "subject": claims.sub,
            "key_id": latest.key_id,
            "public_key": latest.public_key,
            "policy_digest": review["policy_digest"],
        },
        "approval_jti": claims.jti,
        "trusted_policy": latest.model_dump(),
    }
    approved, created, disposition = core.store_source_record(
        session,
        tenant_id,
        "tuesday",
        APPROVAL_SOURCE,
        source.id,
        approved_payload,
        source_version_at=datetime.fromtimestamp(claims.iat, UTC),
    )
    if not created or disposition in {"stale", "conflict"}:
        raise _already_recorded()
    # Canonical Source storage may wait on its identity lock. Revalidate the
    # live policy and proof after that final wait, before accepting anything.
    at = _now()
    final_policy = _policy(tenant_id, policy)
    if digest(final_policy.model_dump()) != review["policy_digest"] or at >= instant(
        review["expires_at"]
    ):
        raise _approval_invalid()
    try:
        verify_proof(
            value.approval_proof, final_policy, action.id, value.review_digest, at
        )
    except (ValueError, TypeError, ValidationError) as error:
        raise _approval_invalid() from error
    receipt = {
        "purpose": PURPOSE,
        "review_id": action.id,
        "review_digest": value.review_digest,
        "expires_at": review["expires_at"],
        "state": "mapping_recorded",
        "source_binding": binding,
        "customer": customer,
        "approval_source_record_id": approved.id,
        "approval_source_hash": approved.payload_hash,
        "recorded_at": at.isoformat(),
        "approval": {
            "kind": "issuer_signed_main_human_review",
            "issuer": claims.iss,
            "subject": claims.sub,
            "jti": claims.jti,
            "proof_digest": proof_digest(value.approval_proof),
        },
        "business_effects_accepted": False,
        "original_source_unchanged": True,
        "import_job_input_unchanged": True,
        "sales_order_created": False,
        "remaining_review": "full_intake_review_not_prepared",
    }
    action.status = "executed"
    action.output = canonical(receipt)
    action.decided_at = at
    action.decided_by_user_id = None
    action.decided_via_token_id = token_id
    action.decided_via_channel = None
    job.attempts += 1
    job.status = "review_required"
    job.completed_at = None
    job.next_attempt_at = None
    job.error = canonical(
        {
            "phase": "buyer_mapping",
            "reason_code": "buyer_mapping_recorded_intake_pending",
            "mapping_review_id": action.id,
            "approval_source_record_id": approved.id,
            "summary": "An existing buyer was human-confirmed for this source. Full intake remains unprepared; no business order was accepted.",
        }
    )
    core._append_interpretation_outcome(
        session,
        tenant_id,
        source,
        job,
        job.attempts,
        "needs_review",
        interpreter_name=ACTION_TYPE,
        reason_code="buyer_mapping_recorded_intake_pending",
        summary="An existing buyer mapping is recorded. Full intake remains held; no business order was accepted.",
    )
    if job.input != original_input:
        raise _basis_changed()
    session.commit()
    return {
        **receipt,
        "current_basis": {"source_current": True, "customer_current": True},
    }
