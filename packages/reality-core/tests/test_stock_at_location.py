"""One item in one place: the pair, and the place scope on the warehouse registers."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import event

from reality.services.core import (
    NotFound,
    create_commitment,
    create_item,
    create_location,
    record_movement,
    reserve,
    update_location,
)
from reality.services.operational_previews import operational_preview
from reality.services.read_contracts import location_inventory_rows
from reality.web.api import location_inspector, stock_inspector
from reality.web.warehouse_reads import warehouse_register


@pytest.fixture
def places(session, business):
    """Three pieces received in Rotterdam, one transferred on, one reserved here."""
    tenant = business.tenant.id
    rotterdam = business.location
    singapore = create_location(session, tenant, "Singapore Warehouse")
    item = business.item
    record_movement(session, tenant, "receipt", item.id, 3, to_location_id=rotterdam.id)
    record_movement(
        session,
        tenant,
        "transfer",
        item.id,
        1,
        from_location_id=rotterdam.id,
        to_location_id=singapore.id,
    )
    commitment = create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        item.id,
        rotterdam.id,
        1,
        "2026-09-30",
    )
    reserve(session, tenant, commitment.id, 1)
    return {
        "tenant": tenant,
        "item": item,
        "rotterdam": rotterdam,
        "singapore": singapore,
        "commitment": commitment,
    }


def pair(places, location_key="rotterdam"):
    return f"{places['item'].id}:{places[location_key].id}"


def rows(sections):
    return {row["label"]: row for section in sections for row in section["rows"]}


def section(sections, title):
    return next(entry for entry in sections if entry["title"] == title)


def metrics(payload):
    return {row["label"]: Decimal(row["value"]) for row in payload["metrics"]}


def test_pair_quantities_equal_the_shared_contract(session, places):
    payload = stock_inspector(session, places["tenant"], pair(places))
    contract = location_inventory_rows(
        session,
        places["tenant"],
        item_id=places["item"].id,
        location_id=places["rotterdam"].id,
    )[pair(places)]
    shown = metrics(payload)
    for label, key, expected in (
        ("Physical", "physical", 2),
        ("Reserved", "reserved", 1),
        ("Available", "available", 1),
    ):
        assert shown[label] == Decimal(contract[key]) == expected


def test_pair_holds_only_this_item_at_this_location(session, places):
    other = create_item(session, places["tenant"], "OTHER-1", "Other item")
    record_movement(
        session,
        places["tenant"],
        "receipt",
        other.id,
        7,
        to_location_id=places["rotterdam"].id,
    )
    record_movement(
        session,
        places["tenant"],
        "receipt",
        places["item"].id,
        4,
        to_location_id=places["singapore"].id,
    )
    payload = stock_inspector(session, places["tenant"], pair(places))
    movements = section(payload["sections"], "Movements here")["rows"]
    assert len(movements) == 2  # the receipt into Rotterdam and the transfer out
    reservations = section(payload["sections"], "Reservations here")["rows"]
    assert len(reservations) == 1
    assert other.name not in str(payload["sections"])


def test_pair_movements_keep_their_moment_beside_the_quantity(session, places):
    """The measure and the moment are separate fields, so each reads as a column."""
    record_movement(
        session,
        places["tenant"],
        "receipt",
        places["item"].id,
        5,
        to_location_id=places["rotterdam"].id,
        occurred_at=datetime(2026, 9, 21, 21, 38, tzinfo=UTC),
    )
    payload = stock_inspector(session, places["tenant"], pair(places))
    row = next(
        entry
        for entry in section(payload["sections"], "Movements here")["rows"]
        if entry["meta"].startswith("2026-09-21")
    )
    unit = places["item"].unit
    assert row["value"] == f"5.0000 {unit}"
    assert row["display_parts"][0] == {"type": "number", "value": "5.0000"}
    assert row["meta_parts"] == [
        {"type": "datetime", "value": "2026-09-21T21:38:00+00:00"}
    ]
    assert unit not in row["meta"] and "\u00b7" not in row["value"]
    reserved = section(payload["sections"], "Reservations here")["rows"][0]
    assert reserved["value"] == f"1.0000 {unit}"
    assert reserved["meta_parts"][0]["type"] == "datetime"


def test_a_movement_imported_without_a_clock_states_only_its_day(session, places):
    """Midnight is what an import writes when it knows no time; do not show it as one."""
    record_movement(
        session,
        places["tenant"],
        "receipt",
        places["item"].id,
        2,
        to_location_id=places["rotterdam"].id,
        occurred_at=datetime(2026, 9, 18, tzinfo=UTC),
    )
    payload = stock_inspector(session, places["tenant"], pair(places))
    row = next(
        entry
        for entry in section(payload["sections"], "Movements here")["rows"]
        if entry["meta"].startswith("2026-09-18")
    )
    assert row["meta_parts"] == [{"type": "date", "value": "2026-09-18"}]


def test_pair_is_reachable_where_nothing_is_left(session, places):
    record_movement(
        session,
        places["tenant"],
        "shipment",
        places["item"].id,
        1,
        from_location_id=places["singapore"].id,
    )
    payload = stock_inspector(session, places["tenant"], pair(places, "singapore"))
    assert metrics(payload)["Physical"] == 0
    assert len(section(payload["sections"], "Movements here")["rows"]) == 2


def test_overallocated_pair_keeps_its_negative_available(session, places):
    record_movement(
        session,
        places["tenant"],
        "shipment",
        places["item"].id,
        2,
        from_location_id=places["rotterdam"].id,
    )
    shown = metrics(stock_inspector(session, places["tenant"], pair(places)))
    assert (shown["Physical"], shown["Reserved"], shown["Available"]) == (0, 1, -1)


def test_a_location_that_stopped_allowing_stock_still_answers_for_its_records(
    session, places
):
    """Configuration changes later than records do; the records stay readable."""
    staging = create_location(session, places["tenant"], "Staging")
    record_movement(
        session,
        places["tenant"],
        "transfer",
        places["item"].id,
        1,
        from_location_id=places["rotterdam"].id,
        to_location_id=staging.id,
    )
    update_location(
        session,
        places["tenant"],
        staging.id,
        staging.name,
        staging.type,
        allows_stock=False,
    )
    payload = stock_inspector(
        session, places["tenant"], f"{places['item'].id}:{staging.id}"
    )
    assert metrics(payload)["Physical"] == 1
    scoped = register(session, places, "stock", location_id=staging.id)
    assert [row["id"] for row in scoped["items"]] == [places["item"].id]


def test_quantities_stay_at_the_exact_location(session, places):
    bin_a = create_location(
        session,
        places["tenant"],
        "Rotterdam Bin A",
        parent_location_id=places["rotterdam"].id,
    )
    record_movement(
        session,
        places["tenant"],
        "transfer",
        places["item"].id,
        2,
        from_location_id=places["rotterdam"].id,
        to_location_id=bin_a.id,
    )
    parent = metrics(stock_inspector(session, places["tenant"], pair(places)))
    child = metrics(
        stock_inspector(session, places["tenant"], f"{places['item'].id}:{bin_a.id}")
    )
    assert parent["Physical"] == 0
    assert child["Physical"] == 2


@pytest.mark.parametrize("record_id", ["itm_missing:loc_missing", "not-a-pair"])
def test_an_unknown_pair_is_not_found(session, places, record_id):
    with pytest.raises(NotFound):
        stock_inspector(session, places["tenant"], record_id)


def test_item_preview_points_its_location_rows_at_the_pair(session, places):
    sections = operational_preview(session, places["tenant"], "item", places["item"].id)
    row = rows(sections)[places["rotterdam"].name]
    assert row["link"] == {"kind": "stock", "id": pair(places)}


def test_location_stock_rows_point_at_the_pair_and_carry_the_unit(session, places):
    payload = location_inspector(session, places["tenant"], places["rotterdam"].id)
    stock = section(payload["sections"], "Physical stock by item")
    row = next(
        entry for entry in stock["rows"] if entry["label"] == places["item"].name
    )
    assert row["link"] == {"kind": "stock", "id": pair(places)}
    assert places["item"].unit in row["value"]


def quantities(row):
    return tuple(Decimal(row[key]) for key in ("physical", "reserved", "available"))


def register(session, places, view, **options):
    return warehouse_register(session, places["tenant"], view, **options)


def test_scoped_stock_reports_the_quantities_of_that_location(session, places):
    scoped = register(session, places, "stock", location_id=places["rotterdam"].id)
    row = next(r for r in scoped["items"] if r["id"] == places["item"].id)
    assert quantities(row) == (2, 1, 1)
    assert scoped["scope"]["location"] == places["rotterdam"].name
    company = register(session, places, "stock")
    row = next(r for r in company["items"] if r["id"] == places["item"].id)
    assert quantities(row) == (3, 1, 2)


def test_scoped_stock_lists_only_items_with_records_there(session, places):
    quiet = create_item(session, places["tenant"], "QUIET-1", "Never moved")
    scoped = register(session, places, "stock", location_id=places["rotterdam"].id)
    assert quiet.id not in {row["id"] for row in scoped["items"]}
    assert quiet.id in {
        row["id"] for row in register(session, places, "stock")["items"]
    }


def test_scoped_reservations_hold_that_location_only(session, places, business):
    elsewhere = create_commitment(
        session,
        places["tenant"],
        "customer_delivery",
        business.company.id,
        business.customer.id,
        places["item"].id,
        places["singapore"].id,
        1,
        "2026-09-30",
    )
    reserve(session, places["tenant"], elsewhere.id, 1)
    rotterdam = register(
        session, places, "reservations", location_id=places["rotterdam"].id
    )
    assert [row["location_id"] for row in rotterdam["items"]] == [
        places["rotterdam"].id
    ]
    assert register(session, places, "reservations")["page"]["total"] == 2


def test_scoped_movements_match_either_side(session, places):
    rotterdam = register(
        session, places, "movements", location_id=places["rotterdam"].id
    )
    singapore = register(
        session, places, "movements", location_id=places["singapore"].id
    )
    transfer = {row["id"] for row in rotterdam["items"]} & {
        row["id"] for row in singapore["items"]
    }
    assert len(transfer) == 1
    assert rotterdam["page"]["total"] == 2
    assert singapore["page"]["total"] == 1


def test_item_and_location_scope_combine(session, places):
    other = create_item(session, places["tenant"], "OTHER-2", "Other item")
    record_movement(
        session,
        places["tenant"],
        "receipt",
        other.id,
        5,
        to_location_id=places["rotterdam"].id,
    )
    scoped = register(
        session,
        places,
        "movements",
        item_id=places["item"].id,
        location_id=places["rotterdam"].id,
    )
    assert scoped["page"]["total"] == 2
    assert scoped["scope"]["item"] and scoped["scope"]["location"]


def test_shortage_state_applies_to_the_scoped_quantities(session, places):
    record_movement(
        session,
        places["tenant"],
        "shipment",
        places["item"].id,
        2,
        from_location_id=places["rotterdam"].id,
    )
    scoped = register(
        session, places, "stock", state="shortage", location_id=places["rotterdam"].id
    )
    assert [row["id"] for row in scoped["items"]] == [places["item"].id]
    company = register(session, places, "stock", state="shortage")
    assert company["items"] == []


def test_an_unknown_location_scope_is_not_found(session, places):
    with pytest.raises(NotFound):
        register(session, places, "stock", location_id="loc_missing")


def test_a_scoped_stock_page_keeps_the_unscoped_query_shape(session, places):
    def count(**options):
        statements = []

        def listener(conn, cursor, statement, *rest):
            statements.append(statement)

        event.listen(session.bind, "before_cursor_execute", listener)
        try:
            warehouse_register(session, places["tenant"], "stock", **options)
        finally:
            event.remove(session.bind, "before_cursor_execute", listener)
        return len(statements)

    unscoped = count()
    scoped = count(location_id=places["rotterdam"].id)
    # One extra statement is the location itself; a per-pair derivation would be many.
    assert scoped <= unscoped + 1


def location_queries(session, places, item_count):
    """Statements one location read issues, with the company grown by item_count."""
    for index in range(item_count):
        extra = create_item(
            session, places["tenant"], f"EXTRA-{index}", f"Extra {index}"
        )
        record_movement(
            session,
            places["tenant"],
            "receipt",
            extra.id,
            1,
            to_location_id=places["rotterdam"].id,
        )
    session.flush()
    statements = []

    def listener(conn, cursor, statement, *rest):
        statements.append(statement)

    event.listen(session.bind, "before_cursor_execute", listener)
    try:
        location_inspector(session, places["tenant"], places["rotterdam"].id)
    finally:
        event.remove(session.bind, "before_cursor_execute", listener)
    return len(statements)


def test_reading_a_location_does_not_grow_with_the_item_count(session, places):
    small = location_queries(session, places, 5)
    large = location_queries(session, places, 40)
    assert large == small


def test_the_location_record_endpoint_derives_no_stock(session, places):
    from reality.services.core import location_detail
    from reality.web.api import get_location

    statements = []

    def listener(conn, cursor, statement, *rest):
        statements.append(statement)

    event.listen(session.bind, "before_cursor_execute", listener)
    try:
        location_detail(session, places["tenant"], places["rotterdam"].id)
        explanation = len(statements)
        statements.clear()
        get_location(places["tenant"], places["rotterdam"].id, session)
    finally:
        event.remove(session.bind, "before_cursor_execute", listener)
    assert len(statements) < explanation
    assert len(statements) <= 2


def test_location_movements_name_their_item_and_their_direction(session, places):
    payload = location_inspector(session, places["tenant"], places["rotterdam"].id)
    rows = section(payload["sections"], "Recent movements")["rows"]
    assert rows, "the location holds movements"
    for row in rows:
        # The measure states how much and which way; the item it moved qualifies it.
        assert places["item"].unit in row["value"]
        assert places["item"].name in row["meta"]
        assert places["item"].name not in row["value"]
    arriving = next(row for row in rows if row["label"] == "Receipt")
    leaving = next(row for row in rows if row["label"] == "Transfer")
    assert "3" in arriving["value"] and "-" not in arriving["value"].split(" ")[0]
    assert leaving["value"].startswith("-")
    record_movement(
        session,
        places["tenant"],
        "transfer",
        places["item"].id,
        1,
        from_location_id=places["rotterdam"].id,
        to_location_id=places["rotterdam"].id,
    )
    internal = location_inspector(session, places["tenant"], places["rotterdam"].id)
    stayed = section(internal["sections"], "Recent movements")["rows"][0]
    assert stayed["value"].startswith("0")  # it changed nothing here


def test_location_stock_counts_what_it_only_counts(session, places):
    payload = location_inspector(session, places["tenant"], places["rotterdam"].id)
    shown = {row["label"]: row["value"] for row in payload["metrics"]}
    assert shown["Stocked items"] == 1
    assert shown["Movements"] == 2
