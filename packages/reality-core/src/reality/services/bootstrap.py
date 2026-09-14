from __future__ import annotations

import os

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session as OrmSession

from reality.db.core import Tenant
from reality.services.core import create_tenant, ensure_demo


def bootstrap_empty_database(session: OrmSession) -> Tenant | None:
    """Create the configured first workspace once, and only in an empty database."""
    name = os.environ.get("REALITY_BOOTSTRAP_TENANT_NAME", "").strip()
    if not name:
        return None
    if session.get_bind().dialect.name == "postgresql":
        # Serialize the first-start check when several replicas boot together.
        session.execute(text("SELECT pg_advisory_xact_lock(5245414)"))
    if session.scalar(select(func.count(Tenant.id))) or 0:
        session.rollback()
        return None
    tenant = create_tenant(session, name)
    ensure_demo(session, tenant)
    return tenant
