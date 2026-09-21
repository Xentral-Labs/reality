"""Confirmed full-line revenue and consumption, with immutable historical membership."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.core import DocumentLine, now
from reality.db.inventory_costing import (
    CostInventoryMember,
    CostInventoryReview,
    CostMovementBasis,
    CostPolicyRevision,
)
from reality.domain.contribution import (
    ContributionContext,
    ContributionInput,
    MatchedSlice,
    aggregate_contribution,
)
from reality.domain.costing import ContributionBatchReview, ContributionReview
from reality.services import core
from reality.services.costing import (
    _hash,
    _money,
    _new,
    _row,
    _sequence,
    contribution_preview,
    inventory_cost,
)
from reality.services.inventory_costing import _values


def _check(session, tenant, request):
    candidate = contribution_preview(session, tenant, request.document_line_id)
    if candidate["state"] != "candidate":
        raise core.InvalidOperation(
            "A complete supported contribution candidate is required."
        )
    if request.expected_candidate_hash != candidate["candidate_hash"]:
        raise core.Conflict(
            "Contribution candidate changed; reload before confirmation."
        )
    trace = candidate["trace"]
    if request.economic_at != datetime.fromisoformat(trace["proposed_economic_at"]):
        raise core.InvalidOperation(
            "Confirm the exact candidate shipment economic time."
        )
    members = list(
        session.scalars(
            select(CostInventoryMember)
            .join(
                CostMovementBasis,
                (CostMovementBasis.tenant_id == CostInventoryMember.tenant_id)
                & (CostMovementBasis.id == CostInventoryMember.movement_basis_id),
            )
            .where(
                CostInventoryMember.tenant_id == tenant,
                CostMovementBasis.tenant_id == tenant,
                CostInventoryMember.review_id == trace["inventory_review_id"],
                CostMovementBasis.movement_id == trace["movement_id"],
                CostInventoryMember.kind == "issue",
            )
            .limit(2)
        )
    )
    if len(members) != 1:
        raise core.InvalidOperation(
            "Contribution requires exact inventory issue membership."
        )
    fields = {
        "document_line_id": request.document_line_id,
        "order_line_id": trace["order_line_id"],
        "movement_basis_id": members[0].movement_basis_id,
        "item_id": trace["item_id"],
        "customer_id": trace["customer_id"],
        "stated_net": _money(Decimal(trace["revenue"]["amounts"]["net"])),
        "quantity": candidate["quantity"],
        "currency": candidate["currency"],
        "base_unit": candidate["base_unit"],
        "invoice_date": (
            date.fromisoformat(trace["invoice_date"])
            if trace["invoice_date"]
            else None
        ),
        "sales_channel": trace["sales_channel"],
        "evidence_hash": trace["revenue"]["evidence_hash"],
        "input_schema_version": 1,
    }
    existing = session.scalar(
        select(CostRevenueMatchBasis).where(
            CostRevenueMatchBasis.tenant_id == tenant,
            CostRevenueMatchBasis.document_line_id == request.document_line_id,
        )
    )
    if existing and any(
        _values(existing)[key] != value for key, value in fields.items()
    ):
        raise core.InvalidOperation(
            "Admitted revenue context or full shipment binding changed."
        )
    other = session.scalar(
        select(CostRevenueMatchBasis.id)
        .where(
            CostRevenueMatchBasis.tenant_id == tenant,
            CostRevenueMatchBasis.movement_basis_id == members[0].movement_basis_id,
            CostRevenueMatchBasis.document_line_id != request.document_line_id,
        )
        .limit(1)
    )
    if other:
        raise core.InvalidOperation(
            "Shipment quantity is already bound to another revenue line."
        )
    from reality.services import selling_costs

    return {
        "selling_parts": selling_costs._check_review(session, tenant, request),
        "candidate": candidate,
        "basis": fields,
        "inventory_member_id": members[0].id,
    }


def _execute(session, tenant, request, prepared, event, action, *, knowledge_at=None):
    basis = session.scalar(
        select(CostRevenueMatchBasis).where(
            CostRevenueMatchBasis.tenant_id == tenant,
            CostRevenueMatchBasis.document_line_id == request.document_line_id,
        )
    )
    if basis is None:
        fields = prepared["basis"] | {
            "stated_net": Decimal(prepared["basis"]["stated_net"]),
            "quantity": Decimal(prepared["basis"]["quantity"]),
        }
        basis = _new(
            session,
            CostRevenueMatchBasis,
            tenant,
            **fields,
            introduced_event_id=event.id,
        )
    prior = session.scalar(
        select(CostContributionReview)
        .where(
            CostContributionReview.tenant_id == tenant,
            CostContributionReview.revenue_basis_id == basis.id,
        )
        .order_by(CostContributionReview.revision.desc())
        .limit(1)
    )
    review = _new(
        session,
        CostContributionReview,
        tenant,
        revenue_basis_id=basis.id,
        inventory_member_id=prepared["inventory_member_id"],
        revision=prior.revision + 1 if prior else 1,
        supersedes_id=prior.id if prior else None,
        profile=request.profile,
        economic_at=request.economic_at,
        knowledge_at=knowledge_at if knowledge_at is not None else now(),
        introduced_event_id=event.id,
        event_sequence=event.sequence,
        action_id=action.id,
        reason=request.reason,
        content_hash="building",
    )
    member = _row(session, CostInventoryMember, tenant, review.inventory_member_id)
    from reality.services import selling_costs

    selling_costs._capture(session, tenant, request, prepared, review)
    selling = selling_costs._inputs(
        session, tenant, review, basis.document_line_id, basis.currency
    )
    digest = {
        "basis": _values(basis),
        "review": _values(review),
        "member": _values(member),
    }
    if selling is not None:
        digest["selling"] = selling
    review.content_hash = _hash(digest)
    session.flush()
    return _read(session, tenant, request.document_line_id, review_id=review.id)


def _read(
    session: Session,
    tenant: str,
    document_line_id: str,
    *,
    review_id: str | None = None,
) -> dict:
    with session.no_autoflush:
        core.get_tenant(session, tenant)
        if (
            not review_id
            and session.connection().get_isolation_level() != "READ COMMITTED"
        ):
            raise core.InvalidOperation(
                "Current contribution reads require READ COMMITTED."
            )
        _row(session, DocumentLine, tenant, document_line_id)
        if review_id:
            review = _row(session, CostContributionReview, tenant, review_id)
        else:
            review = session.scalar(
                select(CostContributionReview)
                .join(
                    CostRevenueMatchBasis,
                    (
                        CostRevenueMatchBasis.tenant_id
                        == CostContributionReview.tenant_id
                    )
                    & (
                        CostRevenueMatchBasis.id
                        == CostContributionReview.revenue_basis_id
                    ),
                )
                .where(
                    CostContributionReview.tenant_id == tenant,
                    CostRevenueMatchBasis.tenant_id == tenant,
                    CostRevenueMatchBasis.document_line_id == document_line_id,
                )
                .order_by(CostContributionReview.revision.desc())
                .limit(1)
            )
        if review is None:
            return {
                "document_line_id": document_line_id,
                "review_id": None,
                "review_state": "unreviewed",
                "db1": None,
                "db2": None,
                "db1_rate": None,
                "db2_rate": None,
                "missing_basis": ["commercial_match_not_reviewed"],
                "persistence": {"business_writes": False, "projection_writes": False},
            }
        basis = _row(session, CostRevenueMatchBasis, tenant, review.revenue_basis_id)
        if basis.document_line_id != document_line_id:
            raise core.NotFound("Contribution scope not found.")
        member = _row(session, CostInventoryMember, tenant, review.inventory_member_id)
        if (
            basis.input_schema_version != 1
            or review.profile != "commercial_v1"
            or member.kind != "issue"
            or member.movement_basis_id != basis.movement_basis_id
        ):
            raise core.InvalidOperation("Contribution input integrity mismatch.")
        from reality.services import selling_costs

        selling = selling_costs._inputs(
            session, tenant, review, basis.document_line_id, basis.currency
        )
        digest = {
            "basis": _values(basis),
            "review": _values(review),
            "member": _values(member),
        }
        if selling is not None:
            digest["selling"] = selling
        if review.content_hash != _hash(digest):
            raise core.InvalidOperation("Contribution input integrity mismatch.")
        movement = _row(session, CostMovementBasis, tenant, basis.movement_basis_id)
        inventory = inventory_cost(
            session, tenant, basis.item_id, review_id=member.review_id
        )
        if (
            inventory["currency"] != basis.currency
            or inventory["base_unit"] != basis.base_unit
        ):
            raise core.InvalidOperation("Contribution inventory integrity mismatch.")
        portions = [
            c
            for c in inventory["consumption"]
            if c["movement_id"] == movement.movement_id and c["kind"] == "issue"
        ]
        if (
            len(portions) != 1
            or portions[0]["cost"] is None
            or Decimal(portions[0]["quantity"]) != basis.quantity
            or movement.occurred_at != review.economic_at
        ):
            raise core.InvalidOperation("Contribution consumption integrity mismatch.")
        cost = portions[0]
        context = ContributionContext(
            tenant_id=tenant,
            generation_id=review.id,
            profile_revision_id=review.id,
            policy_revision_id=inventory["policy_id"],
            profile=review.profile,
            effective_at=datetime.fromisoformat(inventory["effective_at"]),
            knowledge_at=review.knowledge_at,
        )
        direct, allocated, selling_missing = selling_costs._totals(selling)
        selling_state = "unknown" if selling_missing else "reviewed"
        selling_refs = (
            tuple(row["part"]["id"] for row in selling["parts"]) if selling else ()
        )
        # The review itself supplies explicit zero/completeness evidence.
        selling_refs = selling_refs or ((review.id,) if selling else ())
        row = MatchedSlice(
            slice_id=basis.id,
            context=context,
            currency=basis.currency,
            base_unit=basis.base_unit,
            quantity=basis.quantity,
            economic_date=review.economic_at.date(),
            position_id=basis.order_line_id,
            item_id=basis.item_id,
            customer_id=basis.customer_id,
            revenue=ContributionInput(
                amount=basis.stated_net, state="reviewed", references=(basis.id,)
            ),
            goods_cost=ContributionInput(
                amount=cost["cost"],
                state="reviewed",
                references=(member.review_id, member.id),
            ),
            direct_selling_cost=ContributionInput(
                amount=direct if not selling_missing else None,
                state=selling_state,
                references=selling_refs,
            ),
            allocated_selling_cost=ContributionInput(
                amount=allocated if not selling_missing else None,
                state=selling_state,
                references=selling_refs,
            ),
        )
        result = aggregate_contribution([row], context=context).groups[0]
        stale = not review_id and _sequence(session, tenant) > review.event_sequence
        return {
            "document_line_id": document_line_id,
            "review_id": review.id,
            "revision": review.revision,
            "action_id": review.action_id,
            "reason": review.reason,
            "profile": review.profile,
            "profile_revision_id": review.id,
            "economic_at": review.economic_at.isoformat(),
            "knowledge_at": review.knowledge_at.isoformat(),
            "event_sequence": review.event_sequence,
            "review_state": "stale" if stale else "reviewed_complete_at_cutoff",
            "db1": None if stale else _money(result.db1.total),
            "db1_rate": None if stale else _money(result.db1_rate),
            "basis_db1": _money(result.db1.total),
            "db2": None if stale else _money(result.db2.total),
            "db2_rate": None if stale else _money(result.db2_rate),
            "basis_db2": _money(result.db2.total),
            "known_selling_cost": _money(direct + allocated) if selling else None,
            "known_direct_selling_cost": _money(direct) if selling else None,
            "known_allocated_selling_cost": _money(allocated) if selling else None,
            "direct_selling_cost": _money(direct) if not selling_missing else None,
            "allocated_selling_cost": _money(allocated)
            if not selling_missing
            else None,
            "currency": basis.currency,
            "base_unit": basis.base_unit,
            "missing_basis": selling_missing
            + (["contribution_review_stale"] if stale else []),
            "trace": {
                "revenue_basis_id": basis.id,
                "order_line_id": basis.order_line_id,
                "received_net": _money(basis.stated_net),
                "quantity": _money(basis.quantity),
                "invoice_date": basis.invoice_date,
                "sales_channel": basis.sales_channel,
                "customer_id": basis.customer_id,
                "item_id": basis.item_id,
                "evidence_hash": basis.evidence_hash,
                "inventory_member_id": member.id,
                "inventory_review_id": member.review_id,
                "consumption": cost,
                "formula": "reviewed net revenue - reviewed consumed acquisition cost",
                "db2_formula": "DB1 - direct selling cost - allocated selling cost",
                "selling": selling,
            },
            "persistence": {"business_writes": False, "projection_writes": False},
        }


def _batch_members(request: ContributionBatchReview) -> list[ContributionReview]:
    return [
        ContributionReview(
            **position.model_dump(),
            operation="contribution_review",
            expected_event_sequence=request.expected_event_sequence,
            reason=request.reason,
        )
        for position in sorted(request.positions, key=lambda p: p.document_line_id)
    ]


def _check_batch(
    session: Session, tenant: str, request: ContributionBatchReview
) -> dict:
    """Admit every member before creating any joint confirmation authority."""
    prepared = []
    movements = set()
    common = None
    for member in _batch_members(request):
        checked = _check(session, tenant, member)
        movement = checked["basis"]["movement_basis_id"]
        if movement in movements:
            raise core.InvalidOperation("Duplicate contribution shipment binding.")
        movements.add(movement)
        inventory = _row(
            session,
            CostInventoryReview,
            tenant,
            checked["candidate"]["trace"]["inventory_review_id"],
        )
        policy = _row(session, CostPolicyRevision, tenant, inventory.policy_id)
        context = {
            "inventory_action_id": inventory.action_id,
            "effective_at": inventory.effective_at.isoformat(),
            "inventory_knowledge_at": inventory.knowledge_at.isoformat(),
            "inventory_event_id": inventory.introduced_event_id,
            "inventory_event_sequence": inventory.target_event_sequence,
            "owner_party_id": policy.owner_party_id,
            "currency": policy.currency,
        }
        if common is not None and common != context:
            raise core.InvalidOperation(
                "Joint contributions require one compatible confirmed inventory basis."
            )
        common = context
        prepared.append(checked)
    if _sequence(session, tenant) != request.expected_event_sequence:
        raise core.Conflict("Costing preview is stale; reload the held evidence.")
    return {"context": common, "positions": prepared}


def _execute_batch(
    session: Session,
    tenant: str,
    request: ContributionBatchReview,
    prepared: dict,
    event,
    action,
) -> dict:
    # The existing owner/action gate, tenant lock and savepoint surround all members.
    reviews = [
        _execute(
            session,
            tenant,
            member,
            checked,
            event,
            action,
            knowledge_at=event.recorded_at,
        )
        for member, checked in zip(
            _batch_members(request), prepared["positions"], strict=True
        )
    ]
    return {
        "action_id": action.id,
        "profile_scope_action_id": action.id,
        "profile": "commercial_v1",
        **prepared["context"],
        "knowledge_at": event.recorded_at.astimezone(UTC).isoformat(),
        "event_sequence": event.sequence,
        "reviews": reviews,
    }
