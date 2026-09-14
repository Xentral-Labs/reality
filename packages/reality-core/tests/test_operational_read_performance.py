"""Semantic and query-cost regressions for spec 153."""

from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import event, select

from reality.db.core import ProjectionCheckpoint
from reality.services import exceptions, projections
from reality.services.core import (
    correct_movement,
    create_commitment,
    create_document,
    create_tenant,
    financial_open_items,
    post_sales_invoice,
    record_movement,
    revise_commitment,
)
from reality.web.read_models import projection_page, projection_totals

AS_OF = datetime(2026, 9, 9, tzinfo=UTC)


@contextmanager
def query_count(session):
    counts = [0]
    bind = session.get_bind()

    def count(*args):
        counts[0] += 1

    event.listen(bind, "before_cursor_execute", count)
    try:
        yield counts
    finally:
        event.remove(bind, "before_cursor_execute", count)


def promise(session, business, kind="customer_delivery"):
    return create_commitment(
        session,
        business.tenant.id,
        kind,
        business.company.id if kind == "customer_delivery" else business.supplier.id,
        business.customer.id if kind == "customer_delivery" else business.company.id,
        business.item.id,
        business.location.id,
        "10",
        "2026-08-01",
    )


def individual_exceptions(session, tenant_id):
    rows = [
        row
        for derivator in exceptions.DERIVATION_REGISTRY.values()
        for row in derivator(session, tenant_id, AS_OF)
    ]
    return sorted(
        rows,
        key=lambda row: (
            exceptions.SEVERITY_ORDER[row.severity],
            exceptions.CLASS_ORDER[row.class_id],
            row.sort_at or datetime.max.replace(tzinfo=UTC),
            row.record_id,
        ),
    )


def test_exception_inputs_are_bounded_and_match_individual_derivators(
    session, business
):
    for _ in range(20):
        promise(session, business)
    supplier = promise(session, business, "supplier_delivery")
    revise_commitment(session, business.tenant.id, supplier.id, "2026-10-01")
    revise_commitment(session, business.tenant.id, supplier.id, quantity="15")
    movement = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "3",
        to_location_id=business.location.id,
        commitment_id=supplier.id,
    )
    correct_movement(session, business.tenant.id, movement.id, reason="Wrong receipt")
    expected = individual_exceptions(session, business.tenant.id)
    with query_count(session) as counts:
        actual = exceptions.operational_exceptions(
            session, business.tenant.id, as_of=AS_OF
        )
    assert actual == expected
    assert counts[0] < 150, f"Repeated per-commitment input queries: {counts[0]}"


def test_exception_evaluations_do_not_reuse_inputs_after_change_or_failure(
    session, business, monkeypatch
):
    tenant = business.tenant.id
    row = promise(session, business, "supplier_delivery")
    assert any(
        x.record_id == row.id
        for x in exceptions.operational_exceptions(session, tenant, as_of=AS_OF)
    )
    revise_commitment(session, tenant, row.id, "2026-10-01")
    assert not any(
        x.record_id == row.id
        for x in exceptions.operational_exceptions(session, tenant, as_of=AS_OF)
    )
    foreign = create_tenant(session, "Other company")
    assert exceptions.operational_exceptions(session, foreign.id, as_of=AS_OF) == []

    def fail(*args):
        raise RuntimeError("derivation failed")

    with monkeypatch.context() as patch:
        patch.setitem(exceptions.DERIVATION_REGISTRY, "silent_source", fail)
        with pytest.raises(RuntimeError, match="derivation failed"):
            exceptions.operational_exceptions(session, tenant, as_of=AS_OF)
    revise_commitment(session, tenant, row.id, "2026-08-02")
    assert exceptions.operational_exceptions(session, tenant, as_of=AS_OF) == (
        individual_exceptions(session, tenant)
    )


def invoice(session, business, number, amount):
    row = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        business.customer.id,
        amount,
    )
    post_sales_invoice(session, business.tenant.id, row.id)
    return row


