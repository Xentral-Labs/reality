"""Confirmed partial commercial matching over retained source and cost evidence."""

from decimal import Decimal

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.components import FinancialComponent
from reality.db.contribution import (
    CostCommercialDirectPart,
    CostCommercialInventoryPart,
    CostCommercialMatchRevision,
)
from reality.db.core import Document, DocumentLine
from reality.db.costing import CostAttribution, CostAttributionPart, CostComponentBasis
from reality.db.inventory_costing import CostInventoryMember, CostMovementBasis
from reality.domain.contribution import (
    CommercialInventoryPart,
    CommercialMatchLine,
    ContributionRefusal,
    admit_commercial_matches,
)
from reality.services import core
from reality.services.costing import _hash, _money, _new, _row
from reality.services.finance import components
from reality.services.inventory_costing import _values


def _inventory_portion(session: Session, tenant: str, part) -> dict:
    member = _row(session, CostInventoryMember, tenant, part.inventory_member_id)
    movement = _row(session, CostMovementBasis, tenant, member.movement_basis_id)
    entry = _row(session, CostMovementBasis, tenant, part.entry_movement_basis_id)
    receipt = _row(session, CostMovementBasis, tenant, part.receipt_movement_basis_id)
    from reality.db.inventory_costing import CostInventoryReview, CostPolicyRevision
    from reality.services.costing import inventory_cost

    review = _row(session, CostInventoryReview, tenant, member.review_id)
    policy = _row(session, CostPolicyRevision, tenant, review.policy_id)
    inventory = inventory_cost(session, tenant, policy.item_id, review_id=review.id)
    collection = inventory["returns"] if member.kind == "customer_return" else inventory["consumption"]
    rows = [row for row in collection if row["movement_id"] == movement.movement_id]
    if len(rows) != 1:
        raise core.InvalidOperation("Commercial inventory member has no exact frozen observation.")
    original_movement_id = None
    if part.original_issue_member_id:
        original = _row(session, CostInventoryMember, tenant, part.original_issue_member_id)
        original_basis = _row(session, CostMovementBasis, tenant, original.movement_basis_id)
        if original.kind != "issue" or original.review_id != member.review_id:
            raise core.InvalidOperation("Original issue must belong to the same inventory review.")
        original_movement_id = original_basis.movement_id
    matches = [
        portion
        for portion in rows[0]["parts"]
        if portion["entry_movement_id"] == entry.movement_id
        and portion["receipt_movement_id"] == receipt.movement_id
        and portion.get("issue_movement_id") == original_movement_id
    ]
    if len(matches) != 1:
        raise core.InvalidOperation("Commercial inventory portion is not an exact frozen cost portion.")
    frozen = matches[0]
    return {
        "key": (
            member.id,
            entry.id,
            receipt.id,
            part.original_issue_member_id,
        ),
        "quantity": abs(Decimal(frozen["quantity"])),
        "cost": None if frozen["cost"] is None else Decimal(frozen["cost"]),
        "currency": inventory["currency"],
        "base_unit": inventory["base_unit"],
    }


def _active_usage(session: Session, tenant: str, excluded_line_id: str) -> dict:
    revisions = list(
        session.scalars(
            select(CostCommercialMatchRevision)
            .where(CostCommercialMatchRevision.tenant_id == tenant)
            .order_by(
                CostCommercialMatchRevision.document_line_id,
                CostCommercialMatchRevision.revision.desc(),
            )
        )
    )
    latest = {}
    for revision in revisions:
        latest.setdefault(revision.document_line_id, revision)
    active_ids = [
        revision.id
        for line_id, revision in latest.items()
        if line_id != excluded_line_id and revision.goods_cost_disposition == "inventory"
    ]
    used = {}
    if not active_ids:
        return used
    for part in session.scalars(
        select(CostCommercialInventoryPart).where(
            CostCommercialInventoryPart.tenant_id == tenant,
            CostCommercialInventoryPart.match_revision_id.in_(active_ids),
        )
    ):
        key = (
            part.inventory_member_id,
            part.entry_movement_basis_id,
            part.receipt_movement_basis_id,
            part.original_issue_member_id,
        )
        used[key] = used.get(key, Decimal(0)) + part.quantity
    return used


