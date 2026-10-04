"""Every business company knows its own business partner (spec 289)."""

import json

import pytest
import test_costing_services as costing_fixtures
import test_inventory_costing_services as stock
from conftest import record_by_id
from sqlalchemy import select

from reality.db.core import ChangeProposal, Party, PartyRole, SourceRecord
from reality.services import company_party, company_setup
from reality.services.core import InvalidOperation
from reality.services.cost_review_draft import cost_review_draft
from reality.tools.application import approve_and_execute_proposal


def company_parties(session, tenant_id):
    return list(
        session.scalars(
            select(Party)
            .join(
                PartyRole,
                (PartyRole.tenant_id == Party.tenant_id)
                & (PartyRole.party_id == Party.id),
            )
            .where(Party.tenant_id == tenant_id, PartyRole.role == "company")
        )
    )


def all_parties(session, tenant_id):
    return list(session.scalars(select(Party).where(Party.tenant_id == tenant_id)))


def create(
    session, owner, request_key, environment="business", name="Lampenhaus Berg GmbH"
):
    return company_setup.create_company(
        session,
        owner.id,
        request_key,
        name,
        environment,
        "empty",
        confirmed=True,
    )["tenant_id"]


# US1 new companies ------------------------------------------------------------------


def test_business_company_records_its_partner(session, scheduled_owner):
    tenant_id = create(session, scheduled_owner, "company-289")
    (party,) = company_parties(session, tenant_id)
    assert party.name == "Lampenhaus Berg GmbH"
    assert party.type == "company"
    # The company partner is the only business partner of a new company.
    assert [row.id for row in all_parties(session, tenant_id)] == [party.id]


def test_replayed_creation_keeps_one_partner(session, scheduled_owner):
    first = create(session, scheduled_owner, "company-289-replay")
    again = create(session, scheduled_owner, "company-289-replay")
    assert first == again
    assert len(company_parties(session, first)) == 1


def test_creation_source_states_the_requested_name(session, scheduled_owner):
    tenant_id = create(
        session, scheduled_owner, "company-289-source", name=" Kerze & Co "
    )
    (party,) = company_parties(session, tenant_id)
    source = record_by_id(session, SourceRecord, party.source_record_id)
    assert source.tenant_id == tenant_id
    assert source.source_system == "reality"
    assert source.external_id == "company-setup:company-289-source"
    # Recorded as the person stated it (trimmed like the company name), never derived.
    assert json.loads(source.payload) == {
        "name": "Kerze & Co",
        "roles": ["company"],
        "request_key": "company-289-source",
    }


def test_sandbox_demo_and_storyline_parties_are_unchanged(session, scheduled_owner):
    # An empty sandbox keeps no business partner, so Demo Data can still connect to it.
    tenant_id = create(session, scheduled_owner, "sandbox-289", environment="sandbox")
    assert all_parties(session, tenant_id) == []


# US2 existing companies ---------------------------------------------------------------

cost_owner = costing_fixtures.cost_owner


def without_company_partner(session, business):
    for role in session.scalars(
        select(PartyRole).where(
            PartyRole.tenant_id == business.tenant.id, PartyRole.role == "company"
        )
    ):
        session.delete(role)
    business.company.type = "supplier"
    session.flush()


def company_input(session, business):
    draft = cost_review_draft(
        session,
        business.tenant.id,
        kind="inventory",
        scope_id=business.item.id,
        answers={"method": "fifo"},
    )
    return next(
        (e for e in draft["open_inputs"] if e["code"] == "company_party_missing"), None
    )


def confirm(session, business, proposal):
    from intake_review_support import explicit_owner

    return approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, confirming_principal=explicit_owner(session, business.tenant.id), confirmed=True
    )


def test_draft_offers_the_prefilled_action(session, business, cost_owner):
    stock.prepared(session, business, cost_owner)
    # Positive control: with a company partner nothing is asked.
    assert company_input(session, business) is None
    without_company_partner(session, business)
    assert company_input(session, business) == {
        "code": "company_party_missing",
        "action": "company_party_record",
        "name": business.tenant.name,
    }


