from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import case, func, insert, select, text
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    ProjectionRow,
    Reservation,
    SourceRecord,
    Tenant,
)
from reality.services.finance.accounts import _bootstrap_accounts, resolve_account
from reality.services.projections import refresh_operational_projections

DEFINITION_VERSION = "large-tenant-registers-v1"
BENCHMARK_SOURCE = "benchmark-commerce"
SENTINEL = "CONTROL-TENANT-SENTINEL"


@dataclass(frozen=True)
class DatasetProfile:
    """How much of each family the fixture builds.

    `financial_count` used to be 120 in both profiles, so the full profile built
    10,000 orders and 120 finance documents. Every read that derives money was
    therefore measured on a company a hundredth the size of the one it claimed to
    describe, and the derivations that fold a company's finance history in memory
    looked free. A company with 10,000 orders has roughly 10,000 invoices, so the
    full profile now says so, and both counts can be overridden for a scale run.

    `open_every` leaves every nth invoice without its payment. Without it every
    document nets to zero and the open-item path, which is the expensive one,
    returns nothing to work on.
    """

    name: str
    seed: int
    business_date: date
    order_count: int
    item_count: int = 150
    financial_count: int = 120
    open_every: int = 5

    @classmethod
    def reduced(cls, *, seed: int, business_date: date) -> DatasetProfile:
        return cls("reduced", seed, business_date, 120)

    @classmethod
    def full(
        cls,
        *,
        seed: int,
        business_date: date,
        order_count: int = 10_000,
        financial_count: int | None = None,
    ) -> DatasetProfile:
        return cls(
            "full",
            seed,
            business_date,
            order_count,
            financial_count=order_count if financial_count is None else financial_count,
        )


@dataclass(frozen=True)
class DatasetHandle:
    definition_version: str
    profile: DatasetProfile
    tenant_id: str
    control_tenant_id: str
    company_id: str
    customer_id: str
    location_id: str
    item_ids: tuple[str, ...]
    commitment_ids: tuple[str, ...]
    cardinalities: dict[str, int]


def _id(kind: str, tenant_tag: str, number: int) -> str:
    digest = hashlib.sha256(f"{tenant_tag}:{kind}:{number}".encode()).hexdigest()[:16]
    return f"{kind}_{digest}"


def _insert_chunks(session: Session, model, rows: list[dict], size: int = 1000) -> None:
    for start in range(0, len(rows), size):
        session.execute(insert(model), rows[start : start + size])


