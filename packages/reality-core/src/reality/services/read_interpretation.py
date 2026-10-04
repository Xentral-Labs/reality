"""Transient interpretation boundaries; never stored as business authority."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def blocker_kind(code: str) -> str:
    return (
        "recorded_hold"
        if code in {"commitment_hold", "party_delivery_hold"}
        else "derived_readiness_condition"
    )


def historical_fulfillment_cause(open_quantity: Decimal) -> dict[str, str]:
    return {
        "status": "unknown" if open_quantity > 0 else "not_applicable",
        "notice": (
            "Blocker codes describe current readiness, not the historical cause "
            "of remaining fulfillment. This read does not establish why execution "
            "has not happened; missing outbound-delivery records do not prove a "
            "conversion requirement."
            if open_quantity > 0
            else "No open fulfillment remains. Blockers describe current readiness, "
            "not a historical cause."
        ),
    }


def exception_interpretation(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "interpretation_scope": {
            "kind": "current_condition",
            "cross_condition_causality": "not_established_by_this_result",
            "notice": "Own evaluator evidence and trace links describe this condition. "
            "Co-occurrence or shared references do not prove that it caused another condition.",
        },
    }


def projection_interpretation(name: str, row: dict[str, Any]) -> dict[str, Any]:
    """Enrich a read copy, leaving stored cache payloads unchanged."""
    if name == "fulfillment_blockers":
        return {
            **row,
            "blocker_kind": blocker_kind(row["blocker_type"]),
            "identity_kind": "derived_condition_key",
            "notice": "This key identifies a condition for a promise, not a hold record. "
            "Several promises may refer to the same recorded hold; condition counts "
            "are not counts of distinct holds. Current blockers do not prove past causes.",
        }
    if name == "fulfillment_queue":
        lines = []
        for line in row["lines"]:
            value = {
                **line,
                "unfulfilled_cause": historical_fulfillment_cause(
                    Decimal(str(line["open_quantity"]))
                ),
            }
            if line.get("fulfillment_readiness") is not None:
                readiness = dict(line["fulfillment_readiness"])
                readiness["unfulfilled_cause"] = value["unfulfilled_cause"]
                readiness["blockers"] = [
                    {**b, "blocker_kind": blocker_kind(b["code"])}
                    for b in readiness["blockers"]
                ]
                value["fulfillment_readiness"] = readiness
            lines.append(value)
        return {**row, "lines": lines}
    if name == "exceptions":
        return exception_interpretation(row)
    return row


def external_agent_runtime() -> dict[str, str]:
    return {
        "visibility": "outside_reality",
        "owner": "external_client",
        "schedule": "unknown",
        "mission": "unknown",
        "checkpoint": "unknown",
        "next_run": "unknown",
        "pause_state": "unknown",
        "notice": "External client configuration cannot be inspected here. "
        "Missing access does not prove absence.",
    }
