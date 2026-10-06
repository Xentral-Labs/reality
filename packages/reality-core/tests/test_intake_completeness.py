"""Spec 379: required money, truthful absence, order dates and physical units."""

import csv
import io
import json
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from test_artifact_intake_admission import prepare_file
from test_unified_source_api import client_for

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    ImportJob,
    LedgerEntry,
    SourceRecord,
)
from reality.services import core
from reality.services.company_time_zone import set_company_time_zone
from reality.services.intake import apply_prepared_intake, prepare_intake, review_intake
from reality.services.memberships import Principal


def file_content(rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


def order_row(business, **changes):
    return {
        "order_id": "COMPLETE-ORDER",
        "party_name": business.customer.name,
        "location": business.location.name,
        "sku": business.item.sku,
        "quantity": "2",
        "currency": "EUR",
        **changes,
    }


def manual_arguments(business, **line_changes):
    return {
        "direction": "sales",
        "number": "MANUAL-COMPLETENESS",
        "company_party_id": business.company.id,
        "counterparty_id": business.customer.id,
        "location_id": business.location.id,
        "gross_amount": "20",
        "lines": [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "gross_amount": "20",
                **line_changes,
            }
        ],
    }


def accept(session, business, owner, proposal):
    review = review_intake(session, business.tenant.id, proposal.id)
    return apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        review["digest"],
        confirmed=True,
        principal=Principal(owner.id),
    )


@pytest.mark.parametrize("value", [None, "", "  "])
def test_shop_money_without_currency_refuses_and_retains_raw(session, business, value):
    payload = {
        "id": 379,
        "name": "#379",
        "currency": value,
        "total_price": "20",
        "line_items": [
            {"id": 1, "sku": business.item.sku, "quantity": 2, "price": "10"}
        ],
    }
    source, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    with pytest.raises(core.InvalidOperation) as refused:
        prepare_intake(session, business.tenant.id, job.id)
    assert refused.value.code == "source_field_required"
    assert "currency" in str(refused.value)
    assert json.loads(source.payload) == payload
    assert job.status == "failed"
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert session.scalar(select(func.count()).select_from(Commitment)) == 0


def test_shop_omitted_currency_is_not_eur(session, business):
    payload = {
        "id": 380,
        "total_price": "20",
        "line_items": [{"sku": business.item.sku, "quantity": 2, "price": "10"}],
    }
    _, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    with pytest.raises(core.InvalidOperation) as refused:
        prepare_intake(session, business.tenant.id, job.id)
    assert refused.value.code == "source_field_required"


@pytest.mark.parametrize("field", ["currency", "effective_at", "direction"])
@pytest.mark.parametrize("value", [None, "", "  "])
def test_bank_missing_essential_retains_source_without_booking(
    session, business, tmp_path, monkeypatch, field, value
):
    row = {
        "party_name": business.customer.name,
        "amount": "12.30",
        "currency": "EUR",
        "effective_at": "2026-10-05T23:30:00Z",
        "direction": "incoming",
    }
    row[field] = value
    with pytest.raises(core.InvalidOperation) as refused:
        prepare_file(
            session,
            business,
            "bank_statement",
            file_content([row]),
            tmp_path,
            monkeypatch,
        )
    assert refused.value.code == "source_field_required"
    assert field in str(refused.value)
    source = session.scalar(
        select(SourceRecord).where(SourceRecord.source_system == "file_provider")
    )
    assert source is not None and source.source_artifact_id
    job = session.scalar(
        select(ImportJob).where(ImportJob.source_record_id == source.id)
    )
    assert job.status == "failed"
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    assert session.scalar(select(func.count()).select_from(Document)) == 0


@pytest.mark.parametrize("direction", ["incoming", "outgoing"])
def test_complete_bank_statement_preserves_stated_money_and_time(
    session, business, scheduled_owner, tmp_path, monkeypatch, direction
):
    row = {
        "party_name": business.supplier.name
        if direction == "outgoing"
        else business.customer.name,
        "amount": "12.30",
        "currency": "EUR",
        "effective_at": "2026-10-05T23:30:00Z",
        "direction": direction,
    }
    _, proposal = prepare_file(
        session, business, "bank_statement", file_content([row]), tmp_path, monkeypatch
    )
    review = review_intake(session, business.tenant.id, proposal.id)
    args = review["plan"]["effects"][0]["arguments"]
    assert args["effective_at"] == "2026-10-05T23:30:00+00:00"
    assert Decimal(args["amount"]) == Decimal("12.30")
    accept(session, business, scheduled_owner, proposal)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2


@pytest.mark.parametrize("price", ["omitted", "", "  ", "0"])
def test_manual_absent_price_stays_unknown_and_zero_stays_zero(
    session, business, price
):
    args = manual_arguments(
        business, **({} if price == "omitted" else {"unit_price": price})
    )
    preview = core._preview_manual_order(session, business.tenant.id, args)
    expected = Decimal(0) if price == "0" else None
    assert preview["lines"][0]["unit_price"] == expected
    _, _, lines, _ = core.create_manual_order(session, business.tenant.id, **args)
    assert lines[0].unit_price == expected
    assert lines[0].gross_amount == Decimal(20)


def test_manual_order_review_explains_allowed_timing_and_price_gaps(session, business):
    preview = core._preview_manual_order(
        session, business.tenant.id, manual_arguments(business)
    )
    issues = " ".join(preview["issues"])
    for field in ["document date", "order time", "delivery date", "unit price"]:
        assert field in issues.lower()


