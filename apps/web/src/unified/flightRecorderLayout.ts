import type { FlightGraph, FlightNode } from "./flightRecorderGraph";

export const MINUTE5 = 5 * 60_000;
export const QUARTER = 15 * 60_000;
export const HOUR = 60 * 60_000;
export const HOUR6 = 6 * HOUR;
export const DAY = 24 * HOUR;
export const WEEK = 7 * DAY;
export type RecorderInterval =
  typeof MINUTE5 | typeof QUARTER | typeof HOUR | typeof HOUR6 | typeof DAY | typeof WEEK;
/** Zoom levels from finest to coarsest; the automatic choice uses three of them. */
export const INTERVALS: RecorderInterval[] = [MINUTE5, QUARTER, HOUR, HOUR6, DAY, WEEK];

export type RecorderOptions = {
  label: number;
  header: number;
  dot: number;
  gap: number;
  rows: number;
  column: number;
  pad: number;
  /** The recorder's paper always runs up to this instant (defaults to the newest record). */
  now?: number;
  /** Fill at least this many columns so the raster covers the visible band. */
  minColumns?: number;
  /** A zoom level chosen by the user; otherwise the loaded range picks the raster. */
  interval?: RecorderInterval;
  /** Use fixed columns and compact lanes for the aggregate pulse overview. */
  aggregate?: boolean;
  /** Expand aggregate lanes to fill a bounded visualization work area. */
  minHeight?: number;
};
export type RecorderColumn = {
  index: number;
  start: number;
  x: number;
  width: number;
  label: boolean;
  dayStart: boolean;
};
export type RecorderNode = {
  key: string;
  kind: string;
  lane: number;
  column: number;
  subColumn: number;
  row: number;
  reference: boolean;
  node: FlightNode;
};
export type RecorderPulse = {
  key: string;
  lane: number;
  column: number;
  reference: boolean;
  count: number;
  members: string[];
  diameter: number;
  opacity: number;
  x: number;
  y: number;
};
export type RecorderLayout = {
  interval: RecorderInterval;
  columns: RecorderColumn[];
  referenceWidth: number;
  laneTops: number[];
  laneHeights: number[];
  width: number;
  height: number;
  nodes: Map<string, RecorderNode>;
  pulses: RecorderPulse[];
  position: (key: string) => { x: number; y: number };
  /** Horizontal pixel for an instant, and the instant at a horizontal pixel. */
  xAt: (ms: number) => number;
  timeAt: (x: number) => number;
  now: number;
};

/** The loaded range picks the raster: quarter hours, hours or days. */
export function recorderInterval(range: number): RecorderInterval {
  return range <= 6 * HOUR ? QUARTER : range <= 3 * DAY ? HOUR : DAY;
}
const labelEvery: Record<RecorderInterval, number> = {
  [MINUTE5]: 3,
  [QUARTER]: 4,
  [HOUR]: 6,
  [HOUR6]: 4,
  [DAY]: 7,
  [WEEK]: 4,
};

const recordedAt = (node: FlightNode) =>
  node.event ? Date.parse(node.event.recorded_at) : Number.NaN;

