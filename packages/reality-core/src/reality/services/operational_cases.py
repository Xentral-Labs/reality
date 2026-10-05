"""Stable responsibility over accepted goals, without a second business ledger."""

import hashlib
import json

from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from reality.db.core import (
    AppUser,
    BusinessEvent,
    ChangeProposal,
    Commitment,
    Document,
    ImportJob,
    ReturnAnnouncement,
    SourceRecord,
    SourceStream,
    TenantEventProgress,
    TenantMembership,
    now,
    uid,
)
from reality.db.operational_cases import (
    CaseAdoption,
    CaseCommitmentLink,
    CaseConsumerCheckpoint,
    CaseProposalLink,
    CaseRollout,
    OperationalCase,
)
from reality.domain.operational_cases import KINDS, fulfillment_state, return_state
from reality.services import core
from reality.services.business_locks import lock_delivery_state
from reality.services.core import emit_business_event
from reality.services.memberships import Principal, require_owner


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def _member(session, tenant_id, principal):
    if principal is None:
        raise core.NotFound(code="company_not_found")
    tenant = core._tenant_record_read(session, core.Tenant, tenant_id, tenant_id)
    if tenant.archived_at is not None or tenant.purpose != "business":
        raise core.NotFound(code="company_not_found")
    user = session.scalar(
        select(AppUser).where(
            AppUser.id == principal.user_id, AppUser.status == "active"
        )
    )
    member = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == principal.user_id,
            TenantMembership.status == "active",
        )
    )
    if user is None or member is None:
        raise core.NotFound(code="company_not_found")
    return member


def schema_available(session):
    """Probe migration readiness without silently disabling responsibility guards."""
    if "operational_case_schema_available" not in session.info:
        session.info["operational_case_schema_available"] = inspect(
            session.connection()
        ).has_table("case_rollout")
    return session.info["operational_case_schema_available"]


def adoption(session: Session, tenant_id: str):
    if not schema_available(session):
        return None
    return session.get(CaseAdoption, tenant_id)


def _case(session, tenant_id, case_id, *, lock=False):
    query = (
        select(OperationalCase)
        .where(OperationalCase.tenant_id == tenant_id, OperationalCase.id == case_id)
        .execution_options(populate_existing=True)
    )
    if lock:
        query = query.with_for_update()
    found = session.scalar(query)
    if found is None:
        raise core.NotFound(code="case_not_found")
    return found


def coordination_enabled(session: Session, tenant_id: str) -> bool:
    if not schema_available(session):
        raise core.InvalidOperation(code="case_schema_not_ready")
    tenant = core._tenant_record_read(session, core.Tenant, tenant_id, tenant_id)
    return tenant.archived_at is None


def coordination_status(
    session: Session, tenant_id: str, *, principal: Principal | None = None
) -> dict:
    """
    BUSINESS PURPOSE:
    Report default coordination readiness and platform provenance without authorizing business actions.

    BUSINESS RULE services.operational_cases.coordination_status.result:
    Report completion only after bounded scans and current event catch-up; preserve tenant scope.
    """
    tenant = core._tenant_record_read(session, core.Tenant, tenant_id, tenant_id)
    can_control = principal is not None and tenant.purpose == "business"
    if can_control:
        _member(session, tenant_id, principal)
    ready = schema_available(session)
    rollout = (
        session.scalar(
            select(CaseRollout)
            .where(CaseRollout.tenant_id == tenant_id)
            .execution_options(populate_existing=True)
        )
        if ready
        else None
    )
    checkpoint = (
        session.scalar(
            select(CaseConsumerCheckpoint)
            .where(
                CaseConsumerCheckpoint.tenant_id == tenant_id,
                CaseConsumerCheckpoint.policy_version == 1,
            )
            .execution_options(populate_existing=True)
        )
        if ready
        else None
    )
    progress = (
        session.scalar(
            select(TenantEventProgress.last_event_sequence).where(
                TenantEventProgress.tenant_id == tenant_id
            )
        )
        or 0
    )
    from reality.db.scheduled_jobs import ScheduledJobRun

    latest = (
        session.scalar(
            select(ScheduledJobRun)
            .where(
                ScheduledJobRun.tenant_id == tenant_id,
                ScheduledJobRun.job_type == "operational_cases.reconcile",
            )
            .order_by(ScheduledJobRun.created_at.desc(), ScheduledJobRun.id.desc())
            .limit(1)
        )
        if ready
        else None
    )
    caught_up = checkpoint is not None and checkpoint.incorporated_sequence >= (
        progress
    )
    # reality-rule: services.operational_cases.coordination_status.result
    return {
        "adopted": True,
        "enabled": True,
        "can_adopt": False,
        "can_control": can_control,
        "migration_ready": ready,
        "coverage_ready": bool(rollout and rollout.completed_at and caught_up),
        "rollout_version": 377,
        "rollout_provenance": "platform_version",
        "last_job_status": latest.status if latest else None,
        "last_error_code": latest.last_error_code
        if latest
        else ("case_schema_not_ready" if not ready else None),
        "kinds": list(KINDS),
    }


