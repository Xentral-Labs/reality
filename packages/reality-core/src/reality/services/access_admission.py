"""Shared deployment admission policy for verified platform accounts."""

from __future__ import annotations

import logging
import os

from sqlalchemy import update
from sqlalchemy.orm import Session

from reality.db.core import AccessAdmissionCounter, now

log = logging.getLogger(__name__)


def automatic_access_limit() -> int | None:
    """Return unlimited for unset/blank; explicit invalid values require review."""
    raw = os.environ.get("REALITY_AUTO_APPROVE_LIMIT", "").strip()
    if not raw:
        return None
    try:
        return max(0, int(raw))
    except ValueError:
        log.warning("Invalid REALITY_AUTO_APPROVE_LIMIT; requiring manual approval")
        return 0


def claim_automatic_access_slot(session: Session) -> bool:
    """Count admission atomically in the caller's verification transaction."""
    limit = automatic_access_limit()
    if limit == 0:
        return False
    statement = update(AccessAdmissionCounter).where(
        AccessAdmissionCounter.id == "automatic"
    )
    if limit is not None:
        statement = statement.where(AccessAdmissionCounter.used_slots < limit)
    claimed = session.execute(
        statement.values(
            used_slots=AccessAdmissionCounter.used_slots + 1,
            updated_at=now(),
        ).returning(AccessAdmissionCounter.used_slots)
    ).scalar_one_or_none()
    return claimed is not None
