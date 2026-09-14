import { t } from "../localization";

export function SettingsEmptyState({
  message = "No entries yet.",
  reset,
}: {
  message?: string;
  reset?: () => void;
}) {
  return (
    <div className="rounded-lg border border-border-default p-4 text-sm text-fg-muted">
      <p>{t(reset ? "No matching references" : message)}</p>
      {reset && (
        <button type="button" className="br-btn mt-3" onClick={reset}>
          {t("Reset filters")}
        </button>
      )}
    </div>
  );
}
