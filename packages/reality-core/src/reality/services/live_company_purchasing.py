"""Explicit synthetic supplier quotes, installed through ordinary master services."""

from decimal import Decimal

from sqlalchemy import select

from reality.db.core import (
    Item,
    PartyPriceList,
    PriceList,
    PriceListEntry,
    SupplierItemNumber,
    SupplierItemTerms,
)
from reality.services import core, live_company
from reality.services.supplier_item_numbers import set_supplier_item_number
from reality.services.supplier_item_terms import set_supplier_item_terms


def catalogue(session, tenant, config):
    result = []
    for supplier in config["references"]["supplier"]:
        items = []
        for reference in config["items"]:
            item = session.scalar(
                select(Item).where(Item.tenant_id == tenant, Item.id == reference["id"])
            )
            if item is None:
                continue
            terms = session.scalar(
                select(SupplierItemTerms).where(
                    SupplierItemTerms.tenant_id == tenant,
                    SupplierItemTerms.party_id == supplier["id"],
                    SupplierItemTerms.item_id == item.id,
                )
            )
            number = session.scalar(
                select(SupplierItemNumber).where(
                    SupplierItemNumber.tenant_id == tenant,
                    SupplierItemNumber.party_id == supplier["id"],
                    SupplierItemNumber.item_id == item.id,
                )
            )
            quantity = (
                max(Decimal(10), terms.minimum_quantity or Decimal(0))
                if terms
                else Decimal(10)
            )
            price = core.resolve_price(
                session,
                tenant,
                supplier["id"],
                item.id,
                quantity,
                "purchase",
                "EUR",
                item.unit,
            )
            items.append(
                {
                    "item_id": item.id,
                    "sku": item.sku,
                    "name": item.name,
                    "supplier_id": supplier["id"],
                    "unit": item.unit,
                    "supplier_item_number": number.supplier_item_number
                    if number
                    else None,
                    "minimum_quantity": str(terms.minimum_quantity)
                    if terms and terms.minimum_quantity is not None
                    else None,
                    "order_multiple": str(terms.order_multiple)
                    if terms and terms.order_multiple is not None
                    else None,
                    "unit_price": str(price.unit_price) if price else None,
                    "currency": "EUR",
                    "price_list_entry_id": price.price_list_entry_id if price else None,
                    "price_list_id": price.price_list_id if price else None,
                    "evaluated_quantity": str(quantity),
                }
            )
        quote_source = live_company._source(
            session,
            tenant,
            "company_simulator",
            "purchasing_profile",
            "v1:" + supplier["id"],
        )
        result.append(
            {
                "supplier_id": supplier["id"],
                "supplier_name": supplier["name"],
                "quote_source_record_id": quote_source.id if quote_source else None,
                "quote": live_company._json(quote_source) if quote_source else None,
                "items": items,
            }
        )
    return result


