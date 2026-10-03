import pytest
from fastapi.testclient import TestClient

from reality.web.app import app


def test_public_generic_reads_do_not_require_company_or_allow_case_inputs():
    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/business-logic/entries", params={"query": "credit"})
    assert response.status_code == 200
    assert response.json()["entries"]
    assert (
        client.get(
            "/api/business-logic/entries", params={"tenant_id": "foreign"}
        ).status_code
        == 422
    )
    assert (
        client.get("/api/business-logic/entries/tool/does-not-exist").status_code == 404
    )
    assert (
        client.get(
            "/api/business-logic/entries/tool/credit_exposure/source/../../etc/passwd"
        ).status_code
        != 200
    )


def test_tools_are_read_only_and_share_the_blueprint(session, business):
    from reality.mcp.catalog import MCP_TOOL_CATALOG
    from reality.tools.application import run_read_tool

    tools = {t.name: t for t in MCP_TOOL_CATALOG}
    for name in (
        "business_logic_discover",
        "business_logic_explain",
        "business_logic_source",
        "business_logic_compare",
    ):
        assert tools[name].access == "read"
        assert tools[name].input_schema["additionalProperties"] is False
    result = run_read_tool(
        session,
        business.tenant.id,
        "business_logic_explain",
        {"kind": "tool", "key": "credit_exposure"},
    )
    assert result["context"] == "running_implementation"
    assert any("exposure > limit" in n["expression"] for n in result["nodes"])


def test_public_admission_and_size_limits():
    import pytest
    from fastapi import HTTPException

    from reality.web.business_blueprint_api import Admission, _bounded

    admission = Admission()
    for _ in range(30):
        with admission.read("test-address"):
            pass
    with pytest.raises(HTTPException) as error, admission.read("test-address"):
        pass
    assert error.value.status_code == 429
    with pytest.raises(HTTPException) as error:
        _bounded({"text": "x" * (2 * 1024 * 1024)})
    assert error.value.status_code == 503


def test_chat_blueprint_projection_preserves_evidence_without_expanded_graph():
    import json

    from reality.agent.mcp_chat import _tool_result_content

    result = {
        "kind": "tool",
        "key": "future",
        "status": "partial",
        "evidence_digest": "current",
        "release": {"version": "live"},
        "business": {
            "steps": [{"id": "r", "text": "Actual rule", "evidence_ids": ["s"]}],
            "edges": [{"outcome": "x" * 300000}],
        },
        "sources": [
            {"id": "s", "path": "current.py", "code": "x" * 300000, "digest": "abc"}
        ],
        "nodes": [
            {
                "id": "r",
                "kind": "decision",
                "expression": "amount > limit",
                "evidence_id": "s",
                "line": 3,
            }
        ],
        "edges": [{"outcome": "x" * 300000}],
        "scenarios": [
            {
                "id": "case",
                "name": "actual_test",
                "facts": [],
                "expectations": ["amount == 125"],
                "run": {"outcome": "unknown"},
                "code": "x" * 300000,
                "helpers": [],
            }
        ],
        "limitations": ["Partial source"],
    }
    original = json.dumps(result)
    content = _tool_result_content("business_logic_explain", result)
    assert len(content.encode()) <= 120000
    view = json.loads(content)
    assert view["sources"][0]["id"] == "s"
    assert view["scenarios"][0]["expectations"] == ["amount == 125"]
    assert view["scenarios"][0]["run"]["outcome"] == "unknown"
    assert view["evidence_counts"]["scenarios"]["total"] == 1
    assert view["nodes"][0]["expression"] == "amount > limit"
    assert "edges" not in view and "code" not in view["sources"][0]
    assert json.dumps(result) == original
    assert json.loads(_tool_result_content("unrelated_read", {"answer": 7})) == {
        "answer": 7
    }


def test_chat_answer_footer_uses_actual_sources_and_discovered_test_count():
    from reality.agent.mcp_chat import _with_blueprint_evidence

    result = {
        "kind": "tool",
        "key": "future",
        "scenarios": [{"id": "one"}, {"id": "two"}],
        "sources": [{"id": "exact-source-id", "path": "actual.py", "start_line": 12}],
        "business": {"steps": []},
    }
    answer = _with_blueprint_evidence("Antwort", [result], "de")
    assert "2" in answer and "Testnachweise" in answer
    assert "/api/business-logic/entries/tool/future/source/exact-source-id" in answer
    assert "actual.py:12" in answer
    assert "erfolgreichen" in answer
    assert _with_blueprint_evidence("Plain", [], "en") == "Plain"


@pytest.mark.parametrize(
    "kind,key",
    [
        ("view", "items"),
        ("projection", "inventory"),
        ("exception", "overdue_outgoing_customer_commitment"),
    ],
)
def test_public_source_only_read_never_calls_interpreter(monkeypatch, kind, key):
    from reality.services import business_blueprint_presentation as presentation

    def forbidden(*args, **kwargs):
        raise AssertionError("Source viewing must not invoke the model")

    monkeypatch.setattr(presentation, "deployment_provider", forbidden)
    response = TestClient(app).get(
        f"/api/business-logic/entries/{kind}/{key}", params={"interpret": "false"}
    )
    assert response.status_code == 200
    assert response.json()["sources"]
    assert response.json()["business"] is None
