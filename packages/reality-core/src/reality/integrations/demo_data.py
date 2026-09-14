"""Synthetic order inputs; interpretation preserves the ordinary evidence chain."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Commitment, Document, DocumentLine, SourceRecord
from reality.demo.international import DEMO_DATA_CUSTOMERS, DEMO_DATA_PAYMENT_TERM


class DemoLine(BaseModel):
    model_config = ConfigDict(extra="allow")
    item_id: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    gross_amount: Decimal = Field(ge=0)
    unit: str = Field(min_length=1)
    source_line_id: str


class DemoOrder(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: Literal[1]
    synthetic: Literal[True]
    schedule_id: str
    delivery_id: str
    number: str
    ordered_at: datetime
    due_at: datetime
    company_party_id: str
    customer_party_id: str
    location_id: str
    currency: Literal["EUR", "USD"]
    gross_amount: Decimal = Field(ge=0)
    lines: list[DemoLine] = Field(min_length=1, max_length=10)
    # Feature 168: the shop's technical id and the customer's own order number,
    # optional so payloads stored before the feature still validate.
    shop_id: str | None = None
    customer_reference: str = ""


# Relative demand by UTC hour: a quiet night, a morning ramp, a small lunch
# dip and an evening shopping peak, as e-commerce order intake usually looks.
# Normalised so the day averages exactly 1.0 and the selected hourly rate stays
# the daily mean; individual hours run between roughly 70 and 130 percent.
_HOURLY_SHAPE = (
    0.75, 0.70, 0.70, 0.70, 0.72, 0.78, 0.88, 0.98, 1.06, 1.10, 1.12, 1.08,
    1.02, 1.06, 1.10, 1.12, 1.14, 1.18, 1.26, 1.30, 1.28, 1.20, 1.06, 0.91,
)  # fmt: skip
HOURLY_DEMAND = tuple(
    round(value * len(_HOURLY_SHAPE) / sum(_HOURLY_SHAPE), 6) for value in _HOURLY_SHAPE
)
MAX_BURST = 6


def _draw(seed: str, schedule_id: str, delivery_id: str, purpose: str) -> int:
    digest = hashlib.sha256(
        f"{seed}:{schedule_id}:{delivery_id}:{purpose}".encode()
    ).hexdigest()
    return int(digest[:8], 16)


def burst_size(seed: str, schedule_id: str, delivery_id: str, at: datetime) -> int:
    """How many orders one durable delivery carries; reproducible per delivery.

    Orders arrive like a Poisson process whose intensity follows the hour of
    day, so a 60/hour run really delivers about 42 to 78 orders in an hour.
    """
    expected = HOURLY_DEMAND[at.astimezone(UTC).hour]
    uniform = _draw(seed, schedule_id, delivery_id, "burst") / 2**32
    size, probability = 0, math.exp(-expected)
    cumulative = probability
    while uniform > cumulative and size < MAX_BURST:
        size += 1
        probability *= expected / size
        cumulative += probability
    return size


def customer_reference(choice: int, references: dict) -> str:
    """Pick a customer the schedule references, favouring the first pool entries.

    Squaring a uniform draw skews demand toward a few large buyers with a long
    tail of occasional ones, which reads like a real order book.
    """
    customers = [key for key, _ in DEMO_DATA_CUSTOMERS if key in references["parties"]]
    if not customers:
        raise ValueError("Demo Data references contain no customer.")
    position = (choice % 10_000) / 10_000
    return references["parties"][customers[int(len(customers) * position * position)]]


def produce(
    schedule_id: str,
    delivery_id: str,
    seed: str,
    at: datetime,
    references: dict,
    position: int = 1,
) -> dict:
    """One synthetic order; `position` distinguishes orders within one delivery."""
    choice = _draw(seed, schedule_id, delivery_id, f"order:{position}")
    keys = ("P01", "P02", "P11", "P12")
    item = keys[choice % 4]
    suffix = f"-{position}" if position > 1 else ""
    return {
        "schema_version": 1,
        "profile_version": 1,
        "synthetic": True,
        "schedule_id": schedule_id,
        "delivery_id": delivery_id,
        "number": f"DEMO-{delivery_id[-12:].upper()}{suffix}",
        "shop_id": "demo-shop-"
        + hashlib.sha256(
            f"{schedule_id}:{delivery_id}:{position}".encode()
        ).hexdigest()[:12],
        "customer_reference": f"PO-{_draw(seed, schedule_id, delivery_id, f'po:{position}') % 900_000 + 100_000}",
        "ordered_at": at.isoformat(),
        "due_at": (at + timedelta(days=3)).isoformat(),
        "company_party_id": references["parties"]["company"],
        "customer_party_id": customer_reference(choice // 4, references),
        "location_id": references["locations"]["A"],
        "currency": "USD" if choice % 5 == 0 else "EUR",
        "gross_amount": "25",
        "amount_basis": "gross",
        "tax_amount": "0",
        "discount_amount": "0",
        "lines": [
            {
                "item_id": references["items"][item],
                "quantity": "1",
                "unit_price": "25",
                "gross_amount": "25",
                "unit": "pcs",
                "source_line_id": "1",
            }
        ],
    }


def plan(
    schedule_id: str, delivery_id: str, seed: str, at: datetime, references: dict
) -> list[dict]:
    """Every order one delivery carries, in stable position order."""
    return [
        produce(schedule_id, delivery_id, seed, at, references, position)
        for position in range(1, burst_size(seed, schedule_id, delivery_id, at) + 1)
    ]


# --- Feature 168: settlement plan, invoice and payment payloads -----------------
#
# Every synthetic order gets one order-to-cash story derived from the run seed.
# The tables below are the only place the version 1 mix lives. Amounts are
# computed here once and written into the payloads as stated facts; no service
# ever derives a difference or a discount from them (spec 088 DR-007).

OUTCOME_WEIGHTS = {
    "exact": 91,
    "short_discount": 2,
    "short_withheld": 1,
    "short_partial": 1,
    "over": 1,
    "unmatched": 1,
    "late": 2,
    "never": 1,
}
MONEY_PATH_WEIGHTS = {"provider": 60, "bank": 40}
# Compressed wall-clock delays in minutes; spec 146 forbids an accelerated clock.
DELAYS = {"invoice": (2, 10), "provider": (1, 3), "bank": (10, 90), "second": (20, 120)}
LATE_DAYS = (1, 6)
PAYMENT_TERM = DEMO_DATA_PAYMENT_TERM
_DIFFERENCES = {name for name in OUTCOME_WEIGHTS if name != "exact"}
_CENT = Decimal("0.01")

ReferenceType = Literal[
    "invoice_number",
    "shop_id",
    "shop_order_number",
    "customer_reference",
    "customer_number",
]
Outcome = Literal[
    "exact",
    "short_discount",
    "short_withheld",
    "short_partial",
    "over",
    "unmatched",
    "late",
    "never",
]


class Reference(BaseModel):
    """One identifier the payer or provider states, as stated."""

    model_config = ConfigDict(frozen=True)
    type: ReferenceType
    value: str = Field(min_length=1)


class PlannedPayment(BaseModel):
    model_config = ConfigDict(frozen=True)
    index: int = Field(ge=1)
    at: datetime
    amount: Decimal = Field(gt=0)
    references: tuple[Reference, ...]
    remittance_text: str


class SettlementPlan(BaseModel):
    model_config = ConfigDict(frozen=True)
    order_external_id: str
    money_path: Literal["provider", "bank"]
    outcome: Outcome
    invoice_number: str
    invoice_at: datetime
    due_at: datetime
    payments: tuple[PlannedPayment, ...]


class DemoInvoiceLine(BaseModel):
    model_config = ConfigDict(extra="allow")
    item_id: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    gross_amount: Decimal = Field(ge=0)
    unit: str = Field(min_length=1)
    source_line_id: str
    order_source_line_id: str


class DemoInvoice(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: Literal[1]
    synthetic: Literal[True]
    schedule_id: str
    delivery_id: str
    order_external_id: str
    number: str
    issued_at: datetime
    due_at: datetime
    payment_term_code: str
    company_party_id: str
    customer_party_id: str
    currency: Literal["EUR", "USD"]
    gross_amount: Decimal = Field(ge=0)
    lines: list[DemoInvoiceLine] = Field(min_length=1, max_length=10)


class DemoPayment(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: Literal[1]
    synthetic: Literal[True]
    schedule_id: str
    delivery_id: str
    order_external_id: str
    payment_index: int = Field(ge=1)
    money_path: Literal["provider", "bank"]
    payment_number: str
    external_id: str
    customer_party_id: str
    direction: Literal["incoming"]
    amount: Decimal = Field(gt=0)
    currency: Literal["EUR", "USD"]
    effective_at: datetime
    references: list[Reference]
    remittance_text: str


def invoice_external_id(order_external_id: str) -> str:
    return f"{order_external_id}:invoice"


def payment_external_id(order_external_id: str, index: int) -> str:
    return f"{order_external_id}:payment:{index}"


def _uniform(
    seed: str, schedule_id: str, order_external_id: str, purpose: str
) -> float:
    return _draw(seed, schedule_id, order_external_id, f"settle:{purpose}") / 2**32


def _between(
    seed: str,
    schedule_id: str,
    order_external_id: str,
    purpose: str,
    low: int,
    high: int,
) -> int:
    return low + _draw(seed, schedule_id, order_external_id, f"settle:{purpose}") % (
        high - low + 1
    )


def _pick(weights: dict[str, int], uniform: float) -> str:
    threshold = uniform * sum(weights.values())
    cumulative = 0
    for name, weight in weights.items():
        cumulative += weight
        if threshold < cumulative:
            return name
    return name


def _money(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def settlement_plan(
    seed: str, schedule_id: str, order_external_id: str, order: dict
) -> SettlementPlan:
    """The whole order-to-cash story of one synthetic order, reproducible from its inputs."""

    def draw(purpose: str) -> float:
        return _uniform(seed, schedule_id, order_external_id, purpose)

    def between(purpose: str, low: int, high: int) -> int:
        return _between(seed, schedule_id, order_external_id, purpose, low, high)

    outcome = _pick(OUTCOME_WEIGHTS, draw("outcome"))
    if outcome in _DIFFERENCES:
        money_path = "bank"
    else:
        # Differences all lie on the bank path, so exact orders carry the rest of
        # the bank share: (bank weight - difference weight) out of the exact weight.
        bank_share = MONEY_PATH_WEIGHTS["bank"] - sum(
            OUTCOME_WEIGHTS[name] for name in _DIFFERENCES
        )
        money_path = (
            "bank"
            if draw("path") * OUTCOME_WEIGHTS["exact"] < bank_share
            else "provider"
        )

    ordered_at = datetime.fromisoformat(order["ordered_at"])
    invoice_at = ordered_at + timedelta(minutes=between("invoice", *DELAYS["invoice"]))
    due_at = invoice_at + timedelta(days=PAYMENT_TERM["due_days"])
    invoice_number = "INV-" + order["number"].removeprefix("DEMO-")
    gross = Decimal(order["gross_amount"])

    def first_at() -> datetime:
        if outcome == "late":
            return (
                due_at
                + timedelta(days=between("late_days", *LATE_DAYS))
                + timedelta(minutes=between("late_minutes", 0, 1439))
            )
        return invoice_at + timedelta(minutes=between("first", *DELAYS[money_path]))

    def second_at(previous: datetime) -> datetime:
        return previous + timedelta(minutes=between("second", *DELAYS["second"]))

    invoice_ref = Reference(type="invoice_number", value=invoice_number)
    if money_path == "provider":
        references: tuple[Reference, ...] = (
            Reference(type="shop_id", value=order["shop_id"]),
            Reference(type="shop_order_number", value=order["number"]),
        )
        text = f"Order {order['number']}"
    else:
        references = (invoice_ref,)
        text = f"Invoice {invoice_number}"

    payments: list[PlannedPayment] = []

    def add(
        amount: Decimal, at: datetime, refs: tuple[Reference, ...], note: str
    ) -> None:
        payments.append(
            PlannedPayment(
                index=len(payments) + 1,
                at=at,
                amount=_money(amount),
                references=refs,
                remittance_text=note,
            )
        )

    if outcome in {"exact", "late"}:
        add(gross, first_at(), references, text)
    elif outcome == "short_discount":
        percent = 2 if draw("discount") < 0.7 else 3
        add(
            gross - gross * Decimal(percent) / 100,
            first_at(),
            references,
            f"{text} less {percent}% discount",
        )
    elif outcome == "short_withheld":
        withheld = Decimal(between("withheld", 50, 600)) / 100
        if withheld >= gross:
            withheld = Decimal("0.50")
        add(gross - withheld, first_at(), references, f"{text} less freight")
    elif outcome == "short_partial":
        first = _money(gross * Decimal(between("partial", 40, 70)) / 100)
        at = first_at()
        add(first, at, references, f"{text} part 1")
        add(gross - first, second_at(at), references, f"{text} part 2")
    elif outcome == "over":
        if draw("over") < 0.5:
            at = first_at()
            add(gross, at, references, text)
            add(gross, second_at(at), references, text)
        else:
            rounded = (gross // 10 + 1) * 10
            add(rounded, first_at(), references, text)
    elif outcome == "unmatched":
        variant = between("unmatched", 0, 2)
        if variant == 0:
            refs: tuple[Reference, ...] = (
                Reference(
                    type="customer_number",
                    value=f"CUST-{order['customer_party_id'][-6:]}",
                ),
            )
            note = "Payment"
        elif variant == 1:
            wrong = f"PO-{between('wrong_po', 100_000, 999_999)}"
            if wrong == order.get("customer_reference"):
                wrong = f"PO-{100_000 if wrong != 'PO-100000' else 100_001}"
            refs = (Reference(type="customer_reference", value=wrong),)
            note = f"Our order {wrong}"
        else:
            typo = invoice_number[:-1] + ("0" if invoice_number[-1] != "0" else "1")
            refs = (Reference(type="invoice_number", value=typo),)
            note = f"Invoice {typo}"
        add(gross, first_at(), refs, note)
    # "never": no payment is ever produced.

    return SettlementPlan(
        order_external_id=order_external_id,
        money_path=money_path,
        outcome=outcome,
        invoice_number=invoice_number,
        invoice_at=invoice_at,
        due_at=due_at,
        payments=tuple(payments),
    )


def produce_invoice(order: dict, order_external_id: str, plan: SettlementPlan) -> dict:
    """The billing system's invoice for one synthetic order, lossless and versioned."""
    return {
        "schema_version": 1,
        "profile_version": 1,
        "synthetic": True,
        "schedule_id": order["schedule_id"],
        "delivery_id": order["delivery_id"],
        "order_external_id": order_external_id,
        "number": plan.invoice_number,
        "issued_at": plan.invoice_at.isoformat(),
        "due_at": plan.due_at.isoformat(),
        "payment_term_code": PAYMENT_TERM["code"],
        "company_party_id": order["company_party_id"],
        "customer_party_id": order["customer_party_id"],
        "currency": order["currency"],
        "gross_amount": order["gross_amount"],
        "amount_basis": order.get("amount_basis", "gross"),
        "tax_amount": order.get("tax_amount", "0"),
        "discount_amount": order.get("discount_amount", "0"),
        "lines": [
            {**line, "order_source_line_id": line["source_line_id"]}
            for line in order["lines"]
        ],
    }


