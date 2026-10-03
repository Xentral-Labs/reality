"""Merging duplicate business partners (spec 339).

A merge states that one business partner is a duplicate of another, the
survivor. It is one append-only row, carried by an internal source record that
holds the statement and its reason. Nothing already stated changes: the
duplicate's documents, promises and ledger entries keep naming it, and reads
that answer for the survivor add them at read time. The duplicate becomes
inactive through the existing lifecycle event, so pickers stop offering it,
and intake that still names it lands on the survivor.

There are no chains: a merged partner is merged once and is never a survivor.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Document,
    LedgerEntry,
    Party,
    PartyMerge,
    PartyRole,
    uid,
)
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _require_business_mutation,
    _tenant_record,
    active_party_delivery_hold,
    emit_business_event,
    get_tenant,
    set_master_data_active,
    store_source_record,
)

MERGE_SYSTEM = "internal_party_merge"
MERGE_TOOLS = {"party_merge"}
REASON_LIMIT = 500


def merged_into(session: Session, tenant_id: str, party_id: str) -> str | None:
    """The survivor a party was merged into, or None for a party not merged."""
    return session.scalar(
        select(PartyMerge.surviving_party_id).where(
            PartyMerge.tenant_id == tenant_id,
            PartyMerge.duplicate_party_id == party_id,
        )
    )


def merged_members(
    session: Session, tenant_id: str, party_ids: set[str] | list[str]
) -> dict[str, str]:
    """For these survivors, every duplicate merged into them: duplicate → survivor.

    One query, however many records the duplicates hold.
    """
    ids = set(party_ids)
    if not ids:
        return {}
    return dict(
        session.execute(
            select(PartyMerge.duplicate_party_id, PartyMerge.surviving_party_id).where(
                PartyMerge.tenant_id == tenant_id,
                PartyMerge.surviving_party_id.in_(ids),
            )
        ).all()
    )


def survivors_of(
    session: Session, tenant_id: str, party_ids: set[str] | list[str]
) -> dict[str, str]:
    """For these parties, the merged ones and their survivor: duplicate → survivor."""
    ids = set(party_ids)
    if not ids:
        return {}
    return dict(
        session.execute(
            select(PartyMerge.duplicate_party_id, PartyMerge.surviving_party_id).where(
                PartyMerge.tenant_id == tenant_id,
                PartyMerge.duplicate_party_id.in_(ids),
            )
        ).all()
    )


def _roles(session: Session, tenant_id: str, party_id: str) -> set[str]:
    return set(
        session.scalars(
            select(PartyRole.role).where(
                PartyRole.tenant_id == tenant_id, PartyRole.party_id == party_id
            )
        )
    )


def _party(session: Session, tenant_id: str, party_id: Any) -> Party:
    if not isinstance(party_id, str) or not party_id.strip():
        raise InvalidOperation(code="party_merge_parties_required")
    try:
        return _tenant_record(session, Party, tenant_id, party_id.strip())
    except NotFound:
        raise NotFound(code="party_merge_party_not_found") from None


def validate_party_merge(
    session: Session,
    tenant_id: str,
    duplicate_party_id: Any,
    surviving_party_id: Any,
    reason: Any,
) -> tuple[Party, Party, str]:
    """The two partners and the reason, or the coded refusal that stops the merge."""
    get_tenant(session, tenant_id)
    duplicate = _party(session, tenant_id, duplicate_party_id)
    survivor = _party(session, tenant_id, surviving_party_id)
    text = str(reason or "").strip()
    if not text:
        raise InvalidOperation(code="party_merge_reason_required")
    if len(text) > REASON_LIMIT:
        raise InvalidOperation(code="party_merge_reason_too_long")
    if duplicate.id == survivor.id:
        raise InvalidOperation(code="party_merge_same_party")
    for party in (duplicate, survivor):
        target = merged_into(session, tenant_id, party.id)
        if target:
            name = session.get(Party, (tenant_id, target))
            raise InvalidOperation(
                code="party_merge_already_merged",
                values={"party": party.name, "survivor": name.name if name else target},
            )
    if not survivor.is_active:
        raise InvalidOperation(
            code="party_merge_survivor_inactive", values={"party": survivor.name}
        )
    duplicate_roles = _roles(session, tenant_id, duplicate.id)
    if "company" in duplicate_roles or "company" in _roles(
        session, tenant_id, survivor.id
    ):
        raise InvalidOperation(code="party_merge_company_party")
    missing = sorted(duplicate_roles - _roles(session, tenant_id, survivor.id))
    if missing:
        raise InvalidOperation(
            code="party_merge_roles_missing",
            values={"party": survivor.name, "roles": ", ".join(missing)},
        )
    if active_party_delivery_hold(session, tenant_id, duplicate.id) is not None:
        raise InvalidOperation(
            code="party_merge_hold_open", values={"party": duplicate.name}
        )
    return duplicate, survivor, text


def _history_counts(session: Session, tenant_id: str, party_id: str) -> dict[str, int]:
    documents = session.scalar(
        select(func.count()).where(
            Document.tenant_id == tenant_id, Document.party_id == party_id
        )
    )
    commitments = session.scalar(
        select(func.count()).where(
            Commitment.tenant_id == tenant_id,
            (Commitment.from_party_id == party_id)
            | (Commitment.to_party_id == party_id),
        )
    )
    entries = session.scalar(
        select(func.count()).where(
            LedgerEntry.tenant_id == tenant_id, LedgerEntry.party_id == party_id
        )
    )
    return {
        "documents": int(documents or 0),
        "commitments": int(commitments or 0),
        "ledger_entries": int(entries or 0),
    }


def _summary(session: Session, tenant_id: str, party: Party) -> dict[str, Any]:
    return {
        "id": party.id,
        "name": party.name,
        "accounting_code": party.accounting_code,
        "default_currency": party.default_currency,
        "roles": sorted(_roles(session, tenant_id, party.id)),
        **_history_counts(session, tenant_id, party.id),
    }


def review_party_merge(
    session: Session, tenant_id: str, tool_name: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The arguments a confirmation executes and what the person is shown."""
    if tool_name not in MERGE_TOOLS:
        raise InvalidOperation(code="proposal_tool_not_found")
    duplicate, survivor, reason = validate_party_merge(
        session,
        tenant_id,
        arguments.get("duplicate_party_id"),
        arguments.get("surviving_party_id"),
        arguments.get("reason"),
    )
    return (
        {
            "duplicate_party_id": duplicate.id,
            "surviving_party_id": survivor.id,
            "reason": reason,
        },
        {
            "duplicate": _summary(session, tenant_id, duplicate),
            "survivor": _summary(session, tenant_id, survivor),
            "reason": reason,
            "effect": (
                "The duplicate's history stays as stated and reads under the "
                "survivor; the duplicate becomes inactive."
            ),
        },
    )


