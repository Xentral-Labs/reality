"""Atomic synthetic evidence prepared through shared application services."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from reality.db.core import PlaygroundRun
from reality.demo.international import CUSTOMERS, HISTORY, ITEMS, LOCATIONS, SUPPLIERS
from reality.services import core


def seed_profile(
    session: Session, run: PlaygroundRun, anchor: datetime, *, execution: bool = False
) -> dict:
    tenant = run.tenant_id
    parties, items, locations, cases = {}, {}, {}, {}
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
            key,
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
            _commit=False,
        ).id

    def source(kind: str, key: str, payload: dict):
        return core.store_source_record(
            session,
            tenant,
            "demo_profile",
            kind,
            key,
            {"synthetic": True, "profile_version": 1, **payload},
        )[0]

    def order(
        key: str,
        item: str,
        *,
        quantity: str = "5",
        price: str = "10",
        gross: str = "50",
        currency: str = "EUR",
        date: datetime = anchor,
        due: datetime | None = None,
        purchase: bool = False,
    ):
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
            "number": key,
            "date": date.isoformat(),
            "due_at": due.isoformat() if due else None,
            "currency": currency,
            "lines": lines,
            "gross_amount": gross,
            "amount_basis": "gross",
            "tax_amount": "0",
            "discount_amount": "0",
            "sales_channel": "demo_wholesale",
            "external_customer_reference": "demo:C1",
        }
        src = source("purchase_order" if purchase else "sales_order", key, payload)
        party = parties["S1" if purchase else "C1"]
        doc, doc_lines = core.create_manual_document_with_lines(
            session,
            tenant,
            "purchase_order" if purchase else "sales_order",
            key,
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
            "from_location_id" if kind == "shipment" else "to_location_id": locations[
                location
            ]
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
                key, item, quantity="1", gross="10", due=anchor + timedelta(days=3)
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
                key, item, due=anchor + timedelta(days=-2 if index in {4, 5, 8} else 3)
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
        movement("wrong-location", "P08", "8", location="B")
        for index, item in enumerate(("P11", "P15", "P16"), 1):
            due = (
                anchor + timedelta(days=-3 if index == 1 else 5) if index != 3 else None
            )
            cases[f"S{index:02}"], _ = order(
                f"PO-{index:03}", item, purchase=True, due=due
            )
            if index == 1:
                movement(
                    "partial-purchase",
                    item,
                    "2",
                    commitment=cases["S01"]["commitment_id"],
                )
        history = list(HISTORY)
        history += [
            (f"week-{week:02}", "P14", 84 - week * 7, "1", "12", "12", "EUR")
            for week in range(12)
        ]
        for key, item, days, quantity, price, gross, currency in history:
            date = anchor - timedelta(days=days)
            ref, lines = order(
                f"H-{key}",
                item,
                quantity=quantity,
                price=price,
                gross=gross,
                currency=currency,
                date=date,
            )
            invoice_lines = [{**lines[0], "billed_document_line_id": ref["line_id"]}]
            src = source(
                "sales_invoice",
                f"INV-{key}",
                {
                    "date": date.isoformat(),
                    "lines": invoice_lines,
                    "currency": currency,
                    "gross_amount": gross,
                    "amount_basis": "gross",
                    "tax_amount": "0",
                    "discount_amount": "0",
                },
            )
            invoice, _ = core.create_manual_document_with_lines(
                session,
                tenant,
                "sales_invoice",
                f"INV-{key}",
                parties["C1"],
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
            movement(f"history-receipt-{key}", item, quantity, date=date)
            movement(
                f"history-shipment-{key}",
                item,
                quantity,
                "shipment",
                commitment=ref["commitment_id"],
                date=date,
            )
            if key == "credit-origin":
                credit_date = anchor - timedelta(days=10)
                credit_lines = [
                    {**invoice_lines[0], "quantity": "2", "gross_amount": "24"}
                ]
                credit_source = source(
                    "credit_note",
                    "CR-001",
                    {
                        "invoice_external_reference": f"INV-{key}",
                        "order_external_reference": f"H-{key}",
                        "lines": credit_lines,
                        "gross_amount": "24",
                        "currency": "EUR",
                        "amount_basis": "gross",
                        "tax_amount": "0",
                        "discount_amount": "0",
                        "date": credit_date.isoformat(),
                    },
                )
                credit, _ = core.create_manual_document_with_lines(
                    session,
                    tenant,
                    "credit_note",
                    "CR-001",
                    parties["C1"],
                    credit_lines,
                    "24",
                    document_date=credit_date.date().isoformat(),
                    source_record_id=credit_source.id,
                    _commit=False,
                )
                core.post_sales_credit_note(
                    session, tenant, credit.id, effective_at=credit_date, _commit=False
                )
                returned = movement(
                    "return-001",
                    item,
                    "2",
                    "return",
                    commitment=ref["commitment_id"],
                    date=credit_date,
                )
                cases["credit_return"] = {
                    **ref,
                    "invoice_id": invoice.id,
                    "credit_id": credit.id,
                    "return_movement_id": returned.id,
                }
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
            "cost_basis": "missing",
            "promotions": "missing",
            "crm": "another_source",
            "marketing": "another_source",
        },
    }

    from sqlalchemy import func, select

    from reality.db.core import Item, Location, Party
    from reality.demo.profile_contract import ProfileManifest

    for model, expected in zip(
        (Party, Item, Location), (2, 2, 1) if execution else (8, 16, 2), strict=True
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
