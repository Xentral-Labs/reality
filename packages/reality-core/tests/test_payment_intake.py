"""The shared payment intake core: record always, allocate stated links, propose the rest.

Feature 168. These tests feed the core normalised evidence directly, so a later
provider normaliser adds mapping tests only, not behaviour tests.
"""

import ast
import inspect
import textwrap
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import Document, LedgerEntry, SettlementAllocation
from reality.services import core, payment_intake
from reality.services.finance.accounts import list_accounts, update_account
from reality.services.payment_intake import (
    NormalisedInvoice,
    NormalisedInvoiceLine,
    NormalisedPayment,
    Reference,
)

AT = datetime(2026, 9, 10, 8, 0, tzinfo=UTC)
TERM = ("DEMO-14-2", "14 days net, 2 % within 7 days", 14)


def _source(session, tenant, source_type, external_id, payload=None):
    source, _job = core.enqueue_source(
        session,
        tenant,
        "demo_data",
        source_type,
        external_id,
        payload or {"synthetic": True, "external_id": external_id},
        _commit=False,
    )
    return source


def _order(session, business, external_id="sch:run", amount="100", customer=None):
    tenant = business.tenant.id
    customer = customer or business.customer
    source = _source(session, tenant, "order", external_id)
    document, lines = core.create_manual_document_with_lines(
        session,
        tenant,
        "sales_order",
        f"DEMO-{external_id}",
        customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": amount,
                "gross_amount": amount,
                "unit": "pcs",
                "source_line_id": "1",
            }
        ],
        amount,
        customer_reference=f"PO-{external_id}",
        source_record_id=source.id,
        _commit=False,
    )
    return source, document, lines


def _term(session, tenant):
    try:
        core.payment_term_by_code(session, tenant, TERM[0])
    except core.NotFound:
        core.create_payment_term(
            session, tenant, *TERM, discount_percent="2", discount_days=7
        )


def _normalised_invoice(business, order_external_id, number, amount="100", **extra):
    return NormalisedInvoice(
        order_source_system="demo_data",
        order_source_type="order",
        order_external_id=extra.pop("order_ref", order_external_id),
        number=number,
        party_id=extra.pop("party_id", business.customer.id),
        currency=extra.pop("currency", "EUR"),
        issued_at=AT,
        payment_term_code=extra.pop("payment_term_code", TERM[0]),
        gross_amount=Decimal(amount),
        lines=(
            NormalisedInvoiceLine(
                order_source_line_id=extra.pop("order_source_line_id", "1"),
                source_line_id="1",
                item_id=business.item.id,
                quantity=Decimal(1),
                unit_price=Decimal(amount),
                gross_amount=Decimal(amount),
                unit="pcs",
            ),
        ),
        **extra,
    )


def _invoice(
    session, business, external_id="sch:run", number="INV-1", amount="100", **extra
):
    tenant = business.tenant.id
    _term(session, tenant)
    _order(session, business, external_id, amount, customer=extra.pop("customer", None))
    source = _source(session, tenant, "invoice", f"{external_id}:invoice")
    return payment_intake.interpret_sales_invoice(
        session,
        tenant,
        source,
        _normalised_invoice(business, external_id, number, amount, **extra),
    )


def _pay(
    session, business, amount, references=(), external_id="sch:run:payment:1", **extra
):
    tenant = business.tenant.id
    payload = {
        "synthetic": True,
        "references": [reference.model_dump() for reference in references],
        "remittance_text": extra.pop("remittance_text", ""),
    }
    source = _source(session, tenant, "payment", external_id, payload)
    normalised = NormalisedPayment(
        party_id=extra.pop("party_id", business.customer.id),
        amount=Decimal(amount),
        currency=extra.pop("currency", "EUR"),
        effective_at=AT,
        external_payment_id=f"txn-{external_id}",
        references=tuple(references),
        remittance_text=payload["remittance_text"],
        **extra,
    )
    return payment_intake.interpret_customer_payment(
        session, tenant, source, normalised
    )


