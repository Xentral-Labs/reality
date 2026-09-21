"""Receipt acquisition costs derived from held amounts and confirmed attribution.

No read normalizes evidence, writes a snapshot, schedules work or invents missing costs.
"""

import hashlib
import json
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal

from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from reality.db.components import FinancialComponent
from reality.db.core import (
    AppUser,
    BusinessEvent,
    ChangeProposal,
    Document,
    DocumentLine,
    InterpretationRecordReference,
    Item,
    Movement,
    MovementCorrection,
    TenantMembership,
    now,
    uid,
)
from reality.db.costing import (
    CostAttribution,
    CostAttributionPart,
    CostComponentBasis,
    CostComponentReplacement,
    CostCorrectionBasis,
    CostInputManifest,
    CostManifestAttribution,
    CostManifestComponent,
    CostManifestCorrection,
    CostManifestReceipt,
    CostManifestReplacement,
    CostReceiptBasis,
    CostReviewCategory,
    CostScopeReview,
)
from reality.domain.costing import (
    CATEGORIES,
    CHANGE,
    Allocate,
    AllocationTarget,
    Assign,
    CommercialMatchReview,
    ContributionBatchReview,
    ContributionReview,
    ConversionBasisReview,
    InventoryBatchReview,
    InventoryReview,
    Replace,
    Review,
    SellingAllocate,
    SellingAssign,
    ValuationAssessment,
    Withdraw,
    allocate_weighted,
    contribution,
    convert_amount,
    validate_shares,
)
from reality.services import core
from reality.services.business_locks import lock_delivery_state
from reality.services.core import emit_business_event
from reality.services.finance import components
from reality.services.memberships import Principal

ZERO = Decimal(0)
LIMIT = 100


def _money(value):
    return (
        None
        if value is None
        else format(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN), "f")
    )


def _hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def _row(session, model, tenant, identity):
    value = session.scalar(
        select(model).where(model.tenant_id == tenant, model.id == identity)
    )
    if value is None:
        raise core.NotFound("Costing scope not found.")
    return value


def _sequence(session, tenant, *, inputs_only=False, cutoff=None):
    statement = select(func.max(BusinessEvent.sequence)).where(
        BusinessEvent.tenant_id == tenant
    )
    if cutoff is not None:
        statement = statement.where(BusinessEvent.sequence <= cutoff)
    if inputs_only:
        statement = statement.where(BusinessEvent.event_type != "cost.reviewed")
    return int(session.scalar(statement) or 0)


def _owner(session, tenant, principal, *, lock=False):
    if principal is None:
        raise core.InvalidOperation(
            "An authenticated active company owner is required."
        )
    from reality.services.tenant_policy import profile_cost_owner_active

    if profile_cost_owner_active(session, tenant, principal.user_id):
        return
    statement = (
        select(TenantMembership.role, AppUser.status)
        .join(AppUser, AppUser.id == TenantMembership.user_id)
        .where(
            TenantMembership.tenant_id == tenant,
            TenantMembership.user_id == principal.user_id,
            TenantMembership.status == "active",
        )
    )
    if lock:
        statement = statement.with_for_update()
    authority = session.execute(statement).first()
    if authority is None:
        raise core.NotFound("Company not found.")
    if authority.role != "owner" or authority.status != "active":
        raise core.InvalidOperation("An active company owner is required.")


def _request(arguments):
    try:
        return CHANGE.validate_python(arguments)
    except ValidationError as error:
        raise core.InvalidOperation(str(error)) from error


def cost_evidence(
    session: Session,
    tenant_id: str,
    document_id: str,
    document_line_id: str | None = None,
) -> dict:
    """Read exact received fields, including not-yet-normalized supplier evidence."""
    with session.no_autoflush:
        core.get_tenant(session, tenant_id)
        doc = _row(session, Document, tenant_id, document_id)
        if doc.type not in {"supplier_invoice", "supplier_credit_note"}:
            raise core.InvalidOperation(
                "Receipt costs require supplier invoice or credit evidence."
            )
        line = (
            _row(session, DocumentLine, tenant_id, document_line_id)
            if document_line_id
            else None
        )
        if line and line.document_id != doc.id:
            raise core.NotFound("Costing scope not found.")
        if not line and session.scalar(
            select(DocumentLine.id)
            .where(
                DocumentLine.tenant_id == tenant_id, DocumentLine.document_id == doc.id
            )
            .limit(1)
        ):
            raise core.InvalidOperation(
                "Use a received line, not its duplicate document total."
            )
        received = components._received(session, tenant_id, doc, line)
        component = components._component(
            session, tenant_id, doc.id, line.id if line else None
        )
        if component and (
            components._stored_amounts(component) != received["amounts"]
            or component.currency != received["currency"]
        ):
            raise core.Conflict(
                "Received evidence changed; record replacement evidence instead."
            )
        return {
            **received,
            "event_sequence": _sequence(session, tenant_id),
            "component_id": component.id if component else None,
        }


def _movement(session, tenant, identity):
    movement = _row(session, Movement, tenant, identity)
    if (
        movement.type != "receipt"
        or movement.quantity <= 0
        or movement.resolves_movement_id
    ):
        raise core.InvalidOperation(
            "This slice supports positive goods receipts, not returns or inventory valuation."
        )
    return movement


def _resolve_allocation(session, tenant, request: Allocate) -> tuple[Assign, dict]:
    resolved = []
    trace = []
    for target in request.targets:
        movement = _movement(session, tenant, target.movement_id)
        weight = (
            target.weight
            if request.driver_kind == "manual"
            else Decimal(1)
            if request.driver_kind == "equal"
            else movement.quantity
        )
        resolved.append(AllocationTarget(target_id=movement.id, weight=weight))
        trace.append(
            {
                "movement_id": movement.id,
                "weight": _money(weight)
                if request.driver_kind == "quantity"
                else format(weight, "f"),
            }
        )
    capacity = (
        request.nonrecoverable_tax_amount
        if request.amount_bucket == "nonrecoverable_tax"
        else request.allocation_total
    )
    try:
        allocation = allocate_weighted(capacity, request.allocation_total, resolved)
    except ValueError as error:
        raise core.InvalidOperation(str(error)) from error
    parts = [
        {
            "movement_id": target.target_id,
            "category": request.category,
            "source_share": allocation.shares[target.target_id],
            "cost_effect": request.cost_effect,
            "amount_bucket": request.amount_bucket,
            "assignment_kind": "allocated",
            "conversion_basis_revision_id": request.conversion_basis_revision_id,
        }
        for target in resolved
        if allocation.shares[target.target_id] != 0
    ]
    assign = Assign(
        **request.model_dump(
            exclude={
                "operation",
                "allocation_total",
                "category",
                "cost_effect",
                "amount_bucket",
                "driver_kind",
                "conversion_basis_revision_id",
                "targets",
            }
        ),
        operation="assign",
        parts=parts,
    )
    shares = {row["movement_id"]: row["source_share"] for row in parts}
    for row in trace:
        row["source_share"] = _money(shares.get(row["movement_id"], ZERO))
    return assign, {"driver_kind": request.driver_kind, "shares": trace}


