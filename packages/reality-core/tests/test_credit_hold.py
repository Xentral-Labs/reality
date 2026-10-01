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


def test_a_shop_order_past_the_limit_is_held_once_even_when_replayed(session, business):
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
        Decimal(400),
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


# --- Release (FR-004) ----------------------------------------------------------------


def _person(session, business, role):
    from reality.db.core import AppUser, TenantMembership, uid
    from reality.services.memberships import Principal

    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="x",
        display_name=f"{role.title()} Person",
        status="active",
        email_verified_at=core.now(),
    )
    session.add(user)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("mem"),
            tenant_id=business.tenant.id,
            user_id=user.id,
            role=role,
            status="active",
        )
    )
    session.flush()
    return Principal(user.id)


def _prepare_release(session, business, order, reason, request_id="credit-release"):
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "credit_hold_release",
        {"document_id": order.id, "reason": reason},
        request_id=request_id,
    )


def _confirm(session, business, proposal, principal=None):
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=token,
        confirmed=True,
        confirming_principal=principal,
    )


def _held_order(session, business):
    party = _customer(session, business, limit="100")
    order, commitments = _order(session, business, party, "SO-C-REL", "400.00")
    assert len(_holds(session, business, commitments)) == 1
    return order, commitments


def test_an_owner_releases_a_credit_hold_with_a_reason(session, business):
    from reality.services.decision_attribution import record_decisions

    tenant = business.tenant.id
    order, commitments = _held_order(session, business)
    owner = _person(session, business, "owner")
    reason = "Paid by bank transfer today, confirmed by phone"

    proposal = _prepare_release(session, business, order, reason)
    review = json.loads(proposal.input)["_delivery_review"]
    assert (
        review["effect"]["holds_released"],
        review["state"]["exposure"]["excess"],
    ) == (
        "1",
        "300.0000",
    )
    executed = _confirm(session, business, proposal, owner)

    assert executed.status == "executed"
    assert _holds(session, business, commitments) == []
    event = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.event_type == "commitment.hold_released",
            BusinessEvent.action_id == proposal.id,
        )
    ).one()
    assert json.loads(event.payload)["reason"] == reason
    decisions = record_decisions(session, tenant, "commitment", commitments[0].id)
    assert (proposal.id, "credit_hold_release") in {
        (row["id"], row["tool"]) for row in decisions
    }
    # Released, the order is ready once stock is reserved.
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    core.reserve(session, tenant, commitments[0].id)
    assert fulfillment_readiness(session, tenant, commitments[0].id).ship_ready


@pytest.mark.parametrize("reason", ["", "   "])
def test_a_credit_hold_is_released_only_with_a_reason(session, business, reason):
    order, _ = _held_order(session, business)

    with pytest.raises(core.InvalidOperation) as refused:
        _prepare_release(session, business, order, reason)
    assert refused.value.code == "credit_hold_release_reason_missing"


def test_a_member_who_is_not_an_owner_cannot_release_it(session, business):
    order, commitments = _held_order(session, business)
    member = _person(session, business, "member")
    proposal = _prepare_release(session, business, order, "Customer is fine")

    with pytest.raises(core.InvalidOperation) as refused:
        _confirm(session, business, proposal, member)

    assert refused.value.code == "company_owner_access_required"
    assert len(_holds(session, business, commitments)) == 1


def test_an_order_without_a_credit_hold_has_nothing_to_release(session, business):
    party = _customer(session, business, limit="0")
    order, _ = _order(session, business, party, "SO-C-FREE", "400.00")

    with pytest.raises(core.InvalidOperation) as refused:
        _prepare_release(session, business, order, "Nothing to release")
    assert refused.value.code == "credit_hold_not_found"


def test_the_generic_release_leaves_the_credit_hold(session, business):
    tenant = business.tenant.id
    _, commitments = _held_order(session, business)

    # With only the credit hold active, the generic release refuses.
    with pytest.raises(core.InvalidOperation) as refused:
        prepare_delivery_action(
            session,
            tenant,
            "commitment_hold_release",
            {"commitment_id": commitments[0].id},
            request_id="generic-release",
        )
    assert refused.value.code == "credit_hold_owner_release_required"

    # Beside another hold, it lifts that one and keeps the credit hold.
    address = CommitmentHold(
        id=core.uid("hld"),
        tenant_id=tenant,
        commitment_id=commitments[0].id,
        reason_code="address_clarification",
        note="Street unclear",
    )
    session.add(address)
    session.flush()
    proposal = prepare_delivery_action(
        session,
        tenant,
        "commitment_hold_release",
        {"commitment_id": commitments[0].id},
        request_id="generic-release-2",
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True
    )

    assert address.released_at is not None
    assert len(_holds(session, business, commitments)) == 1


