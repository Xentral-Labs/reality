import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import Party, Tenant
from reality.services.core import (
    InvalidOperation,
    archive_tenant,
    create_document,
    create_party,
    create_tenant,
    permanently_delete_tenant,
    restore_tenant,
    tenant_usage_summaries,
    tenants,
)
from reality.web import app as web_module


def test_archived_tenants_leave_the_default_switcher_and_can_be_restored(session):
    first = create_tenant(session, "First Company")
    second = create_tenant(session, "Second Company")

    archive_tenant(session, second.id)

    assert [row.id for row in tenants(session)] == [first.id]
    assert {row.id for row in tenants(session, include_archived=True)} == {
        first.id,
        second.id,
    }
    restore_tenant(session, second.id)
    assert {row.id for row in tenants(session)} == {first.id, second.id}


def test_last_active_tenant_cannot_be_archived(session):
    tenant = create_tenant(session, "Only Company")

    with pytest.raises(InvalidOperation, match="another tenant"):
        archive_tenant(session, tenant.id)


def test_usage_projection_distinguishes_empty_configured_and_in_use(session):
    empty = create_tenant(session, "Empty")
    configured = create_tenant(session, "Configured")
    create_party(session, configured.id, "Configured Company", "company")
    active = create_tenant(session, "In Use")
    party = create_party(session, active.id, "Customer", "customer")
    create_document(session, active.id, "sales_order", "SO-1", party.id, "10")

    result = tenant_usage_summaries(session)

    assert result[empty.id]["state"] == "empty"
    assert result[configured.id]["state"] == "configured"
    assert result[active.id]["state"] == "in_use"
    assert result[active.id]["evidence_count"] == 1
    assert result[active.id]["last_activity_at"] is not None


def test_permanent_deletion_requires_archival_and_two_exact_confirmations(session):
    active = create_tenant(session, "Active Company")
    doomed = create_tenant(session, "Delete Me GmbH")
    create_party(session, doomed.id, "Customer", "customer")

    with pytest.raises(InvalidOperation, match="Archive"):
        permanently_delete_tenant(
            session,
            doomed.id,
            confirmation_name=doomed.name,
            confirmation_word="DELETE",
        )
    archive_tenant(session, doomed.id)
    with pytest.raises(InvalidOperation, match="match exactly"):
        permanently_delete_tenant(
            session,
            doomed.id,
            confirmation_name="Delete Me",
            confirmation_word="DELETE",
        )
    with pytest.raises(InvalidOperation, match="match exactly"):
        permanently_delete_tenant(
            session,
            doomed.id,
            confirmation_name=doomed.name,
            confirmation_word="delete",
        )

    permanently_delete_tenant(
        session,
        doomed.id,
        confirmation_name=doomed.name,
        confirmation_word="DELETE",
    )

    assert session.get(Tenant, doomed.id) is None
    assert session.scalar(select(Party).where(Party.tenant_id == doomed.id)) is None
    assert session.get(Tenant, active.id) is not None


@pytest.mark.skip(reason="Retired server-rendered UI; covered by tenant API tests.")
def test_tenant_management_hides_archived_tenants_and_confirms_web_deletion(
    session, monkeypatch
):
    active = create_tenant(session, "Active Company")
    archived = create_tenant(session, "Archived Company")
    archive_tenant(session, archived.id)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    client = TestClient(web_module.app)

    page = client.get("/settings/tenants", params={"tenant": active.id})
    switcher_page = client.get("/app", params={"tenant": active.id})
    rejected = client.post(
        f"/settings/tenants/{archived.id}/delete",
        data={
            "current_tenant": active.id,
            "confirmation_name": archived.name,
            "confirmation_word": "delete",
        },
    )
    deleted = client.post(
        f"/settings/tenants/{archived.id}/delete",
        data={
            "current_tenant": active.id,
            "confirmation_name": archived.name,
            "confirmation_word": "DELETE",
        },
        follow_redirects=False,
    )

    assert page.status_code == 200
    assert "Archived companies" in page.text
    assert archived.name in page.text
    assert archived.name not in switcher_page.text
    assert rejected.status_code == 400
    assert deleted.status_code == 303
