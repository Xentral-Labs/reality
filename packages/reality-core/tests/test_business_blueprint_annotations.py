"""Authored descriptions are current evidence, never inferred business authority."""

import pytest
from reality.domain.business_blueprints import TestScenario as Scenario
from reality.services.business_blueprint_analysis import analyze_function
from reality.services.business_blueprint_source import SourceUnavailable, capture_source
from test_business_blueprint_release import loaded


def present(tmp_path, code, scenarios=()):
    from reality.services.business_blueprint_annotations import describe

    module = loaded(tmp_path, code)
    source = capture_source(module.check, approved_root=tmp_path)
    rules, _, _ = analyze_function(source)
    return describe(tuple(rules), (source,), scenarios)


ANNOTATED = '''def check(limit, amount):
    """
    BUSINESS PURPOSE:
    Check whether the customer's stated limit is exceeded.

    BUSINESS RULE new.limit:
    IF the amount is greater than the limit:
        Return that the limit is exceeded.
    ELSE:
        Return that it is not exceeded.
    """
    # reality-rule: new.limit
    return amount > limit
'''


def test_unknown_future_function_reads_authored_text_and_real_code_citation(tmp_path):
    result = present(tmp_path, ANNOTATED)
    assert result.mode == "authored" and result.language == "en"
    assert "customer's stated limit" in result.overview.text
    assert len(result.steps) == 1
    assert result.steps[0].rule_ids == ("new.limit",)
    assert result.steps[0].line == 13
    assert "ELSE:" in result.steps[0].text
    assert result.model is None


@pytest.mark.parametrize("change", ["missing", "duplicate", "unknown_header"])
def test_invalid_annotations_are_explicit_and_never_fabricated(tmp_path, change):
    code = ANNOTATED
    if change == "missing":
        code = code.replace("BUSINESS RULE new.limit:", "BUSINESS RULE imaginary:")
    elif change == "duplicate":
        code = code.replace(
            '    """\n    # reality-rule',
            '    BUSINESS RULE new.limit:\n    Duplicate.\n    """\n    # reality-rule',
        )
    else:
        code = code.replace("BUSINESS PURPOSE:", "BUSINESS OTHER:")
    result = present(tmp_path, code)
    assert result.annotation_gaps
    assert not result.steps


def test_missing_descriptions_do_not_invent_rules(tmp_path):
    result = present(tmp_path, "def check(amount):\n    return amount * 3\n")
    assert result.mode == "unavailable" and not result.steps
    assert result.annotation_gaps


def test_docstring_change_requires_reload(tmp_path):
    module = loaded(tmp_path, ANNOTATED)
    capture_source(module.check, approved_root=tmp_path)
    (tmp_path / "blueprint_fixture.py").write_text(
        ANNOTATED.replace("customer's", "supplier's")
    )
    with pytest.raises(SourceUnavailable):
        capture_source(module.check, approved_root=tmp_path)


def test_test_description_keeps_original_assertions_unknown_run_and_variants(tmp_path):
    test_code = '''def test_limit(amount):
    """
    BUSINESS TEST:
    Exact limit stays allowed.
    GIVEN:
    A stated limit equal to the amount.
    WHEN:
    Read the limit check.
    THEN:
    No limit breach is reported.
    BUSINESS RULES:
    new.limit
    """
    assert not check(amount, amount)
'''
    scenarios = tuple(
        Scenario(
            id=f"case-{n}",
            name="test_limit",
            path="test.py",
            line=1,
            digest="same",
            code=test_code,
            expectations=("not check(amount, amount)",),
            parameters={"amount": n},
        )
        for n in (1, 2)
    )
    result = present(tmp_path, ANNOTATED, scenarios)
    assert len(result.scenarios) == 2
    assert result.scenarios[0].title == "Exact limit stays allowed."
    assert result.scenarios[0].then == ("No limit breach is reported.",)
    assert result.scenarios[0].assertion_indices == ()
    assert result.scenarios[0].unexplained_assertions == 1
    assert "not executed" in result.scenarios[0].notice
    assert all(s.run["outcome"] == "unknown" for s in scenarios)


def test_shared_service_never_calls_configured_provider(monkeypatch):
    from reality.services import business_blueprint_presentation, business_blueprints

    def forbidden(*args, **kwargs):
        raise AssertionError("No external inference allowed")

    monkeypatch.setattr(
        business_blueprint_presentation, "deployment_provider", forbidden
    )
    result = business_blueprints.explain("command", "credit_exposure", language="de")
    assert result.business.mode == "authored"
    assert result.business.language == "en"
    assert any(
        "open invoices + uninvoiced orders - available credits" in step.text
        for step in result.business.steps
    )
    assert len(result.business.scenarios) >= 6


def test_public_and_application_reads_share_authored_descriptions_without_provider(
    session, business, monkeypatch
):
    from fastapi.testclient import TestClient
    from reality.services import business_blueprint_presentation
    from reality.tools.application import run_read_tool
    from reality.web.app import app

    def forbidden(*args, **kwargs):
        raise AssertionError("No external inference allowed")

    monkeypatch.setattr(
        business_blueprint_presentation, "deployment_provider", forbidden
    )
    public = TestClient(app).get(
        "/api/business-logic/entries/command/credit_exposure",
        params={"language": "de", "brief": True, "interpret": True},
    )
    assert public.status_code == 200
    tool = run_read_tool(
        session,
        business.tenant.id,
        "business_logic_explain",
        {"kind": "command", "key": "credit_exposure", "language": "de"},
    )
    assert public.json()["business"] == tool["business"]
    assert public.json()["evidence_digest"] == tool["evidence_digest"]
    assert tool["business"]["mode"] == "authored"


def test_helper_purpose_is_not_presented_as_unannotated_entry_purpose(tmp_path):
    from reality.services.business_blueprint_annotations import describe

    module = loaded(tmp_path, ANNOTATED)
    helper = capture_source(module.check, approved_root=tmp_path)
    nodes, _, _ = analyze_function(helper)
    root = helper.model_copy(
        update={
            "id": "unannotated-root",
            "function": "wrapper",
            "code": "def wrapper():\n    return check()\n",
        }
    )
    result = describe(tuple(nodes), (root, helper), ())
    assert result.mode == "authored" and result.steps
    assert result.overview is None


@pytest.mark.parametrize("replacement", ["", "x" * 4001])
def test_empty_and_oversized_description_sections_fail_closed(tmp_path, replacement):
    result = present(
        tmp_path,
        ANNOTATED.replace(
            "Check whether the customer's stated limit is exceeded.", replacement
        ),
    )
    assert result.annotation_gaps
    assert not result.steps and result.overview is None


def test_rule_then_label_remains_conditional_prose(tmp_path):
    result = present(
        tmp_path,
        ANNOTATED.replace(
            "        Return that the limit is exceeded.",
            "    THEN:\n        Return that the limit is exceeded.",
        ),
    )
    assert result.mode == "authored" and not result.annotation_gaps
    assert "THEN:" in result.steps[0].text


def test_repository_annotations_pass_the_repeatable_authoring_audit():
    import importlib.util
    from pathlib import Path

    script = (
        Path(__file__).resolve().parents[3] / "scripts/check_business_annotations.py"
    )
    spec = importlib.util.spec_from_file_location("business_annotation_audit", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.audit()
    assert report["errors"] == []
    assert report["context"] == "repository_authoring_audit"
    assert (
        len(
            [
                name
                for name in report["described_tests"]
                if "test_credit_exposure.py:" in name
            ]
        )
        == 6
    )
    assert isinstance(report["missing_root_descriptions"], dict)
    assert report["entries"] >= report["root_functions"]
