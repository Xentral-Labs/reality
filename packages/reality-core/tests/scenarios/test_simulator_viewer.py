"""Spec375 read-only spectator contracts and explicit evidence boundaries."""

import json
from http.client import HTTPConnection
from threading import Thread

import pytest

from scenarios.company_simulator.viewer.reader import ArtifactStore
from scenarios.company_simulator.viewer.server import make_server


def write(path, value):
    path.write_text(json.dumps(value) + "\n")


def journal(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


@pytest.fixture
def artifacts(tmp_path):
    run = tmp_path / "archive" / "first"
    run.mkdir(parents=True)
    write(
        run / "manifest.json",
        {
            "run_id": "actual-run",
            "days": 30,
            "profile_id": "complete",
            "operator": "prompt",
        },
    )
    events = [
        {
            "phase": "prepared",
            "proposal_id": "p1",
            "tool": "party_create",
            "arguments": {
                "records": [
                    {"name": "North shop", "roles": ["customer"]},
                    {"name": "South shop", "roles": ["customer"]},
                    {"name": "Cup supplier", "roles": ["supplier"]},
                ]
            },
        },
        {
            "phase": "committed",
            "proposal_id": "p1",
            "tool": "party_create",
            "receipt": {
                "records": [
                    {"family": "party", "id": p} for p in ["c1", "c2", "supplier"]
                ]
            },
        },
        {
            "phase": "prepared",
            "proposal_id": "p2",
            "tool": "source_record_ingest",
            "arguments": {"context": {"customer_party_id": "c2"}},
        },
        {
            "phase": "committed",
            "proposal_id": "p2",
            "tool": "source_record_ingest",
            "receipt": {"source_record_id": "src2"},
        },
        {
            "phase": "prepared",
            "proposal_id": "p3",
            "tool": "order_create",
            "arguments": {
                "number": "P001",
                "direction": "purchase",
                "counterparty_id": "supplier",
            },
        },
        {
            "phase": "committed",
            "proposal_id": "p3",
            "tool": "order_create",
            "receipt": {
                "document_id": "purchase-doc",
                "commitment_ids": ["purchase-com"],
            },
        },
    ]
    journal(run / "events.jsonl", events)
    journal(
        run / "messages.jsonl",
        [
            {
                "day": 2,
                "source_record_id": "src2",
                "payload": {
                    "from": "same@example.invalid",
                    "to": "company@example.invalid",
                    "subject": "Hello",
                    "body": "<img src=x onerror=alert(1)>",
                },
            }
        ],
    )
    journal(
        run / "checkpoints.jsonl",
        [
            {
                "day": 2,
                "recorded_at": "2026-10-05T10:00:00Z",
                "actual": {"physical": {"A": "6"}},
                "actual_finance": {"accounts": {"cash": "20"}},
                "differences": [],
            }
        ],
    )
    write(
        run / "report.json",
        {
            "core_status": "passed",
            "world_events": [{"kind": "purchase_order", "day": 2, "id": "P001"}],
            "goals": [{"id": "S01", "status": "missed"}],
            "coverage": {
                "planned": ["purchase_order", "return_receipt"],
                "exercised": ["purchase_order"],
                "not_exercised": ["return_receipt"],
            },
        },
    )
    return tmp_path, run


def test_explicit_customer_supplier_and_no_invented_replies(artifacts):
    root, run = artifacts
    before = {p.name: p.read_bytes() for p in run.iterdir()}
    store = ArtifactStore(root)
    assert store.list_runs()["runs"][0]["key"] == "archive/first"
    data = store.read_run("archive/first")
    assert data["messages"][0]["party_id"] == "c2"
    assert data["messages"][0]["payload"]["body"].startswith("<img")
    assert data["messages"][0]["status"] == "not_recorded"
    assert len(data["messages"]) == 1
    assert data["timeline"][0]["party_id"] == "supplier"
    assert data["summary"]["event_count"] == 1
    assert data["summary"]["goals"] == {"missed": 1}
    assert data["summary"]["core_status"] == "passed"
    assert data["summary"]["physical"] == {"A": "6"}
    assert before == {p.name: p.read_bytes() for p in run.iterdir()}


def test_live_partial_tail_and_unchecked_are_not_passed(artifacts):
    root, run = artifacts
    (run / "report.json").unlink()
    with (run / "messages.jsonl").open("a") as stream:
        stream.write('{"day":3')
    data = ArtifactStore(root).read_run("archive/first")
    assert len(data["messages"]) == 1
    assert data["summary"]["run_state"] == "unfinished"
    assert data["summary"]["core_status"] == "passed_at_checkpoint"
    assert any("incomplete" in n.lower() for n in data["notices"])
    assert data["summary"]["event_count"] is None
    (run / "checkpoints.jsonl").unlink()
    assert (
        ArtifactStore(root).read_run("archive/first")["summary"]["core_status"]
        == "unchecked"
    )


def test_original_outgoing_state_and_unresolved_identity(artifacts):
    root, run = artifacts
    journal(
        run / "messages.jsonl",
        [
            {
                "day": 2,
                "party_id": "c1",
                "direction": "outgoing",
                "status": "proposed",
                "payload": {"subject": "Reply", "body": "Exact draft"},
            },
            {
                "day": 3,
                "payload": {"from": "same@example.invalid", "subject": "Unknown"},
            },
        ],
    )
    rows = ArtifactStore(root).read_run("archive/first")["messages"]
    assert rows[0]["status"] == "proposed" and rows[0]["direction"] == "outgoing"
    assert rows[1]["party_id"] is None


def test_human_numbers_and_amounts_do_not_resolve_party(artifacts):
    root, run = artifacts
    with (run / "events.jsonl").open("a") as stream:
        for row in [
            {
                "phase": "prepared",
                "proposal_id": "cash",
                "tool": "customer_payment_post",
                "arguments": {"customer_party_id": "c1", "amount": "20"},
            },
            {
                "phase": "committed",
                "proposal_id": "cash",
                "tool": "customer_payment_post",
                "receipt": {
                    "amount": "20",
                    "number": "same",
                    "document_id": "payment-doc",
                },
            },
            {
                "phase": "prepared",
                "proposal_id": "unrelated",
                "tool": "unknown",
                "arguments": {"amount": "20", "number": "same"},
            },
            {
                "phase": "committed",
                "proposal_id": "unrelated",
                "tool": "unknown",
                "receipt": {},
            },
        ]:
            stream.write(json.dumps(row) + "\n")
    assert (
        ArtifactStore(root).read_run("archive/first")["operations"][-1]["party_id"]
        is None
    )


def test_reviewed_shop_order_uses_retained_source_reference(artifacts):
    root, run = artifacts
    with (run / "events.jsonl").open("a") as stream:
        stream.write(
            json.dumps(
                {
                    "phase": "committed",
                    "tool": "reviewed_shopify_intake",
                    "source_record_id": "src2",
                    "receipt": {"records": [{"type": "document", "id": "shop-order"}]},
                }
            )
            + "\n"
        )
    write(
        run / "report.json",
        {
            "order_references": {
                "SH01": {"document_id": "shop-order", "source_record_id": "src2"}
            },
            "world_events": [{"day": 2, "kind": "shopify_order", "id": "SH01"}],
        },
    )
    assert (
        ArtifactStore(root).read_run("archive/first")["timeline"][0]["party_id"] == "c2"
    )


def test_malformed_records_and_snapshot_outcome(artifacts):
    root, run = artifacts
    (run / "report.json").write_text("{")
    with (run / "events.jsonl").open("a") as stream:
        stream.write("not JSON\n")
    write(
        run / "spectator.json",
        {
            "run_state": "finished",
            "core_status": "awaiting_review",
            "day": 2,
            "world_events": [],
            "pending_proposal": {"tool": "order_create"},
        },
    )
    data = ArtifactStore(root).read_run("archive/first")
    assert data["summary"]["core_status"] == "awaiting_review"
    assert data["notices"]
    journal(
        run / "checkpoints.jsonl",
        [
            {
                "day": 2,
                "differences": [
                    {
                        "path": "physical.A",
                        "expected": "6",
                        "actual": "5",
                        "delta": "-1",
                    }
                ],
            }
        ],
    )
    (run / "spectator.json").unlink()
    assert (
        ArtifactStore(root).read_run("archive/first")["summary"]["core_status"]
        == "failed_at_checkpoint"
    )


def test_paths_and_symlinks_cannot_escape(artifacts, tmp_path_factory):
    root, run = artifacts
    outside = tmp_path_factory.mktemp("outside")
    write(outside / "manifest.json", {"run_id": "secret"})
    (root / "escape").symlink_to(outside, target_is_directory=True)
    store = ArtifactStore(root)
    for key in ["../outside", "/etc", "escape", "archive/first/../../escape"]:
        with pytest.raises(FileNotFoundError):
            store.read_run(key)
    assert all(r["key"] != "escape" for r in store.list_runs()["runs"])
    (run / "messages.jsonl").unlink()
    (run / "messages.jsonl").symlink_to(outside / "manifest.json")
    data = store.read_run("archive/first")
    assert data["messages"] == []
    assert data["notices"]


def test_http_read_only_routes(artifacts):
    root, _ = artifacts
    server = make_server(root, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection("127.0.0.1", server.server_port)
    try:
        connection.request("GET", "/api/runs/archive/first")
        response = connection.getresponse()
        assert response.status == 200
        assert response.getheader("Cache-Control") == "no-store"
        assert json.loads(response.read())["manifest"]["run_id"] == "actual-run"
        for method, path, headers, expected in [
            ("POST", "/api/runs", {}, 405),
            ("GET", "/api/runs/%2e%2e/outside", {}, 404),
            ("GET", "/manifest.json", {}, 404),
            ("GET", "/api/runs", {"Host": "evil.example"}, 403),
            ("GET", "/api/runs", {"Origin": "https://evil.example"}, 403),
        ]:
            connection.request(method, path, headers=headers)
            response = connection.getresponse()
            assert response.status == expected
            response.read()
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join()


def test_story_data_keeps_complete_checkpoints_and_safe_paths(artifacts):
    root, run = artifacts
    journal(run / "checkpoints.jsonl", [{"day": 1}, {"day": 3}])
    with (run / "checkpoints.jsonl").open("a") as stream:
        stream.write('{"day":4')
    store = ArtifactStore(root)
    data = store.story_data("archive/first")
    assert [row["day"] for row in data["checkpoints"]] == [1, 3]
    assert data["notices"]
    with pytest.raises(FileNotFoundError):
        store.story_data("../escape")
