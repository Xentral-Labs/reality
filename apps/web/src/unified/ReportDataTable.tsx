import { Fragment, useId, useState } from "react";
import { formatDateTime, formatExactDecimal, t } from "../localization";
import { RegisterTable } from "./RegisterTable";
import { TablePreview } from "./InlinePreview";
import { reportColumns, reportFieldLabel } from "./reportPresentation";
import { useActionDiscovery } from "./ActionLauncher";
import { BlockerGuidance } from "./ResolutionGuidance";
import { reasonText } from "./guidanceActions";

const quantities = new Set([
  "quantity",
  "physical",
  "reserved",
  "available",
  "incoming",
  "open_quantity",
  "fulfilled_quantity",
  "shortage_quantity",
  "open_customer_demand",
  "uncovered_demand",
  "projected",
]);
function valueText(key: string, value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return t(value ? "Yes" : "No");
  if (
    typeof value === "string" &&
    key.endsWith("_at") &&
    /^\d{4}-\d{2}-\d{2}T/.test(value) &&
    Number.isFinite(Date.parse(value))
  )
    return formatDateTime(value);
  if (quantities.has(key) && (typeof value === "string" || typeof value === "number"))
    return formatExactDecimal(value);
  if (Array.isArray(value))
    return value.length ? `${value.length} ${t(value.length === 1 ? "Entry" : "Entries")}` : "—";
  if (typeof value === "object") return t("Show details");
  if (key === "priority" && value === "normal") return t("Normal");
  return String(value);
}
function RecordFields({ row }: { row: Record<string, unknown> }) {
  return (
    <dl
      data-report-record-fields
      className="grid min-w-0 gap-x-6 gap-y-3 sm:grid-cols-2 lg:grid-cols-3"
    >
      {Object.entries(row).map(([key, value]) => (
        <div
          key={key}
          className="min-w-0"
          style={{ gridColumn: value !== null && typeof value === "object" ? "1 / -1" : undefined }}
        >
          <dt className="text-xs text-fg-muted">{t(reportFieldLabel(key))}</dt>
          <dd className="mt-1 break-words text-sm" data-localization="original">
            {value !== null && typeof value === "object" ? (
              <details>
                <summary className="cursor-pointer text-primary">{valueText(key, value)}</summary>
                <div className="mt-3 space-y-4 border-l border-border-default pl-3">
                  {Array.isArray(value) ? (
                    value.map((entry, i) => (
                      <div key={i}>
                        {entry !== null && typeof entry === "object" ? (
                          <RecordFields row={entry as Record<string, unknown>} />
                        ) : (
                          String(entry)
                        )}
                      </div>
                    ))
                  ) : (
                    <RecordFields row={value as Record<string, unknown>} />
                  )}
                </div>
              </details>
            ) : (
              valueText(key, value)
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}
// Spec 279: blocker codes read as words in the table cell.
const blockerKeys = new Set(["blocker_codes", "blocking_reasons", "blocker_type"]);
// Queue rows carry a list of codes; blocker report rows carry one `blocker_type`.
const blockerCodes = (row: Record<string, unknown>): string[] =>
  Array.isArray(row.blocker_codes)
    ? row.blocker_codes.map(String)
    : typeof row.blocker_type === "string"
      ? [row.blocker_type]
      : [];
export function ReportDataTable({ name, rows }: { name: string; rows: Record<string, unknown>[] }) {
  const columns = reportColumns(name, rows);
  const catalog = useActionDiscovery()?.data?.resolution_guidance;
  const [expanded, setExpanded] = useState<number | null>(null);
  const prefix = useId();
  return (
    <div className="[&_.register-filter-chip]:!bg-transparent [&_.register-filter-chip]:!text-fg-muted [&_.register-column-chip]:!bg-transparent [&_.register-column-chip]:!text-fg-muted">
      <RegisterTable
        filterControl={false}
        actionPresentation="labels"
        actionWidth={150}
        cursorView={{
          id: `report:${name}:business-v1`,
          widths: [
            ...columns.map((key) => (key === "party" ? 200 : key === "due_at" ? 190 : 150)),
            150,
          ],
        }}
      >
        <thead>
          <tr>
            {columns.map((key) => (
              <th key={key}>{t(reportFieldLabel(key, name))}</th>
            ))}
            <th>{t("Details")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <Fragment key={index}>
              <tr>
                {columns.map((key) => (
                  <td key={key} data-localization="original">
                    {blockerKeys.has(key) && row[key] && catalog ? (
                      ([] as unknown[])
                        .concat(row[key])
                        .map((code) => reasonText(catalog, String(code)).label)
                        .join(", ") || "—"
                    ) : row[key] !== null &&
                      typeof row[key] === "object" &&
                      (!Array.isArray(row[key]) || (row[key] as unknown[]).length > 0) ? (
                      <button
                        type="button"
                        className="text-primary underline-offset-4 hover:underline"
                        aria-expanded={expanded === index}
                        aria-controls={`${prefix}-${index}`}
                        onClick={() => setExpanded(expanded === index ? null : index)}
                      >
                        {valueText(key, row[key])}
                      </button>
                    ) : (
                      valueText(key, row[key])
                    )}
                  </td>
                ))}
                <td>
                  <button
                    type="button"
                    aria-expanded={expanded === index}
                    aria-controls={`${prefix}-${index}`}
                    onClick={() => setExpanded(expanded === index ? null : index)}
                  >
                    {t("Show details")}
                  </button>
                </td>
              </tr>
              <TablePreview
                id={`${prefix}-${index}`}
                open={expanded === index}
                columns={columns.length + 1}
              >
                {blockerCodes(row).length > 0 && (
                  <BlockerGuidance
                    codes={blockerCodes(row)}
                    commitment={
                      typeof row.commitment_id === "string" ? row.commitment_id : undefined
                    }
                  />
                )}
                <RecordFields row={row} />
                <details className="mt-5 border-t border-border-default pt-3">
                  <summary className="cursor-pointer text-sm text-fg-muted">
                    {t("Technical definition")}
                  </summary>
                  <pre
                    className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-all text-xs"
                    data-localization="original"
                  >
                    {JSON.stringify(row, null, 2)}
                  </pre>
                </details>
              </TablePreview>
            </Fragment>
          ))}
        </tbody>
      </RegisterTable>
    </div>
  );
}