def _rollout(session: Session, tenant_id: str) -> CaseRollout:
    # Caller holds the tenant delivery lock, shared with acceptance and guards.
    row = session.scalar(
        select(CaseRollout)
        .where(CaseRollout.tenant_id == tenant_id)
        .execution_options(populate_existing=True)
    )
    if row is None:
        row = CaseRollout(tenant_id=tenant_id)
        session.add(row)
    if session.get(CaseConsumerCheckpoint, (tenant_id, 1)) is None:
        progress = session.scalar(
            select(TenantEventProgress.last_event_sequence).where(
                TenantEventProgress.tenant_id == tenant_id
            )
        )
        capture = (
            progress
            if progress is not None
            else session.scalar(
                select(func.coalesce(func.max(BusinessEvent.sequence), 0)).where(
                    BusinessEvent.tenant_id == tenant_id
                )
            )
        )
        session.add(
            CaseConsumerCheckpoint(
                tenant_id=tenant_id, policy_version=1, incorporated_sequence=capture
            )
        )
    session.flush()
    return row


def _backfill(session: Session, tenant_id: str, rollout: CaseRollout, limit: int):
    remaining = limit
    if rollout.commitment_after is not None:
        ids = list(
            session.scalars(
                select(Commitment.id)
                .join(
                    Document,
                    (Document.tenant_id == Commitment.tenant_id)
                    & (Document.id == Commitment.document_id),
                )
                .where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.type == "customer_delivery",
                    Document.type == "sales_order",
                    Commitment.id > rollout.commitment_after,
                )
                .order_by(Commitment.id)
                .limit(remaining)
            )
        )
        for record_id in ids:
            ensure_commitment(session, tenant_id, record_id)
        rollout.commitment_after = ids[-1] if len(ids) == remaining else None
        remaining -= len(ids)
    if (
        remaining
        and rollout.commitment_after is None
        and rollout.return_after is not None
    ):
        ids = list(
            session.scalars(
                select(ReturnAnnouncement.id)
                .where(
                    ReturnAnnouncement.tenant_id == tenant_id,
                    ReturnAnnouncement.id > rollout.return_after,
                )
                .order_by(ReturnAnnouncement.id)
                .limit(remaining)
            )
        )
        for record_id in ids:
            ensure_return(session, tenant_id, record_id)
        rollout.return_after = ids[-1] if len(ids) == remaining else None
    session.flush()


def ensure_commitment(
    session: Session,
    tenant_id: str,
    commitment_id: str,
    *,
    newly_accepted: bool = False,
):
    if not coordination_enabled(session, tenant_id):
        return None
    commitment = core._tenant_record_read(session, Commitment, tenant_id, commitment_id)
    if commitment.type != "customer_delivery" or not commitment.document_id:
        return None
    document = core._tenant_record_read(
        session, Document, tenant_id, commitment.document_id
    )
    if document.type != "sales_order":
        return None
    lock_delivery_state(session, tenant_id)
    case = session.scalar(
        select(OperationalCase).where(
            OperationalCase.tenant_id == tenant_id,
            OperationalCase.order_document_id == document.id,
        )
    )
    if case is None:
        if (
            commitment.status != "open"
            or core.open_quantity(session, tenant_id, commitment.id) <= 0
        ):
            return None
        case = OperationalCase(
            id=uid("case"),
            tenant_id=tenant_id,
            kind="order_fulfillment",
            order_document_id=document.id,
        )
        session.add(case)
        session.flush()
    if session.get(CaseCommitmentLink, (tenant_id, case.id, commitment.id)) is None:
        session.add(
            CaseCommitmentLink(
                tenant_id=tenant_id, case_id=case.id, commitment_id=commitment.id
            )
        )
        session.flush()
    if newly_accepted:
        executing = core._executing.get()
        if executing is not None and executing[0] == tenant_id:
            bind_proposal(session, tenant_id, executing[1], [case.id])
    return case


