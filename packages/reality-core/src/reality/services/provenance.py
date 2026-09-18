"""Where a record came from, resolved for a bounded page of records.

Operational tables already carry `source_record_id`, and `SourceRecord` retains
the identity a source delivered under. This module turns that existing chain
into one origin statement, batched per displayed page rather than per row, and
never invents an origin: a record without a source says it was created here.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from urllib.parse import quote, urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    AppUser,
    BusinessEvent,
    ChangeProposal,
    Fact,
    SourceRecord,
    SourceStream,
    SourceSystem,
)

APPLICATION_ORIGIN: dict[str, Any] = {"kind": "application"}


def record_origins(
    session: Session,
    tenant_id: str,
    records: Iterable[Any],
    *,
    subject_type: str,
    with_actor: bool = True,
) -> dict[str, dict[str, Any]]:
    """Resolve one origin per record, in a constant number of statements.

    `records` are rows carrying `id` and `source_record_id`. The returned map is
    keyed by record id; every requested record receives an entry, because a
    blank origin reads as a defect rather than as the absence of a source.
    """
    wanted = {
        record.id: getattr(record, "source_record_id", None) for record in records
    }
    if not wanted:
        return {}
    sources = _sources(
        session, tenant_id, {value for value in wanted.values() if value}
    )
    current = _current_source_records(session, tenant_id, set(sources))
    systems = _systems(
        session, tenant_id, {source.source_system for source in sources.values()}
    )
    manual = [
        record_id for record_id, source_id in wanted.items() if source_id not in sources
    ]
    actors = (
        _deciding_actors(session, tenant_id, subject_type, manual)
        if with_actor and manual
        else {}
    )
    origins: dict[str, dict[str, Any]] = {}
    for record_id, source_id in wanted.items():
        source = sources.get(source_id) if source_id else None
        if source is None:
            actor = actors.get(record_id)
            origins[record_id] = (
                {**APPLICATION_ORIGIN, "actor": actor}
                if actor
                else dict(APPLICATION_ORIGIN)
            )
            continue
        system = systems.get(source.source_system)
        origins[record_id] = {
            "kind": "source",
            "system_code": source.source_system,
            "system_name": system.name if system else source.source_system,
            "source_type": source.source_type,
            "external_id": source.external_id,
            "source_version": source.version,
            "received_at": source.received_at,
            "source_record_id": source.id,
            "superseded": source.id not in current,
            "url": external_link(system, source),
        }
    return origins


def record_origin(
    session: Session, tenant_id: str, record: Any, *, subject_type: str
) -> dict[str, Any]:
    """The single-record form of `record_origins`, for detail reads."""
    return record_origins(session, tenant_id, [record], subject_type=subject_type)[
        record.id
    ]


MAX_BASE_URL = 500


def contributing_systems(
    session: Session,
    tenant_id: str,
    subject_type: str,
    subject_id: str,
    *,
    limit: int = 5,
) -> list[str]:
    """The distinct systems whose observations shaped this record, if several.

    A record's own `source_record_id` names the source that created it, which
    stops being the whole answer once a second system contributes observations.
    One system is the ordinary case and is already stated by the origin, so it is
    not repeated here.
    """
    codes = sorted(
        session.scalars(
            select(SourceRecord.source_system)
            .join(Fact, Fact.source_record_id == SourceRecord.id)
            .where(
                Fact.tenant_id == tenant_id,
                Fact.subject_type == subject_type,
                Fact.subject_id == subject_id,
                SourceRecord.tenant_id == tenant_id,
            )
            .distinct()
            .limit(limit + 1)
        )
    )
    return codes[:limit] if len(codes) > 1 else []


def external_link(system: SourceSystem | None, source: SourceRecord) -> str | None:
    """The record's address in the system that owns it, composed at read time.

    Never stored, and never composed from payload content: the only input beyond
    the tenant's configured base address is the external reference the source
    record already carries. An unconfigured address or an undeclared template
    yields no link rather than a guessed one.
    """
    from reality.integrations.catalog import deep_link_template

    if system is None or not system.base_url or not system.connector_code:
        return None
    if not source.external_id:
        return None
    template = deep_link_template(system.connector_code, source.source_type)
    if not template:
        return None
    base = system.base_url if system.base_url.endswith("/") else f"{system.base_url}/"
    return base + template.replace("{external_id}", quote(source.external_id, safe=""))


def validate_base_url(value: str) -> str:
    """Accept an absolute https address that carries no credentials.

    A base address is configuration a user follows in a browser. Rejecting other
    schemes keeps a stored value from becoming a script or a file target, and
    rejecting user information keeps a password out of a field that is displayed.
    """
    candidate = value.strip()
    if not candidate:
        return ""
    if len(candidate) > MAX_BASE_URL:
        raise ValueError("Base address is too long.")
    parsed = urlparse(candidate)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Base address must be an absolute https address.")
    if "@" in parsed.netloc:
        raise ValueError("Base address must not carry user information.")
    if parsed.query or parsed.fragment:
        raise ValueError("Base address must not carry a query or fragment.")
    return candidate


def _sources(
    session: Session, tenant_id: str, source_ids: set[str]
) -> dict[str, SourceRecord]:
    if not source_ids:
        return {}
    rows = session.scalars(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id, SourceRecord.id.in_(source_ids)
        )
    )
    return {row.id: row for row in rows}


def _current_source_records(
    session: Session, tenant_id: str, source_ids: set[str]
) -> set[str]:
    """Which of these source records a stream still points at as its newest."""
    if not source_ids:
        return set()
    return set(
        session.scalars(
            select(SourceStream.current_source_record_id).where(
                SourceStream.tenant_id == tenant_id,
                SourceStream.current_source_record_id.in_(source_ids),
            )
        )
    )


def _systems(
    session: Session, tenant_id: str, codes: set[str]
) -> dict[str, SourceSystem]:
    """Configured systems keyed by the textual code a source record retained.

    The source record keeps a code, not a foreign key, because evidence must not
    depend on configuration that changes after it arrived. A code with no
    configured system is a supported state, not an error.
    """
    if not codes:
        return {}
    rows = session.scalars(
        select(SourceSystem).where(
            SourceSystem.tenant_id == tenant_id, SourceSystem.code.in_(codes)
        )
    )
    return {row.code: row for row in rows}


def _deciding_actors(
    session: Session, tenant_id: str, subject_type: str, record_ids: list[str]
) -> dict[str, str]:
    """The user who decided the change proposal that first recorded each record."""
    if not record_ids:
        return {}
    creating = dict(
        session.execute(
            select(BusinessEvent.subject_id, BusinessEvent.action_id)
            .distinct(BusinessEvent.subject_id)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.subject_type == subject_type,
                BusinessEvent.subject_id.in_(record_ids),
                BusinessEvent.action_id.is_not(None),
            )
            .order_by(BusinessEvent.subject_id, BusinessEvent.sequence)
        ).all()
    )
    if not creating:
        return {}
    deciders = dict(
        session.execute(
            select(ChangeProposal.id, ChangeProposal.decided_by_user_id).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id.in_(set(creating.values())),
                ChangeProposal.decided_by_user_id.is_not(None),
            )
        ).all()
    )
    if not deciders:
        return {}
    names = {
        row.id: (row.display_name or row.email)
        for row in session.execute(
            select(AppUser.id, AppUser.display_name, AppUser.email).where(
                AppUser.id.in_(set(deciders.values()))
            )
        ).all()
    }
    return {
        record_id: names[deciders[action_id]]
        for record_id, action_id in creating.items()
        if action_id in deciders and deciders[action_id] in names
    }
