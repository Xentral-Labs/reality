from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from reality.services.core import (
    create_document,
    create_tenant,
    post_customer_payment,
    post_sales_invoice,
)
from reality.web import api as api_module
from reality.web.app import app


def api_client(session):
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def override_session():
        with factory() as api_session:
            yield api_session

    app.dependency_overrides[api_module.database_session] = override_session
    return TestClient(app)


def test_journal_read_is_tenant_scoped_balanced_filterable_and_inspectable(
    session, business
):
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "UX-JOURNAL-1",
        business.customer.id,
        100,
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)
    post_customer_payment(
        session,
        business.tenant.id,
        invoice.id,
        40,
        payment_number="UX-BANK-1",
    )
    client = api_client(session)
    try:
        response = client.get(
            f"/api/tenants/{business.tenant.id}/finance/journal",
            params={"account": "accounts_receivable"},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["page"]["size"] == 50
        assert payload["page"]["total"] == 2
        assert {row["account"] for row in payload["items"]} == {
            "accounts_receivable"
        }
        assert all(row["inspect_kind"] == "ledger_entry" for row in payload["items"])
        assert all(row["inspect_id"] == row["id"] for row in payload["items"])
        inspector = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/ledger_entry/{payload['items'][0]['id']}"
        )
        assert inspector.status_code == 200
        assert inspector.json()["trail"][-1]["label"] == "Ledger"
        totals = payload["totals"]
        assert totals == [
            {
                "currency": "EUR",
                "debit": "100.0000",
                "credit": "40.0000",
                "balance": "60.0000",
            }
        ]

        foreign = create_tenant(session, "Foreign Journal")
        hidden = client.get(
            f"/api/tenants/{foreign.id}/finance/journal",
            params={"q": "UX-JOURNAL-1"},
        )
        assert hidden.status_code == 200
        assert hidden.json()["items"] == []
    finally:
        app.dependency_overrides.clear()
