"""Store the document date as a day (spec 234, analysis reads on a real date).

The column held ISO text, so every comparison, ordering and calendar grouping ran
against a string. Analysis declares `document_date` as a calendar date, and the
compiler answered that by rebuilding a date per row out of `substr`, `make_date`
and a validity cascade — correct, unindexable, and paid for on every row of every
time series. A `date` column removes the cascade, lets an index serve a period
filter, and refuses an impossible day at the point of writing.

Text that is not an ISO day becomes NULL. Two shapes reach this: the empty string,
which already meant "no date stated", and free-form period labels that the
exception reader explicitly refused to interpret ("A free-form period label is not
a date. Nothing is invented from it."). Neither carried a day, so neither loses
one. The rollover check is deliberate: `to_date('2026-02-30', ...)` silently
answers 2026-03-02, and inventing a day the source never stated is exactly what
this column is meant to stop.
"""

from alembic import op

revision = "0063_document_date_is_a_day"
down_revision = "0062_graph_report_model_version"
branch_labels = None
depends_on = None

ISO_DAY = r"^\d{4}-\d{2}-\d{2}$"


def upgrade():
    op.execute(
        f"""
        ALTER TABLE document
        ALTER COLUMN document_date DROP DEFAULT,
        ALTER COLUMN document_date TYPE date
        USING CASE
            WHEN document_date ~ '{ISO_DAY}'
             AND to_char(to_date(document_date, 'YYYY-MM-DD'), 'YYYY-MM-DD')
                 = document_date
            THEN to_date(document_date, 'YYYY-MM-DD')
        END,
        ALTER COLUMN document_date DROP NOT NULL
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE document
        ALTER COLUMN document_date TYPE varchar
        USING coalesce(to_char(document_date, 'YYYY-MM-DD'), ''),
        ALTER COLUMN document_date SET DEFAULT '',
        ALTER COLUMN document_date SET NOT NULL
        """
    )
