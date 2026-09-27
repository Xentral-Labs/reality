// Welcome reads background readiness and the activity graph. A fixture that lands on
// Welcome answers them with a ready, quiet company; the server always fills the whole
// period with buckets, empty ones included.
export function homeRead(path) {
  if (path.endsWith("/readiness"))
    return {
      status: "ready",
      components: { connection: "ready", scheduler: "ready", worker: "ready" },
      observed_at: "2026-09-27T12:00:00Z",
    };
  if (path.endsWith("/activity-volume"))
    return {
      start: "2026-09-26T12:00:00Z",
      observed_at: "2026-09-27T12:00:00Z",
      coverage_start: "2026-09-26T12:00:00Z",
      bucket_seconds: 1800,
      total: 0,
      buckets: Array.from({ length: 48 }, (_, i) => ({
        start: new Date(Date.parse("2026-09-26T12:00:00Z") + i * 1800000).toISOString(),
        end: new Date(Date.parse("2026-09-26T12:30:00Z") + i * 1800000).toISOString(),
        counts: { orders: 0, reservations: 0, movements: 0, documents: 0 },
      })),
    };
  return null;
}
