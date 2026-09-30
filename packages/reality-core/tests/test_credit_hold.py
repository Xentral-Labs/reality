"""A new order past the credit limit is held at entry (spec 298 FR-002, FR-003).

Every path that records a sales order ends with the same credit check. It never
refuses the order; it holds the order's promises with `credit_check` and keeps
the facts the decision was based on.
"""

import json
from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import BusinessEvent, CommitmentHold
from reality.services import core
from reality.services.credit_exposure import active_credit_holds, place_credit_holds
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.fulfillment_readiness import fulfillment_readiness
from reality.tools.application import approve_and_execute_proposal


def _customer(session, business, limit="1000", currency="EUR"):
    return core.create_party(
        session,
        business.tenant.id,
        "Credit Kunde GmbH",
        "customer",
        credit_limit=limit,
        default_currency=currency,
    )


def _open_invoice(session, business, party, amount, day="2026-07-01", number="RE-C-1"):
    document = core.create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        party.id,
        amount,
        document_date=day,
    )
    core.post_sales_invoice(session, business.tenant.id, document.id)
    return document


def _order(session, business, party, number, total, currency="EUR"):
    _, document, _, commitments = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        party.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "4",
                "unit_price": str(Decimal(total) / 4),
                "gross_amount": total,
            }
        ],
        total,
        currency=currency,
    )
    return document, commitments


def _holds(session, business, commitments):
    return active_credit_holds(
        session, business.tenant.id, [commitment.id for commitment in commitments]
    )


def test_an_order_past_the_limit_is_held_with_its_facts(session, business):
    party = _customer(session, business)
    _open_invoice(session, business, party, "700.00")
    # Positive control: an order that stays within the limit is not held.
    _, within = _order(session, business, party, "SO-C-OK", "200.00")
    assert _holds(session, business, within) == []

    _, over = _order(session, business, party, "SO-C-OVER", "400.00")

    (hold,) = _holds(session, business, over)
    assert (hold.reason_code, hold.created_by) == ("credit_check", "credit_limit")
    assert hold.note.startswith("Credit limit 1000.00 EUR exceeded by 300.00")
    assert "overdue RE-C-1 700.00" in hold.note
    assert "this order 400.00" in hold.note
    event = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.event_type == "commitment.held",
            BusinessEvent.subject_id == over[0].id,
        )
    ).one()
    facts = json.loads(event.payload)["credit"]
    assert (Decimal(facts["exposure"]), Decimal(facts["order_value"])) == (
        Decimal(1300),
        Decimal(400),
    )
    assert [row["number"] for row in facts["overdue_invoices"]["rows"]] == ["RE-C-1"]


def test_a_held_promise_is_not_ready_to_ship(session, business):
    party = _customer(session, business, limit="100")
    _, over = _order(session, business, party, "SO-C-SHIP", "400.00")

    readiness = fulfillment_readiness(session, business.tenant.id, over[0].id)

    assert "commitment_hold" in readiness.blocker_codes


@pytest.mark.parametrize(("limit", "currency"), [("0", "EUR"), ("100", "USD")])
def test_no_limit_or_another_currency_holds_nothing(session, business, limit, currency):
    party = _customer(session, business, limit=limit)
    _, commitments = _order(session, business, party, "SO-C-NONE", "400.00", currency)

    assert _holds(session, business, commitments) == []


def test_the_reviewed_order_tool_holds_too(session, business):
    party = _customer(session, business, limit="100")
    proposal = prepare_delivery_action(
        session,
        business.tenant.id,
        "order_create",
        {
            "direction": "sales",
            "number": "SO-C-TOOL",
            "company_party_id": business.company.id,
            "counterparty_id": party.id,
            "location_id": business.location.id,
            "currency": "EUR",
            "gross_amount": "400.00",
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "4",
                    "unit_price": "100.00",
                    "gross_amount": "400.00",
                }
            ],
        },
        request_id="order-credit-tool",
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    commitment_ids = json.loads(executed.output)["commitment_ids"]

    assert len(active_credit_holds(session, business.tenant.id, commitment_ids)) == 1


def _shop_order(order_id, customer_sku, price="100.00"):
    return {
        "id": order_id,
        "name": f"#{order_id}",
        "currency": "EUR",
        "total_price": str(Decimal(price) * 4),
        "created_at": "2026-09-20T10:00:00Z",
        "updated_at": "2026-09-20T10:00:00Z",
        "line_items": [
            {"id": order_id * 10, "sku": customer_sku, "quantity": 4, "price": price}
        ],
    }


