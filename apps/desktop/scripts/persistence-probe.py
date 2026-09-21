"""Executed by the bundled interpreter to write and read the installation's own data."""

from __future__ import annotations

import json
import os
import sys
import time

from reality.db.core import AppUser, Session, engine, init_db
from sqlalchemy import select, text

action = sys.argv[1]
identity = os.environ["REALITY_INSTALLATION_ID"]
Session.configure(info={"desktop_installation_id": identity})


def prepared() -> None:
    """Wait for the application's own exclusive migration step instead of racing it."""
    if os.environ.get("REALITY_PROBE_WAIT") != "1":
        init_db()
        return
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        with engine.connect() as connection:
            ready = connection.execute(
                text(
                    "SELECT to_regclass('public.alembic_version') IS NOT NULL"
                    " AND EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'app_user')"
                )
            ).scalar_one()
        if ready:
            return
        time.sleep(1)
    raise SystemExit("The application did not finish preparing its database")


if action == "seed":
    # The same exclusive preparation step the application performs before serving.
    prepared()
    from reality.services.core import create_tenant
    from reality.services.desktop_identity import bootstrap_owner

    with Session() as session:
        owner = bootstrap_owner(session, identity)
        session.commit()
        owner_id = owner.id
    with Session() as session:
        tenant = create_tenant(session, sys.argv[2])
        tenant_id = tenant.id
    result = {"owner_id": owner_id, "tenant_id": tenant_id}
else:
    prepared()
    from reality.db.core import Tenant

    with Session() as session:
        owner = session.scalar(
            select(AppUser).where(AppUser.email == f"{identity}@desktop.invalid")
        )
        tenants = sorted(
            (item.id, item.name) for item in session.scalars(select(Tenant)).all()
        )
    result = {
        "owner_id": owner.id if owner else None,
        "tenants": tenants,
    }

with engine.connect() as connection:
    result["migration_revision"] = connection.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalar_one()
    result["tcp_listening"] = (
        connection.execute(text("SHOW listen_addresses")).scalar_one() != ""
    )
print(json.dumps(result))
engine.dispose()
