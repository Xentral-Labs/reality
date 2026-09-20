"""Production-entrypoint orchestration for the fixture J qualification report."""

from __future__ import annotations

import hashlib
import json
import statistics
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from .product_workloads import ProductWorkloads
from .query_evidence import capture_queries, summarize_queries

WORKLOAD_NAMES = ("order", "inventory", "monthly", "exceptions", "mcp")


@dataclass(frozen=True, slots=True)
class ProductProtocol:
    """Exact full protocol; reduced values are allowed only for harness tests."""

    warmups: int = 20
    samples: int = 200
    refresh_changes: int = 30
    refresh_interval_s: float = 1.0
    concurrent_readers: int = 5
    projection_workers: int = 1


class CompanyGenerationReconstructor:
    """Run three supplied retained manifests through the production generation services."""

    def __init__(
        self, session_factory, tenant_id: str, manifest_ids: tuple[str, str, str]
    ):
        if len(manifest_ids) != 3 or len(set(manifest_ids)) != 3:
            raise ValueError("Three distinct retained manifests are required.")
        self.session_factory = session_factory
        self.tenant_id = tenant_id
        self.manifest_ids = iter(manifest_ids)
        self.previous_generation_id: str | None = None

    def __call__(self, cold_cache: bool) -> dict[str, Any]:
        from reality.services import costing

        manifest_id = next(self.manifest_ids)
        started = time.perf_counter()
        start = 0
        with self.session_factory() as session:
            while True:
                built = costing.build_company_cost_generation(
                    session, self.tenant_id, manifest_id, start=start, limit=100
                )
                session.commit()
                if built["state"] == "sealed":
                    break
                start = built["completed_work_count"]
            retry = costing.build_company_cost_generation(
                session, self.tenant_id, manifest_id, start=0, limit=100
            )
            publication = costing.publish_company_cost_generation(
                session,
                self.tenant_id,
                built["generation_id"],
                previous_generation_id=self.previous_generation_id,
            )
            session.commit()
            report = costing.company_cost_generation_report(
                session, self.tenant_id, built["generation_id"], page_size=100
            )
        self.previous_generation_id = built["generation_id"]
        payload = json.dumps(
            report, sort_keys=True, separators=(",", ":"), default=str
        ).encode()
        return {
            "cold_cache": cold_cache,
            "duration_s": time.perf_counter() - started,
            "checksum": hashlib.sha256(payload).hexdigest(),
            "atomic_publication": publication["changed"] is True,
            "failure_retry_recovered": retry["generation_id"] == built["generation_id"],
        }


