"""Live HTTP acceptance proof of owner, member and private-author decisions (spec 323).

Run explicitly with pytest; the shared live stack owns and removes its test database.
Business fixtures and changes use the same application services as the product.
"""

import json
from uuid import uuid4

import httpx
from conftest import business
from intake_review_support import reviewed_reserve
from live_stack import PASSWORD, add_member, live_stack, migrate
from sqlalchemy.orm import sessionmaker
from test_proposal_decision_policy import _held_release
from unified_fixtures import delivery_fixture

from reality.db.core import build_engine
from reality.services.analytics.reports import caller
from reality.services.memberships import Principal
from reality.tools.application import create_change_proposal


def test_live_proposal_decision_roles(postgres_database, tmp_path):
    artifacts = tmp_path / "proposal-decisions"
    artifacts.mkdir(exist_ok=True)
    env = migrate(postgres_database, artifacts)
    engine = build_engine(postgres_database)
    with sessionmaker(engine, expire_on_commit=False)() as session:
        company = business.__wrapped__(session)
        tenant = company.tenant.id
        add_member(session, tenant, "owner@example.test", "Policy Owner", "owner")
        author = add_member(
            session, tenant, "member@example.test", "Policy Member Author", "member"
        )
        credit, _ = _held_release(session, company)
        rejection, _ = _held_release(session, company)
        fixture = delivery_fixture(session, company, quantity="2")
        reviewed_reserve(session, tenant, fixture.commitment.id)
        shipment = create_change_proposal(
            session,
            tenant,
            "shipment_dispatch",
            {
                "purpose": "customer_delivery",
                "counterparty_id": company.customer.id,
                "movements": [
                    {
                        "commitment_id": fixture.commitment.id,
                        "item_id": company.item.id,
                        "from_location_id": company.location.id,
                        "quantity": "2",
                    }
                ],
            },
        )
        with caller(Principal(author.id)):
            report = create_change_proposal(
                session,
                tenant,
                "graph.reports.change",
                {
                    "operation": "create",
                    "request_id": str(uuid4()),
                    "name": "Live policy report",
                    "question": {
                        "from": "order",
                        "as": "o",
                        "measures": ["stated_order_amount"],
                        "group_by": [{"field": "o.currency"}],
                    },
                },
            )
        records = {
            "credit": credit.id,
            "shipment": shipment.id,
            "report": report.id,
            "reject_credit": rejection.id,
        }
        tokens = {
            p.id: json.loads(p.input).get("_delivery_review", {}).get("token")
            for p in [credit, shipment, report, rejection]
        }
        session.commit()
    engine.dispose()
    with (
        live_stack(env, artifacts) as stack,
        httpx.Client(base_url=stack["api"]) as member,
        httpx.Client(base_url=stack["api"]) as owner_client,
    ):
        for client, email in [
            (member, "member@example.test"),
            (owner_client, "owner@example.test"),
        ]:
            login = client.post(
                "/api/auth/login", json={"email": email, "password": PASSWORD}
            )
            assert login.status_code == 200, login.text
        base = f"/api/tenants/{tenant}/change-proposals"
        for key, authority in [
            ("credit", "company_owner"),
            ("shipment", "company_member"),
            ("report", "private_report_author"),
        ]:
            review = member.get(f"{base}/{records[key]}/review")
            assert review.status_code == 200, review.text
            assert (
                review.json()["next_step"]["decision_policy"]["approval"]["authority"]
                == authority
            )

        def approve(client, key):
            token = tokens[records[key]]
            if token:
                fresh = client.post(
                    f"/api/tenants/{tenant}/delivery-actions/{records[key]}/review"
                )
                assert fresh.status_code == 200, fresh.text
                token = fresh.json()["review"]["token"]
            return client.post(
                f"{base}/{records[key]}/approve",
                json={"confirmed": True, "review_token": token},
            )

        refused = approve(member, "credit")
        assert refused.status_code == 400, refused.text
        assert refused.json()["code"] == "company_owner_access_required"
        refused = approve(owner_client, "report")
        assert refused.status_code == 400, refused.text
        assert "original author" in refused.json()["detail"]
        rejected = member.post(
            f"{base}/{records['reject_credit']}/reject", json={"confirmed": True}
        )
        assert (
            rejected.status_code == 200 and rejected.json()["status"] == "rejected"
        ), rejected.text
        # Dispatch first; review each later action against its current state.
        for client, key in [
            (member, "shipment"),
            (owner_client, "credit"),
            (member, "report"),
        ]:
            result = approve(client, key)
            assert (
                result.status_code == 200 and result.json()["status"] == "executed"
            ), result.text
        print(
            "LIVE_API_PASS owner credit; member shipment; original report author; separate rejection",
            flush=True,
        )
