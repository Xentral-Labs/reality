from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from benchmarks.large_tenant_registers.cases import (
    REQUIRED_FAMILIES,
    build_case_catalog,
    run_catalog,
)
from benchmarks.large_tenant_registers.dataset import (
    DatasetProfile,
    build_dataset,
    validate_dataset,
)
from benchmarks.large_tenant_registers.report import (
    BenchmarkResult,
    semantic_result,
)
from benchmarks.large_tenant_registers.runner import validate_database_target


def test_case_catalog_covers_every_core_register_and_requirements():
    catalog = build_case_catalog()
    assert tuple(case.family for case in catalog) == REQUIRED_FAMILIES
    assert len({case.case_id for case in catalog}) == len(catalog)
    assert all(case.requirements for case in catalog)


def test_database_target_requires_all_safety_guards():
    validate_database_target("reality_benchmark_local", confirmed=True, is_empty=True)
    validate_database_target(
        "reality_benchmark_local", confirmed=True, is_empty=False, reuse=True
    )
    with pytest.raises(ValueError, match="reality_benchmark_"):
        validate_database_target("reality", confirmed=True, is_empty=True)
    with pytest.raises(ValueError, match="confirm-disposable"):
        validate_database_target(
            "reality_benchmark_local", confirmed=False, is_empty=True
        )
    with pytest.raises(ValueError, match="empty"):
        validate_database_target(
            "reality_benchmark_local", confirmed=True, is_empty=False
        )


def test_reduced_dataset_is_complete_traceable_and_repeatable(session):
    profile = DatasetProfile.reduced(seed=32010, business_date=date(2026, 9, 1))
    dataset = build_dataset(session, profile)
    validation = validate_dataset(session, dataset)

    assert validation["orders"] == profile.order_count
    assert validation["source_records"] >= profile.order_count
    assert validation["document_lines"] >= profile.order_count
    assert validation["document_lines"] > profile.order_count
    assert validation["commitments"] >= profile.order_count
    assert validation["items"] > 100
    assert validation["reservations"] > 100
    assert validation["movements"] > 100
    assert validation["ledger_entries"] > 100

    first = run_catalog(session, dataset)
    second = run_catalog(session, dataset)
    assert len(first) == len(REQUIRED_FAMILIES)
    assert all(observation.outcome == "passed" for observation in first)
    assert semantic_result(first) == semantic_result(second)


def test_result_model_is_complete_redacted_and_schema_stable(session):
    profile = DatasetProfile.reduced(seed=7, business_date=date(2026, 9, 1))
    dataset = build_dataset(session, profile)
    observations = run_catalog(session, dataset)
    result = BenchmarkResult.from_run(
        dataset, observations, git_revision="abcdef012345"
    )

    payload = result.model_dump(mode="json")
    assert payload["outcome"] == "passed"
    assert payload["dataset"]["cardinalities"]["orders"] == profile.order_count
    assert "password" not in result.model_dump_json().lower()
    assert (
        BenchmarkResult.model_json_schema()["title"]
        == "Large-Tenant Register Benchmark Result"
    )


def test_checked_in_result_schema_matches_model_contract():
    contract = json.loads(
        (
            Path(__file__).parents[3]
            / "specs/033-large-tenant-register-benchmark/contracts/benchmark-result.schema.json"
        ).read_text(encoding="utf-8")
    )
    generated = BenchmarkResult.model_json_schema()
    assert contract == generated
