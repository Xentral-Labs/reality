from __future__ import annotations

from typing import Any

import yaml

from reality.config import config_text

PLACEHOLDER = "{external_id}"


def connector_catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(config_text("connector_catalog.yaml"))
    codes: set[str] = set()
    for connector in catalog.get("connectors", []):
        required = {"code", "name", "category", "capabilities"}
        optional = {"deep_links"}
        code = connector.get("code", "")
        keys = set(connector)
        if (
            not required <= keys
            or keys - required - optional
            or code in codes
            or not connector["capabilities"]
        ):
            raise ValueError(f"Invalid or duplicate connector shell: {code}")
        _validate_deep_links(connector)
        codes.add(code)
    return catalog


def _validate_deep_links(connector: dict[str, Any]) -> None:
    """Templates address declared source types and interpolate nothing else.

    A template that reached payload content would make an outbound address depend
    on data the tenant does not control, so the only placeholder is the external
    reference the source record already carries.
    """
    links = connector.get("deep_links") or {}
    if not isinstance(links, dict):
        raise TypeError(f"Connector deep links must be a mapping: {connector['code']}")
    for source_type, template in links.items():
        unknown = source_type not in connector["capabilities"]
        braces = template.count("{") != template.count(PLACEHOLDER)
        if unknown or not template.strip() or braces or template.startswith("/"):
            raise ValueError(
                f"Invalid deep link for {connector['code']}: {source_type}"
            )


def deep_link_template(connector_code: str, source_type: str) -> str | None:
    """The vendor's relative address for one source type, or None when undeclared."""
    try:
        shell = connector_shell(connector_code)
    except KeyError:
        return None
    return (shell.get("deep_links") or {}).get(source_type)


def connector_shell(code: str) -> dict[str, Any]:
    for connector in connector_catalog()["connectors"]:
        if connector["code"] == code:
            return connector
    raise KeyError(code)
