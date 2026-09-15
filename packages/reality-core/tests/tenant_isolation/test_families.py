from __future__ import annotations

import json
from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.catalogs import load_tenant_isolation_catalog
from reality.db.core import (
    AppUser,
    Document,
    InvitationDelivery,
    TenantMembership,
    now,
    uid,
)
from reality.services.core import (
    NotFound,
    account_balance,
    chat_session_count,
    chat_sessions,
    commitments,
    correct_manual_document_lines,
    create_commitment,
    document_detail,
    financial_open_items,
    get_chat_session,
    integration_registry,
    inventory_rows,
    item_detail,
    items,
    locations,
    manual_document_line_snapshot,
    movement_register,
    parties,
    party_detail,
    source_records,
    stock_at,
    timeline,
)
from reality.services.memberships import (
    Principal,
    access_summary,
    create_invitation,
    inspect_invitation,
)
from reality.services.notifications import issue_delivery_token
from reality.services.projections import (
    projection_rows,
    refresh_operational_projections,
)
from reality.tools.application import run_read_tool

from .coverage import event_sequences, tenant_row_counts


def _family(key: str) -> dict:
    return next(
        family
        for family in load_tenant_isolation_catalog().families
        if family["key"] == key
    )


def test_record_reads_are_non_disclosing(session, two_tenant_graph):
    local = two_tenant_graph.local
    foreign = two_tenant_graph.foreign

    with pytest.raises(NotFound) as foreign_error:
        document_detail(session, local.tenant.id, foreign.document.id)
    with pytest.raises(NotFound) as unknown_error:
        document_detail(session, local.tenant.id, "doc_unknown")

    assert str(foreign_error.value) == str(unknown_error.value)
    assert (
        document_detail(session, local.tenant.id, local.document.id)["document"].id
        == local.document.id
    )
    for detail_service, foreign_id, unknown_id in (
        (party_detail, foreign.customer.id, "par_unknown"),
        (item_detail, foreign.item.id, "itm_unknown"),
        (get_chat_session, foreign.chat_session.id, "cht_unknown"),
    ):
        with pytest.raises(NotFound) as foreign_detail_error:
            detail_service(session, local.tenant.id, foreign_id)
        with pytest.raises(NotFound) as unknown_detail_error:
            detail_service(session, local.tenant.id, unknown_id)
        assert str(foreign_detail_error.value) == str(unknown_detail_error.value)
    assert _family("record_reads")["classification"] == "record_read"


def test_document_line_correction_is_non_disclosing_across_tenants(
    session, two_tenant_graph
):
    local = two_tenant_graph.local
    foreign = two_tenant_graph.foreign

    with pytest.raises(NotFound) as foreign_read:
        manual_document_line_snapshot(session, local.tenant.id, foreign.document.id)
    with pytest.raises(NotFound) as unknown_read:
        manual_document_line_snapshot(session, local.tenant.id, "doc_unknown")
    assert str(foreign_read.value) == str(unknown_read.value)

    with pytest.raises(NotFound) as foreign_write:
        correct_manual_document_lines(
            session,
            local.tenant.id,
            foreign.document.id,
            expected_revision="foreign",
            lines=[{"quantity": "1"}],
        )
    with pytest.raises(NotFound) as unknown_write:
        correct_manual_document_lines(
            session,
            local.tenant.id,
            "doc_unknown",
            expected_revision="foreign",
            lines=[{"quantity": "1"}],
        )
    assert str(foreign_write.value) == str(unknown_write.value)


def test_collections_exclude_foreign_records(session, two_tenant_graph):
    local = two_tenant_graph.local
    foreign = two_tenant_graph.foreign

    assert {row.id for row in parties(session, local.tenant.id)} == {
        local.company.id,
        local.customer.id,
    }
    assert {row.id for row in items(session, local.tenant.id)} == {local.item.id}
    assert {row.id for row in locations(session, local.tenant.id)} == {
        local.location.id
    }
    assert {row.id for row in commitments(session, local.tenant.id)} == {
        local.commitment.id
    }
    assert foreign.item.id not in {
        row["item"].id for row in inventory_rows(session, local.tenant.id)
    }
    assert {row.id for row in source_records(session, local.tenant.id)} == {
        local.source.id
    }
    assert {row.id for row in chat_sessions(session, local.tenant.id)} == {
        local.chat_session.id
    }
    assert {
        system.id
        for system in integration_registry(session, local.tenant.id)["systems"]
    } == {local.source_system.id}
    assert all(
        row["document"].tenant_id == local.tenant.id
        for row in financial_open_items(session, local.tenant.id)
    )
    assert all(
        row["movement"].tenant_id == local.tenant.id
        for row in movement_register(session, local.tenant.id)
    )
    local_timeline_ids = {row[3] for row in timeline(session, local.tenant.id)}
    assert local.source.id in local_timeline_ids
    assert foreign.source.id not in local_timeline_ids
    assert foreign.commitment.id not in local_timeline_ids
    assert _family("collections")["classification"] == "collection"


