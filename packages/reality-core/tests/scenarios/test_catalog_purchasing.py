"""Purchasing scenarios from the catalog (G07, G14, H03, H10, H11, H12, I05, I06, I07, K05)."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import test_costing_services as cost_fixtures
from conftest import record_by_id
from sqlalchemy import select

from reality.db.core import Document, Movement
from reality.services import core
from reality.services.analytics.reports import caller
from reality.services.costing import cost_evidence
from reality.services.decision_attribution import record_decisions
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.exceptions import operational_exceptions
from reality.services.memberships import Principal
from reality.services.shipments import shipment_explain
from reality.services.supply_assignments import assign_supply, supply_coverage
from reality.tools.application import (
    approve_and_execute_proposal,
    confirm_tool,
    create_change_proposal,
    propose_tool,
    run_read_tool,
)

AS_OF = datetime(2026, 9, 25, 12, tzinfo=UTC)
cost_owner = cost_fixtures.cost_owner


def _order(session, business, direction, number, counterparty_id, quantity, price):
    gross = str(Decimal(quantity) * Decimal(price))
    _, document, lines, commitments = core.create_manual_order(
        session,
        business.tenant.id,
        direction,
        number,
        business.company.id,
        counterparty_id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit_price": price,
                "gross_amount": gross,
            }
        ],
        gross,
        document_date="2026-09-01",
    )
    return document, lines[0], commitments[0]


def _execute_delivery(session, tenant_id, tool, arguments):
    proposal = create_change_proposal(session, tenant_id, tool, arguments)
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session, tenant_id, proposal.id, review_token=token, confirmed=True
    )


def _records_of(session, tenant_id, class_id):
    return {
        row.record_id
        for row in operational_exceptions(session, tenant_id, as_of=AS_OF)
        if row.class_id == class_id
    }


def test_two_suppliers_purchases_together_protect_one_customer_promise(
    session, business
):
    """G14: two suppliers' purchases together protect one customer promise."""
    second_supplier = core.create_party(
        session, business.tenant.id, "Light Works AG", "supplier"
    )
    _, _, customer = _order(
        session, business, "sales", "SO-G14", business.customer.id, "10", "20"
    )
    _, _, first = _order(
        session, business, "purchase", "PO-G14-A", business.supplier.id, "6", "10"
    )
    _, _, second = _order(
        session, business, "purchase", "PO-G14-B", second_supplier.id, "8", "11"
    )
    assign_supply(
        session,
        business.tenant.id,
        first.id,
        "6",
        purpose="customer_demand",
        customer_commitment_id=customer.id,
        request_id="g14-first",
    )
    assign_supply(
        session,
        business.tenant.id,
        second.id,
        "4",
        purpose="customer_demand",
        customer_commitment_id=customer.id,
        request_id="g14-second",
    )

    coverage = supply_coverage(
        session, business.tenant.id, customer_commitment_id=customer.id
    )
    assert coverage["customer"]["quantity"] == Decimal(10)
    assert coverage["customer"]["protecting_supply"] == Decimal(10)
    assert sorted(
        (item["supplier_commitment_id"], item["quantity"]) for item in coverage["items"]
    ) == sorted([(first.id, Decimal(6)), (second.id, Decimal(4))])
    assert {first.from_party_id, second.from_party_id} == {
        business.supplier.id,
        second_supplier.id,
    }
    second_view = supply_coverage(
        session, business.tenant.id, supplier_commitment_id=second.id
    )["supplier"]
    assert second_view["customer_assigned"] == Decimal(4)
    assert second_view["unassigned"] == Decimal(4)


