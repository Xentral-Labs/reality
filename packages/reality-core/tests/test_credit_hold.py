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
    """
    BUSINESS TEST:
    An order past the limit is held with its facts.
    GIVEN:
    Customer limit 1000 and overdue invoice 700 exist.
    WHEN:
    Create orders 200 and then 400.
    THEN:
    First order has no credit hold; second has one with exposure 1300, excess 300, order value and overdue invoice evidence.
    """
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
    """
    BUSINESS TEST:
    A held promise is not ready to ship.
    GIVEN:
    Order 400 exceeds customer limit 100.
    WHEN:
    Read fulfillment readiness for its commitment.
    THEN:
    Readiness reports a commitment-hold blocker.
    """
    party = _customer(session, business, limit="100")
    _, over = _order(session, business, party, "SO-C-SHIP", "400.00")

    readiness = fulfillment_readiness(session, business.tenant.id, over[0].id)

    assert "commitment_hold" in readiness.blocker_codes


@pytest.mark.parametrize("currency", ["EUR", "USD"])
def test_no_limit_holds_nothing_in_any_currency(session, business, currency):
    """
    BUSINESS TEST:
    No limit holds nothing in any currency.
    GIVEN:
    Customer limit is zero; currency parameter is EUR or USD.
    WHEN:
    Create order 400 in that currency.
    THEN:
    No credit hold is created.
    """
    party = _customer(session, business, limit="0")
    _, commitments = _order(session, business, party, "SO-C-NONE", "400.00", currency)

    assert _holds(session, business, commitments) == []


def test_an_order_in_another_currency_waits_for_a_person(session, business):
    """
    Spec 341: a limit in EUR cannot count a USD order without converting.

    BUSINESS TEST:
    An order in another currency waits for a person.
    GIVEN:
    Customer limit 1000 EUR and order 200 EUR exist.
    WHEN:
    Create a 50 USD order.
    THEN:
    A review hold names currency mismatch; USD order is excluded from EUR exposure and no numeric limit breach is claimed.
    """
    party = _customer(session, business, limit="1000")
    # Positive control: an order in the limit's currency within it is not held.
    _, within = _order(session, business, party, "SO-C-EUR", "200.00")
    assert _holds(session, business, within) == []

    _, other = _order(session, business, party, "SO-C-USD", "50.00", "USD")

    (hold,) = _holds(session, business, other)
    assert (hold.reason_code, hold.created_by) == ("credit_check", "credit_limit")
    assert hold.note.startswith("Credit limit 1000.00 EUR is stated in EUR")
    assert "this order is in USD" in hold.note
    assert "a person decides (exposure in EUR 200.00)" in hold.note
    event = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.event_type == "commitment.held",
            BusinessEvent.subject_id == other[0].id,
        )
    ).one()
    facts = json.loads(event.payload)["credit"]
    assert facts["order_currency"] == "USD"
    assert [row["number"] for row in facts["not_counted"]] == ["SO-C-USD"]
    # The limit itself is judged in EUR only: this order does not put it over.
    assert facts["over_limit"] is False


def test_an_owner_releases_a_currency_hold_and_a_raise_asks_again(session, business):
    """
    BUSINESS TEST:
    An owner releases a currency hold and a raise asks again.
    GIVEN:
    A USD order has a currency credit hold and an owner principal exists.
    WHEN:
    Confirm reasoned release, then raise commitment quantity to 8.
    THEN:
    Release executes and clears hold; revision creates another credit hold.
    """
    tenant = business.tenant.id
    party = _customer(session, business, limit="1000")
    order, commitments = _order(session, business, party, "SO-C-USD-R", "50.00", "USD")
    owner = _person(session, business, "owner")

    proposal = _prepare_release(session, business, order, "Agreed in USD by phone")
    assert _confirm(session, business, proposal, owner).status == "executed"
    assert _holds(session, business, commitments) == []

    # Raising the order adds credit nobody has judged yet, so it waits again.
    core.revise_commitment(
        session, tenant, commitments[0].id, quantity="8", note="More"
    )
    assert len(_holds(session, business, commitments)) == 1


