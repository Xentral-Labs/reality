"""Generic live interpretation, citation boundaries and graph fidelity."""

import pytest
from test_business_blueprint_release import loaded

from reality.domain.business_blueprints import TestScenario as Scenario
from reality.services import business_blueprint_presentation as presentation
from reality.services.business_blueprint_analysis import analyze_function
from reality.services.business_blueprint_source import capture_source


def evidence(tmp_path, code):
    module = loaded(tmp_path, code)
    source = capture_source(module.check, approved_root=tmp_path)
    nodes, edges, _ = analyze_function(source)
    return tuple(nodes), tuple(edges), (source,)


def explain(tmp_path, code, language="de", scenarios=()):
    nodes, edges, sources = evidence(tmp_path, code)
    return presentation.present(
        nodes, edges, scenarios, sources=sources, language=language
    )


def provider(monkeypatch, infer):
    monkeypatch.setattr(
        presentation, "deployment_provider", lambda: (infer, "test-model")
    )


def test_previously_unknown_operation_uses_live_evidence_without_authored_vocabulary(
    tmp_path, monkeypatch
):
    received = []

    def infer(envelope):
        received.append(envelope)
        rule = next(r for r in envelope["rules"] if r["kind"] == "calculation")
        return {
            "steps": [
                {
                    "rule_id": rule["id"],
                    "text": "Die neue Fachgröße wird aus der aktuellen Formel ermittelt.",
                }
            ]
        }

    provider(monkeypatch, infer)
    first = explain(
        tmp_path,
        "def check(new_business_operand):\n    novel_result = new_business_operand * 3\n    return novel_result\n",
    )
    changed = tmp_path / "changed"
    changed.mkdir()
    second = explain(
        changed,
        "def check(new_business_operand):\n    novel_result = new_business_operand * 7\n    return novel_result\n",
    )
    assert first.mode == second.mode == "llm"
    assert "* 3" in received[0]["sources"][0]["code"]
    assert "* 7" in received[1]["sources"][0]["code"]
    assert received[0]["language"] == "de"
    assert first.steps[0].evidence_ids != second.steps[0].evidence_ids
    assert all(s.rule_ids and s.evidence_ids for s in first.steps)
    assert set(received[0]) == {
        "language",
        "entry",
        "sources",
        "rules",
        "edges",
        "tests",
        "test_helpers",
    }
    assert "KI-Interpretation" in first.notice


@pytest.mark.parametrize(
    "bad", ["unknown_rule", "duplicate", "oversize", "unknown_test"]
)
def test_invalid_interpretation_citations_or_bounds_are_not_displayed(
    tmp_path, monkeypatch, bad
):
    def infer(envelope):
        rule = envelope["rules"][0]
        step = {"rule_id": rule["id"], "text": "Explanation"}
        if bad == "unknown_rule":
            step["rule_id"] = "invented"
        if bad == "oversize":
            step["text"] = "x" * 1201
        return {
            "steps": [step, step] if bad == "duplicate" else [step],
            "scenarios": [{"id": "invented", "title": "Invented case"}]
            if bad == "unknown_test"
            else [],
        }

    provider(monkeypatch, infer)
    result = explain(tmp_path, "def check(value):\n    return value\n")
    assert result.mode == "unavailable"
    assert not result.steps


