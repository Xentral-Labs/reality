"""Feature 168 business story: synthetic orders are invoiced and paid, differences stay honest.

The story runs producer → normaliser → shared core exactly as the settlement job
does, without the scheduler, and reads every outcome through public services.
"""

import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select

from reality.db.core import Document, LedgerEntry, SourceRecord
from reality.demo.international import DEMO_DATA_CUSTOMERS, DEMO_DATA_PAYMENT_TERM
from reality.integrations import demo_data as synthetic
from reality.services import core, payment_intake
from reality.services.finance.accounts import (
    create_account,
    list_accounts,
    set_default_account,
)
from reality.services.finance.credits import available_credit_items
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from reality.tools.finance import ADJUSTMENT_COMMAND, SETTLEMENT_COMMAND

AT = datetime(2026, 9, 10, 8, 0, tzinfo=UTC)
SEED, SCHEDULE = "story-seed", "sch_story"


def references(business):
    return {
        "parties": {
            "company": business.company.id,
            DEMO_DATA_CUSTOMERS[0][0]: business.customer.id,
        },
        "locations": {"A": business.location.id},
        "items": {key: business.item.id for key in ("P01", "P02", "P11", "P12")},
    }


def prepare(session, tenant):
    term = dict(DEMO_DATA_PAYMENT_TERM)
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


def find(business, wanted, *, limit=3000):
    """The first delivery index whose plan matches `wanted(plan, order)`."""
    refs = references(business)
    for index in range(limit):
        order = synthetic.produce(SCHEDULE, f"run_{index}", SEED, AT, refs)
        plan = synthetic.settlement_plan(
            SEED, SCHEDULE, f"{SCHEDULE}:run_{index}", order
        )
        if wanted(plan, order):
            return index
    raise AssertionError("no plan matches")


def enqueue(session, tenant, kind, external_id, payload):
    source, _job = core.enqueue_source(
        session, tenant, "demo_data", kind, external_id, payload, _commit=False
    )
    return source


def story(session, business, index, *, payments=None):
    """Order, invoice and the planned payments (or the first `payments`) of one delivery."""
    tenant = business.tenant.id
    external_id = f"{SCHEDULE}:run_{index}"
    order = synthetic.produce(SCHEDULE, f"run_{index}", SEED, AT, references(business))
    order_source = enqueue(session, tenant, "order", external_id, order)
    core.create_manual_document_with_lines(
        session,
        tenant,
        "sales_order",
        order["number"],
        order["customer_party_id"],
        order["lines"],
        order["gross_amount"],
        currency=order["currency"],
        ordered_at=order["ordered_at"],
        document_date=order["ordered_at"][:10],
        customer_reference=order["customer_reference"],
        sales_channel="demo_data",
        source_record_id=order_source.id,
        _commit=False,
    )
    plan = synthetic.settlement_plan(SEED, SCHEDULE, external_id, order)
    invoice_payload = synthetic.produce_invoice(order, external_id, plan)
    invoice_source = enqueue(
        session, tenant, "invoice", f"{external_id}:invoice", invoice_payload
    )
    _, invoice, _, _ = payment_intake.interpret_sales_invoice(
        session, tenant, invoice_source, synthetic.normalise_invoice(invoice_payload)
    )
    results = []
    for planned in plan.payments[: payments if payments is not None else None]:
        payload = synthetic.produce_payment(order, invoice_payload, plan, planned.index)
        source = enqueue(
            session,
            tenant,
            "payment",
            f"{external_id}:payment:{planned.index}",
            payload,
        )
        results.append(
            payment_intake.interpret_customer_payment(
                session, tenant, source, synthetic.normalise_payment(payload)
            )
        )
    return order, plan, invoice, results


def open_item(session, tenant, invoice):
    return next(
        row
        for row in core.financial_open_items(session, tenant)
        if row["document"].id == invoice.id
    )


