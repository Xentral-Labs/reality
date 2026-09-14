import pytest
from test_http_boundary import client_for

from reality.services.core import InvalidOperation, create_item, create_tenant
from reality.services.inspector_register import inspector_records


def test_record_register_pages_searches_and_isolates(session, business):
    for index in range(27):
        create_item(
            session, business.tenant.id, f"SCAN-{index:02}", f"Scanner {index:02}"
        )
    other = create_tenant(session, "Other company")
    foreign = create_item(session, other.id, "FOREIGN", "Secret scanner")
    page1 = inspector_records(session, business.tenant.id, kind="item", size=25)
    page2 = inspector_records(session, business.tenant.id, kind="item", size=25, page=2)
    assert page1["page"]["total"] == 28
    assert len(page1["items"]) == 25
    assert len(page2["items"]) == 3
    assert not {r["id"] for r in page1["items"]} & {r["id"] for r in page2["items"]}
    assert (
        inspector_records(session, business.tenant.id, query=foreign.id)["items"] == []
    )
    matched = inspector_records(
        session, business.tenant.id, query="Scanner 26", kind="item"
    )
    assert matched["page"]["total"] == 1
    all_rows = inspector_records(session, business.tenant.id, size=100)
    assert {r["kind"] for r in all_rows["items"]} >= {
        "party",
        "item",
        "location",
        "business_event",
    }
    assert {r["kind"] for r in all_rows["types"]} >= {
        "fact",
        "document_line",
        "source_record",
        "ledger_entry",
    }
    assert all("payload" not in r and "tenant_id" not in r for r in all_rows["items"])
    with pytest.raises(InvalidOperation):
        inspector_records(session, business.tenant.id, kind="app_user")


def test_record_register_http_boundary(session, business, monkeypatch):
    client = client_for(session, monkeypatch)
    url = f"/api/tenants/{business.tenant.id}/inspector-records"
    assert (
        client.get(url + "?kind=item&size=25").json()["items"][0]["id"]
        == business.item.id
    )
    assert client.get(url + "?kind=app_user").status_code == 422
    assert client.get(url + "?size=1000").status_code == 422
    assert client.get(url + "?page=0").status_code == 422
