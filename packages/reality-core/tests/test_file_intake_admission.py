"""Spec 358: validate the entire raw input before deterministic review packages."""

import pytest

from reality.domain.intake import PACKAGE_BYTES, canonical_json
from reality.services.core import InvalidOperation
from reality.services.file_intake import package_item_csv


def test_large_file_is_partitioned_before_legacy_limit():
    content = (
        "sku,name\n"
        + "".join(f"SKU-{index},Article {index}\n" for index in range(5000))
    ).encode()
    packages = package_item_csv(content, {"sku": "sku", "name": "name"})
    assert len(packages) == 10
    assert sum(len(package.rows) for package in packages) == 5000
    assert all(
        len(package.rows) <= 500 and package.byte_size <= PACKAGE_BYTES
        for package in packages
    )
    assert package_item_csv(content, {"sku": "sku", "name": "name"}) == packages


def test_full_file_validation_covers_package_boundaries():
    rows = "".join(f"SKU-{index},Article\n" for index in range(501))
    with pytest.raises(InvalidOperation, match="duplicate"):
        package_item_csv(
            ("sku,name\n" + rows + "SKU-0,Duplicate\n").encode(),
            {"sku": "sku", "name": "name"},
        )


def test_utf8_bytes_and_multiline_values_define_package_limits():
    value = "ä" * 18000 + "\ncontinued"
    content = (
        "sku,name\n" + "".join(f'SKU-{index},"{value}"\n' for index in range(250))
    ).encode()
    packages = package_item_csv(content, {"sku": "sku", "name": "name"})
    assert len(packages) > 1
    assert sum(len(package.rows) for package in packages) == 250
    assert packages[0].rows[0]["name"] == value
    assert all(
        package.byte_size == len(canonical_json(list(package.rows)).encode())
        for package in packages
    )


def test_oversized_indivisible_row_refuses_before_any_package():
    content = ("sku,name\nSKU," + "x" * PACKAGE_BYTES + "\n").encode()
    with pytest.raises(InvalidOperation, match="coherent"):
        package_item_csv(content, {"sku": "sku", "name": "name"})


def test_structural_failure_in_late_row_refuses_whole_file():
    content = (
        "sku,name\n"
        + "".join(f"SKU-{index},Article\n" for index in range(501))
        + "bad,too,many\n"
    ).encode()
    with pytest.raises(InvalidOperation):
        package_item_csv(content, {"sku": "sku", "name": "name"})


def test_original_artifact_precedes_master_approval(
    session, business, tmp_path, monkeypatch
):
    import json

    from sqlalchemy import func, select

    from reality.db.core import Item, SourceRecord
    from reality.services import reviewed_item_imports as item_imports
    from reality.services.artifacts import get_artifact, materialize_artifact

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "raw"))
    raw = b'sku,name,unmapped\nFILE-A,"First\nsecond",Original note\nFILE-B,Another,Keep this too\n'
    before = session.scalar(select(func.count()).select_from(Item))
    staged = item_imports.stage_reviewed_item_csv(
        session, business.tenant.id, raw, "original.csv"
    )
    source = session.get(SourceRecord, (business.tenant.id, staged["source_record_id"]))
    artifact = get_artifact(session, business.tenant.id, source.source_artifact_id)
    with materialize_artifact(artifact) as path:
        assert path.read_bytes() == raw
    assert "rows" not in json.loads(source.payload)
    prepared = item_imports.prepare_reviewed_item_file(
        session,
        business.tenant.id,
        source.id,
        {"sku": "sku", "name": "name"},
        request_id="file",
    )
    assert prepared["original_rows"] == 2
    assert prepared["excluded_rows"] == []
    assert len(prepared["entries"]) == 1
    assert session.scalar(select(func.count()).select_from(Item)) == before


def test_master_package_refuses_current_conflict_atomically(
    session, business, tmp_path, monkeypatch, scheduled_owner
):
    from sqlalchemy import select

    from reality.db.core import ChangeProposal, Item
    from reality.services import core
    from reality.services import reviewed_item_imports as item_imports
    from reality.services.intake import apply_prepared_intake
    from reality.services.memberships import Principal

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "raw"))
    staged = item_imports.stage_reviewed_item_csv(
        session,
        business.tenant.id,
        b"sku,name\nFILE-A,First\nFILE-B,Second\n",
        "items.csv",
    )
    prepared = item_imports.prepare_reviewed_item_file(
        session,
        business.tenant.id,
        staged["source_record_id"],
        {"sku": "sku", "name": "name"},
        request_id="conflict",
    )
    child = prepared["entries"][0]
    core.create_item(
        session, business.tenant.id, "FILE-B", "Concurrent existing", "pcs"
    )
    with pytest.raises(core.InvalidOperation):
        apply_prepared_intake(
            session,
            business.tenant.id,
            child["proposal_id"],
            child["digest"],
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(Item).where(Item.sku == "FILE-A")) is None
    proposal = session.get(ChangeProposal, (business.tenant.id, child["proposal_id"]))
    assert proposal.status == "proposed"


