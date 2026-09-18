import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, Search, X } from "lucide-react";
import {
  api,
  type JourneyEdge,
  type JourneyOrder,
  type JourneyRef,
  type TimelineEvent,
} from "../api";
import {
  displayDayBounds,
  formatDate,
  formatDateTime,
  formatNumber,
  formatTime,
  t,
} from "../localization";
import { Inspector } from "./Inspector";
import { ReadLine, ReadState } from "./ReadState";
import { eventTitle } from "./ActivityDrawer";
import { kindLabels } from "./flightRecorderGraph";
import {
  journeyLanes,
  journeyLaneKind,
  journeyRange,
  layoutJourney,
  mergeJourneyEvents,
  type JourneyRange,
} from "./orderJourneyLayout";

const refKey = (ref: JourneyRef) => `${ref.kind}:${ref.id}`;
const eventRef = (event: TimelineEvent) => ({ kind: event.subject_type, id: event.subject_id });
const edgeKey = (edge: JourneyEdge) => `${refKey(edge.from)}|${refKey(edge.to)}|${edge.label}`;

export function OrderJourneyTimeline({ tenant }: { tenant: string }) {
  const [order, setOrder] = useState<JourneyOrder | null>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [revision, retry] = useState(0);
  const [search, setSearch] = useState<{
    orders: JourneyOrder[];
    has_more: boolean;
    error?: boolean;
    ready?: boolean;
  }>({ orders: [], has_more: false });
  const picker = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setSearch({ orders: [], has_more: false });
    const timer = setTimeout(() => {
      api
        .journeyOrders(tenant, query, controller.signal)
        .then((data) => {
          if (!controller.signal.aborted) setSearch({ ...data, ready: true });
        })
        .catch(() => {
          if (!controller.signal.aborted)
            setSearch({ orders: [], has_more: false, error: true, ready: true });
        });
    }, 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [tenant, query, open, revision]);
  return (
    <section data-journey-timeline className="journey-workbench">
      <div className="journey-toolbar">
        <div
          className="relative min-w-0"
          ref={picker}
          onBlur={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
          }}
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              setOpen(false);
              picker.current?.querySelector<HTMLButtonElement>("button")?.focus();
            }
          }}
        >
          <button
            className="br-btn max-w-full"
            aria-label={t("Choose sales order")}
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          >
            <Search size={15} />
            <span className="truncate" data-original-content>
              {order ? order.number : t("Choose sales order")}
            </span>
            <ChevronDown size={14} />
          </button>
          {open && (
            <div className="journey-picker">
              <label className="text-xs text-fg-muted" htmlFor="journey-search">
                {t("Search by order number or customer")}
              </label>
              <input
                autoFocus
                id="journey-search"
                className="br-control mt-2"
                value={query}
                maxLength={200}
                onChange={(e) => setQuery(e.target.value)}
              />
              {!search.ready && <ReadState loading rows={2} />}
              {search.error ? (
                <div role="alert" className="p-3 text-sm">
                  {t("Orders could not be loaded.")}{" "}
                  <button className="br-btn" onClick={() => retry((n) => n + 1)}>
                    {t("Retry")}
                  </button>
                </div>
              ) : (
                search.orders.map((row) => (
                  <button
                    className="journey-order"
                    key={row.id}
                    onClick={() => {
                      setOrder(row);
                      setOpen(false);
                      picker.current?.querySelector<HTMLButtonElement>("button")?.focus();
                    }}
                  >
                    <strong data-original-content>{row.number}</strong>
                    <span data-original-content>{row.party}</span>
                  </button>
                ))
              )}
              {search.ready && !search.error && !search.orders.length && (
                <p className="p-3 text-sm text-fg-muted">{t("No matching sales orders.")}</p>
              )}
              {search.has_more && (
                <p className="p-3 text-xs text-fg-muted">
                  {t("Refine the search to find more orders.")}
                </p>
              )}
            </div>
          )}
        </div>
        <button className="br-btn" aria-pressed={!order} onClick={() => setOrder(null)}>
          {t("All activity")}
        </button>
        {order && (
          <span className="min-w-0 truncate text-sm text-fg-muted" data-original-content>
            {order.party}
          </span>
        )}
      </div>
      <JourneyBody key={`${tenant}:${order?.id || "all"}`} tenant={tenant} order={order} />
    </section>
  );
}

