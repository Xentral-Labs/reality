import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { workspaceApi, type Insights } from "../api";
import { formatDateTime, formatNumber, t } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { Inspector } from "./Inspector";
import { RegisterHeader } from "./RegisterWorkbench";
import { AnalyticsExplorer } from "./analytics/AnalyticsExplorer";
import { ReportLibrary } from "./analytics/ReportLibrary";
import type { AnalyticsReport } from "../api";
import type { Selection } from "./routing";

const labels = {
  open: "Open deliveries",
  fully_reserved: "Fully reserved",
  needs_reservation: "Needs reservation",
  overdue: "Overdue deliveries",
  unknown_due: "Without due date",
  created: "Delivery commitments created",
  shipped: "Shipment movements",
};
const panel = "rounded-xl border border-border-default bg-surface p-6";
export function AnalyticsPreview({
  tenant,
  navigate,
}: {
  tenant: string;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const read = useRead(() => workspaceApi.insights(tenant, 7), [tenant]);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  const position = read.data.position;
  return (
    <section className={panel}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-accent">{t("Analytics")}</p>
          <h2 className="mt-2 text-xl font-semibold text-fg-strong">
            {t("How your operations are moving")}
          </h2>
        </div>
        <button
          className="br-btn"
          onClick={() =>
            navigate({
              route: "analytics",
              analyticsView: "overview",
              page: 1,
              metric: "open",
              day: "",
            })
          }
        >
          {t("Open analytics")}
          <ArrowRight size={16} />
        </button>
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        {(
          [
            ["fully_reserved", position.fully_reserved],
            ["needs_reservation", position.needs_reservation],
            ["overdue", position.overdue],
          ] as const
        ).map(([metric, value]) => (
          <button
            key={metric}
            className="rounded-lg bg-surface-muted p-4 text-left"
            onClick={() =>
              navigate({ route: "analytics", analyticsView: "overview", metric, day: "", page: 1 })
            }
          >
            <span className="text-sm text-fg-muted">{t(labels[metric])}</span>
            <strong className="mt-2 block text-2xl text-fg-strong">{formatNumber(value)}</strong>
          </button>
        ))}
      </div>
    </section>
  );
}
function ActivityChart({ data }: { data: Insights }) {
  const max = Math.max(1, ...data.series.flatMap((row) => [row.created, row.shipped]));
  const points = (key: "created" | "shipped") =>
    data.series
      .map(
        (row, i) =>
          `${30 + (i * 840) / Math.max(1, data.series.length - 1)},${195 - (row[key] * 165) / max}`,
      )
      .join(" ");
  return (
    <svg
      viewBox="0 0 900 235"
      role="img"
      aria-label={t("Recorded activity over time")}
      className="my-5 w-full"
    >
      <title>{t("Delivery commitments created and shipment movements")}</title>
      {[0, 0.5, 1].map((f) => (
        <g key={f}>
          <line
            x1="30"
            x2="870"
            y1={195 - f * 165}
            y2={195 - f * 165}
            stroke="currentColor"
            opacity=".12"
            strokeDasharray="5 5"
          />
          <text x="2" y={199 - f * 165} fontSize="11" fill="currentColor">
            {formatNumber(max * f)}
          </text>
        </g>
      ))}
      <polyline
        points={points("created")}
        fill="none"
        stroke="var(--color-accent, #6254f5)"
        strokeWidth="3"
      />
      <polyline points={points("shipped")} fill="none" stroke="#46a97c" strokeWidth="3" />
      {[data.series[0], data.series[data.series.length - 1]].map((row, i) => (
        <text
          key={i}
          x={i ? 870 : 30}
          y="226"
          textAnchor={i ? "end" : "start"}
          fontSize="12"
          fill="currentColor"
        >
          {row.date}
        </text>
      ))}
    </svg>
  );
}
function AnalyticsOverview({
  selection,
  navigate,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const { tenant, days, metric, day, page } = selection;
  const read = useRead(() => workspaceApi.insights(tenant, days), [tenant, days]);
  const records = useRead(
    () => workspaceApi.contributors(tenant, metric, days, day, page),
    [tenant, metric, days, day, page],
  );
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  const data = read.data;
  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {(["open", "fully_reserved", "needs_reservation", "overdue"] as const).map((key) => (
          <button
            key={key}
            aria-pressed={metric === key}
            className={`${panel} text-left aria-pressed:border-accent aria-pressed:bg-accent-soft`}
            onClick={() => navigate({ metric: key, day: "", page: 1 })}
          >
            <p className="text-sm text-fg-muted">{t(labels[key])}</p>
            <strong className="mt-4 block text-3xl text-fg-strong">
              {formatNumber(data.position[key])}
            </strong>
            <p className="mt-3 text-xs text-fg-muted">
              {key === "fully_reserved"
                ? data.position.coverage_percent === null
                  ? t("No open deliveries to measure")
                  : `${formatNumber(Number(data.position.coverage_percent))}% · ${t("of open deliveries")}`
                : t("Current position · view records")}
            </p>
          </button>
        ))}
      </div>
      <section className={panel}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-fg-strong">{t("Recorded activity")}</h2>
            <p className="mt-2 text-sm text-fg-muted">
              {t("Counts of commitments and movements · UTC days")}
            </p>
          </div>
          <div className="flex gap-2" aria-label={t("Period")}>
            {([7, 30, 90] as const).map((value) => (
              <button
                key={value}
                className="br-btn aria-pressed:border-accent aria-pressed:bg-accent-soft"
                aria-pressed={days === value}
                onClick={() => navigate({ days: value, day: "", page: 1 })}
              >
                {value} {t("days")}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-5 text-sm">
          <span className="text-accent">● {t(labels.created)}</span>
          <span className="text-positive-text">● {t(labels.shipped)}</span>
        </div>
        <ActivityChart data={data} />
        <div className="rounded-lg bg-surface-muted p-4 text-sm text-fg-muted">
          {t(
            "These series count different records, not order conversion. Corrections are reflected in shipment counts. External history may be incomplete.",
          )}
        </div>
        <details className="mt-5">
          <summary className="cursor-pointer text-sm font-medium">
            {t("Daily values and supporting records")}
          </summary>
          <div className="mt-3 max-h-72 overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className="p-2 text-left">{t("Date (UTC)")}</th>
                  <th className="p-2 text-right">{t(labels.created)}</th>
                  <th className="p-2 text-right">{t(labels.shipped)}</th>
                </tr>
              </thead>
              <tbody>
                {data.series.map((row) => (
                  <tr key={row.date} className="border-t border-border-default">
                    <td className="p-2">{row.date}</td>
                    {(["created", "shipped"] as const).map((key) => (
                      <td key={key} className="p-2 text-right">
                        <button
                          className="br-btn"
                          aria-label={`${t(labels[key])} ${row.date}: ${row[key]}`}
                          onClick={() => navigate({ metric: key, day: row.date, page: 1 })}
                        >
                          {formatNumber(row[key])}
                        </button>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </section>
      <section className={panel}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-fg-strong">{t("Supporting records")}</h2>
            <p className="mt-2 text-sm text-fg-muted">
              {t(labels[metric])}
              {day ? ` · ${day} UTC` : ""}
            </p>
          </div>
          <button
            className="br-btn"
            onClick={() => navigate({ metric: "unknown_due", day: "", page: 1 })}
          >
            {t("Without due date")} · {formatNumber(data.position.unknown_due)}
          </button>
        </div>
        {!records.data ? (
          <ReadState loading={records.loading} error={records.error} retry={records.refresh} />
        ) : (
          <>
            <p className="my-4 text-sm text-fg-muted">
              {formatNumber(records.data.page.total)} {t("records")}
            </p>
            <div className="divide-y divide-border-default">
              {records.data.items.map((row) => (
                <button
                  key={row.id}
                  className="flex w-full flex-wrap items-center justify-between gap-3 py-3 text-left"
                  onClick={() =>
                    row.kind === "commitment"
                      ? navigate({
                          route: "orders-deliveries",
                          ordersView: "deliveries",
                          commitment: row.id,
                          proposal: "",
                        })
                      : setTarget(row)
                  }
                >
                  <span className="min-w-0">
                    <strong className="block text-sm">{row.label || row.id}</strong>
                    <span className="break-all font-mono text-xs text-fg-muted">{row.id}</span>
                  </span>
                  <span className="text-sm text-fg-muted">{formatDateTime(row.at)}</span>
                  <ArrowRight size={16} />
                </button>
              ))}
            </div>
            {!records.data.items.length && <p className="py-4">{t("No matching records")}</p>}
            <div className="mt-4 flex items-center gap-3">
              <button
                className="br-btn"
                disabled={!records.data.page.has_previous}
                onClick={() => navigate({ page: records.data!.page.number - 1 })}
              >
                {t("Previous")}
              </button>
              <span>
                {records.data.page.number} / {records.data.page.pages}
              </span>
              <button
                className="br-btn"
                disabled={!records.data.page.has_next}
                onClick={() => navigate({ page: records.data!.page.number + 1 })}
              >
                {t("Next")}
              </button>
            </div>
          </>
        )}
      </section>
      <p className="text-xs text-fg-muted">
        {t("Observed at")} {formatDateTime(data.observed_at)}
      </p>
      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </div>
  );
}

export function AnalyticsPage(props: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const { selection } = props;
  return <AnalyticsWorkspace key={selection.tenant} {...props} />;
}
function AnalyticsWorkspace({
  selection,
  navigate,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const [report, setReport] = useState<AnalyticsReport | null>(null);
  const view = selection.analyticsView || "overview";
  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <RegisterHeader title="Reports">
        <nav className="register-tabs" aria-label={t("Analytics views")}>
          {(
            [
              ["overview", "Overview"],
              ["explore", "Explore"],
              ["reports", "My reports"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              className="br-btn"
              aria-pressed={view === key}
              onClick={() => navigate({ analyticsView: key, page: 1 })}
            >
              {t(label)}
            </button>
          ))}
        </nav>
      </RegisterHeader>
      {view === "overview" && <AnalyticsOverview selection={selection} navigate={navigate} />}
      <div hidden={view !== "explore"}>
        <AnalyticsExplorer tenant={selection.tenant} report={report} onSaved={setReport} />
      </div>
      {view === "reports" && (
        <ReportLibrary
          tenant={selection.tenant}
          open={(value) => {
            setReport(value);
            navigate({ analyticsView: "explore" });
          }}
        />
      )}
    </div>
  );
}
