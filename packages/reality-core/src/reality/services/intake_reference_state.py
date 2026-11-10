"""Canonical mapped-column reference digest without importing intake execution."""

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.sql.sqltypes import Numeric

from reality.domain.intake import content_digest
from reality.services import core


def mapped_state(record: Any) -> str:
    return content_digest(
        {
            column.key: (
                core.decimal(getattr(record, column.key))
                if isinstance(column.type, Numeric)
                and getattr(record, column.key) is not None
                else getattr(record, column.key)
            )
            for column in inspect(type(record)).columns
        }
    )