def test_missing_or_failing_provider_does_not_substitute_saved_prose(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(presentation, "deployment_provider", lambda: None)
    result = explain(tmp_path, "def check(value):\n    return value\n")
    assert result.mode == "unavailable" and not result.steps
    assert "keine gespeicherte" in result.notice

    def failure(_):
        raise ValueError("provider secret must not leak")

    provider(monkeypatch, failure)
    result = explain(tmp_path, "def check(value):\n    return value\n")
    assert "secret" not in result.notice


def test_diagram_uses_actual_branches_across_hidden_scaffolding(tmp_path, monkeypatch):
    def infer(envelope):
        return {
            "steps": [
                {"rule_id": n["id"], "text": n["kind"]}
                for n in envelope["rules"]
                if n["kind"] in {"decision", "refusal", "result"}
            ]
        }

    provider(monkeypatch, infer)
    result = explain(
        tmp_path,
        """def check(limit, exposure):
    if exposure > limit:
        scratch = []
        raise InvalidOperation(code="credit_exceeded")
    scratch = {}
    return exposure
""",
        "en",
    )
    guard = next(s for s in result.steps if s.kind == "decision")
    assert {e.outcome for e in result.edges if e.source == guard.id} == {"yes", "no"}
    assert all(
        e.source in {s.id for s in result.steps}
        and e.target in {s.id for s in result.steps}
        for e in result.edges
    )


def test_scenario_summaries_link_actual_cases_without_claiming_execution(
    tmp_path, monkeypatch
):
    scenario = Scenario(
        id="test_case",
        name="test_limit",
        path="test.py",
        line=1,
        digest="abc",
        code='def test_limit():\n    assert result["exposure"] == 125\n',
    )

    def infer(envelope):
        assert envelope["tests"][0]["run"]["outcome"] == "unknown"
        assert "125" in envelope["tests"][0]["code"]
        return {
            "steps": [],
            "scenarios": [
                {
                    "id": "test_case",
                    "title": "Kreditobligo prüfen",
                    "then": [
                        {"assertion_index": 0, "text": "Das Kreditobligo beträgt 125."}
                    ],
                    "unknowns": ["Ausgangslage nicht vollständig belegt."],
                }
            ],
        }

    provider(monkeypatch, infer)
    result = explain(
        tmp_path, "def check(value):\n    return value\n", scenarios=(scenario,)
    )
    assert result.scenarios[0].id == scenario.id
    assert "125" in " ".join(result.scenarios[0].then)
    assert "erfolgreichen Testlauf" in result.scenarios[0].notice
    assert result.scenarios[0].unexplained_assertions == 0
    assert result.scenarios[0].assertion_indices == (0,)


def test_input_boundary_and_busy_interpreter_are_explicit(tmp_path, monkeypatch):
    provider(monkeypatch, lambda _: pytest.fail("Must not invoke provider"))
    monkeypatch.setattr(presentation, "MAX_INPUT_BYTES", 1)
    result = explain(tmp_path, "def check(value):\n    return value\n")
    assert "Grenze" in result.notice
    monkeypatch.setattr(presentation, "MAX_INPUT_BYTES", 240_000)
    presentation.INFERENCE_SLOTS.acquire()
    presentation.INFERENCE_SLOTS.acquire()
    try:
        result = explain(tmp_path, "def check(value):\n    return value\n")
        assert "ausgelastet" in result.notice
    finally:
        presentation.INFERENCE_SLOTS.release()
        presentation.INFERENCE_SLOTS.release()


def test_source_changed_during_description_read_discards_presentation(
    tmp_path, monkeypatch
):
    from reality.services import business_blueprints as service

    module = loaded(tmp_path, "def check(value):\n    return value\n")
    monkeypatch.setattr(
        service, "_inventory", lambda: {("command", "check"): {"label": "Check"}}
    )
    monkeypatch.setattr(service, "_roots", lambda *args: [module.check])
    monkeypatch.setattr(service, "_test_root", lambda: (None, {}))
    actual_capture = service.capture_source
    monkeypatch.setattr(
        service,
        "capture_source",
        lambda fn, **kwargs: actual_capture(fn, approved_root=tmp_path),
    )

    actual_describe = service.describe

    def changed_during_read(*args, **kwargs):
        result = actual_describe(*args, **kwargs)
        (tmp_path / "blueprint_fixture.py").write_text(
            "def check(value):\n    return False\n"
        )
        return result

    monkeypatch.setattr(service, "describe", changed_during_read)
    result = service.explain("command", "check", language="de")
    assert result.status == "outdated"
    assert result.business.mode == "outdated"
    assert not result.business.steps


def test_technical_evidence_reads_do_not_call_model(tmp_path, monkeypatch):
    from reality.services import business_blueprints as service

    module = loaded(tmp_path, "def check(value):\n    return value\n")
    monkeypatch.setattr(
        service, "_inventory", lambda: {("command", "check"): {"label": "Check"}}
    )
    monkeypatch.setattr(service, "_roots", lambda *args: [module.check])
    monkeypatch.setattr(service, "_test_root", lambda: (None, {}))
    actual_capture = service.capture_source
    monkeypatch.setattr(
        service,
        "capture_source",
        lambda fn, **kwargs: actual_capture(fn, approved_root=tmp_path),
    )
    provider(monkeypatch, lambda _: pytest.fail("Technical reads must not invoke LLM"))
    result = service.explain("command", "check", interpret=False)
    assert result.business is None and result.sources
    assert (
        service.source_for("command", "check", result.sources[0].id)["code"]
        == result.sources[0].code
    )


def test_business_overview_requires_real_source_references(tmp_path, monkeypatch):
    def infer(envelope):
        return {
            "overview": {
                "text": "Der neue Vorgang verarbeitet die gezeigte Fachgröße.",
                "evidence_ids": [envelope["sources"][0]["id"]],
            },
            "steps": [],
        }

    provider(monkeypatch, infer)
    result = explain(tmp_path, "def check(value):\n    return value\n")
    assert result.overview.text.startswith("Der neue")
    assert result.overview.evidence_ids
    provider(
        monkeypatch,
        lambda _: {
            "overview": {"text": "Invented", "evidence_ids": ["unknown"]},
            "steps": [],
        },
    )
    assert (
        explain(tmp_path, "def check(value):\n    return value\n").mode == "unavailable"
    )


def test_deployment_provider_sends_bounded_structured_source_request_without_tools(
    monkeypatch,
):
    import httpx

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-provider-key")
    monkeypatch.delenv("REALITY_BLUEPRINT_LLM_ENABLED", raising=False)
    seen = []

    def post(url, **kwargs):
        seen.append(kwargs)
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "stop_reason": "tool_use",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "explain_current_business_logic",
                        "input": {"steps": []},
                    }
                ],
            },
        )

    monkeypatch.setattr(presentation.httpx, "post", post)
    infer, _ = presentation.deployment_provider()
    assert infer({"language": "de", "sources": []}) == {"steps": []}
    assert "RESPONSE LANGUAGE: GERMAN" in seen[0]["json"]["system"]
    assert seen[0]["timeout"] == 60
    assert seen[0]["json"]["tool_choice"]["name"] == "explain_current_business_logic"
    assert len(seen[0]["json"]["tools"]) == 1
    assert seen[0]["json"]["tools"][0].get("strict") is True
    assert "test-provider-key" not in seen[0]["json"]["messages"][0]["content"]


