"""Received evidence and separate, reasoned cost/classification decisions."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from decimal import InvalidOperation as InvalidDecimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.components import (
    ComponentAssignment,
    ComponentAssignmentPart,
    FinancialComponent,
)
from reality.db.core import Document, DocumentLine, FinanceState, SourceRecord, uid
from reality.services import core
from reality.services.business_locks import lock_delivery_state
from reality.services.finance.accounts import lock_finance
from reality.services.finance.references import list_references, resolve_reference

DOCUMENT_TYPES = {
    "sales_invoice",
    "supplier_invoice",
    "credit_note",
    "supplier_credit_note",
}
BASES = ("net", "gross", "base")


def _amount(value: Any) -> Decimal:
    try:
        if isinstance(value, bool):
            raise TypeError()
        amount = Decimal(str(value))
        if (
            not amount.is_finite()
            or abs(amount) >= Decimal(100000000000000)
            or amount != amount.quantize(Decimal(".0001"))
        ):
            raise ValueError()
        return amount
    except (InvalidDecimal, ValueError, TypeError) as error:
        raise core.InvalidOperation(
            "Amount must be an exact finite decimal with at most four decimal places."
        ) from error


def _money(value: Decimal | None) -> str | None:
    return format(value.normalize(), "f") if value is not None else None


def _document(session: Session, tenant_id: str, document_id: str) -> Document:
    doc = core._tenant_record(session, Document, tenant_id, document_id)
    if doc.type not in DOCUMENT_TYPES:
        raise core.InvalidOperation(
            "Select a customer or supplier invoice or credit note for attribution."
        )
    return doc


def _received(
    session: Session, tenant_id: str, doc: Document, line: DocumentLine | None
) -> dict:
    source = (
        core._tenant_record(session, SourceRecord, tenant_id, doc.source_record_id)
        if doc.source_record_id
        else None
    )
    payload = json.loads(line.payload if line else source.payload if source else "{}")
    detail = payload.get("reality_finance_v1", {}) if isinstance(payload, dict) else {}
    if not isinstance(detail, dict) or detail.get("version", 1) != 1:
        raise core.InvalidOperation("Unsupported received finance detail contract.")
    gross = _amount(line.gross_amount if line else doc.gross_amount)
    if detail.get("gross") is not None and _amount(detail["gross"]) != gross:
        raise core.InvalidOperation(
            "Received gross contradicts the normalized evidence."
        )
    if detail.get("currency", doc.currency) != doc.currency:
        raise core.InvalidOperation(
            "Received component currency contradicts the document."
        )
    values = {
        key: _money(_amount(detail[key])) if detail.get(key) is not None else None
        for key in ("net", "tax", "base")
    }
    values["gross"] = _money(gross)
    result = {
        "document_id": doc.id,
        "document_line_id": line.id if line else None,
        "source_record_id": doc.source_record_id,
        "source_path": "DocumentLine.payload.reality_finance_v1"
        if line
        else "SourceRecord.payload.reality_finance_v1",
        "label": (line.description or line.sku or line.id) if line else doc.number,
        "currency": doc.currency,
        "amounts": values,
        "source_codes": detail.get("codes", {}),
        "document_type": doc.type,
    }
    result["evidence_hash"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, default=str).encode()
    ).hexdigest()
    return result


def _component(
    session: Session, tenant_id: str, doc_id: str, line_id: str | None
) -> FinancialComponent | None:
    return session.scalar(
        select(FinancialComponent).where(
            FinancialComponent.tenant_id == tenant_id,
            FinancialComponent.document_line_id == line_id
            if line_id
            else FinancialComponent.document_id == doc_id,
        )
    )


def _stored_amounts(component: FinancialComponent) -> dict:
    return {
        key: _money(getattr(component, "stated_" + key))
        for key in ("net", "tax", "gross", "base")
    }


def _assignment(
    session: Session,
    tenant_id: str,
    component: FinancialComponent,
    row: ComponentAssignment,
) -> dict:
    parts = [
        {
            "cost_center_reference_id": part.cost_center_reference_id,
            "amount": _money(part.amount),
        }
        for part in session.scalars(
            select(ComponentAssignmentPart)
            .where(
                ComponentAssignmentPart.tenant_id == tenant_id,
                ComponentAssignmentPart.assignment_revision_id == row.id,
            )
            .order_by(ComponentAssignmentPart.cost_center_reference_id)
        )
    ]
    assigned = sum((Decimal(part["amount"]) for part in parts), Decimal(0))
    basis = getattr(component, "stated_" + row.basis)
    return {
        "id": row.id,
        "component_id": component.id,
        "revision": row.revision,
        "basis": row.basis,
        "basis_amount": _money(basis),
        "assigned": _money(assigned),
        "unassigned": _money(basis - assigned) if basis is not None else None,
        "currency": component.currency,
        "case_reference_id": row.case_reference_id,
        "group_reference_id": row.group_reference_id,
        "parts": parts,
        "references": row.reference_snapshot,
        "reason": row.reason,
        "actor_id": row.actor_id,
        "action_id": row.action_id,
        "created_at": row.created_at.isoformat(),
    }


def _current(
    session: Session, tenant_id: str, component: FinancialComponent | None
) -> dict | None:
    if component is None:
        return None
    row = session.scalar(
        select(ComponentAssignment)
        .where(
            ComponentAssignment.tenant_id == tenant_id,
            ComponentAssignment.component_id == component.id,
        )
        .order_by(ComponentAssignment.revision.desc())
        .limit(1)
    )
    return _assignment(session, tenant_id, component, row) if row else None


def _page(limit: int, offset: int) -> None:
    if (
        not isinstance(limit, int)
        or not 1 <= limit <= 200
        or not isinstance(offset, int)
        or offset < 0
    ):
        raise core.InvalidOperation("Use limit 1–200 and a nonnegative offset.")


def component_context(
    session: Session,
    tenant_id: str,
    document_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
    reference_query: str = "",
) -> dict:
    _page(limit, offset)
    doc = _document(session, tenant_id, document_id)
    summary = _received(session, tenant_id, doc, None)
    count = session.scalar(
        select(func.count())
        .select_from(DocumentLine)
        .where(DocumentLine.tenant_id == tenant_id, DocumentLine.document_id == doc.id)
    )
    lines = (
        list(
            session.scalars(
                select(DocumentLine)
                .where(
                    DocumentLine.tenant_id == tenant_id,
                    DocumentLine.document_id == doc.id,
                )
                .order_by(DocumentLine.id)
                .limit(limit)
                .offset(offset)
            )
        )
        if count
        else ([None] if offset == 0 else [])
    )
    items = []
    for line in lines:
        item = _received(session, tenant_id, doc, line)
        component = _component(session, tenant_id, doc.id, line.id if line else None)
        item.update(
            component_id=component.id if component else None,
            current=_current(session, tenant_id, component),
        )
        from reality.services.finance.source_mappings import resolve_source_codes

        item["source_resolution"] = resolve_source_codes(session, tenant_id, item)
        items.append(item)
    return {
        "document_id": doc.id,
        "number": doc.number,
        "summary": summary,
        "line_scope": bool(count),
        "total": count or 1,
        "limit": limit,
        "offset": offset,
        "revision": session.scalar(
            select(FinanceState.revision).where(FinanceState.tenant_id == tenant_id)
        )
        or 0,
        "items": items,
        "references": {
            kind: list_references(
                session,
                tenant_id,
                kind=kind,
                state="active",
                query=reference_query,
                limit=200,
            )
            for kind in ("cost_center", "case_code", "coding_group")
        },
    }


def component_history(
    session: Session,
    tenant_id: str,
    component_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    _page(limit, offset)
    component = core._tenant_record(
        session, FinancialComponent, tenant_id, component_id
    )
    clauses = [
        ComponentAssignment.tenant_id == tenant_id,
        ComponentAssignment.component_id == component.id,
    ]
    return {
        "component_id": component.id,
        "document_id": component.document_id,
        "document_line_id": component.document_line_id,
        "amounts": _stored_amounts(component),
        "currency": component.currency,
        "total": session.scalar(
            select(func.count()).select_from(ComponentAssignment).where(*clauses)
        ),
        "limit": limit,
        "offset": offset,
        "items": [
            _assignment(session, tenant_id, component, row)
            for row in session.scalars(
                select(ComponentAssignment)
                .where(*clauses)
                .order_by(ComponentAssignment.revision.desc())
                .limit(limit)
                .offset(offset)
            )
        ],
    }


def preview_assignment(session: Session, tenant_id: str, arguments: dict) -> dict:
    lock_delivery_state(session, tenant_id)
    state = lock_finance(session, tenant_id)
    doc = _document(session, tenant_id, arguments["document_id"])
    line = (
        core._tenant_record(
            session, DocumentLine, tenant_id, arguments["document_line_id"]
        )
        if arguments.get("document_line_id")
        else None
    )
    if line and line.document_id != doc.id:
        raise core.NotFound("Component line not found on this document.")
    if line is None and session.scalar(
        select(DocumentLine.id)
        .where(DocumentLine.tenant_id == tenant_id, DocumentLine.document_id == doc.id)
        .limit(1)
    ):
        raise core.InvalidOperation(
            "This document has lines; assign individual lines instead of its summary."
        )
    received = _received(session, tenant_id, doc, line)
    if (
        arguments["expected_revision"] != state.revision
        or arguments["expected_evidence_hash"] != received["evidence_hash"]
    ):
        raise core.Conflict(
            "Assignment preview is stale; reload evidence and references."
        )
    basis = arguments["basis"]
    reason = arguments["reason"].strip()
    if basis not in BASES or not reason or len(reason) > 4000:
        raise core.InvalidOperation(
            "Supported basis and a nonempty assignment reason are required."
        )
    component = _component(session, tenant_id, doc.id, line.id if line else None)
    if component and (
        _stored_amounts(component) != received["amounts"]
        or component.currency != received["currency"]
    ):
        raise core.Conflict(
            "Normalized component evidence has changed; reconcile the source instead of rewriting history."
        )
    before = _current(session, tenant_id, component)
    references = {"case": None, "group": None, "centers": {}}
    for key, kind in [("case", "case_code"), ("group", "coding_group")]:
        if arguments.get(key + "_reference_id"):
            row = resolve_reference(
                session, tenant_id, arguments[key + "_reference_id"], kind
            )
            references[key] = {
                k: getattr(row, k) for k in ("id", "code", "name", "kind", "revision")
            }
    parts = []
    seen = set()
    if len(arguments["parts"]) > 100:
        raise core.InvalidOperation("Use at most 100 cost-center shares.")
    for part in arguments["parts"]:
        row = resolve_reference(
            session, tenant_id, part["cost_center_reference_id"], "cost_center"
        )
        amount = _amount(part["amount"])
        if amount <= 0 or row.id in seen:
            raise core.InvalidOperation(
                "Use distinct cost centers and strictly positive shares."
            )
        seen.add(row.id)
        references["centers"][row.id] = {
            k: getattr(row, k) for k in ("id", "code", "name", "kind", "revision")
        }
        parts.append({"cost_center_reference_id": row.id, "amount": _money(amount)})
    parts.sort(key=lambda part: part["cost_center_reference_id"])
    amount = (
        Decimal(received["amounts"][basis])
        if received["amounts"][basis] is not None
        else None
    )
    assigned = sum((Decimal(part["amount"]) for part in parts), Decimal(0))
    if parts and (amount is None or amount < 0 or assigned > amount):
        raise core.InvalidOperation(
            "Cost-center shares exceed or lack a nonnegative received basis."
        )
    after = {
        "component_id": component.id if component else None,
        "revision": before["revision"] + 1 if before else 1,
        "basis": basis,
        "basis_amount": _money(amount),
        "assigned": _money(assigned),
        "unassigned": _money(amount - assigned) if amount is not None else None,
        "currency": received["currency"],
        "case_reference_id": arguments.get("case_reference_id"),
        "group_reference_id": arguments.get("group_reference_id"),
        "parts": parts,
        "references": references,
        "reason": reason,
    }
    return {"received": received, "before": before, "after": after}


def assign_component(
    session: Session,
    tenant_id: str,
    *,
    arguments: dict,
    action_id: str,
    actor_id: str | None = None,
) -> dict:
    core._require_business_mutation(session, tenant_id, "finance_component_assign")
    review = preview_assignment(session, tenant_id, arguments)
    received = review["received"]
    after = review["after"]
    component = _component(
        session, tenant_id, received["document_id"], received["document_line_id"]
    )
    if component is None:
        component = FinancialComponent(
            id=uid("cmp"),
            tenant_id=tenant_id,
            document_id=None
            if received["document_line_id"]
            else received["document_id"],
            document_line_id=received["document_line_id"],
            currency=received["currency"],
            **{
                "stated_" + key: Decimal(value) if value is not None else None
                for key, value in received["amounts"].items()
            },
        )
        session.add(component)
        session.flush()
    row = ComponentAssignment(
        id=uid("asg"),
        tenant_id=tenant_id,
        component_id=component.id,
        revision=after["revision"],
        basis=after["basis"],
        case_reference_id=after["case_reference_id"],
        group_reference_id=after["group_reference_id"],
        reason=after["reason"],
        reference_snapshot=after["references"],
        actor_id=actor_id,
        action_id=action_id,
    )
    session.add(row)
    session.flush()
    for part in after["parts"]:
        session.add(
            ComponentAssignmentPart(
                id=uid("asp"),
                tenant_id=tenant_id,
                assignment_revision_id=row.id,
                cost_center_reference_id=part["cost_center_reference_id"],
                amount=Decimal(part["amount"]),
            )
        )
    session.flush()
    state = lock_finance(session, tenant_id)
    state.revision += 1
    result = _assignment(session, tenant_id, component, row)
    from reality.services.core import emit_business_event

    emit_business_event(
        session,
        tenant_id,
        "finance.component_assigned",
        "financial_component",
        component.id,
        {
            "before_revision_id": review["before"]["id"] if review["before"] else None,
            "after": result,
        },
        source_record_id=received["source_record_id"],
        action_id=action_id,
    )
    session.flush()
    return result
