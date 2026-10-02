"""PostgreSQL schema support for explicitly registered logical SQL interfaces."""

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CreateIndex, CreateTable, DropTable

from reality.db.core import Base


@compiles(CreateTable, "postgresql")
def _create_table_or_view(element, compiler, **kwargs):
    sql = element.element.info.get("compatibility_view_sql")
    return sql if sql is not None else compiler.visit_create_table(element, **kwargs)


@compiles(CreateIndex, "postgresql")
def _create_physical_index(element, compiler, **kwargs):
    if element.element.table.info.get("compatibility_view_sql"):
        return "SELECT 1"
    return compiler.visit_create_index(element, **kwargs)


@compiles(DropTable, "postgresql")
def _drop_table_or_view(element, compiler, **kwargs):
    if element.element.info.get("compatibility_view_sql"):
        return "DROP VIEW " + element.element.name
    return compiler.visit_drop_table(element, **kwargs)


def include_schema_object(obj, name, type_, reflected, compare_to):
    """Alembic compares stored tables, not declared logical view contracts."""
    table = Base.metadata.tables.get(name)
    return not (
        type_ == "table"
        and table is not None
        and table.info.get("compatibility_view_sql")
    )
