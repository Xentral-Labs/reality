"""The company time zone: the zone the company's business days are counted in (spec 349).

Instants are stored in UTC. Wherever Reality turns an instant into a calendar day —
a document dated by its posting, a due date that has passed, a day filter on a
register — the day is the company's local day. A company that states no zone keeps
UTC days, which is how every day was counted before this specification, so nothing
an existing company sees moves until it states its zone.

A statement is reviewed and kept as a version of one source stream per company
(spec 320 pattern); the row names the version in force. Restating is allowed at any
time: days already stored on documents stay as they were stated, and only days
derived at read time follow the new zone.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, tzinfo
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import CompanyTimeZone, now, uid
from reality.domain.calendar import business_day

DEFAULT_TIME_ZONE = "UTC"
SOURCE_SYSTEM = "internal_company_time_zone"
SOURCE_TYPE = "company_time_zone"
COMPANY_TIME_ZONE_TOOLS = {"company_time_zone_set"}
# A review that saw nothing, distinct from a call that checks nothing.
UNCHECKED: Any = object()
_MEMO_KEY = "company_time_zone"


def _row(session: Session, tenant_id: str) -> CompanyTimeZone | None:
    return session.scalar(
        select(CompanyTimeZone).where(CompanyTimeZone.tenant_id == tenant_id)
    )


def _memo(session: Session) -> dict[str, str]:
    return session.info.setdefault(_MEMO_KEY, {})


def _zone_name(session: Session, tenant_id: str) -> str:
    memo = _memo(session)
    if tenant_id not in memo:
        row = _row(session, tenant_id)
        memo[tenant_id] = row.time_zone if row else DEFAULT_TIME_ZONE
    return memo[tenant_id]


def company_zone(session: Session, tenant_id: str) -> tzinfo:
    """
    The zone this company counts its business days in.

    BUSINESS PURPOSE:
    Tell every day computation which local calendar the company lives in.

    BUSINESS RULE company_time_zone.zone:
    IF the company stated a time zone, use it. ELSE use UTC, the way days were
    counted before the company stated one.
    """
    name = _zone_name(session, tenant_id)
    # reality-rule: company_time_zone.zone
    return UTC if name == DEFAULT_TIME_ZONE else ZoneInfo(name)


def company_day(
    session: Session, tenant_id: str, instant: date | datetime | str
) -> date:
    """
    The company's business day for one instant.

    BUSINESS PURPOSE:
    Date a moment the way the company lives it: an order at 23:30 Berlin time on
    31 October belongs to October.

    BUSINESS RULE company_time_zone.day:
    Keep a stated day; convert an instant to the company's zone and take that
    local day (see calendar.business_day).
    """
    # reality-rule: company_time_zone.day
    return business_day(instant, company_zone(session, tenant_id))


def company_today(
    session: Session, tenant_id: str, as_of: datetime | None = None
) -> date:
    """
    The company's business day now, or at a stated moment.

    BUSINESS PURPOSE:
    Decide what "today" is for due dates, overdue days and expiry in the
    company's own calendar.

    BUSINESS RULE company_time_zone.today:
    Take the stated moment, or now when none is stated, and return its business day
    in the company's zone.
    """
    from reality.services.core import now as current

    # reality-rule: company_time_zone.today
    return company_day(session, tenant_id, as_of or current())


def company_time_zone_state(session: Session, tenant_id: str) -> dict[str, Any]:
    """
    What a read shows and a review compares.

    BUSINESS PURPOSE:
    Show which time zone the company's business days are counted in and which
    statement says so.

    BUSINESS RULE company_time_zone.state:
    Return the stated zone, or UTC with stated false when the company stated none,
    and the statement in force.
    """
    row = _row(session, tenant_id)
    # reality-rule: company_time_zone.state
    return {
        "time_zone": row.time_zone if row else DEFAULT_TIME_ZONE,
        "stated": row is not None,
        "source_record_id": row.source_record_id if row else None,
    }


def _validate(time_zone: str) -> str:
    from reality.services.core import InvalidOperation

    stated = str(time_zone or "").strip()
    if stated == DEFAULT_TIME_ZONE:
        return stated
    if stated not in available_timezones():
        raise InvalidOperation(code="company_time_zone_invalid")
    try:
        ZoneInfo(stated)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise InvalidOperation(code="company_time_zone_invalid") from error
    return stated


def set_company_time_zone(
    session: Session,
    tenant_id: str,
    time_zone: str,
    *,
    action_id: str | None = None,
    _expected: Any = UNCHECKED,
    _commit: bool = True,
) -> dict[str, Any]:
    """
    State the company time zone.

    BUSINESS PURPOSE:
    Record the time zone a person states for the company, so business days follow
    the company's own calendar from now on.

    BUSINESS RULE company_time_zone.set.permission:
    Require the business permission for 'set_company_time_zone' before changing
    company records.

    BUSINESS RULE company_time_zone.set.invalid:
    IF the stated zone is neither UTC nor a known IANA zone name:
        Refuse with company_time_zone_invalid.

    BUSINESS RULE company_time_zone.set.changed:
    IF a review saw a zone and the stored zone differs from it now:
        Refuse with company_time_zone_changed_since_review.

    BUSINESS RULE company_time_zone.set.event:
    Record the company_time_zone.set event with the stated and the previous zone.
    """
    from reality.services.business_locks import lock_delivery_state
    from reality.services.core import (
        InvalidOperation,
        _require_business_mutation,
        emit_business_event,
        store_source_record,
    )

    # reality-rule: company_time_zone.set.permission
    _require_business_mutation(session, tenant_id, "set_company_time_zone")
    lock_delivery_state(session, tenant_id)
    # reality-rule: company_time_zone.set.invalid
    stated = _validate(time_zone)
    row = _row(session, tenant_id)
    # reality-rule: company_time_zone.set.changed
    if _expected is not UNCHECKED and (row.time_zone if row else None) != _expected:
        raise InvalidOperation(code="company_time_zone_changed_since_review")
    previous = row.time_zone if row else DEFAULT_TIME_ZONE
    source, _, _ = store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        SOURCE_TYPE,
        tenant_id,
        {"time_zone": stated, "statement_id": action_id or uid("stm")},
    )
    if row is None:
        row = CompanyTimeZone(
            tenant_id=tenant_id, time_zone=stated, source_record_id=source.id
        )
        session.add(row)
    elif row.source_record_id != source.id:
        row.time_zone = stated
        row.source_record_id = source.id
        row.updated_at = now()
    else:
        # The same confirmation again: it already stated this.
        return company_time_zone_state(session, tenant_id)
    session.flush()
    _memo(session)[tenant_id] = stated
    # reality-rule: company_time_zone.set.event
    emit_business_event(
        session,
        tenant_id,
        "company_time_zone.set",
        "company_time_zone",
        tenant_id,
        {"time_zone": stated, "previous": previous},
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return company_time_zone_state(session, tenant_id)


def review_company_time_zone(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    The arguments a confirmation executes and what the person is shown.

    BUSINESS PURPOSE:
    Show the current and the proposed zone before a person confirms.

    BUSINESS RULE company_time_zone.review:
    Validate the stated zone and return it with the zone the review saw, and the
    current and proposed zones for display.
    """
    stated = _validate(str(arguments.get("time_zone") or ""))
    row = _row(session, tenant_id)
    current = row.time_zone if row else None
    # reality-rule: company_time_zone.review
    return (
        {"time_zone": stated, "reviewed": current},
        {"current": current or DEFAULT_TIME_ZONE, "proposed": stated},
    )
