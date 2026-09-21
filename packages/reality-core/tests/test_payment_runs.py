"""A payment run: what is worth paying, and paying it all at once or not at all.

Every amount in these tests is stated. Nothing here multiplies a gross amount by
a discount rate, and one test exists purely to prove the product does not either.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from reality.services.core import (
    PAYMENT_RUN_WITHHELD_REASONS,
    InvalidOperation,
    NotFound,
    aging_register,
    business_events,
    create_document,
    create_party,
    create_payment_term,
    create_tenant,
    duplicate_supplier_invoices,
    execute_payment_run,
    financial_open_items,
    open_invoice_amount,
    payable_supplier_invoices,
    payment_terms,
    post_sales_invoice,
    post_supplier_invoice,
    post_supplier_payment,
    preview_payment_run,
    reverse_ledger_posting_group,
)
from reality.services.exceptions import operational_exceptions

# The queue and the previews are all read at one instant, so nothing in this file
# depends on the day the suite runs.
AS_OF = datetime(2026, 8, 31, 12, tzinfo=UTC)
PAY_BY = datetime(2026, 9, 7, 12, tzinfo=UTC)


def skonto(session, business, code="SK2_10", *, percent="2", days=10, due=30):
    existing = [
        term
        for term in payment_terms(session, business.tenant.id)
        if term.code == code.upper()
    ]
    if existing:
        return existing[0]
    return create_payment_term(
        session,
        business.tenant.id,
        code,
        f"{percent}% {days} days, net {due}",
        due,
        discount_percent=percent,
        discount_days=days,
    )


def net(session, business, code="NET30", *, due=30):
    existing = [
        term
        for term in payment_terms(session, business.tenant.id)
        if term.code == code.upper()
    ]
    if existing:
        return existing[0]
    return create_payment_term(
        session, business.tenant.id, code, f"Net {due} days", due
    )


def supplier_invoice(
    session,
    business,
    number,
    document_date,
    term_code="NET30",
    amount="1000.00",
    *,
    party=None,
    currency="EUR",
    post=True,
):
    invoice = create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        number,
        (party or business.supplier).id,
        amount,
        currency=currency,
        document_date=document_date,
        payment_term_code=term_code,
    )
    if post:
        post_supplier_invoice(session, business.tenant.id, invoice.id)
    return invoice


def proposed_ids(preview):
    return [entry["invoice_id"] for entry in preview["proposed"]]


def test_one_rule_decides_what_is_payable(session, business):
    """The preview and the run ask the same question of the same rule."""
    net(session, business)
    due = supplier_invoice(session, business, "ER-098-DUE", "2026-08-01")
    later = supplier_invoice(session, business, "ER-098-LATER", "2026-08-25")

    payable, withheld = payable_supplier_invoices(
        session, business.tenant.id, as_of=AS_OF
    )

    # Both are payable. Whether either belongs in *this* run is the preview's
    # question, and it is a different one.
    assert {row["document"].id for row in payable} == {due.id, later.id}
    assert withheld == []

    # The rule lives in exactly one place. Nothing in the service layer or the
    # derivation layer may answer "may this be paid" a second time, because two
    # answers is how a proposal and the operation that executes it start
    # disagreeing about money.
    from pathlib import Path

    sources = [
        Path(__file__).resolve().parents[1] / "src/reality/services/core.py",
        Path(__file__).resolve().parents[1] / "src/reality/services/exceptions.py",
    ]
    definitions = sum(
        text.count("def payable_supplier_invoices")
        for text in (path.read_text() for path in sources)
    )
    assert definitions == 1


def test_the_duplicate_rule_has_one_home(session, business):
    """The queue and the payment run read the same duplicate grouping."""
    net(session, business)
    first = supplier_invoice(session, business, "ER-098-SAME", "2026-08-01")
    second = supplier_invoice(session, business, " er-098-same ", "2026-08-02")

    pairs = duplicate_supplier_invoices(session, business.tenant.id)
    assert [(duplicate.id, original.id) for duplicate, original in pairs] == [
        (second.id, first.id)
    ]

    # The exception class is now a consumer of that rule rather than its owner,
    # and it must still report exactly the same document.
    reported = {
        entry.record_id
        for entry in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
        if entry.class_id == "duplicate_supplier_invoice"
    }
    assert reported == {second.id}

    # Positive control: a number nobody reused produces no pair and no entry.
    alone = supplier_invoice(session, business, "ER-098-ALONE", "2026-08-03")
    assert alone.id not in {duplicate.id for duplicate, _ in pairs}


def test_what_is_not_payable_and_why(session, business):
    """Four exclusions, each with a positive control in the same test."""
    net(session, business)
    payable_invoice = supplier_invoice(session, business, "ER-098-OK", "2026-08-01")

    # Reversed: the posting behind it has been withdrawn.
    reversed_invoice = supplier_invoice(session, business, "ER-098-REV", "2026-08-01")
    group = next(
        row["control"].posting_group_id
        for row in financial_open_items(session, business.tenant.id)
        if row["document"].id == reversed_invoice.id
    )
    reverse_ledger_posting_group(
        session, business.tenant.id, group, reason="Booked in error"
    )

    # Duplicate: a number this supplier already used. The first one recorded is
    # still perfectly payable — it is the second that nobody should pay.
    original = supplier_invoice(session, business, "ER-098-TWICE", "2026-08-01")
    duplicate = supplier_invoice(session, business, "ER-098-TWICE", "2026-08-02")

    # Settled: nothing open.
    settled = supplier_invoice(session, business, "ER-098-PAID", "2026-08-01")
    post_supplier_payment(session, business.tenant.id, settled.id, "1000.00")

    # Not a supplier invoice at all.
    customer_invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "RE-098",
        business.customer.id,
        "500.00",
        document_date="2026-08-01",
        payment_term_code="NET30",
    )
    post_sales_invoice(session, business.tenant.id, customer_invoice.id)

    payable, withheld = payable_supplier_invoices(
        session, business.tenant.id, as_of=AS_OF
    )
    reasons = {row["document"].id: row["withheld_because"] for row in withheld}

    assert {row["document"].id for row in payable} == {
        payable_invoice.id,
        original.id,
    }
    assert reasons == {
        reversed_invoice.id: "reversed",
        duplicate.id: "duplicate",
        settled.id: "settled",
    }
    # A sales invoice is absent from both lists rather than withheld. It was
    # never a candidate, and reporting it as one would bury the supplier
    # invoices that were.
    assert customer_invoice.id not in reasons
    assert customer_invoice.id not in {row["document"].id for row in payable}

    # The preview says what it withheld and why, rather than dropping it.
    preview = preview_payment_run(
        session, business.tenant.id, pay_by=PAY_BY, as_of=AS_OF
    )
    assert set(proposed_ids(preview)) == {payable_invoice.id, original.id}
    assert {row["invoice_id"]: row["reason"] for row in preview["withheld"]} == reasons
    assert all(row["explanation"] for row in preview["withheld"])

    # And the run refuses each of them, naming the reason.
    for invoice_id, reason in reasons.items():
        with pytest.raises(InvalidOperation) as refused:
            execute_payment_run(
                session,
                business.tenant.id,
                payments=[{"invoice_id": invoice_id, "amount": "10.00"}],
                currency="EUR",
                expected_total="10.00",
                reason="Friday run",
            )
        # The refusal says the same thing the preview said, from the same place.
        assert str(refused.value) == PAYMENT_RUN_WITHHELD_REASONS[reason]

    # Positive control: the payable one goes through with the same shape of call.
    assert (
        execute_payment_run(
            session,
            business.tenant.id,
            payments=[{"invoice_id": payable_invoice.id, "amount": "10.00"}],
            currency="EUR",
            expected_total="10.00",
            reason="Friday run",
        )["paid"]
        == 1
    )


def test_the_preview_writes_nothing(session, business):
    net(session, business)
    supplier_invoice(session, business, "ER-098-A", "2026-08-01")

    before = (
        len(financial_open_items(session, business.tenant.id)),
        len(business_events(session, business.tenant.id)),
    )
    first = preview_payment_run(session, business.tenant.id, pay_by=PAY_BY, as_of=AS_OF)
    second = preview_payment_run(
        session, business.tenant.id, pay_by=PAY_BY, as_of=AS_OF
    )
    after = (
        len(financial_open_items(session, business.tenant.id)),
        len(business_events(session, business.tenant.id)),
    )

    assert before == after
    # Two identical reads of an unchanged tenant return an identical, identically
    # ordered answer.
    assert proposed_ids(first) == proposed_ids(second)
    assert first["totals"] == second["totals"]


def test_the_preview_proposes_what_is_due_and_what_is_discountable(session, business):
    """Two kinds of invoice belong in a run, and they arrive in one order."""
    net(session, business)
    skonto(session, business)
    # Net 30 from 2026-08-01: due 2026-08-31, on or before the day this run is
    # being made for.
    due_soon = supplier_invoice(session, business, "ER-098-SOON", "2026-08-01")
    # Net 30 from 2026-08-30: due 2026-09-29, with no discount to lose. Payable,
    # and not this run's business.
    much_later = supplier_invoice(session, business, "ER-098-LATE", "2026-08-30")
    # Not due until 2026-09-24, but its early-payment window closes 2026-09-04 —
    # which is exactly why the discount class named a payment run in its own
    # guidance. An invoice nobody has to pay for weeks can still be the one
    # worth paying this afternoon.
    discountable = supplier_invoice(
        session, business, "ER-098-SKONTO", "2026-08-25", "SK2_10"
    )

    preview = preview_payment_run(
        session, business.tenant.id, pay_by=PAY_BY, as_of=AS_OF
    )

    assert proposed_ids(preview) == [due_soon.id, discountable.id]
    assert much_later.id not in proposed_ids(preview)
    # Ordered by the day the money is needed: a due date where there is no open
    # window, and the deadline where there is.
    assert [entry["needed_on"].isoformat() for entry in preview["proposed"]] == [
        "2026-08-31",
        "2026-09-04",
    ]
    assert preview["pay_by"].isoformat() == "2026-09-07"
    assert preview["count"] == 2


def test_the_discount_is_named_never_applied(session, business):
    """The rate and the deadline are stated; what the discount is worth is not."""
    skonto(session, business)
    invoice = supplier_invoice(session, business, "ER-098-RATE", "2026-08-25", "SK2_10")

    preview = preview_payment_run(
        session, business.tenant.id, pay_by=PAY_BY, as_of=AS_OF
    )
    (entry,) = preview["proposed"]

    assert entry["open_amount"] == Decimal(1000)
    assert entry["discount_percent"] == Decimal("2.000")
    assert entry["discount_date"].isoformat() == "2026-09-04"
    # Nothing anywhere in the answer is 980, or 20, or any other figure derived
    # from applying that rate to that amount. A rate times a gross amount is a
    # division producing money nobody agreed to.
    assert "discount_amount" not in entry
    assert "net_amount" not in entry
    assert Decimal(980) not in set(entry.values())
    assert Decimal(20) not in set(entry.values())

    # The operator states 980, and 20 stays open on the invoice — exactly what a
    # single payment does. Spec 088 decided the residue is reported, not cleared.
    execute_payment_run(
        session,
        business.tenant.id,
        payments=[{"invoice_id": invoice.id, "amount": "980.00"}],
        currency="EUR",
        expected_total="980.00",
        reason="2% taken",
        effective_at=datetime(2026, 8, 31, 12, tzinfo=UTC),
    )
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == Decimal(20)


def test_the_preview_totals_per_supplier_and_overall(session, business):
    net(session, business)
    other = create_party(session, business.tenant.id, "Rahmen AG", "supplier")
    supplier_invoice(session, business, "ER-098-S1", "2026-08-01", amount="100.00")
    supplier_invoice(session, business, "ER-098-S2", "2026-08-02", amount="250.00")
    supplier_invoice(
        session, business, "ER-098-O1", "2026-08-03", amount="400.00", party=other
    )
    # A second currency: totalled separately, never summed, because a total in
    # two currencies is not a total.
    supplier_invoice(
        session, business, "ER-098-USD", "2026-08-04", amount="90.00", currency="USD"
    )

    preview = preview_payment_run(
        session, business.tenant.id, pay_by=PAY_BY, as_of=AS_OF
    )

    assert [
        (row["supplier"], row["currency"], row["count"], row["open_amount"])
        for row in preview["suppliers"]
    ] == [
        ("Bike Parts GmbH", "EUR", 2, Decimal(350)),
        ("Rahmen AG", "EUR", 1, Decimal(400)),
        ("Bike Parts GmbH", "USD", 1, Decimal(90)),
    ]
    assert [
        (row["currency"], row["count"], row["open_amount"]) for row in preview["totals"]
    ] == [("EUR", 3, Decimal(750)), ("USD", 1, Decimal(90))]


def test_the_preview_reads_the_register(session, business):
    """Every figure comes from the aging register, so they cannot disagree."""
    skonto(session, business)
    invoice = supplier_invoice(session, business, "ER-098-REG", "2026-08-25", "SK2_10")
    post_supplier_payment(session, business.tenant.id, invoice.id, "400.00")

    (row,) = [
        row
        for row in aging_register(session, business.tenant.id, as_of=AS_OF)
        if row["document"].id == invoice.id
    ]
    (entry,) = preview_payment_run(
        session, business.tenant.id, pay_by=PAY_BY, as_of=AS_OF
    )["proposed"]

    assert entry["open_amount"] == row["open"] == Decimal(600)
    assert entry["due_date"] == row["due_date"]
    assert entry["discount_date"] == row["discount_date"]
    assert entry["days_overdue"] == row["days_overdue"]


def test_a_run_pays_exactly_what_it_was_given(session, business):
    net(session, business)
    first = supplier_invoice(session, business, "ER-098-P1", "2026-08-01")
    second = supplier_invoice(
        session, business, "ER-098-P2", "2026-08-02", amount="600.00"
    )
    untouched = supplier_invoice(session, business, "ER-098-P3", "2026-08-03")

    result = execute_payment_run(
        session,
        business.tenant.id,
        payments=[
            {"invoice_id": first.id, "amount": "1000.00"},
            # A part payment: what the caller stated, not what was open.
            {"invoice_id": second.id, "amount": "150.00"},
        ],
        currency="EUR",
        expected_total="1150.00",
        reason="Weekly supplier run",
    )

    assert result["paid"] == 2
    assert result["total"] == Decimal(1150)
    assert open_invoice_amount(session, business.tenant.id, first.id) == Decimal(0)
    assert open_invoice_amount(session, business.tenant.id, second.id) == Decimal(450)
    # An invoice the run was not given is untouched, even though it was payable
    # and would have been proposed.
    assert open_invoice_amount(session, business.tenant.id, untouched.id) == Decimal(
        1000
    )


def test_a_run_refuses(session, business):
    net(session, business)
    invoice = supplier_invoice(session, business, "ER-098-R", "2026-08-01")
    tenant_id = business.tenant.id
    line = [{"invoice_id": invoice.id, "amount": "100.00"}]

    with pytest.raises(InvalidOperation, match="reason"):
        execute_payment_run(
            session,
            tenant_id,
            payments=line,
            currency="EUR",
            expected_total="100.00",
            reason="   ",
        )
    with pytest.raises(InvalidOperation, match="at least one payment"):
        execute_payment_run(
            session,
            tenant_id,
            payments=[],
            currency="EUR",
            expected_total="0.00",
            reason="Friday",
        )
    with pytest.raises(InvalidOperation, match="each invoice once"):
        execute_payment_run(
            session,
            tenant_id,
            payments=[*line, {"invoice_id": invoice.id, "amount": "50.00"}],
            currency="EUR",
            expected_total="150.00",
            reason="Friday",
        )
    with pytest.raises(InvalidOperation, match="confirmed total"):
        execute_payment_run(
            session,
            tenant_id,
            payments=line,
            currency="EUR",
            expected_total="120.00",
            reason="Friday",
        )
    with pytest.raises(InvalidOperation, match="greater than zero"):
        execute_payment_run(
            session,
            tenant_id,
            payments=[{"invoice_id": invoice.id, "amount": "0"}],
            currency="EUR",
            expected_total="0",
            reason="Friday",
        )
    with pytest.raises(InvalidOperation, match="exceeds the open"):
        execute_payment_run(
            session,
            tenant_id,
            payments=[{"invoice_id": invoice.id, "amount": "1000.01"}],
            currency="EUR",
            expected_total="1000.01",
            reason="Friday",
        )
    with pytest.raises(InvalidOperation, match="currency it is paid in"):
        execute_payment_run(
            session,
            tenant_id,
            payments=line,
            currency="  ",
            expected_total="100.00",
            reason="Friday",
        )

    # Every refusal above rejected the call and wrote nothing.
    assert open_invoice_amount(session, tenant_id, invoice.id) == Decimal(1000)

    # The positive control: the same invoice, the same shape, correctly stated.
    assert (
        execute_payment_run(
            session,
            tenant_id,
            payments=line,
            currency="EUR",
            expected_total="100.00",
            reason="Friday",
        )["paid"]
        == 1
    )


def test_a_run_is_one_currency(session, business):
    net(session, business)
    euros = supplier_invoice(session, business, "ER-098-EUR", "2026-08-01")
    dollars = supplier_invoice(
        session, business, "ER-098-USD", "2026-08-01", currency="USD"
    )

    with pytest.raises(InvalidOperation, match="one currency"):
        execute_payment_run(
            session,
            business.tenant.id,
            payments=[
                {"invoice_id": euros.id, "amount": "10.00"},
                {"invoice_id": dollars.id, "amount": "10.00"},
            ],
            currency="EUR",
            expected_total="20.00",
            reason="Mixed",
        )
    assert open_invoice_amount(session, business.tenant.id, euros.id) == Decimal(1000)

    # Positive control: two runs, one currency each, both go through.
    for invoice, currency in ((euros, "EUR"), (dollars, "USD")):
        assert (
            execute_payment_run(
                session,
                business.tenant.id,
                payments=[{"invoice_id": invoice.id, "amount": "10.00"}],
                currency=currency,
                expected_total="10.00",
                reason="One currency",
            )["paid"]
            == 1
        )


def test_a_failed_run_leaves_nothing_behind(session, business):
    """Either every payment in a run stands, or none of them does."""
    net(session, business)
    first = supplier_invoice(session, business, "ER-098-T1", "2026-08-01")
    second = supplier_invoice(session, business, "ER-098-T2", "2026-08-02")
    third = supplier_invoice(session, business, "ER-098-T3", "2026-08-03")
    tenant_id = business.tenant.id

    # Somebody else settles the second invoice between the preview and the run.
    post_supplier_payment(session, tenant_id, second.id, "1000.00")
    events_before = len(business_events(session, tenant_id))

    with pytest.raises(InvalidOperation):
        execute_payment_run(
            session,
            tenant_id,
            payments=[
                {"invoice_id": first.id, "amount": "1000.00"},
                {"invoice_id": second.id, "amount": "1000.00"},
                {"invoice_id": third.id, "amount": "1000.00"},
            ],
            currency="EUR",
            expected_total="3000.00",
            reason="Friday run",
        )

    # Not a partial Friday: the first and third are exactly as they were.
    assert open_invoice_amount(session, tenant_id, first.id) == Decimal(1000)
    assert open_invoice_amount(session, tenant_id, third.id) == Decimal(1000)
    assert len(business_events(session, tenant_id)) == events_before

    # Positive control: the same run without the settled invoice pays both.
    result = execute_payment_run(
        session,
        tenant_id,
        payments=[
            {"invoice_id": first.id, "amount": "1000.00"},
            {"invoice_id": third.id, "amount": "1000.00"},
        ],
        currency="EUR",
        expected_total="2000.00",
        reason="Friday run",
    )
    assert result["paid"] == 2
    assert open_invoice_amount(session, tenant_id, first.id) == Decimal(0)


def test_a_run_is_recorded_as_one_decision(session, business):
    net(session, business)
    first = supplier_invoice(session, business, "ER-098-E1", "2026-08-01")
    second = supplier_invoice(
        session, business, "ER-098-E2", "2026-08-02", amount="250.00"
    )

    execute_payment_run(
        session,
        business.tenant.id,
        payments=[
            {"invoice_id": first.id, "amount": "1000.00"},
            {"invoice_id": second.id, "amount": "250.00"},
        ],
        currency="EUR",
        expected_total="1250.00",
        reason="September supplier run, approved by the owner",
        actor_context={"actor": "owner"},
    )

    (event,) = [
        entry
        for entry in business_events(session, business.tenant.id)
        if entry.event_type == "payments.run"
    ]
    import json

    payload = json.loads(event.payload)
    assert event.subject_type == "tenant"
    assert payload["reason"] == "September supplier run, approved by the owner"
    assert payload["currency"] == "EUR"
    assert payload["total"] == "1250.00"
    assert payload["count"] == 2
    assert {line["invoice_id"] for line in payload["payments"]} == {
        first.id,
        second.id,
    }
    assert all(line["payment_document_id"] for line in payload["payments"])
    assert payload["actor_context"] == {"actor": "owner"}


def test_a_payment_in_a_run_is_an_ordinary_payment(session, business):
    """A run is a record of a decision, not a document anything posts against."""
    net(session, business)
    alone = supplier_invoice(session, business, "ER-098-ALONE", "2026-08-01")
    in_run = supplier_invoice(session, business, "ER-098-INRUN", "2026-08-01")
    effective = datetime(2026, 8, 31, 9, tzinfo=UTC)

    single = post_supplier_payment(
        session, business.tenant.id, alone.id, "400.00", effective_at=effective
    )
    execute_payment_run(
        session,
        business.tenant.id,
        payments=[{"invoice_id": in_run.id, "amount": "400.00"}],
        currency="EUR",
        expected_total="400.00",
        reason="Friday run",
        effective_at=effective,
    )

    def shape(entries):
        return sorted(
            (entry.account, entry.debit_credit, Decimal(entry.amount))
            for entry in entries
        )

    run_entries = [
        row["control"]
        for row in financial_open_items(session, business.tenant.id)
        if row["document"].id == in_run.id
    ]
    assert shape(single) == [
        ("accounts_payable", "debit", Decimal(400)),
        ("cash", "credit", Decimal(400)),
    ]
    assert open_invoice_amount(session, business.tenant.id, in_run.id) == Decimal(600)
    assert open_invoice_amount(session, business.tenant.id, alone.id) == Decimal(600)
    assert run_entries  # settled through the same control entry as any other


def test_a_run_is_tenant_scoped(session, business):
    net(session, business)
    invoice = supplier_invoice(session, business, "ER-098-TEN", "2026-08-01")

    other = create_tenant(session, "Foreign GmbH")
    create_party(session, other.id, "Foreign Supplier", "supplier")

    # Another tenant can neither see nor pay this invoice.
    assert (
        preview_payment_run(session, other.id, pay_by=PAY_BY, as_of=AS_OF)["proposed"]
        == []
    )
    with pytest.raises(InvalidOperation, match="this tenant only"):
        execute_payment_run(
            session,
            other.id,
            payments=[{"invoice_id": invoice.id, "amount": "10.00"}],
            currency="EUR",
            expected_total="10.00",
            reason="Foreign run",
        )
    with pytest.raises(NotFound):
        preview_payment_run(session, "ten_missing", pay_by=PAY_BY, as_of=AS_OF)

    # Positive control: its own tenant pays it.
    assert (
        execute_payment_run(
            session,
            business.tenant.id,
            payments=[{"invoice_id": invoice.id, "amount": "10.00"}],
            currency="EUR",
            expected_total="10.00",
            reason="Own run",
        )["paid"]
        == 1
    )
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == Decimal(990)
