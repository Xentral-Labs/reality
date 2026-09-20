"""Static experiment adapter to the real shared claim and child watchdog.

Normal product startup never imports this module or accepts its configuration.
"""

import os
import sys
from contextlib import contextmanager
from unittest.mock import patch
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import text

from reality.db.core import AppUser, Base, Tenant
from reality.db.scheduled_jobs import ScheduledJob, ScheduledJobRun
from reality.jobs import registry, runner
from reality.jobs.handlers.projections import authorize
from reality.jobs.registry import JobDefinition, JobResult

from .costing_dataset import VERSION
from .costing_generations import work_generation
from .costing_runner import validate_target


class Configuration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    names: list[str]

    @field_validator("names")
    @classmethod
    def fixed_generation(cls, names):
        if len(names) != 1 or not names[0].startswith("costing:"):
            raise ValueError("One costing generation required.")
        identity = names[0].removeprefix("costing:")
        if UUID(identity).hex != identity:
            raise ValueError("Opaque generation identity required.")
        return names


def initialize_queue(connection):
    """Synthetic queue-control fixtures only, after disposable target validation."""
    connection.execute(text("SET LOCAL search_path TO public"))
    Base.metadata.create_all(
        connection,
        tables=[
            Tenant.__table__,
            AppUser.__table__,
            ScheduledJob.__table__,
            ScheduledJobRun.__table__,
        ],
    )
    connection.execute(
        text("""INSERT INTO public.tenant (id,name,purpose,created_at)
      SELECT id,'Costing worker fixture','playground',clock_timestamp() FROM costing_spike.tenant
      ON CONFLICT(id) DO NOTHING""")
    )


def execute(session, context, config):
    generation = config.names[0].removeprefix("costing:")
    result = work_generation(
        session.connection(), context.tenant_id, generation, deadline=context.deadline
    )
    return JobResult(counts={key: int(value) for key, value in result.items()})


@contextmanager
def registered():
    """Process-local qualification binding, preserving real projection authorization."""
    original = registry.definitions()["projections.refresh"]
    registry._REGISTRY["projections.refresh"] = JobDefinition(
        name="projections.refresh",
        version=1,
        config_model=Configuration,
        authorize=authorize,
        handler=execute,
    )
    try:
        yield
    finally:
        registry._REGISTRY["projections.refresh"] = original


def execute_process(engine, tenant, run, token, *, timeout=30):
    """Use the shared watchdog/settlement with only its static child module substituted."""
    original = runner.subprocess.Popen

    def bootstrap(arguments, **kwargs):
        if arguments[:3] != [sys.executable, "-m", "reality.jobs.runner"]:
            raise ValueError("Unexpected child invocation.")
        return original(
            [
                *arguments[:2],
                "benchmarks.large_tenant_registers.costing_worker",
                *arguments[3:],
            ],
            **kwargs,
        )

    with patch.object(runner.subprocess, "Popen", bootstrap):
        return runner.execute_process(engine, tenant, run, token, timeout=timeout)


def main():
    if len(sys.argv) not in {4, 5}:
        raise SystemExit(2)
    with_info = len(sys.argv) == 5 and sys.argv[4] == "--session-info-stdin"
    if len(sys.argv) == 5 and not with_info:
        raise SystemExit(2)
    url = os.environ.get("REALITY_DATABASE_URL", "")
    validate_target(url, confirmed=True)
    from sqlalchemy import create_engine

    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            if (
                connection.scalar(text("SELECT version FROM costing_spike.manifest"))
                != VERSION
            ):
                raise ValueError("Invalid experiment manifest.")
    finally:
        engine.dispose()
    with registered():
        return runner.child_main(
            *sys.argv[1:4],
            session_info=runner._session_info_from_stdin() if with_info else {},
        )


if __name__ == "__main__":
    raise SystemExit(main())
