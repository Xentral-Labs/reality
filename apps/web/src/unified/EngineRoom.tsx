import { Pause, Play, Radio, RefreshCw, SkipBack, SkipForward, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { APIError, api, type Interaction, type InteractionEvent } from "../api";
import { currentLanguage, formatNumber, formatTime, t } from "../localization";
import { Inspector } from "./Inspector";
import { PreviewButton, TablePreview } from "./InlinePreview";
import { RegisterTable } from "./RegisterTable";
import { filterChips } from "./FilterChip";
import { RegisterToolbar, RegisterWorkbench } from "./RegisterWorkbench";
import {
  CHANNELS,
  KINDS,
  OUTCOMES,
  STAGES,
  emptyLiveFilter,
  COCKPIT_WINDOW_MS,
  cockpit,
  emptyStream,
  isFiltered,
  liveFilterFromParams,
  liveFilterQuery,
  liveFilterToParams,
  matchesSearch,
  periodWindow,
  receive,
  setPaused,
  type LiveFilter,
  type Period,
  type Stage,
  type Stream,
} from "./engineRoomModel";
import type { Selection } from "./routing";

const POLL_MS = 1000;
const TIMEOUT_MS = 8000;
/** How long a stage stays marked after an interaction touched it. */
const MARK_MS = 4000;

const channelLabels: Record<string, string> = {
  web: "Web",
  mcp: "MCP",
  chat: "Chat",
  cli: "CLI",
  worker: "Worker",
};
const kindLabels: Record<string, string> = {
  read: "Read",
  write: "Write",
  propose: "Proposal",
  decide: "Decision",
  job: "Job",
};
const outcomeLabels: Record<string, string> = {
  ok: "OK",
  refused: "Refused",
  failed: "Failed",
  awaiting_decision: "Awaiting decision",
};
const stageLabels: Record<Stage, string> = {
  source: "Source",
  document: "Document",
  fact: "Fact",
  commitment: "Commitment",
  reservation: "Reservation",
  movement: "Movement",
  ledger: "Ledger",
  master_data: "Master data",
};
const stageTone: Record<"read" | "written" | "none", string> = {
  written: "border-accent bg-accent text-fg-inverse",
  read: "border-accent bg-surface text-fg-strong",
  none: "border-border-subtle bg-surface-muted text-fg-muted",
};
const outcomeTone: Record<string, string> = {
  ok: "bg-positive-bg text-positive-text",
  refused: "bg-caution-bg text-caution-text",
  failed: "bg-critical-bg text-critical-text",
  awaiting_decision: "bg-accent-soft text-fg-strong",
};

function actorLine(row: Interaction): string {
  const actor = row.actor;
  if (!actor) return row.channel === "cli" ? t("Operator") : t("Unknown");
  if (actor.kind === "mcp_token") {
    const token = actor.label || t("Unnamed token");
    const issuer = actor.issuer?.label;
    const base = issuer
      ? t("Token {token}, issued by {issuer}").replace("{token}", token).replace("{issuer}", issuer)
      : t("Token {token}").replace("{token}", token);
    return actor.revoked ? `${base} · ${t("revoked")}` : base;
  }
  if (actor.kind === "job") return t("Background job");
  return actor.label || t("Unknown person");
}

function StageMap({ marks }: { marks: Map<Stage, "read" | "written"> }) {
  return (
    <ol
      className="flex flex-wrap items-center gap-1 text-xs"
      aria-label={t("Model stages")}
      data-engine-room-map
    >
      {STAGES.map((stage, index) => {
        const mark = marks.get(stage);
        return (
          <li key={stage} className="flex items-center gap-1">
            {index > 0 && index < 7 && (
              <span aria-hidden className="text-fg-quiet">
                →
              </span>
            )}
            <span
              data-stage={stage}
              data-stage-mark={mark || "none"}
              className={`rounded-full border px-2 py-0.5 transition-colors motion-reduce:transition-none ${stageTone[mark || "none"]}`}
            >
              {t(stageLabels[stage])}
              {mark && (
                <span className="sr-only"> {mark === "written" ? t("written") : t("read")}</span>
              )}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function EventsOf({
  tenant,
  row,
  open,
}: {
  tenant: string;
  row: Interaction;
  open: (target: { kind: string; id: string }) => void;
}) {
  const [events, setEvents] = useState<InteractionEvent[] | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let alive = true;
    api
      .interactionEvents(tenant, row.id)
      .then((result) => alive && setEvents(result.events))
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
    };
  }, [tenant, row.id]);
  if (failed)
    return <div className="text-xs text-critical-text">{t("Events could not be loaded.")}</div>;
  if (!events) return <div className="text-xs text-fg-muted">{t("Loading…")}</div>;
  return (
    <ul className="mt-1 space-y-1" data-engine-room-events>
      {events.map((event) => (
        <li key={event.id} className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-mono text-fg-muted">#{event.sequence}</span>
          <span data-original-content="">{event.type}</span>
          <button
            className="text-accent underline-offset-2 hover:underline"
            onClick={() => open({ kind: "business_event", id: event.id })}
          >
            {t("Inspect event")}
          </button>
          <button
            className="text-accent underline-offset-2 hover:underline"
            onClick={() => open({ kind: event.subject_type, id: event.subject_id })}
          >
            {t("Open record")}
          </button>
        </li>
      ))}
    </ul>
  );
}

function StageChips({ row }: { row: Interaction }) {
  const written = new Set(row.stages.written);
  // Filled where the call wrote, outlined where it read.
  const touched = STAGES.filter((stage) => written.has(stage) || row.stages.read.includes(stage));
  if (!touched.length) return null;
  return (
    <span className="flex flex-wrap gap-1" data-interaction-stages>
      {touched.map((stage) => (
        <span
          key={stage}
          data-stage-touch={written.has(stage) ? "written" : "read"}
          className={`rounded-full border px-2 py-0.5 text-xs ${stageTone[written.has(stage) ? "written" : "read"]}`}
        >
          {t(stageLabels[stage])}
        </span>
      ))}
    </span>
  );
}

function argumentsOf(row: Interaction): string[] {
  const choices = row.summary.choices || {};
  // Arguments with a declared choice show the choice; the rest show their name only.
  return [
    ...Object.entries(choices).map(([name, value]) => `${name}: ${value}`),
    ...(row.summary.arguments || []).filter((name) => !(name in choices)),
  ];
}

function InteractionDetails({
  tenant,
  row,
  open,
  openProposal,
  filterBy,
}: {
  tenant: string;
  row: Interaction;
  open: (target: { kind: string; id: string }) => void;
  openProposal: (id: string) => void;
  filterBy: (change: Partial<LiveFilter>) => void;
}) {
  const args = argumentsOf(row);
  return (
    <div className="max-w-3xl space-y-3 text-sm">
      <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1">
        <dt className="text-fg-muted">{t("Kind")}</dt>
        <dd>{t(kindLabels[row.kind] || row.kind)}</dd>
        {args.length > 0 && (
          <>
            <dt className="text-fg-muted">{t("Arguments")}</dt>
            <dd className="font-mono text-xs" data-original-content="">
              {args.join(", ")}
            </dd>
          </>
        )}
        {row.summary.result_count !== undefined && (
          <>
            <dt className="text-fg-muted">{t("Results")}</dt>
            <dd>{formatNumber(row.summary.result_count)}</dd>
          </>
        )}
        {row.error_code && (
          <>
            <dt className="text-fg-muted">{t("Error code")}</dt>
            <dd className="font-mono text-xs" data-original-content="">
              {row.error_code}
            </dd>
          </>
        )}
      </dl>
      <div className="flex flex-wrap gap-2">
        {row.proposal && (
          <button
            className="br-btn"
            onClick={() => openProposal(row.proposal!.id)}
            data-engine-room-proposal
          >
            {t("Decision")} · {t(row.proposal.status)}
          </button>
        )}
        <button className="br-btn" onClick={() => filterBy({ correlation: row.correlation_id })}>
          {t("All steps of this action")}
        </button>
      </div>
      {row.events.count > 0 && <EventsOf tenant={tenant} row={row} open={open} />}
    </div>
  );
}

function Trace({ values }: { values: number[] }) {
  const peak = Math.max(1, ...values);
  return (
    <span className="flex h-6 w-full items-end gap-0.5" aria-hidden data-cockpit-trace>
      {values.map((value, index) => (
        <span
          key={index}
          className={`min-w-0 flex-1 rounded-sm ${value ? "bg-accent" : "bg-border-subtle"}`}
          style={{ height: `${Math.max(8, (value / peak) * 100)}%` }}
        />
      ))}
    </span>
  );
}

/** The live monitor: one minute of the company's model, like an activity monitor. */
function LiveCockpit({
  tenant,
  rows,
  now,
  marks,
  open,
  openProposal,
  filterBy,
}: {
  tenant: string;
  rows: Interaction[];
  now: number;
  marks: Map<Stage, "read" | "written">;
  open: (target: { kind: string; id: string }) => void;
  openProposal: (id: string) => void;
  filterBy: (change: Partial<LiveFilter>) => void;
}) {
  const view = useMemo(() => cockpit(rows, now), [rows, now]);
  const [selected, setSelected] = useState("");
  const chosen = view.ticker.find((row) => row.id === selected);
  const age = (row: Interaction) => Math.max(0, now - Date.parse(row.recorded_at));
  return (
    <div className="register-table-inset space-y-4 py-4" data-engine-room-cockpit>
      <div
        className="flex flex-wrap items-center gap-3 rounded-lg border border-border-subtle bg-surface-muted px-4 py-3"
        data-cockpit-status={view.quiet ? "quiet" : "active"}
        aria-live="polite"
      >
        <span className="relative flex h-3 w-3" aria-hidden>
          {!view.quiet && (
            <span className="absolute inline-flex h-full w-full rounded-full bg-accent opacity-60 motion-safe:animate-ping" />
          )}
          <span
            className={`relative inline-flex h-3 w-3 rounded-full ${view.quiet ? "bg-border-strong" : "bg-accent"}`}
          />
        </span>
        <span className="font-medium text-fg-strong">
          {view.quiet
            ? t("All quiet")
            : t("{count} accesses in the last minute").replace("{count}", formatNumber(view.total))}
        </span>
        <span className="text-sm text-fg-muted">
          {view.quiet
            ? t("Nothing has touched the model in the last minute.")
            : view.errors
              ? t("{count} refused or failed").replace("{count}", formatNumber(view.errors))
              : t("No errors")}
        </span>
      </div>

      <div
        className="grid gap-2 [grid-template-columns:repeat(auto-fit,minmax(7.5rem,1fr))]"
        data-cockpit-channels
      >
        {view.channels.map((channel) => (
          <button
            key={channel.channel}
            className={`flex min-w-0 flex-col gap-2 rounded-lg border p-3 text-left transition-colors hover:bg-surface-muted ${
              channel.count ? "border-accent" : "border-border-subtle"
            }`}
            onClick={() => filterBy({ channel: channel.channel })}
            title={t("Show only this channel")}
            data-cockpit-channel={channel.channel}
          >
            <span className="flex items-center justify-between gap-2 text-xs text-fg-muted">
              {channelLabels[channel.channel]}
              {channel.errors > 0 && (
                <span className={`rounded px-1.5 py-0.5 ${outcomeTone.failed}`}>
                  {formatNumber(channel.errors)}
                </span>
              )}
            </span>
            <span className="whitespace-nowrap">
              <span className="text-2xl font-semibold tabular-nums text-fg-strong">
                {formatNumber(channel.count)}
              </span>
              <span className="ml-1 text-xs text-fg-muted">{t("/ min")}</span>
            </span>
            <Trace values={channel.trace} />
          </button>
        ))}
      </div>

      <div className="rounded-lg border border-border-subtle p-3" data-cockpit-machine>
        <div className="mb-2 text-xs font-medium text-fg-muted">{t("Model")}</div>
        <ol
          className="grid gap-2 [grid-template-columns:repeat(auto-fit,minmax(6.5rem,1fr))]"
          data-engine-room-map
        >
          {STAGES.map((stage) => {
            const mark = marks.get(stage);
            const counts = view.stages[stage];
            return (
              <li
                key={stage}
                data-stage={stage}
                data-stage-mark={mark || "none"}
                className={`flex flex-col gap-1 rounded-md border px-2.5 py-2 transition-colors motion-reduce:transition-none ${stageTone[mark || "none"]}`}
              >
                <span className="truncate text-xs font-medium">{t(stageLabels[stage])}</span>
                <span className="flex flex-col text-xs tabular-nums opacity-80">
                  <span>
                    {t("read")} {formatNumber(counts.read)}
                  </span>
                  <span>
                    {t("written")} {formatNumber(counts.written)}
                  </span>
                </span>
              </li>
            );
          })}
        </ol>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
        <section className="min-w-0" aria-labelledby="cockpit-actors">
          <h3 id="cockpit-actors" className="mb-2 text-xs font-medium text-fg-muted">
            {t("Active now")}
          </h3>
          {view.actors.length ? (
            <ul className="space-y-1" data-cockpit-actors>
              {view.actors.slice(0, 8).map((actor) => (
                <li key={actor.key}>
                  <button
                    className="flex w-full min-w-0 items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-surface-muted"
                    onClick={() =>
                      actor.kind === "mcp_token"
                        ? filterBy({ mcpToken: actor.key.split(":")[1] })
                        : actor.kind === "user"
                          ? filterBy({ actor: actor.key.split(":")[1] })
                          : filterBy({ channel: actor.channel })
                    }
                  >
                    <span className="shrink-0 rounded bg-surface-muted px-1.5 py-0.5 text-xs">
                      {channelLabels[actor.channel]}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate">
                        {actor.label || (actor.kind === "job" ? t("Background job") : t("Unknown"))}
                      </span>
                      <span className="block truncate text-xs text-fg-muted">
                        {actor.lastLabel ? t(actor.lastLabel) : actor.last}
                      </span>
                    </span>
                    <span className="shrink-0 text-sm font-semibold tabular-nums">
                      {formatNumber(actor.count)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="px-2 py-1.5 text-sm text-fg-muted">{t("Nobody right now.")}</p>
          )}
        </section>
        <section className="min-w-0" aria-labelledby="cockpit-ticker">
          <h3 id="cockpit-ticker" className="mb-2 text-xs font-medium text-fg-muted">
            {t("Happening now")}
          </h3>
          {view.ticker.length ? (
            <ol className="space-y-1" data-engine-room-list>
              {view.ticker.slice(0, 12).map((row) => (
                <li
                  key={row.id}
                  data-interaction={row.id}
                  data-interaction-channel={row.channel}
                  // Older lines fade: the ticker is about now, not about a while ago.
                  style={{ opacity: Math.max(0.35, 1 - age(row) / COCKPIT_WINDOW_MS) }}
                >
                  <button
                    className={`grid w-full grid-cols-[4.5rem_minmax(0,1fr)_auto] items-center gap-2 rounded-md px-2 py-1 text-left text-sm hover:bg-surface-muted ${
                      selected === row.id ? "bg-surface-muted" : ""
                    }`}
                    aria-expanded={selected === row.id}
                    onClick={() => setSelected(selected === row.id ? "" : row.id)}
                  >
                    <span className="font-mono text-xs text-fg-muted">
                      {formatTime(row.recorded_at, true)}
                    </span>
                    <span className="min-w-0 truncate">
                      <span className="mr-1.5 rounded bg-surface-muted px-1.5 py-0.5 text-xs">
                        {channelLabels[row.channel]}
                      </span>
                      <span data-interaction-label>{row.label ? t(row.label) : row.operation}</span>
                      <span className="ml-1.5 text-xs text-fg-muted">{actorLine(row)}</span>
                    </span>
                    <span
                      className={`rounded px-1.5 py-0.5 text-xs ${outcomeTone[row.outcome] || ""}`}
                      data-interaction-outcome
                    >
                      {t(outcomeLabels[row.outcome] || row.outcome)}
                    </span>
                  </button>
                </li>
              ))}
            </ol>
          ) : (
            <p className="px-2 py-1.5 text-sm text-fg-muted" data-cockpit-quiet>
              {t("All quiet. New accesses appear here the moment they happen.")}
            </p>
          )}
          {chosen && (
            <div className="mt-2 rounded-lg border border-border-subtle p-3" data-cockpit-details>
              <InteractionDetails
                tenant={tenant}
                row={chosen}
                open={open}
                openProposal={openProposal}
                filterBy={filterBy}
              />
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

const COLUMNS = 7;

export function EngineRoom({
  selection,
  navigate,
}: {
  selection: Selection;
  navigate: (value: Partial<Selection>) => void;
}) {
  const tenant = selection.tenant;
  const filter = useMemo(
    () => liveFilterFromParams(new URLSearchParams(selection.liveFilter || "")),
    [selection.liveFilter],
  );
  const setFilter = (change: Partial<LiveFilter>) =>
    navigate({ liveFilter: liveFilterToParams({ ...filter, ...change }).toString() });
  const live = !filter.period;
  const [stream, setStream] = useState<Stream<Interaction>>(emptyStream);
  const [windowRows, setWindowRows] = useState<Interaction[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);
  const [truncated, setTruncated] = useState(false);
  const [state, setState] = useState<"loading" | "ready" | "stale" | "forbidden">("loading");
  const [revision, setRevision] = useState(0);
  const [draft, setDraft] = useState(filter.search);
  const [expanded, setExpanded] = useState("");
  const [step, setStep] = useState(0);
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  const [clock, setClock] = useState(Date.now());
  const query = liveFilterQuery(filter).toString();
  const cursorRef = useRef<number | null>(null);
  cursorRef.current = cursor;

  useEffect(() => setDraft(filter.search), [filter.search]);
  // A new filter or period starts a new read.
  useEffect(() => {
    setStream(emptyStream());
    setWindowRows([]);
    setCursor(null);
    setStep(0);
    setState("loading");
  }, [tenant, query, filter.period]);

  useEffect(() => {
    if (!live) return;
    let disposed = false;
    let busy = false;
    const poll = async () => {
      if (disposed || busy || document.hidden) return;
      busy = true;
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), TIMEOUT_MS);
      const params = new URLSearchParams(query);
      params.set("language", currentLanguage());
      if (cursorRef.current !== null) params.set("after", String(cursorRef.current));
      try {
        const page = await api.interactions(tenant, params, controller.signal);
        if (disposed) return;
        setStream((current) => receive(current, page.interactions));
        if (page.cursor !== null) setCursor((value) => Math.max(value ?? 0, page.cursor!));
        if (cursorRef.current === null) setTruncated(page.truncated);
        setState("ready");
      } catch (error) {
        if (disposed) return;
        setState(error instanceof APIError && error.status === 404 ? "forbidden" : "stale");
      } finally {
        window.clearTimeout(timeout);
        busy = false;
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), POLL_MS);
    const visible = () => !document.hidden && void poll();
    document.addEventListener("visibilitychange", visible);
    return () => {
      disposed = true;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [tenant, query, live]);

  // A past period is read once, and again on Refresh.
  useEffect(() => {
    const range = periodWindow(filter.period);
    if (!range) return;
    let disposed = false;
    const params = new URLSearchParams(query);
    params.set("language", currentLanguage());
    params.set("from", range.from.toISOString());
    params.set("to", range.to.toISOString());
    params.set("limit", "500");
    api
      .interactions(tenant, params)
      .then((page) => {
        if (disposed) return;
        setWindowRows(page.interactions);
        setTruncated(page.truncated);
        setState("ready");
      })
      .catch((error) => {
        if (!disposed)
          setState(error instanceof APIError && error.status === 404 ? "forbidden" : "stale");
      });
    return () => {
      disposed = true;
    };
  }, [tenant, query, filter.period, revision]);

  useEffect(() => {
    const timer = window.setInterval(() => setClock(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  // Newest first, as every register reads; the search narrows what is shown.
  const rows = useMemo(
    () =>
      [...(live ? stream.visible : windowRows)]
        .reverse()
        .filter((row) => matchesSearch(row, filter.search, t)),
    [live, stream.visible, windowRows, filter.search],
  );
  // In a past period, the steps run oldest to newest.
  const steps = useMemo(() => [...rows].reverse(), [rows]);
  const current = !live ? steps[Math.min(step, steps.length - 1)] : undefined;
  const marks = useMemo(() => {
    const result = new Map<Stage, "read" | "written">();
    const touching = live
      ? rows.filter((row) => clock - Date.parse(row.recorded_at) < MARK_MS)
      : current
        ? [current]
        : [];
    for (const row of touching) {
      for (const stage of row.stages.read) if (!result.has(stage)) result.set(stage, "read");
      for (const stage of row.stages.written) result.set(stage, "written");
    }
    return result;
  }, [live, rows, current, clock]);
  const openProposal = (id: string) =>
    navigate({ route: "decisions", decisionsView: "history", proposal: id });

  if (state === "forbidden")
    return (
      <div role="status" className="rounded-lg border border-border-subtle p-6 text-sm">
        {t("Only company owners can open the live monitor.")}
      </div>
    );

  const chips: { key: keyof LiveFilter; label: string }[] = [
    { key: "actor", label: t("Person") },
    { key: "mcpToken", label: t("MCP client") },
    { key: "correlation", label: t("One action") },
    { key: "subjectId", label: t("Record") },
  ];
  const submitSearch = () => setFilter({ search: draft.trim() });
  const footer = (
    <p className="text-xs text-fg-muted" data-engine-room-footer>
      {live
        ? stream.paused
          ? t("Paused · {count} new").replace("{count}", formatNumber(stream.pending))
          : state === "stale"
            ? t("The live monitor could not be refreshed. It keeps trying.")
            : t("Live · refreshed every second")
        : t("Interactions are kept for seven days.")}
      {truncated && <> · {t("Showing the newest interactions only.")}</>}
    </p>
  );

  const filterControls = (
    <>
      <select
        aria-label={t("Period")}
        value={filter.period}
        onChange={(event) => setFilter({ period: event.target.value as Period })}
        data-engine-room-period
      >
        <option value="">{t("Live")}</option>
        <option value="1h">{t("Last hour")}</option>
        <option value="24h">{t("Last 24 hours")}</option>
        <option value="7d">{t("Last 7 days")}</option>
      </select>
      {(
        [
          ["channel", t("Channel"), CHANNELS, channelLabels],
          ["kind", t("Kind"), KINDS, kindLabels],
          ["outcome", t("Outcome"), OUTCOMES, outcomeLabels],
        ] as const
      ).map(([key, label, values, labels]) => (
        <select
          key={key}
          aria-label={label}
          value={filter[key]}
          onChange={(event) => setFilter({ [key]: event.target.value })}
        >
          <option value="">{t("All")}</option>
          {values.map((value) => (
            <option key={value} value={value}>
              {key === "channel"
                ? channelLabels[value]
                : t((labels as Record<string, string>)[value] || value)}
            </option>
          ))}
        </select>
      ))}
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={filter.refresh}
          onChange={(event) => setFilter({ refresh: event.target.checked })}
        />
        {t("Show background refresh")}
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={filter.own}
          onChange={(event) => setFilter({ own: event.target.checked })}
          data-engine-room-own
        />
        {t("Show my own access")}
      </label>
      {!live && (
        <>
          <button className="br-btn" onClick={() => setRevision((value) => value + 1)}>
            <RefreshCw size={15} />
            {t("Refresh")}
          </button>
          <span className="inline-flex items-center gap-1">
            <button
              className="br-btn"
              aria-label={t("Previous step")}
              disabled={step <= 0}
              onClick={() => setStep((value) => Math.max(0, value - 1))}
            >
              <SkipBack size={15} />
            </button>
            <span className="min-w-20 text-center text-xs text-fg-muted" data-engine-room-step>
              {steps.length
                ? t("Step {step} of {total}")
                    .replace("{step}", formatNumber(Math.min(step, steps.length - 1) + 1))
                    .replace("{total}", formatNumber(steps.length))
                : "—"}
            </span>
            <button
              className="br-btn"
              aria-label={t("Next step")}
              disabled={step >= steps.length - 1}
              onClick={() => setStep((value) => Math.min(steps.length - 1, value + 1))}
            >
              <SkipForward size={15} />
            </button>
          </span>
        </>
      )}
      {chips
        .filter(({ key }) => filter[key])
        .map(({ key, label }) => (
          <span
            key={key}
            className="inline-flex items-center gap-1 rounded-full bg-accent-soft px-2.5 py-1 text-xs"
            data-engine-room-chip={key}
          >
            {label}: <span data-original-content="">{String(filter[key])}</span>
            <button
              aria-label={t("Remove filter")}
              onClick={() =>
                setFilter(key === "subjectId" ? { subjectId: "", subjectType: "" } : { [key]: "" })
              }
            >
              <X size={12} />
            </button>
          </span>
        ))}
      {isFiltered(filter) && (
        <button className="br-btn" onClick={() => navigate({ liveFilter: "" })}>
          {t("Clear filters")}
        </button>
      )}
    </>
  );
  return (
    <>
      <RegisterWorkbench>
        <section className="register-surface min-w-0 overflow-hidden" data-engine-room>
          {live ? (
            <>
              <div className="register-toolbar-block">
                <div className="register-filter-row">{filterChips(filterControls)}</div>
              </div>
              <LiveCockpit
                tenant={tenant}
                rows={stream.visible}
                now={clock}
                marks={marks}
                open={setTarget}
                openProposal={openProposal}
                filterBy={setFilter}
              />
            </>
          ) : (
            <>
              <RegisterToolbar
                count={rows.length}
                search={
                  <input
                    aria-label={t("Search access")}
                    placeholder={t("Tool, route or client")}
                    className="br-control"
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    onKeyDown={(event) => event.key === "Enter" && submitSearch()}
                  />
                }
                submit={
                  <button className="br-btn" onClick={submitSearch}>
                    {t("Search")}
                  </button>
                }
                filters={filterControls}
              />
              <div className="register-table-inset pt-3">
                <StageMap marks={marks} />
              </div>
              <div className="register-table-inset py-4" data-engine-room-list>
                {state === "loading" ? (
                  <p role="status" className="py-8 text-sm text-fg-muted">
                    {t("Listening…")}
                  </p>
                ) : (
                  <RegisterTable
                    cursorView={{ id: "inspector:live", widths: [90, 260, 100, 230, 190, 80, 50] }}
                    footer={footer}
                    empty={{
                      title: live
                        ? t("Nothing has touched the model yet.")
                        : t("No interactions in this window."),
                      hint: live
                        ? t("Open a page, ask the chat or call a tool, and it appears here.")
                        : undefined,
                    }}
                  >
                    <thead>
                      <tr>
                        <th>{t("Time")}</th>
                        <th>{t("Request")}</th>
                        <th>{t("Outcome")}</th>
                        <th>{t("Who")}</th>
                        <th>{t("Model")}</th>
                        <th>{t("Duration")}</th>
                        <th>{t("Actions")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.flatMap((row) => {
                        const open = expanded === row.id;
                        // A flat list with its own keys: the register flattens fragments,
                        // and their children would share the keys ".0" and ".1".
                        return [
                          <tr
                            key={row.id}
                            data-interaction={row.id}
                            data-interaction-channel={row.channel}
                            aria-current={current?.id === row.id || undefined}
                          >
                            <td className="font-mono text-xs">
                              {formatTime(row.recorded_at, true)}
                            </td>
                            <td>
                              <span className="block truncate" data-interaction-label>
                                {row.label ? t(row.label) : row.operation}
                              </span>
                              {row.label && (
                                <span
                                  className="block truncate font-mono text-xs text-fg-muted"
                                  data-original-content=""
                                >
                                  {row.operation}
                                </span>
                              )}
                            </td>
                            <td>
                              <span
                                className={`inline-block rounded px-1.5 py-0.5 text-xs ${outcomeTone[row.outcome] || ""}`}
                                data-interaction-outcome
                              >
                                {t(outcomeLabels[row.outcome] || row.outcome)}
                              </span>
                            </td>
                            <td>
                              <span className="flex min-w-0 items-center gap-2">
                                <button
                                  className="shrink-0 rounded bg-surface-muted px-1.5 py-0.5 text-xs font-medium hover:bg-surface-sunken"
                                  onClick={() => setFilter({ channel: row.channel })}
                                  title={t("Show only this channel")}
                                >
                                  {channelLabels[row.channel] || row.channel}
                                </button>
                                <button
                                  className="min-w-0 truncate text-left hover:underline"
                                  title={actorLine(row)}
                                  onClick={() =>
                                    row.actor?.kind === "mcp_token"
                                      ? setFilter({ mcpToken: row.actor.id })
                                      : row.actor?.kind === "user"
                                        ? setFilter({ actor: row.actor.id })
                                        : undefined
                                  }
                                >
                                  {actorLine(row)}
                                </button>
                              </span>
                            </td>
                            <td>
                              <StageChips row={row} />
                            </td>
                            <td className="tabular-nums">{formatNumber(row.duration_ms)} ms</td>
                            <td>
                              <span data-engine-room-events-toggle>
                                <PreviewButton
                                  open={open}
                                  controls={`interaction-preview-${row.id}`}
                                  label={row.label ? t(row.label) : row.operation}
                                  toggle={() => {
                                    setExpanded(open ? "" : row.id);
                                    if (!live)
                                      setStep(steps.findIndex((item) => item.id === row.id));
                                  }}
                                />
                              </span>
                            </td>
                          </tr>,
                          <TablePreview
                            key={`preview-${row.id}`}
                            id={`interaction-preview-${row.id}`}
                            open={open}
                            columns={COLUMNS}
                          >
                            <InteractionDetails
                              tenant={tenant}
                              row={row}
                              open={setTarget}
                              openProposal={openProposal}
                              filterBy={setFilter}
                            />
                          </TablePreview>,
                        ];
                      })}
                    </tbody>
                  </RegisterTable>
                )}
              </div>
            </>
          )}
        </section>
      </RegisterWorkbench>
      {/* Outside the workbench: its child-position rules would restyle the dialog. */}
      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </>
  );
}

const PULSE_MS = 10_000;

/** The shell's engine-room indicator: it blinks when the model was touched (US4). */
export function EngineRoomPulse({ tenant, open }: { tenant: string; open: () => void }) {
  const [active, setActive] = useState(false);
  const last = useRef<number | null | undefined>(undefined);
  useEffect(() => {
    let disposed = false;
    let off: number | undefined;
    const read = async () => {
      if (disposed || document.hidden) return;
      try {
        const pulse = await api.interactionsPulse(tenant);
        if (disposed) return;
        if (last.current !== undefined && pulse.latest_cursor !== last.current) {
          setActive(true);
          window.clearTimeout(off);
          off = window.setTimeout(() => setActive(false), 2500);
        }
        last.current = pulse.latest_cursor;
      } catch {
        /* the indicator stays quiet; the engine room itself reports errors */
      }
    };
    void read();
    const timer = window.setInterval(() => void read(), PULSE_MS);
    return () => {
      disposed = true;
      window.clearInterval(timer);
      window.clearTimeout(off);
    };
  }, [tenant]);
  return (
    <button
      type="button"
      className="shell-chat-toggle relative"
      title={t("Live monitor")}
      aria-label={t("Live monitor")}
      data-engine-room-pulse={active || undefined}
      onClick={open}
    >
      <Radio size={16} />
      {active && (
        <span
          aria-hidden
          className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-accent motion-safe:animate-ping"
        />
      )}
    </button>
  );
}