def _count(session, model, tenant):
    return session.scalar(
        select(func.count()).select_from(model).where(model.tenant_id == tenant)
    )


# --- invoice core --------------------------------------------------------------


def test_invoice_core_links_lines_posts_once_and_replays(session, business):
    tenant = business.tenant.id
    source, invoice, lines, entries = _invoice(session, business)
    order_lines = _order_lines(session, tenant)
    assert invoice.type == "sales_invoice" and invoice.source_record_id == source.id
    assert [line.billed_document_line_id for line in lines] == [order_lines[0].id]
    assert (
        invoice.payment_term_id
        == core.payment_term_by_code(session, tenant, TERM[0]).id
    )
    assert sorted((e.account, e.debit_credit, e.amount) for e in entries) == [
        ("accounts_receivable", "debit", Decimal(100)),
        ("sales_revenue", "credit", Decimal(100)),
    ]
    assert core.open_invoice_amount(session, tenant, invoice.id) == Decimal(100)
    again = payment_intake.interpret_sales_invoice(
        session, tenant, source, _normalised_invoice(business, "sch:run", "INV-1")
    )
    assert again[1].id == invoice.id and len(again[3]) == 2
    assert _count(session, Document, tenant) == 2  # one order, one invoice


def _order_lines(session, tenant):
    from reality.db.core import DocumentLine

    return list(
        session.scalars(
            select(DocumentLine)
            .join(Document, Document.id == DocumentLine.document_id)
            .where(Document.tenant_id == tenant, Document.type == "sales_order")
        )
    )


@pytest.mark.parametrize(
    "broken, message",
    [
        ({"order_ref": "sch:missing"}, "order Reality does not hold"),
        ({"order_source_line_id": "9"}, "order line Reality does not hold"),
        ({"payment_term_code": "NOPE"}, "payment term Reality does not hold"),
    ],
)
def test_invoice_core_refuses_unknown_order_line_or_term(
    session, business, broken, message
):
    tenant = business.tenant.id
    _term(session, tenant)
    _order(session, business)
    source = _source(session, tenant, "invoice", "sch:run:invoice")
    with pytest.raises(core.InvalidOperation, match=message), session.begin_nested():
        payment_intake.interpret_sales_invoice(
            session,
            tenant,
            source,
            _normalised_invoice(business, "sch:run", "INV-1", **broken),
        )
    assert _count(session, Document, tenant) == 1
    assert _count(session, LedgerEntry, tenant) == 0


def test_invoice_core_refuses_another_party_than_the_order(session, business):
    tenant = business.tenant.id
    _term(session, tenant)
    _order(session, business)
    source = _source(session, tenant, "invoice", "sch:run:invoice")
    with pytest.raises(core.InvalidOperation, match="another party"):
        payment_intake.interpret_sales_invoice(
            session,
            tenant,
            source,
            _normalised_invoice(
                business, "sch:run", "INV-1", party_id=business.supplier.id
            ),
        )


# --- payment core: tier 1 and tier 2 -------------------------------------------


def test_exact_payment_with_invoice_number_settles_the_invoice(session, business):
    tenant = business.tenant.id
    _, invoice, _, _ = _invoice(session, business)
    source, payment, entries, allocation, resolution = _pay(
        session, business, "100", [Reference(type="invoice_number", value="INV-1")]
    )
    assert payment.type == "customer_payment" and payment.source_record_id == source.id
    assert sorted((e.account, e.debit_credit) for e in entries) == [
        ("accounts_receivable", "credit"),
        ("cash", "debit"),
    ]
    assert allocation.amount == Decimal(100) and resolution.unambiguous.id == invoice.id
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0
    assert payment_intake.unallocated_amount(session, tenant, payment.id) == 0


