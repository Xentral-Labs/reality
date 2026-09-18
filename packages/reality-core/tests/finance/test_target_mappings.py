"""External destinations never become operational financial authority."""

import pytest
from sqlalchemy import func, select

from reality.db.core import LedgerEntry
from reality.services import core
from reality.services.finance.references import _revision
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from tests.finance.test_references import confirm
from tests.finance.test_references import propose as reference_proposal


def proposal(session, tenant, command, **values):
    return create_change_proposal(
        session,
        tenant,
        command,
        {
            "expected_revision": _revision(session, tenant),
            "reason": "Reviewed external configuration",
            **values,
        },
    )


def change(session, tenant, command, **values):
    return confirm(session, tenant, proposal(session, tenant, command, **values))


def setup(session, business):
    tenant = business.tenant.id
    target = change(
        session,
        tenant,
        "finance.target.create",
        namespace="accounting",
        name="Accounting",
    )
    account = change(
        session,
        tenant,
        "finance.target_reference.create",
        target_id=target["id"],
        kind="account",
        code="SALES",
        name="Sales destination",
    )
    case = confirm(
        session,
        tenant,
        reference_proposal(
            session, tenant, kind="case_code", code="DECLARED", name="Declared case"
        ),
    )
    return tenant, target, account, case


def rule(target, account, case, **extra):
    return {
        "target_id": target["id"],
        "mapping_kind": "case_routing",
        "transaction_kind": "sales_invoice",
        "case_reference_id": case["id"],
        "group_mode": "none",
        "external_account_id": account["id"],
        **extra,
    }


def test_target_mapping_confirmation_history_and_no_money(session, business):
    from reality.services.finance import target_mappings as service

    tenant, target, account, case = setup(session, business)
    pending = proposal(
        session, tenant, "finance.target_mapping.set", **rule(target, account, case)
    )
    assert service.list_mappings(session, tenant, target_id=target["id"])["total"] == 0
    first = confirm(session, tenant, pending)
    assert confirm(session, tenant, pending) == first
    blocked = change(
        session,
        tenant,
        "finance.target_mapping.set",
        **rule(target, account, case, state="blocked"),
    )
    assert blocked["revision"] == 2 and blocked["replaces_id"] == first["id"]
    history = service.mapping_history(session, tenant, mapping_id=first["id"])["items"]
    assert history[1]["state"] == "active" and not history[1]["is_current"]
    assert history[1]["configuration_snapshot"]["external_account"]["code"] == "SALES"
    assert (
        session.scalar(
            select(func.count())
            .select_from(LedgerEntry)
            .where(LedgerEntry.tenant_id == tenant)
        )
        == 0
    )


def test_target_boundaries_and_overlap(session, business):
    tenant, target, account, case = setup(session, business)
    other = change(
        session, tenant, "finance.target.create", namespace="other", name="Other"
    )
    with pytest.raises(core.InvalidOperation, match="target"):
        proposal(
            session, tenant, "finance.target_mapping.set", **rule(other, account, case)
        )
    group = confirm(
        session,
        tenant,
        reference_proposal(
            session, tenant, kind="coding_group", code="GOODS", name="Goods"
        ),
    )
    change(session, tenant, "finance.target_mapping.set", **rule(target, account, case))
    with pytest.raises(core.Conflict, match="overlap"):
        proposal(
            session,
            tenant,
            "finance.target_mapping.set",
            **rule(
                target,
                account,
                case,
                group_mode="exact",
                group_reference_id=group["id"],
            ),
        )
    foreign = core.create_tenant(session, "Other tenant").id
    with pytest.raises(core.NotFound):
        proposal(
            session,
            foreign,
            "finance.target_mapping.set",
            **rule(target, account, case),
        )


def test_target_reference_change_invalidates_pending_mapping(session, business):
    tenant, target, account, case = setup(session, business)
    pending = proposal(
        session, tenant, "finance.target_mapping.set", **rule(target, account, case)
    )
    change(
        session,
        tenant,
        "finance.target_reference.update",
        reference_id=account["id"],
        name="Retired sales",
        state="blocked",
    )
    with pytest.raises(core.Conflict, match="stale"):
        approve_and_execute_proposal(session, tenant, pending.id)


