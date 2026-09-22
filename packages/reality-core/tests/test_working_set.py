"""A derivation about open work must not read the work that is finished (181 FR-003).

The rule is that closed records are excluded by predicate rather than fetched and
skipped, so that a company's finished history stops costing anything to ignore. That
is measured here rather than reviewed: the same derivations run against a company with
a few closed promises and again with sixty more, and what they read is compared.

Not every derivation is subject to it. A register shows a promise that was cancelled
and an invoice that was paid, so reading them is the job. The exemption is named per
projection below, with the reason, so that it stays a decision rather than a habit.
"""

import re

import pytest
from sqlalchemy import event

from reality.services import projections
from reality.services.core import (
    cancel_commitment,
    create_commitment,
    create_document,
    record_movement,
)

#: Derivations that answer about open work, and must not pay for closed work.
ABOUT_OPEN_WORK = (
    projections.FULFILLMENT_QUEUE,
    projections.FULFILLMENT_BLOCKERS,
    projections.ITEM_SUPPLY_DEMAND,
    projections.INVENTORY,
)

#: Derivations that legitimately read what is finished, and why. Exceptions is the
#: interesting one: half its classes judge what happened *after* a promise was
#: fulfilled — billed and not received, received and not billed — so an open working
#: set would not be a cheaper version of it, it would be a different answer.
ABOUT_HISTORY = {
    projections.COMMITMENT_REGISTER: "a register lists promises that were cancelled",
    projections.DOCUMENT_REGISTER: "a register lists documents that are settled",
    projections.TIMELINE: "a timeline is what happened",
    projections.EXCEPTIONS: "classes that judge billing after fulfilment need it",
    projections.JOURNAL: "a ledger is history by construction",
    projections.PAYMENTS: "settlement is judged against what was invoiced",
    projections.OPEN_FINANCIAL_ITEMS: "open items are derived from posted history",
    projections.TENANT_USAGE: "counts are of everything",
}


def rows_read(session):
    """How many rows every statement in this block brought back, by table."""
    counts: dict[str, int] = {}
    bind = session.get_bind()
    table = re.compile(r"\bFROM\s+([a-z_]+)", re.IGNORECASE)

    def after(conn, cursor, statement, parameters, context, executemany):
        match = table.search(statement)
        if match and cursor.rowcount and cursor.rowcount > 0:
            counts[match.group(1)] = counts.get(match.group(1), 0) + cursor.rowcount

    event.listen(bind, "after_cursor_execute", after)
    return counts, lambda: event.remove(bind, "after_cursor_execute", after)


def closed_work(session, business, count: int, tag: str) -> None:
    """Orders whose promise was cancelled: finished work nobody is waiting for."""
    tenant = business.tenant.id
    for number in range(count):
        order = create_document(
            session,
            tenant,
            "sales_order",
            f"ORD-{tag}-{number}",
            business.customer.id,
            "100",
            document_date="2026-08-01",
        )
        promise = create_commitment(
            session,
            tenant,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            business.item.id,
            business.location.id,
            "1",
            "2026-08-10T00:00:00+00:00",
            document_id=order.id,
        )
        cancel_commitment(session, tenant, promise.id, reason="Test cancellation", _commit=False)
    # One promise still open, so the derivations have something to answer about.
    still_open = create_document(
        session,
        tenant,
        "sales_order",
        f"ORD-{tag}-open",
        business.customer.id,
        "100",
        document_date="2026-08-01",
    )
    create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        "2026-08-10T00:00:00+00:00",
        document_id=still_open.id,
    )
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "6",
        to_location_id=business.location.id,
    )
    session.flush()


def read_volume(session, tenant_id: str) -> dict[str, int]:
    volume = {}
    for name in projections.MATERIALIZED_PROJECTIONS:
        counts, stop = rows_read(session)
        projections.derive_projection_rows(session, tenant_id, name)
        stop()
        volume[name] = sum(counts.values())
    return volume


@pytest.fixture
def growth(session, business):
    """What each derivation reads before and after sixty more closed promises."""
    tenant = business.tenant.id
    closed_work(session, business, 3, "few")
    few = read_volume(session, tenant)
    closed_work(session, business, 60, "many")
    many = read_volume(session, tenant)
    return {name: many[name] - few[name] for name in few}


@pytest.mark.parametrize("name", ABOUT_OPEN_WORK)
def test_a_derivation_about_open_work_does_not_read_the_closed_work(growth, name):
    """Sixty more cancelled promises must not cost a queue of open ones anything.

    A small constant is allowed: these derivations also read the company's articles
    and partners, which are neither open nor closed. What may not happen is growth in
    proportion to the promises that ended.
    """
    assert growth[name] <= 10, (
        f"{name} read {growth[name]} more rows because sixty promises were cancelled, "
        "so it is fetching closed records and skipping them. Exclude them in the "
        "predicate, or move this projection to ABOUT_HISTORY with a reason."
    )


def test_every_projection_is_either_about_open_work_or_says_why_not(growth):
    """No projection may sit outside this decision unnoticed."""
    classified = set(ABOUT_OPEN_WORK) | set(ABOUT_HISTORY)
    missing = sorted(set(projections.MATERIALIZED_PROJECTIONS) - classified)
    assert not missing, (
        f"{missing} are neither declared to be about open work nor given a reason for "
        "reading what is finished."
    )


def test_the_measurement_can_see_growth_at_all(growth):
    """The control: if nothing grew anywhere, the comparison above proves nothing."""
    assert any(value > 50 for value in growth.values()), (
        "no derivation read more after sixty more closed promises, so this fixture is "
        "not producing the history the test is about and its silence means nothing"
    )