def test_master_package_receipt_replays_without_reading_file(
    session, business, tmp_path, monkeypatch, scheduled_owner
):
    import json

    from sqlalchemy import select

    from reality.db.core import Item
    from reality.services import reviewed_item_imports as item_imports
    from reality.services.intake import apply_prepared_intake
    from reality.services.memberships import Principal

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "raw"))
    staged = item_imports.stage_reviewed_item_csv(
        session,
        business.tenant.id,
        b"sku,name\nFILE-A,First\nFILE-B,Second\n",
        "items.csv",
    )
    prepared = item_imports.prepare_reviewed_item_file(
        session,
        business.tenant.id,
        staged["source_record_id"],
        {"sku": "sku", "name": "name"},
        request_id="replay",
    )
    child = prepared["entries"][0]
    accepted = apply_prepared_intake(
        session,
        business.tenant.id,
        child["proposal_id"],
        child["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    receipt = json.loads(accepted.output)
    assert len([row for row in receipt["records"] if row["type"] == "item"]) == 2
    monkeypatch.setattr(
        item_imports,
        "materialize_artifact",
        lambda *args: (_ for _ in ()).throw(
            AssertionError("Approval/replay must use retained meaning")
        ),
    )
    replay = apply_prepared_intake(
        session,
        business.tenant.id,
        child["proposal_id"],
        child["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    assert json.loads(replay.output) == receipt
    items = list(session.scalars(select(Item).where(Item.sku.like("FILE-%"))))
    assert len(items) == 2
    assert all(row.source_record_id == receipt["source_record_id"] for row in items)


def test_reviewed_master_defaults_cannot_be_changed_by_a_callback(
    session, business, tmp_path, monkeypatch, scheduled_owner
):
    from reality.services import core
    from reality.services import reviewed_item_imports as item_imports
    from reality.services.intake import apply_prepared_intake
    from reality.services.memberships import Principal

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "raw"))
    staged = item_imports.stage_reviewed_item_csv(
        session, business.tenant.id, b"sku,name\nFILE-A,First\n", "items.csv"
    )
    prepared = item_imports.prepare_reviewed_item_file(
        session,
        business.tenant.id,
        staged["source_record_id"],
        {"sku": "sku", "name": "name"},
        request_id="defaults",
    )
    actual = core.create_item

    def change_unoffered_default(*args, **kwargs):
        return actual(*args, **{**kwargs, "item_type": "service"})

    monkeypatch.setattr(core, "create_item", change_unoffered_default)
    child = prepared["entries"][0]
    with pytest.raises(core.InvalidOperation):
        apply_prepared_intake(
            session,
            business.tenant.id,
            child["proposal_id"],
            child["digest"],
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )


def test_exclusions_are_retained_in_exact_file_review(
    session, business, tmp_path, monkeypatch
):
    from reality.services import intake_batches
    from reality.services import reviewed_item_imports as item_imports

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "raw"))
    staged = item_imports.stage_reviewed_item_csv(
        session,
        business.tenant.id,
        b"sku,name\nFILE-A,First\nFILE-B,\nFILE-C,Third\n",
        "issues.csv",
    )
    prepared = item_imports.prepare_reviewed_item_file(
        session,
        business.tenant.id,
        staged["source_record_id"],
        {"sku": "sku", "name": "name"},
        request_id="exclusions",
    )
    review = intake_batches.review_batch(
        session, business.tenant.id, prepared["batch_id"]
    )
    assert review["file_selection"]["original_rows"] == 3
    assert review["file_selection"]["excluded_rows"] == [
        {"row": 3, "reason_code": "item_import_row_field_invalid", "field": "name"}
    ]


