"""Stable codes and values for service refusals (spec 286).

The catalog (`config/service_refusals.json`) holds the English wording of every coded
refusal. A refusal raised with a code renders its English sentence from the catalog, so
chat, MCP and stored receipts keep reading English while the web translates the template.
The code identifies the refusal's meaning; the wording may change, the code never does.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache
from typing import Any

CODE = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")
KINDS = frozenset({"text", "term", "number", "amount", "quantity", "date"})
_PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")


def placeholders(template: str) -> list[str]:
    return _PLACEHOLDER.findall(template)


def validate_catalog(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("Service refusal catalog must be version 1")
    entries = payload.get("refusals")
    terms = payload.get("terms", [])
    if not isinstance(entries, dict) or not isinstance(terms, list):
        raise TypeError("Service refusal catalog needs refusals and terms")
    if len(set(terms)) != len(terms) or not all(
        isinstance(term, str) and term for term in terms
    ):
        raise ValueError("Service refusal terms must be unique non-empty strings")
    for code, entry in entries.items():
        if not CODE.fullmatch(code):
            raise ValueError(f"Refusal code {code!r} must be snake_case")
        message = entry.get("message") if isinstance(entry, dict) else None
        if not isinstance(message, str) or not message:
            raise ValueError(f"Refusal {code!r} needs an English message")
        values = entry.get("values", {})
        if set(entry) - {"message", "values"} or not isinstance(values, dict):
            raise ValueError(f"Refusal {code!r} accepts message and values only")
        if sorted(placeholders(message)) != sorted(values):
            raise ValueError(f"Refusal {code!r} placeholders differ from its values")
        if len(placeholders(message)) != len(set(placeholders(message))):
            raise ValueError(f"Refusal {code!r} repeats a placeholder")
        if not set(values.values()) <= KINDS:
            raise ValueError(f"Refusal {code!r} has an unknown value kind")
    return {"version": 1, "refusals": entries, "terms": terms}


@lru_cache(maxsize=1)
def _shipped() -> dict[str, Any]:
    from reality.config import config_text

    return validate_catalog(json.loads(config_text("service_refusals.json")))


def catalog() -> dict[str, Any]:
    return _shipped()


def _strict() -> bool:
    return os.environ.get("REALITY_STRICT_REFUSALS", "0") == "1"


def value_text(value: Any) -> str:
    """A value as the exact string the sentence shows: no rounding, no locale."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def render(code: str, values: dict[str, Any] | None) -> tuple[str, dict[str, str]]:
    """The English sentence for a coded refusal and its values as strings."""
    texts = {name: value_text(value) for name, value in (values or {}).items()}
    entry = catalog()["refusals"].get(code)
    if entry is None:
        if _strict():
            raise ValueError(f"Unknown refusal code {code!r}")
        return code, texts
    declared = entry.get("values", {})
    if set(texts) != set(declared) and _strict():
        raise ValueError(
            f"Refusal {code!r} values {sorted(texts)} differ from {sorted(declared)}"
        )
    terms = set(catalog()["terms"])
    for name, kind in declared.items():
        if kind == "term" and texts.get(name) not in terms and _strict():
            raise ValueError(f"Refusal {code!r} term {texts.get(name)!r} is not listed")
    sentence = _PLACEHOLDER.sub(
        lambda match: texts.get(match.group(1), match.group(0)), entry["message"]
    )
    return sentence, texts


def payload(error: BaseException) -> dict[str, Any] | None:
    """What clients receive beside the English sentence; None for uncoded refusals."""
    code = getattr(error, "code", None)
    if not code or not getattr(error, "coded", False):
        return None
    entry = catalog()["refusals"].get(code)
    if entry is None:
        return None
    kinds = entry.get("values", {})
    values = getattr(error, "values", {}) or {}
    return {
        "code": code,
        "template": entry["message"],
        "values": {
            name: {"value": values[name], "kind": kinds[name]}
            for name in kinds
            if name in values
        },
    }


class RefusalMixin:
    """Code and values for refusals raised outside the service error classes.

    Domain refusals are `ValueError`s; a service that re-raises one passes
    `code=error.code, values=error.values` through unchanged.
    """

    code: str | None = None
    coded = False
    values: dict[str, str]
    template: str | None = None

    def _init_refusal(
        self, message: str | None, code: str | None, values: dict[str, Any] | None
    ) -> str:
        if code is None:
            if values:
                raise TypeError("Refusal values need a refusal code")
            self.values = {}
            return "" if message is None else message
        if message is not None:
            raise TypeError("A coded refusal renders its sentence from the catalog")
        sentence, texts = render(code, values)
        self.code = code
        self.coded = True
        self.values = texts
        entry = catalog()["refusals"].get(code)
        self.template = entry["message"] if entry else None
        return sentence
