"""Spec393: existing reference observations are not mapping or acceptance."""

import pytest
import test_shopify_intake_preflight as support

from reality.db.core import Item, Location, PartyRole
from reality.domain.shopify_reference_lookup import ReferenceLookupInput
from reality.services import shopify_reference_lookup as lookup
from reality.services.core import (
    InvalidOperation,
    create_item,
    create_location,
    create_party,
)
from reality.services.shopify_order_proposal import _item_digest


@pytest.fixture
def bound(session, business):
    return support.bound.__wrapped__(session, business)


def read(session, bound, family, **kwargs):
    return lookup.shopify_source_reference_lookup(
        session,
        bound["policy"].tenant_id,
        **support.arguments(bound),
        family=family,
        **kwargs,
    )


def test_company_location_item_are_canonical_current_and_no_writes(session, bound):
    x = bound
    session.flush()
    before = support.snapshot(session)
    company = read(session, x, "company", query="Acme")
    location = read(session, x, "location", record_id=x["business"].location.id)
    item = read(session, x, "item", record_id=x["business"].item.id)
    assert company["records"][0]["id"] == x["business"].company.id
    assert company["records"][0]["roles"] == {"kind": "known", "values": ["company"]}
    assert location["records"][0]["roles"] == {"kind": "unknown"}
    assert item["records"][0]["digest"] == _item_digest(x["business"].item)
    assert item["records"][0]["stockUnit"] == x["business"].item.unit
    assert company["source_binding"]["source_hash"] == x["source"].payload_hash
    assert support.snapshot(session) == before


def test_roles_shipping_and_active_filters_never_choose_foreign_meaning(session, bound):
    x = bound
    assert (
        read(session, x, "company", record_id=x["business"].customer.id)["records"]
        == []
    )
    site = create_location(session, x["policy"].tenant_id, "Office", allows_stock=False)
    assert read(session, x, "location", record_id=site.id)["records"] == []
    x["business"].item.is_active = False
    session.flush()
    assert read(session, x, "item", record_id=x["business"].item.id)["records"] == []


def test_duplicate_skus_are_candidates_and_exact_id_overrides_query(session, bound):
    x = bound
    first = x["business"].item
    second = create_item(session, x["policy"].tenant_id, first.sku, "Second exact SKU")
    values = read(session, x, "item", query=first.sku)
    assert {row["id"] for row in values["records"]} == {first.id, second.id}
    assert all(row["roles"] == {"kind": "unknown"} for row in values["records"])
    assert (
        read(session, x, "item", record_id=second.id, query="does not match")[
            "records"
        ][0]["id"]
        == second.id
    )


def test_bounds_tenant_and_source_guards(session, bound):
    x = bound
    for i in range(23):
        create_item(session, x["policy"].tenant_id, f"REF{i}", f"Bounded {i}")
    values = read(session, x, "item", query="Bounded")
    assert len(values["records"]) == 20 and values["hasMore"] is True
    with pytest.raises(ValueError):
        ReferenceLookupInput.model_validate(
            {**support.arguments(x), "family": "item", "query": "x" * 121}
        )
    with pytest.raises(InvalidOperation):
        lookup.shopify_source_reference_lookup(
            session, "foreign", **support.arguments(x), family="company"
        )
    with pytest.raises(InvalidOperation):
        lookup.shopify_source_reference_lookup(
            session,
            x["policy"].tenant_id,
            **{**support.arguments(x), "source_version": 999},
            family="company",
        )


