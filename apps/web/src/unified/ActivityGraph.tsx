import { useEffect, useRef, useState } from "react";
import { api, type ActivityVolume, type ActivityBucket, type TimelineEvent } from "../api";
import { formatDateTime, formatNumber, t } from "../localization";
import { ReadLine } from "./ReadState";
import { eventTitle } from "./ActivityDrawer";
import { Inspector } from "./Inspector";

const categories = [
  ["orders", "New orders"],
  ["reservations", "New reservations"],
  ["movements", "Stock movements"],
  ["documents", "Other documents"],
] as const;
const total = (row: ActivityBucket) => Object.values(row.counts).reduce((a, b) => a + b, 0);
export function ActivityGraph({
  data,
  days,
  tenant,
  stale,
}: {
  data: ActivityVolume;
  days: number;
  tenant: string;
  stale: boolean;
}) {
  const root = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800),
    [clock, setClock] = useState(Date.now());
  const [hover, setHover] = useState<ActivityBucket | null>(null),
    [selected, setSelected] = useState<ActivityBucket | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]),
    [detailError, setDetailError] = useState(false),
    [loading, setLoading] = useState(false),
    [more, setMore] = useState(false);
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  useEffect(() => {
    const observer = new ResizeObserver((entries) => setWidth(entries[0].contentRect.width));
    if (root.current) observer.observe(root.current);
    const timer = window.setInterval(() => {
      if (!document.hidden) setClock(Date.now());
    }, 1000);
    return () => {
      observer.disconnect();
      window.clearInterval(timer);
    };
  }, []);
  useEffect(() => {
    if (!selected) return;
    let active = true;
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 8000);
    setLoading(true);
    setDetailError(false);
    setEvents([]);
    api
      .activityVolumeEvents(tenant, selected.start, selected.end, controller.signal)
      .then((result) => {
        if (active) {
          setEvents(result.events);
          setMore(result.has_more);
        }
      })
      .catch(() => {
        if (active) setDetailError(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [selected, tenant]);
  const received = useRef({ observed: data.observed_at, at: Date.now() });
  if (received.current.observed !== data.observed_at)
    received.current = { observed: data.observed_at, at: Date.now() };
  const end = Date.parse(data.observed_at) + Math.max(0, clock - received.current.at),
    start = end - days * 86400000;
  const groupSize = Math.min(
    48,
    Math.max(1, Math.ceil(data.buckets.length / Math.max(30, Math.floor(width / 4)))),
  );
  const groups: ActivityBucket[] = [];
  for (let i = 0; i < data.buckets.length; i += groupSize) {
    const batch = data.buckets.slice(i, i + groupSize);
    groups.push({
      start: batch[0].start,
      end: batch[batch.length - 1].end,
      counts: { orders: 0, reservations: 0, movements: 0, documents: 0 },
    });
    for (const row of batch)
      for (const [key] of categories) groups[groups.length - 1].counts[key] += row.counts[key];
  }
  const plotWidth = Math.max(280, width);
  const right = plotWidth - 12;
  const maximum = Math.max(2, Math.ceil(Math.max(1, ...groups.map(total)) / 2) * 2);
  const x = (time: number) =>
    52 + Math.max(0, Math.min(1, (time - start) / (end - start))) * (right - 52);
  const covered = Date.parse(data.coverage_start),
    observed = Date.parse(data.observed_at);
  const known = groups
    .map((row) => ({
      ...row,
      start: new Date(
        Math.max(Date.parse(row.start), Date.parse(data.start), covered),
      ).toISOString(),
    }))
    .filter((row) => Date.parse(row.end) > covered && Date.parse(row.end) > start);
  const point = (row: ActivityBucket) =>
    `${x(Math.max(covered, Date.parse(row.start)))} ${210 - (total(row) / maximum) * 160}`;
  const area = known.length
    ? `M ${x(Math.max(covered, Date.parse(known[0].start)))} 210 L ${known.map(point).join(" L ")} L ${x(observed)} 210 Z`
    : "";
  const active = hover || selected;
  const preview = active || known[0] || data.buckets[0];
  const countWidths = Object.fromEntries(
    categories.map(([key]) => [
      key,
      Math.max(1, ...groups.map((row) => formatNumber(row.counts[key]).length)),
    ]),
  );
  return (
    <div ref={root} className="min-w-0" data-activity-graph="">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <p className="font-medium">{t("Recorded business activity")}</p>
        <p className="text-xs text-fg-muted">
          {formatNumber(groupSize * 30)} {t("minutes per bar")}
        </p>
      </div>
      <svg
        viewBox={`0 0 ${plotWidth} 255`}
        className="block w-full overflow-visible"
        role="group"
        aria-label={t("Activity over time")}
      >
        <defs>
          <pattern id="activity-gap" width="8" height="8" patternUnits="userSpaceOnUse">
            <path d="M0 8L8 0" stroke="currentColor" strokeOpacity=".12" />
          </pattern>
        </defs>
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line
              x1="52"
              x2={right}
              y1={210 - f * 160}
              y2={210 - f * 160}
              stroke="currentColor"
              opacity=".12"
            />
            <text x="42" y={214 - f * 160} textAnchor="end" fill="currentColor" fontSize="12">
              {formatNumber(Math.round(maximum * f))}
            </text>
          </g>
        ))}
        <rect
          x="52"
          y="35"
          width={Math.max(0, x(covered) - 52)}
          height="175"
          fill="url(#activity-gap)"
        />
        <rect
          x={x(observed)}
          y="35"
          width={Math.max(0, right - x(observed))}
          height="175"
          fill="url(#activity-gap)"
        />
        <path d={area} fill="var(--color-accent, #6254ff)" opacity=".09" />
        {known.map((row, i) => {
          const left = x(Math.max(covered, Date.parse(row.start))),
            right = x(Date.parse(row.end));
          return (
            <g key={row.start}>
              <rect
                x={left}
                y={210 - (total(row) / maximum) * 160}
                width={Math.max(0.5, right - left - 1)}
                height={Math.max(1, (total(row) / maximum) * 160)}
                fill="currentColor"
                className="text-accent"
                opacity={active?.start === row.start ? 1 : 0.65}
              />
              <rect
                data-activity-bucket=""
                x={left}
                y="35"
                width={Math.max(1, right - left)}
                height="175"
                fill="transparent"
                tabIndex={0}
                role="button"
                aria-label={`${formatDateTime(row.start)} – ${formatDateTime(row.end)}: ${formatNumber(total(row))} ${t("Recorded activities")}`}
                onMouseEnter={() => setHover(row)}
                onMouseLeave={() => setHover(null)}
                onFocus={() => setHover(row)}
                onBlur={() => setHover(null)}
                onClick={() => setSelected(row)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setSelected(row);
                  }
                  if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
                    event.preventDefault();
                    const next = Math.max(
                      0,
                      Math.min(known.length - 1, i + (event.key === "ArrowRight" ? 1 : -1)),
                    );
                    (
                      root.current?.querySelectorAll("[data-activity-bucket]")[next] as SVGElement
                    )?.focus();
                  }
                }}
              />
            </g>
          );
        })}
        <line
          pointerEvents="none"
          x1={right}
          x2={right}
          y1="28"
          y2="215"
          stroke="currentColor"
          className="text-accent"
          strokeDasharray="3 4"
        />
        <circle
          pointerEvents="none"
          cx={right}
          cy="28"
          r="4"
          fill="currentColor"
          className="text-accent"
        />
        <text x="52" y="241" fill="currentColor" fontSize="12">
          {formatDateTime(new Date(start).toISOString())}
        </text>
        <text x={right} y="241" textAnchor="end" fill="currentColor" fontSize="12">
          {t("Now")}
        </text>
      </svg>
      <div
        className="mt-3 grid min-h-16 border-t border-border-default py-3 text-[13px]"
        data-activity-summary=""
      >
        <div
          className={`col-start-1 row-start-1 ${active ? "" : "invisible"}`}
          aria-hidden={!active}
        >
          <p
            className={`mb-2 flex gap-x-1 font-medium tabular-nums ${width < 500 ? "flex-col" : "flex-row"}`}
          >
            <span className="whitespace-nowrap">{formatDateTime(preview.start)} –</span>
            <span className="whitespace-nowrap">{formatDateTime(preview.end)}</span>
          </p>
          <div className="flex flex-wrap gap-x-5 gap-y-1">
            {categories.map(([key, label]) => (
              <span key={key} className="whitespace-nowrap">
                {t(label)}:{" "}
                <strong
                  className="inline-block tabular-nums"
                  style={{ minWidth: `${countWidths[key]}ch` }}
                >
                  {formatNumber(preview.counts[key])}
                </strong>
              </span>
            ))}
          </div>
        </div>
        <div
          className={`col-start-1 row-start-1 ${active ? "invisible" : ""}`}
          aria-hidden={!!active}
        >
          <p>{t("Hover or select a bar to explore what happened.")}</p>
          <p className="mt-1 text-xs text-fg-muted">
            {t("Hatched areas have no observed data. The latest bar is still filling.")}
          </p>
        </div>
      </div>
      <p className="mt-3 text-xs leading-relaxed text-fg-muted">
        {t(
          "Counts new orders, reservations, stock movements and other documents. Technical processing steps are excluded.",
        )}
      </p>
      {stale && (
        <p className="mt-3 text-sm" role="status">
          {t("Updates paused. Showing the last available activity.")}
        </p>
      )}
      {selected && (
        <div className="mt-4 border-t border-border-default pt-4">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-medium">{t("Activity in this interval")}</h3>
            <button className="br-btn" onClick={() => setSelected(null)}>
              {t("Close")}
            </button>
          </div>
          {loading ? (
            <p className="mt-3">
              <ReadLine />
            </p>
          ) : detailError ? (
            <p role="alert" className="mt-3">
              {t("Could not load this view")}
            </p>
          ) : (
            <>
              <ul className="mt-3 max-h-60 overflow-y-auto">
                {events.map((event) => (
                  <li key={event.id}>
                    <button
                      className="my-1 flex w-full flex-wrap justify-between gap-2 rounded-lg p-2 text-left hover:bg-surface-muted"
                      onClick={() => setTarget({ kind: "business_event", id: event.id })}
                    >
                      <span>{eventTitle(event)}</span>
                      <time className="text-xs text-fg-muted">
                        {formatDateTime(event.recorded_at)}
                      </time>
                    </button>
                  </li>
                ))}
              </ul>
              {!events.length && (
                <p className="mt-3">{t("No recorded activity in this interval.")}</p>
              )}
              {more && (
                <p className="mt-3 text-xs text-fg-muted">
                  {t("Showing the latest 50 matching events. Use all activity for more history.")}
                </p>
              )}
            </>
          )}
        </div>
      )}
      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </div>
  );
}
