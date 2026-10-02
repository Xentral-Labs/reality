"""Spec 306: delivery rules for a customer or an order (ship complete, no backorders)."""

import json
from datetime import UTC, datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from reality.db.core import DeliveryRule, SourceRecord
from reality.services import core
from reality.services.delivery_rules import (
    delivery_rules,
    effective_delivery_rule,
    state_delivery_rule,
)


def _order(session, business, number="SO-306", lines=(("8", None),)):
    _, document, _, commitments = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": item or business.item.id,
                "quantity": quantity,
                "unit_price": "10",
                "gross_amount": str(int(quantity) * 10),
            }
            for quantity, item in lines
        ],
        str(sum(int(quantity) * 10 for quantity, _ in lines)),
        requested_delivery_at=datetime(2026, 10, 20, tzinfo=UTC),
    )
    return document, commitments


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code


def test_without_a_statement_partial_delivery_is_allowed(session, business):
    document, _ = _order(session, business)

    rule = effective_delivery_rule(session, business.tenant.id, document.id)

    assert (rule["rule"], rule["source"]) == ("partial_allowed", "default")


def test_a_customer_rule_applies_to_its_orders_and_an_order_rule_wins(
    session, business
):
    tenant = business.tenant.id
    document, _ = _order(session, business)
    other, _ = _order(session, business, "SO-306-B")

    state_delivery_rule(
        session,
        tenant,
        "ship_complete",
        "Customer refuses partial deliveries",
        party_id=business.customer.id,
    )
    assert effective_delivery_rule(session, tenant, document.id) == {
        "rule": "ship_complete",
        "source": "customer",
        "reason": "Customer refuses partial deliveries",
        "subject_id": business.customer.id,
        "source_record_id": effective_delivery_rule(session, tenant, document.id)[
            "source_record_id"
        ],
    }

    state_delivery_rule(
        session,
        tenant,
        "partial_allowed",
        "Agreed by phone for this order",
        document_id=document.id,
    )

    assert effective_delivery_rule(session, tenant, document.id)["source"] == "order"
    assert effective_delivery_rule(session, tenant, document.id)["rule"] == (
        "partial_allowed"
    )
    # The customer's other orders still follow the customer.
    assert effective_delivery_rule(session, tenant, other.id)["rule"] == (
        "ship_complete"
    )


def test_every_statement_is_a_version_of_its_stream(session, business):
    tenant = business.tenant.id
    first = state_delivery_rule(
        session, tenant, "ship_complete", "Asked in June", party_id=business.customer.id
    )
    second = state_delivery_rule(
        session,
        tenant,
        "no_backorders",
        "Asked again in October",
        party_id=business.customer.id,
    )

    assert first.id == second.id
    (row,) = session.scalars(
        select(DeliveryRule).where(DeliveryRule.tenant_id == tenant)
    )
    versions = list(
        session.scalars(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == "internal_delivery_rule",
            )
            .order_by(SourceRecord.version)
        )
    )
    assert [json.loads(v.payload)["rule"] for v in versions] == [
        "ship_complete",
        "no_backorders",
    ]
    assert versions[1].supersedes_source_record_id == versions[0].id
    assert row.source_record_id == versions[1].id
    history = delivery_rules(session, tenant, party_id=business.customer.id)
    assert [entry["rule"] for entry in history["history"]] == [
        "no_backorders",
        "ship_complete",
    ]
    assert history["history"][1]["reason"] == "Asked in June"


def test_statements_are_refused_with_their_code(session, business):
    tenant = business.tenant.id
    document, _ = _order(session, business)
    purchase = core.create_manual_order(
        session,
        tenant,
        "purchase",
        "PO-306",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": "1",
                "gross_amount": "1",
            }
        ],
        "1",
    )[1]

    for code, call in (
        (
            "delivery_rule_subject_required",
            lambda: state_delivery_rule(session, tenant, "ship_complete", "x"),
        ),
        (
            "delivery_rule_subject_required",
            lambda: state_delivery_rule(
                session,
                tenant,
                "ship_complete",
                "x",
                party_id=business.customer.id,
                document_id=document.id,
            ),
        ),
        (
            "delivery_rule_unknown",
            lambda: state_delivery_rule(
                session, tenant, "sometimes", "x", party_id=business.customer.id
            ),
        ),
        (
            "delivery_rule_reason_required",
            lambda: state_delivery_rule(
                session, tenant, "ship_complete", "  ", party_id=business.customer.id
            ),
        ),
        (
            "delivery_rule_party_not_customer",
            lambda: state_delivery_rule(
                session, tenant, "ship_complete", "x", party_id=business.supplier.id
            ),
        ),
        (
            "delivery_rule_document_not_order",
            lambda: state_delivery_rule(
                session, tenant, "ship_complete", "x", document_id=purchase.id
            ),
        ),
    ):
        _refused(code, call)
    # Positive control: the customer and its order can be stated.
    state_delivery_rule(
        session, tenant, "ship_complete", "ok", party_id=business.customer.id
    )
    state_delivery_rule(session, tenant, "ship_complete", "ok", document_id=document.id)


def test_another_company_cannot_state_or_read(session, business):
    other = core.create_tenant(session, "Other GmbH")
    document, _ = _order(session, business)

    _refused(
        "record_not_found",
        lambda: state_delivery_rule(
            session, other.id, "ship_complete", "x", party_id=business.customer.id
        ),
    )
    with pytest.raises((core.InvalidOperation, core.NotFound)):
        effective_delivery_rule(session, other.id, document.id)


def test_the_table_refuses_what_no_statement_can_say(session, business):
    tenant = business.tenant.id
    rule = state_delivery_rule(
        session, tenant, "ship_complete", "ok", party_id=business.customer.id
    )
    for statement in (
        "UPDATE delivery_rule SET rule = 'sometimes' WHERE id = :id",
        "UPDATE delivery_rule SET reason = ' ' WHERE id = :id",
        "UPDATE delivery_rule SET party_id = NULL WHERE id = :id",
    ):
        with pytest.raises(IntegrityError), session.begin_nested():
            session.execute(text(statement), {"id": rule.id})
