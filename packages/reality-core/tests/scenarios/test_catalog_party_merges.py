"""Spec 339: business stories for merging duplicate business partners (L10, O02)."""

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from intake_review_support import accept_shopify_order as ingest_shopify_order

from reality.db.core import Party
from reality.services import core
from reality.services.credit_exposure import credit_exposure
from reality.services.finance.balances import party_balances
from reality.services.party_merges import merge_party, party_merges
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)

AS_OF = datetime(2026, 12, 31, 12, tzinfo=UTC)


def _shop_order(session, business, number, customer_id):
    payload = {
        "id": number,
        "name": f"#{number}",
        "currency": "EUR",
        "total_price": "49.00",
        "line_items": [
            {
                "id": number * 10,
                "sku": business.item.sku,
                "quantity": 1,
                "price": "49.00",
            }
        ],
    }
    _, document, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        customer_id,
        business.location.id,
    )
    return document


def _invoice(session, business, number, amount, party_id):
    document = core.create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        party_id,
        amount,
        document_date="2026-11-02",
    )
    core.post_sales_invoice(session, business.tenant.id, document.id)
    return document


def _merge(session, business, duplicate_id, survivor_id, reason):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "party_merge",
        {
            "duplicate_party_id": duplicate_id,
            "surviving_party_id": survivor_id,
            "reason": reason,
        },
    )
    review = json.loads(proposal.output)["party_merge"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )
    assert executed.status == "executed"
    return review


def _balance(session, business):
    return {
        row["party_id"]: Decimal(row["open"])
        for row in party_balances(
            session, business.tenant.id, side="customer", as_of=AS_OF
        )["items"]
    }


def test_a_guest_order_later_with_an_account(session, business):
    """L10: the guest's history moves under the account, and the next order lands there."""
    tenant = business.tenant.id
    guest = core.create_party(
        session, tenant, "Anna Schmidt (guest checkout)", "customer"
    )
    account = core.create_party(session, tenant, "Anna Schmidt", "customer")
    guest_order = _shop_order(session, business, 7001, guest.id)
    _invoice(session, business, "INV-7001", "49.00", guest.id)
    account_order = _shop_order(session, business, 7002, account.id)
    # Positive control: before the merge, two partners each answer for their half.
    assert {
        d.id for d in core.party_detail(session, tenant, account.id)["documents"]
    } == {account_order.id}
    assert _balance(session, business) == {guest.id: Decimal("49.00")}

    review = _merge(
        session, business, guest.id, account.id, "Guest checkout, same e-mail"
    )

    assert review["duplicate"]["documents"] == 2
    detail = core.party_detail(session, tenant, account.id)
    assert {d.number for d in detail["documents"]} >= {
        guest_order.number,
        account_order.number,
        "INV-7001",
    }
    # History is kept as stated: the guest order still names the guest.
    session.refresh(guest_order)
    assert guest_order.party_id == guest.id
    assert _balance(session, business) == {account.id: Decimal("49.00")}
    session.refresh(guest)
    assert guest.is_active is False

    # The shop still names the guest; the order lands on the account.
    later = _shop_order(session, business, 7003, guest.id)
    assert later.party_id == account.id


def test_two_partners_merged_as_duplicates(session, business):
    """O02: both histories are kept and read under the survivor; no chains."""
    tenant = business.tenant.id
    survivor = core.create_party(
        session, tenant, "Bäckerei Huber", "customer", credit_limit="1000"
    )
    duplicate = core.create_party(session, tenant, "Baeckerei Huber", "customer")
    third = core.create_party(session, tenant, "Huber KG", "customer")
    _invoice(session, business, "INV-H1", "600", survivor.id)
    _invoice(session, business, "INV-H2", "700", duplicate.id)
    # Positive control: each half alone stays inside the limit.
    assert credit_exposure(session, tenant, survivor.id)["over_limit"] is False

    _merge(session, business, duplicate.id, survivor.id, "Created twice by hand")

    exposure = credit_exposure(session, tenant, survivor.id)
    assert (exposure["exposure"], exposure["over_limit"]) == (Decimal(1300), True)
    assert _balance(session, business)[survivor.id] == Decimal(1300)
    assert (
        core.party_detail(session, tenant, duplicate.id)["merged_into"]["party_id"]
        == survivor.id
    )
    (merge,) = party_merges(session, tenant, party_id=survivor.id)
    assert (merge["duplicate"], merge["reason"]) == (
        duplicate.name,
        "Created twice by hand",
    )

    with pytest.raises(core.InvalidOperation) as refused:
        merge_party(session, tenant, third.id, duplicate.id, "Also Huber")
    assert refused.value.code == "party_merge_already_merged"
    assert session.get(Party, (tenant, third.id)).is_active is True
