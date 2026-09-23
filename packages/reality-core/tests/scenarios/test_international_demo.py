from conftest import record_by_id, seed_company
from sqlalchemy import func, select

from reality.db.core import (
    Commitment,
    Document,
    Item,
    Location,
    Party,
    PaymentTerm,
    PlaygroundRun,
)
from reality.demo.international import DEMO_DATA_PAYMENT_TERM, HISTORY
from reality.services import company_setup


def test_canonical_profile_counts_and_cases(session, scheduled_owner, monkeypatch):
    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "canonical",
        "Harbor Supply",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    assert result["status"] == "initializing", result
    tenant = result["tenant_id"]
    assert seed_company(session, tenant) == "succeeded"
    assert (
        company_setup.read_request(session, scheduled_owner.id, "canonical")["status"]
        == "ready"
    )
    for model, count in [(Item, 18), (Party, 24), (Location, 2)]:
        assert (
            session.scalar(
                select(func.count()).select_from(model).where(model.tenant_id == tenant)
            )
            == count
        )
    term = session.scalar(
        select(PaymentTerm).where(
            PaymentTerm.tenant_id == tenant,
            PaymentTerm.code == DEMO_DATA_PAYMENT_TERM["code"],
        )
    )
    assert term is not None
    invoices = list(
        session.scalars(
            select(Document).where(
                Document.tenant_id == tenant,
                Document.type.in_(("sales_invoice", "supplier_invoice")),
            )
        )
    )
    assert invoices and all(invoice.payment_term_id == term.id for invoice in invoices)
    run = record_by_id(session, PlaygroundRun, result["run_id"])
    assert set(run.initialization_progress["cases"]) >= {
        *{f"O{i:02}" for i in range(1, 12)},
        "S07",
        "S08",
        "S09",
    }
    assert (
        session.scalar(
            select(func.count())
            .select_from(Commitment)
            .where(Commitment.tenant_id == tenant)
        )
        >= 13
    )


def test_demo_human_numbers_use_canonical_type_families(
    session, scheduled_owner, monkeypatch
):
    """Feature 246: scenario labels never leak into visible business numbers."""
    import re

    from reality.db.core import Document

    tenant = _demo_company(session, scheduled_owner, "canonical-numbers")
    assert all(
        re.fullmatch(r"ITEM-\d{3}", item.sku)
        for item in session.scalars(select(Item).where(Item.tenant_id == tenant))
    )
    patterns = {
        "sales_order": r"SO-\d{3}",
        "purchase_order": r"PO-\d{3}",
        "sales_invoice": r"INV-\d{8}-[0-9A-F]{6}",
        "supplier_invoice": r"SINV-\d{3}",
        "credit_note": r"CN-\d{3}",
        "supplier_credit_note": r"SCN-\d{3}",
        "customer_payment": r"CPAY-\d{3}",
        "supplier_payment": r"SPAY-\d{3}",
    }
    documents = list(
        session.scalars(select(Document).where(Document.tenant_id == tenant))
    )
    visible_numbers = [
        document.number for document in documents if document.type in patterns
    ]
    duplicates = {
        number for number in visible_numbers if visible_numbers.count(number) > 1
    }
    assert duplicates == set(), duplicates
    for document in documents:
        pattern = patterns.get(document.type)
        if pattern is not None:
            assert re.fullmatch(pattern, document.number), (
                document.type,
                document.number,
            )


