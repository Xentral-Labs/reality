"""Read the engine room (spec 266): what was done to a company's model, live.

Owners only. Every read is scoped to one company. Nothing here is business
authority: stages and labels are derived at read time from the interaction, the
events it committed and the resource catalog, and nothing derived is stored.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from functools import cache
from typing import Any

import yaml
from sqlalchemy import BigInteger, String, and_, column, delete, or_, select, values
from sqlalchemy.orm import Session

from reality.catalogs import RESOURCE_CATALOG_FILE, config_text
from reality.db.core import (
    AppUser,
    BusinessEvent,
    ChangeProposal,
    MCPAccessToken,
    TenantMembership,
    now,
)
from reality.db.interactions import CHANNELS, KINDS, OUTCOMES, Interaction
from reality.services.core import InvalidOperation, NotFound

RETENTION = timedelta(days=7)
#: Rows recorded this recently are returned again with every poll, so an insert that
#: committed after a later cursor from another process is still delivered once.
LATE_COMMIT_WINDOW = timedelta(seconds=5)
LIMIT_MAX = 500
PURGE_BATCH = 5_000

#: The model stages the engine room draws, in reading order.
STAGES = (
    "source",
    "document",
    "fact",
    "commitment",
    "reservation",
    "movement",
    "ledger",
    "master_data",
)
_STAGE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("source", re.compile(r"^(source_|import_job|interpretation)")),
    ("document", re.compile(r"^document")),
    ("fact", re.compile(r"^fact")),
    ("commitment", re.compile(r"^(commitment|return_announcement|supply_assignment)")),
    ("reservation", re.compile(r"^reservation")),
    ("movement", re.compile(r"^(movement|shipment|handling_unit|lot$|serial_unit)")),
    (
        "ledger",
        re.compile(
            r"^(ledger|posting|subledger|settlement|finance|financial_component|"
            r"accounting_target|dunning)"
        ),
    ),
    (
        "master_data",
        re.compile(r"^(party|item$|location|payment_term|price_list|master_data)"),
    ),
)


def stage_of(name: str) -> str | None:
    """The model stage a table or event subject type belongs to, if any."""
    for stage, pattern in _STAGE_PATTERNS:
        if pattern.search(name):
            return stage
    return None


@cache
def _resource_tables() -> tuple[tuple[re.Pattern[str], tuple[str, ...]], ...]:
    payload = yaml.safe_load(config_text(RESOURCE_CATALOG_FILE))
    generic = set(payload.get("generic_tables", ()))
    return tuple(
        (
            re.compile(resource["match"]),
            tuple(
                table for table in resource.get("tables", ()) if table not in generic
            ),
        )
        for resource in payload["resources"]
        if resource.get("match")
    )


def read_stages(
    channel: str, operation: str, choices: dict[str, str] | None = None
) -> list[str]:
    """Stages a tool reads, by the resource catalog's membership rule.

    A declared choice names its stage directly (`family: party` reads master
    data). Web operations are route templates the catalog does not describe; they
    mark no read stage rather than a guessed one.
    """
    if channel == "web":
        return []
    chosen = {stage_of(value) for value in (choices or {}).values()} - {None}
    if chosen:
        return [stage for stage in STAGES if stage in chosen]
    found = {
        stage
        for pattern, tables in _resource_tables()
        if pattern.search(operation)
        for stage in map(stage_of, tables)
        if stage is not None
    }
    return [stage for stage in STAGES if stage in found]


def require_engine_room_access(session: Session, tenant_id: str, user_id: str) -> None:
    """Active owners only; everyone else, a platform admin included, gets not found."""
    role = session.scalar(
        select(TenantMembership.role).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == user_id,
            TenantMembership.status == "active",
        )
    )
    if role != "owner":
        raise NotFound("Company not found.")


def _enumerated(
    values_: list[str] | None, allowed: tuple[str, ...], name: str
) -> list[str]:
    chosen = [value for value in values_ or [] if value]
    unknown = sorted(set(chosen) - set(allowed))
    if unknown:
        raise InvalidOperation(f"Unknown {name}: {', '.join(unknown)}.")
    return chosen


def list_interactions(
    session: Session,
    tenant_id: str,
    *,
    after: int | None = None,
    window_from: datetime | None = None,
    window_to: datetime | None = None,
    channels: list[str] | None = None,
    kinds: list[str] | None = None,
    outcomes: list[str] | None = None,
    actor_user_id: str | None = None,
    mcp_token_id: str | None = None,
    correlation_id: str | None = None,
    subject_type: str | None = None,
    subject_id: str | None = None,
    include_refresh: bool = False,
    exclude_actor_user_id: str | None = None,
    language: str = "en",
    limit: int = 200,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    if after is not None and (window_from is not None or window_to is not None):
        raise InvalidOperation("Use either a cursor or a time window, not both.")
    if (subject_type is None) != (subject_id is None):
        raise InvalidOperation("A subject filter needs both its type and its id.")
    limit = max(1, min(int(limit), LIMIT_MAX))
    moment = as_of or now()
    retention_starts_at = moment - RETENTION
    conditions = [
        Interaction.tenant_id == tenant_id,
        Interaction.recorded_at >= retention_starts_at,
    ]
    if after is not None:
        conditions.append(
            or_(
                Interaction.cursor > after,
                Interaction.recorded_at >= moment - LATE_COMMIT_WINDOW,
            )
        )
    if window_from is not None:
        conditions.append(Interaction.recorded_at >= window_from)
    if window_to is not None:
        conditions.append(Interaction.recorded_at < window_to)
    for field, chosen in (
        (Interaction.channel, _enumerated(channels, CHANNELS, "channel")),
        (Interaction.kind, _enumerated(kinds, KINDS, "kind")),
        (Interaction.outcome, _enumerated(outcomes, OUTCOMES, "outcome")),
    ):
        if chosen:
            conditions.append(field.in_(chosen))
    for field, value in (
        (Interaction.actor_user_id, actor_user_id),
        (Interaction.mcp_token_id, mcp_token_id),
        (Interaction.correlation_id, correlation_id),
    ):
        if value:
            conditions.append(field == value)
    if not include_refresh:
        conditions.append(Interaction.refresh.is_(False))
    if exclude_actor_user_id:
        conditions.append(
            or_(
                Interaction.actor_user_id.is_(None),
                Interaction.actor_user_id != exclude_actor_user_id,
            )
        )
    if subject_type is not None:
        sequences = list(
            session.scalars(
                select(BusinessEvent.sequence).where(
                    BusinessEvent.tenant_id == tenant_id,
                    BusinessEvent.subject_type == subject_type,
                    BusinessEvent.subject_id == subject_id,
                )
            )
        )
        if not sequences:
            conditions.append(Interaction.id.is_(None))
        else:
            conditions.append(
                or_(
                    *(
                        and_(
                            Interaction.event_first_sequence <= sequence,
                            Interaction.event_last_sequence >= sequence,
                        )
                        for sequence in sequences[:500]
                    )
                )
            )
    fetched = list(
        session.scalars(
            select(Interaction)
            .where(*conditions)
            .order_by(Interaction.cursor.desc())
            .limit(limit + 1)
        )
    )
    truncated = len(fetched) > limit
    page = list(reversed(fetched[:limit]))
    if subject_type is not None:
        wanted = set(
            session.scalars(
                select(BusinessEvent.sequence).where(
                    BusinessEvent.tenant_id == tenant_id,
                    BusinessEvent.subject_type == subject_type,
                    BusinessEvent.subject_id == subject_id,
                )
            )
        )
        page = [row for row in page if _covers(row.event_ranges, wanted)]
    return {
        "interactions": _present(session, tenant_id, page, language),
        "cursor": max((row.cursor for row in page), default=after),
        "retention_starts_at": retention_starts_at,
        "truncated": truncated,
    }


def _covers(ranges: list[list[int]] | None, sequences: set[int]) -> bool:
    return any(
        first <= sequence <= last
        for first, last in ranges or ()
        for sequence in sequences
    )


def _written_stages(
    session: Session, tenant_id: str, rows: list[Interaction]
) -> dict[str, list[str]]:
    spans = [
        (row.id, first, last) for row in rows for first, last in row.event_ranges or ()
    ]
    if not spans:
        return {}
    table = values(
        column("interaction_id", String),
        column("first", BigInteger),
        column("last", BigInteger),
        name="spans",
    ).data(spans)
    found: dict[str, set[str]] = {}
    for interaction_id, subject_type in session.execute(
        select(table.c.interaction_id, BusinessEvent.subject_type)
        .join(
            BusinessEvent,
            and_(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.sequence >= table.c.first,
                BusinessEvent.sequence <= table.c.last,
            ),
        )
        .group_by(table.c.interaction_id, BusinessEvent.subject_type)
    ):
        stage = stage_of(subject_type)
        if stage is not None:
            found.setdefault(interaction_id, set()).add(stage)
    return {key: [s for s in STAGES if s in stages] for key, stages in found.items()}


@cache
def _operation_labels() -> dict[str, dict[str, str]]:
    """Tool name -> language -> label, from the MCP registry and catalog labels.

    The German label comes the way the storyline names a tool: MCP name, its
    application tool in the capability guidance, the command label for it.
    """
    from reality.catalogs import load_catalog_labels, runtime_application_catalog
    from reality.mcp.catalog import MCP_TOOL_REGISTRY

    commands = load_catalog_labels()["commands"]
    guidance = runtime_application_catalog().get("capability_guidance") or {}
    labels: dict[str, dict[str, str]] = {}
    for name, definition in MCP_TOOL_REGISTRY.items():
        application = (guidance.get(name) or {}).get("application_tool") or name
        labels[name] = {"en": definition.label, **commands.get(application, {})}
    return labels


def operation_label(channel: str, operation: str, language: str) -> str | None:
    """A reader's name for a tool call; web routes keep their template."""
    if channel == "web":
        return None
    names = _operation_labels().get(operation)
    if not names:
        return None
    return names.get(language) or names.get("en")


