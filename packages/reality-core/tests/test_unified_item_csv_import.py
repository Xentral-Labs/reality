"""Reviewed item CSV preserves bytes and proves atomic, repeatable business effects."""

import io
import json

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import BusinessEvent, Item, SourceRecord
from reality.services import core
from reality.services.artifacts import stage_artifact
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)
from reality.services.item_imports import preview_item_import, stage_item_csv
from reality.tools.application import (
    approve_and_execute_proposal,
    confirm_tool,
    propose_tool,
)


def fixture_file(
    session,
    business,
    tmp_path,
    monkeypatch,
    content=b"sku,name,unit\nCSV-A,First,pcs\nCSV-B,Second,box\n",
):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    staged = stage_item_csv(session, business.tenant.id, content, "items.csv")
    return {
        "artifact_id": staged["id"],
        "source_system": "catalog_upload",
        "mapping": {"sku": "sku", "name": "name", "unit": "unit"},
        "default_unit": "pcs",
    }


def prepare(session, business, config, request="csv-129"):
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "item_create",
        {"import_file": config},
        request_id=request,
    )


def confirm(session, business, proposal):
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )


def items(session, business):
    return session.scalar(
        select(func.count())
        .select_from(Item)
        .where(Item.tenant_id == business.tenant.id)
    )


def test_preview_is_inert_confirm_is_traceable_and_replay_safe(
    session, business, tmp_path, monkeypatch
):
    config = fixture_file(session, business, tmp_path, monkeypatch)
    before = items(session, business)
    preview = preview_item_import(session, business.tenant.id, config)
    assert len(preview["rows"]) == 2
    proposal = prepare(session, business, config)
    assert items(session, business) == before
    with pytest.raises(core.InvalidOperation):
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    saved = confirm(session, business, proposal)
    receipt = json.loads(saved.output)
    assert len(receipt["item_ids"]) == 2
    assert items(session, business) == before + 2
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    source = record_by_id(session, SourceRecord, receipt["source_record_id"])
    assert source.source_artifact_id == config["artifact_id"]
    assert all(
        record_by_id(session, Item, item_id).source_record_id == source.id
        for item_id in receipt["item_ids"]
    )
    assert json.loads(confirm(session, business, proposal).output) == receipt
    assert prepare(session, business, config).id == proposal.id
    assert items(session, business) == before + 2
    with pytest.raises(core.InvalidOperation, match="exists"):
        prepare(session, business, config, "other-request")
    proposal.status = "executing"
    proposal.output = "{}"
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "recorded_unsettled"
    )
    assert (
        reconcile_delivery(session, business.tenant.id, proposal.id)["verification"]
        == "verified"
    )
    assert items(session, business) == before + 2


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"sku,name\nA,\n",
        b"sku,name\nA,One\nA,Two\n",
        b"sku,sku\nA,B\n",
        b"sku,name\nA,One,Extra\n",
        b"sku,name\nA,\xff\n",
        b"sku,name\n" + b"A,One\n" * 501,
    ],
)
def test_invalid_file_never_creates_items(
    session, business, tmp_path, monkeypatch, content
):
    before = items(session, business)
    with pytest.raises(core.InvalidOperation):
        config = fixture_file(session, business, tmp_path, monkeypatch, content)
        config["mapping"].pop("unit")
        preview_item_import(session, business.tenant.id, config)
    assert items(session, business) == before


def test_stale_existing_inactive_sku_and_foreign_artifact_are_rejected(
    session, business, tmp_path, monkeypatch
):
    config = fixture_file(session, business, tmp_path, monkeypatch)
    proposal = prepare(session, business, config)
    item = core.create_item(session, business.tenant.id, "CSV-A", "Concurrent item")
    item.is_active = False
    session.commit()
    with pytest.raises(core.InvalidOperation, match="exists"):
        confirm(session, business, proposal)
    assert proposal.status == "proposed"
    other = core.create_tenant(session, "Other company")
    with pytest.raises(core.NotFound):
        preview_item_import(session, other.id, config)