def test_operational_stock_and_source_lineage(session, scheduled_owner, monkeypatch):
    from decimal import Decimal

    from reality.db.core import Document, DocumentLine, Reservation, SourceRecord
    from reality.services import core

    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "operational",
        "Harbor Supply",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    tenant = result["tenant_id"]
    seed_company(session, tenant)
    manifest = record_by_id(
        session, PlaygroundRun, result["run_id"]
    ).initialization_progress
    for index, stock in enumerate((13, 14, 42, 2, 5, 5, 10, 0, 0, 13), 1):
        assert core.stock_at(
            session,
            tenant,
            manifest["items"][f"P{index:02}"],
            manifest["locations"]["A"],
        ) == Decimal(stock)
        case = manifest["cases"][f"O{index:02}"]
        commitment = record_by_id(session, Commitment, case["commitment_id"])
        line = record_by_id(session, DocumentLine, commitment.document_line_id)
        document = record_by_id(session, Document, line.document_id)
        assert document.id == case["document_id"]
        assert (
            record_by_id(session, SourceRecord, document.source_record_id).source_system
            == "demo_profile"
        )
        reserved = session.scalar(
            select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                Reservation.tenant_id == tenant,
                Reservation.commitment_id == commitment.id,
                Reservation.status == "active",
            )
        )
        assert reserved == {1: 5, 4: 2, 5: 5}.get(index, 0)
    assert (
        core.stock_at(
            session, tenant, manifest["items"]["P08"], manifest["locations"]["B"]
        )
        == 8
    )
    assert (
        core.open_quantity(session, tenant, manifest["cases"]["O06"]["commitment_id"])
        == 2
    )
    assert (
        record_by_id(
            session, Commitment, manifest["cases"]["O09"]["commitment_id"]
        ).status
        == "fulfilled"
    )
    assert (
        record_by_id(
            session, Commitment, manifest["cases"]["O10"]["commitment_id"]
        ).status
        == "cancelled"
    )
    assert (
        record_by_id(
            session, Commitment, manifest["cases"]["O11"]["commitment_id"]
        ).status
        == "cancelled"
    )
    assert core.fulfilled_quantity(
        session, tenant, manifest["cases"]["O11"]["commitment_id"]
    ) == Decimal(2)


def test_supported_edge_cases_are_source_backed_and_traceable(
    session, scheduled_owner, monkeypatch
):
    """Feature 246: every fully supported catalog promise exists in Reality."""
    from datetime import datetime
    from decimal import Decimal

    from reality.db.core import (
        DocumentLine,
        LedgerEntry,
        Lot,
        Movement,
        SerialUnit,
        SourceRecord,
    )
    from reality.services import core

    tenant = _demo_company(session, scheduled_owner, "supported-edge-cases")
    run = session.scalar(select(PlaygroundRun).where(PlaygroundRun.tenant_id == tenant))
    cases = run.initialization_progress["cases"]

    price_credit = cases["price_only_credit"]
    assert core.open_invoice_amount(
        session, tenant, price_credit["invoice_id"]
    ) == Decimal(45)
    assert "return_movement_id" not in price_credit

    reversal = cases["invoice_reversal"]
    original = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant,
                LedgerEntry.posting_group_id == reversal["original_posting_group_id"],
            )
        )
    )
    inverse = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant,
                LedgerEntry.posting_group_id == reversal["reversing_posting_group_id"],
            )
        )
    )
    assert len(original) == len(inverse) == 2
    assert sum(row.amount for row in original) == sum(row.amount for row in inverse)
    assert {row.debit_credit for row in original} == {
        row.debit_credit for row in inverse
    }

    split = cases["split_invoices"]
    split_lines = [
        record_by_id(session, DocumentLine, split[f"invoice_{index}_line_id"])
        for index in (1, 2)
    ]
    assert {line.billed_document_line_id for line in split_lines} == {split["line_id"]}
    assert sum(line.quantity for line in split_lines) == Decimal(10)

    tracked_lot = record_by_id(session, Lot, cases["lot_expiry_transfer"]["lot_id"])
    assert tracked_lot.lot_number == "LOT-2026-001"
    assert (
        tracked_lot.expires_at
        < datetime.fromisoformat(run.initialization_progress["windows"]["end"]).date()
    )
    transfer = record_by_id(
        session, Movement, cases["lot_expiry_transfer"]["transfer_movement_id"]
    )
    assert transfer.type == "transfer" and transfer.lot_id == tracked_lot.id
    assert core.stock_at(
        session, tenant, tracked_lot.item_id, transfer.from_location_id
    ) == Decimal(7)
    assert core.stock_at(
        session, tenant, tracked_lot.item_id, transfer.to_location_id
    ) == Decimal(3)

    serial = record_by_id(
        session, SerialUnit, cases["serial_tracking"]["serial_unit_id"]
    )
    serial_receipt = record_by_id(
        session, Movement, cases["serial_tracking"]["receipt_movement_id"]
    )
    assert serial.serial_number == "SER-0001"
    assert serial_receipt.serial_unit_id == serial.id

    adjustments = [
        record_by_id(session, Movement, movement_id)
        for movement_id in (
            cases["stock_adjustments"][f"{reason}_movement_id"]
            for reason in ("damage", "loss", "scrap")
        )
    ]
    assert all(row.type == "adjustment" for row in adjustments)
    assert {
        record_by_id(session, SourceRecord, row.source_record_id).external_id
        for row in adjustments
    } == {"ADJUSTMENT-001", "ADJUSTMENT-002", "ADJUSTMENT-003"}

    exchange = cases["exchange_replacement"]
    original_shipment = record_by_id(
        session, Movement, exchange["original_shipment_id"]
    )
    customer_return = record_by_id(session, Movement, exchange["return_movement_id"])
    replacement_shipment = record_by_id(
        session, Movement, exchange["replacement_shipment_id"]
    )
    assert exchange["original_order_number"] == "SO-033"
    assert exchange["replacement_order_number"] == "SO-034"
    assert original_shipment.type == "shipment"
    assert customer_return.type == "return"
    assert replacement_shipment.type == "shipment"
    assert original_shipment.occurred_at < customer_return.occurred_at
    assert customer_return.occurred_at < replacement_shipment.occurred_at

    prepayment = cases["customer_prepayment"]
    prepayment_shipment = record_by_id(
        session, Movement, prepayment["shipment_movement_id"]
    )
    assert prepayment["order_number"] == "SO-035"
    assert core.open_invoice_amount(session, tenant, prepayment["invoice_id"]) == 0
    assert (
        datetime.fromisoformat(prepayment["payment_effective_at"])
        < prepayment_shipment.occurred_at
    )


