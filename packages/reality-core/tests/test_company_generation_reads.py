"""Fixed company-generation pages and totals never enqueue work."""

import base64
import json

import pytest
import test_company_generation_jobs as jobs
from sqlalchemy import event

from reality.domain.cost_query import compatible_contexts
from reality.services import core, costing

company_database = jobs.company_database


def test_one_generation_pages_totals_and_no_read_side_enqueue(
    company_database, monkeypatch
):
    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        session.commit()
    statements = []
    with factory() as session:
        monkeypatch.setattr(
            session,
            "flush",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("read flushed")
            ),
        )
        connection = session.connection()
        event.listen(
            connection,
            "before_cursor_execute",
            lambda conn, cursor, statement, *args: statements.append(statement),
        )
        report = costing.company_cost_generation_report(
            session, tenant, built["generation_id"], page_size=1
        )
    assert report["generation_id"] == built["generation_id"]
    assert (
        report["inventory"]["total"] == report["coverage"]["inventory"]["expected"] == 1
    )
    assert (
        report["contribution"]["total"]
        == report["coverage"]["contribution"]["expected"]
        == 1
    )
    assert report["totals"]["acquisition_value"] == "420.0000"
    assert report["totals"]["db1"] == "570.0000"
    assert report["requested"] == {
        "kind": "company",
        "generation_id": built["generation_id"],
        "freshness": "allow_previous",
    }
    assert report["resolved"]["basis_kind"] == "financial_company_generation"
    assert report["resolved"]["generation_id"] == built["generation_id"]
    assert report["resolved"]["manifest_id"] == manifest["id"]
    assert report["resolved"]["policy_revision_id"] is None
    assert report["resolved"]["profile_revision_id"] is None
    assert report["resolved"]["authority_scope"] == "independent_member_reviews"
    assert report["freshness_context"]["state"] == "ready"
    assert len(report["context_id"]) == 64
    assert compatible_contexts(report, report)
    assert report["inventory"]["next_cursor"] is None
    assert report["contribution"]["next_cursor"] is None
    assert sum(" limit " in sql.lower() for sql in statements) >= 2
    assert statements and all(sql.lstrip().startswith("SELECT") for sql in statements)


def test_company_context_is_stable_but_never_compatible_with_single_scope(
    company_database,
):
    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        first = costing.company_cost_generation_report(
            session, tenant, built["generation_id"]
        )
        second = costing.company_cost_generation_report(
            session, tenant, built["generation_id"]
        )

    assert compatible_contexts(first, second)
    assert not compatible_contexts(
        first,
        {
            "context_id": first["context_id"],
            "resolved": {**first["resolved"], "basis_kind": "retained_scope_review"},
        },
    )


def test_company_page_cursor_is_generation_and_family_bound(company_database):
    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        session.commit()

    def cursor(generation, family, after):
        return base64.urlsafe_b64encode(
            json.dumps([generation, family, after], separators=(",", ":")).encode()
        ).decode()

    with factory() as session:
        after_end = costing.company_cost_generation_report(
            session,
            tenant,
            built["generation_id"],
            inventory_cursor=cursor(
                built["generation_id"], "inventory", "zzzz-after-end"
            ),
        )
        assert after_end["inventory"]["rows"] == []
        assert after_end["inventory"]["total"] == 1
        with pytest.raises(core.InvalidOperation, match="cursor"):
            costing.company_cost_generation_report(
                session,
                tenant,
                built["generation_id"],
                inventory_cursor=cursor("other-generation", "inventory", "input"),
            )
        with pytest.raises(core.InvalidOperation, match="cursor"):
            costing.company_cost_generation_report(
                session,
                tenant,
                built["generation_id"],
                inventory_cursor=cursor(
                    built["generation_id"], "contribution", "input"
                ),
            )
