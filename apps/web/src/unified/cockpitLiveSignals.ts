export type MetricObservation = { context: string; value: number };
export type EventObservation = {
  context: string;
  events: readonly { id: string; sequence: number }[];
  sequenceFloor?: number;
};

/** Compare presentation observations; a delta does not establish business throughput. */
export function metricChange(
  previous: MetricObservation | null,
  current: MetricObservation | null,
): number | null {
  if (
    !previous ||
    !current ||
    previous.context !== current.context ||
    !Number.isFinite(previous.value) ||
    !Number.isFinite(current.value)
  )
    return null;
  const delta = current.value - previous.value;
  return delta !== 0 && Number.isFinite(delta) ? delta : null;
}

/** Only later recorded events may enter; old history is never replayed as new work. */
export function newEventIds(
  previous: EventObservation | null,
  current: EventObservation | null,
): string[] {
  if (!previous || !current || previous.context !== current.context) return [];
  const floor = Math.max(
    previous.sequenceFloor || 0,
    ...previous.events.map((event) => event.sequence),
  );
  const ids = new Set(previous.events.map((event) => event.id));
  return current.events
    .filter((event) => !ids.has(event.id) && event.sequence > floor)
    .map((event) => event.id);
}
