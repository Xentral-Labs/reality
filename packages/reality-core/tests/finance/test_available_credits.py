"""Available credit is derived symmetrically from active settlement endpoints."""

from decimal import Decimal

import pytest

from reality.services import core
from reality.services.finance.credits import available_credit_items


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_credit_availability_refund_reversal_and_scope(session, business, side):
    tenant = business.tenant.id
    party = business.customer if side == "customer" else business.supplier
    role = "accounts_receivable" if side == "customer" else "accounts_payable"
    payment = getattr(core, f"record_{side}_payment")(session, tenant, party.id, "120")
    control = next(e for e in payment if e.account == role)
    kind = "sales_invoice" if side == "customer" else "supplier_invoice"
    invoice = core.create_document(session, tenant, kind, "INV-CREDIT", party.id, "100")
    entries = getattr(
        core, f"post_{'sales' if side == 'customer' else 'supplier'}_invoice"
    )(session, tenant, invoice.id)
    target = next(e for e in entries if e.account == role)
    core.allocate_settlement(session, tenant, control.id, target.id, "100")

    def read(**kw):
        return available_credit_items(session, tenant, side=side, **kw)

    row = read()["items"][0]
    assert Decimal(row["open"]) == 20
    assert row["control_entry_id"] == control.id
    assert row["account_id"] == control.account_id
    assert len(row["allocation_ids"]) == 1
    refund = getattr(core, f"record_{side}_refund")(session, tenant, party.id, "8")
    refund_control = next(e for e in refund if e.account == role)
    # Payment credit settles the evidenced refund, without a second receipt.
    core.allocate_settlement(session, tenant, control.id, refund_control.id, "8")
    assert Decimal(read()["items"][0]["open"]) == 12
    core.reverse_ledger_posting_group(
        session, tenant, refund[0].posting_group_id, reason="Refund correction"
    )
    assert Decimal(read()["items"][0]["open"]) == 20
    getattr(core, f"record_{side}_payment")(
        session, tenant, party.id, "7", currency="USD"
    )
    assert {r["currency"] for r in read()["totals"]} == {"EUR", "USD"}
    assert not read(query="does-not-exist")["items"]
    assert read(size=1)["page"]["total"] == 2
    foreign = core.create_tenant(session, "Foreign credit company")
    assert not available_credit_items(session, foreign.id, side=side)["items"]
    core.reverse_ledger_posting_group(
        session, tenant, payment[0].posting_group_id, reason="Payment correction"
    )
    assert all(r["control_entry_id"] != control.id for r in read()["items"])


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_note_credit_target_endpoint_blocked_account_and_http(session, business, side):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.services.finance.accounts import update_account
    from reality.web.api import database_session
    from reality.web.app import app

    tenant = business.tenant.id
    party = business.customer if side == "customer" else business.supplier
    kind = "credit_note" if side == "customer" else "supplier_credit_note"
    source, _, _ = core.store_source_record(
        session,
        tenant,
        "credit_test",
        kind,
        "CREDIT",
        {"gross": "20", "currency": "EUR"},
    )
    note = core.create_document(
        session, tenant, kind, "CREDIT", party.id, "20", source_record_id=source.id
    )
    entries = getattr(
        core, f"post_{'sales' if side == 'customer' else 'supplier'}_credit_note"
    )(session, tenant, note.id)
    getattr(core, f"post_{side}_refund")(session, tenant, note.id, "8")
    role = "accounts_receivable" if side == "customer" else "accounts_payable"
    control = next(e for e in entries if e.account == role)
    update_account(session, tenant, account_id=control.account_id, state="blocked")
    result = available_credit_items(session, tenant, side=side)
    row = result["items"][0]
    assert Decimal(row["open"]) == 12
    assert row["source_record_id"] == source.id
    assert row["account_state"] == "blocked"
    assert len(row["allocation_ids"]) == 1
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/tenants/{tenant}/finance/open-items",
                params={
                    "flow": f"{side}-balance",
                    "item_status": "outstanding",
                    "q": "CREDIT",
                    "size": 1,
                },
            )
            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload["page"] == result["page"] | {"size": 1}
            assert payload["items"][0]["control_entry_id"] == control.id
            assert payload["items"][0]["source_record_id"] == source.id
            assert Decimal(payload["totals"][0]["open"]) == 12
            assert Decimal(payload["items"][0]["gross"]) == 20
    finally:
        app.dependency_overrides.clear()
