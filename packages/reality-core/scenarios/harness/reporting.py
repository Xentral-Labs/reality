"""Run-local artifacts, separate from business truth."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def encode(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True, ensure_ascii=False)


class Recorder:
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=False)
        for filename in ("events.jsonl", "checkpoints.jsonl"):
            (directory / filename).touch()

    def write(self, filename: str, payload: dict) -> None:
        (self.directory / filename).write_text(encode(payload) + "\n")

    def append(self, filename: str, payload: dict) -> None:
        with (self.directory / filename).open("a") as stream:
            stream.write(encode({"recorded_at": timestamp(), **payload}) + "\n")

    def finish(self, result: dict) -> None:
        self.write("report.json", result)
        lines = [
            "# Reality rehearsal result",
            "",
            f"Status: **{result['status']}**",
            "",
            f"Run: `{result['run_id']}`",
            f"Company: `{result.get('company_id')}`",
            "",
            f"Scope: {result['scope']}",
            "",
        ]
        if result.get("failure"):
            failure = result["failure"]
            lines += [
                f"First failure: `{failure['event_id']}`",
                "",
                f"Kind: {failure['kind']}",
                "",
            ]
            for difference in failure.get("differences", []):
                lines.append(
                    f"- {difference['path']}: expected {difference['expected']}, actual {difference['actual']}, delta {difference.get('delta')}"
                )
            if failure.get("error_type"):
                lines += [
                    f"Error type: `{failure['error_type']}`; reconcile retained receipts before retrying."
                ]
        if result.get("final"):
            lines += [
                "",
                f"Closing stock: {encode(result['final']['physical'])}",
                "",
                "Coverage: manual-source core replay; no AI operator, external intake or materialized projection verification.",
            ]
        (self.directory / "report.md").write_text("\n".join(lines) + "\n")
