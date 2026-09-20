from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


def client_for(session, monkeypatch) -> TestClient:
    from reality.web import api as api_module
    from reality.web import app as web_module

    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setattr(web_module, "APP_URL", "http://frontend.example")
    return TestClient(web_module.app)


def test_backend_exposes_health_and_no_browser_assets(session, monkeypatch):
    client = client_for(session, monkeypatch)

    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/static/tailwind.css").status_code == 404
    assert client.get("/definitely-not-a-browser-route").status_code == 404
    assert client.post("/mcp/", json={}).status_code in {404, 405}


def test_system_status_names_the_running_version(session, monkeypatch):
    monkeypatch.setenv("REALITY_VERSION", "0.1.0")
    monkeypatch.setenv("REALITY_COMMIT", "a204c14")
    client = client_for(session, monkeypatch)

    status = client.get("/api/v1/system/status").json()

    assert status["status"] == "ready"
    assert status["version"] == "0.1.0"
    assert status["commit"] == "a204c14"


def test_tenant_application_reference_uses_validated_catalog(
    session, business, monkeypatch
):
    client = client_for(session, monkeypatch)

    response = client.get(f"/api/tenants/{business.tenant.id}/application-reference")

    assert response.status_code == 200
    payload = response.json()
    assert payload["event_count"] == 62
    assert payload["projection_count"] == 13
    assert payload["fact_predicate_count"] == 7
    action = payload["workspaces"][0]["actions"][0]
    command = next(
        command
        for command in payload["commands"]
        if command["service"] == action["command"]
    )
    assert action["description"] == command["effect"]
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    for entry in [*payload["commands"], *payload["projections"]]:
        for contract in entry["contracts"]:
            source = contract["source"]
            relative = Path(source["path"])
            assert not relative.is_absolute() and ".." not in relative.parts
            assert source["path"].startswith("packages/reality-core/src/reality/")
            tree = ast.parse((root / relative).read_text())
            assert any(
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == source["function"]
                for node in ast.walk(tree)
            )


def test_specialized_projection_views_are_allowlisted_and_bounded(
    session, business, monkeypatch
):
    from reality.web import api as api_module

    calls = []

    def fake_page(_session, tenant_id, projection_name, **values):
        calls.append((tenant_id, projection_name, values))
        return {
            "items": [{"order_key": "doc_1", "party": "Example"}],
            "page": {
                "number": 2,
                "size": 25,
                "total": 26,
                "pages": 2,
                "has_previous": True,
                "has_next": False,
            },
        }

    monkeypatch.setattr(api_module, "projection_page", fake_page)
    client = client_for(session, monkeypatch)
    tenant = business.tenant.id

    response = client.get(
        f"/api/tenants/{tenant}/projection-views/fulfillment_queue",
        params={"page": 2, "size": 25, "q": "Example"},
    )
    excluded = client.get(f"/api/tenants/{tenant}/projection-views/tenant_usage")

    assert response.status_code == 200
    assert response.json() == {
        "items": [{"order_key": "doc_1", "party": "Example"}],
        "page": {
            "number": 2,
            "size": 25,
            "total": 26,
            "pages": 2,
            "has_previous": True,
            "has_next": False,
        },
    }
    assert calls == [
        (
            tenant,
            "fulfillment_queue",
            {"page": 2, "size": 25, "query": "Example", "with_metadata": True},
        )
    ]
    assert excluded.status_code == 404