def _demo_company(session, owner, key: str) -> str:
    tenant = company_setup.create_company(
        session,
        owner.id,
        key,
        "Harbor Supply",
        "sandbox",
        "international_demo",
        confirmed=True,
    )["tenant_id"]
    # The profile is seeded by the worker since feature 199.
    assert seed_company(session, tenant) == "succeeded"
    return tenant


def _documents(session, tenant: str, document_type: str):
    from reality.db.core import Document

    names = {
        party.id: party.name
        for party in session.scalars(select(Party).where(Party.tenant_id == tenant))
    }
    return {
        document.number: names[document.party_id]
        for document in session.scalars(
            select(Document).where(
                Document.tenant_id == tenant, Document.type == document_type
            )
        )
    }


def test_orders_spread_over_the_customer_pool(session, scheduled_owner, monkeypatch):
    """Feature 200: every order states its own buyer, a few regulars order more."""
    from collections import Counter

    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    tenant = _demo_company(session, scheduled_owner, "spread")
    orders = _documents(session, tenant, "sales_order")
    portfolio_orders = {
        number: buyer
        for number, buyer in orders.items()
        if number in {f"SO-{index:03}" for index in range(25, 30)}
    }
    assert len(portfolio_orders) == 5, portfolio_orders
    operational_orders = {
        number: buyer
        for number, buyer in orders.items()
        if number not in portfolio_orders
    }
    # SO-040 and SO-041 add the connected B2B fulfilment and cancellation cases.
    assert len(operational_orders) == 36
    held = Counter(operational_orders.values())
    assert len(held) >= 15, held
    assert max(held.values()) <= 5, held
    assert sum(1 for count in held.values() if count > 2) <= 6, held
    suppliers = _documents(session, tenant, "purchase_order")
    assert len(set(suppliers.values())) == 3, suppliers


def test_comparison_windows_and_money_state_one_buyer(
    session, scheduled_owner, monkeypatch
):
    """Feature 200: a family compares one customer; its money follows the order."""
    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    tenant = _demo_company(session, scheduled_owner, "families")
    orders = _documents(session, tenant, "sales_order")
    for prior, current in ((12, 13), (14, 15), (16, 17), (19, 20), (22, 23)):
        assert orders[f"SO-{prior:03}"] == orders[f"SO-{current:03}"]
    invoices = _documents(session, tenant, "sales_invoice")
    assert invoices
    from reality.db.core import Document, SourceRecord

    authored_invoices = session.execute(
        select(SourceRecord.external_id, Document.party_id)
        .join(
            Document,
            (Document.tenant_id == SourceRecord.tenant_id)
            & (Document.source_record_id == SourceRecord.id),
        )
        .where(
            Document.tenant_id == tenant,
            Document.type == "sales_invoice",
            SourceRecord.external_id.like("INV-%"),
        )
    ).all()
    assert len(authored_invoices) == len(HISTORY)
    credits = _documents(session, tenant, "credit_note")
    assert credits == {
        "CN-001": orders["SO-018"],
        "CN-002": "Northstar Outdoor",
        "CN-003": orders["SO-030"],
    }