def _direct_observation(session: Session, tenant: str, attribution_id: str) -> dict:
    attribution = _row(session, CostAttribution, tenant, attribution_id)
    basis = _row(session, CostComponentBasis, tenant, attribution.component_basis_id)
    component = _row(session, FinancialComponent, tenant, basis.component_id)
    from reality.services.costing import _basis_supported

    if attribution.state != "assigned" or not _basis_supported(attribution):
        raise core.InvalidOperation("Direct commercial evidence is not a supported assignment.")
    parts = list(
        session.scalars(
            select(CostAttributionPart).where(
                CostAttributionPart.tenant_id == tenant,
                CostAttributionPart.attribution_revision_id == attribution.id,
            )
        )
    )
    if not parts:
        raise core.InvalidOperation("Direct commercial evidence has no retained cost portions.")
    selected = sum(
        (abs(part.source_share) for part in parts if part.amount_bucket == "selected_basis"),
        Decimal(0),
    )
    tax = sum(
        (
            abs(part.source_share)
            for part in parts
            if part.amount_bucket == "nonrecoverable_tax"
        ),
        Decimal(0),
    )
    stated = getattr(component, "stated_" + attribution.basis)
    if (
        stated is None
        or selected != abs(stated)
        or tax != abs(attribution.nonrecoverable_tax_amount)
    ):
        raise core.InvalidOperation(
            "Direct commercial evidence requires one complete retained attribution."
        )
    amount = sum(
        (abs(part.source_share) * part.cost_effect for part in parts), Decimal(0)
    )
    return {
        "attribution": attribution,
        "component_basis": basis,
        "component": component,
        "parts": parts,
        "amount": amount,
        "currency": component.currency,
    }


def _evidence(session: Session, tenant: str, line_id: str) -> dict:
    line = _row(session, DocumentLine, tenant, line_id)
    document = _row(session, Document, tenant, line.document_id)
    if document.type not in {"sales_invoice", "credit_note"}:
        raise core.InvalidOperation("Commercial matching requires sales evidence.")
    received = components._received(session, tenant, document, line)
    net = received["amounts"]["net"]
    if net is None:
        raise core.InvalidOperation("Commercial matching requires stated net revenue.")
    flow = "credit" if document.type == "credit_note" else "sale"
    quantity = Decimal(line.quantity)
    stated_net = Decimal(net)
    if flow == "credit":
        quantity = -abs(quantity)
        stated_net = -abs(stated_net)
    return {
        "line": line,
        "document": document,
        "received": received,
        "flow": flow,
        "quantity": quantity,
        "stated_net": stated_net,
    }


def _check(session: Session, tenant: str, request) -> dict:
    evidence = _evidence(session, tenant, request.document_line_id)
    if evidence["received"]["evidence_hash"] != request.expected_evidence_hash:
        raise core.Conflict("Commercial evidence preview is stale.")
    inventory_parts = tuple(
        CommercialInventoryPart(
            member_id=part.inventory_member_id,
            entry_basis_id=part.entry_movement_basis_id,
            receipt_basis_id=part.receipt_movement_basis_id,
            original_issue_member_id=part.original_issue_member_id,
            quantity=part.quantity,
        )
        for part in request.inventory_parts
    )
    try:
        line = CommercialMatchLine(
            line_id=request.document_line_id,
            flow=evidence["flow"],
            stated_net=evidence["stated_net"],
            stated_quantity=evidence["quantity"],
            disposition=request.goods_cost_disposition,
            inventory_parts=inventory_parts,
            direct_revision_ids=tuple(
                part.attribution_revision_id for part in request.direct_parts
            ),
            direct_cost_complete=request.direct_cost_complete,
        )
    except ValidationError as error:
        raise core.InvalidOperation(str(error)) from error
    capacities = {}
    for part in request.inventory_parts:
        frozen = _inventory_portion(session, tenant, part)
        if frozen["currency"] != evidence["document"].currency or frozen["base_unit"] != evidence["line"].unit:
            raise core.InvalidOperation("Commercial inventory currency or unit mismatch.")
        capacities[frozen["key"]] = frozen["quantity"]
    for key, quantity in _active_usage(session, tenant, request.document_line_id).items():
        if key in capacities:
            capacities[key] -= quantity
    try:
        admit_commercial_matches((line,), capacities)
    except ContributionRefusal as error:
        raise core.InvalidOperation(error.code) from error
    for part in request.direct_parts:
        direct = _direct_observation(session, tenant, part.attribution_revision_id)
        if direct["currency"] != evidence["document"].currency:
            raise core.InvalidOperation("Direct commercial evidence currency mismatch.")
    return {
        "document_line_id": request.document_line_id,
        "order_line_id": evidence["line"].billed_document_line_id,
        "stated_net": _money(evidence["stated_net"]),
        "stated_quantity": _money(evidence["quantity"]),
        "currency": evidence["document"].currency,
        "base_unit": evidence["line"].unit,
        "evidence_hash": evidence["received"]["evidence_hash"],
        "goods_cost_disposition": request.goods_cost_disposition,
        "inventory_parts": [part.model_dump(mode="json") for part in request.inventory_parts],
        "direct_parts": [part.model_dump(mode="json") for part in request.direct_parts],
    }


