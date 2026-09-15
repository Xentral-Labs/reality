"""Thin operator commands shared by the two migration-free entrypoints."""

from __future__ import annotations

import json
import logging
from typing import Annotated

import typer

from reality.jobs.registry import JobError, definitions

TenantOption = Annotated[str, typer.Option("--tenant")]
ActorOption = Annotated[str, typer.Option("--actor")]
RequestOption = Annotated[str, typer.Option("--request-id")]
JsonOption = Annotated[bool, typer.Option("--json")]


def emit(value, as_json: bool = False) -> None:
    # Structured output is also readable in an ordinary terminal; never print ORM or
    # exception repr because they can contain input payloads or credentials.
    typer.echo(
        json.dumps(value, default=str, sort_keys=True, indent=None if as_json else 2)
    )


def invoke(operation, as_json: bool = False) -> None:
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session

    from reality.jobs.runtime import database

    engine = None
    try:
        from reality.services import scheduled_jobs as jobs

        engine = database()
        with Session(engine) as session, session.begin():
            value = operation(session, jobs)
            if isinstance(value, (list, dict)):
                result = value
            else:
                result = jobs.describe(value)
        emit(result, as_json)
    except (JobError, ValueError) as error:
        emit(
            {"error": error.code if isinstance(error, JobError) else "invalid_input"},
            as_json,
        )
        raise typer.Exit(2) from None
    except (SQLAlchemyError, RuntimeError):
        emit({"error": "database_unavailable_or_schema_missing"}, as_json)
        raise typer.Exit(1) from None
    finally:
        if engine is not None:
            engine.dispose()


def process(
    role: str,
    continuous: bool,
    tenant: str | None,
    poll_seconds: float,
    max_runs: int,
    max_seconds: float,
    as_json: bool,
) -> None:
    from sqlalchemy.exc import SQLAlchemyError

    from reality import telemetry
    from reality.jobs.runtime import ProcessLoop

    # Each runner reports under its own service name so the scheduler and the
    # worker are separable in Grafana; they fail for different reasons.
    telemetry.configure(f"reality-{role}")

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        value, status = ProcessLoop(role, tenant_id=tenant).run(
            continuous=continuous,
            poll_seconds=poll_seconds,
            max_runs=max_runs,
            max_seconds=max_seconds,
        )
        emit(value, as_json)
    except (JobError, ValueError) as error:
        emit(
            {"error": error.code if isinstance(error, JobError) else "invalid_input"},
            as_json,
        )
        raise typer.Exit(2) from None
    except (SQLAlchemyError, RuntimeError):
        emit({"error": "database_unavailable_or_schema_missing"}, as_json)
        raise typer.Exit(1) from None
    raise typer.Exit(status)


schedules = typer.Typer(help="Create and control explicitly authorized schedules.")
job_commands = typer.Typer(help="Inspect registered jobs or enqueue a manual run.")
runs = typer.Typer(help="Read retained tenant-scoped run outcomes.")


@schedules.command("create")
def create(
    job_type: str,
    tenant: TenantOption,
    actor: ActorOption,
    request_id: RequestOption,
    config_json: str = "{}",
    every_seconds: int | None = None,
    cron: str | None = None,
    json_output: JsonOption = False,
):
    invoke(
        lambda s, j: j.create_schedule(
            s,
            tenant,
            actor,
            job_type,
            json.loads(config_json),
            request_id=request_id,
            interval_seconds=every_seconds,
            cron_expression=cron,
        ),
        json_output,
    )


@schedules.command("preview")
def show_preview(
    schedule_id: str,
    tenant: TenantOption,
    actor: ActorOption,
    json_output: JsonOption = False,
):
    invoke(lambda s, j: j.preview_schedule(s, tenant, actor, schedule_id), json_output)


def _control(action: str):
    def command(
        schedule_id: str,
        tenant: TenantOption,
        actor: ActorOption,
        request_id: RequestOption,
        revision: int,
        json_output: JsonOption = False,
    ):
        invoke(
            lambda s, j: j.control_schedule(
                s, tenant, actor, schedule_id, action, revision, request_id
            ),
            json_output,
        )

    return command


schedules.command("pause")(_control("pause"))
schedules.command("resume")(_control("resume"))


@schedules.command("update")
def update(
    schedule_id: str,
    tenant: TenantOption,
    actor: ActorOption,
    request_id: RequestOption,
    revision: int,
    config_json: str | None = None,
    every_seconds: int | None = None,
    cron: str | None = None,
    new_actor: str | None = None,
    json_output: JsonOption = False,
):
    def operation(s, j):
        changes = {}
        if config_json is not None:
            changes["config"] = json.loads(config_json)
        if every_seconds is not None:
            changes["interval_seconds"] = every_seconds
        if cron is not None:
            changes["cron_expression"] = cron
        if new_actor is not None:
            changes["actor_id"] = new_actor
        return j.control_schedule(
            s, tenant, actor, schedule_id, "update", revision, request_id, changes
        )

    invoke(operation, json_output)


@schedules.command("list")
def list_schedules(
    tenant: TenantOption,
    actor: ActorOption,
    limit: int = 50,
    cursor: str | None = None,
    json_output: JsonOption = False,
):
    invoke(
        lambda s, j: j.list_schedules(s, tenant, actor, limit=limit, cursor=cursor),
        json_output,
    )


@job_commands.command("list")
def list_jobs(json_output: JsonOption = False):
    emit(
        [
            {
                "name": d.name,
                "version": d.version,
                "configuration_schema": d.config_model.model_json_schema(),
                "timeout_seconds": 30,
                "max_attempts": 3,
                "effect_contract": "transaction_bound_database",
                "authorization": "current_handler_policy",
                "idempotency": "stable_run_id_atomic_effect_and_completion",
            }
            for d in definitions().values()
        ],
        json_output,
    )


@job_commands.command("run")
def manual(
    job_type: str,
    tenant: TenantOption,
    actor: ActorOption,
    request_id: RequestOption,
    config_json: str = "{}",
    json_output: JsonOption = False,
):
    invoke(
        lambda s, j: j.create_manual_run(
            s, tenant, actor, job_type, json.loads(config_json), request_id=request_id
        ),
        json_output,
    )


@runs.command("list")
def list_runs(
    tenant: TenantOption,
    actor: ActorOption,
    limit: int = 50,
    cursor: str | None = None,
    schedule: str | None = None,
    json_output: JsonOption = False,
):
    invoke(
        lambda s, j: j.list_runs(
            s, tenant, actor, limit=limit, cursor=cursor, schedule_id=schedule
        ),
        json_output,
    )


@runs.command("show")
def show_run(
    run_id: str,
    tenant: TenantOption,
    actor: ActorOption,
    json_output: JsonOption = False,
):
    invoke(lambda s, j: j.get_run(s, tenant, actor, run_id), json_output)