def test_aggregates_exclude_foreign_values(session, two_tenant_graph):
    local = two_tenant_graph.local
    foreign = two_tenant_graph.foreign

    assert stock_at(
        session, local.tenant.id, local.item.id, local.location.id
    ) == Decimal(3)
    assert stock_at(
        session, foreign.tenant.id, foreign.item.id, foreign.location.id
    ) == Decimal(11)
    assert chat_session_count(session, local.tenant.id) == 1
    assert chat_session_count(session, foreign.tenant.id) == 1
    assert account_balance(session, local.tenant.id, "accounts_receivable") == Decimal(
        100
    )
    assert account_balance(
        session, foreign.tenant.id, "accounts_receivable"
    ) == Decimal(100)
    refresh_operational_projections(session, local.tenant.id)
    projected_inventory = projection_rows(session, local.tenant.id, "inventory")
    assert {row["item_id"] for row in projected_inventory} == {local.item.id}
    assert foreign.item.id not in {row["item_id"] for row in projected_inventory}
    assert _family("aggregates")["classification"] == "aggregate"
    from reality.services.core import (
        create_manual_document_with_lines,
        uncredited_return_quantity,
    )

    _, lines = create_manual_document_with_lines(
        session,
        foreign.tenant.id,
        "sales_order",
        "RETURN-FOREIGN",
        foreign.customer.id,
        [
            {
                "item_id": foreign.item.id,
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "25",
                "gross_amount": "25",
            }
        ],
        "25",
    )
    assert uncredited_return_quantity(session, foreign.tenant.id, lines[0].id) == 0
    with pytest.raises(NotFound):
        uncredited_return_quantity(session, local.tenant.id, lines[0].id)
    # The bulk promise read answers only for the tenant it is asked about: foreign
    # promise ids are absent, and without ids it lists the tenant's own promises only.
    from reality.services.core import commitment_terms

    foreign_ids = {row.id for row in commitments(session, foreign.tenant.id)}
    assert foreign_ids
    assert commitment_terms(session, local.tenant.id, foreign_ids) == {}
    assert set(commitment_terms(session, foreign.tenant.id, foreign_ids)) == foreign_ids
    assert set(commitment_terms(session, local.tenant.id)).isdisjoint(foreign_ids)
    # The bulk settlement read answers only for documents of the tenant it is asked
    # about: a foreign invoice passed in is absent, not measured.
    from reality.services.core import open_invoice_amounts, settlement_positions

    foreign_invoices = list(
        session.scalars(
            select(Document).where(
                Document.tenant_id == foreign.tenant.id,
                Document.type == "sales_invoice",
            )
        )
    )
    assert foreign_invoices
    assert settlement_positions(session, local.tenant.id, foreign_invoices) == {}
    assert open_invoice_amounts(session, local.tenant.id, foreign_invoices) == {}
    assert set(open_invoice_amounts(session, foreign.tenant.id, foreign_invoices)) == {
        row.id for row in foreign_invoices
    }


def test_source_evidence_reality_lineage_stays_local_and_lossless(
    session, two_tenant_graph
):
    local = two_tenant_graph.local
    foreign = two_tenant_graph.foreign
    original_payload = local.source.payload

    detail = document_detail(session, local.tenant.id, local.document.id)

    assert detail["source"].id == local.source.id
    assert local.commitment.document_id == local.document.id
    assert json.loads(local.source.payload)["tenant_marker"] == "Local"
    assert local.source.payload == original_payload
    with pytest.raises(NotFound):
        document_detail(session, local.tenant.id, foreign.document.id)


def test_membership_invitation_operations_are_registered_at_tenant_boundaries():
    catalog = load_tenant_isolation_catalog()
    operations = {
        operation for family in catalog.families for operation in family["operations"]
    }

    assert {
        "reality.services.memberships:access_summary",
        "reality.services.memberships:create_invitation",
        "reality.services.memberships:remove_member",
        "reality.services.memberships:resend_invitation",
        "reality.services.memberships:revoke_invitation",
        "reality.services.notifications:enqueue_invitation_delivery",
        "reality.services.notifications:issue_delivery_token",
    } <= operations


