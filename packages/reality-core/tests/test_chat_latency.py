from decimal import Decimal

from sqlalchemy import event

from reality.services.core import (
    active_reserved,
    create_chat_session,
    create_commitment,
    create_item,
    create_location,
    create_tenant,
    inventory_rows,
    open_quantity,
    record_movement,
    reserve,
    revise_commitment,
    send_chat_message,
    stock_at,
)


def test_inventory_reads_are_bounded_and_match_current_terms(session, business):
    tenant = business.tenant.id

    def seed(item):
        incoming = create_commitment(
            session,
            tenant,
            "supplier_delivery",
            business.supplier.id,
            business.company.id,
            item.id,
            business.location.id,
            10,
            "2026-09-20",
        )
        record_movement(
            session,
            tenant,
            "receipt",
            item.id,
            3,
            to_location_id=business.location.id,
            commitment_id=incoming.id,
        )
        revise_commitment(
            session,
            tenant,
            incoming.id,
            quantity=12,
            stated_at="2026-09-16T00:00:00Z",
            note="Supplier restatement",
        )
        outgoing = create_commitment(
            session,
            tenant,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            item.id,
            business.location.id,
            2,
            "2026-09-20",
        )
        reserve(session, tenant, outgoing.id)
        return incoming

    incoming = {business.item.id: seed(business.item)}
    statements = []

    def collect(conn, cursor, statement, parameters, context, many):
        statements.append(statement)

    def measured():
        statements.clear()
        event.listen(session.get_bind(), "before_cursor_execute", collect)
        try:
            result = inventory_rows(session, tenant)
        finally:
            event.remove(session.get_bind(), "before_cursor_execute", collect)
        return result, len(statements)

    _, single_count = measured()
    for index in range(19):
        item = create_item(session, tenant, f"BATCH-{index}", f"Batch {index}")
        incoming[item.id] = seed(item)
    other = create_tenant(session, "Unrelated company")
    other_item = create_item(session, other.id, "OTHER", "Other item")
    other_location = create_location(session, other.id, "Other warehouse")
    record_movement(
        session,
        other.id,
        "opening_stock",
        other_item.id,
        999,
        to_location_id=other_location.id,
    )
    rows, many_count = measured()
    assert len(rows) == 20
    for row in rows:
        identity = row["item"].id
        assert row["physical"] == stock_at(session, tenant, identity) == Decimal(3)
        assert (
            row["reserved"] == active_reserved(session, tenant, identity) == Decimal(2)
        )
        assert (
            row["incoming"]
            == open_quantity(session, tenant, incoming[identity].id)
            == Decimal(9)
        )
        assert row["available"] == 1
        assert row["projected"] == 10
        assert len(row["receipts"]) == 1
        assert row["issues"] == []
    assert many_count == single_count
    assert many_count <= 12


def test_provider_history_is_bounded_in_sql(session, business, monkeypatch):
    from reality.agent import mcp_chat

    chat = create_chat_session(session, business.tenant.id)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    for index in range(8):
        send_chat_message(session, business.tenant.id, chat.id, f"Hello {index}")
    captured = []

    async def provider(**kwargs):
        captured.extend(kwargs["history"])
        return "Done"

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-secret")
    monkeypatch.setattr(mcp_chat, "reply_via_anthropic_tools", provider)
    statements = []

    def collect(conn, cursor, statement, parameters, context, many):
        if "FROM chat_message" in statement:
            statements.append(statement)

    event.listen(session.get_bind(), "before_cursor_execute", collect)
    try:
        send_chat_message(session, business.tenant.id, chat.id, "Latest question")
    finally:
        event.remove(session.get_bind(), "before_cursor_execute", collect)
    assert len(captured) == 12
    assert captured[0]["content"] == "Hello 2"
    assert captured[-2]["content"] == "Hello 7"
    assert any("LIMIT" in query for query in statements)
