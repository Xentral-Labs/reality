"""The company currency: the currency the company keeps its books in (spec 309).

Every ledger entry carries its amount in the company currency beside its own, so
the company currency is read on every posting. It is EUR until the company states
another one, and it can be stated only before the company's first posting:
afterwards every company-currency amount already recorded would be in the old one. A
company whose postings all carry no company value yet (made in another currency
before spec 309) may state their currency, and they take their amount as value.

A statement is reviewed and kept as a version of one source stream per company
(spec 320 pattern); the row names the version in force.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import CompanyCurrency, LedgerEntry, now, uid

DEFAULT_CURRENCY = "EUR"
SOURCE_SYSTEM = "internal_company_currency"
SOURCE_TYPE = "company_currency"
# A review that saw nothing, distinct from a call that checks nothing.
UNCHECKED: Any = object()


def _row(session: Session, tenant_id: str) -> CompanyCurrency | None:
    return session.scalar(
        select(CompanyCurrency).where(CompanyCurrency.tenant_id == tenant_id)
    )


def company_currency(session: Session, tenant_id: str) -> str:
    """The company currency, EUR when none was stated."""
    from reality.services.core import _batch_memo

    memo = _batch_memo(session)
    if memo is not None and ("company_currency", tenant_id) in memo:
        # A batch does not state the company currency (spec 342).
        return memo[("company_currency", tenant_id)]
    row = _row(session, tenant_id)
    currency = row.currency if row else DEFAULT_CURRENCY
    if memo is not None:
        memo[("company_currency", tenant_id)] = currency
    return currency


def company_currency_state(session: Session, tenant_id: str) -> dict[str, Any]:
    """What a read shows and a review compares."""
    row = _row(session, tenant_id)
    return {
        "currency": row.currency if row else DEFAULT_CURRENCY,
        "source_record_id": row.source_record_id if row else None,
        "has_postings": _has_postings(session, tenant_id),
    }


def _has_postings(session: Session, tenant_id: str) -> bool:
    """Whether a posting already carries a company-currency value.

    A company whose postings all predate spec 309 in a currency other than EUR
    carries none yet, and may still state that currency.
    """
    return (
        session.scalar(
            select(LedgerEntry.id)
            .where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.company_amount.is_not(None),
            )
            .limit(1)
        )
        is not None
    )


def _validate(session: Session, tenant_id: str, currency: str) -> str:
    from reality.services.core import InvalidOperation

    stated = str(currency or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", stated):
        raise InvalidOperation(code="company_currency_invalid")
    if stated != company_currency(session, tenant_id) and _has_postings(
        session, tenant_id
    ):
        raise InvalidOperation(code="company_currency_has_postings")
    return stated


def set_company_currency(
    session: Session,
    tenant_id: str,
    currency: str,
    *,
    action_id: str | None = None,
    _expected: Any = UNCHECKED,
    _commit: bool = True,
) -> dict[str, Any]:
    """State the company currency; refused once the company has posted anything."""
    from reality.services.business_locks import lock_delivery_state
    from reality.services.core import (
        InvalidOperation,
        _require_business_mutation,
        emit_business_event,
        store_source_record,
    )

    _require_business_mutation(session, tenant_id, "set_company_currency")
    lock_delivery_state(session, tenant_id)
    stated = _validate(session, tenant_id, currency)
    row = _row(session, tenant_id)
    if _expected is not UNCHECKED and (row.currency if row else None) != _expected:
        raise InvalidOperation(code="company_currency_changed_since_review")
    previous = row.currency if row else DEFAULT_CURRENCY
    source, _, _ = store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        SOURCE_TYPE,
        tenant_id,
        {"currency": stated, "statement_id": action_id or uid("stm")},
    )
    # Postings already made in the stated currency are their own company value.
    from sqlalchemy import update

    session.execute(
        update(LedgerEntry)
        .where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.currency == stated,
            LedgerEntry.company_amount.is_(None),
        )
        .values(company_amount=LedgerEntry.amount, exchange_rate=1)
        .execution_options(synchronize_session=False)
    )
    if row is None:
        row = CompanyCurrency(
            tenant_id=tenant_id, currency=stated, source_record_id=source.id
        )
        session.add(row)
    elif row.source_record_id != source.id:
        row.currency = stated
        row.source_record_id = source.id
        row.updated_at = now()
    else:
        # The same confirmation again: it already stated this.
        return company_currency_state(session, tenant_id)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "company_currency.set",
        "company_currency",
        tenant_id,
        {"currency": stated, "previous": previous},
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return company_currency_state(session, tenant_id)


COMPANY_CURRENCY_TOOLS = {"company_currency_set"}


def review_company_currency(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The arguments a confirmation executes and what the person is shown."""
    stated = _validate(session, tenant_id, str(arguments.get("currency") or ""))
    row = _row(session, tenant_id)
    current = row.currency if row else None
    return (
        {"currency": stated, "reviewed": current},
        {"current": current or DEFAULT_CURRENCY, "proposed": stated},
    )
