from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from typing import Any

import click
import yaml
from typer.main import get_command
from typer.testing import CliRunner

from reality.cli.app import app as cli_app
from reality.config import config_text

ANSI_ESCAPE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
MUTATING_COMMANDS = {
    ("tenant", "create"),
    ("tenant", "use"),
    ("party", "create"),
    ("party", "update"),
    ("party", "deactivate"),
    ("party", "activate"),
    ("party", "delivery-hold"),
    ("party", "release-delivery-hold"),
    ("payment-term", "create"),
    ("payment-term", "deactivate"),
    ("payment-term", "activate"),
    ("pricing", "create-list"),
    ("pricing", "add-tier"),
    ("pricing", "assign-party"),
    ("pricing", "create-group"),
    ("pricing", "add-group-member"),
    ("pricing", "assign-group"),
    ("source", "ingest"),
    ("source", "retry"),
    ("imports", "work"),
    ("item", "create"),
    ("item", "update"),
    ("item", "deactivate"),
    ("item", "activate"),
    ("location", "create"),
    ("location", "update"),
    ("location", "deactivate"),
    ("location", "activate"),
    ("demo",),
    ("scenario", "run"),
    ("finance", "pay-customer"),
    ("finance", "pay-supplier"),
    ("commitment", "hold"),
    ("commitment", "release-hold"),
    ("document", "hold"),
    ("document", "release-holds"),
}


class CliConsoleError(ValueError):
    pass


@dataclass(frozen=True)
class CliCommandDoc:
    command: str
    help: str
    parameters: tuple[CliParameterDoc, ...]


@dataclass(frozen=True)
class CliParameterDoc:
    name: str
    usage: str
    type: str
    required: bool
    default: str
    description: str


@dataclass(frozen=True)
class CliResult:
    command: str
    output: str
    exit_code: int


def clean_terminal_output(value: str) -> str:
    clean = ANSI_ESCAPE.sub("", value)
    lines = [
        line
        for line in clean.splitlines()
        if not line.startswith("INFO  [alembic.runtime.migration]")
    ]
    return "\n".join(lines).strip()


def _parameter_docs(
    command: click.Command, descriptions: dict[str, str]
) -> tuple[CliParameterDoc, ...]:
    result = []
    for parameter in command.params:
        if parameter.name in {"install_completion", "show_completion"}:
            continue
        if isinstance(parameter, click.Option):
            usage = ", ".join([*parameter.opts, *parameter.secondary_opts])
        else:
            usage = parameter.human_readable_name
        default: Any = parameter.default
        result.append(
            CliParameterDoc(
                name=parameter.name,
                usage=usage,
                type=parameter.type.name or str(parameter.type),
                required=parameter.required,
                default="—" if default is None else str(default),
                description=descriptions[parameter.name],
            )
        )
    return tuple(result)


def command_docs() -> list[CliCommandDoc]:
    root = get_command(cli_app)
    runner = CliRunner()
    catalog = yaml.safe_load(config_text("command_catalog.yaml"))
    descriptions = catalog["parameter_descriptions"]

    def help_for(arguments: list[str]) -> str:
        result = runner.invoke(cli_app, [*arguments, "--help"], color=False)
        return clean_terminal_output(result.output)

    docs = [CliCommandDoc("reality", help_for([]), _parameter_docs(root, descriptions))]

    def visit(group, path: list[str]) -> None:
        for name, command in group.commands.items():
            command_path = [*path, name]
            docs.append(
                CliCommandDoc(
                    " ".join(["reality", *command_path]),
                    help_for(command_path),
                    _parameter_docs(command, descriptions),
                )
            )
            if hasattr(command, "commands"):
                visit(command, command_path)

    visit(root, [])
    return docs


def parse_reality_command(command: str) -> list[str]:
    try:
        parts = shlex.split(command)
    except ValueError as error:
        raise CliConsoleError(f"Invalid command: {error}") from error
    if not parts or parts[0] != "reality":
        raise CliConsoleError("Only commands starting with 'reality' are allowed.")
    if len(parts) > 1 and parts[1] in {"web", "mcp"}:
        raise CliConsoleError(
            f"'reality {parts[1]}' cannot be started inside the web terminal."
        )
    return parts[1:]


def command_is_mutating(command: str) -> bool:
    arguments = parse_reality_command(command)
    words = tuple(argument for argument in arguments if not argument.startswith("-"))
    return any(words[: len(prefix)] == prefix for prefix in MUTATING_COMMANDS)


def run_reality_command(command: str) -> CliResult:
    arguments = parse_reality_command(command)
    result = CliRunner().invoke(cli_app, arguments, color=False)
    output = clean_terminal_output(result.output)
    if result.exception and not output:
        output = f"{type(result.exception).__name__}: {result.exception}"
    return CliResult(command=command, output=output, exit_code=result.exit_code)
