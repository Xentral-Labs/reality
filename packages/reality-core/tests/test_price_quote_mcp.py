
import pytest
from intake_review_support import (
    reviewed_add_party_group_member,
    reviewed_assign_group_price_list,
    reviewed_assign_party_price_list,
    reviewed_create_party_group,
    reviewed_create_price_list,
    reviewed_create_price_list_entry,
)

from reality.mcp.catalog import dispatch_tool
from reality.services.core import (
    NotFound,
    create_tenant,
    resolve_price,
)


def quote(session, tenant_id, party_id, item_id, quantity="12"):
    return dispatch_tool(
        session,
        tenant_id,
        "price_quote_read",
        {
            "party_id": party_id,
            "item_id": item_id,
            "quantity": quantity,
            "direction": "sales",
            "currency": "eur",
            "unit": "pcs",
            "at": "2026-09-23T10:00:00Z",
        },
        allowed_access=("read",),
    )


def test_price_quote_matches_canonical_service_and_exposes_direct_provenance(
    session, business
):
    price_list = reviewed_create_price_list(
        session, business.tenant.id, "DIRECT", "Direct", "sales", "EUR"
    )
    entry = reviewed_create_price_list_entry(
        session,
        business.tenant.id,
        price_list.id,
        business.item.id,
        10,
        "8.50",
        "pcs",
    )
    assignment = reviewed_assign_party_price_list(
        session, business.tenant.id, business.customer.id, price_list.id
    )

    result = quote(session, business.tenant.id, business.customer.id, business.item.id)
    canonical = resolve_price(
        session,
        business.tenant.id,
        business.customer.id,
        business.item.id,
        12,
        "sales",
        "EUR",
        "pcs",
        at="2026-09-23T10:00:00Z",
    )

    assert result == {
        "matched": True,
        "party_id": business.customer.id,
        "item_id": business.item.id,
        "quantity": "12",
        "direction": "sales",
        "currency": "EUR",
        "unit": "pcs",
        "evaluated_at": "2026-09-23T10:00:00+00:00",
        "unit_price": str(canonical.unit_price),
        "price_list_id": price_list.id,
        "price_list_entry_id": entry.id,
        "source": "party",
        "assignment_id": assignment.id,
        "party_group_id": None,
    }


def test_price_quote_returns_explicit_no_match(session, business):
    result = quote(session, business.tenant.id, business.customer.id, business.item.id)

    assert result["matched"] is False
    assert result["currency"] == "EUR"
    assert result["evaluated_at"] == "2026-09-23T10:00:00+00:00"
    assert "unit_price" not in result


def test_price_quote_exposes_group_and_default_selection_paths(session, business):
    default = reviewed_create_price_list(
        session,
        business.tenant.id,
        "DEFAULT",
        "Default",
        "sales",
        "EUR",
        is_default=True,
    )
    reviewed_create_price_list_entry(
        session, business.tenant.id, default.id, business.item.id, 1, "10", "pcs"
    )
    default_result = quote(
        session, business.tenant.id, business.customer.id, business.item.id
    )
    assert default_result["source"] == "default"
    assert default_result["assignment_id"] is None

    group_list = reviewed_create_price_list(
        session, business.tenant.id, "GROUP", "Group", "sales", "EUR"
    )
    reviewed_create_price_list_entry(
        session, business.tenant.id, group_list.id, business.item.id, 1, "8", "pcs"
    )
    group = reviewed_create_party_group(session, business.tenant.id, "GROUP", "Group")
    reviewed_add_party_group_member(session, business.tenant.id, group.id, business.customer.id)
    assignment = reviewed_assign_group_price_list(
        session, business.tenant.id, group.id, group_list.id
    )

    group_result = quote(
        session, business.tenant.id, business.customer.id, business.item.id
    )
    assert group_result["source"] == "group"
    assert group_result["assignment_id"] == assignment.id
    assert group_result["party_group_id"] == group.id


def test_price_quote_does_not_disclose_foreign_party_or_item(session, business):
    foreign = create_tenant(session, "Foreign pricing")
    party = reviewed_create_party(session, foreign.id, "Foreign party", "customer")
    item = reviewed_create_item(session, foreign.id, "FOREIGN", "Foreign item")

    with pytest.raises(NotFound):
        quote(session, business.tenant.id, party.id, business.item.id)
    with pytest.raises(NotFound):
        quote(session, business.tenant.id, business.customer.id, item.id)


from intake_review_support import reviewed_create_item, reviewed_create_party
