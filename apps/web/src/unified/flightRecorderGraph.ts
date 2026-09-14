import type { TimelineEvent } from "../api";

export const flightLanes = ["Reference", "Source", "Evidence", "Reality", "Events"] as const;
export const kindLabels: Record<string, string> = {
  party: "Business partner",
  item: "Item",
  location: "Location",
  source_record: "Original source",
  document: "Document",
  document_line: "Document line",
  fact: "Fact",
  commitment: "Commitment",
  reservation: "Reservation",
  movement: "Movement",
  ledger_entry: "Ledger entry",
  payment: "Payment",
  business_event: "Event",
  exception: "Exception",
};
export type FlightNode = {
  key: string;
  kind: string;
  id: string;
  lane: number;
  column: number;
  slot: number;
  label: string;
  detail: string;
  event?: TimelineEvent;
  referenceOnly: boolean;
};
export type FlightEdge = { from: string; to: string; label: string };
export type FlightGraph = {
  nodes: FlightNode[];
  edges: FlightEdge[];
  events: TimelineEvent[];
  slots: number[];
  referenceColumns: number;
};
const laneFor = (kind: string) =>
  ["party", "item", "location"].includes(kind)
    ? 0
    : kind === "source_record"
      ? 1
      : ["document", "document_line"].includes(kind)
        ? 2
        : kind === "business_event"
          ? 4
          : 3;
const scalar = (value: unknown): string =>
  typeof value === "string" || typeof value === "number" ? String(value) : "";
// These payload fields are explicit references. Unknown *_id fields are not guessed.
const references: Record<string, string> = {
  party_id: "party",
  item_id: "item",
  location_id: "location",
  document_id: "document",
  document_line_id: "document_line",
  commitment_id: "commitment",
  reservation_id: "reservation",
  movement_id: "movement",
  source_record_id: "source_record",
  ledger_entry_id: "ledger_entry",
};
function recordText(kind: string, event?: TimelineEvent) {
  if (!event) return { label: "", detail: "" };
  const payload = event.payload || {},
    context = event.business_context || {};
  const names =
    kind === "source_record"
      ? [payload.external_id, payload.source_system]
      : ["party", "item", "location"].includes(kind)
        ? [payload.name, context.name, context.sku]
        : kind === "document"
          ? [payload.number, context.reference, context.party]
          : [context.item, context.party, payload.name, context.reference];
  const label = [...new Set(names.map(scalar).filter(Boolean))].join(" · ");
  const quantity = context.quantity ?? payload.quantity;
  const amount = context.amount ?? payload.amount;
  const detail =
    quantity != null
      ? [quantity, context.unit ?? payload.unit].map(scalar).filter(Boolean).join(" ")
      : amount != null
        ? [amount, context.currency ?? payload.currency].map(scalar).filter(Boolean).join(" ")
        : "";
  return { label, detail };
}
export function buildFlightGraph(input: TimelineEvent[]): FlightGraph {
  const events = [...new Map(input.map((e) => [e.id, e])).values()].sort(
    (a, b) => a.sequence - b.sequence,
  );
  const nodes = new Map<string, FlightNode>();
  const edges = new Map<string, FlightEdge>();
  const ensure = (kind: string, id: string, column: number, event?: TimelineEvent) => {
    const key = `${kind}:${id}`;
    if (!nodes.has(key))
      nodes.set(key, {
        key,
        kind,
        id,
        lane: laneFor(kind),
        column,
        slot: 0,
        ...recordText(kind, event),
        event,
        referenceOnly: !event,
      });
    return key;
  };
  const edge = (from: string, to: string, label: string) => {
    if (from !== to) edges.set(`${from}|${to}|${label}`, { from, to, label });
  };
  // Subject observations take precedence over references, regardless of arrival order.
  events.forEach((event, column) => {
    const key = ensure("business_event", event.id, column, event);
    const node = nodes.get(key)!;
    node.label = event.business_title || event.type;
    if (kindLabels[event.subject_type] && event.subject_type !== "business_event")
      ensure(event.subject_type, event.subject_id, column, event);
  });
  events.forEach((event) => {
    const eventKey = `business_event:${event.id}`;
    const subject = nodes.get(`${event.subject_type}:${event.subject_id}`);
    if (subject) edge(subject.key, eventKey, "Recorded change");
    if (event.source_record_id) {
      const source = ensure("source_record", event.source_record_id, 0);
      edge(source, subject?.key || eventKey, "Source reference");
    }
    for (const [field, kind] of Object.entries(references)) {
      const id = event.payload?.[field];
      if (typeof id !== "string" || !id) continue;
      const reference = ensure(kind, id, 0);
      if (subject) edge(reference, subject.key, "Recorded reference");
      else edge(reference, eventKey, "Recorded reference");
    }
    if (event.causation_id && nodes.has(`business_event:${event.causation_id}`))
      edge(`business_event:${event.causation_id}`, eventKey, "Caused by event");
  });
  // Unknown creation times live before dated columns, never on an event date.
  const referenceCounts = flightLanes.map(() => 0);
  for (const node of nodes.values()) {
    if (node.referenceOnly) referenceCounts[node.lane]++;
  }
  const referenceColumns = Math.ceil(Math.max(...referenceCounts) / 2);
  const referenceOffsets = flightLanes.map(() => 0);
  for (const node of nodes.values()) {
    if (node.referenceOnly) {
      node.column = -referenceColumns + Math.floor(referenceOffsets[node.lane]++ / 2);
    }
  }
  const occupancy = new Map<string, number>();
  const slots = flightLanes.map(() => 1);
  for (const node of nodes.values()) {
    const key = `${node.lane}:${node.column}`;
    node.slot = occupancy.get(key) || 0;
    occupancy.set(key, node.slot + 1);
    slots[node.lane] = Math.max(slots[node.lane], node.slot + 1);
  }
  return {
    nodes: [...nodes.values()],
    edges: [...edges.values()],
    events,
    slots,
    referenceColumns,
  };
}
export function connectedKeys(graph: FlightGraph, selected: string): Set<string> {
  const neighbors = new Map<string, string[]>();
  for (const edge of graph.edges) {
    neighbors.set(edge.from, [...(neighbors.get(edge.from) || []), edge.to]);
    neighbors.set(edge.to, [...(neighbors.get(edge.to) || []), edge.from]);
  }
  const seen = new Set([selected]),
    pending = [selected];
  while (pending.length)
    for (const key of neighbors.get(pending.pop()!) || []) {
      if (!seen.has(key)) {
        seen.add(key);
        pending.push(key);
      }
    }
  return seen;
}

