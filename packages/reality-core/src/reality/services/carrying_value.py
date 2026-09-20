"""Source-backed carrying-value assessments over one retained inventory review."""

from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, SourceRecord, now, uid
from reality.db.inventory_costing import (
    CostInventoryMember,
    CostInventoryReview,
    CostMovementBasis,
    CostPolicyRevision,
    CostValuationAssessmentPart,
    CostValuationAssessmentRevision,
)
from reality.domain.carrying_value import (
    AssessmentPart,
    CarryingValueRefusal,
    reconcile_assessment,
)
from reality.services import core

STEP = Decimal("0.0001")


def _money(value: Decimal) -> str:
    return format(value.quantize(STEP, rounding=ROUND_HALF_EVEN), "f")


def _row(session: Session, model, tenant: str, identity: str):
    row = session.scalar(
        select(model).where(model.tenant_id == tenant, model.id == identity)
    )
    if row is None:
        raise core.NotFound("Costing scope not found.")
    return row


def _inventory_part(session: Session, tenant: str, review: dict, request_part):
    member = _row(
        session, CostInventoryMember, tenant, request_part.inventory_member_id
    )
    if member.review_id != review["review_id"]:
        raise core.NotFound("Costing scope not found.")
    basis = _row(session, CostMovementBasis, tenant, member.movement_basis_id)
    remaining = [
        part
        for part in review["remaining"]
        if part["entry_movement_id"] == basis.movement_id
    ]
    if len(remaining) != 1:
        raise core.InvalidOperation("Assessment member is not exact remaining inventory.")
    retained = remaining[0]
    available = Decimal(retained["quantity"])
    quantity = request_part.quantity
    if quantity > available:
        raise core.InvalidOperation("Assessment quantity exceeds remaining inventory.")
    acquisition = (Decimal(retained["cost"]) * quantity / available).quantize(
        STEP, rounding=ROUND_HALF_EVEN
    )
    _row(
        session,
        SourceRecord,
        tenant,
        request_part.evidence_source_record_id,
    )
    if request_part.currency != review["currency"]:
        raise core.InvalidOperation("Assessment currency differs from inventory currency.")
    return AssessmentPart(
        inventory_member_id=member.id,
        quantity=quantity,
        acquisition_value=acquisition,
        assessed_value=request_part.assessed_value,
    )


def _previous_parts(session: Session, tenant: str, request, review: dict):
    if not request.supersedes_id:
        return None, None
    previous = _row(
        session,
        CostValuationAssessmentRevision,
        tenant,
        request.supersedes_id,
    )
    if previous.inventory_review_id != review["review_id"]:
        raise core.NotFound("Costing scope not found.")
    latest = session.scalar(
        select(CostValuationAssessmentRevision)
        .where(
            CostValuationAssessmentRevision.tenant_id == tenant,
            CostValuationAssessmentRevision.inventory_review_id == review["review_id"],
        )
        .order_by(CostValuationAssessmentRevision.revision.desc())
        .limit(1)
    )
    if latest is None or latest.id != previous.id:
        raise core.Conflict("Assessment predecessor is stale.")
    rows = list(
        session.scalars(
            select(CostValuationAssessmentPart).where(
                CostValuationAssessmentPart.tenant_id == tenant,
                CostValuationAssessmentPart.assessment_revision_id == previous.id,
            )
        )
    )
    acquisition = {
        part.inventory_member_id: part.acquisition_value
        for part in (
            _inventory_part(session, tenant, review, requested)
            for requested in request.parts
        )
    }
    return previous, [
        AssessmentPart(
            inventory_member_id=row.inventory_member_id,
            quantity=row.quantity,
            acquisition_value=acquisition.get(row.inventory_member_id, Decimal(-1)),
            assessed_value=row.assessed_value,
        )
        for row in rows
    ]