def prepare(session, tenant, actor, run_id, *, supplier_id=None, confirmed=False):
    if not confirmed:
        raise ValueError("Purchasing setup requires confirmation")
    live_company._owner(session, tenant, actor)
    _, config = live_company._run(session, tenant, run_id, lock=True)
    suppliers = config["references"]["supplier"]
    if supplier_id is None:
        if len(suppliers) != 1:
            raise ValueError(
                "Select an explicit supplier when the run has multiple suppliers"
            )
        supplier_id = suppliers[0]["id"]
    if supplier_id not in {s["id"] for s in suppliers}:
        raise core.NotFound("Run supplier not found")
    quotes = [
        {
            "item_id": i["id"],
            "unit_price": "5" if i["sku"] == "A" else "6",
            "currency": "EUR",
            "minimum_quantity": "10",
            "order_multiple": "5",
            "supplier_item_number": "SIM-" + i["sku"],
        }
        for i in config["items"]
    ]
    payload = {
        "supplier_id": supplier_id,
        "synthetic": True,
        "quotes": quotes,
        "price_basis": "stated fixture unit price; no tax calculation",
        "first_receipt_minutes": 5,
        "remaining_receipt_minutes": 10,
        "delivery_note": "Simulation reaction windows after an accepted purchase, not guaranteed delivery; selected delays add two minutes.",
    }
    source = live_company._store(
        session,
        tenant,
        "company_simulator",
        "purchasing_profile",
        "v1:" + supplier_id,
        payload,
    )
    session.commit()
    code = ("SIM-PURCHASE-" + supplier_id).upper()
    for quote in quotes:
        item = session.scalar(
            select(Item).where(Item.tenant_id == tenant, Item.id == quote["item_id"])
        )
        if item is None or not item.unit:
            raise ValueError("Purchasing requires an existing item with a unit")
        existing_terms = session.scalar(
            select(SupplierItemTerms).where(
                SupplierItemTerms.tenant_id == tenant,
                SupplierItemTerms.party_id == supplier_id,
                SupplierItemTerms.item_id == item.id,
            )
        )
        quantity = (
            max(Decimal(10), existing_terms.minimum_quantity or Decimal(0))
            if existing_terms
            else Decimal(10)
        )
        price = core.resolve_price(
            session,
            tenant,
            supplier_id,
            item.id,
            quantity,
            "purchase",
            "EUR",
            item.unit,
        )
        if price is None:
            price_list = session.scalar(
                select(PriceList).where(
                    PriceList.tenant_id == tenant, PriceList.code == code
                )
            )
            if price_list is None:
                price_list = core.create_price_list(
                    session,
                    tenant,
                    code,
                    "Synthetic supplier quotation",
                    "purchase",
                    "EUR",
                    source_system="company_simulator",
                    external_id="purchase-list:" + supplier_id,
                    source_payload=payload,
                )
                core.assign_party_price_list(
                    session, tenant, supplier_id, price_list.id, priority=1000
                )
            if not price_list.is_active:
                raise ValueError(
                    "Synthetic purchase list is inactive; inspect the recorded agreement"
                )
            if not session.scalar(
                select(PartyPriceList.id).where(
                    PartyPriceList.tenant_id == tenant,
                    PartyPriceList.party_id == supplier_id,
                    PartyPriceList.price_list_id == price_list.id,
                )
            ):
                core.assign_party_price_list(
                    session, tenant, supplier_id, price_list.id, priority=1000
                )
            if session.scalar(
                select(PriceListEntry.id).where(
                    PriceListEntry.tenant_id == tenant,
                    PriceListEntry.price_list_id == price_list.id,
                    PriceListEntry.item_id == item.id,
                    PriceListEntry.min_quantity == 10,
                )
            ):
                raise ValueError(
                    "Existing synthetic price is not currently resolvable; inspect validity and unit"
                )
            core.create_price_list_entry(
                session,
                tenant,
                price_list.id,
                item.id,
                10,
                quote["unit_price"],
                item.unit,
            )
        if not session.scalar(
            select(SupplierItemNumber.id).where(
                SupplierItemNumber.tenant_id == tenant,
                SupplierItemNumber.party_id == supplier_id,
                SupplierItemNumber.item_id == item.id,
            )
        ):
            set_supplier_item_number(
                session,
                tenant,
                supplier_id,
                item.id,
                quote["supplier_item_number"],
                item.name,
            )
        if not session.scalar(
            select(SupplierItemTerms.id).where(
                SupplierItemTerms.tenant_id == tenant,
                SupplierItemTerms.party_id == supplier_id,
                SupplierItemTerms.item_id == item.id,
            )
        ):
            set_supplier_item_terms(session, tenant, supplier_id, item.id, 10, 5)
    session.commit()
    return {
        **next(
            s
            for s in catalogue(session, tenant, config)
            if s["supplier_id"] == supplier_id
        ),
        "quote_source_record_id": source.id,
    }
