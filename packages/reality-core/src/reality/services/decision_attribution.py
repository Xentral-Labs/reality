"""Which decision caused a change, and who settled it (spec 263).

A decision is settled in one of three ways that the record can tell apart: by a
signed-in person, through an MCP access token, or by nobody the record can name. This
module states exactly that, for a bounded set of decisions in at most three
statements, and never guesses: a token names the owner who issued it only as its
issuer, because Reality sees the token, not the person at the agent client.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy import select, union
from sqlalchemy.orm import Session

from reality.db.core import AppUser, ChangeProposal, MCPAccessToken

UNKNOWN: dict[str, Any] = {"kind": "unknown"}


def decision_attributions(
    session: Session, tenant_id: str, proposal_ids: Iterable[str | None]
) -> dict[str, dict[str, Any]]:
    """Attribute each requested decision of this company, keyed by its id.

    Ids of another company, or of no decision at all, are absent from the result
    rather than reported, so the reader cannot confirm what another company holds.
    """
    wanted = {proposal_id for proposal_id in proposal_ids if proposal_id}
    if not wanted:
        return {}
    decisions = session.execute(
        select(
            ChangeProposal.id,
            ChangeProposal.type,
            ChangeProposal.status,
            ChangeProposal.decided_at,
            ChangeProposal.decided_by_user_id,
            ChangeProposal.decided_via_token_id,
            MCPAccessToken.name,
            MCPAccessToken.token_prefix,
            MCPAccessToken.revoked_at,
            MCPAccessToken.created_by_user_id,
        )
        .outerjoin(
            MCPAccessToken,
            (MCPAccessToken.tenant_id == ChangeProposal.tenant_id)
            & (MCPAccessToken.id == ChangeProposal.decided_via_token_id),
        )
        .where(ChangeProposal.tenant_id == tenant_id, ChangeProposal.id.in_(wanted))
    ).all()
    names = _names(
        session,
        tenant_id,
        {row.decided_by_user_id for row in decisions if row.decided_by_user_id},
        {row.created_by_user_id for row in decisions if row.created_by_user_id},
    )
    return {
        row.id: {
            "id": row.id,
            "tool": row.type.removeprefix("tool:"),
            "outcome": row.status,
            "decided_at": row.decided_at.isoformat() if row.decided_at else None,
            "decider": _decider(row, names),
        }
        for row in decisions
    }


def _decider(row: Any, names: dict[str, str]) -> dict[str, Any]:
    if row.decided_at is None:
        return dict(UNKNOWN)
    if row.decided_by_user_id and row.decided_by_user_id in names:
        return {"kind": "person", "name": names[row.decided_by_user_id]}
    if row.decided_via_token_id and row.name is not None:
        return {
            "kind": "mcp_token",
            "token_name": row.name,
            "token_prefix": row.token_prefix,
            "revoked": row.revoked_at is not None,
            "issuer": names.get(row.created_by_user_id)
            if row.created_by_user_id
            else None,
        }
    return dict(UNKNOWN)


def _names(
    session: Session, tenant_id: str, deciders: set[str], issuers: set[str]
) -> dict[str, str]:
    """Name only people who decided or issued a token for this company.

    The ids arrive from this company's own rows, so a person is resolved here only
    through a link the company itself holds; the register cannot become a directory.
    """
    wanted = deciders | issuers
    if not wanted:
        return {}
    decided = select(ChangeProposal.decided_by_user_id).where(
        ChangeProposal.tenant_id == tenant_id,
        ChangeProposal.decided_by_user_id.in_(deciders),
    )
    issued = select(MCPAccessToken.created_by_user_id).where(
        MCPAccessToken.tenant_id == tenant_id,
        MCPAccessToken.created_by_user_id.in_(issuers),
    )
    rows = session.execute(
        select(AppUser.id, AppUser.display_name, AppUser.email).where(
            AppUser.id.in_(wanted),
            AppUser.id.in_(union(decided, issued)),
        )
    ).all()
    return {row.id: (row.display_name or "").strip() or row.email for row in rows}


#: How many later decisions a detail view lists beside the creating one.
CHANGE_LIMIT = 10


def record_decisions(
    session: Session, tenant_id: str, kind: str, record_id: str
) -> list[dict[str, Any]]:
    """The decisions behind one record, for its detail view (spec 263 FR-013).

    A business event names the one decision that caused it. Any other record names
    the decision behind its first event as the one that created it, and the latest
    distinct decisions of its later events as the ones that changed it. Nothing is
    listed for a record whose events carry no decision.
    """
    from reality.db.core import BusinessEvent

    if kind == "business_event":
        caused = session.scalar(
            select(BusinessEvent.action_id).where(
                BusinessEvent.tenant_id == tenant_id, BusinessEvent.id == record_id
            )
        )
        roles = [("caused", caused)] if caused else []
    else:
        events = session.execute(
            select(BusinessEvent.action_id)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.subject_type == kind,
                BusinessEvent.subject_id == record_id,
            )
            .order_by(BusinessEvent.sequence)
        ).scalars()
        ordered = list(events)
        creating = ordered[0] if ordered else None
        later: list[str] = []
        for action_id in reversed(ordered[1:]):
            if action_id and action_id != creating and action_id not in later:
                later.append(action_id)
        roles = [("created", creating)] if creating else []
        roles += [("changed", action_id) for action_id in reversed(later[:CHANGE_LIMIT])]
    attributions = decision_attributions(session, tenant_id, [a for _, a in roles])
    return [
        {**attributions[action_id], "role": role}
        for role, action_id in roles
        if action_id in attributions
    ]
