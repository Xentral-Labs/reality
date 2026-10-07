import { useEffect, useRef, useState } from "react";
import { formatNumber, formatZonedDateTime, t } from "../localization";
import type { FlowArea, FlowRisk, OperatingFlows } from "./cockpitModel";
import {
  cockpitOriginSelection,
  navigationSelection,
  selectionUrl,
  type Selection,
} from "./routing";

type Metric = { key: string; label: string };
export type OperatingAreaKey = "orders" | "messages" | "supply" | "stock" | "returns";
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
      { key: "received_last_hour", label: "New orders · 60 min" },
      { key: "dispatch_movements_last_hour", label: "Dispatch records · 60 min" },
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
      { key: "incoming_last_hour", label: "Incoming messages · 60 min" },
      { key: "first_replies_last_hour", label: "First replies · 60 min" },
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
      { key: "receipts_last_hour", label: "Receipt records · 60 min" },
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
      { key: "arrivals_last_hour", label: "Return arrivals · 60 min" },
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
function RiskMeter({ risk, stale }: { risk?: FlowRisk; stale: boolean }) {
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
        ) : (
          <i data-risk-segment="unclassified" style={{ width: "100%" }} />
        )}
      </span>
      <span className="cockpit-risk-counts">
        {riskCategories.slice(0, 3).map(({ key, label }) => (
          <span key={key} data-risk-count={key}>
            <strong>{typeof risk?.[key] === "number" ? formatNumber(risk[key]) : "—"}</strong>{" "}
            {t(label)}
          </span>
        ))}
        {typeof risk?.unclassified === "number" && risk.unclassified > 0 && (
          <span data-risk-count="unclassified">
            <strong>{formatNumber(risk.unclassified)}</strong> {t("Not assessed")}
          </span>
        )}
      </span>
    </>
  );
}

export function OperatingStatusPanel({
  value,
  stale,
  selection,
}: {
  value?: OperatingFlows;
  stale: boolean;
  selection: Selection;
}) {
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
          <p>{t("Live company-wide status. Choose a chart area in Detailed analysis.")}</p>
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
                <strong data-status-metric>
                  {typeof data?.[metric.key] === "number"
                    ? formatNumber(data[metric.key] as number)
                    : "—"}
                </strong>
              </span>
              <RiskMeter risk={data?.risk} stale={stale} />
              <span className="cockpit-status-condition">
                <span className="cockpit-status-indicator" aria-hidden="true" />
                <strong>{t(signalLabels[signal])}</strong>
              </span>
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
            <span className="cockpit-status-detail">{t("Open workspace")} →</span>
          </a>
        </li>
      </ul>
      <div className="cockpit-risk-legend" data-risk-legend>
        {riskCategories.map(({ key, label }) => (
          <span key={key} data-risk-key={key}>
            <i aria-hidden="true" />
            {t(label)}
          </span>
        ))}
        <span>{t("Segments: share of the displayed open work")}</span>
      </div>
      <p className="cockpit-footnote">
        {t(
          "In plan: no finding in the evaluated scope. Missing deadlines or assessments remain unclassified.",
        )}
      </p>
    </section>
  );
}

function Curve({
  lines,
  level = false,
  title,
}: {
  lines: { label: string; values: (number | null)[] }[];
  level?: boolean;
  title: string;
}) {
  const container = useRef<HTMLDivElement>(null);
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
    <div
      className="cockpit-analysis-plot"
      ref={container}
      data-analysis-kind={level ? "backlog" : "flow"}
    >
      <h4>{t(title)}</h4>
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
        <p className="cockpit-note">{t("Five-minute intervals; edge intervals may be shorter.")}</p>
      )}
    </div>
  );
}

export function OperatingFlowsPanel({
  value,
  selection,
  stale,
  selected,
  select,
}: {
  value?: OperatingFlows;
  selection: Selection;
  stale: boolean;
  selected: OperatingAreaKey;
  select: (area: OperatingAreaKey) => void;
}) {
  if (!value)
    return (
      <section className="cockpit-card">
        <h2>{t("Company in motion")}</h2>
        <p>{t("Operating flow evidence is unavailable")}</p>
      </section>
    );
  return (
    <section
      className="cockpit-card cockpit-flow-board"
      aria-labelledby="flows-heading"
      data-operating-flows
    >
      <header className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Company-wide · live")}</span>
          <h2 id="flows-heading">{t("Flow analysis")}</h2>
        </div>
        <label className="br-field cockpit-analysis-selector">
          {t("Analysis area")}
          <select
            className="br-control"
            value={selected}
            onChange={(event) => select(event.target.value as OperatingAreaKey)}
            aria-controls={`cockpit-flow-${selected}`}
          >
            {areas.map((area) => (
              <option key={area.key} value={area.key}>
                {t(area.title)}
              </option>
            ))}
          </select>
        </label>
      </header>
      {stale && (
        <p role="status" className="cockpit-note">
          {t("Live status is not confirmed")}
        </p>
      )}
      <div className="cockpit-flow-grid cockpit-analysis-grid">
        {areas.map((area) => {
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
              <h3>{t(area.title)}</h3>
              <p className={`cockpit-flow-signal ${signal}`}>
                <span aria-hidden="true" />
                {t(signalLabels[signal])}
              </p>
              <dl>
                {area.metrics.map((metric) => (
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
                {area.key === "messages" && (
                  <p className="cockpit-note">
                    {t("Local mailbox · provider response status unknown")}
                  </p>
                )}
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
                {area.key === "messages" && (
                  <p className="cockpit-note">
                    {t("Backlog change · 60 min")}:{" "}
                    {typeof data.backlog_change_last_hour === "number"
                      ? `${data.backlog_change_last_hour > 0 ? "+" : ""}${formatNumber(data.backlog_change_last_hour)}`
                      : "—"}
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
      <p className="cockpit-note cockpit-analysis-scope">
        {t("Current queues and the last 60 minutes. Independent of the shipping day and site.")}
        <br />
        {t("Data observed at")} {formatZonedDateTime(value.observed_at)}
      </p>
      <p className="cockpit-note">
        {t(
          "Status describes the recorded condition, not agent quality. Pending work is not automatically a failure.",
        )}
      </p>
    </section>
  );
}
