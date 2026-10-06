"""Synthetic Shopify inputs exercise real reviewed intake and payout booking."""

from scenarios.company_simulator.shopify import run_shopify
from scenarios.company_simulator.viewer.reader import ArtifactStore


def test_synthetic_shopify_month(session, scheduled_owner, tmp_path):
    result = run_shopify(
        session,
        scheduled_owner.id,
        days=30,
        operator="prompt",
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "passed", result.get("failure")
    observed = ArtifactStore(tmp_path).read_run(result["run_id"])
    assert observed["snapshot"]["run_state"] == "finished"
    assert len(observed["messages"]) == 3
    assert all(m["party_id"] for m in observed["messages"])
    assert all(
        e["party_id"] for e in observed["timeline"] if e["kind"] == "shopify_order"
    )
    assert all(g["status"] == "met" for g in result["goals"])
    assert result["shopify"]["synthetic"] is True
    assert result["shopify"]["charges"] == "90"
    assert result["shopify"]["refunds"] == "10"
    assert result["shopify"]["fees"] == "4"
    assert result["shopify"]["bank_deposits"] == "76"
    assert result["shopify"]["clearing_balance"] == "-10"
    assert result["shopify"]["unmatched_charges"] == "10"
    assert result["final_finance"]["open_balances"]["INV-#SYN-03"] == "10"
    assert result["shopify"]["payouts"][-1]["unmatched_line_ids"] == [
        "charge-unmatched"
    ]
    assert result["shopify"]["replay_no_effect"] is True


def test_shopify_idle_receives_unmatched_real_world_payouts(
    session, scheduled_owner, tmp_path
):
    result = run_shopify(
        session,
        scheduled_owner.id,
        days=30,
        operator="idle",
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "passed", result.get("failure")
    assert len(result["shopify"]["payouts"]) == 3
    assert result["shopify"]["bank_deposits"] == "76"
    assert result["shopify"]["clearing_balance"] == "-10"
    assert result["shopify"]["unmatched_charges"] == "10"
    assert result["shopify"]["unallocated_charges"] == "80"
    assert result["shopify"]["unallocated_refunds"] == "10"
    assert result["final_finance"]["accounts"]["accounts_receivable"] == "-70"
    assert result["shopify"]["unmatched_refunds"] == "0"
    assert not result["final_finance"]["errors"]
    assert result["final"]["physical"] == {"A": "6", "B": "6"}
    assert any(g["status"] == "missed" for g in result["goals"])