def _build_control_records(
    session: Session,
    *,
    tag: str,
    tenant_id: str,
    party_id: str,
    item_id: str,
    location_id: str,
    moment: datetime,
) -> None:
    source_id = _id("src", f"{tag}c", 0)
    order_id = _id("doc", f"{tag}c", 0)
    line_id = _id("dln", f"{tag}c", 0)
    commitment_id = _id("com", f"{tag}c", 0)
    payload = json.dumps({"external_id": SENTINEL}, sort_keys=True)
    session.add(
        SourceRecord(
            id=source_id,
            tenant_id=tenant_id,
            source_system=BENCHMARK_SOURCE,
            source_type="sales_order",
            external_id=SENTINEL,
            payload=payload,
            payload_hash=hashlib.sha256(payload.encode()).hexdigest(),
            version=1,
            received_at=moment,
        )
    )
    session.flush()
    session.add(
        Document(
            id=order_id,
            tenant_id=tenant_id,
            source_record_id=source_id,
            type="sales_order",
            number=SENTINEL,
            party_id=party_id,
            currency="EUR",
            gross_amount=Decimal(1),
            status="recorded",
            document_date=moment.date().isoformat(),
            ordered_at=moment,
            requested_delivery_at=moment + timedelta(days=1),
        )
    )
    session.flush()
    session.add(
        DocumentLine(
            id=line_id,
            tenant_id=tenant_id,
            document_id=order_id,
            source_line_id="1",
            item_id=item_id,
            sku="SKU-0000",
            description=SENTINEL,
            quantity=Decimal(1),
            unit_price=Decimal(1),
            gross_amount=Decimal(1),
            payload=payload,
            requested_at=moment + timedelta(days=1),
        )
    )
    session.flush()
    session.add(
        Commitment(
            id=commitment_id,
            tenant_id=tenant_id,
            type="customer_delivery",
            from_party_id=party_id,
            to_party_id=party_id,
            item_id=item_id,
            location_id=location_id,
            quantity=Decimal(1),
            amount=Decimal(1),
            currency="EUR",
            due_at=moment + timedelta(days=1),
            status="open",
            document_id=order_id,
            document_line_id=line_id,
            priority="normal",
        )
    )
    session.flush()
    session.add_all(
        [
            Reservation(
                id=_id("res", f"{tag}c", 0),
                tenant_id=tenant_id,
                commitment_id=commitment_id,
                item_id=item_id,
                location_id=location_id,
                quantity=Decimal(1),
                status="active",
                reserved_at=moment,
            ),
            Movement(
                id=_id("mov", f"{tag}c", 0),
                tenant_id=tenant_id,
                type="opening_stock",
                item_id=item_id,
                to_location_id=location_id,
                quantity=Decimal(10),
                occurred_at=moment,
            ),
        ]
    )
    invoice_id = _id("inv", f"{tag}c", 0)
    payment_id = _id("pay", f"{tag}c", 0)
    session.add_all(
        [
            Document(
                id=invoice_id,
                tenant_id=tenant_id,
                type="sales_invoice",
                number=f"{SENTINEL}-INV",
                party_id=party_id,
                currency="EUR",
                gross_amount=Decimal(10),
                status="recorded",
                document_date=moment.date().isoformat(),
            ),
            Document(
                id=payment_id,
                tenant_id=tenant_id,
                type="customer_payment",
                number=f"{SENTINEL}-PAY",
                party_id=party_id,
                currency="EUR",
                gross_amount=Decimal(10),
                status="recorded",
                document_date=moment.date().isoformat(),
            ),
        ]
    )
    session.flush()
    session.add_all(
        [
            LedgerEntry(
                id=_id("led", f"{tag}c", 0),
                tenant_id=tenant_id,
                posting_group_id="control-invoice",
                account_id=resolve_account(
                    session, tenant_id, "accounts_receivable"
                ).id,
                party_id=party_id,
                amount=Decimal(10),
                currency="EUR",
                debit_credit="debit",
                effective_at=moment,
                document_id=invoice_id,
            ),
            LedgerEntry(
                id=_id("led", f"{tag}c", 1),
                tenant_id=tenant_id,
                posting_group_id="control-invoice",
                account_id=resolve_account(session, tenant_id, "sales_revenue").id,
                party_id=party_id,
                amount=Decimal(10),
                currency="EUR",
                debit_credit="credit",
                effective_at=moment,
                document_id=invoice_id,
            ),
            LedgerEntry(
                id=_id("led", f"{tag}c", 2),
                tenant_id=tenant_id,
                posting_group_id="control-payment",
                account_id=resolve_account(session, tenant_id, "cash").id,
                party_id=party_id,
                amount=Decimal(10),
                currency="EUR",
                debit_credit="debit",
                effective_at=moment,
                document_id=payment_id,
            ),
            LedgerEntry(
                id=_id("led", f"{tag}c", 3),
                tenant_id=tenant_id,
                posting_group_id="control-payment",
                account_id=resolve_account(
                    session, tenant_id, "accounts_receivable"
                ).id,
                party_id=party_id,
                amount=Decimal(10),
                currency="EUR",
                debit_credit="credit",
                effective_at=moment,
                document_id=payment_id,
            ),
        ]
    )
    session.flush()


