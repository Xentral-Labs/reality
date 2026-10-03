import ast

from reality.services.business_blueprint_tests import extract_scenarios
from reality.services.business_blueprint_tests import test_run as read_test_run


def test_scenarios_preserve_assertions_and_parameters_without_executing(tmp_path):
    source = """import pytest
from decimal import Decimal
@pytest.mark.parametrize('limit, expected', [('0', False), ('100', True)])
def test_limit(session, limit, expected):
    result = credit_exposure(session, 'tenant', limit=limit)
    assert result['over_limit'] is expected
"""
    path = tmp_path / "test_limits.py"
    path.write_text(source)
    tests = extract_scenarios(path, {"credit_exposure"}, (), approved_root=tmp_path)
    assert len(tests) == 2
    assert tests[0].parameters == {"limit": "0", "expected": False}
    assert tests[1].parameters == {"limit": "100", "expected": True}
    assert "over_limit" in tests[0].expectations[0]
    assert "Fixture session" in " ".join(tests[0].assumptions)
    assert all(t.run["outcome"] == "unknown" for t in tests)
    path.write_text(source.replace("is expected", "is not expected"))
    changed = extract_scenarios(path, {"credit_exposure"}, (), approved_root=tmp_path)
    assert changed[0].digest != tests[0].digest
    assert "is not" in changed[0].expectations[0]
    ast.parse(source)  # Analysis never imports pytest or executes this module.


def test_execution_outcome_needs_exact_revision_and_time():
    record = {"outcome": "passed", "commit": "old", "executed_at": "2026-10-03T12:00:00Z", "evidence": "ci/run/1"}
    assert read_test_run(record, "current")["revision_match"] is False
    assert read_test_run(record, "old")["revision_match"] is True
    assert read_test_run({}, "old")["outcome"] == "unknown"
    assert read_test_run({"outcome": "passed", "commit": "old"}, "old")["outcome"] == "unknown"


def test_helper_defaults_keep_known_currency_and_unresolved_setup_visible(tmp_path):
    path=tmp_path/'test_limits.py'
    path.write_text('''def _customer(session,limit="1000"):
    return create_party(session,credit_limit=limit,default_currency="EUR")
def test_limit(session):
    party=_customer(session)
    result=credit_exposure(session,party.id,as_of=unknown_date())
    assert result["over_limit"] is False
''')
    scenarios=extract_scenarios(path,{'credit_exposure'},(),approved_root=tmp_path)
    limit=next(f for f in scenarios[0].facts if f.name=='limit')
    assert limit.value=='1000' and limit.currency=='EUR'
    assert any('as_of' in item for item in scenarios[0].assumptions)
    assert scenarios[0].helpers


def test_invalid_execution_timestamp_never_claims_a_run():
    assert read_test_run({'outcome':'passed','commit':'current','executed_at':'yesterday','evidence':'run'},'current')['outcome']=='unknown'


def test_a_commit_label_alone_cannot_prove_changed_source_or_test():
    record={'outcome':'passed','commit':'current','executed_at':'2026-10-03T12:00:00Z','evidence':'run','test_digest':'test-old','source_digest':'source-old'}
    assert read_test_run(record,'current',test_digest='test-new',source_digest='source-old')['revision_match'] is False
    assert read_test_run(record,'current',test_digest='test-old',source_digest='source-new')['revision_match'] is False
    assert read_test_run(record,'current',test_digest='test-old',source_digest='source-old')['revision_match'] is True
