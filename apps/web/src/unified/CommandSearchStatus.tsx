import { LoaderCircle, CircleAlert, ChevronDown } from "lucide-react";
import { t } from "../localization";
import type { SearchProvider } from "../api";
import type { ProviderState } from "./useCommandSearch";

export function CommandSearchStatus({
  providers,
  labels,
  retry,
}: {
  providers: Partial<Record<SearchProvider, ProviderState>>;
  labels: Record<string, string>;
  retry: (provider?: SearchProvider) => void;
}) {
  const pending = Object.values(providers).some((state) => state.loading);
  const failed = Object.entries(providers).filter(([, state]) => state.error);
  return (
    <div className="command-search-status">
      <div className="command-search-progress" role="status" aria-live="polite">
        {pending && (
          <span data-search-loading>
            <LoaderCircle aria-hidden="true" className="command-search-spinner" />
            {t("Searching…")}
          </span>
        )}
      </div>
      {!!failed.length && (
        <details className="command-search-errors">
          <summary>
            <CircleAlert aria-hidden="true" />
            <span>{t("Some results are unavailable.")}</span>
            <ChevronDown aria-hidden="true" />
          </summary>
          <div className="command-search-error-list">
            {failed.map(([provider]) => (
              <div key={provider}>
                <span>{t(labels[provider])}</span>
                <button
                  className="br-btn"
                  aria-label={`${t("Retry")} · ${t(labels[provider])}`}
                  onClick={() => retry(provider as SearchProvider)}
                >
                  {t("Retry")}
                </button>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
