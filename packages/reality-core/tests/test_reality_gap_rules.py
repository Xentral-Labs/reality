from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from reality.db.core import Fact, RuleInterpretationOutcome, SourceRecord, now, uid
from reality.services.core import InvalidOperation, ingest_shopify_order
from reality.services.reality_gaps import (
    activate_rule,
    capture_gap,
    decide_gap,
    gap_detail,
    prepare_implementation,
    replay_rule,
    simulate_rule,
)

FIXTURES = Path(__file__).parents[1] / "fixtures"


def _payload(order_id: str, *, total: str = "1500.00", paid: bool = False) -> dict:
    return {
        "id": order_id,
        "name": f"#{order_id}",
        "created_at": "2026-09-04T10:00:00+02:00",
        "currency": "EUR",
        "total_price": total,
        "financial_status": "paid" if paid else "pending",
        "line_items": [
            {
                "id": f"line-{order_id}",
                "sku": "BIKE-LIGHT",
                "name": "Bike Light",
                "quantity": 1,
                "price": total,
                "properties": {"engraving": "yes"},
            }
        ],
    }


def _prepared_rule(session, business, draft: dict):
    gap = capture_gap(
        session,
        business.tenant.id,
        question=f"How should {draft['logical_name']} be interpreted?",
        intended_use="Test a reviewed ERP condition",
        origin="web",
        idempotency_key=draft["logical_name"],
    )
    decide_gap(
        session,
        business.tenant.id,
        gap.id,
        destination="fact",
        rationale="Explicit source-supported value",
        expected_revision=gap.revision,
        actor_user_id=None,
    )
    return prepare_implementation(
        session,
        business.tenant.id,
        gap.id,
        draft,
        expected_revision=gap.revision,
    )


def test_shared_shopify_gift_wrap_fixtures_match_simulation_and_replay(session, business):
    matching_payload = json.loads(
        (FIXTURES / "shopify_gift_wrap_example.json").read_text(encoding="utf-8")
    )
    skipped_payload = json.loads(
        (FIXTURES / "shopify_gift_wrap_followup.json").read_text(encoding="utf-8")
    )
    matching, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        matching_payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    skipped, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        skipped_payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "Gift wrap requested",
            "source_system": "shopify",
            "source_type": "order",
            "conditions": [
                {
                    "path": "metafields.fulfillment.gift_wrap",
                    "operator": "equals",
                    "value_type": "boolean",
                    "operand": True,
                }
            ],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": "order.gift_wrap_requested",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "boolean",
            "observed_at_mode": "source_received_at",
        },
    )

    preview = simulate_rule(session, business.tenant.id, rule.id)
    assert preview["expected_facts"] == 1
    assert preview["not_applicable"] == 1
    activate_rule(session, business.tenant.id, rule.id)
    result = replay_rule(
        session,
        business.tenant.id,
        rule.id,
        source_ids=[matching.id, skipped.id],
    )
    assert result["facts_created"] == 1
    assert result["not_applicable"] == 1


def test_all_conditions_create_constant_fact_or_normal_not_applicable(session, business):
    matching, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        _payload("conditional-match"),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    skipped, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        _payload("conditional-skip", total="25.00", paid=True),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "High value unpaid order",
            "source_system": "shopify",
            "source_type": "order",
            "conditions_mode": "all",
            "conditions": [
                {
                    "path": "total_price",
                    "operator": "greater_or_equal",
                    "value_type": "decimal",
                    "operand": "1000",
                },
                {
                    "path": "financial_status",
                    "operator": "not_in",
                    "value_type": "string",
                    "operand": ["paid", "authorized"],
                },
            ],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": "order.requires_manual_review",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "boolean",
            "observed_at_mode": "source_received_at",
        },
    )

    preview = simulate_rule(session, business.tenant.id, rule.id)
    assert preview["expected_facts"] == 1
    assert preview["not_applicable"] == 1

    activate_rule(session, business.tenant.id, rule.id)
    result = replay_rule(
        session,
        business.tenant.id,
        rule.id,
        source_ids=[matching.id, skipped.id],
    )
    assert result["facts_created"] == 1
    assert result["not_applicable"] == 1
    facts = list(
        session.scalars(select(Fact).where(Fact.interpretation_rule_id == rule.id))
    )
    assert [(fact.source_record_id, fact.value) for fact in facts] == [
        (matching.id, "true")
    ]