def build_dataset(session: Session, profile: DatasetProfile) -> DatasetHandle:
    tag = f"b{profile.seed}"
    tenant_id = _id("ten", tag, 0)
    control_tenant_id = _id("ten", tag, 1)
    if session.get(Tenant, tenant_id) is not None:
        raise ValueError(
            "Benchmark dataset already exists; explicit rebuild is required."
        )

    company_id = _id("pty", tag, 0)
    customer_id = _id("pty", tag, 1)
    location_id = _id("loc", tag, 0)
    session.add_all(
        [
            Tenant(id=tenant_id, name=f"Benchmark Tenant {profile.seed}"),
            Tenant(id=control_tenant_id, name=f"Control Tenant {profile.seed}"),
        ]
    )
    session.flush()
    _bootstrap_accounts(session, tenant_id)
    _bootstrap_accounts(session, control_tenant_id)
    account_ids = {
        role: resolve_account(session, tenant_id, role).id
        for role in ("accounts_receivable", "cash", "sales_revenue")
    }
    session.add_all(
        [
            Party(
                id=company_id,
                tenant_id=tenant_id,
                type="company",
                name="Benchmark Company",
            ),
            Party(
                id=customer_id,
                tenant_id=tenant_id,
                type="customer",
                name="Benchmark Customer",
            ),
            Location(id=location_id, tenant_id=tenant_id, name="Benchmark Warehouse"),
        ]
    )
    control_party = _id("pty", f"{tag}c", 0)
    control_item = _id("itm", f"{tag}c", 0)
    control_location = _id("loc", f"{tag}c", 0)
    session.flush()
    session.add_all(
        [
            Party(
                id=control_party,
                tenant_id=control_tenant_id,
                type="customer",
                name=SENTINEL,
            ),
            Item(
                id=control_item,
                tenant_id=control_tenant_id,
                sku="SKU-0000",
                name=SENTINEL,
            ),
            Location(id=control_location, tenant_id=control_tenant_id, name=SENTINEL),
        ]
    )
    session.flush()

    item_ids = tuple(_id("itm", tag, index) for index in range(profile.item_count))
    _insert_chunks(
        session,
        Item,
        [
            {
                "id": item_id,
                "tenant_id": tenant_id,
                "sku": f"SKU-{index:04d}",
                "name": f"Benchmark Item {index:04d}",
                "unit": "pcs",
            }
            for index, item_id in enumerate(item_ids)
        ],
    )

    moment = datetime.combine(profile.business_date, datetime.min.time(), tzinfo=UTC)
    sources: list[dict] = []
    documents: list[dict] = []
    lines: list[dict] = []
    commitments: list[dict] = []
    for index in range(profile.order_count):
        source_id = _id("src", tag, index)
        document_id = _id("doc", tag, index)
        external_id = f"ORDER-{index:06d}"
        line_count = 1 + index % 3
        order_amount = sum(
            Decimal((index + ordinal) % 500 + 1) for ordinal in range(line_count)
        )
        payload = json.dumps(
            {"external_id": external_id, "seed": profile.seed}, sort_keys=True
        )
        sources.append(
            {
                "id": source_id,
                "tenant_id": tenant_id,
                "source_system": BENCHMARK_SOURCE,
                "source_type": "sales_order",
                "external_id": external_id,
                "payload": payload,
                "payload_hash": hashlib.sha256(payload.encode()).hexdigest(),
                "version": 1,
                "received_at": moment + timedelta(seconds=index % 86400),
            }
        )
        documents.append(
            {
                "id": document_id,
                "tenant_id": tenant_id,
                "source_record_id": source_id,
                "type": "sales_order",
                "number": external_id,
                "party_id": customer_id,
                "currency": "EUR",
                "gross_amount": order_amount,
                "status": "recorded",
                "document_date": profile.business_date.isoformat(),
                "ordered_at": moment + timedelta(seconds=index % 86400),
                "requested_delivery_at": moment + timedelta(days=1 + index % 5),
                "customer_reference": f"REF-{index:06d}",
                "sales_channel": "benchmark",
            }
        )
        for ordinal in range(line_count):
            line_number = index * 3 + ordinal
            line_id = _id("dln", tag, line_number)
            commitment_id = _id("com", tag, line_number)
            item_index = (index + ordinal) % len(item_ids)
            item_id = item_ids[item_index]
            line_amount = Decimal((index + ordinal) % 500 + 1)
            lines.append(
                {
                    "id": line_id,
                    "tenant_id": tenant_id,
                    "document_id": document_id,
                    "source_line_id": str(ordinal + 1),
                    "item_id": item_id,
                    "sku": f"SKU-{item_index:04d}",
                    "description": f"Benchmark line {index}-{ordinal}",
                    "quantity": Decimal(1),
                    "unit_price": line_amount,
                    "gross_amount": line_amount,
                    "payload": "{}",
                    "requested_at": moment + timedelta(days=1 + index % 5),
                }
            )
            commitments.append(
                {
                    "id": commitment_id,
                    "tenant_id": tenant_id,
                    "type": "customer_delivery",
                    "from_party_id": company_id,
                    "to_party_id": customer_id,
                    "item_id": item_id,
                    "location_id": location_id,
                    "quantity": Decimal(1),
                    "amount": line_amount,
                    "currency": "EUR",
                    "due_at": moment + timedelta(days=1 + index % 5),
                    "status": "open",
                    "document_id": document_id,
                    "document_line_id": line_id,
                    "priority": ("high" if index % 10 == 0 else "normal"),
                }
            )
    _insert_chunks(session, SourceRecord, sources)
    _insert_chunks(session, Document, documents)
    _insert_chunks(session, DocumentLine, lines)
    _insert_chunks(session, Commitment, commitments)

    commitment_ids = tuple(row["id"] for row in commitments)
    reservation_count = min(140, len(commitment_ids))
    _insert_chunks(
        session,
        Reservation,
        [
            {
                "id": _id("res", tag, index),
                "tenant_id": tenant_id,
                "commitment_id": commitment_ids[index],
                "item_id": commitments[index]["item_id"],
                "location_id": location_id,
                "quantity": Decimal(1),
                "status": "active",
                "reserved_at": moment + timedelta(minutes=index),
            }
            for index in range(reservation_count)
        ],
    )
    _insert_chunks(
        session,
        Movement,
        [
            {
                "id": _id("mov", tag, index),
                "tenant_id": tenant_id,
                "type": "opening_stock",
                "item_id": item_id,
                "to_location_id": location_id,
                "quantity": Decimal(1000),
                "occurred_at": moment,
            }
            for index, item_id in enumerate(item_ids)
        ],
    )

    invoice_docs: list[dict] = []
    payment_docs: list[dict] = []
    ledger: list[dict] = []
    for index in range(profile.financial_count):
        invoice_id = _id("inv", tag, index)
        payment_id = _id("pay", tag, index)
        amount = Decimal((index % 90) + 10)
        invoice_docs.append(
            {
                "id": invoice_id,
                "tenant_id": tenant_id,
                "type": "sales_invoice",
                "number": f"INV-{index:05d}",
                "party_id": customer_id,
                "currency": "EUR",
                "gross_amount": amount,
                "status": "recorded",
                "document_date": profile.business_date.isoformat(),
            }
        )
        # Every nth invoice keeps no payment, so the register has something open
        # to derive rather than a company that nets to zero.
        settled = profile.open_every <= 0 or index % profile.open_every != 0
        if settled:
            payment_docs.append(
                {
                    "id": payment_id,
                    "tenant_id": tenant_id,
                    "type": "customer_payment",
                    "number": f"PAY-{index:05d}",
                    "party_id": customer_id,
                    "currency": "EUR",
                    "gross_amount": amount,
                    "status": "recorded",
                    "document_date": profile.business_date.isoformat(),
                }
            )
        postings = [
            (0, "accounts_receivable", "debit", invoice_id, f"invoice-{index}"),
            (1, "sales_revenue", "credit", invoice_id, f"invoice-{index}"),
        ]
        if settled:
            postings += [
                (2, "cash", "debit", payment_id, f"payment-{index}"),
                (3, "accounts_receivable", "credit", payment_id, f"payment-{index}"),
            ]
        for suffix, account, side, document_id, group in postings:
            ledger.append(
                {
                    "id": _id("led", tag, index * 4 + suffix),
                    "tenant_id": tenant_id,
                    "posting_group_id": group,
                    "account_id": account_ids[account],
                    "party_id": customer_id,
                    "amount": amount,
                    "currency": "EUR",
                    "debit_credit": side,
                    "effective_at": moment + timedelta(minutes=index),
                    "document_id": document_id,
                }
            )
    _insert_chunks(session, Document, invoice_docs + payment_docs)
    _insert_chunks(session, LedgerEntry, ledger)
    session.flush()

    _build_control_records(
        session,
        tag=tag,
        tenant_id=control_tenant_id,
        party_id=control_party,
        item_id=control_item,
        location_id=control_location,
        moment=moment,
    )

    # Projection construction is setup, not measured read time. It uses the same
    # authoritative projection builder as Product Web and is never hand-authored.
    refresh_operational_projections(session, tenant_id, force=True)
    refresh_operational_projections(session, control_tenant_id, force=True)

    # A freshly built company has whatever statistics autovacuum happened to reach
    # in time, so the planner's choices — and therefore the recorded durations —
    # depended on a race with a background daemon. One measured derivation came out
    # slower at half the data than at full, reproducibly, until this ran. A real
    # database converges on analysed statistics; the fixture states them.
    session.commit()
    session.execute(text("ANALYZE"))
    return load_dataset(session, profile)


