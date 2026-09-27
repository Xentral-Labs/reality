"""Coded refusals cannot regress, and the ratchet only shrinks (spec 286 FR-006/FR-007).

A pure AST pass: every `raise <refusal class>(...)` in an in-scope module carries a literal
`code=` keyword, or is listed in `config/refusal_ratchet.json` by (path, function, message).
The ratchet records the refusals that are not coded yet: `scope: "286"` entries must be empty
when spec 286 is done, `scope: "later"` entries belong to areas that follow.
"""

from __future__ import annotations

import ast
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from reality.domain import refusals

SOURCE = Path(__file__).resolve().parents[1] / "src"
RATCHET = Path(__file__).resolve().parents[1] / "config" / "refusal_ratchet.json"
#: Classes whose sentence the catalog owns. Classes with their own code vocabulary
#: (analytics, traversal, Cypher) or a fixed coded sentence are not listed here.
CATALOG_CLASSES = frozenset(
    {
        "RealityError",
        "NotFound",
        "InvalidOperation",
        "Conflict",
        "PlaygroundOperationDenied",
    }
)

#: Domain refusals (`ValueError`s) that carry catalog codes into the services' re-raise.
DOMAIN_CLASSES = frozenset(
    {"DomainRefusal", "CostingRefusal", "ShipmentCompatibilityError"}
)


@dataclass(frozen=True)
class Site:
    path: str
    line: int
    function: str
    message: str
    code: str | None
    coded: bool


def _message(call: ast.Call, source: str) -> str:
    """The literal sentence, or the source text of a computed one.

    Source text, not `ast.unparse`: unparse renders f-strings differently across
    Python versions, which would make the ratchet keys depend on the interpreter.
    """
    if not call.args:
        return ""
    first = call.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return " ".join((ast.get_source_segment(source, first) or "").split())


