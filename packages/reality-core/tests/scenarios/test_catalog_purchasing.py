"""Purchasing scenarios from the catalog (B07, B08, B09, G07, G13, G14, H03, H10, H11, H12, H16, I05, I06, I07, K05, R02)."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import test_costing_services as cost_fixtures
from conftest import record_by_id
from intake_review_support import (
    reviewed_assign_party_price_list,
    reviewed_create_price_list,
    reviewed_create_price_list_entry,
    reviewed_manual_order,
    reviewed_record_supplier_invoice,
)
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
    _, document, lines, commitments = reviewed_manual_order(
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
    second_supplier = reviewed_create_party(
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
    reviewed_record_supplier_invoice(
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
        reviewed_record_supplier_invoice(
            session, business.tenant.id, first_line.id, "1", "10", "SINV-I05-OVER"
        )
    reviewed_record_supplier_invoice(
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
    tiers = reviewed_create_price_list(
        session, tenant, "SUP-TIERS", "Supplier tiers", "purchase", "EUR"
    )
    reviewed_create_price_list_entry(
        session, tenant, tiers.id, business.item.id, 1, "5.00", "pcs"
    )
    ten_or_more = reviewed_create_price_list_entry(
        session, tenant, tiers.id, business.item.id, 10, "4.00", "pcs"
    )
    reviewed_assign_party_price_list(session, tenant, business.supplier.id, tiers.id)
    _, _, lines, _ = reviewed_manual_order(
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
            confirmed=True,
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
    _, _, _lines, commitments = reviewed_manual_order(
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
    carrier = reviewed_create_party(session, tenant, "Speedy Freight GmbH", "supplier")
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
        reviewed_create_item(session, tenant, f"JERSEY-{size}", f"Jersey {size}")
        for size in ("S", "M", "L")
    ]
    _, _, _, purchases = reviewed_manual_order(
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


# --- Spec 314: receipts without a purchase (H09) and a partial receipt (B09) ---


def _receipts(session, business):
    return set(
        session.scalars(
            select(Movement.id).where(
                Movement.tenant_id == business.tenant.id, Movement.type == "receipt"
            )
        )
    )


def _receive_unordered(session, business, tracking, **extra):
    before = _receipts(session, business)
    _execute_delivery(
        session,
        business.tenant.id,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": tracking,
            "movements": [
                {
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": "2",
                    **extra,
                }
            ],
        },
    )
    (movement_id,) = _receipts(session, business) - before
    return movement_id


def test_a_receipt_without_a_purchase_order_says_why_it_arrived(session, business):
    """H09: a sample explains itself; a misdelivery is reported until linked."""
    tenant = business.tenant.id

    # Free samples: the receiving clerk states why they came.
    before = _receipts(session, business)
    _reviewed(
        session,
        business,
        "movement_create",
        {
            "movement_type": "receipt",
            "item_id": business.item.id,
            "quantity": "2",
            "to_location_id": business.location.id,
            "reason": "Free samples from the supplier's new range",
        },
        "h09-samples",
    )
    (samples,) = _receipts(session, business) - before
    explanation = run_read_tool(
        session, tenant, "movement_explanation", {"movement_id": samples}
    )
    assert (explanation["kind"], explanation["reason"]) == (
        "explicit_reason",
        "Free samples from the supplier's new range",
    )

    # A parcel nobody ordered, received at the dock without a word.
    misdelivered = _receive_unordered(session, business, "TRK-H09-1")
    unexplained = _records_of(session, tenant, "unexplained_movement")
    assert misdelivered in unexplained
    assert samples not in unexplained
    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 4

    # It turns out to be an early delivery of a purchase ordered by phone.
    _, _, purchase = _order(
        session, business, "purchase", "PO-H09", business.supplier.id, "2", "10"
    )
    received = core.fulfilled_quantity(session, tenant, purchase.id)
    assert received == 0
    core.correct_movement(
        session,
        tenant,
        misdelivered,
        reason="Phone order PO-H09, recorded afterwards",
        replacement={
            "type": "receipt",
            "item_id": business.item.id,
            "quantity": "2",
            "to_location_id": business.location.id,
            "commitment_id": purchase.id,
        },
    )

    assert _records_of(session, tenant, "unexplained_movement") == set()
    assert core.fulfilled_quantity(session, tenant, purchase.id) == 2
    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 4


# --- Spec 305: serving backorders (B07, B08, B09, G13, H16, R02) ---------------------


def _sales(session, business, number, quantity, due):
    _, _, _, commitments = reviewed_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit_price": "20",
                "gross_amount": str(Decimal(quantity) * 20),
            }
        ],
        str(Decimal(quantity) * 20),
        requested_delivery_at=due,
    )
    return commitments[0]


def _purchase(session, business, number, quantity, due="2026-10-12"):
    _, _, _, commitments = reviewed_manual_order(
        session,
        business.tenant.id,
        "purchase",
        number,
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit_price": "10",
                "gross_amount": str(Decimal(quantity) * 10),
            }
        ],
        str(Decimal(quantity) * 10),
        requested_delivery_at=due,
    )
    return commitments[0]


def _assign_to(session, business, purchase, customer, quantity, request_id):
    _reviewed(
        session,
        business,
        "supply_assign",
        {
            "supplier_commitment_id": purchase.id,
            "purpose": "customer_demand",
            "customer_commitment_id": customer.id,
            "quantity": quantity,
        },
        request_id,
    )


def _serve(session, business, purchase=None, lines=None):
    """Review serving backorders, then confirm it as a person; returns the review."""
    arguments = {"item_id": business.item.id, "location_id": business.location.id}
    if purchase:
        arguments["supplier_commitment_id"] = purchase.id
    if lines is not None:
        arguments["lines"] = [
            {"commitment_id": promise.id, "quantity": quantity}
            for promise, quantity in lines
        ]
    proposal = create_change_proposal(
        session, business.tenant.id, "backorders_serve", arguments
    )
    review = json.loads(proposal.output)["backorder_serving"]
    # The review reserves nothing.
    assert review["lines"] and all(
        _reserved(session, business, line["commitment_id"]) == 0
        or line["commitment_id"] in {p.id for p, _ in lines or ()}
        for line in review["lines"]
    )
    approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )
    return review


def _reserved(session, business, commitment_id):
    session.expire_all()
    return core.commitment_terms(session, business.tenant.id, [commitment_id])[
        commitment_id
    ].reserved


def _split(session, business, promise):
    customer = supply_coverage(
        session, business.tenant.id, customer_commitment_id=promise.id
    )["customer"]
    return customer["arrived"], customer["still_to_come"]


def test_a_receipt_serves_the_earlier_due_backorder_first(session, business):
    """B08: two orders wait; the receipt goes to the one due first, as a person confirms."""
    tenant = business.tenant.id
    later = _sales(session, business, "SO-B08-1", "3", "2026-10-20")
    earlier = _sales(session, business, "SO-B08-2", "3", "2026-10-10")
    purchase = _purchase(session, business, "PO-B08", "4")
    # Positive control: before the goods arrive both orders are at risk.
    assert {later.id, earlier.id} <= _records_of(
        session, tenant, "outgoing_commitment_at_risk"
    )
    _receive_into(session, business, "TRK-B08", purchase, "4")
    # A receipt reserves nothing by itself.
    assert (
        _reserved(session, business, later.id),
        _reserved(session, business, earlier.id),
    ) == (0, 0)

    review = _serve(session, business, purchase)

    assert [(line["commitment_id"], line["quantity"]) for line in review["lines"]] == [
        (earlier.id, "3"),
        (later.id, "1"),
    ]
    assert (
        _reserved(session, business, earlier.id),
        _reserved(session, business, later.id),
    ) == (3, 1)
    at_risk = _records_of(session, tenant, "outgoing_commitment_at_risk")
    assert earlier.id not in at_risk
    assert later.id in at_risk


def test_a_customer_specific_purchase_goes_to_its_order(session, business):
    """H16 (cross-docking): the assigned order is served first, though another is due earlier."""
    assigned = _sales(session, business, "SO-H16-1", "3", "2026-10-25")
    earlier = _sales(session, business, "SO-H16-2", "3", "2026-10-10")
    purchase = _purchase(session, business, "PO-H16", "3")
    _assign_to(session, business, purchase, assigned, "3", "h16-assign")
    _receive_into(session, business, "TRK-H16", purchase, "3")

    review = _serve(session, business, purchase)

    assert [(line["commitment_id"], line["why"]) for line in review["lines"]] == [
        (assigned.id, "assigned"),
        (earlier.id, "due"),
    ]
    assert (
        _reserved(session, business, assigned.id),
        _reserved(session, business, earlier.id),
    ) == (3, 0)


def test_a_partial_receipt_names_the_backorders_left_uncovered(session, business):
    """B09: a receipt of 4 against 3 + 3 + 3 covers the first fully and the second partly."""
    tenant = business.tenant.id
    customers = [
        _sales(session, business, f"SO-B09-{n}", "3", "2026-10-20") for n in (1, 2, 3)
    ]
    purchase = _purchase(session, business, "PO-B09", "9")
    for n, customer in enumerate(customers, start=1):
        _assign_to(session, business, purchase, customer, "3", f"b09-assign-{n}")
    # Positive control: before the receipt everything is still to come.
    assert [_split(session, business, c) for c in customers] == [(0, 3)] * 3

    _receive_into(session, business, "TRK-B09", purchase, "4")

    assert [_split(session, business, c) for c in customers] == [(3, 0), (1, 2), (0, 3)]
    _serve(session, business, purchase)
    assert [_reserved(session, business, c.id) for c in customers] == [3, 1, 0]
    at_risk = _records_of(session, tenant, "outgoing_commitment_at_risk")
    assert customers[0].id not in at_risk
    assert {customers[1].id, customers[2].id} <= at_risk


def test_stock_only_on_order_is_promised_by_its_purchase_date(session, business):
    """B07: no stock, one open purchase: the answer names the purchase and its date."""
    tenant = business.tenant.id
    # Positive control: nothing in stock and nothing on order, nothing to promise.
    empty = run_read_tool(
        session, tenant, "available_to_promise", {"item_id": business.item.id}
    )
    assert (empty["now"]["free"], empty["purchases"]) == ("0", [])
    waiting = _sales(session, business, "SO-B07-1", "4", "2026-10-20")
    purchase = _purchase(session, business, "PO-B07", "10", due="2026-10-12")
    _assign_to(session, business, purchase, waiting, "4", "b07-assign")

    answer = run_read_tool(
        session, tenant, "available_to_promise", {"item_id": business.item.id}
    )

    assert answer["now"]["free"] == "0"
    (row,) = answer["purchases"]
    assert (row["commitment_id"], row["due_at"], row["adds"], row["total"]) == (
        purchase.id,
        "2026-10-12",
        "6",
        "6",
    )
    assert row["supplier"] == business.supplier.name


def test_a_cancelled_order_frees_its_purchase_before_the_purchase_is_reduced(
    session, business
):
    """G13: the cancellation ends the assignment; reducing the purchase is its own step."""
    tenant = business.tenant.id
    customer = _sales(session, business, "SO-G13", "4", "2026-10-20")
    purchase = _purchase(session, business, "PO-G13", "10")
    _assign_to(session, business, purchase, customer, "4", "g13-assign")
    assert (
        supply_coverage(session, tenant, supplier_commitment_id=purchase.id)[
            "supplier"
        ]["customer_assigned"]
        == 4
    )

    _reviewed(
        session,
        business,
        "commitment_cancel",
        {"commitment_id": customer.id, "reason": "Customer withdrew the order"},
        "g13-cancel",
    )

    supplier = supply_coverage(session, tenant, supplier_commitment_id=purchase.id)[
        "supplier"
    ]
    assert (supplier["customer_assigned"], supplier["unassigned"]) == (0, 10)
    assert (
        run_read_tool(
            session, tenant, "available_to_promise", {"item_id": business.item.id}
        )["purchases"][0]["adds"]
        == "10"
    )
    _reviewed(
        session,
        business,
        "commitment_revise",
        {
            "commitment_id": purchase.id,
            "quantity": "6",
            "note": "Reduced after SO-G13 was cancelled",
        },
        "g13-reduce",
    )
    assert (
        run_read_tool(
            session, tenant, "available_to_promise", {"item_id": business.item.id}
        )["purchases"][0]["adds"]
        == "6"
    )


def test_two_customers_an_under_delivery_a_key_customer_and_a_cancellation(
    session, business
):
    """R02: two customers wait for one purchase that comes short; the key customer is
    reserved first by a person, the other cancels and its assignment ends."""
    tenant = business.tenant.id
    other = _sales(session, business, "SO-R02-1", "3", "2026-10-15")
    key = _sales(session, business, "SO-R02-2", "3", "2026-10-20")
    purchase = _purchase(session, business, "PO-R02", "6")
    _assign_to(session, business, purchase, other, "3", "r02-assign-1")
    _assign_to(session, business, purchase, key, "3", "r02-assign-2")
    _receive_into(session, business, "TRK-R02", purchase, "4")
    _reviewed(
        session,
        business,
        "commitment_revise",
        {
            "commitment_id": purchase.id,
            "quantity": "4",
            "note": "Supplier delivers only 4",
        },
        "r02-short",
    )
    # In assignment order the other customer would be served fully first, and
    # nothing more comes for the key customer once the purchase was reduced.
    assert (_split(session, business, other), _split(session, business, key)) == (
        (3, 0),
        (1, 0),
    )

    review = _serve(session, business, purchase, lines=[(key, "3"), (other, "1")])

    assert {line["commitment_id"]: line["quantity"] for line in review["lines"]} == {
        other.id: "1",
        key.id: "3",
    }
    assert (
        _reserved(session, business, key.id),
        _reserved(session, business, other.id),
    ) == (3, 1)

    _reviewed(
        session,
        business,
        "commitment_cancel",
        {"commitment_id": other.id, "reason": "Customer cancels the rest"},
        "r02-cancel",
    )

    coverage = supply_coverage(session, tenant, supplier_commitment_id=purchase.id)
    assert [item["customer_commitment_id"] for item in coverage["items"]] == [key.id]
    assert _reserved(session, business, other.id) == 0
    assert _split(session, business, key) == (3, 0)
    assert key.id not in _records_of(session, tenant, "outgoing_commitment_at_risk")


# --- O05 (spec 301) -------------------------------------------------------------------


def test_bought_in_cartons_of_twelve_and_held_in_pieces(session, business):
    """O05: buy 5 cartons of 12, receive them in cartons, hold and sell pieces."""
    from reality.services.delivery_reads import delivery_case

    tenant = business.tenant.id
    item = business.item
    reviewed_update_item(
        session,
        tenant,
        item.id,
        item.sku,
        item.name,
        "pcs",
        purchase_unit="box",
        conversion_factor="12",
    )
    order = {
        "direction": "purchase",
        "number": "PO-O05",
        "company_party_id": business.company.id,
        "counterparty_id": business.supplier.id,
        "location_id": business.location.id,
        "currency": "EUR",
        "gross_amount": "300.00",
        "lines": [
            {
                "item_id": item.id,
                "quantity": "5",
                "unit": "box",
                "unit_price": "60.00",
                "gross_amount": "300.00",
            }
        ],
    }
    # A unit the item states nothing about is refused before anything is recorded.
    with pytest.raises(core.InvalidOperation) as refused:
        prepare_delivery_action(
            session,
            tenant,
            "order_create",
            {
                **order,
                "number": "PO-O05-X",
                "lines": [{**order["lines"][0], "unit": "pallet"}],
            },
            request_id="o05-pallet",
        )
    assert refused.value.code == "purchase_unit_not_convertible"

    _reviewed(session, business, "order_create", order, "o05-order")
    document = session.scalars(
        select(Document).where(
            Document.tenant_id == tenant, Document.number == "PO-O05"
        )
    ).one()
    promise = session.scalars(
        select(core.Commitment).where(
            core.Commitment.tenant_id == tenant,
            core.Commitment.document_id == document.id,
        )
    ).one()
    assert promise.quantity == Decimal("60.0000")

    # Three cartons come in a package, two more on their own, both stated in cartons.
    executed = _execute_delivery(
        session,
        tenant,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "O05-1",
            "movements": [
                {
                    "commitment_id": promise.id,
                    "item_id": item.id,
                    "to_location_id": business.location.id,
                    "quantity": "3",
                    "unit": "box",
                }
            ],
        },
    )
    assert executed.status == "executed"
    _reviewed(
        session,
        business,
        "movement_create",
        {
            "movement_type": "receipt",
            "item_id": item.id,
            "quantity": "2",
            "unit": "box",
            "to_location_id": business.location.id,
            "commitment_id": promise.id,
        },
        "o05-receipt",
    )

    assert core.stock_at(session, tenant, item.id) == Decimal("60.0000")
    received = session.scalars(
        select(Movement).where(
            Movement.tenant_id == tenant, Movement.commitment_id == promise.id
        )
    ).all()
    assert sorted((m.quantity, m.stated_quantity, m.stated_unit) for m in received) == [
        (Decimal("24.0000"), Decimal("2.0000"), "box"),
        (Decimal("36.0000"), Decimal("3.0000"), "box"),
    ]
    case = delivery_case(session, tenant, promise.id)["case"]
    assert (Decimal(case["open"]), case["purchase_unit"]["received"]) == (0, "5")

    # The supplier invoices 5 cartons: it matches the 60 pieces received.
    _supplier_invoice(
        session, business, document_line(session, promise), "5", "300.00", "ER-O05"
    )
    findings = {row.class_id for row in operational_exceptions(session, tenant)}
    assert not {"billed_not_received", "receipt_unbilled", "units_not_comparable"} & (
        findings
    )

    # Pieces are what is sold: 7 of the 60 ship.
    _, _, _, sold = reviewed_manual_order(
        session,
        tenant,
        "sales",
        "SO-O05",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": item.id,
                "quantity": "7",
                "unit_price": "9",
                "gross_amount": "63",
            }
        ],
        "63",
    )
    core.reserve(session, tenant, sold[0].id)
    assert core.active_reserved(session, tenant, item.id) == Decimal("7.0000")


def document_line(session, promise):
    from reality.db.core import DocumentLine

    return session.get(DocumentLine, (promise.tenant_id, promise.document_line_id))


def test_reorder_for_stock_at_the_reorder_point(session, business):
    """G02: stock at a location falls to its reorder point; a buyer orders from it."""
    tenant = business.tenant.id
    item = business.item
    reviewed_update_item(
        session,
        tenant,
        item.id,
        item.sku,
        item.name,
        "pcs",
        purchase_unit="box",
        conversion_factor="12",
    )
    munich = reviewed_create_location(session, tenant, "Munich Warehouse")
    for location, quantity in ((business.location, "12"), (munich, "100")):
        core.record_movement(
            session,
            tenant,
            "opening_stock",
            item.id,
            quantity,
            to_location_id=location.id,
        )
    price_list = reviewed_create_price_list(
        session, tenant, "PL-PARTS", "Parts purchase", "purchase", "EUR"
    )
    reviewed_create_price_list_entry(
        session, tenant, price_list.id, item.id, "1", "54.00", "box"
    )
    reviewed_assign_party_price_list(session, tenant, business.supplier.id, price_list.id)

    # Both points are stated through the reviewed tool, nothing before confirming.
    for location in (business.location, munich):
        proposal = create_change_proposal(
            session,
            tenant,
            "reorder_point_set",
            {
                "item_id": item.id,
                "location_id": location.id,
                "reorder_point": "20",
                "reorder_quantity": "48",
            },
        )
        approve_and_execute_proposal(session, tenant, proposal.id, confirmed=True)

    def reached():
        return {
            row.trace["location_id"]: row
            for row in operational_exceptions(session, tenant)
            if row.class_id == "reorder_point_reached"
        }

    # Only the location at its point is proposed; Munich holds 100.
    (entry,) = reached().values()
    assert entry.trace["location_id"] == business.location.id
    values = entry.causal_values
    assert (
        values["available_quantity"],
        values["incoming_quantity"],
        values["proposed_quantity"],
        values["proposed_unit"],
        values["supplier"],
        values["unit_price"],
    ) == (
        Decimal(12),
        Decimal(0),
        Decimal(4),
        "box",
        business.supplier.name,
        Decimal("54.0000"),
    )

    # The buyer orders what the entry proposes, through the reviewed order.
    _reviewed(
        session,
        business,
        "order_create",
        {
            "direction": "purchase",
            "number": "PO-G02",
            "company_party_id": business.company.id,
            "counterparty_id": entry.trace["supplier_id"],
            "location_id": entry.trace["location_id"],
            "currency": "EUR",
            "gross_amount": "216.00",
            "lines": [
                {
                    "item_id": item.id,
                    "quantity": "4",
                    "unit": "box",
                    "unit_price": "54.00",
                    "gross_amount": "216.00",
                }
            ],
        },
        "g02-order",
    )
    # Forty-eight pieces on their way cover the point: nothing is proposed.
    assert reached() == {}

    # A customer reservation takes what Hamburg holds, but the open purchase
    # still covers the point: 12 − 12 reserved + 48 incoming is 48, above 20.
    _, _, _, sold = reviewed_manual_order(
        session,
        tenant,
        "sales",
        "SO-G02",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": item.id,
                "quantity": "12",
                "unit_price": "9",
                "gross_amount": "108",
            }
        ],
        "108",
    )
    core.reserve(session, tenant, sold[0].id)
    assert reached() == {}
    # Raising the point above what is there and coming brings the entry back.
    proposal = create_change_proposal(
        session,
        tenant,
        "reorder_point_set",
        {
            "item_id": item.id,
            "location_id": business.location.id,
            "reorder_point": "60",
            "reorder_quantity": "48",
        },
    )
    approve_and_execute_proposal(session, tenant, proposal.id, confirmed=True)
    (entry,) = reached().values()
    assert (
        entry.causal_values["available_quantity"],
        entry.causal_values["incoming_quantity"],
    ) == (Decimal(0), Decimal(48))


# --- Spec 309: foreign-currency purchasing (G08, I11, R06) -----------------------


def _exchange_account(session, business):

    account = reviewed_create_account(
        session,
        business.tenant.id,
        code="2660",
        name="Kursdifferenzen",
        role="exchange_difference",
    )
    reviewed_set_default_account(
        session,
        business.tenant.id,
        role="exchange_difference",
        account_id=account["id"],
    )


def _usd_purchase(session, business, number, quantity, price, supplier=None):
    gross = str(Decimal(quantity) * Decimal(price))
    _, _, lines, commitments = reviewed_manual_order(
        session,
        business.tenant.id,
        "purchase",
        number,
        business.company.id,
        (supplier or business.supplier).id,
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
        currency="USD",
        document_date="2026-09-01",
    )
    return lines[0], commitments[0]


def _usd_invoice(session, business, line, quantity, gross, number, rate):
    proposal, receipt = _reviewed(
        session,
        business,
        "supplier_invoice_record",
        {
            "lines": [
                {
                    "order_line_id": line.id,
                    "quantity": quantity,
                    "gross_amount": gross,
                    "reality_finance_v1": {"net": gross, "tax": "0"},
                }
            ],
            "gross_amount": gross,
            "number": number,
            "effective_at": "2026-09-20T10:00:00Z",
            "exchange_rate": rate,
        },
        number,
    )
    from reality.services.delivery_actions import delivery_proposal_detail

    # The recorded invoice proves itself against its review.
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "verified"
    )
    return {row["family"]: row["id"] for row in receipt["records"]}


def _payable(session, business, invoice_id):
    from reality.db.core import LedgerEntry

    return session.scalar(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == business.tenant.id,
            LedgerEntry.document_id == invoice_id,
            LedgerEntry.debit_credit == "credit",
        )
    )


def test_a_usd_purchase_is_invoiced_at_its_stated_rate(session, business):
    """G08: a USD purchase keeps its currency and is booked in EUR at the stated rate."""
    tenant = business.tenant.id
    line, purchase = _usd_purchase(session, business, "PO-G08", "100", "10")
    _receive_into(session, business, "IN-G08", purchase, "100")
    assert (purchase.currency, purchase.amount) == ("USD", Decimal(1000))

    # A USD invoice without its rate is refused.
    with pytest.raises(core.InvalidOperation) as refused:
        _usd_invoice(session, business, line, "100", "1000", "INV-G08", None)
    assert refused.value.code == "exchange_rate_required"

    invoice = _usd_invoice(session, business, line, "100", "1000", "INV-G08", "0.92")

    payable = _payable(session, business, invoice["document"])
    assert (payable.amount, payable.currency) == (Decimal(1000), "USD")
    assert (payable.company_amount, payable.exchange_rate) == (
        Decimal("920.00"),
        Decimal("0.92"),
    )
    assert core.open_invoice_amount(session, tenant, invoice["document"]) == 1000


def test_a_usd_invoice_paid_in_eur_realises_its_exchange_difference(session, business):
    """I11: the EUR payment of a USD invoice books the realised gain or loss."""
    tenant = business.tenant.id
    _exchange_account(session, business)
    line, purchase = _usd_purchase(session, business, "PO-I11", "100", "10")
    _receive_into(session, business, "IN-I11", purchase, "100")
    invoice = _usd_invoice(session, business, line, "100", "1000", "INV-I11", "0.92")[
        "document"
    ]

    first, _ = _reviewed(
        session,
        business,
        "supplier_payment_post",
        {"invoice_id": invoice, "amount": "400", "paid_amount": "372.00"},
        "PAY-I11-1",
    )
    exchange = json.loads(first.input)["_delivery_review"]["state"]["exchange"]
    assert (exchange["kind"], Decimal(exchange["difference"])) == ("loss", 4)
    _reviewed(
        session,
        business,
        "supplier_payment_post",
        {"invoice_id": invoice, "amount": "600", "paid_amount": "540.00"},
        "PAY-I11-2",
    )

    assert core.open_invoice_amount(session, tenant, invoice) == 0
    # 920.00 at the invoice rate, 912.00 paid: a loss of 4.00 and a gain of 12.00.
    assert core.account_balance(session, tenant, "exchange_difference") == 0
    from reality.db.core import LedgerEntry

    differences = sorted(
        (entry.debit_credit, entry.company_amount)
        for entry in session.scalars(
            select(LedgerEntry).where(LedgerEntry.tenant_id == tenant)
        )
        if entry.account == "exchange_difference"
    )
    assert differences == [("credit", Decimal("12.00")), ("debit", Decimal("4.00"))]


def test_an_import_container_lands_in_eur_with_freight_and_duty(
    session, business, cost_owner
):
    """R06: five USD purchases from two suppliers arrive in one container; one
    receipt's landed cost reads in EUR from its invoice rate, freight and duty, and
    the two waiting customer orders are served from the arrival."""
    tenant = business.tenant.id
    second = reviewed_create_party(session, tenant, "Shenzhen Parts Ltd.", "supplier")
    waiting = [
        _sales(session, business, "SO-R06-1", "30", "2026-10-01"),
        _sales(session, business, "SO-R06-2", "20", "2026-10-03"),
    ]
    purchases = [
        _usd_purchase(
            session, business, f"PO-R06-{index}", "10", "10", supplier=supplier
        )
        for index, supplier in enumerate(
            (business.supplier, business.supplier, business.supplier, second, second),
            start=1,
        )
    ]
    receipts = [
        json.loads(
            _receive_into(session, business, f"CNT-R06-{index}", purchase, "10").output
        )["movement_ids"][0]
        for index, (_, purchase) in enumerate(purchases, start=1)
    ]
    invoices = [
        _usd_invoice(session, business, line, "10", "100", f"INV-R06-{index}", rate)
        for index, ((line, _), rate) in enumerate(
            zip(purchases, ("0.92", "0.92", "0.92", "0.91", "0.91"), strict=True),
            start=1,
        )
    ]
    assert (
        sorted(
            _payable(session, business, row["document"]).company_amount
            for row in invoices
        )
        == [Decimal("91.00")] * 2 + [Decimal("92.00")] * 3
    )

    # Freight and duty in EUR, on the first receipt.
    principal = Principal(cost_owner.id)
    for number, category, net in (
        ("FR-R06", "inbound_freight", "8.00"),
        ("ZOLL-R06", "duty", "4.00"),
    ):
        recorded = json.loads(
            confirm_tool(
                session,
                tenant,
                propose_tool(
                    session,
                    tenant,
                    "supplier_invoice_free_record",
                    {
                        "supplier_id": business.supplier.id,
                        "number": number,
                        "currency": "EUR",
                        "gross_amount": net,
                        "document_date": "2026-09-22",
                        "lines": [
                            {
                                "description": f"{category} CNT-R06",
                                "quantity": "1",
                                "unit": "pcs",
                                "unit_price": net,
                                "gross_amount": net,
                                "line_type": "charge",
                                "reality_finance_v1": {"net": net, "tax": "0"},
                            }
                        ],
                    },
                ).id,
                confirmed=True,
            ).output
        )
        ids = {row["family"]: row["id"] for row in recorded["records"]}
        evidence = cost_evidence(session, tenant, ids["document"], ids["document_line"])
        with caller(principal):
            proposal = create_change_proposal(
                session,
                tenant,
                "cost.change",
                {
                    "operation": "assign",
                    "document_id": ids["document"],
                    "document_line_id": ids["document_line"],
                    "expected_event_sequence": evidence["event_sequence"],
                    "expected_evidence_hash": evidence["evidence_hash"],
                    "basis": "net",
                    "tax_treatment": "recoverable",
                    "selected_basis_tax_inclusion": "excluded",
                    "parts": [
                        {
                            "movement_id": receipts[0],
                            "category": category,
                            "source_share": net,
                            "cost_effect": 1,
                        }
                    ],
                    "reason": f"{category} of the container",
                },
            )
        approve_and_execute_proposal(
            session, tenant, proposal.id, confirming_principal=principal, confirmed=True
        )

    # The first invoice's rate is offered as the conversion basis and confirmed.
    first = invoices[0]
    evidence = cost_evidence(session, tenant, first["document"], first["document_line"])
    offer = evidence["offered_conversion_basis"]
    assert (offer["from_code"], offer["to_code"], offer["numerator"]) == (
        "USD",
        "EUR",
        "0.92",
    )
    basis = cost_fixtures.execute(
        session,
        business,
        cost_owner,
        {**offer, "expected_event_sequence": evidence["event_sequence"]},
    )["conversion_basis_revision_id"]
    evidence = cost_evidence(session, tenant, first["document"], first["document_line"])
    with caller(principal):
        goods = create_change_proposal(
            session,
            tenant,
            "cost.change",
            {
                "operation": "assign",
                "document_id": first["document"],
                "document_line_id": first["document_line"],
                "expected_event_sequence": evidence["event_sequence"],
                "expected_evidence_hash": evidence["evidence_hash"],
                "basis": "net",
                "tax_treatment": "recoverable",
                "selected_basis_tax_inclusion": "excluded",
                "parts": [
                    {
                        "movement_id": receipts[0],
                        "category": "goods",
                        "source_share": "100",
                        "cost_effect": 1,
                        "conversion_basis_revision_id": basis,
                    }
                ],
                "reason": "Goods of PO-R06-1 at the invoice rate",
            },
        )
    approve_and_execute_proposal(
        session, tenant, goods.id, confirming_principal=principal, confirmed=True
    )
    cost = run_read_tool(
        session, tenant, "cost.receipt.get", {"movement_id": receipts[0]}
    )
    # 100 USD at 0.92 is 92.00 EUR, plus 8.00 freight and 4.00 duty.
    assert (Decimal(cost["known_cost"]), cost["currency"]) == (Decimal("104.00"), "EUR")

    _serve(session, business)
    assert [_reserved(session, business, promise.id) for promise in waiting] == [
        Decimal(30),
        Decimal(20),
    ]


# --- Spec 310: confirmations, terms, cancellation charges, three-way match ----------


def _purchase_line(session, business, number, quantity="100", price="10"):
    gross = str(Decimal(quantity) * Decimal(price))
    _, document, (line,), (promise,) = reviewed_manual_order(
        session,
        business.tenant.id,
        "purchase",
        number,
        business.company.id,
        business.supplier.id,
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
    return document, line, promise


def _match(session, business, document):
    from reality.services.purchase_match import purchase_match

    return purchase_match(session, business.tenant.id, document.id)


def test_a_supplier_confirms_less_later_and_dearer_and_is_billed_as_confirmed(
    session, business
):
    """G09: the confirmation restates quantity, date and price; the invoice follows it."""
    tenant = business.tenant.id
    document, line, promise = _purchase_line(session, business, "PO-G09")

    _reviewed(
        session,
        business,
        "commitment_revise",
        {
            "commitment_id": promise.id,
            "quantity": "90",
            "due_at": "2026-10-19T00:00:00Z",
            "unit_price": "10.50",
            "note": "Order confirmation AB-G09",
        },
        "rev-G09",
    )
    _receive_into(session, business, "IN-G09", promise, "90")
    invoice = _supplier_invoice(session, business, line, "90", "945", "INV-G09")

    (row,) = _match(session, business, document)["lines"]
    assert (
        row["ordered"],
        row["in_force"],
        row["ordered_unit_price"],
        row["agreed_unit_price"],
    ) == (
        "100",
        "90",
        "10",
        "10.5",
    )
    assert row["matched"] is True
    billed = session.scalars(
        select(core.DocumentLine).where(
            core.DocumentLine.tenant_id == tenant,
            core.DocumentLine.document_id == invoice,
        )
    ).one()
    # Billed at the confirmed price, nothing differs (tests/test_purchasing_depth.py
    # reports a price above it as the control).
    assert billed.id not in _records_of(session, tenant, "invoice_price_differs")
    assert billed.unit_price == Decimal("10.5")


def test_a_minimum_and_a_pack_size_are_named_and_the_surplus_is_stock(
    session, business
):
    """G06: the review names the minimum and pack size; the person orders more."""
    tenant = business.tenant.id
    proposal = create_change_proposal(
        session,
        tenant,
        "supplier_item_terms_set",
        {
            "party_id": business.supplier.id,
            "item_id": business.item.id,
            "minimum_quantity": "50",
            "order_multiple": "12",
        },
    )
    approve_and_execute_proposal(session, tenant, proposal.id, confirmed=True)
    need = _sales(session, business, "SO-G06", "30", "2026-10-20")
    arguments = {
        "direction": "purchase",
        "number": "PO-G06",
        "company_party_id": business.company.id,
        "counterparty_id": business.supplier.id,
        "location_id": business.location.id,
        "currency": "EUR",
        "gross_amount": "300",
        "lines": [
            {
                "item_id": business.item.id,
                "quantity": "30",
                "unit_price": "10",
                "gross_amount": "300",
            }
        ],
    }
    review = json.loads(
        prepare_delivery_action(
            session, tenant, "order_create", arguments, request_id="PO-G06-30"
        ).input
    )["_delivery_review"]
    terms = review["state"]["supplier_terms"]["0"]
    assert (
        terms["below_minimum"],
        terms["off_multiple"],
        terms["suggested_quantity"],
    ) == (
        True,
        True,
        "60",
    )
    # The person orders what the supplier sells: 60, for a need of 30.
    _reviewed(
        session,
        business,
        "order_create",
        {
            **arguments,
            "gross_amount": "600",
            "lines": [
                {**arguments["lines"][0], "quantity": "60", "gross_amount": "600"}
            ],
        },
        "PO-G06-60",
    )
    purchase = session.scalars(
        select(core.Commitment)
        .join(core.Document, core.Document.id == core.Commitment.document_id)
        .where(core.Commitment.tenant_id == tenant, core.Document.number == "PO-G06")
    ).one()
    _receive_into(session, business, "IN-G06", purchase, "60")
    core.reserve(session, tenant, need.id)
    # 30 serve the order and 30 stay free stock.
    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 60
    assert _reserved(session, business, need.id) == 30


def test_a_purchase_cancelled_after_production_records_the_suppliers_charge(
    session, business
):
    """G12: the cancellation and the supplier's charge, with no purchase finding."""
    tenant = business.tenant.id
    document, line, promise = _purchase_line(session, business, "PO-G12", "20")
    _reviewed(
        session,
        business,
        "commitment_cancel",
        {
            "commitment_id": promise.id,
            "reason": "No longer needed; supplier had produced",
        },
        "cxl-G12",
    )
    charge = json.loads(
        confirm_tool(
            session,
            tenant,
            propose_tool(
                session,
                tenant,
                "supplier_invoice_free_record",
                {
                    "supplier_id": business.supplier.id,
                    "number": "CXL-G12",
                    "currency": "EUR",
                    "gross_amount": "40.00",
                    "lines": [
                        {
                            "description": "Cancellation charge PO-G12",
                            "quantity": "1",
                            "unit": "pcs",
                            "unit_price": "40.00",
                            "gross_amount": "40.00",
                            "line_type": "charge",
                            "billed_document_line_id": line.id,
                        }
                    ],
                },
            ).id,
            confirmed=True,
        ).output
    )
    invoice_id = next(r["id"] for r in charge["records"] if r["family"] == "document")
    assert core.open_invoice_amount(session, tenant, invoice_id) == Decimal(40)
    assert line.id not in _records_of(session, tenant, "billed_not_received")
    (row,) = _match(session, business, document)["lines"]
    assert (
        row["cancelled"],
        row["matched"],
        [c["amount"] for c in row["charges"]],
    ) == (
        True,
        True,
        ["40"],
    )