def merge_party(
    session: Session,
    tenant_id: str,
    duplicate_party_id: str,
    surviving_party_id: str,
    reason: str,
    *,
    action_id: str | None = None,
) -> PartyMerge:
    """Record that one business partner is a duplicate of another."""
    _require_business_mutation(session, tenant_id, "merge_party")
    duplicate, survivor, text = validate_party_merge(
        session, tenant_id, duplicate_party_id, surviving_party_id, reason
    )
    source, _, _ = store_source_record(
        session,
        tenant_id,
        MERGE_SYSTEM,
        "party_merge",
        duplicate.id,
        {
            "duplicate_party_id": duplicate.id,
            "surviving_party_id": survivor.id,
            "reason": text,
            "statement_id": action_id or uid("stm"),
        },
    )
    # The source identity is locked; a merge confirmed meanwhile is visible now.
    validate_party_merge(session, tenant_id, duplicate.id, survivor.id, text)
    merge = PartyMerge(
        id=uid("pmg"),
        tenant_id=tenant_id,
        duplicate_party_id=duplicate.id,
        surviving_party_id=survivor.id,
        reason=text,
        source_record_id=source.id,
    )
    session.add(merge)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "party.merged",
        "party",
        survivor.id,
        {
            "merge_id": merge.id,
            "duplicate_party_id": duplicate.id,
            "surviving_party_id": survivor.id,
            "reason": text,
        },
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if duplicate.is_active:
        # Commits the merge and the lifecycle change together.
        set_master_data_active(
            session, tenant_id, Party, duplicate.id, False, action_id=action_id
        )
    else:
        session.commit()
    return merge


def _merge_row(merge: PartyMerge, names: dict[str, str]) -> dict[str, Any]:
    return {
        "id": merge.id,
        "duplicate_party_id": merge.duplicate_party_id,
        "duplicate": names.get(merge.duplicate_party_id),
        "surviving_party_id": merge.surviving_party_id,
        "survivor": names.get(merge.surviving_party_id),
        "reason": merge.reason,
        "merged_at": merge.created_at,
        "source_record_id": merge.source_record_id,
    }


def party_merges(
    session: Session, tenant_id: str, *, party_id: str | None = None
) -> list[dict[str, Any]]:
    """The merges of the company, or those one party took part in, newest first."""
    get_tenant(session, tenant_id)
    query = select(PartyMerge).where(PartyMerge.tenant_id == tenant_id)
    if party_id:
        _tenant_record(session, Party, tenant_id, party_id)
        query = query.where(
            (PartyMerge.duplicate_party_id == party_id)
            | (PartyMerge.surviving_party_id == party_id)
        )
    merges = list(
        session.scalars(query.order_by(PartyMerge.created_at.desc(), PartyMerge.id))
    )
    ids = {m.duplicate_party_id for m in merges} | {
        m.surviving_party_id for m in merges
    }
    names = (
        dict(
            session.execute(
                select(Party.id, Party.name).where(
                    Party.tenant_id == tenant_id, Party.id.in_(ids)
                )
            ).all()
        )
        if ids
        else {}
    )
    return [_merge_row(merge, names) for merge in merges]
