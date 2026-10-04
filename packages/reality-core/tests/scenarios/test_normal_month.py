from datetime import UTC, datetime
from decimal import Decimal

import pytest
from intake_review_support import accept_normal_month as run_normal_month
from sqlalchemy import func, select

from reality.db.core import ChangeProposal, Commitment, Item, Movement, Party
from reality.demo.normal_month import SCENARIO_ACTION
from reality.services import company_setup
from reality.services.core import (
    InvalidOperation,
    aging_register,
    create_party,
    create_tenant,
)
from reality.services.exceptions import operational_exceptions


def test_normal_month_reuses_setup_company_identity(session, scheduled_owner):
    from reality.services.company_party import company_party_ids
    from reality.services.cost_review_draft import cost_review_draft
    from reality.services.file_interpreters import _single_company

    tenant_id = company_setup.create_company(
        session,
        scheduled_owner.id,
        "normal-month-identity",
        "Lampenhaus Berg GmbH",
        "business",
        "empty",
        confirmed=True,
    )["tenant_id"]
    (company,) = session.scalars(
        select(Party).where(Party.tenant_id == tenant_id)
    ).all()
    original = (company.id, company.name, company.source_record_id)
    assert session.scalar(select(Item.id).where(Item.tenant_id == tenant_id)) is None

    result = run_normal_month(session, tenant_id)
    assert result["physical"] == Decimal("6.0000")
    assert company_party_ids(session, tenant_id) == [company.id]
    assert _single_company(session, tenant_id).id == company.id
    assert (company.id, company.name, company.source_record_id) == original
    commitments = session.scalars(
        select(Commitment).where(Commitment.tenant_id == tenant_id)
    ).all()
    assert commitments
    assert all(
        company.id in (row.from_party_id, row.to_party_id) for row in commitments
    )
    review = cost_review_draft(
        session, tenant_id, kind="inventory", scope_id=result["item_id"]
    )
    assert not any(
        row["code"] == "company_party_missing" for row in review["open_inputs"]
    )
    assert run_normal_month(session, tenant_id) == result
    assert company_party_ids(session, tenant_id) == [company.id]


@pytest.mark.parametrize("role", ["customer", "company"])
def test_normal_month_refuses_other_partners_after_setup(
    session, scheduled_owner, role
):
    tenant_id = company_setup.create_company(
        session,
        scheduled_owner.id,
        f"normal-month-other-{role}",
        "Lampenhaus Berg GmbH",
        "business",
        "empty",
        confirmed=True,
    )["tenant_id"]
    create_party(session, tenant_id, "Existing partner", role)
    with pytest.raises(InvalidOperation, match="requires an empty tenant"):
        run_normal_month(session, tenant_id)
    assert session.scalar(select(Item.id).where(Item.tenant_id == tenant_id)) is None


def test_normal_month_refuses_an_unrelated_company_partner(session):
    tenant = create_tenant(session, "Existing business")
    create_party(session, tenant.id, "Existing business", "company")
    with pytest.raises(InvalidOperation, match="requires an empty tenant"):
        run_normal_month(session, tenant.id)
    assert session.scalar(select(Item.id).where(Item.tenant_id == tenant.id)) is None


def test_normal_month_is_complete_deterministic_and_safe_to_rerun(session):
    tenant = create_tenant(session, "September 2026 Demo")

    first = run_normal_month(session, tenant.id)
    counts = {
        model.__tablename__: session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant.id)
        )
        for model in [Party, Item, Commitment, Movement, ChangeProposal]
    }
    second = run_normal_month(session, tenant.id)
    repeated_counts = {
        model.__tablename__: session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant.id)
        )
        for model in [Party, Item, Commitment, Movement, ChangeProposal]
    }

    assert first == second
    assert counts == repeated_counts
    assert first["physical"] == Decimal("6.0000")
    assert first["reserved"] == 0
    assert first["receivable"] == Decimal("870.0000")
    assert counts["party"] == 6
    assert counts["item"] == 5
    assert (
        session.scalar(
            select(func.count())
            .select_from(ChangeProposal)
            .where(
                ChangeProposal.tenant_id == tenant.id,
                ChangeProposal.type == SCENARIO_ACTION,
            )
        )
        == 1
    )


def test_the_month_ends_with_exactly_these_exceptions(session):
    """Pin what a full ERP month leaves in the queue.

    The month is meant to end with these standing. A demo that reconciles to
    nothing shows an ERP where nothing ever goes wrong, which is not the product
    being demonstrated: the queue is where a month's loose ends become visible.
    Do not resolve these by making the demo tidier.

    Nothing asserted this before, so a new exception class could change what the
    demo shows and no gate would notice. Every entry below is named with the act
    that produces it: a change here is a change to the story, and this test
    forces someone to argue it rather than make it in passing.
    """
    tenant = create_tenant(session, "September 2026 Queue")
    run_normal_month(session, tenant.id)

    as_of = datetime(2026, 9, 22, tzinfo=UTC)
    rows = operational_exceptions(session, tenant.id, as_of=as_of)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.class_id] = counts.get(row.class_id, 0) + 1

    def explain() -> str:
        # This test failed in CI on 2026-09-23 between 06:27 and 08:30 UTC with two
        # extra overdue items and never reproduced locally, not even with the same
        # shard, workers and a faked clock. Should it recur, the failure now names
        # what was derived instead of leaving only the counts behind.
        aging = [
            {
                "type": item["document"].type,
                "document_date": str(item["document"].document_date),
                "due_date": str(item["due_date"]),
                "term_days": getattr(item["payment_term"], "due_days", None),
                "status": item["status"],
                "open": str(item["open"]),
            }
            for item in aging_register(session, tenant.id, as_of=as_of)
        ]
        findings = [
            {"class": row.class_id, "impact": row.impact, "values": row.causal_values}
            for row in rows
        ]
        return (
            f"wall clock {datetime.now(UTC).isoformat()}, as_of {as_of.isoformat()}\n"
            f"findings {findings}\naging {aging}"
        )

    assert counts == {
        # Both Shopify orders ship in full against their commitments, and the
        # month's only sales invoice is a header with no lines, so no invoice
        # line bills either order line. Reality is right to say so.
        "shipped_not_billed": 2,
        # Two units come back into the Returns Area on day 18. The write path
        # refuses to link a return to the delivery it reverses, so the movement
        # can only be recorded orphaned — which is what this class reports.
        "unexplained_movement": 1,
    }, explain()


def test_normal_month_runs_on_a_freshly_set_up_business_company(
    session, scheduled_owner
):
    tenant_id = company_setup.create_company(
        session,
        scheduled_owner.id,
        "normal-month-after-setup",
        "Lampenhaus Berg GmbH",
        "business",
        "empty",
        confirmed=True,
    )["tenant_id"]

    result = run_normal_month(session, tenant_id)

    assert result["physical"] > 0


def test_normal_month_refuses_a_business_company_with_another_party(
    session, scheduled_owner
):
    tenant_id = company_setup.create_company(
        session,
        scheduled_owner.id,
        "normal-month-other-party",
        "Lampenhaus Berg GmbH",
        "business",
        "empty",
        confirmed=True,
    )["tenant_id"]
    create_party(session, tenant_id, "Existing Customer GmbH", "customer")

    with pytest.raises(InvalidOperation, match="requires an empty tenant"):
        run_normal_month(session, tenant_id)
