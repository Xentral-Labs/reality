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


def payment_interpretation(row: dict[str, Any]) -> dict[str, Any]:
    """Explain canonical qualification without evaluating settlement again."""
    payment = row["payment"]
    order_id = row["order_id"]
    amount = row["required_amount"] if order_id else None
    codes = [code for code in row["blocker_codes"] if code.startswith("prepayment_")]
    prepaid = row["requires_prepayment"]
    if not prepaid:
        evidence_status = "not_evaluated"
    elif "prepayment_amount_unstated" in codes:
        evidence_status = "amount_unstated"
    elif "prepayment_attribution_ambiguous" in codes:
        evidence_status = "attribution_ambiguous"
    elif not row["invoice_ids"]:
        evidence_status = "invoice_missing"
    else:
        evidence_status = "order_qualified"
    interpreted_amounts = evidence_status in {"invoice_missing", "order_qualified"}
    open_quantity = Decimal(str(row["lines"][0]["open_quantity"]))
    release_id = payment["prepayment_release_id"]
    if open_quantity <= 0:
        constraint_status = "not_applicable"
    elif not prepaid:
        constraint_status = "not_required"
    elif codes:
        constraint_status = "blocked"
    elif release_id:
        constraint_status = "released"
    else:
        constraint_status = "satisfied"
    return {
        "amount_basis": {
            "kind": "not_established"
            if not order_id
            else ("unstated" if amount is None else "stated_order_gross"),
            "amount": amount,
            "currency": row["currency"],
            "document_id": order_id,
        },
        "payment_evidence": {
            "status": evidence_status,
            "received": row["received_amount"] if interpreted_amounts else None,
            "remaining": row["remaining_amount"] if interpreted_amounts else None,
            "invoice_ids": list(row["invoice_ids"]),
            "allocation_ids": list(row["allocation_ids"]),
        },
        "shipment_constraint": {
            "status": constraint_status,
            "blocker_codes": codes,
            "release_id": release_id,
        },
        "notice": (
            "Standard policy does not require prepayment for shipment. The legacy "
            "required amount is an order basis, not an unpaid invoice. Settlement "
            "was not evaluated; legacy received/remaining zeroes establish neither "
            "absence of payments nor a settled balance."
            if not prepaid
            else "Amounts describe canonical qualifying evidence for this order, not "
            "all customer payments or a customer balance. Missing or ambiguous "
            "evidence does not prove absence of actual payments. A prepayment "
            "release is not payment and does not waive surviving payment blockers. "
            "Consolidated invoice qualification follows the existing full-settlement rule."
        ),
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
                readiness["payment_interpretation"] = payment_interpretation(readiness)
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


def order_inventory_interpretation() -> dict[str, str]:
    """Bound current inventory and linked movements without inferring history."""
    return {
        "kind": "current_inventory_and_order_linked_movements",
        "inventory_history": "not_established_by_this_read",
        "notice": "Current inventory and order-linked movements do not establish "
        "complete inventory history or the historical causes of stock. Do not "
        "suggest receipt timing or a different stock context from these values. "
        "If no additional history evidence was inspected, say not checked. "
        "Use movement_explanation with a returned movement ID to read that exact "
        "movement's provenance, not complete inventory history.",
    }
