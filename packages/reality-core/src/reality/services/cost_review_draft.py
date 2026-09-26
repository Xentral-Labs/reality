"""Draft inventory and contribution cost reviews from held records (spec 282).

The draft mirrors the admission rules of `inventory_costing._check` and the contribution
preview, so a complete draft is accepted by the existing proposal validation unchanged.
It copies stated values and derived identities only: an acquisition cost comes from a
source that states it, never from arithmetic here (Constitution VIII). Nothing is stored.
"""

import json
from datetime import timedelta
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from reality.db.components import FinancialComponent
from reality.db.core import (
    Document,
    DocumentLine,
    Item,
    Movement,
    MovementCorrection,
    Party,
    PartyRole,
    SourceRecord,
)
from reality.domain.cost_review_draft import (
    DRAFT_REASON,
    draft,
    method_choices,
    open_input,
)
from reality.services import core
from reality.services.inventory_costing import KINDS, MAX_MOVEMENTS, MAX_RECEIPTS

#: The SourceRecord type an opening cost statement is stored as (services/opening_cost.py).
OPENING_COST_SOURCE_TYPE = "opening_cost_statement"


def cost_review_draft(
    session: Session,
    tenant: str,
    *,
    kind: str,
    scope_id: str,
    answers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return complete review arguments, or the open inputs a person still owes."""
    if kind not in {"inventory", "contribution"}:
        raise core.InvalidOperation("Unsupported cost review draft kind.")
    with session.no_autoflush:
        core.get_tenant(session, tenant)
        if kind == "contribution":
            return _contribution(session, tenant, scope_id)
        return _inventory(
            session, tenant, _item_scope(session, tenant, scope_id), answers or {}
        )


def _item_scope(session: Session, tenant: str, reference: str) -> str:
    """The item's opaque ID, from itself or from an unambiguous SKU or exact name.

    Chat carries only earlier answers' text between turns, so an agent may name the
    item as the person did. A human reference resolves only when exactly one item of
    this company matches; it never becomes identity itself.
    """
    if session.scalar(
        select(Item.id).where(Item.tenant_id == tenant, Item.id == reference)
    ):
        return reference
    for column in (Item.sku, func.lower(Item.name)):
        value = reference.strip() if column is Item.sku else reference.strip().lower()
        matches = session.scalars(
            select(Item.id).where(Item.tenant_id == tenant, column == value).limit(2)
        ).all()
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise core.InvalidOperation(
                "More than one item matches; name the item by its SKU."
            )
    # Last, a unique partial match on SKU or name ("282" for "Stehlampe 282").
    needle = f"%{reference.strip().lower()}%"
    candidates = session.execute(
        select(Item.id, Item.sku, Item.name)
        .where(
            Item.tenant_id == tenant,
            or_(func.lower(Item.sku).like(needle), func.lower(Item.name).like(needle)),
        )
        .limit(6)
    ).all()
    if len(candidates) == 1:
        return candidates[0].id
    if candidates:
        names = ", ".join(f"{row.name} ({row.sku})" for row in candidates[:5])
        raise core.InvalidOperation(f"Several items match: {names}. Ask which one.")
    raise core.NotFound("Item not found.")


def _row(session: Session, model, tenant: str, identity: str):
    from reality.services.costing import _row as costing_row

    return costing_row(session, model, tenant, identity)


def _contribution(session: Session, tenant: str, line_id: str) -> dict[str, Any]:
    from reality.services import costing

    _row(session, DocumentLine, tenant, line_id)
    try:
        preview = costing.contribution_preview(session, tenant, line_id)
    except core.Conflict:
        preview = None
    sequence = (
        preview["event_sequence"] if preview else costing._sequence(session, tenant)
    )
    basis = [{"kind": "document_line", "id": line_id, "role": "invoice_line"}]
    if not preview or preview["state"] != "candidate":
        gaps = list((preview or {}).get("missing_basis") or ())
        return draft(
            kind="contribution",
            scope_id=line_id,
            event_sequence=sequence,
            arguments=None,
            open_inputs=[
                open_input(
                    "upstream_not_ready", reason=gaps[0] if gaps else "inputs_changed"
                )
            ],
            basis=basis,
        )
    trace = preview["trace"]
    basis += [
        {"kind": "document_line", "id": trace["order_line_id"], "role": "order_line"},
        {"kind": "movement", "id": trace["movement_id"], "role": "shipment"},
        {
            "kind": "cost_inventory_review",
            "id": trace["inventory_review_id"],
            "role": "goods_cost",
        },
    ]
    revenue = (trace.get("revenue") or {}).get("amounts") or {}
    return draft(
        kind="contribution",
        scope_id=line_id,
        event_sequence=sequence,
        summary={
            "currency": preview.get("currency"),
            "quantity": preview.get("quantity"),
            "base_unit": preview.get("base_unit"),
            "received_net": revenue.get("net"),
            "goods_cost": (trace.get("consumption") or {}).get("cost"),
            "known_db1": preview.get("known_db1"),
        },
        arguments={
            "operation": "contribution_review",
            "expected_event_sequence": sequence,
            "reason": DRAFT_REASON,
            "document_line_id": line_id,
            "expected_candidate_hash": preview["candidate_hash"],
            "profile": "commercial_v1",
            "profile_confirmed": True,
            "revenue_complete": True,
            "economic_at": trace["proposed_economic_at"],
        },
        open_inputs=[],
        basis=basis,
    )


def _company_parties(session: Session, tenant: str) -> list[str]:
    """Parties the company records as itself, by role or by type."""
    return sorted(
        set(
            session.scalars(
                select(Party.id)
                .outerjoin(
                    PartyRole,
                    (PartyRole.tenant_id == Party.tenant_id)
                    & (PartyRole.party_id == Party.id),
                )
                .where(
                    Party.tenant_id == tenant,
                    or_(PartyRole.role == "company", Party.type == "company"),
                )
            )
        )
    )


def _effective_movements(
    session: Session, tenant: str, item_id: str
) -> tuple[list[Movement], bool]:
    """Movements a review counts: corrected originals and compensations drop out."""
    movements = list(
        session.scalars(
            select(Movement)
            .where(Movement.tenant_id == tenant, Movement.item_id == item_id)
            .order_by(Movement.occurred_at, Movement.id)
            .limit(MAX_MOVEMENTS + 1)
        )
    )
    exceeded = len(movements) > MAX_MOVEMENTS
    ids = [movement.id for movement in movements]
    excluded: set[str] = set()
    for correction in session.scalars(
        select(MovementCorrection).where(
            MovementCorrection.tenant_id == tenant,
            or_(
                MovementCorrection.original_movement_id.in_(ids),
                MovementCorrection.compensating_movement_id.in_(ids),
            ),
        )
    ):
        excluded.update(
            (correction.original_movement_id, correction.compensating_movement_id)
        )
    return [m for m in movements if m.id not in excluded], exceeded


def _receipt_ownership_source(
    session: Session, tenant: str, movement: Movement, trace: list[dict]
) -> str | None:
    """The receipt's own source, else the source of the document behind its goods cost."""
    if movement.source_record_id:
        return movement.source_record_id
    for part in trace:
        if part.get("category") != "goods":
            continue
        component = session.scalar(
            select(FinancialComponent).where(
                FinancialComponent.tenant_id == tenant,
                FinancialComponent.id == part["component_id"],
            )
        )
        if component is None:
            continue
        document_id = component.document_id
        if document_id is None and component.document_line_id:
            document_id = session.scalar(
                select(DocumentLine.document_id).where(
                    DocumentLine.tenant_id == tenant,
                    DocumentLine.id == component.document_line_id,
                )
            )
        source = session.scalar(
            select(Document.source_record_id).where(
                Document.tenant_id == tenant, Document.id == document_id
            )
        )
        if source:
            return source
    return None


def _opening_statement(
    session: Session, tenant: str, movement: Movement
) -> dict[str, Any] | None:
    """The stated acquisition cost the opening points to, copied exactly."""
    if not movement.source_record_id:
        return None
    record = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.id == movement.source_record_id,
        )
    )
    if record is None or record.source_type != OPENING_COST_SOURCE_TYPE:
        return None
    stated = json.loads(record.payload or "{}")
    if not stated.get("amount") or not stated.get("currency"):
        return None
    return {"record_id": record.id, **stated}


