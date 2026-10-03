"""Company dunning schedule, reviewed dunning runs and collection handover (spec 295).

The schedule is the company's stated rule; an item's level is never stored but
read from its non-reversed notices each time it is needed.
"""

import json
from collections import defaultdict
from datetime import UTC, date, datetime, time
from decimal import Decimal
from decimal import InvalidOperation as DecimalInvalid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    CollectionHandover,
    CollectionHandoverInvoice,
    Document,
    DunningNotice,
    DunningNoticeInvoice,
    DunningScheduleLevel,
    FinanceState,
    Party,
    SourceRecord,
    now,
    uid,
)
from reality.services import core
from reality.services.core import emit_business_event
from reality.services.dunning import SOURCE_SYSTEM, _record_notice, notice_detail
from reality.services.finance.accounts import lock_finance, resolve_account

LEVELS = (1, 2, 3)
FEE_SCALE = Decimal("0.0001")
# Bounds a stated value must stay within to be a schedule rather than a typo.
MAX_WAIT_DAYS = 3650
MAX_FEE = Decimal(1000000)
# The customer items a notice may remind (spec 247 `preview_notice`).
DUNNABLE_TYPES = ("sales_invoice", "opening_customer_debt")
RUN_ITEM_LIMIT = 500


def _finance_revision(session: Session, tenant_id: str) -> int:
    revision = session.scalar(
        select(FinanceState.revision).where(FinanceState.tenant_id == tenant_id)
    )
    return revision or 0


def schedule(session: Session, tenant_id: str) -> dict[str, Any]:
    """
    The company's dunning levels, empty when none is set, with the finance revision.

    BUSINESS PURPOSE:
    The company's dunning levels, empty when none is set, with the finance revision.

    BUSINESS RULE services.dunning_runs.schedule.result:
    Return the current result with revision, levels, source_record_id.
    """
    core.get_tenant(session, tenant_id)
    rows = list(
        session.scalars(
            select(DunningScheduleLevel)
            .where(DunningScheduleLevel.tenant_id == tenant_id)
            .order_by(DunningScheduleLevel.level)
        )
    )
    # reality-rule: services.dunning_runs.schedule.result
    return {
        "revision": _finance_revision(session, tenant_id),
        "levels": [
            {
                "level": row.level,
                "wait_days": row.wait_days,
                "fee_amount": str(Decimal(row.fee_amount).quantize(FEE_SCALE)),
            }
            for row in rows
        ],
        "source_record_id": rows[0].source_record_id if rows else None,
    }


def _stated_levels(session: Session, tenant_id: str, levels: Any) -> list[dict]:
    if not isinstance(levels, list) or sorted(
        entry.get("level") if isinstance(entry, dict) else None for entry in levels
    ) != list(LEVELS):
        raise core.InvalidOperation(code="dunning_schedule_incomplete")
    stated = []
    for entry in sorted(levels, key=lambda entry: entry["level"]):
        try:
            wait_days = int(entry["wait_days"])
            fee = Decimal(str(entry.get("fee_amount") or "0"))
        except (KeyError, TypeError, ValueError, DecimalInvalid) as error:
            raise core.InvalidOperation(
                code="dunning_schedule_value_invalid", values={"level": entry["level"]}
            ) from error
        if (
            str(entry["wait_days"]).strip() != str(wait_days)
            or not 0 <= wait_days <= MAX_WAIT_DAYS
            or not fee.is_finite()
            or not 0 <= fee <= MAX_FEE
            or fee.as_tuple().exponent < -4
        ):
            raise core.InvalidOperation(
                code="dunning_schedule_value_invalid", values={"level": entry["level"]}
            )
        stated.append(
            {"level": entry["level"], "wait_days": wait_days, "fee_amount": str(fee)}
        )
    if any(Decimal(entry["fee_amount"]) for entry in stated):
        # A fee is posted against this account; refuse now rather than at the run.
        resolve_account(session, tenant_id, "dunning_fee_revenue")
    return stated


