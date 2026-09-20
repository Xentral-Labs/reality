"""Receipt costs preserve evidence, reviewed completeness and prior knowledge."""

import hashlib
import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import AppUser, ChangeProposal, DocumentLine, TenantMembership
from reality.db.costing import CostAttribution, CostAttributionPart, CostInputManifest
from reality.domain.costing import CATEGORIES
from reality.services import core
from reality.services.costing import (
    cost_evidence,
    execute_cost_change,
    preview_cost_change,
    receipt_cost,
)


@pytest.fixture
def cost_owner(session, business):
    user = AppUser(
        id=core.uid("usr"),
        email=core.uid("mail") + "@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=core.now(),
    )
    session.add(user)
    session.flush()
    session.add(
        TenantMembership(
            id=core.uid("tmb"),
            tenant_id=business.tenant.id,
            user_id=user.id,
            role="owner",
            status="active",
        )
    )
    session.flush()
    return user


def receipt(session, business):
    return core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "100",
        to_location_id=business.location.id,
    )


def evidence(
    session, business, amount="1000", tax="190", document_type="supplier_invoice"
):
    from reality.db.core import SourceRecord

    payload = json.dumps({"reality_finance_v1": {"net": amount, "tax": tax}})
    source = SourceRecord(
        id=core.uid("src"),
        tenant_id=business.tenant.id,
        source_system="cost-fixture",
        source_type="invoice",
        external_id=core.uid("ext"),
        payload=payload,
        payload_hash=hashlib.sha256(payload.encode()).hexdigest(),
        version=1,
    )
    session.add(source)
    session.flush()
    return core.create_document(
        session,
        business.tenant.id,
        document_type,
        core.uid("INV"),
        business.supplier.id,
        str(Decimal(amount) + Decimal(tax)),
        source_record_id=source.id,
    )


def assignment(session, business, movement, doc, amount, category="goods", **kwargs):
    ctx = cost_evidence(session, business.tenant.id, doc.id)
    return {
        "operation": "assign",
        "document_id": doc.id,
        "expected_event_sequence": ctx["event_sequence"],
        "expected_evidence_hash": ctx["evidence_hash"],
        "basis": "net",
        "tax_treatment": "recoverable",
        "selected_basis_tax_inclusion": "excluded",
        "parts": [
            {
                "movement_id": movement.id,
                "category": category,
                "source_share": amount,
                "cost_effect": -1 if category == "purchase_reduction" else 1,
            }
        ],
        "reason": "Received amount attributed to actual receipt",
        **kwargs,
    }


def execute(session, business, owner, arguments):
    from reality.services.memberships import Principal

    preview = preview_cost_change(
        session, business.tenant.id, arguments, principal=Principal(owner.id)
    )
    action = ChangeProposal(
        id=core.uid("act"),
        tenant_id=business.tenant.id,
        type="tool:cost.change",
        status="proposed",
        input=json.dumps(arguments),
        output=json.dumps(preview),
    )
    session.add(action)
    session.flush()
    return execute_cost_change(
        session,
        business.tenant.id,
        arguments=arguments,
        action_id=action.id,
        actor_id=owner.id,
        confirmed=True,
    )


def review(session, business, owner, movement, evidenced):
    return execute(
        session,
        business,
        owner,
        {
            "operation": "review",
            "movement_id": movement.id,
            "expected_event_sequence": receipt_cost(
                session, business.tenant.id, movement.id
            )["event_sequence"],
            "categories": [
                {
                    "category": c,
                    "disposition": "evidenced" if c in evidenced else "not_applicable",
                    "reason": "Reviewed retained receipt scope",
                }
                for c in CATEGORIES
            ],
            "reason": "All required acquisition categories considered",
        },
    )


def test_receipt_a_and_retained_review_survive_late_cost(session, business, cost_owner):
    movement = receipt(session, business)
    for amount, category in [
        ("1000", "goods"),
        ("100", "inbound_freight"),
        ("-50", "purchase_reduction"),
    ]:
        doc = evidence(session, business, amount, "0")
        execute(
            session,
            business,
            cost_owner,
            assignment(session, business, movement, doc, amount, category),
        )
    before = receipt_cost(session, business.tenant.id, movement.id)
    assert before["known_cost"] == "1050.0000" and before["actual_cost"] is None
    settled = review(
        session,
        business,
        cost_owner,
        movement,
        {"goods", "inbound_freight", "purchase_reduction"},
    )
    assert settled["actual_cost"] == "1050.0000" and settled["unit_cost"] == "10.500000"
    manifest = settled["manifest_id"]
    doc = evidence(session, business, "10", "0")
    execute(
        session,
        business,
        cost_owner,
        assignment(session, business, movement, doc, "10", "duty"),
    )
    current = receipt_cost(session, business.tenant.id, movement.id)
    assert (
        current["known_cost"] == "1060.0000"
        and current["actual_cost"] is None
        and current["review_state"] == "stale"
    )
    old = receipt_cost(session, business.tenant.id, movement.id, manifest_id=manifest)
    assert old["actual_cost"] == "1050.0000"


