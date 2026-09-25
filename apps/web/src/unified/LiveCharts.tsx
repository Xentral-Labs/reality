import { useEffect, useMemo, useState } from "react";
import { api, type InteractionSeries } from "../api";
import { formatNumber, formatTime, t } from "../localization";
import type { LiveFilter } from "./engineRoomModel";

// The live monitor's curves (spec 266): the trend behind the minute the cockpit
// shows. One axis per chart; channels keep their colour everywhere on the page.
const CHANNEL_SERIES = [
  { key: "web", label: "Web", color: "var(--series-web)" },
  { key: "mcp", label: "MCP", color: "var(--series-mcp)" },
  { key: "chat", label: "Chat", color: "var(--series-chat)" },
  { key: "cli", label: "CLI", color: "var(--series-cli)" },
  { key: "worker", label: "Worker", color: "var(--series-worker)" },
] as const;
const WINDOWS = [5, 15, 60] as const;
const REFRESH_MS = 10_000;
const TIMEOUT_MS = 8000;
const WIDTH = 300;
const HEIGHT = 96;

type Bucket = InteractionSeries["buckets"][number];
type Series = { key: string; label: string; color: string; values: (number | null)[] };

const x = (index: number, count: number) => (count <= 1 ? 0 : (index / (count - 1)) * WIDTH);
const y = (value: number, peak: number) => HEIGHT - (value / peak) * HEIGHT;

function linePath(values: (number | null)[], peak: number): string {
  // A quiet step has no duration; the line breaks there rather than dropping to zero.
  let path = "";
  let open = false;
  values.forEach((value, index) => {
    if (value === null) {
      open = false;
      return;
    }
    path += `${open ? "L" : "M"}${x(index, values.length)} ${y(value, peak)}`;
    open = true;
  });
  return path;
}

