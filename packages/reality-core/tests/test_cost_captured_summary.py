"""Captured diagnostics reuse canonical SQL amounts without claiming company totals."""

import pytest
import test_cost_captured_basis_storage as storage
import test_cost_review_relevance as relevance
from sqlalchemy import event, select
from test_cost_census import read_session

from reality.db.cost_census import CostCompanyCensus
from reality.services import core, costing

scheduled_database = storage.scheduled_database


def sale(
    identity, revenue="100", goods="60", selling="10", *, currency="EUR", unit="piece"
):
    return {
        "document_line_id": identity,
        "review_id": "review-" + identity,
        "state": "available_at_capture",
        "gaps": [],
        "result": {
            "profile": "commercial_v1",
            "currency": currency,
            "base_unit": unit,
            "direct_selling_cost": selling,
            "allocated_selling_cost": "0" if selling is not None else None,
            "trace": {
                "received_net": revenue,
                "quantity": "1",
                "consumption": {"cost": goods},
            },
        },
    }


def stock(
    identity,
    amount="420",
    *,
    currency="EUR",
    unit="piece",
    owner="owner",
    method="fifo",
):
    return {
        "item_id": identity,
        "review_id": "review-" + identity,
        "state": "available_at_capture",
        "gaps": [],
        "result": {
            "currency": currency,
            "base_unit": unit,
            "owner_party_id": owner,
            "method": method,
            "remaining_quantity": "40",
            "acquisition_value": amount,
            "carrying_value": None,
        },
    }


def grouped(session, inventory=(), contribution=()):
    from reality.services.cost_captured_summary import _groups

    return _groups(session, list(inventory), list(contribution))


def test_missing_goods_never_subtracts_partial_cost_from_full_revenue(session):
    result = grouped(session, contribution=[sale("a"), sale("b", goods=None)])
    group = result["contribution"][0]
    assert group["revenue"]["known"] == "200.0000"
    assert group["goods_cost"]["known"] == "60.0000"
    assert group["db1"]["known"] == "40.0000"
    assert group["db2"]["known"] == "30.0000"
    assert group["db1"]["covered"] == group["db2"]["covered"] == 1
    assert group["db1"]["required"] == 2
    assert group["db1"]["total"] is group["db2"]["total"] is None
    assert group["db1_rate"] is group["db2_rate"] is None


def test_missing_selling_preserves_db1_and_zero_counts_as_known(session):
    group = grouped(
        session,
        contribution=[
            sale("a"),
            sale("b", selling=None),
            sale("zero", revenue="0", goods="0", selling="0"),
        ],
    )["contribution"][0]
    assert group["db1"]["known"] == "80.0000"
    assert group["db1"]["covered"] == 3
    assert group["db2"]["known"] == "30.0000"
    assert group["db2"]["covered"] == 2
    assert group["db1"]["total"] is None
    assert len(group["members"]) == 3


def test_partitions_and_exact_decimal_sums(session):
    inventories = [
        stock("a", "99999999999999.9999"),
        stock("b", "0.0001"),
        stock("c", currency="USD"),
        stock("d", unit="kg"),
        stock("e", owner="other"),
        stock("f", method="weighted_average"),
    ]
    sales = [sale("a"), sale("b", currency="USD"), sale("c", unit="kg")]
    groups = grouped(session, inventories, sales)
    assert len(groups["inventory"]) == 5
    assert len(groups["contribution"]) == 3
    biggest = next(row for row in groups["inventory"] if len(row["members"]) == 2)
    assert biggest["acquisition"]["known"] == "100000000000000.0000"
    assert biggest["remaining_quantity"]["known"] == "80.0000"
    assert biggest["carrying"]["known"] == "0.0000"
    assert biggest["carrying"]["covered"] == 0
    assert biggest["carrying"]["total"] is None
    assert grouped(session, reversed(inventories), reversed(sales)) == groups


def test_empty_unknown_and_historical_rows_never_enter_subtotals(session):
    assert grouped(session) == {"inventory": [], "contribution": []}
    old = stock("old")
    old["basis_result"] = old["result"]
    old.update(result=None, state="unknown_at_capture", gaps=["changed"])
    missing = sale("missing")
    missing.update(result=None, state="unknown_at_capture", gaps=["not_reviewed"])
    assert grouped(session, [old], [missing]) == {"inventory": [], "contribution": []}