def test_missing_business_web_adapters_delegate_to_shared_services(
    session, business, monkeypatch
):
    from reality.web import api as api_module

    calls = []
    monkeypatch.setattr(
        api_module,
        "create_manual_order",
        lambda _session, tenant_id, **values: (
            calls.append(("order", tenant_id, values))
            or (
                SimpleNamespace(id="src_1"),
                SimpleNamespace(id="doc_1"),
                [SimpleNamespace(id="line_1")],
                [SimpleNamespace(id="com_1")],
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        api_module,
        "observe_fact",
        lambda _session, tenant_id, **values: (
            calls.append(("fact", tenant_id, values)) or SimpleNamespace(id="fact_1")
        ),
        raising=False,
    )
    for name in ("post_customer_payment", "post_supplier_payment"):
        monkeypatch.setattr(
            api_module,
            name,
            lambda _session, tenant_id, invoice_id, amount, **values: (
                calls.append(
                    (
                        "payment",
                        tenant_id,
                        {"invoice_id": invoice_id, "amount": amount, **values},
                    )
                )
                or [SimpleNamespace(id="led_1")]
            ),
            raising=False,
        )
    client = client_for(session, monkeypatch)
    tenant = business.tenant.id

    order = client.post(
        f"/api/tenants/{tenant}/manual-orders",
        json={
            "direction": "sales",
            "number": "SO-WEB-1",
            "company_party_id": business.company.id,
            "counterparty_id": business.customer.id,
            "location_id": business.location.id,
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit_price": "10",
                    "gross_amount": "10",
                }
            ],
            "gross_amount": "10",
        },
    )
    fact = client.post(
        f"/api/tenants/{tenant}/facts",
        json={
            "source_record_id": "src_1",
            "subject_type": "commitment",
            "subject_id": "com_1",
            "predicate": "order.shipping_priority",
            "value": "express",
            "observed_at": "2026-09-03T10:00:00Z",
            "idempotency_key": "fact-web-1",
        },
    )
    customer = client.post(
        f"/api/tenants/{tenant}/finance/customer-payments",
        json={"invoice_id": "doc_1", "amount": "10"},
    )
    supplier = client.post(
        f"/api/tenants/{tenant}/finance/supplier-payments",
        json={"invoice_id": "doc_2", "amount": "5"},
    )

    assert [response.status_code for response in (order, fact, customer, supplier)] == [
        201,
        201,
        201,
        201,
    ]
    assert [call[0] for call in calls] == ["order", "fact", "payment", "payment"]


def test_backend_redirects_retired_browser_routes_once(session, monkeypatch):
    client = client_for(session, monkeypatch)

    landing = client.get("/", params={"lang": "de"}, follow_redirects=False)
    assert landing.status_code == 308
    assert landing.headers["location"] == "http://frontend.example/?lang=de"

    product = client.get(
        "/inventory", params={"tenant": "ten_example"}, follow_redirects=False
    )
    assert product.status_code == 308
    assert product.headers["location"] == (
        "http://frontend.example/app?tenant=ten_example"
    )


def test_retired_ui_mutations_are_not_accepted(session, monkeypatch):
    client = client_for(session, monkeypatch)

    response = client.post("/integrations/systems", data={"name": "Old UI"})
    assert response.status_code in {404, 405}


def test_graph_record_suggestions_are_typed_scoped_and_bounded(
    session, business, monkeypatch
):
    from reality.db.core import Fact
    from reality.services.core import create_tenant

    foreign = create_tenant(session, "Other company")
    for index in range(13):
        session.add(
            Fact(
                id=f"graph_fact_{index:02}",
                tenant_id=business.tenant.id,
                subject_type="item",
                subject_id=business.item.id,
                predicate="priority",
                value="true",
            )
        )
    session.add(
        Fact(
            id="foreign_graph_fact",
            tenant_id=foreign.id,
            subject_type="item",
            subject_id="foreign",
            predicate="priority",
            value="true",
        )
    )
    session.flush()
    client = client_for(session, monkeypatch)
    url = f"/api/tenants/{business.tenant.id}/explorer"
    result = client.get(url, params={"kind": "fact", "q": "priority"})
    assert result.status_code == 200
    collections = [c for s in result.json()["sections"] for c in s["collections"]]
    assert [c["name"] for c in collections] == ["fact"]
    assert len(collections[0]["records"]) == 10
    assert all(r["id"] != "foreign_graph_fact" for r in collections[0]["records"])
    exact = client.get(url, params={"kind": "fact", "q": "graph_fact_00"}).json()
    assert exact["sections"][0]["collections"][0]["records"][0]["id"] == "graph_fact_00"
    for kind in (
        "party",
        "item",
        "location",
        "document",
        "document_line",
        "source_record",
        "commitment",
        "reservation",
        "movement",
        "ledger_entry",
        "payment",
        "business_event",
    ):
        assert client.get(url, params={"kind": kind}).status_code == 200
    assert client.get(url, params={"kind": "unknown"}).status_code == 422
    assert (
        client.get(url, params={"kind": "fact", "q": "foreign_graph_fact"}).json()[
            "sections"
        ][0]["collections"][0]["records"]
        == []
    )


