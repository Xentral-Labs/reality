"""Spec 356: retained defaults and separately held partner reference meaning."""

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from intake_review_support import explicit_owner, reviewed_update_party
from test_commercial_master_decisions import OPERATIONS, case, count
from test_document_correction_decisions import case as document_case
from test_document_correction_decisions import state as document_state

from reality.db.core import Party, PriceList, PriceListEntry
from reality.services import core
from reality.tools import application

DEFAULT_CASES = [
    ("payment_term_create", {"discount_percent": None, "discount_days": None, "requires_prepayment": False}),
    ("payment_term_update", {"discount_percent": None, "discount_days": None, "requires_prepayment": False}),
    ("price_list_create", {"valid_from": None, "valid_until": None, "is_default": False}),
    ("price_list_update", {"is_default": False}),
    ("price_tier_create", {"valid_from": None, "valid_until": None}),
    ("party_price_list_assign", {"priority": 100}),
    ("group_price_list_assign", {"priority": 100}),
]


@pytest.mark.parametrize(("tool", "defaults"), DEFAULT_CASES)
def test_commercial_public_defaults_are_retained_before_actual_execution(session, business, tool, defaults):
    tenant = business.tenant.id
    values = case(session, business, tool)
    for field in defaults:
        values.pop(field, None)
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, values)
    prepared = json.loads(proposal.input)
    assert {field: prepared[field] for field in defaults} == defaults
    assert "_commit" not in prepared
    receipt = application.approve_and_execute_proposal(session, tenant, proposal.id, confirming_principal=owner, confirmed=True)
    assert receipt.decided_by_user_id == owner.user_id
    row_id = json.loads(receipt.output)["records"][0]["id"]
    row = session.get(OPERATIONS[tool][1], (tenant, row_id))
    for field, value in defaults.items():
        assert getattr(row, field) == value


@pytest.mark.parametrize("tool", ["price_tier_create", "price_list_create"])
def test_commercial_decimal_and_datetime_statements_keep_their_exact_values(session, business, tool):
    tenant = business.tenant.id
    values = case(session, business, tool)
    if tool == "price_tier_create":
        values.update(unit_price=Decimal("7.1234"), min_quantity=Decimal("2.5000"))
    else:
        values["valid_from"] = datetime(2026, 10, 4, 5, 12, 34, tzinfo=UTC)
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, values)
    prepared = json.loads(proposal.input)
    if tool == "price_tier_create":
        assert prepared["unit_price"] == "7.1234" and prepared["min_quantity"] == "2.5"
    else:
        assert prepared["valid_from"] == "2026-10-04T05:12:34+00:00"
    receipt = application.approve_and_execute_proposal(session, tenant, proposal.id, confirming_principal=owner, confirmed=True)
    row_id = json.loads(receipt.output)["records"][0]["id"]
    model = PriceListEntry if tool == "price_tier_create" else PriceList
    row = session.get(model, (tenant, row_id))
    if tool == "price_tier_create":
        assert row.unit_price == values["unit_price"] and row.min_quantity == values["min_quantity"]
    else:
        assert row.valid_from == values["valid_from"]


@pytest.mark.parametrize("tool", ["party_price_list_assign", "party_group_member_add", "master_data_lifecycle", "document_correct", "document_lines_correct"])
def test_separately_confirmed_partner_roles_require_renewed_retained_review(session, business, tool):
    tenant = business.tenant.id
    if tool.startswith("document_"):
        values = document_case(session, business, tool)
    elif tool == "master_data_lifecycle":
        values = {"model": "party", "record_id": business.customer.id, "is_active": False}
    else:
        values = case(session, business, tool)
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, values)
    party = session.get(Party, (tenant, business.customer.id))
    original_row = {column.name: getattr(party, column.name) for column in Party.__table__.columns}
    reviewed_update_party(session, tenant, party.id, party.name, party.type, roles=["customer", "supplier"])
    session.refresh(party)
    assert {column.name: getattr(party, column.name) for column in Party.__table__.columns} == original_row
    before = (count(session, tenant), document_state(session, tenant))
    with pytest.raises(core.InvalidOperation, match="(?i)changed|review|stale"):
        application.approve_and_execute_proposal(session, tenant, proposal.id, confirming_principal=owner, confirmed=True)
    assert (count(session, tenant), document_state(session, tenant)) == before
