"""Public payment reads use one strict direction vocabulary."""

import pytest

from reality.mcp.catalog import MCP_TOOL_REGISTRY, dispatch_tool
from reality.services import core
from reality.tools.application import run_read_tool


def test_finance_payments_publishes_only_incoming_and_outgoing():
    schema = MCP_TOOL_REGISTRY["finance_payments"].input_schema

    assert schema["additionalProperties"] is False
    assert schema["properties"]["direction"]["enum"] == ["incoming", "outgoing"]
    assert "side" not in schema["properties"]


@pytest.mark.parametrize(
    ("direction", "expected_directions"),
    [("incoming", {"incoming"}), ("outgoing", set())],
)
def test_finance_payments_accepts_each_public_direction(
    session, business, direction, expected_directions
):
    tenant_id = business.tenant.id
    core.record_customer_payment(
        session,
        tenant_id,
        business.customer.id,
        "25",
        payment_number="PAY-IN",
    )

    result = dispatch_tool(
        session,
        tenant_id,
        "finance_payments",
        {"direction": direction},
    )

    assert {item["direction"] for item in result["items"]} == expected_directions


@pytest.mark.parametrize(
    "arguments",
    [
        {"direction": "customer"},
        {"direction": "supplier"},
        {"direction": "inbound"},
        {"direction": ""},
        {"side": "customer"},
    ],
)
def test_finance_payments_rejects_unsupported_filters(session, business, arguments):
    with pytest.raises(
        core.InvalidOperation,
        match="Payment direction must be incoming or outgoing|Unsupported payment filter",
    ):
        run_read_tool(
            session,
            business.tenant.id,
            "finance.payments.list",
            arguments,
        )