def test_unexplained_assertions_count_actual_test_code_not_model_unknowns(
    tmp_path, monkeypatch
):
    scenario = Scenario(
        id="case",
        name="case",
        path="test.py",
        line=1,
        digest="abc",
        code='def test_case():\n    assert result["exposure"] == 125\n    assert unknown_helper(result)\n',
    )

    def infer(_):
        return {
            "steps": [],
            "scenarios": [
                {
                    "id": "case",
                    "title": "Check exposure",
                    "then": [{"assertion_index": 0, "text": "Exposure equals 125"}],
                    "unknowns": ["Setup unknown"],
                }
            ],
        }

    provider(monkeypatch, infer)
    result = explain(
        tmp_path, "def check(value):\n    return value\n", scenarios=(scenario,)
    )
    assert result.scenarios[0].unexplained_assertions == 1
    provider(
        monkeypatch,
        lambda _: {
            "steps": [],
            "scenarios": [
                {
                    "id": "case",
                    "title": "Bad assertion",
                    "then": [{"assertion_index": 2, "text": "Invented"}],
                }
            ],
        },
    )
    assert (
        explain(
            tmp_path, "def check(value):\n    return value\n", scenarios=(scenario,)
        ).mode
        == "unavailable"
    )


def test_json_encoded_step_array_is_validated_without_weakening_citations(
    tmp_path, monkeypatch
):
    import json

    def infer(envelope):
        return {
            "steps": json.dumps(
                [
                    {
                        "rule_id": envelope["rules"][0]["id"],
                        "text": "Der Vorgang liefert die gezeigte Fachgröße.",
                    }
                ]
            )
        }

    provider(monkeypatch, infer)
    result = explain(tmp_path, "def check(value):\n    return value\n")
    assert result.mode == "llm"
    assert result.steps[0].rule_ids
    provider(
        monkeypatch,
        lambda _: {"steps": '[{"rule_id":"invented","text":"No evidence"}]'},
    )
    assert (
        explain(tmp_path, "def check(value):\n    return value\n").mode == "unavailable"
    )
    provider(monkeypatch, lambda _: {"steps": "Uncited prose must not be accepted"})
    assert (
        explain(tmp_path, "def check(value):\n    return value\n").mode == "unavailable"
    )