@pytest.mark.parametrize(
    "values",
    [
        {"group_mode": "exact"},
        {"group_reference_id": "unexpected"},
        {"transaction_kind": "payment"},
        {"local_account_id": "unexpected"},
    ],
)
def test_target_mapping_rejects_invalid_shapes(session, business, values):
    tenant, target, account, case = setup(session, business)
    with pytest.raises(core.InvalidOperation):
        proposal(
            session,
            tenant,
            "finance.target_mapping.set",
            **rule(target, account, case, **values),
        )


def test_real_component_resolution_is_read_only_and_does_not_infer(scheduled_database):
    from types import SimpleNamespace

    from reality.services.finance import components
    from reality.services.finance import target_mappings as service
    from tests.finance.test_components import fixture, prepare

    _, factory, tenant, _ = scheduled_database
    with factory() as db:
        customer = core.create_party(db, tenant, "Mapping customer", "customer")
        business = SimpleNamespace(tenant=SimpleNamespace(id=tenant), customer=customer)
        tenant, target, account, case = setup(db, business)
        doc, _ids = fixture(db, business, detail={"net": "1000", "tax": "190"})
        before = components.component_context(db, tenant, doc.id)
        db.commit()
        preview = service.preview_document(
            db, tenant, target_id=target["id"], document_id=doc.id
        )
        assert preview["items"][0]["status"] == "missing_case"
        confirm(db, tenant, prepare(db, tenant, doc, case_reference_id=case["id"]))
        first = change(
            db, tenant, "finance.target_mapping.set", **rule(target, account, case)
        )
        preview = service.preview_document(
            db, tenant, target_id=target["id"], document_id=doc.id
        )
        assert preview["items"][0]["status"] == "resolved"
        assert preview["items"][0]["mapping"]["id"] == first["id"]
        assert (
            preview["items"][0]["received"]["amounts"] == before["items"][0]["amounts"]
        )
        assert preview["scope"] == "mapping_resolution_only"
        assert preview["operational_legs"] == []
        # A separate credit note has its own evidence and assignment.
        credit = core.create_document(
            db, tenant, "credit_note", "CREDIT-SEPARATE", customer.id, "1190"
        )
        confirm(
            db,
            tenant,
            prepare(db, tenant, credit, basis="gross", case_reference_id=case["id"]),
        )
        assert (
            service.preview_document(
                db, tenant, target_id=target["id"], document_id=credit.id
            )["items"][0]["status"]
            == "missing_mapping"
        )
        change(
            db,
            tenant,
            "finance.target_reference.update",
            reference_id=account["id"],
            name="Blocked sales",
            state="blocked",
        )
        preview = service.preview_document(
            db, tenant, target_id=target["id"], document_id=doc.id
        )
        assert preview["items"][0]["status"] == "blocked_destination"
        assert (
            service.mapping_history(db, tenant, mapping_id=first["id"])["items"][0][
                "configuration_snapshot"
            ]["external_account"]["name"]
            == "Sales destination"
        )
        # Blocking remains possible after the referenced destination was blocked.
        change(
            db,
            tenant,
            "finance.target_mapping.set",
            **rule(target, account, case, state="blocked"),
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(LedgerEntry)
                .where(LedgerEntry.tenant_id == tenant)
            )
            == 0
        )


def test_exact_groups_source_conflicts_and_missing_tax(session, business):
    from reality.services.finance import components
    from reality.services.finance import target_mappings as service
    from tests.finance.test_components import fixture, prepare

    tenant, target, account, case = setup(session, business)
    doc, ids = fixture(session, business, detail={"net": "1000"})
    confirm(
        session, tenant, prepare(session, tenant, doc, case_reference_id=case["id"])
    )
    change(
        session,
        tenant,
        "finance.target_mapping.set",
        **rule(
            target, account, case, group_mode="exact", group_reference_id=ids["GOODS"]
        ),
    )

    def read():
        return service._preview_document(
            session, tenant, target["id"], doc.id, 50, 0, components.component_context
        )["items"][0]

    assert read()["status"] == "missing_group"
    confirm(
        session,
        tenant,
        prepare(
            session,
            tenant,
            doc,
            case_reference_id=case["id"],
            group_reference_id=ids["GOODS"],
        ),
    )
    assert (
        read()["status"] == "resolved" and read()["received"]["amounts"]["tax"] is None
    )
    # An explicit malformed source declaration is never overridden by internal assignment.
    item = components.component_context(session, tenant, doc.id)["items"][0]
    item["source_resolution"]["case"]["status"] = "conflict"
    assert service._classification(session, tenant, item, "case")[1] == "case_conflict"


