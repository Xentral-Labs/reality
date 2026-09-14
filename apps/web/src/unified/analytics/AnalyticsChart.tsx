import { useState } from "react";
import type { AnalyticsResult } from "../../api";
import { labels } from "./AnalyticsTable";
import { formatNumber, t } from "../../localization";

export function AnalyticsChart({
  result,
  kind,
}: {
  result: AnalyticsResult;
  kind: "bar" | "line";
}) {
  const [selectedPartition, setSelectedPartition] = useState<string | null>(null);
  const measure = result.executed_definition.measures[0];
  const dimension = result.executed_definition.dimensions.find(
    (key) => !["unit", "currency"].includes(key),
  );
  const partitionKey = (row: AnalyticsResult["rows"][number]) =>
    JSON.stringify([row.currency ?? null, row.unit ?? null]);
  const partitions = [...new Map(result.rows.map((row) => [partitionKey(row), row])).entries()];
  const activePartition = partitions.find(([key]) => key === selectedPartition) ?? partitions[0];
  const partitionRows = result.rows.filter((row) => partitionKey(row) === activePartition?.[0]);
  const rows = partitionRows.slice(0, 50);
  const hasCurrency = result.rows.some((row) => row.currency != null);
  const hasUnit = result.rows.some((row) => row.unit != null);
  const partitionLabel = (row: AnalyticsResult["rows"][number]) =>
    [
      hasCurrency ? String(row.currency ?? t("Unknown")) : null,
      hasUnit ? String(row.unit ?? t("Unknown")) : null,
    ]
      .filter(Boolean)
      .join(" · ");
  if (!dimension)
    return (
      <p className="rounded-lg bg-surface-muted p-4 text-sm">
        {t("Choose a grouping, such as customer or month, and run the analysis again.")}
      </p>
    );
  const values = rows.map((row) => (row[measure] === null ? null : Number(row[measure])));
  const label = (row: (typeof rows)[number] | undefined) =>
    String(row?.[labels[dimension]] ?? row?.[dimension] ?? "");
  const max = Math.max(1, ...values.map((v) => Math.abs(v ?? 0)));
  const width = 760,
    height = 260;
  const x = (i: number) => 65 + (i * 665) / Math.max(1, rows.length - 1);
  const y = (value: number) => 145 - (value / max) * 100;
  return (
    <div className="rounded-lg border border-border-default p-4">
      {partitions.length > 1 && (
        <fieldset className="mb-4">
          <legend className="mb-2 text-sm font-medium">{t("Show in chart")}</legend>
          <div className="flex flex-wrap gap-2">
            {partitions.map(([key, row]) => (
              <button
                key={key}
                type="button"
                className={`br-btn ${key === activePartition?.[0] ? "br-btn-primary" : ""}`}
                aria-pressed={key === activePartition?.[0]}
                onClick={() => setSelectedPartition(key)}
              >
                {partitionLabel(row)}
              </button>
            ))}
          </div>
        </fieldset>
      )}
      <p className="text-sm font-medium">
        {t(result.columns.find((c) => c.key === measure)?.label ?? measure)} ·{" "}
        {activePartition ? partitionLabel(activePartition[1]) : ""}
      </p>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="my-3 w-full"
        role="img"
        aria-label={t("Analysis chart")}
      >
        <title>{t("Analysis chart")}</title>
        {[-1, 0, 1].map((f) => (
          <g key={f}>
            <line
              x1="60"
              x2="735"
              y1={y(max * f)}
              y2={y(max * f)}
              stroke="currentColor"
              opacity=".12"
            />
            <text x="52" y={y(max * f) + 4} textAnchor="end" fontSize="10" fill="currentColor">
              {formatNumber(max * f)}
            </text>
          </g>
        ))}
        {kind === "line" ? (
          <path
            fill="none"
            stroke="var(--color-accent,#6355e8)"
            strokeWidth="3"
            d={values
              .map((v, i) =>
                v === null ? "" : `${i === 0 || values[i - 1] === null ? "M" : "L"}${x(i)},${y(v)}`,
              )
              .join(" ")}
          />
        ) : (
          rows.map((row, i) =>
            values[i] === null ? null : (
              <rect
                key={i}
                x={60 + (i * 675) / Math.max(1, rows.length)}
                y={Math.min(145, y(values[i]!))}
                width={Math.max(2, 675 / Math.max(1, rows.length) - 8)}
                height={Math.abs(y(values[i]!) - 145)}
                rx="3"
                fill="var(--color-accent,#6355e8)"
              >
                <title>{`${label(row)}: ${row[measure]}`}</title>
              </rect>
            ),
          )
        )}
        <text x="60" y="258" fontSize="10" fill="currentColor">
          {label(rows[0])}
        </text>
        <text x="735" y="258" textAnchor="end" fontSize="10" fill="currentColor">
          {label(rows.at(-1))}
        </text>
      </svg>
      <p className="text-xs text-fg-muted">
        {t("Exact values and supporting records are available in the table.")}
        {result.page.has_more || partitionRows.length > 50
          ? ` ${t("Chart shows a limited selection.")}`
          : ""}
      </p>
    </div>
  );
}