def test_finance_refresh_only_builds_finance_and_preserves_page_totals(
    session, business, monkeypatch
):
    tenant = business.tenant.id
    first = invoice(session, business, "PERF-1", "100")

    def unrelated(*args):
        pytest.fail("Finance rebuilt unrelated operational projections")

    monkeypatch.setattr(projections, "_build_operational_rows", unrelated)
    projections.rebuild_projections(session, tenant, [projections.OPEN_FINANCIAL_ITEMS])
    rows, page = projection_page(
        session,
        tenant,
        projections.OPEN_FINANCIAL_ITEMS,
        size=1,
        flow="receivable",
        status="outstanding",
    )
    assert page.total == 1
    assert rows[0]["document_id"] == first.id
    assert Decimal(rows[0]["open"]) == financial_open_items(session, tenant)[0]["open"]
    invoice(session, business, "PERF-2", "50")
    projections.rebuild_projections(session, tenant, [projections.OPEN_FINANCIAL_ITEMS])
    rows, page = projection_page(
        session,
        tenant,
        projections.OPEN_FINANCIAL_ITEMS,
        size=1,
        flow="receivable",
        status="outstanding",
    )
    assert len(rows) == 1 and page.total == 2
    totals = projection_totals(
        session,
        tenant,
        projections.OPEN_FINANCIAL_ITEMS,
        ("gross", "settled", "open"),
        payload_filters={"document_type": "sales_invoice", "status": "outstanding"},
    )
    assert totals[0]._mapping["open"] == Decimal(150)
    checkpoints = list(
        session.scalars(
            select(ProjectionCheckpoint).where(ProjectionCheckpoint.tenant_id == tenant)
        )
    )
    assert [row.projection_name for row in checkpoints] == [
        projections.OPEN_FINANCIAL_ITEMS
    ]
    other = create_tenant(session, "Foreign finance")
    assert (
        projections.projection_rows(session, other.id, projections.OPEN_FINANCIAL_ITEMS)
        == []
    )


def test_finance_partial_refresh_preserves_other_checkpoints_and_tracks_settlement(
    session, business
):
    from reality.services.core import (
        NotFound,
        post_customer_payment,
        reverse_ledger_posting_group,
    )

    tenant = business.tenant.id
    doc = invoice(session, business, "SETTLE-PERF", "100")
    projections.refresh_operational_projections(session, tenant)

    def checkpoints():
        return {
            row.projection_name: (row.last_event_sequence, row.updated_at)
            for row in session.scalars(
                select(ProjectionCheckpoint).where(
                    ProjectionCheckpoint.tenant_id == tenant
                )
            )
        }

    original = checkpoints()
    payment = post_customer_payment(session, tenant, doc.id, Decimal(40))
    projections.rebuild_projections(session, tenant, [projections.OPEN_FINANCIAL_ITEMS])
    rows = projections.projection_rows(
        session, tenant, projections.OPEN_FINANCIAL_ITEMS
    )
    assert rows[0]["status"] == "partial"
    assert Decimal(rows[0]["open"]) == Decimal(60)
    after = checkpoints()
    assert (
        after[projections.OPEN_FINANCIAL_ITEMS]
        != original[projections.OPEN_FINANCIAL_ITEMS]
    )
    assert {
        k: v for k, v in after.items() if k != projections.OPEN_FINANCIAL_ITEMS
    } == {k: v for k, v in original.items() if k != projections.OPEN_FINANCIAL_ITEMS}
    with query_count(session) as counts:
        assert (
            projections.projection_rows(
                session, tenant, projections.OPEN_FINANCIAL_ITEMS
            )
            == rows
        )
    assert counts[0] <= 4
    reverse_ledger_posting_group(
        session, tenant, payment[0].posting_group_id, reason="Payment recorded in error"
    )
    projections.rebuild_projections(session, tenant, [projections.OPEN_FINANCIAL_ITEMS])
    assert Decimal(
        projections.projection_rows(session, tenant, projections.OPEN_FINANCIAL_ITEMS)[
            0
        ]["open"]
    ) == Decimal(100)
    before_missing = checkpoints()
    with pytest.raises(NotFound):
        projections.refresh_projection(
            session, "ten_missing", projections.OPEN_FINANCIAL_ITEMS
        )
    assert checkpoints() == before_missing


