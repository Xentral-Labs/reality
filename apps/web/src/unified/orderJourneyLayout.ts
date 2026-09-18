import type { TimelineEvent } from "../api";

export const journeyLanes = [
  { kind: "fact", label: "Facts", caption: "Recorded observations", color: "var(--journey-fact)" },
  {
    kind: "commitment",
    label: "Commitments",
    caption: "What was promised",
    color: "var(--journey-commitment)",
  },
  {
    kind: "reservation",
    label: "Reservations",
    caption: "What was bound",
    color: "var(--journey-reservation)",
  },
  {
    kind: "movement",
    label: "Movements",
    caption: "What actually moved",
    color: "var(--journey-movement)",
  },
  {
    kind: "ledger_entry",
    label: "Ledger entries",
    caption: "What was posted",
    color: "var(--journey-ledger)",
  },
] as const;
export const journeyLaneKind = (kind: string) => (kind === "posting_group" ? "ledger_entry" : kind);
export type JourneyRange = { start: number; end: number };
export type JourneyPoint = { key: string; lane: number; x: number; events: TimelineEvent[] };
export const mergeJourneyEvents = (a: TimelineEvent[], b: TimelineEvent[]) =>
  [...new Map([...a, ...b].map((e) => [e.id, e])).values()].sort((a, b) => a.sequence - b.sequence);
export function journeyRange(events: TimelineEvent[], fallback = Date.now()): JourneyRange {
  const eligible = events.filter((e) =>
    journeyLanes.some((l) => l.kind === journeyLaneKind(e.subject_type)),
  );
  const times = (eligible.length ? eligible : events)
    .map((e) => Date.parse(e.recorded_at))
    .filter(Number.isFinite);
  const start = times.length ? Math.min(...times) : fallback;
  const end = times.length ? Math.max(...times) : fallback;
  const pad = Math.max((end - start) * 0.07, 30_000);
  return { start: start - pad, end: end + pad };
}
export function layoutJourney(
  events: TimelineEvent[],
  range: JourneyRange,
  width: number,
): JourneyPoint[] {
  if (width <= 0 || range.end <= range.start) return [];
  const result: JourneyPoint[] = [];
  journeyLanes.forEach((lane, index) => {
    let last: JourneyPoint | undefined;
    const members = events
      .filter((e) => journeyLaneKind(e.subject_type) === lane.kind)
      .sort(
        (a, b) => Date.parse(a.recorded_at) - Date.parse(b.recorded_at) || a.sequence - b.sequence,
      );
    for (const event of members) {
      const time = Date.parse(event.recorded_at);
      if (!Number.isFinite(time) || time < range.start || time > range.end) continue;
      const x = 20 + ((time - range.start) / (range.end - range.start)) * Math.max(1, width - 40);
      if (last && x - last.x < 28) last.events.push(event);
      else {
        last = { key: event.id, lane: index, x, events: [event] };
        result.push(last);
      }
    }
  });
  return result;
}
