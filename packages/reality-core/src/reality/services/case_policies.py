"""Resolve committed notification identities back to current accepted Reality."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    Commitment,
    DocumentLine,
    Movement,
    MovementCorrection,
)
from reality.domain.operational_cases import event_disposition
from reality.services import core


def reconcile_event(session: Session, tenant_id: str, event: BusinessEvent) -> None:
    from reality.services.operational_cases import ensure_commitment, ensure_return

    if event.tenant_id != tenant_id:
        raise core.NotFound(code="case_not_found")
    if event_disposition(event.event_type) in {"no_case", "freshness"}:
        return
    if event.subject_type == "commitment":
        ensure_commitment(session, tenant_id, event.subject_id)
    elif event.subject_type == "return_announcement":
        ensure_return(session, tenant_id, event.subject_id)
    elif event.subject_type in {"document", "document_line"}:
        doc_id = event.subject_id
        if event.subject_type == "document_line":
            doc_id = core._tenant_record_read(
                session, DocumentLine, tenant_id, event.subject_id
            ).document_id
        for row in session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id, Commitment.document_id == doc_id
            )
        ):
            ensure_commitment(session, tenant_id, row.id)
    elif event.subject_type in {"movement", "movement_correction"}:
        movement_id = event.subject_id
        if event.subject_type == "movement_correction":
            movement_id = core._tenant_record_read(
                session, MovementCorrection, tenant_id, event.subject_id
            ).original_movement_id
        row = core._tenant_record_read(session, Movement, tenant_id, movement_id)
        if row.return_announcement_id:
            ensure_return(session, tenant_id, row.return_announcement_id)
        elif row.commitment_id:
            ensure_commitment(session, tenant_id, row.commitment_id)
    # Shipment/source notifications need no copied case state: reads and guards
    # derive current evidence; canonical goal producers already ensure membership.
