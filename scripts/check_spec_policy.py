"""Validate the repository's minimum spec-driven development policy."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE_PATTERN = re.compile(r"^specs/\d{3}-[a-z0-9-]+/spec\.md$")
BEHAVIOR_PATHS = (
    # Shared application core, schema and the machine-readable catalogs that define
    # the observable command, event, projection and isolation vocabulary.
    "packages/reality-core/src/",
    "packages/reality-core/migrations/versions/",
    "packages/reality-core/config/",
    # Browser application: Product Web owns the authenticated surface and is
    # observable behavior.
    "apps/web/src/",
    # Deployable runtime boundaries specified by the app-layout and MCP-runtime work.
    "apps/api/",
    "apps/mcp/",
    "compose.yml",
    "compose.dev.yml",
)
REQUIRED_SPEC_SECTIONS = (
    "## Context and Intent",
    "## User Scenarios & Testing",
    "## Requirements",
    "## Success Criteria",
    "## Requirement Traceability",
)
REQUIRED_SPEC_LANGUAGE = "**Language**: English"
# The Constitution requires non-goals and assumptions in every specification. The
# established convention nests non-goals under "Context and Intent", so the heading is
# accepted at any level while the assumptions section stays top-level.
REQUIRED_SPEC_HEADINGS = (
    (re.compile(r"^#+\s+Non-Goals\s*$", re.MULTILINE), "Non-Goals"),
    (
        re.compile(r"^##\s+Assumptions and Dependencies\s*$", re.MULTILINE),
        "Assumptions and Dependencies",
    ),
)
BASELINE_IDS = (
    "003-tenant-access",
    "004-master-data",
    "005-source-ingestion",
    "006-documents-evidence",
    "008-commitments-holds",
    "009-inventory-execution",
    "010-order-to-cash",
    "011-procure-to-pay",
    "012-ledger-finance",
    "013-explain-projections",
    "014-agent-interaction",
    "015-demo-scenarios",
    "016-web-product",
)
FEATURE_DIR_PATTERN = re.compile(r"^(\d{3})-[a-z0-9-]+$")
# One historical collision predates this check: 022-auditable-document-line-corrections
# and 022-public-site were numbered independently on parallel branches and are both
# merged. Renaming a merged specification would break its recorded cross-references,
# so this pair stays accepted while every new collision fails.
KNOWN_DUPLICATE_FEATURE_NUMBERS = frozenset({"022"})
REQUIRED_BASELINE_SECTIONS = (
    "## Current Capability Boundary",
    "## Reality Applicability",
    "## Requirement Evidence",
)
EVIDENCE_STATUSES = {
    "Verified as-is",
    "Documented gap",
    "Implemented gap",
    "Intended",
}


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files(base_ref: str | None) -> list[str]:
    if not base_ref:
        return []
    git_lines("rev-parse", "--verify", base_ref)
    return git_lines("diff", "--name-only", f"{base_ref}...HEAD")


def meaningful_spec_exception() -> bool:
    body = os.getenv("PR_BODY", "")
    if re.search(r"(?im)^- Spec impact:\s*restores existing requirement\s*$", body):
        spec = re.search(r"(?im)^- Spec:\s*(.+)$", body)
        requirements = re.search(r"(?im)^- Requirements delivered:\s*(.+)$", body)
        return bool(
            spec
            and requirements
            and re.search(r"\b(?:FR|DR)-\d{3}\b", requirements.group(1))
        )
    if re.search(r"(?im)^- Spec impact:\s*none\s*$", body):
        match = re.search(r"(?im)^- Reason when none:\s*(.+)$", body)
        if not match:
            return False
        reason = match.group(1).strip()
        return reason not in {
            "",
            '<!-- Required; "small change" is not sufficient -->',
        }
    return False


def validate_constitution(errors: list[str]) -> None:
    path = ROOT / ".specify/memory/constitution.md"
    if not path.is_file():
        errors.append("missing .specify/memory/constitution.md")
        return
    text = path.read_text(encoding="utf-8")
    if "[PROJECT_NAME]" in text or "[CONSTITUTION_VERSION]" in text:
        errors.append("constitution still contains bootstrap placeholders")
    for phrase in (
        "Source → Evidence → Reality",
        "Tenant and Service Boundaries",
        "Specification and Test Evidence",
        "**Version**:",
    ):
        if phrase not in text:
            errors.append(
                f"constitution is missing required principle/metadata: {phrase}"
            )


def validate_templates(errors: list[str]) -> None:
    overrides = ROOT / ".specify/templates/overrides"
    for name in (
        "spec-template.md",
        "plan-template.md",
        "tasks-template.md",
        "checklist-template.md",
    ):
        if not (overrides / name).is_file():
            errors.append(f"missing project-local Spec Kit override: {name}")


def validate_spec_text(relative: str, text: str, errors: list[str]) -> None:
    """Validate one numbered specification's stable repository contract."""
    for section in REQUIRED_SPEC_SECTIONS:
        if section not in text:
            errors.append(f"{relative} is missing section: {section}")
    for pattern, heading in REQUIRED_SPEC_HEADINGS:
        if not pattern.search(text):
            errors.append(f"{relative} is missing section: {heading}")
    if REQUIRED_SPEC_LANGUAGE not in text:
        errors.append(f"{relative} must declare repository language as English")
    if not re.search(r"\*\*FR-\d{3}\*\*", text):
        errors.append(f"{relative} has no FR-* requirement")
    if "[NEEDS CLARIFICATION" in text and "**Status**: Draft" not in text:
        errors.append(f"{relative} leaves clarification markers outside Draft status")


