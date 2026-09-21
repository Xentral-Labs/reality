from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from reality.db.core import Fact, InterpretationRule, RealityGap
from reality.services.core import InvalidOperation, ingest_shopify_order
from reality.services.reality_gaps import (
    activate_rule,
    add_gap_entry,
    capture_gap,
    decide_gap,
    gap_detail,
    list_gaps,
    prepare_implementation,
    replay_rule,
    search_source_examples,
    simulate_rule,
)


def test_source_example_search_is_bounded_and_returns_safe_payload_candidates(
    session, business
):
    payload = _payload("1042", "gift")
    payload["metafields"] = {"fulfillment": {"gift_wrap": True}}
    source, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )

    result = search_source_examples(session, business.tenant.id, "1042", limit=5)

    assert len(result) == 1
    assert result[0]["source_record_id"] == source.id
    assert result[0]["external_id"] == "1042"
    assert {candidate["path"] for candidate in result[0]["candidates"]} >= {
        "note_attributes.0.name",
        "note_attributes.0.value",
    }
    assert (
        next(
            candidate
            for candidate in result[0]["candidates"]
            if candidate["path"] == "metafields.fulfillment.gift_wrap"
        )["value_type"]
        == "boolean"
    )


def _payload(order_id: str, priority: str = "express") -> dict:
    return {
        "id": order_id,
        "name": f"#{order_id}",
        "created_at": "2026-09-04T10:00:00Z",
        "currency": "EUR",
        "total_price": "15.00",
        "note_attributes": [{"name": "shipping_priority", "value": priority}],
        "line_items": [
            {
                "id": f"line-{order_id}",
                "sku": "BIKE-LIGHT",
                "name": "Bike Light",
                "quantity": 1,
                "price": "15.00",
            }
        ],
    }


def test_gap_capture_is_idempotent_tenant_scoped_and_auditable(session, business):
    gap = capture_gap(
        session,
        business.tenant.id,
        question="Which orders are express?",
        intended_use="Prioritize warehouse work",
        origin="web",
        idempotency_key="express-question",
    )
    repeated = capture_gap(
        session,
        business.tenant.id,
        question="Which orders are express?",
        intended_use="Prioritize warehouse work",
        origin="web",
        idempotency_key="express-question",
    )
    assert repeated.id == gap.id
    add_gap_entry(
        session,
        business.tenant.id,
        gap.id,
        "answer",
        {"key": "recurrence", "value": "every order"},
        expected_revision=gap.revision,
    )
    detail = gap_detail(session, business.tenant.id, gap.id)
    assert detail["gap"]["question"] == "Which orders are express?"
    assert detail["entries"][0]["payload"]["key"] == "recurrence"
    assert [row.id for row in list_gaps(session, business.tenant.id)["items"]] == [
        gap.id
    ]


def test_gap_capture_rejects_explanatory_text_as_the_queue_question(session, business):
    with pytest.raises(InvalidOperation, match="at most 100 characters"):
        capture_gap(
            session,
            business.tenant.id,
            question="Q" * 101,
            intended_use="The complete business explanation belongs here.",
            origin="mcp",
            idempotency_key="oversized-gap-question",
        )


def test_gap_register_filters_lifecycle_search_and_reports_tenant_counts(
    session, business
):
    open_gap = capture_gap(
        session,
        business.tenant.id,
        question="Which orders need cold storage?",
        intended_use="Prepare warehouse work",
        origin="chat",
        idempotency_key="cold-storage-open",
    )
    completed_gap = capture_gap(
        session,
        business.tenant.id,
        question="Which orders are gifts?",
        intended_use="Prepare gift wrapping",
        origin="chat",
        idempotency_key="gift-completed",
    )
    completed_gap.status = "implemented"
    session.commit()

    open_result = list_gaps(session, business.tenant.id, lifecycle="open")
    completed_result = list_gaps(
        session, business.tenant.id, lifecycle="completed", query="gift wrapping"
    )

    assert [row.id for row in open_result["items"]] == [open_gap.id]
    assert [row.id for row in completed_result["items"]] == [completed_gap.id]
    assert completed_result["counts"] == {"open": 1, "completed": 1, "all": 2}


