"""Which exception classes answer differently when only the clock moves.

`exceptions` is the one projection still refreshed every sixty seconds for every
company, because some of its classes judge a record against the moment it is read.
Spec 181 FR-004 wants that cadence taken apart, and the first thing that needs is a
list of the classes it exists for — measured, not recalled, the way
`test_clock_sensitivity.py` measures which projections read the clock at all.

The probe here is universal: the same company, derived twice, four hundred days
apart, with nothing else changed. A class that answers the same does not read the
clock; one that answers differently does.

The *other* property this work wants — whether a class's verdict about one record can
be changed by another record — has no universal probe, and a first attempt to measure
it was wrong in a way worth recording. Adding an unrelated record says nothing,
because "unrelated" is what each class defines differently: for `credit_limit_exceeded`
it is another invoice of the same party, for `duplicate_supplier_invoice` another
invoice under the same number, and for a class with a learned threshold it is any
finished promise at all. Both of those were measured as record-local by such a probe,
and both are company-wide. That property therefore belongs with each class's own
narrowing, tested per class, and not in a table filled in advance.
"""

import datetime as dt
import json

from reality.services import exceptions as exception_services
from reality.services.core import (
    create_commitment,
    create_document,
    hold_commitment,
    hold_party_delivery,
    post_sales_invoice,
    record_customer_payment,
    record_movement,
    reserve,
    revise_commitment,
)

#: Measured by the test below, not declared for it to confirm.
CLOCK_READING = {
    "overdue_outgoing_customer_commitment",
    "overdue_incoming_supplier_commitment",
    "overdue_receivable",
}
#: Classes this fixture does not bring about at all. They are named so the gap is
#: visible and shrinks when someone gives them a scenario; a class that starts
#: producing rows here fails the test until it is moved out of this list.
WITHOUT_A_SCENARIO = {
    "outgoing_commitment_at_risk",
    "order_stalled",
    "shipped_not_billed",
    "billed_not_received",
    "invoice_price_differs",
    "sold_below_purchase_price",
    "returned_not_credited",
    "credited_not_returned",
    "supplier_return_not_credited",
    "supplier_credit_not_returned",
    "return_unresolved",
    "receipt_unbilled",
    "units_not_comparable",
    "reservation_exceeds_stock",
    "silent_source",
    "source_interpretation_failure",
    "sales_invoice_unposted",
    "supplier_invoice_unposted",
    "credit_note_unposted",
    "credit_note_unsettled",
    "supplier_credit_unposted",
    "supplier_credit_unclaimed",
    "overdue_payable",
    "purchase_discount_available",
    "announced_return_not_arrived",
    "commitment_hold_unreleased",
    "party_hold_unreleased",
    "stock_expired",
}


def _rows_by_id(session, tenant, as_of=None):
    """Every row by its id, so a new row is not mistaken for a changed verdict."""
    rows = exception_services.operational_exception_rows(session, tenant, as_of=as_of)
    return {
        row["id"]: (row["class_id"], json.dumps(row, sort_keys=True, default=str))
        for row in rows
    }


def _classes_that_changed(before, after):
    """Classes where a row that existed before now says something else, or is gone."""
    changed = set()
    for row_id, (class_id, payload) in before.items():
        if row_id not in after or after[row_id][1] != payload:
            changed.add(class_id)
    return changed


def _rich_company(session, business):
    tenant = business.tenant.id
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "30",
        to_location_id=business.location.id,
    )
    order = create_document(
        session,
        tenant,
        "sales_order",
        "ORD-M1",
        business.customer.id,
        "100",
        document_date="2026-08-01",
    )
    overdue = create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "4",
        "2026-08-10T00:00:00+00:00",
        document_id=order.id,
    )
    ahead = create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "2",
        "2099-01-01T00:00:00+00:00",
        document_id=order.id,
    )
    revise_commitment(
        session,
        tenant,
        ahead.id,
        "2099-06-01T00:00:00+00:00",
        note="moved",
        _commit=False,
    )
    hold_commitment(session, tenant, overdue.id, "credit_check", _commit=False)
    reserve(session, tenant, ahead.id, "2", _commit=False)
    supply = create_commitment(
        session,
        tenant,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "5",
        "2026-08-05T00:00:00+00:00",
    )
    invoice = create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-M1",
        business.customer.id,
        "100",
        document_date="2026-08-02",
    )
    post_sales_invoice(session, tenant, invoice.id)
    record_customer_payment(session, tenant, business.customer.id, "40")
    hold_party_delivery(session, tenant, business.customer.id, "credit_check")
    # A sales invoice nobody posted, two supplier invoices under one number, and a
    # customer over an agreed limit: three more classes for a few lines.
    create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-UNPOSTED",
        business.customer.id,
        "70",
        document_date="2026-08-02",
    )
    for number in ("SUP-DUP", "SUP-DUP"):
        create_document(
            session,
            tenant,
            "supplier_invoice",
            number,
            business.supplier.id,
            "60",
            document_date="2026-08-03",
        )
    business.customer.credit_limit = 10
    session.flush()
    return {"order": order, "overdue": overdue, "supply": supply, "invoice": invoice}


def test_the_classes_that_read_the_clock_are_measured(session, business):

    tenant = business.tenant.id
    _rich_company(session, business)
    session.flush()

    now = dt.datetime.now(dt.UTC)
    before = _rows_by_id(session, tenant, as_of=now)
    later = _rows_by_id(session, tenant, as_of=now + dt.timedelta(days=400))

    assert before, (
        "the fixture produced no rows, so this file would approve of anything"
    )
    measured = _classes_that_changed(before, later)
    assert measured == CLOCK_READING
    assert measured, "the clock probe moved nothing; the measurement is not measuring"


def test_every_class_is_either_brought_about_here_or_named_as_missing(
    session, business
):
    """The gap is pinned, so it cannot quietly stay the same size."""
    from reality.services.exceptions import DERIVATION_REGISTRY

    tenant = business.tenant.id
    _rich_company(session, business)
    session.flush()
    now = dt.datetime.now(dt.UTC)
    present = {
        class_id for class_id, _ in _rows_by_id(session, tenant, as_of=now).values()
    } | {
        class_id
        for class_id, _ in _rows_by_id(
            session, tenant, as_of=now + dt.timedelta(days=400)
        ).values()
    }

    assert present | WITHOUT_A_SCENARIO == set(DERIVATION_REGISTRY)
    assert not present & WITHOUT_A_SCENARIO, (
        "a class produces rows here and is still listed as missing a scenario"
    )
