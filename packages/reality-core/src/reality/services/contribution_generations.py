"""Atomic disposable observations of one actual joint contribution confirmation."""

import json
from datetime import datetime
from decimal import Decimal

from pydantic import TypeAdapter, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.core import BusinessEvent, ChangeProposal, now, uid
from reality.db.cost_generations import (
    CostContributionGeneration,
    CostContributionSnapshot,
)
from reality.db.inventory_costing import (
    CostInventoryMember,
    CostInventoryReview,
    CostPolicyRevision,
)
from reality.domain.contribution import ALGORITHM_VERSION
from reality.domain.costing import Amount, ContributionBatchReview
from reality.services import core
from reality.services.analytics.contribution_aggregates import (
    contribution_aggregate_columns,
)
from reality.services.analytics.contribution_relation import contribution_relation
from reality.services.costing import (
    _hash,
    _money,
    _request,
    _row,
    _sequence,
    reviewed_contribution,
)
from reality.services.inventory_costing import _values
from reality.services.inventory_generations import _deadline

VERSION = ALGORITHM_VERSION
COST_FIELDS = (
    "goods_cost",
    "known_direct_selling_cost",
    "known_allocated_selling_cost",
)


def _refuse():
    raise core.InvalidOperation("Contribution generation integrity mismatch.")


def _resolve(session: Session, tenant: str, action_id: str) -> tuple[dict, list]:
    core.get_tenant(session, tenant)
    action = _row(session, ChangeProposal, tenant, action_id)
    if action.type != "tool:cost.change" or action.status != "executed":
        raise core.NotFound("Costing scope not found.")
    try:
        request = _request(json.loads(action.input))
        output = json.loads(action.output)
    except (ValueError, TypeError, core.InvalidOperation):
        _refuse()
    if not isinstance(request, ContributionBatchReview):
        raise core.NotFound("Costing scope not found.")
    r, b, m, i, p = (
        CostContributionReview,
        CostRevenueMatchBasis,
        CostInventoryMember,
        CostInventoryReview,
        CostPolicyRevision,
    )
    rows = session.execute(
        select(r, b, m, i, p)
        .select_from(r)
        .join(b, (b.tenant_id == tenant) & (b.id == r.revenue_basis_id))
        .join(m, (m.tenant_id == tenant) & (m.id == r.inventory_member_id))
        .join(i, (i.tenant_id == tenant) & (i.id == m.review_id))
        .join(p, (p.tenant_id == tenant) & (p.id == i.policy_id))
        .where(r.tenant_id == tenant, r.action_id == action.id)
        .order_by(r.id)
        .limit(11)
    ).all()
    scopes = {position.document_line_id: position for position in request.positions}
    if len(rows) != len(scopes) or {b.document_line_id for _, b, *_ in rows} != set(
        scopes
    ):
        _refuse()
    event = _row(session, BusinessEvent, tenant, rows[0][0].introduced_event_id)
    try:
        if not (
            output["action_id"] == output["profile_scope_action_id"] == action.id
            and len(output["reviews"]) == len(rows)
            and {v["review_id"] for v in output["reviews"]} == {r.id for r, *_ in rows}
            and output["event_sequence"]
            == event.sequence
            == request.expected_event_sequence + 1
            and datetime.fromisoformat(output["knowledge_at"]) == event.recorded_at
            and output["profile"] == "commercial_v1"
            and event.event_type == "cost.reviewed"
            and event.subject_type == "action"
            and event.subject_id == event.action_id == action.id
            and json.loads(event.payload).get("operation")
            == "contribution_batch_review"
        ):
            _refuse()
        if len({b.movement_basis_id for _, b, *_ in rows}) != len(rows):
            _refuse()
        output_members = {entry["review_id"]: entry for entry in output["reviews"]}
        for review, basis, member, inventory, policy in rows:
            recorded = output_members[review.id]
            if not (
                recorded["document_line_id"] == basis.document_line_id
                and recorded["action_id"] == action.id
                and recorded["profile_revision_id"] == review.id
                and recorded["event_sequence"] == event.sequence
                and recorded["trace"]["inventory_member_id"] == member.id
                and recorded["trace"]["revenue_basis_id"] == basis.id
            ):
                _refuse()
            scope = scopes[basis.document_line_id]
            if not (
                review.introduced_event_id == event.id
                and review.event_sequence == event.sequence
                and review.knowledge_at == event.recorded_at
                and review.profile == scope.profile
                and review.economic_at == scope.economic_at
                and review.reason == request.reason
                and member.kind == "issue"
                and member.movement_basis_id == basis.movement_basis_id
                and policy.item_id == basis.item_id
                and policy.currency == basis.currency == output["currency"]
                and policy.base_unit == basis.base_unit
                and policy.owner_party_id == output["owner_party_id"]
                and inventory.action_id == output["inventory_action_id"]
                and inventory.effective_at
                == datetime.fromisoformat(output["effective_at"])
                and inventory.knowledge_at
                == datetime.fromisoformat(output["inventory_knowledge_at"])
                and inventory.introduced_event_id == output["inventory_event_id"]
                and inventory.target_event_sequence
                == output["inventory_event_sequence"]
            ):
                _refuse()
    except (ValueError, KeyError, TypeError, AttributeError):
        _refuse()
    context = {
        key: output[key]
        for key in (
            "action_id",
            "profile_scope_action_id",
            "profile",
            "inventory_action_id",
            "effective_at",
            "knowledge_at",
            "event_sequence",
            "currency",
            "owner_party_id",
            "inventory_knowledge_at",
            "inventory_event_id",
            "inventory_event_sequence",
        )
    }
    context["confirmation_hash"] = _hash(
        {"input": json.loads(action.input), "output": output}
    )
    return context, rows


