"""Private bounded inventory implementation behind the shared costing services."""

import json
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import cast, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Item,
    Movement,
    MovementCorrection,
    Party,
    SourceRecord,
    now,
)
from reality.db.costing import CostReceiptBasis
from reality.db.inventory_costing import (
    CostInventoryMember,
    CostInventoryOwnershipPart,
    CostInventoryReview,
    CostMovementBasis,
    CostOpeningBasis,
    CostOwnershipRevision,
    CostPolicyRevision,
)
from reality.domain.costing import InventoryBatchReview, InventoryReview
from reality.domain.inventory_costing import (
    ALGORITHM_VERSION,
    InventoryEvent,
    InventoryRefusal,
    ReturnPart,
    Selection,
    calculate_inventory,
)
from reality.services import core
from reality.services.costing import _hash, _money, _new, _row, _sequence, receipt_cost

MAX_MOVEMENTS = 100
MAX_RECEIPTS = 20
KINDS = {
    "receipt": "receipt",
    "shipment": "issue",
    "transfer": "transfer",
    "return": "customer_return",
    "supplier_return": "supplier_return",
    "adjustment": "loss",
    "opening_stock": "opening",
}
KERNEL_KINDS = {**KINDS, "opening_stock": "receipt"}


def _relevant_event_sequence(
    session: Session, tenant: str, item_id: str, reviewed_sequence: int
) -> int:
    """Latest physical event for one item, never an unrelated company cursor.

    A retained review already captures every event up to ``reviewed_sequence``. A later
    payment, dunning notice or movement of another item cannot invalidate its physical
    basis. Later movement/correction events for this item still make it stale.
    """
    payload_item_id = cast(BusinessEvent.payload, JSONB)["item_id"].astext
    latest = session.scalar(
        select(func.max(BusinessEvent.sequence)).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.sequence > reviewed_sequence,
            or_(
                (
                    (BusinessEvent.event_type == "item.updated")
                    & (BusinessEvent.subject_type == "item")
                    & (BusinessEvent.subject_id == item_id)
                ),
                (
                    BusinessEvent.event_type.in_(
                        ("movement.recorded", "movement.corrected")
                    )
                    & (BusinessEvent.subject_type == "movement")
                    & (payload_item_id == item_id)
                ),
            ),
        )
    )
    return max(reviewed_sequence, latest or 0)