export function layoutRecorder(graph: FlightGraph, options: RecorderOptions): RecorderLayout {
  const { label, header, dot, gap, rows, column, pad } = options;
  const aggregate = options.aggregate ?? false;
  const step = dot + gap;
  const lanes = graph.slots.map((_, lane) => lane);
  const timed = graph.nodes.filter(
    (node) => !node.referenceOnly && !Number.isNaN(recordedAt(node)),
  );
  const times = timed.map(recordedAt);
  const newest = times.length ? Math.max(...times) : (options.now ?? 0);
  const now = Math.max(options.now ?? newest, newest);
  const min = times.length ? Math.min(...times) : now;
  const interval = options.interval ?? recorderInterval(now - min);
  const minColumns = Math.max(1, options.minColumns ?? 1);
  const end = Math.floor(now / interval) * interval;
  const start = Math.min(Math.floor(min / interval) * interval, end - (minColumns - 1) * interval);
  const count = Math.floor((end - start) / interval) + 1;

  // Stacks: one per lane and column, filled in graph order (sequence of first observation).
  const stacks = new Map<string, RecorderNode[]>();
  const nodes = new Map<string, RecorderNode>();
  const push = (key: string, entry: RecorderNode) => {
    const stack = stacks.get(key) || [];
    entry.subColumn = Math.floor(stack.length / rows);
    entry.row = stack.length % rows;
    stack.push(entry);
    stacks.set(key, stack);
    nodes.set(entry.key, entry);
  };
  for (const node of graph.nodes) {
    if (node.referenceOnly) {
      push(`r:${node.lane}`, {
        key: node.key,
        kind: node.kind,
        lane: node.lane,
        column: -1,
        subColumn: 0,
        row: 0,
        reference: true,
        node,
      });
      continue;
    }
    const at = recordedAt(node);
    const index = Number.isNaN(at) ? 0 : Math.floor((at - start) / interval);
    push(`${node.lane}:${index}`, {
      key: node.key,
      kind: node.kind,
      lane: node.lane,
      column: index,
      subColumn: 0,
      row: 0,
      reference: false,
      node,
    });
  }
  const stackWidth = (size: number) => (size ? Math.ceil(size / rows) * step - gap : 0);
  const referenceColumns = Math.max(
    0,
    ...lanes.map((lane) => Math.ceil((stacks.get(`r:${lane}`)?.length || 0) / rows)),
  );
  const referenceWidth = referenceColumns
    ? aggregate
      ? column
      : 2 * pad + referenceColumns * step - gap
    : 0;
  const columns: RecorderColumn[] = [];
  let x = label + referenceWidth;
  let previousDay = "";
  for (let index = 0; index < count; index++) {
    const columnStart = start + index * interval;
    const widest = Math.max(
      0,
      ...lanes.map((lane) => stackWidth(stacks.get(`${lane}:${index}`)?.length || 0)),
    );
    const width = aggregate ? column : Math.max(column, widest + 2 * pad);
    const day = new Date(columnStart).toISOString().slice(0, 10);
    columns.push({
      index,
      start: columnStart,
      x,
      width,
      label: (columnStart / interval) % labelEvery[interval] === 0,
      dayStart: previousDay !== "" && day !== previousDay,
    });
    previousDay = day;
    x += width;
  }
  const width = x + 32;
  const aggregateLaneHeight = Math.max(
    60,
    Math.ceil(((options.minHeight ?? 0) - header) / Math.max(1, lanes.length)),
  );
  const laneHeights = lanes.map((lane) => {
    if (aggregate) return aggregateLaneHeight;
    let deepest = 1;
    for (const [key, stack] of stacks) {
      if (key.startsWith(`${lane}:`) || key === `r:${lane}`)
        deepest = Math.max(deepest, Math.min(rows, stack.length));
    }
    return 2 * pad + deepest * step - gap;
  });
  const laneTops = laneHeights.map(
    (_, lane) => header + laneHeights.slice(0, lane).reduce((a, b) => a + b, 0),
  );
  const height = header + laneHeights.reduce((a, b) => a + b, 0);
  const position = (key: string) => {
    const entry = nodes.get(key);
    if (!entry) return { x: 0, y: 0 };
    if (aggregate) {
      const centerY = laneTops[entry.lane] + laneHeights[entry.lane] / 2;
      const centerX = entry.reference
        ? label + referenceWidth / 2
        : columns[entry.column].x + columns[entry.column].width / 2;
      return { x: centerX - dot / 2, y: centerY - dot / 2 };
    }
    const y = laneTops[entry.lane] + pad + entry.row * step;
    if (entry.reference) return { x: label + pad + entry.subColumn * step, y };
    const col = columns[entry.column];
    const stack = stacks.get(`${entry.lane}:${entry.column}`) || [];
    const inner = stackWidth(stack.length);
    return { x: col.x + (col.width - inner) / 2 + entry.subColumn * step, y };
  };
  const pulseVisual = (count: number) => {
    const strength = Math.min(1, Math.log2(Math.max(1, count)) / 5);
    return {
      diameter: Math.round(dot + strength * (32 - dot)),
      opacity: 0.55 + strength * 0.45,
    };
  };
  const pulses = [...stacks.entries()].map(([key, stack]) => {
    const first = stack[0];
    const visual = pulseVisual(stack.length);
    const centerX = first.reference
      ? label + referenceWidth / 2
      : columns[first.column].x + columns[first.column].width / 2;
    const centerY = laneTops[first.lane] + laneHeights[first.lane] / 2;
    return {
      key: `pulse:${first.lane}:${first.reference ? "reference" : columns[first.column].start}`,
      lane: first.lane,
      column: first.column,
      reference: first.reference,
      count: stack.length,
      members: stack.map((entry) => entry.key),
      diameter: visual.diameter,
      opacity: visual.opacity,
      x: centerX - visual.diameter / 2,
      y: centerY - visual.diameter / 2,
    };
  });
  const xAt = (ms: number) => {
    const index = Math.min(count - 1, Math.max(0, Math.floor((ms - start) / interval)));
    const col = columns[index];
    return col.x + Math.min(1, Math.max(0, (ms - col.start) / interval)) * col.width;
  };
  const timeAt = (px: number) => {
    const col =
      columns.find((candidate) => px < candidate.x + candidate.width) ?? columns[count - 1];
    return col.start + Math.min(1, Math.max(0, (px - col.x) / col.width)) * interval;
  };
  return {
    interval,
    columns,
    referenceWidth,
    laneTops,
    laneHeights,
    width,
    height,
    nodes,
    pulses,
    position,
    xAt,
    timeAt,
    now,
  };
}
