"""Customer refunds share credit capacity, review and exact historical evidence."""

import json
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from reality.db.core import (
    BusinessEvent,
    Document,
    LedgerEntry,
    Movement,
    SettlementAllocation,
)
from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_document,
    create_tenant,
    open_invoice_amount,
    post_sales_credit_note,
    reverse_ledger_posting_group,
)
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)
from reality.tools.application import approve_and_execute_proposal


def obligation(session, business, direction="customer"):
    doc = create_document(
        session,
        business.tenant.id,
        "credit_note",
        "CR-126",
        business.customer.id,
        "300",
        currency="USD",
    )
    post_sales_credit_note(session, business.tenant.id, doc.id)
    return doc


def prepare(
    session, business, invoice, direction="customer", request="refund-126", **changes
):
    args = {
        "credit_note_id": invoice.id,
        "amount": "125",
        "refund_number": "REF-126",
        "effective_at": "2026-09-08T12:00:00Z",
    }
    args.update(changes)
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "customer_refund_post",
        args,
        request_id=request,
    )


def confirm(session, business, proposal):
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirmed=True,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
    )


@pytest.mark.parametrize("direction", ["customer"])
def test_partial_refund_preview_exact_receipt_recovery_and_remainder(
    session, business, direction
):
    invoice = obligation(session, business, direction)
    proposal = prepare(session, business, invoice, direction)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2
    assert session.scalar(select(func.count()).select_from(SettlementAllocation)) == 0
    review = json.loads(proposal.input)["_delivery_review"]
    assert Decimal(review["state"]["open_before"]) == 300
    assert Decimal(review["state"]["open_after"]) == 175
    with pytest.raises(InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    assert len(detail["receipt"]["records"]) == 2
    assert Decimal(detail["observation"]["open"]) == 175
    entries = [session.get(LedgerEntry, r["id"]) for r in detail["receipt"]["records"]]
    assert {(e.account, e.debit_credit, e.amount, e.currency) for e in entries} == {
        (
            "accounts_receivable",
            "debit",
            Decimal(125),
            "USD",
        ),
        (
            "cash",
            "credit",
            Decimal(125),
            "USD",
        ),
    }
    confirm(session, business, proposal)
    receipt = detail["receipt"]
    proposal.status = "executing"
    proposal.output = "{}"
    session.commit()
    with pytest.raises(InvalidOperation, match="unresolved"):
        prepare(
            session,
            business,
            invoice,
            direction,
            request="unknown-overlap",
            amount="10",
        )
    assert (
        reconcile_delivery(session, business.tenant.id, proposal.id)["receipt"]
        == receipt
    )
    remainder = prepare(
        session, business, invoice, direction, request="remainder", amount="175"
    )
    confirm(session, business, remainder)
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == 0
    assert session.scalar(select(func.count()).select_from(SettlementAllocation)) == 2
    assert session.scalar(select(func.count()).select_from(Movement)) == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"amount": "301"},
        {"amount": "0"},
        {"amount": "NaN"},
        {"amount": "0.00001"},
        {"source_record_id": "foreign"},
        {"effective_at": "invalid"},
        {"unexpected": True},
    ],
)
def test_invalid_refund_is_inert(session, business, changes):
    invoice = obligation(session, business)
    with pytest.raises((InvalidOperation, NotFound)):
        prepare(session, business, invoice, **changes)
    assert session.scalar(select(func.count()).select_from(Document)) == 1
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2


def test_foreign_wrong_type_and_current_actor(session, business):
    invoice = obligation(session, business)
    wrong = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "WRONG",
        business.customer.id,
        "300",
    )
    with pytest.raises(InvalidOperation):
        prepare(session, business, wrong)
    foreign = create_tenant(session, "Foreign refund tenant")
    with pytest.raises(NotFound):
        prepare_delivery_action(
            session,
            foreign.id,
            "customer_refund_post",
            {"credit_note_id": invoice.id, "amount": "1"},
            request_id="foreign",
        )
    proposal = prepare(session, business, invoice)
    with pytest.raises(NotFound):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirmed=True,
            review_token=json.loads(proposal.input)["_delivery_review"]["token"],
            confirming_principal=SimpleNamespace(
                user_id="absent", is_platform_admin=False
            ),
        )


