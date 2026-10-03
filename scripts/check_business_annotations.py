"""Validate in-source business descriptions and report incremental preparation gaps.

This reads repository AST for authoring review, not running-source evidence.
No business handlers, tests or inference providers are executed.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/reality-core/src"))

from reality.domain.business_blueprints import SourceEvidence
from reality.services.business_blueprint_analysis import analyze_function
from reality.services.business_blueprint_annotations import (
    sections,
    statements,
)
from reality.services.business_blueprint_tests import APPROVED_TESTS


def audit(root: Path = ROOT) -> dict:
    source_root = root / "packages/reality-core/src/reality"
    test_root = root / "packages/reality-core/tests"
    errors, descriptions, tests, missing_tests = [], [], [], []
    global_rules = set()
    test_references = []
    files = [
        *source_root.rglob("*.py"),
        *[test_root / name for name in APPROVED_TESTS if name != "conftest.py"],
    ]
    for path in sorted(files):
        if not path.exists():
            continue
        raw = path.read_text()
        tree = ast.parse(raw)
        is_test = path.is_relative_to(test_root)
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            code = ast.get_source_segment(raw, function) or ""
            location = f"{path.relative_to(root)}:{function.lineno}:{function.name}"
            markers = set(re.findall(r"#\s*reality-rule:\s*([\w.:-]+)", code))
            if not is_test:
                global_rules.update(markers)
            try:
                doc = sections(code, test=is_test)
                if not doc:
                    if is_test and function.name.startswith("test_"):
                        missing_tests.append(location)
                    continue
                if is_test:
                    tests.append(location)
                    test_references.extend(
                        (location, ref)
                        for ref in statements(doc.get("BUSINESS RULES", ""))
                    )
                else:
                    source = SourceEvidence(
                        id=location,
                        path=str(path),
                        function=function.name,
                        start_line=function.lineno,
                        end_line=function.end_lineno,
                        digest="authoring-audit",
                        code=code,
                    )
                    nodes, _, _ = analyze_function(source)
                    actual = {node.id for node in nodes}
                    refs = {
                        key.removeprefix("BUSINESS RULE ")
                        for key in doc
                        if key.startswith("BUSINESS RULE ")
                    }
                    if not refs <= actual:
                        raise ValueError(
                            "Unresolved rule references: "
                            + ", ".join(sorted(refs - actual))
                        )
                    descriptions.append(location)
            except (ValueError, SyntaxError, StopIteration) as error:
                errors.append(location + ": " + str(error))
    errors.extend(
        location + ": Unknown rule reference: " + ref
        for location, ref in test_references
        if ref not in global_rules
    )
    # Runtime catalog roots determine the worklist; no narrative is generated.
    import inspect

    from reality.services.business_blueprints import (
        _canonical_handler,
        _inventory,
        _roots,
    )

    # Catalog imports construct an engine but this audit never opens a connection.
    os.environ.setdefault(
        "REALITY_DATABASE_URL", "postgresql+psycopg://localhost/authoring_audit"
    )
    inventory = _inventory()
    root_functions = {}
    missing_bindings = []
    for (kind, key), entry in sorted(inventory.items()):
        roots = _roots(entry, inventory)
        if not roots:
            missing_bindings.append(f"{kind}:{key}")
        for function in roots:
            fn = _canonical_handler(function)
            identity = fn.__module__ + "." + fn.__qualname__
            root_functions.setdefault(identity, {"entries": [], "described": False})[
                "entries"
            ].append(f"{kind}:{key}")
            try:
                root_functions[identity]["described"] = bool(
                    sections(inspect.getsource(fn))
                )
            except (OSError, TypeError, ValueError, SyntaxError, StopIteration):
                pass
    missing_roots = {
        identity: value["entries"]
        for identity, value in root_functions.items()
        if not value["described"]
    }
    return {
        "context": "repository_authoring_audit",
        "entries": len(inventory),
        "root_functions": len(root_functions),
        "described_functions": descriptions,
        "described_tests": tests,
        "missing_root_descriptions": missing_roots,
        "missing_test_descriptions": missing_tests,
        "missing_root_bindings": missing_bindings,
        "errors": errors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Print the full preparation worklist as JSON",
    )
    args = parser.parse_args()
    report = audit()
    if args.coverage:
        print(json.dumps(report, indent=2))
    else:
        print(
            f"{len(report['described_functions'])} described functions; {len(report['described_tests'])} described tests; "
            f"{len(report['missing_root_descriptions'])} root functions and {len(report['missing_test_descriptions'])} approved tests still to prepare."
        )
        for error in report["errors"]:
            print(error, file=sys.stderr)
    sys.exit(bool(report["errors"]))