@pytest.mark.parametrize(
    "reference",
    [
        Reference(type="shop_id", value="sch:run"),
        Reference(type="shop_order_number", value="DEMO-sch:run"),
        Reference(type="customer_reference", value="PO-sch:run"),
    ],
)
def test_order_references_resolve_through_billed_lines(session, business, reference):
    tenant = business.tenant.id
    _, invoice, _, _ = _invoice(session, business)
    _, _, _, allocation, resolution = _pay(session, business, "100", [reference])
    assert resolution.unambiguous.id == invoice.id
    assert allocation.amount == Decimal(100)
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0


def test_short_payment_allocates_what_arrived_and_leaves_the_rest_open(
    session, business
):
    tenant = business.tenant.id
    _, invoice, _, _ = _invoice(session, business, amount="1000")
    _, payment, _, allocation, _ = _pay(
        session, business, "980", [Reference(type="invoice_number", value="INV-1")]
    )
    assert allocation.amount == Decimal(980)
    assert core.open_invoice_amount(session, tenant, invoice.id) == Decimal(20)
    assert payment_intake.unallocated_amount(session, tenant, payment.id) == 0
    # No reduction, credit note or write-off was booked: two posting groups only.
    groups = set(
        session.scalars(
            select(LedgerEntry.posting_group_id).where(LedgerEntry.tenant_id == tenant)
        )
    )
    assert len(groups) == 2


def test_over_payment_settles_the_invoice_and_keeps_the_excess_as_credit(
    session, business
):
    tenant = business.tenant.id
    _, invoice, _, _ = _invoice(session, business, amount="1000")
    _, payment, _, allocation, _ = _pay(
        session, business, "1020", [Reference(type="invoice_number", value="INV-1")]
    )
    assert allocation.amount == Decimal(1000)
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0
    assert payment_intake.unallocated_amount(session, tenant, payment.id) == Decimal(20)


def test_second_payment_closes_a_partial_and_a_duplicate_stays_credit(
    session, business
):
    tenant = business.tenant.id
    _, invoice, _, _ = _invoice(session, business, amount="100")
    ref = [Reference(type="invoice_number", value="INV-1")]
    _pay(session, business, "60", ref, external_id="sch:run:payment:1")
    _, _second, _, allocation, _ = _pay(
        session, business, "40", ref, external_id="sch:run:payment:2"
    )
    assert allocation.amount == Decimal(40)
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0
    _, third, _, none, resolution = _pay(
        session, business, "100", ref, external_id="sch:run:payment:3"
    )
    assert none is None
    assert "already settled" in " ".join(resolution.reasons)
    assert payment_intake.unallocated_amount(session, tenant, third.id) == Decimal(100)
    assert _count(session, Document, tenant) == 5  # order, invoice, three payments


def test_replay_of_the_same_source_records_no_second_cash_entry(session, business):
    tenant = business.tenant.id
    _invoice(session, business)
    ref = [Reference(type="invoice_number", value="INV-1")]
    source, payment, _entries, allocation, _ = _pay(session, business, "100", ref)
    again = payment_intake.interpret_customer_payment(
        session,
        tenant,
        source,
        NormalisedPayment(
            party_id=business.customer.id,
            amount=Decimal(100),
            currency="EUR",
            effective_at=AT,
            external_payment_id="txn",
            references=tuple(ref),
        ),
    )
    assert again[1].id == payment.id and again[3].id == allocation.id
    assert _count(session, LedgerEntry, tenant) == 4
    assert _count(session, SettlementAllocation, tenant) == 1


def test_payment_is_pinned_to_the_invoice_control_account(session, business):
    _, _, _, invoice_entries = _invoice(session, business)
    _, _, entries, allocation, _ = _pay(
        session, business, "100", [Reference(type="invoice_number", value="INV-1")]
    )
    receivable = next(e for e in entries if e.account == "accounts_receivable")
    control = next(e for e in invoice_entries if e.account == "accounts_receivable")
    assert receivable.account_id == control.account_id
    assert allocation.invoice_ledger_entry_id == control.id