export function focusFlightGraph(graph: FlightGraph, selected: string | null) {
  if (selected && !graph.nodes.some((node) => node.key === selected)) selected = null;
  const edges = selected
    ? graph.edges.filter((edge) => edge.from === selected || edge.to === selected)
    : [];
  const keys = new Set<string>(selected ? [selected] : []);
  for (const edge of edges) {
    keys.add(edge.from);
    keys.add(edge.to);
  }
  return { keys, edges };
}

export type FlightDirection = "left" | "right" | "up" | "down";
export function flightViewportFocus(
  graph: FlightGraph,
  selected: string | null,
  position: (key: string) => { x: number; y: number },
  bounds: { left: number; top: number; right: number; bottom: number },
  cardWidth: number,
  cardHeight: number,
) {
  const focus = focusFlightGraph(graph, selected);
  const offscreen: Record<FlightDirection, string[]> = { left: [], right: [], up: [], down: [] };
  const visible = new Set<string>();
  for (const key of focus.keys) {
    const { x, y } = position(key);
    const direction =
      x + cardWidth <= bounds.left
        ? "left"
        : x >= bounds.right
          ? "right"
          : y + cardHeight <= bounds.top
            ? "up"
            : y >= bounds.bottom
              ? "down"
              : null;
    if (!direction) visible.add(key);
    else if (key !== selected) offscreen[direction].push(key);
  }
  return {
    ...focus,
    offscreen,
    edges: focus.edges.filter((edge) => visible.has(edge.from) && visible.has(edge.to)),
  };
}