def test_selected_reference_change_during_read_refuses_mixed_report(
    session, bound, monkeypatch
):
    original = lookup._candidates
    calls = 0

    def changing(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 1:
            bound["business"].company.name = "Changed after observation"
            session.flush()
        return result

    monkeypatch.setattr(lookup, "_candidates", changing)
    with pytest.raises(InvalidOperation):
        read(session, bound, "company")


@pytest.mark.parametrize(
    "family,changed", [("company", "role"), ("location", "stock"), ("item", "unit")]
)
def test_two_session_reference_change_refuses(
    postgres_database, monkeypatch, request, family, changed
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from types import SimpleNamespace

    from sqlalchemy import create_engine, delete
    from sqlalchemy.orm import Session

    from reality.db.core import Base
    from reality.services.core import create_tenant

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    writer = Session(engine, expire_on_commit=False)
    request.addfinalizer(engine.dispose)
    request.addfinalizer(writer.close)
    tenant = create_tenant(writer, "Owned393 concurrent company")
    business = SimpleNamespace(
        tenant=tenant,
        company=create_party(writer, tenant.id, "Existing company", "company"),
        customer=create_party(writer, tenant.id, "Existing buyer", "customer"),
        item=create_item(writer, tenant.id, "BIKE-LIGHT", "Light"),
        location=create_location(writer, tenant.id, "Existing warehouse"),
    )
    x = support.bound.__wrapped__(writer, business)
    writer.commit()
    reached, done = Event(), Event()
    original = lookup._candidates

    def delayed(*args, **kwargs):
        result = original(*args, **kwargs)
        if not reached.is_set():
            reached.set()
            assert done.wait(5)
        return result

    monkeypatch.setattr(lookup, "_candidates", delayed)

    def run():
        with Session(engine) as reader, pytest.raises(InvalidOperation):
            read(reader, x, family)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run)
        assert reached.wait(5)
        try:
            with Session(engine) as changer:
                if changed == "role":
                    changer.execute(
                        delete(PartyRole).where(
                            PartyRole.tenant_id == tenant.id,
                            PartyRole.party_id == business.company.id,
                            PartyRole.role == "company",
                        )
                    )
                elif changed == "stock":
                    changer.get(
                        Location, {"tenant_id": tenant.id, "id": business.location.id}
                    ).allows_stock = False
                else:
                    changer.get(
                        Item, {"tenant_id": tenant.id, "id": business.item.id}
                    ).unit = "box"
                changer.commit()
        finally:
            done.set()
        future.result(timeout=8)


def test_authenticated_mcp_read_contract_and_no_generic_permission(
    session, bound, monkeypatch
):
    import json
    import os
    from pathlib import Path

    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.domain.shopify_reference_lookup import ReferenceLookupResult
    from reality.mcp import auth as auth_module
    from reality.mcp import server as server_module
    from reality.mcp.app import create_mcp_app
    from reality.mcp.auth import create_mcp_access_token
    from reality.mcp.config import MCPRuntimeSettings

    tool = "shopify_source_reference_lookup"
    _token, clear = create_mcp_access_token(
        session, bound["policy"].tenant_id, "Owned393 read-only", [tool]
    )
    factory = sessionmaker(
        session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(server_module, "Session", factory)
    runtime = create_mcp_app(
        settings=MCPRuntimeSettings(
            public_url="http://localhost:8001/", bind_host="127.0.0.1", bind_port=8001
        ),
        session_factory=factory,
    )
    headers = {
        "Authorization": "Bearer " + clear,
        "Accept": "application/json, text/event-stream",
        "Host": "localhost:8001",
        "MCP-Protocol-Version": "2025-03-26",
    }
    with TestClient(runtime) as client:
        initialized = client.post(
            "/",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "owned393", "version": "1"},
                },
            },
        )
        assert initialized.status_code == 200
        advertised = client.post(
            "/",
            headers=headers,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        )
        assert advertised.status_code == 200
        definition = next(
            v for v in advertised.json()["result"]["tools"] if v["name"] == tool
        )
        assert definition["annotations"]["readOnlyHint"] is True
        assert definition["annotations"]["destructiveHint"] is False
        response = client.post(
            "/",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool,
                    "arguments": {
                        **support.arguments(bound),
                        "family": "company",
                        "query": "",
                        "record_id": None,
                    },
                },
            },
        )
        assert response.status_code == 200
        assert not response.json()["result"].get("isError"), response.text
        wire = json.loads(response.json()["result"]["content"][0]["text"])
        assert ReferenceLookupResult.model_validate(wire).records
        denied = client.post(
            "/",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "proposal_approve_and_execute",
                    "arguments": {"proposal_id": "no-write"},
                },
            },
        )
        assert denied.status_code == 200 and denied.json()["result"].get("isError")
        noauth = client.post(
            "/",
            headers={k: v for k, v in headers.items() if k != "Authorization"},
            json={"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {}},
        )
        assert noauth.status_code == 401
        if directory := os.environ.get("REALITY_393_CAPTURE_DIRECTORY"):
            root = Path(directory)
            root.mkdir(parents=True, exist_ok=True)
            root.joinpath("actual-sdk-advertisement.json").write_text(
                json.dumps(definition, indent=2, ensure_ascii=False) + "\n"
            )
            root.joinpath("actual-sdk-initialize.json").write_text(
                json.dumps(initialized.json(), indent=2) + "\n"
            )
            root.joinpath("response.example.json").write_text(
                json.dumps(wire, indent=2, ensure_ascii=False) + "\n"
            )


def test_frozen_json_schemas_and_actual_wire_examples():
    import json
    from pathlib import Path

    import jsonschema

    from reality.domain.shopify_reference_lookup import ReferenceLookupResult

    contracts = (
        Path(__file__).parents[3] / "specs/393-shopify-reference-lookup/contracts"
    )
    request_schema = json.loads((contracts / "input.schema.json").read_text())
    response_schema = json.loads((contracts / "response.schema.json").read_text())
    assert request_schema == ReferenceLookupInput.model_json_schema()
    assert response_schema == ReferenceLookupResult.model_json_schema()
    jsonschema.validate(
        json.loads((contracts / "input.example.json").read_text()), request_schema
    )
    jsonschema.validate(
        json.loads((contracts / "response.example.json").read_text()), response_schema
    )
    advertised = json.loads((contracts / "actual-sdk-advertisement.json").read_text())
    assert advertised["name"] == "shopify_source_reference_lookup"
    assert advertised["inputSchema"]["properties"] == request_schema["properties"]
    assert set(advertised["inputSchema"]["required"]) == set(request_schema["required"])
