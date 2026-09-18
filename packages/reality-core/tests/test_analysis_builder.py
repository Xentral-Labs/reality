"""The three builder presentations preserve one checked question."""

import pytest

from reality.domain.traversal import Traversal
from reality.services.analytics.cypher_surface import format_query, parse


def canonical(query):
    data = query.model_dump(by_alias=True, mode="json")
    origin = data["as"]
    for hop in data["follow"]:
        hop["from"] = hop["from"] or origin
        origin = hop["as"]
    return data


def test_builder_path_round_trip_preserves_parameters_and_named_axes():
    question = Traversal.model_validate(
        {
            "from": "order",
            "as": "o",
            "filter": [
                {
                    "field": "o.number",
                    "op": "not_in",
                    "value": ["O'Reilly", "RETURN SET"],
                },
                {"field": "o.currency", "op": "eq", "value": "EUR"},
            ],
            "measures": ["order_count"],
            "group_by": [
                {"field": "o.ordered_at", "bucket": "month", "as": "Order month"}
            ],
            "order_by": [{"by": "Order month", "descending": True}],
            "limit": 50,
        }
    )
    editor = format_query(question)
    assert "O'Reilly" not in editor["path"]
    assert canonical(parse(editor["path"], editor["parameters"])) == canonical(question)


def test_builder_path_preserves_branches_and_advanced_clauses():
    question = Traversal.model_validate(
        {
            "from": "order",
            "as": "o",
            "follow": [
                {"edge": "ordered_by", "as": "c", "from": "o"},
                {"edge": "contains", "as": "l", "from": "o"},
            ],
            "measures": ["line_amount"],
            "group_by": [{"field": "o.currency"}],
            "having": [{"measure": "line_amount", "op": "gt", "value": 10}],
            "exists": [
                {
                    "follow": [{"edge": "ordered_by", "as": "p", "from": "o"}],
                    "filter": [{"field": "p.name", "op": "eq", "value": "Alice"}],
                    "negated": True,
                }
            ],
        }
    )
    editor = format_query(question)
    assert canonical(parse(editor["path"], editor["parameters"])) == canonical(question)


@pytest.mark.parametrize(
    "op,value",
    [
        ("in", []),
        ("not_in", [True, False]),
        ("eq", False),
        ("is_null", None),
        ("is_not_null", None),
    ],
)
def test_builder_filter_values_are_lossless(op, value):
    question = Traversal.model_validate(
        {
            "from": "party",
            "filter": [{"field": "root.name", "op": op, "value": value}],
            "group_by": [{"field": "root.name"}],
        }
    )
    editor = format_query(question)
    assert canonical(parse(editor["path"], editor["parameters"])) == canonical(question)


def test_builder_recursive_path_round_trip():
    question = parse(
        "MATCH (l:location)<-[:within*1..3]-(s:location) RETURN s.name LIMIT 20"
    )
    editor = format_query(question)
    assert canonical(parse(editor["path"], editor["parameters"])) == canonical(question)


def test_interpretation_validates_provider_question_before_returning():
    from reality.services.analytics.interpretation import checked_interpretation

    result = checked_interpretation(
        {
            "status": "ready",
            "message": "Orders by currency",
            "question": {
                "from": "order",
                "measures": ["order_count"],
                "group_by": [{"field": "root.currency"}],
            },
        }
    )
    assert result["status"] == "ready"
    assert result["question"]["from"] == "order"
    with pytest.raises(Exception, match="no.*|unknown|does not|not"):
        checked_interpretation(
            {
                "status": "ready",
                "message": "",
                "question": {
                    "from": "secret_table",
                    "group_by": [{"field": "root.password"}],
                },
            }
        )


def test_interpretation_never_converts_clarification_into_a_question():
    from reality.services.analytics.interpretation import checked_interpretation

    assert checked_interpretation(
        {"status": "clarification", "message": "Which period?"}
    ) == {"status": "clarification", "message": "Which period?", "question": None}
    with pytest.raises(ValueError):
        checked_interpretation({"status": "ready", "message": "Guess"})
    with pytest.raises(ValueError):
        checked_interpretation(
            {"status": "unsupported", "message": "", "question": None}
        )


@pytest.mark.parametrize(
    "clause",
    [
        "order_count > 2 OR order_count < 1",
        "order_count > 2 junk",
        "order_count > 2 AND",
    ],
)
def test_expert_having_refuses_unconsumed_syntax(clause):
    from reality.services.analytics.cypher_surface import CypherRefused

    with pytest.raises(CypherRefused):
        parse(f"MATCH (o:order) RETURN order_count HAVING {clause}")


