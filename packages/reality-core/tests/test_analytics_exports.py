"""Exports retain stated decimals and neutralize spreadsheet formula text."""

import csv
import io

from test_analytics_execution import orders, request

from reality.services.analytics.exports import export_csv, safe_cell


def test_export_covers_population_and_includes_context(session, business):
    orders(session, business)
    result = export_csv(
        session,
        business.tenant.id,
        {"definition": request(dimensions=["record_id"])["definition"]},
    )
    rows = list(csv.reader(io.StringIO(result["csv"])))
    assert len(rows) == 3
    assert result["row_count"] == 2
    assert "observed_at" in rows[0]
    assert (
        result["metadata"]["history_scope"] == "matching_interpreted_retained_records"
    )


def test_formula_text_is_data_but_negative_decimal_is_numeric():
    assert safe_cell("=SUM(A1:A9)", "text").startswith("'")
    assert safe_cell("\t=1+1", "text").startswith("'")
    assert safe_cell("-3.25", "decimal") == "-3.25"
