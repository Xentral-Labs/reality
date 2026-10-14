"""A supplier invoice number is recorded once per supplier while it stands."""

from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import Document
from reality.services import core
from reality.services.invoice_actions import record_free_supplier_invoice


def _purchase_line(session, business, number, supplier=None):
    _, _, (line,), _ = core.create_manual_order(
        session,
        business.tenant.id,
        "purchase",
        number,
        business.company.id,
        (supplier or business.supplier).id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": "10",
                "gross_amount": "100",
            }
        ],
        "100",
    )
    return line


def _record(session, business, number, supplier=None, order="PO-DUP"):
    line = _purchase_line(
        session, business, f"{order}-{core.uid('po')}", supplier=supplier
    )
    receipt = core.record_supplier_invoice(
        session, business.tenant.id, line.id, "10", "100", number
    )
    return next(row["id"] for row in receipt["records"] if row["family"] == "document")


def _supplier_invoices(session, business):
    return session.scalar(
        select(func.count())
        .select_from(Document)
        .where(
            Document.tenant_id == business.tenant.id,
            Document.type == "supplier_invoice",
        )
    )


def _refused(call):
    with pytest.raises(core.InvalidOperation) as refused:
        call()
    assert refused.value.code == "supplier_invoice_number_duplicate"
    return refused.value


def test_a_repeated_number_for_the_same_supplier_is_refused(session, business):
    _record(session, business, "ER-4711")

    refusal = _refused(lambda: _record(session, business, "ER-4711"))
    # Trimmed and case-insensitive, exactly as the duplicate report compares.
    _refused(lambda: _record(session, business, " er-4711 "))

    assert "ER-4711" in str(refusal)
    assert _supplier_invoices(session, business) == 1
    assert core.duplicate_supplier_invoices(session, business.tenant.id) == []


def test_the_free_invoice_path_refuses_the_same_number(session, business):
    _record(session, business, "ER-4712")

    _refused(
        lambda: record_free_supplier_invoice(
            session,
            business.tenant.id,
            supplier_id=business.supplier.id,
            number="ER-4712",
            currency="EUR",
            gross_amount="100",
            lines=[
                {
                    "item_id": business.item.id,
                    "quantity": "10",
                    "unit_price": "10",
                    "gross_amount": "100",
                }
            ],
        )
    )
    assert _supplier_invoices(session, business) == 1


def test_another_supplier_may_use_the_same_number(session, business):
    other = core.create_party(session, business.tenant.id, "Rahmen AG", "supplier")
    first = _record(session, business, "ER-4713")

    second = _record(session, business, "ER-4713", supplier=other)

    assert first != second
    assert _supplier_invoices(session, business) == 2


def test_another_number_from_the_same_supplier_is_recorded(session, business):
    _record(session, business, "ER-4714")
    _record(session, business, "ER-4715")

    assert _supplier_invoices(session, business) == 2


def test_a_reversed_invoice_releases_its_number(session, business):
    first = _record(session, business, "ER-4716")
    group = next(
        row["control"].posting_group_id
        for row in core.financial_open_items(session, business.tenant.id)
        if row["document"].id == first
    )
    core.reverse_ledger_posting_group(
        session, business.tenant.id, group, reason="Booked in error"
    )

    corrected = _record(session, business, "ER-4716")

    assert corrected != first
    assert core.open_invoice_amount(
        session, business.tenant.id, corrected
    ) == Decimal(100)
    # The corrected invoice now holds the number again.
    _refused(lambda: _record(session, business, "ER-4716"))

