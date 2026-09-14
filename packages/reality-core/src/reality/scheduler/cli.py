"""Scheduler process entrypoint; never imports the migration-running main CLI."""

import typer

from reality.jobs.commands import JsonOption, process, schedules

app = typer.Typer(
    help="Materialize due tenant jobs in PostgreSQL; never execute handlers."
)
app.add_typer(schedules, name="schedules")


@app.command()
def tick(
    tenant: str | None = None,
    max_runs: int = 100,
    max_seconds: float = 25,
    json_output: JsonOption = False,
):
    process("scheduler", False, tenant, 5, max_runs, max_seconds, json_output)


@app.command()
def work(
    tenant: str | None = None, poll_seconds: float = 5, json_output: JsonOption = False
):
    process("scheduler", True, tenant, poll_seconds, 100, 25, json_output)


if __name__ == "__main__":
    app()