def _receipt(session, tenant, movement):
    return session.scalar(
        select(CostReceiptBasis).where(
            CostReceiptBasis.tenant_id == tenant,
            CostReceiptBasis.movement_id == movement,
        )
    )


def _latest(session, tenant, basis, cursor):
    return session.scalar(
        select(CostAttribution)
        .join(
            BusinessEvent,
            (BusinessEvent.tenant_id == CostAttribution.tenant_id)
            & (BusinessEvent.id == CostAttribution.introduced_event_id),
        )
        .where(
            CostAttribution.tenant_id == tenant,
            CostAttribution.component_basis_id == basis,
            BusinessEvent.sequence <= cursor,
        )
        .order_by(CostAttribution.revision.desc())
        .limit(1)
    )


def _attributions(session, tenant, receipt_id, cursor):
    newer = aliased(CostAttribution)
    newer_event = aliased(BusinessEvent)
    latest = (
        ~select(newer.id)
        .join(
            newer_event,
            (newer_event.tenant_id == newer.tenant_id)
            & (newer_event.id == newer.introduced_event_id),
        )
        .where(
            newer.tenant_id == tenant,
            newer.component_basis_id == CostAttribution.component_basis_id,
            newer.revision > CostAttribution.revision,
            newer_event.sequence <= cursor,
        )
        .exists()
    )
    statement = (
        select(CostAttribution)
        .join(
            BusinessEvent,
            (BusinessEvent.tenant_id == CostAttribution.tenant_id)
            & (BusinessEvent.id == CostAttribution.introduced_event_id),
        )
        .where(
            CostAttribution.tenant_id == tenant,
            BusinessEvent.sequence <= cursor,
            CostAttribution.state == "assigned",
            latest,
            select(CostAttributionPart.id)
            .where(
                CostAttributionPart.tenant_id == tenant,
                CostAttributionPart.attribution_revision_id == CostAttribution.id,
                CostAttributionPart.receipt_basis_id == receipt_id,
            )
            .exists(),
        )
        .order_by(CostAttribution.id)
        .limit(LIMIT + 1)
    )
    result = list(session.scalars(statement))
    if len(result) > LIMIT:
        raise core.InvalidOperation(
            "Receipt cost scope exceeds the supported 100 component bound."
        )
    return result


def _corrections(session, tenant, movement, cursor):
    return list(
        session.scalars(
            select(CostCorrectionBasis)
            .join(
                MovementCorrection,
                (MovementCorrection.tenant_id == CostCorrectionBasis.tenant_id)
                & (MovementCorrection.id == CostCorrectionBasis.movement_correction_id),
            )
            .join(
                BusinessEvent,
                (BusinessEvent.tenant_id == CostCorrectionBasis.tenant_id)
                & (BusinessEvent.id == CostCorrectionBasis.introduced_event_id),
            )
            .where(
                CostCorrectionBasis.tenant_id == tenant,
                MovementCorrection.original_movement_id == movement,
                BusinessEvent.sequence <= cursor,
            )
        )
    )


def _replacement_ids(session, tenant, bases, cursor):
    if not bases:
        return []
    return list(
        session.scalars(
            select(CostComponentReplacement.id)
            .join(
                BusinessEvent,
                (BusinessEvent.tenant_id == CostComponentReplacement.tenant_id)
                & (BusinessEvent.id == CostComponentReplacement.introduced_event_id),
            )
            .where(
                CostComponentReplacement.tenant_id == tenant,
                CostComponentReplacement.replacement_basis_id.in_(bases),
                BusinessEvent.sequence <= cursor,
            )
        )
    )


def _basis_supported(attribution):
    if (
        attribution.tax_treatment == "unknown"
        or attribution.selected_basis_tax_inclusion == "unknown"
    ):
        return False
    if (
        attribution.basis == "gross"
        or attribution.selected_basis_tax_inclusion == "included"
    ):
        return attribution.tax_treatment in {"nonrecoverable", "not_applicable"}
    return True


def _calculate(session, tenant, basis, attributions, corrections):
    known = ZERO
    currency = None
    categories = set()
    trace = []
    missing = set()
    for attribution in attributions:
        admitted = _row(
            session, CostComponentBasis, tenant, attribution.component_basis_id
        )
        component = _row(session, FinancialComponent, tenant, admitted.component_id)
        parts = list(
            session.scalars(
                select(CostAttributionPart)
                .where(
                    CostAttributionPart.tenant_id == tenant,
                    CostAttributionPart.attribution_revision_id == attribution.id,
                    CostAttributionPart.receipt_basis_id == basis.id,
                )
                .order_by(CostAttributionPart.id)
            )
        )
        part_currencies = set()
        conversions = {}
        for part in parts:
            if part.conversion_basis_revision_id:
                from reality.services.cost_conversions import read_basis

                conversion = read_basis(
                    session, tenant, part.conversion_basis_revision_id, kind="currency"
                )
                if conversion.from_code != component.currency:
                    raise core.InvalidOperation(
                        "Conversion source currency does not match retained evidence."
                    )
                conversions[part.id] = conversion
                part_currencies.add(conversion.to_code)
            else:
                part_currencies.add(component.currency)
        if len(part_currencies) > 1:
            raise core.InvalidOperation("One attribution cannot mix target currencies.")
        part_currency = next(iter(part_currencies), component.currency)
        if currency and currency != part_currency:
            raise core.InvalidOperation(
                "Receipt costs with different currencies require reviewed conversion."
            )
        currency = part_currency
        if not _basis_supported(attribution):
            missing.add("tax_basis_incomplete")
        for part in parts:
            conversion = conversions.get(part.id)
            amount = (
                convert_amount(
                    abs(part.source_share),
                    conversion.numerator,
                    conversion.denominator,
                )
                if conversion
                else abs(part.source_share)
            )
            effect = amount * part.cost_effect
            known += effect
            categories.add(part.category)
            trace.append(
                {
                    "part_id": part.id,
                    "attribution_revision_id": attribution.id,
                    "component_basis_id": admitted.id,
                    "component_id": component.id,
                    "category": part.category,
                    "source_share": _money(part.source_share),
                    "cost_effect": _money(effect),
                    "assignment_kind": part.assignment_kind,
                    "conversion_basis_revision_id": part.conversion_basis_revision_id,
                    "converted_currency": part_currency,
                    "converted_share": _money(amount) if conversion else None,
                }
            )
    if corrections:
        missing.add("receipt_corrected")
    if not attributions:
        missing.add("no_attributed_cost")
    return known, currency, categories, trace, missing


