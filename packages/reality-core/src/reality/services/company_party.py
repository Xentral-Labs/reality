"""The company's own business partner, recorded after a person confirms it (spec 289).

A company owns its stock through the business partner with the role `company`. Companies
created before spec 289 may have none; the cost review draft then offers this command. The
name is the company's current name, read by the server when the proposal is made and
reviewed with it, so a caller can never record another name.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, Tenant
from reality.services import core

TOOL = "company_party_record"


def company_party_ids(session: Session, tenant_id: str) -> list[str]:
    from reality.services.cost_review_draft import _company_parties

    return _company_parties(session, tenant_id)


def proposal_arguments(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    """The reviewed intent: the company's current name and the role company."""
    if arguments:
        raise core.InvalidOperation(code="company_party_arguments_unsupported")
    tenant = core._tenant_record(session, Tenant, tenant_id, tenant_id)
    if not _ordinary(session, tenant):
        raise core.InvalidOperation(code="company_party_business_only")
    core._require_business_mutation(session, tenant_id, "create_party")
    if company_party_ids(session, tenant_id):
        raise core.InvalidOperation(code="company_party_exists")
    return {"name": tenant.name, "roles": ["company"]}


def _ordinary(session: Session, tenant: Tenant) -> bool:
    """An ordinary business company that can confirm cost decisions.

    Sandboxes keep no partner of their own (Demo Data connects only to an empty one),
    and demo or practice companies refuse cost decisions, so offering it there helps
    nobody.
    """
    from reality.services.tenant_policy import business_operation_allowed

    return tenant.purpose == "business" and business_operation_allowed(
        session, tenant.id, "execute_cost_change"
    )


def waiting(session: Session, tenant_id: str) -> ChangeProposal | None:
    """The proposal already waiting for confirmation, if any."""
    return session.scalar(
        select(ChangeProposal)
        .where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == f"tool:{TOOL}",
            ChangeProposal.status == "proposed",
        )
        .order_by(ChangeProposal.created_at.desc(), ChangeProposal.id.desc())
        .limit(1)
    )


def offer(session: Session, tenant_id: str) -> dict[str, Any] | None:
    """What the draft offers when the company has no company partner."""
    tenant = core._tenant_record(session, Tenant, tenant_id, tenant_id)
    if not _ordinary(session, tenant):
        return None
    pending = waiting(session, tenant_id)
    if pending is not None:
        return {"proposal_id": pending.id}
    return {"action": TOOL, "name": tenant.name}


def propose_company_party(session: Session, tenant_id: str) -> ChangeProposal:
    """Propose recording the company partner, or return the one already waiting."""
    from reality.tools.application import create_change_proposal

    pending = waiting(session, tenant_id)
    if pending is not None:
        return pending
    return create_change_proposal(session, tenant_id, TOOL, {}, actor_type="user")


def record_company_party(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    *,
    action_id: str | None = None,
) -> dict[str, Any]:
    """Confirmation: record the reviewed partner unless one appeared meanwhile."""
    from reality.services.business_locks import lock_delivery_state

    lock_delivery_state(session, tenant_id)
    if company_party_ids(session, tenant_id):
        raise core.InvalidOperation(code="company_party_exists")
    (party,) = core.create_parties(
        session,
        tenant_id,
        [{"name": arguments["name"], "type": "company", "roles": ["company"]}],
        action_id=action_id,
    )
    return {"records": [{"family": "party", "id": party.id}]}
