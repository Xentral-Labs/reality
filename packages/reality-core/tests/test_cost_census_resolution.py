"""Captured review resolution never borrows approval from the future."""

from datetime import datetime, timedelta

import conftest as base_fixtures
import pytest
import test_contribution_reviews as commercial
import test_cost_census_storage as storage
import test_costing_services as costs
import test_inventory_costing_services as stock
from test_cost_census import read_session, seed

from reality.services import core, costing

scheduled_database = storage.scheduled_database


def capture(factory, tenant, cutoff, request="capture"):
    with read_session(factory) as session:
        result = costing.retain_company_cost_census(
            session, tenant, cutoff, request_id=request
        )
        session.commit()
        return result["id"]


def setup_review(database, *, contribution=False):
    _, factory, _, _ = database
    with factory() as session:
        business = base_fixtures.business.__wrapped__(session)
        owner = costs.cost_owner.__wrapped__(session, business)
        if contribution:
            args, _ = commercial.prepared(session, business, owner)
            _, result = stock.commit_review(session, business, owner, args)
            from reality.db.inventory_costing import CostInventoryReview

            review = session.get(
                CostInventoryReview, result["trace"]["inventory_review_id"]
            )
            cutoff = review.effective_at
        else:
            args, *_ = stock.prepared(session, business, owner)
            _, result = stock.commit_review(session, business, owner, args)
            cutoff = datetime.fromisoformat(args["effective_at"])
        session.commit()
        return factory, business, owner, cutoff, result


def test_all_unreviewed_subjects_and_gaps_remain(scheduled_database):
    data = seed(scheduled_database)
    factory, tenant, *_ = data
    held = storage.retain(data)
    with read_session(factory) as session:
        result = costing.resolve_company_cost_census(session, tenant, held["id"])
        assert len(result["inventory"]) == len(result["contribution"]) == 1
        assert result["inventory"][0]["result"] is None
        assert result["contribution"][0]["result"] is None
        assert result["inventory"][0]["gaps"] == ["inventory_scope_not_reviewed"]
        assert result["document_gaps"] and result["source_gaps"]
        assert result["publication_eligible"] is False
        assert "knowledge_at" not in result


def test_compatible_inventory_uses_canonical_review_and_preserves_carrying_gap(
    scheduled_database,
):
    factory, business, _, cutoff, review = setup_review(scheduled_database)
    identity = capture(factory, business.tenant.id, cutoff)
    with read_session(factory) as session:
        result = costing.resolve_company_cost_census(
            session, business.tenant.id, identity
        )
    row = result["inventory"][0]
    assert row["review_id"] == review["review_id"]
    assert row["result"]["acquisition_value"] == "420.0000"
    assert row["result"]["carrying_value"] is None
    assert row["state"] == "available_at_capture"


def test_db1_is_not_suppressed_by_unknown_db2(scheduled_database):
    factory, business, _, cutoff, review = setup_review(
        scheduled_database, contribution=True
    )
    identity = capture(factory, business.tenant.id, cutoff)
    with read_session(factory) as session:
        result = costing.resolve_company_cost_census(
            session, business.tenant.id, identity
        )
    row = result["contribution"][0]
    assert row["review_id"] == review["review_id"]
    assert row["result"]["db1"] == "570.0000"
    assert row["result"]["db2"] is None
    assert "selling_costs_unknown" in row["result"]["missing_basis"]


def test_later_live_events_do_not_change_old_captured_answer(scheduled_database):
    factory, business, _, cutoff, _ = setup_review(scheduled_database)
    tenant = business.tenant.id
    old = capture(factory, tenant, cutoff)
    with factory() as session:
        core.create_item(session, tenant, "NEW", "Later item")
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    new = capture(factory, tenant, cutoff, "later")
    with read_session(factory) as session:
        before = costing.resolve_company_cost_census(session, tenant, old)["inventory"][
            0
        ]
        after = costing.resolve_company_cost_census(session, tenant, new)["inventory"][
            0
        ]
    assert before["result"]["acquisition_value"] == "420.0000"
    assert after["result"] is None
    assert after["basis_result"]["acquisition_value"] == "420.0000"
    assert "review_knowledge_changed_at_capture" in after["gaps"]


def test_different_cutoff_is_not_silently_valued(scheduled_database):
    factory, business, _, cutoff, _ = setup_review(scheduled_database)
    identity = capture(factory, business.tenant.id, cutoff + timedelta(seconds=1))
    with read_session(factory) as session:
        row = costing.resolve_company_cost_census(
            session, business.tenant.id, identity
        )["inventory"][0]
    assert row["result"] is None and row["basis_result"] is not None
    assert "inventory_cutoff_mismatch" in row["gaps"]


def test_foreign_and_bounds_refuse_before_valuation(scheduled_database, monkeypatch):
    data = seed(scheduled_database)
    factory, tenant, *_ = data
    held = storage.retain(data)
    with factory() as session:
        other = core.create_tenant(session, "Other").id
        session.commit()
    with read_session(factory) as session:
        with pytest.raises(core.NotFound):
            costing.resolve_company_cost_census(session, other, held["id"])

        def forbidden(*args, **kwargs):
            raise AssertionError("No valuation before bounds")

        monkeypatch.setattr(costing, "inventory_cost", forbidden)
        for limit in (0, 11, True, 1):
            with pytest.raises(core.InvalidOperation, match="subject limit"):
                costing.resolve_company_cost_census(
                    session, tenant, held["id"], max_subjects=limit
                )
    with (
        factory() as session,
        pytest.raises(core.InvalidOperation, match="REPEATABLE READ"),
    ):
        costing.resolve_company_cost_census(session, tenant, held["id"])