def _verify_manifest(
    session: Session, tenant: str, manifest: CostInputManifest
) -> None:
    if (
        manifest.state != "sealed"
        or manifest.algorithm_version != "receipt-v1"
        or manifest.input_schema_version != 1
    ):
        raise core.InvalidOperation("Unsupported receipt cost manifest.")
    members = {}
    for model, field, key in (
        (CostManifestReceipt, "receipt_basis_id", "receipt"),
        (CostManifestAttribution, "attribution_revision_id", "attribution"),
        (CostManifestComponent, "component_basis_id", "component"),
        (CostManifestCorrection, "correction_basis_id", "correction"),
        (CostManifestReplacement, "replacement_id", "replacement"),
    ):
        members[key] = sorted(
            session.scalars(
                select(getattr(model, field))
                .where(model.tenant_id == tenant, model.manifest_id == manifest.id)
                .limit(LIMIT + 1)
            )
        )
        if len(members[key]) > LIMIT:
            raise core.InvalidOperation(
                "Receipt cost manifest exceeds the supported scope."
            )
    if _hash(members) != manifest.content_hash:
        raise core.InvalidOperation(
            "Retained receipt cost manifest is incomplete or corrupt."
        )


def receipt_cost(
    session: Session,
    tenant_id: str,
    movement_id: str,
    *,
    manifest_id: str | None = None,
) -> dict:
    """Read one receipt at current retained knowledge or an exact sealed review basis."""
    with session.no_autoflush:
        core.get_tenant(session, tenant_id)
        _movement(session, tenant_id, movement_id)
        cursor = None if manifest_id else _sequence(session, tenant_id)
        basis = _receipt(session, tenant_id, movement_id)
        if basis is None:
            if manifest_id:
                raise core.NotFound("Costing scope not found.")
            return {
                "movement_id": movement_id,
                "event_sequence": cursor,
                "known_cost": None,
                "actual_cost": None,
                "unit_cost": None,
                "review_state": "unreviewed",
                "missing_basis": ["not_admitted"],
                "trace": [],
                "manifest_id": None,
            }
        if manifest_id:
            manifest = _row(session, CostInputManifest, tenant_id, manifest_id)
            _verify_manifest(session, tenant_id, manifest)
            if not session.scalar(
                select(CostManifestReceipt.id).where(
                    CostManifestReceipt.tenant_id == tenant_id,
                    CostManifestReceipt.manifest_id == manifest.id,
                    CostManifestReceipt.receipt_basis_id == basis.id,
                )
            ):
                raise core.NotFound("Costing scope not found.")
            cursor = manifest.target_event_sequence
            attributions = list(
                session.scalars(
                    select(CostAttribution)
                    .join(
                        CostManifestAttribution,
                        (CostManifestAttribution.tenant_id == CostAttribution.tenant_id)
                        & (
                            CostManifestAttribution.attribution_revision_id
                            == CostAttribution.id
                        ),
                    )
                    .where(
                        CostAttribution.tenant_id == tenant_id,
                        CostManifestAttribution.manifest_id == manifest.id,
                    )
                )
            )
            corrections = list(
                session.scalars(
                    select(CostCorrectionBasis)
                    .join(
                        CostManifestCorrection,
                        (
                            CostManifestCorrection.tenant_id
                            == CostCorrectionBasis.tenant_id
                        )
                        & (
                            CostManifestCorrection.correction_basis_id
                            == CostCorrectionBasis.id
                        ),
                    )
                    .where(
                        CostCorrectionBasis.tenant_id == tenant_id,
                        CostManifestCorrection.manifest_id == manifest.id,
                    )
                )
            )
            review = session.scalar(
                select(CostScopeReview).where(
                    CostScopeReview.tenant_id == tenant_id,
                    CostScopeReview.manifest_id == manifest.id,
                    CostScopeReview.receipt_basis_id == basis.id,
                )
            )
        else:
            attributions = _attributions(session, tenant_id, basis.id, cursor)
            corrections = _corrections(session, tenant_id, movement_id, cursor)
            review = session.scalar(
                select(CostScopeReview)
                .join(
                    BusinessEvent,
                    (BusinessEvent.tenant_id == CostScopeReview.tenant_id)
                    & (BusinessEvent.id == CostScopeReview.introduced_event_id),
                )
                .where(
                    CostScopeReview.tenant_id == tenant_id,
                    CostScopeReview.receipt_basis_id == basis.id,
                    BusinessEvent.sequence <= cursor,
                )
                .order_by(CostScopeReview.revision.desc())
                .limit(1)
            )
            manifest = (
                _row(session, CostInputManifest, tenant_id, review.manifest_id)
                if review
                else None
            )
        known, currency, categories, trace, missing = _calculate(
            session, tenant_id, basis, attributions, corrections
        )
        review_state = "unreviewed"
        if review:
            review_state = "reviewed_complete_at_cutoff"
            if (
                not manifest_id
                and _sequence(session, tenant_id, inputs_only=True, cutoff=cursor)
                > manifest.target_event_sequence
            ):
                review_state = "stale"
                missing.add("review_stale")
            reviewed = list(
                session.scalars(
                    select(CostReviewCategory).where(
                        CostReviewCategory.tenant_id == tenant_id,
                        CostReviewCategory.review_id == review.id,
                    )
                )
            )
            for category in reviewed:
                if category.disposition == "unresolved" or (
                    category.disposition == "evidenced"
                    and category.category not in categories
                ):
                    missing.add("category:" + category.category)
            if len(reviewed) != len(CATEGORIES):
                missing.add("review_categories_incomplete")
        else:
            missing.add("scope_not_reviewed")
        complete = review is not None and not missing
        if review and missing and review_state != "stale":
            review_state = "incomplete"
        return {
            "movement_id": movement_id,
            "receipt_basis_id": basis.id,
            "event_sequence": cursor,
            "manifest_id": manifest.id if manifest else None,
            "currency": currency,
            "base_quantity": _money(basis.base_quantity),
            "base_unit": basis.base_unit,
            "known_cost": _money(known),
            "actual_cost": _money(known) if complete else None,
            "unit_cost": format(
                (known / basis.base_quantity).quantize(
                    Decimal("0.000001"), rounding=ROUND_HALF_EVEN
                ),
                "f",
            )
            if complete
            else None,
            "review_state": review_state,
            "missing_basis": sorted(missing),
            "trace": trace,
            "persistence": {"business_writes": False, "projection_writes": False},
        }


