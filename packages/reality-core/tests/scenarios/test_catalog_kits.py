"""Catalog scenarios for kits, bundles and light assembly (spec 333): K01-K04, K06."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import Commitment, Movement
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.exceptions import operational_exceptions
from reality.services.movement_explanations import movement_explanation
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def _reviewed(session, business, tool, arguments, request_id):
    proposal = prepare_delivery_action(
        session, business.tenant.id, tool, arguments, request_id=request_id
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    return json.loads(proposal.output if executed is None else executed.output)


def _confirmed(session, business, tool, arguments):
    """A kit tool: the server reviews, a person confirms."""
    proposal = create_change_proposal(
        session, business.tenant.id, tool, arguments, actor_type="human"
    )
    review = json.loads(proposal.output)["kit"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )
    return review, json.loads(executed.output)


def _bike_kit(session, business, *, shares=True):
    """A bike kit of one frame and two wheels; the frame carries 60 % of the price."""
    tenant = business.tenant.id
    kit = core.create_item(session, tenant, "KIT-BIKE", "Bike kit")
    frame = core.create_item(session, tenant, "FRAME", "Frame")
    wheel = core.create_item(session, tenant, "WHEEL", "Wheel")
    _confirmed(
        session,
        business,
        "kit_define",
        {
            "kit_item_id": kit.id,
            "components": [
                {
                    "item_id": frame.id,
                    "quantity": "1",
                    **({"share": "0.6"} if shares else {}),
                },
                {
                    "item_id": wheel.id,
                    "quantity": "2",
                    **({"share": "0.4"} if shares else {}),
                },
            ],
        },
    )
    return kit, frame, wheel


def _receive(session, business, item, quantity):
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        item.id,
        quantity,
        to_location_id=business.location.id,
    )


def _order(session, business, number, kit, quantity, gross):
    receipt = _reviewed(
        session,
        business,
        "order_create",
        {
            "direction": "sales",
            "number": number,
            "company_party_id": business.company.id,
            "counterparty_id": business.customer.id,
            "location_id": business.location.id,
            "currency": "EUR",
            "gross_amount": gross,
            "lines": [
                {
                    "item_id": kit.id,
                    "quantity": quantity,
                    "unit_price": str(Decimal(gross) / Decimal(quantity)),
                    "gross_amount": gross,
                }
            ],
        },
        number,
    )
    (promise_id,) = receipt["commitment_ids"]
    return session.get(Commitment, (business.tenant.id, promise_id))


def _assemble(session, business, kit, quantity):
    return _confirmed(
        session,
        business,
        "kit_assemble",
        {
            "kit_item_id": kit.id,
            "location_id": business.location.id,
            "quantity": quantity,
        },
    )


def _dispatch(session, business, promise, quantity, tracking):
    return _reviewed(
        session,
        business,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "carrier": "DHL",
            "tracking_number": tracking,
            "movements": [
                {
                    "commitment_id": promise.id,
                    "item_id": promise.item_id,
                    "from_location_id": business.location.id,
                    "quantity": quantity,
                }
            ],
        },
        tracking,
    )


def _on_hand(session, business, item):
    return core.stock_at(session, business.tenant.id, item.id, business.location.id)


def _availability(session, business, kit):
    (kit_row,) = [
        row
        for row in _read(session, business, "kits", {"item_id": kit.id})
        if row["kit_item_id"] == kit.id
    ]
    (here,) = kit_row["availability"]
    return here


def _read(session, business, tool, arguments):
    from reality.tools.application import TOOLS

    return TOOLS[tool].handler(session, business.tenant.id, arguments)


def _classes(session, business, class_id):
    return {
        row.record_id
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == class_id
    }


def test_a_kit_is_sold_and_shipped_from_its_components(session, business):
    """K01: availability is the minimum the components build; packing assembles it."""
    tenant = business.tenant.id
    kit, frame, wheel = _bike_kit(session, business)
    _receive(session, business, frame, "3")
    _receive(session, business, wheel, "4")
    promise = _order(session, business, "SO-K01", kit, "2", "200.00")

    here = _availability(session, business, kit)
    assert (here["kits_on_hand"], here["buildable"], here["limited_by"]) == (
        "0",
        "2",
        ["WHEEL"],
    )
    # The components cover the order: the kit is not sold beyond what exists.
    assert kit.id not in _classes(session, business, "item_oversold")

    review, assembled = _assemble(session, business, kit, "2")
    assert [(part["sku"], part["quantity"]) for part in review["consumes"]] == [
        ("FRAME", "2"),
        ("WHEEL", "4"),
    ]
    core.reserve(session, tenant, promise.id)
    _dispatch(session, business, promise, "2", "TRK-K01")

    session.refresh(promise)
    assert promise.status == "fulfilled"
    assert (
        _on_hand(session, business, frame),
        _on_hand(session, business, wheel),
        _on_hand(session, business, kit),
    ) == (1, 0, 0)
    # Every assembly movement names the statement that consumed the parts.
    explained = movement_explanation(session, tenant, assembled["movement_ids"][0])
    assert explained["kind"] == "assembly"
    assert explained["links"][0]["id"] == assembled["source_record_id"]


def test_a_kit_missing_one_component_is_held_back_whole(session, business):
    """K02: a missing wheel refuses the whole assembly; no half kit leaves."""
    tenant = business.tenant.id
    kit, frame, wheel = _bike_kit(session, business)
    _receive(session, business, frame, "1")
    _receive(session, business, wheel, "1")
    promise = _order(session, business, "SO-K02", kit, "1", "100.00")

    here = _availability(session, business, kit)
    assert (here["available"], here["limited_by"]) == ("0", ["WHEEL"])
    with pytest.raises(core.InvalidOperation) as refused:
        _assemble(session, business, kit, "1")
    assert (refused.value.code, refused.value.values["sku"]) == (
        "kit_component_short",
        "WHEEL",
    )
    session.rollback()
    # Nothing was consumed, and the kit order cannot ship: there is no kit.
    assert (_on_hand(session, business, frame), _on_hand(session, business, wheel)) == (
        1,
        1,
    )
    with pytest.raises(core.InvalidOperation):
        _dispatch(session, business, promise, "1", "TRK-K02-EARLY")
    session.rollback()
    assert kit.id in _classes(session, business, "item_oversold")

    # Positive control: the missing wheel arrives and the kit ships whole.
    _receive(session, business, wheel, "1")
    _assemble(session, business, kit, "1")
    core.reserve(session, tenant, promise.id)
    _dispatch(session, business, promise, "1", "TRK-K02")
    session.refresh(promise)
    assert promise.status == "fulfilled"
    assert kit.id not in _classes(session, business, "item_oversold")


def test_a_light_assembly_consumes_components_and_produces_the_item(session, business):
    """K04: paired movements under one statement, not corrected one by one."""
    tenant = business.tenant.id
    kit, frame, wheel = _bike_kit(session, business)
    _receive(session, business, frame, "5")
    _receive(session, business, wheel, "10")

    _, assembled = _assemble(session, business, kit, "3")

    movements = list(
        session.scalars(
            select(Movement).where(
                Movement.tenant_id == tenant,
                Movement.source_record_id == assembled["source_record_id"],
            )
        )
    )
    assert sorted((m.type, m.item_id, m.quantity) for m in movements) == sorted(
        [
            ("assembly_input", frame.id, Decimal("3.0000")),
            ("assembly_input", wheel.id, Decimal("6.0000")),
            ("assembly_output", kit.id, Decimal("3.0000")),
        ]
    )
    assert (
        _on_hand(session, business, frame),
        _on_hand(session, business, wheel),
        _on_hand(session, business, kit),
    ) == (2, 4, 3)
    # Assembled kits on hand plus what the rest builds.
    here = _availability(session, business, kit)
    assert (here["kits_on_hand"], here["buildable"], here["available"]) == (
        "3",
        "2",
        "5",
    )
    with pytest.raises(core.InvalidOperation) as refused:
        core.preview_movement_correction(
            session, tenant, movements[0].id, reason="Counted wrong"
        )
    assert refused.value.code == "movement_assembly_not_correctable"
    # Assembly movements are explained by their statement, never "unexplained".
    assert not {m.id for m in movements} & _classes(
        session, business, "unexplained_movement"
    )


def _invoiced_kit(session, business):
    tenant = business.tenant.id
    kit, frame, wheel = _bike_kit(session, business)
    _receive(session, business, frame, "1")
    _receive(session, business, wheel, "2")
    promise = _order(session, business, "SO-K06", kit, "1", "119.00")
    _assemble(session, business, kit, "1")
    core.reserve(session, tenant, promise.id)
    _dispatch(session, business, promise, "1", "TRK-K06")
    receipt = _reviewed(
        session,
        business,
        "sales_invoice_record",
        {
            "order_line_id": promise.document_line_id,
            "quantity": "1",
            "gross_amount": "119.00",
            "number": "RE-K06",
            "effective_at": "2026-09-01T10:00:00Z",
            "reality_finance_v1": {"net": "100.00", "tax": "19.00"},
        },
        "RE-K06",
    )
    invoice_id = next(
        row["id"] for row in receipt["records"] if row["family"] == "document"
    )
    from reality.db.core import DocumentLine

    (line,) = session.scalars(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == invoice_id
        )
    )
    return kit, frame, wheel, promise, line


def test_a_bundle_price_is_split_across_its_components(session, business):
    """K06: the stated net, tax and gross split by the kit's stated shares."""
    _kit, _frame, _wheel, promise, invoice_line = _invoiced_kit(session, business)

    split = _read(session, business, "kit_split", {"document_line_id": invoice_line.id})

    parts = {part["sku"]: part for part in split["split"]}
    assert {
        sku: (part["net"], part["tax"], part["gross"]) for sku, part in parts.items()
    } == {"FRAME": ("60", "11.4", "71.4"), "WHEEL": ("40", "7.6", "47.6")}
    for key, total in (("net", "100"), ("tax", "19"), ("gross", "119")):
        assert sum(Decimal(part[key]) for part in split["split"]) == Decimal(total)
    assert parts["WHEEL"]["gross_per_piece"] == "23.8"
    # The order line splits alike, on its stated gross.
    order_split = _read(
        session, business, "kit_split", {"document_line_id": promise.document_line_id}
    )
    assert {part["sku"]: part["gross"] for part in order_split["split"]} == {
        "FRAME": "71.4",
        "WHEEL": "47.6",
    }


