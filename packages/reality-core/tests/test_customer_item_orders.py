"""Spec 308 FR-002/FR-005: orders by the customer's number, by hand and by file."""

import csv
import json

import pytest
from sqlalchemy import select

from reality.db.core import Commitment, Document, DocumentLine
from reality.services import core
from reality.services.artifacts import stage_artifact
from reality.services.core import process_import_job
from reality.services.customer_item_numbers import (
    resolve_customer_item,
    set_customer_item_number,
)
from reality.services.delivery_reads import delivery_case
from reality.services.file_interpreters import suggested_mapping
from reality.services.order_line_items import assign_line_item, unknown_item_lines
from reality.tools.application import confirm_tool, propose_tool


def _map(session, business, number="K-4711", name="Laufrad 28 Zoll", item=None):
    return set_customer_item_number(
        session,
        business.tenant.id,
        business.customer.id,
        (item or business.item).id,
        number,
        name,
    )


def _manual_order(session, business, number, lines):
    return core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "quantity": quantity,
                "unit_price": "10",
                "gross_amount": str(int(quantity) * 10),
                **line,
            }
            for line, quantity in lines
        ],
        str(sum(int(quantity) * 10 for _, quantity in lines)),
    )


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def test_a_manual_line_resolves_by_the_customers_number(session, business):
    _map(session, business)

    _, document, lines, commitments = _manual_order(
        session, business, "SO-308-1", [({"customer_item_number": "k-4711"}, "2")]
    )

    (line,) = lines
    assert line.item_id == business.item.id
    assert json.loads(line.payload)["customer_item_number"] == "k-4711"
    assert commitments[0].item_id == business.item.id


def test_an_unknown_or_conflicting_number_is_refused_in_entry(session, business):
    lamp = core.create_item(session, business.tenant.id, "LAMP-308", "Lamp 308")
    _map(session, business)

    _refused(
        "customer_item_number_unknown",
        lambda: _manual_order(
            session, business, "SO-308-2", [({"customer_item_number": "K-9"}, "1")]
        ),
    )
    _refused(
        "customer_item_number_conflicts_with_item",
        lambda: _manual_order(
            session,
            business,
            "SO-308-3",
            [({"customer_item_number": "K-4711", "item_id": lamp.id}, "1")],
        ),
    )
    # Positive control: our item and the matching number agree.
    _manual_order(
        session,
        business,
        "SO-308-4",
        [({"customer_item_number": "K-4711", "item_id": business.item.id}, "1")],
    )


def _import(session, business, tmp_path, monkeypatch, rows, order_id="EDI-308"):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    path = tmp_path / "orders.csv"
    columns = [
        "order_id",
        "line_id",
        "party_name",
        "customer_item_number",
        "name",
        "quantity",
        "unit_price",
        "currency",
        "location",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for index, (number, quantity) in enumerate(rows, start=1):
            writer.writerow(
                [
                    order_id,
                    str(index),
                    business.customer.name,
                    number,
                    f"Kundenposition {number}",
                    quantity,
                    "10",
                    "EUR",
                    business.location.name,
                ]
            )
    with path.open("rb") as handle:
        artifact, _ = stage_artifact(
            session,
            business.tenant.id,
            handle,
            filename="orders.csv",
            content_type="text/csv",
        )
    proposal = propose_tool(
        session,
        business.tenant.id,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "edi_customer",
            "source_type": "order",
            "expected_target": "sales_order",
            "column_mapping": suggested_mapping(columns, "sales_order"),
        },
    )
    output = json.loads(confirm_tool(session, business.tenant.id, proposal.id).output)
    return process_import_job(session, business.tenant.id, output["import_job_id"])


def test_an_imported_order_resolves_known_numbers_and_keeps_unknown_lines(
    session, business, tmp_path, monkeypatch
):
    tenant = business.tenant.id
    _map(session, business)

    _import(
        session, business, tmp_path, monkeypatch, [("K-4711", "2"), ("K-9999", "1")]
    )

    document = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant, Document.number == "EDI-308"
        )
    )
    lines = {
        json.loads(line.payload)["customer_item_number"]: line
        for line in session.scalars(
            select(DocumentLine).where(DocumentLine.document_id == document.id)
        )
    }
    assert lines["K-4711"].item_id == business.item.id
    assert lines["K-9999"].item_id is None
    promised = set(
        session.scalars(
            select(Commitment.document_line_id).where(
                Commitment.document_id == document.id
            )
        )
    )
    assert promised == {lines["K-4711"].id}
    # The unknown line is reported until a person assigns it.
    assert [row["line"].id for row in unknown_item_lines(session, tenant)] == [
        lines["K-9999"].id
    ]

    lamp = core.create_item(session, tenant, "LAMP-308I", "Lamp import")
    assign_line_item(
        session,
        tenant,
        document_line_id=lines["K-9999"].id,
        item_id=lamp.id,
        remember_for_customer=True,
    )

    assert (
        resolve_customer_item(session, tenant, business.customer.id, "K-9999").item_id
        == lamp.id
    )
    assert unknown_item_lines(session, tenant) == []


def test_remembering_needs_a_number_on_the_line(
    session, business, tmp_path, monkeypatch
):
    from reality.services.order_line_items import review_item_assignment

    tenant = business.tenant.id
    _import(
        session, business, tmp_path, monkeypatch, [("K-1", "1")], order_id="EDI-308B"
    )
    (row,) = unknown_item_lines(session, tenant)
    review = review_item_assignment(
        session,
        tenant,
        {
            "document_line_id": row["line"].id,
            "item_id": business.item.id,
            "remember_for_customer": True,
        },
    )
    assert review["state"]["customer_item_number"] == "K-1"


def _line_labels(sections):
    return [
        row["label"]
        for section in sections
        if section["title"] == "Lines"
        for row in section["rows"]
    ]


def test_the_stated_number_shows_on_order_delivery_and_invoice(session, business):
    from reality.services.operational_previews import operational_preview

    tenant = business.tenant.id
    _map(session, business)
    _, document, (line,), (commitment,) = _manual_order(
        session, business, "SO-308-5", [({"customer_item_number": "K-4711"}, "2")]
    )

    case = delivery_case(session, tenant, commitment.id)
    assert case["customer_item"] == {
        "customer_item_number": "K-4711",
        "customer_item_name": "Laufrad 28 Zoll",
    }
    labels = _line_labels(operational_preview(session, tenant, "document", document.id))
    assert any("K-4711 Laufrad 28 Zoll" in label for label in labels)
    # An invoice line reaches the number through the order line it bills.
    invoice = core.create_manual_document_with_lines(
        session,
        tenant,
        "sales_invoice",
        "RE-308-1",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
                "billed_document_line_id": line.id,
            }
        ],
        "20",
    )[0]
    invoice_labels = _line_labels(
        operational_preview(session, tenant, "document", invoice.id)
    )
    assert any("K-4711" in label for label in invoice_labels)


def test_a_changed_mapping_leaves_past_lines_as_stated(session, business):
    tenant = business.tenant.id
    lamp = core.create_item(session, tenant, "LAMP-308C", "Lamp changed")
    _map(session, business)
    _, _, (line,), _ = _manual_order(
        session, business, "SO-308-6", [({"customer_item_number": "K-4711"}, "1")]
    )

    _map(session, business, item=lamp, name="Lampe neu")

    session.refresh(line)
    assert (line.item_id, json.loads(line.payload)["customer_item_number"]) == (
        business.item.id,
        "K-4711",
    )
