import json
from decimal import Decimal

from conftest import record_by_id
from sqlalchemy import select
from unified_fixtures import delivery_fixture

from reality.db.core import Movement, SourceRecord
from reality.services.core import (
    correct_movement,
    create_commitment,
    fulfilled_quantity,
    reserve,
    stock_at,
)
from reality.services.shipments import (
    record_shipment_event,
    record_shipment_notice,
    shipment_explain,
)
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def _execute(session, tenant_id, tool, arguments):
    proposal = create_change_proposal(session, tenant_id, tool, arguments)
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session,
        tenant_id,
        proposal.id,
        review_token=token,
        confirmed=True,
    )


def test_customer_dispatch_records_exact_package_contents_and_fulfillment(
    session, business
):
    fixture = delivery_fixture(session, business, quantity="10")
    reserve(session, business.tenant.id, fixture.commitment.id)
    proposal = _execute(
        session,
        business.tenant.id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "carrier": "DHL",
            "tracking_number": "OUT-10",
            "movements": [
                {
                    "commitment_id": fixture.commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "4",
                },
                {
                    "commitment_id": fixture.commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "6",
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
    assert sum((movement.quantity for movement in movements), Decimal()) == 10
    assert fulfilled_quantity(session, business.tenant.id, fixture.commitment.id) == 10
    detail = shipment_explain(session, business.tenant.id, receipt["shipment_id"])
    assert Decimal(detail["quantities"]["promised"]) == 10
    assert Decimal(detail["quantities"]["dispatched"]) == 10
    assert detail["quantities"]["announced"] is None
    assert detail["quantities"]["externally_delivered"] is None
    assert detail["quantities"]["received"] is None
    assert detail["observations"]["dispatched_at"] is not None
    assert (
        stock_at(session, business.tenant.id, business.item.id, business.location.id)
        == 10
    )

    corrected = correct_movement(
        session,
        business.tenant.id,
        movements[0].id,
        reason="Package count corrected",
        replacement={
            "type": "shipment",
            "item_id": business.item.id,
            "quantity": "3",
            "from_location_id": business.location.id,
            "commitment_id": fixture.commitment.id,
        },
    )
    corrected_detail = shipment_explain(
        session, business.tenant.id, receipt["shipment_id"]
    )
    corrected_ids = {row["id"] for row in corrected_detail["movements"]}
    assert movements[0].id not in corrected_ids
    assert corrected.replacement_movement_id in corrected_ids
    assert (
        sum(
            (Decimal(row["quantity"]) for row in corrected_detail["movements"]),
            Decimal(),
        )
        == 9
    )


def test_supplier_notice_has_zero_effect_then_package_receipt_changes_stock(
    session, business
):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "8",
        None,
    )
    before = stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    )
    _execute(
        session,
        business.tenant.id,
        "shipment_notice_record",
        {
            "direction": "inbound",
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "IN-8",
        },
    )
    assert (
        stock_at(session, business.tenant.id, business.item.id, business.location.id)
        == before
    )
    _execute(
        session,
        business.tenant.id,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "IN-8-RECEIVED",
            "movements": [
                {
                    "commitment_id": commitment.id,
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": "3",
                }
            ],
        },
    )
    assert (
        stock_at(session, business.tenant.id, business.item.id, business.location.id)
        == before + 3
    )
    assert fulfilled_quantity(session, business.tenant.id, commitment.id) == 3


def test_supplier_source_payload_and_carrier_warehouse_discrepancy_remain_distinct(
    session, business
):
    raw_payload = '{"pieces":[{"sku":"LIGHT","announced":"8"}],"vendor_extra":7}'
    source = SourceRecord(
        id="src_shipment_notice",
        tenant_id=business.tenant.id,
        source_system="carrier_fixture",
        source_type="shipment_notice",
        external_id="notice-173",
        payload=raw_payload,
        payload_hash="a" * 64,
        version=1,
    )
    session.add(source)
    session.flush()
    shipment, package, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="inbound",
        purpose="supplier_delivery",
        counterparty_id=business.supplier.id,
        source_record_id=source.id,
    )
    record_shipment_event(
        session,
        business.tenant.id,
        shipment.id,
        shipment_package_id=package.id,
        event_type="delivered",
        reporter_type="carrier",
        source_record_id=source.id,
    )

    detail = shipment_explain(session, business.tenant.id, shipment.id)
    assert record_by_id(session, SourceRecord, source.id).payload == raw_payload
    assert detail["quantities"]["announced"] is None
    assert detail["observations"]["externally_delivered"] is True
    assert detail["observations"]["received"] is False
    assert (
        detail["discrepancies"]["external_delivery_without_warehouse_receipt"] is True
    )
