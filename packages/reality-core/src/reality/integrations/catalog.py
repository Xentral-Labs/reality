from __future__ import annotations

from typing import Any

import yaml

from reality.config import config_text


def connector_catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(config_text("connector_catalog.yaml"))
    codes: set[str] = set()
    for connector in catalog.get("connectors", []):
        required = {"code", "name", "category", "capabilities"}
        code = connector.get("code", "")
        if set(connector) != required or code in codes or not connector["capabilities"]:
            raise ValueError(f"Invalid or duplicate connector shell: {code}")
        codes.add(code)
    return catalog


def connector_shell(code: str) -> dict[str, Any]:
    for connector in connector_catalog()["connectors"]:
        if connector["code"] == code:
            return connector
    raise KeyError(code)