def _check(
    session: Session,
    tenant: str,
    request: InventoryReview,
    *,
    movement_limit: int | None = None,
    receipt_limit: int | None = None,
) -> dict:
    movement_limit = MAX_MOVEMENTS if movement_limit is None else movement_limit
    receipt_limit = MAX_RECEIPTS if receipt_limit is None else receipt_limit
    if session.connection().get_isolation_level() != "READ COMMITTED":
        raise core.InvalidOperation(
            "Inventory admission requires READ COMMITTED input capture."
        )
    item = _row(session, Item, tenant, request.item_id)
    _row(session, Party, tenant, request.owner_party_id)
    if request.base_unit != item.unit or request.effective_at > now():
        raise core.InvalidOperation("Unsupported inventory base unit or future cutoff.")
    movements = list(
        session.scalars(
            select(Movement)
            .where(
                Movement.tenant_id == tenant,
                Movement.item_id == item.id,
                Movement.occurred_at <= request.effective_at,
            )
            .order_by(Movement.occurred_at, Movement.id)
            .limit(movement_limit + 1)
        )
    )
    if len(movements) > movement_limit:
        raise core.InvalidOperation("Inventory movement bound exceeded.")
    ids = [m.id for m in movements]
    corrections = list(
        session.scalars(
            select(MovementCorrection).where(
                MovementCorrection.tenant_id == tenant,
                or_(
                    MovementCorrection.original_movement_id.in_(ids),
                    MovementCorrection.compensating_movement_id.in_(ids),
                    MovementCorrection.replacement_movement_id.in_(ids),
                ),
            )
        )
    )
    corrected_subjects = set(
        session.scalars(
            select(BusinessEvent.subject_id).where(
                BusinessEvent.tenant_id == tenant,
                BusinessEvent.event_type == "movement.corrected",
                BusinessEvent.subject_type == "movement",
                BusinessEvent.subject_id.in_(ids),
                BusinessEvent.sequence <= request.expected_event_sequence,
            )
        )
    )
    if corrected_subjects - {row.original_movement_id for row in corrections}:
        raise core.InvalidOperation("Inventory correction chain is incomplete.")
    correction_events = {}
    correction_inputs = {}
    excluded = set()
    for correction in corrections:
        original = _row(session, Movement, tenant, correction.original_movement_id)
        compensation = _row(
            session, Movement, tenant, correction.compensating_movement_id
        )
        replacement = (
            _row(session, Movement, tenant, correction.replacement_movement_id)
            if correction.replacement_movement_id
            else None
        )
        if (
            original is None
            or compensation is None
            or original.item_id != item.id
            or compensation.item_id != item.id
            or compensation.type != "correction"
            or compensation.quantity != original.quantity
            or compensation.from_location_id != original.to_location_id
            or compensation.to_location_id != original.from_location_id
            or (replacement is not None and replacement.item_id != item.id)
        ):
            raise core.InvalidOperation("Inventory correction chain is incomplete.")
        events = list(
            session.scalars(
                select(BusinessEvent).where(
                    BusinessEvent.tenant_id == tenant,
                    BusinessEvent.event_type == "movement.corrected",
                    BusinessEvent.subject_type == "movement",
                    BusinessEvent.subject_id == original.id,
                    BusinessEvent.sequence <= request.expected_event_sequence,
                )
            )
        )
        if len(events) != 1:
            raise core.InvalidOperation(
                "Inventory correction requires one exact event."
            )
        excluded.update((original.id, compensation.id))
        if replacement is not None:
            correction_events[replacement.id] = events[0]
            correction_inputs[replacement.id] = {
                "correction_id": correction.id,
                "original_movement_id": original.id,
                "compensating_movement_id": compensation.id,
                "replacement_movement_id": replacement.id,
                "reason": correction.reason,
            }
    movements = [movement for movement in movements if movement.id not in excluded]
    if not movements or any(m.occurred_at < request.history_start for m in movements):
        raise core.InvalidOperation(
            "Inventory history does not support the declared empty opening."
        )
    if any(m.type not in KINDS or m.quantity <= 0 for m in movements):
        raise core.InvalidOperation(
            "Inventory history contains unsupported movement kinds."
        )
    ownership_parts: list[dict] = []
    owned_quantity = {movement.id: movement.quantity for movement in movements}
    if request.ownership_parts:
        movement_by_id = {movement.id: movement for movement in movements}
        grouped: dict[str, list] = {}
        for part in request.ownership_parts:
            if part.movement_id not in movement_by_id:
                raise core.InvalidOperation(
                    "Inventory ownership references an unavailable movement."
                )
            _row(session, Party, tenant, part.owner_party_id)
            _row(session, SourceRecord, tenant, part.evidence_source_record_id)
            grouped.setdefault(part.movement_id, []).append(part)
        if set(grouped) != set(movement_by_id):
            raise core.InvalidOperation(
                "Inventory ownership must partition every effective movement."
            )
        for movement in movements:
            parts = grouped[movement.id]
            if sum((part.quantity for part in parts), Decimal(0)) != movement.quantity:
                raise core.InvalidOperation(
                    "Inventory ownership portions must conserve movement quantity."
                )
            owned_quantity[movement.id] = sum(
                (
                    part.quantity
                    for part in parts
                    if part.owner_party_id == request.owner_party_id
                ),
                Decimal(0),
            )
            ownership_parts.extend(
                {
                    "movement_id": movement.id,
                    "owner_party_id": part.owner_party_id,
                    "evidence_source_record_id": part.evidence_source_record_id,
                    "quantity": str(part.quantity),
                }
                for part in parts
            )
    owned_movements = [m for m in movements if owned_quantity[m.id] > 0]
    receipt_ids = {m.id for m in owned_movements if m.type == "receipt"}
    if len(receipt_ids) > receipt_limit:
        raise core.InvalidOperation("Inventory receipt bound exceeded.")
    reviewed_receipt_ids = {row.movement_id for row in request.receipts}
    if receipt_ids != reviewed_receipt_ids:
        missing = sorted(receipt_ids - reviewed_receipt_ids)
        unexpected = sorted(reviewed_receipt_ids - receipt_ids)
        raise core.InvalidOperation(
            "Every receipt requires exact cost and ownership evidence; "
            f"missing movement IDs: {missing}; unexpected movement IDs: {unexpected}."
        )
    opening_ids = {m.id for m in owned_movements if m.type == "opening_stock"}
    if opening_ids != {row.movement_id for row in request.openings}:
        raise core.InvalidOperation(
            "Every opening stock requires exact cost and ownership evidence."
        )
    if {m.id for m in owned_movements if m.type == "shipment"} != set(
        request.economic_issue_ids
    ):
        raise core.InvalidOperation(
            "Explicit economic consumption must cover every shipment exactly."
        )
    expected = {
        "return": set(request.customer_return_ids),
        "supplier_return": set(request.supplier_return_ids),
        "adjustment": set(request.loss_movement_ids),
    }
    for movement_type, classified_ids in expected.items():
        if {m.id for m in owned_movements if m.type == movement_type} != classified_ids:
            raise core.InvalidOperation(
                f"Inventory history contains unsupported movement classification: every {movement_type} must be explicit."
            )
    movement_by_id = {movement.id: movement for movement in movements}
    resolved_quantities: dict[str, Decimal] = {}
    for movement in movements:
        if not movement.resolves_movement_id:
            continue
        arrived = movement_by_id.get(movement.resolves_movement_id)
        if (
            movement.type not in {"transfer", "adjustment", "supplier_return"}
            or arrived is None
            or arrived.type != "return"
            or arrived.id not in request.customer_return_ids
        ):
            raise core.InvalidOperation(
                "Inventory settlement must resolve one reviewed customer return."
            )
        resolved_quantities[arrived.id] = (
            resolved_quantities.get(arrived.id, Decimal(0)) + movement.quantity
        )
    if any(
        quantity > movement_by_id[return_id].quantity
        for return_id, quantity in resolved_quantities.items()
    ):
        raise core.InvalidOperation(
            "Inventory settlement exceeds its reviewed customer return."
        )
    received = {}
    for chosen in request.receipts:
        _row(session, SourceRecord, tenant, chosen.ownership_source_record_id)
        current = receipt_cost(session, tenant, chosen.movement_id)
        frozen = receipt_cost(
            session, tenant, chosen.movement_id, manifest_id=chosen.manifest_id
        )
        if (
            current["manifest_id"] != chosen.manifest_id
            or frozen["actual_cost"] is None
            or set(current["missing_basis"]) - {"review_stale"}
            or {p["attribution_revision_id"] for p in current["trace"]}
            != {p["attribution_revision_id"] for p in frozen["trace"]}
        ):
            raise core.InvalidOperation(
                "A new complete receipt review is required before inventory confirmation."
            )
        if (
            frozen["currency"] != request.currency
            or frozen["base_unit"] != request.base_unit
        ):
            raise core.InvalidOperation(
                "Inventory receipt currency/base unit is incompatible."
            )
        received[chosen.movement_id] = {
            "receipt_basis_id": frozen["receipt_basis_id"],
            "manifest_id": chosen.manifest_id,
            "ownership_source_record_id": chosen.ownership_source_record_id,
            "cost": frozen["actual_cost"],
            "quantity": frozen["base_quantity"],
        }
    openings = {}
    for chosen in request.openings:
        _row(session, SourceRecord, tenant, chosen.evidence_source_record_id)
        openings[chosen.movement_id] = {
            "evidence_source_record_id": chosen.evidence_source_record_id,
            "cost": str(chosen.acquisition_cost),
        }
    inputs = []
    selections = {}
    for selected in request.specific_selections:
        selections.setdefault(selected.movement_id, []).append(
            {
                "entry_movement_id": selected.entry_movement_id,
                "receipt_movement_id": selected.receipt_movement_id,
                "quantity": str(selected.quantity),
            }
        )
    return_parts = {}
    for part in request.return_parts:
        return_parts.setdefault(part.movement_id, []).append(
            {
                "issue_movement_id": part.issue_movement_id,
                "entry_movement_id": part.entry_movement_id,
                "receipt_movement_id": part.receipt_movement_id,
                "quantity": _money(part.quantity),
            }
        )
    for movement in movements:
        retained_event = correction_events.get(movement.id)
        events = (
            [retained_event]
            if retained_event is not None
            else list(
                session.scalars(
                    select(BusinessEvent)
                    .where(
                        BusinessEvent.tenant_id == tenant,
                        BusinessEvent.event_type == "movement.recorded",
                        BusinessEvent.subject_type == "movement",
                        BusinessEvent.subject_id == movement.id,
                        BusinessEvent.sequence <= request.expected_event_sequence,
                    )
                    .limit(2)
                )
            )
        )
        if len(events) != 1:
            raise core.InvalidOperation(
                "Inventory movement requires one exact recorded event."
            )
        previous = session.scalar(
            select(CostMovementBasis).where(
                CostMovementBasis.tenant_id == tenant,
                CostMovementBasis.movement_id == movement.id,
            )
        )
        if previous and (
            previous.base_quantity != movement.quantity
            or previous.base_unit != request.base_unit
            or previous.occurred_at != movement.occurred_at
            or previous.movement_type != movement.type
            or previous.movement_event_id != events[0].id
        ):
            raise core.InvalidOperation("Admitted inventory movement input changed.")
        receipt = received.get(movement.id)
        opening = openings.get(movement.id)
        if receipt and Decimal(receipt["quantity"]) != movement.quantity:
            raise core.InvalidOperation(
                "Receipt cost quantity differs from inventory input."
            )
        owner_quantity = owned_quantity[movement.id]
        full_cost = receipt["cost"] if receipt else opening["cost"] if opening else None
        inputs.append(
            {
                "movement_id": movement.id,
                "movement_type": movement.type,
                "physical_quantity": str(movement.quantity),
                "quantity": str(owner_quantity),
                "occurred_at": movement.occurred_at.isoformat(),
                "movement_event_id": events[0].id,
                "sequence": events[0].sequence,
                "acquisition_cost": (
                    _money(Decimal(full_cost) * owner_quantity / movement.quantity)
                    if full_cost is not None and owner_quantity > 0
                    else None
                ),
                "selections": selections.get(movement.id, []),
                "return_parts": return_parts.get(movement.id, []),
                "correction": correction_inputs.get(movement.id),
            }
        )
    calculated = _calculate(inputs, request.method)
    return {
        "acquisition_value": _money(calculated.remaining_cost),
        "remaining_quantity": _money(calculated.remaining_quantity),
        "consumption": _format([asdict(issue) for issue in calculated.issues]),
        "returns": _format([asdict(row) for row in calculated.returns]),
        "movement_count": len(inputs),
        "receipt_count": len(received),
        "movements": inputs,
        "receipts": received,
        "openings": openings,
        "ownership_parts": ownership_parts,
    }


