"""Tenant-owned reference catalog and append-only decisions for later attribution."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, FinanceState, uid
from reality.db.finance_references import FinanceReference
from reality.domain.finance import REFERENCE_KINDS
from reality.services.finance.accounts import lock_finance


def _result(row: FinanceReference) -> dict[str, Any]:
    return {
        key: getattr(row, key)
        for key in ("id", "kind", "code", "name", "state", "revision")
    }


def _get(session: Session, tenant_id: str, reference_id: str) -> FinanceReference:
    from reality.services.core import NotFound

    row = session.scalar(
        select(FinanceReference)
        .where(
            FinanceReference.tenant_id == tenant_id, FinanceReference.id == reference_id
        )
        .execution_options(populate_existing=True)
    )
    if row is None:
        raise NotFound("Finance reference not found.")
    return row


def _page(limit: int, offset: int) -> None:
    from reality.services.core import InvalidOperation

    if (
        not isinstance(limit, int)
        or not isinstance(offset, int)
        or not 1 <= limit <= 200
        or offset < 0
    ):
        raise InvalidOperation(
            "Reference page requires limit 1–200 and nonnegative offset."
        )


def _revision(session: Session, tenant_id: str) -> int:
    return (
        session.scalar(
            select(FinanceState.revision).where(FinanceState.tenant_id == tenant_id)
        )
        or 0
    )


def list_references(
    session: Session,
    tenant_id: str,
    *,
    kind: str | None = None,
    state: str | None = None,
    query: str = "",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    from reality.services.core import InvalidOperation, get_tenant

    get_tenant(session, tenant_id)
    _page(limit, offset)
    if (
        kind is not None
        and kind not in REFERENCE_KINDS
        or state is not None
        and state not in ("active", "blocked")
    ):
        raise InvalidOperation("Unsupported reference kind or state.")
    clauses = [FinanceReference.tenant_id == tenant_id]
    if kind is not None:
        clauses.append(FinanceReference.kind == kind)
    if state is not None:
        clauses.append(FinanceReference.state == state)
    if query.strip():
        clauses.append(
            or_(
                FinanceReference.code.icontains(query.strip(), autoescape=True),
                FinanceReference.name.icontains(query.strip(), autoescape=True),
            )
        )
    return {
        "revision": _revision(session, tenant_id),
        "total": session.scalar(
            select(func.count()).select_from(FinanceReference).where(*clauses)
        ),
        "limit": limit,
        "offset": offset,
        "items": [
            _result(row)
            for row in session.scalars(
                select(FinanceReference)
                .where(*clauses)
                .order_by(
                    FinanceReference.code, FinanceReference.kind, FinanceReference.id
                )
                .limit(limit)
                .offset(offset)
            )
        ],
    }


def reference_history(
    session: Session,
    tenant_id: str,
    reference_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    _page(limit, offset)
    row = _get(session, tenant_id, reference_id)
    clauses = [
        BusinessEvent.tenant_id == tenant_id,
        BusinessEvent.subject_type == "finance_reference",
        BusinessEvent.subject_id == row.id,
        BusinessEvent.event_type == "finance.reference_changed",
    ]
    return {
        "reference": _result(row),
        "total": session.scalar(
            select(func.count()).select_from(BusinessEvent).where(*clauses)
        ),
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "event_id": event.id,
                "action_id": event.action_id,
                "occurred_at": event.occurred_at.isoformat(),
                **json.loads(event.payload),
            }
            for event in session.scalars(
                select(BusinessEvent)
                .where(*clauses)
                .order_by(BusinessEvent.sequence.desc())
                .limit(limit)
                .offset(offset)
            )
        ],
    }


def resolve_reference(
    session: Session, tenant_id: str, reference_id: str, kind: str
) -> FinanceReference:
    from reality.services.core import InvalidOperation

    row = _get(session, tenant_id, reference_id)
    if kind not in REFERENCE_KINDS or row.kind != kind or row.state != "active":
        raise InvalidOperation("Reference is blocked or has the wrong kind.")
    return row


def preview_reference(session: Session, tenant_id: str, arguments: dict) -> dict:
    from reality.services.core import Conflict, InvalidOperation, get_tenant

    get_tenant(session, tenant_id)
    # Serialize the before snapshot and revision with configuration changes.
    lock_finance(session, tenant_id)
    existing = (
        _get(session, tenant_id, arguments["reference_id"])
        if "reference_id" in arguments
        else None
    )
    before = _result(existing) if existing else None
    if arguments["expected_revision"] != _revision(session, tenant_id):
        raise Conflict("Finance preview is stale; reload and confirm again.")
    reason = arguments["reason"].strip()
    name = arguments["name"].strip()
    if not reason or len(reason) > 4000 or not name or len(name) > 200:
        raise InvalidOperation(
            "A reference name and change reason are required within their length limits."
        )
    if existing:
        if arguments["state"] not in ("active", "blocked"):
            raise InvalidOperation("Reference state must be active or blocked.")
        after = {
            **before,
            "name": name,
            "state": arguments["state"],
            "revision": existing.revision + 1,
        }
        if name == existing.name and arguments["state"] == existing.state:
            raise InvalidOperation("Reference change has no effect.")
    else:
        code, kind = arguments["code"].strip(), arguments["kind"]
        if kind not in REFERENCE_KINDS or not code or len(code) > 100:
            raise InvalidOperation(
                "A supported reference kind and nonempty code are required."
            )
        if session.scalar(
            select(FinanceReference.id).where(
                FinanceReference.tenant_id == tenant_id,
                FinanceReference.kind == kind,
                FinanceReference.code == code,
            )
        ):
            raise Conflict("Reference code already exists for this kind.")
        after = {
            "kind": kind,
            "code": code,
            "name": name,
            "state": "active",
            "revision": 1,
        }
    return {"before": before, "after": after, "reason": reason}


def maintain_reference(
    session: Session,
    tenant_id: str,
    *,
    arguments: dict,
    action_id: str,
    actor_id: str | None = None,
) -> dict:
    from reality.services.core import _require_business_mutation, emit_business_event

    _require_business_mutation(session, tenant_id, "finance_reference_maintain")
    coordinator = lock_finance(session, tenant_id)
    review = preview_reference(session, tenant_id, arguments)
    if review["before"]:
        row = _get(session, tenant_id, arguments["reference_id"])
        row.name, row.state, row.revision = (
            review["after"][key] for key in ("name", "state", "revision")
        )
    else:
        row = FinanceReference(id=uid("fref"), tenant_id=tenant_id, **review["after"])
        session.add(row)
    session.flush()
    review["after"] = _result(row)
    coordinator.revision += 1
    emit_business_event(
        session,
        tenant_id,
        "finance.reference_changed",
        "finance_reference",
        row.id,
        {**review, "actor_id": actor_id},
        action_id=action_id,
    )
    session.flush()
    return _result(row)
