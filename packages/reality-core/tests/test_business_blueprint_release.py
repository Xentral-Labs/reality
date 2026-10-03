"""Prove running-source identity rather than trusting checkout text or release tags."""

import importlib.util
import sys

import pytest

from reality.services.business_blueprint_source import SourceUnavailable, capture_source


def loaded(tmp_path, text, name="blueprint_fixture"):
    path = tmp_path / f"{name}.py"
    path.write_text(text)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_disk_edit_is_not_running_code(tmp_path):
    module = loaded(
        tmp_path,
        "def check(limit, exposure):\n    return limit > 0 and exposure > limit\n",
    )
    before = capture_source(module.check, approved_root=tmp_path)
    assert before.digest and "exposure > limit" in before.code
    (tmp_path / "blueprint_fixture.py").write_text(
        "def check(limit, exposure):\n    return limit > 0 and exposure >= limit\n"
    )
    with pytest.raises(SourceUnavailable, match="running"):
        capture_source(module.check, approved_root=tmp_path)
    changed = loaded(
        tmp_path,
        "def check(limit, exposure):\n    return limit > 0 and exposure >= limit\n",
    )
    assert capture_source(changed.check, approved_root=tmp_path).digest != before.digest


def test_symlink_escape_and_missing_source_fail_closed(tmp_path):
    module = loaded(tmp_path, "def check():\n    return True\n")
    with pytest.raises(SourceUnavailable):
        capture_source(module.check, approved_root=tmp_path / "other")
    (tmp_path / "blueprint_fixture.py").unlink()
    with pytest.raises(SourceUnavailable):
        capture_source(module.check, approved_root=tmp_path)


def test_live_source_does_not_execute_handler(tmp_path):
    module = loaded(
        tmp_path, "def check():\n    raise RuntimeError('must never execute')\n"
    )
    assert (
        "must never execute"
        in capture_source(module.check, approved_root=tmp_path).code
    )