def test_blocked_control_account_records_the_money_without_allocating(
    session, business
):
    tenant = business.tenant.id
    _, invoice, _, invoice_entries = _invoice(session, business)
    control = next(e for e in invoice_entries if e.account == "accounts_receivable")
    accounts = list_accounts(session, tenant)
    from reality.services.finance.accounts import create_account, set_default_account

    created = create_account(
        session,
        tenant,
        code="1201",
        name="Receivables 2",
        role="accounts_receivable",
        expected_revision=accounts["revision"],
        _commit=False,
    )
    set_default_account(
        session,
        tenant,
        role="accounts_receivable",
        account_id=created["id"],
        expected_revision=list_accounts(session, tenant)["revision"],
        _commit=False,
    )
    update_account(
        session,
        tenant,
        control.account_id,
        state="blocked",
        expected_revision=list_accounts(session, tenant)["revision"],
        _commit=False,
    )
    _, payment, entries, allocation, resolution = _pay(
        session, business, "100", [Reference(type="invoice_number", value="INV-1")]
    )
    assert allocation is None
    assert "blocked account" in " ".join(resolution.reasons)
    assert (
        next(e for e in entries if e.account == "accounts_receivable").account_id
        == created["id"]
    )
    assert payment_intake.unallocated_amount(session, tenant, payment.id) == Decimal(
        100
    )
    assert core.open_invoice_amount(session, tenant, invoice.id) == Decimal(100)


# --- resolver: what never allocates ----------------------------------------------


def test_unposted_wrong_party_wrong_currency_and_customer_number_never_allocate(
    session, business
):
    tenant = business.tenant.id
    _term(session, tenant)
    # An unposted invoice of the customer.
    _order(session, business, "sch:a")
    core.create_manual_document_with_lines(
        session,
        tenant,
        "sales_invoice",
        "INV-UNPOSTED",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": "100",
                "gross_amount": "100",
                "unit": "pcs",
            }
        ],
        "100",
        payment_term_code=TERM[0],
        _commit=False,
    )
    # A posted invoice of another customer with the same number pattern.
    other = core.create_party(session, tenant, "Other GmbH", "customer")
    _invoice(session, business, "sch:b", "INV-OTHER", customer=other, party_id=other.id)
    # A posted USD invoice of the customer.
    _invoice(session, business, "sch:c", "INV-USD", currency="USD")
    cases = [
        (Reference(type="invoice_number", value="INV-UNPOSTED"), "not posted"),
        (
            Reference(type="invoice_number", value="INV-OTHER"),
            "no invoice INV-OTHER for this customer",
        ),
        (Reference(type="invoice_number", value="INV-USD"), "is in USD, not EUR"),
        (
            Reference(type="customer_number", value="C-1"),
            "identifies the customer only",
        ),
        (Reference(type="shop_id", value="sch:zzz"), "no order with shop id"),
    ]
    for index, (reference, reason) in enumerate(cases, 1):
        _, payment, _, allocation, resolution = _pay(
            session, business, "100", [reference], external_id=f"sch:x:payment:{index}"
        )
        assert allocation is None, reference
        assert any(reason in r for r in resolution.reasons), (
            reference,
            resolution.reasons,
        )
        assert payment_intake.unallocated_amount(
            session, tenant, payment.id
        ) == Decimal(100)


def test_two_invoices_for_one_order_and_a_consolidated_invoice_yield_no_allocation(
    session, business
):
    tenant = business.tenant.id
    _term(session, tenant)
    # Two invoices billing the same order line.
    _order(session, business, "sch:split", "100")
    for number in ("INV-S1", "INV-S2"):
        source = _source(session, tenant, "invoice", f"sch:split:{number}")
        payment_intake.interpret_sales_invoice(
            session,
            tenant,
            source,
            _normalised_invoice(business, "sch:split", number, "50"),
        )
    _, _, _, allocation, resolution = _pay(
        session, business, "100", [Reference(type="shop_id", value="sch:split")]
    )
    assert allocation is None
    assert len(resolution.invoices) == 2
    assert "several invoices" in " ".join(resolution.reasons)