def validate_baseline_text(relative: str, text: str, errors: list[str]) -> None:
    """Validate the stronger as-is baseline evidence contract."""
    validate_spec_text(relative, text, errors)
    for section in REQUIRED_BASELINE_SECTIONS:
        if section not in text:
            errors.append(f"{relative} is missing baseline section: {section}")
    if "**Status**: Reviewed" not in text:
        errors.append(f"{relative} baseline must be Reviewed after owner approval")
    if "[NEEDS CLARIFICATION" in text:
        errors.append(f"{relative} reviewed baseline contains a clarification marker")
    evidence_section = text.split("## Requirement Evidence", 1)[-1].split(
        "## Requirement Traceability", 1
    )[0]
    rows = re.findall(
        r"^\|\s*(FR-\d{3}(?:–FR-\d{3})?|DR-\d{3}(?:–DR-\d{3})?)\s*"
        r"\|\s*([^|]+?)\s*\|",
        evidence_section,
        flags=re.MULTILINE,
    )
    if not rows:
        errors.append(f"{relative} has no Requirement Evidence rows")
    for requirement, status in rows:
        if status.strip() not in EVIDENCE_STATUSES:
            errors.append(
                f"{relative} requirement {requirement} has invalid evidence status: "
                f"{status.strip()}"
            )


def validate_feature_specs(errors: list[str]) -> None:
    specs = ROOT / "specs"
    if not specs.exists():
        return
    for spec in sorted(specs.glob("[0-9][0-9][0-9]-*/spec.md")):
        relative = spec.relative_to(ROOT).as_posix()
        if not FEATURE_PATTERN.match(relative):
            errors.append(f"invalid feature spec path: {relative}")
        text = spec.read_text(encoding="utf-8")
        baseline_id = spec.parent.name
        if baseline_id in BASELINE_IDS:
            validate_baseline_text(relative, text, errors)
        else:
            validate_spec_text(relative, text, errors)