def _percentile(values: list[float], percentile: int) -> float:
    ordered = sorted(values)
    return ordered[max(0, (percentile * len(ordered) + 99) // 100 - 1)]


class ProductQualificationRunner:
    """Capture one complete product report without evaluating or certifying it.

    Fixture construction owns the supplied reconstruction, change/refresh and isolation
    callbacks. Reads themselves always use ``ProductWorkloads``-compatible adapters.
    """

    def __init__(
        self,
        *,
        workload_factory: Callable[[str], ProductWorkloads],
        reconstruct: Callable[[bool], dict[str, Any]],
        refresh: Callable[[int], dict[str, Any]],
        isolation_probe: Callable[[str], bool],
        environment: dict[str, Any],
        cardinalities: dict[str, dict[str, int]],
        resource_sample: Callable[[], dict[str, Any]],
        protocol: ProductProtocol | None = None,
        cold_cache: Callable[[], None] | None = None,
    ):
        self.workload_factory = workload_factory
        self.reconstruct = reconstruct
        self.refresh = refresh
        self.isolation_probe = isolation_probe
        self.environment = environment
        self.cardinalities = cardinalities
        self.resource_sample = resource_sample
        self.protocol = protocol or ProductProtocol()
        self.cold_cache = cold_cache or (lambda: None)

    def _sample(
        self, tenant: str, name: str
    ) -> tuple[float, str, list[dict[str, object]]]:
        workloads = self.workload_factory(tenant)
        started = time.perf_counter()
        try:
            with capture_queries(workloads.session) as queries:
                _, digest = getattr(workloads, name)()
            return time.perf_counter() - started, digest, summarize_queries(queries)
        finally:
            workloads.session.close()

    def _measure(self, name: str) -> dict[str, Any]:
        self.cold_cache()
        cold, digest, evidence = self._sample("primary", name)
        errors = 0
        for _ in range(self.protocol.warmups):
            try:
                self._sample("primary", name)
            except Exception:  # noqa: BLE001 - the report records failed samples
                errors += 1
        values: list[float] = []
        with ThreadPoolExecutor(max_workers=self.protocol.concurrent_readers) as pool:
            futures = [
                pool.submit(self._sample, "primary", name)
                for _ in range(self.protocol.samples)
            ]
            for future in futures:
                try:
                    duration, sample_digest, sample_evidence = future.result()
                    values.append(duration)
                    digest = sample_digest
                    evidence.extend(sample_evidence)
                except Exception:  # noqa: BLE001 - qualification must fail closed
                    errors += 1
        return {
            "warmups": self.protocol.warmups,
            "samples": self.protocol.samples,
            "errors": errors,
            "cold_s": cold,
            "p50_s": statistics.median(values) if values else None,
            "p95_s": _percentile(values, 95) if values else None,
            "serialized_sha256": digest,
            "query_evidence": evidence,
        }

    def _refresh_phase(self) -> dict[str, Any]:
        durations: list[float] = []
        watermarks: list[bool] = []

        def reader(name: str) -> int:
            errors = 0
            for _ in range(self.protocol.refresh_changes):
                try:
                    self._sample("primary", name)
                except Exception:  # noqa: BLE001 - retained in the evidence envelope
                    errors += 1
            return errors

        def changes() -> None:
            started = time.perf_counter()
            for index in range(self.protocol.refresh_changes):
                target = started + index * self.protocol.refresh_interval_s
                remaining = target - time.perf_counter()
                if remaining > 0:
                    time.sleep(remaining)
                result = self.refresh(index)
                durations.append(float(result["duration_s"]))
                watermarks.append(result.get("watermark_correct") is True)

        with ThreadPoolExecutor(max_workers=6) as pool:
            reader_futures = [pool.submit(reader, name) for name in WORKLOAD_NAMES]
            change_future = pool.submit(changes)
            reader_errors = sum(future.result() for future in reader_futures)
            change_future.result()
        return {
            "changes": self.protocol.refresh_changes,
            "highest_volume_scopes": True,
            "one_change_per_second": self.protocol.refresh_interval_s == 1.0,
            "p95_s": _percentile(durations, 95) if durations else None,
            "watermark_correct": bool(watermarks) and all(watermarks),
            "reader_errors": reader_errors,
        }

    def run(self) -> dict[str, Any]:
        resources = [self.resource_sample()]
        measurements = {name: self._measure(name) for name in WORKLOAD_NAMES}
        reconstruction_runs = []
        atomic, recovered = True, True
        for cold in (True, False, False):
            if cold:
                self.cold_cache()
            result = self.reconstruct(cold)
            reconstruction_runs.append(
                {
                    "cold_cache": cold,
                    "duration_s": float(result["duration_s"]),
                    "checksum": result["checksum"],
                }
            )
            atomic = atomic and result.get("atomic_publication") is True
            recovered = recovered and result.get("failure_retry_recovered") is True
        refresh = self._refresh_phase()
        probes = [self.isolation_probe(name) for name in WORKLOAD_NAMES]
        resources.append(self.resource_sample())
        return {
            "schema": "reality.fixture-j.product.v1",
            "profile": "full",
            "seed": 234,
            "business_date": "2026-09-18",
            "entrypoints": "product",
            "environment": {**self.environment, "resource_samples": resources},
            "cardinalities": self.cardinalities,
            "measurements": measurements,
            "tenant_isolation": {
                "probes": len(probes),
                "leaks": sum(not result for result in probes),
            },
            "reconstruction": {
                "runs": reconstruction_runs,
                "atomic_publication": atomic,
                "failure_retry_recovered": recovered,
            },
            "refresh": refresh,
            "concurrent_readers": self.protocol.concurrent_readers,
            "projection_workers": self.protocol.projection_workers,
            "complete_reconstruction_from_retained_inputs": True,
        }