def test_interpretation_checks_membership_before_dispatch(
    session, business, scheduled_owner, monkeypatch
):
    from reality.services.analytics import interpretation
    from reality.services.core import NotFound, create_tenant
    from reality.services.memberships import Principal

    calls = []
    monkeypatch.setattr(
        interpretation, "provider_interpretation", lambda *args: calls.append(args)
    )
    other = create_tenant(session, "Other analysis company")
    with pytest.raises(NotFound):
        interpretation.interpret(
            session, other.id, Principal(scheduled_owner.id), "Orders"
        )
    assert calls == []


def test_managed_interpretation_reserves_before_dispatch_without_sending_record_values(
    session, business, scheduled_owner, monkeypatch
):
    from reality.services import free_playground
    from reality.services.analytics import interpretation
    from reality.services.memberships import Principal

    events = []
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        free_playground,
        "reserve_managed_question",
        lambda s, t, u: events.append(("reserved", t, u)),
    )
    monkeypatch.setattr(
        interpretation,
        "reporting_catalog",
        lambda **kwargs: {
            "nodes": [{"properties": [{"key": "status", "values": ["private-value"]}]}]
        },
    )

    def respond(settings, key, prompt, text):
        assert events == [("reserved", business.tenant.id, scheduled_owner.id)]
        assert "private-value" not in prompt
        assert text == "Orders by currency"
        events.append("dispatched")
        return {
            "status": "ready",
            "question": {
                "from": "order",
                "measures": ["order_count"],
                "group_by": [{"field": "root.currency"}],
            },
        }

    monkeypatch.setattr(interpretation, "provider_interpretation", respond)
    result = interpretation.interpret(
        session, business.tenant.id, Principal(scheduled_owner.id), "Orders by currency"
    )
    assert result["status"] == "ready"
    assert events[-1] == "dispatched"


def test_interpretation_unavailable_and_bad_output_are_explicit(
    session, business, scheduled_owner, monkeypatch
):
    from reality.services import free_playground
    from reality.services.analytics import interpretation
    from reality.services.analytics.errors import AnalyticsError
    from reality.services.memberships import Principal

    principal = Principal(scheduled_owner.id)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(AnalyticsError) as missing:
        interpretation.interpret(session, business.tenant.id, principal, "Orders")
    assert missing.value.code == "provider_unavailable"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    reservations = []
    monkeypatch.setattr(
        free_playground,
        "reserve_managed_question",
        lambda *args: reservations.append(1),
    )
    monkeypatch.setattr(
        interpretation, "provider_interpretation", lambda *args: {"status": "ready"}
    )
    with pytest.raises(AnalyticsError) as invalid:
        interpretation.interpret(session, business.tenant.id, principal, "Orders")
    assert invalid.value.code == "interpretation_failed"
    assert reservations == [1]


def test_graph_formatter_is_tenant_checked_and_has_no_record_values(session, business):
    from reality.services.core import NotFound
    from reality.tools.application import run_read_tool

    question = {"from": "order", "measures": ["order_count"]}
    editor = run_read_tool(
        session, business.tenant.id, "graph.format", {"question": question}
    )
    assert editor["parameters"] == {}
    assert "order_count" in editor["path"]
    with pytest.raises(NotFound):
        run_read_tool(session, "absent-tenant", "graph.format", {"question": question})


def test_advanced_expert_definition_survives_private_save_and_reopen(
    session, business, scheduled_owner
):
    from uuid import uuid4

    from reality.services.analytics.reports import change_graph_report, get_report
    from reality.services.memberships import Principal

    principal = Principal(scheduled_owner.id)
    question = Traversal.model_validate(
        {
            "from": "order",
            "as": "o",
            "measures": ["order_count"],
            "group_by": [{"field": "o.currency", "as": "Currency"}],
            "having": [{"measure": "order_count", "op": "gt", "value": 2}],
            "exists": [
                {
                    "follow": [{"edge": "ordered_by", "as": "p", "from": "o"}],
                    "filter": [{"field": "p.name", "op": "eq", "value": "Alice"}],
                }
            ],
            "order_by": [{"by": "order_count", "descending": True}, {"by": "Currency"}],
        }
    )
    editor = format_query(question)
    checked = parse(editor["path"], editor["parameters"])
    saved = change_graph_report(
        session,
        business.tenant.id,
        principal,
        {
            "operation": "create",
            "request_id": str(uuid4()),
            "name": "Expert orders",
            "question": checked.model_dump(by_alias=True, mode="json"),
        },
    )
    reopened = get_report(session, business.tenant.id, principal, saved["id"])
    assert canonical(Traversal.model_validate(reopened["definition"])) == canonical(
        question
    )


@pytest.mark.parametrize(
    "projection", ["order_count AS total", "sum(order_count) AS total"]
)
def test_expert_measure_alias_is_refused_instead_of_silently_dropped(projection):
    from reality.services.analytics.cypher_surface import CypherRefused

    with pytest.raises(CypherRefused, match="alias"):
        parse(f"MATCH (o:order) RETURN {projection}")
