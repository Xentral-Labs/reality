import type { ProjectionMetadata } from "../api";
import { formatDateTime, t } from "../localization";

export function ProjectionFreshness({
  metadata,
  refresh,
}: {
  metadata?: ProjectionMetadata;
  refresh: () => void;
}) {
  if (!metadata) return null;
  const message =
    metadata.state === "uninitialized"
      ? t("Awaiting first calculation.")
      : metadata.state === "pending"
        ? t("Results are being updated. The last completed result is shown.")
        : metadata.state === "failed"
          ? t("The calculation could not be updated.")
          : t("Stored result");
  return (
    <div
      role="status"
      data-projection-freshness={metadata.state}
      className="my-3 flex flex-wrap items-center gap-3 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted"
    >
      <span>{message}</span>
      {metadata.completed_at && (
        <span>
          {t("Last calculated")}: {formatDateTime(metadata.completed_at)}
        </span>
      )}
      <button type="button" className="br-btn" onClick={refresh}>
        {t("Refresh")}
      </button>
    </div>
  );
}