def produce_payment(
    order: dict, invoice: dict, plan: SettlementPlan, index: int
) -> dict:
    """One bank line or provider capture, named like the bank-statement file profile."""
    planned = plan.payments[index - 1]
    external_id = invoice["order_external_id"]
    digest = hashlib.sha256(f"{external_id}:payment:{index}".encode()).hexdigest()[:16]
    return {
        "schema_version": 1,
        "profile_version": 1,
        "synthetic": True,
        "schedule_id": order["schedule_id"],
        "delivery_id": order["delivery_id"],
        "order_external_id": external_id,
        "payment_index": index,
        "money_path": plan.money_path,
        "payment_number": f"PAY-{order['number'].removeprefix('DEMO-')}-{index}",
        "external_id": f"demo-txn-{digest}",
        "customer_party_id": order["customer_party_id"],
        "direction": "incoming",
        "amount": str(planned.amount),
        "currency": order["currency"],
        "effective_at": planned.at.isoformat(),
        "references": [reference.model_dump() for reference in planned.references],
        "remittance_text": planned.remittance_text,
    }


def interpret(session: Session, tenant_id: str, source: SourceRecord, context: dict):
    from reality.services import core
    from reality.services.tenant_policy import require_demo_intake

    require_demo_intake(session, tenant_id)
    existing = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.source_record_id == source.id,
            Document.type == "sales_order",
        )
    )
    if existing:
        return (
            source,
            existing,
            list(
                session.scalars(
                    select(DocumentLine).where(
                        DocumentLine.tenant_id == tenant_id,
                        DocumentLine.document_id == existing.id,
                    )
                )
            ),
            list(
                session.scalars(
                    select(Commitment).where(
                        Commitment.tenant_id == tenant_id,
                        Commitment.document_id == existing.id,
                    )
                )
            ),
        )
    order = DemoOrder.model_validate(json.loads(source.payload))
    document, lines = core.create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_order",
        order.number,
        order.customer_party_id,
        [line.model_dump(mode="json") for line in order.lines],
        order.gross_amount,
        currency=order.currency,
        ordered_at=order.ordered_at,
        requested_delivery_at=order.due_at,
        document_date=order.ordered_at.date().isoformat(),
        customer_reference=order.customer_reference,
        sales_channel="demo_data",
        source_record_id=source.id,
        _commit=False,
    )
    commitments = [
        core.create_commitment(
            session,
            tenant_id,
            "customer_delivery",
            order.company_party_id,
            order.customer_party_id,
            line.item_id,
            order.location_id,
            line.quantity,
            order.due_at,
            amount=line.gross_amount,
            currency=order.currency,
            document_id=document.id,
            document_line_id=line.id,
            _commit=False,
        )
        for line in lines
    ]
    return source, document, lines, commitments