def test_one_inbound_package_is_split_across_several_purchase_orders(session, business):
    """H10: one received package fulfils several purchase orders by their own lines."""
    _, _, first = _order(
        session, business, "purchase", "PO-H10-A", business.supplier.id, "5", "10"
    )
    _, _, second = _order(
        session, business, "purchase", "PO-H10-B", business.supplier.id, "7", "10"
    )
    before = core.stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    )
    proposal = _execute_delivery(
        session,
        business.tenant.id,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "IN-H10",
            "movements": [
                {
                    "commitment_id": first.id,
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": "5",
                },
                {
                    "commitment_id": second.id,
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": "4",
                },
            ],
        },
    )
    receipt = json.loads(proposal.output)
    movements = list(
        session.scalars(
            select(Movement).where(
                Movement.tenant_id == business.tenant.id,
                Movement.shipment_package_id == receipt["package_id"],
            )
        )
    )

    assert {movement.id for movement in movements} == set(receipt["movement_ids"])
    assert sorted((m.commitment_id, m.quantity) for m in movements) == sorted(
        [(first.id, Decimal(5)), (second.id, Decimal(4))]
    )
    assert core.fulfilled_quantity(session, business.tenant.id, first.id) == Decimal(5)
    assert core.fulfilled_quantity(session, business.tenant.id, second.id) == Decimal(4)
    terms = core.commitment_terms(session, business.tenant.id, [first.id, second.id])
    assert terms[first.id].open == Decimal(0)
    assert terms[second.id].open == Decimal(3)
    assert core.stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    ) == before + Decimal(9)
    detail = shipment_explain(session, business.tenant.id, receipt["shipment_id"])
    assert Decimal(detail["quantities"]["received"]) == Decimal(9)


def test_early_receipt_fulfils_the_purchase_and_keeps_its_due_date(session, business):
    """H11: a delivery before the confirmed date is recorded and readable as early."""
    due = datetime(2026, 9, 20, tzinfo=UTC)
    received_at = datetime(2026, 9, 12, 9, tzinfo=UTC)
    early = core.create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "8",
        due,
    )
    waiting = core.create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "3",
        due,
    )
    movement = core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "8",
        to_location_id=business.location.id,
        commitment_id=early.id,
        occurred_at=received_at,
    )

    terms = core.commitment_terms(session, business.tenant.id, [early.id])[early.id]
    assert terms.fulfilled == Decimal(8)
    assert terms.open == Decimal(0)
    assert terms.due_at == due
    stored = record_by_id(session, Movement, movement.id)
    assert stored.occurred_at == received_at
    # No read labels a receipt "early"; it is derivable from the two held values.
    assert terms.due_at - stored.occurred_at == timedelta(days=7, hours=15)
    overdue = _records_of(
        session, business.tenant.id, "overdue_incoming_supplier_commitment"
    )
    assert waiting.id in overdue
    assert early.id not in overdue


def test_receipt_before_purchase_order_is_linked_later_by_replacement(
    session, business
):
    """H12: a receipt booked before its purchase order exists is linked to it later."""
    received_at = datetime(2026, 9, 10, 8, tzinfo=UTC)
    receipt = core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "10",
        to_location_id=business.location.id,
        occurred_at=received_at,
    )
    assert receipt.id in _records_of(
        session, business.tenant.id, "unexplained_movement"
    )
    assert core.stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    ) == Decimal(10)

    _, _, purchase = _order(
        session, business, "purchase", "PO-H12", business.supplier.id, "10", "10"
    )
    assert core.fulfilled_quantity(session, business.tenant.id, purchase.id) == Decimal(
        0
    )
    result = core.correct_movement(
        session,
        business.tenant.id,
        receipt.id,
        reason="Receipt belongs to PO-H12, entered later",
        replacement={
            "type": "receipt",
            "item_id": business.item.id,
            "quantity": "10",
            "to_location_id": business.location.id,
            "commitment_id": purchase.id,
            "occurred_at": received_at,
        },
    )

    replacement = record_by_id(session, Movement, result.replacement_movement_id)
    assert replacement.commitment_id == purchase.id
    assert replacement.occurred_at == received_at
    assert core.stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    ) == Decimal(10)
    assert core.fulfilled_quantity(session, business.tenant.id, purchase.id) == Decimal(
        10
    )
    unexplained = _records_of(session, business.tenant.id, "unexplained_movement")
    assert receipt.id not in unexplained
    assert replacement.id not in unexplained


