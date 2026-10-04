"""Spec 339: a duplicate business partner merged into its survivor, history kept."""

import json
from datetime import UTC, datetime

import pytest
from intake_review_support import (
    reviewed_merge_party,
    reviewed_post_sales_invoice,
    reviewed_set_master_data_active,
)
from sqlalchemy import event, func, select

from reality.db.core import BusinessEvent, Document, Party, PartyMerge
from reality.services import core
from reality.services.credit_exposure import credit_exposure
from reality.services.finance.balances import party_balances
from reality.services.party_merges import party_merges
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)

AS_OF = datetime(2026, 9, 1, 12, tzinfo=UTC)


def _invoice(session, business, number, amount, party_id):
    document = core.create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        party_id,
        amount,
        document_date="2026-08-01",
    )
    reviewed_post_sales_invoice(session, business.tenant.id, document.id)
    return document


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def _merge(session, business, duplicate, survivor, reason="Same customer"):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "party_merge",
        {
            "duplicate_party_id": duplicate,
            "surviving_party_id": survivor,
            "reason": reason,
        },
    )
    preview = json.loads(proposal.output)
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirmed=True
    )
    return preview, json.loads(executed.output)


def test_a_merge_keeps_both_histories_under_the_survivor(session, business):
    tenant = business.tenant.id
    duplicate = reviewed_create_party(session, tenant, "Müller GmbH (Gast)", "customer")
    _invoice(session, business, "INV-DUP", "100", duplicate.id)
    _invoice(session, business, "INV-SUR", "50", business.customer.id)
    # Positive control: before the merge each partner answers for itself.
    before = party_balances(session, tenant, side="customer", as_of=AS_OF)
    assert {row["party"] for row in before["items"]} == {
        business.customer.name,
        duplicate.name,
    }

    preview, output = _merge(session, business, duplicate.id, business.customer.id)

    assert preview["party_merge"]["duplicate"]["documents"] == 1
    assert preview["party_merge"]["survivor"]["roles"] == ["customer"]
    merge = session.get(PartyMerge, (tenant, output["merge_id"]))
    assert (merge.duplicate_party_id, merge.surviving_party_id) == (
        duplicate.id,
        business.customer.id,
    )
    session.refresh(duplicate)
    assert duplicate.is_active is False
    # Nothing stated changed: the invoice still names the duplicate.
    invoice = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant, Document.number == "INV-DUP"
        )
    )
    assert invoice.party_id == duplicate.id

    detail = core.party_detail(session, tenant, business.customer.id)
    assert {d.number for d in detail["documents"]} == {"INV-DUP", "INV-SUR"}
    assert [m["party_id"] for m in detail["merged_parties"]] == [duplicate.id]
    assert (
        core.party_detail(session, tenant, duplicate.id)["merged_into"]["party_id"]
        == business.customer.id
    )

    after = party_balances(session, tenant, side="customer", as_of=AS_OF)
    (row,) = after["items"]
    assert (row["party_id"], row["party"], row["open"]) == (
        business.customer.id,
        business.customer.name,
        "150.0000",
    )
    assert (
        session.scalar(
            select(func.count()).where(
                BusinessEvent.tenant_id == tenant,
                BusinessEvent.event_type == "party.merged",
            )
        )
        == 1
    )
    (listed,) = party_merges(session, tenant)
    assert (listed["duplicate"], listed["survivor"]) == (
        duplicate.name,
        business.customer.name,
    )


def test_the_credit_exposure_counts_the_merged_partner(session, business):
    tenant = business.tenant.id
    duplicate = reviewed_create_party(session, tenant, "Müller (Shop)", "customer")
    _invoice(session, business, "INV-1", "300", duplicate.id)
    _invoice(session, business, "INV-2", "200", business.customer.id)
    assert credit_exposure(session, tenant, business.customer.id)["exposure"] == 200

    reviewed_merge_party(session, tenant, duplicate.id, business.customer.id, "Shop guest")

    exposure = credit_exposure(session, tenant, business.customer.id)
    assert exposure["exposure"] == 500
    assert {row["number"] for row in exposure["open_invoices"]["rows"]} == {
        "INV-1",
        "INV-2",
    }


