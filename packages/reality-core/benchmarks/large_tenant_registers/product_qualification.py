"""Fail-closed fixture J qualification for integrated product measurements.

This module deliberately does not know how to manufacture measurements.  The product
harness records service/tool results; this evaluator prevents partial, reduced or
prototype evidence from becoming a green release gate.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

WORKLOAD_BUDGETS = {
    "order": 0.5,
    "inventory": 2.0,
    "monthly": 3.0,
    "exceptions": 2.0,
    "mcp": 3.0,
}

EXPECTED_CARDINALITIES = {
    "orders": 100_000,
    "items": 10_000,
    "movements": 1_000_000,
    "components": 1_000_000,
    "attribution_parts": 1_000_000,
    "matching_parts": 600_000,
}


def _require(condition: bool, reason: str, refusals: list[str]) -> None:
    if not condition:
        refusals.append(reason)


def evaluate(report: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic qualification decision and all refusal reasons."""
    refusals: list[str] = []
    _require(report.get("schema") == "reality.fixture-j.product.v1", "schema", refusals)
    _require(report.get("profile") == "full", "full_profile", refusals)
    _require(report.get("seed") == 234, "seed", refusals)
    _require(report.get("business_date") == "2026-09-18", "business_date", refusals)
    _require(report.get("entrypoints") == "product", "product_entrypoints", refusals)

    environment = report.get("environment") or {}
    _require(environment.get("dedicated") is True, "dedicated_host", refusals)
    _require(environment.get("cpu_limit") == 4, "cpu_limit", refusals)
    _require(environment.get("memory_limit_bytes") == 16 * 1024**3, "memory_limit", refusals)
    _require(environment.get("local_ssd") is True, "local_ssd", refusals)
    _require(bool(environment.get("postgres_version")), "postgres_version", refusals)
    _require(bool(environment.get("git_revision")), "git_revision", refusals)
    _require(bool(environment.get("resource_samples")), "resource_samples", refusals)

    cardinalities = report.get("cardinalities") or {}
    _require(set(cardinalities) == {"primary", "control"}, "two_tenants", refusals)
    for tenant in ("primary", "control"):
        actual = cardinalities.get(tenant) or {}
        for family, expected in EXPECTED_CARDINALITIES.items():
            _require(actual.get(family) == expected, f"{tenant}_{family}", refusals)

    measurements = report.get("measurements") or {}
    for name, budget in WORKLOAD_BUDGETS.items():
        measurement = measurements.get(name) or {}
        _require(measurement.get("warmups") == 20, f"{name}_warmups", refusals)
        _require(measurement.get("samples") == 200, f"{name}_samples", refusals)
        _require(measurement.get("errors") == 0, f"{name}_errors", refusals)
        _require(measurement.get("cold_s") is not None, f"{name}_cold", refusals)
        _require(
            isinstance(measurement.get("cold_s"), (int, float))
            and measurement.get("cold_s") <= budget,
            f"{name}_cold_budget",
            refusals,
        )
        _require(
            isinstance(measurement.get("p95_s"), (int, float))
            and measurement.get("p95_s") <= budget,
            f"{name}_p95_budget",
            refusals,
        )
        _require(bool(measurement.get("serialized_sha256")), f"{name}_serialization", refusals)
        _require(bool(measurement.get("query_evidence")), f"{name}_query_evidence", refusals)

    isolation = report.get("tenant_isolation") or {}
    _require(isolation.get("probes") == 5, "tenant_isolation_probes", refusals)
    _require(isolation.get("leaks") == 0, "tenant_isolation", refusals)

    reconstruction = report.get("reconstruction") or {}
    runs = reconstruction.get("runs") or []
    _require(len(runs) == 3, "reconstruction_runs", refusals)
    if len(runs) == 3:
        _require(runs[0].get("cold_cache") is True, "cold_reconstruction", refusals)
        _require(
            all(isinstance(r.get("duration_s"), (int, float)) and r["duration_s"] <= 120 for r in runs),
            "reconstruction_budget",
            refusals,
        )
        _require(len({r.get("checksum") for r in runs}) == 1 and bool(runs[0].get("checksum")), "reconstruction_equality", refusals)
    _require(reconstruction.get("atomic_publication") is True, "atomic_publication", refusals)
    _require(reconstruction.get("failure_retry_recovered") is True, "worker_recovery", refusals)

    refresh = report.get("refresh") or {}
    _require(refresh.get("changes") == 30, "refresh_changes", refusals)
    _require(refresh.get("highest_volume_scopes") is True, "refresh_scope", refusals)
    _require(refresh.get("one_change_per_second") is True, "refresh_rate", refusals)
    _require(
        isinstance(refresh.get("p95_s"), (int, float)) and refresh.get("p95_s") <= 30,
        "refresh_budget",
        refusals,
    )
    _require(refresh.get("watermark_correct") is True, "refresh_watermark", refusals)
    _require(report.get("concurrent_readers") == 5, "concurrent_readers", refusals)
    _require(report.get("projection_workers") == 1, "projection_worker", refusals)
    _require(report.get("complete_reconstruction_from_retained_inputs") is True, "retained_reconstruction", refusals)
    return {"qualification_passed": not refusals, "refusals": refusals}