def test_one_supplier_invoice_bills_lines_of_two_purchase_orders(session, business):
    """I05: one supplier invoice over two purchase orders is allocated per purchase."""
    _, first_line, _ = _order(
        session, business, "purchase", "PO-I05-A", business.supplier.id, "5", "10"
    )
    _, second_line, _ = _order(
        session, business, "purchase", "PO-I05-B", business.supplier.id, "3", "20"
    )
    # Spec 283: the guided invoice command bills positions of several purchase
    # orders of one supplier on one invoice.
    core.record_supplier_invoice(
        session,
        business.tenant.id,
        lines=[
            {"order_line_id": first_line.id, "quantity": "5", "gross_amount": "50"},
            {"order_line_id": second_line.id, "quantity": "2", "gross_amount": "40"},
        ],
        gross_amount="90",
        number="SINV-I05",
    )
    invoice_id = core._order_line_billing(session, business.tenant.id, first_line.id)[
        "evidence"
    ][0]["invoice_id"]

    first_billing = core._order_line_billing(session, business.tenant.id, first_line.id)
    second_billing = core._order_line_billing(
        session, business.tenant.id, second_line.id
    )
    assert (first_billing["invoiced"], first_billing["remaining"]) == (
        Decimal(5),
        Decimal(0),
    )
    assert (second_billing["invoiced"], second_billing["remaining"]) == (
        Decimal(2),
        Decimal(1),
    )
    assert [row["invoice_id"] for row in first_billing["evidence"]] == [invoice_id]
    assert [row["invoice_id"] for row in second_billing["evidence"]] == [invoice_id]
    assert core.open_invoice_amount(session, business.tenant.id, invoice_id) == Decimal(
        90
    )

    # The allocation is binding: PO-A is fully billed, PO-B has exactly one left.
    with pytest.raises(core.InvalidOperation, match="remaining"):
        core.record_supplier_invoice(
            session, business.tenant.id, first_line.id, "1", "10", "SINV-I05-OVER"
        )
    core.record_supplier_invoice(
        session, business.tenant.id, second_line.id, "1", "20", "SINV-I05-REST"
    )
    assert core._order_line_billing(session, business.tenant.id, second_line.id)[
        "remaining"
    ] == Decimal(0)


# --- Spec 294: purchasing and receipt (G07, H03, I06, I07, K05) ----------------


def _reviewed(session, business, tool, arguments, request_id):
    proposal = prepare_delivery_action(
        session, business.tenant.id, tool, arguments, request_id=request_id
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    assert executed.status == "executed"
    return proposal, json.loads(executed.output)


def _receive_into(session, business, tracking, commitment, quantity, item_id=None):
    return _execute_delivery(
        session,
        business.tenant.id,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": tracking,
            "movements": [
                {
                    "commitment_id": commitment.id,
                    "item_id": item_id or business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": quantity,
                }
            ],
        },
    )


def _supplier_invoice(session, business, order_line, quantity, gross, number):
    _, receipt = _reviewed(
        session,
        business,
        "supplier_invoice_record",
        {
            "order_line_id": order_line.id,
            "quantity": quantity,
            "gross_amount": gross,
            "number": number,
            "effective_at": "2026-09-20T10:00:00Z",
        },
        number,
    )
    return next(row["id"] for row in receipt["records"] if row["family"] == "document")


def test_a_supplier_tier_price_is_kept_and_a_different_price_is_reported(
    session, business
):
    """G07: the tier the supplier states for the quantity is the agreed price."""
    tenant = business.tenant.id
    tiers = core.create_price_list(
        session, tenant, "SUP-TIERS", "Supplier tiers", "purchase", "EUR"
    )
    core.create_price_list_entry(
        session, tenant, tiers.id, business.item.id, 1, "5.00", "pcs"
    )
    ten_or_more = core.create_price_list_entry(
        session, tenant, tiers.id, business.item.id, 10, "4.00", "pcs"
    )
    core.assign_party_price_list(session, tenant, business.supplier.id, tiers.id)
    _, _, lines, _ = core.create_manual_order(
        session,
        tenant,
        "purchase",
        "PO-G07",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit": "pcs",
                "unit_price": "4.00",
                "gross_amount": "40.00",
                "price_list_entry_id": ten_or_more.id,
            }
        ],
        "40.00",
        document_date="2026-09-01",
    )
    order_line = lines[0]
    assert order_line.price_list_entry_id == ten_or_more.id

    invoice_id = _supplier_invoice(
        session, business, order_line, "8", "32.00", "ER-G07"
    )
    invoice = record_by_id(session, Document, invoice_id)
    assert invoice.gross_amount == Decimal("32.00")
    assert _records_of(session, tenant, "invoice_price_differs") == set()

    # The supplier bills the rest at the single-unit tier instead.
    recorded = json.loads(
        confirm_tool(
            session,
            tenant,
            propose_tool(
                session,
                tenant,
                "document_create",
                {
                    "document_type": "supplier_invoice",
                    "number": "ER-G07-2",
                    "party_id": business.supplier.id,
                    "gross_amount": "10.00",
                    "document_date": "2026-09-21",
                    "lines": [
                        {
                            "item_id": business.item.id,
                            "quantity": "2",
                            "unit": "pcs",
                            "unit_price": "5.00",
                            "gross_amount": "10.00",
                            "billed_document_line_id": order_line.id,
                        }
                    ],
                },
            ).id,
        ).output
    )
    differing = {
        row.record_id: row
        for row in operational_exceptions(session, tenant, as_of=AS_OF)
        if row.class_id == "invoice_price_differs"
    }
    row = differing[recorded["document_line_ids"][0]]
    assert row.causal_values["agreed_unit_price"] == Decimal("4.0000")
    assert row.causal_values["billed_unit_price"] == Decimal("5.0000")


