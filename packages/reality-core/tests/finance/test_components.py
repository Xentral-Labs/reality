"""Received values and internal attribution never create a second monetary balance."""

import hashlib
import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import DocumentLine, LedgerEntry, SourceRecord
from reality.services import core
from reality.services.finance import components
from reality.tools.application import (
    create_change_proposal,
)
from tests.finance.test_references import confirm
from tests.finance.test_references import propose as reference_proposal


def fixture(session, business, kind="sales_invoice", detail=None, lines=False):
    tenant = business.tenant.id
    source_payload = json.dumps(
        {
            "reality_finance_v1": detail
            if detail is not None
            else {
                "net": "1000",
                "tax": "190",
                "codes": {"case": {"namespace": "supplier-v1", "code": "EU"}},
            }
        }
    )
    source = SourceRecord(
        id=core.uid("src"),
        tenant_id=tenant,
        source_system="declared-finance-test",
        source_type="invoice",
        external_id=core.uid("ext"),
        payload=source_payload,
        payload_hash=hashlib.sha256(source_payload.encode()).hexdigest(),
        version=1,
    )
    session.add(source)
    session.flush()
    doc = core.create_document(
        session,
        tenant,
        kind,
        core.uid("INV"),
        business.customer.id
        if kind in {"sales_invoice", "credit_note"}
        else business.supplier.id,
        "1190",
        source_record_id=source.id,
    )
    if lines:
        session.add(
            DocumentLine(
                id=core.uid("lin"),
                tenant_id=tenant,
                document_id=doc.id,
                sku="ONE",
                quantity=1,
                unit_price=1190,
                gross_amount=1190,
                payload=source_payload,
            )
        )
        session.commit()
    ids = {}
    for reference_kind, code in [
        ("cost_center", "A"),
        ("cost_center", "B"),
        ("case_code", "DOMESTIC"),
        ("coding_group", "GOODS"),
    ]:
        row = confirm(
            session,
            tenant,
            reference_proposal(
                session, tenant, kind=reference_kind, code=code, name=code
            ),
        )
        ids[code] = row["id"]
    return doc, ids


def prepare(session, tenant, doc, **changes):
    ctx = components.component_context(session, tenant, doc.id)
    item = ctx["items"][0]
    arguments = {
        "document_id": doc.id,
        "document_line_id": item["document_line_id"],
        "basis": "net",
        "expected_evidence_hash": item["evidence_hash"],
        "expected_revision": ctx["revision"],
        "parts": [],
        "reason": "Internal responsibility",
        **changes,
    }
    return create_change_proposal(
        session, tenant, "finance.component.assign", arguments
    )


@pytest.mark.parametrize(
    "kind",
    ["sales_invoice", "supplier_invoice", "credit_note", "supplier_credit_note"],
)
def test_received_net_split_and_partial_revision_preserve_gross(
    session, business, kind
):
    from reality.db.components import ComponentAssignment, FinancialComponent

    tenant = business.tenant.id
    doc, ids = fixture(session, business, kind)
    if kind == "sales_invoice":
        core.post_sales_invoice(session, tenant, doc.id)
    before = [
        (r.id, r.amount, r.account_id)
        for r in session.scalars(
            select(LedgerEntry).where(LedgerEntry.tenant_id == tenant)
        )
    ]
    parts = [
        {"cost_center_reference_id": ids["A"], "amount": "600"},
        {"cost_center_reference_id": ids["B"], "amount": "400"},
    ]
    proposal = prepare(
        session,
        tenant,
        doc,
        parts=parts,
        case_reference_id=ids["DOMESTIC"],
        group_reference_id=ids["GOODS"],
    )
    assert session.scalar(select(func.count()).select_from(FinancialComponent)) == 0
    review = json.loads(proposal.output)["assignment"]
    assert (
        review["after"]["assigned"] == "1000" and review["after"]["unassigned"] == "0"
    )
    first = confirm(session, tenant, proposal)
    assert confirm(session, tenant, proposal) == first
    assert session.scalar(select(func.count()).select_from(ComponentAssignment)) == 1
    partial = confirm(session, tenant, prepare(session, tenant, doc, parts=parts[:1]))
    assert partial["assigned"] == "600" and partial["unassigned"] == "400"
    history = components.component_history(session, tenant, first["component_id"])
    assert history["total"] == 2 and history["items"][1]["assigned"] == "1000"
    assert history["items"][1]["references"]["case"]["code"] == "DOMESTIC"
    assert doc.gross_amount == Decimal(1190)
    assert [
        (r.id, r.amount, r.account_id)
        for r in session.scalars(
            select(LedgerEntry).where(LedgerEntry.tenant_id == tenant)
        )
    ] == before