def _check_change(session, tenant, request):
    if request.expected_event_sequence != _sequence(session, tenant):
        raise core.Conflict("Costing preview is stale; reload the held evidence.")
    allocation = None
    if isinstance(request, Allocate):
        request, allocation = _resolve_allocation(session, tenant, request)
    if isinstance(request, (SellingAssign, SellingAllocate)):
        from reality.services.selling_costs import _check

        return _check(session, tenant, request)
    if isinstance(request, ValuationAssessment):
        from reality.services.carrying_value import _check

        return _check(session, tenant, request)
    if isinstance(request, ConversionBasisReview):
        from reality.services.cost_conversions import _check

        return _check(session, tenant, request)
    if isinstance(request, CommercialMatchReview):
        from reality.services.commercial_matching import _check

        return _check(session, tenant, request)
    if isinstance(request, ContributionBatchReview):
        from reality.services.contribution_reviews import _check_batch

        return _check_batch(session, tenant, request)
    if isinstance(request, ContributionReview):
        from reality.services.contribution_reviews import _check

        return _check(session, tenant, request)
    if isinstance(request, InventoryBatchReview):
        from reality.services.inventory_costing import _check_batch

        return _check_batch(session, tenant, request)
    if isinstance(request, InventoryReview):
        from reality.services.inventory_costing import _check

        return _check(session, tenant, request)
    if isinstance(request, (Assign, Replace)):
        received = cost_evidence(
            session, tenant, request.document_id, request.document_line_id
        )
        if received["evidence_hash"] != request.expected_evidence_hash:
            raise core.Conflict("Costing evidence preview is stale.")
        from reality.db.contribution import CostSellingPart
        from reality.services.selling_costs import _family_used

        component_basis = (
            session.scalar(
                select(CostComponentBasis).where(
                    CostComponentBasis.tenant_id == tenant,
                    CostComponentBasis.component_id == received["component_id"],
                )
            )
            if received["component_id"]
            else None
        )
        checked_basis_ids = [component_basis.id] if component_basis else []
        if isinstance(request, Replace):
            checked_basis_ids.append(request.previous_component_basis_id)
        if any(
            _family_used(session, tenant, identity, CostSellingPart)
            for identity in checked_basis_ids
        ):
            raise core.InvalidOperation(
                "Selling evidence cannot be assigned or replaced as acquisition cost."
            )
        raw = received["amounts"][request.basis]
        if raw is None:
            raise core.InvalidOperation(
                "The selected received amount is missing; it cannot be recomputed."
            )
        tax = request.nonrecoverable_tax_amount
        stated_tax = received["amounts"]["tax"]
        if tax and (
            stated_tax is None
            or abs(tax) > abs(Decimal(stated_tax))
            or (tax > 0) != (Decimal(stated_tax) > 0)
        ):
            raise core.InvalidOperation(
                "Nonrecoverable share exceeds or contradicts received tax."
            )
        if tax and (
            request.selected_basis_tax_inclusion != "excluded"
            or request.tax_treatment not in {"mixed", "nonrecoverable"}
        ):
            raise core.InvalidOperation(
                "Tax cannot be counted twice or assigned as recoverable."
            )
        if (
            request.selected_basis_tax_inclusion == "excluded"
            and request.tax_treatment == "nonrecoverable"
            and (stated_tax is None or tax != Decimal(stated_tax))
        ):
            raise core.InvalidOperation(
                "Nonrecoverable tax requires the complete stated tax share."
            )
        if request.tax_treatment == "mixed" and (
            stated_tax is None or not ZERO < abs(tax) < abs(Decimal(stated_tax))
        ):
            raise core.InvalidOperation(
                "Mixed tax requires an explicit partial received tax share."
            )
        if (
            request.basis == "net"
            and request.selected_basis_tax_inclusion == "included"
        ):
            raise core.InvalidOperation("Received net cannot include input tax.")
        if (
            request.basis == "gross"
            and request.selected_basis_tax_inclusion == "excluded"
        ):
            raise core.InvalidOperation("Received gross cannot exclude its stated tax.")
        if (
            request.tax_treatment == "not_applicable"
            and stated_tax is not None
            and Decimal(stated_tax) != ZERO
        ):
            raise core.InvalidOperation(
                "Stated nonzero tax cannot be declared not applicable."
            )
        try:
            validate_shares(request.parts, Decimal(raw), tax)
        except ValueError as error:
            raise core.InvalidOperation(str(error)) from error
        for part in request.parts:
            conversion = None
            if part.conversion_basis_revision_id:
                from reality.services.cost_conversions import read_basis

                conversion = read_basis(
                    session, tenant, part.conversion_basis_revision_id, kind="currency"
                )
                if conversion.from_code != received["currency"]:
                    raise core.InvalidOperation(
                        "Conversion source currency does not match received evidence."
                    )
            movement = _movement(session, tenant, part.movement_id)
            if session.scalar(
                select(MovementCorrection.id).where(
                    MovementCorrection.tenant_id == tenant,
                    MovementCorrection.original_movement_id == movement.id,
                )
            ):
                raise core.InvalidOperation(
                    "Assign to the replacement receipt, not a corrected original."
                )
            item = _row(session, Item, tenant, movement.item_id)
            if not item.unit:
                raise core.InvalidOperation("An evidenced base unit is required.")
            basis = _receipt(session, tenant, movement.id)
            if basis:
                current = _attributions(
                    session, tenant, basis.id, request.expected_event_sequence
                )
                retained_components = set()
                for attribution in current:
                    if (
                        isinstance(request, Replace)
                        and attribution.component_basis_id
                        == request.previous_component_basis_id
                    ):
                        continue
                    retained_components.add(
                        _row(
                            session,
                            CostComponentBasis,
                            tenant,
                            attribution.component_basis_id,
                        ).component_id
                    )
                # Reassigning a component replaces its prior revision; fresh evidence
                # adds one contributor. Refuse before creating an unreadable receipt.
                prospective = len(retained_components) + (
                    received["component_id"] not in retained_components
                )
                if prospective > LIMIT:
                    raise core.InvalidOperation(
                        "Receipt cost component bound would be exceeded."
                    )
                for a in current:
                    cb = _row(session, CostComponentBasis, tenant, a.component_basis_id)
                    c = _row(session, FinancialComponent, tenant, cb.component_id)
                    target_currency = (
                        conversion.to_code
                        if part.conversion_basis_revision_id
                        else received["currency"]
                    )
                    if c.currency != target_currency:
                        raise core.InvalidOperation(
                            "Receipt currency conversion is not supported by this slice."
                        )
        if received["component_id"]:
            admitted = session.scalar(
                select(CostComponentBasis).where(
                    CostComponentBasis.tenant_id == tenant,
                    CostComponentBasis.component_id == received["component_id"],
                )
            )
            if admitted and session.scalar(
                select(CostComponentReplacement.id).where(
                    CostComponentReplacement.tenant_id == tenant,
                    CostComponentReplacement.previous_basis_id == admitted.id,
                )
            ):
                raise core.InvalidOperation("Replaced evidence cannot be reassigned.")
        if isinstance(request, Replace):
            previous = _row(
                session, CostComponentBasis, tenant, request.previous_component_basis_id
            )
            old_component = _row(
                session, FinancialComponent, tenant, previous.component_id
            )
            if previous.component_id == received["component_id"] or session.scalar(
                select(CostComponentBasis.id).where(
                    CostComponentBasis.tenant_id == tenant,
                    CostComponentBasis.component_id == received["component_id"],
                )
            ):
                raise core.InvalidOperation(
                    "Replacement requires fresh distinct evidence."
                )
            if old_component.currency != received["currency"]:
                raise core.InvalidOperation(
                    "Replacement cannot silently change currency."
                )
            if session.scalar(
                select(CostComponentReplacement.id).where(
                    CostComponentReplacement.tenant_id == tenant,
                    CostComponentReplacement.previous_basis_id == previous.id,
                )
            ):
                raise core.Conflict("Evidence was already replaced.")
        result = {
            "received": received,
            "assigned_effect": _money(
                sum((contribution(p) for p in request.parts), ZERO)
            ),
            "unassigned_basis": _money(
                Decimal(raw)
                - sum(
                    (
                        p.source_share
                        for p in request.parts
                        if p.amount_bucket == "selected_basis"
                    ),
                    ZERO,
                )
            ),
        }
        if allocation is not None:
            result["allocation"] = allocation
        return result
    if isinstance(request, Withdraw):
        basis = _row(session, CostComponentBasis, tenant, request.component_basis_id)
        if _latest(session, tenant, basis.id, request.expected_event_sequence) is None:
            raise core.InvalidOperation("No attribution to withdraw.")
        return {
            "component_basis_id": basis.id,
            "effect": "Withdraw current attribution; retain history",
        }
    result = receipt_cost(session, tenant, request.movement_id)
    if "receipt_basis_id" not in result:
        raise core.InvalidOperation(
            "Admit evidenced receipt costs before reviewing scope."
        )
    present = {row["category"] for row in result["trace"]}
    for category in request.categories:
        if (
            category.disposition in {"confirmed_zero", "not_applicable"}
            and category.category in present
        ):
            raise core.InvalidOperation(
                "A category with attributed costs cannot be declared zero/not applicable."
            )
    return {
        "receipt": result,
        "categories": [c.model_dump() for c in request.categories],
    }


