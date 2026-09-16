import pytest

from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_item,
    create_location,
    create_party,
    create_tenant,
    update_item,
)
from reality.services.reference_workspace import (
    prepare_reference,
    reference_detail,
    reference_proposal,
    reference_register,
)
from reality.tools.application import approve_and_execute_proposal


@pytest.mark.parametrize(
    "family,record",
    [
        ("customer", {"name": "New customer"}),
        ("supplier", {"name": "New supplier"}),
        ("item", {"name": "New item", "sku": "NEW", "unit": "pcs"}),
        ("location", {"name": "New location"}),
    ],
)
def test_reference_create_replay_and_confirmation_are_one_effect(
    session, business, family, record
):
    tid = business.tenant.id
    proposal = prepare_reference(
        session, tid, family, "create", record, request_id="new-reference"
    )
    assert (
        prepare_reference(
            session, tid, family, "create", record, request_id="new-reference"
        ).id
        == proposal.id
    )
    with pytest.raises(InvalidOperation):
        prepare_reference(
            session,
            tid,
            family,
            "create",
            {**record, "name": "Different"},
            request_id="new-reference",
        )
    result = approve_and_execute_proposal(session, tid, proposal.id)
    assert (
        approve_and_execute_proposal(session, tid, proposal.id).output == result.output
    )
    detail = reference_proposal(session, tid, proposal.id)
    assert detail["status"] == "executed"
    assert len(detail["links"]) == 1


def test_edit_preserves_advanced_fields_and_refuses_stale_snapshot(session, business):
    tid = business.tenant.id
    location = create_location(session, tid, "Default bin")
    item = create_item(
        session,
        tid,
        "SPECIAL",
        "Tracked lamp",
        default_location_id=location.id,
        tracking_type="lot",
        source_system="external",
        external_id="item-special",
        source_payload={"untouched": {"value": 7}},
    )
    original = reference_detail(session, tid, "item", item.id)
    body = {
        "id": item.id,
        "expected_revision": original["expected_revision"],
        "name": "Renamed lamp",
        "sku": "SPECIAL",
    }
    proposal = prepare_reference(
        session, tid, "item", "update", body, request_id="rename"
    )
    approve_and_execute_proposal(session, tid, proposal.id)
    session.refresh(item)
    assert item.name == "Renamed lamp"
    assert item.tracking_type == "lot" and item.default_location_id == location.id
    assert item.source_record_id == original["source_record_id"]
    with pytest.raises(InvalidOperation):
        prepare_reference(session, tid, "item", "update", body, request_id="stale")
    fresh = reference_detail(session, tid, "item", item.id)
    second = prepare_reference(
        session,
        tid,
        "item",
        "update",
        {**body, "expected_revision": fresh["expected_revision"], "name": "Second"},
        request_id="second",
    )
    update_item(session, tid, item.id, item.sku, "Concurrent", item.unit)
    with pytest.raises(InvalidOperation):
        approve_and_execute_proposal(session, tid, second.id)
    assert second.status == "proposed"


def test_register_roles_paging_and_foreign_reference(session, business):
    tid = business.tenant.id
    party = create_party(
        session, tid, "Shared name", "customer", roles=["customer", "supplier"]
    )
    for family in ["customer", "supplier"]:
        rows = reference_register(session, tid, family, query="Shared", size=1)
        assert rows["page"]["total"] == 1 and rows["items"][0]["id"] == party.id
    other = create_tenant(session, "Foreign references")
    with pytest.raises(NotFound):
        reference_detail(session, other.id, "customer", party.id)


@pytest.mark.parametrize("family", ["customer", "supplier", "location"])
def test_basic_rename_preserves_roles_commercial_values_and_hierarchy(
    session, business, family
):
    tid = business.tenant.id
    if family == "location":
        parent = create_location(session, tid, "Parent warehouse")
        target = create_location(
            session, tid, "Child", location_type="bin", parent_location_id=parent.id
        )
    else:
        target = create_party(
            session,
            tid,
            "Partner",
            family,
            roles=["customer", "supplier"],
            accounting_code="AC-9",
            default_currency="USD",
            credit_limit="150",
            tax_identifier="EXTERNAL",
        )
    before = reference_detail(session, tid, family, target.id)
    proposal = prepare_reference(
        session,
        tid,
        family,
        "update",
        {
            "id": target.id,
            "expected_revision": before["expected_revision"],
            "name": "New label",
        },
        request_id="preservation",
    )
    approve_and_execute_proposal(session, tid, proposal.id)
    after = reference_detail(session, tid, family, target.id)
    assert after["name"] == "New label"
    assert {
        key: value
        for key, value in before.items()
        if key not in {"name", "expected_revision"}
    } == {
        key: value
        for key, value in after.items()
        if key not in {"name", "expected_revision"}
    }


