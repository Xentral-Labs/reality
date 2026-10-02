"""Spec 312: customer pickup and the time goods moved versus when it was recorded."""

import json
from datetime import timedelta

import pytest
from unified_fixtures import delivery_fixture

from reality.db.core import Movement
from reality.services import core
from reality.services.shipments import shipment_explain
from reality.tools.application import approve_and_execute_proposal, create_change_proposal


def _dispatch(session, business, fixture, quantity="2", **extra):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": fixture.commitment.id,
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
    return json.loads(executed.output)


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def test_a_customer_collects_and_says_who(session, business):
    tenant = business.tenant.id
    fixture = delivery_fixture(session, business, quantity="2")
    core.reserve(session, tenant, fixture.commitment.id)

    output = _dispatch(
        session, business, fixture, delivery_mode="pickup", collected_by="M. Müller"
    )

    detail = shipment_explain(session, tenant, output["shipment_id"])
    assert (detail["delivery_mode"], detail["collected_by"]) == ("pickup", "M. Müller")
    assert detail["packages"][0]["carrier"] is None
    session.refresh(fixture.commitment)
    assert fixture.commitment.status == "fulfilled"


def test_a_pickup_takes_no_carrier_and_is_for_customers_only(session, business):
    tenant = business.tenant.id
    fixture = delivery_fixture(session, business, quantity="4")
    core.reserve(session, tenant, fixture.commitment.id)
    _refused(
        "shipment_pickup_carrier_refused",
        lambda: _dispatch(session, business, fixture, delivery_mode="pickup", carrier="DHL"),
    )
    _refused(
        "shipment_delivery_mode_invalid",
        lambda: _dispatch(session, business, fixture, delivery_mode="drone"),
    )
    _refused(
        "shipment_collector_pickup_only",
        lambda: _dispatch(session, business, fixture, carrier="DHL", collected_by="Someone"),
    )
    from reality.services.shipments import record_shipment_notice

    _refused(
        "shipment_pickup_customer_only",
        lambda: record_shipment_notice(
            session,
            tenant,
            direction="inbound",
            purpose="supplier_delivery",
            counterparty_id=business.supplier.id,
            delivery_mode="pickup",
        ),
    )
    # Positive control: by carrier, as before, reads as carrier.
    output = _dispatch(session, business, fixture, carrier="DHL", tracking_number="T-1")
    assert shipment_explain(session, tenant, output["shipment_id"])["delivery_mode"] == "carrier"


def test_movements_carry_when_the_goods_left(session, business):
    tenant = business.tenant.id
    fixture = delivery_fixture(session, business, quantity="2")
    core.reserve(session, tenant, fixture.commitment.id)
    left = core.now() - timedelta(days=3)

    output = _dispatch(session, business, fixture, occurred_at=left.isoformat())

    (movement,) = [
        session.get(Movement, (tenant, movement_id)) for movement_id in output["movement_ids"]
    ]
    assert core.utc_datetime(movement.occurred_at) == left
    detail = shipment_explain(session, tenant, output["shipment_id"])
    assert detail["moved_at"] == left
    assert detail["confirmation_lag_seconds"] >= 3 * 24 * 3600 - 5


def test_a_future_time_is_refused_and_no_time_has_no_lag(session, business):
    tenant = business.tenant.id
    fixture = delivery_fixture(session, business, quantity="2")
    core.reserve(session, tenant, fixture.commitment.id)
    _refused(
        "shipment_occurred_at_future",
        lambda: _dispatch(
            session,
            business,
            fixture,
            occurred_at=(core.now() + timedelta(days=1)).isoformat(),
        ),
    )
    output = _dispatch(session, business, fixture)
    detail = shipment_explain(session, tenant, output["shipment_id"])
    assert (detail["moved_at"], detail["confirmation_lag_seconds"]) == (None, None)


def test_the_migration_guards_its_downgrade(postgres_database, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from reality.services.shipments import record_shipment_notice

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        # Positive control: nothing stated, so the downgrade and upgrade pass.
        command.downgrade(config, "0122_purchasing_depth")
        command.upgrade(config, "head")
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration 312")
            customer = core.create_party(session, tenant.id, "Kunde", "customer")
            record_shipment_notice(
                session,
                tenant.id,
                direction="outbound",
                purpose="customer_delivery",
                counterparty_id=customer.id,
                delivery_mode="pickup",
            )
        with pytest.raises(Exception, match="delivery mode"):
            command.downgrade(config, "0122_purchasing_depth")
    finally:
        engine.dispose()