def test_real_single_basis_summary_and_tenant_boundary(scheduled_database):
    factory, tenant, _, basis = storage.retained(scheduled_database)
    with read_session(factory) as session:
        result = costing.captured_cost_summary(session, tenant, basis["basis_id"])
    assert result["basis"] == basis
    assert result["inventory_groups"][0]["acquisition"]["known"] == "420.0000"
    assert result["contribution_groups"][0]["db1"]["known"] == "570.0000"
    assert result["contribution_groups"][0]["db2"]["covered"] == 0
    assert result["publication_eligible"] is False
    assert result["state"] == "captured_known_subtotals"
    with factory() as session:
        other = core.create_tenant(session, "Other").id
        session.commit()
    with read_session(factory) as session, pytest.raises(core.NotFound):
        costing.captured_cost_summary(session, other, basis["basis_id"])


def test_joint_basis_has_known_db2_subset_and_stable_capture(scheduled_database):
    relevance.test_joint_inventory_and_contribution_reviews_coexist(scheduled_database)
    _, factory, _, _ = scheduled_database
    with factory() as session:
        census, tenant = session.execute(
            select(CostCompanyCensus.id, CostCompanyCensus.tenant_id)
        ).one()
    with read_session(factory) as session:
        basis = costing.retain_captured_cost_basis(
            session, tenant, census, request_id="summary"
        )
        session.commit()
    with read_session(factory) as session:
        before = costing.captured_cost_summary(session, tenant, basis["basis_id"])
    # This joint review deliberately contains different base units.
    assert len(before["contribution_groups"]) == len(before["inventory_groups"]) == 2
    assert all(
        group["db1"]["known"] == "570.0000" for group in before["contribution_groups"]
    )
    assert {group["db2"]["known"] for group in before["contribution_groups"]} == {
        "570.0000",
        "0.0000",
    }
    assert {group["db2"]["covered"] for group in before["contribution_groups"]} == {
        0,
        1,
    }
    assert all(group["db2"]["required"] == 1 for group in before["contribution_groups"])
    assert all(
        group["acquisition"]["known"] == "420.0000"
        for group in before["inventory_groups"]
    )
    with factory() as session:
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    with read_session(factory) as session:
        assert (
            costing.captured_cost_summary(session, tenant, basis["basis_id"]) == before
        )


@pytest.mark.parametrize("reviewed", [False, True])
def test_population_keeps_gaps_and_is_select_only(
    scheduled_database, monkeypatch, reviewed
):
    factory, tenant, _, basis = storage.retained(scheduled_database, reviewed=reviewed)
    statements = []
    with read_session(factory) as session:

        def forbidden(*args, **kwargs):
            raise AssertionError("A summary may not flush")

        monkeypatch.setattr(session, "flush", forbidden)
        connection = session.connection()

        def record(conn, cursor, statement, *args):
            statements.append(statement)

        event.listen(connection, "before_cursor_execute", record)
        try:
            result = costing.captured_cost_summary(session, tenant, basis["basis_id"])
        finally:
            event.remove(connection, "before_cursor_execute", record)
    if reviewed:
        assert result["inventory_groups"] and result["contribution_groups"]
        assert any("verified_captured_inventory" in sql for sql in statements)
        assert any("verified_captured_contribution" in sql for sql in statements)
    else:
        assert result["inventory_groups"] == result["contribution_groups"] == []
        assert (
            len(result["unavailable"]["inventory"])
            == len(result["unavailable"]["contribution"])
            == 1
        )
        assert (
            result["basis"]["gaps"]["documents"] and result["basis"]["gaps"]["sources"]
        )
    assert all(sql.lstrip().startswith("SELECT") for sql in statements)


def test_invalid_membership_and_unsupported_profile_are_refused(session):
    with pytest.raises(core.InvalidOperation, match="limit"):
        grouped(session, [stock(str(index)) for index in range(11)])
    with pytest.raises(core.InvalidOperation, match="membership"):
        grouped(session, contribution=[sale("duplicate"), sale("duplicate")])
    historical = stock("historical")
    historical["state"] = "unknown_at_capture"
    with pytest.raises(core.InvalidOperation, match="membership"):
        grouped(session, [historical])
    unsupported = sale("unsupported")
    unsupported["result"]["profile"] = "unrecognized"
    with pytest.raises(core.InvalidOperation, match="profile"):
        grouped(session, contribution=[unsupported])
