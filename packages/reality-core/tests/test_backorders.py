"""Spec 305: serving backorders, the split of assigned supply, available-to-promise."""

from decimal import Decimal

from reality.services import core
from reality.services.supply_assignments import (
    assign_supply,
    reverse_supply_assignment,
    supply_coverage,
)


def _promise(session, business, quantity, due="2026-10-20", location=None):
    return core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        (location or business.location).id,
        quantity,
        due,
    )


def _purchase(session, business, quantity, due="2026-10-12"):
    return core.create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        quantity,
        due,
    )


def _assign(session, business, purchase, promise, quantity, request):
    return assign_supply(
        session,
        business.tenant.id,
        purchase.id,
        quantity,
        purpose="customer_demand",
        customer_commitment_id=promise.id,
        request_id=request,
    )


def _receive(session, business, purchase, quantity):
    return core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        commitment_id=purchase.id,
    )


def _split(session, business, promise):
    customer = supply_coverage(
        session, business.tenant.id, customer_commitment_id=promise.id
    )["customer"]
    return customer["arrived"], customer["still_to_come"]


# --- split of assigned supply (FR-006) -------------------------------------------------


def test_a_partial_receipt_covers_the_assignments_in_their_order(session, business):
    purchase = _purchase(session, business, "9")
    promises = [_promise(session, business, "3") for _ in range(3)]
    for n, promise in enumerate(promises):
        _assign(session, business, purchase, promise, "3", f"split-{n}")
    # Positive control: before anything arrives, everything is still to come.
    assert [_split(session, business, p) for p in promises] == [(0, 3)] * 3

    _receive(session, business, purchase, "4")

    assert [_split(session, business, p) for p in promises] == [
        (3, 0),
        (1, 2),
        (0, 3),
    ]
    items = supply_coverage(
        session, business.tenant.id, supplier_commitment_id=purchase.id
    )["items"]
    assert [(row["arrived"], row["still_to_come"]) for row in items] == [
        (3, 0),
        (1, 2),
        (0, 3),
    ]
    # The total stays what was assigned.
    assert supply_coverage(
        session, business.tenant.id, customer_commitment_id=promises[1].id
    )["customer"]["protecting_supply"] == Decimal(3)


def test_a_cancelled_or_reversed_assignment_leaves_the_order(session, business):
    purchase = _purchase(session, business, "9")
    first, second, third = (_promise(session, business, "3") for _ in range(3))
    reversed_row = _assign(session, business, purchase, first, "3", "order-1")
    _assign(session, business, purchase, second, "3", "order-2")
    _assign(session, business, purchase, third, "3", "order-3")
    reverse_supply_assignment(
        session,
        business.tenant.id,
        reversed_row.id,
        "3",
        reason="Customer takes stock instead",
        request_id="order-reverse",
    )
    core.cancel_commitment(
        session, business.tenant.id, second.id, reason="Customer withdrew"
    )

    _receive(session, business, purchase, "4")

    assert _split(session, business, third) == (3, 0)


# --- serving backorders (FR-001) -------------------------------------------------------


def _stock(session, business, quantity, location=None):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=(location or business.location).id,
    )


def _review(session, business, **arguments):
    from reality.services.backorders import review_backorder_serving

    return review_backorder_serving(
        session,
        business.tenant.id,
        {"item_id": business.item.id, "location_id": business.location.id} | arguments,
    )


def _lines(preview):
    return [
        (line["commitment_id"], line["quantity"], line["why"])
        for line in preview["lines"]
    ]


def test_the_earlier_due_promise_is_served_first(session, business):
    later = _promise(session, business, "3", due="2026-10-25")
    earlier = _promise(session, business, "3", due="2026-10-15")
    _stock(session, business, "4")

    normalized, preview = _review(session, business)

    assert _lines(preview) == [(earlier.id, "3", "due"), (later.id, "1", "due")]
    assert (preview["available"], preview["reserving"], preview["free_after"]) == (
        "4",
        "4",
        "0",
    )
    # Nothing is reserved by the review.
    assert (
        core.active_reserved(
            session, business.tenant.id, business.item.id, business.location.id
        )
        == 0
    )
    assert normalized["lines"] == [
        {"commitment_id": earlier.id, "quantity": "3"},
        {"commitment_id": later.id, "quantity": "1"},
    ]