def _execute(session, tenant, request, prepared, event, action) -> dict:
    prior = session.scalar(
        select(CostCommercialMatchRevision)
        .where(
            CostCommercialMatchRevision.tenant_id == tenant,
            CostCommercialMatchRevision.document_line_id == request.document_line_id,
        )
        .order_by(CostCommercialMatchRevision.revision.desc())
        .limit(1)
    )
    revision = _new(
        session,
        CostCommercialMatchRevision,
        tenant,
        document_line_id=request.document_line_id,
        order_line_id=prepared["order_line_id"],
        revision=prior.revision + 1 if prior else 1,
        supersedes_id=prior.id if prior else None,
        stated_net=Decimal(prepared["stated_net"]),
        stated_quantity=Decimal(prepared["stated_quantity"]),
        currency=prepared["currency"],
        base_unit=prepared["base_unit"],
        evidence_hash=prepared["evidence_hash"],
        goods_cost_disposition=request.goods_cost_disposition,
        profile=request.profile,
        introduced_event_id=event.id,
        action_id=action.id,
        reason=request.reason,
        input_schema_version=1,
        content_hash="building",
    )
    inventory = [
        _new(
            session,
            CostCommercialInventoryPart,
            tenant,
            match_revision_id=revision.id,
            inventory_member_id=part.inventory_member_id,
            original_issue_member_id=part.original_issue_member_id,
            entry_movement_basis_id=part.entry_movement_basis_id,
            receipt_movement_basis_id=part.receipt_movement_basis_id,
            quantity=part.quantity,
            input_schema_version=1,
        )
        for part in request.inventory_parts
    ]
    direct = [
        _new(
            session,
            CostCommercialDirectPart,
            tenant,
            match_revision_id=revision.id,
            attribution_revision_id=part.attribution_revision_id,
            input_role=part.input_role,
            input_schema_version=1,
        )
        for part in request.direct_parts
    ]
    digest = {
        "revision": _values(revision),
        "inventory_parts": [_values(row) for row in sorted(inventory, key=lambda row: row.id)],
        "direct_parts": [_values(row) for row in sorted(direct, key=lambda row: row.id)],
    }
    revision.content_hash = _hash(digest)
    session.flush()
    return {
        "match_revision_id": revision.id,
        "document_line_id": revision.document_line_id,
        "revision": revision.revision,
        "supersedes_id": revision.supersedes_id,
        "profile": revision.profile,
        "goods_cost_disposition": revision.goods_cost_disposition,
        "stated_net": _money(revision.stated_net),
        "stated_quantity": _money(revision.stated_quantity),
        "currency": revision.currency,
        "base_unit": revision.base_unit,
        "inventory_part_ids": [row.id for row in inventory],
        "direct_part_ids": [row.id for row in direct],
        "content_hash": revision.content_hash,
        "action_id": action.id,
        "event_sequence": event.sequence,
    }