def test_missing_zero_summary_and_no_inferred_tax(session, business):
    tenant = business.tenant.id
    doc, ids = fixture(session, business, detail={"net": None, "tax": "0"}, lines=True)
    ctx = components.component_context(session, tenant, doc.id)
    assert ctx["summary"]["amounts"]["gross"] == "1190"
    assert (
        ctx["items"][0]["amounts"]["net"] is None
        and ctx["items"][0]["amounts"]["tax"] == "0"
    )
    with pytest.raises(core.InvalidOperation, match="basis"):
        prepare(
            session,
            tenant,
            doc,
            parts=[{"cost_center_reference_id": ids["A"], "amount": "1"}],
        )
    with pytest.raises(core.InvalidOperation, match="lines"):
        prepare(session, tenant, doc, document_line_id=None)
    receipt = confirm(
        session,
        tenant,
        prepare(session, tenant, doc, case_reference_id=ids["DOMESTIC"]),
    )
    assert receipt["unassigned"] is None and receipt["assigned"] == "0"


def test_invalid_parts_kind_scope_and_stale_references(session, business):
    tenant = business.tenant.id
    doc, ids = fixture(session, business)
    for parts in (
        [{"cost_center_reference_id": ids["A"], "amount": "1001"}],
        [{"cost_center_reference_id": ids["A"], "amount": "0"}],
        [{"cost_center_reference_id": ids["DOMESTIC"], "amount": "1"}],
        [{"cost_center_reference_id": ids["A"], "amount": "1.00001"}],
        [{"cost_center_reference_id": ids["A"], "amount": "1"}] * 2,
    ):
        with pytest.raises(core.InvalidOperation):
            prepare(session, tenant, doc, parts=parts)
    other = core.create_tenant(session, "Foreign").id
    with pytest.raises(core.NotFound):
        components.component_context(session, other, doc.id)
    foreign = confirm(
        session,
        other,
        reference_proposal(
            session, other, kind="cost_center", code="X", name="Foreign"
        ),
    )
    with pytest.raises(core.NotFound):
        prepare(
            session,
            tenant,
            doc,
            parts=[{"cost_center_reference_id": foreign["id"], "amount": "1"}],
        )
    pending = prepare(
        session,
        tenant,
        doc,
        parts=[{"cost_center_reference_id": ids["A"], "amount": "100"}],
    )
    confirm(
        session,
        tenant,
        reference_proposal(
            session, tenant, reference_id=ids["A"], name="Closed", state="blocked"
        ),
    )
    with pytest.raises(core.Conflict):
        confirm(session, tenant, pending)
    with pytest.raises(core.InvalidOperation):
        prepare(
            session,
            tenant,
            doc,
            parts=[{"cost_center_reference_id": ids["A"], "amount": "1"}],
        )