def _calculate(inputs: list[dict], method: str):
    try:
        return calculate_inventory(
            [
                InventoryEvent(
                    movement_id=m["movement_id"],
                    kind=KERNEL_KINDS[m["movement_type"]],
                    quantity=Decimal(m["quantity"]),
                    occurred_at=m["occurred_at"],
                    sequence=m["sequence"],
                    acquisition_cost=m["acquisition_cost"],
                    selections=tuple(Selection(**row) for row in m["selections"]),
                    return_parts=tuple(ReturnPart(**row) for row in m["return_parts"]),
                )
                for m in inputs
                if Decimal(m["quantity"]) > 0
            ],
            method=method,
        )
    except (InventoryRefusal, ValueError) as error:
        raise core.InvalidOperation(
            f"Unsupported inventory calculation: {error}"
        ) from error


def _execute(
    session: Session,
    tenant: str,
    request: InventoryReview,
    prepared: dict,
    event,
    action,
    *,
    knowledge_at: datetime | None = None,
) -> dict:
    prior = session.scalar(
        select(CostPolicyRevision)
        .where(
            CostPolicyRevision.tenant_id == tenant,
            CostPolicyRevision.item_id == request.item_id,
        )
        .order_by(CostPolicyRevision.revision.desc())
        .limit(1)
    )
    common = {
        "introduced_event_id": event.id,
        "action_id": action.id,
        "reason": request.reason,
    }
    policy = _new(
        session,
        CostPolicyRevision,
        tenant,
        **common,
        item_id=request.item_id,
        owner_party_id=request.owner_party_id,
        method=request.method,
        currency=request.currency,
        base_unit=request.base_unit,
        history_start=request.history_start,
        revision=prior.revision + 1 if prior else 1,
        supersedes_id=prior.id if prior else None,
    )
    review = _new(
        session,
        CostInventoryReview,
        tenant,
        **common,
        policy_id=policy.id,
        effective_at=request.effective_at,
        target_event_sequence=event.sequence,
        knowledge_at=knowledge_at if knowledge_at is not None else now(),
        algorithm_version=ALGORITHM_VERSION,
        input_schema_version=1,
        content_hash="building",
    )
    bases = {}
    for movement in prepared["movements"]:
        basis = session.scalar(
            select(CostMovementBasis).where(
                CostMovementBasis.tenant_id == tenant,
                CostMovementBasis.movement_id == movement["movement_id"],
            )
        )
        if basis is None:
            basis = _new(
                session,
                CostMovementBasis,
                tenant,
                movement_id=movement["movement_id"],
                movement_event_id=movement["movement_event_id"],
                introduced_event_id=event.id,
                movement_type=movement["movement_type"],
                base_quantity=Decimal(movement["physical_quantity"]),
                base_unit=request.base_unit,
                occurred_at=datetime.fromisoformat(movement["occurred_at"]),
                input_schema_version=1,
            )
        bases[movement["movement_id"]] = basis
        chosen = prepared["receipts"].get(basis.movement_id)
        opening = prepared["openings"].get(basis.movement_id)
        ownership = None
        if chosen:
            previous = session.scalar(
                select(CostOwnershipRevision)
                .where(
                    CostOwnershipRevision.tenant_id == tenant,
                    CostOwnershipRevision.receipt_basis_id
                    == chosen["receipt_basis_id"],
                )
                .order_by(CostOwnershipRevision.revision.desc())
                .limit(1)
            )
            ownership = _new(
                session,
                CostOwnershipRevision,
                tenant,
                **common,
                receipt_basis_id=chosen["receipt_basis_id"],
                owner_party_id=request.owner_party_id,
                evidence_source_record_id=chosen["ownership_source_record_id"],
                covered_quantity=Decimal(movement["quantity"]),
                revision=previous.revision + 1 if previous else 1,
                supersedes_id=previous.id if previous else None,
            )
        if opening:
            opening_basis = session.scalar(
                select(CostOpeningBasis).where(
                    CostOpeningBasis.tenant_id == tenant,
                    CostOpeningBasis.movement_basis_id == basis.id,
                )
            )
            if opening_basis is None:
                _new(
                    session,
                    CostOpeningBasis,
                    tenant,
                    **common,
                    movement_basis_id=basis.id,
                    owner_party_id=request.owner_party_id,
                    evidence_source_record_id=opening["evidence_source_record_id"],
                    acquisition_cost=Decimal(opening["cost"]),
                    currency=request.currency,
                    input_schema_version=1,
                )
            elif (
                opening_basis.evidence_source_record_id
                != opening["evidence_source_record_id"]
                or opening_basis.acquisition_cost != Decimal(opening["cost"])
                or opening_basis.currency != request.currency
            ):
                raise core.InvalidOperation("Admitted opening stock input changed.")
        if Decimal(movement["quantity"]) > 0:
            _new(
                session,
                CostInventoryMember,
                tenant,
                review_id=review.id,
                movement_basis_id=basis.id,
                kind=KINDS[basis.movement_type],
                receipt_manifest_id=chosen["manifest_id"] if chosen else None,
                ownership_revision_id=ownership.id if ownership else None,
            )
    for part in prepared["ownership_parts"]:
        _new(
            session,
            CostInventoryOwnershipPart,
            tenant,
            review_id=review.id,
            movement_basis_id=bases[part["movement_id"]].id,
            owner_party_id=part["owner_party_id"],
            evidence_source_record_id=part["evidence_source_record_id"],
            quantity=Decimal(part["quantity"]),
            input_schema_version=1,
        )
    payload, _, _, _ = _inputs(session, tenant, review, policy)
    review.content_hash = _hash(payload)
    session.flush()
    return _read(session, tenant, request.item_id, review_id=review.id)


