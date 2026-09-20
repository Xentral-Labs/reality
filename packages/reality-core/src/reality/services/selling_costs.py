"""Bounded selling attribution and immutable contribution-review membership."""

from decimal import Decimal

from sqlalchemy import exists, select
from sqlalchemy.orm import aliased

from reality.db.components import FinancialComponent
from reality.db.contribution import (
    CostSellingPart,
    CostSellingReviewCategory,
    CostSellingReviewMember,
)
from reality.db.core import Document, DocumentLine, now
from reality.db.costing import CostAttribution, CostAttributionPart, CostComponentBasis
from reality.domain.costing import (
    SELLING_CATEGORIES,
    AllocationTarget,
    SellingAllocate,
    SellingAssign,
    allocate_weighted,
)
from reality.services import core
from reality.services.costing import (
    _admit_component,
    _latest,
    _money,
    _new,
    _row,
    cost_evidence,
)
from reality.services.inventory_costing import _values

LIMIT = 100


def _resolve_allocation(request: SellingAllocate, amount: Decimal, effect: int):
    targets = [
        AllocationTarget(
            target_id=f"{target.document_line_id}:{target.category}",
            weight=target.weight if request.driver_kind == "manual" else Decimal(1),
        )
        for target in request.targets
    ]
    try:
        allocation = allocate_weighted(amount, request.allocation_total, targets)
    except ValueError as error:
        raise core.InvalidOperation(str(error)) from error
    parts = []
    trace = []
    for target, weighted in zip(request.targets, targets, strict=True):
        share = allocation.shares[weighted.target_id]
        if share:
            parts.append(
                {
                    "document_line_id": target.document_line_id,
                    "category": target.category,
                    "source_share": share,
                    "cost_effect": effect,
                    "assignment_kind": "allocated",
                    "conversion_basis_revision_id": request.conversion_basis_revision_id,
                }
            )
        trace.append(
            {
                "document_line_id": target.document_line_id,
                "category": target.category,
                "weight": format(weighted.weight, "f"),
                "source_share": _money(share),
            }
        )
    resolved = SellingAssign(
        **request.model_dump(
            exclude={
                "operation",
                "allocation_total",
                "driver_kind",
                "conversion_basis_revision_id",
                "targets",
            }
        ),
        operation="selling_assign",
        parts=parts,
    )
    return resolved, {"driver_kind": request.driver_kind, "shares": trace}


def _family_used(session, tenant, basis_id, model):
    return (
        session.scalar(
            select(model.id)
            .join(
                CostAttribution,
                (CostAttribution.tenant_id == model.tenant_id)
                & (CostAttribution.id == model.attribution_revision_id),
            )
            .where(
                model.tenant_id == tenant,
                CostAttribution.tenant_id == tenant,
                CostAttribution.component_basis_id == basis_id,
            )
            .limit(1)
        )
        is not None
    )


def _active(session, tenant, line_id):
    newer = aliased(CostAttribution)
    rows = list(
        session.scalars(
            select(CostSellingPart)
            .join(
                CostAttribution,
                (CostAttribution.tenant_id == CostSellingPart.tenant_id)
                & (CostAttribution.id == CostSellingPart.attribution_revision_id),
            )
            .where(
                CostSellingPart.tenant_id == tenant,
                CostSellingPart.document_line_id == line_id,
                CostAttribution.tenant_id == tenant,
                CostAttribution.state == "assigned",
                ~exists(
                    select(newer.id).where(
                        newer.tenant_id == tenant,
                        newer.component_basis_id == CostAttribution.component_basis_id,
                        newer.revision > CostAttribution.revision,
                    )
                ),
            )
            .order_by(CostSellingPart.id)
            .limit(LIMIT + 1)
        )
    )
    if len(rows) > LIMIT:
        raise core.InvalidOperation("Selling part bound exceeded.")
    return rows