def test_seeded_buyers_are_authored_not_drawn(session, scheduled_owner, monkeypatch):
    """Feature 200: the same profile version seeds the same buyer everywhere."""
    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    first = _documents(
        session, _demo_company(session, scheduled_owner, "a"), "sales_order"
    )
    second = _documents(
        session, _demo_company(session, scheduled_owner, "b"), "sales_order"
    )
    assert first == second


def _open_amounts(session, tenant: str, document_type: str) -> dict:
    """What each settleable document still owes, read the way Finance reads it."""
    from decimal import Decimal

    from reality.db.core import Document
    from reality.services import core

    return {
        document.number: (
            abs(core.open_invoice_amount(session, tenant, document.id)),
            Decimal(document.gross_amount),
        )
        for document in session.scalars(
            select(Document).where(
                Document.tenant_id == tenant, Document.type == document_type
            )
        )
    }


def _states(amounts: dict) -> dict:
    return {
        number: "paid"
        if open_amount == 0
        else "part"
        if open_amount < gross
        else "open"
        for number, (open_amount, gross) in amounts.items()
    }


def test_seeded_invoices_are_settled_in_three_states(
    session, scheduled_owner, monkeypatch
):
    """Feature 204: the company gets paid, so open items mean something."""
    from collections import Counter
    from decimal import Decimal

    from reality.db.core import Document

    tenant = _demo_company(session, scheduled_owner, "settled")
    states = Counter(_states(_open_amounts(session, tenant, "sales_invoice")).values())
    assert states["paid"] >= 7, states
    assert states["part"] >= 1, states
    assert states["open"] >= 7, states
    payment_count = session.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.tenant_id == tenant, Document.type == "customer_payment")
    )
    # CN-001, CN-003, the exact reversal and the customer-deposit clearing create
    # settlement states without an ordinary customer-payment document.
    assert payment_count + 4 == states["paid"] + states["part"]
    receivable = sum(
        open_amount
        for open_amount, _ in _open_amounts(session, tenant, "sales_invoice").values()
    )
    invoiced = sum(
        gross for _, gross in _open_amounts(session, tenant, "sales_invoice").values()
    )
    assert Decimal(0) < receivable < invoiced, (receivable, invoiced)


def test_purchases_cover_the_whole_chain(session, scheduled_owner, monkeypatch):
    """Feature 204: ordered, received, invoiced and paid in every combination."""
    from decimal import Decimal

    from reality.db.core import Commitment, PlaygroundRun
    from reality.services import core

    tenant = _demo_company(session, scheduled_owner, "purchases")
    orders = _documents(session, tenant, "purchase_order")
    # PO-010 is the customer-linked procurement case added to the full chain.
    assert len(orders) == 10, orders
    assert len(set(orders.values())) == 3, "every supplier takes part"
    payables = _states(_open_amounts(session, tenant, "supplier_invoice"))
    assert payables["SINV-011"] == "open", payables
    operational_payables = {
        number: state
        for number, state in payables.items()
        if number
        in {
            "SINV-002",
            "SINV-004",
            "SINV-005",
            "SINV-007",
            "SINV-008",
            "SINV-010",
            "SINV-012",
        }
    }
    assert sorted(operational_payables.values()) == [
        "open",
        "open",
        "paid",
        "paid",
        "paid",
        "part",
        "part",
    ], payables
    run = session.scalar(select(PlaygroundRun).where(PlaygroundRun.tenant_id == tenant))
    received = {}
    for key, case in run.initialization_progress["cases"].items():
        if not key.startswith("S"):
            continue
        commitment = record_by_id(session, Commitment, case["commitment_id"])
        received[key] = core.fulfilled_quantity(session, tenant, commitment.id)
    assert received["S01"] == Decimal(2), received
    assert received["S03"] == Decimal(0), received
    assert sum(1 for value in received.values() if value == Decimal(5)) == 6, received
    assert received["S07"] == Decimal(5), received
    assert received["S08"] == Decimal(5), received
    assert received["S09"] == Decimal(0), received
    assert (
        record_by_id(
            session,
            Commitment,
            run.initialization_progress["cases"]["S09"]["commitment_id"],
        ).status
        == "cancelled"
    )
    supplier_credits = _open_amounts(session, tenant, "supplier_credit_note")
    assert supplier_credits["SCN-007"][0] == Decimal(0)