def _values(row) -> dict:
    def canonical(value):
        if isinstance(value, Decimal):
            return _money(value)
        if isinstance(value, datetime):
            return value.astimezone(UTC).isoformat(timespec="microseconds")
        return value

    return {
        c.name: canonical(getattr(row, c.name))
        for c in row.__table__.columns
        if c.name != "content_hash"
    }


def _retained_action_parts(
    session: Session, tenant: str, review, policy
) -> tuple[dict[str, list[dict]], dict[str, list[dict]], list[dict]]:
    action = _row(session, ChangeProposal, tenant, review.action_id)
    arguments = json.loads(action.input)
    if arguments.get("operation") == "inventory_review":
        scope = InventoryReview.model_validate(arguments)
    elif arguments.get("operation") == "inventory_batch_review":
        batch = InventoryBatchReview.model_validate(arguments)
        scope = next(
            (row for row in batch.scopes if row.item_id == policy.item_id), None
        )
        if scope is None:
            raise core.InvalidOperation("Inventory action input integrity mismatch.")
    else:
        raise core.InvalidOperation("Inventory action input integrity mismatch.")
    if scope.method != policy.method or scope.owner_party_id != policy.owner_party_id:
        raise core.InvalidOperation("Inventory action input integrity mismatch.")
    grouped: dict[str, list[dict]] = {}
    for selected in scope.specific_selections:
        grouped.setdefault(selected.movement_id, []).append(
            {
                "entry_movement_id": selected.entry_movement_id,
                "receipt_movement_id": selected.receipt_movement_id,
                "quantity": str(selected.quantity),
            }
        )
    returns: dict[str, list[dict]] = {}
    for part in scope.return_parts:
        returns.setdefault(part.movement_id, []).append(
            {
                "issue_movement_id": part.issue_movement_id,
                "entry_movement_id": part.entry_movement_id,
                "receipt_movement_id": part.receipt_movement_id,
                "quantity": _money(part.quantity),
            }
        )
    ownership_parts = sorted(
        [
            {
                "movement_id": part.movement_id,
                "owner_party_id": part.owner_party_id,
                "evidence_source_record_id": part.evidence_source_record_id,
                "quantity": _money(part.quantity),
            }
            for part in scope.ownership_parts
        ],
        key=lambda row: (row["movement_id"], row["owner_party_id"]),
    )
    return grouped, returns, ownership_parts


