import { useEffect, useRef, useState } from "react";
import type { ProjectionMetadata } from "../api";
import { formatDateTime, t } from "../localization";

/**
 * The stored-result notice, and the control that re-reads it.
 *
 * Refresh performs a read and nothing else: the calculation itself is advanced by the
 * scheduler, never by this page (spec 180, US2 scenario 4). So the ordinary outcome of
 * pressing it is that the same generation comes back, and saying nothing made a working
 * control look broken. The outcome is now stated either way, and the backlog explains
 * why pressing it was worth trying.
 */
export function ProjectionFreshness({
  metadata,
  refresh,
  loading = false,
}: {
  metadata?: ProjectionMetadata;
  refresh: () => void;
  loading?: boolean;
}) {
  const [waiting, setWaiting] = useState(false);
  const [outcome, setOutcome] = useState<"updated" | "unchanged" | null>(null);
  const before = useRef<string | null>(null);
  const wasLoading = useRef(loading);
  useEffect(() => {
    // Only a true → false transition ends a wait. The read reports `loading` from its
    // own effect, so the render right after the click still has it false.
    if (wasLoading.current && !loading && waiting) {
      setWaiting(false);
      setOutcome((metadata?.completed_at ?? null) === before.current ? "unchanged" : "updated");
    }
    wasLoading.current = loading;
  }, [loading, waiting, metadata?.completed_at]);
  if (!metadata) return null;
  const message =
    metadata.state === "uninitialized"
      ? t("Awaiting first calculation.")
      : metadata.state === "pending"
        ? t("Results are being updated. The last completed result is shown.")
        : metadata.state === "failed"
          ? t("The calculation could not be updated.")
          : t("Stored result");
  const behind =
    metadata.processed_event_sequence === null
      ? 0
      : Math.max(0, metadata.target_event_sequence - metadata.processed_event_sequence);
  const start = () => {
    before.current = metadata.completed_at ?? null;
    setOutcome(null);
    setWaiting(true);
    refresh();
  };
  return (
    <div
      role="status"
      aria-busy={waiting || undefined}
      data-projection-freshness={metadata.state}
      className="my-3 flex flex-wrap items-center gap-3 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted"
    >
      <span>{message}</span>
      {metadata.completed_at && (
        <span>
          {t("Last calculated")}: {formatDateTime(metadata.completed_at)}
        </span>
      )}
      {behind > 0 && (
        <span data-projection-behind={behind}>
          {t("Events not yet included")}: {behind}
        </span>
      )}
      {outcome && !waiting && (
        <span data-projection-outcome={outcome}>
          {outcome === "updated" ? t("Updated") : t("Unchanged")}
        </span>
      )}
      <button type="button" className="br-btn" disabled={waiting} onClick={start}>
        {waiting ? t("Updating…") : t("Refresh")}
      </button>
    </div>
  );
}
