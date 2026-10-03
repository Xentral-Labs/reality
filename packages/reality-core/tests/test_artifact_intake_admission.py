"""Spec 353: existing artifact profiles prepare meaning before accepted effects."""

import io
import json

import pytest
from sqlalchemy import func, select

from reality.db.core import Document, Item, LedgerEntry, Location, Movement, Party
from reality.services import core
from reality.services.artifacts import stage_artifact
from reality.services.intake import apply_prepared_intake, prepare_intake, review_intake
from reality.services.memberships import Principal


def prepare_file(session, business, target, content, tmp_path, monkeypatch):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "raw"))
    artifact, _ = stage_artifact(
        session,
        business.tenant.id,
        io.BytesIO(content),
        filename=f"{target}.csv",
        content_type="text/csv",
    )
    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "file_provider",
        target,
        artifact.id,
        {"artifact_id": artifact.id, "sha256": artifact.sha256},
        source_artifact_id=artifact.id,
        context={"expected_target": target, "column_mapping": {}},
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    return source, proposal


@pytest.mark.parametrize(
    "target,content,model",
    [
        ("item", b"sku,name,item_type\nFILE-SERVICE,Consulting,service\n", Item),
        (
            "party",
            b"name,party_type,accounting_code\nFile Partner,customer,FILE-PTY\n",
            Party,
        ),
        (
            "location",
            b"name,location_type,allows_stock\nFile Room,warehouse,false\n",
            Location,
        ),
    ],
)
def test_master_artifact_prepares_without_accepting(
    session, business, scheduled_owner, tmp_path, monkeypatch, target, content, model
):
    before = session.scalar(select(func.count()).select_from(model))
    source, proposal = prepare_file(
        session, business, target, content, tmp_path, monkeypatch
    )
    assert session.scalar(select(func.count()).select_from(model)) == before
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    result = apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        digest,
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    assert session.scalar(select(func.count()).select_from(model)) == before + 1
    assert json.loads(result.output)["source_record_id"] == source.id


