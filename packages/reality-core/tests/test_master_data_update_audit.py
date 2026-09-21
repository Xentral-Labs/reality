import json

from conftest import record_by_id
from sqlalchemy import select

from reality.db.core import BusinessEvent, Item, Party, SourceRecord
from reality.services.core import (
    InvalidOperation,
    set_master_data_active,
    update_item,
    update_party,
)


def _latest_event(session, tenant_id, subject_id):
    return session.scalar(
        select(BusinessEvent)
        .where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.subject_id == subject_id,
        )
        .order_by(BusinessEvent.sequence.desc())
    )


def test_party_update_event_records_every_effective_normalized_change(
    session, business
):
    party = business.customer
    original_id = party.id
    original_name = party.name

    update_party(
        session,
        business.tenant.id,
        party.id,
        "  Renamed Customer  ",
        "customer",
        roles=["customer", "supplier", "customer"],
        accounting_code="AR-200",
        default_currency="usd",
        credit_limit="1500.0000",
        tax_identifier="VAT-2",
    )

    payload = json.loads(_latest_event(session, business.tenant.id, party.id).payload)
    assert party.id == original_id
    assert payload["changes"] == {
        "accounting_code": {"before": "", "after": "AR-200"},
        "credit_limit": {"before": "0", "after": "1500"},
        "default_currency": {"before": "EUR", "after": "USD"},
        "name": {"before": original_name, "after": "Renamed Customer"},
        "roles": {"before": ["customer"], "after": ["customer", "supplier"]},
        "tax_identifier": {"before": "", "after": "VAT-2"},
    }


def test_item_noop_emits_no_update_event(session, business):
    item = business.item
    before = session.scalar(
        select(BusinessEvent.sequence)
        .where(BusinessEvent.tenant_id == business.tenant.id)
        .order_by(BusinessEvent.sequence.desc())
    )

    update_item(
        session,
        business.tenant.id,
        item.id,
        f" {item.sku} ",
        f" {item.name} ",
        f" {item.unit} ",
    )

    after = session.scalar(
        select(BusinessEvent.sequence)
        .where(BusinessEvent.tenant_id == business.tenant.id)
        .order_by(BusinessEvent.sequence.desc())
    )
    assert after == before


def test_lifecycle_event_records_before_and_after_and_noop_is_silent(session, business):
    set_master_data_active(session, business.tenant.id, Item, business.item.id, False)
    event = _latest_event(session, business.tenant.id, business.item.id)
    assert json.loads(event.payload)["changes"] == {
        "is_active": {"before": True, "after": False}
    }
    sequence = event.sequence

    set_master_data_active(session, business.tenant.id, Item, business.item.id, False)
    assert (
        _latest_event(session, business.tenant.id, business.item.id).sequence
        == sequence
    )


def test_failed_update_does_not_persist_state_or_success_event(session, business):
    item = business.item
    original_name = item.name
    try:
        update_item(
            session,
            business.tenant.id,
            item.id,
            item.sku,
            "Changed before failure",
            item.unit,
            lead_time_days=-1,
        )
    except InvalidOperation:
        session.rollback()

    assert record_by_id(session, Party, business.customer.id) is not None
    assert record_by_id(session, Item, item.id).name == original_name
    assert (
        _latest_event(session, business.tenant.id, item.id).event_type == "item.created"
    )


def test_sourced_update_versions_changed_payload_and_audits_source_link(
    session, business
):
    item = business.item
    update_item(
        session,
        business.tenant.id,
        item.id,
        item.sku,
        item.name,
        item.unit,
        source_system="pim",
        external_id="PIM-1",
        source_payload={"version": 1},
    )
    first_source_id = item.source_record_id
    update_item(
        session,
        business.tenant.id,
        item.id,
        item.sku,
        item.name,
        item.unit,
        source_system="pim",
        external_id="PIM-1",
        source_payload={"version": 2},
    )

    source = record_by_id(session, SourceRecord, item.source_record_id)
    event = _latest_event(session, business.tenant.id, item.id)
    assert source.supersedes_source_record_id == first_source_id
    assert event.source_record_id == source.id
    assert json.loads(event.payload)["changes"]["source_record_id"] == {
        "before": first_source_id,
        "after": source.id,
    }
