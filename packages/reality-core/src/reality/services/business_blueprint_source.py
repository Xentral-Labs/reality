"""Inspect server-selected running callables without executing business operations."""

from __future__ import annotations

import ast
import hashlib
import inspect
import os
import types
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

from reality.domain.business_blueprints import SourceEvidence

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MAX_SOURCE_BYTES = 2 * 1024 * 1024
# Public source traversal is narrower than arbitrary modules in the installed package.
DENIED_MODULES = {"account_deletion", "notifications", "email", "desktop_identity", "account_policy"}


class SourceUnavailable(ValueError):
    """Source cannot be established as the loaded, approved implementation."""


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def approved_callable(function: Any) -> bool:
    module = getattr(function, "__module__", "")
    return (
        inspect.isfunction(function)
        and (module.startswith(("reality.services.", "reality.domain.", "reality.tools.", "reality.web.read_models")) or module == "reality.mcp.catalog" and (function.__name__ == "_approve_proposal" or function.__qualname__ in {"_read.<locals>.handler", "_propose.<locals>.handler"}))
        and module.rsplit(".", 1)[-1] not in DENIED_MODULES
        and "business_blueprint" not in module
    )


def code_signature(code: types.CodeType) -> tuple:
    constants = tuple(code_signature(c) if isinstance(c, types.CodeType) else c for c in code.co_consts)
    return (code.co_code, constants, code.co_names, code.co_varnames, code.co_freevars,
            code.co_cellvars, code.co_argcount, code.co_kwonlyargcount, code.co_posonlyargcount,
            code.co_flags, code.co_exceptiontable)


def find_code(code: types.CodeType, qualname: str) -> types.CodeType | None:
    for constant in code.co_consts:
        if isinstance(constant, types.CodeType):
            if constant.co_qualname == qualname:
                return constant
            nested = find_code(constant, qualname)
            if nested is not None:
                return nested
    return None


def literal(node: ast.AST, known: dict[str, Any] | None = None) -> Any:
    """Read syntax constants, never evaluate arbitrary expressions or call fixtures."""
    if isinstance(node, ast.Name) and known is not None and node.id in known:
        return known[node.id]
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        items = [literal(n) for n in node.elts]
        return tuple(items) if isinstance(node, ast.Tuple) else set(items) if isinstance(node, ast.Set) else items
    if isinstance(node, ast.Dict):
        result = {}
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                expanded = literal(value, known)
                if not isinstance(expanded, dict):
                    raise ValueError("Unresolved dictionary expansion")
                result.update(expanded)
            else:
                result[literal(key, known)] = literal(value, known)
        return result
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return literal(node.left, known) | literal(node.right, known)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -literal(node.operand, known)
    if isinstance(node, ast.Call) and ast.unparse(node.func) in {"Decimal", "decimal.Decimal"} and len(node.args) == 1:
        return Decimal(str(literal(node.args[0], known)))
    raise ValueError("Nonliteral source value")


@lru_cache(maxsize=64)
def parsed_module(text: str, filename: str) -> tuple[ast.Module, types.CodeType]:
    tree = ast.parse(text)
    return tree, compile(tree, filename, "exec", dont_inherit=True)