def normalise_invoice(payload: dict):
    """Map the synthetic invoice one to one onto the shared shape; lazy import keeps the boundary."""
    from reality.services.payment_intake import (
        NormalisedInvoice,
        NormalisedInvoiceLine,
    )

    invoice = DemoInvoice.model_validate(payload)
    return NormalisedInvoice(
        order_source_system="demo_data",
        order_source_type="order",
        order_external_id=invoice.order_external_id,
        number=invoice.number,
        party_id=invoice.customer_party_id,
        currency=invoice.currency,
        issued_at=invoice.issued_at,
        due_at=invoice.due_at,
        payment_term_code=invoice.payment_term_code,
        gross_amount=invoice.gross_amount,
        lines=tuple(
            NormalisedInvoiceLine(
                order_source_line_id=line.order_source_line_id,
                source_line_id=line.source_line_id,
                item_id=line.item_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                gross_amount=line.gross_amount,
                unit=line.unit,
            )
            for line in invoice.lines
        ),
    )


def normalise_payment(payload: dict):
    from reality.services.payment_intake import NormalisedPayment
    from reality.services.payment_intake import Reference as SharedReference

    payment = DemoPayment.model_validate(payload)
    return NormalisedPayment(
        party_id=payment.customer_party_id,
        amount=payment.amount,
        currency=payment.currency,
        effective_at=payment.effective_at,
        external_payment_id=payment.external_id,
        payment_number=payment.payment_number,
        money_path=payment.money_path,
        references=tuple(
            SharedReference(type=reference.type, value=reference.value)
            for reference in payment.references
        ),
        remittance_text=payment.remittance_text,
    )


def interpret_invoice(
    session: Session, tenant_id: str, source: SourceRecord, context: dict
):
    from reality.services import payment_intake
    from reality.services.tenant_policy import require_demo_intake

    require_demo_intake(session, tenant_id, settlement=True)
    return payment_intake.interpret_sales_invoice(
        session, tenant_id, source, normalise_invoice(json.loads(source.payload))
    )


def interpret_payment(
    session: Session, tenant_id: str, source: SourceRecord, context: dict
):
    from reality.services import payment_intake
    from reality.services.tenant_policy import require_demo_intake

    require_demo_intake(session, tenant_id, settlement=True)
    return payment_intake.interpret_customer_payment(
        session, tenant_id, source, normalise_payment(json.loads(source.payload))
    )
