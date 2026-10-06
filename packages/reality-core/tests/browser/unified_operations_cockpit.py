"""Spec 378: real committed business changes reach the optional cockpit."""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from live_stack import add_member, live_stack, migrate, run_browser_script
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import build_engine
from reality.db.operational_cases import CaseAdoption, OperationalCase
from reality.mcp.auth import create_mcp_access_token
from reality.services import core
from reality.services.company_time_zone import set_company_time_zone
from reality.services.memberships import Principal
from reality.services.shipments import record_shipment_event, record_shipment_notice
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def test_live_cockpit_shows_committed_hold_and_exact_case_takeover(
    postgres_database, tmp_path
):
    assert os.environ.get("PLAYWRIGHT_MODULE"), (
        "Set PLAYWRIGHT_MODULE for this browser proof."
    )
    artifacts = (
        Path(os.environ.get("JOURNEY_ARTIFACTS", str(tmp_path))) / "operations-cockpit"
    )
    artifacts.mkdir(parents=True, exist_ok=True)
    env = dict(
        migrate(postgres_database, artifacts), REALITY_OPERATIONS_COCKPIT_ENABLED="true"
    )
    engine = build_engine(postgres_database)
    try:
        with sessionmaker(engine, expire_on_commit=False)() as db:
            tenant = core.create_tenant(db, "Live cockpit proof")
            set_company_time_zone(db, tenant.id, "UTC")
            owner = add_member(
                db, tenant.id, "cockpit-owner@example.test", "Olga Operations", "owner"
            )
            company = core.create_party(db, tenant.id, "Live company", "company")
            customer = core.create_party(db, tenant.id, "Live customer", "customer")
            item = core.create_item(db, tenant.id, "LIVE-378", "Live item")
            location = core.create_location(db, tenant.id, "Live dispatch")
            instant = datetime.now(UTC)
            day_end = instant.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)
            cutoff = min(instant + timedelta(hours=1), day_end - timedelta(seconds=60))
            assert cutoff - instant > timedelta(minutes=2), (
                "Run this current-day proof outside the final two minutes of the UTC business day."
            )
            core.record_movement(
                db,
                tenant.id,
                "receipt",
                item.id,
                "10",
                to_location_id=location.id,
                occurred_at=instant - timedelta(minutes=10),
            )
            orders, commitments = [], []
            for suffix in ("A", "B", "C"):
                _, document, _, promises = core.create_manual_order(
                    db,
                    tenant.id,
                    "sales",
                    f"LIVE-{suffix}",
                    company.id,
                    customer.id,
                    location.id,
                    [
                        {
                            "item_id": item.id,
                            "quantity": "1",
                            "unit_price": "10",
                            "gross_amount": "10",
                        }
                    ],
                    "10",
                )
                orders.append(document)
                commitments.append(promises[0])
                core.reserve(db, tenant.id, promises[0].id, location_id=location.id)
            assert db.get(CaseAdoption, tenant.id) is None
            shipment, package, _ = record_shipment_notice(
                db,
                tenant.id,
                direction="outbound",
                purpose="customer_delivery",
                counterparty_id=customer.id,
            )
            core.record_movement(
                db,
                tenant.id,
                "shipment",
                item.id,
                "1",
                from_location_id=location.id,
                commitment_id=commitments[0].id,
                shipment_package_id=package.id,
                occurred_at=instant - timedelta(minutes=6),
            )
            record_shipment_event(
                db,
                tenant.id,
                shipment.id,
                event_type="handed_over",
                reporter_type="carrier",
                occurred_at=instant - timedelta(minutes=5),
            )
            confirmation, _, _ = core.store_source_record(
                db,
                tenant.id,
                "carrier",
                "capacity_confirmation",
                "live-capacity",
                {"completion_slots": 3, "unit": "site-cohort order completion"},
            )
            plan = {
                "statement_kind": "plan",
                "dispatch_location_id": location.id,
                "business_day": instant.date().isoformat(),
                "business_time_zone": "UTC",
                "site_time_zone": "UTC",
                "requirements": [
                    {
                        "commitment_id": promise.id,
                        "quantity": "1",
                        "dispatch_due_at": cutoff.isoformat(),
                        "planned_handover_at": (
                            instant - timedelta(minutes=5) if index == 0 else cutoff
                        ).isoformat(),
                    }
                    for index, promise in enumerate(commitments)
                ],
                "capacity_windows": [
                    {
                        "starts_at": instant.isoformat(),
                        "ends_at": cutoff.isoformat(),
                        "collection_cutoff_at": cutoff.isoformat(),
                        "completion_slots": 3,
                        "confirmation_state": "confirmed",
                        "confirmation_source_record_id": confirmation.id,
                    }
                ],
            }
            proposal = create_change_proposal(
                db, tenant.id, "shipping_plan_state", {"plan": plan}
            )
            approve_and_execute_proposal(
                db,
                tenant.id,
                proposal.id,
                confirming_principal=Principal(owner.id),
                confirmed=True,
            )
            create_mcp_access_token(
                db, tenant.id, "Dispatch Agent", issued_by_user_id=owner.id
            )
            case_id = db.scalar(
                select(OperationalCase.id).where(
                    OperationalCase.tenant_id == tenant.id,
                    OperationalCase.order_document_id == orders[2].id,
                )
            )
            tenant_id, commitment_id = tenant.id, commitments[2].id
    finally:
        engine.dispose()
    with live_stack(env, artifacts) as stack:
        run_browser_script(
            "operations-cockpit-live-browser.mjs",
            dict(
                stack["env"],
                UNIFIED_BASE_URL=stack["web"],
                TENANT=tenant_id,
                COMMITMENT=commitment_id,
                CASE=case_id,
                SHOTS=str(artifacts),
            ),
            artifacts,
        )
    print(f"Live cockpit committed-change/control proof: {artifacts}")