def test_a_single_component_comes_back_from_a_kit(session, business):
    """K03 stays partial: the wheel is back and priced, but not linked to the kit.

    A return names a promise of its own item, and the kit was promised as the
    kit, so the wheel comes back without a promise and stays an Unexplained
    movement until a person explains it; the return and credit classes cannot
    pair it with a credit on the kit's invoice. The credit amount is the
    wheel's per-piece share from the split. The day a component return is
    linked to its kit delivery, this test turns red and K03 can be promoted.
    """
    tenant = business.tenant.id
    _kit, _frame, wheel, promise, invoice_line = _invoiced_kit(session, business)

    returned = core.record_movement(
        session,
        tenant,
        "return",
        wheel.id,
        "1",
        to_location_id=business.location.id,
        reason="Wheel from bike kit SO-K06 sent back",
    )

    assert _on_hand(session, business, wheel) == 1
    split = _read(session, business, "kit_split", {"document_line_id": invoice_line.id})
    (wheel_part,) = [part for part in split["split"] if part["sku"] == "WHEEL"]
    assert wheel_part["gross_per_piece"] == "23.8"
    # The recorded K03 finding.
    assert returned.id in _classes(session, business, "unexplained_movement")
    assert promise.id not in _classes(session, business, "returned_not_credited")
