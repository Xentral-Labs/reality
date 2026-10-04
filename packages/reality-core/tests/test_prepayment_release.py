"""Spec 347: an owner ships a partly prepaid order before it is paid."""

import json
from decimal import Decimal

import pytest
from intake_review_support import (
    reviewed_create_payment_term,
    reviewed_manual_order,
    reviewed_post_customer_payment,
)
from sqlalchemy import select

from reality.db.core import (
    AppUser,
    BusinessEvent,
    PrepaymentRelease,
    TenantMembership,
    uid,
)
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.delivery_reads import delivery_case
from reality.services.fulfillment_readiness import fulfillment_readiness
from reality.services.memberships import Principal
from reality.tools.application import approve_and_execute_proposal


def _person(session, tenant, role):
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('m')}@example.test",
        password_hash="x",
        display_name=role,
        status="active",
        email_verified_at=core.now(),
    )
    session.add(user)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("mem"), tenant_id=tenant, user_id=user.id, role=role, status="active"
        )
    )
    session.flush()
    return Principal(user.id)


def _order(session, business, number, *, prepaid=True, paid="80.00"):
    tenant = business.tenant.id
    code = "PREPAY" if prepaid else "NET30"
    if not session.scalar(
        select(core.PaymentTerm.id).where(
            core.PaymentTerm.tenant_id == tenant, core.PaymentTerm.code == code
        )
    ):
        reviewed_create_payment_term(
            session,
            tenant,
            code,
            code,
            0 if prepaid else 30,
            requires_prepayment=prepaid,
        )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    _, order, lines, (promise,) = reviewed_manual_order(
        session,
        tenant,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": "10",
                "gross_amount": "100.00",
            }
        ],
        "100.00",
        payment_term_code=code,
    )
    core.reserve(session, tenant, promise.id)
    proposal = prepare_delivery_action(
        session,
        tenant,
        "sales_invoice_record",
        {
            "order_line_id": lines[0].id,
            "quantity": "10",
            "gross_amount": "100.00",
            "number": f"RE-{number}",
            "effective_at": "2026-09-01T10:00:00Z",
        },
        request_id=f"inv-{number}",
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    receipt = json.loads(
        approve_and_execute_proposal(
            session, tenant, proposal.id, review_token=token, confirmed=True
        ).output
    )
    invoice = session.get(
        core.Document,
        (
            tenant,
            next(
                row["id"] for row in receipt["records"] if row["family"] == "document"
            ),
        ),
    )
    if Decimal(paid):
        reviewed_post_customer_payment(session, tenant, invoice.id, paid)
    return order, promise, invoice


def _prepare(session, business, order, reason="Long-standing customer, rest by Friday"):
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "prepayment_release",
        {"document_id": order.id, "reason": reason},
        request_id=f"ppr-{order.id}-{reason[:5]}",
    )


def _confirm(session, business, proposal, principal):
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=token,
        confirmed=True,
        confirming_principal=principal,
    )


def test_an_owner_releases_a_partly_paid_order_and_it_ships(session, business):
    tenant = business.tenant.id
    order, promise, invoice = _order(session, business, "SO-PPR-1")
    before = fulfillment_readiness(session, tenant, promise.id)
    assert "prepayment_required" in before.blocker_codes
    assert not before.ship_ready

    proposal = _prepare(session, business, order)
    review = json.loads(proposal.input)["_delivery_review"]
    assert review["state"]["payment"]["remaining"] == "20.0000"
    assert review["effect"]["owner_required"] is True
    executed = _confirm(session, business, proposal, _person(session, tenant, "owner"))
    assert executed.status == "executed"

    after = fulfillment_readiness(session, tenant, promise.id)
    assert after.ship_ready
    assert after.prepayment_release_id
    # The unpaid rest stays an ordinary open receivable.
    assert after.remaining_amount == Decimal("20.0000")
    assert core.open_invoice_amount(session, tenant, invoice.id) == Decimal("20.0000")
    event = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.event_type == "order.prepayment_released",
            BusinessEvent.action_id == proposal.id,
        )
    ).one()
    payload = json.loads(event.payload)
    assert (event.subject_type, event.subject_id) == ("document", order.id)
    assert payload["reason"] == "Long-standing customer, rest by Friday"
    assert payload["lifts"] == ["prepayment_required"]
    # The delivery case names the release.
    case = delivery_case(session, tenant, promise.id)["case"]
    assert case["prepayment"]["release_id"] == after.prepayment_release_id
    assert case["prepayment"]["blockers"] == []