def test_register_filters_before_count_and_pagination(session, business):
    from reality.services.core import set_master_data_active

    tid = business.tenant.id
    rows = [
        create_item(session, tid, f"SEARCH-{index}", f"Search {index}")
        for index in range(3)
    ]
    from reality.db.core import Item

    set_master_data_active(session, tid, Item, rows[0].id, False)
    assert (
        reference_register(session, tid, "item", query="Search", size=1)["page"][
            "total"
        ]
        == 2
    )
    all_rows = reference_register(
        session, tid, "item", query="Search", size=1, page=3, include_inactive=True
    )
    assert all_rows["page"]["total"] == 3 and all_rows["page"]["number"] == 3


def test_two_connections_serialize_stale_reference_updates(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, build_engine

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as connection:
            tid = create_tenant(connection, "Concurrent references").id
            item = create_item(connection, tid, "ORIGINAL", "Original")
            snapshot = reference_detail(connection, tid, "item", item.id)
            proposals = [
                prepare_reference(
                    connection,
                    tid,
                    "item",
                    "update",
                    {
                        "id": item.id,
                        "name": name,
                        "sku": "ORIGINAL",
                        "expected_revision": snapshot["expected_revision"],
                    },
                    request_id=name,
                ).id
                for name in ["First", "Second"]
            ]
        barrier = Barrier(2)

        def confirm(identity):
            with factory() as connection:
                barrier.wait(timeout=5)
                try:
                    return approve_and_execute_proposal(
                        connection, tid, identity
                    ).status
                except InvalidOperation:
                    return "stale"

        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(confirm, proposals)) == ["executed", "stale"]
        with factory() as connection:
            assert sorted(
                reference_proposal(connection, tid, identity)["status"]
                for identity in proposals
            ) == ["executed", "proposed"]
    finally:
        engine.dispose()


def test_practice_business_reads_do_not_grant_mutation_authority(session):
    from reality.db.core import Tenant, uid
    from reality.services.company_insights import company_insights

    tenant = Tenant(id=uid("ten"), name="Isolated practice", purpose="playground")
    session.add(tenant)
    session.commit()
    assert reference_register(session, tenant.id, "item")["items"] == []
    from reality.services.reference_workspace import require_ordinary_workspace

    with pytest.raises(InvalidOperation):
        require_ordinary_workspace(session, tenant.id)
    assert company_insights(session, tenant.id)["position"]["open"] == 0


def _confirm(session, tid, family, operation, record, request_id):
    proposal = prepare_reference(
        session, tid, family, operation, record, request_id=request_id
    )
    approve_and_execute_proposal(session, tid, proposal.id)
    return proposal


def test_full_party_edit_changes_commercial_defaults_roles_and_provenance(
    session, business
):
    from reality.services.core import create_payment_term

    tid = business.tenant.id
    create_payment_term(session, tid, "NET30", "Net 30", 30)
    party = create_party(
        session, tid, "Maple", "customer", source_system="shop", external_id="c-1"
    )
    before = reference_detail(session, tid, "customer", party.id)
    assert (
        before["payment_term_code"],
        before["source_system"],
        before["external_id"],
    ) == (
        "",
        "shop",
        "c-1",
    )
    _confirm(
        session,
        tid,
        "customer",
        "update",
        {
            "id": party.id,
            "expected_revision": before["expected_revision"],
            "name": "Maple Retail",
            "type": "customer",
            "roles": ["supplier", "customer"],
            "accounting_code": "D-100",
            "payment_term_code": "NET30",
            "default_currency": "usd",
            "credit_limit": "2500.50",
            "tax_identifier": "DE123",
            "source_system": "shop",
            "external_id": "c-1",
        },
        "full-party",
    )
    after = reference_detail(session, tid, "customer", party.id)
    assert after["name"] == "Maple Retail"
    assert after["roles"] == ["customer", "supplier"]
    assert after["accounting_code"] == "D-100"
    assert after["payment_term_code"] == "NET30"
    assert after["default_currency"] == "USD"
    assert after["credit_limit"] == "2500.5"
    assert after["tax_identifier"] == "DE123"
    # Unchanged external identity keeps the same source evidence.
    assert after["source_record_id"] == before["source_record_id"]
    # Omitted fields keep their current value; a changed external identity
    # creates a new source version and provenance follows it.
    _confirm(
        session,
        tid,
        "customer",
        "update",
        {
            "id": party.id,
            "expected_revision": after["expected_revision"],
            "external_id": "c-2",
        },
        "identity",
    )
    final = reference_detail(session, tid, "customer", party.id)
    assert final["source_record_id"] != after["source_record_id"]
    assert (final["source_system"], final["external_id"]) == ("shop", "c-2")
    assert final["credit_limit"] == "2500.5"
    assert final["roles"] == ["customer", "supplier"]
    assert final["payment_term_code"] == "NET30"