def test_stale_allocation_and_historical_reversal(session, business):
    invoice = obligation(session, business)
    first = prepare(session, business, invoice)
    stale = prepare(session, business, invoice, request="stale", amount="50")
    confirm(session, business, first)
    with pytest.raises(InvalidOperation, match="review"):
        confirm(session, business, stale)
    assert stale.status == "proposed"
    receipt = json.loads(first.output)
    entry = session.get(LedgerEntry, receipt["records"][0]["id"])
    reverse_ledger_posting_group(
        session, business.tenant.id, entry.posting_group_id, reason="Incorrect refund"
    )
    detail = delivery_proposal_detail(session, business.tenant.id, first.id)
    assert detail["verification"] == "verified"
    assert Decimal(detail["observation"]["open"]) == 300
    assert detail["observation"]["allocation_active"] is False


def test_incomplete_proof_stays_unresolved_and_default_reference_is_supported(
    session, business
):
    invoice = obligation(session, business)
    proposal = prepare(
        session, business, invoice, refund_number=None, effective_at=None
    )
    confirm(session, business, proposal)
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "verified"
    )
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "settlement.allocated",
        )
    )
    event.action_id = None
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


@pytest.mark.parametrize("direction", ["customer"])
def test_refund_http_review_and_confirmation(session, business, direction):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    invoice = obligation(session, business, direction)
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            credits = client.get(
                f"{base}/finance/open-items?flow=customer-credit&item_status=outstanding&size=25"
            )
            assert credits.status_code == 200, credits.text
            assert credits.json()["items"][0]["document_id"] == invoice.id
            assert credits.json()["page"]["size"] == 25
            response = client.post(
                f"{base}/delivery-actions/prepare",
                json={
                    "tool": "customer_refund_post",
                    "request_id": "http",
                    "arguments": {"credit_note_id": invoice.id, "amount": "100"},
                },
            )
            assert response.status_code == 200, response.text
            proposal = response.json()
            response = client.post(
                f"{base}/change-proposals/{proposal['id']}/approve",
                json={"confirmed": True, "review_token": proposal["review"]["token"]},
            )
            assert response.status_code == 200, response.text
            assert (
                client.get(f"{base}/delivery-actions/{proposal['id']}").json()[
                    "verification"
                ]
                == "verified"
            )
    finally:
        app.dependency_overrides.clear()


def test_original_refund_source_is_preserved(session, business):
    from reality.db.core import SourceRecord
    from reality.services.core import create_master_source_record

    invoice = obligation(session, business)
    payload = {"amount": "125", "bank_reference": "Original <bank> note"}
    source = create_master_source_record(
        session, business.tenant.id, "refund", "bank", "bank-126", payload
    )
    proposal = prepare(session, business, invoice, source_record_id=source.id)
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    assert {"kind": "source_record", "id": source.id} in detail["links"]
    assert json.loads(session.get(SourceRecord, source.id).payload) == payload
    for record in detail["receipt"]["records"]:
        assert session.get(LedgerEntry, record["id"]).source_record_id == source.id


def test_reversed_invoice_rejects_stale_and_new_refund(session, business):
    invoice = obligation(session, business)
    proposal = prepare(session, business, invoice)
    control = json.loads(proposal.input)["_delivery_review"]["state"]["control"]
    reverse_ledger_posting_group(
        session, business.tenant.id, control["posting_group_id"], reason="Wrong invoice"
    )
    with pytest.raises(InvalidOperation, match="reversed"):
        confirm(session, business, proposal)
    with pytest.raises(InvalidOperation, match="reversed"):
        prepare(session, business, invoice, request="new")
    assert session.scalar(select(func.count()).select_from(SettlementAllocation)) == 0


def test_malformed_attributed_amount_is_not_verified(session, business):
    invoice = obligation(session, business)
    proposal = prepare(session, business, invoice)
    confirm(session, business, proposal)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "document.recorded",
        )
    )
    payload = json.loads(event.payload)
    payload["amount"] = "not a number"
    event.payload = json.dumps(payload)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_concurrent_reviews_cannot_silently_spend_changed_capacity(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, build_engine
    from reality.services.core import create_party

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as session:
            tenant = create_tenant(session, "Concurrent refund test")
            party = create_party(session, tenant.id, "Customer", "customer")
            business = SimpleNamespace(tenant=tenant, customer=party)
            invoice = obligation(session, business)
            first = prepare(session, business, invoice, request="first", amount="100")
            second = prepare(session, business, invoice, request="second", amount="100")
            claims = [
                (p.id, json.loads(p.input)["_delivery_review"]["token"])
                for p in (first, second)
            ]
            tenant_id, invoice_id = tenant.id, invoice.id
        gate = Barrier(2)

        def execute(claim):
            with factory() as connection:
                gate.wait(timeout=10)
                try:
                    approve_and_execute_proposal(
                        connection,
                        tenant_id,
                        claim[0],
                        confirmed=True,
                        review_token=claim[1],
                    )
                    return True
                except InvalidOperation as error:
                    assert "review" in str(error) or "unresolved" in str(error)
                    return False

        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(execute, claims)) == [False, True]
        with factory() as session:
            assert open_invoice_amount(session, tenant_id, invoice_id) == Decimal(200)
            assert (
                session.scalar(select(func.count()).select_from(SettlementAllocation))
                == 1
            )
    finally:
        engine.dispose()