def preview_cost_change(
    session: Session,
    tenant_id: str,
    arguments: dict,
    *,
    principal: Principal | None = None,
) -> dict:
    """Validate the exact owner's decision without creating financial records."""
    with session.no_autoflush:
        _owner(session, tenant_id, principal)
        request = _request(arguments)
        return {
            "request": request.model_dump(mode="json"),
            "review": _check_change(session, tenant_id, request),
            "requires_human_confirmation": True,
        }


def _new(session, model, tenant, **values):
    row = model(id=uid("cst"), tenant_id=tenant, **values)
    session.add(row)
    session.flush()
    return row


def _admit_receipt(session, tenant, movement_id, event):
    basis = _receipt(session, tenant, movement_id)
    if basis:
        return basis
    movement = _movement(session, tenant, movement_id)
    item = _row(session, Item, tenant, movement.item_id)
    return _new(
        session,
        CostReceiptBasis,
        tenant,
        movement_id=movement.id,
        introduced_event_id=event.id,
        base_quantity=movement.quantity,
        base_unit=item.unit,
        input_schema_version=1,
    )


def _admit_component(session, tenant, request, received, event):
    component = components._component(
        session, tenant, request.document_id, request.document_line_id
    )
    if component is None:
        component = _new(
            session,
            FinancialComponent,
            tenant,
            document_id=None if request.document_line_id else request.document_id,
            document_line_id=request.document_line_id,
            currency=received["currency"],
            **{
                "stated_" + key: Decimal(value) if value is not None else None
                for key, value in received["amounts"].items()
            },
        )
    basis = session.scalar(
        select(CostComponentBasis).where(
            CostComponentBasis.tenant_id == tenant,
            CostComponentBasis.component_id == component.id,
        )
    )
    if basis:
        return basis
    # Source evidence may have been admitted manually through the normal document
    # service; absence of an interpretation outcome is not an invented outcome.
    outcome = session.scalar(
        select(InterpretationRecordReference.outcome_id)
        .where(
            InterpretationRecordReference.tenant_id == tenant,
            InterpretationRecordReference.record_type
            == ("document_line" if request.document_line_id else "document"),
            InterpretationRecordReference.record_id
            == (request.document_line_id or request.document_id),
        )
        .limit(1)
    )
    return _new(
        session,
        CostComponentBasis,
        tenant,
        component_id=component.id,
        introduced_event_id=event.id,
        evidence_fingerprint=received["evidence_hash"],
        input_schema_version=1,
        interpretation_outcome_id=outcome,
    )


def _withdraw(session, tenant, basis_id, event, action, reason):
    previous = _latest(session, tenant, basis_id, event.sequence)
    return _new(
        session,
        CostAttribution,
        tenant,
        component_basis_id=basis_id,
        revision=previous.revision + 1,
        supersedes_id=previous.id,
        introduced_event_id=event.id,
        action_id=action,
        effective_at=now(),
        reason=reason,
        state="withdrawn",
        basis=previous.basis,
        tax_treatment=previous.tax_treatment,
        selected_basis_tax_inclusion=previous.selected_basis_tax_inclusion,
        nonrecoverable_tax_amount=previous.nonrecoverable_tax_amount,
    )


def _seal(session, tenant, basis, cursor):
    attributions = _attributions(session, tenant, basis.id, cursor)
    corrections = _corrections(session, tenant, basis.movement_id, cursor)
    components_set = sorted({r.component_basis_id for r in attributions})
    replacements = _replacement_ids(session, tenant, components_set, cursor)
    members = {
        "receipt": [basis.id],
        "attribution": sorted(r.id for r in attributions),
        "component": components_set,
        "correction": sorted(r.id for r in corrections),
        "replacement": sorted(replacements),
    }
    instant = now()
    manifest = _new(
        session,
        CostInputManifest,
        tenant,
        target_event_sequence=cursor,
        effective_at=instant,
        knowledge_at=instant,
        sealed_at=instant,
        input_schema_version=1,
        algorithm_version="receipt-v1",
        state="sealed",
        content_hash=_hash(members),
    )
    for model, field, key in (
        (CostManifestReceipt, "receipt_basis_id", "receipt"),
        (CostManifestAttribution, "attribution_revision_id", "attribution"),
        (CostManifestComponent, "component_basis_id", "component"),
        (CostManifestCorrection, "correction_basis_id", "correction"),
        (CostManifestReplacement, "replacement_id", "replacement"),
    ):
        for identity in members[key]:
            _new(session, model, tenant, manifest_id=manifest.id, **{field: identity})
    return manifest