def test_file_order_review_explains_all_allowed_gaps(
    session, business, tmp_path, monkeypatch
):
    _, proposal = prepare_file(
        session,
        business,
        "sales_order",
        file_content([order_row(business)]),
        tmp_path,
        monkeypatch,
    )
    issues = " ".join(
        review_intake(session, business.tenant.id, proposal.id)["plan"]["issues"]
    ).lower()
    for field in [
        "document date",
        "order time",
        "delivery date",
        "unit price",
        "line amount",
        "order total",
    ]:
        assert field in issues


@pytest.mark.parametrize(
    "changes,expected",
    [
        (
            {"document_date": "2026-10-04", "ordered_at": "2026-10-05T23:30:00Z"},
            date(2026, 10, 4),
        ),
        ({"ordered_at": "2026-10-05T23:30:00Z"}, date(2026, 10, 6)),
    ],
)
def test_file_order_date_is_stated_or_company_local_and_reaches_http(
    session, business, scheduled_owner, tmp_path, monkeypatch, changes, expected
):
    set_company_time_zone(session, business.tenant.id, "Europe/Berlin")
    _, proposal = prepare_file(
        session,
        business,
        "sales_order",
        file_content([order_row(business, **changes)]),
        tmp_path,
        monkeypatch,
    )
    accept(session, business, scheduled_owner, proposal)
    order = session.scalar(select(Document).where(Document.type == "sales_order"))
    assert order.document_date == expected
    with client_for(session) as client:
        result = client.get(
            f"/api/tenants/{business.tenant.id}/evidence-documents?document_type=sales_order"
        )
    assert result.status_code == 200
    assert result.json()["items"][0]["date"] == expected.isoformat()


@pytest.mark.parametrize(
    "field,values",
    [
        ("ordered_at", ["2026-10-05T10:00:00Z", "2026-10-06T10:00:00Z"]),
        ("document_date", ["2026-10-05", "2026-10-06"]),
    ],
)
def test_coherent_file_order_refuses_conflicting_header_dates(
    session, business, tmp_path, monkeypatch, field, values
):
    rows = [order_row(business, **{field: value}) for value in values]
    with pytest.raises(core.InvalidOperation) as refused:
        prepare_file(
            session, business, "sales_order", file_content(rows), tmp_path, monkeypatch
        )
    assert refused.value.code == "source_order_header_conflict"
    assert session.scalar(select(func.count()).select_from(Document)) == 0


@pytest.mark.parametrize("path", ["manual", "file"])
def test_unsupported_sales_quantity_unit_refuses_before_promises(
    session, business, tmp_path, monkeypatch, path
):
    with pytest.raises(core.InvalidOperation) as refused:
        if path == "manual":
            core.create_manual_order(
                session, business.tenant.id, **manual_arguments(business, unit="box")
            )
        else:
            prepare_file(
                session,
                business,
                "sales_order",
                file_content([order_row(business, unit="box")]),
                tmp_path,
                monkeypatch,
            )
    assert refused.value.code == "source_quantity_unit_unsupported"
    assert session.scalar(select(func.count()).select_from(Commitment)) == 0
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_known_item_file_order_inherits_recorded_unit_without_inventing_a_price(
    session, business, scheduled_owner, tmp_path, monkeypatch
):
    _, proposal = prepare_file(
        session,
        business,
        "sales_order",
        file_content([order_row(business)]),
        tmp_path,
        monkeypatch,
    )
    accept(session, business, scheduled_owner, proposal)
    line = session.scalar(select(DocumentLine))
    assert line.unit == business.item.unit
    assert line.unit_price is None and line.gross_amount is None


@pytest.mark.parametrize(
    "profile", ["customer_payment.v1", "supplier_payment.v1", "sales_invoice.v1"]
)
@pytest.mark.parametrize("currency", [None, "", "   "])
def test_normalized_financial_source_requires_stated_currency(
    session, business, profile, currency
):
    payload = {
        "party_id": business.customer.id,
        "currency": currency,
        "amount": "5",
        "effective_at": "2026-10-06T10:00:00Z",
        "external_payment_id": "completeness",
    }
    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "financial_provider",
        "statement",
        profile,
        payload,
        context={"profile": profile},
    )
    with pytest.raises(core.InvalidOperation) as refused:
        prepare_intake(session, business.tenant.id, job.id)
    assert refused.value.code == "source_field_required"
    assert job.status == "failed"
    assert json.loads(source.payload) == payload
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0


def test_completeness_policy_distinguishes_absence_from_zero():
    from reality.domain.intake_completeness import (
        MissingEssentialValue,
        is_unstated,
        order_issues,
        required_text,
    )

    assert all(is_unstated(value) for value in [None, "", " "])
    assert not any(is_unstated(value) for value in [0, Decimal(0), "0"])
    assert required_text(" EUR ", "currency") == "EUR"
    with pytest.raises(MissingEssentialValue) as missing:
        required_text(None, "currency")
    assert missing.value.field == "currency"
    document = {
        "document_date": "2026-10-06",
        "ordered_at": "2026-10-06T10:00:00Z",
        "requested_delivery_at": "2026-10-08T10:00:00Z",
        "gross_amount": "0",
    }
    assert order_issues(document, [{"unit_price": 0, "gross_amount": 0}]) == ()