def test_confirmed_proposal_records_through_master_data(session, business, cost_owner):
    stock.prepared(session, business, cost_owner)
    without_company_partner(session, business)
    proposal = company_party.propose_company_party(session, business.tenant.id)
    assert proposal.type == "tool:company_party_record"
    assert json.loads(proposal.input) == {
        "name": business.tenant.name,
        "roles": ["company"],
    }
    confirm(session, business, proposal)
    (party,) = company_parties(session, business.tenant.id)
    assert party.name == business.tenant.name
    # The draft now uses it as the stock owner.
    assert company_input(session, business) is None


def test_draft_names_the_waiting_proposal(session, business, cost_owner):
    stock.prepared(session, business, cost_owner)
    without_company_partner(session, business)
    proposal = company_party.propose_company_party(session, business.tenant.id)
    assert company_input(session, business) == {
        "code": "company_party_missing",
        "proposal_id": proposal.id,
    }
    # Asking again returns the waiting proposal instead of a second one.
    assert (
        company_party.propose_company_party(session, business.tenant.id).id
        == proposal.id
    )


def test_confirmation_is_refused_once_a_partner_exists(session, business, cost_owner):
    from intake_review_support import create_reviewed_master

    stock.prepared(session, business, cost_owner)
    without_company_partner(session, business)
    proposal = company_party.propose_company_party(session, business.tenant.id)
    create_reviewed_master(session, business.tenant.id, "party", {"name": "Recorded meanwhile", "type": "company", "roles": ["company"]})
    with pytest.raises(InvalidOperation, match="already exists") as refused:
        confirm(session, business, proposal)
    assert refused.value.code == "company_party_exists"
    assert [p.name for p in company_parties(session, business.tenant.id)] == [
        "Recorded meanwhile"
    ]


def test_several_partners_keep_the_choice(session, business, cost_owner):
    from intake_review_support import create_reviewed_master

    stock.prepared(session, business, cost_owner)
    create_reviewed_master(session, business.tenant.id, "party", {"name": "Second company", "type": "company", "roles": ["company"]})
    entry = company_input(session, business)
    assert set(entry) == {"code", "choices"} and len(entry["choices"]) == 2


def test_no_party_before_confirmation(session, business, cost_owner):
    stock.prepared(session, business, cost_owner)
    without_company_partner(session, business)
    before = len(all_parties(session, business.tenant.id))
    company_party.propose_company_party(session, business.tenant.id)
    assert len(all_parties(session, business.tenant.id)) == before
    assert company_parties(session, business.tenant.id) == []
    # A caller cannot choose the name: the proposal takes no fields.
    from reality.tools.application import create_change_proposal

    with pytest.raises(InvalidOperation) as refused:
        create_change_proposal(
            session, business.tenant.id, "company_party_record", {"name": "Other"}
        )
    assert refused.value.code == "company_party_arguments_unsupported"
    assert (
        session.scalar(
            select(ChangeProposal.id).where(ChangeProposal.input.contains("Other"))
        )
        is None
    )


def test_practice_company_is_not_offered_the_action(session, scheduled_owner):
    tenant_id = create(
        session, scheduled_owner, "sandbox-289-offer", environment="sandbox"
    )
    assert company_party.offer(session, tenant_id) is None


# US3 chat and MCP -----------------------------------------------------------------------


def test_mcp_draft_and_propose_parity(session, business, cost_owner):
    from reality.mcp.catalog import MCP_TOOL_REGISTRY

    stock.prepared(session, business, cost_owner)
    without_company_partner(session, business)
    read = MCP_TOOL_REGISTRY["cost_review_draft"].handler(
        session,
        business.tenant.id,
        {
            "kind": "inventory",
            "scope_id": business.item.id,
            "answers": {"method": "fifo"},
        },
    )
    entry = next(e for e in read["open_inputs"] if e["code"] == "company_party_missing")
    # The same action and name the web draft offers.
    assert entry == company_input(session, business)
    proposed = MCP_TOOL_REGISTRY["company_party_record_propose"].handler(
        session, business.tenant.id, {}
    )
    assert proposed["name"] == business.tenant.name
    assert proposed["status"] == "proposed"
    assert company_parties(session, business.tenant.id) == []
    again = MCP_TOOL_REGISTRY["company_party_record_propose"].handler(
        session, business.tenant.id, {}
    )
    assert again["proposal_id"] == proposed["proposal_id"]
