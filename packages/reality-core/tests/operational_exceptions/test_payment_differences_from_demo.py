"""Feature 168 FR-025: synthetic payment differences surface through existing exception classes."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from reality.demo.international import DEMO_DATA_CUSTOMERS, DEMO_DATA_PAYMENT_TERM
from reality.integrations import demo_data as synthetic
from reality.services import core, payment_intake
from reality.services.exceptions import operational_exceptions

AT = datetime(2026, 9, 10, 8, 0, tzinfo=UTC)
SEED, SCHEDULE = "exception-seed", "sch_exc"
AFTER_DUE = AT + timedelta(days=40)


def _references(business):
    return {
        "parties": {
            "company": business.company.id,
            DEMO_DATA_CUSTOMERS[0][0]: business.customer.id,
        },
        "locations": {"A": business.location.id},
        "items": {key: business.item.id for key in ("P01", "P02", "P11", "P12")},
    }


def _find(business, wanted, limit=4000):
    refs = _references(business)
    for index in range(limit):
        order = synthetic.produce(SCHEDULE, f"run_{index}", SEED, AT, refs)
        plan = synthetic.settlement_plan(
            SEED, SCHEDULE, f"{SCHEDULE}:run_{index}", order
        )
        if wanted(plan):
            return index
    raise AssertionError("no plan matches")


def _story(session, business, index, *, payments=None):
    tenant = business.tenant.id
    term = dict(DEMO_DATA_PAYMENT_TERM)
    try:
        core.payment_term_by_code(session, tenant, term["code"])
    except core.NotFound:
        core.create_payment_term(
            session,
            tenant,
            term["code"],
            term["name"],
            term["due_days"],
            discount_percent=term["discount_percent"],
            discount_days=term["discount_days"],
            _commit=False,
        )
    external_id = f"{SCHEDULE}:run_{index}"
    order = synthetic.produce(SCHEDULE, f"run_{index}", SEED, AT, _references(business))
    source, _ = core.enqueue_source(
        session, tenant, "demo_data", "order", external_id, order, _commit=False
    )
    core.create_manual_document_with_lines(
        session,
        tenant,
        "sales_order",
        order["number"],
        order["customer_party_id"],
        order["lines"],
        order["gross_amount"],
        currency=order["currency"],
        document_date=order["ordered_at"][:10],
        customer_reference=order["customer_reference"],
        source_record_id=source.id,
        _commit=False,
    )
    plan = synthetic.settlement_plan(SEED, SCHEDULE, external_id, order)
    invoice_payload = synthetic.produce_invoice(order, external_id, plan)
    invoice_source, _ = core.enqueue_source(
        session,
        tenant,
        "demo_data",
        "invoice",
        f"{external_id}:invoice",
        invoice_payload,
        _commit=False,
    )
    _, invoice, _, _ = payment_intake.interpret_sales_invoice(
        session, tenant, invoice_source, synthetic.normalise_invoice(invoice_payload)
    )
    results = []
    for planned in plan.payments[:payments] if payments is not None else plan.payments:
        payload = synthetic.produce_payment(order, invoice_payload, plan, planned.index)
        payment_source, _ = core.enqueue_source(
            session,
            tenant,
            "demo_data",
            "payment",
            f"{external_id}:payment:{planned.index}",
            payload,
            _commit=False,
        )
        results.append(
            payment_intake.interpret_customer_payment(
                session, tenant, payment_source, synthetic.normalise_payment(payload)
            )
        )
    return plan, invoice, results


def _rows(session, tenant, class_id, *, as_of):
    return {
        row.record_id: row
        for row in operational_exceptions(session, tenant, as_of=as_of)
        if row.class_id == class_id
    }


def test_unallocated_remainders_raise_unmatched_financial_event(session, business):
    tenant = business.tenant.id
    over = _find(business, lambda p: p.outcome == "over")
    plan, invoice, results = _story(session, business, over)
    unmatched = _find(business, lambda p: p.outcome == "unmatched")
    _, _, unmatched_results = _story(session, business, unmatched)
    rows = _rows(session, tenant, "unmatched_financial_event", as_of=AT)
    excess = sum(p.amount for p in plan.payments) - Decimal(invoice.gross_amount)
    by_amount = {row.causal_values["unallocated_amount"] for row in rows.values()}
    assert Decimal(invoice.gross_amount) in by_amount  # the unmatched payment, in full
    assert any(value == excess for value in by_amount)  # the overpayment remainder
    controls = {
        entry.id
        for _, _, entries, _, _ in results + unmatched_results
        for entry in entries
        if entry.account == "accounts_receivable"
    }
    assert set(rows) & controls


def test_late_and_never_paid_invoices_age_and_a_late_payment_clears_them(
    session, business
):
    tenant = business.tenant.id
    never = _find(business, lambda p: p.outcome == "never")
    _, never_invoice, _ = _story(session, business, never)
    late = _find(business, lambda p: p.outcome == "late")
    plan, late_invoice, _ = _story(session, business, late, payments=0)
    before_due = _rows(
        session, tenant, "overdue_receivable", as_of=AT + timedelta(days=1)
    )
    assert not {never_invoice.id, late_invoice.id} & set(before_due)
    overdue = _rows(session, tenant, "overdue_receivable", as_of=AFTER_DUE)
    assert {never_invoice.id, late_invoice.id} <= set(overdue)
    assert overdue[late_invoice.id].causal_values["outstanding_amount"] == Decimal(
        late_invoice.gross_amount
    )
    # The late payment arrives; the claim is settled and the exception ends.
    _story_payment(session, business, late, plan, late_invoice)
    after = _rows(session, tenant, "overdue_receivable", as_of=AFTER_DUE)
    assert late_invoice.id not in after and never_invoice.id in after


def _story_payment(session, business, index, plan, invoice):
    tenant = business.tenant.id
    external_id = f"{SCHEDULE}:run_{index}"
    order = synthetic.produce(SCHEDULE, f"run_{index}", SEED, AT, _references(business))
    invoice_payload = synthetic.produce_invoice(order, external_id, plan)
    payload = synthetic.produce_payment(order, invoice_payload, plan, 1)
    source, _ = core.enqueue_source(
        session,
        tenant,
        "demo_data",
        "payment",
        f"{external_id}:payment:1",
        payload,
        _commit=False,
    )
    return payment_intake.interpret_customer_payment(
        session, tenant, source, synthetic.normalise_payment(payload)
    )


def test_a_two_percent_short_payment_carries_the_discount_tag(session, business):
    tenant = business.tenant.id
    index = _find(
        business,
        lambda p: (
            p.outcome == "short_discount"
            and p.payments[0].amount
            == (Decimal(25) * Decimal("0.98")).quantize(Decimal("0.01"))
        ),
    )
    plan, invoice, _ = _story(session, business, index)
    row = _rows(session, tenant, "overdue_receivable", as_of=AFTER_DUE)[invoice.id]
    assert row.cause_ids == ("early_payment_discount_taken",)
    assert (
        row.causal_values["outstanding_amount"] == Decimal(25) - plan.payments[0].amount
    )
    three = _find(
        business,
        lambda p: (
            p.outcome == "short_discount"
            and p.payments[0].amount
            == (Decimal(25) * Decimal("0.97")).quantize(Decimal("0.01"))
        ),
    )
    _, other, _ = _story(session, business, three)
    assert (
        _rows(session, tenant, "overdue_receivable", as_of=AFTER_DUE)[
            other.id
        ].cause_ids
        == ()
    )