def test_strict_provider_schema_restricts_known_references_and_keeps_local_bounds():
    schema = presentation.provider_schema(
        {"rules": [{"id": "r0"}], "sources": [{"id": "s0"}], "tests": [{"id": "case"}]}
    )
    step = schema["$defs"]["InterpretedStep"]["properties"]
    assert step["rule_id"]["enum"] == ["r0"]
    assert "maxLength" not in step["text"]
    assert "1200" in step["text"]["description"]
    assert schema["$defs"]["InterpretedOverview"]["properties"]["evidence_ids"][
        "items"
    ]["enum"] == ["s0"]
    assert schema["$defs"]["InterpretedScenario"]["properties"]["id"]["enum"] == [
        "case"
    ]


def test_each_test_sentence_carries_its_assertion_in_one_structured_value(
    tmp_path, monkeypatch
):
    scenario = Scenario(
        id="case",
        name="case",
        path="test.py",
        line=1,
        digest="abc",
        code="def test_case():\n    assert result == 125\n",
    )
    provider(
        monkeypatch,
        lambda _: {
            "steps": [],
            "scenarios": [
                {
                    "id": "case",
                    "title": "Result",
                    "then": [
                        {"assertion_index": 0, "text": "Das Ergebnis beträgt 125."}
                    ],
                }
            ],
        },
    )
    result = explain(
        tmp_path, "def check(value):\n    return value\n", scenarios=(scenario,)
    )
    assert result.mode == "llm"
    assert result.scenarios[0].assertion_indices == (0,)
    assert result.scenarios[0].then == ("Das Ergebnis beträgt 125.",)


def test_brief_live_read_retains_current_source_but_omits_test_generation(
    tmp_path, monkeypatch
):
    received = []

    def infer(envelope):
        received.append(envelope)
        return {
            "steps": [{"rule_id": envelope["rules"][0]["id"], "text": "Current rule."}]
        }

    provider(monkeypatch, infer)
    nodes, edges, sources = evidence(
        tmp_path, "def check(value):\n    return value * 7\n"
    )
    result = presentation.present(
        nodes, edges, (), sources=sources, language="en", brief=True
    )
    assert result.mode == "llm"
    assert received[0]["brief"] is True
    assert received[0]["tests"] == received[0]["test_helpers"] == []
    assert "* 7" in received[0]["sources"][0]["code"]
    assert "brief" in result.notice.lower()
    assert result.steps[0].evidence_ids


def test_brief_provider_schema_structurally_limits_six_slots():
    schema = presentation.provider_schema(
        {"brief": True, "rules": [{"id": "r0"}], "sources": [{"id": "s0"}]}
    )
    assert schema["properties"]["steps"]["type"] == "object"
    assert schema["properties"]["steps"]["required"] == [
        f"rule_{i}" for i in range(1, 7)
    ]
    assert schema["properties"]["steps"]["additionalProperties"] is False
    assert schema["properties"]["overview"] == {"type": "null"}


def test_conditional_reading_preserves_multiline_text_and_exact_citation(
    tmp_path, monkeypatch
):
    wording = "WENN der Betrag positiv ist:\nDANN gilt die genannte Prüfung."

    def infer(envelope):
        decision = next(
            rule for rule in envelope["rules"] if rule["kind"] == "decision"
        )
        return {"steps": [{"rule_id": decision["id"], "text": wording}]}

    provider(monkeypatch, infer)
    result = explain(
        tmp_path,
        "def check(amount):\n    if amount > 0:\n        return True\n    return False\n",
    )
    assert result.steps[0].text == wording
    assert len(result.steps[0].rule_ids) == len(result.steps[0].evidence_ids) == 1
    assert "IF / THEN / ELSE" in presentation.SYSTEM
    assert "Never invent an ELSE" in presentation.SYSTEM
