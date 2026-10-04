from decimal import Decimal

from test_mcp_read_contract import order

from reality.mcp.catalog import dispatch_tool
from reality.services.core import hold_commitment
from reality.services.projections import (
    FULFILLMENT_BLOCKERS,
    FULFILLMENT_QUEUE,
    derive_projection_rows,
    projection_rows,
    refresh_projection,
)
from reality.services.read_interpretation import (
    historical_fulfillment_cause,
    projection_interpretation,
)


def test_existing_fulfillment_reads_share_boundaries_without_cache_authority(
    session, business
):
    _, document, _, commitments = order(session, business)
    commitment = next(c for c in commitments if c.type == "customer_delivery")
    hold = hold_commitment(
        session, business.tenant.id, commitment.id, "manual_review", "Review"
    )
    readiness = dispatch_tool(
        session,
        business.tenant.id,
        "fulfillment_readiness",
        {"commitment_id": commitment.id},
    )
    kinds = {b["code"]: b["blocker_kind"] for b in readiness["blockers"]}
    assert kinds["commitment_hold"] == "recorded_hold"
    assert kinds["insufficient_reservation"] == "derived_readiness_condition"
    assert {"kind": "commitment_hold", "id": hold.id} in readiness["links"]
    expected = readiness["unfulfilled_cause"]
    assert expected["status"] == "unknown"
    for name in (FULFILLMENT_QUEUE, FULFILLMENT_BLOCKERS):
        fresh = derive_projection_rows(session, business.tenant.id, name)
        refresh_projection(session, business.tenant.id, projection_name=name)
        stored = projection_rows(session, business.tenant.id, name)
        assert [
            projection_interpretation(name, value) for value in fresh.values()
        ] == stored
        page = dispatch_tool(
            session, business.tenant.id, name, {"response_format": "page"}
        )
        assert page["records"] == stored
        if name == FULFILLMENT_QUEUE:
            assert stored[0]["lines"][0]["unfulfilled_cause"] == expected
        else:
            assert {b["blocker_kind"] for b in stored} == {
                "recorded_hold",
                "derived_readiness_condition",
            }
            assert all(b["identity_kind"] == "derived_condition_key" for b in stored)
    explained = dispatch_tool(
        session, business.tenant.id, "order_explain", {"order_reference": document.id}
    )
    assert explained["fulfillment"]["lines"][0]["unfulfilled_cause"] == expected
    from sqlalchemy import select

    from reality.db.core import ProjectionRow

    for payload in session.scalars(
        select(ProjectionRow.payload).where(
            ProjectionRow.tenant_id == business.tenant.id
        )
    ):
        assert "unfulfilled_cause" not in str(payload)
        assert "blocker_kind" not in str(payload)


def test_closed_cause_is_not_applicable():
    assert historical_fulfillment_cause(Decimal(0))["status"] == "not_applicable"
    assert historical_fulfillment_cause(Decimal(-1))["status"] == "not_applicable"


def test_exception_list_and_explanation_preserve_own_evidence(session, business):
    order(session, business)
    rows = dispatch_tool(session, business.tenant.id, "exceptions_list", {})
    assert rows
    for row in rows:
        scope = row["interpretation_scope"]
        assert scope["cross_condition_causality"] == "not_established_by_this_result"
        explained = dispatch_tool(
            session,
            business.tenant.id,
            "exception_explain",
            {"exception_id": row["id"]},
        )
        assert explained["interpretation_scope"] == scope
        assert explained["cause_ids"] == row["cause_ids"]
        assert explained["trace"] == row["trace"]


def test_capability_discovery_does_not_assert_external_configuration_absent(
    session, business
):
    index = dispatch_tool(session, business.tenant.id, "capability_catalog", {})
    topic = dispatch_tool(
        session,
        business.tenant.id,
        "capability_catalog",
        {"topic": index["topics"][0]["topic"]},
    )
    for result in (index, topic):
        runtime = result["external_agent_runtime"]
        assert runtime["visibility"] == "outside_reality"
        assert all(
            runtime[key] == "unknown"
            for key in ("schedule", "mission", "checkpoint", "next_run", "pause_state")
        )