def test_missing_net_and_recoverable_gross_never_become_final(
    session, business, cost_owner
):
    movement = receipt(session, business)
    doc = evidence(session, business)
    args = assignment(
        session,
        business,
        movement,
        doc,
        "1190",
        basis="gross",
        selected_basis_tax_inclusion="included",
    )
    execute(session, business, cost_owner, args)
    out = review(session, business, cost_owner, movement, {"goods"})
    assert out["actual_cost"] is None and "tax_basis_incomplete" in out["missing_basis"]


def test_owner_staleness_and_foreign_scope_leave_no_parts(
    session, business, cost_owner
):
    movement = receipt(session, business)
    doc = evidence(session, business)
    args = assignment(session, business, movement, doc, "1000")
    member = session.scalar(
        select(TenantMembership).where(TenantMembership.user_id == cost_owner.id)
    )
    member.role = "member"
    session.flush()
    with pytest.raises(core.InvalidOperation, match="owner"), session.begin_nested():
        execute(session, business, cost_owner, args)
    assert session.scalar(select(func.count()).select_from(CostAttribution)) == 0
    member.role = "owner"
    session.flush()
    other = core.create_tenant(session, "Other cost tenant")
    with pytest.raises(core.NotFound):
        receipt_cost(session, other.id, movement.id)
    core.emit_business_event(
        session, business.tenant.id, "document.corrected", "document", doc.id, {}
    )
    session.flush()
    with pytest.raises(core.Conflict, match="stale"), session.begin_nested():
        execute(session, business, cost_owner, args)
    assert session.scalar(select(func.count()).select_from(CostAttributionPart)) == 0


def test_replacement_retires_predecessor_and_history_stays_readable(
    session, business, cost_owner
):
    movement = receipt(session, business)
    doc = evidence(session, business)
    first = execute(
        session,
        business,
        cost_owner,
        assignment(session, business, movement, doc, "1000"),
    )
    old = review(session, business, cost_owner, movement, {"goods"})
    replacement = evidence(session, business, "900", "0")
    args = assignment(
        session,
        business,
        movement,
        replacement,
        "900",
        operation="replace",
        previous_component_basis_id=first["component_basis_id"],
    )
    execute(session, business, cost_owner, args)
    assert (
        receipt_cost(session, business.tenant.id, movement.id)["known_cost"]
        == "900.0000"
    )
    assert (
        receipt_cost(
            session, business.tenant.id, movement.id, manifest_id=old["manifest_id"]
        )["actual_cost"]
        == "1000.0000"
    )


def test_reads_do_not_flush_pending_changes(session, business):
    movement = receipt(session, business)
    doc = evidence(session, business)
    session.add(
        DocumentLine(
            id=core.uid("lin"),
            tenant_id=business.tenant.id,
            document_id=doc.id,
            sku="pending",
            quantity=1,
            unit_price=1,
            gross_amount=1,
            payload="{}",
        )
    )
    receipt_cost(session, business.tenant.id, movement.id)
    cost_evidence(session, business.tenant.id, doc.id)
    assert session.new
    assert (
        session.scalar(
            select(func.count())
            .select_from(CostInputManifest)
            .execution_options(autoflush=False)
        )
        == 0
    )


def test_mixed_tax_is_separate_and_cannot_be_counted_twice(
    session, business, cost_owner
):
    movement = receipt(session, business)
    doc = evidence(session, business)
    args = assignment(
        session,
        business,
        movement,
        doc,
        "1000",
        tax_treatment="mixed",
        nonrecoverable_tax_amount="95",
    )
    args["parts"].append(
        {
            "movement_id": movement.id,
            "category": "nonrecoverable_tax",
            "source_share": "95",
            "cost_effect": 1,
            "amount_bucket": "nonrecoverable_tax",
        }
    )
    execute(session, business, cost_owner, args)
    assert (
        review(
            session, business, cost_owner, movement, {"goods", "nonrecoverable_tax"}
        )["actual_cost"]
        == "1095.0000"
    )
    args.update(
        expected_event_sequence=receipt_cost(session, business.tenant.id, movement.id)[
            "event_sequence"
        ],
        basis="gross",
        selected_basis_tax_inclusion="included",
    )
    with pytest.raises(core.InvalidOperation, match="twice"):
        execute(session, business, cost_owner, args)


