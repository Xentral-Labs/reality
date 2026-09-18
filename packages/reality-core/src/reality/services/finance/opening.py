"""Confirmed residual positions with explicit source coverage and no cash effect."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, union
from sqlalchemy.orm import Session

from reality.db.core import (
    Document,
    LedgerEntry,
    LedgerReversal,
    Party,
    PartyRole,
    SourceRecord,
)
from reality.db.opening import OpeningItem, OpeningScope
from reality.domain.finance import OPENING_DIRECTIONS
from reality.services import core
from reality.services.business_locks import lock_delivery_state
from reality.services.finance.accounts import (
    list_accounts,
    lock_finance,
    resolve_account,
)
from reality.services.finance.settlement_flows import _amount

SOURCE_SYSTEM = "internal_opening_subledger"
NORMAL_KINDS = {
    "sales_invoice": "customer",
    "credit_note": "customer",
    "customer_payment": "customer",
    "customer_refund": "customer",
    "supplier_invoice": "supplier",
    "supplier_credit_note": "supplier",
    "supplier_payment": "supplier",
    "supplier_refund": "supplier",
}


def _day(value: str | None, name: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError) as error:
        raise core.InvalidOperation(f"Enter a valid {name} date.") from error


def opening_context(
    session: Session, tenant_id: str, query: str = ""
) -> dict[str, Any]:
    accounts = list_accounts(session, tenant_id)
    statement = select(Party).where(
        Party.tenant_id == tenant_id, Party.is_active.is_(True)
    )
    if query.strip():
        statement = statement.where(Party.name.ilike(f"%{query.strip()}%"))
    parties = list(session.scalars(statement.order_by(Party.name, Party.id).limit(101)))
    return {
        **accounts,
        "counterpart": next(
            (
                a
                for a in accounts["accounts"]
                if a["id"] == accounts["defaults"].get("opening_counterpart")
            ),
            None,
        ),
        "parties": [{"id": p.id, "name": p.name} for p in parties[:100]],
        "more_parties": len(parties) > 100,
    }


def _scopes(
    session: Session, tenant_id: str, party_id: str, currency: str, side: str
) -> list[OpeningScope]:
    return list(
        session.scalars(
            select(OpeningScope).where(
                OpeningScope.tenant_id == tenant_id,
                OpeningScope.party_id == party_id,
                OpeningScope.currency == currency,
                OpeningScope.direction.in_((f"{side}_debt", f"{side}_credit")),
            )
        )
    )


def _existing_financial_documents(
    session: Session, tenant_id: str, party_id: str, currency: str, side: str
) -> list[Document]:
    inverses = union(
        select(LedgerReversal.original_posting_group_id).where(
            LedgerReversal.tenant_id == tenant_id
        ),
        select(LedgerReversal.reversing_posting_group_id).where(
            LedgerReversal.tenant_id == tenant_id
        ),
    )
    return list(
        session.scalars(
            select(Document)
            .join(
                LedgerEntry,
                (LedgerEntry.tenant_id == tenant_id)
                & (LedgerEntry.document_id == Document.id),
            )
            .where(
                Document.tenant_id == tenant_id,
                Document.party_id == party_id,
                Document.currency == currency,
                Document.type.in_(
                    [kind for kind, value in NORMAL_KINDS.items() if value == side]
                ),
                LedgerEntry.posting_group_id.not_in(inverses),
            )
            .distinct()
        )
    )


def preview_opening(session: Session, tenant_id: str, values: dict) -> dict:
    context = opening_context(session, tenant_id)
    cutover = _day(values["cutover_date"], "cutover")
    if cutover is None or cutover > core.now().date():
        raise core.InvalidOperation(
            "Opening cutover must be a stated date no later than today."
        )
    prepared, totals, seen, summary_scopes = [], {}, set(), set()
    for item in values["items"]:
        party = core._tenant_record(session, Party, tenant_id, item["party_id"])
        direction, currency = item["direction"], item["currency"]
        if direction not in OPENING_DIRECTIONS:
            raise core.InvalidOperation("Unsupported opening direction.")
        side = direction.split("_")[0]
        roles = set(
            session.scalars(
                select(PartyRole.role).where(
                    PartyRole.tenant_id == tenant_id, PartyRole.party_id == party.id
                )
            )
        ) | {party.type}
        if not party.is_active or side not in roles:
            raise core.InvalidOperation(
                "Select an active party with the matching customer or supplier role."
            )
        amount = _amount(item["amount"])
        if item.get("original_total") is not None:
            _amount(item["original_total"])
        original_date = _day(item.get("original_document_date"), "original document")
        due = _day(item.get("due_date"), "original due")
        if original_date and original_date > cutover:
            raise core.InvalidOperation(
                "Original document date cannot be after the opening cutover."
            )
        if item.get("source_record_id"):
            core._tenant_record(
                session, SourceRecord, tenant_id, item["source_record_id"]
            )
        scope_key = (party.id, direction, currency)
        identity = (*scope_key, item["external_item_key"])
        if identity in seen:
            raise core.Conflict("Duplicate opening item identity within this batch.")
        seen.add(identity)
        if values["coverage_kind"] == "summary":
            if scope_key in summary_scopes:
                raise core.Conflict(
                    "A summary has one item per party, direction and currency."
                )
            summary_scopes.add(scope_key)
        scopes = _scopes(session, tenant_id, party.id, currency, side)
        same = next((scope for scope in scopes if scope.direction == direction), None)
        for scope in scopes:
            if (
                scope.source_namespace != values["source_namespace"]
                or scope.snapshot_key != values["snapshot_key"]
                or scope.cutover_date != cutover
            ):
                raise core.Conflict(
                    "Existing opening coverage has another source, snapshot or cutover; reconcile it first."
                )
        if same:
            if (
                same.coverage_kind != values["coverage_kind"]
                or same.coverage_kind == "summary"
            ):
                raise core.Conflict(
                    "Opening summary/detail coverage overlaps; reconcile it first."
                )
            if session.scalar(
                select(OpeningItem.id).where(
                    OpeningItem.tenant_id == tenant_id,
                    OpeningItem.scope_id == same.id,
                    OpeningItem.external_item_key == item["external_item_key"],
                )
            ):
                raise core.Conflict(
                    "This opening item identity has already been imported."
                )
        for existing in _existing_financial_documents(
            session, tenant_id, party.id, currency, side
        ):
            original = (
                core._tenant_record(
                    session, SourceRecord, tenant_id, existing.source_record_id
                )
                if existing.source_record_id
                else None
            )
            exact = (
                original
                and original.source_system == values["source_namespace"]
                and original.external_id == item["external_item_key"]
            )
            if existing.type.endswith(("_payment", "_refund")):
                actual = session.scalar(
                    select(func.min(LedgerEntry.effective_at)).where(
                        LedgerEntry.tenant_id == tenant_id,
                        LedgerEntry.document_id == existing.id,
                        LedgerEntry.account == "cash",
                    )
                )
                existing_day = core.utc_datetime(actual).date() if actual else None
            else:
                existing_day = existing.document_date
            if exact or existing_day is None or existing_day <= cutover:
                raise core.Conflict(
                    "Existing historical or undated financial evidence overlaps this opening; reconcile it first."
                )
        control = resolve_account(session, tenant_id, OPENING_DIRECTIONS[direction][0])
        prepared.append(
            {
                **item,
                "amount": str(amount),
                "party": party.name,
                "document_type": f"opening_{direction}",
                "scope_id": same.id if same else None,
                "control_account_id": control.id,
                "control_account_code": control.code,
                "due_date": due.isoformat() if due else None,
            }
        )
        totals[(direction, currency)] = (
            totals.get((direction, currency), Decimal(0)) + amount
        )
    if context["revision"] != values["expected_revision"]:
        raise core.Conflict("Finance preview is stale; reload and confirm again.")
    counterpart = resolve_account(session, tenant_id, "opening_counterpart")
    return {
        "source_namespace": values["source_namespace"],
        "snapshot_key": values["snapshot_key"],
        "cutover_date": cutover.isoformat(),
        "coverage_kind": values["coverage_kind"],
        "reason": values["reason"],
        "items": prepared,
        "totals": [
            {"direction": d, "currency": c, "amount": str(v)}
            for (d, c), v in sorted(totals.items())
        ],
        "counterpart_account_id": counterpart.id,
        "counterpart_account_code": counterpart.code,
        "cash_change": "0",
        "unknown_due_dates": sum(item["due_date"] is None for item in prepared),
    }


def import_opening(
    session: Session, tenant_id: str, *, action_id: str, actor_id: str | None, **values
) -> dict:
    """Called inside the owner-confirmed finance transaction; no independent commit."""
    lock_delivery_state(session, tenant_id)
    lock_finance(session, tenant_id)
    preview = preview_opening(session, tenant_id, values)
    scopes, results = {}, []
    with session.begin_nested():
        for item in preview["items"]:
            key = (item["party_id"], item["direction"], item["currency"])
            scope = scopes.get(key)
            if scope is None:
                scope = (
                    core._tenant_record(
                        session, OpeningScope, tenant_id, item["scope_id"]
                    )
                    if item["scope_id"]
                    else OpeningScope(
                        id=core.uid("ops"),
                        tenant_id=tenant_id,
                        source_namespace=values["source_namespace"],
                        snapshot_key=values["snapshot_key"],
                        cutover_date=date.fromisoformat(values["cutover_date"]),
                        coverage_kind=values["coverage_kind"],
                        party_id=item["party_id"],
                        direction=item["direction"],
                        currency=item["currency"],
                    )
                )
                session.add(scope)
                session.flush()
                scopes[key] = scope
            stated = next(
                row
                for row in values["items"]
                if (
                    row["party_id"],
                    row["direction"],
                    row["currency"],
                    row["external_item_key"],
                )
                == (*key, item["external_item_key"])
            )
            source, _, _ = core.store_source_record(
                session,
                tenant_id,
                SOURCE_SYSTEM,
                "opening_item",
                core.uid("origin"),
                {
                    "source_namespace": values["source_namespace"],
                    "snapshot_key": values["snapshot_key"],
                    "cutover_date": values["cutover_date"],
                    "coverage_kind": values["coverage_kind"],
                    "reason": values["reason"],
                    "item": stated,
                    "actor_id": actor_id,
                    "confirmation_id": action_id,
                    "confirmed_at": core.now().isoformat(),
                },
            )
            document = core.create_document(
                session,
                tenant_id,
                item["document_type"],
                item["reference"] or item["external_item_key"],
                item["party_id"],
                item["amount"],
                currency=item["currency"],
                document_date=item.get("original_document_date") or "",
                source_record_id=source.id,
                action_id=action_id,
                _commit=False,
            )
            detail = OpeningItem(
                id=core.uid("opi"),
                tenant_id=tenant_id,
                scope_id=scope.id,
                document_id=document.id,
                external_item_key=item["external_item_key"],
                original_due_date=_day(item["due_date"], "original due"),
            )
            session.add(detail)
            session.flush()
            role, sign = OPENING_DIRECTIONS[item["direction"]]
            entries = core.post_ledger(
                session,
                tenant_id,
                document.id,
                item["party_id"],
                [
                    (role, sign, item["amount"]),
                    (
                        "opening_counterpart",
                        "credit" if sign == "debit" else "debit",
                        item["amount"],
                    ),
                ],
                currency=item["currency"],
                account_ids={
                    role: item["control_account_id"],
                    "opening_counterpart": preview["counterpart_account_id"],
                },
                source_record_id=source.id,
                effective_at=datetime.combine(
                    scope.cutover_date, datetime.min.time(), tzinfo=UTC
                ),
                action_id=action_id,
                _commit=False,
            )
            results.append(
                {
                    "document_id": document.id,
                    "source_record_id": source.id,
                    "scope_id": scope.id,
                    "opening_item_id": detail.id,
                    "posting_group_id": entries[0].posting_group_id,
                    "direction": item["direction"],
                    "currency": item["currency"],
                    "amount": item["amount"],
                    "reference": document.number,
                }
            )
    return {**preview, "items": results}


def check_opening_coverage(
    session: Session, tenant_id: str, document: Document, effective_at: datetime | None
) -> None:
    """Hold historical normal posting for review once an opening scope covers it."""
    side = NORMAL_KINDS.get(document.type)
    core._tenant_record(session, Document, tenant_id, document.id)
    if not side:
        if document.type.startswith("opening_"):
            detail = session.scalar(
                select(OpeningItem.id).where(
                    OpeningItem.tenant_id == tenant_id,
                    OpeningItem.document_id == document.id,
                )
            )
            posted = session.scalar(
                select(LedgerEntry.id)
                .where(
                    LedgerEntry.tenant_id == tenant_id,
                    LedgerEntry.document_id == document.id,
                )
                .limit(1)
            )
            if not detail or posted:
                raise core.InvalidOperation(
                    "Opening evidence must be created once by the confirmed opening import."
                )
        return
    scopes = _scopes(session, tenant_id, document.party_id, document.currency, side)
    if not scopes:
        return
    source = (
        core._tenant_record(session, SourceRecord, tenant_id, document.source_record_id)
        if document.source_record_id
        else None
    )
    for scope in scopes:
        if (
            source
            and source.source_system == scope.source_namespace
            and session.scalar(
                select(OpeningItem.id).where(
                    OpeningItem.tenant_id == tenant_id,
                    OpeningItem.scope_id == scope.id,
                    OpeningItem.external_item_key == source.external_id,
                )
            )
        ):
            raise core.InvalidOperation(
                "Original source item is already represented by opening evidence; inspect it without posting again."
            )
    cash = document.type.endswith(("_payment", "_refund"))
    observed = (
        core.utc_datetime(effective_at).date() if effective_at is not None else None
    )
    if not cash:
        observed = document.document_date
    if observed is None:
        raise core.InvalidOperation(
            "Opening cutover coverage requires an explicit original date or actual cash timestamp."
        )
    if any(observed <= scope.cutover_date for scope in scopes):
        raise core.InvalidOperation(
            "Financial evidence is at or before the opening cutover; reconcile coverage before posting."
        )
