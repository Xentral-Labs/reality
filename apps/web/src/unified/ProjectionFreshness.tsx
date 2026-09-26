import { useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { api, type ProjectionMetadata } from "../api";
import { formatDateTime, t } from "../localization";
import { useActionDiscovery } from "./ActionLauncher";
import { reasonText } from "./guidanceActions";
import { useRead } from "./useCompanyContext";

/** Read the latest stored calculation without starting background work. */
export function ProjectionFreshness({
  metadata,
  refresh,
  loading = false,
  error,
}: {
  metadata?: ProjectionMetadata;
  refresh: () => void;
  loading?: boolean;
  error?: string;
}) {
  const [waiting, setWaiting] = useState(false);
  const [minimumFeedback, setMinimumFeedback] = useState(false);
  useEffect(() => {
    if (!minimumFeedback) return;
    // Keep a fast read visible without delaying the data itself.
    const timer = window.setTimeout(() => setMinimumFeedback(false), 1000);
    return () => window.clearTimeout(timer);
  }, [minimumFeedback]);
  const busy = waiting || minimumFeedback;
  const context = useActionDiscovery();
  const explain = !!metadata?.guidance && metadata.state !== "ready" && !!context;
  // Spec 279 FR-011: say whether background processing runs; read it only when needed.
  const readiness = useRead(
    () => (explain ? api.readiness(context!.tenant) : Promise.resolve(null)),
    [explain, context?.tenant],
  );
  const [outcome, setOutcome] = useState<"updated" | "unchanged" | null>(null);
  const before = useRef<string | null>(null);
  const wasLoading = useRef(loading);
  useEffect(() => {
    // Only a true → false transition ends a wait. The read reports `loading` from its
    // own effect, so the render right after the click still has it false.
    if (wasLoading.current && !loading && waiting) {
      setWaiting(false);
      setOutcome(
        error || !metadata
          ? null
          : (metadata.completed_at ?? null) === before.current
            ? "unchanged"
            : "updated",
      );
    }
    wasLoading.current = loading;
  }, [loading, waiting, metadata, error]);
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
    if (busy || loading) return;
    before.current = metadata.completed_at ?? null;
    setWaiting(true);
    setMinimumFeedback(true);
    refresh();
  };
  const feedback = [
    t("Calculations run in the background. Refresh checks for a newer result."),
    t("Checking for a newer calculation…"),
    t("No newer calculation available."),
    t("Newer calculation loaded."),
    t("Could not check for a newer calculation. Try again."),
  ];
  const feedbackIndex = busy
    ? 1
    : error
      ? 4
      : outcome === "updated"
        ? 3
        : outcome === "unchanged"
          ? 2
          : 0;
  const guidance = explain ? metadata.guidance! : null;
  const reason = guidance
    ? reasonText(context?.data?.resolution_guidance, guidance.reason_code)
    : null;
  const processing = readiness.data?.components?.worker;
  return (
    <>
      <div
        role="status"
        aria-busy={busy || undefined}
        data-projection-freshness={metadata.state}
        data-projection-attention={metadata.state !== "ready" || behind > 0 || !!error}
        className="my-3 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted"
      >
        <div className="flex flex-wrap items-center gap-3">
          <span data-projection-timestamp>
            {metadata.completed_at
              ? `${t("Last calculated")}: ${formatDateTime(metadata.completed_at)}`
              : message}
          </span>
          <button
            type="button"
            className="br-btn shrink-0 transition-none aria-disabled:cursor-wait"
            aria-disabled={busy || loading}
            aria-busy={busy || undefined}
            onClick={start}
          >
            <RefreshCw
              size={14}
              aria-hidden="true"
              data-refresh-spinner
              className="shrink-0 animate-spin motion-reduce:animate-none"
              style={{ animation: busy ? undefined : "none" }}
            />
            {t("Refresh")}
          </button>
        </div>
        {(metadata.completed_at && metadata.state !== "ready") || behind > 0 ? (
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1">
            {metadata.completed_at && metadata.state !== "ready" && <span>{message}</span>}
            {behind > 0 && (
              <span data-projection-behind={behind}>
                {t("Events not yet included")}: {behind}
              </span>
            )}
          </div>
        ) : null}
        {error && <p className="mt-1">{feedback[4]}</p>}
        <span
          className="sr-only"
          data-projection-feedback
          data-projection-outcome={!busy && !error ? outcome : undefined}
        >
          {feedback[feedbackIndex]}
        </span>
      </div>
      {guidance && reason && (
        <div
          data-projection-guidance={guidance.reason_code}
          className="-mt-1 mb-3 rounded-lg border border-border-default p-3 text-sm"
        >
          <div className="font-medium text-fg-strong">{reason.label}</div>
          <div className="mt-1 text-fg-muted">{reason.explanation}</div>
          {processing && processing !== "ready" && (
            <div className="mt-2" data-projection-processing={processing}>
              {t(
                processing === "unavailable"
                  ? "Background processing is currently unavailable, so calculations cannot run."
                  : "Background processing has not been confirmed yet.",
              )}
            </div>
          )}
          <button
            type="button"
            className="br-btn mt-2"
            onClick={() => context?.navigate({ route: "home" })}
          >
            {t("Open system status")}
          </button>
        </div>
      )}
    </>
  );
}
