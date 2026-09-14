"""Causal event prerequisites for the real Playground recorder (096/FR-005)."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import BusinessEvent, ChangeProposal, Movement, Reservation, uid
from reality.services.core import (
    NotFound,
    active_reserved,
    create_commitment,
    create_tenant,
    open_quantity,
    record_movement,
    stock_at,
)
from reality.tools.application import confirm_tool, propose_tool


def opening_arguments(engine, run_id):
    from sqlalchemy.orm import Session

    from reality.db.core import PlaygroundRun

    with Session(engine) as session:
        references = session.get(PlaygroundRun, run_id).initialization_progress
        return {
            "movement_type": "opening_stock",
            "item_id": references["items"]["BIKE-LIGHT"],
            "to_location_id": references["locations"]["warehouse"],
            "quantity": "20",
        }


@pytest.mark.parametrize("tamper", [None, "quantity", "action", "from", "source"])
def test_purchase_partial_receipts_continue_in_same_sandbox(
    durable_playground, monkeypatch, tamper
):
    from sqlalchemy.orm import Session

    from reality.db.core import PlaygroundRun
    from reality.services.core import InvalidOperation
    from reality.services.playground import confirm_step, prepare_step
    from reality.services.tenant_policy import PlaygroundOperationDenied

    engine, owner, run_id = durable_playground
    with Session(engine) as session:
        run = session.get(PlaygroundRun, run_id)
        tenant_id, refs = run.tenant_id, run.initialization_progress

    def execute(key, tool, args):
        proposal = prepare_step(engine, owner, run_id, key, tool, args)
        result = confirm_step(
            engine,
            owner,
            run_id,
            proposal["step_id"],
            proposal["preview"]["revision"],
            confirmed=True,
        )
        assert result["status"] == "executed", result
        assert result["receipt"] is not None
        return result, proposal

    order, _ = execute(
        "purchase",
        "order_create",
        {
            "direction": "purchase",
            "number": "PO-1",
            "company_party_id": refs["parties"]["company"],
            "counterparty_id": refs["parties"]["supplier"],
            "location_id": refs["locations"]["warehouse"],
            "item_id": refs["items"]["BIKE-LIGHT"],
            "quantity": "10",
            "unit_price": "8",
        },
    )
    commitment = next(
        r["id"] for r in order["receipt"]["records"] if r["family"] == "commitment"
    )
    args = {
        "movement_type": "receipt",
        "commitment_id": commitment,
        "item_id": refs["items"]["BIKE-LIGHT"],
        "to_location_id": refs["locations"]["warehouse"],
        "quantity": "4",
    }
    with Session(engine) as session:
        assert (
            stock_at(session, tenant_id, args["item_id"], args["to_location_id"]) == 0
        )
        assert open_quantity(session, tenant_id, commitment) == 10
    for change in (
        {"quantity": "11"},
        {"item_id": refs["items"]["HELMET"]},
        {"from_location_id": args["to_location_id"]},
    ):
        with pytest.raises(InvalidOperation):
            prepare_step(
                engine,
                owner,
                run_id,
                uid("invalid"),
                "movement_create",
                {**args, **change},
            )
    with pytest.raises(NotFound):
        prepare_step(
            engine,
            owner,
            run_id,
            "foreign",
            "movement_create",
            {**args, "commitment_id": "com_foreign"},
        )
    preview = prepare_step(engine, owner, run_id, "receive-4", "movement_create", args)
    with pytest.raises(PlaygroundOperationDenied):
        confirm_step(
            engine,
            owner,
            run_id,
            preview["step_id"],
            preview["preview"]["revision"],
            confirmed=False,
        )
    from reality.services.core import Conflict

    with pytest.raises(Conflict):
        confirm_step(
            engine, owner, run_id, preview["step_id"], "altered", confirmed=True
        )
    if tamper:
        from dataclasses import replace

        from reality.tools import application

        original = application.TOOLS["movement_create"]

        def misuse(session, tenant, arguments):
            changed = dict(arguments)
            changed.update(
                {
                    "quantity": {"quantity": "5"},
                    "action": {"_action_id": None},
                    "from": {"from_location_id": args["to_location_id"]},
                    "source": {"source_record_id": "src_unreviewed"},
                }[tamper]
            )
            return original.handler(session, tenant, changed)

        monkeypatch.setitem(
            application.TOOLS, "movement_create", replace(original, handler=misuse)
        )
        denied = confirm_step(
            engine,
            owner,
            run_id,
            preview["step_id"],
            preview["preview"]["revision"],
            confirmed=True,
        )
        assert denied["status"] == "executing"
        with Session(engine) as session:
            assert (
                session.scalar(
                    select(Movement.id).where(Movement.tenant_id == tenant_id)
                )
                is None
            )
        return
    partial, preview = execute("receive-4", "movement_create", args)
    assert partial["receipt"]["after"]["open_quantity"] == "6.0000"
    replay = confirm_step(
        engine,
        owner,
        run_id,
        preview["step_id"],
        preview["preview"]["revision"],
        confirmed=True,
    )
    assert replay["receipt"] == partial["receipt"]
    final, _ = execute("receive-6", "movement_create", {**args, "quantity": "6"})
    assert Decimal(final["receipt"]["after"]["open_quantity"]) == 0
    assert final["receipt"]["event_ids"]
    with Session(engine) as session:
        assert (
            stock_at(session, tenant_id, args["item_id"], args["to_location_id"]) == 10
        )
        assert open_quantity(session, tenant_id, commitment) == 0
        assert (
            len(
                list(
                    session.scalars(
                        select(Movement).where(Movement.tenant_id == tenant_id)
                    )
                )
            )
            == 2
        )
    with pytest.raises(InvalidOperation):
        prepare_step(engine, owner, run_id, "too-late", "movement_create", args)
    line_id = next(
        r["id"] for r in order["receipt"]["records"] if r["family"] == "document_line"
    )
    invoice_args = {
        "order_line_id": line_id,
        "quantity": "10",
        "gross_amount": "81",
        "number": "SUP-1",
    }
    with pytest.raises(InvalidOperation):
        prepare_step(
            engine,
            owner,
            run_id,
            "wrong-invoice-type",
            "sales_invoice_record",
            invoice_args,
        )
    invoice, _ = execute("supplier-invoice", "supplier_invoice_record", invoice_args)
    invoice_id = next(
        r["id"] for r in invoice["receipt"]["records"] if r["family"] == "document"
    )
    assert Decimal(invoice["receipt"]["after"]["open_amount"]) == 81
    payment_args = {
        "invoice_id": invoice_id,
        "amount": "31",
        "payment_number": "SUP-PAY-1",
    }
    for tool, changes in [
        ("customer_payment_post", {}),
        ("supplier_payment_post", {"amount": "82"}),
    ]:
        with pytest.raises(InvalidOperation):
            prepare_step(
                engine,
                owner,
                run_id,
                uid("invalid-finance"),
                tool,
                {**payment_args, **changes},
            )
    paid, paid_preview = execute(
        "supplier-payment", "supplier_payment_post", payment_args
    )
    assert Decimal(paid["receipt"]["after"]["open_amount"]) == 50
    replay = confirm_step(
        engine,
        owner,
        run_id,
        paid_preview["step_id"],
        paid_preview["preview"]["revision"],
        confirmed=True,
    )
    assert replay["receipt"] == paid["receipt"]
    customer_order, _ = execute(
        "customer-after-purchase",
        "order_create",
        {
            "direction": "sales",
            "number": "SO-AFTER-PURCHASE",
            "company_party_id": refs["parties"]["company"],
            "counterparty_id": refs["parties"]["customer_huber"],
            "location_id": refs["locations"]["warehouse"],
            "item_id": args["item_id"],
            "quantity": "1",
            "unit_price": "25",
        },
    )
    customer_commitment = next(
        r["id"]
        for r in customer_order["receipt"]["records"]
        if r["family"] == "commitment"
    )
    with pytest.raises(InvalidOperation):
        prepare_step(
            engine,
            owner,
            run_id,
            "customer-not-supplier",
            "movement_create",
            {**args, "commitment_id": customer_commitment, "quantity": "1"},
        )
    with Session(engine) as session:
        from reality.db.core import LedgerEntry

        assert (
            len(
                list(
                    session.scalars(
                        select(LedgerEntry.id).where(LedgerEntry.tenant_id == tenant_id)
                    )
                )
            )
            == 4
        )


def test_invoice_and_payment_learning_steps(durable_playground):
    from sqlalchemy.orm import Session

    from reality.db.core import Document, PlaygroundRun
    from reality.services.core import open_invoice_amount
    from reality.services.playground import confirm_step, prepare_step, read_step

    engine, owner, run_id = durable_playground

    def execute(key, tool, args):
        preview = prepare_step(engine, owner, run_id, key, tool, args)
        result = confirm_step(
            engine,
            owner,
            run_id,
            preview["step_id"],
            preview["preview"]["revision"],
            confirmed=True,
        )
        assert result["status"] == "executed", result
        assert result["receipt"] is not None
        return result, preview

    execute("stock", "movement_create", opening_arguments(engine, run_id))
    with Session(engine) as session:
        run = session.get(PlaygroundRun, run_id)
        tenant_id, refs = run.tenant_id, run.initialization_progress
    order, _ = execute(
        "order",
        "order_create",
        {
            "direction": "sales",
            "number": "ORDER-1",
            "company_party_id": refs["parties"]["company"],
            "counterparty_id": refs["parties"]["customer_huber"],
            "location_id": refs["locations"]["warehouse"],
            "item_id": refs["items"]["BIKE-LIGHT"],
            "quantity": "12",
            "unit_price": "25",
        },
    )
    records = order["receipt"]["records"]
    commitment_id = next(r["id"] for r in records if r["family"] == "commitment")
    line_id = next(r["id"] for r in records if r["family"] == "document_line")
    execute("reserve", "reserve", {"commitment_id": commitment_id, "quantity": "12"})
    execute(
        "ship",
        "movement_create",
        {
            "movement_type": "shipment",
            "commitment_id": commitment_id,
            "item_id": refs["items"]["BIKE-LIGHT"],
            "from_location_id": refs["locations"]["warehouse"],
            "quantity": "12",
        },
    )
    invoice, preview = execute(
        "invoice",
        "sales_invoice_record",
        {
            "order_line_id": line_id,
            "quantity": "12",
            "gross_amount": "300",
            "number": "INV-1",
        },
    )
    invoice_id = next(
        r["id"] for r in invoice["receipt"]["records"] if r["family"] == "document"
    )
    with Session(engine) as session:
        assert open_invoice_amount(session, tenant_id, invoice_id) == 300
        assert session.get(Document, invoice_id).gross_amount == 300
    replay = confirm_step(
        engine,
        owner,
        run_id,
        preview["step_id"],
        preview["preview"]["revision"],
        confirmed=True,
    )
    assert replay["receipt"] == invoice["receipt"]
    payment, _ = execute(
        "payment",
        "customer_payment_post",
        {"invoice_id": invoice_id, "amount": "125", "payment_number": "PAY-1"},
    )
    with Session(engine) as session:
        assert open_invoice_amount(session, tenant_id, invoice_id) == 175
        assert (
            read_step(session, owner, run_id, payment["step_id"])["receipt"]
            == payment["receipt"]
        )

    # A second business operation reuses the run and the remaining eight pieces.
    second_order, _ = execute(
        "order-2",
        "order_create",
        {
            "direction": "sales",
            "number": "ORDER-2",
            "company_party_id": refs["parties"]["company"],
            "counterparty_id": refs["parties"]["customer_huber"],
            "location_id": refs["locations"]["warehouse"],
            "item_id": refs["items"]["BIKE-LIGHT"],
            "quantity": "3",
            "unit_price": "25",
        },
    )
    second_records = second_order["receipt"]["records"]
    second_commitment = next(
        r["id"] for r in second_records if r["family"] == "commitment"
    )
    second_line = next(
        r["id"] for r in second_records if r["family"] == "document_line"
    )
    assert second_commitment != commitment_id
    assert second_line != line_id
    execute(
        "reserve-2", "reserve", {"commitment_id": second_commitment, "quantity": "3"}
    )
    execute(
        "ship-2",
        "movement_create",
        {
            "movement_type": "shipment",
            "commitment_id": second_commitment,
            "item_id": refs["items"]["BIKE-LIGHT"],
            "from_location_id": refs["locations"]["warehouse"],
            "quantity": "3",
        },
    )
    second_invoice, _ = execute(
        "invoice-2",
        "sales_invoice_record",
        {
            "order_line_id": second_line,
            "quantity": "3",
            "gross_amount": "75",
            "number": "INV-2",
        },
    )
    second_invoice_id = next(
        r["id"]
        for r in second_invoice["receipt"]["records"]
        if r["family"] == "document"
    )
    execute(
        "payment-2",
        "customer_payment_post",
        {
            "invoice_id": second_invoice_id,
            "amount": "75",
            "payment_number": "PAY-2",
        },
    )
    with Session(engine) as session:
        from reality.services.core import stock_at
        from reality.services.playground import read_run

        assert session.get(PlaygroundRun, run_id).tenant_id == tenant_id
        assert open_invoice_amount(session, tenant_id, invoice_id) == 175
        assert open_invoice_amount(session, tenant_id, second_invoice_id) == 0
        assert (
            stock_at(
                session,
                tenant_id,
                refs["items"]["BIKE-LIGHT"],
                refs["locations"]["warehouse"],
            )
            == 5
        )
        assert len(read_run(session, owner, run_id)["steps"]) == 11

    returned, _ = execute(
        "return-1",
        "movement_create",
        {
            "movement_type": "return",
            "commitment_id": second_commitment,
            "item_id": refs["items"]["BIKE-LIGHT"],
            "to_location_id": refs["locations"]["warehouse"],
            "quantity": "1",
        },
    )
    assert returned["receipt"]["after"]["order_line_id"] == second_line
    assert Decimal(returned["receipt"]["after"]["returnable_quantity"]) == 2
    assert Decimal(returned["receipt"]["after"]["open_quantity"]) == 0
    from reality.services.core import InvalidOperation

    return_args = {
        "movement_type": "return",
        "commitment_id": second_commitment,
        "item_id": refs["items"]["BIKE-LIGHT"],
        "to_location_id": refs["locations"]["warehouse"],
        "quantity": "3",
    }
    with pytest.raises(InvalidOperation):
        prepare_step(
            engine, owner, run_id, "excess-return", "movement_create", return_args
        )
    with pytest.raises(NotFound):
        prepare_step(
            engine,
            owner,
            run_id,
            "foreign-return",
            "movement_create",
            {**return_args, "commitment_id": "com_foreign"},
        )
    with pytest.raises(InvalidOperation):
        prepare_step(
            engine,
            owner,
            run_id,
            "excess-credit",
            "sales_credit_record",
            {
                "order_line_id": second_line,
                "quantity": "2",
                "gross_amount": "26",
                "number": "CR-INVALID",
            },
        )
    credit, _ = execute(
        "credit-1",
        "sales_credit_record",
        {
            "order_line_id": second_line,
            "quantity": "1",
            "gross_amount": "26",
            "number": "CREDIT-STATED-1",
        },
    )
    credit_id = next(
        r["id"] for r in credit["receipt"]["records"] if r["family"] == "document"
    )
    assert Decimal(credit["receipt"]["after"]["open_amount"]) == 26
    with pytest.raises(InvalidOperation):
        prepare_step(
            engine,
            owner,
            run_id,
            "duplicate-credit",
            "sales_credit_record",
            {
                "order_line_id": second_line,
                "quantity": "1",
                "gross_amount": "26",
                "number": "CR-DUPLICATE",
            },
        )
    for changes in [
        {"amount": "27"},
        {"credit_note_id": second_invoice_id},
        {"source_record_id": "src_unreviewed"},
    ]:
        with pytest.raises(InvalidOperation):
            prepare_step(
                engine,
                owner,
                run_id,
                uid("bad-refund"),
                "customer_refund_post",
                {
                    "credit_note_id": credit_id,
                    "amount": "26",
                    "refund_number": "REF-INVALID",
                    **changes,
                },
            )
    refund, refund_preview = execute(
        "refund-1",
        "customer_refund_post",
        {
            "credit_note_id": credit_id,
            "amount": "26",
            "refund_number": "REFUND-1",
        },
    )
    assert Decimal(refund["receipt"]["after"]["open_amount"]) == 0
    assert (
        confirm_step(
            engine,
            owner,
            run_id,
            refund_preview["step_id"],
            refund_preview["preview"]["revision"],
            confirmed=True,
        )["receipt"]
        == refund["receipt"]
    )
    with Session(engine) as session:
        assert (
            stock_at(
                session,
                tenant_id,
                refs["items"]["BIKE-LIGHT"],
                refs["locations"]["warehouse"],
            )
            == 6
        )
        assert open_quantity(session, tenant_id, second_commitment) == 0
        assert open_invoice_amount(session, tenant_id, second_invoice_id) == 0


def test_confirm_opening_records_once_with_observation(durable_playground):
    from sqlalchemy.orm import Session

    from reality.db.core import PlaygroundRun
    from reality.services.playground import confirm_step, prepare_step, read_step

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    proposal = prepare_step(
        engine, owner_id, run_id, "opening", "movement_create", args
    )
    result = confirm_step(
        engine,
        owner_id,
        run_id,
        proposal["step_id"],
        proposal["preview"]["revision"],
        confirmed=True,
    )
    assert result["status"] == "executed"
    assert result["receipt"]["before"]["physical"] == "0"
    assert Decimal(result["receipt"]["after"]["physical"]) == 20
    assert result["verification"]["operational_state"] == "verified"
    replay = confirm_step(
        engine,
        owner_id,
        run_id,
        proposal["step_id"],
        proposal["preview"]["revision"],
        confirmed=True,
    )
    assert replay["receipt"] == result["receipt"]
    from reality.services.core import Conflict

    with pytest.raises(Conflict):
        confirm_step(
            engine,
            owner_id,
            run_id,
            proposal["step_id"],
            "wrong-review",
            confirmed=True,
        )
    with Session(engine) as session:
        tenant_id = session.get(PlaygroundRun, run_id).tenant_id
        movements = list(
            session.scalars(select(Movement).where(Movement.tenant_id == tenant_id))
        )
        assert len(movements) == 1 and movements[0].quantity == 20
        assert (
            read_step(session, owner_id, run_id, proposal["step_id"])["receipt"]
            == result["receipt"]
        )
        assert (
            session.get(ChangeProposal, proposal["proposal_id"]).decided_by_user_id
            == owner_id
        )
    assert (
        prepare_step(engine, owner_id, run_id, "opening", "movement_create", args)[
            "status"
        ]
        == "executed"
    )


@pytest.mark.parametrize("change", ["confirmation", "revision", "reference"])
def test_confirm_opening_requires_current_review(durable_playground, change):
    from sqlalchemy.orm import Session

    from reality.db.core import Item
    from reality.services.core import Conflict
    from reality.services.playground import confirm_step, prepare_step
    from reality.services.tenant_policy import PlaygroundOperationDenied

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    proposal = prepare_step(
        engine, owner_id, run_id, "opening", "movement_create", args
    )
    revision = proposal["preview"]["revision"]
    if change == "reference":
        with Session(engine) as session:
            session.get(Item, args["item_id"]).name = "Changed article"
            session.commit()
    error = PlaygroundOperationDenied if change == "confirmation" else Conflict
    with pytest.raises(error):
        confirm_step(
            engine,
            owner_id,
            run_id,
            proposal["step_id"],
            "old" if change == "revision" else revision,
            confirmed=change != "confirmation",
        )


def test_reject_opening_uses_existing_lifecycle(durable_playground):
    from sqlalchemy.orm import Session

    from reality.services.core import Conflict
    from reality.services.playground import confirm_step, prepare_step, reject_step

    engine, owner_id, run_id = durable_playground
    proposal = prepare_step(
        engine,
        owner_id,
        run_id,
        "opening",
        "movement_create",
        opening_arguments(engine, run_id),
    )
    result = reject_step(engine, owner_id, run_id, proposal["step_id"], confirmed=True)
    assert result["status"] == "rejected" and result["receipt"] is None
    assert (
        reject_step(engine, owner_id, run_id, proposal["step_id"], confirmed=True)[
            "status"
        ]
        == "rejected"
    )
    with pytest.raises(Conflict):
        confirm_step(
            engine,
            owner_id,
            run_id,
            proposal["step_id"],
            proposal["preview"]["revision"],
            confirmed=True,
        )
    with Session(engine) as session:
        assert (
            session.get(ChangeProposal, proposal["proposal_id"]).decided_by_user_id
            == owner_id
        )
        assert session.scalar(select(Movement.id)) is None


@pytest.mark.parametrize("after_effect", [False, True])
def test_confirm_opening_interruption_never_reexecutes(
    durable_playground, monkeypatch, after_effect
):
    from dataclasses import replace

    from sqlalchemy.orm import Session

    from reality.services.core import Conflict
    from reality.services.playground import confirm_step, prepare_step
    from reality.tools import application

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    proposal = prepare_step(
        engine, owner_id, run_id, "opening", "movement_create", args
    )
    original = application.TOOLS["movement_create"]
    calls = 0

    def interrupted(*args):
        nonlocal calls
        calls += 1
        if after_effect:
            original.handler(*args)
        raise RuntimeError("Simulated interruption")

    monkeypatch.setitem(
        application.TOOLS, "movement_create", replace(original, handler=interrupted)
    )
    for _ in range(2):
        result = confirm_step(
            engine,
            owner_id,
            run_id,
            proposal["step_id"],
            proposal["preview"]["revision"],
            confirmed=True,
        )
        assert result["status"] == "executing"
        assert result["verification"]["execution"] == (
            "effect_observed_proposal_unsettled" if after_effect else "unknown"
        )
        assert result["receipt"] is None
    assert calls == 1
    with pytest.raises(Conflict):
        prepare_step(engine, owner_id, run_id, "another", "movement_create", args)
    with Session(engine) as session:
        assert len(list(session.scalars(select(Movement)))) == int(after_effect)


def test_confirm_opening_observation_failure_is_not_execution_failure(
    durable_playground, monkeypatch
):
    from sqlalchemy.orm import Session

    from reality.services import playground
    from reality.services.core import Conflict

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    proposal = playground.prepare_step(
        engine, owner_id, run_id, "opening", "movement_create", args
    )
    original = playground._store_opening_observation

    def unavailable(*_args):
        raise RuntimeError("Simulated unavailable observation")

    monkeypatch.setattr(playground, "_store_opening_observation", unavailable)
    result = playground.confirm_step(
        engine,
        owner_id,
        run_id,
        proposal["step_id"],
        proposal["preview"]["revision"],
        confirmed=True,
    )
    assert result["status"] == "executed" and result["observation"] == "unavailable"
    assert result["verification"]["operational_state"] == "verified"
    with pytest.raises(Conflict):
        playground.prepare_step(
            engine, owner_id, run_id, "another", "movement_create", args
        )
    monkeypatch.setattr(playground, "_store_opening_observation", original)
    recovered = playground.confirm_step(
        engine,
        owner_id,
        run_id,
        proposal["step_id"],
        proposal["preview"]["revision"],
        confirmed=True,
    )
    assert recovered["receipt"] is not None
    with Session(engine) as session:
        assert len(list(session.scalars(select(Movement)))) == 1


@pytest.mark.parametrize("operation", ["prepare", "confirm", "reject"])
def test_step_decisions_owner_boundary(durable_playground, operation):
    from reality.services import playground

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    proposal = playground.prepare_step(
        engine, owner_id, run_id, "opening", "movement_create", args
    )
    with pytest.raises(NotFound):
        if operation == "prepare":
            playground.prepare_step(
                engine, "foreign", run_id, "another", "movement_create", args
            )
        elif operation == "confirm":
            playground.confirm_step(
                engine,
                "foreign",
                run_id,
                proposal["step_id"],
                proposal["preview"]["revision"],
                confirmed=True,
            )
        else:
            playground.reject_step(
                engine, "foreign", run_id, proposal["step_id"], confirmed=True
            )


def test_step_read_owner_boundary(durable_playground):
    from sqlalchemy.orm import Session

    from reality.services.playground import prepare_step, read_step

    engine, owner_id, run_id = durable_playground
    proposal = prepare_step(
        engine,
        owner_id,
        run_id,
        "opening",
        "movement_create",
        opening_arguments(engine, run_id),
    )
    with pytest.raises(NotFound), Session(engine) as session:
        read_step(session, "foreign", run_id, proposal["step_id"])


@pytest.mark.parametrize(
    "attempt", ["quantity", "identity", "extra", "core", "event", "duplicate"]
)
def test_opening_execution_permission_is_narrow(
    durable_playground, monkeypatch, attempt
):
    from dataclasses import replace

    from sqlalchemy.orm import Session

    from reality.services import core, playground
    from reality.tools import application

    engine, owner_id, run_id = durable_playground
    proposal = playground.prepare_step(
        engine,
        owner_id,
        run_id,
        "opening",
        "movement_create",
        opening_arguments(engine, run_id),
    )
    original = application.TOOLS["movement_create"]

    def misuse(session, tenant_id, arguments):
        arguments = dict(arguments)
        if attempt == "quantity":
            arguments["quantity"] = "999"
        elif attempt == "identity":
            arguments["_action_id"] = "forged"
        elif attempt == "extra":
            arguments["source_record_id"] = "forged"
        elif attempt == "core":
            return core.create_item(session, tenant_id, "WRONG", "Unapproved item")
        elif attempt == "event":
            return core.emit_business_event(
                session,
                tenant_id,
                "fact.observed",
                "fact",
                "forged",
                {},
                action_id=arguments["_action_id"],
            )
        elif attempt == "duplicate":
            original.handler(session, tenant_id, arguments)
        return original.handler(session, tenant_id, arguments)

    monkeypatch.setitem(
        application.TOOLS, "movement_create", replace(original, handler=misuse)
    )
    result = playground.confirm_step(
        engine,
        owner_id,
        run_id,
        proposal["step_id"],
        proposal["preview"]["revision"],
        confirmed=True,
    )
    assert result["status"] == "executing"
    with Session(engine) as session:
        movements = list(session.scalars(select(Movement)))
        assert len(movements) == int(attempt == "duplicate")
        if movements:
            assert movements[0].quantity == 20


def test_concurrent_opening_confirmation_returns_busy(durable_playground, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import replace
    from threading import Event

    from reality.services.core import Conflict
    from reality.services.playground import confirm_step, prepare_step
    from reality.tools import application

    engine, owner_id, run_id = durable_playground
    proposal = prepare_step(
        engine,
        owner_id,
        run_id,
        "opening",
        "movement_create",
        opening_arguments(engine, run_id),
    )
    original = application.TOOLS["movement_create"]
    entered, release = Event(), Event()

    def paused(*args):
        entered.set()
        assert release.wait(10)
        return original.handler(*args)

    monkeypatch.setitem(
        application.TOOLS, "movement_create", replace(original, handler=paused)
    )
    args = (
        engine,
        owner_id,
        run_id,
        proposal["step_id"],
        proposal["preview"]["revision"],
    )
    with ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(confirm_step, *args, confirmed=True)
        try:
            assert entered.wait(10)
            with pytest.raises(Conflict, match="busy"):
                confirm_step(*args, confirmed=True)
        finally:
            release.set()
        assert running.result(timeout=10)["status"] == "executed"
    assert confirm_step(*args, confirmed=True)["status"] == "executed"


def test_opening_observation_remains_historical(durable_playground):
    from sqlalchemy.orm import Session

    from reality.db.core import PlaygroundRun, now
    from reality.services.playground import confirm_step, prepare_step, read_step

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    first = prepare_step(engine, owner_id, run_id, "first", "movement_create", args)
    original = confirm_step(
        engine,
        owner_id,
        run_id,
        first["step_id"],
        first["preview"]["revision"],
        confirmed=True,
    )
    second = prepare_step(
        engine, owner_id, run_id, "second", "movement_create", {**args, "quantity": "5"}
    )
    result = confirm_step(
        engine,
        owner_id,
        run_id,
        second["step_id"],
        second["preview"]["revision"],
        confirmed=True,
    )
    assert Decimal(result["receipt"]["before"]["physical"]) == 20
    assert Decimal(result["receipt"]["after"]["physical"]) == 25
    with Session(engine) as session:
        run = session.get(PlaygroundRun, run_id)
        run.status, run.archived_at = "archived", now()
        session.commit()
        assert (
            read_step(session, owner_id, run_id, first["step_id"])["receipt"]
            == original["receipt"]
        )


def test_opening_execution_rechecks_applied_capacity(durable_playground, monkeypatch):
    from sqlalchemy.orm import Session

    from reality.db.core import PlaygroundRun
    from reality.services.playground import (
        PlaygroundStepQuotaExceeded,
        confirm_step,
        prepare_step,
    )

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    with Session(engine) as session:
        another_item = session.get(PlaygroundRun, run_id).initialization_progress[
            "items"
        ]["HELMET"]
    first = prepare_step(engine, owner_id, run_id, "first", "movement_create", args)
    second = prepare_step(
        engine,
        owner_id,
        run_id,
        "second",
        "movement_create",
        {**args, "item_id": another_item},
    )
    monkeypatch.setenv("REALITY_PLAYGROUND_STEP_LIMIT", "1")
    confirm_step(
        engine,
        owner_id,
        run_id,
        first["step_id"],
        first["preview"]["revision"],
        confirmed=True,
    )
    with pytest.raises(PlaygroundStepQuotaExceeded):
        confirm_step(
            engine,
            owner_id,
            run_id,
            second["step_id"],
            second["preview"]["revision"],
            confirmed=True,
        )


def test_opening_verification_requires_correlated_evidence(durable_playground):
    from sqlalchemy.orm import Session

    from reality.services.playground import confirm_step, prepare_step, read_step

    engine, owner_id, run_id = durable_playground
    proposal = prepare_step(
        engine,
        owner_id,
        run_id,
        "first",
        "movement_create",
        opening_arguments(engine, run_id),
    )
    result = confirm_step(
        engine,
        owner_id,
        run_id,
        proposal["step_id"],
        proposal["preview"]["revision"],
        confirmed=True,
    )
    with Session(engine) as session:
        event = session.get(BusinessEvent, result["receipt"]["event_ids"][0])
        event.action_id = (
            None  # Simulate missing attribution, not a supported domain correction.
        )
        session.commit()
        observed = read_step(session, owner_id, run_id, proposal["step_id"])
        assert observed["status"] == "executed"
        assert observed["verification"]["operational_state"] == "unresolved"
        assert observed["reconciliation_evidence"] is None


def test_prepare_opening_is_atomic_idempotent_and_not_execution(durable_playground):
    from sqlalchemy import func
    from sqlalchemy.orm import Session

    from reality.db.core import (
        Commitment,
        Document,
        Fact,
        PlaygroundRun,
        PlaygroundStep,
        SourceRecord,
    )
    from reality.services.playground import prepare_step
    from reality.services.tenant_policy import PlaygroundOperationDenied

    engine, owner_id, run_id = durable_playground
    arguments = opening_arguments(engine, run_id)
    result = prepare_step(
        engine, owner_id, run_id, "opening-1", "movement_create", arguments
    )
    replay = prepare_step(
        engine, owner_id, run_id, "opening-1", "movement_create", arguments
    )
    assert result == replay
    assert result["status"] == "proposed"
    assert result["arguments"]["quantity"] == "20"
    assert result["arguments"]["occurred_at"]
    assert result["preview"]["requires_human_confirmation"] is True
    assert result["preview"]["defaults"] == ["occurred_at"]
    with Session(engine) as session:
        tenant_id = session.get(PlaygroundRun, run_id).tenant_id
        for model, count in [
            (PlaygroundStep, 1),
            (ChangeProposal, 1),
            (Movement, 0),
            (Fact, 0),
            (Commitment, 0),
            (Reservation, 0),
            (Document, 0),
            (SourceRecord, 0),
            (BusinessEvent, 8),
        ]:
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(model.tenant_id == tenant_id)
                )
                == count
            )
        step = session.get(PlaygroundStep, result["step_id"])
        assert step.before_observation is None and step.receipt_observation is None
        assert step.proposal_id == result["proposal_id"]
        with pytest.raises(PlaygroundOperationDenied):
            confirm_tool(session, tenant_id, step.proposal_id)


@pytest.mark.parametrize(
    "change", ["quantity", "tool", "extra", "foreign", "nan", "precision", "date"]
)
def test_prepare_opening_rejects_invalid_or_changed_intent(durable_playground, change):
    from reality.services.core import Conflict, InvalidOperation
    from reality.services.playground import prepare_step

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    prepare_step(engine, owner_id, run_id, "first", "movement_create", args)
    tool = "movement_create"
    key = "second"
    error = InvalidOperation
    if change == "quantity":
        args["quantity"] = "21"
        key, error = "first", Conflict
    elif change == "tool":
        tool = "order_create"
    elif change == "extra":
        args["_action_id"] = "forged"
    elif change == "foreign":
        args["item_id"] = "foreign-item"
        error = NotFound
    elif change == "nan":
        args["quantity"] = "NaN"
    elif change == "precision":
        args["quantity"] = "1.00001"
    else:
        args["occurred_at"] = "2026-09-06T10:00:00"
    with pytest.raises(error):
        prepare_step(engine, owner_id, run_id, key, tool, args)


def test_prepare_opening_rolls_back_proposal_when_step_fails(
    durable_playground, monkeypatch
):
    from sqlalchemy import event, func
    from sqlalchemy.orm import Session

    from reality.db.core import PlaygroundStep
    from reality.services.playground import prepare_step

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)

    def fail_step(_mapper, _connection, _target):
        raise RuntimeError("Simulated metadata failure")

    event.listen(PlaygroundStep, "before_insert", fail_step)
    try:
        with pytest.raises(RuntimeError, match="metadata failure"):
            prepare_step(engine, owner_id, run_id, "first", "movement_create", args)
    finally:
        event.remove(PlaygroundStep, "before_insert", fail_step)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ChangeProposal)) == 0
    result = prepare_step(engine, owner_id, run_id, "first", "movement_create", args)
    assert result["sequence"] == 1


def test_prepare_opening_owner_boundary(durable_playground):
    from reality.services.playground import prepare_step

    engine, _owner_id, run_id = durable_playground
    with pytest.raises(NotFound):
        prepare_step(
            engine,
            "foreign-owner",
            run_id,
            "first",
            "movement_create",
            opening_arguments(engine, run_id),
        )


@pytest.mark.parametrize("state", ["executing", "quota", "inactive", "foreign", "busy"])
def test_prepare_opening_state_guards(durable_playground, monkeypatch, state):
    from contextlib import nullcontext

    from sqlalchemy.orm import Session

    from reality.db.core import Item, PlaygroundRun
    from reality.services.core import Conflict, InvalidOperation, create_item
    from reality.services.playground import _mutation_session, prepare_step

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    with Session(engine) as setup:
        tenant_id = setup.get(PlaygroundRun, run_id).tenant_id
        if state in {"executing", "quota"}:
            setup.add(
                ChangeProposal(
                    id=uid("act"),
                    tenant_id=tenant_id,
                    type="tool:movement_create",
                    status="executing" if state == "executing" else "executed",
                )
            )
            monkeypatch.setenv("REALITY_PLAYGROUND_STEP_LIMIT", "1")
        elif state == "inactive":
            setup.get(Item, args["item_id"]).is_active = False
        elif state == "foreign":
            production = create_tenant(setup, "Production fixture")
            args["item_id"] = create_item(
                setup, production.id, "REAL", "Real article"
            ).id
        setup.commit()
    error = (
        NotFound
        if state == "foreign"
        else (Conflict if state in {"busy", "executing"} else InvalidOperation)
    )
    lock = (
        _mutation_session(engine, owner_id, run_id)
        if state == "busy"
        else nullcontext()
    )
    with lock, pytest.raises(error):
        prepare_step(engine, owner_id, run_id, "first", "movement_create", args)


def test_prepare_opening_preserves_explicit_time_and_rejects_changed_default(
    durable_playground,
):
    from reality.services.core import Conflict
    from reality.services.playground import prepare_step

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    args["occurred_at"] = "2026-09-06T12:00:00+02:00"
    result = prepare_step(engine, owner_id, run_id, "first", "movement_create", args)
    assert result["arguments"]["occurred_at"] == "2026-09-06T10:00:00+00:00"
    assert result["preview"]["defaults"] == []
    del args["occurred_at"]
    with pytest.raises(Conflict):
        prepare_step(engine, owner_id, run_id, "first", "movement_create", args)


@pytest.mark.parametrize(
    "attempt",
    ["commit", "arguments", "tool", "session", "transaction", "core", "tenant"],
)
def test_proposal_scope_is_exact_and_never_execution(durable_playground, attempt):
    from sqlalchemy.orm import Session

    from reality.db.core import PlaygroundRun
    from reality.services.core import create_item
    from reality.services.tenant_policy import (
        PlaygroundOperationDenied,
        _proposal_creation_scope,
    )
    from reality.tools.application import create_change_proposal

    engine, owner_id, run_id = durable_playground
    args = opening_arguments(engine, run_id)
    with Session(engine) as session, Session(engine) as other:
        tenant_id = session.get(PlaygroundRun, run_id).tenant_id
        production_id = create_tenant(session, "Production fixture").id
        with _proposal_creation_scope(
            session, run_id, owner_id, "movement_create", args
        ):
            target_session = session
            supplied, tool = dict(args), "movement_create"
            if attempt == "arguments":
                supplied["quantity"] = "99"
            elif attempt == "tool":
                tool = "party_create"
            elif attempt == "session":
                target_session = other
            elif attempt == "transaction":
                session.rollback()
            elif attempt == "tenant":
                tenant_id = production_id
            with pytest.raises(PlaygroundOperationDenied):
                if attempt == "core":
                    create_item(session, tenant_id, "DENIED", "Not a proposal")
                else:
                    create_change_proposal(
                        target_session,
                        tenant_id,
                        tool,
                        supplied,
                        _commit=attempt == "commit",
                    )
        session.rollback()
        with pytest.raises(PlaygroundOperationDenied):
            create_change_proposal(
                session,
                session.get(PlaygroundRun, run_id).tenant_id,
                "movement_create",
                args,
            )


@pytest.fixture
def durable_playground(postgres_database, monkeypatch):
    """Real commits and independent connections, not the test savepoint wrapper."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from reality.db.core import AppUser, Base, now
    from reality.services.playground import start_run

    engine = create_engine(postgres_database, pool_size=2, max_overflow=2)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        owner = AppUser(
            id=uid("usr"),
            email=f"{uid('mail')}@example.test",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        session.add(owner)
        session.commit()
        run = start_run(session, owner.id, "first", confirmed=True)
        identity = (owner.id, run.id)
    try:
        yield engine, *identity
    finally:
        engine.dispose()


def test_run_lock_survives_commits_and_rollback(durable_playground):
    from sqlalchemy import text

    from reality.services.core import Conflict
    from reality.services.playground import _mutation_session

    engine, owner_id, run_id = durable_playground
    with _mutation_session(engine, owner_id, run_id) as (session, run):
        assert run.id == run_id
        backend = session.scalar(text("SELECT pg_backend_pid()"))
        for settle in (session.commit, session.rollback, session.commit):
            settle()
            assert session.scalar(text("SELECT pg_backend_pid()")) == backend
            with (
                pytest.raises(Conflict, match="busy"),
                _mutation_session(engine, owner_id, run_id),
            ):
                pytest.fail("Another connection entered the locked run")
    with _mutation_session(engine, owner_id, run_id):
        pass


@pytest.mark.parametrize("failure", ["application", "transaction", "disconnect"])
def test_run_lock_released_after_failure(durable_playground, failure):
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from reality.services.playground import _mutation_session
    from reality.services.tenant_policy import PlaygroundOperationDenied

    engine, owner_id, run_id = durable_playground
    error = {
        "application": RuntimeError,
        "transaction": DBAPIError,
        "disconnect": PlaygroundOperationDenied,
    }[failure]
    with (
        pytest.raises(error),
        _mutation_session(engine, owner_id, run_id) as (session, _run),
    ):
        if failure == "application":
            raise RuntimeError("Simulated caller failure")
        if failure == "transaction":
            session.execute(text("SELECT 1 / 0"))
        connection = session.connection()
        connection.invalidate()
        session.rollback()
        # Reconnecting would silently lose the session-level advisory lock.
        session.execute(text("SELECT 1"))
    with _mutation_session(engine, owner_id, run_id):
        pass


def test_run_lock_does_not_grant_mutation_permission(durable_playground):
    from reality.services.core import create_item
    from reality.services.playground import _mutation_session
    from reality.services.tenant_policy import PlaygroundOperationDenied

    engine, owner_id, run_id = durable_playground
    with _mutation_session(engine, owner_id, run_id) as (session, run):
        with pytest.raises(PlaygroundOperationDenied):
            create_item(session, run.tenant_id, "BYPASS", "Not confirmed")
        with pytest.raises(PlaygroundOperationDenied):
            propose_tool(session, run.tenant_id, "item_create", {"records": []})


@pytest.mark.parametrize(
    "unavailable", ["owner", "account", "run", "tenant", "membership"]
)
def test_run_lock_checks_current_admission(
    durable_playground, monkeypatch, unavailable
):
    from sqlalchemy.orm import Session

    from reality.db.core import AppUser, PlaygroundRun, Tenant, TenantMembership, now
    from reality.services.playground import _mutation_session
    from reality.services.tenant_policy import PlaygroundOperationDenied

    engine, owner_id, run_id = durable_playground
    with Session(engine) as session:
        run = session.get(PlaygroundRun, run_id)
        if unavailable == "owner":
            owner_id = "another-owner"
        elif unavailable == "account":
            session.get(AppUser, owner_id).status = "suspended"
        elif unavailable == "run":
            run.status = "archived"
            run.archived_at = now()
        elif unavailable == "tenant":
            session.get(Tenant, run.tenant_id).archived_at = now()
        else:
            session.scalar(
                select(TenantMembership).where(
                    TenantMembership.tenant_id == run.tenant_id,
                    TenantMembership.user_id == owner_id,
                )
            ).status = "removed"
        session.commit()
    expected = (
        NotFound
        if unavailable in {"owner", "membership"}
        else PlaygroundOperationDenied
    )
    with pytest.raises(expected), _mutation_session(engine, owner_id, run_id):
        pytest.fail("Unavailable run acquired mutation session")


def test_run_lock_session_cannot_be_reused(durable_playground):
    from sqlalchemy import text
    from sqlalchemy.exc import InvalidRequestError

    from reality.services.playground import _mutation_session

    engine, owner_id, run_id = durable_playground
    with _mutation_session(engine, owner_id, run_id) as (session, _run):
        session.commit()
    with pytest.raises(InvalidRequestError):
        session.execute(text("SELECT 1"))


def test_run_lock_keeps_reads_available(durable_playground):
    from sqlalchemy.orm import Session

    from reality.services.playground import _mutation_session, read_run

    engine, owner_id, run_id = durable_playground
    with _mutation_session(engine, owner_id, run_id), Session(engine) as reader:
        assert read_run(reader, owner_id, run_id)["status"] == "active"


def test_run_lock_rechecks_admission_after_acquisition(durable_playground, monkeypatch):
    from sqlalchemy.orm import Session

    from reality.db.core import AppUser
    from reality.services import playground
    from reality.services.tenant_policy import PlaygroundOperationDenied

    engine, owner_id, run_id = durable_playground
    original = playground.require_playground_run
    calls = 0

    def revoke_between_checks(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            with Session(engine) as other:
                other.get(AppUser, owner_id).status = "suspended"
                other.commit()
        return original(*args, **kwargs)

    monkeypatch.setattr(playground, "require_playground_run", revoke_between_checks)
    with (
        pytest.raises(PlaygroundOperationDenied),
        playground._mutation_session(engine, owner_id, run_id),
    ):
        pytest.fail("Pre-lock admission was incorrectly reused")
    assert calls == 2
    with Session(engine) as other:
        other.get(AppUser, owner_id).status = "active"
        other.commit()
    with playground._mutation_session(engine, owner_id, run_id):
        pass


@pytest.mark.parametrize("statement", ["pg_try_advisory_lock", "pg_advisory_unlock"])
def test_run_lock_discards_connection_after_uncertain_lock_reply(
    durable_playground, statement
):
    from sqlalchemy import event

    from reality.services.playground import _mutation_session

    engine, owner_id, run_id = durable_playground

    def fail_after_server_reply(_conn, _cursor, sql, *_args):
        if statement in sql:
            raise RuntimeError("Simulated lost lock reply")

    event.listen(engine, "after_cursor_execute", fail_after_server_reply)
    try:
        with (
            pytest.raises(RuntimeError, match="lost lock reply"),
            _mutation_session(engine, owner_id, run_id),
        ):
            pass
    finally:
        event.remove(engine, "after_cursor_execute", fail_after_server_reply)
    with _mutation_session(engine, owner_id, run_id):
        pass


def test_run_lock_rolls_back_uncommitted_metadata(durable_playground):
    from sqlalchemy.orm import Session

    from reality.db.core import PlaygroundRun
    from reality.services.playground import _mutation_session

    engine, owner_id, run_id = durable_playground
    with _mutation_session(engine, owner_id, run_id) as (session, run):
        run.initialization_error_code = "not_committed"
        session.flush()
    with Session(engine) as reader:
        assert reader.get(PlaygroundRun, run_id).initialization_error_code is None


def test_run_lock_is_scoped_to_one_run(durable_playground):
    from sqlalchemy.orm import Session

    from reality.db.core import AppUser, now
    from reality.services.playground import _mutation_session, start_run

    engine, owner_id, run_id = durable_playground
    with Session(engine, expire_on_commit=False) as setup:
        other = AppUser(
            id=uid("usr"),
            email=f"{uid('mail')}@example.test",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        setup.add(other)
        setup.commit()
        another_run = start_run(setup, other.id, "another", confirmed=True)
        another_id, another_owner = another_run.id, other.id
    with (
        _mutation_session(engine, owner_id, run_id),
        _mutation_session(engine, another_owner, another_id),
    ):
        pass


@pytest.mark.parametrize(
    "tool,record,event_type",
    [
        (
            "party_create",
            {"name": "Sample buyer", "roles": ["customer"]},
            "party.created",
        ),
        ("item_create", {"sku": "SAMPLE", "name": "Sample item"}, "item.created"),
        ("location_create", {"name": "Sample warehouse"}, "location.created"),
    ],
)
def test_reference_creation_attributes_action(
    session, business, tool, record, event_type
):
    action = execute(session, business.tenant.id, tool, {"records": [record]})
    events = events_for(session, business.tenant.id, action.id)
    assert [event.event_type for event in events] == [event_type]
    assert events[0].subject_id == json.loads(action.output)["records"][0]["id"]


def test_order_attributes_evidence_and_commitment(session, business):
    action = execute(
        session,
        business.tenant.id,
        "order_create",
        {
            "direction": "sales",
            "number": "LEARN-1",
            "company_party_id": business.company.id,
            "counterparty_id": business.customer.id,
            "location_id": business.location.id,
            "gross_amount": "588",
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "12",
                    "unit_price": "49",
                    "gross_amount": "588",
                }
            ],
        },
    )
    events = events_for(session, business.tenant.id, action.id)
    assert {event.event_type for event in events} == {
        "source_record.stored",
        "document.recorded",
        "order.recorded",
        "commitment.created",
    }
    result = json.loads(action.output)
    assert {event.subject_id for event in events} == {
        result["source_record_id"],
        result["document_id"],
        *result["commitment_ids"],
    }
    document_event = next(
        event for event in events if event.event_type == "document.recorded"
    )
    assert (
        json.loads(document_event.payload)["document_line_ids"]
        == result["document_line_ids"]
    )
    assert document_event.source_record_id == result["source_record_id"]


def test_movement_rejects_foreign_action_before_writing(session, business):
    other = create_tenant(session, "Other business")
    action = ChangeProposal(id=uid("act"), tenant_id=other.id, type="test")
    session.add(action)
    session.commit()
    with pytest.raises(NotFound):
        record_movement(
            session,
            business.tenant.id,
            "opening_stock",
            business.item.id,
            1,
            to_location_id=business.location.id,
            action_id=action.id,
        )
    assert stock_at(session, business.tenant.id, business.item.id) == 0


def test_automatic_events_rollback_with_movement(session, business, monkeypatch):
    from reality.services import core

    tenant_id = business.tenant.id
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        1,
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        "2026-09-07",
    )
    reserve_action = execute(
        session, tenant_id, "reserve", {"commitment_id": commitment.id}
    )
    original_id = events_for(session, tenant_id, reserve_action.id)[0].subject_id
    original_emitter = core.emit_business_event

    def fail_after_event(*args, **kwargs):
        event = original_emitter(*args, **kwargs)
        if event.event_type == "commitment.fulfilled":
            raise RuntimeError("Simulated event persistence failure")
        return event

    monkeypatch.setattr(core, "emit_business_event", fail_after_event)
    with pytest.raises(RuntimeError, match="Simulated"):
        record_movement(
            session,
            tenant_id,
            "shipment",
            business.item.id,
            1,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
        )
    session.rollback()
    assert stock_at(session, tenant_id, business.item.id) == 1
    assert session.get(Reservation, original_id).status == "active"
    assert commitment.status == "open"
    assert not session.scalar(
        select(Movement.id).where(
            Movement.tenant_id == tenant_id, Movement.type == "shipment"
        )
    )
    assert not session.scalar(
        select(BusinessEvent.id).where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.event_type.in_(
                ["reservation.consumed", "commitment.fulfilled"]
            ),
        )
    )


