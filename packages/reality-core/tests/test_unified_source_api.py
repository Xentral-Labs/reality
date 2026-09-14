from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.orm import sessionmaker

from reality.db.core import ChangeProposal, Document, ImportJob, SourceRecord
from reality.services.core import (
    create_document,
    create_source_system,
    create_tenant,
    enqueue_source,
    store_source_record,
)
from reality.web.api import database_session
from reality.web.app import app


@contextmanager
def client_for(session):
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_source_metadata_is_paged_scoped_and_never_loads_payloads(session, business):
    tid = business.tenant.id
    system = create_source_system(session, tid, "sample-shop", "Sample shop")
    first, _, _ = store_source_record(
        session, tid, system.code, "order", "EXT-1", {"secret": "old"}
    )
    second, _, _ = store_source_record(
        session, tid, system.code, "order", "EXT-1", {"secret": "new"}
    )
    queued, job = enqueue_source(
        session, tid, "unregistered", "unknown", "EXT-2", {"secret": "job"}
    )
    foreign = create_tenant(session, "Other source company")
    create_source_system(session, foreign.id, system.code, system.name)
    store_source_record(
        session, foreign.id, system.code, "order", "FOREIGN", {"secret": "foreign"}
    )
    models = (SourceRecord, ImportJob, Document, ChangeProposal)

    def counts():
        return [
            session.scalar(
                select(func.count()).select_from(model).where(model.tenant_id == tid)
            )
            for model in models
        ]

    before = counts()
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        with client_for(session) as client:
            base = f"/api/tenants/{tid}/data-sources"
            registry = client.get(base + "/systems?q=Sample&size=1")
            assert registry.status_code == 200
            assert registry.json()["items"][0]["record_count"] == 2
            assert registry.json()["items"][0]["id"] == system.id
            records = client.get(
                base + "/records?source_system=sample-shop&size=1"
            ).json()
            next_page = client.get(
                base + "/records?source_system=sample-shop&size=1&page=2"
            ).json()
            assert records["page"]["total"] == 2
            assert {records["items"][0]["id"], next_page["items"][0]["id"]} == {
                first.id,
                second.id,
            }
            assert records["items"][0]["job_status"] is None
            assert client.get(base + "/records?q=FOREIGN").json()["items"] == []
            queued_read = client.get(
                base + "/records?source_system=unregistered"
            ).json()
            assert queued_read["items"][0]["id"] == queued.id
            assert queued_read["items"][0]["job_status"] == job.status == "unmapped"
            assert "secret" not in str(queued_read)
            assert client.get(base + "/records?size=101").status_code == 422
            assert client.get(base + "/systems?page=0").status_code == 422
            assert (
                client.get(base + "/records?page=999&size=1").json()["page"]["number"]
                == 3
            )
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)
    assert statements
    for column in ("source_record.payload", "import_job.input", "import_job.error"):
        assert not any(column in statement for statement in statements)
    assert before == counts()


def test_evidence_filter_uses_exact_source_version_before_paging(session, business):
    tid = business.tenant.id
    first, _, _ = store_source_record(
        session, tid, "proof", "invoice", "SAME", {"version": 1}
    )
    second, _, _ = store_source_record(
        session, tid, "proof", "invoice", "SAME", {"version": 2}
    )
    documents = [
        create_document(
            session,
            tid,
            "sales_invoice" if i == 0 else "sales_order",
            f"PROOF-{i}",
            business.customer.id,
            "123.45",
            source_record_id=first.id,
        )
        for i in range(2)
    ]
    create_document(
        session,
        tid,
        "sales_invoice",
        "PROOF-NEW",
        business.customer.id,
        "999",
        source_record_id=second.id,
    )
    foreign = create_tenant(session, "Foreign evidence")
    with client_for(session) as client:
        url = (
            f"/api/tenants/{tid}/evidence-documents?source_record_id={first.id}&size=1"
        )
        first_page = client.get(url).json()
        second_page = client.get(url + "&page=2").json()
        assert first_page["page"]["total"] == 2
        assert {first_page["items"][0]["id"], second_page["items"][0]["id"]} == {
            row.id for row in documents
        }
        assert client.get(url + "&source_system=wrong").json()["items"] == []
        assert (
            client.get(
                f"/api/tenants/{foreign.id}/evidence-documents?source_record_id={first.id}"
            ).json()["items"]
            == []
        )
        assert (
            client.get(
                f"/api/tenants/{foreign.id}/inspector/source_record/{first.id}"
            ).status_code
            == 404
        )