def test_cancelling_the_order_still_releases_every_hold(session, business):
    tenant = business.tenant.id
    _, commitments = _held_order(session, business)

    core.cancel_commitment(
        session, tenant, commitments[0].id, reason="Customer cancelled"
    )

    assert _holds(session, business, commitments) == []


# --- One exposure everywhere (FR-005, SC-003) -------------------------------------


def _finding(session, business, party):
    from reality.services.exceptions import operational_exceptions

    return next(
        (
            row
            for row in operational_exceptions(session, business.tenant.id)
            if row.class_id == "credit_limit_exceeded" and row.record_id == party.id
        ),
        None,
    )


def test_the_finding_reports_the_exposure_the_hold_used(session, business):
    from reality.services.credit_exposure import credit_exposure

    tenant = business.tenant.id
    party = _customer(session, business)
    overdue = _open_invoice(session, business, party, "700.00")
    _open_invoice(
        session,
        business,
        party,
        "150.00",
        day=core.now().date().isoformat(),
        number="RE-C-2",
    )
    # Positive control: within the limit there is no finding.
    assert _finding(session, business, party) is None

    _, over = _order(session, business, party, "SO-C-FIND", "400.00")

    finding = _finding(session, business, party)
    exposure = credit_exposure(session, tenant, party.id)
    assert finding.causal_values["outstanding_amount"] == exposure["exposure"]
    assert finding.causal_values["excess_amount"] == exposure["excess"]
    assert finding.causal_values["open_orders_amount"] == Decimal("400.00")
    # The overdue invoice is named; the one due today is not.
    assert finding.causal_values["overdue_document_ids"] == [overdue.id]
    assert finding.causal_values["overdue_amount"] == Decimal("700.0000")
    (hold,) = _holds(session, business, over)
    assert f"exposure {Decimal(exposure['exposure']).quantize(Decimal('0.01'))}" in (
        hold.note
    )


def test_an_available_credit_lowers_the_finding(session, business):
    party = _customer(session, business)
    _open_invoice(session, business, party, "1100.00")
    assert _finding(session, business, party) is not None

    note = core.create_document(
        session, business.tenant.id, "credit_note", "GS-C-1", party.id, "200.00"
    )
    core.post_sales_credit_note(session, business.tenant.id, note.id)

    assert _finding(session, business, party) is None


# --- Review round (spec 298) ----------------------------------------------------------


def test_every_generic_release_path_keeps_the_credit_hold(session, business):
    from reality.tools.application import confirm_tool, propose_tool

    tenant = business.tenant.id
    order, commitments = _held_order(session, business)
    address = CommitmentHold(
        id=core.uid("hld"),
        tenant_id=tenant,
        commitment_id=commitments[0].id,
        reason_code="address_clarification",
        note="Street unclear",
    )
    session.add(address)
    session.flush()

    # The document release through the chat tool lifts the address hold only.
    proposal = propose_tool(
        session, tenant, "document_hold_release", {"document_id": order.id}
    )
    confirm_tool(session, tenant, proposal.id)
    assert address.released_at is not None
    assert len(_holds(session, business, commitments)) == 1

    # The service the web endpoint and the CLI call keeps it too.
    core.release_commitment_hold(session, tenant, commitments[0].id)
    core.release_document_holds(session, tenant, order.id)
    assert len(_holds(session, business, commitments)) == 1


def test_the_generic_release_is_verified_when_it_keeps_a_credit_hold(session, business):
    from reality.services.delivery_actions import delivery_proposal_detail

    tenant = business.tenant.id
    _, commitments = _held_order(session, business)
    session.add(
        CommitmentHold(
            id=core.uid("hld"),
            tenant_id=tenant,
            commitment_id=commitments[0].id,
            reason_code="customer_request",
            note="Wait for the customer",
        )
    )
    session.flush()
    proposal = prepare_delivery_action(
        session,
        tenant,
        "commitment_hold_release",
        {"commitment_id": commitments[0].id},
        request_id="generic-verified",
    )
    _confirm(session, business, proposal)

    detail = delivery_proposal_detail(session, tenant, proposal.id)
    assert detail["verification"] == "verified"
    assert json.loads(proposal.input)["_delivery_review"]["effect"] == {
        "holds_released": "1",
        "credit_holds_kept": "1",
    }


