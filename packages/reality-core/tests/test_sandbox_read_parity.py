"""Sandbox business reads preserve ordinary results and isolation (spec 155)."""

import asyncio
import io
from types import SimpleNamespace

import pytest
from sqlalchemy import event

from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_commitment,
    create_tenant,
    record_movement,
    reserve,
)
from reality.services.item_imports import preview_item_import, stage_item_csv
from reality.services.reference_workspace import (
    prepare_reference,
    reference_detail,
    reference_proposal,
    reference_register,
    require_ordinary_workspace,
)
from reality.web.api import get_item_csv_original
from reality.web.source_reads import source_metadata_page
from reality.web.warehouse_reads import warehouse_register


@pytest.fixture
def sandbox_business(session, scheduled_owner, monkeypatch):
    from reality.services.company_setup import create_company
    from reality.services.core import (
        create_item,
        create_location,
        create_party,
        get_tenant,
    )

    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    result = create_company(
        session,
        scheduled_owner.id,
        "reads",
        "Read Sandbox",
        "sandbox",
        "empty",
        confirmed=True,
    )
    tid = result["tenant_id"]
    return SimpleNamespace(
        tenant=get_tenant(session, tid),
        company=create_party(session, tid, "Company", "company"),
        customer=create_party(session, tid, "Customer", "customer"),
        supplier=create_party(session, tid, "Supplier", "supplier"),
        item=create_item(session, tid, "ITEM", "Item"),
        location=create_location(session, tid, "Warehouse"),
    )


@pytest.mark.parametrize("view", ["stock", "reservations", "movements"])
def test_populated_sandbox_warehouse_preserves_values_without_writes(
    session, sandbox_business, view
):
    tid = sandbox_business.tenant.id
    record_movement(
        session,
        tid,
        "receipt",
        sandbox_business.item.id,
        "10",
        to_location_id=sandbox_business.location.id,
    )
    commitment = create_commitment(
        session,
        tid,
        "customer_delivery",
        sandbox_business.company.id,
        sandbox_business.customer.id,
        sandbox_business.item.id,
        sandbox_business.location.id,
        "3",
        None,
    )
    reserve(session, tid, commitment.id)
    before = warehouse_register(
        session, tid, view, size=1, item_id=sandbox_business.item.id
    )
    assert before["items"]

    def no_write(conn, cursor, statement, parameters, context, executemany):
        assert statement.lstrip().split()[0].upper() not in {
            "INSERT",
            "UPDATE",
            "DELETE",
        }

    connection = session.connection()
    event.listen(connection, "before_cursor_execute", no_write)
    try:
        after = warehouse_register(
            session, tid, view, size=1, item_id=sandbox_business.item.id
        )
        assert after.pop("observed_at") >= before.pop("observed_at")
        assert after == before
        if view == "stock":
            from decimal import Decimal

            assert Decimal(after["items"][0]["physical"]) == 10
            assert Decimal(after["items"][0]["reserved"]) == 3
            assert Decimal(after["items"][0]["available"]) == 7
    finally:
        event.remove(connection, "before_cursor_execute", no_write)
    other = create_tenant(session, "Other warehouse")
    with pytest.raises(NotFound):
        warehouse_register(session, other.id, view, item_id=sandbox_business.item.id)
    with pytest.raises(NotFound):
        warehouse_register(session, "missing-tenant", view)


@pytest.mark.parametrize("family", ["customer", "supplier", "item", "location"])
def test_reference_sandbox_lists_and_details_preserve_filters(
    session, sandbox_business, family
):
    tid = sandbox_business.tenant.id
    record = getattr(sandbox_business, family)
    before = reference_register(session, tid, family, query=record.name, size=1)
    detail = reference_detail(session, tid, family, record.id)
    assert reference_register(session, tid, family, query=record.name, size=1) == before
    assert reference_detail(session, tid, family, record.id) == detail
    other = create_tenant(session, "Other references")
    with pytest.raises(NotFound):
        reference_detail(session, other.id, family, record.id)
    with pytest.raises(NotFound):
        reference_register(session, "missing-tenant", family)
    with pytest.raises(InvalidOperation):
        require_ordinary_workspace(session, tid)


def test_sandbox_proposal_inspection_does_not_approve_or_prepare(
    session, sandbox_business
):
    tid = sandbox_business.tenant.id
    from reality.tools.application import create_change_proposal

    proposal = create_change_proposal(
        session,
        tid,
        "item_create",
        {"records": [{"name": "New", "sku": "NEW", "unit": "pcs"}]},
    )
    before = reference_proposal(session, tid, proposal.id)
    assert reference_proposal(session, tid, proposal.id) == before
    assert proposal.status == "proposed"
    with pytest.raises(InvalidOperation):
        prepare_reference(
            session,
            tid,
            "item",
            "create",
            {"name": "Another", "sku": "ANOTHER"},
            request_id="write",
        )
    other = create_tenant(session, "Other proposal")
    with pytest.raises(NotFound):
        reference_proposal(session, other.id, proposal.id)


@pytest.mark.parametrize("view", ["systems", "records"])
def test_sandbox_source_reads_preserve_filtered_metadata(
    session, sandbox_business, view
):
    from reality.services.core import create_source_system, store_source_record

    tid = sandbox_business.tenant.id
    create_source_system(session, tid, "read-test", "Read test")
    store_source_record(session, tid, "read-test", "item", "SOURCE-1", {"raw": "kept"})
    before, pager = source_metadata_page(session, tid, view, size=1, query="read-test")
    assert before
    after, after_pager = source_metadata_page(
        session, tid, view, size=1, query="read-test"
    )
    assert after == before and after_pager == pager
    other = create_tenant(session, "Other sources")
    assert source_metadata_page(session, other.id, view)[0] == []
    with pytest.raises(NotFound):
        source_metadata_page(session, "missing-tenant", view)


def test_sandbox_csv_preview_and_original_preserve_bytes_and_isolation(
    session, sandbox_business, monkeypatch, tmp_path
):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setenv("REALITY_ARTIFACT_STORAGE", "file")
    tid = sandbox_business.tenant.id
    content = b"sku,name\r\nNEW,Original name\r\n"
    from reality.services.artifacts import stage_artifact

    artifact, _ = stage_artifact(
        session,
        tid,
        io.BytesIO(content),
        filename="original.csv",
        content_type="text/csv",
    )
    staged = {"id": artifact.id}
    config = {
        "artifact_id": staged["id"],
        "source_system": "csv",
        "mapping": {"sku": "sku", "name": "name"},
    }
    before = preview_item_import(session, tid, config)
    assert preview_item_import(session, tid, config) == before
    response = get_item_csv_original(tid, staged["id"], session)

    async def read_bytes():
        return b"".join([chunk async for chunk in response.body_iterator])

    assert asyncio.run(read_bytes()) == content
    with pytest.raises(InvalidOperation):
        stage_item_csv(session, tid, content, "blocked.csv")
    other = create_tenant(session, "Other artifacts")
    with pytest.raises(NotFound):
        preview_item_import(session, other.id, config)
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        get_item_csv_original(other.id, staged["id"], session)
    assert error.value.status_code == 404
