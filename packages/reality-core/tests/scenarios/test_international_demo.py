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
    for model, count in [(Item, 16), (Party, 8), (Location, 2)]:
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
