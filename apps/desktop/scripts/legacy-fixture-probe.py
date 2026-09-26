"""Create a minimal tenant using the exact core bundled in a prior runtime."""

import json
import sys

from reality.db.core import Session, init_db
from reality.services.core import create_tenant
from sqlalchemy import text


def main() -> None:
    init_db()
    with Session() as session:
        tenant = create_tenant(session, sys.argv[1])
        tenant_id = tenant.id
    with Session() as session:
        revision = session.scalar(text("SELECT version_num FROM alembic_version"))
    print(json.dumps({"tenant_id": tenant_id, "migration_revision": revision}))


if __name__ == "__main__":
    main()