def test_manual_evidence_cannot_overwrite_admitted_cost(session, business, cost_owner):
    movement = receipt(session, business)
    doc = core.create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        "manual-cost",
        business.supplier.id,
        "1000",
    )
    execute(
        session,
        business,
        cost_owner,
        assignment(
            session,
            business,
            movement,
            doc,
            "1000",
            basis="gross",
            tax_treatment="not_applicable",
            selected_basis_tax_inclusion="included",
        ),
    )
    with pytest.raises(core.InvalidOperation, match="immutable"):
        core.correct_manual_document(
            session,
            business.tenant.id,
            doc.id,
            document_type=doc.type,
            number=doc.number,
            party_id=doc.party_id,
            amount="900",
        )
    assert doc.gross_amount == Decimal(1000)


def test_receipt_correction_invalidates_current_but_not_retained_review(
    session, business, cost_owner
):
    movement = receipt(session, business)
    doc = evidence(session, business)
    execute(
        session,
        business,
        cost_owner,
        assignment(session, business, movement, doc, "1000"),
    )
    old = review(session, business, cost_owner, movement, {"goods"})
    core.correct_movement(
        session, business.tenant.id, movement.id, reason="Receipt entered incorrectly"
    )
    current = receipt_cost(session, business.tenant.id, movement.id)
    assert (
        current["actual_cost"] is None
        and "receipt_corrected" in current["missing_basis"]
    )
    assert (
        receipt_cost(
            session, business.tenant.id, movement.id, manifest_id=old["manifest_id"]
        )["actual_cost"]
        == "1000.0000"
    )


def test_failed_attribution_rolls_back_normalization_and_event(
    session, business, cost_owner, monkeypatch
):
    from reality.db.components import FinancialComponent
    from reality.db.core import BusinessEvent
    from reality.db.costing import CostReceiptBasis
    from reality.services import costing

    movement = receipt(session, business)
    doc = evidence(session, business)
    args = assignment(session, business, movement, doc, "1000")
    counts = [
        session.scalar(select(func.count()).select_from(model))
        for model in (BusinessEvent, FinancialComponent, CostReceiptBasis)
    ]
    original = costing._new

    def fail_part(session, model, tenant, **values):
        if model is CostAttributionPart:
            raise RuntimeError("injected write failure")
        return original(session, model, tenant, **values)

    monkeypatch.setattr(costing, "_new", fail_part)
    with pytest.raises(RuntimeError, match="injected"):
        execute(session, business, cost_owner, args)
    assert counts == [
        session.scalar(select(func.count()).select_from(model))
        for model in (BusinessEvent, FinancialComponent, CostReceiptBasis)
    ]


def test_service_replay_and_foreign_manifest_are_bound(session, business, cost_owner):
    movement = receipt(session, business)
    doc = evidence(session, business)
    args = assignment(session, business, movement, doc, "1000")
    first = execute(session, business, cost_owner, args)
    action = session.scalar(
        select(ChangeProposal).where(ChangeProposal.type == "tool:cost.change")
    )
    assert (
        execute_cost_change(
            session,
            business.tenant.id,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
        == first
    )
    assert session.scalar(select(func.count()).select_from(CostAttribution)) == 1
    old = review(session, business, cost_owner, movement, {"goods"})
    other = core.create_tenant(session, "Foreign receipt history")
    with pytest.raises(core.NotFound):
        receipt_cost(session, other.id, movement.id, manifest_id=old["manifest_id"])
    with pytest.raises(core.NotFound):
        execute_cost_change(
            session,
            other.id,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )


def test_foreign_receipt_reference_fails_at_database_boundary(
    session, business, cost_owner
):
    from sqlalchemy.exc import IntegrityError

    from reality.db.costing import CostReceiptBasis

    movement = receipt(session, business)
    doc = evidence(session, business)
    execute(
        session,
        business,
        cost_owner,
        assignment(session, business, movement, doc, "1000"),
    )
    basis = session.scalar(select(CostReceiptBasis))
    other = core.create_tenant(session, "Foreign cost reference")
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            CostReceiptBasis(
                id=core.uid("cst"),
                tenant_id=other.id,
                movement_id=movement.id,
                introduced_event_id=basis.introduced_event_id,
                base_quantity=100,
                base_unit=basis.base_unit,
                input_schema_version=1,
            )
        )
        session.flush()


def test_missing_net_is_not_inferred_and_gross_cannot_gain_tax_twice(
    session, business, cost_owner
):
    movement = receipt(session, business)
    manual = core.create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        "gross-only",
        business.supplier.id,
        "1190",
    )
    with pytest.raises(core.InvalidOperation, match="missing"):
        execute(
            session,
            business,
            cost_owner,
            assignment(session, business, movement, manual, "1000"),
        )
    doc = evidence(session, business)
    args = assignment(
        session,
        business,
        movement,
        doc,
        "1190",
        basis="gross",
        tax_treatment="nonrecoverable",
        nonrecoverable_tax_amount="190",
    )
    with pytest.raises(core.InvalidOperation, match="gross"):
        execute(session, business, cost_owner, args)