def validate_feature_numbers(errors: list[str]) -> None:
    """Ensure one feature number identifies exactly one specification.

    Spec Kit derives the next number from the `specs/` directory of the current
    checkout, so parallel branches can claim the same number without noticing.
    `scripts/next_feature_number.py` widens that search; this check makes a
    surviving collision fail before it reaches the default branch.
    """
    specs = ROOT / "specs"
    if not specs.is_dir():
        return
    owners: dict[str, list[str]] = {}
    for entry in sorted(specs.iterdir()):
        if not entry.is_dir():
            continue
        match = FEATURE_DIR_PATTERN.match(entry.name)
        if not match:
            errors.append(f"invalid feature directory name: specs/{entry.name}")
            continue
        if not (entry / "spec.md").is_file():
            errors.append(
                f"specs/{entry.name} claims a feature number without a spec.md; "
                "complete or remove the directory"
            )
            continue
        owners.setdefault(match.group(1), []).append(entry.name)
    for number, names in sorted(owners.items()):
        if len(names) > 1 and number not in KNOWN_DUPLICATE_FEATURE_NUMBERS:
            errors.append(
                f"feature number {number} is claimed by more than one specification: "
                f"{', '.join(names)}; derive the next number with "
                "scripts/next_feature_number.py"
            )


def _catalog_table_names(catalog_text: str) -> set[str]:
    in_tables = False
    names: set[str] = set()
    for line in catalog_text.splitlines():
        if line == "tables:":
            in_tables = True
            continue
        if in_tables:
            match = re.match(r"^  ([a-z][a-z0-9_]*):$", line)
            if match:
                names.add(match.group(1))
            elif line and not line.startswith(" "):
                break
    return names


def validate_coverage_matrix(errors: list[str]) -> None:
    """Ensure every deterministic baseline source family has a matrix owner."""
    path = ROOT / "docs/SPEC_COVERAGE_MATRIX.md"
    if not path.is_file():
        errors.append("missing docs/SPEC_COVERAGE_MATRIX.md")
        return
    text = path.read_text(encoding="utf-8")
    if REQUIRED_SPEC_LANGUAGE not in text:
        errors.append("docs/SPEC_COVERAGE_MATRIX.md must declare English")
    for baseline_id in BASELINE_IDS:
        if baseline_id not in text:
            errors.append(f"coverage matrix is missing baseline: {baseline_id}")
    for contract in sorted((ROOT / "docs/features").glob("*.md")):
        relative = contract.relative_to(ROOT).as_posix()
        if relative not in text:
            errors.append(f"coverage matrix is missing feature contract: {relative}")
    catalog_path = ROOT / "packages/reality-core/config/data_model.yaml"
    if not catalog_path.is_file():
        errors.append("missing packages/reality-core/config/data_model.yaml")
    else:
        for table in sorted(
            _catalog_table_names(catalog_path.read_text(encoding="utf-8"))
        ):
            if f"`{table}`" not in text:
                errors.append(f"coverage matrix is missing catalog table: {table}")
    tests_root = ROOT / "packages/reality-core/tests"
    for test in sorted(tests_root.glob("test_*.py")) + sorted(
        tests_root.glob("*/test_*.py")
    ):
        relative = test.relative_to(ROOT).as_posix()
        if relative not in text:
            errors.append(f"coverage matrix is missing test family: {relative}")


def validate_change_policy(files: list[str], errors: list[str]) -> None:
    behavior_changed = any(path.startswith(BEHAVIOR_PATHS) for path in files)
    spec_changed = any(FEATURE_PATTERN.match(path) for path in files)
    if behavior_changed and not spec_changed and not meaningful_spec_exception():
        errors.append(
            "observable-code paths changed without a numbered feature spec; "
            "add specs/NNN-feature/spec.md or declare a concrete 'Spec impact: none' "
            "reason in the pull request"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-ref", help="Git ref used to enforce changed-file policy"
    )
    args = parser.parse_args()
    errors: list[str] = []
    validate_constitution(errors)
    validate_templates(errors)
    validate_feature_specs(errors)
    validate_feature_numbers(errors)
    validate_coverage_matrix(errors)
    try:
        files = changed_files(args.base_ref)
    except RuntimeError as error:
        errors.append(str(error))
        files = []
    validate_change_policy(files, errors)
    if errors:
        print("Spec policy failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    suffix = f" across {len(files)} changed file(s)" if args.base_ref else ""
    print(f"Spec policy passed{suffix}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
