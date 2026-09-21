from conftest import record_by_id, seed_company
from reality.db.core import Commitment, Item, Location, Party, PlaygroundRun
from reality.demo.international import HISTORY
from reality.services import company_setup
from sqlalchemy import func, select


def test_canonical_profile_counts_and_cases(session, scheduled_owner, monkeypatch):
    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "canonical",
        "Harbor Supply",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    assert result["status"] == "initializing", result
    tenant = result["tenant_id"]
    assert seed_company(session, tenant) == "succeeded"
    assert (
        company_setup.read_request(session, scheduled_owner.id, "canonical")["status"]
        == "ready"
    )
    for model, count in [(Item, 16), (Party, 24), (Location, 2)]:
        assert (
            session.scalar(
                select(func.count()).select_from(model).where(model.tenant_id == tenant)
            )
            == count
        )
    run = record_by_id(session, PlaygroundRun, result["run_id"])
    assert set(run.initialization_progress["cases"]) >= {
        f"O{i:02}" for i in range(1, 11)
    }
    assert (
        session.scalar(
            select(func.count())
            .select_from(Commitment)
            .where(Commitment.tenant_id == tenant)
        )
        >= 13
    )


def test_operational_stock_and_source_lineage(session, scheduled_owner, monkeypatch):
    from decimal import Decimal

    from reality.db.core import Document, DocumentLine, Reservation, SourceRecord
    from reality.services import core

    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "operational",
        "Harbor Supply",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    tenant = result["tenant_id"]
    seed_company(session, tenant)
    manifest = record_by_id(
        session, PlaygroundRun, result["run_id"]
    ).initialization_progress
    for index, stock in enumerate((10, 10, 42, 2, 5, 7, 10, 0, 0, 10), 1):
        assert core.stock_at(
            session,
            tenant,
            manifest["items"][f"P{index:02}"],
            manifest["locations"]["A"],
        ) == Decimal(stock)
        case = manifest["cases"][f"O{index:02}"]
        commitment = record_by_id(session, Commitment, case["commitment_id"])
        line = record_by_id(session, DocumentLine, commitment.document_line_id)
        document = record_by_id(session, Document, line.document_id)
        assert document.id == case["document_id"]
        assert (
            record_by_id(session, SourceRecord, document.source_record_id).source_system
            == "demo_profile"
        )
        reserved = session.scalar(
            select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                Reservation.tenant_id == tenant,
                Reservation.commitment_id == commitment.id,
                Reservation.status == "active",
            )
        )
        assert reserved == {1: 5, 4: 2, 5: 5}.get(index, 0)
    assert (
        core.stock_at(
            session, tenant, manifest["items"]["P08"], manifest["locations"]["B"]
        )
        == 8
    )
    assert (
        core.open_quantity(session, tenant, manifest["cases"]["O06"]["commitment_id"])
        == 2
    )
    assert (
        record_by_id(
            session, Commitment, manifest["cases"]["O09"]["commitment_id"]
        ).status
        == "fulfilled"
    )
    assert (
        record_by_id(
            session, Commitment, manifest["cases"]["O10"]["commitment_id"]
        ).status
        == "cancelled"
    )


def _demo_company(session, owner, key: str) -> str:
    tenant = company_setup.create_company(
        session,
        owner.id,
        key,
        "Harbor Supply",
        "sandbox",
        "international_demo",
        confirmed=True,
    )["tenant_id"]
    # The profile is seeded by the worker since feature 199.
    assert seed_company(session, tenant) == "succeeded"
    return tenant


def _documents(session, tenant: str, document_type: str):
    from reality.db.core import Document

    names = {
        party.id: party.name
        for party in session.scalars(select(Party).where(Party.tenant_id == tenant))
    }
    return {
        document.number: names[document.party_id]
        for document in session.scalars(
            select(Document).where(
                Document.tenant_id == tenant, Document.type == document_type
            )
        )
    }


def test_orders_spread_over_the_customer_pool(session, scheduled_owner, monkeypatch):
    """Feature 200: every order states its own buyer, a few regulars order more."""
    from collections import Counter

    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    tenant = _demo_company(session, scheduled_owner, "spread")
    orders = _documents(session, tenant, "sales_order")
    portfolio_orders = {
        number: buyer
        for number, buyer in orders.items()
        if number.startswith("COST-PORTFOLIO-")
    }
    assert len(portfolio_orders) == 5, portfolio_orders
    operational_orders = {
        number: buyer
        for number, buyer in orders.items()
        if number not in portfolio_orders
    }
    assert len(operational_orders) == 23
    held = Counter(operational_orders.values())
    assert len(held) >= 15, held
    assert max(held.values()) <= 5, held
    assert sum(1 for count in held.values() if count > 2) <= 3, held
    suppliers = _documents(session, tenant, "purchase_order")
    assert len(set(suppliers.values())) == 3, suppliers


