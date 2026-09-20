"""Bounded captured-review resolution; no common company financial authority."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.core import BusinessEvent
from reality.db.inventory_costing import (
    CostInventoryMember,
    CostInventoryReview,
    CostMovementBasis,
    CostPolicyRevision,
    CostValuationAssessmentRevision,
)
from reality.domain.cost_captured_basis import assemble_captured_basis
from reality.services import core, costing
from reality.services.cost_census_storage import _header, _verify
from reality.services.cost_review_relevance import _unchanged


def _inventory_review(session: Session, tenant: str, item: str, cursor: int):
    review, policy, event = (
        CostInventoryReview.__table__,
        CostPolicyRevision.__table__,
        BusinessEvent.__table__,
    )
    return (
        session.execute(
            select(review)
            .join(
                policy,
                (policy.c.tenant_id == tenant) & (policy.c.id == review.c.policy_id),
            )
            .join(
                event,
                (event.c.tenant_id == tenant)
                & (event.c.id == review.c.introduced_event_id),
            )
            .where(
                review.c.tenant_id == tenant,
                policy.c.item_id == item,
                event.c.sequence <= cursor,
                review.c.target_event_sequence == event.c.sequence,
            )
            .order_by(
                event.c.sequence.desc(), policy.c.revision.desc(), review.c.id.desc()
            )
            .limit(1)
        )
        .mappings()
        .one_or_none()
    )


def _contribution_review(session: Session, tenant: str, line: str, cursor: int):
    review, basis, event = (
        CostContributionReview.__table__,
        CostRevenueMatchBasis.__table__,
        BusinessEvent.__table__,
    )
    return (
        session.execute(
            select(review, basis.c.item_id)
            .join(
                basis,
                (basis.c.tenant_id == tenant)
                & (basis.c.id == review.c.revenue_basis_id),
            )
            .join(
                event,
                (event.c.tenant_id == tenant)
                & (event.c.id == review.c.introduced_event_id),
            )
            .where(
                review.c.tenant_id == tenant,
                basis.c.document_line_id == line,
                event.c.sequence <= cursor,
                review.c.event_sequence == event.c.sequence,
            )
            .order_by(
                event.c.sequence.desc(), review.c.revision.desc(), review.c.id.desc()
            )
            .limit(1)
        )
        .mappings()
        .one_or_none()
    )


def _inventory_assessment(
    session: Session, tenant: str, review_id: str, cursor: int
) -> str | None:
    assessment, event = (
        CostValuationAssessmentRevision.__table__,
        BusinessEvent.__table__,
    )
    return session.scalar(
        select(assessment.c.id)
        .join(
            event,
            (event.c.tenant_id == tenant)
            & (event.c.id == assessment.c.introduced_event_id),
        )
        .where(
            assessment.c.tenant_id == tenant,
            assessment.c.inventory_review_id == review_id,
            event.c.sequence <= cursor,
        )
        .order_by(assessment.c.revision.desc())
        .limit(1)
    )


def _inventory_gaps(
    session: Session, tenant: str, review_id: str, header: dict, captured: set[str]
) -> list[str]:
    review, member, movement = (
        CostInventoryReview.__table__,
        CostInventoryMember.__table__,
        CostMovementBasis.__table__,
    )
    cutoff = session.scalar(
        select(review.c.effective_at).where(
            review.c.tenant_id == tenant, review.c.id == review_id
        )
    )
    identities = list(
        session.scalars(
            select(movement.c.movement_id)
            .join(
                member,
                (member.c.tenant_id == tenant)
                & (member.c.movement_basis_id == movement.c.id),
            )
            .where(movement.c.tenant_id == tenant, member.c.review_id == review_id)
            .limit(101)
        )
    )
    gaps = []
    if cutoff != header["effective_at"]:
        gaps.append("inventory_cutoff_mismatch")
    if len(identities) > 100 or set(identities) != captured:
        gaps.append("inventory_movement_membership_mismatch")
    return gaps


def _row(key: str, identity: str, review, result: dict | None, gaps: list[str]) -> dict:
    return {
        key: identity,
        "review_id": review["id"] if review is not None else None,
        "review_content_hash": review["content_hash"] if review is not None else None,
        "state": "available_at_capture"
        if result is not None and not gaps
        else "unknown_at_capture",
        "result": result if not gaps else None,
        "basis_result": result,
        "gaps": gaps,
    }


def _resolve(
    session: Session,
    tenant: str,
    identity: str,
    *,
    max_subjects: int = 10,
    _pinned: dict | None = None,
    _tenant_locked: bool = False,
) -> dict:
    if type(max_subjects) is not int or not 1 <= max_subjects <= 10:
        raise core.InvalidOperation("Census resolution subject limit must be 1–10.")
    isolation = session.connection().get_isolation_level()
    if isolation != "REPEATABLE READ" and not (
        isolation == "READ COMMITTED" and _tenant_locked
    ):
        raise core.InvalidOperation("Census resolution requires REPEATABLE READ.")
    with session.no_autoflush:
        records = {}
        _verify(session, tenant, identity, _records=records)
        header = _header(session, tenant, identity)
        inventory = {}
        for member in records["movement"]:
            inventory.setdefault(member["observed_values"]["item_id"], set()).add(
                member["movement_id"]
            )
        if len(inventory) + len(records["line"]) > max_subjects:
            raise core.InvalidOperation("Census resolution subject limit exceeded.")
        cursor = header["event_sequence"]
        stock, contribution = [], []
        for item in sorted(inventory):
            review = (
                _inventory_review(session, tenant, item, cursor)
                if _pinned is None
                else _pinned["inventory"][item]
            )
            if review is None:
                stock.append(
                    _row("item_id", item, None, None, ["inventory_scope_not_reviewed"])
                )
                continue
            result = costing.inventory_cost(
                session,
                tenant,
                item,
                review_id=review["id"],
                assessment_revision_id=_inventory_assessment(
                    session, tenant, review["id"], cursor
                ),
            )
            gaps = _inventory_gaps(
                session, tenant, review["id"], header, inventory[item]
            )
            proof = _unchanged(session, tenant, review["target_event_sequence"], cursor)
            if not proof["unchanged"]:
                gaps.append("review_knowledge_changed_at_capture")
            stock.append(
                {
                    **_row("item_id", item, review, result, gaps),
                    "freshness_proof": proof,
                }
            )
        for member in sorted(records["line"], key=lambda row: row["document_line_id"]):
            line = member["document_line_id"]
            review = (
                _contribution_review(session, tenant, line, cursor)
                if _pinned is None
                else _pinned["contribution"][line]
            )
            if review is None:
                contribution.append(
                    _row(
                        "document_line_id",
                        line,
                        None,
                        None,
                        ["commercial_match_not_reviewed"],
                    )
                )
                continue
            result = costing.reviewed_contribution(
                session, tenant, line, review_id=review["id"]
            )
            gaps = _inventory_gaps(
                session,
                tenant,
                result["trace"]["inventory_review_id"],
                header,
                inventory.get(review["item_id"], set()),
            )
            if datetime.fromisoformat(result["economic_at"]) > header["effective_at"]:
                gaps.append("economic_activity_after_capture_cutoff")
            proof = _unchanged(
                session, tenant, review["event_sequence"], cursor, document_line_id=line
            )
            if not proof["unchanged"]:
                gaps.append("review_knowledge_changed_at_capture")
            contribution.append(
                {
                    **_row("document_line_id", line, review, result, gaps),
                    "freshness_proof": proof,
                }
            )
        populated = {row["document_member_id"] for row in records["line"]}
        resolved = {
            "census_id": identity,
            "tenant_id": tenant,
            "state": "resolved_scope_reviews",
            "publication_eligible": False,
            "effective_at": header["effective_at"].isoformat(),
            "event_sequence": cursor,
            "inventory": stock,
            "contribution": contribution,
            "document_gaps": [
                {"document_id": row["document_id"], "reason": "document_lines_missing"}
                for row in sorted(
                    records["document"], key=lambda row: row["document_id"]
                )
                if row["id"] not in populated
            ],
            "source_gaps": [
                {
                    "source_record_id": row["source_record_id"],
                    "classification": row["observed_values"]["classification"],
                }
                for row in sorted(
                    records["source"], key=lambda row: row["source_record_id"]
                )
                if row["observed_values"]["classification"] != "interpreted"
            ],
            "persistence": {"business_writes": False, "projection_writes": False},
        }

        try:
            resolved["captured_basis"] = assemble_captured_basis(
                header,
                resolved,
                inventory,
                [row["document_line_id"] for row in records["line"]],
            )
        except ValueError as error:
            raise core.InvalidOperation(str(error)) from error
        return resolved
