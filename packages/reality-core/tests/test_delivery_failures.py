"""Spec 335: parcels that came back undeliverable, were refused or were lost."""

import json
from datetime import timedelta
from decimal import Decimal

import pytest
from intake_review_support import reviewed_reserve
from unified_fixtures import delivery_fixture

from reality.services import core
from reality.services.delivery_failures import (
    delivery_failure_summary,
    record_delivery_failure,
)
from reality.services.finance.accounts import (
    list_accounts,
)
from reality.services.shipments import shipment_explain
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def _dispatch(session, business, promise, quantity="2", **extra):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": promise.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": quantity,
                }
            ],
            **extra,
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    return json.loads(executed.output)["shipment_id"]


def _shipped(session, business, quantity="2", **extra):
    fixture = delivery_fixture(session, business, quantity=quantity)
    reviewed_reserve(session, business.tenant.id, fixture.commitment.id)
    shipment_id = _dispatch(session, business, fixture.commitment, quantity, **extra)
    session.refresh(fixture.commitment)
    assert fixture.commitment.status == "fulfilled"
    return fixture.commitment, shipment_id


def _stock(session, business):
    return core.stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    )


def claim_account(session, tenant):
    state = list_accounts(session, tenant)
    if "carrier_claim_income" in state["defaults"]:
        return
    account = reviewed_create_account(
        session,
        tenant,
        code="4830",
        name="Carrier and insurance claims",
        role="carrier_claim_income",
        expected_revision=state["revision"],
    )
    reviewed_set_default_account(
        session,
        tenant,
        role="carrier_claim_income",
        account_id=account["id"],
        expected_revision=list_accounts(session, tenant)["revision"],
    )


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def test_an_undeliverable_parcel_reopens_the_promise_and_brings_the_goods_back(
    session, business
):
    tenant = business.tenant.id
    promise, shipment_id = _shipped(session, business)
    after_shipment = _stock(session, business)
    # Positive control: a customer return keeps the promise kept (spec 079).
    returned, _ = _shipped(session, business, quantity="1")
    core.record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "1",
        to_location_id=business.location.id,
        commitment_id=returned.id,
    )
    session.refresh(returned)
    assert returned.status == "fulfilled"
    stock_before = _stock(session, business)

    failure = record_delivery_failure(
        session,
        tenant,
        shipment_id=shipment_id,
        kind="undeliverable",
        reason="Address unknown",
    )

    session.refresh(promise)
    assert promise.status == "open"
    assert core.open_quantity(session, tenant, promise.id) == Decimal(2)
    assert _stock(session, business) == stock_before + 2
    assert after_shipment < stock_before + 2
    detail = shipment_explain(session, tenant, shipment_id)
    assert detail["delivery_failure"]["kind"] == "undeliverable"
    assert detail["movements"] == []
    summary = delivery_failure_summary(session, tenant, delivery_failure_id=failure.id)
    assert summary["goods"] == "back_in_stock"
    assert len(summary["corrections"]) == 1
    assert summary["claim"] is None

    # A person reships it: reserved and shipped again, the promise is kept.
    reviewed_reserve(session, tenant, promise.id)
    _dispatch(session, business, promise)
    session.refresh(promise)
    assert promise.status == "fulfilled"


def test_a_refusal_keeps_its_reason(session, business):
    tenant = business.tenant.id
    promise, shipment_id = _shipped(session, business)
    record_delivery_failure(
        session,
        tenant,
        shipment_id=shipment_id,
        kind="refused",
        reason="Customer refused: parcel damaged",
    )
    failure = shipment_explain(session, tenant, shipment_id)["delivery_failure"]
    assert (failure["kind"], failure["reason"]) == (
        "refused",
        "Customer refused: parcel damaged",
    )
    session.refresh(promise)
    assert promise.status == "open"


def test_a_lost_parcel_is_written_off_and_claimed_from_the_carrier(session, business):
    tenant = business.tenant.id
    claim_account(session, tenant)
    carrier = reviewed_create_party(session, tenant, "Parcel Carrier GmbH", "supplier")
    promise, shipment_id = _shipped(
        session, business, carrier="DHL", tracking_number="LOST-1"
    )
    after_shipment = _stock(session, business)

    failure = record_delivery_failure(
        session,
        tenant,
        shipment_id=shipment_id,
        kind="lost",
        reason="Lost in transit, carrier confirmed",
        claim_party_id=carrier.id,
        claim_amount="25.00",
    )

    session.refresh(promise)
    assert promise.status == "open"
    assert _stock(session, business) == after_shipment
    claim = delivery_failure_summary(session, tenant, shipment_id=shipment_id)["claim"]
    assert claim["number"] == "LOST-1-CLAIM"
    assert (claim["party_id"], claim["amount"], claim["open"]) == (
        carrier.id,
        "25.0000",
        "25.0000",
    )
    assert failure.kind == "lost"

    # The carrier pays: an ordinary incoming payment settles the claim.
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.settlement.apply",
        {
            "document_id": claim["document_id"],
            "mode": "payment",
            "amount": "25",
            "allocation_amount": "25",
            "reference": "Carrier claim payment",
            "effective_at": core.now().isoformat(),
            "expected_revision": list_accounts(session, tenant)["revision"],
        },
        actor_type="human",
    )
    approve_and_execute_proposal(session, tenant, proposal.id, confirmed=True)
    assert core.open_invoice_amount(session, tenant, claim["document_id"]) == 0


