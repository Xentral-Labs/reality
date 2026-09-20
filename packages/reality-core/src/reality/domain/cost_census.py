"""Canonical observation snapshots: exact received values, no financial authority."""

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

MEMBER_BYTES = 1024 * 1024
CAPTURE_BYTES = 64 * 1024 * 1024


def normalize(value: Any) -> Any:
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Non-finite census decimal.")
        return format(value, "f")
    if isinstance(value, datetime):
        if value.utcoffset() is None:
            raise ValueError("Census timestamps require a timezone.")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict) and all(type(key) is str for key in value):
        return {key: normalize(part) for key, part in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(part) for part in value]
    raise ValueError("Unsupported census snapshot value.")


def canonical(value: Any) -> bytes:
    return json.dumps(
        normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def check_size(value: Any, *, total: int = 0) -> int:
    size = len(canonical(value))
    if size > MEMBER_BYTES or total + size > CAPTURE_BYTES:
        raise ValueError("Census snapshot byte limit exceeded.")
    return total + size
