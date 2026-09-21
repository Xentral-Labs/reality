import io
import json
from pathlib import Path

from conftest import record_by_id

from reality.db.core import SourceArtifact, SourceRecord
from reality.services.artifacts import (
    artifact_path,
    materialize_artifact,
    stage_artifact,
)
from reality.services.core import (
    business_events,
    enqueue_source,
    process_import_job,
    retry_import_job,
)
from reality.tools.application import confirm_tool, propose_tool


class FakeS3:
    def __init__(self):
        self.objects: dict[tuple[str, str], bytes] = {}

    def upload_file(self, filename, bucket, key, ExtraArgs=None):
        self.objects[(bucket, key)] = Path(filename).read_bytes()

    def download_file(self, bucket, key, filename):
        Path(filename).write_bytes(self.objects[(bucket, key)])


def test_unknown_source_is_stored_idempotently_as_unmapped(session, business):
    payload = {"anything": {"is": "preserved"}, "amount": "12.30"}
    source, job = enqueue_source(
        session,
        business.tenant.id,
        "custom-crm",
        "mystery_object",
        "EXT-42",
        payload,
    )
    repeated_source, repeated_job = enqueue_source(
        session,
        business.tenant.id,
        "custom-crm",
        "mystery_object",
        "EXT-42",
        payload,
    )

    assert json.loads(source.payload) == payload
    assert job.status == "unmapped"
    assert repeated_source.id == source.id
    assert repeated_job.id == job.id
    assert process_import_job(session, business.tenant.id, job.id) is None
    assert retry_import_job(session, business.tenant.id, job.id).status == "unmapped"
    event_types = [
        event.event_type for event in business_events(session, business.tenant.id)
    ]
    assert event_types.count("source_record.received") == 1
    assert event_types.count("source_record.unmapped") == 1


def test_generic_source_versions_changed_payload(session, business):
    first, _ = enqueue_source(
        session, business.tenant.id, "pim", "product", "P-1", {"name": "Old"}
    )
    second, _ = enqueue_source(
        session, business.tenant.id, "pim", "product", "P-1", {"name": "New"}
    )
    assert second.version == 2
    assert second.supersedes_source_record_id == first.id


def test_large_artifact_is_streamed_then_attached_by_confirmed_tool(
    session, business, tmp_path, monkeypatch
):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    content = b"sku,quantity\nBIKE-LIGHT,20\n" * 100_000
    artifact, sample = stage_artifact(
        session,
        business.tenant.id,
        io.BytesIO(content),
        filename="stock.csv",
        content_type="text/csv",
    )
    assert sample.startswith(b"sku,quantity")
    assert artifact.byte_size == len(content)
    assert artifact_path(artifact).read_bytes() == content

    proposal = propose_tool(
        session,
        business.tenant.id,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "warehouse_export",
            "source_type": "inventory_snapshot",
            "expected_target": "inventory_snapshot",
        },
        actor_type="human",
    )
    executed = confirm_tool(session, business.tenant.id, proposal.id)
    output = json.loads(executed.output)
    source = record_by_id(session, SourceRecord, output["source_record_id"])
    session.refresh(artifact)

    assert source.source_artifact_id == artifact.id
    assert json.loads(source.payload)["artifact"]["sha256"] == artifact.sha256
    assert output["import_status"] == "pending"
    assert artifact.status == "attached"


def test_artifact_content_is_deduplicated_per_tenant(
    session, business, tmp_path, monkeypatch
):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    first, _ = stage_artifact(
        session,
        business.tenant.id,
        io.BytesIO(b"same"),
        filename="a.txt",
        content_type="text/plain",
    )
    second, _ = stage_artifact(
        session,
        business.tenant.id,
        io.BytesIO(b"same"),
        filename="b.txt",
        content_type="text/plain",
    )
    assert second.id == first.id
    assert session.query(SourceArtifact).count() == 1


def test_s3_artifact_adapter_streams_and_materializes(
    session, business, tmp_path, monkeypatch
):
    from reality.services import artifacts

    fake = FakeS3()
    monkeypatch.setenv("REALITY_ARTIFACT_STORAGE", "s3")
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "staging"))
    monkeypatch.setenv("REALITY_S3_BUCKET", "reality-artifacts")
    monkeypatch.setattr(artifacts, "_s3_client", lambda: fake)
    content = b"immutable source evidence"

    artifact, _ = stage_artifact(
        session,
        business.tenant.id,
        io.BytesIO(content),
        filename="evidence.txt",
        content_type="text/plain",
    )

    assert fake.objects[("reality-artifacts", artifact.storage_key)] == content
    with materialize_artifact(artifact) as local_path:
        assert local_path.read_bytes() == content


def test_artifact_upload_uses_file_profile_not_object_interpreter(
    session, business, tmp_path, monkeypatch
):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    artifact, _ = stage_artifact(
        session,
        business.tenant.id,
        io.BytesIO(b'{"id": 42, "line_items": []}'),
        filename="order.json",
        content_type="application/json",
    )
    proposal = propose_tool(
        session,
        business.tenant.id,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "shopify",
            "source_type": "order",
            "expected_target": "sales_order",
        },
    )
    executed = confirm_tool(session, business.tenant.id, proposal.id)
    assert json.loads(executed.output)["import_status"] == "pending"


def test_item_csv_file_is_explicitly_mapped_by_worker(
    session, business, tmp_path, monkeypatch
):
    from reality.db.core import Item

    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    artifact, _ = stage_artifact(
        session,
        business.tenant.id,
        io.BytesIO(
            b"sku,name,unit,item_type,tracking_type\nBELL,Bike Bell,pcs,stocked,none\n"
        ),
        filename="items.csv",
        content_type="text/csv",
    )
    proposal = propose_tool(
        session,
        business.tenant.id,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "pim",
            "source_type": "item",
            "expected_target": "item",
        },
    )
    executed = confirm_tool(session, business.tenant.id, proposal.id)
    output = json.loads(executed.output)
    result = process_import_job(session, business.tenant.id, output["import_job_id"])
    imported = (
        session.query(Item).filter_by(tenant_id=business.tenant.id, sku="BELL").one()
    )

    assert result["rows"] == 1
    assert imported.name == "Bike Bell"
    assert imported.source_record_id == output["source_record_id"]
