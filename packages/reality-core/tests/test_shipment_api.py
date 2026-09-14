from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from reality.services.shipments import record_shipment_notice
from reality.web.api import database_session
from reality.web.app import app


def test_shipment_http_reads_and_reviewed_notice_action(session, business):
    shipment, package, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
        carrier="DHL",
        tracking_number="HTTP-TRACK",
    )
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            listing = client.get(f"{base}/shipments?q=http-track&direction=outbound")
            assert listing.status_code == 200
            assert listing.json()["items"][0]["id"] == shipment.id
            assert client.get(f"{base}/shipments/{shipment.id}").status_code == 200
            assert client.get(f"{base}/shipments/missing").status_code == 404
            shipment_inspector = client.get(
                f"{base}/inspector/shipment/{shipment.id}"
            )
            assert shipment_inspector.status_code == 200, shipment_inspector.text
            assert shipment_inspector.json()["id"] == shipment.id
            package_inspector = client.get(
                f"{base}/inspector/shipment_package/{package.id}"
            )
            assert package_inspector.status_code == 200, package_inspector.text
            assert package_inspector.json()["id"] == package.id

            prepared = client.post(
                f"{base}/delivery-actions/prepare",
                json={
                    "request_id": "http-shipment-notice",
                    "tool": "shipment_notice_record",
                    "arguments": {
                        "direction": "inbound",
                        "purpose": "supplier_delivery",
                        "counterparty_id": business.supplier.id,
                        "tracking_number": "HTTP-IN",
                    },
                },
            )
            assert prepared.status_code == 200
            review = prepared.json()["review"]
            route = f"{base}/change-proposals/{prepared.json()['id']}/approve"
            assert client.post(route, json={"confirmed": True}).status_code == 400
            confirmed = client.post(
                route,
                json={"confirmed": True, "review_token": review["token"]},
            )
            assert confirmed.status_code == 200
            assert confirmed.json()["output"]["shipment_id"]
    finally:
        app.dependency_overrides.clear()