def ensure_return(
    session: Session,
    tenant_id: str,
    announcement_id: str,
    *,
    newly_accepted: bool = False,
):
    if not coordination_enabled(session, tenant_id):
        return None
    announcement = core._tenant_record_read(
        session, ReturnAnnouncement, tenant_id, announcement_id
    )
    lock_delivery_state(session, tenant_id)
    case = session.scalar(
        select(OperationalCase).where(
            OperationalCase.tenant_id == tenant_id,
            OperationalCase.return_announcement_id == announcement.id,
        )
    )
    if case is None:
        if (
            announcement.status != "open"
            or core.announcement_outstanding(session, tenant_id, announcement) <= 0
        ):
            return None
        case = OperationalCase(
            id=uid("case"),
            tenant_id=tenant_id,
            kind="customer_return",
            return_announcement_id=announcement.id,
        )
        session.add(case)
        session.flush()
    if newly_accepted:
        executing = core._executing.get()
        if executing is not None and executing[0] == tenant_id:
            bind_proposal(session, tenant_id, executing[1], [case.id])
    return case


def object_cases(session: Session, tenant_id: str, record_type: str, record_id: str):
    """
    BUSINESS PURPOSE:
    Discover existing case identities through typed same-company business references without creating work.

    BUSINESS RULE services.operational_cases.object_cases.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    models = {
        "commitment": Commitment,
        "document": Document,
        "return_announcement": ReturnAnnouncement,
        "proposal": ChangeProposal,
    }
    if record_type not in models:
        raise core.InvalidOperation(code="case_object_unsupported")
    core._tenant_record_read(session, models[record_type], tenant_id, record_id)
    if not coordination_enabled(session, tenant_id):
        return []
    if record_type == "commitment":
        query = select(CaseCommitmentLink.case_id).where(
            CaseCommitmentLink.tenant_id == tenant_id,
            CaseCommitmentLink.commitment_id == record_id,
        )
    elif record_type == "proposal":
        query = select(CaseProposalLink.case_id).where(
            CaseProposalLink.tenant_id == tenant_id,
            CaseProposalLink.proposal_id == record_id,
        )
    else:
        field = (
            OperationalCase.order_document_id
            if record_type == "document"
            else OperationalCase.return_announcement_id
        )
        query = select(OperationalCase.id).where(
            OperationalCase.tenant_id == tenant_id, field == record_id
        )
    # reality-rule: services.operational_cases.object_cases.result
    return sorted(session.scalars(query))


def bind_proposal(
    session: Session, tenant_id: str, proposal_id: str | None, case_ids: list[str]
):
    lock_delivery_state(session, tenant_id)
    core._tenant_record_read(session, ChangeProposal, tenant_id, proposal_id)
    for case_id in sorted(set(case_ids)):
        case = _case(session, tenant_id, case_id, lock=True)
        if session.get(CaseProposalLink, (tenant_id, case_id, proposal_id)) is None:
            session.add(
                CaseProposalLink(
                    tenant_id=tenant_id,
                    case_id=case_id,
                    proposal_id=proposal_id,
                    bound_control_revision=case.control_revision,
                )
            )
    session.flush()


def _control_replay(session, tenant_id, action_type, request_key, arguments):
    # Request keys are bounded exact control identifiers, never business identity.
    if not isinstance(request_key, str) or not 1 <= len(request_key) <= 128:
        raise core.InvalidOperation(code="case_request_invalid")
    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import JSONB

    tool_type = "tool:operational_case_" + action_type.removeprefix("case:")
    prior = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type.in_((action_type, tool_type)),
            ChangeProposal.status == "executed",
            cast(ChangeProposal.input, JSONB)["request_key"].astext == request_key,
        )
    )
    if prior is not None:
        retained = json.loads(prior.input)
        if prior.type == tool_type:
            # Generic control proposals are the actual retained decision. Compare
            # canonical arguments, not preview metadata or caller actor labels.
            retained = {
                key: retained.get(key, [] if key in {"order_ids", "return_ids"} else "")
                for key in arguments
                if key != "actor"
            }
            for key in {"order_ids", "return_ids"} & retained.keys():
                retained[key] = sorted(set(retained[key]))
            retained["actor"] = prior.decided_by_user_id
        if retained != arguments:
            raise core.InvalidOperation(code="case_request_conflict")
        return json.loads(prior.output)
    return None


def _decision(session, tenant_id, action_type, principal, arguments, result):
    executing = core._executing.get()
    if executing is not None and executing[0] == tenant_id:
        return core._tenant_record_read(
            session, ChangeProposal, tenant_id, executing[1]
        )
    decision = ChangeProposal(
        id=uid("act"),
        tenant_id=tenant_id,
        type=action_type,
        actor_type="human",
        status="executed",
        input=json.dumps(arguments, sort_keys=True),
        output=json.dumps(result, sort_keys=True, default=str),
        decided_at=now(),
        decided_by_user_id=principal.user_id,
    )
    session.add(decision)
    session.flush()
    return decision


def adopt(
    session: Session,
    tenant_id: str,
    principal: Principal | None,
    *,
    confirmed: bool,
    request_key: str,
    order_ids: tuple[str, ...] | list[str] = (),
    return_ids: tuple[str, ...] | list[str] = (),
    _commit: bool = True,
):
    """
    BUSINESS PURPOSE:
    Acknowledge default coordination for legacy owner clients without altering responsibility or historical consent.

    BUSINESS RULE services.operational_cases.adopt.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    lock_delivery_state(session, tenant_id)
    if principal is None:
        raise core.NotFound(code="company_not_found")
    _member(session, tenant_id, principal)
    require_owner(session, tenant_id, principal)
    if not confirmed:
        raise core.InvalidOperation(code="review_confirmation_required")
    if len(order_ids) + len(return_ids) > 500:
        raise core.InvalidOperation(code="case_selection_too_large")
    args = {
        "request_key": request_key,
        "order_ids": sorted(set(order_ids)),
        "return_ids": sorted(set(return_ids)),
        "actor": principal.user_id,
    }
    replay = _control_replay(session, tenant_id, "case:adopt", request_key, args)
    if replay is not None:
        return replay
    for record_id in args["order_ids"]:
        doc = core._tenant_record_read(session, Document, tenant_id, record_id)
        if doc.type != "sales_order":
            raise core.InvalidOperation(code="case_object_unsupported")
    for record_id in args["return_ids"]:
        core._tenant_record_read(session, ReturnAnnouncement, tenant_id, record_id)
    # Deprecated compatibility acknowledgement. Never manufacture consent/history.
    result = {
        "policy_version": 1,
        **coordination_status(session, tenant_id, principal=principal),
    }
    if _commit:
        session.commit()
    # reality-rule: services.operational_cases.adopt.result
    return result


