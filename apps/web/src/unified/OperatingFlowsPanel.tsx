import { InstrumentTrend } from "./InstrumentTrend";
import { ObservedMetric } from "./ObservedMetric";
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { AnalysisMetricGroup, AnalysisPlot } from "./AnalysisSections";
import { Info, X } from "lucide-react";
import { formatNumber, formatZonedDateTime, t } from "../localization";
import type { FlowArea, FlowRisk, InstrumentGroup, OperatingFlows } from "./cockpitModel";
import {
  cockpitOriginSelection,
  navigationSelection,
  selectionUrl,
  type Selection,
} from "./routing";

type Metric = { key: string; label: string; recent?: boolean };
export type OperatingAreaKey = "orders" | "messages" | "supply" | "stock" | "returns";
export type AnalysisAreaKey = "shipping" | OperatingAreaKey;
const areas: {
  key: OperatingAreaKey;
  title: string;
  metrics: Metric[];
  lines: { key: string; label: string }[];
  explanation: string;
  destination: Partial<Selection>;
}[] = [
  {
    key: "orders",
    title: "Customer orders",
    metrics: [
      { key: "open_orders", label: "Orders still to dispatch" },
      { key: "received_last_hour", label: "New orders · 60 min", recent: true },
      { key: "dispatch_movements_last_hour", label: "Dispatch records · 60 min", recent: true },
    ],
    lines: [
      { key: "orders_received", label: "New orders" },
      { key: "dispatch_movements", label: "Physical dispatch records" },
    ],
    explanation:
      "Orders count once at first recording. Dispatch records are stock movements; confirmed handovers remain in the shipping chart.",
    destination: { route: "orders-deliveries", ordersView: "customer-orders" },
  },
  {
    key: "messages",
    title: "Messages & responses",
    metrics: [
      { key: "unanswered", label: "Without a recorded reply" },
      { key: "customer_requests", label: "Customer requests awaiting reply" },
      { key: "unread", label: "Not yet acknowledged" },
      { key: "incoming_last_hour", label: "Incoming messages · 60 min", recent: true },
      { key: "first_replies_last_hour", label: "First replies · 60 min", recent: true },
    ],
    lines: [
      { key: "messages_incoming", label: "Incoming messages" },
      { key: "message_first_replies", label: "First recorded replies" },
    ],
    explanation:
      "Reply backlog covers the local simulator mailbox. Reading is not replying. Recorded replies do not prove delivery or completed work; provider reply coverage is unavailable.",
    destination: { route: "inspector", inspectorView: "business" },
  },
  {
    key: "supply",
    title: "Expected goods & receipts",
    metrics: [
      { key: "open_lines", label: "Supplier lines still expected" },
      { key: "fully_received_lines", label: "Fully received supplier lines" },
      { key: "receipts_last_hour", label: "Receipt records · 60 min", recent: true },
      { key: "unknown_due_lines", label: "Expected lines without a date" },
    ],
    lines: [{ key: "receipts", label: "Goods receipt records" }],
    explanation:
      "Expected work counts open supplier promise lines. A receipt record can be partial; purchase documents and goods quantities are not added together.",
    destination: { route: "orders-deliveries", ordersView: "supplier-orders" },
  },
  {
    key: "stock",
    title: "Stock risks",
    metrics: [{ key: "oversold_items", label: "Items with uncovered demand" }],
    lines: [],
    explanation:
      "Current oversold-item exceptions compare open demand with physical stock and expected supply in compatible item units. No historical stock curve or new safety-stock target is inferred.",
    destination: { route: "warehouse", warehouseView: "stock" },
  },
  {
    key: "returns",
    title: "Returns & disposition",
    metrics: [
      { key: "pending_positions", label: "Arrived positions still to process" },
      { key: "resolved_positions", label: "Physically processed positions" },
      { key: "arrived_positions", label: "Recorded return arrivals · total" },
      { key: "expected_announcements", label: "Announced returns still expected" },
      { key: "arrivals_last_hour", label: "Return arrivals · 60 min", recent: true },
    ],
    lines: [
      { key: "return_arrivals", label: "Return receipt records" },
      { key: "return_dispositions", label: "Disposition movement records" },
    ],
    explanation:
      "Arrivals and physical disposition are separate. Partial disposition stays open; physical processing does not prove refund or completion of the whole return case.",
    destination: { route: "warehouse", warehouseView: "movements", state: "return" },
  },
];
const signalLabels = {
  critical: "Critical recorded condition",
  attention: "Recorded condition needs attention",
  progress: "Pending work",
  clear: "No finding in the evaluated scope",
  unknown: "Data incomplete",
};