def set_schedule(
    session: Session,
    tenant_id: str,
    *,
    levels: list[dict[str, Any]],
    expected_revision: int,
    action_id: str,
    actor_id: str | None,
) -> dict[str, Any]:
    """
    Replace the company's three dunning levels; callers own the outer transaction.

    BUSINESS PURPOSE:
    Replace the company's three dunning levels; callers own the outer transaction.

    BUSINESS RULE services.dunning_runs.set_schedule.step-10:
    Require the business permission for 'set_dunning_schedule' before changing company records.

    BUSINESS RULE services.dunning_runs.set_schedule.refusal-22:
    IF the current finance revision differs from the reviewed revision:
        Refuse with dunning_preview_stale.

    BUSINESS RULE services.dunning_runs.set_schedule.step-25:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.dunning_runs.set_schedule.step-55:
    Record the dunning.schedule_set audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.dunning_runs.set_schedule.result:
    Return the result from schedule; inspect that called function for its calculation and eligibility rules.
    """
    # reality-rule: services.dunning_runs.set_schedule.step-10
    core._require_business_mutation(session, tenant_id, "set_dunning_schedule")
    state = lock_finance(session, tenant_id)
    replay = session.scalar(
        select(SourceRecord.id).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == SOURCE_SYSTEM,
            SourceRecord.source_type == "dunning_schedule",
            SourceRecord.external_id == action_id,
        )
    )
    if replay:
        return schedule(session, tenant_id)
    # reality-rule: services.dunning_runs.set_schedule.refusal-22
    if state.revision != expected_revision:
        raise core.Conflict(code="dunning_preview_stale")
    stated = _stated_levels(session, tenant_id, levels)
    # reality-rule: services.dunning_runs.set_schedule.step-25
    source, _, _ = core.store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        "dunning_schedule",
        action_id,
        {"levels": stated, "actor_id": actor_id, "confirmation_id": action_id},
    )
    current = {
        row.level: row
        for row in session.scalars(
            select(DunningScheduleLevel).where(
                DunningScheduleLevel.tenant_id == tenant_id
            )
        )
    }
    for entry in stated:
        row = current.get(entry["level"])
        if row is None:
            row = DunningScheduleLevel(
                id=uid("dsl"), tenant_id=tenant_id, level=entry["level"]
            )
            session.add(row)
        row.wait_days = entry["wait_days"]
        row.fee_amount = Decimal(entry["fee_amount"])
        row.source_record_id = source.id
        row.updated_at = now()
    # The schedule decides levels and fees, so a prepared run is stale after it.
    state.revision += 1
    session.flush()
    # reality-rule: services.dunning_runs.set_schedule.step-55
    emit_business_event(
        session,
        tenant_id,
        "dunning.schedule_set",
        "tenant",
        tenant_id,
        {"levels": stated},
        source_record_id=source.id,
        action_id=action_id,
    )
    # reality-rule: services.dunning_runs.set_schedule.result
    return schedule(session, tenant_id)


# --- The derived dunning state of an invoice -------------------------------------


def invoice_dunning_state(
    session: Session, tenant_id: str, invoice_ids: set[str] | None = None
) -> dict[str, dict[str, Any]]:
    """
    Per invoice, its last non-reversed notice and any collection handover.

    The one reader behind the run, the handover and the invoice explanation, so
    all of them agree on an item's level. Three queries, whatever the count.

    BUSINESS PURPOSE:
    Per invoice, its last non-reversed notice and any collection handover.

    BUSINESS RULE services.dunning_runs.invoice_dunning_state.result:
    Return the result from dict; inspect that called function for its calculation and eligibility rules.
    """
    reversed_ids = select(BusinessEvent.subject_id).where(
        BusinessEvent.tenant_id == tenant_id,
        BusinessEvent.event_type == "dunning.notice_reversed",
        BusinessEvent.subject_type == "dunning_notice",
    )
    notices = (
        select(
            DunningNoticeInvoice.invoice_id,
            DunningNotice.id,
            DunningNotice.document_id,
            DunningNotice.level,
            DunningNotice.notice_date,
        )
        .join(
            DunningNotice,
            (DunningNotice.tenant_id == tenant_id)
            & (DunningNotice.id == DunningNoticeInvoice.notice_id),
        )
        .where(
            DunningNoticeInvoice.tenant_id == tenant_id,
            DunningNotice.id.not_in(reversed_ids),
        )
        .order_by(DunningNotice.notice_date, DunningNotice.created_at, DunningNotice.id)
    )
    handovers = select(
        CollectionHandoverInvoice.invoice_id, CollectionHandoverInvoice.handover_id
    ).where(CollectionHandoverInvoice.tenant_id == tenant_id)
    if invoice_ids is not None:
        notices = notices.where(DunningNoticeInvoice.invoice_id.in_(invoice_ids))
        handovers = handovers.where(
            CollectionHandoverInvoice.invoice_id.in_(invoice_ids)
        )
    state: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "last_notice_id": None,
            "last_notice_document_id": None,
            "level": None,
            "last_notice_date": None,
            "handover_id": None,
        }
    )
    for invoice_id, notice_id, document_id, level, day in session.execute(notices):
        # Ordered oldest first, so the last row per invoice is its current level.
        state[invoice_id].update(
            last_notice_id=notice_id,
            last_notice_document_id=document_id,
            level=level,
            last_notice_date=day,
        )
    for invoice_id, handover_id in session.execute(handovers):
        state[invoice_id]["handover_id"] = handover_id
    # reality-rule: services.dunning_runs.invoice_dunning_state.result
    return dict(state)