def _check(session: Session, tenant: str, request) -> dict:
    from reality.services.costing import inventory_cost

    retained = _row(
        session, CostInventoryReview, tenant, request.inventory_review_id
    )
    review = inventory_cost(
        session,
        tenant,
        _row(session, CostPolicyRevision, tenant, retained.policy_id).item_id,
        review_id=retained.id,
    )
    if request.effective_at != retained.effective_at:
        raise core.InvalidOperation("Assessment cutoff differs from inventory review.")
    existing = session.scalar(
        select(CostValuationAssessmentRevision.id)
        .where(
            CostValuationAssessmentRevision.tenant_id == tenant,
            CostValuationAssessmentRevision.inventory_review_id == retained.id,
        )
        .limit(1)
    )
    if request.kind == "write_down" and existing:
        raise core.Conflict("Inventory review already has an assessment history.")
    parts = [_inventory_part(session, tenant, review, part) for part in request.parts]
    previous, previous_parts = _previous_parts(session, tenant, request, review)
    try:
        result = reconcile_assessment(request.kind, parts, previous=previous_parts)
    except CarryingValueRefusal as error:
        raise core.InvalidOperation(str(error)) from error
    return {
        "inventory_review_id": retained.id,
        "previous_assessment_id": previous.id if previous else None,
        "assessment": {
            "acquisition_value": _money(result.acquisition_value),
            "assessed_value": _money(result.carrying_value),
            "adjustment": _money(result.adjustment),
            "quantity": _money(sum((part.quantity for part in result.parts), Decimal(0))),
        },
    }


def _execute(session: Session, tenant: str, request, checked: dict, event, action) -> dict:
    from reality.services.costing import _hash

    previous = (
        _row(
            session,
            CostValuationAssessmentRevision,
            tenant,
            checked["previous_assessment_id"],
        )
        if checked["previous_assessment_id"]
        else None
    )
    revision = previous.revision + 1 if previous else 1
    row = CostValuationAssessmentRevision(
        id=uid("cva"),
        tenant_id=tenant,
        inventory_review_id=request.inventory_review_id,
        revision=revision,
        supersedes_id=previous.id if previous else None,
        kind=request.kind,
        effective_at=request.effective_at,
        target_event_sequence=request.expected_event_sequence,
        knowledge_at=now(),
        introduced_event_id=event.id,
        action_id=action.id,
        reason=request.reason,
        input_schema_version=1,
        content_hash="building",
    )
    session.add(row)
    session.flush()
    retained_parts = []
    for requested in request.parts:
        part = CostValuationAssessmentPart(
            id=uid("cvp"),
            tenant_id=tenant,
            assessment_revision_id=row.id,
            inventory_member_id=requested.inventory_member_id,
            evidence_source_record_id=requested.evidence_source_record_id,
            quantity=requested.quantity,
            assessed_value=requested.assessed_value,
            currency=requested.currency,
            input_schema_version=1,
        )
        session.add(part)
        retained_parts.append(
            {
                "inventory_member_id": part.inventory_member_id,
                "evidence_source_record_id": part.evidence_source_record_id,
                "quantity": str(part.quantity),
                "assessed_value": str(part.assessed_value),
                "currency": part.currency,
            }
        )
    session.flush()
    row.content_hash = _hash(
        {
            "inventory_review_id": row.inventory_review_id,
            "revision": row.revision,
            "supersedes_id": row.supersedes_id,
            "kind": row.kind,
            "effective_at": row.effective_at.isoformat(),
            "target_event_sequence": row.target_event_sequence,
            "parts": retained_parts,
        }
    )
    session.flush()
    return {
        "assessment_revision_id": row.id,
        "inventory_review_id": row.inventory_review_id,
        "revision": revision,
        "kind": row.kind,
        "assessment": checked["assessment"],
    }


def review_unchanged_by_assessments(
    session: Session, tenant: str, review_id: str, after: int, through: int
) -> bool:
    """Prove the complete later event interval contains only this review's assessments."""
    if through <= after:
        return True
    events = list(
        session.scalars(
            select(BusinessEvent.id)
            .where(
                BusinessEvent.tenant_id == tenant,
                BusinessEvent.sequence > after,
                BusinessEvent.sequence <= through,
            )
            .order_by(BusinessEvent.sequence)
        )
    )
    if len(events) != through - after:
        return False
    assessment_events = set(
        session.scalars(
            select(CostValuationAssessmentRevision.introduced_event_id).where(
                CostValuationAssessmentRevision.tenant_id == tenant,
                CostValuationAssessmentRevision.inventory_review_id == review_id,
            )
        )
    )
    return bool(events) and set(events) <= assessment_events


