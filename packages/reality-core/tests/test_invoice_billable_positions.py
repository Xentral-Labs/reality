"""Spec 283 FR-006: a party's billable order positions, grouped by order."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import event

from reality.services import core
from reality.services.invoice_billing import billable_positions
from reality.tools.application import run_read_tool


def placed(
    session, b, direction="sales", *, party=None, currency="EUR", quantity="3", day=""
):
    counterparty = party or (b.customer if direction == "sales" else b.supplier)
    _, document, lines, promises = core.create_manual_order(
        session,
        b.tenant.id,
        direction,
        "ORDER-283-" + uuid4().hex[:6],
        b.company.id,
        counterparty.id,
        b.location.id,
        [
            {
                "item_id": b.item.id,
                "quantity": quantity,
                "unit_price": "10",
                "gross_amount": str(10 * int(quantity)),
            }
        ],
        gross_amount=str(10 * int(quantity)),
        currency=currency,
        document_date=day,
    )
    return document, lines[0], promises[0]


def move(session, b, kind, promise, quantity):
    outbound = kind in {"shipment", "supplier_return"}
    core.record_movement(
        session,
        b.tenant.id,
        kind,
        b.item.id,
        quantity,
        **(
            {"from_location_id": b.location.id}
            if outbound
            else {"to_location_id": b.location.id}
        ),
        commitment_id=promise.id,
    )


def stock(session, b, quantity=50):
    core.record_movement(
        session,
        b.tenant.id,
        "opening_stock",
        b.item.id,
        quantity,
        to_location_id=b.location.id,
    )


def listed(result):
    return {
        position["order_line_id"]: position["billable"]
        for order in result["orders"]
        for position in order["positions"]
    }


def read(session, b, direction="sales", **extra):
    party = b.customer if direction == "sales" else b.supplier
    return billable_positions(
        session,
        b.tenant.id,
        direction=direction,
        party_id=party.id,
        currency=extra.pop("currency", "EUR"),
        **extra,
    )


def test_delivered_and_unbilled_positions_are_listed_by_order(session, business):
    """What was kept and not yet billed, per order line, grouped by order."""
    stock(session, business)
    doc_b, b, b_promise = placed(session, business, quantity="5", day="2026-09-05")
    doc_a, a, a_promise = placed(session, business, day="2026-09-01")
    _, billed, billed_promise = placed(session, business)
    _, unshipped, _ = placed(session, business)
    other = core.create_party(session, business.tenant.id, "Other KG", "customer")
    _, foreign, foreign_promise = placed(session, business, party=other)
    _, swiss, swiss_promise = placed(session, business, currency="CHF")
    for promise, quantity in (
        (a_promise, 3),
        (b_promise, 2),
        (billed_promise, 3),
        (foreign_promise, 3),
        (swiss_promise, 3),
    ):
        move(session, business, "shipment", promise, quantity)
    core.record_sales_invoice(
        session, business.tenant.id, billed.id, "3", "30", "INV-D"
    )

    result = read(session, business)

    assert listed(result) == {a.id: Decimal(3), b.id: Decimal(2)}
    assert [order["id"] for order in result["orders"]] == [doc_a.id, doc_b.id]
    assert result["total"] == 2
    position = result["orders"][1]["positions"][0]
    assert (
        position["ordered"],
        position["delivered"],
        position["invoiced"],
        position["remaining"],
    ) == (Decimal(5), Decimal(2), Decimal(0), Decimal(5))
    assert unshipped.id not in listed(result)
    assert foreign.id not in listed(result) and swiss.id not in listed(result)


def test_returns_partial_invoices_and_reversals_change_what_is_billable(
    session, business
):
    """Kept, not shipped; billed honours a reversed invoice."""
    stock(session, business)
    _, a, a_promise = placed(session, business)
    _, b, b_promise = placed(session, business)
    move(session, business, "shipment", a_promise, 3)
    move(session, business, "shipment", b_promise, 3)
    move(session, business, "return", a_promise, 1)
    receipt = core.record_sales_invoice(
        session, business.tenant.id, b.id, "3", "30", "INV-REV"
    )
    assert listed(read(session, business)) == {a.id: Decimal(2)}

    group = next(
        row
        for row in core._order_line_billing(session, business.tenant.id, b.id)[
            "evidence"
        ]
    )["posting_group_ids"][0]
    core.reverse_ledger_posting_group(
        session, business.tenant.id, group, reason="Wrong number"
    )
    assert receipt
    assert listed(read(session, business)) == {a.id: Decimal(2), b.id: Decimal(3)}


def test_supplier_positions_are_billable_as_received_less_returned(session, business):
    """Purchase direction: received less sent back, not yet billed."""
    _, a, a_promise = placed(session, business, "purchase")
    _, b, _ = placed(session, business, "purchase")
    move(session, business, "receipt", a_promise, 3)
    move(session, business, "supplier_return", a_promise, 1)

    assert listed(read(session, business, "purchase")) == {a.id: Decimal(2)}
    assert b.id not in listed(read(session, business, "purchase"))


def test_the_limit_keeps_a_truthful_total(session, business):
    """At most `limit` positions are returned; the total counts all of them."""
    stock(session, business)
    for _ in range(3):
        _, _, promise = placed(session, business)
        move(session, business, "shipment", promise, 3)

    result = read(session, business, limit=2)
    assert len(listed(result)) == 2
    assert result["total"] == 3
    with pytest.raises(core.InvalidOperation):
        read(session, business, limit=201)


def test_the_read_is_tenant_scoped(session, business):
    """A party of another company is not found."""
    other = core.create_tenant(session, "Foreign 283")
    with pytest.raises(core.NotFound):
        billable_positions(
            session,
            other.id,
            direction="sales",
            party_id=business.customer.id,
            currency="EUR",
        )


def test_history_does_not_multiply_the_statements(session, business):
    """A4: fully billed history is filtered in SQL, not read line by line."""
    stock(session, business, 200)
    _, _, promise = placed(session, business)
    move(session, business, "shipment", promise, 3)

    def statements():
        count = 0

        def counter(*_):
            nonlocal count
            count += 1

        engine = session.get_bind()
        event.listen(engine, "before_cursor_execute", counter)
        try:
            read(session, business)
        finally:
            event.remove(engine, "before_cursor_execute", counter)
        return count

    baseline = statements()
    for index in range(10):
        _, line, history = placed(session, business)
        move(session, business, "shipment", history, 3)
        core.record_sales_invoice(
            session, business.tenant.id, line.id, "3", "30", f"INV-H{index}"
        )
    assert statements() == baseline


def test_the_read_tool_and_http_route_answer_the_same(session, business):
    """FR-007: MCP/Chat read tool and HTTP call the same service."""
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    stock(session, business)
    _, a, promise = placed(session, business)
    move(session, business, "shipment", promise, 3)
    session.commit()
    arguments = {
        "direction": "sales",
        "party_id": business.customer.id,
        "currency": "EUR",
    }
    tool = run_read_tool(
        session, business.tenant.id, "invoice_billable_positions", arguments
    )
    assert {key: Decimal(str(value)) for key, value in listed(tool).items()} == {
        a.id: Decimal(3)
    }

    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/tenants/{business.tenant.id}/invoice-billable-positions",
                params=arguments,
            )
            assert response.status_code == 200, response.text
            body = response.json()
            assert [
                position["order_line_id"]
                for order in body["orders"]
                for position in order["positions"]
            ] == [a.id]
            assert body["total"] == 1
    finally:
        app.dependency_overrides.clear()
