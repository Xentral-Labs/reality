"""The fixture J release gate cannot turn partial evidence green."""

from copy import deepcopy

from benchmarks.large_tenant_registers.product_qualification import (
    EXPECTED_CARDINALITIES,
    WORKLOAD_BUDGETS,
    evaluate,
)


def complete_report():
    return {
        "schema": "reality.fixture-j.product.v1",
        "profile": "full",
        "seed": 234,
        "business_date": "2026-09-18",
        "entrypoints": "product",
        "environment": {
            "dedicated": True,
            "cpu_limit": 4,
            "memory_limit_bytes": 16 * 1024**3,
            "local_ssd": True,
            "postgres_version": "17.1",
            "git_revision": "abc123",
            "resource_samples": [{"rss_bytes": 1, "io_bytes": 1}],
        },
        "cardinalities": {
            "primary": dict(EXPECTED_CARDINALITIES),
            "control": dict(EXPECTED_CARDINALITIES),
        },
        "measurements": {
            name: {
                "warmups": 20,
                "samples": 200,
                "errors": 0,
                "cold_s": budget,
                "p95_s": budget,
                "serialized_sha256": "0" * 64,
                "query_evidence": {"statements": 1, "rows": 1},
            }
            for name, budget in WORKLOAD_BUDGETS.items()
        },
        "tenant_isolation": {"probes": 5, "leaks": 0},
        "reconstruction": {
            "runs": [
                {"cold_cache": True, "duration_s": 120, "checksum": "same"},
                {"cold_cache": False, "duration_s": 120, "checksum": "same"},
                {"cold_cache": False, "duration_s": 120, "checksum": "same"},
            ],
            "atomic_publication": True,
            "failure_retry_recovered": True,
        },
        "refresh": {
            "changes": 30,
            "highest_volume_scopes": True,
            "one_change_per_second": True,
            "p95_s": 30,
            "watermark_correct": True,
        },
        "concurrent_readers": 5,
        "projection_workers": 1,
        "complete_reconstruction_from_retained_inputs": True,
    }


def test_complete_boundary_evidence_passes():
    assert evaluate(complete_report()) == {"qualification_passed": True, "refusals": []}


def test_reduced_or_prototype_evidence_cannot_pass():
    report = complete_report()
    report["profile"] = "reduced"
    report["entrypoints"] = "costing_spike"
    report["measurements"]["order"]["samples"] = 199
    result = evaluate(report)
    assert result["qualification_passed"] is False
    assert {"full_profile", "product_entrypoints", "order_samples"} <= set(
        result["refusals"]
    )


def test_each_budget_and_required_proof_fails_closed():
    cases = []
    for name, budget in WORKLOAD_BUDGETS.items():
        cases.append(
            (f"{name}_p95_budget", ("measurements", name, "p95_s"), budget + 0.001)
        )
    cases += [
        ("tenant_isolation", ("tenant_isolation", "leaks"), 1),
        (
            "reconstruction_equality",
            ("reconstruction", "runs", 2, "checksum"),
            "different",
        ),
        ("refresh_budget", ("refresh", "p95_s"), 30.001),
    ]
    for refusal, path, value in cases:
        report = deepcopy(complete_report())
        target = report
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        assert refusal in evaluate(report)["refusals"]


def test_missing_resource_and_query_evidence_is_rejected():
    report = complete_report()
    report["environment"]["resource_samples"] = []
    report["measurements"]["exceptions"]["query_evidence"] = {}
    assert {"resource_samples", "exceptions_query_evidence"} <= set(
        evaluate(report)["refusals"]
    )
