// The engine room's live list (spec 266): merging polls, pausing, grouping by
// cause and carrying the filter through the URL. Pure, so it is tested alone.

export const CHANNELS = ["web", "mcp", "chat", "cli", "worker"] as const;
export const KINDS = ["read", "write", "propose", "decide", "job"] as const;
export const OUTCOMES = ["ok", "refused", "failed", "awaiting_decision"] as const;
export const STAGES = [
  "source",
  "document",
  "fact",
  "commitment",
  "reservation",
  "movement",
  "ledger",
  "master_data",
] as const;

export type Channel = (typeof CHANNELS)[number];
export type Stage = (typeof STAGES)[number];

export type InteractionActor = {
  kind: "user" | "mcp_token" | "job";
  id: string;
  label: string | null;
  issuer?: { id: string; label: string | null } | null;
  revoked?: boolean;
};

export type Interaction = {
  id: string;
  cursor: number;
  started_at: string;
  recorded_at: string;
  duration_ms: number;
  channel: Channel;
  kind: (typeof KINDS)[number];
  operation: string;
  /** A reader's name for a tool call; null for web routes. */
  label: string | null;
  outcome: (typeof OUTCOMES)[number];
  error_code: string | null;
  actor: InteractionActor | null;
  correlation_id: string;
  proposal: { id: string; status: string; type: string } | null;
  events: { count: number; first_sequence: number | null; last_sequence: number | null };
  stages: { read: Stage[]; written: Stage[] };
  summary: { arguments?: string[]; choices?: Record<string, string>; result_count?: number };
  refresh: boolean;
};

export type InteractionPage = {
  interactions: Interaction[];
  cursor: number | null;
  retention_starts_at: string;
  truncated: boolean;
};

type Cursored = { id: string; cursor: number };

/** Merge a poll into what is shown: once per id, in cursor order, newest `cap` kept. */
export function mergeRows<T extends Cursored>(existing: T[], incoming: T[], cap = 1000): T[] {
  const byId = new Map(existing.map((row) => [row.id, row]));
  for (const row of incoming) byId.set(row.id, row);
  const merged = [...byId.values()].sort((a, b) => a.cursor - b.cursor);
  return merged.length > cap ? merged.slice(merged.length - cap) : merged;
}

export type Stream<T extends Cursored> = {
  visible: T[];
  buffered: T[];
  paused: boolean;
  pending: number;
};

export const emptyStream = <T extends Cursored>(): Stream<T> => ({
  visible: [],
  buffered: [],
  paused: false,
  pending: 0,
});

const unseen = <T extends Cursored>(visible: T[], buffered: T[]) => {
  const shown = new Set(visible.map((row) => row.id));
  return buffered.filter((row) => !shown.has(row.id)).length;
};

/** Take a poll: shown at once, or held back and counted while paused (FR-014). */
export function receive<T extends Cursored>(stream: Stream<T>, incoming: T[]): Stream<T> {
  if (!stream.paused) return { ...stream, visible: mergeRows(stream.visible, incoming) };
  const buffered = mergeRows(stream.buffered, incoming);
  return { ...stream, buffered, pending: unseen(stream.visible, buffered) };
}

export const setPaused = <T extends Cursored>(stream: Stream<T>, paused: boolean): Stream<T> =>
  paused ? { ...stream, paused } : resume(stream);

export function resume<T extends Cursored>(stream: Stream<T>): Stream<T> {
  return {
    visible: mergeRows(stream.visible, stream.buffered),
    buffered: [],
    paused: false,
    pending: 0,
  };
}

export type CorrelationGroup<T> = { correlation: string; rows: T[]; latest: number };

