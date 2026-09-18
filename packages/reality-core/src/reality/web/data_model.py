from __future__ import annotations

from typing import Any

import yaml

from reality.config import config_text
from reality.db.core import Base


def _default_text(column: Any) -> str:
    default = column.default
    if default is None:
        return "—"
    value = default.arg
    if callable(value):
        return "generated"
    if isinstance(value, str):
        return value or '""'
    return str(value)


def load_data_model() -> dict[str, Any]:
    """Load the catalog and enrich it with verified SQLAlchemy schema details."""
    catalog = yaml.safe_load(config_text("data_model.yaml"))
    common = catalog.get("common_columns", {})
    documented_tables = catalog["tables"]
    actual_tables = Base.metadata.tables

    missing_tables = set(actual_tables) - set(documented_tables)
    stale_tables = set(documented_tables) - set(actual_tables)
    if missing_tables or stale_tables:
        raise ValueError(
            "Data model catalog table mismatch: "
            f"missing={sorted(missing_tables)}, stale={sorted(stale_tables)}"
        )

    rendered_tables: dict[str, Any] = {}
    for table_name, table_doc in documented_tables.items():
        table = actual_tables[table_name]
        documented_columns = table_doc["columns"]
        actual_column_names = {column.name for column in table.columns}
        missing_columns = actual_column_names - set(documented_columns)
        stale_columns = set(documented_columns) - actual_column_names
        if missing_columns or stale_columns:
            raise ValueError(
                f"Data model catalog column mismatch for {table_name}: "
                f"missing={sorted(missing_columns)}, stale={sorted(stale_columns)}"
            )

        columns = []
        for column in table.columns:
            field_doc = documented_columns[column.name] or {}
            description = field_doc.get("description") or common.get(column.name)
            if not description:
                raise ValueError(f"Missing description for {table_name}.{column.name}")
            foreign_key = next(iter(column.foreign_keys), None)
            keys = []
            if column.primary_key:
                keys.append("Primary key")
            if foreign_key:
                keys.append(f"→ {foreign_key.target_fullname}")
            columns.append(
                {
                    "name": column.name,
                    "type": str(column.type),
                    "required": not column.nullable,
                    "key": " · ".join(keys) or "—",
                    "default": _default_text(column),
                    "description": description,
                }
            )
        rendered_tables[table_name] = {
            "name": table_name,
            "display_name": table_doc.get("display_name", table_name),
            "description": table_doc["description"],
            "columns": columns,
        }

    sections = []
    listed_tables: list[str] = []
    for section in catalog["sections"]:
        listed_tables.extend(section["tables"])
        sections.append(
            {
                **section,
                "tables": [rendered_tables[name] for name in section["tables"]],
            }
        )
    if set(listed_tables) != set(rendered_tables) or len(listed_tables) != len(
        rendered_tables
    ):
        raise ValueError("Every catalog table must occur in exactly one section")

    return {
        "version": catalog["version"],
        "title": catalog["title"],
        "description": catalog["description"],
        "sections": sections,
        "table_count": len(rendered_tables),
        "column_count": sum(
            len(table["columns"]) for table in rendered_tables.values()
        ),
    }
