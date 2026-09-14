from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from unified_fixtures import delivery_fixture

from reality.web.api import database_session
from reality.web.app import app


def test_delivery_http_exposes_authoritative_case_and_sample_scope(session, business):
    fixture = delivery_fixture(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            response = client.get(f"{base}/delivery-work")
            assert response.status_code == 200
            assert response.json()["items"][0]["id"] == fixture.commitment.id
            response = client.get(f"{base}/delivery-work/{fixture.commitment.id}")
            assert response.status_code == 200
            assert response.json()["case"]["id"] == fixture.commitment.id
            assert client.get(f"{base}/delivery-work/missing").status_code == 404
            assert (
                client.get(f"{base}/dashboard").json()["sample_scope"]["exceptions"][
                    "limit"
                ]
                == 5
            )
    finally:
        app.dependency_overrides.clear()


def test_action_http_validates_review_and_session_before_effect(session, business):
    from decimal import Decimal

    from reality.services.core import (
        active_reserved,
        create_chat_session,
        create_tenant,
    )

    fixture = delivery_fixture(session, business)
    other = create_tenant(session, "Foreign company")
    chat = create_chat_session(session, other.id)
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            body = {
                "request_id": "http-action",
                "tool": "reserve",
                "arguments": {"commitment_id": fixture.commitment.id, "quantity": "12"},
            }
            assert (
                client.post(
                    f"{base}/delivery-actions/prepare",
                    json={**body, "session_id": chat.id},
                ).status_code
                == 404
            )
            prepared = client.post(f"{base}/delivery-actions/prepare", json=body)
            assert prepared.status_code == 200
            data = prepared.json()
            assert active_reserved(session, business.tenant.id, business.item.id) == 0
            route = f"{base}/change-proposals/{data['id']}/approve"
            assert client.post(route, json={"confirmed": True}).status_code == 400
            assert (
                client.post(
                    route,
                    json={
                        "confirmed": True,
                        "review_token": data["review"]["token"],
                        "quantity": "99",
                    },
                ).status_code
                == 422
            )
            response = client.post(
                route, json={"confirmed": True, "review_token": data["review"]["token"]}
            )
            assert response.status_code == 200
            assert Decimal(response.json()["output"]["applied"]) == 12
            assert (
                client.get(f"{base}/delivery-actions/{data['id']}").json()[
                    "verification"
                ]
                == "verified"
            )
    finally:
        app.dependency_overrides.clear()
