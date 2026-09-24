import { Pause, Play, Radio, Rewind, SkipBack, SkipForward, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { APIError, api, type Interaction, type InteractionEvent } from "../api";
import { formatDateTime, formatNumber, formatTime, t } from "../localization";
import { Inspector } from "./Inspector";
import {
  CHANNELS,
  KINDS,
  OUTCOMES,
  STAGES,
  emptyLiveFilter,
  emptyStream,
  groupByCorrelation,
  isFiltered,
  liveFilterFromParams,
  liveFilterQuery,
  liveFilterToParams,
  receive,
  setPaused,
  type LiveFilter,
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
  written: "border-accent bg-accent text-fg-on-solid",
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
      className="flex flex-wrap items-center gap-1.5 text-xs"
      aria-label={t("Model stages")}
      data-engine-room-map
    >
      {STAGES.map((stage, index) => {
        const mark = marks.get(stage);
        return (
          <li key={stage} className="flex items-center gap-1.5">
            {index > 0 && index < 7 && (
              <span aria-hidden className="text-fg-quiet">
                →
              </span>
            )}
            <span
              data-stage={stage}
              data-stage-mark={mark || "none"}
              className={`rounded-full border px-2.5 py-1 transition-colors motion-reduce:transition-none ${stageTone[mark || "none"]}`}
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

function RealityCell({
  tenant,
  row,
  open,
  openProposal,
}: {
  tenant: string;
  row: Interaction;
  open: (target: { kind: string; id: string }) => void;
  openProposal: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  if (!row.events.count && !row.proposal)
    return <span className="text-xs text-fg-quiet">{t("Changed nothing")}</span>;
  return (
    <div className="min-w-0">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {row.proposal && (
          <button
            className="text-accent underline-offset-2 hover:underline"
            onClick={() => openProposal(row.proposal!.id)}
            data-engine-room-proposal
          >
            {t("Decision")} · {t(row.proposal.status)}
          </button>
        )}
        {row.events.count > 0 && (
          <button
            className="text-accent underline-offset-2 hover:underline"
            aria-expanded={expanded}
            onClick={() => setExpanded((value) => !value)}
            data-engine-room-events-toggle
          >
            {row.events.count === 1
              ? t("1 event")
              : t("{count} events").replace("{count}", formatNumber(row.events.count))}
          </button>
        )}
      </div>
      {expanded && <EventsOf tenant={tenant} row={row} open={open} />}
    </div>
  );
}

function InteractionRow({
  tenant,
  row,
  current,
  open,
  openProposal,
  filterBy,
}: {
  tenant: string;
  row: Interaction;
  current: boolean;
  open: (target: { kind: string; id: string }) => void;
  openProposal: (id: string) => void;
  filterBy: (change: Partial<LiveFilter>) => void;
}) {
  const args = row.summary.arguments || [];
  return (
    <li
      className={`grid gap-x-4 gap-y-1 px-3 py-2 text-sm md:grid-cols-[minmax(0,1.1fr)_minmax(0,1.4fr)_minmax(0,1fr)] ${
        current ? "bg-accent-soft" : ""
      }`}
      data-interaction={row.id}
      data-interaction-channel={row.channel}
      aria-current={current || undefined}
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-fg-muted">
            {formatTime(row.recorded_at, true)}
          </span>
          <button
            className="rounded bg-surface-muted px-1.5 py-0.5 text-xs font-medium hover:bg-surface-sunken"
            onClick={() => filterBy({ channel: row.channel })}
            title={t("Show only this channel")}
          >
            {channelLabels[row.channel] || row.channel}
          </button>
        </div>
        <button
          className="block max-w-full truncate text-left text-xs text-fg-secondary hover:underline"
          onClick={() =>
            row.actor?.kind === "mcp_token"
              ? filterBy({ mcpToken: row.actor.id })
              : row.actor?.kind === "user"
                ? filterBy({ actor: row.actor.id })
                : undefined
          }
          title={t("Show only this actor")}
        >
          {actorLine(row)}
        </button>
      </div>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate font-mono text-xs" data-original-content="">
            {row.operation}
          </span>
          <span className={`rounded px-1.5 py-0.5 text-xs ${outcomeTone[row.outcome] || ""}`}>
            {t(outcomeLabels[row.outcome] || row.outcome)}
          </span>
        </div>
        <div className="text-xs text-fg-muted">
          {t(kindLabels[row.kind] || row.kind)} · {formatNumber(row.duration_ms)} ms
          {row.error_code && (
            <>
              {" "}
              · <span data-original-content="">{row.error_code}</span>
            </>
          )}
          {row.summary.result_count !== undefined && (
            <>
              {" "}
              · {t("{count} results").replace("{count}", formatNumber(row.summary.result_count))}
            </>
          )}
          {args.length > 0 && (
            <>
              {" "}
              · <span data-original-content="">{args.join(", ")}</span>
            </>
          )}
        </div>
      </div>
      <RealityCell tenant={tenant} row={row} open={open} openProposal={openProposal} />
    </li>
  );
}

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
  const [stream, setStream] = useState<Stream<Interaction>>(emptyStream);
  const [cursor, setCursor] = useState<number | null>(null);
  const [truncated, setTruncated] = useState(false);
  const [retention, setRetention] = useState<string | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "stale" | "forbidden">("loading");
  const [mode, setMode] = useState<"live" | "replay">("live");
  const [window_, setWindow] = useState(() => {
    const end = new Date();
    return { from: new Date(end.getTime() - 3600_000), to: end };
  });
  const [replay, setReplay] = useState<Interaction[]>([]);
  const [step, setStep] = useState(0);
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  const [clock, setClock] = useState(Date.now());
  const query = liveFilterQuery(filter).toString();
  const cursorRef = useRef<number | null>(null);
  cursorRef.current = cursor;

  // A new filter starts a new stream.
  useEffect(() => {
    setStream(emptyStream());
    setCursor(null);
    setState("loading");
  }, [tenant, query]);

  useEffect(() => {
    if (mode !== "live") return;
    let disposed = false;
    let busy = false;
    const poll = async () => {
      if (disposed || busy || document.hidden) return;
      busy = true;
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), TIMEOUT_MS);
      const params = new URLSearchParams(query);
      if (cursorRef.current !== null) params.set("after", String(cursorRef.current));
      try {
        const page = await api.interactions(tenant, params, controller.signal);
        if (disposed) return;
        setStream((current) => receive(current, page.interactions));
        if (page.cursor !== null) setCursor((value) => Math.max(value ?? 0, page.cursor!));
        if (cursorRef.current === null) setTruncated(page.truncated);
        setRetention(page.retention_starts_at);
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
  }, [tenant, query, mode]);

  useEffect(() => {
    const timer = window.setInterval(() => setClock(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const loadReplay = async () => {
    const params = new URLSearchParams(query);
    params.set("from", window_.from.toISOString());
    params.set("to", window_.to.toISOString());
    params.set("limit", "500");
    try {
      const page = await api.interactions(tenant, params);
      setReplay(page.interactions);
      setRetention(page.retention_starts_at);
      setTruncated(page.truncated);
      setStep(0);
      setState("ready");
    } catch (error) {
      setState(error instanceof APIError && error.status === 404 ? "forbidden" : "stale");
    }
  };

  const rows = mode === "live" ? stream.visible : replay;
  const marks = useMemo(() => {
    const result = new Map<Stage, "read" | "written">();
    const touching =
      mode === "replay"
        ? replay.slice(step, step + 1)
        : stream.visible.filter((row) => clock - Date.parse(row.recorded_at) < MARK_MS);
    for (const row of touching) {
      for (const stage of row.stages.read) if (!result.has(stage)) result.set(stage, "read");
      for (const stage of row.stages.written) result.set(stage, "written");
    }
    return result;
  }, [mode, replay, step, stream.visible, clock]);
  const groups = useMemo(
    () => (mode === "live" ? groupByCorrelation(rows).slice(0, 100) : []),
    [mode, rows],
  );
  const openProposal = (id: string) =>
    navigate({ route: "decisions", decisionsView: "history", proposal: id });
  const beyondRetention = retention !== null && window_.from < new Date(retention);

  if (state === "forbidden")
    return (
      <div role="status" className="rounded-lg border border-border-subtle p-6 text-sm">
        {t("Only company owners can open the engine room.")}
      </div>
    );

  const chips: { key: keyof LiveFilter; label: string }[] = [
    { key: "actor", label: t("Person") },
    { key: "mcpToken", label: t("MCP client") },
    { key: "correlation", label: t("One action") },
    { key: "subjectId", label: t("Record") },
  ];

  return (
    <section className="space-y-3" data-engine-room aria-labelledby="engine-room-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="engine-room-title" className="flex items-center gap-2 text-base font-semibold">
            <Radio size={16} aria-hidden />
            {t("Engine room")}
          </h2>
          <div className="text-sm text-fg-muted">
            {t(
              "Every access to this company's model, as it happens: who, through which channel, what was asked, and what it changed.",
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <nav className="register-tabs" aria-label={t("Engine room mode")}>
            <button aria-pressed={mode === "live"} onClick={() => setMode("live")}>
              {t("Live")}
            </button>
            <button
              aria-pressed={mode === "replay"}
              onClick={() => {
                setMode("replay");
                void loadReplay();
              }}
            >
              {t("Replay")}
            </button>
          </nav>
          {mode === "live" && (
            <button
              className="br-btn"
              onClick={() => setStream((current) => setPaused(current, !current.paused))}
              aria-pressed={stream.paused}
              data-engine-room-pause
            >
              {stream.paused ? <Play size={15} /> : <Pause size={15} />}
              {stream.paused
                ? stream.pending
                  ? t("Resume ({count} new)").replace("{count}", formatNumber(stream.pending))
                  : t("Resume")
                : t("Pause")}
            </button>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-border-subtle bg-surface p-3">
        <StageMap marks={marks} />
      </div>

      <div className="flex flex-wrap items-center gap-3 text-sm">
        {(
          [
            ["channel", t("Channel"), CHANNELS, channelLabels],
            ["kind", t("Kind"), KINDS, kindLabels],
            ["outcome", t("Outcome"), OUTCOMES, outcomeLabels],
          ] as const
        ).map(([key, label, values, labels]) => (
          <label key={key} className="flex items-center gap-2">
            {label}
            <select
              aria-label={label}
              className="rounded-lg border border-border-default bg-surface px-2 py-1.5"
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
          </label>
        ))}
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={filter.refresh}
            onChange={(event) => setFilter({ refresh: event.target.checked })}
          />
          {t("Show background refresh")}
        </label>
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
                  setFilter(
                    key === "subjectId" ? { subjectId: "", subjectType: "" } : { [key]: "" },
                  )
                }
              >
                <X size={12} />
              </button>
            </span>
          ))}
        {isFiltered(filter) && (
          <button
            className="text-xs text-accent hover:underline"
            onClick={() => navigate({ liveFilter: "" })}
          >
            {t("Clear filters")}
          </button>
        )}
      </div>

      {mode === "replay" && (
        <div className="flex flex-wrap items-end gap-3 rounded-lg border border-border-subtle p-3 text-sm">
          {(["from", "to"] as const).map((edge) => (
            <label key={edge} className="flex flex-col gap-1">
              {edge === "from" ? t("From") : t("To")}
              <input
                type="datetime-local"
                className="rounded-lg border border-border-default bg-surface px-2 py-1.5"
                value={new Date(window_[edge].getTime() - window_[edge].getTimezoneOffset() * 60000)
                  .toISOString()
                  .slice(0, 16)}
                onChange={(event) =>
                  event.target.value &&
                  setWindow((value) => ({ ...value, [edge]: new Date(event.target.value) }))
                }
              />
            </label>
          ))}
          <button className="br-btn" onClick={() => void loadReplay()}>
            <Rewind size={15} />
            {t("Load window")}
          </button>
          <div className="flex items-center gap-1">
            <button
              className="br-btn"
              aria-label={t("Previous step")}
              disabled={step <= 0}
              onClick={() => setStep((value) => Math.max(0, value - 1))}
            >
              <SkipBack size={15} />
            </button>
            <span className="min-w-20 text-center text-xs text-fg-muted" data-engine-room-step>
              {replay.length
                ? t("Step {step} of {total}")
                    .replace("{step}", formatNumber(step + 1))
                    .replace("{total}", formatNumber(replay.length))
                : "—"}
            </span>
            <button
              className="br-btn"
              aria-label={t("Next step")}
              disabled={step >= replay.length - 1}
              onClick={() => setStep((value) => Math.min(replay.length - 1, value + 1))}
            >
              <SkipForward size={15} />
            </button>
          </div>
          {beyondRetention && retention && (
            <div className="w-full text-xs text-fg-muted" role="note" data-engine-room-retention>
              {t(
                "Interactions are kept for seven days, since {date}. Business events stay in Activities.",
              ).replace("{date}", formatDateTime(retention))}
            </div>
          )}
        </div>
      )}

      {state === "stale" && (
        <div role="status" className="text-xs text-caution-text">
          {t("The engine room could not be refreshed. It keeps trying.")}
        </div>
      )}
      {truncated && (
        <div role="note" className="text-xs text-fg-muted">
          {t("Showing the newest interactions only.")}
        </div>
      )}

      <div className="hidden gap-4 px-3 text-xs font-medium text-fg-muted md:grid md:grid-cols-[minmax(0,1.1fr)_minmax(0,1.4fr)_minmax(0,1fr)]">
        <span>{t("Access")}</span>
        <span>{t("Intent")}</span>
        <span>{t("Reality")}</span>
      </div>
      {state === "loading" ? (
        <div role="status" className="py-8 text-sm text-fg-muted">
          {t("Listening…")}
        </div>
      ) : !rows.length ? (
        <div
          role="status"
          className="rounded-lg border border-dashed border-border-subtle p-6 text-sm text-fg-muted"
        >
          {mode === "live"
            ? t(
                "Nothing has touched the model yet. Open a page, ask the chat or call a tool, and it appears here.",
              )
            : t("No interactions in this window.")}
        </div>
      ) : mode === "live" ? (
        <ol
          className="divide-y divide-border-subtle rounded-lg border border-border-subtle"
          data-engine-room-list
        >
          {groups.map((group) => (
            <li key={group.correlation} data-correlation={group.correlation}>
              {group.rows.length > 1 && (
                <button
                  className="w-full px-3 pt-2 text-left text-xs text-fg-muted hover:underline"
                  onClick={() => setFilter({ correlation: group.correlation })}
                >
                  {t("{count} steps of one action").replace(
                    "{count}",
                    formatNumber(group.rows.length),
                  )}
                </button>
              )}
              <ol>
                {group.rows.map((row) => (
                  <InteractionRow
                    key={row.id}
                    tenant={tenant}
                    row={row}
                    current={false}
                    open={setTarget}
                    openProposal={openProposal}
                    filterBy={setFilter}
                  />
                ))}
              </ol>
            </li>
          ))}
        </ol>
      ) : (
        <ol
          className="divide-y divide-border-subtle rounded-lg border border-border-subtle"
          data-engine-room-list
        >
          {replay.map((row, index) => (
            <InteractionRow
              key={row.id}
              tenant={tenant}
              row={row}
              current={index === step}
              open={setTarget}
              openProposal={openProposal}
              filterBy={setFilter}
            />
          ))}
        </ol>
      )}
      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </section>
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
      title={t("Engine room")}
      aria-label={t("Engine room")}
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
