"""Only proved contribution-only decisions can cross an unchanged-input interval."""

import json

import pytest
import test_cost_census_resolution as resolution
from conftest import record_by_id
from sqlalchemy import select, update
from test_cost_census import read_session

from reality.db.contribution import CostContributionReview
from reality.db.core import BusinessEvent, ChangeProposal
from reality.db.inventory_costing import CostInventoryReview
from reality.services import core, costing

scheduled_database = resolution.scheduled_database


def prepared(database):
    factory, business, _, cutoff, result = resolution.setup_review(
        database, contribution=True
    )
    with factory() as session:
        inventory = record_by_id(
            session, CostInventoryReview, result["trace"]["inventory_review_id"]
        )
        contribution = record_by_id(
            session, CostContributionReview, result["review_id"]
        )
        return (
            factory,
            business.tenant.id,
            cutoff,
            inventory.target_event_sequence,
            contribution.event_sequence,
            contribution.introduced_event_id,
            contribution.action_id,
            result["document_line_id"],
        )


def test_normal_db_confirmation_preserves_both_stock_and_db(scheduled_database):
    factory, tenant, cutoff, *_ = prepared(scheduled_database)
    census = resolution.capture(factory, tenant, cutoff)
    with read_session(factory) as session:
        result = costing.resolve_company_cost_census(session, tenant, census)
    assert result["inventory"][0]["result"]["acquisition_value"] == "420.0000"
    assert result["contribution"][0]["result"]["db1"] == "570.0000"
    assert result["inventory"][0]["freshness_proof"]["checked_review_event_ids"]
    assert result["publication_eligible"] is False


def test_same_line_is_not_exempt_and_other_line_is_disjoint(scheduled_database):
    from reality.services.cost_review_relevance import _unchanged

    factory, tenant, _, before, after, event_id, _, line = prepared(scheduled_database)
    with read_session(factory) as session:
        assert not _unchanged(session, tenant, before, after, document_line_id=line)[
            "unchanged"
        ]
        proof = _unchanged(
            session, tenant, before, after, document_line_id="different-line"
        )
        assert proof["unchanged"] and proof["checked_review_event_ids"] == [event_id]


@pytest.mark.parametrize(
    "fault",
    [
        "unconfirmed",
        "wrong_operation",
        "event_payload",
        "missing_reviews",
        "wrong_sequence",
        "wrong_target",
        "extra_review",
    ],
)
def test_labels_alone_do_not_prove_non_invalidation(scheduled_database, fault):
    from reality.services.cost_review_relevance import _unchanged

    factory, tenant, _, before, after, event_id, action_id, _ = prepared(
        scheduled_database
    )
    with factory() as session:
        if fault == "unconfirmed":
            session.execute(
                update(ChangeProposal)
                .where(ChangeProposal.id == action_id)
                .values(decided_by_user_id=None)
            )
        elif fault == "wrong_operation":
            session.execute(
                update(ChangeProposal)
                .where(ChangeProposal.id == action_id)
                .values(input=json.dumps({"operation": "inventory_review"}))
            )
        elif fault == "event_payload":
            session.execute(
                update(BusinessEvent)
                .where(BusinessEvent.id == event_id)
                .values(
                    payload='{"operation":"contribution_review","extra":"unproven"}'
                )
            )
        elif fault == "missing_reviews":
            # Move the row's introducing event to an earlier valid event (fault injection).
            earlier = session.scalar(
                select(BusinessEvent.id).where(
                    BusinessEvent.tenant_id == tenant, BusinessEvent.sequence == before
                )
            )
            session.execute(
                update(CostContributionReview)
                .where(CostContributionReview.action_id == action_id)
                .values(introduced_event_id=earlier)
            )
        elif fault == "wrong_target":
            action = record_by_id(session, ChangeProposal, action_id)
            arguments = json.loads(action.input)
            arguments["document_line_id"] = "different-target"
            action.input = json.dumps(arguments)
        elif fault == "extra_review":
            from sqlalchemy import insert

            table = CostContributionReview.__table__
            row = dict(
                session.execute(select(table).where(table.c.action_id == action_id))
                .mappings()
                .one()
            )
            row.update(
                id=core.uid("review"),
                revision=row["revision"] + 1,
                supersedes_id=row["id"],
            )
            session.execute(insert(table).values(**row))
        elif fault == "wrong_sequence":
            session.execute(
                update(CostContributionReview)
                .where(CostContributionReview.action_id == action_id)
                .values(event_sequence=before)
            )
        session.commit()
    with read_session(factory) as session:
        assert not _unchanged(session, tenant, before, after)["unchanged"]


