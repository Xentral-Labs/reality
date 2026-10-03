"""Bounded whole-file parsing and stable non-authoritative packages (spec 353)."""

import csv
import io
import threading
from dataclasses import dataclass
from typing import Any

from reality.domain.intake import (
    PACKAGE_BYTES,
    PACKAGE_ROWS,
    canonical_json,
    content_digest,
)
from reality.services.core import InvalidOperation

RAW_BYTES = 20 * 1024 * 1024
RAW_ROWS = 5000
# The standard-library CSV field-size setting is process-global. Preserve it while
# parsing a bounded large input, rather than leaving a larger limit behind.
_csv_lock = threading.Lock()


@dataclass(frozen=True)
class FilePackage:
    index: int
    first_row: int
    rows: tuple[dict[str, Any], ...]
    byte_size: int
    digest: str


def partition_rows(rows: list[dict[str, Any]]) -> tuple[FilePackage, ...]:
    """Keep each row intact; constrain both canonical UTF-8 bytes and row count."""
    if not 1 <= len(rows) <= RAW_ROWS:
        raise InvalidOperation(code="intake_file_rows_invalid")
    packages = []
    current = []
    current_size = 2  # Canonical JSON array brackets, including for a single row.
    first_row = 2

    def retain() -> None:
        packages.append(
            FilePackage(
                len(packages),
                first_row,
                tuple(current),
                current_size,
                content_digest(current),
            )
        )

    for number, row in enumerate(rows, 2):
        row_size = len(canonical_json(row).encode("utf-8"))
        if row_size + 2 > PACKAGE_BYTES:
            raise InvalidOperation(code="intake_package_too_large")
        added = row_size + (1 if current else 0)
        if current and (
            len(current) == PACKAGE_ROWS or current_size + added > PACKAGE_BYTES
        ):
            retain()
            current = []
            current_size = 2
            first_row = number
            added = row_size
        current.append(dict(row))
        current_size += added
    retain()
    return tuple(packages)


def package_item_csv(
    content: bytes, mapping: dict[str, str], *, default_unit: str = "pcs"
) -> tuple[FilePackage, ...]:
    """Validate the complete structure and duplicate set before returning packages.

    This produces proposed content only. Database conflicts and semantic field
    validation must still be checked by the reviewed master-data adapter.
    """
    if not content or len(content) > RAW_BYTES:
        raise InvalidOperation(code="intake_file_size_invalid")
    try:
        text = content.decode("utf-8-sig")
        if "\x00" in text:
            raise InvalidOperation(code="item_import_csv_null_character")
        with _csv_lock:
            previous_limit = csv.field_size_limit()
            csv.field_size_limit(RAW_BYTES)
            try:
                try:
                    dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
                except csv.Error:
                    dialect = csv.excel
                reader = csv.reader(
                    io.StringIO(text, newline=""), dialect=dialect, strict=True
                )
                columns = next(reader)
                if (
                    not 1 <= len(columns) <= 50
                    or any(
                        not column.strip() or len(column) > 500 for column in columns
                    )
                    or len({column.strip().lower() for column in columns})
                    != len(columns)
                ):
                    raise InvalidOperation(code="item_import_csv_columns_invalid")
                if (
                    set(mapping) - {"sku", "name", "unit"}
                    or not mapping.get("sku")
                    or not mapping.get("name")
                    or any(column not in columns for column in mapping.values())
                    or len(set(mapping.values())) != len(mapping)
                ):
                    raise InvalidOperation(code="item_import_mapping_columns_invalid")
                if (
                    not isinstance(default_unit, str)
                    or not default_unit.strip()
                    or len(default_unit) > 500
                ):
                    raise InvalidOperation(code="item_import_default_unit_invalid")
                rows = []
                seen = set()
                for number, values in enumerate(reader, 2):
                    if len(values) != len(columns):
                        raise InvalidOperation(
                            code="item_import_row_field_count_mismatch",
                            values={"row": number},
                        )
                    raw = dict(zip(columns, values, strict=True))
                    row = {
                        "sku": raw[mapping["sku"]].strip(),
                        "name": raw[mapping["name"]].strip(),
                        "unit": (
                            raw[mapping["unit"]].strip() if mapping.get("unit") else ""
                        )
                        or default_unit.strip(),
                    }
                    if row["sku"] in seen:
                        raise InvalidOperation(
                            code="item_import_row_duplicate_sku",
                            values={"row": number, "sku": row["sku"]},
                        )
                    seen.add(row["sku"])
                    rows.append(row)
                    if len(rows) > RAW_ROWS:
                        raise InvalidOperation(code="intake_file_rows_invalid")
            finally:
                csv.field_size_limit(previous_limit)
    except (UnicodeError, csv.Error, StopIteration) as error:
        raise InvalidOperation(code="item_import_csv_not_utf8") from error
    return partition_rows(rows)