@pytest.mark.parametrize("amount", ["0.0001", "125.1234", "125.00000"])
def test_supported_refund_precision_is_preserved(session, business, amount):
    invoice = obligation(session, business)
    proposal = prepare(session, business, invoice, amount=amount)
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    for record in detail["receipt"]["records"]:
        assert session.get(LedgerEntry, record["id"]).amount == Decimal(amount)
    assert Decimal(detail["observation"]["open"]) == Decimal(300) - Decimal(amount)


def test_netting_consumes_credit_and_stales_review(session, business):
    from reality.services.core import allocate_credit_note, post_sales_invoice

    credit = obligation(session, business)
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "INV-NET",
        business.customer.id,
        "200",
        currency="USD",
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)
    old = prepare(session, business, credit, amount="20")
    allocate_credit_note(session, business.tenant.id, credit.id, invoice.id, "50")
    with pytest.raises(InvalidOperation, match="review"):
        confirm(session, business, old)
    fresh = prepare(session, business, credit, request="after-net", amount="20")
    review = json.loads(fresh.input)["_delivery_review"]
    assert Decimal(review["state"]["open_before"]) == 250
    assert len(review["state"]["allocations"]) == 1
    confirm(session, business, fresh)
    assert open_invoice_amount(session, business.tenant.id, credit.id) == 230
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == 150


def test_refund_allocation_failure_rolls_back_document_and_postings(
    session, business, monkeypatch
):
    from reality.services import core

    credit = obligation(session, business)

    def fail(*args, **kwargs):
        raise InvalidOperation("Allocation unavailable")

    monkeypatch.setattr(core, "allocate_settlement", fail)
    with pytest.raises(InvalidOperation, match="Allocation unavailable"):
        core.post_customer_refund(session, business.tenant.id, credit.id, "20")
    session.commit()
    assert session.scalar(select(func.count()).select_from(Document)) == 1
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2


@pytest.mark.parametrize(
    "amount", ["garbage", "Infinity", "-1", "100000000000000", "0.00001"]
)
def test_direct_refund_uses_same_precision_guard(session, business, amount):
    from reality.services.core import post_customer_refund

    credit = obligation(session, business)
    with pytest.raises(InvalidOperation):
        post_customer_refund(session, business.tenant.id, credit.id, amount)
    assert session.scalar(select(func.count()).select_from(Document)) == 1


def test_credit_register_filters_and_totals(session, business):
    from reality.services.core import post_customer_refund
    from reality.services.payment_actions import _customer_credit_items

    credit = obligation(session, business)
    create_document(
        session,
        business.tenant.id,
        "credit_note",
        "UNPOSTED",
        business.customer.id,
        "10",
    )
    post_customer_refund(session, business.tenant.id, credit.id, "20")
    rows = _customer_credit_items(
        session, business.tenant.id, status="outstanding", size=25
    )
    assert len(rows["items"]) == 1
    assert rows["items"][0]["document_id"] == credit.id
    assert Decimal(rows["totals"][0]["open"]) == 280
    assert rows["page"]["size"] == 25
    assert not _customer_credit_items(session, business.tenant.id, query="absent")[
        "items"
    ]
    foreign = create_tenant(session, "Foreign credit register")
    assert not _customer_credit_items(session, foreign.id)["items"]


