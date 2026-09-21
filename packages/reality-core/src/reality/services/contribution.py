"""Bounded current evidence candidates, not retained or confirmed commercial matches."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    CommitmentRevision,
    Document,
    DocumentLine,
    Movement,
    MovementCorrection,
    Party,
)
from reality.domain.contribution import (
    ContributionContext,
    ContributionInput,
    MatchedSlice,
    aggregate_contribution,
)
from reality.services import core
from reality.services.costing import _hash, _money, _row, _sequence, inventory_cost
from reality.services.finance import components


def _gap(line_id: str, reason: str) -> dict:
    return {
        "document_line_id": line_id,
        "state": "unavailable",
        "known_db1": None,
        "db1": None,
        "db2": None,
        "db1_rate": None,
        "db2_rate": None,
        "missing_basis": [reason],
    }


def _candidate(session: Session, tenant: str, billed: DocumentLine) -> dict:
    def gap(reason):
        return _gap(billed.id, reason)

    invoice = _row(session, Document, tenant, billed.document_id)
    if (
        invoice.type != "sales_invoice"
        or billed.line_type != "item"
        or not billed.item_id
    ):
        return gap("unsupported_revenue_type")
    if not billed.billed_document_line_id:
        return gap("billed_order_line_missing")
    agreed = _row(session, DocumentLine, tenant, billed.billed_document_line_id)
    order = _row(session, Document, tenant, agreed.document_id)
    if order.type != "sales_order" or agreed.line_type != "item":
        return gap("unsupported_order_scope")
    for party_id in (invoice.party_id, order.party_id):
        if party_id:
            _row(session, Party, tenant, party_id)
    if not invoice.party_id or invoice.party_id != order.party_id:
        return gap("customer_scope_mismatch")
    if invoice.currency != order.currency:
        return gap("currency_scope_mismatch")
    if billed.item_id != agreed.item_id:
        return gap("item_scope_mismatch")
    if billed.unit != agreed.unit:
        return gap("unit_scope_mismatch")
    if billed.quantity <= 0 or billed.quantity != agreed.quantity:
        return gap("quantity_scope_mismatch")
    billing = list(
        session.scalars(
            select(DocumentLine.id)
            .where(
                DocumentLine.tenant_id == tenant,
                DocumentLine.billed_document_line_id.in_([agreed.id, billed.id]),
            )
            .limit(2)
        )
    )
    if billing != [billed.id]:
        return gap("ambiguous_billing")
    commitments = list(
        session.scalars(
            select(Commitment)
            .where(
                Commitment.tenant_id == tenant,
                Commitment.document_line_id == agreed.id,
                Commitment.type == "customer_delivery",
            )
            .limit(2)
        )
    )
    if len(commitments) != 1:
        return gap("ambiguous_fulfilment")
    promise = commitments[0]
    if promise.cancelled_at or session.scalar(
        select(CommitmentRevision.id)
        .where(
            CommitmentRevision.tenant_id == tenant,
            CommitmentRevision.commitment_id == promise.id,
        )
        .limit(1)
    ):
        return gap("revised_fulfilment_unsupported")
    if promise.document_id not in (None, order.id) or promise.item_id != billed.item_id:
        return gap("item_scope_mismatch")
    if promise.to_party_id != invoice.party_id:
        return gap("customer_scope_mismatch")
    if promise.quantity != billed.quantity:
        return gap("quantity_scope_mismatch")
    movements = list(
        session.scalars(
            select(Movement)
            .where(
                Movement.tenant_id == tenant,
                Movement.commitment_id == promise.id,
            )
            .limit(2)
        )
    )
    if len(movements) != 1:
        return gap("ambiguous_fulfilment")
    movement = movements[0]
    if movement.type != "shipment" or movement.resolves_movement_id:
        return gap("unsupported_fulfilment")
    if movement.item_id != billed.item_id:
        return gap("item_scope_mismatch")
    if movement.quantity != billed.quantity:
        return gap("quantity_scope_mismatch")
    if session.scalar(
        select(MovementCorrection.id)
        .where(
            MovementCorrection.tenant_id == tenant,
            or_(
                MovementCorrection.original_movement_id == movement.id,
                MovementCorrection.compensating_movement_id == movement.id,
                MovementCorrection.replacement_movement_id == movement.id,
            ),
        )
        .limit(1)
    ):
        return gap("corrected_fulfilment_unsupported")
    received = components._received(session, tenant, invoice, billed)
    net = received["amounts"]["net"]
    if net is None:
        return gap("received_net_missing")
    if Decimal(net) < 0:
        return gap("negative_revenue_requires_match")
    inventory = inventory_cost(session, tenant, billed.item_id)
    if inventory["review_state"] != "reviewed_complete_at_cutoff":
        return gap(
            "inventory_review_stale"
            if inventory["review_state"] == "stale"
            else "inventory_scope_not_reviewed"
        )
    if inventory["owner_party_id"] != promise.from_party_id:
        return gap("owner_scope_mismatch")
    if inventory["currency"] != invoice.currency:
        return gap("currency_scope_mismatch")
    if inventory["base_unit"] != billed.unit:
        return gap("unit_scope_mismatch")
    consumed = [
        c
        for c in inventory["consumption"]
        if c["movement_id"] == movement.id and c["kind"] == "issue"
    ]
    if len(consumed) != 1 or consumed[0]["cost"] is None:
        return gap("consumption_not_reviewed")
    cost = consumed[0]
    if Decimal(cost["quantity"]) != billed.quantity:
        return gap("quantity_scope_mismatch")
    cutoff = datetime.fromisoformat(inventory["effective_at"])
    if movement.occurred_at > cutoff:
        return gap("consumption_after_cutoff")
    context = ContributionContext(
        tenant_id=tenant,
        generation_id=None,
        profile_revision_id=None,
        mode="preview",
        policy_revision_id=inventory["policy_id"],
        profile="commercial_v1",
        effective_at=cutoff,
        knowledge_at=datetime.fromisoformat(inventory["knowledge_at"]),
    )
    unknown = ContributionInput(amount=None, state="unknown")
    matched = MatchedSlice(
        slice_id=billed.id,
        context=context,
        currency=invoice.currency,
        base_unit=billed.unit,
        quantity=billed.quantity,
        economic_date=movement.occurred_at.date(),
        position_id=agreed.id,
        order_id=order.id,
        item_id=billed.item_id,
        customer_id=invoice.party_id,
        revenue=ContributionInput(
            amount=net, state="evidenced", references=(billed.id,)
        ),
        goods_cost=ContributionInput(
            amount=cost["cost"],
            state="reviewed",
            references=(inventory["review_id"], movement.id),
        ),
        direct_selling_cost=unknown,
        allocated_selling_cost=unknown,
    )
    calculated = aggregate_contribution([matched], context=context).groups[0]
    return {
        "document_line_id": billed.id,
        "state": "candidate",
        "profile": "commercial_v1",
        "known_db1": _money(calculated.db1.known),
        "db1": None,
        "db2": None,
        "db1_rate": None,
        "db2_rate": None,
        "currency": invoice.currency,
        "base_unit": billed.unit,
        "quantity": _money(billed.quantity),
        "missing_basis": [
            "commercial_match_not_reviewed",
            "contribution_profile_not_reviewed",
            "selling_costs_unknown",
        ],
        "trace": {
            "order_line_id": agreed.id,
            "order_id": order.id,
            "commitment_id": promise.id,
            "movement_id": movement.id,
            "inventory_review_id": inventory["review_id"],
            "policy_id": inventory["policy_id"],
            "revenue": received,
            "consumption": cost,
            "receipt_sources": [
                source
                for source in inventory["receipt_sources"]
                if source["movement_id"]
                in {part["receipt_movement_id"] for part in cost["parts"]}
            ],
            "customer_id": invoice.party_id,
            "item_id": billed.item_id,
            "sales_channel": order.sales_channel,
            "invoice_date": (
                invoice.document_date.isoformat() if invoice.document_date else None
            ),
            "proposed_economic_at": movement.occurred_at.isoformat(),
            "inventory_effective_at": inventory["effective_at"],
            "inventory_knowledge_at": inventory["knowledge_at"],
            "formula": "known received net revenue - reviewed consumed acquisition cost",
        },
    }


def _read(session: Session, tenant: str, document_line_id: str) -> dict:
    with session.no_autoflush:
        core.get_tenant(session, tenant)
        if session.connection().get_isolation_level() != "READ COMMITTED":
            raise core.InvalidOperation(
                "Current contribution preview requires READ COMMITTED."
            )
        before = _sequence(session, tenant)
        billed = _row(session, DocumentLine, tenant, document_line_id)
        result = _candidate(session, tenant, billed)
        if before != _sequence(session, tenant):
            raise core.Conflict(
                "Contribution inputs changed during preview; retry the read."
            )
        result["candidate_hash"] = (
            _hash(result) if result["state"] == "candidate" else None
        )
        return {
            **result,
            "event_sequence": before,
            "historical_replay": False,
            "persistence": {"business_writes": False, "projection_writes": False},
        }