def test_target_database_rejects_wrong_target_and_kind(session, business):
    from sqlalchemy.exc import IntegrityError

    from reality.db.target_mappings import TargetMapping

    tenant, target, account, case = setup(session, business)
    first = change(
        session, tenant, "finance.target_mapping.set", **rule(target, account, case)
    )
    other = change(
        session, tenant, "finance.target.create", namespace="other", name="Other"
    )
    row = session.get(TargetMapping, first["id"])
    with pytest.raises(IntegrityError), session.begin_nested():
        row.target_id = other["id"]
        session.flush()
    with pytest.raises(IntegrityError), session.begin_nested():
        row.case_kind = "coding_group"
        session.flush()


def test_target_activation_race_and_history(scheduled_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    from reality.services.finance import target_mappings as service

    _, factory, tenant, _ = scheduled_database
    with factory() as db:
        tenant, target, account, case = setup(
            db, SimpleNamespace(tenant=SimpleNamespace(id=tenant))
        )
        a = proposal(
            db, tenant, "finance.target_mapping.set", **rule(target, account, case)
        ).id
        b = proposal(
            db, tenant, "finance.target_mapping.set", **rule(target, account, case)
        ).id
    barrier = Barrier(2)

    def approve(identity):
        with factory() as db:
            barrier.wait(timeout=10)
            try:
                return approve_and_execute_proposal(db, tenant, identity).status
            except core.Conflict:
                return "stale"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(approve, [a, b])) == ["executed", "stale"]
    with factory() as db:
        assert service.list_mappings(db, tenant, target_id=target["id"])["total"] == 1


