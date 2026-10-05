"""Closed v1 coordination policies; no business balances or workflow state."""

from typing import Literal

POLICY_VERSION = 1
KINDS = ("order_fulfillment", "customer_return")
EventDisposition = Literal[
    "create_or_match", "update", "settle", "freshness", "no_case"
]
CREATE_EVENTS = frozenset(
    {
        "commitment.created",
        "return.announced",
        "document.recorded",
        "order.recorded",
        "source_record.interpreted",
        "document_line.item_assigned",
    }
)
UPDATE_EVENTS = frozenset(
    {
        "commitment.revised",
        "commitment.held",
        "commitment.hold_released",
        "movement.recorded",
        "movement.corrected",
        "shipment.notice_recorded",
        "shipment.event_recorded",
        "shipment.event_superseded",
    }
)
SETTLE_EVENTS = frozenset(
    {"commitment.cancelled", "commitment.fulfilled", "return.announcement_withdrawn"}
)


def event_disposition(event_type: str) -> EventDisposition:
    if event_type in CREATE_EVENTS:
        return "create_or_match"
    if event_type in UPDATE_EVENTS:
        return "update"
    if event_type in SETTLE_EVENTS:
        return "settle"
    if event_type == "source_record.received":
        return "freshness"
    return "no_case"


def fulfillment_state(work: list[dict]) -> str:
    from decimal import Decimal

    if any(
        row["status"] == "open" and Decimal(row["open_quantity"]) > 0 for row in work
    ):
        return "outstanding"
    return "completed"


def return_state(status: str) -> str:
    return {"withdrawn": "abandoned", "fulfilled": "completed"}.get(
        status, "outstanding"
    )