function JourneyBody({ tenant, order }: { tenant: string; order: JourneyOrder | null }) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [edges, setEdges] = useState<JourneyEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [more, setMore] = useState(false);
  const [newer, setNewer] = useState(false);
  const [linksTruncated, setLinksTruncated] = useState(false);
  const [range, setRange] = useState<JourneyRange | null>(null);
  const [mode, setMode] = useState("fit");
  const [selected, select] = useState<string | null>(null);
  const [cluster, setCluster] = useState<string[]>([]);
  const [target, setTarget] = useState<JourneyRef | null>(null);
  const [width, setWidth] = useState(700);
  const canvas = useRef<HTMLDivElement>(null);
  const alive = useRef(false),
    busy = useRef(false),
    initialized = useRef(false);
  const held = useRef<TimelineEvent[]>([]);
  const controller = useRef<AbortController | null>(null);
  const failedMode = useRef<"initial" | "older" | "refresh">("initial");
  const load = useCallback(
    async (requestMode: "initial" | "older" | "refresh") => {
      if (busy.current) return;
      busy.current = true;
      setLoading(true);
      setError(false);
      failedMode.current = requestMode;
      const abort = new AbortController();
      controller.current = abort;
      const sequences = held.current.map((e) => e.sequence);
      const cursor =
        requestMode === "older" && sequences.length
          ? { before: Math.min(...sequences) }
          : requestMode === "refresh" && sequences.length
            ? { after: Math.max(...sequences) }
            : {};
      try {
        const page = await api.journey(tenant, order?.id || "", cursor, abort.signal);
        if (!alive.current || abort.signal.aborted) return;
        const merged = mergeJourneyEvents(held.current, page.events);
        held.current = merged;
        setEvents(merged);
        if (page.links_truncated) setLinksTruncated(true);
        setEdges((previous) => [
          ...new Map(
            [...previous, ...(page.edges || [])].map((edge) => [edgeKey(edge), edge]),
          ).values(),
        ]);
        if (requestMode === "refresh" && sequences.length) setNewer(page.has_more);
        else setMore(page.has_more);
        if (!initialized.current) {
          setRange(journeyRange(merged));
          initialized.current = true;
        }
      } catch {
        if (alive.current && !abort.signal.aborted) setError(true);
      } finally {
        if (alive.current && !abort.signal.aborted) {
          busy.current = false;
          setLoading(false);
        }
      }
    },
    [tenant, order?.id],
  );
  useEffect(() => {
    alive.current = true;
    void load("initial");
    const timer = setInterval(() => {
      if (document.visibilityState === "visible")
        void load(initialized.current ? "refresh" : "initial");
    }, 30_000);
    return () => {
      alive.current = false;
      busy.current = false;
      controller.current?.abort();
      clearInterval(timer);
    };
  }, [load]);
  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const observer = new ResizeObserver(() => setWidth(Math.max(600, element.clientWidth) - 140));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const activeRange = range || journeyRange([]);
  const points = useMemo(
    () => layoutJourney(events, activeRange, width),
    [events, activeRange.start, activeRange.end, width],
  );
  const pointByEvent = new Map(
    points.flatMap((point) => point.events.map((event) => [event.id, point] as const)),
  );
  const chosen = events.find((e) => e.id === selected);
  const connections = chosen
    ? edges.filter(
        (edge) =>
          refKey(edge.from) === refKey(eventRef(chosen)) ||
          refKey(edge.to) === refKey(eventRef(chosen)),
      )
    : [];
  const timelineEdges = useMemo(() => {
    const bySubject = new Map<string, (typeof points)[number]>();
    for (const point of points)
      for (const event of point.events)
        if (!bySubject.has(refKey(eventRef(event)))) bySubject.set(refKey(eventRef(event)), point);
    return edges.flatMap((edge) => {
      const from = bySubject.get(refKey(edge.from)),
        to = bySubject.get(refKey(edge.to));
      return from && to && from.key !== to.key ? [{ ...edge, a: from, b: to }] : [];
    });
  }, [points, edges]);
  const chooseRange = (value: string) => {
    setMode(value);
    setCluster([]);
    if (value === "fit") {
      setRange(journeyRange(events));
      return;
    }
    if (value === "today") {
      setRange(displayDayBounds());
      return;
    }
    const end = events.length
      ? Math.max(...events.map((e) => Date.parse(e.recorded_at)))
      : Date.now();
    setRange({ start: end - (value === "15m" ? 15 : 60) * 60_000, end: end + 1000 });
  };
  const clear = () => {
    select(null);
    setCluster([]);
  };
  const pin = (event: TimelineEvent) => {
    select(event.id);
    setCluster([]);
  };
  return (
    <div
      onKeyDown={(e) => {
        if (e.key === "Escape" && !target) clear();
      }}
    >
      <div className="journey-rangebar">
        <div className="journey-periods" aria-label={t("Time range")}>
          {[
            ["15m", "15 minutes"],
            ["1h", "1 hour"],
            ["today", "Today"],
            ["fit", "Fit history"],
          ].map(([value, label]) => (
            <button key={value} aria-pressed={mode === value} onClick={() => chooseRange(value)}>
              {t(label)}
            </button>
          ))}
        </div>
        <button
          className="br-btn"
          disabled={loading}
          onClick={() => void load(initialized.current ? "refresh" : "initial")}
        >
          {t("Refresh")}
        </button>
        {more && (
          <button className="br-btn" disabled={loading} onClick={() => void load("older")}>
            {t("Load older events")}
          </button>
        )}
      </div>
      {error && (
        <div className="journey-notice" role="alert">
          {t("History could not be loaded.")}{" "}
          <button className="br-btn" onClick={() => void load(failedMode.current)}>
            {t("Retry")}
          </button>
        </div>
      )}
      {loading && <ReadLine />}
      {newer && (
        <div className="journey-notice">
          {t("More new events are available.")}{" "}
          <button className="br-btn" disabled={loading} onClick={() => void load("refresh")}>
            {t("Load newer events")}
          </button>
        </div>
      )}
      <div className="journey-layout">
        <div className="min-w-0">
          <div className="journey-chart" ref={canvas}>
            <div className="journey-chart-heading">
              <span>{t("Recorded at")}</span>
              <span>
                {formatDateTime(new Date(activeRange.start).toISOString())} –{" "}
                {formatDateTime(new Date(activeRange.end).toISOString())}
              </span>
            </div>
            <div className="journey-chart-scroll">
              <div className="journey-paper" style={{ width: width + 140, height: 430 }}>
                <div className="journey-axis" style={{ left: 140, width }}>
                  {Array.from({ length: 5 }, (_, i) => {
                    const time =
                      activeRange.start + ((activeRange.end - activeRange.start) * i) / 4;
                    return (
                      <span key={i} style={{ left: 20 + ((width - 40) * i) / 4 }}>
                        {activeRange.end - activeRange.start > 86_400_000
                          ? formatDate(new Date(time).toISOString())
                          : formatTime(new Date(time).toISOString())}
                      </span>
                    );
                  })}
                </div>
                {journeyLanes.map((lane, index) => (
                  <div
                    key={lane.kind}
                    data-journey-lane={lane.kind}
                    className="journey-lane"
                    style={{ top: 44 + index * 76, height: 76 }}
                  >
                    <div className="journey-lane-label">
                      <strong>
                        <i style={{ background: lane.color }} />
                        {t(lane.label)}
                      </strong>
                      <span>{t(lane.caption)}</span>
                    </div>
                    <div className="journey-track" style={{ left: 140, width }} />
                  </div>
                ))}
                <svg
                  className="journey-lines"
                  style={{ left: 140 }}
                  width={width}
                  height={430}
                  aria-hidden="true"
                >
                  {Array.from({ length: 5 }, (_, i) => (
                    <line
                      key={i}
                      x1={20 + ((width - 40) * i) / 4}
                      x2={20 + ((width - 40) * i) / 4}
                      y1={44}
                      y2={424}
                      className="journey-gridline"
                    />
                  ))}
                  {timelineEdges.map((edge) => (
                    <path
                      data-journey-edge
                      key={edgeKey(edge)}
                      d={`M ${edge.a.x} ${82 + edge.a.lane * 76} C ${(edge.a.x + edge.b.x) / 2} ${82 + edge.a.lane * 76}, ${(edge.a.x + edge.b.x) / 2} ${82 + edge.b.lane * 76}, ${edge.b.x} ${82 + edge.b.lane * 76}`}
                      className={`journey-edge ${chosen && (refKey(edge.from) === refKey(eventRef(chosen)) || refKey(edge.to) === refKey(eventRef(chosen))) ? "is-selected" : ""}`}
                    />
                  ))}
                </svg>
                {points.map((point) => {
                  const single = point.events.length === 1,
                    event = point.events[0],
                    active =
                      point.events.some((e) => e.id === selected) ||
                      point.events.some((e) => cluster.includes(e.id));
                  return (
                    <button
                      key={point.key}
                      data-journey-event={single ? event.id : undefined}
                      data-journey-cluster={single ? undefined : point.key}
                      className={`journey-point${active ? " is-selected" : ""}${single ? "" : " is-cluster"}`}
                      style={{
                        left: 140 + point.x,
                        top: 82 + point.lane * 76,
                        background: journeyLanes[point.lane].color,
                      }}
                      aria-pressed={active}
                      aria-label={
                        single
                          ? `${eventTitle(event)} · ${formatTime(event.recorded_at, true)}`
                          : `${t(journeyLanes[point.lane].label)} · ${formatNumber(point.events.length)} · ${t("Recorded changes")}`
                      }
                      title={
                        single
                          ? `${eventTitle(event)} · ${event.business_detail}`
                          : `${formatNumber(point.events.length)} ${t("Recorded changes")}`
                      }
                      onClick={() =>
                        single ? pin(event) : setCluster(point.events.map((e) => e.id))
                      }
                    >
                      {!single && formatNumber(point.events.length)}
                    </button>
                  );
                })}
              </div>
            </div>
            {!loading && !events.length && (
              <p className="journey-empty">{t("No recorded changes for this selection.")}</p>
            )}
            {events.length > 0 && !points.length && (
              <div className="journey-empty">
                {t("No business events in this time range.")}{" "}
                <button className="br-btn" onClick={() => chooseRange("fit")}>
                  {t("Fit history")}
                </button>
              </div>
            )}
          </div>
          <div className="journey-footnote">
            <span>
              {formatNumber(events.length)} {t("Loaded events")}
            </span>
            <span>{t("Points show recorded changes. Lines show held record relationships.")}</span>
          </div>
          {more && (
            <p className="text-xs text-fg-muted mt-2">
              {t("Partial history. Load older events to see earlier changes.")}
            </p>
          )}
          {linksTruncated && (
            <p className="text-xs text-fg-muted mt-2">
              {t(
                "Some ledger links are not shown. Inspect the posting event for its full payload.",
              )}
            </p>
          )}
          {cluster.length > 0 && (
            <section className="journey-group" aria-label={t("Grouped changes")}>
              <div className="flex justify-between gap-2">
                <strong>{t("Grouped changes")}</strong>
                <button className="br-btn" aria-label={t("Close")} onClick={() => setCluster([])}>
                  <X size={14} />
                </button>
              </div>
              {events
                .filter((e) => cluster.includes(e.id))
                .map((event) => (
                  <button
                    key={event.id}
                    data-journey-cluster-member={event.id}
                    className="journey-group-member"
                    onClick={() => pin(event)}
                  >
                    <span>{eventTitle(event)}</span>
                    <span>{formatTime(event.recorded_at, true)}</span>
                    <small data-original-content>{event.business_detail}</small>
                  </button>
                ))}
            </section>
          )}
        </div>
        <aside className="journey-detail" aria-label={t("Recorded history")}>
          <div className="journey-detail-head">
            <div>
              <span className="text-xs text-fg-muted">
                {t(order ? "Sales order" : "All activity")}
              </span>
              <h2 data-original-content>{order?.number || t("Recorded history")}</h2>
              {order && <p data-original-content>{order.party}</p>}
            </div>
            {chosen && (
              <button className="br-btn" aria-label={t("Clear selection")} onClick={clear}>
                <X size={14} />
              </button>
            )}
          </div>
          {order && (
            <button
              className="journey-text-action"
              onClick={() => setTarget({ kind: "document", id: order.id })}
            >
              {t("Inspect order and source")}
            </button>
          )}
          {chosen && (
            <section className="journey-selected" data-journey-selection>
              <h3>{eventTitle(chosen)}</h3>
              <p className="text-sm break-words" data-original-content>
                {chosen.business_detail}
              </p>
              <dl>
                <dt>{t("Recorded at")}</dt>
                <dd>{formatDateTime(chosen.recorded_at)}</dd>
                <dt>{t("Occurred at")}</dt>
                <dd>{formatDateTime(chosen.occurred_at)}</dd>
              </dl>
              {!pointByEvent.has(chosen.id) && (
                <p className="text-xs text-fg-muted">
                  {t("Selected change is outside the plotted lanes or time range.")}
                </p>
              )}
              <div className="flex flex-wrap gap-2 mt-3">
                {kindLabels[chosen.subject_type] && chosen.subject_type !== "business_event" && (
                  <button className="br-btn" onClick={() => setTarget(eventRef(chosen))}>
                    {t("Inspect record")}
                  </button>
                )}
                <button
                  className="br-btn"
                  onClick={() => setTarget({ kind: "business_event", id: chosen.id })}
                >
                  {t("Inspect event")}
                </button>
              </div>
              {connections.length > 0 && (
                <div className="journey-connections">
                  <strong>{t("Record relationships")}</strong>
                  {connections.map((edge) => {
                    const other =
                      refKey(edge.from) === refKey(eventRef(chosen)) ? edge.to : edge.from;
                    return (
                      <button key={edgeKey(edge)} onClick={() => setTarget(other)}>
                        <span>
                          {t(edge.label)}
                          {t(edge.label) !== t(kindLabels[other.kind] || other.kind) && (
                            <> · {t(kindLabels[other.kind] || other.kind)}</>
                          )}
                        </span>
                        <small data-original-content>{other.id}</small>
                      </button>
                    );
                  })}
                </div>
              )}
            </section>
          )}
          {!chosen && (
            <p className="journey-hint">{t("Select a point to inspect its change and origin.")}</p>
          )}
          <ol className="journey-history">
            {[...events]
              .sort(
                (a, b) =>
                  Date.parse(a.recorded_at) - Date.parse(b.recorded_at) || a.sequence - b.sequence,
              )
              .map((event) => {
                const lane = journeyLanes.find(
                  (l) => l.kind === journeyLaneKind(event.subject_type),
                );
                return (
                  <li key={event.id}>
                    <button
                      data-journey-history={event.id}
                      className={selected === event.id ? "is-selected" : ""}
                      aria-pressed={selected === event.id}
                      onClick={() => pin(event)}
                    >
                      <i style={{ background: lane?.color || "var(--text-muted)" }} />
                      <time dateTime={event.recorded_at}>{formatDateTime(event.recorded_at)}</time>
                      <strong>{eventTitle(event)}</strong>
                      <span data-original-content>{event.business_detail}</span>
                    </button>
                  </li>
                );
              })}
          </ol>
        </aside>
      </div>
      {target && (
        <Inspector
          key={refKey(target)}
          tenant={tenant}
          target={target}
          close={() => setTarget(null)}
        />
      )}
    </div>
  );
}