def load_dataset(session: Session, profile: DatasetProfile) -> DatasetHandle:
    tag = f"b{profile.seed}"
    tenant_id = _id("ten", tag, 0)
    control_tenant_id = _id("ten", tag, 1)
    if (
        session.get(Tenant, tenant_id) is None
        or session.get(Tenant, control_tenant_id) is None
    ):
        raise ValueError(
            "Completed benchmark and control tenants are required for reuse."
        )
    handle = DatasetHandle(
        DEFINITION_VERSION,
        profile,
        tenant_id,
        control_tenant_id,
        _id("pty", tag, 0),
        _id("pty", tag, 1),
        _id("loc", tag, 0),
        tuple(_id("itm", tag, index) for index in range(profile.item_count)),
        tuple(
            _id("com", tag, index * 3 + ordinal)
            for index in range(profile.order_count)
            for ordinal in range(1 + index % 3)
        ),
        validate_cardinalities(session, tenant_id),
    )
    validate_dataset(session, handle)
    return handle


def validate_cardinalities(session: Session, tenant_id: str) -> dict[str, int]:
    models = {
        "source_records": SourceRecord,
        "documents": Document,
        "document_lines": DocumentLine,
        "commitments": Commitment,
        "items": Item,
        "reservations": Reservation,
        "movements": Movement,
        "ledger_entries": LedgerEntry,
        "projection_rows": ProjectionRow,
    }
    counts = {
        name: int(
            session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.tenant_id == tenant_id)
            )
            or 0
        )
        for name, model in models.items()
    }
    counts["orders"] = int(
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == tenant_id, Document.type == "sales_order")
        )
        or 0
    )
    return counts