def test_what_is_refused(session, business):
    tenant = business.tenant.id
    promise, shipment_id = _shipped(session, business)
    carrier = reviewed_create_party(session, tenant, "Carrier", "supplier")

    def record(**values):
        return lambda: record_delivery_failure(
            session,
            tenant,
            **{"shipment_id": shipment_id, "kind": "undeliverable", "reason": "x"}
            | values,
        )

    _refused("delivery_failure_kind_invalid", record(kind="stolen"))
    _refused("delivery_failure_reason_required", record(reason="  "))
    _refused(
        "delivery_failure_time_future",
        record(occurred_at=(core.now() + timedelta(days=1)).isoformat()),
    )
    _refused(
        "delivery_failure_before_shipment",
        record(occurred_at=(core.now() - timedelta(days=30)).isoformat()),
    )
    _refused(
        "delivery_failure_claim_lost_only",
        record(claim_party_id=carrier.id, claim_amount="5"),
    )
    _refused("delivery_failure_claim_incomplete", record(kind="lost", claim_amount="5"))
    _refused(
        "delivery_failure_claim_amount_invalid",
        record(kind="lost", claim_party_id=carrier.id, claim_amount="-1"),
    )
    _refused(
        "finance_account_default_missing",
        record(kind="lost", claim_party_id=carrier.id, claim_amount="5"),
    )
    # Positive control: the same shipment fails once, and then never again.
    record()()
    _refused("delivery_failure_already_recorded", record())
    session.refresh(promise)
    assert promise.status == "open"


def test_only_an_outbound_customer_delivery_can_fail(session, business):
    from reality.services.shipments import record_shipment_notice

    shipment, _, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="inbound",
        purpose="supplier_delivery",
        counterparty_id=business.supplier.id,
    )
    _refused(
        "delivery_failure_not_customer_delivery",
        lambda: record_delivery_failure(
            session,
            business.tenant.id,
            shipment_id=shipment.id,
            kind="undeliverable",
            reason="x",
        ),
    )


def test_another_company_cannot_record_or_read_it(session, business):
    _, shipment_id = _shipped(session, business)
    other = core.create_tenant(session, "Other GmbH")
    with pytest.raises(core.NotFound):
        record_delivery_failure(
            session, other.id, shipment_id=shipment_id, kind="lost", reason="x"
        )
    record_delivery_failure(
        session,
        business.tenant.id,
        shipment_id=shipment_id,
        kind="undeliverable",
        reason="Address unknown",
    )
    with pytest.raises(core.NotFound):
        delivery_failure_summary(session, other.id, shipment_id=shipment_id)


def test_the_reviewed_action_records_once_and_verifies(session, business):
    from reality.services.delivery_actions import delivery_proposal_detail

    tenant = business.tenant.id
    promise, shipment_id = _shipped(session, business)
    proposal = create_change_proposal(
        session,
        tenant,
        "shipment_delivery_failure",
        {"shipment_id": shipment_id, "kind": "refused", "reason": "Refused at door"},
    )
    review = json.loads(proposal.input)["_delivery_review"]
    assert review["effect"]["goods"] == "back_in_stock"
    assert review["effect"]["reopened"][0]["open_after"] == "2.0000"
    # Nothing changes before confirmation.
    session.refresh(promise)
    assert promise.status == "fulfilled"

    executed = approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=review["token"], confirmed=True
    )
    receipt = json.loads(executed.output)
    replay = approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=review["token"], confirmed=True
    )
    assert json.loads(replay.output) == receipt
    detail = delivery_proposal_detail(session, tenant, proposal.id)
    assert detail["verification"] == "verified"
    assert detail["observation"]["kind"] == "refused"
    session.refresh(promise)
    assert promise.status == "open"


def test_an_agent_records_a_lost_parcel_through_the_strict_schema(session, business):
    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.mcp.server import _reject_unknown_fields

    tenant = business.tenant.id
    claim_account(session, tenant)
    carrier = reviewed_create_party(session, tenant, "Insurer AG", "supplier")
    _, shipment_id = _shipped(session, business)
    arguments = {
        "shipment_id": shipment_id,
        "kind": "lost",
        "reason": "Lost in the hub",
        "claim_party_id": carrier.id,
        "claim_amount": "40",
    }
    definition = MCP_TOOL_REGISTRY["shipment_delivery_failure_propose"]
    _reject_unknown_fields(definition.input_schema, arguments)

    proposed = definition.handler(session, tenant, arguments)

    assert proposed["proposal_id"]
    read = MCP_TOOL_REGISTRY["delivery_failure_summary"]
    with pytest.raises(core.NotFound):
        read.handler(session, tenant, {"shipment_id": shipment_id})


from intake_review_support import (
    reviewed_create_account,
    reviewed_create_party,
    reviewed_set_default_account,
)