def test_5000_items_are_ten_reviewed_atomic_packages(
    session, business, tmp_path, monkeypatch, scheduled_owner
):
    from sqlalchemy import func, select

    from reality.db.core import Item
    from reality.services import intake_batches, scheduled_jobs
    from reality.services import reviewed_item_imports as item_imports
    from reality.services.memberships import Principal

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "raw"))
    raw = (
        "sku,name\n"
        + "".join(f"FILE-{number},Article {number}\n" for number in range(5000))
    ).encode()
    before = session.scalar(select(func.count()).select_from(Item))
    staged = item_imports.stage_reviewed_item_csv(
        session, business.tenant.id, raw, "5000.csv"
    )
    prepared = item_imports.prepare_reviewed_item_file(
        session,
        business.tenant.id,
        staged["source_record_id"],
        {"sku": "sku", "name": "name"},
        request_id="five-thousand",
    )
    assert prepared["original_rows"] == 5000
    assert len(prepared["entries"]) == 10
    assert session.scalar(select(func.count()).select_from(Item)) == before
    intake_batches.approve_batch(
        session,
        business.tenant.id,
        prepared["batch_id"],
        prepared["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    claim = scheduled_jobs.claim_next(session, business.tenant.id)
    session.commit()
    assert (
        scheduled_jobs.execute_claim(
            session, business.tenant.id, claim.id, claim.claim_token
        )
        == "succeeded"
    )
    session.commit()
    assert session.scalar(select(func.count()).select_from(Item)) == before + 5000
    page = intake_batches.batch_status(
        session, business.tenant.id, prepared["batch_id"]
    )
    assert page["status"] == "executed"
    assert len(page["results"]) == 10
    assert sum(len(row["receipt"]["records"]) for row in page["results"]) == 5000
    assert all(row["disposition"] == "applied" for row in page["results"])
    replay = item_imports.prepare_reviewed_item_file(
        session,
        business.tenant.id,
        staged["source_record_id"],
        {"sku": "sku", "name": "name"},
        request_id="five-thousand",
    )
    assert replay == prepared


def test_http_file_review_queues_without_accepting_and_status_read_is_inert(
    session, business, tmp_path, monkeypatch, scheduled_owner
):
    from fastapi.testclient import TestClient
    from sqlalchemy import func, select

    from reality.db.core import Item
    from reality.services.memberships import Principal
    from reality.web.api import database_session
    from reality.web.app import app

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("REALITY_AUTH_MODE", "disabled")
    app.dependency_overrides[database_session] = lambda: session
    monkeypatch.setattr(
        "reality.web.api.optional_request_principal",
        lambda request: Principal(scheduled_owner.id),
    )
    before = session.scalar(select(func.count()).select_from(Item))
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            staged = client.post(
                f"{base}/item-imports/artifacts?filename=review.csv",
                content=b"sku,name\nHTTP-A,First\n",
                headers={"Content-Type": "text/csv"},
            )
            assert staged.status_code == 201
            prepared = client.post(
                f"{base}/item-imports/reviewed/prepare",
                json={
                    "request_id": "http-review",
                    "config": {
                        "artifact_id": staged.json()["id"],
                        "source_system": "catalog_import",
                        "mapping": {"sku": "sku", "name": "name"},
                        "default_unit": "pcs",
                    },
                },
            )
            assert prepared.status_code == 200, prepared.text
            batch = prepared.json()
            assert batch["review"]["state"]["creation"]["original_rows"] == 1
            assert session.scalar(select(func.count()).select_from(Item)) == before
            approved = client.post(
                f"{base}/change-proposals/{batch['id']}/approve",
                json={"confirmed": True, "review_token": batch["review"]["token"]},
            )
            assert approved.status_code == 200, approved.text
            for _ in range(2):
                read = client.get(f"{base}/item-imports/reviewed/{batch['id']}")
                assert read.status_code == 200
                assert read.json()["status"] == "executing"
                assert read.json()["verification"] == "queued"
            assert session.scalar(select(func.count()).select_from(Item)) == before
    finally:
        app.dependency_overrides.clear()


def test_foreign_company_cannot_prepare_or_read_item_file(
    session, business, tmp_path, monkeypatch
):
    from reality.db.core import ImportJob, SourceRecord
    from reality.services import core
    from reality.services import reviewed_item_imports as item_imports

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "raw"))
    staged = item_imports.stage_reviewed_item_csv(
        session, business.tenant.id, b"sku,name\nBOUNDARY-A,First\n", "items.csv"
    )
    prepared = item_imports.prepare_reviewed_item_file(
        session,
        business.tenant.id,
        staged["source_record_id"],
        {"sku": "sku", "name": "name"},
        request_id="boundary",
    )
    foreign = core.create_tenant(session, "Foreign file review")
    source = session.get(SourceRecord, (business.tenant.id, staged["source_record_id"]))
    job = session.get(ImportJob, (business.tenant.id, staged["job_id"]))
    for operation in (
        lambda: item_imports.stage_reviewed_item_csv(
            session, "missing-company", b"sku,name\nA,First\n", "items.csv"
        ),
        lambda: item_imports.capture_reviewed_item_artifact(
            session, foreign.id, staged["artifact_id"], "catalog_upload"
        ),
        lambda: item_imports.prepare_reviewed_item_file(
            session,
            foreign.id,
            source.id,
            {"sku": "sku", "name": "name"},
            request_id="foreign",
        ),
        lambda: item_imports.prepare_reviewed_item_import(
            session,
            foreign.id,
            {
                "artifact_id": staged["artifact_id"],
                "source_system": "catalog_upload",
                "mapping": {"sku": "sku", "name": "name"},
            },
            request_id="foreign",
        ),
        lambda: item_imports.prepare_item_package(session, foreign.id, source, job),
        lambda: item_imports.reviewed_item_file_detail(
            session, foreign.id, prepared["batch_id"]
        ),
    ):
        with pytest.raises(core.NotFound):
            operation()