def test_three_conditions_use_all_of_semantics_in_simulation_and_replay(
    session, business
):
    payloads = [
        {**_payload("all-three-match"), "risk_score": 7},
        {**_payload("first-condition-misses", total="999.00"), "risk_score": 7},
        {**_payload("middle-condition-misses", paid=True), "risk_score": 7},
        _payload("last-condition-is-missing"),
        {**_payload("last-condition-has-wrong-type"), "risk_score": "high"},
    ]
    sources = [
        ingest_shopify_order(
            session,
            business.tenant.id,
            payload,
            business.company.id,
            business.customer.id,
            business.location.id,
        )[0]
        for payload in payloads
    ]
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "High value unpaid risky order",
            "source_system": "shopify",
            "source_type": "order",
            "conditions_mode": "all",
            "conditions": [
                {
                    "path": "total_price",
                    "operator": "greater_or_equal",
                    "value_type": "decimal",
                    "operand": "1000",
                },
                {
                    "path": "financial_status",
                    "operator": "not_in",
                    "value_type": "string",
                    "operand": ["paid", "authorized"],
                },
                {
                    "path": "risk_score",
                    "operator": "equals",
                    "value_type": "integer",
                    "operand": 7,
                },
            ],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": "order.requires_risk_review",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "boolean",
            "observed_at_mode": "source_received_at",
        },
    )

    preview = simulate_rule(session, business.tenant.id, rule.id)
    assert preview["expected_facts"] == 1
    assert preview["not_applicable"] == 2
    assert preview["invalid_values"] == 2

    activate_rule(session, business.tenant.id, rule.id)
    result = replay_rule(
        session,
        business.tenant.id,
        rule.id,
        source_ids=[source.id for source in sources],
    )
    assert result["facts_created"] == 1
    assert result["not_applicable"] == 2
    assert result["failed"] == 2
    facts = list(
        session.scalars(select(Fact).where(Fact.interpretation_rule_id == rule.id))
    )
    assert [fact.source_record_id for fact in facts] == [sources[0].id]
    outcomes = {
        outcome.source_record_id: outcome.status
        for outcome in session.scalars(
            select(RuleInterpretationOutcome).where(
                RuleInterpretationOutcome.rule_id == rule.id
            )
        )
    }
    assert outcomes == {
        sources[0].id: "fact_created",
        sources[1].id: "not_applicable",
        sources[2].id: "not_applicable",
        sources[3].id: "invalid_value",
        sources[4].id: "invalid_value",
    }


def test_nested_all_any_groups_preserve_reviewed_boolean_semantics(session, business):
    payloads = [
        {**_payload("b2b-high-value"), "customer_kind": "b2b", "overdue": False},
        {
            **_payload("b2b-overdue", total="25.00"),
            "customer_kind": "b2b",
            "overdue": True,
        },
        {**_payload("b2b-neither", total="25.00"), "customer_kind": "b2b", "overdue": False},
        {**_payload("b2c-high-value"), "customer_kind": "b2c", "overdue": False},
        {**_payload("b2b-high-value-overdue-missing"), "customer_kind": "b2b"},
        {
            **_payload("b2b-low-value-overdue-missing", total="25.00"),
            "customer_kind": "b2b",
        },
    ]
    sources = [
        ingest_shopify_order(
            session,
            business.tenant.id,
            payload,
            business.company.id,
            business.customer.id,
            business.location.id,
        )[0]
        for payload in payloads
    ]
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "B2B high value or overdue order",
            "source_system": "shopify",
            "source_type": "order",
            "conditions_mode": "all",
            "conditions": [
                {
                    "path": "customer_kind",
                    "operator": "equals",
                    "value_type": "string",
                    "operand": "b2b",
                },
                {
                    "mode": "any",
                    "conditions": [
                        {
                            "path": "overdue",
                            "operator": "equals",
                            "value_type": "boolean",
                            "operand": True,
                        },
                        {
                            "path": "total_price",
                            "operator": "greater_than",
                            "value_type": "decimal",
                            "operand": "1000",
                        },
                    ],
                },
            ],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": "order.requires_attention",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "boolean",
            "observed_at_mode": "source_received_at",
        },
    )

    preview = simulate_rule(session, business.tenant.id, rule.id)
    assert preview["expected_facts"] == 3
    assert preview["not_applicable"] == 2
    assert preview["invalid_values"] == 1
    activate_rule(session, business.tenant.id, rule.id)
    result = replay_rule(
        session,
        business.tenant.id,
        rule.id,
        source_ids=[source.id for source in sources],
    )
    assert result["facts_created"] == 3
    assert result["not_applicable"] == 2
    assert result["failed"] == 1
    assert {
        fact.source_record_id
        for fact in session.scalars(
            select(Fact).where(Fact.interpretation_rule_id == rule.id)
        )
    } == {sources[0].id, sources[1].id, sources[4].id}


