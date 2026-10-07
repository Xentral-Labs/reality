"""Reviewed immutable planning evidence; no shipping or provider execution."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, NamedTuple

from pydantic import ValidationError
from sqlalchemy import cast, select, true
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Session, aliased

from reality.db.core import (
    ChangeProposal,
    Commitment,
    CommitmentRevision,
    Document,
    ImportJob,
    Location,
    ShippingCapacityWindow,
    ShippingDispatchRequirement,
    ShippingPlanStatement,
    SourceRecord,
    uid,
)
from reality.domain.shipping_performance import PlanInput
from reality.services import core
from reality.services.business_locks import lock_delivery_state
from reality.services.case_action_guards import human_principal
from reality.services.company_time_zone import company_time_zone_state
from reality.services.core import emit_business_event
from reality.services.memberships import require_owner
from reality.services.operational_cases import _member

SOURCE_SYSTEM = "internal_shipping_plan"
SOURCE_TYPE = "dispatch_plan"


class _StatementHeader(NamedTuple):
    tenant_id: str
    id: str
    source_record_id: str
    statement_kind: str
    dispatch_location_id: str
    business_day: date
    business_time_zone: str
    site_time_zone: str


class _StatementSource(NamedTuple):
    id: str
    external_id: str
    version: int
    statement_action_id: str | None


def statement_action_id(source: SourceRecord | _StatementSource) -> str | None:
    """Read the original accepted action reference, without copying a plan payload."""
    return (
        source.statement_action_id
        if isinstance(source, _StatementSource)
        else json.loads(source.payload).get("statement_id")
    )


def _source_basis_inputs(
    session: Session, tenant_id: str, source_ids: set[str]
) -> dict:
    """Read original source/current-intake metadata once for this exact company cohort."""
    columns = (
        SourceRecord.id,
        SourceRecord.source_system,
        SourceRecord.source_type,
        SourceRecord.external_id,
        SourceRecord.version,
        SourceRecord.payload_hash,
    )
    current = aliased(SourceRecord)
    current_columns = tuple(getattr(current, column.key) for column in columns)
    latest_source = (
        select(*current_columns)
        .where(
            current.tenant_id == SourceRecord.tenant_id,
            current.source_system == SourceRecord.source_system,
            current.source_type == SourceRecord.source_type,
            current.external_id == SourceRecord.external_id,
            current.version > SourceRecord.version,
        )
        .order_by(current.version.desc())
        .limit(1)
        .correlate(SourceRecord)
        .lateral()
    )
    rows = []
    latest = {}
    for combined in core._metadata_execute(
        session,
        select(*columns, *latest_source.c)
        .outerjoin(latest_source, true())
        .where(
            SourceRecord.tenant_id == tenant_id,
            core._id_cohort(SourceRecord.id, source_ids),
        ),
    ):
        original = tuple(combined[:6])
        current_row = original if combined[6] is None else tuple(combined[6:])
        rows.append(original)
        latest[original[1:4]] = current_row
    jobs = dict(
        core._metadata_execute(
            session,
            select(ImportJob.source_record_id, ImportJob.status).where(
                ImportJob.tenant_id == tenant_id,
                core._id_cohort(
                    ImportJob.source_record_id, {row[0] for row in latest.values()}
                ),
            ),
        ).all()
    )
    return {
        "session": session,
        "tenant_id": tenant_id,
        "source_ids": set(source_ids),
        "rows": {row[0]: row for row in rows},
        "latest": latest,
        "jobs": jobs,
    }


def source_basis(
    session: Session,
    tenant_id: str,
    source_ids: set[str],
    *,
    current_required: set[str] | None = None,
    _inputs: dict | None = None,
) -> dict:
    """Bind original evidence and current intake coverage; confirmations require exact current versions."""
    inputs = (
        _inputs
        if (
            session.info.get("operations_snapshot_consistent")
            and _inputs is not None
            and _inputs["session"] is session
            and _inputs["tenant_id"] == tenant_id
            and source_ids <= _inputs["source_ids"]
        )
        else _source_basis_inputs(session, tenant_id, source_ids)
    )
    rows = [row for identity, row in inputs["rows"].items() if identity in source_ids]
    if len(rows) != len(source_ids):
        raise core.NotFound(code="shipping_plan_reference_unavailable")
    latest, jobs = inputs["latest"], inputs["jobs"]
    exact = source_ids if current_required is None else current_required
    result = {}
    for identity, system, kind, external, version, payload_hash in rows:
        current = latest[(system, kind, external)]
        current_id, current_hash = current[0], current[5]
        status = jobs.get(current_id)
        # Match the existing case source-coverage contract: only completed intake
        # resolves a newer original-order statement. It cannot replace an exact
        # plan/capacity confirmation selected by the owner.
        if (status is not None and status != "completed") or (
            current_id != identity and (identity in exact or status != "completed")
        ):
            raise core.InvalidOperation(code="shipping_plan_source_unresolved")
        result[identity] = {
            "version": version,
            "payload_hash": payload_hash,
            "current_source_record_id": current_id,
            "current_payload_hash": current_hash,
            "current_intake_status": status,
        }
    return result


def current_statements(
    session: Session,
    tenant_id: str,
    *,
    business_day: date | None = None,
    location_id: str | None = None,
    _metadata_only: bool = False,
) -> list[
    tuple[ShippingPlanStatement | _StatementHeader, SourceRecord | _StatementSource]
]:
    """Read accepted versions per opaque stream, preserving withdrawal history."""
    narrow = _metadata_only and bool(session.info.get("operations_snapshot_consistent"))
    columns = (
        (
            *ShippingPlanStatement.__table__.columns,
            SourceRecord.id.label("original_source_id"),
            SourceRecord.external_id,
            SourceRecord.version,
            cast(SourceRecord.payload, JSON)["statement_id"].astext.label(
                "statement_action_id"
            ),
        )
        if narrow
        else (ShippingPlanStatement, SourceRecord)
    )
    query = (
        select(*columns)
        .join(
            SourceRecord,
            (SourceRecord.tenant_id == ShippingPlanStatement.tenant_id)
            & (SourceRecord.id == ShippingPlanStatement.source_record_id),
        )
        .where(
            ShippingPlanStatement.tenant_id == tenant_id,
            SourceRecord.tenant_id == tenant_id,
        )
    )
    if business_day is not None:
        query = query.where(ShippingPlanStatement.business_day == business_day)
    if location_id is not None:
        query = query.where(ShippingPlanStatement.dispatch_location_id == location_id)
    selected = {}
    observed_rows = (
        core._metadata_execute(session, query.order_by(SourceRecord.version))
        if narrow
        else session.execute(query.order_by(SourceRecord.version))
    )
    for row in observed_rows:
        statement, source = (
            (_StatementHeader(*row[:8]), _StatementSource(*row[8:])) if narrow else row
        )
        selected[source.external_id] = (statement, source)
    return list(selected.values())


def review_plan(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> tuple[dict, dict]:
    """
    BUSINESS PURPOSE:
    Prepare an exact shipping-plan review without accepting evidence or dispatching goods.

    BUSINESS RULE shipping_plans.review_plan.inputs:
    Require closed source-stated inputs, the current company calendar and same-company location.

    BUSINESS RULE shipping_plans.review_plan.current_scope:
    Require the exact current prior version for revision or withdrawal. Refuse competing active site/day plans or a requirement owned by another current plan.

    BUSINESS RULE shipping_plans.review_plan.meaning:
    Require live customer-delivery promises of sales orders and their full current canonical quantity. Bind the exact source versions and original payload hashes; newer unresolved evidence refuses review.
    """
    # reality-rule: shipping_plans.review_plan.inputs
    core.get_tenant(session, tenant_id)
    if set(arguments) - {"plan", "plan_id", "prior_source_record_id", "reviewed"}:
        raise core.InvalidOperation(code="shipping_plan_arguments_invalid")
    try:
        plan = PlanInput.model_validate(arguments.get("plan"))
    except ValidationError as error:
        raise core.InvalidOperation(code="shipping_plan_inputs_invalid") from error
    core._tenant_record(session, Location, tenant_id, plan.dispatch_location_id)
    zone = company_time_zone_state(session, tenant_id)["time_zone"]
    if plan.business_time_zone != zone:
        raise core.InvalidOperation(code="shipping_plan_calendar_changed")
    # reality-rule: shipping_plans.review_plan.current_scope
    plan_id = arguments.get("plan_id")
    prior = arguments.get("prior_source_record_id")
    current = current_statements(
        session,
        tenant_id,
        business_day=plan.business_day,
        location_id=plan.dispatch_location_id,
    )
    prior_pair = next(
        (
            (statement, source)
            for statement, source in current
            if source.external_id == plan_id
        ),
        None,
    )
    if plan_id is None:
        if prior is not None or plan.statement_kind == "withdrawal":
            raise core.InvalidOperation(code="shipping_plan_prior_required")
        plan_id = uid("shp")
    elif prior_pair is None or prior_pair[1].id != prior:
        raise core.InvalidOperation(code="shipping_plan_version_changed")
    if any(
        statement.statement_kind == "plan" and source.external_id != plan_id
        for statement, source in current
    ):
        raise core.InvalidOperation(code="shipping_plan_scope_conflict")
    ids = {row.commitment_id for row in plan.requirements}
    other_statement_ids = {
        statement.id
        for statement, source in current_statements(session, tenant_id)
        if statement.statement_kind == "plan" and source.external_id != plan_id
    }
    if (
        ids
        and other_statement_ids
        and session.scalar(
            select(ShippingDispatchRequirement.id)
            .where(
                ShippingDispatchRequirement.tenant_id == tenant_id,
                ShippingDispatchRequirement.statement_id.in_(other_statement_ids),
                ShippingDispatchRequirement.commitment_id.in_(ids),
            )
            .limit(1)
        )
    ):
        raise core.InvalidOperation(code="shipping_plan_requirement_conflict")
    # reality-rule: shipping_plans.review_plan.meaning
    commitments = {
        row.id: row
        for row in session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id, Commitment.id.in_(ids)
            )
        )
    }
    if len(commitments) != len(ids):
        raise core.NotFound(code="shipping_plan_commitment_unavailable")
    terms = core.commitment_terms(session, tenant_id, ids)
    quantity_revisions = {}
    for revision in session.scalars(
        select(CommitmentRevision)
        .where(
            CommitmentRevision.tenant_id == tenant_id,
            CommitmentRevision.commitment_id.in_(ids),
            CommitmentRevision.quantity.is_not(None),
        )
        .order_by(CommitmentRevision.stated_at, CommitmentRevision.id)
    ):
        quantity_revisions[revision.commitment_id] = revision
    documents = {
        row.id: row
        for row in session.scalars(
            select(Document).where(
                Document.tenant_id == tenant_id,
                Document.id.in_({row.document_id for row in commitments.values()}),
            )
        )
    }
    for requirement in plan.requirements:
        commitment = commitments[requirement.commitment_id]
        if (
            commitment.type != "customer_delivery"
            or commitment.cancelled_at
            or commitment.document_id not in documents
            or documents[commitment.document_id].type != "sales_order"
        ):
            raise core.InvalidOperation(code="shipping_plan_commitment_invalid")
        if requirement.quantity != terms[commitment.id].quantity:
            raise core.InvalidOperation(code="shipping_plan_quantity_changed")
    current_required = {
        window.confirmation_source_record_id
        for window in plan.capacity_windows
        if window.confirmation_source_record_id
    }
    sources = set(current_required)
    sources |= {
        row.source_record_id for row in documents.values() if row.source_record_id
    }
    sources |= {
        row.source_record_id
        for row in quantity_revisions.values()
        if row.source_record_id
    }
    if prior:
        sources.add(prior)
        current_required.add(prior)
    basis = {
        "prior_source_record_id": prior,
        "company_time_zone": zone,
        "sources": source_basis(
            session, tenant_id, sources, current_required=current_required
        ),
        "commitments": {
            identity: {
                "quantity": format(terms[identity].quantity, ".4f"),
                "quantity_revision_id": quantity_revisions[identity].id
                if identity in quantity_revisions
                else None,
                "document_id": commitments[identity].document_id,
                "location_id": commitments[identity].location_id,
                "cancelled_at": None,
            }
            for identity in sorted(ids)
        },
    }
    normalized = {
        "plan": arguments["plan"],
        "plan_id": plan_id,
        "prior_source_record_id": prior,
        "reviewed": basis,
    }
    return normalized, {
        "plan_id": plan_id,
        "stated_inputs": arguments["plan"],
        "basis": basis,
        "effect": "Retain planning evidence only; no stock, fulfillment, case or provider change.",
    }


def state_plan(session: Session, tenant_id: str, arguments: dict[str, Any]) -> dict:
    """
    BUSINESS PURPOSE:
    Retain an exact owner-confirmed shipping statement as immutable source-backed planning evidence.

    BUSINESS RULE shipping_plans.state_plan.authority:
    Require an observed current company owner and the common executing shipping-plan proposal. Lock the company delivery state before rechecking business meaning.

    BUSINESS RULE shipping_plans.state_plan.replay:
    An already accepted action returns its retained identities. A changed review basis refuses; no later plan is overwritten by replay.

    BUSINESS RULE shipping_plans.state_plan.evidence:
    Preserve the original stated plan payload in a versioned Source. Append its typed requirement/capacity evidence and a linked business event; do not dispatch, reserve, adopt a case or contact a provider.
    """
    # reality-rule: shipping_plans.state_plan.authority
    action_id = arguments.get("_action_id")
    principal = human_principal(session, tenant_id)
    require_owner(session, tenant_id, principal)
    proposal = core._tenant_record(session, ChangeProposal, tenant_id, action_id or "")
    if proposal.status != "executing" or proposal.type != "tool:shipping_plan_state":
        raise core.InvalidOperation(code="shipping_plan_review_required")
    lock_delivery_state(session, tenant_id)
    membership = _member(session, tenant_id, principal)
    session.refresh(membership)
    require_owner(session, tenant_id, principal)
    core._require_business_mutation(session, tenant_id, "state_shipping_plan")
    # reality-rule: shipping_plans.state_plan.replay
    for statement, source in current_statements(session, tenant_id):
        if json.loads(source.payload).get("statement_id") == action_id:
            return {
                "statement_id": statement.id,
                "source_record_id": source.id,
                "plan_id": source.external_id,
            }
    reviewed_args = {
        key: value for key, value in arguments.items() if key != "_action_id"
    }
    if reviewed_args.get("prior_source_record_id") is None:
        reviewed_args.pop("plan_id", None)
    normalized, _ = review_plan(session, tenant_id, reviewed_args)
    normalized["plan_id"] = arguments["plan_id"]
    if normalized["reviewed"] != arguments.get("reviewed"):
        raise core.InvalidOperation(code="shipping_plan_basis_changed")
    plan = PlanInput.model_validate(arguments["plan"])
    # reality-rule: shipping_plans.state_plan.evidence
    source, _, _ = core.store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        SOURCE_TYPE,
        normalized["plan_id"],
        {"plan": arguments["plan"], "statement_id": action_id},
    )
    statement = ShippingPlanStatement(
        tenant_id=tenant_id,
        id=uid("sps"),
        source_record_id=source.id,
        statement_kind=plan.statement_kind,
        dispatch_location_id=plan.dispatch_location_id,
        business_day=plan.business_day,
        business_time_zone=plan.business_time_zone,
        site_time_zone=plan.site_time_zone,
    )
    session.add(statement)
    session.flush()
    for row in plan.requirements:
        session.add(
            ShippingDispatchRequirement(
                tenant_id=tenant_id,
                id=uid("sdr"),
                statement_id=statement.id,
                **row.model_dump(),
            )
        )
    for row in plan.capacity_windows:
        session.add(
            ShippingCapacityWindow(
                tenant_id=tenant_id,
                id=uid("scw"),
                statement_id=statement.id,
                **row.model_dump(),
            )
        )
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "shipping_plan.stated",
        "shipping_plan_statement",
        statement.id,
        {
            "plan_id": normalized["plan_id"],
            "statement_kind": plan.statement_kind,
            "dispatch_location_id": plan.dispatch_location_id,
            "business_day": plan.business_day.isoformat(),
        },
        source_record_id=source.id,
        action_id=action_id,
    )
    return {
        "statement_id": statement.id,
        "source_record_id": source.id,
        "plan_id": normalized["plan_id"],
    }
