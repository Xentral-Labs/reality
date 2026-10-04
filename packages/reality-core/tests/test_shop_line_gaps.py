"""A shop order line without a price or quantity (spec 314 FR-006).

A line without a stated price is kept without an invented one and reported;
a line without a quantity fails the order with a code, in the reported path,
and the rest of the batch goes on.
"""

import json

import pytest
from intake_review_support import accept_import_job, reviewed_record_sales_invoice
from sqlalchemy import select

from reality.db.core import DocumentLine, ImportJob, InterpretationOutcome
from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.invoice_billing import billable_positions

PRICED = {"id": 71, "sku": "BIKE-LIGHT", "quantity": 2, "price": "10.00"}


def _payload(order_id, *lines, updated_at="2026-09-01T10:00:00Z"):
    return {
        "id": order_id,
        "name": f"#{order_id}",
        "currency": "EUR",
        "total_price": "20.00",
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": updated_at,
        "line_items": list(lines),
    }


def _enqueue(session, business, payload):
    return core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )


def _intake(session, business, payload):
    source, job = _enqueue(session, business, payload)
    return source, accept_import_job(session, business.tenant.id, job.id)


def _findings(session, business, class_id):
    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == class_id
    }


def _lines(session, business, document_id):
    return {
        line.source_line_id: line
        for line in session.scalars(
            select(DocumentLine).where(
                DocumentLine.tenant_id == business.tenant.id,
                DocumentLine.document_id == document_id,
            )
        )
    }


@pytest.mark.parametrize(
    "unpriced",
    [
        {"id": 72, "sku": "BIKE-LIGHT", "quantity": 1},
        {"id": 72, "sku": "BIKE-LIGHT", "quantity": 1, "price": None},
    ],
    ids=["missing", "null"],
)
def test_a_line_without_a_price_is_kept_without_one_and_reported(
    session, business, unpriced
):
    _, interpreted = _intake(session, business, _payload(7001, PRICED, unpriced))

    document = interpreted[1]
    lines = _lines(session, business, document.id)
    assert lines["71"].unit_price == 10
    assert lines["72"].unit_price is None
    assert json.loads(lines["72"].payload) == unpriced
    # Both lines are promised; nothing can be billed from a price nobody stated.
    assert sorted(c.quantity for c in interpreted[3]) == [1, 2]
    # Only the unpriced line is reported; the priced one is the control.
    findings = _findings(session, business, "order_line_price_missing")
    assert set(findings) == {lines["72"].id}
    assert findings[lines["72"].id].causal_values["order_number"] == "#7001"


@pytest.mark.parametrize(
    "unquantified",
    [
        {"id": 82, "sku": "BIKE-LIGHT", "price": "10.00"},
        {"id": 82, "sku": "BIKE-LIGHT", "price": "10.00", "quantity": None},
    ],
    ids=["missing", "null"],
)
def test_a_line_without_a_quantity_fails_with_a_code_and_the_batch_goes_on(
    session, business, unquantified
):
    tenant = business.tenant.id
    broken, broken_job = _enqueue(session, business, _payload(8001, unquantified))
    _, good_job = _enqueue(session, business, _payload(8002, PRICED))

    assert core.process_pending_import_jobs(session, tenant) == (1, 1)

    failed = session.get(ImportJob, (tenant, broken_job.id))
    assert failed.status == "failed"
    outcome = session.scalars(
        select(InterpretationOutcome).where(
            InterpretationOutcome.tenant_id == tenant,
            InterpretationOutcome.source_record_id == broken.id,
        )
    ).one()
    assert outcome.classification == "failed"
    assert failed.id in _findings(session, business, "source_interpretation_failure")
    with pytest.raises(core.InvalidOperation) as refused:
        accept_import_job(session, tenant, broken_job.id)
    assert refused.value.code == "source_line_quantity_missing"
    assert session.get(ImportJob, (tenant, good_job.id)).status == "awaiting_decision"
    accept_import_job(session, tenant, good_job.id)
    assert session.get(ImportJob, (tenant, good_job.id)).status == "completed"


def test_a_later_version_stating_the_price_waits_for_review(session, business):
    unpriced = {"id": 92, "sku": "BIKE-LIGHT", "quantity": 1}
    _intake(session, business, _payload(9001, PRICED, unpriced))

    later, held = _intake(
        session,
        business,
        _payload(
            9001,
            PRICED,
            {**unpriced, "price": "12.00"},
            updated_at="2026-09-02T10:00:00Z",
        ),
    )

    assert held is None
    outcome = session.scalars(
        select(InterpretationOutcome)
        .where(
            InterpretationOutcome.tenant_id == business.tenant.id,
            InterpretationOutcome.source_record_id == later.id,
        )
        .order_by(InterpretationOutcome.attempt.desc())
    ).first()
    assert outcome.reason_code == "price_changed"


