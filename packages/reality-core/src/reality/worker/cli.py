"""Worker process entrypoint; never computes new scheduled occurrences."""

import typer

from reality.jobs.commands import JsonOption, job_commands, process, runs

app = typer.Typer(
    help="Consume queued tenant jobs through registered application handlers."
)
app.add_typer(job_commands, name="jobs")
app.add_typer(runs, name="runs")


@app.command()
def once(
    tenant: str | None = None,
    max_runs: int = 10,
    max_seconds: float = 25,
    json_output: JsonOption = False,
):
    process("worker", False, tenant, 5, max_runs, max_seconds, json_output)


@app.command()
def work(
    tenant: str | None = None, poll_seconds: float = 5, json_output: JsonOption = False
):
    process("worker", True, tenant, poll_seconds, 10, 25, json_output)


if __name__ == "__main__":
    app()
