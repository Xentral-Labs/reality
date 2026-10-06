"""Independent raw-effect checks for externally operated live companies."""

import hashlib
import json
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select

from reality.db.core import (
    Commitment,
    CommitmentRevision,
    Document,
    DocumentLine,
    LedgerEntry,
    LedgerReversal,
    Movement,
    MovementCorrection,
    Reservation,
    SettlementAllocation,
    SourceRecord,
)
from reality.services import core


def check_effects(session, tenant):
    def rows(model):
        return list(session.scalars(select(model).where(model.tenant_id == tenant)))

    errors = []
    documents = {d.id: d for d in rows(Document)}
    lines = {l.id: l for l in rows(DocumentLine)}
    moves = rows(Movement)
    corrections = {r.original_movement_id for r in rows(MovementCorrection)}
    fulfilled_by_kind = defaultdict(Decimal)
    for movement in moves:
        if movement.id not in corrections:
            fulfilled_by_kind[(movement.commitment_id, movement.type)] += (
                movement.quantity
            )
    actual_terms = core.commitment_terms(session, tenant)
    reserved = defaultdict(Decimal)
    for row in rows(Reservation):
        if row.status == "active":
            reserved[row.commitment_id] += row.quantity
    revisions = {}
    for revision in sorted(rows(CommitmentRevision), key=lambda r: (r.stated_at, r.id)):
        if revision.quantity is not None:
            revisions[revision.commitment_id] = revision.quantity
    source_ids = {d.source_record_id for d in documents.values() if d.source_record_id}
    sources = {
        r.id: r
        for r in session.scalars(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant, SourceRecord.id.in_(source_ids)
            )
        )
    }
    for source in sources.values():
        value = json.loads(source.payload)
        digest = hashlib.sha256(
            json.dumps(
                value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        if digest != source.payload_hash:
            errors.append(
                {
                    "source_record_id": source.id,
                    "reason": "Source payload/hash mismatch",
                }
            )
    for commitment in rows(Commitment):
        document = documents.get(commitment.document_id)
        line = lines.get(commitment.document_line_id)
        if (
            not document
            or not line
            or document.source_record_id not in sources
            or line.document_id != document.id
        ):
            errors.append(
                {
                    "commitment_id": commitment.id,
                    "reason": "Broken source/document/line lineage",
                }
            )
            continue
        quantity = revisions.get(commitment.id, commitment.quantity)
        actual_quantity = actual_terms[commitment.id].quantity
        kind = "shipment" if commitment.type == "customer_delivery" else "receipt"
        fulfilled = fulfilled_by_kind[(commitment.id, kind)]
        actual_fulfilled = actual_terms[commitment.id].fulfilled
        open_quantity = max(Decimal(0), quantity - fulfilled)
        actual_open = actual_terms[commitment.id].open
        if (quantity, fulfilled, open_quantity) != (
            actual_quantity,
            actual_fulfilled,
            actual_open,
        ):
            errors.append(
                {
                    "commitment_id": commitment.id,
                    "reason": "Commitment quantity/fulfilment/open discrepancy",
                    "expected": [str(quantity), str(fulfilled), str(open_quantity)],
                    "actual": [
                        str(actual_quantity),
                        str(actual_fulfilled),
                        str(actual_open),
                    ],
                }
            )
        if (
            reserved[commitment.id] < 0
            or reserved[commitment.id] > open_quantity
            or (commitment.status == "cancelled" and reserved[commitment.id])
        ):
            errors.append(
                {
                    "commitment_id": commitment.id,
                    "reason": "Invalid reservation against obligation",
                }
            )
    entries = rows(LedgerEntry)
    by_id = {e.id: e for e in entries}
    reversed_groups = {r.original_posting_group_id for r in rows(LedgerReversal)}
    used = defaultdict(Decimal)
    for allocation in rows(SettlementAllocation):
        payment = by_id.get(allocation.payment_ledger_entry_id)
        invoice = by_id.get(allocation.invoice_ledger_entry_id)
        if not payment or not invoice:
            errors.append(
                {
                    "allocation_id": allocation.id,
                    "reason": "Missing allocation endpoint",
                }
            )
            continue
        if (
            payment.posting_group_id in reversed_groups
            or invoice.posting_group_id in reversed_groups
        ):
            continue
        if (
            payment.currency != invoice.currency
            or payment.currency != allocation.currency
            or payment.party_id != invoice.party_id
        ):
            errors.append(
                {
                    "allocation_id": allocation.id,
                    "reason": "Allocation party/currency mismatch",
                }
            )
        for entry_id in {payment.id, invoice.id}:
            used[entry_id] += allocation.amount
    for entry_id, amount in used.items():
        if amount < 0 or amount > by_id[entry_id].amount:
            errors.append(
                {
                    "ledger_entry_id": entry_id,
                    "reason": "Allocation exceeds posting amount",
                }
            )
    controls = {
        "sales_invoice": ("accounts_receivable", "debit"),
        "supplier_invoice": ("accounts_payable", "credit"),
        "credit_note": ("accounts_receivable", "credit"),
        "customer_refund": ("accounts_receivable", "debit"),
        "supplier_credit_note": ("accounts_payable", "debit"),
        "supplier_refund": ("accounts_payable", "credit"),
    }
    ledger_by_document = defaultdict(list)
    balances_by_document_account = defaultdict(Decimal)
    for entry in entries:
        ledger_by_document[entry.document_id].append(entry)
        balances_by_document_account[(entry.document_id, entry.account)] += (
            entry.amount if entry.debit_credit == "debit" else -entry.amount
        )
    selected = [d for d in documents.values() if d.type in controls]
    actual_open = core.open_invoice_amounts(session, tenant, selected)
    for document in selected:
        account, side = controls[document.type]
        control = next(
            (
                e
                for e in ledger_by_document[document.id]
                if e.document_id == document.id
                and e.account == account
                and e.debit_credit == side
            ),
            None,
        )
        if control is None:
            continue
        balance = balances_by_document_account[(document.id, account)]
        expected = (
            Decimal(0)
            if control.posting_group_id in reversed_groups
            else (balance if side == "debit" else -balance) - used[control.id]
        )
        if actual_open.get(document.id) != expected:
            errors.append(
                {
                    "document_id": document.id,
                    "reason": "Open-balance/allocation discrepancy",
                    "expected": str(expected),
                    "actual": str(actual_open.get(document.id)),
                }
            )
    for entry in entries:
        doc = documents.get(entry.document_id)
        if not doc or (entry.source_record_id or doc.source_record_id) is None:
            errors.append(
                {"ledger_entry_id": entry.id, "reason": "Missing posting evidence"}
            )
    return errors


def delivery_goals(session, tenant, orders, observed_at):
    """Score original demand against raw current arrival evidence, never dispatch alone."""
    from collections import Counter, defaultdict
    from datetime import datetime, timedelta

    from reality.db.core import (
        BusinessEvent,
        Shipment,
        ShipmentEvent,
        ShipmentEventSupersession,
        ShipmentPackage,
    )

    cancelled = {
        c.document_line_id
        for c in session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant, Commitment.status == "cancelled"
            )
        )
    }
    lines = {
        line.document_id: line
        for line in session.scalars(
            select(DocumentLine).where(DocumentLine.tenant_id == tenant)
        )
    }
    documents = {
        doc.id: doc
        for doc in session.scalars(select(Document).where(Document.tenant_id == tenant))
    }
    commitments = {
        c.id: c
        for c in session.scalars(
            select(Commitment).where(Commitment.tenant_id == tenant)
        )
    }
    shipments = {
        s.id: s
        for s in session.scalars(
            select(Shipment).where(
                Shipment.tenant_id == tenant,
                Shipment.direction == "outbound",
                Shipment.purpose == "customer_delivery",
            )
        )
    }
    packages = {
        p.id: p
        for p in session.scalars(
            select(ShipmentPackage).where(ShipmentPackage.tenant_id == tenant)
        )
    }
    notices = {
        subject: json.loads(payload)
        for subject, payload in session.execute(
            select(BusinessEvent.subject_id, BusinessEvent.payload).where(
                BusinessEvent.tenant_id == tenant,
                BusinessEvent.event_type == "shipment.notice_recorded",
            )
        )
    }
    superseded = set(
        session.scalars(
            select(ShipmentEventSupersession.superseded_event_id).where(
                ShipmentEventSupersession.tenant_id == tenant
            )
        )
    )
    arrival_by_package = defaultdict(list)
    arrival_by_shipment = defaultdict(list)
    for event in session.scalars(
        select(ShipmentEvent).where(
            ShipmentEvent.tenant_id == tenant, ShipmentEvent.event_type == "delivered"
        )
    ):
        if event.id not in superseded and event.occurred_at:
            if event.shipment_package_id:
                arrival_by_package[event.shipment_package_id].append(event.occurred_at)
            else:
                arrival_by_shipment[event.shipment_id].append(event.occurred_at)
    corrected = set(
        session.scalars(
            select(MovementCorrection.original_movement_id).where(
                MovementCorrection.tenant_id == tenant
            )
        )
    )
    by_document = defaultdict(list)
    for movement in session.scalars(
        select(Movement).where(
            Movement.tenant_id == tenant, Movement.type == "shipment"
        )
    ):
        commitment = commitments.get(movement.commitment_id)
        if not commitment or movement.id in corrected:
            continue
        # Index by the existing line relation, not by a human document number.
        by_document[commitment.document_line_id].append(movement)
    counts = Counter()
    for order in orders:
        if order["kind"] != "order":
            continue
        doc = documents.get(order["document_id"])
        line = lines.get(order["document_id"])
        if not doc or not line:
            counts["unrecorded"] += 1
            continue
        delivered = Decimal(0)
        timely = Decimal(0)
        wrong_context = False
        deadline = datetime.fromisoformat(order["released_at"]) + timedelta(hours=2)
        for movement in by_document[line.id]:
            package = packages.get(movement.shipment_package_id)
            shipment = shipments.get(package.shipment_id) if package else None
            if not shipment:
                continue
            times = (
                arrival_by_package[movement.shipment_package_id]
                + arrival_by_shipment[shipment.id]
            )
            if not times:
                continue
            notice = notices.get(shipment.id, {})
            address = notice.get("address") or {}
            expected = order["destination"]
            matches = (
                shipment.counterparty_id == order["party_id"]
                and notice.get("recipient_party_id") == order["party_id"]
                and movement.item_id == order["item_id"]
                and all(address.get(k) == v for k, v in expected.items())
            )
            if not matches:
                wrong_context = True
                continue
            delivered += movement.quantity
            if min(times) <= deadline:
                timely += movement.quantity
        required = Decimal(str(order["quantity"]))
        status = (
            "met"
            if timely >= required
            else "late"
            if delivered >= required
            else "wrong_recipient_or_destination"
            if wrong_context
            else "cancelled"
            if line.id in cancelled
            else "overdue"
            if observed_at > deadline
            else "pending"
        )
        counts[status] += 1
    return dict(counts)