def test_mid_batch_failure_rolls_back_items_sources_and_events(
    session, business, tmp_path, monkeypatch
):
    from reality.services import item_imports

    config = fixture_file(session, business, tmp_path, monkeypatch)
    proposal = prepare(session, business, config)
    before = items(session, business)
    original = item_imports.create_item
    calls = 0

    def broken(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise core.InvalidOperation("Injected second-row failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(item_imports, "create_item", broken)
    with pytest.raises(core.InvalidOperation):
        confirm(session, business, proposal)
    session.rollback()
    assert items(session, business) == before
    assert not session.scalar(
        select(BusinessEvent.id).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.action_id == proposal.id,
        )
    )


def test_legacy_item_file_atomic_replay_and_retry(
    session, business, tmp_path, monkeypatch
):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    artifact, _ = stage_artifact(
        session,
        business.tenant.id,
        io.BytesIO(b"sku,name\nLEGACY-A,One\nLEGACY-B,Two\n"),
        filename="legacy.csv",
        content_type="text/csv",
    )
    proposal = propose_tool(
        session,
        business.tenant.id,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "legacy",
            "source_type": "item",
            "expected_target": "item",
        },
    )
    job = json.loads(confirm_tool(session, business.tenant.id, proposal.id).output)[
        "import_job_id"
    ]
    first = core.process_import_job(session, business.tenant.id, job)
    second = core.process_import_job(session, business.tenant.id, job)
    assert set(first["created_ids"]) == set(second["created_ids"])
    assert len(first["created_ids"]) == 2
    assert core.retry_import_job(session, business.tenant.id, job).status == "completed"
    artifact, _ = stage_artifact(
        session,
        business.tenant.id,
        io.BytesIO(b"sku,name\nBAD-A,One\nBAD-B,\n"),
        filename="bad.csv",
        content_type="text/csv",
    )
    proposal = propose_tool(
        session,
        business.tenant.id,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "legacy",
            "source_type": "item",
            "expected_target": "item",
        },
    )
    job = json.loads(confirm_tool(session, business.tenant.id, proposal.id).output)[
        "import_job_id"
    ]
    before = items(session, business)
    with pytest.raises(core.InvalidOperation):
        core.process_import_job(session, business.tenant.id, job)
    assert items(session, business) == before
    assert core.retry_import_job(session, business.tenant.id, job).status == "pending"


def test_csv_http_stage_review_confirm_and_original(
    session, business, tmp_path, monkeypatch
):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            content = b"number;title\nHTTP-A;Article A\nHTTP-B;Article B\n"
            staged = client.post(
                f"{base}/item-imports/artifacts?filename=articles.csv",
                content=content,
                headers={"Content-Type": "text/csv"},
            )
            assert staged.status_code == 201, staged.text
            config = {
                "artifact_id": staged.json()["id"],
                "source_system": "test_import",
                "mapping": {"sku": "number", "name": "title"},
                "default_unit": "pcs",
            }
            response = client.post(
                f"{base}/item-imports/prepare",
                json={"request_id": "http-csv", "config": config},
            )
            assert response.status_code == 200, response.text
            proposal = response.json()
            assert proposal["review"]["state"]["creation"]["rows"][0]["unit"] == "pcs"
            response = client.post(
                f"{base}/change-proposals/{proposal['id']}/approve",
                json={"confirmed": True, "review_token": proposal["review"]["token"]},
            )
            assert response.status_code == 200, response.text
            detail = client.get(f"{base}/delivery-actions/{proposal['id']}").json()
            assert detail["verification"] == "verified"
            download = client.get(
                f"{base}/item-imports/artifacts/{config['artifact_id']}/download"
            )
            assert download.status_code == 200
            assert download.content == content
            assert "attachment" in download.headers["content-disposition"]
            other = core.create_tenant(session, "Foreign CSV company")
            assert (
                client.get(
                    f"/api/tenants/{other.id}/item-imports/artifacts/{config['artifact_id']}/download"
                ).status_code
                == 404
            )
    finally:
        app.dependency_overrides.clear()