def _check(session, tenant, request):
    received = cost_evidence(
        session, tenant, request.document_id, request.document_line_id
    )
    if received["evidence_hash"] != request.expected_evidence_hash:
        raise core.Conflict("Selling evidence preview is stale.")
    raw = received["amounts"]["net"]
    if raw is None:
        raise core.InvalidOperation("Received net selling amount is required.")
    amount = Decimal(raw)
    tax = received["amounts"]["tax"]
    if (
        request.tax_treatment == "not_applicable"
        and tax is not None
        and Decimal(tax) != 0
    ):
        raise core.InvalidOperation("Stated nonzero tax cannot be not applicable.")
    doc = _row(session, Document, tenant, request.document_id)
    effect = -1 if doc.type == "supplier_credit_note" else 1
    allocation = None
    if isinstance(request, SellingAllocate):
        request, allocation = _resolve_allocation(request, amount, effect)
    if any(p.cost_effect != effect for p in request.parts):
        raise core.InvalidOperation(
            "Selling effect must follow invoice or credit semantics."
        )
    if any(amount == 0 or (p.source_share > 0) != (amount > 0) for p in request.parts):
        raise core.InvalidOperation("Selling shares must preserve the received sign.")
    if sum((abs(p.source_share) for p in request.parts), Decimal(0)) > abs(amount):
        raise core.InvalidOperation("Selling shares exceed the received net amount.")
    basis = (
        session.scalar(
            select(CostComponentBasis).where(
                CostComponentBasis.tenant_id == tenant,
                CostComponentBasis.component_id == received["component_id"],
            )
        )
        if received["component_id"]
        else None
    )
    if basis and _family_used(session, tenant, basis.id, CostAttributionPart):
        raise core.InvalidOperation(
            "Acquisition evidence cannot also fund selling costs."
        )
    effects = []
    for line_id in {p.document_line_id for p in request.parts}:
        line = _row(session, DocumentLine, tenant, line_id)
        target = _row(session, Document, tenant, line.document_id)
        if target.type != "sales_invoice":
            raise core.InvalidOperation(
                "Selling target must be an exact sales invoice line."
            )
        related = [p for p in request.parts if p.document_line_id == line_id]
        for part in related:
            if part.conversion_basis_revision_id:
                from reality.domain.costing import convert_amount
                from reality.services.cost_conversions import read_basis

                conversion = read_basis(
                    session, tenant, part.conversion_basis_revision_id, kind="currency"
                )
                if (
                    conversion.from_code != received["currency"]
                    or conversion.to_code != target.currency
                ):
                    raise core.InvalidOperation(
                        "Selling conversion does not match source and target currencies."
                    )
                effects.append(
                    convert_amount(
                        abs(part.source_share),
                        conversion.numerator,
                        conversion.denominator,
                    )
                    * part.cost_effect
                )
            elif target.currency != received["currency"]:
                raise core.InvalidOperation("Selling currency conversion is unsupported.")
            else:
                effects.append(abs(part.source_share) * part.cost_effect)
        active = _active(session, tenant, line_id)
        retained = [
            p
            for p in active
            if not basis
            or _row(
                session, CostAttribution, tenant, p.attribution_revision_id
            ).component_basis_id
            != basis.id
        ]
        if (
            len(retained) + sum(p.document_line_id == line_id for p in request.parts)
            > LIMIT
        ):
            raise core.InvalidOperation("Selling part bound would be exceeded.")
    result = {
        "received": received,
        "assigned_effect": _money(sum(effects, Decimal(0))),
        "unassigned_basis": _money(
            amount - sum((p.source_share for p in request.parts), Decimal(0))
        ),
    }
    if allocation is not None:
        result["allocation"] = allocation
    return result


def _execute(session, tenant, request, prepared, event, action):
    if isinstance(request, SellingAllocate):
        amount = Decimal(prepared["received"]["amounts"]["net"])
        document = _row(session, Document, tenant, request.document_id)
        effect = -1 if document.type == "supplier_credit_note" else 1
        request = _resolve_allocation(request, amount, effect)[0]
    basis = _admit_component(session, tenant, request, prepared["received"], event)
    prior = _latest(session, tenant, basis.id, event.sequence)
    row = _new(
        session,
        CostAttribution,
        tenant,
        component_basis_id=basis.id,
        revision=prior.revision + 1 if prior else 1,
        supersedes_id=prior.id if prior else None,
        introduced_event_id=event.id,
        action_id=action.id,
        effective_at=now(),
        reason=request.reason,
        state="assigned",
        basis="net",
        tax_treatment=request.tax_treatment,
        selected_basis_tax_inclusion="excluded",
        nonrecoverable_tax_amount=Decimal(0),
    )
    for part in request.parts:
        _new(
            session,
            CostSellingPart,
            tenant,
            attribution_revision_id=row.id,
            **part.model_dump(),
        )
    return {
        "component_basis_id": basis.id,
        "attribution_revision_id": row.id,
        "revision": row.revision,
        **{k: prepared[k] for k in ("assigned_effect", "unassigned_basis")},
    }