def test_ready_and_completed_reads_have_consistent_cause(session, business):
    from reality.services.core import record_movement, reserve

    _, document, _, commitments = order(session, business)
    commitment = next(c for c in commitments if c.type == "customer_delivery")
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "2",
        to_location_id=business.location.id,
    )
    reserve(session, business.tenant.id, commitment.id)
    ready = dispatch_tool(
        session,
        business.tenant.id,
        "fulfillment_readiness",
        {"commitment_id": commitment.id},
    )
    assert ready["ship_ready"] is True
    assert ready["unfulfilled_cause"]["status"] == "unknown"
    queue = dispatch_tool(session, business.tenant.id, "fulfillment_queue", {})
    assert (
        queue["records"][0]["lines"][0]["unfulfilled_cause"]
        == ready["unfulfilled_cause"]
    )
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    closed = dispatch_tool(
        session,
        business.tenant.id,
        "fulfillment_readiness",
        {"commitment_id": commitment.id},
    )
    assert closed["unfulfilled_cause"]["status"] == "not_applicable"
    explained = dispatch_tool(
        session, business.tenant.id, "order_explain", {"order_reference": document.id}
    )
    assert (
        explained["fulfillment"]["lines"][0]["unfulfilled_cause"]
        == closed["unfulfilled_cause"]
    )


def test_shared_party_hold_is_one_record_for_two_conditions(session, business):
    from reality.services.core import hold_party_delivery

    first = order(session, business, "ONE")[3]
    second = order(session, business, "TWO")[3]
    commitments = [
        next(c for c in rows if c.type == "customer_delivery")
        for rows in (first, second)
    ]
    hold = hold_party_delivery(
        session, business.tenant.id, business.customer.id, "manual_review"
    )
    for commitment in commitments:
        readiness = dispatch_tool(
            session,
            business.tenant.id,
            "fulfillment_readiness",
            {"commitment_id": commitment.id},
        )
        blocker = next(
            b for b in readiness["blockers"] if b["code"] == "party_delivery_hold"
        )
        assert blocker["blocker_kind"] == "recorded_hold"
        assert blocker["links"] == [{"kind": "party_hold", "id": hold.id}]
    blockers = dispatch_tool(session, business.tenant.id, "fulfillment_blockers", {})[
        "records"
    ]
    held = [b for b in blockers if b["blocker_type"] == "party_delivery_hold"]
    assert len(held) == 2
    assert len({b["blocker_id"] for b in held}) == 2
    assert all("not counts of distinct holds" in b["notice"] for b in held)


def test_cost_exception_cache_can_be_reread_and_rebuilt(session, business, monkeypatch):
    import json

    from sqlalchemy import select

    from reality.db.core import ProjectionRow
    from reality.services import exceptions
    from reality.services.projections import EXCEPTIONS, rebuild_projections

    finding = exceptions._cost_finding(
        "missing_acquisition_cost",
        "item",
        business.item.id,
        cause_ids=(business.item.id,),
        causal_values={},
        trace={"cost_basis_state": "ready"},
    )

    def cost(db, tenant, *, previous_rows=()):
        assert all(
            isinstance(row, exceptions.OperationalException) for row in previous_rows
        )
        return [finding]

    monkeypatch.setattr(exceptions, "cost_findings", cost)
    for _ in range(2):
        rebuild_projections(session, business.tenant.id, [EXCEPTIONS], force=True)
        values = projection_rows(session, business.tenant.id, EXCEPTIONS)
        assert (
            next(row for row in values if row["id"] == finding.id)[
                "interpretation_scope"
            ]["kind"]
            == "current_condition"
        )
        payload = session.scalar(
            select(ProjectionRow.payload).where(
                ProjectionRow.tenant_id == business.tenant.id,
                ProjectionRow.record_key == finding.id,
            )
        )
        raw = json.loads(payload)
        assert "interpretation_scope" not in raw
        assert exceptions.OperationalException(**raw).id == finding.id


def test_external_visibility_preserves_restricted_grants(session, business):
    from test_capability_catalog import _manual

    from reality.mcp.principal import mcp_principal_context
    from reality.services.capability_catalog import topic_capabilities, topic_index

    with mcp_principal_context(_manual(business.tenant.id, {"capability_catalog"})):
        index = topic_index(session, business.tenant.id)
        result = topic_capabilities(
            session, business.tenant.id, index["topics"][0]["topic"]
        )
    assert result["external_agent_runtime"]["schedule"] == "unknown"
    assert all(
        not tool["callable"]
        for cap in result["capabilities"]
        for tool in cap["tools"]
        if tool["name"] != "capability_catalog"
    )