def test_unknown_events_and_interval_overflow_remain_pending(scheduled_database):
    from reality.services.cost_review_relevance import _unchanged

    factory, tenant, _, before, after, *_ = prepared(scheduled_database)
    with factory() as session:
        event = core.emit_business_event(
            session, tenant, "cost.attributed", "tenant", tenant, {}
        )
        cursor = event.sequence
        session.commit()
    with read_session(factory) as session:
        assert not _unchanged(session, tenant, before, cursor)["unchanged"]
        assert not _unchanged(session, tenant, before, before + 101)["unchanged"]
        assert not _unchanged(session, "missing", before, after)["unchanged"]
        assert _unchanged(session, tenant, after, after)["unchanged"]


def test_joint_inventory_and_contribution_reviews_coexist(scheduled_database):
    import conftest as fixtures
    import test_contribution_batch_review as batch
    import test_costing_services as costs
    import test_inventory_costing_services as stock

    _, factory, _, _ = scheduled_database
    with factory() as session:
        business = fixtures.business.__wrapped__(session)
        owner = costs.cost_owner.__wrapped__(session, business)
        args, _, inventory_action = batch.prepared(session, business, owner)
        stock.commit_review(session, business, owner, args)
        cutoff = session.scalar(
            select(CostInventoryReview.effective_at)
            .where(
                CostInventoryReview.tenant_id == business.tenant.id,
                CostInventoryReview.action_id == inventory_action,
            )
            .limit(1)
        )
        session.commit()
    census = resolution.capture(factory, business.tenant.id, cutoff)
    with read_session(factory) as session:
        result = costing.resolve_company_cost_census(
            session, business.tenant.id, census
        )
    assert len(result["inventory"]) == len(result["contribution"]) == 2
    assert all(
        row["result"]["acquisition_value"] == "420.0000" for row in result["inventory"]
    )
    assert all(row["result"]["db1"] == "570.0000" for row in result["contribution"])
    assert {row["result"]["db2"] for row in result["contribution"]} == {
        "570.0000",
        None,
    }
    assert all(row["freshness_proof"]["unchanged"] for row in result["inventory"])


def test_missing_interval_event_cannot_be_treated_as_no_change(scheduled_database):
    from reality.services.cost_review_relevance import _unchanged

    factory, tenant, _, before, after, *_ = prepared(scheduled_database)
    with read_session(factory) as session:
        assert not _unchanged(session, tenant, before, after + 1)["unchanged"]


@pytest.mark.parametrize("after,through", [(True, 1), (0, "1"), (2, 1), (-1, 0)])
def test_invalid_intervals_refuse(scheduled_database, after, through):
    from reality.services.cost_review_relevance import _unchanged

    _, factory, tenant, _ = scheduled_database
    with (
        read_session(factory) as session,
        pytest.raises(core.InvalidOperation, match="interval"),
    ):
        _unchanged(session, tenant, after, through)


def test_an_event_cannot_name_another_company_s_action_at_all(scheduled_database):
    """The fault this used to stage is no longer possible to stage.

    A `foreign_action` case pointed a business event at another company's change
    proposal, so the relevance check could be shown to notice. Since spec 181
    FR-005 a reference between two company-scoped tables carries the company, and
    the database refuses the write instead — which is the stronger place for it,
    because no reader has to remember to look.
    """
    from sqlalchemy.exc import IntegrityError

    factory, _tenant, _, _, _, event_id, _, _ = prepared(scheduled_database)
    with factory() as session:
        other = core.create_tenant(session, "Other").id
        foreign = ChangeProposal(
            id=core.uid("act"), tenant_id=other, type="tool:cost.change", input="{}"
        )
        session.add(foreign)
        session.flush()
        with pytest.raises(IntegrityError):
            session.execute(
                update(BusinessEvent)
                .where(BusinessEvent.id == event_id)
                .values(action_id=foreign.id, subject_id=foreign.id)
            )
            session.flush()
