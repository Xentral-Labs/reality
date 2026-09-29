"""Company dunning schedule, reviewed dunning runs and collection handover (spec 295).

The schedule is the company's stated rule; an item's level is never stored but
read from its non-reversed notices each time it is needed.
"""

from decimal import Decimal
from decimal import InvalidOperation as DecimalInvalid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import DunningScheduleLevel, SourceRecord, now, uid
from reality.services import core
from reality.services.core import emit_business_event
from reality.services.dunning import SOURCE_SYSTEM
from reality.services.finance.accounts import lock_finance, resolve_account

LEVELS = (1, 2, 3)
FEE_SCALE = Decimal("0.0001")


def schedule(session: Session, tenant_id: str) -> dict[str, Any]:
    """The company's dunning levels, empty when none is set, with the finance revision."""
    from reality.services.finance.accounts import list_accounts

    core.get_tenant(session, tenant_id)
    rows = list(
        session.scalars(
            select(DunningScheduleLevel)
            .where(DunningScheduleLevel.tenant_id == tenant_id)
            .order_by(DunningScheduleLevel.level)
        )
    )
    return {
        "revision": list_accounts(session, tenant_id)["revision"],
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
            or wait_days < 0
            or not fee.is_finite()
            or fee < 0
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
    """Replace the company's three dunning levels; callers own the outer transaction."""
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
    if state.revision != expected_revision:
        raise core.Conflict(code="dunning_preview_stale")
    stated = _stated_levels(session, tenant_id, levels)
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
    return schedule(session, tenant_id)
