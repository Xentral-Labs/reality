from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "scripts/check_spec_policy.py"
SPEC = importlib.util.spec_from_file_location("check_spec_policy", POLICY_PATH)
assert SPEC is not None and SPEC.loader is not None
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


def test_repository_spec_policy_passes() -> None:
    result = subprocess.run(
        ["python3", str(POLICY_PATH)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_baseline_contract_rejects_missing_sections_status_and_evidence() -> None:
    errors: list[str] = []
    policy.validate_baseline_text(
        "specs/999-example/spec.md",
        """**Language**: English
**Status**: Draft
## Context and Intent
## User Scenarios & Testing
## Requirements
- **FR-001**: Example.
## Success Criteria
## Requirement Traceability""",
        errors,
    )
    assert any("Current Capability Boundary" in error for error in errors)
    assert any("Reality Applicability" in error for error in errors)
    assert any("Requirement Evidence" in error for error in errors)
    assert any("must be Reviewed" in error for error in errors)
    assert any("no Requirement Evidence rows" in error for error in errors)


def test_baseline_contract_rejects_unknown_evidence_status() -> None:
    errors: list[str] = []
    text = """**Language**: English
**Status**: Reviewed
## Context and Intent
## Current Capability Boundary
## User Scenarios & Testing
## Requirements
- **FR-001**: Example.
## Reality Applicability
## Success Criteria
## Requirement Evidence
| Requirement | Status | Contract | Implementation | Executable proof | Gap |
|---|---|---|---|---|---|
| FR-001 | Probably | contract | service | test | — |
## Requirement Traceability"""
    policy.validate_baseline_text("specs/999-example/spec.md", text, errors)
    assert any("invalid evidence status: Probably" in error for error in errors)


def test_data_model_catalog_parser_returns_only_table_keys() -> None:
    tables = policy._catalog_table_names(
        (ROOT / "packages/reality-core/config/data_model.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert {"tenant", "source_record", "document", "commitment", "movement"} <= tables
    assert "common_columns" not in tables


def test_localization_evidence_is_verified_without_hiding_other_gaps() -> None:
    web_baseline = (ROOT / "specs/016-web-product/spec.md").read_text(encoding="utf-8")
    coverage = (ROOT / "docs/SPEC_COVERAGE_MATRIX.md").read_text(encoding="utf-8")

    assert "| FR-013 | Verified as-is |" in web_baseline
    assert "| FR-006 | Verified as-is |" in web_baseline
    assert "| FR-015 | Verified as-is |" in web_baseline
    assert "| `016/FR-013` |" not in coverage
    assert "| `016/FR-006` |" not in coverage
    assert "No accepted documented gaps remain" in coverage
    assert "Spec 033" in coverage


def test_tenant_isolation_evidence_is_verified_without_hiding_other_gaps() -> None:
    tenant_baseline = (ROOT / "specs/003-tenant-access/spec.md").read_text(
        encoding="utf-8"
    )
    coverage = (ROOT / "docs/SPEC_COVERAGE_MATRIX.md").read_text(encoding="utf-8")

    assert "| FR-012 | Verified as-is |" in tenant_baseline
    assert "tenant_isolation_catalog.yaml" in tenant_baseline
    assert "| `003/FR-012` |" not in coverage
    assert "| `004/FR-016` |" not in coverage
    assert "| `015/FR-010` |" not in coverage
    assert "No accepted documented gaps remain" in coverage


def test_exception_coverage_is_verified_without_hiding_other_gaps() -> None:
    baseline = (ROOT / "specs/013-explain-projections/spec.md").read_text(
        encoding="utf-8"
    )
    coverage = (ROOT / "docs/SPEC_COVERAGE_MATRIX.md").read_text(encoding="utf-8")

    assert "| FR-005 | Verified as-is |" in baseline
    assert "operational_exception_catalog.yaml" in coverage
    assert "| `013/FR-005` |" not in coverage
    assert "| `004/FR-016` |" not in coverage
    assert "| `015/FR-010` |" not in coverage
    assert "No accepted documented gaps remain" in coverage


def test_historical_pricing_is_verified_without_hiding_other_gaps() -> None:
    baseline = (ROOT / "specs/004-master-data/spec.md").read_text(encoding="utf-8")
    coverage = (ROOT / "docs/SPEC_COVERAGE_MATRIX.md").read_text(encoding="utf-8")

    assert "| FR-014 | Verified as-is |" in baseline
    assert "specs/025-historical-pricing-integrity/spec.md" in baseline
    assert "| `004/FR-014` |" not in coverage
    assert "| `015/FR-010` |" not in coverage
    assert "No accepted documented gaps remain" in coverage


def test_master_data_adapter_parity_is_verified_without_hiding_other_gaps() -> None:
    baseline = (ROOT / "specs/004-master-data/spec.md").read_text(encoding="utf-8")
    coverage = (ROOT / "docs/SPEC_COVERAGE_MATRIX.md").read_text(encoding="utf-8")

    assert "| FR-016 | Verified as-is |" in baseline
    assert "specs/026-master-data-adapter-parity/spec.md" in baseline
    assert "| `004/FR-016` |" not in coverage
    assert "| `015/FR-010` |" not in coverage
    assert "| `016/FR-006` |" not in coverage
    assert "No accepted documented gaps remain" in coverage


def test_demo_entrypoint_equivalence_is_verified_without_hiding_web_gaps() -> None:
    baseline = (ROOT / "specs/015-demo-scenarios/spec.md").read_text(encoding="utf-8")
    coverage = (ROOT / "docs/SPEC_COVERAGE_MATRIX.md").read_text(encoding="utf-8")

    assert "| FR-010 | Verified as-is |" in baseline
    assert "tests/test_demo_entrypoint_parity.py" in baseline
    assert "| `015/FR-010` |" not in coverage
    assert "| `016/FR-006` |" not in coverage
    assert "No accepted documented gaps remain" in coverage


def test_web_ux_matrix_and_large_tenant_proofs_are_independently_verified() -> None:
    baseline = (ROOT / "specs/016-web-product/spec.md").read_text(encoding="utf-8")
    coverage = (ROOT / "docs/SPEC_COVERAGE_MATRIX.md").read_text(encoding="utf-8")

    assert "| FR-006 | Verified as-is |" in baseline
    assert "Spec 030 evidence accepted 2026-09-02" in baseline
    assert "| FR-015 | Verified as-is |" in baseline
    assert "| `016/FR-006` |" not in coverage
    assert "No accepted documented gaps remain" in coverage
    assert "Spec 033" in baseline


def test_current_runtime_contract_is_http_only_and_separately_owned() -> None:
    supported_sources = (
        ROOT / "packages/reality-core/src/reality/cli/app.py",
        ROOT / "packages/reality-core/src/reality/agent/mcp_chat.py",
        ROOT / "packages/reality-core/src/reality/mcp/server.py",
        ROOT / "README.md",
        ROOT / "docs/ARCHITECTURE.md",
        ROOT / "docs/CLI_SPEC.md",
        ROOT / "docs/WEB_SPEC.md",
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in supported_sources)
    assert "mcp.client.stdio" not in combined
    assert "StdioServerParameters" not in combined
    assert 'command("mcp")' not in combined
    assert "python -m reality.mcp.server" not in combined

    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "shared application" in architecture.lower()
    assert "operation context" in architecture.lower()
    assert "not business truth" in architecture.lower()


def _feature_dir(specs: Path, name: str, *, with_spec: bool = True) -> None:
    directory = specs / name
    directory.mkdir(parents=True)
    if with_spec:
        (directory / "spec.md").write_text("placeholder", encoding="utf-8")


def test_feature_number_collision_is_rejected(tmp_path, monkeypatch) -> None:
    specs = tmp_path / "specs"
    _feature_dir(specs, "026-first-parallel-change")
    _feature_dir(specs, "026-second-parallel-change")
    monkeypatch.setattr(policy, "ROOT", tmp_path)

    errors: list[str] = []
    policy.validate_feature_numbers(errors)

    assert any(
        "feature number 026 is claimed by more than one specification" in error
        for error in errors
    )
    assert any("next_feature_number.py" in error for error in errors)


def test_accepted_historical_collision_does_not_fail(tmp_path, monkeypatch) -> None:
    specs = tmp_path / "specs"
    _feature_dir(specs, "022-auditable-document-line-corrections")
    _feature_dir(specs, "022-public-site")
    monkeypatch.setattr(policy, "ROOT", tmp_path)

    errors: list[str] = []
    policy.validate_feature_numbers(errors)

    assert errors == []


def test_feature_directory_without_specification_is_rejected(
    tmp_path, monkeypatch
) -> None:
    specs = tmp_path / "specs"
    _feature_dir(specs, "027-leftover-directory", with_spec=False)
    monkeypatch.setattr(policy, "ROOT", tmp_path)

    errors: list[str] = []
    policy.validate_feature_numbers(errors)

    assert any("claims a feature number without a spec.md" in error for error in errors)


def test_browser_catalog_and_runtime_paths_require_a_specification(
    monkeypatch,
) -> None:
    monkeypatch.setenv("PR_BODY", "")
    for path in (
        "apps/web/src/App.tsx",
        "packages/reality-core/config/command_catalog.yaml",
        "apps/mcp/Dockerfile",
        "compose.yml",
    ):
        errors: list[str] = []
        policy.validate_change_policy([path], errors)
        assert errors, f"{path} must require a specification or a stated reason"


def test_stated_reason_still_permits_a_documentation_only_change(monkeypatch) -> None:
    monkeypatch.setenv(
        "PR_BODY",
        "- Spec impact: none\n- Reason when none: relocates a non-contract document\n",
    )
    errors: list[str] = []
    policy.validate_change_policy(["apps/web/src/App.tsx"], errors)

    assert errors == []


def test_web_ux_matrix_keeps_browser_presentation_only_and_schema_unchanged() -> None:
    web_sources = tuple((ROOT / "apps/web/src").rglob("*.ts")) + tuple(
        (ROOT / "apps/web/src").rglob("*.tsx")
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in web_sources)
    assert "session.add(" not in combined
    assert "create_engine(" not in combined
    assert "CREATE TABLE" not in combined

    plan = (ROOT / "specs/030-web-ux-matrix-completion/plan.md").read_text(
        encoding="utf-8"
    )
    manifest = (ROOT / "apps/web/scripts/fixtures/ux-matrix-v1.json").read_text(
        encoding="utf-8"
    )
    assert "no schema/migration planned" in plan
    assert '"authority": "verification_only"' in manifest


def _spec_text(*, non_goals: str = "### Non-Goals", assumptions: bool = True) -> str:
    """A minimal specification body that satisfies every other policy rule."""
    sections = [
        "**Language**: English",
        "**Status**: Draft",
        "## Context and Intent",
        non_goals,
        "## User Scenarios & Testing",
        "## Requirements",
        "- **FR-001**: Example.",
    ]
    if assumptions:
        sections.append("## Assumptions and Dependencies")
    sections += ["## Success Criteria", "## Requirement Traceability"]
    return "\n".join(section for section in sections if section)


def test_specification_without_non_goals_is_rejected() -> None:
    errors: list[str] = []
    policy.validate_spec_text(
        "specs/999-example/spec.md", _spec_text(non_goals=""), errors
    )
    assert any("missing section: Non-Goals" in error for error in errors)


def test_specification_without_assumptions_is_rejected() -> None:
    errors: list[str] = []
    policy.validate_spec_text(
        "specs/999-example/spec.md", _spec_text(assumptions=False), errors
    )
    assert any(
        "missing section: Assumptions and Dependencies" in error for error in errors
    )


def test_non_goals_is_accepted_at_either_nesting_level() -> None:
    for heading in ("### Non-Goals", "## Non-Goals"):
        errors: list[str] = []
        policy.validate_spec_text(
            "specs/999-example/spec.md", _spec_text(non_goals=heading), errors
        )
        assert errors == [], f"{heading} must satisfy the requirement"


def test_every_specification_carries_both_mandatory_sections() -> None:
    """The Constitution requires non-goals and assumptions in every specification."""
    for spec in sorted((ROOT / "specs").glob("[0-9][0-9][0-9]-*/spec.md")):
        text = spec.read_text(encoding="utf-8")
        assert re.search(r"^#+\s+Non-Goals\s*$", text, re.MULTILINE), spec.name
        assert "## Assumptions and Dependencies" in text, spec.name


def test_large_tenant_benchmark_closes_only_the_read_gap() -> None:
    baseline = (ROOT / "specs/016-web-product/spec.md").read_text(encoding="utf-8")
    capacity_idea = (ROOT / "docs/ideas/ecommerce-capacity-baseline.md").read_text(
        encoding="utf-8"
    )
    coverage = (ROOT / "docs/SPEC_COVERAGE_MATRIX.md").read_text(encoding="utf-8")

    assert "| FR-015 | Verified as-is |" in baseline
    assert "Spec 033" in baseline
    assert "No accepted documented gaps remain" in coverage
    assert "Established groundwork from Spec 033" in capacity_idea
    assert "does **not** prove production-shaped ingestion throughput" in capacity_idea
    assert "AWS capacity/cost" in capacity_idea