def test_exception_scope_is_session_bound_and_restored_when_nested(session, business):
    from sqlalchemy.orm import Session

    from reality.services.exception_inputs import _exception_input_scope, _inputs

    tenant = business.tenant.id
    foreign = create_tenant(session, "Nested company")
    with _exception_input_scope(session, tenant):
        outer = _inputs(session, tenant)
        assert outer is not None
        with Session(session.get_bind()) as other_session:
            assert _inputs(other_session, tenant) is None
        assert _inputs(session, foreign.id) is None
        with _exception_input_scope(session, foreign.id):
            assert _inputs(session, tenant) is None
            assert _inputs(session, foreign.id) is not None
        assert _inputs(session, tenant) is outer
    assert _inputs(session, tenant) is None


def test_exception_batch_preserves_invoice_linked_credit_evidence(session, business):
    from reality.services.core import (
        create_manual_document_with_lines,
        create_manual_order,
    )

    tenant = business.tenant.id
    _, _, lines, commitments = create_manual_order(
        session,
        tenant,
        "sales",
        "PERF-ORDER",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit": "pcs",
                "unit_price": "10",
                "gross_amount": "100",
            }
        ],
        "100",
        requested_delivery_at="2026-08-01",
    )
    record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )
    record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "2",
        to_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )

    def evidence(kind, number, quantity, referenced):
        return create_manual_document_with_lines(
            session,
            tenant,
            kind,
            number,
            business.customer.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": quantity,
                    "unit": "pcs",
                    "unit_price": "10",
                    "gross_amount": "10",
                    "billed_document_line_id": referenced,
                }
            ],
            "10",
        )

    _, billed = evidence("sales_invoice", "PERF-BILLED", "5", lines[0].id)
    _, credits = evidence("credit_note", "PERF-CREDIT", "1", billed[0].id)
    expected = individual_exceptions(session, tenant)
    actual = exceptions.operational_exceptions(session, tenant, as_of=AS_OF)
    assert actual == expected
    assert any(row.class_id == "returned_not_credited" for row in actual)
    assert any(row.trace.get("document_line_id") == lines[0].id for row in actual)
    from reality.services.exception_inputs import _exception_input_scope

    with _exception_input_scope(session, tenant):
        assert {
            line.id for line in exceptions._billing_lines(session, tenant, lines[0].id)
        } == {billed[0].id, credits[0].id}


def test_exception_helpers_fall_back_for_records_arriving_after_batch_load(
    session, business
):
    """READ COMMITTED can expose new intake between batch and later class queries."""
    from reality.services.exception_inputs import _exception_input_scope

    with _exception_input_scope(session, business.tenant.id):
        row = promise(session, business, "supplier_delivery")
        record_movement(
            session,
            business.tenant.id,
            "receipt",
            business.item.id,
            "3",
            to_location_id=business.location.id,
            commitment_id=row.id,
        )
        assert exceptions._promise_quantity(
            session, business.tenant.id, row
        ) == Decimal(10)
        assert exceptions._promise_due_at(session, business.tenant.id, row) == (
            row.due_at,
            0,
        )
        assert exceptions._fulfilled_quantity(
            session, business.tenant.id, row.id, "receipt"
        ) == Decimal(3)


def test_projection_builders_read_per_company_not_per_record(session, business):
    """Spec 181: a builder's reads must not grow with the number of promises or documents."""
    for _ in range(20):
        promise(session, business)
    promise(session, business, "supplier_delivery")
    with query_count(session) as few:
        few_rows = {
            name: len(
                projections.derive_projection_rows(session, business.tenant.id, name)
            )
            for name in (
                "fulfillment_queue",
                "fulfillment_blockers",
                "item_supply_demand",
                "commitment_register",
                "document_register",
                "timeline",
            )
        }
    for _ in range(40):
        promise(session, business)
    with query_count(session) as many:
        many_rows = {
            name: len(
                projections.derive_projection_rows(session, business.tenant.id, name)
            )
            for name in few_rows
        }
    assert many_rows["commitment_register"] == few_rows["commitment_register"] + 40
    assert many[0] == few[0], (few[0], many[0])
    assert few[0] < 120, f"Per-record builder reads: {few[0]}"
