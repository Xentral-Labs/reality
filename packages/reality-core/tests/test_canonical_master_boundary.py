"""Spec 356 FR-002: canonical master changes require an exact decision."""

import pytest

from reality.services import core


@pytest.mark.parametrize("auth_mode", ["enabled", "disabled"])
@pytest.mark.parametrize("family", ["party", "item", "location"])
def test_direct_master_update_cannot_reuse_an_action_tag(
    session, business, monkeypatch, family, auth_mode
):
    monkeypatch.setenv("REALITY_AUTH_MODE", auth_mode)
    record = {
        "party": business.customer,
        "item": business.item,
        "location": business.location,
    }[family]
    before = record.name
    arguments = {
        "party": (record.id, "Unapproved changed name", "customer"),
        "item": (record.id, "UNAPPROVED-CHANGED-SKU", "Unapproved changed name", "pcs"),
        "location": (record.id, "Unapproved changed name", "warehouse"),
    }[family]
    with (
        core.executing_proposal(business.tenant.id, "forged-update-decision"),
        pytest.raises(core.InvalidOperation) as refused,
    ):
        getattr(core, f"update_{family}")(
            session, business.tenant.id, *arguments, _commit=False
        )
    assert refused.value.code == "intake_approval_required"
    session.expire(record)
    assert record.name == before


@pytest.mark.parametrize(
    "family,collection,body,model",
    [
        (
            "party",
            "parties",
            {"name": "Unconfirmed REST partner", "type": "customer"},
            "Party",
        ),
        (
            "item",
            "items",
            {"sku": "UNCONFIRMED-REST-SKU", "name": "Unconfirmed REST item"},
            "Item",
        ),
        ("location", "locations", {"name": "Unconfirmed REST location"}, "Location"),
    ],
)
def test_rest_master_request_without_confirmation_has_no_effect(
    session, business, family, collection, body, model
):
    from sqlalchemy import func, select
    from test_master_data_api import api_client, app

    from reality.db import core as records

    table = getattr(records, model)
    before = session.scalar(select(func.count()).select_from(table))
    proposals = session.scalar(select(func.count()).select_from(records.ChangeProposal))
    client = api_client(session)
    try:
        response = client.post(
            f"/api/tenants/{business.tenant.id}/{collection}", json=body
        )
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "review_confirmation_required"
        assert session.scalar(select(func.count()).select_from(table)) == before
        assert (
            session.scalar(select(func.count()).select_from(records.ChangeProposal))
            == proposals
        )
    finally:
        app.dependency_overrides.clear()
