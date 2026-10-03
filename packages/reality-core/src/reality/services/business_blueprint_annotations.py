"""Read bounded, source-authored business descriptions without external inference.

Descriptions are reviewed commentary, not executed rules or coverage measurements.
Every displayed rule binds to an actual node in its verified source function.
"""

from __future__ import annotations

import ast
import re
import textwrap

from reality.domain.business_blueprints import (
    BusinessOverview,
    BusinessPresentation,
    BusinessScenario,
    BusinessStep,
    RuleNode,
    SourceEvidence,
    TestScenario,
)

HEADER = re.compile(
    r"^(BUSINESS (?:PURPOSE|TEST|RULES|RULE [\w.:-]+)|GIVEN|WHEN|THEN):\s*$"
)
MAX_DOC_BYTES = 24_000
MAX_SECTION_BYTES = 4_000


def sections(code: str, *, test: bool = False) -> dict[str, str]:
    """Parse only a function docstring; source text is never executed."""
    tree = ast.parse(textwrap.dedent(code))
    function = next(
        n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    doc = ast.get_docstring(function) or ""
    if "BUSINESS " not in doc:
        return {}
    if len(doc.encode()) > MAX_DOC_BYTES:
        raise ValueError("Description exceeds the docstring size limit")
    result: dict[str, list[str]] = {}
    key = None
    for line in doc.splitlines():
        stripped = line.strip()
        match = HEADER.fullmatch(stripped)
        if match and not test and match.group(1) in {"GIVEN", "WHEN", "THEN"}:
            # Conditional THEN labels are prose inside a function's rule section.
            match = None
        if match:
            key = match.group(1)
            allowed = (
                key in {"BUSINESS TEST", "GIVEN", "WHEN", "THEN", "BUSINESS RULES"}
                if test
                else key == "BUSINESS PURPOSE" or key.startswith("BUSINESS RULE ")
            )
            if not allowed or key in result:
                raise ValueError("Unknown or duplicate business description section")
            result[key] = []
        elif stripped.startswith("BUSINESS "):
            raise ValueError("Malformed business description section")
        elif key:
            result[key].append(line)
    values = {
        key: textwrap.dedent("\n".join(lines)).strip() for key, lines in result.items()
    }
    required = (
        {"BUSINESS TEST", "GIVEN", "WHEN", "THEN"} if test else {"BUSINESS PURPOSE"}
    )
    if not required <= values.keys() or any(
        not v or len(v.encode()) > MAX_SECTION_BYTES for v in values.values()
    ):
        raise ValueError("Missing, empty or oversized business description section")
    return values


def statements(value: str) -> tuple[str, ...]:
    return tuple(
        line.strip().removeprefix("- ") for line in value.splitlines() if line.strip()
    )


def describe(
    nodes: tuple[RuleNode, ...],
    sources: tuple[SourceEvidence, ...],
    scenarios: tuple[TestScenario, ...],
) -> BusinessPresentation:
    """Return exact English commentary with independently checked source bindings."""
    steps = []
    overviews = []
    tests = []
    gaps = []
    known_rules = {node.id for node in nodes}
    explained = set()
    for source in sources:
        try:
            doc = sections(source.code)
            if not doc:
                gaps.append("Function description missing: " + source.function)
                continue
            own = {node.id: node for node in nodes if node.evidence_id == source.id}
            referenced = {
                key.removeprefix("BUSINESS RULE ")
                for key in doc
                if key.startswith("BUSINESS RULE ")
            }
            if not referenced <= own.keys():
                raise ValueError("Description references a rule outside this function")
            overviews.append((source, doc["BUSINESS PURPOSE"]))
            for key, text in doc.items():
                if not key.startswith("BUSINESS RULE "):
                    continue
                rule = own[key.removeprefix("BUSINESS RULE ")]
                steps.append(
                    BusinessStep(
                        id=rule.id,
                        function=source.function,
                        kind=rule.kind,
                        text=text,
                        rule_ids=(rule.id,),
                        evidence_ids=(source.id,),
                        line=rule.line,
                    )
                )
                explained.add(rule.id)
        except (ValueError, SyntaxError, StopIteration) as error:
            gaps.append(f"Invalid function description: {source.function}: {error}")
    for scenario in scenarios:
        try:
            doc = sections(scenario.code, test=True)
            if not doc:
                gaps.append("Test description missing: " + scenario.id)
                continue
            references = set(statements(doc.get("BUSINESS RULES", "")))
            unresolved = references - known_rules
            if unresolved:
                gaps.append(
                    "Test rule references not present in this read: "
                    + scenario.id
                    + ": "
                    + ", ".join(sorted(unresolved))
                )
            tests.append(
                BusinessScenario(
                    id=scenario.id,
                    title=doc["BUSINESS TEST"],
                    given=statements(doc["GIVEN"]),
                    when=statements(doc["WHEN"]),
                    then=statements(doc["THEN"]),
                    notice="Authored test description; test not executed by this read. See original assertions and recorded run evidence.",
                    unexplained_assertions=len(scenario.expectations),
                )
            )
        except (ValueError, SyntaxError, StopIteration) as error:
            gaps.append(f"Invalid test description: {scenario.id}: {error}")
    # A helper purpose must not masquerade as the purpose of an unannotated entry.
    primary = next(
        (text for source, text in overviews if sources and source.id == sources[0].id),
        None,
    )
    overview = (
        BusinessOverview(text=primary, evidence_ids=(sources[0].id,))
        if primary
        else None
    )
    return BusinessPresentation(
        language="en",
        heading="Steps and rules from source descriptions",
        notice="Authored English descriptions read from current source. No AI generation. Descriptions do not prove code correctness or passing tests.",
        mode="authored" if overviews or steps or tests else "unavailable",
        overview=overview,
        steps=tuple(steps),
        scenarios=tuple(tests),
        unexplained_rules=len(known_rules - explained),
        annotation_gaps=tuple(gaps),
    )
