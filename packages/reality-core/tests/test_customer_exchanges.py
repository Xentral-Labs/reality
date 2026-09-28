"""Spec 293: a customer exchange settles a return with a replacement instead of a credit."""

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from reality.db.core import (
    Commitment,
    CustomerExchange,
    LedgerEntry,
    Movement,
    SourceRecord,
)
from reality.services import core, customer_exchanges
from reality.services.decision_attribution import record_decisions
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
)
from reality.services.delivery_reads import delivery_case
from reality.services.movement_explanations import movement_explanation
from reality.tools.application import approve_and_execute_proposal

AS_OF = datetime(2026, 9, 30, 12, tzinfo=UTC)


def _delivered(session, business, quantity="2"):
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    commitment = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        "2026-09-10",
        amount="40.00",
    )
    core.reserve(session, tenant, commitment.id)
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    return commitment


def _returned(session, business, commitment, quantity="1"):
    return core.record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
    )


# --- T005: the record ------------------------------------------------------------


def _exchange_values(session, business, **columns):
    """Everything an exchange row names, created through the services first."""
    tenant = business.tenant.id
    replacement = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        None,
    )
    source = core.create_master_source_record(
        session, tenant, "customer_exchange", "manual", core.uid("t005"), {}
    )
    return {
        "id": core.uid("cex"),
        "tenant_id": tenant,
        "replacement_commitment_id": replacement.id,
        "quantity": Decimal(1),
        "reason": "Wrong size",
        "source_record_id": source.id,
        **columns,
    }


def _insert(session, values):
    with session.begin_nested():
        session.add(CustomerExchange(**values))
        session.flush()


def test_the_exchange_record_names_exactly_one_return_side(session, business):
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    announcement = core.announce_customer_return(
        session, business.tenant.id, commitment.id, 1, reference="RMA-T005"
    )

    # Positive control: one side is enough.
    _insert(
        session, _exchange_values(session, business, return_movement_id=goods_back.id)
    )

    for sides in (
        {},
        {
            "return_movement_id": goods_back.id,
            "return_announcement_id": announcement.id,
        },
    ):
        values = _exchange_values(session, business, **sides)
        with pytest.raises(IntegrityError, match="ck_customer_exchange_one_return"):
            _insert(session, values)


def test_the_exchange_record_refuses_a_non_positive_quantity(session, business):
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    values = _exchange_values(
        session, business, return_movement_id=goods_back.id, quantity=Decimal(0)
    )

    with pytest.raises(IntegrityError, match="ck_customer_exchange_quantity_positive"):
        _insert(session, values)


def test_one_replacement_settles_at_most_one_exchange(session, business):
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    first = _exchange_values(session, business, return_movement_id=goods_back.id)
    _insert(session, first)

    again = _exchange_values(session, business, return_movement_id=goods_back.id)
    again["replacement_commitment_id"] = first["replacement_commitment_id"]
    with pytest.raises(IntegrityError, match="uq_customer_exchange_replacement"):
        _insert(session, again)


# --- T008: recording an exchange after the goods are back -----------------------


def _sold(session, business, number, quantity="2", unit_price="20.00"):
    """An order line delivered and invoiced, as the credit rules need it."""
    tenant = business.tenant.id
    gross = str(Decimal(quantity) * Decimal(unit_price))
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    _, _, lines, commitments = core.create_manual_order(
        session,
        tenant,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit_price": unit_price,
                "gross_amount": gross,
            }
        ],
        gross,
    )
    commitment = commitments[0]
    core.reserve(session, tenant, commitment.id)
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    receipt = core.record_sales_invoice(
        session, tenant, lines[0].id, quantity, gross, f"RE-{number}"
    )
    invoice_line_id = next(
        row["id"] for row in receipt["records"] if row["family"] == "document_line"
    )
    return commitment, lines[0], invoice_line_id


def _credit(session, business, invoice_line_id, quantity, unit_price="20.00"):
    gross = str(Decimal(quantity) * Decimal(unit_price))
    note, _ = core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "credit_note",
        core.uid("GS"),
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit": "pcs",
                "unit_price": unit_price,
                "gross_amount": gross,
                "billed_document_line_id": invoice_line_id,
            }
        ],
        gross,
    )
    return note


def _variant(session, business, sku="BIKE-LIGHT-XL"):
    return core.create_item(session, business.tenant.id, sku, "Bike Light XL")


def _exchange(session, business, **values):
    arguments = {
        "quantity": "1",
        "replacement_quantity": "1",
        "reason": "Customer wants the XL",
        **values,
    }
    arguments.setdefault("replacement_item_id", business.item.id)
    return customer_exchanges.record_customer_exchange(
        session, business.tenant.id, **arguments
    )