def refusal_sites(source: str, path: str) -> list[Site]:
    """Every raise of a catalog refusal class in one module, with its enclosing function."""
    tree = ast.parse(source)
    sites: list[Site] = []

    def visit(node: ast.AST, scope: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                visit(child, (*scope, child.name))
                continue
            if isinstance(child, ast.Raise) and isinstance(child.exc, ast.Call):
                func = child.exc.func
                name = (
                    func.id
                    if isinstance(func, ast.Name)
                    else func.attr
                    if isinstance(func, ast.Attribute)
                    else None
                )
                if name in CATALOG_CLASSES:
                    keyword = next(
                        (k for k in child.exc.keywords if k.arg == "code"), None
                    )
                    literal = (
                        keyword.value.value
                        if keyword is not None
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                        else None
                    )
                    sites.append(
                        Site(
                            path,
                            child.lineno,
                            ".".join(scope) or "<module>",
                            _message(child.exc, source),
                            literal,
                            keyword is not None,
                        )
                    )
            visit(child, scope)

    visit(tree, ())
    return sites


def gate(modules: dict[str, str], ratchet: list[dict], catalog: dict) -> list[str]:
    """All violations for the given module sources, ratchet entries and catalog."""
    problems: list[str] = []
    allowed = Counter(
        (entry["path"], entry["function"], entry["message"])
        for entry in ratchet
        for _ in range(entry.get("count", 1))
    )
    used = Counter()
    for path, source in modules.items():
        for site in refusal_sites(source, path):
            if site.coded:
                if site.code is not None and site.code not in catalog["refusals"]:
                    problems.append(
                        f"{site.path}:{site.line} raises unknown refusal code {site.code!r}"
                    )
                continue
            key = (site.path, site.function, site.message)
            used[key] += 1
            if used[key] > allowed[key]:
                problems.append(
                    f"{site.path}:{site.line} raises an uncoded refusal in {site.function}: "
                    f"{site.message!r}"
                )
    for key, count in allowed.items():
        if used[key] < count:
            problems.append(
                f"ratchet entry is stale (fixed or moved; remove it): {key[0]} {key[1]} "
                f"{key[2]!r}"
            )
    return problems


def _load_ratchet() -> dict:
    return json.loads(RATCHET.read_text(encoding="utf-8"))


def _module_sources(paths: list[str]) -> dict[str, str]:
    return {path: (SOURCE / path).read_text(encoding="utf-8") for path in paths}


# The shipped state --------------------------------------------------------------------


def test_in_scope_modules_raise_only_coded_or_ratcheted_refusals():
    ratchet = _load_ratchet()
    problems = gate(
        _module_sources(ratchet["modules"]), ratchet["entries"], refusals.catalog()
    )
    assert problems == [], "\n".join(problems)


def constructed_codes(source: str) -> list[tuple[int, str]]:
    """Every literal code a catalog refusal class is constructed with, raised or not."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else func.attr
            if isinstance(func, ast.Attribute)
            else None
        )
        if name not in CATALOG_CLASSES | DOMAIN_CLASSES:
            continue
        for keyword in node.keywords:
            if (
                keyword.arg == "code"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ):
                found.append((node.lineno, keyword.value.value))
    return found


def test_every_code_in_the_package_is_in_the_catalog_and_every_entry_is_raised():
    catalog = refusals.catalog()
    raised: set[str] = set()
    unknown: list[str] = []
    for path in sorted(SOURCE.rglob("*.py")):
        relative = str(path.relative_to(SOURCE))
        for line, code in constructed_codes(path.read_text(encoding="utf-8")):
            raised.add(code)
            if code not in catalog["refusals"]:
                unknown.append(f"{relative}:{line} {code}")
    # Codes raised indirectly (a class that passes its own code, a domain refusal)
    # are declared beside the ratchet.
    raised |= set(_load_ratchet().get("indirect_codes", []))
    assert unknown == []
    assert sorted(set(catalog["refusals"]) - raised) == []


def test_ratchet_is_well_formed():
    ratchet = _load_ratchet()
    assert ratchet["version"] == 1
    assert len(ratchet["modules"]) == len(set(ratchet["modules"]))
    for entry in ratchet["entries"]:
        assert set(entry) <= {"path", "function", "message", "count", "scope"}
        assert entry["scope"] in {"286", "later"}
        assert entry["path"] in ratchet["modules"]


# Positive and negative controls on synthetic sources ---------------------------------------

SAMPLE = """
from reality.services import core
from reality.services.core import InvalidOperation

def coded():
    raise InvalidOperation(code="sample_plain")

def uncoded(value):
    raise core.InvalidOperation(f"Value {value} is refused.")

def other():
    raise ValueError("Not a refusal class.")
"""
CATALOG = {"version": 1, "refusals": {"sample_plain": {"message": "x"}}, "terms": []}


def test_gate_accepts_coded_and_ratcheted_refusals():
    entry = {
        "path": "sample.py",
        "function": "uncoded",
        "message": 'f"Value {value} is refused."',
        "scope": "286",
    }
    assert gate({"sample.py": SAMPLE}, [entry], CATALOG) == []


def test_gate_names_an_uncoded_refusal():
    problems = gate({"sample.py": SAMPLE}, [], CATALOG)
    assert len(problems) == 1 and "sample.py:9" in problems[0]


def test_gate_names_a_stale_ratchet_entry():
    stale = {"path": "sample.py", "function": "gone", "message": "Old.", "scope": "286"}
    entry = {
        "path": "sample.py",
        "function": "uncoded",
        "message": 'f"Value {value} is refused."',
        "scope": "286",
    }
    problems = gate({"sample.py": SAMPLE}, [entry, stale], CATALOG)
    assert problems == [
        "ratchet entry is stale (fixed or moved; remove it): sample.py gone 'Old.'"
    ]


def test_gate_names_an_unknown_code():
    problems = gate({"sample.py": SAMPLE}, [], {**CATALOG, "refusals": {}})
    assert any("unknown refusal code 'sample_plain'" in p for p in problems)


def test_no_spec_286_refusal_remains_uncoded():
    """FR-006: every refusal behind the in-scope forms and the chat send path is coded.

    The remaining entries belong to later areas (and to request field validation, which
    spec 286 leaves in English like FastAPI's 422).
    """
    remaining = [e for e in _load_ratchet()["entries"] if e["scope"] != "later"]
    assert remaining == []