def test_actual_refund_document_tampering_is_unresolved(session, business):
    credit = obligation(session, business)
    proposal = prepare(session, business, credit)
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    document = session.get(Document, detail["payment_document_id"])
    document.gross_amount = Decimal(1)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_refund_and_credit_reversal_unresolved_overlap_both_directions(
    session, business
):
    credit = obligation(session, business)
    refund = prepare(session, business, credit)
    control = json.loads(refund.input)["_delivery_review"]["state"]["control"]
    reversal_args = {
        "posting_group_id": control["posting_group_id"],
        "reason": "Incorrect credit",
    }
    reversal = prepare_delivery_action(
        session,
        business.tenant.id,
        "ledger_reverse",
        reversal_args,
        request_id="reversal",
    )
    refund.status = "executing"
    session.commit()
    with pytest.raises(InvalidOperation, match="unresolved"):
        confirm(session, business, reversal)
    refund.status = "proposed"
    reversal.status = "executing"
    session.commit()
    with pytest.raises(InvalidOperation, match="unresolved"):
        prepare(session, business, credit, request="blocked-by-reversal")


def test_credit_cannot_be_netted_again_after_refund_consumes_capacity(
    session, business
):
    from reality.services.core import (
        allocate_credit_note,
        post_customer_refund,
        post_sales_invoice,
    )

    credit = obligation(session, business)
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "NET-AFTER-REFUND",
        business.customer.id,
        "300",
        currency="USD",
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)
    post_customer_refund(session, business.tenant.id, credit.id, "250")
    with pytest.raises(InvalidOperation, match="exceeds"):
        allocate_credit_note(session, business.tenant.id, credit.id, invoice.id, "100")
    assert open_invoice_amount(session, business.tenant.id, credit.id) == 50


def test_direct_refund_and_netting_serialize_shared_credit_capacity(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, build_engine
    from reality.services.core import (
        allocate_credit_note,
        create_party,
        post_customer_refund,
        post_sales_invoice,
    )

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as connection:
            tenant = create_tenant(connection, "Concurrent refund and netting")
            party = create_party(connection, tenant.id, "Customer", "customer")
            context = SimpleNamespace(tenant=tenant, customer=party)
            credit = obligation(connection, context)
            invoice = create_document(
                connection,
                tenant.id,
                "sales_invoice",
                "NET",
                party.id,
                "300",
                currency="USD",
            )
            post_sales_invoice(connection, tenant.id, invoice.id)
            tenant_id, credit_id, invoice_id = tenant.id, credit.id, invoice.id
        gate = Barrier(2)

        def execute(refund):
            with factory() as connection:
                gate.wait(timeout=10)
                try:
                    if refund:
                        post_customer_refund(connection, tenant_id, credit_id, "200")
                    else:
                        allocate_credit_note(
                            connection, tenant_id, credit_id, invoice_id, "200"
                        )
                    return True
                except InvalidOperation:
                    connection.rollback()
                    return False

        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(execute, [True, False])) == [False, True]
        with factory() as connection:
            assert open_invoice_amount(connection, tenant_id, credit_id) == 100
            assert (
                connection.scalar(
                    select(func.count()).select_from(SettlementAllocation)
                )
                == 1
            )
    finally:
        engine.dispose()


def test_refund_receipt_links_are_inspectable_and_tenant_scoped(session, business):
    from reality.web.api import get_inspector

    credit = obligation(session, business)
    proposal = prepare(session, business, credit)
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    for link in detail["links"]:
        result = get_inspector(link["kind"], link["id"], business.tenant.id, session)
        assert result["id"] == link["id"]
    foreign = create_tenant(session, "Foreign refund inspector")
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        get_inspector("document", detail["payment_document_id"], foreign.id, session)
    assert error.value.status_code == 404


def test_credit_register_paging_sorting_and_reversed_exclusion(session, business):
    from reality.services.payment_actions import _customer_credit_items

    first = obligation(session, business)
    second = create_document(
        session,
        business.tenant.id,
        "credit_note",
        "AAA",
        business.customer.id,
        "50",
        currency="EUR",
    )
    entries = post_sales_credit_note(session, business.tenant.id, second.id)
    page = _customer_credit_items(
        session, business.tenant.id, size=1, page=2, sort="number"
    )
    assert page["items"][0]["document_id"] == first.id
    assert page["page"]["pages"] == 2
    assert {row["currency"] for row in page["totals"]} == {"EUR", "USD"}
    reverse_ledger_posting_group(
        session, business.tenant.id, entries[0].posting_group_id, reason="Wrong credit"
    )
    assert (
        len(
            _customer_credit_items(session, business.tenant.id, status="outstanding")[
                "items"
            ]
        )
        == 1
    )
    rows = _customer_credit_items(session, business.tenant.id)
    reversed_row = next(row for row in rows["items"] if row["document_id"] == second.id)
    assert reversed_row["status"] == "reversed"
    assert Decimal(reversed_row["open"]) == 0