def test_assignment_audit_failure_rolls_back_normalization(
    session, business, monkeypatch
):
    from reality.db.components import ComponentAssignment, FinancialComponent

    tenant = business.tenant.id
    doc, ids = fixture(session, business)
    proposal = prepare(
        session,
        tenant,
        doc,
        parts=[{"cost_center_reference_id": ids["A"], "amount": "100"}],
    )
    with monkeypatch.context() as patch:

        def fail(*args, **kwargs):
            raise RuntimeError("audit failure")

        patch.setattr(core, "emit_business_event", fail)
        with pytest.raises(RuntimeError):
            confirm(session, tenant, proposal)
    assert session.scalar(select(func.count()).select_from(FinancialComponent)) == 0
    assert session.scalar(select(func.count()).select_from(ComponentAssignment)) == 0
    assert confirm(session, tenant, proposal)["assigned"] == "100"


@pytest.mark.parametrize(
    "detail",
    [
        {"gross": "1189"},
        {"currency": "USD"},
        {"version": 2},
        {"net": "NaN"},
        {"tax": "0.00001"},
        {"base": True},
    ],
)
def test_invalid_received_contract_never_becomes_attribution(session, business, detail):
    from reality.db.components import FinancialComponent

    doc, _ = fixture(session, business, detail=detail)
    with pytest.raises(core.InvalidOperation):
        components.component_context(session, business.tenant.id, doc.id)
    assert session.scalar(select(func.count()).select_from(FinancialComponent)) == 0


def test_zero_unknown_and_gross_basis_are_distinct(session, business):
    tenant = business.tenant.id
    doc, ids = fixture(session, business, detail={"net": "0", "tax": None})
    context = components.component_context(session, tenant, doc.id)
    assert context["items"][0]["amounts"] == {
        "net": "0",
        "tax": None,
        "gross": "1190",
        "base": None,
    }
    with pytest.raises(core.InvalidOperation):
        prepare(
            session,
            tenant,
            doc,
            parts=[{"cost_center_reference_id": ids["A"], "amount": "1"}],
        )
    zero = confirm(session, tenant, prepare(session, tenant, doc))
    assert zero["assigned"] == zero["unassigned"] == "0"
    gross = confirm(
        session,
        tenant,
        prepare(
            session,
            tenant,
            doc,
            basis="gross",
            parts=[{"cost_center_reference_id": ids["A"], "amount": "1190"}],
        ),
    )
    assert gross["unassigned"] == "0"
    cleared = confirm(session, tenant, prepare(session, tenant, doc, basis="gross"))
    assert cleared["unassigned"] == "1190" and cleared["parts"] == []


def test_stale_evidence_and_frozen_history(session, business):
    tenant = business.tenant.id
    doc, ids = fixture(session, business)
    first = confirm(
        session,
        tenant,
        prepare(
            session,
            tenant,
            doc,
            parts=[{"cost_center_reference_id": ids["A"], "amount": "100"}],
        ),
    )
    pending = prepare(session, tenant, doc)
    doc.gross_amount = Decimal(1200)
    session.commit()
    with pytest.raises(core.Conflict):
        confirm(session, tenant, pending)
    with pytest.raises(core.Conflict):
        prepare(session, tenant, doc)
    confirm(
        session,
        tenant,
        reference_proposal(
            session,
            tenant,
            reference_id=ids["A"],
            name="Closed center",
            state="blocked",
        ),
    )
    history = components.component_history(
        session, tenant, first["component_id"], limit=1
    )
    assert history["items"][0]["references"]["centers"][ids["A"]]["name"] == "A"
    assert history["items"][0]["basis_amount"] == "1000"
    assert (
        components.component_history(session, tenant, first["component_id"], offset=1)[
            "items"
        ]
        == []
    )
    other = core.create_tenant(session, "Foreign history").id
    with pytest.raises(core.NotFound):
        components.component_history(session, other, first["component_id"])


