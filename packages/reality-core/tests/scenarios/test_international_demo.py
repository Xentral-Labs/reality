from conftest import seed_company
from sqlalchemy import func, select

from reality.db.core import Commitment, Item, Location, Party, PlaygroundRun
from reality.services import company_setup


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
    run = session.get(PlaygroundRun, result["run_id"])
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
    manifest = session.get(PlaygroundRun, result["run_id"]).initialization_progress
    for index, stock in enumerate((10, 10, 2, 2, 5, 7, 10, 0, 0, 10), 1):
        assert core.stock_at(
            session,
            tenant,
            manifest["items"][f"P{index:02}"],
            manifest["locations"]["A"],
        ) == Decimal(stock)
        case = manifest["cases"][f"O{index:02}"]
        commitment = session.get(Commitment, case["commitment_id"])
        line = session.get(DocumentLine, commitment.document_line_id)
        document = session.get(Document, line.document_id)
        assert document.id == case["document_id"]
        assert (
            session.get(SourceRecord, document.source_record_id).source_system
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
        session.get(Commitment, manifest["cases"]["O09"]["commitment_id"]).status
        == "fulfilled"
    )
    assert (
        session.get(Commitment, manifest["cases"]["O10"]["commitment_id"]).status
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
    assert len(orders) == 34
    held = Counter(orders.values())
    assert len(held) >= 18, held
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
    for number, buyer in invoices.items():
        assert orders[f"H-{number.removeprefix('INV-')}"] == buyer, number
    credits = _documents(session, tenant, "credit_note")
    assert credits == {"CR-001": invoices["INV-credit-origin"]}


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
