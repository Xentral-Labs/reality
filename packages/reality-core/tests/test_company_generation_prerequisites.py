"""Published company generations are explicit cost-finding prerequisites only."""

import test_company_generation_jobs as jobs
from sqlalchemy import event

from reality.services import attention_reads, core, costing, projections

company_database = jobs.company_database


def test_cost_basis_unavailable_ready_pending_and_identity_preserved(company_database):
    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        assert (
            projections.cost_finding_prerequisite(session, tenant)["state"]
            == "unavailable"
        )
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        costing.publish_company_cost_generation(
            session, tenant, built["generation_id"], previous_generation_id=None
        )
        session.commit()
    with factory() as session:
        ready = projections.cost_finding_prerequisite(session, tenant)
        assert ready["state"] == "ready"
        assert ready["generation_id"] == built["generation_id"]
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    with factory() as session:
        pending = projections.cost_finding_prerequisite(session, tenant)
        assert pending["state"] == "pending"
        assert pending["generation_id"] == ready["generation_id"]
        assert pending["processed_event_sequence"] < pending["target_event_sequence"]


def test_attention_metadata_binds_basis_without_activating_cost_findings(
    company_database, monkeypatch
):
    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        costing.publish_company_cost_generation(
            session, tenant, built["generation_id"], previous_generation_id=None
        )
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
        summary = attention_reads.attention_summary(session, tenant)
        register = attention_reads.attention_register(session, tenant)
    assert summary["metadata"]["cost_basis"]["generation_id"] == built["generation_id"]
    assert register["metadata"]["cost_basis"] == summary["metadata"]["cost_basis"]
    assert not any(row["class_id"].startswith("cost_") for row in register["items"])
    assert statements and all(sql.lstrip().startswith("SELECT") for sql in statements)


def test_cost_findings_share_projection_page_count_register_and_detail(
    company_database,
):
    factory, tenant, manifest = jobs._manifest(company_database, reviewed=False)
    with factory() as session:
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        costing.publish_company_cost_generation(
            session, tenant, built["generation_id"], previous_generation_id=None
        )
        session.commit()
    with factory() as session:
        projections.refresh_projection(session, tenant, projections.EXCEPTIONS)
    with factory() as session:
        summary = attention_reads.attention_summary(session, tenant)
        register = attention_reads.attention_register(
            session, tenant, class_id="missing_acquisition_cost"
        )
        count = next(
            row["open"]
            for row in summary["classes"]
            if row["class_id"] == "missing_acquisition_cost"
        )
        assert count == register["page"]["total"] == len(register["items"]) == 2
        assert all(
            row["trace"]["generation_id"] == built["generation_id"]
            for row in register["items"]
        )
        detail = attention_reads.attention_detail(
            session, tenant, register["items"][0]["id"]
        )
        assert detail["class_id"] == "missing_acquisition_cost"
        assert detail["trace"]["manifest_id"] == manifest["id"]


def test_pending_cost_basis_preserves_projected_findings(company_database):
    factory, tenant, manifest = jobs._manifest(company_database, reviewed=False)
    with factory() as session:
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        costing.publish_company_cost_generation(
            session, tenant, built["generation_id"], previous_generation_id=None
        )
        session.commit()
    with factory() as session:
        projections.refresh_projection(session, tenant, projections.EXCEPTIONS)
    with factory() as session:
        before = attention_reads.attention_register(
            session, tenant, class_id="missing_acquisition_cost"
        )
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    with factory() as session:
        projections.refresh_projection(session, tenant, projections.EXCEPTIONS)
    with factory() as session:
        after = attention_reads.attention_register(
            session, tenant, class_id="missing_acquisition_cost"
        )
    assert [row["id"] for row in after["items"]] == [
        row["id"] for row in before["items"]
    ]
    assert all(row["trace"]["cost_basis_state"] == "pending" for row in after["items"])
