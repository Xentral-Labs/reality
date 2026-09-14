import { ZoomIn, ZoomOut } from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { api, type TimelineEvent } from "../api";
import { formatDate, formatTime, t } from "../localization";
import { Inspector } from "./Inspector";
import { eventTitle } from "./ActivityDrawer";
import { ObjectGraph } from "./ObjectGraph";
import { buildFlightGraph, flightLanes, kindLabels, type FlightNode } from "./flightRecorderGraph";
import {
  DAY,
  HOUR,
  HOUR6,
  INTERVALS,
  MINUTE5,
  QUARTER,
  WEEK,
  layoutRecorder,
  type RecorderInterval,
} from "./flightRecorderLayout";

const LABEL = 112,
  HEADER = 58,
  DOT = 12,
  GAP = 6,
  ROWS = 4,
  COLUMN = 48,
  PAD = 8,
  REFRESH_MS = 30_000,
  TICK_MS = 60_000;
// Lane colours come from theme tokens so dots hold contrast in both themes.
const laneColor = (lane: number) => `var(--lane-${flightLanes[lane].toLowerCase()})`;
const intervalText: Record<RecorderInterval, string> = {
  [MINUTE5]: "Columns are five-minute recording intervals.",
  [QUARTER]: "Columns are 15-minute recording intervals.",
  [HOUR]: "Columns are one-hour recording intervals.",
  [HOUR6]: "Columns are six-hour recording intervals.",
  [DAY]: "Columns are one-day recording intervals.",
  [WEEK]: "Columns are one-week recording intervals.",
};
type Target = { kind: string; id: string };
export function FlightRecorder({ tenant }: { tenant: string }) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [more, setMore] = useState(true);
  const [target, setTarget] = useState<Target | null>(null);
  const [selected, select] = useState<string | null>(null);
  const [selectedPulse, selectPulse] = useState<string | null>(null);
  const [viewport, setViewport] = useState({ left: 0, top: 0, width: 0, height: 0 });
  const [now, setNow] = useState(() => Date.now());
  const [zoom, setZoom] = useState<RecorderInterval | null>(null);
  const generation = useRef(0),
    busy = useRef(false);
  const cursor = useRef<number | undefined>(undefined);
  const band = useRef<HTMLDivElement>(null);
  const constellation = useRef<HTMLDivElement>(null);
  const initialized = useRef(false);
  // Older pages re-run the layout, so the viewed position is anchored to an instant, not a pixel.
  const anchor = useRef<{ time: number; offset: number } | null>(null);
  const timeAt = useRef<(x: number) => number>(() => 0);
  const load = useCallback(async () => {
    if (busy.current) return;
    busy.current = true;
    const version = generation.current;
    setLoading(true);
    setError(false);
    try {
      const data = await api.timeline(tenant, "", "", "", 0, "", cursor.current);
      if (generation.current !== version) return;
      if (band.current)
        anchor.current = { time: timeAt.current(band.current.scrollLeft), offset: 0 };
      setEvents((previous) => [
        ...new Map([...previous, ...data.events].map((event) => [event.id, event])).values(),
      ]);
      const next = data.events.at(-1)?.sequence;
      setMore(
        data.has_more &&
          next !== undefined &&
          (cursor.current === undefined || next < cursor.current),
      );
      cursor.current = next;
    } catch {
      if (generation.current === version) setError(true);
    } finally {
      if (generation.current === version) {
        busy.current = false;
        setLoading(false);
      }
    }
  }, [tenant]);
  useEffect(() => {
    void load();
    return () => {
      generation.current++;
      busy.current = false;
    };
  }, [load]);
  // The paper keeps running: the now mark advances and newly recorded events are appended.
  useEffect(() => {
    const tick = setInterval(() => setNow(Date.now()), TICK_MS);
    const refresh = setInterval(() => {
      if (document.visibilityState !== "visible" || busy.current) return;
      const version = generation.current;
      api
        .timeline(tenant, "", "", "", 0, "")
        .then((data) => {
          if (generation.current !== version) return;
          setEvents((previous) => [
            ...new Map([...previous, ...data.events].map((event) => [event.id, event])).values(),
          ]);
          setNow(Date.now());
        })
        .catch(() => undefined);
    }, REFRESH_MS);
    return () => {
      clearInterval(tick);
      clearInterval(refresh);
    };
  }, [tenant]);

  const graph = useMemo(() => buildFlightGraph(events), [events]);
  const layout = useMemo(
    () =>
      layoutRecorder(graph, {
        label: LABEL,
        header: HEADER,
        dot: DOT,
        gap: GAP,
        rows: ROWS,
        column: COLUMN,
        pad: PAD,
        now,
        minColumns: Math.max(1, Math.ceil((viewport.width - LABEL - 32) / COLUMN)),
        interval: zoom ?? undefined,
        aggregate: true,
      }),
    [graph, now, viewport.width, zoom],
  );
  // Zooming changes the raster; the instant in the middle of the view stays in the middle.
  const zoomBy = (steps: number) => {
    const index = INTERVALS.indexOf(layout.interval) + steps;
    if (index < 0 || index >= INTERVALS.length) return;
    if (band.current) {
      const offset = band.current.clientWidth / 2;
      anchor.current = { time: layout.timeAt(band.current.scrollLeft + offset), offset };
    }
    setZoom(INTERVALS[index]);
  };
  timeAt.current = layout.timeAt;
  const { width, height } = layout;
  const byKey = new Map(graph.nodes.map((node) => [node.key, node]));
  const current = selected ? byKey.get(selected) : null;
  const graphKey = selected;
  const graphRecord = graphKey ? byKey.get(graphKey) : null;
  const pulse = selectedPulse
    ? (layout.pulses.find((candidate) => candidate.key === selectedPulse) ?? null)
    : null;
  const pulseMembers = pulse ? pulse.members : [];
  useEffect(() => {
    if (selectedPulse && !pulse) {
      selectPulse(null);
      select(null);
    }
  }, [pulse, selectedPulse]);
  const syncViewport = useCallback(() => {
    const element = band.current;
    if (element)
      setViewport({
        left: element.scrollLeft,
        top: element.scrollTop,
        width: element.clientWidth,
        height: element.clientHeight,
      });
  }, []);
  useLayoutEffect(() => {
    const element = band.current;
    if (!element) return;
    const observer = new ResizeObserver(syncViewport);
    observer.observe(element);
    syncViewport();
    return () => observer.disconnect();
  }, [events.length, height, syncViewport]);
  const openPulseMember = (key: string) => {
    select(key);
    requestAnimationFrame(() =>
      constellation.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }),
    );
  };
  const closePulse = useCallback(() => {
    select(null);
    selectPulse(null);
  }, []);
  useEffect(() => {
    if (!selectedPulse) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") closePulse();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [closePulse, selectedPulse]);
  useLayoutEffect(() => {
    if (!band.current || !events.length) return;
    if (!initialized.current) {
      // Open with the newest record in view; the now mark follows when the gap fits the band.
      const newest = Math.max(
        0,
        ...graph.nodes
          .filter((node) => node.event && !node.referenceOnly)
          .map((node) => Date.parse(node.event!.recorded_at)),
      );
      band.current.scrollLeft = newest
        ? Math.max(0, layout.xAt(newest) - LABEL - COLUMN)
        : band.current.scrollWidth;
      initialized.current = true;
    } else if (anchor.current) {
      band.current.scrollLeft = Math.max(
        0,
        layout.xAt(anchor.current.time) - anchor.current.offset,
      );
    }
    anchor.current = null;
  }, [events, layout, graph]);
  // The view may open at the left edge of the paper or a compact page may not overflow;
  // keep loading older history until the band scrolls away from the edge or history ends.
  useLayoutEffect(() => {
    const element = band.current;
    if (!element || loading || error || !more || !events.length) return;
    if (
      element.scrollWidth <= element.clientWidth ||
      element.scrollLeft < layout.referenceWidth + 80
    )
      void load();
  }, [events, loading, error, more, load, layout]);
  const older = () => {
    if (
      !loading &&
      !error &&
      more &&
      initialized.current &&
      band.current &&
      band.current.scrollLeft < layout.referenceWidth + 80
    )
      void load();
  };
  const title = (node: FlightNode) =>
    node.kind === "business_event" && node.event
      ? eventTitle(node.event)
      : node.label || t(kindLabels[node.kind] || node.kind);
  const columnLabel = (start: number) => {
    const iso = new Date(start).toISOString();
    return layout.interval >= DAY ? formatDate(iso) : formatTime(iso);
  };
  return (
    <section
      className="min-w-0 overflow-hidden rounded-xl border border-border-default bg-surface"
      aria-label={t("Timeline")}
    >
      <div className="min-w-0" data-context-layout="stacked">
        <div className="min-w-0" data-recorder-pane>
          <div
            className="flex flex-col gap-3 border-b border-border-default px-4 py-3"
            data-recorder-header
          >
            <div className="flex min-w-0 flex-wrap items-center gap-x-5 gap-y-1 text-xs text-fg-muted">
              <span>
                {t("Recorded events")}: {events.length}
              </span>
              <span>{t(intervalText[layout.interval])}</span>
              <span>{t("Records in the same interval combine into one pulse per lane.")}</span>
              <span>
                {t("Scroll left for older history. Click a node to follow its connections.")}
              </span>
            </div>
            <div className="flex flex-wrap gap-2" data-recorder-controls>
              <button
                className="br-btn"
                disabled={loading || (!more && !error)}
                onClick={() => void load()}
              >
                {t(loading ? "Loading…" : error ? "Retry" : "Load older events")}
              </button>
              <button
                className="br-btn"
                disabled={!events.length}
                onClick={() => {
                  if (band.current) band.current.scrollLeft = band.current.scrollWidth;
                }}
              >
                {t("Latest events")}
              </button>
              <button
                className="br-btn"
                aria-label={t("Zoom in")}
                title={t("Zoom in")}
                disabled={!events.length || INTERVALS.indexOf(layout.interval) === 0}
                onClick={() => zoomBy(-1)}
                data-recorder-zoom="in"
              >
                <ZoomIn size={16} aria-hidden="true" />
              </button>
              <button
                className="br-btn"
                aria-label={t("Zoom out")}
                title={t("Zoom out")}
                disabled={
                  !events.length || INTERVALS.indexOf(layout.interval) === INTERVALS.length - 1
                }
                onClick={() => zoomBy(1)}
                data-recorder-zoom="out"
              >
                <ZoomOut size={16} aria-hidden="true" />
              </button>
            </div>
          </div>
          {error && (
            <p role="alert" className="px-4 py-3 text-sm">
              {t("Activity could not be loaded.")}
            </p>
          )}
          {!loading && !error && !events.length && (
            <p className="p-8 text-sm text-fg-muted">{t("No recorded events yet.")}</p>
          )}
          {events.length > 0 && (
            <>
              <div
                ref={band}
                tabIndex={0}
                aria-label={t("Event history")}
                onScroll={() => {
                  syncViewport();
                  older();
                }}
                className="relative max-h-[72vh] overflow-auto overscroll-contain"
                data-flight-band
              >
                <div className="relative" style={{ width, height }}>
                  {flightLanes.map((lane, index) => (
                    <div
                      key={lane}
                      className="absolute left-0 w-full border-b border-border-default"
                      style={{ top: layout.laneTops[index], height: layout.laneHeights[index] }}
                    />
                  ))}
                  <svg
                    width={width}
                    height={height}
                    className="pointer-events-none absolute inset-0 text-fg-muted"
                    aria-hidden="true"
                  >
                    {layout.columns.map((column) => (
                      <line
                        key={column.index}
                        x1={column.x}
                        x2={column.x}
                        y1={HEADER}
                        y2={height}
                        stroke="currentColor"
                        opacity={column.label || column.dayStart ? 0.18 : 0.07}
                      />
                    ))}
                    {flightLanes.map((lane, index) => (
                      <line
                        key={`trace-${lane}`}
                        x1={LABEL}
                        x2={width}
                        y1={layout.laneTops[index] + layout.laneHeights[index] / 2}
                        y2={layout.laneTops[index] + layout.laneHeights[index] / 2}
                        stroke="currentColor"
                        opacity="0.18"
                      />
                    ))}
                    <line
                      x1={layout.xAt(layout.now)}
                      x2={layout.xAt(layout.now)}
                      y1={HEADER - 8}
                      y2={height}
                      stroke="currentColor"
                      className="text-accent"
                      strokeWidth={1.5}
                      data-recorder-now
                    />
                  </svg>
                  {layout.pulses.map((item) => {
                    const active = !selectedPulse || selectedPulse === item.key;
                    const interval = item.reference
                      ? t("Earlier reference")
                      : `${columnLabel(layout.columns[item.column].start)} · ${t(intervalText[layout.interval])}`;
                    return (
                      <button
                        key={item.key}
                        data-recorder-pulse={item.key}
                        aria-pressed={selectedPulse === item.key}
                        aria-label={`${t("Activity pulse")} · ${t(flightLanes[item.lane])} · ${item.count} ${t("records in this interval")} · ${interval}`}
                        title={`${t(flightLanes[item.lane])} · ${item.count} ${t("records in this interval")} · ${interval}`}
                        onClick={() => {
                          selectPulse(selectedPulse === item.key ? null : item.key);
                          select(null);
                          if (selectedPulse !== item.key)
                            requestAnimationFrame(() =>
                              constellation.current?.scrollIntoView({
                                behavior: "smooth",
                                block: "nearest",
                              }),
                            );
                        }}
                        className="absolute z-10 flex items-center justify-center rounded-full border-2 border-surface text-[10px] font-semibold text-white shadow-sm outline-offset-2 transition hover:scale-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent aria-pressed:ring-2 aria-pressed:ring-accent aria-pressed:ring-offset-2 aria-pressed:ring-offset-surface"
                        style={{
                          left: item.x,
                          top: item.y,
                          width: item.diameter,
                          height: item.diameter,
                          opacity: active ? item.opacity : 0.22,
                          backgroundColor: laneColor(item.lane),
                        }}
                      >
                        {item.count > 1 ? item.count : ""}
                      </button>
                    );
                  })}
                  <div
                    className="pointer-events-none sticky left-0 top-0 z-20"
                    style={{ width: LABEL, height }}
                  >
                    <div
                      className="absolute left-0 top-0 flex items-center border-b border-r border-border-default bg-surface px-3 text-xs font-medium text-fg-muted"
                      style={{ width: LABEL, height: HEADER }}
                    >
                      {t("Recorded at")} →
                    </div>
                    {flightLanes.map((lane, index) => (
                      <div
                        key={lane}
                        className="absolute left-0 flex items-center gap-2 border-b border-r border-border-default bg-surface px-3"
                        style={{
                          top: layout.laneTops[index],
                          width: LABEL,
                          height: layout.laneHeights[index],
                        }}
                      >
                        <span
                          className="inline-block h-2 w-2 shrink-0 rounded-full"
                          style={{ backgroundColor: laneColor(index) }}
                          aria-hidden="true"
                        />
                        <h3 className="truncate text-xs font-semibold">{t(lane)}</h3>
                      </div>
                    ))}
                  </div>
                  <div
                    className="pointer-events-none absolute left-0 top-0 border-b border-border-default bg-surface"
                    style={{ width, height: HEADER }}
                  >
                    {layout.referenceWidth > 0 && (
                      <div
                        className="absolute top-0 flex items-center overflow-hidden px-2 text-[10px] text-fg-muted"
                        style={{ left: LABEL, width: layout.referenceWidth, height: HEADER }}
                        title={t("Earlier reference")}
                      >
                        {layout.referenceWidth >= 90 ? t("Earlier reference") : "…"}
                      </div>
                    )}
                    <div
                      className="absolute top-0 flex items-center whitespace-nowrap pl-1.5 text-xs font-medium text-accent"
                      style={{ left: layout.xAt(layout.now), height: HEADER }}
                    >
                      {t("Now")} · {formatTime(new Date(layout.now).toISOString())}
                    </div>
                    {layout.columns.map(
                      (column) =>
                        (column.label || (column.dayStart && layout.interval < DAY)) && (
                          <div
                            key={column.index}
                            className="absolute top-0 flex flex-col justify-center whitespace-nowrap pl-1.5 text-xs text-fg-muted"
                            style={{ left: column.x, height: HEADER }}
                          >
                            {column.label && (
                              <time dateTime={new Date(column.start).toISOString()}>
                                {columnLabel(column.start)}
                              </time>
                            )}
                            {column.dayStart && layout.interval < DAY && (
                              <span className="text-[10px]">
                                {formatDate(new Date(column.start).toISOString())}
                              </span>
                            )}
                          </div>
                        ),
                    )}
                  </div>
                </div>
              </div>
              <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border-default bg-surface px-4 py-3 text-xs text-fg-muted">
                {!more && <span>{t("Beginning of recorded history")}</span>}
              </footer>
            </>
          )}
        </div>
        {pulse && (
          <div
            ref={constellation}
            className="min-w-0 border-t border-border-default"
            data-context-detail-shell
            data-relationship-pane
          >
            <div
              className="flex flex-wrap items-start justify-between gap-3 border-b border-border-default bg-surface-subtle px-4 py-3"
              data-relationship-header
            >
              {!graphRecord ? (
                <>
                  <div>
                    <span className="block text-[10px] font-medium uppercase tracking-wide text-accent">
                      {t("Activity pulse")} · {t(flightLanes[pulse.lane])}
                    </span>
                    <strong className="block text-sm">
                      {pulse.count} {t("records in this interval")}
                    </strong>
                    <p className="text-xs text-fg-muted">
                      {t("Choose a record to trace its connections.")}
                    </p>
                  </div>
                  <button
                    className="br-btn w-fit text-xs"
                    onClick={closePulse}
                    aria-label={t("Clear pulse")}
                    title={t("Clear pulse")}
                    data-close-focus-mode
                  >
                    × {t("Clear pulse")}
                  </button>
                </>
              ) : (
                <>
                  <div className="min-w-0">
                    <span className="block text-[10px] font-medium uppercase tracking-wide text-accent">
                      {t("Relationship trace")} ·{" "}
                      {t(kindLabels[graphRecord.kind] || graphRecord.kind)}
                    </span>
                    <strong className="block truncate text-sm" data-localization="original">
                      {title(graphRecord)}
                    </strong>
                    <p className="text-xs text-fg-muted">
                      {t("Open a linked record to continue the trace.")}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button className="br-btn text-xs" onClick={() => select(null)}>
                      ← {t("Back to pulse")}
                    </button>
                    <button
                      className="br-btn text-xs"
                      onClick={() => setTarget({ kind: graphRecord.kind, id: graphRecord.id })}
                    >
                      {t("Details")}
                    </button>
                    <button
                      className="br-btn text-xs"
                      onClick={closePulse}
                      aria-label={t("Clear pulse")}
                      title={t("Clear pulse")}
                      data-close-focus-mode
                    >
                      ×
                    </button>
                  </div>
                </>
              )}
            </div>
            {!graphRecord && (
              <div className="overflow-x-auto" data-pulse-record-list>
                <table className="w-full border-collapse text-left text-xs">
                  <thead className="bg-surface-subtle text-[10px] uppercase tracking-wide text-fg-muted">
                    <tr>
                      <th className="px-4 py-2 font-medium">{t("Record type")}</th>
                      <th className="px-4 py-2 font-medium">{t("Business record")}</th>
                      <th className="px-4 py-2 font-medium">{t("Recorded at")}</th>
                      <th className="px-4 py-2 text-right font-medium">{t("Details")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pulseMembers.map((key) => {
                      const node = byKey.get(key);
                      if (!node) return null;
                      const label = `${t(kindLabels[node.kind] || node.kind)} · ${title(node)}`;
                      return (
                        <tr
                          key={key}
                          className="border-t border-border-default hover:bg-accent-soft"
                        >
                          <td className="whitespace-nowrap px-4 py-2.5 text-fg-muted">
                            {t(kindLabels[node.kind] || node.kind)}
                          </td>
                          <td className="min-w-52 px-4 py-2.5">
                            <strong data-pulse-record-label data-localization="original">
                              {title(node)}
                            </strong>
                            <span
                              className="mt-0.5 block max-w-80 truncate font-mono text-[10px] text-fg-muted"
                              title={node.id}
                            >
                              {node.id}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-4 py-2.5 text-fg-muted">
                            {node.event
                              ? `${formatDate(node.event.recorded_at)} · ${formatTime(node.event.recorded_at)}`
                              : t("Earlier reference")}
                          </td>
                          <td className="px-4 py-2 text-right">
                            <button
                              className="br-btn whitespace-nowrap text-xs"
                              aria-label={label}
                              title={label}
                              onClick={() => openPulseMember(key)}
                              data-pulse-record={key}
                              data-open-relationship-trace
                            >
                              {t("Open")} →
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
            {graphRecord && (
              <div className="p-3" data-flight-selection>
                <ObjectGraph
                  key={`${tenant}:${graphRecord.kind}:${graphRecord.id}`}
                  tenant={tenant}
                  root={{ kind: graphRecord.kind, id: graphRecord.id }}
                  variant="trace"
                />
              </div>
            )}
          </div>
        )}
      </div>
      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </section>
  );
}