const riskCategories = [
  { key: "in_plan", label: "In plan" },
  { key: "at_risk", label: "At risk" },
  { key: "critical", label: "Critical" },
  { key: "unclassified", label: "Not assessed" },
] as const;
function RiskMeter({
  risk,
  stale,
  inspect,
}: {
  risk?: FlowRisk;
  stale: boolean;
  inspect?: (group: InstrumentGroup) => void;
}) {
  const total = risk?.total;
  return (
    <>
      <span className="cockpit-instrument-strip" data-instrument-strip aria-hidden="true">
        {typeof total === "number" && total > 0 && !stale ? (
          riskCategories.map(({ key }) => {
            const count = risk?.[key];
            return typeof count === "number" && count > 0 ? (
              <i key={key} data-risk-segment={key} style={{ width: `${(100 * count) / total}%` }} />
            ) : null;
          })
        ) : typeof total === "number" && total === 0 && !stale ? null : (
          <i data-risk-segment="unclassified" style={{ width: "100%" }} />
        )}
      </span>
      <span className="cockpit-risk-counts">
        {riskCategories.slice(0, 3).map(({ key, label }) =>
          inspect ? (
            <button
              type="button"
              key={key}
              data-risk-count={key}
              className="cockpit-risk-trigger"
              disabled={typeof risk?.[key] !== "number"}
              onClick={() => inspect(key)}
              aria-haspopup="dialog"
            >
              <strong>{typeof risk?.[key] === "number" ? formatNumber(risk[key]) : "—"}</strong>{" "}
              <span className="cockpit-risk-label">{t(label)}</span>
            </button>
          ) : (
            <span key={key} data-risk-count={key}>
              <strong>{typeof risk?.[key] === "number" ? formatNumber(risk[key]) : "—"}</strong>{" "}
              <span className="cockpit-risk-label">{t(label)}</span>
            </span>
          ),
        )}
        {typeof risk?.unclassified === "number" &&
          risk.unclassified > 0 &&
          (inspect ? (
            <button
              type="button"
              data-risk-count="unclassified"
              className="cockpit-risk-trigger"
              aria-haspopup="dialog"
              onClick={() => inspect("unclassified")}
            >
              <strong>{formatNumber(risk.unclassified)}</strong>
              <span className="cockpit-risk-label">{t("Not assessed")}</span>
            </button>
          ) : (
            <span data-risk-count="unclassified">
              <strong>{formatNumber(risk.unclassified)}</strong>
              <span className="cockpit-risk-label">{t("Not assessed")}</span>
            </span>
          ))}
      </span>
    </>
  );
}

