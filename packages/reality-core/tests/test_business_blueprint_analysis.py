"""Graph fidelity, stable identity and non-developer condition phrasing."""

import ast

import pytest
from test_business_blueprint_release import loaded

from reality.services.business_blueprint_analysis import (
    analyze_function,
    expression_text,
)
from reality.services.business_blueprint_source import capture_source


def test_operators_and_zero_limit_survive_business_translation():
    text = expression_text(ast.parse("limit > 0 and exposure > limit", mode="eval").body)
    assert "greater than" in text and "0" in text
    assert "greater than or equal" not in text
    equal = expression_text(ast.parse("exposure >= limit", mode="eval").body)
    assert "greater than or equal" in equal


def test_real_branch_edges_and_refusal_source(tmp_path):
    module = loaded(tmp_path, """def check(limit, exposure):
    # reality-rule: credit.limit
    if limit > 0 and exposure > limit:
        raise ValueError('over_limit')
    return True
""")
    nodes, edges, limitations = analyze_function(capture_source(module.check, approved_root=tmp_path))
    decision = next(n for n in nodes if n.kind == "decision")
    assert decision.id == "credit.limit"
    assert {e.outcome for e in edges if e.source == decision.id} == {"yes", "no"}
    assert any(n.kind == "refusal" and "over_limit" in n.expression for n in nodes)
    assert all(n.evidence_id for n in nodes)
    assert not limitations


def test_duplicate_rule_markers_are_rejected(tmp_path):
    module = loaded(tmp_path, """def check(a, b):
    # reality-rule: duplicate
    if a:
        return True
    # reality-rule: duplicate
    if b:
        return False
    return None
""")
    with pytest.raises(ValueError, match="Duplicate"):
        analyze_function(capture_source(module.check, approved_root=tmp_path))


def test_nested_helpers_and_loop_transfers_have_actual_edges(tmp_path):
    module = loaded(tmp_path, '''def check(rows):
    def eligible(value):
        if value > 0:
            return True
        return False
    for value in rows:
        if not eligible(value):
            continue
        if value > 100:
            break
    return rows
''')
    nodes,edges,limits=analyze_function(capture_source(module.check,approved_root=tmp_path))
    assert any(n.function.endswith('.eligible') and n.expression == 'value > 0' for n in nodes)
    loop=next(n for n in nodes if n.kind=='loop')
    skip=next(n for n in nodes if n.expression=='continue')
    end=next(n for n in nodes if n.expression=='break')
    assert any(e.source==skip.id and e.target==loop.id for e in edges)
    assert any(e.source==end.id and e.outcome=='loop ended' for e in edges)
    assert not limits


def test_expression_and_filter_predicates_are_not_hidden(tmp_path):
    module=loaded(tmp_path,'''def check(limit,exposure,rows):
    over_limit = limit > 0 and exposure > limit
    eligible = [row for row in rows if row.currency == "EUR"]
    amount = exposure if limit > 0 else 0
    return over_limit
''')
    nodes,_edges,limits=analyze_function(capture_source(module.check,approved_root=tmp_path))
    predicates={p for n in nodes for p in n.predicates}
    assert {'limit > 0','exposure > limit',"row.currency == 'EUR'"} <= predicates
    assert not limits


def test_dynamic_local_dispatch_is_named_as_unresolved():
    import ast
    import inspect
    import textwrap

    from reality.services.business_blueprints import _resolve_calls

    def dispatch(record):
        operation = record["operation"]
        return operation(record)

    _, limitations = _resolve_calls(dispatch, ast.parse(textwrap.dedent(inspect.getsource(dispatch))))
    assert any("operation" in item and "dynamic" in item.lower() for item in limitations)


def test_duplicate_identities_across_functions_are_rejected(monkeypatch):
    from reality.domain.business_blueprints import RuleNode
    from reality.services import business_blueprints as service
    from reality.services.credit_exposure import _json_exposure, _money

    monkeypatch.setattr(service, "_roots", lambda *args: [_money, _json_exposure])
    monkeypatch.setattr(service, "_resolve_calls", lambda *args: ([], []))
    def duplicate_analysis(source):
        return ([RuleNode(id="duplicate.rule", function=source.function, kind="decision", text="Check the rule", expression="value > 0", evidence_id=source.id, line=source.start_line, end_line=source.end_line, durable=True)], [], [])
    monkeypatch.setattr(service, "analyze_function", duplicate_analysis)
    import pytest
    with pytest.raises(ValueError, match="Duplicate shared rule identity"):
        service.explain("command", "credit_exposure")


def test_unverified_source_defaults_remain_visible_in_blueprint(monkeypatch):
    from reality.services import business_blueprints as service
    from reality.services.credit_exposure import _money

    original = service.capture_source
    monkeypatch.setattr(service, "_roots", lambda *args: [_money])
    monkeypatch.setattr(service, "_resolve_calls", lambda *args: ([], []))
    monkeypatch.setattr(service, "capture_source", lambda *args, **kwargs: original(*args, **kwargs).model_copy(update={"limitations": ("Unverified default binding: example",)}))
    result = service.explain("command", "credit_exposure")
    assert "Unverified default binding: example" in result.limitations
    assert result.status == "partial"
