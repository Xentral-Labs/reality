"""Owner-issued finite delegation and source-bound agent decisions (spec 355)."""

import base64
import hashlib
import json
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC

from pydantic import ValidationError
from sqlalchemy import Numeric, cast, event, func, select
from sqlalchemy.dialects.postgresql import JSONB

from reality.db.core import (
    AppUser,
    ChangeProposal,
    MCPAccessToken,
    SourceArtifact,
    SourceCapability,
    SourceRecord,
    SourceSystem,
    TenantMembership,
)
from reality.db.intake_review import IntakeReviewMandate
from reality.domain.intake import PreparedIntake, canonical_json
from reality.domain.intake_review import (
    MONEY_EFFECTS,
    AgentReviewEvidence,
    MandateGrant,
    MandateScope,
)
from reality.mcp.principal import current_mcp_principal
from reality.services import core
from reality.services.business_locks import lock_delivery_state
from reality.services.finance.accounts import lock_finance
from reality.services.memberships import Principal, require_owner

_change_scope = ContextVar("confirmed_intake_mandate_change", default=None)
_agent_scope = ContextVar("exact_intake_agent_decision", default=None)


@contextmanager
def _mandate_change_scope(session, tenant_id, proposal, principal, arguments):
    if principal is None:
        raise core.InvalidOperation(code="company_owner_access_required")
    require_owner(session, tenant_id, principal)
    lock_delivery_state(session, tenant_id)
    token = _change_scope.set(
        {
            "session": session,
            "transaction": session.get_transaction(),
            "tenant_id": tenant_id,
            "proposal_id": proposal.id,
            "operation": proposal.type,
            "principal": principal,
            "arguments": canonical_json(arguments),
        }
    )
    nested = session.get_nested_transaction()

    def deny_commit(_session):
        if (
            _session.get_nested_transaction() is not None
            and _session.get_nested_transaction() is not nested
        ):
            return
        raise core.InvalidOperation(code="intake_partial_commit_forbidden")

    event.listen(session, "before_commit", deny_commit)
    try:
        yield
    finally:
        event.remove(session, "before_commit", deny_commit)
        _change_scope.reset(token)


