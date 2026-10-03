"""Read actual synthetic test definitions and assertions, never execute them."""

from __future__ import annotations

import ast
from datetime import datetime
from decimal import Decimal
from itertools import product
from pathlib import Path
from typing import Any

from reality.domain.business_blueprints import (
    RuleNode,
    SourceEvidence,
    TestFact,
    TestScenario,
)
from reality.services.business_blueprint_analysis import business_label, expression_text
from reality.services.business_blueprint_source import digest_bytes, literal

APPROVED_TESTS = (
    "test_credit_exposure.py", "test_credit_hold.py", "test_credit_hold_adapters.py",
    "test_fulfillment_readiness.py", "test_proposal_decision_policy.py", "test_down_payments.py",
    "test_stock_blocks.py", "test_movement_corrections.py", "finance/test_available_credits.py",
    "finance/test_settlement_flows.py", "conftest.py",
)


def test_run(record: dict[str, Any], commit: str | None, *, test_digest: str | None = None, source_digest: str | None = None) -> dict[str, Any]:
    outcome = record.get("outcome")
    if outcome not in {"passed", "failed", "skipped"} or not all(record.get(k) for k in ("commit", "executed_at", "evidence")):
        return {"outcome": "unknown", "revision_match": False}
    try:
        if datetime.fromisoformat(record["executed_at"]).tzinfo is None:
            raise ValueError("Run timestamp requires timezone")
    except (ValueError, TypeError):
        return {"outcome": "unknown", "revision_match": False}
    return {"outcome": outcome, "revision_match": bool(commit and record["commit"] == commit and (test_digest is None or record.get("test_digest") == test_digest) and (source_digest is None or record.get("source_digest") == source_digest)),
            "commit": record["commit"], "executed_at": record["executed_at"], "evidence": record["evidence"]}


def _variants(function: ast.FunctionDef) -> list[dict[str, Any]]:
    sets: list[list[dict[str, Any]]] = []
    for decorator in function.decorator_list:
        if not isinstance(decorator, ast.Call) or not ast.unparse(decorator.func).endswith("parametrize") or len(decorator.args) < 2:
            continue
        try:
            names = literal(decorator.args[0])
            names = [n.strip() for n in names.split(",")] if isinstance(names, str) else list(names)
            values = literal(decorator.args[1])
            sets.append([dict(zip(names, list(value) if len(names) > 1 else [value], strict=True)) for value in values])
        except (ValueError, TypeError, ArithmeticError):
            continue
    if not sets:
        return [{}]
    return [{k: v for part in parts for k, v in part.items()} for parts in product(*sets)][:200]