@pytest.mark.parametrize(
    ("conditions_mode", "conditions", "message"),
    [
        ("some", [], "mode"),
        ("any", [], "empty"),
        ("all", [{"mode": "any", "conditions": []}], "empty"),
        (
            "all",
            [
                {
                    "mode": "all",
                    "conditions": [
                        {
                            "mode": "any",
                            "conditions": [
                                {
                                    "mode": "all",
                                    "conditions": [
                                        {
                                            "path": "id",
                                            "operator": "exists",
                                            "value_type": "string",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
            "depth",
        ),
    ],
)
def test_condition_group_bounds_are_rejected_before_storage(
    session, business, conditions_mode, conditions, message
):
    with pytest.raises(InvalidOperation, match=message):
        _prepared_rule(
            session,
            business,
            {
                "logical_name": f"Invalid group {message}",
                "source_system": "shopify",
                "source_type": "order",
                "conditions_mode": conditions_mode,
                "conditions": conditions,
                "output_mode": "constant",
                "constant_value": True,
                "predicate": "order.invalid_group",
                "subject_type": "commitment",
                "subject_resolver": "source_document_commitments",
                "value_type": "boolean",
                "observed_at_mode": "source_received_at",
            },
        )


def test_source_path_observation_time_is_timezone_aware_and_normalized(session, business):
    source, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        _payload("effective-time"),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "Order total at creation",
            "source_system": "shopify",
            "source_type": "order",
            "conditions": [],
            "output_mode": "source_path",
            "output_path": "total_price",
            "predicate": "order.source_total",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "decimal",
            "observed_at_mode": "source_path",
            "observed_at_path": "created_at",
        },
    )
    activate_rule(session, business.tenant.id, rule.id)
    replay_rule(session, business.tenant.id, rule.id, source_ids=[source.id])

    fact = session.scalar(select(Fact).where(Fact.interpretation_rule_id == rule.id))
    assert fact is not None
    assert fact.observed_at == datetime(2026, 9, 4, 8, 0, tzinfo=UTC)


def test_line_iteration_resolves_document_line_and_keeps_per_element_outcomes(
    session, business
):
    source, _, lines, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        _payload("line-rule"),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "Engraved order line",
            "source_system": "shopify",
            "source_type": "order",
            "iteration_path": "line_items",
            "source_line_id_path": "id",
            "conditions": [
                {
                    "path": "properties.engraving",
                    "scope": "element",
                    "operator": "equals",
                    "value_type": "string",
                    "operand": "yes",
                }
            ],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": "order_line.engraving_requested",
            "subject_type": "document_line",
            "subject_resolver": "source_document_lines",
            "value_type": "boolean",
            "observed_at_mode": "source_received_at",
        },
    )
    activate_rule(session, business.tenant.id, rule.id)
    result = replay_rule(session, business.tenant.id, rule.id, source_ids=[source.id])

    assert result["facts_created"] == 1
    fact = session.scalar(select(Fact).where(Fact.interpretation_rule_id == rule.id))
    assert fact is not None
    assert (fact.subject_type, fact.subject_id) == ("document_line", lines[0].id)
    outcome = session.scalar(
        select(RuleInterpretationOutcome).where(
            RuleInterpretationOutcome.rule_id == rule.id
        )
    )
    assert outcome is not None
    assert outcome.element_key == "0:line-line-rule"


def test_competing_active_rules_report_conflict_without_silent_precedence(
    session, business
):
    source, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        _payload("conflicting-rules"),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    base = {
        "source_system": "shopify",
        "source_type": "order",
        "conditions": [],
        "output_mode": "constant",
        "predicate": "order.requires_manual_review",
        "subject_type": "commitment",
        "subject_resolver": "source_document_commitments",
        "value_type": "boolean",
        "observed_at_mode": "source_path",
        "observed_at_path": "created_at",
    }
    positive = _prepared_rule(
        session,
        business,
        {**base, "logical_name": "Review positive", "constant_value": True},
    )
    negative = _prepared_rule(
        session,
        business,
        {**base, "logical_name": "Review negative", "constant_value": False},
    )
    activate_rule(session, business.tenant.id, positive.id)
    replay_rule(session, business.tenant.id, positive.id, source_ids=[source.id])
    activate_rule(session, business.tenant.id, negative.id)

    preview = simulate_rule(session, business.tenant.id, negative.id)
    assert preview["conflicts"] == 1
    result = replay_rule(session, business.tenant.id, negative.id, source_ids=[source.id])
    assert result["conflicts"] == 1
    assert session.scalar(
        select(Fact).where(Fact.interpretation_rule_id == negative.id)
    ) is None


def test_replay_returns_scope_bound_cursor_and_resumes_without_duplicates(
    session, business
):
    sources = []
    for number in range(3):
        source, _, _, _ = ingest_shopify_order(
            session,
            business.tenant.id,
            _payload(f"replay-{number}"),
            business.company.id,
            business.customer.id,
            business.location.id,
        )
        sources.append(source)
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "Replay all totals",
            "source_system": "shopify",
            "source_type": "order",
            "conditions": [],
            "output_mode": "source_path",
            "output_path": "total_price",
            "predicate": "order.source_total",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "decimal",
            "observed_at_mode": "source_received_at",
        },
    )
    activate_rule(session, business.tenant.id, rule.id)

    first = replay_rule(
        session,
        business.tenant.id,
        rule.id,
        source_ids=[source.id for source in sources],
        limit=2,
    )
    assert first["facts_created"] == 2
    assert first["complete"] is False
    assert first["next_cursor"]
    second = replay_rule(
        session,
        business.tenant.id,
        rule.id,
        source_ids=[source.id for source in sources],
        limit=2,
        cursor=first["next_cursor"],
    )
    assert second["facts_created"] == 1
    assert second["complete"] is True
    assert second["next_cursor"] is None
    assert second["cumulative"]["facts_created"] == 3
    assert len(
        list(session.scalars(select(Fact).where(Fact.interpretation_rule_id == rule.id)))
    ) == 3


@pytest.mark.parametrize(
    ("operator", "path", "value_type", "operand"),
    [
        ("equals", "financial_status", "string", "pending"),
        ("not_equals", "financial_status", "string", "paid"),
        ("in", "financial_status", "string", ["pending", "authorized"]),
        ("not_in", "financial_status", "string", ["paid", "authorized"]),
        ("exists", "financial_status", "string", None),
        ("not_exists", "cancelled_at", "string", None),
        ("greater_than", "total_price", "decimal", "100"),
        ("greater_or_equal", "total_price", "decimal", "1500"),
        ("less_than", "total_price", "decimal", "2000"),
        ("less_or_equal", "total_price", "decimal", "1500"),
    ],
)
def test_closed_condition_operator_matrix(
    session, business, operator, path, value_type, operand
):
    ingest_shopify_order(
        session,
        business.tenant.id,
        _payload(f"operator-{operator}"),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    condition = {"path": path, "operator": operator, "value_type": value_type}
    if operand is not None:
        condition["operand"] = operand
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": f"Operator {operator}",
            "source_system": "shopify",
            "source_type": "order",
            "conditions": [condition],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": f"order.operator_{operator}",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "boolean",
            "observed_at_mode": "source_received_at",
        },
    )
    assert simulate_rule(session, business.tenant.id, rule.id)["expected_facts"] == 1


def test_unsupported_condition_is_rejected_before_rule_storage(session, business):
    with pytest.raises(InvalidOperation, match="condition"):
        _prepared_rule(
            session,
            business,
            {
                "logical_name": "Unsafe condition",
                "source_system": "shopify",
                "source_type": "order",
                "conditions": [
                    {
                        "path": "total_price",
                        "operator": "execute_expression",
                        "value_type": "decimal",
                        "operand": "1000",
                    }
                ],
                "output_mode": "constant",
                "constant_value": True,
                "predicate": "order.unsafe",
                "subject_type": "commitment",
                "subject_resolver": "source_document_commitments",
                "value_type": "boolean",
                "observed_at_mode": "source_received_at",
            },
        )


def test_rule_rejects_more_than_twenty_conditions(session, business):
    with pytest.raises(InvalidOperation, match="20"):
        _prepared_rule(
            session,
            business,
            {
                "logical_name": "Too many conditions",
                "source_system": "shopify",
                "source_type": "order",
                "conditions": [
                    {
                        "path": "financial_status",
                        "operator": "exists",
                        "value_type": "string",
                    }
                    for _ in range(21)
                ],
                "output_mode": "constant",
                "constant_value": True,
                "predicate": "order.too_many_conditions",
                "subject_type": "commitment",
                "subject_resolver": "source_document_commitments",
                "value_type": "boolean",
                "observed_at_mode": "source_received_at",
            },
        )


def test_line_iteration_over_five_hundred_elements_fails_closed(session, business):
    payload = {"line_items": [{"id": str(index)} for index in range(501)]}
    source = SourceRecord(
        id=uid("src"),
        tenant_id=business.tenant.id,
        source_system="shopify",
        source_type="order",
        external_id="oversized-line-list",
        payload=json.dumps(payload),
        payload_hash="0" * 64,
        version=1,
        received_at=now(),
    )
    session.add(source)
    session.commit()
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "Bounded line iteration",
            "source_system": "shopify",
            "source_type": "order",
            "iteration_path": "line_items",
            "source_line_id_path": "id",
            "conditions": [],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": "order_line.bounded",
            "subject_type": "document_line",
            "subject_resolver": "source_document_lines",
            "value_type": "boolean",
            "observed_at_mode": "source_received_at",
        },
    )

    preview = simulate_rule(session, business.tenant.id, rule.id)
    assert preview["invalid_values"] == 1