def test_billing_offers_the_unpriced_position_without_a_price(session, business):
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    unpriced = {"id": 102, "sku": "BIKE-LIGHT", "quantity": 1}
    _, interpreted = _intake(session, business, _payload(10001, unpriced))
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=interpreted[3][0].id,
    )

    (order,) = billable_positions(
        session,
        tenant,
        direction="sales",
        party_id=business.customer.id,
        currency="EUR",
    )["orders"]
    (position,) = order["positions"]
    assert (position["billable"], position["unit_price"]) == (1, None)

    # The person states what is billed; the invoice line states no unit price either.
    reviewed_record_sales_invoice(
        session,
        tenant,
        lines=[
            {
                "order_line_id": position["order_line_id"],
                "quantity": "1",
                "gross_amount": "11.00",
            }
        ],
        gross_amount="11.00",
        number="RE-10001",
    )
    (billed,) = session.scalars(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant,
            DocumentLine.billed_document_line_id == position["order_line_id"],
        )
    )
    assert (billed.unit_price, billed.gross_amount) == (None, 11)
    # Deriving every class reads the unpriced pair without failing; the price
    # comparison has nothing to compare on either side.
    assert billed.id not in _findings(session, business, "invoice_price_differs")


def test_a_billed_unpriced_line_is_no_longer_reported(session, business):
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    unpriced = {"id": 112, "sku": "BIKE-LIGHT", "quantity": 1}
    _, interpreted = _intake(session, business, _payload(11001, unpriced))
    line = interpreted[2][0]
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=interpreted[3][0].id,
    )
    # Positive control: shipped and still without a price, it is reported.
    assert line.id in _findings(session, business, "order_line_price_missing")

    reviewed_record_sales_invoice(
        session,
        tenant,
        lines=[{"order_line_id": line.id, "quantity": "1", "gross_amount": "11.00"}],
        gross_amount="11.00",
        number="RE-11001",
    )

    # The invoice states what is billed, which closes the gap.
    assert line.id not in _findings(session, business, "order_line_price_missing")


def test_an_unknown_item_without_a_price_can_still_be_assigned(session, business):
    from reality.services.order_line_items import assign_line_item

    tenant = business.tenant.id
    helmet = reviewed_create_item(session, tenant, "HELMET-M", "Helmet M")
    _, interpreted = _intake(
        session,
        business,
        _payload(12001, {"id": 122, "sku": "HELMET-M?", "quantity": 1}),
    )
    (line,) = interpreted[2]
    assert (line.item_id, line.unit_price) == (None, None)

    result = assign_line_item(
        session, tenant, document_line_id=line.id, item_id=helmet.id
    )

    assert result is not None
    (promise,) = session.scalars(
        select(core.Commitment).where(
            core.Commitment.tenant_id == tenant,
            core.Commitment.document_line_id == line.id,
        )
    )
    assert promise.amount == 0


@pytest.mark.parametrize("stated", ["", "  "])
def test_a_blank_price_is_no_price_and_a_blank_quantity_no_quantity(
    session, business, stated
):
    tenant = business.tenant.id
    _, interpreted = _intake(
        session,
        business,
        _payload(
            13001, {"id": 132, "sku": "BIKE-LIGHT", "quantity": 1, "price": stated}
        ),
    )
    assert interpreted[2][0].unit_price is None

    _, job = _enqueue(
        session,
        business,
        _payload(13002, {"id": 133, "sku": "BIKE-LIGHT", "quantity": stated}),
    )
    with pytest.raises(core.InvalidOperation) as refused:
        accept_import_job(session, tenant, job.id)
    assert refused.value.code == "source_line_quantity_missing"


def test_a_person_entering_a_line_states_its_price(session, business):
    from reality.tools.application import confirm_tool, propose_tool

    arguments = {
        "document_type": "sales_order",
        "number": "SO-MAN-1",
        "party_id": business.customer.id,
        "gross_amount": "10.00",
        "lines": [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit": "pcs",
                "unit_price": None,
                "gross_amount": "10.00",
            }
        ],
    }
    proposal = propose_tool(session, business.tenant.id, "document_create", arguments)
    with pytest.raises(core.InvalidOperation) as refused:
        confirm_tool(session, business.tenant.id, proposal.id)
    assert refused.value.code == "manual_line_unit_price_missing"

    # Positive control: a stated 0 is a free line and is accepted.
    arguments["lines"][0]["unit_price"] = "0"
    arguments["number"] = "SO-MAN-2"
    proposal = propose_tool(session, business.tenant.id, "document_create", arguments)
    assert json.loads(confirm_tool(session, business.tenant.id, proposal.id).output)[
        "document_id"
    ]


def test_a_file_row_stating_zero_is_a_free_line(session, business):
    from decimal import Decimal

    from reality.services.file_interpreters import _stated_price

    assert _stated_price({"unit_price": 0}) == Decimal(0)
    assert _stated_price({"unit_price": "0"}) == Decimal(0)
    assert _stated_price({"price": 3}) == Decimal(3)
    assert _stated_price({"unit_price": "", "price": None}) is None
    assert _stated_price({}) is None


from intake_review_support import reviewed_create_item