/** Rows that share a cause, oldest first inside a group, the newest cause first. */
export function groupByCorrelation<T extends Cursored & { correlation_id: string }>(
  rows: T[],
): CorrelationGroup<T>[] {
  const groups = new Map<string, CorrelationGroup<T>>();
  for (const row of [...rows].sort((a, b) => a.cursor - b.cursor)) {
    const group = groups.get(row.correlation_id) || {
      correlation: row.correlation_id,
      rows: [],
      latest: row.cursor,
    };
    group.rows.push(row);
    group.latest = Math.max(group.latest, row.cursor);
    groups.set(row.correlation_id, group);
  }
  return [...groups.values()].sort((a, b) => b.latest - a.latest);
}

export type LiveFilter = {
  channel: string;
  kind: string;
  outcome: string;
  actor: string;
  mcpToken: string;
  correlation: string;
  subjectType: string;
  subjectId: string;
  refresh: boolean;
  /** Show the viewer's own interactions; hidden by default. */
  own: boolean;
};

export const emptyLiveFilter: LiveFilter = {
  channel: "",
  kind: "",
  outcome: "",
  actor: "",
  mcpToken: "",
  correlation: "",
  subjectType: "",
  subjectId: "",
  refresh: false,
  own: false,
};

const opaque = /^[A-Za-z0-9_-]{1,64}$/;
const urlKeys: Record<Exclude<keyof LiveFilter, "refresh" | "own">, string> = {
  channel: "live_channel",
  kind: "live_kind",
  outcome: "live_outcome",
  actor: "live_actor",
  mcpToken: "live_token",
  correlation: "live_correlation",
  subjectType: "live_subject_type",
  subjectId: "live_subject_id",
};

/** The filter as it travels in the page URL, so a reload or a shared link keeps it. */
export function liveFilterToParams(filter: LiveFilter): URLSearchParams {
  const params = new URLSearchParams();
  for (const [key, name] of Object.entries(urlKeys) as [keyof typeof urlKeys, string][]) {
    const value = filter[key];
    if (value) params.set(name, value);
  }
  if (filter.refresh) params.set("live_refresh", "1");
  if (filter.own) params.set("live_own", "1");
  return params;
}

export function liveFilterFromParams(params: URLSearchParams): LiveFilter {
  const read = (name: string, allowed?: readonly string[]) => {
    const value = params.get(name) || "";
    if (allowed) return allowed.includes(value) ? value : "";
    return opaque.test(value) ? value : "";
  };
  return {
    channel: read("live_channel", CHANNELS),
    kind: read("live_kind", KINDS),
    outcome: read("live_outcome", OUTCOMES),
    actor: read("live_actor"),
    mcpToken: read("live_token"),
    correlation: read("live_correlation"),
    subjectType: read("live_subject_type"),
    subjectId: read("live_subject_id"),
    refresh: params.get("live_refresh") === "1",
    own: params.get("live_own") === "1",
  };
}

/** The filter as the interactions API expects it. */
export function liveFilterQuery(filter: LiveFilter): URLSearchParams {
  const query = new URLSearchParams();
  const pairs = {
    channel: filter.channel,
    kind: filter.kind,
    outcome: filter.outcome,
    actor_user_id: filter.actor,
    mcp_token_id: filter.mcpToken,
    correlation_id: filter.correlation,
  };
  for (const [name, value] of Object.entries(pairs)) if (value) query.set(name, value);
  if (filter.subjectType && filter.subjectId) {
    query.set("subject_type", filter.subjectType);
    query.set("subject_id", filter.subjectId);
  }
  if (filter.refresh) query.set("include_refresh", "true");
  if (!filter.own) query.set("hide_own", "true");
  return query;
}

export const isFiltered = (filter: LiveFilter) =>
  Object.entries(filter).some(
    ([key, value]) => key !== "refresh" && key !== "own" && Boolean(value),
  );

/** A link into the engine room with a filter, for the contextual entry points (US4). */
export function engineRoomHref(tenant: string, filter: Partial<LiveFilter> = {}): string {
  const params = liveFilterToParams({ ...emptyLiveFilter, ...filter });
  params.set("tenant", tenant);
  params.set("inspector_view", "live");
  return `/app/inspector?${params}`;
}
