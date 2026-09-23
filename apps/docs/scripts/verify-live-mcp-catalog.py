"""Compare a redacted deployed MCP tools/list result with generated Tool Usage data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _type(schema: dict[str, Any]) -> str:
    value = schema.get("type")
    if isinstance(value, list):
        value = next((item for item in value if item != "null"), "unknown")
    return str(value or "unknown")


def _flatten(
    schema: dict[str, Any], *, prefix: str = "", required: set[str] | None = None
) -> list[dict[str, Any]]:
    required = required or set(schema.get("required", []))
    rows: list[dict[str, Any]] = []
    for name, field in schema.get("properties", {}).items():
        path = f"{prefix}.{name}" if prefix else name
        kind = _type(field)
        row = {"name": path, "type": kind, "required": name in required}
        if isinstance(field.get("enum"), list):
            row["enum"] = field["enum"]
        rows.append(row)
        if kind == "object":
            rows.extend(
                _flatten(
                    field,
                    prefix=path,
                    required=set(field.get("required", [])),
                )
            )
        elif kind == "array" and isinstance(field.get("items"), dict):
            item = field["items"]
            rows.extend(
                _flatten(
                    item,
                    prefix=f"{path}[]",
                    required=set(item.get("required", [])),
                )
            )
    return rows


def _signature(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            key: row[key]
            for key in ("name", "type", "required", "enum")
            if key in row
        }
        for row in rows
    ]


def compare(tools_payload: dict[str, Any], reference: dict[str, Any]) -> list[str]:
    tools = tools_payload.get("tools") or tools_payload.get("result", {}).get("tools")
    if not isinstance(tools, list):
        raise TypeError("tools/list capture must contain a tools array")
    deployed = {str(tool["name"]): tool for tool in tools}
    generated = {
        str(entry["key"]): entry
        for entry in reference.get("entries", [])
        if entry.get("kind") == "tool"
    }
    errors: list[str] = []
    if set(deployed) != set(generated):
        errors.append(
            "tool names differ: "
            f"missing={sorted(set(generated) - set(deployed))}, "
            f"unexpected={sorted(set(deployed) - set(generated))}"
        )
    for name in sorted(set(deployed) & set(generated)):
        actual = _signature(_flatten(deployed[name].get("inputSchema", {})))
        expected = _signature(generated[name].get("parameters", []))
        if actual != expected:
            errors.append(f"schema differs: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tools_file", type=Path, help="Redacted JSON-RPC tools/list result")
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("apps/docs/.vitepress/data/tool-usage.json"),
    )
    args = parser.parse_args()
    tools_payload = json.loads(args.tools_file.read_text(encoding="utf-8"))
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    errors = compare(tools_payload, reference)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"MCP catalog matches generated reference ({len(tools_payload.get('tools', []))} tools).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