def _ledger_count(session, business):
    return session.scalar(
        select(func.count())
        .select_from(LedgerEntry)
        .where(LedgerEntry.tenant_id == business.tenant.id)
    )


def test_an_exchange_after_a_return_promises_a_free_replacement(session, business):
    """US1.1: another variant goes to the same customer, at no price, with no money."""
    tenant = business.tenant.id
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    larger = _variant(session, business)
    ledger_before = _ledger_count(session, business)

    exchange = _exchange(
        session,
        business,
        return_movement_id=goods_back.id,
        replacement_item_id=larger.id,
    )

    assert exchange.return_movement_id == goods_back.id
    assert exchange.return_announcement_id is None
    assert exchange.quantity == Decimal(1)
    assert exchange.reason == "Customer wants the XL"
    replacement = record_by_id(session, Commitment, exchange.replacement_commitment_id)
    assert (replacement.type, replacement.status) == ("customer_delivery", "open")
    assert (replacement.from_party_id, replacement.to_party_id) == (
        commitment.from_party_id,
        commitment.to_party_id,
    )
    assert (replacement.item_id, replacement.quantity) == (larger.id, Decimal(1))
    assert replacement.location_id == commitment.location_id
    assert replacement.amount == Decimal(0)
    assert replacement.document_id is None and replacement.document_line_id is None
    # No money moves: nothing is booked, invoiced, credited, paid or refunded.
    assert _ledger_count(session, business) == ledger_before
    source = record_by_id(session, SourceRecord, exchange.source_record_id)
    assert json.loads(source.payload)["reason"] == "Customer wants the XL"
    # The original promise stays kept (spec 079).
    assert record_by_id(session, Commitment, commitment.id).status == "fulfilled"
    assert core.open_quantity(session, tenant, replacement.id) == Decimal(1)


def test_a_return_is_exchanged_at_most_once_per_unit(session, business):
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment, "2")
    _exchange(session, business, return_movement_id=goods_back.id, quantity="1")
    _exchange(session, business, return_movement_id=goods_back.id, quantity="1")

    with pytest.raises(core.InvalidOperation) as refused:
        _exchange(session, business, return_movement_id=goods_back.id, quantity="1")
    assert refused.value.code == "customer_exchange_exceeds_exchangeable"


def test_a_partly_credited_return_can_exchange_only_the_rest(session, business):
    """US1.3: of two back, one is credited and one exchanged; a third is refused."""
    commitment, _, invoice_line_id = _sold(session, business, "SO-EX-3")
    goods_back = _returned(session, business, commitment, "2")
    _credit(session, business, invoice_line_id, "1")

    _exchange(session, business, return_movement_id=goods_back.id, quantity="1")
    with pytest.raises(core.InvalidOperation) as refused:
        _exchange(session, business, return_movement_id=goods_back.id, quantity="1")
    assert refused.value.code == "customer_exchange_already_credited"


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"quantity": "0"}, "customer_exchange_quantity_not_positive"),
        ({"replacement_quantity": "-1"}, "customer_exchange_quantity_not_positive"),
        ({"quantity": "3"}, "customer_exchange_exceeds_exchangeable"),
        ({"reason": "  "}, "customer_exchange_reason_required"),
    ],
)
def test_an_exchange_refuses_what_it_cannot_state(session, business, change, code):
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment, "2")
    # Positive control: the same exchange without the change is accepted.
    customer_exchanges.preview_customer_exchange(
        session,
        business.tenant.id,
        return_movement_id=goods_back.id,
        quantity="1",
        replacement_item_id=business.item.id,
        replacement_quantity="1",
        reason="Wrong size",
    )

    with pytest.raises(core.InvalidOperation) as refused:
        _exchange(session, business, return_movement_id=goods_back.id, **change)
    assert refused.value.code == code


def test_an_exchange_needs_exactly_one_customer_return(session, business):
    tenant = business.tenant.id
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    announcement = core.announce_customer_return(
        session, tenant, commitment.id, 1, reference="RMA-EX"
    )
    shipment = session.scalars(
        select(Movement).where(
            Movement.tenant_id == tenant,
            Movement.commitment_id == commitment.id,
            Movement.type == "shipment",
        )
    ).one()
    unlinked = core.record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )

    for sides, code in [
        ({}, "customer_exchange_fields_invalid"),
        (
            {
                "return_movement_id": goods_back.id,
                "return_announcement_id": announcement.id,
            },
            "customer_exchange_fields_invalid",
        ),
        ({"return_movement_id": shipment.id}, "customer_exchange_return_not_customer"),
        ({"return_movement_id": unlinked.id}, "customer_exchange_return_unlinked"),
    ]:
        with pytest.raises(core.InvalidOperation) as refused:
            _exchange(session, business, **sides)
        assert refused.value.code == code

    core.withdraw_return_announcement(
        session, tenant, announcement.id, note="Customer keeps it"
    )
    with pytest.raises(core.InvalidOperation) as refused:
        _exchange(session, business, return_announcement_id=announcement.id)
    assert refused.value.code == "customer_exchange_announcement_not_open"


