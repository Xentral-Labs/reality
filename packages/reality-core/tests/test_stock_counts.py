"""Spec 307: stock counts record what was counted and post the differences."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from reality.db.core import Movement, StockCount, StockCountLine
from reality.services import core
from reality.services.stock_blocks import block_stock
from reality.services.stock_counts import (
    book_as_of,
    record_stock_count,
    review_stock_count,
    stock_count_detail,
)


@pytest.fixture
def lamp(session, business):
    return core.create_item(session, business.tenant.id, "LAMP-307", "Lamp 307")


def _stock(session, business, item, quantity, at=None, lot=None):
    return core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        item.id,
        quantity,
        to_location_id=business.location.id,
        lot_id=lot.id if lot else None,
        occurred_at=at,
    )


def _review(session, business, lines, **extra):
    return review_stock_count(
        session,
        business.tenant.id,
        {"location_id": business.location.id, "lines": lines, **extra},
    )


def _post(session, business, lines, **extra):
    normalized, preview = _review(session, business, lines, **extra)
    count = record_stock_count(session, business.tenant.id, **normalized)
    return count, preview


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def test_a_gain_and_a_loss_are_posted_and_linked_to_their_lines(
    session, business, lamp
):
    tenant = business.tenant.id
    _stock(session, business, business.item, "20")
    _stock(session, business, lamp, "8")

    normalized, preview = _review(
        session,
        business,
        [
            {"item_id": business.item.id, "counted_quantity": "17"},
            {"item_id": lamp.id, "counted_quantity": "9"},
        ],
        note="Month end",
    )
    assert [
        (line["book"], line["counted"], line["difference"]) for line in preview["lines"]
    ] == [("20", "17", "-3"), ("8", "9", "1")]
    # The review records nothing.
    assert (
        session.scalar(select(StockCount.id).where(StockCount.tenant_id == tenant))
        is None
    )

    count = record_stock_count(session, tenant, **normalized)

    assert core.stock_at(session, tenant, business.item.id) == 17
    assert core.stock_at(session, tenant, lamp.id) == 9
    lines = {
        row.item_id: row
        for row in session.scalars(
            select(StockCountLine).where(StockCountLine.stock_count_id == count.id)
        )
    }
    moved = {
        row.id: row
        for row in session.scalars(
            select(Movement).where(
                Movement.id.in_([line.movement_id for line in lines.values()])
            )
        )
    }
    loss = moved[lines[business.item.id].movement_id]
    gain = moved[lines[lamp.id].movement_id]
    assert (loss.type, loss.from_location_id, loss.quantity) == (
        "adjustment",
        business.location.id,
        3,
    )
    assert (gain.type, gain.to_location_id, gain.quantity) == (
        "adjustment",
        business.location.id,
        1,
    )
    detail = stock_count_detail(session, tenant, count.id)
    assert detail["note"] == "Month end"
    assert [line["difference"] for line in detail["lines"]] == ["-3", "1"]


def test_a_line_equal_to_the_book_posts_nothing(session, business):
    _stock(session, business, business.item, "5")

    count, preview = _post(
        session, business, [{"item_id": business.item.id, "counted_quantity": "5"}]
    )

    (line,) = session.scalars(
        select(StockCountLine).where(StockCountLine.stock_count_id == count.id)
    )
    assert (preview["lines"][0]["difference"], line.movement_id) == ("0", None)


def test_the_book_is_read_at_the_counting_time(session, business):
    """J03: a shipment after the line was counted is not part of its difference."""
    tenant = business.tenant.id
    counted_at = datetime.now(UTC) - timedelta(hours=1)
    _stock(session, business, business.item, "10", at=counted_at - timedelta(days=1))
    core.record_movement(
        session,
        tenant,
        "adjustment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        reason="picked after the count",
        occurred_at=counted_at + timedelta(minutes=30),
    )
    assert (
        book_as_of(
            session, tenant, business.item.id, business.location.id, None, counted_at
        )
        == 10
    )

    _post(
        session,
        business,
        [
            {
                "item_id": business.item.id,
                "counted_quantity": "9",
                "counted_at": counted_at.isoformat(),
            }
        ],
    )

    # 9 counted against 10 at the counting time: -1, beside the later -2.
    assert core.stock_at(session, tenant, business.item.id) == 7


def test_a_loss_takes_free_stock_first_then_blocks(session, business):
    tenant = business.tenant.id
    _stock(session, business, business.item, "10")
    block = block_stock(
        session, tenant, business.item.id, business.location.id, "4", "quality"
    )

    _, preview = _post(
        session, business, [{"item_id": business.item.id, "counted_quantity": "3"}]
    )

    assert (preview["lines"][0]["from_free"], preview["lines"][0]["from_blocks"]) == (
        "6",
        "1",
    )
    assert core.stock_at(session, tenant, business.item.id) == 3
    assert core.blocked_quantity(session, tenant, business.item.id) == 3
    assert core.blocked_quantity(session, tenant, business.item.id) < Decimal(
        block.quantity
    )


def test_a_loss_beyond_what_is_there_now_is_refused(session, business):
    tenant = business.tenant.id
    counted_at = datetime.now(UTC) - timedelta(hours=1)
    _stock(session, business, business.item, "5", at=counted_at - timedelta(days=1))
    core.record_movement(
        session,
        tenant,
        "adjustment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        reason="all left after the count",
        occurred_at=counted_at + timedelta(minutes=5),
    )

    _refused(
        "stock_count_loss_exceeds_stock",
        lambda: _post(
            session,
            business,
            [
                {
                    "item_id": business.item.id,
                    "counted_quantity": "2",
                    "counted_at": counted_at.isoformat(),
                }
            ],
        ),
    )


def test_a_lot_is_counted_by_its_lot(session, business):
    tenant = business.tenant.id
    item = core.create_item(session, tenant, "LOT-307", "Lot 307", tracking_type="lot")
    first = core.create_lot(session, tenant, item.id, "L-1")
    second = core.create_lot(session, tenant, item.id, "L-2")
    _stock(session, business, item, "5", lot=first)
    _stock(session, business, item, "5", lot=second)

    _post(
        session,
        business,
        [{"item_id": item.id, "lot_id": first.id, "counted_quantity": "4"}],
    )

    assert (
        core.stock_by_identity(
            session, tenant, item.id, business.location.id, lot_id=first.id
        )
        == 4
    )
    assert (
        core.stock_by_identity(
            session, tenant, item.id, business.location.id, lot_id=second.id
        )
        == 5
    )
    _refused(
        "stock_count_lot_required",
        lambda: _review(
            session, business, [{"item_id": item.id, "counted_quantity": "1"}]
        ),
    )


def test_the_review_names_the_reservations_a_loss_leaves_uncovered(session, business):
    """R07: three reservations against 12; a count finds 9."""
    tenant = business.tenant.id
    _stock(session, business, business.item, "12")
    promises = [
        core.create_commitment(
            session,
            tenant,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            business.item.id,
            business.location.id,
            "4",
            "2026-10-20",
        )
        for _ in range(3)
    ]
    for promise in promises:
        core.reserve(session, tenant, promise.id)
    # Positive control: a count that finds everything names nobody.
    _, unchanged = _review(
        session, business, [{"item_id": business.item.id, "counted_quantity": "12"}]
    )
    assert unchanged["uncovered"] == []

    _, preview = _review(
        session, business, [{"item_id": business.item.id, "counted_quantity": "9"}]
    )

    (item,) = preview["uncovered"]
    assert (item["reserved"], item["physical_after"]) == ("12", "9")
    assert {row["commitment_id"] for row in item["reservations"]} == {
        promise.id for promise in promises
    }


def test_counts_are_refused_with_their_code(session, business, lamp):
    tenant = business.tenant.id
    serial = core.create_item(
        session, tenant, "SER-307", "Serial 307", tracking_type="serial"
    )
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    for code, lines in (
        ("stock_count_lines_required", []),
        (
            "stock_count_item_not_found",
            [{"item_id": "itm_nope", "counted_quantity": "1"}],
        ),
        ("stock_count_serial_item", [{"item_id": serial.id, "counted_quantity": "1"}]),
        (
            "stock_count_quantity_invalid",
            [{"item_id": lamp.id, "counted_quantity": "-1"}],
        ),
        (
            "stock_count_time_in_future",
            [{"item_id": lamp.id, "counted_quantity": "1", "counted_at": future}],
        ),
        (
            "stock_count_line_twice",
            [
                {"item_id": lamp.id, "counted_quantity": "1"},
                {"item_id": lamp.id, "counted_quantity": "2"},
            ],
        ),
    ):
        _refused(code, lambda lines=lines: _review(session, business, lines))
    other = core.create_location(session, tenant, "Transit", allows_stock=False)
    _refused(
        "stock_count_location_not_stock",
        lambda: review_stock_count(
            session,
            tenant,
            {
                "location_id": other.id,
                "lines": [{"item_id": lamp.id, "counted_quantity": "1"}],
            },
        ),
    )
    # Positive control.
    assert _review(session, business, [{"item_id": lamp.id, "counted_quantity": "1"}])


def test_a_confirmation_after_the_book_changed_is_refused(session, business):
    tenant = business.tenant.id
    counted_at = datetime.now(UTC) - timedelta(hours=1)
    _stock(session, business, business.item, "10", at=counted_at - timedelta(days=1))
    normalized, _ = _review(
        session,
        business,
        [
            {
                "item_id": business.item.id,
                "counted_quantity": "8",
                "counted_at": counted_at.isoformat(),
            }
        ],
    )
    # A movement stated before the counting time arrives afterwards.
    _stock(session, business, business.item, "1", at=counted_at - timedelta(minutes=5))

    _refused(
        "stock_count_changed_since_review",
        lambda: record_stock_count(session, tenant, **normalized),
    )


def test_another_company_cannot_count_here(session, business):
    other = core.create_tenant(session, "Other GmbH")

    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        review_stock_count(
            session,
            other.id,
            {
                "location_id": business.location.id,
                "lines": [{"item_id": business.item.id, "counted_quantity": "1"}],
            },
        )
    # Not disclosed: the location is unknown to the other company.
    assert refused.value.code == "stock_count_location_not_stock"


def test_the_tables_refuse_what_no_count_can_say(session, business):
    _stock(session, business, business.item, "5")
    count, _ = _post(
        session, business, [{"item_id": business.item.id, "counted_quantity": "4"}]
    )
    (line,) = session.scalars(
        select(StockCountLine).where(StockCountLine.stock_count_id == count.id)
    )
    with pytest.raises(IntegrityError), session.begin_nested():
        session.execute(
            text("UPDATE stock_count_line SET counted_quantity = -1 WHERE id = :id"),
            {"id": line.id},
        )


# --- review round (T013) ---------------------------------------------------------------


def test_the_same_sheet_counted_twice_posts_its_loss_once(session, business):
    tenant = business.tenant.id
    counted_at = datetime.now(UTC) - timedelta(hours=1)
    _stock(session, business, business.item, "20", at=counted_at - timedelta(days=1))
    line = {
        "item_id": business.item.id,
        "counted_quantity": "17",
        "counted_at": counted_at.isoformat(),
    }
    _post(session, business, [line])

    _, again = _post(session, business, [line])

    # The first count's adjustment is dated at its counting time, so the
    # second sees the book it left: nothing more is posted.
    assert again["lines"][0]["difference"] == "0"
    assert core.stock_at(session, tenant, business.item.id) == 17


def test_a_counting_time_before_the_goods_came_is_refused(session, business):
    received = datetime.now(UTC) - timedelta(days=10)
    _stock(session, business, business.item, "20", at=received)

    _refused(
        "stock_count_time_before_stock",
        lambda: _review(
            session,
            business,
            [
                {
                    "item_id": business.item.id,
                    "counted_quantity": "17",
                    "counted_at": (received - timedelta(days=365)).isoformat(),
                }
            ],
        ),
    )
    # Positive control: a time after the receipt is accepted.
    assert _review(
        session,
        business,
        [
            {
                "item_id": business.item.id,
                "counted_quantity": "17",
                "counted_at": (received + timedelta(hours=1)).isoformat(),
            }
        ],
    )


def test_a_counting_time_without_its_offset_is_refused(session, business):
    _stock(session, business, business.item, "5")

    _refused(
        "stock_count_time_needs_offset",
        lambda: _review(
            session,
            business,
            [
                {
                    "item_id": business.item.id,
                    "counted_quantity": "4",
                    "counted_at": "2026-10-02T10:00:00",
                }
            ],
        ),
    )


def test_a_block_placed_after_the_review_refuses_the_confirmation(session, business):
    tenant = business.tenant.id
    _stock(session, business, business.item, "10")
    normalized, preview = _review(
        session, business, [{"item_id": business.item.id, "counted_quantity": "7"}]
    )
    assert preview["lines"][0]["from_blocks"] == "0"

    block_stock(session, tenant, business.item.id, business.location.id, "8", "quality")

    _refused(
        "stock_count_changed_since_review",
        lambda: record_stock_count(session, tenant, **normalized),
    )


def test_a_corrected_movement_is_not_in_the_book(session, business):
    tenant = business.tenant.id
    counted_at = datetime.now(UTC) - timedelta(hours=1)
    _stock(session, business, business.item, "5", at=counted_at - timedelta(days=1))
    wrong = _stock(
        session, business, business.item, "10", at=counted_at - timedelta(hours=2)
    )
    core.correct_movement(session, tenant, wrong.id, reason="Booked twice")

    assert (
        book_as_of(
            session, tenant, business.item.id, business.location.id, None, counted_at
        )
        == 5
    )


def test_the_block_part_of_a_loss_cites_the_count(session, business):
    from reality.db.core import StockBlockResolution

    tenant = business.tenant.id
    _stock(session, business, business.item, "10")
    block = block_stock(
        session, tenant, business.item.id, business.location.id, "4", "quality"
    )

    count, _ = _post(
        session,
        business,
        [{"item_id": business.item.id, "counted_quantity": "3"}],
        note="Month end",
    )

    (resolution,) = session.scalars(
        select(StockBlockResolution).where(StockBlockResolution.block_id == block.id)
    )
    assert (resolution.kind, resolution.quantity) == ("scrap", 1)
    assert resolution.reason == f"count {count.id}: Month end"
    detail = stock_count_detail(session, tenant, count.id)
    assert (detail["lines"][0]["difference"], detail["lines"][0]["book"]) == (
        "-7",
        "10",
    )


def test_replaying_the_same_confirmation_records_nothing_twice(session, business):
    from reality.tools.application import create_change_proposal

    tenant = business.tenant.id
    _stock(session, business, business.item, "10")
    lines = [{"item_id": business.item.id, "counted_quantity": "8"}]
    proposal = create_change_proposal(
        session,
        tenant,
        "stock_count",
        {"location_id": business.location.id, "lines": lines},
    )
    normalized, _ = _review(session, business, lines)

    first = record_stock_count(session, tenant, **normalized, action_id=proposal.id)
    again = record_stock_count(session, tenant, **normalized, action_id=proposal.id)

    assert first.id == again.id
    assert core.stock_at(session, tenant, business.item.id) == 8