def _digest(context: dict, members: list, observations: list[dict]) -> str:
    return _hash(
        {
            "algorithm_version": VERSION,
            "context": context,
            "inputs": [
                [
                    *(_values(record) for record in row),
                    row[0].content_hash,
                    row[3].content_hash,
                ]
                for row in members
            ],
            "observations": sorted(observations, key=lambda row: row["review_id"]),
        }
    )


def _observation(row: CostContributionSnapshot) -> dict:
    return {
        "review_id": row.review_id,
        "selling_complete": row.selling_complete,
        **{key: _money(getattr(row, key)) for key in COST_FIELDS},
    }


def _load(session: Session, tenant: str, context: dict, members: list):
    # These locks protect disposable rows through the caller's final SQL aggregate;
    # no tenant/intake row is locked. A publication is one committed complete set.
    generation = session.scalar(
        select(CostContributionGeneration)
        .where(
            CostContributionGeneration.tenant_id == tenant,
            CostContributionGeneration.action_id == context["action_id"],
            CostContributionGeneration.algorithm_version == VERSION,
        )
        .with_for_update(read=True)
    )
    if generation is None:
        return None
    snapshots = list(
        session.scalars(
            select(CostContributionSnapshot)
            .where(
                CostContributionSnapshot.tenant_id == tenant,
                CostContributionSnapshot.generation_id == generation.id,
            )
            .order_by(CostContributionSnapshot.id)
            .with_for_update(read=True)
        )
    )
    if len(snapshots) != len(members) or {s.review_id for s in snapshots} != {
        r.id for r, *_ in members
    }:
        _refuse()
    if generation.output_hash != _digest(
        context, members, [_observation(s) for s in snapshots]
    ):
        _refuse()
    return generation


def _build(
    session: Session, tenant: str, action_id: str, *, deadline: datetime | None = None
) -> dict:
    if session.connection().get_isolation_level() != "READ COMMITTED":
        raise core.InvalidOperation(
            "Contribution cache maintenance requires READ COMMITTED."
        )
    _deadline(deadline)
    with session.begin_nested():
        context, members = _resolve(session, tenant, action_id)
        session.execute(
            select(
                func.pg_advisory_xact_lock(
                    func.hashtextextended(
                        f"cost-contribution:{tenant}:{action_id}:{VERSION}", 0
                    )
                )
            )
        )
        generation = _load(session, tenant, context, members)
        created = generation is None
        if created:
            observations = []
            for review, basis, *_ in members:
                _deadline(deadline)
                result = reviewed_contribution(
                    session, tenant, basis.document_line_id, review_id=review.id
                )
                values = {
                    "goods_cost": result["trace"]["consumption"]["cost"],
                    "known_direct_selling_cost": result["known_direct_selling_cost"],
                    "known_allocated_selling_cost": result[
                        "known_allocated_selling_cost"
                    ],
                }
                try:
                    values = {
                        key: None
                        if value is None and key != "goods_cost"
                        else _money(TypeAdapter(Amount).validate_python(Decimal(value)))
                        for key, value in values.items()
                    }
                except (ValidationError, ValueError, TypeError) as error:
                    raise core.InvalidOperation(
                        "Contribution observation exceeds supported precision."
                    ) from error
                observations.append(
                    {
                        "review_id": review.id,
                        "selling_complete": result["db2"] is not None,
                        **values,
                    }
                )
            _deadline(deadline)
            # Never write a cache row before every financial replay has completed.
            generation = CostContributionGeneration(
                id=uid("ccg"),
                tenant_id=tenant,
                action_id=action_id,
                algorithm_version=VERSION,
                completed_at=now(),
                output_hash=_digest(context, members, observations),
            )
            session.add(generation)
            session.flush()
            for observation in observations:
                session.add(
                    CostContributionSnapshot(
                        id=uid("ccs"),
                        tenant_id=tenant,
                        generation_id=generation.id,
                        **{
                            key: Decimal(value)
                            if key in COST_FIELDS and value is not None
                            else value
                            for key, value in observation.items()
                        },
                    )
                )
            session.flush()
            _load(session, tenant, context, members)
        _deadline(deadline)
        return {
            "generation_id": generation.id,
            "created": created,
            "contribution_rows": len(members),
        }