def test_an_exchange_cannot_reach_another_tenant(session, business):
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    other = core.create_tenant(session, "Other GmbH")

    with pytest.raises(core.NotFound):
        customer_exchanges.record_customer_exchange(
            session,
            other.id,
            return_movement_id=goods_back.id,
            quantity="1",
            replacement_item_id=business.item.id,
            replacement_quantity="1",
            reason="Wrong tenant",
        )


# --- T012: the reviewed route ----------------------------------------------------


def _prepare(session, business, request_id, **values):
    arguments = {
        "quantity": "1",
        "replacement_item_id": business.item.id,
        "replacement_quantity": "1",
        "reason": "Wrong size",
        **values,
    }
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "customer_exchange_record",
        arguments,
        request_id=request_id,
    )


def _confirm(session, business, proposal):
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )


def test_the_review_states_what_the_exchange_creates_and_that_no_money_moves(
    session, business
):
    """US1.4 and FR-010."""
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    larger = _variant(session, business)

    proposal = _prepare(
        session,
        business,
        "exchange-review",
        return_movement_id=goods_back.id,
        replacement_item_id=larger.id,
    )
    review = json.loads(proposal.input)["_delivery_review"]
    assert review["effect"] == {
        "returned_delivery_id": commitment.id,
        "return": {"kind": "movement", "id": goods_back.id, "exchangeable": "1"},
        "exchanged_quantity": "1",
        "replacement": {
            "item_id": larger.id,
            "quantity": "1",
            "location_id": commitment.location_id,
        },
        "money_moves": False,
        "creates": ["customer_exchange", "commitment"],
    }
    # Nothing exists before confirmation.
    assert session.scalar(select(func.count()).select_from(CustomerExchange)) == 0

    executed = _confirm(session, business, proposal)
    assert executed.status == "executed"
    receipt = json.loads(executed.output)
    exchange = record_by_id(session, CustomerExchange, receipt["exchange_id"])
    assert exchange.replacement_commitment_id == receipt["replacement_commitment_id"]
    source = record_by_id(session, SourceRecord, exchange.source_record_id)
    assert source.external_id == proposal.id
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    assert {"kind": "customer_exchange", "id": exchange.id} in detail["links"]
    # Replaying the executed proposal changes nothing.
    assert _confirm(session, business, proposal).output == executed.output
    assert session.scalar(select(func.count()).select_from(CustomerExchange)) == 1


def test_a_stale_exchange_review_is_refused(session, business):
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    first = _prepare(session, business, "exchange-a", return_movement_id=goods_back.id)
    second = _prepare(session, business, "exchange-b", return_movement_id=goods_back.id)
    _confirm(session, business, first)

    # The second review saw one unit exchangeable; now there is none.
    with pytest.raises(core.InvalidOperation) as refused:
        _confirm(session, business, second)
    assert refused.value.code == "customer_exchange_exceeds_exchangeable"
    assert session.scalar(select(func.count()).select_from(CustomerExchange)) == 1


def test_a_changed_but_still_valid_exchange_review_must_be_reviewed_again(
    session, business
):
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment, "2")
    first = _prepare(session, business, "exchange-c", return_movement_id=goods_back.id)
    second = _prepare(session, business, "exchange-d", return_movement_id=goods_back.id)
    _confirm(session, business, first)

    # One unit is still exchangeable, but not the two the second review saw.
    with pytest.raises(core.InvalidOperation) as refused:
        _confirm(session, business, second)
    assert refused.value.code == "review_delivery_changed"


def test_the_review_refuses_fields_the_contract_does_not_name(session, business):
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)

    with pytest.raises(core.InvalidOperation) as refused:
        _prepare(
            session,
            business,
            "exchange-extra",
            return_movement_id=goods_back.id,
            refund="20.00",
        )
    assert refused.value.code == "customer_exchange_fields_invalid"


# --- T013: a cancelled replacement stops settling the return --------------------


def test_cancelling_the_replacement_ends_what_the_exchange_settles(session, business):
    """FR-008: before it ships, a cancelled replacement settles nothing."""
    tenant = business.tenant.id
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    exchange = _exchange(session, business, return_movement_id=goods_back.id)
    assert customer_exchanges.settled_by_delivery(session, tenant) == {
        commitment.id: Decimal(1)
    }

    core.cancel_commitment(
        session, tenant, exchange.replacement_commitment_id, reason="Out of stock"
    )

    assert customer_exchanges.settled_by_delivery(session, tenant) == {}
    detail = customer_exchanges.customer_exchange_detail(
        session, tenant, exchange_id=exchange.id
    )
    assert (detail["settles"], detail["replacement"]["status"]) == ("0", "cancelled")
    # The returned unit can be exchanged again, or credited.
    _exchange(session, business, return_movement_id=goods_back.id)


