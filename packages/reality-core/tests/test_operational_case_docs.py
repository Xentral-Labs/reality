"""Published integration vocabulary matches the executable closed v1 policy."""

from pathlib import Path

import yaml

from reality.config import config_text
from reality.domain.operational_cases import KINDS, event_disposition


def test_policy_catalog_matches_actual_events_and_enabled_kinds():
    policy = yaml.safe_load(config_text("case_policy_catalog.yaml"))
    events = {
        row["type"]
        for row in yaml.safe_load(config_text("business_event_catalog.yaml"))["events"]
    }
    assert policy["version"] == 1
    assert set(policy["kinds"]) == set(KINDS)
    for classification, types in policy["classifications"].items():
        if classification == "default":
            assert types == "no_case"
            continue
        assert set(types) <= events
        assert all(event_disposition(event) == classification for event in types)
    assert {
        "live_shopify_transport",
        "refund_intent_execution",
        "unannounced_return_automation",
        "unanchored_customer_delivery",
    } <= set(policy["unavailable"])


def test_guidance_preserves_id_meanings_and_capability_limits():
    root = Path(__file__).resolve().parents[3]
    contract = (root / "docs/features/operational-cases.md").read_text()
    for term in [
        "case_id",
        "action_id",
        "correlation_id",
        "executing",
        "historical",
        "refund",
        "Live",
        "manual takeover",
        "handback",
    ]:
        assert term.lower() in contract.lower()
    for language in ["", "de/"]:
        guide = (
            root / f"apps/docs/content/{language}integrations/operational-cases.md"
        ).read_text()
        assert "operational_case_object" in guide
        assert "operational_case_explain" in guide
        assert "Shopify" in guide