def _finish(
    session: Session, action: ChangeProposal, actor_id: str, result: dict
) -> dict:
    action.status = "executed"
    action.decided_at = now()
    action.decided_by_user_id = actor_id
    action.output = json.dumps(result, sort_keys=True, default=str)
    session.flush()
    return result


def execute_cost_change(
    session: Session,
    tenant_id: str,
    *,
    arguments: dict,
    action_id: str,
    actor_id: str | None,
    confirmed: bool = False,
) -> dict:
    """Execute one bound, explicitly confirmed owner decision in the caller transaction."""
    if not confirmed:
        raise core.InvalidOperation(
            "Explicit confirmation is required for cost decisions."
        )
    lock_delivery_state(session, tenant_id)
    _owner(session, tenant_id, Principal(actor_id) if actor_id else None, lock=True)
    action = _row(session, ChangeProposal, tenant_id, action_id)
    request = _request(arguments)
    if action.type != "tool:cost.change" or _request(
        json.loads(action.input)
    ).model_dump(mode="json") != request.model_dump(mode="json"):
        raise core.InvalidOperation("Cost decision is not bound to this proposal.")
    if action.status == "executed":
        return json.loads(action.output)
    if action.status != "proposed":
        raise core.InvalidOperation("Cost proposal is not available for execution.")
    core._require_business_mutation(session, tenant_id, "execute_cost_change")
    with session.begin_nested():
        review = _check_change(session, tenant_id, request)
        if isinstance(
            request,
            (
                Review,
                InventoryReview,
                InventoryBatchReview,
                ContributionReview,
                ContributionBatchReview,
                CommercialMatchReview,
                ValuationAssessment,
                ConversionBasisReview,
            ),
        ):
            event = emit_business_event(
                session,
                tenant_id,
                "cost.reviewed",
                "action",
                action.id,
                {"operation": request.operation},
                action_id=action.id,
            )
        else:
            event = emit_business_event(
                session,
                tenant_id,
                "cost.attributed",
                "action",
                action.id,
                {"operation": request.operation},
                action_id=action.id,
            )
        session.flush()
        if isinstance(request, (SellingAssign, SellingAllocate)):
            from reality.services.selling_costs import _execute

            result = _execute(session, tenant_id, request, review, event, action)
            return _finish(session, action, actor_id, result)
        if isinstance(request, ValuationAssessment):
            from reality.services.carrying_value import _execute

            result = _execute(session, tenant_id, request, review, event, action)
            return _finish(session, action, actor_id, result)
        if isinstance(request, ConversionBasisReview):
            from reality.services.cost_conversions import _execute

            result = _execute(session, tenant_id, request, review, event, action)
            return _finish(session, action, actor_id, result)
        if isinstance(request, CommercialMatchReview):
            from reality.services.commercial_matching import _execute

            result = _execute(session, tenant_id, request, review, event, action)
            return _finish(session, action, actor_id, result)
        if isinstance(request, ContributionBatchReview):
            from reality.services.contribution_reviews import _execute_batch

            result = _execute_batch(session, tenant_id, request, review, event, action)
            return _finish(session, action, actor_id, result)
        if isinstance(request, ContributionReview):
            from reality.services.contribution_reviews import _execute

            result = _execute(session, tenant_id, request, review, event, action)
            return _finish(session, action, actor_id, result)
        if isinstance(request, InventoryBatchReview):
            from reality.services.inventory_costing import _execute_batch

            result = _execute_batch(session, tenant_id, request, review, event, action)
            return _finish(session, action, actor_id, result)
        if isinstance(request, InventoryReview):
            from reality.services.inventory_costing import _execute

            result = _execute(session, tenant_id, request, review, event, action)
            return _finish(session, action, actor_id, result)
        if isinstance(request, Withdraw):
            row = _withdraw(
                session,
                tenant_id,
                request.component_basis_id,
                event,
                action.id,
                request.reason,
            )
            return _finish(
                session,
                action,
                actor_id,
                {"attribution_revision_id": row.id, "state": "withdrawn"},
            )
        if isinstance(request, (Assign, Replace, Allocate)):
            persisted_request = (
                _resolve_allocation(session, tenant_id, request)[0]
                if isinstance(request, Allocate)
                else request
            )
            admitted = _admit_component(
                session, tenant_id, persisted_request, review["received"], event
            )
            if isinstance(request, Replace):
                _withdraw(
                    session,
                    tenant_id,
                    request.previous_component_basis_id,
                    event,
                    action.id,
                    request.reason,
                )
                _new(
                    session,
                    CostComponentReplacement,
                    tenant_id,
                    previous_basis_id=request.previous_component_basis_id,
                    replacement_basis_id=admitted.id,
                    introduced_event_id=event.id,
                    action_id=action.id,
                    reason=request.reason,
                )
            previous = _latest(session, tenant_id, admitted.id, event.sequence)
            row = _new(
                session,
                CostAttribution,
                tenant_id,
                component_basis_id=admitted.id,
                revision=previous.revision + 1 if previous else 1,
                supersedes_id=previous.id if previous else None,
                introduced_event_id=event.id,
                action_id=action.id,
                effective_at=now(),
                reason=request.reason,
                state="assigned",
                basis=request.basis,
                tax_treatment=request.tax_treatment,
                selected_basis_tax_inclusion=request.selected_basis_tax_inclusion,
                nonrecoverable_tax_amount=request.nonrecoverable_tax_amount,
            )
            for part in persisted_request.parts:
                basis = _admit_receipt(session, tenant_id, part.movement_id, event)
                _new(
                    session,
                    CostAttributionPart,
                    tenant_id,
                    attribution_revision_id=row.id,
                    receipt_basis_id=basis.id,
                    **part.model_dump(exclude={"movement_id"}),
                )
            return _finish(
                session,
                action,
                actor_id,
                {
                    "component_basis_id": admitted.id,
                    "attribution_revision_id": row.id,
                    "revision": row.revision,
                    **{k: review[k] for k in ("assigned_effect", "unassigned_basis")},
                },
            )
        basis = _receipt(session, tenant_id, request.movement_id)
        manifest = _seal(session, tenant_id, basis, request.expected_event_sequence)
        previous = session.scalar(
            select(CostScopeReview)
            .where(
                CostScopeReview.tenant_id == tenant_id,
                CostScopeReview.receipt_basis_id == basis.id,
            )
            .order_by(CostScopeReview.revision.desc())
            .limit(1)
        )
        row = _new(
            session,
            CostScopeReview,
            tenant_id,
            receipt_basis_id=basis.id,
            revision=previous.revision + 1 if previous else 1,
            supersedes_id=previous.id if previous else None,
            manifest_id=manifest.id,
            introduced_event_id=event.id,
            action_id=action.id,
            reason=request.reason,
        )
        for category in request.categories:
            _new(
                session,
                CostReviewCategory,
                tenant_id,
                review_id=row.id,
                **category.model_dump(),
            )
        return _finish(
            session,
            action,
            actor_id,
            receipt_cost(session, tenant_id, request.movement_id),
        )


