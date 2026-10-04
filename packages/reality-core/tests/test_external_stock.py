"""Spec 344: stock someone outside states is compared, never taken over."""

import json
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import event, func, select

from reality.db.core import ExternalStockStatement, Movement
from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.external_stock import external_stock, record_external_stock
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def _stock(session, business, quantity, at):
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        occurred_at=at,
    )


def _state(session, business, quantity, at, **extra):
    return record_external_stock(
        session,
        business.tenant.id,
        [
            {
                "item_id": business.item.id,
                "location_id": business.location.id,
                "quantity": quantity,
                "stated_at": at.isoformat(),
            }
        ],
        **extra,
    )


def _differs(session, business):
    return [
        row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == "external_stock_differs"
    ]


def _movements(session, business):
    return session.scalar(
        select(func.count())
        .select_from(Movement)
        .where(Movement.tenant_id == business.tenant.id)
    )


def test_a_statement_that_differs_is_reported_and_moves_nothing(session, business):
    tenant = business.tenant.id
    yesterday = core.now() - timedelta(days=1)
    _stock(session, business, "100", yesterday - timedelta(hours=1))
    three_pl = reviewed_create_party(session, tenant, "Fulfil GmbH", "supplier")
    before = _movements(session, business)

    # Positive control: a matching statement gives no finding.
    _state(session, business, "100", yesterday, reporter_party_id=three_pl.id)
    assert _differs(session, business) == []

    _state(
        session,
        business,
        "95",
        yesterday + timedelta(minutes=5),
        reporter_party_id=three_pl.id,
    )

    (finding,) = _differs(session, business)
    values = finding.causal_values
    assert (values["stated_quantity"], values["reality_quantity"]) == (
        Decimal(95),
        Decimal(100),
    )
    assert values["difference"] == Decimal(-5)
    assert values["reporter_party_id"] == three_pl.id
    assert "Fulfil GmbH states 95" in finding.impact
    assert _movements(session, business) == before


def test_reality_is_read_at_the_stated_time_not_now(session, business):
    stated = core.now() - timedelta(days=2)
    _stock(session, business, "100", stated - timedelta(hours=1))
    _state(session, business, "100", stated)
    # A receipt after the statement does not make it differ.
    _stock(session, business, "20", stated + timedelta(hours=1))
    assert _differs(session, business) == []
    # One recorded later but dated before it does.
    _stock(session, business, "3", stated - timedelta(minutes=30))
    (finding,) = _differs(session, business)
    assert finding.causal_values["difference"] == Decimal(-3)


def test_a_count_at_the_stated_time_clears_it(session, business):
    stated = core.now() - timedelta(days=1)
    _stock(session, business, "100", stated - timedelta(hours=1))
    _state(session, business, "95", stated)
    assert len(_differs(session, business)) == 1

    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "stock_count",
        {
            "location_id": business.location.id,
            "note": "Take over the 3PL report",
            "lines": [
                {
                    "item_id": business.item.id,
                    "counted_quantity": "95",
                    "counted_at": stated.isoformat(),
                }
            ],
        },
    )
    approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )

    assert _differs(session, business) == []


def test_a_newer_statement_that_matches_clears_it(session, business):
    stated = core.now() - timedelta(days=1)
    _stock(session, business, "100", stated - timedelta(hours=1))
    _state(session, business, "95", stated)
    assert len(_differs(session, business)) == 1

    _state(session, business, "100", stated + timedelta(hours=2))

    assert _differs(session, business) == []
    (row,) = external_stock(session, business.tenant.id)
    assert (row["stated_quantity"], row["difference"]) == ("100", "0")


@pytest.mark.parametrize(
    ("line", "code"),
    [
        ({"quantity": "-1"}, "external_stock_quantity_invalid"),
        ({"quantity": "1.00001"}, "external_stock_quantity_invalid"),
        ({"stated_at": "tomorrow"}, "external_stock_time_invalid"),
        ({"item_id": "itm_missing"}, "item_not_found"),
        ({"location_id": "loc_missing"}, "external_stock_location_not_stock"),
        ({"lot_id": "x"}, "external_stock_fields_invalid"),
    ],
)
def test_what_cannot_be_stated_is_refused(session, business, line, code):
    base = {
        "item_id": business.item.id,
        "location_id": business.location.id,
        "quantity": "5",
    }
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        record_external_stock(session, business.tenant.id, [{**base, **line}])
    assert refused.value.code == code


def test_a_future_time_is_refused(session, business):
    with pytest.raises(core.InvalidOperation) as refused:
        _state(session, business, "5", core.now() + timedelta(days=1))
    assert refused.value.code == "external_stock_time_future"


def test_the_reviewed_tool_records_what_was_reviewed(session, business):
    stated = core.now() - timedelta(hours=3)
    _stock(session, business, "10", stated - timedelta(hours=1))
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "external_stock_state",
        {
            "lines": [
                {
                    "item_id": business.item.id,
                    "location_id": business.location.id,
                    "quantity": "8",
                    "stated_at": stated.isoformat(),
                }
            ]
        },
    )
    (line,) = json.loads(proposal.output)["external_stock"]["lines"]
    assert (line["reality_quantity"], line["difference"]) == ("10", "-2")

    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )

    assert executed.status == "executed"
    (statement,) = session.scalars(
        select(ExternalStockStatement).where(
            ExternalStockStatement.tenant_id == business.tenant.id
        )
    )
    assert Decimal(statement.quantity) == 8
    assert len(_differs(session, business)) == 1


def test_another_company_sees_nothing(session, business):
    stated = core.now() - timedelta(days=1)
    _stock(session, business, "100", stated - timedelta(hours=1))
    _state(session, business, "95", stated)
    other = core.create_tenant(session, "Other GmbH")

    assert len(_differs(session, business)) == 1
    assert external_stock(session, other.id) == []
    assert not [
        row
        for row in operational_exceptions(session, other.id)
        if row.class_id == "external_stock_differs"
    ]


def test_the_comparison_reads_every_statement_in_bounded_queries(session, business):
    tenant = business.tenant.id
    stated = core.now() - timedelta(days=1)
    locations = [business.location] + [
        reviewed_create_location(session, tenant, f"3PL {n}") for n in range(5)
    ]

    def compare():
        statements = []

        def count(*_):
            statements.append(1)

        engine = session.get_bind()
        event.listen(engine, "before_cursor_execute", count)
        try:
            external_stock(session, tenant)
        finally:
            event.remove(engine, "before_cursor_execute", count)
        return len(statements)

    for location in locations[:2]:
        record_external_stock(
            session,
            tenant,
            [
                {
                    "item_id": business.item.id,
                    "location_id": location.id,
                    "quantity": "1",
                    "stated_at": stated.isoformat(),
                }
            ],
        )
    few = compare()
    for location in locations[2:]:
        record_external_stock(
            session,
            tenant,
            [
                {
                    "item_id": business.item.id,
                    "location_id": location.id,
                    "quantity": "1",
                    "stated_at": stated.isoformat(),
                }
            ],
        )

    assert compare() == few


from intake_review_support import reviewed_create_location, reviewed_create_party