def test_component_owner_and_http_mcp_parity(
    session, business, scheduled_owner, monkeypatch
):
    from fastapi.testclient import TestClient

    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.services.memberships import Principal
    from reality.tools.application import approve_and_execute_proposal
    from reality.web.api import database_session
    from reality.web.app import app

    tenant = business.tenant.id
    doc, _ = fixture(session, business)
    proposal = prepare(session, tenant, doc)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    with pytest.raises(core.InvalidOperation, match="owner"):
        confirm(session, tenant, proposal)
    receipt = json.loads(
        approve_and_execute_proposal(
            session,
            tenant,
            proposal.id,
            confirming_principal=Principal(scheduled_owner.id),
        ).output
    )
    assert receipt["actor_id"] == scheduled_owner.id
    monkeypatch.setenv("REALITY_AUTH_MODE", "disabled")
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{tenant}/finance/components"
            assert client.get(base + "/context/" + doc.id).json() == MCP_TOOL_REGISTRY[
                "finance_components"
            ].handler(session, tenant, {"document_id": doc.id})
            assert client.get(
                base + "/" + receipt["component_id"] + "/history"
            ).json() == MCP_TOOL_REGISTRY["finance_component_history"].handler(
                session, tenant, {"component_id": receipt["component_id"]}
            )
            assert (
                client.get(base + "/context/" + doc.id + "?limit=201").status_code
                == 400
            )
    finally:
        app.dependency_overrides.clear()


def test_component_concurrent_replay_and_reference_change(scheduled_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    from reality.db.components import ComponentAssignment
    from reality.tools.application import approve_and_execute_proposal

    _, factory, tenant, _ = scheduled_database
    with factory() as db:
        customer = core.create_party(db, tenant, "Concurrent customer", "customer")
        doc, ids = fixture(
            db, SimpleNamespace(tenant=SimpleNamespace(id=tenant), customer=customer)
        )
        proposal_id = prepare(db, tenant, doc).id
    barrier = Barrier(2)

    def execute(proposal_id):
        with factory() as db:
            barrier.wait(timeout=10)
            try:
                return approve_and_execute_proposal(db, tenant, proposal_id).status
            except core.Conflict:
                return "stale"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(execute, [proposal_id, proposal_id])) == [
            "executed",
            "executed",
        ]
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(ComponentAssignment)) == 1
        assignment = prepare(
            db,
            tenant,
            doc,
            parts=[{"cost_center_reference_id": ids["A"], "amount": "100"}],
        ).id
        blocking = reference_proposal(
            db, tenant, reference_id=ids["A"], name="Blocked", state="blocked"
        ).id
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(execute, [assignment, blocking])) == [
            "executed",
            "stale",
        ]


def test_component_migration_preserves_postings_and_guards_history(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0051_finance_references")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as db:
            tenant = core.create_tenant(db, "Component migration").id
            party = core.create_party(db, tenant, "Customer", "customer")
            doc = core.create_document(
                db, tenant, "sales_invoice", "INV", party.id, "119"
            )
            doc_id = doc.id
            core.post_sales_invoice(db, tenant, doc_id)
            before = (
                db.execute(
                    text("SELECT row_to_json(e)::text FROM ledger_entry e ORDER BY id")
                )
                .scalars()
                .all()
            )
        command.upgrade(config, "head")
        with Session(engine) as db:
            assert (
                db.execute(
                    text("SELECT row_to_json(e)::text FROM ledger_entry e ORDER BY id")
                )
                .scalars()
                .all()
                == before
            )
            assert components.component_context(db, tenant, doc_id)["items"][0][
                "amounts"
            ] == {"net": None, "tax": None, "base": None, "gross": "119"}
        command.downgrade(config, "0051_finance_references")
        command.upgrade(config, "head")
        with Session(engine) as db:
            from reality.db.core import Document

            doc = db.get(Document, doc_id)
            confirm(db, tenant, prepare(db, tenant, doc, basis="gross"))
        with pytest.raises(RuntimeError, match="history"):
            command.downgrade(config, "0051_finance_references")
    finally:
        engine.dispose()