def _protect_document(session, tenant, document_id):
    from reality.db.contribution import CostRevenueMatchBasis

    lines = select(DocumentLine.id).where(
        DocumentLine.tenant_id == tenant, DocumentLine.document_id == document_id
    )
    if session.scalar(
        select(CostRevenueMatchBasis.id)
        .where(
            CostRevenueMatchBasis.tenant_id == tenant,
            or_(
                CostRevenueMatchBasis.document_line_id.in_(lines),
                CostRevenueMatchBasis.order_line_id.in_(lines),
            ),
        )
        .limit(1)
    ):
        raise core.InvalidOperation(
            "Admitted contribution evidence is immutable; replacement and rematching require a supported review workflow."
        )
    statement = (
        select(CostComponentBasis.id)
        .join(
            FinancialComponent,
            (FinancialComponent.tenant_id == CostComponentBasis.tenant_id)
            & (FinancialComponent.id == CostComponentBasis.component_id),
        )
        .where(
            CostComponentBasis.tenant_id == tenant,
            or_(
                FinancialComponent.document_id == document_id,
                FinancialComponent.document_line_id.in_(
                    select(DocumentLine.id).where(
                        DocumentLine.tenant_id == tenant,
                        DocumentLine.document_id == document_id,
                    )
                ),
            ),
        )
        .limit(1)
    )
    if session.scalar(statement):
        raise core.InvalidOperation(
            "Admitted cost evidence is immutable; create replacement evidence and confirm cost.change replace."
        )


def _capture_correction(session, tenant, correction, event):
    if _receipt(session, tenant, correction.original_movement_id):
        _new(
            session,
            CostCorrectionBasis,
            tenant,
            movement_correction_id=correction.id,
            introduced_event_id=event.id,
            input_schema_version=1,
        )


def inventory_cost(
    session: Session,
    tenant_id: str,
    item_id: str,
    *,
    review_id: str | None = None,
    assessment_revision_id: str | None = None,
) -> dict:
    """Read a confirmed bounded inventory basis without writing or live history replay."""
    from reality.services.inventory_costing import _read

    return _read(
        session,
        tenant_id,
        item_id,
        review_id=review_id,
        assessment_revision_id=assessment_revision_id,
    )


def contribution_preview(
    session: Session, tenant_id: str, document_line_id: str
) -> dict:
    """Read a current, unconfirmed revenue/consumption candidate without writes."""
    from reality.services.contribution import _read

    return _read(session, tenant_id, document_line_id)


def reviewed_contribution(
    session: Session,
    tenant_id: str,
    document_line_id: str,
    *,
    review_id: str | None = None,
) -> dict:
    """Derive confirmed DB1 from an exact retained commercial and inventory review."""
    from reality.services.contribution_reviews import _read

    return _read(session, tenant_id, document_line_id, review_id=review_id)


def commercial_match(
    session: Session,
    tenant_id: str,
    document_line_id: str,
    *,
    match_revision_id: str | None = None,
) -> dict:
    """Read a retained partial commercial match and derive its current observation."""
    from reality.services.commercial_matching import _read

    return _read(
        session,
        tenant_id,
        document_line_id,
        match_revision_id=match_revision_id,
    )


def cost_record(
    session: Session,
    tenant_id: str,
    kind: str,
    record_id: str,
    *,
    page: int = 1,
    language: str = "en",
) -> dict:
    """Inspect a retained cost record and bounded exact membership without valuation writes."""
    from reality.services.cost_records import _read

    return _read(session, tenant_id, kind, record_id, page=page, language=language)


def cost_query(
    session: Session,
    tenant_id: str,
    *,
    kind: str,
    scope_id: str,
    review_id: str | None = None,
    effective_at: datetime | str | None = None,
    knowledge_at: datetime | str | None = None,
    policy_revision_id: str | None = None,
) -> dict:
    """Resolve a retained cost answer and its exact constrained query context."""
    from reality.services.cost_query import _read

    return _read(
        session,
        tenant_id,
        {
            "kind": kind,
            "scope_id": scope_id,
            "review_id": review_id,
            "effective_at": effective_at,
            "knowledge_at": knowledge_at,
            "policy_revision_id": policy_revision_id,
        },
    )


def build_inventory_generation(
    session: Session,
    tenant_id: str,
    review_id: str,
    *,
    deadline: datetime | None = None,
) -> dict:
    """Maintenance-only disposable cache build; never approve financial inputs."""
    from reality.services.inventory_generations import _build

    return _build(session, tenant_id, review_id, deadline=deadline)


def inventory_cost_snapshot(
    session: Session,
    tenant_id: str,
    item_id: str,
    *,
    review_id: str | None = None,
    generation_id: str | None = None,
    allow_previous: bool = False,
) -> dict:
    """Read one pinned stored inventory observation without recalculation or jobs."""
    from reality.services.inventory_generations import _read

    return _read(
        session,
        tenant_id,
        item_id,
        review_id=review_id,
        generation_id=generation_id,
        allow_previous=allow_previous,
    )


def inventory_cost_snapshots(
    session: Session,
    tenant_id: str,
    generation_ids: list[str] | tuple[str, ...],
) -> dict:
    """Read a bounded historical selection without inventing a common cost basis."""
    from reality.services.inventory_generations import _read_selection

    return _read_selection(session, tenant_id, generation_ids)


def build_inventory_batch_generation(
    session: Session,
    tenant_id: str,
    action_id: str,
    *,
    deadline: datetime | None = None,
) -> dict:
    """Atomically build all retained members of one confirmed inventory action."""
    from reality.services.inventory_batch_generations import _build

    return _build(session, tenant_id, action_id, deadline=deadline)


def inventory_batch_snapshot(
    session: Session,
    tenant_id: str,
    action_id: str,
    *,
    mode: str = "historical",
    allow_previous: bool = False,
) -> dict:
    """Read a complete selected inventory scope, preserving freshness and units."""
    from reality.services.inventory_batch_generations import _read

    return _read(
        session, tenant_id, action_id, mode=mode, allow_previous=allow_previous
    )