def test_settlement_is_authored_not_drawn(session, scheduled_owner, monkeypatch):
    """Feature 204: the same profile version settles the same way everywhere."""
    first = _demo_company(session, scheduled_owner, "settle-a")
    second = _demo_company(session, scheduled_owner, "settle-b")
    for document_type in ("sales_invoice", "supplier_invoice"):
        assert _states(_open_amounts(session, first, document_type)) == _states(
            _open_amounts(session, second, document_type)
        ), document_type


def test_finance_fangfragen_are_deterministic_and_explainable(
    session, scheduled_owner, monkeypatch
):
    """Feature 246: common sales-demo settlement questions have fixed answers."""
    import json
    from decimal import Decimal

    from reality.db.core import ChangeProposal, Document, SourceRecord
    from reality.services import core
    from reality.services.finance.credits import available_credit_rows

    tenant = _demo_company(session, scheduled_owner, "finance-cases")
    run = session.scalar(select(PlaygroundRun).where(PlaygroundRun.tenant_id == tenant))
    cases = run.initialization_progress["cases"]

    for key in (
        "supplier_discount",
        "customer_overpayment",
        "supplier_overpayment",
        "accepted_small_remainder",
    ):
        assert key in cases
        assert core.open_invoice_amount(session, tenant, cases[key]["invoice_id"]) == 0

    customer_credit, _ = available_credit_rows(
        session, tenant, side="customer", status="outstanding"
    )
    supplier_credit, _ = available_credit_rows(
        session, tenant, side="supplier", status="outstanding"
    )
    assert {row["number"]: Decimal(row["open"]) for row in customer_credit}[
        "CPAY-009"
    ] == Decimal(10)
    assert {row["number"]: Decimal(row["open"]) for row in supplier_credit}[
        "SPAY-005"
    ] == Decimal(10)

    adjustments = {
        key: record_by_id(session, Document, cases[key]["adjustment_document_id"])
        for key in ("supplier_discount", "accepted_small_remainder")
    }
    assert adjustments["supplier_discount"].type == "supplier_settlement_adjustment"
    assert (
        adjustments["accepted_small_remainder"].type == "customer_settlement_adjustment"
    )
    reasons = {
        key: json.loads(
            record_by_id(session, SourceRecord, document.source_record_id).payload
        )["reason_category"]
        for key, document in adjustments.items()
    }
    assert reasons == {
        "supplier_discount": "early_payment_discount",
        "accepted_small_remainder": "accepted_small_remainder",
    }
    adjustment_actions = list(
        session.scalars(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:finance.adjustment.accept",
            )
        )
    )
    assert len(adjustment_actions) == 3
    assert {action.status for action in adjustment_actions} == {"executed"}


def test_the_profile_may_settle_but_not_decide(session, scheduled_owner):
    """Feature 204: the seed gained settlement, and nothing beyond it."""
    from reality.services.tenant_policy import _PROFILE_OPERATIONS

    assert {
        "post_customer_payment",
        "allocate_credit_note",
        "record_customer_payment",
        "post_supplier_invoice",
        "post_supplier_credit_note",
        "allocate_supplier_credit_note",
        "post_supplier_payment",
        "record_supplier_payment",
        "allocate_settlement",
    } <= _PROFILE_OPERATIONS
    for denied in (
        "post_customer_refund",
        "record_customer_refund",
        "archive_tenant",
        "create_change_proposal",
    ):
        assert denied not in _PROFILE_OPERATIONS, denied