def test_target_migration_preserves_ledger_and_refuses_history_loss(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0053_source_classification")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as db:
            tenant = core.create_tenant(db, "Target migration").id
            customer = core.create_party(db, tenant, "Customer", "customer")
            doc = core.create_document(
                db,
                tenant,
                "sales_invoice",
                "PRESERVED",
                customer.id,
                "119",
                document_date="2026-01-05",
            )
            core.post_sales_invoice(db, tenant, doc.id)
            before = db.scalars(
                text("SELECT row_to_json(e)::text FROM ledger_entry e ORDER BY id")
            ).all()
        command.upgrade(config, "head")
        with Session(engine) as db:
            assert (
                db.scalars(
                    text("SELECT row_to_json(e)::text FROM ledger_entry e ORDER BY id")
                ).all()
                == before
            )
        command.downgrade(config, "0053_source_classification")
        command.upgrade(config, "head")
        with Session(engine) as db:
            change(
                db,
                tenant,
                "finance.target.create",
                namespace="migration",
                name="Preserved target",
            )
        with pytest.raises(RuntimeError, match="history"):
            command.downgrade(config, "0053_source_classification")
    finally:
        engine.dispose()


def test_target_owner_and_shared_adapter_contract(
    session, business, monkeypatch, scheduled_owner
):
    import json
    from contextlib import contextmanager

    from fastapi.testclient import TestClient
    from typer.testing import CliRunner

    from reality.cli.app import app as cli
    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.services.memberships import Principal
    from reality.web.api import database_session
    from reality.web.app import app

    tenant, target, account, case = setup(session, business)
    pending = proposal(
        session, tenant, "finance.target_mapping.set", **rule(target, account, case)
    )
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    with pytest.raises(core.InvalidOperation, match="owner"):
        confirm(session, tenant, pending)
    row = json.loads(
        approve_and_execute_proposal(
            session,
            tenant,
            pending.id,
            confirming_principal=Principal(scheduled_owner.id),
        ).output
    )
    assert row["actor_id"] == scheduled_owner.id
    monkeypatch.setenv("REALITY_AUTH_MODE", "disabled")
    app.dependency_overrides[database_session] = lambda: session

    @contextmanager
    def shared_session():
        yield session

    monkeypatch.setattr("reality.cli.app.Session", shared_session)
    monkeypatch.setattr("reality.cli.app.init_db", lambda: None)
    try:
        with TestClient(app) as client:
            path = f"/api/tenants/{tenant}/finance/target-mappings"
            http = client.get(path, params={"target_id": target["id"]}).json()
            assert http == MCP_TOOL_REGISTRY["finance_target_mappings"].handler(
                session, tenant, {"target_id": target["id"]}
            )
            result = CliRunner().invoke(
                cli,
                [
                    "finance-target-read",
                    "--tool",
                    "finance.target_mappings.list",
                    "--arguments",
                    json.dumps({"target_id": target["id"]}),
                    "--tenant-id",
                    tenant,
                ],
            )
            assert result.exit_code == 0, result.output
            assert json.loads(result.output) == http
            assert (
                client.get(
                    path, params={"target_id": target["id"], "limit": 201}
                ).status_code
                == 400
            )
            assert (
                client.get(path + f"/{row['id']}/history").json()["items"][0]["id"]
                == row["id"]
            )
    finally:
        app.dependency_overrides.clear()


def test_target_two_received_cases_keep_scope_and_stated_amounts(session, business):
    import json

    from reality.db.core import DocumentLine
    from reality.services.finance import components
    from reality.services.finance import target_mappings as service
    from tests.finance.test_components import fixture, prepare

    tenant, target, account, case = setup(session, business)
    doc, ids = fixture(session, business, detail={"net": "1000"}, lines=True)
    first_line = session.scalar(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == doc.id
        )
    )
    first_line.gross_amount = 595
    first_line.payload = json.dumps({"reality_finance_v1": {"net": "500", "tax": "95"}})
    second = DocumentLine(
        id=core.uid("lin"),
        tenant_id=tenant,
        document_id=doc.id,
        sku="SECOND",
        quantity=1,
        unit_price=595,
        gross_amount=595,
        payload=first_line.payload,
    )
    session.add(second)
    session.flush()
    received = components.component_context(session, tenant, doc.id)["items"]
    for item, case_id in zip(received, (case["id"], ids["DOMESTIC"]), strict=True):
        confirm(
            session,
            tenant,
            prepare(
                session,
                tenant,
                doc,
                document_line_id=item["document_line_id"],
                expected_evidence_hash=item["evidence_hash"],
                case_reference_id=case_id,
            ),
        )
    tax = change(
        session,
        tenant,
        "finance.target_reference.create",
        target_id=target["id"],
        kind="tax_code",
        code="EXPLICIT",
        name="Declared target tax code",
    )
    a = change(
        session,
        tenant,
        "finance.target_mapping.set",
        **rule(target, account, case, external_tax_code_id=tax["id"]),
    )
    b = change(
        session,
        tenant,
        "finance.target_mapping.set",
        **rule(target, account, {"id": ids["DOMESTIC"]}),
    )
    result = service._preview_document(
        session, tenant, target["id"], doc.id, 50, 0, components.component_context
    )
    assert {i["mapping"]["id"] for i in result["items"]} == {a["id"], b["id"]}
    assert all(
        i["received"]["amounts"]
        == {"net": "500", "tax": "95", "gross": "595", "base": None}
        for i in result["items"]
    )
    assert sum(i["external_tax_code"] is not None for i in result["items"]) == 1
    assert result["operational_legs_total"] == 0