def _serialize(rows) -> list[dict]:
    return [
        {
            key: _money(value)
            if isinstance(value, Decimal)
            else value.isoformat()
            if isinstance(value, datetime)
            else value
            for key, value in row.items()
        }
        for row in rows
    ]


def _validate_mode(session: Session, mode: str) -> None:
    if mode not in ("historical", "current"):
        raise core.InvalidOperation("Unsupported contribution read mode.")
    if (
        mode == "current"
        and session.connection().get_isolation_level() != "READ COMMITTED"
    ):
        raise core.InvalidOperation(
            "Current contribution reads require READ COMMITTED."
        )


def _freshness(
    session: Session, tenant: str, context: dict, *, mode: str, initialized: bool
) -> dict:
    """A final observation of the live cursor, never a lock or lasting guarantee."""
    target = _sequence(session, tenant) if mode == "current" else None
    processed = context["event_sequence"] if initialized else None
    if target is not None and target < context["event_sequence"]:
        raise core.InvalidOperation("Contribution event cursor invalid.")
    state = (
        "uninitialized"
        if not initialized
        else "historical"
        if mode == "historical"
        else "pending"
        if target > processed
        else "ready"
    )
    return {
        "state": state,
        "processed_event_sequence": processed,
        "target_event_sequence": target,
    }


def _read(
    session: Session, tenant: str, action_id: str, *, mode: str = "historical"
) -> dict:
    with session.no_autoflush:
        _validate_mode(session, mode)
        context, members = _resolve(session, tenant, action_id)
        generation = _load(session, tenant, context, members)
        result = {
            "state": "uninitialized",
            "generation_id": None,
            "context": context,
            "coverage": {"expected_positions": len(members), "available_positions": 0},
            "rows": [],
            "groups": [],
            "persistence": {"business_writes": False, "projection_writes": False},
        }
        if generation is None:
            return result | {
                "freshness": _freshness(
                    session, tenant, context, mode=mode, initialized=False
                )
            }
        source = contribution_relation(tenant, generation.id).subquery()
        dimensions = (
            "review_id",
            "document_line_id",
            "order_line_id",
            "item_id",
            "customer_id",
            "sales_channel",
            "currency",
            "base_unit",
            "quantity",
            "policy_revision_id",
            "economic_at",
            "knowledge_at",
            "known_direct_selling_cost",
            "known_allocated_selling_cost",
        )
        columns = [source.c[key] for key in dimensions]
        aggregates = contribution_aggregate_columns(source, reviewed=True)
        rows = (
            session.execute(
                select(*columns, *aggregates)
                .group_by(*columns)
                .order_by(source.c.review_id)
            )
            .mappings()
            .all()
        )
        if len(rows) != len(members):
            _refuse()
        groups = (
            session.execute(
                select(
                    source.c.currency,
                    source.c.base_unit,
                    func.sum(source.c.quantity).label("quantity"),
                    func.sum(source.c.known_direct_selling_cost).label(
                        "known_direct_selling_cost"
                    ),
                    func.sum(source.c.known_allocated_selling_cost).label(
                        "known_allocated_selling_cost"
                    ),
                    *aggregates,
                )
                .group_by(source.c.currency, source.c.base_unit)
                .order_by(source.c.currency, source.c.base_unit)
            )
            .mappings()
            .all()
        )
        freshness = _freshness(session, tenant, context, mode=mode, initialized=True)
        usable = freshness["state"] != "pending"
        return result | {
            "state": freshness["state"],
            "freshness": freshness,
            "generation_id": generation.id,
            "algorithm_version": generation.algorithm_version,
            "completed_at": generation.completed_at.isoformat(),
            "coverage": {
                "expected_positions": len(members),
                "available_positions": len(rows),
            },
            "rows": _serialize(rows) if usable else [],
            "groups": _serialize(groups) if usable else [],
        }
