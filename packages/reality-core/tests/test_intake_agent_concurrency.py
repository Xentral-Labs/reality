"""Spec 355: independent database transactions share one real mandate quota."""

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select, text
from test_bulk_intake_admission import prepared_orders
from test_intake_agent_review import agent_context, owner_mandate, reviewed_evidence

from reality.db.core import AppUser, ChangeProposal, Document
from reality.services import core
from reality.services.intake_review import submit_agent_review


@pytest.mark.parametrize("distinct", [True, False])
def test_competing_connections_charge_one_exact_accepted_receipt(
    scheduled_database, distinct
):
    _engine, factory, tenant_id, actor_id = scheduled_database
    with factory() as session:
        business = SimpleNamespace(
            tenant=core.get_tenant(session, tenant_id),
            company=reviewed_create_party(
                session, tenant_id, "Quota company", "company"
            ),
            customer=reviewed_create_party(
                session, tenant_id, "Quota customer", "customer"
            ),
            item=reviewed_create_item(session, tenant_id, "QUOTA-ITEM", "Quota item"),
            location=reviewed_create_location(session, tenant_id, "Quota warehouse"),
        )
        owner = session.get(AppUser, actor_id)
        mandate_id, token = owner_mandate(session, business, owner, daily_units=1)
        entries = prepared_orders(session, business, 2 if distinct else 1)
        with agent_context(business, token):
            evidence = [
                reviewed_evidence(
                    session,
                    business,
                    mandate_id,
                    session.get(ChangeProposal, (tenant_id, entry["proposal_id"])),
                )
                for entry in entries
            ]
        session.commit()
    barrier = Barrier(2)

    def submit(index):
        with factory() as session, agent_context(business, token):
            session.execute(text("SET LOCAL statement_timeout = '20s'"))
            barrier.wait(timeout=10)
            try:
                result = submit_agent_review(
                    session, tenant_id, evidence[index if distinct else 0]
                )
            except core.InvalidOperation as error:
                session.rollback()
                assert error.code == "intake_approval_required"
                return "quota_refused"
            assert result.status == "executed"
            return "accepted"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert results.count("accepted") == (1 if distinct else 2)
    assert results.count("quota_refused") == (1 if distinct else 0)
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(Document)) == 1
        accepted = list(
            session.scalars(
                select(ChangeProposal).where(
                    ChangeProposal.tenant_id == tenant_id,
                    ChangeProposal.type == "tool:intake_apply",
                    ChangeProposal.status == "executed",
                )
            )
        )
        assert len(accepted) == 1
        assert accepted[0].decided_by_user_id is None
        assert accepted[0].decided_via_token_id == token.id
        receipt = json.loads(accepted[0].output)["agent_review"]
        assert receipt["mandate_id"] == mandate_id
        assert receipt["source_stated_amount"] == "1"
        with agent_context(business, token):
            exact = next(
                review for review in evidence if review["proposal_id"] == accepted[0].id
            )
            assert submit_agent_review(session, tenant_id, exact).id == accepted[0].id


from intake_review_support import (
    reviewed_create_item,
    reviewed_create_location,
    reviewed_create_party,
)