def test_an_under_delivery_is_closed_with_its_reason_and_decision(session, business):
    """H03: the rest never comes, and a confirmed revision says why and who."""
    tenant = business.tenant.id
    _, _, _lines, commitments = core.create_manual_order(
        session,
        tenant,
        "purchase",
        "PO-H03",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": "10",
                "gross_amount": "100",
            }
        ],
        "100",
        requested_delivery_at=AS_OF - timedelta(days=10),
    )
    purchase = commitments[0]
    _receive_into(session, business, "IN-H03", purchase, "7")
    # Positive control: 3 still open and past due are reported.
    assert purchase.id in _records_of(
        session, tenant, "overdue_incoming_supplier_commitment"
    )

    proposal, _ = _reviewed(
        session,
        business,
        "commitment_revise",
        {
            "commitment_id": purchase.id,
            "quantity": "7",
            "note": "Supplier discontinued the item; the rest will not come",
        },
        "revise-h03",
    )

    assert core.commitment_terms(session, tenant, [purchase.id])[purchase.id].open == 0
    assert purchase.id not in _records_of(
        session, tenant, "overdue_incoming_supplier_commitment"
    )
    revision = core.commitment_revisions(session, tenant, purchase.id)[-1]
    assert revision.note == "Supplier discontinued the item; the rest will not come"
    assert revision.quantity == Decimal(7)
    decisions = record_decisions(session, tenant, "commitment", purchase.id)
    assert (proposal.id, "commitment_revise") in {
        (row["id"], row["tool"]) for row in decisions
    }


def test_several_partial_supplier_invoices_are_summed_against_the_purchase(
    session, business
):
    """I06: two invoices bill one purchase line; billing beyond receipt is reported."""
    tenant = business.tenant.id
    _, order_line, purchase = _order(
        session, business, "purchase", "PO-I06", business.supplier.id, "10", "10"
    )
    _receive_into(session, business, "IN-I06", purchase, "8")

    _supplier_invoice(session, business, order_line, "6", "60.00", "ER-I06-1")
    # Six billed of eight received is ordinary.
    assert order_line.id not in _records_of(session, tenant, "billed_not_received")

    _supplier_invoice(session, business, order_line, "4", "40.00", "ER-I06-2")
    row = next(
        entry
        for entry in operational_exceptions(session, tenant, as_of=AS_OF)
        if entry.class_id == "billed_not_received" and entry.record_id == order_line.id
    )
    assert row.causal_values["billed_quantity"] == Decimal("10.0000")
    assert row.causal_values["unreceived_quantity"] == Decimal("2.0000")

    # Nothing more of the line can be billed through the guided invoice.
    with pytest.raises(core.InvalidOperation) as refused:
        _supplier_invoice(session, business, order_line, "1", "10.00", "ER-I06-3")
    assert refused.value.code == "invoice_quantity_exceeds_billable"