def test_demo_order_to_cash_business_story(session, business):
    tenant = business.tenant.id
    prepare(session, tenant)
    reduction = create_account(
        session,
        tenant,
        code="reduction",
        name="Accepted reductions",
        role="customer_reduction",
    )
    set_default_account(
        session, tenant, role="customer_reduction", account_id=reduction["id"]
    )
    gross = Decimal(25)

    # Exact payments on both money paths settle silently.
    for path in ("bank", "provider"):
        index = find(
            business,
            lambda p, o, path=path: p.outcome == "exact" and p.money_path == path,
        )
        _, plan, invoice, results = story(session, business, index)
        assert results[0][3].amount == gross
        assert open_item(session, tenant, invoice)["status"] == "paid"
        if path == "provider":
            assert {r.type for r in plan.payments[0].references} >= {"shop_id"}

    # A short payment claiming the discount leaves exactly the difference open,
    # books no reduction, and shows paid and remaining separately.
    index = find(business, lambda p, o: p.outcome == "short_discount")
    _, plan, invoice, results = story(session, business, index)
    row = open_item(session, tenant, invoice)
    assert row["status"] == "partial"
    assert row["settled"] == plan.payments[0].amount
    assert row["open"] == gross - plan.payments[0].amount
    groups = set(
        session.scalars(
            select(LedgerEntry.posting_group_id).where(
                LedgerEntry.tenant_id == tenant,
                LedgerEntry.document_id.in_([invoice.id, results[0][1].id]),
            )
        )
    )
    assert len(groups) == 2  # invoice and payment only; no reduction booked

    # An overpayment settles the invoice and leaves the excess as available credit.
    index = find(business, lambda p, o: p.outcome == "over")
    _, plan, invoice, results = story(session, business, index)
    assert open_item(session, tenant, invoice)["status"] == "paid"
    excess = sum(p.amount for p in plan.payments) - gross
    credits = available_credit_items(session, tenant, side="customer")["items"]
    credit_documents = {results[i][1].id for i in range(len(results))}
    available = sum(
        (
            Decimal(item["open"])
            for item in credits
            if item["document_id"] in credit_documents
        ),
        Decimal(0),
    )
    assert available == excess

    # A payment nobody can match is recorded, offered as candidates, and settled
    # only when a person confirms one through the existing settlement flow.
    index = find(business, lambda p, o: p.outcome == "unmatched")
    _, plan, invoice, results = story(session, business, index)
    _, payment, _, allocation, _ = results[0]
    assert allocation is None
    assert open_item(session, tenant, invoice)["status"] == "open"
    candidates = payment_intake.payment_candidates(session, tenant, payment.id)
    assert invoice.id in {c.invoice_id for c in candidates}
    proposal = create_change_proposal(
        session,
        tenant,
        SETTLEMENT_COMMAND,
        {
            "document_id": payment.id,
            "mode": "allocate_credit",
            "expected_revision": list_accounts(session, tenant)["revision"],
            "amount": str(gross),
            "invoice_id": invoice.id,
        },
        actor_type="human",
    )
    outcome = json.loads(
        approve_and_execute_proposal(session, tenant, proposal.id).output
    )
    assert outcome["allocation_id"]
    assert open_item(session, tenant, invoice)["status"] == "paid"
    assert payment_intake.payment_candidates(session, tenant, payment.id) == []

    # A withheld small amount stays open until a person accepts the remainder.
    index = find(business, lambda p, o: p.outcome == "short_withheld")
    _, plan, invoice, results = story(session, business, index)
    remainder = gross - plan.payments[0].amount
    assert open_item(session, tenant, invoice)["open"] == remainder
    accepted = create_change_proposal(
        session,
        tenant,
        ADJUSTMENT_COMMAND,
        {
            "invoice_id": invoice.id,
            "amount": str(remainder),
            "reason_category": "accepted_small_remainder",
            "reason": "Freight withheld; accepted after review.",
            "expected_revision": list_accounts(session, tenant)["revision"],
        },
        actor_type="human",
    )
    approve_and_execute_proposal(session, tenant, accepted.id)
    row = open_item(session, tenant, invoice)
    assert row["status"] == "paid" and row["open"] == 0
    cash = session.scalar(
        select(func.sum(LedgerEntry.amount)).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.document_id == results[0][1].id,
            LedgerEntry.debit_credit == "debit",
        )
    )
    assert cash == plan.payments[0].amount  # the acceptance moved no cash

    # A partial payment followed by the rest closes the invoice.
    index = find(business, lambda p, o: p.outcome == "short_partial")
    _, plan, invoice, results = story(session, business, index)
    assert len(results) == 2 and open_item(session, tenant, invoice)["status"] == "paid"

    # Late and never: nothing arrives yet, the claim stays open and honest.
    for outcome in ("late", "never"):
        index = find(business, lambda p, o, outcome=outcome: p.outcome == outcome)
        _, plan, invoice, results = story(session, business, index, payments=0)
        assert results == [] and open_item(session, tenant, invoice)["open"] == gross

    # Every record traces to its synthetic source and run.
    documents = list(
        session.scalars(
            select(Document).where(
                Document.tenant_id == tenant,
                Document.type.in_(["sales_order", "sales_invoice", "customer_payment"]),
            )
        )
    )
    assert documents and all(document.source_record_id for document in documents)
    sources = {
        source.id: source
        for source in session.scalars(
            select(SourceRecord).where(SourceRecord.tenant_id == tenant)
        )
    }
    for document in documents:
        source = sources[document.source_record_id]
        assert source.source_system == "demo_data"
        assert source.external_id.startswith(f"{SCHEDULE}:run_")
        assert json.loads(source.payload)["synthetic"] is True