def _inventory(
    session: Session, tenant: str, item_id: str, answers: dict[str, Any]
) -> dict[str, Any]:
    from reality.services import costing

    item = _row(session, Item, tenant, item_id)
    sequence = costing._sequence(session, tenant)
    movements, exceeded = _effective_movements(session, tenant, item_id)
    receipts = [m for m in movements if m.type == "receipt"]
    if exceeded or len(receipts) > MAX_RECEIPTS:
        return draft(
            kind="inventory",
            scope_id=item_id,
            event_sequence=sequence,
            arguments=None,
            open_inputs=[open_input("review_bound_exceeded")],
            basis=[{"kind": "item", "id": item_id, "role": "scope"}],
        )
    open_inputs: list[dict[str, Any]] = []
    basis: list[dict[str, str]] = [{"kind": "item", "id": item_id, "role": "scope"}]

    # Owner: the company's own party; an answer may pick among several, never invent one.
    candidates = _company_parties(session, tenant)
    owner = answers.get("owner_party_id")
    if owner not in candidates:
        owner = candidates[0] if len(candidates) == 1 else None
    if owner is None:
        open_inputs.append(
            open_input("company_party_missing", choices=candidates or None)
        )

    if not movements:
        open_inputs.append(
            open_input("upstream_not_ready", reason="inventory_history_empty")
        )

    currencies: set[str] = set()
    receipt_rows, opening_rows = [], []
    economic, losses, supplier_returns, customer_returns = [], [], [], []
    for movement in movements:
        subject = {"kind": "movement", "id": movement.id}
        if movement.type not in KINDS:
            open_inputs.append(
                open_input(
                    "movement_unclassified", subject=subject, reason=movement.type
                )
            )
        elif movement.type == "receipt":
            cost = costing.receipt_cost(session, tenant, movement.id)
            gaps = sorted(set(cost["missing_basis"]) - {"review_stale"})
            if gaps:
                open_inputs.append(
                    open_input(
                        "receipt_cost_incomplete", subject=subject, reason=gaps[0]
                    )
                )
                continue
            source = _receipt_ownership_source(session, tenant, movement, cost["trace"])
            if source is None:
                open_inputs.append(open_input("ownership_ambiguous", subject=subject))
                continue
            currencies.add(cost["currency"])
            receipt_rows.append(
                {
                    "movement_id": movement.id,
                    "manifest_id": cost["manifest_id"],
                    "ownership_source_record_id": source,
                }
            )
            basis.append(
                {
                    "kind": "cost_input_manifest",
                    "id": cost["manifest_id"],
                    "role": "receipt_cost",
                }
            )
        elif movement.type == "opening_stock":
            stated = _opening_statement(session, tenant, movement)
            if stated is None:
                open_inputs.append(open_input("opening_cost_missing", subject=subject))
                continue
            currencies.add(stated["currency"])
            opening_rows.append(
                {
                    "movement_id": movement.id,
                    "evidence_source_record_id": stated["record_id"],
                    "acquisition_cost": stated["amount"],
                }
            )
            basis.append(
                {
                    "kind": "source_record",
                    "id": stated["record_id"],
                    "role": "opening_cost",
                }
            )
        elif movement.type == "shipment":
            economic.append(movement.id)
        elif movement.type == "adjustment":
            losses.append(movement.id)
        elif movement.type == "supplier_return":
            supplier_returns.append(movement.id)
        elif movement.type == "return":
            customer_returns.append(movement.id)
            # Exact original issue portions are not determined by held links yet.
            open_inputs.append(
                open_input("return_portion_undetermined", subject=subject)
            )
    for identity in supplier_returns:
        # Supplier returns always need an exact layer selection (inventory_costing._check).
        open_inputs.append(
            open_input(
                "movement_unclassified",
                subject={"kind": "movement", "id": identity},
                reason="specific_selection_required",
            )
        )

    choices = method_choices(item.tracking_type)
    method = answers.get("method")
    if method not in choices:
        method = None
        open_inputs.append(
            open_input("valuation_method", choices=choices, default="fifo")
        )
    elif method == "specific" and (economic or losses):
        open_inputs.append(
            open_input("movement_unclassified", reason="specific_selection_required")
        )

    if len(currencies) > 1:
        open_inputs.append(open_input("currency_ambiguous", choices=sorted(currencies)))
    currency = next(iter(currencies)) if len(currencies) == 1 else None
    if currency is None and not currencies and owner:
        currency = session.scalar(
            select(Party.default_currency).where(
                Party.tenant_id == tenant, Party.id == owner
            )
        )
    arguments = (
        {
            "operation": "inventory_review",
            "expected_event_sequence": sequence,
            "reason": DRAFT_REASON,
            "item_id": item_id,
            "owner_party_id": owner,
            "method": method,
            "currency": currency,
            "base_unit": item.unit,
            "history_start": (
                movements[0].occurred_at - timedelta(seconds=1)
            ).isoformat(),
            "effective_at": core.now().isoformat(),
            "history_complete_from_zero": True,
            "receipt_cost_scopes_confirmed": True,
            "economic_issue_ids": economic,
            "loss_movement_ids": losses,
            "supplier_return_ids": supplier_returns,
            "customer_return_ids": customer_returns,
            "receipts": receipt_rows,
            "openings": opening_rows,
        }
        if movements
        else None
    )
    basis += [{"kind": "movement", "id": m.id, "role": m.type} for m in movements]
    counts: dict[str, int] = {}
    for movement in movements:
        counts[movement.type] = counts.get(movement.type, 0) + 1
    names = dict(
        session.execute(
            select(Party.id, Party.name).where(
                Party.tenant_id == tenant, Party.id.in_(candidates)
            )
        ).all()
    )
    return draft(
        kind="inventory",
        scope_id=item_id,
        event_sequence=sequence,
        arguments=arguments,
        open_inputs=open_inputs,
        basis=basis,
        summary={
            "item_name": item.name,
            "item_sku": item.sku,
            "base_unit": item.unit,
            "owner_name": names.get(owner) if owner else None,
            "party_names": names,
            "currency": currency,
            "movement_counts": counts,
            "openings": [
                {
                    "amount": row["acquisition_cost"],
                    "currency": currency,
                    "quantity": format(
                        next(
                            m.quantity for m in movements if m.id == row["movement_id"]
                        ),
                        "f",
                    ),
                    "movement_id": row["movement_id"],
                }
                for row in opening_rows
            ],
        },
    )


