"""Executed by the bundled interpreter to write and read the installation's own data."""

from __future__ import annotations

import json
import os
import sys

from reality.db.core import AppUser, Session, engine, init_db
from sqlalchemy import select, text

action = sys.argv[1]
identity = os.environ["REALITY_INSTALLATION_ID"]
Session.configure(info={"desktop_installation_id": identity})

if action == "seed":
    # The same exclusive preparation step the application performs before serving.
    init_db()
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
    init_db()
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
