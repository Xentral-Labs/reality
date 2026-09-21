"""T087 owner-confirmed conversions derive target values without replacing evidence."""

import hashlib
import json

import pytest
import test_contribution_reviews as revenue
import test_cost_allocation_services as allocation
import test_costing_services as costs
import test_inventory_costing_services as stock
import test_selling_costs as selling

from reality.db.core import SourceRecord
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.costing import (
    cost_evidence,
    cost_record,
    preview_cost_change,
    receipt_cost,
)
from reality.services.memberships import Principal
from reality.tools.application import run_read_tool

cost_owner = costs.cost_owner


def foreign_evidence(session, business, amount="10"):
    payload = json.dumps({"reality_finance_v1": {"net": amount, "tax": "0"}})
    source = SourceRecord(
        id=core.uid("src"),
        tenant_id=business.tenant.id,
        source_system="conversion-fixture",
        source_type="invoice",
        external_id=core.uid("ext"),
        payload=payload,
        payload_hash=hashlib.sha256(payload.encode()).hexdigest(),
        version=1,
    )
    session.add(source)
    session.flush()
    document = core.create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        core.uid("INV"),
        business.supplier.id,
        amount,
        currency="USD",
        source_record_id=source.id,
    )
    return source, document


def confirm_conversion(
    session, business, owner, source, document, *, kind="currency", **changes
):
    context = cost_evidence(session, business.tenant.id, document.id)
    arguments = {
        "operation": "conversion_basis",
        "expected_event_sequence": context["event_sequence"],
        "evidence_source_record_id": source.id,
        "kind": kind,
        "from_code": "USD" if kind == "currency" else "EA",
        "to_code": "EUR" if kind == "currency" else "BOX",
        "numerator": "9",
        "denominator": "10",
        "effective_at": core.now().isoformat(),
        "reason": "Source-backed conversion basis",
    }
    arguments.update(changes)
    return costs.execute(session, business, owner, arguments)


def test_confirmed_currency_basis_converts_read_observation_and_preserves_source_share(
    session, business, cost_owner
):
    movements = [costs.receipt(session, business), costs.receipt(session, business)]
    source, document = foreign_evidence(session, business)
    converted = confirm_conversion(session, business, cost_owner, source, document)
    arguments = allocation.weighted(
        session,
        business,
        movements,
        document,
        allocation_total="10",
        conversion_basis_revision_id=converted["conversion_basis_revision_id"],
    )
    costs.execute(session, business, cost_owner, arguments)
    result = receipt_cost(session, business.tenant.id, movements[0].id)
    assert result["known_cost"] == "2.2500"
    assert result["currency"] == "EUR"
    assert result["trace"][0]["source_share"] == "2.5000"
    assert result["trace"][0]["converted_share"] == "2.2500"
    assert (
        result["trace"][0]["conversion_basis_revision_id"]
        == converted["conversion_basis_revision_id"]
    )

    identity = converted["conversion_basis_revision_id"]
    record = cost_record(
        session, business.tenant.id, "cost_conversion_basis_revision", identity
    )
    assert record["fields"]["numerator"] == "9.000000000000"
    assert record["fields"]["denominator"] == "10.000000000000"
    assert {row["link"]["kind"] for row in record["sections"][1]["rows"]} >= {
        "source_record",
        "business_event",
        "action",
    }
    read_args = {
        "kind": "cost_conversion_basis_revision",
        "record_id": identity,
    }
    assert (
        run_read_tool(session, business.tenant.id, "cost.record.get", read_args)
        == record
    )
    schema = json.dumps(MCP_TOOL_REGISTRY["cost_change_propose"].input_schema)
    assert "conversion_basis" in schema
    assert "conversion_basis_revision_id" in schema


def test_conversion_revision_requires_exact_predecessor_and_unit_basis_cannot_price(
    session, business, cost_owner
):
    movements = [costs.receipt(session, business), costs.receipt(session, business)]
    source, document = foreign_evidence(session, business)
    first = confirm_conversion(session, business, cost_owner, source, document)
    with pytest.raises(core.Conflict, match="supersede"):
        confirm_conversion(session, business, cost_owner, source, document)
    second = confirm_conversion(
        session,
        business,
        cost_owner,
        source,
        document,
        numerator="4",
        denominator="5",
        supersedes_id=first["conversion_basis_revision_id"],
    )
    assert second["revision"] == 2
    unit = confirm_conversion(
        session, business, cost_owner, source, document, kind="unit"
    )
    arguments = allocation.weighted(
        session,
        business,
        movements,
        document,
        allocation_total="10",
        conversion_basis_revision_id=unit["conversion_basis_revision_id"],
    )
    with pytest.raises(core.InvalidOperation, match="kind"):
        preview_cost_change(
            session,
            business.tenant.id,
            arguments,
            principal=Principal(cost_owner.id),
        )


def test_selling_conversion_flows_through_reviewed_db2(session, business, cost_owner):
    contribution_args, data = revenue.prepared(session, business, cost_owner)
    source, document = foreign_evidence(session, business, "30")
    converted = confirm_conversion(session, business, cost_owner, source, document)
    context = cost_evidence(session, business.tenant.id, document.id)
    arguments = {
        "operation": "selling_allocate",
        "document_id": document.id,
        "expected_event_sequence": context["event_sequence"],
        "expected_evidence_hash": context["evidence_hash"],
        "tax_treatment": "recoverable",
        "selling_expense_confirmed": True,
        "allocation_total": "30",
        "driver_kind": "manual",
        "conversion_basis_revision_id": converted["conversion_basis_revision_id"],
        "targets": [
            {
                "document_line_id": data[0].id,
                "category": "outbound_freight",
                "weight": "1",
            },
            {
                "document_line_id": data[0].id,
                "category": "payment_fee",
                "weight": "2",
            },
        ],
        "reason": "Allocate converted selling evidence",
    }
    preview = preview_cost_change(
        session,
        business.tenant.id,
        arguments,
        principal=Principal(cost_owner.id),
    )
    assert preview["review"]["assigned_effect"] == "27.0000"
    costs.execute(session, business, cost_owner, arguments)
    reviewed = selling.refresh(
        session,
        business,
        cost_owner,
        contribution_args,
        data,
        selling.categories("outbound_freight", "payment_fee"),
    )
    _, result = stock.commit_review(session, business, cost_owner, reviewed)
    assert result["db1"] == "570.0000"
    assert result["allocated_selling_cost"] == "27.0000"
    assert result["db2"] == "543.0000"
