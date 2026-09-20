"""Bounded inventory cache maintenance and generation-pinned read contracts."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, Item, now, uid
from reality.db.cost_generations import (
    CostInventoryGeneration,
    CostInventoryPublication,
    CostInventorySnapshot,
)
from reality.db.inventory_costing import (
    CostInventoryReview,
    CostPolicyRevision,
    CostValuationAssessmentRevision,
)
from reality.domain.cost_generation import (
    Completion,
    Generation,
    GenerationBasis,
    publication_decision,
)
from reality.domain.inventory_costing import ALGORITHM_VERSION
from reality.jobs.registry import JobError
from reality.services import core
from reality.services.analytics.costing_relation import (
    inventory_relation,
    inventory_selection_source,
    selection_ids,
)
from reality.services.costing import _hash, _money, _row, _sequence, inventory_cost

VERSION = ALGORITHM_VERSION


def _basis(
    session: Session,
    tenant: str,
    generation: CostInventoryGeneration,
    review: CostInventoryReview,
    policy: CostPolicyRevision,
) -> Generation:
    assessment = (
        _row(
            session,
            CostValuationAssessmentRevision,
            tenant,
            generation.assessment_revision_id,
        )
        if generation.assessment_revision_id
        else None
    )
    assessment_event = (
        _row(session, BusinessEvent, tenant, assessment.introduced_event_id)
        if assessment
        else None
    )
    return Generation(
        id=generation.id,
        basis=GenerationBasis(
            tenant_id=tenant,
            scope_key=_hash(
                {
                    "policy": policy.id,
                    "effective_at": review.effective_at.isoformat(),
                    "assessment_revision_id": generation.assessment_revision_id,
                }
            ),
            kind="inventory",
            manifest_id=review.id,
            policy_revision_id=policy.id,
            profile_revision_id=None,
            effective_at=review.effective_at,
            knowledge_at=assessment.knowledge_at if assessment else review.knowledge_at,
            event_sequence=(
                assessment_event.sequence
                if assessment_event
                else review.target_event_sequence
            ),
            algorithm_version=generation.algorithm_version,
        ),
    )


def _values(
    quantity: Decimal, amount: Decimal, carrying: Decimal | None
) -> dict[str, str | None]:
    return {
        "remaining_quantity": _money(quantity),
        "acquisition_value": _money(amount),
        "carrying_value": _money(carrying) if carrying is not None else None,
    }


def _digest(
    review: CostInventoryReview,
    assessment_revision_id: str | None,
    values: dict[str, str | None],
) -> str:
    return _hash(
        {
            "review_id": review.id,
            "input_hash": review.content_hash,
            "algorithm_version": VERSION,
            "assessment_revision_id": assessment_revision_id,
            "values": values,
        }
    )


def _observation(
    session: Session,
    tenant: str,
    generation: CostInventoryGeneration,
    review: CostInventoryReview,
) -> dict[str, str | None]:
    row = session.execute(inventory_relation(tenant, generation.id)).one_or_none()
    if row is None:
        raise core.InvalidOperation("Inventory cache integrity mismatch.")
    return _verified_observation(
        generation,
        review,
        row.remaining_quantity,
        row.acquisition_value,
        row.carrying_value,
    )


def _verified_observation(
    generation: CostInventoryGeneration,
    review: CostInventoryReview,
    quantity: Decimal,
    amount: Decimal,
    carrying: Decimal | None,
) -> dict[str, str | None]:
    if generation.algorithm_version != VERSION:
        raise core.InvalidOperation("Inventory cache integrity mismatch.")
    values = _values(quantity, amount, carrying)
    if generation.output_hash != _digest(
        review, generation.assessment_revision_id, values
    ):
        raise core.InvalidOperation("Inventory cache integrity mismatch.")
    return {
        **values,
        "carrying_value_state": (
            "reviewed_assessment" if carrying is not None else "assessment_missing"
        ),
    }


def _deadline(deadline: datetime | None) -> None:
    if deadline is not None:
        if deadline.tzinfo is None or deadline.utcoffset() is None:
            raise core.InvalidOperation("An aware worker deadline is required.")
        if now() >= deadline:
            raise JobError("handler_timeout")


def _build(
    session: Session,
    tenant: str,
    review_id: str,
    *,
    deadline: datetime | None = None,
    _prepared: dict | None = None,
    _allow_replay: bool = True,
) -> dict:
    if session.connection().get_isolation_level() != "READ COMMITTED":
        raise core.InvalidOperation(
            "Inventory cache maintenance requires READ COMMITTED."
        )
    _deadline(deadline)
    # The existing worker owns the outer transaction and claim. A savepoint also
    # prevents a maintenance caller catching a refusal from retaining partial rows.
    with session.begin_nested():
        core.get_tenant(session, tenant)
        review = _row(session, CostInventoryReview, tenant, review_id)
        policy = _row(session, CostPolicyRevision, tenant, review.policy_id)
        assessment = session.scalar(
            select(CostValuationAssessmentRevision)
            .where(
                CostValuationAssessmentRevision.tenant_id == tenant,
                CostValuationAssessmentRevision.inventory_review_id == review.id,
            )
            .order_by(CostValuationAssessmentRevision.revision.desc())
            .limit(1)
        )
        assessment_id = assessment.id if assessment else None
        if review.algorithm_version != VERSION:
            raise core.InvalidOperation("Unsupported inventory algorithm.")
        session.execute(
            select(
                func.pg_advisory_xact_lock(
                    func.hashtextextended(
                        f"cost-inventory:{tenant}:{review.id}:{assessment_id}:{VERSION}", 0
                    )
                )
            )
        )
        publication = session.scalar(
            select(CostInventoryPublication).where(
                CostInventoryPublication.tenant_id == tenant,
                CostInventoryPublication.review_id == review.id,
            )
        )
        generation = session.scalar(
            select(CostInventoryGeneration).where(
                CostInventoryGeneration.tenant_id == tenant,
                CostInventoryGeneration.review_id == review.id,
                CostInventoryGeneration.assessment_revision_id.is_(assessment_id)
                if assessment_id is None
                else CostInventoryGeneration.assessment_revision_id == assessment_id,
                CostInventoryGeneration.algorithm_version == VERSION,
            )
        )
        previous = None
        if publication is not None:
            old = _row(
                session, CostInventoryGeneration, tenant, publication.generation_id
            )
            if old.review_id != review.id:
                raise core.InvalidOperation("Inventory publication integrity mismatch.")
            previous = _basis(session, tenant, old, review, policy)
        created = generation is None
        if created:
            if _prepared is None and not _allow_replay:
                raise core.Conflict(
                    "Inventory cache changed during joint build; retry."
                )
            # The historical reader verifies retained membership and input hashes.
            result = (
                inventory_cost(
                    session,
                    tenant,
                    policy.item_id,
                    review_id=review.id,
                    assessment_revision_id=assessment_id,
                )
                if _prepared is None
                else _prepared
            )
            if (
                result["review_id"] != review.id
                or result["item_id"] != policy.item_id
                or result["algorithm_version"] != VERSION
            ):
                raise core.InvalidOperation("Inventory prepared basis mismatch.")
            values = _values(
                Decimal(result["remaining_quantity"]),
                Decimal(result["acquisition_value"]),
                Decimal(result["carrying_value"])
                if result["carrying_value"] is not None
                else None,
            )
            generation = CostInventoryGeneration(
                id=uid("cig"),
                tenant_id=tenant,
                review_id=review.id,
                assessment_revision_id=assessment_id,
                algorithm_version=VERSION,
                completed_at=now(),
                output_hash=_digest(review, assessment_id, values),
            )
            session.add(generation)
            session.flush()
            session.add(
                CostInventorySnapshot(
                    id=uid("cis"),
                    tenant_id=tenant,
                    generation_id=generation.id,
                    remaining_quantity=Decimal(values["remaining_quantity"]),
                    acquisition_value=Decimal(values["acquisition_value"]),
                    carrying_value=(
                        Decimal(values["carrying_value"])
                        if values["carrying_value"] is not None
                        else None
                    ),
                )
            )
            session.flush()
        _observation(session, tenant, generation, review)
        actual = session.scalar(
            select(func.count())
            .select_from(CostInventorySnapshot)
            .where(
                CostInventorySnapshot.tenant_id == tenant,
                CostInventorySnapshot.generation_id == generation.id,
            )
        )
        _deadline(deadline)
        decision = publication_decision(
            tenant_id=tenant,
            candidate=_basis(session, tenant, generation, review, policy),
            completion=Completion(
                inputs_sealed=True,
                content_verified=True,
                planned_work=1,
                completed_work=1,
                expected_inventory_rows=1,
                inventory_rows=actual,
                expected_contribution_rows=0,
                contribution_rows=0,
                expected_trace_rows=0,
                trace_rows=0,
            ),
            published=previous,
            expected_previous_id=previous.id if previous else None,
            target_event_sequence=_sequence(session, tenant),
        )
        if decision.change_pointer:
            if publication is None:
                session.add(
                    CostInventoryPublication(
                        id=uid("cip"),
                        tenant_id=tenant,
                        review_id=review.id,
                        generation_id=generation.id,
                    )
                )
            else:
                publication.generation_id = generation.id
            session.flush()
        return {**decision.model_dump(mode="json"), "created": created}


def _read(
    session: Session,
    tenant: str,
    item_id: str,
    *,
    review_id: str | None = None,
    generation_id: str | None = None,
    allow_previous: bool = False,
) -> dict:
    if type(allow_previous) is not bool:
        raise core.InvalidOperation("allow_previous must be a boolean.")
    historical = review_id is not None or generation_id is not None
    with session.no_autoflush:
        if (
            not historical
            and session.connection().get_isolation_level() != "READ COMMITTED"
        ):
            raise core.InvalidOperation(
                "Current inventory snapshots require READ COMMITTED."
            )
        core.get_tenant(session, tenant)
        _row(session, Item, tenant, item_id)
        generation = None
        if generation_id is not None:
            generation = _row(session, CostInventoryGeneration, tenant, generation_id)
            if review_id is not None and generation.review_id != review_id:
                raise core.NotFound("Costing scope not found.")
            review_id = generation.review_id
        if review_id is not None:
            review = _row(session, CostInventoryReview, tenant, review_id)
        else:
            review = session.scalar(
                select(CostInventoryReview)
                .join(
                    CostPolicyRevision,
                    (CostPolicyRevision.tenant_id == CostInventoryReview.tenant_id)
                    & (CostPolicyRevision.id == CostInventoryReview.policy_id),
                )
                .where(
                    CostInventoryReview.tenant_id == tenant,
                    CostPolicyRevision.item_id == item_id,
                )
                .order_by(CostPolicyRevision.revision.desc())
                .limit(1)
            )
        policy = (
            _row(session, CostPolicyRevision, tenant, review.policy_id)
            if review
            else None
        )
        if policy is not None and policy.item_id != item_id:
            raise core.NotFound("Costing scope not found.")
        if review is not None and generation is None:
            generation = session.scalar(
                select(CostInventoryGeneration)
                .join(
                    CostInventoryPublication,
                    (
                        CostInventoryPublication.tenant_id
                        == CostInventoryGeneration.tenant_id
                    )
                    & (
                        CostInventoryPublication.generation_id
                        == CostInventoryGeneration.id
                    ),
                )
                .where(
                    CostInventoryPublication.tenant_id == tenant,
                    CostInventoryPublication.review_id == review.id,
                )
            )
        result, context = None, None
        if generation is not None:
            result = _observation(session, tenant, generation, review)
            context = _context(session, tenant, generation, review, policy)
        target = None if historical else _sequence(session, tenant)
        processed = (
            _basis(session, tenant, generation, review, policy).basis.event_sequence
            if generation is not None
            else None
        )
        state = (
            "uninitialized"
            if generation is None
            else "historical"
            if historical
            else "pending"
            if target > processed
            else "ready"
        )
        return {
            "generation_id": generation.id if generation else None,
            "context": context,
            "freshness": {
                "state": state,
                "processed_event_sequence": processed,
                "target_event_sequence": target,
            },
            "result": result
            if state in {"ready", "historical"} or allow_previous
            else None,
            "basis_result": result,
            "persistence": {"business_writes": False, "projection_writes": False},
        }


def _context(
    session: Session,
    tenant: str,
    generation: CostInventoryGeneration,
    review: CostInventoryReview,
    policy: CostPolicyRevision,
) -> dict:
    context = _basis(
        session, tenant, generation, review, policy
    ).basis.model_dump(mode="json")
    context.update(
        review_id=review.id,
        assessment_revision_id=generation.assessment_revision_id,
        review_action_id=review.action_id,
        item_id=policy.item_id,
        currency=policy.currency,
        base_unit=policy.base_unit,
        method=policy.method,
        owner_party_id=policy.owner_party_id,
        completed_at=generation.completed_at.astimezone(UTC).isoformat(),
    )
    return context


def _read_selection(
    session: Session, tenant: str, generation_ids: list[str] | tuple[str, ...]
) -> dict:
    selected = selection_ids(generation_ids)
    with session.no_autoflush:
        core.get_tenant(session, tenant)
        rows = session.execute(
            select(
                CostInventoryGeneration,
                CostInventoryReview,
                CostPolicyRevision,
                CostInventorySnapshot.remaining_quantity,
                CostInventorySnapshot.acquisition_value,
                CostInventorySnapshot.carrying_value,
            )
            .select_from(inventory_selection_source(tenant, selected))
            .order_by(CostInventoryGeneration.id)
        ).all()
        if len(rows) != len(selected):
            raise core.NotFound("Costing selection not found.")
        observations = []
        for generation, review, policy, quantity, amount, carrying in rows:
            result = _verified_observation(
                generation, review, quantity, amount, carrying
            )
            observations.append(
                {
                    "generation_id": generation.id,
                    "context": _context(
                        session, tenant, generation, review, policy
                    ),
                    "freshness": {
                        "state": "historical",
                        "processed_event_sequence": review.target_event_sequence,
                        "target_event_sequence": None,
                    },
                    "result": result,
                    "basis_result": result,
                    "persistence": {
                        "business_writes": False,
                        "projection_writes": False,
                    },
                }
            )
        return {
            "mode": "historical_selection",
            "count": len(observations),
            "rows": observations,
            "persistence": {"business_writes": False, "projection_writes": False},
        }
