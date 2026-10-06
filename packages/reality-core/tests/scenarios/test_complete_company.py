"""Spec374 end-to-end simulated company proofs."""

import json
from pathlib import Path

import pytest

from scenarios.company_simulator.complete import complete_profile, run_complete


@pytest.mark.parametrize("operator", ["prompt", "delayed", "idle", "wrong_address"])
def test_complete_month(session, scheduled_owner, tmp_path, operator):
    result = run_complete(
        session,
        scheduled_owner.id,
        complete_profile(),
        days=30,
        operator=operator,
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "passed", result.get("failure")
    spectator = json.loads(
        (Path(result["artifact_dir"]) / "spectator.json").read_text()
    )
    assert spectator["run_id"] == result["run_id"]
    assert spectator["run_state"] == "finished"
    assert spectator["core_status"] == result["core_status"]
    assert spectator["world_events"] == result["world_events"]
    assert spectator["business_references"] == result["business_references"]
    assert spectator["goals"] == result["goals"]
    if operator == "prompt":
        assert all(g["status"] in {"met", "cancelled"} for g in result["goals"])
        assert result["coverage"]["exercised"] == result["coverage"]["planned"]
        assert result["final_finance"]["open_balances"]
        assert result["final_finance"]["open_balances"]["INV-S09"] == "20"
        assert not result["final_finance"]["errors"]
        assert result["final"]["physical"] == {"A": "4", "B": "2"}
        assert result["final_finance"]["accounts"] == {
            "cash": "190",
            "accounts_receivable": "20",
            "accounts_payable": "0",
            "sales_revenue": "-370",
            "inventory": "160",
            "payment_fee_expense": "0",
        }
        assert result["final"]["counts"]["sales_orders"] == 10
        assert result["final"]["counts"]["purchase_orders"] == 4
        assert result["final"]["counts"]["ledger_entries"] == 72

        checkpoints = [
            json.loads(line)
            for line in (Path(result["artifact_dir"]) / "checkpoints.jsonl")
            .read_text()
            .splitlines()
        ]
        credit = next(e for e in result["world_events"] if e["kind"] == "sales_credit")
        day = credit["day"]
        by_day = {c["day"]: c for c in checkpoints}
        assert by_day[day]["actual_finance"]["open_balances"]["CR-S03"] == "10"
        assert by_day[day + 1]["actual_finance"]["open_balances"]["CR-S03"] == "6"
        assert by_day[day + 2]["actual_finance"]["open_balances"]["CR-S03"] == "0"
        assert all(
            c["actual"]["lines"]["S03:A"]["fulfilled"] == "5"
            for c in checkpoints
            if c["day"] >= day
        )
        assert any(c["actual"]["return_open"]["A"] == "1" for c in checkpoints)

    else:
        assert any(g["status"] == "missed" for g in result["goals"])
    if operator == "wrong_address":
        assert any(g.get("wrong_destination") for g in result["goals"])


def test_finance_corruption_stops(session, scheduled_owner, tmp_path, monkeypatch):
    from scenarios.company_simulator import complete_observer

    original = complete_observer.finance_observation

    def corrupt(*args, **kwargs):
        result = original(*args, **kwargs)
        result["accounts"]["cash"] = "999"
        return result

    monkeypatch.setattr(complete_observer, "finance_observation", corrupt)
    result = run_complete(
        session,
        scheduled_owner.id,
        complete_profile(),
        days=30,
        operator="prompt",
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "failed"
    assert result["failure"]["day"] <= 1


def test_custom_operator_needs_exact_review(session, scheduled_owner, tmp_path):
    calls = []

    def operator(view):
        assert "future" not in view and "expected_accounts" not in view
        calls.append(view)
        return [{"kind": "purchase", "sku": "A"}]

    result = run_complete(
        session,
        scheduled_owner.id,
        complete_profile(),
        days=1,
        operator=operator,
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "awaiting_review"
    assert result["pending_proposal"]["arguments"]
    spectator = json.loads(
        (Path(result["artifact_dir"]) / "spectator.json").read_text()
    )
    assert spectator["core_status"] == "awaiting_review"
    assert spectator["pending_proposal"] == result["pending_proposal"]
    assert "delay_sku" not in spectator["released"]["quote"]
    assert len(spectator["released"]["requests"]) == 1
    assert calls


def test_spectator_export_failure_does_not_change_business(
    session, scheduled_owner, tmp_path, monkeypatch
):
    original = Path.replace

    def unavailable(path, target):
        if path.name == "spectator.tmp":
            raise OSError("Synthetic viewer export failure")
        return original(path, target)

    monkeypatch.setattr(Path, "replace", unavailable)
    result = run_complete(
        session,
        scheduled_owner.id,
        complete_profile(),
        days=1,
        operator="idle",
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "passed"
    assert result["spectator_error"] == "OSError"
    assert result["final"]["counts"]["sales_orders"] == 1


def test_live_review_requires_principal_not_boolean(session, scheduled_owner, tmp_path):
    def policy(view):
        return [{"kind": "purchase", "sku": "A"}]

    result = run_complete(
        session,
        scheduled_owner.id,
        complete_profile(),
        days=1,
        operator=policy,
        review=lambda proposal: True,
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "awaiting_review"
    assert result["coverage"]["exercised"].count("purchase_order") == 0


def test_live_review_approves_exact_proposal(session, scheduled_owner, tmp_path):
    from reality.services.memberships import Principal

    reviewed = []

    def policy(view):
        return [{"kind": "purchase", "sku": "A"}]

    def review(proposal):
        reviewed.append(proposal)
        assert proposal["tool"] == "order_create"
        assert proposal["arguments"]["direction"] == "purchase"
        return Principal(scheduled_owner.id)

    result = run_complete(
        session,
        scheduled_owner.id,
        complete_profile(),
        days=1,
        operator=policy,
        review=review,
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "passed", result.get("failure")
    assert len(reviewed) == 1
    assert result["final"]["counts"]["purchase_orders"] == 1


def test_private_customer_reactions_hidden():
    from scenarios.company_simulator.complete_world import CompleteWorld

    world = CompleteWorld(complete_profile())
    world.release(4)
    view = world.view(4)
    request = next(r for r in view["requests"] if r["id"] == "S03")
    assert "return" not in request and "payments" not in request
    view["stock"]["W1"]["A"] = 999
    assert world.locations["W1"]["A"] == 6


def test_private_supplier_delay_hidden():
    from scenarios.company_simulator.complete_world import CompleteWorld

    world = CompleteWorld(complete_profile())
    world.purchase("P1", "B", 1)
    view = world.view(1)
    assert "delay_sku" not in view["quote"] and "delay_days" not in view["quote"]
    assert "deliveries" not in view["purchases"][0]
    assert view["purchases"][0]["quoted_arrival_days"] == [3, 5]
    assert world.purchases["P1"]["deliveries"][0]["day"] == 4


def test_complete_correspondence(session, scheduled_owner, tmp_path):
    from sqlalchemy import select

    from reality.db.core import SourceRecord
    from scenarios.company_simulator.viewer.reader import ArtifactStore

    result = run_complete(
        session,
        scheduled_owner.id,
        complete_profile(),
        days=30,
        operator="prompt",
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "passed", result.get("failure")
    data = ArtifactStore(tmp_path).read_run(result["run_id"])
    messages = data["messages"]
    by_id = {m["payload"]["message_id"]: m for m in messages}
    kinds = {m["payload"].get("kind") for m in messages}
    assert {
        "supplier_confirmation",
        "supplier_delay_notice",
        "supplier_receipt",
        "customer_cancellation",
        "customer_return",
        "customer_status_query",
        "agent_reply",
    } <= kinds
    assert len(by_id) == len(messages)
    for message in messages:
        assert message["party_id"] in result["business_references"]["parties"].values()
        stored = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == result["company_id"],
                SourceRecord.id == message["source_record_id"],
            )
        )
        assert stored is not None
        assert json.loads(stored.payload) == message["payload"]
        assert message["payload"]["transport"] == "local_simulation"
        assert message["payload"]["business_references"]
        if message["direction"] == "outgoing":
            assert message["status"] == "simulated"
            assert message["payload"]["in_reply_to"] in by_id
    assert result["final"]["physical"] == {"A": "4", "B": "2"}
    assert result["final_finance"]["accounts"]["cash"] == "190"
    assert result["communication"]["messages"] == len(messages)


def test_idle_correspondence_has_no_agent_replies(session, scheduled_owner, tmp_path):
    result = run_complete(
        session,
        scheduled_owner.id,
        complete_profile(),
        days=10,
        operator="idle",
        output_root=tmp_path,
        confirmed=True,
    )
    rows = [
        json.loads(line)
        for line in (Path(result["artifact_dir"]) / "messages.jsonl")
        .read_text()
        .splitlines()
    ]
    assert any(m["payload"].get("kind") == "customer_status_query" for m in rows)
    assert not any(m.get("direction") == "outgoing" for m in rows)
    assert not any(m["payload"].get("kind", "").startswith("supplier_") for m in rows)


def test_custom_reply_is_explicit_draft(session, scheduled_owner, tmp_path):
    observed = []

    def policy(view):
        observed.extend(view["messages"])
        incoming = view["messages"][0]["payload"]
        return [
            {
                "kind": "reply",
                "message_id": incoming["message_id"],
                "subject": "Re: Order S01",
                "body": "I will check availability.",
            }
        ]

    result = run_complete(
        session,
        scheduled_owner.id,
        complete_profile(),
        days=1,
        operator=policy,
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "passed", result.get("failure")
    rows = [
        json.loads(line)
        for line in (Path(result["artifact_dir"]) / "messages.jsonl")
        .read_text()
        .splitlines()
    ]
    outgoing = [m for m in rows if m.get("direction") == "outgoing"]
    assert len(outgoing) == 1
    assert outgoing[0]["status"] == "proposed"
    assert outgoing[0]["payload"]["body"] == "I will check availability."
    assert outgoing[0]["payload"]["in_reply_to"] == observed[0]["payload"]["message_id"]
    assert result["final"]["counts"]["purchase_orders"] == 0


def test_supplier_notice_releases_only_after_purchase(
    session, scheduled_owner, tmp_path
):
    from scenarios.company_simulator.complete import CompanyRun

    run = CompanyRun(
        session, scheduled_owner.id, complete_profile(), 1, "prompt", tmp_path, None
    )
    run.initialize()
    run.day = 1
    run.purchase("B")
    run.correspondence.incoming()
    assert not run.world.messages
    run.day = 2
    run.correspondence.incoming()
    notices = run.world.view(2)["messages"]
    assert {m["payload"]["kind"] for m in notices} == {
        "supplier_confirmation",
        "supplier_delay_notice",
    }
    delay = next(m for m in notices if m["payload"]["kind"] == "supplier_delay_notice")
    assert delay["payload"]["body"]["revised_arrival_days"] == [4, 6]
    run.correspondence.incoming()
    assert len(run.world.messages) == 2
    with pytest.raises(ValueError, match="released incoming"):
        run.correspondence.draft({"message_id": "unreleased"})