def test_reversed_invoice_does_not_resolve(session, business):
    tenant = business.tenant.id
    _, invoice, _, entries = _invoice(session, business)
    core.reverse_ledger_posting_group(
        session, tenant, entries[0].posting_group_id, reason="test"
    )
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0
    _, _, _, allocation, resolution = _pay(
        session, business, "100", [Reference(type="invoice_number", value="INV-1")]
    )
    assert allocation is None and "not posted" in " ".join(resolution.reasons)


# --- candidates (tier 3) ----------------------------------------------------------


def test_candidates_have_reasons_and_write_nothing(session, business):
    tenant = business.tenant.id
    _invoice(session, business, "sch:one", "INV-100", "100")
    _invoice(session, business, "sch:two", "INV-250", "250")
    _, payment, _, allocation, _ = _pay(
        session,
        business,
        "100",
        [Reference(type="customer_number", value="C-1")],
        remittance_text="thanks, ref INV-250 and something",
    )
    assert allocation is None
    before = {
        m: _count(session, m, tenant)
        for m in (Document, LedgerEntry, SettlementAllocation)
    }
    first = payment_intake.payment_candidates(session, tenant, payment.id)
    second = payment_intake.payment_candidates(session, tenant, payment.id)
    assert first == second
    assert {m: _count(session, m, tenant) for m in before} == before
    by_number = {candidate.number: candidate for candidate in first}
    assert by_number["INV-100"].reasons == ("amount equals the open amount",)
    assert by_number["INV-250"].reasons == (
        "invoice number appears in the remittance text",
    )
    assert by_number["INV-100"].open_amount == Decimal(100)


def test_ambiguous_reference_produces_candidates_and_allocation_ends_them(
    session, business
):
    tenant = business.tenant.id
    _term(session, tenant)
    _order(session, business, "sch:split", "100")
    for number in ("INV-S1", "INV-S2"):
        source = _source(session, tenant, "invoice", f"sch:split:{number}")
        payment_intake.interpret_sales_invoice(
            session,
            tenant,
            source,
            _normalised_invoice(business, "sch:split", number, "50"),
        )
    _, payment, entries, _, _ = _pay(
        session, business, "50", [Reference(type="shop_id", value="sch:split")]
    )
    candidates = payment_intake.payment_candidates(session, tenant, payment.id)
    assert {c.number for c in candidates} == {"INV-S1", "INV-S2"}
    assert all(
        c.reasons
        == (
            "amount equals the open amount",
            "stated reference names this invoice among others",
        )
        for c in candidates
    )
    invoice = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant, Document.number == "INV-S1"
        )
    )
    core.allocate_settlement(
        session,
        tenant,
        next(e for e in entries if e.account == "accounts_receivable").id,
        core._settlement_control_entry(session, tenant, invoice.id).id,
        Decimal(50),
        _commit=False,
    )
    assert payment_intake.payment_candidates(session, tenant, payment.id) == []


def test_candidates_exist_for_customer_payments_only(session, business):
    tenant = business.tenant.id
    _, invoice, _, _ = _invoice(session, business)
    with pytest.raises(core.InvalidOperation):
        payment_intake.payment_candidates(session, tenant, invoice.id)


# --- guard rails -------------------------------------------------------------------