def execute(session, tenant_id, tool, arguments):
    proposal = propose_tool(session, tenant_id, tool, arguments)
    review = json.loads(proposal.input).get("_delivery_review", {})
    return confirm_tool(session, tenant_id, proposal.id, review_token=review.get("token"), confirmed=True)


def events_for(session, tenant_id, proposal_id):
    return list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal_id,
            )
            .order_by(BusinessEvent.sequence)
        )
    )


def test_confirmed_shipments_attribute_automatic_effects(session, business):
    tenant_id = business.tenant.id
    opening = execute(
        session,
        tenant_id,
        "movement_create",
        {
            "movement_type": "opening_stock",
            "item_id": business.item.id,
            "quantity": "20",
            "to_location_id": business.location.id,
        },
    )
    assert [
        event.event_type for event in events_for(session, tenant_id, opening.id)
    ] == ["movement.recorded"]
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        12,
        "2026-09-07",
    )
    reserve_action = execute(
        session,
        tenant_id,
        "reserve",
        {"commitment_id": commitment.id, "quantity": "12"},
    )
    original = session.scalar(
        select(Reservation).where(
            Reservation.tenant_id == tenant_id,
            Reservation.commitment_id == commitment.id,
        )
    )
    assert original is not None
    assert (
        events_for(session, tenant_id, reserve_action.id)[0].subject_id == original.id
    )

    for quantity, remaining, expected_types in (
        (5, 7, ["movement.recorded", "reservation.consumed", "reservation.created"]),
        (7, 0, ["movement.recorded", "reservation.consumed", "commitment.fulfilled"]),
    ):
        action = execute(
            session,
            tenant_id,
            "movement_create",
            {
                "movement_type": "shipment",
                "item_id": business.item.id,
                "quantity": str(quantity),
                "from_location_id": business.location.id,
                "commitment_id": commitment.id,
            },
        )
        events = events_for(session, tenant_id, action.id)
        assert [event.event_type for event in events] == expected_types
        assert all(event.correlation_id == action.id for event in events)
        assert all(event.causation_id == events[0].id for event in events[1:])
        assert events[1].subject_id == original.id
        assert Decimal(json.loads(events[1].payload)["consumed_quantity"]) == quantity
        assert active_reserved(session, tenant_id, business.item.id) == remaining
        assert open_quantity(session, tenant_id, commitment.id) == remaining
        assert stock_at(session, tenant_id, business.item.id) == remaining + 8
        assert commitment.status == ("open" if remaining else "fulfilled")
        assert original.status == "consumed"
        if remaining:
            original = session.scalar(
                select(Reservation).where(
                    Reservation.tenant_id == tenant_id,
                    Reservation.id == events[2].subject_id,
                )
            )
            assert original.quantity == remaining
            assert json.loads(events[2].payload)["cause"] == "shipment_remainder"
        else:
            assert events[2].subject_id == commitment.id
        confirm_tool(session, tenant_id, action.id)
        assert [event.id for event in events_for(session, tenant_id, action.id)] == [
            event.id for event in events
        ]


def test_confirmed_release_is_correlated(session, business):
    tenant_id = business.tenant.id
    execute(
        session,
        tenant_id,
        "movement_create",
        {
            "movement_type": "opening_stock",
            "item_id": business.item.id,
            "quantity": "1",
            "to_location_id": business.location.id,
        },
    )
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        "2026-09-07",
    )
    reserve_action = execute(
        session, tenant_id, "reserve", {"commitment_id": commitment.id}
    )
    reservation_id = events_for(session, tenant_id, reserve_action.id)[0].subject_id
    action = execute(
        session, tenant_id, "reservation_release", {"reservation_id": reservation_id}
    )
    events = events_for(session, tenant_id, action.id)
    assert [(event.event_type, event.subject_id) for event in events] == [
        ("reservation.released", reservation_id)
    ]
