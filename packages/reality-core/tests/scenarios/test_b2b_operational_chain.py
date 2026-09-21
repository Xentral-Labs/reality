import re
from decimal import Decimal

from conftest import record_by_id, seed_company
from reality.db.core import Document, PlaygroundRun
from reality.services import company_setup
from reality.services.costing import reviewed_contribution
from reality.services.exceptions import operational_exceptions
from reality.services.movement_explanations import movement_explanation
from reality.services.return_dispositions import return_disposition_summary
from reality.services.supply_assignments import supply_coverage
from sqlalchemy import select


def _company(session, owner, request_id="b2b-operational-chain"):
    result = company_setup.create_company(
        session,
        owner.id,
        request_id,
        "Harbor Supply B2B",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    assert seed_company(session, result["tenant_id"]) == "succeeded"
    run = record_by_id(session, PlaygroundRun, result["run_id"])
    return result["tenant_id"], run.initialization_progress


def test_empty_company_profile_builds_dated_consistently_numbered_story(
    session, scheduled_owner
):
    tenant, manifest = _company(session, scheduled_owner)

    assert {"b2b_supply_chain", "b2b_return_disposition"} <= set(manifest["cases"])
    documents = list(
        session.scalars(select(Document).where(Document.tenant_id == tenant))
    )
    assert documents and all(row.document_date is not None for row in documents)
    patterns = {
        "sales_order": r"SO-\d{3}",
        "purchase_order": r"PO-\d{3}",
        "supplier_invoice": r"SINV-\d{3}",
        "credit_note": r"CN-\d{3}",
        "supplier_credit_note": r"SCN-\d{3}",
        "customer_payment": r"CPAY-\d{3}",
        "supplier_payment": r"SPAY-\d{3}",
    }
    for row in documents:
        if row.type in patterns:
            assert re.fullmatch(patterns[row.type], row.number), (row.type, row.number)


def test_supply_and_return_reconciliations_are_exact(session, scheduled_owner):
    tenant, manifest = _company(session, scheduled_owner, "b2b-reconciliation")
    supply = manifest["cases"]["b2b_supply_chain"]
    coverage = supply_coverage(
        session,
        tenant,
        supplier_commitment_id=supply["purchase_commitment_id"],
    )["supplier"]
    assert coverage == {
        "commitment_id": supply["purchase_commitment_id"],
        "quantity": Decimal(10),
        "received": Decimal(4),
        "open": Decimal(6),
        "customer_assigned": Decimal(6),
        "stock_replenishment": Decimal(2),
        "unassigned": Decimal(2),
    }

    returned = manifest["cases"]["b2b_return_disposition"]
    disposition = return_disposition_summary(
        session, tenant, returned["return_movement_id"]
    )
    assert disposition["arrived"] == Decimal(5)
    assert disposition["unresolved"] == Decimal(0)
    assert disposition["totals"] == {
        "restock": Decimal(2),
        "quarantine_repair": Decimal(1),
        "scrap_loss": Decimal(1),
        "return_to_supplier": Decimal(1),
    }

    contribution_case = manifest["costing_cases"]["fixture_a"]
    contribution = reviewed_contribution(
        session,
        tenant,
        contribution_case["invoice_line_id"],
        review_id=contribution_case["contribution_review_id"],
    )
    assert contribution["db1"] == "570.0000"
    assert contribution["db2"] == "456.0000"
    assert contribution["missing_basis"] == []


def test_story_movements_are_explained_and_setup_replay_is_idempotent(
    session, scheduled_owner
):
    tenant, manifest = _company(session, scheduled_owner, "b2b-replay")
    movement_ids = {
        manifest["cases"]["b2b_supply_chain"]["receipt_movement_id"],
        manifest["cases"]["b2b_return_disposition"]["return_movement_id"],
        *(
            manifest["cases"]["b2b_return_disposition"][key]
            for key in (
                "restock_movement_id",
                "quarantine_movement_id",
                "scrap_movement_id",
                "supplier_return_movement_id",
            )
        ),
    }
    assert all(
        movement_explanation(session, tenant, movement_id)["explained"]
        for movement_id in movement_ids
    )
    unexplained = {
        row.record_id
        for row in operational_exceptions(session, tenant)
        if row.class_id == "unexplained_movement"
    }
    assert movement_ids.isdisjoint(unexplained)

    replay = company_setup.create_company(
        session,
        scheduled_owner.id,
        "b2b-replay",
        "Harbor Supply B2B",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    assert replay["tenant_id"] == tenant