def _present(
    session: Session, tenant_id: str, rows: list[Interaction], language: str = "en"
) -> list[dict]:
    user_ids = {row.actor_user_id for row in rows if row.actor_user_id}
    token_ids = {row.mcp_token_id for row in rows if row.mcp_token_id}
    proposal_ids = {row.proposal_id for row in rows if row.proposal_id}
    tokens = (
        {
            token.id: token
            for token in session.scalars(
                select(MCPAccessToken).where(
                    MCPAccessToken.tenant_id == tenant_id,
                    MCPAccessToken.id.in_(token_ids),
                )
            )
        }
        if token_ids
        else {}
    )
    user_ids |= {t.created_by_user_id for t in tokens.values() if t.created_by_user_id}
    users = (
        {
            user.id: user.display_name or user.email
            for user in session.scalars(select(AppUser).where(AppUser.id.in_(user_ids)))
        }
        if user_ids
        else {}
    )
    proposals = (
        {
            proposal.id: proposal
            for proposal in session.scalars(
                select(ChangeProposal).where(
                    ChangeProposal.tenant_id == tenant_id,
                    ChangeProposal.id.in_(proposal_ids),
                )
            )
        }
        if proposal_ids
        else {}
    )
    written = _written_stages(session, tenant_id, rows)
    return [_view(row, users, tokens, proposals, written, language) for row in rows]