def test_owner_can_prepare_simulate_activate_and_replay_safe_fact_rule(
    session, business
):
    source, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        _payload("1001"),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    gap = capture_gap(
        session,
        business.tenant.id,
        question="Which orders are express?",
        intended_use="Filter fulfillment",
        origin="mcp",
        idempotency_key="gap-1001",
    )
    decide_gap(
        session,
        business.tenant.id,
        gap.id,
        destination="fact",
        rationale="Explicit source statement",
        expected_revision=gap.revision,
        actor_user_id=None,
    )
    rule = prepare_implementation(
        session,
        business.tenant.id,
        gap.id,
        {
            "logical_name": "Shopify shipping priority",
            "source_system": "shopify",
            "source_type": "order",
            "value_path": "note_attributes.0.value",
            "predicate": "order.shipping_priority",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "enum",
            "allowed_values": ["standard", "express"],
            "normalization": ["trim", "lowercase"],
            "observed_at_mode": "source_received_at",
        },
        expected_revision=gap.revision,
    )
    preview = simulate_rule(session, business.tenant.id, rule.id, limit=100)
    assert preview["sources_considered"] == 1
    assert preview["expected_facts"] == 1
    activate_rule(session, business.tenant.id, rule.id)
    result = replay_rule(session, business.tenant.id, rule.id, source_ids=[source.id])
    assert result["facts_created"] == 1
    assert (
        replay_rule(session, business.tenant.id, rule.id, source_ids=[source.id])[
            "facts_existing"
        ]
        == 1
    )
    fact = session.scalar(select(Fact).where(Fact.interpretation_rule_id == rule.id))
    assert fact is not None and fact.value == "express"
    assert (
        session.scalar(
            select(InterpretationRule).where(InterpretationRule.id == rule.id)
        ).status
        == "active"
    )
    assert (
        session.scalar(select(RealityGap).where(RealityGap.id == gap.id)).status
        == "implemented"
    )


def test_rule_state_filter_precedes_paging_and_uses_versions_not_gap_lifecycle(
    session, business, monkeypatch
):
    from reality.services.core import create_tenant

    gaps = []
    for index, state in enumerate(["active", "draft", "disabled"]):
        gap = capture_gap(
            session,
            business.tenant.id,
            question=f"Rule {index}",
            intended_use="Filter actual rule states",
            origin="web",
            idempotency_key=f"rule-state-{index}",
        )
        gap.status = "implemented"
        gaps.append(gap)
        session.add(
            InterpretationRule(
                id=f"state-rule-{index}",
                tenant_id=business.tenant.id,
                gap_id=gap.id,
                logical_name=f"Rule {index}",
                status=state,
                source_system="shop",
                source_type="order",
                value_path="note",
                predicate="note",
            )
        )
    session.add(
        InterpretationRule(
            id="state-second-draft",
            tenant_id=business.tenant.id,
            gap_id=gaps[0].id,
            logical_name="Rule 0",
            version=2,
            status="draft",
            source_system="shop",
            source_type="order",
            value_path="note",
            predicate="note",
        )
    )
    other = create_tenant(session, "Other rule company")
    # A rule of another company pointing at this company's gap used to be written
    # here, so the filter could be shown to ignore it. Since spec 181 FR-005 the
    # inconsistent link cannot be written at all: a reference between two
    # company-scoped tables carries the company. The filter is still checked
    # below for what is genuinely its own.
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            InterpretationRule(
                id="state-foreign",
                tenant_id=other.id,
                gap_id=gaps[2].id,
                logical_name="Foreign",
                status="active",
                source_system="shop",
                source_type="order",
                value_path="note",
                predicate="note",
            )
        )
        session.flush()
    session.commit()
    active = list_gaps(session, business.tenant.id, rule_status="active", size=1)
    assert active["total"] == 1
    assert [row.id for row in active["items"]] == [gaps[0].id]
    assert active["rule_statuses"][gaps[0].id] == ["active", "draft"]
    draft = list_gaps(session, business.tenant.id, rule_status="draft", size=1, page=2)
    assert draft["total"] == 2
    assert len(draft["items"]) == 1
    disabled = list_gaps(session, business.tenant.id, rule_status="disabled")
    assert [row.id for row in disabled["items"]] == [gaps[2].id]
    assert disabled["rule_statuses"][gaps[2].id] == ["disabled"]
    with pytest.raises(InvalidOperation):
        list_gaps(session, business.tenant.id, rule_status="implemented")
    from test_http_boundary import client_for

    client = client_for(session, monkeypatch)
    response = client.get(
        f"/api/tenants/{business.tenant.id}/reality-gaps?rule_status=active&size=1"
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["rule_statuses"] == ["active", "draft"]
    assert (
        client.get(
            f"/api/tenants/{business.tenant.id}/reality-gaps?rule_status=implemented"
        ).status_code
        == 400
    )