class DraftChanged(core.Conflict):
    """The draft moved or still needs answers; the caller re-drafts instead of proposing."""

    code = "draft_changed"

    def __init__(self, current: dict[str, Any]):
        super().__init__("The cost review draft changed or still has open inputs.")
        self.draft = current


def propose_drafted_review(
    session: Session,
    tenant: str,
    *,
    kind: str,
    scope_id: str,
    answers: dict[str, Any] | None = None,
    event_sequence: int | None = None,
    actor_type: str = "human",
):
    """Re-draft now and propose exactly that decision; one path for Web, MCP and chat.

    Nobody copies review arguments: the caller names the scope and the answers, and the
    server derives the arguments again. A draft that moved since the caller saw it, or
    that still has open inputs, is refused so a stale decision is never proposed. The
    same drafted decision submitted twice returns the waiting proposal.
    """
    from reality.db.core import ChangeProposal
    from reality.services.costing import _request as cost_request
    from reality.tools.application import create_change_proposal

    current = cost_review_draft(
        session, tenant, kind=kind, scope_id=scope_id, answers=answers
    )
    if current["open_inputs"] or (
        event_sequence is not None and current["event_sequence"] != event_sequence
    ):
        raise DraftChanged(current)
    arguments = current["arguments"]

    def decision(values: dict[str, Any]) -> dict[str, Any]:
        # The draft's valuation cutoff is "now"; at the same event sequence and with
        # the same content it is the same decision, whatever second it was drafted.
        normalized = cost_request(values).model_dump(mode="json")
        normalized.pop("effective_at", None)
        return normalized

    wanted = decision(arguments)
    for row in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant,
            ChangeProposal.type == "tool:cost.change",
            ChangeProposal.status == "proposed",
        )
    ):
        if decision(json.loads(row.input or "{}")) == wanted:
            return row, False
    proposal = create_change_proposal(
        session, tenant, "cost.change", arguments, actor_type=actor_type
    )
    return proposal, True