def _work(session, tenant_id, case):
    if case.kind == "order_fulfillment":
        rows = list(
            session.scalars(
                select(Commitment)
                .where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.document_id == case.order_document_id,
                    Commitment.type == "customer_delivery",
                )
                .order_by(Commitment.id)
            )
        )
        return rows
    announcement = core._tenant_record_read(
        session, ReturnAnnouncement, tenant_id, case.return_announcement_id
    )
    return [
        core._tenant_record_read(
            session, Commitment, tenant_id, announcement.commitment_id
        )
    ]


def _coverage_gaps(session, tenant_id, case):
    # Only authoritative order source streams relevant to this goal are required.
    gaps = []
    docs = {
        row.document_id for row in _work(session, tenant_id, case) if row.document_id
    }
    source_ids = set()
    for doc_id in sorted(docs):
        doc = core._tenant_record_read(session, Document, tenant_id, doc_id)
        if doc.source_record_id:
            source_ids.add(doc.source_record_id)
    if case.return_announcement_id:
        announcement = core._tenant_record_read(
            session, ReturnAnnouncement, tenant_id, case.return_announcement_id
        )
        if announcement.source_record_id:
            source_ids.add(announcement.source_record_id)
    for source_id in sorted(source_ids):
        source = core._tenant_record_read(session, SourceRecord, tenant_id, source_id)
        stream = session.scalar(
            select(SourceStream).where(
                SourceStream.tenant_id == tenant_id,
                SourceStream.source_system == source.source_system,
                SourceStream.source_type == source.source_type,
                SourceStream.external_id == source.external_id,
            )
        )
        if stream is None:
            continue
        job = session.scalar(
            select(ImportJob).where(
                ImportJob.tenant_id == tenant_id,
                ImportJob.source_record_id == stream.current_source_record_id,
            )
        )
        if (job is not None and job.status != "completed") or (
            job is None and stream.current_source_record_id != source.id
        ):
            gaps.append(
                {
                    "source_record_id": stream.current_source_record_id,
                    "status": job.status
                    if job is not None
                    else "interpretation_missing",
                }
            )
    return gaps


