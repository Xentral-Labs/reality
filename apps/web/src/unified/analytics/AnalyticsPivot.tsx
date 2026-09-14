import type { AnalyticsResult } from "../../api";
import { t } from "../../localization";
import { analyticValue, labels } from "./AnalyticsTable";

export function AnalyticsPivot({
  result,
  inspect,
}: {
  result: AnalyticsResult;
  inspect: (row: Record<string, string | number | null>, measure: string) => void;
}) {
  const pivot = result.pivot;
  if (!pivot) return null;
  const columns = [...new Set(pivot.cells.map((row) => row[pivot.column_dimension]))];
  const matches = (
    cell: Record<string, string | number | null>,
    row: Record<string, string | number | null>,
  ) => pivot.row_dimensions.every((key) => cell[key] === row[key]);
  return (
    <div className="overflow-auto rounded-lg border border-border-default">
      <table className="w-full text-sm">
        <caption className="p-3 text-left text-fg-muted">
          {t("Pivot totals are calculated from the full population.")}
        </caption>
        <thead>
          <tr>
            <th className="p-3 text-left">
              {pivot.row_dimensions
                .map((key) => t(result.columns.find((c) => c.key === key)?.label || key))
                .join(" · ")}
            </th>
            {columns.map((column) => (
              <th key={String(column)} className="p-3 text-right" colSpan={pivot.measures.length}>
                {column ?? t("Unknown")}
              </th>
            ))}
            <th className="p-3 text-right" colSpan={pivot.measures.length}>
              {t("Total")}
            </th>
          </tr>
        </thead>
        <tbody>
          {pivot.row_totals.map((row, i) => (
            <tr key={i} className="border-t border-border-default">
              <th className="p-3 text-left font-normal">
                {pivot.row_dimensions
                  .map((key) => String(row[labels[key]] ?? row[key] ?? t("Unknown")))
                  .join(" · ")}
              </th>
              {columns.flatMap((column) =>
                pivot.measures.map((measure) => {
                  const cell = pivot.cells.find(
                    (candidate) =>
                      matches(candidate, row) && candidate[pivot.column_dimension] === column,
                  );
                  return (
                    <td key={`${column}-${measure}`} className="p-3 text-right tabular-nums">
                      {cell ? (
                        <button
                          className="text-accent underline decoration-dotted"
                          onClick={() => inspect(cell, measure)}
                          title={t(result.columns.find((c) => c.key === measure)?.label || measure)}
                        >
                          {analyticValue(
                            cell[measure],
                            result.columns.find((c) => c.key === measure)!.type,
                          )}
                        </button>
                      ) : (
                        "—"
                      )}
                    </td>
                  );
                }),
              )}
              {pivot.measures.map((measure) => (
                <td key={measure} className="p-3 text-right font-semibold tabular-nums">
                  {analyticValue(row[measure], result.columns.find((c) => c.key === measure)!.type)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
        <tfoot className="border-t border-border-default font-semibold">
          {pivot.totals.map((partition, i) => (
            <tr key={i}>
              <th className="p-3 text-left">
                {t("Total")} · {partition.currency ?? ""} {partition.unit ?? ""}
              </th>
              {columns.flatMap((column) =>
                pivot.measures.map((measure) => {
                  const total = pivot.column_totals.find(
                    (row) =>
                      row[pivot.column_dimension] === column &&
                      ["currency", "unit"].every(
                        (key) => partition[key] === undefined || row[key] === partition[key],
                      ),
                  );
                  return (
                    <td key={`${column}-${measure}`} className="p-3 text-right tabular-nums">
                      {analyticValue(
                        total?.[measure],
                        result.columns.find((c) => c.key === measure)!.type,
                      )}
                    </td>
                  );
                }),
              )}
              {pivot.measures.map((measure) => (
                <td key={measure} className="p-3 text-right tabular-nums">
                  {analyticValue(
                    partition[measure],
                    result.columns.find((c) => c.key === measure)!.type,
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tfoot>
      </table>
    </div>
  );
}