def test_every_refusal_changes_nothing(session, business):
    tenant = business.tenant.id
    duplicate = reviewed_create_party(session, tenant, "Dublette", "customer")
    supplier_too = reviewed_create_party(
        session, tenant, "Beides GmbH", "customer", roles=["customer", "supplier"]
    )
    held = reviewed_create_party(session, tenant, "Gesperrt", "customer")
    core.hold_party_delivery(session, tenant, held.id, "collection")
    inactive = reviewed_create_party(session, tenant, "Alt", "customer")
    reviewed_set_master_data_active(session, tenant, Party, inactive.id, False)

    _refused(
        "party_merge_same_party",
        lambda: reviewed_merge_party(session, tenant, duplicate.id, duplicate.id, "x"),
    )
    _refused(
        "party_merge_reason_required",
        lambda: reviewed_merge_party(session, tenant, duplicate.id, business.customer.id, " "),
    )
    _refused(
        "party_merge_party_not_found",
        lambda: reviewed_merge_party(session, tenant, duplicate.id, "pty_missing", "x"),
    )
    _refused(
        "party_merge_company_party",
        lambda: reviewed_merge_party(
            session, tenant, business.company.id, business.customer.id, "x"
        ),
    )
    _refused(
        "party_merge_roles_missing",
        lambda: reviewed_merge_party(
            session, tenant, supplier_too.id, business.customer.id, "x"
        ),
    )
    _refused(
        "party_merge_hold_open",
        lambda: reviewed_merge_party(session, tenant, held.id, business.customer.id, "x"),
    )
    _refused(
        "party_merge_survivor_inactive",
        lambda: reviewed_merge_party(session, tenant, duplicate.id, inactive.id, "x"),
    )
    assert session.scalar(select(func.count()).select_from(PartyMerge)) == 0

    # Positive control, then no chains either way.
    reviewed_merge_party(session, tenant, duplicate.id, business.customer.id, "Same")
    _refused(
        "party_merge_already_merged",
        lambda: reviewed_merge_party(session, tenant, duplicate.id, supplier_too.id, "x"),
    )
    _refused(
        "party_merge_already_merged",
        lambda: reviewed_merge_party(session, tenant, held.id, duplicate.id, "x"),
    )
    assert session.scalar(select(func.count()).select_from(PartyMerge)) == 1


def test_another_company_sees_nothing(session, business):
    tenant = business.tenant.id
    duplicate = reviewed_create_party(session, tenant, "Dublette", "customer")
    reviewed_merge_party(session, tenant, duplicate.id, business.customer.id, "Same")
    other = core.create_tenant(session, "Other GmbH")
    stranger = reviewed_create_party(session, other.id, "Fremd", "customer")

    assert party_merges(session, other.id) == []
    _refused(
        "party_merge_party_not_found",
        lambda: reviewed_merge_party(session, other.id, stranger.id, business.customer.id, "x"),
    )


def test_merged_reads_cost_the_same_however_much_the_duplicate_holds(session, business):
    tenant = business.tenant.id

    def statements(call):
        count = 0

        def counter(*_args, **_kwargs):
            nonlocal count
            count += 1

        event.listen(session.bind, "before_cursor_execute", counter)
        try:
            call()
        finally:
            event.remove(session.bind, "before_cursor_execute", counter)
        return count

    small = reviewed_create_party(session, tenant, "Klein", "customer")
    _invoice(session, business, "INV-S1", "10", small.id)
    reviewed_merge_party(session, tenant, small.id, business.customer.id, "Same")
    detail_small = statements(
        lambda: core.party_detail(session, tenant, business.customer.id)
    )

    big = reviewed_create_party(session, tenant, "Gross", "customer")
    for number in range(5):
        _invoice(session, business, f"INV-B{number}", "10", big.id)
    reviewed_merge_party(session, tenant, big.id, business.customer.id, "Same")
    detail_big = statements(
        lambda: core.party_detail(session, tenant, business.customer.id)
    )

    assert detail_big == detail_small


def test_a_file_row_naming_the_duplicate_lands_on_the_survivor(session, business):
    from reality.services.file_interpreters import _party

    tenant = business.tenant.id
    duplicate = reviewed_create_party(session, tenant, "Müller GmbH", "customer")
    # Positive control: two partners of one name are ambiguous before the merge.
    _refused_text = pytest.raises(core.InvalidOperation)
    with _refused_text:
        _party(session, tenant, {"party_name": "Müller GmbH"})

    reviewed_merge_party(session, tenant, duplicate.id, business.customer.id, "Same")

    assert _party(session, tenant, {"party_name": "Müller GmbH"}).id == (
        business.customer.id
    )


from intake_review_support import reviewed_create_party