def test_the_order_value_is_its_stated_amount_not_quantity_times_price(
    session, business
):
    party = _customer(session, business, limit="300")
    # Four at a list price of 100 with a stated rebate to 200 in total.
    _, _, _, commitments = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "SO-C-REBATE",
        business.company.id,
        party.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "4",
                "unit_price": "100.00",
                "gross_amount": "200.00",
            }
        ],
        "200.00",
    )
    from reality.services.credit_exposure import credit_exposure

    assert credit_exposure(session, business.tenant.id, party.id)["open_orders"][
        "amount"
    ] == Decimal("200.00")
    assert _holds(session, business, commitments) == []
    # Positive control: another 200 takes it past 300.
    _, more = _order(session, business, party, "SO-C-MORE", "200.00")
    assert len(_holds(session, business, more)) == 1


def test_a_cancelled_order_stops_counting_its_service_line(session, business):
    from reality.services.credit_exposure import credit_exposure

    tenant = business.tenant.id
    party = _customer(session, business, limit="10000")
    _, job = core.enqueue_shopify_order(
        session,
        tenant,
        {
            "id": 9951,
            "name": "#9951",
            "currency": "EUR",
            "total_price": "215.00",
            "created_at": "2026-09-20T10:00:00Z",
            "updated_at": "2026-09-20T10:00:00Z",
            "line_items": [
                {"id": 1, "sku": business.item.sku, "quantity": 2, "price": "100.00"},
                {
                    "id": 2,
                    "sku": "",
                    "quantity": 1,
                    "price": "15.00",
                    "requires_shipping": False,
                    "title": "Gift wrap",
                },
            ],
        },
        business.company.id,
        party.id,
        business.location.id,
    )
    _, _, _, commitments = core.process_import_job(session, tenant, job.id)
    # Positive control: while the order is open its service line counts.
    assert credit_exposure(session, tenant, party.id)["open_orders"][
        "amount"
    ] == Decimal("215.00")

    for commitment in commitments:
        core.cancel_commitment(session, tenant, commitment.id, reason="Cancelled")

    assert credit_exposure(session, tenant, party.id)["open_orders"]["amount"] == 0


def test_an_order_revised_upwards_past_the_limit_is_held(session, business):
    party = _customer(session, business, limit="500")
    _, commitments = _order(session, business, party, "SO-C-UP", "400.00")
    assert _holds(session, business, commitments) == []

    core.revise_commitment(
        session, business.tenant.id, commitments[0].id, quantity="8", note="More"
    )

    assert len(_holds(session, business, commitments)) == 1


def test_the_exposure_read_does_not_grow_with_the_order_lines(session, business):
    from sqlalchemy import event

    from reality.services.credit_exposure import credit_exposure

    tenant = business.tenant.id
    party = _customer(session, business, limit="0")

    def order_with(lines, number):
        core.create_manual_order(
            session,
            tenant,
            "sales",
            number,
            business.company.id,
            party.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit_price": "10.00",
                    "gross_amount": "10.00",
                }
                for _ in range(lines)
            ],
            str(10 * lines),
        )

    def statements():
        count = 0

        def tick(*_):
            nonlocal count
            count += 1

        event.listen(session.bind, "before_cursor_execute", tick)
        try:
            credit_exposure(session, tenant, party.id)
        finally:
            event.remove(session.bind, "before_cursor_execute", tick)
        return count

    order_with(2, "SO-C-Q1")
    few = statements()
    order_with(40, "SO-C-Q2")

    assert statements() <= few + 2


def test_the_delivery_case_says_which_hold_only_an_owner_releases(session, business):
    from reality.services.delivery_reads import delivery_case

    tenant = business.tenant.id
    _, commitments = _held_order(session, business)
    session.add(
        CommitmentHold(
            id=core.uid("hld"),
            tenant_id=tenant,
            commitment_id=commitments[0].id,
            reason_code="credit_check",
            note="Placed by hand",
        )
    )
    session.flush()

    blockers = delivery_case(session, tenant, commitments[0].id)["case"]["blockers"]

    # The credit check's own hold is the owner's; the one a person placed is not.
    assert sorted((row["note"][:6], row["owner_release"]) for row in blockers) == [
        ("Credit", True),
        ("Placed", False),
    ]
