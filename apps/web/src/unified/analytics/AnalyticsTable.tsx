import type { AnalyticsResult } from "../../api";
import { formatDateTime, formatExactDecimal, t } from "../../localization";

export const labels: Record<string, string> = {
  customer_id: "customer",
  supplier_id: "supplier",
  product_id: "product",
  party_id: "party",
  order_id: "order",
  location_id: "location",
};
export function analyticLabel(label: string) {
  for (const prefix of ["Change (%)", "Change"]) {
    if (label.startsWith(`${prefix} · `))
      return `${t(prefix)} · ${t(label.slice(prefix.length + 3))}`;
  }
  return t(label);
}
export function analyticValue(value: string | number | null | undefined, type: string) {
  if (value === null || value === undefined) return t("Unknown");
  if (type === "decimal" || type === "integer") return formatExactDecimal(value);
  if (type === "datetime") return formatDateTime(String(value));
  return String(value);
}
export function AnalyticsTable({
  result,
  inspect,
}: {
  result: AnalyticsResult;
  inspect: (row: Record<string, string | number | null>, measure: string) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border-default">
      <table className="w-full text-sm">
        <thead className="bg-surface-muted">
          <tr>
            {result.columns.map((column) => (
              <th
                key={column.key}
                className={`whitespace-nowrap px-4 py-3 font-medium ${["decimal", "integer"].includes(column.type) ? "text-right" : "text-left"}`}
              >
                {analyticLabel(column.label)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border-default">
          {result.rows.map((row, index) => (
            <tr key={index} className="hover:bg-surface-muted">
              {result.columns.map((column) => {
                const numeric = ["decimal", "integer"].includes(column.type);
                const value = row[labels[column.key]] ?? row[column.key];
                return (
                  <td
                    key={column.key}
                    data-numeric={numeric}
                    className="px-4 py-3 text-left data-[numeric=true]:text-right data-[numeric=true]:tabular-nums"
                  >
                    {result.executed_definition.measures.includes(column.key) ? (
                      <button
                        className="text-accent underline decoration-dotted underline-offset-4"
                        onClick={() => inspect(row, column.key)}
                        aria-label={`${t("Supporting records")}: ${analyticLabel(column.label)}`}
                      >
                        {analyticValue(value, column.type)}
                      </button>
                    ) : (
                      analyticValue(value, column.type)
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {!result.rows.length && (
        <p className="p-8 text-center text-fg-muted">{t("No matching records")}</p>
      )}
    </div>
  );
}
