"""External stock from the catalog (J07; spec 344)."""

import json
from datetime import timedelta
from decimal import Decimal

from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    run_read_tool,
)


def _confirm(session, business, tool, arguments):
    """A reviewed change: proposed, then confirmed by a person."""
    proposal = create_change_proposal(session, business.tenant.id, tool, arguments)
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )
    assert executed.status == "executed", executed.output
    return json.loads(executed.output)


def _report(session, business, location, quantity, at, reporter):
    return _confirm(
        session,
        business,
        "external_stock_state",
        {
            "reporter_party_id": reporter.id,
            "lines": [
                {
                    "item_id": business.item.id,
                    "location_id": location.id,
                    "quantity": quantity,
                    "stated_at": at.isoformat(),
                }
            ],
        },
    )


def _differs(session, business):
    return [
        row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == "external_stock_differs"
    ]


def test_a_3pl_stock_report_that_differs_is_visible_until_resolved(session, business):
    """J07: the 3PL reports 95 where Reality's movements hold 100."""
    tenant = business.tenant.id
    three_pl = core.create_party(session, tenant, "Fulfil Logistics", "supplier")
    warehouse = core.create_location(session, tenant, "Fulfil 3PL Leipzig")
    monday = core.now() - timedelta(days=3)
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "100",
        to_location_id=warehouse.id,
        occurred_at=monday - timedelta(days=1),
    )

    # Positive control: Monday's report matches, so there is nothing to look at.
    _report(session, business, warehouse, "100", monday, three_pl)
    assert _differs(session, business) == []

    # Tuesday's report says 95.
    tuesday = monday + timedelta(days=1)
    _report(session, business, warehouse, "95", tuesday, three_pl)

    (finding,) = _differs(session, business)
    values = finding.causal_values
    assert (values["stated_quantity"], values["reality_quantity"]) == (
        Decimal(95),
        Decimal(100),
    )
    assert values["difference"] == Decimal(-5)
    assert values["reporter_party_id"] == three_pl.id
    assert values["stated_at"] == tuesday
    (row,) = run_read_tool(session, tenant, "external_stock", {"differing_only": True})
    assert (row["location"], row["difference"]) == ("Fulfil 3PL Leipzig", "-5")
    # Stating stock moved nothing: Reality still holds 100.
    assert core.stock_at(session, tenant, business.item.id, warehouse.id) == 100

    # The warehouse lead takes the 3PL's count over at Tuesday's time.
    _confirm(
        session,
        business,
        "stock_count",
        {
            "location_id": warehouse.id,
            "note": "Five lost at the 3PL, per their report",
            "lines": [
                {
                    "item_id": business.item.id,
                    "counted_quantity": "95",
                    "counted_at": tuesday.isoformat(),
                }
            ],
        },
    )
    assert _differs(session, business) == []
    assert core.stock_at(session, tenant, business.item.id, warehouse.id) == 95

    # Wednesday's report differs again; the finding names the newer statement.
    wednesday = tuesday + timedelta(days=1)
    latest = _report(session, business, warehouse, "93", wednesday, three_pl)
    (finding,) = _differs(session, business)
    assert finding.record_id == latest["statement_ids"][0]
    assert finding.causal_values["difference"] == Decimal(-2)