def test_nothing_in_the_core_divides_or_multiplies_a_rate():
    """Spec 088 DR-007 carried over: amounts are stated, never derived."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(payment_intake)))
    arithmetic = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Div | ast.FloorDiv | ast.Mult)
    ]
    assert arithmetic == []


def test_core_imports_only_services_and_db():
    source = inspect.getsource(payment_intake)
    for forbidden in (
        "reality.web",
        "reality.mcp",
        "reality.tools",
        "reality.jobs",
        "reality.integrations",
    ):
        assert forbidden not in source, forbidden


def test_matching_cost_does_not_grow_with_the_customers_settled_history(
    session, business
):
    """Spec 181 FR-001: candidates and interpretation read a bounded number of times.

    Paid invoices are history. Before this rule the candidate search measured every
    invoice the customer ever had against every allocation of the company, so one
    payment cost more with every order recorded.
    """
    from sqlalchemy import event

    tenant = business.tenant.id

    def settle(count, prefix):
        for index in range(count):
            _invoice(session, business, f"{prefix}:{index}", f"{prefix}-{index}", "40")
            _pay(
                session,
                business,
                "40",
                [Reference(type="invoice_number", value=f"{prefix}-{index}")],
                external_id=f"{prefix}:{index}:payment",
            )

    def cost(operation):
        counts = [0]
        bind = session.get_bind()

        def count(*args):
            counts[0] += 1

        event.listen(bind, "before_cursor_execute", count)
        try:
            result = operation()
        finally:
            event.remove(bind, "before_cursor_execute", count)
        return counts[0], result

    settle(2, "few")
    _invoice(session, business, "open:a", "OPEN-A", "77")
    small_candidates, first = cost(
        lambda: payment_intake.payment_candidates(
            session,
            tenant,
            _pay(
                session,
                business,
                "77",
                [Reference(type="customer_number", value="C-1")],
                external_id="probe:1",
            )[1].id,
        )
    )
    assert {c.number for c in first} == {"OPEN-A"}
    settle(10, "many")
    large_candidates, second = cost(
        lambda: payment_intake.payment_candidates(
            session,
            tenant,
            _pay(
                session,
                business,
                "77",
                [Reference(type="customer_number", value="C-1")],
                external_id="probe:2",
            )[1].id,
        )
    )
    assert {c.number for c in second} == {"OPEN-A"}
    assert large_candidates == small_candidates, (small_candidates, large_candidates)
    # The bounded allocation read is what keeps a single measurement flat too.
    invoice = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant, Document.number == "OPEN-A"
        )
    )
    single, amount = cost(lambda: core.open_invoice_amount(session, tenant, invoice.id))
    assert amount == Decimal(77)
    assert single <= 8, single


def test_the_candidate_search_does_not_read_more_as_the_history_settles(
    session, business
):
    """FR-001, in the measure the statement count cannot show.

    The search asked a bounded number of times and read an unbounded number of
    rows: every invoice the customer ever had, settled or not, and a settlement
    position for each. On a company of four hundred invoices that was 55 ms where
    fifty took 11 — flat in statements, growing in work.

    Rows read is the measure that sees it, and it is the same number on any host.
    """
    from sqlalchemy import event

    tenant = business.tenant.id

    def settle(count, prefix):
        for index in range(count):
            _invoice(session, business, f"{prefix}:{index}", f"{prefix}-{index}", "40")
            _pay(
                session,
                business,
                "40",
                [Reference(type="invoice_number", value=f"{prefix}-{index}")],
                external_id=f"{prefix}:{index}:payment",
            )

    def rows_read(operation):
        counted = [0]
        bind = session.get_bind()

        def after(conn, cursor, *args):
            if cursor.rowcount and cursor.rowcount > 0:
                counted[0] += cursor.rowcount

        event.listen(bind, "after_cursor_execute", after)
        try:
            result = operation()
        finally:
            event.remove(bind, "after_cursor_execute", after)
        return counted[0], result

    def candidates(probe):
        return lambda: payment_intake.payment_candidates(
            session,
            tenant,
            _pay(
                session,
                business,
                "77",
                [Reference(type="customer_number", value="C-1")],
                external_id=probe,
            )[1].id,
        )

    settle(2, "few")
    _invoice(session, business, "open:a", "OPEN-A", "77")
    small, first = rows_read(candidates("rows:1"))
    assert {c.number for c in first} == {"OPEN-A"}

    settle(20, "many")
    large, second = rows_read(candidates("rows:2"))
    assert {c.number for c in second} == {"OPEN-A"}

    assert large <= small + 10, (
        f"twenty more settled invoices cost {large - small} more rows to search"
    )