def validate_dataset(session: Session, dataset: DatasetHandle) -> dict[str, int]:
    counts = validate_cardinalities(session, dataset.tenant_id)
    if counts != dataset.cardinalities:
        raise ValueError("Benchmark dataset cardinality drift detected.")
    if counts["orders"] != dataset.profile.order_count:
        raise ValueError("Benchmark order cardinality is incomplete.")
    if dataset.profile.name == "full" and counts["orders"] < 10_000:
        raise ValueError("Full benchmark requires at least 10,000 orders.")
    dates = set(
        session.scalars(
            select(Document.document_date).where(
                Document.tenant_id == dataset.tenant_id, Document.type == "sales_order"
            )
        )
    )
    if dates != {dataset.profile.business_date}:
        raise ValueError("Benchmark orders must share one business date.")
    first_source = session.get(SourceRecord, _id("src", f"b{dataset.profile.seed}", 0))
    first_document = session.get(Document, _id("doc", f"b{dataset.profile.seed}", 0))
    first_line = session.get(DocumentLine, _id("dln", f"b{dataset.profile.seed}", 0))
    first_commitment = session.get(
        Commitment, _id("com", f"b{dataset.profile.seed}", 0)
    )
    if not all((first_source, first_document, first_line, first_commitment)):
        raise ValueError("Benchmark sample trace is incomplete.")
    if (
        hashlib.sha256(first_source.payload.encode()).hexdigest()
        != first_source.payload_hash
    ):
        raise ValueError("Immutable source payload hash does not match.")
    if (
        first_source.version != 1
        or first_document.source_record_id != first_source.id
        or first_line.document_id != first_document.id
        or first_commitment.document_line_id != first_line.id
        or first_commitment.document_id != first_document.id
    ):
        raise ValueError("Source → Evidence → Reality sample links are invalid.")
    balance_rows = session.execute(
        select(
            LedgerEntry.posting_group_id,
            func.sum(
                case(
                    (LedgerEntry.debit_credit == "debit", LedgerEntry.amount),
                    else_=-LedgerEntry.amount,
                )
            ),
        )
        .where(LedgerEntry.tenant_id == dataset.tenant_id)
        .group_by(LedgerEntry.posting_group_id)
    )
    if any(Decimal(balance or 0) != 0 for _, balance in balance_rows):
        raise ValueError("Benchmark ledger posting groups must balance.")
    control_counts = validate_cardinalities(session, dataset.control_tenant_id)
    required_control = (
        "orders",
        "documents",
        "document_lines",
        "commitments",
        "items",
        "reservations",
        "movements",
        "ledger_entries",
        "projection_rows",
    )
    if any(control_counts[name] < 1 for name in required_control):
        raise ValueError("Control tenant must populate every register family.")
    return counts