def test_review_manifest_detects_member_loss(session, business, cost_owner):
    from sqlalchemy import delete

    from reality.db.costing import CostManifestAttribution

    movement = receipt(session, business)
    doc = evidence(session, business)
    execute(
        session,
        business,
        cost_owner,
        assignment(session, business, movement, doc, "1000"),
    )
    old = review(session, business, cost_owner, movement, {"goods"})
    session.execute(
        delete(CostManifestAttribution).where(
            CostManifestAttribution.tenant_id == business.tenant.id,
            CostManifestAttribution.manifest_id == old["manifest_id"],
        )
    )
    with pytest.raises(core.InvalidOperation, match="manifest"):
        receipt_cost(
            session, business.tenant.id, movement.id, manifest_id=old["manifest_id"]
        )


def test_component_bound_refuses_before_adding_unreadable_scope(
    session, business, cost_owner, monkeypatch
):
    from reality.services import costing

    monkeypatch.setattr(costing, "LIMIT", 1)
    movement = receipt(session, business)
    doc = evidence(session, business)
    execute(
        session,
        business,
        cost_owner,
        assignment(session, business, movement, doc, "1000"),
    )
    freight = evidence(session, business, "100", "0")
    with pytest.raises(core.InvalidOperation, match="bound"):
        execute(
            session,
            business,
            cost_owner,
            assignment(session, business, movement, freight, "100", "inbound_freight"),
        )
    assert (
        receipt_cost(session, business.tenant.id, movement.id)["known_cost"]
        == "1000.0000"
    )


@pytest.mark.parametrize("credit,tax", [("50", "9.5"), ("-50", "-9.5")])
def test_nonrecoverable_tax_on_supplier_credit_reduces_cost(
    session, business, cost_owner, credit, tax
):
    movement = receipt(session, business)
    goods = evidence(session, business, "1000", "0")
    execute(
        session,
        business,
        cost_owner,
        assignment(session, business, movement, goods, "1000"),
    )
    credit_doc = evidence(
        session, business, credit, tax, document_type="supplier_credit_note"
    )
    args = assignment(
        session,
        business,
        movement,
        credit_doc,
        credit,
        "purchase_reduction",
        tax_treatment="nonrecoverable",
        nonrecoverable_tax_amount=tax,
    )
    args["parts"].append(
        {
            "movement_id": movement.id,
            "category": "nonrecoverable_tax",
            "source_share": tax,
            "amount_bucket": "nonrecoverable_tax",
            "cost_effect": -1,
        }
    )
    execute(session, business, cost_owner, args)
    complete = review(
        session,
        business,
        cost_owner,
        movement,
        {"goods", "purchase_reduction", "nonrecoverable_tax"},
    )
    assert complete["actual_cost"] == "940.5000"
    assert complete["unit_cost"] == "9.405000"


def test_line_evidence_uses_shortest_link_and_cannot_be_overwritten(
    session, business, cost_owner
):
    from reality.db.components import FinancialComponent

    movement = receipt(session, business)
    doc, lines = core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "supplier_invoice",
        "LINE-COST",
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "source_line_id": "1",
                "quantity": "100",
                "unit_price": "10",
                "gross_amount": "1000",
            }
        ],
        "1000",
    )
    with pytest.raises(core.InvalidOperation, match="line"):
        cost_evidence(session, business.tenant.id, doc.id)
    line = lines[0]
    ctx = cost_evidence(session, business.tenant.id, doc.id, line.id)
    args = {
        "operation": "assign",
        "document_id": doc.id,
        "document_line_id": line.id,
        "expected_event_sequence": ctx["event_sequence"],
        "expected_evidence_hash": ctx["evidence_hash"],
        "basis": "gross",
        "selected_basis_tax_inclusion": "included",
        "tax_treatment": "not_applicable",
        "reason": "Received line with no applicable tax",
        "parts": [
            {
                "movement_id": movement.id,
                "category": "goods",
                "source_share": "1000",
                "cost_effect": 1,
            }
        ],
    }
    execute(session, business, cost_owner, args)
    component = session.scalar(
        select(FinancialComponent).where(
            FinancialComponent.tenant_id == business.tenant.id
        )
    )
    assert component.document_line_id == line.id and component.document_id is None
    assert (
        review(session, business, cost_owner, movement, {"goods"})["actual_cost"]
        == "1000.0000"
    )
    snapshot = core.manual_document_line_snapshot(session, business.tenant.id, doc.id)
    with pytest.raises(core.InvalidOperation, match="immutable"):
        core.correct_manual_document_lines(
            session,
            business.tenant.id,
            doc.id,
            expected_revision=snapshot["revision"],
            lines=[
                {**snapshot["lines"][0], "description": "Changed after cost admission"}
            ],
        )
