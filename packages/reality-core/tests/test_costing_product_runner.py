"""The fixture J product runner captures complete evidence without weakening defaults."""

from contextlib import contextmanager
from types import SimpleNamespace

from benchmarks.large_tenant_registers import product_runner as subject


class Workloads:
    def __init__(self, tenant):
        self.tenant_id = tenant
        self.session = SimpleNamespace(close=lambda: None)

    def _read(self, name):
        return f"{self.tenant_id}:{name}".encode(), name * 8

    order = lambda self: self._read("order")
    inventory = lambda self: self._read("inventory")
    monthly = lambda self: self._read("monthly")
    exceptions = lambda self: self._read("exceptions")
    mcp = lambda self: self._read("mcp")


@contextmanager
def queries(_session):
    yield [
        SimpleNamespace(
            statement="SELECT tenant_id LIMIT 1",
            has_tenant_scope=True,
            has_limit=True,
            has_order=False,
            is_count=False,
            is_bounded=True,
        )
    ]


def test_runner_captures_reconstruction_refresh_readers_and_control_probes(monkeypatch):
    monkeypatch.setattr(subject, "capture_queries", queries)
    monkeypatch.setattr(
        subject, "summarize_queries", lambda rows: [vars(row) for row in rows]
    )
    reconstructions = []
    refreshes = []

    def reconstruct(cold):
        reconstructions.append(cold)
        return {
            "duration_s": 1.0,
            "checksum": "same",
            "atomic_publication": True,
            "failure_retry_recovered": True,
        }

    def refresh(index):
        refreshes.append(index)
        return {"duration_s": 0.5, "watermark_correct": True}

    runner = subject.ProductQualificationRunner(
        workload_factory=Workloads,
        reconstruct=reconstruct,
        refresh=refresh,
        isolation_probe=lambda name: name in subject.WORKLOAD_NAMES,
        environment={
            "dedicated": False,
            "cpu_limit": 8,
            "memory_limit_bytes": 32,
            "local_ssd": True,
            "postgres_version": "17",
            "git_revision": "test",
        },
        cardinalities={"primary": {}, "control": {}},
        resource_sample=lambda: {"rss_bytes": 1, "io_bytes": 2},
        protocol=subject.ProductProtocol(
            warmups=1, samples=2, refresh_changes=3, refresh_interval_s=0
        ),
    )
    report = runner.run()
    assert reconstructions == [True, False, False]
    assert refreshes == [0, 1, 2]
    assert report["concurrent_readers"] == 5
    assert report["projection_workers"] == 1
    assert report["tenant_isolation"] == {"probes": 5, "leaks": 0}
    assert report["reconstruction"]["atomic_publication"] is True
    assert report["refresh"]["changes"] == 3
    assert report["refresh"]["watermark_correct"] is True
    assert set(report["measurements"]) == set(subject.WORKLOAD_NAMES)
    assert all(
        row["warmups"] == 1 and row["samples"] == 2
        for row in report["measurements"].values()
    )
    assert all(row["query_evidence"] for row in report["measurements"].values())


def test_full_protocol_defaults_match_the_fail_closed_qualification_contract():
    protocol = subject.ProductProtocol()
    assert (protocol.warmups, protocol.samples, protocol.refresh_changes) == (
        20,
        200,
        30,
    )
    assert protocol.concurrent_readers == 5
    assert protocol.projection_workers == 1