def test_a_purchase_receipt_and_invoice_that_agree_are_matched(session, business):
    """I01: a positive three-way match, and the line that is not."""
    tenant = business.tenant.id
    document, line, promise = _purchase_line(session, business, "PO-I01", "10")
    _, short_line, short = _purchase_line(session, business, "PO-I01-B", "10")
    _receive_into(session, business, "IN-I01", promise, "10")
    _supplier_invoice(session, business, line, "10", "100", "INV-I01")
    _receive_into(session, business, "IN-I01-B", short, "8")
    _supplier_invoice(session, business, short_line, "8", "80", "INV-I01-B")

    assert _match(session, business, document)["matched"] is True
    other = session.scalars(
        select(core.Document).where(
            core.Document.tenant_id == tenant, core.Document.number == "PO-I01-B"
        )
    ).one()
    # Positive control: the short line names its difference.
    assert _match(session, business, other)["lines"][0]["differences"] == [
        "received_short"
    ]


# --- G10: an unconfirmed purchase order (spec 346) ------------------------------


def test_a_purchase_order_the_supplier_has_not_confirmed_is_flagged(session, business):
    """G10: asked about before its delivery date, cleared by the confirmation."""
    tenant = business.tenant.id
    placed = core.now() - timedelta(days=4)
    due = (core.now() + timedelta(days=21)).isoformat()

    def purchase(number):
        _, _, _, (promise,) = reviewed_manual_order(
            session,
            tenant,
            "purchase",
            number,
            business.company.id,
            business.supplier.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "50",
                    "unit_price": "8",
                    "gross_amount": "400",
                }
            ],
            "400",
            ordered_at=placed,
            requested_delivery_at=due,
        )
        return promise

    silent = purchase("PO-G10-A")
    answered = purchase("PO-G10-B")

    def unconfirmed():
        return {
            row.record_id: row
            for row in operational_exceptions(session, tenant)
            if row.class_id == "purchase_order_unconfirmed"
        }

    # Neither supplier has answered; the delivery date is still three weeks away.
    assert {silent.id, answered.id} <= set(unconfirmed())
    assert not any(
        row.class_id == "overdue_incoming_supplier_commitment"
        and row.record_id in {silent.id, answered.id}
        for row in operational_exceptions(session, tenant)
    )

    # The second supplier confirms exactly as ordered: the buyer restates its date.
    _reviewed(
        session,
        business,
        "commitment_revise",
        {
            "commitment_id": answered.id,
            "due_at": due,
            "note": "Order confirmation AB-7781 as ordered",
        },
        "g10-confirm",
    )

    found = unconfirmed()
    assert answered.id not in found
    # Positive control: the supplier who stayed silent is still asked about.
    assert "PO-G10-A" in found[silent.id].impact