def _inputs(
    session: Session, tenant: str, review, policy
) -> tuple[dict, list[dict], list[dict], list[dict]]:
    if (
        review.algorithm_version != ALGORITHM_VERSION
        or review.input_schema_version != 1
    ):
        raise core.InvalidOperation("Unsupported inventory review version.")
    members = list(
        session.scalars(
            select(CostInventoryMember)
            .where(
                CostInventoryMember.tenant_id == tenant,
                CostInventoryMember.review_id == review.id,
            )
            .order_by(CostInventoryMember.id)
            .limit(MAX_MOVEMENTS + 1)
        )
    )
    if len(members) > MAX_MOVEMENTS:
        raise core.InvalidOperation("Inventory movement bound exceeded.")
    selections, return_parts, requested_ownership_parts = _retained_action_parts(
        session, tenant, review, policy
    )
    ownership_parts = list(
        session.scalars(
            select(CostInventoryOwnershipPart)
            .where(
                CostInventoryOwnershipPart.tenant_id == tenant,
                CostInventoryOwnershipPart.review_id == review.id,
            )
            .order_by(
                CostInventoryOwnershipPart.movement_basis_id,
                CostInventoryOwnershipPart.owner_party_id,
            )
            .limit(501)
        )
    )
    if len(ownership_parts) > 500:
        raise core.InvalidOperation("Inventory ownership portion bound exceeded.")
    basis_by_id = {}
    grouped_parts: dict[str, list] = {}
    retained_ownership = []
    for part in ownership_parts:
        basis = _row(session, CostMovementBasis, tenant, part.movement_basis_id)
        _row(session, Party, tenant, part.owner_party_id)
        _row(session, SourceRecord, tenant, part.evidence_source_record_id)
        if part.input_schema_version != 1 or part.quantity <= 0:
            raise core.InvalidOperation("Inventory ownership integrity mismatch.")
        basis_by_id[basis.id] = basis
        grouped_parts.setdefault(basis.id, []).append(part)
        retained_ownership.append({"part": _values(part), "movement": _values(basis)})
    for basis_id, parts in grouped_parts.items():
        if (
            sum((part.quantity for part in parts), Decimal(0))
            != basis_by_id[basis_id].base_quantity
        ):
            raise core.InvalidOperation("Inventory ownership integrity mismatch.")
    stored_requested = sorted(
        [
            {
                "movement_id": basis_by_id[part.movement_basis_id].movement_id,
                "owner_party_id": part.owner_party_id,
                "evidence_source_record_id": part.evidence_source_record_id,
                "quantity": _money(part.quantity),
            }
            for part in ownership_parts
        ],
        key=lambda row: (row["movement_id"], row["owner_party_id"]),
    )
    if stored_requested != requested_ownership_parts:
        raise core.InvalidOperation("Inventory action input integrity mismatch.")
    selected_quantity = {
        basis_id: sum(
            (
                part.quantity
                for part in parts
                if part.owner_party_id == policy.owner_party_id
            ),
            Decimal(0),
        )
        for basis_id, parts in grouped_parts.items()
    }
    payload = {
        "policy": _values(policy),
        "review": _values(review),
        "specific_selections": selections,
        "return_parts": return_parts,
        "ownership_parts": retained_ownership,
        "members": [],
    }
    inputs, receipts, openings = [], [], []
    for member in members:
        basis = _row(session, CostMovementBasis, tenant, member.movement_basis_id)
        source_event = _row(session, BusinessEvent, tenant, basis.movement_event_id)
        correction_input = None
        valid_source_event = (
            source_event.event_type == "movement.recorded"
            and source_event.subject_type == "movement"
            and source_event.subject_id == basis.movement_id
        )
        if source_event.event_type == "movement.corrected":
            correction = session.scalar(
                select(MovementCorrection).where(
                    MovementCorrection.tenant_id == tenant,
                    MovementCorrection.replacement_movement_id == basis.movement_id,
                    MovementCorrection.original_movement_id == source_event.subject_id,
                )
            )
            if correction is not None and source_event.subject_type == "movement":
                valid_source_event = True
                correction_input = {
                    "correction_id": correction.id,
                    "original_movement_id": correction.original_movement_id,
                    "compensating_movement_id": correction.compensating_movement_id,
                    "replacement_movement_id": correction.replacement_movement_id,
                    "reason": correction.reason,
                }
        if (
            basis.input_schema_version != 1
            or basis.base_unit != policy.base_unit
            or basis.occurred_at > review.effective_at
            or basis.occurred_at < policy.history_start
            or KINDS.get(basis.movement_type) != member.kind
            or not valid_source_event
            or source_event.sequence > review.target_event_sequence
        ):
            raise core.InvalidOperation("Inventory input integrity mismatch.")
        retained = {
            "member": _values(member),
            "movement": _values(basis),
            "movement_sequence": source_event.sequence,
        }
        if correction_input is not None:
            retained["correction"] = correction_input
        cost = None
        quantity = (
            selected_quantity.get(basis.id, Decimal(0))
            if ownership_parts
            else basis.base_quantity
        )
        if quantity <= 0:
            raise core.InvalidOperation("Inventory ownership integrity mismatch.")
        if member.kind == "receipt":
            if len(receipts) >= MAX_RECEIPTS:
                raise core.InvalidOperation("Inventory receipt bound exceeded.")
            ownership = _row(
                session, CostOwnershipRevision, tenant, member.ownership_revision_id
            )
            receipt_basis = _row(
                session, CostReceiptBasis, tenant, ownership.receipt_basis_id
            )
            if (
                ownership.owner_party_id != policy.owner_party_id
                or ownership.covered_quantity != quantity
                or receipt_basis.movement_id != basis.movement_id
            ):
                raise core.InvalidOperation("Inventory ownership integrity mismatch.")
            held = receipt_cost(
                session,
                tenant,
                basis.movement_id,
                manifest_id=member.receipt_manifest_id,
            )
            if (
                held["actual_cost"] is None
                or held["currency"] != policy.currency
                or held["base_unit"] != policy.base_unit
            ):
                raise core.InvalidOperation(
                    "Inventory receipt review integrity mismatch."
                )
            cost = _money(Decimal(held["actual_cost"]) * quantity / basis.base_quantity)
            retained["ownership"] = _values(ownership)
            receipts.append(
                {
                    "movement_id": basis.movement_id,
                    "receipt_manifest_id": member.receipt_manifest_id,
                    "ownership_revision_id": ownership.id,
                    "ownership_source_record_id": ownership.evidence_source_record_id,
                }
            )
        elif member.kind == "opening":
            opening = session.scalar(
                select(CostOpeningBasis).where(
                    CostOpeningBasis.tenant_id == tenant,
                    CostOpeningBasis.movement_basis_id == basis.id,
                )
            )
            if (
                opening is None
                or (
                    not ownership_parts
                    and opening.owner_party_id != policy.owner_party_id
                )
                or opening.currency != policy.currency
                or opening.input_schema_version != 1
            ):
                raise core.InvalidOperation("Inventory opening integrity mismatch.")
            _row(session, SourceRecord, tenant, opening.evidence_source_record_id)
            cost = _money(opening.acquisition_cost * quantity / basis.base_quantity)
            retained["opening"] = _values(opening)
            openings.append(
                {
                    "movement_id": basis.movement_id,
                    "opening_basis_id": opening.id,
                    "evidence_source_record_id": opening.evidence_source_record_id,
                }
            )
        payload["members"].append(retained)
        inputs.append(
            {
                "movement_id": basis.movement_id,
                "movement_type": basis.movement_type,
                "quantity": str(quantity),
                "occurred_at": basis.occurred_at.isoformat(),
                "sequence": source_event.sequence,
                "acquisition_cost": cost,
                "selections": selections.get(basis.movement_id, []),
                "return_parts": return_parts.get(basis.movement_id, []),
            }
        )
    if ownership_parts:
        member_basis_ids = {member.movement_basis_id for member in members}
        expected_basis_ids = {
            basis_id for basis_id, quantity in selected_quantity.items() if quantity > 0
        }
        if member_basis_ids != expected_basis_ids:
            raise core.InvalidOperation("Inventory ownership integrity mismatch.")
    return payload, inputs, receipts, openings