def explain(session: Session, tenant_id: str, case_id: str):
    """
    BUSINESS PURPOSE:
    Explain current work, ownership, source coverage, related goals and unresolved executions from held Reality.

    BUSINESS RULE services.operational_cases.explain.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    case = _case(session, tenant_id, case_id)
    commitments = _work(session, tenant_id, case)
    work = [
        {
            "commitment_id": row.id,
            "open_quantity": str(core.open_quantity(session, tenant_id, row.id)),
            "status": row.status,
        }
        for row in commitments
    ]
    related = []
    if case.kind == "order_fulfillment":
        ids = [row.id for row in commitments]
        related = list(
            session.scalars(
                select(OperationalCase.id)
                .join(
                    ReturnAnnouncement,
                    (ReturnAnnouncement.tenant_id == OperationalCase.tenant_id)
                    & (ReturnAnnouncement.id == OperationalCase.return_announcement_id),
                )
                .where(
                    OperationalCase.tenant_id == tenant_id,
                    ReturnAnnouncement.commitment_id.in_(ids),
                )
            )
        )
        state = fulfillment_state(work)
    else:
        ann = core._tenant_record_read(
            session, ReturnAnnouncement, tenant_id, case.return_announcement_id
        )
        state = return_state(ann.status)
        work = [
            {
                "commitment_id": ann.commitment_id,
                "return_announcement_id": ann.id,
                "open_quantity": str(
                    core.announcement_outstanding(session, tenant_id, ann)
                ),
                "status": ann.status,
            }
        ]
        for row in commitments:
            related.extend(object_cases(session, tenant_id, "commitment", row.id))
    links = list(
        session.scalars(
            select(CaseProposalLink)
            .where(
                CaseProposalLink.tenant_id == tenant_id,
                CaseProposalLink.case_id == case.id,
            )
            .order_by(CaseProposalLink.proposal_id)
        )
    )
    actions = []
    current_business_review = None
    for link in links:
        action = core._tenant_record_read(
            session, ChangeProposal, tenant_id, link.proposal_id
        )
        reason = None
        if action.status == "proposed":
            if link.bound_control_revision != case.control_revision:
                reason = "control_revision_changed"
            else:
                preview = json.loads(action.output)
                frozen = (
                    preview.get("_case_business_review", {}).get(case.id)
                    if isinstance(preview, dict)
                    else None
                )
                if frozen is not None:
                    if current_business_review is None:
                        current_business_review = business_review(
                            session, tenant_id, case.id
                        )
                    if frozen != current_business_review:
                        reason = (
                            "goal_no_longer_outstanding"
                            if state != "outstanding"
                            else "business_state_changed"
                        )
        actions.append(
            {
                "proposal_id": action.id,
                "status": action.status,
                "obsolete": reason is not None,
                "obsolescence_reason": reason,
            }
        )
    checkpoint = session.get(CaseConsumerCheckpoint, (tenant_id, 1))
    progress = (
        session.scalar(
            select(TenantEventProgress.last_event_sequence).where(
                TenantEventProgress.tenant_id == tenant_id
            )
        )
        or 0
    )
    from reality.db.scheduled_jobs import ScheduledJobRun

    latest_run = session.scalar(
        select(ScheduledJobRun)
        .where(
            ScheduledJobRun.tenant_id == tenant_id,
            ScheduledJobRun.job_type == "operational_cases.reconcile",
        )
        .order_by(ScheduledJobRun.created_at.desc(), ScheduledJobRun.id.desc())
        .limit(1)
    )
    # reality-rule: services.operational_cases.explain.result
    return {
        "consumer": {
            "latest_sequence": progress,
            "incorporated_sequence": checkpoint.incorporated_sequence
            if checkpoint
            else None,
            "last_job_status": latest_run.status if latest_run else None,
            "last_error_code": latest_run.last_error_code if latest_run else None,
        },
        "case_id": case.id,
        "kind": case.kind,
        "order_document_id": case.order_document_id,
        "return_announcement_id": case.return_announcement_id,
        "control_mode": case.control_mode,
        "control_revision": case.control_revision,
        "takeover_user_id": case.takeover_user_id,
        "goal_state": state,
        "work": work,
        "source_record_ids": sorted(
            {
                doc.source_record_id
                for row in commitments
                if row.document_id
                for doc in [
                    core._tenant_record_read(
                        session, Document, tenant_id, row.document_id
                    )
                ]
                if doc.source_record_id
            }
            | (
                {ann.source_record_id}
                if case.return_announcement_id and ann.source_record_id
                else set()
            )
        ),
        "unavailable_capabilities": [
            "live_shopify_transport",
            "refund_intent_execution",
        ],
        "related_case_ids": sorted(set(related)),
        "actions": actions,
        "unsettled_actions": [
            row["proposal_id"] for row in actions if row["status"] == "executing"
        ],
        "coverage_gaps": _coverage_gaps(session, tenant_id, case),
        "incorporated_sequence": checkpoint.incorporated_sequence
        if checkpoint
        else None,
    }


def list_cases(session: Session, tenant_id: str, *, after: str = "", limit: int = 100):
    """
    BUSINESS PURPOSE:
    Read a bounded page of same-company responsibility boundaries without creating goals.

    BUSINESS RULE services.operational_cases.list_cases.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    if not 1 <= limit <= 100:
        raise core.InvalidOperation(code="case_selection_too_large")
    core._tenant_record_read(session, core.Tenant, tenant_id, tenant_id)
    if not coordination_enabled(session, tenant_id):
        return []
    # reality-rule: services.operational_cases.list_cases.result
    return [
        explain(session, tenant_id, case_id)
        for case_id in session.scalars(
            select(OperationalCase.id)
            .where(OperationalCase.tenant_id == tenant_id, OperationalCase.id > after)
            .order_by(OperationalCase.id)
            .limit(limit)
        )
    ]