def build_contribution_generation(
    session: Session,
    tenant_id: str,
    action_id: str,
    *,
    deadline: datetime | None = None,
) -> dict:
    """Rebuild the complete historical scope of one confirmed joint contribution."""
    from reality.services.contribution_generations import _build

    return _build(session, tenant_id, action_id, deadline=deadline)


def contribution_snapshot(
    session: Session, tenant_id: str, action_id: str, *, mode: str = "historical"
) -> dict:
    """Read a protected selected scope, withholding stale current observations."""
    from reality.services.contribution_generations import _read

    return _read(session, tenant_id, action_id, mode=mode)


def capture_company_cost_census(
    session: Session,
    tenant_id: str,
    effective_at: datetime,
    *,
    max_records: int = 100_000,
) -> dict:
    """Discover bounded current company inputs, without valuation or publication."""
    from reality.services.cost_census import _capture

    return _capture(session, tenant_id, effective_at, max_records=max_records)


def retain_company_cost_census(
    session: Session,
    tenant_id: str,
    effective_at: datetime,
    *,
    request_id: str,
    max_records: int = 100_000,
) -> dict:
    """Retain current discovery atomically; caller owns the clean transaction."""
    from reality.services.cost_census_storage import _retain

    return _retain(
        session, tenant_id, effective_at, request_id=request_id, max_records=max_records
    )


def company_cost_census(session: Session, tenant_id: str, census_id: str) -> dict:
    """Inspect retained discovery metadata without assessing financial completeness."""
    from reality.services.cost_census_storage import _get

    return _get(session, tenant_id, census_id)


def verify_company_cost_census(
    session: Session, tenant_id: str, census_id: str
) -> dict:
    """Builder-only full retained membership verification; never valuation."""
    from reality.services.cost_census_storage import _verify

    return _verify(session, tenant_id, census_id)


def company_cost_census_members(
    session: Session,
    tenant_id: str,
    census_id: str,
    *,
    family: str,
    limit: int = 100,
    cursor: str | None = None,
) -> dict:
    """Inspect a bounded page of frozen typed members."""
    from reality.services.cost_census_storage import _members

    return _members(
        session, tenant_id, census_id, family=family, limit=limit, cursor=cursor
    )


def resolve_company_cost_census(
    session: Session, tenant_id: str, census_id: str, *, max_subjects: int = 10
) -> dict:
    """Resolve bounded captured subjects to retained reviews without approving inputs."""
    from reality.services.cost_census_resolution import _resolve

    return _resolve(session, tenant_id, census_id, max_subjects=max_subjects)


def admit_company_cost_manifest(
    session: Session,
    tenant_id: str,
    census_id: str,
    *,
    principal: Principal,
    max_subjects: int = 10,
) -> dict:
    """Retain owner-authorized exact financial inputs for one current census."""
    from reality.services.company_generations import _admit

    return _admit(
        session,
        tenant_id,
        census_id,
        principal=principal,
        max_subjects=max_subjects,
    )


def build_company_cost_generation(
    session: Session,
    tenant_id: str,
    manifest_id: str,
    *,
    start: int = 0,
    limit: int = 100,
    deadline: datetime | None = None,
) -> dict:
    """Build a deterministic range of one retained company manifest."""
    from reality.services.company_generations import _build

    return _build(
        session,
        tenant_id,
        manifest_id,
        start=start,
        limit=limit,
        deadline=deadline,
    )


def publish_company_cost_generation(
    session: Session,
    tenant_id: str,
    generation_id: str,
    *,
    previous_generation_id: str | None,
) -> dict:
    """CAS-publish one complete company generation."""
    from reality.services.company_generations import _publish

    return _publish(session, tenant_id, generation_id, previous_generation_id)


def company_cost_generation_report(
    session: Session,
    tenant_id: str,
    generation_id: str,
    *,
    page_size: int = 50,
    inventory_cursor: str | None = None,
    contribution_cursor: str | None = None,
) -> dict:
    """Read fixed-generation company pages and totals without scheduling work."""
    from reality.services.company_generations import _report

    return _report(
        session,
        tenant_id,
        generation_id,
        page_size=page_size,
        inventory_cursor=inventory_cursor,
        contribution_cursor=contribution_cursor,
    )


def retain_captured_cost_basis(
    session: Session,
    tenant_id: str,
    census_id: str,
    *,
    request_id: str,
    max_subjects: int = 10,
) -> dict:
    """Retain a verified captured review selection; caller owns commit/rollback."""
    from reality.services.cost_captured_basis import _retain

    return _retain(
        session, tenant_id, census_id, request_id=request_id, max_subjects=max_subjects
    )


def captured_cost_basis(session: Session, tenant_id: str, basis_id: str) -> dict:
    """Read verified retained membership without calculating financial amounts."""
    from reality.services.cost_captured_basis import _read

    return _read(session, tenant_id, basis_id)


def replay_captured_cost_basis(session: Session, tenant_id: str, basis_id: str) -> dict:
    """Reconstruct canonical financial observations from pinned review identities."""
    from reality.services.cost_captured_basis import _replay

    return _replay(session, tenant_id, basis_id)


def captured_cost_summary(session: Session, tenant_id: str, basis_id: str) -> dict:
    """Known subtotals of a verified retained basis; never final company totals."""
    from reality.services.cost_captured_summary import _summary

    return _summary(session, tenant_id, basis_id)


def build_captured_cost_generation(
    session: Session, tenant_id: str, basis_id: str
) -> dict:
    """Build a disposable report from a verified retained selection; caller commits."""
    from reality.services.captured_report import _build

    return _build(session, tenant_id, basis_id)


def publish_captured_cost_generation(
    session: Session,
    tenant_id: str,
    generation_id: str,
    *,
    expected_previous_id: str | None,
) -> dict:
    """Atomically select a sealed captured report, without financial approval."""
    from reality.services.captured_report import _publish

    return _publish(session, tenant_id, generation_id, expected_previous_id)


def captured_cost_report(
    session: Session,
    tenant_id: str,
    generation_id: str,
    *,
    page_size: int = 50,
    inventory_cursor: str | None = None,
    contribution_cursor: str | None = None,
) -> dict:
    """Read fixed cached rows and known subtotals without financial input replay."""
    from reality.services.captured_report import _report

    return _report(
        session,
        tenant_id,
        generation_id,
        page_size=page_size,
        inventory_cursor=inventory_cursor,
        contribution_cursor=contribution_cursor,
    )


def discard_captured_cost_generation(
    session: Session, tenant_id: str, generation_id: str
) -> None:
    """Discard only an unpublished cache; retain its input selection and evidence."""
    from reality.services.captured_report import _discard

    _discard(session, tenant_id, generation_id)
