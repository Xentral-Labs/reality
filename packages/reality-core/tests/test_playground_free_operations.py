"""Selected work remains independent of lesson order (097/FR-003–005)."""

from decimal import Decimal
from types import SimpleNamespace

import test_playground_steps
from conftest import record_by_id

from reality.web import api

durable_playground = test_playground_steps.durable_playground


def test_mixed_orders_can_be_fulfilled_independently(durable_playground):
    from sqlalchemy.orm import Session

    from reality.db.core import PlaygroundRun
    from reality.services.core import open_quantity, stock_at
    from reality.services.playground import confirm_step, prepare_step, read_run

    engine, owner, run_id = durable_playground
    with Session(engine) as session:
        run = record_by_id(session, PlaygroundRun, run_id)
        tenant, refs = run.tenant_id, run.initialization_progress
    item = refs["items"]["BIKE-LIGHT"]
    location = refs["locations"]["warehouse"]

    def execute(key, tool, args):
        proposal = prepare_step(engine, owner, run_id, key, tool, args)
        result = confirm_step(
            engine,
            owner,
            run_id,
            proposal["step_id"],
            proposal["preview"]["revision"],
            confirmed=True,
        )
        assert result["status"] == "executed", result
        assert result["receipt"]
        return result

    def order(key, direction):
        result = execute(
            key,
            "order_create",
            {
                "direction": direction,
                "number": key,
                "company_party_id": refs["parties"]["company"],
                "counterparty_id": refs["parties"][
                    "supplier" if direction == "purchase" else "customer_huber"
                ],
                "item_id": item,
                "location_id": location,
                "quantity": "10",
                "unit_price": "8",
            },
        )
        return next(
            row["id"]
            for row in result["receipt"]["records"]
            if row["family"] == "commitment"
        )

    a = order("sales-a", "sales")
    b = order("purchase-b", "purchase")
    c = order("sales-c", "sales")
    with Session(engine) as session:
        assert stock_at(session, tenant, item, location) == 0
        assert len(read_run(session, owner, run_id)["steps"]) == 3
    execute(
        "partial-b",
        "movement_create",
        {
            "movement_type": "receipt",
            "commitment_id": b,
            "item_id": item,
            "to_location_id": location,
            "quantity": "4",
        },
    )
    execute("reserve-a", "reserve", {"commitment_id": a, "quantity": "4"})
    execute(
        "ship-a",
        "movement_create",
        {
            "movement_type": "shipment",
            "commitment_id": a,
            "item_id": item,
            "from_location_id": location,
            "quantity": "4",
        },
    )
    execute(
        "remaining-b",
        "movement_create",
        {
            "movement_type": "receipt",
            "commitment_id": b,
            "item_id": item,
            "to_location_id": location,
            "quantity": "6",
        },
    )
    with Session(engine) as session:
        assert open_quantity(session, tenant, a) == 6
        assert open_quantity(session, tenant, b) == 0
        assert open_quantity(session, tenant, c) == 10
        assert stock_at(session, tenant, item, location) == 6


def test_commitment_response_exposes_selected_target(monkeypatch):
    row = SimpleNamespace(
        id="com_selected",
        type="customer_delivery",
        due_at=None,
        item_id="itm_selected",
        location_id="loc_selected",
        quantity=Decimal(12),
        status="open",
        document_id="doc_selected",
    )
    monkeypatch.setattr(api, "get_tenant", lambda *args: None)
    monkeypatch.setattr(
        api,
        "commitment_page",
        lambda *args, **kwargs: (
            [(row, "ok", "Customer", "Bell", Decimal(3), Decimal(7))],
            None,
        ),
    )
    monkeypatch.setattr(api, "_page_response", lambda page: {})
    result = api.tenant_commitment_control("sandbox", None, page=1, size=50)
    assert result["items"][0]["location_id"] == "loc_selected"
    assert result["items"][0]["open_quantity"] == "7"


def test_shipment_review_tracks_remaining_commitment(monkeypatch):
    from reality.services import playground

    commitment = SimpleNamespace(
        id="com_selected", item_id="item", location_id="location", status="open"
    )
    session = SimpleNamespace(scalar=lambda query: commitment)
    monkeypatch.setattr(playground, "stock_at", lambda *args: Decimal(12))
    monkeypatch.setattr(playground, "open_quantity", lambda *args: Decimal(7))
    args = {
        "commitment_id": "com_selected",
        "item_id": "item",
        "from_location_id": "location",
    }
    before = playground._shipment_state(session, "sandbox", args)
    assert before["open_quantity"] == "7"
    monkeypatch.setattr(playground, "open_quantity", lambda *args: Decimal(5))
    after = playground._shipment_state(session, "sandbox", args)
    assert playground._preview_revision(args, before) != playground._preview_revision(
        args, after
    )