def _read(
    session: Session,
    tenant: str,
    document_line_id: str,
    *,
    match_revision_id: str | None = None,
) -> dict:
    """Derive a commercial observation from retained references without writes."""
    _row(session, DocumentLine, tenant, document_line_id)
    if match_revision_id:
        revision = _row(
            session, CostCommercialMatchRevision, tenant, match_revision_id
        )
        if revision.document_line_id != document_line_id:
            raise core.NotFound("Commercial match scope not found.")
    else:
        revision = session.scalar(
            select(CostCommercialMatchRevision)
            .where(
                CostCommercialMatchRevision.tenant_id == tenant,
                CostCommercialMatchRevision.document_line_id == document_line_id,
            )
            .order_by(CostCommercialMatchRevision.revision.desc())
            .limit(1)
        )
    if revision is None:
        return {
            "document_line_id": document_line_id,
            "match_revision_id": None,
            "review_state": "unreviewed",
            "db1": None,
            "missing_basis": ["commercial_match_not_reviewed"],
            "persistence": {"business_writes": False, "projection_writes": False},
        }
    inventory = list(
        session.scalars(
            select(CostCommercialInventoryPart)
            .where(
                CostCommercialInventoryPart.tenant_id == tenant,
                CostCommercialInventoryPart.match_revision_id == revision.id,
            )
            .order_by(CostCommercialInventoryPart.id)
        )
    )
    direct = list(
        session.scalars(
            select(CostCommercialDirectPart)
            .where(
                CostCommercialDirectPart.tenant_id == tenant,
                CostCommercialDirectPart.match_revision_id == revision.id,
            )
            .order_by(CostCommercialDirectPart.id)
        )
    )
    digest = {
        "revision": _values(revision),
        "inventory_parts": [_values(row) for row in inventory],
        "direct_parts": [_values(row) for row in direct],
    }
    if revision.content_hash != _hash(digest):
        raise core.InvalidOperation("Commercial match input integrity mismatch.")
    goods_cost = Decimal(0)
    missing = []
    if revision.goods_cost_disposition == "inventory":
        for part in inventory:
            frozen = _inventory_portion(session, tenant, part)
            if frozen["cost"] is None:
                missing.append("commercial_inventory_cost_unknown")
                continue
            goods_cost += frozen["cost"] * part.quantity / frozen["quantity"]
    elif revision.goods_cost_disposition == "direct_evidence":
        for part in direct:
            goods_cost += _direct_observation(
                session, tenant, part.attribution_revision_id
            )["amount"]
    elif revision.goods_cost_disposition == "unresolved":
        missing.append("commercial_goods_cost_unresolved")
    if revision.stated_quantity < 0:
        goods_cost = -abs(goods_cost)
    complete = not missing
    db1 = revision.stated_net - goods_cost if complete else None
    matched_quantity = (
        sum((part.quantity for part in inventory), Decimal(0))
        if revision.goods_cost_disposition == "inventory"
        else abs(revision.stated_quantity)
        if complete
        else Decimal(0)
    )
    return {
        "document_line_id": document_line_id,
        "match_revision_id": revision.id,
        "revision": revision.revision,
        "supersedes_id": revision.supersedes_id,
        "action_id": revision.action_id,
        "profile": revision.profile,
        "goods_cost_disposition": revision.goods_cost_disposition,
        "review_state": "reviewed_complete" if complete else "incomplete",
        "stated_net": _money(revision.stated_net),
        "stated_quantity": _money(revision.stated_quantity),
        "goods_cost": _money(goods_cost) if complete else None,
        "db1": _money(db1),
        "currency": revision.currency,
        "base_unit": revision.base_unit,
        "coverage": {
            "matched_quantity": _money(
                matched_quantity.copy_sign(revision.stated_quantity)
            ),
            "stated_quantity": _money(revision.stated_quantity),
            "complete": complete
            and matched_quantity == abs(revision.stated_quantity),
        },
        "missing_basis": missing,
        "trace": {
            "evidence_hash": revision.evidence_hash,
            "inventory_part_ids": [row.id for row in inventory],
            "direct_part_ids": [row.id for row in direct],
            "formula": "source-stated net revenue - frozen matched goods cost",
        },
        "persistence": {"business_writes": False, "projection_writes": False},
    }