def test_a_shop_order_past_the_limit_is_held_once_even_when_replayed(
    session, business
):
    tenant = business.tenant.id
    party = _customer(session, business, limit="100")

    def intake():
        _, job = core.enqueue_shopify_order(
            session,
            tenant,
            _shop_order(9901, business.item.sku),
            business.company.id,
            party.id,
            business.location.id,
        )
        return core.process_import_job(session, tenant, job.id)

    interpreted = intake()
    commitments = interpreted[3]
    assert len(_holds(session, business, commitments)) == 1

    intake()

    assert len(_holds(session, business, commitments)) == 1


def test_a_file_order_past_the_limit_is_held(session, business, tmp_path, monkeypatch):
    import csv

    from reality.services.artifacts import stage_artifact
    from reality.services.file_interpreters import suggested_mapping
    from reality.tools.application import confirm_tool, propose_tool

    tenant = business.tenant.id
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    party = _customer(session, business, limit="100")
    path = tmp_path / "orders.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        columns = ["order_id", "order_number", "party_name", "sku", "quantity"]
        writer.writerow([*columns, "unit_price", "currency", "location"])
        writer.writerow(
            ["F-1", "AB-F-1", party.name, business.item.sku, "4", "100.00", "EUR"]
            + [business.location.name]
        )
    header = next(csv.reader(path.open(encoding="utf-8")))
    with path.open("rb") as handle:
        artifact, _ = stage_artifact(
            session, tenant, handle, filename=path.name, content_type="text/csv"
        )
    proposal = propose_tool(
        session,
        tenant,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "erp_export",
            "source_type": "order",
            "expected_target": "sales_order",
            "column_mapping": suggested_mapping(header, "sales_order"),
        },
    )
    job_id = json.loads(confirm_tool(session, tenant, proposal.id).output)[
        "import_job_id"
    ]
    core.process_import_job(session, tenant, job_id)

    holds = session.scalars(
        select(CommitmentHold).where(
            CommitmentHold.tenant_id == tenant,
            CommitmentHold.reason_code == "credit_check",
        )
    ).all()
    assert len(holds) == 1


def test_a_credit_hold_is_added_beside_another_hold(session, business):
    tenant = business.tenant.id
    party = _customer(session, business, limit="0")
    _, commitments = _order(session, business, party, "SO-C-ADDR", "400.00")
    address = core.hold_commitment(
        session, tenant, commitments[0].id, "address_clarification", "Street unclear"
    )
    from reality.services.credit_exposure import credit_exposure

    placed = place_credit_holds(
        session,
        tenant,
        commitments,
        credit_exposure(session, tenant, party.id),
        Decimal("400"),
    )

    assert len(placed) == 1
    active = session.scalars(
        select(CommitmentHold).where(
            CommitmentHold.tenant_id == tenant,
            CommitmentHold.commitment_id == commitments[0].id,
            CommitmentHold.released_at.is_(None),
        )
    ).all()
    assert {hold.id for hold in active} == {address.id, placed[0].id}


def test_an_assigned_line_of_a_credit_held_order_is_held(session, business):
    from reality.services.order_line_items import assign_line_item

    tenant = business.tenant.id
    party = _customer(session, business, limit="100")
    helmet = core.create_item(session, tenant, "HELMET-C", "Helmet")
    payload = _shop_order(9902, business.item.sku)
    payload["line_items"].append(
        {"id": 99021, "sku": "HELMET-C?", "quantity": 1, "price": "10.00"}
    )
    _, job = core.enqueue_shopify_order(
        session, tenant, payload, business.company.id, party.id, business.location.id
    )
    _, _, lines, commitments = core.process_import_job(session, tenant, job.id)
    assert len(_holds(session, business, commitments)) == 1
    unknown = next(line for line in lines if line.item_id is None)

    assign_line_item(session, tenant, document_line_id=unknown.id, item_id=helmet.id)

    assigned = session.scalars(
        select(core.Commitment).where(
            core.Commitment.tenant_id == tenant,
            core.Commitment.document_line_id == unknown.id,
        )
    ).one()
    assert len(_holds(session, business, [assigned])) == 1