def _run_date(value: Any) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise core.InvalidOperation(code="dunning_run_date_invalid") from error


def _schedule_levels(session: Session, tenant_id: str) -> dict[int, Any]:
    levels = {
        row.level: row
        for row in session.scalars(
            select(DunningScheduleLevel).where(
                DunningScheduleLevel.tenant_id == tenant_id
            )
        )
    }
    if set(levels) != set(LEVELS):
        raise core.InvalidOperation(code="dunning_schedule_missing")
    return levels


def _customers(session: Session, tenant_id: str, party_ids: Any) -> set[str] | None:
    if not party_ids:
        return None
    if not isinstance(party_ids, list | tuple):
        raise core.InvalidOperation(code="dunning_run_parties_invalid")
    return {
        core._tenant_record(session, Party, tenant_id, str(party_id)).id
        for party_id in party_ids
    }


def _customers_with_credit(
    session: Session, tenant_id: str, party_ids: set[str]
) -> set[tuple[str, str]]:
    from reality.services.finance.credits import available_credit_rows

    if not party_ids:
        return set()
    rows, _ = available_credit_rows(
        session, tenant_id, side="customer", party_ids=party_ids
    )
    return {
        (row["party_id"], row["currency"]) for row in rows if Decimal(row["open"]) > 0
    }


