"""Complete, pinned inventory observations for one real joint confirmation."""

import json
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, localcontext

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, ChangeProposal
from reality.db.cost_generations import (
    CostInventoryGeneration,
    CostInventoryPublication,
    CostInventorySnapshot,
)
from reality.db.inventory_costing import CostInventoryReview, CostPolicyRevision
from reality.domain.costing import InventoryBatchReview
from reality.services import core, inventory_generations
from reality.services.costing import _money, _request, _row, _sequence


def _resolve(
    session: Session, tenant: str, action_id: str
) -> tuple[InventoryBatchReview, list, BusinessEvent]:
    core.get_tenant(session, tenant)
    action = _row(session, ChangeProposal, tenant, action_id)
    if action.type != "tool:cost.change" or action.status != "executed":
        raise core.NotFound("Costing scope not found.")
    try:
        request = _request(json.loads(action.input))
        output = json.loads(action.output)
    except (ValueError, TypeError) as error:
        raise core.InvalidOperation("Joint inventory integrity mismatch.") from error
    if not isinstance(request, InventoryBatchReview):
        raise core.NotFound("Costing scope not found.")
    members = session.execute(
        select(CostInventoryReview, CostPolicyRevision)
        .join(
            CostPolicyRevision,
            (CostPolicyRevision.tenant_id == tenant)
            & (CostPolicyRevision.id == CostInventoryReview.policy_id),
        )
        .where(
            CostInventoryReview.tenant_id == tenant,
            CostInventoryReview.action_id == action.id,
        )
        .order_by(CostInventoryReview.id)
        .limit(11)
    ).all()
    scopes = {scope.item_id: scope for scope in request.scopes}
    if len(members) != len(scopes) or {p.item_id for _, p in members} != set(scopes):
        raise core.InvalidOperation("Joint inventory integrity mismatch.")
    event = _row(session, BusinessEvent, tenant, members[0][0].introduced_event_id)
    try:
        exact_output = (
            output["action_id"] == action.id
            and len(output["reviews"]) == len(members)
            and {r["review_id"] for r in output["reviews"]}
            == {r.id for r, _ in members}
        )
        exact_event = (
            json.loads(event.payload).get("operation") == "inventory_batch_review"
        )
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise core.InvalidOperation("Joint inventory integrity mismatch.") from error
    if not (
        exact_output
        and exact_event
        and event.event_type == "cost.reviewed"
        and event.subject_type == "action"
        and event.subject_id == action.id
        and event.action_id == action.id
        and event.sequence == request.expected_event_sequence + 1
    ):
        raise core.InvalidOperation("Joint inventory integrity mismatch.")
    for review, policy in members:
        scope = scopes[policy.item_id]
        if (
            review.introduced_event_id != event.id
            or review.target_event_sequence != event.sequence
            or review.knowledge_at != event.recorded_at
            or review.effective_at != scope.effective_at
            or review.algorithm_version != inventory_generations.VERSION
            or policy.action_id != action.id
            or policy.introduced_event_id != event.id
            or any(
                getattr(policy, name) != getattr(scope, name)
                for name in (
                    "owner_party_id",
                    "method",
                    "currency",
                    "base_unit",
                    "history_start",
                )
            )
        ):
            raise core.InvalidOperation("Joint inventory integrity mismatch.")
    return request, members, event


def _build(
    session: Session, tenant: str, action_id: str, *, deadline: datetime | None = None
) -> dict:
    if session.connection().get_isolation_level() != "READ COMMITTED":
        raise core.InvalidOperation(
            "Joint inventory maintenance requires READ COMMITTED."
        )
    inventory_generations._deadline(deadline)
    with session.begin_nested():
        session.execute(
            select(
                func.pg_advisory_xact_lock(
                    func.hashtextextended(
                        f"cost-inventory-batch:{tenant}:{action_id}:{inventory_generations.VERSION}",
                        0,
                    )
                )
            )
        )
        _, members, _ = _resolve(session, tenant, action_id)
        existing = set(
            session.scalars(
                select(CostInventoryGeneration.review_id).where(
                    CostInventoryGeneration.tenant_id == tenant,
                    CostInventoryGeneration.review_id.in_(
                        [review.id for review, _ in members]
                    ),
                    CostInventoryGeneration.algorithm_version
                    == inventory_generations.VERSION,
                )
            )
        )
        prepared = {}
        # Finish all financial replay before any cache insert takes tenant FK locks.
        # Only the short publication phase may briefly contend with business writes.
        for review, policy in members:
            inventory_generations._deadline(deadline)
            if review.id not in existing:
                prepared[review.id] = inventory_generations.inventory_cost(
                    session, tenant, policy.item_id, review_id=review.id
                )
        results = [
            inventory_generations._build(
                session,
                tenant,
                review.id,
                deadline=deadline,
                _prepared=prepared.get(review.id),
                _allow_replay=False,
            )
            for review, _ in members
        ]
        inventory_generations._deadline(deadline)
        return {
            "action_id": action_id,
            "created": sum(int(row["created"]) for row in results),
            "generation_ids": sorted(row["generation_id"] for row in results),
            "inventory_rows": len(results),
        }


