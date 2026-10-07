"""Shipping reads explain full retained work, never a sampled denominator."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from test_shipping_plan_inputs import accept, payload, staged_plan

from reality.db.core import BusinessEvent, SourceRecord
from reality.services import core
from reality.services.shipments import (
    record_shipment_event,
    record_shipment_notice,
    supersede_shipment_event,
)
from reality.tools.application import create_change_proposal

OBSERVED = datetime(2026, 10, 6, 12, 30, tzinfo=UTC)


@pytest.fixture
def planned_shipping(session, business, scheduled_owner):
    proposal, value, commitment = staged_plan(session, business)
    source, _, _ = core.store_source_record(
        session,
        business.tenant.id,
        "carrier",
        "capacity_confirmation",
        "read-capacity",
        {
            "unit": "site-cohort order completion",
            "completion_slots": 2,
            "work_mix": [commitment.id],
        },
    )
    value["capacity_windows"] = payload()["capacity_windows"]
    value["capacity_windows"][0]["confirmation_source_record_id"] = source.id
    proposal = create_change_proposal(
        session, business.tenant.id, "shipping_plan_state", {"plan": value}
    )
    accept(session, business, scheduled_owner, proposal)
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "20",
        to_location_id=business.location.id,
        occurred_at=OBSERVED,
    )
    core.reserve(session, business.tenant.id, commitment.id)
    return commitment


def read(session, business, **kwargs):
    from reality.services.shipping_performance import shipping_performance

    return shipping_performance(
        session, business.tenant.id, day="2026-10-06", observed_at=OBSERVED, **kwargs
    )


def test_missing_plan_is_unknown_while_a_cancelled_known_cohort_is_zero(
    session, business, scheduled_owner
):
    # BUSINESS PURPOSE: Empty planning evidence must never suggest today's shipping is complete.
    # BUSINESS RULE: Unknown planning is distinct from zero remaining work after explicit cancellation.
    missing = read(session, business)
    assert missing["coverage"]["cohort"] == "unavailable"
    assert missing["totals"]["due"] is None
    proposal, _, commitment = staged_plan(session, business)
    accept(session, business, scheduled_owner, proposal)
    core.cancel_commitment(
        session, business.tenant.id, commitment.id, reason="Customer cancelled"
    )
    empty = read(session, business)
    assert empty["coverage"]["cohort"] == "complete"
    assert empty["totals"]["due"] == 0
    assert empty["totals"]["handed_over"] == 0
    assert empty["excluded"][0]["reason"] == "cancelled"


def test_ready_work_uses_confirmed_capacity_and_source_stated_plan_times(
    session, business, planned_shipping
):
    before_events = list(session.scalars(select(BusinessEvent.id)))
    before_sources = list(session.scalars(select(SourceRecord.id)))
    result = read(session, business)
    assert result["totals"] == {"due": 1, "handed_over": 0, "forecast": 1, "risk": 0}
    assert result["series"]["plan"][-1] == {
        "at": "2026-10-06T13:00:00+00:00",
        "count": 1,
    }
    assert result["series"]["forecast"][-1] == {
        "at": "2026-10-06T13:15:00+00:00",
        "count": 1,
    }
    assert result["sites"][0]["location_id"] == business.location.id
    assert result["sites"][0]["cutoffs"][0]["at"] == "2026-10-06T14:00:00+00:00"
    assert result["basis"]["statement_ids"]
    assert list(session.scalars(select(BusinessEvent.id))) == before_events
    assert list(session.scalars(select(SourceRecord.id))) == before_sources


def test_partial_contents_and_duplicate_events_never_multiply_completed_orders(
    session, business, planned_shipping
):
    shipment, package, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
    )
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=planned_shipping.id,
        shipment_package_id=package.id,
        occurred_at=OBSERVED.replace(hour=12, minute=0),
    )
    for _ in range(2):
        record_shipment_event(
            session,
            business.tenant.id,
            shipment.id,
            event_type="handed_over",
            reporter_type="carrier",
            occurred_at=OBSERVED.replace(minute=10),
        )
    assert read(session, business)["totals"]["handed_over"] == 0
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=planned_shipping.id,
        shipment_package_id=package.id,
        occurred_at=OBSERVED.replace(hour=12, minute=0),
    )
    complete = read(session, business)
    assert complete["totals"]["handed_over"] == 1
    assert complete["series"]["handover"][-1]["count"] == 1


def test_conflicting_effective_handover_requires_reconciliation_not_recorded_time(
    session, business, planned_shipping
):
    shipment, package, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
    )
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=planned_shipping.id,
        shipment_package_id=package.id,
        occurred_at=OBSERVED.replace(minute=0),
    )
    record_shipment_event(
        session,
        business.tenant.id,
        shipment.id,
        event_type="handed_over",
        reporter_type="carrier",
        occurred_at=OBSERVED.replace(minute=10),
    )
    conflicting = record_shipment_event(
        session,
        business.tenant.id,
        shipment.id,
        event_type="handed_over",
        reporter_type="carrier",
        occurred_at=OBSERVED.replace(minute=20),
    )
    result = read(session, business)
    assert result["coverage"]["handover"] == "partial"
    assert result["coverage"]["cohort"] == "complete"
    assert result["series"]["plan"][-1]["count"] == 1
    assert result["totals"]["forecast"] is None
    supersede_shipment_event(
        session,
        business.tenant.id,
        conflicting.id,
        reason="Incorrect carrier timestamp",
    )
    assert read(session, business)["totals"]["handed_over"] == 1


def test_missing_capacity_is_unavailable_not_zero_forecast(
    session, business, scheduled_owner
):
    proposal, _, _ = staged_plan(session, business)
    accept(session, business, scheduled_owner, proposal)
    result = read(session, business)
    assert result["totals"]["due"] == 1
    assert result["totals"]["forecast"] is None
    assert result["series"]["forecast"] is None


def test_changed_quantity_invalidates_accepted_plan_without_changing_stated_inputs(
    session, business, planned_shipping
):
    from reality.services.core import revise_commitment

    revise_commitment(
        session,
        business.tenant.id,
        planned_shipping.id,
        quantity=Decimal(3),
        note="Customer increased quantity",
    )
    result = read(session, business)
    assert result["coverage"]["cohort"] == "partial"
    assert result["totals"]["forecast"] is None
    assert any(
        row["code"] == "shipping_plan_quantity_changed" for row in result["gaps"]
    )


def test_foreign_dispatch_location_is_non_disclosing(
    session, business, planned_shipping
):
    with pytest.raises(core.NotFound):
        read(session, business, location_id="loc_foreign")


def test_a_raw_confirmation_change_during_read_is_detected_without_a_business_event(
    session, business, planned_shipping, monkeypatch
):
    from reality.services import shipping_performance as shipping

    canonical_readiness = shipping.fulfillment_readiness_batch
    changed = False

    def concurrently_changed(*args, **kwargs):
        nonlocal changed
        result = canonical_readiness(*args, **kwargs)
        if not changed:
            changed = True
            core.store_source_record(
                session,
                business.tenant.id,
                "carrier",
                "capacity_confirmation",
                "read-capacity",
                {"completion_slots": 0, "revoked": True},
            )
        return result

    monkeypatch.setattr(shipping, "fulfillment_readiness_batch", concurrently_changed)
    result = read(session, business)
    assert result["totals"]["forecast"] is None
    assert any(
        row["code"] == "observation_changed_during_read" for row in result["gaps"]
    )


def test_supporting_orders_reuse_full_totals_and_bind_cursor_to_company_and_filter(
    session, business, planned_shipping
):
    from reality.services.shipping_performance import shipping_supporting_orders

    first = shipping_supporting_orders(
        session,
        business.tenant.id,
        day="2026-10-06",
        measure="due",
        limit=1,
        observed_at=OBSERVED,
    )
    assert first["total"] == 1
    assert first["items"][0]["order_id"] == planned_shipping.document_id
    assert first["items"][0]["commitment_ids"] == [planned_shipping.id]
    assert first["items"][0]["due_at"] == "2026-10-06T14:00:00+00:00"
    assert first["has_more"] is False
    assert first["re_evaluated"] is False
    repeated = shipping_supporting_orders(
        session,
        business.tenant.id,
        day="2026-10-06",
        measure="due",
        basis_key="previous-inputs",
        observed_at=OBSERVED,
    )
    assert repeated["re_evaluated"] is True
    assert repeated["total"] == 1


def test_supporting_time_filters_use_cumulative_or_half_open_business_instants(
    session, business, planned_shipping
):
    from reality.services.shipping_performance import shipping_supporting_orders

    args = {"day": "2026-10-06", "measure": "plan", "observed_at": OBSERVED}
    before = shipping_supporting_orders(
        session, business.tenant.id, at="2026-10-06T12:59:59Z", **args
    )
    assert before["total"] == 0
    planned = shipping_supporting_orders(
        session, business.tenant.id, at="2026-10-06T13:00:00Z", **args
    )
    assert planned["total"] == 1
    excluded = shipping_supporting_orders(
        session,
        business.tenant.id,
        from_at="2026-10-06T12:00:00Z",
        until="2026-10-06T13:00:00Z",
        **args,
    )
    assert excluded["total"] == 0
    included = shipping_supporting_orders(
        session,
        business.tenant.id,
        from_at="2026-10-06T13:00:00Z",
        until="2026-10-06T14:00:00Z",
        **args,
    )
    assert included["total"] == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"limit": 101},
        {"limit": True},
        {"measure": "value_at_risk"},
        {"at": "2026-10-06T13:00:00"},
        {"at": "2026-10-07T13:00:00Z"},
        {"at": "2026-10-06T13:00:00Z", "from_at": "2026-10-06T12:00:00Z"},
        {"from_at": "2026-10-06T12:00:00Z"},
        {"after": "not-a-cursor"},
    ],
)
def test_supporting_queries_refuse_ambiguous_or_unbounded_filters(
    session, business, planned_shipping, changes
):
    from reality.services.shipping_performance import shipping_supporting_orders

    with pytest.raises(core.InvalidOperation):
        shipping_supporting_orders(
            session,
            business.tenant.id,
            day="2026-10-06",
            observed_at=OBSERVED,
            **changes,
        )


def test_confirmed_series_has_no_future_point_for_a_future_selected_day(
    session, business, planned_shipping
):
    from reality.services.shipping_performance import shipping_performance

    result = shipping_performance(
        session,
        business.tenant.id,
        day="2026-10-06",
        observed_at=datetime(2026, 10, 5, 12, 30, tzinfo=UTC),
    )
    assert result["series"]["handover"] == []


def test_a_pinned_past_day_never_claims_a_reconstructed_historical_forecast(
    session, business, planned_shipping
):
    from reality.services.shipping_performance import shipping_performance

    result = shipping_performance(
        session,
        business.tenant.id,
        day="2026-10-06",
        observed_at=datetime(2026, 10, 7, 12, 30, tzinfo=UTC),
    )
    assert result["totals"]["forecast"] is None
    assert result["series"]["forecast"] is None
    assert result["series"]["plan"][-1]["count"] == 1


def test_capacity_after_day_end_cannot_raise_shipping_by_end_of_day(
    session, business, scheduled_owner
):
    _, value, commitment = staged_plan(session, business)
    confirmation, _, _ = core.store_source_record(
        session,
        business.tenant.id,
        "carrier",
        "capacity_confirmation",
        "late-window",
        {
            "unit": "site-cohort order completion",
            "completion_slots": 2,
            "work_mix": [commitment.id],
        },
    )
    window = payload()["capacity_windows"][0]
    window.update(
        starts_at="2026-10-07T00:00:00Z",
        ends_at="2026-10-07T01:00:00Z",
        collection_cutoff_at="2026-10-07T01:00:00Z",
        confirmation_source_record_id=confirmation.id,
    )
    value["capacity_windows"] = [window]
    proposal = create_change_proposal(
        session, business.tenant.id, "shipping_plan_state", {"plan": value}
    )
    accept(session, business, scheduled_owner, proposal)
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "2",
        to_location_id=business.location.id,
        occurred_at=OBSERVED,
    )
    core.reserve(session, business.tenant.id, commitment.id)
    result = read(session, business)
    assert result["totals"]["forecast"] == 0
    assert result["series"]["forecast"][-1]["count"] == 0
    assert result["totals"]["risk"] == 1


def test_unplanned_work_is_discoverable_without_a_fabricated_dispatch_deadline(
    session, business, planned_shipping
):
    # BUSINESS PURPOSE: Accepted open work must remain findable when no dispatch plan assigns it.
    # BUSINESS RULE: Unplanned work is company-wide and has no inferred shipping date or site.
    from reality.services.shipping_performance import shipping_supporting_orders

    _, document, _, _ = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "UNPLANNED",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": "10",
                "gross_amount": "10",
            }
        ],
        "10",
    )
    result = shipping_supporting_orders(
        session,
        business.tenant.id,
        day="2026-10-06",
        measure="unplanned",
        observed_at=OBSERVED,
    )
    assert result["total"] == 1 and result["items"][0]["order_id"] == document.id
    assert result["items"][0]["due_at"] is None
    assert result["items"][0]["location_ids"] == []
    assert result["scope"] == "company_unplanned"
    assert result["totals"]["due"] == 1
    with pytest.raises(core.InvalidOperation):
        shipping_supporting_orders(
            session,
            business.tenant.id,
            day="2026-10-06",
            measure="unplanned",
            location_id=business.location.id,
            observed_at=OBSERVED,
        )


def test_unplanned_full_totals_and_every_order_survive_more_than_two_hundred_rows(
    session, business
):
    # BUSINESS PURPOSE: A display page never becomes the company's workload denominator.
    # BUSINESS RULE: Full matching totals precede bounded company/filter-bound keyset pages.
    from reality.services.shipping_performance import shipping_supporting_orders

    expected = set()
    for index in range(205):
        _, doc, _, _ = core.create_manual_order(
            session,
            business.tenant.id,
            "sales",
            f"UNPLANNED-{index}",
            business.company.id,
            business.customer.id,
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
            _commit=False,
        )
        expected.add(doc.id)
    session.flush()
    found = []
    cursor = ""
    while True:
        result = shipping_supporting_orders(
            session,
            business.tenant.id,
            day="2026-10-06",
            measure="unplanned",
            after=cursor,
            limit=100,
            observed_at=OBSERVED,
        )
        assert result["total"] == 205 and len(result["items"]) <= 100
        found.extend(row["order_id"] for row in result["items"])
        if not result["has_more"]:
            break
        cursor = result["next_after"]
    assert len(found) == 205 and set(found) == expected
    with pytest.raises(core.InvalidOperation):
        shipping_supporting_orders(
            session,
            business.tenant.id,
            day="2026-10-07",
            measure="unplanned",
            after=cursor,
            observed_at=OBSERVED,
        )


def test_batched_readiness_preserves_canonical_stock_hold_and_payment_rules(
    session, business, planned_shipping
):
    # BUSINESS PURPOSE: Enterprise observations reuse readiness instead of creating a competing rule.
    # BUSINESS RULE: Batch inputs change query shape only; scalar evidence and blockers remain exact.
    from reality.services.fulfillment_readiness import (
        fulfillment_readiness,
        fulfillment_readiness_batch,
    )

    before = fulfillment_readiness(
        session,
        business.tenant.id,
        planned_shipping.id,
        from_location_id=business.location.id,
    ).as_dict()
    assert (
        fulfillment_readiness_batch(
            session, business.tenant.id, {planned_shipping.id: business.location.id}
        )[planned_shipping.id].as_dict()
        == before
    )
    core.hold_commitment(
        session,
        business.tenant.id,
        planned_shipping.id,
        "customer_request",
        "Customer requested pause",
    )
    held = fulfillment_readiness(
        session,
        business.tenant.id,
        planned_shipping.id,
        from_location_id=business.location.id,
    ).as_dict()
    assert "commitment_hold" in [row["code"] for row in held["blockers"]]
    assert (
        fulfillment_readiness_batch(
            session, business.tenant.id, {planned_shipping.id: business.location.id}
        )[planned_shipping.id].as_dict()
        == held
    )
    with pytest.raises(core.InvalidOperation):
        fulfillment_readiness_batch(
            session, business.tenant.id, {"foreign": business.location.id}
        )


def test_batched_readiness_query_count_is_bounded_for_repeated_order_work(
    session, business, planned_shipping
):
    # BUSINESS PURPOSE: A large active cohort must not issue the same stock/policy reads per line.
    # BUSINESS RULE: Complete inputs are grouped within this one authorized snapshot, with no durable cache.
    from sqlalchemy import event

    from reality.services.fulfillment_readiness import fulfillment_readiness_batch

    ids = {planned_shipping.id: business.location.id}
    for index in range(100):
        row = core.create_commitment(
            session,
            business.tenant.id,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            business.item.id,
            business.location.id,
            "1",
            None,
            document_id=planned_shipping.document_id,
            _commit=False,
        )
        ids[row.id] = business.location.id
    session.flush()
    reads = []
    connection = session.connection()

    def record(conn, cursor, statement, parameters, context, executemany):
        reads.append(statement)

    event.listen(connection, "before_cursor_execute", record)
    try:
        result = fulfillment_readiness_batch(session, business.tenant.id, ids)
    finally:
        event.remove(connection, "before_cursor_execute", record)
    assert len(result) == 101
    assert all(
        not result[identity].ship_ready
        for identity in ids
        if identity != planned_shipping.id
    )
    assert len(reads) <= 30, len(reads)


def test_batch_preserves_prepayment_and_complete_order_policy(session, business):
    # BUSINESS PURPOSE: Grouping must not erase financial or complete-order delivery blockers.
    # BUSINESS RULE: Qualifying payment and delivery-policy branches remain canonical in the batch.
    from test_fulfillment_readiness import _prepayment_order

    from reality.services.fulfillment_readiness import (
        fulfillment_readiness,
        fulfillment_readiness_batch,
    )

    _, _, commitment = _prepayment_order(session, business)
    before = fulfillment_readiness(session, business.tenant.id, commitment.id).as_dict()
    batched = fulfillment_readiness_batch(
        session, business.tenant.id, {commitment.id: None}
    )[commitment.id].as_dict()
    assert batched == before
    assert "prepayment_required" in [row["code"] for row in batched["blockers"]]


def test_basis_preview_is_bounded_without_sampling_complete_observation_inputs():
    # BUSINESS PURPOSE: An all-day overview must not transfer an enterprise company's full evidence on every refresh.
    # BUSINESS RULE: A bounded preview labels complete sizes and leaves full evidence available through exact order drilldown.
    from reality.services.shipping_performance import _basis_preview

    full = {
        "context": {"tenant_id": "tenant_exact", "business_day": "2026-10-06"},
        "statement_ids": ["plan_exact"],
        "planning_source_record_ids": ["source_204"],
        "sources": {
            "plan_exact": {f"source_{i:03}": {"version": 1} for i in range(205)}
        },
        "quantity_revision_ids": {
            f"commitment_{i:03}": f"revision_{i:03}" for i in range(205)
        },
        "work": [{"commitment_id": f"commitment_{i:03}"} for i in range(205)],
        "readiness": {f"commitment_{i:03}": {"ship_ready": True} for i in range(205)},
        "physical_contents": {f"commitment_{i:03}": [] for i in range(205)},
        "capacities": [],
    }
    preview = _basis_preview(full)
    assert len(preview["work"]) == 50
    assert preview["planning_source_record_ids"] == ["source_204"]
    assert "source_204" in preview["sources"]["plan_exact"]
    assert sum(len(rows) for rows in preview["sources"].values()) == 50
    assert len(preview["readiness"]) == 50
    assert len(preview["quantity_revision_ids"]) == 50
    assert preview["disclosure"]["complete_counts"]["work"] == 205
    assert preview["disclosure"]["complete_counts"]["sources"] == 205
    assert preview["disclosure"]["sampled"] is True
    assert preview["context"] == full["context"]
    assert len(full["work"]) == 205 and len(full["sources"]["plan_exact"]) == 205


def test_shipping_basis_binds_exact_company_day_and_site(
    session, business, planned_shipping
):
    # BUSINESS PURPOSE: A prior observation can only be compared in its actual company and business context.
    # BUSINESS RULE: The fingerprint inputs carry exact company, resolved day, dispatch site and calendar boundaries.
    result = read(session, business)
    assert result["basis"]["context"] == {
        "tenant_id": business.tenant.id,
        "business_day": result["business_day"],
        "location_id": None,
        "time_zone": result["time_zone"],
        "day_start": result["day_start"],
        "day_end": result["day_end"],
    }


@pytest.mark.parametrize("prepayment", [False, True])
def test_narrow_snapshot_inputs_preserve_exact_scalar_readiness(
    session, business, planned_shipping, prepayment
):
    # BUSINESS PURPOSE: Fresh read-only input projections retain canonical readiness and its public representation.
    # BUSINESS RULE: Stored Decimal scale, stock, holds and prepayment evidence match the scalar reader exactly.
    from test_fulfillment_readiness import _prepayment_order

    from reality.services.fulfillment_readiness import (
        fulfillment_readiness,
        fulfillment_readiness_batch,
    )

    commitment = (
        _prepayment_order(session, business)[2] if prepayment else planned_shipping
    )
    identity = commitment.id
    core.hold_commitment(
        session,
        business.tenant.id,
        identity,
        "customer_request",
        "Retain exact hold evidence",
    )
    session.flush()
    session.expire_all()
    expected = fulfillment_readiness(session, business.tenant.id, identity).as_dict()
    session.info["operations_snapshot_consistent"] = True
    try:
        actual = fulfillment_readiness_batch(
            session, business.tenant.id, {identity: None}
        )[identity].as_dict()
    finally:
        session.info.pop("operations_snapshot_consistent", None)
    assert actual == expected
    assert "commitment_hold" in actual["blocker_codes"]
    if prepayment:
        assert "prepayment_required" in actual["blocker_codes"]


def test_snapshot_overview_preserves_evidence_without_loading_original_payloads(
    session, business, planned_shipping
):
    # BUSINESS PURPOSE: Large accepted plans stay inspectable without transferring their unused payload/preview copies into every aggregate read.
    # BUSINESS RULE: Narrow original metadata and the exact reviewed basis produce the identical complete observation; no source or decision is changed.
    from sqlalchemy import event

    from reality.db.core import ChangeProposal
    from reality.services.shipping_performance import shipping_performance

    tenant_id = business.tenant.id
    session.flush()
    session.expire_all()
    expected = read(session, business)
    source_payloads = dict(
        session.execute(
            select(SourceRecord.id, SourceRecord.payload).where(
                SourceRecord.tenant_id == tenant_id
            )
        ).all()
    )
    session.expunge_all()
    large_records = []

    def loaded(db, record):
        if isinstance(record, (SourceRecord, ChangeProposal)):
            large_records.append(type(record).__name__)

    event.listen(session, "loaded_as_persistent", loaded)
    session.info["operations_snapshot_consistent"] = True
    try:
        actual = shipping_performance(
            session, tenant_id, day="2026-10-06", observed_at=OBSERVED
        )
    finally:
        session.info.pop("operations_snapshot_consistent", None)
        event.remove(session, "loaded_as_persistent", loaded)
    assert actual == expected
    assert not large_records, large_records
    assert (
        dict(
            session.execute(
                select(SourceRecord.id, SourceRecord.payload).where(
                    SourceRecord.tenant_id == tenant_id
                )
            ).all()
        )
        == source_payloads
    )


def test_snapshot_reuses_scoped_order_and_commitment_inputs_without_changing_results(
    session, business, planned_shipping
):
    # BUSINESS PURPOSE: An enterprise observation must not reload the same original order and promise for each canonical calculation.
    # BUSINESS RULE: A single call-scoped read of each input cohort preserves exact canonical quantities, readiness, policy, evidence and fingerprint.
    import re

    from sqlalchemy import event

    session.flush()
    session.expire_all()
    expected = read(session, business)
    counts = {"commitment": 0, "document": 0}

    def counted(connection, cursor, statement, parameters, context, many):
        for name in counts:
            if re.search(r"\bFROM " + name + r"\b", statement):
                counts[name] += 1

    bind = session.get_bind()
    event.listen(bind, "before_cursor_execute", counted)
    session.info["operations_snapshot_consistent"] = True
    try:
        actual = read(session, business)
    finally:
        session.info.pop("operations_snapshot_consistent", None)
        event.remove(bind, "before_cursor_execute", counted)
    assert actual == expected
    assert counts == {"commitment": 1, "document": 1}, counts


def test_readonly_policy_reuse_never_downgrades_a_rule_from_foreign_input(
    session, business, planned_shipping
):
    # BUSINESS PURPOSE: A foreign/incomplete reusable order input must never weaken the actual company's delivery policy.
    # BUSINESS RULE: Missing scoped customer input falls back to the canonical tenant read; ordinary callers retain their original read behavior.
    from types import SimpleNamespace

    from reality.services.delivery_rules import effective_rules, state_delivery_rule

    tenant_id = business.tenant.id
    document_id = planned_shipping.document_id
    state_delivery_rule(
        session,
        tenant_id,
        "ship_complete",
        "Customer requires one shipment",
        party_id=business.customer.id,
    )
    session.expire_all()
    expected = effective_rules(session, tenant_id, [document_id])
    assert expected[document_id]["rule"] == "ship_complete"
    foreign = {
        document_id: SimpleNamespace(
            id=document_id, tenant_id="another-company", party_id=None
        )
    }
    assert (
        effective_rules(session, tenant_id, [document_id], _orders=foreign) == expected
    )
    session.info["operations_snapshot_consistent"] = True
    try:
        assert (
            effective_rules(session, tenant_id, [document_id], _orders=foreign)
            == expected
        )
    finally:
        session.info.pop("operations_snapshot_consistent", None)


@pytest.mark.parametrize("condition", ["healthy", "held", "source_gap"])
def test_overview_detail_projection_preserves_the_full_shipping_observation(
    session, business, planned_shipping, condition
):
    # BUSINESS PURPOSE: Live overview avoids building unused order details while retaining complete operational truth.
    # BUSINESS RULE: Full basis/curves/totals/terms precede exact deviation-only projection; ordinary/supporting reads stay complete.
    import json

    from reality.db.core import Document
    from reality.services.shipping_performance import _read_shipping

    if condition == "held":
        core.hold_commitment(
            session,
            business.tenant.id,
            planned_shipping.id,
            "customer_request",
            "Customer asked to pause dispatch",
        )
    elif condition == "source_gap":
        doc = session.scalar(
            select(Document).where(
                Document.tenant_id == business.tenant.id,
                Document.id == planned_shipping.document_id,
            )
        )
        original = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == business.tenant.id,
                SourceRecord.id == doc.source_record_id,
            )
        )
        changed = {
            **json.loads(original.payload),
            "note": "New original source awaits interpretation",
        }
        core.store_source_record(
            session,
            business.tenant.id,
            original.source_system,
            original.source_type,
            original.external_id,
            changed,
        )
    session.flush()
    session.expire_all()
    arguments = {"day": "2026-10-06", "observed_at": OBSERVED}
    normal = _read_shipping(session, business.tenant.id, **arguments)
    assert (
        _read_shipping(session, business.tenant.id, **arguments, _deviations_only=True)
        == normal
    )
    session.info["operations_snapshot_consistent"] = True
    try:
        full = _read_shipping(session, business.tenant.id, **arguments)
        projected = _read_shipping(
            session, business.tenant.id, **arguments, _deviations_only=True
        )
    finally:
        session.info.pop("operations_snapshot_consistent", None)
    assert projected[0] == full[0] == normal[0]
    assert projected[2] == full[2]
    assert full[0]["totals"]["due"] == 1
    assert projected[1] == [
        row for row in full[1] if row["at_risk"] or row["coverage_gaps"]
    ]
    assert len(projected[1]) == (0 if condition == "healthy" else 1)


def test_overview_projection_keeps_every_deviation_before_the_display_limit(
    session, business, scheduled_owner, monkeypatch
):
    # BUSINESS PURPOSE: A busy company's exception total remains complete even when its overview displays fifty orders.
    # BUSINESS RULE: Exact at-risk requirements, full shipping evidence and supporting pagination survive overview-only detail allocation.
    from reality.services import operations_cockpit
    from reality.services.memberships import Principal
    from reality.services.shipping_performance import (
        _read_shipping,
        shipping_supporting_orders,
    )

    _, value, original = staged_plan(session, business)
    for index in range(62):
        _, _, _, commitments = core.create_manual_order(
            session,
            business.tenant.id,
            "sales",
            f"MANY-RISKS-{index}",
            business.company.id,
            business.customer.id,
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
        )
        value["requirements"].append(
            {
                **value["requirements"][0],
                "commitment_id": commitments[0].id,
                "quantity": "1",
            }
        )
    confirmation, _, _ = core.store_source_record(
        session,
        business.tenant.id,
        "carrier",
        "capacity_confirmation",
        "many-risk-capacity",
        {
            "completion_slots": 2,
            "unit": "site-cohort order completion",
            "work_mix": [row["commitment_id"] for row in value["requirements"]],
        },
    )
    value["capacity_windows"] = payload()["capacity_windows"]
    value["capacity_windows"][0]["confirmation_source_record_id"] = confirmation.id
    accept(
        session,
        business,
        scheduled_owner,
        create_change_proposal(
            session, business.tenant.id, "shipping_plan_state", {"plan": value}
        ),
    )
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "1000",
        to_location_id=business.location.id,
        occurred_at=OBSERVED,
    )
    for requirement in value["requirements"]:
        core.reserve(
            session, business.tenant.id, requirement["commitment_id"], _commit=False
        )
    session.flush()
    session.expire_all()
    full = _read_shipping(
        session, business.tenant.id, day="2026-10-06", observed_at=OBSERVED
    )
    assert full[0]["totals"] == {"due": 63, "handed_over": 0, "forecast": 2, "risk": 61}
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    session.info["operations_snapshot_consistent"] = True
    session.info["operations_snapshot_observed_at"] = OBSERVED
    try:
        projected = _read_shipping(
            session,
            business.tenant.id,
            day="2026-10-06",
            observed_at=OBSERVED,
            _deviations_only=True,
        )
        overview = operations_cockpit.operations_cockpit(
            session, business.tenant.id, Principal(scheduled_owner.id), day="2026-10-06"
        )
        supported = shipping_supporting_orders(
            session,
            business.tenant.id,
            day="2026-10-06",
            observed_at=OBSERVED,
            limit=100,
        )
    finally:
        session.info.pop("operations_snapshot_consistent", None)
        session.info.pop("operations_snapshot_observed_at", None)
    assert projected[0] == full[0]
    assert projected[2] == full[2]
    assert len(projected[1]) == 61
    assert projected[1] == [
        row for row in full[1] if row["at_risk"] or row["coverage_gaps"]
    ]
    assert overview["deviation_total"] == 61 and overview["deviations_has_more"]
    assert len(overview["deviations"]) == 50
    assert overview["shipping"] == full[0]
    assert supported["total"] == 63 and len(supported["items"]) == 63
    assert original.id in projected[2]


def test_batched_original_source_metadata_preserves_per_statement_scope_and_errors(
    session, business, planned_shipping
):
    # BUSINESS PURPOSE: Multiple site plans reuse original source reads without weakening any exact confirmation.
    # BUSINESS RULE: Canonical results/errors remain per selected source scope; private inputs never cross company/session or excuse missing evidence.
    import json

    from reality.services import shipping_plans

    sources = list(
        session.scalars(
            select(SourceRecord).where(SourceRecord.tenant_id == business.tenant.id)
        )
    )
    original = sources[0]
    ids = {row.id for row in sources}
    session.info["operations_snapshot_consistent"] = True
    try:
        inputs = shipping_plans._source_basis_inputs(
            session, business.tenant.id, ids | {"missing-source"}
        )
        expected = shipping_plans.source_basis(session, business.tenant.id, ids)
        assert (
            shipping_plans.source_basis(
                session, business.tenant.id, ids, _inputs=inputs
            )
            == expected
        )
        for selected in ({"missing-source"}, {original.id, "missing-source"}):
            with pytest.raises(core.NotFound) as scalar:
                shipping_plans.source_basis(session, business.tenant.id, selected)
            with pytest.raises(core.NotFound) as batched:
                shipping_plans.source_basis(
                    session, business.tenant.id, selected, _inputs=inputs
                )
            assert (
                batched.value.code
                == scalar.value.code
                == "shipping_plan_reference_unavailable"
            )
        assert (
            shipping_plans.source_basis(
                session, "foreign-company", set(), _inputs=inputs
            )
            == {}
        )
        with pytest.raises(core.NotFound) as foreign:
            shipping_plans.source_basis(session, "foreign-company", ids, _inputs=inputs)
        assert foreign.value.code == "shipping_plan_reference_unavailable"
    finally:
        session.info.pop("operations_snapshot_consistent", None)
    core.store_source_record(
        session,
        business.tenant.id,
        original.source_system,
        original.source_type,
        original.external_id,
        {**json.loads(original.payload), "new_note": "A later original statement"},
    )
    session.info["operations_snapshot_consistent"] = True
    try:
        current = shipping_plans._source_basis_inputs(session, business.tenant.id, ids)
        for exact in ({original.id}, set()):
            with pytest.raises(core.InvalidOperation) as scalar:
                shipping_plans.source_basis(
                    session, business.tenant.id, {original.id}, current_required=exact
                )
            with pytest.raises(core.InvalidOperation) as batched:
                shipping_plans.source_basis(
                    session,
                    business.tenant.id,
                    {original.id},
                    current_required=exact,
                    _inputs=current,
                )
            assert (
                batched.value.code
                == scalar.value.code
                == "shipping_plan_source_unresolved"
            )
    finally:
        session.info.pop("operations_snapshot_consistent", None)
    # An old call-local input is ignored outside the read-only observation.
    with pytest.raises(core.InvalidOperation):
        shipping_plans.source_basis(
            session, business.tenant.id, {original.id}, _inputs=inputs
        )


def test_ready_overview_materializes_only_disclosed_readiness_evidence(
    session, business, scheduled_owner, monkeypatch
):
    # BUSINESS PURPOSE: Full enterprise cohorts retain exact fingerprints without allocating unused readable evidence.
    # BUSINESS RULE: Every readiness input remains fingerprinted; only fifty preview entries are rendered for an entirely ready narrow overview.
    from reality.services.fulfillment_readiness import FulfillmentReadiness
    from reality.services.shipping_performance import _read_shipping

    _, value, _ = staged_plan(session, business)
    for index in range(62):
        _, _, _, commitments = core.create_manual_order(
            session,
            business.tenant.id,
            "sales",
            f"READY-PREVIEW-{index}",
            business.company.id,
            business.customer.id,
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
        )
        value["requirements"].append(
            {
                **value["requirements"][0],
                "commitment_id": commitments[0].id,
                "quantity": "1",
            }
        )
    confirmation, _, _ = core.store_source_record(
        session,
        business.tenant.id,
        "carrier",
        "capacity_confirmation",
        "ready-preview-capacity",
        {
            "completion_slots": 1000,
            "unit": "site-cohort order completion",
            "work_mix": [row["commitment_id"] for row in value["requirements"]],
        },
    )
    value["capacity_windows"] = payload()["capacity_windows"]
    value["capacity_windows"][0]["completion_slots"] = 1000
    value["capacity_windows"][0]["confirmation_source_record_id"] = confirmation.id
    accept(
        session,
        business,
        scheduled_owner,
        create_change_proposal(
            session, business.tenant.id, "shipping_plan_state", {"plan": value}
        ),
    )
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "1000",
        to_location_id=business.location.id,
        occurred_at=OBSERVED,
    )
    for requirement in value["requirements"]:
        core.reserve(
            session, business.tenant.id, requirement["commitment_id"], _commit=False
        )
    session.flush()
    session.expire_all()
    full = _read_shipping(
        session, business.tenant.id, day="2026-10-06", observed_at=OBSERVED
    )
    assert full[0]["totals"] == {"due": 63, "handed_over": 0, "forecast": 63, "risk": 0}
    rendered = []
    original = FulfillmentReadiness.as_dict

    def counted(self, *, include_interpretation=True):
        rendered.append(self.commitment_id)
        return original(self, include_interpretation=include_interpretation)

    monkeypatch.setattr(FulfillmentReadiness, "as_dict", counted)
    session.info["operations_snapshot_consistent"] = True
    try:
        projected = _read_shipping(
            session,
            business.tenant.id,
            day="2026-10-06",
            observed_at=OBSERVED,
            _deviations_only=True,
        )
    finally:
        session.info.pop("operations_snapshot_consistent", None)
    assert projected[0] == full[0]
    assert projected[1] == []
    assert projected[0]["basis"]["disclosure"]["complete_counts"]["readiness"] == 63
    assert set(rendered) == set(projected[0]["basis"]["readiness"])
    assert len(rendered) == 50


def test_shipping_fingerprint_contains_every_canonical_readiness_field(
    session, business, planned_shipping, monkeypatch
):
    # BUSINESS PURPOSE: Compact evidence hashing must retain all canonical inputs including fields not rendered in ordinary evidence.
    # BUSINESS RULE: Versioned fingerprints contain every frozen readiness field without sampling or nested interpretation duplicates.
    import hashlib
    import json
    from dataclasses import fields

    from reality.services.fulfillment_readiness import (
        FulfillmentReadiness,
        fulfillment_readiness,
    )
    from reality.services.shipping_performance import _json_value, _read_shipping

    readiness = fulfillment_readiness(session, business.tenant.id, planned_shipping.id)
    captured = []
    original = hashlib.sha256

    def capture(value=b"", **kwargs):
        if b'"fingerprint_format": "shipping-inputs-v2"' in value:
            captured.append(json.loads(value))
        return original(value, **kwargs)

    monkeypatch.setattr(hashlib, "sha256", capture)
    snapshot, _, _ = _read_shipping(
        session, business.tenant.id, day="2026-10-06", observed_at=OBSERVED
    )
    assert len(captured) == 1
    compact = captured[0]["readiness"][planned_shipping.id]
    assert set(compact) == {field.name for field in fields(FulfillmentReadiness)}
    assert compact == _json_value(readiness.__dict__)
    assert snapshot["basis"]["readiness"][planned_shipping.id] == readiness.as_dict(
        include_interpretation=False
    )
    for field in fields(FulfillmentReadiness):
        changed = {
            **captured[0],
            "readiness": {
                planned_shipping.id: {
                    **compact,
                    field.name: ["different", compact[field.name]],
                }
            },
        }
        assert (
            original(
                json.dumps(changed, default=str, sort_keys=True).encode()
            ).hexdigest()
            != snapshot["basis_key"]
        )


@pytest.mark.parametrize("missing_package", [False, True])
def test_snapshot_physical_projection_preserves_handover_without_orm_materialization(
    session, business, planned_shipping, missing_package
):
    # BUSINESS PURPOSE: Complete handover evidence remains exact without retaining unused physical ORM state during live observation.
    # BUSINESS RULE: Linked and unresolved package evidence retain scalar/snapshot parity, including quantities, timing, coverage, source IDs and full fingerprint.
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    from reality.db.core import Movement, Shipment, ShipmentPackage
    from reality.services.shipping_performance import _read_shipping

    shipment, package, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
    )
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        str(planned_shipping.quantity),
        from_location_id=business.location.id,
        commitment_id=planned_shipping.id,
        shipment_package_id=None if missing_package else package.id,
        occurred_at=OBSERVED.replace(hour=12, minute=0),
    )
    record_shipment_event(
        session,
        business.tenant.id,
        shipment.id,
        event_type="handed_over",
        reporter_type="carrier",
        occurred_at=OBSERVED.replace(minute=10),
    )
    session.flush()
    arguments = {"day": "2026-10-06", "observed_at": OBSERVED}
    with Session(session.connection(), autoflush=False) as reader:
        expected = _read_shipping(reader, business.tenant.id, **arguments)
    loaded = []

    def retained(reader, row):
        if isinstance(row, (Movement, Shipment, ShipmentPackage)):
            loaded.append((type(row).__name__, row.id))

    with Session(session.connection(), autoflush=False) as reader:
        reader.info["operations_snapshot_consistent"] = True
        event.listen(reader, "loaded_as_persistent", retained)
        actual = _read_shipping(reader, business.tenant.id, **arguments)
    assert actual == expected
    assert actual[0]["totals"]["due"] == 1
    assert actual[0]["totals"]["handed_over"] == (0 if missing_package else 1)
    assert loaded == []


def test_shipping_fingerprint_retains_standard_v2_json_bytes(
    session, business, planned_shipping, monkeypatch
):
    # BUSINESS PURPOSE: Faster live allocation must retain every byte of the full declared fingerprint input.
    # BUSINESS RULE: The complete typed basis hashes identically to the standard v2 JSON encoder, including Decimal scale and UTC time.
    import hashlib
    import json

    standard = json.dumps
    fingerprints = []

    def compare(value, *args, **kwargs):
        encoded = standard(value, *args, **kwargs)
        if (
            isinstance(value, dict)
            and value.get("fingerprint_format") == "shipping-inputs-v2"
        ):
            reference_options = {**kwargs, "check_circular": True}
            expected = standard(value, *args, **reference_options)
            assert encoded == expected
            fingerprints.append(hashlib.sha256(expected.encode()).hexdigest())
        return encoded

    monkeypatch.setattr(json, "dumps", compare)
    result = read(session, business)
    assert fingerprints == [result["basis_key"]]


def test_full_source_metadata_keeps_latest_version_for_every_original(
    session, business
):
    # BUSINESS PURPOSE: Original order evidence remains exact when its stream receives newer versions.
    # BUSINESS RULE: Preserve all six original/current metadata fields per exact opaque stream, including up-to-date originals and distinct sibling streams.
    from reality.services import shipping_plans

    tenant = business.tenant.id
    versions = [
        core.store_source_record(
            session,
            tenant,
            "source-profile",
            "orders",
            "opaque,{NULL}",
            {"stated_version": i},
        )[0]
        for i in range(3)
    ]
    sibling = core.store_source_record(
        session,
        tenant,
        "source-profile",
        "orders",
        "other-stream",
        {"stated_version": 8},
    )[0]
    session.flush()
    records = [*versions, sibling]
    inputs = shipping_plans._source_basis_inputs(
        session, tenant, {r.id for r in records}
    )

    def metadata(row):
        return (
            row.id,
            row.source_system,
            row.source_type,
            row.external_id,
            row.version,
            row.payload_hash,
        )

    assert inputs["rows"] == {r.id: metadata(r) for r in records}
    assert inputs["latest"] == {
        ("source-profile", "orders", "opaque,{NULL}"): metadata(versions[-1]),
        ("source-profile", "orders", "other-stream"): metadata(sibling),
    }


def test_readonly_plan_review_headers_keep_every_original_binding(
    session, business, planned_shipping
):
    # BUSINESS PURPOSE: Live observations need full original identity/version bindings without transporting unused review values.
    # BUSINESS RULE: Project every same-company source and commitment binding while retaining the immutable original Action for execution and evidence.
    import json

    from reality.db.core import ChangeProposal
    from reality.services import shipping_performance as shipping
    from reality.services import shipping_plans

    _, source = shipping_plans.current_statements(session, business.tenant.id)[0]
    identity = shipping_plans.statement_action_id(source)
    original = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == business.tenant.id,
            ChangeProposal.id == identity,
        )
    )
    before = original.input
    review = json.loads(before)["reviewed"]
    projected = shipping._reviewed_shipping_inputs(
        session, business.tenant.id, {identity}
    )[identity]
    assert set(projected["sources"]) == set(review["sources"])
    assert projected["commitments"] == {
        key: {"quantity_revision_id": value.get("quantity_revision_id")}
        if value
        else value
        for key, value in review["commitments"].items()
    }
    assert original.input == before
    assert (
        shipping._reviewed_shipping_inputs(session, "foreign-company", {identity}) == {}
    )


def test_plan_review_projection_retains_complete_large_bindings_and_legacy_shapes(
    session, business, planned_shipping
):
    # BUSINESS PURPOSE: Enterprise observation carries every needed original binding while leaving large unused review payloads at their evidence boundary.
    # BUSINESS RULE: No source/commitment key is sampled, empty/null bindings keep their truth, fallback reviews retain their original values and immutable input remains untouched.
    import json

    from sqlalchemy.orm import Session

    from reality.db.core import ChangeProposal
    from reality.services import shipping_performance as shipping
    from reality.services import shipping_plans

    _, source = shipping_plans.current_statements(session, business.tenant.id)[0]
    identity = shipping_plans.statement_action_id(source)
    original = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == business.tenant.id,
            ChangeProposal.id == identity,
        )
    )
    original_input = original.input
    review = {
        "sources": {
            f"source-{i}": {"unused_original_values": "x" * 1024} for i in range(205)
        },
        "commitments": {
            f"promise-{i}": {
                "quantity_revision_id": f"revision-{i}",
                "unused_original_values": "x" * 1024,
            }
            for i in range(205)
        },
        "unused_review_values": "x" * 65536,
    }
    review["commitments"].update({"empty-binding": {}, "null-binding": None})
    try:
        original.input = json.dumps({"reviewed": review})
        session.flush()
        with Session(session.connection()) as reader:
            projected = shipping._reviewed_shipping_inputs(
                reader, business.tenant.id, {identity}
            )[identity]
            assert not any(
                isinstance(value, ChangeProposal)
                for value in reader.identity_map.values()
            )
            assert not reader.new and not reader.dirty and not reader.deleted
        assert set(projected["sources"]) == set(review["sources"])
        assert projected["commitments"] == {
            key: {"quantity_revision_id": value.get("quantity_revision_id")}
            if value
            else value
            for key, value in review["commitments"].items()
        }
        assert len(json.dumps(projected)) < len(original.input) // 8
        assert json.loads(original.input)["reviewed"] == review
        for legacy in (None, {}, "opaque-review", {"sources": [], "commitments": {}}):
            original.input = json.dumps({"reviewed": legacy})
            session.flush()
            assert (
                shipping._reviewed_shipping_inputs(
                    session, business.tenant.id, {identity}
                )[identity]
                == legacy
            )
    finally:
        original.input = original_input
        session.flush()
