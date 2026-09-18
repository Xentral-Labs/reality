"""Index what sixteen analysis objects share (spec 234, one table, sixteen meanings).

`document` carries sixteen of the sixty-four analysis objects and `document_line`
eight; each tells itself apart by a `where` selector the compiler turns into a
filter. Only `tenant_id` was indexed, so a question about sales orders read every
document of the company and discarded the rest — measured on a 10,233-document
company, 3,438 rows returned and 6,795 removed by the filter on every such read.

The day is the third column because a question that names a type almost always
bounds or groups by the date as well, and after 0063 it is a date that an index
can order. The line index serves the EXISTS the compiler emits for a child object
("only lines whose document is an order"), and every line-to-document join beside it.

`if_not_exists` tolerates an index an operator created by hand under the same name.
The models declare the same indexes, so the test schema and this migration agree.
"""

from alembic import op

revision = "0064_analysis_document_indexes"
down_revision = "0063_document_date_is_a_day"
branch_labels = None
depends_on = None

INDEXES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "ix_document_tenant_type_date",
        "document",
        ("tenant_id", "type", "document_date"),
    ),
    (
        "ix_document_line_tenant_document",
        "document_line",
        ("tenant_id", "document_id"),
    ),
)


def upgrade():
    for name, table, columns in INDEXES:
        op.create_index(name, table, list(columns), if_not_exists=True)


def downgrade():
    for name, table, _ in reversed(INDEXES):
        op.drop_index(name, table_name=table, if_exists=True)