def test_a_carrier_freight_invoice_is_attributed_to_the_receipt_cost(
    session, business, cost_owner
):
    """I07: freight billed by a third party adds to the cost of the goods it carried."""
    tenant = business.tenant.id
    carrier = core.create_party(session, tenant, "Speedy Freight GmbH", "supplier")
    _, _, purchase = _order(
        session, business, "purchase", "PO-I07", business.supplier.id, "10", "10"
    )
    received = json.loads(
        _receive_into(session, business, "IN-I07", purchase, "10").output
    )
    receipt_movement_id = received["movement_ids"][0]

    freight = json.loads(
        confirm_tool(
            session,
            tenant,
            propose_tool(
                session,
                tenant,
                "supplier_invoice_free_record",
                {
                    "supplier_id": carrier.id,
                    "number": "FR-I07",
                    "currency": "EUR",
                    "gross_amount": "23.80",
                    "document_date": "2026-09-22",
                    "lines": [
                        {
                            "description": "Inbound freight PO-I07",
                            "quantity": "1",
                            "unit": "pcs",
                            "unit_price": "23.80",
                            "gross_amount": "23.80",
                            "line_type": "charge",
                            "reality_finance_v1": {"net": "20.00", "tax": "3.80"},
                        }
                    ],
                },
            ).id,
            confirmed=True,
        ).output
    )
    invoice_id = next(
        row["id"] for row in freight["records"] if row["family"] == "document"
    )
    invoice_line_id = next(
        row["id"] for row in freight["records"] if row["family"] == "document_line"
    )
    evidence = cost_evidence(session, tenant, invoice_id, invoice_line_id)
    principal = Principal(cost_owner.id)
    with caller(principal):
        proposal = create_change_proposal(
            session,
            tenant,
            "cost.change",
            {
                "operation": "assign",
                "document_id": invoice_id,
                "document_line_id": invoice_line_id,
                "expected_event_sequence": evidence["event_sequence"],
                "expected_evidence_hash": evidence["evidence_hash"],
                "basis": "net",
                "tax_treatment": "recoverable",
                "selected_basis_tax_inclusion": "excluded",
                "parts": [
                    {
                        "movement_id": receipt_movement_id,
                        "category": "inbound_freight",
                        "source_share": "20.00",
                        "cost_effect": 1,
                    }
                ],
                "reason": "Carrier freight for the PO-I07 receipt",
            },
        )
    approve_and_execute_proposal(
        session, tenant, proposal.id, confirming_principal=principal, confirmed=True
    )

    cost = run_read_tool(
        session, tenant, "cost.receipt.get", {"movement_id": receipt_movement_id}
    )
    assert Decimal(cost["known_cost"]) == Decimal("20.00")
    assert record_by_id(session, Document, invoice_id).party_id == carrier.id
    assert carrier.id != business.supplier.id


def test_variants_bought_together_each_hold_and_reserve_their_own_stock(
    session, business
):
    """K05: three sizes on one purchase are three items with three stocks."""
    tenant = business.tenant.id
    sizes = [
        core.create_item(session, tenant, f"JERSEY-{size}", f"Jersey {size}")
        for size in ("S", "M", "L")
    ]
    _, _, _, purchases = core.create_manual_order(
        session,
        tenant,
        "purchase",
        "PO-K05",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {"item_id": item.id, "quantity": q, "unit_price": "20", "gross_amount": g}
            for item, q, g in zip(sizes, ("3", "5", "2"), ("60", "100", "40"))
        ],
        "200",
    )
    _execute_delivery(
        session,
        tenant,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "IN-K05",
            "movements": [
                {
                    "commitment_id": purchase.id,
                    "item_id": item.id,
                    "to_location_id": business.location.id,
                    "quantity": q,
                }
                for purchase, item, q in zip(purchases, sizes, ("3", "5", "2"))
            ],
        },
    )
    assert [
        core.stock_at(session, tenant, item.id, business.location.id) for item in sizes
    ] == [Decimal(3), Decimal(5), Decimal(2)]

    effects = {}
    for item, wanted in zip(sizes, ("2", "5", "4")):
        promise = core.create_commitment(
            session,
            tenant,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            item.id,
            business.location.id,
            wanted,
            "2026-10-05",
        )
        proposal = prepare_delivery_action(
            session,
            tenant,
            "reserve",
            {"commitment_id": promise.id},
            request_id=f"reserve-k05-{item.sku}",
        )
        effects[item.sku] = json.loads(proposal.input)["_delivery_review"]["effect"]

    # Each size reserves only its own stock; only L runs short.
    assert {sku: effect["shortage"] for sku, effect in effects.items()} == {
        "JERSEY-S": "0",
        "JERSEY-M": "0",
        "JERSEY-L": "2",
    }