def _total(rows: list[dict], currency: str) -> dict:
    with localcontext() as context:
        context.prec = 80
        amounts = Decimal(0)
        quantities = defaultdict(lambda: Decimal(0))
        for row in rows:
            amounts += Decimal(row["result"]["acquisition_value"])
            quantities[row["context"]["base_unit"]] += Decimal(
                row["result"]["remaining_quantity"]
            )
        return {
            "acquisition_value": _money(amounts),
            "currency": currency,
            "quantities": [
                {"base_unit": unit, "remaining_quantity": _money(amount)}
                for unit, amount in sorted(quantities.items())
            ],
            "carrying_value": None,
            "carrying_value_state": "assessment_not_supported",
        }


def _read(
    session: Session,
    tenant: str,
    action_id: str,
    *,
    mode: str = "historical",
    allow_previous: bool = False,
    _protect: bool = False,
) -> dict:
    if mode not in ("historical", "current") or type(allow_previous) is not bool:
        raise core.InvalidOperation("Unsupported joint inventory read options.")
    with session.no_autoflush:
        if (
            mode == "current"
            and session.connection().get_isolation_level() != "READ COMMITTED"
        ):
            raise core.InvalidOperation(
                "Current inventory snapshots require READ COMMITTED."
            )
        request, members, event = _resolve(session, tenant, action_id)
        review_ids = [review.id for review, _ in members]
        generation_ids = list(
            session.scalars(
                select(CostInventoryGeneration.id)
                .join(
                    CostInventoryPublication,
                    (CostInventoryPublication.tenant_id == tenant)
                    & (
                        CostInventoryPublication.generation_id
                        == CostInventoryGeneration.id
                    )
                    & (
                        CostInventoryPublication.review_id
                        == CostInventoryGeneration.review_id
                    ),
                )
                .where(
                    CostInventoryGeneration.tenant_id == tenant,
                    CostInventoryGeneration.review_id.in_(review_ids),
                    CostInventoryGeneration.algorithm_version
                    == inventory_generations.VERSION,
                )
                .order_by(CostInventoryGeneration.id)
                .limit(11)
            )
        )
        complete = len(generation_ids) == len(members)
        if complete and _protect:
            from reality.services.analytics.costing_relation import (
                inventory_selection_source,
            )

            locked = session.scalars(
                select(CostInventoryGeneration.id)
                .select_from(inventory_selection_source(tenant, generation_ids))
                .order_by(CostInventoryGeneration.id)
                .with_for_update(
                    read=True, of=[CostInventoryGeneration, CostInventorySnapshot]
                )
            ).all()
            if list(locked) != generation_ids:
                raise core.InvalidOperation(
                    "Inventory report basis disappeared; retry the read."
                )
        rows = (
            inventory_generations._read_selection(session, tenant, generation_ids)[
                "rows"
            ]
            if complete
            else []
        )
        if complete and {row["context"]["review_id"] for row in rows} != set(
            review_ids
        ):
            raise core.InvalidOperation("Joint inventory integrity mismatch.")
        scope = request.scopes[0]
        basis = _total(rows, scope.currency) if complete else None
        target = _sequence(session, tenant) if mode == "current" else None
        if target is not None and target < event.sequence:
            raise core.InvalidOperation("Joint inventory event cursor invalid.")
        state = (
            "uninitialized"
            if not complete
            else "historical"
            if mode == "historical"
            else "pending"
            if target > event.sequence
            else "ready"
        )
        usable = complete and (state != "pending" or allow_previous)
        return {
            "action_id": action_id,
            "generation_ids": generation_ids,
            "context": {
                "effective_at": scope.effective_at.isoformat(),
                "knowledge_at": event.recorded_at.astimezone(UTC).isoformat(),
                "owner_party_id": scope.owner_party_id,
                "currency": scope.currency,
                "algorithm_version": inventory_generations.VERSION,
                "review_ids": review_ids,
            },
            "coverage": {
                "expected_items": len(members),
                "available_items": len(generation_ids),
            },
            "freshness": {
                "state": state,
                "processed_event_sequence": event.sequence if complete else None,
                "target_event_sequence": target,
            },
            "result": basis if usable else None,
            "rows": rows if usable else [],
            "basis_result": basis,
            "basis_rows": rows,
            "persistence": {"business_writes": False, "projection_writes": False},
        }