def run_context(
    session: Session,
    tenant_id: str,
    *,
    run_date: Any,
    party_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Which overdue items a run on this date would remind, at which level, and why.

    Records nothing. Each item's level follows from its last non-reversed notice
    and the company schedule; items that cannot be reminded are named with a code.

    BUSINESS PURPOSE:
    Which overdue items a run on this date would remind, at which level, and why.

    BUSINESS RULE services.dunning_runs.run_context.result:
    Return the current result with revision, run_date, party_ids, schedule_source_record_id, notices, ready_for_collection, left_out.
    """
    core.get_tenant(session, tenant_id)
    day = _run_date(run_date)
    levels = _schedule_levels(session, tenant_id)
    customers = _customers(session, tenant_id, party_ids)
    as_of = datetime.combine(day, time.max, tzinfo=UTC)
    rows = [
        row
        for row in core.aging_register(
            session, tenant_id, as_of=as_of, party_ids=customers
        )
        if row["document"].type in DUNNABLE_TYPES
        and row["status"] in {"open", "partial"}
        and Decimal(row["open"]) > 0
        and (row.get("days_overdue") or 0) > 0
    ]
    state = invoice_dunning_state(
        session, tenant_id, {row["document"].id for row in rows}
    )
    credit = _customers_with_credit(
        session, tenant_id, {row["document"].party_id for row in rows}
    )
    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    ready: list[dict[str, Any]] = []
    left_out: list[dict[str, Any]] = []
    for row in sorted(
        rows, key=lambda row: (row["party"], row["document"].number, row["document"].id)
    ):
        document = row["document"]
        known = state.get(document.id, {})
        item = {
            "invoice_id": document.id,
            "number": document.number,
            "party_id": document.party_id,
            "party": row["party"],
            "currency": document.currency,
            "open": str(row["open"]),
            "due_date": row["due_date"].isoformat() if row["due_date"] else None,
            "days_overdue": row["days_overdue"],
            "previous_notice_id": known.get("last_notice_id"),
            "previous_level": known.get("level"),
            "previous_notice_date": known["last_notice_date"].isoformat()
            if known.get("last_notice_date")
            else None,
        }
        if known.get("handover_id"):
            left_out.append({**item, "code": "in_collection"})
            continue
        if (document.party_id, document.currency) in credit:
            left_out.append({**item, "code": "credit_available"})
            continue
        previous = known.get("level")
        if previous == LEVELS[-1]:
            ready.append({**item, "last_notice_id": known["last_notice_id"]})
            continue
        level = (previous or 0) + 1
        wait_days = levels[level].wait_days
        waited = (
            row["days_overdue"]
            if previous is None
            else (day - known["last_notice_date"]).days
        )
        if waited < wait_days:
            left_out.append(
                {
                    **item,
                    "code": "waiting",
                    "level": level,
                    "wait_days": wait_days,
                    "eligible_on": date.fromordinal(
                        day.toordinal() + wait_days - waited
                    ).isoformat(),
                }
            )
            continue
        groups[(document.party_id, document.currency, level)].append(
            {**item, "level": level, "wait_days": wait_days}
        )
    notices = [
        {
            "party_id": party_id,
            "party": items[0]["party"],
            "currency": currency,
            "level": level,
            "fee_amount": str(Decimal(levels[level].fee_amount).quantize(FEE_SCALE)),
            "items": items,
        }
        for (party_id, currency, level), items in groups.items()
    ]
    # reality-rule: services.dunning_runs.run_context.result
    return {
        "revision": _finance_revision(session, tenant_id),
        "run_date": day.isoformat(),
        "party_ids": sorted(customers) if customers else [],
        "schedule_source_record_id": levels[1].source_record_id,
        "notices": notices,
        "ready_for_collection": ready,
        "left_out": left_out,
    }


# --- Confirming a run --------------------------------------------------------------


def _run_items(session: Session, tenant_id: str, items: Any) -> dict[str, int]:
    if not isinstance(items, list) or not items or len(items) > RUN_ITEM_LIMIT:
        raise core.InvalidOperation(code="dunning_run_items_invalid")
    chosen: dict[str, int] = {}
    for entry in items:
        try:
            invoice_id, level = str(entry["invoice_id"]), int(entry["level"])
        except (KeyError, TypeError, ValueError) as error:
            raise core.InvalidOperation(code="dunning_run_items_invalid") from error
        chosen[invoice_id] = level
    types = dict(
        session.execute(
            select(Document.id, Document.type).where(
                Document.tenant_id == tenant_id, Document.id.in_(chosen)
            )
        ).all()
    )
    for invoice_id, level in chosen.items():
        if types.get(invoice_id) not in DUNNABLE_TYPES or level not in LEVELS:
            raise core.InvalidOperation(
                code="dunning_run_item_unknown", values={"invoice_id": invoice_id}
            )
    return chosen


def run_outcome(
    session: Session, tenant_id: str, context: dict[str, Any], chosen: dict[str, int]
) -> tuple[dict[int, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Which chosen items a run records, per notice, and which it skips and why.

    The one rule behind the proposal's review and the confirmation, so what a
    person approves is what is recorded.
    """
    due = {
        item["invoice_id"]: (index, item)
        for index, notice in enumerate(context["notices"])
        for item in notice["items"]
    }
    left_out = {item["invoice_id"]: item["code"] for item in context["left_out"]}
    ready = {item["invoice_id"] for item in context["ready_for_collection"]}
    missing = [
        invoice_id
        for invoice_id in chosen
        if invoice_id not in due
        and invoice_id not in left_out
        and invoice_id not in ready
    ]
    still_open = set()
    if missing:
        documents = list(
            session.scalars(
                select(Document).where(
                    Document.tenant_id == tenant_id, Document.id.in_(missing)
                )
            )
        )
        still_open = {
            invoice_id
            for invoice_id, amount in core.open_invoice_amounts(
                session, tenant_id, documents
            ).items()
            if amount > 0
        }
    numbers = dict(
        session.execute(
            select(Document.id, Document.number).where(
                Document.tenant_id == tenant_id, Document.id.in_(chosen)
            )
        ).all()
    )
    selected: dict[int, list[dict[str, Any]]] = defaultdict(list)
    skipped = []
    for invoice_id, level in chosen.items():
        if invoice_id in due and due[invoice_id][1]["level"] == level:
            selected[due[invoice_id][0]].append(due[invoice_id][1])
            continue
        code = left_out.get(invoice_id)
        if code not in {"in_collection", "credit_available"}:
            if invoice_id in due or invoice_id in ready or code == "waiting":
                code = "level_changed"
            elif invoice_id in still_open:
                # Open but no longer overdue, or outside the run's customers.
                code = "not_due"
            else:
                code = "paid"
        skipped.append(
            {
                "invoice_id": invoice_id,
                "number": numbers.get(invoice_id),
                "level": level,
                "code": code,
            }
        )
    return dict(selected), skipped


def _run_receipt(
    session: Session, tenant_id: str, run_source_id: str
) -> dict[str, Any]:
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.event_type == "dunning.run_confirmed",
            BusinessEvent.source_record_id == run_source_id,
        )
    )
    payload = (
        json.loads(event.payload) if isinstance(event.payload, str) else event.payload
    )
    return {
        "run_source_record_id": run_source_id,
        "run_date": payload["run_date"],
        "notices": [
            notice_detail(session, tenant_id, notice_id)
            for notice_id in payload["notice_ids"]
        ],
        "skipped": payload["skipped"],
    }


