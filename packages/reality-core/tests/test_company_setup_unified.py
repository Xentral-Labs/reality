from conftest import seed_company

from reality.services import company_setup, demo_profile


def test_unified_baseline_uses_current_domain_services(
    session, scheduled_owner, monkeypatch
):
    seed = demo_profile.seed_profile
    errors = []

    def observed(*args, **kwargs):
        try:
            return seed(*args, **kwargs)
        except Exception:
            import traceback

            errors.append(traceback.format_exc())
            raise

    monkeypatch.setattr(demo_profile, "seed_profile", observed)
    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "unified-profile",
        "Unified Demo",
        "sandbox",
        "international_demo",
        live_simulation=True,
        confirmed=True,
    )
    assert result["status"] == "initializing"
    assert seed_company(session, result["tenant_id"]) == "succeeded"
    assert not errors, "\n".join(errors)
    ready = company_setup.read_request(session, scheduled_owner.id, "unified-profile")
    assert ready["status"] == "ready"
    assert ready["destination"].startswith("/app?")

    # Spec146 FR-030: the real demo must support the same exception investigation.
    from reality.services.attention_reads import attention_detail, attention_register
    from reality.services.exceptions import operational_exception_rows
    from reality.services.projections import EXCEPTIONS, rebuild_projections

    # Spec180: a company nobody has calculated yet is awaiting its first generation,
    # not empty; the worker publishes it, and only then does the register list rows.
    awaiting = attention_register(session, result["tenant_id"])
    assert awaiting["items"] == []
    assert awaiting["metadata"]["state"] == "uninitialized"
    rebuild_projections(session, result["tenant_id"], [EXCEPTIONS], force=True)
    session.flush()
    findings = attention_register(session, result["tenant_id"])
    assert findings["items"]
    assert findings["metadata"]["state"] == "ready"
    assert findings["page"]["total"] == len(
        operational_exception_rows(session, result["tenant_id"])
    )
    detail = attention_detail(session, result["tenant_id"], findings["items"][0]["id"])
    assert detail["id"] == findings["items"][0]["id"]
    assert detail["guidance"]

    labels = company_setup._company_presentation(
        session, scheduled_owner.id, [result["tenant_id"]]
    )
    assert labels[result["tenant_id"]] == {
        "company_kind": "demo",
        "demo_data_state": "running",
    }
    assert (
        company_setup._company_presentation(
            session, "foreign-user", [result["tenant_id"]]
        )
        == {}
    )
    from reality.services import demo_data

    current = demo_data.status(session, result["tenant_id"], scheduled_owner.id)
    demo_data.control(
        session,
        result["tenant_id"],
        scheduled_owner.id,
        "pause",
        current["revision"],
        "card-pause",
        confirmed=True,
    )
    assert (
        company_setup._company_presentation(
            session, scheduled_owner.id, [result["tenant_id"]]
        )[result["tenant_id"]]["demo_data_state"]
        == "paused"
    )


def test_sandbox_reports_readable_without_mutation_authority(
    session, scheduled_owner, monkeypatch
):
    import pytest
    from sqlalchemy import event

    from reality.services.core import InvalidOperation
    from reality.services.reference_workspace import require_ordinary_workspace
    from reality.tools.application import run_read_tool

    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "read-reports",
        "Reports Sandbox",
        "sandbox",
        "empty",
        confirmed=True,
    )

    def deny_commit(*args):
        pytest.fail("Analytics committed during read")

    event.listen(session, "before_commit", deny_commit)
    try:
        catalog = run_read_tool(session, result["tenant_id"], "graph.catalog", {})
        assert catalog["nodes"]
    finally:
        event.remove(session, "before_commit", deny_commit)
    with pytest.raises(InvalidOperation):
        require_ordinary_workspace(session, result["tenant_id"])