def test_the_reviewed_order_tool_holds_too(session, business):
    """
    BUSINESS TEST:
    The reviewed order tool holds too.
    GIVEN:
    Customer limit 100 and reviewed order proposal 400 exist.
    WHEN:
    Approve order creation with its review token.
    THEN:
    Created commitments carry one active credit hold.
    """
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
    """
    BUSINESS TEST:
    A shop order past the limit is held once even when replayed.
    GIVEN:
    Shopify order 400 is imported for customer limit 100.
    WHEN:
    Process the order and replay the same intake.
    THEN:
    Exactly one active credit hold remains after each intake.
    """
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
    """
    BUSINESS TEST:
    A file order past the limit is held.
    GIVEN:
    CSV order states four items at 100 EUR for customer limit 100.
    WHEN:
    Stage file, confirm mapped source intake and process import job.
    THEN:
    One credit-check hold is recorded.
    """
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
    """
    BUSINESS TEST:
    A credit hold is added beside another hold.
    GIVEN:
    An order commitment already has an address-clarification hold.
    WHEN:
    Explicitly place credit holds using its current exposure.
    THEN:
    A new credit hold is added and both original and new holds remain active.
    """
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
    """
    BUSINESS TEST:
    An assigned line of a credit held order is held.
    GIVEN:
    Imported over-limit order has one unknown item line and an existing credit hold.
    WHEN:
    Assign that line to a known item.
    THEN:
    The new commitment receives a credit hold with the original order hold note.
    """
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
    (order_hold,) = _holds(session, business, commitments)
    unknown = next(line for line in lines if line.item_id is None)

    assign_line_item(session, tenant, document_line_id=unknown.id, item_id=helmet.id)

    assigned = session.scalars(
        select(core.Commitment).where(
            core.Commitment.tenant_id == tenant,
            core.Commitment.document_line_id == unknown.id,
        )
    ).one()
    (assigned_hold,) = _holds(session, business, [assigned])
    # The line waits for the same decision, with the same reason (spec 341).
    assert assigned_hold.note == order_hold.note


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
    """
    BUSINESS TEST:
    An owner releases a credit hold with a reason.
    GIVEN:
    Order 400 exceeds limit 100 and an owner supplies a reason.
    WHEN:
    Confirm reviewed release, inspect event/decision, add stock and reserve.
    THEN:
    Hold clears, reason and proposal attribution remain traceable, and commitment becomes ship-ready.
    """
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
    """
    BUSINESS TEST:
    A credit hold is released only with a reason.
    GIVEN:
    A credit-held order exists; reason parameter is empty or whitespace.
    WHEN:
    Prepare credit-hold release.
    THEN:
    Refusal code is credit_hold_release_reason_missing.
    """
    order, _ = _held_order(session, business)

    with pytest.raises(core.InvalidOperation) as refused:
        _prepare_release(session, business, order, reason)
    assert refused.value.code == "credit_hold_release_reason_missing"


def test_a_member_who_is_not_an_owner_cannot_release_it(session, business):
    """
    BUSINESS TEST:
    A member who is not an owner cannot release it.
    GIVEN:
    A credit-held order has a release proposal and a member principal.
    WHEN:
    Confirm as the member.
    THEN:
    Company-owner access is required and the credit hold remains.
    """
    order, commitments = _held_order(session, business)
    member = _person(session, business, "member")
    proposal = _prepare_release(session, business, order, "Customer is fine")

    with pytest.raises(core.InvalidOperation) as refused:
        _confirm(session, business, proposal, member)

    assert refused.value.code == "company_owner_access_required"
    assert len(_holds(session, business, commitments)) == 1


def test_an_order_without_a_credit_hold_has_nothing_to_release(session, business):
    """
    BUSINESS TEST:
    An order without a credit hold has nothing to release.
    GIVEN:
    An order for a customer with no limit has no credit hold.
    WHEN:
    Prepare credit-hold release.
    THEN:
    Refusal code is credit_hold_not_found.
    """
    party = _customer(session, business, limit="0")
    order, _ = _order(session, business, party, "SO-C-FREE", "400.00")

    with pytest.raises(core.InvalidOperation) as refused:
        _prepare_release(session, business, order, "Nothing to release")
    assert refused.value.code == "credit_hold_not_found"


