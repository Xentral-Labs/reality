import { t } from "../localization";

/**
 * The shared placeholder for a read that has no answer yet. It draws the shape of the
 * answer that is coming instead of a framed sentence, so the page keeps its height and
 * loses its border-inside-a-border. The reveal is delayed in CSS, so a fast read never
 * flashes a placeholder at all. A failed read keeps its own card with the retry action,
 * because that state persists until someone acts on it.
 */
export function ReadState({
  loading,
  error,
  retry,
  rows = 3,
}: {
  loading?: boolean;
  error?: string;
  retry?: () => void;
  rows?: number;
}) {
  if (loading)
    return (
      <div className="read-skeleton" role="status" aria-label={t("Loading…")}>
        {Array.from({ length: Math.max(1, rows) }, (_, index) => (
          <span key={index} style={{ width: `${88 - (index % 3) * 14}%` }} />
        ))}
      </div>
    );
  return (
    <div className="rounded-xl border border-border-default bg-surface p-6" role="alert">
      <p className="font-medium">{t("Could not load this view")}</p>
      <p className="my-3 text-sm text-fg-muted">{error}</p>
      <button className="br-btn" onClick={retry}>
        {t("Retry")}
      </button>
    </div>
  );
}

/** The same placeholder for a single value read inside an existing card or row. */
export function ReadLine() {
  return <span className="read-line" role="status" aria-label={t("Loading…")} />;
}

/**
 * Classes for content that is already on screen while a newer read is in flight. The
 * previous answer stays in place and dims; it never collapses into a placeholder.
 */
export function reading(loading: boolean | undefined, className = "") {
  return `${className} read-pane${loading ? " read-busy" : ""}`.trim();
}