def test_catalog_code_is_actual_source_and_catalog_allowlisted(
    session, business, monkeypatch
):
    client = client_for(session, monkeypatch)
    base = f"/api/tenants/{business.tenant.id}/catalog-code"
    for kind, key, function in [
        ("command", "reserve", "reserve"),
        ("action", "reserve_stock", "reserve"),
        ("projection", "inventory", "inventory_rows"),
        ("view", "inventory", "inventory_rows"),
        ("view", "items", "list_items"),
    ]:
        response = client.get(base, params={"kind": kind, "key": key})
        assert response.status_code == 200
        payload = response.json()
        source = next(
            item for item in payload["sources"] if item["function"] == function
        )
        assert f"def {function}(" in source["code"]
        assert source["path"].startswith("packages/reality-core/src/reality/")
        assert ".." not in source["path"].split("/")
        assert len(source["code"].encode()) <= 65536
        assert len(source["code"].splitlines()) <= 600
        assert isinstance(source["truncated"], bool)
    for kind, key in [
        ("file", "etc/passwd"),
        ("command", "_service"),
        ("view", "unknown"),
        ("projection", "../../.env"),
    ]:
        assert client.get(base, params={"kind": kind, "key": key}).status_code == 404

    from reality import catalogs

    monkeypatch.setattr(
        catalogs.inspect, "getsource", lambda _reader: "# example\n" * 601
    )
    source = client.get(base, params={"kind": "command", "key": "reserve"}).json()[
        "sources"
    ][0]
    assert source["truncated"] is True
    assert len(source["code"].splitlines()) == 600
    monkeypatch.setattr(catalogs.inspect, "getsource", lambda _reader: "é" * 40000)
    source = client.get(base, params={"kind": "command", "key": "reserve"}).json()[
        "sources"
    ][0]
    assert source["truncated"] is True
    assert len(source["code"].encode()) <= 65536


def test_reference_endpoint_reuses_global_metadata(session, business, monkeypatch):
    from reality import catalogs

    catalogs.clear_runtime_application_catalog()
    calls = []
    tool_calls = []

    def build():
        calls.append(True)
        return {"version": 1, "projections": []}

    def build_tools(catalog):
        tool_calls.append(catalog["version"])
        return {"version": 1, "entries": []}

    monkeypatch.setattr(catalogs, "load_application_catalog", build)
    monkeypatch.setattr("reality.tool_catalog.build_tool_catalog", build_tools)
    client = client_for(session, monkeypatch)
    try:
        for _ in range(2):
            response = client.get(
                f"/api/tenants/{business.tenant.id}/application-reference"
            )
            assert response.status_code == 200
            result = response.json()
            vocabulary = result.pop("search_vocabulary")
            assert vocabulary and all(
                "key" in row and "labels" in row for row in vocabulary
            )
            assert result == {
                "version": 1,
                "projections": [],
                "tool_catalog": {"version": 1, "entries": []},
            }
        assert len(calls) == 1
        assert tool_calls == [1]
    finally:
        catalogs.clear_runtime_application_catalog()


def test_projection_http_reads_do_not_materialize(session, business, monkeypatch):
    from reality.services import projections

    def forbidden(*args, **kwargs):
        raise AssertionError("Read attempted to materialize")

    monkeypatch.setattr(projections, "rebuild_projections", forbidden)
    client = client_for(session, monkeypatch)
    base = f"/api/tenants/{business.tenant.id}"
    assert client.get(base + "/projections/inventory").json() == []
    result = client.get(base + "/projection-snapshots/inventory")
    assert result.status_code == 200
    assert result.json()["metadata"]["state"] == "uninitialized"
    assert client.get(base + "/projection-snapshots/missing").status_code == 404
    assert (
        client.get(base + "/finance/open-items").json()["metadata"]["state"]
        == "uninitialized"
    )
