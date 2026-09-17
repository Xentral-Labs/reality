from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from reality.services.core import create_tenant
from reality.web.api import database_session
from reality.web.app import app


def test_workspace_http_scopes_reads_and_requires_exact_confirmation(session, business):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    other = create_tenant(session, "Foreign workspace")

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            assert client.get(f"{base}/analytics?days=7").status_code == 404
            # Composable contributors live at /analytics/query/contributors.
            assert client.get(f"{base}/analytics/contributors").status_code == 404
            assert (
                client.get(f"{base}/master-data?family=item&size=101").status_code
                == 422
            )
            assert (
                client.get(f"{base}/master-data/item/{business.item.id}").status_code
                == 200
            )
            assert (
                client.get(
                    f"/api/tenants/{other.id}/master-data/item/{business.item.id}"
                ).status_code
                == 404
            )
            body = {
                "family": "customer",
                "operation": "create",
                "request_id": "api-create",
                "record": {"name": "HTTP customer"},
            }
            prepared = client.post(f"{base}/master-data/prepare", json=body)
            assert prepared.status_code == 200, prepared.text
            identity = prepared.json()["id"]
            assert (
                client.get(
                    f"/api/tenants/{other.id}/master-data/proposals/{identity}"
                ).status_code
                == 404
            )
            route = f"{base}/master-data/proposals/{identity}/confirm"
            assert client.post(route, json={"confirmed": False}).status_code == 422
            assert (
                client.post(
                    route, json={"confirmed": True, "name": "Injected"}
                ).status_code
                == 422
            )
            result = client.post(route, json={"confirmed": True})
            assert result.status_code == 200, result.text
            assert result.json()["status"] == "executed"
            assert (
                client.get(f"{base}/master-data/proposals/{identity}").json()["links"]
                == result.json()["links"]
            )
            assert (
                client.post(route, json={"confirmed": True}).json()["links"]
                == result.json()["links"]
            )
            assert (
                client.get(f"{base}/master-data?family=customer&q=HTTP").json()["page"][
                    "total"
                ]
                == 1
            )
    finally:
        app.dependency_overrides.clear()


def test_master_data_prepare_accepts_typed_field_values_and_names_rejections(
    session, business
):
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            detail = client.get(f"{base}/master-data/customer/{business.customer.id}")
            assert detail.status_code == 200, detail.text
            assert {"payment_term_code", "source_system", "external_id"} <= set(
                detail.json()
            )
            body = {
                "family": "customer",
                "operation": "update",
                "request_id": "api-typed",
                "record": {
                    "id": business.customer.id,
                    "expected_revision": detail.json()["expected_revision"],
                    "roles": ["customer", "company"],
                    "credit_limit": "12.5",
                    "default_currency": "gbp",
                },
            }
            prepared = client.post(f"{base}/master-data/prepare", json=body)
            assert prepared.status_code == 200, prepared.text
            record = prepared.json()["input"]["records"][0]
            assert record["roles"] == ["company", "customer"]
            assert record["credit_limit"] == "12.5"
            assert record["default_currency"] == "GBP"
            # Omitted fields travel with their current value for review.
            assert record["name"] == business.customer.name
            assert record["accounting_code"] == ""
            rejected = client.post(
                f"{base}/master-data/prepare",
                json={
                    **body,
                    "request_id": "api-bad",
                    "record": {
                        **body["record"],
                        "lead_time_days": 3,
                    },
                },
            )
            assert rejected.status_code == 400, rejected.text
            assert "lead_time_days" in rejected.json()["detail"]
            location = client.post(
                f"{base}/master-data/prepare",
                json={
                    "family": "location",
                    "operation": "create",
                    "request_id": "api-location",
                    "record": {
                        "name": "Returns",
                        "type": "returns",
                        "parent_location_id": business.location.id,
                        "allows_stock": False,
                    },
                },
            )
            assert location.status_code == 200, location.text
            assert location.json()["input"]["records"][0]["allows_stock"] is False
    finally:
        app.dependency_overrides.clear()
