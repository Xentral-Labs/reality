"""Explicit trusted-local shipping fixtures; never a worker or MCP approval mandate."""

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, cast, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from reality.db.core import Commitment, ShippingDispatchRequirement, SourceRecord, now
from reality.services import core, live_company, shipping_plans
from reality.services.business_locks import lock_delivery_state
from reality.services.company_time_zone import company_time_zone_state
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def ensure_daily_plan(
    session: Session,
    tenant_id: str,
    run_id: str,
    *,
    principal: Principal,
    confirmed: bool,
    observed_at: datetime | None = None,
    completion_slots: int,
    collection_hour: int,
    site_time_zone: str,
) -> dict:
    """Author an exact synthetic day plan under the local owner's explicit request.

    BUSINESS PURPOSE:
    Keep the authorized multi-day local demonstration supplied with daily planning
    inputs without treating recorded customer delivery promises as dispatch plans.

    BUSINESS RULE company_simulator.daily_shipping.authority:
    Require exact confirmation, the observed run owner and active retained run.
    Preserve every existing day statement. Never expose this helper to agent/worker
    transports or grant production planning authority.

    BUSINESS RULE company_simulator.daily_shipping.source:
    Select only run-linked open customer commitments. State new explicit synthetic
    day/cutoff/capacity/work-mix choices in immutable Sources and accept the exact
    proposal through shared owner-confirmation tooling. Replay never revises plans; work already owned by another current plan is excluded.
    """
    # reality-rule: company_simulator.daily_shipping.authority
    if (
        confirmed is not True
        or type(completion_slots) is not int
        or completion_slots < 0
        or type(collection_hour) is not int
        or not 1 <= collection_hour <= 23
    ):
        raise ValueError(
            "Exact local demo planning confirmation and valid capacity/cutoff required"
        )
    ZoneInfo(site_time_zone)
    live_company._owner(session, tenant_id, principal.user_id)
    _, config = live_company._run(session, tenant_id, run_id, lock=True)
    if config["owner_id"] != principal.user_id:
        raise core.NotFound("Live simulator run not found")
    instant = observed_at or now()
    if instant.tzinfo is None:
        raise ValueError("An explicit observation time zone is required")
    instant = instant.astimezone(UTC)
    if (
        not datetime.fromisoformat(config["started_at"])
        <= instant
        < datetime.fromisoformat(config["ends_at"])
    ):
        return {"status": "inactive"}
    zone_name = company_time_zone_state(session, tenant_id)["time_zone"]
    zone = ZoneInfo(zone_name)
    day = instant.astimezone(zone).date()
    location = config["location_id"]
    lock_delivery_state(session, tenant_id)
    existing = shipping_plans.current_statements(
        session, tenant_id, business_day=day, location_id=location
    )
    if existing:
        return {
            "status": "existing",
            "business_day": str(day),
            "statement_id": existing[0][0].id,
        }
    # reality-rule: company_simulator.daily_shipping.source
    payload = cast(SourceRecord.payload, JSONB)
    documents = select(payload["document_id"].astext).where(
        SourceRecord.tenant_id == tenant_id,
        SourceRecord.source_system == live_company._namespace(run_id),
        SourceRecord.source_type == "incoming",
        payload["kind"].astext == "order",
        cast(payload["released_at"].astext, DateTime(timezone=True)) <= instant,
    )
    commitments = list(
        session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id.in_(documents),
                Commitment.type == "customer_delivery",
                Commitment.location_id == location,
                Commitment.cancelled_at.is_(None),
            )
        )
    )
    terms = core.commitment_terms(session, tenant_id, {row.id for row in commitments})
    current_ids = {
        statement.id
        for statement, _ in shipping_plans.current_statements(session, tenant_id)
        if statement.statement_kind == "plan"
    }
    assigned = set(
        session.scalars(
            select(ShippingDispatchRequirement.commitment_id).where(
                ShippingDispatchRequirement.tenant_id == tenant_id,
                ShippingDispatchRequirement.statement_id.in_(current_ids),
            )
        )
    )
    selected = sorted(
        row.id
        for row in commitments
        if terms[row.id].open > 0 and row.id not in assigned
    )
    if not selected:
        return {"status": "empty", "business_day": str(day)}
    starts = datetime.combine(day, time.min, zone).astimezone(UTC)
    cutoff = datetime.combine(day, time(collection_hour), zone).astimezone(UTC)
    if instant >= cutoff:
        return {"status": "collection_ended", "business_day": str(day)}
    requirements = [
        {
            "commitment_id": identity,
            "quantity": str(terms[identity].quantity),
            "dispatch_due_at": cutoff.isoformat(),
            "planned_handover_at": cutoff.isoformat(),
        }
        for identity in selected
    ]
    assumption = {
        "statement": "Explicit synthetic local simulator daily dispatch plan and capacity. Not a real carrier confirmation or a customer delivery promise. The local owner requests the listed open, otherwise unassigned run work at today's stated collection cutoff.",
        "simulator_run_id": run_id,
        "business_day": str(day),
        "business_time_zone": zone_name,
        "dispatch_location_id": location,
        "site_time_zone": site_time_zone,
        "starts_at": starts.isoformat(),
        "ends_at": cutoff.isoformat(),
        "collection_cutoff_at": cutoff.isoformat(),
        "completion_slots": completion_slots,
        "unit": "site-cohort order completion",
        "work_mix": selected,
        "requirements": requirements,
    }
    source, _, _ = core.store_source_record(
        session,
        tenant_id,
        "local_cockpit_demo",
        "synthetic_daily_shipping_capacity",
        f"{run_id}:{day}:{location}:daily-v1",
        assumption,
    )
    plan = {
        "statement_kind": "plan",
        "dispatch_location_id": location,
        "business_day": str(day),
        "business_time_zone": zone_name,
        "site_time_zone": site_time_zone,
        "requirements": requirements,
        "capacity_windows": [
            {
                "starts_at": starts.isoformat(),
                "ends_at": cutoff.isoformat(),
                "collection_cutoff_at": cutoff.isoformat(),
                "completion_slots": completion_slots,
                "confirmation_state": "confirmed",
                "confirmation_source_record_id": source.id,
            }
        ],
    }
    proposal = create_change_proposal(
        session, tenant_id, "shipping_plan_state", {"plan": plan}
    )
    accepted = approve_and_execute_proposal(
        session,
        tenant_id,
        proposal.id,
        confirming_principal=principal,
        confirmed=True,
        settling_channel="cli",
    )
    statement = shipping_plans.current_statements(
        session, tenant_id, business_day=day, location_id=location
    )[0][0]
    return {
        "status": "created",
        "business_day": str(day),
        "statement_id": statement.id,
        "proposal_id": accepted.id,
        "capacity_source_record_id": source.id,
        "commitments": len(selected),
        "completion_slots": completion_slots,
    }