def test_target_search_paging_and_duplicate_reference_codes(session, business):
    from reality.services.finance import target_mappings as service

    tenant, target, account, _case = setup(session, business)
    tax = change(
        session,
        tenant,
        "finance.target_reference.create",
        target_id=target["id"],
        kind="tax_code",
        code="SALES",
        name="Same code different kind",
    )
    page = service.list_target_references(
        session, tenant, target_id=target["id"], query="SALES", limit=1
    )
    next_page = service.list_target_references(
        session, tenant, target_id=target["id"], query="SALES", limit=1, offset=1
    )
    assert page["total"] == next_page["total"] == 2
    assert {page["items"][0]["id"], next_page["items"][0]["id"]} == {
        account["id"],
        tax["id"],
    }
    with pytest.raises(core.Conflict, match="already"):
        proposal(
            session,
            tenant,
            "finance.target_reference.create",
            target_id=target["id"],
            kind="account",
            code="SALES",
            name="Duplicate",
        )
    with pytest.raises(core.InvalidOperation):
        service.list_targets(session, tenant, limit=201)


@pytest.mark.parametrize(
    "kind", ["sales_invoice", "supplier_invoice", "credit_note", "supplier_credit_note"]
)
def test_target_customer_supplier_invoice_and_credit_preview(session, business, kind):
    from reality.services.finance import components
    from reality.services.finance import target_mappings as service
    from tests.finance.test_components import fixture, prepare

    tenant, target, account, case = setup(session, business)
    doc, _ = fixture(session, business, kind=kind, detail={"net": "1000", "tax": "190"})
    confirm(
        session, tenant, prepare(session, tenant, doc, case_reference_id=case["id"])
    )
    mapped = change(
        session,
        tenant,
        "finance.target_mapping.set",
        **rule(target, account, case, transaction_kind=kind),
    )
    preview = service._preview_document(
        session, tenant, target["id"], doc.id, 50, 0, components.component_context
    )
    assert preview["transaction_kind"] == kind
    assert preview["items"][0]["status"] == "resolved"
    assert preview["items"][0]["mapping"]["id"] == mapped["id"]
    assert preview["items"][0]["received"]["source_record_id"] == doc.source_record_id
    assert preview["items"][0]["received"]["amounts"]["gross"] == "1190"


def test_target_operational_leg_does_not_fill_missing_component_case(session, business):
    from reality.db.core import SubledgerAccount
    from reality.services.finance import components
    from reality.services.finance import target_mappings as service
    from tests.finance.test_components import fixture

    tenant, target, account, _ = setup(session, business)
    doc, _ = fixture(session, business, detail={"net": "1000", "tax": "190"})
    core.post_sales_invoice(session, tenant, doc.id)
    local = session.scalar(
        select(SubledgerAccount).where(
            SubledgerAccount.tenant_id == tenant,
            SubledgerAccount.role == "accounts_receivable",
        )
    )
    mapped = change(
        session,
        tenant,
        "finance.target_mapping.set",
        target_id=target["id"],
        mapping_kind="local_account",
        local_account_id=local.id,
        external_account_id=account["id"],
    )
    preview = service._preview_document(
        session, tenant, target["id"], doc.id, 50, 0, components.component_context
    )
    assert preview["items"][0]["status"] == "missing_case"
    resolved = [r for r in preview["operational_legs"] if r["status"] == "resolved"]
    assert len(resolved) == 1 and resolved[0]["mapping"]["id"] == mapped["id"]
    assert resolved[0]["external_tax_code"] is None


def test_target_preview_refuses_assignment_from_previous_evidence(session, business):
    from reality.services.finance import components
    from reality.services.finance import target_mappings as service
    from tests.finance.test_components import fixture, prepare

    tenant, target, account, case = setup(session, business)
    doc, _ = fixture(session, business, detail={"net": "1000", "tax": "190"})
    confirm(
        session, tenant, prepare(session, tenant, doc, case_reference_id=case["id"])
    )
    change(session, tenant, "finance.target_mapping.set", **rule(target, account, case))
    source, _, _ = core.store_source_record(
        session,
        tenant,
        "declared-finance-test",
        "invoice",
        "CORRECTED",
        {"reality_finance_v1": {"net": "1100", "tax": "90"}},
    )
    doc.source_record_id = source.id
    session.flush()
    result = service._preview_document(
        session, tenant, target["id"], doc.id, 50, 0, components.component_context
    )
    assert result["items"][0]["status"] == "stale_assignment"
    assert result["items"][0]["received"]["amounts"]["net"] == "1100"
