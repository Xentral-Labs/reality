"""Future executable entries and tests must not silently lose source descriptions."""

import importlib.util
from pathlib import Path

import pytest
from test_business_blueprint_release import loaded

from reality.services import business_blueprints

SOURCE = '''def check(amount):
    """
    BUSINESS PURPOSE:
    Keep the customer's stated amount visible.

    BUSINESS RULE fixture.amount:
    Return the amount exactly as supplied.
    """
    # reality-rule: fixture.amount
    return amount
'''

TEST_SOURCE = '''def test_stated_amount():
    """
    BUSINESS TEST:
    The stated amount is retained.
    GIVEN:
    The amount is 12.
    WHEN:
    Read the supplied amount.
    THEN:
    The result remains 12.
    BUSINESS RULES:
    fixture.amount
    """
    assert check(12) == 12
'''


@pytest.fixture
def authoring_audit(tmp_path, monkeypatch):
    script = (
        Path(__file__).resolve().parents[3] / "scripts/check_business_annotations.py"
    )
    spec = importlib.util.spec_from_file_location("fixture_annotation_audit", script)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    source_dir = tmp_path / "packages/reality-core/src/reality"
    source_dir.mkdir(parents=True)
    test_dir = tmp_path / "packages/reality-core/tests"
    test_dir.mkdir(parents=True)
    source = loaded(source_dir, SOURCE, name="audit_fixture")
    (test_dir / "test_example.py").write_text(TEST_SOURCE)
    monkeypatch.setattr(checker, "APPROVED_TESTS", ("test_example.py",))
    inventory = {("command", "stated_amount"): {"handler": source.check}}
    monkeypatch.setattr(business_blueprints, "_inventory", lambda: inventory)
    monkeypatch.setattr(
        business_blueprints, "_roots", lambda entry, _: [entry["handler"]]
    )
    return checker, tmp_path, source_dir, test_dir, inventory


def test_complete_authored_fixture_passes_strict_coverage(authoring_audit):
    checker, root, _, _, _ = authoring_audit
    report = checker.audit(root)
    assert report["errors"] == []
    assert report["missing_root_descriptions"] == {}
    assert report["missing_test_descriptions"] == []
    assert report["missing_root_bindings"] == []
    assert checker.coverage_failures(report) == []


def test_future_registered_root_without_docstring_fails_coverage(authoring_audit):
    checker, root, source_dir, _, inventory = authoring_audit
    future = loaded(
        source_dir,
        "def future_check(amount):\n    return amount\n",
        name="future_audit",
    )
    inventory[("command", "future_check")] = {"handler": future.future_check}
    report = checker.audit(root)
    assert report["missing_root_descriptions"] == {
        "future_audit.future_check": ["command:future_check"]
    }
    assert checker.coverage_failures(report)


def test_future_approved_test_without_business_description_fails_coverage(
    authoring_audit,
):
    checker, root, _, test_dir, _ = authoring_audit
    with (test_dir / "test_example.py").open("a") as target:
        target.write("\ndef test_future_case():\n    assert check(0) == 0\n")
    report = checker.audit(root)
    assert len(report["missing_test_descriptions"]) == 1
    assert report["missing_test_descriptions"][0].endswith(":test_future_case")
    assert checker.coverage_failures(report)


def test_registered_entry_without_source_binding_fails_coverage(
    authoring_audit, monkeypatch
):
    checker, root, _, _, inventory = authoring_audit
    inventory[("view", "future_view")] = {"handler": None}
    monkeypatch.setattr(
        business_blueprints,
        "_roots",
        lambda entry, _: [entry["handler"]] if entry["handler"] else [],
    )
    report = checker.audit(root)
    assert report["missing_root_bindings"] == ["view:future_view"]
    assert checker.coverage_failures(report)


def test_invalid_rule_binding_fails_even_when_root_has_a_docstring(authoring_audit):
    checker, root, source_dir, _, inventory = authoring_audit
    broken = loaded(
        source_dir,
        SOURCE.replace("BUSINESS RULE fixture.amount:", "BUSINESS RULE nonexistent:"),
        name="broken_audit",
    )
    inventory.clear()
    inventory[("command", "broken")] = {"handler": broken.check}
    report = checker.audit(root)
    assert any("Unresolved rule references: nonexistent" in e for e in report["errors"])
    assert checker.coverage_failures(report)


def test_two_public_names_reuse_one_verified_physical_closure(authoring_audit):
    checker, root, source_dir, _, inventory = authoring_audit
    closure = loaded(
        source_dir,
        '''def bind(application_name):
    def handler(arguments):
        """
        BUSINESS PURPOSE:
        Read the application capability bound to this adapter.

        BUSINESS RULE fixture.bound_read:
        Return the bound name and original arguments; this adapter does not mutate business records.
        """
        # reality-rule: fixture.bound_read
        return application_name, arguments
    return handler
''',
        name="closure_audit",
    )
    inventory.clear()
    inventory[("tool", "first_read")] = {"handler": closure.bind("first")}
    inventory[("tool", "second_read")] = {"handler": closure.bind("second")}
    report = checker.audit(root)
    assert report["entries"] == 2
    assert report["root_functions"] == 1
    assert report["missing_root_descriptions"] == {}
    assert report["errors"] == []
    # The audit inspects shared source; calling either closure is unnecessary.
    assert any(name.endswith(":handler") for name in report["described_functions"])