def test_later_review_is_not_borrowed_by_older_capture(scheduled_database):
    _, factory, _, _ = scheduled_database
    with factory() as session:
        business = base_fixtures.business.__wrapped__(session)
        owner = costs.cost_owner.__wrapped__(session, business)
        args, *_ = stock.prepared(session, business, owner)
        cutoff = datetime.fromisoformat(args["effective_at"])
        session.commit()
    before = capture(factory, business.tenant.id, cutoff, "before-review")
    with factory() as session:
        stock.commit_review(session, business, owner, args)
        session.commit()
    after = capture(factory, business.tenant.id, cutoff, "after-review")
    with read_session(factory) as session:
        old = costing.resolve_company_cost_census(session, business.tenant.id, before)[
            "inventory"
        ][0]
        new = costing.resolve_company_cost_census(session, business.tenant.id, after)[
            "inventory"
        ][0]
    assert old["review_id"] is None and old["basis_result"] is None
    assert new["result"]["acquisition_value"] == "420.0000"


def test_additional_movement_is_not_hidden_by_old_review(scheduled_database):
    factory, business, _, cutoff, _ = setup_review(scheduled_database)
    with factory() as session:
        core.record_movement(
            session,
            business.tenant.id,
            "receipt",
            business.item.id,
            "1",
            to_location_id=business.location.id,
            occurred_at=cutoff,
        )
        session.commit()
    identity = capture(factory, business.tenant.id, cutoff)
    with read_session(factory) as session:
        row = costing.resolve_company_cost_census(
            session, business.tenant.id, identity
        )["inventory"][0]
    assert row["result"] is None
    assert "inventory_movement_membership_mismatch" in row["gaps"]


def test_resolution_does_not_flush_write_or_call_current_readers(
    scheduled_database, monkeypatch
):
    from sqlalchemy import event

    factory, business, _, cutoff, _ = setup_review(scheduled_database)
    identity = capture(factory, business.tenant.id, cutoff)
    statements = []

    def forbidden(*args, **kwargs):
        raise AssertionError("Resolution may not flush")

    with read_session(factory) as session:
        monkeypatch.setattr(session, "flush", forbidden)
        connection = session.connection()

        def track(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(connection, "before_cursor_execute", track)
        try:
            result = costing.resolve_company_cost_census(
                session, business.tenant.id, identity
            )
        finally:
            event.remove(connection, "before_cursor_execute", track)
    assert result["inventory"][0]["result"]["acquisition_value"] == "420.0000"
    assert statements and all(
        statement.lstrip().startswith("SELECT") for statement in statements
    )


def test_confirmed_db2_uses_existing_selling_cost_proof(scheduled_database):
    import test_selling_costs as selling

    from reality.db.inventory_costing import CostInventoryReview

    _, factory, _, _ = scheduled_database
    with factory() as session:
        business = base_fixtures.business.__wrapped__(session)
        owner = costs.cost_owner.__wrapped__(session, business)
        args, data = commercial.prepared(session, business, owner)
        doc = costs.evidence(session, business, "114", "0")
        assignment = selling.selling(session, business, data[0], doc)
        assignment["parts"] = [
            assignment["parts"][0] | {"source_share": "90"},
            assignment["parts"][0]
            | {
                "source_share": "24",
                "category": "payment_fee",
                "assignment_kind": "allocated",
            },
        ]
        stock.commit_review(session, business, owner, assignment)
        args = selling.refresh(
            session,
            business,
            owner,
            args,
            data,
            selling.categories("outbound_freight", "payment_fee"),
        )
        _, result = stock.commit_review(session, business, owner, args)
        cutoff = session.get(
            CostInventoryReview, result["trace"]["inventory_review_id"]
        ).effective_at
        session.commit()
    identity = capture(factory, business.tenant.id, cutoff)
    with read_session(factory) as session:
        captured = costing.resolve_company_cost_census(
            session, business.tenant.id, identity
        )
        row = captured["contribution"][0]
    coverage = captured["captured_basis"]["coverage"]
    assert coverage["acquisition"]["covered"] == 1
    assert coverage["carrying"]["covered"] == 0
    assert coverage["db1"]["covered"] == coverage["db2"]["covered"] == 1
    assert row["result"]["db1"] == "570.0000"
    assert row["result"]["db2"] == "456.0000"
    assert row["result"]["db2_rate"] == "38.0000"


def test_economic_activity_after_cutoff_is_not_invented_as_current(scheduled_database):
    factory, business, _, _, reviewed = setup_review(
        scheduled_database, contribution=True
    )
    cutoff = datetime.fromisoformat(reviewed["economic_at"]) - timedelta(microseconds=1)
    identity = capture(factory, business.tenant.id, cutoff)
    with read_session(factory) as session:
        row = costing.resolve_company_cost_census(
            session, business.tenant.id, identity
        )["contribution"][0]
    assert row["result"] is None and row["basis_result"]["db1"] == "570.0000"
    assert "economic_activity_after_capture_cutoff" in row["gaps"]