def test_invalid_effective_time_creates_failure_outcome_and_no_fact(session, business):
    payload = _payload("naive-time")
    payload["created_at"] = "2026-09-04T10:00:00"
    source, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "Reject naive effective time",
            "source_system": "shopify",
            "source_type": "order",
            "conditions": [],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": "order.effective_time_test",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "boolean",
            "observed_at_mode": "source_path",
            "observed_at_path": "created_at",
        },
    )
    activate_rule(session, business.tenant.id, rule.id)
    result = replay_rule(session, business.tenant.id, rule.id, source_ids=[source.id])

    assert result["failed"] == 1
    assert session.scalar(
        select(Fact).where(Fact.interpretation_rule_id == rule.id)
    ) is None


def test_replay_cursor_cannot_broaden_its_reviewed_source_scope(session, business):
    sources = []
    for number in range(3):
        source, _, _, _ = ingest_shopify_order(
            session,
            business.tenant.id,
            _payload(f"cursor-scope-{number}"),
            business.company.id,
            business.customer.id,
            business.location.id,
        )
        sources.append(source)
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "Cursor scope",
            "source_system": "shopify",
            "source_type": "order",
            "conditions": [],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": "order.cursor_scope",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "boolean",
            "observed_at_mode": "source_received_at",
        },
    )
    first = replay_rule(
        session,
        business.tenant.id,
        rule.id,
        source_ids=[source.id for source in sources],
        limit=1,
    )
    with pytest.raises(InvalidOperation, match="cursor"):
        replay_rule(
            session,
            business.tenant.id,
            rule.id,
            source_ids=[sources[0].id],
            limit=1,
            cursor=first["next_cursor"],
        )