def test_the_assigned_promise_stands_first_even_if_due_later(session, business):
    earlier = _promise(session, business, "3", due="2026-10-15")
    assigned = _promise(session, business, "3", due="2026-10-30")
    purchase = _purchase(session, business, "3")
    _assign(session, business, purchase, assigned, "3", "first-assigned")
    _receive(session, business, purchase, "3")

    _, without = _review(session, business)
    _, served = _review(session, business, supplier_commitment_id=purchase.id)

    # Positive control: without naming the purchase, due date decides.
    assert _lines(without)[0] == (earlier.id, "3", "due")
    assert _lines(served) == [(assigned.id, "3", "assigned"), (earlier.id, "0", "due")]


def test_stated_lines_are_checked(session, business):
    first = _promise(session, business, "3", due="2026-10-15")
    second = _promise(session, business, "3", due="2026-10-16")
    other = core.create_location(session, business.tenant.id, "Elsewhere")
    elsewhere = _promise(session, business, "3", location=other)
    _stock(session, business, "4")

    normalized, preview = _review(
        session,
        business,
        lines=[
            {"commitment_id": first.id, "quantity": "0"},
            {"commitment_id": second.id, "quantity": "3"},
        ],
    )
    assert normalized["lines"] == [{"commitment_id": second.id, "quantity": "3"}]
    assert preview["reserving"] == "3"

    for lines, code in (
        (
            [{"commitment_id": elsewhere.id, "quantity": "1"}],
            "backorder_serving_line_not_waiting",
        ),
        (
            [{"commitment_id": first.id, "quantity": "4"}],
            "backorder_serving_line_exceeds_need",
        ),
        (
            [
                {"commitment_id": first.id, "quantity": "3"},
                {"commitment_id": second.id, "quantity": "2"},
            ],
            "backorder_serving_exceeds_available",
        ),
        (
            [{"commitment_id": first.id, "quantity": "0"}],
            "backorder_serving_nothing_to_serve",
        ),
        (
            [{"commitment_id": first.id, "quantity": "x"}],
            "backorder_serving_line_quantity_invalid",
        ),
    ):
        try:
            _review(session, business, lines=lines)
        except core.InvalidOperation as error:
            assert error.code == code, (lines, error.code)
        else:
            raise AssertionError(f"accepted {lines}")


def test_a_held_promise_is_listed_apart_and_not_served(session, business):
    held = _promise(session, business, "3", due="2026-10-10")
    waiting = _promise(session, business, "3", due="2026-10-20")
    core.hold_commitment(session, business.tenant.id, held.id, "customer_request")
    _stock(session, business, "3")

    _, preview = _review(session, business)

    assert _lines(preview) == [(waiting.id, "3", "due")]
    assert [row["commitment_id"] for row in preview["held"]] == [held.id]


def test_blocked_stock_is_not_served(session, business):
    from reality.services.stock_blocks import block_stock

    _promise(session, business, "5")
    _stock(session, business, "5")
    block_stock(
        session,
        business.tenant.id,
        business.item.id,
        business.location.id,
        "3",
        "quality",
    )

    _, preview = _review(session, business)

    assert (preview["available"], preview["reserving"]) == ("2", "2")


def test_a_tracked_item_is_refused(session, business):
    item = core.create_item(
        session, business.tenant.id, "LOT-305", "Lot item", tracking_type="lot"
    )
    try:
        _review(session, business, item_id=item.id)
    except core.InvalidOperation as error:
        assert error.code == "backorder_serving_tracked_item"
    else:
        raise AssertionError("a tracked item was served")


def test_serving_reserves_the_confirmed_lines(session, business):
    from reality.services.backorders import serve_backorders

    first = _promise(session, business, "3", due="2026-10-15")
    second = _promise(session, business, "3", due="2026-10-16")
    _stock(session, business, "4")
    normalized, _ = _review(session, business)

    result = serve_backorders(
        session,
        business.tenant.id,
        business.item.id,
        business.location.id,
        normalized["lines"],
    )

    assert [row["quantity"] for row in result["reservations"]] == ["3", "1"]
    terms = core.commitment_terms(session, business.tenant.id, [first.id, second.id])
    assert (terms[first.id].reserved, terms[second.id].reserved) == (3, 1)


