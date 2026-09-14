"""Serialize delivery capacity validation with mutations in their transaction."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Tenant

# Acquire before reads/row locks in the shared core mutation boundary. Composite
# calls retain the lock until their transaction commits; repeat acquisition is safe.
DELIVERY_WRITERS = frozenset(
    {
        "record_sales_invoice",
        "record_supplier_invoice",
        "record_sales_credit",
        "post_customer_refund",
        "record_customer_refund",
        "create_manual_document_with_lines",
        "post_ledger",
        "post_sales_invoice",
        "post_sales_credit_note",
        "post_supplier_invoice",
        "reserve",
        "release_reservation",
        "record_movement",
        "correct_movement",
        "create_commitment",
        "revise_commitment",
        "cancel_commitment",
        "hold_commitment",
        "release_commitment_hold",
        "hold_document_commitments",
        "release_document_holds",
        "hold_party_delivery",
        "release_party_delivery_hold",
        "correct_manual_document_lines",
        "correct_manual_document",
        "close_stale_promises",
        "create_item",
        "create_items",
        "update_items",
        "update_parties",
        "update_locations",
        "update_item",
        "update_location",
        "update_party",
        "set_master_data_active",
        "archive_tenant",
    }
)


def lock_delivery_state(session: Session, tenant_id: str) -> None:
    from reality.services.core import NotFound

    found = session.scalar(
        select(Tenant.id).where(Tenant.id == tenant_id).with_for_update()
    )
    if found is None:
        raise NotFound("Tenant not found.")