def test_a_member_who_is_not_an_owner_cannot_release_it(session, business):
    tenant = business.tenant.id
    order, promise, _ = _order(session, business, "SO-PPR-2")
    proposal = _prepare(session, business, order)
    with pytest.raises(core.InvalidOperation) as refused:
        _confirm(session, business, proposal, _person(session, tenant, "member"))
    assert refused.value.code == "company_owner_access_required"
    assert (
        "prepayment_required"
        in fulfillment_readiness(session, tenant, promise.id).blocker_codes
    )
    assert case_offers_release(session, tenant, promise.id)


def case_offers_release(session, tenant, promise_id):
    return delivery_case(session, tenant, promise_id)["case"]["prepayment"][
        "owner_release"
    ]


@pytest.mark.parametrize(
    ("number", "prepaid", "paid", "reason", "code"),
    [
        ("SO-PPR-N", False, "0", "Ship it", "prepayment_release_not_required"),
        (
            "SO-PPR-P",
            True,
            "100.00",
            "Ship it",
            "prepayment_release_nothing_to_release",
        ),
        ("SO-PPR-R", True, "80.00", "   ", "prepayment_release_reason_missing"),
    ],
)
def test_a_release_is_refused_where_it_cannot_stand(
    session, business, number, prepaid, paid, reason, code
):
    order, _, _ = _order(session, business, number, prepaid=prepaid, paid=paid)
    with pytest.raises(core.InvalidOperation) as refused:
        _prepare(session, business, order, reason=reason)
    assert refused.value.code == code


def test_a_release_names_the_order_and_a_reason_only(session, business):
    order, _, invoice = _order(session, business, "SO-PPR-F")
    for arguments, code in (
        ({"document_id": order.id}, "prepayment_release_fields_invalid"),
        (
            {"document_id": invoice.id, "reason": "Ship it"},
            "prepayment_release_order_not_found",
        ),
    ):
        with pytest.raises(core.InvalidOperation) as refused:
            prepare_delivery_action(
                session,
                business.tenant.id,
                "prepayment_release",
                arguments,
                request_id=f"ppr-fields-{code}",
            )
        assert refused.value.code == code


def test_a_second_release_is_refused_once_one_covers_the_order(session, business):
    tenant = business.tenant.id
    order, _, _ = _order(session, business, "SO-PPR-2X")
    _confirm(
        session,
        business,
        _prepare(session, business, order),
        _person(session, tenant, "owner"),
    )
    with pytest.raises(core.InvalidOperation) as refused:
        _prepare(session, business, order, reason="Again")
    assert refused.value.code == "prepayment_release_nothing_to_release"


def test_a_release_covers_only_the_amount_it_was_given_for(session, business):
    """The gate asks again when the order's required amount exceeds the release."""
    tenant = business.tenant.id
    order, promise, _ = _order(session, business, "SO-PPR-C")
    session.add(
        PrepaymentRelease(
            id=uid("ppr"),
            tenant_id=tenant,
            document_id=order.id,
            covered_amount=Decimal("90.00"),
            currency="EUR",
            reason="Covered a smaller order",
        )
    )
    session.flush()
    assert (
        "prepayment_required"
        in fulfillment_readiness(session, tenant, promise.id).blocker_codes
    )
    # Positive control: a release for the whole amount lifts it.
    session.add(
        PrepaymentRelease(
            id=uid("ppr"),
            tenant_id=tenant,
            document_id=order.id,
            covered_amount=Decimal("100.00"),
            currency="EUR",
            reason="Covers the order",
        )
    )
    session.flush()
    assert fulfillment_readiness(session, tenant, promise.id).ship_ready


def test_another_company_sees_no_release(session, business):
    tenant = business.tenant.id
    order, _, _ = _order(session, business, "SO-PPR-T")
    other = core.create_tenant(session, "Other GmbH")
    with pytest.raises(core.NotFound):
        prepare_delivery_action(
            session,
            other.id,
            "prepayment_release",
            {"document_id": order.id, "reason": "Ship it"},
            request_id="ppr-foreign",
        )
    assert (
        session.scalars(
            select(PrepaymentRelease).where(PrepaymentRelease.tenant_id == tenant)
        ).all()
        == []
    )
