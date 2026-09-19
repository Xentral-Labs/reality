"""Executed by the bundled interpreter against the smoke harness's disposable database."""

from __future__ import annotations

import json

from reality.config import config_text
from reality.db.core import engine, init_db
from sqlalchemy import text

# The explicit smoke harness is the release/migration step, never API/worker startup.
init_db()
with engine.connect() as connection:
    revision = connection.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalar_one()
    search_version = connection.execute(
        text("SELECT extversion FROM pg_extension WHERE extname = 'pg_trgm'")
    ).scalar_one()
    listen = connection.execute(text("SHOW listen_addresses")).scalar_one()
    method = connection.execute(text("SHOW unix_socket_permissions")).scalar_one()
    assert listen == "", "PostgreSQL unexpectedly listens on TCP"
    assert method == "0700", "PostgreSQL socket permissions are too broad"
    assert connection.execute(text("SELECT count(*) FROM tenant")).scalar_one() == 0
assert "commands" in config_text("command_catalog.yaml")
# Import the real roles without starting services, bootstrap side effects or jobs.
from reality.scheduler import cli as scheduler_cli
from reality.worker import cli as worker_cli

assert scheduler_cli.app and worker_cli.app
print(
    json.dumps(
        {
            "migration_revision": revision,
            "pg_trgm_version": search_version,
            "tcp_listening": False,
            "tenant_count": 0,
            "catalog_loaded": True,
            "job_roles_imported": True,
        }
    )
)
engine.dispose()