def test_mapping_change_and_changed_original_require_fresh_review(
    session, business, tmp_path, monkeypatch
):
    from reality.services.artifacts import artifact_path, get_artifact

    config = fixture_file(session, business, tmp_path, monkeypatch)
    proposal = prepare(session, business, config)
    with pytest.raises(core.InvalidOperation, match="identity"):
        prepare(session, business, {**config, "default_unit": "box"})
    path = artifact_path(
        get_artifact(session, business.tenant.id, config["artifact_id"])
    )
    path.write_bytes(b"sku,name\nCHANGED,Changed\n")
    with pytest.raises(core.InvalidOperation, match="hash"):
        confirm(session, business, proposal)
    assert items(session, business) == 1


def test_same_file_deduplicates_and_valid_utf8_defaults_are_explicit(
    session, business, tmp_path, monkeypatch
):
    content = "\ufeffnumber;title;unused\r\nCSV-X;Änderung;=2+2\r\n".encode()
    config = fixture_file(session, business, tmp_path, monkeypatch, content)
    same = stage_item_csv(session, business.tenant.id, content, "again.csv")
    assert same["id"] == config["artifact_id"]
    config["mapping"] = {"sku": "number", "name": "title"}
    preview = preview_item_import(session, business.tenant.id, config)
    assert preview["rows"] == [{"sku": "CSV-X", "name": "Änderung", "unit": "pcs"}]
    assert preview["default_unit"] == "pcs"
    with pytest.raises(core.InvalidOperation, match="2 MiB"):
        stage_item_csv(
            session, business.tenant.id, b"x" * (2 * 1024 * 1024 + 1), "huge.csv"
        )


def test_concurrent_imports_revalidate_skus(postgres_database, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, build_engine

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as connection:
            business = SimpleNamespace(
                tenant=core.create_tenant(connection, "Concurrent CSV")
            )
            config = fixture_file(connection, business, tmp_path, monkeypatch)
            first = prepare(connection, business, config, "first")
            second = prepare(connection, business, config, "second")
            claims = [
                (p.id, json.loads(p.input)["_delivery_review"]["token"])
                for p in (first, second)
            ]
        gate = Barrier(2)

        def execute(claim):
            with factory() as connection:
                gate.wait(timeout=10)
                try:
                    approve_and_execute_proposal(
                        connection,
                        business.tenant.id,
                        claim[0],
                        review_token=claim[1],
                        confirmed=True,
                    )
                    return True
                except core.InvalidOperation:
                    return False

        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(execute, claims)) == [False, True]
        with factory() as connection:
            assert items(connection, business) == 2
    finally:
        engine.dispose()


def test_direct_creation_keeps_tenant_lock_through_item_insert(
    postgres_database, tmp_path, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from types import SimpleNamespace

    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, build_engine

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as connection:
            business = SimpleNamespace(
                tenant=core.create_tenant(connection, "Direct CSV race")
            )
            config = fixture_file(connection, business, tmp_path, monkeypatch)
            proposal = prepare(connection, business, config)
            identity, token = (
                proposal.id,
                json.loads(proposal.input)["_delivery_review"]["token"],
            )
        entered, release, confirming = Event(), Event(), Event()
        original = core.create_master_source_record

        def hold_source(*args, **kwargs):
            value = original(*args, **kwargs)
            entered.set()
            assert release.wait(timeout=10)
            return value

        monkeypatch.setattr(core, "create_master_source_record", hold_source)

        def direct():
            with factory() as connection:
                core.create_item(connection, business.tenant.id, "CSV-A", "Direct item")

        def imported():
            with factory() as connection:
                confirming.set()
                try:
                    approve_and_execute_proposal(
                        connection,
                        business.tenant.id,
                        identity,
                        review_token=token,
                        confirmed=True,
                    )
                    return True
                except core.InvalidOperation:
                    return False

        with ThreadPoolExecutor(max_workers=2) as workers:
            direct_work = workers.submit(direct)
            assert entered.wait(timeout=10)
            import_work = workers.submit(imported)
            assert confirming.wait(timeout=10)
            release.set()
            direct_work.result(timeout=10)
            assert import_work.result(timeout=10) is False
        with factory() as connection:
            assert items(connection, business) == 1
    finally:
        engine.dispose()