# --- O06 (spec 345) -------------------------------------------------------------------


def _state_supplier_number(session, business, supplier_id, number, name):
    tenant = business.tenant.id
    return confirm_tool(
        session,
        tenant,
        propose_tool(
            session,
            tenant,
            "supplier_item_number_set",
            {
                "party_id": supplier_id,
                "item_id": business.item.id,
                "supplier_item_number": number,
                "supplier_item_name": name,
            },
        ).id,
    )


def _purchase_by_number(session, business, supplier_id, number, quoted, request_id):
    _, created = _reviewed(
        session,
        business,
        "order_create",
        {
            "direction": "purchase",
            "number": number,
            "company_party_id": business.company.id,
            "counterparty_id": supplier_id,
            "location_id": business.location.id,
            "gross_amount": "100",
            "lines": [
                {
                    "supplier_item_number": quoted,
                    "quantity": "10",
                    "unit": "pcs",
                    "unit_price": "10",
                    "gross_amount": "100",
                }
            ],
        },
        request_id,
    )
    return created


def test_two_suppliers_name_one_item_by_their_own_numbers(session, business):
    """O06: each supplier's own number resolves to our item, on order and invoice."""
    tenant = business.tenant.id
    velo = reviewed_create_party(session, tenant, "Velo Import AG", "supplier")
    _state_supplier_number(
        session, business, business.supplier.id, "LF900-12", "Laufrad 28 Lindner"
    )
    _state_supplier_number(session, business, velo.id, "VI-77", "Wheel 28in")

    # Each supplier is ordered from by its own number; both mean our wheel.
    _purchase_by_number(
        session, business, business.supplier.id, "PO-O06-A", "lf 900-12", "o06-a"
    )
    _purchase_by_number(session, business, velo.id, "PO-O06-B", "VI-77", "o06-b")
    orders = {
        number: session.scalars(
            select(Document).where(
                Document.tenant_id == tenant, Document.number == number
            )
        ).one()
        for number in ("PO-O06-A", "PO-O06-B")
    }
    match = run_read_tool(
        session, tenant, "purchase_match", {"document_id": orders["PO-O06-A"].id}
    )
    (line,) = match["lines"]
    assert (line["item_id"], line["supplier_item_number"]) == (
        business.item.id,
        "lf 900-12",
    )
    other = run_read_tool(
        session, tenant, "purchase_match", {"document_id": orders["PO-O06-B"].id}
    )["lines"][0]
    assert (other["item_id"], other["supplier_item_number"]) == (
        business.item.id,
        "VI-77",
    )

    # Lindner delivers and invoices quoting its own number again.
    commitment = session.scalars(
        select(core.Commitment).where(
            core.Commitment.tenant_id == tenant,
            core.Commitment.document_id == orders["PO-O06-A"].id,
        )
    ).one()
    _receive_into(session, business, "TRK-O06", commitment, "10")
    confirm_tool(
        session,
        tenant,
        propose_tool(
            session,
            tenant,
            "document_create",
            {
                "document_type": "supplier_invoice",
                "number": "LF-RE-O06",
                "party_id": business.supplier.id,
                "gross_amount": "100",
                "lines": [
                    {
                        "supplier_item_number": "LF900-12",
                        "quantity": "10",
                        "unit": "pcs",
                        "unit_price": "10",
                        "gross_amount": "100",
                        "billed_document_line_id": line["document_line_id"],
                    }
                ],
            },
        ).id,
        confirmed=True,
    )
    assert run_read_tool(
        session, tenant, "purchase_match", {"document_id": orders["PO-O06-A"].id}
    )["lines"][0]["matched"]

    # Positive control: Velo's number means nothing at Lindner.
    with pytest.raises(core.InvalidOperation) as refused:
        _purchase_by_number(
            session, business, business.supplier.id, "PO-O06-C", "VI-77", "o06-c"
        )
    assert refused.value.code == "supplier_item_number_unknown"


from intake_review_support import (
    reviewed_create_account,
    reviewed_create_item,
    reviewed_create_location,
    reviewed_create_party,
    reviewed_set_default_account,
    reviewed_update_item,
)
