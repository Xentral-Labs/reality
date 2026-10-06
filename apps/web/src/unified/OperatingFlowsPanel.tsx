import { formatNumber, formatZonedDateTime, t } from "../localization";
import type { FlowArea, OperatingFlows } from "./cockpitModel";
import {
  cockpitOriginSelection,
  navigationSelection,
  selectionUrl,
  type Selection,
} from "./routing";

type Metric = { key: string; label: string };
const areas: {
  key: "orders" | "messages" | "supply" | "stock" | "returns";
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
    lines: [{ key: "unanswered", label: "Messages awaiting reply" }],
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
  unknown: "Evidence incomplete",
};

export function OperatingStatusPanel({ value, stale }: { value?: OperatingFlows; stale: boolean }) {
  const titles = {
    orders: "Order status",
    messages: "Message status",
    supply: "Supply status",
    stock: "Stock status",
    returns: "Return status",
  };
  return (
    <section
      className="br-card cockpit-card cockpit-status-overview"
      aria-labelledby="operating-status-heading"
      data-operating-status
    >
      <header className="cockpit-card-heading">
        <div>
          <h2 id="operating-status-heading">{t("Company status")}</h2>
          <p>
            {t("Company-wide recorded conditions. Select an area for its details and evidence.")}
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
              <span className="cockpit-status-condition">
                <span className="cockpit-status-indicator" aria-hidden="true" />
                <strong>{t(signalLabels[signal])}</strong>
              </span>
              <span className="cockpit-status-metric-row">
                <span>{t(metric.label)}</span>
                <strong data-status-metric>
                  {typeof data?.[metric.key] === "number"
                    ? formatNumber(data[metric.key] as number)
                    : "—"}
                </strong>
              </span>
              {data && (
                <span className="cockpit-status-detail">
                  {t("Status details")} <span aria-hidden="true">↓</span>
                </span>
              )}
            </>
          );
          return (
            <li
              className={`br-card cockpit-status-tile ${signal}`}
              key={area.key}
              data-status-area={area.key}
              data-signal={signal}
            >
              {data ? (
                <a className="br-link cockpit-status-link" href={`#cockpit-flow-${area.key}`}>
                  {contents}
                </a>
              ) : (
                <div className="cockpit-status-link">{contents}</div>
              )}
            </li>
          );
        })}
      </ul>
      <p className="cockpit-note">
        {t(
          "Red: critical · Orange: pending work, attention or incomplete evidence · Green: no recorded deviation",
        )}
      </p>
    </section>
  );
}

function Curve({
  lines,
  level = false,
}: {
  lines: { label: string; values: (number | null)[] }[];
  level?: boolean;
}) {
  const known = lines.flatMap((line) => line.values.filter((n): n is number => n !== null));
  const minimum = level && known.length ? Math.min(...known) : 0;
  const maximum = known.length ? Math.max(...known) : 0;
  const range = Math.max(1, maximum - minimum);
  return (
    <>
      <svg
        viewBox="0 0 260 64"
        role="img"
        aria-label={lines.map((line) => t(line.label)).join(" · ")}
        className="cockpit-flow-curve"
      >
        <path d="M0 58 H260" className="cockpit-flow-axis" />
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
              return `${command}${(i * 260) / Math.max(1, line.values.length - 1)},${58 - ((value - minimum) * 50) / range}`;
            })
            .join(" ");
          return <path key={line.label} d={path} className={`cockpit-flow-line line-${index}`} />;
        })}
      </svg>
      <div className="cockpit-flow-axis-labels">
        <span>{t("60 minutes ago")}</span>
        <span>
          {t("Displayed range")}:{" "}
          {known.length ? `${formatNumber(minimum)}–${formatNumber(maximum)}` : "—"}
        </span>
        <span>{t("Now")}</span>
      </div>
      <div className="cockpit-flow-legend">
        {lines.map((line, i) => (
          <span key={line.label} className={`line-${i}`}>
            {t(line.label)}
          </span>
        ))}
      </div>
    </>
  );
}

export function OperatingFlowsPanel({
  value,
  selection,
  stale,
}: {
  value?: OperatingFlows;
  selection: Selection;
  stale: boolean;
}) {
  if (!value)
    return (
      <section className="cockpit-card">
        <h2>{t("Company in motion")}</h2>
        <p>{t("Operating flow evidence is unavailable")}</p>
      </section>
    );
  return (
    <section className="cockpit-flow-board" aria-labelledby="flows-heading" data-operating-flows>
      <header className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Company-wide · live")}</span>
          <h2 id="flows-heading">{t("Company in motion")}</h2>
          <p>
            {t("Current queues and the last 60 minutes. Independent of the shipping day and site.")}
          </p>
        </div>
        <small>
          {t("Data observed at")} {formatZonedDateTime(value.observed_at)}
        </small>
      </header>
      {stale && (
        <p role="status" className="cockpit-note">
          {t("Live status is not confirmed")}
        </p>
      )}
      <div className="cockpit-flow-grid">
        {areas.map((area) => {
          const data: FlowArea = value[area.key];
          const signal = stale ? "unknown" : data.signal;
          const lines =
            area.key === "messages"
              ? [
                  {
                    label: area.lines[0].label,
                    values: value.messages.series.map((point) => point.unanswered),
                  },
                ]
              : area.lines.map((line) => ({
                  label: line.label,
                  values: value.buckets.map((bucket) =>
                    bucket.known ? Number(bucket[line.key] || 0) : null,
                  ),
                }));
          return (
            <article
              className="cockpit-card cockpit-flow-card"
              data-flow-area={area.key}
              id={`cockpit-flow-${area.key}`}
              tabIndex={-1}
              key={area.key}
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
                {lines.length > 0 && <Curve lines={lines} level={area.key === "messages"} />}
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
      <p className="cockpit-note">
        {t(
          "Status describes the recorded condition, not agent quality. Pending work is not automatically a failure.",
        )}
      </p>
    </section>
  );
}
