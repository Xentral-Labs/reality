"""A company keeps running when the canonical catalog moves on around it.

Spec 256 FR-011, FR-015 (status payload). The observed production failure was a
company seeded when demo items carried the key as their item number; the catalog
later numbered them differently, and the running source could never be resumed.
"""

from datetime import timedelta

import pytest
from sqlalchemy import select

from reality.db.core import Item, now
from reality.db.scheduled_jobs import ScheduledJob
from reality.services import company_setup, demo_data
from reality.services.core import InvalidOperation


def live_company(session, owner, key):
    result = company_setup.create_company(
        session, owner.id, key, "Live Practice", "sandbox", "empty", confirmed=True
    )
    tenant = result["tenant_id"]
    preview = demo_data.preview(session, tenant, owner.id)
    connection = demo_data.connect(
        session, tenant, owner.id, f"{key}-c", preview["fingerprint"], confirmed=True
    )
    demo_data.control(
        session,
        tenant,
        owner.id,
        "start",
        connection["revision"],
        f"{key}-s",
        confirmed=True,
    )
    return tenant


def test_a_renumbered_catalog_does_not_strand_a_running_company(
    session, scheduled_owner
):
    tenant = live_company(session, scheduled_owner, "renumber")
    # The company keeps the item numbers it was seeded with while the canonical
    # catalog numbers them differently.
    for item in session.scalars(select(Item).where(Item.tenant_id == tenant)):
        item.sku = f"LEGACY-{item.sku}"
    session.flush()
    resolved = demo_data.preview(session, tenant, scheduled_owner.id)["references"]
    assert resolved["items"], "the company's own items must still resolve"
    state = demo_data.status(session, tenant, scheduled_owner.id)
    paused = demo_data.control(
        session,
        tenant,
        scheduled_owner.id,
        "pause",
        state["revision"],
        "renumber-p",
        confirmed=True,
    )
    resumed = demo_data.control(
        session,
        tenant,
        scheduled_owner.id,
        "resume",
        paused["revision"],
        "renumber-r",
        confirmed=True,
    )
    assert resumed["state"] == "running" and resumed["next_arrival"] is not None


def test_a_reference_the_source_uses_still_refuses(session, scheduled_owner):
    tenant = live_company(session, scheduled_owner, "missing")
    used = session.scalar(
        select(ScheduledJob).where(ScheduledJob.tenant_id == tenant)
    ).configuration["arguments"]["references"]
    item_id = next(iter(used["items"].values()))
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant, Item.id == item_id)
    )
    item.name = "Renamed beyond recognition"
    session.flush()
    state = demo_data.status(session, tenant, scheduled_owner.id)
    paused = demo_data.control(
        session,
        tenant,
        scheduled_owner.id,
        "pause",
        state["revision"],
        "missing-p",
        confirmed=True,
    )
    with pytest.raises(Exception) as refusal:
        demo_data.control(
            session,
            tenant,
            scheduled_owner.id,
            "resume",
            paused["revision"],
            "missing-r",
            confirmed=True,
        )
    assert "incompatible_references" in str(getattr(refusal.value, "code", refusal.value))


def test_a_new_connection_still_needs_the_current_catalog(session, scheduled_owner):
    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "strict",
        "Strict Practice",
        "sandbox",
        "empty",
        confirmed=True,
    )
    tenant = result["tenant_id"]
    preview = demo_data.preview(session, tenant, scheduled_owner.id)
    demo_data.connect(
        session, tenant, scheduled_owner.id, "strict-c", preview["fingerprint"], confirmed=True
    )
    for item in session.scalars(select(Item).where(Item.tenant_id == tenant)):
        item.name = f"Other {item.name}"
    session.flush()
    # A company without a connection is still judged against the whole catalog.
    demo_data._connection(session, tenant).state = "disconnected"
    session.flush()
    with pytest.raises(InvalidOperation):
        demo_data.preview(session, tenant, scheduled_owner.id, established=False)


def test_status_states_why_a_source_stopped(session, scheduled_owner):
    tenant = live_company(session, scheduled_owner, "stall")
    schedule = session.scalar(
        select(ScheduledJob).where(
            ScheduledJob.tenant_id == tenant,
            ScheduledJob.job_type == "demo.generate_orders",
        )
    )
    schedule.enabled, schedule.resume_after = False, now() + timedelta(hours=5)
    session.flush()
    state = demo_data.status(session, tenant, scheduled_owner.id)
    assert state["derived_state"] == "suspended"
    assert state["stall"]["kind"] == "suspended" and state["stall"]["automatic"] is True
    assert state["stall"]["recovery_at"] == schedule.resume_after

    schedule.enabled, schedule.resume_after = True, None
    schedule.next_run_at = now() - timedelta(hours=2)
    session.flush()
    overdue = demo_data.status(session, tenant, scheduled_owner.id)
    assert overdue["derived_state"] == "overdue"
    assert overdue["stall"]["kind"] == "overdue"

    schedule.next_run_at = now() + timedelta(seconds=30)
    session.flush()
    healthy = demo_data.status(session, tenant, scheduled_owner.id)
    assert healthy["stall"] is None and healthy["derived_state"] == "running"