function InstrumentDialog({
  area,
  group,
  setGroup,
  value,
  selection,
  stale,
  close,
}: {
  area: (typeof areas)[number];
  group: InstrumentGroup;
  setGroup: (group: InstrumentGroup) => void;
  value: OperatingFlows;
  selection: Selection;
  stale: boolean;
  close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const previous = useRef(document.activeElement as HTMLElement);
  useLayoutEffect(() => {
    const node = dialog.current;
    node?.showModal();
    return () => {
      node?.close();
      previous.current?.focus({ preventScroll: true });
    };
  }, []);
  const data = value[area.key];
  const page = data.inspection?.[group];
  const total = page?.total;
  return (
    <dialog
      ref={dialog}
      className="cockpit-instrument-dialog"
      aria-labelledby="instrument-inspection-heading"
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
    >
      <header className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t(area.title)}</span>
          <h2 id="instrument-inspection-heading">{t("Quick inspection")}</h2>
          <p>
            {t(area.metrics[0].label)} · {typeof total === "number" ? formatNumber(total) : "—"}
          </p>
        </div>
        <button type="button" className="shell-icon-button" aria-label={t("Close")} onClick={close}>
          <X size={18} />
        </button>
      </header>
      <label className="br-field">
        {t("Risk group")}
        <select
          className="br-control"
          value={group}
          onChange={(event) => setGroup(event.target.value as InstrumentGroup)}
        >
          <option value="all">{t("All open work")}</option>
          {riskCategories.map(({ key, label }) => (
            <option value={key} key={key} disabled={data.inspection?.[key]?.total == null}>
              {t(label)} ·{" "}
              {data.inspection?.[key]?.total == null
                ? "—"
                : formatNumber(data.inspection[key].total!)}
            </option>
          ))}
        </select>
      </label>
      {stale && (
        <p role="status" className="cockpit-note">
          {t("Previous observation — refresh failed")}
        </p>
      )}
      {typeof total !== "number" ? (
        <p role="status">{t("Inspection evidence is unavailable")}</p>
      ) : total === 0 ? (
        <p role="status" className="cockpit-inspection-empty">
          {t("No records in this group")}
        </p>
      ) : (
        <>
          <div className="cockpit-inspection-table-wrap">
            <table className="cockpit-inspection-table">
              <thead>
                <tr>
                  <th>{t("Record")}</th>
                  <th>{t("Recorded condition")}</th>
                  <th>{t("Due / recorded at")}</th>
                </tr>
              </thead>
              <tbody>
                {page?.items.map((row) => (
                  <tr key={`${row.kind}:${row.id}`}>
                    <td>
                      <a
                        className="br-link"
                        href={selectionUrl(
                          navigationSelection(selection, {
                            route: "inspector",
                            inspectorView: "records",
                            inspectorTargetKind: row.kind,
                            inspectorTargetId: row.id,
                            cockpitOrigin: cockpitOriginSelection(selection),
                          }),
                        )}
                      >
                        {row.label}
                      </a>
                      {row.item_label && row.item_label !== row.label && (
                        <small>{row.item_label}</small>
                      )}
                      <small>{row.id}</small>
                    </td>
                    <td>
                      <span className="cockpit-inspection-group" data-risk-count={row.category}>
                        {t(riskCategories.find((r) => r.key === row.category)!.label)}
                      </span>
                      <small>
                        {row.conditions.length
                          ? row.conditions.map((condition) => t(condition)).join(" · ")
                          : t(
                              row.category === "in_plan"
                                ? "No finding in the evaluated scope"
                                : "No recorded assessment",
                            )}
                      </small>
                      {row.shortfall !== null && (
                        <small>
                          {t("Uncovered quantity")}: {formatNumber(Number(row.shortfall))}{" "}
                          {row.unit || ""}
                        </small>
                      )}
                    </td>
                    <td>{row.at ? formatZonedDateTime(row.at) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="cockpit-note">
            {t("Shown")}: {formatNumber(page?.items.length || 0)} / {formatNumber(total)} ·{" "}
            {t("Preview only; open the workspace for the complete register.")}
          </p>
        </>
      )}
      <footer className="cockpit-inspection-footer">
        <span>
          {t("Data observed at")} {formatZonedDateTime(value.observed_at)}
        </span>
        <a
          className="br-link"
          href={selectionUrl(
            navigationSelection(selection, {
              ...area.destination,
              cockpitOrigin: cockpitOriginSelection(selection),
            }),
          )}
        >
          {t("Open workspace")} →
        </a>
      </footer>
    </dialog>
  );
}

export function OperatingStatusPanel({
  value,
  stale,
  selection,
  supporting,
}: {
  value?: OperatingFlows;
  stale: boolean;
  selection: Selection;
  supporting?: ReactNode;
}) {
  const [inspection, setInspection] = useState<{
    area: OperatingAreaKey;
    group: InstrumentGroup;
  } | null>(null);
  useEffect(() => setInspection(null), [selection.tenant]);
  const titles = {
    orders: "Order status",
    messages: "Message status",
    supply: "Supply status",
    stock: "Stock status",
    returns: "Return status",
  };
  return (
    <section
      className="cockpit-status-overview cockpit-instruments"
      aria-labelledby="operating-status-heading"
      data-operating-status
    >
      <header className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Company-wide · live")}</span>
          <h2 id="operating-status-heading">{t("Company instruments")}</h2>
          <p>
            {t("Select a tile to inspect its records.")}{" "}
            {t("Live company-wide status. Choose a chart area in Detailed analysis.")}
          </p>
        </div>
      </header>
      <ul className="cockpit-status-grid">
        {areas.map((area) => {
          const data = value?.[area.key];
          const signal = stale || !data ? "unknown" : data.signal;
          const metric = area.metrics[0];
          const contents = (
            <>
              <span className="cockpit-status-area-title">{t(titles[area.key])}</span>
              <span className="cockpit-status-metric-row">
                <span>{t(metric.label)}</span>
                <button
                  type="button"
                  className="cockpit-metric-trigger"
                  aria-haspopup="dialog"
                  disabled={typeof data?.[metric.key] !== "number" || !data?.inspection}
                  aria-label={`${t(titles[area.key])} · ${t(metric.label)} · ${typeof data?.[metric.key] === "number" ? formatNumber(data[metric.key] as number) : "—"}`}
                  onClick={() => setInspection({ area: area.key, group: "all" })}
                >
                  <ObservedMetric
                    value={
                      typeof data?.[metric.key] === "number" ? (data[metric.key] as number) : null
                    }
                    context={`${selection.tenant}:${selection.cockpitMinutes || 15}:${area.key}`}
                    current={!stale}
                  />
                </button>
              </span>
              <RiskMeter
                risk={data?.risk}
                stale={stale}
                inspect={
                  data?.inspection ? (group) => setInspection({ area: area.key, group }) : undefined
                }
              />
              <span className="cockpit-status-condition">
                <span className="cockpit-status-indicator" aria-hidden="true" />
                <strong>{t(signalLabels[signal])}</strong>
              </span>
              <InstrumentTrend
                area={area.key}
                title={titles[area.key]}
                value={value}
                stale={stale}
              />
            </>
          );
          return (
            <li
              className={`br-card cockpit-status-tile ${signal}`}
              key={area.key}
              data-status-area={area.key}
              data-signal={signal}
            >
              <div className="cockpit-status-link">{contents}</div>
            </li>
          );
        })}
        <li className="br-card cockpit-status-tile unknown" data-instrument-area="finance">
          <a
            className="br-link cockpit-status-link"
            href={selectionUrl(
              navigationSelection(selection, {
                route: "finance",
                financeView: "open-items",
                cockpitOrigin: cockpitOriginSelection(selection),
              }),
            )}
          >
            <span className="cockpit-status-area-title">{t("Finance")}</span>
            <span className="cockpit-status-metric-row">
              <span>{t("Not available in this observation")}</span>
              <strong>—</strong>
            </span>
            <RiskMeter stale={stale} />
            <span className="cockpit-status-condition">
              <span className="cockpit-status-indicator" aria-hidden="true" />
              <strong>{t("Data incomplete")}</strong>
            </span>
            <InstrumentTrend area="finance" title="Finance" value={value} stale={stale} />
          </a>
        </li>
      </ul>
      {inspection && value && (
        <InstrumentDialog
          area={areas.find((area) => area.key === inspection.area)!}
          group={inspection.group}
          setGroup={(group) => setInspection({ ...inspection, group })}
          value={value}
          selection={selection}
          stale={stale}
          close={() => setInspection(null)}
        />
      )}
      <footer className="cockpit-instrument-footer" data-instrument-legend-footer>
        <div className="cockpit-risk-legend" data-risk-legend>
          {riskCategories.map(({ key, label }) => (
            <span key={key} data-risk-key={key}>
              <i aria-hidden="true" />
              {t(label)}
            </span>
          ))}
          <details
            className="cockpit-risk-explanation"
            data-risk-explanation
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                event.preventDefault();
                event.stopPropagation();
                event.currentTarget.open = false;
                event.currentTarget.querySelector("summary")?.focus({ preventScroll: true });
              }
            }}
          >
            <summary
              className="shell-icon-button cockpit-icon-action"
              aria-label={t("Definition & evidence")}
              title={t("Definition & evidence")}
            >
              <Info size={14} aria-hidden="true" />
            </summary>
            <div className="cockpit-risk-explanation-content">
              <p className="cockpit-risk-scope">
                {t("Segments: share of the displayed open work")}
              </p>
              <p className="cockpit-footnote">
                {t(
                  "In plan: no finding in the evaluated scope. Missing deadlines or assessments remain unclassified.",
                )}
              </p>
            </div>
          </details>
        </div>
      </footer>
      {supporting}
    </section>
  );
}

function Curve({
  lines,
  level = false,
  title,
  context,
}: {
  context?: ReactNode;
  lines: { label: string; values: (number | null)[] }[];
  level?: boolean;
  title: string;
}) {
  const container = useRef<HTMLElement>(null);
  const [width, setWidth] = useState(360);
  useEffect(() => {
    if (!container.current) return;
    const observer = new ResizeObserver(([entry]) => {
      if (entry.contentRect.width > 0) setWidth(entry.contentRect.width);
    });
    observer.observe(container.current);
    return () => observer.disconnect();
  }, []);
  const known = lines.flatMap((line) => line.values.filter((n): n is number => n !== null));
  const minimum = level && known.length ? Math.max(0, Math.min(...known) - 1) : 0;
  const maximum = known.length ? Math.max(...known) + (level ? 1 : 0) : 0;
  const range = Math.max(1, maximum - minimum);
  const left = 50,
    right = width - 10,
    top = 30,
    bottom = 143;
  const y = (value: number) => bottom - ((value - minimum) * (bottom - top)) / range;
  return (
    <AnalysisPlot title={t(title)} kind={level ? "backlog" : "flow"} plotRef={container}>
      <svg
        viewBox={`0 0 ${width} 190`}
        role="img"
        aria-label={`${t(title)} · ${lines.map((line) => t(line.label)).join(" · ")}`}
        className="cockpit-flow-curve"
      >
        <title>{t(title)}</title>
        <text x={left} y={14}>
          {t(level ? "Open messages" : "Records per interval")}
        </text>
        {[minimum, minimum + range / 2, minimum + range].map((value, index) => (
          <g key={index}>
            <path d={`M${left} ${y(value)} H${right}`} className="cockpit-flow-axis" />
            <text x={left - 8} y={y(value) + 4} textAnchor="end">
              {formatNumber(value)}
            </text>
          </g>
        ))}
        {lines.map((line, index) => {
          let open = false;
          const path = line.values
            .map((value, i) => {
              if (value === null) {
                open = false;
                return "";
              }
              const command = open ? "L" : "M";
              open = true;
              return `${command}${left + (i * (right - left)) / Math.max(1, line.values.length - 1)},${y(value)}`;
            })
            .join(" ");
          return (
            <path
              key={line.label}
              d={path}
              className={`cockpit-flow-line line-${index}`}
              data-flow-series={line.label}
            >
              <title>{t(line.label)}</title>
            </path>
          );
        })}
        <text x={left} y={166}>
          {t("60 minutes ago")}
        </text>
        <text x={right} y={166} textAnchor="end">
          {t("Now")}
        </text>
        <text x={right} y={187} textAnchor="end">
          {t("Last 60 minutes")}
        </text>
      </svg>
      <div className="cockpit-plot-context">
        <div className="cockpit-flow-axis-labels">
          <span>
            {t("Displayed range")}:{" "}
            {known.length ? `${formatNumber(minimum)}–${formatNumber(maximum)}` : "—"}
          </span>
          {!known.length && <span>{t("Data incomplete")}</span>}
        </div>
        <div className="cockpit-flow-legend">
          {lines.map((line, i) => (
            <span key={line.label} className={`line-${i}`}>
              {t(line.label)}
            </span>
          ))}
        </div>
        {!level && (
          <p className="cockpit-note">
            {t("Five-minute intervals; edge intervals may be shorter.")}
          </p>
        )}
        {context}
      </div>
    </AnalysisPlot>
  );
}

export function OperatingFlowsPanel({
  value,
  selection,
  stale,
  selected,
  select,
  shipping,
}: {
  value?: OperatingFlows;
  selection: Selection;
  stale: boolean;
  selected: AnalysisAreaKey;
  select: (area: AnalysisAreaKey) => void;
  shipping: ReactNode;
}) {
  return (
    <section
      className="cockpit-card cockpit-flow-board"
      aria-labelledby="flows-heading"
      data-operating-flows
    >
      <header className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Flow analysis")}</span>
          <h2 id="flows-heading">
            {t(
              selected === "shipping"
                ? "Shipping by end of day"
                : areas.find((area) => area.key === selected)!.title,
            )}
          </h2>
        </div>
        <label className="br-field cockpit-analysis-selector">
          {t("Analysis area")}
          <select
            className="br-control"
            value={selected}
            onChange={(event) => select(event.target.value as AnalysisAreaKey)}
            aria-controls={`cockpit-flow-${selected}`}
          >
            <option value="shipping">{t("Shipping performance")}</option>
            {areas.map((area) => (
              <option key={area.key} value={area.key}>
                {t(area.title)}
              </option>
            ))}
          </select>
        </label>
      </header>
      {selected !== "shipping" && (
        <p className="cockpit-analysis-context cockpit-note">
          {t("Current queues and the last 60 minutes. Independent of the shipping day and site.")}
        </p>
      )}
      {selected !== "shipping" && stale && (
        <p role="status" className="cockpit-note">
          {t("Live status is not confirmed")}
        </p>
      )}
      <div id="cockpit-flow-shipping" hidden={selected !== "shipping"} data-shipping-analysis>
        {shipping}
      </div>
      {!value && selected !== "shipping" && <p>{t("Operating flow evidence is unavailable")}</p>}
      <div className="cockpit-flow-grid cockpit-analysis-grid">
        {value &&
          areas.map((area) => {
            const data: FlowArea = value[area.key];
            const signal = stale ? "unknown" : data.signal;
            const lines = area.lines.map((line) => ({
              label: line.label,
              values: value.buckets.map((bucket) =>
                bucket.known &&
                (area.key !== "messages" || value.messages.coverage !== "unavailable") &&
                typeof bucket[line.key] === "number"
                  ? (bucket[line.key] as number)
                  : null,
              ),
            }));
            return (
              <article
                className="cockpit-flow-card cockpit-analysis-card"
                data-flow-area={area.key}
                id={`cockpit-flow-${area.key}`}
                tabIndex={-1}
                key={area.key}
                hidden={selected !== area.key}
              >
                <p className={`cockpit-flow-signal ${signal}`}>
                  <span aria-hidden="true" />
                  {t(signalLabels[signal])}
                </p>
                <div className="cockpit-metric-groups">
                  {([false, true] as const).map((recent) => {
                    const metrics = area.metrics.filter(
                      (metric) => Boolean(metric.recent) === recent,
                    );
                    if (!metrics.length) return null;
                    return (
                      <AnalysisMetricGroup
                        key={recent ? "recent" : "current"}
                        period={recent ? "recent" : "current"}
                        title={t(recent ? "Last 60 minutes" : "Current status")}
                      >
                        <dl data-metric-count={metrics.length}>
                          {metrics.map((metric) => (
                            <div key={metric.key}>
                              <dt>{t(metric.label)}</dt>
                              <dd>
                                {typeof data[metric.key] === "number"
                                  ? formatNumber(data[metric.key] as number)
                                  : "—"}
                              </dd>
                            </div>
                          ))}
                        </dl>
                      </AnalysisMetricGroup>
                    );
                  })}
                </div>
                <div className="cockpit-flow-chart" data-flow-chart>
                  {lines.length > 0 && (
                    <Curve
                      lines={lines}
                      title={
                        area.key === "messages" ? "Incoming & first replies" : "Recorded movements"
                      }
                    />
                  )}
                  {area.key === "messages" && (
                    <Curve
                      title="Unanswered backlog"
                      context={
                        <div data-backlog-context>
                          <p className="cockpit-note">
                            {t("Local mailbox · provider response status unknown")}
                          </p>
                          <p className="cockpit-note">
                            {t("Backlog change · 60 min")}:{" "}
                            {typeof data.backlog_change_last_hour === "number"
                              ? `${data.backlog_change_last_hour > 0 ? "+" : ""}${formatNumber(data.backlog_change_last_hour)}`
                              : "—"}
                          </p>
                        </div>
                      }
                      lines={[
                        {
                          label: "Messages awaiting reply",
                          values: value.messages.series.map((point) => point.unanswered),
                        },
                      ]}
                      level
                    />
                  )}
                  {area.key === "stock" && (
                    <p className="cockpit-note">
                      {t("Current observation · risk history unavailable")}
                    </p>
                  )}
                </div>
                <div className="cockpit-flow-notes">
                  {typeof data.exception_total === "number" && data.exception_total > 0 && (
                    <p className="cockpit-note">
                      {formatNumber(data.exception_total)} {t("recorded exceptions")}
                    </p>
                  )}
                  {area.key === "returns" && Number(data.unknown_positions) > 0 && (
                    <p className="cockpit-note">
                      {formatNumber(Number(data.unknown_positions))}{" "}
                      {t("positions with unknown disposition")}
                    </p>
                  )}
                </div>
                <details className="cockpit-flow-details">
                  <summary>{t("Definition & evidence")}</summary>
                  <p>{t(area.explanation)}</p>
                  <p>
                    {t(
                      "Risk counts use the complete displayed cohort, with each identity counted once at its worst recorded condition. High or critical findings are red; other findings are orange.",
                    )}
                  </p>
                  {area.key === "messages" && (
                    <p>{t("Message deadlines are not recorded; urgency cannot be assessed.")}</p>
                  )}
                  {area.key === "returns" && (
                    <p>
                      {t(
                        "Pending returns without a recorded finding remain unclassified; a missing learned threshold does not prove timeliness.",
                      )}
                    </p>
                  )}
                  {area.key === "stock" && (
                    <p>
                      {t(
                        "Stock segments cover only items with uncovered demand, not all stocked items.",
                      )}
                    </p>
                  )}
                  {area.key === "messages" && Number(data.external_incoming) > 0 && (
                    <p>
                      {formatNumber(Number(data.external_incoming))}{" "}
                      {t("provider messages with unknown reply state")}
                    </p>
                  )}
                  {area.key === "orders" && Number(data.unlinked_open_lines) > 0 && (
                    <p>
                      {formatNumber(Number(data.unlinked_open_lines))}{" "}
                      {t("open delivery lines without an order link")}
                    </p>
                  )}
                  <ul>
                    {data.evidence.map((row) => (
                      <li key={`${row.kind}:${row.id}`}>
                        <a
                          href={selectionUrl(
                            navigationSelection(selection, {
                              route: "inspector",
                              inspectorView: "records",
                              inspectorTargetKind: row.kind,
                              inspectorTargetId: row.id,
                              cockpitOrigin: cockpitOriginSelection(selection),
                            }),
                          )}
                        >
                          {row.label}
                        </a>
                      </li>
                    ))}
                  </ul>
                  {(data.exceptions || []).map((row) => (
                    <p key={row.id}>
                      <a
                        href={selectionUrl(
                          navigationSelection(selection, {
                            route: "inspector",
                            inspectorView: "records",
                            inspectorTargetKind: row.kind,
                            inspectorTargetId: row.record_id,
                            cockpitOrigin: cockpitOriginSelection(selection),
                          }),
                        )}
                      >
                        {t(row.title)}
                      </a>
                    </p>
                  ))}
                  <p className="cockpit-note">
                    {t("Complete company totals; up to four evidence records shown.")}
                  </p>
                </details>
                <a
                  className="cockpit-flow-workspace"
                  href={selectionUrl(
                    navigationSelection(selection, {
                      ...area.destination,
                      cockpitOrigin: cockpitOriginSelection(selection),
                    }),
                  )}
                >
                  {t("Open workspace")} <span aria-hidden="true">→</span>
                </a>
              </article>
            );
          })}
      </div>
      {value && selected !== "shipping" && (
        <>
          <p className="cockpit-note cockpit-analysis-scope">
            {t("Data observed at")} {formatZonedDateTime(value.observed_at)}
          </p>
          <p className="cockpit-note">
            {t(
              "Status describes the recorded condition, not agent quality. Pending work is not automatically a failure.",
            )}
          </p>
        </>
      )}
    </section>
  );
}