def takeover(
    session: Session,
    tenant_id: str,
    case_id: str,
    principal: Principal | None,
    *,
    expected_revision: int,
    request_key: str,
    confirmed: bool,
    reason: str = "",
    _commit: bool = True,
):
    """
    BUSINESS PURPOSE:
    Transfer responsibility to the authenticated active member, increasing the control revision so older automated starts are revoked.

    BUSINESS RULE services.operational_cases.takeover.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    lock_delivery_state(session, tenant_id)
    _member(session, tenant_id, principal)
    case = _case(session, tenant_id, case_id, lock=True)
    if not confirmed:
        raise core.InvalidOperation(code="review_confirmation_required")
    args = {
        "request_key": request_key,
        "case_id": case_id,
        "expected_revision": expected_revision,
        "reason": reason,
        "actor": principal.user_id,
    }
    replay = _control_replay(session, tenant_id, "case:takeover", request_key, args)
    if replay is not None:
        return replay
    if case.control_revision != expected_revision:
        raise core.InvalidOperation(code="case_review_stale")
    case.control_mode = "human"
    case.takeover_user_id = principal.user_id
    case.control_revision += 1
    session.flush()
    result = explain(session, tenant_id, case_id)
    decision = _decision(session, tenant_id, "case:takeover", principal, args, result)
    emit_business_event(
        session,
        tenant_id,
        "operational_case.taken_over",
        "operational_case",
        case_id,
        {"revision": case.control_revision, "reason": reason},
        action_id=decision.id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.operational_cases.takeover.result
    return result


def handback_preview(session: Session, tenant_id: str, case_id: str):
    """
    BUSINESS PURPOSE:
    Bind a handback review to the exact current held goal, source coverage and unresolved action set.

    BUSINESS RULE services.operational_cases.handback_preview.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    from reality.services.intake import _state
    from reality.services.shopify_intake import order_state

    result = explain(session, tenant_id, case_id)
    case = _case(session, tenant_id, case_id)
    state = {
        row.document_id: order_state(session, tenant_id, row.document_id)
        for row in _work(session, tenant_id, case)
        if row.document_id
    }
    if case.return_announcement_id:
        state["announcement"] = _state(
            core._tenant_record_read(
                session, ReturnAnnouncement, tenant_id, case.return_announcement_id
            )
        )
    # Consumer cursor is telemetry, not business meaning; worker catch-up alone does not invalidate review.
    relevant = {
        k: v
        for k, v in result.items()
        if k not in {"incorporated_sequence", "consumer"}
    }
    # reality-rule: services.operational_cases.handback_preview.result
    return {**result, "digest": _digest({"case": relevant, "state": state})}