def enrich_inventory_result(
    session: Session,
    tenant: str,
    result: dict,
    *,
    assessment_revision_id: str | None = None,
) -> dict:
    """Derive one carrying bridge from retained assessment authority without writes."""
    if result["review_state"] == "stale":
        return {
            **result,
            "carrying_value": None,
            "carrying_adjustment": None,
            "carrying_value_state": "inventory_review_stale",
            "valuation_assessment": None,
        }
    statement = select(CostValuationAssessmentRevision).where(
        CostValuationAssessmentRevision.tenant_id == tenant,
        CostValuationAssessmentRevision.inventory_review_id == result["review_id"],
    )
    if assessment_revision_id:
        statement = statement.where(
            CostValuationAssessmentRevision.id == assessment_revision_id
        )
    else:
        statement = statement.order_by(
            CostValuationAssessmentRevision.revision.desc()
        ).limit(1)
    assessment = session.scalar(statement)
    if assessment is None:
        if assessment_revision_id:
            raise core.NotFound("Costing scope not found.")
        return {
            **result,
            "carrying_value": None,
            "carrying_adjustment": None,
            "carrying_value_state": "assessment_missing",
            "valuation_assessment": None,
        }
    rows = list(
        session.scalars(
            select(CostValuationAssessmentPart)
            .where(
                CostValuationAssessmentPart.tenant_id == tenant,
                CostValuationAssessmentPart.assessment_revision_id == assessment.id,
            )
            .order_by(CostValuationAssessmentPart.inventory_member_id)
        )
    )
    current_parts = [_inventory_part(session, tenant, result, row) for row in rows]
    previous_parts = None
    if assessment.kind == "recovery":
        previous = _row(
            session,
            CostValuationAssessmentRevision,
            tenant,
            assessment.supersedes_id,
        )
        prior_rows = list(
            session.scalars(
                select(CostValuationAssessmentPart).where(
                    CostValuationAssessmentPart.tenant_id == tenant,
                    CostValuationAssessmentPart.assessment_revision_id == previous.id,
                )
            )
        )
        acquisition = {
            part.inventory_member_id: part.acquisition_value for part in current_parts
        }
        previous_parts = [
            AssessmentPart(
                inventory_member_id=row.inventory_member_id,
                quantity=row.quantity,
                acquisition_value=acquisition.get(row.inventory_member_id, Decimal(-1)),
                assessed_value=row.assessed_value,
            )
            for row in prior_rows
        ]
    try:
        bridge = reconcile_assessment(
            assessment.kind, current_parts, previous=previous_parts
        )
    except CarryingValueRefusal as error:
        raise core.InvalidOperation("Valuation assessment integrity mismatch.") from error
    acquisition = Decimal(result["acquisition_value"])
    carrying = (acquisition + bridge.adjustment).quantize(STEP)
    return {
        **result,
        "carrying_value": _money(carrying),
        "carrying_adjustment": _money(bridge.adjustment),
        "carrying_value_state": "reviewed_assessment",
        "valuation_assessment": {
            "assessment_revision_id": assessment.id,
            "revision": assessment.revision,
            "kind": assessment.kind,
            "supersedes_id": assessment.supersedes_id,
            "effective_at": assessment.effective_at.isoformat(),
            "knowledge_at": assessment.knowledge_at.isoformat(),
            "reason": assessment.reason,
            "parts": [
                {
                    "inventory_member_id": row.inventory_member_id,
                    "evidence_source_record_id": row.evidence_source_record_id,
                    "quantity": _money(row.quantity),
                    "assessed_value": _money(row.assessed_value),
                    "currency": row.currency,
                }
                for row in rows
            ],
        },
    }