def _actor(row: Interaction, users: dict, tokens: dict) -> dict[str, Any] | None:
    if row.mcp_token_id and row.mcp_token_id in tokens:
        token = tokens[row.mcp_token_id]
        issuer = token.created_by_user_id
        return {
            "kind": "mcp_token",
            "id": token.id,
            "label": token.name,
            "issuer": {"id": issuer, "label": users.get(issuer)} if issuer else None,
            "revoked": token.revoked_at is not None,
        }
    if row.actor_user_id:
        return {
            "kind": "user",
            "id": row.actor_user_id,
            "label": users.get(row.actor_user_id),
        }
    if row.job_id:
        return {"kind": "job", "id": row.job_id, "label": row.operation}
    return None


def _view(row, users, tokens, proposals, written, language="en") -> dict[str, Any]:
    proposal = proposals.get(row.proposal_id) if row.proposal_id else None
    count = sum(last - first + 1 for first, last in row.event_ranges or ())
    return {
        "id": row.id,
        "cursor": row.cursor,
        "started_at": row.started_at,
        "recorded_at": row.recorded_at,
        "duration_ms": row.duration_ms,
        "channel": row.channel,
        "kind": row.kind,
        "operation": row.operation,
        "label": operation_label(row.channel, row.operation, language),
        "outcome": row.outcome,
        "error_code": row.error_code,
        "actor": _actor(row, users, tokens),
        "correlation_id": row.correlation_id,
        "proposal": {
            "id": proposal.id,
            "status": proposal.status,
            "type": proposal.type,
        }
        if proposal
        else None,
        "events": {
            "count": count,
            "first_sequence": row.event_first_sequence,
            "last_sequence": row.event_last_sequence,
        },
        "stages": {
            "read": read_stages(
                row.channel, row.operation, (row.summary or {}).get("choices")
            ),
            "written": written.get(row.id, []),
        },
        "summary": row.summary or {},
        "refresh": row.refresh,
    }


def events_of(
    session: Session, tenant_id: str, interaction_id: str
) -> list[BusinessEvent]:
    """The committed business events one interaction caused, in sequence order."""
    row = session.get(Interaction, (tenant_id, interaction_id))
    if row is None:
        raise NotFound("Interaction not found.")
    if not row.event_ranges:
        return []
    return list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                or_(
                    *(
                        BusinessEvent.sequence.between(first, last)
                        for first, last in row.event_ranges
                    )
                ),
            )
            .order_by(BusinessEvent.sequence)
        )
    )