def test_snapshot_waits_for_decision_and_binds_current_stock(
    session, business, scheduled_owner, tmp_path, monkeypatch
):
    content = f"sku,location,quantity\n{business.item.sku},{business.location.name},7\n".encode()
    _, proposal = prepare_file(
        session, business, "inventory_snapshot", content, tmp_path, monkeypatch
    )
    assert session.scalar(select(func.count()).select_from(Movement)) == 0
    review = review_intake(session, business.tenant.id, proposal.id)
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    with pytest.raises(core.InvalidOperation):
        apply_prepared_intake(
            session,
            business.tenant.id,
            proposal.id,
            review["digest"],
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert (
        core.stock_at(
            session, business.tenant.id, business.item.id, business.location.id
        )
        == 1
    )


def test_file_order_keeps_unstated_totals_unknown(
    session, business, scheduled_owner, tmp_path, monkeypatch
):
    content = f"order_id,party_name,location,sku,quantity,unit_price\nFILE-ORDER,{business.customer.name},{business.location.name},{business.item.sku},2,5\n".encode()
    _, proposal = prepare_file(
        session, business, "sales_order", content, tmp_path, monkeypatch
    )
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        digest,
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    order = session.scalar(select(Document).where(Document.type == "sales_order"))
    assert order.gross_amount is None
    line = core.document_detail(session, business.tenant.id, order.id)["lines"][0]
    assert line.gross_amount is None
    assert line.unit_price == core.decimal("5")


def test_bank_artifact_is_non_posting_before_owner_decision(
    session, business, scheduled_owner, tmp_path, monkeypatch
):
    content = f"party_name,amount,currency,payment_number,effective_at\n{business.customer.name},12.30,EUR,BANK-FILE,2026-09-12T10:00:00Z\n".encode()
    _, proposal = prepare_file(
        session, business, "bank_statement", content, tmp_path, monkeypatch
    )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        digest,
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2


def test_large_master_file_retains_exact_batch_without_business_writes(
    session, business, scheduled_owner, tmp_path, monkeypatch
):
    from reality.services.intake_batches import review_batch

    before = session.scalar(select(func.count()).select_from(Location))
    content = (
        "name,location_type,allows_stock\n"
        + "".join(f"File room {index},warehouse,false\n" for index in range(501))
    ).encode()
    source, proposal = prepare_file(
        session, business, "location", content, tmp_path, monkeypatch
    )
    assert proposal.type == "tool:intake_batch_apply"
    review = review_batch(session, business.tenant.id, proposal.id)
    assert review["total"] == 2
    assert session.scalar(select(func.count()).select_from(Location)) == before
    assert (
        prepare_intake(
            session,
            business.tenant.id,
            session.scalar(
                select(core.ImportJob).where(
                    core.ImportJob.source_record_id == source.id
                )
            ).id,
        ).id
        == proposal.id
    )

    from reality.services import intake_batches

    intake_batches.approve_batch(
        session,
        business.tenant.id,
        proposal.id,
        review["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    intake_batches.settle_chunk(
        session,
        business.tenant.id,
        proposal.id,
        continuation_id=json.loads(proposal.output)["continuation_id"],
    )
    assert session.scalar(select(func.count()).select_from(Location)) == before + 501
    root_job = session.scalar(
        select(core.ImportJob).where(core.ImportJob.source_record_id == source.id)
    )
    assert root_job.status == "completed"
    assert root_job.completed_at is not None


def test_file_orders_keep_independent_source_identities(
    session, business, scheduled_owner, tmp_path, monkeypatch
):
    from reality.services.intake_batches import review_batch

    content = (
        "order_id,party_name,location,sku,quantity,unit_price\n"
        + "".join(
            f"ORDER-{index},{business.customer.name},{business.location.name},{business.item.sku},2,5\n"
            for index in range(2)
        )
    ).encode()
    _, proposal = prepare_file(
        session, business, "sales_order", content, tmp_path, monkeypatch
    )
    assert proposal.type == "tool:intake_batch_apply"
    review = review_batch(session, business.tenant.id, proposal.id)
    assert review["total"] == 2
    assert len({row["source_record_id"] for row in review["entries"]}) == 2

    from reality.services import intake_batches

    intake_batches.approve_batch(
        session,
        business.tenant.id,
        proposal.id,
        review["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    intake_batches.settle_chunk(
        session,
        business.tenant.id,
        proposal.id,
        continuation_id=json.loads(proposal.output)["continuation_id"],
    )
    orders = list(
        session.scalars(select(Document).where(Document.type == "sales_order"))
    )
    assert len(orders) == 2
    assert len({order.source_record_id for order in orders}) == 2
    assert all(order.gross_amount is None for order in orders)


@pytest.mark.parametrize("total", ["0", "99.1234"])
def test_file_order_records_received_total_even_when_lines_disagree(
    session, business, scheduled_owner, tmp_path, monkeypatch, total
):
    content = (
        f"order_id,party_name,location,sku,quantity,unit_price,line_amount,order_amount\n"
        f"STATED,{business.customer.name},{business.location.name},{business.item.sku},2,5,7,{total}\n"
    ).encode()
    _, proposal = prepare_file(
        session, business, "sales_order", content, tmp_path, monkeypatch
    )
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        digest,
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    order = session.scalar(select(Document).where(Document.type == "sales_order"))
    assert order.gross_amount == core.decimal(total)
    assert (
        core.document_detail(session, business.tenant.id, order.id)["lines"][
            0
        ].gross_amount
        == 7
    )


def test_external_statement_is_received_evidence_without_book_stock_change(
    session, business, scheduled_owner, tmp_path, monkeypatch
):
    from reality.db.core import ExternalStockStatement

    content = (
        f"sku,location,quantity\n{business.item.sku},{business.location.name},12\n"
    ).encode()
    _, proposal = prepare_file(
        session, business, "external_stock", content, tmp_path, monkeypatch
    )
    assert session.scalar(select(func.count()).select_from(ExternalStockStatement)) == 0
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        digest,
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    assert session.scalar(select(func.count()).select_from(ExternalStockStatement)) == 1
    assert (
        core.stock_at(
            session, business.tenant.id, business.item.id, business.location.id
        )
        == 0
    )
    assert session.scalar(select(func.count()).select_from(Movement)) == 0


def test_cross_package_duplicate_sku_refuses_before_business_acceptance(
    session, business, tmp_path, monkeypatch
):
    before = session.scalar(select(func.count()).select_from(Item))
    content = (
        "sku,name\n"
        + "".join(f"NEW-{n},New item\n" for n in range(500))
        + "NEW-0,Duplicate\n"
    ).encode()
    with pytest.raises(core.InvalidOperation):
        prepare_file(session, business, "item", content, tmp_path, monkeypatch)
    assert session.scalar(select(func.count()).select_from(Item)) == before


def test_changed_location_defaults_inside_writer_refuse_atomically(
    session, business, scheduled_owner, tmp_path, monkeypatch
):
    content = b"name,location_type,allows_stock\nFILE-EXACT,warehouse,false\n"
    _, proposal = prepare_file(
        session, business, "location", content, tmp_path, monkeypatch
    )
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    original = core.create_location

    def changed(*args, **kwargs):
        kwargs["allows_stock"] = True
        return original(*args, **kwargs)

    monkeypatch.setattr(core, "create_location", changed)
    with pytest.raises(core.InvalidOperation):
        apply_prepared_intake(
            session,
            business.tenant.id,
            proposal.id,
            digest,
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(Location).where(Location.name == "FILE-EXACT")) is None


def test_unknown_order_total_renders_unknown_in_register_and_inspector(
    session, business, scheduled_owner, tmp_path, monkeypatch
):
    from reality.web.api import document_inspector, tenant_evidence_documents

    content = (
        f"order_id,party_name,location,sku,quantity,unit_price\n"
        f"UNKNOWN,{business.customer.name},{business.location.name},{business.item.sku},2,5\n"
    ).encode()
    _, proposal = prepare_file(
        session, business, "sales_order", content, tmp_path, monkeypatch
    )
    apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        review_intake(session, business.tenant.id, proposal.id)["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    order = session.scalar(select(Document).where(Document.type == "sales_order"))
    detail = document_inspector(session, business.tenant.id, order.id)
    gross = next(row for row in detail["metrics"] if row["label"] == "Gross amount")
    assert gross["value"] == "—"
    assert gross["display_parts"] == [{"type": "text", "value": "—"}]
    register = tenant_evidence_documents(business.tenant.id, session, page=1, size=50)
    assert register["items"][0]["gross_amount"] is None