def _fact_value(node: ast.AST, known: dict[str, Any]) -> Any:
    if isinstance(node, ast.Name) and node.id in known:
        return known[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        left, right = Decimal(str(_fact_value(node.left, known))), Decimal(str(_fact_value(node.right, known)))
        return str({ast.Add: lambda: left+right, ast.Sub: lambda: left-right, ast.Mult: lambda: left*right, ast.Div: lambda: left/right}[type(node.op)]())
    if isinstance(node, ast.Call) and ast.unparse(node.func) in {"Decimal", "str"} and len(node.args) == 1:
        return _fact_value(node.args[0], known)
    return literal(node)


def extract_scenarios(path: Path, function_names: set[str], rules: tuple[RuleNode, ...], *, approved_root: Path) -> list[TestScenario]:
    resolved = path.resolve()
    relative = resolved.relative_to(approved_root.resolve()).as_posix()
    if relative not in APPROVED_TESTS and path.parent.resolve() != approved_root.resolve():
        raise ValueError("Unapproved test evidence")
    if path.is_symlink():
        raise ValueError("Unapproved test evidence")
    raw = path.read_bytes()
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Test source exceeds evidence boundary")
    source = raw.decode("utf-8")
    tree = ast.parse(source)
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    fixtures = dict(functions)
    conftest = approved_root / "conftest.py"
    if conftest.is_symlink():
        raise ValueError("Unapproved fixture evidence")
    if conftest.exists() and conftest != path:
        fixtures.update({n.name: n for n in ast.parse(conftest.read_text()).body if isinstance(n, ast.FunctionDef)})
    aliases = {n.asname or n.name: n.name for node in tree.body if isinstance(node, ast.ImportFrom) for n in node.names}
    global_values: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            try:
                value = literal(node.value)
            except (ValueError, TypeError, ArithmeticError):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    global_values[target.id] = value

    def calls_for(function: ast.FunctionDef, visited: set[str]) -> set[str]:
        names: set[str] = set()
        for node in ast.walk(function):
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func).rsplit(".", 1)[-1]
                names.add(aliases.get(name, name))
                if name in functions and name not in visited and len(visited) < 30:
                    names |= calls_for(functions[name], visited | {name})
        return names

    scenarios: list[TestScenario] = []
    for function in functions.values():
        if not function.name.startswith("test_") or not calls_for(function, {function.name}) & function_names:
            continue
        assertions = [node for node in ast.walk(function) if isinstance(node, ast.Assert)]
        # Output-key equality assertions can substantiate the matching calculation only.
        result_names = {target.id for stmt in function.body if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call) and aliases.get(ast.unparse(stmt.value.func).rsplit(".",1)[-1], ast.unparse(stmt.value.func).rsplit(".",1)[-1]) in function_names for target in stmt.targets if isinstance(target, ast.Name)}
        assertion_keys = {n.slice.value for assertion in assertions for n in ast.walk(assertion.test)
                          if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id in result_names and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str)}
        linked = tuple(rule.id for rule in rules if rule.kind == "calculation" and any(
            re_assignment(rule.expression, key) for key in assertion_keys))
        for index, parameters in enumerate(_variants(function)):
            known = {**global_values, **parameters}
            facts: list[TestFact] = []
            setup: list[str] = []
            action: list[str] = []
            assumptions = ["Fixture " + a.arg + ": read its source; runtime state is not executed or inferred."
                           for a in function.args.args if a.arg not in parameters]
            helpers: list[SourceEvidence] = []
            for decorator in function.decorator_list:
                if isinstance(decorator, ast.Call) and ast.unparse(decorator.func).endswith("parametrize") and len(decorator.args) >= 2:
                    try:
                        literal(decorator.args[1])
                    except (ValueError, TypeError, ArithmeticError):
                        assumptions.append("Parameterized values cannot be resolved statically; displayed source does not represent every executable variant.")

            for statement in function.body:
                if isinstance(statement, ast.Assign):
                    try:
                        value = _fact_value(statement.value, known)
                    except (ValueError, TypeError, ArithmeticError):
                        value = None
                    if value is not None:
                        for target in statement.targets:
                            if isinstance(target, ast.Name):
                                known[target.id] = value
                for node in ast.walk(statement):
                    if not isinstance(node, ast.Call):
                        continue
                    name = ast.unparse(node.func).rsplit(".", 1)[-1]
                    if name in function_names:
                        action.append(expression_text(node))
                    elif name in functions or name.startswith(("create_", "record_", "post_", "_")):
                        setup.append(expression_text(node))
                    keywords = {kw.arg: kw.value for kw in node.keywords if kw.arg}
                    helper = functions.get(name)
                    if helper:
                        defaults = dict(zip([a.arg for a in helper.args.args][-len(helper.args.defaults):], helper.args.defaults)) if helper.args.defaults else {}
                        keywords = {**defaults, **{arg.arg: value for arg, value in zip(helper.args.args, node.args)}, **keywords}

                        if len(helpers) < 20:
                            helpers.append(SourceEvidence(id=digest_bytes(f"{relative}:{name}:{digest_bytes(raw)}".encode())[:32],
                                path="packages/reality-core/tests/" + relative, function=name,
                                start_line=helper.lineno, end_line=helper.end_lineno, digest=digest_bytes(raw),
                                code=ast.get_source_segment(source, helper) or ""))
                    helper_currency = None
                    if helper:
                        for helper_call in ast.walk(helper):
                            if isinstance(helper_call, ast.Call):
                                for kw in helper_call.keywords:
                                    if kw.arg == "default_currency":
                                        try:
                                            helper_currency = _fact_value(kw.value, known)
                                        except (ValueError, TypeError, ArithmeticError):
                                            pass
                    for key, value_node in keywords.items():
                        if key in {"session", "tenant_id", "business", "party", "document", "order"}:
                            continue
                        try:
                            value = _fact_value(value_node, known)
                        except (ValueError, TypeError, ArithmeticError):
                            assumptions.append(f"Input {key} at {relative}:{node.lineno} is not statically resolved: {expression_text(value_node)}")
                            continue
                        if isinstance(value, (str, int, float, bool)) or value is None:
                            currency_node = keywords.get("currency") or keywords.get("default_currency")
                            unit_node = keywords.get("unit")
                            try:
                                currency = _fact_value(currency_node, known) if currency_node else helper_currency
                                unit = _fact_value(unit_node, known) if unit_node else None
                            except (ValueError, TypeError, ArithmeticError):
                                currency, unit = None, None
                            facts.append(TestFact(name=key, value=value, origin=f"{relative}:{node.lineno}", currency=str(currency) if currency and key not in {"currency","default_currency","name","kind","number"} else None, unit=str(unit) if unit else None))
            for arg in function.args.args:
                fixture = fixtures.get(arg.arg)
                if fixture is not None and not arg.arg.startswith(("session", "postgres", "monkeypatch")):
                    fixture_path = path if arg.arg in functions else conftest
                    fixture_text = fixture_path.read_text()
                    helpers.append(SourceEvidence(id=digest_bytes(f"{fixture_path.name}:{arg.arg}:{digest_bytes(fixture_text.encode())}".encode())[:32],
                        path="packages/reality-core/tests/" + fixture_path.relative_to(approved_root).as_posix(),
                        function=arg.arg, start_line=fixture.lineno, end_line=fixture.end_lineno,
                        digest=digest_bytes(fixture_text.encode()), code=ast.get_source_segment(fixture_text, fixture) or ""))
            identity = f"{relative}::{function.name}" + (f"[{index}]" if parameters else "")
            scenarios.append(TestScenario(id=identity, name=business_label(function.name.removeprefix("test_")),
                path="packages/reality-core/tests/" + relative, line=function.lineno, digest=digest_bytes(raw),
                setup=tuple(dict.fromkeys(setup)), action=tuple(dict.fromkeys(action)),
                expectations=tuple(expression_text(a.test) for a in assertions), facts=tuple(facts),
                assumptions=tuple(assumptions), rules=linked, parameters=parameters,
                relationship="assertion_linked" if linked else "candidate",
                code=ast.get_source_segment(source, function) or "", helpers=tuple({h.id: h for h in helpers}.values())))
    return scenarios


def re_assignment(expression: str, name: str) -> bool:
    try:
        node = ast.parse(expression).body[0]
    except SyntaxError:
        return False
    return isinstance(node, ast.Assign) and any(isinstance(n, ast.Name) and n.id == name for n in node.targets)