def _require_change(session, tenant_id, operation, arguments):
    scope = _change_scope.get()
    if (
        scope is None
        or scope["session"] is not session
        or scope["transaction"] is not session.get_transaction()
        or scope["tenant_id"] != tenant_id
        or scope["operation"] != operation
        or scope["arguments"] != canonical_json(arguments)
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    require_owner(session, tenant_id, scope["principal"])
    proposal = core._tenant_record_read(
        session, ChangeProposal, tenant_id, scope["proposal_id"]
    )
    if (
        proposal.status != "executing"
        or proposal.decided_by_user_id != scope["principal"].user_id
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    return proposal, scope["principal"]


def grant_review_mandate(
    session, tenant_id, agent_token_id, scope, expires_at, *, _commit=False
):
    """
    BUSINESS PURPOSE:
    Retain finite delegation only under an actual confirmed company-owner decision.

    BUSINESS RULE intake_agent.grant_mandate:
    Bind exact source scope, named owner-issued token and expiry to the same-tenant granting decision.
    """
    # reality-rule: intake_agent.grant_mandate
    if _commit:
        raise core.InvalidOperation(code="intake_partial_commit_forbidden")
    arguments = {
        "agent_token_id": agent_token_id,
        "scope": scope,
        "expires_at": expires_at,
    }
    proposal, principal = _require_change(
        session, tenant_id, "tool:intake_mandate_grant", arguments
    )
    try:
        request = MandateGrant.model_validate(arguments)
    except ValidationError as error:
        raise core.InvalidOperation(code="intake_review_invalid") from error
    if request.expires_at <= core.now():
        raise core.InvalidOperation(code="intake_review_stale")
    token = core._tenant_record_read(session, MCPAccessToken, tenant_id, agent_token_id)
    if token.revoked_at is not None or token.created_by_user_id != principal.user_id:
        raise core.InvalidOperation(code="intake_approval_required")
    system = core._tenant_record_read(
        session, SourceSystem, tenant_id, request.scope.source_system_id
    )
    if not system.is_active:
        raise core.InvalidOperation(code="intake_review_stale")
    for identity in request.scope.capability_ids:
        capability = session.scalar(
            select(SourceCapability)
            .where(
                SourceCapability.tenant_id == tenant_id, SourceCapability.id == identity
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if capability is None:
            raise core.NotFound(code="proposal_not_found")
        if not capability.is_active or capability.source_system_id != system.id:
            raise core.InvalidOperation(code="intake_review_stale")
    row = IntakeReviewMandate(
        id=core.uid("mandate"),
        tenant_id=tenant_id,
        grant_decision_id=proposal.id,
        agent_token_id=token.id,
        scope=request.scope.model_dump(mode="json"),
        expires_at=request.expires_at,
        revision=1,
        created_at=core.now(),
    )
    session.add(row)
    session.flush()
    if _commit:
        session.commit()
    return {
        "mandate_id": row.id,
        "revision": row.revision,
        "agent_token_id": token.id,
        "grant_decision_id": proposal.id,
        "expires_at": row.expires_at.isoformat(),
    }


def revoke_review_mandate(
    session, tenant_id, mandate_id, expected_revision, *, _commit=False
):
    """
    BUSINESS PURPOSE:
    End delegated review authority without rewriting prior decisions or receipts.

    BUSINESS RULE intake_agent.revoke_mandate:
    Require an exact confirmed owner request and current revision before retaining revocation.
    """
    # reality-rule: intake_agent.revoke_mandate
    if _commit:
        raise core.InvalidOperation(code="intake_partial_commit_forbidden")
    _require_change(
        session,
        tenant_id,
        "tool:intake_mandate_revoke",
        {"mandate_id": mandate_id, "expected_revision": expected_revision},
    )
    row = _mandate_row(session, tenant_id, mandate_id)
    if row.revision != expected_revision or row.revoked_at is not None:
        raise core.InvalidOperation(code="intake_review_stale")
    row.revoked_at = core.now()
    row.revision += 1
    session.flush()
    if _commit:
        session.commit()
    return {
        "mandate_id": row.id,
        "revision": row.revision,
        "revoked_at": row.revoked_at.isoformat(),
    }


def _mandate_row(session, tenant_id, mandate_id):
    row = session.scalar(
        select(IntakeReviewMandate)
        .where(
            IntakeReviewMandate.tenant_id == tenant_id,
            IntakeReviewMandate.id == mandate_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if row is None:
        raise core.NotFound(code="proposal_not_found")
    return row


def _authenticated_agent(tenant_id, tool_name):
    actual = current_mcp_principal()
    if (
        actual is None
        or actual.authentication_kind != "manual"
        or actual.tenant_id != tenant_id
        or not actual.permits(tool_name)
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    return actual.credential_id


def _current_mandate(
    session, tenant_id, mandate_id, token_id, revision=None, *, required_tool=None
):
    lock_delivery_state(session, tenant_id)
    lock_finance(session, tenant_id)
    row = _mandate_row(session, tenant_id, mandate_id)
    grant = core._tenant_record_read(
        session, ChangeProposal, tenant_id, row.grant_decision_id
    )
    token = session.scalar(
        select(MCPAccessToken)
        .where(MCPAccessToken.tenant_id == tenant_id, MCPAccessToken.id == token_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if token is None:
        raise core.NotFound(code="proposal_not_found")
    if (
        row.agent_token_id != token.id
        or row.revoked_at is not None
        or row.expires_at <= core.now()
        or revision is not None
        and revision != row.revision
        or token.revoked_at is not None
        or grant.type != "tool:intake_mandate_grant"
        or grant.status != "executed"
        or not grant.decided_by_user_id
        or token.created_by_user_id != grant.decided_by_user_id
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    permissions = json.loads(token.allowed_tools)
    if not {
        "*",
        "intake_agent_review_and_execute",
        "intake_agent_batch_review_and_queue",
    } & set(permissions):
        raise core.InvalidOperation(code="intake_approval_required")
    if (
        required_tool is not None
        and "*" not in permissions
        and required_tool not in permissions
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    principal = Principal(grant.decided_by_user_id)
    issuer = session.scalar(
        select(AppUser)
        .where(AppUser.id == principal.user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if issuer is None or issuer.status != "active":
        raise core.InvalidOperation(code="intake_approval_required")
    session.scalar(
        select(TenantMembership)
        .where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == principal.user_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    require_owner(session, tenant_id, principal)
    try:
        scope = MandateScope.model_validate(row.scope)
    except ValidationError as error:
        raise core.InvalidOperation(code="intake_review_invalid") from error
    return row, scope, principal


def _source_scope(session, tenant_id, plan, scope):
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, plan.source_record_id
    )
    root_id = plan.mapping.get("parent_source_id")
    original = (
        core._tenant_record_read(session, SourceRecord, tenant_id, root_id)
        if root_id
        else source
    )
    system = session.scalar(
        select(SourceSystem)
        .where(
            SourceSystem.tenant_id == tenant_id,
            SourceSystem.id == scope.source_system_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if system is None:
        raise core.NotFound(code="proposal_not_found")
    if not system.is_active or original.source_system != system.code:
        raise core.InvalidOperation(code="intake_approval_required")
    permitted = False
    for identity in scope.capability_ids:
        capability = session.scalar(
            select(SourceCapability)
            .where(
                SourceCapability.tenant_id == tenant_id, SourceCapability.id == identity
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if capability is None:
            raise core.NotFound(code="proposal_not_found")
        if (
            capability.is_active
            and capability.source_system_id == system.id
            and capability.source_type == original.source_type
        ):
            permitted = True
    if (
        not permitted
        or plan.profile not in scope.profiles
        or plan.row_count > scope.max_rows_per_unit
        or not {effect.operation for effect in plan.effects} <= set(scope.effects)
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    return source


SOURCE_PAGE_BYTES = 65536
SOURCE_REVIEW_BYTES = 20 * 1024 * 1024


def _streams(session, tenant_id, source, plan):
    payload = source.payload.encode("utf-8")
    if len(payload) > SOURCE_REVIEW_BYTES:
        raise core.InvalidOperation(code="intake_package_too_large")
    streams = {
        "source": {
            "bytes": payload,
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    }
    root_id = plan.mapping.get("parent_source_id")
    if root_id:
        root = core._tenant_record_read(session, SourceRecord, tenant_id, root_id)
        original = root.payload.encode("utf-8")
        if len(original) > SOURCE_REVIEW_BYTES:
            raise core.InvalidOperation(code="intake_package_too_large")
        streams["original"] = {
            "bytes": original,
            "size": len(original),
            "sha256": hashlib.sha256(original).hexdigest(),
        }
    if source.source_artifact_id:
        artifact = core._tenant_record_read(
            session, SourceArtifact, tenant_id, source.source_artifact_id
        )
        if not 0 < artifact.byte_size <= SOURCE_REVIEW_BYTES:
            raise core.InvalidOperation(code="intake_package_too_large")
        streams["artifact"] = {
            "artifact": artifact,
            "size": artifact.byte_size,
            "sha256": artifact.sha256,
        }
    return streams


def _coverage(session, tenant_id, source, plan):
    references = {f"source:{source.id}:{source.payload_hash}"}
    for kind, stream in _streams(session, tenant_id, source, plan).items():
        references.update(
            f"{kind}_bytes:{stream['sha256']}:{start}:{min(start + SOURCE_PAGE_BYTES, stream['size'])}"
            for start in range(0, stream["size"], SOURCE_PAGE_BYTES)
        )
    if source.source_artifact_id:
        numbers = plan.mapping.get("row_numbers") or list(range(2, plan.row_count + 2))
        references.update(f"row:{number}" for number in numbers)
    else:
        payload = json.loads(source.payload)
        references.update(
            f"line:{index}:{line.get('id', '')}"
            for index, line in enumerate(payload.get("line_items", []))
        )
    if len(references) > 1002:
        raise core.InvalidOperation(code="intake_package_too_large")
    return tuple(sorted(references))


def agent_review_source_page(
    session, tenant_id, mandate_id, proposal_id, *, stream="source", cursor=0
):
    """
    BUSINESS PURPOSE:
    Read original source bytes in bounded pages for complete external agent assessment.

    BUSINESS RULE intake_agent.source_page:
    Recheck current named-agent scope and return exact original byte ranges without normalization or business effects.
    """
    from reality.services.artifacts import materialize_artifact
    from reality.services.intake import review_intake

    # reality-rule: intake_agent.source_page
    token_id = _authenticated_agent(tenant_id, "intake_agent_review_source_page")
    _, scope, _ = _current_mandate(session, tenant_id, mandate_id, token_id)
    review = review_intake(session, tenant_id, proposal_id)
    plan = PreparedIntake.model_validate(review["plan"])
    source = _source_scope(session, tenant_id, plan, scope)
    streams = _streams(session, tenant_id, source, plan)
    if (
        stream not in streams
        or type(cursor) is not int
        or cursor < 0
        or cursor % SOURCE_PAGE_BYTES
        or cursor >= streams[stream]["size"]
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    held = streams[stream]
    if stream == "artifact":
        with materialize_artifact(held["artifact"]) as path:
            if path.stat().st_size != held["size"]:
                raise core.InvalidOperation(code="item_import_file_hash_mismatch")
            with path.open("rb") as original:
                original.seek(cursor)
                content = original.read(SOURCE_PAGE_BYTES)
    else:
        content = held["bytes"][cursor : cursor + SOURCE_PAGE_BYTES]
    end = cursor + len(content)
    return {
        "stream": stream,
        "source_record_id": source.id,
        "sha256": held["sha256"],
        "source_digest": source.payload_hash,
        "byte_size": held["size"],
        "cursor": cursor,
        "next_cursor": end if end < held["size"] else None,
        "reference": f"{stream}_bytes:{held['sha256']}:{cursor}:{end}",
        "encoding": "base64",
        "content": base64.b64encode(content).decode("ascii"),
    }


def _checks(session, tenant_id, proposal, plan):
    from reality.services.intake import _validate_current_plan

    state = "pass"
    try:
        _validate_current_plan(
            session,
            tenant_id,
            proposal,
            plan,
            lock_finance(session, tenant_id).revision,
        )
    except core.RealityError:
        state = "fail"
    return [
        {"code": code, "result": state if code == "current_state" else "pass"}
        for code in (
            "exact_source",
            "exact_plan",
            "full_source_coverage",
            "closed_effects",
            "current_state",
            "uncertainties",
        )
    ]


def agent_review_material(session, tenant_id, mandate_id, proposal_id):
    """
    BUSINESS PURPOSE:
    Expose complete source references, exact prepared meaning and server checks to the named agent.

    BUSINESS RULE intake_agent.review_material:
    Validate current delegation and return full review material without accepting business effects.
    """
    from reality.services.intake import review_intake

    # reality-rule: intake_agent.review_material
    token_id = _authenticated_agent(tenant_id, "intake_agent_review_material")
    mandate, scope, _ = _current_mandate(session, tenant_id, mandate_id, token_id)
    review = review_intake(session, tenant_id, proposal_id)
    plan = PreparedIntake.model_validate(review["plan"])
    source = _source_scope(session, tenant_id, plan, scope)
    proposal = core._tenant_record_read(session, ChangeProposal, tenant_id, proposal_id)
    return {
        "source": {
            "source_record_id": source.id,
            "payload_pages": [
                {
                    "stream": kind,
                    "byte_size": stream["size"],
                    "sha256": stream["sha256"],
                    "tool": "intake_agent_review_source_page",
                    "cursor": 0,
                }
                for kind, stream in _streams(session, tenant_id, source, plan).items()
            ],
            "artifact_id": source.source_artifact_id,
        },
        "review": review,
        "issues": list(plan.issues),
        "evidence_template": {
            "mandate_id": mandate.id,
            "revision": mandate.revision,
            "proposal_id": proposal.id,
            "digest": review["digest"],
            "source_digest": source.payload_hash,
            "reviewed_references": list(_coverage(session, tenant_id, source, plan)),
            "checks": _checks(session, tenant_id, proposal, plan),
        },
    }


def _stated_amount(plan, scope):
    required = bool({effect.operation for effect in plan.effects} & MONEY_EFFECTS)
    if not required:
        return None
    statements = [
        effect
        for effect in plan.effects
        if effect.operation
        in {"document", "customer_payment", "supplier_payment", "source_document"}
    ]
    if len(statements) != 1 or scope.amount_rule is None:
        raise core.InvalidOperation(code="intake_approval_required")
    statement = statements[0]
    value = statement.arguments.get(
        "gross_amount" if statement.operation == "document" else "amount"
    )
    currency = statement.arguments.get("currency")
    if value is None or currency != scope.amount_rule.currency:
        raise core.InvalidOperation(code="intake_approval_required")
    amount = core.decimal(value)
    if (
        not amount.is_finite()
        or amount < 0
        or amount > core.decimal(scope.amount_rule.max_amount_per_unit)
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    return str(amount)


def _quota(session, tenant_id, mandate, scope, stated_amount, *, units=1):
    day = core.now().astimezone(UTC).date().isoformat()
    receipt = cast(ChangeProposal.output, JSONB)["agent_review"]
    count, used = session.execute(
        select(
            func.count(),
            func.coalesce(
                func.sum(cast(receipt["source_stated_amount"].astext, Numeric())), 0
            ),
        ).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.status == "executed",
            receipt["mandate_id"].astext == mandate.id,
            receipt["revision"].astext == str(mandate.revision),
            receipt["quota_day"].astext == day,
        )
    ).one()
    if count + units > scope.max_units_per_day:
        raise core.InvalidOperation(code="intake_approval_required")
    if stated_amount is not None and used + core.decimal(stated_amount) > core.decimal(
        scope.amount_rule.max_amount_per_day
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    return day


def _current_agent_authorization(session, tenant_id, proposal_id):
    scope = _agent_scope.get()
    if scope is None:
        return None
    if (
        scope["session"] is not session
        or scope["transaction"] is not session.get_transaction()
        or scope["tenant_id"] != tenant_id
        or scope["proposal_id"] != proposal_id
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    return scope["authorization"]


@contextmanager
def _agent_execution_scope(session, tenant_id, proposal_id, authorization):
    token = _agent_scope.set(
        {
            "session": session,
            "transaction": session.get_transaction(),
            "tenant_id": tenant_id,
            "proposal_id": proposal_id,
            "authorization": authorization,
        }
    )
    try:
        yield
    finally:
        _agent_scope.reset(token)


def submit_agent_review(session, tenant_id, evidence, *, _commit=True):
    """
    BUSINESS PURPOSE:
    Settle one exact source review through current finite authority of the authenticated named agent.

    BUSINESS RULE intake_agent.submit_review:
    Validate complete evidence and current mandate; escalate uncertainty, enforce global quota and preserve token attribution.
    """
    from reality.services.intake import (
        apply_prepared_intake,
        reject_prepared_intake,
        review_intake,
    )

    # reality-rule: intake_agent.submit_review
    token_id = _authenticated_agent(tenant_id, "intake_agent_review_and_execute")
    try:
        evidence = AgentReviewEvidence.model_validate(evidence)
    except ValidationError as error:
        raise core.InvalidOperation(code="intake_review_invalid") from error
    mandate, scope, principal = _current_mandate(
        session,
        tenant_id,
        evidence.mandate_id,
        token_id,
        evidence.revision,
        required_tool="intake_agent_review_and_execute",
    )
    proposal = core._tenant_record_read(
        session, ChangeProposal, tenant_id, evidence.proposal_id
    )
    review = review_intake(session, tenant_id, proposal.id)
    plan = PreparedIntake.model_validate(review["plan"])
    source = _source_scope(session, tenant_id, plan, scope)
    if (
        evidence.digest != review["digest"]
        or evidence.source_digest != source.payload_hash
        or tuple(sorted(evidence.reviewed_references))
        != _coverage(session, tenant_id, source, plan)
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    held = evidence.model_dump(mode="json")
    if proposal.status in {"executed", "rejected"}:
        previous = json.loads(proposal.output).get("agent_review")
        if (
            previous is None
            or previous["evidence"] != held
            or previous["token_id"] != token_id
        ):
            raise core.InvalidOperation(code="intake_review_stale")
        return proposal
    actual_checks = _checks(session, tenant_id, proposal, plan)
    if sorted(held["checks"], key=lambda check: check["code"]) != sorted(
        actual_checks, key=lambda check: check["code"]
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    if evidence.verdict == "uncertain" or any(
        check["result"] != "pass" for check in actual_checks
    ):
        output = json.loads(proposal.output)
        reviews = output.get("agent_reviews", [])
        if held not in reviews:
            if len(reviews) >= 50:
                raise core.InvalidOperation(code="intake_package_too_large")
            proposal.output = canonical_json(
                {**output, "agent_reviews": [*reviews, held]}
            )
        if _commit:
            session.commit()
        else:
            session.flush()
        return proposal
    amount = _stated_amount(plan, scope) if evidence.verdict == "approve" else None
    day = (
        _quota(session, tenant_id, mandate, scope, amount)
        if evidence.verdict == "approve"
        else core.now().astimezone(UTC).date().isoformat()
    )
    authorization = {
        "mandate_id": mandate.id,
        "revision": mandate.revision,
        "token_id": token_id,
        "evidence": held,
        "source_stated_amount": amount,
        "currency": scope.amount_rule.currency if amount is not None else None,
        "quota_day": day,
    }
    with _agent_execution_scope(session, tenant_id, proposal.id, authorization):
        if evidence.verdict == "approve":
            return apply_prepared_intake(
                session,
                tenant_id,
                proposal.id,
                evidence.digest,
                confirmed=True,
                principal=principal,
                settling_token_id=token_id,
                _commit=_commit,
            )
        return reject_prepared_intake(
            session,
            tenant_id,
            proposal.id,
            principal=principal,
            settling_token_id=token_id,
            _commit=_commit,
        )


def _batch_evidence(session, tenant_id, evidence, scope):
    from reality.services.intake import review_intake

    review = review_intake(session, tenant_id, evidence.proposal_id)
    plan = PreparedIntake.model_validate(review["plan"])
    source = _source_scope(session, tenant_id, plan, scope)
    if (
        evidence.digest != review["digest"]
        or evidence.source_digest != source.payload_hash
        or tuple(sorted(evidence.reviewed_references))
        != _coverage(session, tenant_id, source, plan)
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    checks = _checks(
        session,
        tenant_id,
        core._tenant_record_read(
            session, ChangeProposal, tenant_id, evidence.proposal_id
        ),
        plan,
    )
    if sorted(
        evidence.model_dump(mode="json")["checks"], key=lambda check: check["code"]
    ) != sorted(checks, key=lambda check: check["code"]):
        raise core.InvalidOperation(code="intake_review_invalid")
    return plan, any(check["result"] != "pass" for check in checks)


def submit_agent_batch_review(session, tenant_id, evidence, *, _commit=True):
    """
    BUSINESS PURPOSE:
    Queue a fixed selection of complete external agent verdicts within current owner delegation.

    BUSINESS RULE intake_agent.submit_batch_review:
    Bind every child to the exact manifest and named token; uncertain evidence creates no execution authority.
    """
    from reality.domain.intake import content_digest
    from reality.domain.intake_review import AgentBatchReviewEvidence
    from reality.services import intake_batches
    from reality.services.scheduled_jobs import enqueue_intake_batch_run
    from reality.tools.application import _record_decision

    # reality-rule: intake_agent.submit_batch_review
    token_id = _authenticated_agent(tenant_id, "intake_agent_batch_review_and_queue")
    try:
        evidence = AgentBatchReviewEvidence.model_validate(evidence)
    except ValidationError as error:
        raise core.InvalidOperation(code="intake_review_invalid") from error
    retained = evidence.model_dump(mode="json")
    if len(canonical_json(retained).encode("utf-8")) > 2 * 1024 * 1024:
        raise core.InvalidOperation(code="intake_package_too_large")
    first = evidence.reviews[0]
    mandate, scope, principal = _current_mandate(
        session,
        tenant_id,
        first.mandate_id,
        token_id,
        first.revision,
        required_tool="intake_agent_batch_review_and_queue",
    )
    batch = intake_batches._batch(session, tenant_id, evidence.batch_id, lock=True)
    held, manifest = intake_batches._manifest(batch)
    if (
        evidence.manifest_digest != held["digest"]
        or evidence.manifest_revision != manifest.revision
        or [(review.proposal_id, review.digest) for review in evidence.reviews]
        != [(entry.proposal_id, entry.digest) for entry in manifest.entries]
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    if batch.status in {"executing", "executed"}:
        previous = (
            json.loads(batch.output).get("authorization", {}).get("agent_review", {})
        )
        if previous.get("evidence") != retained or previous.get("token_id") != token_id:
            raise core.InvalidOperation(code="intake_review_stale")
        return batch
    if batch.status != "proposed":
        raise core.InvalidOperation(code="proposal_no_longer_available")
    intake_batches._validate_file_selection(session, tenant_id, manifest)
    from reality.services.artifact_batches import _validate_selection

    _validate_selection(session, tenant_id, manifest)
    uncertain = False
    amounts = []
    for review in evidence.reviews:
        child = core._tenant_record_read(
            session, ChangeProposal, tenant_id, review.proposal_id
        )
        if child.status != "proposed":
            raise core.InvalidOperation(code="intake_review_stale")
        plan, failed = _batch_evidence(session, tenant_id, review, scope)
        uncertain |= failed or review.verdict == "uncertain"
        if review.verdict == "approve" and not failed:
            amounts.append(_stated_amount(plan, scope))
    if uncertain:
        output = json.loads(batch.output)
        reviews = output.get("agent_reviews", [])
        if retained not in reviews:
            if len(reviews) >= 5:
                raise core.InvalidOperation(code="intake_package_too_large")
            batch.output = canonical_json(
                {**output, "agent_reviews": [*reviews, retained]}
            )
        if _commit:
            session.commit()
        else:
            session.flush()
        return batch
    stated = [core.decimal(amount) for amount in amounts if amount is not None]
    if amounts:
        _quota(
            session,
            tenant_id,
            mandate,
            scope,
            str(sum(stated, core.ZERO)) if stated else None,
            units=len(amounts),
        )
    authorization = {
        "batch_id": batch.id,
        "manifest_revision": manifest.revision,
        "manifest_digest": held["digest"],
        "reviewer_user_id": principal.user_id,
        "token_id": token_id,
        "channel": None,
        "authorized_at": core.now().isoformat(),
        "agent_review": {
            "mandate_id": mandate.id,
            "revision": mandate.revision,
            "token_id": token_id,
            "evidence": retained,
        },
    }
    _record_decision(batch, None, token_id, None)
    batch.status = "executing"
    batch.output = canonical_json(
        {
            "authorization": authorization,
            "authorization_digest": content_digest(authorization),
            "next_index": 0,
            "continuation_id": core.uid("cont"),
            "results": [],
            "stopped": False,
        }
    )
    session.flush()
    enqueue_intake_batch_run(session, tenant_id, batch.id)
    if _commit:
        session.commit()
    return batch


def _settle_agent_batch_child(session, tenant_id, proposal_id, authorization):
    from reality.domain.intake_review import AgentBatchReviewEvidence
    from reality.services.intake import apply_prepared_intake, reject_prepared_intake
    from reality.services.intake_batches import _current_child_authorization

    if (
        _current_child_authorization(session, tenant_id, proposal_id)
        is not authorization
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    retained = authorization["agent_review"]
    evidence = AgentBatchReviewEvidence.model_validate(retained["evidence"])
    review = next(
        (review for review in evidence.reviews if review.proposal_id == proposal_id),
        None,
    )
    if review is None or review.verdict not in {"approve", "reject"}:
        raise core.InvalidOperation(code="intake_approval_required")
    token_id = retained["token_id"]
    mandate, scope, principal = _current_mandate(
        session,
        tenant_id,
        review.mandate_id,
        token_id,
        review.revision,
        required_tool="intake_agent_batch_review_and_queue",
    )
    child = core._tenant_record_read(session, ChangeProposal, tenant_id, proposal_id)
    if child.status in {"executed", "rejected"}:
        receipt = json.loads(child.output).get("agent_review", {})
        if (
            receipt.get("evidence") != review.model_dump(mode="json")
            or receipt.get("token_id") != token_id
        ):
            raise core.InvalidOperation(code="intake_review_stale")
        return "replayed" if child.status == "executed" else "rejected"
    plan, failed = _batch_evidence(session, tenant_id, review, scope)
    if failed:
        raise core.InvalidOperation(code="intake_review_stale")
    amount = _stated_amount(plan, scope) if review.verdict == "approve" else None
    day = (
        _quota(session, tenant_id, mandate, scope, amount)
        if review.verdict == "approve"
        else core.now().astimezone(UTC).date().isoformat()
    )
    authority = {
        "mandate_id": mandate.id,
        "revision": mandate.revision,
        "token_id": token_id,
        "evidence": review.model_dump(mode="json"),
        "source_stated_amount": amount,
        "currency": scope.amount_rule.currency if amount is not None else None,
        "quota_day": day,
    }
    with _agent_execution_scope(session, tenant_id, proposal_id, authority):
        if review.verdict == "approve":
            apply_prepared_intake(
                session,
                tenant_id,
                proposal_id,
                review.digest,
                confirmed=True,
                principal=principal,
                settling_token_id=token_id,
                _commit=False,
            )
            return "applied"
        reject_prepared_intake(
            session,
            tenant_id,
            proposal_id,
            principal=principal,
            settling_token_id=token_id,
            _commit=False,
        )
        return "rejected"
