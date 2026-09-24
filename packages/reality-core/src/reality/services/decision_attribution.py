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
