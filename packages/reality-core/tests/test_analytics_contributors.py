"""A grouped value explains its exact evidence and preserves scoped filtering."""

from decimal import Decimal

import pytest
from test_analytics_execution import orders, request

from reality.services.analytics.contributors import contributors
from reality.services.analytics.execution import AnalyticsError


def test_contributors_follow_evidence_lines_without_fanout(session, business):
    orders(session, business)
    args = {
        **request(),
        "group": {"customer_id": business.customer.id},
        "measure": "stated_line_amount",
    }
    result = contributors(session, business.tenant.id, args)
    assert len(result["records"]) == 2
    assert all(
        r["record_kind"] == "document_line" and r["source_record_id"]
        for r in result["records"]
    )
    assert sum(Decimal(r["stated_line_amount"]) for r in result["records"]) == 12
    with pytest.raises(AnalyticsError):
        contributors(
            session, business.tenant.id, {**args, "group": {"tenant_id": "foreign"}}
        )


def test_contributor_cursor_is_scoped_and_visits_each_line(session, business):
    orders(session, business)
    args = {
        **request(),
        "group": {"customer_id": business.customer.id},
        "measure": "stated_line_amount",
        "page_size": 1,
    }
    first = contributors(session, business.tenant.id, args)
    assert first["has_more"] and first["next_cursor"]
    second = contributors(
        session, business.tenant.id, {**args, "cursor": first["next_cursor"]}
    )
    assert first["records"][0]["record_id"] != second["records"][0]["record_id"]
    assert not second["has_more"]
    with pytest.raises(AnalyticsError, match="cursor"):
        contributors(
            session,
            business.tenant.id,
            {**args, "measure": "order_count", "cursor": first["next_cursor"]},
        )


def test_distinct_order_count_explains_one_record_per_order(session, business):
    orders(session, business)
    result = contributors(
        session, business.tenant.id, {**request(), "measure": "order_count"}
    )
    assert result["total"] == 1
    assert result["records"][0]["record_kind"] == "document"
