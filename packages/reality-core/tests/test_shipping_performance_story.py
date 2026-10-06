"""The independently authored two-site business oracle uses shared evidence services."""

from datetime import UTC, datetime

from test_shipping_plan_inputs import accept

from reality.services import core
from reality.services.company_time_zone import set_company_time_zone
from reality.services.shipments import record_shipment_event, record_shipment_notice
from reality.services.shipping_performance import shipping_performance
from reality.tools.application import create_change_proposal


def at(hour, minute=0):
    return datetime(2026, 10, 6, hour, minute, tzinfo=UTC)


def test_two_site_plan_partial_handover_and_confirmed_forecast_have_independent_totals(
    session, business, scheduled_owner
):
    """
    BUSINESS TEST:
    Shipping by end of day counts a split-site order once and does not count labels or partial orders.
    GIVEN:
    Four customer orders, two stated dispatch sites, one whole and one partial
    handover, one held order and confirmed completion budgets of two and one.
    WHEN:
    Their source-backed shipping performance is observed at 14:30 Berlin.
    THEN:
    One company order is handed over, one is planned by now and three can finish
    under the declared baseline. C appears at both sites but once for the company.
    BUSINESS RULES:
    shipping_performance.read.scope
    shipping_performance.read.evidence
    shipping_performance.read.result
    """
    tenant = business.tenant.id
    set_company_time_zone(session, tenant, "Europe/Berlin")
    venlo = business.location
    leipzig = core.create_location(session, tenant, "Leipzig")
    for site in (venlo, leipzig):
        core.record_movement(
            session,
            tenant,
            "receipt",
            business.item.id,
            "20",
            to_location_id=site.id,
            occurred_at=at(10),
        )

    def order(name, lines):
        return core.create_manual_order(
            session,
            tenant,
            "sales",
            name,
            business.company.id,
            business.customer.id,
            venlo.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit_price": "10",
                    "gross_amount": "10",
                }
                for _ in range(lines)
            ],
            str(lines * 10),
        )[3]

    a = order("A", 1)[0]
    b1, b2 = order("B", 2)
    c1, c2 = order("C", 2)
    d = order("D", 1)[0]
    assignments = [
        (a, venlo),
        (b1, venlo),
        (b2, venlo),
        (c1, venlo),
        (c2, leipzig),
        (d, leipzig),
    ]
    for commitment, site in assignments:
        core.reserve(session, tenant, commitment.id, location_id=site.id)
    core.hold_commitment(
        session, tenant, d.id, "customer_request", "Dispatch paused by customer"
    )

    def handover(commitment, minute):
        shipment, package, _ = record_shipment_notice(
            session,
            tenant,
            direction="outbound",
            purpose="customer_delivery",
            counterparty_id=business.customer.id,
        )
        core.record_movement(
            session,
            tenant,
            "shipment",
            business.item.id,
            "1",
            from_location_id=venlo.id,
            commitment_id=commitment.id,
            shipment_package_id=package.id,
            occurred_at=at(12),
        )
        record_shipment_event(
            session,
            tenant,
            shipment.id,
            event_type="handed_over",
            reporter_type="carrier",
            occurred_at=at(12, minute),
        )

    handover(a, 10)
    handover(b1, 20)
    record_shipment_notice(
        session,
        tenant,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
        tracking_number="D-label-only",
    )

    def requirement(commitment, planned, due):
        return {
            "commitment_id": commitment.id,
            "quantity": "1",
            "planned_handover_at": planned.isoformat(),
            "dispatch_due_at": due.isoformat(),
        }

    plans = [
        (
            venlo,
            [
                requirement(a, at(12), at(14)),
                requirement(b1, at(12), at(13, 30)),
                requirement(b2, at(13), at(13, 30)),
                requirement(c1, at(13, 30), at(14)),
            ],
            2,
        ),
        (
            leipzig,
            [requirement(c2, at(13, 30), at(14)), requirement(d, at(14), at(14))],
            1,
        ),
    ]
    for site, requirements, slots in plans:
        confirmation, _, _ = core.store_source_record(
            session,
            tenant,
            "carrier",
            "capacity_confirmation",
            site.id,
            {
                "unit": "site-cohort order completion",
                "completion_slots": slots,
                "work_mix": [row["commitment_id"] for row in requirements],
            },
        )
        plan = {
            "statement_kind": "plan",
            "dispatch_location_id": site.id,
            "business_day": "2026-10-06",
            "business_time_zone": "Europe/Berlin",
            "site_time_zone": "Europe/Amsterdam"
            if site.id == venlo.id
            else "Europe/Berlin",
            "requirements": requirements,
            "capacity_windows": [
                {
                    "starts_at": at(12, 30).isoformat(),
                    "ends_at": at(14).isoformat(),
                    "collection_cutoff_at": at(14).isoformat(),
                    "completion_slots": slots,
                    "confirmation_state": "confirmed",
                    "confirmation_source_record_id": confirmation.id,
                }
            ],
        }
        proposal = create_change_proposal(
            session, tenant, "shipping_plan_state", {"plan": plan}
        )
        accept(session, business, scheduled_owner, proposal)

    result = shipping_performance(
        session, tenant, day="2026-10-06", observed_at=at(12, 30)
    )
    assert result["totals"] == {"due": 4, "handed_over": 1, "forecast": 3, "risk": 1}
    assert result["series"]["plan"] == [
        {"at": "2026-10-05T22:00:00+00:00", "count": 0},
        {"at": at(12).isoformat(), "count": 1},
        {"at": at(13).isoformat(), "count": 2},
        {"at": at(13, 30).isoformat(), "count": 3},
        {"at": at(14).isoformat(), "count": 4},
    ]
    assert result["series"]["forecast"] == [
        {"at": at(12, 30).isoformat(), "count": 1},
        {"at": at(13, 15).isoformat(), "count": 2},
        {"at": at(14).isoformat(), "count": 3},
    ]
    sites = {row["location_id"]: row for row in result["sites"]}
    assert sites[venlo.id]["due"] == 3
    assert sites[leipzig.id]["due"] == 2
    assert sites[venlo.id]["forecast"] == 3
    assert sites[leipzig.id]["forecast"] == 1
    assert result["coverage"]["cohort"] == "complete"