function Chart({
  title,
  series,
  buckets,
  kind,
  hover,
  setHover,
  unit,
}: {
  title: string;
  series: Series[];
  buckets: Bucket[];
  kind: "stack" | "line" | "bars";
  hover: number | null;
  setHover: (index: number | null) => void;
  unit: string;
}) {
  const count = buckets.length;
  const totals = buckets.map((_, index) =>
    kind === "stack"
      ? series.reduce((sum, item) => sum + (item.values[index] || 0), 0)
      : Math.max(0, ...series.map((item) => item.values[index] || 0)),
  );
  const peak = Math.max(1, ...totals);
  // Without a hover, the last complete step: the running one is still filling.
  const at = hover ?? Math.max(0, count - 2);
  const shapes = useMemo(() => {
    // Nothing to draw until the first read has arrived.
    if (count < 2) return null;
    if (kind === "stack") {
      const base = buckets.map(() => 0);
      return series.map((item) => {
        const lower = [...base];
        item.values.forEach((value, index) => (base[index] += value || 0));
        const top = base.map((value, index) => `${x(index, count)} ${y(value, peak)}`);
        const bottom = lower
          .map((value, index) => `${x(index, count)} ${y(value, peak)}`)
          .reverse();
        return (
          <path
            key={item.key}
            d={`M${top.join(" L")} L${bottom.join(" L")} Z`}
            fill={item.color}
            // A thin surface seam keeps adjacent bands apart.
            stroke="var(--color-surface)"
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
        );
      });
    }
    if (kind === "bars") {
      const width = Math.max(0.5, WIDTH / count - 1);
      return series.map((item) =>
        item.values.map((value, index) =>
          value ? (
            <rect
              key={`${item.key}-${index}`}
              x={x(index, count) - width / 2}
              y={y(value, peak)}
              width={width}
              height={HEIGHT - y(value, peak)}
              rx={1}
              fill={item.color}
            />
          ) : null,
        ),
      );
    }
    return series.map((item) => (
      <path
        key={item.key}
        d={linePath(item.values, peak)}
        fill="none"
        stroke={item.color}
        strokeWidth={2}
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    ));
  }, [kind, series, buckets, count, peak]);
  const value = (item: Series) => item.values[at];
  return (
    <figure className="min-w-0 rounded-lg border border-border-subtle p-3" data-live-chart={kind}>
      <figcaption className="mb-1 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="text-xs font-medium text-fg-strong">{title}</span>
        <span className="text-xs tabular-nums text-fg-muted">
          {buckets[at] ? formatTime(buckets[at].at, true) : ""}
        </span>
      </figcaption>
      <ul className="mb-2 flex flex-wrap gap-x-3 gap-y-1 text-xs" aria-hidden>
        {series.map((item) => (
          <li key={item.key} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-sm" style={{ background: item.color }} />
            <span className="text-fg-secondary">{t(item.label)}</span>
            <span className="tabular-nums text-fg-strong">
              {value(item) === null || value(item) === undefined
                ? "—"
                : `${formatNumber(value(item) as number)}${unit}`}
            </span>
          </li>
        ))}
      </ul>
      <div className="text-right text-[10px] tabular-nums text-fg-quiet" aria-hidden>
        {t("max")} {formatNumber(peak)}
        {unit}
      </div>
      <div className="relative">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          preserveAspectRatio="none"
          className="block h-24 w-full overflow-visible"
          role="img"
          aria-label={title}
          onPointerMove={(event) => {
            const box = event.currentTarget.getBoundingClientRect();
            const ratio = (event.clientX - box.left) / Math.max(1, box.width);
            setHover(Math.max(0, Math.min(count - 1, Math.round(ratio * (count - 1)))));
          }}
          onPointerLeave={() => setHover(null)}
        >
          {/* Recessive guides: the baseline and half the peak. */}
          <line
            x1={0}
            x2={WIDTH}
            y1={HEIGHT}
            y2={HEIGHT}
            stroke="var(--color-border-default)"
            vectorEffect="non-scaling-stroke"
          />
          <line
            x1={0}
            x2={WIDTH}
            y1={HEIGHT / 2}
            y2={HEIGHT / 2}
            stroke="var(--color-border-subtle)"
            strokeDasharray="2 3"
            vectorEffect="non-scaling-stroke"
          />
          {shapes}
          {hover !== null && (
            <line
              x1={x(hover, count)}
              x2={x(hover, count)}
              y1={0}
              y2={HEIGHT}
              stroke="var(--color-fg-muted)"
              vectorEffect="non-scaling-stroke"
            />
          )}
        </svg>
      </div>
      {/* The same numbers as a table, for readers who do not see the curve. */}
      <table className="sr-only">
        <caption>{title}</caption>
        <thead>
          <tr>
            <th>{t("Time")}</th>
            {series.map((item) => (
              <th key={item.key}>{t(item.label)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {buckets.map((bucket, index) =>
            series.some((item) => item.values[index]) ? (
              <tr key={bucket.at}>
                <td>{formatTime(bucket.at, true)}</td>
                {series.map((item) => (
                  <td key={item.key}>{item.values[index] ?? "—"}</td>
                ))}
              </tr>
            ) : null,
          )}
        </tbody>
      </table>
    </figure>
  );
}

/** Four curves over a rolling window: load by channel, latency, errors, reads against writes. */
export function LiveCharts({ tenant, filter }: { tenant: string; filter: LiveFilter }) {
  const [minutes, setMinutes] = useState<(typeof WINDOWS)[number]>(15);
  const [data, setData] = useState<InteractionSeries | null>(null);
  const [hover, setHover] = useState<number | null>(null);
  const query = useMemo(() => {
    const params = new URLSearchParams({ minutes: String(minutes) });
    if (filter.channel) params.set("channel", filter.channel);
    if (filter.actor) params.set("actor_user_id", filter.actor);
    if (filter.mcpToken) params.set("mcp_token_id", filter.mcpToken);
    if (filter.own) params.set("hide_own", "false");
    return params.toString();
  }, [minutes, filter.channel, filter.actor, filter.mcpToken, filter.own]);
  useEffect(() => {
    let disposed = false;
    const read = async () => {
      if (disposed || document.hidden) return;
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), TIMEOUT_MS);
      try {
        const series = await api.interactionSeries(
          tenant,
          new URLSearchParams(query),
          controller.signal,
        );
        if (!disposed) setData(series);
      } catch {
        /* the curves keep their last values; the cockpit reports a stale read */
      } finally {
        window.clearTimeout(timeout);
      }
    };
    void read();
    const timer = window.setInterval(() => void read(), REFRESH_MS);
    return () => {
      disposed = true;
      window.clearInterval(timer);
    };
  }, [tenant, query]);
  const buckets = data?.buckets || [];
  const perMinute = 60 / (data?.step_seconds || 60);
  const rate = (value: number) => Math.round(value * perMinute);
  const charts: {
    title: string;
    kind: "stack" | "line" | "bars";
    unit: string;
    series: Series[];
  }[] = [
    {
      title: t("Accesses per minute by channel"),
      kind: "stack",
      unit: "",
      series: CHANNEL_SERIES.map((item) => ({
        ...item,
        values: buckets.map((bucket) => rate(bucket.channels[item.key])),
      })),
    },
    {
      title: t("Response time"),
      kind: "line",
      unit: " ms",
      series: [
        {
          key: "p95",
          label: "p95",
          color: "var(--color-accent)",
          values: buckets.map((b) => b.p95_ms),
        },
        {
          key: "p50",
          label: "p50",
          color: "var(--color-fg-muted)",
          values: buckets.map((b) => b.p50_ms),
        },
      ],
    },
    {
      title: t("Refused or failed per minute"),
      kind: "bars",
      unit: "",
      series: [
        {
          key: "errors",
          label: "Refused or failed",
          color: "var(--color-critical)",
          values: buckets.map((bucket) => rate(bucket.errors)),
        },
      ],
    },
    {
      title: t("Reads and changes per minute"),
      kind: "line",
      unit: "",
      series: [
        {
          key: "reads",
          label: "Reads",
          color: "var(--color-fg-muted)",
          values: buckets.map((b) => rate(b.reads)),
        },
        {
          key: "writes",
          label: "Changes",
          color: "var(--color-accent)",
          values: buckets.map((b) => rate(b.writes)),
        },
      ],
    },
  ];
  return (
    <section className="@container space-y-2" aria-labelledby="live-charts-title" data-live-charts>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 id="live-charts-title" className="text-xs font-medium text-fg-muted">
          {t("Trend")}
        </h3>
        <div className="register-tabs" role="group" aria-label={t("Window")}>
          {WINDOWS.map((value) => (
            <button key={value} aria-pressed={minutes === value} onClick={() => setMinutes(value)}>
              {t("{count} min").replace("{count}", String(value))}
            </button>
          ))}
        </div>
      </div>
      {/* Two by two, or one column when narrow: the grid always closes. */}
      <div className="grid gap-2 @xl:grid-cols-2">
        {charts.map((chart) => (
          <Chart
            key={chart.title}
            title={chart.title}
            series={chart.series}
            buckets={buckets}
            kind={chart.kind}
            hover={hover}
            setHover={setHover}
            unit={chart.unit}
          />
        ))}
      </div>
    </section>
  );
}