def test_register_role_guard_and_invalid_values_leave_no_proposal(session, business):
    from sqlalchemy import func, select

    from reality.db.core import ChangeProposal

    tid = business.tenant.id
    party = business.customer
    detail = reference_detail(session, tid, "customer", party.id)
    base = {"id": party.id, "expected_revision": detail["expected_revision"]}
    invalid_cases = [
        {"roles": ["supplier"]},
        {"roles": ["owner"]},
        {"roles": []},
        {"roles": "customer"},
        {"type": "person"},
        {"credit_limit": "-1"},
        {"credit_limit": "abc"},
        {"credit_limit": True},
        {"default_currency": "EURO"},
        {"unknown": "x"},
        {"source_payload": {"a": 1}},
        {"name": ""},
        {"name": 5},
        {"name": "x" * 501},
    ]
    for index, invalid in enumerate(invalid_cases):
        with pytest.raises(InvalidOperation):
            prepare_reference(
                session,
                tid,
                "customer",
                "update",
                {**base, **invalid},
                request_id=f"invalid-{index}",
            )
    with pytest.raises(InvalidOperation):
        prepare_reference(
            session,
            tid,
            "supplier",
            "create",
            {"name": "Wrong register", "roles": ["customer"]},
            request_id="wrong-register",
        )
    assert (
        session.scalar(
            select(func.count())
            .select_from(ChangeProposal)
            .where(ChangeProposal.tenant_id == tid)
        )
        == 0
    )


def test_full_item_edit_changes_inventory_behaviour(session, business):
    from decimal import Decimal

    tid = business.tenant.id
    bin_location = create_location(session, tid, "Bin A")
    item = business.item
    detail = reference_detail(session, tid, "item", item.id)
    _confirm(
        session,
        tid,
        "item",
        "update",
        {
            "id": item.id,
            "expected_revision": detail["expected_revision"],
            "sku": "BIKE-LIGHT-2",
            "name": "Bike light",
            "unit": "box",
            "item_type": "stocked",
            "tracking_type": "lot",
            "default_location_id": bin_location.id,
            "purchase_unit": "pallet",
            "conversion_factor": "24",
            "lead_time_days": "7",
        },
        "full-item",
    )
    session.refresh(item)
    assert (
        item.sku,
        item.unit,
        item.tracking_type,
        item.default_location_id,
        item.purchase_unit,
        item.lead_time_days,
    ) == ("BIKE-LIGHT-2", "box", "lot", bin_location.id, "pallet", 7)
    assert item.conversion_factor == Decimal(24)
    fresh = reference_detail(session, tid, "item", item.id)
    assert fresh["lead_time_days"] == 7 and fresh["conversion_factor"] == "24"
    invalid_cases = [
        {"item_type": "bundle"},
        {"tracking_type": "batch"},
        {"conversion_factor": "0"},
        {"lead_time_days": -1},
        {"lead_time_days": "soon"},
        {"default_location_id": ""},
        {"unit": ""},
    ]
    for index, invalid in enumerate(invalid_cases):
        with pytest.raises(InvalidOperation):
            prepare_reference(
                session,
                tid,
                "item",
                "update",
                {
                    "id": item.id,
                    "expected_revision": fresh["expected_revision"],
                    **invalid,
                },
                request_id=f"bad-item-{index}",
            )


def test_full_location_edit_changes_type_parent_and_stock(session, business):
    tid = business.tenant.id
    parent = create_location(session, tid, "Main hall")
    location = business.location
    detail = reference_detail(session, tid, "location", location.id)
    _confirm(
        session,
        tid,
        "location",
        "update",
        {
            "id": location.id,
            "expected_revision": detail["expected_revision"],
            "type": "zone",
            "parent_location_id": parent.id,
            "allows_stock": False,
        },
        "full-location",
    )
    session.refresh(location)
    assert (location.type, location.parent_location_id, location.allows_stock) == (
        "zone",
        parent.id,
        False,
    )
    assert location.name == "Augsburg Warehouse"
    fresh = reference_detail(session, tid, "location", location.id)
    invalid_cases = [
        {"parent_location_id": location.id},
        {"allows_stock": "yes"},
        {"type": ""},
    ]
    for index, invalid in enumerate(invalid_cases):
        with pytest.raises(InvalidOperation):
            prepare_reference(
                session,
                tid,
                "location",
                "update",
                {
                    "id": location.id,
                    "expected_revision": fresh["expected_revision"],
                    **invalid,
                },
                request_id=f"bad-location-{index}",
            )


