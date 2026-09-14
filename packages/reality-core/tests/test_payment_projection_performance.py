"""Live payment totals and explicit isolated materialization (specs 154, 179)."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import ProjectionCheckpoint
from reality.services import projections
from reality.services.core import (
    create_document,
    create_tenant,
    payment_rows,
    post_customer_payment,
    post_sales_invoice,
    reverse_ledger_posting_group,
)
from reality.web.api import tenant_payments


def payment_history(session, business):
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "PAYMENT-PERF",
        business.customer.id,
        "100",
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)
    return invoice


def read_payments(session, tenant):
    return tenant_payments(
        tenant,
        session,
        page=1,
        size=1,
        q="",
        direction="",
        sort="",
        sort_direction="asc",
    )


def test_payment_refresh_avoids_unrelated_views_and_preserves_totals(
    session, business, monkeypatch
):
    tenant = business.tenant.id
    invoice = payment_history(session, business)
    payment = post_customer_payment(session, tenant, invoice.id, Decimal(40))

    def unrelated(*args):
        pytest.fail("Payment totals rebuilt unrelated projections")

    monkeypatch.setattr(projections, "_build_operational_rows", unrelated)
    result = read_payments(session, tenant)
    assert result["page"]["total"] == 1
    assert Decimal(result["totals"][0]["amount"]) == Decimal(40)
    assert Decimal(result["totals"][0]["allocated"]) == Decimal(40)
    assert Decimal(result["totals"][0]["unallocated"]) == 0
    projections.rebuild_projections(session, tenant, [projections.PAYMENTS])
    projected = projections.projection_rows(session, tenant, projections.PAYMENTS)
    canonical = payment_rows(session, tenant)
    assert projected[0]["payment_entry_id"] == canonical[0]["cash_entry"].id
    assert Decimal(projected[0]["allocated"]) == canonical[0]["allocated"]
    assert {
        row.projection_name
        for row in session.scalars(
            select(ProjectionCheckpoint).where(ProjectionCheckpoint.tenant_id == tenant)
        )
    } == {projections.PAYMENTS}
    post_customer_payment(session, tenant, invoice.id, Decimal(20))
    result = read_payments(session, tenant)
    assert len(result["items"]) == 1 and result["page"]["total"] == 2
    assert Decimal(result["totals"][0]["amount"]) == Decimal(60)
    reverse_ledger_posting_group(
        session, tenant, payment[0].posting_group_id, reason="Wrong payment"
    )
    result = read_payments(session, tenant)
    assert Decimal(result["totals"][0]["allocated"]) == Decimal(20)
    other = create_tenant(session, "Other payment company")
    assert read_payments(session, other.id)["items"] == []
    assert read_payments(session, other.id)["totals"] == []


def test_payment_refresh_keeps_other_checkpoints_and_read_only_derivation(
    session, business, monkeypatch
):
    tenant = business.tenant.id
    invoice = payment_history(session, business)
    projections.refresh_operational_projections(session, tenant)

    def other_checkpoints():
        return {
            row.projection_name: (row.last_event_sequence, row.updated_at)
            for row in session.scalars(
                select(ProjectionCheckpoint).where(
                    ProjectionCheckpoint.tenant_id == tenant,
                    ProjectionCheckpoint.projection_name != projections.PAYMENTS,
                )
            )
        }

    before = other_checkpoints()
    post_customer_payment(session, tenant, invoice.id, Decimal(40))
    monkeypatch.setattr(
        projections,
        "_build_operational_rows",
        lambda *args: pytest.fail("full rebuild"),
    )
    derived = projections.derive_projection_rows(session, tenant, projections.PAYMENTS)
    assert other_checkpoints() == before
    projections.rebuild_projections(session, tenant, [projections.PAYMENTS])
    rows = projections.projection_rows(session, tenant, projections.PAYMENTS)
    assert rows == list(derived.values())
    assert other_checkpoints() == before


def test_payment_totals_keep_currencies_separate_and_apply_direction_filter(
    session, business
):
    from reality.services.core import post_supplier_invoice, post_supplier_payment

    tenant = business.tenant.id
    for number, kind, party, currency, amount in [
        ("PAY-EUR", "sales_invoice", business.customer.id, "EUR", 40),
        ("PAY-USD", "sales_invoice", business.customer.id, "USD", 70),
        ("PAY-OUT", "supplier_invoice", business.supplier.id, "EUR", 15),
    ]:
        invoice = create_document(
            session, tenant, kind, number, party, amount, currency=currency
        )
        if kind == "sales_invoice":
            post_sales_invoice(session, tenant, invoice.id)
            post_customer_payment(session, tenant, invoice.id, Decimal(amount))
        else:
            post_supplier_invoice(session, tenant, invoice.id)
            post_supplier_payment(session, tenant, invoice.id, Decimal(amount))
    result = tenant_payments(
        tenant,
        session,
        page=1,
        size=1,
        q="",
        direction="incoming",
        sort="",
        sort_direction="asc",
    )
    assert len(result["items"]) == 1 and result["page"]["total"] == 2
    assert {row["currency"]: Decimal(row["amount"]) for row in result["totals"]} == {
        "EUR": Decimal(40),
        "USD": Decimal(70),
    }
    assert all(Decimal(row["unallocated"]) == 0 for row in result["totals"])