def test_membership_access_collection_is_scoped_and_non_disclosing(
    session, two_tenant_graph
):
    local = two_tenant_graph.local
    foreign = two_tenant_graph.foreign
    local_owner = AppUser(
        id=uid("usr"),
        email="isolation-local-owner@example.com",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    foreign_owner = AppUser(
        id=uid("usr"),
        email="isolation-foreign-owner@example.com",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add_all([local_owner, foreign_owner])
    session.flush()
    session.add_all(
        [
            TenantMembership(
                id=uid("tmb"),
                tenant_id=local.tenant.id,
                user_id=local_owner.id,
                role="owner",
                status="active",
            ),
            TenantMembership(
                id=uid("tmb"),
                tenant_id=foreign.tenant.id,
                user_id=foreign_owner.id,
                role="owner",
                status="active",
            ),
        ]
    )
    session.flush()
    local_invitation = create_invitation(
        session,
        local.tenant.id,
        Principal(local_owner.id),
        "isolation-local-recipient@example.com",
    )
    foreign_invitation = create_invitation(
        session,
        foreign.tenant.id,
        Principal(foreign_owner.id),
        "isolation-foreign-recipient@example.com",
    )
    local_delivery = (
        session.query(InvitationDelivery)
        .filter_by(invitation_id=local_invitation.id)
        .one()
    )
    foreign_delivery = (
        session.query(InvitationDelivery)
        .filter_by(invitation_id=foreign_invitation.id)
        .one()
    )
    _, _, local_token = issue_delivery_token(
        session, local.tenant.id, local_delivery.id
    )
    _, _, foreign_token = issue_delivery_token(
        session, foreign.tenant.id, foreign_delivery.id
    )

    summary = access_summary(session, local.tenant.id, Principal(local_owner.id))
    assert {row["email"] for row in summary["members"]} == {local_owner.email}
    assert foreign_owner.email not in {row["email"] for row in summary["members"]}
    assert inspect_invitation(session, local_token)["company_name"] == local.tenant.name
    assert (
        inspect_invitation(session, foreign_token)["company_name"]
        == foreign.tenant.name
    )
    assert inspect_invitation(session, "unknown-token") == {"status": "unavailable"}

    with pytest.raises(NotFound) as foreign_error:
        access_summary(session, foreign.tenant.id, Principal(local_owner.id))
    with pytest.raises(NotFound) as unknown_error:
        access_summary(session, "ten_unknown", Principal(local_owner.id))
    assert str(foreign_error.value) == str(unknown_error.value) == "Company not found."


def test_cross_tenant_mutations_are_atomic(session, two_tenant_graph):
    local = two_tenant_graph.local
    foreign = two_tenant_graph.foreign
    tenant_ids = (local.tenant.id, foreign.tenant.id)
    rows_before = tenant_row_counts(session, tenant_ids)
    events_before = event_sequences(session, tenant_ids)

    with pytest.raises(NotFound):
        create_commitment(
            session,
            local.tenant.id,
            "customer_delivery",
            local.company.id,
            local.customer.id,
            foreign.item.id,
            local.location.id,
            1,
            "2026-09-04",
        )

    assert tenant_row_counts(session, tenant_ids) == rows_before
    assert event_sequences(session, tenant_ids) == events_before
    assert (
        _family("mutations_and_relationships")["classification"]
        == "mutation_relationship"
    )


def test_registered_boundaries_are_tenant_scoped(session, two_tenant_graph):
    local = two_tenant_graph.local
    foreign = two_tenant_graph.foreign

    from reality.services.projections import INVENTORY, rebuild_projections

    for graph in (local, foreign):
        rebuild_projections(session, graph.tenant.id, (INVENTORY,))
    result = run_read_tool(session, local.tenant.id, "inventory")

    assert {row["item_id"] for row in result} == {local.item.id}
    assert foreign.item.id not in {row["item_id"] for row in result}
    assert _family("application_boundaries")["classification"] == "boundary"


def test_global_tenant_administration_is_explicit():
    family = _family("tenant_administration")

    assert family["classification"] == "global_admin"
    assert family["reason"]
    assert all(
        operation.startswith("reality.services.core:")
        for operation in family["operations"]
    )
