"""Spec 345: a supplier's own item numbers for our items."""

import json

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from reality.db.core import SourceRecord, SupplierItemNumber
from reality.services import core
from reality.services.supplier_item_numbers import (
    remove_supplier_item_number,
    resolve_supplier_item,
    set_supplier_item_number,
    supplier_item_numbers,
)


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def test_a_number_resolves_for_its_supplier_ignoring_case_and_spaces(session, business):
    tenant = business.tenant.id
    set_supplier_item_number(
        session,
        tenant,
        business.supplier.id,
        business.item.id,
        "LF900-12",
        "Laufrad 28 Zoll, Lindner",
    )

    for quoted in ("LF900-12", "lf900-12", " LF 900-12 "):
        row = resolve_supplier_item(session, tenant, business.supplier.id, quoted)
        assert row is not None and row.item_id == business.item.id, quoted
    # Positive control: an unknown number resolves to nothing.
    assert resolve_supplier_item(session, tenant, business.supplier.id, "K-9") is None


def test_the_same_number_at_another_supplier_is_its_own(session, business):
    tenant = business.tenant.id
    other = reviewed_create_party(session, tenant, "Lindner Teile GmbH", "supplier")
    lamp = reviewed_create_item(session, tenant, "LAMP-345", "Lamp 308")
    set_supplier_item_number(
        session, tenant, business.supplier.id, business.item.id, "A-1", "Rad"
    )
    set_supplier_item_number(session, tenant, other.id, lamp.id, "A-1", "Lampe")

    assert (
        resolve_supplier_item(session, tenant, business.supplier.id, "A-1").item_id
        == business.item.id
    )
    assert resolve_supplier_item(session, tenant, other.id, "A-1").item_id == lamp.id


def test_restating_and_removing_are_versions_of_one_stream(session, business):
    tenant = business.tenant.id
    lamp = reviewed_create_item(session, tenant, "LAMP-345B", "Lamp 308 B")
    first = set_supplier_item_number(
        session, tenant, business.supplier.id, business.item.id, "K-1", "Rad"
    )
    second = set_supplier_item_number(
        session, tenant, business.supplier.id, lamp.id, "k-1", "Lampe"
    )
    assert first.id == second.id
    assert (
        resolve_supplier_item(session, tenant, business.supplier.id, "K-1").item_id
        == lamp.id
    )
    # An item may have several numbers at the same supplier.
    set_supplier_item_number(
        session, tenant, business.supplier.id, lamp.id, "K-2", "Lampe alt"
    )
    assert {
        row["supplier_item_number"]
        for row in supplier_item_numbers(session, tenant, item_id=lamp.id)
    } == {"k-1", "K-2"}

    remove_supplier_item_number(session, tenant, business.supplier.id, "K-1")

    assert resolve_supplier_item(session, tenant, business.supplier.id, "K-1") is None
    versions = [
        json.loads(row.payload)
        for row in session.scalars(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == "internal_supplier_item_number",
                SourceRecord.external_id.like(f"{business.supplier.id}:K-1"),
            )
            .order_by(SourceRecord.version)
        )
    ]
    assert [row.get("item_id") for row in versions] == [
        business.item.id,
        lamp.id,
        None,
    ]
    assert versions[-1]["removed"] is True


def test_statements_are_refused_with_their_code(session, business):
    tenant = business.tenant.id
    for code, call in (
        (
            "supplier_item_number_party_not_supplier",
            lambda: set_supplier_item_number(
                session, tenant, business.customer.id, business.item.id, "X", ""
            ),
        ),
        (
            "supplier_item_number_required",
            lambda: set_supplier_item_number(
                session, tenant, business.supplier.id, business.item.id, "  ", ""
            ),
        ),
        (
            "supplier_item_number_item_not_found",
            lambda: set_supplier_item_number(
                session, tenant, business.supplier.id, "itm_nope", "X", ""
            ),
        ),
        (
            "supplier_item_number_not_found",
            lambda: remove_supplier_item_number(
                session, tenant, business.supplier.id, "NOPE"
            ),
        ),
    ):
        _refused(code, call)
    # Positive control.
    assert set_supplier_item_number(
        session, tenant, business.supplier.id, business.item.id, "OK-1", ""
    )


def test_another_company_cannot_state_or_resolve(session, business):
    tenant = business.tenant.id
    set_supplier_item_number(
        session, tenant, business.supplier.id, business.item.id, "K-1", ""
    )
    other = core.create_tenant(session, "Other GmbH")

    assert resolve_supplier_item(session, other.id, business.supplier.id, "K-1") is None
    with pytest.raises((core.InvalidOperation, core.NotFound)):
        set_supplier_item_number(
            session, other.id, business.supplier.id, business.item.id, "K-2", ""
        )


def test_the_table_refuses_a_blank_number_and_a_second_mapping(session, business):
    tenant = business.tenant.id
    row = set_supplier_item_number(
        session, tenant, business.supplier.id, business.item.id, "K-1", ""
    )
    with pytest.raises(IntegrityError), session.begin_nested():
        session.execute(
            text(
                "UPDATE supplier_item_number SET supplier_item_number = ' ' "
                "WHERE id = :id"
            ),
            {"id": row.id},
        )
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            SupplierItemNumber(
                id="sin_dup",
                tenant_id=tenant,
                party_id=business.supplier.id,
                item_id=business.item.id,
                supplier_item_number="k-1",
                match_key="K-1",
                supplier_item_name="",
                source_record_id=row.source_record_id,
            )
        )
        session.flush()


from intake_review_support import reviewed_create_item, reviewed_create_party