def test_raw_evidence_package_has_matching_bytes_and_no_saved_explanations(tmp_path):
    import hashlib
    import importlib.util
    from pathlib import Path

    script = (
        Path(__file__).resolve().parents[3]
        / "scripts/package_business_blueprint_evidence.py"
    )
    spec = importlib.util.spec_from_file_location("blueprint_package", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = Path(__file__).parent
    manifest = module.package(root, tmp_path, "test-release")
    assert manifest["commit"] == "test-release"
    for name, digest in manifest["tests"].items():
        assert (tmp_path / "tests" / name).read_bytes() == (root / name).read_bytes()
        assert (
            hashlib.sha256((tmp_path / "tests" / name).read_bytes()).hexdigest()
            == digest
        )
    assert {p.name for p in tmp_path.iterdir()} == {"tests", "manifest.json"}


def test_missing_and_mixed_release_evidence_remains_unknown(tmp_path, monkeypatch):
    import json

    from reality.services.business_blueprints import _test_root

    monkeypatch.setenv("REALITY_BLUEPRINT_EVIDENCE", str(tmp_path))
    monkeypatch.setenv("REALITY_COMMIT", "new")
    assert _test_root() == (None, {})
    (tmp_path / "manifest.json").write_text(json.dumps({"commit": "old"}))
    assert _test_root() == (None, {})


def test_request_detects_source_changed_between_capture_and_response(
    tmp_path, monkeypatch
):
    from reality.services import business_blueprints as service

    module = loaded(tmp_path, "def check():\n    return True\n")
    monkeypatch.setattr(
        service,
        "_inventory",
        lambda: {
            ("command", "check"): {"kind": "command", "key": "check", "label": "Check"}
        },
    )
    monkeypatch.setattr(service, "_roots", lambda *a: [module.check])
    real = service.capture_source
    calls = 0

    def capture(fn, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            (tmp_path / "blueprint_fixture.py").write_text(
                "def check():\n    return False\n"
            )
        return real(fn, approved_root=tmp_path)

    monkeypatch.setattr(service, "capture_source", capture)
    result = service.explain("command", "check")
    assert result.status == "outdated"
    assert any("running" in item for item in result.limitations)


def test_changed_expanded_constants_do_not_match_loaded_configuration(tmp_path):
    text = 'BASE = {"role":"receivable"}\nPOLICY = {**BASE,"enabled":True}\ndef check():\n    return POLICY["role"]\n'
    module = loaded(tmp_path, text)
    capture_source(module.check, approved_root=tmp_path)
    (tmp_path / "blueprint_fixture.py").write_text(
        text.replace("receivable", "payable")
    )
    with pytest.raises(SourceUnavailable, match="Module values"):
        capture_source(module.check, approved_root=tmp_path)


def test_mutated_callable_default_is_not_the_displayed_source(tmp_path):
    module = loaded(tmp_path, "def check(limit=100):\n    return limit\n")
    module.check.__defaults__ = (200,)
    with pytest.raises(SourceUnavailable, match="defaults"):
        capture_source(module.check, approved_root=tmp_path)


def test_runtime_bindings_never_expose_secret_values(tmp_path, monkeypatch):
    from reality.services import business_blueprints as service

    module = loaded(
        tmp_path,
        'API_SECRET = "sensitive-marker"\ndef check():\n    return API_SECRET\n',
    )
    monkeypatch.setattr(
        service,
        "_inventory",
        lambda: {
            ("command", "check"): {"kind": "command", "key": "check", "label": "Check"}
        },
    )
    monkeypatch.setattr(service, "_roots", lambda *a: [module.check])
    real = service.capture_source
    monkeypatch.setattr(
        service, "capture_source", lambda fn, **kwargs: real(fn, approved_root=tmp_path)
    )
    result = service.explain("command", "check")
    assert "sensitive-marker" not in result.model_dump_json()
    assert not result.runtime_values
    assert result.status == "partial"


def test_imported_default_mutation_is_not_claimed_as_matching_source(tmp_path):
    module = loaded(
        tmp_path, "from math import pi\ndef check(limit=pi):\n    return limit\n"
    )
    capture_source(module.check, approved_root=tmp_path)
    module.check.__defaults__ = (1.0,)
    with pytest.raises(SourceUnavailable, match="defaults"):
        capture_source(module.check, approved_root=tmp_path)


def test_unsupported_defaults_are_disclosed_without_executing_the_factory(tmp_path):
    module = loaded(
        tmp_path,
        "calls = []\ndef make_default():\n    calls.append('created')\n    return {'limit': 1}\ndef check(limit=make_default()):\n    return limit\n",
    )
    before = list(module.calls)
    evidence = capture_source(module.check, approved_root=tmp_path)
    assert module.calls == before
    assert any(
        "default" in item.lower() and "unverified" in item.lower()
        for item in evidence.limitations
    )


def test_changed_default_layout_marks_the_blueprint_outdated(monkeypatch):
    from decimal import Decimal

    from reality.services import business_blueprints as service
    from reality.services.credit_exposure import _money

    monkeypatch.setattr(_money, "__defaults__", (Decimal(1),))
    monkeypatch.setattr(service, "_roots", lambda *args: [_money])
    result = service.explain("command", "credit_exposure")
    assert result.status == "outdated"
    assert any("defaults differ" in item for item in result.limitations)


def test_function_span_index_matches_first_walk_node_for_decorators_and_nesting():
    import ast

    from reality.services.business_blueprint_source import function_span_index

    tree = ast.parse(
        "def identity(fn):\n    return fn\n"
        "@identity\ndef decorated():\n    return 1\n"
        "def outer():\n    async def nested():\n        return 2\n    return nested\n"
    )
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    # Preserve the old next(ast.walk(...)) semantics even for colliding spans.
    functions[-1].lineno = functions[0].lineno
    expected = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = min([node.lineno, *(d.lineno for d in node.decorator_list)])
            expected.setdefault(start, node)
    indexed = function_span_index(tree)
    assert indexed.keys() == expected.keys()
    assert all(indexed[start] is node for start, node in expected.items())
    assert indexed[3].name == "decorated"
    assert indexed[1].name == "identity"


def test_repeated_capture_indexes_each_content_parsed_module_only_once(
    tmp_path, monkeypatch
):
    from reality.services import business_blueprint_source as source

    module = loaded(
        tmp_path,
        "def identity(fn):\n    return fn\n"
        "@identity\ndef first(value=1):\n    return value\n"
        "def second():\n    return 2\n",
    )
    source.function_span_index.cache_clear()
    original_walk = source.ast.walk
    traversals = []

    def counted_walk(tree):
        traversals.append(tree)
        return original_walk(tree)

    monkeypatch.setattr(source.ast, "walk", counted_walk)
    first = source.capture_source(module.first, approved_root=tmp_path)
    second = source.capture_source(module.second, approved_root=tmp_path)
    repeated = source.capture_source(module.first, approved_root=tmp_path)
    assert first.code.startswith("@identity\n")
    assert second.code.startswith("def second():")
    assert repeated == first
    assert len(traversals) == 1
    assert source.function_span_index.cache_info().hits == 2
    assert source.function_span_index.cache_info().maxsize == 32


def test_changed_source_uses_a_new_span_index_and_stale_callable_still_fails(tmp_path):
    from reality.services import business_blueprint_source as source

    module = loaded(tmp_path, "def check():\n    return 1\n")
    source.capture_source(module.check, approved_root=tmp_path)
    path = tmp_path / "blueprint_fixture.py"
    before = path.read_text()
    old_tree, _ = source.parsed_module(before, str(path))
    old_index = source.function_span_index(old_tree)
    path.write_text("# A changed source version\ndef check():\n    return 2\n")
    new_tree, _ = source.parsed_module(path.read_text(), str(path))
    new_index = source.function_span_index(new_tree)
    assert new_tree is not old_tree
    assert new_index is not old_index
    assert set(old_index) == {1}
    assert set(new_index) == {2}
    with pytest.raises(SourceUnavailable, match="running implementation"):
        source.capture_source(module.check, approved_root=tmp_path)
