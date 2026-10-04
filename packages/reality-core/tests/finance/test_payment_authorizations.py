"""Spec 336: payment authorizations and captures, and an expired one left uncovered."""

import json
from datetime import timedelta

import pytest
from intake_review_support import reviewed_manual_order

from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.payment_authorizations import authorizations
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def _order(session, business, number="SO-336", amount="100"):
    _, _, _, (promise,) = reviewed_manual_order(
        session,
        business.tenant.id,
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
                "gross_amount": amount,
            }
        ],
        amount,
    )
    return core._tenant_record(
        session, core.Document, business.tenant.id, promise.document_id
    ), promise


def _confirm(session, tenant, tool, values):
    proposal = create_change_proposal(session, tenant, tool, values, actor_type="human")
    return json.loads(
        approve_and_execute_proposal(
            session, tenant, proposal.id, confirmed=True
        ).output
    )


def _authorize(session, tenant, order, amount="100", days=7, reference="AUTH-1"):
    at = core.now() - timedelta(days=10)
    return _confirm(
        session,
        tenant,
        "finance.payment.authorization.record",
        {
            "order_document_id": order.id,
            "amount": amount,
            "currency": "EUR",
            "authorized_at": at.isoformat(),
            "valid_until": (at + timedelta(days=days)).isoformat(),
            "reference": reference,
        },
    )


def _capture(session, tenant, authorization, amount, after_days=1):
    return _confirm(
        session,
        tenant,
        "finance.payment.capture.record",
        {
            "authorization_id": authorization["id"],
            "amount": amount,
            "captured_at": (
                core.utc_datetime(authorization["authorized_at"])
                + timedelta(days=after_days)
            ).isoformat(),
            "reference": "CAP-1",
        },
    )


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def _expired(session, tenant):
    return {
        row.record_id: row
        for row in operational_exceptions(session, tenant)
        if row.class_id == "payment_authorization_expired"
    }


def test_authorization_and_capture_are_separate_records(session, business):
    tenant = business.tenant.id
    order, _ = _order(session, business)
    authorization = _authorize(session, tenant, order, days=30)
    assert (authorization["captured"], authorization["remaining"]) == ("0", "100")

    captured = _capture(session, tenant, authorization, "60")

    assert (captured["captured"], captured["remaining"], captured["state"]) == (
        "60",
        "40",
        "live",
    )
    (row,) = authorizations(session, tenant, order_document_id=order.id)
    assert (row["amount"], row["captured"], row["remaining"]) == ("100", "60", "40")
    assert [capture["amount"] for capture in captured["captures"]] == ["60"]


def test_what_cannot_be_authorized_or_captured_is_refused(session, business):
    tenant = business.tenant.id
    order, _ = _order(session, business)
    invoice = core.create_document(
        session, tenant, "sales_invoice", "RE-336", business.customer.id, "100"
    )
    base = {
        "order_document_id": order.id,
        "amount": "100",
        "currency": "EUR",
        "authorized_at": "2026-09-01T10:00:00+00:00",
        "valid_until": "2026-09-08T10:00:00+00:00",
        "reference": "AUTH-9",
    }
    tool = "finance.payment.authorization.record"
    for change, code in (
        ({"order_document_id": invoice.id}, "payment_authorization_order_invalid"),
        ({"currency": "USD"}, "payment_authorization_currency_mismatch"),
        (
            {"valid_until": "2026-09-01T09:00:00+00:00"},
            "payment_authorization_expiry_invalid",
        ),
        ({"amount": "0"}, "payment_authorization_amount_invalid"),
    ):
        _refused(
            code,
            lambda change=change: _confirm(session, tenant, tool, {**base, **change}),
        )
    # Positive control: the stated authorization is recorded, once.
    authorization = _confirm(session, tenant, tool, base)
    _refused(
        "payment_authorization_duplicate", lambda: _confirm(session, tenant, tool, base)
    )
    capture = "finance.payment.capture.record"
    for values, code in (
        (
            {"amount": "101", "captured_at": "2026-09-02T10:00:00+00:00"},
            "payment_capture_exceeds_authorization",
        ),
        (
            {"amount": "10", "captured_at": "2026-09-09T10:00:00+00:00"},
            "payment_capture_after_expiry",
        ),
        (
            {"amount": "10", "captured_at": "2026-08-31T10:00:00+00:00"},
            "payment_capture_before_authorization",
        ),
    ):
        _refused(
            code,
            lambda values=values: _confirm(
                session,
                tenant,
                capture,
                {"authorization_id": authorization["id"], **values},
            ),
        )
    assert (
        _confirm(
            session,
            tenant,
            capture,
            {
                "authorization_id": authorization["id"],
                "amount": "100",
                "captured_at": "2026-09-02T10:00:00+00:00",
            },
        )["state"]
        == "captured"
    )


def test_an_expired_authorization_leaves_the_rest_uncovered_until_authorized_again(
    session, business
):
    tenant = business.tenant.id
    order, _ = _order(session, business)
    authorization = _authorize(session, tenant, order, days=7)
    _capture(session, tenant, authorization, "60")

    finding = _expired(session, tenant)[order.id]
    assert finding.causal_values["uncovered_amount"] == 40
    assert finding.causal_values["captured_amount"] == 60

    _confirm(
        session,
        tenant,
        "finance.payment.authorization.record",
        {
            "order_document_id": order.id,
            "amount": "40",
            "currency": "EUR",
            "authorized_at": core.now().isoformat(),
            "valid_until": (core.now() + timedelta(days=7)).isoformat(),
            "reference": "AUTH-2",
        },
    )
    assert order.id not in _expired(session, tenant)


def test_nothing_left_to_ship_is_not_uncovered(session, business):
    tenant = business.tenant.id
    order, promise = _order(session, business, "SO-336-B")
    authorization = _authorize(session, tenant, order, days=7)
    _capture(session, tenant, authorization, "60")
    assert order.id in _expired(session, tenant)

    core.cancel_commitment(session, tenant, promise.id, reason="Rest not wanted")

    assert order.id not in _expired(session, tenant)
    # Positive control: a live authorization is never reported.
    live, _ = _order(session, business, "SO-336-C")
    _authorize(session, tenant, live, days=30, reference="AUTH-L")
    assert live.id not in _expired(session, tenant)


def test_another_company_sees_no_authorization(session, business):
    tenant = business.tenant.id
    order, _ = _order(session, business)
    _authorize(session, tenant, order, days=7)
    other = core.create_tenant(session, "Other GmbH")

    assert order.id in _expired(session, tenant)
    assert authorizations(session, other.id) == []
    assert not _expired(session, other.id)