def test_full_field_creation_records_every_value(session, business):
    from reality.services.core import create_payment_term

    tid = business.tenant.id
    create_payment_term(session, tid, "NET14", "Net 14", 14)
    parent = business.location

    def created(family, record, request_id):
        proposal = _confirm(session, tid, family, "create", record, request_id)
        link = reference_proposal(session, tid, proposal.id)["links"][0]
        return reference_detail(session, tid, family, link["id"])

    supplier = created(
        "supplier",
        {
            "name": "Bike Parts",
            "type": "supplier",
            "roles": ["supplier", "company"],
            "accounting_code": "K-7",
            "payment_term_code": "NET14",
            "default_currency": "chf",
            "credit_limit": "100",
            "tax_identifier": "CHE-1",
            "source_system": "erp",
            "external_id": "s-9",
        },
        "create-supplier",
    )
    assert supplier["roles"] == ["company", "supplier"]
    assert supplier["payment_term_code"] == "NET14"
    assert supplier["default_currency"] == "CHF" and supplier["credit_limit"] == "100"
    assert supplier["tax_identifier"] == "CHE-1"
    assert (supplier["source_system"], supplier["external_id"]) == ("erp", "s-9")
    item = created(
        "item",
        {
            "sku": "PUMP",
            "name": "Floor pump",
            "unit": "pcs",
            "item_type": "service",
            "tracking_type": "serial",
            "default_location_id": parent.id,
            "purchase_unit": "box",
            "conversion_factor": "6",
            "lead_time_days": 3,
        },
        "create-item",
    )
    assert (item["item_type"], item["tracking_type"], item["default_location_id"]) == (
        "service",
        "serial",
        parent.id,
    )
    assert (
        item["purchase_unit"],
        item["conversion_factor"],
        item["lead_time_days"],
    ) == (
        "box",
        "6",
        3,
    )
    location = created(
        "location",
        {
            "name": "Returns bin",
            "type": "bin",
            "parent_location_id": parent.id,
            "allows_stock": False,
        },
        "create-location",
    )
    assert (
        location["type"],
        location["parent_location_id"],
        location["allows_stock"],
    ) == (
        "bin",
        parent.id,
        False,
    )


def test_business_preview_names_fields_and_preserves_revision(session, business):
    from reality.services.core import (
        _snapshot_revision,
        create_payment_term,
        master_data_update_snapshot,
    )

    tid = business.tenant.id
    create_payment_term(session, tid, "NET209", "Thirty days", due_days=30)
    party = create_party(
        session,
        tid,
        "Preview customer",
        "customer",
        accounting_code="AR-209",
        payment_term_code="NET209",
        credit_limit="1250.50",
        tax_identifier="VAT209",
        roles=["customer", "supplier"],
    )
    listing = reference_register(session, tid, "customer", query="Preview customer")[
        "items"
    ][0]
    assert listing["accounting_code"] == "AR-209"
    assert listing["payment_term_code"] == "NET209"
    assert listing["default_currency"] == "EUR"
    detail = reference_detail(session, tid, "customer", party.id)
    fields = {r["label"]: r for s in detail["preview_sections"] for r in s["rows"]}
    assert fields["Credit limit"]["display_parts"][0]["value"] == "1250.5"
    assert detail["expected_revision"] == _snapshot_revision(
        master_data_update_snapshot(session, tid, "party", party.id)
    )
    assert detail["roles"] == ["customer", "supplier"]
    item = create_item(
        session, tid, "SKU209", "Named item", default_location_id=business.location.id
    )
    child = create_location(
        session,
        tid,
        "Named bin",
        parent_location_id=business.location.id,
        allows_stock=False,
    )
    for family, record, key in [
        ("item", item, "default_location_name"),
        ("location", child, "parent_location_name"),
    ]:
        detail = reference_detail(session, tid, family, record.id)
        assert detail[key] == business.location.name
        listing = reference_register(session, tid, family, query=record.name)["items"][
            0
        ]
        assert listing[key] == business.location.name
        assert detail["preview_sections"]
    foreign = create_tenant(session, "Foreign reference preview")
    for family, record in [("customer", party), ("item", item), ("location", child)]:
        with pytest.raises(NotFound):
            reference_detail(session, foreign.id, family, record.id)
