"""Atomic synthetic evidence prepared through shared application services."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import PaymentTerm, PlaygroundRun
from reality.demo.international import (
    CUSTOMERS,
    DEMO_DATA_PAYMENT_TERM,
    HISTORY,
    ITEMS,
    LOCATIONS,
    ORDER_CUSTOMERS,
    PROFILE_VERSION,
    PURCHASES,
    SETTLEMENT,
    SUPPLIER_ITEMS,
    SUPPLIERS,
    WEEKLY_CUSTOMERS,
    WEEKLY_SETTLEMENT,
    item_number,
)
from reality.integrations.demo_data import demo_invoice_number
from reality.services import core


def _cost_action(session: Session, run: PlaygroundRun, arguments: dict) -> dict:
    """Execute one fixed canonical-profile cost decision without committing."""
    from reality.services.analytics.reports import caller
    from reality.services.costing import execute_cost_change
    from reality.services.memberships import Principal
    from reality.services.tenant_policy import profile_cost_action_scope
    from reality.tools.application import create_change_proposal

    with profile_cost_action_scope(session, run.id, run.owner_user_id, arguments):
        with caller(Principal(run.owner_user_id)):
            action = create_change_proposal(
                session,
                run.tenant_id,
                "cost.change",
                arguments,
                actor_type="system",
                _commit=False,
            )
        return execute_cost_change(
            session,
            run.tenant_id,
            arguments=arguments,
            action_id=action.id,
            actor_id=run.owner_user_id,
            confirmed=True,
        )


def _settlement_adjustment(
    session: Session,
    run: PlaygroundRun,
    invoice_id: str,
    amount: str,
    *,
    reason_category: str,
    reason: str,
    agreement: str = "",
) -> dict:
    """Execute one fixed accepted reduction inside confirmed profile setup."""
    import json

    from reality.services.analytics.reports import caller
    from reality.services.finance.settlement import (
        accept_adjustment,
        adjustment_context,
    )
    from reality.services.memberships import Principal
    from reality.services.tenant_policy import profile_finance_action_scope
    from reality.tools.application import create_change_proposal

    context = adjustment_context(session, run.tenant_id, invoice_id)
    arguments = {
        "invoice_id": invoice_id,
        "amount": amount,
        "expected_revision": context["revision"],
        "reason_category": reason_category,
        "reason": reason,
        "agreement": agreement,
    }
    with profile_finance_action_scope(session, run.id, run.owner_user_id, arguments):
        with caller(Principal(run.owner_user_id)):
            action = create_change_proposal(
                session,
                run.tenant_id,
                "finance.adjustment.accept",
                arguments,
                actor_type="system",
                _commit=False,
            )
        result = accept_adjustment(
            session,
            run.tenant_id,
            action_id=action.id,
            actor_id=run.owner_user_id,
            **arguments,
        )
        action.status = "executed"
        action.decided_at = core.now()
        action.decided_by_user_id = run.owner_user_id
        action.output = json.dumps(result, sort_keys=True)
        return result


def _finance_action(
    session: Session, run: PlaygroundRun, tool_name: str, arguments: dict
) -> dict:
    """Execute one fixed finance action through the normal confirmed dispatcher."""
    import json

    from reality.services.analytics.reports import caller
    from reality.services.memberships import Principal
    from reality.services.tenant_policy import profile_finance_action_scope
    from reality.tools.application import create_change_proposal
    from reality.tools.finance import execute_finance_command

    with profile_finance_action_scope(
        session,
        run.id,
        run.owner_user_id,
        arguments,
        tool_name=tool_name,
    ):
        with caller(Principal(run.owner_user_id)):
            action = create_change_proposal(
                session,
                run.tenant_id,
                tool_name,
                arguments,
                actor_type="system",
                _commit=False,
            )
        result = execute_finance_command(
            session,
            run.tenant_id,
            tool_name,
            arguments,
            action_id=action.id,
            actor_id=run.owner_user_id,
        )
        action.status = "executed"
        action.decided_at = core.now()
        action.decided_by_user_id = run.owner_user_id
        action.output = json.dumps(result, sort_keys=True)
        return result


def seed_profile(
    session: Session, run: PlaygroundRun, anchor: datetime, *, execution: bool = False
) -> dict:
    tenant = run.tenant_id
    payment_term = session.scalar(
        select(PaymentTerm).where(
            PaymentTerm.tenant_id == tenant,
            PaymentTerm.code == DEMO_DATA_PAYMENT_TERM["code"],
        )
    )
    if payment_term is None:
        payment_term = core.create_payment_term(
            session,
            tenant,
            **DEMO_DATA_PAYMENT_TERM,
            source_system="demo_profile",
            external_id=DEMO_DATA_PAYMENT_TERM["code"],
            source_payload={**DEMO_DATA_PAYMENT_TERM, "synthetic": True},
            _commit=False,
        )

    def create_document_with_lines(*args, **kwargs):
        """Use the normal evidence service and bind invoice terms explicitly."""
        if len(args) > 2 and args[2] in {"sales_invoice", "supplier_invoice"}:
            kwargs["payment_term_code"] = payment_term.code
        return core.create_manual_document_with_lines(*args, **kwargs)

    parties, items, locations, cases = {}, {}, {}, {}
    sales_order_sequence = 0
    vocabulary = [("company", "Harbor Supply", "company")]
    vocabulary += [(f"C{i}", name, "customer") for i, name in enumerate(CUSTOMERS, 1)]
    vocabulary += [(f"S{i}", name, "supplier") for i, name in enumerate(SUPPLIERS, 1)]
    for key, name, role in vocabulary[:2] if execution else vocabulary:
        parties[key] = core.create_party(
            session,
            tenant,
            name,
            role,
            source_system="demo_profile",
            external_id=key,
            source_payload={"key": key, "name": name, "role": role, "synthetic": True},
            _commit=False,
        ).id
    for key, name in zip(("A", "B"), LOCATIONS, strict=True):
        if execution and key == "B":
            continue
        locations[key] = core.create_location(
            session,
            tenant,
            name,
            source_system="demo_profile",
            external_id=key,
            source_payload={"key": key, "name": name, "synthetic": True},
            _commit=False,
        ).id
    for key, name, unit, category in ITEMS[:2] if execution else ITEMS:
        items[key] = core.create_item(
            session,
            tenant,
            item_number(key),
            name,
            unit,
            source_system="demo_profile",
            external_id=key,
            source_payload={
                "key": key,
                "name": name,
                "unit": unit,
                "category": category,
                "synthetic": True,
                "cost_basis": None,
            },
            default_location_id=locations["A"],
            tracking_type=(
                "lot" if key == "P17" else "serial" if key == "P18" else "none"
            ),
            _commit=False,
        ).id

    def source(kind: str, key: str, payload: dict):
        return core.store_source_record(
            session,
            tenant,
            "demo_profile",
            kind,
            key,
            {"synthetic": True, "profile_version": PROFILE_VERSION, **payload},
        )[0]

    def buyer(key: str) -> str:
        """The authored customer of a case key; one family compares one buyer."""
        family, _, week = key.partition("-")
        return (
            WEEKLY_CUSTOMERS[int(week) % len(WEEKLY_CUSTOMERS)]
            if family == "week"
            else ORDER_CUSTOMERS[family]
        )

    def order(
        key: str,
        item: str,
        *,
        counterparty: str,
        quantity: str = "5",
        price: str = "10",
        gross: str = "50",
        currency: str = "EUR",
        date: datetime = anchor,
        due: datetime | None = None,
        purchase: bool = False,
    ):
        nonlocal sales_order_sequence
        if purchase:
            document_number = key
        else:
            sales_order_sequence += 1
            document_number = f"SO-{sales_order_sequence:03}"
        unit = next(row[2] for row in ITEMS if row[0] == item)
        lines = [
            {
                "item_id": items[item],
                "quantity": quantity,
                "unit_price": price,
                "gross_amount": gross,
                "unit": unit,
                "source_line_id": f"{key}-1",
            }
        ]
        payload = {
            "number": document_number,
            "date": date.isoformat(),
            "due_at": due.isoformat() if due else None,
            "currency": currency,
            "lines": lines,
            "gross_amount": gross,
            "amount_basis": "gross",
            "tax_amount": "0",
            "discount_amount": "0",
            "sales_channel": "demo_wholesale",
            "external_customer_reference": f"demo:{counterparty}",
        }
        src = source("purchase_order" if purchase else "sales_order", key, payload)
        party = parties[counterparty]
        doc, doc_lines = create_document_with_lines(
            session,
            tenant,
            "purchase_order" if purchase else "sales_order",
            document_number,
            party,
            lines,
            gross,
            currency=currency,
            document_date=date.date().isoformat(),
            ordered_at=date,
            requested_delivery_at=due,
            sales_channel="demo_wholesale",
            source_record_id=src.id,
            _commit=False,
        )
        commitment = core.create_commitment(
            session,
            tenant,
            "supplier_delivery" if purchase else "customer_delivery",
            party if purchase else parties["company"],
            parties["company"] if purchase else party,
            items[item],
            locations["A"],
            quantity,
            due,
            amount=gross,
            currency=currency,
            document_id=doc.id,
            document_line_id=doc_lines[0].id,
            _commit=False,
        )
        return {
            "source_id": src.id,
            "document_id": doc.id,
            "line_id": doc_lines[0].id,
            "commitment_id": commitment.id,
            "number": document_number,
        }, lines

    def movement(
        key: str,
        item: str,
        quantity: str,
        kind: str = "receipt",
        *,
        location: str = "A",
        commitment: str | None = None,
        date: datetime = anchor,
    ):
        src = source(
            "movement",
            key,
            {
                "type": kind,
                "item_key": item,
                "quantity": quantity,
                "unit": next(row[2] for row in ITEMS if row[0] == item),
                "location_key": location,
                "occurred_at": date.isoformat(),
            },
        )
        kwargs = {
            "from_location_id"
            if kind in {"shipment", "supplier_return"}
            else "to_location_id": locations[location]
        }
        return core.record_movement(
            session,
            tenant,
            kind,
            items[item],
            quantity,
            commitment_id=commitment,
            source_record_id=src.id,
            occurred_at=date,
            _commit=False,
            **kwargs,
        )

    if execution:
        for index in (1, 2):
            key, item = f"E{index:02}", f"P{index:02}"
            cases[key], _ = order(
                key,
                item,
                counterparty=buyer(key),
                quantity="1",
                gross="10",
                due=anchor + timedelta(days=3),
            )
            movement(f"opening-{item}", item, "1")
        core.hold_commitment(
            session,
            tenant,
            cases["E02"]["commitment_id"],
            "manual_review",
            "Synthetic refusal case",
            _commit=False,
        )
    else:
        for index, quantity in enumerate(
            ("10", "10", "2", "2", "5", "10", "10", "0", "5", "10"), 1
        ):
            key, item = f"O{index:02}", f"P{index:02}"
            cases[key], _ = order(
                key,
                item,
                counterparty=buyer(key),
                due=anchor + timedelta(days=-2 if index in {4, 5, 8} else 3),
            )
            if quantity != "0":
                movement(f"opening-{item}", item, quantity)
            commitment = cases[key]["commitment_id"]
            if index in {1, 4, 5, 10}:
                core.reserve(
                    session,
                    tenant,
                    commitment,
                    "2" if index == 4 else "5",
                    _commit=False,
                )
            if index in {6, 9}:
                movement(
                    f"shipment-{item}",
                    item,
                    "3" if index == 6 else "5",
                    "shipment",
                    commitment=commitment,
                )
            if index in {7, 8}:
                core.hold_commitment(
                    session,
                    tenant,
                    commitment,
                    "manual_review",
                    "Synthetic review hold",
                    _commit=False,
                )
            if index == 10:
                core.cancel_commitment(session, tenant, commitment, _commit=False)
        cases["O11"], _ = order(
            "O11",
            "P06",
            counterparty=buyer("O11"),
            due=anchor + timedelta(days=3),
        )
        movement(
            "shipment-cancelled-remainder",
            "P06",
            "2",
            "shipment",
            commitment=cases["O11"]["commitment_id"],
        )
        core.cancel_commitment(
            session, tenant, cases["O11"]["commitment_id"], _commit=False
        )
        movement("wrong-location", "P08", "8", location="B")
        # Feature 204: ordered, received, invoiced and paid in every combination, so a
        # person can follow one purchase all the way to the money.
        for index, (key, item, ordered, received, invoiced, paid) in enumerate(
            PURCHASES, 1
        ):
            due = (
                anchor + timedelta(days=-3 if index == 1 else 5) if index != 3 else None
            )
            ref, order_lines = order(
                f"PO-{index:03}",
                item,
                counterparty=SUPPLIER_ITEMS[item],
                quantity=ordered,
                purchase=True,
                due=due,
                date=anchor - timedelta(days=20),
            )
            cases[key] = ref
            if received != "0":
                movement(
                    f"purchase-receipt-{key}",
                    item,
                    received,
                    commitment=ref["commitment_id"],
                    date=anchor - timedelta(days=12),
                )
            if invoiced is None:
                continue
            invoice_date = anchor - timedelta(days=10)
            invoice_lines = [
                {**order_lines[0], "billed_document_line_id": ref["line_id"]}
            ]
            src = source(
                "supplier_invoice",
                f"SINV-{index:03}",
                {
                    "date": invoice_date.isoformat(),
                    "lines": invoice_lines,
                    "currency": "EUR",
                    "gross_amount": invoiced,
                    "amount_basis": "gross",
                    "tax_amount": "0",
                    "discount_amount": "0",
                },
            )
            supplier_invoice, _ = create_document_with_lines(
                session,
                tenant,
                "supplier_invoice",
                f"SINV-{index:03}",
                parties[SUPPLIER_ITEMS[item]],
                invoice_lines,
                invoiced,
                document_date=invoice_date.date().isoformat(),
                source_record_id=src.id,
                _commit=False,
            )
            core.post_supplier_invoice(
                session,
                tenant,
                supplier_invoice.id,
                effective_at=invoice_date,
                _commit=False,
            )
            cases[key] = {**ref, "supplier_invoice_id": supplier_invoice.id}
            if paid is None:
                continue
            core.post_supplier_payment(
                session,
                tenant,
                supplier_invoice.id,
                paid,
                payment_number=f"SPAY-{index:03}",
                effective_at=anchor - timedelta(days=5),
                _commit=False,
            )
        # Feature 246: deterministic settlement examples answer the ordinary
        # finance questions every demo receives. Cash is recorded as stated;
        # allocation and accepted reductions remain separate evidence.
        from reality.services.finance.accounts import (
            create_account,
            list_accounts,
            set_default_account,
        )

        for role, name in (
            ("customer_reduction", "Customer reductions"),
            ("supplier_reduction", "Supplier reductions"),
            ("bad_debt_expense", "Customer bad-debt expense"),
            ("dunning_fee_revenue", "Dunning fee revenue"),
        ):
            account = create_account(
                session,
                tenant,
                code=role,
                name=name,
                role=role,
                _commit=False,
            )
            set_default_account(
                session,
                tenant,
                role=role,
                account_id=account["id"],
                _commit=False,
            )

        supplier_discount = cases["S02"]
        discount_payment_source = source(
            "supplier_payment",
            "SPAY-002",
            {
                "number": "SPAY-002",
                "date": (anchor - timedelta(days=5)).isoformat(),
                "amount": "49",
                "currency": "EUR",
                "invoice_external_reference": "SINV-002",
            },
        )
        core.post_supplier_payment(
            session,
            tenant,
            supplier_discount["supplier_invoice_id"],
            "49",
            payment_number="SPAY-002",
            source_record_id=discount_payment_source.id,
            effective_at=anchor - timedelta(days=5),
            _commit=False,
        )
        discount_adjustment = _settlement_adjustment(
            session,
            run,
            supplier_discount["supplier_invoice_id"],
            "1",
            reason_category="early_payment_discount",
            reason="2% early-payment discount taken inside the stated seven-day window",
            agreement="Supplier invoice terms state 2% discount within seven days",
        )
        cases["supplier_discount"] = {
            "invoice_id": supplier_discount["supplier_invoice_id"],
            "payment_number": "SPAY-002",
            "adjustment_document_id": discount_adjustment["document_id"],
        }

        supplier_overpayment = cases["S05"]
        supplier_overpayment_source = source(
            "supplier_payment",
            "SPAY-005",
            {
                "number": "SPAY-005",
                "date": (anchor - timedelta(days=5)).isoformat(),
                "amount": "60",
                "currency": "EUR",
                "invoice_external_reference": "SINV-005",
            },
        )
        supplier_payment_entries = core.record_supplier_payment(
            session,
            tenant,
            parties[SUPPLIER_ITEMS["P16"]],
            "60",
            payment_number="SPAY-005",
            source_record_id=supplier_overpayment_source.id,
            effective_at=anchor - timedelta(days=5),
            _control_account_id=core._settlement_control_entry(
                session, tenant, supplier_overpayment["supplier_invoice_id"]
            ).account_id,
            _commit=False,
        )
        core.allocate_settlement(
            session,
            tenant,
            core._control_entry(supplier_payment_entries, "accounts_payable").id,
            core._settlement_control_entry(
                session, tenant, supplier_overpayment["supplier_invoice_id"]
            ).id,
            "50",
            _commit=False,
        )
        cases["supplier_overpayment"] = {
            "invoice_id": supplier_overpayment["supplier_invoice_id"],
            "payment_number": "SPAY-005",
        }
        # Feature 246: ordinary purchase exceptions remain normal source-backed
        # documents and Reality movements, not special fixture state.
        for key, item, returned, credited in (
            ("S07", "P01", "2", "20"),
            ("S08", "P02", "1", None),
        ):
            ref, purchase_lines = order(
                f"PO-{int(key[1:]):03}",
                item,
                counterparty="S3",
                quantity="5",
                purchase=True,
                due=anchor + timedelta(days=5),
                date=anchor - timedelta(days=20),
            )
            movement(
                f"purchase-receipt-{key}",
                item,
                "5",
                commitment=ref["commitment_id"],
                date=anchor - timedelta(days=12),
            )
            invoice_date = anchor - timedelta(days=10)
            invoice_lines = [
                {**purchase_lines[0], "billed_document_line_id": ref["line_id"]}
            ]
            invoice_source = source(
                "supplier_invoice",
                f"SINV-{int(key[1:]):03}",
                {
                    "number": f"SINV-{int(key[1:]):03}",
                    "date": invoice_date.isoformat(),
                    "lines": invoice_lines,
                    "currency": "EUR",
                    "gross_amount": "50",
                    "amount_basis": "gross",
                    "tax_amount": "0",
                    "discount_amount": "0",
                },
            )
            supplier_invoice, _ = create_document_with_lines(
                session,
                tenant,
                "supplier_invoice",
                f"SINV-{int(key[1:]):03}",
                parties["S3"],
                invoice_lines,
                "50",
                document_date=invoice_date.date().isoformat(),
                source_record_id=invoice_source.id,
                _commit=False,
            )
            core.post_supplier_invoice(
                session,
                tenant,
                supplier_invoice.id,
                effective_at=invoice_date,
                _commit=False,
            )
            returned_movement = movement(
                f"supplier-return-{key}",
                item,
                returned,
                "supplier_return",
                commitment=ref["commitment_id"],
                date=anchor - timedelta(days=4),
            )
            cases[key] = {
                **ref,
                "supplier_invoice_id": supplier_invoice.id,
                "supplier_return_id": returned_movement.id,
            }
            if credited is not None:
                credit_date = anchor - timedelta(days=3)
                credit_lines = [
                    {
                        **purchase_lines[0],
                        "quantity": returned,
                        "gross_amount": credited,
                        "billed_document_line_id": ref["line_id"],
                    }
                ]
                credit_source = source(
                    "supplier_credit_note",
                    f"SCN-{int(key[1:]):03}",
                    {
                        "number": f"SCN-{int(key[1:]):03}",
                        "date": credit_date.isoformat(),
                        "lines": credit_lines,
                        "currency": "EUR",
                        "gross_amount": credited,
                    },
                )
                credit, _ = create_document_with_lines(
                    session,
                    tenant,
                    "supplier_credit_note",
                    f"SCN-{int(key[1:]):03}",
                    parties["S3"],
                    credit_lines,
                    credited,
                    document_date=credit_date.date().isoformat(),
                    source_record_id=credit_source.id,
                    _commit=False,
                )
                core.post_supplier_credit_note(
                    session,
                    tenant,
                    credit.id,
                    effective_at=credit_date,
                    _commit=False,
                )
                core.allocate_supplier_credit_note(
                    session,
                    tenant,
                    credit.id,
                    supplier_invoice.id,
                    credited,
                    _commit=False,
                )
                cases[key]["supplier_credit_id"] = credit.id

        cancel_ref, _ = order(
            "PO-009",
            "P01",
            counterparty="S3",
            quantity="5",
            purchase=True,
            due=anchor + timedelta(days=5),
            date=anchor - timedelta(days=20),
        )
        core.cancel_commitment(
            session, tenant, cancel_ref["commitment_id"], _commit=False
        )
        cases["S09"] = cancel_ref
        history = list(HISTORY)
        history_cost_rows = []
        for history_index, (
            key,
            item,
            days,
            quantity,
            price,
            gross,
            currency,
        ) in enumerate(history, 1):
            # Keep the authored foreign-currency comparison on its own SKU so its
            # retained acquisition basis does not pretend that EUR and USD opening
            # values are interchangeable for one physical stock pool.
            if currency != "EUR":
                item = "P09"
            date = anchor - timedelta(days=days)
            invoice_number = demo_invoice_number(date, f"seed:{key}")
            customer = buyer(key)
            ref, lines = order(
                f"H-{key}",
                item,
                counterparty=customer,
                quantity=quantity,
                price=price,
                gross=gross,
                currency=currency,
                date=date,
            )
            invoice_lines = [
                {
                    **lines[0],
                    "billed_document_line_id": ref["line_id"],
                    "reality_finance_v1": {"net": gross, "tax": "0"},
                }
            ]
            src = source(
                "sales_invoice",
                f"INV-{key}",
                {
                    "number": invoice_number,
                    "date": date.isoformat(),
                    "lines": invoice_lines,
                    "currency": currency,
                    "gross_amount": gross,
                    "amount_basis": "gross",
                    "tax_amount": "0",
                    "discount_amount": "0",
                },
            )
            invoice, created_invoice_lines = create_document_with_lines(
                session,
                tenant,
                "sales_invoice",
                invoice_number,
                parties[customer],
                invoice_lines,
                gross,
                currency=currency,
                document_date=date.date().isoformat(),
                source_record_id=src.id,
                _commit=False,
            )
            core.post_sales_invoice(
                session, tenant, invoice.id, effective_at=date, _commit=False
            )
            receipt = movement(
                f"history-receipt-{key}",
                item,
                quantity,
                "opening_stock",
                date=date,
            )
            shipment = movement(
                f"history-shipment-{key}",
                item,
                quantity,
                "shipment",
                commitment=ref["commitment_id"],
                date=date,
            )
            history_cost_rows.append(
                {
                    "key": key,
                    "item": item,
                    "quantity": quantity,
                    "currency": currency,
                    "receipt": receipt,
                    "shipment": shipment,
                    "invoice": invoice,
                    "invoice_line": created_invoice_lines[0],
                }
            )
            if key == "credit-origin":
                credit_date = anchor - timedelta(days=10)
                credit_lines = [
                    {
                        **invoice_lines[0],
                        "quantity": "10",
                        "gross_amount": "120",
                        "billed_document_line_id": None,
                    }
                ]
                credit_source = source(
                    "credit_note",
                    "CN-001",
                    {
                        "invoice_external_reference": f"INV-{key}",
                        "order_external_reference": f"H-{key}",
                        "lines": credit_lines,
                        "gross_amount": "120",
                        "currency": "EUR",
                        "amount_basis": "gross",
                        "tax_amount": "0",
                        "discount_amount": "0",
                        "date": credit_date.isoformat(),
                    },
                )
                credit, _ = create_document_with_lines(
                    session,
                    tenant,
                    "credit_note",
                    "CN-001",
                    parties[customer],
                    credit_lines,
                    "120",
                    document_date=credit_date.date().isoformat(),
                    source_record_id=credit_source.id,
                    _commit=False,
                )
                core.post_sales_credit_note(
                    session, tenant, credit.id, effective_at=credit_date, _commit=False
                )
                core.allocate_credit_note(
                    session,
                    tenant,
                    credit.id,
                    invoice.id,
                    "120",
                    _commit=False,
                )
                returned = movement(
                    "return-001",
                    item,
                    "10",
                    "return",
                    date=credit_date,
                )
                cases["credit_return"] = {
                    **ref,
                    "invoice_id": invoice.id,
                    "credit_id": credit.id,
                    "return_movement_id": returned.id,
                }
            # Feature 204: the invoice is settled last, so a credit note has already
            # reduced what is open and the payment states what was really received.
            settlement = (
                WEEKLY_SETTLEMENT[int(key.removeprefix("week-"))]
                if key.startswith("week-")
                else SETTLEMENT[key]
            )
            if key == "decline-current":
                payment_source = source(
                    "customer_payment",
                    "CPAY-006",
                    {
                        "number": "CPAY-006",
                        "date": min(date + timedelta(days=10), anchor).isoformat(),
                        "amount": "74.50",
                        "currency": currency,
                        "invoice_external_reference": invoice.number,
                    },
                )
                core.post_customer_payment(
                    session,
                    tenant,
                    invoice.id,
                    "74.50",
                    payment_number="CPAY-006",
                    source_record_id=payment_source.id,
                    effective_at=min(date + timedelta(days=10), anchor),
                    _commit=False,
                )
                adjustment = _settlement_adjustment(
                    session,
                    run,
                    invoice.id,
                    "0.50",
                    reason_category="accepted_small_remainder",
                    reason="Aged fifty-cent customer remainder reviewed and accepted",
                )
                cases["accepted_small_remainder"] = {
                    "invoice_id": invoice.id,
                    "payment_number": "CPAY-006",
                    "adjustment_document_id": adjustment["document_id"],
                }
            elif key == "outlier-current":
                payment_source = source(
                    "customer_payment",
                    "CPAY-009",
                    {
                        "number": "CPAY-009",
                        "date": min(date + timedelta(days=10), anchor).isoformat(),
                        "amount": "5010",
                        "currency": currency,
                        "invoice_external_reference": invoice.number,
                    },
                )
                payment_entries = core.record_customer_payment(
                    session,
                    tenant,
                    invoice.party_id,
                    "5010",
                    currency=currency,
                    payment_number="CPAY-009",
                    source_record_id=payment_source.id,
                    effective_at=min(date + timedelta(days=10), anchor),
                    _control_account_id=core._settlement_control_entry(
                        session, tenant, invoice.id
                    ).account_id,
                    _commit=False,
                )
                core.allocate_settlement(
                    session,
                    tenant,
                    core._control_entry(payment_entries, "accounts_receivable").id,
                    core._settlement_control_entry(session, tenant, invoice.id).id,
                    "5000",
                    _commit=False,
                )
                cases["customer_overpayment"] = {
                    "invoice_id": invoice.id,
                    "payment_number": "CPAY-009",
                }
            elif settlement != "open":
                outstanding = core.open_invoice_amount(session, tenant, invoice.id)
                paid = outstanding if settlement == "paid" else outstanding / 2
                core.post_customer_payment(
                    session,
                    tenant,
                    invoice.id,
                    paid.quantize(Decimal("0.01")),
                    payment_number=f"CPAY-{history_index:03}",
                    effective_at=min(date + timedelta(days=10), anchor),
                    _commit=False,
                )
        original = movement("correction-original", "P16", "3")
        corrected = core.correct_movement(
            session,
            tenant,
            original.id,
            reason="Synthetic supplier corrected its stated receipt from 3 kg to 2 kg",
            replacement={
                "type": "receipt",
                "item_id": items["P16"],
                "quantity": "2",
                "to_location_id": locations["A"],
                "source_record_id": source(
                    "movement",
                    "correction-replacement",
                    {
                        "quantity": "2",
                        "unit": "kg",
                        "original_external_reference": "correction-original",
                    },
                ).id,
            },
            _commit=False,
        )
        cases["correction"] = {
            "original_movement_id": original.id,
            "correction_id": corrected.correction_id,
        }

        # FR-026 fixture A: authored source evidence enters the ordinary document,
        # movement and costing services. P03's pre-existing two units stay supplier-
        # owned for this review, while 40 company-owned units remain as a visibly
        # valued demo stock position after the sale and signed return story.
        from reality.db.core import Movement
        from reality.db.inventory_costing import CostInventoryMember, CostMovementBasis
        from reality.services.costing import _sequence, contribution_preview
        from reality.services.finance import components

        # Every ordinary sales invoice in the demo is immediately useful for a
        # margin walkthrough. The receipts above are the retained acquisition
        # evidence; a conservative, non-zero per-unit cost is reviewed through
        # the same costing services used by the product UI.
        history_rows_by_item = {}
        for selected_row in history_cost_rows:
            key = (selected_row["item"], selected_row["currency"])
            history_rows_by_item.setdefault(key, []).append(selected_row)
        for (item_key, currency), selected_rows in history_rows_by_item.items():
            rows = [row for row in history_cost_rows if row["item"] == item_key]
            unit_cost = Decimal(6)
            inventory_arguments = {
                "operation": "inventory_review",
                "expected_event_sequence": _sequence(session, tenant),
                "item_id": items[item_key],
                "owner_party_id": parties["company"],
                "method": "fifo",
                "currency": currency,
                "base_unit": next(row[2] for row in ITEMS if row[0] == item_key),
                "history_start": (
                    min(row["receipt"].occurred_at for row in rows)
                    - timedelta(seconds=1)
                ).isoformat(),
                "effective_at": max(
                    row["shipment"].occurred_at for row in rows
                ).isoformat(),
                "history_complete_from_zero": True,
                "receipt_cost_scopes_confirmed": True,
                "economic_issue_ids": [row["shipment"].id for row in rows],
                "openings": [
                    {
                        "movement_id": row["receipt"].id,
                        "evidence_source_record_id": row["receipt"].source_record_id,
                        "acquisition_cost": str(Decimal(row["quantity"]) * unit_cost),
                    }
                    for row in rows
                ],
                "ownership_parts": [
                    {
                        "movement_id": movement_row.id,
                        "owner_party_id": parties["company"],
                        "evidence_source_record_id": movement_row.source_record_id,
                        "quantity": str(movement_row.quantity),
                    }
                    for row in rows
                    for movement_row in (row["receipt"], row["shipment"])
                ],
                "reason": (
                    f"Canonical demo history cost review for {item_key} {currency}"
                ),
            }
            history_inventory = _cost_action(session, run, inventory_arguments)
            receipt_bases = {
                row["receipt"].id: session.scalar(
                    select(CostMovementBasis).where(
                        CostMovementBasis.tenant_id == tenant,
                        CostMovementBasis.movement_id == row["receipt"].id,
                    )
                )
                for row in rows
            }
            for row in selected_rows:
                issue_basis = session.scalar(
                    select(CostMovementBasis).where(
                        CostMovementBasis.tenant_id == tenant,
                        CostMovementBasis.movement_id == row["shipment"].id,
                    )
                )
                issue_member = session.scalar(
                    select(CostInventoryMember).where(
                        CostInventoryMember.tenant_id == tenant,
                        CostInventoryMember.review_id == history_inventory["review_id"],
                        CostInventoryMember.movement_basis_id == issue_basis.id,
                    )
                )
                receipt_basis = receipt_bases[row["receipt"].id]
                received = components._received(
                    session, tenant, row["invoice"], row["invoice_line"]
                )
                _cost_action(
                    session,
                    run,
                    {
                        "operation": "commercial_match_review",
                        "expected_event_sequence": _sequence(session, tenant),
                        "document_line_id": row["invoice_line"].id,
                        "expected_evidence_hash": received["evidence_hash"],
                        "profile": "commercial_v1",
                        "profile_confirmed": True,
                        "goods_cost_disposition": "inventory",
                        "inventory_parts": [
                            {
                                "inventory_member_id": issue_member.id,
                                "entry_movement_basis_id": receipt_basis.id,
                                "receipt_movement_basis_id": receipt_basis.id,
                                "quantity": row["quantity"],
                            }
                        ],
                        "reason": f"Canonical demo history match for {row['key']}",
                    },
                )
            refreshed_arguments = inventory_arguments | {
                "expected_event_sequence": _sequence(session, tenant)
            }
            _cost_action(session, run, refreshed_arguments)
            history_positions = []
            for row in selected_rows:
                candidate = contribution_preview(
                    session, tenant, row["invoice_line"].id
                )
                if candidate.get("state") != "candidate":
                    raise core.InvalidOperation(
                        f"Demo history contribution incomplete: {candidate}"
                    )
                history_positions.append(
                    {
                        "document_line_id": row["invoice_line"].id,
                        "expected_candidate_hash": candidate["candidate_hash"],
                        "profile": "commercial_v1",
                        "profile_confirmed": True,
                        "revenue_complete": True,
                        "economic_at": candidate["trace"]["proposed_economic_at"],
                        "selling_categories": [
                            {
                                "category": category,
                                "disposition": "confirmed_zero",
                                "reason": "Canonical demo history reviewed selling scope",
                            }
                            for category in (
                                "outbound_freight",
                                "fulfilment",
                                "packaging",
                                "payment_fee",
                                "marketplace_commission",
                                "sales_commission",
                                "other_selling",
                            )
                        ],
                    }
                )
            contribution_request = {
                "expected_event_sequence": _sequence(session, tenant),
                "reason": f"Canonical demo history DB2 review for {item_key}",
            }
            if len(history_positions) == 1:
                contribution_request.update(
                    operation="contribution_review", **history_positions[0]
                )
            else:
                contribution_request.update(
                    operation="contribution_batch_review",
                    positions=history_positions,
                )
            _cost_action(session, run, contribution_request)

        # Keep the canonical costing case inside the final week of the retained
        # twelve-week demo history while still ordering its events explicitly.
        fixture_time = anchor - timedelta(seconds=1)
        acquisition_source = source(
            "cost_evidence",
            "COST-A-ACQUISITION",
            {
                "item_key": "P03",
                "quantity": "100",
                "unit": "pcs",
                "currency": "EUR",
                "acquisition_cost": "1050",
            },
        )
        opening = core.record_movement(
            session,
            tenant,
            "opening_stock",
            items["P03"],
            "100",
            to_location_id=locations["A"],
            source_record_id=acquisition_source.id,
            occurred_at=fixture_time,
            _commit=False,
        )
        sale, sale_lines = order(
            "COST-A-ORDER",
            "P03",
            counterparty="C1",
            quantity="60",
            price="20",
            gross="1200",
            date=fixture_time,
        )
        issue = movement(
            "COST-A-SHIPMENT",
            "P03",
            "60",
            "shipment",
            commitment=sale["commitment_id"],
            date=fixture_time + timedelta(seconds=1),
        )
        invoice_lines = [
            {
                **sale_lines[0],
                "billed_document_line_id": sale["line_id"],
                "reality_finance_v1": {"net": "1200", "tax": "0"},
            }
        ]
        fixture_invoice_number = demo_invoice_number(fixture_time, "COST-A-INVOICE")
        invoice_source = source(
            "sales_invoice",
            "COST-A-INVOICE",
            {
                "number": fixture_invoice_number,
                "date": fixture_time.isoformat(),
                "currency": "EUR",
                "gross_amount": "1200",
                "amount_basis": "net",
                "tax_amount": "0",
                "lines": invoice_lines,
            },
        )
        _invoice, billed_lines = create_document_with_lines(
            session,
            tenant,
            "sales_invoice",
            fixture_invoice_number,
            parties["C1"],
            invoice_lines,
            "1200",
            document_date=fixture_time.date().isoformat(),
            source_record_id=invoice_source.id,
            _commit=False,
        )
        core.post_sales_invoice(
            session, tenant, _invoice.id, effective_at=fixture_time, _commit=False
        )
        prior_p03 = list(
            session.scalars(
                select(Movement).where(
                    Movement.tenant_id == tenant,
                    Movement.item_id == items["P03"],
                    Movement.id.not_in([opening.id, issue.id]),
                    Movement.occurred_at <= issue.occurred_at,
                )
            )
        )
        ownership = [
            {
                "movement_id": row.id,
                "owner_party_id": parties["S1"],
                "evidence_source_record_id": row.source_record_id,
                "quantity": str(row.quantity),
            }
            for row in prior_p03
        ] + [
            {
                "movement_id": opening.id,
                "owner_party_id": parties["company"],
                "evidence_source_record_id": acquisition_source.id,
                "quantity": "100",
            },
            {
                "movement_id": issue.id,
                "owner_party_id": parties["company"],
                "evidence_source_record_id": acquisition_source.id,
                "quantity": "60",
            },
        ]
        inventory = _cost_action(
            session,
            run,
            {
                "operation": "inventory_review",
                "expected_event_sequence": _sequence(session, tenant),
                "item_id": items["P03"],
                "owner_party_id": parties["company"],
                "method": "fifo",
                "currency": "EUR",
                "base_unit": "pcs",
                "history_start": (anchor - timedelta(seconds=1)).isoformat(),
                "effective_at": issue.occurred_at.isoformat(),
                "history_complete_from_zero": True,
                "receipt_cost_scopes_confirmed": True,
                "economic_issue_ids": [issue.id],
                "openings": [
                    {
                        "movement_id": opening.id,
                        "evidence_source_record_id": acquisition_source.id,
                        "acquisition_cost": "1050",
                    }
                ],
                "ownership_parts": ownership,
                "reason": "Canonical fixture A ownership and acquisition review",
            },
        )
        issue_basis = session.scalar(
            select(CostMovementBasis).where(
                CostMovementBasis.tenant_id == tenant,
                CostMovementBasis.movement_id == issue.id,
            )
        )
        opening_basis = session.scalar(
            select(CostMovementBasis).where(
                CostMovementBasis.tenant_id == tenant,
                CostMovementBasis.movement_id == opening.id,
            )
        )
        issue_member = session.scalar(
            select(CostInventoryMember).where(
                CostInventoryMember.tenant_id == tenant,
                CostInventoryMember.review_id == inventory["review_id"],
                CostInventoryMember.movement_basis_id == issue_basis.id,
            )
        )
        received = components._received(session, tenant, _invoice, billed_lines[0])
        commercial = _cost_action(
            session,
            run,
            {
                "operation": "commercial_match_review",
                "expected_event_sequence": _sequence(session, tenant),
                "document_line_id": billed_lines[0].id,
                "expected_evidence_hash": received["evidence_hash"],
                "profile": "commercial_v1",
                "profile_confirmed": True,
                "goods_cost_disposition": "inventory",
                "inventory_parts": [
                    {
                        "inventory_member_id": issue_member.id,
                        "entry_movement_basis_id": opening_basis.id,
                        "receipt_movement_basis_id": opening_basis.id,
                        "quantity": "60",
                    }
                ],
                "reason": "Canonical fixture A exact commercial match",
            },
        )
        returned = movement(
            "COST-LATE-RETURN",
            "P03",
            "10",
            "return",
            date=fixture_time + timedelta(seconds=3),
        )
        late_ownership = ownership + [
            {
                "movement_id": returned.id,
                "owner_party_id": parties["company"],
                "evidence_source_record_id": acquisition_source.id,
                "quantity": "10",
            },
        ]
        late_inventory_arguments = {
            "operation": "inventory_review",
            "expected_event_sequence": _sequence(session, tenant),
            "item_id": items["P03"],
            "owner_party_id": parties["company"],
            "method": "fifo",
            "currency": "EUR",
            "base_unit": "pcs",
            "history_start": (anchor - timedelta(seconds=1)).isoformat(),
            "effective_at": returned.occurred_at.isoformat(),
            "history_complete_from_zero": True,
            "receipt_cost_scopes_confirmed": True,
            "economic_issue_ids": [issue.id],
            "customer_return_ids": [returned.id],
            "openings": [
                {
                    "movement_id": opening.id,
                    "evidence_source_record_id": acquisition_source.id,
                    "acquisition_cost": "1050",
                }
            ],
            "return_parts": [
                {
                    "movement_id": returned.id,
                    "issue_movement_id": issue.id,
                    "entry_movement_id": opening.id,
                    "receipt_movement_id": opening.id,
                    "quantity": "10",
                }
            ],
            "ownership_parts": late_ownership,
            "reason": "Canonical late cost and exact customer return review",
        }
        late_inventory = _cost_action(session, run, late_inventory_arguments)
        late_issue_member = session.scalar(
            select(CostInventoryMember).where(
                CostInventoryMember.tenant_id == tenant,
                CostInventoryMember.review_id == late_inventory["review_id"],
                CostInventoryMember.movement_basis_id == issue_basis.id,
            )
        )
        return_basis = session.scalar(
            select(CostMovementBasis).where(
                CostMovementBasis.tenant_id == tenant,
                CostMovementBasis.movement_id == returned.id,
            )
        )
        return_member = session.scalar(
            select(CostInventoryMember).where(
                CostInventoryMember.tenant_id == tenant,
                CostInventoryMember.review_id == late_inventory["review_id"],
                CostInventoryMember.movement_basis_id == return_basis.id,
            )
        )
        credit_lines = [
            {
                **sale_lines[0],
                "quantity": "10",
                "gross_amount": "200",
                # The credit is matched through its exact returned inventory slice.
                # Do not pretend it is a second billing line for the order: that would
                # make the otherwise complete sale's fulfillment scope ambiguous.
                "billed_document_line_id": None,
                "reality_finance_v1": {"net": "200", "tax": "0"},
            }
        ]
        credit_source = source(
            "credit_note",
            "CN-002",
            {
                "number": "CN-002",
                "date": returned.occurred_at.isoformat(),
                "gross_amount": "200",
                "currency": "EUR",
                "lines": credit_lines,
            },
        )
        credit, credit_billed = create_document_with_lines(
            session,
            tenant,
            "credit_note",
            "CN-002",
            parties["C1"],
            credit_lines,
            "200",
            document_date=returned.occurred_at.date().isoformat(),
            source_record_id=credit_source.id,
            _commit=False,
        )
        core.post_sales_credit_note(
            session,
            tenant,
            credit.id,
            effective_at=returned.occurred_at,
            _commit=False,
        )
        credit_received = components._received(
            session, tenant, credit, credit_billed[0]
        )
        return_match = _cost_action(
            session,
            run,
            {
                "operation": "commercial_match_review",
                "expected_event_sequence": _sequence(session, tenant),
                "document_line_id": credit_billed[0].id,
                "expected_evidence_hash": credit_received["evidence_hash"],
                "profile": "commercial_v1",
                "profile_confirmed": True,
                "goods_cost_disposition": "inventory",
                "inventory_parts": [
                    {
                        "inventory_member_id": return_member.id,
                        "original_issue_member_id": late_issue_member.id,
                        "entry_movement_basis_id": opening_basis.id,
                        "receipt_movement_basis_id": opening_basis.id,
                        "quantity": "10",
                    }
                ],
                "reason": "Canonical signed return commercial match",
            },
        )
        selling_lines = [
            {
                "item_id": None,
                "quantity": "1",
                "unit": "service",
                "unit_price": "114",
                "gross_amount": "114",
                "source_line_id": "COST-A-SELLING-1",
                "description": "Authored selling costs for fixture A",
                "reality_finance_v1": {"net": "114", "tax": "0"},
            }
        ]
        selling_source = source(
            "supplier_invoice",
            "COST-A-SELLING",
            {
                "number": "SINV-012",
                "date": fixture_time.isoformat(),
                "gross_amount": "114",
                "currency": "EUR",
                "lines": selling_lines,
            },
        )
        selling_document, selling_document_lines = create_document_with_lines(
            session,
            tenant,
            "supplier_invoice",
            "SINV-012",
            parties["S1"],
            selling_lines,
            "114",
            document_date=fixture_time.date().isoformat(),
            source_record_id=selling_source.id,
            _commit=False,
        )
        core.post_supplier_invoice(
            session,
            tenant,
            selling_document.id,
            effective_at=fixture_time,
            _commit=False,
        )
        selling_evidence = components._received(
            session, tenant, selling_document, selling_document_lines[0]
        )
        _cost_action(
            session,
            run,
            {
                "operation": "selling_assign",
                "expected_event_sequence": _sequence(session, tenant),
                "reason": "Canonical fixture A authored selling costs",
                "document_id": selling_document.id,
                "document_line_id": selling_document_lines[0].id,
                "expected_evidence_hash": selling_evidence["evidence_hash"],
                "tax_treatment": "not_applicable",
                "selling_expense_confirmed": True,
                "parts": [
                    {
                        "document_line_id": billed_lines[0].id,
                        "category": "outbound_freight",
                        "source_share": "90",
                        "cost_effect": 1,
                        "assignment_kind": "direct",
                    },
                    {
                        "document_line_id": billed_lines[0].id,
                        "category": "payment_fee",
                        "source_share": "24",
                        "cost_effect": 1,
                        "assignment_kind": "allocated",
                    },
                ],
            },
        )
        late_cleanup = movement(
            "COST-LATE-CLEANUP",
            "P03",
            "10",
            "shipment",
            date=fixture_time + timedelta(seconds=4),
        )
        fixture_refreshed_arguments = late_inventory_arguments | {
            "expected_event_sequence": _sequence(session, tenant),
            "effective_at": late_cleanup.occurred_at.isoformat(),
            "economic_issue_ids": [issue.id, late_cleanup.id],
            "ownership_parts": late_ownership
            + [
                {
                    "movement_id": late_cleanup.id,
                    "owner_party_id": parties["company"],
                    "evidence_source_record_id": late_cleanup.source_record_id,
                    "quantity": "10",
                }
            ],
        }
        _cost_action(session, run, fixture_refreshed_arguments)
        candidate = contribution_preview(session, tenant, billed_lines[0].id)
        evidenced_selling = {"outbound_freight", "payment_fee"}
        contribution = _cost_action(
            session,
            run,
            {
                "operation": "contribution_review",
                "expected_event_sequence": candidate["event_sequence"],
                "reason": "Canonical fixture A complete DB2 review",
                "document_line_id": billed_lines[0].id,
                "expected_candidate_hash": candidate["candidate_hash"],
                "profile": "commercial_v1",
                "profile_confirmed": True,
                "revenue_complete": True,
                "economic_at": candidate["trace"]["proposed_economic_at"],
                "selling_categories": [
                    {
                        "category": category,
                        "disposition": (
                            "evidenced"
                            if category in evidenced_selling
                            else "confirmed_zero"
                        ),
                        "reason": "Canonical fixture A reviewed selling scope",
                    }
                    for category in (
                        "outbound_freight",
                        "fulfilment",
                        "packaging",
                        "payment_fee",
                        "marketplace_commission",
                        "sales_commission",
                        "other_selling",
                    )
                ],
            },
        )

        # Feature 243: five more complete outcomes turn the single technical proof
        # into a bounded business portfolio. Received amounts stay in ordinary
        # sources; the existing retained-cost services remain the only calculators.
        portfolio_specs = (
            ("healthy", "C3", "250", "20", "5"),
            ("low", "C4", "150", "25", "15"),
            ("negative", "C5", "130", "35", "25"),
            ("zero-selling", "C6", "180", "0", "0"),
            ("allocated-heavy", "C7", "220", "10", "50"),
        )
        portfolio_time = anchor - timedelta(minutes=1)
        portfolio_acquisition_source = source(
            "cost_evidence",
            "COST-PORTFOLIO-ACQUISITION",
            {
                "item_key": "P05",
                "quantity": "50",
                "unit": "pcs",
                "currency": "EUR",
                "acquisition_cost": "500",
            },
        )
        portfolio_opening = core.record_movement(
            session,
            tenant,
            "opening_stock",
            items["P05"],
            "50",
            to_location_id=locations["A"],
            source_record_id=portfolio_acquisition_source.id,
            occurred_at=portfolio_time,
            _commit=False,
        )
        portfolio_rows = []
        for index, (name, customer, revenue, direct, allocated) in enumerate(
            portfolio_specs, 1
        ):
            reference = f"COST-PORTFOLIO-{name.upper()}"
            sold, sold_lines = order(
                f"{reference}-ORDER",
                "P05",
                counterparty=customer,
                quantity="10",
                price=str(Decimal(revenue) / Decimal(10)),
                gross=revenue,
                date=portfolio_time,
            )
            portfolio_issue = movement(
                f"{reference}-SHIPMENT",
                "P05",
                "10",
                "shipment",
                commitment=sold["commitment_id"],
                date=portfolio_time + timedelta(seconds=index),
            )
            portfolio_invoice_lines = [
                {
                    **sold_lines[0],
                    "billed_document_line_id": sold["line_id"],
                    "reality_finance_v1": {"net": revenue, "tax": "0"},
                }
            ]
            portfolio_invoice_source = source(
                "sales_invoice",
                f"{reference}-INVOICE",
                {
                    "number": demo_invoice_number(portfolio_time, reference),
                    "date": portfolio_time.isoformat(),
                    "currency": "EUR",
                    "gross_amount": revenue,
                    "amount_basis": "net",
                    "tax_amount": "0",
                    "lines": portfolio_invoice_lines,
                },
            )
            portfolio_invoice, portfolio_billed = create_document_with_lines(
                session,
                tenant,
                "sales_invoice",
                demo_invoice_number(portfolio_time, reference),
                parties[customer],
                portfolio_invoice_lines,
                revenue,
                document_date=portfolio_time.date().isoformat(),
                source_record_id=portfolio_invoice_source.id,
                _commit=False,
            )
            core.post_sales_invoice(
                session,
                tenant,
                portfolio_invoice.id,
                effective_at=portfolio_issue.occurred_at,
                _commit=False,
            )
            portfolio_rows.append(
                {
                    "name": name.replace("-", "_"),
                    "reference": reference,
                    "revenue": revenue,
                    "direct": direct,
                    "allocated": allocated,
                    "issue": portfolio_issue,
                    "invoice": portfolio_invoice,
                    "invoice_line": portfolio_billed[0],
                }
            )

        portfolio_movement_ids = {
            portfolio_opening.id,
            *(row["issue"].id for row in portfolio_rows),
        }
        prior_p05 = list(
            session.scalars(
                select(Movement).where(
                    Movement.tenant_id == tenant,
                    Movement.item_id == items["P05"],
                    Movement.id.not_in(portfolio_movement_ids),
                    Movement.occurred_at <= late_cleanup.occurred_at,
                )
            )
        )
        portfolio_ownership = [
            {
                "movement_id": row.id,
                "owner_party_id": parties["S1"],
                "evidence_source_record_id": row.source_record_id,
                "quantity": str(row.quantity),
            }
            for row in prior_p05
        ] + [
            {
                "movement_id": portfolio_opening.id,
                "owner_party_id": parties["company"],
                "evidence_source_record_id": portfolio_acquisition_source.id,
                "quantity": "50",
            },
            *(
                {
                    "movement_id": row["issue"].id,
                    "owner_party_id": parties["company"],
                    "evidence_source_record_id": portfolio_acquisition_source.id,
                    "quantity": "10",
                }
                for row in portfolio_rows
            ),
        ]
        portfolio_inventory_arguments = {
            "operation": "inventory_review",
            "expected_event_sequence": _sequence(session, tenant),
            "item_id": items["P05"],
            "owner_party_id": parties["company"],
            "method": "fifo",
            "currency": "EUR",
            "base_unit": "pcs",
            "history_start": (portfolio_time - timedelta(seconds=1)).isoformat(),
            "effective_at": late_cleanup.occurred_at.isoformat(),
            "history_complete_from_zero": True,
            "receipt_cost_scopes_confirmed": True,
            "economic_issue_ids": [row["issue"].id for row in portfolio_rows],
            "openings": [
                {
                    "movement_id": portfolio_opening.id,
                    "evidence_source_record_id": portfolio_acquisition_source.id,
                    "acquisition_cost": "500",
                }
            ],
            "ownership_parts": portfolio_ownership,
            "reason": "Canonical contribution portfolio acquisition review",
        }
        portfolio_inventory = _cost_action(session, run, portfolio_inventory_arguments)
        portfolio_opening_basis = session.scalar(
            select(CostMovementBasis).where(
                CostMovementBasis.tenant_id == tenant,
                CostMovementBasis.movement_id == portfolio_opening.id,
            )
        )
        for row in portfolio_rows:
            row["issue_basis"] = session.scalar(
                select(CostMovementBasis).where(
                    CostMovementBasis.tenant_id == tenant,
                    CostMovementBasis.movement_id == row["issue"].id,
                )
            )
            row["inventory_member"] = session.scalar(
                select(CostInventoryMember).where(
                    CostInventoryMember.tenant_id == tenant,
                    CostInventoryMember.review_id == portfolio_inventory["review_id"],
                    CostInventoryMember.movement_basis_id == row["issue_basis"].id,
                )
            )
            portfolio_received = components._received(
                session, tenant, row["invoice"], row["invoice_line"]
            )
            row["commercial"] = _cost_action(
                session,
                run,
                {
                    "operation": "commercial_match_review",
                    "expected_event_sequence": _sequence(session, tenant),
                    "document_line_id": row["invoice_line"].id,
                    "expected_evidence_hash": portfolio_received["evidence_hash"],
                    "profile": "commercial_v1",
                    "profile_confirmed": True,
                    "goods_cost_disposition": "inventory",
                    "inventory_parts": [
                        {
                            "inventory_member_id": row["inventory_member"].id,
                            "entry_movement_basis_id": portfolio_opening_basis.id,
                            "receipt_movement_basis_id": portfolio_opening_basis.id,
                            "quantity": "10",
                        }
                    ],
                    "reason": f"Canonical {row['reference']} commercial match",
                },
            )

        portfolio_selling_lines = []
        for row in portfolio_rows:
            selling_total = Decimal(row["direct"]) + Decimal(row["allocated"])
            if not selling_total:
                continue
            portfolio_selling_lines.append(
                {
                    "item_id": None,
                    "quantity": "1",
                    "unit": "service",
                    "unit_price": str(selling_total),
                    "gross_amount": str(selling_total),
                    "source_line_id": f"{row['reference']}-SELLING-1",
                    "description": f"Authored selling costs for {row['reference']}",
                    "reality_finance_v1": {"net": str(selling_total), "tax": "0"},
                }
            )
        portfolio_selling_total = sum(
            (Decimal(line["gross_amount"]) for line in portfolio_selling_lines),
            Decimal(0),
        )
        portfolio_selling_source = source(
            "supplier_invoice",
            "COST-PORTFOLIO-SELLING",
            {
                "number": "SINV-011",
                "date": portfolio_time.isoformat(),
                "gross_amount": str(portfolio_selling_total),
                "currency": "EUR",
                "lines": portfolio_selling_lines,
            },
        )
        portfolio_selling_document, portfolio_selling_document_lines = (
            create_document_with_lines(
                session,
                tenant,
                "supplier_invoice",
                "SINV-011",
                parties["S1"],
                portfolio_selling_lines,
                str(portfolio_selling_total),
                document_date=portfolio_time.date().isoformat(),
                source_record_id=portfolio_selling_source.id,
                _commit=False,
            )
        )
        core.post_supplier_invoice(
            session,
            tenant,
            portfolio_selling_document.id,
            effective_at=portfolio_time,
            _commit=False,
        )
        evidenced_index = 0
        for row in portfolio_rows:
            evidenced_categories = set()
            parts = []
            if Decimal(row["direct"]) or Decimal(row["allocated"]):
                selling_line = portfolio_selling_document_lines[evidenced_index]
                evidenced_index += 1
                selling_evidence = components._received(
                    session, tenant, portfolio_selling_document, selling_line
                )
                if Decimal(row["direct"]):
                    evidenced_categories.add("outbound_freight")
                    parts.append(
                        {
                            "document_line_id": row["invoice_line"].id,
                            "category": "outbound_freight",
                            "source_share": row["direct"],
                            "cost_effect": 1,
                            "assignment_kind": "direct",
                        }
                    )
                if Decimal(row["allocated"]):
                    evidenced_categories.add("payment_fee")
                    parts.append(
                        {
                            "document_line_id": row["invoice_line"].id,
                            "category": "payment_fee",
                            "source_share": row["allocated"],
                            "cost_effect": 1,
                            "assignment_kind": "allocated",
                        }
                    )
                _cost_action(
                    session,
                    run,
                    {
                        "operation": "selling_assign",
                        "expected_event_sequence": _sequence(session, tenant),
                        "reason": f"Canonical {row['reference']} selling costs",
                        "document_id": portfolio_selling_document.id,
                        "document_line_id": selling_line.id,
                        "expected_evidence_hash": selling_evidence["evidence_hash"],
                        "tax_treatment": "not_applicable",
                        "selling_expense_confirmed": True,
                        "parts": parts,
                    },
                )
            row["evidenced_categories"] = evidenced_categories

        final_inventory_batch = _cost_action(
            session,
            run,
            {
                "operation": "inventory_batch_review",
                "expected_event_sequence": _sequence(session, tenant),
                "reason": "Canonical contribution portfolio final joint inventory review",
                "scopes": [
                    {
                        key: value
                        for key, value in arguments.items()
                        if key not in {"operation", "expected_event_sequence", "reason"}
                    }
                    for arguments in (
                        fixture_refreshed_arguments,
                        portfolio_inventory_arguments,
                    )
                ],
            },
        )
        final_inventory_by_item = {
            result["item_id"]: result for result in final_inventory_batch["reviews"]
        }
        portfolio_positions = []
        for row in portfolio_rows:
            candidate = contribution_preview(session, tenant, row["invoice_line"].id)
            portfolio_positions.append(
                {
                    "document_line_id": row["invoice_line"].id,
                    "expected_candidate_hash": candidate["candidate_hash"],
                    "profile": "commercial_v1",
                    "profile_confirmed": True,
                    "revenue_complete": True,
                    "economic_at": candidate["trace"]["proposed_economic_at"],
                    "selling_categories": [
                        {
                            "category": category,
                            "disposition": (
                                "evidenced"
                                if category in row["evidenced_categories"]
                                else "confirmed_zero"
                            ),
                            "reason": f"Canonical {row['reference']} reviewed selling scope",
                        }
                        for category in (
                            "outbound_freight",
                            "fulfilment",
                            "packaging",
                            "payment_fee",
                            "marketplace_commission",
                            "sales_commission",
                            "other_selling",
                        )
                    ],
                }
            )
        fixture_candidate = contribution_preview(session, tenant, billed_lines[0].id)
        portfolio_positions.insert(
            0,
            {
                "document_line_id": billed_lines[0].id,
                "expected_candidate_hash": fixture_candidate["candidate_hash"],
                "profile": "commercial_v1",
                "profile_confirmed": True,
                "revenue_complete": True,
                "economic_at": fixture_candidate["trace"]["proposed_economic_at"],
                "selling_categories": [
                    {
                        "category": category,
                        "disposition": (
                            "evidenced"
                            if category in evidenced_selling
                            else "confirmed_zero"
                        ),
                        "reason": "Canonical fixture A reviewed selling scope",
                    }
                    for category in (
                        "outbound_freight",
                        "fulfilment",
                        "packaging",
                        "payment_fee",
                        "marketplace_commission",
                        "sales_commission",
                        "other_selling",
                    )
                ],
            },
        )
        portfolio_contributions = _cost_action(
            session,
            run,
            {
                "operation": "contribution_batch_review",
                "expected_event_sequence": _sequence(session, tenant),
                "reason": "Canonical contribution portfolio complete DB2 review",
                "positions": portfolio_positions,
            },
        )
        from reality.services.costing import build_contribution_generation

        build_contribution_generation(
            session,
            tenant,
            portfolio_contributions["action_id"],
        )
        contributions_by_line = {
            result["document_line_id"]: result
            for result in portfolio_contributions["reviews"]
        }
        for row in portfolio_rows:
            row["contribution"] = contributions_by_line[row["invoice_line"].id]
        contribution = contributions_by_line[billed_lines[0].id]

        costing_cases = {
            "fixture_a": {
                "reference": "COST-A-INVOICE",
                "item_id": items["P03"],
                "invoice_line_id": billed_lines[0].id,
                "inventory_review_id": inventory["review_id"],
                "match_revision_id": commercial["match_revision_id"],
                "contribution_review_id": contribution["review_id"],
                "final_inventory_review_id": final_inventory_by_item[items["P03"]][
                    "review_id"
                ],
            },
            "late_cost_return": {
                "credit_line_id": credit_billed[0].id,
                "inventory_review_id": late_inventory["review_id"],
                "return_match_revision_id": return_match["match_revision_id"],
                "initial_state": "cost_incomplete",
                "current_state": "late_cost_return_reviewed",
            },
            **{
                f"portfolio_{row['name']}": {
                    "reference": f"{row['reference']}-INVOICE",
                    "item_id": items["P05"],
                    "invoice_line_id": row["invoice_line"].id,
                    "inventory_review_id": final_inventory_by_item[items["P05"]][
                        "review_id"
                    ],
                    "match_revision_id": row["commercial"]["match_revision_id"],
                    "contribution_review_id": row["contribution"]["review_id"],
                }
                for row in portfolio_rows
            },
        }

        # Feature 246: fully supported edge cases use the same document, ledger and
        # inventory services as ordinary operation. Human references continue the
        # canonical sequences; opaque IDs remain the actual identity.
        def billed_sale(
            case_key: str,
            item_key: str,
            customer_key: str,
            quantity: str,
            gross: str,
            invoice_parts: tuple[tuple[str, str], ...],
            *,
            days_before: int = 8,
        ) -> tuple[dict, list]:
            ref, lines = order(
                case_key,
                item_key,
                counterparty=customer_key,
                quantity=quantity,
                price="10",
                gross=gross,
                date=anchor - timedelta(days=days_before),
            )
            invoices = []
            for part_index, (part_quantity, part_gross) in enumerate(invoice_parts, 1):
                invoice_date = anchor - timedelta(days=days_before - 1 - part_index)
                invoice_number = demo_invoice_number(
                    invoice_date, f"seed:{case_key}:{part_index}"
                )
                invoice_lines = [
                    {
                        **lines[0],
                        "quantity": part_quantity,
                        "gross_amount": part_gross,
                        "billed_document_line_id": ref["line_id"],
                        "reality_finance_v1": {"net": part_gross, "tax": "0"},
                    }
                ]
                invoice_source = source(
                    "sales_invoice",
                    f"{case_key}-INV-{part_index}",
                    {
                        "number": invoice_number,
                        "date": invoice_date.isoformat(),
                        "lines": invoice_lines,
                        "currency": "EUR",
                        "gross_amount": part_gross,
                    },
                )
                invoice, invoice_lines_created = create_document_with_lines(
                    session,
                    tenant,
                    "sales_invoice",
                    invoice_number,
                    parties[customer_key],
                    invoice_lines,
                    part_gross,
                    document_date=invoice_date.date().isoformat(),
                    source_record_id=invoice_source.id,
                    _commit=False,
                )
                core.post_sales_invoice(
                    session,
                    tenant,
                    invoice.id,
                    effective_at=invoice_date,
                    _commit=False,
                )
                invoices.append((invoice, invoice_lines_created[0]))
            return ref, invoices

        price_ref, price_invoices = billed_sale(
            "PRICE-CREDIT", "P04", "C4", "5", "50", (("5", "50"),)
        )
        price_credit_date = anchor - timedelta(days=4)
        price_credit_number = "CN-003"
        price_credit_lines = [
            {
                "item_id": items["P04"],
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "5",
                "gross_amount": "5",
                "source_line_id": "PRICE-CREDIT-1",
                "billed_document_line_id": None,
                "description": "Price-only allowance; no goods returned",
                "reality_finance_v1": {"net": "5", "tax": "0"},
            }
        ]
        price_credit_source = source(
            "credit_note",
            price_credit_number,
            {
                "number": price_credit_number,
                "date": price_credit_date.isoformat(),
                "gross_amount": "5",
                "currency": "EUR",
                "lines": price_credit_lines,
            },
        )
        price_credit, _ = create_document_with_lines(
            session,
            tenant,
            "credit_note",
            price_credit_number,
            parties["C4"],
            price_credit_lines,
            "5",
            document_date=price_credit_date.date().isoformat(),
            source_record_id=price_credit_source.id,
            _commit=False,
        )
        core.post_sales_credit_note(
            session,
            tenant,
            price_credit.id,
            effective_at=price_credit_date,
            _commit=False,
        )
        core.allocate_credit_note(
            session,
            tenant,
            price_credit.id,
            price_invoices[0][0].id,
            "5",
            _commit=False,
        )
        cases["price_only_credit"] = {
            **price_ref,
            "invoice_id": price_invoices[0][0].id,
            "credit_id": price_credit.id,
            "credit_number": price_credit_number,
        }

        reversal_ref, reversal_invoices = billed_sale(
            "INVOICE-REVERSAL", "P05", "C5", "2", "20", (("2", "20"),)
        )
        reversal_invoice = reversal_invoices[0][0]
        reversal_group = core._settlement_control_entry(
            session, tenant, reversal_invoice.id
        ).posting_group_id
        reversal_reason = "Customer invoice cancelled before settlement"
        reversal_preview = core.preview_ledger_reversal(
            session, tenant, reversal_group, reason=reversal_reason
        )
        reversal = core.reverse_ledger_posting_group(
            session,
            tenant,
            reversal_group,
            reason=reversal_reason,
            actor_context={"source": "canonical_demo_profile"},
            expected_revision=reversal_preview["revision"],
            preview_fingerprint=reversal_preview["request_fingerprint"],
            _commit=False,
        )
        cases["invoice_reversal"] = {
            **reversal_ref,
            "invoice_id": reversal_invoice.id,
            "invoice_number": reversal_invoice.number,
            "reversal_id": reversal.reversal_id,
            "original_posting_group_id": reversal.original_posting_group_id,
            "reversing_posting_group_id": reversal.reversing_posting_group_id,
        }

        split_ref, split_invoices = billed_sale(
            "SPLIT-INVOICE", "P06", "C6", "10", "100", (("4", "40"), ("6", "60"))
        )
        cases["split_invoices"] = {
            **split_ref,
            "invoice_1_id": split_invoices[0][0].id,
            "invoice_1_number": split_invoices[0][0].number,
            "invoice_1_line_id": split_invoices[0][1].id,
            "invoice_2_id": split_invoices[1][0].id,
            "invoice_2_number": split_invoices[1][0].number,
            "invoice_2_line_id": split_invoices[1][1].id,
        }

        lot_source = source(
            "lot_label",
            "LOT-2026-001",
            {
                "item_key": "P17",
                "lot_number": "LOT-2026-001",
                "expires_at": (anchor.date() - timedelta(days=1)).isoformat(),
            },
        )
        lot = core.create_lot(
            session,
            tenant,
            items["P17"],
            "LOT-2026-001",
            expires_at=anchor.date() - timedelta(days=1),
            source_record_id=lot_source.id,
            _commit=False,
        )
        lot_receipt_source = source(
            "movement",
            "LOT-RECEIPT-001",
            {"type": "receipt", "quantity": "10", "lot_number": lot.lot_number},
        )
        lot_receipt = core.record_movement(
            session,
            tenant,
            "receipt",
            items["P17"],
            "10",
            to_location_id=locations["A"],
            lot_id=lot.id,
            source_record_id=lot_receipt_source.id,
            occurred_at=anchor - timedelta(days=3),
            _commit=False,
        )
        transfer_source = source(
            "movement",
            "TRANSFER-001",
            {
                "type": "transfer",
                "quantity": "3",
                "from": "A",
                "to": "B",
                "lot_number": lot.lot_number,
            },
        )
        transfer = core.record_movement(
            session,
            tenant,
            "transfer",
            items["P17"],
            "3",
            from_location_id=locations["A"],
            to_location_id=locations["B"],
            lot_id=lot.id,
            source_record_id=transfer_source.id,
            occurred_at=anchor - timedelta(days=2),
            _commit=False,
        )
        cases["lot_expiry_transfer"] = {
            "item_id": items["P17"],
            "lot_id": lot.id,
            "receipt_movement_id": lot_receipt.id,
            "transfer_movement_id": transfer.id,
        }

        serial_source = source(
            "serial_label", "SER-0001", {"item_key": "P18", "serial_number": "SER-0001"}
        )
        serial = core.create_serial_unit(
            session,
            tenant,
            items["P18"],
            "SER-0001",
            source_record_id=serial_source.id,
            _commit=False,
        )
        serial_receipt_source = source(
            "movement",
            "SERIAL-RECEIPT-001",
            {"type": "receipt", "quantity": "1", "serial_number": serial.serial_number},
        )
        serial_receipt = core.record_movement(
            session,
            tenant,
            "receipt",
            items["P18"],
            "1",
            to_location_id=locations["A"],
            serial_unit_id=serial.id,
            source_record_id=serial_receipt_source.id,
            occurred_at=anchor - timedelta(days=2),
            _commit=False,
        )
        cases["serial_tracking"] = {
            "item_id": items["P18"],
            "serial_unit_id": serial.id,
            "receipt_movement_id": serial_receipt.id,
        }

        adjustment_opening = movement(
            "ADJUSTMENT-OPENING",
            "P10",
            "6",
            "opening_stock",
            date=anchor - timedelta(days=4),
        )
        adjustment_ids = {}
        for index, reason in enumerate(("damage", "loss", "scrap"), 1):
            adjustment_source = source(
                "movement",
                f"ADJUSTMENT-{index:03}",
                {"type": "adjustment", "quantity": "1", "reason": reason},
            )
            adjusted = core.record_movement(
                session,
                tenant,
                "adjustment",
                items["P10"],
                "1",
                from_location_id=locations["A"],
                reason=reason,
                source_record_id=adjustment_source.id,
                occurred_at=anchor - timedelta(days=3 - index),
                _commit=False,
            )
            adjustment_ids[reason] = adjusted.id
        cases["stock_adjustments"] = {
            "item_id": items["P10"],
            "opening_movement_id": adjustment_opening.id,
            "damage_movement_id": adjustment_ids["damage"],
            "loss_movement_id": adjustment_ids["loss"],
            "scrap_movement_id": adjustment_ids["scrap"],
        }

        exchange_original, _ = order(
            "EXCHANGE-ORIGINAL",
            "P07",
            counterparty="C7",
            quantity="1",
            price="20",
            gross="20",
            date=anchor - timedelta(days=8),
        )
        movement(
            "EXCHANGE-OPENING",
            "P07",
            "1",
            "opening_stock",
            date=anchor - timedelta(days=7),
        )
        original_shipment = movement(
            "EXCHANGE-SHIPMENT",
            "P07",
            "1",
            "shipment",
            commitment=exchange_original["commitment_id"],
            date=anchor - timedelta(days=6),
        )
        customer_return = movement(
            "EXCHANGE-RETURN",
            "P07",
            "1",
            "return",
            date=anchor - timedelta(days=5),
        )
        exchange_replacement, _ = order(
            "EXCHANGE-REPLACEMENT",
            "P07",
            counterparty="C7",
            quantity="1",
            price="0",
            gross="0",
            date=anchor - timedelta(days=4),
        )
        replacement_shipment = movement(
            "EXCHANGE-REPLACEMENT-SHIPMENT",
            "P07",
            "1",
            "shipment",
            commitment=exchange_replacement["commitment_id"],
            date=anchor - timedelta(days=3),
        )
        cases["exchange_replacement"] = {
            "original_order_id": exchange_original["document_id"],
            "original_order_number": exchange_original["number"],
            "original_shipment_id": original_shipment.id,
            "return_movement_id": customer_return.id,
            "replacement_order_id": exchange_replacement["document_id"],
            "replacement_order_number": exchange_replacement["number"],
            "replacement_shipment_id": replacement_shipment.id,
        }

        prepayment_ref, prepayment_invoices = billed_sale(
            "CUSTOMER-PREPAYMENT", "P08", "C8", "2", "40", (("2", "40"),)
        )
        prepayment_invoice = prepayment_invoices[0][0]
        payment_effective_at = anchor - timedelta(days=4)
        prepayment_source = source(
            "customer_payment",
            "CPAY-010",
            {
                "number": "CPAY-010",
                "date": payment_effective_at.isoformat(),
                "amount": "40",
                "currency": "EUR",
                "invoice_external_reference": prepayment_invoice.number,
            },
        )
        core.post_customer_payment(
            session,
            tenant,
            prepayment_invoice.id,
            "40",
            payment_number="CPAY-010",
            source_record_id=prepayment_source.id,
            effective_at=payment_effective_at,
            _commit=False,
        )
        movement(
            "PREPAYMENT-OPENING",
            "P08",
            "2",
            "opening_stock",
            date=anchor - timedelta(days=2),
        )
        prepayment_shipment = movement(
            "PREPAYMENT-SHIPMENT",
            "P08",
            "2",
            "shipment",
            commitment=prepayment_ref["commitment_id"],
            date=anchor - timedelta(days=1),
        )
        cases["customer_prepayment"] = {
            "order_id": prepayment_ref["document_id"],
            "order_number": prepayment_ref["number"],
            "invoice_id": prepayment_invoice.id,
            "invoice_number": prepayment_invoice.number,
            "payment_number": "CPAY-010",
            "payment_effective_at": payment_effective_at.isoformat(),
            "shipment_movement_id": prepayment_shipment.id,
        }

        # Feature 247: the four commercial edge workflows are ordinary confirmed
        # product actions with exact references, not profile-only records.
        dunning_ref, dunning_invoices = billed_sale(
            "DUNNING", "P09", "C9", "2", "100", (("2", "100"),), days_before=30
        )
        dunning_invoice = dunning_invoices[0][0]
        dunning = _finance_action(
            session,
            run,
            "finance.dunning.record",
            {
                "expected_revision": list_accounts(session, tenant)["revision"],
                "invoice_ids": [dunning_invoice.id],
                "level": 2,
                "notice_date": anchor.date().isoformat(),
                "fee_amount": "5",
                "reason": "Second reminder in the canonical demo",
                "number": "DN-2026-0001",
            },
        )
        cases["dunning_with_fee"] = {
            "order_id": dunning_ref["document_id"],
            "order_number": dunning_ref["number"],
            "invoice_id": dunning_invoice.id,
            "invoice_number": dunning_invoice.number,
            "notice_id": dunning["id"],
            "notice_number": dunning["number"],
            "fee_document_id": dunning["fee_document_id"],
            "fee_amount": "5",
        }

        bad_debt_ref, bad_debt_invoices = billed_sale(
            "BAD-DEBT", "P10", "C10", "2", "100", (("2", "100"),)
        )
        bad_debt_invoice = bad_debt_invoices[0][0]
        core.post_customer_payment(
            session,
            tenant,
            bad_debt_invoice.id,
            "60",
            payment_number="CPAY-013",
            effective_at=anchor - timedelta(days=2),
            _commit=False,
        )
        bad_debt = _settlement_adjustment(
            session,
            run,
            bad_debt_invoice.id,
            "25",
            reason_category="bad_debt",
            reason="Confirmed irrecoverable customer balance",
        )
        cases["customer_bad_debt"] = {
            "order_id": bad_debt_ref["document_id"],
            "order_number": bad_debt_ref["number"],
            "invoice_id": bad_debt_invoice.id,
            "invoice_number": bad_debt_invoice.number,
            "payment_number": "CPAY-013",
            "adjustment_document_id": bad_debt["document_id"],
            "written_off": "25",
            "remaining": "15",
        }

        customer_deposit = _finance_action(
            session,
            run,
            "finance.deposit.record",
            {
                "expected_revision": list_accounts(session, tenant)["revision"],
                "side": "customer",
                "party_id": parties["C11"],
                "amount": "100",
                "currency": "EUR",
                "reference": "CDEP-001",
                "effective_at": (anchor - timedelta(days=12)).isoformat(),
            },
        )
        customer_final_ref, customer_final_invoices = billed_sale(
            "CUSTOMER-DEPOSIT-FINAL", "P11", "C11", "4", "80", (("4", "80"),)
        )
        customer_final = customer_final_invoices[0][0]
        customer_clearing = _finance_action(
            session,
            run,
            "finance.deposit.clear",
            {
                "expected_revision": list_accounts(session, tenant)["revision"],
                "deposit_document_id": customer_deposit["document_id"],
                "invoice_id": customer_final.id,
                "amount": "80",
            },
        )
        cases["customer_deposit_clearing"] = {
            "order_number": customer_final_ref["number"],
            "deposit_number": customer_deposit["number"],
            "invoice_id": customer_final.id,
            "invoice_number": customer_final.number,
            "allocation_id": customer_clearing["allocation_id"],
            "remaining_credit": "20",
        }

        supplier_deposit = _finance_action(
            session,
            run,
            "finance.deposit.record",
            {
                "expected_revision": list_accounts(session, tenant)["revision"],
                "side": "supplier",
                "party_id": parties["S1"],
                "amount": "120",
                "currency": "EUR",
                "reference": "SDEP-001",
                "effective_at": (anchor - timedelta(days=12)).isoformat(),
            },
        )
        supplier_final_source = source(
            "supplier_invoice",
            "SINV-DEPOSIT-FINAL",
            {"number": "SINV-010", "date": (anchor - timedelta(days=6)).isoformat()},
        )
        supplier_final, _ = create_document_with_lines(
            session,
            tenant,
            "supplier_invoice",
            "SINV-010",
            parties["S1"],
            [
                {
                    "item_id": items["P01"],
                    "quantity": "5",
                    "unit_price": "20",
                    "gross_amount": "100",
                    "source_line_id": "SINV-DEPOSIT-FINAL-1",
                }
            ],
            "100",
            document_date=(anchor - timedelta(days=6)).date().isoformat(),
            source_record_id=supplier_final_source.id,
            _commit=False,
        )
        core.post_supplier_invoice(session, tenant, supplier_final.id, _commit=False)
        supplier_clearing = _finance_action(
            session,
            run,
            "finance.deposit.clear",
            {
                "expected_revision": list_accounts(session, tenant)["revision"],
                "deposit_document_id": supplier_deposit["document_id"],
                "invoice_id": supplier_final.id,
                "amount": "100",
            },
        )
        cases["supplier_deposit_clearing"] = {
            "deposit_number": supplier_deposit["number"],
            "invoice_number": supplier_final.number,
            "allocation_id": supplier_clearing["allocation_id"],
            "remaining_credit": "20",
        }

        overdelivery_ref, _ = order(
            "CONTROLLED-OVERDELIVERY",
            "P12",
            counterparty="C12",
            quantity="10",
            gross="100",
            date=anchor - timedelta(days=5),
        )
        overdelivery_revision = core.revise_commitment(
            session,
            tenant,
            overdelivery_ref["commitment_id"],
            quantity="12",
            note="Customer confirmed two additional pieces",
            stated_at=anchor - timedelta(days=4),
            _commit=False,
        )
        movement(
            "CONTROLLED-OVERDELIVERY-OPENING",
            "P12",
            "12",
            "opening_stock",
            date=anchor - timedelta(days=3),
        )
        overdelivery_movement = movement(
            "CONTROLLED-OVERDELIVERY-SHIPMENT",
            "P12",
            "12",
            "shipment",
            commitment=overdelivery_ref["commitment_id"],
            date=anchor - timedelta(days=2),
        )
        cases["controlled_overdelivery"] = {
            "order_number": overdelivery_ref["number"],
            "original_quantity": "10",
            "quantity_in_force": "12",
            "revision_id": overdelivery_revision.id,
            "shipment_movement_id": overdelivery_movement.id,
        }

        # Spec 248: one compact, exact supply chain demonstrates that commercial
        # intent (customer demand versus stock) remains independent from receipt.
        from reality.services.supply_assignments import assign_supply

        supply_demand, _ = order(
            "B2B-SUPPLY-DEMAND",
            "P11",
            counterparty="C1",
            quantity="6",
            price="24",
            gross="144",
            date=anchor - timedelta(days=3),
            due=anchor + timedelta(days=4),
        )
        supply_order, _ = order(
            "PO-010",
            "P11",
            counterparty="S3",
            quantity="10",
            price="12",
            gross="120",
            date=anchor - timedelta(days=2),
            due=anchor + timedelta(days=3),
            purchase=True,
        )
        customer_assignment = assign_supply(
            session,
            tenant,
            supply_order["commitment_id"],
            "6",
            purpose="customer_demand",
            customer_commitment_id=supply_demand["commitment_id"],
            request_id="DEMO-SUPPLY-CUSTOMER-001",
            _commit=False,
        )
        stock_assignment = assign_supply(
            session,
            tenant,
            supply_order["commitment_id"],
            "2",
            purpose="stock_replenishment",
            request_id="DEMO-SUPPLY-STOCK-001",
            _commit=False,
        )
        supply_receipt = movement(
            "purchase-receipt-S10-partial",
            "P11",
            "4",
            commitment=supply_order["commitment_id"],
            date=anchor - timedelta(days=1),
        )
        cases["b2b_supply_chain"] = {
            "sales_order_number": supply_demand["number"],
            "sales_commitment_id": supply_demand["commitment_id"],
            "purchase_order_number": supply_order["number"],
            "purchase_commitment_id": supply_order["commitment_id"],
            "customer_assignment_id": customer_assignment.id,
            "stock_assignment_id": stock_assignment.id,
            "receipt_movement_id": supply_receipt.id,
            "ordered": "10",
            "customer_assigned": "6",
            "stock_replenishment": "2",
            "unassigned": "2",
            "received": "4",
            "sales_ui_path": f"Sales → Orders → {supply_demand['number']}",
            "purchasing_ui_path": (
                f"Purchasing → Orders → {supply_order['number']}"
            ),
            "warehouse_ui_path": "Warehouse → Items → ITEM-011",
        }

        # The five returned units are deliberately resolved through every
        # supported physical outcome. Credit remains a separate commercial fact.
        from reality.services.return_dispositions import record_return_disposition

        return_sale, _ = order(
            "B2B-RETURN-SALE",
            "P12",
            counterparty="C2",
            quantity="5",
            price="25",
            gross="125",
            date=anchor - timedelta(days=8),
        )
        movement(
            "B2B-RETURN-OPENING",
            "P12",
            "5",
            "opening_stock",
            date=anchor - timedelta(days=7),
        )
        movement(
            "B2B-RETURN-SHIPMENT",
            "P12",
            "5",
            "shipment",
            commitment=return_sale["commitment_id"],
            date=anchor - timedelta(days=6),
        )
        arrived_return = movement(
            "B2B-RETURN-ARRIVAL",
            "P12",
            "5",
            "return",
            location="B",
            commitment=return_sale["commitment_id"],
            date=anchor - timedelta(days=4),
        )
        dispositions = [
            record_return_disposition(
                session,
                tenant,
                arrived_return.id,
                "restock",
                "2",
                destination_location_id=locations["A"],
                _commit=False,
            ),
            record_return_disposition(
                session,
                tenant,
                arrived_return.id,
                "quarantine_repair",
                "1",
                destination_location_id=locations["B"],
                _commit=False,
            ),
            record_return_disposition(
                session,
                tenant,
                arrived_return.id,
                "scrap_loss",
                "1",
                reason="Damaged beyond repair",
                _commit=False,
            ),
            record_return_disposition(
                session,
                tenant,
                arrived_return.id,
                "return_to_supplier",
                "1",
                reason="Supplier quality claim",
                _commit=False,
            ),
        ]
        cases["b2b_return_disposition"] = {
            "sales_order_number": return_sale["number"],
            "commitment_id": return_sale["commitment_id"],
            "return_movement_id": arrived_return.id,
            "restock_movement_id": dispositions[0].id,
            "quarantine_movement_id": dispositions[1].id,
            "scrap_movement_id": dispositions[2].id,
            "supplier_return_movement_id": dispositions[3].id,
            "arrived": "5",
            "restocked": "2",
            "quarantined": "1",
            "scrapped": "1",
            "returned_to_supplier": "1",
            "unresolved": "0",
            "sales_ui_path": f"Sales → Orders → {return_sale['number']}",
            "warehouse_ui_path": "Warehouse → Items → ITEM-012 → Movements",
        }

    session.flush()
    manifest = {
        "parties": parties,
        "items": items,
        "locations": locations,
        "cases": cases,
        "windows": {
            "prior_start": (anchor - timedelta(days=84)).isoformat(),
            "current_start": (anchor - timedelta(days=42)).isoformat(),
            "end": anchor.isoformat(),
        },
        "capabilities": {
            "operations": "available",
            "finance": "available" if not execution else "not_seeded",
            "metric": "Booked sales_revenue credits minus debits, grouped by currency and effective_at; gross amounts, not net revenue, profit or payment.",
            "cost_basis": "bounded_cases",
            "promotions": "missing",
            "crm": "another_source",
            "marketing": "another_source",
        },
        "costing_cases": {} if execution else costing_cases,
    }

    from reality.db.core import Item, Location, Party
    from reality.demo.profile_contract import ProfileManifest

    for model, expected in zip(
        (Party, Item, Location), (2, 2, 1) if execution else (24, 18, 2), strict=True
    ):
        if (
            session.scalar(
                select(func.count()).select_from(model).where(model.tenant_id == tenant)
            )
            != expected
        ):
            raise core.InvalidOperation("Profile contains unexpected records.")
    return ProfileManifest.model_validate(
        {**manifest, "execution": execution}
    ).model_dump()