def handback(
    session: Session,
    tenant_id: str,
    case_id: str,
    principal: Principal | None,
    *,
    review_digest: str,
    request_key: str,
    confirmed: bool,
    _commit: bool = True,
):
    """
    BUSINESS PURPOSE:
    Return responsibility after exact current human review, refusing unresolved sources or executing actions and preserving old action invalidation.

    BUSINESS RULE services.operational_cases.handback.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    lock_delivery_state(session, tenant_id)
    _member(session, tenant_id, principal)
    case = _case(session, tenant_id, case_id, lock=True)
    if not confirmed:
        raise core.InvalidOperation(code="review_confirmation_required")
    args = {
        "request_key": request_key,
        "case_id": case_id,
        "digest": review_digest,
        "actor": principal.user_id,
    }
    replay = _control_replay(session, tenant_id, "case:handback", request_key, args)
    if replay is not None:
        return replay
    current = handback_preview(session, tenant_id, case_id)
    if current["digest"] != review_digest or case.control_mode != "human":
        raise core.InvalidOperation(code="case_review_stale")
    if current["unsettled_actions"]:
        raise core.InvalidOperation(code="case_execution_unresolved")
    if current["coverage_gaps"]:
        raise core.InvalidOperation(code="case_source_unresolved")
    case.control_mode = "automation"
    case.takeover_user_id = None
    case.control_revision += 1
    session.flush()
    result = explain(session, tenant_id, case_id)
    decision = _decision(session, tenant_id, "case:handback", principal, args, result)
    emit_business_event(
        session,
        tenant_id,
        "operational_case.handed_back",
        "operational_case",
        case_id,
        {"revision": case.control_revision},
        action_id=decision.id,
    )
    if _commit:
        session.commit()
    # reality-rule: services.operational_cases.handback.result
    return result


def reconcile_events(
    session: Session, tenant_id: str, *, limit: int = 100, _commit: bool = True
):
    if not 1 <= limit <= 100:
        raise core.InvalidOperation(code="case_selection_too_large")
    lock_delivery_state(session, tenant_id)
    if not coordination_enabled(session, tenant_id):
        return 0
    rollout = _rollout(session, tenant_id)
    _backfill(session, tenant_id, rollout, limit)
    checkpoint = session.scalar(
        select(CaseConsumerCheckpoint)
        .where(
            CaseConsumerCheckpoint.tenant_id == tenant_id,
            CaseConsumerCheckpoint.policy_version == 1,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    events = list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.sequence > checkpoint.incorporated_sequence,
            )
            .order_by(BusinessEvent.sequence)
            .limit(limit)
        )
    )
    from reality.services.case_policies import reconcile_event

    for event in events:
        reconcile_event(session, tenant_id, event)
        checkpoint.incorporated_sequence = event.sequence
    progress = (
        session.scalar(
            select(TenantEventProgress.last_event_sequence).where(
                TenantEventProgress.tenant_id == tenant_id
            )
        )
        or 0
    )
    if (
        rollout.commitment_after is None
        and rollout.return_after is None
        and checkpoint.incorporated_sequence >= progress
        and rollout.completed_at is None
    ):
        rollout.completed_at = now()
    session.flush()
    if _commit:
        session.commit()
    return len(events)


def business_review(session: Session, tenant_id: str, case_id: str):
    """Exact held business prerequisites, excluding consumer progress and our own audit links."""
    from reality.services.intake import _state
    from reality.services.shopify_intake import order_state

    case = _case(session, tenant_id, case_id)
    states = {
        row.document_id: order_state(session, tenant_id, row.document_id)
        for row in _work(session, tenant_id, case)
        if row.document_id
    }
    if case.return_announcement_id:
        states["announcement"] = _state(
            core._tenant_record_read(
                session, ReturnAnnouncement, tenant_id, case.return_announcement_id
            )
        )
    return _digest(states)
