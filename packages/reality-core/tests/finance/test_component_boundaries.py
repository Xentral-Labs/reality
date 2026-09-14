"""Attribution adapter and database boundaries."""

import json
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from reality.db.components import ComponentAssignmentPart, FinancialComponent
from reality.services import core
from reality.services.finance import components
from tests.finance.test_components import fixture, prepare
from tests.finance.test_references import confirm


def test_line_assignment_uses_shortest_owner_and_kind_constraints(session, business):
    tenant = business.tenant.id
    doc, ids = fixture(session, business, lines=True)
    item = components.component_context(session, tenant, doc.id)["items"][0]
    receipt = confirm(
        session,
        tenant,
        prepare(
            session,
            tenant,
            doc,
            parts=[{"cost_center_reference_id": ids["A"], "amount": "600"}],
        ),
    )
    history = components.component_history(session, tenant, receipt["component_id"])
    assert history["document_id"] is None
    assert history["document_line_id"] == item["document_line_id"]
    assert history["items"][0]["unassigned"] == "400"
    assert (
        components.component_context(session, tenant, doc.id, offset=1)["items"] == []
    )
    another = core.create_document(
        session, tenant, "sales_invoice", "OTHER", business.customer.id, "1190"
    )
    with pytest.raises(core.NotFound):
        prepare(session, tenant, another, document_line_id=item["document_line_id"])
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            ComponentAssignmentPart(
                id=core.uid("part"),
                tenant_id=tenant,
                assignment_revision_id=receipt["id"],
                cost_center_reference_id=ids["DOMESTIC"],
                amount="1",
            )
        )
        session.flush()
    other = core.create_tenant(session, "Foreign component").id
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            FinancialComponent(
                id=core.uid("fc"),
                tenant_id=other,
                document_line_id=item["document_line_id"],
                currency="EUR",
            )
        )
        session.flush()
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            FinancialComponent(
                id=core.uid("fc"),
                tenant_id=tenant,
                document_id=doc.id,
                document_line_id=item["document_line_id"],
                currency="EUR",
            )
        )
        session.flush()


def test_component_cli_proposal_and_history_use_shared_services(
    scheduled_database, monkeypatch
):
    from typer.testing import CliRunner

    from reality.cli import app as cli_module

    _, factory, tenant, _ = scheduled_database
    with factory() as db:
        customer = core.create_party(db, tenant, "CLI customer", "customer")
        doc, _ = fixture(
            db, SimpleNamespace(tenant=SimpleNamespace(id=tenant), customer=customer)
        )
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    runner = CliRunner()
    result = runner.invoke(
        cli_module.app, ["finance-components", doc.id, "--tenant-id", tenant]
    )
    assert result.exit_code == 0, result.output
    context = json.loads(result.output)
    arguments = {
        "document_id": doc.id,
        "basis": "net",
        "parts": [],
        "reason": "CLI classification",
        "expected_revision": context["revision"],
        "expected_evidence_hash": context["items"][0]["evidence_hash"],
    }
    result = runner.invoke(
        cli_module.app,
        ["finance-component-propose", json.dumps(arguments), "--tenant-id", tenant],
    )
    assert result.exit_code == 0, result.output
    proposal = json.loads(result.output)
    from reality.tools.application import approve_and_execute_proposal

    with factory() as db:
        assert (
            components.component_context(db, tenant, doc.id)["items"][0]["component_id"]
            is None
        )
        receipt = json.loads(
            approve_and_execute_proposal(db, tenant, proposal["id"]).output
        )
    result = runner.invoke(
        cli_module.app,
        ["finance-component-history", receipt["component_id"], "--tenant-id", tenant],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["items"][0]["reason"] == "CLI classification"