def _notice_values(
    session: Session,
    tenant_id: str,
    notice: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    run_date: str,
    number: str,
    revenue_account_id: str | None,
) -> dict[str, Any]:
    """The same values `preview_notice` returns, from an already derived run."""
    fee = Decimal(notice["fee_amount"])
    invoice_ids = [item["invoice_id"] for item in items]
    accounts = None
    if fee:
        receivable = core._settlement_control_entry(session, tenant_id, invoice_ids[0])
        accounts = {
            "accounts_receivable": receivable.account_id,
            "dunning_fee_revenue": revenue_account_id,
        }
    return {
        "invoice_ids": invoice_ids,
        "party_id": notice["party_id"],
        "currency": notice["currency"],
        "notice_date": run_date,
        "level": notice["level"],
        "fee_amount": str(fee),
        "reason": f"Dunning run {run_date}",
        "number": number,
        "accounts": accounts,
        "invoice_open": {item["invoice_id"]: item["open"] for item in items},
    }


def confirm_run(
    session: Session,
    tenant_id: str,
    *,
    run_date: str,
    items: list[dict[str, Any]],
    schedule_source_record_id: str,
    action_id: str,
    actor_id: str | None,
    party_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Record the reviewed notices still due at their reviewed level, name the rest.

    Re-derives the run for the same date and customers under the finance lock, so
    an item paid, reminded or handed over since the review is skipped with a code
    instead of reminded twice or wrongly. Only a changed schedule makes the review
    stale, because it changes the fees the person approved. Callers own the outer
    transaction.

    BUSINESS PURPOSE:
    Record the reviewed notices still due at their reviewed level, name the rest.

    BUSINESS RULE services.dunning_runs.confirm_run.step-19:
    Require the business permission for 'record_dunning_run' before changing company records.

    BUSINESS RULE services.dunning_runs.confirm_run.refusal-33:
    IF the current schedule source record differs from the schedule source that was reviewed:
        Refuse with dunning_preview_stale.

    BUSINESS RULE services.dunning_runs.confirm_run.step-36:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.dunning_runs.confirm_run.step-80:
    Record the dunning.run_confirmed audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.dunning_runs.confirm_run.result:
    Return the recorded dunning-run receipt and its affected invoice identities from the shared run receipt reader.
    """
    # reality-rule: services.dunning_runs.confirm_run.step-19
    core._require_business_mutation(session, tenant_id, "record_dunning_run")
    lock_finance(session, tenant_id)
    replay = session.scalar(
        select(SourceRecord.id).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == SOURCE_SYSTEM,
            SourceRecord.source_type == "dunning_run",
            SourceRecord.external_id == action_id,
        )
    )
    if replay:
        return _run_receipt(session, tenant_id, replay)
    chosen = _run_items(session, tenant_id, items)
    context = run_context(session, tenant_id, run_date=run_date, party_ids=party_ids)
    # reality-rule: services.dunning_runs.confirm_run.refusal-33
    if context["schedule_source_record_id"] != schedule_source_record_id:
        raise core.Conflict(code="dunning_preview_stale")
    selected, skipped = run_outcome(session, tenant_id, context, chosen)
    # reality-rule: services.dunning_runs.confirm_run.step-36
    run_source, _, _ = core.store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        "dunning_run",
        action_id,
        {
            "run_date": context["run_date"],
            "party_ids": context["party_ids"],
            "items": [
                {"invoice_id": invoice_id, "level": level}
                for invoice_id, level in chosen.items()
            ],
            "actor_id": actor_id,
            "confirmation_id": action_id,
        },
    )
    revenue = (
        resolve_account(session, tenant_id, "dunning_fee_revenue").id
        if any(Decimal(context["notices"][index]["fee_amount"]) for index in selected)
        else None
    )
    notice_ids = []
    for position, index in enumerate(sorted(selected), start=1):
        notice = context["notices"][index]
        values = _notice_values(
            session,
            tenant_id,
            notice,
            selected[index],
            run_date=context["run_date"],
            number=f"DN-{action_id[-6:].upper()}-{position}",
            revenue_account_id=revenue,
        )
        recorded = _record_notice(
            session,
            tenant_id,
            values=values,
            source_key=f"{action_id}:{position}",
            action_id=action_id,
            actor_id=actor_id,
            context={"dunning_run_source_record_id": run_source.id},
        )
        notice_ids.append(recorded["id"])
    # reality-rule: services.dunning_runs.confirm_run.step-80
    emit_business_event(
        session,
        tenant_id,
        "dunning.run_confirmed",
        "source_record",
        run_source.id,
        {
            "run_date": context["run_date"],
            "notice_ids": notice_ids,
            "skipped": skipped,
        },
        source_record_id=run_source.id,
        action_id=action_id,
    )
    session.flush()
    # reality-rule: services.dunning_runs.confirm_run.result
    return _run_receipt(session, tenant_id, run_source.id)


# --- Collection handover -----------------------------------------------------------


def handover_detail(
    session: Session, tenant_id: str, handover_id: str
) -> dict[str, Any]:
    """
    BUSINESS PURPOSE:
    Read a recorded collections handover and its invoice evidence for this company.

    BUSINESS RULE services.dunning_runs.handover_detail.result:
    Return the current result with id, party_id, handover_date, reason, invoice_ids, last_notice_ids, hold_id, hold_placed, source_record_id, created_at.
    """
    handover = core._tenant_record(session, CollectionHandover, tenant_id, handover_id)
    invoice_ids = sorted(
        session.scalars(
            select(CollectionHandoverInvoice.invoice_id).where(
                CollectionHandoverInvoice.tenant_id == tenant_id,
                CollectionHandoverInvoice.handover_id == handover.id,
            )
        )
    )
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.event_type == "dunning.collection_handover_recorded",
            BusinessEvent.subject_type == "collection_handover",
            BusinessEvent.subject_id == handover.id,
        )
    )
    payload = (
        (json.loads(event.payload) if isinstance(event.payload, str) else event.payload)
        if event
        else {}
    )
    # reality-rule: services.dunning_runs.handover_detail.result
    return {
        "id": handover.id,
        "party_id": handover.party_id,
        "handover_date": handover.handover_date.isoformat(),
        "reason": handover.reason,
        "invoice_ids": invoice_ids,
        "last_notice_ids": payload.get("last_notice_ids", {}),
        "hold_id": payload.get("hold_id"),
        "hold_placed": payload.get("hold_placed", False),
        "source_record_id": handover.source_record_id,
        "created_at": handover.created_at.isoformat(),
    }


def handovers(session: Session, tenant_id: str) -> list[dict[str, Any]]:
    """
    Collection handovers newest first with their invoices and delivery hold.

    BUSINESS PURPOSE:
    Collection handovers newest first with their invoices and delivery hold.

    BUSINESS RULE services.dunning_runs.handovers.result:
    Return the selected records in the displayed response structure; preserve the source identifiers and stated values used by this comprehension.
    """
    core.get_tenant(session, tenant_id)
    # reality-rule: services.dunning_runs.handovers.result
    return [
        handover_detail(session, tenant_id, handover_id)
        for handover_id in session.scalars(
            select(CollectionHandover.id)
            .where(CollectionHandover.tenant_id == tenant_id)
            .order_by(
                CollectionHandover.handover_date.desc(),
                CollectionHandover.created_at.desc(),
                CollectionHandover.id,
            )
        )
    ]


def _handover_invoices(
    session: Session, tenant_id: str, invoice_ids: Any
) -> tuple[list[Document], dict[str, dict[str, Any]]]:
    ids = list(dict.fromkeys(str(invoice_id) for invoice_id in invoice_ids or []))
    if not ids:
        raise core.InvalidOperation(code="collection_invoices_missing")
    invoices = [core._tenant_record(session, Document, tenant_id, id_) for id_ in ids]
    if len({invoice.party_id for invoice in invoices}) != 1:
        raise core.InvalidOperation(code="collection_mixed_customers")
    state = invoice_dunning_state(session, tenant_id, set(ids))
    for invoice in invoices:
        known = state.get(invoice.id, {})
        if known.get("handover_id"):
            raise core.InvalidOperation(
                code="collection_already_handed_over",
                values={"number": invoice.number},
            )
        if invoice.type not in DUNNABLE_TYPES or known.get("level") != LEVELS[-1]:
            raise core.InvalidOperation(
                code="collection_level_missing", values={"number": invoice.number}
            )
    open_ids = {
        row["document"].id
        for row in core.aging_register(session, tenant_id, document_ids=set(ids))
        if row["status"] in {"open", "partial"} and Decimal(row["open"]) > 0
    }
    for invoice in invoices:
        if invoice.id not in open_ids:
            raise core.InvalidOperation(
                code="collection_invoice_not_open", values={"number": invoice.number}
            )
    return invoices, state


def preview_handover(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Validate a handover and name what it would do, recording nothing.

    BUSINESS PURPOSE:
    Validate a handover and name what it would do, recording nothing.

    BUSINESS RULE services.dunning_runs.preview_handover.refusal-5:
    IF the collection handover reason is empty after trimming whitespace:
        Refuse with collection_reason_missing.

    BUSINESS RULE services.dunning_runs.preview_handover.result:
    Return the current result with party_id, invoice_ids, last_notice_ids, delivery_hold.
    """
    reason = str(arguments.get("reason") or "").strip()
    # reality-rule: services.dunning_runs.preview_handover.refusal-5
    if not reason:
        raise core.InvalidOperation(code="collection_reason_missing")
    _run_date(arguments.get("handover_date"))
    invoices, state = _handover_invoices(
        session, tenant_id, arguments.get("invoice_ids")
    )
    existing = core.active_party_delivery_hold(session, tenant_id, invoices[0].party_id)
    # reality-rule: services.dunning_runs.preview_handover.result
    return {
        "party_id": invoices[0].party_id,
        "invoice_ids": [invoice.id for invoice in invoices],
        "last_notice_ids": {
            invoice.id: state[invoice.id]["last_notice_id"] for invoice in invoices
        },
        "delivery_hold": "kept" if existing else "placed",
    }


def record_handover(
    session: Session,
    tenant_id: str,
    *,
    invoice_ids: list[str],
    handover_date: str,
    reason: str,
    expected_revision: int,
    action_id: str,
    actor_id: str | None,
) -> dict[str, Any]:
    """
    Hand dunned invoices to collection and hold the customer's deliveries.

    One transaction: the handover, its invoice links and the delivery hold with
    the reason `collection` (an already active hold is kept). Callers own the
    outer transaction.

    BUSINESS PURPOSE:
    Hand dunned invoices to collection and hold the customer's deliveries.

    BUSINESS RULE services.dunning_runs.record_handover.step-17:
    Require the business permission for 'record_collection_handover' before changing company records.

    BUSINESS RULE services.dunning_runs.record_handover.refusal-35:
    IF the current finance revision differs from the reviewed revision:
        Refuse with dunning_preview_stale.

    BUSINESS RULE services.dunning_runs.record_handover.step-37:
    Run the shared preview handover check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.dunning_runs.record_handover.step-42:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.dunning_runs.record_handover.step-86:
    Record the dunning.collection_handover_recorded audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.dunning_runs.record_handover.result:
    Return the result from handover detail; inspect that called function for its calculation and eligibility rules.
    """
    # reality-rule: services.dunning_runs.record_handover.step-17
    core._require_business_mutation(session, tenant_id, "record_collection_handover")
    state = lock_finance(session, tenant_id)
    replay = session.scalar(
        select(CollectionHandover.id).where(
            CollectionHandover.tenant_id == tenant_id,
            CollectionHandover.source_record_id
            == select(SourceRecord.id)
            .where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == SOURCE_SYSTEM,
                SourceRecord.source_type == "collection_handover",
                SourceRecord.external_id == action_id,
            )
            .scalar_subquery(),
        )
    )
    if replay:
        return handover_detail(session, tenant_id, replay)
    # reality-rule: services.dunning_runs.record_handover.refusal-35
    if state.revision != expected_revision:
        raise core.Conflict(code="dunning_preview_stale")
    # reality-rule: services.dunning_runs.record_handover.step-37
    preview = preview_handover(
        session,
        tenant_id,
        {"invoice_ids": invoice_ids, "handover_date": handover_date, "reason": reason},
    )
    # reality-rule: services.dunning_runs.record_handover.step-42
    source, _, _ = core.store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        "collection_handover",
        action_id,
        {
            **preview,
            "handover_date": _run_date(handover_date).isoformat(),
            "reason": reason.strip(),
            "actor_id": actor_id,
            "confirmation_id": action_id,
        },
    )
    handover = CollectionHandover(
        id=uid("col"),
        tenant_id=tenant_id,
        party_id=preview["party_id"],
        handover_date=_run_date(handover_date),
        reason=reason.strip(),
        source_record_id=source.id,
    )
    session.add(handover)
    session.flush()
    session.add_all(
        CollectionHandoverInvoice(
            id=uid("chi"),
            tenant_id=tenant_id,
            handover_id=handover.id,
            invoice_id=invoice_id,
        )
        for invoice_id in preview["invoice_ids"]
    )
    existing = core.active_party_delivery_hold(session, tenant_id, handover.party_id)
    hold = existing or core.hold_party_delivery(
        session,
        tenant_id,
        handover.party_id,
        "collection",
        reason.strip(),
        created_by=actor_id or "human",
        action_id=action_id,
        _commit=False,
    )
    # reality-rule: services.dunning_runs.record_handover.step-86
    emit_business_event(
        session,
        tenant_id,
        "dunning.collection_handover_recorded",
        "collection_handover",
        handover.id,
        {
            "invoice_ids": preview["invoice_ids"],
            "last_notice_ids": preview["last_notice_ids"],
            "reason": reason.strip(),
            "hold_id": hold.id,
            "hold_placed": existing is None,
        },
        source_record_id=source.id,
        action_id=action_id,
    )
    session.flush()
    # reality-rule: services.dunning_runs.record_handover.result
    return handover_detail(session, tenant_id, handover.id)


def invoice_dunning_rows(
    session: Session, tenant_id: str, invoice: Document
) -> list[dict[str, Any]]:
    """What an invoice's explanation says about its dunning: level, notice, handover."""
    if invoice.type not in DUNNABLE_TYPES:
        return []
    known = invoice_dunning_state(session, tenant_id, {invoice.id}).get(invoice.id)
    if not known:
        return []
    rows = []
    if known["last_notice_id"]:
        rows.append(
            {
                "label": "Dunning level",
                "value": known["level"],
                "kind": "document",
                "record_id": known["last_notice_document_id"],
                "meta": known["last_notice_date"].isoformat(),
            }
        )
    if known["handover_id"]:
        handover = core._tenant_record(
            session, CollectionHandover, tenant_id, known["handover_id"]
        )
        rows.append(
            {
                "label": "Collection",
                "value": f"{handover.handover_date.isoformat()} · {handover.reason}",
                "kind": "source_record",
                "record_id": handover.source_record_id,
            }
        )
    return rows
