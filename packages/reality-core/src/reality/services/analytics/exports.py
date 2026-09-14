"""Bounded CSV from one complete analytical observation."""

import csv
import io

from reality.services.analytics.budget import check_budget
from reality.services.analytics.execution import AnalyticsError, canonical, query


def safe_cell(value, kind):
    if value is None:
        return ""
    value = str(value)
    if kind not in {"decimal", "integer"} and value.lstrip().startswith(
        ("=", "+", "-", "@")
    ):
        return "'" + value
    return value


def export_csv(session, tenant_id, arguments):
    definition = arguments.get("definition")
    result = query(session, tenant_id, {"definition": definition}, all_rows=True)
    if (
        arguments.get("expected_fingerprint")
        and arguments["expected_fingerprint"] != result["definition_fingerprint"]
    ):
        raise AnalyticsError(
            "The export definition changed. Review it before exporting.",
            "invalid_definition",
        )
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    columns = result["columns"]
    writer.writerow(
        [column["key"] for column in columns] + ["observed_at", "definition"]
    )
    context = canonical(result["executed_definition"])
    for row in result["rows"]:
        check_budget()
        writer.writerow(
            [safe_cell(row.get(column["key"]), column["type"]) for column in columns]
            + [result["metadata"]["observed_at"], context]
        )
        if output.tell() > 10 * 1024 * 1024:
            raise AnalyticsError(
                "Export exceeds 10 MiB. Narrow the analysis.", "query_too_broad"
            )
    content = output.getvalue()
    if len(content.encode()) > 10 * 1024 * 1024:
        raise AnalyticsError(
            "Export exceeds 10 MiB. Narrow the analysis.", "query_too_broad"
        )
    return {
        "csv": content,
        "filename": "analysis.csv",
        "row_count": len(result["rows"]),
        "metadata": result["metadata"],
    }