def test_the_generic_release_leaves_the_credit_hold(session, business):
    """
    BUSINESS TEST:
    The generic release leaves the credit hold.
    GIVEN:
    A credit-held commitment first has no other hold, then gains an address hold.
    WHEN:
    Prepare generic release before and after adding address hold, then confirm.
    THEN:
    Credit-only release is refused; generic release clears the address hold and retains credit hold.
    """
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
    """
    BUSINESS TEST:
    Cancelling the order still releases every hold.
    GIVEN:
    An order commitment is credit-held.
    WHEN:
    Cancel the commitment with a reason.
    THEN:
    No active credit hold remains.
    """
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
    """
    BUSINESS TEST:
    The finding reports the exposure the hold used.
    GIVEN:
    Customer limit 1000 has invoices 700 overdue and 150 current.
    WHEN:
    Create order 400 and inspect exception, exposure and hold.
    THEN:
    Exception values agree with exposure, open order and overdue evidence; hold note contains that exposure.
    """
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
    """
    BUSINESS TEST:
    An available credit lowers the finding.
    GIVEN:
    Customer limit 1000 has an invoice 1100 and a limit-exceeded finding.
    WHEN:
    Post a credit note 200.
    THEN:
    The limit-exceeded finding disappears.
    """
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
    """
    BUSINESS TEST:
    Every generic release path keeps the credit hold.
    GIVEN:
    Credit-held order also has an address hold.
    WHEN:
    Confirm document release, then invoke generic commitment and document release services.
    THEN:
    Address hold clears but credit hold remains through every path.
    """
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
    """
    BUSINESS TEST:
    The generic release is verified when it keeps a credit hold.
    GIVEN:
    Credit-held commitment also has a customer-request hold.
    WHEN:
    Confirm generic release and inspect verification.
    THEN:
    Result is verified and effect states one hold released and one credit hold kept.
    """
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
    """
    BUSINESS TEST:
    The order value is its stated amount not quantity times price.
    GIVEN:
    Customer limit 300; four units have price 100 but stated gross amount 200.
    WHEN:
    Read exposure and create another order 200.
    THEN:
    First order counts 200 and has no hold; second order crosses the limit and is held.
    """
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
    """
    BUSINESS TEST:
    A cancelled order stops counting its service line.
    GIVEN:
    Imported order 215 includes physical goods 200 and service line 15.
    WHEN:
    Read exposure, cancel every commitment and read again.
    THEN:
    Open order amount changes from 215 to zero, including the service line.
    """
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
    """
    BUSINESS TEST:
    An order revised upwards past the limit is held.
    GIVEN:
    Order 400 is below customer limit 500.
    WHEN:
    Raise commitment quantity from four to eight.
    THEN:
    A credit hold is created after revision.
    """
    party = _customer(session, business, limit="500")
    _, commitments = _order(session, business, party, "SO-C-UP", "400.00")
    assert _holds(session, business, commitments) == []

    core.revise_commitment(
        session, business.tenant.id, commitments[0].id, quantity="8", note="More"
    )

    assert len(_holds(session, business, commitments)) == 1


def test_the_exposure_read_does_not_grow_with_the_order_lines(session, business):
    """
    BUSINESS TEST:
    The exposure read does not grow with the order lines.
    GIVEN:
    A customer has an order with two lines and later another with forty lines.
    WHEN:
    Count database statements for exposure reads before and after.
    THEN:
    Later read uses no more than two additional statements.
    """
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
    """
    BUSINESS TEST:
    The delivery case says which hold only an owner releases.
    GIVEN:
    Commitment has automatic credit hold and manually placed credit-check hold.
    WHEN:
    Read delivery case blockers.
    THEN:
    Automatic hold requires owner release; manually placed hold does not.
    """
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
