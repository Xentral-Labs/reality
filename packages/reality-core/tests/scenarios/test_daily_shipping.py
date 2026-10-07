"""Trusted local demo planning remains explicit and calendar scoped."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from reality.db.core import ShippingPlanStatement, SourceRecord
from reality.services import core, live_company
from reality.services.memberships import Principal


def setup_run(session, business, owner, monkeypatch, at):
    monkeypatch.setattr(live_company, "now", lambda: at)
    run = live_company.start(
        session,
        business.tenant.id,
        owner.id,
        request_id="daily-plan-run",
        confirmed=True,
    )["run_id"]
    mail = live_company.inject(
        session,
        business.tenant.id,
        owner.id,
        run,
        {
            "kind": "order",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "quantity": 2,
            "amount": "20",
            "subject": "Order",
            "body": "Two pieces",
        },
        request_id="daily-order",
        confirmed=True,
        at=at,
    )
    return run, mail["receipt"]["commitment_ids"][0]


def test_daily_fixture_rolls_calendar_preserves_promises_and_replays(
    session, business, scheduled_owner, monkeypatch
):
    # BUSINESS PURPOSE: The multi-day local demonstration needs a fresh authored day plan.
    # BUSINESS RULE: Exact synthetic planning choices never change customer delivery promises or silently revise existing plans.
    from scenarios.company_simulator.daily_shipping import ensure_daily_plan

    at = datetime(2026, 10, 6, 10, tzinfo=UTC)
    run, commitment = setup_run(session, business, scheduled_owner, monkeypatch, at)
    original = core.commitment_terms(session, business.tenant.id, {commitment})[
        commitment
    ].due_at
    args = {
        "principal": Principal(scheduled_owner.id),
        "confirmed": True,
        "observed_at": at,
        "completion_slots": 500,
        "collection_hour": 22,
        "site_time_zone": "Europe/Berlin",
    }
    result = ensure_daily_plan(session, business.tenant.id, run, **args)
    assert result["status"] == "created" and result["business_day"] == "2026-10-06"
    replay = ensure_daily_plan(session, business.tenant.id, run, **args)
    assert (
        replay["status"] == "existing"
        and replay["statement_id"] == result["statement_id"]
    )
    new_mail = live_company.inject(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run,
        {
            "kind": "order",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "quantity": 1,
            "amount": "10",
            "body": "Tomorrow order",
        },
        request_id="next-day-order",
        confirmed=True,
        at=at + timedelta(days=1),
    )
    tomorrow = ensure_daily_plan(
        session,
        business.tenant.id,
        run,
        **{**args, "observed_at": at + timedelta(days=1)},
    )
    assert tomorrow["business_day"] == "2026-10-07" and tomorrow["status"] == "created"
    assert (
        core.commitment_terms(session, business.tenant.id, {commitment})[
            commitment
        ].due_at
        == original
    )
    sources = list(
        session.scalars(
            select(SourceRecord).where(
                SourceRecord.tenant_id == business.tenant.id,
                SourceRecord.source_type == "synthetic_daily_shipping_capacity",
            )
        )
    )
    assert len(sources) == 2
    assert tomorrow["commitments"] == 1
    assert commitment not in json.loads(sources[1].payload)["work_mix"]
    assert (
        new_mail["receipt"]["commitment_ids"][0]
        in json.loads(sources[1].payload)["work_mix"]
    )
    assert json.loads(sources[1].payload)["completion_slots"] == 500
    assert "synthetic" in json.loads(sources[1].payload)["statement"].lower()
    assert len(session.scalars(select(ShippingPlanStatement)).all()) == 2


def test_daily_fixture_requires_confirmation_exact_owner_active_run_and_empty_safety(
    session, business, scheduled_owner, monkeypatch
):
    # BUSINESS PURPOSE: Fixture automation cannot confer owner authority on an agent token or invent work.
    # BUSINESS RULE: Unconfirmed, foreign and ended-run invocation cannot write a shipping plan; empty work remains unknown.
    from scenarios.company_simulator.daily_shipping import ensure_daily_plan

    at = datetime(2026, 10, 6, 10, tzinfo=UTC)
    run, commitment = setup_run(session, business, scheduled_owner, monkeypatch, at)
    args = {
        "principal": Principal(scheduled_owner.id),
        "confirmed": True,
        "observed_at": at,
        "completion_slots": 500,
        "collection_hour": 22,
        "site_time_zone": "UTC",
    }
    with pytest.raises(ValueError):
        ensure_daily_plan(
            session, business.tenant.id, run, **{**args, "confirmed": False}
        )
    with pytest.raises(core.NotFound):
        ensure_daily_plan(session, "foreign", run, **args)
    assert (
        ensure_daily_plan(
            session,
            business.tenant.id,
            run,
            **{**args, "observed_at": at + timedelta(days=5)},
        )["status"]
        == "inactive"
    )
    core.cancel_commitment(session, business.tenant.id, commitment, reason="Cancelled")
    assert (
        ensure_daily_plan(session, business.tenant.id, run, **args)["status"] == "empty"
    )
    assert not session.scalars(select(ShippingPlanStatement)).all()


@pytest.mark.parametrize(
    "at,day,start,cutoff",
    [
        (
            datetime(2026, 3, 28, 23, 30, tzinfo=UTC),
            "2026-03-29",
            "2026-03-28T23:00:00+00:00",
            "2026-03-29T20:00:00+00:00",
        ),
        (
            datetime(2026, 10, 24, 22, 30, tzinfo=UTC),
            "2026-10-25",
            "2026-10-24T22:00:00+00:00",
            "2026-10-25T21:00:00+00:00",
        ),
    ],
)
def test_daily_fixture_uses_company_day_across_dst(
    session, business, scheduled_owner, monkeypatch, at, day, start, cutoff
):
    # BUSINESS PURPOSE: Midnight/DST must not leave the local company with yesterday's fixture.
    # BUSINESS RULE: Calendar boundaries follow the stated company zone, not a fixed 24-hour UTC increment.
    from reality.services.company_time_zone import set_company_time_zone
    from scenarios.company_simulator.daily_shipping import ensure_daily_plan

    set_company_time_zone(session, business.tenant.id, "Europe/Berlin")
    run, _ = setup_run(session, business, scheduled_owner, monkeypatch, at)
    result = ensure_daily_plan(
        session,
        business.tenant.id,
        run,
        principal=Principal(scheduled_owner.id),
        confirmed=True,
        observed_at=at,
        completion_slots=50,
        collection_hour=22,
        site_time_zone="Europe/Berlin",
    )
    assert result["business_day"] == day
    source = session.get(
        SourceRecord, (business.tenant.id, result["capacity_source_record_id"])
    )
    value = json.loads(source.payload)
    assert value["starts_at"] == start and value["collection_cutoff_at"] == cutoff


def test_daily_fixture_preserves_existing_external_day_plan(
    session, business, scheduled_owner, monkeypatch
):
    # BUSINESS PURPOSE: A demo must not overwrite a separately reviewed shipping decision.
    # BUSINESS RULE: Any existing current day statement prevents fixture creation, even for otherwise eligible simulator work.
    from test_shipping_plan_inputs import accept, staged_plan

    from scenarios.company_simulator.daily_shipping import ensure_daily_plan

    proposal, _, _ = staged_plan(session, business)
    accept(session, business, scheduled_owner, proposal)
    at = datetime(2026, 10, 6, 10, tzinfo=UTC)
    run, _ = setup_run(session, business, scheduled_owner, monkeypatch, at)
    before = list(session.scalars(select(SourceRecord.id)))
    result = ensure_daily_plan(
        session,
        business.tenant.id,
        run,
        principal=Principal(scheduled_owner.id),
        confirmed=True,
        observed_at=at,
        completion_slots=500,
        collection_hour=22,
        site_time_zone="UTC",
    )
    assert result["status"] == "existing"
    assert list(session.scalars(select(SourceRecord.id))) == before