def test_comparison_windows_and_money_state_one_buyer(
    session, scheduled_owner, monkeypatch
):
    """Feature 200: a family compares one customer; its money follows the order."""
    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    tenant = _demo_company(session, scheduled_owner, "families")
    orders = _documents(session, tenant, "sales_order")
    for family in ("volume", "price", "decline", "outlier", "usd"):
        assert orders[f"H-{family}-prior"] == orders[f"H-{family}-current"], family
    invoices = _documents(session, tenant, "sales_invoice")
    assert invoices
    from reality.db.core import Document, SourceRecord

    authored_invoices = session.execute(
        select(SourceRecord.external_id, Document.party_id).join(
            Document,
            (Document.tenant_id == SourceRecord.tenant_id)
            & (Document.source_record_id == SourceRecord.id),
        ).where(
            Document.tenant_id == tenant,
            Document.type == "sales_invoice",
            SourceRecord.external_id.like("INV-%"),
        )
    ).all()
    assert len(authored_invoices) == len(HISTORY)
    credits = _documents(session, tenant, "credit_note")
    assert credits == {
        "CR-001": orders["H-credit-origin"],
        "COST-LATE-CREDIT": "Northstar Outdoor",
    }


def test_seeded_buyers_are_authored_not_drawn(session, scheduled_owner, monkeypatch):
    """Feature 200: the same profile version seeds the same buyer everywhere."""
    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    first = _documents(
        session, _demo_company(session, scheduled_owner, "a"), "sales_order"
    )
    second = _documents(
        session, _demo_company(session, scheduled_owner, "b"), "sales_order"
    )
    assert first == second


def _open_amounts(session, tenant: str, document_type: str) -> dict:
    """What each settleable document still owes, read the way Finance reads it."""
    from decimal import Decimal

    from reality.db.core import Document
    from reality.services import core

    return {
        document.number: (
            abs(core.open_invoice_amount(session, tenant, document.id)),
            Decimal(document.gross_amount),
        )
        for document in session.scalars(
            select(Document).where(
                Document.tenant_id == tenant, Document.type == document_type
            )
        )
    }


def _states(amounts: dict) -> dict:
    return {
        number: "paid"
        if open_amount == 0
        else "part"
        if open_amount < gross
        else "open"
        for number, (open_amount, gross) in amounts.items()
    }


def test_seeded_invoices_are_settled_in_three_states(
    session, scheduled_owner, monkeypatch
):
    """Feature 204: the company gets paid, so open items mean something."""
    from collections import Counter
    from decimal import Decimal

    from reality.db.core import Document

    tenant = _demo_company(session, scheduled_owner, "settled")
    states = Counter(_states(_open_amounts(session, tenant, "sales_invoice")).values())
    assert states["paid"] >= 7, states
    assert states["part"] >= 2, states
    assert states["open"] >= 9, states
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == tenant, Document.type == "customer_payment")
        )
        == states["paid"] + states["part"]
    )
    receivable = sum(
        open_amount
        for open_amount, _ in _open_amounts(session, tenant, "sales_invoice").values()
    )
    invoiced = sum(
        gross for _, gross in _open_amounts(session, tenant, "sales_invoice").values()
    )
    assert Decimal(0) < receivable < invoiced, (receivable, invoiced)


def test_purchases_cover_the_whole_chain(session, scheduled_owner, monkeypatch):
    """Feature 204: ordered, received, invoiced and paid in every combination."""
    from decimal import Decimal

    from reality.db.core import Commitment, PlaygroundRun
    from reality.services import core

    tenant = _demo_company(session, scheduled_owner, "purchases")
    orders = _documents(session, tenant, "purchase_order")
    assert len(orders) == 6, orders
    assert len(set(orders.values())) == 3, "every supplier takes part"
    payables = _states(_open_amounts(session, tenant, "supplier_invoice"))
    assert payables["COST-PORTFOLIO-SELLING"] == "open", payables
    operational_payables = {
        number: state
        for number, state in payables.items()
        if number != "COST-PORTFOLIO-SELLING"
    }
    assert sorted(operational_payables.values()) == ["open", "open", "paid", "part"], (
        payables
    )
    run = session.scalar(select(PlaygroundRun).where(PlaygroundRun.tenant_id == tenant))
    received = {}
    for key, case in run.initialization_progress["cases"].items():
        if not key.startswith("S"):
            continue
        commitment = record_by_id(session, Commitment, case["commitment_id"])
        received[key] = core.fulfilled_quantity(session, tenant, commitment.id)
    assert received["S01"] == Decimal(2), received
    assert received["S03"] == Decimal(0), received
    assert sum(1 for value in received.values() if value == Decimal(5)) == 4, received


def test_settlement_is_authored_not_drawn(session, scheduled_owner, monkeypatch):
    """Feature 204: the same profile version settles the same way everywhere."""
    first = _demo_company(session, scheduled_owner, "settle-a")
    second = _demo_company(session, scheduled_owner, "settle-b")
    for document_type in ("sales_invoice", "supplier_invoice"):
        assert _states(_open_amounts(session, first, document_type)) == _states(
            _open_amounts(session, second, document_type)
        ), document_type


def test_the_profile_may_settle_but_not_decide(session, scheduled_owner):
    """Feature 204: the seed gained settlement, and nothing beyond it."""
    from reality.services.tenant_policy import _PROFILE_OPERATIONS

    assert {
        "post_customer_payment",
        "record_customer_payment",
        "post_supplier_invoice",
        "post_supplier_payment",
        "record_supplier_payment",
        "allocate_settlement",
    } <= _PROFILE_OPERATIONS
    for denied in (
        "post_customer_refund",
        "allocate_credit_note",
        "archive_tenant",
        "create_change_proposal",
    ):
        assert denied not in _PROFILE_OPERATIONS, denied