def pulse(
    session: Session, tenant_id: str, exclude_actor_user_id: str | None = None
) -> dict[str, Any]:
    conditions = [Interaction.tenant_id == tenant_id, Interaction.refresh.is_(False)]
    if exclude_actor_user_id:
        conditions.append(
            or_(
                Interaction.actor_user_id.is_(None),
                Interaction.actor_user_id != exclude_actor_user_id,
            )
        )
    latest = session.execute(
        select(Interaction.cursor, Interaction.recorded_at)
        .where(*conditions)
        .order_by(Interaction.cursor.desc())
        .limit(1)
    ).first()
    return {
        "latest_cursor": latest[0] if latest else None,
        "latest_at": latest[1] if latest else None,
    }


def purge_expired(
    session: Session,
    tenant_id: str,
    *,
    as_of: datetime | None = None,
    batch: int = PURGE_BATCH,
    batches: int | None = None,
) -> int:
    """Delete one company's interactions older than the retention, in batches.

    `batches` bounds the work of one call; None removes everything expired.
    """
    cutoff = (as_of or now()) - RETENTION
    removed = 0
    done = 0
    while batches is None or done < batches:
        expired = (
            select(Interaction.id)
            .where(Interaction.tenant_id == tenant_id, Interaction.recorded_at < cutoff)
            .limit(batch)
        )
        result = session.execute(
            delete(Interaction).where(
                Interaction.tenant_id == tenant_id, Interaction.id.in_(expired)
            )
        )
        count = result.rowcount or 0
        removed += count
        done += 1
        if count < batch:
            break
    return removed


#: The windows the live monitor draws, and the width of one point in each.
SERIES_STEPS = {5: 10, 15: 10, 60: 60}


def series(
    session: Session,
    tenant_id: str,
    *,
    minutes: int = 15,
    channels: list[str] | None = None,
    actor_user_id: str | None = None,
    mcp_token_id: str | None = None,
    exclude_actor_user_id: str | None = None,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """Counts per time step for the live monitor's curves, derived at read time.

    Each step says how many interactions each channel made, how many were refused
    or failed, how many wrote events and how many only read, and the median and
    95th percentile of their duration. Quiet steps are zero rather than missing,
    so a curve is flat where nothing happened.
    """
    from sqlalchemy import extract, func

    step = SERIES_STEPS.get(int(minutes))
    if step is None:
        raise InvalidOperation("Choose a window of 5, 15 or 60 minutes.")
    moment = as_of or now()
    end_epoch = int(moment.timestamp()) // step * step + step
    start_epoch = end_epoch - minutes * 60
    conditions = [
        Interaction.tenant_id == tenant_id,
        Interaction.refresh.is_(False),
        Interaction.recorded_at
        >= datetime.fromtimestamp(start_epoch, tz=moment.tzinfo),
        Interaction.recorded_at < datetime.fromtimestamp(end_epoch, tz=moment.tzinfo),
    ]
    chosen = _enumerated(channels, CHANNELS, "channel")
    if chosen:
        conditions.append(Interaction.channel.in_(chosen))
    if actor_user_id:
        conditions.append(Interaction.actor_user_id == actor_user_id)
    if mcp_token_id:
        conditions.append(Interaction.mcp_token_id == mcp_token_id)
    if exclude_actor_user_id:
        conditions.append(
            or_(
                Interaction.actor_user_id.is_(None),
                Interaction.actor_user_id != exclude_actor_user_id,
            )
        )
    bucket = func.floor(extract("epoch", Interaction.recorded_at) / step).label(
        "bucket"
    )
    failed = Interaction.outcome.in_(("refused", "failed"))
    wrote = Interaction.event_first_sequence.is_not(None)
    rows = session.execute(
        select(
            bucket,
            *(
                func.count().filter(Interaction.channel == channel).label(channel)
                for channel in CHANNELS
            ),
            func.count().filter(failed).label("errors"),
            func.count().filter(wrote).label("writes"),
            func.percentile_cont(0.5)
            .within_group(Interaction.duration_ms)
            .label("p50"),
            func.percentile_cont(0.95)
            .within_group(Interaction.duration_ms)
            .label("p95"),
        )
        .where(*conditions)
        .group_by(bucket)
    ).all()
    by_bucket = {int(row.bucket): row for row in rows}
    buckets = []
    for index in range(start_epoch // step, end_epoch // step):
        row = by_bucket.get(index)
        counts = {
            channel: int(getattr(row, channel)) if row else 0 for channel in CHANNELS
        }
        total = sum(counts.values())
        writes = int(row.writes) if row else 0
        buckets.append(
            {
                "at": datetime.fromtimestamp(index * step, tz=moment.tzinfo),
                "channels": counts,
                "total": total,
                "errors": int(row.errors) if row else 0,
                "writes": writes,
                "reads": total - writes,
                "p50_ms": round(row.p50) if row and row.p50 is not None else None,
                "p95_ms": round(row.p95) if row and row.p95 is not None else None,
            }
        )
    return {"minutes": minutes, "step_seconds": step, "buckets": buckets}