def test_a_confirmation_after_the_stock_changed_is_refused(session, business):
    from reality.services.backorders import serve_backorders

    first = _promise(session, business, "3", due="2026-10-15")
    _stock(session, business, "3")
    normalized, _ = _review(session, business)
    # Someone else takes the stock first.
    core.reserve(session, business.tenant.id, _promise(session, business, "3").id)

    try:
        serve_backorders(
            session,
            business.tenant.id,
            business.item.id,
            business.location.id,
            normalized["lines"],
        )
    except core.InvalidOperation as error:
        assert error.code == "backorder_serving_changed_since_review"
    else:
        raise AssertionError("a stale serving was executed")
    assert (
        core.commitment_terms(session, business.tenant.id, [first.id])[
            first.id
        ].reserved
        == 0
    )


# --- available-to-promise (FR-003) -----------------------------------------------------


def _atp(session, business):
    from reality.services.backorders import available_to_promise

    return available_to_promise(session, business.tenant.id, business.item.id)


def test_promise_from_stock_and_open_purchases(session, business):
    """US2: 5 free, a purchase of 10 due 12 Oct with 4 assigned: 5 now, 11 from 12 Oct."""
    _stock(session, business, "5")
    purchase = _purchase(session, business, "10", due="2026-10-12")
    customer = _promise(session, business, "4")
    _assign(session, business, purchase, customer, "4", "atp-assign")

    answer = _atp(session, business)

    assert answer["now"]["free"] == "5"
    (row,) = answer["purchases"]
    assert (
        row["commitment_id"],
        row["due_at"],
        row["assigned_to_come"],
        row["adds"],
        row["total"],
    ) == (
        purchase.id,
        "2026-10-12",
        "4",
        "6",
        "11",
    )


def test_waiting_need_without_supply_takes_from_free_stock(session, business):
    _stock(session, business, "5")
    # Positive control: nothing waits, all 5 are free.
    assert _atp(session, business)["now"]["free"] == "5"
    _promise(session, business, "3")

    answer = _atp(session, business)

    assert (answer["now"]["waiting_uncovered"], answer["now"]["free"]) == ("3", "2")


def test_purchases_follow_their_dates_and_say_when_overdue(session, business):
    late = _purchase(session, business, "4", due="2030-01-10")
    overdue = _purchase(session, business, "2", due="2020-01-10")

    rows = _atp(session, business)["purchases"]

    assert [(row["commitment_id"], row["overdue"], row["total"]) for row in rows] == [
        (overdue.id, True, "2"),
        (late.id, False, "6"),
    ]


def test_a_cancelled_promise_leaves_the_answer(session, business):
    purchase = _purchase(session, business, "10")
    customer = _promise(session, business, "4")
    _assign(session, business, purchase, customer, "4", "atp-cancel")
    assert _atp(session, business)["purchases"][0]["adds"] == "6"

    core.cancel_commitment(session, business.tenant.id, customer.id, reason="Withdrawn")

    answer = _atp(session, business)
    assert (answer["now"]["waiting_uncovered"], answer["purchases"][0]["adds"]) == (
        "0",
        "10",
    )


def test_a_person_confirms_the_reviewed_serving(session, business):
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    first = _promise(session, business, "3", due="2026-10-15")
    _promise(session, business, "3", due="2026-10-16")
    _stock(session, business, "3")

    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "backorders_serve",
        {"item_id": business.item.id, "location_id": business.location.id},
    )
    import json

    preview = json.loads(proposal.output)["backorder_serving"]
    assert [line["quantity"] for line in preview["lines"]] == ["3", "0"]
    assert (
        core.commitment_terms(session, business.tenant.id, [first.id])[
            first.id
        ].reserved
        == 0
    )

    approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )

    assert (
        core.commitment_terms(session, business.tenant.id, [first.id])[
            first.id
        ].reserved
        == 3
    )
