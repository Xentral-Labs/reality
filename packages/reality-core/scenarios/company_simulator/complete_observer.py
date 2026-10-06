"""Read-only tenant-scoped finance and logistics verification."""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select

from scenarios.company_simulator.complete_world import ROLES, number


def finance_observation(session, tenant_id, world):
    from reality.db.core import (
        Document,
        LedgerEntry,
        SettlementAllocation,
        SourceRecord,
    )
    from reality.services.core import open_invoice_amount

    entries = list(
        session.scalars(select(LedgerEntry).where(LedgerEntry.tenant_id == tenant_id))
    )
    by_id = {e.id: e for e in entries}
    documents = {
        d.id: d
        for d in session.scalars(
            select(Document).where(Document.tenant_id == tenant_id)
        )
    }
    sources = {
        s.id
        for s in session.scalars(
            select(SourceRecord).where(SourceRecord.tenant_id == tenant_id)
        )
    }
    allocations = list(
        session.scalars(
            select(SettlementAllocation).where(
                SettlementAllocation.tenant_id == tenant_id
            )
        )
    )
    accounts = {role: Decimal(0) for role in ROLES}
    groups = defaultdict(Decimal)
    errors = []
    for e in entries:
        signed = e.amount if e.debit_credit == "debit" else -e.amount
        accounts[e.account] = accounts.get(e.account, Decimal(0)) + signed
        groups[e.posting_group_id] += signed
        document = documents.get(e.document_id)
        source_id = e.source_record_id or (
            document.source_record_id if document else None
        )
        if document is None or source_id not in sources or e.currency != "EUR":
            errors.append(f"Unexplained finance lineage/currency: {e.id}")
    for group, balance in groups.items():
        if balance:
            errors.append(f"Unbalanced posting group: {group}")
    expected_ids = set()
    expected_allocation_ids = set()
    for action in world.finance_actions:
        ids = action["entry_ids"]
        expected_ids.update(ids)
        rows = [by_id[i] for i in ids if i in by_id]
        wanted = sorted(
            [
                (action["debit"], "debit", action["amount"]),
                (action["credit"], "credit", action["amount"]),
            ]
        )
        actual = sorted((e.account, e.debit_credit, number(e.amount)) for e in rows)
        if actual != wanted or len({e.posting_group_id for e in rows}) != 1:
            errors.append(f"Wrong exact posting: {action['label']}")
        if action["document_id"] and any(
            e.document_id != action["document_id"] for e in rows
        ):
            errors.append(f"Wrong financial document: {action['label']}")
        for side in ("debit", "credit"):
            key = side + "_account_id"
            if action.get(key) and any(
                e.account_id != action[key] for e in rows if e.debit_credit == side
            ):
                errors.append(f"Wrong exact cash account: {action['label']}")
        if action["party_id"] and any(e.party_id != action["party_id"] for e in rows):
            errors.append(f"Wrong financial counterparty: {action['label']}")
        if action.get("allocation_to"):
            target = world.documents[action["allocation_to"]]["id"]
            matched = [
                a
                for a in allocations
                if a.payment_ledger_entry_id in ids
                and by_id.get(a.invoice_ledger_entry_id)
                and by_id[a.invoice_ledger_entry_id].document_id == target
            ]
            expected_allocation_ids.update(a.id for a in matched)
            if len(matched) != 1 or number(matched[0].amount) != action["amount"]:
                errors.append(f"Wrong exact allocation: {action['label']}")
    if set(by_id) != expected_ids:
        errors.append("Unexpected or missing ledger entries")
    if {a.id for a in allocations} != expected_allocation_ids:
        errors.append("Unexpected or missing settlement allocations")
    result = {
        "accounts": {role: number(value) for role, value in accounts.items()},
        "open_balances": {
            label: number(open_invoice_amount(session, tenant_id, d["id"]))
            for label, d in world.documents.items()
        },
        "errors": errors,
    }

    if hasattr(world, "cash_accounts"):
        result["cash_accounts"] = {
            key: number(
                sum(
                    (
                        e.amount if e.debit_credit == "debit" else -e.amount
                        for e in entries
                        if e.account_id == key
                    ),
                    Decimal(0),
                )
            )
            for key in world.cash_accounts
        }
    if hasattr(world, "held_payments"):
        from reality.services.core import payment_rows

        payments = {
            r["document"].id: number(r["unallocated"])
            for r in payment_rows(session, tenant_id)
        }
        result["unallocated_payments"] = {
            label: payments.get(value["id"], "unknown")
            for label, value in world.held_payments.items()
        }
    return result


def logistics_observation(session, tenant_id, world):
    from reality.db.core import Movement
    from reality.services.shipments import shipment_explain

    shipments = {}
    errors = []
    for request in world.requests.values():
        for shipment in request["shipments"]:
            detail = shipment_explain(session, tenant_id, shipment["id"])
            shipments[shipment["id"]] = {
                "recipient_party_id": detail["recipient_party_id"],
                "address": detail["address"],
                "delivered": detail["observations"]["externally_delivered"],
                "failed": bool(detail["delivery_failure"]),
            }
        if request.get("return_movement_ids"):
            for movement_id in request["return_movement_ids"]:
                movement = session.scalar(
                    select(Movement).where(
                        Movement.tenant_id == tenant_id, Movement.id == movement_id
                    )
                )
                if (
                    movement is None
                    or movement.return_announcement_id != request["return_announced"]
                    or movement.commitment_id != request["commitment_id"]
                ):
                    errors.append(f"Broken original return link: {movement_id}")
    return {"shipments": shipments, "errors": errors}