def test_malformed_replay_cursor_is_rejected_as_invalid_operation(session, business):
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "Malformed cursor",
            "source_system": "shopify",
            "source_type": "order",
            "conditions": [],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": "order.malformed_cursor",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "boolean",
            "observed_at_mode": "source_received_at",
        },
    )

    with pytest.raises(InvalidOperation, match="cursor"):
        replay_rule(session, business.tenant.id, rule.id, cursor="not-base64")


def test_rule_summary_links_created_fact_to_source(session, business):
    source, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        _payload("summary-link"),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    rule = _prepared_rule(
        session,
        business,
        {
            "logical_name": "Summary link",
            "source_system": "shopify",
            "source_type": "order",
            "conditions": [],
            "output_mode": "constant",
            "constant_value": True,
            "predicate": "order.summary_link",
            "subject_type": "commitment",
            "subject_resolver": "source_document_commitments",
            "value_type": "boolean",
            "observed_at_mode": "source_received_at",
        },
    )
    activate_rule(session, business.tenant.id, rule.id)
    replay_rule(session, business.tenant.id, rule.id, source_ids=[source.id])

    detail = gap_detail(session, business.tenant.id, rule.gap_id)
    summary_fact = detail["rules"][0]["summary"]["facts"][0]
    assert summary_fact["source_record_id"] == source.id
    assert summary_fact["fact_id"]