def test_a_partly_shipped_then_cancelled_replacement_settles_what_left(
    session, business
):
    tenant = business.tenant.id
    commitment = _delivered(session, business, "4")
    goods_back = _returned(session, business, commitment, "2")
    exchange = _exchange(
        session,
        business,
        return_movement_id=goods_back.id,
        quantity="2",
        replacement_quantity="2",
    )
    core.reserve(session, tenant, exchange.replacement_commitment_id)
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=exchange.replacement_commitment_id,
    )

    core.cancel_commitment(
        session, tenant, exchange.replacement_commitment_id, reason="Rest refunded"
    )

    assert customer_exchanges.settled_by_delivery(session, tenant) == {
        commitment.id: Decimal(1)
    }


# --- T017: both sides and the decision explain each other -----------------------


def _links(explanation):
    return {(link["kind"], link["id"]) for link in explanation["links"]}


def test_the_returned_goods_name_their_exchange_and_replacement(session, business):
    """US3.1: the return's explanation says what answered it."""
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    before = movement_explanation(session, business.tenant.id, goods_back.id)
    assert ("customer_exchange", None) not in _links(before)
    assert not any(link["kind"] == "customer_exchange" for link in before["links"])

    exchange = _exchange(session, business, return_movement_id=goods_back.id)

    explained = movement_explanation(session, business.tenant.id, goods_back.id)
    # What the movement is stays what it was: goods back on their delivery.
    assert explained["kind"] == before["kind"] == "commitment"
    assert {
        ("customer_exchange", exchange.id),
        ("commitment", exchange.replacement_commitment_id),
    } <= _links(explained)


def test_announced_goods_that_arrive_name_the_advance_exchange(session, business):
    tenant = business.tenant.id
    commitment = _delivered(session, business)
    announcement = core.announce_customer_return(
        session, tenant, commitment.id, 1, reference="RMA-EXPLAIN"
    )
    exchange = _exchange(session, business, return_announcement_id=announcement.id)

    arrived = core.record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "1",
        to_location_id=business.location.id,
        commitment_id=commitment.id,
        return_announcement_id=announcement.id,
    )

    explained = movement_explanation(session, tenant, arrived.id)
    assert explained["kind"] == "return_announcement"
    assert ("customer_exchange", exchange.id) in _links(explained)


def test_the_replacement_names_its_exchange_and_the_delivery_it_replaces(
    session, business
):
    """US3.2: from the replacement side, the free delivery is explained."""
    tenant = business.tenant.id
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    exchange = _exchange(session, business, return_movement_id=goods_back.id)
    core.reserve(session, tenant, exchange.replacement_commitment_id)
    sent = core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=exchange.replacement_commitment_id,
    )

    explained = movement_explanation(session, tenant, sent.id)
    assert explained["kind"] == "commitment"
    assert {
        ("commitment", exchange.replacement_commitment_id),
        ("customer_exchange", exchange.id),
        ("commitment", commitment.id),
    } <= _links(explained)

    case = delivery_case(session, tenant, exchange.replacement_commitment_id)
    assert {
        ("customer_exchange", exchange.id),
        ("commitment", commitment.id),
        ("movement", goods_back.id),
    } <= {(link["kind"], link["id"]) for link in case["links"]}
    # Positive control: an ordinary delivery names no exchange.
    ordinary = delivery_case(session, tenant, commitment.id)
    assert not any(link["kind"] == "customer_exchange" for link in ordinary["links"])


def test_the_exchange_names_who_confirmed_it_when_and_why(session, business):
    """US3.3: the decision behind the exchange, from its own detail view."""
    commitment = _delivered(session, business)
    goods_back = _returned(session, business, commitment)
    proposal = _prepare(
        session, business, "exchange-decision", return_movement_id=goods_back.id
    )
    receipt = json.loads(_confirm(session, business, proposal).output)

    decisions = record_decisions(
        session, business.tenant.id, "customer_exchange", receipt["exchange_id"]
    )
    assert [(row["role"], row["id"], row["tool"]) for row in decisions] == [
        ("created", proposal.id, "customer_exchange_record")
    ]
    assert decisions[0]["decided_at"] and decisions[0]["decider"]
    detail = customer_exchanges.customer_exchange_detail(
        session, business.tenant.id, exchange_id=receipt["exchange_id"]
    )
    assert (detail["reason"], detail["action_id"]) == ("Wrong size", proposal.id)