def _format(value):
    if isinstance(value, Decimal):
        return _money(value)
    if isinstance(value, dict):
        return {k: _format(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_format(v) for v in value]
    return value


def _read(
    session: Session,
    tenant: str,
    item_id: str,
    *,
    review_id: str | None = None,
    assessment_revision_id: str | None = None,
) -> dict:
    with session.no_autoflush:
        core.get_tenant(session, tenant)
        _row(session, Item, tenant, item_id)
        if review_id:
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
        if review is None:
            return {
                "item_id": item_id,
                "review_id": None,
                "review_state": "unreviewed",
                "acquisition_value": None,
                "carrying_value": None,
                "consumption": [],
                "returns": [],
                "missing_basis": ["inventory_scope_not_reviewed"],
                "persistence": {"business_writes": False, "projection_writes": False},
            }
        policy = _row(session, CostPolicyRevision, tenant, review.policy_id)
        if policy.item_id != item_id:
            raise core.NotFound("Costing scope not found.")
        payload, inputs, receipts, openings = _inputs(session, tenant, review, policy)
        if _hash(payload) != review.content_hash:
            raise core.InvalidOperation("Inventory input integrity mismatch.")
        result = _calculate(inputs, policy.method)
        cursor = (
            review.target_event_sequence
            if review_id
            else _relevant_event_sequence(
                session, tenant, item_id, review.target_event_sequence
            )
        )
        stale = cursor > review.target_event_sequence
        if stale:
            from reality.services.carrying_value import (
                review_unchanged_by_assessments,
            )

            stale = not review_unchanged_by_assessments(
                session, tenant, review.id, review.target_event_sequence, cursor
            )
        consumption = []
        for issue in result.issues:
            row = _format(asdict(issue))
            row["basis_cost"] = row["cost"]
            if stale:
                row["cost"] = None
            consumption.append(row)
        returns = [_format(asdict(row)) for row in result.returns]
        answer = {
            "item_id": item_id,
            "review_id": review.id,
            "policy_id": policy.id,
            "policy_revision": policy.revision,
            "history_start": policy.history_start.isoformat(),
            "action_id": review.action_id,
            "reason": review.reason,
            "algorithm_version": review.algorithm_version,
            "method": policy.method,
            "owner_party_id": policy.owner_party_id,
            "currency": policy.currency,
            "base_unit": policy.base_unit,
            "effective_at": review.effective_at.isoformat(),
            "knowledge_at": review.knowledge_at.isoformat(),
            "event_sequence": review.target_event_sequence,
            "review_state": "stale" if stale else "reviewed_complete_at_cutoff",
            "missing_basis": ["inventory_review_stale"] if stale else [],
            "remaining_quantity": None if stale else _money(result.remaining_quantity),
            "basis_remaining_quantity": _money(result.remaining_quantity),
            "acquisition_value": None if stale else _money(result.remaining_cost),
            "basis_acquisition_value": _money(result.remaining_cost),
            "carrying_value": None,
            "carrying_value_state": "assessment_not_supported",
            "consumption": None if stale else consumption,
            "returns": None if stale else returns,
            "basis_returns": returns,
            "remaining": None
            if stale
            else _format([asdict(p) for p in result.remaining]),
            **(
                {
                    "basis_consumption": consumption,
                    "basis_remaining": _format([asdict(p) for p in result.remaining]),
                }
                if stale
                else {}
            ),
            "receipt_sources": receipts,
            "opening_sources": openings,
            **(
                {
                    "ownership_sources": [
                        {
                            "movement_id": row["movement"]["movement_id"],
                            "owner_party_id": row["part"]["owner_party_id"],
                            "evidence_source_record_id": row["part"][
                                "evidence_source_record_id"
                            ],
                            "quantity": row["part"]["quantity"],
                        }
                        for row in payload["ownership_parts"]
                    ]
                }
                if payload["ownership_parts"]
                else {}
            ),
            "persistence": {"business_writes": False, "projection_writes": False},
        }
        from reality.services.carrying_value import enrich_inventory_result

        return enrich_inventory_result(
            session,
            tenant,
            answer,
            assessment_revision_id=assessment_revision_id,
        )


def _batch_members(request: InventoryBatchReview) -> list[InventoryReview]:
    return [
        InventoryReview(
            **scope.model_dump(),
            operation="inventory_review",
            expected_event_sequence=request.expected_event_sequence,
            reason=request.reason,
        )
        for scope in sorted(request.scopes, key=lambda scope: scope.item_id)
    ]


def _check_batch(session: Session, tenant: str, request: InventoryBatchReview) -> dict:
    movements = receipts = 0
    rows = []
    for member in _batch_members(request):
        prepared = _check(
            session,
            tenant,
            member,
            movement_limit=MAX_MOVEMENTS - movements,
            receipt_limit=MAX_RECEIPTS - receipts,
        )
        movements += prepared["movement_count"]
        receipts += prepared["receipt_count"]
        rows.append({"item_id": member.item_id, "review": prepared})
    if _sequence(session, tenant) != request.expected_event_sequence:
        raise core.Conflict("Costing preview is stale; reload the held evidence.")
    return {
        "scopes": rows,
        "movement_count": movements,
        "receipt_count": receipts,
    }


def _execute_batch(
    session: Session,
    tenant: str,
    request: InventoryBatchReview,
    prepared: dict,
    event,
    action,
) -> dict:
    # The caller owns the tenant lock/savepoint. One real decision event seals every
    # member; no worker or collection of old reviews can manufacture this authority.
    members = _batch_members(request)
    reviews = [
        _execute(
            session,
            tenant,
            member,
            checked["review"],
            event,
            action,
            knowledge_at=event.recorded_at,
        )
        for member, checked in zip(members, prepared["scopes"], strict=True)
    ]
    return {
        "action_id": action.id,
        "effective_at": members[0].effective_at.isoformat(),
        "knowledge_at": event.recorded_at.astimezone(UTC).isoformat(),
        "event_sequence": event.sequence,
        "reviews": reviews,
    }
