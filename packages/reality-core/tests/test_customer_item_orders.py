"""Spec 308 FR-002/FR-005: orders by the customer's number, by hand and by file."""

import csv
import json

import pytest
from intake_review_support import accept_import_job as process_import_job
from intake_review_support import (
    reviewed_manual_document_with_lines,
    reviewed_manual_order,
)
from sqlalchemy import select

from reality.db.core import Commitment, Document, DocumentLine
from reality.services import core
from reality.services.artifacts import stage_artifact
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
    return reviewed_manual_order(
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

    _, _document, lines, commitments = _manual_order(
        session, business, "SO-308-1", [({"customer_item_number": "k-4711"}, "2")]
    )

    (line,) = lines
    assert line.item_id == business.item.id
    assert json.loads(line.payload)["customer_item_number"] == "k-4711"
    assert commitments[0].item_id == business.item.id


def test_an_unknown_or_conflicting_number_is_refused_in_entry(session, business):
    lamp = reviewed_create_item(session, business.tenant.id, "LAMP-308", "Lamp 308")
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


def _import(
    session, business, tmp_path, monkeypatch, rows, order_id="EDI-308", skus=None
):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    path = tmp_path / f"{order_id}.csv"
    columns = [
        "order_id",
        "line_id",
        "party_name",
        *(["sku"] if skus else []),
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
                    *([skus[index - 1]] if skus else []),
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

    # The finding carries the quoted number, so assigning can remember it.
    from reality.services.exceptions import _order_line_item_unknown_exceptions

    (finding,) = _order_line_item_unknown_exceptions(session, tenant, None)
    assert finding.trace["customer_item_number"] == "K-9999"

    lamp = reviewed_create_item(session, tenant, "LAMP-308I", "Lamp import")
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


def test_a_file_line_stating_our_item_has_its_number_checked(
    session, business, tmp_path, monkeypatch
):
    lamp = reviewed_create_item(session, business.tenant.id, "LAMP-308F", "Lamp file")
    _map(session, business)

    with pytest.raises(core.InvalidOperation) as refused:
        _import(
            session,
            business,
            tmp_path,
            monkeypatch,
            [("K-4711", "1")],
            order_id="EDI-308C",
            skus=[lamp.sku],
        )
    assert refused.value.code == "customer_item_number_conflicts_with_item"
    session.rollback()
    # Positive control: our item and the customer's number agree.
    _import(
        session,
        business,
        tmp_path,
        monkeypatch,
        [("K-4711", "1")],
        order_id="EDI-308D",
        skus=[business.item.sku],
    )
    assert unknown_item_lines(session, business.tenant.id) == []


def test_a_line_without_item_or_number_is_still_refused(
    session, business, tmp_path, monkeypatch
):
    with pytest.raises(core.InvalidOperation, match="Unknown SKU"):
        _import(
            session,
            business,
            tmp_path,
            monkeypatch,
            [("", "1")],
            order_id="EDI-308E",
            skus=[" "],
        )


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
    invoice = reviewed_manual_document_with_lines(
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
    lamp = reviewed_create_item(session, tenant, "LAMP-308C", "Lamp changed")
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


def test_remembering_shows_a_remap_and_refuses_one_made_since_the_review(
    session, business, tmp_path, monkeypatch
):
    from reality.services.delivery_actions import prepare_delivery_action
    from reality.tools.application import approve_and_execute_proposal

    tenant = business.tenant.id
    lamp = reviewed_create_item(session, tenant, "LAMP-308R", "Lamp remap")
    _import(
        session, business, tmp_path, monkeypatch, [("K-7", "1")], order_id="EDI-308R"
    )
    (row,) = unknown_item_lines(session, tenant)
    arguments = {
        "document_line_id": row["line"].id,
        "item_id": business.item.id,
        "remember_for_customer": True,
    }
    # Positive control: nothing is mapped yet, so nothing is replaced.
    first = prepare_delivery_action(
        session, tenant, "order_line_item_assign", arguments, request_id="r-1"
    )
    review = json.loads(first.input)["_delivery_review"]
    assert review["effect"]["remembers"]["replaces"] is None

    _map(session, business, number="K-7", item=lamp, name="Lampe")

    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(
            session, tenant, first.id, review_token=review["token"], confirmed=True
        )
    assert refused.value.code == "review_delivery_changed"
    session.rollback()
    second = prepare_delivery_action(
        session, tenant, "order_line_item_assign", arguments, request_id="r-2"
    )
    replaces = json.loads(second.input)["_delivery_review"]["effect"]["remembers"][
        "replaces"
    ]
    assert replaces["item_id"] == lamp.id


def test_a_correction_that_does_not_state_the_number_keeps_it(session, business):
    from reality.services.core import (
        correct_manual_document_lines,
        manual_document_line_snapshot,
    )

    tenant = business.tenant.id
    document, (line,) = reviewed_manual_document_with_lines(
        session,
        tenant,
        "sales_invoice",
        "RE-308-7",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": "10",
                "gross_amount": "10",
                "customer_item_number": "K-4711",
            }
        ],
        "10",
    )[:2]
    snapshot = manual_document_line_snapshot(session, tenant, document.id)
    # As the web form sends it: the line's columns, the number unstated.
    unchanged = {
        key: value
        for key, value in snapshot["lines"][0].items()
        if key != "customer_item_number"
    }

    result = correct_manual_document_lines(
        session,
        tenant,
        document.id,
        expected_revision=snapshot["revision"],
        lines=[{**unchanged, "customer_item_number": None}],
    )
    assert result["changed"] is False
    # Positive control: a real correction still keeps the stated number.
    correct_manual_document_lines(
        session,
        tenant,
        document.id,
        expected_revision=snapshot["revision"],
        lines=[{**unchanged, "description": "Corrected"}],
    )
    session.refresh(line)
    assert json.loads(line.payload)["customer_item_number"] == "K-4711"


from intake_review_support import reviewed_create_item
