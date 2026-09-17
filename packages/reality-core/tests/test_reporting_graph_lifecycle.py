"""A saved graph report holds the question, and reopening it asks again.

The number is never stored, because a number stored is a number that stops being
true. What has to survive instead is the question and the meaning that produced
it — so a report records the model version, and a report saved under one meaning
cannot be silently reopened under another.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from reality.domain.traversal import Traversal
from reality.services.analytics.errors import AnalyticsError
from reality.services.analytics.graph_model import reporting_graph
from reality.services.analytics.reports import (
    change_graph_report,
    get_report,
    list_reports,
)
from reality.services.analytics.traversal import run_traversal
from reality.services.core import NotFound, create_manual_order
from reality.services.memberships import Principal

QUESTION = {
    "from": "order",
    "as": "o",
    "measures": ["stated_order_amount"],
    "group_by": [{"field": "o.currency"}],
}


def save(session, tenant_id, principal, **changes):
    arguments = {
        "operation": "create",
        "request_id": str(uuid4()),
        "name": "Umsatz nach Währung",
        "question": QUESTION,
        **changes,
    }
    return change_graph_report(session, tenant_id, principal, arguments)


@pytest.fixture
def author(scheduled_owner):
    return Principal(scheduled_owner.id)


@pytest.fixture
def sales(session, business):
    create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "AN-001",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "sku": business.item.sku,
                "quantity": "1",
                "unit_price": "1",
                "gross_amount": "250",
                "unit": "pcs",
            }
            for _ in range(4)
        ],
        "1000",
        currency="EUR",
        ordered_at="2026-03-10T10:00:00Z",
        document_date="2026-03-10",
    )
    session.flush()


# --- saving the question ---------------------------------------------------------


def test_a_saved_report_holds_the_question_and_its_meaning(session, business, author):
    saved = save(session, business.tenant.id, author)
    assert saved["kind"] == "graph"
    assert saved["model_version"] == reporting_graph().model_version
    assert saved["definition"]["from"] == "order"
    assert saved["definition"]["measures"] == ["stated_order_amount"]


def test_the_stored_question_carries_no_sql_and_no_dialect(session, business, author):
    """What makes a different execution backend a compiler change, not a migration."""
    stored = repr(save(session, business.tenant.id, author)["definition"]).lower()
    for trace in ("select", "join", "document", "postgres", "sql"):
        assert trace not in stored, trace


def test_reopening_asks_the_question_again(session, business, author, sales):
    saved = save(session, business.tenant.id, author)
    reopened = get_report(
        session, business.tenant.id, author, saved["id"], report_kind="graph"
    )
    result = run_traversal(
        session, business.tenant.id, Traversal.model_validate(reopened["definition"])
    )
    assert Decimal(result.rows[0]["stated_order_amount"]) == Decimal(1000)


def test_a_reopened_question_is_the_one_that_was_saved(session, business, author):
    saved = save(session, business.tenant.id, author)
    reopened = get_report(
        session, business.tenant.id, author, saved["id"], report_kind="graph"
    )
    assert Traversal.model_validate(reopened["definition"]) == Traversal.model_validate(
        QUESTION
    )


# --- a lost response must not create two reports ----------------------------------


def test_a_retry_returns_the_same_report(session, business, author):
    arguments = {
        "operation": "create",
        "request_id": str(uuid4()),
        "name": "Umsatz nach Währung",
        "question": QUESTION,
    }
    first = change_graph_report(session, business.tenant.id, author, arguments)
    again = change_graph_report(session, business.tenant.id, author, arguments)
    assert again["id"] == first["id"]
    assert again["replayed"] is True
    listed = list_reports(session, business.tenant.id, author, report_kind="graph")
    assert len(listed["records"]) == 1, "a lost response creates one report, not two"


def test_reusing_a_retry_key_for_a_different_question_is_refused(
    session, business, author
):
    request_id = str(uuid4())
    save(session, business.tenant.id, author, request_id=request_id)
    with pytest.raises(AnalyticsError) as refusal:
        save(
            session,
            business.tenant.id,
            author,
            request_id=request_id,
            name="Etwas anderes",
        )
    assert refusal.value.code == "idempotency_conflict"


def test_saving_over_a_stale_revision_is_refused(session, business, author):
    saved = save(session, business.tenant.id, author)
    change_graph_report(
        session,
        business.tenant.id,
        author,
        {
            "operation": "rename",
            "request_id": str(uuid4()),
            "report_id": saved["id"],
            "expected_revision": saved["revision"],
            "name": "Neu benannt",
        },
    )
    with pytest.raises(AnalyticsError) as refusal:
        change_graph_report(
            session,
            business.tenant.id,
            author,
            {
                "operation": "rename",
                "request_id": str(uuid4()),
                "report_id": saved["id"],
                "expected_revision": saved["revision"],
                "name": "Zu spät",
            },
        )
    assert refusal.value.code == "revision_conflict"


# --- what the retired generation left behind ---------------------------------------


def _retired_report(session, tenant_id, owner):
    """A row exactly as the configured generation saved it: no kind, no version.

    They are still in the table. Nothing reads them any more, and the point of
    these tests is that nothing silently writes over them either.
    """
    from reality.db.analytics import AnalyticsReport
    from reality.db.core import uid

    row = AnalyticsReport(
        id=uid("rep"),
        tenant_id=tenant_id,
        owner_user_id=owner.user_id,
        name="Alte Art",
        definition={
            "dataset": "sales_orders",
            "dimensions": ["customer_id"],
            "measures": ["order_count"],
        },
        revision=1,
        create_request_id=str(uuid4()),
        create_payload_hash="retired",
        last_request_id=str(uuid4()),
        last_payload_hash="retired",
    )
    session.add(row)
    session.flush()
    return row


def test_a_retired_report_is_not_listed_among_graph_ones(session, business, author):
    save(session, business.tenant.id, author)
    _retired_report(session, business.tenant.id, author)
    listed = list_reports(session, business.tenant.id, author, report_kind="graph")
    assert [r["name"] for r in listed["records"]] == ["Umsatz nach Währung"]


def test_a_retired_report_cannot_be_opened_as_a_graph_one(session, business, author):
    """Reading it with the wrong meaning is worse than not finding it."""
    row = _retired_report(session, business.tenant.id, author)
    with pytest.raises(NotFound):
        get_report(session, business.tenant.id, author, row.id, report_kind="graph")


def test_a_retired_report_is_not_overwritten_by_a_graph_change(
    session, business, author
):
    """The kind column is NULL on those rows, which is not the same as "any kind"."""
    row = _retired_report(session, business.tenant.id, author)
    with pytest.raises(AnalyticsError) as refusal:
        change_graph_report(
            session,
            business.tenant.id,
            author,
            {
                "operation": "rename",
                "request_id": str(uuid4()),
                "report_id": row.id,
                "expected_revision": row.revision,
                "name": "Falsche Art",
            },
        )
    assert refusal.value.code == "kind_mismatch"
