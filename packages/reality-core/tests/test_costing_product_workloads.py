"""Fixture J workload adapters stay on shared read-only product entrypoints."""

from types import SimpleNamespace

from benchmarks.large_tenant_registers import product_workloads as subject


def scope():
    return subject.ProductWorkloadScope(
        order_line_id="line",
        inventory_item_id="item",
        company_generation_id="generation",
        monthly_question={"from": "contribution_valuation"},
    )


def test_product_workloads_use_shared_tools_and_serialize(monkeypatch):
    calls = []

    def read(session, tenant, name, arguments):
        calls.append((tenant, name, arguments))
        return {"tool": name, "arguments": arguments}

    monkeypatch.setattr(subject, "run_read_tool", read)
    workloads = subject.ProductWorkloads(object(), "tenant-a", scope())
    for method in (workloads.order, workloads.inventory, workloads.monthly):
        payload, digest = method()
        assert payload and len(digest) == 64
    assert [call[1] for call in calls] == [
        "cost.query.get",
        "cost.query.get",
        "graph.ask",
        "graph.ask",
        "graph.ask",
    ]
    assert all(call[0] == "tenant-a" for call in calls)


def test_exception_page_and_count_share_tenant(monkeypatch):
    calls = []
    monkeypatch.setattr(
        subject,
        "exception_page",
        lambda session, tenant, **kw: (
            calls.append(("page", tenant, kw)) or [{"id": "exception"}],
            SimpleNamespace(page=1, size=100, pages=1),
        ),
    )
    monkeypatch.setattr(
        subject,
        "exception_count",
        lambda session, tenant: calls.append(("count", tenant)) or 1,
    )
    payload, _ = subject.ProductWorkloads(object(), "tenant-a", scope()).exceptions()
    assert b'"count":1' in payload
    assert calls == [
        ("page", "tenant-a", {"page": 1, "size": 100}),
        ("count", "tenant-a"),
    ]


def test_mcp_adapter_uses_registered_serialized_cost_query(monkeypatch):
    calls = []
    handler = lambda session, tenant, arguments: calls.append((tenant, arguments)) or {"ok": True}
    monkeypatch.setitem(
        subject.MCP_TOOL_REGISTRY,
        "cost_query_get",
        SimpleNamespace(handler=handler),
    )
    payload, _ = subject.ProductWorkloads(object(), "tenant-a", scope()).mcp()
    assert payload == b'{"ok":true}'
    assert calls == [("tenant-a", {"kind": "contribution", "scope_id": "line"})]