def _check_review(session, tenant, request):
    if request.selling_categories is None:
        return None
    parts = _active(session, tenant, request.document_line_id)
    present = {p.category for p in parts}
    for category in request.selling_categories:
        if (
            category.disposition in {"confirmed_zero", "not_applicable"}
            and category.category in present
        ):
            raise core.InvalidOperation(
                "Attributed selling category cannot be zero/not applicable."
            )
    return [p.id for p in parts]


def _capture(session, tenant, request, prepared, review):
    if request.selling_categories is None:
        return
    for category in request.selling_categories:
        _new(
            session,
            CostSellingReviewCategory,
            tenant,
            review_id=review.id,
            **category.model_dump(),
        )
    for identity in prepared["selling_parts"]:
        _new(
            session,
            CostSellingReviewMember,
            tenant,
            review_id=review.id,
            part_id=identity,
        )


def _inputs(session, tenant, review, line_id, currency):
    categories = list(
        session.scalars(
            select(CostSellingReviewCategory)
            .where(
                CostSellingReviewCategory.tenant_id == tenant,
                CostSellingReviewCategory.review_id == review.id,
            )
            .order_by(CostSellingReviewCategory.category)
            .limit(len(SELLING_CATEGORIES) + 1)
        )
    )
    members = list(
        session.scalars(
            select(CostSellingReviewMember)
            .where(
                CostSellingReviewMember.tenant_id == tenant,
                CostSellingReviewMember.review_id == review.id,
            )
            .order_by(CostSellingReviewMember.part_id)
            .limit(LIMIT + 1)
        )
    )
    if not categories and not members:
        return None
    if (
        len(members) > LIMIT
        or {c.category for c in categories} != set(SELLING_CATEGORIES)
        or len(categories) != len(SELLING_CATEGORIES)
    ):
        raise core.InvalidOperation("Selling review membership integrity mismatch.")
    rows = []
    for member in members:
        part = _row(session, CostSellingPart, tenant, member.part_id)
        revision = _row(session, CostAttribution, tenant, part.attribution_revision_id)
        basis = _row(session, CostComponentBasis, tenant, revision.component_basis_id)
        component = _row(session, FinancialComponent, tenant, basis.component_id)
        conversion = None
        if part.conversion_basis_revision_id:
            from reality.domain.costing import convert_amount
            from reality.services.cost_conversions import read_basis

            conversion = read_basis(
                session, tenant, part.conversion_basis_revision_id, kind="currency"
            )
        if (
            part.document_line_id != line_id
            or (
                conversion is None
                and component.currency != currency
            )
            or (
                conversion is not None
                and (
                    conversion.from_code != component.currency
                    or conversion.to_code != currency
                )
            )
            or basis.input_schema_version != 1
            or revision.state != "assigned"
            or revision.basis != "net"
            or revision.tax_treatment not in {"recoverable", "not_applicable"}
        ):
            raise core.InvalidOperation("Selling input integrity mismatch.")
        part_values = _values(part)
        part_values["cost_share"] = (
            format(
                convert_amount(
                    abs(part.source_share),
                    conversion.numerator,
                    conversion.denominator,
                ),
                "f",
            )
            if conversion
            else format(abs(part.source_share), "f")
        )
        rows.append(
            {
                "member": _values(member),
                "part": part_values,
                "revision": _values(revision),
                "basis": _values(basis),
                "component": _values(component),
            }
        )
    return {"categories": [_values(c) for c in categories], "parts": rows}


def _totals(inputs):
    if inputs is None:
        return Decimal(0), Decimal(0), ["selling_costs_unknown"]
    direct, allocated = Decimal(0), Decimal(0)
    present = set()
    for row in inputs["parts"]:
        part = row["part"]
        value = Decimal(part["cost_share"]) * part["cost_effect"]
        if part["assignment_kind"] == "direct":
            direct += value
        else:
            allocated += value
        present.add(part["category"])
    missing = []
    for category in inputs["categories"]:
        if category["disposition"] == "unresolved" or (
            category["disposition"] == "evidenced"
            and category["category"] not in present
        ):
            missing.append("selling_category:" + category["category"])
        if (
            category["disposition"] in {"confirmed_zero", "not_applicable"}
            and category["category"] in present
        ):
            raise core.InvalidOperation(
                "Selling review contradicts attributed evidence."
            )
    return direct, allocated, missing