def capture_source(function: Any, *, approved_root: Path | None = None) -> SourceEvidence:
    if approved_root is None and not approved_callable(function):
        raise SourceUnavailable("This function is outside the approved business source boundary.")
    root = approved_root or PACKAGE_ROOT
    try:
        filename = inspect.getsourcefile(function)
        if not filename:
            raise SourceUnavailable("Running source is unavailable.")
        path = Path(filename)
        relative = path.resolve().relative_to(root.resolve())
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root.parent):
            raise SourceUnavailable("Symlink source is not approved.")
        raw = path.read_bytes()
        if len(raw) > MAX_SOURCE_BYTES:
            raise SourceUnavailable("Running source exceeds the analysis boundary.")
        text = raw.decode("utf-8")
        tree, compiled = parsed_module(text, str(path))
        candidate = find_code(compiled, function.__qualname__)
        if candidate is None or code_signature(candidate) != code_signature(function.__code__):
            raise SourceUnavailable("Disk source differs from the running implementation; reload is required.")
        # Resolve literal definitions in source order, including dictionary expansion.
        # Never execute module initialization or use a saved description as authority.
        expected_values: dict[str, Any] = {}
        for statement in tree.body:
            if not isinstance(statement, (ast.Assign, ast.AnnAssign)) or statement.value is None:
                continue
            try:
                expected = literal(statement.value, expected_values)
            except (ValueError, TypeError, ArithmeticError):
                continue
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                expected_values[target.id] = expected
                if target.id in function.__code__.co_names and target.id in function.__globals__ and function.__globals__[target.id] != expected:
                    raise SourceUnavailable("Module values differ from the running implementation; reload is required.")
        start = candidate.co_firstlineno
        source_node = next((n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and min([n.lineno, *(d.lineno for d in n.decorator_list)]) == start), None)
        if source_node is None:
            raise SourceUnavailable("Running source span is unavailable.")
        arguments = [*source_node.args.posonlyargs, *source_node.args.args]
        defaults = list(zip(arguments[-len(source_node.args.defaults):], source_node.args.defaults)) if source_node.args.defaults else []
        defaults += [(arg, value) for arg, value in zip(source_node.args.kwonlyargs, source_node.args.kw_defaults, strict=True) if value is not None]
        positional_defaults = function.__defaults__ or ()
        if len(positional_defaults) > len(arguments):
            raise SourceUnavailable("Function defaults differ from the running implementation; reload is required.")
        actual_defaults = dict(zip([arg.arg for arg in arguments[-len(positional_defaults):]], positional_defaults)) if positional_defaults else {}
        actual_defaults.update(function.__kwdefaults__ or {})
        if set(actual_defaults) != {arg.arg for arg, _ in defaults}:
            raise SourceUnavailable("Function defaults differ from the running implementation; reload is required.")
        source_limits: list[str] = []
        for argument, value in defaults:
            try:
                expected = literal(value, expected_values)
            except (ValueError, TypeError, ArithmeticError):
                binding = function.__globals__.get(value.id) if isinstance(value, ast.Name) else None
                if isinstance(value, ast.Name) and value.id in function.__globals__ and type(binding) in (str, int, float, bool, type(None), Decimal):
                    expected = binding
                else:
                    source_limits.append("Unverified default binding: " + function.__module__ + "." + function.__qualname__ + ":" + argument.arg)
                    continue
            actual = actual_defaults[argument.arg]
            if type(actual) is not type(expected) or actual != expected:
                raise SourceUnavailable("Function defaults differ from the running implementation; reload is required.")
        lines = text.splitlines(keepends=True)[start - 1:source_node.end_lineno]
        code = "".join(lines)
        digest = digest_bytes(raw)
        qualified = function.__module__ + "." + function.__qualname__
        prefix = "packages/reality-core/src/reality/" if approved_root is None else ""
        return SourceEvidence(id=digest_bytes(f"{qualified}:{digest}".encode())[:32],
                              path=prefix + relative.as_posix(), function=qualified,
                              start_line=start, end_line=start + len(lines) - 1,
                              digest=digest, code=code, limitations=tuple(source_limits))
    except (OSError, TypeError, UnicodeError, SyntaxError, ValueError) as error:
        if isinstance(error, SourceUnavailable):
            raise
        raise SourceUnavailable("Approved running source is unavailable.") from None


def release_identity() -> dict[str, Any]:
    commit = os.environ.get("REALITY_COMMIT", "")
    return {"version": os.environ.get("REALITY_VERSION") or "development", "commit": commit or None,
            "provenance": "release" if commit else "development", "source_basis": "loaded_callable"}
